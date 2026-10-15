#!/usr/bin/env python3
"""
Results collector for the ZH_XSec Paper reproduction (arXiv:2512.21290, JHEP version).

Reads every combine MultiDimFit grid scan of the reproduction at sqrt(s) = 240 and
365 GeV, derives the expected 1-sigma precision on sigma_ZH (half the distance
between the 2*deltaNLL = 1 crossings around the best fit, the fit_precision.py
logic) and prints a markdown comparison against the published Table 2 (MVA-based
configuration, "total (stat-only)" per channel; Table 1 in the arXiv v1 numbering).
The paper's two numbers map onto the reproduction's scans as: paper total <->
xsecSTATshapes (stat + the 1% background normalizations, the only nuisance parameters
of the paper's fit), paper stat-only <-> xsecSTAT (everything frozen = "background
normalization parameters fixed"); the xsec scan (BES, momentum scale, sqrt(s) profiled
in addition) is beyond the paper's quoted precision and is labelled as such. With
--cut-based (implied by a --suffix containing 'cutbased') the same run-dir names hold
the single-region cut-based fits (makeWS_recoil_2cat.py --single-region, makeWS_2D_qq.py
--recoil-only) and the paper's Cut-based columns are the reference.
The model-independence bias test (Sec 7.2, Table 3; Table 2 in arXiv v1) is tabulated
for all five paper columns (mumu, ee, ll, qq, combination) from the per-decay fit
files that bias_test_qq.py / bias_test_generic.py leave behind
(<rundir>/bias_<Hdecay>/higgsCombinebiastest.MultiDimFit.mH125.root), or from their
stdout logs (--bias-logs).

python3 + ROOT + stdlib only: runs in the key4hep env or inside the combine
container (./run_combine.sh python3 analysis/ZH_XSec/Paper/collect_results.py ...).

  python3 collect_results.py                       # live run dirs, both energies
  python3 collect_results.py --suffix .jul2026     # preserved July-2026 run dirs
  python3 collect_results.py --ecm 240 --out results_240.md
  python3 collect_results.py --bias-logs 240:bias_qq_240.log 365:bias_mumu_365.log
  python3 collect_results.py --base /some/scratch/S{ecm}/combine   # fits run with FIT_BASE=...

Run dirs read, per energy (<base>/<dir><suffix>/, base = S{ecm}/combine by default).
Paper-spec fits (primary rows):
  run_recoil_2cat_mumu / _ee           leptonic: recoil mass 100-150 GeV in two BDT regions,
                                       per-component 1% lnN backgrounds, signal = all ZH
                                       final states (makeWS_recoil_2cat.py)
  run_recoil_2cat_combined             Z(ll)H = ee + mumu
  run_2D_mrecoil_mjj_qq                hadronic 2D m_recoil x m_jj in two BDT regions, signal = all
                                       ZH final states, BES nuisance (makeWS_2D_qq.py, since 2026-09)
  run_{ecm}_all                        ee + mumu + qq combination
Cross-checks (July-2026 style: binned BDT-score fit, lumped background with a free rateParam):
  run_binned_BDTScore_ee / _mumu / _combined / _qq, run_{ecm}_all_bdt
  run_2D_mrecoil_mjj_qq_zhbkg          qq 2D with the July signal definition (Z(qq/ss/cc/bb)H signal
                                       only, other ZH as the background bkg_ZH, no BES;
                                       makeWS_2D_qq.py --zh-other-as-bkg)
The qq signal definition is DETECTED from the card in each run dir (a 'bkg_ZH' process = July
definition): a run_2D_mrecoil_mjj_qq<suffix> dir holding the July definition (the preserved
run_2D_mrecoil_mjj_qq.jul2026 does) is shown in the July-definition cross-check row, not in the
paper-spec qq row (n/a), and a combination card whose qq part is the July definition is marked
(double dagger). Its bias_H*/ fits (bias_test_qq.py: hadronic-Z per-decay templates) are
tabulated in the qq column with that origin noted.
Scan files higgsCombine<name>.MultiDimFit.mH125.root with <name> =
  xsec            everything profiled (+ the regular shape systematics BES, momentum
                  scale, sqrt(s)) - beyond the paper's quoted precision
  xsecSTAT        stat-only, paper definition (background normalizations fixed: all
                  constrained nuisances + all rateParams frozen)
  xsecSTATshapes  only the shape nuisances frozen, the background normalizations float
                  = the paper's quoted total (stat + 1% bkg norm for the paper-spec cards,
                  stat + a free normalization for the July-style cards; the July-2026
                  run-book called this scan 'stat-only')
The July combination dirs use xsecALL / xsecALLfine / xsecALLSTAT; a 'fine' scan is
preferred whenever both exist. A missing dir or file gives an 'n/a' cell. An xsecSTAT
scan that has no xsecSTATshapes companion in a dir whose datacard carries rateParams was
produced by a pre-September driver that froze only the shape nuisances: it is shown in
the paper-definition column but flagged (dagger) as the July definition. With
--suffix .jul2026 only the July-style rows exist; the paper-spec rows show n/a.

Bias test: bias = r_fit - (1 + X) in % of sigma_ZH, X = 5% for mumu/ee/ll and 1% for
qq/all (paper Sec 7.2; override with --bias-inject ch=X). Fit files are looked for in
the paper-spec run dir of each channel; a --bias-logs file replaces the fit files of
the (ecm, channel) blocks it contains. Log format (bias_test_qq.py / bias_test_generic.py):
  === bias test: channel=<name> X = <X>% ...      (bias_test_qq.py prints no channel= -> qq)
    Hbb      BR= 0.58240  r_fit=1.05012  bias=+0.012%
"""
import argparse
import contextlib
import datetime
import glob
import io
import os
import re
import sys

