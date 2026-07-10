import uproot
import numpy as np
import matplotlib.pyplot as plt

samples = {
    "H→bs (signal)":   "analysis/Hbs/mumu/ROOT_Files/wzp6_ee_mumuH_Hbs_ecm240/chunk0.root",
    "ZH (inclusive)":   "analysis/Hbs/mumu/ROOT_Files/wzp6_ee_mumuH_ecm240/chunk0.root",
    "ZZ":               "analysis/Hbs/mumu/ROOT_Files/p8_ee_ZZ_ecm240/chunk0.root",
    "WW→μμ":           "analysis/Hbs/mumu/ROOT_Files/p8_ee_WW_mumu_ecm240/chunk0.root",
    "Z/γ→μμ":          "analysis/Hbs/mumu/ROOT_Files/wzp6_ee_mumu_ecm240/chunk0.root",
    "eγ→eZ→μμ":       "analysis/Hbs/mumu/ROOT_Files/wzp6_egamma_eZ_Zmumu_ecm240/chunk0.root",
    "γe→eZ→μμ":       "analysis/Hbs/mumu/ROOT_Files/wzp6_gammae_eZ_Zmumu_ecm240/chunk0.root",
    "γγ→μμ":           "analysis/Hbs/mumu/ROOT_Files/wzp6_gaga_mumu_60_ecm240/chunk0.root",
}

colors = {
    "H→bs (signal)":   "magenta",
    "ZH (inclusive)":   "red",
    "ZZ":               "green",
    "WW→μμ":           "blue",
    "Z/γ→μμ":          "cyan",
    "eγ→eZ→μμ":       "springgreen",
    "γe→eZ→μμ":       "darkgreen",
    "γγ→μμ":           "slateblue",
}

branches = ["zll_m", "zll_recoil_m", "higgs_m", "btag_max", "stag_other"]

data = {}
for name, path in samples.items():
    f = uproot.open(path)
    data[name] = f["events"].arrays(branches, library="np")

outdir = "/afs/cern.ch/user/d/dduan/private/FCCWorkplace/block_visualized_graphs/"

labels = {
    "zll_m": "m_{ll} [GeV]",
    "zll_recoil_m": "Recoil mass [GeV]",
    "higgs_m": "Higgs mass [GeV]",
    "btag_max": "max b-tag score",
    "stag_other": "other s-tag score",
}

for var in branches:
    fig, ax = plt.subplots()

    all_vals = np.concatenate([d[var] for d in data.values()])
    bins = np.linspace(all_vals.min(), all_vals.max(), 50)

    heights = {}
    for name, d in data.items():
        h, _ = np.histogram(d[var], bins=bins, density=True)
        heights[name] = h.max()

    sorted_names = sorted(heights, key=heights.get, reverse=True)

    for name in sorted_names:
        ax.hist(data[name][var], bins=bins, density=True,
                histtype="stepfilled", label=name,
                color=colors[name], alpha=1)
        #ax.hist(data[name][var], bins=bins, density=True,
                #histtype="step", color=colors[name])

    ax.set_xlabel(labels[var])
    ax.set_ylabel("Normalised to unit area")
    ax.legend(fontsize=7)
    fig.savefig(f"{outdir}{var}_normalised.png")
    plt.close(fig)