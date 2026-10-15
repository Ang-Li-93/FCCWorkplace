#!/usr/bin/env python3
"""
Model-independence bias test (arXiv:2512.21290 Sec. 7.2) for ANY fit setup built
here, ecm 240: generalizes bias_test_qq.py to the paper-spec leptonic fits and the
combined cards.

The branching ratio of each Higgs decay mode h is perturbed individually by a fixed
amount chosen such that the TOTAL ZH cross section shifts by the relative amount X
(paper: 5% for mumu / ee / ll, 1% for qq and the full combination): the mode-h
signal template is scaled by (1 + X/BR_h) in the pseudo-data of every bin, the
nominal fit (identical templates and nuisances) is rerun on each pseudo-dataset and
the bias is reported as r_fit - (1+X), in percent of sigma_ZH (paper Table 3).

  python3 bias_test_generic.py <mumu|ee|ll|qq|qq-zhbkg|all> [--x X] [--decays Hbb,Hgg,...]
                               [--br sample|table] [--synthetic-by-decay] [--tag SUFFIX]
                               [FIT_BASE=<dir>, RUNDIR_SUFFIX / QQ_RUNDIR_SUFFIX=<sfx>, as the fit drivers]
Run INSIDE the combine container (./run_combine.sh ...), AFTER the nominal fit setup:
  mumu | ee   run_recoil_2cat_<flavor>/datacard_recoil_2cat_<flavor>.txt  (makeWS_recoil_2cat.py)
  ll          run_recoil_2cat_combined/datacard_combined.txt   (run_fit_combination.sh ll recoil)
  qq          run_2D_mrecoil_mjj_qq/datacard_2d_qq.txt         (makeWS_2D_qq.py: paper spec, signal =
              all ZH final states, per-decay templates summed over ALL 8 Z decays - the paper
              perturbs the Z(qq)H, Z(tautau)H, Z(nunu)H, Z(ll)H parts alike); a run dir written
              by 'makeWS_2D_qq.py --jesjer|--jes-only|--jer-only' holds datacard_2d_qq_jesjer.txt
              instead (JES / JER shape nuisances on every process), which is then used
  qq-zhbkg    run_2D_mrecoil_mjj_qq_zhbkg/datacard_2d_qq_zhbkg.txt (makeWS_2D_qq.py --zh-other-as-bkg:
              July-2026 definition, hadronic-Z signal only = bias_test_qq.py's convention; a
              cross-check, not a paper column - collect_results.py skips its block)
  all         run_<ecm>_all/datacard_all.txt                   (run_fit_combination.sh all recoil)
--tag SUFFIX: the run-dir suffix of a variant, applied to the chosen channel's run dir:
run_recoil_2cat_{mumu,ee,combined}<SUFFIX> (makeWS_recoil_2cat.py --tag, RUNDIR_SUFFIX of the
fit drivers), run_2D_mrecoil_mjj_qq[_zhbkg]<SUFFIX> (makeWS_2D_qq.py --tag, QQ_RUNDIR_SUFFIX of
the fit drivers, e.g. _nott: 365 GeV without the ttbar template) and run_<ecm>_all<SUFFIX>
(run_fit_combination.sh names it run_<ecm>_all<RUNDIR_SUFFIX><QQ_RUNDIR_SUFFIX>, identical
suffixes not doubled, or run_<ecm>_all<ALL_RUNDIR_SUFFIX> when that variable is set). Default:
the drivers' environment - $RUNDIR_SUFFIX for mumu/ee/ll, $QQ_RUNDIR_SUFFIX for qq/qq-zhbkg,
$ALL_RUNDIR_SUFFIX if set else their concatenation (identical suffixes not doubled) for all -
else none.

Per-decay templates: the card's shapes lines are parsed (combine's own lookup order:
exact bin then '*', exact process then '*') to learn, for every bin, the shapes file
and the histogram naming pattern; the bin's data_obs is that pattern with
$PROCESS=data_obs, and its mode-h template is the pattern with $PROCESS=sig_<h> read
from signal_by_decay.root NEXT TO that bin's shapes file (so a combined card takes
each channel's own per-decay templates: <cat>_sig_<h> of run_recoil_2cat_<flavor>/
and of run_2D_mrecoil_mjj_qq/, whatever the combined bin is called). Paths are
never hard-coded. For each decay a copy of the card is written to bias_<h>/ with
modified copies of every referenced shapes file (data_obs += X/BR_h x sig_h), then
text2workspace + MultiDimFit --algo singles, exactly as bias_test_qq.py.
--synthetic-by-decay: MECHANICS CHECK ONLY - for bins whose signal_by_decay.root is
missing, sig_h := BR_h x nominal signal template, which makes every bias trivially
~0 (the injection is then exactly X x signal). Used for the July-data tests where the
exclusive samples do not exist; never for physics numbers. So that such a run can never
be mistaken for a physics result, its fit files go to bias_synthetic_<h>/ (not the
bias_<h>/ that collect_results.py reads) and its header says channel=<name>-synthetic
(unknown to collect_results.py, which then skips the block).

Branching ratios BR_h (--br; the injection scales sig_h by X/BR_h):
  sample (DEFAULT)  BR_h = sum_z sigma(wzp6_ee_<z>H_<h>_ecm<ecm>) / sum_{z,h'} sigma(wzp6_ee_<z>H_<h'>)
                    over the 8 Z decays x 11 H decays of the winter2023 exclusive sets, read
                    from FCCee_procDict_winter2023_IDEA.json (looked up in $FCCDICTSDIR, a
                    colon-separated list as the FCCAnalyses setup exports it, then in
                    /cvmfs/fcc.cern.ch/FCCDicts; the combine container sees cvmfs). These are
                    the BRs the templates actually carry: sig_h is normalized to the exclusive
                    cross sections of the very same sets (signal_by_decay.root of
                    makeWS_recoil_2cat.py / makeWS_2D_qq.py), so X/BR_h x sig_h is exactly an
                    X shift of the generated sigma_ZH and sum_h BR_h = 1. nunuH_Hinv has no
                    template (zero acceptance) but stays in the cross-section sums: it is part
                    of sigma(ZH, H->inv), and a set with zero acceptance contributes nothing to
                    sig_Hinv either way - dropped from the sums, BR_Hinv would fall from
                    0.00105 to 0.00081 and the Hinv injection be 30% too large.
  table             the SM table of bias_test_qq.py (mH = 125 GeV; H->inv ~ ZZ*->4nu), the
                    convention of the July-2026 logs. The sample fractions differ from it by
                    up to 0.6% for the dominant modes (HWW 0.2147 vs 0.2137, HZZ 0.0263 vs
                    0.0262) and by 4% for Hss (0.000239 vs 0.00025), so the injection is
                    X x BR_sample/BR_table instead of X: at X = 5% an apparent bias of -0.2%
                    for Hss (ee @ 240: -0.24% observed vs -0.01 in paper Table 3) and of
                    +-0.03% for HWW / HZZ, which 'sample' removes.
The log header prints both sets and their ratio per decay (all 11, whatever --decays).

Prints, for log parsers (collect_results.py), exactly the bias_test_qq.py formats
(the header's 'br=<mode>' token sits after the X = <X>% that the parser anchors on):
  === bias test: channel=<name> X = <X>% br=<mode> total-xsec injection per decay mode ===
    Hbb      BR= 0.58240  r_fit=1.05012  bias=+0.012%
  Summary block, and 'Largest |bias|'.
"""
import argparse
import json
import os
import subprocess
import sys

