'''
Overlay the histmaker output for the two samples (Whizard ME decay vs Pythia6
resonance decay) and write independent PDF+PNG plots, one per observable.

Run (after `fccanalysis run histmaker.py`):  python plot.py
'''
import os
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(HERE, "plots")
os.makedirs(OUT, exist_ok=True)

f_st = ROOT.TFile(os.path.join(HERE, "output", "wzp6_ee_mumuH_Hbb_ecm240.root"))
f_me = ROOT.TFile(os.path.join(HERE, "output", "wzp6_ee_mumuH_Hbb_MEdecay_ecm240.root"))

C_ST = ROOT.TColor.GetColor("#1f77b4")
C_ME = ROOT.TColor.GetColor("#d62728")
SUB  = "ee #rightarrow #mu#muH, 240 GeV, winter2023"

# observable -> (title, x-axis label, reference-line position)
PLOTS = {
    "m_parton": ("parton m(b,#bar{b})",                         "m(b,#bar{b}) [GeV]",            125),
    "m_vis":    ("particle-level VISIBLE (no #nu, MET-blind)",  "m_{vis}(bb) [GeV]",             125),
    "m_full":   ("particle-level FULL (+#nu / MET-corrected)",  "m(bb) [GeV]",                   125),
    "m_bdesc":  ("invariant mass of hard b/#bar{b} descendants","m(b/#bar{b} descendants) [GeV]",125),
    "m_dijet":  ("detector-level Durham n=2 dijet mass",        "m_{jj} [GeV]",                  125),
    "m_dijet_met": ("detector-level Durham n=2 dijet + MET",    "m(jj+MET) [GeV]",               125),
    "m_recoil": ("#mu^{+}#mu^{-} recoil mass (detector)",       "m_{recoil} [GeV]",              125),
    # muon-pair (Z) at three levels
    "mll_parton":    ("m(#mu^{+}#mu^{-}) parton (hard)",        "m_{#mu#mu} [GeV]",              91.2),
    "mll_gen":       ("m(#mu^{+}#mu^{-}) particle (post-FSR)",  "m_{#mu#mu} [GeV]",              91.2),
    "mll_reco":      ("m(#mu^{+}#mu^{-}) detector",            "m_{#mu#mu} [GeV]",               91.2),
    "recoil_parton": ("#mu^{+}#mu^{-} recoil parton (hard)",    "m_{recoil} [GeV]",              125),
    "recoil_gen":    ("#mu^{+}#mu^{-} recoil particle (post-FSR)","m_{recoil} [GeV]",            125),
}

def norm(h):
    h = h.Clone()
    h.SetDirectory(0)
    if h.Integral() > 0:
        h.Scale(1.0 / h.Integral())
    return h

for name, (title, xlab, refx) in PLOTS.items():
    h_st = norm(f_st.Get(name))
    h_me = norm(f_me.Get(name))

    c = ROOT.TCanvas("c_" + name, name, 800, 600)
    c.SetLeftMargin(0.13); c.SetRightMargin(0.05); c.SetTopMargin(0.08)

    for h, col in [(h_st, C_ST), (h_me, C_ME)]:
        h.SetLineColor(col); h.SetLineWidth(2)
    ymax = 1.35 * max(h_st.GetMaximum(), h_me.GetMaximum())

    h_st.SetTitle(f"{title}   ({SUB})")
    h_st.GetXaxis().SetTitle(xlab)
    h_st.GetYaxis().SetTitle("normalised / bin")
    h_st.GetYaxis().SetTitleOffset(1.5)
    h_st.SetMaximum(ymax); h_st.SetMinimum(0)
    h_st.Draw("hist")
    h_me.Draw("hist same")

    line = ROOT.TLine(refx, 0, refx, ymax); line.SetLineStyle(2)
    line.SetLineColor(ROOT.kGray + 1); line.Draw()

    leg = ROOT.TLegend(0.16, 0.74, 0.62, 0.90)
    leg.SetBorderSize(0); leg.SetFillStyle(0); leg.SetTextSize(0.030)
    leg.AddEntry(h_st, f"H#rightarrow bb: Pythia6 resonance decay  "
                       f"(mean {h_st.GetMean():.1f}, RMS {h_st.GetRMS():.1f})", "l")
    leg.AddEntry(h_me, f"H#rightarrow bb: Whizard ME decay  "
                       f"(mean {h_me.GetMean():.1f}, RMS {h_me.GetRMS():.1f})", "l")
    leg.Draw()

    for ext in ("pdf", "png"):
        c.SaveAs(os.path.join(OUT, f"{name}.{ext}"))
    print("wrote", name, "(.pdf + .png)")

print("done:", len(PLOTS), "plots ->", OUT)
