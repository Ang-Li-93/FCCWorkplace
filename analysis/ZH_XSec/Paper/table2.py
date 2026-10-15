#!/usr/bin/env python3
"""
Table 2 of arXiv:2512.21290 (JHEP version, MVA-based configuration) from the reproduction's
combine scans: one row per paper column and the three uncertainty definitions the fit drivers
(run_fit_leptonic.sh / run_fit_qq.sh / run_fit_combination.sh) produce for every run dir:

  stat only                  = xsecSTAT        every constrained nuisance frozen = the paper's stat-only
                                               (--freezeParameters=allConstrainedNuisances[,<rateParams>]:
                                               the 1% lnN background normalizations norm_* AND the
                                               shape nuisances BES / MUSCALE / ELSCALE / JETSCALE / SQRTS)
  stat + 1% bkg norm         = xsecSTATshapes  only the shape nuisances frozen, the norm_* lnN float
                                               = the paper's quoted TOTAL (the 1% normalizations are the
                                               only nuisance parameters of the paper's fit, Sec. 5.3;
                                               its stat-only = "background normalization parameters fixed")
  + regular syst profiled    = xsec            nothing frozen: BES, the lepton / jet momentum scale and
                                               sqrt(s) profiled in addition - BEYOND the paper's quoted
                                               precision (the paper evaluated these effects separately by
                                               repeating the fit with shifted inputs, 0.095% combined)

The paper-spec cards (makeWS_recoil_2cat.py, makeWS_2D_qq.py and their combineCards.py
combinations) carry no rateParam, so allConstrainedNuisances is the complete nuisance list.
The freeze lists are NOT hard-coded here: they are parsed from the '(paper stat-only: ...)' and
'(July run-book stat-only: ...)' header fragments of <rundir>/fit_summary.txt (the drivers
build them from the card and tee them there) and checked against the lnN / shape / rateParam
lines of the datacard found in the run dir; both are printed in the footnote, a disagreement
is flagged.

Precision = half the distance between the 2*deltaNLL = 1 crossings around the best fit
(linear interpolation): scan_points() / crossings() of S240/combine/fit_precision.py,
imported unchanged. Every printed value is also compared with the fit_precision.py printout
in fit_summary.txt of the same run dir (3 decimals); a mismatch is flagged in the Sources block.

Run dirs, per energy: <base>/<dir><suffix>/ with base = S{ecm}/combine (or --base) and
  Z(ee)H       run_recoil_2cat_ee          Z(mumu)H   run_recoil_2cat_mumu
  Z(ll)H       run_recoil_2cat_combined    Z(qq)H     run_2D_mrecoil_mjj_qq
  Combination  run_{ecm}_all
Scan files: higgsCombine<xsec|xsecSTAT|xsecSTATshapes>.MultiDimFit.mH125.root ('limit' tree,
branches r, deltaNLL, quantileExpected = -1 for the best-fit entry). A missing dir, file or
crossing gives an 'n/a' cell, never an abort; the exit code is 0 in every data situation
(only an argparse usage error, e.g. --ecm 300, exits 2).

python3 + ROOT + stdlib only (key4hep env or the combine container):
  python3 table2.py --suffix _oldbdt --label 'original models'
  python3 table2.py --ecm 240 --out table2_240.md --tex table2_240.tex
  /gpfs/mnt/gpfs01/usfcc/ali3/FCCWorkplace/run_combine.sh python3 analysis/ZH_XSec/Paper/table2.py
"""
import argparse
import contextlib
import datetime
import glob
import io
import os
import re
import sys
import traceback

import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kWarning

PAPER = os.path.dirname(os.path.abspath(__file__))

# fit_precision.py (S240 and S365 copies are identical) is imported unchanged; no bytecode is
# written so that nothing is created under S240/combine by this script.
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(PAPER, "S240", "combine"))
from fit_precision import crossings, scan_points  # noqa: E402

