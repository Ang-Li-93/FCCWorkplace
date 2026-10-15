"""Analytic SM state of H -> W W* and the W* mass spectrum (PLAN.md Sec. 3.4)."""
import numpy as np
import pytest

from qtomo import basis, config, sm

# 2302.00683 does not state its masses; these round values reproduce its figure labels.
M_H, M_W = 125.0, 80.4


def _entropy(rho):
    ev = np.linalg.eigvalsh(basis.reduced_wplus(rho))
    ev = ev[ev > 1e-15]
    return float(-np.sum(ev * np.log(ev)))


def _c2(rho):
    """2 max(0, Tr rho^2 - Tr rho_A^2, Tr rho^2 - Tr rho_B^2) (PLAN.md Sec. 3.5)."""
    p = basis.purity(rho)
    return 2 * max(0.0, p - basis.purity(basis.reduced_wplus(rho)), p - basis.purity(basis.reduced_wminus(rho)))


def test_kappa_definition():
    assert np.isclose(sm.kappa(M_H, M_W, M_H - M_W), 1.0)       # threshold
    f = np.linspace(0.05, 0.55, 11)
    eq313 = 1 + (M_H ** 2 - (1 + f) ** 2 * M_W ** 2) / (2 * f * M_W ** 2)   # paper Eq. (3.13)
    assert np.allclose(sm.kappa(M_H, M_W, f * M_W), eq313)
    assert np.allclose(sm.kappa(M_H, 30.0, M_W), sm.kappa(M_H, M_W, 30.0))


@pytest.mark.parametrize("k", [1.0, 1.4, 3.0, 25.0])
def test_state_is_pure_and_normalised(k):
    rho = sm.density_matrix(k)
    assert np.isclose(np.trace(rho).real, 1.0)
    assert np.isclose(basis.purity(rho), 1.0)
    assert basis.min_eigenvalue(rho) > -1e-14


def test_closed_form_in_kappa_matches_state():
    k = np.linspace(1.0, 30.0, 50)
    for got, ref in zip(sm.coefficients(k), basis.coefficients(sm.density_matrix(k))):
        assert np.allclose(got, ref, atol=1e-14)


@pytest.mark.parametrize("m_H,M_V", [(125.0, 80.4), (125.2, 80.3692)])
def test_paper_closed_forms_match_state(m_H, M_V):
    """2302.00683 Eqs. (3.5)-(3.6) agree with |Psi_H> coefficient by coefficient (all 80):
    the paper and PLAN.md Sec. 3.4 share the phase conventions, no local unitary needed."""
    f = np.linspace(0.01, (m_H - M_V) / M_V - 1e-6, 25)
    got = sm.coefficients_paper(m_H, M_V, f)
    ref = basis.coefficients(sm.density_matrix(sm.kappa(m_H, M_V, f * M_V)))
    for a, b in zip(got, ref):
        assert np.allclose(a, b, atol=1e-13)


def test_paper_identities_and_eq_3_8():
    for k in (1.0, 1.7, 6.0):
        _, _, h = sm.coefficients(k)
        assert np.isclose(h[3, 3], 2 * (h[0, 5] ** 2 + 2 * h[3, 3] ** 2))   # Eq. (3.9)
        assert np.isclose(4 * (h[2, 2] + h[3, 3]), 1.0)                     # Tr rho = 1
        expected = np.zeros((9, 9))
        for i in (2, 6):
            for j in (2, 6):
                expected[i, j] = 2 * h[3, 3]
            expected[i, 4] = expected[4, i] = 2 * h[0, 5]
        expected[4, 4] = 4 * h[2, 2]                                         # Eq. (3.8)
        assert np.allclose(sm.density_matrix(k), expected)


@pytest.mark.parametrize("mstar,entropy,c2", [(4.0, 0.062, 0.039), (12.0, 0.35, 0.31),
                                              (20.0, 0.66, 0.71), (40.0, 1.1, 1.3)])
