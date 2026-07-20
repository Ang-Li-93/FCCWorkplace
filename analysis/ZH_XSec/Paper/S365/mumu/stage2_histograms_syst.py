#python examples/FCCee/higgs/mH-recoil/mumu/finalSel.py
#Input directory where the files produced at the pre-selection level are
# site-aware paths: SDCC GPFS or original lxplus /eos (see Paper/site_config.py)
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from site_config import output_dir as _sdir
inputDir = _sdir(365, "mumu", "BDT_analysis_samples")

#Input directory where the files produced at the pre-selection level are
outputDir = _sdir(365, "mumu", "BDT_analysis_samples/syst")

###Link to the dictonary that contains all the cross section informations etc...
procDict = "FCCee_procDict_winter2023_IDEA.json"
#Add MySample_p8_ee_ZH_ecm240 as it is not an offical process
procDictAdd={"mywzp6_ee_mumuH_ecm240": {"numberOfEvents": 1000000, "sumOfWeights": 1000000.0, "crossSection": 0.0067643, "kfactor": 1.0, "matchingEfficiency": 1.0}}
#procDictAdd={"wzp6_ee_mumuH_ecm240": {"numberOfEvents": 1000000, "sumOfWeights": 1000000.0, "crossSection": 0.0067643, "kfactor": 1.0, "matchingEfficiency": 1.0},
#              "p8_ee_ZZ_ecm240": {"numberOfEvents": 59800000, "sumOfWeights": 59800000, "crossSection": 1.35899, "kfactor": 1.0, "matchingEfficiency": 1.0},
#              "p8_ee_WW_mumu_ecm240": {"numberOfEvents": 10000000, "sumOfWeights": 10000000, "crossSection": 0.25792, "kfactor": 1.0, "matchingEfficiency": 1.0},
#              "wzp6_ee_mumu_ecm240": {"numberOfEvents": 49400000, "sumOfWeights": 49400000.0, "crossSection": 5.288, "kfactor": 1.0, "matchingEfficiency": 1.0},
#              "wzp6_egamma_eZ_Zmumu_ecm240": {"numberOfEvents": 5000000, "sumOfWeights": 5000000.0, "crossSection": 0.10368, "kfactor": 1.0, "matchingEfficiency": 1.0},
#              "wzp6_gammae_eZ_Zmumu_ecm240": {"numberOfEvents": 5000000, "sumOfWeights": 5000000.0, "crossSection": 0.10368, "kfactor": 1.0, "matchingEfficiency": 1.0}
#             }
###Process list that should match the produced files.
processList = {
                #signal
                "wzp6_ee_mumuH_ecm365",
                ##signal mass
                #"wzp6_ee_mumuH_mH-higher-100MeV_ecm365",
                #"wzp6_ee_mumuH_mH-higher-50MeV_ecm365",
                #"wzp6_ee_mumuH_mH-lower-100MeV_ecm365",
                #"wzp6_ee_mumuH_mH-lower-50MeV_ecm365",
                #signal syst
                "wzp6_ee_mumuH_BES-higher-1pc_ecm365",
                "wzp6_ee_mumuH_BES-lower-1pc_ecm365",
                "wzp6_ee_mumuH_BES-higher-10pc_ecm365",
                "wzp6_ee_mumuH_BES-lower-10pc_ecm365", 
                #background: 
                "p8_ee_WW_ecm365",
                "p8_ee_ZZ_ecm365",
                "wzp6_ee_mumu_ecm365",
                "wzp6_ee_tautau_ecm365",
                #rare backgrounds:
                "wzp6_egamma_eZ_Zmumu_ecm365",
                "wzp6_gammae_eZ_Zmumu_ecm365",
                "wzp6_gaga_mumu_60_ecm365",
                "wzp6_gaga_tautau_60_ecm365",
                "wzp6_ee_nuenueZ_ecm365",
                "p8_ee_tt_ecm365",
              }
###Add MySample_p8_ee_ZH_ecm240 as it is not an offical process

#Number of CPUs to use
nCPUS = 8
#produces ROOT TTrees, default is False
doTree = False