# arXiv:2512.21290 (JHEP version) Table 2, MVA-based configuration: relative uncertainty on
# sigma_ZH in %, (total, stat-only)
PAPER_TABLE2 = {
    240: {"ee": (0.81, 0.78), "mumu": (0.68, 0.66), "ll": (0.52, 0.50), "qq": (0.38, 0.30), "all": (0.31, 0.26)},
    365: {"ee": (1.91, 1.90), "mumu": (1.79, 1.79), "ll": (1.32, 1.30), "qq": (0.56, 0.47), "all": (0.52, 0.44)},
}
# paper row order: key, markdown label, run-dir template, paper-table group (LaTeX)
ROWS = [
    ("ee",   "Z(ee)H",      "run_recoil_2cat_ee",       "Leptonic final states"),
    ("mumu", "Z(mumu)H",    "run_recoil_2cat_mumu",     "Leptonic final states"),
    ("ll",   "Z(ll)H",      "run_recoil_2cat_combined", None),
    ("qq",   "Z(qq)H",      "run_2D_mrecoil_mjj_qq",    "Hadronic final state"),
    ("all",  "Combination", "run_{ecm}_all",            "Combination"),
]
TEX_ROW = {"ee": r"\ZeeH", "mumu": r"\ZmumuH", "ll": r"\ZllH", "qq": r"\ZqqH", "all": r"\ZH"}
# the paper's channel macros, with fallbacks for a standalone compilation
TEX_MACROS = [
    r"\providecommand{\ZeeH}{$\mathrm{Z(e^+e^-)H}$}",
    r"\providecommand{\ZmumuH}{$\mathrm{Z(\mu^+\mu^-)H}$}",
    r"\providecommand{\ZllH}{$\mathrm{Z(\ell^+\ell^-)H}$}",
    r"\providecommand{\ZqqH}{$\mathrm{Z(q\bar{q})H}$}",
    r"\providecommand{\ZH}{$\mathrm{ZH}$}",
]
# --label is free text: escaped where it lands in the caption (a '%' would otherwise comment out
# the rest of the \caption line and break the build)
TEX_SPECIALS = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
                "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def oneline(text):
    """Whitespace runs (newlines included) collapsed, so a LaTeX comment stays one comment line."""
    return " ".join(text.split())


def tex_escape(text):
    return "".join(TEX_SPECIALS.get(ch, ch) for ch in oneline(text))


# table columns in order: key, combine -n name, markdown header, LaTeX header
COLS = [
    ("stat",  "xsec"+"STAT",       "stat only (= paper stat)",                  r"stat"),
    ("bkg",   "xsec"+"STATshapes", "stat + 1% bkg norm (= paper total)",        r"stat+bkg"),
    ("total", "xsec",              "+ regular syst profiled (beyond the paper)", r"+syst"),
]
SCAN_FILE = "higgsCombine{}.MultiDimFit.mH125.root"
SUMMARY_FILE = "fit_summary.txt"
TITLE = ("Table 2 (arXiv:2512.21290, MVA-based): stat only (= paper stat) / stat + 1% bkg norm (= paper total) / "
         "+ regular syst profiled (beyond the paper), relative uncertainty on sigma_ZH in %")

# fit_summary.txt (tee of the drivers' precision printout):
#   == mumu @ 240 GeV (recoil): total vs xsecSTAT (paper stat-only: allConstrainedNuisances)
#   total    : r = 1.0000  [0.9931, 1.0068]  ->  0.685%
#   stat-only: r = 1.0000  [0.9934, 1.0066]  ->  0.660%
#   syst     :                                0.181%
#   == mumu @ 240 GeV (recoil): total vs xsecSTATshapes (July run-book stat-only: BES,MUSCALE,SQRTS)
#   ...
SUMMARY_HEADER = re.compile(r"^==.*total vs (xsecSTAT|xsecSTATshapes)\s*\(((?:paper|July run-book) stat-only):\s*([^)]*)\)")
SUMMARY_VALUE = re.compile(r"^(total|stat-only|syst)\s*:.*?([0-9]+\.[0-9]+)%\s*$")


