#!/usr/bin/env python3
"""
plot_bib_truth.py - what makes the vertex-barrel background hits, layer by layer.

From the BIB truth ntuple (merge_bib_truth_ntuple.py) makes, with explicit axes:
  hits_per_layer_by_origin   SimTrackerHits per BX and layer, split by what made the hit
  pt_spectrum_L3_L4          local pT of the hit-making track vs the pT needed to
                             reach the layer from the beam line (2 T field)
  hits_vs_ptcut              hits per BX above a pT cut, L3 vs L4 (the pT-cut answer)
  helix_prediction_vs_sim    primaries reaching each layer: helix calculation vs sim
  ratio_summary              L4/L3 under different ways of counting and selecting
  density_vs_radius          hits/cm^2/BX vs layer radius, charged vs soft component
  density_vs_z_L3_L4         hits/cm^2/BX along z by origin
  time_L3_L4, edep_L3_L4     hit time and deposited energy by origin
  occupancy_per_layer        true pixel occupancy per BX (fired pixels / all pixels)
and summary_numbers.md with the tables behind them.

  python3 plot_bib_truth.py TRUTH_vertex.root [--full TRUTH.root] [--outdir outputs/BIB/plots_LCC_truth]
"""
import argparse
from pathlib import Path

import numpy as np

BFIELD_T = 2.0
KAPPA = 0.299792458 * BFIELD_T               # pT[MeV] = KAPPA * R[mm]
BX_SPACING_NS = 1e3 / 37.04                  # LCC V106 @ Z: 37.04 MHz
# layer: (mean hit radius_mm, sensitive half_length_mm, n_sensors, sensor sensitive
#         area cm^2, pixels per sensor at the sample's own segmentation)
GEO = {0: (13.91, 96.5, 90, 0.64 * 3.2, 256 * 1280),     # 6.4 x 32 mm, 25 um
       1: (24.16, 160.9, 240, 0.64 * 3.2, 256 * 1280),
       2: (34.84, 241.4, 540, 0.64 * 3.2, 256 * 1280),
       3: (131.33, 162.7, 736, 1.86 * 1.98, 372 * 132),  # 18.6 x 19.8 mm, 50 x 150 um
       4: (316.04, 325.9, 3264, 1.86 * 1.98, 372 * 132)}
MAPS_PIXELS = 930 * 990                      # 20 um MAPS pitch on the same sensor
REACH = {L: KAPPA * g[0] / 2 for L, g in GEO.items()}    # min pT [MeV] from the beam line
SIWR_QUADS = (83 * 262, 83 * 262, 84 * 262, 84 * 262)    # Si-wrapper barrel layers: staves x quad modules
SIWR_QUAD_CM2 = 14.95                        # sensitive area of one quad
SIWR_R_MM = 2063.0

INK, INK2, MUTED, GRID, AXIS, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
CLASSES = [("primary e± (GuineaPig) itself", "#2a78d6"),
           ("stored secondary (created > 1 MeV)", "#eb6834"),
           ("sub-MeV secondary electron", "#1baf7a")]
C_L3, C_L4 = "#4a3aa7", "#e34948"
SAMPLE = "IPC @ Z, LCC V106.2, central mdi_v2 simulation, 19,673 bunch crossings · SimTrackerHits (1 keV simulation cut)"
HITS = "SimTrackerHits per bunch crossing"


def rname(L):
    r = GEO[L][0]
    return f"{r:.0f} mm" if r > 100 else f"{r:.1f} mm"


def setup(plt):
    plt.rcParams.update({
        "font.family": "sans-serif", "font.size": 10.5, "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE, "axes.edgecolor": AXIS,
        "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": MUTED,
        "xtick.labelcolor": INK2, "ytick.labelcolor": INK2, "axes.linewidth": 0.8,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
        "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
        "lines.linewidth": 2.0, "lines.solid_capstyle": "round"})


