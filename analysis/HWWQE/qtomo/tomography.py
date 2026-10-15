"""Moment estimators of the 80 Gell-Mann coefficients, their covariance and unbiased
quadratic invariants (PLAN.md Sec. 3.3, 3.5 and 4; CONVENTIONS.md Sec. 2, 3 and 6).

Every event gives the unbiased estimator x = basis.estimator_vector(...) of the coefficient
vector c (``basis.pack`` order; f = <p+>/6, g = <p->/6, h = <p+ p-^T>/4), with the per-leg
mistag correction of CONVENTIONS.md Sec. 3 when rates are given.  With event weights w (e.g. the
reweighting of PLAN.md Sec. 3.7; w = 1 by default)

    c     = sum w x / sum w,
    cov   = sum w^2 (x - c)(x - c)^T / (sum w)^2      (linearised ratio estimator),
    n_eff = (sum w)^2 / sum w^2.

The squares c_k^2 are estimated without the plug-in bias (+cov_kk) by the U-statistic

    [(sum w x_k)^2 - sum w^2 x_k^2] / [(sum w)^2 - sum w^2],

the (w_i w_j)-weighted mean of x_ik x_jk over pairs i != j, exactly unbiased for unit weights
(for random weights a ratio of unbiased U-statistics, with a bias of order c/N_eff).  The
purities Tr rho^2 = 1/9 + 6 sum f^2 + 6 sum g^2 + 4 sum h^2, Tr rho_A^2 = 1/3 + 18 sum f^2 and
Tr rho_B^2 = 1/3 + 18 sum g^2 (A = W+, B = W-) are linear in the squares, hence so are their
unbiased estimates and those of both arguments of the max in C2 (CONVENTIONS.md Sec. 6).
Their standard deviations come from ``invariant_sigma`` for estimates from data (conservative
near c = 0) and from ``expected_invariant_sigma`` for the exact moments of a hypothesis.

All sums are additive: ``MomentAccumulator`` objects filled in chunks or in separate jobs merge
exactly.
"""
import operator
import os
from dataclasses import dataclass
from typing import NamedTuple

import numpy as np

from . import basis

CHUNK = 100_000     # events per call of basis.estimator_vector: (CHUNK, 80) floats in memory
N = basis.N_COEFF
_F, _G = slice(0, 8), slice(8, 16)


# --------------------------------------------------------------------------
# Quadratic invariants
# --------------------------------------------------------------------------
class Invariants(NamedTuple):
    """Quadratic invariants of rho; A = W+, B = W- (CONVENTIONS.md Sec. 6).
    C2 = 2 max(0, c2_arg_wplus, c2_arg_wminus)."""
    purity: float           # Tr rho^2
    purity_wplus: float     # Tr rho_A^2
    purity_wminus: float    # Tr rho_B^2
    c2_arg_wplus: float     # Tr rho^2 - Tr rho_A^2
    c2_arg_wminus: float    # Tr rho^2 - Tr rho_B^2


# invariant_j = _INV_CONST[j] + _INV_WEIGHTS[j] . (c_k^2)_k
_INV_CONST = np.array([1 / 9, 1 / 3, 1 / 3, -2 / 9, -2 / 9])
_INV_WEIGHTS = np.zeros((5, N))
_INV_WEIGHTS[0] = basis.NORMS           # Tr[O_k O_l] = NORMS_k delta_kl, Tr O_k = 0
_INV_WEIGHTS[1, _F] = 18.0              # rho_A = 1/3 + 3 f_a T^a, Tr[T^a T^b] = 2 delta_ab
_INV_WEIGHTS[2, _G] = 18.0
_INV_WEIGHTS[3] = _INV_WEIGHTS[0] - _INV_WEIGHTS[1]
_INV_WEIGHTS[4] = _INV_WEIGHTS[0] - _INV_WEIGHTS[2]