# ----------------------------------------------------------------------------- inputs
def read_scan(path):
    """Precision from one MultiDimFit grid scan; never raises.

    dict: path, sigma (fraction, None when not determinable), best, lo, hi, npts (grid points,
    best-fit entry excluded), rmin, rmax, notes."""
    res = {"path": path, "sigma": None, "notes": []}
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):  # fit_precision prints its warnings
            best, pts = scan_points(path)
            lo, hi = crossings(best, pts)
    except SystemExit as exc:  # fit_precision exits on an unreadable / empty file
        res["notes"].append(str(exc).replace(path, os.path.basename(path)))
        return res
    except Exception as exc:  # pylint: disable=broad-except  (PyROOT >= 6.22 raises OSError on a bad file)
        res["notes"].append(f"{type(exc).__name__}: {exc}".replace(path, os.path.basename(path)))
        return res
    res["notes"] += [re.sub(r"^WARNING:\s*", "", l.strip()).replace(path, os.path.basename(path))
                     for l in buf.getvalue().splitlines() if l.strip()]
    res.update(best=best, lo=lo, hi=hi, npts=len(pts), rmin=pts[0][0], rmax=pts[-1][0])
    if lo is None or hi is None:
        res["notes"].append(f"2dNLL=1 crossing {'below' if lo is None else 'above'} the best fit is outside "
                            f"the scan range [{pts[0][0]:.3f}, {pts[-1][0]:.3f}]")
        return res
    res["sigma"] = 0.5 * (hi - lo)
    return res


def parse_summary(rundir):
    """Freeze lists and 3-decimal precisions from <rundir>/fit_summary.txt, or None.

    dict: path, freeze {scan name: freeze string}, fragments [raw header fragments],
    values {scan name: '0.685'}, syst {scan name: '0.181'} (syst of the block 'total vs <scan>')."""
    path = os.path.join(rundir, SUMMARY_FILE)
    if not os.path.isfile(path):
        return None
    res = {"path": path, "freeze": {}, "fragments": [], "values": {}, "syst": {}, "notes": []}
    block = None
    try:
        with open(path, errors="replace") as fh:
            for line in fh:
                m = SUMMARY_HEADER.match(line)
                if m:
                    block = m.group(1)
                    res["freeze"][block] = m.group(3).strip()
                    res["fragments"].append(f"({m.group(2)}: {m.group(3).strip()})")
                    continue
                m = SUMMARY_VALUE.match(line.rstrip())
                if m and block:
                    what, val = m.group(1), m.group(2)
                    if what == "total":
                        prev = res["values"].get("xsec")
                        if prev is not None and prev != val:
                            res["notes"].append(f"fit_summary.txt quotes two different totals ({prev} / {val})")
                        res["values"]["xsec"] = val
                    elif what == "stat-only":
                        res["values"][block] = val
                    else:
                        res["syst"][block] = val
    except OSError as exc:
        res["notes"].append(f"cannot read {SUMMARY_FILE}: {exc}")
    return res


def parse_card(rundir):
    """Nuisance lines of the datacard(s) datacard*.txt in rundir, by type (never raises)."""
    info = {"cards": [], "lnn": [], "shape": [], "rateparam": [], "other": [], "notes": []}
    for card in sorted(glob.glob(os.path.join(rundir, "datacard*.txt"))):
        info["cards"].append(os.path.basename(card))
        try:
            with open(card, errors="replace") as fh:
                for line in fh:
                    parts = line.split("#")[0].split()
                    if len(parts) < 2:
                        continue
                    name, kind = parts[0], parts[1]
                    if kind == "rateParam":
                        info["rateparam"].append(name)
                    elif kind.startswith("shape"):
                        info["shape"].append(name)
                    elif kind in ("lnN", "lnU", "gmN"):
                        info["lnn"].append(name)
                    elif kind in ("param", "extArg", "discrete", "group", "autoMCStats"):
                        info["other"].append(f"{name} ({kind})")
        except OSError as exc:
            info["notes"].append(f"cannot read {os.path.basename(card)}: {exc}")
    for k in ("lnn", "shape", "rateparam", "other"):
        info[k] = sorted(set(info[k]))
    return info


