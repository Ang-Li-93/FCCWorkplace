"""Bootstrap, p-values, significances and error propagation (PLAN.md rule 4, Sec. 6.3)."""
import numpy as np
import pytest
from scipy import stats as st

from qtomo import stats


def _rng(seed=4242):
    return np.random.default_rng(seed)


# --------------------------------------------------------------------------
# Bootstrap
# --------------------------------------------------------------------------
@pytest.mark.parametrize("method", ["poisson", "resample"])
def test_bootstrap_std_of_mean(method):
    """The bootstrap spread of a sample mean is s/sqrt(n)."""
    r = _rng(1)
    x = r.normal(3.0, 2.0, 2000)
    n_boot = 2000
    vals = stats.bootstrap(np.average, x, n_boot, r, method=method)
    se = x.std(ddof=1) / np.sqrt(x.size)
    assert vals.shape == (n_boot,)
    assert abs(vals.std(ddof=1) / se - 1) < 5 / np.sqrt(2 * (n_boot - 1))
    assert abs(vals.mean() - x.mean()) < 5 * se / np.sqrt(n_boot)


def test_bootstrap_several_arrays():
    r = _rng(2)
    x, y = r.normal(1.0, 1.0, 500), r.normal(2.0, 1.0, 500)

    def means(a, b, weights=None):
        return np.array([np.average(a, weights=weights), np.average(b, weights=weights)])

    vals = stats.bootstrap(means, (x, y), 300, r)
    assert vals.shape == (300, 2)
    assert np.all(np.abs(vals.mean(axis=0) - [x.mean(), y.mean()]) < 5 * np.array([x.std(), y.std()]) / np.sqrt(500 * 300))
    with pytest.raises(ValueError):
        stats.bootstrap(means, (x, y[:10]), 5, r)
    with pytest.raises(ValueError):
        stats.bootstrap(np.average, x, 5, r, method="jackknife")


def test_poisson_weights_are_chunk_invariant():
    """The weight of event i in replica r does not depend on the chunking; Poisson(1) moments."""
    full = np.concatenate([w for _, w in stats.poisson_weights(_rng(3), 10_000, 50, chunk=10_000)])
    parts = list(stats.poisson_weights(_rng(3), 10_000, 50, chunk=777))
    assert parts[0][0] == slice(0, 777) and parts[-1][0].stop == 10_000
    assert np.array_equal(np.concatenate([w for _, w in parts]), full) and full.shape == (10_000, 50)
    assert abs(full.mean() - 1) < 5 / np.sqrt(full.size)
    assert abs(full.var() - 1) < 5 * np.sqrt(3 / full.size)       # Var(s^2) = (mu4 - 1)/n, mu4 = 4
    assert abs(np.mean(full == 0) - np.exp(-1)) < 5 * np.sqrt(np.exp(-1) * (1 - np.exp(-1)) / full.size)
    scaled = np.concatenate([w for _, w in stats.poisson_weights(_rng(3), 10_000, 50, mean=3.0)])
    assert abs(scaled.mean() - 3) < 5 * np.sqrt(3 / scaled.size)


def test_poisson_bootstrap_sums():
    """Replica sums equal sum_i u_ir w_i v_i with the poisson_weights stream; their spread is
    sqrt(sum_i (w_i v_i)^2) for Poisson(1) multiplicities."""
    r = _rng(4)
    n, n_boot = 5000, 400
    v, wt = r.normal(size=(n, 3)), r.uniform(0.5, 1.5, n)
    sums = stats.poisson_bootstrap_sums(v, n, n_boot, _rng(5), weights=wt, chunk=1234)
    u = np.concatenate([w for _, w in stats.poisson_weights(_rng(5), n, n_boot, chunk=999)])
    a = v * wt[:, None]
    assert sums.shape == (n_boot, 3) and np.allclose(sums, u.T @ a)
    assert np.allclose(stats.poisson_bootstrap_sums(lambda sl: v[sl], n, n_boot, _rng(5), weights=wt), sums)
    sd = np.sqrt((a ** 2).sum(axis=0))
    assert np.all(np.abs(sums.std(axis=0, ddof=1) / sd - 1) < 5 / np.sqrt(2 * (n_boot - 1)))
    assert np.all(np.abs(sums.mean(axis=0) - a.sum(axis=0)) < 5 * sd / np.sqrt(n_boot))


