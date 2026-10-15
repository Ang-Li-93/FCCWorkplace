"""CGLMP operator, optimised I3, concurrence bound C2 and entanglement entropy
(PLAN.md Sec. 3.5; CONVENTIONS.md Sec. 6)."""
import time

import numpy as np
import pytest
from scipy.linalg import expm
from scipy.stats import unitary_group

from qtomo import basis, bell, config, sm

T = basis.GELL_MANN
# 2302.00683 does not state its masses; these round values reproduce its figure labels.
M_H, M_W = 125.0, 80.4


def _rng(seed=2718):
    return np.random.default_rng(seed)


def _local_unitary(rng):
    """Haar-random U x V (scipy, independent of the optimiser's own sampler)."""
    return np.kron(unitary_group.rvs(3, random_state=rng), unitary_group.rvs(3, random_state=rng))


def _rotate(rho, m):
    return m @ rho @ m.conj().T


def _plan_operator():
    """B transcribed term by term from PLAN.md Sec. 3.5."""
    k = np.kron
    t1, t2, t4, t5, t6, t7 = T[0], T[1], T[3], T[4], T[5], T[6]
    return (k(t4, t4) + k(t5, t5)
            - (k(t1, t1) + k(t1, t6) + k(t6, t1) + k(t6, t6)
               + k(t2, t2) + k(t2, t7) + k(t7, t2) + k(t7, t7)) / np.sqrt(3))


def _cglmp_operator():
    """CGLMP Bell operator for d = 3 from first principles (Collins et al., PRL 88 (2002) 040404),
    I3 = P(A1=B1) + P(B1=A2+1) + P(A2=B2) + P(B2=A1) - P(A1=B1-1) - P(B1=A2) - P(A2=B2-1) - P(B2=A1-1)
    (outcomes mod 3), with the settings that are optimal for sum_j |jj>/sqrt3:
    |k>_{A,a} = sum_j exp(2 pi i j (k + alpha_a)/3)|j>/sqrt3,
    |l>_{B,b} = sum_j exp(-2 pi i j (l - beta_b)/3)|j>/sqrt3, alpha = (0, 1/2), beta = (1/4, -1/4)."""
    j = np.arange(3)

    def projectors(kets):
        return [np.outer(e, e.conj()) for e in kets]

    # row k (l) of the 3x3 argument is (k + alpha) j  ((l - beta) j)
    pa = [projectors(np.exp(2j * np.pi * np.outer(j + a, j) / 3) / np.sqrt(3)) for a in (0.0, 0.5)]
    pb = [projectors(np.exp(-2j * np.pi * np.outer(j - b, j) / 3) / np.sqrt(3)) for b in (0.25, -0.25)]

    def prob(a, b, shift):
        """Operator of P(A_a = B_b + shift); settings 0, 1 are A1, A2 and B1, B2."""
        return sum(np.kron(pa[a][(l + shift) % 3], pb[b][l]) for l in range(3))

    return (prob(0, 0, 0) + prob(1, 0, -1) + prob(1, 1, 0) + prob(0, 1, 0)
            - prob(0, 0, -1) - prob(1, 0, 0) - prob(1, 1, -1) - prob(0, 1, 1))


def _max_entangled():
    psi = np.zeros(9, dtype=complex)
    psi[[0, 4, 8]] = 1 / np.sqrt(3)            # (|++> + |00> + |-->)/sqrt3
    return np.outer(psi, psi.conj())


def _top_eigenstate():
    vec = np.linalg.eigh(_plan_operator())[1][:, -1]
    return np.outer(vec, vec.conj())


