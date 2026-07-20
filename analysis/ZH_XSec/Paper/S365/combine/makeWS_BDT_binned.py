
import sys,copy,array,os,subprocess
import ROOT

ROOT.TH1.SetDefaultSumw2(True)
ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)

doPlot = True
if doPlot:
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))  # Paper root: plotter.py
    import plotter

# ---- hadronic (qq) channel: many-process signal/background sums ----
_ecm = "365"
_z_had = ["qq", "ss", "cc", "bb"]
_z_lep = ["ee", "mumu", "tautau", "nunu"]
_h_decays = ["Hbb", "Hcc", "Hss", "Hgg", "Haa", "HZa", "HWW", "HZZ", "Hmumu", "Htautau", "Hinv"]

def qq_signal_procs():
    # hadronic Z decays x all H decays; ZH with leptonic/invisible Z decays counts as
    # background (kept orthogonal to the ee/mumu channels by the stage1 lepton veto)
    return [f"wzp6_ee_{z}H_{h}_ecm{_ecm}" for z in _z_had for h in _h_decays]

def qq_background_procs():
# nunuH_Hinv excluded: fully invisible, zero hadronic acceptance (empty stage1/stage2)
    return ([f"wzp6_ee_{z}H_{h}_ecm{_ecm}" for z in _z_lep for h in _h_decays
             if not (z == "nunu" and h == "Hinv")] + [
        f"p8_ee_WW_ecm{_ecm}", f"p8_ee_WW_mumu_ecm{_ecm}", f"p8_ee_WW_ee_ecm{_ecm}",
        f"p8_ee_ZZ_ecm{_ecm}",
        f"wzp6_ee_qq_ecm{_ecm}", f"wzp6_ee_tautau_ecm{_ecm}", f"wzp6_ee_mumu_ecm{_ecm}",
        f"wzp6_ee_ee_Mee_30_150_ecm{_ecm}",
        f"wzp6_egamma_eZ_Zmumu_ecm{_ecm}", f"wzp6_gammae_eZ_Zmumu_ecm{_ecm}",
        f"wzp6_egamma_eZ_Zee_ecm{_ecm}", f"wzp6_gammae_eZ_Zee_ecm{_ecm}",
        f"wzp6_gaga_mumu_60_ecm{_ecm}", f"wzp6_gaga_ee_60_ecm{_ecm}",
        f"wzp6_gaga_tautau_60_ecm{_ecm}", f"wzp6_ee_nuenueZ_ecm{_ecm}"]
        + ([f"p8_ee_tt_ecm{_ecm}"] if _ecm == "365" else []))

def sumProcs(procs, sel, hname, newname):
    """
    Sum one histogram over many processes. A missing stage2 file aborts the run:
    the winter2023 catalog has every process, so a gap means the stage1/stage2
    production is incomplete, and skipping it would silently bias the template
    (and let nominal and Up/Down templates sum different process sets).
    Set FCC_ALLOW_MISSING=1 to downgrade to a warning.
    """
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
    return h.Rebin(rebin)

