"""Moment estimators, covariance and unbiased quadratic invariants
(PLAN.md Sec. 3.3, 3.5 and 4; CONVENTIONS.md Sec. 2, 3 and 6)."""
import functools
import time

import numpy as np
import pytest
from scipy import stats

from qtomo import basis, sm, tomography, toy

P_MIN = 1e-4                         # p-value threshold per test function, split over its checks
PREF = (3 / (4 * np.pi)) ** 2
H44, H55 = basis.COEFF_LABELS.index("h44"), basis.COEFF_LABELS.index("h55")
_EV, _VEC = np.linalg.eigh(basis.RANK1)
E1, E2 = _VEC[:, _EV > 0.5], _VEC[:, _EV < 0.5]      # orthonormal rank-1 (3) and rank-2 (5) bases


def _rng(seed):
    return np.random.default_rng(seed)


def _state(name):
    if name.startswith("sm"):
        return sm.density_matrix(float(name[2:]))
    if name == "random":
        return basis.random_density_matrix(_rng(101))
    if name == "isotropic":
        return basis.ID9 / 9
    raise ValueError(name)


def _chi2_pvalue(c, cov, c_ref):
    d = c - c_ref
    return stats.chi2.sf(d @ np.linalg.solve(cov, d), d.size)


def _whitened(res, c_ref):
    return np.linalg.solve(np.linalg.cholesky(res.cov), res.c - c_ref)


def _check_standard_normal(z):
    assert abs(z.mean()) < 5 / np.sqrt(z.size)
    assert abs(z.std() - 1) < 5 / np.sqrt(2 * z.size)
    assert stats.kstest(z, "norm").pvalue > P_MIN


def _err(v):
    v = np.asarray(v)
    return v.std(axis=0, ddof=1) / np.sqrt(len(v))


def _pair_trace(rho, th, ph):
    """Tr[rho (Pi+(i) x Pi-(j))] on all pairs of nodes, from explicit 9x9 traces."""
    return np.einsum("ikjl,xji,ylk->xy", np.asarray(rho).reshape(3, 3, 3, 3),
                     basis.projector(th, ph, +1), basis.projector(th, ph, -1), optimize=True).real


def _grid(rho):
    """Probabilities of the product quadrature nodes under (3/4pi)^2 Tr[rho Pi+ x Pi-] and the
    estimator vectors at the nodes (exact for degree <= 6 on each sphere)."""
    th, ph, w = basis.sphere_quadrature(8, 16)
    prob = (PREF * np.outer(w, w) * _pair_trace(rho, th, ph)).ravel()
    i, j = np.divmod(np.arange(th.size ** 2), th.size)
    return prob, basis.estimator_vector(th[i], ph[i], th[j], ph[j])


def _exact_moments(rho):
    """Per-event mean and covariance of basis.estimator_vector, by product quadrature."""
    prob, x = _grid(rho)
    mean = prob @ x
    return mean, x.T @ (prob[:, None] * x) - np.outer(mean, mean)


def _invariant_weights():
    """Rows a_j with invariant_j = const_j + a_j . c^2, read off quadratic_invariants (which
    test_quadratic_invariants_exact pins to the direct traces)."""
    zero = np.array(tomography.quadratic_invariants(np.zeros(basis.N_COEFF)))
    return np.array([np.array(tomography.quadratic_invariants(e)) - zero
                     for e in np.eye(basis.N_COEFF)]).T


def _hoeffding_sigma(rho, n):
    """Exact standard deviations of the five unbiased invariants of n events: textbook Hoeffding
    variance 2 [2 (n - 2) zeta1 + zeta2] / (n (n - 1)) of the U-statistic with kernel
    k(x, y) = sum_k a_k x_k y_k, with zeta1 = Var E[k(X, Y) | X] and zeta2 = Var k(X, Y) from
    their definitions on the quadrature grid (independent events: E[k^2] = a.(M o M).a with
    M = E[x x^T])."""
    prob, x = _grid(rho)
    a = _invariant_weights()
    c = prob @ x
    k1 = x @ (a * c).T                                   # E[k(x, Y)] at every node, (nodes, 5)
    zeta1 = prob @ k1 ** 2 - (prob @ k1) ** 2
    m2 = x.T @ (prob[:, None] * x)
    zeta2 = np.einsum("jk,kl,jl->j", a, m2 * m2, a) - (a @ c ** 2) ** 2
    return np.sqrt(2 * (2 * (n - 2) * zeta1 + zeta2) / (n * (n - 1)))