def _product_maximum(n_starts=200, n_iter=100, seed=5):
    """max over product vectors of <a b|B|a b>, by alternating eigenvectors (independent of
    the optimiser): for fixed b the best a is the top eigenvector of <b|B|b>, and vice versa."""
    b4 = _plan_operator().reshape(3, 3, 3, 3)
    r = _rng(seed)
    vb = r.normal(size=(n_starts, 3)) + 1j * r.normal(size=(n_starts, 3))
    vb /= np.linalg.norm(vb, axis=1, keepdims=True)
    for _ in range(n_iter):
        va = np.linalg.eigh(np.einsum("ikjl,nk,nl->nij", b4, vb.conj(), vb))[1][:, :, -1]
        lam, vec = np.linalg.eigh(np.einsum("ikjl,ni,nj->nkl", b4, va.conj(), va))
        vb = vec[:, :, -1]
    return lam[:, -1].max()


def _herm_noise(r, eps):
    x = r.normal(size=(9, 9)) + 1j * r.normal(size=(9, 9))
    x = 0.5 * (x + x.conj().T)
    return eps * (x - np.trace(x) / 9 * np.eye(9))


@pytest.fixture(scope="module")
def sm_average():
    rho, _ = sm.OffShellSpectrum.from_config(config.constants()).average_density_matrix(n_u=400, n_y=200)
    return rho


# --------------------------------------------------------------------------
# The operator
# --------------------------------------------------------------------------
def test_operator_transcription_and_eq_2_40():
    b = bell.B_CGLMP
    assert np.allclose(b, _plan_operator(), atol=1e-15)
    assert np.allclose(b, b.conj().T) and abs(np.trace(b)) < 1e-14 and np.allclose(b.imag, 0.0)
    # same operator in spin form, l4 x l4 + l5 x l5 - (2/sqrt3)(Sx x Sx + Sy x Sy)
    spin = np.kron(T[3], T[3]) + np.kron(T[4], T[4]) - 2 / np.sqrt(3) * (
        np.kron(basis.SX, basis.SX) + np.kron(basis.SY, basis.SY))
    assert np.allclose(b, spin)
    # invariant under a common rotation about k and under W+ <-> W-
    jz = np.kron(basis.SZ, basis.ID3) + np.kron(basis.ID3, basis.SZ)
    assert np.allclose(b @ jz, jz @ b) and np.allclose(basis.SWAP @ b @ basis.SWAP, b)
    # Eq. (2.40) and Tr[rho B] for a stack of random states
    r = _rng(1)
    rho = np.array([basis.random_density_matrix(r, rank=k) for k in (1, 2, 3, 9, 9)])
    direct = np.real(np.einsum("nij,ji->n", rho, _plan_operator()))
    _, _, h = basis.coefficients(rho)
    assert np.allclose(bell.i3_from_coefficients(h), direct, atol=1e-13)
    assert np.allclose(bell.i3_unrotated(rho), direct, atol=1e-13)


def test_operator_spectrum():
    """Largest eigenvalue 1 + sqrt(11/3) = 2.9149: no state exceeds ~2.915 (PLAN.md Sec. 3.5).
    The spectrum is that of the CGLMP operator built from probabilities, and the top
    eigenvector has Schmidt coefficients ~ (1, 1, g), g = (sqrt11 - sqrt3)/2 (Acin et al. 2002)."""
    ev = np.linalg.eigvalsh(bell.B_CGLMP)
    assert ev[-1] == pytest.approx(1 + np.sqrt(11 / 3), abs=1e-12)
    assert ev[-1] == pytest.approx(2.9149, abs=5e-5) and ev[-1] < 2.915
    assert bell.I3_MAX == pytest.approx(ev[-1], abs=1e-12)
    assert np.allclose(ev, np.linalg.eigvalsh(_cglmp_operator()), atol=1e-12)
    top = np.linalg.eigh(bell.B_CGLMP)[1][:, -1]
    gamma = (np.sqrt(11) - np.sqrt(3)) / 2
    schmidt = np.linalg.svd(top.reshape(3, 3), compute_uv=False)
    assert np.allclose(schmidt, np.array([1, 1, gamma]) / np.sqrt(2 + gamma ** 2), atol=1e-12)