def doSyst(Syst):

    proc_Up = "wzp6_ee_{flavor}H_ecm365".format(flavor=flavor)
    proc_Down = "wzp6_ee_{flavor}H_ecm365".format(flavor=flavor)
    # variation selections are named relative to the baseline selection, so the same
    # logic serves the leptonic (sel_Baseline_no_costhetamiss*) and qq (sel_Baseline*) stage2
    selection_Up = selection
    selection_Down = selection
    if Syst == "BES":
        if flavor == "qq":
            sys.exit("ERROR: no BES samples for hadronic Z decays in winter2023")
        proc_Up = "wzp6_ee_{flavor}H_BES-higher-10pc_ecm365".format(flavor=flavor)
        proc_Down = "wzp6_ee_{flavor}H_BES-lower-10pc_ecm365".format(flavor=flavor)
        hName_Up = "BDT_Score"
        hName_Down = "BDT_Score"
        syst_name = "BES"
    elif Syst == "SQRTS":
        selection_Up = selection + "_sqrtsup"
        selection_Down = selection + "_sqrtsdw"
        hName_Up    = "BDT_Score"
        hName_Down  = "BDT_Score"
        syst_name = "SQRTS"

    elif Syst == "LEPSCALE":
        selection_Up = selection + "_scaleup"
        selection_Down = selection + "_scaledw"
        hName_Up = "BDT_Score_scaleup"
        hName_Down = "BDT_Score_scaledw"
        if flavor == "mumu":
            syst_name = "MUSCALE"
        elif flavor == "ee":
            syst_name = "ELSCALE"
    elif Syst == "JETSCALE":
        # qq: the BDT score is not recomputed under the jet-scale shift (stage1 keeps
        # the nominal score); the +-1e-5 scale enters via the selection migration
        selection_Up = selection + "_scaleup"
        selection_Down = selection + "_scaledw"
        hName_Up = "BDT_Score"
        hName_Down = "BDT_Score"
        syst_name = "JETSCALE"
    else:
        sys.exit("ERROR: Syst not defined")

    

    # recoil mass plot settings
    cfg = {
 
        'logy'              : False,
        'logx'              : False,
    
        'xmin'              : 120 if not "Score" in hName else 0,
        'xmax'              : 140 if not "Score" in hName else 1,
        'ymin'              : 0,
        'ymax'              : 3000,
        
        'xtitle'            : "Recoil mass (GeV)" if not "Score" in hName else "BDT Score",
        'ytitle'            : "Events / 0.2 GeV" if not "Score" in hName else "Events / 0.05",
        
        'topRight'          : "ZH, #sqrt{s} = 365 GeV, 3.12 ab^{#minus1}", 
        'topLeft'           : "#bf{FCC-ee} #scale[0.7]{#it{Simulation}}",
        
        'ratiofraction'     : 0.25,
        'ytitleR'           : "Ratio",
        'yminR'             : 0.9,
        'ymaxR'             : 1.1,
    }
    

    
    if flavor == "qq":
        hist_Up = sumProcs(qq_signal_procs(), selection_Up, hName_Up, "signal_%sUp" % (syst_name))
        hist_Down = sumProcs(qq_signal_procs(), selection_Down, hName_Down, "signal_%sDown" % (syst_name))
        hists.append(hist_Up)
        hists.append(hist_Down)
    else:
        fIn_Up = ROOT.TFile(baseFileName.format(sampleName=proc_Up,selection=selection_Up))
        fIn_Down = ROOT.TFile(baseFileName.format(sampleName=proc_Down,selection=selection_Down))
        hist_Up     = copy.deepcopy(fIn_Up.Get(hName_Up))
        hist_Down   = copy.deepcopy(fIn_Down.Get(hName_Down))
        hist_Up     = hist_Up.Rebin(rebin)
        hist_Down   = hist_Down.Rebin(rebin)
        hist_Up.SetName("signal_%sUp" % (syst_name))
        hist_Down.SetName("signal_%sDown" % (syst_name))
        #hist_Up.Scale(signal_yield/hist_Up.Integral())
        #hist_Down.Scale(signal_yield/hist_Down.Integral())
        hist_Up.Scale(lumi)
        hist_Down.Scale(lumi)
        hists.append(hist_Up)
        hists.append(hist_Down)
        fIn_Up.Close()
        fIn_Down.Close()
    
    if doPlot:
        # do plotting
        plotter.cfg = cfg
    
        cfg['ymax'] = 1.3*hist_zh.GetMaximum()
    
        canvas, padT, padB = plotter.canvasRatio()
        dummyT, dummyB = plotter.dummyRatio()
    
        ## TOP PAD ##
        canvas.cd()
        padT.Draw()
        padT.cd()
        dummyT.Draw("HIST")
    
        hist_zh.SetLineColor(ROOT.kBlack)
        hist_zh.SetLineWidth(2)
        hist_zh.Draw("HIST E SAME")

        hist_Up.SetLineColor(ROOT.kBlue)
        hist_Up.SetLineWidth(2)
        hist_Up.Draw("HIST E SAME")

        hist_Down.SetLineColor(ROOT.kRed)
        hist_Down.SetLineWidth(2)
        hist_Down.Draw("HIST E SAME")

        # after you've drawn your histograms:
        legend = ROOT.TLegend(0.6, 0.7, 0.8, 0.9)  # coordinates are in pad fractions, adjust as needed
        legend.AddEntry(hist_zh, "%s__Nominal" % syst_name, "l")
        legend.AddEntry(hist_Up, "%s__Up" % syst_name, "l")
        legend.AddEntry(hist_Down, "%s__Down" % syst_name, "l")
        legend.SetTextSize(0.04) # Set the text size. Adjust the number as needed
        legend.SetBorderSize(0)  # No border
        legend.Draw()

        canvas.Update()
    
        latex = ROOT.TLatex()
        latex.SetNDC()
        latex.SetTextSize(0.045)
        latex.SetTextColor(1)
        latex.SetTextFont(42)
        latex.SetTextAlign(13)
        latex.DrawLatex(0.2, 0.88, label)
        plotter.auxRatio()
    
        ## BOTTOM PAD ##
        # Calculate ratio for hist_Up
        hist_ratio_Up = hist_Up.Clone()
        hist_ratio_Up.Divide(hist_zh) 

        # Calculate ratio for hist_Down
        hist_ratio_Down = hist_Down.Clone()
        hist_ratio_Down.Divide(hist_zh) 
 
        canvas.cd()
        padB.Draw()
        padB.cd()
        dummyB.Draw("HIST")

        hist_ratio_Up.SetLineColor(ROOT.kBlue)
        hist_ratio_Up.SetLineWidth(2)
        hist_ratio_Up.Draw("HIST E SAME")

        hist_ratio_Down.SetLineColor(ROOT.kRed)
        hist_ratio_Down.SetLineWidth(2)
        hist_ratio_Down.Draw("HIST E SAME")

        line = ROOT.TLine(0, 1, 1, 1)
        line.SetLineColor(ROOT.kBlack)
        line.SetLineWidth(2)
        line.Draw("SAME")
    
        canvas.SaveAs("%s/hist_BDT_%s_%s.png" % (outDir, syst_name, selection))
        canvas.SaveAs("%s/hist_BDT_%s_%s.pdf" % (outDir, syst_name, selection))

    
    
        del dummyB
        del dummyT
        del padT
        del padB
        del canvas

