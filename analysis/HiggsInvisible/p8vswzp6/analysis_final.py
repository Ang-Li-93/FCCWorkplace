# run as: fccanalysis final analysis_HInvjj_final.py
import os
os.environ["FCCDICTSDIR"] = "/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/HiggsInvisible/lia/FCCDicts/"

#Input directory where the files produced at the pre-selection level are
inputDir  = "outputs_HInvjj/test2"
#inputDir  = "outputs_HInvjj_IDEA/stage1"

#Input directory where the files produced at the pre-selection level are
outputDir  = "outputs_HInvjj/final/"
#outputDir  = "outputs_HInvjj_IDEA/final/"


#Mandatory: List of processes
processList = {
    #'p8_ee_ZZ_ecm240':{},#Run the full statistics in one output file named <outputDir>/p8_ee_ZZ_ecm240.root
    #'p8_ee_WW_ecm240':{'fraction':0.5, 'chunks':2}, #Run 50% of the statistics in two files named <outputDir>/p8_ee_WW_ecm240/chunk<N>.root
    #'wzp6_ee_qqH_ecm240':{} #Run over the full statistics from the previous stage's input file <inputDir>/p8_ee_ZH_ecm240_out.root. 
    #'output':{} #Run over the full statistics from the previous stage's input file <inputDir>/p8_ee_ZH_ecm240_out.root. 
    'output_p8':{},
    'output_wzp6':{},
    #'output_wzp6_scott':{},
}


#Link to the dictonary that contains all the cross section informations etc...
# can be found at: /cvmfs/fcc.cern.ch/FCCDicts/
procDict = "FCCee_procDict_winter2023_IDEA.json"

#Add MySample_p8_ee_ZH_ecm240 as it is not an offical process
procDictAdd={
    "output_wzp6":{"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 1.0, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "output_p8":{"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 1.0, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "output_wzp6_scott":{"numberOfEvents": 100000, "sumOfWeights": 100000, "crossSection": 1.0, "kfactor": 1.0, "matchingEfficiency": 1.0},
}

#Number of CPUs to use
nCPUS = 1

#produces ROOT TTrees, default is False
doTree = False

###Dictionnay of the list of cuts. The key is the name of the selection that will be added to the output file
cutList = {
    "sel0_NoCuts" : "1",
    #"sel1_METCut" : "MET[0] > 10",
    # cut 60 < mZ < 100 GeV for bb, cut mZ \pm 5 GeV for qq/mumu ,  cut mZ \pm 4 GeV for ee
    "sel2_mZCut" : "ZBosonMass[0] > 60 && ZBosonMass[0] < 100", 

    #"sel3" : "selected_jets_pt_0 > 40",
    #"sel4" : "selected_jets_pt_0 > 50",
    #"sel0" : "Zcand_m > 40 && Zcand_m < 120",
}

#Dictionary for the ouput variable/hitograms. The key is the name of the variable in the output files. "name" is the name of the variable in the input file, "title" is the x-axis label of the histogram, "bin" the number of bins of the histogram, "xmin" the minimum x-axis value and "xmax" the maximum x-axis value.
histoList = {
    "jets_pt":{"name":"jets_pt","title":"jet pT [GeV]","bin":100,"xmin":0,"xmax":200},
    "ZBosonPt":{"name":"ZBosonPt","title":"ZBosonPt [GeV]","bin":100,"xmin":0,"xmax":200},
    "ZBosonMass":{"name":"ZBosonMass","title":"m_Z [GeV]","bin":200,"xmin":0,"xmax":200},
    #"MET":{"name":"MET","title":"MET [GeV]","bin":100,"xmin":0,"xmax":-1},
    "recoil_M":{"name":"recoil_M","title":"recoil_M [GeV]","bin":200,"xmin":0,"xmax":200},
    "Z_MC_no":{"name":"Z_MC_no","title":"Z_MC_no","bin":6,"xmin":-0.5,"xmax":5.5},
    "Z_MC_m":{"name":"Z_MC_m","title":"Z_MC_m","bin":80,"xmin":90.6,"xmax":91.4},
    "Z_MC_m_large":{"name":"Z_MC_m","title":"Z_MC_m","bin":80,"xmin":20,"xmax":100},
    "Z_MC_p":{"name":"Z_MC_p","title":"Z_MC_p","bin":80,"xmin":20,"xmax":100},
    "Z_MC_GenID":{"name":"Z_MC_GenID","title":"Z_MC_GenID","bin":24,"xmin":-0.5,"xmax":23.5},
    }