"""Gell-Mann basis for two spin-1 particles and the spin-1 decay analysers.

Conventions (CONVENTIONS.md; PLAN.md Sec. 3.1 and 3.3), pinned down by
tests/test_basis.py:

* single-W states are ordered (+1, 0, -1); in two-W operators the first tensor
  factor is the W+ and the second the W-, so |m+ m-> has the flat index
  3 i(m+) + i(m-) with i(+1) = 0, i(0) = 1, i(-1) = 2;
* ``GELL_MANN[a-1]`` is the standard Gell-Mann matrix T^a,
  Tr[T^a T^b] = 2 delta_ab (2302.00683 Eq. A.4);
* rho = 1/9 + f_a T^a x 1 + g_a 1 x T^a + h_ab T^a x T^b, with
  f_a = Tr[rho T^a x 1]/6, g_a = Tr[rho 1 x T^a]/6, h_ab = Tr[rho T^a x T^b]/4;
* ``q_functions`` and ``p_functions`` are Eqs. (B.1) and (B.2) of 2302.00683,
  transcribed verbatim.  q^a = Tr[Pi T^a] for the rank-1 projectors
  Pi_+ = |+1_n><+1_n| (analyser of the W+: l+, or the down-type antiquark) and
  Pi_- = |-1_n><-1_n| (analyser of the W-: l-, or the down-type quark), where
  |m_n> = exp(-i phi S_z) exp(-i theta S_y) |m>.  Consequently

      Pi = 1/3 + (1/2) sum_a q^a T^a,
      (3/4pi) int p^n q^m dOmega = 2 delta_nm,
      <p+^a> = 6 f_a,   <p-^a> = 6 g_a,   <p+^a p-^b> = 4 h_ab.

  PLAN.md Sec. 3.3 and the paper's Eqs. (2.43), (2.45), (2.47)-(2.48) state these
  relations without the factors 1/2, 2, 6 and 4.  The explicit functions of
  Appendix B are the correct ones; the paper's own Eqs. (2.24) and (2.46) agree
  with the factors above.
"""
import numpy as np

SQRT2 = np.sqrt(2.0)
SQRT3 = np.sqrt(3.0)
SPIN_LABELS = (+1, 0, -1)


def _gell_mann():
    t = np.zeros((8, 3, 3), dtype=complex)
    t[0][0, 1] = t[0][1, 0] = 1.0
    t[1][0, 1], t[1][1, 0] = -1j, 1j
    t[2][0, 0], t[2][1, 1] = 1.0, -1.0
    t[3][0, 2] = t[3][2, 0] = 1.0
    t[4][0, 2], t[4][2, 0] = -1j, 1j
    t[5][1, 2] = t[5][2, 1] = 1.0
    t[6][1, 2], t[6][2, 1] = -1j, 1j
    t[7] = np.diag([1.0, 1.0, -2.0]) / SQRT3
    return t


GELL_MANN = _gell_mann()
ID3 = np.eye(3, dtype=complex)
ID9 = np.eye(9, dtype=complex)

# Spin-1 matrices in this basis (2302.00683 Eqs. A.1-A.2).
SX = (GELL_MANN[0] + GELL_MANN[5]) / SQRT2
SY = (GELL_MANN[1] + GELL_MANN[6]) / SQRT2
SZ = 0.5 * GELL_MANN[2] + 0.5 * SQRT3 * GELL_MANN[7]

# Two-qutrit operators in coefficient order [f_1..f_8, g_1..g_8, h_11, h_12, ..., h_88]:
# rho = 1/9 + sum_k c_k OPERATORS[k], c_k = Tr[rho OPERATORS[k]] / NORMS[k],
# Tr[OPERATORS[k] OPERATORS[l]] = NORMS[k] delta_kl.
OPERATORS = np.array([np.kron(t, ID3) for t in GELL_MANN]
                     + [np.kron(ID3, t) for t in GELL_MANN]
                     + [np.kron(ta, tb) for ta in GELL_MANN for tb in GELL_MANN])
NORMS = np.array([6.0] * 16 + [4.0] * 64)
N_COEFF = 80
COEFF_LABELS = tuple([f"f{a}" for a in range(1, 9)]
                     + [f"g{a}" for a in range(1, 9)]
                     + [f"h{a}{b}" for a in range(1, 9) for b in range(1, 9)])

# Exchange of the W+ and W- factors.
SWAP = np.zeros((9, 9))
for _i in range(3):
    for _j in range(3):
        SWAP[3 * _j + _i, 3 * _i + _j] = 1.0


