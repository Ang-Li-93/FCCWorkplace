"""Basis, coefficient and analyser conventions (PLAN.md Sec. 3.1, 3.3)."""
import numpy as np
import pytest
from scipy.linalg import expm

from qtomo import basis

T = basis.GELL_MANN


def _rng(seed=12345):
    return np.random.default_rng(seed)


def _angles(n=200, seed=1):
    r = _rng(seed)
    theta = np.concatenate([np.arccos(r.uniform(-1, 1, n)), [0.0, np.pi, np.pi / 2, 1e-9]])
    phi = np.concatenate([r.uniform(0, 2 * np.pi, n), [0.0, 1.0, 2 * np.pi - 1e-9, 3.0]])
    return theta, phi


def _coherent(theta, phi, m):
    """|m_n> = exp(-i phi S_z) exp(-i theta S_y) |m>, built independently with expm."""
    e = np.zeros(3, dtype=complex)
    e[{+1: 0, 0: 1, -1: 2}[m]] = 1.0
    return expm(-1j * phi * basis.SZ) @ expm(-1j * theta * basis.SY) @ e


# --------------------------------------------------------------------------
def test_gell_mann_algebra():
    for a in range(8):
        assert np.allclose(T[a], T[a].conj().T)
        assert abs(np.trace(T[a])) < 1e-14
        for b in range(8):
            assert np.isclose(np.trace(T[a] @ T[b]), 2.0 * (a == b))


def test_spin_matrices_match_paper_A1():
    sx = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]]) / np.sqrt(2)
    sy = np.array([[0, -1j, 0], [1j, 0, -1j], [0, 1j, 0]]) / np.sqrt(2)
    sz = np.diag([1.0, 0.0, -1.0])
    assert np.allclose(basis.SX, sx) and np.allclose(basis.SY, sy) and np.allclose(basis.SZ, sz)
    assert np.allclose(basis.SX @ basis.SY - basis.SY @ basis.SX, 1j * basis.SZ)
    s2 = basis.SX @ basis.SX + basis.SY @ basis.SY + basis.SZ @ basis.SZ
    assert np.allclose(s2, 2 * np.eye(3))


def test_operator_basis_orthogonality():
    gram = np.real(np.einsum("kij,lji->kl", basis.OPERATORS, basis.OPERATORS))
    assert np.allclose(gram, np.diag(basis.NORMS))
    assert len(basis.COEFF_LABELS) == basis.N_COEFF == 80


def test_coefficient_definitions_and_round_trip():
    r = _rng()
    for _ in range(20):
        rho = basis.random_density_matrix(r)
        f, g, h = basis.coefficients(rho)
        for a in range(8):
            assert np.isclose(f[a], np.trace(rho @ np.kron(T[a], basis.ID3)).real / 6)
            assert np.isclose(g[a], np.trace(rho @ np.kron(basis.ID3, T[a])).real / 6)
            for b in range(8):
                assert np.isclose(h[a, b], np.trace(rho @ np.kron(T[a], T[b])).real / 4)
        assert np.allclose(basis.density_matrix(f, g, h), rho, atol=1e-13)
        assert np.allclose(basis.unpack(basis.pack(f, g, h))[2], h)
    assert np.allclose(basis.coefficient_vector(basis.ID9 / 9), 0.0)
    stack = np.array([basis.random_density_matrix(r) for _ in range(3)])
    assert np.allclose(basis.density_matrix(*basis.coefficients(stack)), stack, atol=1e-13)


def test_reduced_density_matrices_and_swap():
    r = _rng(3)
    a, b = basis.random_density_matrix(r, 3), basis.random_density_matrix(r, 3)
    rho = np.kron(a, b)
    assert np.allclose(basis.reduced_wplus(rho), a) and np.allclose(basis.reduced_wminus(rho), b)
    rho = basis.random_density_matrix(r)
    f, g, _ = basis.coefficients(rho)
    assert np.allclose(basis.reduced_wplus(rho), basis.ID3 / 3 + 3 * np.einsum("a,aij->ij", f, T))
    assert np.allclose(basis.reduced_wminus(rho), basis.ID3 / 3 + 3 * np.einsum("a,aij->ij", g, T))
    assert np.allclose(basis.SWAP @ np.kron(a, b) @ basis.SWAP, np.kron(b, a))
    f2, g2, h2 = basis.coefficients(basis.SWAP @ rho @ basis.SWAP)
    _, _, h = basis.coefficients(rho)
    assert np.allclose(f2, g) and np.allclose(g2, f) and np.allclose(h2, h.T)