def test_operator_is_cglmp_up_to_local_unitaries():
    """rho_c = 1/9 + B_c/18 is a state (B_c >= -2).  For any O = (U x V)^dag B (U x V),
    Tr[B_c O] <= Tr[B_c^2] with equality only if O = B_c (Cauchy-Schwarz, equal spectra), so
    I3(rho_c) = Tr[B_c^2]/18 = 28/27 holds iff B is the CGLMP operator in a rotated local basis."""
    b_c = _cglmp_operator()
    rho_c = np.eye(9) / 9 + b_c / 18
    assert np.linalg.eigvalsh(rho_c)[0] > -1e-12
    assert np.trace(b_c @ b_c).real == pytest.approx(56 / 3)
    res = bell.i3_optimise(rho_c, full_output=True)
    assert res.value == pytest.approx(28 / 27, abs=1e-9)
    assert np.allclose(bell.bell_operator(res.u, res.v), b_c, atol=1e-6)


# --------------------------------------------------------------------------
# Optimised I3: reference states
# --------------------------------------------------------------------------
def test_maximally_entangled():
    """sum_i |ii>/sqrt3: unrotated 0, I3 = 4/(6 sqrt3 - 9) = 2.8729 after optimisation."""
    rho = _max_entangled()
    assert abs(bell.i3_unrotated(rho)) < 1e-15
    i3 = bell.i3_optimise(rho)
    assert i3 == pytest.approx(4 / (6 * np.sqrt(3) - 9), abs=1e-9)
    assert i3 == pytest.approx(2.8729, abs=5e-5) and bell.I3_MAX_ENTANGLED == pytest.approx(i3, abs=1e-9)
    assert bell.c2(rho) == pytest.approx(4 / 3)
    assert bell.entanglement_entropy(rho) == pytest.approx(np.log(3))
    # white noise: Tr B = 0, so I3(p rho + (1-p)/9) = p I3(rho)
    for p in (0.3, 0.7):
        assert bell.i3_optimise(p * rho + (1 - p) * np.eye(9) / 9) == pytest.approx(p * i3, abs=1e-9)
    # the SM state at threshold (kappa = 1) is maximally entangled, already optimal unrotated
    sm1 = sm.density_matrix(1.0)
    assert bell.i3_unrotated(sm1) == pytest.approx(i3, abs=1e-12)
    assert bell.i3_optimise(sm1) == pytest.approx(i3, abs=1e-9)


def test_optimised_states_never_exceed_bound():
    r = _rng(2)
    top = _top_eigenstate()
    # the bound is attained by the top eigenvector of B, also after a random local rotation
    assert bell.i3_optimise(_rotate(top, _local_unitary(r))) == pytest.approx(bell.I3_MAX, abs=1e-9)
    assert bell.i3_optimise(0.6 * top + 0.4 * np.eye(9) / 9) == pytest.approx(0.6 * bell.I3_MAX, abs=1e-9)
    states = [basis.random_density_matrix(r, rank=k) for k in (1, 1, 1, 1, 2, 3, 9)]
    states += [_rotate(0.97 * top + 0.03 * basis.random_density_matrix(r), _local_unitary(r))
               for _ in range(3)]
    for rho in states:
        i3 = bell.i3_optimise(rho)
        assert bell.i3_unrotated(rho) - 1e-12 <= i3 <= bell.I3_MAX + 1e-10
    assert i3 > 2.8        # the near-optimal states come close to the bound


def test_product_and_separable_states():
    """Product states and 1/9: I3 <= 2 and C2 = 0 (PLAN.md Sec. 3.5).  The maximum over product
    states, 1.4738, bounds every separable state (convexity); all pure products reach it."""
    ref = _product_maximum()
    assert 1.47 < ref < 1.48
    r = _rng(3)
    for _ in range(3):
        rho = basis.random_product_state(r, pure=True)
        assert bell.i3_optimise(rho, n_starts=128) == pytest.approx(ref, abs=1e-8)
        assert bell.c2(rho) < 1e-12 and max(bell.c2_terms(rho)) < 1e-12      # 0 up to rounding
    for _ in range(3):
        rho = basis.random_product_state(r, pure=False)
        assert bell.i3_optimise(rho, n_starts=128) <= ref + 1e-9
        assert bell.c2(rho) == 0.0
    assert abs(bell.i3_optimise(np.eye(9) / 9)) < 1e-14 and bell.c2(np.eye(9) / 9) == 0.0
    dec = sm.decohered(sm.density_matrix(sm.kappa(M_H, M_W, 30.0)))     # mixture of |m+ m-> products
    assert bell.i3_optimise(dec, n_starts=128) <= ref + 1e-9 and bell.c2(dec) == 0.0
    assert ref < bell.I3_LOCAL_BOUND


