"""GATE 1 figures for channel A (Z -> ee/mumu, H -> l nu q q), from the stored Phase 1 outputs.

    python analysis/phase1_figures.py

Reads outputs/phase1/truth_tomography.json (event set 'lvqq_emu_channelA_samples', H frame =
W+ W- rest frame) and outputs/phase1/truth_kinematics.npz (W masses of all six winter2023 signal
samples; the W line shape does not depend on the Z decay), and writes to config/phase1.yaml
'figure_dir':
  truth_channelA_vs_mstar      chi2 p-values, C2 (unbiased) and h44 per M* bin vs the analytic state
  truth_channelA_pulls         pulls of the 80 coefficients (inclusive in M*)
  truth_w_masses_generator     W mass spectra vs the generator line shape (config 'generator') and PDG
"""
import json
from pathlib import Path

import numpy as np

import batch  # noqa: F401  (puts the analysis root on sys.path)
from qtomo import basis, config, plotting, sm

SET = "lvqq_emu_channelA_samples"


def main():
    import matplotlib.pyplot as plt
    c = config.load("phase1")
    out = config.resolve(c["output_dir"])
    figdir = Path(c["figure_dir"])
    res = json.loads((out / "truth_tomography.json").read_text())["sets"][SET]
    bins = [b for b in res if b != "inclusive"]
    lo_hi = [tuple(float(x) for x in b.split("-")) for b in bins]
    centre = np.array([0.5 * (max(lo, 12.0) + hi) for lo, hi in lo_hi])   # no events below 12 GeV
    half = np.array([0.5 * (hi - max(lo, 12.0)) for lo, hi in lo_hi])

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    axes[0].errorbar(centre, [res[b]["p"] for b in bins], xerr=half, fmt="o", ms=4, label="80 coefficients")
    axes[0].errorbar(centre, [res[b]["p_rot"] for b in bins], xerr=half, fmt="s", ms=4, mfc="none",
                     label="18 rotation-invariant combinations")
    axes[0].axhline(c["p_value_threshold"], color="k", ls=":", lw=0.8)
    axes[0].set_yscale("log")
    axes[0].set_ylim(1e-4, 1.5)
    axes[0].set_ylabel("$\\chi^2$ p-value (truth vs analytic SM)")
    axes[0].legend(fontsize=7, loc="lower left")
    for ax, (pred, meas, err, name) in zip(axes[1:], (("c2_pred", "c2_unbiased", "c2_unbiased_err", "$\\mathcal{C}_2$ (unbiased)"),
                                                      ("h44_pred", "h44", "h44_err", "$h_{44}$"))):
        ax.errorbar(centre, [res[b][pred] for b in bins], xerr=half, fmt="s", ms=5, mfc="none",
                    label="analytic SM (each event's $\\varkappa$)")
        ax.errorbar(centre, [res[b][meas] for b in bins], [res[b][err] for b in bins], fmt="o", ms=4,
                    label="winter2023 truth")
        ax.set_ylabel(name)
    axes[1].legend(fontsize=7)
    for ax in axes:
        ax.set_xlabel("$M^* = \\min(m_{W^+}, m_{W^-})$ [GeV]")
    plotting.add_label(axes[0], kind="mc", title=True)
    plotting.save(fig, figdir / "truth_channelA_vs_mstar")

    inc = res["inclusive"]
    pulls = (np.array(inc["c"]) - np.array(inc["c_pred"])) / np.array(inc["sigma"])
    fig, ax = plt.subplots(figsize=(13, 3.8))
    ax.errorbar(np.arange(80), pulls, np.ones(80), fmt="o", ms=3)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xticks(np.arange(80))
    ax.set_xticklabels(basis.COEFF_LABELS, rotation=90, fontsize=6)
    ax.set_ylabel("(truth $-$ analytic) / $\\sigma$")
    ax.set_title(f"channel A, $\\ell\\nu qq$ ($\\ell$ = e, $\\mu$): {inc['n_events']} events, "
                 f"$\\chi^2$/ndf = {inc['chi2']:.1f}/{inc['ndf']} (p = {inc['p']:.2f})", fontsize=8, loc="right")
    plotting.add_label(ax, kind="mc", title=True)
    plotting.save(fig, figdir / "truth_channelA_pulls")

    kin = np.load(out / "truth_kinematics.npz")
    gen, const = c["generator"], config.constants()
    lo_w, hi_w = gen["w_mass_window"]
    rng = np.random.default_rng(1)
    gen_spec = sm.OffShellSpectrum(gen["m_H"], gen["m_W"], gen["Gamma_W"], lo_w)
    pdg_spec = sm.OffShellSpectrum.from_config(const)
    models = [(gen_spec.sample(2_000_000, rng), "tree level, generator $m_W$, $\\Gamma_W$, $M^* \\geq$ 12 GeV", "-"),
              (pdg_spec.sample(2_000_000, rng), "tree level, PDG $m_W$, $\\Gamma_W$ (reference)", ":")]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, data, pick, rng_, xl in ((axes[0], kin["mstar"], np.minimum, (0, 46), "$M^*$ [GeV]"),
                                     (axes[1], kin["mheavy"], np.maximum, (70, 90), "$M$ [GeV]")):
        ax.hist(data, bins=92, range=rng_, density=True, histtype="step", lw=1.5, label="winter2023 truth (5.3M events)")
        for (mp, mm), lab, ls in models:
            ax.hist(pick(mp, mm), bins=92, range=rng_, density=True, histtype="step", ls=ls, label=lab)
        ax.set_xlabel(xl)
        ax.set_ylabel("probability density [1/GeV]")
    axes[0].legend(fontsize=7, loc="upper left")
    plotting.add_label(axes[0], kind="mc", title=True)
    plotting.save(fig, figdir / "truth_w_masses_generator")
    print(f"figures in {figdir}")


if __name__ == "__main__":
    main()
