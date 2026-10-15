"""Higgs rest frame, helicity axes {n, r, k} and the W decay angles (PLAN.md Sec. 3.2,
CONVENTIONS.md Sec. 4), pinned down by tests/test_frames.py.

Four-vectors are arrays (..., 4) ordered (E, p_x, p_y, p_z) in GeV, metric (+, -, -, -);
every function is vectorised over, and broadcasts, the leading axes.

* H rest frame: pure boost from the lab along p_H (truth H, or the reco recoil /
  visible system chosen by the channel driver).
* k = W+ direction in the H frame, p = e+ beam direction boosted into the H frame,
  cos(Theta) = p.k, r = (p - cos(Theta) k)/sin(Theta), n = r x k = (p x k)/sin(Theta)
  (2302.00683 Eq. 2.26).  {n, r, k} is right-handed and serves both W bosons
  (x = n, y = r, z = k): the W- spin is also quantised along +k.
* Decay angles: each analyser is boosted lab -> H frame -> its W rest frame, the second
  step a pure boost along that W's H-frame momentum (a direct lab -> W boost differs by
  a Wigner rotation); theta = polar angle w.r.t. k, phi = atan2(a.r, a.n) in [0, 2 pi).
* Analysers (CONVENTIONS.md Sec. 2): W+ -> l+ or the down-type antiquark (W+ -> u dbar),
  W- -> l- or the down-type quark (W- -> d ubar).

With these conventions the decay distribution is (3/4pi)^2 Tr[rho (Pi+ x Pi-)]
(``basis.trace_projectors``) and the tree-level SM state is ``sm.density_matrix(kappa)``;
tests/test_frames.py checks both against four-fermion matrix elements.

Inputs that do not define a rest frame give nan in the affected outputs instead of raising
or warning: an H or W four-vector that is not future-directed timelike (spacelike,
lightlike, or E <= 0, e.g. a reco W = l + p_miss with E_miss < -E_l), or a W+ at rest in
the H frame.  Select ``np.isfinite`` events.  A four-vector that is lightlike only to
rounding formally has a rest frame, but the boost into it amplifies rounding by
(E/m)^2 ~ 1e16 and gives meaningless angles: cut on the reconstructed W masses.
"""
import numpy as np

from .sm import kallen

TWO_PI = 2.0 * np.pi
# Below this sin(Theta) the production plane is undefined to working precision: the
# regular construction would orient n with a rounding error ~1e-16/sin(Theta).
SIN_THETA_MIN = 1e-8


# --------------------------------------------------------------------------
# Four-vector algebra
# --------------------------------------------------------------------------
def _dot3(a, b):
    return np.einsum("...i,...i->...", a, b)


def _unit(v):
    return v / np.sqrt(_dot3(v, v))[..., None]


def minkowski_dot(a, b):
    """a.b = a_0 b_0 - a_vec.b_vec (bilinear, no complex conjugation)."""
    a, b = np.asarray(a), np.asarray(b)
    return a[..., 0] * b[..., 0] - _dot3(a[..., 1:], b[..., 1:])


def invariant_mass(p):
    """sqrt(p.p); -sqrt(-p.p) for a spacelike p (ROOT convention)."""
    m2 = minkowski_dot(p, p)
    return np.sign(m2) * np.sqrt(np.abs(m2))


def _has_rest_frame(p):
    """E > 0 and p.p > 0: p is future-directed timelike, the four-momentum of a system."""
    p = np.asarray(p, dtype=float)
    return (p[..., 0] > 0) & (minkowski_dot(p, p) > 0)


def boost_to_rest_frame(p, ref, mass=None):
    """p as seen in the rest frame of ref: pure boost with beta = ref_vec / ref_E.

        E' = (E_r E - P.p)/m,   p' = p + P [P.p/(E_r + m) - E]/m,   m^2 = ref.ref.

    p and ref broadcast against each other.  ref must be future-directed timelike
    (E_r > 0, m^2 > 0); a spacelike, lightlike or negative-energy ref has no rest frame
    and gives nan.  ``mass`` (optional) is the known rest mass of ref; it avoids the
    rounding of E_r^2 - P^2, relative ~1e-16 (E_r/m)^2, for light, fast references.
    """
    p = np.asarray(p, dtype=float)
    ref = np.asarray(ref, dtype=float)
    e_r, p_r = ref[..., 0], ref[..., 1:]
    with np.errstate(invalid="ignore", divide="ignore"):
        m = np.sqrt(e_r * e_r - _dot3(p_r, p_r)) if mass is None else np.asarray(mass, dtype=float)
        m = np.where((e_r > 0) & (m > 0), m, np.nan)
        dot = _dot3(p_r, p[..., 1:])
        out = np.empty(np.broadcast_shapes(p.shape, ref.shape))
        out[..., 0] = (e_r * p[..., 0] - dot) / m
        out[..., 1:] = p[..., 1:] + ((dot / (e_r + m) - p[..., 0]) / m)[..., None] * p_r
    return out


