#!/usr/bin/env python3
"""
Build the PAPER-SPEC leptonic (Z->mumu / Z->ee) fit inputs, ecm 240, following
arXiv:2512.21290 Sec. 5.2/5.3: a binned likelihood fit of the RECOIL MASS
(100-150 GeV, 100 bins) done simultaneously in TWO regions of the BDT output
(loBDT / hiBDT; boundary 0.83 mumu, 0.88 ee at 240 GeV, 0.66 / 0.76 at 365 GeV,
applied by the stage2 selections sel_Baseline_{lo,hi}BDT, which also carry the
paper's 86<m_ll<96 GeV and p_ll window and no cos(theta_miss) cut). One parameter
of interest r scales the TOTAL ZH rate.

Signal = ALL ZH final states passing the selection (paper Sec. 5.2). Two
constructions of the nominal template (--signal, default 'inclusive'):
  inclusive  the inclusive wzp6_ee_<flavor>H sample (targeted Z(ll)H, all H decays)
             + the sum of the exclusive wzp6_ee_<z>H_<Hdecay> samples of the OTHER
             seven Z decays (ee|mumu, tautau, nunu, qq, ss, cc, bb; nunuH_Hinv
             excluded: fully invisible, zero acceptance).
  exclusive  the sum of the exclusive samples of ALL 8 Z decays x 11 H decays
             (87 sets, nunuH_Hinv excluded), built as sum_h of the per-decay
             templates written to signal_by_decay.root, so that the fit signal and
             the bias-test decomposition are IDENTICAL bin by bin (no k factor, no
             residual). The inclusive sample enters only through the BES variation
             (below). Motivation: the inclusive sample and the exclusive sets are
             independent generations whose total yields differ by ~0.3% (sum of the
             exclusive cross sections vs the inclusive one, MC statistics) - not
             physics. With the inclusive nominal, sum_h sig_h differs from the fit
             signal per category by O(0.01-0.4%), and the bias test (which adds
             X/BR_h x sig_h to the Asimov data) reads that as a spurious per-mode
             bias of the same order.
Backgrounds as separate components, each with a 1% lnN normalization nuisance in
the datacard (datacard_recoil_2cat_<flavor>.txt; names shared with the qq card
where the physics process is the same, so the combination correlates them):
  bkg_WW (norm_WW), bkg_ZZ (norm_ZZ), bkg_Zll (norm_Zll: Z/gamma* -> ll, tautau),
  bkg_rare (norm_rare: egamma/gammae, gaga, nuenueZ[, tt at 365]).
The process lists below are exactly the channel's stage1 processList.
Shape nuisances (same names as the July BDT-score cards, so the combination
correlates them with the qq card's JETSCALE/SQRTS consistently):
  MUSCALE|ELSCALE  lepton momentum scale, from the stage2 *_scaleup/_scaledw
                   selections (recoil_m_scaleup/_scaledw) of the SAME sample set
                   as the nominal (inclusive + other-Z, or the 87 exclusive sets)
  SQRTS            sqrt(s) +-2 MeV, *_sqrtsup/_sqrtsdw selections, same sets
  BES              beam energy spread, from the dedicated inclusive samples
                   wzp6_ee_<flavor>H_BES-higher-1pc / -lower-1pc under the nominal
                   selection: signal_BESUp = signal + (incl_BESup - incl_nominal)
                   (inclusive mode: = incl_BESup + otherZ_nominal). The other-Z part
                   carries NO BES variation (no BES samples exist for the exclusive
                   sets). In EXCLUSIVE mode the Up/Down templates are in addition
                   scaled to the nominal integral per category (normalization-
                   preserving; the pre-scaling shift is printed): the BES samples
                   are yet another independent generation, and their integral
                   relative to the exclusive sum is MC statistics / cross-section
                   rounding, not a BES effect (a BES change does not alter the ZH
                   rate). Bins driven negative by the subtraction are clipped to
                   zero first (count and content reported).
No rateParam (paper: background normalizations are constrained, 1% each).
No autoMCStats: every template is high-statistics MC (10^5-10^7 generated events
per process, per-bin MC uncertainties far below the Asimov Poisson errors), the
July cards and the qq card carry none either, and the paper's nuisance list
(Sec. 5.3) has no MC-statistics term - so the nuisance set stays identical to
the paper's. data_obs = Asimov sum of signal and backgrounds.

Outputs in <out-base>/run_recoil_2cat_<flavor><tag>/  (out-base default: this dir):
  datacard.root         <cat>_<proc>[_<SYST>Up|Down] TH1s + <cat>_data_obs
  signal_by_decay.root  <cat>_sig_<Hdecay>: exclusive wzp6_ee_<flavor>H_<Hdecay>
                        + the other-Z exclusive samples of that decay. Used ONLY by
                        bias_test_generic.py (paper Sec. 7.2).
                        inclusive mode: the fit signal is the inclusive-based template
                        above and the BR-weighted sum of the exclusive samples only
                        APPROXIMATES it (independent generation; sum of exclusive
                        xsecs differs from the inclusive xsec by ~0.3%), so the
                        own-flavor exclusive part is renormalized by one global
                        factor k = I(inclusive) / I(sum_h exclusive_h) (both
                        categories summed) such that sum_h sig_h and the fit signal
                        have the same total yield; the residual per-category
                        difference is printed.
                        exclusive mode: k = 1 and sum_h sig_h == signal exactly.
                        Written only when every per-decay template has input (a
                        stale file is removed otherwise, so the bias test cannot
                        pick it up).
  templates.root        the pieces (inclusive, other-Z, per-process, BES samples;
                        exclusive mode adds <cat>_signal_inclbased, the inclusive-
                        based alternative, for comparison)
  datacard_recoil_2cat_<flavor>.txt  copied card; text2workspace is attempted and
                        only succeeds in the combine env (run book).

--single-region: the paper's CUT-BASED configuration (Table 2, Sec. 6: the recoil mass
fitted in a SINGLE region per final state, no BDT categorization). Every template -
the signal (inclusive + other-Z, or the 87 exclusive sets), the per-decay pieces of
signal_by_decay.root, the background components and all MUSCALE|ELSCALE / SQRTS / BES
variations - is the SUM of the loBDT and hiBDT stage2 histograms of the same process
and variation: the two BDT regions partition the baseline selection (BDTscore < x and
>= x on top of identical cuts, so sel_Baseline_loBDT + sel_Baseline_hiBDT ==
sel_Baseline_wide by construction) and the sum is that selection without the BDT cut,
with exactly the events of the two-region fit. The builder checks this closure per
process and bin against the sel_Baseline_wide[_<tag>] histograms where they exist
(max relative difference printed, WARNING above 1e-6). The single category is named
noBDT (<cat> = noBDT in every histogram name); the card is a ONE-bin derivative of
datacard_recoil_2cat_<flavor>.txt (same processes, same nuisances: the columns of one
bin) written under the SAME file name into the run dir; and the run dir keeps the name
run_recoil_2cat_<flavor><tag> - with --single-region the '2cat' in that name is
HISTORICAL, kept so that run_fit_leptonic.sh, run_fit_combination.sh and
bias_test_generic.py work unchanged through RUNDIR_SUFFIX / --tag. Always give such a
build its own --tag (e.g. _cutbased), otherwise it overwrites the two-region dir.

A missing stage2 file for any process/variation aborts (a gap means the production
is incomplete and would silently bias the template); FCC_ALLOW_MISSING=1 downgrades
that to a warning: partially missing sums use what exists, a variation with NO input
at all becomes a copy of the nominal (no-op nuisance, loudly announced), a nominal
template with no input still aborts.

Run in the key4hep env, from this dir:
  python3 makeWS_recoil_2cat.py <mumu|ee> [--signal inclusive|exclusive] [--tag SUFFIX]
                                [--rebin N] [--input-base DIR] [--out-base DIR] [--single-region]
                                [--lumi-scale F]
  --signal      nominal signal construction, see above (default inclusive)
  --tag SUFFIX  run dir run_recoil_2cat_<flavor><SUFFIX> (default none): variants live
                next to the default dir; the fit drivers / bias test find them with
                RUNDIR_SUFFIX=<SUFFIX> (run_fit_leptonic.sh, run_fit_combination.sh,
                bias_test_generic.py --tag)
  --input-base  stage2 histogram dir, default
                /gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper/S240/<flavor>/BDT_analysis_samples/syst
  --out-base    parent of the run dir (tests: a scratch dir; then FIT_BASE=<out-base>
                for run_fit_leptonic.sh / run_fit_combination.sh / bias_test_generic.py)
  --rebin N     merge N recoil-mass bins (default 1 = 0.5 GeV bins)
  --single-region  ONE region (category noBDT = loBDT + hiBDT summed) instead of the two BDT
                regions: the paper's cut-based configuration, see above; the run dir keeps
                its run_recoil_2cat_ name, so give the build a --tag (e.g. _cutbased)
  --lumi-scale F  multiply the module luminosity (lumi = the paper value) by F before any
                template is scaled (default 1 = unchanged); e.g. 0.961538 = 3.0/3.12 ab-1 at
                365 GeV (the value of Jan Eysermans' paper histmakers); give such a build its
                own --tag (e.g. _lumi3p0)
"""
import argparse
import copy
import os
import shutil
import subprocess
import sys