def quadratic_invariants(c_sq):
    """Invariants from the squares c_k^2: exact squares, or their U-statistic (unbiased) or
    plug-in (c_hat^2) estimates."""
    return Invariants(*map(float, _INV_CONST + _INV_WEIGHTS @ np.asarray(c_sq, dtype=float)))


def _lin_quad(c, cov):
    """(a o c)^T cov (a o c) and a^T (cov o cov) a for the weight vectors a of the five
    invariants (o = elementwise product)."""
    cov = np.asarray(cov, dtype=float)
    ac = _INV_WEIGHTS * np.asarray(c, dtype=float)
    return (np.einsum("jk,kl,jl->j", ac, cov, ac),
            np.einsum("jk,kl,jl->j", _INV_WEIGHTS, cov * cov, _INV_WEIGHTS))


def invariant_sigma(c, cov):
    """Standard deviations of the unbiased invariants, estimated from data: ``c`` and ``cov`` are
    the coefficient estimates and their covariance (``Result.c``, ``Result.cov``).

    For N unit-weight events the variance of sum_k a_k U_k is 4 (a o c)^T cov (a o c)
    + 2 a^T (cov o cov) a N/(N-1) (Hoeffding decomposition, ``expected_invariant_sigma``).
    With the estimate c_hat the first term is biased by +4 a^T (cov o cov) a, which is
    subtracted, and the variance is floored at its value for c = 0, 2 a^T (cov o cov) a.
    The result is close to the true standard deviation where |a o c| is large compared with its
    precision (SM states: a few per cent low at N ~ 500, from the square root), but conservative
    near c = 0, where the floor acts: at rho = 1/9 its mean is about 10% (Tr rho^2, C2 arguments)
    to 18% (Tr rho_A^2, Tr rho_B^2) above the true value, for any N (tests/test_tomography.py).
    For null hypotheses and significances use pseudo-experiments (PLAN.md rule 4) or
    ``expected_invariant_sigma``.  Approximate for weighted events.  Not meant for exact
    moments: with the true c it would still subtract the bias term.
    """
    lin, quad = _lin_quad(c, cov)
    return Invariants(*map(float, np.sqrt(2.0 * quad + np.maximum(0.0, 4.0 * lin - 4.0 * quad))))


def expected_invariant_sigma(mean, cov, n_events):
    """Exact standard deviations of the unbiased invariants of ``n_events`` unweighted events,
    from the exact per-event mean and covariance of the estimator vector (``expected_moments``,
    with or without mistag):

        Var = 4 (a o c)^T cov (a o c) / N + 2 a^T (cov o cov) a / (N (N - 1)),

    the Hoeffding decomposition of the U-statistic sum_k a_k U_k, exact for N >= 2 (ideal
    statistical reach, PLAN.md Sec. 4).  For estimates from data use ``invariant_sigma``.
    """
    n = float(n_events)
    if not n >= 2.0:
        raise ValueError("n_events must be at least 2")
    lin, quad = _lin_quad(mean, cov)
    return Invariants(*map(float, np.sqrt(4.0 * lin / n + 2.0 * quad / (n * (n - 1.0)))))


