
import sys,copy,array,os,subprocess
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)

ROOT.gSystem.Load("libHiggsAnalysisCombinedLimit.so")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../python")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../baselineAnalysis")
import functions
import datasets as ds
import plotter

sumw2err = ROOT.kFALSE

    
def doSignal():

    global h_obs
    
    mHs = [124.9, 124.95, 125.0, 125.05, 125.1]
    procs = ["wzp6_ee_mumuH_mH-lower-100MeV_ecm240", "wzp6_ee_mumuH_mH-lower-50MeV_ecm240", "wzp6_ee_mumuH_ecm240", "wzp6_ee_mumuH_mH-higher-50MeV_ecm240", "wzp6_ee_mumuH_mH-higher-100MeV_ecm240"]
    recoilmass = w_tmp.var("zed_leptonic_recoil_m")
    MH = w_tmp.var("MH")
    
    param_yield, param_mh, param_mean, param_mean_gt, param_sigma, param_sigma_gt, param_alpha_1, param_alpha_2, param_n_1, param_n_2, param_cb_1, param_cb_2 = [], [], [], [], [], [], [], [], [], [], [], []
    param_yield_err, param_mean_err, param_sigma_err, param_mean_gt_err, param_sigma_gt_err, param_alpha_1_err, param_alpha_2_err, param_n_1_err, param_n_2_err, param_cb_1_err, param_cb_2_err  = [], [], [], [], [], [], [], [], [], [], []

    # recoil mass plot settings
    cfg = {

        'logy'              : False,
        'logx'              : False,
    
        'xmin'              : 120,
        'xmax'              : 140,
        'ymin'              : 0,
        'ymax'              : 1500,
        
        'xtitle'            : "Recoil mass (GeV)",
        'ytitle'            : "Events / 0.2 GeV",
        
        'topRight'          : "ZH, #sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Internal}}",
        
        'ratiofraction'     : 0.25,
        'ytitleR'           : "Pull",
        'yminR'             : -6,
        'ymaxR'             : 6,
    }
   
    for i, proc in enumerate(procs):
        
        mH = mHs[i]
        mH_ = ("%.2f" % mH).replace(".", "p")
        print("Do mH=%.2f" % mH)
       
        
        ### get the signal data
        print("%s/%s_hists.root" % (histDir, proc))
        fIn = ROOT.TFile("%s/%s_hists.root" % (histDir, proc))
        print("zed_leptonic_recoil_m_%s" % sel)
        hist_zh = copy.deepcopy(fIn.Get("zed_leptonic_recoil_m_%s" % sel))
        hist_zh.Scale(lumi*ds.datasets[proc]['xsec']*1e6/ds.datasets[proc]['nevents'])
        hist_zh.SetName("hist_zh_%s" % mH_)
        hist_zh = hist_zh.Rebin(rebin)
        rdh_zh = ROOT.RooDataHist("rdh_zh_%s" % mH_, "rdh_zh", ROOT.RooArgList(recoilmass), ROOT.RooFit.Import(hist_zh))
        yield_zh = rdh_zh.sum(False)
        fIn.Close()

        if mH == 125.0 and h_obs == None: h_obs = hist_zh.Clone("h_obs") # take 125.0 GeV to add to observed (need to add background later as well)
        
        

        ### fit parameter configuration of 2CBG
        
        # IDEA
        mean = ROOT.RooRealVar("mean_%s" % mH_, '', 1.25086e+02, mH-1., mH+1.)
        #sigma = ROOT.RooRealVar("sigma_%s" % mH_, '', 4.10819e-01, 0, 1)
        sigma = ROOT.RooRealVar("sigma_%s" % mH_, '', 4.1e-01) # fixed
        alpha_1 = ROOT.RooRealVar("alpha_1_%s" % mH_, '', -1.39903e-01, -10, 0)
        #alpha_1 = ROOT.RooRealVar("alpha_1_%s" % mH_, '', -0.14322)
        #alpha_2 = ROOT.RooRealVar("alpha_2_%s" % mH_, '', 3.65257e+00, 0, 10)
        alpha_2 = ROOT.RooRealVar("alpha_2_%s" % mH_, '', 3.60)
        #n_1 = ROOT.RooRealVar("n_1_%s" % mH_, '', 2.35540e+00, -10, 10)
        n_1 = ROOT.RooRealVar("n_1_%s" % mH_, '', 3.90)
        #n_2 = ROOT.RooRealVar("n_2_%s" % mH_, '', 4.51050e-01, -10, 10)
        n_2 = ROOT.RooRealVar("n_2_%s" % mH_, '', 0.6)

        mean_gt = ROOT.RooRealVar("mean_gt_%s" % mH_, '', 1.25442e+02, recoilMin, recoilMax)
        #sigma_gt = ROOT.RooRealVar("sigma_gt_%s" % mH_, '', 8.47732e-01, 0, 1)
        sigma_gt = ROOT.RooRealVar("sigma_gt_%s" % mH_, '', 0.842) # fixed  
        

        # IDEA_3T
        '''
        mean = ROOT.RooRealVar("mean_%s" % mH_, '', 1.25086e+02, mH-1., mH+1.)
        #sigma = ROOT.RooRealVar("sigma_%s" % mH_, '', 4.10819e-01, 0, 1)
        sigma = ROOT.RooRealVar("sigma_%s" % mH_, '', 0.371) # fixed
        alpha_1 = ROOT.RooRealVar("alpha_1_%s" % mH_, '', -1.39903e-01, -10, 0)
        #alpha_2 = ROOT.RooRealVar("alpha_2_%s" % mH_, '', 3.65257e+00, 0, 10)
        alpha_2 = ROOT.RooRealVar("alpha_2_%s" % mH_, '', 4.18)
        #n_1 = ROOT.RooRealVar("n_1_%s" % mH_, '', 2.35540e+00, -10, 10)
        n_1 = ROOT.RooRealVar("n_1_%s" % mH_, '', 3.46)
        #n_2 = ROOT.RooRealVar("n_2_%s" % mH_, '', 4.51050e-01, -10, 10)
        n_2 = ROOT.RooRealVar("n_2_%s" % mH_, '', 0.08)
        mean_gt = ROOT.RooRealVar("mean_gt_%s" % mH_, '', 1.25442e+02, recoilMin, recoilMax)
        #sigma_gt = ROOT.RooRealVar("sigma_gt_%s" % mH_, '', 8.47732e-01, 0, 1)
        sigma_gt = ROOT.RooRealVar("sigma_gt_%s" % mH_, '', 0.720) # fixed 
        '''

        # IDEA_FS
        '''
        mean = ROOT.RooRealVar("mean_%s" % mH_, '', 1.25086e+02, mH-1., mH+1.)
        #sigma = ROOT.RooRealVar("sigma_%s" % mH_, '', 4.10819e-01, 0, 1)
        sigma = ROOT.RooRealVar("sigma_%s" % mH_, '', 0.529) # fixed
        alpha_1 = ROOT.RooRealVar("alpha_1_%s" % mH_, '', -1.39903e-01, -10, 0)
        #alpha_2 = ROOT.RooRealVar("alpha_2_%s" % mH_, '', 3.65257e+00, 0, 10)
        alpha_2 = ROOT.RooRealVar("alpha_2_%s" % mH_, '', 3.34)
        #n_1 = ROOT.RooRealVar("n_1_%s" % mH_, '', 2.35540e+00, -10, 10)
        n_1 = ROOT.RooRealVar("n_1_%s" % mH_, '', 4.6)
        #n_2 = ROOT.RooRealVar("n_2_%s" % mH_, '', 4.51050e-01, -10, 10)
        n_2 = ROOT.RooRealVar("n_2_%s" % mH_, '', 0.41)
        mean_gt = ROOT.RooRealVar("mean_gt_%s" % mH_, '', 1.25442e+02, recoilMin, recoilMax)
        #sigma_gt = ROOT.RooRealVar("sigma_gt_%s" % mH_, '', 8.47732e-01, 0, 1)
        sigma_gt = ROOT.RooRealVar("sigma_gt_%s" % mH_, '', 1.115) # fixed
        '''
        # IDEA MC
        '''    
        mean = ROOT.RooRealVar("mean_%s" % mH_, '', 1.25086e+02, mH-1., mH+1.)
        #sigma = ROOT.RooRealVar("sigma_%s" % mH_, '', 4.10819e-01, 0, 1)
        sigma = ROOT.RooRealVar("sigma_%s" % mH_, '', 4.1e-01) # fixed
        alpha_1 = ROOT.RooRealVar("alpha_1_%s" % mH_, '', -1.39903e-01, -10, 0)
        #alpha_1 = ROOT.RooRealVar("alpha_1_%s" % mH_, '', -0.14322)
        #alpha_2 = ROOT.RooRealVar("alpha_2_%s" % mH_, '', 3.65257e+00, 0, 10)
        alpha_2 = ROOT.RooRealVar("alpha_2_%s" % mH_, '', 3.60)
        #n_1 = ROOT.RooRealVar("n_1_%s" % mH_, '', 2.35540e+00, -10, 10)
        n_1 = ROOT.RooRealVar("n_1_%s" % mH_, '', 3.90)
        #n_2 = ROOT.RooRealVar("n_2_%s" % mH_, '', 4.51050e-01, -10, 10)
        n_2 = ROOT.RooRealVar("n_2_%s" % mH_, '', 0.6)

        mean_gt = ROOT.RooRealVar("mean_gt_%s" % mH_, '', 1.25442e+02, recoilMin, recoilMax)
        #sigma_gt = ROOT.RooRealVar("sigma_gt_%s" % mH_, '', 8.47732e-01, 0, 1)
        sigma_gt = ROOT.RooRealVar("sigma_gt_%s" % mH_, '', 0.842) # fixed  
        '''        
           
        
        # construct the 2CBG and perform the fit: pdf = cb_1*cbs_1 + cb_2*cbs_2 + gauss (cb_1 and cb_2 are the fractions, floating)
        cbs_1 = ROOT.RooCBShape("CrystallBall_1_%s" % mH_, "CrystallBall_1", recoilmass, mean, sigma, alpha_1, n_1) # first CrystallBall
        cbs_2 = ROOT.RooCBShape("CrystallBall_2_%s" % mH_, "CrystallBall_2", recoilmass, mean, sigma, alpha_2, n_2) # second CrystallBall
        gauss = ROOT.RooGaussian("gauss_%s" % mH_, "gauss", recoilmass, mean_gt, sigma_gt) # the Gauss
        cb_1 = ROOT.RooRealVar("cb_1_%s" % mH_, '', 3.96333e-01 , 0, 1)
        cb_2 = ROOT.RooRealVar("cb_2_%s" % mH_, '', 4.75471e-01 , 0, 1)
        #cb_1 = ROOT.RooRealVar("cb_1_%s" % mH_, '', 0.458)
        #cb_2 = ROOT.RooRealVar("cb_2_%s" % mH_, '', 0.4114)
            
        sig = ROOT.RooAddPdf("sig_%s" % mH_, '', ROOT.RooArgList(cbs_1, cbs_2, gauss), ROOT.RooArgList(cb_1, cb_2)) # half of both CB functions
        sig_norm = ROOT.RooRealVar("sig_%s_norm" % mH_, '', yield_zh, 0, 1e6) # fix normalization
        sig_fit = ROOT.RooAddPdf("zh_model_%s" % mH_, '', ROOT.RooArgList(sig), ROOT.RooArgList(sig_norm))
        sig_fit.fitTo(rdh_zh, ROOT.RooFit.Extended(ROOT.kTRUE), ROOT.RooFit.SumW2Error(sumw2err))
        
        
        cb1__ = cb_1.getVal()
        cb2__ = cb_2.getVal()
        
        # do plotting
        plotter.cfg = cfg
        
        canvas, padT, padB = plotter.canvasRatio()
        dummyT, dummyB = plotter.dummyRatio()
        
        ## TOP PAD ##
        canvas.cd()
        padT.Draw()
        padT.cd()
        dummyT.Draw("HIST")
        
        plt = recoilmass.frame()
        plt.SetTitle("ZH signal")
        rdh_zh.plotOn(plt, ROOT.RooFit.Binning(200)) # , ROOT.RooFit.Normalization(yield_zh, ROOT.RooAbsReal.NumEvent)
        
        sig_fit.plotOn(plt, ROOT.RooFit.LineColor(ROOT.kRed))
        sig_fit.paramOn(plt, ROOT.RooFit.Format("NELU", ROOT.RooFit.AutoPrecision(2)), ROOT.RooFit.Layout(0.45, 0.9, 0.9))
        
        histpull = plt.pullHist()
        plt.Draw("SAME")
        
        plotter.auxRatio()
        
        ## BOTTOM PAD ##
        canvas.cd()
        padB.Draw()
        padB.cd()
        dummyB.Draw("HIST")
        

        plt = recoilmass.frame()
        plt.addPlotable(histpull, "P")
        plt.Draw("SAME")
        
        line = ROOT.TLine(120, 0, 140, 0)
        line.SetLineColor(ROOT.kBlue+2)
        line.SetLineWidth(2)
        line.Draw("SAME")
        
      
        canvas.Modify()
        canvas.Update()
        canvas.Draw()
        canvas.SaveAs("%s/fit_mH%s.png" % (outDir, mH_))
        canvas.SaveAs("%s/fit_mH%s.pdf" % (outDir, mH_))
        
    
        del dummyB
        del dummyT
        del padT
        del padB
        del canvas
        

        cfg['ymax'] = 2500
        plotter.cfg = cfg
        canvas = plotter.canvas()
        dummy = plotter.dummy()
        dummy.Draw("HIST")
        plt = w_tmp.var("zed_leptonic_recoil_m").frame()
        colors = [ROOT.kRed, ROOT.kBlue, ROOT.kBlack, ROOT.kGreen, ROOT.kCyan] 
        
        leg = ROOT.TLegend(.50, 0.7, .95, .90)
        leg.SetBorderSize(0)
        leg.SetFillStyle(0)
        leg.SetTextSize(0.04)
        leg.SetMargin(0.15)

        cbs_1.plotOn(plt, ROOT.RooFit.LineColor(ROOT.kRed), ROOT.RooFit.Normalization(yield_zh*cb1__, ROOT.RooAbsReal.NumEvent))
        cbs_2.plotOn(plt, ROOT.RooFit.LineColor(ROOT.kBlue), ROOT.RooFit.Normalization(yield_zh*cb2__, ROOT.RooAbsReal.NumEvent))
        gauss.plotOn(plt, ROOT.RooFit.LineColor(ROOT.kCyan), ROOT.RooFit.Normalization(yield_zh*(1.-cb1__-cb2__), ROOT.RooAbsReal.NumEvent))
        sig_fit.plotOn(plt, ROOT.RooFit.LineColor(ROOT.kBlack), ROOT.RooFit.Normalization(yield_zh, ROOT.RooAbsReal.NumEvent))     
        
            
        # define TGraphs for legend
        tmp1 = ROOT.TGraph()
        tmp1.SetPoint(0, 0, 0)
        tmp1.SetLineColor(ROOT.kBlack)
        tmp1.SetLineWidth(3)
        tmp1.Draw("SAME")
        leg.AddEntry(tmp1, "Total PDF", "L")
        
        tmp2 = ROOT.TGraph()
        tmp2.SetPoint(0, 0, 0)
        tmp2.SetLineColor(ROOT.kRed)
        tmp2.SetLineWidth(3)
        tmp2.Draw("SAME")
        leg.AddEntry(tmp2, "CB1", "L")
        
        tmp3 = ROOT.TGraph()
        tmp3.SetPoint(0, 0, 0)
        tmp3.SetLineColor(ROOT.kBlue)
        tmp3.SetLineWidth(3)
        tmp3.Draw("SAME")
        leg.AddEntry(tmp3, "CB2", "L")
        
        tmp4 = ROOT.TGraph()
        tmp4.SetPoint(0, 0, 0)
        tmp4.SetLineColor(ROOT.kCyan)
        tmp4.SetLineWidth(3)
        tmp4.Draw("SAME")
        leg.AddEntry(tmp4, "Gauss", "L")
        
        plt.Draw("SAME")
        leg.Draw()
        plotter.aux()
        canvas.Modify()
        canvas.Update()
        canvas.Draw()
        canvas.SaveAs("%s/fit_mH%s_decomposition.png" % (outDir, mH_))
        canvas.SaveAs("%s/fit_mH%s_decomposition.pdf" % (outDir, mH_))
        cfg['ymax'] = 1500
        
        
        # import
        getattr(w_tmp, 'import')(rdh_zh)
        getattr(w_tmp, 'import')(sig_fit)
        
        
        param_mh.append(mH)
        param_mean.append(mean.getVal())
        param_sigma.append(sigma.getVal())
        param_mean_gt.append(mean_gt.getVal())
        param_sigma_gt.append(sigma_gt.getVal())
        param_alpha_1.append(alpha_1.getVal())
        param_alpha_2.append(alpha_2.getVal())
        param_n_1.append(n_1.getVal())
        param_n_2.append(n_2.getVal())
        param_yield.append(sig_norm.getVal())
        param_cb_1.append(cb_1.getVal())
        param_cb_2.append(cb_2.getVal())
        
        param_mean_err.append(mean.getError())
        param_sigma_err.append(sigma.getError())
        param_mean_gt_err.append(mean.getError())
        param_sigma_gt_err.append(sigma.getError())
        param_alpha_1_err.append(alpha_1.getError())
        param_alpha_2_err.append(alpha_2.getError())
        param_n_1_err.append(n_1.getError())
        param_n_2_err.append(n_2.getError())
        param_yield_err.append(sig_norm.getError())
        param_cb_1_err.append(cb_1.getError())
        param_cb_2_err.append(cb_2.getError())

  
  
    ##################################
    # plot all fitted signals
    ##################################
    cfg['ymax'] = 2500
    cfg['xmin'] = 124
    cfg['xmax'] = 130
    plotter.cfg = cfg
    
    
    canvas = plotter.canvas()
    dummy = plotter.dummy()
    dummy.Draw("HIST")
    
    plt = w_tmp.var("zed_leptonic_recoil_m").frame()
    colors = [ROOT.kRed, ROOT.kBlue, ROOT.kBlack, ROOT.kGreen, ROOT.kCyan]
    for i, mH in enumerate(mHs):
        
        mH_ = ("%.2f" % mH).replace(".", "p")
    
        sig_fit = w_tmp.pdf("zh_model_%s" % mH_)
        # need to re-normalize the pdf, as the pdf is normalized to 1
        sig_fit.plotOn(plt, ROOT.RooFit.LineColor(colors[i]), ROOT.RooFit.Normalization(w_tmp.var("sig_%s_norm" % mH_).getVal(), ROOT.RooAbsReal.NumEvent))
        

    plt.Draw("SAME")
    

    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/fit_all.png" % (outDir))   
    canvas.SaveAs("%s/fit_all.pdf" % (outDir))  


    # make splines, to connect the fit parameters a function of the Higgs mass
    # plot them afterwards
    spline_mean = ROOT.RooSpline1D("spline_mean", "spline_mean", MH, len(param_mh), array.array('d', param_mh), array.array('d', param_mean))
    spline_sigma = ROOT.RooSpline1D("spline_sigma", "spline_sigma", MH, len(param_mh), array.array('d', param_mh), array.array('d', param_sigma))
    spline_mean_gt = ROOT.RooSpline1D("spline_mean_gt", "spline_mean_gt", MH, len(param_mh), array.array('d', param_mh), array.array('d', param_mean_gt))
    #spline_mean_gt = ROOT.RooFormulaVar("spline_mean_gt", "0.9728*@0 + 3.8228", ROOT.RooArgList(MH))
    spline_sigma_gt = ROOT.RooSpline1D("spline_sigma_gt", "spline_sigma_gt", MH, len(param_mh), array.array('d', param_mh), array.array('d', param_sigma_gt))
    spline_yield = ROOT.RooSpline1D("spline_yield", "spline_yield", MH, len(param_mh), array.array('d', param_mh), array.array('d', param_yield))
    spline_alpha_1 = ROOT.RooSpline1D("spline_alpha_1", "spline_alpha_1", MH, len(param_mh), array.array('d', param_mh), array.array('d', param_alpha_1))
    spline_alpha_2 = ROOT.RooSpline1D("spline_alpha_2", "spline_alpha_2", MH, len(param_mh), array.array('d', param_mh), array.array('d', param_alpha_2))
    spline_n_1 = ROOT.RooSpline1D("spline_n_1", "spline_n_1", MH, len(param_mh), array.array('d', param_mh), array.array('d', param_n_1))
    spline_n_2 = ROOT.RooSpline1D("spline_n_2", "spline_n_2", MH, len(param_mh), array.array('d', param_mh), array.array('d', param_n_2))
    spline_cb_1 = ROOT.RooSpline1D("spline_cb_1", "spline_cb_1", MH, len(param_mh), array.array('d', param_mh), array.array('d', param_cb_1))
    spline_cb_2 = ROOT.RooSpline1D("spline_cb_2", "spline_cb_2", MH, len(param_mh), array.array('d', param_mh), array.array('d', param_cb_2))
    
    
    ##################################
    # mean
    ##################################
    graph_mean = ROOT.TGraphErrors(len(param_mh), array.array('d', param_mh), array.array('d', param_mean), array.array('d', [0]*len(param_mean_err)), array.array('d', param_mean_err))
    
    cfg = {

        'logy'              : False,
        'logx'              : False,
    
        'xmin'              : 124.8,
        'xmax'              : 125.2,
        'ymin'              : 0.999*min(param_mean),
        'ymax'              : 1.001*max(param_mean),
        
        'xtitle'            : "m_{h} (GeV)",
        'ytitle'            : "#mu (GeV)",
        
        'topRight'          : "ZH, #sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Internal}}",
    }

    plotter.cfg = cfg
    canvas = plotter.canvas()
    dummy = plotter.dummy()
    dummy.Draw("HIST")

    plt = MH.frame()
    spline_mean.plotOn(plt)    
    graph_mean.SetMarkerStyle(8)
    graph_mean.SetMarkerColor(ROOT.kBlack)
    graph_mean.SetMarkerSize(1.5)
    graph_mean.Draw("SAME P")
    
    plt.Draw("SAME")
    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/fit_mean.png" % (outDir))   
    canvas.SaveAs("%s/fit_mean.pdf" % (outDir))   
    
    ##################################
    # mean_gt
    ##################################
    graph_mean_gt = ROOT.TGraphErrors(len(param_mh), array.array('d', param_mh), array.array('d', param_mean_gt), array.array('d', [0]*len(param_mean_gt_err)), array.array('d', param_mean_gt_err))
    
    cfg = {

        'logy'              : False,
        'logx'              : False,
    
        'xmin'              : 124.8,
        'xmax'              : 125.2,
        'ymin'              : 0.999*min(param_mean_gt),
        'ymax'              : 1.001*max(param_mean_gt),
        
        'xtitle'            : "m_{h} (GeV)",
        'ytitle'            : "#mu_{gt} (GeV)",
        
        'topRight'          : "ZH, #sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Internal}}",
    }

    plotter.cfg = cfg
    canvas = plotter.canvas()
    dummy = plotter.dummy()
    dummy.Draw("HIST")

    plt = MH.frame()
    spline_mean_gt.plotOn(plt)    
    graph_mean_gt.SetMarkerStyle(8)
    graph_mean_gt.SetMarkerColor(ROOT.kBlack)
    graph_mean_gt.SetMarkerSize(1.5)
    graph_mean_gt.Draw("SAME P")
    
    plt.Draw("SAME")
    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/fit_mean_gt.png" % (outDir)) 
    canvas.SaveAs("%s/fit_mean_gt.pdf" % (outDir)) 
    
    
    ##################################
    # signal yield
    ##################################
    graph_yield = ROOT.TGraphErrors(len(param_mh), array.array('d', param_mh), array.array('d', param_yield), array.array('d', [0]*len(param_mean_err)), array.array('d', param_yield_err))
    
    cfg = {

        'logy'              : False,
        'logx'              : False,
    
        'xmin'              : 124.8,
        'xmax'              : 125.2,
        'ymin'              : 0.95*min(param_yield),
        'ymax'              : 1.05*max(param_yield),
        
        'xtitle'            : "m_{h} (GeV)",
        'ytitle'            : "Events",
        
        'topRight'          : "ZH, #sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Internal}}",
    }

    plotter.cfg = cfg
    canvas = plotter.canvas()
    dummy = plotter.dummy()
    dummy.Draw("HIST")

    plt = MH.frame()
    spline_yield.plotOn(plt)    
    graph_yield.SetMarkerStyle(8)
    graph_yield.SetMarkerColor(ROOT.kBlack)
    graph_yield.SetMarkerSize(1.5)
    graph_yield.Draw("SAME P")
    
    plt.Draw("SAME")
    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/fit_yield.png" % (outDir))     
    canvas.SaveAs("%s/fit_yield.pdf" % (outDir))     


    ##################################
    # sigma 
    ##################################
    graph_sigma = ROOT.TGraphErrors(len(param_mh), array.array('d', param_mh), array.array('d', param_sigma), array.array('d', [0]*len(param_sigma_err)), array.array('d', param_sigma_err))
    
    cfg = {

        'logy'              : False,
        'logx'              : False,
    
        'xmin'              : 124.8,
        'xmax'              : 125.2,
        'ymin'              : 0.95*min(param_sigma),
        'ymax'              : 1.05*max(param_sigma),
        
        'xtitle'            : "m_{h} (GeV)",
        'ytitle'            : "#sigma (GeV)",
        
        'topRight'          : "ZH, #sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Internal}}",
    }

    plotter.cfg = cfg
    canvas = plotter.canvas()
    dummy = plotter.dummy()
    dummy.Draw("HIST")

    plt = MH.frame()
    spline_sigma.plotOn(plt)    
    graph_sigma.SetMarkerStyle(8)
    graph_sigma.SetMarkerColor(ROOT.kBlack)
    graph_sigma.SetMarkerSize(1.5)
    graph_sigma.Draw("SAME P")
    
    plt.Draw("SAME")
    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/fit_sigma.png" % (outDir)) 
    canvas.SaveAs("%s/fit_sigma.pdf" % (outDir)) 

    ##################################
    # sigma_gt
    ##################################
    graph_sigma_gt = ROOT.TGraphErrors(len(param_mh), array.array('d', param_mh), array.array('d', param_sigma_gt), array.array('d', [0]*len(param_sigma_gt_err)), array.array('d', param_sigma_gt_err))
    
    cfg = {

        'logy'              : False,
        'logx'              : False,
    
        'xmin'              : 124.8,
        'xmax'              : 125.2,
        'ymin'              : 0.95*min(param_sigma_gt),
        'ymax'              : 1.05*max(param_sigma_gt),
        
        'xtitle'            : "m_{h} (GeV)",
        'ytitle'            : "#sigma_{gt} (GeV)",
        
        'topRight'          : "ZH, #sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Internal}}",
    }

    plotter.cfg = cfg
    canvas = plotter.canvas()
    dummy = plotter.dummy()
    dummy.Draw("HIST")

    plt = MH.frame()
    spline_sigma_gt.plotOn(plt)    
    graph_sigma_gt.SetMarkerStyle(8)
    graph_sigma_gt.SetMarkerColor(ROOT.kBlack)
    graph_sigma_gt.SetMarkerSize(1.5)
    graph_sigma_gt.Draw("SAME P")
    
    plt.Draw("SAME")
    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/fit_sigma_gt.png" % (outDir))     
    canvas.SaveAs("%s/fit_sigma_gt.pdf" % (outDir))    
    
    ##################################
    # alpha_1
    ##################################
    graph_alpha_1 = ROOT.TGraphErrors(len(param_mh), array.array('d', param_mh), array.array('d', param_alpha_1), array.array('d', [0]*len(param_alpha_1_err)), array.array('d', param_alpha_1_err))
    
    cfg = {

        'logy'              : False,
        'logx'              : False,
    
        'xmin'              : 124.8,
        'xmax'              : 125.2,
        'ymin'              : 0.8*min(param_alpha_1),
        'ymax'              : 1.2*max(param_alpha_1),
        
        'xtitle'            : "m_{h} (GeV)",
        'ytitle'            : "#alpha_{1}",
        
        'topRight'          : "ZH, #sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Internal}}",
    }

    plotter.cfg = cfg
    canvas = plotter.canvas()
    dummy = plotter.dummy()
    dummy.Draw("HIST")

    plt = MH.frame()
    spline_alpha_1.plotOn(plt)    
    graph_alpha_1.SetMarkerStyle(8)
    graph_alpha_1.SetMarkerColor(ROOT.kBlack)
    graph_alpha_1.SetMarkerSize(1.5)
    graph_alpha_1.Draw("SAME P")
    
    plt.Draw("SAME")
    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/fit_alpha_1.png" % (outDir)) 
    canvas.SaveAs("%s/fit_alpha_1.pdf" % (outDir)) 
    
    ##################################
    # alpha_2
    ##################################
    graph_alpha_2 = ROOT.TGraphErrors(len(param_mh), array.array('d', param_mh), array.array('d', param_alpha_2), array.array('d', [0]*len(param_alpha_2_err)), array.array('d', param_alpha_2_err))
    
    cfg = {

        'logy'              : False,
        'logx'              : False,
    
        'xmin'              : 124.8,
        'xmax'              : 125.2,
        'ymin'              : 0.8*min(param_alpha_2),
        'ymax'              : 1.2*max(param_alpha_2),
        
        'xtitle'            : "m_{h} (GeV)",
        'ytitle'            : "#alpha_{2}",
        
        'topRight'          : "ZH, #sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Internal}}",
    }

    plotter.cfg = cfg
    canvas = plotter.canvas()
    dummy = plotter.dummy()
    dummy.Draw("HIST")

    plt = MH.frame()
    spline_alpha_2.plotOn(plt)    
    graph_alpha_2.SetMarkerStyle(8)
    graph_alpha_2.SetMarkerColor(ROOT.kBlack)
    graph_alpha_2.SetMarkerSize(1.5)
    graph_alpha_2.Draw("SAME P")
    
    plt.Draw("SAME")
    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/fit_alpha_2.png" % (outDir)) 
    canvas.SaveAs("%s/fit_alpha_2.pdf" % (outDir)) 
    
    
    ##################################
    # n_1
    ##################################
    graph_n_1 = ROOT.TGraphErrors(len(param_mh), array.array('d', param_mh), array.array('d', param_n_1), array.array('d', [0]*len(param_n_1_err)), array.array('d', param_n_1_err))
    
    cfg = {

        'logy'              : False,
        'logx'              : False,
    
        'xmin'              : 124.8,
        'xmax'              : 125.2,
        'ymin'              : 0.8*min(param_n_1),
        'ymax'              : 1.2*max(param_n_1),
        
        'xtitle'            : "m_{h} (GeV)",
        'ytitle'            : "n_{1}",
        
        'topRight'          : "ZH, #sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Internal}}",
    }

    plotter.cfg = cfg
    canvas = plotter.canvas()
    dummy = plotter.dummy()
    dummy.Draw("HIST")

    plt = MH.frame()
    spline_n_1.plotOn(plt)    
    graph_n_1.SetMarkerStyle(8)
    graph_n_1.SetMarkerColor(ROOT.kBlack)
    graph_n_1.SetMarkerSize(1.5)
    graph_n_1.Draw("SAME P")
    
    plt.Draw("SAME")
    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/fit_n_1.png" % (outDir)) 
    canvas.SaveAs("%s/fit_n_1.pdf" % (outDir)) 
    
    ##################################
    # n_2
    ##################################
    graph_n_2 = ROOT.TGraphErrors(len(param_mh), array.array('d', param_mh), array.array('d', param_n_2), array.array('d', [0]*len(param_n_2_err)), array.array('d', param_n_2_err))
    
    cfg = {

        'logy'              : False,
        'logx'              : False,
    
        'xmin'              : 124.8,
        'xmax'              : 125.2,
        'ymin'              : 0.8*min(param_n_2),
        'ymax'              : 1.2*max(param_n_2),
        
        'xtitle'            : "m_{h} (GeV)",
        'ytitle'            : "n_{2}",
        
        'topRight'          : "ZH, #sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Internal}}",
    }

    plotter.cfg = cfg
    canvas = plotter.canvas()
    dummy = plotter.dummy()
    dummy.Draw("HIST")

    plt = MH.frame()
    spline_n_2.plotOn(plt)    
    graph_n_2.SetMarkerStyle(8)
    graph_n_2.SetMarkerColor(ROOT.kBlack)
    graph_n_2.SetMarkerSize(1.5)
    graph_n_2.Draw("SAME P")
    
    plt.Draw("SAME")
    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/fit_n_2.png" % (outDir)) 
    canvas.SaveAs("%s/fit_n_2.pdf" % (outDir)) 
    
    ##################################
    # cb_1
    ##################################
    graph_cb_1 = ROOT.TGraphErrors(len(param_mh), array.array('d', param_mh), array.array('d', param_cb_1), array.array('d', [0]*len(param_cb_1_err)), array.array('d', param_cb_1_err))
    
    cfg = {

        'logy'              : False,
        'logx'              : False,
    
        'xmin'              : 124.8,
        'xmax'              : 125.2,
        'ymin'              : 0.8*min(param_cb_1),
        'ymax'              : 1.2*max(param_cb_1),
        
        'xtitle'            : "m_{h} (GeV)",
        'ytitle'            : "cb_{1}",
        
        'topRight'          : "ZH, #sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Internal}}",
    }

    plotter.cfg = cfg
    canvas = plotter.canvas()
    dummy = plotter.dummy()
    dummy.Draw("HIST")

    plt = MH.frame()
    spline_cb_1.plotOn(plt)    
    graph_cb_1.SetMarkerStyle(8)
    graph_cb_1.SetMarkerColor(ROOT.kBlack)
    graph_cb_1.SetMarkerSize(1.5)
    graph_cb_1.Draw("SAME P")
    
    plt.Draw("SAME")
    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/fit_cb_1.png" % (outDir)) 
    canvas.SaveAs("%s/fit_cb_1.pdf" % (outDir)) 
    
    ##################################
    # cb_2
    ##################################
    graph_cb_2 = ROOT.TGraphErrors(len(param_mh), array.array('d', param_mh), array.array('d', param_cb_2), array.array('d', [0]*len(param_cb_2_err)), array.array('d', param_cb_2_err))
    
    cfg = {

        'logy'              : False,
        'logx'              : False,
    
        'xmin'              : 124.8,
        'xmax'              : 125.2,
        'ymin'              : 0.8*min(param_cb_2),
        'ymax'              : 1.2*max(param_cb_2),
        
        'xtitle'            : "m_{h} (GeV)",
        'ytitle'            : "cb_{2}",
        
        'topRight'          : "ZH, #sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Internal}}",
    }

    plotter.cfg = cfg
    canvas = plotter.canvas()
    dummy = plotter.dummy()
    dummy.Draw("HIST")

    plt = MH.frame()
    spline_cb_2.plotOn(plt)    
    graph_cb_2.SetMarkerStyle(8)
    graph_cb_2.SetMarkerColor(ROOT.kBlack)
    graph_cb_2.SetMarkerSize(1.5)
    graph_cb_2.Draw("SAME P")
    
    plt.Draw("SAME")
    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/fit_cb_2.png" % (outDir)) 
    canvas.SaveAs("%s/fit_cb_2.pdf" % (outDir)) 
    
    
    
    ##################################
    getattr(w_tmp, 'import')(spline_mean)
    getattr(w_tmp, 'import')(spline_sigma)
    getattr(w_tmp, 'import')(spline_yield)
    getattr(w_tmp, 'import')(spline_alpha_1)
    getattr(w_tmp, 'import')(spline_alpha_2)
    getattr(w_tmp, 'import')(spline_n_1)
    getattr(w_tmp, 'import')(spline_n_2)
    getattr(w_tmp, 'import')(spline_cb_1)
    getattr(w_tmp, 'import')(spline_cb_2)
    getattr(w_tmp, 'import')(spline_mean_gt)
    getattr(w_tmp, 'import')(spline_sigma_gt)

    return param_mh, param_yield


