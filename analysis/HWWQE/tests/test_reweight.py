"""Decay-angle reweighting (PLAN.md Sec. 3.7)."""
import numpy as np
import pytest
from scipy import stats as st

from qtomo import basis, config, reweight, sm

KAPPA = 1.6
N_TOY = 100_000


def _rng(seed=2024):
    return np.random.default_rng(seed)


def _isotropic(n, rng):
    """Uniform analyser directions for both W bosons (rho = 1/9)."""
    return (np.arccos(rng.uniform(-1, 1, n)), rng.uniform(0, 2 * np.pi, n),
            np.arccos(rng.uniform(-1, 1, n)), rng.uniform(0, 2 * np.pi, n))


def _sample(rho, n, rng, chunk=200_000):
    """Accept-reject from (3/4pi)^2 Tr[rho (Pi+ x Pi-)]: uniform directions accepted
    with probability Tr[...] <= 1 (basis.trace_projectors)."""
    out, have = [], 0
    while have < n:
        a = np.array(_isotropic(chunk, rng))
        keep = rng.uniform(size=chunk) < basis.trace_projectors(rho, *a)
        out.append(a[:, keep])
        have += int(keep.sum())
    return tuple(np.concatenate(out, axis=1)[:, :n])


def _weighted_moments(w, angles, chunk=50_000):
    """Mean of w x (x = basis.estimator_vector) and the covariance of that mean."""
    n = w.size
    s, ss = np.zeros(80), np.zeros((80, 80))
    for start in range(0, n, chunk):
        sl = slice(start, start + chunk)
        y = w[sl, None] * basis.estimator_vector(*(a[sl] for a in angles))
        s += y.sum(axis=0)
        ss += y.T @ y
    mean = s / n
    return mean, (ss / n - np.outer(mean, mean)) / (n - 1)


def _chi2_p(residual, cov):
    return st.chi2.sf(residual @ np.linalg.solve(cov, residual), residual.size)


def _direct_trace(rho, angles):
    """Tr[rho (Pi+ x Pi-)] from explicit 9x9 Kronecker products of the projectors."""
    pp = basis.projector(angles[0], angles[1], +1)
    pm = basis.projector(angles[2], angles[3], -1)
    kron = np.einsum("nab,ncd->nacbd", pp, pm).reshape(-1, 9, 9)
    return np.real(np.einsum("ij,nji->n", rho, kron))


def _quadrature_pairs(n_cos=6, n_phi=12):
    """Product quadrature on (sphere x sphere), exact for the polynomials used here;
    weights normalised to the isotropic distribution (sum = 1)."""
    th, ph, w = basis.sphere_quadrature(n_cos, n_phi)
    angles = (np.repeat(th, th.size), np.repeat(ph, ph.size), np.tile(th, th.size), np.tile(ph, ph.size))
    return angles, np.outer(w, w).ravel() / (4 * np.pi) ** 2


def _targets():
    r = _rng(5)
    return {"sm": reweight.target_sm(KAPPA), "decohered_sm": reweight.target_decohered_sm(KAPPA),
            "random": basis.random_density_matrix(r), "random_rank2": basis.random_density_matrix(r, rank=2)}


# --------------------------------------------------------------------------
# Linear form and per-event states
# --------------------------------------------------------------------------
def test_phi_functions_give_isotropic_weight():
    """9 Tr[rho (Pi+ x Pi-)] = 1 + c . phi, checked against explicit Kronecker products."""
    r = _rng(1)
    angles = _isotropic(300, r)
    phi = reweight.phi_functions(*angles)
    assert phi.shape == (300, 80)
    for _ in range(5):
        rho = basis.random_density_matrix(r)
        direct = 9 * _direct_trace(rho, angles)
        assert np.allclose(1 + phi @ basis.coefficient_vector(rho), direct, atol=1e-12)
        assert np.allclose(reweight.weights_from_isotropic(rho, *angles), direct, atol=1e-12)