def test_summarise():
    v = np.arange(101.0)
    s = stats.summarise(v)
    assert s.n == 101 and s.mean == 50 and s.median == 50
    assert np.isclose(s.q16, 16) and np.isclose(s.q84, 84)
    assert np.isclose(s.std, np.sqrt(np.sum((v - 50) ** 2) / 100))
    two = stats.summarise(np.column_stack([v, -v]))
    assert np.allclose(two.median, [50, -50]) and np.allclose(two.q16, [16, -84]) and np.allclose(two.q84, [84, -16])


# --------------------------------------------------------------------------
# p-values and significances
# --------------------------------------------------------------------------
def test_p_value_conventions():
    """p = (1 + #{null at least as extreme}) / (1 + N); ties count as extreme."""
    null = np.arange(10.0)
    assert np.isclose(stats.p_value_from_null(9.5, null), 1 / 11)        # beyond all null values
    assert np.isclose(stats.p_value_from_null(9.0, null), 2 / 11)
    assert np.isclose(stats.p_value_from_null(4.5, null), 6 / 11)
    assert np.isclose(stats.p_value_from_null(-1.0, null), 1.0)
    assert np.isclose(stats.p_value_from_null(-0.5, null, "less"), 1 / 11)
    assert np.isclose(stats.p_value_from_null(0.0, null, "less"), 2 / 11)
    assert np.allclose(stats.p_value_from_null([9.5, 4.5, 9.0], null), [1 / 11, 6 / 11, 2 / 11])
    assert np.isclose(stats.p_value_from_null(9.5, null, "two-sided"), 2 / 11)
    assert np.isclose(stats.p_value_from_null(4.5, null, "two-sided"), 1.0)
    with pytest.raises(ValueError):
        stats.p_value_from_null(1.0, null, "sideways")
    # exchangeable observation: p is uniform on {1, ..., N+1}/(N+1), so P(p <= 0.05) = 0.05
    r = _rng(6)
    toys = r.normal(size=(4000, 100))
    p = np.array([stats.p_value_from_null(t[-1], t[:-1]) for t in toys])
    assert abs(np.mean(p <= 0.05) - 0.05) < 5 * np.sqrt(0.05 * 0.95 / 4000)
    assert abs(p.mean() - 101 / 200) < 5 * np.sqrt(1 / 12 / 4000)


def test_z_from_p():
    assert stats.z_from_p(0.5) == pytest.approx(0.0, abs=1e-15)
    assert stats.z_from_p(2.87e-7) == pytest.approx(5.0, abs=2e-3)
    assert stats.z_from_p(st.norm.sf(1.0)) == pytest.approx(1.0, abs=1e-12)
    assert stats.z_from_p(1.349898e-3) == pytest.approx(3.0, abs=1e-5)
    assert np.allclose(stats.p_from_z(stats.z_from_p([0.3, 1e-4, 1e-12])), [0.3, 1e-4, 1e-12])


def test_significance_bound_and_extrapolation():
    r = _rng(7)
    null = r.normal(size=5000)
    z, beyond = stats.significance([0.0, 1.0, 2.0], null)
    assert not beyond.any() and np.allclose(z, [0.0, 1.0, 2.0], atol=0.2)
    z, beyond = stats.significance([10.0], null)                          # default: the bound
    assert beyond[0] and np.isclose(z[0], stats.z_from_p(1 / 5001))
    z, beyond = stats.significance([10.0], null, extrapolate=True)
    assert beyond[0] and np.isclose(z[0], (10.0 - null.mean()) / null.std(ddof=1))
    z, beyond = stats.significance([-10.0, 0.0], null, side="less", extrapolate=True)
    assert beyond[0] and not beyond[1] and z[0] > 9 and abs(z[1]) < 0.2
    z, _ = stats.significance([np.nan, 0.0], null)
    assert np.isnan(z[0]) and np.isfinite(z[1])
    with pytest.raises(ValueError):
        stats.significance([1.0], null, side="two-sided")
    with pytest.raises(ValueError):
        stats.significance([1.0], np.append(null, np.nan))


def test_bound_is_conservative_for_skewed_null():
    """For an exponential null the Gaussian-tail extrapolation overstates Z; the default
    bound never exceeds the true significance of a value beyond the null range."""
    r = _rng(9)
    null = r.exponential(size=1000)
    v = null.max() + 0.01
    true_z = stats.z_from_p(np.exp(-v))
    z_bound, _ = stats.significance([v], null)
    z_extr, _ = stats.significance([v], null, extrapolate=True)
    assert z_bound[0] <= true_z + 0.05
    assert z_extr[0] > true_z + 1.0