import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.TH1.AddDirectory(False)

_ecm = "240"   # the S365 copy differs only in this line and the header

# --br table: SM branching ratios (mH = 125 GeV); H->inv approximated by ZZ*->4nu (bias_test_qq.py)
BR_TABLE = {
    "Hbb": 0.5824, "HWW": 0.2137, "Hgg": 0.0818, "Htautau": 0.0627,
    "Hcc": 0.0289, "HZZ": 0.02619, "Haa": 0.00227, "HZa": 0.001533,
    "Hmumu": 0.000218, "Hss": 0.00025, "Hinv": 0.00106,
}
# --br sample: cross-section fractions of the winter2023 exclusive sets wzp6_ee_<z>H_<h>_ecm<ecm>
# over these Z decays (the sets behind signal_by_decay.root; see the docstring on nunuH_Hinv)
_z_all = ["ee", "mumu", "tautau", "nunu", "qq", "ss", "cc", "bb"]
PROCDICT = "FCCee_procDict_winter2023_IDEA.json"
DICTS_DEFAULT = "/cvmfs/fcc.cern.ch/FCCDicts"

# channel -> (run dir, card, default X, producer hint)
SETUPS = {
    "mumu": ("run_recoil_2cat_mumu",     "datacard_recoil_2cat_mumu.txt", 0.05, "python3 makeWS_recoil_2cat.py mumu (key4hep env)"),
    "ee":   ("run_recoil_2cat_ee",       "datacard_recoil_2cat_ee.txt",   0.05, "python3 makeWS_recoil_2cat.py ee (key4hep env)"),
    "ll":   ("run_recoil_2cat_combined", "datacard_combined.txt",         0.05, "./run_fit_combination.sh ll recoil"),
    "qq":   ("run_2D_mrecoil_mjj_qq",    "datacard_2d_qq.txt",            0.01, "python3 makeWS_2D_qq.py (key4hep env)"),
    "qq-zhbkg": ("run_2D_mrecoil_mjj_qq_zhbkg", "datacard_2d_qq_zhbkg.txt", 0.01, "python3 makeWS_2D_qq.py --zh-other-as-bkg (key4hep env)"),
    "all":  (f"run_{_ecm}_all",          "datacard_all.txt",              0.01, "./run_fit_combination.sh all recoil"),
}
HERE = os.path.dirname(os.path.abspath(__file__))
BY_DECAY_FILE = "signal_by_decay.root"


