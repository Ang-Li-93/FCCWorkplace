import uproot
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

f = uproot.open("/afs/cern.ch/user/d/dduan/private/FCCWorkplace/analysis/Hbs/mumu/ROOT_Files/wzp6_ee_mumuH_Hbs_ecm240/chunk0.root")
outdir = "/afs/cern.ch/user/d/dduan/private/FCCWorkplace/analysis/Hbs/mumu/sb_jet_efficiency_plots/"

branches = ["jet1_btag", "jet1_stag", "jet1_theta", "jet1_phi",
            "jet2_btag", "jet2_stag", "jet2_theta", "jet2_phi",
            "gen_b_theta", "gen_b_phi","gen_s_theta", "gen_s_phi",
            "btag_max", "stag_other"]

data = f["events"].arrays(branches, library="np")

#b jet efficiency
working_point = 0.7

# delta R matching
d_theta1 = data["jet1_theta"] - data["gen_b_theta"]
d_phi1 = (data["jet1_phi"] - data["gen_b_phi"] + np.pi) % (2 * np.pi) - np.pi
dR_1 = np.sqrt(d_theta1**2 + d_phi1**2)

d_theta2 = data["jet2_theta"] - data["gen_b_theta"]
d_phi2 = (data["jet2_phi"] - data["gen_b_phi"] + np.pi) % (2 * np.pi) - np.pi
dR_2 = np.sqrt(d_theta2**2 + d_phi2**2)

#assigns index depending on which jet has the lower deltaR and higher tagging score
dR_index   = np.where(dR_1 < dR_2, 0, 1)
btag_index = np.where(data["jet1_btag"] < data["jet2_btag"], 1, 0)

#if dR_1<dR_2, then dR_index = 0, and matched_stag puts the data from jet 1 as an s-jet for that event.
#We then limit that dR_index and stag_index point to the same jet as being matched
matched_btag    = np.where(dR_index == 0, data["jet1_btag"], data["jet2_btag"])
b_matched_correct = btag_index == dR_index
#matched_mask    = np.minimum(dR_1, dR_2) < 0.4

b_good = b_matched_correct #& matched_mask

# efficiency curve
thresholds = np.linspace(0, 1, 200)
b_eff = [np.mean(matched_btag[b_good] > t) for t in thresholds]
eps_b = np.mean(matched_btag[b_good] > working_point)
print(f"ε_b at WP={working_point}: {eps_b:.3f}")

#s jet efficiency

# delta R matching
d_theta1 = data["jet1_theta"] - data["gen_s_theta"]
d_phi1 = (data["jet1_phi"] - data["gen_s_phi"] + np.pi) % (2 * np.pi) - np.pi
dR_1 = np.sqrt(d_theta1**2 + d_phi1**2)

d_theta2 = data["jet2_theta"] - data["gen_s_theta"]
d_phi2 = (data["jet2_phi"] - data["gen_s_phi"] + np.pi) % (2 * np.pi) - np.pi
dR_2 = np.sqrt(d_theta2**2 + d_phi2**2)

#assigns index depending on which jet has the lower deltaR and higher tagging score
dR_index   = np.where(dR_1 < dR_2, 0, 1)
stag_index = np.where(data["jet1_stag"] < data["jet2_stag"], 1, 0)

#if dR_1<dR_2, then dR_index = 0, and matched_stag puts the data from jet 1 as an s-jet for that event.
#We then limit that dR_index and stag_index point to the same jet as being matched
matched_stag    = np.where(dR_index == 0, data["jet1_stag"], data["jet2_stag"])
s_matched_correct = stag_index == dR_index
#matched_mask    = np.minimum(dR_1, dR_2) < 0.4

s_good = s_matched_correct #& matched_mask

# efficiency curve
thresholds = np.linspace(0, 1, 200)
s_eff = [np.mean(matched_stag[s_good] > t) for t in thresholds]
eps_s = np.mean(matched_stag[s_good] > working_point)
print(f"ε_s at WP={working_point}: {eps_s:.3f}")

# joint efficiency
both_good = b_good & s_good  # events where BOTH jets are correctly matched

bt_thresholds = np.linspace(0, 1, 50)
st_thresholds = np.linspace(0, 1, 50)

joint_eff_2d = np.zeros((len(bt_thresholds), len(st_thresholds)))

for i, bt in enumerate(bt_thresholds):
    for j, st in enumerate(st_thresholds):
        joint_eff_2d[i, j] = np.mean(
            (matched_btag[both_good] > bt) & (matched_stag[both_good] > st)
        )


#Plotting

#b tag score
fig1, ax1 = plt.subplots(figsize=(6, 4))

ax1.hist(matched_btag[b_good], bins=50, range=(0, 1))
ax1.set_xlabel("b-tag score")
ax1.set_ylabel("events")
ax1.set_title("truth-matched b-tag score distribution")