def doSignal():

    global h_obs
    global hist_zh 
    mHs = [125.0]
    if flavor == "mumu":
        procs = ["wzp6_ee_mumuH_ecm365"]

    if flavor == "ee":
        procs = ["wzp6_ee_eeH_ecm365"]

    if flavor == "qq":
        procs = ["qq_signal_sum"]  # summed over qq_signal_procs() below

    # recoil mass plot settings
    cfg = {
 
        'logy'              : False,
        'logx'              : False,
    
        'xmin'              : 120 if not "Score" in hName else 0,
        'xmax'              : 140 if not "Score" in hName else 1,
        'ymin'              : 0,
        'ymax'              : 3000,
        
        'xtitle'            : "Recoil mass (GeV)" if not "Score" in hName else "BDT Score",
        'ytitle'            : "Events / 0.2 GeV" if not "Score" in hName else "Events / 0.05",
        
        'topRight'          : "ZH, #sqrt{s} = 365 GeV, 3.12 ab^{#minus1}", 
        'topLeft'           : "#bf{FCC-ee} #scale[0.7]{#it{Simulation}}",
        
        'ratiofraction'     : 0.25,
        'ytitleR'           : "Pull",
        'yminR'             : -3.5,
        'ymaxR'             : 3.5,
    }
    
   
    for i, proc in enumerate(procs):

        mH = mHs[i]
        mH_ = ("%.2f" % mH).replace(".", "p")

        if flavor == "qq":
            hist_zh = sumProcs(qq_signal_procs(), selection, hName, "signal")
        else:
            fIn = ROOT.TFile(baseFileName.format(sampleName=proc,selection=selection))
            hist_zh = copy.deepcopy(fIn.Get(hName))
            hist_zh = hist_zh.Rebin(rebin)
            hist_zh.SetName("signal")
            hist_zh.Scale(lumi)
            fIn.Close()
        hists.append(hist_zh)
        
        if mH == 125.0:
            if h_obs == None: h_obs = hist_zh.Clone("h_obs") # take 125.0 GeV to add to observed (need to add background later as well)
            else: h_obs.Add(hist_zh)

        if not doPlot:
            continue
        # do plotting
        plotter.cfg = cfg
        
        cfg['ymax'] = 1.3*hist_zh.GetMaximum()
        
        canvas, padT, padB = plotter.canvasRatio()
        dummyT, dummyB = plotter.dummyRatio()
        
        ## TOP PAD ##
        canvas.cd()
        padT.Draw()
        padT.cd()
        dummyT.Draw("HIST")
        
        hist_zh.SetLineColor(ROOT.kBlack)
        hist_zh.SetLineWidth(2)
        hist_zh.Draw("HIST E SAME")
        
        latex = ROOT.TLatex()
        latex.SetNDC()
        latex.SetTextSize(0.045)
        latex.SetTextColor(1)
        latex.SetTextFont(42)
        latex.SetTextAlign(13)
        latex.DrawLatex(0.2, 0.88, label)
        plotter.auxRatio()
        
        ## BOTTOM PAD ##
        canvas.cd()
        padB.Draw()
        padB.cd()
        dummyB.Draw("HIST")

        line = ROOT.TLine(120, 0, 140, 0)
        line.SetLineColor(ROOT.kBlue+2)
        line.SetLineWidth(2)
        line.Draw("SAME")
        
      
        canvas.Modify()
        canvas.Update()
        canvas.Draw()
        canvas.SaveAs("%s/hist_mH%s_%s.png" % (outDir, mH_, selection))
        canvas.SaveAs("%s/hist_mH%s_%s.pdf" % (outDir, mH_, selection))
        
    
        del dummyB
        del dummyT
        del padT
        del padB
        del canvas
        

        
  
  


