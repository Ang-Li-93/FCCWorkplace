#!/usr/bin/env python3
# Build Combine datacards for the rare Higgs decay search: one card per
# "one rare decay vs all SM" scenario, fitting the renormalized multiclass
# BDT score  norm_prob{i} = P(rare_i) / (P(rare_i) + P(SM Higgs) + P(SM bkg))
# in the baseline selection.
#
# Inputs:  Histo_Files/<process>_sel_Baseline_no_costhetamiss_histo.root
#          (histograms normalized to xsec*eff in pb, intLumi=1)
# Outputs: cards/<scenario>/shapes.root + datacard.txt
#          data_obs = SM-only Asimov (sum of backgrounds)
#
# Run inside any environment with ROOT (e.g. the Combine standalone env),
# then e.g.:
#   text2workspace.py cards/Hbs/datacard.txt
#   combine -M AsymptoticLimits cards/Hbs/datacard.txt -t -1 -n _Hbs

import os
import ROOT

ROOT.gROOT.SetBatch(True)

HISTO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Histo_Files")
OUT_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cards")
SELECTION = "sel_Baseline_no_costhetamiss"
INT_LUMI  = 10.8e6          # pb^-1 (10.8 ab^-1, as in analysis_stage1_plots.py)
XSEC_MUMUH = 0.0067643      # pb, wzp6_ee_mumuH_ecm240 -> BR = r * xsec_sample / XSEC_MUMUH

# scenario -> (signal sample, renormalized score); class numbering from
# process_sig_bkg_samples_for_multi.py
SCENARIOS = {
    "Hbs": ("wzp6_ee_mumuH_Hbs_W4p1MeV_ecm240", "norm_prob0"),
    "Huu": ("wzp6_ee_mumuH_Huu_ecm240",         "norm_prob1"),
    "Hdd": ("wzp6_ee_mumuH_Hdd_ecm240",         "norm_prob2"),
    "Hcu": ("wzp6_ee_mumuH_Hcu_W4p1MeV_ecm240", "norm_prob3"),
    "Hsd": ("wzp6_ee_mumuH_Hsd_W4p1MeV_ecm240", "norm_prob4"),
    "Hbd": ("wzp6_ee_mumuH_Hbd_W4p1MeV_ecm240", "norm_prob5"),
}

# "all SM" backgrounds. The SM Higgs decays (class 6) are merged into a single
# inclusive ZH(Z->mumu) process — their xsec-weighted sum reproduces the
# inclusive wzp6_ee_mumuH decomposition (0.006753 pb vs 0.0067643 pb; only
# Hmumu/Hgamgam/Hinv missing). Other rare modes are excluded (one-at-a-time).
SM_HIGGS = [
    "wzp6_ee_mumuH_Hbb_ecm240",
    "wzp6_ee_mumuH_Hcc_ecm240",
    "wzp6_ee_mumuH_Hss_ecm240",
    "wzp6_ee_mumuH_Hgg_ecm240",
    "wzp6_ee_mumuH_HWW_ecm240",
    "wzp6_ee_mumuH_HZZ_noInv_ecm240",
    "wzp6_ee_mumuH_HZa_ecm240",
    "wzp6_ee_mumuH_Htautau_ecm240",
]
BACKGROUNDS = [
    ("ZZ",      "p8_ee_ZZ_ecm240"),
    ("WW",      "p8_ee_WW_ecm240"),
    ("Zmumu",   "wzp6_ee_mumu_ecm240"),
    ("egamma",  "wzp6_egamma_eZ_Zmumu_ecm240"),
    ("gammae",  "wzp6_gammae_eZ_Zmumu_ecm240"),
    ("gaga",    "wzp6_gaga_mumu_60_ecm240"),
]

LUMI_UNC = 1.005  # placeholder luminosity lnN