def titles(fig, title, sub=SAMPLE, top=0.86):
    fig.text(0.012, 0.975, title, ha="left", va="top", color=INK, fontsize=12.5, fontweight="semibold")
    fig.text(0.012, 0.975 - 0.062 * 4.6 / fig.get_figheight(), sub, ha="left", va="top", color=MUTED, fontsize=8.5)
    fig.subplots_adjust(top=top)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ntuple", help="vertex-only (or whole-tracker) truth ntuple, merged with --pixesl-csv")
    ap.add_argument("--full", default=None, help="whole-tracker ntuple: adds the Si-wrapper point to density_vs_radius")
    ap.add_argument("--outdir", default="outputs/BIB/plots_LCC_truth", help="directory for the png/pdf files and summary_numbers.md")
    args = ap.parse_args(argv)

    import uproot, matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    setup(plt)
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    def save(fig, name):
        for ext in ("png", "pdf"):
            fig.savefig(out / f"{name}.{ext}", dpi=170)
        plt.close(fig)
        print(f"[plot] {out / name}.png")

    f = uproot.open(args.ntuple)
    bxt = f["bx"].arrays(["bx"] + [f"pred_first_L{L}" for L in GEO], library="np")
    NBX = len(bxt["bx"])
    h = f["hits"].arrays(["bx", "det", "layer", "module", "sensor", "ix", "iy", "x", "y", "z", "t", "edep",
                          "pt", "p", "by_secondary", "mc_gen_status", "prim_pt", "col20", "row20"],
                         cut="det==0", library="np")
    ibx = np.searchsorted(bxt["bx"], h["bx"])
    cls = np.where(h["by_secondary"] == 1, 2, np.where(h["mc_gen_status"] == 1, 0, 1))
    lay = h["layer"]
    md = [f"# Vertex-barrel background hits by origin - {SAMPLE}", "",
          "Errors are BX-to-BX standard errors (bursts included); ratios use a bootstrap over the 19,673 BXs.", ""]
    rng = np.random.default_rng(7)
    boot = rng.integers(0, NBX, size=(500, NBX))

    def cnt(mask):
        return np.bincount(ibx[mask], minlength=NBX)

    def rate(mask):
        """mean per BX and its standard error (BX-to-BX fluctuations, bursts included)"""
        c = cnt(mask)
        return c.mean(), c.std(ddof=1) / np.sqrt(NBX)

    def ratio(c4, c3):
        """L4/L3 of two per-BX count arrays, with its bootstrap error"""
        r = c4[boot].sum(axis=1) / np.maximum(c3[boot].sum(axis=1), 1)
        return c4.sum() / max(c3.sum(), 1), r.std()

    def ratio_of(sel):
        return ratio(cnt((lay == 4) & sel), cnt((lay == 3) & sel))

    # ---- hits per BX by origin ---------------------------------------------
    area = {L: g[2] * g[3] for L, g in GEO.items()}
    md += ["## SimTrackerHits per BX by what made the hit", "",
           "| layer | r [mm] | all | primary itself | stored secondary | sub-MeV secondary | sub-MeV fraction | sensitive area [cm2] | all /cm2/BX | sub-MeV /cm2/BX | charged-track /cm2/BX |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    tab = {}
    for L in GEO:
        s = lay == L
        tot, etot = rate(s)
        parts = [rate(s & (cls == c)) for c in range(3)]
        tab[L] = (tot, etot, parts)
        md.append(f"| L{L} | {GEO[L][0]} | {tot:.4f} ± {etot:.4f} | " + " | ".join(f"{v:.4f} ± {e:.4f}" for v, e in parts)
                  + f" | {parts[2][0] / tot * 100:.1f}% | {area[L]:.0f} | {tot / area[L]:.3e} | {parts[2][0] / area[L]:.3e} | {(tot - parts[2][0]) / area[L]:.3e} |")

    fig, axs = plt.subplots(1, 2, figsize=(9.2, 4.6), gridspec_kw={"width_ratios": [3, 2], "wspace": 0.28})
    for ax, layers in zip(axs, ([0, 1, 2], [3, 4])):
        bottom = np.zeros(len(layers))
        for c, (label, colour) in enumerate(CLASSES):
            v = np.array([tab[L][2][c][0] for L in layers])
            ax.bar(range(len(layers)), v, 0.42, bottom=bottom, color=colour, edgecolor=SURFACE, linewidth=1.2,
                   label=label)
            bottom += v
        for i, L in enumerate(layers):
            ax.text(i, bottom[i] * 1.015, f"{tab[L][0]:.3g}", ha="center", va="bottom", color=INK, fontsize=10)
        ax.set_xticks(range(len(layers)))
        ax.set_xticklabels([f"L{L}\nr = {rname(L)}" for L in layers])
        ax.set_xlim(-0.6, len(layers) - 0.4)
        ax.set_ylim(0, bottom.max() * 1.13)
        ax.grid(axis="x", visible=False)
    axs[0].set_ylabel(HITS + " (whole layer)")
    axs[0].set_title("inner barrel", loc="left", color=INK2, fontsize=10)
    axs[1].set_title("outer barrel (MAPS layers), own scale", loc="left", color=INK2, fontsize=10)
    axs[0].legend(loc="upper right", title="hit made by", fontsize=9, title_fontsize=9)
    titles(fig, "Layer 4 beats layer 3 only through sub-MeV secondary electrons", top=0.80)
    save(fig, "hits_per_layer_by_origin")

    # ---- pT spectrum on L3 / L4 --------------------------------------------
    edges = np.logspace(-2, 3, 51)
    fig, axs = plt.subplots(1, 2, figsize=(9.8, 4.6), sharey=True, gridspec_kw={"wspace": 0.14})
    for ax, L in zip(axs, (3, 4)):
        s = lay == L
        bottom = np.zeros(len(edges) - 1)
        for c, (label, colour) in enumerate(CLASSES):
            v = np.histogram(h["pt"][s & (cls == c)], bins=edges)[0] / NBX
            ax.stairs(bottom + v, edges, baseline=bottom, fill=True, color=colour, label=label,
                      edgecolor=SURFACE, linewidth=0.4)
            bottom += v
        ax.axvline(REACH[L], color=INK, lw=1.0)
        ax.text(REACH[L] * 0.82, 0.97, f"p$_T$ needed to reach L{L}\nfrom the beam line:\n{REACH[L]:.0f} MeV",
                transform=ax.get_xaxis_transform(), ha="right", va="top", color=INK2, fontsize=8.5)
        below = (h["pt"][s] < REACH[L]).mean()
        ax.set_title(f"L{L} (r = {rname(L)}): {below * 100:.0f}% of hits below the threshold",
                     loc="left", color=INK2, fontsize=10)
        ax.set_xscale("log")
        ax.set_xlim(edges[0], edges[-1])
        ax.set_xlabel("p$_T$ of the track at the hit [MeV]")
    axs[0].set_ylabel(HITS + " per bin\n(10 bins per decade)")
    axs[1].legend(loc="upper right", fontsize=8.5, bbox_to_anchor=(1.0, 0.72))
    titles(fig, "Most outer-barrel hits come from tracks too soft to have arrived from the beam line", top=0.80)
    save(fig, "pt_spectrum_L3_L4")

    # ---- hits per BX above a pT cut ----------------------------------------
    md += ["", "## SimTrackerHits per BX above a cut on the local pT of the track that made the hit", "",
           "(the stored hit momentum is the mean of entry and exit: half the entry value for a track that stops in the sensor)", "",
           "| pT cut [MeV] | L0 | L1 | L2 | L3 | L4 | L4/L3 |", "|---|---|---|---|---|---|---|"]
    for cut in (0.0, 0.1, 1.0, 10.0, REACH[3], REACH[4]):
        r = [rate((lay == L) & (h["pt"] >= cut)) for L in GEO]
        v, e = ratio_of(h["pt"] >= cut)
        md.append(f"| {cut:.4g} | " + " | ".join(f"{a:.4f} ± {b:.4f}" for a, b in r) + f" | {v:.2f} ± {e:.2f} |")
    own = [rate((lay == L) & (h["pt"] >= REACH[L])) for L in (3, 4)]
    v, e = ratio(cnt((lay == 4) & (h["pt"] >= REACH[4])), cnt((lay == 3) & (h["pt"] >= REACH[3])))
    md.append(f"| each layer's own reach threshold ({REACH[3]:.1f} / {REACH[4]:.1f}) | | | | {own[0][0]:.4f} ± {own[0][1]:.4f} | "
              f"{own[1][0]:.4f} ± {own[1][1]:.4f} | {v:.2f} ± {e:.2f} |")
    md += ["", "## Same, with the cut on the pT of the GuineaPig primary at the root of the hit (a generator-level cut)", "",
           "| primary pT cut [MeV] | L3 | L4 | L4/L3 |", "|---|---|---|---|"]
    for cut in (0.0, 1.0, 5.0, 10.0, 20.0, REACH[3]):
        r3, r4 = rate((lay == 3) & (h["prim_pt"] >= cut)), rate((lay == 4) & (h["prim_pt"] >= cut))
        v, e = ratio_of(h["prim_pt"] >= cut)
        md.append(f"| {cut:.4g} | {r3[0]:.4f} ± {r3[1]:.4f} | {r4[0]:.4f} ± {r4[1]:.4f} | {v:.2f} ± {e:.2f} |")

    cuts = np.logspace(-2, 3, 201)
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    for L, colour in ((3, C_L3), (4, C_L4)):
        pts = np.sort(h["pt"][lay == L])
        y = (len(pts) - np.searchsorted(pts, cuts, side="left")) / NBX
        ax.plot(cuts, y, color=colour, label=f"L{L} (r = {rname(L)})")
        ax.text(cuts[0] * 1.15, y[0] * 1.12, f"L{L}: {len(pts) / NBX:.3f} with no cut", color=INK, fontsize=9, va="bottom")
        y1 = (pts >= 1.0).sum() / NBX
        ax.plot([1.0], [y1], "o", ms=7, color=colour, markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=5)
        ax.annotate(f"L{L}: {y1:.3f}", (1.0, y1), color=INK, fontsize=9, xytext=(8, 5), textcoords="offset points")
        ax.axvline(REACH[L], color=colour, lw=0.9, ymax=0.42)
        ax.text(REACH[L] * (0.90 if L == 3 else 1.10), 2.4e-3, f"reach\nL{L}", color=INK2, fontsize=8,
                ha="right" if L == 3 else "left", va="bottom")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(cuts[0], cuts[-1])
    ax.set_ylim(2e-3, 1.5)
    ax.set_xlabel("minimum p$_T$ of the track at the hit [MeV]")
    ax.set_ylabel(HITS + " above the cut")
    ax.legend(loc="upper right")
    titles(fig, "A 1 MeV p$_T$ cut puts layer 3 four times above layer 4", top=0.82)
    save(fig, "hits_vs_ptcut")

    # ---- helix prediction vs simulation ------------------------------------
    p = f["particles"].arrays(["gen_status"] + [f"pred_first_L{L}" for L in GEO] + [f"n_direct_vb_L{L}" for L in GEO],
                              library="np")
    prim = p["gen_status"] == 1
    md += ["", "## Primaries reaching each layer: ideal helix (2 T, vacuum, from the GuineaPig start point) vs simulation", "",
           "| layer | pT to reach it from the beam line [MeV] | predicted primaries/BX (first arc inside the layer length) | sim primaries with a direct hit /BX | predicted primaries with a direct hit | found | sim direct hits by primaries /BX | hits per primary | all sim hits /BX |",
           "|---|---|---|---|---|---|---|---|---|"]
    pred, seen = [], []
    for L in GEO:
        a, b = prim & (p[f"pred_first_L{L}"] == 1), prim & (p[f"n_direct_vb_L{L}"] > 0)
        nh = p[f"n_direct_vb_L{L}"][prim].sum()
        npred = int(bxt[f"pred_first_L{L}"].sum())      # all predicted primaries (the tree keeps only some without hits)
        pred.append(npred / NBX)
        seen.append(b.sum() / NBX)
        md.append(f"| L{L} | {REACH[L]:.1f} | {pred[-1]:.4f} | {seen[-1]:.4f} | {(a & b).sum()} of {npred} | "
                  f"{(a & b).sum() / max(npred, 1) * 100:.0f}% | {nh / NBX:.4f} | {nh / max(b.sum(), 1):.2f} | {tab[L][0]:.4f} |")
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    x = np.arange(len(GEO))
    ax.plot(x - 0.08, pred, "o", ms=9, color="#2a78d6", markeredgecolor=SURFACE, markeredgewidth=1.5,
            label="helix calculation: primaries whose first arc crosses the layer")
    ax.plot(x + 0.08, seen, "s", ms=8, color="#eb6834", markeredgecolor=SURFACE, markeredgewidth=1.5,
            label="simulation: primaries with a direct hit on the layer")
    ax.plot(x, [tab[L][0] for L in GEO], "_", ms=22, mew=2.0, color=INK2, label="simulation: all hits on the layer")
    for L in (3, 4):
        ax.annotate(f"{pred[L]:.4f}", (L - 0.08, pred[L]), xytext=(-8, -3), textcoords="offset points", ha="right",
                    va="top", color=INK, fontsize=9)
        ax.annotate(f"{tab[L][0]:.3f}", (L, tab[L][0]), xytext=(0, 7), textcoords="offset points", ha="center",
                    color=INK, fontsize=9)
    ax.set_yscale("log")
    ax.set_ylim(1.5e-3, 80)
    ax.set_xticks(x)
    ax.set_xticklabels([f"L{L}\n{rname(L)}\np$_T$ > {REACH[L]:.0f} MeV" for L in GEO])
    ax.grid(axis="x", visible=False)
    ax.set_ylabel("per bunch crossing")
    ax.legend(loc="lower left", fontsize=8.5)
    titles(fig, "Field + geometry predict how many primaries reach each layer", top=0.82)
    fig.subplots_adjust(bottom=0.19)
    save(fig, "helix_prediction_vs_sim")

    # ---- L4/L3 under different ways of counting ----------------------------
    def unique_pixels(L, sel):
        s = (lay == L) & sel
        u = np.unique(np.stack([ibx[s], h["module"][s], h["sensor"][s], h["col20"][s], h["row20"][s]]), axis=1)
        return np.bincount(u[0], minlength=NBX)

    every = np.ones(len(lay), bool)
    z3 = (GEO[3][1], -1.0)                                   # sensitive half-length and z offset of L3
    inz = np.abs(h["z"] - z3[1]) <= z3[0]
    rows = [("all SimTrackerHits", ratio_of(every)),
            ("fired 20 µm pixels", ratio(unique_pixels(4, every), unique_pixels(3, every))),
            ("hits above 3.6 keV (1000 e⁻)", ratio_of(h["edep"] >= 3.6)),
            (f"hits earlier than {BX_SPACING_NS:.0f} ns (one bunch spacing)", ratio_of(h["t"] < BX_SPACING_NS)),
            ("sub-MeV secondary electrons only", ratio_of(cls == 2)),
            ("only the part of L4 inside the z range of L3", ratio(cnt((lay == 4) & inz), cnt(lay == 3))),
            ("hits made by a stored charged particle", ratio_of(cls < 2)),
            ("track p$_T$ at the hit > 1 MeV", ratio_of(h["pt"] >= 1.0)),
            ("helix calculation: primaries reaching the layer", ratio(bxt["pred_first_L4"], bxt["pred_first_L3"]))]
    md += ["", "## L4/L3 under different ways of counting and selecting", "", "| selection | L4/L3 |", "|---|---|"]
    md += [f"| {n.replace('$_T$', 'T')} | {v:.3f} ± {e:.3f} |" for n, (v, e) in rows]
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    ys = np.arange(len(rows))[::-1]
    vals, errs = np.array([r[1][0] for r in rows]), np.array([r[1][1] for r in rows])
    ax.axvline(1.0, color=INK, lw=1.0)
    ax.errorbar(vals, ys, xerr=errs, fmt="o", ms=8, color="#2a78d6", ecolor=INK2, elinewidth=1.2, capsize=0,
                markeredgecolor=SURFACE, markeredgewidth=1.5)
    for y, v in zip(ys, vals):
        ax.text(v * 1.16, y, f"{v:.2f}", va="center", color=INK, fontsize=9)
    ax.set_xscale("log")
    ax.set_xlim(0.08, 4.5)
    ax.set_xticks([0.1, 0.2, 0.5, 1, 2, 4])
    ax.set_xticklabels(["0.1", "0.2", "0.5", "1", "2", "4"])
    ax.set_yticks(ys)
    ax.set_yticklabels([r[0] for r in rows])
    ax.set_ylim(-0.6, len(rows) - 0.4)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("layer 4 / layer 3  (per bunch crossing, whole layers)")
    ax.text(0.985, 1.02, "layer 4 higher →", transform=ax.transAxes, ha="right", color=MUTED, fontsize=8.5)
    ax.text(0.02, 1.02, "← layer 3 higher", transform=ax.transAxes, ha="left", color=MUTED, fontsize=8.5)
    titles(fig, "What does and does not put layer 3 back above layer 4", top=0.80)
    fig.subplots_adjust(left=0.47, right=0.97)
    save(fig, "ratio_summary")

    md += ["", "## L4 restricted to the z range of L3 (equal length, 2.2x the silicon)", "",
           "| | L3 | L4, same z range | L4/L3 |", "|---|---|---|---|"]
    for name, sel in (("all hits", every), ("sub-MeV secondary electrons", cls == 2), ("stored charged particles", cls < 2)):
        r3, r4 = rate((lay == 3) & sel), rate((lay == 4) & sel & inz)
        v, e = ratio(cnt((lay == 4) & sel & inz), cnt((lay == 3) & sel))
        md.append(f"| {name} | {r3[0]:.4f} ± {r3[1]:.4f} | {r4[0]:.4f} ± {r4[1]:.4f} | {v:.3f} ± {e:.3f} |")
    md += ["", "## L4/L3 versus a charge threshold and versus a time window", "",
           "| hits with | L3 /BX | L4 /BX | L4/L3 |", "|---|---|---|---|"]
    for name, sel in ([(f"E_dep >= {c:g} keV", h["edep"] >= c) for c in (1.0, 1.8, 3.6, 5.0, 10.0)]
                      + [(f"t < {c:g} ns", h["t"] < c) for c in (2.0, 5.0, 10.0, 20.0, BX_SPACING_NS, 100.0)]):
        r3, r4 = rate((lay == 3) & sel), rate((lay == 4) & sel)
        v, e = ratio_of(sel)
        md.append(f"| {name.replace(f't < {BX_SPACING_NS:g}', f't < {BX_SPACING_NS:.1f}')} | {r3[0]:.4f} ± {r3[1]:.4f} | "
                  f"{r4[0]:.4f} ± {r4[1]:.4f} | {v:.3f} ± {e:.3f} |")

    # ---- density vs radius -------------------------------------------------
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    rr = np.array([GEO[L][0] for L in GEO])
    soft = np.array([tab[L][2][2][0] / area[L] for L in GEO])
    hard = np.array([(tab[L][0] - tab[L][2][2][0]) / area[L] for L in GEO])
    if args.full:
        w = uproot.open(args.full)["hits"].arrays(["layer", "by_secondary"], cut="det==2", library="np")
        warea = sum(SIWR_QUADS) * SIWR_QUAD_CM2
        ws, wh = (w["by_secondary"] == 1).sum() / NBX / warea, (w["by_secondary"] == 0).sum() / NBX / warea
        rr, soft, hard = np.append(rr, SIWR_R_MM), np.append(soft, ws), np.append(hard, wh)
        md += ["", f"Si-wrapper barrel (r = {SIWR_R_MM / 1e3:.2f} m, {len(SIWR_QUADS)} layers, {warea:.0f} cm2 in total): "
                   f"sub-MeV {ws:.3e} and charged-track {wh:.3e} hits/cm2/BX"]
    ax.plot(rr, hard, "-o", ms=7, color="#2a78d6", markeredgecolor=SURFACE, markeredgewidth=1.5,
            label="made by a stored charged particle")
    ax.plot(rr, soft, "-^", ms=8, color="#1baf7a", markeredgecolor=SURFACE, markeredgewidth=1.5,
            label="sub-MeV secondary electrons")
    guide = hard[0] * (rr[0] / rr) ** 2
    ax.plot(rr, guide, color=AXIS, lw=1.0, zorder=1)
    ax.text(rr[2] * 1.25, guide[2] * 0.62, "∝ 1/r²", color=MUTED, fontsize=9, ha="left", va="bottom")
    for i, name in enumerate(["L0", "L1", "L2", "L3", "L4"] + (["Si wrapper"] if args.full else [])):
        ax.annotate(name, (rr[i], soft[i]), xytext=(0, 8), textcoords="offset points", ha="center", color=INK2, fontsize=9)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("layer radius [mm]")
    ax.set_ylabel("SimTrackerHits per cm² of sensor per bunch crossing")
    ax.legend(loc="lower left")
    titles(fig, "Per unit area the sub-MeV component falls far more slowly with radius", top=0.82)
    save(fig, "density_vs_radius")

    # ---- time and deposited energy on L3 / L4 ------------------------------
    for name, col, edges, xlabel, logx, title in (
            ("time_L3_L4", "t", np.logspace(-1, 4, 41), "hit time after the bunch crossing [ns]", True,
             "Outer-barrel hits are late: most arrive after 2 ns, some after the next crossing"),
            ("edep_L3_L4", "edep", np.linspace(0, 100, 51), "deposited energy in the 50 µm sensor [keV]", False,
             "Charged tracks give a Landau peak; sub-MeV electrons a 1.6 keV Auger line plus a continuum")):
        fig, axs = plt.subplots(1, 2, figsize=(9.8, 4.6), sharey=True, gridspec_kw={"wspace": 0.14})
        for ax, L in zip(axs, (3, 4)):
            s = lay == L
            bottom = np.zeros(len(edges) - 1)
            for c, (label, colour) in enumerate(CLASSES):
                v = np.histogram(h[col][s & (cls == c)], bins=edges)[0] / NBX
                ax.stairs(bottom + v, edges, baseline=bottom, fill=True, color=colour, label=label,
                          edgecolor=SURFACE, linewidth=0.4)
                bottom += v
            inside = ((h[col][s] >= edges[0]) & (h[col][s] < edges[-1])).mean()
            extra = ""
            if col == "t":
                ax.axvline(BX_SPACING_NS, color=INK, lw=1.0)
                ax.text(BX_SPACING_NS * 1.12, 0.97, f"next bunch\ncrossing\n({BX_SPACING_NS:.0f} ns)",
                        transform=ax.get_xaxis_transform(), va="top", color=INK2, fontsize=8.5)
                extra = f"; {(h['t'][s] > BX_SPACING_NS).mean() * 100:.0f}% later than {BX_SPACING_NS:.0f} ns"
            ax.set_title(f"L{L}: {inside * 100:.1f}% of hits in range{extra}", loc="left", color=INK2, fontsize=10)
            if logx:
                ax.set_xscale("log")
            ax.set_xlim(edges[0], edges[-1])
            ax.set_xlabel(xlabel)
        axs[0].set_ylabel(HITS + " per bin" + ("\n(8 bins per decade)" if logx else " (2 keV)"))
        axs[1].legend(loc="upper right", fontsize=8.5, bbox_to_anchor=(1.0, 0.70 if col == "t" else 1.0))
        titles(fig, title, top=0.80)
        save(fig, name)

    # ---- fired MAPS pixels (what the readout sees) --------------------------
    md += ["", "## Fired 20 um MAPS pixels per BX (several SimTrackerHits can share one pixel)", "",
           "| layer | SimTrackerHits /BX | fired pixels /BX | hits per fired pixel | pixels fired by a stored charged particle /BX | pixels fired only by sub-MeV electrons /BX | sub-MeV hits that are 1.5-1.75 keV Si Auger electrons | of those, sharing the pixel with another hit |",
           "|---|---|---|---|---|---|---|---|"]
    for L in (3, 4):
        s = lay == L
        key = np.stack([ibx[s], h["module"][s], h["sensor"][s], h["col20"][s], h["row20"][s]])
        u, inv, n_in_pixel = np.unique(key, axis=1, return_inverse=True, return_counts=True)
        inv = inv.ravel()
        hard_pixel = np.zeros(u.shape[1], bool)
        hard_pixel[inv[cls[s] < 2]] = True
        auger = (cls[s] == 2) & (h["edep"][s] >= 1.5) & (h["edep"][s] < 1.75)
        md.append(f"| L{L} | {s.sum() / NBX:.4f} | {u.shape[1] / NBX:.4f} | {s.sum() / u.shape[1]:.2f} | {hard_pixel.sum() / NBX:.4f} | "
                  f"{(~hard_pixel).sum() / NBX:.4f} | {auger.sum() / max((cls[s] == 2).sum(), 1) * 100:.0f}% | "
                  f"{(n_in_pixel[inv][auger] > 1).mean() * 100:.0f}% |")

    # ---- true occupancy ----------------------------------------------------
    md += ["", "## Occupancy per BX (what the bib-studies 'occupancy [%]' is not)", "",
           "| layer | sensors | pixels/sensor (sample segmentation) | fired pixels /BX | fired pixels / sensors [%] (= bib-studies 'occupancy') | true pixel occupancy /BX | sensors hit /BX | fraction of sensors hit | BXs with >=1 hit | fired 20 um pixels /BX | true occupancy at 20 um |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    occ, occ20 = {}, {}
    for L in GEO:
        s = lay == L
        npx = len(np.unique(np.stack([ibx[s], h["module"][s], h["sensor"][s], h["ix"][s], h["iy"][s]]), axis=1).T) / NBX
        nse = len(np.unique(np.stack([ibx[s], h["module"][s], h["sensor"][s]]), axis=1).T) / NBX
        occ[L] = npx / (GEO[L][2] * GEO[L][4])
        n20 = o20 = ""
        if L >= 3:
            n = len(np.unique(np.stack([ibx[s], h["module"][s], h["sensor"][s], h["col20"][s], h["row20"][s]]), axis=1).T) / NBX
            occ20[L] = n / (GEO[L][2] * MAPS_PIXELS)
            n20, o20 = f"{n:.4f}", f"{occ20[L]:.2e}"
        md.append(f"| L{L} | {GEO[L][2]} | {GEO[L][4]} | {npx:.4f} | {npx / GEO[L][2] * 100:.4f} | {occ[L]:.2e} | {nse:.4f} | "
                  f"{nse / GEO[L][2] * 100:.3f}% | {len(np.unique(ibx[s])) / NBX * 100:.1f}% | {n20} | {o20} |")
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    ys = np.arange(len(GEO))[::-1]
    ax.hlines(ys, 1e-11, [occ[L] for L in GEO], color=AXIS, lw=1.0)
    ax.plot([occ[L] for L in GEO], ys, "o", ms=9, color="#2a78d6", markeredgecolor=SURFACE, markeredgewidth=1.5,
            label="at the segmentation of the sample (25 µm inner, 50×150 µm outer)")
    ax.plot([occ20[L] for L in (3, 4)], [ys[3], ys[4]], "s", ms=8, color="#eb6834", markeredgecolor=SURFACE,
            markeredgewidth=1.5, label="at the 20 µm MAPS pitch")
    for L in GEO:
        ax.text(occ[L] * 1.5, ys[L], f"{occ[L]:.1e}", va="center", color=INK, fontsize=9)
    ax.set_xscale("log")
    ax.set_xlim(1e-11, 1e-5)
    ax.set_ylim(-0.6, len(GEO) - 0.4)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"L{L}" for L in GEO])
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("fraction of pixels fired per bunch crossing (fired pixels / all pixels of the layer)")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1, fontsize=8.5)
    titles(fig, "True pixel occupancy per bunch crossing is below 10⁻⁶ on every layer", top=0.80)
    fig.subplots_adjust(bottom=0.30)
    save(fig, "occupancy_per_layer")

    # ---- density along z ----------------------------------------------------
    fig, axs = plt.subplots(1, 2, figsize=(9.8, 4.6), sharey=True, gridspec_kw={"wspace": 0.14, "width_ratios": [1, 2]})
    for ax, L in zip(axs, (3, 4)):
        s = lay == L
        hz = GEO[L][1]
        edges = np.linspace(-hz, hz, int(round(2 * hz / 20.4)) + 1)      # one bin per sensor row
        bin_area = area[L] / (len(edges) - 1)
        bottom = np.zeros(len(edges) - 1)
        for c, (label, colour) in enumerate(CLASSES):
            v = np.histogram(h["z"][s & (cls == c)] - (-1.0 if L == 3 else 1.0), bins=edges)[0] / NBX / bin_area
            ax.stairs(bottom + v, edges, baseline=bottom, fill=True, color=colour, label=label,
                      edgecolor=SURFACE, linewidth=0.4)
            bottom += v
        ax.set_xlim(-hz, hz)
        ax.set_xlabel("z relative to the layer centre [mm]")
        ax.set_title(f"L{L}: {tab[L][0] / area[L]:.2e} per cm² on average", loc="left", color=INK2, fontsize=10)
    axs[0].set_ylabel("SimTrackerHits per cm² of sensor per bunch crossing")
    axs[1].legend(loc="upper right", fontsize=8.5)
    titles(fig, "Along z the sub-MeV component is nearly flat on both layers", top=0.80)
    save(fig, "density_vs_z_L3_L4")

    (out / "summary_numbers.md").write_text("\n".join(md) + "\n")
    print(f"[table] {out / 'summary_numbers.md'}")


if __name__ == "__main__":
    main()