def doBackgrounds():

    global h_obs

    recoilmass = w_tmp.var("zed_leptonic_recoil_m")
    hist_bkg = None
    
    procs = ["p8_ee_WW_mumu_ecm240", "p8_ee_ZZ_ecm240", "wzp6_egamma_eZ_Zmumu_ecm240", "wzp6_gammae_eZ_Zmumu_ecm240", "wzp6_gaga_mumu_60_ecm240", "wzp6_gaga_tautau_60_ecm240", "p8_ee_Zll_ecm240"]
    

    

    for proc in procs:
    
        fIn = ROOT.TFile("%s/%s_hists.root" % (histDir, proc))
        hist = copy.deepcopy(fIn.Get("zed_leptonic_recoil_m_%s" % sel))
        hist.Scale(lumi*ds.datasets[proc]['xsec']*1e6/ds.datasets[proc]['nevents'])
        hist = hist.Rebin(rebin)
        rdh = ROOT.RooDataHist("rdh_%s" % proc, "rdh", ROOT.RooArgList(recoilmass), ROOT.RooFit.Import(hist))
        fIn.Close()
        
        # add to total background
        if hist_bkg == None: hist_bkg = hist
        else: hist_bkg.Add(hist)
        
        # add to observed 
        if h_obs == None: h_obs = hist.Clone("h_obs")
        else: h_obs.Add(hist)


    hist_bkg.SetName("total_bkg")
    rdh_bkg = ROOT.RooDataHist("rdh_bkg", "rdh_bkg", ROOT.RooArgList(recoilmass), ROOT.RooFit.Import(hist_bkg))
    yield_bkg_ = rdh_bkg.sum(False) 


    # construct background as 4th order Bernstein polynomial
    b0 = ROOT.RooRealVar("bern0", "bern_coeff", 1, -2, 2)
    b1 = ROOT.RooRealVar("bern1", "bern_coeff", 0.001, -10, 10)
    b2 = ROOT.RooRealVar("bern2", "bern_coeff", 0.001, -10, 10)
    b3 = ROOT.RooRealVar("bern3", "bern_coeff", 0.001, -10, 10)
    bkg = ROOT.RooBernsteinFast(3)("bkg", "bkg", recoilmass, ROOT.RooArgList(b0, b1, b2))

    bkg_norm = ROOT.RooRealVar('bkg_norm', 'bkg_norm', yield_bkg_, 0, 1e6)
    bkg_fit = ROOT.RooAddPdf('bkg_fit', '', ROOT.RooArgList(bkg), ROOT.RooArgList(bkg_norm))
    bkg_fit.fitTo(rdh_bkg, ROOT.RooFit.Extended(ROOT.kTRUE), ROOT.RooFit.SumW2Error(sumw2err))   


    ########### PLOTTING ###########
    cfg = {

        'logy'              : False,
        'logx'              : False,
    
        'xmin'              : 120,
        'xmax'              : 140,
        'ymin'              : 0,
        'ymax'              : 500,
        
        'xtitle'            : "Recoil mass (GeV)",
        'ytitle'            : "Events / 0.1 GeV",
        
        'topRight'          : "BKGS, #sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Internal}}",
        
        'ratiofraction'     : 0.25,
        'ytitleR'           : "Pull",
        'yminR'             : -6,
        'ymaxR'             : 6,
    }
    
    plotter.cfg = cfg
    
    canvas, padT, padB = plotter.canvasRatio()
    dummyT, dummyB = plotter.dummyRatio()
    
    ## TOP PAD ##
    canvas.cd()
    padT.Draw()
    padT.cd()
    dummyT.Draw("HIST")
    
    plt = recoilmass.frame()
    rdh_bkg.plotOn(plt, ROOT.RooFit.Binning(200))
    
    bkg_fit.plotOn(plt, ROOT.RooFit.LineColor(ROOT.kRed))
    bkg_fit.paramOn(plt, ROOT.RooFit.Format("NELU", ROOT.RooFit.AutoPrecision(2)), ROOT.RooFit.Layout(0.5, 0.9, 0.9))
    
    histpull = plt.pullHist()
    plt.Draw("SAME")
    
    plotter.auxRatio()
    
    ## BOTTOM PAD ##
    canvas.cd()
    padB.Draw()
    padB.cd()
    dummyB.Draw("HIST")
    

    plt = recoilmass.frame()
    plt.addPlotable(histpull, "P")
    plt.Draw("SAME")
    
    line = ROOT.TLine(120, 0, 140, 0)
    line.SetLineColor(ROOT.kBlue+2)
    line.SetLineWidth(2)
    line.Draw("SAME")
    
  
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/fit_bkg.png" % (outDir))  
    canvas.SaveAs("%s/fit_bkg.pdf" % (outDir))  
    
    # import background parameterization to the workspace
    bkg_norm.setVal(yield_bkg_) # not constant, as
    b0.setConstant(True) # set as constant
    b1.setConstant(True) # set as constant
    b2.setConstant(True) # set as constant
    b3.setConstant(True) # set as constant
    getattr(w_tmp, 'import')(bkg)
    getattr(w_tmp, 'import')(bkg_norm)
    
    
    return bkg_norm.getVal()
 
 