def get_shape(process, var, newname):
    fname = os.path.join(HISTO_DIR, f"{process}_{SELECTION}_histo.root")
    f = ROOT.TFile.Open(fname)
    if not f or f.IsZombie():
        raise RuntimeError(f"cannot open {fname}")
    h = f.Get(var)
    if not h:
        raise RuntimeError(f"{var} not found in {fname}")
    out = h.Clone(newname)
    out.SetDirectory(0)
    f.Close()
    # fold under/overflow into the edge bins so the shape integral is complete
    n = out.GetNbinsX()
    out.SetBinContent(1, out.GetBinContent(0) + out.GetBinContent(1))
    out.SetBinContent(n, out.GetBinContent(n) + out.GetBinContent(n + 1))
    out.SetBinError(1, (out.GetBinError(0) ** 2 + out.GetBinError(1) ** 2) ** 0.5)
    out.SetBinError(n, (out.GetBinError(n) ** 2 + out.GetBinError(n + 1) ** 2) ** 0.5)
    out.SetBinContent(0, 0.0); out.SetBinError(0, 0.0)
    out.SetBinContent(n + 1, 0.0); out.SetBinError(n + 1, 0.0)
    out.Scale(INT_LUMI)
    return out


def get_xsec(process):
    fname = os.path.join(HISTO_DIR, f"{process}_{SELECTION}_histo.root")
    f = ROOT.TFile.Open(fname)
    xs = f.Get("crossSection").GetVal()
    f.Close()
    return xs


def make_card(scenario, sig_process, var):
    outdir = os.path.join(OUT_DIR, scenario)
    os.makedirs(outdir, exist_ok=True)

    shapes = {"sig": get_shape(sig_process, var, "sig")}

    zh = get_shape(SM_HIGGS[0], var, "ZH")
    for process in SM_HIGGS[1:]:
        zh.Add(get_shape(process, var, f"tmp_{process}"))
    shapes["ZH"] = zh

    for name, process in BACKGROUNDS:
        shapes[name] = get_shape(process, var, name)

    data_obs = shapes["ZH"].Clone("data_obs")
    for name, _ in BACKGROUNDS:
        data_obs.Add(shapes[name])

    fout = ROOT.TFile(os.path.join(outdir, "shapes.root"), "RECREATE")
    for h in list(shapes.values()) + [data_obs]:
        h.Write()
    fout.Close()

    bkg_names = ["ZH"] + [name for name, _ in BACKGROUNDS]
    procs = ["sig"] + bkg_names
    idx = [0] + list(range(1, len(bkg_names) + 1))

    card = os.path.join(outdir, "datacard.txt")
    with open(card, "w") as fc:
        fc.write(f"# {scenario}: {sig_process} vs all-SM, shape fit of {var} ({SELECTION})\n")
        fc.write(f"# lumi = {INT_LUMI:g} pb^-1; signal placeholder xsec = {get_xsec(sig_process):g} pb\n")
        fc.write(f"# BR({scenario}) = r * {get_xsec(sig_process) / XSEC_MUMUH:.4g}\n")
        fc.write("imax 1\njmax *\nkmax *\n")
        fc.write("---------------\n")
        fc.write("shapes * ch1 shapes.root $PROCESS\n")
        fc.write("---------------\n")
        fc.write("bin ch1\nobservation -1\n")
        fc.write("---------------\n")
        fc.write("bin      " + " ".join(["ch1"] * len(procs)) + "\n")
        fc.write("process  " + " ".join(procs) + "\n")
        fc.write("process  " + " ".join(str(i) for i in idx) + "\n")
        fc.write("rate     " + " ".join(["-1"] * len(procs)) + "\n")
        fc.write("---------------\n")
        fc.write("lumi lnN " + " ".join([f"{LUMI_UNC}"] * len(procs)) + "\n")
        fc.write("* autoMCStats 10\n")

    yields = {p: shapes[p].Integral() for p in procs}
    return card, yields, data_obs.Integral()


if __name__ == "__main__":
    for scenario, (sig_process, var) in SCENARIOS.items():
        card, yields, nobs = make_card(scenario, sig_process, var)
        print(f"\n== {scenario} ({var}) -> {card}")
        print(f"   signal    {yields['sig']:12.1f}   (placeholder normalization)")
        for name in ["ZH"] + [n for n, _ in BACKGROUNDS]:
            print(f"   {name:9s} {yields[name]:12.1f}")
        print(f"   data_obs  {nobs:12.1f}   (SM-only Asimov)")
