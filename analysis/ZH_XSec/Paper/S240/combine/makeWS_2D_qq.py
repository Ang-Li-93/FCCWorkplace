"""
Build the hadronic (Z->qq) 2D m_recoil x m_jj fit inputs (ecm 240), following
arXiv:2512.21290: the 2D shape is fitted SIMULTANEOUSLY in two BDT-score regions
(loBDT constrains the backgrounds, hiBDT carries the sensitivity; boundary 0.75 at
240 GeV, 0.95 at 365 GeV, applied in stage2), with the backgrounds split into
components (WW, ZZ, Z/gamma* -> qq, ZH with non-hadronic Z, rare), each with a 1%
normalization nuisance in the datacard (datacard_2d_qq.txt).

Outputs in run_2D_mrecoil_mjj_qq/:
  datacard.root        <cat>_<proc>[_<syst>] unrolled TH1s + <cat>_data_obs (Asimov)
  signal_by_decay.root <cat>_sig_<Hdecay> sums, used by bias_test_qq.py (paper 7.2)
  templates_2d.root    the summed TH2s for inspection
  datacard_2d_qq.txt   copied datacard; text2workspace only succeeds in the combine env

A missing stage2 file for any process aborts (FCC_ALLOW_MISSING=1 downgrades to a
warning). Run in the key4hep env: python3 makeWS_2D_qq.py
"""
import copy
import os
import subprocess
import sys

import ROOT

ROOT.TH1.SetDefaultSumw2(True)
ROOT.gROOT.SetBatch(True)

_ecm = "240"
lumi = 10800000.

_z_had = ["qq", "ss", "cc", "bb"]
_z_lep = ["ee", "mumu", "tautau", "nunu"]
_h_decays = ["Hbb", "Hcc", "Hss", "Hgg", "Haa", "HZa", "HWW", "HZZ", "Hmumu", "Htautau", "Hinv"]

def qq_signal_procs(h=None):
    """Hadronic-Z ZH sets; restrict to one H decay when h is given (bias test)."""
    hs = [h] if h else _h_decays
    return [f"wzp6_ee_{z}H_{hh}_ecm{_ecm}" for z in _z_had for hh in hs]

# background components (arXiv:2512.21290: 1% normalization nuisance each);
# nunuH_Hinv excluded: fully invisible, zero hadronic acceptance
BKG_COMPONENTS = {
    "bkg_WW":   [f"p8_ee_WW_ecm{_ecm}", f"p8_ee_WW_mumu_ecm{_ecm}", f"p8_ee_WW_ee_ecm{_ecm}"],
    "bkg_ZZ":   [f"p8_ee_ZZ_ecm{_ecm}"],
    "bkg_Zqq":  [f"wzp6_ee_qq_ecm{_ecm}"],
    "bkg_ZH":   [f"wzp6_ee_{z}H_{h}_ecm{_ecm}" for z in _z_lep for h in _h_decays
                 if not (z == "nunu" and h == "Hinv")],
    "bkg_rare": [f"wzp6_ee_tautau_ecm{_ecm}", f"wzp6_ee_mumu_ecm{_ecm}",
                 f"wzp6_ee_ee_Mee_30_150_ecm{_ecm}",
                 f"wzp6_egamma_eZ_Zmumu_ecm{_ecm}", f"wzp6_gammae_eZ_Zmumu_ecm{_ecm}",
                 f"wzp6_egamma_eZ_Zee_ecm{_ecm}", f"wzp6_gammae_eZ_Zee_ecm{_ecm}",
                 f"wzp6_gaga_mumu_60_ecm{_ecm}", f"wzp6_gaga_ee_60_ecm{_ecm}",
                 f"wzp6_gaga_tautau_60_ecm{_ecm}", f"wzp6_ee_nuenueZ_ecm{_ecm}"]
                + ([f"p8_ee_tt_ecm{_ecm}"] if _ecm == "365" else []),
}

CATEGORIES = ["hiBDT", "loBDT"]
VARIATIONS = {"JETSCALE": ("scaleup", "scaledw"), "SQRTS": ("sqrtsup", "sqrtsdw")}

baseFileName = ("/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper/S240/qq/"
                "BDT_analysis_samples/syst/{sampleName}_{selection}_histo.root")
runDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_2D_mrecoil_mjj_qq")


