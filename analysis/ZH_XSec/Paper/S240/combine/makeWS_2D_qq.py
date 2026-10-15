#!/usr/bin/env python3
"""
Build the hadronic (Z->qq) 2D m_recoil x m_jj fit inputs, ecm 240, PAPER SPEC
(arXiv:2512.21290 Sec. 5.2/5.3): the unrolled 2D shape is fitted SIMULTANEOUSLY in
two BDT-score regions (loBDT constrains the backgrounds, hiBDT carries the
sensitivity; boundary 0.75 at 240 GeV, 0.95 at 365 GeV, applied in stage2), one
parameter of interest r scaling the TOTAL ZH rate.

Signal = ALL ZH final states passing the hadronic selection (paper Sec. 5.2: "the
targeted Z(qq)H process, as well as the contributions from Z(ll)H, Z(tautau)H and
Z(nunu)H events that can pass the selection ... combined and treated as a single
parameter of interest"): the 87 exclusive sets wzp6_ee_<z>H_<Hdecay> over the 8 Z
decays (qq, ss, cc, bb, ee, mumu, tautau, nunu) x 11 H decays, minus nunuH_Hinv
(fully invisible, zero hadronic acceptance). Backgrounds as separate components,
each with a 1% lnN normalization nuisance in datacard_2d_qq.txt (names shared with
the leptonic cards where the physics process is the same, so the combination
correlates them): bkg_WW (norm_WW), bkg_ZZ (norm_ZZ), bkg_Zqq (norm_Zqq: Z/gamma*
-> qq), bkg_rare (norm_rare: dilepton, egamma/gammae, gaga, nuenueZ[, tt at 365]).
Shape nuisances on the signal (paper Sec. 5.3):
  JETSCALE  jet momentum scale, stage2 *_scaleup/_scaledw selections + mrecoil_mjj_scale*
  SQRTS     sqrt(s) +-2 MeV, *_sqrtsup/_sqrtsdw selections + mrecoil_mjj_sqrts*
  BES       beam energy spread +-1%, from the dedicated INCLUSIVE-H samples
            wzp6_ee_<z>H_BES-{higher,lower}-1pc (all 8 Z decays exist at both
            energies, winter2023) and their nominal wzp6_ee_<z>H, under the nominal
            selection:  signal_BESUp = signal + sum_z (incl_z_BESup - incl_z_nominal).
            The difference is taken between the two inclusive samples of the same Z
            decay, so the (independent-generation) normalization offset between the
            inclusive sample and the per-decay exclusive sum cancels; the exclusive
            sum and the inclusive sample agree only STATISTICALLY (the sum of the
            exclusive cross sections exceeds the inclusive one by ~0.3%, up to 1.2%
            for bbH at 240; the inclusive samples have ~1M events each vs ~10M per Z
            decay in the exclusive sets) - the ratio I(sum_z incl_z)/I(signal) per
            category and per Z decay is printed as a diagnostic. Bins driven
            negative by the statistical noise of the difference are clipped to 0
            (counted and printed). The BES nuisance is shared by name with the
            leptonic cards (one machine parameter) in the combination.
            SHAPE-ONLY by default: each signal_BESUp/Down is then rescaled to the
            nominal signal integral of its category. The nominal and the BES-shifted
            inclusive samples are generated independently (~1M events each), so
            I(incl_z_BES) - I(incl_z_nominal) carries a statistical normalization
            noise of O(1e-3) x I(incl_z) that has nothing to do with the beam energy
            spread - a resolution effect on m_recoil whose acceptance change is far
            below that; left in, the noise would turn the BES nuisance into a
            spurious +-0.x% signal-rate parameter correlated with r (the target
            precision is 0.3%). The pre-scaling shift and the applied factor are
            printed per category (a no-op template gets factor 1 exactly);
            --bes-keep-norm keeps the raw normalization (the previous behaviour).
No rateParam (paper: background normalizations constrained), no autoMCStats (high-
statistics MC templates; the paper's nuisance list has none). data_obs = Asimov.

--jesjer    adds the jet energy scale and resolution nuisances that paper Sec. 5.3 evaluated
            (1% JES shift, additional 1% jet energy smearing: -3.9% / -3.2% relative
            degradation of the hadronic precision at 240 GeV) but did not include in the
            quoted precision, as profiled shape nuisances on the SIGNAL AND EVERY BACKGROUND
            component (a detector effect on all jets, correlated across the processes
            through one nuisance each):
              JES  <cat>_<proc>_JESUp/Down from the stage2-style files
                   <proc>_sel_Baseline_<cat>_jesup|jesdw_histo.root (TH2 mrecoil_mjj_jesup|jesdw)
              JER  <cat>_<proc>_JERUp from ..._jerup_histo.root (mrecoil_mjj_jerup); the
                   smearing is one-sided, so JERDown = the bin-wise MIRROR of Up around the
                   nominal, nominal - (up - nominal), clipped at 0 (clipped bins are counted
                   and printed)
            produced by ../qq/stage2_jesjer_templates.py into the same syst/ dir as the stage2
            files (new file names): both jets scaled by 1 +- 1% (m' = k m, p' = k p, E' = k E,
            recoil recomputed) / each jet momentum smeared by 1% with deterministic per-event
            seeds; the BDT score is NOT recomputed under JES/JER (the JETSCALE convention);
            the stage1 m_jj / p_jj windows make the edge migration one-way (documented there).
            Card datacard_2d_qq_jesjer.txt = datacard_2d_qq.txt + 'JES shape' and 'JER shape'
            lines on every process, copied into the run dir (the fit drivers pick it up when
            present; their xsecSTATshapes scan then freezes JES and JER together with the other
            shape nuisances - stat + 1% background normalizations - and xsec floats them). The
            same strict missing-file policy applies to the JES/JER inputs. The run dir is
            run_2D_mrecoil_mjj_qq<tag>: give a --tag ending in _jesjer (e.g. _oldbdt_jesjer) so
            that it never overwrites the nominal run dir (a NOTE is printed otherwise), and use
            it as QQ_RUNDIR_SUFFIX of the fit drivers.
--jes-only / --jer-only  only one of the two nuisances (the paper's separate 3.9% / 3.2%
            comparison): the run dir card is datacard_2d_qq_jesjer.txt WITHOUT the other
            nuisance's line, the templates of the other one are not built; --tag e.g. _oldbdt_jes
            / _oldbdt_jer. Not combinable with --zh-other-as-bkg (paper-spec card only).

--recoil-only  CUT-BASED hadronic fit (paper Table 2 'Cut-based' column, Sec. 6: "each final
            state is fitted in a single region, and the hadronic final state is fitted using
            only the recoil mass distribution"): ONE region, the stage2 selection
            sel_Baseline_nomva (the baseline selection without the BDT cut; the September
            stage2 validation checked hiBDT + loBDT == nomva for every process and variation),
            and the m_recoil projection of the TH2 mrecoil_mjj[_<tag>] (X axis; the in-range
            m_jj bins summed, errors in quadrature: project_x()) as the observable of EVERY
            template. Stage2.sum() projects right after the per-process sum, so the whole
            template arithmetic runs on the 1D recoil histograms: JETSCALE / SQRTS from the
            projected mrecoil_mjj_<tag> variations, BES = signal + sum_z (incl_z_BES -
            incl_z_nominal) with the clipping of negative bins and the shape-only rescaling
            (scale_to_integral) on the projected histograms. Everything else is the default
            configuration: signal = the 87 ZH sets, the four background components with their
            1% lnN, --exclude / --zh-other-as-bkg / --bes-keep-norm as usual. The card is the
            ONE-bin derivation of datacard_2d_qq.txt (zhbkg: datacard_2d_qq_zhbkg.txt) made at
            run time by one_bin_card(): the columns of one bin only, named 'nomva', imax 1, the
            same nuisance lines; written under the SAME file name into the SAME run dir
            run_2D_mrecoil_mjj_qq<tag> so that run_fit_qq.sh 2d, run_fit_combination.sh all and
            bias_test_generic.py qq work unchanged with QQ_RUNDIR_SUFFIX=<tag> / --tag <tag>.
            The '2D' in the run dir name is HISTORICAL in this mode (the templates are 1D):
            --tag is mandatory (e.g. _oldbdt_cutbased) so that the nominal 2D run dir is never
            overwritten. Templates: nomva_<proc>[_<SYST>Up|Down] TH1s over m_recoil (25 bins
            100-150 GeV at 240, 20 bins 100-180 GeV at 365), nomva_sig_<Hdecay> in
            signal_by_decay.root, the projected working histograms (<cat>_<..>1d) in
            templates_recoil.root instead of templates_2d.root. Not combinable with --jesjer /
            --jes-only / --jer-only (refused: the paper evaluated JES / JER on the MVA-based 2D
            fit only).

--zh-other-as-bkg  July-2026 definition, kept as a cross-check: signal = the 44
            hadronic-Z sets Z(qq/ss/cc/bb)H x 11 H decays only, the other 43 ZH sets
            form a fifth background component bkg_ZH (norm_ZH 1% lnN), NO BES
            nuisance (the old card datacard_2d_qq_zhbkg.txt is used, run dir
            run_2D_mrecoil_mjj_qq_zhbkg/, signal_by_decay.root over the hadronic Z
            decays only, i.e. bias_test_qq.py's convention). Reproduces the July
            templates and numbers exactly; run_fit_qq.sh 2d-zhbkg fits it.
--exclude PROC[,PROC...]  drop the named stage1 processes from EVERY component they
            belong to (signal, bkg_*, hence also the Asimov data_obs and the per-H-decay
            bias templates); the remaining processes form the template. A name that is
            in no component's process list aborts (typo guard); a component left with
            no process aborts (remove it from the datacard instead: combine refuses a
            null-norm process). The dropped processes, their components and their
            nominal lumi-scaled yields per category are printed. Paper-faithful 365 GeV
            fit without ttbar: --exclude p8_ee_tt_ecm365 --tag _nott (the paper's
            hadronic fit had no tt template, tt being negligible in the selected phase
            space; the July-2026 port had added p8_ee_tt_ecm365 to bkg_rare).
--tag SFX   run dir run_2D_mrecoil_mjj_qq<SFX> (zhbkg: run_2D_mrecoil_mjj_qq_zhbkg<SFX>),
            default none: a variant lives next to the nominal dir; the fit drivers take
            the suffix as QQ_RUNDIR_SUFFIX, bias_test_generic.py as --tag.

Outputs in <out-base>/run_2D_mrecoil_mjj_qq[_zhbkg]<tag>/  (out-base default: this dir):
  datacard.root         <cat>_<proc>[_<SYST>Up|Down] unrolled TH1s + <cat>_data_obs
                        (--recoil-only: <cat> = nomva, TH1s over m_recoil)
  signal_by_decay.root  <cat>_sig_<Hdecay> = sum over ALL 8 Z decays of the exclusive
                        sets of that H decay (the paper's Sec. 7.2 bias test
                        perturbs every ZH process, "also treated as part of the
                        signal"); used by bias_test_generic.py qq|all. sum_h sig_h ==
                        signal exactly (same samples).
  templates_2d.root     the summed TH2s (signal, components, variations, inclusive
                        and BES pieces) for inspection (--recoil-only: templates_recoil.root,
                        the projected TH1s, names <cat>_<..>1d)
  datacard_2d_qq[_zhbkg].txt  copied card; text2workspace is attempted and only
                        succeeds in the combine env (run_fit_qq.sh builds ws.root)

A missing stage2 file for any process/variation aborts (a gap means the production is
incomplete and would silently bias the template); FCC_ALLOW_MISSING=1 downgrades that
to a warning: partially missing sums use what exists, a Z decay whose inclusive
nominal or BES sample is absent contributes no BES variation, a BES template with NO
inclusive input at all becomes a copy of the nominal (no-op nuisance, loudly
announced), a nominal template with no input still aborts.

Run in the key4hep env, from this dir:
  python3 makeWS_2D_qq.py [--zh-other-as-bkg] [--bes-keep-norm] [--exclude PROC[,PROC...]] [--tag SFX]
                          [--jesjer | --jes-only | --jer-only | --recoil-only] [--input-base DIR] [--out-base DIR]
                          [--lumi-scale F]
  --bes-keep-norm  raw BES templates (no rescaling to the nominal signal integral)
  --input-base  stage2 histogram dir, default
                /gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper/S240/qq/BDT_analysis_samples/syst
  --out-base    parent of the run dir (tests: a scratch dir; then FIT_BASE=<out-base>
                for run_fit_qq.sh / run_fit_combination.sh / bias_test_generic.py)
  --lumi-scale F  multiply the module luminosity (lumi = the paper value) by F before any
                template is scaled (default 1 = unchanged); e.g. 0.961538 = 3.0/3.12 ab-1 at
                365 GeV (the value of Jan Eysermans' paper histmakers); give such a build its
                own --tag (e.g. _lumi3p0)
"""
import argparse
import os
import shutil
import subprocess
import sys

