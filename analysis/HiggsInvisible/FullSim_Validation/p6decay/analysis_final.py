# run as: fccanalysis final analysis_HInvjj_final.py
import os
os.environ["FCCDICTSDIR"] = "/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/HiggsInvisible/lia/FCCDicts/"

#Input directory where the files produced at the pre-selection level are
inputDir  = "outputs_HInvjj/Validation_p6decay/"
#inputDir  = "outputs_HInvjj_IDEA/stage1"

#Input directory where the files produced at the pre-selection level are
outputDir  = "outputs_HInvjj/Validation_p6decay_Final/"
#outputDir  = "outputs_HInvjj_IDEA/final/"


#Mandatory: List of processes
processList = {
    #'output_ee_WW_munumunu_ecm240_p6decay':{},
    #'output_ee_WW_enuenu_ecm240_p6decay':{},
    #'output_ee_WW_lvqq_ecm240_p6decay':{},
    'output_ee_WW_munumunu_parent':{},
    'output_ee_WW_enuenu_parent':{},
    'output_ee_WW_lvqq_parent':{},
    #'output_ee_WW_munumunu_test':{},
}


#Link to the dictonary that contains all the cross section informations etc...
# can be found at: /cvmfs/fcc.cern.ch/FCCDicts/
procDict = "FCCee_procDict_winter2023_IDEA.json"