# --------------------------------------------------------------------------
# rho <-> coefficients
# --------------------------------------------------------------------------
def pack(f, g, h):
    """Coefficient vector (..., 80) from f (..., 8), g (..., 8), h (..., 8, 8)."""
    f, g, h = (np.asarray(x, dtype=float) for x in (f, g, h))
    return np.concatenate([f, g, h.reshape(h.shape[:-2] + (64,))], axis=-1)


def unpack(c):
    """Inverse of ``pack``."""
    c = np.asarray(c, dtype=float)
    return c[..., :8], c[..., 8:16], c[..., 16:].reshape(c.shape[:-1] + (8, 8))


def coefficient_vector(rho):
    """Coefficient vector (..., 80) of a density matrix (or stack of them)."""
    rho = np.asarray(rho)
    return np.real(np.einsum("kij,...ji->...k", OPERATORS, rho)) / NORMS


def coefficients(rho):
    """(f, g, h) of a density matrix (or stack of them)."""
    return unpack(coefficient_vector(rho))


def density_matrix_from_vector(c):
    c = np.asarray(c, dtype=float)
    return ID9 / 9 + np.einsum("...k,kij->...ij", c, OPERATORS)


def density_matrix(f, g, h):
    """rho = 1/9 + f_a T^a x 1 + g_a 1 x T^a + h_ab T^a x T^b."""
    return density_matrix_from_vector(pack(f, g, h))


def reduced_wplus(rho):
    """Reduced density matrix of the W+ (trace over the W-)."""
    rho = np.asarray(rho)
    return np.einsum("...ikjk->...ij", rho.reshape(rho.shape[:-2] + (3, 3, 3, 3)))


def reduced_wminus(rho):
    """Reduced density matrix of the W- (trace over the W+)."""
    rho = np.asarray(rho)
    return np.einsum("...kikj->...ij", rho.reshape(rho.shape[:-2] + (3, 3, 3, 3)))


def purity(rho):
    rho = np.asarray(rho)
    return np.real(np.einsum("...ij,...ji->...", rho, rho))


def min_eigenvalue(rho):
    rho = np.asarray(rho)
    return np.linalg.eigvalsh(0.5 * (rho + np.swapaxes(rho.conj(), -1, -2)))[..., 0]


def nearest_physical(rho):
    """Closest density matrix to a Hermitian, unit-trace matrix in Frobenius norm.

    Algorithm of Smolin, Gambetta and Smith, PRL 108 (2012) 070502: the
    eigenvalues are projected onto the probability simplex, the eigenvectors kept.
    A physical input is returned unchanged.
    """
    rho = np.asarray(rho, dtype=complex)
    rho = 0.5 * (rho + rho.conj().T)
    mu, vecs = np.linalg.eigh(rho)
    mu, vecs = mu[::-1], vecs[:, ::-1]          # decreasing order
    lam = mu.copy()
    acc = 0.0
    i = len(mu)
    while i > 0 and mu[i - 1] + acc / i < 0.0:
        acc += mu[i - 1]
        lam[i - 1] = 0.0
        i -= 1
    lam[:i] = mu[:i] + acc / i
    return (vecs * lam) @ vecs.conj().T


# --------------------------------------------------------------------------
# Random states (tests, toys)
# --------------------------------------------------------------------------
def random_density_matrix(rng, dim=9, rank=None):
    """Random density matrix from the Ginibre ensemble (rank ``rank``, default full)."""
    rank = dim if rank is None else rank
    g = rng.normal(size=(dim, rank)) + 1j * rng.normal(size=(dim, rank))
    rho = g @ g.conj().T
    return rho / np.trace(rho).real


def random_product_state(rng, pure=True):
    rank = 1 if pure else None
    return np.kron(random_density_matrix(rng, 3, rank), random_density_matrix(rng, 3, rank))


# --------------------------------------------------------------------------
# Decay analysers: Wigner Q and P symbols (2302.00683 App. B)
# --------------------------------------------------------------------------
def _check_sign(sign):
    if sign not in (1, -1):
        raise ValueError("sign must be +1 (W+ analyser) or -1 (W- analyser)")


def _trig(theta, phi):
    theta = np.asarray(theta, dtype=float)
    phi = np.asarray(phi, dtype=float)
    return np.broadcast_arrays(np.cos(theta), np.sin(theta), np.cos(2 * theta),
                               np.cos(phi), np.sin(phi), np.cos(2 * phi), np.sin(2 * phi))