def _check_spread(values, sigma):
    """Standard deviations of the columns of values against sigma, within 5 standard errors from
    the sample kurtosis, Var(s^2) = (m4 - s^4)/n (small-sample invariants near c = 0 are not
    normally distributed)."""
    v = np.asarray(values)
    s = v.std(axis=0, ddof=1)
    kurt = np.mean((v - v.mean(axis=0)) ** 4, axis=0) / s ** 4
    err = 0.5 * s * np.sqrt((kurt - 1) / len(v))
    assert np.all(np.abs(s - sigma) < 5 * err), (s / sigma, err / sigma)


# --------------------------------------------------------------------------
# Formulas
# --------------------------------------------------------------------------
def test_quadratic_invariants_exact():
    """Tr rho^2, Tr rho_A^2, Tr rho_B^2 from the squares agree with the direct traces."""
    r = _rng(1)
    states = ([basis.random_density_matrix(r) for _ in range(4)]
              + [basis.random_density_matrix(r, rank=1), basis.random_product_state(r),
                 basis.random_product_state(r, pure=False), sm.density_matrix(1.3), basis.ID9 / 9])
    for rho in states:
        inv = tomography.quadratic_invariants(basis.coefficient_vector(rho) ** 2)
        p, pa, pb = (basis.purity(x) for x in (rho, basis.reduced_wplus(rho), basis.reduced_wminus(rho)))
        assert np.allclose(inv, [p, pa, pb, p - pa, p - pb], atol=1e-13)
    # product states are separable (C2 arguments <= 0); the SM state is entangled
    for rho in states[5:7] + states[-1:]:
        inv = tomography.quadratic_invariants(basis.coefficient_vector(rho) ** 2)
        assert max(inv.c2_arg_wplus, inv.c2_arg_wminus) <= 1e-13
    inv = tomography.quadratic_invariants(basis.coefficient_vector(sm.density_matrix(1.3)) ** 2)
    assert np.isclose(inv.purity, 1.0) and min(inv.c2_arg_wplus, inv.c2_arg_wminus) > 0.1


def test_estimate_formulas_on_a_small_sample():
    """Weighted mean, linearised covariance, n_eff and U-statistic against a direct evaluation
    on 7 events (the U-statistic as an explicit sum over pairs i != j)."""
    r = _rng(2)
    ang = toy.isotropic(7, r)
    w = r.uniform(0.2, 2.0, 7)
    res = tomography.estimate(*ang, weights=w, mistag_p=0.1, mistag_m=0.2)
    x = basis.estimator_vector(*ang, 0.1, 0.2)
    c = w @ x / w.sum()
    cov = sum(wi ** 2 * np.outer(xi - c, xi - c) for wi, xi in zip(w, x)) / w.sum() ** 2
    pairs = [(i, j) for i in range(7) for j in range(7) if i != j]
    c_sq = sum(w[i] * w[j] * x[i] * x[j] for i, j in pairs) / sum(w[i] * w[j] for i, j in pairs)
    assert np.allclose(res.c, c) and np.allclose(res.cov, cov) and np.allclose(res.c_sq, c_sq)
    assert np.allclose(res.sigma, np.sqrt(np.diag(cov)))
    assert np.isclose(res.n_eff, w.sum() ** 2 / (w ** 2).sum()) and res.n_events == 7
    assert np.isclose(res.sum_w, w.sum())
    f, g, h = basis.unpack(c)
    assert np.allclose(res.f, f) and np.allclose(res.g, g) and np.allclose(res.h, h)
    assert np.allclose(res.rho, basis.density_matrix(f, g, h))
    assert np.allclose(res.rho_physical, basis.nearest_physical(res.rho))
    assert np.isclose(res.min_eigenvalue, basis.min_eigenvalue(res.rho))
    assert np.allclose(res.invariants, tomography.quadratic_invariants(c_sq))
    assert np.allclose(res.invariants_plugin, tomography.quadratic_invariants(c ** 2))
    x0 = basis.estimator_vector(*ang)
    res0 = tomography.estimate(*ang)
    assert np.isclose(res0.n_eff, 7.0)
    assert np.allclose(res0.c_sq, (x0.sum(0) ** 2 - (x0 ** 2).sum(0)) / (7 * 6))


