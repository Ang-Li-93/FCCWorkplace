#!/usr/bin/env python3
"""
plot_pixesl_hits.py
===================
Plots for the MAPS-vertex PixESL hits. Prefers the *extended* CSV
(<stem>_extended.csv: + layer,module,sensor,r_mm,z_mm) for per-layer plots;
falls back to the strict CSV (BX,COL,ROW,h_time,qin).

    python analysis/plot_pixesl_hits.py outputs/pixesl_qq_5evt.csv [--outdir outputs/plots]

Produces (in --outdir):
  occupancy_map_L<layer>.png   COL vs ROW 2D pixel hit map, per VTXOB layer
  qin_hist.png                 charge (Landau), per layer
  h_time_hist.png              hit time, per layer  (shows TOF: r=130 vs 315 mm)
  hits_per_event.png           hit multiplicity per event
  rz_hitmap.png                r vs z of hits (the two VTXOB cylinders)
  hits_per_layer.png           hit counts / rate per layer
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path


def die(m, c=1):
    print(f"ERROR: {m}", file=sys.stderr); sys.exit(c)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Plot MAPS-vertex PixESL hits.")
    ap.add_argument("csv", help="PixESL CSV (strict or extended)")
    ap.add_argument("--outdir", default="outputs/plots")
    ap.add_argument("--bins", type=int, default=100)
    ap.add_argument("--format", default="pdf", help="image format (pdf, png, ...)")
    args = ap.parse_args(argv)

    try:
        import numpy as np, pandas as pd, matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # noqa: BLE001
        die(f"need numpy/pandas/matplotlib ({exc}). Source the Key4hep stack.")

    csv = Path(args.csv)
    ext = csv.with_name(csv.stem + "_extended.csv")
    use = ext if ext.is_file() else csv
    df = pd.read_csv(use)
    if df.empty:
        die("CSV has no rows.")
    has_layer = "layer" in df.columns
    layers = sorted(df["layer"].unique()) if has_layer else [None]
    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    print(f"[plot] using {use.name}  ({len(df)} hits, layers={layers if has_layer else 'n/a'})")

    def save(fig, name):
        path = outdir / f"{Path(name).stem}.{args.format}"
        fig.savefig(path, dpi=130, bbox_inches="tight"); plt.close(fig)
        print(f"[plot] wrote {path}")

    cmap_layer = {l: c for l, c in zip(layers, ["C0", "C1", "C2", "C3", "C4"])}

    # 1) per-layer 2D occupancy (COL vs ROW)
    if has_layer:
        for L in layers:
            d = df[df["layer"] == L]
            fig, ax = plt.subplots(figsize=(6, 5))
            h = ax.hist2d(d["COL"], d["ROW"], bins=args.bins, cmap="viridis")
            fig.colorbar(h[3], ax=ax, label="hits/bin")
            ax.set(xlabel="COL (20 µm pixel)", ylabel="ROW (20 µm pixel)",
                   title=f"VTXOB layer {L} occupancy  ({len(d)} hits)")
            save(fig, f"occupancy_map_L{L}.png")
    else:
        fig, ax = plt.subplots(figsize=(6, 5))
        h = ax.hist2d(df["COL"], df["ROW"], bins=args.bins, cmap="viridis")
        fig.colorbar(h[3], ax=ax, label="hits/bin")
        ax.set(xlabel="COL", ylabel="ROW", title="Occupancy map")
        save(fig, "occupancy_map.png")

    # 2) qin (charge) per layer
    fig, ax = plt.subplots(figsize=(6, 4))
    rng = (0, np.percentile(df["qin"], 99))
    for L in layers:
        d = df[df["layer"] == L] if has_layer else df
        ax.hist(d["qin"], bins=60, range=rng, histtype="step", linewidth=1.6,
                label=(f"layer {L}" if has_layer else "all"))
    ax.set(xlabel="qin [electrons]", ylabel="hits",
           title=f"Charge (median {df['qin'].median():.0f} e-, MIP~3600)")
    ax.legend(); save(fig, "qin_hist.png")

    # 3) h_time per layer -- zoomed to the PROMPT region (late backscatter from
    #    the calo can reach tens of ns and would swamp the TOF structure).
    tmax = 3000.0   # ps: prompt TOF window (layer 3 ~0.43 ns, layer 4 ~1.05 ns)
    fig, ax = plt.subplots(figsize=(6, 4))
    for L in layers:
        d = df[df["layer"] == L] if has_layer else df
        ax.hist(d["h_time"], bins=60, range=(0, tmax), histtype="step", linewidth=1.6,
                label=(f"layer {L}" if has_layer else "all"))
    ax.set(xlabel="h_time [ps]", ylabel="hits",
           title=f"Hit time / TOF (prompt; >{tmax:.0f} ps backscatter tail not shown)")
    ax.legend(); save(fig, "h_time_hist.png")

    # 3b) full-range h_time on log-y (shows the backscatter tail)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(df["h_time"], bins=80, log=True, color="C3")
    ax.set(xlabel="h_time [ps]", ylabel="hits (log)",
           title="Hit time, full range (late tail = calo backscatter)")
    save(fig, "h_time_hist_full.png")

    # 4) hits per event
    hpe = df.groupby("BX").size()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(hpe.values, bins=range(0, int(hpe.max()) + 2))
    ax.set(xlabel="hits per event (BX)", ylabel="events",
           title=f"Hits/event (mean {hpe.mean():.1f})")
    save(fig, "hits_per_event.png")

    # 5) r-z hit map (the two VTXOB cylinders) -- needs extended
    if {"r_mm", "z_mm"}.issubset(df.columns):
        fig, ax = plt.subplots(figsize=(7, 4))
        for L in layers:
            d = df[df["layer"] == L] if has_layer else df
            ax.scatter(d["z_mm"], d["r_mm"], s=4, alpha=0.5,
                       label=(f"layer {L}" if has_layer else "all"))
        ax.set(xlabel="z [mm]", ylabel="r [mm]", title="VTXOB hit positions (r vs z)")
        ax.legend(); save(fig, "rz_hitmap.png")

    # 6) hits per layer (counts)
    if has_layer:
        fig, ax = plt.subplots(figsize=(5, 4))
        counts = df.groupby("layer").size()
        ax.bar([str(l) for l in counts.index], counts.values, color="C0")
        for i, v in enumerate(counts.values):
            ax.text(i, v, str(v), ha="center", va="bottom")
        ax.set(xlabel="VTXOB layer", ylabel="hits", title="Hits per VTXOB layer")
        save(fig, "hits_per_layer.png")

    print(f"[plot] done -> {outdir}/")


if __name__ == "__main__":
    main()
