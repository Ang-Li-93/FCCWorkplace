
import sys,array,ROOT,math,os,copy

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)


sys.path.insert(0, '/afs/cern.ch/work/l/lia/private/FCC/FCCeeHiggsStudies/python')
import plotter
import datasets as ds


def getHist(proc, sel, hName, rebin):

    fIn = ROOT.TFile("%s/%s_hists.root" % (histDir, proc))
    h = copy.deepcopy(fIn.Get("%s_%s" % (hName, sel)))
    h.Rebin(rebin)
    h.Scale(lumi*ds.datasets[proc]['xsec']*1e6/ds.datasets[proc]['nevents'])
    fIn.Close()
    return h



def recoil_log(sel):

    fOut = "zed_leptonic_recoil_m"
    xMin, xMax = 0, 150
    rebin = 500

    hName = "zed_leptonic_recoil_m"

    st = ROOT.THStack()
    st.SetName("stack")
        
    leg = ROOT.TLegend(.4, 0.97-(len(bkgs)+2)*0.055, .7, .90)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.035)
    


    h_sig = None
    for sig in sigs:
    
        h = getHist(sig, sel, hName, rebin)
        if h_sig == None: h_sig = h
        else: h_sig.Add(h)
		
    h_sig.SetLineColor(ROOT.TColor.GetColor("#BF2229"))
    h_sig.SetLineWidth(4)
    h_sig.SetLineStyle(1)
    leg.AddEntry(h_sig, sigLegend, "L") #  (10#times)

    
    # Get all bkg histograms
    st = ROOT.THStack()
    st.SetName("stack")
    h_bkg = None
    for i,bkg in enumerate(bkgs):
		
        hist = None
        for x in bgks_cfg[bkg]:
            
            h = getHist(x, sel, hName, rebin)
		
            if hist == None: hist = h
            else: hist.Add(h)
		
        hist.SetName(bkg)
        hist.SetFillColor(bkgs_colors[i])
        hist.SetLineColor(ROOT.kBlack)
        hist.SetLineWidth(1)
        hist.SetLineStyle(1)
		
        leg.AddEntry(hist, bkgs_legends[i], "F")
        st.Add(hist)
        if h_bkg == None:
            h_bkg = copy.deepcopy(hist)
            h_bkg.SetName("h_bkg")
        else: h_bkg.Add(hist)
        

    
    yMax = math.ceil(h_bkg.GetMaximum()*100)/10.
    

    cfg = {

        'logy'              : True,
        'logx'              : False,
        
        'xmin'              : xMin,
        'xmax'              : xMax,
        'ymin'              : 1e2,
        'ymax'              : 1e5,
            
        'xtitle'            : "m_{rec} (GeV)",
        'ytitle'            : "Events / 0.5 GeV",
            
        'topRight'          : "#sqrt{s} = 240 GeV, 5 ab^{#minus1}",
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Simulation}}",

    }
        

    plotter.cfg = cfg
    canvas = plotter.canvas()
        
    dummy = plotter.dummy()
    dummy.Draw("HIST")
        
    st.Draw("HIST SAME")
    
    
    '''
    hTot_err = hTot.Clone("hTot_err")
    hTot_err.SetFillColor(ROOT.kBlack)
    hTot_err.SetMarkerColor(ROOT.kBlack)
    hTot_err.SetFillStyle(3004)
    leg.AddEntry(hTot_err, "Stat. Unc.", "F")
    '''
    
    h_bkg.SetLineColor(ROOT.kBlack)
    h_bkg.SetFillColor(0)
    h_bkg.SetLineWidth(2)
    #hTot_err.Draw("E2 SAME")
    h_bkg.Draw("HIST SAME")
    
    h_sig.Draw("HIST SAME")
    
    leg.Draw("SAME")
        
    canvas.SetGrid()
    canvas.Modify()
    canvas.Update()

    plotter.aux()
    ROOT.gPad.SetTicks()
    ROOT.gPad.RedrawAxis()

    canvas.SaveAs("%s/recoil_%s.png" % (outDir, sel))
    canvas.SaveAs("%s/recoil_%s.pdf" % (outDir, sel))
    canvas.Close()