@pytest.mark.parametrize("mstar,i3,i3_label,c2,c2_label", [
    (4.0, 1.673, "1.67", 0.039, "0.039"), (12.0, 2.082, "2.08", 0.315, "0.31"),
    (20.0, 2.444, "2.44", 0.714, "0.71"), (40.0, 2.885, "2.89", 1.316, "1.3")])
def test_paper_figure_4(mstar, i3, i3_label, c2, c2_label):
    """I3 (left) and C2 (right) of Fig. 4 of 2302.00683 for the SM state at the labelled W*
    masses: the computed values round to the labels; the 3-digit values within rounding."""
    def half_unit(label):
        return 0.5 * 10.0 ** -len(label.split(".")[1]) + 1e-9
    kappa = sm.kappa(M_H, M_W, mstar)
    rho = sm.density_matrix(kappa)
    got_i3, got_c2 = bell.i3_optimise(rho), float(bell.c2(rho))
    assert got_i3 == pytest.approx(float(i3_label), abs=half_unit(i3_label))
    assert got_c2 == pytest.approx(float(c2_label), abs=half_unit(c2_label))
    assert got_i3 == pytest.approx(i3, abs=6e-4) and got_c2 == pytest.approx(c2, abs=6e-4)
    # pure state: C2 = 2(1 - Tr rho_A^2), rho_A = diag(1, kappa^2, 1)/(2 + kappa^2)
    assert got_c2 == pytest.approx(4 * (1 + 2 * kappa ** 2) / (2 + kappa ** 2) ** 2, abs=1e-12)


@pytest.mark.parametrize("mstar,label", [(4.0, "0.062"), (12.0, "0.35"), (20.0, "0.66"), (40.0, "1.1")])
def test_entanglement_entropy_sm(mstar, label):
    """Analytic entropy of |Psi_H> and the labels of Fig. 3 of 2302.00683."""
    kappa = sm.kappa(M_H, M_W, mstar)
    p = np.array([1.0, kappa ** 2, 1.0]) / (2 + kappa ** 2)
    got = bell.entanglement_entropy(sm.density_matrix(kappa))
    assert got == pytest.approx(-np.sum(p * np.log(p)), abs=1e-12)
    assert got == pytest.approx(float(label), abs=0.5 * 10.0 ** -len(label.split(".")[1]) + 1e-9)


def test_entanglement_entropy_general():
    r = _rng(4)
    assert abs(bell.entanglement_entropy(basis.random_product_state(r))) < 1e-12
    for _ in range(3):
        psi = r.normal(size=9) + 1j * r.normal(size=9)
        psi /= np.linalg.norm(psi)
        s2 = np.linalg.svd(psi.reshape(3, 3), compute_uv=False) ** 2          # Schmidt probabilities
        rho = np.outer(psi, psi.conj())
        assert bell.entanglement_entropy(rho) == pytest.approx(-np.sum(s2 * np.log(s2)), abs=1e-12)
    stack = np.array([_max_entangled(), basis.random_product_state(r)])
    assert np.allclose(bell.entanglement_entropy(stack), [np.log(3), 0.0], atol=1e-12)
    # entropy of the W+ (first factor): rho_a x |+1><+1| gives S(rho_a), |+1><+1| x rho_a gives 0
    rho_a = basis.random_density_matrix(r, 3)
    lam = np.linalg.eigvalsh(rho_a)
    s_a = -np.sum(lam * np.log(lam))
    pure = np.diag([1.0, 0.0, 0.0])
    assert s_a > 0.1 and bell.entanglement_entropy(np.kron(rho_a, pure)) == pytest.approx(s_a, abs=1e-12)
    assert abs(bell.entanglement_entropy(np.kron(pure, rho_a))) < 1e-12
    assert bell.entanglement_entropy(np.kron(np.eye(3) / 3, pure)) == pytest.approx(np.log(3), abs=1e-12)