def doMC():


    ## only consider variation for 125 GeV
    ## assume variations to be indentical for other mass points
    proc = "wzp6_ee_mumuH_ecm240"
    mH = 125.0
    mH_ = ("%.2f" % mH).replace(".", "p")

    recoilmass = w_tmp.var("zed_leptonic_recoil_m")
    MH = w_tmp.var("MH")

    param_mean, param_mean_delta, param_sigma, param_alpha_1, param_alpha_2, param_n_1, param_n_2 = [], [], [], [], [], [], []
    param_yield, param_mean_err, param_sigma_err, param_alpha_1_err, param_alpha_2_err, param_n_1_err, param_n_2_err = [], [], [], [], [], [], []

    
    # recoil mass plot settings
    cfg = {

        'logy'              : False,
        'logx'              : False,
    
        'xmin'              : 120,
        'xmax'              : 140,
        'ymin'              : 0,
        'ymax'              : 1500,
        
        'xtitle'            : "MC Recoil mass (GeV)",
        'ytitle'            : "Events / 0.2 GeV",
        
        'topRight'          : "ZH, #sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Internal}}",
        
        'ratiofraction'     : 0.25,
        'ytitleR'           : "Pull",
        'yminR'             : -6,
        'ymaxR'             : 6,
    }
    
    
    ## for MUSCALE, consider only variations in norm, CB mean and CB sigma
    ## assume others to be identical to nominal sample
    MH.setVal(125.0) # evaluate all at 125 GeV
    spline_alpha_1 = w_tmp.obj("spline_alpha_1")
    spline_alpha_2 = w_tmp.obj("spline_alpha_2")
    spline_n_1 = w_tmp.obj("spline_n_1")
    spline_n_2 = w_tmp.obj("spline_n_2")
    spline_cb_1 = w_tmp.obj("spline_cb_1")
    spline_cb_2 = w_tmp.obj("spline_cb_2")
    spline_mean_gt = w_tmp.obj("spline_mean_gt")
    spline_sigma_gt = w_tmp.obj("spline_sigma_gt")

    #sel_tmp = sel
    sel = 'sel6'

    fIn = ROOT.TFile("%s/%s_hists.root" % (histDir, proc))
    hist_zh = copy.deepcopy(fIn.Get("zed_leptonic_recoil_m_MC_%s" % sel))
    hist_zh.Scale(lumi*ds.datasets[proc]['xsec']*1e6/ds.datasets[proc]['nevents'])
    hist_zh.SetName("hist_zh_%s_MC" % mH_)
    hist_zh = hist_zh.Rebin(rebin)
    rdh_zh = ROOT.RooDataHist("rdh_zh_%s_MC" % mH_, "rdh_zh", ROOT.RooArgList(recoilmass), ROOT.RooFit.Import(hist_zh))
    yield_zh = rdh_zh.sum(False)
    
    
    mean = ROOT.RooRealVar("mean_%s_MC" % mH_, '', 1.25086e+02, mH-1., mH+1.)
    sigma = ROOT.RooRealVar("sigma_%s_MC" % mH_, '', 4.10819e-01, 0, 1)
    alpha_1 = ROOT.RooRealVar("alpha_1_%s_MC" % mH_, '', spline_alpha_1.getVal(),-10,0)
    alpha_2 = ROOT.RooRealVar("alpha_2_%s_MC" % mH_, '', spline_alpha_2.getVal(),0,10)
    n_1 = ROOT.RooRealVar("n_1_%s_MC" % mH_, '', spline_n_1.getVal())
    n_2 = ROOT.RooRealVar("n_2_%s_MC" % mH_, '', spline_n_2.getVal())
    mean_gt = ROOT.RooRealVar("mean_gt_%s_MC" % mH_, '', spline_mean_gt.getVal(),spline_mean_gt.getVal()-1,spline_mean_gt.getVal()+1)
    sigma_gt = ROOT.RooRealVar("sigma_gt_%s_MC" % mH_, '', spline_sigma_gt.getVal(), spline_sigma_gt.getVal()-1, spline_sigma_gt.getVal()+1)   
        
    cbs_1 = ROOT.RooCBShape("CrystallBall_1_%s_MC" % mH_, "CrystallBall_1", recoilmass, mean, sigma, alpha_1, n_1)
    cbs_2 = ROOT.RooCBShape("CrystallBall_2_%s_MC" % mH_, "CrystallBall_2", recoilmass, mean, sigma, alpha_2, n_2)
    gauss = ROOT.RooGaussian("gauss_%s_MC" % mH_, "gauss", recoilmass, mean_gt, sigma_gt)
    cb_1 = ROOT.RooRealVar("cb_1_%s_MC" % mH_, '', spline_cb_1.getVal())
    cb_2 = ROOT.RooRealVar("cb_2_%s_MC" % mH_, '', spline_cb_2.getVal())
            
    sig = ROOT.RooAddPdf("sig_%s_MC" % mH_, '', ROOT.RooArgList(cbs_1, cbs_2, gauss), ROOT.RooArgList(cb_1, cb_2)) # half of both CB functions
    sig_norm = ROOT.RooRealVar("sig_%s_norm_MC" % mH_, '', yield_zh, 0, 1e6) # fix normalization
    sig_fit = ROOT.RooAddPdf("zh_model_%s_MC" % mH_, '', ROOT.RooArgList(sig), ROOT.RooArgList(sig_norm))
    sig_fit.fitTo(rdh_zh, ROOT.RooFit.Extended(ROOT.kTRUE), ROOT.RooFit.SumW2Error(sumw2err))
        
        
        
    mean__=mean.getVal()
    sigma__=sigma.getVal()
    norm__=sig_norm.getVal()
       
    ## IDEA
    #mean = ROOT.RooRealVar("mean_%s" % mH_, '', 1.25086e+02, mH-1., mH+1.)
    ##sigma = ROOT.RooRealVar("sigma_%s" % mH_, '', 4.10819e-01, 0, 1)
    #sigma = ROOT.RooRealVar("sigma_%s" % mH_, '', 4.1e-01) # fixed
    #alpha_1 = ROOT.RooRealVar("alpha_1_%s" % mH_, '', -1.39903e-01, -10, 0)
    ##alpha_1 = ROOT.RooRealVar("alpha_1_%s" % mH_, '', -0.14322)
    ##alpha_2 = ROOT.RooRealVar("alpha_2_%s" % mH_, '', 3.65257e+00, 0, 10)
    #alpha_2 = ROOT.RooRealVar("alpha_2_%s" % mH_, '', 3.60)
    ##n_1 = ROOT.RooRealVar("n_1_%s" % mH_, '', 2.35540e+00, -10, 10)
    #n_1 = ROOT.RooRealVar("n_1_%s" % mH_, '', 3.90)
    ##n_2 = ROOT.RooRealVar("n_2_%s" % mH_, '', 4.51050e-01, -10, 10)
    #n_2 = ROOT.RooRealVar("n_2_%s" % mH_, '', 0.6)

    #mean_gt = ROOT.RooRealVar("mean_gt_%s" % mH_, '', 1.25442e+02, recoilMin, recoilMax)
    ##sigma_gt = ROOT.RooRealVar("sigma_gt_%s" % mH_, '', 8.47732e-01, 0, 1)
    #sigma_gt = ROOT.RooRealVar("sigma_gt_%s" % mH_, '', 0.842) # fixed  
        



    
    
    # do plotting
    plotter.cfg = cfg
        
    canvas, padT, padB = plotter.canvasRatio()
    dummyT, dummyB = plotter.dummyRatio()
        
    ## TOP PAD ##
    canvas.cd()
    padT.Draw()
    padT.cd()
    dummyT.Draw("HIST")
        
    plt = recoilmass.frame()
    plt.SetTitle("ZH signal")
    rdh_zh.plotOn(plt, ROOT.RooFit.Binning(200))
        
    sig_fit.plotOn(plt, ROOT.RooFit.LineColor(ROOT.kRed))
    sig_fit.paramOn(plt, ROOT.RooFit.Format("NELU", ROOT.RooFit.AutoPrecision(2)), ROOT.RooFit.Layout(0.4, 0.9, 0.9))
        
    histpull = plt.pullHist()
    plt.Draw("SAME")
        
    plotter.auxRatio()
        
    ## BOTTOM PAD ##
    canvas.cd()
    padB.Draw()
    padB.cd()
    dummyB.Draw("HIST")
        

    plt = recoilmass.frame()
    plt.addPlotable(histpull, "P")
    plt.Draw("SAME")
        
    line = ROOT.TLine(120, 0, 140, 0)
    line.SetLineColor(ROOT.kBlue+2)
    line.SetLineWidth(2)
    line.Draw("SAME")
        
      
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/fit_mH%s_MC.png" % (outDir, mH_))
    canvas.SaveAs("%s/fit_mH%s_MC.pdf" % (outDir, mH_))
        
    del dummyB
    del dummyT
    del padT
    del padB
    del canvas
        
        
    # import
    getattr(w_tmp, 'import')(rdh_zh)
    getattr(w_tmp, 'import')(sig_fit)
    #getattr(w_tmp, 'import')(sig_norm) # already imported with sig_fit
            

    
    '''
    mean__nominal = w_tmp.obj("spline_mean").getVal()
    sigma__nominal = w_tmp.obj("spline_sigma").getVal()
    norm__nominal = w_tmp.obj("spline_yield").getVal()
    #alpha_1__nominal = w_tmp.obj("spline_alpha_1").getVal()
    #alpha_2__nominal = w_tmp.obj("spline_alpha_2").getVal()
    #n_1__nominal = w_tmp.obj("spline_n_1").getVal()
    #n_2__nominal = w_tmp.obj("spline_n_2").getVal()
    #mean_gt__nominal = w_tmp.obj("spline_mean_gt").getVal()
    #sigma_gt__nominal = w_tmp.obj("spline_sigma_gt").getVal()
    #cb_1__nominal = w_tmp.obj("spline_cb_1").getVal()
    #cb_2__nominal = w_tmp.obj("spline_cb_2").getVal()
   
    
    
    sig_mean_MC = ROOT.RooRealVar('sig_mean_MC', 'sig_mean_MC', abs(mean__nominal-mean.getVal())/mean__nominal)
    sig_sigma_MC = ROOT.RooRealVar('sig_sigma_MC', 'sig_sigma_MC', abs(sigma__nominal-sigma.getVal())/sigma__nominal)
    sig_norm_MC = ROOT.RooRealVar('sig_norm_MC', 'sig_norm_MC', abs(norm__nominal-sig_norm.getVal())/norm__nominal)
    #sig_alpha_1_MC = ROOT.RooRealVar('sig_alpha_1_MC', 'sig_alpha_1_MC', abs(alpha_1__nominal-alpha_1.getVal())/alpha_1__nominal)
    #sig_alpha_2_MC = ROOT.RooRealVar('sig_alpha_2_MC', 'sig_alpha_2_MC', abs(alpha_2__nominal-alpha_2.getVal())/alpha_2__nominal)
    #sig_n_1_MC = ROOT.RooRealVar('sig_n_1_MC', 'sig_n_1_MC', abs(n_1__nominal-n_1.getVal())/n_1__nominal)
    #sig_n_2_MC = ROOT.RooRealVar('sig_n_2_MC', 'sig_n_2_MC', abs(n_2__nominal-n_2.getVal())/n_2__nominal)
    #sig_mean_gt_MC = ROOT.RooRealVar('sig_mean_gt_MC', 'sig_mean_gt_MC', abs(mean_gt__nominal-mean_gt.getVal())/mean_gt__nominal)
    #sig_sigma_gt_MC = ROOT.RooRealVar('sig_sigma_gt_MC', 'sig_sigma_gt_MC', abs(sigma_gt__nominal-sigma_gt.getVal())/sigma_gt__nominal)
    #sig_cb_1_MC = ROOT.RooRealVar('sig_cb_1_MC', 'sig_norm_MC', abs(cb_1__nominal-cb_1.getVal())/cb_1__nominal)
    #sig_cb_2_MC = ROOT.RooRealVar('sig_cb_2_MC', 'sig_norm_MC', abs(cb_2__nominal-cb_1.getVal())/cb_2__nominal)

    getattr(w_tmp, 'import')(sig_mean_MC)
    getattr(w_tmp, 'import')(sig_sigma_MC)
    getattr(w_tmp, 'import')(sig_norm_MC)
    #getattr(w_tmp, 'import')(sig_alpha_1_MC)
    #getattr(w_tmp, 'import')(sig_alpha_2_MC)
    #getattr(w_tmp, 'import')(sig_n_1_MC)
    #getattr(w_tmp, 'import')(sig_n_2_MC)
    #getattr(w_tmp, 'import')(sig_mean_gt_MC)
    #getattr(w_tmp, 'import')(sig_sigma_gt_MC)
    #getattr(w_tmp, 'import')(sig_cb_1_MC)
    #getattr(w_tmp, 'import')(sig_cb_2_MC)

    #sel = sel_tmp
    '''

