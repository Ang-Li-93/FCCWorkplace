#!/usr/bin/env python3
"""
JES / JER variant histograms for the hadronic (Z->qq) 2D m_recoil x m_jj fit, derived
from the stored stage1 analysis ntuples (no re-simulation), for one energy.

arXiv:2512.21290 Sec. 5.3 evaluated a 1% jet energy scale shift (JES) and an additional
1% Gaussian jet energy smearing (JER, added in quadrature to the nominal resolution) as
relative degradations of the hadronic precision, without including them in the quoted
numbers. Here both become profiled SHAPE nuisances of the hadronic 2D fit: this script
writes, per process, the varied selections and TH2s that makeWS_2D_qq.py picks up like the
existing JETSCALE / SQRTS variations (selection sel_Baseline_<cat>_<tag>, histogram
mrecoil_mjj_<tag>, file <out-dir>/<proc>_sel_Baseline_<cat>_<tag>_histo.root):

  jesup / jesdw   JES: both jets of the Z candidate scaled by k = 1 +- 0.01. Exact on the
                  pair: m' = k m, p' = k p, E' = k E (E = sqrt(p^2 + m^2) of the stored
                  pair), m_recoil'^2 = s - 2 sqrt(s) E' + m'^2. --self-check compares it at
                  k = 1 +- 1e-5 with the stored zqq_*_scaleup/scaledw branches: identical to the
                  float ulp (~1e-5 GeV) for the massless hypotheses; for best_clustering_idx 0
                  the stored JETSCALE branches scale the jet 3-momenta with FIXED jet masses
                  (HiggsTools::lepton_momentum_scale), a different convention that differs from
                  the 4-vector scaling used here by ~2e-4 GeV (240) / ~5e-4 GeV (365) at 1e-5,
                  i.e. ~0.04 (max 0.2) GeV at 240 / ~0.08 (max 0.4) GeV at 365 in m_jj at the
                  1% shift, on those ~20% of the events (the spec asks for the 4-vector scaling).
  jerup           JER: the two jet momenta smeared independently, p_i' = p_i (1 + 0.01 g_i),
                  g_i ~ N(0,1) with a DETERMINISTIC per-event draw (below). The pair is
                  rebuilt from (p1', p2', alpha) with cos(alpha) = -cos(acolinearity), the
                  opening angle of the two jets (HiggsTools::acolinearity_scalar). The
                  exclusive ee_kt hypotheses (best_clustering_idx 1-3) have MASSLESS jets,
                  for which the massless rebuild m^2 = 2 p1 p2 (1 - cos a), p^2 = p1^2 +
                  p2^2 + 2 p1 p2 cos a, E = p1 + p2 reproduces the stored pair to 1e-7. The
                  inclusive-kt hypothesis (idx 0, E-scheme, ~20% of the events at 240) has
                  MASSIVE jets (m_jj off by 2.3% on average, up to 13%, recoil by up to 8 GeV
                  in the massless rebuild), so the rebuild is written as a jet-4-vector
                  scaling that reduces EXACTLY to the stored nominal at g = 0: the jet
                  energies are split as E_i = (E^2 + p_i^2 - p_j^2) / (2E) (the two jets are
                  given the same mass, fixed by the stored pair energy E; E_1 + E_2 = E),
                  then E' = k_1 E_1 + k_2 E_2, p'^2 = p^2 + [p_ml'^2 - p_ml^2] (massless
                  momentum-sum change added to the stored p^2), m'^2 = E'^2 - p'^2, recoil
                  as above. For massless jets this IS the massless rebuild; for k_1 = k_2 it
                  is the exact JES. Only the UP template is produced: the JER 'Down' template
                  is the mirror of Up around the nominal (bin-wise nominal - (up - nominal),
                  clipped at 0), to be built by makeWS_2D_qq.py from the nominal and jerup.
  Deterministic draws: g_1, g_2 are Box-Muller normals from a 64-bit hash (splitmix64
  finalizer) of --seed and the bit patterns of leading_jet_p, subleading_jet_p, acolinearity,
  zqq_recoil_m_best, zqq_m_best, cosThetaMiss of the event: a pure function of the event
  content, hence identical across runs, thread counts and file orders (no dependence on
  rdfentry_, which is not unique in multi-threaded chains). --self-check prints the mean /
  RMS of p_i'/p_i (expected 1.000 / 0.0100), the g_1-g_2 and g-kinematics correlations, and
  --compare-dir checks two productions bin by bin.

Conventions shared with the stage2 config (PAPER/S<ecm>/qq/stage2_histograms_syst.py, which is
IMPORTED so the windows, MVA working point, process list, binning and procDict are the same
object, never a copy): the baseline selection is re-applied per variant with the varied
m / p / recoil (the mva_score[0] category cut is unchanged - the BDT score is NOT
recomputed under JES/JER, the convention of the existing JETSCALE treatment), categories
hiBDT / loBDT (the fit) and nomva (control), the TH2 mrecoil_mjj_<tag> with the stage2
binning, plus 1D controls recoil_m_<tag>, zqq_m_<tag>, zqq_p_<tag> and BDT_Score. NB stage1
hard-cuts the NOMINAL m_jj and p_jj at the window edges, so under a 1% shift/smearing the
varied m/p windows can only LOSE events at the edges (one-sided migration; the recoil window,
not cut at stage1, migrates both ways); --self-check prints the sizes.

Normalization exactly as 'fccanalysis final' (FCCAnalyses-winter2023 run_final_analysis.py):
every TH is filled unweighted from ONE RDataFrame over <proc>.root and/or <proc>/chunk*.root
of the stage dir, then Scale(crossSection * kfactor * matchingEfficiency * intLumi / sum of
the chunks' eventsProcessed TParameters), the procDict resolved through $FCCDICTSDIR like the
runner, intLumi / doScale from the config (defaults 1.0 / True, i.e. per pb-1; makeWS scales
to the luminosity); TH1::Scale enables Sumw2 (errors sqrt(N) x scale). The same TParameters as
the stage2 files are written. --self-check fills the NOMINAL mrecoil_mjj through this code path
and compares it bin by bin (contents and errors, all cells incl. under/overflow) with the
stage2 file <ref-dir>/<proc>_sel_Baseline_<cat>_histo.root: max relative difference < 1e-9
required, otherwise the replication is wrong and the run exits 1. Everything else printed by
--self-check (JES at 1e-5 vs the stored branches, JER at sigma = 0 vs the nominal, the
massless-rebuild diagnostic per best_clustering_idx, edge migrations) is diagnostic.

Output files are new names next to the stage2 files (the stage2 files are never touched);
per process one line with the raw / xsec-scaled yields per category and the relative changes
of jesup / jesdw / jerup.

Run in the key4hep env:
  python3 qq_jesjer_templates.py --ecm 240|365 [--stage-dir DIR] [--out-dir DIR] [--ref-dir DIR]
                                 [--procs P1,P2,...] [--nthreads N] [--seed S] [--self-check | --check-nominal]
                                 [--compare-dir DIR]
  --stage-dir   stage1 ntuple dir, default STORE/S<ecm>/qq/BDT_analysis_samples_oldbdt (alias --input-dir)
  --out-dir     default <stage-dir>/syst (next to the stage2 files) (alias --output-dir)
  --ref-dir     stage2 files for the --self-check nominal comparison, default <stage-dir>/syst
  --procs       restrict to these processes (must be in the stage2 process list)
  --nthreads    ROOT implicit MT (default 1); the production pass uses 8 once the node is free (alias --ncpu)
  --seed        JER hash seed (default 20260929); a different seed = an independent smearing
  --check-nominal  only the bit-exact nominal comparison of --self-check (production pass guard, ~40% extra; alias --check)
  Per-energy wrappers S<ecm>/qq/stage2_jesjer_templates.py forward to this script with --ecm set
  (the name makeWS_2D_qq.py --jesjer refers to).
  --compare-dir compare every written mrecoil_mjj_<tag> with the same file there (reproducibility)
"""
import argparse
import contextlib
import glob
import importlib.util
import io
import json
import os
import re
import sys
import time

