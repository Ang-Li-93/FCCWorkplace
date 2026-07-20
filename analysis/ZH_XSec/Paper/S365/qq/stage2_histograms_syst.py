# Stage2 for the ZH hadronic (Z->qq) channel, ecm 365: BDT-score (and control)
# histograms for all selections incl. systematic variations, from the stage1
# analysis ntuples (stage1_analysis_ntuples.py -> BDT_analysis_samples/).
#
# Mirrors the leptonic stage2_histograms_syst.py:
#   - the baseline selection is re-applied per variation with the shifted branches
#     (jet-scale: zqq_*_scaleup/scaledw; sqrt(s): zqq_recoil_m_sqrtsup/sqrtsdw),
#   - the BDT score itself is not recomputed under the jet-scale shift (unlike the
#     leptonic LEPSCALE): the +-1e-5 scale enters through the selection migration,
#   - no BES / mH-shifted samples exist in winter2023 for hadronic Z decays,
#   - p8_ee_tt added at 365 (as in stage1_analysis_ntuples.py).
#
# Run: fccanalysis final analysis/ZH_XSec/Paper/S365/qq/stage2_histograms_syst.py
import glob
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from site_config import output_dir as _sdir

ecm = 365

inputDir = _sdir(ecm, "qq", "BDT_analysis_samples")
outputDir = _sdir(ecm, "qq", "BDT_analysis_samples/syst")

###Link to the dictonary that contains all the cross section informations etc...
procDict = "FCCee_procDict_winter2023_IDEA.json"

###Process list: same samples as stage1_analysis_ntuples.py, restricted to those
###that actually produced stage1 output (guards against an incomplete stage1 production;
###the winter2023 catalog itself has every Z x H combination).
z_decays = ["qq", "ss", "cc", "bb", "ee", "mumu", "tautau", "nunu"]
h_decays = ["Hbb", "Hcc", "Hss", "Hgg", "Haa", "HZa", "HWW", "HZZ", "Hmumu", "Htautau", "Hinv"]

# nunuH_Hinv is fully invisible: zero hadronic acceptance, empty stage1 outputs
_all_procs = [f"wzp6_ee_{z}H_{h}_ecm{ecm}" for z in z_decays for h in h_decays
              if not (z == "nunu" and h == "Hinv")] + [
    f"p8_ee_WW_ecm{ecm}",
    f"p8_ee_WW_mumu_ecm{ecm}",
    f"p8_ee_WW_ee_ecm{ecm}",
    f"p8_ee_ZZ_ecm{ecm}",
    f"p8_ee_tt_ecm{ecm}",
    f"wzp6_ee_qq_ecm{ecm}",
    f"wzp6_ee_tautau_ecm{ecm}",
    f"wzp6_ee_mumu_ecm{ecm}",
    f"wzp6_ee_ee_Mee_30_150_ecm{ecm}",
    f"wzp6_egamma_eZ_Zmumu_ecm{ecm}",
    f"wzp6_gammae_eZ_Zmumu_ecm{ecm}",
    f"wzp6_gaga_mumu_60_ecm{ecm}",
    f"wzp6_egamma_eZ_Zee_ecm{ecm}",
    f"wzp6_gammae_eZ_Zee_ecm{ecm}",
    f"wzp6_gaga_ee_60_ecm{ecm}",
    f"wzp6_gaga_tautau_60_ecm{ecm}",
    f"wzp6_ee_nuenueZ_ecm{ecm}",
]

processList = {p for p in _all_procs if glob.glob(f"{inputDir}/{p}/chunk*.root") or
               os.path.isfile(f"{inputDir}/{p}.root")}
_missing = [p for p in _all_procs if p not in processList]
if _missing:
    print(f"WARNING: no stage1 output for {len(_missing)} processes, skipped: {_missing}")

#Number of CPUs to use
nCPUS = 8
#produces ROOT TTrees, default is False
doTree = False

# BDT category boundary (arXiv:2512.21290: 0.75 at 240 GeV, 0.95 at 365 GeV).
# The 2D fit runs simultaneously in the low- and high-score regions: the low region
# constrains the background normalizations, the high region carries the sensitivity.
# The nominal score is used in every variation (not recomputed under jet-scale).
MVA_WP = 0.95