import ROOT

ROOT.TH1.SetDefaultSumw2(True)
ROOT.gROOT.SetBatch(True)

_ecm = "240"          # the S365 copy differs in _ecm, lumi and the header text
lumi = 10800000.      # pb-1 (arXiv:2512.21290: 10.8 ab-1 at 240, 3.12 ab-1 at 365)
BES_TAG = "1pc"       # dedicated BES samples wzp6_ee_<flavor>H_BES-{higher,lower}-<tag>

STORE = "/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper"
HERE = os.path.dirname(os.path.abspath(__file__))

_z_all = ["ee", "mumu", "tautau", "nunu", "qq", "ss", "cc", "bb"]
_h_decays = ["Hbb", "Hcc", "Hss", "Hgg", "Haa", "HZa", "HWW", "HZZ", "Hmumu", "Htautau", "Hinv"]

CATEGORIES = ["hiBDT", "loBDT"]
SINGLE_CAT = "noBDT"            # --single-region: the one category = loBDT + hiBDT summed
WIDE_SEL = "sel_Baseline_wide"  # --single-region closure reference: the same cuts without the BDT condition
HNAME = "recoil_m"    # stage2 histoList key: zll_recoil_m, 100 bins in [100, 150] GeV


def incl_proc(flavor, tag=""):
    """Inclusive Z(ll)H sample (all H decays); tag = '' | 'BES-higher-1pc' | ..."""
    return f"wzp6_ee_{flavor}H_{tag + '_' if tag else ''}ecm{_ecm}"


