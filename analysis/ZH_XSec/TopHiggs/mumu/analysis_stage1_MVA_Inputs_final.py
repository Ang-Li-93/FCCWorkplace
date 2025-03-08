#python examples/FCCee/higgs/mH-recoil/mumu/finalSel.py
#Input directory where the files produced at the pre-selection level are
inputDir = "/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/mass_xsec/lia/FCCee/TopHiggs/mumu/MVAInputs/"

#Input directory where the files produced at the pre-selection level are
outputDir = "/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/mass_xsec/lia/FCCee/TopHiggs/mumu/MVAInputs/final"

###Link to the dictonary that contains all the cross section informations etc...
procDict = "FCCee_procDict_winter2023_IDEA.json"
#Add MySample_p8_ee_ZH_ecm240 as it is not an offical process

###Process list that should match the produced files.
processList = {
                
                'wzp6_ee_mumuH_ecm365',
                'p8_ee_tt_ecm365',
                'p8_ee_WW_ecm365',
                'wzp6_egamma_eZ_Zmumu_ecm365',
                'wzp6_gammae_eZ_Zmumu_ecm365',
                'wzp6_ee_mumu_ecm365',
                'wzp6_ee_tautau_ecm365',
                'p8_ee_ZZ_ecm365',
                "wzp6_gaga_mumu_60_ecm365",
                "wzp6_gaga_tautau_60_ecm365",
                "wzp6_ee_nunuH_ecm365",
              }
###Add MySample_p8_ee_ZH_ecm240 as it is not an offical process

#Number of CPUs to use
nCPUS = 2
#produces ROOT TTrees, default is False
doTree = False

###Dictionnay of the list of cuts. The key is the name of the selection that will be added to the output file
cutList = { 
            ####baseline without costhetamiss 
            #"noselection":"true",
            #"sel_Basic":"zll_m  > 86 && zll_m  < 96  && zll_recoil_m > 120 &&zll_recoil_m  <140 && zll_p  > 20 && zll_p  <70",
            #"sel_Baseline":"zll_m  > 86 && zll_m  < 96  && zll_recoil_m > 120 &&zll_recoil_m  <140 && zll_p  > 20 && zll_p  <70 && cosTheta_miss.size() >=1 && cosTheta_miss[0] > -0.98 && cosTheta_miss[0] < 0.98",
            #"sel_Baseline_pT20":"zll_m  > 86 && zll_m  < 96  && zll_recoil_m > 120 &&zll_recoil_m  <140 && zll_p  > 20 && cosTheta_miss.size() >=1 && cosTheta_miss[0] > -0.98 && cosTheta_miss[0] < 0.98", 
            "sel_Basic_p20":"zll_m  > 86 && zll_m  < 96  && zll_recoil_m > 120 &&zll_recoil_m  <140 && zll_p  > 20",            
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
    "zll_m_large":{"name":"zll_m","title":"m_{l^{+}l^{-}} [GeV]","bin":100,"xmin":0,"xmax":200},
    "zll_p":{"name":"zll_p","title":"p_{l^{+}l^{-}} [GeV]","bin":100,"xmin":20,"xmax":70},
    "zll_p_large":{"name":"zll_p","title":"p_{l^{+}l^{-}} [GeV]","bin":100,"xmin":0,"xmax":200},
    "zll_theta":{"name":"zll_theta","title":"#theta_{l^{+}l^{-}}","bin":100,"xmin":0,"xmax":3.2},
    #more control variables
    "zll_leptons_acolinearity":{"name":"zll_leptons_acolinearity","title":"#Delta#theta_{l^{+}l^{-}}","bin":100,"xmin":0,"xmax":3.2},
    "zll_leptons_acoplanarity":{"name":"zll_leptons_acoplanarity","title":"#Delta#phi_{l^{+}l^{-}}","bin":100,"xmin":0,"xmax":3.2},
    #Recoil
    "zll_recoil_m":{"name":"zll_recoil_m","title":"m_{recoil} [GeV]","bin":100,"xmin":120,"xmax":140},
    "zll_recoil_m_large":{"name":"zll_recoil_m","title":"p_{recoil} [GeV]","bin":100,"xmin":0,"xmax":300},
    #missing Information
    "cosTheta_miss":{"name":"cosTheta_miss","title":"cos#theta_{missing}","bin":100,"xmin":-1,"xmax":1},
    #Higgsstrahlungness
    "H":{"name":"H","title":"Higgsstrahlungness","bin":110,"xmin":0,"xmax":110} 

}