import ROOT

PAPER = os.path.dirname(os.path.abspath(__file__))
STORE = "/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper"
FCCDICTS_FALLBACK = "/cvmfs/fcc.cern.ch/FCCDicts"

JES_SHIFT = 0.01      # jet energy scale, both jets, +- (paper Sec. 5.3: 1%)
JER_SIGMA = 0.01      # additional Gaussian jet momentum smearing per jet (paper: 1%)
HNAME = "mrecoil_mjj"
CATEGORIES = {"hiBDT": "hi", "loBDT": "lo", "nomva": None}   # stage2 _sel() mva argument
TAGS = ["jesup", "jesdw", "jerup"]
NOMINAL = {"m": "zqq_m_best", "p": "zqq_p_best", "r": "zqq_recoil_m_best"}
SELF_CHECK_TOL = 1e-9

CPP = r"""
#include <cstdint>
#include <cstring>
#include <cmath>
#include <algorithm>
namespace jesjer {
struct Kin { double m; double p; double r; };
struct G2  { double g1; double g2; };
inline double signed_sqrt(double x) { return x >= 0.0 ? std::sqrt(x) : -std::sqrt(-x); }   // TLorentzVector::M() convention
inline double pair_energy(double m, double p) { return std::sqrt(p * p + m * m); }
// JES: both jet 4-vectors scaled by k -> exact on the pair (m' = k m, p' = k p, E' = k E)
inline Kin jes(float m_, float p_, double k, double ecm) {
    const double m = m_, p = p_;
    const double mv = k * m, pv = k * p, Ev = k * pair_energy(m, p);
    return {mv, pv, signed_sqrt(ecm * ecm - 2.0 * ecm * Ev + mv * mv)};
}
// JER: jet i scaled by k_i; jet energies split with equal jet masses fixed by the stored pair
// energy (E_1 + E_2 = E exactly); the massless momentum-sum change is added to the stored p^2.
// k_1 = k_2 = 1 returns the stored (m, p, recoil) up to double rounding.
inline Kin jer(float m_, float p_, float p1_, float p2_, float aco_, double k1, double k2, double ecm) {
    const double m = m_, p = p_, p1 = p1_, p2 = p2_;
    const double E = pair_energy(m, p);
    const double E1 = (E * E + p1 * p1 - p2 * p2) / (2.0 * E), E2 = E - E1;
    const double ca = -std::cos((double)aco_);                    // cos(opening angle)
    const double dp2 = (k1 * k1 - 1.0) * p1 * p1 + (k2 * k2 - 1.0) * p2 * p2 + 2.0 * (k1 * k2 - 1.0) * p1 * p2 * ca;
    const double Ev = k1 * E1 + k2 * E2, pv2 = p * p + dp2, mv2 = Ev * Ev - pv2;
    return {signed_sqrt(mv2), std::sqrt(std::max(pv2, 0.0)), signed_sqrt(ecm * ecm - 2.0 * ecm * Ev + mv2)};
}
// massless rebuild of the pair mass from (p1, p2, alpha): diagnostic only
inline double m_massless(float p1_, float p2_, float aco_) {
    const double p1 = p1_, p2 = p2_, ca = -std::cos((double)aco_);
    return std::sqrt(std::max(2.0 * p1 * p2 * (1.0 - ca), 0.0));
}
// deterministic per-event standard normals: splitmix64 mixing of the seed and the event content
inline uint64_t mix64(uint64_t z) {
    z += 0x9E3779B97F4A7C15ULL;
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}
inline uint64_t fbits(float f) { uint32_t u; std::memcpy(&u, &f, sizeof u); return u; }
inline G2 gauss2(uint64_t seed, float a, float b, float c, float d, float e, float f) {
    uint64_t h = mix64(seed);
    h = mix64(h ^ (fbits(a) | (fbits(b) << 32)));
    h = mix64(h ^ (fbits(c) | (fbits(d) << 32)));
    h = mix64(h ^ (fbits(e) | (fbits(f) << 32)));
    const uint64_t u1 = mix64(h), u2 = mix64(u1 ^ 0x5851F42D4C957F2DULL);
    const double x = ((double)(u1 >> 11) + 0.5) * (1.0 / 9007199254740992.0);   // (0,1)
    const double y = (double)(u2 >> 11) * (1.0 / 9007199254740992.0);           // [0,1)
    const double rad = std::sqrt(-2.0 * std::log(x));
    return {rad * std::cos(2.0 * M_PI * y), rad * std::sin(2.0 * M_PI * y)};
}
}
"""