def excl_proc(z, h):
    return f"wzp6_ee_{z}H_{h}_ecm{_ecm}"


def other_z_procs(flavor, h=None):
    """Exclusive ZH sets of the seven non-targeted Z decays; one H decay when h is given."""
    hs = [h] if h else _h_decays
    return [excl_proc(z, hh) for z in _z_all if z != flavor for hh in hs
            if not (z == "nunu" and hh == "Hinv")]


def own_excl_procs(flavor, h):
    return [excl_proc(flavor, h)]


def all_excl_procs(flavor):
    """The 87 exclusive sets (8 Z x 11 H decays, nunuH_Hinv excluded), own flavor first."""
    return [p for h in _h_decays for p in own_excl_procs(flavor, h)] + other_z_procs(flavor)


def bkg_components(flavor):
    """Background components (1% lnN each); exactly the stage1 processList of the channel."""
    zll = {"mumu": f"wzp6_ee_mumu_ecm{_ecm}", "ee": f"wzp6_ee_ee_Mee_30_150_ecm{_ecm}"}[flavor]
    return {
        "bkg_WW":   [f"p8_ee_WW_ecm{_ecm}"],
        "bkg_ZZ":   [f"p8_ee_ZZ_ecm{_ecm}"],
        "bkg_Zll":  [zll, f"wzp6_ee_tautau_ecm{_ecm}"],
        "bkg_rare": [f"wzp6_egamma_eZ_Z{flavor}_ecm{_ecm}", f"wzp6_gammae_eZ_Z{flavor}_ecm{_ecm}",
                     f"wzp6_gaga_{flavor}_60_ecm{_ecm}", f"wzp6_gaga_tautau_60_ecm{_ecm}",
                     f"wzp6_ee_nuenueZ_ecm{_ecm}"]
                    + ([f"p8_ee_tt_ecm{_ecm}"] if _ecm == "365" else []),
    }


# shape nuisance -> (up selection tag, down selection tag); histogram = recoil_m_<tag>
def variations(flavor):
    return {{"mumu": "MUSCALE", "ee": "ELSCALE"}[flavor]: ("scaleup", "scaledw"),
            "SQRTS": ("sqrtsup", "sqrtsdw")}


