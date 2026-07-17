#python examples/FCCee/higgs/mH-recoil/mumu/finalSel.py

#Input directory where the files produced at the pre-selection level are
inputDir = "/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/HiggsInvisible/lia/muon_comparison/stage1"

#Input directory where the files produced at the pre-selection level are
outputDir = "/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/HiggsInvisible/lia/muon_comparison/final"

###Link to the dictonary that contains all the cross section informations etc...
procDict = "FCCee_procDict_winter2023_IDEA.json"
#Add MySample_p8_ee_ZH_ecm240 as it is not an offical process

###Process list that should match the produced files.
processList = {
                #signal
                #"wzp6_ee_mumuH_ecm240",
                #"wzp6_ee_mumuH_HZZ_ecm240",
                #"p8_ee_WW_ecm240",
                #"p8_ee_ZZ_ecm240",
                "wzp6_ee_mumu_ecm240",
                "wzp6_ee_tautau_ecm240",
                #rare backgrounds:
                #"wzp6_egamma_eZ_Zmumu_ecm240",
                #"wzp6_gammae_eZ_Zmumu_ecm240",
                #"wzp6_gaga_mumu_60_ecm240",
                #"wzp6_gaga_tautau_60_ecm240",
                #"wzp6_ee_nuenueZ_ecm240"
              }
###Add MySample_p8_ee_ZH_ecm240 as it is not an offical process

#Number of CPUs to use
nCPUS = 2
#produces ROOT TTrees, default is False
doTree = False

###Dictionnay of the list of cuts. The key is the name of the selection that will be added to the output file
cutList = {
            #"NoSel":"return true",
            #"sel1":"muons_no==2",
            #"sel2":"muons_no==2 && electrons_no==0",
            #"sel3":"muons_no==2 && electrons_no==0 && Z_m[0] > 86 && Z_m[0] < 96",
            #"sel4":"muons_no==2 && electrons_no==0 && Z_m[0] > 86 && Z_m[0] < 96 && missing_mass[0] > 100 && missing_mass[0] < 140", 
            #"sel5":"muons_no==2 && electrons_no==0 && Z_m[0] > 86 && Z_m[0] < 96 && missing_mass[0] > 100 && missing_mass[0] < 140 && visible_mass[0] > 86 && visible_mass[0] < 96",
            "sel_BNL1":"muons_no==2 && electrons_no==0 && Z_m[0] > 87 && Z_m[0] < 95 && missing_pt[0] > 10 && muons_p[0] > 10 && muons_p[1] > 10",
            #"sel_BNL2":"muons_no==2 && electrons_no==0 && Z_m[0] > 87 && Z_m[0] < 95 && missing_pt[0] > 11 && muons_p[0] > 10 && muons_p[1] > 10",
            #"sel_BNL3":"muons_no==2 && electrons_no==0 && Z_m[0] > 87 && Z_m[0] < 95 && missing_pt[0] > 15 && muons_p[0] > 10 && muons_p[1] > 10",
            #"sel_BNL4":"muons_no==2 && electrons_no==0 && Z_m[0] > 87 && Z_m[0] < 95 && missing_pt[0] > 20 && muons_p[0] > 10 && muons_p[1] > 10",
            }


###Dictionary for the ouput variable/hitograms. The key is the name of the variable in the output files. "name" is the name of the variable in the input file, "title" is the x-axis label of the histogram, "bin" the number of bins of the histogram, "xmin" the minimum x-axis value and "xmax" the maximum x-axis value.