#Add MySample_p8_ee_ZH_ecm240 as it is not an offical process
procDictAdd={
    "output_wzp6":{"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 1.0, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "output_p8":{"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 1.0, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "output_ee_WW_lvqq":{"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 1.0, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "output_ee_WW_lvqq_parent":{"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 1.0, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "output_ee_WW_lvqq_p6decay_test":{"numberOfEvents": 100, "sumOfWeights": 100, "crossSection": 1.0, "kfactor": 1.0, "matchingEfficiency": 1.0}, 
    "output_ee_WW_munumunu":{"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 1.0, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "output_ee_WW_munumunu_parent":{"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 1.0, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "output_ee_WW_enuenu":{"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 1.0, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "output_ee_WW_enuenu_parent":{"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 1.0, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "output_ee_ZZ_nunuqq":{"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 1.0, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "output_ee_WW_munumunu_test":{"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 1.0, "kfactor": 1.0, "matchingEfficiency": 1.0},
    
}

#Number of CPUs to use
nCPUS = 1

#produces ROOT TTrees, default is False
doTree = False

###Dictionnay of the list of cuts. The key is the name of the selection that will be added to the output file
cutList = {
    "sel0_NoCuts" : "1", 
    "sel2_mZCut" : "ZBosonMass[0] > 60 && ZBosonMass[0] < 100", 

}

#Dictionary for the ouput variable/hitograms. The key is the name of the variable in the output files. "name" is the name of the variable in the input file, "title" is the x-axis label of the histogram, "bin" the number of bins of the histogram, "xmin" the minimum x-axis value and "xmax" the maximum x-axis value.
histoList = {

    # Muons
    "n_muons":{"name":"n_muons","title":"n_muons","bin":10,"xmin":-0.5,"xmax":9.5}, 
    "muons_p":{"name":"muons_p","title":"Muon Momentum [GeV]","bin":100,"xmin":0,"xmax":200},
    "muons_e":{"name":"muons_e","title":"Muon Energy [GeV]","bin":100,"xmin":0,"xmax":200},
    "muons_y":{"name":"muons_y","title":"Muon Rapidity","bin":100,"xmin":-5,"xmax":5},
    # Electrons:
    "n_electrons":{"name":"n_electrons","title":"n_electrons","bin":10,"xmin":-0.5,"xmax":9.5},
    "electrons_p":{"name":"electrons_p","title":"Electron Momentum [GeV]","bin":100,"xmin":0,"xmax":200},
    "electrons_e":{"name":"electrons_e","title":"Electron Energy [GeV]","bin":100,"xmin":0,"xmax":200},
    "electrons_y":{"name":"electrons_y","title":"Electron Rapidity","bin":100,"xmin":-5,"xmax":5},
    # Jets
    "n_jets":{"name":"n_jets","title":"n_jets","bin":10,"xmin":-0.5,"xmax":9.5},
    "jets_p":{"name":"jets_p","title":"Jet Transverse Momentum [GeV]","bin":100,"xmin":0,"xmax":200},
    "jets_e":{"name":"jets_e","title":"Jet Energy [GeV]","bin":100,"xmin":0,"xmax":200},
    "jets_y":{"name":"jets_y","title":"Jet Rapidity","bin":100,"xmin":-5,"xmax":5},

    #Delta Rs
    "deltaR_muJet_00":{"name":"deltaR_muJet_00","title":"deltaR_muJet_00","bin":100,"xmin":0,"xmax":5},
    "deltaR_muJet_01":{"name":"deltaR_muJet_01","title":"deltaR_muJet_01","bin":100,"xmin":0,"xmax":5},
    "deltaR_muJet_10":{"name":"deltaR_muJet_10","title":"deltaR_muJet_02","bin":100,"xmin":0,"xmax":5},
    "deltaR_muJet_11":{"name":"deltaR_muJet_11","title":"deltaR_muJet_11","bin":100,"xmin":0,"xmax":5},
    "deltaR_eJet_00":{"name":"deltaR_eJet_00","title":"deltaR_eJet_00","bin":100,"xmin":0,"xmax":5},
    "deltaR_eJet_01":{"name":"deltaR_eJet_01","title":"deltaR_eJet_01","bin":100,"xmin":0,"xmax":5},
    "deltaR_eJet_10":{"name":"deltaR_eJet_10","title":"deltaR_eJet_02","bin":100,"xmin":0,"xmax":5},
    "deltaR_eJet_11":{"name":"deltaR_eJet_11","title":"deltaR_eJet_11","bin":100,"xmin":0,"xmax":5},

    # Reconstructed Z boson
    "ZBosonP":{"name":"ZBosonP","title":"Z Candidate P [GeV]","bin":100,"xmin":0,"xmax":200},
    "ZBosonMass":{"name":"ZBosonMass","title":"Z Candidate Mass [GeV]","bin":200,"xmin":0,"xmax":200},

    # Recoil:
    "recoil_M":{"name":"recoil_M","title":"recoil_M [GeV]","bin":200,"xmin":0,"xmax":200},
    # MC particles:
    "MC_GenID":{"name":"MC_GenID","title":"MC_GenID","bin":24,"xmin":-0.5,"xmax":23.5}, 
    "W_MC_no":{"name":"W_MC_no","title":"W_MC_no","bin":6,"xmin":-0.5,"xmax":5.5},
    "W_MC_m":{"name":"W_MC_m","title":"W_MC_m","bin":80,"xmin":20,"xmax":100},
    "W_MC_p":{"name":"W_MC_p","title":"W_MC_p","bin":80,"xmin":20,"xmax":100},
    "W_MC_GenID":{"name":"W_MC_GenID","title":"W_MC_GenID","bin":24,"xmin":-0.5,"xmax":23.5},
    "pdgID":{"name":"pdgID","title":"pdgID","bin":101,"xmin":-50.5,"xmax":50.5},
   
    "Wp_MC_no":{"name":"Wp_MC_no","title":"Wp_MC_no","bin":6,"xmin":-0.5,"xmax":5.5},
    "daughter_Wp_no":{"name":"daughter_Wp_no","title":"daughter_Wp_no","bin":6,"xmin":-0.5,"xmax":5.5},
    "daughter_Wp_0_pid":{"name":"daughter_Wp_0_pid","title":"daughter_Wp_0_pid","bin":101,"xmin":-50.5,"xmax":50.5},
    "daughter_Wp_1_pid":{"name":"daughter_Wp_1_pid","title":"daughter_Wp_1_pid","bin":101,"xmin":-50.5,"xmax":50.5},
    "Wm_MC_no":{"name":"Wm_MC_no","title":"Wm_MC_no","bin":6,"xmin":-0.5,"xmax":5.5},
    "daughter_Wm_no":{"name":"daughter_Wm_no","title":"daughter_Wm_no","bin":6,"xmin":-0.5,"xmax":5.5},
    "daughter_Wm_0_pid":{"name":"daughter_Wm_0_pid","title":"daughter_Wm_0_pid","bin":101,"xmin":-50.5,"xmax":50.5},
    "daughter_Wm_1_pid":{"name":"daughter_Wm_1_pid","title":"daughter_Wm_1_pid","bin":101,"xmin":-50.5,"xmax":50.5},
    
    "Muon_MC_Parent":{"name":"Muon_MC_Parent","title":"Muon_MC_Parent","bin":51,"xmin":-0.5,"xmax":50.5},
    "Muon_MC_no":{"name":"Muon_MC_no","title":"Muon_MC_no","bin":6,"xmin":-0.5,"xmax":5.5},
    "Electron_MC_Parent":{"name":"Electron_MC_Parent","title":"Electron_MC_Parent","bin":51,"xmin":-0.5,"xmax":50.5},
    "Electron_MC_no":{"name":"Electron_MC_no","title":"Electron_MC_no","bin":6,"xmin":-0.5,"xmax":5.5},
    }