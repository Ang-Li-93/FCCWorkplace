import ROOT

# global parameters
intLumi        = 10.8e+06 #in pb-1
ana_tex        = 'e^{+}e^{-} #rightarrow ZH #rightarrow #mu^{+}#mu^{-} + X'
delphesVersion = '3.4.2'
energy         = 240.0
collider       = 'FCC-ee'
inputDir       = '/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/mass_xsec/lia/FCCee/FinalReport/S240/mumu/BDT_analysis_samples/final/'
#formats        = ['png','pdf']
yaxis          = ['lin','log']
#yaxis          = ['lin']
stacksig       = ['stack','nostack']
#stacksig       = ['stack']
formats        = ['pdf','png','eps','tex']
#yaxis          = ['lin']
outdir         = '/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/mass_xsec/lia/FCCee/FinalReport/S240/mumu/BDT_analysis_samples/plots_reproduce/'

variables = [  #muons
               "leptonic_recoil_m",
               "leptonic_recoil_m_zoom1",
               "leptonic_recoil_m_zoom2",
               "leptonic_recoil_m_zoom3",
               "leptonic_recoil_m_zoom4",
               "leptonic_recoil_m_zoom5",
               "leptonic_recoil_m_zoom6",
               "leptonic_recoil_m_zoom7",
               ]
###Dictonnary with the analysis name as a key, and the list of selections to be plotted for this analysis. The name of the selections should be the same than in the final selection
selections = {}
selections['ZH']   =[ 
                        "sel0",
                        "sel_Baseline",
                        "sel_Baseline_without_mrec",
                        "sel_Baseline_without_mrec_1",
                        "sel_Baseline_without_mrec_2",
                        "sel_Baseline_without_mrec_3",
                        "sel_Baseline_without_mrec_4"
                     ]
extralabel = {}
extralabel['sel0']                            = "Selection: No Selection"
extralabel['sel_Baseline']                    = "Baseline"
extralabel['sel_Baseline_without_mrec']        = ""
extralabel['sel_Baseline_without_mrec_1']        = ""
extralabel['sel_Baseline_without_mrec_2']        = ""
extralabel['sel_Baseline_without_mrec_3']        = ""
extralabel['sel_Baseline_without_mrec_4']        = ""

colors = {}
colors['mumuH'] = ROOT.kRed
colors['tautauH'] = ROOT.kMagenta
colors['nunuH'] = ROOT.kOrange
colors['eeH'] = ROOT.kYellow
colors['qqH'] = ROOT.kSpring
colors['WWmumu'] = ROOT.kBlue+1
colors['ZZ'] = ROOT.kGreen+2
colors['Zqq'] = ROOT.kYellow+2
colors['Zll'] = ROOT.kCyan
colors['eeZ'] = ROOT.kSpring+10
colors['gagatautau'] = ROOT.kViolet+7
colors['gagamumu'] = ROOT.kBlue-8
colors['ZH'] = ROOT.kRed
colors['WW'] = ROOT.kBlue+1
colors['VV'] = ROOT.kGreen+3
colors['rare'] = ROOT.kSpring
colors['Other'] = ROOT.kCyan
plots = {}
plots['ZH'] = {'signal':{'ZH':['wzp6_ee_mumuH_ecm240']},
                 'backgrounds':{
                                'WW':['p8_ee_WW_ecm240'],
                                'ZZ':['p8_ee_ZZ_ecm240'],
                                'Other':[
                                        "wzp6_ee_mumu_ecm240",
                                        #"wzp6_egamma_eZ_Zmumu_ecm240",
                                        #"wzp6_gammae_eZ_Zmumu_ecm240", 
                                        #"wzp6_ee_tautau_ecm240",
                                        #"wzp6_gaga_mumu_60_ecm240",
                                        #"wzp6_gaga_tautau_60_ecm240",
                                        #"wzp6_ee_nuenueZ_ecm240"
                                        ]}
              }
legend = {}
legend['mumuH'] = 'Z(#mu^{-}#mu^{+})H'
legend['tautauH'] = 'Z(#tau^{-}#tau^{+})H'
legend['qqH'] = 'Z(q#bar{q})H'
legend['eeH'] = 'Z(e^{-}e^{+})H'
legend['nunuH'] = 'Z(#nu#bar{#nu})H'
legend['Zqq'] = 'Z#rightarrow q#bar{q}'
legend['Zll'] = 'Z/#gamma#rightarrow #mu^{+}#mu^{-}'
legend['eeZ'] = 'e^{+}(e^{-})Z'
legend['Wmumu'] = 'W^{+}(#bar{#nu}#mu^{+})W^{-}(#nu#mu^{-})'
legend['gagamumu'] = '#gamma#gamma#mu^{-}#mu^{+}'
legend['gagatautau'] = '#gamma#gamma#tau^{-}#tau^{+}'
legend['ZH'] = 'ZH'
legend['WW'] = 'WW'
legend['ZZ'] = 'ZZ'
legend['VV'] = 'VV boson'
legend['rare'] = 'Rare'
legend['Other'] = 'Other Backgrounds'


