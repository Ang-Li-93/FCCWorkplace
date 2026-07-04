#Mandatory: List of processes
# BDT training samples (reference: FCCPhysics zh_hadronic_training/train.py):
# signal = Z(qq/bb/cc/ss)H with all H decays except Hinv, background = WW + Z/gamma*->qq.
# 'fraction' limits the input files (handled by condor/submit_stage1.py).
ecm = 240
z_decays = ["qq", "bb", "cc", "ss"]
h_decays = ["Hbb", "Hcc", "Hss", "Hgg", "Hmumu", "Htautau", "HZZ", "HWW", "HZa", "Haa"]

processList = {}
for z in z_decays:
    for h in h_decays:
        processList[f"wzp6_ee_{z}H_{h}_ecm{ecm}"] = {'chunks': 10, 'fraction': 0.5}
# backgrounds (wzp6_ee_qq replaces the wz3p6_ee_uu/dd/ss/cc/bb samples, absent in winter2023)
processList[f"p8_ee_WW_ecm{ecm}"]  = {'chunks': 40, 'fraction': 0.1}
processList[f"wzp6_ee_qq_ecm{ecm}"] = {'chunks': 40, 'fraction': 0.1}

#Mandatory: Production tag when running over EDM4Hep centrally produced events
prodTag     = "FCCee/winter2023/IDEA/"

outputDir   = "MVA_ntuples"
#Optional: ncpus, default is 4
nCPUS       = 4

#Optional running on HTCondor, default is False (custom SDCC submitter is used instead)
runBatch    = False

#USER DEFINED CODE
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import zqq_stage1_common as zqq

#Mandatory: RDFanalysis class
class RDFanalysis():

    def analysers(df):
        # training stage: no MC-truth process filters, no BDT (matches the reference treemaker)
        return zqq.build_graph_zqq(df, ecm=240, proc="", tmva_helper=None, syst=False)

    def output():
        return zqq.TREE_BRANCHES
