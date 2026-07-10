import uproot
import numpy as np
import matplotlib.pyplot as plt
import os
import glob 

outdir = "/eos/user/d/dduan/FCCee/Hbs/mumu/visualize_graphs/"

samples = {
    # Off-Diagonal Higgs Decay signals
    "H→bs (Signal)":    "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/wzp6_ee_mumuH_Hbs_W4p1MeV_ecm240",
    "H→bd (Signal)":    "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/wzp6_ee_mumuH_Hbd_W4p1MeV_ecm240",
    "H→cu (Signal)":    "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/wzp6_ee_mumuH_Hcu_W4p1MeV_ecm240",
    "H→sd (Signal)":    "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/wzp6_ee_mumuH_Hsd_W4p1MeV_ecm240",

    # Diagonal Higgs Decay signals
    "H→bb":                 "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/wzp6_ee_mumuH_Hbb_ecm240",
    "H→ss":                 "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/wzp6_ee_mumuH_Hss_ecm240",
    "H→cc":                 "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/wzp6_ee_mumuH_Hcc_ecm240",
    "H→dd":                 "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/wzp6_ee_mumuH_Hdd_ecm240",
    "H→uu":                 "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/wzp6_ee_mumuH_Huu_ecm240",

    # Other backgrounds
    "ZH (inclusive)":       "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/wzp6_ee_mumuH_ecm240",
    "ZZ":                   "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/p8_ee_ZZ_ecm240",
    "Z/γ→μμ":               "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/wzp6_ee_mumu_ecm240",
    "eγ→eZ→μμ":             "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/wzp6_egamma_eZ_Zmumu_ecm240",
    "γe→eZ→μμ":             "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/wzp6_gammae_eZ_Zmumu_ecm240",
    "γγ→μμ":                "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/wzp6_gaga_mumu_60_ecm240",
    'WW (inclusive)':       "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/p8_ee_WW_ecm240",
    "H→gg":                 "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/wzp6_ee_mumuH_Hgg_ecm240",

    #Old backgrounds/signals
    #"WW→μμ":                "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/p8_ee_WW_mumu_ecm240",
    #"H→bb (Signal)":    "/eos/user/d/dduan/FCCee/Hbs/mumu/batch_3/wzp6_ee_mumuH_Hbb_MEdecay_ecm240",

}                  

colors = {
    # Off-Diagonal Higgs Decay signals
    "H→bs (Signal)":        "black",
    "H→bd (Signal)":        "tomato",
    "H→cu (Signal)":        "sandybrown",
    "H→sd (Signal)":        "gold",

    # Diagonal Higgs Decay signals
    "H→bb":                 "darkorange",
    "H→ss":                 "crimson",
    "H→cc":                 "mediumslateblue",
    "H→uu":                 "lightcoral",
    "H→dd":                 "indianred",

    # Non-Higgs Backgrounds (Distinct cool, deep, and neutral tones)
    "ZH (inclusive)":       "indigo",
    "ZZ":                   "forestgreen",
    "WW (inclusive)":       "darkcyan",
    "Z/γ→μμ":               "turquoise",
    "eγ→eZ→μμ":             "khaki",
    "γe→eZ→μμ":             "olive",
    "γγ→μμ":                "slategray",

    #Old Signal/Backgrounds
    #"WW→μμ":                "dodgerblue",
    #"H→bb (final_state)":   "darkorchid",
}

branches = ["zll_m", "zll_p", "zll_recoil_m", "higgs_m", 
            "btag_max", "stag_other",
            #"total_m", "total_e", 
            "higgs_met_m", "higgs_met_e",
            "met_p", "met_pt", "met_theta", "met_phi",]

#Load all files
data = {}
for name, dir_path in samples.items():
    # Construct a search pattern for any .root files inside the directory or its subdirectories
    search_pattern = os.path.join(dir_path, "**/*.root")
    file_list = glob.glob(search_pattern, recursive=True)
    
    if not file_list:
        print(f"Warning: No .root files found in {dir_path}")
        continue
        
    print(f"Loading {len(file_list)} files for {name}...")
    
    # Target the 'events' tree inside every file paths in our list
    tree_paths = [f"{f}:events" for f in file_list]
    
    # Concatenate all trees directly into a dictionary of numpy arrays
    data[name] = uproot.concatenate(tree_paths, expressions=branches, library="np")