def test_expected_significance_gaussian_toys():
    """Null N(0, 1), alternative N(mu, 1): median Z = mu with the 16-84% band [mu - 1, mu + 1];
    beyond the null range the value is a flagged lower limit unless extrapolated."""
    r = _rng(8)
    null = r.normal(size=20_000)
    res = stats.expected_significance(r.normal(2.0, 1.0, 20_000), null)
    assert res.median == pytest.approx(2.0, abs=0.12)
    assert res.q16 == pytest.approx(1.0, abs=0.1)
    assert res.q84 == pytest.approx(3.0, abs=0.3)
    assert not res.median_is_limit and 0 < res.beyond_fraction < 0.1
    assert res.n_alt == 20_000 and res.n_null == 20_000 and res.n_failed == 0
    far_alt = r.normal(8.0, 1.0, 5000)
    far = stats.expected_significance(far_alt, null)
    assert far.median_is_limit and far.beyond_fraction > 0.99
    assert far.median == pytest.approx(stats.z_from_p(1 / 20_001))
    ext = stats.expected_significance(far_alt, null, extrapolate=True)
    assert ext.extrapolated and ext.median == pytest.approx(8.0, abs=0.25)
    assert ext.q16 == pytest.approx(7.0, abs=0.25) and ext.q84 == pytest.approx(9.0, abs=0.25)
    low = stats.expected_significance(r.normal(-2.0, 1.0, 20_000), null, side="less")
    assert low.median == pytest.approx(2.0, abs=0.12)
    # failed (NaN) pseudo-experiments are excluded, not counted as maximally significant
    alt = r.normal(1.0, 1.0, 10_000)
    alt_nan = alt.copy()
    alt_nan[:4000] = np.nan
    res_nan = stats.expected_significance(alt_nan, null)
    assert res_nan.n_failed == 4000 and res_nan.n_alt == 6000
    assert res_nan.median == pytest.approx(1.0, abs=0.1)


# --------------------------------------------------------------------------
# Error propagation and closure metrics
# --------------------------------------------------------------------------
def test_delta_method_and_numerical_jacobian():
    r = _rng(9)
    cov = np.array([[2.0, 0.3], [0.3, 1.0]])
    jac = np.array([[1.0, 2.0], [0.5, -1.0], [3.0, 0.0]])
    y = r.multivariate_normal([1.0, 2.0], cov, size=200_000) @ jac.T
    mc = np.cov(y.T)
    lin = stats.delta_method(jac, cov)
    assert np.all(np.abs(mc - lin) < 5 * np.sqrt((lin ** 2 + np.outer(np.diag(lin), np.diag(lin))) / 200_000))
    # ratio of two quantities: var(a/b) = (a/b)^2 (va/a^2 + vb/b^2 - 2 cab/(a b))
    mu, cov2 = np.array([3.0, 5.0]), np.array([[4.0, 1.0], [1.0, 9.0]]) * 1e-4
    j = stats.numerical_jacobian(lambda v: v[0] / v[1], mu)
    assert j.shape == (1, 2) and np.allclose(j, [[1 / 5, -3 / 25]], atol=1e-9)
    analytic = (3 / 5) ** 2 * (cov2[0, 0] / 9 + cov2[1, 1] / 25 - 2 * cov2[0, 1] / 15)
    assert np.isclose(stats.delta_method(j, cov2)[0, 0], analytic, rtol=1e-7)


def test_pulls_and_chi_square():
    r = _rng(10)
    truth, err = r.normal(size=50), r.uniform(0.5, 2.0, 50)
    p = stats.pulls(truth + err * r.normal(size=(4000, 50)), truth, err)
    assert abs(p.mean()) < 5 / np.sqrt(p.size) and abs(p.std() - 1) < 5 / np.sqrt(2 * p.size)
    k = 6
    m = r.normal(size=(k, k))
    cov = m @ m.T + 0.1 * np.eye(k)
    x = r.multivariate_normal(np.zeros(k), cov, size=4000)
    chis = np.array([stats.chi_square(v, cov)[0] for v in x])
    assert abs(chis.mean() - k) < 5 * np.sqrt(2 * k / 4000)
    chi2, ndf, pval = stats.chi_square(x[0], cov)
    assert ndf == k and np.isclose(pval, st.chi2.sf(chi2, k))
    # rank-deficient covariance (a 3-dimensional subspace): ndf = rank
    b = np.linalg.qr(r.normal(size=(k, 3)))[0]
    proj = b @ b.T
    cov_r = proj @ cov @ proj
    chis = np.array([stats.chi_square(proj @ v, cov_r) for v in x])
    assert np.all(chis[:, 1] == 3) and abs(chis[:, 0].mean() - 3) < 5 * np.sqrt(6 / 4000)