fig1.tight_layout()
fig1.savefig(f"{outdir}btag_score_distribution.png")
plt.close(fig1)

#WP thresholds vs ε_b
fig2, ax2 = plt.subplots(figsize=(6, 4))

ax2.plot(thresholds, b_eff)
ax2.axvline(working_point, color='red', linestyle='--', 
            label=f'WP = {working_point} (ε_b={eps_b:.2f})')
ax2.set_xlabel("WP threshold")
ax2.set_ylabel("ε_b")
ax2.set_title("b-jet efficiency curve")
ax2.legend()
ax2.grid(True)

fig2.tight_layout()
fig2.savefig(f"{outdir}btag_efficiency_curve.png")
plt.close(fig2)

#s jet plots
fig3, ax3 = plt.subplots(figsize=(6, 4))
ax3.hist(matched_stag[s_good], bins=50, range=(0, 1))
ax3.set_xlabel("s-tag score")
ax3.set_ylabel("events")
ax3.set_title("truth-matched s-tag score distribution")

fig3.tight_layout()
fig3.savefig(f"{outdir}stag_score_distribution.png")
plt.close(fig3)

#WP thresholds vs ε_s
fig4, ax4 = plt.subplots(figsize=(6, 4))
ax4.plot(thresholds, s_eff)
ax4.axvline(working_point, color='red', linestyle='--', 
            label=f'WP = {working_point} (ε_s={eps_s:.2f})')
ax4.set_xlabel("WP threshold")
ax4.set_ylabel("ε_s")
ax4.set_title("s-jet efficiency curve")
ax4.legend()
ax4.grid(True)

fig4.tight_layout()
fig4.savefig(f"{outdir}stag_efficiency_curve.png")
plt.close(fig4)

#2D btag to stag for each jet
fig5, ax5 = plt.subplots(figsize=(6, 4))
h = ax5.hist2d(
    data["jet1_btag"],
    data["jet1_stag"],
    bins=10,
    range=[[0, 1], [0, 1]],
    cmap="turbo",
    #norm=mcolors.LogNorm()
)

fig5.colorbar(h[3], ax=ax5, label="events")
ax5.set_xlabel("Jet1 b-tag score")
ax5.set_ylabel("Jet1 s-tag score")
ax5.set_title("b-tag vs s-tag")

fig5.tight_layout()
fig5.savefig(f"{outdir}Jet1_btag_stag_2d.png")
plt.close(fig5)

fig6, ax6 = plt.subplots(figsize=(6, 4))
h = ax6.hist2d(
    data["jet2_btag"],
    data["jet2_stag"],
    bins=10,
    range=[[0, 1], [0, 1]],
    cmap="turbo",
    #norm=mcolors.LogNorm()
)

fig6.colorbar(h[3], ax=ax6, label="events")
ax6.set_xlabel("Jet2 b-tag score")
ax6.set_ylabel("Jet2 s-tag score")
ax6.set_title("b-tag vs s-tag")

fig6.tight_layout()
fig6.savefig(f"{outdir}Jet2_btag_stag_2d.png")
plt.close(fig6)

#Joint Efficiency
fig7, ax7 = plt.subplots(figsize=(6, 4))
im = ax7.imshow(
    joint_eff_2d, 
    origin='lower', 
    aspect='auto',
    extent=[0, 1, 0, 1], cmap='turbo'
)
ax7.axvline(0.7, color='red', linestyle='--', label='btag WP=0.7')
ax7.axhline(0.7, color='orange', linestyle='--', label='stag WP=0.7')
fig7.colorbar(im, ax=ax7, label='joint efficiency')
ax7.set_xlabel('btag threshold')
ax7.set_ylabel('stag threshold')
ax7.set_title('joint b+s tagging efficiency')
ax7.legend()

fig7.tight_layout()
fig7.savefig(f"{outdir}joint_efficiency_2d.png")
plt.close(fig7)

#btag max plots
fig8, ax8 = plt.subplots(figsize=(6, 4))
ax8.hist(data["btag_max"], bins=50, range=(0, 1))
ax8.set_xlabel("b-tag max")
ax8.set_ylabel("events")
ax8.set_title("maximum b-tag score between 2 jets in an event")

fig8.tight_layout()
fig8.savefig(f"{outdir}max_btag_score_distribution.png")
plt.close(fig8)

#stag other plots
fig9, ax9 = plt.subplots(figsize=(6, 4))
ax9.hist(data["stag_other"], bins=50, range=(0, 1))
ax9.set_xlabel("s-tag other")
ax9.set_ylabel("events")
ax9.set_title("other stag score between 2 jets in an event")

fig9.tight_layout()
fig9.savefig(f"{outdir}other_stag_score_distribution.png")
plt.close(fig9)






