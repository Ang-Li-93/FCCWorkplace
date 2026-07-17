import numpy as np

#python examples/FCCee/higgs/mH-recoil/mumu/finalSel.py
#Input directory where the files produced at the pre-selection level are
# inputDir = "/afs/cern.ch/user/d/dduan/private/FCCWorkplace/analysis/Hbs/mumu/ROOT_Files"
inputDir = "/eos/user/d/dduan/FCCee/Hbs/mumu/BDT_analysis_samples"

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
    "wzp6_ee_mumuH_Hcu_W4p1MeV_ecm240": {"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 0.01, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_ee_mumuH_Hbd_W4p1MeV_ecm240": {"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 0.01, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_ee_mumuH_Huu_W4p1MeV_ecm240": {"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 0.01, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_ee_mumuH_Hdd_W4p1MeV_ecm240": {"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 0.01, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_ee_mumuH_Hsd_W4p1MeV_ecm240": {"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 0.01, "kfactor": 1.0, "matchingEfficiency": 1.0},
}


###Process list that should match the produced files.
processList = {
    # Off-Diagonal Higgs Decays (FCNC Signals)
    "wzp6_ee_mumuH_Hbs_W4p1MeV_ecm240",
    "wzp6_ee_mumuH_Hbd_W4p1MeV_ecm240",
    "wzp6_ee_mumuH_Hcu_W4p1MeV_ecm240",
    "wzp6_ee_mumuH_Hsd_W4p1MeV_ecm240",

    # Higgs Decays (Bosons / Leptons)
    "wzp6_ee_mumuH_HWW_ecm240",
    "wzp6_ee_mumuH_HZZ_noInv_ecm240",
    "wzp6_ee_mumuH_Htautau_ecm240",
    "wzp6_ee_mumuH_HZa_ecm240",

    # Diagonal Higgs Decays (Quarks & Gluons)
    "wzp6_ee_mumuH_Hbb_ecm240",
    "wzp6_ee_mumuH_Hss_ecm240",
    "wzp6_ee_mumuH_Hcc_ecm240",
    "wzp6_ee_mumuH_Hdd_ecm240",
    "wzp6_ee_mumuH_Huu_ecm240",
    "wzp6_ee_mumuH_Hgg_ecm240",

    # Standard Model Backgrounds
    #"wzp6_ee_mumuH_ecm240",
    "p8_ee_ZZ_ecm240",
    "p8_ee_WW_ecm240",
    "wzp6_ee_mumu_ecm240",
    
    # Rare Backgrounds
    "wzp6_egamma_eZ_Zmumu_ecm240",
    "wzp6_gammae_eZ_Zmumu_ecm240",
    "wzp6_gaga_mumu_60_ecm240",
}

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
    # ── Plot Fundamental Lepton Variables ──────────────────────────────────────
    "leading_zll_lepton_p": {"name": "leading_zll_lepton_p", "title": "p_{l,leading} [GeV]", "bin": 100, "xmin": 45, "xmax": 85},
    "leading_zll_lepton_theta": {"name": "leading_zll_lepton_theta", "title": "#theta_{l,leading}", "bin": 100, "xmin": 0, "xmax": 3.2},
    "subleading_zll_lepton_p": {"name": "subleading_zll_lepton_p", "title": "p_{l,subleading}  [GeV]", "bin": 100, "xmin": 20, "xmax": 60},
    "subleading_zll_lepton_theta": {"name": "subleading_zll_lepton_theta", "title": "#theta_{l,subleading}", "bin": 100, "xmin": 0, "xmax": 3.2},
    
    # ── Zed Resonances ────────────────────────────────────────────────────────
    "zll_m": {"name": "zll_m", "title": "m_{l^{+}l^{-}} [GeV]", "bin": 20, "xmin": 86, "xmax": 96}, # 0.5 GeV bin width
    "zll_p": {"name": "zll_p", "title": "p_{l^{+}l^{-}} [GeV]", "bin": 100, "xmin": 20, "xmax": 70},
    "zll_theta": {"name": "zll_theta", "title": "#theta_{l^{+}l^{-}}", "bin": 100, "xmin": 0, "xmax": 3.2},
    
    # ── Higgs / Recoil ────────────────────────────────────────────────────────
    "higgs_m": {"name": "higgs_m", "title": "m_{Higgs} [GeV]", "bin": 80, "xmin": 100, "xmax": 140}, 
    "zll_recoil_m": {"name": "zll_recoil_m", "title": "m_{recoil} [GeV]", "bin": 40, "xmin": 120, "xmax": 140}, # 0.5 GeV bin width
    
    # ── Lepton Angular / MET Control Variables ─────────────────────────────────
    "zll_leptons_acolinearity": {"name": "zll_leptons_acolinearity", "title": "#Delta#theta_{l^{+}l^{-}}", "bin": 100, "xmin": 0, "xmax": 3.2},
    "zll_leptons_acoplanarity": {"name": "zll_leptons_acoplanarity", "title": "#Delta#phi_{l^{+}l^{-}}", "bin": 100, "xmin": 0, "xmax": 3.2},
    "cosTheta_miss": {"name": "cosTheta_miss", "title": "cos#theta_{missing}", "bin": 100, "xmin": -1, "xmax": 1},

    # ── Jet Flavor Tagging Scores ──────────────────────────────────────────────
    "btag_max": {"name": "btag_max", "title": "max b-tag score", "bin": 100, "xmin": 0, "xmax": 1},
    "stag_other": {"name": "stag_other", "title": "other s-tag score", "bin": 100, "xmin": 0, "xmax": 1},
    "jet1_btag": {"name": "jet1_btag", "title": "Jet 1 b-tag score", "bin": 100, "xmin": 0, "xmax": 1},
    "jet2_btag": {"name": "jet2_btag", "title": "Jet 2 b-tag score", "bin": 100, "xmin": 0, "xmax": 1},
    "jet1_stag": {"name": "jet1_stag", "title": "Jet 1 s-tag score", "bin": 100, "xmin": 0, "xmax": 1},
    "jet2_stag": {"name": "jet2_stag", "title": "Jet 2 s-tag score", "bin": 100, "xmin": 0, "xmax": 1},
    "jet1_ctag": {"name": "jet1_ctag", "title": "Jet 1 c-tag score", "bin": 100, "xmin": 0, "xmax": 1},
    "jet2_ctag": {"name": "jet2_ctag", "title": "Jet 2 c-tag score", "bin": 100, "xmin": 0, "xmax": 1},
    "jet1_utag": {"name": "jet1_utag", "title": "Jet 1 u-tag score", "bin": 100, "xmin": 0, "xmax": 1},
    "jet2_utag": {"name": "jet2_utag", "title": "Jet 2 u-tag score", "bin": 100, "xmin": 0, "xmax": 1},
    "jet1_dtag": {"name": "jet1_dtag", "title": "Jet 1 d-tag score", "bin": 100, "xmin": 0, "xmax": 1},
    "jet2_dtag": {"name": "jet2_dtag", "title": "Jet 2 d-tag score", "bin": 100, "xmin": 0, "xmax": 1},
    "jet1_Gtag": {"name": "jet1_Gtag", "title": "Jet 1 gluon-tag score", "bin": 100, "xmin": 0, "xmax": 1},
    "jet2_Gtag": {"name": "jet2_Gtag", "title": "Jet 2 gluon-tag score", "bin": 100, "xmin": 0, "xmax": 1},
    "jet1_tautag": {"name": "jet1_tautag", "title": "Jet 1 tau-tag score", "bin": 100, "xmin": 0, "xmax": 1},
    "jet2_tautag": {"name": "jet2_tautag", "title": "Jet 2 tau-tag score", "bin": 100, "xmin": 0, "xmax": 1},

    # ── Jet Kinematics and Merging Scales ──────────────────────────────────────
    "jet1_p": {"name": "jet1_p", "title": "p_{jet 1} [GeV]", "bin": 100, "xmin": 0, "xmax": 100},
    "jet2_p": {"name": "jet2_p", "title": "p_{jet 2} [GeV]", "bin": 100, "xmin": 0, "xmax": 100},
    "jet1_E": {"name": "jet1_E", "title": "E_{jet 1} [GeV]", "bin": 100, "xmin": 0, "xmax": 100},
    "jet2_E": {"name": "jet2_E", "title": "E_{jet 2} [GeV]", "bin": 100, "xmin": 0, "xmax": 100},
    "jet1_mass": {"name": "jet1_mass", "title": "m_{jet 1} [GeV]", "bin": 100, "xmin": 0, "xmax": 50},
    "jet2_mass": {"name": "jet2_mass", "title": "m_{jet 2} [GeV]", "bin": 100, "xmin": 0, "xmax": 50},
    "jet1_nconst": {"name": "jet1_nconst", "title": "Constituent multiplicity (Jet 1)", "bin": 50, "xmin": 0, "xmax": 50},
    "jet2_nconst": {"name": "jet2_nconst", "title": "Constituent multiplicity (Jet 2)", "bin": 50, "xmin": 0, "xmax": 50},
    "event_d12": {"name": "event_d12", "title": "d_{12} jet-merging scale [GeV^{2}]", "bin": 100, "xmin": 0, "xmax": 15000},
    "event_d23": {"name": "event_d23", "title": "d_{23} jet-merging scale [GeV^{2}]", "bin": 100, "xmin": 0, "xmax": 5000},
    "event_d34": {"name": "event_d34", "title": "d_{34} jet-merging scale [GeV^{2}]", "bin": 100, "xmin": 0, "xmax": 2000},
    "event_d45": {"name": "event_d45", "title": "d_{45} jet-merging scale [GeV^{2}]", "bin": 100, "xmin": 0, "xmax": 1000},

    # ── Event-Wide Mass, Energy and MET ────────────────────────────────────────
    "total_m": {"name": "total_m", "title": "Total reconstructed mass [GeV]", "bin": 120, "xmin": 200, "xmax": 260},
    "total_e": {"name": "total_e", "title": "Total reconstructed energy [GeV]", "bin": 120, "xmin": 200, "xmax": 260},
    "higgs_met_m": {"name": "higgs_met_m", "title": "Reconstructed Mass for jj+met [GeV]", "bin": 80, "xmin": 100, "xmax": 140},
    "higgs_met_e": {"name": "higgs_met_e", "title": "Reconstructed Energy for jj+met [GeV]", "bin": 80, "xmin": 100, "xmax": 140},
    "met_p": {"name": "met_p", "title": "MET Momentum [GeV]", "bin": 40, "xmin": 0, "xmax": 100},
    "met_pt": {"name": "met_pt", "title": "MET Transverse Momentum [GeV]", "bin": 100, "xmin": 0, "xmax": 15},
    "met_theta": {"name": "met_theta", "title": "#theta_{missing}", "bin": 100, "xmin": 0, "xmax": np.pi},
    "met_phi": {"name": "met_phi", "title": "#phi_{missing}", "bin": 100, "xmin": -np.pi, "xmax": np.pi},

    # ── Multi-Class BDT Raw Output Scores ──────────────────────────────────────
    "BDTscore_class0": {"name": "BDTscore_class0", "title": "Raw BDT Score (Class 0)", "bin": 20, "xmin": 0.0, "xmax": 1.0},
    "BDTscore_class1": {"name": "BDTscore_class1", "title": "Raw BDT Score (Class 1)", "bin": 20, "xmin": 0.0, "xmax": 1.0},
    "BDTscore_class2": {"name": "BDTscore_class2", "title": "Raw BDT Score (Class 2)", "bin": 20, "xmin": 0.0, "xmax": 1.0},
    "BDTscore_class3": {"name": "BDTscore_class3", "title": "Raw BDT Score (Class 3)", "bin": 20, "xmin": 0.0, "xmax": 1.0},
    "BDTscore_class4": {"name": "BDTscore_class4", "title": "Raw BDT Score (Class 4)", "bin": 20, "xmin": 0.0, "xmax": 1.0},
    "BDTscore_class5": {"name": "BDTscore_class5", "title": "Raw BDT Score (Class 5)", "bin": 20, "xmin": 0.0, "xmax": 1.0},
    "BDTscore_class6": {"name": "BDTscore_class6", "title": "Raw BDT Score (Class 6)", "bin": 20, "xmin": 0.0, "xmax": 1.0},
    "BDTscore_class7": {"name": "BDTscore_class7", "title": "Raw BDT Score (Class 7)", "bin": 20, "xmin": 0.0, "xmax": 1.0},

    # ── Multi-Class BDT Normalized Probabilities ──────────────────────────────
    "norm_prob0": {"name": "norm_prob0", "title": "Normalized Prob (Class 0)", "bin": 20, "xmin": 0.0, "xmax": 1.0},
    "norm_prob1": {"name": "norm_prob1", "title": "Normalized Prob (Class 1)", "bin": 20, "xmin": 0.0, "xmax": 1.0},
    "norm_prob2": {"name": "norm_prob2", "title": "Normalized Prob (Class 2)", "bin": 20, "xmin": 0.0, "xmax": 1.0},
    "norm_prob3": {"name": "norm_prob3", "title": "Normalized Prob (Class 3)", "bin": 20, "xmin": 0.0, "xmax": 1.0},
    "norm_prob4": {"name": "norm_prob4", "title": "Normalized Prob (Class 4)", "bin": 20, "xmin": 0.0, "xmax": 1.0},
    "norm_prob5": {"name": "norm_prob5", "title": "Normalized Prob (Class 5)", "bin": 20, "xmin": 0.0, "xmax": 1.0},
}