def sumProcs2D(procs, sel, hname, newname):
    """Sum one TH2 over many processes (strict on missing stage2 files)."""
    h, missing = None, []
    for proc in procs:
        fname = baseFileName.format(sampleName=proc, selection=sel)
        if not os.path.isfile(fname):
            missing.append(proc)
            continue
        fIn = ROOT.TFile(fname)
        hist = copy.deepcopy(fIn.Get(hname))
        fIn.Close()
        if h is None: h = hist
        else: h.Add(hist)
    if missing:
        msg = f"{newname} ({sel}/{hname}): {len(missing)}/{len(procs)} processes without stage2 output: {missing}"
        if os.environ.get("FCC_ALLOW_MISSING") == "1":
            print(f"WARNING (FCC_ALLOW_MISSING=1): {msg}")
        else:
            sys.exit(f"ERROR: {msg}")
    if h is None:
        sys.exit(f"ERROR: no histograms found for {newname} ({sel}/{hname})")
    h.SetName(newname)
    h.Scale(lumi)
    return h


def unroll(h2, name):
    """TH2 -> TH1 with nx*ny bins, k = (j-1)*nx + i (m_recoil runs fastest)."""
    nx, ny = h2.GetNbinsX(), h2.GetNbinsY()
    h1 = ROOT.TH1D(name, ";unrolled (m_{recoil} #times m_{jj}) bin;Events",
                   nx * ny, 0.5, nx * ny + 0.5)
    for j in range(1, ny + 1):
        for i in range(1, nx + 1):
            k = (j - 1) * nx + i
            h1.SetBinContent(k, h2.GetBinContent(i, j))
            h1.SetBinError(k, h2.GetBinError(i, j))
    return h1


if __name__ == "__main__":
    os.makedirs(runDir, exist_ok=True)

    hists, hists2d, by_decay = [], [], []
    for cat in CATEGORIES:
        sel = f"sel_Baseline_{cat}"

        sig2d = sumProcs2D(qq_signal_procs(), sel, "mrecoil_mjj", f"{cat}_signal2d")
        hists2d.append(sig2d)
        h_sig = unroll(sig2d, f"{cat}_signal")
        hists.append(h_sig)
        h_obs = h_sig.Clone(f"{cat}_data_obs")   # Asimov: signal + backgrounds

        for comp, procs in BKG_COMPONENTS.items():
            b2d = sumProcs2D(procs, sel, "mrecoil_mjj", f"{cat}_{comp}2d")
            hists2d.append(b2d)
            hb = unroll(b2d, f"{cat}_{comp}")
            hists.append(hb)
            h_obs.Add(hb)
        hists.append(h_obs)

        for syst, (up, dw) in VARIATIONS.items():
            for tag, ud in ((up, "Up"), (dw, "Down")):
                h2 = sumProcs2D(qq_signal_procs(), f"{sel}_{tag}",
                                f"mrecoil_mjj_{tag}", f"{cat}_signal2d_{syst}{ud}")
                hists2d.append(h2)
                hists.append(unroll(h2, f"{cat}_signal_{syst}{ud}"))

        # per-H-decay signal sums for the bias test (paper 7.2)
        for h in _h_decays:
            hd2 = sumProcs2D(qq_signal_procs(h), sel, "mrecoil_mjj", f"{cat}_sig2d_{h}")
            by_decay.append(unroll(hd2, f"{cat}_sig_{h}"))

        named = {x.GetName(): x.Integral() for x in hists if x.GetName().startswith(cat)}
        print(f"{cat}: signal {named[f'{cat}_signal']:.1f}, "
              f"total bkg {sum(v for k, v in named.items() if 'bkg' in k):.1f}")

    fOut = ROOT.TFile(f"{runDir}/datacard.root", "RECREATE")
    for h in hists: h.Write()
    fOut.Close()
    fD = ROOT.TFile(f"{runDir}/signal_by_decay.root", "RECREATE")
    for h in by_decay: h.Write()
    fD.Close()
    fCtl = ROOT.TFile(f"{runDir}/templates_2d.root", "RECREATE")
    for h in hists2d: h.Write()
    fCtl.Close()

    cmd = "cp %s/datacard_2d_qq.txt %s/" % (os.path.dirname(os.path.abspath(__file__)), runDir)
    subprocess.call(cmd, shell=True)
    cmd = "text2workspace.py datacard_2d_qq.txt -o ws.root"
    ret = subprocess.call(cmd, shell=True, cwd=runDir)
    if ret != 0:
        print("NOTE: text2workspace failed (expected outside the combine env) - "
              "build ws.root in the combine env, run book step 9. Templates in "
              f"{runDir}/datacard.root are complete.")
