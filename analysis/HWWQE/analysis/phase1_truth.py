"""Phase 1, PLAN.md Sec. 5.2: truth validation of the central winter2023 H -> WW* signal.

    python analysis/phase1_truth.py submit [--dry-run]   # truth stage1 on HTCondor (winter2023 env)
    python analysis/phase1_truth.py tomography           # truth tomography vs the analytic SM state
    python analysis/phase1_truth.py plot

The truth stage1 (stage1/truth_hww.py) stores the beams, H, W+, W-, the W analysers and
their partners.  Decay angles come from qtomo.frames with the truth four-vectors.  In each
bin of M* = min(m_W+, m_W-) the measured coefficients are compared with the analytic
expectation, the average of rho_SM(kappa_i) over the same events, kappa_i from each event's
truth masses (m_H, m_W+, m_W-) — an exact prediction for that event sample.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import yaml

import batch
from qtomo import basis, bell, config, frames, plotting, sm, stats, tomography

SLOT = {name: i for i, name in enumerate(
    ("beam_em", "beam_ep", "H", "Wp", "Wm", "ana_p", "partner_p", "ana_m", "partner_m", "zf1", "zf2"))}
LEPTONS = {11: "e", 13: "mu", 15: "tau"}


def cfg():
    return config.load("phase1")


def _outdir(c):
    return config.resolve(c["output_dir"]) / "truth"


def submit(args):
    c = cfg()
    samples = config.load("samples")["samples"]
    cmds = []
    for name, s in samples.items():
        if s["role"] != "signal":
            continue
        for i, url in enumerate(s["files"]):
            out = _outdir(c) / name / f"chunk_{i:03d}.root"
            if out.exists():
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            cmds.append(f"fccanalysis run {c['stage1_script']} --files-list {url} --output {out}")
    sub = batch.write_jobs(_outdir(c) / "jobs", cmds, c["batch"], setup=c["stage1_setup"])
    print(f"{len(cmds)} jobs written: {sub}")
    if cmds and not args.dry_run:
        print(batch.submit(sub))


def load_events(c):
    """Truth four-vectors (n, 11, 4) as (E, px, py, pz), PDG codes (n, 11), sample labels."""
    import uproot
    p4s, pdgs, labels = [], [], []
    samples = config.load("samples")["samples"]
    for name, s in samples.items():
        if s["role"] != "signal":
            continue
        for f in sorted((_outdir(c) / name).glob("chunk_*.root")):
            a = uproot.open(f)["events"].arrays(library="np")
            p4 = np.stack([np.stack(a[k]) for k in ("truth_e", "truth_px", "truth_py", "truth_pz")], axis=-1)
            p4s.append(p4.astype(float))
            pdgs.append(np.stack(a["truth_pdg"]).astype(int))
            labels.append(np.full(len(p4), name, dtype=object))
    return np.concatenate(p4s), np.concatenate(pdgs), np.concatenate(labels)


def classify(pdg):
    """Per event: decay class of each W ('e', 'mu', 'tau' or 'had') from its analyser."""
    def leg(code):
        a = np.abs(code)
        out = np.full(code.shape, "had", dtype=object)
        for k, v in LEPTONS.items():
            out[a == k] = v
        out[code == 0] = "none"
        return out
    return leg(pdg[:, SLOT["ana_p"]]), leg(pdg[:, SLOT["ana_m"]])


def compare(ang_sel, kappa_sel, n_starts, rng):
    """Truth tomography of one event set against the per-event analytic expectation."""
    res = tomography.estimate(ang_sel["theta_p"], ang_sel["phi_p"], ang_sel["theta_m"], ang_sel["phi_m"])
    pred = np.mean(basis.pack(*sm.coefficients(kappa_sel)), axis=0)
    resid = res.c - pred
    chi2, ndf, p = stats.chi_square(resid, res.cov)
    rot = basis.subspace("rotation_invariant")
    chi2_r, ndf_r, p_r = stats.chi_square(rot.T @ resid, rot.T @ res.cov @ rot)
    # components outside the rotation-invariant subspace must vanish for any spin-0 parent
    out_proj = np.eye(80) - rot @ rot.T
    chi2_o, ndf_o, p_o = stats.chi_square(out_proj @ resid, out_proj @ res.cov @ out_proj)
    rho_pred = basis.density_matrix_from_vector(pred)
    ref = bell.i3_optimise(rho_pred, n_starts=n_starts, full_output=True)
    obs = bell.observables(res.rho, n_starts=n_starts, rng=rng, x0=ref)
    g = bell.i3_weights(ref.u, ref.v)
    inv = res.invariants
    h44 = basis.COEFF_LABELS.index("h44")
    return {"n_events": int(res.n_events), "chi2": chi2, "ndf": ndf, "p": p,
            "chi2_rot": chi2_r, "ndf_rot": ndf_r, "p_rot": p_r,
            "chi2_nonrot": chi2_o, "ndf_nonrot": ndf_o, "p_nonrot": p_o,
            "max_abs_pull": float(np.max(np.abs(resid) / res.sigma)),
            "i3_pred": ref.value, "i3_fixed_settings": float(g @ res.c),
            "i3_fixed_settings_err": float(np.sqrt(g @ res.cov @ g)),
            "i3_raw": obs["i3"], "i3_physical": obs["i3_physical"],
            "c2_pred": float(bell.c2(rho_pred)),
            "c2_unbiased": 2.0 * max(inv.c2_arg_wplus, inv.c2_arg_wminus),
            "c2_unbiased_err": 2.0 * max(res.invariants_sigma.c2_arg_wplus, res.invariants_sigma.c2_arg_wminus),
            "h44_pred": float(pred[h44]), "h44": float(res.c[h44]), "h44_err": float(res.sigma[h44]),
            "c": res.c.tolist(), "sigma": res.sigma.tolist(), "c_pred": pred.tolist()}


def tomography_cmd(args):
    c = cfg()
    const = config.constants()
    p4, pdg, label = load_events(c)
    n_all = len(p4)
    ok = np.all(pdg[:, [SLOT["H"], SLOT["Wp"], SLOT["Wm"], SLOT["ana_p"], SLOT["ana_m"], SLOT["beam_ep"]]] != 0, axis=1)
    p4, pdg, label = p4[ok], pdg[ok], label[ok]
    # H frame: rest frame of W+ + W-.  The recorded H is Pythia6's documentation copy with
    # the Whizard momentum; the decaying copy was shifted by the shower recoil (Z -> qq quarks,
    # photons off Z -> ll), so the recorded H differs from W+ + W- in 20 % (Z -> mumu) to 99 %
    # (Z -> qq) of the events.  ``--higgs recorded`` keeps it for comparison.
    p_h = p4[:, SLOT["Wp"]] + p4[:, SLOT["Wm"]] if args.higgs == "ww" else p4[:, SLOT["H"]]
    ang = frames.decay_angles(p_h, p4[:, SLOT["Wp"]], p4[:, SLOT["Wm"]],
                              p4[:, SLOT["ana_p"]], p4[:, SLOT["ana_m"]], p4[:, SLOT["beam_ep"]])
    m_h = frames.invariant_mass(p_h)
    kappa = sm.kappa(m_h, ang["m_Wp"], ang["m_Wm"])
    mstar = np.minimum(ang["m_Wp"], ang["m_Wm"])
    leg_p, leg_m = classify(pdg)
    lep_p, lep_m = np.isin(leg_p, ["e", "mu"]), np.isin(leg_m, ["e", "mu"])
    is_lvqq = (lep_p & (leg_m == "had")) | (lep_m & (leg_p == "had"))
    is_A = np.isin(label, ["wzp6_ee_mumuH_HWW_ecm240", "wzp6_ee_eeH_HWW_ecm240"])
    good = np.isfinite(ang["theta_p"]) & np.isfinite(ang["theta_m"]) & np.isfinite(kappa)
    rng = np.random.default_rng(20261015)
    sets = {"lvqq_emu": is_lvqq, "lvqq_emu_channelA_samples": is_lvqq & is_A,
            "lvqq_emu_channelB_samples": is_lvqq & ~is_A, "all_decays": np.ones(len(p4), bool)}
    bins = np.array(c["mstar_bins"])
    results = {"n_events_read": int(n_all), "n_events_complete": int(ok.sum()),
               "n_events_bad_angles": int((~good).sum()),
               "fraction_lvqq_emu": float(is_lvqq.mean()), "sets": {}}
    for name, sel0 in sets.items():
        sel0 = sel0 & good
        if sel0.sum() < 1000:
            print(f"{name}: {int(sel0.sum())} events, skipped")
            continue
        out = {"inclusive": compare({k: v[sel0] for k, v in ang.items()}, kappa[sel0], c["i3_n_starts"], rng)}
        for lo, hi in zip(bins[:-1], bins[1:]):
            sel = sel0 & (mstar >= lo) & (mstar < hi)
            if sel.sum() > 1000:
                out[f"{lo:g}-{hi:g}"] = compare({k: v[sel] for k, v in ang.items()}, kappa[sel], c["i3_n_starts"], rng)
        results["sets"][name] = out
        inc = out["inclusive"]
        print(f"{name:28s} N = {inc['n_events']:8d}  chi2/ndf = {inc['chi2']:.1f}/{inc['ndf']} (p = {inc['p']:.3g}); "
              f"rot {inc['chi2_rot']:.1f}/{inc['ndf_rot']} (p = {inc['p_rot']:.3g}); "
              f"I3 pred {inc['i3_pred']:.4f} fixed-setting {inc['i3_fixed_settings']:.4f} +- {inc['i3_fixed_settings_err']:.4f}")
    # kinematic sanity checks on the generator record
    beam = p4[:, SLOT["beam_ep"]]
    results["checks"] = {
        "beam_ep_direction_mean": (beam[:, 1:] / np.linalg.norm(beam[:, 1:], axis=1)[:, None]).mean(axis=0).tolist(),
        "beam_ep_max_transverse_GeV": float(np.max(np.hypot(beam[:, 1], beam[:, 2]))),
        "m_H_mean": float(np.mean(m_h)), "m_H_std": float(np.std(m_h)),
        "cos_Theta_mean": float(np.mean(ang["cos_Theta"][good])),
        "cos_Theta_second_moment": float(np.mean(ang["cos_Theta"][good] ** 2)),
        "mstar_quantiles": np.quantile(mstar[good], [0.1, 0.5, 0.9]).tolist(),
        "mheavy_median": float(np.median(np.maximum(ang["m_Wp"], ang["m_Wm"])[good])),
        "frac_wplus_offshell": float(np.mean(ang["wplus_offshell"][good])),
        "decay_classes": {f"{a}/{b}": int(np.sum((leg_p == a) & (leg_m == b)))
                          for a in ("e", "mu", "tau", "had") for b in ("e", "mu", "tau", "had")},
    }
    results["higgs_frame"] = args.higgs
    suffix = "" if args.higgs == "ww" else "_recorded_higgs"
    path = config.resolve(c["output_dir"]) / f"truth_tomography{suffix}.json"
    path.write_text(json.dumps(results, indent=1))
    if args.higgs != "ww":
        print(f"wrote {path}")
        return
    np.savez(config.resolve(c["output_dir"]) / "truth_kinematics.npz", mstar=mstar[good],
             mheavy=np.maximum(ang["m_Wp"], ang["m_Wm"])[good], cos_theta=ang["cos_Theta"][good],
             lvqq=is_lvqq[good], m_h=m_h[good])
    print(f"wrote {path}")


def plot(args):
    import matplotlib.pyplot as plt
    c = cfg()
    res = json.loads((config.resolve(c["output_dir"]) / "truth_tomography.json").read_text())
    figdir = Path(c["figure_dir"])
    sel = res["sets"]["lvqq_emu"]
    bins = [k for k in sel if k != "inclusive"]
    centres = [np.mean([float(x) for x in b.split("-")]) for b in bins]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    for ax, (pred, meas, err, name) in zip(axes, (
            ("i3_pred", "i3_fixed_settings", "i3_fixed_settings_err", "$I_3$ (fixed optimal settings)"),
            ("c2_pred", "c2_unbiased", "c2_unbiased_err", r"$\mathcal{C}_2$ (unbiased)"),
            ("h44_pred", "h44", "h44_err", "$h_{44}$"))):
        ax.plot(centres, [sel[b][pred] for b in bins], "s", mfc="none", label="analytic SM (per-event $\\varkappa$)")
        ax.errorbar(centres, [sel[b][meas] for b in bins], [sel[b][err] for b in bins], fmt="o", ms=4,
                    label="winter2023 truth")
        ax.set_xlabel("$M^* = \\min(m_{W^+}, m_{W^-})$ [GeV]")
        ax.set_ylabel(name)
    axes[0].legend(fontsize=7)
    plotting.add_label(axes[0], kind="mc", title=True)
    plotting.save(fig, figdir / "truth_observables_vs_mstar")

    inc = sel["inclusive"]
    c_meas, c_err, c_pred = (np.array(inc[k]) for k in ("c", "sigma", "c_pred"))
    fig, ax = plt.subplots(figsize=(13, 3.8))
    ax.errorbar(np.arange(80), (c_meas - c_pred) / c_err, np.ones(80), fmt="o", ms=3)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(np.arange(80))
    ax.set_xticklabels(basis.COEFF_LABELS, rotation=90, fontsize=6)
    ax.set_ylabel("(truth - analytic) / $\\sigma$")
    plotting.add_label(ax, kind="mc", title=True)
    plotting.save(fig, figdir / "truth_coefficient_pulls")

    kin = np.load(config.resolve(c["output_dir"]) / "truth_kinematics.npz")
    spec = sm.OffShellSpectrum.from_config(config.constants())
    mp, mm = spec.sample(2_000_000, np.random.default_rng(1))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, data, model, rng_, xl in ((axes[0], kin["mstar"], np.minimum(mp, mm), (0, 46), "$M^*$ [GeV]"),
                                      (axes[1], kin["mheavy"], np.maximum(mp, mm), (60, 100), "$M$ [GeV]")):
        ax.hist(data, bins=92, range=rng_, density=True, histtype="step", label="winter2023 truth")
        ax.hist(model, bins=92, range=rng_, density=True, histtype="step", label="tree-level double Breit-Wigner (PDG)")
        ax.set_xlabel(xl)
        ax.set_ylabel("probability density [1/GeV]")
    axes[0].legend(fontsize=7)
    plotting.add_label(axes[0], kind="mc", title=True)
    plotting.save(fig, figdir / "truth_w_masses")
    print(f"figures in {figdir}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("submit")
    s.add_argument("--dry-run", action="store_true")
    t = sp.add_parser("tomography")
    t.add_argument("--higgs", choices=("ww", "recorded"), default="ww",
                   help="H frame: W+ + W- (default) or the recorded H four-vector (diagnostic)")
    sp.add_parser("plot")
    args = ap.parse_args()
    {"submit": submit, "tomography": tomography_cmd, "plot": plot}[args.cmd](args)


if __name__ == "__main__":
    main()
