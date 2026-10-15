"""Accept-reject toy generator and analyser mistag (PLAN.md Sec. 3.6)."""
import contextlib
import signal
import time

import numpy as np
import pytest
from scipy import stats

from qtomo import basis, config, sm, tomography, toy

P_MIN = 1e-4                         # p-value threshold per test function, split over its checks
PREF = (3 / (4 * np.pi)) ** 2


def _rng(seed):
    return np.random.default_rng(seed)


@contextlib.contextmanager
def _time_limit(seconds):
    """Raise TimeoutError instead of hanging (SIGALRM: Unix, main thread)."""
    def handler(signum, frame):
        raise TimeoutError(f"still running after {seconds} s")
    previous = signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


# --------------------------------------------------------------------------
# Exact references by quadrature
# --------------------------------------------------------------------------
def _pair_density(rho, nodes_p, nodes_m):
    """w_i w_k (3/4pi)^2 Tr[rho (Pi+(i) x Pi-(k))] on two sets of nodes (theta, phi, weight),
    from explicit 9x9 traces of the analyser projectors (independent of trace_projectors)."""
    (tp, pp, wp), (tm, pm, wm) = nodes_p, nodes_m
    tr = np.einsum("ikjl,aji,blk->ab", np.asarray(rho).reshape(3, 3, 3, 3),
                   basis.projector(tp, pp, +1), basis.projector(tm, pm, -1), optimize=True)
    return PREF * np.outer(wp, wm) * tr.real


def _gauss(lo, hi, n):
    """Gauss-Legendre nodes and weights on [lo, hi]."""
    x, w = np.polynomial.legendre.leggauss(n)
    return lo + (hi - lo) * (x + 1) / 2, (hi - lo) / 2 * w


def _theta_nodes(n=16):
    """Gauss-Legendre in theta on [0, pi], weights including the Jacobian sin(theta); converges
    to machine precision for the odd powers of sin(theta) that survive when phi is not
    integrated over a full period."""
    theta, w = _gauss(0.0, np.pi, n)
    return theta, w * np.sin(theta)


def _phi_nodes(n=16):
    """Uniform rule in phi, exact for harmonics |m| < n."""
    return (np.arange(n) + 0.5) * 2 * np.pi / n, np.full(n, 2 * np.pi / n)


def _product(nodes_a, nodes_b):
    (a, wa), (b, wb) = nodes_a, nodes_b
    aa, bb = np.meshgrid(a, b, indexing="ij")
    return aa.ravel(), bb.ravel(), np.outer(wa, wb).ravel()


def _theta_sphere(n_theta=16, n_phi=32):
    return _product(_theta_nodes(n_theta), _phi_nodes(n_phi))


def _binned_nodes(edges, variable):
    """Nodes restricted to each bin of cos(theta) (phi over the full circle) or of phi
    (theta over [0, pi]) on one sphere, with the bin label of each node."""
    nodes, labels = [], []
    for b, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        if variable == "cos":
            u, wu = _gauss(lo, hi, 8)
            th, ph, w = _product((np.arccos(u), wu), _phi_nodes(16))
        else:
            th, ph, w = _product(_theta_nodes(16), _gauss(lo, hi, 8))
        nodes.append((th, ph, w))
        labels.append(np.full(th.size, b))
    return tuple(np.concatenate(z) for z in zip(*nodes)), np.concatenate(labels)


def _leg_bin_probs(rho, leg, edges, variable):
    """Exact bin probabilities of cos(theta) or phi of one analyser.  The other sphere is
    integrated with basis.sphere_quadrature, exact for the polynomials in cos(theta) left
    after its full phi integral."""
    nodes, labels = _binned_nodes(edges, variable)
    other = basis.sphere_quadrature(8, 16)
    d = _pair_density(rho, nodes, other) if leg > 0 else _pair_density(rho, other, nodes).T
    return np.bincount(labels, weights=d.sum(axis=1), minlength=len(edges) - 1)


