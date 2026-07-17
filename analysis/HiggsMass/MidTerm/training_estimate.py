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
#from userConfig import loc, mode, train_vars, train_vars_vtx, mode_names
from userConfig import loc, train_vars, train_vars_vtx, mode_names
import plotting
import utils as ut
from config.common_defaults import deffccdicts

def run(channel, modes, n_folds, stage):
  #xsec, from http://fcc-physics-events.web.cern.ch/fcc-physics-events/Delphesevents_spring2021_IDEA.php
  xsec = {}
  xsec["mumuH"]   = 0.0067643
  xsec["WWmumu"]  = 0.25792
  xsec["ZZ"]      = 1.35899
  xsec["Zll"]     = 5.288
  xsec["eeZ"]     = 0.10368
  
  if channel == 'mumu':
    sigs = ["wzp6_ee_mumuH_ecm240"]
    bkgs = ["p8_ee_WW_ecm240", 
            "p8_ee_ZZ_ecm240",
            "wzp6_ee_mumu_ecm240",
            #"wzp6_ee_tautau_ecm240",
            "wzp6_egamma_eZ_Zmumu_ecm240",
            "wzp6_gammae_eZ_Zmumu_ecm240",
            "wzp6_gaga_mumu_60_ecm240",
            #"wzp6_gaga_tautau_60_ecm240",
            #"wzp6_ee_nuenueZ_ecm240"
            ]
  elif channel == 'ee':
    sigs = ["wzp6_ee_eeH_ecm240"]
    bkgs = ["p8_ee_WW_ecm240",
            "p8_ee_ZZ_ecm240",
            "wzp6_ee_ee_Mee_30_150_ecm240",
            #"wzp6_ee_tautau_ecm240",
            "wzp6_egamma_eZ_Zee_ecm240",
            "wzp6_gammae_eZ_Zee_ecm240",
            #"wzp6_gaga_ee_60_ecm240",
            #"wzp6_gaga_tautau_60_ecm240",
            #"wzp6_ee_nuenueZ_ecm240"
            ]
  else:
    print("Channel doesn't exist, please choose 'ee' or 'mumu'")
    exit(0)
  
  data_path =os.path.join(loc.EOS,channel,"training_estimation")

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
  procFile = os.path.join(os.getenv('FCCDICTSDIR', deffccdicts), '') + procFile
  print(procFile)
  if not os.path.isfile(procFile):
    print ('----> No procDict found: ==={}===, exit'.format(procFile))
    sys.exit(3)
  with open(procFile, 'r') as f:
    procDict=json.load(f)
  
  
  for pr in sigs+bkgs: 
    xsec[pr] = procDict[pr]["crossSection"]*procDict[pr]["kfactor"]*procDict[pr]["matchingEfficiency"]
    print(f"-->Cross-section for {pr} is \t\t\t {xsec[pr]}")
    frac[pr] = 1.0

  print(f"--->Working on variables: {vars_list}")
  for cur_mode in sigs+bkgs:
    print(f"--->Working on {cur_mode}")
    
    path = f"{data_path}/{cur_mode}"  
    files[cur_mode] = glob.glob(f"{path}/*.root")
   
    N_events[cur_mode] = sum([uproot.open(f)["eventsProcessed"].value for f in files[cur_mode]])
    print(f"------>Produced {N_events[cur_mode]} of {cur_mode} MC samples")
    df[cur_mode] = pd.concat((ut.get_df(f, vars_list) for f in files[cur_mode]), ignore_index=True)
    print(f"------>After selection: {len(df[cur_mode])} {cur_mode} MC samples")
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