# --------------------------------------------------------------------------
# Analysers
# --------------------------------------------------------------------------
@pytest.mark.parametrize("sign", [1, -1])
def test_q_is_trace_of_coherent_state_projector(sign):
    """Eq. (B.1) q^a = Tr[|m_n><m_n| T^a] with m = +1 for the W+, -1 for the W-."""
    theta, phi = _angles(60)
    q = basis.q_functions(theta, phi, sign)
    proj = basis.projector(theta, phi, sign)
    for i, (th, ph) in enumerate(zip(theta, phi)):
        v = _coherent(th, ph, sign)
        pi = np.outer(v, v.conj())
        assert np.allclose(q[i], [np.trace(pi @ T[a]).real for a in range(8)], atol=1e-13)
        assert np.allclose(proj[i], pi, atol=1e-13)


@pytest.mark.parametrize("sign", [1, -1])
def test_projector_is_rank1_projector(sign):
    theta, phi = _angles()
    p = basis.projector(theta, phi, sign)
    assert np.allclose(p, np.swapaxes(p.conj(), -1, -2), atol=1e-14)
    assert np.allclose(np.trace(p, axis1=-2, axis2=-1), 1.0)
    assert np.allclose(p @ p, p, atol=1e-13)
    assert np.allclose(np.linalg.eigvalsh(p), [0.0, 0.0, 1.0], atol=1e-12)


def test_analyser_polarisation_along_z():
    """Pi_+(theta=0) = |+1><+1| (l+ along the W+ spin), Pi_-(theta=0) = |-1><-1|."""
    assert np.allclose(basis.projector(0.0, 0.0, +1), np.diag([1, 0, 0]))
    assert np.allclose(basis.projector(0.0, 0.0, -1), np.diag([0, 0, 1]))


def test_plan_literal_projector_is_not_a_projector():
    """PLAN.md Sec. 3.3 and 2302.00683 Eq. (2.43) write Pi = 1/3 + sum q^a T^a; with the
    Eq. (B.1) functions that matrix has eigenvalues (5/3, -1/3, -1/3).  The factor 1/2 in
    basis.projector is the fix."""
    for sign in (1, -1):
        q = basis.q_functions(0.7, 1.9, sign)
        literal = basis.ID3 / 3 + np.einsum("a,aij->ij", q, T)
        assert np.allclose(np.linalg.eigvalsh(literal), [-1 / 3, -1 / 3, 5 / 3])


def test_sphere_quadrature():
    th, ph, w = basis.sphere_quadrature(10, 20)
    assert np.isclose(w.sum(), 4 * np.pi)
    assert np.isclose(np.sum(w * np.cos(th) ** 2), 4 * np.pi / 3)
    assert abs(np.sum(w * np.sin(th) * np.cos(ph))) < 1e-13


@pytest.mark.parametrize("sign", [1, -1])
def test_pq_duality(sign):
    """(3/4pi) int p^n q^m dOmega = 2 delta_nm.  PLAN.md Sec. 3.3 and Eq. (2.45) of the paper
    quote delta_nm; the B.1/B.2 functions satisfy the paper's Eqs. (2.44) and (2.46),
    p = m^-1 q with m = (3/8pi) int q q, which implies the factor 2."""
    th, ph, w = basis.sphere_quadrature(24, 48)
    q = basis.q_functions(th, ph, sign)
    p = basis.p_functions(th, ph, sign)
    dual = 3 / (4 * np.pi) * np.einsum("ia,ib,i->ab", p, q, w)
    assert np.allclose(dual, 2 * np.eye(8), atol=1e-12)
    m = 3 / (8 * np.pi) * np.einsum("ia,ib,i->ab", q, q, w)
    assert np.allclose(np.linalg.solve(m, q.T).T, p, atol=1e-11)


@pytest.mark.parametrize("sign", [1, -1])
def test_completeness_and_zero_means(sign):
    th, ph, w = basis.sphere_quadrature(12, 24)
    proj = basis.projector(th, ph, sign)
    assert np.allclose(3 / (4 * np.pi) * np.einsum("i,ijk->jk", w, proj), basis.ID3, atol=1e-13)
    assert np.allclose(w @ basis.q_functions(th, ph, sign), 0.0, atol=1e-12)
    assert np.allclose(w @ basis.p_functions(th, ph, sign), 0.0, atol=1e-12)


