"""Linear response of the reco moments and unfolding (PLAN.md Sec. 6.3, items 2-3)."""
import numpy as np
import pytest
from scipy import stats as st
from scipy.linalg import block_diag
from scipy.optimize import least_squares

from qtomo import basis, response, reweight, sm

KAPPA = 1.7                 # SM state at M_W* of about 30 GeV
W_MISTAG = 0.2              # d/u confusion on the W- leg of the toy detector
N_BASE = 1_000_000          # isotropic base sample (S2 analogue)
N_DATA = 100_000            # SM pseudo-data


def _rng(seed=99):
    return np.random.default_rng(seed)


def _isotropic(n, rng):
    return (np.arccos(rng.uniform(-1, 1, n)), rng.uniform(0, 2 * np.pi, n),
            np.arccos(rng.uniform(-1, 1, n)), rng.uniform(0, 2 * np.pi, n))


def _sample(rho, n, rng, chunk=200_000):
    """Accept-reject from (3/4pi)^2 Tr[rho (Pi+ x Pi-)] (basis.trace_projectors <= 1)."""
    out, have = [], 0
    while have < n:
        a = np.array(_isotropic(chunk, rng))
        keep = rng.uniform(size=chunk) < basis.trace_projectors(rho, *a)
        out.append(a[:, keep])
        have += int(keep.sum())
    return tuple(np.concatenate(out, axis=1)[:, :n])


def _direction_angles(v):
    return np.arccos(np.clip(v[..., 2], -1, 1)), np.mod(np.arctan2(v[..., 1], v[..., 0]), 2 * np.pi)


def _unit(theta, phi):
    return np.stack([np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)], axis=-1)


def _detector(true, rng, sigma=0.15, w_m=W_MISTAG):
    """Toy detector: Gaussian smearing of both analyser directions (sigma per Cartesian
    component, then renormalised), the W- analyser flipped with probability w_m, and a
    theta-dependent acceptance (1 - 0.6 cos^2 theta+) x (|cos theta-| < 0.9) on reco angles."""
    tp, fp, tm, fm = true
    rtp, rfp = _direction_angles(_unit(tp, fp) + sigma * rng.normal(size=(tp.size, 3)))
    rtm, rfm = _direction_angles(_unit(tm, fm) + sigma * rng.normal(size=(tm.size, 3)))
    flip = rng.uniform(size=tp.size) < w_m
    at, af = basis.antipode(rtm, rfm)
    rtm, rfm = np.where(flip, at, rtm), np.where(flip, af, rfm)
    eff = (1 - 0.6 * np.cos(rtp) ** 2) * (np.abs(np.cos(rtm)) < 0.9)
    return (rtp, rfp, rtm, rfm), rng.uniform(size=tp.size) < eff


def _quadrature_pairs(n_cos=6, n_phi=12):
    """(sphere x sphere) product quadrature as weighted 'events', sum of weights = 1."""
    th, ph, w = basis.sphere_quadrature(n_cos, n_phi)
    angles = (np.repeat(th, th.size), np.repeat(ph, ph.size), np.tile(th, th.size), np.tile(ph, ph.size))
    return angles, np.outer(w, w).ravel() / (4 * np.pi) ** 2


def _moments(angles, w_p=0.0, w_m=0.0):
    """[1, basis.estimator_vector] built directly from basis."""
    x = basis.estimator_vector(*angles, w_p, w_m)
    return np.hstack([np.ones((x.shape[0], 1)), x])


@pytest.fixture(scope="module")
def toy():
    """Response from a large isotropic base sample through the toy detector, and an
    independently generated SM pseudo-data sample through the same detector."""
    rng = _rng(7)
    rho = sm.density_matrix(KAPPA)
    c_sm = basis.coefficient_vector(rho)
    true_b = _isotropic(N_BASE, rng)
    reco_b, sel_b = _detector(true_b, rng)
    A, C = response.build_response(true_b, reco_b, sel_b, mistag=(0.0, W_MISTAG), cov_at=c_sm)
    true_d = _sample(rho, N_DATA, rng)
    reco_d, sel_d = _detector(true_d, rng)
    s, V = response.observed_sums(reco_d, sel_d, mistag=(0.0, W_MISTAG))
    return {"c_sm": c_sm, "A": A, "C": C, "s": s, "V": V, "base": (true_b, reco_b, sel_b)}


