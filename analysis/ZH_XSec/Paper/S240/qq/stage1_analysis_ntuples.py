#Mandatory: List of processes
# ZH hadronic analysis samples, adapted from FCCPhysics h_zh_hadronic.py to winter2023:
#   - signals: all 8 Z decay sets x 11 H decays (Hinv also exists as wzp6 in winter2023)
#   - wzp6_ee_qq replaces the wz3p6_ee_uu/dd/ss/cc/bb samples (absent in winter2023)
#   - wz3p6_ee_nunu dropped: no winter2023 equivalent (fully invisible final state anyway)
ecm = 240
z_decays = ["qq", "ss", "cc", "bb", "ee", "mumu", "tautau", "nunu"]
h_decays = ["Hbb", "Hcc", "Hss", "Hgg", "Haa", "HZa", "HWW", "HZZ", "Hmumu", "Htautau", "Hinv"]

processList = {}
for z in z_decays:
    for h in h_decays:
        processList[f"wzp6_ee_{z}H_{h}_ecm{ecm}"] = {'chunks': 10}

# Inclusive-H ZH samples and their beam-energy-spread variants, for the BES nuisance of
# the hadronic channel (arXiv:2512.21290 Sec 5.3). The winter2023 catalog has
# wzp6_ee_{z}H_ecm{ecm} (all H decays with SM BRs) and
# wzp6_ee_{z}H_BES-{higher,lower}-1pc_ecm{ecm} for EVERY Z decay at 240 and 365: the
# hadronic-Z, tautau and nunu BES sets were produced on 2026-09-07, i.e. after the
# July-2026 campaign (whose note that none existed was correct at the time); verified
# with xrdfs, 2026-09-29. The nominal inclusive sample is taken along so the
# BES template shift can be formed between statistically consistent inclusive samples,
# signal_BESUp = signal + (incl_BESup - incl_nominal), as makeWS_recoil_2cat.py does
# for the leptonic channels; the exclusive Z x H sets above stay the nominal templates.
# These names trigger none of the process-name-driven MC-truth filters in
# zqq_stage1_common.py (no 'HZZ' substring, not 'p8_ee_WW_ecm'), which is correct:
# they are inclusive in H decays, so H->ZZ->invisible is in the mix exactly once and
# must not be removed.
# NB: keep this loop BEFORE the first import (condor/submit_stage1.py executes the
# config section statement by statement up to the first import).
for z in z_decays:
    for _tag in ("", "_BES-higher-1pc", "_BES-lower-1pc"):
        processList[f"wzp6_ee_{z}H{_tag}_ecm{ecm}"] = {'chunks': 10}

processList.update({
    f"p8_ee_WW_ecm{ecm}":               {'chunks': 80},
    f"p8_ee_WW_mumu_ecm{ecm}":          {'chunks': 20},
    f"p8_ee_WW_ee_ecm{ecm}":            {'chunks': 20},
    f"p8_ee_ZZ_ecm{ecm}":               {'chunks': 20},
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

# TMVAHelperXGB reads the thread-pool size at construction: enable MT first.
# Not when the runner limits the events (--nevents -> RDataFrame::Range, which is
# single-thread only): it then stays single-threaded and the helper uses one slot.
if "--nevents" not in sys.argv:
    ROOT.EnableImplicitMT(nCPUS)
from addons.TMVAHelper.TMVAHelper import TMVAHelperXGB
tmva_helper = TMVAHelperXGB(bdt_model(240, "qq"), "bdt_model")

# process name from the condor wrapper, drives the MC-truth filters (HZZ->inv, WW->leptonic)
PROC = os.environ.get("FCCANA_PROCESS", "")
if not PROC:
    print("WARNING: FCCANA_PROCESS not set - the HZZ->invisible / WW->leptonic MC-truth\n"
          "         filters are DISABLED for this run. Export FCCANA_PROCESS=<process>\n"
          "         (as the condor wrapper does) when re-running chunks by hand.")

#Mandatory: RDFanalysis class
class RDFanalysis():

    def analysers(df):
        return zqq.build_graph_zqq(df, ecm=240, proc=PROC, tmva_helper=tmva_helper, syst=True)

    def output():
        return zqq.TREE_BRANCHES + zqq.ANALYSIS_EXTRA_BRANCHES + zqq.SYST_BRANCHES