def test_chunked_merged_and_saved_accumulators_agree(tmp_path):
    r = _rng(3)
    ang = toy.generate(_state("random"), 5000, r)
    w, wp = r.uniform(0.5, 1.5, 5000), r.uniform(0.0, 0.3, 5000)
    kw = dict(mistag_m=0.2)

    def acc(sl=slice(None), **extra):
        return tomography.MomentAccumulator().add(*(a[sl] for a in ang), weights=w[sl],
                                                  mistag_p=wp[sl], **kw, **extra)

    full = acc().result()
    parts = [acc(slice(0, 1000)), acc(slice(1000, 3500)), acc(slice(3500, None))]
    parts[0].save(tmp_path / "part0.npz")
    loaded = tomography.MomentAccumulator.load(tmp_path / "part0.npz")
    merged = loaded + parts[1]
    merged += parts[2]
    for other in (acc(chunk=777), sum(parts, tomography.MomentAccumulator()), merged):
        res = other.result()
        assert res.n_events == full.n_events and np.isclose(res.sum_w, full.sum_w)
        for name in ("c", "cov", "c_sq"):
            assert np.allclose(getattr(res, name), getattr(full, name), rtol=1e-10, atol=1e-14)
    assert parts[1].n_events == 2500                     # merging leaves the parts untouched
    vec = tomography.MomentAccumulator().add_vectors(basis.estimator_vector(*ang, wp, 0.2), w)
    assert np.allclose(vec.result().cov, full.cov, rtol=1e-10, atol=1e-14)
    # save and load agree on the file name when it lacks the .npz suffix
    parts[1].save(tmp_path / "part1")
    assert (tmp_path / "part1.npz").exists()
    reloaded = tomography.MomentAccumulator.load(tmp_path / "part1")
    assert all(np.array_equal(a, b) for a, b in zip(reloaded.state().values(),
                                                    parts[1].state().values()))


def test_errors():
    r = _rng(4)
    ang = toy.isotropic(10, r)
    with pytest.raises(ValueError):
        tomography.MomentAccumulator().result()
    with pytest.raises(ValueError):
        tomography.estimate(ang[0][:5], *ang[1:])
    with pytest.raises(ValueError):
        tomography.estimate(*ang, mistag_p=np.zeros(3))
    with pytest.raises(ValueError):
        tomography.estimate(*ang, mistag_p=0.5)                  # no rank-1 information
    one = tomography.estimate(*(a[:1] for a in ang))
    assert np.all(np.isnan(one.c_sq)) and np.isnan(one.invariants.purity)
    # the options are keyword-only: neither a toy.SMEvents (masses first) nor a positional
    # weight can be unpacked into them
    events = toy.SMEvents(np.full(10, 80.0), np.full(10, 30.0), *ang)
    with pytest.raises(TypeError):
        tomography.estimate(*events)
    with pytest.raises(TypeError):
        tomography.MomentAccumulator().add(*events)
    with pytest.raises(TypeError):
        tomography.estimate(*ang, np.ones(10))
    assert np.array_equal(tomography.estimate(*events.angles).c, tomography.estimate(*ang).c)
    # rates outside [0, 1], non-finite rates, weights or angles, and empty chunks
    for kw in (dict(mistag_p=1.7), dict(mistag_m=-0.1), dict(mistag_p=np.full(10, np.nan)),
               dict(weights=np.full(10, np.nan)), dict(weights=np.inf), dict(chunk=0)):
        with pytest.raises(ValueError):
            tomography.estimate(*ang, **kw)
    bad = [a.copy() for a in ang]
    bad[1][3] = np.nan
    with pytest.raises(ValueError, match="finite"):
        tomography.estimate(*bad)


# --------------------------------------------------------------------------
# Closure on toys (PLAN.md Sec. 3.3, third bullet)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name,seed", [("sm1.0", 51), ("sm1.8", 52), ("sm6.0", 53),
                                       ("random", 54), ("isotropic", 55)])