def test_per_event_states_match_fixed_states():
    """Per-event targets (stacks, PerEventStates, kappa arrays) agree event by event with the
    fixed-state evaluation, independently of the chunk size."""
    r = _rng(2)
    n = 57
    angles = _isotropic(n, r)
    stack = np.array([basis.random_density_matrix(r) for _ in range(n)])
    loop = np.array([basis.trace_projectors(rho, *(a[i] for a in angles)) for i, rho in enumerate(stack)])
    assert np.allclose(reweight.trace_states(stack, *angles, chunk=10), loop, atol=1e-13)
    per_event = reweight.target_from_coefficients(basis.coefficient_vector(stack))
    assert isinstance(per_event, reweight.PerEventStates) and len(per_event) == n
    assert np.allclose(per_event.density_matrices(slice(3, 5)), stack[3:5], atol=1e-13)
    assert np.allclose(reweight.trace_states(per_event, *angles, chunk=8), loop, atol=1e-13)
    kap = 1.0 + r.exponential(2.0, n)
    for build, ref in ((reweight.target_sm, sm.density_matrix),
                       (reweight.target_decohered_sm, lambda k: sm.decohered(sm.density_matrix(k)))):
        target = build(kap)
        assert isinstance(target, reweight.PerEventStates)
        expected = np.array([9 * basis.trace_projectors(ref(k), *(a[i] for a in angles))
                             for i, k in enumerate(kap)])
        assert np.allclose(reweight.weights_from_isotropic(target, *angles, chunk=16), expected, atol=1e-12)
        assert np.allclose(target.density_matrices(), ref(kap), atol=1e-13)
    with pytest.raises(ValueError):
        reweight.trace_states(stack[:10], *angles)


def test_target_builders():
    """SM and decohered SM targets are sm.density_matrix and its diagonal part."""
    rho = sm.density_matrix(KAPPA)
    assert np.allclose(reweight.target_sm(KAPPA), rho)
    dec = reweight.target_decohered_sm(KAPPA)
    assert np.allclose(dec, np.diag(np.diag(rho))) and np.isclose(np.trace(dec).real, 1.0)
    assert np.abs(rho - np.diag(np.diag(rho))).max() > 0.1          # coherences really removed
    assert np.allclose(reweight.target_isotropic(), basis.ID9 / 9)


# --------------------------------------------------------------------------
# Isotropic base: exact expectations and toys
# --------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["sm", "decohered_sm", "random", "random_rank2"])
def test_isotropic_weights_exact(name):
    """Over the isotropic distribution (exact quadrature) E[w] = 1 and E[w x] = c_target."""
    rho = _targets()[name]
    angles, qw = _quadrature_pairs()
    w = reweight.weights_from_isotropic(rho, *angles)
    assert np.isclose(qw @ w, 1.0, atol=1e-13)
    x = basis.estimator_vector(*angles)
    assert np.allclose((qw * w) @ x, basis.coefficient_vector(rho), atol=1e-12)


def test_isotropic_weight_bound():
    """0 <= w <= 9 for physical targets; the bound is reached for a product of coherent
    states at its own analyser directions (Pi+ x Pi- is a rank-1 projector)."""
    r = _rng(3)
    angles = _isotropic(20_000, r)
    for _ in range(10):
        rank = int(r.integers(1, 10))
        w = reweight.weights_from_isotropic(basis.random_density_matrix(r, rank=rank), *angles)
        assert w.min() >= -1e-12 and w.max() <= 9 + 1e-12
    t0, f0, t1, f1 = 0.7, 2.1, 2.3, 4.0
    coherent = np.kron(basis.projector(t0, f0, +1), basis.projector(t1, f1, -1))
    assert np.isclose(reweight.weights_from_isotropic(coherent, t0, f0, t1, f1), 9.0)


@pytest.mark.parametrize("name", ["sm", "decohered_sm", "random"])
def test_isotropic_toys_reproduce_target(name):
    """Weighted isotropic toys: mean weight 1, max <= 9, moments = target coefficients."""
    rho = _targets()[name]
    angles = _isotropic(N_TOY, _rng(11))
    w = reweight.weights_from_isotropic(rho, *angles)
    assert abs(w.mean() - 1.0) < 5 * w.std() / np.sqrt(w.size)
    assert w.max() <= 9 + 1e-12
    mean, cov = _weighted_moments(w, angles)
    assert _chi2_p(mean - basis.coefficient_vector(rho), cov) > 1e-4