def recoil_lin(sel):

    fOut = "zed_leptonic_recoil_m"
    xMin, xMax = 0, 150
    rebin = 500

    hName = "zed_leptonic_recoil_m"

    st = ROOT.THStack()
    st.SetName("stack")
        
    leg = ROOT.TLegend(.4, 0.97-(len(bkgs)+2)*0.055, .7, .90)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.035)
    


    h_sig = None
    for sig in sigs:
    
        h = getHist(sig, sel, hName, rebin)
        if h_sig == None: h_sig = h
        else: h_sig.Add(h)
		
    h_sig.SetLineColor(ROOT.TColor.GetColor("#BF2229"))
    h_sig.SetLineWidth(4)
    h_sig.SetLineStyle(1)
    leg.AddEntry(h_sig, sigLegend, "L") #  (10#times)

    
    # Get all bkg histograms
    st = ROOT.THStack()
    st.SetName("stack")
    h_bkg = None
    for i,bkg in enumerate(bkgs):
		
        hist = None
        for x in bgks_cfg[bkg]:
            
            h = getHist(x, sel, hName, rebin)
		
            if hist == None: hist = h
            else: hist.Add(h)
		
        hist.SetName(bkg)
        hist.SetFillColor(bkgs_colors[i])
        hist.SetLineColor(ROOT.kBlack)
        hist.SetLineWidth(1)
        hist.SetLineStyle(1)
		
        leg.AddEntry(hist, bkgs_legends[i], "F")
        st.Add(hist)
        if h_bkg == None:
            h_bkg = copy.deepcopy(hist)
            h_bkg.SetName("h_bkg")
        else: h_bkg.Add(hist)
        

    
    yMax = math.ceil(h_bkg.GetMaximum()*100)/10.
    

    cfg = {

        'logy'              : False,
        'logx'              : False,
        
        'xmin'              : xMin,
        'xmax'              : xMax,
        'ymin'              : 0,
        'ymax'              : 1.5e4,
            
        'xtitle'            : "m_{rec} (GeV)",
        'ytitle'            : "Events / 0.5 GeV",
            
        'topRight'          : "#sqrt{s} = 240 GeV, 5 ab^{#minus1}",
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Simulation}}",

    }
        

    plotter.cfg = cfg
    canvas = plotter.canvas()
        
    dummy = plotter.dummy()
    dummy.Draw("HIST")
        
    st.Draw("HIST SAME")
    
    
    '''
    hTot_err = hTot.Clone("hTot_err")
    hTot_err.SetFillColor(ROOT.kBlack)
    hTot_err.SetMarkerColor(ROOT.kBlack)
    hTot_err.SetFillStyle(3004)
    leg.AddEntry(hTot_err, "Stat. Unc.", "F")
    '''
    
    h_bkg.SetLineColor(ROOT.kBlack)
    h_bkg.SetFillColor(0)
    h_bkg.SetLineWidth(2)
    #hTot_err.Draw("E2 SAME")
    h_bkg.Draw("HIST SAME")
    
    h_sig.Draw("HIST SAME")
    
    leg.Draw("SAME")
        
    canvas.SetGrid()
    canvas.Modify()
    canvas.Update()

    plotter.aux()
    ROOT.gPad.SetTicks()
    ROOT.gPad.RedrawAxis()

    canvas.SaveAs("%s/recoil_lin_%s.png" % (outDir, sel))
    canvas.SaveAs("%s/recoil_lin_%s.pdf" % (outDir, sel))
    canvas.Close()



