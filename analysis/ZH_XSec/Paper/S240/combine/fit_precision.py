#!/usr/bin/env python3
"""
Read combine MultiDimFit grid scans and print the 1-sigma precision on r
(2*deltaNLL = 1 crossings, linear interpolation around the best fit), plus the
systematic component sqrt(total^2 - stat^2) when a stat-only scan is also given.

Usage:
  python3 fit_precision.py <total_scan.root> [<stat_only_scan.root>]
  (files as produced by combine: higgsCombine<name>.MultiDimFit.mH125.root)

Channel/observable agnostic (python3 + ROOT only): works for the qq fits and the
leptonic scans alike.
"""
import sys

import ROOT


def scan_points(fname):
    """Return (best_r, sorted [(r, 2*deltaNLL)]) from a MultiDimFit limit tree."""
    f = ROOT.TFile.Open(fname)
    if not f or f.IsZombie():
        sys.exit(f"ERROR: cannot open {fname}")
    t = f.Get("limit")
    if not t:
        sys.exit(f"ERROR: no 'limit' tree in {fname}")
    best, pts = None, {}
    for i in range(t.GetEntries()):
        t.GetEntry(i)
        if t.quantileExpected == -1:  # best-fit entry
            best = t.r
            continue
        pts[t.r] = 2.0 * t.deltaNLL
    f.Close()
    if not pts:
        sys.exit(f"ERROR: no scan points in {fname}")
    if best is None:
        # initial fit failed (combine wrote no best-fit entry): use the grid minimum
        best = min(pts, key=pts.get)
        print(f"WARNING: no best-fit entry in {fname}; using grid minimum r={best:.4f}")
    xs = sorted(pts)
    return best, [(x, pts[x]) for x in xs]


def crossings(best, pts, cross=1.0):
    """Interpolated r values where 2*deltaNLL crosses `cross`, left/right of best."""
    lo = hi = None
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if (y1 - cross) * (y2 - cross) > 0:
            continue
        if y2 == y1:
            continue
        x = x1 + (cross - y1) * (x2 - x1) / (y2 - y1)
        if x < best:
            lo = x  # keep the crossing closest to best (last one before it)
        elif hi is None:
            hi = x
    return lo, hi


def precision(fname, label):
    best, pts = scan_points(fname)
    lo, hi = crossings(best, pts)
    if lo is None or hi is None:
        print(f"{label}: best fit r = {best:.4f}, but 2dNLL=1 crossing "
              f"{'below' if lo is None else 'above'} best fit is OUTSIDE the scan "
              f"range [{pts[0][0]:.3f}, {pts[-1][0]:.3f}] - widen --setParameterRanges")
        return None
    sigma = 0.5 * (hi - lo)
    print(f"{label}: r = {best:.4f}  [{lo:.4f}, {hi:.4f}]  ->  {100*sigma:.3f}%")
    return sigma


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    ROOT.gROOT.SetBatch(True)
    tot = precision(sys.argv[1], "total    ")
    if len(sys.argv) > 2:
        stat = precision(sys.argv[2], "stat-only")
        if tot is not None and stat is not None:
            syst2 = tot * tot - stat * stat
            syst = syst2 ** 0.5 if syst2 > 0 else 0.0
            print(f"syst     :                                {100*syst:.3f}%")