# ------------------------------------------------------------------ datacard parsing
def parse_card(path):
    """(bins, shapes) of a datacard; shapes = [(process, bin, file, nominal, syst)]."""
    bins, shapes = [], []
    with open(path) as fh:
        for raw in fh:
            l = raw.split("#")[0].strip()
            if not l or l.startswith("--"):
                continue
            f = l.split()
            if f[0] == "shapes":
                if len(f) < 5:
                    sys.exit(f"ERROR: malformed shapes line in {path}: {raw.rstrip()}")
                shapes.append((f[1], f[2], f[3], f[4], f[5] if len(f) > 5 else None))
            elif f[0] == "bin" and not bins:
                for b in f[1:]:          # first 'bin' line = observation bins
                    if b not in bins:
                        bins.append(b)
    if not bins:
        sys.exit(f"ERROR: no 'bin' line in {path}")
    if not shapes:
        sys.exit(f"ERROR: no shapes line in {path} (counting card?)")
    return bins, shapes


def shape_entry(shapes, bin_, process, card):
    """The shapes line combine uses for (bin, process): exact bin else '*', then exact process else '*'."""
    for b in (bin_, "*"):
        entries = [s for s in shapes if s[1] == b]
        if not entries:
            continue
        for p in (process, "*"):
            for s in entries:
                if s[0] == p:
                    return s
        sys.exit(f"ERROR: {card}: no shapes line for process '{process}' in bin '{bin_}'")
    sys.exit(f"ERROR: {card}: no shapes line for bin '{bin_}'")


def expand(pattern, bin_, process):
    return pattern.replace("$CHANNEL", bin_).replace("$PROCESS", process).replace("$MASS", "125")


def resolve(path, card_dir):
    return path if os.path.isabs(path) else os.path.normpath(os.path.join(card_dir, path))


def get_hist(fname, key, cache):
    if fname not in cache:
        f = ROOT.TFile.Open(fname)
        if not f or f.IsZombie():
            sys.exit(f"ERROR: cannot open {fname}")
        cache[fname] = f
    h = cache[fname].Get(key)
    if not h:
        sys.exit(f"ERROR: histogram '{key}' not found in {fname}")
    return h


