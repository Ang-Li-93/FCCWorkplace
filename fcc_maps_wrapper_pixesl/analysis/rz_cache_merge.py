#!/usr/bin/env python3
"""Merge rz_cache_part*.npz (from rz_cache_slice.py) into rz_cache.npz."""
import argparse, glob, sys
from pathlib import Path
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--partdir", required=True, help="dir with rz_cache_part*.npz")
ap.add_argument("--outdir", required=True, help="dir for the merged rz_cache.npz")
ap.add_argument("--expect", type=int, default=None, help="expected number of parts")
args = ap.parse_args()

parts = sorted(glob.glob(f"{args.partdir}/rz_cache_part*.npz"))
if args.expect is not None and len(parts) != args.expect:
    sys.exit(f"ERROR: found {len(parts)} parts, expected {args.expect}")
z = []; r = []; cat = []; nev = 0
for p in parts:
    d = np.load(p)
    z.append(d["z"]); r.append(d["r"]); cat.append(d["cat"]); nev += int(d["nev"])
out = Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
np.savez(out / "rz_cache.npz", z=np.concatenate(z), r=np.concatenate(r),
         cat=np.concatenate(cat), nev=nev)
print(f"merged {len(parts)} parts: {sum(len(a) for a in z)} hits, {nev} events "
      f"-> {out/'rz_cache.npz'}")
