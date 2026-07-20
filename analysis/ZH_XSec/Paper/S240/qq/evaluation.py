"""
Evaluate the trained ZH hadronic BDT (ecm 240): performance and validation plots,
mirroring the leptonic evaluation.py (log-loss, ROC, overtraining check, feature
importance, efficiency vs score cut), weighted with the per-process event weights.

Reads training/preprocessed.pkl and the pickled classifier saved next to the
TMVA model (train_xgb.py). Plots go to training/plots/.

Run inside the key4hep environment: python evaluation.py
"""
import os
import sys
import pickle

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from site_config import bdt_model, output_dir
from zqq_stage1_common import TRAIN_VARS

ECM = 240
LABEL = r"$Z(q\bar{q})H$, $\sqrt{s}$ = %d GeV" % ECM

trainDir = output_dir(ECM, "qq", "training")
plotDir = f"{trainDir}/plots"

latex_mapping = {
    "zqq_p_best": r"$p_{qq}$",
    "leading_jet_costheta": r"$|\cos\theta_{j_1}|$",
    "subleading_jet_costheta": r"$|\cos\theta_{j_2}|$",
    "leading_jet_p": r"$p_{j_1}$",
    "subleading_jet_p": r"$p_{j_2}$",
    "acolinearity": r"$|\Delta\theta_{jj}|$",
    "acoplanarity": r"$|\Delta\phi_{jj}|$",
    "W1_p": r"$p_{W_1}$",
    "W2_p": r"$p_{W_2}$",
    "W1_m": r"$m_{W_1}$",
    "W2_m": r"$m_{W_2}$",
    "z_costheta": r"$|\cos\theta_{qq}|$",
    "thrust_magn": r"$T$",
    "W1_costheta": r"$|\cos\theta_{W_1}|$",
    "W2_costheta": r"$|\cos\theta_{W_2}|$",
}

# groups for the efficiency plot (per-process curves would be unreadable: 40 signals)
eff_groups = {
    "ZH (signal)": lambda df: df["isSignal"] == 1,
    "WW": lambda df: df["sample"] == f"p8_ee_WW_ecm{ECM}",
    r"Z/$\gamma^{*}\to q\bar{q}$": lambda df: df["sample"] == f"wzp6_ee_qq_ecm{ECM}",
}


def decorate(ax, right_label=LABEL):
    ax.set_title("FCC-ee Simulation", fontsize=13, loc="left", style="italic", weight="bold")
    ax.set_title(right_label, fontsize=13, loc="right")


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(f"{plotDir}/{name}.{ext}")
    plt.close(fig)
    print(f"------>Saved {plotDir}/{name}.png/.pdf")


def plot_log_loss(bdt):
    results = bdt.evals_result()
    x = range(len(results["validation_0"]["logloss"]))
    fig, ax = plt.subplots()
    ax.plot(x, results["validation_0"]["logloss"], label="Training")
    ax.plot(x, results["validation_1"]["logloss"], label="Validation")
    ax.set_xlabel("Number of trees")
    ax.set_ylabel("Log loss")
    ax.legend()
    decorate(ax)
    save(fig, "log_loss")


def plot_roc(df):
    fig, ax = plt.subplots(figsize=(6, 6))
    for sel, style, label in ((df["valid"], "-", "Validation sample"),
                              (~df["valid"], "--", "Training sample")):
        d = df[sel]
        fpr, tpr, _ = roc_curve(d["isSignal"], d["BDTscore"], sample_weight=d["weight"])
        ax.plot(fpr, tpr, style, label=f"{label} (AUC = {auc(fpr, tpr):.4f})")
    ax.plot([0, 1], [0, 1], color="navy", lw=1, linestyle=":")
    ax.set_xlabel(r"$\epsilon_B$")
    ax.set_ylabel(r"$\epsilon_S$")
    ax.legend(loc="lower right")
    decorate(ax)
    save(fig, "roc")


def plot_bdt_score(df):
    fig, ax = plt.subplots(figsize=(8, 6))
    for cut, ls, color, label in (
            ((~df["valid"]) & (df["isSignal"] == 1), "solid", "red", "Signal training"),
            ((df["valid"]) & (df["isSignal"] == 1), "dashed", "red", "Signal validation"),
            ((~df["valid"]) & (df["isSignal"] == 0), "solid", "blue", "Background training"),
            ((df["valid"]) & (df["isSignal"] == 0), "dashed", "blue", "Background validation")):
        d = df[cut]
        ax.hist(d["BDTscore"], weights=d["weight"], density=True, bins=50, range=(0, 1),
                histtype="step", label=label, linestyle=ls, color=color, linewidth=1.5)
    ax.set_yscale("log")
    ax.set_xlim(0, 1)
    ax.set_xlabel("BDT score")
    ax.set_ylabel("Normalized to unity")
    ax.legend(loc="upper center", frameon=False)
    decorate(ax)
    save(fig, "bdt_score")


def plot_importance(bdt):
    importance = bdt.get_booster().get_score(importance_type="weight")
    items = sorted(importance.items(), key=lambda x: x[1])
    names = [latex_mapping[TRAIN_VARS[int(k[1:])]] for k, _ in items]
    values = [v for _, v in items]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(names, values)
    ax.set_xlabel("F-score")
    decorate(ax)
    fig.tight_layout()
    save(fig, "importance")


def plot_efficiency(df):
    valid = df[df["valid"]]
    cuts = np.linspace(0, 0.99, 100)
    fig, ax = plt.subplots(figsize=(8, 6))
    for label, sel in eff_groups.items():
        d = valid[sel(valid)]
        total = d["weight"].sum()
        effs = [d.loc[d["BDTscore"] > c, "weight"].sum() / total for c in cuts]
        ax.plot(cuts, effs, label=label)
    ax.set_xlim(0, 1)
    ax.set_xlabel("BDT score cut")
    ax.set_ylabel("Efficiency")
    ax.grid(alpha=0.4)
    ax.legend()
    decorate(ax)
    save(fig, "efficiency")


def run():
    df = pd.read_pickle(f"{trainDir}/preprocessed.pkl")
    model_pkl = bdt_model(ECM, "qq").replace(".root", ".pkl")
    print(f"--->Loading BDT model {model_pkl}")
    with open(model_pkl, "rb") as f:
        bdt = pickle.load(f)

    print("--->Evaluating BDT model")
    # score with ALL exported trees: SaveXGBoost exports the full booster (incl. the
    # 1-2 early-stopping overshoot rounds), while a plain predict_proba stops at
    # best_iteration and would differ slightly from the deployed mva_score
    n_rounds = bdt.get_booster().num_boosted_rounds()
    df["BDTscore"] = bdt.predict_proba(df[TRAIN_VARS].to_numpy(),
                                       iteration_range=(0, n_rounds))[:, 1]

    os.makedirs(plotDir, exist_ok=True)
    plot_log_loss(bdt)
    plot_roc(df)
    plot_bdt_score(df)
    plot_importance(bdt)
    plot_efficiency(df)


if __name__ == "__main__":
    run()