def load_stage2_config(ecm):
    """Import PAPER/S<ecm>/qq/stage2_histograms_syst.py (its stdout, the live-dir WARNING, is muted)."""
    path = os.path.join(PAPER, f"S{ecm}", "qq", "stage2_histograms_syst.py")
    if not os.path.isfile(path):
        sys.exit(f"ERROR: stage2 config {path} not found")
    spec = importlib.util.spec_from_file_location(f"stage2_qq_{ecm}", path)
    cfg = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(cfg)
    for attr in ("ecm", "_all_procs", "_sel", "MVA_WP", "_bins2d", "histoList", "procDict"):
        if not hasattr(cfg, attr):
            sys.exit(f"ERROR: {path} has no '{attr}' - the stage2 config layout changed, adapt this script")
    if int(cfg.ecm) != int(ecm):
        sys.exit(f"ERROR: {path} declares ecm = {cfg.ecm}, expected {ecm}")
    if cfg.histoList.get(HNAME, {}).get("bins") != cfg._bins2d:
        sys.exit(f"ERROR: histoList['{HNAME}'] binning differs from _bins2d in {path}")
    return cfg, path


def parse_windows(cfg):
    """(lo, hi) of the m / p / recoil windows from the config's _sel() template; verified by re-rendering."""
    tpl = cfg._sel("M", "P", "R")
    win = {}
    for var, op, val in re.findall(r"\b([MPR])\s*([<>])\s*([0-9.]+)", tpl):
        win.setdefault(var, {})[op] = float(val)
    try:
        win = {v: (win[v][">"], win[v]["<"]) for v in "MPR"}
    except KeyError:
        sys.exit(f"ERROR: cannot parse the m/p/recoil windows from the stage2 _sel() template: {tpl!r}")
    rendered = " && ".join(f"{v} > {lo:g} && {v} < {hi:g}" for v, (lo, hi) in win.items())
    if re.sub(r"\s+", " ", rendered) != re.sub(r"\s+", " ", tpl).strip():
        sys.exit(f"ERROR: window re-rendering {rendered!r} != stage2 template {tpl!r}")
    return win


def resolve_procdict(name):
    """Like FCCAnalyses process.get_process_dict: absolute/local path, then $FCCDICTSDIR, then cvmfs."""
    dirs = [""] + [d for d in os.environ.get("FCCDICTSDIR", "").split(":") if d] + [FCCDICTS_FALLBACK]
    for d in dirs:
        p = os.path.join(d, name)
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                return json.load(f), p
    sys.exit(f"ERROR: process dictionary {name} not found in {dirs}")


