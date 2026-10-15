"""Frames and decay angles (PLAN.md Sec. 3.2, CONVENTIONS.md Sec. 4).

The key tests (PLAN.md rule 2) compare basis.trace_projectors(rho, angles from
frames.decay_angles) with H -> W+ W- -> 4f matrix elements evaluated directly on the
four-vectors: the SM one in closed form and a generic HVV vertex with explicit spinors.
The configurations come from frames.construct_event; the matrix elements depend only on
the four-vectors, which are checked to be physical.
"""
import time

import numpy as np
import pytest

from qtomo import basis, config, frames, sm

CONST = config.constants()
M_H = CONST["m_H"]
E_BEAM = CONST["sqrt_s"] / 2
SQRT2 = np.sqrt(2.0)
# (m_W+, m_W-) in GeV: both off-shell assignments, from near threshold to M* -> 0
MASS_POINTS = [(80.4, 30.0), (30.0, 80.4), (75.0, 4.0), (2.0, 82.0), (55.0, 50.0)]
INPUT_KEYS = ("p_H", "p_Wp", "p_Wm", "p_ana_p", "p_ana_m", "p_beam_eplus")


def _rng(seed):
    return np.random.default_rng(seed)


def _mdot(a, b):
    """Minkowski product (+, -, -, -), bilinear; independent of qtomo.frames."""
    return a[..., 0] * b[..., 0] - np.sum(a[..., 1:] * b[..., 1:], axis=-1)


def _boost_matrix(beta):
    """Lambda taking four-vectors from the rest frame of a body to the frame in which it
    moves with velocity beta (Jackson, Classical Electrodynamics, Sec. 11.3, beta -> -beta)."""
    beta = np.asarray(beta, dtype=float)
    b2 = np.sum(beta * beta, axis=-1)
    g = 1 / np.sqrt(1 - b2)
    lam = np.empty(beta.shape[:-1] + (4, 4))
    lam[..., 0, 0] = g
    lam[..., 0, 1:] = lam[..., 1:, 0] = g[..., None] * beta
    lam[..., 1:, 1:] = np.eye(3) + ((g - 1) / b2)[..., None, None] * beta[..., :, None] * beta[..., None, :]
    return lam


def _random_unit(r, n):
    v = r.normal(size=(n, 3))
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def _random_rotation(r):
    q, upper = np.linalg.qr(r.normal(size=(3, 3)))
    q = q * np.sign(np.diag(upper))
    return q if np.linalg.det(q) > 0 else -q


def _unit_vector(theta, phi):
    return np.stack([np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)], axis=-1)


def _polar(a, n, r, k):
    """(theta, phi) of a in the axes {n, r, k}, written out independently of qtomo.frames."""
    x, y, z = (np.sum(a * e, axis=-1) for e in (n, r, k))
    return np.arctan2(np.hypot(x, y), z), np.mod(np.arctan2(y, x), 2 * np.pi)


def _dphi(a, b):
    """a - b wrapped to (-pi, pi]."""
    return np.angle(np.exp(1j * (a - b)))


def _event(r, n, m_wp=None, m_wm=None, p_max=300.0, cos_theta=None, beam=None):
    """Random decay angles, production orientation, H lab momentum (|p| < p_max) and e+ beam
    direction (unless ``beam`` is given); random W masses (either W off-shell, M* >= 0.5 GeV)
    unless given."""
    if m_wp is None:
        heavy = r.uniform(45.0, 110.0, n)
        light = r.uniform(0.5, np.minimum(heavy, M_H - heavy) - 0.1)
        wplus_heavy = r.uniform(size=n) < 0.5
        m_wp, m_wm = np.where(wplus_heavy, heavy, light), np.where(wplus_heavy, light, heavy)
    kin = {"theta_p": np.arccos(r.uniform(-1, 1, n)), "phi_p": r.uniform(0, 2 * np.pi, n),
           "theta_m": np.arccos(r.uniform(-1, 1, n)), "phi_m": r.uniform(0, 2 * np.pi, n),
           "m_Wp": np.broadcast_to(m_wp, (n,)), "m_Wm": np.broadcast_to(m_wm, (n,)),
           "cos_Theta": r.uniform(-1, 1, n) if cos_theta is None else np.broadcast_to(cos_theta, (n,)),
           "psi": r.uniform(0, 2 * np.pi, n)}
    p_h = _random_unit(r, n) * r.uniform(0.0, p_max, n)[:, None]
    if beam is None:
        beam = np.concatenate([np.full((n, 1), E_BEAM), E_BEAM * _random_unit(r, n)], axis=1)
    return kin, frames.construct_event(**kin, m_H=M_H, p_H_lab=p_h, p_beam_eplus=beam)


def _angles(ev, **kwargs):
    return frames.decay_angles(*(ev[key] for key in INPUT_KEYS), **kwargs)


def _check_physical(ev, kin):
    """Four-momentum conservation, on-shell H, requested W masses, massless fermions."""
    scale = ev["p_H"][..., :1]
    assert np.all(np.abs(ev["p_Wp"] + ev["p_Wm"] - ev["p_H"]) < 1e-12 * scale)
    assert np.allclose(np.sqrt(_mdot(ev["p_H"], ev["p_H"])), M_H, rtol=1e-12)
    for s in ("p", "m"):
        f, fbar = ev["p_ana_" + s], ev["p_partner_" + s]
        assert np.all(np.abs(f + fbar - ev["p_W" + s]) < 1e-12 * scale)
        for x in (f, fbar):         # absolute rounding of a soft fermion is set by its parent
            assert np.all(np.abs(_mdot(x, x)) < 1e-12 * x[..., 0] * scale[..., 0])
        assert np.allclose(np.sqrt(_mdot(ev["p_W" + s], ev["p_W" + s])), kin["m_W" + s], rtol=1e-9)


