#!/usr/bin/env python3
# Run the rare-decay fits on the cards produced by make_datacards.py.
# For each scenario:
#   1. expected (Asimov, blind) 68% and 95% CL upper limits on the signal
#      cross-section sigma(ee -> mumuH, H -> X)
#   2. the signal cross-section needed for 3 sigma evidence and 5 sigma
#      discovery (bisection on expected Significance vs injected signal)
#
# Must be run inside the Combine standalone environment:
#   cd HiggsAnalysis/CombinedLimit && source env_standalone.sh
#   python3 run_fits.py

import os
import re
import subprocess

import ROOT

CARDS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cards")
XSEC_MUMUH = 0.0067643  # pb, for BR conversion

SCENARIOS = ["Hbs", "Huu", "Hdd", "Hcu", "Hsd", "Hbd"]


def placeholder_xsec(wdir):
    # generator placeholder xsec of the signal sample, recorded in the
    # datacard header by make_datacards.py (r is measured relative to it)
    with open(os.path.join(wdir, "datacard.txt")) as f:
        for line in f:
            m = re.search(r"signal placeholder xsec = ([0-9.eE+-]+) pb", line)
            if m:
                return float(m.group(1))
    raise RuntimeError(f"no placeholder xsec in {wdir}/datacard.txt")


def run(cmd, cwd):
    p = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return p.stdout + p.stderr


def expected_limit(wdir, cl):
    # data_obs is the SM-only Asimov, so no -t -1 needed. Default rAbsAcc
    # (5e-4) is larger than the limits here and freezes the bracketing at the
    # same r for every CL — tighten it. Read the limit tree for full precision.
    run(f"combine -M AsymptoticLimits workspace.root --cl {cl} "
        f"--rAbsAcc 1e-8 --rRelAcc 0.002 -n _cl{cl}", wdir)
    f = ROOT.TFile.Open(os.path.join(wdir, f"higgsCombine_cl{cl}.AsymptoticLimits.mH120.root"))
    t = f.Get("limit")
    vals = {}
    for e in t:
        vals[round(e.quantileExpected, 3)] = e.limit
    f.Close()
    return vals[0.5] if 0.5 in vals else vals[-1.0]


def significance(wdir, r):
    out = run(f"combine -M Significance workspace.root -t -1 --expectSignal {r:.6g} -n _sig", wdir)
    m = re.search(r"Significance: ([0-9.eE+-]+)", out)
    if not m:
        raise RuntimeError(f"no significance parsed in {wdir} (r={r})")
    return float(m.group(1))


def r_for_sigma(wdir, target, r_start):
    # significance grows ~linearly with r here; fixed-point iteration converges fast
    r = r_start
    for _ in range(12):
        z = significance(wdir, r)
        if z > 0 and abs(z - target) < 0.02:
            return r
        r *= target / max(z, 1e-3)
    return r


if __name__ == "__main__":
    rows = []
    for scenario in SCENARIOS:
        wdir = os.path.join(CARDS_DIR, scenario)
        xsec = placeholder_xsec(wdir)
        run("text2workspace.py datacard.txt -o workspace.root", wdir)
        r95 = expected_limit(wdir, 0.95)
        r68 = expected_limit(wdir, 0.68)
        r3 = r_for_sigma(wdir, 3.0, r95)
        r5 = r_for_sigma(wdir, 5.0, r3 * 5.0 / 3.0)
        to_br = xsec / XSEC_MUMUH  # BR = r * placeholder_xsec / sigma(mumuH)
        rows.append((scenario, r68 * to_br, r95 * to_br, r3 * to_br, r5 * to_br))
        print(f"{scenario}: xsec_ref={xsec:g} pb "
              f"(r95={r95:.4g}, r68={r68:.4g}, r3={r3:.4g}, r5={r5:.4g})")

    print(f"\n{'':4s}  {'BR UL68':>11s} {'BR UL95':>11s} {'BR 3sig':>11s} {'BR 5sig':>11s}")
    for scenario, ul68, ul95, s3, s5 in rows:
        print(f"{scenario:4s}  {ul68:11.4g} {ul95:11.4g} {s3:11.4g} {s5:11.4g}")