def mapping_notes(summary, card):
    """Check the parsed freeze lists against the card: [] when the mapping is confirmed."""
    notes = []
    if not card["cards"]:
        return ["no datacard*.txt in the run dir: freeze lists not checked against a card"]
    exp_stat = "allConstrainedNuisances" + ("," + ",".join(card["rateparam"]) if card["rateparam"] else "")
    if summary is not None:  # header fragments present: compare them with the card
        got_stat = summary["freeze"].get("xsecSTAT")
        if got_stat is None:
            notes.append("no '(paper stat-only: ...)' header in fit_summary.txt (xsecSTAT block missing)")
        elif set(got_stat.split(",")) != set(exp_stat.split(",")):
            notes.append(f"xsecSTAT freeze list '{got_stat}' differs from what the card implies ('{exp_stat}'): "
                         f"check the 'stat only' column")
        got_shapes = summary["freeze"].get("xsecSTATshapes")
        if got_shapes is None:
            notes.append("no '(July run-book stat-only: ...)' header in fit_summary.txt (xsecSTATshapes block missing)")
        elif set(got_shapes.split(",")) != set(card["shape"]):
            notes.append(f"xsecSTATshapes freeze list '{got_shapes}' differs from the card's shape nuisances "
                         f"('{','.join(card['shape'])}'): check the 'stat + 1% bkg norm' column")
    if card["rateparam"]:
        notes.append(f"card carries rateParam(s) {','.join(card['rateparam'])}: not a paper-spec card (free "
                     f"background normalization); xsecSTAT froze them too (still stat only), in xsecSTATshapes "
                     f"they float, so that column is 'stat + free bkg norm', not 'stat + 1% bkg norm'")
    if card["other"]:
        notes.append("card has further constrained terms: " + ", ".join(card["other"]))
    return notes


def collect_row(rundir):
    row = {"rundir": rundir, "exists": os.path.isdir(rundir), "scans": {}, "summary": None,
           "card": None, "mapping": [], "check": [], "notes": []}
    if not row["exists"]:
        return row
    for key, name, _, _ in COLS:
        path = os.path.join(rundir, SCAN_FILE.format(name))
        row["scans"][key] = read_scan(path) if os.path.isfile(path) else None
    row["summary"] = parse_summary(rundir)
    row["card"] = parse_card(rundir)
    row["mapping"] = mapping_notes(row["summary"], row["card"])
    # cross-check against the fit_precision.py printout tee'd to fit_summary.txt (3 decimals)
    if row["summary"] is not None:
        for key, name, _, _ in COLS:
            mine, ref = sigma_of(row, key), row["summary"]["values"].get(name)
            if mine is None or ref is None:
                continue
            if f"{100 * mine:.3f}" != ref:
                row["check"].append(f"{name}: {100 * mine:.3f} here vs {ref} in fit_summary.txt")
        row["notes"] += row["summary"]["notes"]
    row["notes"] += row["card"]["notes"]
    return row


def sigma_of(row, key):
    scan = row["scans"].get(key)
    return scan["sigma"] if scan else None


def run_base(args, ecm):
    base = args.base or os.path.join(PAPER, "S{ecm}", "combine")
    return os.path.abspath(base.format(ecm=ecm))