def _spread(x):
    return (x.max() - x.min()) / np.abs(x.mean())


def _residual(x, y):
    """max |x - y| / max |x|: equality up to rounding, relative to the scale of the distribution.
    A ratio x/y would not do: near the zeros of a pure-state decay distribution both sides vanish
    and their ratio is rounding noise (relative error ~1e-16 <Tr>/Tr, Tr/<Tr> down to ~1e-8)."""
    return np.max(np.abs(x - y)) / np.max(np.abs(x))


def _chain_angles(ev):
    """Decay angles by the chain documented in decay_angles, with explicit boost matrices and
    independently of qtomo.frames: H frame from p_H alone, axes {n, r, k} from the H-frame W+ and
    e+ beam, each analyser boosted along its own W's H-frame momentum."""
    to_h = _boost_matrix(-ev["p_H"][:, 1:] / ev["p_H"][:, :1])

    def h_frame(v):
        return np.einsum("nij,nj->ni", to_h, np.broadcast_to(v, ev["p_H"].shape))

    k, p = (h_frame(ev[key])[:, 1:] for key in ("p_Wp", "p_beam_eplus"))
    k = k / np.linalg.norm(k, axis=-1, keepdims=True)
    p = p / np.linalg.norm(p, axis=-1, keepdims=True)
    cos_t = np.sum(p * k, axis=-1, keepdims=True)
    r = (p - cos_t * k) / np.sqrt(1 - cos_t ** 2)
    n = np.cross(r, k)
    out = {}
    for s in ("p", "m"):
        w, a = h_frame(ev["p_W" + s]), h_frame(ev["p_ana_" + s])
        a_w = np.einsum("nij,nj->ni", _boost_matrix(-w[:, 1:] / w[:, :1]), a)
        out["theta_" + s], out["phi_" + s] = _polar(a_w[:, 1:], n, r, k)
    return out


# --------------------------------------------------------------------------
# Four-vector algebra
# --------------------------------------------------------------------------
def test_boost_to_rest_frame():
    # hand-computed: ref = (5, 0, 0, 3) has m = 4, beta = 0.6, gamma = 1.25
    ref = np.array([5.0, 0.0, 0.0, 3.0])
    assert np.allclose(frames.boost_to_rest_frame([2.0, 1.0, 0.0, 1.0], ref), [1.75, 1.0, 0.0, -0.25],
                       rtol=0, atol=1e-15)
    # photon along beta: Doppler factor sqrt((1 - beta)/(1 + beta)) = 1/2
    assert np.allclose(frames.boost_to_rest_frame([2.0, 0.0, 0.0, 2.0], ref), [1.0, 0.0, 0.0, 1.0],
                       rtol=0, atol=1e-15)
    assert np.allclose(frames.boost_to_rest_frame(ref, ref), [4.0, 0.0, 0.0, 0.0], rtol=0, atol=1e-15)

    r = _rng(1)
    n = 1000
    beta = _random_unit(r, n) * r.uniform(0.01, 0.999, n)[:, None]
    mass = r.uniform(0.1, 200.0, n)
    ref = mass[:, None] * _boost_matrix(beta)[:, :, 0]          # mass m moving with beta
    p, q = r.normal(scale=50.0, size=(2, n, 4))
    out = frames.boost_to_rest_frame(p, ref)
    expected = np.einsum("nij,nj->ni", _boost_matrix(-beta), p)
    scale = np.abs(expected).max()                               # gamma up to 22
    rest = frames.boost_to_rest_frame(ref, ref)
    assert np.allclose(rest[:, 0], mass, rtol=1e-12)
    assert np.all(np.abs(rest[:, 1:]) < 1e-12 * ref[:, :1])
    assert np.allclose(out, expected, rtol=0, atol=1e-12 * scale)
    assert np.allclose(_mdot(out, frames.boost_to_rest_frame(q, ref)), _mdot(p, q),
                       rtol=0, atol=1e-12 * scale ** 2)
    assert np.allclose(frames.boost_from_rest_frame(out, ref), p, rtol=0, atol=1e-12 * scale)
    assert np.allclose(frames.boost_to_rest_frame(p, ref, mass=mass), out, rtol=0, atol=1e-12 * scale)
    # broadcasting over leading axes
    assert np.allclose(frames.boost_to_rest_frame(p[0], ref), np.einsum("nij,j->ni", _boost_matrix(-beta), p[0]))
    assert np.allclose(frames.boost_to_rest_frame(p, ref[0]), np.einsum("ij,nj->ni", _boost_matrix(-beta[0]), p))
    assert frames.boost_to_rest_frame(p.reshape(10, 100, 4), ref[:100]).shape == (10, 100, 4)


def test_minkowski_dot_and_invariant_mass():
    assert frames.minkowski_dot([2.0, 1.0, 0.0, 1.0], [5.0, 0.0, 0.0, 3.0]) == pytest.approx(7.0)
    assert frames.invariant_mass([5.0, 0.0, 0.0, 3.0]) == pytest.approx(4.0)
    assert frames.invariant_mass([1.0, 0.0, 2.0, 0.0]) == pytest.approx(-np.sqrt(3.0))  # spacelike


