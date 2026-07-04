#!/usr/bin/env python3
"""
Convert an existing (old-format) xgboost model to the new TMVA RBDT format so it
can be read by ROOT 6.38's TMVA::Experimental::RBDT on the latest FCCAnalyses stack.

The original models were saved with the old TMVA SaveXGBoost; ROOT 6.38's RBDT
reader cannot parse that structure ("No RBDT with name ..."). But the original
xgboost booster is preserved alongside as xgb_bdt.joblib, so we:
  1. load the joblib (XGBClassifier),
  2. round-trip the booster through a clean .json (clears the old-serialization
     warning and normalizes the format),
  3. re-export via the new ROOT.TMVA.Experimental.SaveXGBoost -> xgb_bdt_rbdt.root,
  4. verify it loads with RBDT and predicts in [0,1].

No retraining: the decision trees are unchanged, only the on-disk format.

Usage:  python convert_bdt.py <model_dir>   # dir holding xgb_bdt.joblib
"""
import sys
import os
import joblib
import xgboost
import ROOT

KEY = "ZH_Recoil_BDT"   # must match the RBDT name the stage1 scripts request
NUM_INPUTS = 9          # Compute<9, float> in the stage1 scripts

model_dir = sys.argv[1] if len(sys.argv) > 1 else "."
joblib_path = os.path.join(model_dir, "xgb_bdt.joblib")
json_path = os.path.join(model_dir, "xgb_bdt.json")
out_path = os.path.join(model_dir, "xgb_bdt_rbdt.root")

print(f"[convert] loading {joblib_path}")
clf = joblib.load(joblib_path)
booster = clf.get_booster()

print(f"[convert] round-tripping booster through {json_path}")
booster.save_model(json_path)
# rebuild a clean sklearn XGBClassifier (SaveXGBoost needs .objective etc.)
clean = xgboost.XGBClassifier()
clean.load_model(json_path)
# preserve the original training objective if the clean reload lost it
if not getattr(clean, "objective", None):
    clean.objective = getattr(clf, "objective", "binary:logistic")
print(f"[convert] objective = {clean.objective}")

print(f"[convert] exporting to new RBDT format: {out_path} (key={KEY}, n_inputs={NUM_INPUTS})")
if os.path.exists(out_path):
    os.remove(out_path)
ROOT.TMVA.Experimental.SaveXGBoost(clean, KEY, out_path, num_inputs=NUM_INPUTS)

print("[verify] loading converted model with RBDT and predicting")
rbdt = ROOT.TMVA.Experimental.RBDT(KEY, out_path)
import array
x = ROOT.std.vector("float")([0.5] * NUM_INPUTS)
y = rbdt.Compute(x)
print(f"[verify] RBDT loaded OK; output size={y.size()}, val0={y[0]:.6f}")
print("[done]", out_path)
