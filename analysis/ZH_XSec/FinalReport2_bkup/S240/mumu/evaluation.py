import argparse
import numbers
from re import I
import sys, os
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import roc_curve, auc
from sklearn.metrics import accuracy_score
import uproot
import ROOT
import joblib
import glob
#import seaborn as sns
from tqdm import tqdm

from matplotlib import rc
from userConfig import loc, train_vars, mode_names, latex_mapping, final_states
import plotting
import utils as ut

rc('font', **{'family': 'serif', 'serif': ['Roman']})
rc('text', usetex=True)


def load_data():
    path = f"{loc.PKL}"
    df = pd.read_pickle(f"{path}/preprocessed.pkl")
    return df


def print_input_summary(df, modes):
    print(f"__________________________________________________________")
    print(f"Input number of events:")
    for cur_mode in modes:
        print(f"Number of training {cur_mode}: {int(len(df[(df['sample'] == cur_mode) & (df['valid'] == False)]))}")
        print(f"Number of validation {cur_mode}: {int(len(df[(df['sample'] == cur_mode) & (df['valid'] == True)]))}")
    print(f"__________________________________________________________")


def load_trained_model(loc):
    print(f"--->Loading BDT model {loc.BDT}/xgb_bdt.joblib")
    bdt = joblib.load(f"{loc.BDT}/xgb_bdt.joblib")
    return bdt


def evaluate_bdt_model(df, bdt, vars_list):
    X = df[vars_list]
    print(f"--->Evaluating BDT model")
    df["BDTscore"] = bdt.predict_proba(X).tolist()
    df["BDTscore"] = df["BDTscore"].apply(lambda x: x[1])
    return df


def get_performance_metrics(bdt):
    print("------>Retrieving performance metrics")
    results = bdt.evals_result()
    epochs = len(results['validation_0']['error'])
    x_axis = range(0, epochs)
    best_iteration = bdt.best_iteration + 1
    return results, epochs, x_axis, best_iteration


def plot_metrics(df,bdt,vars_list,results, epochs, x_axis, best_iteration,mode_names,latex_mappingf,final_states):    
    if final_states == "mumu":
      label = r"$Z(\mu^+\mu^-)H$"
    elif final_states == "ee":
      label = r"$Z(e^+e^-)H$"
    else:
      exit("ERROR: Invalid final state")
    ut.create_dir(f"{loc.PLOTS}")
    plot_log_loss(results, x_axis, best_iteration,label)
    plot_classification_error(results, x_axis, best_iteration,label)
    plot_auc(results, x_axis, best_iteration,label)
    plot_roc(df,label)
    plot_bdt_score(df,label)
    plot_importance(bdt,vars_list,latex_mapping,label)
    plot_significance_scan(df,label)
    plot_efficiency(df,mode_names,label)


def plot_log_loss(results, x_axis, best_iteration,label):
    print("------>Plotting log loss")
    fig, ax = plt.subplots()
    ax.plot(x_axis, results['validation_0']['logloss'], label='Training')
    ax.plot(x_axis, results['validation_1']['logloss'], label='Validation')
    #plt.axvline(best_iteration, color="gray", label="Optimal tree number")
    ax.legend()
    plt.xlabel("Number of trees")
    plt.ylabel('Log Loss')
    ax.set_title(r'$\textbf{\textit{FCC-ee}}$ $\textbf{\textit{Simulation}}$', fontsize=16, loc='left')
    ax.set_title(label, fontsize=16, loc='right')
    plt.savefig(f"{loc.PLOTS}/log_loss.png")
    plt.savefig(f"{loc.PLOTS}/log_loss.pdf")
    plt.savefig(f"{loc.PLOTS}/log_loss.eps")
    plt.close()


def plot_classification_error(results, x_axis, best_iteration, label):
    print("------>Plotting classification error")
    fig, ax = plt.subplots()
    ax.plot(x_axis, results['validation_0']['error'], label='Training')
    ax.plot(x_axis, results['validation_1']['error'], label='Validation')
    #plt.axvline(best_iteration, color="gray", label="Optimal tree number")
    ax.legend()
    plt.xlabel('Number of trees')
    plt.ylabel('Classification Error')
    ax.set_title(r'$\textbf{\textit{FCC-ee}}$ $\textbf{\textit{Simulation}}$', fontsize=16, loc='left')
    ax.set_title(label, fontsize=16, loc='right')
    plt.savefig(f"{loc.PLOTS}/classification_error.png")
    plt.savefig(f"{loc.PLOTS}/classification_error.pdf")
    plt.savefig(f"{loc.PLOTS}/classification_error.eps")
    plt.close()