class Stage2:
    """Reader of the stage2 histogram files with the strict missing-input policy."""

    def __init__(self, base, rebin):
        self.base = base
        self.rebin = rebin
        self.allow_missing = os.environ.get("FCC_ALLOW_MISSING") == "1"
        self.single = {}   # (proc, sel) -> lumi-scaled nominal TH1, for templates.root

    def fname(self, proc, sel):
        return os.path.join(self.base, f"{proc}_{sel}_histo.root")

    def read(self, proc, sel, hname):
        """lumi-scaled, rebinned TH1 or None if the stage2 file does not exist."""
        fn = self.fname(proc, sel)
        if not os.path.isfile(fn):
            return None
        fIn = ROOT.TFile.Open(fn)
        if not fIn or fIn.IsZombie():
            sys.exit(f"ERROR: cannot open {fn}")
        h = fIn.Get(hname)
        if not h:
            sys.exit(f"ERROR: histogram '{hname}' missing in {fn}")
        h = copy.deepcopy(h)
        fIn.Close()
        h.SetDirectory(0)
        h.Scale(lumi)
        if self.rebin > 1:
            h = h.Rebin(self.rebin)
        return h

    def sum(self, procs, sel, hname, newname, variation=False):
        """Sum one histogram over many processes; sel is one selection name or a list of
        them, summed as well (--single-region: the loBDT and hiBDT files of every process).

        Missing stage2 files abort unless FCC_ALLOW_MISSING=1 (warning). With NO input
        at all: variations return None (caller substitutes the nominal, loudly), a
        nominal template always aborts.
        """
        sels = [sel] if isinstance(sel, str) else list(sel)
        h, missing = None, []
        for proc in procs:
            for s in sels:
                hist = self.read(proc, s, hname)
                if hist is None:
                    missing.append(proc if len(sels) == 1 else f"{proc}[{s}]")
                    continue
                if hname == HNAME:
                    self.single[(proc, s)] = hist
                if h is None:
                    h = hist.Clone(newname)
                else:
                    h.Add(hist)
        if missing:
            msg = (f"{newname} ({'+'.join(sels)}/{hname}): {len(missing)}/{len(procs) * len(sels)} processes "
                   f"without stage2 output: {missing}")
            if self.allow_missing:
                print(f"WARNING (FCC_ALLOW_MISSING=1): {msg}")
            else:
                sys.exit(f"ERROR: {msg}")
        if h is None:
            if variation and self.allow_missing:
                return None
            sys.exit(f"ERROR: no histograms found for {newname} ({sel}/{hname})")
        h.SetName(newname)
        h.SetDirectory(0)
        return h


def add_all(name, parts):
    """Clone-and-add of the non-None histograms in parts (None if there is none)."""
    h = None
    for part in parts:
        if part is None:
            continue
        if h is None:
            h = part.Clone(name)
        else:
            h.Add(part)
    if h is not None:
        h.SetDirectory(0)
    return h


def clip_negative(h):
    """Set negative bins to zero; returns (number of bins, content) clipped."""
    n, c = 0, 0.0
    for i in range(1, h.GetNbinsX() + 1):
        v = h.GetBinContent(i)
        if v < 0:
            n += 1
            c += v
            h.SetBinContent(i, 0.0)
    return n, c


def with_tag(sels, tag):
    """The varied selections <sel>_<tag> of a category's selection list."""
    return [f"{s}_{tag}" for s in sels]


def closure_check(s2, procs, sels, tag=""):
    """--single-region closure: per process, sum over sels[_tag] vs the WIDE_SEL[_tag] file of
    HNAME[_tag], every bin incl. under/overflow. Returns (max relative bin difference, the
    process it occurs in, processes compared, processes without a wide file). A bin that is
    zero in the wide file but not in the sum counts as inf."""
    hname = f"{HNAME}_{tag}" if tag else HNAME
    worst, wproc, n, nowide = 0.0, None, 0, 0
    for proc in procs:
        wide = s2.read(proc, f"{WIDE_SEL}_{tag}" if tag else WIDE_SEL, hname)
        if wide is None:
            nowide += 1
            continue
        parts = [s2.read(proc, f"{s}_{tag}" if tag else s, hname) for s in sels]
        if any(p is None for p in parts):
            continue   # reported by the template build's missing-input policy
        n += 1
        for i in range(0, wide.GetNbinsX() + 2):
            a = sum(p.GetBinContent(i) for p in parts)
            b = wide.GetBinContent(i)
            d = abs(a - b) / abs(b) if b != 0 else (0.0 if a == 0 else float("inf"))
            if d > worst:
                worst, wproc = d, proc
    return worst, wproc, n, nowide