def test_closure_large_toy(name, seed):
    """SM states at several kappa, a random full-rank state and 1/9 are recovered from
    2e5 toy events (chi-square of the 80 coefficients with the estimated covariance)."""
    rho = _state(name)
    c_true = basis.coefficient_vector(rho)
    res = tomography.estimate(*toy.generate(rho, 200_000, _rng(seed)))
    assert _chi2_pvalue(res.c, res.cov, c_true) > P_MIN
    assert np.all(np.abs(res.c - c_true) < 5 * res.sigma)
    assert np.isclose(np.trace(res.rho).real, 1.0)
    assert basis.min_eigenvalue(res.rho_physical) > -1e-12
    # projection onto the (convex) set of states never moves away from a physical truth
    assert np.linalg.norm(res.rho_physical - rho) <= np.linalg.norm(res.rho - rho) + 1e-12


@pytest.mark.parametrize("name", ["sm1.4", "random"])
def test_pulls_small_toys(name):
    """Whitened residuals of 50 toys of 4000 events (80 x 50 values) are N(0, 1)."""
    rho = _state(name)
    c_true = basis.coefficient_vector(rho)
    z = [_whitened(tomography.estimate(*ang), c_true) for ang in toy.pseudo_experiments(
        functools.partial(toy.generate, rho), 4000, 50, _rng(5))]
    _check_standard_normal(np.concatenate(z))


def test_covariance_matches_spread_over_toys():
    """The estimated covariance agrees with the exact one (quadrature) and with the spread of
    the estimates over 200 independent toys."""
    rho = _state("random")
    c_true = basis.coefficient_vector(rho)
    n_ev, n_toys = 2000, 200
    cs, covs = [], []
    for ang in toy.pseudo_experiments(functools.partial(toy.generate, rho), n_ev, n_toys, _rng(6)):
        res = tomography.estimate(*ang)
        cs.append(res.c)
        covs.append(res.cov)
    cs, covs = np.array(cs), np.array(covs)
    cov_est = covs.mean(axis=0)
    mean_exact, cov_exact = _exact_moments(rho)
    assert np.allclose(mean_exact, c_true, atol=1e-12)
    cov_exact = cov_exact / n_ev
    diag = np.einsum("tkk->tk", covs)
    assert np.all(np.abs(diag.mean(axis=0) - np.diag(cov_exact)) < 5 * _err(diag))
    assert np.linalg.norm(cov_est - cov_exact) < 0.02 * np.linalg.norm(cov_exact)
    # spread over the toys: chi-square of all deviations, both tails, and the trace ratio
    z = np.linalg.solve(np.linalg.cholesky(cov_est), (cs - c_true).T)
    chi2 = np.sum(z ** 2)
    assert stats.chi2.sf(chi2, z.size) > P_MIN / 2 and stats.chi2.cdf(chi2, z.size) > P_MIN / 2
    ratio = np.trace(np.linalg.solve(cov_est, np.cov(cs, rowvar=False))) / basis.N_COEFF
    assert abs(ratio - 1) < 5 * np.sqrt(2 / (basis.N_COEFF * (n_toys - 1)))


# --------------------------------------------------------------------------
# Unbiased squares and invariants
# --------------------------------------------------------------------------
def _invariant_toys(sample, n_ev, n_toys, rng):
    """Per toy: U-statistic and plug-in sum h^2, unbiased invariants and invariants_sigma."""
    u, plug, inv, sig = [], [], [], []
    for ang in toy.pseudo_experiments(sample, n_ev, n_toys, rng):
        res = tomography.estimate(*ang)
        u.append(res.c_sq[16:].sum())
        plug.append(np.sum(res.c[16:] ** 2))
        inv.append(res.invariants)
        sig.append(res.invariants_sigma)
    return map(np.array, (u, plug, inv, sig))


def test_unbiased_squares_isotropic():
    """rho = 1/9 (all c = 0): the U-statistic of sum h^2 averages to 0, the plug-in value to
    sum_k Var(x_k)/N > 0, exact by quadrature; the unbiased invariants average to those of 1/9
    and spread as the exact Hoeffding value.  invariants_sigma is conservative here by the
    documented 10-20% (the floor of invariant_sigma); a wrong c = 0 term, a missing bias
    correction or a missing floor puts it outside (1, 1.25)."""
    n_ev = 500
    u, plug, inv, sig = _invariant_toys(toy.isotropic, n_ev, 1000, _rng(7))
    th, ph, w = basis.sphere_quadrature(8, 16)
    p2 = [w @ basis.p_functions(th, ph, s) ** 2 / (4 * np.pi) for s in (1, -1)]
    bias = np.outer(*p2).sum() / 16 / n_ev       # Var(p+^a p-^b / 4), independent isotropic legs
    assert abs(u.mean()) < 5 * _err(u)
    assert abs(plug.mean() - bias) < 5 * _err(plug)
    assert plug.mean() > 20 * _err(plug)
    exact = np.array([1 / 9, 1 / 3, 1 / 3, -2 / 9, -2 / 9])
    assert np.all(np.abs(inv.mean(axis=0) - exact) < 5 * _err(inv))
    sigma = _hoeffding_sigma(basis.ID9 / 9, n_ev)
    _check_spread(inv, sigma)
    ratio = sig.mean(axis=0) / sigma
    assert np.all((ratio > 1.0) & (ratio < 1.25)), ratio


