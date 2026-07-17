import uproot
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

outdir = "/eos/user/d/dduan/FCCee/Hbs/mumu/"

corr_vars = [
    "met_p", "met_pt", "met_theta", "met_phi",
    "met_px", "met_py", "met_pz",
    "higgs_met_m", "higgs_met_e",
    "total_m", "total_e",
    "zll_m", "zll_p", "zll_theta",
    "zll_recoil_m",
    "leading_zll_lepton_p", "leading_zll_lepton_theta",
    "subleading_zll_lepton_p", "subleading_zll_lepton_theta",
    "zll_leptons_acolinearity", "zll_leptons_acoplanarity",
    "higgs_m",
    "jet1_p", "jet1_theta", "jet1_phi", "jet1_mass",
    "jet2_p", "jet2_theta", "jet2_phi", "jet2_mass",
    "jet1_btag", "jet2_btag",
    "jet1_stag", "jet2_stag",
    "btag_max", "stag_other",
    "cosTheta_miss",
]

# open the ROOT file, grab the events tree, load as pandas dataframe
f = uproot.open("/eos/user/d/dduan/FCCee/Hbs/mumu/firstlook/wzp6_ee_mumuH_Hbs_W4p1MeV_ecm240/chunk_0.root")
df_signal = f["events"].arrays(corr_vars, library="pd")

# now just
corr_matrix = df_signal.corr()

# 2. Set up a large matplotlib figure so 37 variables actually fit
plt.figure(figsize=(18, 14))

# 3. Draw the heatmap
sns.heatmap(
    corr_matrix,
    cmap="coolwarm",  # Perfect diverging scale for -1 (blue) to 1 (red)
    vmin=-1,
    vmax=1,  # Forces the colorbar bounds
    square=True,  # Forces cells to be square shape
    linewidths=0.1,  # Puts a tiny white line between cells for readability
    xticklabels=True,
    yticklabels=True,  # Ensures all variable names show up
)

# 4. Clean up the formatting
plt.title("Feature Correlation Matrix (Signal)", fontsize=16, fontweight="bold")
plt.xticks(rotation=90, fontsize=9)
plt.yticks(rotation=0, fontsize=9)
plt.tight_layout()

# 5. SAVE THE PLOT (Replace plt.show() with this)
plt.savefig(
    f"{outdir}correlation_matrix.png",  # The filename and format (.png, .pdf, .svg)
    dpi=300,  # High resolution for publication-quality clarity
    bbox_inches="tight",  # CRITICAL: Prevents your 37 variable labels from being cut off
)

# Optional: Clear the current figure memory after saving
plt.close()