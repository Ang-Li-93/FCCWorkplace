import ROOT

# global parameters
intLumi					= 10.8e+06 #in pb-1
ana_tex        	= 'e^{+}e^{-} #rightarrow ZH #rightarrow #mu^{+}#mu^{-} + X'
#delphesVersion = '3.4.2'
energy         	= 240.0
collider       	= 'FCC-ee'
inputDir         = '/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/mass_xsec/lia/FCCee/FinalReport/S240/mumu/BDT_analysis_samples/final'
formats        	= ['png','pdf','eps']
outDir            = '/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/mass_xsec/lia/FCCee/FinalReport/S240/mumu/BDT_analysis_samples/final/fitresults/'
variables 			= ['mz','mz_zoom','leptonic_recoil_m','leptonic_recoil_m_zoom','leptonic_recoil_m_zoom2', 'leptonic_recoil_m_zoom6']
histoName				= "leptonic_recoil_m_zoom2"
# selection name
sel							= 'sel_Baseline'
#sel              = 'sel10'
# fit mode
# true: 	Signal + background fit
# false:  Signal Only fit
SBMode					= True
# activate the new modelled signal method 
NewModelledSignalMode	= False
modelFunction			= 'DCB'

#fitMode:
#0: default
#1: range fit please set fitRange
#2 sideband fit please set sidebandRange
fitMode 				= 0
fitRange				= ['124', '130']
sidebandRange				= ['120', '124', '130', '140']

# fit function
#fitting fucntions, if SBMode = true, please set sgnFunction and bkgFunction

#sgnFunction			= 'Pol2'
#sgnFunction     = 'Pol3'
sgnFunction     = 'DCB'
bkgFunction			= 'Pol2'
#bkgFunction      = 'Pol3'
#bkgFunction      = 'Pol4'
#bkgFunction      = 'Chebychev4'
#Processes
sgnProcesses   = ['wzp6_ee_mumuH_ecm240']
bkgProcesses    = [
                    'p8_ee_ZZ_ecm240', 
                    'p8_ee_WW_ecm240',
                    "wzp6_ee_mumu_ecm240",
                    "wzp6_ee_tautau_ecm240",
                    #rare backgrounds:
                    "wzp6_egamma_eZ_Zmumu_ecm240",
                    "wzp6_gammae_eZ_Zmumu_ecm240",
                    "wzp6_gaga_mumu_60_ecm240",
                    "wzp6_gaga_tautau_60_ecm240",
                    "wzp6_ee_nuenueZ_ecm240"
                ]
# fitting parameters
# if not set, will use tha default value



