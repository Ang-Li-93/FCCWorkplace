import ROOT
import sys, os, argparse
import uproot
import awkward as ak
import json
import numpy as np
import math
import matplotlib.pyplot as plt
from particle import literals as lp
import pandas as pd
import glob
from sklearn.model_selection import train_test_split
#Local code
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))  # Paper root
from leptonic_training_config import make
import training_utils as ut

def run(channel, modes, n_folds, stage):
  loc, train_vars, mode_names, _, _ = make(365, channel)
  #xsec, from http://fcc-physics-events.web.cern.ch/fcc-physics-events/Delphesevents_spring2021_IDEA.php
  xsec = {}
  #xsec["mumuH"]   = 0.0067643
  #xsec["WWmumu"]  = 0.25792
  #xsec["ZZ"]      = 1.35899
  #xsec["Zll"]     = 5.288
  #xsec["eeZ"]     = 0.10368
  procDictLocal = {
    "wzp6_gaga_mumu_60_ecm365": {"crossSection": 2.8456143E+03 / 1000, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_gaga_ee_60_ecm365": {"crossSection": 2.0195309E+03 / 1000, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_egamma_eZ_Zmumu_ecm365": {"crossSection": 1.4001117E+02 / 1000, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_egamma_eZ_Zee_ecm365": {"crossSection": 7.0051377E+01 / 1000, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_ee_tautau_ecm365": {"crossSection": 2.0170420E+03 / 1000, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_ee_nuenueZ_ecm365": {"crossSection": 1.2632582E+02 / 1000, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_ee_mumu_ecm365": {"crossSection": 2.2881408E+03 / 1000, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_ee_ee_Mee_30_150_ecm365": {"crossSection": 1.5269275E+03 / 1000, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_gammae_eZ_Zmumu_ecm365": {"crossSection": 1.4027678E+02 / 1000, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_gammae_eZ_Zee_ecm365": {"crossSection": 7.0240520E+01 / 1000, "kfactor": 1.0, "matchingEfficiency": 1.0},
    "wzp6_gaga_tautau_60_ecm365": {"crossSection": 1.5388183E+03 / 1000, "kfactor": 1.0, "matchingEfficiency": 1.0},
  }



  if channel == 'mumu':
    sigs = ["wzp6_ee_mumuH_ecm365"]
    bkgs = [#"p8_ee_WW_ecm365", 
            "p8_ee_ZZ_ecm365",
            "wzp6_ee_mumu_ecm365",
            #"wzp6_ee_tautau_ecm365",
            "wzp6_egamma_eZ_Zmumu_ecm365",
            "wzp6_gammae_eZ_Zmumu_ecm365",
            "wzp6_gaga_mumu_60_ecm365",
            #"wzp6_gaga_tautau_60_ecm365",
            #"wzp6_ee_nunuH_ecm365",
            #"wzp6_ee_nuenueZ_ecm365"
            ]
  elif channel == 'ee':
    sigs = ["wzp6_ee_eeH_ecm365"]
    bkgs = [#"p8_ee_WW_ecm365",
            #"p8_ee_ZZ_ecm365",
            #"wzp6_ee_ee_Mee_30_150_ecm365",
            #"wzp6_ee_tautau_ecm365",
            #"wzp6_egamma_eZ_Zee_ecm365",
            #"wzp6_gammae_eZ_Zee_ecm365",
            "wzp6_gaga_ee_60_ecm365",
            #"wzp6_gaga_tautau_60_ecm365",
            #"wzp6_ee_nunuH_ecm365",
            #"wzp6_ee_nuenueZ_ecm365"
            ]
  else:
    print("Channel doesn't exist, please choose 'ee' or 'mumu'")
    exit(0)
  
  # producer on SDCC: python condor/submit_stage1.py S365/<flavor>/stage1_training_estimate.py --stage training_estimation
  data_path = os.path.join(loc.EOS, "training_estimation")
  print(f"-->Data path: {data_path}")
  files = {}
  df = {}
  N_events = {}
  eff = {}
  N_BDT_inputs = {}
  vars_list = train_vars.copy()
  df0 = {} 
  df1 = {} 
  frac = {}
  
  procFile = "FCCee_procDict_winter2023_IDEA.json"
  # FCCDICTSDIR may be a colon-separated list in the key4hep+FCCAnalyses env
  for _d in os.getenv('FCCDICTSDIR', '/cvmfs/fcc.cern.ch/FCCDicts').split(':'):
    _cand = os.path.join(_d, procFile)
    if os.path.isfile(_cand):
      procFile = _cand
      break
  print(procFile)
  if not os.path.isfile(procFile):
    print ('----> No procDict found: ==={}===, exit'.format(procFile))
    sys.exit(3)
  with open(procFile, 'r') as f:
    procDict=json.load(f)
  

  for pr in sigs + bkgs:

    if procDict[pr]["crossSection"] != 1.0:
      procDict[pr] = procDict[pr]
    # If not in procDict, check if it exists in procDictLocal
    elif procDict[pr]["crossSection"] == 1.0:
      procDict[pr]["crossSection"] = procDictLocal[pr]["crossSection"]
      procDict[pr]["kfactor"] = procDictLocal[pr]["kfactor"]
      procDict[pr]["matchingEfficiency"] = procDictLocal[pr]["matchingEfficiency"]
   
    # If data is found, calculate the cross-section
    #xsec[pr] = procDict[pr]["crossSection"]*procDict[pr]["kfactor"]*procDict[pr]["matchingEfficiency"]
    xsec[pr] = procDict[pr]["crossSection"] * procDict[pr]["kfactor"] * procDict[pr]["matchingEfficiency"]
    print(f"-->Cross-section for {pr} is \t\t\t {xsec[pr]}")
    frac[pr] = 1.0
    
    if pr in procDict:
      proc_info = {
        "numberOfEvents": procDict[pr]["numberOfEvents"], 
        "sumOfWeights": procDict[pr]["sumOfWeights"], 
        "crossSection": procDict[pr]["crossSection"], 
        "kfactor": procDict[pr]["kfactor"], 
        "matchingEfficiency": procDict[pr]["matchingEfficiency"]
      }
      print(f"{pr}:{proc_info}")

  print(f"--->Working on variables: {vars_list}")
  for cur_mode in sigs+bkgs:
    print(f"--->Working on {cur_mode}") 
    path = f"{data_path}/{cur_mode}"  
    files[cur_mode] = glob.glob(f"{path}/*.root")
   
    N_events[cur_mode] = sum([uproot.open(f)["eventsProcessed"].value for f in files[cur_mode]])
    print(f"------>Produced {N_events[cur_mode]} of {cur_mode} MC samples")
    df[cur_mode] = pd.concat((ut.get_df(f, vars_list) for f in files[cur_mode]), ignore_index=True)
    print(f"------>After selection: {len(df[cur_mode])} of {cur_mode} MC samples")
    eff[cur_mode] = len(df[cur_mode])/N_events[cur_mode]
    print(f"------>Cut Efficiency: {eff[cur_mode]*100} %")
    df[cur_mode]['sample'] = cur_mode
    df[cur_mode]['isSignal'] = (1 if(cur_mode in sigs) else 0)
    print(cur_mode)
  #exit(0)
  #set the BDT input numbers of each process
  
  xsec_tot_bkg = sum([ eff[cur_mode]*xsec[cur_mode] for cur_mode in bkgs])
  xsec_tot_sig = sum([ eff[cur_mode]*xsec[cur_mode] for cur_mode in sigs])
  N_sigs = sum([len(df[cur_mode]) for cur_mode in sigs])
  xsec_tot = sum([ eff[cur_mode]*xsec[cur_mode] for cur_mode in sigs+bkgs])
  print(xsec_tot_bkg)
  print(xsec_tot_sig)
  

  for cur_mode in sigs+bkgs:
    N_BDT_inputs[cur_mode] = (int(frac[cur_mode]*len(df[cur_mode])) if cur_mode in sigs else int(frac[cur_mode]*N_sigs*(eff[cur_mode]*xsec[cur_mode]/xsec_tot_bkg)))
    print(f"------->On {cur_mode}")
    print(f"--------->BDT inputs of: {N_BDT_inputs[cur_mode]}")
    print(f"--------->Before cut inputs needed: {math.ceil((N_BDT_inputs[cur_mode])/eff[cur_mode])}")
    print(f"--------->Cut efficiency of: {eff[cur_mode]*100} %")
    print(f"--------->#Events before the cut: {N_events[cur_mode]}") 
    print(f"--------->#Events after the cut: {len(df[cur_mode])}")
    print(f"--------->Percentage after cut: {((eff[cur_mode]*xsec[cur_mode])/xsec_tot)*100} %")
  print(f"--->Finished")

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Process mumuH, WWmumu, ZZ, Zll,eeZ MC to make reduced files for xgboost training')
  parser.add_argument("--Channel", action = "store", dest = "channel", default = "mumu", help="ee or mumu")
  parser.add_argument("--Mode", action = "store", dest = "modes", default = ["mumuH","ZZ","WWmumu","Zll","eeZ"], help="Decay cur_mode")
  parser.add_argument("--Folds", action = "store", dest = "n_folds", default = 2, help="Number of Folds")
  parser.add_argument("--Stage", action = "store", dest = "stage", default = "training", choices=["training","validation"], help="training or validation")
  args = vars(parser.parse_args())

  run(**args)