labels = {
    "zll_p": "p_{l^{+}l^{-}} [GeV]",
    "zll_m": "m_{ll} [GeV]",
    "zll_recoil_m": "Recoil mass [GeV]",
    "higgs_m": "Higgs mass [GeV]",
    "btag_max": "max b-tag score",
    "stag_other": "other s-tag score",
    "total_m": "Total reconstructed mass [GeV]",
    "total_e": "Total reconstructed energy [GeV]",
    "higgs_met_m": "Reconstructed Mass for jj+met",
    "higgs_met_e": "Reconstructed Energy for jj+met",

    "met_p": "MET Momentum",
    "met_pt": "MET Transverse Momentum",
    "met_theta": "MET Theta",
    "met_phi": "MET Phi",
}

xlims = {
    "zll_p": (20,70),
    "zll_m":        (86, 96),
    "higgs_m":      (100, 140),
    
    "btag_max":     (0, 1),
    "stag_other":   (0, 1),

    "zll_recoil_m": (120, 140),
    "total_m": (200, 260),
    "total_e": (200, 260),
    "higgs_met_m": (100,140),
    "higgs_met_e": (100,140),
    "met_p":   (0, 20),
    "met_pt":  (0, 50),
    "met_theta": (0, np.pi),
    "met_phi":   (-3.2, 3.2),
}

for var in branches:
    fig, ax = plt.subplots()

    low_lim, high_lim = xlims[var]

    if var == "btag_max" or var == "stag_other" or var == "met_theta":
        bins = np.linspace(low_lim, high_lim, 50)
    else:
        bins = np.arange(low_lim, high_lim + 0.5, 0.5)

    for name, d in data.items():
        ax.hist(d[var], bins=bins, range=(low_lim, high_lim),
                density=True, histtype="step",
                label=name, color=colors[name])

    ax.set_xlim(*xlims[var])
    ax.set_xlabel(labels[var])
    ax.set_ylabel("Normalised to unit area")
    ax.legend(fontsize=7)
    fig.savefig(f"{outdir}{var}_normalised.png")
    plt.close(fig)


#Cutflow
cutflow = {name: [] for name in data}

#Create mask and layer for each cut
for name, d in data.items():
    mask = np.ones(len(d[branches[0]]), dtype=bool)

    # Raw Events
    cutflow[name].append(mask.sum())  

    #Z-momentum cut
    mask &= (d["zll_p"] > 20) & (d["zll_p"] < 70)
    cutflow[name].append(mask.sum())

    #Cut on Z- mass
    mask &= (d["zll_m"] > 86) & (d["zll_m"] < 96)
    cutflow[name].append(mask.sum())

    #Cut on Recoil mass
    mask &= (d["zll_recoil_m"] > 120) & (d["zll_recoil_m"] < 140)
    cutflow[name].append(mask.sum())

steps = ["Preselection", "Z-Momentum Cut", "Z-Mass Cut", "Recoil Cut"]

#Total Decay Cutflow

fig, ax = plt.subplots(figsize=(8, 5))

#Loop and plot dictionary
# for name, counts in cutflow.items():
#     ax.plot(steps, counts, marker='o', label=name, color=colors[name], linewidth=2)

# Loop and plot percentages relative to Preselection
for name, counts in cutflow.items(): 
    initial_events = counts[0]
    if initial_events > 0:
        percentages = [(c / initial_events) * 100 for c in counts]
    else:
        percentages = [0] * len(counts)
        
    ax.plot(steps, percentages, marker='o', label=name, color=colors[name], linewidth=2)

ax.set_yscale("linear")
ax.set_ylabel("Percentage of Surviving Events")
ax.set_xlabel("Selection Stage")
ax.set_title("Analysis Cutflow Comparison")
ax.grid(True, which="both", linestyle="--", alpha=0.5)
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)

plt.tight_layout()
fig.savefig(f"{outdir}total_cutflow_plot.png")
plt.close(fig)

print("Total Cutflow plot successfully generated!")

#Total Decay Cutflow with relative percentages

fig, ax = plt.subplots(figsize=(8, 5))

# Loop through each sample/process in your cutflow dictionary
for name, counts_list in cutflow.items(): 
    percentages = []
    
    # Initialize previous_step to the first cut of THIS specific sample
    previous_step = counts_list[0] if len(counts_list) > 0 else 0
    
    for c in counts_list:
        if previous_step > 0:
            pct = (c / previous_step) * 100
            percentages.append(pct)
        else:
            percentages.append(0.0)
            
        # Update previous_step to the current step for the next iteration
        previous_step = c
        
    # Plot the full line for this sample
    ax.plot(steps, percentages, marker='o', label=name, color=colors[name], linewidth=2)

