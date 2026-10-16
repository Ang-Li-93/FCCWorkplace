"""Phase 1 (PLAN.md Sec. 5.2): kinematic studies of the central winter2023 ZH, H -> WW* signal.

Task A -- the W* mass window.  The H of the winter2023 Whizard samples is decayed by the Pythia 6.4.27
bundled in Whizard.  For the first decay of a resonance PYRESD raises CKIN(45) and CKIN(47) to
max(decay threshold, CKIN) and calls PYOFSH(2), which samples both W masses from constant-width
Breit-Wigners in M^2 between max(CKIN(45 or 47), PARP(42)) and m_H - max(CKIN(47 or 45), PARP(42)) and
accepts them with the weight lambda^1/2 [(1 - r1 - r2)^2 + 8 r1 r2], r_i = M_i^2 / m_H^2 -- the shape
of qtomo.sm.offshell_density.  The PYDATA defaults CKIN(45) = CKIN(47) = 12 GeV remove every W* below
12 GeV (PMAS(24,3), the Breit-Wigner truncation of ordinary decays, is not used on this path).
Sources (Pythia 6.4.27, GENSER copy on cvmfs, generator.pythia6_source): pydata.f l. 1644 (DATA CKIN:
CKIN(41..48) = 12, -1, 12, -1, 12, -1, 12, -1), l. 504 and 541 (PMAS(24,1) = 80.45 GeV,
PMAS(24,2) = 2.07115 GeV), l. 1660 and 1682 (MSTP(42) = 1, PARP(41..43) = 0.02, 2.0, 0.10);
pyresd.f l. 472-479 (CKIN(45), CKIN(47) and the call PYOFSH(2, ...)); pyofsh.f l. 52 (MMED = 1 for
H -> WW), l. 90-98 (mass limits), l. 281 (Breit-Wigner sampling), l. 291-292 (weight); pyinre.f l. 193
(PYINIT resets PMAS(24,2) to the PYWIDT width).  The same values are in the initialised data of the
Whizard 3.1.2 library of the winter2023 stack (MSTP(181..183) = 6, 427, 2012).  The Pythia 6.4 manual
itself is not on cvmfs (share/doc only holds the hepforge URL).

    window   fraction of the tree-level spectrum below 12 GeV and the effect of the truncation on the
             spectrum-averaged SM state (PDG constants, config/constants.yaml) and on the l nu q q
             yields; binned likelihood fit of the truth M = max(m_W+, m_W-) distribution for the
             W mass and width used by Pythia6.
    pythia6  (winter2023 environment only) H -> W+ W- decays with the Whizard-bundled Pythia6
             (PY1ENT + PYEXEC -> PYRESD -> PYOFSH), W bosons undecayed, the H settings of the
             FCC-config card; --pygive "CKIN(45)=0.5" ... opens the window.

Task B -- the Higgs rest frame for Phase 2.  Decay angles (qtomo.frames) in
    ww           the W+ W- rest frame (reference: the decaying H, m = 125.0 GeV),
    recorded     the recorded H (Pythia6 documentation copy = Whizard H, before the shower recoil),
    recoil_pre   the recoil against the pre-shower Z fermions, (sqrt(s), 0) - p_f - p_fbar, nominal sqrt(s),
    recoil_post  the recoil against the post-shower Z system: the shower conserves momentum and the H
                 takes the recoil, so p_Z,post = p_f + p_fbar - (p_WW - p_H,recorded) and
                 recoil_post = p_WW + [(sqrt(s), 0) - p_f - p_fbar - p_H,recorded] (ISR + beam-energy
                 spread only; what a perfect Z reconstruction gives).
Resolution of theta, phi, cos(theta) and of the analyser direction, and the bias of the truth
tomography in each frame, paired event by event with the reference (channel A and B samples).
--record FILE splits recoil_post into its beam-energy-spread and ISR parts with the EDM4hep record
(beams after the Gaussian spread and ISR photons) of the first wzp6_ee_mumuH_HWW_ecm240 file.

    source setup_hbs.sh   # winter2023 stack, Pythia6 only
    python analysis/phase1_kinematics.py pythia6 --n 1000000 --tag default --pygive "MSTJ(24)=0"
    python analysis/phase1_kinematics.py pythia6 --n 1000000 --tag open --pygive "MSTJ(24)=0" \
        "CKIN(45)=0.5" "CKIN(47)=0.5" "PARP(42)=0.5"
    source setup.sh       # Key4hep 2026-04-08 (qtomo); never in the same shell as setup_hbs.sh
    python analysis/phase1_kinematics.py window
    python analysis/phase1_kinematics.py frames [--record FILE] [--workers 4]
    python analysis/phase1_kinematics.py plot

Results (json, npz) go to <output_dir>/kinematics (config/phase1.yaml, git-ignored) or --out-dir;
figures to <figure_dir>/kinematics_*.{pdf,png}.  Study parameters (recoil window, binning, seeds, the
Pythia6 settings, resolution definitions) are the ``kinematics:`` block of config/phase1.yaml and the
generator facts (m_H, Pythia6 m_W and widths, the W mass window, the Pythia6 source) its ``generator:``
block (PLAN rule 5).
"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ANALYSIS_ROOT))

SLOT = {name: i for i, name in enumerate(
    ("beam_em", "beam_ep", "H", "Wp", "Wm", "ana_p", "partner_p", "ana_m", "partner_m", "zf1", "zf2"))}
FRAMES = ("ww", "recorded", "recoil_pre", "recoil_post")
FRAME_LABELS = {"ww": "$W^+W^-$ rest frame", "recorded": "recorded H",
                "recoil_pre": "recoil, pre-shower Z", "recoil_post": "recoil, post-shower Z",
                "recoil_post_bes": "recoil, beam-energy spread only", "recoil_post_isr": "recoil, ISR only"}
ANGLE_VARS = ("dtheta", "dphi", "dcos", "alpha")
BLOCK = 50_000


# --------------------------------------------------------------------------
# Common helpers
# --------------------------------------------------------------------------
def _cfg():
    from qtomo import config
    return config.load("phase1")


def _kcfg():
    """The ``kinematics:`` block of config/phase1.yaml."""
    return _cfg()["kinematics"]


def _generator():
    """The ``generator:`` block of config/phase1.yaml (central-sample generator facts)."""
    return _cfg()["generator"]


def _tail_key(t):
    return "tail_" + f"{t:g}".replace(".", "p")


def _out_dir(args):
    from qtomo import config
    d = Path(args.out_dir) if args.out_dir else config.resolve(_cfg()["output_dir"]) / "kinematics"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _json_default(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer, np.bool_)):
        return o.item()
    raise TypeError(type(o))


def _write_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=1, default=_json_default))
    print(f"wrote {path}")


def signal_samples():
    from qtomo import config
    return {n: s for n, s in config.load("samples")["samples"].items() if s["role"] == "signal"}


def truth_files(max_files=None):
    """(sample, channel, path) of the truth stage1 chunks (stage1/truth_hww.py)."""
    from qtomo import config
    base = config.resolve(_cfg()["output_dir"]) / "truth"
    out = []
    for name, s in signal_samples().items():
        files = sorted((base / name).glob("chunk_*.root"))
        out += [(name, s["channel"], f) for f in files[:max_files]]
    return out


def load_chunk(path):
    """Truth four-vectors (n, 11, 4) as (E, px, py, pz) in GeV and PDG codes (n, 11)."""
    import awkward as ak
    import uproot
    a = uproot.open(path)["events"].arrays(["truth_e", "truth_px", "truth_py", "truth_pz", "truth_pdg"],
                                           library="ak")
    p4 = np.stack([ak.to_numpy(a[k]).astype(float) for k in ("truth_e", "truth_px", "truth_py", "truth_pz")],
                  axis=-1)
    pdg = np.rint(ak.to_numpy(a["truth_pdg"])).astype(int)    # stored as float by FCCAnalyses
    return p4, pdg


def is_lvqq(pdg):
    """One W -> e/mu nu (analyser a charged lepton), the other hadronic (analyser a quark)."""
    a_p, a_m = np.abs(pdg[:, SLOT["ana_p"]]), np.abs(pdg[:, SLOT["ana_m"]])
    lep_p, lep_m = np.isin(a_p, (11, 13)), np.isin(a_m, (11, 13))
    had_p, had_m = (a_p >= 1) & (a_p <= 5), (a_m >= 1) & (a_m <= 5)
    return (lep_p & had_m) | (lep_m & had_p)


def wrap(dphi):
    return (dphi + np.pi) % (2 * np.pi) - np.pi


def unit_vectors(theta, phi):
    st = np.sin(theta)
    return np.stack([st * np.cos(phi), st * np.sin(phi), np.cos(theta)], axis=-1)


def opening_angle(th1, ph1, th2, ph2):
    """Angle between two directions given by polar angles (numerically stable at small angles)."""
    d = np.linalg.norm(unit_vectors(th1, ph1) - unit_vectors(th2, ph2), axis=-1)
    return 2.0 * np.arcsin(np.clip(0.5 * d, 0.0, 1.0))


# --------------------------------------------------------------------------
# Task A: the analytic spectrum with a lower cut on M*
# --------------------------------------------------------------------------
def segment_integrals(m_H, m_W, gamma_W, edges, n_u=6000, n_y=400):
    """Integrals of the tree-level (M_heavy, M*) density (qtomo.sm.offshell_density, ordered region
    M* <= M_heavy) over M* in each segment [edges[i], edges[i+1]), and of the weights 1/d, kappa/d,
    kappa^2/d (d = 2 + kappa^2) that fix the spectrum-averaged SM state.

    Midpoint rule in u = arctan((M_heavy^2 - m_W^2)/(m_W Gamma_W)) (flattens the Breit-Wigner) and in
    y = M*^2, with a separate grid in every segment so the segment edges are exact.
    Returns (w, a, b, c) arrays of length len(edges) - 1 (un-normalised)."""
    from qtomo import sm
    am = m_W * gamma_W
    lo_all = edges[0]
    u_lo = np.arctan((lo_all ** 2 - m_W ** 2) / am)
    u_hi = np.arctan(((m_H - lo_all) ** 2 - m_W ** 2) / am)
    du = (u_hi - u_lo) / n_u
    u = u_lo + (np.arange(n_u) + 0.5) * du
    mh = np.sqrt(m_W ** 2 + am * np.tan(u))
    jac_h = ((mh ** 2 - m_W ** 2) ** 2 + am ** 2) / (2 * am * mh)          # dM_heavy / du
    out = np.zeros((4, len(edges) - 1))
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        y_lo, y_hi = lo ** 2, min(hi, m_H / 2) ** 2
        if y_hi <= y_lo:
            continue
        dy = (y_hi - y_lo) / n_y
        ml = np.sqrt(y_lo + (np.arange(n_y) + 0.5) * dy)
        for blk in np.array_split(np.arange(n_u), 8):
            M, m = mh[blk, None], ml[None, :]
            w = sm.offshell_density(M, m, m_H, m_W, gamma_W) * (m <= M) * jac_h[blk, None] / (2 * m) * du * dy
            k = sm.kappa(m_H, M, m)
            d = 2 + k ** 2
            with np.errstate(invalid="ignore"):
                out[:, i] += [w.sum(), np.nansum(w / d), np.nansum(w * k / d), np.nansum(w * k * k / d)]
    return out


def averaged_state(a, b, c):
    """Spectrum-averaged SM density matrix from <1/d>, <kappa/d>, <kappa^2/d> (as sm.OffShellSpectrum)."""
    from qtomo import sm
    rho = np.zeros((9, 9))
    for i in (sm.I_PM, sm.I_MP):
        for j in (sm.I_PM, sm.I_MP):
            rho[i, j] = a
        rho[i, sm.I_00] = rho[sm.I_00, i] = -b
    rho[sm.I_00, sm.I_00] = c
    return rho.astype(complex)


def state_summary(rho, n_starts, x0=None):
    from qtomo import basis, bell
    c = basis.coefficient_vector(rho)
    ref = bell.i3_optimise(rho, n_starts=n_starts, full_output=True, x0=x0)
    return {"c": c, "i3": ref.value, "c2": float(bell.c2(rho)), "h44": float(c[basis.COEFF_LABELS.index("h44")]),
            "h55": float(c[basis.COEFF_LABELS.index("h55")]), "purity": float(basis.purity(rho).real)}, ref


def heavy_mass_model(edges, m_H, m_W, gamma_W, cut, n_m=4, n_s=64):
    """Per-bin integrals of the density of M = max(M1, M2) with M* in [cut, min(M, m_H - M)]
    (Gauss-Legendre in M within each bin and in M* between the exact limits)."""
    from qtomo import sm
    xm, wm = np.polynomial.legendre.leggauss(n_m)
    xs, ws = np.polynomial.legendre.leggauss(n_s)
    lo, hi = np.asarray(edges[:-1]), np.asarray(edges[1:])
    M = 0.5 * (lo + hi)[:, None] + 0.5 * (hi - lo)[:, None] * xm
    wM = 0.5 * (hi - lo)[:, None] * wm
    span = np.clip(np.minimum(M, m_H - M) - cut, 0.0, None)
    Ms = cut + span[..., None] * 0.5 * (xs + 1)
    inner = np.sum(sm.offshell_density(M[..., None], Ms, m_H, m_W, gamma_W) * 0.5 * ws, axis=-1) * span
    return np.sum(inner * wM, axis=1)


def light_mass_density(mstar, m_H, m_W, gamma_W, n_u=64):
    """Density of M* = min(M1, M2) at the points mstar (un-normalised), integrating M_heavy in
    [M*, m_H - M*] with the Breit-Wigner mapping u."""
    from qtomo import sm
    am = m_W * gamma_W
    mstar = np.asarray(mstar, dtype=float)
    xs, ws = np.polynomial.legendre.leggauss(n_u)
    u_lo = np.arctan((mstar ** 2 - m_W ** 2) / am)
    u_hi = np.arctan(((m_H - mstar) ** 2 - m_W ** 2) / am)
    u = 0.5 * (u_lo + u_hi)[:, None] + 0.5 * (u_hi - u_lo)[:, None] * xs
    mh = np.sqrt(m_W ** 2 + am * np.tan(u))
    jac = ((mh ** 2 - m_W ** 2) ** 2 + am ** 2) / (2 * am * mh)
    d = sm.offshell_density(mh, mstar[:, None], m_H, m_W, gamma_W) * jac
    return np.sum(d * 0.5 * ws, axis=1) * (u_hi - u_lo)


def fit_heavy_mass(counts, edges, m_H, cut, start):
    """Binned multinomial likelihood fit of (m_W, Gamma_W) to the M histogram; returns dict."""
    from scipy.optimize import minimize
    n = np.asarray(counts, dtype=float)

    def nll(theta):
        m_w, g_w = theta
        if g_w <= 0.1 or not 60 < m_w < 100:
            return 1e30
        mu = heavy_mass_model(edges, m_H, m_w, g_w, cut)
        p = mu / mu.sum()
        return -np.sum(n[n > 0] * np.log(p[n > 0]))

    res = minimize(nll, np.asarray(start, float), method="Nelder-Mead",
                   options={"xatol": 1e-7, "fatol": 1e-4, "maxiter": 2000})
    x = res.x
    h = np.array([2e-3, 2e-3])
    hess = np.zeros((2, 2))
    f0 = nll(x)
    for i in range(2):
        for j in range(2):
            ei, ej = np.eye(2)[i] * h[i], np.eye(2)[j] * h[j]
            hess[i, j] = (nll(x + ei + ej) - nll(x + ei - ej) - nll(x - ei + ej) + nll(x - ei - ej)) / (4 * h[i] * h[j])
    cov = np.linalg.inv(hess)
    mu = heavy_mass_model(edges, m_H, *x, cut)
    mu = mu / mu.sum() * n.sum()
    return {"m_W": x[0], "Gamma_W": x[1], "m_W_err": np.sqrt(cov[0, 0]), "Gamma_W_err": np.sqrt(cov[1, 1]),
            "corr": cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1]), "nll": f0, "converged": bool(res.success),
            "expected": mu}


def pearson(n, mu, min_expected):
    """Pearson chi^2 over bins with expected >= min_expected (config: 20); returns (chi2, n_bins)."""
    n, mu = np.asarray(n, float), np.asarray(mu, float)
    k = mu >= min_expected
    return float(np.sum((n[k] - mu[k]) ** 2 / mu[k])), int(k.sum())


def two_sample_chi2(n1, n2, min_count):
    """chi^2 compatibility of two histograms with different totals (bins with n1 + n2 >= min_count;
    config: 20)."""
    n1, n2 = np.asarray(n1, float), np.asarray(n2, float)
    s1, s2 = n1.sum(), n2.sum()
    k = (n1 + n2) >= min_count
    chi2 = np.sum((n1[k] / s1 - n2[k] / s2) ** 2 / (n1[k] / s1 ** 2 + n2[k] / s2 ** 2))
    return float(chi2), int(k.sum()) - 1


def window(args):
    """Task A: W* mass window -- analytic truncation effects, l nu q q yields, truth mass fit."""
    from scipy import stats as st

    from qtomo import basis, bell, config, frames
    out = _out_dir(args)
    const = config.constants()
    samples = signal_samples()
    lumi = config.load("samples")["luminosity_pb"]
    gen, kw = _generator(), _kcfg()["window"]
    cut = gen["w_mass_window"][0]                  # CKIN(45) = CKIN(47): lower limit of both W masses
    res = {"pythia6_source": gen["pythia6_source"], "ckin45": cut, "pmas24_pydata": (gen["m_W"], gen["Gamma_W_pydata"])}

    # ---- (2) analytic: fraction below 12 GeV and the averaged state with and without the cut ----
    if cut not in kw["truncation_scan"]:
        raise ValueError("kinematics.window.truncation_scan must contain generator.w_mass_window[0]")
    edges = np.array([const["mstar_min"]] + list(kw["truncation_scan"]) + [const["m_H"] / 2])
    w, a, b, cc = segment_integrals(const["m_H"], const["m_W"], const["Gamma_W"], edges)
    rows, ref_full = [], None
    for j, lo in enumerate(edges[:-1]):
        W = w[j:].sum()
        s, ref = state_summary(averaged_state(a[j:].sum() / W, b[j:].sum() / W, cc[j:].sum() / W),
                               kw["i3_n_starts"], x0=ref_full)
        if j == 0:
            ref_full = ref
            g_full = bell.i3_weights(ref.u, ref.v)
        s.update(mstar_min=lo, fraction_kept=W / w.sum(), i3_at_full_settings=float(g_full @ s["c"]))
        rows.append(s)
    full = rows[0]
    trunc = next(r for r in rows if r["mstar_min"] == cut)
    dc = trunc["c"] - full["c"]
    res["analytic_pdg"] = {
        "constants": {k: const[k] for k in ("m_H", "m_W", "Gamma_W", "mstar_min")},
        "fraction_below_cut": 1.0 - trunc["fraction_kept"],
        "full": {k: v for k, v in full.items() if k != "c"}, "truncated": {k: v for k, v in trunc.items() if k != "c"},
        "c_full": full["c"], "c_truncated": trunc["c"], "delta_c": dc,
        "delta_c_nonzero": {basis.COEFF_LABELS[i]: dc[i] for i in np.flatnonzero(np.abs(dc) > 1e-12)},
        "scan": [{k: v for k, v in r.items() if k != "c"} for r in rows]}
    print(f"PDG spectrum: fraction M* < {cut:g} GeV = {1 - trunc['fraction_kept']:.5f}; "
          f"I3 {full['i3']:.4f} -> {trunc['i3']:.4f}, C2 {full['c2']:.4f} -> {trunc['c2']:.4f}, "
          f"h44 {full['h44']:.5f} -> {trunc['h44']:.5f}")
    # generator parameters (m_H = 125.0; Pythia6 m_W, Gamma_W) for the direct comparison
    m_h_gen = gen["m_H"]
    if any(s.get("m_H") != m_h_gen for s in samples.values()):
        raise ValueError("generator.m_H differs from the m_H of a signal sample in samples.yaml")

    # ---- truth: W masses, decay classes, yields ----
    m_wp, m_wm, label, lvqq = [], [], [], []
    for name, ch, path in truth_files(args.max_files):
        p4, pdg = load_chunk(path)
        m_wp.append(frames.invariant_mass(p4[:, SLOT["Wp"]]))
        m_wm.append(frames.invariant_mass(p4[:, SLOT["Wm"]]))
        label.append(np.full(len(p4), name, dtype=object))
        lvqq.append(is_lvqq(pdg))
    m_wp, m_wm, label, lvqq = map(np.concatenate, (m_wp, m_wm, label, lvqq))
    heavy, light = np.maximum(m_wp, m_wm), np.minimum(m_wp, m_wm)
    n_tot = len(heavy)
    res["truth"] = {"n_events": n_tot, "mstar_min": light.min(), "mstar_max": light.max(),
                    "mheavy_min": heavy.min(), "mheavy_max": heavy.max(),
                    "n_below_cut": int(np.sum(light < cut))}
    print(f"truth: {n_tot} events, M* in [{light.min():.4f}, {light.max():.3f}], M in [{heavy.min():.3f}, {heavy.max():.3f}] GeV")

    yields = {}
    for ch in ("A", "B"):
        names = [n for n, s in samples.items() if s["channel"] == ch]
        n_hww = sum(samples[n]["cross_section_pb"] * lumi for n in names)
        n_lvqq, var = 0.0, 0.0
        for n in names:
            sel = label == n
            frac = lvqq[sel].mean()
            n_lvqq += samples[n]["cross_section_pb"] * lumi * frac
            var += (samples[n]["cross_section_pb"] * lumi) ** 2 * frac * (1 - frac) / sel.sum()
        f12 = res["analytic_pdg"]["fraction_below_cut"]
        yields[ch] = {"samples": names, "n_hww": n_hww, "n_lvqq_emu": n_lvqq, "n_lvqq_emu_mc_err": np.sqrt(var),
                      "lvqq_fraction": n_lvqq / n_hww,
                      "n_lvqq_below_cut": f12 * n_lvqq, "n_lvqq_above_cut_true": (1 - f12) * n_lvqq,
                      "overestimate_above_cut": 1.0 / (1.0 - f12)}
    res["yields_10p8_ab"] = yields
    for ch, y in yields.items():
        print(f"channel {ch}: N(H->WW) = {y['n_hww']:.0f}, N(lvqq e/mu) = {y['n_lvqq_emu']:.0f}; "
              f"M* < {cut:g} GeV (absent from the MC): {y['n_lvqq_below_cut']:.0f}")

    # ---- (3) fit of the truth M distribution ----
    m_edges = np.arange(cut, gen["w_mass_window"][1] + 1e-9, kw["heavy_bin_width"])
    h_heavy, _ = np.histogram(heavy, bins=m_edges)
    s_edges = np.arange(0.0, m_h_gen / 2 + 1e-9, kw["light_bin_width"])
    h_light, _ = np.histogram(light, bins=s_edges)
    fit = fit_heavy_mass(h_heavy, m_edges, m_h_gen, cut, (const["m_W"], const["Gamma_W"]))
    chi2_fit, nb = pearson(h_heavy, fit["expected"], kw["chi2_min_expected"])
    models = {"fit": (m_h_gen, fit["m_W"], fit["Gamma_W"]),
              "pythia6_pydata": (m_h_gen, gen["m_W"], gen["Gamma_W_pydata"]),
              "pdg_mH125p0": (m_h_gen, const["m_W"], const["Gamma_W"]),
              "pdg": (const["m_H"], const["m_W"], const["Gamma_W"])}
    gof = {}
    for key, (mh_, mw_, gw_) in models.items():
        mu = heavy_mass_model(m_edges, mh_, mw_, gw_, cut)
        mu = mu / mu.sum() * h_heavy.sum()
        chi2, nb = pearson(h_heavy, mu, kw["chi2_min_expected"])
        ndf = nb - 1 - (2 if key == "fit" else 0)
        gof[key] = {"m_H": mh_, "m_W": mw_, "Gamma_W": gw_, "chi2": chi2, "ndf": ndf, "p": float(st.chi2.sf(chi2, ndf)),
                    "expected": mu}
        # light-mass shape (M* in [cut, m_H/2))
        xg, wg = np.polynomial.legendre.leggauss(8)
        lo_, hi_ = s_edges[:-1], s_edges[1:]
        pts = 0.5 * (lo_ + hi_)[:, None] + 0.5 * (hi_ - lo_)[:, None] * xg
        dens = light_mass_density(pts.ravel(), mh_, mw_, gw_).reshape(pts.shape)
        mu_l = np.sum(dens * 0.5 * (hi_ - lo_)[:, None] * wg, axis=1) * (lo_ >= cut)
        mu_l = mu_l / mu_l.sum() * h_light.sum()
        chi2_l, nb_l = pearson(h_light, mu_l, kw["chi2_min_expected"])
        gof[key].update(chi2_light=chi2_l, ndf_light=nb_l - 1, p_light=float(st.chi2.sf(chi2_l, nb_l - 1)),
                        expected_light=mu_l)
        print(f"  {key:16s} m_H {mh_:.2f} m_W {mw_:.4f} G {gw_:.4f}: M chi2/ndf = {chi2:.1f}/{ndf}; "
              f"M* chi2/ndf = {chi2_l:.1f}/{nb_l - 1}")
    fitted_frac = {}
    for mmin in [const["mstar_min"]] + list(kw["fraction_lower_limits"]):
        e2 = np.array([mmin, cut, m_h_gen / 2])
        wseg = segment_integrals(m_h_gen, fit["m_W"], fit["Gamma_W"], e2)[0]
        fitted_frac[f"from_{mmin:g}"] = wseg[0] / wseg.sum()
    # expected number of events above the largest observed M
    m_hi = np.array([heavy.max(), gen["w_mass_window"][1]])
    p_tail = heavy_mass_model(m_hi, m_h_gen, fit["m_W"], fit["Gamma_W"], cut, n_m=16)[0]
    p_all = heavy_mass_model(m_edges, m_h_gen, fit["m_W"], fit["Gamma_W"], cut).sum()
    res["fit_heavy_mass"] = {
        "m_H_fixed": m_h_gen, "range": [cut, m_h_gen - cut], "bin_width": 0.2,
        **{k: v for k, v in fit.items() if k != "expected"},
        "chi2": chi2_fit, "n_bins_chi2": nb, "goodness": {k: {kk: vv for kk, vv in v.items() if not kk.startswith("expected")}
                                                           for k, v in gof.items()},
        "fraction_below_cut_fitted_params": fitted_frac,
        "expected_events_above_max_observed": n_tot * p_tail / p_all,
        "pull_m_W_vs_pdg": (fit["m_W"] - const["m_W"]) / fit["m_W_err"],
        "pull_Gamma_W_vs_pdg": (fit["Gamma_W"] - const["Gamma_W"]) / fit["Gamma_W_err"],
        "pull_m_W_vs_pydata": (fit["m_W"] - gen["m_W"]) / fit["m_W_err"],
        "pull_Gamma_W_vs_pydata": (fit["Gamma_W"] - gen["Gamma_W_pydata"]) / fit["Gamma_W_err"]}
    print(f"fit: m_W = {fit['m_W']:.4f} +- {fit['m_W_err']:.4f}, Gamma_W = {fit['Gamma_W']:.4f} +- {fit['Gamma_W_err']:.4f} "
          f"(corr {fit['corr']:.2f}); fraction below {cut:g} GeV with these: {fitted_frac}")

    # ---- Pythia6 standalone runs (pythia6 command), if present ----
    p6 = {}
    for tag in ("default", "open"):
        f = out / f"pythia6_{tag}.npz"
        if not f.exists():
            continue
        d = np.load(f)
        lp, hp = np.minimum(d["m_wp"], d["m_wm"]), np.maximum(d["m_wp"], d["m_wm"])
        ok = np.isfinite(lp) & np.isfinite(hp)
        lp, hp = lp[ok], hp[ok]
        frac = float(np.mean(lp < cut))
        entry = {"n": int(ok.sum()), "m_W": float(d["m_w"]), "Gamma_W": float(d["gamma_w"]),
                 "mstar_min": float(lp.min()), "mstar_max": float(lp.max()), "mheavy_max": float(hp.max()),
                 "fraction_below_cut": frac, "fraction_below_cut_err": float(np.sqrt(frac * (1 - frac) / ok.sum())),
                 "pygive": [str(x) for x in d["pygive"]]}
        hh, _ = np.histogram(hp, bins=m_edges)
        hl, _ = np.histogram(lp, bins=s_edges)
        if tag == "default":
            chi2, ndf = two_sample_chi2(h_heavy, hh, kw["two_sample_min_count"])
            entry.update(chi2_vs_truth_M=chi2, ndf_vs_truth_M=ndf, p_vs_truth_M=float(st.chi2.sf(chi2, ndf)))
            chi2, ndf = two_sample_chi2(h_light[s_edges[:-1] >= cut], hl[s_edges[:-1] >= cut], kw["two_sample_min_count"])
            entry.update(chi2_vs_truth_Mstar=chi2, ndf_vs_truth_Mstar=ndf, p_vs_truth_Mstar=float(st.chi2.sf(chi2, ndf)))
        else:      # analytic fraction with the same parameters and lower mass limit as the run
            e2 = np.array([float(d["mass_lower_limit"]), cut, m_h_gen / 2])
            wseg = segment_integrals(m_h_gen, float(d["m_w"]), float(d["gamma_w"]), e2)[0]
            entry["mass_lower_limit"] = float(d["mass_lower_limit"])
            entry["fraction_below_cut_analytic_same_params"] = wseg[0] / wseg.sum()
        p6[tag] = entry
        p6[tag + "_hist_heavy"], p6[tag + "_hist_light"] = hh, hl
        print(f"pythia6 {tag}: {entry}")
    res["pythia6"] = {k: v for k, v in p6.items() if not k.endswith(("_heavy", "_light"))}

    np.savez(out / "window_hist.npz", m_edges=m_edges, h_heavy=h_heavy, s_edges=s_edges, h_light=h_light,
             **{f"exp_{k}": v["expected"] for k, v in gof.items()},
             **{f"expl_{k}": v["expected_light"] for k, v in gof.items()},
             **{f"p6_{k}": v for k, v in p6.items() if k.endswith(("_heavy", "_light"))})
    _write_json(out / "window.json", res)


# --------------------------------------------------------------------------
# Task A: Pythia6 standalone (winter2023 environment)
# --------------------------------------------------------------------------
def _load_whizard_pythia6():
    """The Pythia 6.4.27 compiled into the Key4hep Whizard library (found from PATH/LD_LIBRARY_PATH)."""
    import ctypes
    import shutil
    whizard = shutil.which("whizard")
    if whizard is None:
        raise RuntimeError("whizard not on PATH: source setup_hbs.sh (winter2023 stack) first")
    libdir = Path(whizard).resolve().parents[1] / "lib"

    def find(name):
        dirs = [d for d in os.environ.get("LD_LIBRARY_PATH", "").split(":") if d]
        for prefix in (d for d in os.environ.get("CMAKE_PREFIX_PATH", "").split(":") if d):
            dirs += [f"{prefix}/lib", f"{prefix}/lib64"]
        for d in dirs:
            p = Path(d) / name
            if p.exists():
                return str(p)
        raise RuntimeError(f"{name} not found in LD_LIBRARY_PATH or CMAKE_PREFIX_PATH")

    for lib in (find("libHepMC3.so"), find("libHepMC3rootIO.so"), find("liblcio.so"),
                str(libdir / "libwhizard_prebuilt.so")):      # dependencies that libwhizard.so leaves undefined
        ctypes.CDLL(lib, mode=ctypes.RTLD_GLOBAL)
    return ctypes.CDLL(str(libdir / "libwhizard.so"), mode=ctypes.RTLD_GLOBAL)


def pythia6(args):
    """H(125) -> W+ W- with the Whizard-bundled Pythia6: PY1ENT + PYEXEC (-> PYRESD -> PYOFSH(2)),
    W bosons undecayed (MDCY(24,1) = 0); H settings and MDME switches of the FCC-config card."""
    import ctypes
    lib = _load_whizard_pythia6()

    class PyJets(ctypes.Structure):
        _fields_ = [("n", ctypes.c_int), ("npad", ctypes.c_int), ("k", ctypes.c_int * 20000),
                    ("p", ctypes.c_double * 20000), ("v", ctypes.c_double * 20000)]

    jets = PyJets.in_dll(lib, "pyjets_")
    base2 = ctypes.addressof(ctypes.c_char.in_dll(lib, "pydat2_"))
    pmas = (ctypes.c_double * 2000).from_address(base2 + 4 * 2000)        # PMAS(500,4) after KCHG(500,4)
    pypars = (ctypes.c_int * 200).in_dll(lib, "pypars_")                  # MSTP(200), then PARP(200)
    parp = (ctypes.c_double * 200).from_address(ctypes.addressof(pypars) + 4 * 200)
    base_s = ctypes.addressof(ctypes.c_char.in_dll(lib, "pysubs_"))       # MSEL, MSELPD, MSUB, KFIN, CKIN
    ckin = (ctypes.c_double * 200).from_address(base_s + 4 * (2 + 500 + 162))

    def pygive(s):
        b = s.encode()
        lib.pygive_(ctypes.c_char_p(b), ctypes.c_size_t(len(b)))

    card = list(_kcfg()["pythia6"]["pygive"])      # H settings of the FCC-config card, W undecayed
    for s in card + list(args.pygive):
        pygive(s)
    lib.pyinre_()                                    # resonance widths, as PYINIT does
    lower = max(ckin[44], ckin[46], parp[41])        # PYOFSH: max(CKIN(45/47), PARP(42)) (thresholds ~ 0)
    print(f"Pythia {pypars[180]}.{pypars[181]} ({pypars[182]}): PMAS(24,1) = {pmas[23]:.5f}, "
          f"PMAS(24,2) = {pmas[523]:.5f} after PYINRE; CKIN(45) = {ckin[44]}, CKIN(47) = {ckin[46]}, "
          f"PARP(42) = {parp[41]}", flush=True)
    ip, kf = ctypes.c_int(1), ctypes.c_int(25)
    pe, zero = ctypes.c_double(_generator()["m_H"]), ctypes.c_double(0.0)     # H at rest
    n = args.n
    m_h, m1, m2 = np.empty(n), np.full(n, np.nan), np.full(n, np.nan)
    for i in range(n):
        lib.py1ent_(ctypes.byref(ip), ctypes.byref(kf), ctypes.byref(pe), ctypes.byref(zero), ctypes.byref(zero))
        lib.pyexec_()
        m_h[i] = jets.p[16000]                       # P(1,5)
        for j in range(1, jets.n):
            if jets.k[8000 + j] == 1:                # mother = the H
                if jets.k[4000 + j] == 24:
                    m1[i] = jets.p[16000 + j]
                elif jets.k[4000 + j] == -24:
                    m2[i] = jets.p[16000 + j]
    path = _out_dir(args) / f"pythia6_{args.tag}.npz"
    np.savez(path, m_h=m_h, m_wp=m1, m_wm=m2, m_w=pmas[23], gamma_w=pmas[523], mass_lower_limit=lower,
             pygive=np.array(card + list(args.pygive)))
    light = np.minimum(m1, m2)
    print(f"{n} decays; M* in [{np.nanmin(light):.4f}, {np.nanmax(light):.3f}] GeV; "
          f"fraction M* < 12 GeV = {np.nanmean(light < 12):.5f}; wrote {path}")


# --------------------------------------------------------------------------
# Task B: Higgs frames
# --------------------------------------------------------------------------
def frame_vectors(p4, sqrt_s):
    p_ww = p4[:, SLOT["Wp"]] + p4[:, SLOT["Wm"]]
    p_h = p4[:, SLOT["H"]]
    p_z = p4[:, SLOT["zf1"]] + p4[:, SLOT["zf2"]]
    nominal = np.array([sqrt_s, 0.0, 0.0, 0.0])
    return {"ww": p_ww, "recorded": p_h, "recoil_pre": nominal - p_z,
            "recoil_post": p_ww + (nominal - p_z - p_h)}


def _angles(frames_mod, p_frame, p4):
    return frames_mod.decay_angles(p_frame, p4[:, SLOT["Wp"]], p4[:, SLOT["Wm"]], p4[:, SLOT["ana_p"]],
                                   p4[:, SLOT["ana_m"]], p4[:, SLOT["beam_ep"]])


def _per_event_differences(ang, ref, vec, vref, sel):
    """Angle and frame differences frame - reference for the selected events (float32)."""
    from qtomo import frames
    out = {}
    for leg in ("p", "m"):
        th, ph = ang[f"theta_{leg}"][sel], ang[f"phi_{leg}"][sel]
        th0, ph0 = ref[f"theta_{leg}"][sel], ref[f"phi_{leg}"][sel]
        out[f"dtheta_{leg}"] = th - th0
        out[f"dphi_{leg}"] = wrap(ph - ph0)
        out[f"dcos_{leg}"] = np.cos(th) - np.cos(th0)
        out[f"alpha_{leg}"] = opening_angle(th, ph, th0, ph0)
    d = vec[sel] - vref[sel]
    out.update(dE=d[:, 0], dpz=d[:, 3], dpt=np.hypot(d[:, 1], d[:, 2]), mass=frames.invariant_mass(vec[sel]))
    return {k: v.astype(np.float32) for k, v in out.items()}


def _frames_chunk(task):
    """One truth chunk: moment accumulators per (subset, frame) and of the paired differences,
    per-event analytic prediction sums, and per-event differences for the l nu q q events."""
    name, channel, path, sqrt_s, bins, recoil_window = task
    from qtomo import basis, frames, sm, tomography
    p4, pdg = load_chunk(path)
    need = [SLOT[k] for k in ("H", "Wp", "Wm", "ana_p", "ana_m", "beam_ep", "zf1", "zf2")]
    ok = np.all(pdg[:, need] != 0, axis=1)
    n_read = len(p4)
    p4, pdg = p4[ok], pdg[ok]
    vec = frame_vectors(p4, sqrt_s)
    ang = {f: _angles(frames, v, p4) for f, v in vec.items()}
    keys = ("theta_p", "phi_p", "theta_m", "phi_m")
    good = np.all([np.isfinite(ang[f][k]) for f in FRAMES for k in keys], axis=0)
    ref = ang["ww"]
    kappa = sm.kappa(frames.invariant_mass(vec["ww"]), ref["m_Wp"], ref["m_Wm"])
    mstar = np.minimum(ref["m_Wp"], ref["m_Wm"])
    good &= np.isfinite(kappa)
    lvqq = is_lvqq(pdg) & good
    m_rec = frames.invariant_mass(vec["recoil_post"])
    in_window = (m_rec >= recoil_window[0]) & (m_rec <= recoil_window[1])
    subsets = {f"{channel}_lvqq": lvqq, f"{channel}_all": good, f"{channel}_lvqqwin": lvqq & in_window}
    for lo, hi in bins:
        subsets[f"{channel}_lvqq_{lo:g}-{hi:g}"] = lvqq & (mstar >= lo) & (mstar < hi)
    for f in FRAMES:                                     # angles of excluded events: any finite value
        for k in keys:
            ang[f][k] = np.where(good, ang[f][k], 0.0)
    acc = {}
    for start in range(0, len(p4), BLOCK):
        sl = slice(start, start + BLOCK)
        x = {f: basis.estimator_vector(*(ang[f][k][sl] for k in keys)) for f in FRAMES}
        for sname, sel_all in subsets.items():
            s = sel_all[sl]
            if not s.any():
                continue
            for f in FRAMES:
                acc.setdefault((sname, f), tomography.MomentAccumulator()).add_vectors(x[f][s])
                if f != "ww":
                    acc.setdefault((sname, "d_" + f), tomography.MomentAccumulator()).add_vectors(x[f][s] - x["ww"][s])
    pred = {}
    for sname, sel in subsets.items():
        if sel.any():
            pred[sname] = (np.sum(basis.pack(*sm.coefficients(kappa[sel])), axis=0), int(sel.sum()))
    per_event = {"mstar": mstar[lvqq].astype(np.float32), "mheavy": np.maximum(ref["m_Wp"], ref["m_Wm"])[lvqq].astype(np.float32),
                 "channel": np.full(int(lvqq.sum()), channel), "sample": np.full(int(lvqq.sum()), name)}
    for f in FRAMES[1:]:
        for k, v in _per_event_differences(ang[f], ref, vec[f], vec["ww"], lvqq).items():
            per_event[f"{f}_{k}"] = v
    counts = {"n_read": n_read, "n_complete": int(ok.sum()), "n_good": int(good.sum()), "n_lvqq": int(lvqq.sum()),
              "recorded_identical": int(np.sum(np.max(np.abs(vec["recorded"] - vec["ww"]), axis=1)[good] < 1e-3))}
    return name, channel, {k: v.state() for k, v in acc.items()}, pred, per_event, counts


def _resolution(v, rng, n_batches, tails, core=True):
    """Residual v = frame - reference: RMS (about 0), mean, median, sigma68 (half-width of the central
    68.27 % interval), Gaussian core width (iterative fit within +-1.5 sigma), tail fractions |v| > t for
    t in ``tails`` (config: 0.05, 0.01); for a positive quantity (the opening angle alpha, core=None) the
    68.27 % and 90 % quantiles q68, q90 instead of sigma68 and the core.  Uncertainties from
    ``n_batches`` (config: 20) batch means."""
    import warnings

    from scipy.optimize import OptimizeWarning, curve_fit
    v = np.asarray(v, dtype=float)
    v = v[np.isfinite(v)]
    positive = core is None

    def gauss(x, a, mu, s):
        return a * np.exp(-0.5 * ((x - mu) / s) ** 2)

    def stats_of(x):
        out = {"rms": float(np.sqrt(np.mean(x ** 2))), "mean": float(np.mean(x))}
        out.update({_tail_key(t): float(np.mean(np.abs(x) > t)) for t in tails})
        if positive:
            q = np.quantile(x, [0.5, 0.682689, 0.9])
            out.update(median=float(q[0]), q68=float(q[1]), q90=float(q[2]))
            return out
        q = np.quantile(x, [0.158655, 0.5, 0.841345])
        out.update(median=float(q[1]), sigma68=float(0.5 * (q[2] - q[0])))
        if core:
            mu, s = q[1], out["sigma68"]
            if s > 1e-6:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", OptimizeWarning)
                        for _ in range(4):
                            h, e = np.histogram(x, bins=60, range=(mu - 1.5 * s, mu + 1.5 * s))
                            cen = 0.5 * (e[1:] + e[:-1])
                            popt, _ = curve_fit(gauss, cen, h, p0=(h.max(), mu, s), sigma=np.sqrt(np.maximum(h, 1)))
                            mu, s = popt[1], abs(popt[2])
                except (RuntimeError, ValueError):
                    s = np.nan
            out["core"] = float(s)
        return out

    full = stats_of(v)
    groups = np.array_split(v[rng.permutation(len(v))], n_batches)
    per = [stats_of(g) for g in groups]
    return {k: full[k] for k in full} | {k + "_err": float(np.std([p[k] for p in per], ddof=1) / np.sqrt(n_batches))
                                          for k in full}


def _c2_weights():
    from qtomo import basis
    w_p = basis.NORMS.copy()
    w_p[:8] -= 18.0
    w_m = basis.NORMS.copy()
    w_m[8:16] -= 18.0
    return w_p, w_m


def _tomo_summary(res_x, res_d, pred, ref_i3, rng, n_data, n_starts):
    """Tomography of one frame against the analytic prediction, and its paired shift from the reference."""
    from qtomo import basis, bell, stats
    h44, h55 = basis.COEFF_LABELS.index("h44"), basis.COEFF_LABELS.index("h55")
    g = bell.i3_weights(ref_i3.u, ref_i3.v)
    rot = basis.subspace("rotation_invariant")
    # The optimal settings of the SM state are degenerate (J_z orbit and further families with the same
    # I3), and g.c of a measured state depends on the point chosen (lvqq truth: 2.677-2.692 for
    # sigma_stat = 0.010).  Projecting c first onto the 13-dim rotation_invariant_real subspace
    # (CONVENTIONS.md Sec. 7) makes it essentially point independent (spread 1e-4): "i3_fixed_sm13".
    sm13 = basis.subspace("rotation_invariant_real")
    g_rot = sm13 @ (sm13.T @ g)
    resid = res_x.c - pred
    chi2, ndf, p = stats.chi_square(resid, res_x.cov)
    chi2_r, ndf_r, p_r = stats.chi_square(rot.T @ resid, rot.T @ res_x.cov @ rot)
    obs = bell.observables(res_x.rho, n_starts=n_starts, rng=rng, x0=ref_i3)
    inv, inv_s = res_x.invariants, res_x.invariants_sigma
    side = int(inv.c2_arg_wminus > inv.c2_arg_wplus)
    c2 = 2.0 * max(inv.c2_arg_wplus, inv.c2_arg_wminus, 0.0)
    c2_err = 2.0 * (inv_s.c2_arg_wplus, inv_s.c2_arg_wminus)[side]
    scale = np.sqrt(res_x.n_events / n_data) if n_data else np.nan
    out = {"n_events": res_x.n_events, "chi2_vs_pred": chi2, "ndf": ndf, "p_vs_pred": p,
           "chi2_rot_vs_pred": chi2_r, "ndf_rot": ndf_r, "p_rot_vs_pred": p_r,
           "i3_pred": ref_i3.value, "i3_fixed": float(g @ res_x.c), "i3_fixed_err": float(np.sqrt(g @ res_x.cov @ g)),
           "i3_fixed_sm13": float(g_rot @ res_x.c), "i3_fixed_sm13_err": float(np.sqrt(g_rot @ res_x.cov @ g_rot)),
           "i3_raw": obs["i3"], "i3_physical": obs["i3_physical"],
           "c2_unbiased": c2, "c2_unbiased_err": c2_err, "c2_pred": float(bell.c2(basis.density_matrix_from_vector(pred))),
           "h44": float(res_x.c[h44]), "h44_err": float(res_x.sigma[h44]), "h44_pred": float(pred[h44]),
           "h55": float(res_x.c[h55]), "h55_err": float(res_x.sigma[h55]),
           "c": res_x.c, "sigma": res_x.sigma, "c_pred": pred, "sigma_data": res_x.sigma * scale,
           "n_data": n_data}
    if res_d is not None:
        d, cov = res_d.c, res_d.cov
        chi2_b, ndf_b, p_b = stats.chi_square(d, cov)
        w = _c2_weights()[side]
        cbar = res_x.c - 0.5 * d
        grad = 2.0 * w * cbar
        inv_r = (res_x.invariants.c2_arg_wplus, res_x.invariants.c2_arg_wminus)
        out.update(bias=d, bias_sigma=res_d.sigma, bias_chi2=chi2_b, bias_ndf=ndf_b, bias_p=p_b,
                   bias_max_abs_pull=float(np.max(np.abs(d) / res_d.sigma)),
                   bias_over_sigma_data=d / (res_x.sigma * scale),
                   di3_fixed=float(g @ d), di3_fixed_err=float(np.sqrt(g @ cov @ g)),
                   di3_fixed_sm13=float(g_rot @ d), di3_fixed_sm13_err=float(np.sqrt(g_rot @ cov @ g_rot)),
                   dh44=float(d[h44]), dh44_err=float(res_d.sigma[h44]),
                   dh55=float(d[h55]), dh55_err=float(res_d.sigma[h55]),
                   dc2_linear=float(grad @ d), dc2_err=float(np.sqrt(grad @ cov @ grad)),
                   c2_arg_side=("wplus", "wminus")[side], c2_arg=inv_r[side])
    return out


def frames_cmd(args):
    """Task B: decay angles and truth tomography in four Higgs frames, channel A and B samples."""
    from concurrent.futures import ProcessPoolExecutor

    from qtomo import basis, bell, config, tomography
    c = _cfg()
    kc = c["kinematics"]
    rp = kc["resolution"]
    out = _out_dir(args)
    const = config.constants()
    samples = signal_samples()
    lumi = config.load("samples")["luminosity_pb"]
    bins = list(zip(c["mstar_bins"][:-1], c["mstar_bins"][1:]))
    recoil_window = tuple(kc["recoil_window"])
    tasks = [(n, ch, str(p), const["sqrt_s"], bins, recoil_window) for n, ch, p in truth_files(args.max_files)]
    accs, preds, per_event, counts = {}, {}, [], {}
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for name, ch, acc_states, pred, pe, cnt in pool.map(_frames_chunk, tasks):
            for key, stt in acc_states.items():
                a = tomography.MomentAccumulator.from_state(stt)
                accs[key] = accs[key].merge(a) if key in accs else a
            for s, (vsum, nn) in pred.items():
                v0, n0 = preds.get(s, (0.0, 0))
                preds[s] = (v0 + vsum, n0 + nn)
            per_event.append(pe)
            cs = counts.setdefault(name, {})
            for k, v in cnt.items():
                cs[k] = cs.get(k, 0) + v
            print(f"  {Path(name).name} chunk done ({cnt['n_good']} events)", flush=True)
    per_event = {k: np.concatenate([p[k] for p in per_event]) for k in per_event[0]}
    # expected pre-selection l nu q q (e, mu) yields at 10.8 ab-1 (sample cross sections x truth fractions)
    n_data = {}
    for ch in ("A", "B"):
        n_data[ch] = sum(samples[n]["cross_section_pb"] * lumi * counts[n]["n_lvqq"] / counts[n]["n_good"]
                         for n in samples if samples[n]["channel"] == ch and n in counts)
    rng = np.random.default_rng(kc["seed"])
    results = {"counts": counts, "n_data_lvqq_emu": n_data, "sqrt_s": const["sqrt_s"],
               "recoil_window": recoil_window, "subsets": {}}
    for sname in sorted({k[0] for k in accs}):
        ch, kind = sname.split("_")[0], sname.split("_")[1]
        vsum, nn = preds[sname]
        pred = vsum / nn
        # reference settings as in phase1_truth.py (same n_starts and seed): the SM optimum is a J_z orbit,
        # and the fixed-settings I3 of a measured (not exactly rotation-invariant) state depends on the point
        ref_i3 = bell.i3_optimise(basis.density_matrix_from_vector(pred), n_starts=c["i3_n_starts"], full_output=True)
        nd = None                                             # data yield (l nu q q e/mu, no selection)
        if kind in ("lvqq", "lvqqwin"):                       # subsets scaled by their MC fraction
            nd = n_data[ch] * nn / preds[f"{ch}_lvqq"][1]
        entry = {}
        for f in FRAMES:
            if (sname, f) not in accs:
                continue
            rd = accs[(sname, "d_" + f)].result() if f != "ww" else None
            entry[f] = _tomo_summary(accs[(sname, f)].result(), rd, pred, ref_i3, rng, nd, c["i3_n_starts"])
        results["subsets"][sname] = entry
        e = entry
        line = f"{sname:22s} N = {e['ww']['n_events']:8d}"
        for f in FRAMES:
            s = e[f]
            line += (f" | {f}: chi2/ndf {s['chi2_vs_pred']:.0f}/{s['ndf']}"
                     + (f", dI3 {s['di3_fixed']:+.4f}+-{s['di3_fixed_err']:.4f}, bias chi2 {s['bias_chi2']:.0f}" if f != "ww" else ""))
        print(line)
    # resolution of the angles (l nu q q events)
    res_tab = {}
    m_post = per_event["recoil_post_mass"]
    window_sel = (m_post >= recoil_window[0]) & (m_post <= recoil_window[1])

    def resolution(v, core=True):
        return _resolution(v, rng, rp["n_batches"], rp["tail_thresholds"], core=core)
    for ch in ("A", "B"):
        sel_ch = per_event["channel"] == ch
        res_tab[f"{ch}/recoil_window_efficiency"] = float(window_sel[sel_ch].mean())
        for f in FRAMES[1:]:
            for leg in ("p", "m"):
                for var in ANGLE_VARS:
                    key = f"{f}_{var}_{leg}"
                    res_tab[f"{ch}/{key}"] = resolution(per_event[key][sel_ch], core=None if var == "alpha" else True)
                    if var in ("alpha", "dcos"):                  # inside the recoil-mass window
                        res_tab[f"{ch}/{key}_win"] = resolution(per_event[key][sel_ch & window_sel],
                                                                core=None if var == "alpha" else True)
            for var in ("alpha", "dcos"):
                vb = []
                for lo, hi in bins:
                    sb = sel_ch & (per_event["mstar"] >= lo) & (per_event["mstar"] < hi)
                    if sb.sum() < rp["min_events_bin"]:
                        continue
                    v = np.concatenate([per_event[f"{f}_{var}_p"][sb], per_event[f"{f}_{var}_m"][sb]])
                    vb.append({"lo": lo, "hi": hi, **resolution(v, core=None if var == "alpha" else False)})
                res_tab[f"{ch}/{f}_{var}_vs_mstar"] = vb
            for var in ("dE", "dpz", "dpt", "mass"):
                v = per_event[f"{f}_{var}"][sel_ch].astype(float)
                q = np.quantile(v, [0.01, 0.158655, 0.5, 0.841345, 0.99])
                res_tab[f"{ch}/{f}_{var}_summary"] = {"mean": float(v.mean()), "rms": float(np.sqrt(np.mean(v ** 2))),
                                                      "quantiles_1_16_50_84_99": q,
                                                      f"frac_abs_gt_{rp['shift_threshold']:g}GeV":
                                                          float(np.mean(np.abs(v) > rp["shift_threshold"]))}
    results["resolution"] = res_tab
    hist = {k: v for k, v in per_event.items() if k not in ("sample",)}
    np.savez(out / "frames_events.npz", **hist)
    if args.record:
        results["record"] = record_decomposition(args.record, const["sqrt_s"], rng, out, kc)
    _write_json(out / "frames.json", results)


def record_decomposition(record_path, sqrt_s, rng, out_dir, kc):
    """Beam-energy-spread / ISR split of recoil_post on one EDM4hep file of kinematics.record_sample
    (wzp6_ee_mumuH_HWW_ecm240; the file of truth chunk_000, matched event by event).  Record of the
    Whizard events: 0, 1 nominal beams; 2, 3 beams after the Gaussian spread; 4, 5 e-/e+ after ISR (hard
    process); 6, 7 the ISR photons; 8, 9 the hard-process Z fermions; 10 the H."""
    import awkward as ak
    import uproot

    from qtomo import basis, frames, stats, tomography
    name = kc["record_sample"]
    rp = kc["resolution"]

    def resolution(v, core=True):
        return _resolution(v, rng, rp["n_batches"], rp["tail_thresholds"], core=core)
    chunk = truth_files(1)
    chunk = [p for n, _, p in chunk if n == name][0]
    br = {"pdg": "Particle/Particle.PDG", "m": "Particle/Particle.mass", "px": "Particle/Particle.momentum.x",
          "py": "Particle/Particle.momentum.y", "pz": "Particle/Particle.momentum.z",
          "status": "Particle/Particle.generatorStatus"}
    a = uproot.open(record_path)["events"].arrays(list(br.values()), library="ak")
    if ak.min(ak.num(a[br["pdg"]])) < 11:
        raise RuntimeError("record with fewer than 11 particles")
    first = {k: np.asarray(ak.to_regular(a[v][:, :11], axis=1)) for k, v in br.items()}
    p3 = np.stack([first["px"], first["py"], first["pz"]], axis=-1).astype(float)
    e = np.sqrt(np.sum(p3 ** 2, axis=-1) + first["m"].astype(float) ** 2)
    rec = np.concatenate([e[..., None], p3], axis=-1)              # (n, 11, 4)
    pdg = first["pdg"]
    # total four-momentum of the final state (generatorStatus 1) against the beams after the spread
    fs = a[br["status"]] == 1
    tot = np.stack([ak.to_numpy(ak.sum(np.sqrt(a[br["px"]] ** 2 + a[br["py"]] ** 2 + a[br["pz"]] ** 2 + a[br["m"]] ** 2)[fs], axis=1))]
                   + [ak.to_numpy(ak.sum(a[br[k]][fs], axis=1)) for k in ("px", "py", "pz")], axis=-1)
    conservation = np.max(np.abs(tot - rec[:, 2] - rec[:, 3]), axis=1)
    del a
    structure = np.all(pdg[:, :8] == np.array([11, -11, 11, -11, 11, -11, 22, 22]), axis=1)
    # ISR in Whizard's "recoil" mode balances momentum between the two sides, so only the total
    # p2 + p3 = p4 + p5 + p6 + p7 holds (each side alone is off by up to ~1 GeV in 20 % of events)
    split_ok = np.max(np.abs(rec[:, 2] + rec[:, 3] - rec[:, 4] - rec[:, 5] - rec[:, 6] - rec[:, 7]), axis=1) < 1e-3
    p4, _ = load_chunk(chunk)
    n = min(len(p4), len(rec))
    match = np.max(np.abs(rec[:n, 8] - p4[:n, SLOT["zf1"]]), axis=1) < 1e-3
    match &= np.max(np.abs(rec[:n, 10] - p4[:n, SLOT["H"]]), axis=1) < 1e-3
    good = structure[:n] & split_ok[:n] & match
    rec, p4 = rec[:n][good], p4[:n][good]
    nominal = np.array([sqrt_s, 0.0, 0.0, 0.0])
    bes = nominal - rec[:, 2] - rec[:, 3]
    isr = rec[:, 6] + rec[:, 7]
    hard = rec[:, 4] + rec[:, 5]
    closure = np.max(np.abs(hard - p4[:, SLOT["zf1"]] - p4[:, SLOT["zf2"]] - p4[:, SLOT["H"]]), axis=1)
    p_ww = p4[:, SLOT["Wp"]] + p4[:, SLOT["Wm"]]
    vec = {"ww": p_ww, "recoil_post": p_ww + bes + isr, "recoil_post_bes": p_ww + bes, "recoil_post_isr": p_ww + isr}
    post_check = np.max(np.abs(vec["recoil_post"] - frame_vectors(p4, sqrt_s)["recoil_post"]), axis=1)
    ang = {f: _angles(frames, v, p4) for f, v in vec.items()}
    keys = ("theta_p", "phi_p", "theta_m", "phi_m")
    ok = np.all([np.isfinite(ang[f][k]) for f in vec for k in keys], axis=0)
    alphas = {}
    out = {"file": str(record_path), "chunk": str(chunk), "n_events": int(n), "n_used": int(ok.sum()),
           "structure_ok": float(structure[:n].mean()), "isr_split_ok": float(split_ok[:n].mean()),
           "matched_to_chunk": float(match.mean()),
           "final_state_minus_spread_beams_GeV_quantiles_50_99_max": np.quantile(conservation[:n][good], [0.5, 0.99, 1.0]),
           "hard_process_closure_max_GeV": float(closure.max()), "recoil_post_check_max_GeV": float(post_check.max()),
           "bes": {"dE_rms": float(np.std(bes[:, 0])), "dpz_rms": float(np.std(bes[:, 3])),
                   "sqrt_s_spread_rms": float(np.std(frames.invariant_mass(rec[:, 2] + rec[:, 3])))},
           "isr": {"E_mean": float(isr[:, 0].mean()), "E_median": float(np.median(isr[:, 0])),
                   "frac_E_gt": {str(t): float(np.mean(isr[:, 0] > t)) for t in kc["isr_energy_thresholds"]},
                   "pt_quantiles_50_90_99": np.quantile(np.hypot(isr[:, 1], isr[:, 2]), [0.5, 0.9, 0.99])},
           "frames": {}}
    x_ref = None
    for f in vec:
        x = basis.estimator_vector(*(np.where(ok, ang[f][k], 0.0)[ok] for k in keys))
        if f == "ww":
            x_ref = x
            out["frames"][f] = {"n": int(ok.sum())}
            continue
        d = tomography.MomentAccumulator().add_vectors(x - x_ref).result()
        chi2, ndf, p = stats.chi_square(d.c, d.cov)
        h44 = basis.COEFF_LABELS.index("h44")
        entry = {"bias_chi2": chi2, "bias_ndf": ndf, "bias_p": p, "dh44": float(d.c[h44]), "dh44_err": float(d.sigma[h44])}
        for leg in ("p", "m"):
            th, ph = ang[f][f"theta_{leg}"][ok], ang[f][f"phi_{leg}"][ok]
            th0, ph0 = ang["ww"][f"theta_{leg}"][ok], ang["ww"][f"phi_{leg}"][ok]
            alphas[f"alpha_{leg}_{f}"] = opening_angle(th, ph, th0, ph0).astype(np.float32)
            entry[f"alpha_{leg}"] = resolution(alphas[f"alpha_{leg}_{f}"], core=None)
            entry[f"dcos_{leg}"] = resolution(np.cos(th) - np.cos(th0), core=True)
        out["frames"][f] = entry
        print(f"record {f}: alpha+ median {entry['alpha_p']['median']:.4f} q68 {entry['alpha_p']['q68']:.4f} "
              f"rms {entry['alpha_p']['rms']:.4f}; dcos+ sigma68 {entry['dcos_p']['sigma68']:.4f} "
              f"core {entry['dcos_p']['core']:.4f}; bias chi2 {chi2:.1f}/{ndf}")
    np.savez(Path(out_dir) / "record_split.npz", bes=bes.astype(np.float32), isr=isr.astype(np.float32), **alphas)
    return out


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------
def trunc_d(an, key):
    """Truncated minus full value of an observable of the spectrum-averaged state (window.json)."""
    return an["truncated"][key] - an["full"][key]


def plot(args):
    import matplotlib.pyplot as plt

    from qtomo import basis, config, plotting
    c = _cfg()
    out = _out_dir(args)
    figdir = Path(c["figure_dir"])
    const = config.constants()
    win = json.loads((out / "window.json").read_text()) if (out / "window.json").exists() else None
    if win:
        h = np.load(out / "window_hist.npz")
        fit = win["fit_heavy_mass"]
        cut = win["ckin45"]
        m_h_gen = fit["m_H_fixed"]
        # --- M* spectrum and the window ---
        fig, (ax, axr) = plt.subplots(2, 1, figsize=(7, 6), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
        se, hl = h["s_edges"], h["h_light"]
        width = np.diff(se)
        cen = 0.5 * (se[1:] + se[:-1])
        f_fit = win["fit_heavy_mass"]["fraction_below_cut_fitted_params"][f"from_{const['mstar_min']:g}"]
        dens_truth = hl / hl.sum() / width * (1 - f_fit)
        xs = np.linspace(const["mstar_min"], m_h_gen / 2 - 1e-3, 600)
        d_fit = light_mass_density(xs, m_h_gen, fit["m_W"], fit["Gamma_W"])
        norm = np.trapezoid(d_fit, xs)
        ax.stairs(dens_truth, se, label=f"winter2023 truth ($M^* \\geq$ {cut:g} GeV), scaled by $1-f$", lw=1.5)
        if "p6_open_hist_light" in h.files:
            ho = h["p6_open_hist_light"]
            ax.stairs(ho / ho.sum() / width, se, ls="--", label="Pythia 6.4.27, CKIN(45) = CKIN(47) = 0.5 GeV")
        ax.plot(xs, d_fit / norm, "k-", lw=1, label=f"tree level, fitted $m_W$, $\\Gamma_W$, $m_H$ = {m_h_gen:g} GeV")
        d_pdg = light_mass_density(xs, const["m_H"], const["m_W"], const["Gamma_W"])
        ax.plot(xs, d_pdg / np.trapezoid(d_pdg, xs), ":", color="grey", label="tree level, PDG constants")
        ax.axvspan(0, cut, color="tab:red", alpha=0.12, label=f"absent from the samples: $f$ = {100 * f_fit:.2f} %")
        ax.set_ylabel("probability density [1/GeV]")
        ax.legend(fontsize=7, loc="upper left")
        plotting.add_label(ax, kind="mc", title=True)
        mu = h["expl_fit"]
        r = np.where(mu > 0, hl / np.where(mu > 0, mu, 1), np.nan)
        axr.errorbar(cen, r, np.where(mu > 0, np.sqrt(np.maximum(hl, 1)) / np.where(mu > 0, mu, 1), np.nan), fmt=".", ms=3)
        axr.axhline(1, color="k", lw=0.8)
        axr.set_ylim(0.95, 1.05)
        axr.set_xlabel("$M^* = \\min(m_{W^+}, m_{W^-})$ [GeV]")
        axr.set_ylabel("truth / fit")
        plotting.save(fig, figdir / "kinematics_wstar_window")
        # --- M fit ---
        fig, (ax, axr) = plt.subplots(2, 1, figsize=(7, 6), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
        me, hh = h["m_edges"], h["h_heavy"]
        mc = 0.5 * (me[1:] + me[:-1])
        ax.stairs(hh, me, label="winter2023 truth", lw=1.5)
        g = fit["goodness"]
        ax.plot(mc, h["exp_fit"], "k-", lw=0.8,
                label=f"fit: $m_W$ = {fit['m_W']:.3f} $\\pm$ {fit['m_W_err']:.3f} GeV, "
                      f"$\\Gamma_W$ = {fit['Gamma_W']:.3f} $\\pm$ {fit['Gamma_W_err']:.3f} GeV "
                      f"($\\chi^2$/ndf = {g['fit']['chi2']:.0f}/{g['fit']['ndf']})")
        ax.plot(mc, h["exp_pdg"], ":", color="tab:red",
                label=f"PDG constants ($\\chi^2$/ndf = {g['pdg']['chi2']:.0f}/{g['pdg']['ndf']})")
        ax.set_yscale("log")
        ax.set_ylim(0.3, None)
        ax.set_ylabel("events / 0.2 GeV")
        ax.legend(fontsize=7, loc="upper left")
        plotting.add_label(ax, kind="mc", title=True)
        for key, sty in (("fit", "k."), ("pdg", "r.")):
            mu = h[f"exp_{key}"]
            k = mu > 20
            axr.plot(mc[k], ((hh - mu) / np.sqrt(mu))[k], sty, ms=2, label=key)
        axr.axhline(0, color="k", lw=0.8)
        axr.set_ylim(-8, 8)
        axr.set_xlabel("$M = \\max(m_{W^+}, m_{W^-})$ [GeV]")
        axr.set_ylabel("(truth - model)/$\\sqrt{model}$")
        plotting.save(fig, figdir / "kinematics_w_mass_fit")
        # --- truncation and the averaged state ---
        an = win["analytic_pdg"]
        scan = [s for s in an["scan"] if s["mstar_min"] <= 30.0]
        cuts = [s["mstar_min"] for s in scan]
        fig = plt.figure(figsize=(13, 7.5))
        gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.38)
        panels = ((gs[0, 0], "i3", "$I_3$ (optimised)"), (gs[0, 1], "c2", "$\\mathcal{C}_2$"),
                  (gs[0, 2], "h44", "$h_{44}$"), (gs[1, 0], "removed", "H $\\to$ WW* removed [%]"))
        for k, (spec, key, lab) in enumerate(panels):
            ax = fig.add_subplot(spec)
            y = [100 * (1 - s["fraction_kept"]) if key == "removed" else s[key] for s in scan]
            ax.plot(cuts, y, "o-", ms=3)
            ax.axvline(cut, color="tab:red", ls="--", lw=1, label=f"Pythia6 window ({cut:g} GeV)")
            ax.set_xlabel("lower cut on $M^*$ [GeV]")
            ax.set_ylabel(lab)
            if k == 0:
                plotting.add_label(ax, kind="mc", title=True)
                ax.legend(fontsize=7, loc="lower right")
                ax.text(0.03, 0.9, "tree-level SM, averaged over\n$M^*$ > cut (PDG constants)",
                        transform=ax.transAxes, fontsize=7, va="top")
        ax = fig.add_subplot(gs[1, 1:])
        dc = np.array(an["delta_c"])
        idx = np.flatnonzero(np.abs(dc) > 1e-12)
        ax.bar(np.arange(len(idx)), dc[idx])
        ax.set_xticks(np.arange(len(idx)))
        ax.set_xticklabels([basis.COEFF_LABELS[i] for i in idx], rotation=90, fontsize=8)
        ax.axhline(0, color="k", lw=0.8)
        ax.set_ylabel(f"$c(M^* \\geq$ {cut:g} GeV) $- c$(full)")
        ax.set_title(f"$\\Delta I_3$ = {trunc_d(an, 'i3'):+.4f}, $\\Delta\\mathcal{{C}}_2$ = {trunc_d(an, 'c2'):+.4f}, "
                     f"$\\Delta h_{{44}}$ = {trunc_d(an, 'h44'):+.5f}", fontsize=8, loc="right")
        plotting.save(fig, figdir / "kinematics_truncation_state")
    if (out / "frames.json").exists():
        fr = json.loads((out / "frames.json").read_text())
        ev = np.load(out / "frames_events.npz")
        colours = {"recorded": "tab:blue", "recoil_pre": "tab:orange", "recoil_post": "tab:green"}
        # --- angle residuals ---
        for ch in ("A", "B"):
            sel = ev["channel"] == ch
            fig, axes = plt.subplots(2, 2, figsize=(11, 7.5))
            spec = ((axes[0, 0], "dcos", "$\\Delta\\cos\\theta_+$ (frame - $W^+W^-$ frame)", (-0.3, 0.3)),
                    (axes[0, 1], "dphi", "$\\Delta\\phi_+$ [rad]", (-np.pi, np.pi)),
                    (axes[1, 0], "dtheta", "$\\Delta\\theta_+$ [rad]", (-0.4, 0.4)),
                    (axes[1, 1], "alpha", "angle between analyser directions, $\\alpha_+$ [rad]", (0, 0.5)))
            for ax, var, lab, rng_ in spec:
                for f in FRAMES[1:]:
                    v = ev[f"{f}_{var}_p"][sel]
                    r = fr["resolution"][f"{ch}/{f}_{var}_p"]
                    width = (f"68 % quantile {r['q68']:.4f}" if var == "alpha" else f"$\\sigma_{{68}}$ {r['sigma68']:.4f}")
                    ax.hist(np.clip(v, *rng_), bins=200, range=rng_, histtype="step", color=colours[f],
                            label=f"{FRAME_LABELS[f]}: RMS {r['rms']:.3f}, {width}")
                ax.set_yscale("log")
                ax.set_xlabel(lab)
                ax.set_ylabel("events / bin")
                ax.legend(fontsize=6)
            axes[0, 1].set_title(f"channel {ch} samples, $\\ell\\nu qq$ ($\\ell$ = e, $\\mu$); overflow in the edge bins",
                                 fontsize=8, loc="right")
            plotting.add_label(axes[0, 0], kind="mc", title=True)
            plotting.save(fig, figdir / f"kinematics_frame_angles_{ch}")
        # --- resolution versus M* ---
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
        for ax, ch in zip(axes, ("A", "B")):
            for f in FRAMES[1:]:
                vb = fr["resolution"][f"{ch}/{f}_alpha_vs_mstar"]
                x = [0.5 * (b["lo"] + b["hi"]) for b in vb]
                ax.errorbar(x, [b["q68"] for b in vb], [b["q68_err"] for b in vb], fmt="o-", ms=3,
                            color=colours[f], label=f"{FRAME_LABELS[f]} (68 % quantile)")
                ax.plot(x, [b["rms"] for b in vb], "s:", ms=3, color=colours[f], label=f"{FRAME_LABELS[f]} (RMS)")
            ax.set_yscale("log")
            ax.set_ylim(3e-3, 0.4)
            ax.set_xlabel("$M^* = \\min(m_{W^+}, m_{W^-})$ [GeV]")
            ax.set_ylabel("analyser direction error $\\alpha$ (both legs) [rad]")
            ax.set_title(f"channel {ch} samples", fontsize=8, loc="right")
        axes[0].text(0.03, 0.04, "recorded H: H not shifted in 80 % of the events\n(68 % quantile below the axis)",
                     transform=axes[0].transAxes, fontsize=7, color=colours["recorded"])
        axes[0].legend(fontsize=6, loc="upper left")
        plotting.add_label(axes[0], kind="mc", title=True)
        plotting.save(fig, figdir / "kinematics_frame_resolution_vs_mstar")
        # --- beam-energy spread versus ISR (EDM4hep record of one mumuH file) ---
        if (out / "record_split.npz").exists() and "record" in fr:
            rs = np.load(out / "record_split.npz")
            rec = fr["record"]
            fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
            fig.subplots_adjust(wspace=0.32)
            axes[0].hist(np.clip(rs["isr"][:, 0], 1e-4, 200), bins=np.logspace(-4, np.log10(200), 120),
                         histtype="step", label="ISR photons, sum of energies")
            axes[0].set_xscale("log")
            axes[0].set_xlabel("$E_\\gamma$(ISR) [GeV]")
            axes[0].set_yscale("log")
            axes[0].set_ylabel("events / bin")
            b = rec["bes"]
            axes[1].hist(-rs["bes"][:, 0], bins=120, range=(-1.5, 1.5), histtype="step",
                         label=f"$\\sqrt{{s'}}$ - 240 GeV (RMS {b['sqrt_s_spread_rms']:.3f} GeV)")
            axes[1].hist(-rs["bes"][:, 3], bins=120, range=(-1.5, 1.5), histtype="step",
                         label=f"$p_z$ of the colliding pair (RMS {b['dpz_rms']:.3f} GeV)")
            axes[1].set_xlabel("beam-energy spread [GeV]")
            axes[1].set_ylabel("events / 0.025 GeV")
            axes[1].legend(fontsize=6)
            for f, col in (("recoil_post", colours["recoil_post"]), ("recoil_post_bes", "tab:purple"),
                           ("recoil_post_isr", "tab:brown")):
                a = rs[f"alpha_p_{f}"]
                e = rec["frames"][f]["alpha_p"]
                axes[2].hist(np.clip(a, 1e-6, 1.0), bins=np.logspace(-6, 0, 120), histtype="step", color=col,
                             label=f"{FRAME_LABELS[f]}: median {e['median'] * 1e3:.1f} mrad, RMS {e['rms'] * 1e3:.0f} mrad")
            axes[2].set_xscale("log")
            axes[2].set_xlabel("analyser direction error $\\alpha_+$ [rad]")
            axes[2].set_ylabel("events / bin")
            axes[2].legend(fontsize=6, loc="upper left")
            axes[2].set_title("wzp6_ee_mumuH_HWW_ecm240, 1 file, all W decays", fontsize=7, loc="right")
            plotting.add_label(axes[0], kind="mc", title=True)
            plotting.save(fig, figdir / "kinematics_frame_isr_bes")
        # --- tomography bias ---
        fig, axes = plt.subplots(2, 1, figsize=(13, 7.5), sharex=True)
        for ax, ch in zip(axes, ("A", "B")):
            sub = fr["subsets"][f"{ch}_lvqq"]
            for off, f in zip((-0.25, 0.0, 0.25), FRAMES[1:]):
                s = sub[f]
                ax.errorbar(np.arange(80) + off, np.array(s["bias_over_sigma_data"]),
                            np.array(s["bias_sigma"]) / np.array(s["sigma_data"]), fmt="o", ms=2, color=colours[f],
                            label=f"{FRAME_LABELS[f]}: $\\Delta I_3$ = {s['di3_fixed_sm13']:+.4f} $\\pm$ {s['di3_fixed_sm13_err']:.4f}, "
                                  f"$\\Delta\\mathcal{{C}}_2$ = {s['dc2_linear']:+.4f} $\\pm$ {s['dc2_err']:.4f}, "
                                  f"$\\Delta h_{{44}}$ = {s['dh44']:+.5f} $\\pm$ {s['dh44_err']:.5f}")
            ax.axhline(0, color="k", lw=0.8)
            ax.set_ylabel("frame shift / $\\sigma_{\\mathrm{stat}}$(10.8 ab$^{-1}$, no selection)")
            ax.set_title(f"channel {ch} samples, $\\ell\\nu qq$ ($\\ell$ = e, $\\mu$), "
                         f"$N_{{data}}$ = {sub['ww']['n_data']:.0f}", fontsize=8, loc="right")
            ax.legend(fontsize=6, loc="lower left")
        axes[1].set_xticks(np.arange(80))
        axes[1].set_xticklabels(basis.COEFF_LABELS, rotation=90, fontsize=6)
        plotting.add_label(axes[0], kind="mc", title=True)
        plotting.save(fig, figdir / "kinematics_frame_bias")
        # --- frame kinematics ---
        fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
        for ch, ls in (("A", "-"), ("B", "--")):
            sel = ev["channel"] == ch
            for f in FRAMES[1:]:
                axes[0].hist(ev[f"{f}_mass"][sel], bins=200, range=(115, 165), histtype="step", ls=ls, color=colours[f],
                             label=f"{FRAME_LABELS[f]}, ch. {ch}")
                axes[1].hist(np.clip(ev[f"{f}_dpz"][sel], -30, 30), bins=240, range=(-30, 30), histtype="step", ls=ls,
                             color=colours[f])
                axes[2].hist(np.clip(np.log10(np.maximum(ev[f"{f}_dpt"][sel], 1e-6)), -6, 2), bins=160, range=(-6, 2),
                             histtype="step", ls=ls, color=colours[f])
        axes[0].set_xlabel("frame invariant mass [GeV]")
        axes[1].set_xlabel("$p_z$(frame) - $p_z(W^+W^-)$ [GeV]")
        axes[2].set_xlabel("$\\log_{10}$($|p_T$(frame) - $p_T(W^+W^-)|$ / GeV)")
        for ax in axes:
            ax.set_yscale("log")
            ax.set_ylabel("events / bin")
        axes[0].legend(fontsize=6)
        plotting.add_label(axes[0], kind="mc", title=True)
        plotting.save(fig, figdir / "kinematics_frame_kinematics")
    print(f"figures in {figdir}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default=None, help="results directory (default <output_dir>/kinematics)")
    sp = ap.add_subparsers(dest="cmd", required=True)
    w = sp.add_parser("window")
    w.add_argument("--max-files", type=int, default=None, help="truth chunks per sample (tests)")
    p = sp.add_parser("pythia6")
    p.add_argument("--n", type=int, default=100000)
    p.add_argument("--tag", required=True)
    p.add_argument("--pygive", nargs="*", default=[])
    f = sp.add_parser("frames")
    f.add_argument("--max-files", type=int, default=None, help="truth chunks per sample (tests)")
    f.add_argument("--workers", type=int, default=4)
    f.add_argument("--record", default=None, help="EDM4hep file of truth chunk_000 of wzp6_ee_mumuH_HWW_ecm240")
    sp.add_parser("plot")
    args = ap.parse_args()
    {"window": window, "pythia6": pythia6, "frames": frames_cmd, "plot": plot}[args.cmd](args)


if __name__ == "__main__":
    main()