# baseline windows. NB stage1 already hard-cuts the NOMINAL zqq_m/zqq_p at these
# values, so the scaled selections can only lose events at the m/p window edges,
# never gain them (one-sided migration; O(1e-5 x edge bin) - negligible). Only the
# recoil window, not cut at stage1, migrates two-sided.
_windows = {
    "":        ("zqq_m_best",    "zqq_p_best",    "zqq_recoil_m_best"),
    "scaleup": ("zqq_m_scaleup", "zqq_p_scaleup", "zqq_recoil_m_scaleup"),
    "scaledw": ("zqq_m_scaledw", "zqq_p_scaledw", "zqq_recoil_m_scaledw"),
    "sqrtsup": ("zqq_m_best",    "zqq_p_best",    "zqq_recoil_m_sqrtsup"),
    "sqrtsdw": ("zqq_m_best",    "zqq_p_best",    "zqq_recoil_m_sqrtsdw"),
}

def _sel(m, p, r, mva=None):
    # 365 windows per arXiv:2512.21290: 60 < m_jj < 200, 20 < p_jj < 160
    s = (f"{m} > 60 && {m} < 200 && {p} > 20 && {p} < 160 && "
         f"{r} > 100 && {r} < 180")
    if mva == "hi":
        s += f" && mva_score[0] >= {MVA_WP}"
    elif mva == "lo":
        s += f" && mva_score[0] < {MVA_WP}"
    return s

cutList = {"sel0": "return true;"}
for _tag, (_m, _p, _r) in _windows.items():
    _suffix = f"_{_tag}" if _tag else ""
    cutList["sel_Baseline_hiBDT" + _suffix] = _sel(_m, _p, _r, "hi")
    cutList["sel_Baseline_loBDT" + _suffix] = _sel(_m, _p, _r, "lo")
    # without the BDT split: full-range score fit (makeWS_BDT_binned qq cross-check),
    # score control plots, and WP optimisation
    cutList["sel_Baseline_nomva" + _suffix] = _sel(_m, _p, _r)

# 2D fit observable m_recoil x m_jj: one histogram per branch pairing; makeWS_2D_qq.py
# pairs each with its selection (nominal <-> sel_Baseline, scaleup <-> _scaleup, ...)
_bins2d = [(20, 100, 180), (14, 60, 200)]   # (recoil), (m_jj)
_h2 = {
    "mrecoil_mjj":         ("zqq_recoil_m_best",    "zqq_m_best"),
    "mrecoil_mjj_scaleup": ("zqq_recoil_m_scaleup", "zqq_m_scaleup"),
    "mrecoil_mjj_scaledw": ("zqq_recoil_m_scaledw", "zqq_m_scaledw"),
    "mrecoil_mjj_sqrtsup": ("zqq_recoil_m_sqrtsup", "zqq_m_best"),
    "mrecoil_mjj_sqrtsdw": ("zqq_recoil_m_sqrtsdw", "zqq_m_best"),
}

###Dictionary for the output variables/histograms
histoList = {
    "BDT_Score":    {"name": "mva_score",         "title": "BDT Score",         "bin": 100, "xmin": 0,   "xmax": 1},
    "recoil_m":     {"name": "zqq_recoil_m_best", "title": "Recoil mass (GeV)", "bin": 160, "xmin": 100, "xmax": 180},
    "zqq_m":        {"name": "zqq_m_best",        "title": "m_{qq} (GeV)",      "bin": 140, "xmin": 60,  "xmax": 200},
    "zqq_p":        {"name": "zqq_p_best",        "title": "p_{qq} (GeV)",      "bin": 140, "xmin": 20,  "xmax": 160},
    "cosThetaMiss": {"name": "cosThetaMiss",      "title": "|cos#theta_{miss}|", "bin": 100, "xmin": 0,  "xmax": 1},
}
for _hname, _cols in _h2.items():
    histoList[_hname] = {"cols": list(_cols), "bins": _bins2d}
