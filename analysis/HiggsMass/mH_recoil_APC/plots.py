import ROOT

# global parameters
intLumi        = 5.0e+06 #in pb-1
ana_tex        = 'e^{+}e^{-} #rightarrow ZH #rightarrow #mu^{+}#mu^{-} + X'

#ana_tex        = 'e^{+}e^{-} #rightarrow #mu^{+}#mu^{-}'
delphesVersion = '3.4.2'
energy         = 240.0
collider       = 'FCC-ee'
inputDir       = '/eos/home-l/lia/FCCee/mumu/'
#formats        = ['png','pdf']
yaxis          = ['lin','log']
stacksig       = ['stack','nostack']
formats        = ['pdf']
#yaxis          = ['lin']
outdir         = '/eos/home-l/lia/FCCee/mumu/plots/'

#variables = ["SF_kkmc_wzp","z_pt","z_mass","z_MC_pt","z_MC_mass","Gen_pt_mumu","Gen_pt_mumu_025","Gen_mass_mumu"]
#variables = ['leptonic_recoil_m_zoom2']
#variables = ['leptonic_recoil_m_zoom9']
#variables = ['Nmu', 'Nmu_plus', 'Nmu_minus', 'Cz', 'Nz', 'mz','mz_zoom1','mz_zoom2', 'mz_zoom3', 'mz_zoom4', 'mz_zoom5', 'mz_zoom6', 'leptonic_recoil_m','leptonic_recoil_m_zoom1', 'leptonic_recoil_m_zoom2', 'leptonic_recoil_m_zoom3', 'leptonic_recoil_m_zoom4', 'leptonic_recoil_m_zoom5', 'leptonic_recoil_m_zoom6', 'leptonic_recoil_m_zoom7', 'leptonic_recoil_m_zoom8', 'leptonic_recoil_m_zoom9', 'leptonic_recoil_m_zoom10', 'muon_y', 'muon_pT', 'muon_E']
#variables = ["Nmu", "Nmu_plus", "Nmu_minus", 'Cz', 'Nz', 'mz','mz_zoom1','mz_zoom2', 'mz_zoom3', 'mz_zoom4', 'mz_zoom5', 'mz_zoom6', 'leptonic_recoil_m','leptonic_recoil_m_zoom1', 'leptonic_recoil_m_zoom2', 'leptonic_recoil_m_zoom3', 'muon_y', 'muon_pT', 'muon_E']
variables = ["MET_costheta", "Nmu_plus", "Nmu_minus", "Nmu",
              "Cz", "Nz",
              "mz", "mz_zoom1", 'mz_zoom2', 'mz_zoom3', 'mz_zoom4', 'mz_zoom5', 'mz_zoom6', 'mz_zoom7',
              "z_pt", "z_y", "z_p", "z_e",
              'leptonic_recoil_m','leptonic_recoil_m_zoom1', 'leptonic_recoil_m_zoom2', 'leptonic_recoil_m_zoom3',
              'leptonic_recoil_m_zoom4', 'leptonic_recoil_m_zoom5', 'leptonic_recoil_m_zoom6', 'leptonic_recoil_m_zoom7',
              'leptonic_recoil_m_zoom8', 'leptonic_recoil_m_zoom9', 'leptonic_recoil_m_zoom10', 'leptonic_recoil_m_zoom11', 'leptonic_recoil_m_zoom12',
              'muon_y', 'muon_pT', 'muon_p', "muon_costheta", "muon_e", "muon_m",
              "Cz_MC", "Nz_MC",
              "mz_MC", "mz_MC_zoom1", 'mz_MC_zoom2', 'mz_MC_zoom3', 'mz_MC_zoom4', 'mz_MC_zoom5', 'mz_MC_zoom6', 'mz_MC_zoom7',
              "z_MC_pt", "z_MC_y", "z_MC_p", "z_MC_e",
              'leptonic_recoil_m_MC','leptonic_recoil_m_MC_zoom1', 'leptonic_recoil_m_MC_zoom2', 'leptonic_recoil_m_MC_zoom3',
              'leptonic_recoil_m_MC_zoom4', 'leptonic_recoil_m_MC_zoom5', 'leptonic_recoil_m_MC_zoom6', 'leptonic_recoil_m_MC_zoom7',
              'leptonic_recoil_m_MC_zoom8', 'leptonic_recoil_m_MC_zoom9', 'leptonic_recoil_m_MC_zoom10', 'leptonic_recoil_m_MC_zoom11', 'leptonic_recoil_m_MC_zoom12',
              "SF_kkmcp8_wzp6","z_pt","z_mass","z_MC_pt","z_MC_mass","Gen_pt_mumu","Gen_pt_mumu_025","Gen_mass_mumu","Gen_mass_mumu_Z","Gen_pt_ZH","Gen_pt_ZH_025","Gen_mass_ZH"]