# --------------------------------------------------------------------------
# Helicity axes
# --------------------------------------------------------------------------
def test_helicity_axes():
    r = _rng(2)
    k = r.normal(size=(500, 3)) * r.uniform(0.1, 10.0, (500, 1))       # not normalised
    p = r.normal(size=(500, 3))
    n, rr, kk, cos_t, degenerate = frames.helicity_axes(k, p)
    k_hat = k / np.linalg.norm(k, axis=-1, keepdims=True)
    p_hat = p / np.linalg.norm(p, axis=-1, keepdims=True)
    assert not degenerate.any()
    assert np.allclose(kk, k_hat, atol=1e-15)
    assert np.allclose(cos_t, np.sum(p_hat * k_hat, axis=-1), atol=1e-15)
    sin_t = np.sqrt(1 - cos_t ** 2)[:, None]
    assert np.allclose(rr, (p_hat - cos_t[:, None] * k_hat) / sin_t, atol=1e-12)   # CONVENTIONS.md Sec. 4
    assert np.allclose(n, np.cross(rr, k_hat), atol=1e-12)
    triad = np.stack([n, rr, kk], axis=-1)                                     # columns n, r, k
    assert np.allclose(np.swapaxes(triad, -1, -2) @ triad, np.eye(3), atol=1e-14)
    assert np.allclose(np.linalg.det(triad), 1.0)                              # right-handed
    assert np.all(np.sum(p_hat * rr, axis=-1) > 0)                             # beam at +r in the (r, k) plane
    # broadcasting: one beam direction for all events; one W+ direction (k returned as a proper array,
    # not a zero-stride view)
    assert np.allclose(frames.helicity_axes(k, p[0])[1], frames.helicity_axes(k, np.tile(p[0], (500, 1)))[1])
    k_one = frames.helicity_axes(k[0], p)[2]
    assert k_one.shape == (500, 3) and k_one.flags.c_contiguous and k_one.flags.writeable


def test_helicity_axes_degenerate():
    """W+ along the beam axis: flagged, deterministic orthonormal right-handed axes."""
    k = np.array([[0.0, 0.0, 1.0], [0.3, -0.4, 0.5], [1.0, 2.0, -3.0], [0.0, 1.0, 0.0]])
    fallback = None
    for p in (2.5 * k, -k, k + 1e-13 * np.array([1.0, -1.0, 0.5])):
        n, rr, kk, cos_t, degenerate = frames.helicity_axes(k, p)
        assert degenerate.all() and np.allclose(np.abs(cos_t), 1.0)
        triad = np.stack([n, rr, kk], axis=-1)
        assert np.allclose(np.swapaxes(triad, -1, -2) @ triad, np.eye(3), atol=1e-14)
        assert np.allclose(np.linalg.det(triad), 1.0)
        if fallback is None:
            fallback = (n, rr)
        assert np.array_equal(n, fallback[0]) and np.array_equal(rr, fallback[1])  # independent of p
    # just above the threshold the regular construction is used and accurate
    n, rr, _, _, degenerate = frames.helicity_axes([0.0, 0.0, 1.0], [1e-6, 0.0, 1.0])
    assert not degenerate and np.allclose(rr, [1.0, 0.0, 0.0], atol=1e-12) and np.allclose(n, [0.0, -1.0, 0.0])
    _, _, _, _, degenerate = frames.helicity_axes([0.0, 0.0, 1.0], [1e-12, 0.0, 1.0])
    assert degenerate.shape == () and degenerate


# --------------------------------------------------------------------------
# Decay angles: round trip and invariances
# --------------------------------------------------------------------------
def test_round_trip():
    """construct_event -> decay_angles recovers every input: random angles, W masses down to
    0.5 GeV with either W off-shell, H lab momenta up to 300 GeV, random e+ beam direction."""
    r = _rng(3)
    kin, ev = _event(r, 20000)
    _check_physical(ev, kin)
    out = _angles(ev)
    for key in ("theta_p", "theta_m", "cos_Theta"):
        assert np.max(np.abs(out[key] - kin[key])) < 1e-9
    for key in ("m_Wp", "m_Wm"):
        assert np.max(np.abs(out[key] / kin[key] - 1)) < 1e-9
    for s in ("p", "m"):
        theta, phi = kin["theta_" + s], kin["phi_" + s]
        ok = np.sin(theta) > 1e-6                                   # phi is undefined on the k axis
        assert np.max(np.abs(_dphi(out["phi_" + s], phi)[ok])) < 1e-9
        assert np.all((out["phi_" + s] >= 0) & (out["phi_" + s] < 2 * np.pi))
        assert np.max(np.abs(_unit_vector(out["theta_" + s], out["phi_" + s]) - _unit_vector(theta, phi))) < 1e-9
    heavy, light = np.maximum(kin["m_Wp"], kin["m_Wm"]), np.minimum(kin["m_Wp"], kin["m_Wm"])
    assert np.allclose(out["M"], heavy, rtol=1e-9) and np.allclose(out["f"], light / heavy, rtol=1e-9)
    assert np.array_equal(out["wplus_offshell"], kin["m_Wp"] < kin["m_Wm"])
    assert 0.45 < out["wplus_offshell"].mean() < 0.55
    assert not out["degenerate"].any()