def test_unbiased_squares_and_invariants_sm():
    """SM state (c != 0): unbiased sum h^2 and invariants; the plug-in is biased upward; the
    invariants spread as the exact Hoeffding value, and invariants_sigma agrees with it up to the
    few per cent of the square root (without the bias correction, or with the plain delta
    method 4 (a o c)^T cov (a o c), it is 10-30% high)."""
    rho = _state("sm1.5")
    c = basis.coefficient_vector(rho)
    n_ev = 500
    u, plug, inv, sig = _invariant_toys(functools.partial(toy.generate, rho), n_ev, 800, _rng(8))
    true_h2 = np.sum(c[16:] ** 2)
    assert abs(u.mean() - true_h2) < 5 * _err(u)
    assert plug.mean() - true_h2 > 10 * _err(plug)
    p, pa, pb = (basis.purity(x) for x in (rho, basis.reduced_wplus(rho), basis.reduced_wminus(rho)))
    exact = np.array([p, pa, pb, p - pa, p - pb])
    assert np.all(np.abs(inv.mean(axis=0) - exact) < 5 * _err(inv))
    sigma = _hoeffding_sigma(rho, n_ev)
    _check_spread(inv, sigma)
    ratio = sig.mean(axis=0) / sigma
    assert np.all((ratio > 0.9) & (ratio < 1.07)), ratio


def test_expected_invariant_sigma():
    """Exact standard deviations of the unbiased invariants from the exact moments, against the
    textbook Hoeffding variance with zeta1, zeta2 from their definitions (N = 2: the variance
    of a single pair, zeta2)."""
    r = _rng(16)
    for rho in (_state("random"), _state("sm1.5"), basis.ID9 / 9,
                basis.random_product_state(r, pure=False)):
        mean, cov = tomography.expected_moments(rho)
        for n in (2, 7, 500, 100_000):
            assert np.allclose(tomography.expected_invariant_sigma(mean, cov, n),
                               _hoeffding_sigma(rho, n), rtol=1e-9, atol=0)
    with pytest.raises(ValueError):
        tomography.expected_invariant_sigma(mean, cov, 1)


# --------------------------------------------------------------------------
# Weighted events (PLAN.md Sec. 3.7)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["random", "sm1.5"])
def test_weighted_isotropic_reproduces_rho(name):
    """Isotropic angles with w = 9 Tr[rho Pi+ x Pi-] reproduce rho; n_eff = N / E[w^2]."""
    rho = _state(name)
    c_true = basis.coefficient_vector(rho)
    n = 200_000
    ang = toy.isotropic(n, _rng(9))
    res = tomography.estimate(*ang, weights=9 * basis.trace_projectors(rho, *ang))
    assert _chi2_pvalue(res.c, res.cov, c_true) > P_MIN
    assert np.all(np.abs(res.c - c_true) < 5 * res.sigma)
    th, ph, wq = basis.sphere_quadrature(8, 16)
    prob = np.outer(wq, wq) / (4 * np.pi) ** 2                       # isotropic base
    wgt = 9 * _pair_trace(rho, th, ph)
    e_w, e_w2, e_w4 = (np.sum(prob * wgt ** k) for k in (1, 2, 4))
    assert np.isclose(e_w, 1.0)
    tol = 5 * (np.sqrt((e_w4 - e_w2 ** 2) / n) / e_w2 + 2 * np.sqrt((e_w2 - 1) / n))
    assert abs(res.n_eff / (n / e_w2) - 1) < tol