# --------------------------------------------------------------------------
# Result and accumulator
# --------------------------------------------------------------------------
@dataclass(frozen=True, repr=False)
class Result:
    """Moment-estimator tomography of one sample.

    c, cov             coefficient estimates (80, ``basis.pack`` order) and their covariance
    c_sq               unbiased (U-statistic) estimates of c_k^2
    n_events, sum_w    number of events and sum of weights; n_eff = (sum w)^2 / sum w^2
    rho                basis.density_matrix of the raw estimates (may have negative eigenvalues)
    rho_physical       basis.nearest_physical(rho); quote both (PLAN.md Sec. 3.5)
    min_eigenvalue     smallest eigenvalue of rho
    invariants         unbiased Tr rho^2, Tr rho_A^2, Tr rho_B^2 and C2 arguments
    invariants_plugin  the same from c_hat^2 (= the values of the raw rho)
    invariants_sigma   standard deviations of ``invariants`` estimated from the sample
                       (``invariant_sigma``: conservative near c = 0)
    """
    c: np.ndarray
    cov: np.ndarray
    c_sq: np.ndarray
    n_events: int
    sum_w: float
    n_eff: float
    rho: np.ndarray
    rho_physical: np.ndarray
    min_eigenvalue: float
    invariants: Invariants
    invariants_plugin: Invariants
    invariants_sigma: Invariants

    @property
    def f(self):
        return basis.unpack(self.c)[0]

    @property
    def g(self):
        return basis.unpack(self.c)[1]

    @property
    def h(self):
        return basis.unpack(self.c)[2]

    @property
    def sigma(self):
        return np.sqrt(np.diag(self.cov))

    def __repr__(self):
        return (f"Result(n_events={self.n_events}, n_eff={self.n_eff:.1f}, "
                f"min_eigenvalue={self.min_eigenvalue:.3g})")


def _positive_int(value, name):
    value = operator.index(value)
    if value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _per_event(value, n, name, rate=False):
    """A finite float or one finite value per event; mistag rates (``rate``) in [0, 1]."""
    if value is None:
        return None
    arr = np.asarray(value, dtype=float)
    if arr.ndim:
        arr = arr.ravel()
        if arr.size != n:
            raise ValueError(f"{name} must be a scalar or have one entry per event")
    if rate and not np.all((arr >= 0.0) & (arr <= 1.0)):      # also rejects nan
        raise ValueError(f"{name} must lie in [0, 1]")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must be finite")
    return arr if arr.ndim else float(arr)


def _part(value, sl):
    return value[sl] if np.ndim(value) else value