def test_angles_invariant_under_rotation_and_boost():
    """A common rotation and/or an extra common boost of the whole event, beam included,
    leaves every angle unchanged (the boost composes with p_H into a boost and a Wigner
    rotation of the H frame, which the axes follow).  The tolerance is 1e-9 up to a W lab
    Lorentz factor gamma = 300 and then grows as gamma^2, like the rounding (~2e-16 gamma^2)
    of the angles of a light, fast W* (gamma up to ~2000 here; a fixed 1e-9 fails for about
    1 seed in 1000)."""
    r = _rng(4)
    kin, ev = _event(r, 5000)
    ref = _angles(ev)
    rot = _random_rotation(r)
    lam = _boost_matrix(0.9 * _random_unit(r, 1)[0])

    def rotate(v):
        return np.concatenate([v[..., :1], v[..., 1:] @ rot.T], axis=-1)

    def gamma(e):
        return np.maximum(e["p_Wp"][:, 0] / kin["m_Wp"], e["p_Wm"][:, 0] / kin["m_Wm"])

    for transform in (rotate, lambda v: v @ lam.T, lambda v: rotate(v) @ lam.T):
        moved = {key: transform(v) for key, v in ev.items()}
        out = _angles(moved)
        tol = 1e-9 * np.maximum(1.0, np.maximum(gamma(ev), gamma(moved)) / 300) ** 2
        for key in ("theta_p", "theta_m", "cos_Theta", "m_Wp", "m_Wm"):
            assert np.all(np.abs(out[key] - ref[key]) < tol)
        for s in ("p", "m"):
            ok = np.sin(ref["theta_" + s]) > 1e-6
            assert np.all(np.abs(_dphi(out["phi_" + s], ref["phi_" + s])[ok]) < tol[ok])


def test_decay_angles_shapes():
    r = _rng(5)
    kin, ev = _event(r, 6)
    out = _angles(ev, return_frame=True)
    assert all(out[key].shape == (6,) for key in ("theta_p", "phi_m", "cos_Theta", "M", "f", "degenerate"))
    assert out["n_hat"].shape == (6, 3) and out["p_Wm_H"].shape == (6, 4)
    single = frames.decay_angles(*(ev[key][2] for key in INPUT_KEYS))      # one event: 0-d arrays
    assert single["theta_m"].shape == () and np.isclose(single["theta_m"], out["theta_m"][2])
    grid = frames.decay_angles(*(ev[key].reshape(2, 3, 4) for key in INPUT_KEYS[:-1]), ev["p_beam_eplus"][0])
    assert grid["phi_p"].shape == (2, 3)
    assert all(v.flags.writeable for res in (out, single, grid) for v in res.values())
    # both quark assignments of a hadronic W- on an extra axis: every output takes the common shape
    # as a writeable array (not a read-only broadcast view); the swapped one is the antipode
    hyp = frames.decay_angles(ev["p_H"], ev["p_Wp"], ev["p_Wm"], ev["p_ana_p"],
                              np.stack([ev["p_ana_m"], ev["p_partner_m"]]), ev["p_beam_eplus"])
    assert all(v.shape == (2, 6) and v.flags.writeable for v in hyp.values())
    assert np.array_equal(hyp["theta_p"][1], out["theta_p"]) and np.allclose(hyp["phi_m"][0], out["phi_m"])
    assert np.allclose(_unit_vector(hyp["theta_m"][1], hyp["phi_m"][1]),
                       -_unit_vector(out["theta_m"], out["phi_m"]), atol=1e-9)
    hyp["theta_p"][0, 0] = -1.0
    assert hyp["theta_p"][1, 0] == out["theta_p"][0]


# --------------------------------------------------------------------------
# First-principles matrix elements (PLAN.md rule 2)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("m_wp,m_wm", MASS_POINTS)
def test_sm_matrix_element(m_wp, m_wm):
    """H -> W+ W- -> l+ nu l- nubar with massless leptons, SM vertex g_mu,nu and V-A currents:
    at fixed W masses the propagators are constant and (Fierz) |M|^2 is proportional to
        (p_nu.p_l-)(p_nubar.p_l+) = (lambda + 12 M1^2 M2^2)/16 Tr[rho_SM (Pi+ x Pi-)],
    lambda + 12 M1^2 M2^2 = 4 M1^2 M2^2 (2 + kappa^2) being the helicity sum of sm.offshell_density.
    The Lorentz-invariant left side uses the four-vectors only; the right side the angles of
    decay_angles.  W+ -> u dbar has the same structure with dbar <-> l+ and u <-> nu (and
    W- -> d ubar with d <-> l-, ubar <-> nubar), hence the down-type analysers.  The constant
    ratio is checked as equality of |M|^2 and norm x Tr up to rounding (``_residual``), plus the
    least-squares constant, since the ratio itself is ill-conditioned where both sides vanish.

    Sensitivity: the neutrino as W+ analyser, a direct lab -> W boost of the analysers, or the
    W- angles taken in its own helicity frame (z = W- direction) break the constancy.  A
    left-handed frame (n = k x r, i.e. phi -> pi - phi for both analysers) does not: the SM
    distribution depends on the azimuths only through cos(dphi) and cos(2 dphi) (it is P-even),
    so the handedness is tested by test_generic_coupling_matrix_element.
    """
    r = _rng(10)
    kin, ev = _event(r, 4000, m_wp, m_wm)
    _check_physical(ev, kin)
    me = _mdot(ev["p_partner_p"], ev["p_ana_m"]) * _mdot(ev["p_partner_m"], ev["p_ana_p"])
    rho = sm.density_matrix(sm.kappa(M_H, m_wp, m_wm))
    norm = (sm.kallen(M_H ** 2, m_wp ** 2, m_wm ** 2) + 12 * m_wp ** 2 * m_wm ** 2) / 16

    def trace(theta_p, phi_p, theta_m, phi_m):
        return basis.trace_projectors(rho, theta_p, phi_p, theta_m, phi_m)

    out = _angles(ev, return_frame=True)
    tr = trace(out["theta_p"], out["phi_p"], out["theta_m"], out["phi_m"])
    assert _residual(me, norm * tr) < 1e-9
    assert np.sum(me * tr) / np.sum(tr * tr) == pytest.approx(norm, rel=1e-12)

    nu = _angles(dict(ev, p_ana_p=ev["p_partner_p"]))           # neutrino as the W+ analyser
    assert _spread(me / trace(nu["theta_p"], nu["phi_p"], nu["theta_m"], nu["phi_m"])) > 0.1
    axes = (out["n_hat"], out["r_hat"], out["k_hat"])
    lab_p = _polar(frames.boost_to_rest_frame(ev["p_ana_p"], ev["p_Wp"])[:, 1:], *axes)
    lab_m = _polar(frames.boost_to_rest_frame(ev["p_ana_m"], ev["p_Wm"])[:, 1:], *axes)
    assert _spread(me / trace(*lab_p, *lab_m)) > 0.1
    own = trace(out["theta_p"], out["phi_p"], np.pi - out["theta_m"], np.pi - out["phi_m"])
    assert _spread(me / own) > 0.1
    mirrored = trace(out["theta_p"], np.pi - out["phi_p"], out["theta_m"], np.pi - out["phi_m"])
    assert _residual(me, norm * mirrored) < 1e-9