import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kWarning

PAPER = os.path.dirname(os.path.abspath(__file__))

# Precision logic shared with the per-energy fit scripts (S240 and S365 copies are
# identical); imported unchanged.
sys.path.insert(0, os.path.join(PAPER, "S240", "combine"))
from fit_precision import crossings, scan_points  # noqa: E402

# arXiv:2512.21290 (JHEP version) Table 2, MVA-based configuration: relative uncertainty
# on sigma_ZH in %, (total, stat-only). NB the arXiv v1 (Table 1) quoted totals only.
PAPER_TABLE2 = {
    240: {"ee": (0.81, 0.78), "mumu": (0.68, 0.66), "ll": (0.52, 0.50), "qq": (0.38, 0.30), "all": (0.31, 0.26)},
    365: {"ee": (1.91, 1.90), "mumu": (1.79, 1.79), "ll": (1.32, 1.30), "qq": (0.56, 0.47), "all": (0.52, 0.44)},
}
# The same table's Cut-based columns ("each final state is fitted in a single region, and the
# hadronic final state is fitted using only the recoil mass distribution", Sec. 6): the reference
# with --cut-based (run dirs of makeWS_recoil_2cat.py --single-region / makeWS_2D_qq.py --recoil-only)
PAPER_TABLE2_CUTBASED = {
    240: {"ee": (1.01, 0.97), "mumu": (0.84, 0.80), "ll": (0.64, 0.62), "qq": (1.20, 0.63), "all": (0.56, 0.44)},
    365: {"ee": (2.27, 2.16), "mumu": (2.11, 2.03), "ll": (1.56, 1.48), "qq": (1.42, 0.63), "all": (1.06, 0.58)},
}
# row labels of the primary rows under --cut-based (same run-dir names, one region)
CUTBASED_LABEL = {
    "mumu": "Z(mumu)H (recoil, single region)", "ee": "Z(ee)H (recoil, single region)",
    "ll": "Z(ll)H = ee+mumu (recoil, single region)", "qq": "Z(qq)H (recoil only, single region)",
    "all": "combination ee+mumu+qq (single regions)",
}
CHANNELS = ["mumu", "ee", "ll", "qq", "all"]
CHANNEL_LABEL = {"mumu": "Z(mumu)H", "ee": "Z(ee)H", "ll": "Z(ll)H", "qq": "Z(qq)H", "all": "combination"}
# Sec 7.2: injected relative shift X of the total sigma_ZH per channel
BIAS_X = {"mumu": 0.05, "ee": 0.05, "ll": 0.05, "qq": 0.01, "all": 0.01}
BIAS_ECM = 240  # energy of the paper's Table 3
# Table 3 (240 GeV): bias in % of sigma_ZH, columns (mumu, ee, ll, qq, combination)
PAPER_TABLE3_BIAS = {
    "bb":     (-0.01, +0.00, -0.01, +0.04, +0.02),
    "cc":     (+0.00, -0.02, -0.01, -0.08, -0.06),
    "ss":     (-0.01, -0.01, -0.01, -0.17, -0.12),
    "gg":     (+0.00, -0.03, -0.01, -0.04, -0.03),
    "mumu":   (+0.09, -0.01, +0.04, +0.26, +0.18),
    "tautau": (-0.01, -0.01, -0.01, -0.04, -0.03),
    "ZZ":     (+0.34, +0.33, +0.33, +0.02, +0.03),
    "WW":     (-0.01, -0.03, -0.02, -0.07, -0.05),
    "Za":     (+0.36, +0.32, +0.32, -0.17, -0.09),
    "aa":     (+0.00, -0.01, +0.00, +0.43, +0.28),
    "inv":    (+0.01, +0.01, +0.01, +0.51, +0.34),
}
MODE_FROM_H = {  # bias_test_*.py decay labels -> paper labels
    "Hbb": "bb", "Hcc": "cc", "Hss": "ss", "Hgg": "gg", "Hmumu": "mumu",
    "Htautau": "tautau", "HZZ": "ZZ", "HWW": "WW", "HZa": "Za", "Haa": "aa",
    "Hinv": "inv",
}
# channel names as bias_test_generic.py / run dirs may spell them -> paper column
CHANNEL_ALIASES = {"mumu": "mumu", "ee": "ee", "ll": "ll", "combined": "ll", "eemumu": "ll",
                   "qq": "qq", "all": "all", "combination": "all"}

