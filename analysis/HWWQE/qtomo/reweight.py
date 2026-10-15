"""Decay-angle reweighting between spin states (PLAN.md Sec. 3.7).

An event generated with the spin state rho_b and analyser directions
(Omega+, Omega-) is moved to the target state rho_t with the weight

    w = Tr[rho_t (Pi+ x Pi-)] / Tr[rho_b (Pi+ x Pi-)]

(decay distribution (3/4pi)^2 Tr[rho (Pi+ x Pi-)], CONVENTIONS.md Sec. 2).  For
unit-trace states the distributions of all spin-independent quantities
(production kinematics, W masses, detector response at fixed true directions)
are unchanged.  For an isotropic base (rho_b = 1/9, sample S2 of PLAN.md
Sec. 5.3) the weight is

    w = 9 Tr[rho_t (Pi+ x Pi-)] = 1 + c_t . phi(Omega+, Omega-),

exactly linear in the target coefficients c_t (``phi_functions``) and bounded
by 9 for a physical target (Pi+ x Pi- is a rank-1 projector).

A state is a (9, 9) density matrix shared by all events, or one state per event:
an array (n, 9, 9) or a ``PerEventStates``, which builds the states of a chunk
of events on demand (e.g. the SM state at each event's kappa) so that large
samples never hold n 9x9 matrices.
"""
import numpy as np

from . import basis, sm

CHUNK = 100_000                 # events per chunk: keeps (chunk, 80) work arrays small

# Flattened operators: c_k = Re Tr[rho O_k] / N_k = Re(rho.ravel() @ _OPS_FLAT[k]) / N_k
# (``basis.coefficient_vector`` as a single matrix product, for stacks of states).
_OPS_FLAT = np.swapaxes(basis.OPERATORS, -1, -2).reshape(basis.N_COEFF, 81)


def _coefficient_vectors(rho):
    """``basis.coefficient_vector`` for a stack (m, 9, 9), via one BLAS product."""
    rho = np.asarray(rho)
    return np.real(rho.reshape(rho.shape[:-2] + (81,)) @ _OPS_FLAT.T) / basis.NORMS


def phi_functions(theta_p, phi_p, theta_m, phi_m):
    """phi = 9 [q+ (8), q- (8), q+ q-^T (64)] in ``basis.pack`` order, shape (..., 80).

    9 Tr[rho (Pi+ x Pi-)] = 1 + c . phi for the state with coefficient vector c,
    since Tr[(T^a x T^b)(Pi+ x Pi-)] = q+^a q-^b (CONVENTIONS.md Sec. 1-2).
    Memory: (n, 80) floats, so evaluate large samples in chunks.
    """
    qp = basis.q_functions(theta_p, phi_p, +1)
    qm = basis.q_functions(theta_m, phi_m, -1)
    hh = qp[..., :, None] * qm[..., None, :]
    return 9.0 * np.concatenate([qp, qm, hh.reshape(hh.shape[:-2] + (64,))], axis=-1)


class PerEventStates:
    """One spin state per event, built chunk by chunk from per-event parameters.

    ``make(*params[index])`` returns the coefficient vectors (m, 80) of the
    events selected by ``index``; all parameters have length n along axis 0.
    Used for targets that vary from event to event, e.g. the SM state at the
    kappa of each event's W masses (``target_sm``).
    """

    def __init__(self, make, *params):
        self.make = make
        self.params = tuple(np.asarray(p) for p in params)
        lengths = {len(p) for p in self.params}
        if len(lengths) != 1:
            raise ValueError("PerEventStates: parameters must have one common length")
        self.n = lengths.pop()

    def __len__(self):
        return self.n

    def coefficients(self, index=slice(None)):
        """Coefficient vectors (m, 80) of the selected events."""
        return np.asarray(self.make(*(p[index] for p in self.params)), dtype=float)

    def density_matrices(self, index=slice(None)):
        """Density matrices (m, 9, 9) of the selected events."""
        return basis.density_matrix_from_vector(self.coefficients(index))


