"""Linear response of the reco-level moments and its inversion (PLAN.md Sec. 6.3,
items 2-3; machinery only, no MC yet).

Base sample: isotropic decays (rho_b = 1/9, sample S2), events i with true
analyser directions Omega_i, base weights b_i, a selection flag sel_i and reco
angles.  Reweighted to target coefficients c, event i carries the weight
b_i (1 + c . phi(Omega_i)) exactly (``reweight.phi_functions``), so every
expected reco-level sum per generated event,

    S_j(c) = E[sel m_j(reco)] = A_j . (1, c),          j = 0 .. 80,

is exactly linear in (1, c), with m_0 = 1 (selected count) and m_1..80 the
estimators of ``basis.estimator_vector`` on the reco angles (optionally with
the mistag correction, CONVENTIONS.md Sec. 3).  A is (81, 81), the identity for
a perfect detector, and is accumulated directly from the base sample.  The
plan's construction, reweighting S2 to the basis-element targets
1/9 +- eps O_k (``reweight.target_basis_element``) and differencing, gives the
same A for any eps (tests/test_response.py).

Data with N_tot produced signal events have expected sums A psi with
psi = N_tot (1, c), and Poisson covariance estimated by sum_i m_i m_i^T over the
selected events (``observed_sums``).  ``unfold`` solves for psi by generalised
least squares in a subspace of coefficients (``basis.subspace``), optionally
Tikhonov-regularised, and returns c = psi_1.. / psi_0 with linearised errors.
The normalised form of the plan, reco moment means = R c + b around c0, is
``linearised_moments``.
"""
from dataclasses import dataclass

import numpy as np
from scipy import linalg as _la
from scipy import stats as _st

from . import basis
from .reweight import phi_functions
from .stats import delta_method

CHUNK = 100_000
N_MOMENTS = 1 + basis.N_COEFF
MOMENT_LABELS = ("n",) + basis.COEFF_LABELS


def reco_moments(theta_p, phi_p, theta_m, phi_m, mistag_p=0.0, mistag_m=0.0):
    """Reco moment functions m = [1, x], x = ``basis.estimator_vector``, shape (..., 81).
    Memory: (n, 81) floats, so evaluate large samples in chunks."""
    x = basis.estimator_vector(theta_p, phi_p, theta_m, phi_m, mistag_p, mistag_m)
    return np.concatenate([np.ones(x.shape[:-1] + (1,)), x], axis=-1)


def _take(x, idx):
    return x if x.ndim == 0 else x[idx]


def _angles(angles):
    out = tuple(np.asarray(a, dtype=float) for a in angles)
    if len(out) != 4 or len({a.shape for a in out}) != 1 or out[0].ndim != 1:
        raise ValueError("angles must be (theta+, phi+, theta-, phi-), four 1-d arrays of equal length")
    return out


def build_response(true_angles, reco_angles, selected=None, base_weights=None,
                   mistag=(0.0, 0.0), n_generated=None, cov_at=None, chunk=CHUNK):
    """Response matrix A (81, 81): S_j(c) = A_j . (1, c) (module docstring).

    true_angles, reco_angles: (theta+, phi+, theta-, phi-), arrays (n,); reco angles
        are read only for selected events (others may be NaN).
    selected: bool (n,), default all.
    base_weights: (n,) weights of the isotropic base sample, default 1.  A
        non-isotropic base can be used with reweight.weights_ratio(1/9, rho_b, ...).
    mistag: (w+, w-) analyser mistag rates for the reco estimators, scalars or (n,).
    n_generated: total base weight of the generated sample when the arrays hold only
        part of it (e.g. only the selected events); default sum(base_weights).
    cov_at: coefficient vector c_ref (80,).  Then C (81, 81) is returned as well, the
        base-sample statistical covariance of A . (1, c_ref) (Poisson estimate
        sum_i [b_i sel_i (1 + c_ref . phi_i)]^2 m_i m_i^T / n_generated^2); for N_tot
        data events the predicted sums carry N_tot^2 C (``unfold(cov_response=C)``).
    Returns A, or (A, C).
    """
    true = _angles(true_angles)
    reco = _angles(reco_angles)
    n = true[0].size
    if reco[0].size != n:
        raise ValueError("true and reco angles must describe the same events")
    sel = np.ones(n, dtype=bool) if selected is None else np.asarray(selected, dtype=bool)
    b = np.ones(n) if base_weights is None else np.broadcast_to(np.asarray(base_weights, dtype=float), (n,))
    norm = float(b.sum()) if n_generated is None else float(n_generated)
    w_p, w_m = (np.asarray(w, dtype=float) for w in mistag)
    ct = None if cov_at is None else np.concatenate([[1.0], np.asarray(cov_at, dtype=float)])
    A = np.zeros((N_MOMENTS, N_MOMENTS))
    C = None if ct is None else np.zeros((N_MOMENTS, N_MOMENTS))
    for start in range(0, n, chunk):
        idx = start + np.flatnonzero(sel[start:start + chunk])
        if idx.size == 0:
            continue
        m = reco_moments(*(a[idx] for a in reco), _take(w_p, idx), _take(w_m, idx))
        design = np.empty((idx.size, N_MOMENTS))
        design[:, 0] = 1.0
        design[:, 1:] = phi_functions(*(a[idx] for a in true))
        A += (m * b[idx, None]).T @ design
        if C is not None:
            y = m * (b[idx] * (design @ ct))[:, None]
            C += y.T @ y
    A /= norm
    if C is None:
        return A
    return A, C / norm ** 2


