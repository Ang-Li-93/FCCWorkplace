"""Toy generator of the W+ W- decay angles (PLAN.md Sec. 3.6) and analyser mistag.

Events (Omega+, Omega-) follow the decay distribution of CONVENTIONS.md Sec. 2,

    (1/sigma) dsigma / dOmega+ dOmega- = (3/4pi)^2 Tr[rho (Pi+ x Pi-)],

sampled by accept-reject: both directions uniform on the sphere (density 1/(4pi)^2), accepted
with probability Tr[rho (Pi+ x Pi-)] = ``basis.trace_projectors``, which lies in [0, 1] for a
physical rho (the plan's bound 9/(4pi)^2 on the density).  Averaged over the proposals the
acceptance is Tr[rho (1/3 x 1/3)] = 1/9 for every rho, so the efficiency is exactly 1/9.

Angles follow ``basis``: theta in [0, pi] w.r.t. k, phi in [0, 2pi) w.r.t. n (CONVENTIONS.md
Sec. 4).  Every sampler returns per-event arrays; the first n accepted proposals of an iid
stream form an exact iid sample, so chunking does not bias anything.  Invalid input
(non-finite or unphysical states, sizes that are not integers) raises before any loop starts.
"""
import operator
from typing import NamedTuple

import numpy as np

from . import basis, sm

CHUNK = 250_000         # proposals (or events) per vectorised step
_WEIGHT_BLOCK = 50_000  # events per block when building per-event SM weights
_TOL = 1e-9             # rounding tolerance on Tr[rho (Pi+ x Pi-)], Tr rho and Hermiticity

# Tree-level SM states used as the affine basis of the family rho_SM(kappa), see ``sm_weights``.
SM_REFERENCE_KAPPA = (1.0, 2.0, 20.0)


class Angles(NamedTuple):
    """Analyser directions of the W+ (theta_p, phi_p) and the W- (theta_m, phi_m)."""
    theta_p: np.ndarray
    phi_p: np.ndarray
    theta_m: np.ndarray
    phi_m: np.ndarray


class SMEvents(NamedTuple):
    """SM toy events with the W* mass spectrum: both W masses (GeV) and the angles.
    Estimate them with tomography.estimate(*events.angles)."""
    m_p: np.ndarray
    m_m: np.ndarray
    theta_p: np.ndarray
    phi_p: np.ndarray
    theta_m: np.ndarray
    phi_m: np.ndarray

    @property
    def angles(self):
        return Angles(self.theta_p, self.phi_p, self.theta_m, self.phi_m)


# --------------------------------------------------------------------------
# Checks (written so that nan fails them: a nan acceptance would never accept)
# --------------------------------------------------------------------------
def _size(value, name, minimum=0):
    """An integer >= minimum; a float such as 1e3 raises TypeError."""
    value = operator.index(value)
    if value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _check_state(rho):
    rho = np.asarray(rho, dtype=complex)
    if rho.shape != (9, 9):
        raise ValueError(f"rho must be a 9x9 matrix, got shape {rho.shape}")
    if not (np.all(np.isfinite(rho)) and np.abs(rho - rho.conj().T).max() <= _TOL
            and abs(np.trace(rho) - 1.0) <= _TOL):
        raise ValueError("rho must be finite and Hermitian with unit trace")
    return rho


def _check_probability(prob):
    if not np.all((prob >= -_TOL) & (prob <= 1.0 + _TOL)):
        raise ValueError(f"Tr[rho (Pi+ x Pi-)] reaches [{np.min(prob):.3g}, {np.max(prob):.3g}], "
                         "outside [0, 1]: rho is not a physical state")
    return prob


# --------------------------------------------------------------------------
# Samplers
# --------------------------------------------------------------------------
def uniform_directions(n, rng):
    """n isotropic directions: cos(theta) uniform in [-1, 1], phi uniform in [0, 2pi)."""
    return np.arccos(rng.uniform(-1.0, 1.0, n)), rng.uniform(0.0, 2 * np.pi, n)


def isotropic(n, rng):
    """Exact sample for rho = 1/9: independent isotropic analysers on both legs."""
    return Angles(*uniform_directions(n, rng), *uniform_directions(n, rng))