# --------------------------------------------------------------------------
# Moments and the response matrix
# --------------------------------------------------------------------------
def test_reco_moments_layout():
    angles = _isotropic(100, _rng(1))
    m = response.reco_moments(*angles, 0.1, 0.25)
    assert m.shape == (100, 81) and np.all(m[:, 0] == 1.0)
    assert np.array_equal(m[:, 1:], basis.estimator_vector(*angles, 0.1, 0.25))
    assert len(response.MOMENT_LABELS) == 81 and response.MOMENT_LABELS[0] == "n"
    assert response.MOMENT_LABELS[1:] == basis.COEFF_LABELS


def test_identity_detector_response_is_identity():
    """Perfect detector: A = 1 exactly (quadrature 'events', E_iso[x (1 + c.phi)] = c), and
    within the statistical errors for an isotropic MC base sample."""
    angles, qw = _quadrature_pairs()
    assert np.allclose(response.build_response(angles, angles, base_weights=qw), np.eye(81), atol=1e-12)
    true = _isotropic(200_000, _rng(2))
    A = response.build_response(true, true)
    # per-entry errors of A_jk = mean of m_j (1, phi)_k
    m2 = np.zeros((81, 81))
    for start in range(0, 200_000, 50_000):
        sl = slice(start, start + 50_000)
        a = tuple(t[sl] for t in true)
        m = _moments(a)
        d = np.hstack([np.ones((m.shape[0], 1)), reweight.phi_functions(*a)])
        m2 += (m ** 2).T @ d ** 2
    err = np.sqrt(np.maximum(m2 / 200_000 - A ** 2, 1e-300) / 200_000)
    pull = (A - np.eye(81)) / err
    assert A[0, 0] == 1.0
    assert np.max(np.abs(pull[1:, :])) < 6 and np.max(np.abs(pull[0, 1:])) < 6      # union bound over 6560 entries


@pytest.mark.parametrize("w", [0.15, 0.35])
def test_mistag_response_exact(w):
    """Flipping the W- analyser with probability w: A = diag(1, 1_8, D, 1_8 x D),
    D = basis.mistag_dilution(w), for uncorrected estimators; A = 1 with the correction."""
    angles, qw = _quadrature_pairs()
    flipped = basis.antipode(angles[2], angles[3])
    true = tuple(np.concatenate([a, a]) for a in angles)
    reco = (true[0], true[1], np.concatenate([angles[2], flipped[0]]), np.concatenate([angles[3], flipped[1]]))
    bw = np.concatenate([(1 - w) * qw, w * qw])
    d = basis.mistag_dilution(w)
    expected = block_diag(1.0, np.eye(8), d, np.kron(np.eye(8), d))
    assert np.allclose(response.build_response(true, reco, base_weights=bw), expected, atol=1e-12)
    assert np.allclose(response.build_response(true, reco, base_weights=bw, mistag=(0.0, w)), np.eye(81), atol=1e-12)