###Dictionnay of the list of cuts. The key is the name of the selection that will be added to the output file
cutList = { "sel0":"return true;",
            "sel_Baseline":"zll_m > 86 && zll_m < 96 && zll_recoil_m > 120 &&zll_recoil_m <140 && zll_p > 20 && cosTheta_miss.size() >=1 && cosTheta_miss[0] > -0.98 && cosTheta_miss[0] < 0.98",
            # no-BDT baseline (referee scenario): wide recoil window 100-150, the
            # sidebands constrain the background normalization LEP-style
            "sel_Baseline_wide":"zll_m > 86 && zll_m < 96 && zll_recoil_m > 100 && zll_recoil_m < 150 && zll_p > 50 && zll_p < 150",
            "sel_Baseline_wide_scaleup":"zll_m_scaleup > 86 && zll_m_scaleup < 96 && zll_recoil_m_scaleup > 100 && zll_recoil_m_scaleup < 150 && zll_p_scaleup > 50 && zll_p_scaleup < 150",
            "sel_Baseline_wide_scaledw":"zll_m_scaledw > 86 && zll_m_scaledw < 96 && zll_recoil_m_scaledw > 100 && zll_recoil_m_scaledw < 150 && zll_p_scaledw > 50 && zll_p_scaledw < 150",
            "sel_Baseline_wide_sqrtsup":"zll_m > 86 && zll_m < 96 && zll_recoil_m_sqrtsup > 100 && zll_recoil_m_sqrtsup < 150 && zll_p > 50 && zll_p < 150",
            "sel_Baseline_wide_sqrtsdw":"zll_m > 86 && zll_m < 96 && zll_recoil_m_sqrtsdw > 100 && zll_recoil_m_sqrtsdw < 150 && zll_p > 50 && zll_p < 150",
            # paper (arXiv:2512.21290) BDT regions: recoil fitted in low/high score
            "sel_Baseline_loBDT":"zll_m > 86 && zll_m < 96 && zll_recoil_m > 100 && zll_recoil_m < 150 && zll_p > 20 && BDTscore < 0.66",
            "sel_Baseline_hiBDT":"zll_m > 86 && zll_m < 96 && zll_recoil_m > 100 && zll_recoil_m < 150 && zll_p > 20 && BDTscore >= 0.66",
            "sel_Baseline_no_costhetamiss":"zll_m  > 86 && zll_m  < 96  && zll_recoil_m > 120 &&zll_recoil_m  <140 && zll_p  > 20 ", 
            "sel_Baseline_no_costhetamiss_scaleup":"zll_m_scaleup  > 86 && zll_m_scaleup  < 96  && zll_recoil_m_scaleup > 120 &&zll_recoil_m_scaleup  <140 && zll_p_scaleup  > 20", 
            "sel_Baseline_no_costhetamiss_scaledw":"zll_m_scaledw  > 86 && zll_m_scaledw  < 96  && zll_recoil_m_scaledw > 120 &&zll_recoil_m_scaledw  <140 && zll_p_scaledw  > 20",
            "sel_Baseline_no_costhetamiss_besup":"zll_m  > 86 && zll_m  < 96  && zll_recoil_m > 120 &&zll_recoil_m  <140 && zll_p  > 20", 
            "sel_Baseline_no_costhetamiss_besdw":"zll_m  > 86 && zll_m  < 96  && zll_recoil_m > 120 &&zll_recoil_m  <140 && zll_p  > 20",
            "sel_Baseline_no_costhetamiss_sqrtsup":"zll_m  > 86 && zll_m  < 96  && zll_recoil_m_sqrtsup > 120 &&zll_recoil_m_sqrtsup  <140 && zll_p  > 20",
            "sel_Baseline_no_costhetamiss_sqrtsdw":"zll_m  > 86 && zll_m  < 96  && zll_recoil_m_sqrtsdw > 120 &&zll_recoil_m_sqrtsdw  <140 && zll_p  > 20",
            }


###Dictionary for the ouput variable/hitograms. The key is the name of the variable in the output files. "name" is the name of the variable in the input file, "title" is the x-axis label of the histogram, "bin" the number of bins of the histogram, "xmin" the minimum x-axis value and "xmax" the maximum x-axis value.
histoList = {
    "BDT_Score":{"name":"BDTscore","title":"BDT Score","bin":100,"xmin":0,"xmax":1},
    "recoil_m":{"name":"zll_recoil_m","title":"Recoil mass (GeV)","bin":100,"xmin":100,"xmax":150},
    "recoil_m_scaleup":{"name":"zll_recoil_m_scaleup","title":"Recoil mass scaleup (GeV)","bin":100,"xmin":100,"xmax":150},
    "recoil_m_scaledw":{"name":"zll_recoil_m_scaledw","title":"Recoil mass scaledw (GeV)","bin":100,"xmin":100,"xmax":150},
    "recoil_m_sqrtsup":{"name":"zll_recoil_m_sqrtsup","title":"Recoil mass sqrtsup (GeV)","bin":100,"xmin":100,"xmax":150},
    "recoil_m_sqrtsdw":{"name":"zll_recoil_m_sqrtsdw","title":"Recoil mass sqrtsdw (GeV)","bin":100,"xmin":100,"xmax":150},
    "zll_m_h":{"name":"zll_m","title":"m_{ll} (GeV)","bin":50,"xmin":86,"xmax":96},
    "zll_p_h":{"name":"zll_p","title":"p_{ll} (GeV)","bin":100,"xmin":0,"xmax":120},
    "leading_lep_p":{"name":"leading_zll_lepton_p","title":"p_{l1} (GeV)","bin":100,"xmin":20,"xmax":100},
    "leading_lep_theta":{"name":"leading_zll_lepton_theta","title":"#theta_{l1}","bin":64,"xmin":0,"xmax":3.2},
    "acolinearity_h":{"name":"zll_leptons_acolinearity","title":"|#Delta#theta_{ll}|","bin":64,"xmin":0,"xmax":3.2},
    "BDT_Score":{"name":"BDTscore","title":"BDT Score","bin":100,"xmin":0,"xmax":1}, 
    "BDT_Score_scaleup":{"name":"BDTscore_scaleup","title":"BDT Score LEPSCALE UP","bin":100,"xmin":0,"xmax":1}, 
    "BDT_Score_scaledw":{"name":"BDTscore_scaledw","title":"BDT Score LEPSCALE DOWN","bin":100,"xmin":0,"xmax":1}, 
}