class MomentAccumulator:
    """Chunked, mergeable sums for the (weighted) moment estimator.

    Holds n_events, sum w, sum w^2, sum w x, sum w^2 x and sum w^2 x x^T of the per-event
    estimator vectors x; everything in the module docstring follows from these.  Accumulators
    merge with ``merge`` / ``+`` / ``+=`` and persist with ``save`` / ``load`` (npz).
    """
    _SCALARS = ("n_events", "sum_w", "sum_w2")
    _ARRAYS = ("sum_wx", "sum_w2x", "sum_w2xx")

    def __init__(self):
        self.n_events = 0
        self.sum_w = 0.0
        self.sum_w2 = 0.0
        self.sum_wx = np.zeros(N)
        self.sum_w2x = np.zeros(N)
        self.sum_w2xx = np.zeros((N, N))

    def add(self, theta_p, phi_p, theta_m, phi_m, *, weights=None, mistag_p=0.0, mistag_m=0.0,
            chunk=CHUNK):
        """Add events given by their analyser angles, which must be finite (frames.py gives nan
        where no rest frame is defined: select finite events first).  ``weights``, ``mistag_p``
        and ``mistag_m`` (the W+ / W- flip probabilities in [0, 1], CONVENTIONS.md Sec. 3) are
        scalars or per-event arrays.  They are keyword-only, so that a tuple with more fields
        (e.g. toy.SMEvents, whose masses come first) cannot be unpacked into the arguments.
        Evaluated in chunks of ``chunk`` events."""
        angles = [np.ravel(np.asarray(a, dtype=float)) for a in (theta_p, phi_p, theta_m, phi_m)]
        n = angles[0].size
        if any(a.size != n for a in angles):
            raise ValueError("the four angle arrays must have the same length")
        if not all(np.all(np.isfinite(a)) for a in angles):
            raise ValueError("angles must be finite (select events with a defined frame)")
        chunk = _positive_int(chunk, "chunk")
        weights = _per_event(weights, n, "weights")
        mistag_p = _per_event(mistag_p, n, "mistag_p", rate=True)
        mistag_m = _per_event(mistag_m, n, "mistag_m", rate=True)
        for start in range(0, n, chunk):
            sl = slice(start, start + chunk)
            x = basis.estimator_vector(*(a[sl] for a in angles), _part(mistag_p, sl),
                                       _part(mistag_m, sl))
            self.add_vectors(x, _part(weights, sl))
        return self

    def add_vectors(self, x, weights=None):
        """Add per-event estimator vectors x (n, 80) directly, with optional weights."""
        x = np.asarray(x, dtype=float).reshape(-1, N)
        self.n_events += len(x)
        if weights is None:
            s = x.sum(axis=0)
            self.sum_w += len(x)
            self.sum_w2 += len(x)
            self.sum_wx += s
            self.sum_w2x += s
            self.sum_w2xx += x.T @ x
        else:
            w = np.broadcast_to(np.asarray(weights, dtype=float), (len(x),))
            if not np.all(np.isfinite(w)):
                raise ValueError("weights must be finite")
            xw = x * w[:, None]
            self.sum_w += w.sum()
            self.sum_w2 += w @ w
            self.sum_wx += xw.sum(axis=0)
            self.sum_w2x += w @ xw
            self.sum_w2xx += xw.T @ xw
        return self

    # merging and persistence ----------------------------------------------
    def merge(self, other):
        """Add the sums of another accumulator (in place); returns self."""
        for key in self._SCALARS + self._ARRAYS:
            setattr(self, key, getattr(self, key) + getattr(other, key))
        return self

    __iadd__ = merge

    def __add__(self, other):
        return self.copy().merge(other)

    def state(self):
        """The sums as a dict of numpy arrays (copies)."""
        return {key: np.array(getattr(self, key)) for key in self._SCALARS + self._ARRAYS}

    @classmethod
    def from_state(cls, state):
        acc = cls()
        acc.n_events = int(state["n_events"])
        acc.sum_w = float(state["sum_w"])
        acc.sum_w2 = float(state["sum_w2"])
        for key in cls._ARRAYS:
            acc_shape = getattr(acc, key).shape
            setattr(acc, key, np.array(state[key], dtype=float).reshape(acc_shape))
        return acc

    def copy(self):
        return self.from_state(self.state())

    @staticmethod
    def _npz_path(path):
        """``path`` with '.npz' appended unless it already ends so (the rule of np.savez)."""
        path = os.fspath(path)
        return path if path.endswith(".npz") else path + ".npz"

    def save(self, path):
        """Write the sums to ``path`` as npz ('.npz' appended if missing, as in ``load``)."""
        np.savez(self._npz_path(path), **self.state())

    @classmethod
    def load(cls, path):
        """Read sums written by ``save`` ('.npz' appended if missing)."""
        with np.load(cls._npz_path(path)) as data:
            return cls.from_state(data)

    # estimates -------------------------------------------------------------
    @property
    def n_eff(self):
        return self.sum_w ** 2 / self.sum_w2

    @property
    def mean(self):
        """Coefficient estimates c = sum w x / sum w."""
        return self.sum_wx / self.sum_w

    @property
    def cov(self):
        """sum w^2 (x - c)(x - c)^T / (sum w)^2, expanded in the stored sums."""
        c = self.mean
        m = (self.sum_w2xx - np.outer(c, self.sum_w2x) - np.outer(self.sum_w2x, c)
             + self.sum_w2 * np.outer(c, c))
        return m / self.sum_w ** 2

    @property
    def c_sq(self):
        """U-statistic estimates of c_k^2 (NaN for fewer than two events)."""
        den = self.sum_w ** 2 - self.sum_w2
        if not den > 0:
            return np.full(N, np.nan)
        return (self.sum_wx ** 2 - np.diag(self.sum_w2xx)) / den

    def result(self):
        if self.n_events == 0 or not self.sum_w > 0:
            raise ValueError("no events, or a non-positive sum of weights, accumulated")
        c, cov, c_sq = self.mean, self.cov, self.c_sq
        rho = basis.density_matrix(*basis.unpack(c))
        return Result(c=c, cov=cov, c_sq=c_sq, n_events=int(self.n_events),
                      sum_w=float(self.sum_w), n_eff=float(self.n_eff), rho=rho,
                      rho_physical=basis.nearest_physical(rho),
                      min_eigenvalue=float(basis.min_eigenvalue(rho)),
                      invariants=quadratic_invariants(c_sq),
                      invariants_plugin=quadratic_invariants(c ** 2),
                      invariants_sigma=invariant_sigma(c, cov))