def recoil_lin_zoom(sel):

    fOut = "zed_leptonic_recoil_m"
    xMin, xMax = 120, 140
    rebin = 100

    hName = "zed_leptonic_recoil_m"

    st = ROOT.THStack()
    st.SetName("stack")
        
    leg = ROOT.TLegend(.4, 0.97-(len(bkgs)+2)*0.055, .7, .90)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.035)
    


    h_sig = None
    for sig in sigs:
    
        h = getHist(sig, sel, hName, rebin)
        if h_sig == None: h_sig = h
        else: h_sig.Add(h)
		
    h_sig.SetLineColor(ROOT.TColor.GetColor("#BF2229"))
    h_sig.SetLineWidth(4)
    h_sig.SetLineStyle(1)
    leg.AddEntry(h_sig, sigLegend, "L") #  (10#times)

    
    # Get all bkg histograms
    st = ROOT.THStack()
    st.SetName("stack")
    h_bkg = None
    for i,bkg in enumerate(bkgs):
		
        hist = None
        for x in bgks_cfg[bkg]:
            
            h = getHist(x, sel, hName, rebin)
		
            if hist == None: hist = h
            else: hist.Add(h)
		
        hist.SetName(bkg)
        hist.SetFillColor(bkgs_colors[i])
        hist.SetLineColor(ROOT.kBlack)
        hist.SetLineWidth(1)
        hist.SetLineStyle(1)
		
        leg.AddEntry(hist, bkgs_legends[i], "F")
        st.Add(hist)
        if h_bkg == None:
            h_bkg = copy.deepcopy(hist)
            h_bkg.SetName("h_bkg")
        else: h_bkg.Add(hist)
        

    
    yMax = math.ceil(h_bkg.GetMaximum()*100)/10.
    

    cfg = {

        'logy'              : False,
        'logx'              : False,
        
        'xmin'              : xMin,
        'xmax'              : xMax,
        'ymin'              : 0,
        'ymax'              : 1000,
            
        'xtitle'            : "m_{rec} (GeV)",
        'ytitle'            : "Events / 0.1 GeV",
            
        'topRight'          : "#sqrt{s} = 240 GeV, 5 ab^{#minus1}",
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Simulation}}",

    }
        

    plotter.cfg = cfg
    canvas = plotter.canvas()
        
    dummy = plotter.dummy()
    dummy.Draw("HIST")
        
    st.Draw("HIST SAME")
    
    
    '''
    hTot_err = hTot.Clone("hTot_err")
    hTot_err.SetFillColor(ROOT.kBlack)
    hTot_err.SetMarkerColor(ROOT.kBlack)
    hTot_err.SetFillStyle(3004)
    leg.AddEntry(hTot_err, "Stat. Unc.", "F")
    '''
    
    h_bkg.SetLineColor(ROOT.kBlack)
    h_bkg.SetFillColor(0)
    h_bkg.SetLineWidth(2)
    #hTot_err.Draw("E2 SAME")
    h_bkg.Draw("HIST SAME")
    
    h_sig.Draw("HIST SAME")
    
    leg.Draw("SAME")
        
    canvas.SetGrid()
    canvas.Modify()
    canvas.Update()

    plotter.aux()
    ROOT.gPad.SetTicks()
    ROOT.gPad.RedrawAxis()

    canvas.SaveAs("%s/recoil_lin_zoom_%s.png" % (outDir, sel))
    canvas.SaveAs("%s/recoil_lin_zoom_%s.pdf" % (outDir, sel))
    canvas.Close()