###Dictonnary with the analysis name as a key, and the list of selections to be plotted for this analysis. The name of the selections should be the same than in the final selection


selections = {}
#selections['ZH']   = ["sel0","sel1","sel2"]
#selections['ZH_2'] = ["sel0","sel1","sel2"]
#selections['ZH']   = ["sel1"]
#selections['ZH']   = ["sel0", "sel1", "sel2", "sel3", "sel4", "sel5", 
#                      "sel6", "sel7", "sel8", "sel9", "sel10", "sel11",
#                      "sel12", "sel13", "sel14","sel10", "sel11", "sel12", 
#                      "sel13", "sel14","sel15", "sel16", "sel17", "sel18", 
#                      "sel19","sel20", "sel21", "sel22", "sel23",
#                      "sel24","sel25", "sel26", "sel27", "sel28", "sel29"
#                      #"MC_sel1", "MC_sel2", "MC_sel3", "MC_sel4", "MC_sel5", 
#                      #"MC_sel6", "MC_sel7", "MC_sel8", "MC_sel9", "MC_sel10", "MC_sel11",
#                      #"MC_sel12", "MC_sel13", "MC_sel14","MC_sel10", "MC_sel11", "MC_sel12", 
#                      #"MC_sel13", "MC_sel14","MC_sel15", "MC_sel16", "MC_sel17", "MC_sel18", 
#                      #"MC_sel19","MC_sel20", "MC_sel21", "MC_sel22", "MC_sel23",
#                      #"MC_sel24","MC_sel25", "MC_sel26", "MC_sel27", "MC_sel28", "MC_sel29"
#                      ]
#selections['ZH_P']   = ["sel0", "sel1", "sel2", "sel3", "sel4", "sel5", 
#                      "sel6", "sel7", "sel8", "sel9", "sel10", "sel11",
#                      "sel12", "sel13", "sel14","sel10", "sel11", "sel12", 
#                      "sel13", "sel14","sel15", "sel16", "sel17", "sel18", 
#                      "sel19","sel20", "sel21", "sel22", "sel23",
#                      "sel24","sel25", "sel26", "sel27", "sel28", "sel29",
#                      "MC_sel1", "MC_sel2", "MC_sel3", "MC_sel4", "MC_sel5", 
#                      "MC_sel6", "MC_sel7", "MC_sel8", "MC_sel9", "MC_sel10", "MC_sel11",
#                      "MC_sel12", "MC_sel13", "MC_sel14","MC_sel10", "MC_sel11", "MC_sel12", 
#                      "MC_sel13", "MC_sel14","MC_sel15", "MC_sel16", "MC_sel17", "MC_sel18", 
#                      "MC_sel19","MC_sel20", "MC_sel21", "MC_sel22", "MC_sel23",
#                      "MC_sel24","MC_sel25", "MC_sel26", "MC_sel27", "MC_sel28", "MC_sel29"
#                      ]
#
#selections['ZH_W']   = [#"sel0", "sel1", "sel2", "sel3", "sel4", "sel5", 
#                      #"sel6", "sel7", "sel8", "sel9", "sel10", "sel11",
#                      #"sel12", "sel13", "sel14","sel10", "sel11", "sel12", 
#                      #"sel13", "sel14","sel15", "sel16", "sel17", "sel18", 
#                      #"sel19","sel20", "sel21", "sel22", "sel23",
#                      #"sel24","sel25", "sel26", "sel27", "sel28", "sel29"
#                      "MC_sel1", "MC_sel2", "MC_sel3", "MC_sel4", "MC_sel5", 
#                      "MC_sel6", "MC_sel7", "MC_sel8", "MC_sel9", "MC_sel10", "MC_sel11",
#                      "MC_sel12", "MC_sel13", "MC_sel14","MC_sel10", "MC_sel11", "MC_sel12", 
#                      "MC_sel13", "MC_sel14","MC_sel15", "MC_sel16", "MC_sel17", "MC_sel18", 
#                      "MC_sel19","MC_sel20", "MC_sel21", "MC_sel22", "MC_sel23",
#                      "MC_sel24","MC_sel25", "MC_sel26", "MC_sel27", "MC_sel28", "MC_sel29"
#                      ]
selections['ee_mumu'] = ['sel0',"Gen_mass_220","sel23"]