# key, label, run-dir template, paper column, datacard name(s) used by the fit
# (glob; read only to find rateParams), primary (paper spec) or July-style cross-check
ROWS = [
    ("mumu",    "Z(mumu)H (recoil, 2 BDT regions)",        "run_recoil_2cat_mumu",       "mumu", "datacard*.txt",           True),
    ("ee",      "Z(ee)H (recoil, 2 BDT regions)",          "run_recoil_2cat_ee",         "ee",   "datacard*.txt",           True),
    ("ll",      "Z(ll)H = ee+mumu (recoil, 2 BDT regions)", "run_recoil_2cat_combined",  "ll",   "datacard*.txt",           True),
    ("qq",      "Z(qq)H (2D m_recoil x m_jj)",             "run_2D_mrecoil_mjj_qq",      "qq",   "datacard_2d_qq.txt",      True),
    ("all",     "combination ee+mumu+qq",                  "run_{ecm}_all",              "all",  "datacard_all.txt",        True),
    ("mumu_bdt", "Z(mumu)H (binned BDT score)",            "run_binned_BDTScore_mumu",   "mumu", "datacard_binned_mumu.txt", False),
    ("ee_bdt",  "Z(ee)H (binned BDT score)",               "run_binned_BDTScore_ee",     "ee",   "datacard_binned_ee.txt",  False),
    ("ll_bdt",  "Z(ll)H = ee+mumu (binned BDT score)",     "run_binned_BDTScore_combined", "ll", "datacard_combined.txt",   False),
    ("qq_zhbkg", "Z(qq)H 2D, ZH-other as bkg (July def.)",  "run_2D_mrecoil_mjj_qq_zhbkg", "qq",  "datacard_2d_qq*.txt",     False),
    ("qq_bdt",  "Z(qq)H (1D BDT score)",                   "run_binned_BDTScore_qq",     "qq",   "datacard_binned_qq.txt",  False),
    ("all_bdt", "combination ee+mumu+qq (BDT-score leptonic cards)", "run_{ecm}_all_bdt", "all", "datacard_all.txt",       False),
]
BIAS_RUNDIR = {"mumu": "run_recoil_2cat_mumu", "ee": "run_recoil_2cat_ee", "ll": "run_recoil_2cat_combined",
               "qq": "run_2D_mrecoil_mjj_qq", "all": "run_{ecm}_all"}
# scan kind -> base names in order of preference ("<base>fine" beats "<base>")
SCANS = {
    "total":  ["xsec", "xsecALL"],
    "stat":   ["xsecSTAT", "xsecALLSTAT"],
    "shapes": ["xsecSTATshapes", "xsecALLSTATshapes"],
}
SCAN_FILE = "higgsCombine{}.MultiDimFit.mH125.root"
BIAS_FILE = "higgsCombinebiastest.MultiDimFit.mH125.root"
DAGGER = "†"
DDAGGER = "‡"   # marks a combination whose qq part is the July signal definition
JULY_QQ_PROCESS = "bkg_ZH"   # process present only in the July-definition qq card
# bias-test channels that are cross-checks without a paper column: their log blocks are skipped
BIAS_SKIP_CHANNELS = {"qq-zhbkg"}

# bias_test_*.py stdout formats:
#   "=== bias test: channel=mumu X = 5% br=sample ..."  /  "=== bias test: X = 1% total-xsec ..." (block header;
#   the br=<mode> token of bias_test_generic.py sits after the X = <X>% the regex anchors on)
#   "  Hbb      BR= 0.58240  r_fit=1.01038  bias=+0.038%"   (per-mode line)
#   "  Hbb      +0.038%"                                     (summary block)
LOG_HEADER = re.compile(r"^===\s*bias test:\s*(?:channel\s*=\s*(\S+)\s+)?X\s*=\s*([0-9.]+)\s*%")
LOG_DETAIL = re.compile(r"^\s*(H\w+)\s+BR=\s*[0-9.eE+-]+\s+r_fit=\s*[0-9.eE+-]+\s+bias=\s*([+-]?[0-9.]+)%")
LOG_SUMMARY = re.compile(r"^\s*(H\w+)\s+([+-]?[0-9.]+)%\s*$")


# ----------------------------------------------------------------------------- scans
def find_scan(rundir, kind):
    """Path of the preferred scan file of this kind in rundir, or None."""
    for base in SCANS[kind]:
        for name in (base + "fine", base):
            path = os.path.join(rundir, SCAN_FILE.format(name))
            if os.path.isfile(path):
                return path
    return None


def scan_precision(path):
    """Precision from one MultiDimFit grid scan; never raises.

    Returns a dict: sigma (fraction, None when not determinable), best, lo, hi,
    npts, rmin, rmax, notes (warnings from the scan reader / crossing search).
    """
    res = {"path": path, "sigma": None, "notes": []}
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):  # fit_precision prints its warnings
            best, pts = scan_points(path)
            lo, hi = crossings(best, pts)
    except SystemExit as exc:  # fit_precision exits on unreadable / empty files
        res["notes"].append(str(exc))
        return res
    except Exception as exc:  # pylint: disable=broad-except
        res["notes"].append(f"{type(exc).__name__}: {exc}")
        return res
    res["notes"] += [re.sub(r"^WARNING:\s*", "", l.strip()) for l in buf.getvalue().splitlines() if l.strip()]
    res.update(best=best, lo=lo, hi=hi, npts=len(pts), rmin=pts[0][0], rmax=pts[-1][0])
    if lo is None or hi is None:
        res["notes"].append(
            f"2dNLL=1 crossing {'below' if lo is None else 'above'} the best fit is "
            f"outside the scan range [{pts[0][0]:.3f}, {pts[-1][0]:.3f}]")
        return res
    res["sigma"] = 0.5 * (hi - lo)
    return res