def mll(sel):

    fOut = "zed_leptonic_m"
    xMin, xMax = 0, 250
    rebin = 1500 # 3000 = /1GeV, 300 = 0.1 GeV

    hName = "zed_leptonic_m"

    st = ROOT.THStack()
    st.SetName("stack")
        
    leg = ROOT.TLegend(.47, 0.97-(len(bkgs)+2)*0.055, 0.47+0.3, .90)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.035)
    


    h_sig = None
    for sig in sigs:
    
        h = getHist(sig, sel, hName, rebin)
        if h_sig == None: h_sig = h
        else: h_sig.Add(h)
		
    h_sig.SetLineColor(ROOT.TColor.GetColor("#BF2229"))
    h_sig.SetLineWidth(4)
    h_sig.SetLineStyle(1)
    #h_sig.Scale(10)
    leg.AddEntry(h_sig, sigLegend, "L") #  (10#times)

    
    # Get all bkg histograms
    st = ROOT.THStack()
    st.SetName("stack")
    h_bkg = None
    for i,bkg in enumerate(bkgs):
		
        hist = None
        for x in bgks_cfg[bkg]:
            
            h = getHist(x, sel, hName, rebin)
		
            if hist == None: hist = h
            else: hist.Add(h)
		
        hist.SetName(bkg)
        hist.SetFillColor(bkgs_colors[i])
        hist.SetLineColor(ROOT.kBlack)
        hist.SetLineWidth(1)
        hist.SetLineStyle(1)
		
        leg.AddEntry(hist, bkgs_legends[i], "F")
        st.Add(hist)
        if h_bkg == None:
            h_bkg = copy.deepcopy(hist)
            h_bkg.SetName("h_bkg")
        else: h_bkg.Add(hist)
        

    
    yMax = math.ceil(h_bkg.GetMaximum()*100)/10.
    

    cfg = {

        'logy'              : True,
        'logx'              : False,
        
        'xmin'              : xMin,
        'xmax'              : xMax,
        'ymin'              : 1e3,
        'ymax'              : 1e7, # 3e6
            
        'xtitle'            : "m_{#mu^{+},#mu^{#minus}} (GeV)",
        'ytitle'            : "Events / 0.5 GeV",
            
        'topRight'          : "#sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Simulation}}",

    }
        

    plotter.cfg = cfg
    canvas = plotter.canvas()
        
    dummy = plotter.dummy()
    dummy.Draw("HIST")
        
    st.Draw("HIST SAME")
    
    ROOT.TGaxis.SetExponentOffset(-0.07,0.015)
    
    
    '''
    hTot_err = hTot.Clone("hTot_err")
    hTot_err.SetFillColor(ROOT.kBlack)
    hTot_err.SetMarkerColor(ROOT.kBlack)
    hTot_err.SetFillStyle(3004)
    leg.AddEntry(hTot_err, "Stat. Unc.", "F")
    '''
    
    h_bkg.SetLineColor(ROOT.kBlack)
    h_bkg.SetFillColor(0)
    h_bkg.SetLineWidth(2)
    #hTot_err.Draw("E2 SAME")
    h_bkg.Draw("HIST SAME")
    
    h_sig.Draw("HIST SAME")
    
    leg.Draw("SAME")
        
    canvas.SetGrid()
    canvas.Modify()
    canvas.Update()

    plotter.aux()
    ROOT.gPad.SetTicks()
    ROOT.gPad.RedrawAxis()

    canvas.SaveAs("%s/mll_%s.png" % (outDir, sel))
    canvas.SaveAs("%s/mll_%s.pdf" % (outDir, sel))
    canvas.Close()