histoList = {
    # Zed
    "Z_m": {"name": "Z_m", "title": "m_{Z} [GeV]", "bin": 125, "xmin": 0, "xmax": 250},
    "Z_p": {"name": "Z_p", "title": "zll_p", "bin": 200, "xmin": 0, "xmax": 200},
    "Z_theta": {"name": "Z_theta", "title": "zll_theta", "bin": 70, "xmin": -3.5, "xmax": 3.5},
    "Z_phi": {"name": "Z_phi", "title": "zll_phi", "bin": 70, "xmin": -3.5, "xmax": 3.5},

    # Recoil
    "Z_recoil_m": {"name": "Z_recoil_m", "title": "Recoil m_{Z} [GeV]", "bin": 125, "xmin": 0, "xmax": 250},
    "Z_recoil_p": {"name": "Z_recoil_p", "title": "Recoil p_{Z} [GeV]", "bin": 200, "xmin": 0, "xmax": 200},
    "Z_recoil_theta": {"name": "Z_recoil_theta", "title": "Recoil #theta_{Z}", "bin": 70, "xmin": -3.5, "xmax": 3.5},
    "Z_recoil_phi": {"name": "Z_recoil_phi", "title": "Recoil #phi_{Z}", "bin": 70, "xmin": -3.5, "xmax": 3.5},

    # Missing
    "missing_mass": {"name": "missing_mass", "title": "Missing Mass [GeV]", "bin": 125, "xmin": 0, "xmax": 250},
    "missing_e": {"name": "missing_e", "title": "Missing Energy [GeV]", "bin": 200, "xmin": 0, "xmax": 200},
    "missing_p": {"name": "missing_p", "title": "Missing Momentum [GeV]", "bin": 200, "xmin": 0, "xmax": 200},
    "missing_theta": {"name": "missing_theta", "title": "Missing #theta", "bin": 70, "xmin": -3.5, "xmax": 3.5},
    "missing_phi": {"name": "missing_phi", "title": "Missing #phi", "bin": 70, "xmin": -3.5, "xmax": 3.5},
    "missing_px": {"name": "missing_px", "title": "Missing p_{x} [GeV]", "bin": 200, "xmin": 0, "xmax": 200},
    "missing_py": {"name": "missing_py", "title": "Missing p_{y} [GeV]", "bin": 200, "xmin": 0, "xmax": 200},
    "missing_pz": {"name": "missing_pz", "title": "Missing p_{z} [GeV]", "bin": 200, "xmin": 0, "xmax": 200},
    "missing_pt": {"name": "missing_pt", "title": "Missing p_{T} [GeV]", "bin": 200, "xmin": 0, "xmax": 200},
    "missing_costheta": {"name": "missing_costheta", "title": "Missing cos(#theta)", "bin": 200, "xmin": -1, "xmax": 1},
    
    # Visible
    "visible_mass": {"name": "visible_mass", "title": "Visible Mass [GeV]", "bin": 125, "xmin": 0, "xmax": 250},
    "visible_e": {"name": "visible_e", "title": "Visible Energy [GeV]", "bin": 200, "xmin": 0, "xmax": 200},
    "visible_p": {"name": "visible_p", "title": "Visible Momentum [GeV]", "bin": 200, "xmin": 0, "xmax": 200},
    "visible_theta": {"name": "visible_theta", "title": "Visible #theta", "bin": 70, "xmin": -3.5, "xmax": 3.5},
    "visible_phi": {"name": "visible_phi", "title": "Visible #phi", "bin": 70, "xmin": -3.5, "xmax": 3.5},
    "visible_px": {"name": "visible_px", "title": "Visible p_{x} [GeV]", "bin": 200, "xmin": -100, "xmax": 100},
    "visible_py": {"name": "visible_py", "title": "Visible p_{y} [GeV]", "bin": 200, "xmin": -100, "xmax": 100},
    "visible_pz": {"name": "visible_pz", "title": "Visible p_{z} [GeV]", "bin": 200, "xmin": -100, "xmax": 100},

    # Muons
    "muons_p": {"name": "muons_p", "title": "Muon Momentum [GeV]", "bin": 200, "xmin": 0, "xmax": 200},
    "muons_theta": {"name": "muons_theta", "title": "Muon #theta", "bin": 70, "xmin": -3.5, "xmax": 3.5},
    "muons_phi": {"name": "muons_phi", "title": "Muon #phi", "bin": 70, "xmin": -3.5, "xmax": 3.5},
    "muons_no": {"name": "muons_no", "title": "Number of Muons", "bin": 6, "xmin": -0.5, "xmax": 5.5},

    # Electrons
    "electrons_p": {"name": "electrons_p", "title": "Electron Momentum [GeV]", "bin": 200, "xmin": 0, "xmax": 200},
    "electrons_theta": {"name": "electrons_theta", "title": "Electron #theta", "bin": 70, "xmin": -3.5, "xmax": 3.5},
    "electrons_phi": {"name": "electrons_phi", "title": "Electron #phi", "bin": 70, "xmin": -3.5, "xmax": 3.5},
    "electrons_no": {"name": "electrons_no", "title": "Number of Electrons", "bin": 6, "xmin": -0.5, "xmax": 5.5},

    # Others
    "ZHChi2": {"name": "ZHChi2", "title": "ZHChi2", "bin": 100, "xmin": 0, "xmax": 100},
    "leps_iso": {"name": "leps_iso", "title": "Leptons Isolation", "bin": 100, "xmin": 0, "xmax": 100},

    #Zoom in 
    "Z_recoil_m_zoom1": {"name": "Z_recoil_m", "title": "Recoil m_{Z} [GeV]", "bin": 100, "xmin": 120, "xmax": 140},
    
}


