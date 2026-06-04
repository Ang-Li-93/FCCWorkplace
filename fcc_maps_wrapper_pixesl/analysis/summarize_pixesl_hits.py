#!/usr/bin/env python3
"""
summarize_pixesl_hits.py
========================
Print summary statistics for a PixESL CSV (BX,COL,ROW,h_time,qin).

    python analysis/summarize_pixesl_hits.py outputs/pixesl_hits_zinclusive.csv

If a sibling ``<name>.metadata.json`` exists it is used for the pixel-grid size
(occupancy denominator) and detector geometry; otherwise sensible fallbacks are
derived from the data and an optional --geometry YAML.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def die(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def load_csv(path: Path):
    try:
        import pandas as pd
    except Exception as exc:  # noqa: BLE001
        die(f"pandas required ({exc}). Source Key4hep or 'pip install pandas'.")
    if not path.is_file():
        die(f"CSV not found: {path}")
    df = pd.read_csv(path)
    need = {"BX", "COL", "ROW", "h_time", "qin"}
    if not need.issubset(df.columns):
        die(f"CSV missing columns. Found {list(df.columns)}, need {sorted(need)}")
    if df.empty:
        die("CSV has no rows (0 hits). Check the conversion step.")
    return df


def find_metadata(csv_path: Path):
    cand = csv_path.with_name(csv_path.stem + ".metadata.json")
    if cand.is_file():
        with cand.open() as fh:
            return json.load(fh)
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Summarize a PixESL hits CSV.")
    ap.add_argument("csv", help="PixESL CSV (BX,COL,ROW,h_time,qin)")
    ap.add_argument("--geometry", default=None,
                    help="optional geometry_config.yaml for grid size fallback")
    args = ap.parse_args(argv)

    csv_path = Path(args.csv)
    df = load_csv(csv_path)
    meta = find_metadata(csv_path)

    import numpy as np

    n_hits = len(df)
    bx_vals = df["BX"].to_numpy()
    n_bx = int(np.unique(bx_vals).size)
    hits_per_bx = df.groupby("BX").size()

    # ---- pixel grid size for occupancy ----------------------------------
    n_col = n_row = None
    if meta:
        n_col = meta.get("n_col_effective")
        n_row = meta.get("n_row_effective")
    if (n_col is None or n_row is None) and args.geometry:
        try:
            import yaml
            g = yaml.safe_load(Path(args.geometry).read_text())
            n_col = g["sensor"]["n_col"]
            n_row = g["sensor"]["n_row"]
        except Exception:  # noqa: BLE001
            pass
    n_pixels = (n_col * n_row) if (n_col and n_row) else None

    qin = df["qin"].to_numpy()
    htime = df["h_time"].to_numpy()

    def pct(a, q):
        return float(np.percentile(a, q))

    print("=" * 60)
    print(f"PixESL summary: {csv_path}")
    if meta:
        print(f"  (collection: {meta.get('collection_used')}, "
              f"mode: {meta.get('mapping_mode')}, "
              f"input: {Path(meta.get('input_file','?')).name})")
    print("=" * 60)
    print(f"number of hits         : {n_hits}")
    print(f"number of BX            : {n_bx}")
    print(f"avg hits / BX           : {n_hits / n_bx:.3f}")
    print(f"max hits / BX           : {int(hits_per_bx.max())}")
    print(f"min hits / BX (nonzero) : {int(hits_per_bx.min())}")
    print("-" * 60)
    print(f"qin  mean   [e-]        : {qin.mean():.1f}")
    print(f"qin  median [e-]        : {np.median(qin):.1f}")
    print(f"qin  5/25/75/95 pct     : "
          f"{pct(qin,5):.0f} / {pct(qin,25):.0f} / "
          f"{pct(qin,75):.0f} / {pct(qin,95):.0f}")
    print(f"qin  min / max          : {qin.min():.1f} / {qin.max():.1f}")
    print("-" * 60)
    print(f"h_time min / max [ps]   : {htime.min():.1f} / {htime.max():.1f}")
    print(f"h_time mean [ps]        : {htime.mean():.1f}")
    print("-" * 60)
    print(f"COL min / max           : {int(df['COL'].min())} / {int(df['COL'].max())}")
    print(f"ROW min / max           : {int(df['ROW'].min())} / {int(df['ROW'].max())}")
    print("-" * 60)

    # ---- hottest pixels --------------------------------------------------
    hottest = (df.groupby(["COL", "ROW"]).size()
                 .sort_values(ascending=False).head(10))
    print("top 10 hottest pixels (COL, ROW : nhits):")
    for (col, row), cnt in hottest.items():
        print(f"   ({col:>8}, {row:>8}) : {cnt}")
    print("-" * 60)

    # ---- occupancy -------------------------------------------------------
    if n_pixels:
        avg_occ = (n_hits / n_bx) / n_pixels
        max_occ = int(hits_per_bx.max()) / n_pixels
        print(f"pixel grid (COL x ROW)  : {n_col} x {n_row} = {n_pixels} pixels")
        print(f"occupancy / BX (avg)    : {avg_occ:.3e}")
        print(f"occupancy / BX (max)    : {max_occ:.3e}")
    else:
        print("occupancy: pixel grid size unknown "
              "(no metadata json, no --geometry). Skipped.")

    # ---- hit rate per cm^2 per event (barrel area) -----------------------
    if meta and meta.get("wrapper_radius_mm") and meta.get("wrapper_half_length_mm"):
        r_cm = meta["wrapper_radius_mm"] / 10.0
        hl_cm = meta["wrapper_half_length_mm"] / 10.0
        area_cm2 = 2.0 * math.pi * r_cm * (2.0 * hl_cm)  # barrel lateral area
        rate = n_hits / n_bx / area_cm2
        print("-" * 60)
        print(f"barrel area [cm^2]      : {area_cm2:.1f}")
        print(f"hit rate / cm^2 / event : {rate:.3e}")
    print("=" * 60)


if __name__ == "__main__":
    main()
