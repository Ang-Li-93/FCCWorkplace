#python examples/FCCee/higgs/mH-recoil/mumu/finalSel.py
#Input directory where the files produced at the pre-selection level are
inputDir = "/eos/user/l/lia/FCCee/MidTerm/mumu/BDT_analysis_samples"

#Input directory where the files produced at the pre-selection level are
outputDir = "/eos/user/l/lia/FCCee/MidTerm/mumu/BDT_analysis_samples/syst_test"

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
                "wzp6_ee_mumuH_ecm240",
                ##signal mass
                #"wzp6_ee_mumuH_mH-higher-100MeV_ecm240",
                #"wzp6_ee_mumuH_mH-higher-50MeV_ecm240",
                #"wzp6_ee_mumuH_mH-lower-100MeV_ecm240",
                #"wzp6_ee_mumuH_mH-lower-50MeV_ecm240",
                #signal syst
                "wzp6_ee_mumuH_BES-higher-1pc_ecm240",
                "wzp6_ee_mumuH_BES-lower-1pc_ecm240",
                #background: 
                "p8_ee_WW_ecm240",
                "p8_ee_ZZ_ecm240",
                "wzp6_ee_mumu_ecm240",
                "wzp6_ee_tautau_ecm240",
                #rare backgrounds:
                "wzp6_egamma_eZ_Zmumu_ecm240",
                "wzp6_gammae_eZ_Zmumu_ecm240",
                "wzp6_gaga_mumu_60_ecm240",
                "wzp6_gaga_tautau_60_ecm240",
                "wzp6_ee_nuenueZ_ecm240"
              }
###Add MySample_p8_ee_ZH_ecm240 as it is not an offical process

#Number of CPUs to use
nCPUS = 2
#produces ROOT TTrees, default is False
doTree = False

###Dictionnay of the list of cuts. The key is the name of the selection that will be added to the output file
cutList = { "sel0":"return true;",
            "sel_Baseline":"zll_m > 86 && zll_m < 96 && zll_recoil_m > 120 &&zll_recoil_m <140 && zll_p > 20 && zll_p <70 && cosTheta_miss.size() >=1 && cosTheta_miss[0] > -0.98 && cosTheta_miss[0] < 0.98",
            "sel_Baseline_no_costhetamiss":"zll_m  > 86 && zll_m  < 96  && zll_recoil_m > 120 &&zll_recoil_m  <140 && zll_p  > 20 && zll_p  <70", 
            "sel_Baseline_no_costhetamiss_scaleup":"zll_m_scaleup  > 86 && zll_m_scaleup  < 96  && zll_recoil_m_scaleup > 120 &&zll_recoil_m_scaleup  <140 && zll_p_scaleup  > 20 && zll_p_scaleup  <70", 
            "sel_Baseline_no_costhetamiss_scaledw":"zll_m_scaledw  > 86 && zll_m_scaledw  < 96  && zll_recoil_m_scaledw > 120 &&zll_recoil_m_scaledw  <140 && zll_p_scaledw  > 20 && zll_p_scaledw  <70",
            "sel_Baseline_no_costhetamiss_besup":"zll_m  > 86 && zll_m  < 96  && zll_recoil_m > 120 &&zll_recoil_m  <140 && zll_p  > 20 && zll_p  <70", 
            "sel_Baseline_no_costhetamiss_besdw":"zll_m  > 86 && zll_m  < 96  && zll_recoil_m > 120 &&zll_recoil_m  <140 && zll_p  > 20 && zll_p  <70",
            "sel_Baseline_no_costhetamiss_sqrtsup":"zll_m  > 86 && zll_m  < 96  && zll_recoil_m_sqrtsup > 120 &&zll_recoil_m_sqrtsup  <140 && zll_p  > 20 && zll_p  <70",
            "sel_Baseline_no_costhetamiss_sqrtsdw":"zll_m  > 86 && zll_m  < 96  && zll_recoil_m_sqrtsdw > 120 &&zll_recoil_m_sqrtsdw  <140 && zll_p  > 20 && zll_p  <70",
            }


###Dictionary for the ouput variable/hitograms. The key is the name of the variable in the output files. "name" is the name of the variable in the input file, "title" is the x-axis label of the histogram, "bin" the number of bins of the histogram, "xmin" the minimum x-axis value and "xmax" the maximum x-axis value.
histoList = {
    "BDT_Score":{"name":"BDTscore","title":"BDT Score","bin":100,"xmin":0,"xmax":1},
    "BDT_Score":{"name":"BDTscore","title":"BDT Score","bin":100,"xmin":0,"xmax":1}, 
    "BDT_Score_scaleup":{"name":"BDTscore_scaleup","title":"BDT Score LEPSCALE UP","bin":100,"xmin":0,"xmax":1}, 
    "BDT_Score_scaledw":{"name":"BDTscore_scaledw","title":"BDT Score LEPSCALE DOWN","bin":100,"xmin":0,"xmax":1}, 
}