# Generic HVV vertex with explicit spinors (Weyl representation, Peskin & Schroeder Ch. 3):
# gamma^mu = [[0, sigma^mu], [sigmabar^mu, 0]], gamma5 = diag(-1, 1), P_L = (1 - gamma5)/2.
SIGMA_BAR = np.array([[[1, 0], [0, 1]], [[0, -1], [-1, 0]], [[0, 1j], [-1j, 0]], [[-1, 0], [0, 1]]])
EPS_0123 = -1.0      # eps_{0123} = -eps^{0123}, eps^{0123} = +1; cancels between the two computations


def _chi_minus(p):
    """Two-spinor with (sigma . p_hat) chi = -chi."""
    theta = np.arccos(np.clip(p[..., 3] / np.linalg.norm(p[..., 1:], axis=-1), -1.0, 1.0))
    phi = np.arctan2(p[..., 2], p[..., 1])
    return np.stack([-np.exp(-1j * phi) * np.sin(theta / 2), np.cos(theta / 2) + 0j], axis=-1)


def _current(p_f, p_fbar):
    """J^mu = ubar(p_f) gamma^mu P_L v(p_fbar), massless: u_L^dagger sigmabar^mu v_L with the
    left-chiral components u_L = sqrt(2E) chi_-(p_f), v_L = sqrt(2E) chi_-(p_fbar)."""
    u = np.sqrt(2 * p_f[..., :1]) * _chi_minus(p_f)
    v = np.sqrt(2 * p_fbar[..., :1]) * _chi_minus(p_fbar)
    return np.einsum("...i,mij,...j->...m", u.conj(), SIGMA_BAR, v)


def _vertex(x, y, q1, q2, a, b, c):
    """V_{mu nu} x^mu y^nu, V = a g + b eps_{mu nu rho sigma} q1^rho q2^sigma/m_H^2 + c q2_mu q1_nu/m_H^2."""
    x, y, q1, q2 = np.broadcast_arrays(x, y, q1 + 0j, q2 + 0j)
    eps = EPS_0123 * np.linalg.det(np.stack([x, y, q1, q2], axis=-2))
    return a * _mdot(x, y) + (b * eps + c * _mdot(q2, x) * _mdot(q1, y)) / M_H ** 2


def _polarisation_vectors(q, n, r, k):
    """eps^mu(q, m), m = +1, 0, -1 on axis -2: the spherical basis e_+1 = -(n + i r)/sqrt2,
    e_0 = k, e_-1 = (n - i r)/sqrt2 of the W rest frame (spin quantised along +k, also for the
    W-), boosted to the H frame along the W momentum q."""
    e = np.stack([-(n + 1j * r) / SQRT2, k + 0j, (n - 1j * r) / SQRT2], axis=-2)
    e4 = np.concatenate([np.zeros(e.shape[:-1] + (1,)), e], axis=-1)
    return np.einsum("...ij,...mj->...mi", _boost_matrix(q[..., 1:] / q[..., :1]), e4)


def _spin_amplitudes(fr, a, b, c, n_sign=1.0):
    """M(m+, m-) = V_{mu nu} eps*^mu(q1, m+) eps*^nu(q2, m-) as flat 9-vectors (index 3 i(m+) + i(m-))
    from the decay_angles axes; n_sign = -1 builds them in the left-handed frame {-n, r, k}."""
    axes = (n_sign * fr["n_hat"], fr["r_hat"], fr["k_hat"])
    q1, q2 = fr["p_Wp_H"], fr["p_Wm_H"]
    e1 = _polarisation_vectors(q1, *axes).conj()
    e2 = _polarisation_vectors(q2, *axes).conj()
    return np.stack([_vertex(e1[..., i, :], e2[..., j, :], q1, q2, a, b, c)
                     for i in range(3) for j in range(3)], axis=-1)


@pytest.mark.parametrize("m_wp,m_wm", MASS_POINTS[:3])
def test_spinor_currents(m_wp, m_wm):
    """Validation of the spinor currents: conserved, -J.J* = 2 M^2, and for the SM vertex
    |J+ . J-|^2 = 16 (p_nu.p_l-)(p_nubar.p_l+) (the trace result behind test_sm_matrix_element)."""
    r = _rng(11)
    kin, ev = _event(r, 2000, m_wp, m_wm)
    sigma_dot = np.einsum("ni,iab->nab", ev["p_ana_p"][:, 1:] / ev["p_ana_p"][:, :1], -SIGMA_BAR[1:])
    chi = _chi_minus(ev["p_ana_p"])
    assert np.allclose(np.einsum("nab,nb->na", sigma_dot, chi), -chi, atol=1e-12)
    j_p = _current(ev["p_partner_p"], ev["p_ana_p"])             # ubar(nu) gamma P_L v(l+)
    j_m = _current(ev["p_ana_m"], ev["p_partner_m"])             # ubar(l-) gamma P_L v(nubar)
    for j, f, fbar, m in ((j_p, ev["p_partner_p"], ev["p_ana_p"], m_wp),
                          (j_m, ev["p_ana_m"], ev["p_partner_m"], m_wm)):
        size = np.abs(j).max(axis=-1) * (f[:, 0] + fbar[:, 0])
        assert np.all(np.abs(_mdot(j, f)) < 1e-12 * size) and np.all(np.abs(_mdot(j, fbar)) < 1e-12 * size)
        assert np.allclose(-_mdot(j, j.conj()), 2 * m ** 2, rtol=1e-12)
    sm_trace = 16 * _mdot(ev["p_partner_p"], ev["p_ana_m"]) * _mdot(ev["p_partner_m"], ev["p_ana_p"])
    assert _residual(sm_trace, np.abs(_mdot(j_p, j_m)) ** 2) < 1e-9