def observed_sums(reco_angles, selected=None, weights=None, mistag=(0.0, 0.0), chunk=CHUNK):
    """Observed sums s = sum_i w_i m(reco_i) over the selected events and their Poisson
    covariance V = sum_i w_i^2 m_i m_i^T (PLAN.md Sec. 6.3); shapes (81,) and (81, 81).
    ``weights`` (default 1): event weights, e.g. reweighting or bootstrap weights."""
    reco = _angles(reco_angles)
    n = reco[0].size
    sel = np.ones(n, dtype=bool) if selected is None else np.asarray(selected, dtype=bool)
    w = np.ones(n) if weights is None else np.broadcast_to(np.asarray(weights, dtype=float), (n,))
    w_p, w_m = (np.asarray(x, dtype=float) for x in mistag)
    s = np.zeros(N_MOMENTS)
    V = np.zeros((N_MOMENTS, N_MOMENTS))
    for start in range(0, n, chunk):
        idx = start + np.flatnonzero(sel[start:start + chunk])
        if idx.size == 0:
            continue
        m = reco_moments(*(a[idx] for a in reco), _take(w_p, idx), _take(w_m, idx))
        wm = m * w[idx, None]
        s += wm.sum(axis=0)
        V += wm.T @ wm
    return s, V


def expected_sums(A, c, n_total=1.0):
    """Expected observed sums N_tot A (1, c) for target coefficients c (80,)."""
    return n_total * (np.asarray(A, dtype=float) @ np.concatenate([[1.0], np.asarray(c, dtype=float)]))


def normalised_moments(A, c):
    """Expected reco moment means over the selected events, S_j(c) / S_0(c), j = 1 .. 80."""
    s = expected_sums(A, c)
    return s[1:] / s[0]


def linearised_moments(A, c0):
    """Linearised normalised moments around c0: S_j(c)/S_0(c) ~ R c + b (PLAN.md Sec. 6.3
    item 2), R = d(S_j/S_0)/dc at c0 (80, 80) and b = mu(c0) - R c0.  For a perfect
    detector R = 1, b = 0.  Diagnostics only: ``unfold`` uses the exact linear form."""
    A = np.asarray(A, dtype=float)
    c0 = np.asarray(c0, dtype=float)
    s = expected_sums(A, c0)
    R = (A[1:, 1:] * s[0] - np.outer(s[1:], A[0, 1:])) / s[0] ** 2
    return R, s[1:] / s[0] - R @ c0


@dataclass
class Unfolded:
    """Result of ``unfold``.  c = B beta; covariances are linearised (delta method)."""
    coefficients: np.ndarray        # c (80,)
    covariance: np.ndarray          # cov(c) (80, 80), rank k
    beta: np.ndarray                # subspace coordinates (k,)
    cov_beta: np.ndarray            # (k, k)
    basis: np.ndarray               # B (80, k), orthonormal columns
    n_total: float                  # psi_0: produced signal events, A normalisation
    n_total_error: float
    theta: np.ndarray               # GLS parameters (psi_0, psi_0 beta) (1 + k,)
    cov_theta: np.ndarray
    chi2: float                     # GLS chi^2 of the moment equations
    ndf: int                        # n_moments - (1 + k)
    condition_number: float         # cond(A E), the response restricted to the subspace
    regularisation: float
    converged: bool                 # iterations (regularisation, cov_response) converged

    @property
    def errors(self):
        return np.sqrt(np.clip(np.diag(self.covariance), 0.0, None))

    @property
    def p_value(self):
        return float(_st.chi2.sf(self.chi2, self.ndf)) if self.ndf > 0 else float("nan")