# --------------------------------------------------------------------------
# Coefficient forms and invariance
# --------------------------------------------------------------------------
def _c2_terms_direct(rho):
    r4 = rho.reshape(3, 3, 3, 3)
    rho_a, rho_b = np.einsum("ikjk->ij", r4), np.einsum("kikj->ij", r4)
    p = np.trace(rho @ rho).real
    return p - np.trace(rho_a @ rho_a).real, p - np.trace(rho_b @ rho_b).real


def test_coefficient_forms():
    """Eqs. (2.39) and (2.40) agree with the trace forms, also for unphysical matrices."""
    r = _rng(6)
    states = [basis.random_density_matrix(r, rank=k) for k in (1, 1, 2, 3, 9, 9)]
    states += [basis.random_product_state(r, pure=False), sm.density_matrix(2.0)]
    states += [basis.random_density_matrix(r, rank=2) + _herm_noise(r, 0.05) for _ in range(3)]
    n_entangled = 0
    for rho in states:
        f, g, h = basis.coefficients(rho)
        t_a, t_b = _c2_terms_direct(rho)
        assert np.allclose(bell.c2_terms(rho), (t_a, t_b), atol=1e-14)
        assert bell.c2_from_coefficients(f, g, h) == pytest.approx(2 * max(0.0, t_a, t_b), abs=1e-13)
        assert bell.c2(rho) == pytest.approx(2 * max(0.0, t_a, t_b), abs=1e-14)
        trace_form = np.trace(rho @ _plan_operator()).real
        assert bell.i3_from_coefficients(h) == pytest.approx(trace_form, abs=1e-13)
        n_entangled += max(t_a, t_b) > 0
    assert 0 < n_entangled < len(states)          # both branches of the max are exercised
    stack = np.array(states)
    f, g, h = basis.coefficients(stack)
    assert np.allclose(bell.c2_from_coefficients(f, g, h), bell.c2(stack), atol=1e-13)


def test_local_unitary_invariance(sm_average):
    r = _rng(7)
    states = [basis.random_density_matrix(r, rank=1), basis.random_density_matrix(r, rank=3), sm_average,
              sm_average + _herm_noise(r, 0.02)]
    for rho in states:
        m = _local_unitary(r)
        rot = _rotate(rho, m)
        assert bell.i3_optimise(rot) == pytest.approx(bell.i3_optimise(rho), abs=1e-8)
        assert np.allclose(bell.c2_terms(rot), bell.c2_terms(rho), atol=1e-13)
        assert bell.c2(rot) == pytest.approx(bell.c2(rho), abs=1e-13)
        assert bell.entanglement_entropy(rot) == pytest.approx(bell.entanglement_entropy(rho), abs=1e-10)
        assert abs(bell.i3_unrotated(rot) - bell.i3_unrotated(rho)) > 1e-3     # not trivially invariant


