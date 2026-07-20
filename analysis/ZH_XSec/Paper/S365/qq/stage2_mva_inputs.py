# Stage2 over the qq TRAINING trees (winter2023_training campaign, ecm 365):
# histograms of the BDT input variables from MVA_ntuples/, for input validation
# and the stage3_mva_inputs_plots.py plots. Mirrors the leptonic stage2_mva_inputs.py.
#
# Run: fccanalysis final analysis/ZH_XSec/Paper/S365/qq/stage2_mva_inputs.py
import glob
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from site_config import output_dir as _sdir

ecm = 365

inputDir = _sdir(ecm, "qq", "MVA_ntuples")
outputDir = _sdir(ecm, "qq", "MVAInputs_final")

###Link to the dictonary that contains all the cross section informations etc...
procDict = "FCCee_procDict_winter2023_training_IDEA.json"

###Process list: the training samples, restricted to those with treemaker output.
z_decays = ["qq", "bb", "cc", "ss"]
h_decays = ["Hbb", "Hcc", "Hss", "Hgg", "Hmumu", "Htautau", "HZZ", "HWW", "HZa", "Haa"]

_all_procs = [f"wzp6_ee_{z}H_{h}_ecm{ecm}" for z in z_decays for h in h_decays] + [
    f"p8_ee_WW_ecm{ecm}",
    f"wzp6_ee_qq_ecm{ecm}",
]

processList = {p for p in _all_procs if glob.glob(f"{inputDir}/{p}/chunk*.root") or
               os.path.isfile(f"{inputDir}/{p}.root")}
_missing = [p for p in _all_procs if p not in processList]
if _missing:
    print(f"WARNING: no treemaker output for {len(_missing)} processes, skipped: {_missing}")

#Number of CPUs to use
nCPUS = 8
#produces ROOT TTrees, default is False
doTree = False

###The training trees already carry the full hadronic preselection
cutList = {"sel0": "return true;"}

###Histogram per BDT input variable (histogram key == branch name, as the leptonic
###channels do, so stage3_mva_inputs_plots.py can list the same names)
histoList = {
    "zqq_p_best":            {"name": "zqq_p_best",            "title": "p_{qq} (GeV)",            "bin": 140, "xmin": 20,  "xmax": 160},
    "zqq_m_best":            {"name": "zqq_m_best",            "title": "m_{qq} (GeV)",            "bin": 140, "xmin": 60,  "xmax": 200},
    "zqq_recoil_m_best":     {"name": "zqq_recoil_m_best",     "title": "Recoil mass (GeV)",       "bin": 160, "xmin": 100, "xmax": 180},
    "leading_jet_p":         {"name": "leading_jet_p",         "title": "p_{j_{1}} (GeV)",         "bin": 100, "xmin": 0,   "xmax": 200},
    "subleading_jet_p":      {"name": "subleading_jet_p",      "title": "p_{j_{2}} (GeV)",         "bin": 100, "xmin": 0,   "xmax": 160},
    "leading_jet_costheta":  {"name": "leading_jet_costheta",  "title": "|cos#theta_{j_{1}}|",     "bin": 50,  "xmin": 0,   "xmax": 1},
    "subleading_jet_costheta": {"name": "subleading_jet_costheta", "title": "|cos#theta_{j_{2}}|", "bin": 50,  "xmin": 0,   "xmax": 1},
    "z_costheta":            {"name": "z_costheta",            "title": "|cos#theta_{qq}|",        "bin": 50,  "xmin": 0,   "xmax": 1},
    "acolinearity":          {"name": "acolinearity",          "title": "|#Delta#theta_{jj}|",     "bin": 64,  "xmin": 0,   "xmax": 3.2},
    "acoplanarity":          {"name": "acoplanarity",          "title": "|#Delta#phi_{jj}|",       "bin": 64,  "xmin": 0,   "xmax": 3.2},
    "W1_p":                  {"name": "W1_p",                  "title": "p_{W_{1}} (GeV)",         "bin": 100, "xmin": 0,   "xmax": 180},
    "W2_p":                  {"name": "W2_p",                  "title": "p_{W_{2}} (GeV)",         "bin": 100, "xmin": 0,   "xmax": 180},
    "W1_m":                  {"name": "W1_m",                  "title": "m_{W_{1}} (GeV)",         "bin": 125, "xmin": 0,   "xmax": 250},
    "W2_m":                  {"name": "W2_m",                  "title": "m_{W_{2}} (GeV)",         "bin": 125, "xmin": 0,   "xmax": 250},
    "W1_costheta":           {"name": "W1_costheta",           "title": "|cos#theta_{W_{1}}|",     "bin": 50,  "xmin": 0,   "xmax": 1},
    "W2_costheta":           {"name": "W2_costheta",           "title": "|cos#theta_{W_{2}}|",     "bin": 50,  "xmin": 0,   "xmax": 1},
    "thrust_magn":           {"name": "thrust_magn",           "title": "Thrust",                  "bin": 50,  "xmin": 0.5, "xmax": 1},
}
