import ROOT

# global parameters
intLumi        = 7.2e+06 #in pb-1
ana_tex        = 'e^{+}e^{-} #rightarrow ZH #rightarrow #mu^{+}#mu^{-} + Invisible'
delphesVersion = '3.4.2'
energy         = 240.0
collider       = 'FCC-ee'
inputDir       = '/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/HiggsInvisible/lia/firstlook/final/'
yaxis          = ['lin','log']
stacksig       = ['stack','nostack']
formats        = ['pdf']
outdir         = '/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/HiggsInvisible/lia/firstlook/plots/'

variables = [  #muons
                "muons_p",  
                "muons_theta",
                "muons_phi",
                "muons_no", 
            
                #electrons
                "electrons_p",
                "electrons_theta",
                "electrons_phi",
                "electrons_no",

                #Z
                "Z_p",
                "Z_m",
                "Z_theta",
                "Z_phi",

                #recoil
                "Z_recoil_m",
                "Z_recoil_p",
                "Z_recoil_theta",
                "Z_recoil_phi",

                #missing
                "missing_mass",
                "missing_e",
                "missing_p",
                "missing_theta",
                "missing_phi",
                "missing_px",
                "missing_py",
                "missing_pz",

                #visible
                "visible_mass",
                "visible_e",
                "visible_p",
                "visible_theta",
                "visible_phi",
                "visible_px",
                "visible_py",
                "visible_pz",

                "ZHChi2",

                "leps_iso" 
               ]
###Dictonnary with the analysis name as a key, and the list of selections to be plotted for this analysis. The name of the selections should be the same than in the final selection
selections = {}
selections['mumuH']   =[ 
                     "sel0", 
                     "sel1",
                     "sel2",
                     "sel3",
                     "sel4",
                     "sel5",
                     ]
selections['mumuH_HZZ']   =[ 
                     "sel0", 
                     "sel1",
                     "sel2",
                     "sel3",
                     "sel4",
                     "sel5", 
                     ]

extralabel = {}
extralabel['sel0']    = "Selection: No Selection"
extralabel["sel1"]    = "sel1"
extralabel["sel2"]    = "sel2"
extralabel["sel3"]    = "sel3"
extralabel["sel4"]    = "sel4"
extralabel["sel5"]    = "sel5"

colors = {}
colors['mumuH_HZZ'] = ROOT.kBlue+2
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

plots = {}
plots['mumuH'] = {'signal':{'mumuH':['wzp6_ee_mumuH_ecm240']},
               'backgrounds':{'eeZ':["wzp6_egamma_eZ_Zmumu_ecm240",
                                     "wzp6_gammae_eZ_Zmumu_ecm240"],
                                'WW':['p8_ee_WW_ecm240'],
                                'Zll':['wzp6_ee_mumu_ecm240'],
                                'ZZ':['p8_ee_ZZ_ecm240'],
                                'rare':["wzp6_ee_tautau_ecm240",
                                        "wzp6_gaga_mumu_60_ecm240",
                                        "wzp6_gaga_tautau_60_ecm240",
                                        "wzp6_ee_nuenueZ_ecm240"
                                        ]}
              }
plots['mumuH_HZZ'] = {'signal':{'mumuH_HZZ':['wzp6_ee_mumuH_HZZ_ecm240']},
                        'backgrounds':{'mumuH':["wzp6_ee_mumuH_ecm240"]}
              }
legend = {}
legend['mumuH_HZZ'] = 'Z(#mu^{-}#mu^{+})H(ZZ)'
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
legend['WW'] = 'W^{+}W^{-}'
legend['ZZ'] = 'ZZ'
legend['VV'] = 'VV boson'
legend['rare'] = 'Rare'


