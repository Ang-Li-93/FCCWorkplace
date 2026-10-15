"""CGLMP Bell observable I3, concurrence bound C2 and entanglement entropy of the
W+ W- spin state (PLAN.md Sec. 3.5; CONVENTIONS.md Sec. 6), pinned down by
tests/test_bell.py.

* ``B_CGLMP`` is the unrotated CGLMP operator of PLAN.md Sec. 3.5,

      B = T4xT4 + T5xT5 - (1/sqrt3)[T1xT1 + T1xT6 + T6xT1 + T6xT6 + T2xT2 + T2xT7 + T7xT2 + T7xT7]
        = T4xT4 + T5xT5 - (2/sqrt3)(Sx x Sx + Sy x Sy),

  so that Tr[rho B] = 4(h44 + h55) - (4/sqrt3)(h11 + h16 + h61 + h66 + h22 + h27 + h72 + h77)
  (2302.00683 Eq. 2.40).  It is the Bell operator of the CGLMP inequality (Collins et al.,
  PRL 88 (2002) 040404) for the measurement settings that are optimal for the maximally
  entangled state, written in a different local basis: local realism gives Tr[rho B] <= 2,
  its largest eigenvalue is 1 + sqrt(11/3) = 2.9149 (Acin et al., PRA 65 (2002) 052325) and the
  maximally entangled state reaches 4/(6 sqrt3 - 9) = 2.8729.  Separable states give
  I3 <= 1.4738 (the maximum over product states, tests/test_bell.py), well below 2.
  B commutes with J_z = S_z x 1 + 1 x S_z, so I3 maxima are never isolated points.
* I3 = max_{U,V in U(3)} Tr[rho (U x V)^dag B (U x V)] (``i3_optimise``).
* C2 = 2 max(0, Tr rho^2 - Tr rho_A^2, Tr rho^2 - Tr rho_B^2) (2302.00683 Eq. 2.39 and the
  references there), a lower bound on the squared concurrence, equal to it for pure states
  (4/3 when maximally entangled); C2 > 0 implies entanglement.  A = W+, B = W-.

All functions accept unphysical (reconstructed) Hermitian, unit-trace matrices; quote results
both raw and after ``basis.nearest_physical`` (CONVENTIONS.md Sec. 6, ``observables``).
"""
from dataclasses import dataclass

import numpy as np
from scipy.linalg import schur
from scipy.optimize import minimize

from . import basis

SQRT3 = basis.SQRT3
_T = basis.GELL_MANN
_ID3 = basis.ID3


def _cglmp_operator():
    k = np.kron
    rank2 = k(_T[3], _T[3]) + k(_T[4], _T[4])
    vector = (sum(k(_T[a], _T[b]) for a in (0, 5) for b in (0, 5))      # T1, T6
              + sum(k(_T[a], _T[b]) for a in (1, 6) for b in (1, 6)))   # T2, T7
    return rank2 - vector / SQRT3


B_CGLMP = _cglmp_operator()
I3_LOCAL_BOUND = 2.0                            # local realism
I3_MAX = 1.0 + np.sqrt(11.0 / 3.0)              # largest eigenvalue of B (no state exceeds it)
I3_MAX_ENTANGLED = 4.0 / (6.0 * SQRT3 - 9.0)    # sum_i |ii>/sqrt3 after optimisation


# --------------------------------------------------------------------------
# Bell operator expectation values
# --------------------------------------------------------------------------
def _kron33(u, v):
    """Kronecker product of (stacks of) 3x3 matrices, broadcast over leading axes."""
    out = np.asarray(u)[..., :, None, :, None] * np.asarray(v)[..., None, :, None, :]
    return out.reshape(out.shape[:-4] + (9, 9))


def bell_operator(u=None, v=None):
    """Rotated CGLMP operator (U x V)^dag B (U x V); identity for u, v = None."""
    m = _kron33(_ID3 if u is None else u, _ID3 if v is None else v)
    return np.swapaxes(m.conj(), -1, -2) @ B_CGLMP @ m


def bell_expectation(rho, u=None, v=None):
    """Tr[rho (U x V)^dag B (U x V)] for a density matrix (or stack of them)."""
    rho = np.asarray(rho)
    return np.real(np.einsum("...ij,...ji->...", rho, bell_operator(u, v)))


def i3_unrotated(rho):
    """Tr[rho B] (or stack of them), without optimisation over local unitaries."""
    return bell_expectation(rho)


