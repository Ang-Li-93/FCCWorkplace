#!/usr/bin/env python3
"""
plot_readout_metrics.py  -  the readout-relevant plots for a MAPS pixel detector.

From the extended PixESL CSV (needs layer, z_mm) + per-layer geometry, makes:
  hitdensity_vs_z.pdf   hit density (hits/cm^2/event) vs z, per layer  (occupancy profile)
  rate_per_layer.pdf    hit rate (hits/cm^2/event) per layer            (headline)
  occupancy_per_layer.pdf  pixel occupancy/event (avg & peak BX) per layer
  occupancy_vs_window.pdf  occupancy vs # bunch crossings integrated     (readout scaling)

  python plot_readout_metrics.py <extended.csv> [--outdir DIR] [--pitch-um 20]
"""
from __future__ import annotations
import argparse, math, sys
from pathlib import Path

# per-layer geometry: layer id -> (radius_mm, half_length_mm)
GEO = {3: (130.0, 163.0), 4: (315.0, 326.0)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", help="extended PixESL CSV (with layer,z_mm)")
    ap.add_argument("--outdir", default="outputs/plots_readout")
    ap.add_argument("--pitch-um", type=float, default=20.0)
    args = ap.parse_args(argv)

    import numpy as np, pandas as pd, matplotlib
    matplotlib.use("Agg"); import matplotlib.pyplot as plt

    df = pd.read_csv(args.csv)
    if "layer" not in df or "z_mm" not in df:
        sys.exit("ERROR: need the *extended* CSV (layer, z_mm columns).")
    NEV = df.BX.nunique()
    layers = [L for L in sorted(df.layer.unique()) if L in GEO]
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    pitch_cm = args.pitch_um / 1e4
    def save(fig, n): fig.savefig(outdir/n, bbox_inches="tight"); plt.close(fig); print(f"[plot] {outdir/n}")

    # ---- 1) hit density vs z (occupancy profile) ----
    fig, ax = plt.subplots(figsize=(7,4))
    nb = 60
    for L in layers:
        r_cm, hl_cm = GEO[L][0]/10, GEO[L][1]/10
        d = df[df.layer==L]
        cnt, edges = np.histogram(d.z_mm, bins=nb, range=(-GEO[L][1], GEO[L][1]))
        dz_cm = (edges[1]-edges[0])/10.0
        dens = cnt / NEV / (2*math.pi*r_cm*dz_cm)         # hits/cm^2/event
        ctr = 0.5*(edges[1:]+edges[:-1])
        ax.step(ctr, dens, where="mid", label=f"layer {L} (r={GEO[L][0]:.0f} mm)")
    ax.set(xlabel="z [mm]", ylabel="hit density [hits/cm$^2$/event]",
           title="VTXOB occupancy profile vs z (physics only)")
    ax.legend(); save(fig, "hitdensity_vs_z.pdf")

    # ---- per-layer rate & occupancy ----
    rate, occ_avg, occ_max, labels = [], [], [], []
    for L in layers:
        r_cm, hl_cm = GEO[L][0]/10, GEO[L][1]/10
        area = 2*math.pi*r_cm*(2*hl_cm); npix = area/pitch_cm**2
        d = df[df.layer==L]; hpe = len(d)/NEV; perbx = d.groupby("BX").size()
        rate.append(hpe/area); occ_avg.append(hpe/npix); occ_max.append(perbx.max()/npix)
        labels.append(f"L{L}\nr={GEO[L][0]:.0f}mm")

    # 2) rate per layer
    fig, ax = plt.subplots(figsize=(5,4))
    ax.bar(labels, rate, color="C0")
    for i,v in enumerate(rate): ax.text(i, v, f"{v:.1e}", ha="center", va="bottom")
    ax.set(ylabel="hit rate [hits/cm$^2$/event]", title="Hit rate per VTXOB layer")
    save(fig, "rate_per_layer.pdf")

    # 3) occupancy per layer (avg + peak)
    fig, ax = plt.subplots(figsize=(5,4)); x = np.arange(len(layers))
    ax.bar(x-0.2, occ_avg, 0.4, label="avg/event", color="C0")
    ax.bar(x+0.2, occ_max, 0.4, label="peak BX", color="C3")
    ax.set_yscale("log"); ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set(ylabel="pixel occupancy / event", title=f"Occupancy per VTXOB layer ({args.pitch_um:.0f} µm pixels)")
    ax.legend(); save(fig, "occupancy_per_layer.pdf")

    # 4) occupancy vs integration window (# BX)
    fig, ax = plt.subplots(figsize=(6,4))
    windows = np.array([1,2,5,10,20,50,100,200,500,1000])
    for L, oa in zip(layers, occ_avg):
        ax.plot(windows, oa*windows, marker="o", label=f"layer {L}")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.axhline(1e-3, ls="--", color="grey", lw=0.8)
    ax.text(1, 1.1e-3, "0.1% occupancy", color="grey", fontsize=8)
    ax.set(xlabel="# bunch crossings integrated (frame)", ylabel="occupancy",
           title="Occupancy vs MAPS integration window (physics only)")
    ax.legend(); save(fig, "occupancy_vs_window.pdf")

    print(f"[plot] readout metrics -> {outdir}/   (events={NEV})")


if __name__ == "__main__":
    main()