def generate(rho, n, rng, chunk=CHUNK, return_efficiency=False):
    """Exact sample of n events from (3/4pi)^2 Tr[rho (Pi+ x Pi-)] (PLAN.md Sec. 3.6).

    Accept-reject in steps of at most ``chunk`` proposals.  Raises ValueError if rho is not
    finite, Hermitian and unit-trace, or if the acceptance probability leaves [0, 1] beyond
    rounding on any proposal (unphysical rho).  With ``return_efficiency`` the result is
    (Angles, accepted / proposed) over all proposals made (expectation 1/9).
    """
    rho = _check_state(rho)
    n, chunk = _size(n, "n"), _size(chunk, "chunk", 1)
    parts, have, n_prop = [], 0, 0
    while have < n:
        m = int(min(chunk, 1.2 * 9 * (n - have) + 1000))
        tp, pp = uniform_directions(m, rng)
        tm, pm = uniform_directions(m, rng)
        prob = _check_probability(basis.trace_projectors(rho, tp, pp, tm, pm))
        keep = rng.uniform(size=m) < prob
        parts.append((tp[keep], pp[keep], tm[keep], pm[keep]))
        have += int(keep.sum())
        n_prop += m
    out = Angles(*(np.concatenate([np.empty(0)] + [p[i] for p in parts])[:n] for i in range(4)))
    if return_efficiency:
        return out, (have / n_prop if n_prop else np.nan)
    return out


def _affine_trace(states, weights, theta_p, phi_p, theta_m, phi_m):
    """sum_j weights[:, j] basis.trace_projectors(states[j], ...) per event, for rows of weights
    summing to one: the same expression, 1/9 + f.q+ + g.q- + q+.h.q- (CONVENTIONS.md Sec. 2),
    with the q functions evaluated once for all states instead of once per state."""
    f, g, h = basis.coefficients(states)                                # (m, 8), (m, 8), (m, 8, 8)
    m = len(f)
    qp = basis.q_functions(theta_p, phi_p, +1)
    qm = basis.q_functions(theta_m, phi_m, -1)
    qp_h = (qp @ h.transpose(1, 0, 2).reshape(8, 8 * m)).reshape(-1, m, 8)   # q+.h_j
    per_state = qp @ f.T + qm @ g.T + np.einsum("njb,nb->nj", qp_h, qm)
    return 1.0 / 9.0 + np.einsum("nj,nj->n", weights, per_state)


def generate_per_event(states, weights, rng, chunk=CHUNK):
    """Exact sample with a state per event: event i is drawn from
    rho_i = sum_j weights[i, j] states[j].

    The rows of ``weights`` (n, m) sum to one; entries may be negative (affine, not convex,
    combination) as long as every rho_i is physical.  Each event is re-proposed until accepted,
    with probability Tr[rho_i (Pi+ x Pi-)] = sum_j weights[i, j] basis.trace_projectors(states[j],
    ...), evaluated with the q functions shared between the states (``_affine_trace``); the same
    checks as in ``generate`` apply, and the weights must be finite.
    """
    states = np.array([_check_state(s) for s in states])
    weights = np.atleast_2d(np.asarray(weights, dtype=float))
    if weights.ndim != 2 or weights.shape[1] != len(states):
        raise ValueError("weights must have shape (n, number of states)")
    if not np.all(np.isfinite(weights)):
        raise ValueError("weights must be finite")
    if not np.all(np.abs(weights.sum(axis=1) - 1.0) <= _TOL):
        raise ValueError("each row of weights must sum to one")
    chunk = _size(chunk, "chunk", 1)
    n = len(weights)
    out = np.empty((4, n))
    for start in range(0, n, chunk):
        pending = np.arange(start, min(start + chunk, n))
        while pending.size:
            tp, pp = uniform_directions(pending.size, rng)
            tm, pm = uniform_directions(pending.size, rng)
            prob = _check_probability(_affine_trace(states, weights[pending], tp, pp, tm, pm))
            keep = rng.uniform(size=pending.size) < prob
            out[:, pending[keep]] = tp[keep], pp[keep], tm[keep], pm[keep]
            pending = pending[~keep]
    return Angles(*out)


def affine_weights(states, targets):
    """Weights w (n, m), rows summing to one, with sum_j w[i, j] states[j] equal to the state of
    coefficient vector targets[i] (``basis.pack`` order).  Raises ValueError if a target is not
    finite or lies outside the affine span of the states."""
    ref = basis.coefficient_vector(np.asarray(states))           # (m, 80)
    targets = np.atleast_2d(np.asarray(targets, dtype=float))     # (n, 80)
    if not np.all(np.isfinite(targets)):
        raise ValueError("target coefficients must be finite")
    span = (ref[1:] - ref[0]).T                                   # (80, m - 1)
    sol = np.linalg.pinv(span) @ (targets - ref[0]).T             # (m - 1, n)
    if not np.all(np.abs(targets - ref[0] - (span @ sol).T) <= _TOL):
        raise ValueError("target state outside the affine span of the reference states")
    return np.column_stack([1.0 - sol.sum(axis=0), sol.T])