def estimate(theta_p, phi_p, theta_m, phi_m, *, weights=None, mistag_p=0.0, mistag_m=0.0,
             chunk=CHUNK):
    """Moment-estimator tomography of one sample (PLAN.md Sec. 3.3); returns a ``Result``.
    Arguments as in ``MomentAccumulator.add``: estimate(*angles) for a toy.Angles,
    estimate(*events.angles) for a toy.SMEvents."""
    return MomentAccumulator().add(theta_p, phi_p, theta_m, phi_m, weights=weights,
                                   mistag_p=mistag_p, mistag_m=mistag_m, chunk=chunk).result()


# --------------------------------------------------------------------------
# Exact moments (ideal statistical reach, PLAN.md Sec. 4)
# --------------------------------------------------------------------------
def expected_moments(rho, mistag_p=0.0, mistag_m=0.0, *, correct_p=None, correct_m=None,
                     n_cos=8, n_phi=16):
    """Exact per-event mean (80,) and covariance (80, 80) of the estimator vector for events
    from (3/4pi)^2 Tr[rho (Pi+ x Pi-)] whose W+ / W- analysers are flipped with probabilities
    mistag_p / mistag_m and corrected with the rates correct_p / correct_m (scalars in [0, 1];
    by default the flip rates, which gives mean = c).  A correction rate of 0 gives the
    uncorrected estimator, mean = D(w) c (``basis.mistag_dilution``), also at w = 1/2 where no
    correction exists; its rank-(2,2) entries (e.g. h44, h55) do not depend on the flips.

    For N unweighted events the covariance of the estimate is cov / N and the standard
    deviations of the unbiased invariants are ``expected_invariant_sigma(mean, cov, N)``.
    Product quadrature (``basis.sphere_quadrature``) on both spheres, exact because the
    integrands are polynomials of degree <= 6 on each sphere (needs n_cos >= 4, n_phi >= 7).
    """
    rates = (mistag_p, mistag_m, mistag_p if correct_p is None else correct_p,
             mistag_m if correct_m is None else correct_m)
    if any(np.ndim(r) for r in rates):
        raise ValueError("expected_moments takes scalar flip and correction rates")
    w_p, w_m, k_p, k_m = (float(r) for r in rates)
    if not all(0.0 <= r <= 1.0 for r in (w_p, w_m, k_p, k_m)):
        raise ValueError("flip and correction rates must lie in [0, 1]")
    th, ph, wt = basis.sphere_quadrature(n_cos, n_phi)
    tp, tm = np.repeat(th, th.size), np.tile(th, th.size)
    pp, pm = np.repeat(ph, ph.size), np.tile(ph, ph.size)
    prob = ((3 / (4 * np.pi)) ** 2 * np.outer(wt, wt).ravel()
            * basis.trace_projectors(rho, tp, pp, tm, pm))
    mean, second = np.zeros(N), np.zeros((N, N))
    for flip_p, prob_p in ((False, 1.0 - w_p), (True, w_p)):
        for flip_m, prob_m in ((False, 1.0 - w_m), (True, w_m)):
            if prob_p * prob_m == 0.0:
                continue
            ap = basis.antipode(tp, pp) if flip_p else (tp, pp)
            am = basis.antipode(tm, pm) if flip_m else (tm, pm)
            x = basis.estimator_vector(*ap, *am, k_p, k_m)
            w = prob_p * prob_m * prob
            mean += w @ x
            second += x.T @ (w[:, None] * x)
    return mean, second - np.outer(mean, mean)