def test_moment_estimators_exact():
    """For the exact distribution (3/4pi)^2 Tr[rho Pi+ x Pi-]:
    <p+^a> = 6 f_a, <p-^a> = 6 g_a, <p+^a p-^b> = 4 h_ab (quadrature is exact here)."""
    th, ph, w = basis.sphere_quadrature(8, 16)
    proj_p, proj_m = basis.projector(th, ph, +1), basis.projector(th, ph, -1)
    pp, pm = basis.p_functions(th, ph, +1), basis.p_functions(th, ph, -1)
    r = _rng(7)
    for _ in range(5):
        rho = basis.random_density_matrix(r)
        r4 = rho.reshape(3, 3, 3, 3)
        dens = np.real(np.einsum("ikjl,xji,ylk->xy", r4, proj_p, proj_m))
        prob = (3 / (4 * np.pi)) ** 2 * np.outer(w, w) * dens
        assert np.isclose(prob.sum(), 1.0)
        f, g, h = basis.coefficients(rho)
        assert np.allclose(np.einsum("xy,xa->a", prob, pp), 6 * f, atol=1e-12)
        assert np.allclose(np.einsum("xy,ya->a", prob, pm), 6 * g, atol=1e-12)
        assert np.allclose(np.einsum("xy,xa,yb->ab", prob, pp, pm), 4 * h, atol=1e-12)


def test_trace_projectors_and_estimator_vector():
    """trace_projectors equals the direct trace; estimator_vector is unbiased (exact)."""
    r = _rng(17)
    theta_p, phi_p = _angles(40, seed=2)
    theta_m, phi_m = _angles(40, seed=3)
    rho = basis.random_density_matrix(r)
    direct = np.real(np.einsum("ij,nji->n", rho, np.einsum(
        "nab,ncd->nacbd", basis.projector(theta_p, phi_p, +1),
        basis.projector(theta_m, phi_m, -1)).reshape(-1, 9, 9)))
    assert np.allclose(basis.trace_projectors(rho, theta_p, phi_p, theta_m, phi_m), direct)
    th, ph, w = basis.sphere_quadrature(8, 16)
    t_p, t_m = np.repeat(th, th.size), np.tile(th, th.size)
    f_p, f_m = np.repeat(ph, ph.size), np.tile(ph, ph.size)
    prob = (3 / (4 * np.pi)) ** 2 * np.outer(w, w).ravel() * basis.trace_projectors(rho, t_p, f_p, t_m, f_m)
    x = basis.estimator_vector(t_p, f_p, t_m, f_m)
    assert np.allclose(prob @ x, basis.coefficient_vector(rho), atol=1e-12)


@pytest.mark.parametrize("w_p,w_m", [(0.2, 0.0), (0.0, 0.3), (0.1, 0.35)])
def test_estimator_vector_mistag_unbiased(w_p, w_m):
    """Averaging the corrected estimators over independent analyser flips with
    probabilities w_p, w_m gives back the unflipped estimators, event by event."""
    theta_p, phi_p = _angles(30, seed=4)
    theta_m, phi_m = _angles(30, seed=5)
    flipped_p, flipped_m = basis.antipode(theta_p, phi_p), basis.antipode(theta_m, phi_m)
    avg = 0.0
    for fp, prob_p in ((False, 1 - w_p), (True, w_p)):
        for fm, prob_m in ((False, 1 - w_m), (True, w_m)):
            tp, pp_ = flipped_p if fp else (theta_p, phi_p)
            tm, pm_ = flipped_m if fm else (theta_m, phi_m)
            avg = avg + prob_p * prob_m * basis.estimator_vector(tp, pp_, tm, pm_, w_p, w_m)
    assert np.allclose(avg, basis.estimator_vector(theta_p, phi_p, theta_m, phi_m), atol=1e-12)
    per_event = np.full(theta_p.shape, w_p)
    assert np.allclose(basis.estimator_vector(theta_p, phi_p, theta_m, phi_m, per_event, w_m),
                       basis.estimator_vector(theta_p, phi_p, theta_m, phi_m, w_p, w_m))


# --------------------------------------------------------------------------
# Vector / tensor polarisation and analyser flips
# --------------------------------------------------------------------------
@pytest.mark.parametrize("sign", [1, -1])
def test_flip_relations(sign):
    theta, phi = _angles()
    tha, pha = basis.antipode(theta, phi)
    for fun in (basis.q_functions, basis.p_functions):
        assert np.allclose(fun(tha, pha, sign), fun(theta, phi, sign) @ basis.FLIP.T, atol=1e-12)
    # flipping the W+ analyser gives the W- functions and vice versa
    assert np.allclose(basis.q_functions(tha, pha, sign), basis.q_functions(theta, phi, -sign), atol=1e-12)
    assert np.allclose(basis.p_functions(tha, pha, sign), basis.p_functions(theta, phi, -sign), atol=1e-12)