def card_rateparams(rundir, pattern):
    """Names of the rateParam lines of the datacard(s) matching pattern in rundir."""
    names = []
    for card in sorted(glob.glob(os.path.join(rundir, pattern))):
        try:
            with open(card, errors="replace") as fh:
                for line in fh:
                    parts = line.split("#")[0].split()
                    if len(parts) > 1 and parts[1] == "rateParam":
                        names.append(parts[0])
        except OSError:
            continue
    return sorted(set(names))


def card_processes(rundir, pattern):
    """Process names of the datacard(s) matching pattern in rundir (the first 'process' line)."""
    names = set()
    for card in sorted(glob.glob(os.path.join(rundir, pattern))):
        try:
            with open(card, errors="replace") as fh:
                for line in fh:
                    parts = line.split("#")[0].split()
                    if len(parts) > 1 and parts[0] == "process" and not parts[1].lstrip("-").isdigit():
                        names.update(parts[1:])
                        break
        except OSError:
            continue
    return names


def is_july_qq(rundir, pattern):
    """True when the card in rundir carries the July-definition qq process bkg_ZH."""
    return JULY_QQ_PROCESS in card_processes(rundir, pattern)


def run_base(args, ecm):
    """Parent of the run dirs for this energy (the fit scripts' FIT_BASE)."""
    base = args.base or os.path.join(PAPER, "S{ecm}", "combine")
    return os.path.abspath(base.format(ecm=ecm))


def collect(ecm, args):
    rows = []
    paper = PAPER_TABLE2_CUTBASED if args.cut_based else PAPER_TABLE2
    for key, label, template, pkey, card, primary in ROWS:
        if args.cut_based and primary:
            label = CUTBASED_LABEL.get(key, label)
        rundir = os.path.join(run_base(args, ecm), template.format(ecm=ecm) + args.suffix)
        row = {"key": key, "label": label, "primary": primary, "paper": paper[ecm][pkey],
               "rundir": rundir, "scans": {k: None for k in SCANS}, "rateparams": [],
               "stat_is_july": False, "july_qq": False, "notes": []}
        if os.path.isdir(rundir):
            for kind in SCANS:
                path = find_scan(rundir, kind)
                if path:
                    row["scans"][kind] = scan_precision(path)
            row["rateparams"] = card_rateparams(rundir, card)
            # a stat scan without the shapes companion comes from a pre-September driver
            # (run_fit_qq.sh, the July hand-run commands): only the shapes were frozen there
            row["stat_is_july"] = bool(row["scans"]["stat"] and not row["scans"]["shapes"]
                                       and row["rateparams"])
            # qq signal definition, from the card: bkg_ZH = July (ZH-other as background, no BES)
            row["july_qq"] = is_july_qq(rundir, card)
        rows.append(row)
    by_key = {r["key"]: r for r in rows}
    # the paper-spec qq row must hold the paper definition: a run_2D_mrecoil_mjj_qq<suffix> dir
    # with the July card (the preserved .jul2026 dir) is moved to the July-definition row
    qq, qq_july = by_key["qq"], by_key["qq_zhbkg"]
    if qq["july_qq"]:
        src = os.path.basename(qq["rundir"])
        if os.path.isdir(qq_july["rundir"]):
            qq["notes"].append(f"{src} holds the JULY qq definition (card has {JULY_QQ_PROCESS}) but "
                               f"{os.path.basename(qq_july['rundir'])} exists too: {src} is stale and ignored - "
                               "rebuild it with makeWS_2D_qq.py (paper spec)")
        else:
            qq_july["notes"].append(f"scans taken from {src}: its card carries {JULY_QQ_PROCESS}, i.e. the July "
                                    "signal definition (Z(qq/ss/cc/bb)H signal, other ZH as background, no BES)")
            for k in ("rundir", "scans", "rateparams", "stat_is_july"):
                qq_july[k] = qq[k]
            qq_july["july_qq"] = True
        qq["notes"].append(f"{src} holds the JULY qq definition (card has {JULY_QQ_PROCESS}): not a paper-spec "
                           "fit, shown in the cross-check row 'Z(qq)H 2D, ZH-other as bkg (July def.)'; rebuild "
                           "with makeWS_2D_qq.py (paper spec) for this row")
        qq["scans"] = {k: None for k in SCANS}
        qq["rateparams"] = []
        qq["stat_is_july"] = False
        qq["july_qq"] = False
    return rows


def sigma_of(row, kind):
    scan = row["scans"].get(kind)
    return scan["sigma"] if scan else None


