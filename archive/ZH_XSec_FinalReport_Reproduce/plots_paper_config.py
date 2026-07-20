import ROOT

# global parameters
intLumi        = 10.8e+06 #in pb-1
ana_tex        = 'e^{+}e^{-} #rightarrow ZH #rightarrow #mu^{+}#mu^{-} + X'
delphesVersion = '3.4.2'
energy         = 240.0
collider       = 'FCC-ee'
inputDir       = '/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/mass_xsec/lia/FCCee/FinalReport/S240//mumu/BDT_analysis_samples/final/'
#formats        = ['png','pdf']
#yaxis          = ['lin','log']
#stacksig       = ['stack','nostack']
formats        = ['pdf']
yaxis          = ['lin']
stacksig       = ['stack']
outdir         = '/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/mass_xsec/lia/FCCee/FinalReport/S240//mumu/BDT_analysis_samples/plots_reproduce/'

#variables = ["Nmu", "Nmu_plus", "Nmu_minus", 'Cz', 'Nz', 'mz','mz_zoom1','mz_zoom2', 'mz_zoom3', 'mz_zoom4', 'mz_zoom5', 'mz_zoom6', 'leptonic_recoil_m','leptonic_recoil_m_zoom1', 'leptonic_recoil_m_zoom2', 'leptonic_recoil_m_zoom3', 'leptonic_recoil_m_zoom4', 'leptonic_recoil_m_zoom5', 'leptonic_recoil_m_zoom6', 'leptonic_recoil_m_zoom7', 'leptonic_recoil_m_zoom8', 'leptonic_recoil_m_zoom9', 'muon_y', 'muon_pT', 'muon_E']
#variables = ["Nmu", "Nmu_plus", "Nmu_minus", 'Cz', 'Nz', 'mz','mz_zoom1','mz_zoom2', 'mz_zoom3', 'mz_zoom4', 'mz_zoom5', 'mz_zoom6', 'leptonic_recoil_m','leptonic_recoil_m_zoom1', 'leptonic_recoil_m_zoom2', 'leptonic_recoil_m_zoom3', 'muon_y', 'muon_pT', 'muon_E']
#variables = ['leptonic_recoil_m_zoom9']
variables = ['leptonic_recoil_m_zoom7']
###Dictonnary with the analysis name as a key, and the list of selections to be plotted for this analysis. The name of the selections should be the same than in the final selection
selections = {}
#selections['ZH']   = ["sel0","sel1","sel2"]
#selections['ZH_2'] = ["sel0","sel1","sel2"]
#selections['ZH']   = ["sel1"]
#selections['ZH']   = ["sel0", "sel1", "sel2", "sel3", "sel4", "sel5", "sel6", "sel7", "sel8", "sel9", "sel10", "sel11", "sel12", "sel13"]
selections['ZH']   = ["sel_Baseline",
                        "sel_Baseline_without_mrec",
                        "sel_Baseline_without_mrec_1",
                        "sel_Baseline_without_mrec_2",
                        "sel_Baseline_without_mrec_3",
                        "sel_Baseline_without_mrec_4",
                        "sel_Baseline_without_mrec_5"
                     ]
extralabel = {}
extralabel['sel_Baseline'] = " "
extralabel['sel_Baseline_without_mrec'] = " "
extralabel['sel_Baseline_without_mrec_1'] = " "
extralabel['sel_Baseline_without_mrec_2'] = " "
extralabel['sel_Baseline_without_mrec_3'] = " "
extralabel['sel_Baseline_without_mrec_4'] = " "
extralabel['sel_Baseline_without_mrec_5'] = " "
colors = {}
colors['ZH'] = ROOT.kRed
colors['WW'] = ROOT.kBlue+1
colors['ZZ'] = ROOT.kGreen+2
colors['VV'] = ROOT.kGreen+3
colors['Other'] = ROOT.kCyan
plots = {}
#plots['ZH'] = {'signal':{'ZH':['p8_ee_ZH_ecm240']},
#               'backgrounds':{'WW':['p8_ee_WW_mumu_ecm240'],
#                              'ZZ':['p8_ee_ZZ_ecm240']}
#           }
plots['ZH'] = {'signal':{'ZH':['wzp6_ee_mumuH_ecm240']},
               'backgrounds':{
                              'Other':[
                                        "wzp6_ee_mumu_ecm240",
                                        "wzp6_ee_tautau_ecm240",
                                        #rare backgrounds:
                                        "wzp6_egamma_eZ_Zmumu_ecm240",
                                        "wzp6_gammae_eZ_Zmumu_ecm240",
                                        "wzp6_gaga_mumu_60_ecm240",
                                        "wzp6_gaga_tautau_60_ecm240",
                                        "wzp6_ee_nuenueZ_ecm240"
                                        ],
                               'WW':['p8_ee_WW_ecm240'],
                               'ZZ':['p8_ee_ZZ_ecm240']
                          }
            }
               #plots['ZH'] = {'signal':{'ZH':['p8_ee_ZH_ecm240']},
#							'backgrounds':{}
#		}



#plots['ZH_2'] = {'signal':{'ZH':['p8_ee_ZH_ecm240']},
#                 'backgrounds':{'VV':['p8_ee_WW_ecm240','p8_ee_ZZ_ecm240']}
#             }

legend = {}
legend['ZH'] = 'ZH'
legend['WW'] = 'WW'
legend['ZZ'] = 'ZZ'
legend['VV'] = 'VV boson'
legend['Other'] = 'Other Backgrounds'
