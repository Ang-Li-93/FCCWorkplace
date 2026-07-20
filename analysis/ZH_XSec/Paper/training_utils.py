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


def get_df(path, vars_list=None):
    """Load the 'events' tree of a ROOT file into a pandas DataFrame."""
    with uproot.open(path) as f:
        return f["events"].arrays(vars_list, library="pd")


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