# ------------------------------------------------------------------------------ bias
def best_fit_r(path):
    """r of the best-fit entry (quantileExpected == -1) of a MultiDimFit file."""
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        return None
    t = f.Get("limit")
    if not t or t.GetEntries() == 0:
        f.Close()
        return None
    r = None
    for i in range(t.GetEntries()):
        t.GetEntry(i)
        if t.quantileExpected == -1:
            r = float(t.r)
            break
    if r is None:  # no best-fit flag: bias_test_qq.py convention (entry 0)
        t.GetEntry(0)
        r = float(t.r)
    f.Close()
    return r


def parse_bias_log(path):
    """[(channel or None, X or None, {mode: bias %})] blocks of a bias_test_*.py stdout log.
    Lines before the first header form a block with channel None (old logs without one)."""
    blocks = []
    cur = None
    with open(path, errors="replace") as fh:
        for line in fh:
            m = LOG_HEADER.match(line)
            if m:
                cur = (m.group(1), float(m.group(2)) / 100.0, {})
                blocks.append(cur)
                continue
            m = LOG_DETAIL.match(line) or LOG_SUMMARY.match(line)
            if m:
                if cur is None:
                    cur = (None, None, {})
                    blocks.append(cur)
                cur[2][MODE_FROM_H.get(m.group(1), m.group(1))] = float(m.group(2))
    return [b for b in blocks if b[2]]


def bias_from_fits(rundir, inject):
    """({mode: bias %}, [unreadable-file notes]) from the bias_H*/ fit files left by
    bias_test_qq.py / bias_test_generic.py. A corrupt / empty fit file gives a note."""
    biases, problems = {}, []
    for h, mode in MODE_FROM_H.items():
        path = os.path.join(rundir, f"bias_{h}", BIAS_FILE)
        if not os.path.isfile(path):
            continue
        try:
            r = best_fit_r(path)
            note = "no fit result (empty or missing 'limit' tree)"
        except Exception as exc:  # pylint: disable=broad-except
            # PyROOT (>= 6.22) raises OSError from TFile.Open on an unreadable file
            r, note = None, f"{type(exc).__name__}: {exc}".replace(path, os.path.basename(path))
        if r is None:
            problems.append(f"bias_{h}: {note}")
            continue
        biases[mode] = (r - (1.0 + inject)) * 100.0
    return biases, problems


def parse_inject(specs):
    """--bias-inject values: 'ch=X' per channel, or a bare X for every channel."""
    inject = dict(BIAS_X)
    for spec in specs or []:
        if "=" in spec:
            ch, val = spec.split("=", 1)
            ch = CHANNEL_ALIASES.get(ch.strip())
            if ch is None:
                sys.exit(f"ERROR: --bias-inject: unknown channel in '{spec}' (use {', '.join(CHANNELS)})")
            inject[ch] = float(val)
        else:
            inject = {ch: float(spec) for ch in CHANNELS}
    return inject


def bias_sources(args, ecms, inject):
    """{(ecm, channel): {"biases": {mode: %}, "X": X, "origin": str}} from --bias-logs and,
    for every (ecm, channel) without a log, from the fit files in the paper-spec run dir."""
    sources = {}
    for spec in args.bias_logs or []:
        ecm, path = None, spec
        m = re.match(r"^(240|365):(.+)$", spec)
        if m:
            ecm, path = int(m.group(1)), m.group(2)
        else:
            m = re.search(r"(?<!\d)(240|365)(?!\d)", path)
            if m:
                ecm = int(m.group(1))
        if not os.path.isfile(path):
            print(f"WARNING: bias log not found, skipped: {path}", file=sys.stderr)
            continue
        if ecm is None:
            print(f"WARNING: cannot tell the energy of {path} (prefix it with 240: or 365:), skipped",
                  file=sys.stderr)
            continue
        blocks = parse_bias_log(path)
        if not blocks:
            print(f"WARNING: no bias lines recognised in {path}", file=sys.stderr)
            continue
        for raw_ch, x_log, biases in blocks:
            if (raw_ch or "").lower() in BIAS_SKIP_CHANNELS:
                print(f"NOTE: {path}: '{raw_ch}' bias block (July qq definition cross-check, no paper column) skipped",
                      file=sys.stderr)
                continue
            ch = CHANNEL_ALIASES.get((raw_ch or "qq").lower())
            if ch is None:
                print(f"WARNING: {path}: unknown channel '{raw_ch}' in a bias-test header, block skipped",
                      file=sys.stderr)
                continue
            x = x_log if x_log is not None else inject[ch]
            if abs(x - inject[ch]) > 1e-9:
                print(f"WARNING: {path}: {ch} block injected X={100*x:g}% (expected {100*inject[ch]:g}%); "
                      f"the paper compares at the expected value", file=sys.stderr)
            if (ecm, ch) in sources:
                print(f"WARNING: several bias-log blocks for {ch} @ {ecm} GeV; the last one wins", file=sys.stderr)
            sources[(ecm, ch)] = {"biases": biases, "X": x, "origin": f"log {path}"}
    for ecm, ch in sorted(sources):
        if ecm not in ecms:
            print(f"WARNING: bias-log block for {ch} @ {ecm} GeV ignored ({ecm} GeV not in --ecm)", file=sys.stderr)
    if not args.no_bias_fits:
        for ecm in ecms:
            for ch in CHANNELS:
                if (ecm, ch) in sources:
                    continue
                rundir = os.path.join(run_base(args, ecm), BIAS_RUNDIR[ch].format(ecm=ecm) + args.suffix)
                if not os.path.isdir(rundir):
                    continue
                biases, problems = bias_from_fits(rundir, inject[ch])
                for problem in problems:
                    print(f"WARNING: {rundir}: {problem} - mode skipped", file=sys.stderr)
                origin = os.path.basename(rundir) + "/bias_H*/"
                if ch == "qq" and is_july_qq(rundir, "datacard_2d_qq*.txt"):
                    origin += (f" (JULY qq definition: card carries {JULY_QQ_PROCESS}; per-decay templates over "
                               "Z(qq/ss/cc/bb)H only, bias_test_qq.py convention)")
                if problems:
                    origin += " (unreadable: " + "; ".join(problems) + ")"
                if biases:
                    sources[(ecm, ch)] = {"biases": biases, "X": inject[ch], "origin": origin}
    return sources