# --------------------------------------------------------------------- branching ratios
def find_procdict():
    """Path of PROCDICT: first hit in $FCCDICTSDIR (colon-separated list, as the FCCAnalyses
    setup exports it - the lookup of process_sig_bkg_samples_for_xgb.py), then the cvmfs
    default; None if nowhere."""
    dirs = [d for d in os.environ.get("FCCDICTSDIR", "").split(":") if d] + [DICTS_DEFAULT]
    for d in dirs:
        cand = os.path.join(d, PROCDICT)
        if os.path.isfile(cand):
            return cand
    return None


def sample_br(strict):
    """({h: BR_h}, procDict path) from the winter2023 exclusive-sample cross sections:
    sum over the 8 Z decays of sigma(wzp6_ee_<z>H_<h>_ecm<ecm>) divided by the sum over all
    8 x 11 sets (nunuH_Hinv included: part of sigma(ZH, H->inv), zero acceptance - see the
    docstring). When the procDict is not visible, unreadable or incomplete: abort if strict
    (--br sample needs it), else a WARNING and (None, path-or-None) - --br table needs no
    procDict, so a procDict problem must never stop a table-mode run."""
    path = find_procdict()
    if path is None:
        if strict:
            sys.exit(f"ERROR: {PROCDICT} not found in $FCCDICTSDIR ({os.environ.get('FCCDICTSDIR', '')!r}) "
                     f"nor in {DICTS_DEFAULT} - needed for --br sample (cvmfs not visible?); --br table needs no procDict")
        return None, None
    problem = None
    try:
        with open(path) as fh:
            d = json.load(fh)
        if not isinstance(d, dict):
            raise ValueError("not a JSON object")
    except (OSError, ValueError) as e:
        d, problem = {}, f"cannot read {path}: {e}"
    xs, missing = {}, []
    for h in BR_TABLE:
        xs[h] = 0.0
        for z in _z_all:
            p = f"wzp6_ee_{z}H_{h}_ecm{_ecm}"
            if p not in d or not isinstance(d[p], dict) or "crossSection" not in d[p]:
                missing.append(p)
                continue
            xs[h] += float(d[p]["crossSection"])
    tot = sum(xs.values())
    if problem is None and missing:
        problem = f"{len(missing)} exclusive ZH sets without a cross section in {path}: {missing}"
    if problem is None and not tot > 0:
        problem = f"zero total cross section from {path}"
    if problem is not None:
        if strict:
            sys.exit(f"ERROR: {problem} - needed for --br sample; --br table needs no procDict")
        print(f"WARNING: {problem} - sample BR set not shown (--br table does not need it)")
        return None, path
    return {h: xs[h] / tot for h in BR_TABLE}, path