def i3_from_coefficients(h):
    """Tr[rho B] from the correlation matrix h (..., 8, 8): 2302.00683 Eq. (2.40),
    4(h44 + h55) - (4/sqrt3)(h11 + h16 + h61 + h66 + h22 + h27 + h72 + h77)."""
    h = np.asarray(h, dtype=float)
    vec = (sum(h[..., a, b] for a in (0, 5) for b in (0, 5))
           + sum(h[..., a, b] for a in (1, 6) for b in (1, 6)))
    return 4.0 * (h[..., 3, 3] + h[..., 4, 4]) - 4.0 / SQRT3 * vec


def i3_weights(u=None, v=None):
    """Weights w (80,) with Tr[rho (U x V)^dag B (U x V)] = w . basis.coefficient_vector(rho).

    With the per-event estimators x of ``basis.estimator_vector``, x . w is an unbiased per-event
    estimate of the Bell expectation at fixed settings (U, V), e.g. the optimum of a reference state.
    """
    return np.real(np.einsum("kij,...ji->...k", basis.OPERATORS, bell_operator(u, v)))


# --------------------------------------------------------------------------
# Optimisation over local unitaries
# --------------------------------------------------------------------------
# Left translations U -> exp(iX) U, V -> exp(iY) V with X = x.T, Y = y.T act on U x V as
# exp(i z_a Z_a), Z = [T^a x 1, 1 x T^a].  With rho' = (U x V) rho (U x V)^dag,
#     F(z) = Tr[B rho'] + z_a Tr[G_a rho'] + (1/2) z_a z_b Tr[S_ab rho'] + O(z^3),
#     G_a = i[B, Z_a],  S_ab = -(1/2)([[B, Z_a], Z_b] + [[B, Z_b], Z_a]),
# so value, gradient and Hessian are one linear map of rho'.  Tr[O r] = Re(vec(O) . vec(r^T))
# for Hermitian O, r; the map acts on vec(rho'^T) viewed as interleaved (Re, Im) floats.
_Z = basis.OPERATORS[:16]
_CB = B_CGLMP @ _Z - _Z @ B_CGLMP
_DCB = np.einsum("aij,bjk->abik", _CB, _Z) - np.einsum("bij,ajk->abik", _Z, _CB)
_IU = np.triu_indices(16)
_OPS = np.concatenate([B_CGLMP[None], 1j * _CB, -0.5 * (_DCB + np.swapaxes(_DCB, 0, 1))[_IU]])
_LIN = np.empty((162, len(_OPS)))
_LIN[0::2], _LIN[1::2] = _OPS.reshape(-1, 81).T.real, -_OPS.reshape(-1, 81).T.imag
_LIN_VALUE = np.ascontiguousarray(_LIN[:, 0])
_T_FLAT = _T.reshape(8, 9)
_EYE16 = np.eye(16)

GTOL = 1e-9          # convergence: max |dF/dz_a| (left-trivialised gradient)
SADDLE_TOL = 1e-7    # Hessian eigenvalue above SADDLE_TOL (1 + max|eigenvalue|): saddle point
SAME_TOL = 1e-7      # starts within SAME_TOL of the best value count as having found it
N_STARTS = 48        # default number of random starts (see i3_optimise)
_MAX_ESCAPES = 10


def _rotated_flat(rho, w):
    """vec((M rho M^dag)^T) as interleaved floats (n, 162); M = U x V, w = (U, V) of shape (n, 2, 3, 3)."""
    m = _kron33(w[:, 0], w[:, 1])
    rot_t = np.conj(m) @ rho.T @ np.swapaxes(m, -1, -2)
    return np.ascontiguousarray(rot_t).reshape(-1, 81).view(np.float64)


def _value(rho, w):
    return _rotated_flat(rho, w) @ _LIN_VALUE


def _value_grad_hess(rho, w):
    out = _rotated_flat(rho, w) @ _LIN
    h = np.empty((len(out), 16, 16))
    h[:, _IU[0], _IU[1]] = h[:, _IU[1], _IU[0]] = out[:, 17:]
    return out[:, 0], out[:, 1:17], h


def _cayley(z):
    """R = (1 - iX/2)^-1 (1 + iX/2) = exp(iX) + O(X^3) for X = z[:8].T (U) and z[8:].T (V);
    z (n, 16) -> (n, 2, 3, 3)."""
    gen = (z.reshape(-1, 2, 8) @ _T_FLAT).reshape(-1, 2, 3, 3)
    return 2 * np.linalg.inv(_ID3 - 0.5j * gen) - _ID3