# ---------------------------------------------------------------------------- output
def pct(x, nd=3, mark=""):
    return "n/a" if x is None else f"{100 * x:.{nd}f}{mark}"


def ratio(x, ref):
    return "n/a" if x is None or not ref else f"{100 * x / ref:.2f}"


def syst_of(tot, stat):
    if tot is None or stat is None:
        return None
    d = tot * tot - stat * stat
    return d ** 0.5 if d > 0 else 0.0


def scan_summary(scan):
    if scan is None:
        return "none"
    s = os.path.basename(scan["path"])
    if "best" in scan:
        s += (f" (r={scan['best']:.4f}, {scan['npts']} pts in "
              f"[{scan['rmin']:.3f}, {scan['rmax']:.3f}]")
        if scan["sigma"] is not None:
            s += f", 2dNLL=1 at [{scan['lo']:.4f}, {scan['hi']:.4f}]"
        s += ")"
    for note in scan["notes"]:
        s += f" WARNING: {note}"
    return s


def precision_table(rows):
    """Paper value vs the reproduction in the paper's definitions (total = xsecSTATshapes, stat-only =
    xsecSTAT), the ratios, the background-normalization component, then the xsec scan (regular shape
    systematics profiled in addition: beyond the paper) and the full systematic component."""
    out = ["| Channel | Paper total (stat) | Repro total (paper def.: stat + bkg norm) | Repro stat (paper def.) "
           "| Ratio total | Ratio stat | bkg-norm syst sqrt(total^2 - stat^2) "
           "| + regular syst profiled (xsec, beyond the paper) | full syst sqrt(xsec^2 - stat^2) |",
           "|---|---|---|---|---|---|---|---|---|"]
    for row in rows:
        ptot, pstat = row["paper"]
        xsec, stat, shapes = (sigma_of(row, k) for k in ("total", "stat", "shapes"))
        mark = ""
        if row["stat_is_july"] and stat is not None:
            # pre-September driver: its xsecSTAT scan froze the shape nuisances only (rateParams floating),
            # i.e. it is the total of the paper's definition (with a free normalization) and no stat-only
            # scan exists in that dir
            shapes, stat, mark = stat, None, DAGGER
        label = row["label"] + (f" {DDAGGER}" if row["july_qq"] and row["key"] != "qq_zhbkg" and xsec is not None else "")
        full = syst_of(xsec, stat if stat is not None else shapes)
        out.append(f"| {label} | {ptot:.2f} ({pstat:.2f}) | {pct(shapes, mark=mark)} | {pct(stat)} "
                   f"| {ratio(shapes, ptot)}{mark if shapes is not None else ''} | {ratio(stat, pstat)} "
                   f"| {pct(syst_of(shapes, stat))} | {pct(xsec)} | {pct(full, mark=mark)} |")
    return out