def q_functions(theta, phi, sign):
    """Wigner Q symbols q^a_{+/-}(theta, phi), Eq. (B.1) of 2302.00683 verbatim.

    Returns an array of shape ``broadcast(theta, phi).shape + (8,)``.
    q^a = Tr[Pi T^a] (see the module docstring for the normalisation).
    """
    _check_sign(sign)
    c, s, c2t, cp, sp, c2p, s2p = _trig(theta, phi)
    out = np.empty(c.shape + (8,))
    out[..., 0] = s * (c + sign) * cp / SQRT2
    out[..., 1] = s * (c + sign) * sp / SQRT2
    out[..., 2] = (1 + sign * 4 * c + 3 * c2t) / 8
    out[..., 3] = 0.5 * s * s * c2p
    out[..., 4] = 0.5 * s * s * s2p
    out[..., 5] = s * (-c + sign) * cp / SQRT2
    out[..., 6] = s * (-c + sign) * sp / SQRT2
    out[..., 7] = (-1 + sign * 12 * c - 3 * c2t) / (8 * SQRT3)
    return out


def p_functions(theta, phi, sign):
    """Wigner P symbols p^a_{+/-}(theta, phi), Eq. (B.2) of 2302.00683 verbatim.

    Dual to ``q_functions``: (3/4pi) int p^n q^m dOmega = 2 delta_nm, so that the
    event average <p^a> equals Tr[rho_W T^a] for a single W.
    """
    _check_sign(sign)
    c, s, c2t, cp, sp, c2p, s2p = _trig(theta, phi)
    out = np.empty(c.shape + (8,))
    out[..., 0] = SQRT2 * s * (5 * c + sign) * cp
    out[..., 1] = SQRT2 * s * (5 * c + sign) * sp
    out[..., 2] = (5 + sign * 4 * c + 15 * c2t) / 4
    out[..., 3] = 5 * s * s * c2p
    out[..., 4] = 5 * s * s * s2p
    out[..., 5] = SQRT2 * s * (-5 * c + sign) * cp
    out[..., 6] = SQRT2 * s * (-5 * c + sign) * sp
    out[..., 7] = (-5 + sign * 12 * c - 15 * c2t) / (4 * SQRT3)
    return out


def projector(theta, phi, sign):
    """Pi_+ = |+1_n><+1_n| (sign=+1) or Pi_- = |-1_n><-1_n| (sign=-1),
    built as 1/3 + (1/2) sum_a q^a T^a."""
    q = q_functions(theta, phi, sign)
    return ID3 / 3 + 0.5 * np.einsum("...a,aij->...ij", q, GELL_MANN)


# --------------------------------------------------------------------------
# Vector (rank-1) and tensor (rank-2) polarisation; analyser flips
# --------------------------------------------------------------------------
_RANK1_BASIS = np.zeros((3, 8))
_RANK1_BASIS[0, [0, 5]] = 1 / SQRT2                       # S_x = (T1 + T6)/sqrt2
_RANK1_BASIS[1, [1, 6]] = 1 / SQRT2                       # S_y = (T2 + T7)/sqrt2
_RANK1_BASIS[2, 2], _RANK1_BASIS[2, 7] = 0.5, SQRT3 / 2   # S_z = T3/2 + sqrt3 T8/2
RANK1 = _RANK1_BASIS.T @ _RANK1_BASIS     # projector on vector-polarisation components
RANK2 = np.eye(8) - RANK1                 # projector on tensor-polarisation components
FLIP = RANK2 - RANK1                      # q(-n) = FLIP q(n), p(-n) = FLIP p(n)


def antipode(theta, phi):
    """Angles of the opposite direction -n: (pi - theta, phi + pi)."""
    return np.pi - np.asarray(theta, dtype=float), np.mod(np.asarray(phi, dtype=float) + np.pi, 2 * np.pi)


def mistag_dilution(w):
    """D(w) = RANK2 + (1 - 2w) RANK1: the average of q or p over an analyser
    direction that is flipped (n -> -n) with probability w, e.g. the
    down/up-type confusion of the two back-to-back quarks of a hadronic W."""
    return RANK2 + (1.0 - 2.0 * w) * RANK1


def mistag_correction(w):
    """Inverse of ``mistag_dilution``; undefined at w = 1/2 (no rank-1 information)."""
    if abs(1.0 - 2.0 * w) < 1e-12:
        raise ValueError("mistag rate w = 1/2 removes all rank-1 information")
    return RANK2 + RANK1 / (1.0 - 2.0 * w)