def _is_fixed(rho):
    return not isinstance(rho, PerEventStates) and np.ndim(rho) == 2


def _chunk_coefficients(rho, index):
    if isinstance(rho, PerEventStates):
        return rho.coefficients(index)
    return _coefficient_vectors(np.asarray(rho)[index])


def trace_states(rho, theta_p, phi_p, theta_m, phi_m, chunk=CHUNK):
    """Tr[rho (Pi+ x Pi-)] per event for unit-trace states.

    ``rho``: a (9, 9) state for all events (``basis.trace_projectors``), or
    per-event states (array (n, 9, 9) or ``PerEventStates``), evaluated in chunks
    as (1 + c . phi) / 9.  Lies in [0, 1] for physical states.
    """
    angles = np.broadcast_arrays(*(np.asarray(a, dtype=float)
                                   for a in (theta_p, phi_p, theta_m, phi_m)))
    fixed = _is_fixed(rho)
    if fixed and angles[0].ndim != 1:
        return basis.trace_projectors(np.asarray(rho), *angles)
    n = angles[0].shape[0] if angles[0].ndim else 1
    if angles[0].ndim != 1 or not (fixed or len(rho) == n):
        raise ValueError("per-event states need 1-d angle arrays of the same length")
    out = np.empty(n)
    for start in range(0, n, chunk):
        sl = slice(start, start + chunk)
        if fixed:
            out[sl] = basis.trace_projectors(np.asarray(rho), *(a[sl] for a in angles))
        else:
            phi = phi_functions(*(a[sl] for a in angles))
            out[sl] = (1.0 + np.einsum("nk,nk->n", _chunk_coefficients(rho, sl), phi)) / 9.0
    return out


def weights_from_isotropic(rho_target, theta_p, phi_p, theta_m, phi_m, chunk=CHUNK):
    """w = 9 Tr[rho_t (Pi+ x Pi-)] for a base sample with isotropic decays (rho_b = 1/9).

    E[w] = 1 over the isotropic base and 0 <= w <= 9 for a physical target
    (PLAN.md Sec. 3.7).  ``rho_target`` as in ``trace_states``.
    """
    return 9.0 * trace_states(rho_target, theta_p, phi_p, theta_m, phi_m, chunk)


def weights_ratio(rho_target, rho_base, theta_p, phi_p, theta_m, phi_m, eps=1e-6, chunk=CHUNK):
    """w = Tr[rho_t (Pi+ x Pi-)] / Tr[rho_b (Pi+ x Pi-)] for a base sample generated with rho_b.

    Events with Tr[rho_b (Pi+ x Pi-)] < eps are rejected (w = 0), PLAN.md Sec. 3.7.
    The target probability in the rejected region is lost; for unit-trace states
    E_b[w] = 1 - (lost target probability), so 1 - mean(w) estimates it.
    For a pure base state (e.g. the SM at fixed kappa) the denominator vanishes on a
    codimension-2 set of directions: the weights then have a tail P(w > W) ~ W^-2 and a
    logarithmically divergent variance (cut off by eps), so sample-variance errors of
    weighted means underestimate the spread (chi^2 of the 80 reweighted moments about 30%
    high on average, with a heavy upper tail).  A mixed base (e.g. the SM averaged over
    m_W*, or any base with an isotropic admixture) or an isotropic base does not have
    this problem.
    Returns (weights, rejected_mask, rejected_fraction of the base events).
    """
    num = trace_states(rho_target, theta_p, phi_p, theta_m, phi_m, chunk)
    den = trace_states(rho_base, theta_p, phi_p, theta_m, phi_m, chunk)
    num, den = np.broadcast_arrays(num, den)
    rejected = den < eps
    w = np.zeros(den.shape)
    np.divide(num, den, out=w, where=~rejected)
    return w, rejected, float(rejected.mean()) if rejected.size else 0.0


# --------------------------------------------------------------------------
# Targets (PLAN.md Sec. 3.7)
# --------------------------------------------------------------------------
def _sm_coefficients(kappa):
    return basis.pack(*sm.coefficients(kappa))


