import ROOT

# global parameters
intLumi        = 3.0e+06 #in pb-1
ana_tex        = 'e^{+}e^{-} #rightarrow ZH #rightarrow #mu^{+}#mu^{-} + X'
delphesVersion = '3.4.2'
energy         = 365.0
collider       = 'FCC-ee'
inputDir       = '/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/mass_xsec/lia/FCCee/FinalReport/S365/mumu/MVAInputs/final/'
formats        = ['pdf']
yaxis          = ['lin','log']
#yaxis          = ['lin']
stacksig       = ['stack','nostack']
#stacksig       = ['stack']
#formats        = ['pdf']
#yaxis          = ['lin']
outdir         = '/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/mass_xsec/lia/FCCee/FinalReport/S365/mumu/MVAInputs/plots/'

variables = [   #muons
                "leading_zll_lepton_p",
                "leading_zll_lepton_theta",
                "subleading_zll_lepton_p",
                "subleading_zll_lepton_theta",
                #Zed
                "zll_m",
                "zll_p",
                "zll_theta",
                #more control variables
                "zll_leptons_acolinearity",
                "zll_leptons_acoplanarity",
                #Recoil
                "zll_recoil_m",
                #missing Information
                "cosTheta_miss",
                #Higgsstrahlungness
                "H"
               ]
###Dictonnary with the analysis name as a key, and the list of selections to be plotted for this analysis. The name of the selections should be the same than in the final selection
selections = {}
selections['ZH']   =[ 
                     #"noselection",
                     #"sel_Basic",
                     #"sel_Baseline",
                     #"sel_Baseline_pT20",
                     "sel_Basic_pT20"
                     ]

extralabel = {}
extralabel["sel_Basic"]            = "Basic selection"
extralabel["sel_Baseline"]         = "Baseline selection"
extralabel["sel_Baseline_pT20"]    = "Baseline selection, p_{ll} > 20 GeV"
extralabel["sel_Basic_pT20"]       = "Basic selection, p_{ll} > 20 GeV, training"
extralabel["noselection"]          = "No selection"   


colors = {}
colors['mumuH'] = ROOT.kRed
colors['eeH'] = ROOT.kRed
colors['Zmumu'] = ROOT.kCyan
colors['Zee'] = ROOT.kCyan
colors['eeZ'] = ROOT.kSpring+10
colors['WWmumu'] = ROOT.kBlue+1
colors['WWee'] = ROOT.kBlue+1
colors['gagamumu'] = ROOT.kBlue-8
colors['gagaee'] = ROOT.kBlue-8
colors['WW'] = ROOT.kBlue+1
colors['ZZ'] = ROOT.kGreen+2
colors['ttbar'] = ROOT.kOrange+1
colors['nunuH'] = ROOT.kRed+3

plots = {}
plots['ZH'] = {'signal':{'mumuH':['wzp6_ee_mumuH_ecm365']},
               'backgrounds':{
                                #'WW':['p8_ee_WW_ecm365'],
                                'ZZ':['p8_ee_ZZ_ecm365'],
                                'Zmumu':['wzp6_ee_mumu_ecm365'],
                                'eeZ':["wzp6_egamma_eZ_Zmumu_ecm365",
                                     "wzp6_gammae_eZ_Zmumu_ecm365"],
                                'gagamumu':["wzp6_gaga_mumu_60_ecm365"],
                                #'ttbar':["p8_ee_tt_ecm365"],
                                #'nunuH':['wzp6_ee_nunuH_ecm365']
                                }
              }
legend = {}
legend['mumuH'] = 'Z(#mu^{-}#mu^{+})H'
legend['eeH'] = 'Z(e^{-}e^{+})H'
legend['Zmumu'] = 'Z/#gamma#rightarrow #mu^{+}#mu^{-}'
legend['Zee'] = 'Z/#gamma#rightarrow e^{+}e^{-}'
legend['eeZ'] = 'e^{+}(e^{-})#gamma'
legend['WWmumu'] = 'W^{+}(#nu_{#mu}#mu^{+})W^{-}(#bar{#nu}_{#mu}#mu^{-})'
legend['WWee'] = 'W^{+}(#nu_{e}e^{+})W^{-}(#bar{#nu}_{e}e^{-})'
legend['gagamumu'] = '#gamma#gamma#rightarrow#mu^{+}#mu^{-}'
legend['gagaee'] = '#gamma#gamma#rightarrow e^{+}e^{-}'
legend['WW'] = 'W^{+}W^{-}'
legend['ZZ'] = 'ZZ'
legend['ttbar'] = 't#bar{t}'
legend['nunuH'] = '#nu#nuH'