def collect(ecm, args):
    rows = []
    for key, label, template, group in ROWS:
        rundir = os.path.join(run_base(args, ecm), template.format(ecm=ecm) + args.suffix)
        row = collect_row(rundir)
        row.update(key=key, label=label, group=group, paper=PAPER_TABLE2[ecm][key])
        rows.append(row)
    return rows


# ----------------------------------------------------------------------------- output
def pct(x):
    return "n/a" if x is None else f"{100 * x:.3f}"


def quad(a, b):
    """sqrt(b^2 - a^2) in % as a string; '~0' when the argument is negative, 'n/a' when undefined."""
    if a is None or b is None:
        return "n/a"
    d = b * b - a * a
    return "~0" if d < 0 else f"{100 * d ** 0.5:.3f}"


def scan_summary(scan):
    if scan is None:
        return "none (file missing)"
    s = os.path.basename(scan["path"])
    if "best" in scan:
        s += f" (r={scan['best']:.4f}, {scan['npts']} pts in [{scan['rmin']:.3f}, {scan['rmax']:.3f}]"
        if scan["sigma"] is not None:
            s += f", 2dNLL=1 at [{scan['lo']:.4f}, {scan['hi']:.4f}] -> {100 * scan['sigma']:.3f}%"
        s += ")"
    for note in scan["notes"]:
        s += f" WARNING: {note}"
    return s


def energy_section(ecm, rows, base, suffix):
    out = [f"## sqrt(s) = {ecm} GeV", ""]
    out.append("| Channel | Paper total (stat) | " + " | ".join(c[2] for c in COLS) + " |")
    out.append("|---|---|" + "---|" * len(COLS))
    for row in rows:
        ptot, pstat = row["paper"]
        cells = " | ".join(pct(sigma_of(row, c[0])) for c in COLS)
        out.append(f"| {row['label']} | {ptot:.2f} ({pstat:.2f}) | {cells} |")
    out.append("")
    out.append("Quadrature decomposition (in %; c1 = stat only, c2 = stat + 1% bkg norm = the paper's total, "
               "c3 = + regular syst profiled (xsec); a negative argument prints '~0'):")
    out.append("")
    out.append("| Channel | 1% bkg-norm component sqrt(c2^2 - c1^2) | regular-syst component sqrt(c3^2 - c2^2) "
               "| full syst sqrt(c3^2 - c1^2) |")
    out.append("|---|---|---|---|")
    for row in rows:
        c1, c2, c3 = (sigma_of(row, k) for k in ("stat", "bkg", "total"))
        out.append(f"| {row['label']} | {quad(c1, c2)} | {quad(c2, c3)} | {quad(c1, c3)} |")
    out.append("")
    out += footnote(rows, base, suffix)
    out += sources(rows, base, suffix, ecm)
    return out