def ptll(sel):

    fOut = "zed_leptonic_pt"
    xMin, xMax = 0, 120
    rebin = 1000

    hName = "zed_leptonic_pt"

    st = ROOT.THStack()
    st.SetName("stack")
        
    leg = ROOT.TLegend(.4, 0.97-(len(bkgs)+2)*0.055, .7, .90)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.035)
    


    h_sig = None
    for sig in sigs:
    
        h = getHist(sig, sel, hName, rebin)
        if h_sig == None: h_sig = h
        else: h_sig.Add(h)
		
    h_sig.SetLineColor(ROOT.TColor.GetColor("#BF2229"))
    h_sig.SetLineWidth(4)
    h_sig.SetLineStyle(1)
    #h_sig.Scale(10)
    leg.AddEntry(h_sig, sigLegend, "L") #  (10#times)

    
    # Get all bkg histograms
    st = ROOT.THStack()
    st.SetName("stack")
    h_bkg = None
    for i,bkg in enumerate(bkgs):
		
        hist = None
        for x in bgks_cfg[bkg]:
            
            h = getHist(x, sel, hName, rebin)
		
            if hist == None: hist = h
            else: hist.Add(h)
		
        hist.SetName(bkg)
        hist.SetFillColor(bkgs_colors[i])
        hist.SetLineColor(ROOT.kBlack)
        hist.SetLineWidth(1)
        hist.SetLineStyle(1)
		
        leg.AddEntry(hist, bkgs_legends[i], "F")
        st.Add(hist)
        if h_bkg == None:
            h_bkg = copy.deepcopy(hist)
            h_bkg.SetName("h_bkg")
        else: h_bkg.Add(hist)
        


    cfg = {

        'logy'              : True,
        'logx'              : False,
        
        'xmin'              : xMin,
        'xmax'              : xMax,
        'ymin'              : 1e2,
        'ymax'              : 1e7, # 3e6
            
        'xtitle'            : "p_{T}^{#mu^{+},#mu^{#minus}} (GeV)",
        'ytitle'            : "Events / 0.5 GeV",
            
        'topRight'          : "#sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Simulation}}",

    }
        

    plotter.cfg = cfg
    canvas = plotter.canvas()
        
    dummy = plotter.dummy()
    dummy.Draw("HIST")
        
    st.Draw("HIST SAME")
    
    ROOT.TGaxis.SetExponentOffset(-0.07,0.015)
    
    
    '''
    hTot_err = hTot.Clone("hTot_err")
    hTot_err.SetFillColor(ROOT.kBlack)
    hTot_err.SetMarkerColor(ROOT.kBlack)
    hTot_err.SetFillStyle(3004)
    leg.AddEntry(hTot_err, "Stat. Unc.", "F")
    '''
    
    h_bkg.SetLineColor(ROOT.kBlack)
    h_bkg.SetFillColor(0)
    h_bkg.SetLineWidth(2)
    #hTot_err.Draw("E2 SAME")
    h_bkg.Draw("HIST SAME")
    
    h_sig.Draw("HIST SAME")
    
    leg.Draw("SAME")
        
    canvas.SetGrid()
    canvas.Modify()
    canvas.Update()

    plotter.aux()
    ROOT.gPad.SetTicks()
    ROOT.gPad.RedrawAxis()

    canvas.SaveAs("%s/ptll_%s.png" % (outDir, sel))
    canvas.SaveAs("%s/ptll_%s.pdf" % (outDir, sel))
    canvas.Close()



def costhetamissing(sel):

    fOut = "costheta_missing"
    xMin, xMax = 0, 1
    rebin = 500

    hName = "cosTheta_miss"

    st = ROOT.THStack()
    st.SetName("stack")
        
    leg = ROOT.TLegend(.3, 0.97-(len(bkgs)+2)*0.055, .6, .90)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.035)
    


    h_sig = None
    for sig in sigs:
    
        h = getHist(sig, sel, hName, rebin)
        if h_sig == None: h_sig = h
        else: h_sig.Add(h)
		
    h_sig.SetLineColor(ROOT.TColor.GetColor("#BF2229"))
    h_sig.SetLineWidth(4)
    h_sig.SetLineStyle(1)
    #h_sig.Scale(10)
    leg.AddEntry(h_sig, sigLegend, "L") #  (10#times)

    
    # Get all bkg histograms
    st = ROOT.THStack()
    st.SetName("stack")
    h_bkg = None
    for i,bkg in enumerate(bkgs):
		
        hist = None
        for x in bgks_cfg[bkg]:
            
            h = getHist(x, sel, hName, rebin)
		
            if hist == None: hist = h
            else: hist.Add(h)
		
        hist.SetName(bkg)
        hist.SetFillColor(bkgs_colors[i])
        hist.SetLineColor(ROOT.kBlack)
        hist.SetLineWidth(1)
        hist.SetLineStyle(1)
		
        leg.AddEntry(hist, bkgs_legends[i], "F")
        st.Add(hist)
        if h_bkg == None:
            h_bkg = copy.deepcopy(hist)
            h_bkg.SetName("h_bkg")
        else: h_bkg.Add(hist)
        


    cfg = {

        'logy'              : True,
        'logx'              : False,
        
        'xmin'              : xMin,
        'xmax'              : xMax,
        'ymin'              : 1e2,
        'ymax'              : 1e6, # 3e6
            
        'xtitle'            : "|cos#theta_{missing}|",
        'ytitle'            : "Events",
            
        'topRight'          : "#sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Simulation}}",

    }
        

    plotter.cfg = cfg
    canvas = plotter.canvas()
        
    dummy = plotter.dummy()
    dummy.Draw("HIST")
        
    st.Draw("HIST SAME")
    
    ROOT.TGaxis.SetExponentOffset(-0.07,0.015)
    
    
    '''
    hTot_err = hTot.Clone("hTot_err")
    hTot_err.SetFillColor(ROOT.kBlack)
    hTot_err.SetMarkerColor(ROOT.kBlack)
    hTot_err.SetFillStyle(3004)
    leg.AddEntry(hTot_err, "Stat. Unc.", "F")
    '''
    
    h_bkg.SetLineColor(ROOT.kBlack)
    h_bkg.SetFillColor(0)
    h_bkg.SetLineWidth(2)
    #hTot_err.Draw("E2 SAME")
    h_bkg.Draw("HIST SAME")
    
    h_sig.Draw("HIST SAME")
    
    leg.Draw("SAME")
        
    canvas.SetGrid()
    canvas.Modify()
    canvas.Update()

    plotter.aux()
    ROOT.gPad.SetTicks()
    ROOT.gPad.RedrawAxis()

    canvas.SaveAs("%s/costheta_missing_%s.png" % (outDir, sel))
    canvas.SaveAs("%s/costheta_missing_%s.pdf" % (outDir, sel))
    canvas.Close()



	