# --------------------------------------------------------------------------
# Optimiser internals, warm starts and the scipy cross-check
# --------------------------------------------------------------------------
def test_gradients_against_finite_differences():
    r = _rng(8)
    rho = basis.random_density_matrix(r)
    u0, v0 = unitary_group.rvs(3, random_state=r), unitary_group.rvs(3, random_state=r)
    # Cayley-chart objective used with scipy
    for x in (np.zeros(16), 0.5 * r.normal(size=16)):
        f0, g0 = bell._chart_objective(x, rho, u0, v0)
        eps = 1e-6
        num = np.array([(bell._chart_objective(x + eps * e, rho, u0, v0)[0]
                         - bell._chart_objective(x - eps * e, rho, u0, v0)[0]) / (2 * eps)
                        for e in np.eye(16)])
        assert np.allclose(g0, num, atol=1e-8)
        gen = [np.einsum("a,aij->ij", x[s], T) for s in (slice(0, 8), slice(8, 16))]
        u, v = (np.linalg.solve(np.eye(3) - 0.5j * a, np.eye(3) + 0.5j * a) for a in gen)
        m = np.kron(u @ u0, v @ v0)
        assert -f0 == pytest.approx(np.trace(rho @ m.conj().T @ _plan_operator() @ m).real, abs=1e-13)

    # left-trivialised gradient and Hessian of the Newton iteration, against
    # F(exp(iX) U0, exp(iY) V0) with scipy's matrix exponential
    def f_exp(z):
        u = expm(1j * np.einsum("a,aij->ij", z[:8], T)) @ u0
        m = np.kron(u, expm(1j * np.einsum("a,aij->ij", z[8:], T)) @ v0)
        return np.trace(rho @ m.conj().T @ _plan_operator() @ m).real

    f, g, h = bell._value_grad_hess(rho.astype(complex), np.array([[u0, v0]]))
    assert f[0] == pytest.approx(f_exp(np.zeros(16)), abs=1e-13)
    e1, e2 = 1e-5, 1e-4
    grad = np.array([(f_exp(e1 * e) - f_exp(-e1 * e)) / (2 * e1) for e in np.eye(16)])
    hess = np.array([[(f_exp(e2 * (a + b)) - f_exp(e2 * (a - b)) - f_exp(e2 * (b - a))
                       + f_exp(-e2 * (a + b))) / (4 * e2 ** 2) for b in np.eye(16)] for a in np.eye(16)])
    assert np.allclose(g[0], grad, atol=1e-8)
    assert np.allclose(h[0], hess, atol=1e-6)


def test_newton_escapes_saddle_points(monkeypatch):
    """Newton steps also converge to saddle points.  With saddle detection disabled some starts
    stop at stationary points with positive curvature; the default iteration leaves them and,
    for a pure state (single maximum value), reaches the global maximum."""
    rho = sm.density_matrix(sm.kappa(M_H, M_W, 40.0)).astype(complex)
    w = np.array([[unitary_group.rvs(3, random_state=s), unitary_group.rvs(3, random_state=s + 1000)]
                  for s in range(64)])
    monkeypatch.setattr(bell, "SADDLE_TOL", np.inf)
    f, w_end, _, _ = bell._newton_batch(rho, w, bell.GTOL, 200)
    monkeypatch.undo()
    stuck = f < f.max() - 1e-6
    assert stuck.sum() >= 2
    _, g, h = bell._value_grad_hess(rho, w_end[stuck])
    assert np.abs(g).max() < 1e-8 and np.all(np.linalg.eigvalsh(h)[:, -1] > 0.1)
    f_esc, _, _, conv = bell._newton_batch(rho, w_end[stuck], bell.GTOL, 200)
    assert np.allclose(f_esc, f.max(), atol=1e-9) and conv.all()