def doBackgrounds():

    global h_obs
    if flavor == "mumu":
        procs = [ 'p8_ee_WW_ecm365',
                  'wzp6_egamma_eZ_Zmumu_ecm365',
                  'wzp6_gammae_eZ_Zmumu_ecm365',
                  'wzp6_ee_mumu_ecm365',
                  'p8_ee_ZZ_ecm365',
                  ##rare  
                  "wzp6_ee_tautau_ecm365",
                  "wzp6_gaga_mumu_60_ecm365",
                  "wzp6_gaga_tautau_60_ecm365",
                  "wzp6_ee_nuenueZ_ecm365"
                ]
    
    elif flavor == "ee":
        procs = [ 'p8_ee_WW_ecm365',
                  'wzp6_egamma_eZ_Zee_ecm365',
                  'wzp6_gammae_eZ_Zee_ecm365',
                  'wzp6_ee_ee_Mee_30_150_ecm365',
                  'p8_ee_ZZ_ecm365',
                  ##rare  
                  "wzp6_ee_tautau_ecm365",
                  "wzp6_gaga_ee_60_ecm365",
                  "wzp6_gaga_tautau_60_ecm365",
                  "wzp6_ee_nuenueZ_ecm365"
                ]
    

    if flavor == "qq":
        hist_bkg = sumProcs(qq_background_procs(), selection, hName, "background")
        if h_obs == None: h_obs = hist_bkg.Clone("h_obs")
        else: h_obs.Add(hist_bkg)
        hists.append(hist_bkg)
    else:
        hist_bkg = None
        for proc in procs:

            fIn = ROOT.TFile(baseFileName.format(sampleName=proc,selection=selection))
            hist = copy.deepcopy(fIn.Get(hName))
            fIn.Close()
            hist.Scale(lumi)
            hist = hist.Rebin(rebin)

            if hist_bkg == None: hist_bkg = hist
            else: hist_bkg.Add(hist)

            # add to observed
            if h_obs == None: h_obs = hist.Clone("h_obs")
            else: h_obs.Add(hist)


        hist_bkg.SetName("background")
        hists.append(hist_bkg)

    if not doPlot:
        return
    ########### PLOTTING ###########
    cfg = {

        'logy'              : False,
        'logx'              : False,
    
        'xmin'              : 120 if not "Score" in hName else 0,
        'xmax'              : 140 if not "Score" in hName else 1,
        'ymin'              : 0,
        'ymax'              : 1.3*hist_bkg.GetMaximum(),
        
        'xtitle'            : "Recoil mass (GeV)" if not "Score" in hName else "BDT Score",
        'ytitle'            : "Events / 0.1 GeV" if not "Score" in hName else "Events / 0.05",
        
        'topRight'          : "BKGS, #sqrt{s} = 365 GeV, 3.12 ab^{#minus1}", 
        'topLeft'           : "#bf{FCC-ee} #scale[0.7]{#it{Simulation}}",
        
        'ratiofraction'     : 0.25,
        'ytitleR'           : "Pull",
        'yminR'             : -3.5,
        'ymaxR'             : 3.5,
    }
    
    plotter.cfg = cfg
    
    canvas, padT, padB = plotter.canvasRatio()
    dummyT, dummyB = plotter.dummyRatio()
    
    ## TOP PAD ##
    canvas.cd()
    padT.Draw()
    padT.cd()
    dummyT.Draw("HIST")
    
    hist_bkg.SetLineColor(ROOT.kBlack)
    hist_bkg.SetLineWidth(2)
    hist_bkg.Draw("HIST E SAME")
    

        
    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextSize(0.045)
    latex.SetTextColor(1)
    latex.SetTextFont(42)
    latex.SetTextAlign(13)
    latex.DrawLatex(0.2, 0.88, label)

    plotter.auxRatio()
    
    ## BOTTOM PAD ##
    canvas.cd()
    padB.Draw()
    padB.cd()
    dummyB.Draw("HIST")

    line = ROOT.TLine(120, 0, 140, 0)
    line.SetLineColor(ROOT.kBlue+2)
    line.SetLineWidth(2)
    line.Draw("SAME")
    
  
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/binned_bkg_%s.png" % (outDir, selection))  
    canvas.SaveAs("%s/binned_bkg_%s.pdf" % (outDir, selection))  
    
  

 