@pytest.mark.parametrize("m_wp,m_wm", MASS_POINTS)
def test_polarisation_vectors_give_sm_state(m_wp, m_wm):
    """For V = g_mu,nu the amplitudes M(m+, m-) from the polarisation vectors are exactly
    (|+-> - kappa |00> + |-+>), phases included: sm.state and sm.density_matrix are the state
    in the frames of decay_angles.  (The SM state is symmetric under e_+1 <-> e_-1, i.e. under
    n -> -n, so it cannot see the handedness; test_generic_coupling_matrix_element can.)"""
    r = _rng(12)
    _, ev = _event(r, 500, m_wp, m_wm)
    fr = _angles(ev, return_frame=True)
    kap = sm.kappa(M_H, m_wp, m_wm)
    psi = _spin_amplitudes(fr, 1.0, 0.0, 0.0)
    assert np.allclose(psi / np.sqrt(2 + kap ** 2), sm.state(kap), atol=1e-12)
    rho = np.einsum("ni,nj->nij", psi, psi.conj()) / np.sum(np.abs(psi) ** 2, axis=-1)[:, None, None]
    assert np.allclose(rho, sm.density_matrix(kap), atol=1e-12)
    assert np.allclose(_spin_amplitudes(fr, 1.0, 0.0, 0.0, n_sign=-1.0), psi, atol=1e-10)


@pytest.mark.parametrize("m_wp,m_wm", MASS_POINTS)
def test_generic_coupling_matrix_element(m_wp, m_wm):
    """M = V_{mu nu} J+^mu J-^nu, V = a g + b eps(., ., q1, q2)/m_H^2 + c q2 q1/m_H^2 with random
    complex a, b, c and explicit spinor currents, against rho = M M^dagger/Tr from the
    polarisation vectors in the decay_angles axes:
        |M|^2 = 4 M1^2 M2^2 sum|M(m+, m-)|^2 Tr[rho (Pi+ x Pi-)]
    for every configuration, to rounding (``_residual``).  The CP-odd b term gives a state outside
    the real subspace and sin(dphi) terms in the distribution, which fix the handedness of
    {n, r, k}: mirrored angles (phi -> pi - phi) or a consistently left-handed frame (n -> -n in
    the polarisation vectors and the angles) break the relation.  A common shift of the azimuthal
    origin cannot be seen by any spin-0 decay (rho commutes with J_k)."""
    r = _rng(13)
    _, ev = _event(r, 3000, m_wp, m_wm)
    fr = _angles(ev, return_frame=True)
    a, b, c = r.normal(size=3) + 1j * r.normal(size=3)
    psi = _spin_amplitudes(fr, a, b, c)
    norm = np.sum(np.abs(psi) ** 2, axis=-1)
    rho = np.einsum("ni,nj->nij", psi, psi.conj()) / norm[:, None, None]
    assert np.allclose(rho, rho[0], atol=1e-12)              # same state in every frame
    v = basis.coefficient_vector(rho[0])
    for name, inside in (("rotation_invariant", True), ("rotation_invariant_real", False)):
        sub = basis.subspace(name)
        assert np.allclose(sub @ (sub.T @ v), v, atol=1e-12) == inside

    me = np.abs(_vertex(_current(ev["p_partner_p"], ev["p_ana_p"]), _current(ev["p_ana_m"], ev["p_partner_m"]),
                        ev["p_Wp"], ev["p_Wm"], a, b, c)) ** 2
    tr = basis.trace_projectors(rho[0], fr["theta_p"], fr["phi_p"], fr["theta_m"], fr["phi_m"])
    assert _residual(me, 4 * m_wp ** 2 * m_wm ** 2 * norm * tr) < 1e-9

    mirrored = (fr["theta_p"], np.pi - fr["phi_p"], fr["theta_m"], np.pi - fr["phi_m"])
    assert _spread(me / basis.trace_projectors(rho[0], *mirrored)) > 1e-2
    psi_lh = _spin_amplitudes(fr, a, b, c, n_sign=-1.0)[0]
    rho_lh = np.outer(psi_lh, psi_lh.conj()) / np.sum(np.abs(psi_lh) ** 2)
    assert _spread(me / basis.trace_projectors(rho_lh, *mirrored)) > 1e-2


