
import sys,copy,array,os,subprocess
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)

doPlot = True
if doPlot:
    import plotter

def doSyst(Syst):

    proc_Up = "wzp6_ee_{flavor}H_ecm240".format(flavor=flavor)
    proc_Down = "wzp6_ee_{flavor}H_ecm240".format(flavor=flavor)
    selection_Up = "sel_Baseline_no_costhetamiss"
    selection_Down = "sel_Baseline_no_costhetamiss"
    if Syst == "BES":
        proc_Up = "wzp6_ee_{flavor}H_BES-higher-1pc_ecm240".format(flavor=flavor)
        proc_Down = "wzp6_ee_{flavor}H_BES-lower-1pc_ecm240".format(flavor=flavor)
        hName_Up = "BDT_Score"
        hName_Down = "BDT_Score"
        syst_name = "BES"
    elif Syst == "SQRTS":
        selection_Up = "sel_Baseline_no_costhetamiss_sqrtsup"
        selection_Down = "sel_Baseline_no_costhetamiss_sqrtsdw" 
        hName_Up    = "BDT_Score"
        hName_Down  = "BDT_Score"
        syst_name = "SQRTS"

    elif Syst == "LEPSCALE":
        selection_Up = "sel_Baseline_no_costhetamiss_scaleup"
        selection_Down = "sel_Baseline_no_costhetamiss_scaledw"
        hName_Up = "BDT_Score_scaleup"
        hName_Down = "BDT_Score_scaledw"
        if flavor == "mumu":
            syst_name = "MUSCALE"
        elif flavor == "ee":
            syst_name = "ELSCALE"
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
        
        'topRight'          : "ZH, #sqrt{s} = 240 GeV, 7.2 ab^{#minus1}", 
        'topLeft'           : "#bf{FCC-ee} #scale[0.7]{#it{Simulation}}",
        
        'ratiofraction'     : 0.25,
        'ytitleR'           : "Ratio",
        'yminR'             : 0.9,
        'ymaxR'             : 1.1,
    }
    

    
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
        procs = ["wzp6_ee_mumuH_ecm240"]

    if flavor == "ee":
        procs = ["wzp6_ee_eeH_ecm240"]

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
        
        'topRight'          : "ZH, #sqrt{s} = 240 GeV, 7.2 ab^{#minus1}", 
        'topLeft'           : "#bf{FCC-ee} #scale[0.7]{#it{Simulation}}",
        
        'ratiofraction'     : 0.25,
        'ytitleR'           : "Pull",
        'yminR'             : -3.5,
        'ymaxR'             : 3.5,
    }
    
   
    for i, proc in enumerate(procs):
    
        fIn = ROOT.TFile(baseFileName.format(sampleName=proc,selection=selection))
        
        mH = mHs[i]
        mH_ = ("%.2f" % mH).replace(".", "p")

        hist_zh = copy.deepcopy(fIn.Get(hName))
        hist_zh = hist_zh.Rebin(rebin)
        hist_zh.SetName("signal")
        hist_zh.Scale(lumi)
        hists.append(hist_zh)
        fIn.Close()
        
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
        procs = [ 'p8_ee_WW_ecm240',
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
        procs = [ 'p8_ee_WW_ecm240',
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
        
        'topRight'          : "BKGS, #sqrt{s} = 240 GeV, 7.2 ab^{#minus1}", 
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

    #flavor = "ee"
    flavor = "mumu"
    
    if flavor == "mumu":
        label = "#mu^{#plus}#mu^{#minus}"
    elif flavor == "ee":
        label = "e^{#plus}e^{#minus}"

    baseFileName = "/eos/user/l/lia/FCCee/MidTerm/" + flavor + "/BDT_analysis_samples/syst/{sampleName}_{selection}_histo.root"    
    hName = "BDT_Score"
    runDir = "combine/run_binned_BDTScore_{flavor}/".format(flavor=flavor)
    outDir = "/eos/user/l/lia/FCCee/MidTerm/{flavor}/ZH_mass_xsec/combine_binned_BDTScore/".format(flavor=flavor)
    if not os.path.exists(outDir): os.makedirs(outDir)
    if not os.path.exists(runDir): os.makedirs(runDir)
    lumi = 10800000.
    rebin = 1
    h_obs = None # should hold the data_obs = sum of signal and backgrounds

    hists = []
    hist_zh = None 
    # define temporary output workspace
    w_tmp = ROOT.RooWorkspace("w_tmp", "workspace")
    w = ROOT.RooWorkspace("w", "workspace") # final workspace for combine

    selection = "sel_Baseline_no_costhetamiss"    
    doSignal()
    doBackgrounds()
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
    cmd = "cp scripts/ZH_mass_xsec_MidTerm/combine/datacard_binned_%s.txt %s/" % (flavor, runDir)
    subprocess.call(cmd, shell=True)
    
    
    #cmd = "sed -i 's/bkg/bkg_{flavor}/g' datacard_binned.txt".format(flavor=flavor)
    #subprocess.call(cmd, shell=True, cwd=runDir)
    
    cmd = "text2workspace.py datacard_binned_%s.txt -o ws.root -v 10" % flavor
    subprocess.call(cmd, shell=True, cwd=runDir)