#selections['zh']   = ["sel13"]
extralabel = {}
#extralabel['sel0'] = "Selection: N_{Z} = 1"
#extralabel['sel1'] = "Selection: N_{Z} = 1; 80 GeV < m_{Z} < 100 GeV"
extralabel['sel0'] = "selection: No Selection"
extralabel["Gen_mass_220"] = "gen_mass > 220"

extralabel['sel1'] = "sel.1"
extralabel['sel2'] = "sel.2"
extralabel['sel3'] = "sel.3"
extralabel['sel4'] = "sel.4"
extralabel['sel5'] = "sel.5"
extralabel['sel6'] = "sel.6"
extralabel['sel7'] = "sel.7"
extralabel['sel8'] = "sel.8"
extralabel['sel9'] = "sel.9"
extralabel['sel10'] = "Sel.10"
extralabel['sel11'] = "Sel.11"
extralabel['sel12'] = "Sel.12"
extralabel['sel13'] = "Sel.13"
extralabel['sel14'] = "Sel.14"
extralabel['sel15'] = "Sel.15"
extralabel['sel16'] = "Sel.16"
extralabel['sel17'] = "Sel.17"
extralabel['sel18'] = "Sel.18"
extralabel['sel19'] = "Sel.19"
extralabel['sel20'] = "Sel.20"
extralabel['sel21'] = "Sel.21"
extralabel['sel22'] = "Sel.22"
extralabel['sel23'] = "Sel.23"
extralabel['sel24'] = "Sel.24"
extralabel['sel25'] = "Sel.25"
extralabel['sel26'] = "Sel.26"
extralabel['sel27'] = "Sel.27"
extralabel['sel28'] = "Sel.28"
extralabel['sel29'] = "Sel.29"

extralabel['MC_sel1'] = "MC_Sel.1"
extralabel['MC_sel2'] = "MC_Sel.2"
extralabel['MC_sel3'] = "MC_Sel.3"
extralabel['MC_sel4'] = "MC_Sel.4"
extralabel['MC_sel5'] = "MC_Sel.5"
extralabel['MC_sel6'] = "MC_Sel.6"
extralabel['MC_sel7'] = "MC_Sel.7"
extralabel['MC_sel8'] = "MC_Sel.8"
extralabel['MC_sel9'] = "MC_Sel.9"
extralabel['MC_sel10'] = "MC_Sel.10"
extralabel['MC_sel11'] = "MC_Sel.11"
extralabel['MC_sel12'] = "MC_Sel.12"
extralabel['MC_sel13'] = "MC_Sel.13"
extralabel['MC_sel14'] = "MC_Sel.14"
extralabel['MC_sel15'] = "MC_Sel.15"
extralabel['MC_sel16'] = "MC_Sel.16"
extralabel['MC_sel17'] = "MC_Sel.17"
extralabel['MC_sel18'] = "MC_Sel.18"
extralabel['MC_sel19'] = "MC_Sel.19"
extralabel['MC_sel20'] = "MC_Sel.20"
extralabel['MC_sel21'] = "MC_Sel.21"
extralabel['MC_sel22'] = "MC_Sel.22"
extralabel['MC_sel23'] = "MC_Sel.23"
extralabel['MC_sel24'] = "MC_Sel.24"
extralabel['MC_sel25'] = "MC_Sel.25"
extralabel['MC_sel26'] = "MC_Sel.26"
extralabel['MC_sel27'] = "MC_Sel.27"
extralabel['MC_sel28'] = "MC_Sel.28"
extralabel['MC_sel29'] = "MC_Sel.29"