def test_weighted_pulls():
    """The linearised ratio-estimator covariance describes weighted toys (50 x 8000 events,
    reweighted to a pure SM state: strongly varying weights, n_eff / N ~ 0.57)."""
    rho = _state("sm1.5")
    c_true = basis.coefficient_vector(rho)
    z, n_eff = [], []
    for ang in toy.pseudo_experiments(toy.isotropic, 8000, 50, _rng(10)):
        res = tomography.estimate(*ang, weights=9 * basis.trace_projectors(rho, *ang))
        z.append(_whitened(res, c_true))
        n_eff.append(res.n_eff)
    assert 0.4 < np.mean(n_eff) / 8000 < 0.8
    _check_standard_normal(np.concatenate(z))


# --------------------------------------------------------------------------
# Analyser mistag (CONVENTIONS.md Sec. 3; PLAN.md Sec. 4, task 3)
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def mistag_sample():
    rho = _state("random")
    return rho, toy.generate(rho, 200_000, _rng(11))


@pytest.mark.parametrize("w_p,w_m", [(0.2, 0.0), (0.0, 0.3), (0.15, 0.25), ("per_event", 0.25)])
def test_mistag_unbiased(mistag_sample, w_p, w_m):
    """Flipped analysers estimated with the matching rates are unbiased; uncorrected estimates
    follow the dilution D(w); h44, h55 are unchanged by flips even without correction."""
    rho, ang = mistag_sample
    r = _rng(12)
    if w_p == "per_event":
        w_p = r.uniform(0.0, 0.35, ang.theta_p.size)
    tp, pp, _ = toy.apply_mistag(ang.theta_p, ang.phi_p, w_p, r)
    tm, pm, _ = toy.apply_mistag(ang.theta_m, ang.phi_m, w_m, r)
    c_true = basis.coefficient_vector(rho)
    corrected = tomography.estimate(tp, pp, tm, pm, mistag_p=w_p, mistag_m=w_m)
    assert _chi2_pvalue(corrected.c, corrected.cov, c_true) > P_MIN / 2
    raw = tomography.estimate(tp, pp, tm, pm)
    f, g, h = basis.coefficients(rho)
    d_p, d_m = basis.mistag_dilution(np.mean(w_p)), basis.mistag_dilution(w_m)
    assert _chi2_pvalue(raw.c, raw.cov, basis.pack(d_p @ f, d_m @ g, d_p @ h @ d_m.T)) > P_MIN / 2
    if np.any(w_p) and np.any(w_m):                     # dilution visible: the plain truth fails
        assert _chi2_pvalue(raw.c, raw.cov, c_true) < 1e-10
    unflipped = tomography.estimate(*ang)
    for res in (raw, corrected):
        assert np.allclose(res.c[[H44, H55]], unflipped.c[[H44, H55]], rtol=0, atol=1e-12)


@pytest.mark.parametrize("leg,w", [(+1, 0.1), (+1, 0.3), (-1, 0.2)])
def test_mistag_variance_growth(mistag_sample, leg, w):
    """Rank-1 variances of the corrected single-W coefficients grow as
    E[y^2]/(1-2w)^2 - E[y]^2 (about 1/(1-2w)^2); rank-2 blocks are unchanged."""
    rho, ang = mistag_sample
    r = _rng(13)
    tp, pp, tm, pm = ang
    if leg > 0:
        tp, pp, _ = toy.apply_mistag(tp, pp, w, r)
    else:
        tm, pm, _ = toy.apply_mistag(tm, pm, w, r)
    res_w = tomography.estimate(tp, pp, tm, pm, mistag_p=w * (leg > 0), mistag_m=w * (leg < 0))
    res_0 = tomography.estimate(*ang)
    blk = slice(0, 8) if leg > 0 else slice(8, 16)
    cov_w, cov_0 = res_w.cov[blk, blk], res_0.cov[blk, blk]
    assert np.allclose(E2.T @ cov_w @ E2, E2.T @ cov_0 @ E2, rtol=1e-9, atol=1e-16)
    # exact single-W moments by quadrature: y = e.p for the rank-1 directions e
    th, ph, wq = basis.sphere_quadrature(8, 16)
    marg = PREF * np.outer(wq, wq) * _pair_trace(rho, th, ph)
    marg = marg.sum(axis=1) if leg > 0 else marg.sum(axis=0)
    y = basis.p_functions(th, ph, leg) @ E1
    m1, m2 = marg @ y, marg @ y ** 2
    expected = (m2 / (1 - 2 * w) ** 2 - m1 ** 2) / (m2 - m1 ** 2)
    ratio = np.diag(E1.T @ cov_w @ E1) / np.diag(E1.T @ cov_0 @ E1)
    assert np.allclose(ratio, expected, rtol=0.01)
    assert np.allclose(ratio, 1 / (1 - 2 * w) ** 2, rtol=0.05)


