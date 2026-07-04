#Mandatory: List of processes
# ZH hadronic analysis samples, adapted from FCCPhysics h_zh_hadronic.py to winter2023:
#   - signals: all 8 Z decay sets x 11 H decays (Hinv also exists as wzp6 in winter2023)
#   - wzp6_ee_qq replaces the wz3p6_ee_uu/dd/ss/cc/bb samples (absent in winter2023)
#   - wz3p6_ee_nunu dropped: no winter2023 equivalent (fully invisible final state anyway)
#   - p8_ee_tt added at 365 (not in the reference list; the thrust cut targets it)
ecm = 365
z_decays = ["qq", "ss", "cc", "bb", "ee", "mumu", "tautau", "nunu"]
h_decays = ["Hbb", "Hcc", "Hss", "Hgg", "Haa", "HZa", "HWW", "HZZ", "Hmumu", "Htautau", "Hinv"]

processList = {}
for z in z_decays:
    for h in h_decays:
        processList[f"wzp6_ee_{z}H_{h}_ecm{ecm}"] = {'chunks': 10}

processList.update({
    f"p8_ee_WW_ecm{ecm}":               {'chunks': 80},
    f"p8_ee_WW_mumu_ecm{ecm}":          {'chunks': 20},
    f"p8_ee_WW_ee_ecm{ecm}":            {'chunks': 20},
    f"p8_ee_ZZ_ecm{ecm}":               {'chunks': 20},
    f"p8_ee_tt_ecm{ecm}":               {'chunks': 20},
    f"wzp6_ee_qq_ecm{ecm}":             {'chunks': 40},
    f"wzp6_ee_tautau_ecm{ecm}":         {'chunks': 20},
    f"wzp6_ee_mumu_ecm{ecm}":           {'chunks': 20},
    f"wzp6_ee_ee_Mee_30_150_ecm{ecm}":  {'chunks': 20},
    f"wzp6_egamma_eZ_Zmumu_ecm{ecm}":   {'chunks': 20},
    f"wzp6_gammae_eZ_Zmumu_ecm{ecm}":   {'chunks': 20},
    f"wzp6_gaga_mumu_60_ecm{ecm}":      {'chunks': 20},
    f"wzp6_egamma_eZ_Zee_ecm{ecm}":     {'chunks': 20},
    f"wzp6_gammae_eZ_Zee_ecm{ecm}":     {'chunks': 20},
    f"wzp6_gaga_ee_60_ecm{ecm}":        {'chunks': 20},
    f"wzp6_gaga_tautau_60_ecm{ecm}":    {'chunks': 20},
    f"wzp6_ee_nuenueZ_ecm{ecm}":        {'chunks': 20},
})

#Mandatory: Production tag when running over EDM4Hep centrally produced events
prodTag     = "FCCee/winter2023/IDEA/"

outputDir   = "BDT_analysis_samples"
#Optional: ncpus, default is 4
nCPUS       = 4

#Optional running on HTCondor, default is False (custom SDCC submitter is used instead)
runBatch    = False

#USER DEFINED CODE
import ROOT, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import zqq_stage1_common as zqq
from site_config import bdt_model

# TMVAHelperXGB reads the thread-pool size at construction: enable MT first
ROOT.EnableImplicitMT(nCPUS)
from addons.TMVAHelper.TMVAHelper import TMVAHelperXGB
tmva_helper = TMVAHelperXGB(bdt_model(365, "qq"), "bdt_model")

# process name from the condor wrapper, drives the MC-truth filters (HZZ->inv, WW->leptonic)
PROC = os.environ.get("FCCANA_PROCESS", "")

#Mandatory: RDFanalysis class
class RDFanalysis():

    def analysers(df):
        return zqq.build_graph_zqq(df, ecm=365, proc=PROC, tmva_helper=tmva_helper, syst=True)

    def output():
        return zqq.TREE_BRANCHES + zqq.ANALYSIS_EXTRA_BRANCHES + zqq.SYST_BRANCHES
