"""
Train the ZH hadronic BDT (ecm 365) on the preprocessed training set
(process_sig_bkg_samples_for_xgb.py -> training/preprocessed.pkl).

Adapted from FCCPhysics zh_hadronic_training/train365.py (hyperparameters
parms_softprob), structured like the leptonic train_xgb.py:
  - reads the pickled train/validation split (valid column),
  - trains with the per-process event weights (sample_weight; an earlier
    version only passed them to the eval sets, so they were ignored in the fit),
  - saves the model in TMVA format (SaveXGBoost + variables TList), loadable
    by TMVAHelperXGB, to the site_config qq model path, plus a pickle of the
    classifier for evaluation.py.

NB: the stage1 W1_costheta/W2_costheta bug of the reference (both abs(W1.Theta()))
is fixed in zqq_stage1_common.py, so this training is NOT weight-compatible with
the pre-trained MIT model bdt_model_ecm365.root.

Run inside the key4hep environment: python train_xgb.py
(xgboost 1.6.2 in the 2024-03-10 stack: constructor-style eval_metric /
early_stopping_rounds).

ZQQ_BDT_VARIANT=<variant> (zqq_bdt_variant.py; e.g. bugw = the reference histmaker's W-angle
inputs) switches to a variant of the BDT inputs: outputs then go to training_<variant>/ and
models_variants/<variant>/ instead; unset = the behaviour below, unchanged.
XGB_NTHREAD=<n> limits the xgboost thread count (unset = xgboost default, all cores).
"""
import os
import sys
import pickle

import pandas as pd
import xgboost as xgb
import ROOT

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from site_config import bdt_model, output_dir
from zqq_stage1_common import TRAIN_VARS
from zqq_bdt_variant import describe as variant_describe, model_path as variant_model_path, training_dir as variant_training_dir

ROOT.gROOT.SetBatch(True)

ECM = 365

trainDir = variant_training_dir(ECM)   # training/ (nominal) or training_<variant>/ (ZQQ_BDT_VARIANT)


def run():
    print(f"BDT inputs: {variant_describe()}; training set {trainDir}/preprocessed.pkl")
    data = pd.read_pickle(f"{trainDir}/preprocessed.pkl")
    train, valid = data[~data["valid"]], data[data["valid"]]
    print(f"Training on {len(train)} events, validating on {len(valid)} "
          f"(signal fraction {train['target'].mean():.3f})")

    # conversion to numpy needed for default feature names (needed for the TMVA conversion)
    train_data, valid_data = train[TRAIN_VARS].to_numpy(), valid[TRAIN_VARS].to_numpy()
    train_labels, valid_labels = train["target"].to_numpy(), valid["target"].to_numpy()
    train_weights, valid_weights = train["weight"].to_numpy(), valid["weight"].to_numpy()

    # hyperparameters of the reference training (parms_softprob)
    params = {
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        "n_estimators": 350,
        "max_depth": 5,
        "early_stopping_rounds": 1,
    }
    if os.environ.get("XGB_NTHREAD"):   # optional thread cap (shared nodes); unset = xgboost default
        params["nthread"] = int(os.environ["XGB_NTHREAD"])

    print("Start training")
    eval_set = [(train_data, train_labels), (valid_data, valid_labels)]
    bdt = xgb.XGBClassifier(**params)
    bdt.fit(train_data, train_labels, sample_weight=train_weights,
            verbose=True, eval_set=eval_set,
            sample_weight_eval_set=[train_weights, valid_weights])

    print("Export model")
    fOutName = variant_model_path(ECM)   # site_config.bdt_model(ECM, "qq") for the nominal inputs
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


if __name__ == "__main__":
    run()