import ROOT

ROOT.TH1.SetDefaultSumw2(True)
ROOT.TH1.AddDirectory(False)
ROOT.gROOT.SetBatch(True)

_ecm = "240"          # the S365 copy differs in _ecm, lumi and the header text
lumi = 10800000.      # pb-1 (arXiv:2512.21290: 10.8 ab-1 at 240, 3.12 ab-1 at 365)
BES_TAG = "1pc"       # dedicated BES samples wzp6_ee_<z>H_BES-{higher,lower}-<tag>

STORE = "/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper"
HERE = os.path.dirname(os.path.abspath(__file__))

_z_had = ["qq", "ss", "cc", "bb"]
_z_other = ["ee", "mumu", "tautau", "nunu"]
_z_all = _z_had + _z_other
_h_decays = ["Hbb", "Hcc", "Hss", "Hgg", "Haa", "HZa", "HWW", "HZZ", "Hmumu", "Htautau", "Hinv"]

CATEGORIES = ["hiBDT", "loBDT"]
RECOIL_CAT = "nomva"    # --recoil-only: the single region = stage2 sel_Baseline_nomva (no BDT cut)
HNAME = "mrecoil_mjj"   # stage2 TH2 (240: 25 x 24 bins over [100,150] x [20,140])
# shape nuisance -> (up selection tag, down selection tag); TH2 = mrecoil_mjj_<tag>
VARIATIONS = {"JETSCALE": ("scaleup", "scaledw"), "SQRTS": ("sqrtsup", "sqrtsdw")}
# --jesjer: shape nuisances on EVERY process (signal and background components); a None down
# tag = the Down template is the bin-wise mirror of Up around the nominal (one-sided smearing)
JESJER = {"JES": ("jesup", "jesdw"), "JER": ("jerup", None)}
JESJER_CARD = "datacard_2d_qq_jesjer.txt"   # datacard_2d_qq.txt + JES/JER shape lines on every process