def test_result_parameters_and_warm_start_forms(sm_average):
    res = bell.i3_optimise(sm_average, full_output=True)
    assert res.converged and res.gradient < 1e-8 and res.curvature < 1e-6
    assert res.n_starts == bell.N_STARTS + 1 and 1 <= res.n_best <= res.n_starts
    assert res.values[0] == res.value and np.all(np.diff(res.values) <= 0)
    assert bell.bell_expectation(sm_average, res.u, res.v) == pytest.approx(res.value, abs=1e-12)
    u, v = bell.unitaries(res.x)
    for got, want in ((u, res.u), (v, res.v)):                  # equal up to a global phase
        assert abs(abs(np.trace(got.conj().T @ want)) - 3) < 1e-10
    assert bell.bell_expectation(sm_average, u, v) == pytest.approx(res.value, abs=1e-10)
    for x0 in (res, (res.u, res.v), res.x, np.array([res.x, -res.x]), [res, res.x]):
        warm = bell.i3_optimise(sm_average, n_starts=0, x0=x0, full_output=True)
        assert warm.value == pytest.approx(res.value, abs=1e-10)
        assert warm.n_starts == len(bell._warm_starts(x0)) + 1
    with pytest.raises(ValueError):
        bell.i3_optimise(sm_average, x0=np.zeros(5))
    with pytest.raises(ValueError):
        bell.i3_optimise(np.eye(3))
    with pytest.raises(ValueError):
        bell.i3_optimise(sm_average, method="nonsense")


def test_settings_order_wplus_wminus():
    """The optimal u, v (and the parameters x) act on the W+ and the W- (first and second
    factor), as does a warm start (U, V).  Checked on a state without W+ <-> W- symmetry, for
    which the swapped settings give a much smaller value."""
    r = _rng(13)
    rho = basis.random_density_matrix(r, rank=3)
    res = bell.i3_optimise(rho, full_output=True)

    def direct(u, v):
        m = np.kron(u, v)
        return np.trace(rho @ m.conj().T @ _plan_operator() @ m).real

    assert direct(res.u, res.v) == pytest.approx(res.value, abs=1e-12)
    weights = bell.i3_weights(res.u, res.v)
    assert weights @ basis.coefficient_vector(rho) == pytest.approx(res.value, abs=1e-12)
    assert direct(res.v, res.u) < res.value - 0.1
    assert direct(*bell.unitaries(res.x)) == pytest.approx(res.value, abs=1e-10)
    for x0 in (res, (res.u, res.v), res.x):
        (u, v), = bell._warm_starts(x0)
        assert direct(u, v) == pytest.approx(res.value, abs=1e-10)
    assert bell.i3_optimise(rho, n_starts=0, x0=(res.u, res.v)) == pytest.approx(res.value, abs=1e-10)


def test_warm_start_nearest_unitary():
    """A warm start (U, V) is replaced by its nearest unitaries (polar factors), so rescaled,
    rounded or averaged settings cannot inflate I3: the optimiser only multiplies a start by
    unitaries, and (2U, V) would otherwise give 4 I3.  Non-finite warm starts are rejected."""
    rho = sm.density_matrix(sm.kappa(M_H, M_W, 30.0))          # pure: every start reaches the maximum
    res = bell.i3_optimise(rho, full_output=True)
    r = _rng(14)
    noise = 0.05 * (r.normal(size=(3, 3)) + 1j * r.normal(size=(3, 3)))
    for x0 in ((2.0 * res.u, res.v), (1.01 * res.u, 0.5 * res.v), (res.u + noise, res.v)):
        (u, v), = bell._warm_starts(x0)
        for m in (u, v):
            assert np.abs(m.conj().T @ m - np.eye(3)).max() < 1e-13
        assert bell.i3_optimise(rho, n_starts=0, x0=x0) == pytest.approx(res.value, abs=1e-10)
    (u, v), = bell._warm_starts((2.0 * res.u, res.v))          # polar factor of a rescaled unitary
    assert np.abs(u - res.u).max() < 1e-13 and np.abs(v - res.v).max() < 1e-13
    assert bell.observables(rho, x0=(1.1 * res.u, res.v))["i3"] == pytest.approx(res.value, abs=1e-10)
    bad = res.u.copy()
    bad[0, 0] = np.nan
    for x0 in ((bad, res.v), np.r_[np.inf, res.x[1:]]):
        with pytest.raises(ValueError, match="finite"):       # not numpy's LinAlgError (a ValueError)
            bell.i3_optimise(rho, x0=x0)


