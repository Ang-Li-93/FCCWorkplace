#!/usr/bin/env python3
"""
rz_cache_slice.py - parallel read pass for plot_rz_layout.py.

Reads every NSLICES-th file (offset SLICE) of an EDM4hep directory and writes
a partial coordinate cache rz_cache_part<SLICE>.npz. Merge with
rz_cache_merge.py into the rz_cache.npz that plot_rz_layout.py consumes
(concatenation of hit-coordinate arrays = exact, no normalization involved).

  python3 rz_cache_slice.py --indir D --compact X --outdir O --slice K --nslices N
"""
import argparse, glob, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plot_rz_layout import read_hits  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--indir", required=True)
    ap.add_argument("--compact", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--slice", type=int, required=True)
    ap.add_argument("--nslices", type=int, required=True)
    args = ap.parse_args()

    import numpy as np
    files = sorted(glob.glob(f"{args.indir}/events_*.edm4hep.root")
                   or glob.glob(f"{args.indir}/bx_*.edm4hep.root")
                   or glob.glob(f"{args.indir}/*.edm4hep.root")
                   or glob.glob(f"{args.indir}/output_*.root")
                   or glob.glob(f"{args.indir}/*.root"))
    part = files[args.slice::args.nslices]
    if not part:
        sys.exit(f"no files for slice {args.slice}/{args.nslices}")
    print(f"[slice {args.slice}] {len(part)} files", file=sys.stderr)
    z, r, cat, nev = read_hits(part, args.compact, np)
    out = Path(args.outdir) / f"rz_cache_part{args.slice}.npz"
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, z=z, r=r, cat=cat, nev=nev)
    print(f"[slice {args.slice}] {len(z)} hits, {nev} events -> {out}")


if __name__ == "__main__":
    main()