def boost_from_rest_frame(p, ref, mass=None):
    """Inverse of ``boost_to_rest_frame``: p given in the rest frame of ref, returned in
    the frame in which ref has four-momentum ref (nan unless ref is future-directed timelike)."""
    ref = np.array(ref, dtype=float)
    ref[..., 1:] *= -1.0
    return boost_to_rest_frame(p, ref, mass)


# --------------------------------------------------------------------------
# Helicity axes
# --------------------------------------------------------------------------
def _transverse_basis(a):
    """(u, v) completing unit vectors a (..., 3) to the right-handed triad (u, v, a);
    u is the coordinate axis least aligned with a, orthogonalised (deterministic)."""
    e = np.eye(3)[np.argmin(np.abs(a), axis=-1)]
    u = _unit(e - _dot3(e, a)[..., None] * a)
    return u, np.cross(a, u)


def helicity_axes(k_hat, p_hat):
    """Right-handed axes {n, r, k} from the W+ direction k and the e+ beam direction p
    in the H frame (CONVENTIONS.md Sec. 4); inputs need not be normalised.

    Returns (n_hat, r_hat, k_hat, cos_Theta, degenerate) with cos_Theta = p.k,
    r = (p - cos_Theta k)/sin_Theta and n = r x k, evaluated as n = (p x k)/|p x k|
    (made exactly orthogonal to k) and r = k x n.

    ``degenerate`` flags sin_Theta < SIN_THETA_MIN (W+ along the beam axis, measure
    zero), where the production plane is undefined.  The fallback r is the coordinate
    axis least aligned with k, orthogonalised to k, and n = r x k.  For a spin-0 parent
    rho commutes with J_k (``basis.subspace('rotation_invariant')``): the decay
    distribution does not depend on the azimuthal origin, so the fallback biases none of
    the coefficients a spin-0 decay can populate.
    """
    with np.errstate(invalid="ignore", divide="ignore"):      # zero-length input -> nan
        k = _unit(np.asarray(k_hat, dtype=float))
        p = _unit(np.asarray(p_hat, dtype=float))
    k, p = np.broadcast_arrays(k, p)
    shape = k.shape
    k, p = np.ascontiguousarray(k).reshape(-1, 3), p.reshape(-1, 3)    # k returned: no zero strides
    cos_t = np.clip(_dot3(p, k), -1.0, 1.0)
    c = np.cross(p, k)                          # sin(Theta) n
    c -= _dot3(c, k)[:, None] * k
    sin_t = np.sqrt(_dot3(c, c))
    degenerate = sin_t < SIN_THETA_MIN
    if np.any(degenerate):
        r_fallback, _ = _transverse_basis(k[degenerate])
        c[degenerate] = np.cross(r_fallback, k[degenerate])
        sin_t[degenerate] = 1.0
    n = c / sin_t[:, None]
    r = np.cross(k, n)
    return (n.reshape(shape), r.reshape(shape), k.reshape(shape),
            cos_t.reshape(shape[:-1]), degenerate.reshape(shape[:-1]))


def _polar_angles(a, n, r, k):
    """(theta, phi) of the vectors a (..., 3) in the frame {n, r, k}."""
    x, y, z = _dot3(a, n), _dot3(a, r), _dot3(a, k)
    theta = np.arctan2(np.hypot(x, y), z)
    phi = np.arctan2(y, x)
    phi = np.where(phi < 0.0, phi + TWO_PI, phi)
    return theta, np.where(phi >= TWO_PI, 0.0, phi)     # -tiny + 2 pi rounds to 2 pi


