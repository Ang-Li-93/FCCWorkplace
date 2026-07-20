#!/usr/bin/env python3
"""
Model-independence bias test for the hadronic (Z->qq) channel, ecm 240, following
arXiv:2512.21290 Section 7.2: the branching ratio of each Higgs decay mode is
perturbed individually by a fixed amount chosen such that the TOTAL ZH cross
section shifts by a relative amount X (X = 1% for the hadronic channel). The
mode-h signal template is scaled by (1 + X/BR_h) in the pseudo-data, the nominal
fit (identical templates and nuisances) is rerun on each pseudo-dataset, and the
bias is reported as (r_fit - (1+X)) in percent.

Inputs: run_2D_mrecoil_mjj_qq/{datacard.root, signal_by_decay.root, datacard_2d_qq.txt}
        (produced by makeWS_2D_qq.py) - run AFTER the nominal fit setup.
Run INSIDE the combine env (cd HiggsAnalysis/CombinedLimit && source env_standalone.sh):
  python3 bias_test_qq.py

Also prints the per-decay selection efficiency spread (hiBDT+loBDT yields), the
companion table to the paper's model-independence discussion.
"""
import os
import shutil
import subprocess
import sys

import ROOT

ROOT.gROOT.SetBatch(True)

X = 0.01  # injected relative shift of the total ZH cross section (paper: 1% hadronic)

# SM branching ratios (mH = 125 GeV); H->inv approximated by ZZ*->4nu
BR = {
    "Hbb": 0.5824, "HWW": 0.2137, "Hgg": 0.0818, "Htautau": 0.0627,
    "Hcc": 0.0289, "HZZ": 0.02619, "Haa": 0.00227, "HZa": 0.001533,
    "Hmumu": 0.000218, "Hss": 0.00025, "Hinv": 0.00106,
}

CATEGORIES = ["hiBDT", "loBDT"]
HERE = os.path.dirname(os.path.abspath(__file__))
RUNDIR = os.path.join(HERE, "run_2D_mrecoil_mjj_qq")


def best_fit_r(carddir):
    """text2workspace + MultiDimFit best fit on the card's OWN data_obs."""
    subprocess.check_call("text2workspace.py datacard_2d_qq.txt -o ws.root",
                          shell=True, cwd=carddir, stdout=subprocess.DEVNULL,
                          stderr=subprocess.STDOUT)
    subprocess.check_call(
        "combine -M MultiDimFit --algo singles --setParameterRanges r=0.9,1.1 ws.root "
        "-m 125 --cminDefaultMinimizerStrategy 0 -n biastest > combine.log 2>&1", shell=True, cwd=carddir)
    f = ROOT.TFile.Open(f"{carddir}/higgsCombinebiastest.MultiDimFit.mH125.root")
    t = f.Get("limit")
    if not t or t.GetEntries() == 0:
        f.Close()
        sys.exit(f"ERROR: fit produced no result in {carddir} (see combine.log)")
    t.GetEntry(0)  # best-fit entry
    r = float(t.r)
    f.Close()
    if r <= 0.5:
        sys.exit(f"ERROR: fit failed in {carddir} (r={r}); see combine.log")
    return r


def main():
    for fn in ("datacard.root", "signal_by_decay.root", "datacard_2d_qq.txt"):
        if not os.path.isfile(os.path.join(RUNDIR, fn)):
            sys.exit(f"ERROR: {RUNDIR}/{fn} missing - run makeWS_2D_qq.py first")

    fT = ROOT.TFile.Open(f"{RUNDIR}/datacard.root")
    fS = ROOT.TFile.Open(f"{RUNDIR}/signal_by_decay.root")

    # per-decay yields / efficiency spread (companion table)
    print("=== per-decay signal yields (hiBDT / loBDT) ===")
    tot = {c: fT.Get(f"{c}_signal").Integral() for c in CATEGORIES}
    for h in BR:
        y = {c: fS.Get(f"{c}_sig_{h}").Integral() for c in CATEGORIES}
        print(f"  {h:8s}  hi {y['hiBDT']:12.1f}  lo {y['loBDT']:12.1f}   "
              f"(hi fraction of mode: {100*y['hiBDT']/max(y['hiBDT']+y['loBDT'],1e-9):.1f}%)")
    print(f"  {'TOTAL':8s}  hi {tot['hiBDT']:12.1f}  lo {tot['loBDT']:12.1f}")

    print(f"\n=== bias test: X = {100*X:.0f}% total-xsec injection per decay mode ===")
    results = []
    for h, br in BR.items():
        scale = X / br  # extra fraction of the mode's own yield
        vdir = os.path.join(RUNDIR, f"bias_{h}")
        os.makedirs(vdir, exist_ok=True)
        shutil.copy(os.path.join(RUNDIR, "datacard_2d_qq.txt"), vdir)

        fOut = ROOT.TFile(f"{vdir}/datacard.root", "RECREATE")
        for key in fT.GetListOfKeys():
            obj = fT.Get(key.GetName())
            if key.GetName().endswith("_data_obs"):
                cat = key.GetName().replace("_data_obs", "")
                obj = obj.Clone(key.GetName())
                obj.Add(fS.Get(f"{cat}_sig_{h}"), scale)
            obj.Write(key.GetName())
        fOut.Close()

        r = best_fit_r(vdir)
        bias = (r - (1.0 + X)) * 100.0
        results.append((h, br, r, bias))
        print(f"  {h:8s} BR={br:8.5f}  r_fit={r:.5f}  bias={bias:+.3f}%")

    print("\nSummary (bias = r_fit - (1+X), percent of sigma_ZH):")
    worst = max(results, key=lambda x: abs(x[3]))
    for h, br, r, bias in results:
        print(f"  {h:8s} {bias:+.3f}%")
    print(f"Largest |bias|: {worst[0]} ({worst[3]:+.3f}%)")


if __name__ == "__main__":
    main()
