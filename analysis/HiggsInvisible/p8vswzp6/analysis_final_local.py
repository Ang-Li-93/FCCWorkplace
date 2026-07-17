# run as: fccanalysis final analysis_HInvjj_final.py

#Input directory where the files produced at the pre-selection level are
inputDir  = "outputs_HInvjj_CLIC/stage1"
#inputDir  = "outputs_HInvjj_IDEA/stage1"

#Input directory where the files produced at the pre-selection level are
outputDir  = "outputs_HInvjj_CLIC/final/"
#outputDir  = "outputs_HInvjj_IDEA/final/"


#Mandatory: List of processes
processList = {
    #'p8_ee_ZZ_ecm240':{},#Run the full statistics in one output file named <outputDir>/p8_ee_ZZ_ecm240.root
    #'p8_ee_WW_ecm240':{'fraction':0.5, 'chunks':2}, #Run 50% of the statistics in two files named <outputDir>/p8_ee_WW_ecm240/chunk<N>.root
    #'wzp6_ee_qqH_ecm240':{} #Run over the full statistics from the previous stage's input file <inputDir>/p8_ee_ZH_ecm240_out.root. 
    'output':{} #Run over the full statistics from the previous stage's input file <inputDir>/p8_ee_ZH_ecm240_out.root. 
}


#Link to the dictonary that contains all the cross section informations etc...
# can be found at: /cvmfs/fcc.cern.ch/FCCDicts/
procDict = "FCCee_procDict_winter2023_IDEA.json"

#Add MySample_p8_ee_ZH_ecm240 as it is not an offical process
procDictAdd={"output":{"numberOfEvents": 1200000, "sumOfWeights": 1200000, "crossSection": 0.0067643, "kfactor": 1.0, "matchingEfficiency": 1.0}}

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
#histoList = {
#    "mz":{"name":"Zcand_m","title":"m_{Z} [GeV]","bin":125,"xmin":0,"xmax":250},
#    "mz_zoom":{"name":"Zcand_m","title":"m_{Z} [GeV]","bin":40,"xmin":80,"xmax":100},
#    "leptonic_recoil_m":{"name":"Zcand_recoil_m","title":"Z leptonic recoil [GeV]","bin":100,"xmin":0,"xmax":200},
#    "leptonic_recoil_m_zoom":{"name":"Zcand_recoil_m","title":"Z leptonic recoil [GeV]","bin":200,"xmin":80,"xmax":160},
#    "leptonic_recoil_m_zoom1":{"name":"Zcand_recoil_m","title":"Z leptonic recoil [GeV]","bin":100,"xmin":120,"xmax":140},
#    "leptonic_recoil_m_zoom2":{"name":"Zcand_recoil_m","title":"Z leptonic recoil [GeV]","bin":200,"xmin":120,"xmax":140},
#    "leptonic_recoil_m_zoom3":{"name":"Zcand_recoil_m","title":"Z leptonic recoil [GeV]","bin":400,"xmin":120,"xmax":140},
#    "leptonic_recoil_m_zoom4":{"name":"Zcand_recoil_m","title":"Z leptonic recoil [GeV]","bin":800,"xmin":120,"xmax":140},
#    "leptonic_recoil_m_zoom5":{"name":"Zcand_recoil_m","title":"Z leptonic recoil [GeV]","bin":2000,"xmin":120,"xmax":140},
#    "leptonic_recoil_m_zoom6":{"name":"Zcand_recoil_m","title":"Z leptonic recoil [GeV]","bin":100,"xmin":130.3,"xmax":132.5},
#}

#Dictionary for the ouput variable/hitograms. The key is the name of the variable in the output files. "name" is the name of the variable in the input file, "title" is the x-axis label of the histogram, "bin" the number of bins of the histogram, "xmin" the minimum x-axis value and "xmax" the maximum x-axis value.
histoList = {
    "jets_pt":{"name":"jets_pt","title":"jet pT [GeV]","bin":100,"xmin":0,"xmax":-1},
    "ZBosonPt":{"name":"ZBosonPt","title":"ZBosonPt [GeV]","bin":100,"xmin":0,"xmax":-1},
    "ZBosonMass":{"name":"ZBosonMass","title":"m_Z [GeV]","bin":200,"xmin":0,"xmax":200},
    #"MET":{"name":"MET","title":"MET [GeV]","bin":100,"xmin":0,"xmax":-1},
    "recoil_M":{"name":"recoil_M","title":"recoil_M [GeV]","bin":200,"xmin":100,"xmax":200},



    }