if __name__ == "__main__":
    flavor = sys.argv[1] if len(sys.argv) > 1 else "mumu"
    
    if flavor == "mumu":
        label = "#mu^{#plus}#mu^{#minus}"
    elif flavor == "ee":
        label = "e^{#plus}e^{#minus}"
    elif flavor == "qq":
        label = "q#bar{q}"

    baseFileName = "/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper/S365/" + flavor + "/BDT_analysis_samples/syst/{sampleName}_{selection}_histo.root"
    hName = "BDT_Score"
    runDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_binned_BDTScore_{flavor}".format(flavor=flavor))
    outDir = "/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper/S365/{flavor}/combine_binned_BDTScore".format(flavor=flavor)
    if not os.path.exists(outDir): os.makedirs(outDir)
    if not os.path.exists(runDir): os.makedirs(runDir)
    lumi = 3120000.
    rebin = 1
    h_obs = None # should hold the data_obs = sum of signal and backgrounds

    hists = []
    hist_zh = None 
    # define temporary output workspace
    w_tmp = ROOT.RooWorkspace("w_tmp", "workspace")
    w = ROOT.RooWorkspace("w", "workspace") # final workspace for combine

    # the qq cross-check fits the FULL BDT-score shape (no working-point cut), like
    # the leptonic channels; the primary 2D fit (makeWS_2D_qq.py) applies the MVA cut
    selection = "sel_Baseline_nomva" if flavor == "qq" else "sel_Baseline_no_costhetamiss"
    doSignal()
    doBackgrounds()
    if flavor == "qq":
        # no BES samples for hadronic Z decays; jet scale replaces the lepton scale
        doSyst("JETSCALE")
        doSyst("SQRTS")
    else:
        doSyst("BES")
        doSyst("LEPSCALE")
        doSyst("SQRTS")

    h_obs.SetName("data_obs")
    
    fOut = ROOT.TFile("%s/datacard.root" % runDir, "RECREATE")
    for h in hists:
        h.Write()
    h_obs.Write()
    fOut.Close()

    # build the Combine workspace based on the datacard, save it to ws.root    
    cmd = "cp %s/datacard_binned_%s.txt %s/" % (os.path.dirname(os.path.abspath(__file__)), flavor, runDir)
    subprocess.call(cmd, shell=True)
    
    
    cmd = "sed -i 's/bkg/bkg_{flavor}/g' datacard_binned_{flavor}.txt".format(flavor=flavor)
    subprocess.call(cmd, shell=True, cwd=runDir)
    
    cmd = "text2workspace.py datacard_binned_%s.txt -o ws.root -v 10" % flavor
    subprocess.call(cmd, shell=True, cwd=runDir)
