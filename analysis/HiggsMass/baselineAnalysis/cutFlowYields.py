
import sys,array,ROOT,math,os,copy

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)


sys.path.insert(0, '/afs/cern.ch/work/j/jaeyserm/pythonlibs')
import plotter
import datasets as ds

def getYield(proc, sel):

    hName = "cosTheta_miss" # take an event variable, always filled regardless the cut
    
    xMin=-1e6
    xMax=1e6
        
    fIn = ROOT.TFile("%s/%s_hists.root" % (histDir, proc))
    h = fIn.Get("%s_%s" % (hName, sel))
    h.Scale(lumi*ds.datasets[proc]['xsec']*1e6/ds.datasets[proc]['nevents'])


    xbinMin = h.GetXaxis().FindBin(xMin)
    xbinMax = h.GetXaxis().FindBin(xMax)
    
 
    evYield, err = 0, 0
    for i in range(xbinMin, xbinMax):
    
        evYield += h.GetBinContent(i) 
        err += h.GetBinError(i)**2
    
    err = err**0.5

    y = h.Integral()
    fIn.Close()
    
    return y, err

def makePlot():
	

    totEntries = 1 + len(bkgs)
    #leg = ROOT.TLegend(.5, 1.0-totEntries*0.06, .92, .90)
    leg = ROOT.TLegend(.5, 0.97-(len(bkgs)+2)*0.055, .8, .90)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.035)
    
    sig = ["wzp6_ee_mumuH_ecm240"]
    h_sig = ROOT.TH1D("h_sig", "h_sig", 10, 0, 10)  
    for j,sel in enumerate(sels):
            
        yield_ = 0.
        for i,sig in enumerate(sigs): 
        
            y, err = getYield(sig, sel)
            yield_ += y
            
        h_sig.SetBinContent(j+1, yield_*10)
		
    h_sig.SetLineColor(ROOT.TColor.GetColor("#BF2229"))
    h_sig.SetLineWidth(4)
    h_sig.SetLineStyle(1)
    leg.AddEntry(h_sig, "ZH (10#times)", "L")
    #print("SIG", h_sig.GetBinContent(6))


	
    # Get all bkg histograms
    st = ROOT.THStack()
    st.SetName("stack")
    h_bkg = ROOT.TH1D("h_bkg", "h_bkg", 10, 0, 10)
    for i,bkg in enumerate(bkgs):
		
        hist = ROOT.TH1D(bkg, bkg, 10, 0, 10)
        
        for j,sel in enumerate(sels):
        
            yield_ = 0.
            
            for x in bgks_cfg[bkg]:
            
                y, err = getYield(x, sel)
                yield_ += y
		
            hist.SetBinContent(j+1, yield_)
		
        hist.SetFillColor(bkgs_colors[i])
        hist.SetLineColor(ROOT.kBlack)
        hist.SetLineWidth(1)
        hist.SetLineStyle(1)
		
        leg.AddEntry(hist, bkgs_legends[i], "F")
        st.Add(hist)
        h_bkg.Add(hist)
        
        #print(bkg, hist.GetBinContent(6))


    h_bkg.SetLineColor(ROOT.kBlack)
    h_bkg.SetLineWidth(2)
	


    ########### PLOTTING ###########
    cfg = {

        'logy'              : True,
        'logx'              : False,
        
        'xmin'              : 0,
        'xmax'              : 6,
        'ymin'              : 1e4,
        'ymax'              : 1e9 ,
            
        'xtitle'            : "",
        'ytitle'            : "Events",
            
        'topRight'          : "#sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Simulation}}",
        }
        
    plotter.cfg = cfg
        
    canvas = plotter.canvas()
    canvas.SetGrid()
    dummy = plotter.dummy(len(sels))
    dummy.GetXaxis().SetLabelSize(0.8*dummy.GetXaxis().GetLabelSize())
    dummy.GetXaxis().SetLabelOffset(1.3*dummy.GetXaxis().GetLabelOffset())
    for i,label in enumerate(labels): dummy.GetXaxis().SetBinLabel(i+1, label)
    dummy.GetXaxis().LabelsOption("u")
    
    dummy.Draw("HIST")
    
    st.Draw("SAME")
    h_bkg.Draw("SAME")
    h_sig.Draw("SAME")
    leg.Draw("SAME")
    
            
    plotter.aux()
    canvas.RedrawAxis()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/cutFlow.png" % outDir)
    canvas.SaveAs("%s/cutFlow.pdf" % outDir)
    
	
	
	
