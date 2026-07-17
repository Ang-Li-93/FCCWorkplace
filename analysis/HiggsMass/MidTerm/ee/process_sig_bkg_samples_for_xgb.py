import os
import sys
import argparse
import glob
import uproot
import pandas as pd
from sklearn.model_selection import train_test_split
from userConfig import loc, train_vars, mode_names
import utils as ut
import json
from config.common_defaults import deffccdicts

def get_data_paths(cur_mode, data_path):
    path = f"{data_path}/{mode_names[cur_mode]}"
    return glob.glob(f"{path}/*.root")

def calculate_event_counts_and_efficiencies(cur_mode, files, vars_list):
    N_events = sum([uproot.open(f)["eventsProcessed"].value for f in files])
    print(f"Number of events in {cur_mode}: {N_events}")
    print(f"Number of files in {cur_mode}: {len(files)}")
    print(f"Reading files {files}")
    df = pd.concat((ut.get_df(f, vars_list) for f in files), ignore_index=True)
    eff = len(df) / N_events
    return N_events, df, eff

def update_dataframe_with_additional_info(df, cur_mode, sig):
    df['sample'] = cur_mode
    df['isSignal'] = int(cur_mode == sig)
    return df

def calculate_BDT_input_numbers(mode_names, sig, df, eff, xsec, frac):
    N_BDT_inputs = {}
    print(f"Calculating number of BDT inputs for {mode_names}")
    print(f"eff = {eff}")
    xsec_tot_bkg = sum(eff[mode] * xsec[mode] for mode in mode_names if mode != sig)
    for cur_mode in mode_names:
        N_BDT_inputs[cur_mode] = (int(frac[cur_mode] * len(df[cur_mode])) if cur_mode == sig else
                                  int(frac[cur_mode] * len(df[sig]) * (eff[cur_mode] * xsec[cur_mode] / xsec_tot_bkg)))
    return N_BDT_inputs

def split_data_and_update_dataframe(df, N_BDT_inputs, xsec, N_events, cur_mode):
    df = df.sample(n=N_BDT_inputs[cur_mode], random_state=1)
    df0, df1 = train_test_split(df, test_size=0.5, random_state=7)
    df.loc[df0.index, "valid"] = False
    df.loc[df1.index, "valid"] = True
    df.loc[df.index, "norm_weight"] = xsec[cur_mode] / N_events[cur_mode]
    return df

def save_data_to_pickle(dfsum, pkl_path):
    print("Writing output to pickle file")
    ut.create_dir(pkl_path)
    print(f"--->Preprocessed saved {pkl_path}/preprocessed.pkl")
    dfsum.to_pickle(f"{pkl_path}/preprocessed.pkl")

def get_procDict(procFile):
    procDict = None
    if 'http://' in procFile or 'https://' in procFile:
        print ('----> getting process dictionary from the web')
        import urllib.request
        req = urllib.request.urlopen(procFile).read()
        procDict = json.loads(req.decode('utf-8'))
    else:
        if not ('eos' in procFile): 
            procFile = os.path.join(os.getenv('FCCDICTSDIR', deffccdicts), '') + procFile
        print(procFile)
        if not os.path.isfile(procFile):
            print ('----> No procDict found: ==={}===, exit'.format(procFile))
            sys.exit(3)
        with open(procFile, 'r') as f:
            procDict=json.load(f)

    return procDict

def update_procDict_keys(procDict, mode_names):
    # Reverse the mode_names dictionary
    reversed_mode_names = {v: k for k, v in mode_names.items()}

    updated_dict = {}
    for key, value in procDict.items():
        new_key = reversed_mode_names.get(key, key)
        updated_dict[new_key] = value
    return updated_dict

    
def run(modes, n_folds, stage):

    procFile = "FCCee_procDict_winter2023_training_IDEA.json"
    proc_dict = get_procDict(procFile)
    procDict = update_procDict_keys(proc_dict, mode_names)

    xsec = {key: value["crossSection"] for key, value in procDict.items() if key in mode_names}

    #print(f"Cross sections = {xsec}")
    
    sig = "eeH"
    data_path = loc.TRAIN if stage == "training" else loc.ANALYSIS
    pkl_path = loc.PKL if stage == "training" else loc.PKL_Val

    files = {}
    df = {}
    N_events = {}
    eff = {}
    vars_list = train_vars.copy()

    frac = {
        "eeH": 1.0,
        "WWee": 1.0,
        "ZZ": 1.0,
        "Zll": 1.0,
        "egamma": 1.0,
        "gammae": 1.0,
        "gaga_ee": 1.0
    }

    for cur_mode in mode_names:
        files[cur_mode] = get_data_paths(cur_mode, data_path)
        N_events[cur_mode], df[cur_mode], eff[cur_mode] = calculate_event_counts_and_efficiencies(cur_mode, files[cur_mode], vars_list)
        print(f"Number of events in {cur_mode} = {N_events[cur_mode]}")
        print(f"Efficiency of {cur_mode} = {eff[cur_mode]}")
        df[cur_mode] = update_dataframe_with_additional_info(df[cur_mode], cur_mode, sig)

    N_BDT_inputs = calculate_BDT_input_numbers(mode_names, sig, df, eff, xsec, frac)

    print(f"Number of BDT inputs = {N_BDT_inputs}")
    for cur_mode in mode_names:
        df[cur_mode] = split_data_and_update_dataframe(df[cur_mode], N_BDT_inputs, xsec, N_events, cur_mode)

    dfsum = pd.concat([df[cur_mode] for cur_mode in mode_names])

    save_data_to_pickle(dfsum, pkl_path)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process eeH, WWee, ZZ, Zll,eeZ MC to make reduced files for xgboost training')
    parser.add_argument("--Mode", action="store", dest="modes", default=["eeH", "ZZ", "WWee", "Zll", "egamma", "gammae", "gaga_ee"], help="Decay mode")
    parser.add_argument("--Folds", action="store", dest="n_folds", default=2, help="Number of Folds")
    parser.add_argument("--Stage", action="store", dest="stage", default="training", choices=["training", "validation"], help="training or validation")
    args = vars(parser.parse_args())
    run(**args)