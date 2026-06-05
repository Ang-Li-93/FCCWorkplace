import uproot
import numpy as np
import matplotlib.pyplot as plt

# open both samples
f_sig = uproot.open("analysis/Hbs/mumu/ROOT_Files/wzp6_ee_mumuH_Hbs_ecm240/chunk0.root")
f_bkg = uproot.open("analysis/Hbs/mumu/ROOT_Files/wzp6_ee_mumuH_Hbb_ecm240/chunk0.root")
f_bb  = uproot.open("analysis/Hbs/mumu/ROOT_Files/wzp6_ee_mumuH_ecm240/chunk0.root")

branches = ["zll_m", "zll_recoil_m", "higgs_m", "btag_max", "stag_other"]

d_sig = f_sig["events"].arrays(branches, library="np")
d_bkg = f_bkg["events"].arrays(branches, library="np")
d_bb  = f_bb["events"].arrays(branches, library="np")

outdir="/afs/cern.ch/user/d/dduan/private/FCCWorkplace/visualize_graphs/"

labels = {
    "zll_m": "m_{ll} [GeV]",
    "zll_recoil_m": "Recoil mass [GeV]",
    "higgs_m": "Higgs mass [GeV]",
    "btag_max": "max b-tag score",
    "stag_other": "other s-tag score",
}

for var in branches:
    fig, ax = plt.subplots()
    bins = np.linspace(min(d_sig[var].min(), d_bkg[var].min()),
                       max(d_sig[var].max(), d_bkg[var].max()), 50)

    ax.hist(d_sig[var], bins=bins, density=True, histtype="step", label="H→bs", color="magenta")
    ax.hist(d_bkg[var], bins=bins, density=True, histtype="step", label="ZH (inclusive)", color="red")
    ax.hist(d_bb[var],  bins=bins, density=True, histtype="step", label="H→bb", color="orange")

    ax.set_xlabel(labels[var])
    ax.set_ylabel("Normalised to unit area")
    ax.legend()
    fig.savefig(f"{outdir}{var}_normalised.png")
    plt.close(fig)