def test_response_is_exactly_linear_in_target():
    """A (1, c) equals the reco sums of the base reweighted with 9 Tr[rho Pi Pi]
    (basis.trace_projectors), for a deterministic detector (fixed rotation of both
    analysers, a deterministic flip pattern, hard acceptance); normalised moments agree."""
    angles, qw = _quadrature_pairs()
    rot = np.array([[1, 0, 0], [0, np.cos(0.3), -np.sin(0.3)], [0, np.sin(0.3), np.cos(0.3)]])
    rtp, rfp = _direction_angles(_unit(angles[0], angles[1]) @ rot.T)
    rtm, rfm = _direction_angles(_unit(angles[2], angles[3]) @ rot.T)
    flip = angles[3] < 1.0
    at, af = basis.antipode(rtm, rfm)
    reco = (rtp, rfp, np.where(flip, at, rtm), np.where(flip, af, rfm))
    sel = np.abs(np.cos(rtp)) < 0.8
    A = response.build_response(angles, reco, sel, base_weights=qw, mistag=(0.0, 0.1))
    m = _moments(tuple(r[sel] for r in reco), 0.0, 0.1)
    r = _rng(3)
    for rho in (sm.density_matrix(KAPPA), basis.random_density_matrix(r), basis.random_density_matrix(r, rank=1)):
        c = basis.coefficient_vector(rho)
        w = 9 * qw[sel] * basis.trace_projectors(rho, *(a[sel] for a in angles))
        assert np.allclose(response.expected_sums(A, c), w @ m, atol=1e-12)
        assert np.allclose(response.normalised_moments(A, c), (w @ m)[1:] / w.sum(), atol=1e-12)
    # only the selected events with the total generated weight give the same A
    sub = tuple(a[sel] for a in angles), tuple(a[sel] for a in reco)
    assert np.allclose(response.build_response(*sub, base_weights=qw[sel], mistag=(0.0, 0.1), n_generated=qw.sum()), A,
                       atol=1e-14)


def test_finite_difference_construction_matches(toy):
    """The plan's construction: reweight the base to 1/9 +- eps O_k (reweight targets) and
    difference the reco sums.  Same A as the direct accumulation, for any eps."""
    n = 40_000
    true, reco = (tuple(a[:n] for a in x) for x in toy["base"][:2])
    sel = toy["base"][2][:n]
    A = response.build_response(true, reco, sel, mistag=(0.0, W_MISTAG))
    m = _moments(tuple(a[sel] for a in reco), 0.0, W_MISTAG)
    true_sel = tuple(a[sel] for a in true)

    def sums(rho):
        return reweight.weights_from_isotropic(rho, *true_sel) @ m / n

    iso = sums(reweight.target_isotropic())
    a_fd = np.empty_like(A)
    a_fd[:, 0] = iso
    for k in range(80):
        lo, hi = reweight.basis_element_eps_range(k)
        eps = 0.5 * min(-lo, hi)
        a_fd[:, 1 + k] = (sums(reweight.target_basis_element(k, eps))
                          - sums(reweight.target_basis_element(k, -eps))) / (2 * eps)
        if k in (2, 43, 79):            # one-sided, smaller eps: identical (exact linearity)
            one_sided = (sums(reweight.target_basis_element(k, eps / 7)) - iso) / (eps / 7)
            assert np.allclose(one_sided, a_fd[:, 1 + k], rtol=1e-8, atol=1e-10)
    assert np.allclose(a_fd, A, rtol=1e-9, atol=1e-11)


def test_response_mc_covariance(toy):
    """C from build_response(cov_at=c): the formula sum [b sel 9 Tr[rho Pi Pi]]^2 m m^T / N^2
    on a small sample, and the observed spread of A (1, c) over independent base samples."""
    c = toy["c_sm"]
    rho = sm.density_matrix(KAPPA)
    n = 3000
    true, reco = (tuple(a[:n] for a in x) for x in toy["base"][:2])
    sel = toy["base"][2][:n]
    b = _rng(4).uniform(0.5, 1.5, n)
    A, C = response.build_response(true, reco, sel, base_weights=b, mistag=(0.0, W_MISTAG), cov_at=c)
    y = (b * 9 * basis.trace_projectors(rho, *true))[sel, None] * _moments(tuple(a[sel] for a in reco), 0.0, W_MISTAG)
    assert np.allclose(C, y.T @ y / b.sum() ** 2, rtol=1e-12, atol=1e-16)
    assert np.allclose(A @ np.concatenate([[1.0], c]), y.sum(axis=0) / b.sum(), atol=1e-13)
    rng = _rng(5)
    preds, covs = [], []
    for _ in range(30):
        t = _isotropic(20_000, rng)
        rec, s_ = _detector(t, rng)
        a_r, c_r = response.build_response(t, rec, s_, mistag=(0.0, W_MISTAG), cov_at=c)
        preds.append(a_r @ np.concatenate([[1.0], c]))
        covs.append(c_r)
    d = np.array(preds) - np.mean(preds, axis=0)
    q = np.einsum("ri,ij,rj->r", d, np.linalg.inv(np.mean(covs, axis=0)), d) * 30 / 29
    # E[q] = 81 for a correct covariance (slightly less: Poisson estimate, fixed N); 5 sigma band
    assert abs(q.mean() - 81) < 5 * np.sqrt(2 * 81 / 30)


