import ROOT
import os
import subprocess
import plotter
import copy

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)


def get_hist_from_file(file_name, hist_name, lumi, rebin):
    """Get a histogram from a file, scale it by lumi, and rebin."""
    print(f"Getting histogram {hist_name} from file {file_name}") 
    with ROOT.TFile(file_name) as f:
        hist = f.Get(hist_name).Clone()
    hist.Scale(lumi)
    hist.Rebin(rebin)
    return hist

def process_histograms(procs, base_file_name, hist_name, lumi, rebin):
    """Process histograms for a list of processes."""
    hists = []
    for proc in procs:
        file_name = base_file_name.format(sampleName=proc)
        hist = get_hist_from_file(file_name, hist_name, lumi, rebin)
        hists.append(hist)
    return hists

def process_files(base_file_name, hist_name, lumi, rebin):
    """Process files for signal and background."""
    global flavor
    if flavor == "mumu":
        procs_signal = ["wzp6_ee_mumuH_ecm240"]
        procs_background = ['p8_ee_WW_ecm240',
                            'wzp6_egamma_eZ_Zmumu_ecm240',
                            'wzp6_gammae_eZ_Zmumu_ecm240',
                            'wzp6_ee_mumu_ecm240',
                            'p8_ee_ZZ_ecm240',
                            ##rare  
                            "wzp6_ee_tautau_ecm240",
                            "wzp6_gaga_mumu_60_ecm240",
                            "wzp6_gaga_tautau_60_ecm240",
                            "wzp6_ee_nuenueZ_ecm240"
                            ]
    elif flavor == "ee":
        procs_signal = ["wzp6_ee_eeH_ecm240"]
        procs_background = ['p8_ee_WW_ecm240',
                            'wzp6_egamma_eZ_Zee_ecm240',
                            'wzp6_gammae_eZ_Zee_ecm240',
                            'wzp6_ee_ee_Mee_30_150_ecm240',
                            'p8_ee_ZZ_ecm240',
                            ##rare  
                            "wzp6_ee_tautau_ecm240",
                            "wzp6_gaga_ee_60_ecm240",
                            "wzp6_gaga_tautau_60_ecm240",
                            "wzp6_ee_nuenueZ_ecm240"
                            ]
    else:
        raise ValueError(f"Invalid flavor: {flavor}")

    hists_signal = process_histograms(procs_signal, base_file_name, hist_name, lumi, rebin)
    hists_background = process_histograms(procs_background, base_file_name, hist_name, lumi, rebin)
    return hists_signal, hists

def plot_histogram(hist, cfg, label, out_filename):
    canvas, padT, padB = plotter.canvasRatio()
    dummyT, dummyB = plotter.dummyRatio()
    # Top pad
    canvas.cd()
    padT.Draw()
    padT.cd()
    dummyT.Draw("HIST")
    hist.SetLineColor(ROOT.kBlack)
    hist.SetLineWidth(2)
    hist.Draw("HIST E SAME")
    draw_label(0.2, 0.88, label)
    plotter.auxRatio()
    # Bottom pad
    canvas.cd()
    padB.Draw()
    padB.cd()
    dummyB.Draw("HIST")
    line = ROOT.TLine(cfg['xmin'], 0, cfg['xmax'], 0)
    line.SetLineColor(ROOT.kBlue+2)
    line.SetLineWidth(2)
    line.Draw("SAME")
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs(f"{out_filename}.png")
    canvas.SaveAs(f"{out_filename}.pdf")
    # Clear memory
    del dummyB
    del dummyT
    del padT
    del padB
    del canvas

def process_file(file_name, hist_name, lumi, rebin):
    global flavor
    fIn = ROOT.TFile(file_name)
    hist = copy.deepcopy(fIn.Get(hist_name))
    fIn.Close()
    print(f"Getting histogram {hist_name} from file {file_name}")
    hist.Scale(lumi)
    hist = hist.Rebin(rebin)
    return hist

def process_samples(procs, baseFileName, hist_name, lumi, rebin):
    global flavor, selection
    h_obs = None
    for proc in procs:
        hist = process_file(baseFileName.format(flavor=flavor,selection=selection,sampleName=proc), hist_name, lumi, rebin)
        if h_obs is None:
            h_obs = hist.Clone("h_obs")
        else:
            h_obs.Add(hist)
    return h_obs

def doSignal():
    global h_obs, flavor, selection
    mHs = [125.0]
    procs = [f"wzp6_ee_{flavor}H_ecm240"]
    for i, proc in enumerate(procs):
        hist = process_file(baseFileName.format(flavor=flavor,selection=selection,sampleName=proc), hName, lumi, rebin)
        hist.SetName("signal")
        hists.append(hist)
        if mHs[i] == 125.0:
            if h_obs is None:
                h_obs = hist.Clone("h_obs")
            else:
                h_obs.Add(hist)
        if doPlot:
            plot_histogram(hist, cfg, label, f"{outDir}/hist_mH{('%.2f' % mHs[i]).replace('.', 'p')}_{selection}")

def doBackgrounds():
    global h_obs, flavor, hName, lumi, rebin
    procs = ['p8_ee_WW_ecm240',
             f'wzp6_egamma_eZ_Z{flavor}_ecm240',
             f'wzp6_gammae_eZ_Z{flavor}_ecm240',
             f'wzp6_ee_{flavor}_ecm240',
             'p8_ee_ZZ_ecm240',
             ##rare  
             "wzp6_ee_tautau_ecm240",
             f"wzp6_gaga_{flavor}_60_ecm240",
             "wzp6_gaga_tautau_60_ecm240",
             "wzp6_ee_nuenueZ_ecm240"
            ]
    h_obs = process_samples(procs, baseFileName, hName, lumi, rebin)
    h_obs.SetName("background")
    hists.append(h_obs)
    if doPlot:
        plot_histogram(h_obs, cfg, label, f"{outDir}/hist_background_{selection}")

def run():
    global h_obs, hists, selection
    hists = []
    h_obs = None
    doSignal()
    doBackgrounds()

    # Create output directory if it doesn't exist
    if not os.path.exists(outDir):
        os.makedirs(outDir)

        ##write
    outFile = ROOT.TFile(f"{outDir}/{outFileName}_{selection}.root", "RECREATE")
    for hist in hists:
        hist.Write()
    outFile.Close()

if __name__ == '__main__':
    doPlot = True
    flavor = "mumu"  # Define flavor here
    selection = "sel_Baseline_no_costhetamiss"
    hName = "BDT_Score"
    lumi = 10e+06
    rebin = 1
    baseFileName = "/eos/user/l/lia/FCCee/MidTerm/{flavor}/BDT_analysis_samples/final/{sampleName}_{selection}_histo.root"
    run()