def test_paper_figure_labels(mstar, entropy, c2):
    """Entanglement entropy (Fig. 3) and C2 (Fig. 4, right) of 2302.00683 at the labelled
    W* masses.  The labels carry two significant figures, hence the tolerances."""
    rho = sm.density_matrix(sm.kappa(M_H, M_W, mstar))
    tol_s = 0.006 if entropy < 1 else 0.05
    tol_c = 0.006 if c2 < 1 else 0.05
    assert _entropy(rho) == pytest.approx(entropy, abs=tol_s)
    assert _c2(rho) == pytest.approx(c2, abs=tol_c)


def test_decohered_state():
    rho = sm.density_matrix(1.7)
    dec = sm.decohered(rho)
    assert np.allclose(dec, np.diag(np.diag(rho)))
    assert np.isclose(np.trace(dec).real, 1.0)
    assert _c2(dec) == 0.0
    f, g, h = basis.coefficients(dec)
    allowed_f = {2, 7}
    assert all(abs(f[a]) < 1e-15 and abs(g[a]) < 1e-15 for a in range(8) if a not in allowed_f)
    assert all(abs(h[a, b]) < 1e-15 for a in range(8) for b in range(8)
               if not (a in allowed_f and b in allowed_f))


# --------------------------------------------------------------------------
# W* mass spectrum
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def spectrum():
    return sm.OffShellSpectrum.from_config(config.constants())


def test_offshell_density_support_and_symmetry():
    c = config.constants()
    m1 = np.array([80.0, 30.0, 70.0, 60.0, 10.0])
    m2 = np.array([30.0, 80.0, 70.0, 66.0, 20.0])
    d = sm.offshell_density(m1, m2, c["m_H"], c["m_W"], c["Gamma_W"])
    assert d[0] > 0 and np.isclose(d[0], d[1])
    assert d[2] == 0.0 and d[3] == 0.0 and d[4] > 0


def test_offshell_sampler_matches_grid(spectrum):
    c = config.constants()
    mp, mm = spectrum.sample(200000, np.random.default_rng(7))
    assert np.all(mp + mm < c["m_H"]) and np.all(np.minimum(mp, mm) >= c["mstar_min"])
    assert abs(np.mean(mp < mm) - 0.5) < 0.006
    mh, ml, w = spectrum.grid(2000, 2000)
    for sample, grid_vals, points in ((np.minimum(mp, mm), ml, np.linspace(5, 44, 14)),
                                      (np.maximum(mp, mm), mh, np.linspace(50, 100, 11))):
        cdf_grid = np.array([w[grid_vals < x].sum() for x in points])
        cdf_mc = np.array([np.mean(sample < x) for x in points])
        assert np.max(np.abs(cdf_grid - cdf_mc)) < 0.006


def test_spectrum_average(spectrum):
    c = config.constants()
    rho, frac = spectrum.average_density_matrix()
    assert frac == pytest.approx(1.0)
    assert np.isclose(np.trace(rho).real, 1.0) and basis.min_eigenvalue(rho) > -1e-12
    assert basis.purity(rho) < 1.0
    real = basis.subspace("rotation_invariant_real")
    v = basis.coefficient_vector(rho)
    assert np.allclose(real @ (real.T @ v), v, atol=1e-12)
    rho_fine, _ = spectrum.average_density_matrix(n_u=4000, n_y=800)
    assert np.allclose(rho, rho_fine, atol=2e-4)
    mp, mm = spectrum.sample(200000, np.random.default_rng(9))
    k = sm.kappa(c["m_H"], mp, mm)
    d = 2 + k ** 2
    assert np.mean(1 / d) == pytest.approx(rho[2, 2].real, abs=3e-3)
    assert np.mean(k / d) == pytest.approx(-rho[2, 4].real, abs=3e-3)
    assert np.mean(k ** 2 / d) == pytest.approx(rho[4, 4].real, abs=3e-3)
    rho_hi, frac_hi = spectrum.average_density_matrix(mstar_range=(30.0, np.inf))
    assert 0 < frac_hi < 1
    assert _c2(rho_hi) > _c2(rho)
