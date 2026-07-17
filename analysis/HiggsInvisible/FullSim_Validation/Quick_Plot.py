import ROOT

ROOT.gROOT.SetBatch(True)

# Open the ROOT files
file1 = ROOT.TFile.Open("/afs/cern.ch/work/l/lia/private/FCC/FCCWorkplace/outputs_HInvjj/test2/output_wzp6.root")
file2 = ROOT.TFile.Open("/afs/cern.ch/work/l/lia/private/FCC/FCCWorkplace/outputs_HInvjj/test2/output_p8.root")

# Get the TTrees
tree1 = file1.Get("events")
tree2 = file2.Get("events")

# Define variables and create histograms
variables = ["jets_pt",
            "jets_y",
            "jets_p",
            "jets_e",
            "ZBosonPt",
            "ZBosonMass",
            #"MET",
            "recoil_M",
            #"Z_MC_no",
            "Z_MC_m",
            "Z_MC_p",
            ]
#variables = ["z_pt", "z_m", "h_pt", "h_m", "ht_pt", "ht_m"]
histograms1 = {}
histograms2 = {}

for var in variables:
    histograms1[var] = ROOT.TH1F(f"hist1_{var}", f"{var}; {var}; Events", 50, 0, 200)
    histograms2[var] = ROOT.TH1F(f"hist2_{var}", f"{var}; {var}; Events", 50, 0, 200)

# Fill the histograms
for event in tree1:
    for var in variables:
        values = getattr(event, var)
        for value in values:
            histograms1[var].Fill(value)

for event in tree2:
    for var in variables:
        values = getattr(event, var)
        for value in values:
            histograms2[var].Fill(value)

# Normalize the histograms to one
for var in variables:
    if histograms1[var].Integral() != 0:
        histograms1[var].Scale(1.0 / histograms1[var].Integral())
    if histograms2[var].Integral() != 0:
        histograms2[var].Scale(1.0 / histograms2[var].Integral())

# Create a canvas to draw the histograms and the ratio plots
canvas = ROOT.TCanvas("canvas", "Comparing Trees", 800, 800)
pad1 = ROOT.TPad("pad1", "pad1", 0, 0.35, 1, 1)  # Increase bottom margin of pad1
pad1.SetBottomMargin(0.03)
pad1.Draw()
pad2 = ROOT.TPad("pad2", "pad2", 0, 0, 1, 0.35)  # Increase top margin of pad2
pad2.SetTopMargin(0.1)
pad2.SetBottomMargin(0.3)
pad2.Draw()

# Draw the histograms using a loop
for var in variables:
    pad1.cd()
    pad1.Clear()

    histograms1[var].SetLineColor(ROOT.kRed)
    histograms2[var].SetLineColor(ROOT.kBlue)
    histograms1[var].SetStats(0)
    histograms2[var].SetStats(0)
    histograms1[var].Draw()
    histograms2[var].Draw("SAME")

    legend = ROOT.TLegend(0.75, 0.75, 0.9, 0.9)
    legend.AddEntry(histograms1[var], "wzp6", "l")
    legend.AddEntry(histograms2[var], "p8", "l")
    legend.Draw()

    # Draw the ratio plot
    pad2.cd()
    pad2.Clear()

    ratio_hist = histograms1[var].Clone(f"ratio_{var}")
    ratio_hist.SetLineColor(ROOT.kBlack)
    ratio_hist.SetTitle("")
    ratio_hist.Divide(histograms2[var])
    ratio_hist.GetYaxis().SetTitle("Ratio wzp6/p8")
    ratio_hist.GetYaxis().SetNdivisions(505)
    ratio_hist.GetYaxis().SetTitleSize(20)
    ratio_hist.GetYaxis().SetTitleFont(43)
    ratio_hist.GetYaxis().SetTitleOffset(1.55)
    ratio_hist.GetYaxis().SetLabelFont(43)
    ratio_hist.GetYaxis().SetLabelSize(15)
    ratio_hist.GetXaxis().SetTitleSize(20)
    ratio_hist.GetXaxis().SetTitleFont(43)
    ratio_hist.GetXaxis().SetTitleOffset(4.0)
    ratio_hist.GetXaxis().SetLabelFont(43)
    ratio_hist.GetXaxis().SetLabelSize(15)
    ratio_hist.Draw("ep")

    # Update the canvas to display the plots
    canvas.Update()
    canvas.Draw()

    # Save the canvas as an image file with variable name in the file name
    canvas.SaveAs(f"Compare/comparison_{var}.png")
    canvas.SaveAs(f"Compare/comparison_{var}.pdf")

# Close the ROOT files
file1.Close()
file2.Close()