if __name__ == "__main__":

    lumi = 5.0 # integrated lumi in /ab
    histDir = "/eos/home-l/lia/FCCee/mumu_Combine"
    outDir_ = "/eos/home-l/lia/FCCee/mumu_Combine/baselineAnalysis"
    
	
    
    sigs = ["wzp6_ee_mumuH_ecm240", "wzp6_ee_tautauH_ecm240", "wzp6_ee_eeH_ecm240", "wzp6_ee_nunuH_ecm240", "wzp6_ee_qqH_ecm240"]
    sigLegend = "ZH" # "ZH #rightarrow #mu^{+}#mu^{#minus}H"
	
    bkgs = ["WW", "ZZ", "Zg", "RARE"] # this is the order of the plot
    bkgs_legends = ["W^{+}(#nu#mu^{+})W^{#minus}(#bar{#nu}#mu^{#minus})", "ZZ", "Z/#gamma^{*} #rightarrow l#bar{l}", "Rare (e(e)Z, #gamma#gamma#rightarrow#mu#mu,#tau#tau)"]
    bkgs_colors = [ROOT.TColor.GetColor(248, 206, 104), ROOT.TColor.GetColor(222, 90, 106), ROOT.TColor.GetColor(100, 192, 232), ROOT.TColor.GetColor(155, 152, 204)] # from 
    bgks_cfg = { 
        "WW"	: ["p8_ee_WW_mumu_ecm240"],
        "ZZ"	: ["p8_ee_ZZ_ecm240"],
        "Zg"    : ["p8_ee_Zll_ecm240"],
        "RARE"	: ["wzp6_egamma_eZ_Zmumu_ecm240", "wzp6_gammae_eZ_Zmumu_ecm240", "wzp6_gaga_mumu_60_ecm240", "wzp6_gaga_tautau_60_ecm240"],
    }


    for sel in ["sel0", "sel1", "sel2", "sel3", "sel4", "sel5"]:
    
    
        outDir = "%s/plots_%s/" % (outDir_, sel)
        os.system("mkdir -p %s" % outDir)
        os.system("cp %s/../index.php %s" % (outDir, outDir))

        mll(sel)
        ptll(sel)
        costhetamissing(sel)
        recoil_log(sel)
        recoil_lin(sel)
        recoil_lin_zoom(sel)