def single_region_card(text, cat):
    """ONE-bin derivative of the two-region card text: the columns of its first bin, renamed cat.

    Structure-aware line rewrite - imax; the channel list / observation pair; the process
    block (bin / process / process / rate); the nuisance lines <name> <type> <one value per
    process column>. Comments, separators, shapes, jmax/kmax pass through unchanged. Same
    processes and nuisances as the two-region card. Any other line aborts (no rateParam /
    autoMCStats in the recoil cards; extend here if that ever changes).
    """
    out, first, cols, ncol = [], None, None, None
    out.append(f"# SINGLE-REGION derivative (makeWS_recoil_2cat.py --single-region): ONE bin '{cat}' = "
               "loBDT + hiBDT summed, the columns of the two-region card's first bin; same processes and nuisances.")
    for raw in text.splitlines():
        line = raw.split("#")[0].rstrip()
        f = line.split()
        if not f or line.startswith("--") or f[0] in ("shapes", "jmax", "kmax"):
            out.append(raw)
            continue
        if f[0] == "imax":
            out.append("imax 1")
        elif f[0] == "bin" and first is None:          # channel list
            first = f[1]
            out.append(f"bin           {cat}")
        elif f[0] == "observation":
            out.append("observation   -1")
        elif f[0] == "bin" and cols is None:           # process block header
            ncol = len(f) - 1
            cols = [i for i, b in enumerate(f[1:]) if b == first]
            out.append("bin       " + "  ".join(f"{cat:8s}" for _ in cols))
        elif f[0] in ("process", "rate") and cols is not None:
            out.append(f"{f[0]:9s} " + "  ".join(f"{f[1 + i]:8s}" for i in cols))
        elif cols is not None and len(f) == 2 + ncol and f[1] not in ("rateParam", "autoMCStats", "param", "group"):
            vals = f[2:]
            out.append(f"{f[0]:10s} {f[1]:6s} " + "  ".join(f"{vals[i]:8s}" for i in cols))
        else:
            sys.exit(f"ERROR: single-region card: cannot derive the one-bin form of the line {raw!r}")
    if first is None or cols is None or not cols:
        sys.exit("ERROR: single-region card: no bin / process block found in the two-region card")
    return "\n".join(l.rstrip() for l in out) + "\n"


