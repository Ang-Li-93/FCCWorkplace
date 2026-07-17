import os
import ROOT
import atlasplots as aplt

path_PS = "/afs/cern.ch/work/l/lia/private/FCC/FCCWorkplace/outputs_HInvjj/stage1/test/output_p8.root"
path_noPS = "/afs/cern.ch/work/l/lia/private/FCC/FCCWorkplace/outputs_HInvjj/stage1/test/output_wzp6.root"

outDir = './test'
histos = {}

# Define variables with specific binning
variable_binning = {
    'jet_pt': (100, 0, 500),
    'z_pt': (100, 0, 500),
    'z_m': (100, 0, 500),
    'h_pt': (100, 0, 500),
    'h_m': (100, 0, 500),
}

colors = [ROOT.kRed+1, ROOT.kBlue+1, ROOT.kMagenta+1, ROOT.kOrange+1, ROOT.kYellow+1, ROOT.kCyan+1, ROOT.kGreen+1]

if not os.path.exists(outDir): os.makedirs(outDir)
# Preselection
df_PS = ROOT.RDataFrame("events", path_PS)
df_noPS = ROOT.RDataFrame("events", path_noPS)

# Setup style
ROOT.gROOT.SetBatch()
aplt.set_atlas_style()

for cur_var, (n_bins, min_bin, max_bin) in variable_binning.items():
    print(f"---->Working on the variable {cur_var}")
    
    # Initialize the plotting
    fig, (ax1, ax2) = aplt.ratio_plot(name=f"fig_{cur_var}", figsize=(800, 800), hspace=0.05)
    
    h_PS = df_PS.Histo1D(ROOT.RDF.TH1DModel(f"{cur_var}", f"{cur_var}", n_bins, min_bin, max_bin), f"{cur_var}", "weight")
    h_noPS = df_noPS.Histo1D(ROOT.RDF.TH1DModel(f"{cur_var}", f"{cur_var}", n_bins, min_bin, max_bin), f"{cur_var}", "weight")
    
    histo_PS = h_PS.GetValue().Clone()
    histo_noPS = h_noPS.GetValue().Clone()
    
    histo_PS.Scale(1./histo_PS.Integral())
    histo_noPS.Scale(1./histo_noPS.Integral())
    
    # Calculate the mean values
    mean_PS = histo_PS.GetMean()
    mean_noPS = histo_noPS.GetMean()
    
    # Plot the histograms
    ax1.plot(histo_PS, label="p8", linecolor=ROOT.kBlue+1, labelfmt="L")
    ax1.plot(histo_noPS, label="wzp6", linecolor=ROOT.kBlack+1, labelfmt="L")
    
    # Calculate and draw the ratio
    ratio_hist = histo_PS.Clone(f"ratio_{cur_var}")
    ratio_hist.Divide(histo_noPS)
    ax2.plot(ratio_hist, linecolor=ROOT.kBlack)
    
    # Set y-axis range for the ratio plot
    ax2.set_ylim(0, 2)
    
    # Draw line at y=1 in ratio panel
    line = ROOT.TLine(ax1.get_xlim()[0], 1, ax1.get_xlim()[1], 1)
    ax2.plot(line)
    
    # Add margins and axis titles
    ax1.add_margins(top=0.16)
    ax2.add_margins(top=0.1, bottom=0.1)
    ax2.set_xlabel(f"{cur_var}")
    ax1.set_ylabel("Normalised to unity")
    ax2.set_ylabel("p8 / wzp6", loc="centre")
    
    # Add the ATLAS Label
    ax1.cd()
    #aplt.atlas_label(text="Internal", loc="upper left")
    ax1.text(0.2, 0.84, "#sqrt{s} = 240 GeV, 10.8 fb^{-1}", size=22, align=13)
    #ax1.text(0.2, 0.76, f"Mean (with PS) = {mean_PS:.2f}", size=22, align=13, color=ROOT.kBlue+1)
    #ax1.text(0.2, 0.71, f"Mean (w/o PS) = {mean_noPS:.2f}", size=22, align=13, color=ROOT.kBlack+1)
    
    # Add legend
    ax1.legend(loc=(0.75, 0.75, 1 - ROOT.gPad.GetRightMargin() - 0.05, 1 - ROOT.gPad.GetTopMargin() - 0.05))
    
    # Save the plot in both PDF and PNG formats
    fig.savefig(os.path.join(outDir, f"Compare_{cur_var}.pdf"))
    fig.savefig(os.path.join(outDir, f"Compare_{cur_var}.png"))