def _cos_dphi_probs(rho, m, edges, j_max=8):
    """Exact bin probabilities of cos(m dphi), dphi = phi+ - phi-.  For psi = m dphi with
    Fourier coefficients A_j = <cos(j psi)> (by quadrature), the bin cos(psi) in [u0, u1] is
    psi in [a1, a0] or [2pi - a0, 2pi - a1], a = arccos(u); the sine terms cancel."""
    nodes = _theta_sphere(16, 32)
    d = _pair_density(rho, nodes, nodes)
    phi = nodes[1]
    alpha = np.arccos(edges)
    prob = (alpha[:-1] - alpha[1:]) / np.pi
    for j in range(1, j_max + 1):
        k = m * j
        a_k = np.cos(k * phi) @ d @ np.cos(k * phi) + np.sin(k * phi) @ d @ np.sin(k * phi)
        prob += 2 / np.pi * a_k * (np.sin(j * alpha[:-1]) - np.sin(j * alpha[1:])) / j
    return prob


def _marginals(rho):
    """name -> (function of the angles, bin edges, exact bin probabilities)."""
    cos_e, phi_e = np.linspace(-1, 1, 21), np.linspace(0, 2 * np.pi, 17)
    return {
        "cos_theta_p": (lambda a: np.cos(a[0]), cos_e, _leg_bin_probs(rho, +1, cos_e, "cos")),
        "cos_theta_m": (lambda a: np.cos(a[2]), cos_e, _leg_bin_probs(rho, -1, cos_e, "cos")),
        "phi_p": (lambda a: a[1], phi_e, _leg_bin_probs(rho, +1, phi_e, "phi")),
        "phi_m": (lambda a: a[3], phi_e, _leg_bin_probs(rho, -1, phi_e, "phi")),
        "cos_dphi": (lambda a: np.cos(a[1] - a[3]), cos_e, _cos_dphi_probs(rho, 1, cos_e)),
        "cos_2dphi": (lambda a: np.cos(2 * (a[1] - a[3])), cos_e, _cos_dphi_probs(rho, 2, cos_e)),
    }


def _chi2_pvalue(values, edges, prob):
    counts, _ = np.histogram(values, edges)
    expected = counts.sum() * prob
    return stats.chi2.sf(np.sum((counts - expected) ** 2 / expected), len(counts) - 1)


def _moment_pvalue(angles, rho):
    """Chi-square of the 80 estimated coefficients against those of rho."""
    res = tomography.estimate(*angles)
    d = res.c - basis.coefficient_vector(rho)
    return stats.chi2.sf(d @ np.linalg.solve(res.cov, d), d.size)


# --------------------------------------------------------------------------
# Accept-reject generator
# --------------------------------------------------------------------------
@pytest.mark.parametrize("which", ["sm", "random_pure"])
def test_generate_marginals(which):
    """Marginals of cos(theta+-), phi+-, cos(dphi), cos(2 dphi) against the exact distribution
    (chi-square); efficiency 1/9.  A wrong state is rejected by the same test."""
    if which == "sm":
        rho, wrong = sm.density_matrix(1.6), sm.density_matrix(2.2)
    else:
        rho = basis.random_density_matrix(_rng(11), rank=1)
        wrong = basis.SWAP @ rho @ basis.SWAP       # W+ and W- exchanged
    n = 200_000
    angles, eff = toy.generate(rho, n, _rng(12), return_efficiency=True)
    assert isinstance(angles, toy.Angles) and all(a.shape == (n,) for a in angles)
    assert np.all((angles.theta_p >= 0) & (angles.theta_p <= np.pi))
    assert np.all((angles.phi_m >= 0) & (angles.phi_m < 2 * np.pi))
    assert abs(eff - 1 / 9) < 5 * np.sqrt(1 / 9 * 8 / 9 / (9 * n))
    p_wrong = []
    for name, (fun, edges, prob) in _marginals(rho).items():
        assert np.isclose(prob.sum(), 1.0, atol=1e-10), name
        assert np.all(prob > 0), name
        assert _chi2_pvalue(fun(angles), edges, prob) > P_MIN / 6, name
    for name, (fun, edges, prob) in _marginals(wrong).items():
        p_wrong.append(_chi2_pvalue(fun(angles), edges, prob))
    assert min(p_wrong) < 1e-10