def main():
    global lumi
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("flavor", choices=("mumu", "ee"))
    ap.add_argument("--signal", choices=("inclusive", "exclusive"), default="inclusive",
                    help="nominal signal: 'inclusive' (default) = inclusive Z(ll)H sample + other-Z exclusive sets; "
                         "'exclusive' = sum of the 87 exclusive sets = sum_h of the per-decay templates (see the docstring)")
    ap.add_argument("--tag", metavar="SUFFIX", default="",
                    help="run dir name suffix: run_recoil_2cat_<flavor><SUFFIX> (default none; e.g. _excl); "
                         "the fit drivers and bias_test_generic.py take it as RUNDIR_SUFFIX / --tag")
    ap.add_argument("--rebin", type=int, default=1, help="merge N recoil-mass bins (default 1)")
    ap.add_argument("--single-region", action="store_true",
                    help="paper cut-based configuration: ONE region (category noBDT = loBDT + hiBDT summed) instead of the "
                         "two BDT regions, one-bin card; the run dir keeps its run_recoil_2cat_ name (give a --tag; docstring)")
    ap.add_argument("--input-base", metavar="DIR", help="stage2 histogram dir (default STORE/S%s/<flavor>/BDT_analysis_samples/syst)" % _ecm)
    ap.add_argument("--out-base", metavar="DIR", default=HERE, help="parent of run_recoil_2cat_<flavor><tag>/ (default: this dir)")
    ap.add_argument("--lumi-scale", metavar="F", type=float, default=1.0,
                    help="multiply the module luminosity (lumi = the paper value) by F before any template is scaled "
                         "(default 1.0 = unchanged); e.g. 0.961538 = 3.0/3.12 ab-1 at 365 GeV (the value of Jan "
                         "Eysermans' paper histmakers); give such a build its own --tag (e.g. _lumi3p0)")
    args = ap.parse_args()
    if not args.lumi_scale > 0:
        sys.exit(f"ERROR: --lumi-scale {args.lumi_scale} must be positive")
    if args.lumi_scale != 1.0:
        lumi_module = lumi
        lumi = lumi_module * args.lumi_scale
        print(f"== --lumi-scale {args.lumi_scale:g}: effective lumi {lumi:.2f} pb-1 = module lumi {lumi_module:.2f} pb-1 "
              f"x {args.lumi_scale:g} (every template below is scaled to the effective lumi)")
    flavor = args.flavor
    excl_mode = args.signal == "exclusive"
    if args.rebin < 1 or 100 % args.rebin:
        sys.exit(f"ERROR: --rebin {args.rebin} must divide the 100 recoil-mass bins")
    if args.tag and (os.sep in args.tag or any(c.isspace() for c in args.tag)):
        sys.exit(f"ERROR: --tag {args.tag!r} must be a plain name fragment (no path separator or whitespace: "
                 "it becomes part of the run dir name and of the combined card's shapes paths)")
    base = args.input_base or f"{STORE}/S{_ecm}/{flavor}/BDT_analysis_samples/syst"
    if not os.path.isdir(base):
        sys.exit(f"ERROR: stage2 input dir {base} does not exist (run 'fccanalysis final' for S{_ecm}/{flavor} first)")
    runDir = os.path.join(os.path.abspath(args.out_base), f"run_recoil_2cat_{flavor}{args.tag}")
    os.makedirs(runDir, exist_ok=True)
    print(f"== {flavor} @ {_ecm} GeV, lumi {lumi:.4g} pb-1, rebin {args.rebin}, signal = {args.signal}"
          f"\n== stage2 input: {base}\n== run dir: {runDir}")

    # category -> stage2 selections summed per template: one BDT region each (default), or the single
    # category noBDT = loBDT + hiBDT (--single-region: the baseline selection without the BDT cut)
    if args.single_region:
        cats = [SINGLE_CAT]
        regions = {SINGLE_CAT: [f"sel_Baseline_{c}" for c in CATEGORIES]}
        print(f"== single region (paper cut-based configuration): category {SINGLE_CAT} = "
              f"{' + '.join(regions[SINGLE_CAT])}, one-bin card; the '2cat' of the run dir name is historical")
    else:
        cats = list(CATEGORIES)
        regions = {c: [f"sel_Baseline_{c}"] for c in cats}

    s2 = Stage2(base, args.rebin)
    incl = incl_proc(flavor)
    other = other_z_procs(flavor)
    # sample set of the nominal and of the MUSCALE|ELSCALE / SQRTS variations
    signal_procs = all_excl_procs(flavor) if excl_mode else [incl] + other
    if excl_mode:
        print(f"== exclusive mode: signal = sum of {len(signal_procs)} exclusive sets "
              f"(8 Z x 11 H decays, nunuH_Hinv excluded); inclusive {incl} only enters the BES variation")
    comps = bkg_components(flavor)

    hists, ctl, by_decay = [], [], []
    decay_ok = True
    incl_tot, own_excl_tot = 0.0, {}   # for the per-decay renormalization factor k (inclusive mode)
    yields = {}
    for cat in cats:
        sel = regions[cat]
        h_incl = s2.sum([incl], sel, HNAME, f"{cat}_signal_incl")
        h_other = s2.sum(other, sel, HNAME, f"{cat}_signal_otherZ", variation=True)
        ctl.append(h_incl)
        if h_other is not None:
            ctl.append(h_other)
        else:
            print(f"WARNING (FCC_ALLOW_MISSING=1): {cat}: no other-Z exclusive sample found")
        # inclusive-based construction (the nominal in inclusive mode, a control in exclusive mode)
        h_inclbased = add_all(f"{cat}_signal_inclbased", [h_incl, h_other])
        # per-H-decay pieces: own-flavor exclusive + other-Z exclusive of that decay
        pieces = []
        for h in _h_decays:
            own = s2.sum(own_excl_procs(flavor, h), sel, HNAME, f"{cat}_sigown_{h}", variation=True)
            oth = s2.sum(other_z_procs(flavor, h), sel, HNAME, f"{cat}_sigoth_{h}", variation=True)
            if own is None:
                decay_ok = False
            else:
                own_excl_tot[h] = own_excl_tot.get(h, 0.0) + own.Integral()
            pieces.append((h, own, oth))
        h_own = add_all(f"{cat}_signal_ownexcl", [own for _, own, _ in pieces])

        if excl_mode:
            # nominal = sum_h (own_h + oth_h): bin-by-bin identical to sum_h sig_h by construction
            h_sig = add_all(f"{cat}_signal", [p for _, own, oth in pieces for p in (own, oth)])
            if h_sig is None:
                sys.exit(f"ERROR: {cat}: no exclusive ZH sample at all - cannot build the exclusive-sum signal")
            if h_own is None:
                print(f"WARNING (FCC_ALLOW_MISSING=1): {cat}: no own-flavor exclusive sample found - "
                      f"signal = other-Z exclusive sets only")
            ctl.append(h_inclbased)
            ctl.append(h_own)
        else:
            h_sig = h_inclbased.Clone(f"{cat}_signal")
            h_sig.SetDirectory(0)
            if h_other is None:
                print(f"WARNING (FCC_ALLOW_MISSING=1): {cat}: signal = inclusive {incl} only")
        hists.append(h_sig)
        h_obs = h_sig.Clone(f"{cat}_data_obs")   # Asimov: signal + backgrounds
        yields[cat] = {"signal": h_sig.Integral(), "signal_incl": h_incl.Integral(),
                       "signal_otherZ": h_other.Integral() if h_other is not None else 0.0,
                       "signal_ownexcl": h_own.Integral() if h_own is not None else 0.0,
                       "signal_inclbased": h_inclbased.Integral()}
        incl_tot += h_incl.Integral()

        for comp, procs in comps.items():
            hb = s2.sum(procs, sel, HNAME, f"{cat}_{comp}")
            hists.append(hb)
            h_obs.Add(hb)
            yields[cat][comp] = hb.Integral()
        hists.append(h_obs)
        yields[cat]["data_obs"] = h_obs.Integral()

        # lepton scale / sqrt(s): varied selections and recoil variables of the nominal's sample set
        for syst, tags in variations(flavor).items():
            for tag, ud in zip(tags, ("Up", "Down")):
                hv = s2.sum(signal_procs, with_tag(sel, tag), f"{HNAME}_{tag}", f"{cat}_signal_{syst}{ud}", variation=True)
                if hv is None:
                    print(f"WARNING (FCC_ALLOW_MISSING=1): {cat}_signal_{syst}{ud}: no input at all - "
                          f"template = copy of the nominal (no-op nuisance)")
                    hv = h_sig.Clone(f"{cat}_signal_{syst}{ud}")
                hists.append(hv)
        # BES: dedicated inclusive samples under the nominal selection; signal + (incl_BES - incl_nominal)
        for tag, ud in (("higher", "Up"), ("lower", "Down")):
            bes = incl_proc(flavor, f"BES-{tag}-{BES_TAG}")
            hb = s2.sum([bes], sel, HNAME, f"{cat}_incl_BES{ud}", variation=True)
            if hb is None:
                print(f"WARNING (FCC_ALLOW_MISSING=1): {cat}_signal_BES{ud}: {bes} missing - "
                      f"template = copy of the nominal (no-op nuisance)")
                hv = h_sig.Clone(f"{cat}_signal_BES{ud}")
            elif excl_mode:
                ctl.append(hb)
                hv = h_sig.Clone(f"{cat}_signal_BES{ud}")
                hv.Add(hb)
                hv.Add(h_incl, -1.0)
                shift = hv.Integral() / h_sig.Integral() - 1.0
                nneg, cneg = clip_negative(hv)
                print(f"   {cat}_signal_BES{ud}: pre-scaling normalization shift {100 * shift:+.4f}% "
                      f"(I({bes}) - I({incl}) = {hb.Integral() - h_incl.Integral():+.2f} on {h_sig.Integral():.2f}); "
                      f"{nneg} negative bins ({cneg:+.4f} events) clipped to 0; scaled to the nominal integral")
                hv.Scale(h_sig.Integral() / hv.Integral())
            else:
                ctl.append(hb)
                hv = hb.Clone(f"{cat}_signal_BES{ud}")
                if h_other is not None:
                    hv.Add(h_other)
            hv.SetDirectory(0)
            hists.append(hv)

        # per-H-decay signal templates for the bias test (paper Sec. 7.2)
        for h, own, oth in pieces:
            if own is None:
                continue
            by_decay.append((cat, h, own, oth))

    # per-decay templates: inclusive mode renormalizes the own-flavor exclusive part so that
    # sum_h sig_h == fit signal in total yield; exclusive mode: k = 1, identity by construction
    if decay_ok and by_decay:
        if excl_mode:
            k = 1.0
            print("== per-decay templates: exclusive mode, k = 1 (sum_h sig_h == fit signal by construction)")
        else:
            excl_sum = sum(own_excl_tot.values())
            k = incl_tot / excl_sum if excl_sum > 0 else 1.0
            print(f"== per-decay templates: k = I(inclusive)/I(sum_h exclusive_h) = {incl_tot:.2f}/{excl_sum:.2f} = {k:.5f} "
                  f"applied to the own-flavor exclusive part ({'both categories' if len(cats) > 1 else 'single category'})")
        out_by_decay = []
        percat = {cat: None for cat in cats}
        for cat, h, own, oth in by_decay:
            hd = own.Clone(f"{cat}_sig_{h}")
            hd.Scale(k)
            if oth is not None:
                hd.Add(oth)
            hd.SetDirectory(0)
            out_by_decay.append(hd)
            percat[cat] = add_all(f"{cat}_sumdecay", [percat[cat], hd])
        for cat in cats:
            h_sig = next(h for h in hists if h.GetName() == f"{cat}_signal")
            hsum = percat[cat]
            maxdiff = max(abs(hsum.GetBinContent(i) - h_sig.GetBinContent(i)) for i in range(1, h_sig.GetNbinsX() + 1))
            print(f"   {cat}: sum_h sig_h = {hsum.Integral():.2f} vs fit signal {yields[cat]['signal']:.2f} "
                  f"(residual {100 * (hsum.Integral() / yields[cat]['signal'] - 1):+.4f}%, max |bin diff| {maxdiff:.2e})")
        by_decay = out_by_decay
    else:
        by_decay = []

    if args.single_region:
        # closure of the summed region against the stage2 selection without the BDT condition
        allprocs = sorted(set(signal_procs + [incl] + other + all_excl_procs(flavor)
                              + [incl_proc(flavor, f"BES-{t}-{BES_TAG}") for t in ("higher", "lower")]
                              + [p for procs in comps.values() for p in procs]))
        print(f"== single-region closure: {' + '.join(regions[SINGLE_CAT])} vs {WIDE_SEL} per process and bin "
              f"(incl. under/overflow), {len(allprocs)} processes, nominal and varied selections:")
        worst_all = 0.0
        for tag in [""] + [t for tags in variations(flavor).values() for t in tags]:
            worst, wproc, n, nowide = closure_check(s2, allprocs, regions[SINGLE_CAT], tag)
            worst_all = max(worst_all, worst)
            print(f"   {tag or 'nominal':8s}: {n} processes compared, max relative bin difference {worst:.2e}"
                  + (f" ({wproc})" if wproc else "")
                  + (f"; {nowide} without a {WIDE_SEL}{'_' + tag if tag else ''} file (not compared)" if nowide else ""))
        if worst_all > 1e-6:
            print(f"WARNING: single-region closure broken (max relative bin difference {worst_all:.2e} > 1e-6): "
                  f"the loBDT/hiBDT files do not partition {WIDE_SEL} - check the stage2 selections")

    for cat in cats:
        y = yields[cat]
        bkg = sum(v for k_, v in y.items() if k_.startswith("bkg_"))
        if excl_mode:
            parts = (f"own-flavor exclusive {y['signal_ownexcl']:.1f} + other-Z {y['signal_otherZ']:.1f}; "
                     f"inclusive-based alternative {y['signal_inclbased']:.1f} = inclusive {y['signal_incl']:.1f} + other-Z, "
                     f"exclusive/inclusive-based - 1 = {100 * (y['signal'] / y['signal_inclbased'] - 1):+.3f}%")
        else:
            parts = f"inclusive {y['signal_incl']:.1f} + other-Z {y['signal_otherZ']:.1f}"
        print(f"{cat}: signal {y['signal']:.1f} ({parts}), "
              f"total bkg {bkg:.1f} [" + ", ".join(f"{c} {y[c]:.1f}" for c in comps) + f"], S/B {y['signal'] / max(bkg, 1e-9):.3f}")

    # combine refuses a process template with null normalization (text2workspace: "Null norm
    # for channel <cat>, process <proc>") and a zero-integral shape variation: catch it here
    # with the offending template named instead of an obscure failure in the combine
    # container later (fix the stage2 input, or drop the process from the datacard).
    empty = [h.GetName() for h in hists if not h.Integral() > 0]
    if empty:
        sys.exit(f"ERROR: template(s) with zero (or negative/NaN) integral: {empty} - combine's "
                 "text2workspace refuses a process with null norm; fix the stage2 input or remove "
                 "the process from the datacard")

    fOut = ROOT.TFile(f"{runDir}/datacard.root", "RECREATE")
    for h in hists:
        h.Write()
    fOut.Close()
    fD = f"{runDir}/signal_by_decay.root"
    if by_decay:
        f = ROOT.TFile(fD, "RECREATE")
        for h in by_decay:
            h.Write()
        f.Close()
    else:
        print("WARNING: per-decay templates incomplete (exclusive samples missing) - "
              "signal_by_decay.root NOT written; bias_test_generic.py cannot run on this dir")
        if os.path.isfile(fD):
            os.remove(fD)
            print(f"WARNING: removed stale {fD}")
    fCtl = ROOT.TFile(f"{runDir}/templates.root", "RECREATE")
    for h in ctl:
        if h is not None:
            h.Write()
    for (proc, sel), h in s2.single.items():
        h.Write(f"{sel.replace('sel_Baseline_', '')}_{proc}")
    fCtl.Close()

    card = f"datacard_recoil_2cat_{flavor}.txt"
    if args.single_region:
        # ONE-bin derivative of the two-region card, under the same file name (the fit drivers and the
        # bias test look for datacard_recoil_2cat_<flavor>.txt in the run dir)
        with open(os.path.join(HERE, card)) as fh:
            text = single_region_card(fh.read(), SINGLE_CAT)
        with open(os.path.join(runDir, card), "w") as fh:
            fh.write(text)
        print(f"== single-region card {runDir}/{card} (ONE bin {SINGLE_CAT}, derived from {os.path.join(HERE, card)}):")
        print("\n".join("   " + l for l in text.splitlines() if l.strip() and not l.startswith("#")))
    else:
        shutil.copy(os.path.join(HERE, card), runDir)
    ret = subprocess.call(f"text2workspace.py {card} -o ws.root", shell=True, cwd=runDir)
    if ret != 0:
        print("NOTE: text2workspace failed (expected outside the combine env) - "
              f"run_fit_leptonic.sh {flavor} builds ws.root in the combine env. Templates in "
              f"{runDir}/datacard.root are complete.")


if __name__ == "__main__":
    main()