def footnote(rows, base, suffix):
    out = [f"Definitions ({base}/<dir>{suffix}/; freeze lists parsed from the fit_summary.txt header fragments "
           "'(paper stat-only: ...)' = xsecSTAT and '(July run-book stat-only: ...)' = xsecSTATshapes, which the "
           "drivers run_fit_leptonic.sh / run_fit_qq.sh / run_fit_combination.sh build from the card and tee there; "
           "checked against the lnN / shape / rateParam lines of the datacard in the run dir):", ""]
    out.append("- stat only = `xsecSTAT`: `--freezeParameters=allConstrainedNuisances[,<rateParams>]` - every "
               "constrained nuisance fixed, i.e. the 1% lnN background normalizations norm_* AND the shape "
               "nuisances (BES, MUSCALE / ELSCALE / JETSCALE, SQRTS); the paper-spec cards have no rateParam, so "
               "nothing but r floats = statistical only = the paper's stat-only ('obtained with the background "
               "normalization parameters fixed').")
    out.append("- stat + 1% bkg norm = `xsecSTATshapes`: `--freezeParameters=<the card's shape nuisances>` - only "
               "the shape nuisances fixed, the norm_* lnN (1%) float = the paper's quoted total (the 1% "
               "normalizations are the only nuisance parameters of the paper's fit, Sec. 5.3).")
    out.append("- + regular syst profiled = `xsec`: nothing frozen - BES, the lepton / jet momentum scale and "
               "sqrt(s) profiled in addition; beyond the paper's quoted precision (the paper evaluated these "
               "effects separately by repeating the fit with shifted inputs, 0.095% combined, Sec. 5.3).")
    out.append("")
    out.append("Per run dir (header as parsed; 'header = card: OK' = the parsed lists agree with the card):")
    out.append("")
    for row in rows:
        rel = os.path.basename(row["rundir"])
        if not row["exists"]:
            out.append(f"- {row['label']}: {rel} missing (not produced yet)")
            continue
        card = row["card"]
        cards = ",".join(card["cards"]) if card["cards"] else "no datacard*.txt"
        parts = []
        if row["summary"] is None:
            exp_stat = "allConstrainedNuisances" + ("," + ",".join(card["rateparam"]) if card["rateparam"] else "")
            parts.append(f"no {SUMMARY_FILE} (fits not finished?); the card implies xsecSTAT freeze "
                         f"'{exp_stat}' and xsecSTATshapes freeze '{','.join(card['shape'])}'")
            if row["mapping"]:
                parts.append("WARNING: " + "; ".join(row["mapping"]))
        else:
            fs = row["summary"]["freeze"]
            stat = fs.get("xsecSTAT")
            if stat is not None:
                nuis = [] if card["cards"] else ["no datacard*.txt to expand it"]
                if card["lnn"]:
                    nuis.append("lnN " + ",".join(card["lnn"]))
                if card["shape"]:
                    nuis.append("shape " + ",".join(card["shape"]))
                if card["cards"]:
                    nuis.append("rateParam " + ",".join(card["rateparam"]) if card["rateparam"] else "no rateParam")
                parts.append(f"xsecSTAT freeze '{stat}' (= {'; '.join(nuis)}) -> stat only")
            shapes = fs.get("xsecSTATshapes")
            if shapes is not None:
                parts.append(f"xsecSTATshapes freeze '{shapes}', norm_* float -> stat + 1% bkg norm")
            parts.append("xsec nothing frozen -> + regular syst profiled (beyond the paper)")
            parts.append("header = card: OK" if not row["mapping"] else "WARNING: " + "; ".join(row["mapping"]))
        out.append(f"- {row['label']} [{rel}/{cards}]: " + "; ".join(parts))
    out.append("")
    return out


def sources(rows, base, suffix, ecm):
    out = [f"Sources ({base}/<dir>{suffix}/; 'pts' = grid points of the scan, best-fit entry excluded):"]
    n_found = 0
    for row in rows:
        rel = os.path.basename(row["rundir"])
        notes = "".join(f" NOTE: {n}" for n in row["notes"])
        if not row["exists"]:
            out.append(f"- {row['label']}: {rel} missing (not produced yet){notes}")
            continue
        parts = [f"{name}: {scan_summary(row['scans'].get(key))}" for key, name, _, _ in COLS]
        if row["summary"] is None:
            parts.append(f"{SUMMARY_FILE}: missing, no cross-check")
        else:
            vals = row["summary"]["values"]
            quoted = ", ".join(f"{name} {vals[name]}" for _, name, _, _ in COLS if name in vals)
            syst = row["summary"]["syst"]
            if syst:
                quoted += "; syst " + "/".join(f"{syst[k]} (vs {k})" for k in ("xsecSTAT", "xsecSTATshapes") if k in syst)
            compared = [name for k, name, _, _ in COLS if sigma_of(row, k) is not None and name in vals]
            missing = [name for _, name, _, _ in COLS if name not in compared]
            if row["check"]:
                parts.append(f"{SUMMARY_FILE}: {quoted or 'no values'} -> MISMATCH: " + "; ".join(row["check"]))
            elif not compared:
                parts.append(f"{SUMMARY_FILE}: {quoted or 'no values'} -> nothing to compare")
            elif missing:
                parts.append(f"{SUMMARY_FILE}: {quoted} -> match for {', '.join(compared)} "
                             f"({', '.join(missing)} not comparable: n/a here or absent there)")
            else:
                parts.append(f"{SUMMARY_FILE}: {quoted} -> match")
        n_found += any(sigma_of(row, k) is not None for k, _, _, _ in COLS)
        out.append(f"- {row['label']} [{rel}]: " + "; ".join(parts) + notes)
    if n_found == 0:
        out.append(f"- no scan file found for {ecm} GeV (run the fits, or check --suffix / --base)")
    out.append("")
    return out


