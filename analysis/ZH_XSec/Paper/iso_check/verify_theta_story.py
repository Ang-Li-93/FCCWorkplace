#!/usr/bin/env python3
"""
Verify the *mechanism* behind the eta->theta isolation difference, not just its size.

Claim: dR_theta = sqrt(dTheta^2 + dPhi^2) vs dR_eta = sqrt(dEta^2 + dPhi^2). Since
|dEta| = |dTheta| / sin(theta), at forward angles (small sin theta) a fixed cone radius
spans a WIDER physical theta window in the theta-metric than in the eta-metric. So the
theta-cone captures more nearby activity for forward leptons -> larger isolation ->
forward muons are preferentially pushed ABOVE the 0.25 cut. Predictions, all testable
on the same sample:
  (1) per-lepton iso(theta) - iso(eta) grows toward |cos theta| -> 1 (forward),
  (2) leptons that cross the cut (iso_eta < 0.25 <= iso_theta) pile up at forward |cos theta|,
  (3) the crossing is one-directional: eta-pass->theta-fail >> theta-pass->eta-fail.

Run:  source env.sh (winter2023) ; python verify_theta_story.py
"""
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gSystem.Load("libFCCAnalyses")
ROOT.gInterpreter.Declare('#include "FCCAnalyses/ReconstructedParticle.h"')
ROOT.gInterpreter.Declare('#include "FCCAnalyses/HiggsTools.h"')

INFILE = ("root://eospublic.cern.ch//eos/experiment/fcc/ee/generation/DelphesEvents/"
          "winter2023/IDEA/wzp6_ee_mumuH_ecm240/events_017670037.root")
CUT = 0.25

ROOT.EnableImplicitMT()
df = (
    ROOT.RDataFrame("events", INFILE)
    .Alias("Lepton0", "Muon#0.index")
    .Define("leps_all", "FCCAnalyses::ReconstructedParticle::get(Lepton0, ReconstructedParticles)")
    .Define("leps", "FCCAnalyses::ReconstructedParticle::sel_p(20)(leps_all)")
    .Define("leps_iso_eta", "HiggsTools::coneIsolation(0.01, 0.5)(leps, ReconstructedParticles)")
    .Define("leps_iso_th",  "HiggsTools::coneIsolationTheta(0.01, 0.5)(leps, ReconstructedParticles)")
    .Define("leps_theta",   "FCCAnalyses::ReconstructedParticle::get_theta(leps)")
    # per-lepton derived quantities (RVecs, element-aligned)
    .Define("leps_abscos",  "ROOT::VecOps::abs(ROOT::VecOps::cos(leps_theta))")
    .Define("leps_iso_diff","ROOT::VecOps::RVec<double>(leps_iso_th) - ROOT::VecOps::RVec<double>(leps_iso_eta)")
    # threshold-crossers, both directions
    .Define("cross_e2t", "leps_iso_eta < %g && leps_iso_th >= %g" % (CUT, CUT))   # eta-pass -> theta-fail
    .Define("cross_t2e", "leps_iso_th  < %g && leps_iso_eta >= %g" % (CUT, CUT))   # theta-pass -> eta-fail
    .Define("abscos_e2t", "leps_abscos[cross_e2t]")
    .Define("abscos_t2e", "leps_abscos[cross_t2e]")
)

# (1) mean Delta-iso vs |cos theta|  (profile: expect rising toward 1)
prof = df.Profile1D(("prof", "mean #Delta iso vs |cos#theta|;|cos#theta|;<iso(#theta)-iso(#eta)>", 20, 0.0, 1.0),
                    "leps_abscos", "leps_iso_diff")
# 2D for context
h2 = df.Histo2D(("h2", "iso(#theta)-iso(#eta) vs |cos#theta|;|cos#theta|;#Delta iso", 50, 0.0, 1.0, 100, -0.1, 0.6),
                "leps_abscos", "leps_iso_diff")
# (2) |cos theta| of all leptons vs threshold-crossers
h_all  = df.Histo1D(("h_all",  "all leptons;|cos#theta|;leptons", 25, 0.0, 1.0), "leps_abscos")
h_e2t  = df.Histo1D(("h_e2t",  "eta-pass#rightarrow theta-fail;|cos#theta|;leptons", 25, 0.0, 1.0), "abscos_e2t")
h_t2e  = df.Histo1D(("h_t2e",  "theta-pass#rightarrow eta-fail;|cos#theta|;leptons", 25, 0.0, 1.0), "abscos_t2e")

# (3) directional counts and where they sit in |cos theta|
n_e2t = df.Define("n", "ROOT::VecOps::Sum(cross_e2t)").Sum("n")
n_t2e = df.Define("n", "ROOT::VecOps::Sum(cross_t2e)").Sum("n")
ne2t, nt2e = n_e2t.GetValue(), n_t2e.GetValue()

# fraction of e2t crossers that are forward (|cos theta| > 0.8)
fwd_e2t = df.Define("n", "ROOT::VecOps::Sum(leps_abscos > 0.8 && cross_e2t)").Sum("n").GetValue()

print("\n================= theta-story verification =================")
print("threshold crossers  eta-pass->theta-fail : %d" % ne2t)
print("threshold crossers  theta-pass->eta-fail : %d" % nt2e)
print("directionality ratio (e2t / t2e)         : %.1f" % (ne2t/nt2e if nt2e else float('inf')))
print("e2t crossers with |cos#theta| > 0.8 (forward): %d  (%.1f%% of e2t)"
      % (fwd_e2t, 100.0*fwd_e2t/ne2t if ne2t else 0))
print("mean Delta-iso in central |cos#theta|<0.2  : %.4f" % prof.GetBinContent(prof.FindBin(0.1)))
print("mean Delta-iso in forward |cos#theta|>0.8  : %.4f" % prof.GetBinContent(prof.FindBin(0.9)))
print("===========================================================\n")

# --- plots ---
c = ROOT.TCanvas("c", "", 900, 700)
prof.SetLineColor(ROOT.kRed+1); prof.SetLineWidth(2); prof.SetMarkerStyle(20)
prof.Draw("E1")
c.SaveAs("theta_story_meandiff_vs_costheta.png")

c2 = ROOT.TCanvas("c2", "", 900, 700)
c2.SetLogy()
h_all.SetLineColor(ROOT.kGray+2); h_all.SetLineWidth(2)
h_e2t.SetLineColor(ROOT.kRed+1);  h_e2t.SetLineWidth(2)
h_t2e.SetLineColor(ROOT.kBlue+1); h_t2e.SetLineWidth(2); h_t2e.SetLineStyle(2)
h_e2t.Draw("hist"); h_t2e.Draw("hist same")
leg = ROOT.TLegend(0.15, 0.72, 0.55, 0.88)
leg.AddEntry(h_e2t.GetValue(), "#eta-pass #rightarrow #theta-fail", "l")
leg.AddEntry(h_t2e.GetValue(), "#theta-pass #rightarrow #eta-fail", "l")
leg.Draw()
c2.SaveAs("theta_story_crossers_vs_costheta.png")

c3 = ROOT.TCanvas("c3", "", 900, 700)
c3.SetRightMargin(0.15); c3.SetLogz()
h2.Draw("colz")
c3.SaveAs("theta_story_diff2d.png")

print("Wrote: theta_story_meandiff_vs_costheta.png, theta_story_crossers_vs_costheta.png, theta_story_diff2d.png")