def _solve(a, b):
    try:
        return np.linalg.solve(a, b[..., None])[..., 0]
    except np.linalg.LinAlgError:
        return np.array([np.linalg.lstsq(ai, bi, rcond=None)[0] for ai, bi in zip(a, b)])


def _newton_batch(rho, w, gtol, max_iter):
    """Damped-Newton (Levenberg-Marquardt) ascent from every start w = (U, V) (n, 2, 3, 3) at once.

    Each iteration solves (mu - H) z = g with the exact Hessian, moves along the Cayley
    retraction and adapts mu by the ratio of actual to predicted gain.  Where the gradient
    vanishes, a positive Hessian eigenvalue (saddle point) triggers a step along its
    eigenvector.  Returns final values, (U, V), iterations and a convergence flag per start.
    """
    w = np.array(w, dtype=complex)
    n = len(w)
    f, g, h = _value_grad_hess(rho, w)
    gmax = np.abs(g).max(axis=1)
    mu = np.ones(n)
    active = np.ones(n, bool)
    converged = np.zeros(n, bool)
    escapes = np.zeros(n, int)
    nit = np.zeros(n, int)
    for _ in range(max_iter):
        flat = active & (gmax < gtol)
        if flat.any():
            j = np.flatnonzero(flat)
            lam = np.linalg.eigvalsh(h[j])
            saddle = lam[:, -1] > SADDLE_TOL * (1.0 + np.abs(lam).max(axis=1))
            converged[j[~saddle]] = True
            active[j[~saddle | (escapes[j] >= _MAX_ESCAPES)]] = False
            j = j[saddle & (escapes[j] < _MAX_ESCAPES)]
            if j.size:
                d = np.linalg.eigh(h[j])[1][:, :, -1]            # direction of positive curvature
                best_f, best_w = f[j].copy(), w[j].copy()
                for tau in (0.5, -0.5, 0.1, -0.1):
                    wn = _cayley(tau * d) @ w[j]
                    fn = _value(rho, wn)
                    up = fn > best_f
                    best_f[up], best_w[up] = fn[up], wn[up]
                active[j[best_f <= f[j]]] = False
                w[j] = best_w
                f[j], g[j], h[j] = _value_grad_hess(rho, w[j])
                gmax[j], mu[j], escapes[j] = np.abs(g[j]).max(axis=1), 1.0, escapes[j] + 1
        idx = np.flatnonzero(active & (gmax >= gtol))
        if idx.size == 0:
            if active.any():
                continue
            break
        fi, gi, hi, mi = f[idx], g[idx], h[idx], mu[idx]
        z = _solve(mi[:, None, None] * _EYE16 - hi, gi)
        pred = np.einsum("na,na->n", gi, z) + 0.5 * np.einsum("na,nab,nb->n", z, hi, z)
        wn = _cayley(z) @ w[idx]
        fn, gn, hn = _value_grad_hess(rho, wn)
        ratio = (fn - fi) / np.where(pred > 0, pred, 1.0)
        # below ~1e-13 the gain is lost in rounding: accept the (tiny) step, gtol decides
        ok = (pred > 0) & ((ratio > 1e-4) | (pred < 1e-13 * (1.0 + np.abs(fi))))
        acc = idx[ok]
        w[acc], f[acc], g[acc], h[acc] = wn[ok], fn[ok], gn[ok], hn[ok]
        gmax[acc] = np.abs(gn[ok]).max(axis=1)
        scale = np.where(ratio > 0.75, 1 / 3, np.where(ratio < 0.25, 2.0, 1.0))
        mu[idx] = np.clip(mi * np.where(ok, scale, 4.0), 1e-12, 1e12)
        nit[idx] += 1
        active[idx[~ok & (mu[idx] >= 1e12)]] = False      # no further gain to working precision
    return f, w, nit, converged