def test_warm_start_timing(sm_average):
    """Pseudo-experiment use: warm-started calls on perturbed states (unphysical, like moment
    estimates) take < 50 ms (median CPU time of this process, insensitive to other load on the
    machine; single-threaded) and agree with a thorough cold optimisation."""
    ref = bell.i3_optimise(sm_average, full_output=True)
    r = _rng(9)
    states = [sm_average + _herm_noise(r, 0.01) for _ in range(8)]
    bell.i3_optimise(states[0], x0=ref)              # warm-up
    times, values = [], []
    for rho in states:
        t0 = time.process_time()
        values.append(bell.i3_optimise(rho, x0=ref))
        times.append(time.process_time() - t0)
    assert np.median(times) < 0.05
    for rho, val in zip(states[:2], values[:2]):
        assert val == pytest.approx(bell.i3_optimise(rho, n_starts=256, rng=1), abs=1e-8)


def test_newton_and_scipy_agree():
    r = _rng(10)
    for _ in range(2):
        rho = basis.random_density_matrix(r, rank=3)
        newton = bell.i3_optimise(rho, full_output=True)
        scipy_ = bell.i3_optimise(rho, n_starts=24, method="scipy", full_output=True)
        assert scipy_.value == pytest.approx(newton.value, abs=1e-8)
        assert scipy_.converged and newton.converged


# --------------------------------------------------------------------------
# Fixed settings and raw / physical results
# --------------------------------------------------------------------------
def test_bell_expectation_and_weights():
    """Tr[rho (U x V)^dag B (U x V)] directly, from the 80 weights, and as the exact mean of the
    per-event estimator x . w over the decay distribution (quadrature)."""
    r = _rng(11)
    rho = basis.random_density_matrix(r)
    u, v = unitary_group.rvs(3, random_state=r), unitary_group.rvs(3, random_state=r)
    m = np.kron(u, v)
    direct = np.trace(rho @ m.conj().T @ _plan_operator() @ m).real
    assert bell.bell_expectation(rho, u, v) == pytest.approx(direct, abs=1e-13)
    w = bell.i3_weights(u, v)
    assert w @ basis.coefficient_vector(rho) == pytest.approx(direct, abs=1e-13)
    beta = np.zeros((8, 8))                     # Eq. (2.40): weights 4, 4 and -4/sqrt3 on the h_ab
    beta[3, 3] = beta[4, 4] = 1.0
    for pair in ((0, 5), (1, 6)):
        beta[np.ix_(pair, pair)] = -1 / np.sqrt(3)
    assert np.allclose(bell.i3_weights(), basis.pack(np.zeros(8), np.zeros(8), 4 * beta))
    th, ph, wq = basis.sphere_quadrature(8, 16)
    t_p, t_m = np.repeat(th, th.size), np.tile(th, th.size)
    f_p, f_m = np.repeat(ph, ph.size), np.tile(ph, ph.size)
    prob = (3 / (4 * np.pi)) ** 2 * np.outer(wq, wq).ravel() * basis.trace_projectors(
        rho, t_p, f_p, t_m, f_m)
    assert prob @ (basis.estimator_vector(t_p, f_p, t_m, f_m) @ w) == pytest.approx(direct, abs=1e-12)


def test_observables_raw_and_physical(sm_average):
    phys = sm.density_matrix(sm.kappa(M_H, M_W, 40.0))
    out = bell.observables(phys)
    assert out["i3"] == pytest.approx(out["i3_physical"], abs=1e-9)
    assert out["c2"] == pytest.approx(out["c2_physical"], abs=1e-12) and out["min_eigenvalue"] > -1e-12
    r = _rng(12)
    raw = sm_average + _herm_noise(r, 0.03)
    out = bell.observables(raw)
    proj = basis.nearest_physical(raw)
    assert out["min_eigenvalue"] < 0
    assert out["i3_physical"] == pytest.approx(bell.i3_optimise(proj), abs=1e-8)
    assert out["i3_physical"] <= bell.I3_MAX + 1e-10
    assert out["c2"] == pytest.approx(bell.c2(raw)) and out["c2_physical"] == pytest.approx(bell.c2(proj))