def unfold(A, sums, cov, subspace="full", regularisation=0.0, reference=None,
           cov_response=None, max_iter=100):
    """Unfold observed reco sums to the coefficients (PLAN.md Sec. 6.3 item 3).

    Parameters psi = N_tot (1, c) with c = B beta in the subspace B (a ``basis.subspace``
    name or an (80, k) matrix with orthonormal columns), i.e. psi = E theta,
    theta = (psi_0, gamma), gamma = psi_0 beta, E = diag(1, B).  Generalised least squares

        min_theta (s - A E theta)^T V^-1 (s - A E theta) + regularisation |beta - beta_ref|^2

    with V = ``cov`` (+ psi_0^2 ``cov_response`` for the base-sample statistics of A,
    ``build_response(cov_at=...)``, updated with the current psi_0).  The optional
    Tikhonov term is a Gaussian constraint of width 1/sqrt(regularisation) on every
    subspace coefficient around ``reference`` (default 0, the isotropic state); as
    beta = gamma / psi_0 it is minimised by Gauss-Newton iteration.  The returned
    covariance is the sandwich M^-1 F M^-1, F = (AE)^T V^-1 (AE), M = F + regularisation
    J^T J, J = d beta / d theta (statistical only: the regularisation bias is not
    included).  Without regularisation and with A square and invertible in the full space
    this is psi = A^-1 s for any V.  ``A``, ``sums`` and ``cov`` may be restricted to a
    subset of moment rows by the caller; row 0 (the selected count) must be kept, it
    gives the starting value of psi_0.  The condition number reported is that of AE,
    the response restricted to the subspace (1 for a perfect detector).
    """
    A = np.asarray(A, dtype=float)
    s = np.asarray(sums, dtype=float)
    V = np.asarray(cov, dtype=float)
    B = basis.subspace(subspace) if isinstance(subspace, str) else np.asarray(subspace, dtype=float)
    n_c, k = B.shape
    if A.shape[1] != 1 + n_c or A.shape[0] != s.size or V.shape != (s.size, s.size):
        raise ValueError("inconsistent shapes of A, sums, cov and subspace")
    E = np.zeros((1 + n_c, 1 + k))
    E[0, 0] = 1.0
    E[1:, 1:] = B
    X = A @ E
    c_ref = np.zeros(n_c) if reference is None else np.asarray(reference, dtype=float)
    beta_ref = B.T @ c_ref
    psi0 = s[0] / (A[0] @ np.concatenate([[1.0], c_ref]))     # N_tot if c = c_ref
    theta = np.concatenate([[psi0], psi0 * beta_ref])
    linear = regularisation == 0 and cov_response is None
    converged = False
    for _ in range(max_iter):
        Vt = V if cov_response is None else V + theta[0] ** 2 * np.asarray(cov_response, dtype=float)
        try:
            chol = _la.cho_factor(Vt)
        except _la.LinAlgError as err:
            raise ValueError("unfold: covariance of the sums is not positive definite") from err
        F = X.T @ _la.cho_solve(chol, X)
        beta = theta[1:] / theta[0]
        jac = np.hstack([-beta[:, None], np.eye(k)]) / theta[0]     # d beta / d theta, jac @ theta = 0
        M = F + regularisation * (jac.T @ jac)
        new = np.linalg.solve(M, X.T @ _la.cho_solve(chol, s) + regularisation * jac.T @ (beta_ref - beta))
        converged = linear or np.allclose(new, theta, rtol=1e-12, atol=1e-12 * abs(new[0]))
        theta = new
        if converged:
            break
    beta = theta[1:] / theta[0]
    jac = np.hstack([-beta[:, None], np.eye(k)]) / theta[0]
    M = F + regularisation * (jac.T @ jac)
    m_inv = np.linalg.inv(M)
    cov_theta = m_inv @ F @ m_inv
    cov_beta = delta_method(jac, cov_theta)
    r = s - X @ theta
    return Unfolded(coefficients=B @ beta, covariance=B @ cov_beta @ B.T, beta=beta,
                    cov_beta=cov_beta, basis=B, n_total=float(theta[0]),
                    n_total_error=float(np.sqrt(cov_theta[0, 0])), theta=theta,
                    cov_theta=cov_theta, chi2=float(r @ _la.cho_solve(chol, r)),
                    ndf=int(s.size - 1 - k), condition_number=float(np.linalg.cond(X)),
                    regularisation=float(regularisation), converged=bool(converged))