def test_generate_small_samples_and_identity():
    """n = 0 and tiny samples work; rho = 1/9 is accepted everywhere with probability 1/9."""
    r = _rng(13)
    assert all(a.size == 0 for a in toy.generate(basis.ID9 / 9, 0, r))
    assert all(a.size == 5 for a in toy.generate(sm.density_matrix(3.0), 5, r))
    angles, eff = toy.generate(basis.ID9 / 9, 50_000, r, return_efficiency=True)
    assert abs(eff - 1 / 9) < 5 * np.sqrt(1 / 9 * 8 / 9 / (9 * 50_000))
    assert stats.kstest(np.cos(angles.theta_m), "uniform", args=(-1, 2)).pvalue > P_MIN / 2
    assert stats.kstest(angles.phi_p, "uniform", args=(0, 2 * np.pi)).pvalue > P_MIN / 2


def test_generate_rejects_invalid_states():
    r = _rng(14)
    e = np.eye(9)
    bad = basis.ID9 / 9 + 2.0 * (np.outer(e[2], e[2]) - np.outer(e[4], e[4]))   # not positive
    assert np.isclose(np.trace(bad), 1.0) and basis.min_eigenvalue(bad) < 0
    with pytest.raises(ValueError, match="physical"):
        toy.generate(bad, 1000, r)
    with pytest.raises(ValueError):
        toy.generate(2 * basis.ID9 / 9, 10, r)                       # trace 2
    with pytest.raises(ValueError):
        toy.generate(basis.ID9 / 9 + 0.01 * np.eye(9, k=1), 10, r)   # not Hermitian
    with pytest.raises(ValueError, match="physical"):
        toy.generate_per_event([bad], np.ones((100, 1)), r)


def test_invalid_input_raises_at_once():
    """Non-finite states, weights, kappa or rates and sizes that are not integers raise before
    sampling (with nan the accept-reject loops would never accept)."""
    r = _rng(22)
    rho = sm.density_matrix(2.0)
    states, _ = toy.sm_weights(2.0)
    spectrum = sm.OffShellSpectrum.from_config(config.constants())
    cases = [
        (ValueError, lambda: toy.generate(np.full((9, 9), np.nan), 10, r)),
        (ValueError, lambda: toy.generate(rho, 10, r, chunk=0)),
        (ValueError, lambda: toy.generate(rho, -1, r)),
        (TypeError, lambda: toy.generate(rho, 1e3, r)),
        (ValueError, lambda: toy.generate_per_event([rho], np.full((5, 1), np.nan), r)),
        (ValueError, lambda: toy.generate_per_event([rho], np.ones((5, 1)), r, chunk=0)),
        (ValueError, lambda: toy.sm_weights(np.array([np.inf, 2.0]))),
        (ValueError, lambda: toy.affine_weights(states, np.full(80, np.nan))),
        (TypeError, lambda: toy.generate_sm_spectrum(10.0, r, spectrum)),
        (ValueError, lambda: toy.apply_mistag(np.zeros(3), np.zeros(3), np.nan, r)),
        (ValueError, lambda: next(toy.pseudo_experiments(toy.isotropic, -5, 2, r))),
    ]
    with _time_limit(20):
        for error, call in cases:
            with pytest.raises(error):
                call()


