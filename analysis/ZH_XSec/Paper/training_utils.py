"""
Helper functions for the leptonic BDT-training trio (process_sig_bkg_samples_for_xgb,
train_xgb, evaluation) and training_estimate.py, imported as `ut`.

Reimplementation of the lxplus-era `utils.py` (FCCeePhysicsPerformance mH-recoil
workflow) that was never checked into this repository - only the functions the
training scripts actually call: get_df, create_dir, plot_roc_curve, Significance, Z.
Event weights: the per-event 'norm_weight' column (xsec/N, set by
process_sig_bkg_samples_for_xgb) is used when present, else 'weight', else unweighted.
"""
import os

import numpy as np
import pandas as pd
import uproot
from sklearn.metrics import roc_curve

# Acolinearity variant of the leptonic BDT inputs (env LEP_ACOL, see leptonic_training_config):
#   unset / 'training' : zll_leptons_acolinearity as stored by stage1 (= |theta1 - theta2|)
#   'jan'              : the FCCPhysics histmaker definition acos(-cos(opening angle)) =
#                        pi - opening angle of the two Z leptons, recomputed from the stored
#                        theta/phi and written INTO the zll_leptons_acolinearity column, so the
#                        training trio needs no other change (same variable name, same model
#                        format; rescore_leptonic.py applies the same definition downstream).
ACOL_VAR = "zll_leptons_acolinearity"
ACOL_ANGLES = ["leading_zll_lepton_theta", "leading_zll_lepton_phi",
               "subleading_zll_lepton_theta", "subleading_zll_lepton_phi"]


def acol_variant():
    v = os.environ.get("LEP_ACOL", "training").lower()
    if v not in ("training", "jan"):
        raise ValueError(f"LEP_ACOL={v!r}: expected 'training' or 'jan'")
    return v


def acolinearity_jan(theta1, phi1, theta2, phi2):
    """pi - opening angle of two directions (FCCPhysics functions.h acolinearity), float64 math."""
    t1, p1, t2, p2 = (np.asarray(a, dtype=np.float64) for a in (theta1, phi1, theta2, phi2))
    c = np.sin(t1) * np.sin(t2) * np.cos(p1 - p2) + np.cos(t1) * np.cos(t2)
    return np.arccos(-np.clip(c, -1.0, 1.0))


def get_df(path, vars_list=None):
    """Load the 'events' tree of a ROOT file into a pandas DataFrame
    (LEP_ACOL=jan: zll_leptons_acolinearity replaced by the Jan definition, see above)."""
    jan = acol_variant() == "jan" and (vars_list is None or ACOL_VAR in vars_list)
    with uproot.open(path) as f:
        if not jan:
            return f["events"].arrays(vars_list, library="pd")
        extra = [] if vars_list is None else [a for a in ACOL_ANGLES if a not in vars_list]
        df = f["events"].arrays(None if vars_list is None else list(vars_list) + extra, library="pd")
        df[ACOL_VAR] = acolinearity_jan(*(df[a] for a in ACOL_ANGLES)).astype(df[ACOL_VAR].dtype)
        return df.drop(columns=extra) if extra else df


def create_dir(path):
    os.makedirs(path, exist_ok=True)


def _weights(df):
    for col in ("norm_weight", "weight"):
        if col in df.columns:
            return df[col].to_numpy()
    return None


def plot_roc_curve(df, score_column, ax=None, color=None, label=None,
                   tpr_threshold=0.0, linestyle='-'):
    """Draw eff_S vs eff_B (y = signal efficiency, x = background efficiency)."""
    fpr, tpr, _ = roc_curve(df["isSignal"], df[score_column], sample_weight=_weights(df))
    sel = tpr >= tpr_threshold
    kwargs = {"linestyle": linestyle}
    if color is not None:
        kwargs["color"] = color
    if label is not None:
        kwargs["label"] = label
    ax.plot(fpr[sel], tpr[sel], **kwargs)


def Z(S, B):
    """Approximate significance S/sqrt(S+B)."""
    return S / np.sqrt(S + B)


def Significance(sig_df, bkg_df, score_column="BDTscore", func=Z, nbins=100):
    """
    Significance scan vs score cut: DataFrame indexed by the cut value with a 'Z'
    column, func(S(cut), B(cut)) with S/B the weighted yields above the cut.
    """
    cuts = np.linspace(0, 1, nbins, endpoint=False)
    sw = _weights(sig_df)
    bw = _weights(bkg_df)
    sw = np.ones(len(sig_df)) if sw is None else sw
    bw = np.ones(len(bkg_df)) if bw is None else bw
    s_scores = sig_df[score_column].to_numpy()
    b_scores = bkg_df[score_column].to_numpy()
    zs = []
    for c in cuts:
        S = sw[s_scores > c].sum()
        B = bw[b_scores > c].sum()
        zs.append(func(S, B) if S + B > 0 else 0.0)
    return pd.DataFrame({"Z": zs}, index=cuts)