# --------------------------------------------------------------------------
# Non-isotropic base: ratio weights
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def sm_average():
    """SM state averaged over the W* mass spectrum (rank 2: bounded ratio weights)."""
    rho, _ = sm.OffShellSpectrum.from_config(config.constants()).average_density_matrix()
    return rho


def test_ratio_weights_sm_to_decohered(sm_average):
    """SM base (m_W*-averaged) reweighted to its decohered state reproduces the decohered
    coefficients; nothing is rejected at the default eps."""
    target = sm.decohered(sm_average)
    angles = _sample(sm_average, N_TOY, _rng(21))
    w, rejected, frac = reweight.weights_ratio(target, sm_average, *angles)
    assert frac == 0.0 and not rejected.any()
    assert abs(w.mean() - 1.0) < 5 * w.std() / np.sqrt(w.size)
    mean, cov = _weighted_moments(w, angles)
    assert _chi2_p(mean - basis.coefficient_vector(target), cov) > 1e-4
    # the SM coherences (h16, h44, ...) are really removed
    coh = [basis.COEFF_LABELS.index(k) for k in ("h16", "h27", "h44", "h55")]
    assert np.all(np.abs(basis.coefficient_vector(sm_average)[coh]) > 10 * np.sqrt(np.diag(cov))[coh])