# run dir / card per signal definition
SETUP = {
    "paper": ("run_2D_mrecoil_mjj_qq", "datacard_2d_qq.txt"),
    "zhbkg": ("run_2D_mrecoil_mjj_qq_zhbkg", "datacard_2d_qq_zhbkg.txt"),
}


def excl_proc(z, h):
    return f"wzp6_ee_{z}H_{h}_ecm{_ecm}"


def incl_proc(z, tag=""):
    """Inclusive-H Z(z)H sample; tag = '' | 'BES-higher-1pc' | 'BES-lower-1pc'."""
    return f"wzp6_ee_{z}H_{tag + '_' if tag else ''}ecm{_ecm}"


def zh_procs(zs, h=None):
    """Exclusive ZH sets of the Z decays zs (one H decay when h is given); nunuH_Hinv excluded."""
    hs = [h] if h else _h_decays
    return [excl_proc(z, hh) for z in zs for hh in hs if not (z == "nunu" and hh == "Hinv")]


def signal_z(zh_other_as_bkg):
    return _z_had if zh_other_as_bkg else _z_all


def bkg_components(zh_other_as_bkg):
    """Background components (1% lnN each); together with the signal exactly the stage1 processList."""
    comps = {
        "bkg_WW":  [f"p8_ee_WW_ecm{_ecm}", f"p8_ee_WW_mumu_ecm{_ecm}", f"p8_ee_WW_ee_ecm{_ecm}"],
        "bkg_ZZ":  [f"p8_ee_ZZ_ecm{_ecm}"],
        "bkg_Zqq": [f"wzp6_ee_qq_ecm{_ecm}"],
    }
    if zh_other_as_bkg:   # July definition: ZH with a non-hadronic Z as a background
        comps["bkg_ZH"] = zh_procs(_z_other)
    comps["bkg_rare"] = ([f"wzp6_ee_tautau_ecm{_ecm}", f"wzp6_ee_mumu_ecm{_ecm}",
                          f"wzp6_ee_ee_Mee_30_150_ecm{_ecm}",
                          f"wzp6_egamma_eZ_Zmumu_ecm{_ecm}", f"wzp6_gammae_eZ_Zmumu_ecm{_ecm}",
                          f"wzp6_egamma_eZ_Zee_ecm{_ecm}", f"wzp6_gammae_eZ_Zee_ecm{_ecm}",
                          f"wzp6_gaga_mumu_60_ecm{_ecm}", f"wzp6_gaga_ee_60_ecm{_ecm}",
                          f"wzp6_gaga_tautau_60_ecm{_ecm}", f"wzp6_ee_nuenueZ_ecm{_ecm}"]
                         + ([f"p8_ee_tt_ecm{_ecm}"] if _ecm == "365" else []))
    return comps