def input_files(stage_dir, proc):
    """(files, sum of eventsProcessed): <proc>.root and/or <proc>/chunk*.root, as the runner."""
    files = []
    single = os.path.join(stage_dir, proc + ".root")
    if os.path.isfile(single):
        files.append(single)
    d = os.path.join(stage_dir, proc)
    if os.path.isdir(d):
        files += sorted(glob.glob(os.path.join(d, "chunk*.root")))
    n_proc = 0
    for fn in files:
        f = ROOT.TFile.Open(fn)
        if not f or f.IsZombie():
            sys.exit(f"ERROR: cannot open {fn}")
        par = f.Get("eventsProcessed")
        if par:
            n_proc += int(par.GetVal())
        else:
            print(f"WARNING: {fn} has no eventsProcessed TParameter (counted as 0, like the runner)", flush=True)
        f.Close()
    return files, n_proc


def process_list(cfg, stage_dir, only):
    """The stage2 process list restricted to what exists in stage_dir (chunks or a single file)."""
    procs = []
    for p in cfg._all_procs:
        if only is not None and p not in only:
            continue
        if glob.glob(os.path.join(stage_dir, p, "chunk*.root")) or os.path.isfile(os.path.join(stage_dir, p + ".root")):
            procs.append(p)
        else:
            print(f"WARNING: no stage1 output for {p} in {stage_dir}, skipped", flush=True)
    return procs


def compare_hists(a, b):
    """(max rel diff of contents, max rel diff of errors, cells with different content) over ALL cells."""
    if (a.GetNbinsX(), a.GetNbinsY()) != (b.GetNbinsX(), b.GetNbinsY()):
        return float("inf"), float("inf"), 0
    dc = de = 0.0
    ndiff = 0
    for j in range(0, a.GetNbinsY() + 2):
        for i in range(0, a.GetNbinsX() + 2):
            ca, cb = a.GetBinContent(i, j), b.GetBinContent(i, j)
            ea, eb = a.GetBinError(i, j), b.GetBinError(i, j)
            m = max(abs(ca), abs(cb))
            if m > 0:
                dc = max(dc, abs(ca - cb) / m)
            if ca != cb:
                ndiff += 1
            m = max(abs(ea), abs(eb))
            if m > 0:
                de = max(de, abs(ea - eb) / m)
    return dc, de, ndiff


def integral(h):
    """Integral over the regular bins (what makeWS_2D_qq.py uses)."""
    return h.Integral(1, h.GetNbinsX(), 1, h.GetNbinsY()) if h.GetDimension() == 2 else h.Integral(1, h.GetNbinsX())