def test_isotropic():
    tp, pp, tm, pm = toy.isotropic(100_000, _rng(15))
    for t in (tp, tm):
        assert stats.kstest(np.cos(t), "uniform", args=(-1, 2)).pvalue > P_MIN / 4
    for p in (pp, pm):
        assert stats.kstest(p, "uniform", args=(0, 2 * np.pi)).pvalue > P_MIN / 4
    assert abs(np.corrcoef(np.cos(tp), np.cos(tm))[0, 1]) < 5 / np.sqrt(tp.size)
    assert abs(np.corrcoef(pp, pm)[0, 1]) < 5 / np.sqrt(tp.size)


# --------------------------------------------------------------------------
# Per-event states and the SM with the W* spectrum
# --------------------------------------------------------------------------
def test_sm_weights_reproduce_states():
    kappa = np.concatenate([np.geomspace(1.0, 1e4, 300), [np.sqrt(2.0), 3.7]])
    states, w = toy.sm_weights(kappa)
    assert w.shape == (kappa.size, 3) and np.allclose(w.sum(axis=1), 1.0)
    assert np.allclose(np.einsum("nj,jab->nab", w, states), sm.density_matrix(kappa), atol=1e-12)
    with pytest.raises(ValueError, match="span"):
        toy.affine_weights(states, basis.coefficient_vector(basis.ID9 / 9))


def test_generate_per_event_assigns_states():
    r = _rng(16)
    a, b = basis.random_density_matrix(r, rank=1), sm.density_matrix(2.5)
    n = 60_000
    weights = np.zeros((n, 2))
    weights[::2, 0] = weights[1::2, 1] = 1.0
    angles = toy.generate_per_event([a, b], weights, r, chunk=25_000)
    for sel, rho in ((slice(0, None, 2), a), (slice(1, None, 2), b)):
        assert _moment_pvalue([x[sel] for x in angles], rho) > P_MIN / 2
    assert _moment_pvalue([x[::2] for x in angles], b) < 1e-10
    with pytest.raises(ValueError, match="sum to one"):
        toy.generate_per_event([a, b], np.ones((3, 2)), r)


def test_per_event_acceptance_is_trace_projectors():
    """The acceptance probability of generate_per_event, evaluated with the q functions shared
    between the states, equals sum_j w_ij basis.trace_projectors(states[j]) and the explicit
    9x9 trace Tr[rho_i (Pi+ x Pi-)] of the per-event state (affine weights, rows summing to 1)."""
    r = _rng(23)
    states = np.array([basis.random_density_matrix(r), basis.random_density_matrix(r, rank=1),
                       sm.density_matrix(1.7), basis.random_product_state(r)])
    n = 400
    w = r.normal(size=(n, len(states)))
    w[:, 0] += 1.0 - w.sum(axis=1)
    ang = toy.isotropic(n, r)
    prob = toy._affine_trace(states, w, *ang)
    ref = sum(w[:, j] * basis.trace_projectors(s, *ang) for j, s in enumerate(states))
    assert np.allclose(prob, ref, rtol=0, atol=1e-13)
    proj = np.einsum("nab,ncd->nacbd", basis.projector(ang.theta_p, ang.phi_p, +1),
                     basis.projector(ang.theta_m, ang.phi_m, -1)).reshape(n, 9, 9)
    rho_i = np.einsum("nj,jab->nab", w, states)
    assert np.allclose(prob, np.einsum("nij,nji->n", rho_i, proj).real, rtol=0, atol=1e-13)