# --------------------------------------------------------------------------
# Edge cases
# --------------------------------------------------------------------------
def test_analyser_along_k():
    """theta = 0, pi (phi undefined) and close to them: theta is recovered and the analyser
    functions, which do not depend on phi on the k axis, agree with the inputs."""
    r = _rng(20)
    edge = np.array([0.0, 1e-10, 1e-6, np.pi - 1e-6, np.pi - 1e-10, np.pi])
    theta_p, theta_m = (x.ravel() for x in np.meshgrid(edge, edge))
    n = theta_p.size
    phi_p, phi_m = r.uniform(0, 2 * np.pi, (2, n))
    p_h = _random_unit(r, n) * 200.0
    ev = frames.construct_event(theta_p, phi_p, theta_m, phi_m, 30.0, 80.4, r.uniform(-1, 1, n),
                                r.uniform(0, 2 * np.pi, n), M_H, p_h, [E_BEAM, 0.0, 0.0, E_BEAM])
    out = _angles(ev)
    assert np.max(np.abs(out["theta_p"] - theta_p)) < 1e-9 and np.max(np.abs(out["theta_m"] - theta_m)) < 1e-9
    for sign, s, theta, phi in ((1, "p", theta_p, phi_p), (-1, "m", theta_m, phi_m)):
        assert np.allclose(basis.q_functions(out["theta_" + s], out["phi_" + s], sign),
                           basis.q_functions(theta, phi, sign), atol=1e-9)
    rho = basis.random_density_matrix(r)
    assert np.allclose(basis.trace_projectors(rho, out["theta_p"], out["phi_p"], out["theta_m"], out["phi_m"]),
                       basis.trace_projectors(rho, theta_p, phi_p, theta_m, phi_m), atol=1e-9)


def test_wplus_along_beam():
    """cos(Theta) = +-1: flagged, finite, deterministic; the fallback axes differ from the
    construction's by a rotation about k, so theta+-, phi+ - phi- and Tr[rho Pi+ x Pi-] of any
    state commuting with J_k (every spin-0 decay) are recovered."""
    r = _rng(21)
    kin, ev = _event(r, 400, cos_theta=np.repeat([1.0, -1.0], 200))
    out = _angles(ev)
    assert out["degenerate"].all() and all(np.all(np.isfinite(out[k])) for k in ("phi_p", "phi_m"))
    assert np.allclose(np.abs(out["cos_Theta"]), 1.0)
    for key in ("theta_p", "theta_m"):
        assert np.max(np.abs(out[key] - kin[key])) < 1e-9
    assert np.max(np.abs(_dphi(out["phi_p"] - out["phi_m"], kin["phi_p"] - kin["phi_m"]))) < 1e-9
    amp = r.normal(size=3) + 1j * r.normal(size=3)
    psi = np.zeros(9, dtype=complex)
    psi[[2, 4, 6]] = amp / np.linalg.norm(amp)                   # J_k = 0, random
    rho = np.outer(psi, psi.conj())
    assert np.allclose(basis.trace_projectors(rho, out["theta_p"], out["phi_p"], out["theta_m"], out["phi_m"]),
                       basis.trace_projectors(rho, kin["theta_p"], kin["phi_p"], kin["theta_m"], kin["phi_m"]),
                       atol=1e-9)
    again = _angles(ev)
    assert all(np.array_equal(out[k], again[k]) for k in ("phi_p", "phi_m"))
    # just off the axis (sin(Theta) = 1.4e-6) the regular construction still recovers phi,
    # to the rounding of k (~1e-14) divided by sin(Theta)
    kin, ev = _event(r, 200, p_max=60.0, cos_theta=np.repeat([1 - 1e-12, -1 + 1e-12], 100))
    out = _angles(ev)
    assert not out["degenerate"].any()
    assert np.max(np.abs(_dphi(out["phi_p"], kin["phi_p"]))) < 1e-7


def test_reco_level_frame_mismatch():
    """p_H != p_Wp + p_Wm (reco level, documented in decay_angles): no exception, finite angles;
    the W+ angles depend only on (p_H, p_Wp, p_ana_p, beam).  With p_H also shifted, as for a
    recoil-defined H frame, both analysers follow the documented chain (``_chain_angles``: H frame
    from p_H alone, each analyser boosted along its own W's H-frame momentum, axes {n, r, k}); the
    W- is not along -k here, so a W- boost along -k (the same at truth level) fails.  The angles
    approach the exact ones as the mismatch vanishes."""
    r = _rng(22)
    n = 2000
    kin, ev = _event(r, n, p_max=60.0)
    exact = _angles(ev)
    reco = dict(ev, p_Wm=ev["p_Wm"].copy(), p_ana_m=ev["p_ana_m"] * r.uniform(0.95, 1.05, (n, 1)))
    reco["p_Wm"][:, 1:] *= r.uniform(0.9, 0.99, (n, 1))          # stays timelike
    out = _angles(reco, return_frame=True)
    w_m = out["p_Wm_H"][:, 1:] / np.linalg.norm(out["p_Wm_H"][:, 1:], axis=-1, keepdims=True)
    assert np.median(np.linalg.norm(w_m + out["k_hat"], axis=-1)) > 1e-3   # W- not along -k
    assert all(np.all(np.isfinite(out[k])) for k in ("theta_p", "phi_p", "theta_m", "phi_m"))
    assert np.array_equal(out["theta_p"], exact["theta_p"]) and np.array_equal(out["phi_p"], exact["phi_p"])
    assert np.allclose(out["m_Wm"], np.sqrt(_mdot(reco["p_Wm"], reco["p_Wm"])))
    assert np.max(np.abs(out["theta_m"] - exact["theta_m"])) > 1e-3
    reco["p_H"] = ev["p_H"] + r.normal(scale=3.0, size=(n, 4))    # recoil-like H system
    out, chain = _angles(reco), _chain_angles(reco)
    for s in ("p", "m"):
        assert np.max(np.abs(out["theta_" + s] - chain["theta_" + s])) < 1e-9
        assert np.max(np.abs(_unit_vector(out["theta_" + s], out["phi_" + s])
                             - _unit_vector(chain["theta_" + s], chain["phi_" + s]))) < 1e-9
    for size in (1e-4, 1e-7):
        out = _angles(dict(ev, p_H=ev["p_H"] + r.normal(scale=size, size=(n, 4))))
        for s in ("p", "m"):
            diff = (_unit_vector(out["theta_" + s], out["phi_" + s])
                    - _unit_vector(exact["theta_" + s], exact["phi_" + s]))
            assert np.max(np.abs(diff)) < 1e2 * size


