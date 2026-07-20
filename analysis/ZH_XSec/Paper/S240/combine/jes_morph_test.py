#!/usr/bin/env python3
"""
Morphed jet-energy-scale robustness test for the hadronic (Z->qq) 2D fit (ecm 240).

The stage1 JETSCALE templates are produced at +-1e-5 (a placeholder magnitude carried
over from the muon momentum-scale treatment; no FCC report motivates 1e-5 for JETS).
Since the template shift is linear in the scale at these magnitudes, a REALISTIC
jet-energy-scale variation delta is approximated by linear morphing:

    T(delta) = T_nom + (delta / 1e-5) * (T(1e-5) - T_nom)

This builds variant datacards with JETSCALE Up/Down morphed to delta = 1e-4 (k=10)
and delta = 1e-3 (k=100), i.e. up to the level of a conservative in-situ-calibrated
FCC-ee JES, and refits. Negative bins arising from the extrapolation are clipped to
1e-9 (counted and reported). Run INSIDE the combine env:
  python3 jes_morph_test.py
"""
import os
import shutil
import subprocess
import sys

import ROOT

ROOT.gROOT.SetBatch(True)

HERE = os.path.dirname(os.path.abspath(__file__))
RUNDIR = os.path.join(HERE, "run_2D_mrecoil_mjj_qq")
SCALES = {"jes_1em4": 10.0, "jes_1em3": 100.0}
CATEGORIES = ["hiBDT", "loBDT"]


def morph(nom, var, k, name):
    h = nom.Clone(name)
    clipped = 0
    for b in range(1, h.GetNbinsX() + 1):
        v = nom.GetBinContent(b) + k * (var.GetBinContent(b) - nom.GetBinContent(b))
        if v < 0:
            v = 1e-9
            clipped += 1
        h.SetBinContent(b, v)
        h.SetBinError(b, nom.GetBinError(b))
    return h, clipped


def scan(carddir, freeze=None):
    tag = "STAT" if freeze else "tot"
    fr = f"--freezeParameters={freeze} " if freeze else ""
    subprocess.check_call("text2workspace.py datacard_2d_qq.txt -o ws.root", shell=True,
                          cwd=carddir, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    subprocess.check_call(
        f"combine -M MultiDimFit -t -1 --setParameterRanges r=0.97,1.03 --points=60 "
        f"--algo=grid ws.root --expectSignal=1 -m 125 --X-rtd TMCSO_AdaptivePseudoAsimov "
        f"--X-rtd ADDNLL_CBNLL=0 --cminDefaultMinimizerStrategy 0 {fr}-n {tag} "
        f"> combine_{tag}.log 2>&1", shell=True, cwd=carddir)
    out = subprocess.check_output(
        f"python3 {HERE}/fit_precision.py higgsCombine{tag}.MultiDimFit.mH125.root",
        shell=True, cwd=carddir, text=True)
    return out.strip().splitlines()[-1]


def main():
    fT = ROOT.TFile.Open(f"{RUNDIR}/datacard.root")
    for vname, k in SCALES.items():
        vdir = os.path.join(RUNDIR, vname)
        os.makedirs(vdir, exist_ok=True)
        shutil.copy(os.path.join(HERE, "datacard_2d_qq.txt"), vdir)
        nclip = 0
        fOut = ROOT.TFile(f"{vdir}/datacard.root", "RECREATE")
        for key in fT.GetListOfKeys():
            n = key.GetName()
            obj = fT.Get(n)
            if "_JETSCALE" in n:
                cat = n.split("_")[0]
                nom = fT.Get(f"{cat}_signal")
                m, c = morph(nom, obj, k, n)
                nclip += c
                m.Write(n)
            else:
                obj.Write(n)
        fOut.Close()
        print(f"=== {vname} (k={k:.0f}, JES delta = {k*1e-5:.0e}) — clipped bins: {nclip} ===")
        print("  total :", scan(vdir))
        print("  frozen:", scan(vdir, "JETSCALE"))
    fT.Close()
    print("\nnominal reference (JETSCALE at 1e-5): total 0.457%, stat-only 0.358%")


if __name__ == "__main__":
    main()