def test_chunking_and_observed_sums(toy):
    """Chunk size does not matter; observed sums equal direct sums; unselected events
    may carry NaN reco angles."""
    n = 30_000
    true, reco = (tuple(a[:n] for a in x) for x in toy["base"][:2])
    sel = toy["base"][2][:n]
    reco = tuple(np.where(sel, a, np.nan) for a in reco)
    w_m = _rng(6).uniform(0.0, 0.3, n)
    A1, C1 = response.build_response(true, reco, sel, mistag=(0.05, w_m), cov_at=toy["c_sm"], chunk=7777)
    A2, C2 = response.build_response(true, reco, sel, mistag=(0.05, w_m), cov_at=toy["c_sm"])
    assert np.isfinite(A1).all() and np.allclose(A1, A2, rtol=1e-12, atol=1e-14)
    assert np.allclose(C1, C2, rtol=1e-12, atol=1e-16)
    wt = _rng(7).uniform(0.0, 2.0, n)
    s1, V1 = response.observed_sums(reco, sel, weights=wt, mistag=(0.05, w_m), chunk=999)
    m = _moments(tuple(a[sel] for a in reco), 0.05, w_m[sel])
    assert np.allclose(s1, wt[sel] @ m, rtol=1e-12)
    assert np.allclose(V1, (m * wt[sel, None] ** 2).T @ m, rtol=1e-12)


# --------------------------------------------------------------------------
# Unfolding
# --------------------------------------------------------------------------
def test_identity_detector_trivial_recovery():
    """A = 1: unfolding returns the plain moment estimators and the covariance of their mean."""
    data = _sample(sm.density_matrix(KAPPA), 20_000, _rng(8))
    s, V = response.observed_sums(data)
    u = response.unfold(np.eye(81), s, V)
    x = basis.estimator_vector(*data)
    assert np.allclose(u.coefficients, x.mean(axis=0), atol=1e-13)
    assert np.allclose(u.covariance, np.cov(x.T, ddof=0) / len(x), rtol=1e-9, atol=1e-16)
    assert np.isclose(u.n_total, 20_000) and np.isclose(u.condition_number, 1.0) and u.ndf == 0


@pytest.mark.parametrize("subspace", ["full", "rotation_invariant"])
def test_closure_toy_detector(toy, subspace):
    """SM pseudo-data through the toy detector, unfolded with the response of an
    independent isotropic base sample (its statistical covariance included), close
    on the SM coefficients: chi^2 in the subspace and pulls."""
    A, s, V, c_sm = toy["A"], toy["s"], toy["V"], toy["c_sm"]
    u = response.unfold(A, s, V, subspace=subspace, cov_response=toy["C"])
    truth = u.basis.T @ c_sm
    assert np.allclose(u.basis @ truth, c_sm, atol=1e-12)          # the SM lies in the subspace
    resid = u.beta - truth
    assert st.chi2.sf(resid @ np.linalg.solve(u.cov_beta, resid), truth.size) > 1e-4
    assert np.max(np.abs(resid / np.sqrt(np.diag(u.cov_beta)))) < 5
    assert abs(u.n_total - N_DATA) < 5 * u.n_total_error
    assert 1.5 < u.condition_number < 100 and u.converged
    if subspace == "full":       # psi = A^-1 s with covariance A^-1 (V + N_tot^2 C) A^-T
        a_inv = np.linalg.inv(A)
        assert np.allclose(u.theta, a_inv @ s, rtol=1e-10)
        assert np.allclose(u.cov_theta, a_inv @ (V + u.n_total ** 2 * toy["C"]) @ a_inv.T, rtol=1e-8)
    if u.ndf:
        assert u.p_value > 1e-4                                    # GLS chi^2 of the moment equations
    # the detector matters: the raw reco moment means (A = 1) are far from the truth
    raw = response.unfold(np.eye(81), s, V)
    d = raw.coefficients - c_sm
    assert d @ np.linalg.solve(raw.covariance, d) > 1e3
    # the SM coherence h44 is measured with high significance
    k = basis.COEFF_LABELS.index("h44")
    assert u.coefficients[k] / u.errors[k] > 10