# --------------------------------------------------------------------------
# Per-event decay probability and moment estimators
# --------------------------------------------------------------------------
def trace_projectors(rho, theta_p, phi_p, theta_m, phi_m):
    """Tr[rho (Pi_+ x Pi_-)] for the analyser directions of the W+ and the W-.

    The decay distribution is (3/4pi)^2 times this; it lies in [0, 1] for a
    physical rho.  Evaluated as 1/9 + f.q+ + g.q- + q+.h.q-.
    """
    f, g, h = coefficients(rho)
    qp = q_functions(theta_p, phi_p, +1)
    qm = q_functions(theta_m, phi_m, -1)
    return 1.0 / 9.0 + qp @ f + qm @ g + np.einsum("...a,ab,...b->...", qp, h, qm)


def _corrected_p(theta, phi, sign, w):
    p = p_functions(theta, phi, sign)
    w = np.asarray(w, dtype=float)
    if not np.any(w):
        return p
    scale = 1.0 - 2.0 * w
    if np.any(np.abs(scale) < 1e-12):
        raise ValueError("mistag rate w = 1/2 removes all rank-1 information")
    if scale.ndim:
        scale = scale[..., None]
    rank1 = p @ RANK1          # RANK1 is symmetric
    return p - rank1 + rank1 / scale


def estimator_vector(theta_p, phi_p, theta_m, phi_m, mistag_p=0.0, mistag_m=0.0):
    """Per-event unbiased estimators x of the 80 coefficients, E[x] = c:
    x = [p+/6, p-/6, (p+ p-^T)/4] in ``pack`` order.

    ``mistag_p`` / ``mistag_m`` (scalar or per event) are the probabilities that the
    W+ / W- analyser direction was flipped; the P functions are then replaced by
    mistag_correction(w) p, which keeps x unbiased (CONVENTIONS.md Sec. 3).
    Memory: (n, 80) floats, so evaluate large samples in chunks.
    """
    pp = _corrected_p(theta_p, phi_p, +1, mistag_p)
    pm = _corrected_p(theta_m, phi_m, -1, mistag_m)
    hh = pp[..., :, None] * pm[..., None, :] / 4.0
    return np.concatenate([pp / 6.0, pm / 6.0, hh.reshape(hh.shape[:-2] + (64,))], axis=-1)


# --------------------------------------------------------------------------
# Linear subspaces of the 80-dimensional coefficient space
# --------------------------------------------------------------------------
_IMAGINARY = np.array([np.abs(op.real).max() < 1e-12 for op in OPERATORS])


def _null_space(m, rtol=1e-10):
    _, s, vt = np.linalg.svd(m)
    rank = int(np.sum(s > rtol * s.max()))
    return vt[rank:].T


def _rotation_constraints():
    jz = np.kron(SZ, ID3) + np.kron(ID3, SZ)
    comm = np.array([(jz @ op - op @ jz).ravel() for op in OPERATORS]).T
    return np.vstack([comm.real, comm.imag])


def subspace(name):
    """Orthonormal basis, shape (80, k), of a linear subspace of coefficients.

    'full'                     k = 80.
    'rotation_invariant'       k = 18: rho commutes with J_k = S_z x 1 + 1 x S_z,
                               i.e. it is invariant under a common rotation about k.
                               Holds for any spin-0 parent (SM, CP-odd admixtures,
                               mixtures over kinematics) and for 1/9.
    'rotation_invariant_real'  k = 13: additionally rho is real in the |m+ m-> basis
                               (no CP-even/CP-odd interference or absorptive phases);
                               contains the tree-level SM state.
    """
    if name == "full":
        return np.eye(N_COEFF)
    cons = _rotation_constraints()
    if name == "rotation_invariant":
        return _null_space(cons)
    if name == "rotation_invariant_real":
        sel = np.eye(N_COEFF)[_IMAGINARY]
        return _null_space(np.vstack([cons, sel]))
    raise ValueError(f"unknown subspace {name!r}")


# --------------------------------------------------------------------------
# Quadrature on the sphere (exact expectations in tests and studies)
# --------------------------------------------------------------------------
def sphere_quadrature(n_cos=24, n_phi=48):
    """Product rule on the unit sphere: Gauss-Legendre in cos(theta) x uniform in phi.

    Exact for spherical harmonics of degree <= min(2 n_cos - 1, n_phi - 1).
    Returns flat arrays (theta, phi, weight) with sum(weight) = 4 pi.
    """
    x, wx = np.polynomial.legendre.leggauss(n_cos)
    phi = (np.arange(n_phi) + 0.5) * 2 * np.pi / n_phi
    theta, phi = np.meshgrid(np.arccos(x), phi, indexing="ij")
    weight = np.outer(wx, np.full(n_phi, 2 * np.pi / n_phi))
    return theta.ravel(), phi.ravel(), weight.ravel()