def tex_table(results, args, title):
    """Plain (booktabs-free) tabular in the layout of the paper's Table 2: rows = final states in the
    paper's groups, columns = per energy the paper value and the three definitions."""
    ecms = [e for e, _ in results]
    ncol = 1 + 4 * len(ecms)
    out = [f"% {oneline(title)}",
           f"% generated {datetime.date.today()} by table2.py from {PAPER} (run-dir suffix '{oneline(args.suffix)}'"
           + (f", base {oneline(args.base)}" if args.base else "") + ")",
           "% per energy: paper = Table 2 total (stat-only); stat = xsecSTAT (all constrained nuisances frozen) =",
           "% the paper's stat-only; stat+bkg = xsecSTATshapes (shape nuisances frozen, 1% lnN normalizations float)",
           "% = the paper's quoted total; +syst = xsec (nothing frozen: BES, momentum scale, sqrt(s) profiled in",
           "% addition - beyond the paper's quoted precision). Precision = half the 2*deltaNLL = 1 interval.",
           "% the \\providecommand lines are fallbacks for a standalone build; the paper's own macros win."]
    out += TEX_MACROS
    out += [r"\begin{table}[ht!]", r"\renewcommand{\arraystretch}{1.1}", r"\centering",
            (r"\caption{Relative uncertainties at the 68\% confidence level on the \ZH cross section "
             r"(in \%) from the reproduction, MVA-based configuration" + (f" ({tex_escape(args.label)})" if args.label else "")
             + r". For each center-of-mass energy: paper = published value (statistical only in "
             r"parentheses); stat = statistical only (the paper's stat-only definition); stat+bkg = statistical "
             r"plus the 1\% background-normalization uncertainties (the paper's quoted total); +syst = with, in "
             r"addition, the regular shape systematic uncertainties (beam energy spread, lepton or jet momentum "
             r"scale, $\sqrt{s}$) profiled, beyond the paper's quoted precision.}"),
            r"\vspace{0.5em}", r"\label{tab:results_xsec_repro}", "{\\footnotesize", r"\setlength{\tabcolsep}{4pt}",
            r"\begin{tabular}{l" + "|cccc" * len(ecms) + "}", r"\hline",
            f" & \\multicolumn{{{ncol - 1}}}{{c}}{{$\\delta\\sigma_{{\\mathrm{{ZH}}}}/\\sigma_{{\\mathrm{{ZH}}}}$ [\\%]}} \\\\",
            r"\hline"]
    head = " "
    for i, ecm in enumerate(ecms):
        align = "c|" if i < len(ecms) - 1 else "c"
        head += f" & \\multicolumn{{4}}{{{align}}}{{$\\sqrt{{s}} = {ecm}$~GeV}}"
    out.append(head + r" \\")
    sub = r"\textbf{Final state}"
    for _ in ecms:
        sub += " & paper (stat) & " + " & ".join(c[3] for c in COLS)
    out += [sub + r" \\", r"\hline"]
    last_group = None
    for i, (key, _, _, group) in enumerate(ROWS):
        if group is not None and group != last_group:
            if i > 0:
                out.append(r"\hline")
            out.append(f"\\multicolumn{{{ncol}}}{{l}}{{\\textbf{{{group}}}}} \\\\")
            last_group = group
        elif group is None:
            out.append(r"\hline")
        line = TEX_ROW[key]
        for _, rows in results:
            row = next(r for r in rows if r["key"] == key)
            ptot, pstat = row["paper"]
            line += f" & {ptot:.2f} ({pstat:.2f})"
            for c in COLS:
                line += " & " + pct(sigma_of(row, c[0]))
        out.append(line + r" \\")
    out += [r"\hline", r"\end{tabular}", "}", r"\end{table}"]
    out.append("% quadrature decomposition per energy (in %): 1% bkg-norm component sqrt(c2^2 - c1^2), "
               "shape-syst component sqrt(c3^2 - c2^2), full syst sqrt(c3^2 - c1^2)")
    for ecm, rows in results:
        for row in rows:
            c1, c2, c3 = (sigma_of(row, k) for k in ("stat", "bkg", "total"))
            out.append(f"%   {ecm} GeV {row['label']:<12} bkg-norm {quad(c1, c2):>6}  shape-syst {quad(c2, c3):>6}  "
                       f"full syst {quad(c1, c3):>6}")
    return out