def _chart_objective(x, rho, u0, v0):
    """(-F, -grad F) in the Cayley chart U = R(X) u0, V = R(Y) v0 centred on (u0, v0), with
    R(X) = (1 - iX/2)^-1 (1 + iX/2), X = x[:8].T, Y = x[8:].T.  Exact gradient:
    dU/dx_a = i P T^a P^dag U, P = (1 - iX/2)^-1, and dF = 2 Re Tr[B dM rho M^dag]."""
    p = np.linalg.inv(_ID3 - 0.5j * (x.reshape(2, 8) @ _T_FLAT).reshape(2, 3, 3))
    u, v = (2 * p[0] - _ID3) @ u0, (2 * p[1] - _ID3) @ v0
    m = _kron33(u, v)
    k = m @ rho @ m.conj().T @ B_CGLMP
    k4 = k.reshape(3, 3, 3, 3)
    k_red = np.stack([np.einsum("ikjk->ij", k4), np.einsum("kikj->ij", k4)])      # Tr_W- K, Tr_W+ K
    gen_t = p[:, None] @ _T[None] @ np.swapaxes(p.conj(), -1, -2)[:, None]        # P T^a P^dag
    grad = -2 * np.imag(np.einsum("naij,nji->na", gen_t, k_red))
    return -np.real(np.trace(k)), -grad.ravel()


def _scipy_local(rho, u0, v0, gtol, max_iter):
    """L-BFGS-B from (u0, v0) in the chart of ``_chart_objective``; returns (F, U, V, OptimizeResult)."""
    res = minimize(_chart_objective, np.zeros(16), args=(rho, u0, v0), jac=True, method="L-BFGS-B",
                   options={"gtol": gtol, "ftol": 1e-15, "maxiter": max_iter})
    r = _cayley(res.x[None])[0]
    return -res.fun, r[0] @ u0, r[1] @ v0, res


def unitaries(x):
    """(U, V) = (exp(i x[:8].T), exp(i x[8:].T)) from the 16 parameters x (or a stack (..., 16))."""
    x = np.asarray(x, dtype=float)
    gen = (x.reshape(x.shape[:-1] + (2, 8)) @ _T_FLAT).reshape(x.shape[:-1] + (2, 3, 3))
    lam, w = np.linalg.eigh(gen)
    e = (w * np.exp(1j * lam)[..., None, :]) @ np.swapaxes(w.conj(), -1, -2)
    return e[..., 0, :, :], e[..., 1, :, :]


def parameters(u, v):
    """16 parameters x with ``unitaries(x)`` = (U, V) up to global phases (principal logarithm)."""
    out = []
    for m in (u, v):
        tri, q = schur(np.asarray(m, dtype=complex), output="complex")
        gen = (q * np.angle(np.diag(tri))) @ q.conj().T
        out.append(np.real(np.einsum("aij,ji->a", _T, gen)) / 2)     # traceless part, x_a = Tr[X T^a]/2
    return np.concatenate(out)


def _haar(rng, n):
    """n Haar-random 3x3 unitaries (QR of a complex Ginibre matrix, Mezzadri 2007)."""
    z = rng.normal(size=(n, 3, 3)) + 1j * rng.normal(size=(n, 3, 3))
    q, r = np.linalg.qr(z)
    d = np.diagonal(r, axis1=-2, axis2=-1)
    return q * (d / np.abs(d))[..., None, :]


@dataclass
class I3Result:
    """Result of ``i3_optimise``.  ``x`` are the parameters of (u, v) (see ``unitaries``);
    ``values`` holds the local maximum reached from every start (descending), ``n_best`` how
    many of them reached ``value`` (within SAME_TOL); ``gradient`` and ``curvature`` are the
    largest |gradient component| and Hessian eigenvalue at the optimum (<= ~0 at a maximum)."""
    value: float
    u: np.ndarray
    v: np.ndarray
    x: np.ndarray
    values: np.ndarray
    n_best: int
    n_starts: int
    gradient: float
    curvature: float
    converged: bool
    nit: int
    method: str


def _unitary_pair(u, v):
    """(U, V) replaced by their unitary polar factors, the nearest unitary matrices (Frobenius
    norm).  The optimiser only multiplies a start by unitaries, so a non-unitary start (rounded,
    rescaled or averaged settings) would keep its norm and inflate I3, even above I3_MAX."""
    m = np.array([u, v], dtype=complex)
    if not np.all(np.isfinite(m)):
        raise ValueError("x0: warm-start matrices must be finite")
    w, _, vh = np.linalg.svd(m)
    return w[0] @ vh[0], w[1] @ vh[1]