def plot_auc(results, x_axis, best_iteration, label):
    print("------>Plotting AUC")
    fig, ax = plt.subplots()
    ax.plot(x_axis, results['validation_0']['auc'], label='Training')
    ax.plot(x_axis, results['validation_1']['auc'], label='Validation')
    #plt.axvline(best_iteration, color="gray", label="Optimal tree number")
    ax.legend()
    plt.xlabel('Number of trees')
    plt.ylabel('AUC')
    ax.set_title(r'$\textbf{\textit{FCC-ee}}$ $\textbf{\textit{Simulation}}$', fontsize=16, loc='left')
    ax.set_title(label, fontsize=16, loc='right')
    plt.savefig(f"{loc.PLOTS}/auc.png")
    plt.savefig(f"{loc.PLOTS}/auc.pdf")
    plt.savefig(f"{loc.PLOTS}/auc.eps")
    plt.close()


def plot_roc(df,label):
    # plot ROC 1
    print("------>Plotting ROC")
    fig, axes = plt.subplots(1, 1, figsize=(5,5))
    #df_train = df_tot.query('valid==False')
    #df_valid =  df_tot.query("valid==True")
    eps=0.
    ax=axes
    ax.set_xlabel("$\epsilon_B$")
    ax.set_ylabel("$\epsilon_S$")
    ut.plot_roc_curve(df[df['valid']==True],  "BDTscore", ax=ax, label="Validation Sample", tpr_threshold=eps)
    ut.plot_roc_curve(df[df['valid']==False], "BDTscore", ax=ax, color="#ff7f02", tpr_threshold=eps,linestyle='--', label="Training Sample")
    plt.plot([eps, 1], [eps, 1], color='navy', lw=2, linestyle='--')
    ax.legend()
    ax.set_title(r'$\textbf{\textit{FCC-ee}}$ $\textbf{\textit{Simulation}}$', fontsize=16, loc='left')
    ax.set_title(label, fontsize=16, loc='right')
    print(f"Saving ROC plot to {loc.PLOTS}/ROC1.pdf")
    fig.savefig(f"{loc.PLOTS}/ROC1.pdf")
    fig.savefig(f"{loc.PLOTS}/ROC1.png")
    fig.savefig(f"{loc.PLOTS}/ROC1.eps")


def plot_bdt_score(df, label):
    print("------>Plotting BDT score (overtraining check)")
    
    fig, ax = plt.subplots(figsize=(8, 6))
    Bins = 20
    htype = "step"
    
    tag = ['Signal Training', 'Signal Validation', 'Background Training', 'Background Validation']
    line = ['solid', 'dashed', 'solid', 'dashed']
    color = ['red', 'red', 'blue', 'blue']
    cut = ['valid==False & isSignal==1', 'valid==True & isSignal==1', 'valid==False & isSignal!=1', 'valid==True & isSignal!=1']
    
    for (x, y, z, w) in zip(tag, line, color, cut):
        df_instance = df.query(w)
        print('--------->', x, len(df_instance), "Ratio: %.2f%%" % ((len(df_instance)/float(len(df))) * 100.0))
        ax.hist(df_instance['BDTscore'], density=True, bins=Bins, range=[0.0, 1.0], histtype=htype, label=x, linestyle=y, color=z, linewidth=1.5)
    
    plt.yscale('log')
    ax.legend(loc="upper right", fontsize="medium", frameon=False, shadow=False)
    ax.set_title(r'$\textbf{\textit{FCC-ee}}$ $\textbf{\textit{Simulation}}$', fontsize=16, loc='left')
    ax.set_title(label, fontsize=18, loc='right')

    ax.set_xlabel("BDT Score", fontsize=14, loc='right', weight='bold')  
    ax.set_ylabel("Normalized to Unity", fontsize=14, loc='top', weight='bold')  
     
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    
    ax.set_ylim(top=ax.get_ylim()[1] * 2.0)  # Increase the Y-axis space
    ax.set_xlim(left=0.0, right=1.0) 

    print("------>Plotting BDT score")
    plt.savefig(f"{loc.PLOTS}/bdt_score.png")
    plt.savefig(f"{loc.PLOTS}/bdt_score.pdf")
    plt.savefig(f"{loc.PLOTS}/bdt_score.eps")
    plt.close()

def plot_importance(bdt, vars_list, latex_mapping,label):
    print("------>Plotting feature importance")
    print("------>Plotting inportance")
    fig, ax = plt.subplots(figsize=(12, 6))

    # Get feature importances and sort them by importance
    importance = bdt.get_booster().get_score(importance_type='weight')
    sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=False)

    # Get the sorted indices of the variables
    sorted_indices = [int(x[0][1:]) for x in sorted_importance]

    # Get the sorted variable names and their corresponding importances
    sorted_vars = [vars_list[i] for i in sorted_indices]
    sorted_values = [x[1] for x in sorted_importance]

    # Update variable names with their LaTeX versions
    sorted_vars_latex = [latex_mapping[var] for var in sorted_vars]

    # Create a DataFrame and plot the feature importances
    importance_df = pd.DataFrame({'Variable': sorted_vars_latex, 'Importance': sorted_values})
    importance_df.plot(kind='barh', x='Variable', y='Importance', legend=None, ax=ax)
    ax.set_xlabel('F-score')
    ax.set_title(r'$\textbf{\textit{FCC-ee}}$ $\textbf{\textit{simulation}}$', fontsize=16, loc='left')
    ax.set_title(label, fontsize=16, loc='right')
    print(f"------>Saved {loc.PLOTS}/Importance.pdf")
    plt.savefig(f"{loc.PLOTS}/importance.png")
    plt.savefig(f"{loc.PLOTS}/importance.pdf")
    plt.savefig(f"{loc.PLOTS}/importance.eps")
    plt.close()