def write(path, text):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text + "\n")
    print(f"[written to {path}]", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--suffix", default="", help="run-dir suffix, e.g. _oldbdt (original models); default none")
    ap.add_argument("--ecm", type=int, nargs="+", choices=(240, 365), default=[240, 365],
                    help="energies (default: both)")
    ap.add_argument("--out", metavar="FILE.md", help="also write the markdown to FILE.md")
    ap.add_argument("--tex", metavar="FILE.tex", help="write the table as a plain LaTeX tabular to FILE.tex")
    ap.add_argument("--label", default="", help="text prefixed to the title, e.g. 'original models'")
    ap.add_argument("--base", metavar="DIR",
                    help="parent of the run dirs, '{ecm}' substituted (default <Paper>/S{ecm}/combine, "
                         "the fit drivers' default FIT_BASE)")
    args = ap.parse_args()
    if any(ch.isspace() or ch == os.sep for ch in args.suffix):
        print(f"WARNING: --suffix {args.suffix!r} contains whitespace or '/', no run dir can match", file=sys.stderr)

    ecms = sorted(set(args.ecm))
    title = f"{args.label}: {TITLE}" if args.label else TITLE
    out = [f"# {title}", ""]
    out.append(f"Generated {datetime.date.today()} by table2.py from {PAPER} (run-dir suffix '{args.suffix}'"
               + (f", base {args.base}" if args.base else "") + "). Precision = half the distance between the "
               "2*deltaNLL = 1 crossings around the best fit (fit_precision.py logic), Asimov data, r = "
               "sigma_ZH / SM. 'Paper total (stat)' = Table 2 total (stat-only): the paper's total corresponds to "
               "the 'stat + 1% bkg norm' column (xsecSTATshapes, the 1% background normalizations being the only "
               "nuisance parameters of its fit) and its stat-only to the 'stat only' column (xsecSTAT); the "
               "'+ regular syst profiled' column (xsec) is beyond the paper's quoted precision. A missing run dir / "
               "scan / crossing gives n/a.")
    out.append("")
    results = []
    for ecm in ecms:
        rows = collect(ecm, args)
        results.append((ecm, rows))
        out += energy_section(ecm, rows, run_base(args, ecm), args.suffix)
    text = "\n".join(out)
    print(text)
    if args.out:
        write(args.out, text)
    if args.tex:
        write(args.tex, "\n".join(tex_table(results, args, title)))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:  # pylint: disable=broad-except  (never abort a chain: report, exit 0)
        traceback.print_exc()
        print("ERROR: table2.py failed (see the traceback above); exit code 0 by design", file=sys.stderr)
    sys.exit(0)