@pytest.mark.filterwarnings("error")
def test_systems_without_rest_frame_give_nan():
    """An H or W four-vector that is not future-directed timelike (spacelike, lightlike, or E <= 0,
    e.g. a reco W = l + p_miss with E_miss < -E_l) gives nan, not finite values, an exception or a
    warning: in the boosts, in every output that depends on it (module docstring), and in M, f."""
    p = [2.0, 1.0, 0.0, 1.0]
    bad = np.array([[-5.0, 0.0, 0.0, 3.0], [-4.0, 0.0, 0.0, 0.0],         # timelike, E < 0
                    [3.0, 0.0, 0.0, 3.0], [5.0, 3.0, 4.0, 0.0],           # exactly lightlike
                    [1.0, 2.0, 0.0, 0.0], [np.nan, 0.0, 0.0, 0.0]])       # spacelike, nan
    for boost in (frames.boost_to_rest_frame, frames.boost_from_rest_frame):
        assert np.all(np.isnan(boost(p, bad)))
    assert np.all(np.isnan(frames.boost_to_rest_frame(p, bad[:2], mass=4.0)))

    r = _rng(23)
    kin, ev = _event(r, 50, p_max=60.0)
    exact = _angles(ev)
    ang_p, ang_m = ("theta_p", "phi_p"), ("theta_m", "phi_m")
    flip = np.array([-1.0, 1.0, 1.0, 1.0])                       # E -> -E: timelike, past-directed
    spacelike = np.concatenate([0.5 * np.linalg.norm(ev["p_Wm"][:, 1:], axis=-1, keepdims=True),
                                ev["p_Wm"][:, 1:]], axis=-1)
    for p_wm in (ev["p_Wm"] * flip, spacelike):                   # W-: the W+ angles are unaffected
        out = _angles(dict(ev, p_Wm=p_wm))
        assert all(np.all(np.isnan(out[k])) for k in ang_m + ("M", "f")) and not out["wplus_offshell"].any()
        assert all(np.array_equal(out[k], exact[k]) for k in ang_p + ("cos_Theta",))
    assert np.all(out["m_Wm"] < 0)                                # signed invariant mass
    out = _angles(dict(ev, p_Wp=ev["p_Wp"] * flip))               # W+: also the axes, hence all angles
    assert all(np.all(np.isnan(out[k])) for k in ang_p + ang_m + ("cos_Theta", "M", "f"))
    for p_h in (ev["p_H"] * flip, np.array([10.0, 50.0, 0.0, 0.0])):    # H system: W masses unaffected
        out = _angles(dict(ev, p_H=p_h))
        assert all(np.all(np.isnan(out[k])) for k in ang_p + ang_m + ("cos_Theta",))
        assert np.array_equal(out["M"], exact["M"]) and np.array_equal(out["f"], exact["f"])
    # an exactly lightlike W+ (integer components: with the H at rest the H frame is exact) and a W+
    # at rest in the H frame (k undefined; both W masses are fine)
    h_rest, w_m, a_p, a_m = [125.0, 0, 0, 0], [60.0, 0, 0, -30.0], [10.0, 0, 6.0, 8.0], [10.0, 6.0, 0, -8.0]
    for p_wp, heavy in (([50.0, 30.0, 40.0, 0.0], np.nan), ([80.0, 0.0, 0.0, 0.0], 80.0)):
        out = frames.decay_angles(h_rest, p_wp, w_m, a_p, a_m, [E_BEAM, 0.0, 0.0, E_BEAM])
        assert all(np.isnan(out[k]) for k in ang_p + ang_m + ("cos_Theta",))
        assert np.array_equal(out["M"], heavy, equal_nan=True)


@pytest.mark.parametrize("m_wp,m_wm,cos_theta", [(80.0, 50.0, 0.0), (0.0, 30.0, 0.0), (80.0, -1.0, 0.0),
                                                  (np.nan, 30.0, 0.0), (80.0, 30.0, 1.5),
                                                  (80.0, 30.0, np.nan)])
def test_construct_event_rejects_unphysical_input(m_wp, m_wm, cos_theta):
    with pytest.raises(ValueError):
        frames.construct_event(1.0, 1.0, 1.0, 1.0, m_wp, m_wm, cos_theta, 0.0, M_H, [0, 0, 0],
                               [E_BEAM, 0, 0, E_BEAM])


def test_performance_one_million_events():
    """decay_angles on 1e6 events takes about a second (the bound leaves a wide margin)."""
    r = _rng(30)
    n = 1_000_000
    beam = np.array([E_BEAM, 0.0, 0.0, E_BEAM])                         # one beam vector for all events
    kin, ev = _event(r, n, 80.4, 30.0, p_max=60.0, beam=beam)
    start = time.perf_counter()
    out = frames.decay_angles(ev["p_H"], ev["p_Wp"], ev["p_Wm"], ev["p_ana_p"], ev["p_ana_m"], beam)
    elapsed = time.perf_counter() - start
    assert out["theta_p"].shape == (n,)
    assert np.max(np.abs(out["theta_m"] - kin["theta_m"])) < 1e-9
    assert elapsed < 15.0, f"decay_angles took {elapsed:.1f} s for 1e6 events"
