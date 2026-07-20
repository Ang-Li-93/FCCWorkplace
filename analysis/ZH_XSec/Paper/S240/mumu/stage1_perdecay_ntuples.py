# Per-H-decay Z(mumu)H stage1 (ecm 240): the SAME muon-channel selection/graph as
# stage1_analysis_ntuples.py, run over the individual wzp6_ee_mumuH_<Hdecay> samples.
# Used for the paper's per-decay selection-efficiency figures (arXiv:2512.21290
# Figs. 5/10), the per-decay BDT shapes (Fig. 6) and the leptonic bias test.
#
# Submit: python condor/submit_stage1.py S240/mumu/stage1_perdecay_ntuples.py --stage perdecay_ntuples
ecm = 240
h_decays = ["Hbb", "Hcc", "Hss", "Hgg", "Haa", "HZa", "HWW", "HZZ", "Hmumu", "Htautau", "Hinv"]

processList = {}
for h in h_decays:
    processList[f"wzp6_ee_mumuH_{h}_ecm{ecm}"] = {'chunks': 10}

#Mandatory: Production tag when running over EDM4Hep centrally produced events
prodTag     = "FCCee/winter2023/IDEA/"

outputDir   = "perdecay_ntuples"
#Optional: ncpus, default is 4
nCPUS       = 4

#Optional running on HTCondor, default is False (custom SDCC submitter is used instead)
runBatch    = False

#USER DEFINED CODE: reuse the full muon-channel analysis graph
import os, sys, importlib.util
_here = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("mumu_stage1", os.path.join(_here, "stage1_analysis_ntuples.py"))
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

RDFanalysis = _mod.RDFanalysis