def doISR():

    recoilmass = w_tmp.var("zed_leptonic_recoil_m")
    MH = w_tmp.var("MH")
    
    param_yield, param_mh, param_mean, param_mean_gt, param_sigma, param_sigma_gt, param_alpha_1, param_alpha_2, param_n_1, param_n_2, param_cb_1, param_cb_2 = [], [], [], [], [], [], [], [], [], [], [], []
    param_yield_err, param_mean_err, param_sigma_err, param_mean_gt_err, param_sigma_gt_err, param_alpha_1_err, param_alpha_2_err, param_n_1_err, param_n_2_err, param_cb_1_err, param_cb_2_err  = [], [], [], [], [], [], [], [], [], [], []

    # recoil mass plot settings
    cfg = {

        'logy'              : False,
        'logx'              : False,
    
        'xmin'              : 120,
        'xmax'              : 140,
        'ymin'              : 0,
        'ymax'              : 1500,
        
        'xtitle'            : "Recoil mass (GeV)",
        'ytitle'            : "Events / 0.2 GeV",
        
        'topRight'          : "ZH, #sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Internal}}",
        
        'ratiofraction'     : 0.25,
        'ytitleR'           : "Pull",
        'yminR'             : -6,
        'ymaxR'             : 6,
    }
    
    
   

    mH = 125.0
    mH_ = ("%.2f" % mH).replace(".", "p")
    
    ## for ISR, consider only variations in norm, mean and sigma, n1, n2, mean_gt and sigma_gt (so also tails)
    ## assume others to be identical to nominal sample
    MH.setVal(125.0) # evaluate all at 125 GeV
    spline_alpha_1 = w_tmp.obj("spline_alpha_1")
    spline_alpha_2 = w_tmp.obj("spline_alpha_2")
    spline_cb_1 = w_tmp.obj("spline_cb_1")
    spline_cb_2 = w_tmp.obj("spline_cb_2")
    spline_sigma_gt = w_tmp.obj("spline_sigma_gt")
    
    
    #proc = "wzp6_ee_mumuH_ISRnoRecoil_ecm240"
    proc = "wzp6_ee_mumuH_ecm240_reweighted"
    fIn = ROOT.TFile("%s/%s_hists.root" % (histDir, proc))
    hist_zh = copy.deepcopy(fIn.Get("zed_leptonic_recoil_m_%s" % sel))
    hist_zh.Scale(lumi*ds.datasets[proc]['xsec']*1e6/ds.datasets[proc]['nevents'])
    hist_zh.SetName("hist_zh_%s_ISR" % mH_)
    hist_zh = hist_zh.Rebin(rebin)
    rdh_zh = ROOT.RooDataHist("rdh_zh_%s_ISR" % (mH_), "rdh_zh", ROOT.RooArgList(recoilmass), ROOT.RooFit.Import(hist_zh))
    yield_zh = rdh_zh.sum(False)



    # fixed values taken from 125 GeV fit  
    mean = ROOT.RooRealVar("mean_%s_ISR" % (mH_), '', 1.25086e+02, mH-1., mH+1.)
    sigma = ROOT.RooRealVar("sigma_%s_ISR" % (mH_), '', 4.10819e-01, 0, 1)
    alpha_1 = ROOT.RooRealVar("alpha_1_%s_ISR" % (mH_), '', spline_alpha_1.getVal())
    alpha_2 = ROOT.RooRealVar("alpha_2_%s_ISR" % (mH_), '', spline_alpha_2.getVal())
    n_1 = ROOT.RooRealVar("n_1_%s_ISR" % (mH_), '', 2.35540e+00, -10, 10) # better to float for ISR tails
    n_2 = ROOT.RooRealVar("n_2_%s_ISR" % (mH_), '', 4.51050e-01, -10, 10) # better to float for ISR tails
    mean_gt = ROOT.RooRealVar("mean_gt_%s_ISR" % (mH_), '', 1.25442e+02, recoilMin, recoilMax)
    sigma_gt = ROOT.RooRealVar("sigma_gt_%s_ISR" % (mH_), '', spline_sigma_gt.getVal()) # fixed            
            
    cbs_1 = ROOT.RooCBShape("CrystallBall_1_%s_ISR" % (mH_), "CrystallBall_1", recoilmass, mean, sigma, alpha_1, n_1)
    cbs_2 = ROOT.RooCBShape("CrystallBall_2_%s_ISR" % (mH_), "CrystallBall_2", recoilmass, mean, sigma, alpha_2, n_2)
    gauss = ROOT.RooGaussian("gauss_%s_ISR" % (mH_), "gauss", recoilmass, mean_gt, sigma_gt)
    cb_1 = ROOT.RooRealVar("cb_1_%s_ISR" % (mH_), '', spline_cb_1.getVal()) # 
    cb_2 = ROOT.RooRealVar("cb_2_%s_ISR" % (mH_), '', spline_cb_2.getVal()) # 

                
    sig = ROOT.RooAddPdf("sig_%s_ISR" % (mH_), '', ROOT.RooArgList(cbs_1, cbs_2, gauss), ROOT.RooArgList(cb_1, cb_2)) # half of both CB functions
    sig_norm = ROOT.RooRealVar("sig_%s_ISR_norm" % (mH_), '', yield_zh, 0, 1e6) # fix normalization
    sig_fit = ROOT.RooAddPdf("zh_model_%s_ISR" % (mH_), '', ROOT.RooArgList(sig), ROOT.RooArgList(sig_norm))
    sig_fit.fitTo(rdh_zh, ROOT.RooFit.Extended(ROOT.kTRUE), ROOT.RooFit.SumW2Error(sumw2err))
        
    getattr(w_tmp, 'import')(rdh_zh)
    getattr(w_tmp, 'import')(sig_fit)        
    
    # do plotting
    plotter.cfg = cfg
            
    canvas, padT, padB = plotter.canvasRatio()
    dummyT, dummyB = plotter.dummyRatio()
            
    ## TOP PAD ##
    canvas.cd()
    padT.Draw()
    padT.cd()
    dummyT.Draw("HIST")
            
    plt = recoilmass.frame()
    plt.SetTitle("ZH signal")
    rdh_zh.plotOn(plt, ROOT.RooFit.Binning(200))
            
    sig_fit.plotOn(plt, ROOT.RooFit.LineColor(ROOT.kRed))
    sig_fit.paramOn(plt, ROOT.RooFit.Format("NELU", ROOT.RooFit.AutoPrecision(2)), ROOT.RooFit.Layout(0.45, 0.9, 0.9))
            
    histpull = plt.pullHist()
    plt.Draw("SAME")
            
    plotter.auxRatio()
            
    ## BOTTOM PAD ##
    canvas.cd()
    padB.Draw()
    padB.cd()
    dummyB.Draw("HIST")
            

    plt = recoilmass.frame()
    plt.addPlotable(histpull, "P")
    plt.Draw("SAME")
            
    line = ROOT.TLine(120, 0, 140, 0)
    line.SetLineColor(ROOT.kBlue+2)
    line.SetLineWidth(2)
    line.Draw("SAME")
            
          
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/fit_mH%s_ISR.png" % (outDir, mH_))
    canvas.SaveAs("%s/fit_mH%s_ISR.pdf" % (outDir, mH_))
            
    del dummyB
    del dummyT
    del padT
    del padB
    del canvas
            
            
            
    # plot with nominal
    cfg['ymax'] = 2500
    cfg['xmin'] = 124
    cfg['xmax'] = 127
    plotter.cfg = cfg
        
        
    canvas = plotter.canvas()
    dummy = plotter.dummy()
        
    dummy.Draw("HIST")

    plt = w_tmp.var("zed_leptonic_recoil_m").frame()
    colors = [ROOT.kRed, ROOT.kBlack, ROOT.kBlue]
        

    sig_fit = w_tmp.pdf("zh_model_%s_ISR" % mH_)  # "sig_%s_BES%s_norm" % (mH_, s)
    sig_fit.plotOn(plt, ROOT.RooFit.LineColor(colors[0]), ROOT.RooFit.Normalization(w_tmp.var("sig_%s_ISR_norm" % mH_).getVal(), ROOT.RooAbsReal.NumEvent))
            
    sig_fit = w_tmp.pdf("zh_model_%s" % mH_)
    sig_fit.plotOn(plt, ROOT.RooFit.LineColor(colors[1]), ROOT.RooFit.Normalization(w_tmp.var("sig_%s_norm" % mH_).getVal(), ROOT.RooAbsReal.NumEvent))
        
        
    plt.Draw("SAME")
    
    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/fit_mH%s_ISR_c.png" % (outDir, mH_))
    canvas.SaveAs("%s/fit_mH%s_ISR_c.pdf" % (outDir, mH_))

    cfg['ymax'] = 1500
    cfg['xmin'] = 120
    cfg['xmax'] = 140
            

            
        

    MH.setVal(125.0) # evaluate all at 125 GeV
    mean__nominal = w_tmp.obj("spline_mean").getVal()
    sigma__nominal = w_tmp.obj("spline_sigma").getVal()
    norm__nominal = w_tmp.obj("spline_yield").getVal()
    #alpha_1__nominal = w_tmp.obj("spline_alpha_1").getVal()
    #alpha_2__nominal = w_tmp.obj("spline_alpha_2").getVal()
    n_1__nominal = w_tmp.obj("spline_n_1").getVal()
    n_2__nominal = w_tmp.obj("spline_n_2").getVal()
    mean_gt__nominal = w_tmp.obj("spline_mean_gt").getVal()
    #sigma_gt__nominal = w_tmp.obj("spline_sigma_gt").getVal()
    #cb_1__nominal = w_tmp.obj("spline_cb_1").getVal()
    #cb_2__nominal = w_tmp.obj("spline_cb_2").getVal()
   
    
    
    sig_mean_ISR = ROOT.RooRealVar('sig_mean_ISR', 'sig_mean_ISR', abs(mean__nominal-mean.getVal())/mean__nominal)
    sig_sigma_ISR = ROOT.RooRealVar('sig_sigma_ISR', 'sig_sigma_ISR', abs(sigma__nominal-sigma.getVal())/sigma__nominal)
    sig_norm_ISR = ROOT.RooRealVar('sig_norm_ISR', 'sig_norm_ISR', abs(norm__nominal-sig_norm.getVal())/norm__nominal)
    #sig_alpha_1_ISR = ROOT.RooRealVar('sig_alpha_1_ISR', 'sig_alpha_1_ISR', abs(alpha_1__nominal-alpha_1.getVal())/alpha_1__nominal)
    #sig_alpha_2_ISR = ROOT.RooRealVar('sig_alpha_2_ISR', 'sig_alpha_2_ISR', abs(alpha_2__nominal-alpha_2.getVal())/alpha_2__nominal)
    sig_n_1_ISR = ROOT.RooRealVar('sig_n_1_ISR', 'sig_n_1_ISR', abs(n_1__nominal-n_1.getVal())/n_1__nominal)
    sig_n_2_ISR = ROOT.RooRealVar('sig_n_2_ISR', 'sig_n_2_ISR', abs(n_2__nominal-n_2.getVal())/n_2__nominal)
    sig_mean_gt_ISR = ROOT.RooRealVar('sig_mean_gt_ISR', 'sig_mean_gt_ISR', abs(mean_gt__nominal-mean_gt.getVal())/mean_gt__nominal)
    #sig_sigma_gt_ISR = ROOT.RooRealVar('sig_sigma_gt_ISR', 'sig_sigma_gt_ISR', abs(sigma_gt__nominal-sigma_gt.getVal())/sigma_gt__nominal)
    #sig_cb_1_ISR = ROOT.RooRealVar('sig_cb_1_ISR', 'sig_norm_ISR', abs(cb_1__nominal-cb_1.getVal())/cb_1__nominal)
    #sig_cb_2_ISR = ROOT.RooRealVar('sig_cb_2_ISR', 'sig_norm_ISR', abs(cb_2__nominal-cb_1.getVal())/cb_2__nominal)

    getattr(w_tmp, 'import')(sig_mean_ISR)
    getattr(w_tmp, 'import')(sig_sigma_ISR)
    getattr(w_tmp, 'import')(sig_norm_ISR)
    #getattr(w_tmp, 'import')(sig_alpha_1_ISR)
    #getattr(w_tmp, 'import')(sig_alpha_2_ISR)
    getattr(w_tmp, 'import')(sig_n_1_ISR)
    getattr(w_tmp, 'import')(sig_n_2_ISR)
    getattr(w_tmp, 'import')(sig_mean_gt_ISR)
    #getattr(w_tmp, 'import')(sig_sigma_gt_ISR)
    #getattr(w_tmp, 'import')(sig_cb_1_ISR)
    #getattr(w_tmp, 'import')(sig_cb_2_ISR)

  


 
