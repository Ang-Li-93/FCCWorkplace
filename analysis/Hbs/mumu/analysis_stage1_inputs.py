import numpy as np

#python examples/FCCee/higgs/mH-recoil/mumu/finalSel.py
#Input directory where the files produced at the pre-selection level are
# inputDir = "/afs/cern.ch/user/d/dduan/private/FCCWorkplace/analysis/Hbs/mumu/ROOT_Files"
inputDir = "/eos/user/d/dduan/FCCee/Hbs/mumu/initial_batch1"

#Output directory for the plotting script
outputDir = "/eos/user/d/dduan/FCCee/Hbs/mumu/Histo_Files"

###Link to the dictonary that contains all the cross section informations etc...
procDict = "FCCee_procDict_winter2023_IDEA.json"
#Add MySample_p8_ee_ZH_ecm240 as it is not an offical process
#procDictAdd={"myp8_ee_WW_mumu_ecm240": {"numberOfEvents": 5000000, "sumOfWeights": 5000000.0, "crossSection": 0.25792, "kfactor": 1.0, "matchingEfficiency": 1.0}}
procDictAdd = {
    "wzp6_ee_mumuH_ecm240": {"numberOfEvents": 1200000, "sumOfWeights": 1200000, "crossSection": 0.0067643, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "p8_ee_ZZ_ecm240": {"numberOfEvents": 56162093, "sumOfWeights": 56162093, "crossSection": 1.35899, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "p8_ee_WW_mumu_ecm240": {"numberOfEvents": 10000000, "sumOfWeights": 10000000, "crossSection": 0.25792, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_ee_mumu_ecm240": {"numberOfEvents": 53400000, "sumOfWeights": 53400000, "crossSection": 5.288, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_egamma_eZ_Zmumu_ecm240": {"numberOfEvents": 6000000, "sumOfWeights": 6000000, "crossSection": 0.10368, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_gammae_eZ_Zmumu_ecm240": {"numberOfEvents": 6000000, "sumOfWeights": 6000000, "crossSection": 0.10368, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_ee_mumuH_Hbb_ecm240": {"numberOfEvents": 300000, "sumOfWeights": 300000, "crossSection": 0.00394, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_ee_mumuH_Hss_ecm240": {"numberOfEvents": 400000, "sumOfWeights": 400000, "crossSection": 0.000001624, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_gaga_mumu_60_ecm240": {"numberOfEvents": 33900000, "sumOfWeights": 33900000, "crossSection": 1.5523, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_ee_mumuH_Hbs_W4p1MeV_ecm240": {"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 0.01, "kfactor": 1.0, "matchingEfficiency": 1.0},
}


###Process list that should match the produced files.
processList = {
                #background: 
                'wzp6_ee_mumuH_ecm240',
                #signal
                'wzp6_ee_mumuH_Hbs_W4p1MeV_ecm240',
                #Check
                'wzp6_ee_mumuH_Hbb_ecm240',
                'wzp6_ee_mumuH_Hss_ecm240',

                'p8_ee_WW_mumu_ecm240',
                'p8_ee_mumu_ecm240',
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

###Dictionary of the list of cuts. The key is the name of the selection that will be added to the output file
cutList = { 
            #Without Cuts
            "No_Cuts":"1",
            ####baseline without costhetamiss 
            "sel_Baseline_no_costhetamiss":"zll_m  > 86 && zll_m  < 96  && zll_recoil_m > 120 &&zll_recoil_m  <140 && zll_p  > 20 && zll_p  <70",
            }


###Dictionary for the ouput variable/hitograms. The key is the name of the variable in the output files. "name" is the name of the variable in the input file, "title" is the x-axis label of the histogram, "bin" the number of bins of the histogram, "xmin" the minimum x-axis value and "xmax" the maximum x-axis value.
histoList = {
    # plot fundamental variables:
    "leading_zll_lepton_p": {"name": "leading_zll_lepton_p", "title": "p_{l,leading} [GeV]", "bin": 100, "xmin": 45, "xmax": 85},
    "leading_zll_lepton_theta": {"name": "leading_zll_lepton_theta", "title": "#theta_{l,leading}", "bin": 100, "xmin": 0, "xmax": 3.2},
    "subleading_zll_lepton_p": {"name": "subleading_zll_lepton_p", "title": "p_{l,subleading}  [GeV]", "bin": 100, "xmin": 20, "xmax": 60},
    "subleading_zll_lepton_theta": {"name": "subleading_zll_lepton_theta", "title": "#theta_{l,subleading}", "bin": 100, "xmin": 0, "xmax": 3.2},
    
    # Zed
    "zll_m": {"name": "zll_m", "title": "m_{l^{+}l^{-}} [GeV]", "bin": 20, "xmin": 86, "xmax": 96}, # 0.5 GeV bin width
    "zll_p": {"name": "zll_p", "title": "p_{l^{+}l^{-}} [GeV]", "bin": 100, "xmin": 20, "xmax": 70},
    "zll_theta": {"name": "zll_theta", "title": "#theta_{l^{+}l^{-}}", "bin": 100, "xmin": 0, "xmax": 3.2},
    
    # Higgs / Recoil
    "higgs_m": {"name": "higgs_m", "title": "m_{Higgs} [GeV]", "bin": 80, "xmin": 100, "xmax": 140}, # Range expanded to (100,140) per your script
    "zll_recoil_m": {"name": "zll_recoil_m", "title": "m_{recoil} [GeV]", "bin": 40, "xmin": 120, "xmax": 140}, # 0.5 GeV bin width
    
    # More control variables
    "zll_leptons_acolinearity": {"name": "zll_leptons_acolinearity", "title": "#Delta#theta_{l^{+}l^{-}}", "bin": 100, "xmin": 0, "xmax": 3.2},
    "zll_leptons_acoplanarity": {"name": "zll_leptons_acoplanarity", "title": "#Delta#phi_{l^{+}l^{-}}", "bin": 100, "xmin": 0, "xmax": 3.2},
    "cosTheta_miss": {"name": "cosTheta_miss", "title": "cos#theta_{missing}", "bin": 100, "xmin": -1, "xmax": 1},

    # --- NEW VARIABLES FROM MATPLOTLIB SCRIPT ---
    "btag_max": {"name": "btag_max", "title": "max b-tag score", "bin": 100, "xmin": 0, "xmax": 1},
    "stag_other": {"name": "stag_other", "title": "other s-tag score", "bin": 100, "xmin": 0, "xmax": 1},
    
    "total_m": {"name": "total_m", "title": "Total reconstructed mass [GeV]", "bin": 120, "xmin": 200, "xmax": 260}, # 0.5 GeV bin width
    "total_e": {"name": "total_e", "title": "Total reconstructed energy [GeV]", "bin": 120, "xmin": 200, "xmax": 260}, # 0.5 GeV bin width
    
    "higgs_met_m": {"name": "higgs_met_m", "title": "Reconstructed Mass for jj+met [GeV]", "bin": 80, "xmin": 100, "xmax": 140}, # 0.5 GeV bin width
    "higgs_met_e": {"name": "higgs_met_e", "title": "Reconstructed Energy for jj+met [GeV]", "bin": 80, "xmin": 100, "xmax": 140}, # 0.5 GeV bin width
    
    "met_p": {"name": "met_p", "title": "MET Momentum [GeV]", "bin": 40, "xmin": 0, "xmax": 100}, # 0.5 GeV bin width
    "met_pt": {"name": "met_pt", "title": "MET Transverse Momentum [GeV]", "bin": 100, "xmin": 0, "xmax": 15}, # 0.5 GeV bin width
    "met_theta": {"name": "met_theta", "title": "#theta_{missing}", "bin": 100, "xmin": 0, "xmax": np.pi},
    "met_phi": {"name": "met_phi", "title": "#phi_{missing}", "bin": 100, "xmin": -np.pi, "xmax": np.pi},
}