def test_ratio_weights_bounded_base():
    """SM base diluted with 1/9, rho_b = (1 - lam) rho_SM(kappa) + lam/9, for several kappa ->
    decohered SM target.  Tr[rho_b Pi Pi] >= lam/9 bounds the weights, so sample-variance
    errors are valid and the strict threshold applies."""
    lam = 0.2
    r = _rng(31)
    parts, weights, truths = [], [], []
    for k in (1.05, 1.6, 3.0, 8.0):
        base = (1 - lam) * sm.density_matrix(k) + lam * basis.ID9 / 9
        target = sm.decohered(sm.density_matrix(k))
        a = _sample(base, N_TOY // 4, r)
        w, _, frac = reweight.weights_ratio(target, base, *a)
        assert frac == 0.0 and w.max() <= 9 / lam
        parts.append(a)
        weights.append(w)
        truths.append(basis.coefficient_vector(target))
    angles = tuple(np.concatenate([p[i] for p in parts]) for i in range(4))
    mean, cov = _weighted_moments(np.concatenate(weights), angles)
    assert _chi2_p(mean - np.mean(truths, axis=0), cov) > 1e-4


@pytest.mark.parametrize("kappa", [1.6, 3.0])
def test_ratio_weights_pure_base_tail(kappa):
    """For a pure base (SM at fixed kappa) the base density vanishes on a codimension-2 set
    of directions, so the weights have a tail P(w > W) ~ W^-2 (reweight.weights_ratio):
    slope of log P(w > W) against log W between W = 3 and 100 within 0.3 of -2, and the
    mean weight still close to 1 (the target is fully supported)."""
    rho = sm.density_matrix(kappa)
    angles = _sample(rho, 400_000, _rng(61))
    w, _, frac = reweight.weights_ratio(sm.decohered(rho), rho, *angles)
    edges = np.array([3.0, 10.0, 30.0, 100.0])
    surv = np.array([np.mean(w > x) for x in edges])
    slope = np.polyfit(np.log(edges), np.log(surv), 1)[0]
    assert frac == 0.0 and abs(slope + 2.0) < 0.3
    assert abs(w.mean() - 1.0) < 0.02


def test_ratio_weights_rejection():
    """Base |+1><+1| x 1/3 vanishes at theta+ = pi, where the target |-1><-1| x 1/3 peaks.
    Analytically Tr[rho_b Pi Pi] = (1+cos)^2/12 and w = ((1-cos)/(1+cos))^2; with
    x0 = sqrt(12 eps) the rejected base fraction is (x0/2)^3 and the retained target
    probability E_b[w] = (1 - x0/2)^3."""
    up, down = np.diag([1.0, 0, 0]).astype(complex), np.diag([0, 0, 1.0]).astype(complex)
    rho_b, rho_t = np.kron(up, basis.ID3 / 3), np.kron(down, basis.ID3 / 3)
    eps = 0.01
    angles = _sample(rho_b, N_TOY, _rng(41))
    w, rejected, frac = reweight.weights_ratio(rho_t, rho_b, *angles, eps=eps)
    cos = np.cos(angles[0])
    assert np.array_equal(rejected, (1 + cos) ** 2 / 12 < eps) and np.all(w[rejected] == 0)
    assert np.allclose(w[~rejected], ((1 - cos[~rejected]) / (1 + cos[~rejected])) ** 2)
    x0 = np.sqrt(12 * eps)
    p_rej = (x0 / 2) ** 3
    assert frac == rejected.mean() and frac > 0
    assert abs(frac - p_rej) < 5 * np.sqrt(p_rej * (1 - p_rej) / N_TOY)
    assert abs(w.mean() - (1 - x0 / 2) ** 3) < 5 * w.std() / np.sqrt(N_TOY)
    # the same base without a cut: nothing rejected, w unbounded near theta+ = pi
    w0, rej0, frac0 = reweight.weights_ratio(rho_t, rho_b, *angles, eps=0.0)
    assert frac0 == 0.0 and not rej0.any() and w0.max() > w.max()


# --------------------------------------------------------------------------
# Single basis elements
# --------------------------------------------------------------------------
def test_basis_element_positivity():
    """Allowed eps from the Gell-Mann spectra: T1..T7 have eigenvalues (1, 0, -1), T8 has
    (1, 1, -2)/sqrt3; Kronecker products multiply them."""
    s3 = np.sqrt(3.0)
    expected = {"f1": (-1 / 9, 1 / 9), "g3": (-1 / 9, 1 / 9), "f8": (-s3 / 9, s3 / 18),
                "h44": (-1 / 9, 1 / 9), "h88": (-1 / 12, 1 / 6), "h18": (-s3 / 18, s3 / 18)}
    for label, (lo, hi) in expected.items():
        k = basis.COEFF_LABELS.index(label)
        assert np.allclose(reweight.basis_element_eps_range(label), (lo, hi))
        assert np.allclose(reweight.basis_element_eps_range(k), (lo, hi))
        for eps in (lo, hi):
            rho = reweight.target_basis_element(k, eps)
            assert abs(basis.min_eigenvalue(rho)) < 1e-12 and np.isclose(np.trace(rho).real, 1.0)
            assert np.allclose(basis.coefficient_vector(rho), eps * np.eye(80)[k], atol=1e-14)
            with pytest.raises(ValueError):
                reweight.target_basis_element(k, 1.01 * eps)
    with pytest.raises(ValueError):
        reweight.target_basis_element(80, 0.01)
    c_bad = np.zeros(80)
    c_bad[basis.COEFF_LABELS.index("h44")] = 0.2
    with pytest.raises(ValueError):
        reweight.target_from_coefficients(c_bad)
    c_sm = basis.coefficient_vector(sm.density_matrix(KAPPA))
    assert np.allclose(reweight.target_from_coefficients(c_sm), sm.density_matrix(KAPPA))


@pytest.mark.parametrize("label", ["f3", "g1", "h16", "h44", "h88"])
def test_basis_element_derivative(label):
    """d/d eps of the weighted moments for the targets 1/9 +- eps O_k is the unit vector e_k:
    exactly by quadrature, and within the statistical errors for isotropic toys."""
    k = basis.COEFF_LABELS.index(label)
    eps = 0.5 * min(-reweight.basis_element_eps_range(k)[0], reweight.basis_element_eps_range(k)[1])
    plus, minus = reweight.target_basis_element(k, eps), reweight.target_basis_element(k, -eps)
    angles, qw = _quadrature_pairs()
    x = basis.estimator_vector(*angles)
    dw = (reweight.weights_from_isotropic(plus, *angles) - reweight.weights_from_isotropic(minus, *angles)) / (2 * eps)
    assert np.allclose((qw * dw) @ x, np.eye(80)[k], atol=1e-12)
    angles = _isotropic(N_TOY, _rng(51))
    dw = (reweight.weights_from_isotropic(plus, *angles) - reweight.weights_from_isotropic(minus, *angles)) / (2 * eps)
    deriv, cov = _weighted_moments(dw, angles)
    z = deriv / np.sqrt(np.diag(cov))
    assert np.argmax(np.abs(z)) == k and z[k] > 20
    assert _chi2_p(deriv - np.eye(80)[k], cov) > 1e-4