def energy_section(ecm, rows, base, suffix, cut_based=False):
    out = [f"## sqrt(s) = {ecm} GeV", ""]
    primary = [r for r in rows if r["primary"]]
    xcheck = [r for r in rows if not r["primary"]]
    if cut_based:
        out.append("Cut-based fits (paper Table 2 'Cut-based': the recoil mass in a single region per final state, "
                   "the hadronic final state with the recoil mass only; makeWS_recoil_2cat.py --single-region / "
                   "makeWS_2D_qq.py --recoil-only):")
    else:
        out.append("Paper-spec fits (recoil mass in two BDT regions for the leptonic channels, "
                   "2D m_recoil x m_jj for qq):")
    out.append("")
    out += precision_table(primary)
    out.append("")
    out.append("Cross-checks (July-2026 style: binned BDT-score fits with a lumped free-rateParam background; "
               "qq 2D with the July signal definition, ZH-other as bkg_ZH, no BES):")
    out.append("")
    out += precision_table(xcheck)
    out.append("")
    flagged = [r for r in rows if r["stat_is_july"] and sigma_of(r, "stat") is not None]
    if flagged:
        out.append(f"{DAGGER} xsecSTAT scan without an xsecSTATshapes companion in a dir whose datacard "
                   f"carries rateParams ({'; '.join(r['key'] + ': ' + ','.join(r['rateparams']) for r in flagged)}): "
                   f"produced by a pre-September driver that froze only the shape nuisances (rateParams "
                   f"floating), i.e. the total of the paper's definition with a free instead of a 1% background "
                   f"normalization; shown in the 'Repro total (paper def.)' column, no stat-only scan exists for "
                   f"these rows ('Repro stat', 'Ratio stat' and 'bkg-norm syst' n/a; 'full syst' is taken "
                   f"against that scan).")
        out.append("")
    marked = [r for r in rows if r["july_qq"] and r["key"] != "qq_zhbkg" and sigma_of(r, "total") is not None]
    if marked:
        out.append(f"{DDAGGER} the qq part of this combination is the JULY signal definition (its card carries "
                   f"the {JULY_QQ_PROCESS} process: Z(qq/ss/cc/bb)H signal, other ZH as background, no BES), "
                   f"not the paper-spec qq card ({'; '.join(r['key'] for r in marked)}).")
        out.append("")
    n_found = sum(sigma_of(r, "total") is not None for r in rows)
    out.append(f"Sources ({base}/<dir>{suffix}/):")
    for row in rows:
        rel = os.path.basename(row["rundir"])
        notes = "".join(f" NOTE: {n}" for n in row["notes"])
        if not os.path.isdir(row["rundir"]):
            out.append(f"- {row['label']}: {rel} missing{notes}")
            continue
        if sigma_of(row, "total") is None and row["notes"] and row["key"] == "qq":
            out.append(f"- {row['label']}: n/a{notes}")
            continue
        parts = [f"{k}: {scan_summary(row['scans'][k])}" for k in SCANS]
        if row["rateparams"]:
            parts.append(f"card rateParams: {','.join(row['rateparams'])}")
        out.append(f"- {row['label']} [{rel}]: " + "; ".join(parts) + notes)
    if n_found == 0:
        out.append(f"- no scan file found for {ecm} GeV (run the fits, or pass --suffix)")
    out.append("")
    return out