def test_generate_sm_spectrum():
    """Angles follow rho_SM(kappa_i) of each event: the sample reproduces the spectrum-averaged
    state, inclusively and in bins of M* = min(M_W+, M_W-), where the inclusive average fails."""
    const = config.constants()
    spectrum = sm.OffShellSpectrum.from_config(const)
    n = 100_000
    ev = toy.generate_sm_spectrum(n, _rng(17), spectrum)
    assert isinstance(ev, toy.SMEvents) and all(a.shape == (n,) for a in ev)
    assert np.all(ev.m_p + ev.m_m < const["m_H"])
    assert np.all(np.minimum(ev.m_p, ev.m_m) >= const["mstar_min"])
    assert abs(np.mean(ev.m_p > ev.m_m) - 0.5) < 5 * np.sqrt(0.25 / n)
    mstar = np.minimum(ev.m_p, ev.m_m)
    rho_all, _ = spectrum.average_density_matrix(n_u=4000, n_y=800)
    for lo, hi in ((0.0, np.inf), (0.0, 30.0), (30.0, np.inf)):
        sel = (mstar >= lo) & (mstar < hi)
        rho_bin, frac = spectrum.average_density_matrix((lo, hi), n_u=4000, n_y=800)
        assert abs(sel.mean() - frac) < 5 * np.sqrt(frac * (1 - frac) / n) + 1e-3
        angles = [a[sel] for a in ev.angles]
        assert _moment_pvalue(angles, rho_bin) > P_MIN / 3
        if (lo, hi) != (0.0, np.inf):
            assert _moment_pvalue(angles, rho_all) < 1e-10
    assert all(a.size == 0 for a in toy.generate_sm_spectrum(0, _rng(18), spectrum))


@pytest.mark.slow
def test_performance_sm_spectrum():
    """1e6 SM events with the W* spectrum within twice the generation target of about 15 s."""
    spectrum = sm.OffShellSpectrum.from_config(config.constants())
    t0 = time.perf_counter()
    ev = toy.generate_sm_spectrum(1_000_000, _rng(24), spectrum)
    assert ev.theta_p.size == 1_000_000 and time.perf_counter() - t0 < 30.0


# --------------------------------------------------------------------------
# Mistag and pseudo-experiments
# --------------------------------------------------------------------------
def _unit(theta, phi):
    return np.stack([np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)], -1)


def test_apply_mistag():
    r = _rng(19)
    theta, phi = toy.uniform_directions(100_000, r)
    th2, ph2, flipped = toy.apply_mistag(theta, phi, 0.3, r)
    assert abs(flipped.mean() - 0.3) < 5 * np.sqrt(0.3 * 0.7 / theta.size)
    assert np.allclose(_unit(th2, ph2)[flipped], -_unit(theta, phi)[flipped])
    assert np.array_equal(th2[~flipped], theta[~flipped]) and np.array_equal(ph2[~flipped], phi[~flipped])
    assert np.all((th2 >= 0) & (th2 <= np.pi) & (ph2 >= 0) & (ph2 < 2 * np.pi))
    w = np.where(np.arange(theta.size) % 3 == 0, 1.0, 0.0)          # per-event rates
    assert np.array_equal(toy.apply_mistag(theta, phi, w, r)[2], w == 1.0)
    w = r.uniform(0.0, 0.5, theta.size)
    assert abs(toy.apply_mistag(theta, phi, w, r)[2].mean() - 0.25) < 5 * np.sqrt(0.25 * 0.75 / theta.size)
    for bad in (1.5, -0.2, np.nan):
        with pytest.raises(ValueError):
            toy.apply_mistag(theta, phi, bad, r)


def test_pseudo_experiments():
    """Consecutive blocks of one event stream: nothing lost or repeated; Poisson sizes."""
    toys = list(toy.pseudo_experiments(toy.isotropic, 1000, 7, _rng(20), batch=2500))
    assert len(toys) == 7 and all(isinstance(t, toy.Angles) and t.theta_p.size == 1000 for t in toys)
    r = _rng(20)
    stream = [toy.isotropic(n, r) for n in (2500, 2500, 2000)]     # the last batch is capped
    for k in range(4):
        joined = np.concatenate([t[k] for t in toys])
        assert np.array_equal(joined, np.concatenate([s[k] for s in stream])[:7000])
    sizes = [t.theta_p.size for t in toy.pseudo_experiments(toy.isotropic, 50, 400, _rng(21),
                                                            poisson=True, batch=3000)]
    assert abs(np.mean(sizes) - 50) < 5 * np.sqrt(50 / 400)
    assert abs(np.var(sizes, ddof=1) / 50 - 1) < 5 * np.sqrt(2 / 399)
