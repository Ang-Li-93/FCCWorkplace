#python examples/FCCee/higgs/mH-recoil/mumu/finalSel.py
#Input directory where the files produced at the pre-selection level are
inputDir = "/eos/user/l/lia/FCCee/MidTerm/mumu/MVAInputs"

#Input directory where the files produced at the pre-selection level are
outputDir = "/eos/user/l/lia/FCCee/MidTerm/mumu/MVAInputs/final_test"

###Link to the dictonary that contains all the cross section informations etc...
procDict = "FCCee_procDict_winter2023_training_IDEA.json"
#Add MySample_p8_ee_ZH_ecm240 as it is not an offical process
procDictAdd={"myp8_ee_WW_mumu_ecm240": {"numberOfEvents": 5000000, "sumOfWeights": 5000000.0, "crossSection": 0.25792, "kfactor": 1.0, "matchingEfficiency": 1.0},
             
             }
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
                #background: 
                "p8_ee_WW_mumu_ecm240",
                "p8_ee_ZZ_ecm240",
                "wzp6_ee_mumu_ecm240",
                #rare backgrounds:
                "wzp6_egamma_eZ_Zmumu_ecm240",
                "wzp6_gammae_eZ_Zmumu_ecm240",
                "wzp6_gaga_mumu_60_ecm240",
              }
###Add MySample_p8_ee_ZH_ecm240 as it is not an offical process

#Number of CPUs to use
nCPUS = 2
#produces ROOT TTrees, default is False
doTree = False

###Dictionnay of the list of cuts. The key is the name of the selection that will be added to the output file
cutList = { 
            ####baseline without costhetamiss 
            "sel_Baseline_no_costhetamiss":"zll_m  > 86 && zll_m  < 96  && zll_recoil_m > 120 &&zll_recoil_m  <140 && zll_p  > 20 && zll_p  <70",
            }


###Dictionary for the ouput variable/hitograms. The key is the name of the variable in the output files. "name" is the name of the variable in the input file, "title" is the x-axis label of the histogram, "bin" the number of bins of the histogram, "xmin" the minimum x-axis value and "xmax" the maximum x-axis value.
histoList = {
    #plot fundamental varibales:
    "leading_zll_lepton_p":{"name":"leading_zll_lepton_p","title":"p_{l,leading} [GeV]","bin":100,"xmin":45,"xmax":85},
    "leading_zll_lepton_theta":{"name":"leading_zll_lepton_theta","title":"#theta_{l,leading}","bin":100,"xmin":0,"xmax":3.2},
    "subleading_zll_lepton_p":{"name":"subleading_zll_lepton_p","title":"p_{l,subleading}  [GeV]","bin":100,"xmin":20,"xmax":60},
    "subleading_zll_lepton_theta":{"name":"subleading_zll_lepton_theta","title":"#theta_{l,subleading}","bin":100,"xmin":0,"xmax":3.2},
    #Zed
    "zll_m":{"name":"zll_m","title":"m_{l^{+}l^{-}} [GeV]","bin":100,"xmin":86,"xmax":96},
    "zll_p":{"name":"zll_p","title":"p_{l^{+}l^{-}} [GeV]","bin":100,"xmin":20,"xmax":70},
    "zll_theta":{"name":"zll_theta","title":"#theta_{l^{+}l^{-}}","bin":100,"xmin":0,"xmax":3.2},
    #more control variables
    "zll_leptons_acolinearity":{"name":"zll_leptons_acolinearity","title":"#Delta#theta_{l^{+}l^{-}}","bin":100,"xmin":0,"xmax":3.2},
    "zll_leptons_acoplanarity":{"name":"zll_leptons_acoplanarity","title":"#Delta#phi_{l^{+}l^{-}}","bin":100,"xmin":0,"xmax":3.2},
    #Recoil
    "zll_recoil_m":{"name":"zll_recoil_m","title":"m_{recoil} [GeV]","bin":100,"xmin":120,"xmax":140},
    #missing Information
    "cosTheta_miss":{"name":"cosTheta_miss","title":"cos#theta_{missing}","bin":100,"xmin":-1,"xmax":1},
    #Higgsstrahlungness
    "H":{"name":"H","title":"Higgsstrahlungness","bin":110,"xmin":0,"xmax":110} 

}