# ------------------------------------------------------------------------------- fit
def best_fit_r(carddir, card, rrange):
    """text2workspace + MultiDimFit best fit on the card's OWN data_obs (as bias_test_qq.py)."""
    subprocess.check_call(f"text2workspace.py {card} -o ws.root", shell=True, cwd=carddir,
                          stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    subprocess.check_call(
        f"combine -M MultiDimFit --algo singles --setParameterRanges {rrange} ws.root "
        "-m 125 --cminDefaultMinimizerStrategy 0 -n biastest > combine.log 2>&1", shell=True, cwd=carddir)
    f = ROOT.TFile.Open(f"{carddir}/higgsCombinebiastest.MultiDimFit.mH125.root")
    t = f.Get("limit") if f and not f.IsZombie() else None
    if not t or t.GetEntries() == 0:
        sys.exit(f"ERROR: fit produced no result in {carddir} (see combine.log)")
    t.GetEntry(0)  # best-fit entry
    r = float(t.r)
    f.Close()
    if r <= 0.5:
        sys.exit(f"ERROR: fit failed in {carddir} (r={r}); see combine.log")
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("channel", choices=list(SETUPS))
    ap.add_argument("--x", type=float, metavar="X", help="injected relative shift of sigma_ZH (default: 0.05 mumu/ee/ll, 0.01 qq/qq-zhbkg/all)")
    ap.add_argument("--decays", metavar="LIST", help="comma-separated subset of H decays (default: all 11)")
    ap.add_argument("--br", choices=("sample", "table"), default="sample",
                    help="BR_h of the injection X/BR_h: 'sample' (default) = cross-section fractions of the "
                         f"winter2023 exclusive ZH sets ({PROCDICT}), 'table' = the SM table (July-2026 convention)")
    ap.add_argument("--synthetic-by-decay", action="store_true",
                    help="MECHANICS CHECK: bins without signal_by_decay.root use BR_h x nominal signal")
    ap.add_argument("--base", metavar="DIR", default=os.environ.get("FIT_BASE", HERE),
                    help="parent of the run dirs (default: $FIT_BASE or this dir)")
    ap.add_argument("--tag", metavar="SUFFIX", default=None,
                    help="run-dir suffix of a variant, applied to the channel's run dir (run_recoil_2cat_<..><SUFFIX>, "
                         "run_2D_mrecoil_mjj_qq[_zhbkg]<SUFFIX>, run_<ecm>_all<SUFFIX>; makeWS_*.py --tag / "
                         "RUNDIR_SUFFIX and QQ_RUNDIR_SUFFIX of the fit drivers; default: $RUNDIR_SUFFIX for "
                         "mumu/ee/ll, $QQ_RUNDIR_SUFFIX for qq/qq-zhbkg, $ALL_RUNDIR_SUFFIX if set else both "
                         "concatenated for all, else none)")
    args = ap.parse_args()

    rd, card, x_default, hint = SETUPS[args.channel]
    X = args.x if args.x is not None else x_default
    if X <= 0:
        sys.exit("ERROR: --x must be positive")
    if args.tag is None:   # the fit drivers' convention: leptonic suffix, qq suffix, both for the combination
        lep, qq = os.environ.get("RUNDIR_SUFFIX", ""), os.environ.get("QQ_RUNDIR_SUFFIX", "")
        if args.channel == "all":
            all_sfx = os.environ.get("ALL_RUNDIR_SUFFIX")   # explicit output-dir suffix of run_fit_combination.sh
            args.tag = all_sfx if all_sfx is not None else (lep + qq if qq != lep else lep)
        else:
            args.tag = qq if args.channel.startswith("qq") else lep
    if args.tag and (os.sep in args.tag or any(c.isspace() for c in args.tag)):
        sys.exit(f"ERROR: --tag {args.tag!r} must be a plain name fragment (no path separator or whitespace)")
    suffix = args.tag
    rundir = os.path.join(os.path.abspath(args.base), rd + suffix)
    cardpath = os.path.join(rundir, card)
    if args.channel == "qq" and not os.path.isfile(cardpath) and os.path.isfile(os.path.join(rundir, "datacard_2d_qq_jesjer.txt")):
        card = "datacard_2d_qq_jesjer.txt"   # makeWS_2D_qq.py --jesjer|--jes-only|--jer-only run dir: JES/JER nuisances
        cardpath = os.path.join(rundir, card)
        print(f"NOTE: {rundir} holds {card} (JES/JER shape nuisances): the bias test runs on that card")
    if not os.path.isfile(cardpath):
        sys.exit(f"ERROR: {cardpath} missing - run '{hint}' first"
                 + (f" (variant suffix {suffix!r}: makeWS --tag / RUNDIR_SUFFIX / QQ_RUNDIR_SUFFIX)" if suffix else ""))
    decays = list(BR_TABLE)
    if args.decays:
        decays = [d.strip() for d in args.decays.split(",") if d.strip()]
        bad = [d for d in decays if d not in BR_TABLE]
        if bad:
            sys.exit(f"ERROR: unknown decays {bad}; known: {list(BR_TABLE)}")
    # fit range: bias_test_qq.py's r=0.9,1.1 for the 1% injection, wider for larger X
    rrange = "r=0.9,1.1" if X <= 0.01 else "r=0.8,1.2"
    # BR set of the injection (both sets go to the log header; the sample set is optional
    # information in table mode, mandatory in sample mode)
    BR_SAMPLE, procdict = sample_br(strict=args.br == "sample")
    BR = BR_SAMPLE if args.br == "sample" else BR_TABLE

    bins, shapes = parse_card(cardpath)
    card_dir = os.path.dirname(cardpath)
    cache = {}
    # per bin: shapes file, data_obs key, signal key, per-decay file (or None -> synthetic)
    info = {}
    synthetic = []
    for b in bins:
        e_obs = shape_entry(shapes, b, "data_obs", cardpath)
        e_sig = shape_entry(shapes, b, "signal", cardpath)
        if "$PROCESS" not in e_sig[3]:
            sys.exit(f"ERROR: {cardpath}: the nominal shape pattern of bin '{b}' ({e_sig[3]}) has no $PROCESS - "
                     "cannot derive the per-decay histogram names (<pattern with $PROCESS=sig_<h>>)")
        f_obs, f_sig = resolve(e_obs[2], card_dir), resolve(e_sig[2], card_dir)
        for f in (f_obs, f_sig):
            if not os.path.isfile(f):
                sys.exit(f"ERROR: shapes file {f} referenced by {cardpath} (bin {b}) does not exist")
        by_decay = os.path.join(os.path.dirname(f_sig), BY_DECAY_FILE)
        if not os.path.isfile(by_decay):
            if not args.synthetic_by_decay:
                sys.exit(f"ERROR: {by_decay} missing for bin '{b}' (per-decay templates; produced by the makeWS step "
                         "when the exclusive ZH samples are available; --synthetic-by-decay for a mechanics check only)")
            by_decay = None
            synthetic.append(b)
        info[b] = {"file_obs": f_obs, "key_obs": expand(e_obs[3], b, "data_obs"),
                   "file_sig": f_sig, "key_sig": expand(e_sig[3], b, "signal"),
                   "pattern": e_sig[3], "by_decay": by_decay}
        get_hist(f_obs, info[b]["key_obs"], cache)   # existence checks
        get_hist(f_sig, info[b]["key_sig"], cache)

    def sig_template(b, h):
        """Mode-h signal template of bin b (real per-decay file, or synthetic BR_h x signal)."""
        i = info[b]
        if i["by_decay"] is None:
            hs = get_hist(i["file_sig"], i["key_sig"], cache).Clone(f"synthetic_{b}_{h}")
            hs.Scale(BR[h])
            return hs
        return get_hist(i["by_decay"], expand(i["pattern"], b, f"sig_{h}"), cache)

    # per-decay yields / efficiency spread (companion table; sum_h vs fit signal shows
    # how well the per-decay templates reproduce the fit template)
    print(f"=== per-decay signal yields per bin ({args.channel} @ {_ecm} GeV, card {cardpath}) ===")
    if synthetic:
        print(f"  SYNTHETIC per-decay templates (BR_h x nominal signal; mechanics check only) for bins: {synthetic}")
    for b in bins:
        srcs = "synthetic" if info[b]["by_decay"] is None else info[b]["by_decay"]
        print(f"  bin {b}: shapes {info[b]['file_sig']} [{info[b]['pattern']}], per-decay: {srcs}")
    w = max(len(b) for b in bins) + 2
    print("  " + f"{'decay':9s}" + "".join(f"{b:>{max(w, 12)}s}" for b in bins))
    sums = {b: 0.0 for b in bins}
    for h in BR_TABLE:
        ys = {b: sig_template(b, h).Integral() for b in bins}
        for b in bins:
            sums[b] += ys[b]
        print("  " + f"{h:9s}" + "".join(f"{ys[b]:>{max(w, 12)}.1f}" for b in bins))
    print("  " + f"{'sum_h':9s}" + "".join(f"{sums[b]:>{max(w, 12)}.1f}" for b in bins))
    tots = {b: get_hist(info[b]["file_sig"], info[b]["key_sig"], cache).Integral() for b in bins}
    print("  " + f"{'signal':9s}" + "".join(f"{tots[b]:>{max(w, 12)}.1f}" for b in bins) + "   (fit template)")
    print("  " + f"{'ratio':9s}" + "".join(f"{sums[b] / max(tots[b], 1e-9):>{max(w, 12)}.4f}" for b in bins) + "   (sum_h / signal)")

    # modified-shapes-file names inside bias_<h>/: EVERY shapes file the card references is
    # copied there (unchanged unless it holds a bin's data_obs), so the rewritten card is
    # complete even when some process comes from a file other than the data_obs one
    files = sorted({resolve(s[2], card_dir) for s in shapes if s[2] != "FAKE"} | {i["file_obs"] for i in info.values()})
    for f in files:
        if not os.path.isfile(f):
            sys.exit(f"ERROR: shapes file {f} referenced by {cardpath} does not exist")
    local = {}
    for f in files:
        name = os.path.basename(f) if len(files) == 1 else f"{os.path.basename(os.path.dirname(f))}__{os.path.basename(f)}"
        if name in local.values():
            name = f"{len(local)}__{name}"
        local[f] = name
    obs_by_file = {}
    for b, i in info.items():
        obs_by_file.setdefault(i["file_obs"], {})[i["key_obs"]] = b

    # a synthetic (mechanics-only) run must never be mistaken for a physics result: fit
    # files in bias_synthetic_<h>/ (collect_results.py reads bias_<h>/ only), header
    # channel=<name>-synthetic (unknown to the collector -> block skipped with a warning)
    label = f"{args.channel}-synthetic" if synthetic else args.channel
    subdir = "bias_synthetic_{}" if synthetic else "bias_{}"
    print(f"\n=== bias test: channel={label} X = {100 * X:g}% br={args.br} total-xsec injection per decay mode ===")
    print(f"  fit range {rrange}; {len(decays)} decays; run dir {rundir}")
    print(f"  BR set used: {args.br} (injection = X/BR_h x sig_h); sample = winter2023 exclusive-set cross-section "
          f"fractions over {len(_z_all)} Z x {len(BR_TABLE)} H decays from "
          f"{procdict or PROCDICT + ' (not found)'}{'' if BR_SAMPLE else ' (sample set not shown)'}, table = SM (mH = 125 GeV)")
    for h in BR_TABLE:
        s = f"BR_sample={BR_SAMPLE[h]:.6f}" if BR_SAMPLE else "BR_sample=n/a"
        ratio = f"sample/table={BR_SAMPLE[h] / BR_TABLE[h]:.4f}" if BR_SAMPLE else ""
        print(f"    {h:8s} {s}  BR_table={BR_TABLE[h]:.6f}  {ratio}")
    results = []
    for h in decays:
        br = BR[h]
        scale = X / br  # extra fraction of the mode's own yield
        vdir = os.path.join(rundir, subdir.format(h))
        os.makedirs(vdir, exist_ok=True)
        for f in files:
            fIn = ROOT.TFile.Open(f)
            fOut = ROOT.TFile(os.path.join(vdir, local[f]), "RECREATE")
            obs_keys = obs_by_file.get(f, {})
            for key in fIn.GetListOfKeys():
                name = key.GetName()
                obj = fIn.Get(name)
                if name in obs_keys:
                    obj = obj.Clone(name)
                    obj.Add(sig_template(obs_keys[name], h), scale)
                fOut.cd()
                obj.Write(name)
            fOut.Close()
            fIn.Close()
        # card copy with the shapes lines pointing at the local modified files
        with open(cardpath) as src, open(os.path.join(vdir, card), "w") as dst:
            for raw in src:
                f = raw.split("#")[0].split()
                if f and f[0] == "shapes" and len(f) >= 5 and f[3] != "FAKE":
                    f[3] = local[resolve(f[3], card_dir)]
                    dst.write(" ".join(f) + "\n")
                else:
                    dst.write(raw)
        r = best_fit_r(vdir, card, rrange)
        bias = (r - (1.0 + X)) * 100.0
        results.append((h, br, r, bias))
        print(f"  {h:8s} BR={br:8.5f}  r_fit={r:.5f}  bias={bias:+.3f}%")

    print("\nSummary (bias = r_fit - (1+X), percent of sigma_ZH):")
    worst = max(results, key=lambda x: abs(x[3]))
    for h, br, r, bias in results:
        print(f"  {h:8s} {bias:+.3f}%")
    print(f"Largest |bias|: {worst[0]} ({worst[3]:+.3f}%)")
    if synthetic:
        print(f"NOTE: synthetic per-decay templates were used for bins {synthetic} - mechanics check, not a physics result")
    for f in cache.values():
        f.Close()


if __name__ == "__main__":
    main()