def _decohered_sm_coefficients(kappa):
    return _coefficient_vectors(sm.decohered(sm.density_matrix(kappa)))


def _identity(c):
    return c


def target_sm(kappa):
    """SM state |Psi_H(kappa)><Psi_H(kappa)| (``sm.density_matrix``).

    Scalar kappa: a (9, 9) matrix.  One kappa per event (m_W*-dependent target):
    ``PerEventStates`` from the closed form ``sm.coefficients``, which
    tests/test_sm.py pins to ``sm.density_matrix``.
    """
    if np.ndim(kappa) == 0:
        return sm.density_matrix(kappa)
    return PerEventStates(_sm_coefficients, np.asarray(kappa, dtype=float))


def target_decohered_sm(kappa):
    """SM state with all coherences removed in the |m+ m-> basis (``sm.decohered``):
    a separable null hypothesis.  Scalar or per-event kappa as in ``target_sm``."""
    if np.ndim(kappa) == 0:
        return sm.decohered(sm.density_matrix(kappa))
    return PerEventStates(_decohered_sm_coefficients, np.asarray(kappa, dtype=float))


def target_isotropic():
    """1/9: no spin information (the S2 null)."""
    return basis.ID9 / 9.0


def _coeff_index(k):
    if isinstance(k, str):
        return basis.COEFF_LABELS.index(k)
    k = int(k)
    if not 0 <= k < basis.N_COEFF:
        raise ValueError(f"coefficient index {k} outside [0, {basis.N_COEFF})")
    return k


def basis_element_eps_range(k):
    """Interval (eps_min, eps_max) for which 1/9 + eps OPERATORS[k] is positive
    semi-definite: -1/(9 lambda_max) <= eps <= 1/(9 |lambda_min|), lambda the
    eigenvalues of OPERATORS[k].  ``k``: index in ``basis.pack`` order or a label
    such as 'h44'."""
    lam = np.linalg.eigvalsh(basis.OPERATORS[_coeff_index(k)])
    return -1.0 / (9.0 * lam[-1]), 1.0 / (9.0 * -lam[0])


def target_basis_element(k, eps):
    """1/9 + eps OPERATORS[k]: coefficient k equal to eps, all others zero.

    These are the single-basis-element targets used to build the linear
    response (PLAN.md Sec. 3.7, 6.3).  Raises ValueError if |eps| is too large
    for a positive semi-definite state (``basis_element_eps_range``).
    """
    k = _coeff_index(k)
    lo, hi = basis_element_eps_range(k)
    if not lo * (1 + 1e-12) <= eps <= hi * (1 + 1e-12):       # rounding at the edge
        raise ValueError(f"eps = {eps} outside [{lo:.6g}, {hi:.6g}]: "
                         f"1/9 + eps O[{basis.COEFF_LABELS[k]}] is not a physical state")
    return basis.ID9 / 9.0 + eps * basis.OPERATORS[k]


def target_from_coefficients(c, check=True, tol=1e-12):
    """State 1/9 + sum_k c_k OPERATORS[k] from a coefficient vector (80,) (a (9, 9)
    matrix) or one vector per event (n, 80) (``PerEventStates``).

    With ``check`` a ValueError is raised if any state has an eigenvalue below
    -tol (weights would not be bounded by 9 and could be negative).
    """
    c = np.asarray(c, dtype=float)
    if c.shape[-1] != basis.N_COEFF or c.ndim not in (1, 2):
        raise ValueError("coefficients must have shape (80,) or (n, 80)")
    if check:
        for start in range(0, len(c) if c.ndim == 2 else 1, CHUNK):
            block = c[start:start + CHUNK] if c.ndim == 2 else c
            lam = basis.min_eigenvalue(basis.density_matrix_from_vector(block))
            if np.min(lam) < -tol:
                raise ValueError(f"coefficients give an unphysical state "
                                 f"(minimum eigenvalue {np.min(lam):.3g})")
    if c.ndim == 1:
        return basis.density_matrix_from_vector(c)
    return PerEventStates(_identity, c)
