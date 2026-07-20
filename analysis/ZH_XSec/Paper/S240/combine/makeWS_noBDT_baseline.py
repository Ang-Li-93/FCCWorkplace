"""
Referee baseline scenario (ecm 240): NO BDT anywhere, single baseline region,
1D recoil-mass fit for every channel.

  python3 makeWS_noBDT_baseline.py mumu   -> run_noBDT_recoil_mumu/
  python3 makeWS_noBDT_baseline.py ee     -> run_noBDT_recoil_ee/
  python3 makeWS_noBDT_baseline.py qq     -> run_noBDT_recoil_qq/

mumu/ee: recoil_m under sel_Baseline_no_costhetamiss (signal + lumped background,
  free background_norm rateParam, BES/LEPSCALE/SQRTS signal shapes from the shifted-
  branch recoil histograms; reuses datacard_binned_<flavor>.txt).
qq: X-projection (m_recoil, 25 bins 100-150) of the 2D mrecoil_mjj histograms under
  sel_Baseline_nomva (no MVA cut, no categories), per-component backgrounds with 1%
  lnN as in the paper-spec fit (datacard_recoil_qq.txt), JETSCALE/SQRTS signal shapes
  from the shifted-branch 2D histograms.

Run in the key4hep env; text2workspace only succeeds in the combine env (soft-fails).
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
HERE = os.path.dirname(os.path.abspath(__file__))

_z_had = ["qq", "ss", "cc", "bb"]
_z_lep = ["ee", "mumu", "tautau", "nunu"]
_h_decays = ["Hbb", "Hcc", "Hss", "Hgg", "Haa", "HZa", "HWW", "HZZ", "Hmumu", "Htautau", "Hinv"]

QQ_SIG = [f"wzp6_ee_{z}H_{h}_ecm{_ecm}" for z in _z_had for h in _h_decays]
QQ_BKG = {
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
                 f"wzp6_gaga_tautau_60_ecm{_ecm}", f"wzp6_ee_nuenueZ_ecm{_ecm}"],
}

LEP_BKG = {
    "mumu": [f"p8_ee_WW_ecm{_ecm}", f"p8_ee_ZZ_ecm{_ecm}", f"wzp6_ee_mumu_ecm{_ecm}",
             f"wzp6_ee_tautau_ecm{_ecm}",
             f"wzp6_egamma_eZ_Zmumu_ecm{_ecm}", f"wzp6_gammae_eZ_Zmumu_ecm{_ecm}",
             f"wzp6_gaga_mumu_60_ecm{_ecm}", f"wzp6_gaga_tautau_60_ecm{_ecm}",
             f"wzp6_ee_nuenueZ_ecm{_ecm}"],
    "ee":   [f"p8_ee_WW_ecm{_ecm}", f"p8_ee_ZZ_ecm{_ecm}", f"wzp6_ee_ee_Mee_30_150_ecm{_ecm}",
             f"wzp6_ee_tautau_ecm{_ecm}",
             f"wzp6_egamma_eZ_Zee_ecm{_ecm}", f"wzp6_gammae_eZ_Zee_ecm{_ecm}",
             f"wzp6_gaga_ee_60_ecm{_ecm}", f"wzp6_gaga_tautau_60_ecm{_ecm}",
             f"wzp6_ee_nuenueZ_ecm{_ecm}"],
}


def get1d(base, proc, sel, hname, project=False):
    fname = base.format(sampleName=proc, selection=sel)
    if not os.path.isfile(fname):
        return None
    fIn = ROOT.TFile(fname)
    h = fIn.Get(hname)
    if not h:
        fIn.Close()
        return None
    h = copy.deepcopy(h)
    fIn.Close()
    if project:
        h = h.ProjectionX(f"{proc}_{sel}_{hname}_px")
    return h


def sum1d(base, procs, sel, hname, newname, project=False, strict=True):
    h, missing = None, []
    for p in procs:
        hi = get1d(base, p, sel, hname, project)
        if hi is None:
            missing.append(p)
            continue
        if h is None: h = hi
        else: h.Add(hi)
    if missing and strict and os.environ.get("FCC_ALLOW_MISSING") != "1":
        sys.exit(f"ERROR: {newname}: missing stage2 for {missing}")
    if h is None:
        sys.exit(f"ERROR: nothing found for {newname}")
    h.SetName(newname)
    h.Scale(lumi)
    return h


def build_qq():
    base = (f"/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper/S{_ecm}/qq/"
            "BDT_analysis_samples/syst/{sampleName}_{selection}_histo.root")
    runDir = os.path.join(HERE, "run_noBDT_recoil_qq")
    os.makedirs(runDir, exist_ok=True)
    hists = []
    sel = "sel_Baseline_nomva"
    hists.append(sum1d(base, QQ_SIG, sel, "mrecoil_mjj", "signal", project=True))
    h_obs = hists[0].Clone("data_obs")
    for comp, procs in QQ_BKG.items():
        hb = sum1d(base, procs, sel, "mrecoil_mjj", comp, project=True)
        hists.append(hb)
        h_obs.Add(hb)
    hists.append(h_obs)
    for syst, (up, dw) in {"JETSCALE": ("scaleup", "scaledw"), "SQRTS": ("sqrtsup", "sqrtsdw")}.items():
        for tag, ud in ((up, "Up"), (dw, "Down")):
            hists.append(sum1d(base, QQ_SIG, f"{sel}_{tag}", f"mrecoil_mjj_{tag}",
                               f"signal_{syst}{ud}", project=True))
    fOut = ROOT.TFile(f"{runDir}/datacard.root", "RECREATE")
    for h in hists: h.Write()
    fOut.Close()
    print(f"qq noBDT: signal {hists[0].Integral():.1f}, "
          f"bkg {h_obs.Integral()-hists[0].Integral():.1f}")
    subprocess.call(f"cp {HERE}/datacard_recoil_qq.txt {runDir}/", shell=True)
    return runDir


def build_lep(flavor):
    base = (f"/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper/S{_ecm}/{flavor}/"
            "BDT_analysis_samples/syst/{sampleName}_{selection}_histo.root")
    runDir = os.path.join(HERE, f"run_noBDT_recoil_{flavor}")
    os.makedirs(runDir, exist_ok=True)
    sel = "sel_Baseline_wide"  # no-BDT, recoil 100-150: sidebands constrain the background
    sig = f"wzp6_ee_{flavor}H_ecm{_ecm}"
    hists = []
    hists.append(sum1d(base, [sig], sel, "recoil_m", "signal"))
    h_obs = hists[0].Clone("data_obs")
    hb = sum1d(base, LEP_BKG[flavor], sel, "recoil_m", "background")
    hists.append(hb)
    h_obs.Add(hb)
    hists.append(h_obs)
    scale_name = "MUSCALE" if flavor == "mumu" else "ELSCALE"
    hists.append(sum1d(base, [sig], f"{sel}_scaleup", "recoil_m_scaleup", f"signal_{scale_name}Up"))
    hists.append(sum1d(base, [sig], f"{sel}_scaledw", "recoil_m_scaledw", f"signal_{scale_name}Down"))
    hists.append(sum1d(base, [sig], f"{sel}_sqrtsup", "recoil_m_sqrtsup", "signal_SQRTSUp"))
    hists.append(sum1d(base, [sig], f"{sel}_sqrtsdw", "recoil_m_sqrtsdw", "signal_SQRTSDown"))
    hists.append(sum1d(base, [f"wzp6_ee_{flavor}H_BES-higher-1pc_ecm{_ecm}"], sel, "recoil_m", "signal_BESUp"))
    hists.append(sum1d(base, [f"wzp6_ee_{flavor}H_BES-lower-1pc_ecm{_ecm}"], sel, "recoil_m", "signal_BESDown"))
    fOut = ROOT.TFile(f"{runDir}/datacard.root", "RECREATE")
    for h in hists: h.Write()
    fOut.Close()
    print(f"{flavor} noBDT: signal {hists[0].Integral():.1f}, background {hb.Integral():.1f}")
    subprocess.call(f"cp {HERE}/datacard_binned_{flavor}.txt {runDir}/", shell=True)
    subprocess.call(f"sed -i 's/bkg/bkg_{flavor}/g' datacard_binned_{flavor}.txt",
                    shell=True, cwd=runDir)
    return runDir


if __name__ == "__main__":
    flavor = sys.argv[1] if len(sys.argv) > 1 else "qq"
    runDir = build_qq() if flavor == "qq" else build_lep(flavor)
    card = "datacard_recoil_qq.txt" if flavor == "qq" else f"datacard_binned_{flavor}.txt"
    ret = subprocess.call(f"text2workspace.py {card} -o ws.root", shell=True, cwd=runDir)
    if ret != 0:
        print("NOTE: text2workspace failed (expected outside the combine env).")