def test_rank_projectors():
    r1, r2 = basis.RANK1, basis.RANK2
    assert np.allclose(r1 @ r1, r1) and np.allclose(r1, r1.T) and np.isclose(np.trace(r1), 3)
    assert np.isclose(np.trace(r2), 5) and np.allclose(r1 @ r2, 0)
    for s in (basis.SX, basis.SY, basis.SZ):
        v = np.array([np.trace(s @ T[a]).real for a in range(8)]) / 2
        assert np.allclose(r1 @ v, v)
    quad = basis.SZ @ basis.SZ - 2 / 3 * basis.ID3
    v = np.array([np.trace(quad @ T[a]).real for a in range(8)]) / 2
    assert np.allclose(r2 @ v, v)
    for w in (0.0, 0.1, 0.3, 0.7):
        assert np.allclose(basis.mistag_dilution(w) @ basis.mistag_correction(w), np.eye(8))
    with pytest.raises(ValueError):
        basis.mistag_correction(0.5)


@pytest.mark.parametrize("w", [0.0, 0.2, 0.5])
def test_mistag_dilution_is_flip_average(w):
    theta, phi = _angles(50)
    tha, pha = basis.antipode(theta, phi)
    for sign in (1, -1):
        avg = (1 - w) * basis.p_functions(theta, phi, sign) + w * basis.p_functions(tha, pha, sign)
        assert np.allclose(avg, basis.p_functions(theta, phi, sign) @ basis.mistag_dilution(w).T)


# --------------------------------------------------------------------------
# Subspaces of the coefficient space
# --------------------------------------------------------------------------
def _in_span(v, b):
    return np.allclose(b @ (b.T @ v), v, atol=1e-12)


def test_subspace_dimensions():
    for name, k in (("full", 80), ("rotation_invariant", 18), ("rotation_invariant_real", 13)):
        b = basis.subspace(name)
        assert b.shape == (80, k)
        assert np.allclose(b.T @ b, np.eye(k), atol=1e-12)
    with pytest.raises(ValueError):
        basis.subspace("nonsense")


def test_subspace_membership():
    r = _rng(11)
    rot, real = basis.subspace("rotation_invariant"), basis.subspace("rotation_invariant_real")
    jz = np.kron(basis.SZ, basis.ID3) + np.kron(basis.ID3, basis.SZ)
    for _ in range(10):
        amp = r.normal(size=3) + 1j * r.normal(size=3)
        psi = np.zeros(9, dtype=complex)
        psi[[2, 4, 6]] = amp / np.linalg.norm(amp)
        v = basis.coefficient_vector(np.outer(psi, psi.conj()))
        assert _in_span(v, rot) and not _in_span(v, real)
        psi = np.abs(psi)
        assert _in_span(basis.coefficient_vector(np.outer(psi, psi)), real)
        # a rotation-invariant state is unchanged by a common rotation about k
        rho = basis.density_matrix_from_vector(rot @ (rot.T @ basis.coefficient_vector(
            basis.random_density_matrix(r))))
        u = expm(-1j * 0.83 * jz)
        assert np.allclose(u @ rho @ u.conj().T, rho)
    assert not _in_span(basis.coefficient_vector(basis.random_density_matrix(r)), rot)


# --------------------------------------------------------------------------
# Nearest physical state
# --------------------------------------------------------------------------
def _simplex_projection(v):
    """Euclidean projection on the probability simplex (Duchi et al., ICML 2008)."""
    u = np.sort(v)[::-1]
    css = np.cumsum(u)
    k = np.arange(1, len(v) + 1)
    idx = np.nonzero(u - (css - 1) / k > 0)[0][-1]
    return np.maximum(v - (css[idx] - 1) / (idx + 1), 0.0)


def test_nearest_physical():
    r = _rng(5)
    rho = basis.random_density_matrix(r)
    assert np.allclose(basis.nearest_physical(rho), rho, atol=1e-13)
    for _ in range(20):
        x = r.normal(size=(9, 9)) + 1j * r.normal(size=(9, 9))
        x = 0.5 * (x + x.conj().T)
        x -= np.trace(x) / 9 * np.eye(9)
        sigma = basis.random_density_matrix(r) + 0.15 * x
        assert basis.min_eigenvalue(sigma) < 0
        proj = basis.nearest_physical(sigma)
        ev = np.linalg.eigvalsh(proj)
        assert ev.min() > -1e-12 and np.isclose(np.trace(proj).real, 1.0)
        assert np.allclose(np.sort(ev), np.sort(_simplex_projection(np.linalg.eigvalsh(sigma))), atol=1e-12)
        dist = np.linalg.norm(sigma - proj)
        for _ in range(30):
            other = basis.random_density_matrix(r, rank=int(r.integers(1, 10)))
            assert np.linalg.norm(sigma - other) >= dist - 1e-12