def rel(y, y0):
    return f"{100 * (y / y0 - 1):+.3f}%" if y0 else "n/a"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ecm", type=int, required=True, choices=(240, 365))
    ap.add_argument("--stage-dir", "--input-dir", metavar="DIR", help="stage1 ntuple dir (alias --input-dir)")
    ap.add_argument("--out-dir", "--output-dir", metavar="DIR", help="default <stage-dir>/syst (alias --output-dir)")
    ap.add_argument("--ref-dir", metavar="DIR", help="stage2 files for the --self-check nominal comparison")
    ap.add_argument("--procs", metavar="P1,P2,...", default="")
    ap.add_argument("--nthreads", "--ncpu", type=int, default=1, help="ROOT implicit MT threads (alias --ncpu)")
    ap.add_argument("--seed", type=int, default=20260929)
    ap.add_argument("--self-check", action="store_true", help="full validation (implies --check-nominal)")
    ap.add_argument("--check-nominal", "--check", action="store_true",
                    help="also fill the nominal mrecoil_mjj and require it bit-identical to the stage2 file of every "
                         "process (the per-process summary then shows the relative changes); ~40%% more work")
    ap.add_argument("--compare-dir", metavar="DIR")
    args = ap.parse_args()

    ecm = args.ecm
    need_nominal = args.self_check or args.check_nominal
    stage_dir = os.path.abspath(args.stage_dir or f"{STORE}/S{ecm}/qq/BDT_analysis_samples_oldbdt")
    out_dir = os.path.abspath(args.out_dir or os.path.join(stage_dir, "syst"))
    ref_dir = os.path.abspath(args.ref_dir or os.path.join(stage_dir, "syst"))
    if not os.path.isdir(stage_dir):
        sys.exit(f"ERROR: stage dir {stage_dir} does not exist")
    os.makedirs(out_dir, exist_ok=True)
    if not 0 <= args.seed < 2 ** 64:
        sys.exit("ERROR: --seed must be in [0, 2^64) (a uint64 literal in the JIT code)")
    if args.compare_dir and not os.path.isdir(args.compare_dir):
        sys.exit(f"ERROR: --compare-dir {args.compare_dir} is not a directory")

    cfg, cfg_path = load_stage2_config(ecm)
    windows = parse_windows(cfg)
    proc_dict, proc_dict_path = resolve_procdict(cfg.procDict)
    int_lumi = float(getattr(cfg, "intLumi", 1.0))     # runner defaults
    do_scale = bool(getattr(cfg, "doScale", True))
    only = None
    if args.procs.strip():
        only = [p.strip() for p in args.procs.split(",") if p.strip()]
        unknown = [p for p in only if p not in cfg._all_procs]
        if unknown:
            sys.exit(f"ERROR: --procs {unknown} not in the stage2 process list of {cfg_path}")
    procs = process_list(cfg, stage_dir, only)
    if not procs:
        sys.exit("ERROR: no process with stage1 output to run over")

    ROOT.gROOT.SetBatch(True)
    ROOT.gErrorIgnoreLevel = ROOT.kWarning
    if args.nthreads > 1:
        ROOT.ROOT.EnableImplicitMT(args.nthreads)
    if not ROOT.gInterpreter.Declare(CPP):
        sys.exit("ERROR: the JES/JER C++ helpers failed to compile")

    bins2d = tuple(i for sub in cfg._bins2d for i in sub)
    h1d = {k: cfg.histoList[k] for k in ("recoil_m", "zqq_m", "zqq_p", "BDT_Score") if k in cfg.histoList}
    for k, v in h1d.items():
        if "name" not in v:
            sys.exit(f"ERROR: stage2 histoList['{k}'] is not a 1D 'name' histogram")
    k_up, k_dw = 1.0 + JES_SHIFT, 1.0 - JES_SHIFT
    wm, wp, wr = windows["M"], windows["P"], windows["R"]
    ecm_s = repr(float(ecm))

    def window(col, lo_hi):
        return f"({col} > {lo_hi[0]:g} && {col} < {lo_hi[1]:g})"

    print(f"== JES/JER templates qq @ {ecm} GeV: JES +-{JES_SHIFT:g} (both jets), JER sigma {JER_SIGMA:g} per jet, seed {args.seed}"
          f"\n== stage2 config: {cfg_path} (MVA_WP {cfg.MVA_WP}, windows m {wm} p {wp} recoil {wr}, {HNAME} bins {bins2d})"
          f"\n== procDict: {proc_dict_path}  intLumi {int_lumi:g}  doScale {do_scale}"
          f"\n== stage dir: {stage_dir}\n== out dir:   {out_dir}\n== ref dir:   {ref_dir}"
          f"\n== {len(procs)} processes, {args.nthreads} thread(s), self-check {'ON' if args.self_check else 'off'}, "
          f"nominal check {'ON' if need_nominal else 'off'}"
          + (f", compare-dir {args.compare_dir}" if args.compare_dir else ""), flush=True)

    n_done, failures, compared, n_ref = 0, [], [0, 0], 0
    t_all = time.time()
    for proc in procs:
        t0 = time.time()
        files, n_processed = input_files(stage_dir, proc)
        if n_processed == 0:
            sys.exit(f"ERROR: {proc}: the number of processed events is zero - cannot scale (the runner aborts too)")
        info = proc_dict.get(proc)
        if info is None:
            sys.exit(f"ERROR: {proc} not in the process dictionary - the runner would scale by xsec 1.0; refusing")
        xsec, kfactor, matching = info["crossSection"], info["kfactor"], info["matchingEfficiency"]
        gen_sf = xsec * kfactor * matching
        factor = gen_sf * int_lumi / n_processed        # runner: gen_sf * int_lumi / process_events

        vfiles = ROOT.std.vector("string")()
        for fn in files:
            vfiles.push_back(fn)
        df = ROOT.RDataFrame("events", vfiles)

        # varied kinematics
        df = (df.Define("jj_g", f"jesjer::gauss2({args.seed}ULL, leading_jet_p, subleading_jet_p, acolinearity, "
                                "zqq_recoil_m_best, zqq_m_best, cosThetaMiss)")
                .Define("jer_k1", f"1.0 + {JER_SIGMA!r} * jj_g.g1")
                .Define("jer_k2", f"1.0 + {JER_SIGMA!r} * jj_g.g2")
                .Define("kin_jesup", f"jesjer::jes(zqq_m_best, zqq_p_best, {k_up!r}, {ecm_s})")
                .Define("kin_jesdw", f"jesjer::jes(zqq_m_best, zqq_p_best, {k_dw!r}, {ecm_s})")
                .Define("kin_jerup", f"jesjer::jer(zqq_m_best, zqq_p_best, leading_jet_p, subleading_jet_p, acolinearity, "
                                     f"jer_k1, jer_k2, {ecm_s})"))
        cols = {"": (NOMINAL["m"], NOMINAL["p"], NOMINAL["r"])}
        for tag in TAGS:
            df = (df.Define(f"zqq_m_{tag}", f"kin_{tag}.m")
                    .Define(f"zqq_p_{tag}", f"kin_{tag}.p")
                    .Define(f"zqq_recoil_m_{tag}", f"kin_{tag}.r"))
            cols[tag] = (f"zqq_m_{tag}", f"zqq_p_{tag}", f"zqq_recoil_m_{tag}")

        # selections and histograms (lazy); the nominal only with --self-check
        hists = {}    # (cat, tag) -> {hname: RResultPtr}
        counts = {}
        for cat, mva in CATEGORIES.items():
            for tag in ([""] if need_nominal else []) + TAGS:
                m_col, p_col, r_col = cols[tag]
                dfc = df.Filter(cfg._sel(m_col, p_col, r_col, mva))
                sfx = f"_{tag}" if tag else ""
                hh = {HNAME + sfx: dfc.Histo2D((HNAME + sfx, "", *bins2d), r_col, m_col)}
                for k, v in h1d.items():
                    col = {"recoil_m": r_col, "zqq_m": m_col, "zqq_p": p_col}.get(k, v["name"])
                    name = k + (sfx if k != "BDT_Score" else "")
                    hh[name] = dfc.Histo1D(ROOT.RDF.TH1DModel(name, f';{v["title"]};', v["bin"], v["xmin"], v["xmax"]), col)
                hists[(cat, tag)] = hh
                counts[(cat, tag)] = dfc.Count()

        checks = {}
        if args.self_check:
            df = (df.Define("kin_su", f"jesjer::jes(zqq_m_best, zqq_p_best, {1.0 + 1e-5!r}, {ecm_s})")
                    .Define("kin_sd", f"jesjer::jes(zqq_m_best, zqq_p_best, {1.0 - 1e-5!r}, {ecm_s})")
                    .Define("kin_jer0", f"jesjer::jer(zqq_m_best, zqq_p_best, leading_jet_p, subleading_jet_p, acolinearity, "
                                        f"1.0, 1.0, {ecm_s})")
                    .Define("jj_mml_rel", "jesjer::m_massless(leading_jet_p, subleading_jet_p, acolinearity) / zqq_m_best - 1.0")
                    .Define("jj_g1g2", "jj_g.g1 * jj_g.g2")
                    .Define("jj_g1p1", "jj_g.g1 * leading_jet_p")
                    .Define("jj_g2p2", "jj_g.g2 * subleading_jet_p"))
            stored = {"m": "zqq_m_", "p": "zqq_p_", "r": "zqq_recoil_m_"}
            for tag, kin in (("scaleup", "kin_su"), ("scaledw", "kin_sd")):
                for q in ("m", "p", "r"):
                    c = f"jj_d_{tag}_{q}"
                    df = df.Define(c, f"std::abs({kin}.{q} - (double){stored[q]}{tag})")
                    checks[c] = df.Max(c)
            for q in ("m", "p", "r"):
                c = f"jj_d_jer0_{q}"
                df = df.Define(c, f"std::abs(kin_jer0.{q} - (double){NOMINAL[q]})")
                checks[c] = df.Max(c)
            for c in ("jer_k1", "jer_k2", "jj_g1g2", "jj_g1p1", "jj_g2p2", "leading_jet_p", "subleading_jet_p"):
                checks["mean_" + c] = df.Mean(c)
                checks["std_" + c] = df.StdDev(c)
            checks["n_all"] = df.Count()
            for idx in range(4):
                dfi = df.Filter(f"best_clustering_idx == {idx}")
                checks[f"idx{idx}_n"] = dfi.Count()
                checks[f"idx{idx}_mml_mean"] = dfi.Mean("jj_mml_rel")
                checks[f"idx{idx}_mml_min"] = dfi.Min("jj_mml_rel")
                checks[f"idx{idx}_mml_max"] = dfi.Max("jj_mml_rel")
            # JER at sigma = 0 through the nominal selection: must reproduce the nominal TH2
            m0, p0, r0 = "zqq_m_jer0", "zqq_p_jer0", "zqq_recoil_m_jer0"
            df = df.Define(m0, "kin_jer0.m").Define(p0, "kin_jer0.p").Define(r0, "kin_jer0.r")
            for cat, mva in CATEGORIES.items():
                checks[f"h_jer0_{cat}"] = df.Filter(cfg._sel(m0, p0, r0, mva)).Histo2D((f"{HNAME}_jer0_{cat}", "", *bins2d), r0, m0)
            # edge migrations w.r.t. the nominal nomva selection (m/p: one-sided, recoil: two-sided)
            nom_full = cfg._sel(*cols[""])
            nom_mp = f"({window(cols[''][0], wm)} && {window(cols[''][1], wp)})"
            for tag in TAGS:
                m_col, p_col, r_col = cols[tag]
                mp_var = f"({window(m_col, wm)} && {window(p_col, wp)})"
                checks[f"lost_mp_{tag}"] = df.Filter(f"({nom_full}) && !{mp_var}").Count()
                checks[f"lost_r_{tag}"] = df.Filter(f"({nom_full}) && {mp_var} && !{window(r_col, wr)}").Count()
                checks[f"gain_r_{tag}"] = df.Filter(f"!({nom_full}) && {nom_mp} && {mp_var} && {window(r_col, wr)}").Count()

        # event loop, then scale everything once (runner: h.Scale(gen_sf * int_lumi / process_events))
        n_all = df.Count().GetValue()
        if do_scale:
            for hh in hists.values():
                for rp in hh.values():
                    rp.GetValue().Scale(factor)
            for cat in CATEGORIES:
                if f"h_jer0_{cat}" in checks:
                    checks[f"h_jer0_{cat}"].GetValue().Scale(factor)

        # write the variant files
        for (cat, tag), hh in hists.items():
            if not tag:
                continue
            fname = os.path.join(out_dir, f"{proc}_sel_Baseline_{cat}_{tag}_histo.root")
            tmp = fname + ".tmp"
            fout = ROOT.TFile(tmp, "RECREATE")
            if not fout or fout.IsZombie():
                sys.exit(f"ERROR: cannot create {tmp}")
            for rp in hh.values():
                rp.GetValue().Write()
            ROOT.TParameter(int)("eventsProcessed", n_processed).Write()
            ROOT.TParameter(float)("sumOfWeights", float(n_processed)).Write()
            ROOT.TParameter(float)("intLumi", int_lumi).Write()
            ROOT.TParameter(float)("crossSection", xsec).Write()
            ROOT.TParameter(float)("kfactor", kfactor).Write()
            ROOT.TParameter(float)("matchingEfficiency", matching).Write()
            fout.Close()
            os.replace(tmp, fname)
            if args.compare_dir:
                other = os.path.join(args.compare_dir, os.path.basename(fname))
                if os.path.isfile(other):
                    fo = ROOT.TFile.Open(other)
                    ho = fo.Get(f"{HNAME}_{tag}")
                    dc, de, nd = compare_hists(hh[f"{HNAME}_{tag}"].GetValue(), ho) if ho else (float("inf"), float("inf"), -1)
                    fo.Close()
                    compared[0] += 1
                    if dc > 0 or de > 0:
                        compared[1] += 1
                        print(f"   COMPARE {os.path.basename(fname)}: {nd} cells differ, max rel diff content {dc:.3e} errors {de:.3e}", flush=True)

        # summary line: raw / xsec-scaled yields per category, relative changes of the variants
        parts = []
        for cat in CATEGORIES:
            if need_nominal:
                y0 = integral(hists[(cat, "")][HNAME].GetValue())
                parts.append(f"{cat} nom {counts[(cat, '')].GetValue()} ({y0:.4e}) "
                             + " ".join(f"{tag} {rel(integral(hists[(cat, tag)][f'{HNAME}_{tag}'].GetValue()), y0)}" for tag in TAGS))
            else:
                parts.append(f"{cat} " + " ".join(f"{tag} {counts[(cat, tag)].GetValue()} "
                                                  f"({integral(hists[(cat, tag)][f'{HNAME}_{tag}'].GetValue()):.4e})" for tag in TAGS))
        print(f"{proc}: {n_all} events, {len(files)} files, eventsProcessed {n_processed}, scale {factor:.6e} | "
              + " | ".join(parts) + f" | {time.time() - t0:.0f}s", flush=True)

        if need_nominal:
            ok = True
            # 1. nominal replication vs the stage2 files; 2. JER at sigma = 0 vs the nominal (--self-check)
            for cat in CATEGORIES:
                h_mine = hists[(cat, "")][HNAME].GetValue()
                ref = os.path.join(ref_dir, f"{proc}_sel_Baseline_{cat}_histo.root")
                if os.path.isfile(ref):
                    fr = ROOT.TFile.Open(ref)
                    href = fr.Get(HNAME)
                    if not href:
                        print(f"   SELF-CHECK {cat}: {HNAME} missing in {ref} -> FAIL", flush=True)
                        ok = False
                    else:
                        dc, de, nd = compare_hists(h_mine, href)
                        same = dc < SELF_CHECK_TOL and de < SELF_CHECK_TOL
                        n_ref += 1
                        print(f"   SELF-CHECK {cat}: nominal {HNAME} vs stage2: entries {h_mine.GetEntries():.0f}/{href.GetEntries():.0f}, "
                              f"integral {integral(h_mine):.6e}/{integral(href):.6e}, max rel diff content {dc:.2e} errors {de:.2e}, "
                              f"{nd} cells differ -> {'PASS' if same else 'FAIL'}", flush=True)
                        ok &= same
                    fr.Close()
                else:
                    print(f"   SELF-CHECK {cat}: no stage2 reference {ref} (nominal not compared)", flush=True)
                if not args.self_check:
                    continue
                dc0, de0, nd0 = compare_hists(h_mine, checks[f"h_jer0_{cat}"].GetValue())
                print(f"   SELF-CHECK {cat}: JER(sigma=0) vs nominal: {nd0} cells differ, max rel diff {dc0:.2e}"
                      + (" (bin-edge rounding, double vs stored float, O(1) events expected)" if nd0 else ""), flush=True)
            if not ok:
                failures.append(proc)
        if args.self_check:
            # 3. JES formulas at k = 1 +- 1e-5 vs the stored scaleup/scaledw branches; JER(0) vs the stored nominal
            for tag, sign in (("scaleup", "+"), ("scaledw", "-")):
                print(f"   SELF-CHECK JES k = 1{sign}1e-5 vs stored zqq_*_{tag}: max |diff| "
                      f"m {checks[f'jj_d_{tag}_m'].GetValue():.2e}  p {checks[f'jj_d_{tag}_p'].GetValue():.2e}  "
                      f"recoil {checks[f'jj_d_{tag}_r'].GetValue():.2e} GeV (massless hypotheses idx 1-3: float ulp ~1e-5; "
                      "idx 0: ~2e-4 at 240 / ~5e-4 at 365 GeV, the stored JETSCALE branches keep the jet masses fixed)", flush=True)
            print(f"   SELF-CHECK JER(sigma=0) vs stored nominal: max |diff| m {checks['jj_d_jer0_m'].GetValue():.2e}  "
                  f"p {checks['jj_d_jer0_p'].GetValue():.2e}  recoil {checks['jj_d_jer0_r'].GetValue():.2e} GeV", flush=True)
            # 4. JER draws
            n = checks["n_all"].GetValue()
            g = {c: (checks["mean_" + c].GetValue(), checks["std_" + c].GetValue())
                 for c in ("jer_k1", "jer_k2", "jj_g1g2", "jj_g1p1", "jj_g2p2", "leading_jet_p", "subleading_jet_p")}
            corr1 = (g["jj_g1p1"][0] - (g["jer_k1"][0] - 1) / JER_SIGMA * g["leading_jet_p"][0]) / max(g["leading_jet_p"][1], 1e-12)
            corr2 = (g["jj_g2p2"][0] - (g["jer_k2"][0] - 1) / JER_SIGMA * g["subleading_jet_p"][0]) / max(g["subleading_jet_p"][1], 1e-12)
            print(f"   SELF-CHECK JER p'/p: jet1 mean {g['jer_k1'][0]:.5f} rms {g['jer_k1'][1]:.5f}, jet2 mean {g['jer_k2'][0]:.5f} "
                  f"rms {g['jer_k2'][1]:.5f} (expected 1.00000 / {JER_SIGMA:.5f}, stat. precision {JER_SIGMA / max(n, 1) ** 0.5:.1e}); "
                  f"<g1 g2> {g['jj_g1g2'][0]:+.4f}, corr(g1,p1) {corr1:+.4f}, corr(g2,p2) {corr2:+.4f} "
                  f"(expected 0 +- {1 / max(n, 1) ** 0.5:.1e})", flush=True)
            # 5. massless-rebuild diagnostic per clustering hypothesis
            s = "   SELF-CHECK massless (p1,p2,alpha) rebuild of m_jj vs stored, rel diff mean [min, max]:"
            for idx in range(4):
                ni = checks[f"idx{idx}_n"].GetValue()
                if ni:
                    s += (f" idx{idx} (n={ni}) {checks[f'idx{idx}_mml_mean'].GetValue():+.2e} "
                          f"[{checks[f'idx{idx}_mml_min'].GetValue():+.2e}, {checks[f'idx{idx}_mml_max'].GetValue():+.2e}];")
            print(s + " (idx 0 = inclusive kt, massive jets: the reason for the jet-mass-aware JER rebuild)", flush=True)
            # 6. edge migrations
            n_nom = counts[("nomva", "")].GetValue()
            s = f"   SELF-CHECK migrations vs the nominal nomva selection ({n_nom} events):"
            for tag in TAGS:
                lm, lr, gr = (checks[f"lost_mp_{tag}"].GetValue(), checks[f"lost_r_{tag}"].GetValue(), checks[f"gain_r_{tag}"].GetValue())
                s += (f" {tag}: lost at the m/p window edges {lm} ({100 * lm / max(n_nom, 1):.3f}%, one-sided, stage1 cut), "
                      f"recoil out {lr} / in {gr};")
            print(s, flush=True)
        n_done += 1

    print(f"== done: {n_done} processes in {time.time() - t_all:.0f}s -> {out_dir}"
          + (f"; compare-dir: {compared[0]} histograms compared, {compared[1]} differ" if args.compare_dir else ""), flush=True)
    if args.compare_dir and compared[1]:
        print("== COMPARE-DIR: differences found (see COMPARE lines)", flush=True)
        sys.exit(1)
    if need_nominal:
        if failures:
            print(f"== SELF-CHECK FAILED for {failures}: the stage2 normalization/selection replication is wrong", flush=True)
            sys.exit(1)
        if n_ref == 0:
            print(f"== SELF-CHECK: WARNING - no stage2 reference file found in {ref_dir}, the nominal replication was "
                  "NOT compared (give --ref-dir)", flush=True)
        else:
            print(f"== SELF-CHECK PASSED ({n_ref} process x category nominal replications within {SELF_CHECK_TOL:g}; "
                  "the other lines are diagnostics)", flush=True)


if __name__ == "__main__":
    main()