# --------------------------------------------------------------------------
# Decay angles
# --------------------------------------------------------------------------
def decay_angles(p_H, p_Wp, p_Wm, p_ana_p, p_ana_m, p_beam_eplus, return_frame=False):
    """Decay angles of both W analysers from lab four-vectors (PLAN.md Sec. 3.2).

    p_H: H rest-frame system; p_Wp, p_Wm: W+ and W-; p_ana_p: W+ analyser (l+ or the
    down-type antiquark); p_ana_m: W- analyser (l- or the down-type quark);
    p_beam_eplus: e+ beam, e.g. a single (4,) vector for all events.

    Returns a dict of arrays: theta_p, phi_p, theta_m, phi_m (theta in [0, pi], phi in
    [0, 2 pi), both analysers in the common {n, r, k} axes), cos_Theta (= p.k),
    m_Wp, m_Wm (invariant masses of p_Wp, p_Wm), M = max(m_Wp, m_Wm), f = min/max,
    wplus_offshell (m_Wp < m_Wm), degenerate (see ``helicity_axes``).  With
    ``return_frame`` also the H-frame axes n_hat, r_hat, k_hat and four-vectors
    p_Wp_H, p_Wm_H.

    p_H need not equal p_Wp + p_Wm (reco level): the H frame is defined by p_H alone,
    k is the W+ direction in it, and the W- analyser is boosted along the W- H-frame
    momentum, which is then not exactly -k; its angles are still measured in {n, r, k}.
    The W+ angles depend only on (p_H, p_Wp, p_ana_p, p_beam_eplus).

    A system without a rest frame (module docstring) gives nan in what depends on it:
    p_H or p_Wp in every angle and cos_Theta (the axes need k), p_Wm in theta_m, phi_m.
    M and f are nan, and wplus_offshell False, unless both p_Wp and p_Wm have a rest
    frame; m_Wp, m_Wm are always the signed ``invariant_mass``.  All outputs are
    writeable arrays of the common broadcast shape.
    """
    w_p = boost_to_rest_frame(p_Wp, p_H)
    w_m = boost_to_rest_frame(p_Wm, p_H)
    beam = boost_to_rest_frame(p_beam_eplus, p_H)
    k_dir = np.where(_has_rest_frame(w_p)[..., None], w_p[..., 1:], np.nan)    # needs a W+ system
    n, r, k, cos_t, degenerate = helicity_axes(k_dir, beam[..., 1:])
    a_p = boost_to_rest_frame(boost_to_rest_frame(p_ana_p, p_H), w_p)[..., 1:]
    a_m = boost_to_rest_frame(boost_to_rest_frame(p_ana_m, p_H), w_m)[..., 1:]
    theta_p, phi_p = _polar_angles(a_p, n, r, k)
    theta_m, phi_m = _polar_angles(a_m, n, r, k)
    shape = np.broadcast_shapes(theta_p.shape, theta_m.shape)

    m_wp, m_wm = invariant_mass(p_Wp), invariant_mass(p_Wm)
    both = _has_rest_frame(p_Wp) & _has_rest_frame(p_Wm)
    heavy = np.where(both, np.maximum(m_wp, m_wm), np.nan)
    light = np.where(both, np.minimum(m_wp, m_wm), np.nan)
    out = {"theta_p": theta_p, "phi_p": phi_p, "theta_m": theta_m, "phi_m": phi_m,
           "cos_Theta": cos_t, "m_Wp": m_wp, "m_Wm": m_wm, "M": heavy, "f": light / heavy,
           "wplus_offshell": both & (m_wp < m_wm), "degenerate": degenerate}
    # np.broadcast_to alone would give read-only views; np.asarray turns 0-d scalars into arrays
    out = {key: np.asarray(x) if x.shape == shape else np.broadcast_to(x, shape).copy()
           for key, x in out.items()}
    if return_frame:
        out.update(n_hat=n, r_hat=r, k_hat=k, p_Wp_H=w_p, p_Wm_H=w_m)
    return out


# --------------------------------------------------------------------------
# Inverse: four-vectors from decay angles
# --------------------------------------------------------------------------
def _with_energy(e, p3):
    out = np.empty(p3.shape[:-1] + (4,))
    out[..., 0] = e
    out[..., 1:] = p3
    return out