#extralabel['sel1'] = "Selection: N_{Z} = 1; 73 GeV < m_{Z} < 120 GeV"
#extralabel['sel2'] = "Selection: N_{Z} = 1; 80 GeV < m_{Z} < 110 GeV"
#extralabel['sel3'] = "Selection: N_{Z} = 1; 80 GeV < m_{Z} < 100 GeV"
#extralabel['sel4'] = "Selection: N_{Z} = 1; 80 GeV < m_{Z} < 100 GeV; 10 GeV < p_{T}^Z < 70 GeV"
#extralabel['sel6'] = "Selection: N_{Z} = 1; 80 GeV < m_{Z} < 100 GeV; 10 GeV < p_{T}^Z < 70 GeV; 120 GeV < m_{recoil} < 140 GeV"
#extralabel['sel7'] = "Selection: 8"
#extralabel['sel8'] = "Selection: 9"
#extralabel['sel9'] = "Selection: 10"
#extralabel['sel10'] = "Selection: 11"
#extralabel['sel11'] = "Selection: 12"
#extralabel['sel12'] = "Selection: 13"
#extralabel['sel13'] = "Selection: 14"
#extralabel['sel14'] = "Selection: 15"
#extralabel['sel15'] = "Selection: 16"
#extralabel['sel1'] = "Selection: N_{Z} = 1; 80 GeV < m_{Z} < 100 GeV; p_{T #muon} > 20 GeV; #theta_{#mu^{+}#mu^{-}} < 175^{#degree}"
#extralabel['sel2'] = "Selection: N_{Z} = 1; 86 GeV < m_{Z} < 96 GeV"
#extralabel['sel3'] = "Selection: N_{Z} = 1; new"

colors = {}
colors['mumuH_reweighted'] = ROOT.kBlue
colors['mumuH'] = ROOT.kRed
colors['tautauH'] = ROOT.kMagenta
colors['nunuH'] = ROOT.kOrange
colors['eeH'] = ROOT.kYellow
colors['qqH'] = ROOT.kSpring
colors['WWmumu'] = ROOT.kBlue+1
colors['ZZ'] = ROOT.kGreen+2
colors['Zqq'] = ROOT.kYellow+2
colors['Zll'] = ROOT.kCyan
colors['egamma'] = ROOT.kSpring+10
colors['gagatautau'] = ROOT.kViolet+7
colors['gagamumu'] = ROOT.kBlue-8
colors['ZH_wzp6'] = ROOT.kRed
colors['ZH'] = ROOT.kRed
colors['WW'] = ROOT.kBlue+1
colors['VV'] = ROOT.kGreen+3
colors['KKMC'] = ROOT.kRed 
colors['Whizard'] = ROOT.kBlue+1

plots = {}
#plots['ZH'] = {'signal':{'nunuH':['wzp6_ee_nunuH_ecm240'],
#                          'eeH':['wzp6_ee_eeH_ecm240'],
#                          'tautauH':['wzp6_ee_tautauH_ecm240'],
#                          'qqH':['wzp6_ee_qqH_ecm240'],
#                          'mumuH':['wzp6_ee_mumuH_ecm240']},
#                'backgrounds':{'gagatautau':['wzp6_gaga_tautau_60_ecm240'],
#                                'gagamumu':['wzp6_gaga_mumu_60_ecm240'],
#                                'egamma':['wzp6_gammae_eZ_Zmumu_ecm240', 'wzp6_egamma_eZ_Zmumu_ecm240'],
#                                 'Zqq':['p8_ee_Zqq_ecm240'],
#                                'WWmumu':['p8_ee_WW_mumu_ecm240'],
#                                'Zll':['p8_ee_Zll_ecm240'],
#                                'ZZ':['p8_ee_ZZ_ecm240']}
#            }
#
#plots['ZH_P'] = {'signal':{'ZH':['p8_ee_ZH_ecm240']},
#                  'backgrounds':{'gagatautau':['wzp6_gaga_tautau_60_ecm240'],
#                                  'gagamumu':['wzp6_gaga_mumu_60_ecm240'],
#                                  'egamma':['wzp6_gammae_eZ_Zmumu_ecm240', 'wzp6_egamma_eZ_Zmumu_ecm240'],
#                                  'Zqq':['p8_ee_Zqq_ecm240'],
#                                  'WWmumu':['p8_ee_WW_mumu_ecm240'],
#                                  'Zll':['p8_ee_Zll_ecm240'],
#                                  'ZZ':['p8_ee_ZZ_ecm240']}
#            }
#plots['ZH_W'] = {'signal':{'ZH_wzp6':['wzp6_ee_mumuH_ecm240','wzp6_ee_eeH_ecm240','wzp6_ee_tautauH_ecm240','wzp6_ee_qqH_ecm240','wzp6_ee_nunuH_ecm240']},
#                  'backgrounds':{'gagatautau':['wzp6_gaga_tautau_60_ecm240'],
#                                  'gagamumu':['wzp6_gaga_mumu_60_ecm240'],
#                                  'egamma':['wzp6_gammae_eZ_Zmumu_ecm240', 'wzp6_egamma_eZ_Zmumu_ecm240'],
#                                  'Zqq':['p8_ee_Zqq_ecm240'],
#                                  'WWmumu':['p8_ee_WW_mumu_ecm240'],
#                                  'Zll':['p8_ee_Zll_ecm240'],
#                                  'ZZ':['p8_ee_ZZ_ecm240']}
#            }
#
#plots['ee_mumu'] = {'signal':{'KKMC':['kkmcp8_ee_mumu_noFSR_ecm240']},
#                  'backgrounds':{'Whizard':['wzp6_ee_mumu_noFSR_ecm240']}
#            }
plots['ee_mumu'] = {'signal':{'mumuH_reweighted':['wzp6_ee_mumuH_ecm240_reweighted']},
                   'backgrounds':{'mumuH':['wzp6_ee_mumuH_ecm240']}
    }