# --------------------------------------------------------------------------
# Exact moments
# --------------------------------------------------------------------------
def test_expected_moments(mistag_sample):
    rho, ang = mistag_sample
    c_true = basis.coefficient_vector(rho)
    mean, cov = tomography.expected_moments(rho)
    ref_mean, ref_cov = _exact_moments(rho)
    assert np.allclose(mean, c_true, atol=1e-13) and np.allclose(cov, ref_cov, atol=1e-11)
    assert np.allclose(tomography.expected_moments(rho, n_cos=10, n_phi=20)[1], cov, atol=1e-11)
    # mistag: still unbiased; rank-2 blocks unchanged; rank-1 single-W variances rescaled
    w_p, w_m = 0.2, 0.35
    mean_w, cov_w = tomography.expected_moments(rho, w_p, w_m)
    assert np.allclose(mean_w, c_true, atol=1e-13)
    r2h = np.kron(basis.RANK2, basis.RANK2)
    assert np.allclose(r2h @ cov_w[16:, 16:] @ r2h, r2h @ cov[16:, 16:] @ r2h, atol=1e-12)
    for blk, w in ((slice(0, 8), w_p), (slice(8, 16), w_m)):
        assert np.allclose(E2.T @ cov_w[blk, blk] @ E2, E2.T @ cov[blk, blk] @ E2, atol=1e-12)
        second = E1.T @ (cov[blk, blk] + np.outer(c_true[blk], c_true[blk])) @ E1
        first = E1.T @ c_true[blk]
        assert np.allclose(E1.T @ cov_w[blk, blk] @ E1,
                           second / (1 - 2 * w) ** 2 - np.outer(first, first), atol=1e-12)
    # and they describe mistagged toys
    r = _rng(14)
    tp, pp, _ = toy.apply_mistag(ang.theta_p, ang.phi_p, w_p, r)
    tm, pm, _ = toy.apply_mistag(ang.theta_m, ang.phi_m, w_m, r)
    res = tomography.estimate(tp, pp, tm, pm, mistag_p=w_p, mistag_m=w_m)
    assert np.allclose(np.diag(res.cov) * res.n_events, np.diag(cov_w), rtol=0.05)
    with pytest.raises(ValueError):
        tomography.expected_moments(rho, np.zeros(3))
    # separate correction rates: the defaults are the flip rates; without correction the mean is
    # D(w) c, also at w = 1/2 (no correction exists), with the rank-(2,2) block unchanged
    mean_k, cov_k = tomography.expected_moments(rho, w_p, w_m, correct_p=w_p, correct_m=w_m)
    assert np.allclose(mean_k, mean_w, atol=1e-15) and np.allclose(cov_k, cov_w, atol=1e-15)
    f, g, h = basis.coefficients(rho)
    d = basis.mistag_dilution(0.5)
    mean_u, cov_u = tomography.expected_moments(rho, 0.5, 0.0, correct_p=0.0)
    assert np.allclose(mean_u, basis.pack(d @ f, g, d @ h), atol=1e-13)
    assert np.allclose(r2h @ cov_u[16:, 16:] @ r2h, r2h @ cov[16:, 16:] @ r2h, atol=1e-12)
    for kw in (dict(mistag_p=1.5), dict(mistag_m=-0.1), dict(correct_p=np.nan)):
        with pytest.raises(ValueError):
            tomography.expected_moments(rho, **kw)


# --------------------------------------------------------------------------
# Performance (targets: 1e6 events generated in about 15 s and estimated in about 5 s)
# --------------------------------------------------------------------------
@pytest.mark.slow
def test_performance():
    rho = _state("random")
    t0 = time.perf_counter()
    ang = toy.generate(rho, 1_000_000, _rng(15))
    t1 = time.perf_counter()
    res = tomography.estimate(*ang)
    t2 = time.perf_counter()
    assert res.n_events == 1_000_000
    assert t1 - t0 < 30.0 and t2 - t1 < 10.0    # twice the targets, for a loaded node