class Stage2:
    """Reader of the stage2 TH2 files with the strict missing-input policy."""

    def __init__(self, base, exclude=(), project=False):
        self.base = base
        self.allow_missing = os.environ.get("FCC_ALLOW_MISSING") == "1"
        self.exclude = set(exclude)   # --exclude: dropped from every process list handed to sum()
        self.project = project        # --recoil-only: sum() returns the m_recoil projection (project_x)

    def fname(self, proc, sel):
        return os.path.join(self.base, f"{proc}_{sel}_histo.root")

    def read(self, proc, sel, hname):
        """UNSCALED TH2 (as stored by stage2), or None if the stage2 file does not exist."""
        fn = self.fname(proc, sel)
        if not os.path.isfile(fn):
            return None
        fIn = ROOT.TFile.Open(fn)
        if not fIn or fIn.IsZombie():
            sys.exit(f"ERROR: cannot open {fn}")
        h = fIn.Get(hname)
        if not h:
            sys.exit(f"ERROR: histogram '{hname}' missing in {fn}")
        h = h.Clone(f"{proc}_{sel}_{hname}")
        h.SetDirectory(0)
        fIn.Close()
        return h

    def sum(self, procs, sel, hname, newname, variation=False):
        """Sum one TH2 over many processes, then scale to lumi (July arithmetic).

        With project=True (--recoil-only) the m_recoil projection of the lumi-scaled sum
        (project_x, a TH1) is returned instead of the TH2.
        Missing stage2 files abort unless FCC_ALLOW_MISSING=1 (warning). With NO input
        at all: variations return None (caller substitutes the nominal, loudly), a
        nominal template always aborts. Processes named by --exclude are skipped; a
        list left empty by the exclusion aborts (no template without a process).
        """
        use = [p for p in procs if p not in self.exclude]
        if procs and not use:
            sys.exit(f"ERROR: {newname} ({sel}/{hname}): every process excluded via --exclude ({procs}) - a "
                     "component without any process cannot be a template; remove it from the datacard instead")
        h, missing = None, []
        for proc in use:
            hist = self.read(proc, sel, hname)
            if hist is None:
                missing.append(proc)
                continue
            if h is None:
                h = hist.Clone(newname)
            else:
                h.Add(hist)
        if missing:
            msg = (f"{newname} ({sel}/{hname}): {len(missing)}/{len(use)} processes "
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
        h.Scale(lumi)
        if self.project:
            return project_x(h, newname)
        return h


def unroll(h2, name):
    """TH2 -> TH1 with nx*ny bins, k = (j-1)*nx + i (m_recoil runs fastest)."""
    nx, ny = h2.GetNbinsX(), h2.GetNbinsY()
    h1 = ROOT.TH1D(name, ";unrolled (m_{recoil} #times m_{jj}) bin;Events",
                   nx * ny, 0.5, nx * ny + 0.5)
    for j in range(1, ny + 1):
        for i in range(1, nx + 1):
            k = (j - 1) * nx + i
            h1.SetBinContent(k, h2.GetBinContent(i, j))
            h1.SetBinError(k, h2.GetBinError(i, j))
    h1.SetDirectory(0)
    return h1


def project_x(h2, name):
    """TH2 -> TH1 over the X axis (m_recoil), the --recoil-only observable: every in-range X bin
    is the sum of its in-range Y (m_jj) bins, errors added in quadrature. The X axis binning is
    kept; under/overflow bins are not carried (empty under the stage2 selection windows anyway)."""
    nx, ny = h2.GetNbinsX(), h2.GetNbinsY()
    ax = h2.GetXaxis()
    if ax.GetXbins().GetSize():
        h1 = ROOT.TH1D(name, ";m_{recoil} (GeV);Events", nx, ax.GetXbins().GetArray())
    else:
        h1 = ROOT.TH1D(name, ";m_{recoil} (GeV);Events", nx, ax.GetXmin(), ax.GetXmax())
    for i in range(1, nx + 1):
        c, e2 = 0.0, 0.0
        for j in range(1, ny + 1):
            c += h2.GetBinContent(i, j)
            e2 += h2.GetBinError(i, j) ** 2
        h1.SetBinContent(i, c)
        h1.SetBinError(i, e2 ** 0.5)
    h1.SetDirectory(0)
    return h1


def template(h, name):
    """Fit template of a working histogram: the unrolled TH2 (default), or a copy of the
    projected TH1 (--recoil-only: Stage2.sum() already projected it)."""
    if h.GetDimension() == 1:
        h1 = h.Clone(name)
        h1.SetDirectory(0)
        return h1
    return unroll(h, name)


def clip_negative(h2):
    """Set negative bins of a TH2 to 0; returns (n clipped, summed negative content).

    Also serves the projected TH1s of --recoil-only: GetNbinsY() is 1 there and ROOT's
    (i, j) accessors of a TH1 address bin i.
    """
    n, tot = 0, 0.0
    for j in range(1, h2.GetNbinsY() + 1):
        for i in range(1, h2.GetNbinsX() + 1):
            c = h2.GetBinContent(i, j)
            if c < 0:
                n += 1
                tot += c
                h2.SetBinContent(i, j, 0.0)
    return n, tot


def mirror_down(nominal, up, name):
    """Down template of a one-sided variation: nominal - (up - nominal) bin-wise, clipped at 0.

    Returns (h, n clipped, summed negative content before the clipping). TH2 or TH1 (see
    clip_negative).
    """
    h = nominal.Clone(name)
    h.Scale(2.0)
    h.Add(up, -1.0)
    n, tot = clip_negative(h)
    return h, n, tot


def scale_to_integral(h, target):
    """Rescale h in place to the integral target (shape-only variation).

    Returns (shift, factor): shift = I(h)/target - 1 BEFORE the scaling, factor =
    target/I(h) applied to every bin (Sumw2 errors follow). A template already at the
    target (a no-op BES copy of the nominal) gets factor 1.0 exactly; an empty or
    negative-integral template aborts (a shape variation must have content).
    """
    i = h.Integral()
    if not (i > 0 and target > 0):
        sys.exit(f"ERROR: cannot rescale {h.GetName()} (integral {i}) to {target}")
    factor = target / i
    h.Scale(factor)
    return i / target - 1.0, factor


def one_bin_card(src, dst, cat):
    """Write the ONE-bin derivation of the two-region card src to dst (--recoil-only): imax 1,
    the observation and process-block columns of the card's FIRST bin only, that bin renamed
    cat, every nuisance line reduced to those columns (same nuisances, same values). The comment
    header of src is kept behind a note. Only the line kinds of datacard_2d_qq[_zhbkg].txt are
    understood (imax/jmax/kmax, shapes, bin/observation, bin/process/rate, column-form lnN /
    lnU / shape* nuisances); anything else (a rateParam, ...) aborts.
    """
    with open(src) as fh:
        lines = fh.readlines()
    out = [f"# ONE-bin derivation of {os.path.basename(src)} by makeWS_2D_qq.py --recoil-only (cut-based fit):\n",
           f"# one region '{cat}' = stage2 sel_Baseline_{cat} (no BDT cut), observable = the m_recoil projection\n",
           f"# of {HNAME}; the columns of one bin, the same nuisances. The file name and the run dir name\n",
           "# run_2D_mrecoil_mjj_qq<tag> (the '2D' being historical here) are kept for run_fit_qq.sh /\n",
           "# run_fit_combination.sh / bias_test_generic.py. Header of the source card:\n"]
    first, keep, n_bin_lines = None, None, 0
    for raw in lines:
        f = raw.split("#")[0].split()
        if not f:                                   # comment or blank line
            out.append(raw)
            continue
        key = f[0]
        if key == "imax":
            out.append("imax 1\n")
        elif key in ("jmax", "kmax", "shapes") or key.startswith("--"):
            out.append(raw)
        elif key == "bin":
            n_bin_lines += 1
            if n_bin_lines == 1:                    # observation block: the bins
                first = f[1]
                out.append(f"bin           {cat}\n")
            elif n_bin_lines == 2:                  # process block: the columns of the first bin
                keep = [i for i, b in enumerate(f[1:]) if b == first]
                ncol = len(f) - 1
                if not keep:
                    sys.exit(f"ERROR: {src}: no process column of bin {first!r}")
                out.append("bin       " + "  ".join([cat] * len(keep)) + "\n")
            else:
                sys.exit(f"ERROR: {src}: more than two 'bin' lines")
        elif key == "observation":
            out.append("observation   -1\n")
        elif key in ("process", "rate"):
            if keep is None or len(f) - 1 != ncol:
                sys.exit(f"ERROR: {src}: '{key}' line before the process-block 'bin' line or with a column mismatch")
            out.append(f"{key:9s} " + "  ".join(f[1 + i] for i in keep) + "\n")
        elif len(f) > 2 and f[1] in ("lnN", "lnU", "shape", "shapeN2", "shapeU"):
            if keep is None or len(f) - 2 != ncol:
                sys.exit(f"ERROR: {src}: nuisance line {key!r} before the process block or with a column mismatch")
            out.append(f"{key:10s} {f[1]:6s} " + "  ".join(f[2 + i] for i in keep) + "\n")
        else:
            sys.exit(f"ERROR: {src}: line kind not understood by one_bin_card(): {raw.rstrip()!r}")
    if n_bin_lines != 2:
        sys.exit(f"ERROR: {src}: expected an observation 'bin' line and a process-block 'bin' line")
    with open(dst, "w") as fh:
        fh.writelines(out)


def main():
    global lumi
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zh-other-as-bkg", action="store_true",
                    help="July-2026 definition: signal = hadronic-Z ZH only, other ZH as bkg_ZH, no BES "
                         "(run_2D_mrecoil_mjj_qq_zhbkg/, datacard_2d_qq_zhbkg.txt)")
    ap.add_argument("--bes-keep-norm", action="store_true",
                    help="keep the raw normalization of the BES templates (default: shape-only, each "
                         "signal_BESUp/Down rescaled to the nominal signal integral of its category)")
    ap.add_argument("--exclude", metavar="PROC[,PROC...]", default="",
                    help="drop these stage1 processes from every component they belong to (signal, bkg_*, the "
                         "per-decay bias templates); a name in no component aborts. Paper-faithful 365 GeV fit "
                         "without ttbar: --exclude p8_ee_tt_ecm365 --tag _nott")
    ap.add_argument("--tag", metavar="SUFFIX", default="",
                    help="run dir name suffix: run_2D_mrecoil_mjj_qq[_zhbkg]<SUFFIX> (default none; e.g. _nott); "
                         "the fit drivers take it as QQ_RUNDIR_SUFFIX, bias_test_generic.py as --tag")
    ap.add_argument("--jesjer", action="store_true",
                    help="add the JES and JER shape nuisances on every process (jesup/jesdw/jerup stage2-style files "
                         "from ../qq/stage2_jesjer_templates.py; JER Down = mirror of Up); card "
                         f"{JESJER_CARD}; give a --tag ending in _jesjer")
    ap.add_argument("--jes-only", action="store_true", help="only the JES nuisance (card without the JER line); --tag e.g. _jes")
    ap.add_argument("--jer-only", action="store_true", help="only the JER nuisance (card without the JES line); --tag e.g. _jer")
    ap.add_argument("--recoil-only", action="store_true",
                    help="CUT-BASED hadronic fit (paper Table 2 'Cut-based'): one region sel_Baseline_nomva (no BDT cut), "
                         "the m_recoil projection of the TH2 as the observable of every template, the ONE-bin derivation "
                         "of the card under the same name in the same run dir run_2D_mrecoil_mjj_qq<tag> (the '2D' is "
                         "historical there); requires --tag (e.g. _oldbdt_cutbased); not with --jesjer/--jes-only/--jer-only")
    ap.add_argument("--input-base", metavar="DIR",
                    help="stage2 histogram dir (default STORE/S%s/qq/BDT_analysis_samples/syst)" % _ecm)
    ap.add_argument("--out-base", metavar="DIR", default=HERE,
                    help="parent of the run dir (default: this dir)")
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
    zhbkg = args.zh_other_as_bkg
    mode = "zhbkg" if zhbkg else "paper"
    rd, card = SETUP[mode]
    if args.tag and (os.sep in args.tag or any(c.isspace() for c in args.tag)):
        sys.exit(f"ERROR: --tag {args.tag!r} must be a plain name fragment (no path separator or whitespace)")
    rd += args.tag
    # --jesjer / --jes-only / --jer-only: the JES/JER nuisances to build (paper-spec card only)
    if sum((args.jesjer, args.jes_only, args.jer_only)) > 1:
        sys.exit("ERROR: --jesjer, --jes-only and --jer-only are mutually exclusive")
    jj_systs = list(JESJER) if args.jesjer else (["JES"] if args.jes_only else (["JER"] if args.jer_only else []))
    if jj_systs:
        if zhbkg:
            sys.exit("ERROR: --jesjer / --jes-only / --jer-only apply to the paper-spec card only (not --zh-other-as-bkg)")
        card = JESJER_CARD
        want = {"JES,JER": "_jesjer", "JES": "_jes", "JER": "_jer"}[",".join(jj_systs)]
        if not args.tag.endswith(want):
            print(f"NOTE: --tag {args.tag!r} does not end in {want!r}: the run dir {rd} is the one the fit drivers "
                  f"read as QQ_RUNDIR_SUFFIX={args.tag or '(none)'}; a JES/JER run dir should carry the suffix "
                  f"{want} so that it never replaces the nominal one")
    recoil = args.recoil_only
    if recoil and jj_systs:
        sys.exit("ERROR: --recoil-only is not combinable with --jesjer / --jes-only / --jer-only: the cut-based fit is "
                 "the recoil mass alone in one region (the paper evaluated JES / JER on the MVA-based 2D fit only)")
    if recoil and not args.tag:
        sys.exit("ERROR: --recoil-only requires a --tag (e.g. _oldbdt_cutbased): without one the run dir would be the "
                 f"nominal 2D one, {rd}")
    cats = [RECOIL_CAT] if recoil else CATEGORIES
    W = "1d" if recoil else "2d"   # infix of the working-histogram names: projected TH1 (--recoil-only) / TH2
    exclude = []
    for p in args.exclude.split(","):
        if p.strip() and p.strip() not in exclude:
            exclude.append(p.strip())

    base = args.input_base or f"{STORE}/S{_ecm}/qq/BDT_analysis_samples/syst"
    if not os.path.isdir(base):
        sys.exit(f"ERROR: stage2 input dir {base} does not exist (run 'fccanalysis final' for S{_ecm}/qq first)")
    runDir = os.path.join(os.path.abspath(args.out_base), rd)
    os.makedirs(runDir, exist_ok=True)
    zs = signal_z(zhbkg)
    sig_procs = zh_procs(zs)
    comps = bkg_components(zhbkg)
    # --exclude: every name must belong to a component (typo guard); Stage2.sum() then drops
    # it from every process list it appears in (signal, bkg_*, per-decay, diagnostics)
    components = {"signal": sig_procs, **comps}
    unknown = [p for p in exclude if not any(p in ps for ps in components.values())]
    if unknown:
        sys.exit(f"ERROR: --exclude: {unknown} in no component's process list; known processes: "
                 + ", ".join(sorted({p for ps in components.values() for p in ps})))
    membership = {p: [c for c, ps in components.items() if p in ps] for p in exclude}
    s2 = Stage2(base, exclude, project=recoil)
    n_sig = len([p for p in sig_procs if p not in exclude])
    print(f"== qq @ {_ecm} GeV, lumi {lumi:.4g} pb-1, signal definition: "
          + ("JULY (Z(qq/ss/cc/bb)H, other ZH as bkg_ZH, no BES)" if zhbkg
             else "PAPER (all ZH final states, BES from the inclusive samples)")
          + f"\n== signal: {n_sig} exclusive sets over Z decays {zs}"
          f"\n== stage2 input: {base}\n== run dir: {runDir}\n== card: {card}")
    print("== regions / observable: " + (
        f"ONE region {RECOIL_CAT} (stage2 sel_Baseline_{RECOIL_CAT}, no BDT cut), the m_recoil projection of {HNAME} - "
        "CUT-BASED fit (--recoil-only): the card is the one-bin derivation of the 2D card under the same name, the "
        "'2D' in the run dir name is historical" if recoil else
        f"{CATEGORIES} (stage2 sel_Baseline_<cat>), unrolled {HNAME} - 2D fit"))
    if exclude:
        print(f"== --exclude: {len(exclude)} process(es) dropped from every component: "
              + ", ".join(f"{p} [{'/'.join(membership[p])}]" for p in exclude))
    if not zhbkg:
        print("== BES templates: " + ("RAW normalization kept (--bes-keep-norm)" if args.bes_keep_norm else
                                     "shape-only (rescaled to the nominal signal integral per category)"))
    if jj_systs:
        print(f"== JES/JER nuisances on every process: {jj_systs} (JES from jesup/jesdw, JER from jerup with the "
              f"Down template mirrored around the nominal); card {card}")

    hists, ctl, by_decay = [], [], []   # fit templates, working histograms (TH2, or their projections), per-decay
    yields = {}
    incl_ratio = {}   # (cat, z) -> (I(incl_z), I(sum_h excl_z_h))
    for cat in cats:
        sel = f"sel_Baseline_{cat}"

        sig2d = s2.sum(sig_procs, sel, HNAME, f"{cat}_signal{W}")
        ctl.append(sig2d)
        nom2d = {"signal": sig2d}   # nominal TH2 per process (JES/JER mirror and ratios)
        h_sig = template(sig2d, f"{cat}_signal")
        hists.append(h_sig)
        h_obs = h_sig.Clone(f"{cat}_data_obs")   # Asimov: signal + backgrounds
        yields[cat] = {"signal": h_sig.Integral()}

        for comp, procs in comps.items():
            b2d = s2.sum(procs, sel, HNAME, f"{cat}_{comp}{W}")
            ctl.append(b2d)
            nom2d[comp] = b2d
            hb = template(b2d, f"{cat}_{comp}")
            hists.append(hb)
            h_obs.Add(hb)
            yields[cat][comp] = hb.Integral()
        hists.append(h_obs)
        yields[cat]["data_obs"] = h_obs.Integral()

        # jet scale / sqrt(s): varied selections and observables, whole signal
        for syst, tags in VARIATIONS.items():
            for tag, ud in zip(tags, ("Up", "Down")):
                h2 = s2.sum(sig_procs, f"{sel}_{tag}", f"{HNAME}_{tag}", f"{cat}_signal{W}_{syst}{ud}", variation=True)
                if h2 is None:
                    print(f"WARNING (FCC_ALLOW_MISSING=1): {cat}_signal_{syst}{ud}: no input at all - "
                          f"template = copy of the nominal (no-op nuisance)")
                    h2 = sig2d.Clone(f"{cat}_signal{W}_{syst}{ud}")
                ctl.append(h2)
                hists.append(template(h2, f"{cat}_signal_{syst}{ud}"))

        # JES / JER (--jesjer): every process, varied selections + observables; the JER Down
        # template is the mirror of Up around the nominal (one-sided smearing)
        for syst in jj_systs:
            up_tag, dw_tag = JESJER[syst]
            for pname, procs in [("signal", sig_procs)] + list(comps.items()):
                nom = nom2d[pname]
                h_up = s2.sum(procs, f"{sel}_{up_tag}", f"{HNAME}_{up_tag}", f"{cat}_{pname}{W}_{syst}Up", variation=True)
                if h_up is None:
                    print(f"WARNING (FCC_ALLOW_MISSING=1): {cat}_{pname}_{syst}Up: no input at all - "
                          f"template = copy of the nominal (no-op nuisance)")
                    h_up = nom.Clone(f"{cat}_{pname}{W}_{syst}Up")
                if dw_tag:
                    h_dw = s2.sum(procs, f"{sel}_{dw_tag}", f"{HNAME}_{dw_tag}", f"{cat}_{pname}{W}_{syst}Down", variation=True)
                    if h_dw is None:
                        print(f"WARNING (FCC_ALLOW_MISSING=1): {cat}_{pname}_{syst}Down: no input at all - "
                              f"template = copy of the nominal (no-op nuisance)")
                        h_dw = nom.Clone(f"{cat}_{pname}{W}_{syst}Down")
                    how = "up/down inputs"
                else:
                    h_dw, n_clip, tot_clip = mirror_down(nom, h_up, f"{cat}_{pname}{W}_{syst}Down")
                    how = "Down = mirror of Up around the nominal" + (
                        f", {n_clip} bin(s) clipped at 0 (summed content {tot_clip:.2f} of {h_dw.Integral():.1f})" if n_clip else "")
                i0 = nom.Integral()
                print(f"   {cat}_{pname}_{syst}: I(Up)/I(nom) = {h_up.Integral() / i0 if i0 else float('nan'):.5f}, "
                      f"I(Down)/I(nom) = {h_dw.Integral() / i0 if i0 else float('nan'):.5f}  [{how}]")
                ctl += [h_up, h_dw]
                hists.append(template(h_up, f"{cat}_{pname}_{syst}Up"))
                hists.append(template(h_dw, f"{cat}_{pname}_{syst}Down"))

        # BES: inclusive-H samples per Z decay, nominal selection (paper spec only)
        if not zhbkg:
            incl_nom = {}
            for z in zs:
                hz = s2.sum([incl_proc(z)], sel, HNAME, f"{cat}_incl_{z}", variation=True)
                if hz is not None:
                    ctl.append(hz)
                    incl_nom[z] = hz
                    excl_z = s2.sum(zh_procs([z]), sel, HNAME, f"{cat}_excl_{z}")
                    incl_ratio[(cat, z)] = (hz.Integral(), excl_z.Integral())
            for tag, ud in (("higher", "Up"), ("lower", "Down")):
                delta, contributing = None, []
                for z in zs:
                    if z not in incl_nom:
                        continue
                    hv = s2.sum([incl_proc(z, f"BES-{tag}-{BES_TAG}")], sel, HNAME, f"{cat}_incl_{z}_BES{ud}", variation=True)
                    if hv is None:
                        continue
                    ctl.append(hv)
                    d = hv.Clone(f"{cat}_besdelta_{z}_{ud}")
                    d.Add(incl_nom[z], -1.0)
                    if delta is None:
                        delta = d
                    else:
                        delta.Add(d)
                    contributing.append(z)
                if delta is None:
                    print(f"WARNING (FCC_ALLOW_MISSING=1): {cat}_signal_BES{ud}: no inclusive nominal+BES "
                          f"sample pair for any Z decay - template = copy of the nominal (no-op nuisance)")
                    h2 = sig2d.Clone(f"{cat}_signal{W}_BES{ud}")
                else:
                    missing_z = [z for z in zs if z not in contributing]
                    if missing_z:
                        print(f"WARNING (FCC_ALLOW_MISSING=1): {cat}_signal_BES{ud}: Z decays without an inclusive "
                              f"nominal+BES pair contribute NO BES variation: {missing_z} (used: {contributing})")
                    delta.SetName(f"{cat}_besdelta{W}_{ud}")
                    ctl.append(delta)
                    h2 = sig2d.Clone(f"{cat}_signal{W}_BES{ud}")
                    h2.Add(delta)
                    n, tot = clip_negative(h2)
                    if n:
                        print(f"   {cat}_signal_BES{ud}: {n} bins driven negative by the BES difference "
                              f"(summed content {tot:.2f} of {h2.Integral():.1f}) clipped to 0")
                    print(f"   {cat}_signal_BES{ud}: I = {h2.Integral():.2f} vs nominal {sig2d.Integral():.2f} "
                          f"({100 * (h2.Integral() / sig2d.Integral() - 1):+.3f}%) from Z decays {contributing}")
                # BES is a shape effect: the normalization offset between two independently
                # generated inclusive samples is statistical noise (docstring) - remove it
                if args.bes_keep_norm:
                    print(f"   {cat}_signal_BES{ud}: normalization shift "
                          f"{100 * (h2.Integral() / sig2d.Integral() - 1):+.3f}% KEPT (--bes-keep-norm)")
                else:
                    shift, factor = scale_to_integral(h2, sig2d.Integral())
                    print(f"   {cat}_signal_BES{ud}: shape-only: pre-scaling normalization shift {100 * shift:+.3f}%, "
                          f"scaled by {factor:.6f} -> I = {h2.Integral():.2f}")
                ctl.append(h2)
                hists.append(template(h2, f"{cat}_signal_BES{ud}"))

        # per-H-decay signal templates for the bias test (paper Sec. 7.2): all signal Z decays
        for h in _h_decays:
            hd2 = s2.sum(zh_procs(zs, h), sel, HNAME, f"{cat}_sig{W}_{h}")
            by_decay.append(template(hd2, f"{cat}_sig_{h}"))

    # diagnostics: the inclusive samples vs the exclusive per-decay sums (independent
    # generation: they agree only statistically; the BES template uses the DIFFERENCE
    # of the two inclusive samples, so this offset does not enter the fit)
    if incl_ratio:
        print("== inclusive-H samples vs the exclusive per-H-decay sums (diagnostic; BES uses the "
              "inclusive BES-nominal DIFFERENCE only):")
        for cat in cats:
            i_sum = sum(v[0] for (c, z), v in incl_ratio.items() if c == cat)
            zs_ok = [z for (c, z) in incl_ratio if c == cat]
            print(f"   {cat}: I(sum_z incl_z) / I(signal) = {i_sum:.2f} / {yields[cat]['signal']:.2f} = "
                  f"{i_sum / max(yields[cat]['signal'], 1e-9):.5f}   (Z decays with inclusive input: {zs_ok})")
            for z in zs_ok:
                i_in, i_ex = incl_ratio[(cat, z)]
                print(f"      {z:7s} incl {i_in:12.2f}  excl sum {i_ex:12.2f}  ratio {i_in / max(i_ex, 1e-9):.5f}")

    for cat in cats:
        y = yields[cat]
        bkg = sum(v for k, v in y.items() if k.startswith("bkg_"))
        print(f"{cat}: signal {y['signal']:.1f}, total bkg {bkg:.1f} ["
              + ", ".join(f"{c} {y[c]:.1f}" for c in comps) + f"], S/B {y['signal'] / max(bkg, 1e-9):.3f}")
    if exclude:
        print("== excluded processes (--exclude): in NO template above; their nominal lumi-scaled yields under "
              "sel_Baseline_<cat>, for reference:")
        for p in exclude:
            parts = []
            for cat in cats:
                h = s2.read(p, f"sel_Baseline_{cat}", HNAME)
                if h is None:
                    parts.append(f"{cat} n/a (no stage2 file)")
                else:
                    y = lumi * h.Integral()
                    parts.append(f"{cat} {y:.1f} ({100 * y / max(yields[cat]['signal'], 1e-9):.2f}% of signal)")
            print(f"   {p} [{'/'.join(membership[p])}]: " + ", ".join(parts))

    # combine refuses a process template with null normalization (text2workspace: "Null norm
    # for channel <cat>, process <proc>") and a zero-integral shape variation: catch it here
    empty = [h.GetName() for h in hists if not h.Integral() > 0]
    if empty:
        sys.exit(f"ERROR: template(s) with zero (or negative/NaN) integral: {empty} - combine's "
                 "text2workspace refuses a process with null norm; fix the stage2 input or remove "
                 "the process from the datacard")

    fOut = ROOT.TFile(f"{runDir}/datacard.root", "RECREATE")
    for h in hists:
        h.Write()
    fOut.Close()
    fD = ROOT.TFile(f"{runDir}/signal_by_decay.root", "RECREATE")
    for h in by_decay:
        h.Write()
    fD.Close()
    ctl_file = "templates_recoil.root" if recoil else "templates_2d.root"   # the working histograms
    fCtl = ROOT.TFile(f"{runDir}/{ctl_file}", "RECREATE")
    for h in ctl:
        h.Write()
    fCtl.Close()

    if recoil:
        # the ONE-bin derivation of the two-region card, under the drivers' file name
        one_bin_card(os.path.join(HERE, card), os.path.join(runDir, card), RECOIL_CAT)
        print(f"== card {card} written as its ONE-bin derivation (bin {RECOIL_CAT}, the same nuisances; the 2D card's "
              "file name is kept for the fit drivers)")
    elif jj_systs and set(jj_systs) != set(JESJER):
        # one nuisance only: the jesjer card without the other one's shape line
        drop = [n for n in JESJER if n not in jj_systs]
        with open(os.path.join(HERE, card)) as src, open(os.path.join(runDir, card), "w") as dst:
            for raw in src:
                f = raw.split("#")[0].split()
                if len(f) > 1 and f[1] == "shape" and f[0] in drop:
                    continue
                dst.write(raw)
        print(f"== card {card} copied WITHOUT the {drop} shape line(s) ({'/'.join(jj_systs)} only)")
    else:
        shutil.copy(os.path.join(HERE, card), runDir)
    # the fit drivers take datacard_2d_qq_jesjer.txt when present in the run dir, else
    # datacard_2d_qq.txt: a stale card of the other kind (earlier makeWS run with the other
    # option into the same run dir) must not survive next to fresh templates
    for other in ({SETUP["paper"][1], JESJER_CARD} - {card}) if not zhbkg else ():
        stale = os.path.join(runDir, other)
        if os.path.isfile(stale):
            os.remove(stale)
            print(f"== removed the stale {other} from {runDir} (this run wrote {card})")
    stale = os.path.join(runDir, "templates_2d.root" if recoil else "templates_recoil.root")
    if os.path.isfile(stale):   # control file of the other mode from an earlier run into the same dir
        os.remove(stale)
        print(f"== removed the stale {os.path.basename(stale)} from {runDir} (this run wrote {ctl_file})")
    ret = subprocess.call(f"text2workspace.py {card} -o ws.root", shell=True, cwd=runDir)
    if ret != 0:
        print("NOTE: text2workspace failed (expected outside the combine env) - "
              f"{'QQ_RUNDIR_SUFFIX=' + args.tag + ' ' if args.tag else ''}run_fit_qq.sh "
              f"{'2d-zhbkg' if zhbkg else '2d'} builds ws.root in the combine env"
              f"{' (it takes ' + card + ' from the run dir)' if jj_systs else ''}. "
              f"Templates in {runDir}/datacard.root are complete.")


if __name__ == "__main__":
    main()
