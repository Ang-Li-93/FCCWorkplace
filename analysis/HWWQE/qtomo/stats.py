"""Bootstrap, pseudo-experiment p-values, significances and error propagation
(PLAN.md rule 4 and Sec. 6.3 items 5-6).

* Poisson bootstrap: every event enters a replica with an independent
  Poisson(1) weight, the model of the pseudo-experiments of Sec. 6.3 item 6
  (the total count fluctuates as in data).  ``poisson_weights`` yields the
  weights chunk by chunk, identical for any chunking, so samples that do not fit
  in memory can be bootstrapped (``poisson_bootstrap_sums`` for linear statistics).
* p-values from null pseudo-experiments use p = (1 + #{null at least as extreme})
  / (1 + N_null), never zero; significances are one-sided, Z = Phi^-1(1 - p).
"""
from typing import NamedTuple

import numpy as np
from scipy import stats as _st

CHUNK = 100_000


# --------------------------------------------------------------------------
# Bootstrap
# --------------------------------------------------------------------------
def poisson_weights(rng, n_events, n_boot, chunk=CHUNK, mean=1.0):
    """Yield (slice, w) over consecutive chunks of events; w has shape
    (n_chunk, n_boot) with w[i, r] ~ Poisson(mean) the weight of event i in replica r.

    The weights are drawn in event order, so the concatenated stream does not
    depend on the chunking (tests/test_stats.py).  A chunk holds at most ``chunk``
    events and about 4e6 weights.  ``mean`` != 1 scales the expected yield of every
    replica, e.g. to a different integrated luminosity.
    """
    step = max(1, min(chunk, 4_000_000 // max(n_boot, 1)))
    for start in range(0, n_events, step):
        stop = min(start + step, n_events)
        yield slice(start, stop), rng.poisson(mean, size=(stop - start, n_boot))


def bootstrap(stat_fn, arrays, n_boot, rng, method="poisson"):
    """Bootstrap replicas of a statistic of per-event arrays; returns an array (n_boot, ...).

    ``arrays``: one array or a sequence of arrays sharing their length along axis 0.
    method 'poisson':  stat_fn(*arrays, weights=w) with w ~ Poisson(1) per event
                       (stat_fn must accept a ``weights`` keyword, e.g. np.average);
    method 'resample': stat_fn(*resampled_arrays), resampling events with replacement.
    """
    if isinstance(arrays, np.ndarray):
        arrays = (arrays,)
    arrays = tuple(np.asarray(a) for a in arrays)
    n = len(arrays[0])
    if any(len(a) != n for a in arrays):
        raise ValueError("bootstrap: arrays must share their length along axis 0")
    out = []
    for _ in range(n_boot):
        if method == "poisson":
            out.append(stat_fn(*arrays, weights=rng.poisson(1.0, n)))
        elif method == "resample":
            idx = rng.integers(0, n, n)
            out.append(stat_fn(*(a[idx] for a in arrays)))
        else:
            raise ValueError(f"unknown bootstrap method {method!r}")
    return np.asarray(out)


def poisson_bootstrap_sums(values, n_events, n_boot, rng, weights=None, chunk=CHUNK, mean=1.0):
    """Replica sums S[r] = sum_i u_ir v_i with u_ir = Poisson(mean) x weights_i.

    ``values``: per-event values, an array (n, k) or a callable values(slice) -> (m, k)
    so that the (n, k) array is never built.  Returns (n_boot, k).  Non-linear
    statistics (unfolded coefficients, I3, C2, ...) are then evaluated replica by replica.
    """
    total = None
    for sl, u in poisson_weights(rng, n_events, n_boot, chunk, mean):
        v = values(sl) if callable(values) else np.asarray(values)[sl]
        v = np.asarray(v, dtype=float).reshape(sl.stop - sl.start, -1)
        if weights is not None:
            v = v * np.asarray(weights, dtype=float)[sl, None]
        part = u.T @ v
        total = part if total is None else total + part
    return total


class Summary(NamedTuple):
    mean: np.ndarray
    std: np.ndarray
    median: np.ndarray
    q16: np.ndarray
    q84: np.ndarray
    n: int


def summarise(values):
    """Mean, standard deviation (ddof = 1), median, 16% and 84% quantiles and count
    of replica or pseudo-experiment values, along axis 0."""
    v = np.asarray(values, dtype=float)
    q16, med, q84 = np.quantile(v, [0.16, 0.5, 0.84], axis=0)
    std = v.std(axis=0, ddof=1) if len(v) > 1 else np.full(v.shape[1:], np.nan)
    return Summary(v.mean(axis=0), std, med, q16, q84, len(v))


# --------------------------------------------------------------------------
# p-values and significances
# --------------------------------------------------------------------------
def p_value_from_null(observed, null_values, side="greater"):
    """Empirical p-value of ``observed`` (scalar or array) against null pseudo-experiments.

    side 'greater': p = (1 + #{null >= obs}) / (1 + N);  'less': #{null <= obs};
    'two-sided': min(1, 2 min(p_greater, p_less)).  The smallest attainable p is 1/(1 + N).
    Non-finite null values raise ValueError; a NaN observation (failed pseudo-experiment)
    gets p = NaN instead of being ranked.
    """
    null = np.sort(np.asarray(null_values, dtype=float).ravel())
    if null.size == 0 or not np.all(np.isfinite(null)):
        raise ValueError("null pseudo-experiments must be non-empty and finite")
    obs = np.asarray(observed, dtype=float)
    n = null.size
    greater = (1.0 + n - np.searchsorted(null, obs, side="left")) / (1.0 + n)
    less = (1.0 + np.searchsorted(null, obs, side="right")) / (1.0 + n)
    if side == "greater":
        out = greater
    elif side == "less":
        out = less
    elif side == "two-sided":
        out = np.minimum(1.0, 2.0 * np.minimum(greater, less))
    else:
        raise ValueError(f"unknown side {side!r}")
    return np.where(np.isnan(obs), np.nan, out)


def z_from_p(p):
    """One-sided significance Z = Phi^-1(1 - p) (scipy.stats.norm.isf): p = 0.5 -> 0, 2.87e-7 -> 5."""
    return _st.norm.isf(p)


def p_from_z(z):
    """Inverse of ``z_from_p``."""
    return _st.norm.sf(z)


def significance(values, null_values, side="greater", extrapolate=False):
    """One-sided Z of each value against null pseudo-experiments; returns (z, beyond).

    Inside the null range Z = z_from_p(p_value_from_null).  A value beyond all null
    values (flagged in the boolean array ``beyond``) only has the bound p < 1/(1 + N),
    so by default it gets the lower limit Z = z_from_p(1/(1 + N)).  ``extrapolate=True``
    replaces it by the Gaussian-tail value (value - mean_null) / std_null ('less': sign
    reversed), which is only meaningful for a null with Gaussian tails: for a skewed null
    it can overstate Z by a large factor.  NaN values give NaN.
    """
    if side not in ("greater", "less"):
        raise ValueError("significance is one-sided: side must be 'greater' or 'less'")
    null = np.asarray(null_values, dtype=float).ravel()
    v = np.asarray(values, dtype=float)
    z = z_from_p(p_value_from_null(v, null, side))
    beyond = v > null.max() if side == "greater" else v < null.min()
    if extrapolate:
        sign = 1.0 if side == "greater" else -1.0
        z = np.where(beyond, sign * (v - null.mean()) / null.std(ddof=1), z)
    return z, beyond


class ExpectedSignificance(NamedTuple):
    median: float
    q16: float
    q84: float
    n_alt: int                      # finite alternative pseudo-experiments used
    n_null: int
    n_failed: int                   # non-finite alternative values, excluded
    beyond_fraction: float          # alternatives beyond all null values
    median_is_limit: bool           # median beyond the null range: a lower limit (or extrapolated)
    extrapolated: bool              # Gaussian-tail extrapolation used beyond the null range


def expected_significance(alt_values, null_values, side="greater", extrapolate=False):
    """Median expected significance of the alternative hypothesis and its 16-84% band
    (PLAN.md Sec. 6.3 item 6): Z of every finite alternative pseudo-experiment against
    the null distribution (``significance``), then its median and 16%/84% quantiles.
    Non-finite alternatives (failed pseudo-experiments) are excluded and counted in
    ``n_failed``.  When the median lies beyond all null values it is a lower limit
    (or, with ``extrapolate``, a Gaussian-tail extrapolation) and ``median_is_limit`` is set."""
    alt = np.asarray(alt_values, dtype=float).ravel()
    null = np.asarray(null_values, dtype=float).ravel()
    ok = np.isfinite(alt)
    if not ok.any():
        raise ValueError("no finite alternative pseudo-experiments")
    z, beyond = significance(alt[ok], null, side, extrapolate)
    q16, med, q84 = np.quantile(z, [0.16, 0.5, 0.84])
    t_med = np.median(alt[ok])
    med_beyond = bool(t_med > null.max() if side == "greater" else t_med < null.min())
    return ExpectedSignificance(float(med), float(q16), float(q84), int(ok.sum()), null.size,
                                int((~ok).sum()), float(np.mean(beyond)), med_beyond,
                                bool(extrapolate))


# --------------------------------------------------------------------------
# Error propagation and closure metrics
# --------------------------------------------------------------------------
def delta_method(jacobian, cov):
    """Linearised covariance J C J^T of y = f(x), J = dy/dx (m, n), C = cov(x) (n, n)."""
    j = np.atleast_2d(np.asarray(jacobian, dtype=float))
    return j @ np.asarray(cov, dtype=float) @ j.T


def numerical_jacobian(fn, x, step=1e-6):
    """Central-difference Jacobian d fn / dx (m, n) at x (n,), relative step ``step``."""
    x = np.asarray(x, dtype=float)
    h = step * np.maximum(1.0, np.abs(x))
    cols = []
    for i in range(x.size):
        dx = np.zeros_like(x)
        dx[i] = h[i]
        cols.append((np.atleast_1d(fn(x + dx)) - np.atleast_1d(fn(x - dx))) / (2 * h[i]))
    return np.stack(cols, axis=-1)


def pulls(estimates, truth, errors):
    """(estimate - truth) / error, element by element."""
    return (np.asarray(estimates, dtype=float) - np.asarray(truth, dtype=float)) / np.asarray(errors, dtype=float)


def chi_square(residual, cov, rtol=1e-10):
    """chi^2 = r^T C^+ r on the support of C (eigenvalues above rtol x the largest), so a
    rank-deficient covariance (e.g. coefficients unfolded in a subspace) is handled;
    components of r outside the support are ignored.  Returns (chi2, ndf, p-value)."""
    r = np.asarray(residual, dtype=float)
    lam, vec = np.linalg.eigh(np.asarray(cov, dtype=float))
    keep = lam > rtol * lam.max()
    proj = vec[:, keep].T @ r
    chi2 = float(np.sum(proj ** 2 / lam[keep]))
    ndf = int(keep.sum())
    return chi2, ndf, float(_st.chi2.sf(chi2, ndf))
