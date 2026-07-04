"""
Train the ZH hadronic BDT (ecm 365) on the stage1 MVA ntuples.

Adapted from FCCPhysics zh_hadronic_training/train365.py:
  - reads the chunked SDCC ntuples (MVA_ntuples/<process>/chunk_*.root),
  - cross-sections from the winter2023 procDict on cvmfs (the old-style stage1
    output has no crossSection key),
  - signal weight = f * intLumi / eventsProcessed (equal weight per H decay),
    background weight = xsec * intLumi / eventsProcessed,
  - saves the model in TMVA format (SaveXGBoost + variables TList), loadable
    by TMVAHelperXGB, to the site_config qq model path.

Run inside the key4hep environment: python train_xgb.py
"""
import glob
import json
import os
import sys
import pickle

import uproot
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
import ROOT

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from site_config import bdt_model, output_dir
from zqq_stage1_common import TRAIN_VARS

ROOT.gROOT.SetBatch(True)

ECM = 365
INT_LUMI = 3e6        # pb-1
SIG_LUMI_FRAC = 0.15   # equal effective lumi per Higgs decay (reference: 0.15 * intLumi at 365)
PROCDICT = "/cvmfs/fcc.cern.ch/FCCDicts/FCCee_procDict_winter2023_IDEA.json"

inputDir = output_dir(ECM, "qq", "MVA_ntuples")

z_decays = ["qq", "bb", "cc", "ss"]
h_decays = ["Hbb", "Hcc", "Hss", "Hgg", "Hmumu", "Htautau", "HZZ", "HWW", "HZa", "Haa"]
sig_procs = [f"wzp6_ee_{z}H_{h}_ecm{ECM}" for z in z_decays for h in h_decays]
bkg_procs = [f"p8_ee_WW_ecm{ECM}", f"wzp6_ee_qq_ecm{ECM}"]

procDict = json.load(open(PROCDICT))


def load_process(proc, target=0):
    files = sorted(glob.glob(f"{inputDir}/{proc}/chunk_*.root"))
    if not files:
        sys.exit(f"ERROR: no chunks for {proc} in {inputDir}")
    ev_proc = 0.
    for f in files:
        with uproot.open(f) as fIn:
            ev_proc += fIn["eventsProcessed"].value
    df = uproot.concatenate([f"{f}:events" for f in files], TRAIN_VARS, library="pd")
    if target == 1:
        weight = SIG_LUMI_FRAC * INT_LUMI / ev_proc
    else:
        xsec = procDict[proc]["crossSection"]
        weight = xsec * INT_LUMI / ev_proc
    print(f"Loaded {proc}: {len(df)} events, eventsProcessed={ev_proc:.0f}, weight={weight:.3e}")
    df["target"] = target
    df["weight"] = weight
    return df


print("Parse inputs")
dfs = [load_process(p, target=1) for p in sig_procs] + [load_process(p) for p in bkg_procs]
data = pd.concat(dfs, ignore_index=True)

train_data, test_data, train_labels, test_labels, train_weights, test_weights = train_test_split(
    data[TRAIN_VARS], data["target"], data["weight"], test_size=0.2, random_state=42
)

# conversion to numpy needed for default feature names (needed for the TMVA conversion)
train_data, test_data = train_data.to_numpy(), test_data.to_numpy()
train_labels, test_labels = train_labels.to_numpy(), test_labels.to_numpy()
train_weights, test_weights = train_weights.to_numpy(), test_weights.to_numpy()

# hyperparameters of the reference training (parms_softprob)
params = {
    "objective": "binary:logistic",
    "eval_metric": "logloss",
    "n_estimators": 350,
    "max_depth": 5,
    "early_stopping_rounds": 1,
}

print("Start training")
eval_set = [(train_data, train_labels), (test_data, test_labels)]
bdt = xgb.XGBClassifier(**params)
bdt.fit(train_data, train_labels, verbose=True, eval_set=eval_set,
        sample_weight_eval_set=[train_weights, test_weights])

print("Export model")
fOutName = bdt_model(ECM, "qq")
os.makedirs(os.path.dirname(fOutName), exist_ok=True)
ROOT.TMVA.Experimental.SaveXGBoost(bdt, "bdt_model", fOutName, num_inputs=len(TRAIN_VARS))

# append the variable list (read back by TMVAHelperXGB)
variables_ = ROOT.TList()
for var in TRAIN_VARS:
    variables_.Add(ROOT.TObjString(var))
fOut = ROOT.TFile(fOutName, "UPDATE")
fOut.WriteObject(variables_, "variables")
fOut.Close()

with open(fOutName.replace(".root", ".pkl"), "wb") as f:
    pickle.dump(bdt, f)

print(f"Model saved to {fOutName}")