def _warm_starts(x0):
    """List of unitary (U, V) from x0: an I3Result, a pair (U, V), parameters (16,) or (k, 16),
    or a list of any of these.  Matrices are replaced by their nearest unitaries (``_unitary_pair``)."""
    if x0 is None or (isinstance(x0, (list, tuple)) and len(x0) == 0):
        return []
    if isinstance(x0, I3Result):
        return [_unitary_pair(x0.u, x0.v)]
    if isinstance(x0, (list, tuple)) and len(x0) == 2 and all(np.shape(m) == (3, 3) for m in x0):
        return [_unitary_pair(*x0)]
    if isinstance(x0, (list, tuple)) and not all(np.isscalar(e) for e in x0):
        return [s for e in x0 for s in _warm_starts(e)]
    x = np.asarray(x0, dtype=float)
    if x.shape[-1:] != (16,) or x.ndim > 2:
        raise ValueError("x0: expected an I3Result, (U, V), parameters (16,) or (k, 16), or a list of them")
    if not np.all(np.isfinite(x)):
        raise ValueError("x0: parameters must be finite")
    u, v = unitaries(x.reshape(-1, 16))
    return list(zip(u, v))


def i3_optimise(rho, n_starts=N_STARTS, rng=None, x0=None, full_output=False, method="newton",
                gtol=GTOL, max_iter=200):
    """I3 = max over U, V in U(3) of Tr[rho (U x V)^dag B (U x V)] (PLAN.md Sec. 3.5).

    Local maximisation from every start: the warm start(s) ``x0`` (an ``I3Result``, (U, V),
    parameters or a list of them; matrices are replaced by the nearest unitaries), the identity,
    and ``n_starts`` Haar-random (U, V) drawn from ``rng`` (a Generator or seed; default: fixed
    seed 0, i.e. reproducible).  Global phases drop out, so U and V have 8 parameters each.

    method='newton' (default): all starts at once by damped Newton with the exact gradient and
    Hessian (``_newton_batch``); the best one is then polished with scipy L-BFGS-B
    (``_chart_objective``, exact gradient).  method='scipy': L-BFGS-B from every start
    (about 20 times slower per start; independent cross-check).

    Reliability versus cost (13 classes of states x 10, global maximum from 512 starts): for
    pure states, including the SM state at fixed M*, every start reaches the global maximum.
    Mixed or reconstructed states have several local maxima, typically 0.01-0.07 below the
    global one, and one random start finds the global maximum with probability p = 0.2-1
    (p = 0.2-0.8, mean 0.4, for noisy SM states and for SM and 1/9 states reconstructed from
    2e3-2e4 toy events).  It is missed with probability ~(1-p)^n: averaged over these classes
    <~ 4e-3 for n = 16, 8e-5 for n = 32, 2e-6 for n = 48 (default) and 6e-8 for n = 64; for the
    worst state seen (p = 0.20) 3e-2, 8e-4, 2e-5 and 6e-7.  The default missed none of the 130
    states.  A miss biases I3 low.  Cost ~0.5 ms per start: n = 48 takes 20-35 ms.
    Warm starts add starting points but do not replace the random ones: the SM optimum is an
    orbit of the common rotation about k (J_z symmetry of rho and B), which a perturbation
    splits into nearly degenerate maxima, and a single warm start then misses the global
    maximum of a perturbed SM state about half of the time.  Pseudo-experiments therefore need
    the default n_starts besides the warm start: with n_starts = 4, 10 of 160 states
    reconstructed from 2e3-1e4 toy events (1/9, SM and decohered SM) missed it, by up to 0.07.

    Returns I3 (float), or an ``I3Result`` with full_output=True.
    """
    rho = np.asarray(rho, dtype=complex)
    if rho.shape != (9, 9) or not np.all(np.isfinite(rho)):
        raise ValueError("rho must be a finite 9x9 matrix")
    rho = 0.5 * (rho + rho.conj().T)
    if not isinstance(rng, np.random.Generator):
        rng = np.random.default_rng(0 if rng is None else rng)
    w0 = np.concatenate([np.array(_warm_starts(x0) + [(_ID3, _ID3)], dtype=complex).reshape(-1, 2, 3, 3),
                         _haar(rng, 2 * n_starts).reshape(n_starts, 2, 3, 3)])
    if method == "newton":
        f, w, nit, _ = _newton_batch(rho, w0, gtol, max_iter)
        b = int(np.argmax(f))
        val, ub, vb, _ = _scipy_local(rho, w[b, 0], w[b, 1], gtol, 50 * max_iter)
        if val > f[b]:
            f[b], w[b, 0], w[b, 1] = val, ub, vb
    elif method == "scipy":
        f, w, nit = np.empty(len(w0)), w0.copy(), np.zeros(len(w0), int)
        for i in range(len(w0)):
            f[i], w[i, 0], w[i, 1], res = _scipy_local(rho, w0[i, 0], w0[i, 1], gtol, 50 * max_iter)
            nit[i] = res.nit
        b = int(np.argmax(f))
    else:
        raise ValueError(f"unknown method {method!r}")
    if not full_output:
        return float(f[b])
    _, g, h = _value_grad_hess(rho, w[b:b + 1])
    lam = np.linalg.eigvalsh(h[0])
    grad, curv = float(np.abs(g).max()), float(lam[-1])
    return I3Result(value=float(f[b]), u=w[b, 0], v=w[b, 1], x=parameters(w[b, 0], w[b, 1]),
                    values=np.sort(f)[::-1], n_best=int(np.sum(f > f[b] - SAME_TOL)), n_starts=len(f),
                    gradient=grad, curvature=curv,
                    converged=bool(grad < 1e3 * gtol and curv <= SADDLE_TOL * (1.0 + np.abs(lam).max())),
                    nit=int(nit.max()), method=method)