def bias_section(sources, ecms, inject, cut_based=False):
    out = ["## Model-independence bias test (paper Sec 7.2, Table 3 at 240 GeV; bias = r_fit - (1+X) in % of sigma_ZH)", ""]
    out.append("Injection X = " + ", ".join(f"{ch} {100*inject[ch]:g}%" for ch in CHANNELS) + ".")
    out.append("")
    if cut_based:
        out.append("NOTE: the paper's Table 3 is MVA-based; bias tests found in the cut-based (single-region) run "
                   "dirs are a mechanics check of the one-bin cards, and their 'Delta vs paper' compares with the "
                   "MVA-based paper column for reference only.")
        out.append("")
    missing = []
    for ci, ch in enumerate(CHANNELS):
        avail = [ecm for ecm in ecms if (ecm, ch) in sources]
        if not avail:
            missing.append(ch)
            continue
        out.append(f"### {CHANNEL_LABEL[ch]} (X = {100*inject[ch]:g}%)")
        out.append("")
        header = f"| H decay | Paper ({BIAS_ECM}) |"
        sep = "|---|---|"
        for ecm in avail:
            header += f" Repro {ecm} |"
            sep += "---|"
            if ecm == BIAS_ECM:
                header += " Delta vs paper |"
                sep += "---|"
        out += [header, sep]
        for mode, vals in PAPER_TABLE3_BIAS.items():
            paper = vals[ci]
            line = f"| {mode} | {paper:+.2f} |"
            for ecm in avail:
                b = sources[(ecm, ch)]["biases"].get(mode)
                line += " n/a |" if b is None else f" {b:+.3f} |"
                if ecm == BIAS_ECM:
                    line += " n/a |" if b is None else f" {b - paper:+.3f} |"
            out.append(line)
        out.append("")
        for ecm in avail:
            src = sources[(ecm, ch)]
            biases = src["biases"]
            worst = max(biases, key=lambda m: abs(biases[m]))
            line = (f"- {ecm} GeV: {len(biases)} modes from {src['origin']} (X = {100*src['X']:g}%); "
                    f"largest |bias| {worst} ({biases[worst]:+.3f}%)")
            if ecm == BIAS_ECM:
                deltas = {m: biases[m] - PAPER_TABLE3_BIAS[m][ci] for m in biases if m in PAPER_TABLE3_BIAS}
                if deltas:
                    wd = max(deltas, key=lambda m: abs(deltas[m]))
                    line += f"; largest |delta vs paper| {wd} ({deltas[wd]:+.3f}%)"
            out.append(line)
        out.append("")
    if missing:
        out.append("- no bias-test input for: " + ", ".join(CHANNEL_LABEL[ch] for ch in missing)
                   + " (run bias_test_qq.py / bias_test_generic.py so that <rundir>/bias_H*/ exist, or pass --bias-logs)")
        out.append("")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--suffix", default="", help="run-dir suffix, e.g. .jul2026 for the preserved July-2026 dirs")
    ap.add_argument("--base", metavar="DIR",
                    help="parent of the run dirs, '{ecm}' substituted (default: <Paper>/S{ecm}/combine, "
                         "the fit scripts' default FIT_BASE)")
    ap.add_argument("--ecm", type=int, nargs="+", choices=(240, 365), default=[240, 365],
                    help="energies to collect (default: both)")
    ap.add_argument("--out", metavar="FILE", help="also write the markdown to FILE")
    ap.add_argument("--bias-logs", nargs="+", metavar="[ECM:]FILE",
                    help="bias_test_qq.py / bias_test_generic.py stdout logs; prefix 240: / 365: "
                         "(else inferred from the path); the channel comes from the log header")
    ap.add_argument("--bias-inject", nargs="+", metavar="[CH=]X",
                    help="injected relative xsec shift used for the fit-file fallback, per channel "
                         "(default " + " ".join(f"{c}={x}" for c, x in BIAS_X.items()) + "); a bare X applies to all")
    ap.add_argument("--no-bias-fits", action="store_true",
                    help="do not fall back to the bias_H*/ fit files when no log is given")
    ap.add_argument("--cut-based", action="store_true",
                    help="the run dirs hold the single-region cut-based fits: compare with the paper's Cut-based "
                         "columns (implied by a --suffix containing 'cutbased')")
    args = ap.parse_args()
    args.cut_based = args.cut_based or "cutbased" in args.suffix

    ecms = sorted(set(args.ecm))
    inject = parse_inject(args.bias_inject)
    cfg = "Cut-based" if args.cut_based else "MVA-based"
    out = [f"# ZH_XSec Paper reproduction vs arXiv:2512.21290 (JHEP Table 2, {cfg} configuration)", ""]
    out.append(f"Generated {datetime.date.today()} by collect_results.py from {PAPER} "
               f"(run-dir suffix '{args.suffix or ''}'"
               + (", cut-based single-region fits" if args.cut_based else "") + "). All numbers are relative "
               f"uncertainties on sigma_ZH in %; precision = half the distance between the "
               f"2*deltaNLL = 1 crossings around the best fit (fit_precision.py logic); ratios = "
               f"reproduction / paper. 'Paper total (stat)' = Table 2, {cfg} column, total (stat-only). "
               f"Mapping: 'Repro total (paper def.)' = xsecSTATshapes (only the shape nuisances frozen, the "
               f"background normalizations float = stat + the 1% lnN normalizations, the only nuisance "
               f"parameters of the paper's fit - Sec. 5.3: 'each with a normalization uncertainty of 1% included "
               f"as a nuisance parameter in the fit', 'Shape uncertainties are not included as nuisance "
               f"parameters'; for the July-style cross-check cards the normalization is a free rateParam "
               f"instead); 'Repro stat (paper def.)' = xsecSTAT (all constrained nuisances + all rateParams "
               f"frozen, i.e. background normalizations fixed - the paper's stat-only); bkg-norm syst = "
               f"sqrt(total^2 - stat^2) in these definitions. '+ regular syst profiled' = xsec (nothing frozen: "
               f"BES, the lepton / jet momentum scale and sqrt(s) profiled in addition) - beyond the paper's "
               f"quoted precision, which evaluated these effects separately (0.095% combined, Sec. 5.3); full "
               f"syst = sqrt(xsec^2 - stat^2).")
    if "jul2026" in args.suffix:
        out.append("")
        out.append("Note: the preserved July-2026 dirs hold only the binned BDT-score leptonic fits and "
                   "predate the xsecSTAT/xsecSTATshapes split, so the paper-spec leptonic rows are n/a "
                   "and the July run_<ecm>_all dir (leptonic BDT-score cards + qq 2D) appears under the "
                   "paper-spec combination row; their xsecSTAT (xsecALLSTAT) scans froze the shape "
                   "nuisances only (background rateParams floating; flagged with " + DAGGER + "), except the "
                   "qq 2D fit whose card has no rateParam and whose five norm_* nuisances were frozen "
                   "(= paper definition). The July qq 2D fit (run_2D_mrecoil_mjj_qq.jul2026) used the "
                   "JULY signal definition - Z(qq/ss/cc/bb)H signal, ZH with a non-hadronic Z as the "
                   "background bkg_ZH, no BES nuisance (detected from its card) - so it is shown in the "
                   "cross-check row 'Z(qq)H 2D, ZH-other as bkg (July def.)' and the paper-spec qq row "
                   "(signal = all ZH final states + BES, makeWS_2D_qq.py since 2026-09) is n/a; the July "
                   "combination's qq part is that definition too (" + DDAGGER + "). Its qq bias-test "
                   "fits (bias_test_qq.py, hadronic-Z per-decay templates) fill the qq bias column.")
    out.append("")
    for ecm in ecms:
        out += energy_section(ecm, collect(ecm, args), run_base(args, ecm), args.suffix, args.cut_based)
    out += bias_section(bias_sources(args, ecms, inject), ecms, inject, args.cut_based)

    text = "\n".join(out)
    print(text)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w") as fh:
            fh.write(text + "\n")
        print(f"[written to {args.out}]", file=sys.stderr)


if __name__ == "__main__":
    main()