def sm_weights(kappa):
    """Reference states rho_SM(SM_REFERENCE_KAPPA) (3, 9, 9) and weights (n, 3) such that
    rho_SM(kappa_i) = sum_j w[i, j] rho_SM(SM_REFERENCE_KAPPA[j]) exactly.

    All coefficients of rho_SM(kappa) are linear in (1/d, kappa/d, kappa^2/d), d = 2 + kappa^2,
    with 2/d + kappa^2/d = 1 (CONVENTIONS.md Sec. 5): the tree-level states form a
    two-dimensional affine family and three of them span it.  ``affine_weights`` verifies this.
    kappa must be finite (it is infinite for a zero W mass).
    """
    states = sm.density_matrix(np.array(SM_REFERENCE_KAPPA))
    kappa = np.atleast_1d(np.asarray(kappa, dtype=float))
    if not np.all(np.isfinite(kappa)):
        raise ValueError("kappa must be finite (both W masses positive)")
    blocks = [affine_weights(states, basis.pack(*sm.coefficients(kappa[i:i + _WEIGHT_BLOCK])))
              for i in range(0, kappa.size, _WEIGHT_BLOCK)]
    return states, np.concatenate([np.empty((0, len(states)))] + blocks)


def generate_sm_spectrum(n, rng, spectrum, m_H=None, chunk=CHUNK):
    """n tree-level SM events with the off-shell W* spectrum (PLAN.md Sec. 3.4).

    The masses (M_W+, M_W-) come from ``spectrum.sample`` (sm.OffShellSpectrum); the angles of
    each event are drawn exactly from rho_SM(kappa_i), kappa_i = sm.kappa(m_H, M_W+, M_W-),
    with ``generate_per_event``.  ``m_H`` defaults to ``spectrum.m_H``.  Returns SMEvents.
    """
    n = _size(n, "n")
    if n == 0:
        return SMEvents(*(np.empty(0) for _ in range(6)))
    m_H = spectrum.m_H if m_H is None else m_H
    m_p, m_m = spectrum.sample(n, rng)
    states, weights = sm_weights(sm.kappa(m_H, m_p, m_m))
    return SMEvents(m_p, m_m, *generate_per_event(states, weights, rng, chunk))


# --------------------------------------------------------------------------
# Analyser mistag and pseudo-experiments
# --------------------------------------------------------------------------
def apply_mistag(theta, phi, w, rng):
    """Flip each analyser direction (n -> -n, ``basis.antipode``) with probability w (scalar
    or per event, in [0, 1]), e.g. the d/u-type confusion of a hadronic W (CONVENTIONS.md
    Sec. 3).  Returns (theta, phi, flipped)."""
    theta = np.asarray(theta, dtype=float)
    phi = np.asarray(phi, dtype=float)
    w = np.broadcast_to(np.asarray(w, dtype=float), theta.shape)
    if not np.all((w >= 0.0) & (w <= 1.0)):
        raise ValueError("mistag rates must lie in [0, 1]")
    flipped = rng.uniform(size=theta.shape) < w
    theta_f, phi_f = basis.antipode(theta, phi)
    return np.where(flipped, theta_f, theta), np.where(flipped, phi_f, phi), flipped


def _like(template, arrays):
    return type(template)(*arrays) if hasattr(template, "_fields") else tuple(arrays)


def pseudo_experiments(sample, n_events, n_toys, rng, poisson=False, batch=1_000_000):
    """Yield n_toys independent pseudo-experiments.

    ``sample(n, rng)`` returns a tuple of per-event arrays, e.g. ``isotropic``,
    ``functools.partial(generate, rho)`` or ``functools.partial(generate_sm_spectrum,
    spectrum=spectrum)``; each toy has the same type (an SMEvents toy is estimated with
    tomography.estimate(*toy.angles)).  Events are generated in batches of at most ``batch``
    (more if a single toy needs it, never more than the remaining toys need) and split into
    consecutive blocks of n_events (Poisson-distributed sizes of mean n_events if ``poisson``).
    """
    n_toys = _size(n_toys, "n_toys")
    if not n_events >= 0:
        raise ValueError("n_events must be non-negative")
    sizes = rng.poisson(n_events, n_toys) if poisson else np.full(n_toys, int(n_events))
    remaining = int(np.sum(sizes))
    pool, pos = None, 0
    for size in sizes:
        have = 0 if pool is None else len(pool[0]) - pos
        if pool is None or size > have:
            fresh = sample(max(min(int(batch), remaining - have), int(size - have)), rng)
            pool = fresh if pool is None else _like(
                fresh, [np.concatenate([old[pos:], new]) for old, new in zip(pool, fresh)])
            pos = 0
        yield _like(pool, [a[pos:pos + size] for a in pool])
        pos += size
        remaining -= size
