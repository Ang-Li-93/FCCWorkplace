#!/usr/bin/env python3
"""Bin-by-bin comparison of every histogram (recursing into subdirectories)
of two ROOT files. Exit 0 iff all bins agree within rtol."""
import argparse, sys
import ROOT


def walk(d, prefix=""):
    for k in d.GetListOfKeys():
        obj = k.ReadObj()
        name = prefix + k.GetName()
        if obj.InheritsFrom("TDirectory"):
            yield from walk(obj, name + "/")
        elif obj.InheritsFrom("TH1"):
            yield name, obj


ap = argparse.ArgumentParser()
ap.add_argument("a"); ap.add_argument("b")
ap.add_argument("--rtol", type=float, default=1e-6)
args = ap.parse_args()

fa, fb = ROOT.TFile(args.a), ROOT.TFile(args.b)
ha = dict(walk(fa)); hb = dict(walk(fb))
only_a = sorted(set(ha) - set(hb)); only_b = sorted(set(hb) - set(ha))
if only_a: print("only in A:", only_a[:10])
if only_b: print("only in B:", only_b[:10])
nbad = 0; nhist = 0; worst = (0.0, "")
for name in sorted(set(ha) & set(hb)):
    A, B = ha[name], hb[name]
    nhist += 1
    bad = 0
    for i in range(A.GetNcells()):
        a, b = A.GetBinContent(i), B.GetBinContent(i)
        if a == b: continue
        denom = max(abs(a), abs(b), 1e-300)
        rel = abs(a - b) / denom
        if rel > args.rtol:
            bad += 1
            if rel > worst[0]: worst = (rel, f"{name}[{i}] {a} vs {b}")
    if bad:
        nbad += 1
        print(f"MISMATCH {name}: {bad} bins differ")
print(f"compared {nhist} histograms: {nbad} with mismatches"
      + (f"; worst rel diff {worst[0]:.2e} at {worst[1]}" if worst[0] else ""))
sys.exit(1 if (nbad or only_a or only_b) else 0)
