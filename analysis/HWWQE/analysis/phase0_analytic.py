"""Phase 0 analytic validation figures (PLAN.md Sec. 3.4-3.5, Sec. 4).

- I3, C2, entanglement entropy and h44 of the analytic SM state against M* (on-shell
  partner), with the labels of 2302.00683 Figs. 3-4 (masses m_H = 125.0, M_W = 80.4 GeV
  reproduce them; the curves use config/constants.yaml);
- the W* mass spectrum of H -> W W* and the distribution of kappa;
- the asymptotic significance proxies against a lower cut on M* (reach_asymptotic.json).

    python analysis/phase0_analytic.py
"""
import json
from pathlib import Path

import numpy as np

import phase0_common as pc
from qtomo import bell, config, plotting, sm

# 2302.00683 figure labels (Fig. 3: entanglement entropy; Fig. 4: I3 and C2) at M_W* [GeV]
PAPER_I3 = {0: 1.47, 4: 1.67, 8: 1.86, 12: 2.08, 16: 2.27, 20: 2.44, 24: 2.59, 28: 2.71, 32: 2.80, 36: 2.86, 40: 2.89}
PAPER_C2 = {4: 0.039, 8: 0.15, 12: 0.31, 16: 0.51, 20: 0.71, 24: 0.90, 28: 1.1, 32: 1.2, 36: 1.3, 40: 1.3}
PAPER_S = {4: 0.062, 8: 0.19, 12: 0.35, 16: 0.51, 20: 0.66, 24: 0.80, 28: 0.91, 32: 0.99, 36: 1.1, 40: 1.1}


def curves(m_H, m_W, mstar):
    rho = sm.density_matrix(sm.kappa(m_H, m_W, mstar))
    i3 = np.array([bell.i3_optimise(r, n_starts=24) for r in rho])
    return i3, bell.c2(rho), bell.entanglement_entropy(rho), sm.coefficients(sm.kappa(m_H, m_W, mstar))[2][:, 3, 3]


def main():
    import matplotlib.pyplot as plt
    cfg = pc.cfg()
    const = config.constants()
    figdir = Path(cfg["figure_dir"])
    mstar = np.linspace(1.0, const["m_H"] - const["m_W"] - 0.05, 60)
    i3, c2, ent, h44 = curves(const["m_H"], const["m_W"], mstar)
    i3_p, c2_p, ent_p, _ = curves(125.0, 80.4, mstar)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    for ax, ours, theirs, paper, name in ((axes[0], i3, i3_p, PAPER_I3, "$I_3$"),
                                          (axes[1], c2, c2_p, PAPER_C2, r"$\mathcal{C}_2$"),
                                          (axes[2], ent, ent_p, PAPER_S, "entanglement entropy [nats]")):
        ax.plot(mstar, ours, "-", label=f"qtomo, $m_H$ = {const['m_H']}, $m_W$ = {const['m_W']} GeV")
        ax.plot(mstar, theirs, "--", label="qtomo, $m_H$ = 125.0, $m_W$ = 80.4 GeV")
        ax.plot(list(paper), list(paper.values()), "o", ms=4, label="2302.00683 figure labels")
        ax.set_xlabel("$M^* = m_{W^*}$ [GeV]")
        ax.set_ylabel(name)
    axes[0].axhline(2.0, color="k", lw=0.8, ls=":")
    axes[0].axhline(bell.I3_MAX, color="grey", lw=0.8, ls=":")
    axes[0].legend(fontsize=7)
    plotting.add_label(axes[0], title=True)
    plotting.save(fig, figdir / "analytic_sm_vs_mstar")

    spec = pc.spectrum()
    mp, mm = spec.sample(1_000_000, np.random.default_rng(int(cfg["seed"])))
    lo, hi = np.minimum(mp, mm), np.maximum(mp, mm)
    kap = sm.kappa(const["m_H"], mp, mm)
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    axes[0].hist(lo, bins=90, range=(0, 45), histtype="step", density=True)
    axes[0].set_xlabel(r"$M^* = \min(m_{W^+}, m_{W^-})$ [GeV]")
    axes[0].set_ylabel("probability density [1/GeV]")
    axes[1].hist(hi, bins=100, range=(40, 100), histtype="step", density=True)
    axes[1].set_xlabel(r"$M = \max(m_{W^+}, m_{W^-})$ [GeV]")
    axes[1].set_ylabel("probability density [1/GeV]")
    axes[2].hist(np.clip(kap, 1, 10), bins=90, range=(1, 10), histtype="step", density=True)
    axes[2].set_xlabel(r"$\varkappa$ (overflow in last bin)")
    axes[2].set_ylabel("probability density")
    plotting.add_label(axes[0], title=True)
    plotting.save(fig, figdir / "analytic_mass_spectrum")

    path = config.resolve(cfg["output_dir"]) / "reach_asymptotic.json"
    if path.exists():
        scan = json.loads(path.read_text())["mstar_scan"]
        fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
        for i, c in enumerate(cfg["reach"]["categories"]):
            rows = sorted((r for r in scan if r["category"] == c and r["w"] == 0.0), key=lambda r: r["mstar_min"])
            cut = [r["mstar_min"] for r in rows]
            axes[0].plot(cut, [(r["i3"] - 2) / r["sigma_i3"] for r in rows], "o-", ms=3, color=f"C{i}", label=c)
            axes[1].plot(cut, [r["c2"] / r["sigma_c2"] for r in rows], "o-", ms=3, color=f"C{i}")
            axes[2].plot(cut, [r["h44"] / r["sigma_h44"] for r in rows], "o-", ms=3, color=f"C{i}")
        for ax, name in zip(axes, (r"$(I_3 - 2)/\sigma(I_3)$", r"$\mathcal{C}_2/\sigma(\mathcal{C}_2)$",
                                   r"$h_{44}/\sigma(h_{44})$")):
            ax.set_xlabel("lower cut on $M^*$ [GeV]")
            ax.set_ylabel(name + " (asymptotic, $w$ = 0)")
        axes[0].legend(fontsize=7)
        plotting.add_label(axes[0], title=True)
        plotting.save(fig, figdir / "reach_mstar_cut")
    print(f"figures in {figdir}")


if __name__ == "__main__":
    main()