# --------------------------------------------------------------------------
# Concurrence bound and entanglement entropy
# --------------------------------------------------------------------------
def c2_terms(rho):
    """The two unclipped arguments (Tr rho^2 - Tr rho_A^2, Tr rho^2 - Tr rho_B^2) of
    C2 = 2 max(0, ., .), A = W+, B = W- (stacks allowed)."""
    p = basis.purity(rho)
    return p - basis.purity(basis.reduced_wplus(rho)), p - basis.purity(basis.reduced_wminus(rho))


def c2(rho):
    """C2 = 2 max(0, Tr rho^2 - Tr rho_A^2, Tr rho^2 - Tr rho_B^2) (PLAN.md Sec. 3.5)."""
    t_a, t_b = c2_terms(rho)
    return 2.0 * np.maximum(0.0, np.maximum(t_a, t_b))


def c2_from_coefficients(f, g, h):
    """C2 from (f, g, h), 2302.00683 Eq. (2.39):
    2 max(0, -2/9 - 12 f.f + 6 g.g + 4 h:h, -2/9 + 6 f.f - 12 g.g + 4 h:h)."""
    f, g, h = (np.asarray(x, dtype=float) for x in (f, g, h))
    ff, gg, hh = np.sum(f * f, axis=-1), np.sum(g * g, axis=-1), np.sum(h * h, axis=(-2, -1))
    t_a = -2.0 / 9.0 - 12.0 * ff + 6.0 * gg + 4.0 * hh
    t_b = -2.0 / 9.0 + 6.0 * ff - 12.0 * gg + 4.0 * hh
    return 2.0 * np.maximum(0.0, np.maximum(t_a, t_b))


def entanglement_entropy(rho):
    """von Neumann entropy -Tr[rho_A ln rho_A] of the W+ reduced state (nats; ln 3 at most).
    The entanglement entropy for a pure state; for mixed states only a diagnostic.
    Negative eigenvalues of an unphysical rho_A are ignored."""
    lam = np.linalg.eigvalsh(basis.reduced_wplus(np.asarray(rho)))
    lam = np.where(lam > 0, lam, 1.0)           # 0 ln 0 = 0; 1 ln 1 = 0 replaces lam <= 0
    return -np.sum(lam * np.log(lam), axis=-1)


# --------------------------------------------------------------------------
# Raw and physical results (CONVENTIONS.md Sec. 6)
# --------------------------------------------------------------------------
def observables(rho, **optimise_kwargs):
    """I3 and C2 of rho as given (raw) and after projection onto the nearest physical state
    (``basis.nearest_physical``), plus the smallest eigenvalue of rho.  Keyword arguments
    go to ``i3_optimise``; the projected I3 is warm-started from the raw optimum."""
    rho = np.asarray(rho, dtype=complex)
    optimise_kwargs.pop("full_output", None)
    phys = basis.nearest_physical(rho)
    raw = i3_optimise(rho, full_output=True, **optimise_kwargs)
    kw = dict(optimise_kwargs, x0=[raw] + _warm_starts(optimise_kwargs.get("x0")))
    return {"i3": raw.value, "c2": float(c2(rho)),
            "i3_physical": i3_optimise(phys, **kw), "c2_physical": float(c2(phys)),
            "min_eigenvalue": float(basis.min_eigenvalue(rho))}