def plot_significance_scan(df,label):
    print("------>Plotting Significance scan")
    #compute the significance
    df_Z = ut.Significance(df[(df['isSignal'] == 1) & (df['valid'] == True)], df[(df['isSignal'] == 0) & (df['valid'] == True)], score_column = 'BDTscore', func=ut.Z, nbins=100)
    max_index=df_Z["Z"].idxmax()
    print('max-Z: {:.2f}'.format(df_Z.loc[max_index,"Z"]), 'cut threshold: [', max_index, ']')
    fig, ax = plt.subplots(figsize=(12,8))
    plt.scatter(df_Z.index, df_Z["Z"])
    ax.scatter(x=max_index, y=df_Z.loc[max_index,"Z"], c='r', marker="*")
    plt.xlabel("BDT Score ")
    plt.ylabel("Significance")
    txt1 = Rectangle((0, 0), 1, 1, fc="w", fill=False, edgecolor='none', linewidth=0)
    txt2 = Rectangle((0, 0), 1, 1, fc="w", fill=False, edgecolor='none', linewidth=0)
    plt.legend([txt1, txt2], ('max-Z: {:.2f} cut threshold: [{:.2f}]'.format(df_Z.loc[max_index,"Z"],max_index), "$Z = S/\\sqrt{S+B}$"))
    ax.set_title(r'$\textbf{\textit{FCC-ee}}$ $\textbf{\textit{Simulation}}$', fontsize=16, loc='left')
    ax.set_title(label, fontsize=16, loc='right')
    print("------>Plotting significance scan")
    plt.savefig(f"{loc.PLOTS}/significance_scan.png")
    plt.savefig(f"{loc.PLOTS}/significance_scan.pdf")
    plt.savefig(f"{loc.PLOTS}/significance_scan.eps")
    plt.close()


def plot_efficiency(df,mode_names,label):
    
    #Plot efficiency as a function of BDT cut in each sample
    print("------>Plotting Efficiency")
    BDT_cuts = np.linspace(0,99,99)
    cut_vals = []
    eff = {}

    for cur_mode in mode_names:
      eff[cur_mode] = []

    for x in tqdm(BDT_cuts):
      cut_val = float(x)/100
      cut_vals.append(cut_val)
      for cur_mode in mode_names:
        eff[cur_mode].append(float(len(df[(df['sample'] == cur_mode) & (df['valid'] == True) & (df['BDTscore'] > cut_val)]))/float(len(df[(df['sample'] == cur_mode) & (df['valid'] == True)])))
    
    fig, ax = plt.subplots(figsize=(12,8))
    
    for cur_mode in mode_names:
      plt.plot(cut_vals, eff[cur_mode], label=cur_mode)
         
    ax.tick_params(axis='both', which='major', labelsize=25)
    plt.xlim(0,1)
    plt.xlabel("BDT score",fontsize=30)
    plt.ylabel("Efficiency",fontsize=30)
    #plt.yscale('log')
    ymin,ymax = plt.ylim()
    plt.ylim(ymin,1.3)
    plt.legend(fontsize=20, loc="best")
    plt.grid(alpha=0.4,which="both")
    ax.set_title(r'$\textbf{\textit{FCC-ee}}$ $\textbf{\textit{Simulation}}$', fontsize=16, loc='left')
    ax.set_title(label, fontsize=16, loc='right')
    plt.tight_layout()
    print("------>Plotting efficiency")
    plt.savefig(f"{loc.PLOTS}/efficiency.png")
    plt.savefig(f"{loc.PLOTS}/efficiency.pdf")
    plt.savefig(f"{loc.PLOTS}/efficiency.eps")
    plt.close()


def main():
    modes = ["mumuH","ZZ","WWmumu","Zll","egamma","gammae","gaga_mumu"]
    df = load_data()
    print_input_summary(df, mode_names)
    bdt = load_trained_model(loc)
    df = evaluate_bdt_model(df, bdt, train_vars)
    results, epochs, x_axis, best_iteration = get_performance_metrics(bdt)
    plot_metrics(df,bdt,train_vars,results, epochs, x_axis, best_iteration,mode_names,latex_mapping,final_states)


if __name__ == "__main__":
    main()