if __name__ == "__main__":

    lumi = 5.0 # integrated lumi in /ab
    histDir = "/eos/user/j/jaeyserm/analysis/FCCee/ZH/"
    outDir = "/eos/user/j/jaeyserm/www/FCCee/ZH/baselineAnalysis"
	
    sels = ["sel0", "sel1", "sel2", "sel3", "sel4", "sel5"]
    labels = ["All events", "#mu^{+}#mu^{#minus} pair", "86 < m_{#mu^{+}#mu^{#minus}} < 96", "20 < p_{T}^{#mu^{+}#mu^{#minus}} < 70", "|cos#theta_{missing}| < 0.98", "120 < m_{rec} < 140"]
    
    sigs = ["wzp6_ee_mumuH_ecm240", "wzp6_ee_tautauH_ecm240", "wzp6_ee_eeH_ecm240", "wzp6_ee_nunuH_ecm240", "wzp6_ee_qqH_ecm240"]
    
    bkgs = ["WW", "ZZ", "Zg", "RARE"] # this is the order of the plot
    bkgs_legends = ["W^{+}(#nu#mu^{+})W^{#minus}(#bar{#nu}#mu^{#minus})", "ZZ", "Z/#gamma^{*} #rightarrow l#bar{l}", "Rare (e(e)Z, #gamma#gamma#rightarrow#mu#mu,#tau#tau)"]
    bkgs_colors = [ROOT.TColor.GetColor(248, 206, 104), ROOT.TColor.GetColor(222, 90, 106), ROOT.TColor.GetColor(100, 192, 232), ROOT.TColor.GetColor(155, 152, 204)] # from
    bgks_cfg = { 
        "WW"	: ["p8_ee_WW_mumu_ecm240"],
        "ZZ"	: ["p8_ee_ZZ_ecm240"],
        "Zg"    : ["p8_ee_Zll_ecm240"],
        "RARE"	: ["wzp6_egamma_eZ_Zmumu_ecm240", "wzp6_gammae_eZ_Zmumu_ecm240", "wzp6_gaga_mumu_60_ecm240", "wzp6_gaga_tautau_60_ecm240"],
    }
    
    makePlot()
    
    
    
    ## event yields
    procs = ["wzp6_ee_mumuH_ecm240", "wzp6_ee_mumuH_noISR_ecm240", "wzp6_noBES_ee_mumuH_ecm240", "wzp6_ee_mumuH_ISRnoRecoil_ecm240", "", "wzp6_ee_mumuH_BES-higher-6pc_ecm240", "wzp6_ee_mumuH_BES-lower-6pc_ecm240", "wzp6_ee_mumuH_BES-lower-1pc_ecm240", "wzp6_ee_mumuH_BES-higher-1pc_ecm240", "", "wzp6_ee_tautauH_ecm240", "wzp6_ee_eeH_ecm240", "wzp6_ee_nunuH_ecm240", "wzp6_ee_qqH_ecm240", "", "wzp6_gaga_mumu_60_ecm240", "wzp6_gaga_tautau_60_ecm240", "wzp6_egamma_eZ_Zmumu_ecm240", "wzp6_gammae_eZ_Zmumu_ecm240", "", "p8_ee_ZZ_ecm240", "p8_ee_WW_mumu_ecm240", "p8_ee_Zll_ecm240"]
    
    
    
    print("%-50s %-20s %-20s %-20s" % ("Process", "Events", "Stat. Error", "Sqrt(evts)"))
    for proc in procs:
     
        if proc == "":
            print()
            continue
            
        evYield, err = getYield(proc, "sel5")
        print("%-50s %-20.2f %-20.2f %-20.2f" % (proc, evYield, err, math.sqrt(evYield)))
