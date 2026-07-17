import ROOT

# global parameters
intLumi        = 10.8e+06 #in pb-1
ana_tex        = 'e^{+}e^{-} #rightarrow ZH #rightarrow #mu^{+}#mu^{-} + Invisible'
delphesVersion = '3.4.2'
energy         = 240.0
collider       = 'FCC-ee'
inputDir       = '/afs/cern.ch/work/l/lia/private/FCC/FCCWorkplace/outputs_HInvjj/final/'
yaxis          = ['lin']
stacksig       = ['nostack']
#stacksig       = ['nostack']
formats        = ['pdf','png']
outdir         = '/afs/cern.ch/work/l/lia/private/FCC/FCCWorkplace/outputs_HInvjj/plots_last/'

variables = [ 
    "jets_pt",
    "ZBosonPt",
    "ZBosonMass",
    "recoil_M",
    "Z_MC_m",
    "Z_MC_m_large",
    "Z_MC_p",
    "Z_MC_no",
    "Z_MC_GenID"
               ]
###Dictonnary with the analysis name as a key, and the list of selections to be plotted for this analysis. The name of the selections should be the same than in the final selection
selections = {}
selections['mumuH']   =[ 
                     "sel0_NoCuts",
                     "sel2_mZCut"
                     ]

extralabel = {}
extralabel['sel0_NoCuts'] = "Selection: No Cuts"
extralabel['sel2_mZCut']  = "Selection: 60 < m_{Z} < 100 GeV"
extralabel['NoSel']    = "Selection: No Selection"
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

colors['mumuH_HZZ4nu'] = ROOT.kRed
colors['nunuH_HZZ_mumununu'] = ROOT.kBlue
colors['nunuH_HWW_munumunu'] = ROOT.kGreen
colors["output_wzp6"] = ROOT.kRed
colors["output_p8"] = ROOT.kBlue

plots = {}
plots['mumuH'] = {'signal':{'output_wzp6':['output_wzp6']},
                  'backgrounds':{'output_p8':["output_p8"]
                                 }
                }
legend = {}

legend['output_wzp6'] = 'wzp6'
legend['output_p8'] = 'p8'
legend['mumuH_HZZ4nu'] = 'Z(#mu^{-}#mu^{+})H(4#nu)'
legend['nunuH_HZZ_mumununu'] = 'Z(#nu#bar{#nu})H(ZZ#rightarrow#mu^{-}#mu^{+}#nu#bar{#nu})'
legend['nunuH_HWW_munumunu'] = 'Z(#nu#bar{#nu})H(WW#rightarrow#mu^{-}#bar{#nu}#mu^{+}#nu)'


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