if __name__ == "__main__":

    lumi = 5.0 # integrated lumi in /ab
    histDir = "/eos/user/l/lia/FCCee/mumu_Combine/"
    outDir = "/eos/user/l/lia/FCCee/mumu_Combine/fitAnalysis_detector"
    runDir = "fitAnalysis/combine_detector"
    sel = "sel5" # selection identifier

    rebin = 1 # the recoil histograms are binned at 1 MeV
    lumi = 5.0
    recoilMin = 120
    recoilMax = 140
    h_obs = None # should hold the data_obs = sum of signal and backgrounds

    recoilmass = ROOT.RooRealVar("zed_leptonic_recoil_m", "Recoil mass (GeV)", 125, recoilMin, recoilMax)
    MH = ROOT.RooRealVar("MH", "Higgs mass (GeV)", 125, 124.9, 125.1) # name Higgs mass as MH to be compatible with combine
    
    
    # define temporary output workspace
    w_tmp = ROOT.RooWorkspace("w_tmp", "workspace")
    w = ROOT.RooWorkspace("w", "workspace") # final workspace for combine
 
    getattr(w_tmp, 'import')(recoilmass)
    getattr(w_tmp, 'import')(MH)
    
    
    doSignal()
    doMC()
    #doSignal3T()
    #doSignalFullSil()
    #doBackground()


    '''
    # build background model
    bkg_yield = w_tmp.obj("bkg_norm").getVal()
    #b0 = ROOT.RooRealVar("bern0", "bern_coeff", w_tmp.obj("bern0").getVal())
    #b1 = ROOT.RooRealVar("bern1", "bern_coeff", w_tmp.obj("bern1").getVal())
    #b2 = ROOT.RooRealVar("bern2", "bern_coeff", w_tmp.obj("bern2").getVal())
    #b3 = ROOT.RooRealVar("bern3", "bern_coeff", w_tmp.obj("bern3").getVal())
    #bkg = ROOT.RooBernsteinFast(1)("bkg", "bkg", recoilmass, ROOT.RooArgList(b0))
    #bkg = ROOT.RooBernsteinFast(3)("bkg", "bkg", recoilmass, ROOT.RooArgList(b0, b1, b2))
    bkg_norm = ROOT.RooRealVar('bkg_norm', 'bkg_norm', bkg_yield, 0, 1e6) # nominal background yield, floating
    bkg_norm.setVal(bkg_yield) # not constant!
    #b0.setConstant(True) # set as constant
    #b1.setConstant(True) # set as constant
    #b2.setConstant(True) # set as constant
    #b3.setConstant(True) # set as constant
    bkg = w_tmp.obj("bkg")
    getattr(w, 'import')(bkg)
    getattr(w, 'import')(bkg_norm)
    
    
    sig_mean_MUSCALE = w_tmp.obj("sig_mean_MUSCALE")
    sig_sigma_MUSCALE = w_tmp.obj("sig_sigma_MUSCALE")


    # build signal model, taking into account all uncertainties
    spline_mean = w_tmp.obj("spline_mean")
    spline_sigma = w_tmp.obj("spline_sigma")
    spline_yield = w_tmp.obj("spline_yield")
    spline_alpha_1 = w_tmp.obj("spline_alpha_1")
    spline_alpha_2 = w_tmp.obj("spline_alpha_2")
    spline_n_1 = w_tmp.obj("spline_n_1")
    spline_n_2 = w_tmp.obj("spline_n_2")
    spline_cb_1 = w_tmp.obj("spline_cb_1")
    spline_cb_2 = w_tmp.obj("spline_cb_2")
    spline_mean_gt = w_tmp.obj("spline_mean_gt")
    spline_sigma_gt = w_tmp.obj("spline_sigma_gt")
    
    list_mean = ROOT.RooArgList(spline_mean, BES, sig_mean_BES, ISR, sig_mean_ISR, SQRTS, sig_mean_SQRTS, MUSCALE, sig_mean_MUSCALE)
    list_mean.add(FSR)
    list_mean.add(sig_mean_FSR)
    list_sigma = ROOT.RooArgList(spline_sigma, BES, sig_sigma_BES, ISR, sig_sigma_ISR, SQRTS, sig_sigma_SQRTS, MUSCALE, sig_sigma_MUSCALE)
    list_sigma.add(FSR)
    list_sigma.add(sig_sigma_FSR)
    
    #sig_mean = ROOT.RooFormulaVar("sig_mean", "@0*(1+@1*@2)*(1+@3*@4)*(1+@5*@6)*(1+@7*@8)*(1+@9*@10)", ROOT.RooArgList(spline_mean, BES, sig_mean_BES, ISR, sig_mean_ISR, SQRTS, sig_mean_SQRTS, MUSCALE, sig_mean_MUSCALE, FSR, sig_mean_FSR))
    sig_mean = ROOT.RooFormulaVar("sig_mean", "@0*(1+@1*@2)*(1+@3*@4)*(1+@5*@6)*(1+@7*@8)*(1+@9*@10)",list_mean)
    #sig_sigma = ROOT.RooFormulaVar("sig_sigma", "@0*(1+@1*@2)*(1+@3*@4)*(1+@5*@6)*(1+@7*@8)*(1+@9*@10)", ROOT.RooArgList(spline_sigma, BES, sig_sigma_BES, ISR, sig_sigma_ISR, SQRTS, sig_sigma_SQRTS, MUSCALE, sig_sigma_MUSCALE, FSR, sig_sigma_FSR))
    sig_sigma = ROOT.RooFormulaVar("sig_sigma", "@0*(1+@1*@2)*(1+@3*@4)*(1+@5*@6)*(1+@7*@8)*(1+@9*@10)",list_sigma)
    #sig_alpha_1 = ROOT.RooFormulaVar("sig_alpha_1", "@0", ROOT.RooArgList(spline_alpha_1))
    sig_alpha_1 = ROOT.RooFormulaVar("sig_alpha_1", "@0*(1+@1*@2)", ROOT.RooArgList(spline_alpha_1, FSR, sig_alpha_1_FSR))
    sig_alpha_2 = ROOT.RooFormulaVar("sig_alpha_2", "@0", ROOT.RooArgList(spline_alpha_2))
    sig_n_1 = ROOT.RooFormulaVar("sig_n_1", "@0*(1+@1*@2)*(1+@3*@4)", ROOT.RooArgList(spline_n_1, ISR, sig_n_1_ISR, FSR, sig_n_1_FSR))
    sig_n_2 = ROOT.RooFormulaVar("sig_n_2", "@0*(1+@1*@2)*(1+@3*@4)", ROOT.RooArgList(spline_n_2, ISR, sig_n_2_ISR, FSR, sig_n_2_FSR))
    sig_cb_1 = ROOT.RooFormulaVar("sig_cb_1", "@0", ROOT.RooArgList(spline_cb_1))
    sig_cb_2 = ROOT.RooFormulaVar("sig_cb_2", "@0", ROOT.RooArgList(spline_cb_2))
    sig_mean_gt = ROOT.RooFormulaVar("sig_mean_gt", "@0*(1+@1*@2)*(1+@3*@4)", ROOT.RooArgList(spline_mean_gt, ISR, sig_mean_gt_ISR, FSR, sig_mean_gt_FSR))
    sig_sigma_gt = ROOT.RooFormulaVar("sig_sigma_gt", "@0", ROOT.RooArgList(spline_sigma_gt))
    sig_norm = ROOT.RooFormulaVar("sig_norm", "@0*(1+@1*@2)*(1+@3*@4)*(1+@5*@6)", ROOT.RooArgList(spline_yield, BES, sig_norm_BES, ISR, sig_norm_ISR, FSR, sig_norm_FSR))


    cbs_1 = ROOT.RooCBShape("CrystallBall_1", "CrystallBall_1", recoilmass, sig_mean, sig_sigma, sig_alpha_1, sig_n_1)
    cbs_2 = ROOT.RooCBShape("CrystallBall_2", "CrystallBall_2", recoilmass, sig_mean, sig_sigma, sig_alpha_2, sig_n_2)
    gauss = ROOT.RooGaussian("gauss", "gauss", recoilmass, sig_mean_gt, sig_sigma_gt)
    sig = ROOT.RooAddPdf("sig", "sig", ROOT.RooArgList(cbs_1, cbs_2, gauss), ROOT.RooArgList(sig_cb_1, sig_cb_2))
    '''
    
    
    #getattr(w, 'import')(sig_norm)
    #getattr(w, 'import')(sig)
    
   
    data_obs = ROOT.RooDataHist("data_obs", "data_obs", ROOT.RooArgList(recoilmass), ROOT.RooFit.Import(h_obs))
    getattr(w, 'import')(data_obs)
    
    w.writeToFile("%s/datacard.root" % runDir)
    w.Print()

    
    del w
    del w_tmp


    # build the Combine workspace based on the datacard, save it to ws.root
    #cmd = "text2workspace.py datacard.txt -o ws.root -v 10"
    #subprocess.call(cmd, shell=True, cwd=runDir)