#plots['ZH'] = {'signal':{'ZH':['p8_ee_ZH_ecm240']},
#               'backgrounds':{'WW':['p8_ee_WW_ecm240'],
#                              'ZZ':['p8_ee_ZZ_ecm240']}
#           }
#plots['ZH'] = {'signal':{'ZH':['p8_noBES_ee_ZH_ecm240']},
#                'backgrounds':{'WW':['p8_noBES_ee_WW_ecm240'],
#                                'ZZ':['p8_noBES_ee_ZZ_ecm240']}
#            }
#plots['ZH'] = {'signal':{'ZH':['p8_ee_ZH_ecm240']},
#               'backgrounds':{'WW':['p8_ee_WW_mumu_ecm240'],
#                               'ZZ':['p8_ee_ZZ_ecm240']}
#            }
#plots['ZH'] = {'signal':{'ZH':['wzp6_ee_mumuH_ecm240_v2']}
#
#    }
#plots['ZH'] = {'signal':{'ZH':['p8_ee_ZH_ecm240']},
#                'backgrounds':{'WW':['p8_ee_WW_mumu_ecm240'],
#                                'Zqq':['p8_ee_Zqq_ecm240'],
#                                'Zll':['p8_ee_Zll_ecm240'],
#                                'ZZ':['p8_ee_ZZ_ecm240']}
#            }
#plots['ZH_2'] = {'signal':{'ZH':['p8_ee_ZH_ecm240']},
#                 'backgrounds':{'VV':['p8_ee_WW_ecm240','p8_ee_ZZ_ecm240']}
#             }
legend = {}
legend['mumuH_reweighted'] = 'Z(#mu^{-}#mu^{+})H reweighted'
legend['mumuH'] = 'Z(#mu^{-}#mu^{+})H'
legend['tautauH'] = 'Z(#tau^{-}#tau^{+})H'
legend['qqH'] = 'Z(q#bar{q})H'
legend['eeH'] = 'Z(e^{-}e^{+})H'
legend['nunuH'] = 'Z(#nu#bar{#nu})H'
legend['Zqq'] = 'Z#rightarrow q#bar{q}'
legend['Zll'] = 'Z#rightarrow l#bar{l}'
legend['egamma'] = 'eeZ'
legend['WWmumu'] = 'W^{+}(#bar{#nu}#mu^{+})W^{-}(#nu#mu^{-})'
legend['gagamumu'] = '#gamma#gamma#mu^{-}#mu^{+}'
legend['gagatautau'] = '#gamma#gamma#tau^{-}#tau^{+}'
legend['ZH_wzp6'] = 'sum ZH wzp6'
legend['KKMC'] = 'KKMC'
legend['Whizard'] = 'Whizard'
legend['ZH'] = 'ZH'
legend['WW'] = 'WW'
legend['ZZ'] = 'ZZ'
legend['VV'] = 'VV boson'


scaleSig = 1.0

