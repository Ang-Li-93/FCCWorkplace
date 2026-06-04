#!/usr/bin/env python3
"""
plot_pixesl_hits.py
===================
Make summary plots for a PixESL CSV (BX,COL,ROW,h_time,qin):

  * COL vs ROW 2D occupancy map        -> occupancy_map.png
  * hits-per-BX histogram              -> hits_per_bx.png
  * qin distribution                   -> qin_hist.png
  * h_time distribution                -> h_time_hist.png
  * coarse hottest-region map          -> hottest_map.png

    python analysis/plot_pixesl_hits.py outputs/pixesl_hits_zinclusive.csv \
        [--outdir outputs/plots]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def die(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Plot a PixESL hits CSV.")
    ap.add_argument("csv", help="PixESL CSV (BX,COL,ROW,h_time,qin)")
    ap.add_argument("--outdir", default="outputs/plots", help="output directory")
    ap.add_argument("--bins", type=int, default=80, help="2D map bins per axis")
    args = ap.parse_args(argv)

    try:
        import numpy as np
        import pandas as pd
        import matplotlib
        matplotlib.use("Agg")  # headless
        import matplotlib.pyplot as plt
    except Exception as exc:  # noqa: BLE001
        die(f"plotting needs numpy/pandas/matplotlib ({exc}). "
            "Source Key4hep or 'pip install numpy pandas matplotlib'.")

    csv_path = Path(args.csv)
    if not csv_path.is_file():
        die(f"CSV not found: {csv_path}")
    df = pd.read_csv(csv_path)
    if df.empty:
        die("CSV has no rows (0 hits). Nothing to plot.")

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    def save(fig, name):
        path = outdir / name
        fig.savefig(path, dpi=130, bbox_inches="tight")
        plt.close(fig)
        print(f"[plot] wrote {path}")

    # --- 1) COL vs ROW 2D occupancy ---------------------------------------
    fig, ax = plt.subplots(figsize=(6, 5))
    h = ax.hist2d(df["COL"], df["ROW"], bins=args.bins, cmap="viridis")
    fig.colorbar(h[3], ax=ax, label="hits / bin")
    ax.set_xlabel("COL")
    ax.set_ylabel("ROW")
    ax.set_title("PixESL occupancy map (COL vs ROW)")
    save(fig, "occupancy_map.png")

    # --- 2) hits per BX ---------------------------------------------------
    hits_per_bx = df.groupby("BX").size()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(hits_per_bx.values,
            bins=range(0, int(hits_per_bx.max()) + 2))
    ax.set_xlabel("hits per BX")
    ax.set_ylabel("number of BX")
    ax.set_title(f"Hits per BX (mean {hits_per_bx.mean():.2f})")
    save(fig, "hits_per_bx.png")

    # --- 3) qin -----------------------------------------------------------
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(df["qin"], bins=60)
    ax.set_xlabel("qin  [electrons]")
    ax.set_ylabel("hits")
    ax.set_title(f"Charge distribution (median {np.median(df['qin']):.0f} e-)")
    save(fig, "qin_hist.png")

    # --- 4) h_time --------------------------------------------------------
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.hist(df["h_time"], bins=60)
    ax.set_xlabel("h_time  [ps]")
    ax.set_ylabel("hits")
    ax.set_title("Hit-time distribution")
    save(fig, "h_time_hist.png")

    # --- 5) coarse hottest-region map ------------------------------------
    fig, ax = plt.subplots(figsize=(6, 5))
    h = ax.hist2d(df["COL"], df["ROW"], bins=max(20, args.bins // 4),
                  cmap="inferno")
    fig.colorbar(h[3], ax=ax, label="hits / coarse bin")
    ax.set_xlabel("COL")
    ax.set_ylabel("ROW")
    ax.set_title("Hottest-region map (coarse bins)")
    save(fig, "hottest_map.png")

    print(f"[plot] all plots written to {outdir}/")


if __name__ == "__main__":
    main()
