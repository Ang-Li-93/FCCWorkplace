#!/usr/bin/env python3
"""
Cross-check for the referee: muon cone-isolation built from pseudorapidity (eta, old
nominal) vs polar angle (theta, new). Reads one winter2023 ZH(mumu) sample over xrootd,
computes BOTH isolations on the *same* selected leptons with identical cone radii
(dr_min=0.01, dr_max=0.5), and reports:
  - per-lepton isolation distributions (eta vs theta) and their difference,
  - the PRIMARY impact number: the fraction of events whose sel_isol(0.25) decision
    flips between the two metrics (normalized to events with >=1 muon to isolate),
  - the net selected-event yield change (secondary; quoted "of all events").

Run inside the FCCAnalyses env:  source env.sh ; python iso_eta_vs_theta.py
"""
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

# load the FCCAnalyses analyzers (lib + headers) so the RDF JIT knows the functions
# (fccanalysis run does this automatically; a bare python run must do it explicitly)
ROOT.gSystem.Load("libFCCAnalyses")
ROOT.gInterpreter.Declare('#include "FCCAnalyses/ReconstructedParticle.h"')
ROOT.gInterpreter.Declare('#include "FCCAnalyses/HiggsTools.h"')

# one winter2023 sample file, read via xrootd (no /eos mount needed on SDCC)
INFILE = ("root://eospublic.cern.ch//eos/experiment/fcc/ee/generation/DelphesEvents/"
          "winter2023/IDEA/wzp6_ee_mumuH_ecm240/events_017670037.root")
ISO_CUT = 0.25   # nominal sel_isol threshold

ROOT.EnableImplicitMT()

df = ROOT.RDataFrame("events", INFILE)

df = (
    df
    .Alias("Lepton0", "Muon#0.index")
    # bare muons, then the nominal pT>20 selection used in stage1
    .Define("leps_all", "FCCAnalyses::ReconstructedParticle::get(Lepton0, ReconstructedParticles)")
    .Define("leps", "FCCAnalyses::ReconstructedParticle::sel_p(20)(leps_all)")
    # the two isolations on the SAME leptons: eta-based (nominal) vs theta-based (new)
    .Define("leps_iso_eta", "HiggsTools::coneIsolation(0.01, 0.5)(leps, ReconstructedParticles)")
    .Define("leps_iso_th",  "HiggsTools::coneIsolationTheta(0.01, 0.5)(leps, ReconstructedParticles)")
    .Define("leps_iso_diff", "leps_iso_th - leps_iso_eta")
    # selected-lepton counts under each metric (event passes if >=1 isolated lepton)
    .Define("nsel_eta", "HiggsTools::sel_isol(%g)(leps, leps_iso_eta).size()" % ISO_CUT)
    .Define("nsel_th",  "HiggsTools::sel_isol(%g)(leps, leps_iso_th).size()"  % ISO_CUT)
    .Define("pass_eta", "leps.size() >= 1 && nsel_eta > 0")
    .Define("pass_th",  "leps.size() >= 1 && nsel_th  > 0")
)

# histograms (per-lepton iso) and the difference
h_eta  = df.Histo1D(("h_eta",  "cone iso;isolation;leptons", 100, 0.0, 1.0), "leps_iso_eta")
h_th   = df.Histo1D(("h_th",   "cone iso;isolation;leptons", 100, 0.0, 1.0), "leps_iso_th")
h_diff = df.Histo1D(("h_diff", "iso(#theta) - iso(#eta);#Delta isolation;leptons", 400, -1.0, 1.0), "leps_iso_diff")

# event yields
n_tot   = df.Count()
n_mu    = df.Filter("leps.size() >= 1").Count()   # events with a muon the cut can act on
n_eta   = df.Filter("pass_eta").Count()
n_th    = df.Filter("pass_th").Count()
# events where the two metrics disagree on the selection decision (immune to denominator)
n_flip  = df.Filter("pass_eta != pass_th").Count()
# directional split of the flips
n_flip_eta_only = df.Filter("pass_eta && !pass_th").Count()   # eta-pass -> theta-fail
n_flip_th_only  = df.Filter("!pass_eta && pass_th").Count()   # theta-pass -> eta-fail

ntot = n_tot.GetValue()
nmu  = n_mu.GetValue()
neta = n_eta.GetValue()
nth  = n_th.GetValue()
nflip = n_flip.GetValue()
nflip_eo = n_flip_eta_only.GetValue()
nflip_to = n_flip_th_only.GetValue()

