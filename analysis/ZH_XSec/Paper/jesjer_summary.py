#!/usr/bin/env python3
"""
JES / JER impact table: the hadronic 2D fit and the full combination WITH the jet energy scale
and resolution nuisances (makeWS_2D_qq.py --jesjer / --jes-only / --jer-only run dirs) next to the
nominal fit, per energy, for the three uncertainty definitions of the fit drivers:
  stat only              xsecSTAT        every constrained nuisance frozen
  stat + 1% bkg norm     xsecSTATshapes  only the shape nuisances frozen (JES / JER included)
  stat + 1% bkg + syst   xsec            nothing frozen (JES / JER profiled)
and the relative degradation of the total precision with respect to the nominal fit,
xsec(variant) / xsec(nominal) - 1, the quantity arXiv:2512.21290 Sec. 5.3 quotes (+3.9% JES,
+3.2% JER for the hadronic channel at 240 GeV, not included in the paper's Table 2).

Run dirs (per energy, <base>/<dir>; base = S{ecm}/combine or --base):
  qq   run_2D_mrecoil_mjj_qq<suffix>            nominal, and run_2D_mrecoil_mjj_qq<suffix>_<variant>
  all  run_<ecm>_all<suffix>                    nominal, and run_<ecm>_all<suffix>_<variant>
with the scan files higgsCombine<xsec|xsecSTAT|xsecSTATshapes>.MultiDimFit.mH125.root. Missing
dirs or files give n/a cells (exit code 0). The precision is read exactly as fit_precision.py
does (2*deltaNLL = 1 crossings, linear interpolation); the fit_summary.txt printouts of the
same run dirs are cross-checked to 3 decimals when present.

  python3 jesjer_summary.py [--suffix _oldbdt] [--variants jesjer,jes,jer] [--ecm 240,365] [--base DIR] [--out FILE]
"""
import argparse
import contextlib
import io
import os
import re
import sys

import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kWarning
PAPER = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(PAPER, "S240", "combine"))
from fit_precision import crossings, scan_points  # noqa: E402

SCANS = [("stat", "xsecSTAT"), ("shapes", "xsecSTATshapes"), ("total", "xsec")]
SCAN_FILE = "higgsCombine{}.MultiDimFit.mH125.root"
LABEL = {"": "nominal", "jesjer": "JES + JER", "jes": "JES only", "jer": "JER only"}
SUMMARY_RE = re.compile(r"^(total|stat-only)\s*: r = .*->\s+([0-9.]+)%")


def precision(path):
    """1-sigma precision (fraction) from a MultiDimFit grid scan, or None."""
    if not os.path.isfile(path):
        return None
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            best, pts = scan_points(path)
            lo, hi = crossings(best, pts)
    except SystemExit:
        return None
    if lo is None or hi is None:
        return None
    return 0.5 * (hi - lo)


def summary_values(rundir):
    """Precisions printed in fit_summary.txt: {'total': x, 'xsecSTAT': y, 'xsecSTATshapes': z} in %, or {}."""
    path = os.path.join(rundir, "fit_summary.txt")
    out = {}
    if not os.path.isfile(path):
        return out
    block = None
    with open(path, errors="replace") as fh:
        for line in fh:
            m = re.search(r"total vs (xsecSTATshapes|xsecSTAT)\b", line)
            if m:
                block = m.group(1)
                continue
            m = SUMMARY_RE.match(line)
            if m and block:
                out["total" if m.group(1) == "total" else block] = float(m.group(2))
    return out


def pct(x, nd=3):
    return "n/a" if x is None else f"{100 * x:.{nd}f}%"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--suffix", default="_oldbdt", help="base run-dir suffix of the nominal fits (default _oldbdt)")
    ap.add_argument("--variants", default="jesjer,jes,jer", help="run-dir suffix fragments appended to the base suffix")
    ap.add_argument("--ecm", default="240,365")
    ap.add_argument("--base", default=None, help="parent of the run dirs, with {ecm} (default S{ecm}/combine)")
    ap.add_argument("--out", default=None, help="write the markdown here as well")
    args = ap.parse_args()
    variants = [""] + [v.strip() for v in args.variants.split(",") if v.strip()]
    lines = [f"JES / JER impact (run-dir suffix '{args.suffix}'; precision = half the 2dNLL=1 interval, Asimov; "
             "'rel. total' = xsec(variant)/xsec(nominal) - 1)", ""]
    for ecm in [e.strip() for e in args.ecm.split(",") if e.strip()]:
        base = (args.base or os.path.join(PAPER, "S{ecm}", "combine")).format(ecm=ecm)
        lines.append(f"## {ecm} GeV")
        lines.append("")
        lines.append("| channel | nuisances | stat only (xsecSTAT) | stat + 1% bkg (xsecSTATshapes) | stat + 1% bkg + syst (xsec) | rel. total vs nominal | run dir |")
        lines.append("|---|---|---|---|---|---|---|")
        notes = []
        for ch, tmpl in (("Z(qq)H 2D", "run_2D_mrecoil_mjj_qq"), ("ee+mumu+qq", f"run_{ecm}_all")):
            nominal_total = None
            for v in variants:
                rd = os.path.join(base, tmpl + args.suffix + (f"_{v}" if v else ""))
                vals = {k: precision(os.path.join(rd, SCAN_FILE.format(name))) for k, name in SCANS}
                if v == "":
                    nominal_total = vals["total"]
                rel = ("n/a" if vals["total"] is None or not nominal_total else f"{100 * (vals['total'] / nominal_total - 1):+.2f}%")
                lines.append(f"| {ch} | {LABEL.get(v, v)} | {pct(vals['stat'])} | {pct(vals['shapes'])} | {pct(vals['total'])} | "
                             f"{rel if v else '-'} | {os.path.basename(rd) if os.path.isdir(rd) else os.path.basename(rd) + ' (missing)'} |")
                # cross-check against fit_summary.txt (3 decimals)
                sv = summary_values(rd)
                for k, name in SCANS:
                    key = "total" if k == "total" else name
                    if vals[k] is not None and key in sv and abs(100 * vals[k] - sv[key]) > 0.0015:
                        notes.append(f"{os.path.basename(rd)}: {name} {100 * vals[k]:.3f}% here vs {sv[key]:.3f}% in fit_summary.txt")
        lines.append("")
        if notes:
            lines.append("Cross-check notes: " + "; ".join(notes))
            lines.append("")
    text = "\n".join(lines)
    print(text)
    if args.out:
        with open(args.out, "w") as fh:
            fh.write(text + "\n")


if __name__ == "__main__":
    main()