def test_unfold_asimov_subspaces_and_regularisation(toy):
    """Asimov sums are recovered exactly in any subspace containing c; Tikhonov
    regularisation interpolates between the GLS solution and the reference."""
    A, V, c = toy["A"], toy["V"], toy["c_sm"]
    asimov = response.expected_sums(A, c, N_DATA)
    for sub in ("full", "rotation_invariant", "rotation_invariant_real", basis.subspace("rotation_invariant_real")):
        u = response.unfold(A, asimov, V, subspace=sub)
        assert np.allclose(u.coefficients, c, atol=1e-10) and np.isclose(u.n_total, N_DATA)
        assert u.chi2 < 1e-12
    ua = response.unfold(A, asimov, V, subspace="rotation_invariant", regularisation=1e4, reference=c)
    assert np.allclose(ua.coefficients, c, atol=1e-10)              # no bias at the reference
    s = toy["s"]
    u0 = response.unfold(A, s, V, subspace="rotation_invariant")
    tiny = response.unfold(A, s, V, subspace="rotation_invariant", regularisation=1e-6)
    assert np.allclose(tiny.coefficients, u0.coefficients, atol=1e-9)
    c_ref = np.zeros(80)
    huge = response.unfold(A, s, V, subspace="rotation_invariant", regularisation=1e14, reference=c_ref)
    assert np.allclose(huge.coefficients, 0.0, atol=1e-7)
    # chi^2 + tau |beta - beta_ref|^2 minimised independently over (psi_0, beta)
    b = basis.subspace("rotation_invariant")
    x = A @ block_diag(1.0, b)
    lw = np.linalg.cholesky(np.linalg.inv(V))
    for tau, ref in ((1.0 / np.median(np.diag(u0.cov_beta)), c_ref), (1e3, 0.5 * c)):
        mid = response.unfold(A, s, V, subspace="rotation_invariant", regularisation=tau, reference=ref)

        def resid(p):
            th = np.concatenate([[p[0]], p[0] * p[1:]])
            return np.concatenate([lw.T @ (s - x @ th), np.sqrt(tau) * (p[1:] - b.T @ ref)])

        sol = least_squares(resid, np.concatenate([[u0.n_total], u0.beta]), method="lm", x_scale="jac",
                            xtol=1e-15, ftol=1e-15, gtol=1e-15)
        assert mid.converged
        assert np.max(np.abs(sol.x[1:] - mid.beta) / np.sqrt(np.diag(u0.cov_beta))) < 1e-5
        assert np.all(np.diag(mid.cov_beta) < np.diag(u0.cov_beta))
    with pytest.raises(ValueError):
        response.unfold(A, s, -V)


def test_linearised_moments(toy):
    """Reco moment means = R c + b around c0: exact at c0, second-order residual, R the
    derivative; R = 1 and b = 0 for a perfect detector."""
    c0 = toy["c_sm"]
    R, b = response.linearised_moments(np.eye(81), c0)
    assert np.allclose(R, np.eye(80)) and np.allclose(b, 0.0)
    A = toy["A"]
    R, b = response.linearised_moments(A, c0)
    assert np.allclose(R @ c0 + b, response.normalised_moments(A, c0), atol=1e-14)
    d = _rng(9).normal(size=80) * 1e-2
    res = [np.abs(response.normalised_moments(A, c0 + t * d) - R @ (c0 + t * d) - b).max() for t in (1.0, 0.5)]
    assert 3.5 < res[0] / res[1] < 4.5
    fd = (response.normalised_moments(A, c0 + 1e-4 * d) - response.normalised_moments(A, c0 - 1e-4 * d)) / 2e-4
    assert np.allclose(fd, R @ d, atol=1e-9)