# diff-histogram overflow check (forward-lepton tail must not be buried)
under = h_diff.GetBinContent(0)
over  = h_diff.GetBinContent(h_diff.GetNbinsX() + 1)

print("\n================ eta vs theta isolation =================")
print("input               : %s" % INFILE)
print("events processed     : %d" % ntot)
print("events w/ >=1 muon   : %d   (nmu/ntot = %.4f%%)" % (nmu, 100.0*nmu/ntot if ntot else 0))
print("--- PRIMARY: selection-decision flips (eta != theta) ---")
print("flips                : %d events" % nflip)
print("  flip fraction (of muon events) : %.4f%%" % (100.0*nflip/nmu if nmu else 0))
print("  flip fraction (of all events)  : %.4f%%" % (100.0*nflip/ntot if ntot else 0))
print("  directional: eta-pass->theta-fail = %d , theta-pass->eta-fail = %d" % (nflip_eo, nflip_to))
print("--- SECONDARY: net selected-yield change (of all events) ---")
print("selected (eta)       : %d  (%.4f%% of all)" % (neta, 100.0*neta/ntot if ntot else 0))
print("selected (theta)     : %d  (%.4f%% of all)" % (nth,  100.0*nth/ntot   if ntot else 0))
print("net yield delta      : %d events  (%.4f%% of selected)" %
      (nth-neta, 100.0*(nth-neta)/neta if neta else 0))
print("--- per-lepton isolation ---")
print("mean iso(eta)        : %.6f" % h_eta.GetMean())
print("mean iso(theta)      : %.6f" % h_th.GetMean())
print("mean iso diff        : %.2e  (rms %.2e)" % (h_diff.GetMean(), h_diff.GetRMS()))
ndiff = h_diff.GetEntries()
print("diff hist under/over : %g / %g  (%.3f%% of leptons in the |#Delta|>1 forward tail)"
      % (under, over, 100.0*(under+over)/ndiff if ndiff else 0))
print("=========================================================\n")

# overlay plot — zoom to the populated region and show the 0.25 selection cut
c = ROOT.TCanvas("c", "", 900, 700)
c.SetLogy()
h_eta.SetLineColor(ROOT.kBlue+1); h_eta.SetLineWidth(2)
h_th.SetLineColor(ROOT.kRed+1);   h_th.SetLineWidth(2); h_th.SetLineStyle(2)
h_eta.GetXaxis().SetRangeUser(0.0, 0.4)
h_eta.Draw("hist")
h_th.Draw("hist same")
ROOT.gPad.Update()
cut = ROOT.TLine(0.25, ROOT.gPad.GetUymin(), 0.25, 10**ROOT.gPad.GetUymax())
cut.SetLineColor(ROOT.kGray+2); cut.SetLineStyle(2); cut.SetLineWidth(2); cut.Draw()
leg = ROOT.TLegend(0.55, 0.72, 0.88, 0.88)
leg.AddEntry(h_eta.GetValue(), "#DeltaR(#eta) [old nominal]", "l")
leg.AddEntry(h_th.GetValue(),  "#DeltaR(#theta) [new]",       "l")
leg.AddEntry(cut, "sel_isol cut = 0.25", "l")
leg.Draw()
c.SaveAs("iso_eta_vs_theta_overlay.png")
c.SaveAs("iso_eta_vs_theta_overlay.pdf")

c2 = ROOT.TCanvas("c2", "", 900, 700)
c2.SetLogy()
# fold under/overflow into the visible edge bins so the forward tail isn't hidden
nb = h_diff.GetNbinsX()
h_diff.SetBinContent(1,  h_diff.GetBinContent(1)  + h_diff.GetBinContent(0))
h_diff.SetBinContent(nb, h_diff.GetBinContent(nb) + h_diff.GetBinContent(nb + 1))
h_diff.SetBinContent(0, 0); h_diff.SetBinContent(nb + 1, 0)
h_diff.SetLineColor(ROOT.kBlack); h_diff.SetLineWidth(2)
h_diff.Draw("hist")
note = ROOT.TLatex(); note.SetNDC(); note.SetTextSize(0.03)
note.DrawLatex(0.14, 0.85, "edge bins include overflow (forward tail)")
c2.SaveAs("iso_eta_vs_theta_diff.png")

print("Wrote: iso_eta_vs_theta_overlay.{png,pdf}, iso_eta_vs_theta_diff.png")
