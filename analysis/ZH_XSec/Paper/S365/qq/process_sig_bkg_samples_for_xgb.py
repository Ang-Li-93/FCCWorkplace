"""
Prepare the ZH hadronic (Z->qq) BDT training set (ecm 365) from the stage1 training
ntuples (stage1_training_ntuples.py -> MVA_ntuples/<process>/chunk*.root).

Mirrors the leptonic process_sig_bkg_samples_for_xgb.py -> preprocessed.pkl interface
(columns: TRAIN_VARS + sample / isSignal / valid / weight), with the weighting of the
hadronic reference training (FCCPhysics zh_hadronic_training/train365.py):
  - signal weight     = SIG_LUMI_FRAC * intLumi / eventsProcessed
    (equal effective luminosity for every H decay),
  - background weight = xsec * intLumi / eventsProcessed,
  - cross-sections from the winter2023_training procDict on cvmfs (the training
    trees come from the dedicated winter2023_training campaign; the old-style
    stage1 output has no crossSection key),
  - one global 50/50 train/validation split (equal split per arXiv:2512.21290;
    the FCCPhysics reference used 80/20).

Run inside the key4hep environment: python process_sig_bkg_samples_for_xgb.py
"""
import glob
import json
import os
import sys

import uproot
import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from site_config import output_dir
from zqq_stage1_common import TRAIN_VARS

ECM = 365
INT_LUMI = 3.12e6     # pb-1 (arXiv:2512.21290)
SIG_LUMI_FRAC = 0.15   # equal effective lumi per Higgs decay (reference: 0.15 * intLumi at 365)
PROCDICT = "/cvmfs/fcc.cern.ch/FCCDicts/FCCee_procDict_winter2023_training_IDEA.json"

inputDir = output_dir(ECM, "qq", "MVA_ntuples")
outDir = output_dir(ECM, "qq", "training")

z_decays = ["qq", "bb", "cc", "ss"]
h_decays = ["Hbb", "Hcc", "Hss", "Hgg", "Hmumu", "Htautau", "HZZ", "HWW", "HZa", "Haa"]
sig_procs = [f"wzp6_ee_{z}H_{h}_ecm{ECM}" for z in z_decays for h in h_decays]
bkg_procs = [f"p8_ee_WW_ecm{ECM}", f"wzp6_ee_qq_ecm{ECM}"]

procDict = json.load(open(PROCDICT))


def load_process(proc, target=0):
    files = sorted(glob.glob(f"{inputDir}/{proc}/chunk*.root"))
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
    df["sample"] = proc
    df["target"] = target
    df["isSignal"] = target
    df["weight"] = weight
    return df


def run():
    print("Parse inputs")
    dfs = [load_process(p, target=1) for p in sig_procs] + [load_process(p) for p in bkg_procs]
    data = pd.concat(dfs, ignore_index=True)

    train_idx, valid_idx = train_test_split(data.index, test_size=0.5, random_state=42)
    data["valid"] = False
    data.loc[valid_idx, "valid"] = True

    n_sig, n_bkg = (data["isSignal"] == 1).sum(), (data["isSignal"] == 0).sum()
    print(f"Total events: {len(data)} (signal {n_sig}, background {n_bkg}); "
          f"train {len(train_idx)}, validation {len(valid_idx)}")

    os.makedirs(outDir, exist_ok=True)
    data.to_pickle(f"{outDir}/preprocessed.pkl")
    print(f"--->Preprocessed saved {outDir}/preprocessed.pkl")


if __name__ == "__main__":
    run()