ax.set_yscale("linear")
ax.set_ylabel("Percentage of Surviving Events")
ax.set_xlabel("Selection Stage")
ax.set_title("Analysis Cutflow Comparison")
ax.grid(True, which="both", linestyle="--", alpha=0.5)
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)

plt.tight_layout()
fig.savefig(f"{outdir}relative%_cutflow_plot.png")
plt.close(fig)

print("Total Cutflow plot successfully generated!")


#Higgs Decays Cutflow Plot

higgs_decays = [
    "H→bs (Signal)", "H→bb (Signal)", "H→bd (Signal)", 
    "H→cu (Signal)", "H→sd (Signal)", "H→ss", "H→bb (final_state)"
]

fig, ax = plt.subplots(figsize=(8, 5))

#Loop and plot dictionary
# for name, counts in cutflow.items():
#     ax.plot(steps, counts, marker='o', label=name, color=colors[name], linewidth=2)

# Loop and plot percentages relative to Preselection
for name, counts in cutflow.items(): 
    if name not in higgs_decays:
        continue
    initial_events = counts[0]
    if initial_events > 0:
        percentages = [(c / initial_events) * 100 for c in counts]
    else:
        percentages = [0] * len(counts)
        
    ax.plot(steps, percentages, marker='o', label=name, color=colors[name], linewidth=2)

ax.set_yscale("linear")
ax.set_ylabel("Percentage of Surviving Events")
ax.set_xlabel("Selection Stage")
ax.set_title("Analysis Cutflow Comparison")
ax.grid(True, which="both", linestyle="--", alpha=0.5)
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)

plt.tight_layout()
fig.savefig(f"{outdir}higgs_cutflow_plot.png")
plt.close(fig)

print("Higgs Cutflow plot successfully generated!")


#Non-Higgs Backgrounds

other_backgrounds = [
    "ZH (inclusive)",
    "ZZ",
    "WW",
    "Z/γ→μμ",
    "eγ→eZ→μμ",
    "γe→eZ→μμ",
    "γγ→μμ",
    "WW (inclusive)"
]

fig, ax = plt.subplots(figsize=(8, 5))

#Loop and plot dictionary
# for name, counts in cutflow.items():
#     ax.plot(steps, counts, marker='o', label=name, color=colors[name], linewidth=2)

# Loop and plot percentages relative to 'Raw Events'
for name, counts in cutflow.items():
    if name not in other_backgrounds:
        continue
    initial_events = counts[0]
    if initial_events > 0:
        percentages = [(c / initial_events) * 100 for c in counts]
    else:
        percentages = [0] * len(counts)
        
    ax.plot(steps, percentages, marker='o', label=name, color=colors[name], linewidth=2)

ax.set_yscale("linear")
ax.set_ylabel("Percentage of Surviving Events")
ax.set_xlabel("Selection Stage")
ax.set_title("Analysis Cutflow Comparison")
ax.grid(True, which="both", linestyle="--", alpha=0.5)
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8) # Push legend outside

plt.tight_layout()
fig.savefig(f"{outdir}other_background_cutflow_plot.png")
plt.close(fig)

print("Other Background Cutflow plot successfully generated!")


#Table
fig, ax = plt.subplots(figsize=(16, 6))  # 1. Increased figure width (12 -> 16)
ax.axis('off')

steps = ["Preselection", "Z-Mass Cut", "Z-Momentum Cut", "Recoil Cut"]

table_data = [] 
for name, counts in cutflow.items():
    initial_events = counts[0]
    row = [name]
    for c in counts:
        pct = (c / initial_events * 100) if initial_events > 0 else 0.0
        row.append(f"{c}\n({pct:.2f}%)")
    table_data.append(row)

col_labels = ["Sample"] + steps

# 2. Calculate explicit, generous column widths
# Give the "Sample" column more space (e.g., 35% of width) and split the rest evenly
num_cols = len(col_labels)
col_widths = [0.32] + [0.17] * (num_cols - 1) 

table = ax.table(
    cellText=table_data,
    colLabels=col_labels,
    colWidths=col_widths, # 3. Pass the explicit widths here
    loc='center',
    cellLoc='center'
)

table.auto_set_font_size(False)
table.set_fontsize(9) # Slightly larger font since we have more room now

# 4. Scale the row heights (1.8x) so the stacked text doesn't overflow vertically
table.scale(1, 1.8) 

# 5. Apply a tight layout with padding so edges don't get clipped
plt.tight_layout(pad=2.0)

fig.savefig(f"{outdir}cutflow_table.png", bbox_inches='tight', dpi=150)
plt.close(fig)