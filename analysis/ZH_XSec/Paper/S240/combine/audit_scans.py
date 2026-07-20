#!/usr/bin/env python3
"""
Audit all MultiDimFit grid scans for reliability:
 - best-fit entry present (quantileExpected == -1)
 - the scan parabola touches 0: min(2*deltaNLL) over grid points ~ 0
 - no negative deltaNLL grid points (would mean a better minimum than the fit found)
 - minimum located at r ~ 1 (Asimov)
 - no large grid gap near the minimum; both 2dNLL=1 crossings inside the range
Usage: python3 audit_scans.py <base_dir> [...]; audits every higgsCombine*.MultiDimFit* found.
"""
import glob
import os
import sys

import ROOT

ROOT.gROOT.SetBatch(True)

def audit(fname):
    f = ROOT.TFile.Open(fname)
    if not f or f.IsZombie():
        return "UNREADABLE", []
    t = f.Get("limit")
    if not t or t.GetEntries() == 0:
        f.Close()
        return "EMPTY", []
    best, pts = None, {}
    for i in range(t.GetEntries()):
        t.GetEntry(i)
        if t.quantileExpected == -1:
            best = float(t.r)
        else:
            pts[float(t.r)] = 2.0 * float(t.deltaNLL)
    f.Close()
    issues = []
    if not pts:
        return "NO-GRID (algo singles?)", []
    xs = sorted(pts)
    ys = [pts[x] for x in xs]
    mn = min(ys); rmin = xs[ys.index(mn)]
    if best is None: issues.append("no best-fit entry (initial fit failed)")
    if mn > 0.05: issues.append(f"parabola does NOT touch 0: min 2dNLL = {mn:.3f}")
    neg = [y for y in ys if y < -1e-3]
    if neg: issues.append(f"{len(neg)} negative dNLL points (better min than fit: {min(neg):.3f})")
    if abs(rmin - 1.0) > 0.003: issues.append(f"minimum off r=1: r_min = {rmin:.4f}")
    # crossings + gap near minimum
    lo = hi = None
    for (x1, y1), (x2, y2) in zip(zip(xs, ys), list(zip(xs, ys))[1:]):
        if (y1 - 1) * (y2 - 1) <= 0 and y2 != y1:
            x = x1 + (1 - y1) * (x2 - x1) / (y2 - y1)
            if x < rmin: lo = x
            elif hi is None: hi = x
    if lo is None or hi is None:
        issues.append(f"2dNLL=1 crossing missing ({'left' if lo is None else 'right'}) - range too narrow")
    core = [x for x, y in zip(xs, ys) if y < 4]
    if len(core) >= 2:
        gaps = [b - a for a, b in zip(core, core[1:])]
        med = sorted(gaps)[len(gaps)//2]
        if max(gaps) > 3.5 * max(med, 1e-9):
            issues.append(f"grid gap near minimum: max spacing {max(gaps):.4f} vs median {med:.4f}")
    if len(core) < 6: issues.append(f"only {len(core)} points in the 2dNLL<4 core")
    prec = 0.5 * (hi - lo) * 100 if lo is not None and hi is not None else float("nan")
    verdict = "OK" if not issues else "CHECK"
    return f"{verdict}  npts={len(xs)} min2dNLL={mn:+.4f} rmin={rmin:.4f} prec={prec:.3f}%", issues

for base in sys.argv[1:]:
    for fname in sorted(glob.glob(os.path.join(base, "**", "higgsCombine*.MultiDimFit*.root"), recursive=True)):
        rel = os.path.relpath(fname, base)
        status, issues = audit(fname)
        print(f"{status:70s} {rel}")
        for i in issues:
            print(f"    -> {i}")
