import sys
import argparse
import re
import os
import math
import copy
import ROOT
import ctypes

from re import search
from ROOT import *
# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
def removekey(d, key):
  r = dict(d)
  del r[key]
  return r

# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
def mapHistos(Var,Sel,Label):
  print ('run plots for var:{}     label:{}     selection:{}'.format(Var,Label,Sel))
  #signals=processes[label]['signal']
  #backgrounds=processes[label]['backgrounds']

  histos = {}
  for keygroup in processes[label]:
    histos[keygroup]={}
    for channel in processes[label][keygroup]:
      histos[keygroup][channel]=[] 
      for file in processes[label][keygroup][channel]:
        fin=os.path.join(baseDir, file+"_"+Sel+"_histo.root")
        #print(fin)
        if not os.path.isfile(fin):
          print ('file {} does not exist, skip'.format(fin))
        else:
          tf=ROOT.TFile(fin)
          h=tf.Get(var)
          hh = copy.deepcopy(h)
          #print(hh.Integral())
          hh.Scale(intLumi)
          #print(hh.Integral())
          if len(histos[keygroup][channel])==0:
            histos[keygroup][channel].append(hh)
          else:
            hh.Add(histos[keygroup][channel][0])
            histos[keygroup][channel][0]=hh
  for keygroup in histos:
    for channel in histos[keygroup]:
      if len(histos[keygroup][channel])==0:
        histos[keygroup]=removekey(histos[keygroup],channel)

  return histos
# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
def Count(Histos,Variable,Label,Selection):
  
  
  print("------------------------------------------------------------------------------------ ")
  print("var:{}     label:{}     selection:{}".format(Variable,Label,Selection))
  print("------------------------------------------------------------------------------------ ")
  print('{:<40s} {:>10s} {:>10s} {:>10s}'.format('Process','Yield','Error','Entries'))
  print("------------------------------------------------------------------------------------ ")
  #print(len(histos))
  S=0;
  B=0;
  for keygroup in Histos:
    print("data group:     {}".format(keygroup))
    yield_total=0.0
    Error_total=0.0
    Entries_total=0.0
    for channel in Histos[keygroup]:
      error_tmp = ctypes.c_double()
      #print(Histos[keygroup][channel])
      integral = Histos[keygroup][channel][0].IntegralAndError(1,Histos[keygroup][channel][0].GetNbinsX(),error_tmp,"")
      #print(error_tmp)
      error = error_tmp.value
      entries = Histos[keygroup][channel][0].GetEntries()
      #print('{:15} {:.1f} {:.1f}'.format(process_list[k],h.GetBinContent(3),h.GetBinError(3)))
      print('{:<40s} {:>10.1f} {:>10.1f} {:>10.0f}'.format(channel,integral,error,entries))
      yield_total+=integral
      Error_total+=error
      Entries_total+=entries
    if (keygroup=='signal'):
      S = yield_total
    elif ((keygroup=='backgrounds')):
      B = yield_total
    print("------------------------------------------------------------------------------------ ")
    print('{:<40s} {:>10.1f} {:>10.1f} {:>10.0f}'.format('Total_'+keygroup,yield_total,Error_total,Entries_total))
    print("------------------------------------------------------------------------------------ ")
  print('{:<40s} {:>10.1f}'.format('Significance S/sqrt(S+B)', S/math.sqrt(S+B)))
  print("")
# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
if __name__ == "__main__":
  #var = 'Nz'
  var = 'leptonic_recoil_m_zoom5'
  #var = 'mz'
  #var = 'zed_leptonic_recoil_m'
  baseDir = "/eos/user/l/lia/FCCee/MVA/trainedNtuples/final"
  #baseDir = "/eos/user/l/lia/FCCee/MVA/flatNtuples_stage2/final"
  #process_list=['wzp6_gaga_mumu_60_ecm240','wzp6_gaga_tautau_60_ecm240','wzp6_gammae_eZ_Zmumu_ecm240','wzp6_egamma_eZ_Zmumu_ecm240','p8_ee_Zqq_ecm240','p8_ee_Zll_ecm240','p8_ee_ZZ_ecm240','p8_ee_WW_mumu_ecm240','wzp6_ee_mumuH_ecm240','wzp6_ee_tautauH_ecm240','wzp6_ee_qqH_ecm240','wzp6_ee_nunuH_ecm240','wzp6_ee_eeH_ecm240']
  intLumi        = 5.0e+06 #in pb-1
  
  selections         = [#"sel0", 
                        "sel0_MRecoil_Mll_73_120_pTll_05",                    
                        "sel0_MRecoil_Mll_73_120_pTll_05_costhetamiss",
                       ]
  processes = {}
  processes['ZH'] = {'signal':{'mumuH':['wzp6_ee_mumuH_ecm240']},
                     'backgrounds':{'eeZ':["wzp6_egamma_eZ_Zmumu_ecm240",
                                           "wzp6_gammae_eZ_Zmumu_ecm240"],
                                    'WWmumu':['p8_ee_WW_mumu_ecm240'],
                                    'ZZ':['p8_ee_ZZ_ecm240'],
                                    'Zll':['wzp6_ee_mumu_ecm240']}
                    }
  #iterProcess = iter(process_list)
  iterSelection = iter(selections)
  for label, process in processes.items():
    for sel in selections:
      histo=mapHistos(var,sel,label)
      Count(histo,var,label,sel)