def construct_event(theta_p, phi_p, theta_m, phi_m, m_Wp, m_Wm, cos_Theta, psi,
                    m_H, p_H_lab, p_beam_eplus):
    """Exact lab four-vectors of H -> W+ W- -> 4 massless fermions with the given decay
    angles: the inverse of ``decay_angles`` (tests, toys with detector effects).

    theta_p, phi_p, theta_m, phi_m: analyser angles in {n, r, k} (theta in [0, pi]);
    m_Wp, m_Wm: W masses; cos_Theta, psi: production orientation,
    k = cos_Theta p + sin_Theta (cos psi u + sin psi v) in the H frame, where p is the
    e+ beam direction there, u the H-frame coordinate axis least aligned with p made
    orthogonal to p, and v = p x u; m_H: Higgs mass; p_H_lab (..., 3): H lab momentum;
    p_beam_eplus (..., 4): e+ beam.  Raises ValueError unless 0 < m_Wp, m_Wm,
    m_Wp + m_Wm <= m_H and |cos_Theta| <= 1 (hence also for nan).  For a spin-0 parent
    the decay angles are independent of (cos_Theta, psi), and both are uniform
    (isotropic H decay).

    Returns a dict of lab four-vectors (..., 4): p_H, p_Wp, p_Wm, p_ana_p, p_ana_m (the
    analysers, CONVENTIONS.md Sec. 2), p_partner_p (nu or u), p_partner_m (nubar or
    ubar) and p_beam_eplus, with p_H = p_Wp + p_Wm and p_W = p_ana + p_partner.  Each
    analyser is built in its W rest frame and boosted W -> H -> lab, as ``decay_angles``
    undoes.  At cos_Theta = +-1 the triad used here (n = p x w) differs from the
    ``helicity_axes`` fallback by a rotation about k (common shift of phi_p, phi_m).
    """
    scal = [np.asarray(x, dtype=float)
            for x in (theta_p, phi_p, theta_m, phi_m, m_Wp, m_Wm, cos_Theta, psi)]
    p_H_lab = np.asarray(p_H_lab, dtype=float)
    p_beam = np.asarray(p_beam_eplus, dtype=float)
    shape = np.broadcast_shapes(*(x.shape for x in scal), p_H_lab.shape[:-1], p_beam.shape[:-1])
    th_p, ph_p, th_m, ph_m, m1, m2, cos_t, psi = (np.broadcast_to(x, shape) for x in scal)
    if not (np.all(m1 > 0) and np.all(m2 > 0) and np.all(m1 + m2 <= m_H)):     # also rejects nan
        raise ValueError("construct_event needs 0 < m_Wp, m_Wm and m_Wp + m_Wm <= m_H")
    if not np.all(np.abs(cos_t) <= 1):
        raise ValueError("construct_event needs |cos_Theta| <= 1")

    p3 = np.broadcast_to(p_H_lab, shape + (3,))
    h = _with_energy(np.sqrt(m_H ** 2 + _dot3(p3, p3)), p3)
    beam = np.broadcast_to(p_beam, shape + (4,))

    # production orientation in the H frame: (n, r, k) from (p, cos_Theta, psi)
    p_hat = _unit(boost_to_rest_frame(beam, h)[..., 1:])
    u, v = _transverse_basis(p_hat)
    sin_t = np.sqrt(1.0 - cos_t ** 2)
    w = np.cos(psi)[..., None] * u + np.sin(psi)[..., None] * v
    k = cos_t[..., None] * p_hat + sin_t[..., None] * w
    r = sin_t[..., None] * p_hat - cos_t[..., None] * w
    n = np.cross(p_hat, w)                      # = r x k

    # W four-momenta in the H frame
    q = np.sqrt(np.maximum(kallen(m_H ** 2, m1 ** 2, m2 ** 2), 0.0)) / (2 * m_H)
    e1 = (m_H ** 2 + m1 ** 2 - m2 ** 2) / (2 * m_H)
    w_p = _with_energy(e1, q[..., None] * k)
    w_m = _with_energy(m_H - e1, -q[..., None] * k)

    def direction(theta, phi):
        st = np.sin(theta)[..., None]
        return (st * np.cos(phi)[..., None] * n + st * np.sin(phi)[..., None] * r
                + np.cos(theta)[..., None] * k)

    out = {"p_H": h, "p_beam_eplus": np.array(beam)}
    for tag, w_h, m, theta, phi in (("p", w_p, m1, th_p, ph_p), ("m", w_m, m2, th_m, ph_m)):
        a = (0.5 * m)[..., None] * direction(theta, phi)    # analyser momentum, W rest frame
        out["p_W" + tag] = boost_from_rest_frame(w_h, h, m_H)
        for name, sign in (("p_ana_", 1.0), ("p_partner_", -1.0)):
            f_h = boost_from_rest_frame(_with_energy(0.5 * m, sign * a), w_h, m)
            out[name + tag] = boost_from_rest_frame(f_h, h, m_H)
    return out
