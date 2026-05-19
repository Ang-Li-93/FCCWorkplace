
import sys,copy,array,os,subprocess,math
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)

import plotter



def findCrossing(xv, yv, left=True, flip=125, cross=1.):

    closestPoint, idx = 1e9, -1
    for i in range(0, len(xv)):
    
        if left and xv[i] > flip: continue
        if not left and xv[i] < flip: continue
        
        dy = abs(yv[i]-cross)
        if dy < closestPoint: 
            closestPoint = dy
            idx = i
    # find correct indices around crossing
    if left: 
        if yv[idx] > cross: idx_ = idx+1
        else: idx_ = idx-1
    else:
        if yv[idx] > cross: idx_ = idx-1
        else: idx_ = idx+1
      
    # do interpolation  
    omega = (yv[idx]-yv[idx_])/(xv[idx]-xv[idx_])
    return (cross-yv[idx])/omega + xv[idx] 

def analyzeMass(runDir, outDir, xMin=-1, xMax=-1, yMin=0, yMax=2, label="label"):

    if not os.path.exists(outDir): os.makedirs(outDir)

    fIn = ROOT.TFile("%s/higgsCombinemass.MultiDimFit.mH125.root" % runDir, "READ")
    t = fIn.Get("limit")
    
    str_out = ""
    
    xv, yv = [], []
    for i in range(0, t.GetEntries()):

        t.GetEntry(i)
        
        if t.quantileExpected < -1.5: continue
        if t.deltaNLL > 1000: continue
        if t.deltaNLL > 20: continue
        xv.append(getattr(t, "MH"))
        yv.append(t.deltaNLL*2.)


 
    xv, yv = zip(*sorted(zip(xv, yv)))
    g = ROOT.TGraph(len(xv), array.array('d', xv), array.array('d', yv))
    
    # bestfit = minimum
    mass = 1e9
    for i in xrange(g.GetN()):
        if g.GetY()[i] == 0.: mass = g.GetX()[i]

    # extract uncertainties at crossing = 1
    unc_m = findCrossing(xv, yv, left=True, flip=mass)
    unc_p = findCrossing(xv, yv, left=False, flip=mass)
    unc = 0.5*(abs(mass-unc_m) + abs(unc_p-mass))
       
    ########### PLOTTING ###########
    cfg = {

        'logy'              : False,
        'logx'              : False,
        
        'xmin'              : min(xv) if xMin < 0 else xMin,
        'xmax'              : max(xv) if xMax < 0 else xMax,
        'ymin'              : yMin,
        'ymax'              : yMax , # max(yv)
            
        'xtitle'            : "m_{h} (GeV)",
        'ytitle'            : "-2#DeltaNLL",
            
        'topRight'          : "#sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCC-ee} #scale[0.7]{#it{Internal}}",
        }
        
    plotter.cfg = cfg
        
    canvas = plotter.canvas()
    canvas.SetGrid()
    dummy = plotter.dummy()
        
    dummy.GetXaxis().SetNdivisions(507)  
    dummy.Draw("HIST")
    
    g.SetMarkerStyle(20)
    g.SetMarkerColor(ROOT.kRed)
    g.SetMarkerSize(1)
    g.SetLineColor(ROOT.kRed)
    g.SetLineWidth(2)
    g.Draw("SAME LP")
    

    line = ROOT.TLine(float(cfg['xmin']), 1, float(cfg['xmax']), 1)
    line.SetLineColor(ROOT.kBlack)
    line.SetLineWidth(2)
    line.Draw("SAME")
    
    leg = ROOT.TLegend(.20, 0.825, 0.90, .9)
    leg.SetBorderSize(0)
    leg.SetTextSize(0.035)
    leg.SetMargin(0.15)
    leg.SetBorderSize(1)
    leg.AddEntry(g, "%s, #delta(m_{h}) = %.2f MeV" % (label, unc*1000.), "LP")
    leg.Draw()
        
    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/mass%s.png" % (outDir, suffix))
    canvas.SaveAs("%s/mass%s.pdf" % (outDir, suffix))
    
    
    # write values to text file
    str_out = "%f %f %f %f\n" % (unc_m, unc_p, unc, mass)
    for i in range(0, len(xv)): str_out += "%f %f\n" % (xv[i], yv[i])
    tFile = open("%s/mass%s.txt" % (outDir, suffix), "w")
    tFile.write(str_out)
    tFile.close()
    tFile = open("%s/mass%s.txt" % (runDir, suffix), "w")
    tFile.write(str_out)
    tFile.close()
        
def analyzeXsec(runDir, outDir, xMin=-1, xMax=-1, yMin=0, yMax=2, label="label"):

    fIn = ROOT.TFile("%s/higgsCombinexsec.MultiDimFit.mH125.root" % runDir, "READ")
    t = fIn.Get("limit")
    
    ref_xsec = 0.201868 # pb, for pythia
    ref_xsec = 0.0067656 # whizard, Z->mumu
    ref_xsec = 1

    xv, yv = [], []
    for i in range(0, t.GetEntries()):

        t.GetEntry(i)
        xv.append(getattr(t, "r")*ref_xsec)
        yv.append(t.deltaNLL*2.)

 
    xv, yv = zip(*sorted(zip(xv, yv)))        
    g = ROOT.TGraph(len(xv), array.array('d', xv), array.array('d', yv))
    
    # bestfit = minimum
    xsec = 1e9
    for i in xrange(g.GetN()):
        if g.GetY()[i] == 0.: xsec = g.GetX()[i]
    
    # extract uncertainties at crossing = 1
    unc_m = findCrossing(xv, yv, left=True, flip=ref_xsec)
    unc_p = findCrossing(xv, yv, left=False, flip=ref_xsec)
    unc = 0.5*(abs(xsec-unc_m) + abs(unc_p-xsec))

   
    ########### PLOTTING ###########
    cfg = {

        'logy'              : False,
        'logx'              : False,
        
        'xmin'              : min(xv),
        'xmax'              : max(xv),
        'ymin'              : min(yv),
        'ymax'              : 2 , # max(yv)
            
        'xtitle'            : "#sigma(ZH, Z#rightarrow#mu#mu)/#sigma_{ref}",
        'ytitle'            : "-2#DeltaNLL",
            
        'topRight'          : "#sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Internal}}",
    }
        
    plotter.cfg = cfg
        
    canvas = plotter.canvas()
    canvas.SetGrid()
    dummy = plotter.dummy()
        
    dummy.GetXaxis().SetNdivisions(507)    
    dummy.Draw("HIST")
    
    g.SetMarkerStyle(20)
    g.SetMarkerColor(ROOT.kRed)
    g.SetMarkerSize(1)
    g.SetLineColor(ROOT.kRed)
    g.SetLineWidth(2)
    g.Draw("SAME LP")

    
    line = ROOT.TLine(float(cfg['xmin']), 1, float(cfg['xmax']), 1)
    line.SetLineColor(ROOT.kBlack)
    line.SetLineWidth(2)
    line.Draw("SAME")

    leg = ROOT.TLegend(.20, 0.825, 0.90, .9)
    leg.SetBorderSize(0)
    leg.SetTextSize(0.035)
    leg.SetMargin(0.15)
    leg.SetBorderSize(1)
    leg.AddEntry(g, "%s, #delta(#sigma) = %.2f %%" % (label, unc*100.), "LP")
    leg.Draw()
              
    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/xsec%s.png" % (outDir, suffix))
    canvas.SaveAs("%s/xsec%s.pdf" % (outDir, suffix))
    
    # write values to text file
    str_out = "%f %f %f %f\n" % (unc_m, unc_p, unc, xsec)
    for i in range(0, len(xv)): str_out += "%f %f\n" % (xv[i], yv[i])
    tFile = open("%s/xsec%s.txt" % (outDir, suffix), "w")
    tFile.write(str_out)
    tFile.close()
    tFile = open("%s/xsec%s.txt" % (runDir, suffix), "w")
    tFile.write(str_out)
    tFile.close()

    

def doFit_xsec(runDir, rMin=0.98, rMax=1.02, npoints=50, combineOptions = ""):

    # scan for signal strength (= xsec)
    #cmd = "combine -M MultiDimFit -t -1 --setParameterRanges r=%f,%f --points=%d --algo=grid ws.root --expectSignal=1 -m 125 --X-rtd TMCSO_AdaptivePseudoAsimov -v 10 --X-rtd ADDNLL_CBNLL=0 -n xsec %s" % (rMin, rMax, npoints, combineOptions)
    cmd = "combine -M FitDiagnostics -t -1 ws.root --expectSignal=1 -m 125  -v 10 --rMin %f --rMax %f --points=%d --algo=grid --X-rtd TMCSO_AdaptivePseudoAsimov -v 10 --X-rtd ADDNLL_CBNLL=0 -n xsec %s" % (rMin, rMax, npoints, combineOptions)  
    subprocess.call(cmd, shell=True, cwd=runDir)
     
def doFit_mass(runDir, mhMin=124.99, mhMax=125.01, npoints=50, combineOptions = ""):

    # scan for signal mass
    cmd = "combine -M MultiDimFit -t -1 --setParameterRanges MH=%f,%f --points=%d --algo=grid ws.root --expectSignal=1 -m 125 --redefineSignalPOIs MH --X-rtd TMCSO_AdaptivePseudoAsimov -v 10 --X-rtd ADDNLL_CBNLL=0 -n mass %s" % (mhMin, mhMax, npoints, combineOptions)
    
    subprocess.call(cmd, shell=True, cwd=runDir)
    
def doFitDiagnostics_mass(runDir, mhMin=124.99, mhMax=125.01, combineOptions = ""):

    # scan for signal mass
    cmd = "combine -M FitDiagnostics -t -1 --setParameterRanges MH=%f,%f ws.root --expectSignal=1 -m 125 --redefineSignalPOIs MH --X-rtd TMCSO_AdaptivePseudoAsimov -v 10 --X-rtd ADDNLL_CBNLL=0 -n mass %s" % (mhMin, mhMax, combineOptions)
    
    # ,shapeBkg_bkg_bin1__norm
    subprocess.call(cmd, shell=True, cwd=runDir)
    
def plotMultiple(tags, labels, fOut, xMin=-1, xMax=-1, yMin=0, yMax=2):

    best_mass, best_xsec = [], []
    unc_mass, unc_xsec = [], []
    g_mass, g_xsec = [], []

    
    for tag in tags:
    
        xv, yv = [], []
        fIn = open("%s/mass%s.txt" % (tag, suffix), "r")
        for i,line in enumerate(fIn.readlines()):

            line = line.rstrip()
            if i == 0: 
                best_mass.append(float(line.split(" ")[3]))
                unc_mass.append(float(line.split(" ")[2]))
            else:
                xv.append(float(line.split(" ")[0]))
                yv.append(float(line.split(" ")[1]))
    
        g = ROOT.TGraph(len(xv), array.array('d', xv), array.array('d', yv))    
        g_mass.append(g)


 
    ########### PLOTTING ###########
    cfg = {

        'logy'              : False,
        'logx'              : False,
        
        'xmin'              : xMin,
        'xmax'              : xMax,
        'ymin'              : yMin,
        'ymax'              : yMax,
            
        'xtitle'            : "m_{h} (GeV)",
        'ytitle'            : "-2#DeltaNLL",
            
        'topRight'          : "#sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCC-ee} #scale[0.7]{#it{Simulation}}",
        }
        
    plotter.cfg = cfg
        
    canvas = plotter.canvas()
    canvas.SetGrid()
    dummy = plotter.dummy()
        
    dummy.GetXaxis().SetNdivisions(507)  
    dummy.Draw("HIST")
    
    totEntries = len(g_mass)
    leg = ROOT.TLegend(.20, 0.9-totEntries*0.05, 0.90, .9)
    leg.SetBorderSize(0)
    #leg.SetFillStyle(0) 
    leg.SetTextSize(0.03)
    leg.SetMargin(0.15)
    leg.SetBorderSize(1)
    
    colors = [ROOT.kBlack, ROOT.kRed, ROOT.kBlue, ROOT.kGreen+1]
    for i,g in enumerate(g_mass):
    
        g.SetMarkerStyle(20)
        g.SetMarkerColor(colors[i])
        g.SetMarkerSize(1)
        g.SetLineColor(colors[i])
        g.SetLineWidth(4)
        g.Draw("SAME L")
        leg.AddEntry(g, "%s #delta(m_{h}) = %.2f MeV" % (labels[i], unc_mass[i]*1000.), "L")
    
    leg.Draw()
    line = ROOT.TLine(float(cfg['xmin']), 1, float(cfg['xmax']), 1)
    line.SetLineColor(ROOT.kBlack)
    line.SetLineWidth(2)
    line.Draw("SAME")

    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s%s.png" % (fOut, suffix))
    canvas.SaveAs("%s%s.pdf" % (fOut, suffix))
    
    
def breakDown():

    def getUnc(tag, type_):

        xv, yv = [], []
        fIn = open("%s/%s_%s.txt" % (runDir, type_, tag), "r")
        for i,line in enumerate(fIn.readlines()):

            line = line.rstrip()
            if i == 0: 
                best = float(line.split(" ")[3])
                unc = float(line.split(" ")[2])
                break
                
        if type_ == "mass": unc*= 1000. # convert to MeV
        if type_ == "xsec": unc*= 100. # convert to %
        return best, unc


    ############# xsec
    canvas = ROOT.TCanvas("c", "c", 800, 800)
    canvas.SetTopMargin(0.08)
    canvas.SetBottomMargin(0.1)
    canvas.SetLeftMargin(0.25)
    canvas.SetRightMargin(0.05)
    canvas.SetFillStyle(4000) # transparency?
    canvas.SetGrid(1, 0)
    canvas.SetTickx(1)

    xMin, xMax = -2, 2
    xTitle = "#sigma_{syst.}(#sigma(ZH, Z#rightarrow#mu#mu)/#sigma_{ref}) (%)"

    ref = "IDEA_STAT"
    best_ref, unc_ref = getUnc(ref, "xsec")
    params = ["IDEA_ISR", "IDEA_BES", "IDEA_SQRTS", "IDEA_MUSCALE", "IDEA_ISR_BES_SQRTS_MUSCALE"]
    labels = ["ISR (conservative)", "BES 1%", "#sqrt{s} #pm 2 MeV", "Muon scale (~10^{-5})", "#splitline{Syst. combined}{(BES 1%)}"]
    
    
    n_params = len(params)
    h_pulls = ROOT.TH2F("pulls", "pulls", 6, xMin, xMax, n_params, 0, n_params)
    g_pulls = ROOT.TGraphAsymmErrors(n_params)

    i = n_params
    for p in xrange(n_params):

        i -= 1
        best, unc = getUnc(params[p], "xsec")
        unc = math.sqrt(unc**2 - unc_ref**2)
        g_pulls.SetPoint(i, 0, float(i) + 0.5)
        g_pulls.SetPointError(i, unc, unc, 0., 0.)
        h_pulls.GetYaxis().SetBinLabel(i + 1, labels[p])
       


    h_pulls.GetXaxis().SetTitleSize(0.04)
    h_pulls.GetXaxis().SetLabelSize(0.03)
    h_pulls.GetXaxis().SetTitle(xTitle)
    h_pulls.GetXaxis().SetTitleOffset(1)
    h_pulls.GetYaxis().SetLabelSize(0.045)
    h_pulls.GetYaxis().SetTickLength(0)
    h_pulls.GetYaxis().LabelsOption('v')
    h_pulls.SetNdivisions(506, 'XYZ')
    h_pulls.Draw("HIST")
    

    g_pulls.SetMarkerSize(0.8)
    g_pulls.SetMarkerStyle(20)
    g_pulls.SetLineWidth(2)
    g_pulls.Draw('P SAME')
    
    
    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextSize(0.045)
    latex.SetTextColor(1)
    latex.SetTextFont(42)
    latex.SetTextAlign(30) # 0 special vertical aligment with subscripts
    latex.DrawLatex(0.95, 0.925, "#sqrt{s} = 240 GeV, 5 ab^{#minus1}")

    latex.SetTextAlign(13)
    latex.SetTextFont(42)
    latex.SetTextSize(0.045)
    latex.DrawLatex(0.25, 0.96, "#bf{FCCee} #scale[0.7]{#it{Simulation}}")

        
    canvas.SaveAs("%s/xsec_breakDown.png" % outDir)
    canvas.SaveAs("%s/xsec_breakDown.pdf" % outDir)    
    del canvas, g_pulls, h_pulls

  
    ############# mass
    canvas = ROOT.TCanvas("c", "c", 800, 800)
    canvas.SetTopMargin(0.08)
    canvas.SetBottomMargin(0.1)
    canvas.SetLeftMargin(0.25)
    canvas.SetRightMargin(0.05)
    canvas.SetFillStyle(4000) # transparency?
    canvas.SetGrid(1, 0)
    canvas.SetTickx(1)


    xMin, xMax = -5, 5
    xTitle = "#sigma_{syst.}(m_{h}) (MeV)"

    ref = "IDEA_STAT"
    best_ref, unc_ref = getUnc(ref, "mass")
    params = ["IDEA_ISR", "IDEA_BES", "IDEA_SQRTS", "IDEA_MUSCALE", "IDEA_ISR_BES_SQRTS_MUSCALE"]
    labels = ["ISR (conservative)", "BES 1%", "#sqrt{s} #pm 2 MeV", "Muon scale (~10^{-5})", "#splitline{Syst. combined}{(BES 1%)}"]
    
    n_params = len(params)
    h_pulls = ROOT.TH2F("pulls", "pulls", 6, xMin, xMax, n_params, 0, n_params)
    g_pulls = ROOT.TGraphAsymmErrors(n_params)

    i = n_params
    for p in xrange(n_params):

        i -= 1
        best, unc = getUnc(params[p], "mass")
        unc = math.sqrt(unc**2 - unc_ref**2)
        g_pulls.SetPoint(i, 0, float(i) + 0.5)
        g_pulls.SetPointError(i, unc, unc, 0., 0.)
        h_pulls.GetYaxis().SetBinLabel(i + 1, labels[p])
       


    h_pulls.GetXaxis().SetTitleSize(0.04)
    h_pulls.GetXaxis().SetLabelSize(0.03)
    h_pulls.GetXaxis().SetTitle(xTitle)
    h_pulls.GetXaxis().SetTitleOffset(1)
    h_pulls.GetYaxis().SetLabelSize(0.045)
    h_pulls.GetYaxis().SetTickLength(0)
    h_pulls.GetYaxis().LabelsOption('v')
    h_pulls.SetNdivisions(506, 'XYZ')
    h_pulls.Draw("HIST")
    

    g_pulls.SetMarkerSize(0.8)
    g_pulls.SetMarkerStyle(20)
    g_pulls.SetLineWidth(2)
    g_pulls.Draw('P SAME')
    
    
    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextSize(0.045)
    latex.SetTextColor(1)
    latex.SetTextFont(42)
    latex.SetTextAlign(30) # 0 special vertical aligment with subscripts
    latex.DrawLatex(0.95, 0.925, "#sqrt{s} = 240 GeV, 5 ab^{#minus1}")

    latex.SetTextAlign(13)
    latex.SetTextFont(42)
    latex.SetTextSize(0.045)
    latex.DrawLatex(0.25, 0.96, "#bf{FCCee} #scale[0.7]{#it{Simulation}}")

        
    canvas.SaveAs("%s/mass_breakDown.png" % outDir)
    canvas.SaveAs("%s/mass_breakDown.pdf" % outDir)   
    del canvas, g_pulls, h_pulls
    

def text2workspace(runDir):

    cmd = "text2workspace.py datacard.txt -o ws.root  -v 10"
    subprocess.call(cmd, shell=True, cwd=runDir)
    
def combineCards(runDir, input_=[]):

    if not os.path.exists(runDir): os.makedirs(runDir)
    
    input_ = ["%s/%s" % (os.getcwd(), i) for i in input_]
    cards = ' '.join(input_)
    
    cmd = "combineCards.py %s > datacard.txt" % cards
    subprocess.call(cmd, shell=True, cwd=runDir)
    text2workspace(runDir)

  
if __name__ == "__main__":

    combineDir = "combine/run_binned_BDT/"
    outDir = "/eos/user/l/lia/FCCee/ZH_Converge/combine/"
    doSyst=False
    
    suffix=""
    if not doSyst:
        suffix = "_stat"
    
    ############### MUON
    if True:
        combineOptions = "--setParameters shapeBkg_bkg_bin1__norm=0,r=1.0"
        #combineOptions = "--freezeParameters r,shapeBkg_bkg_bin1__norm --setParameters MH=125.00,shapeBkg_bkg_bin1__norm=0"
        combineOptions = "--freezeParameters bkg_norm --setParameters bkg_norm=0"
        #combineOptions = "--freezeParameters r,shapeBkg_bkg_bin1__norm --setParameters MH=125.00,shapeBkg_bkg_bin1__norm=0"
        combineOptions = ""
        #if not doSyst:
        #    combineOptions = "--freezeParameters BES,ISR,SQRTS,LEPSCALE_MU"
        
        tag, label = "mumu", "#mu^{#plus}#mu^{#minus}, inclusive"
        mhMin, mhMax = 124.99, 125.01
        rMin, rMax = 0.98, 1.02
        #doFit_mass("%s/%s" % (combineDir, tag), mhMin=mhMin, mhMax=mhMax, npoints=50, combineOptions=combineOptions)
        #analyzeMass("%s/%s" % (combineDir, tag), "%s/%s/" % (outDir, tag), label=label, xMin=mhMin, xMax=mhMax)
        doFit_xsec("%s/%s" % (combineDir, tag), rMin=rMin, rMax=rMax, npoints=50, combineOptions=combineOptions)
        analyzeXsec("%s/%s" % (combineDir, tag), "%s/%s/" % (outDir, tag), label=label, xMin=rMin, xMax=rMax)
        #doFitDiagnostics_mass("%s/%s" % (combineDir, tag), mhMin=mhMin, mhMax=mhMax, combineOptions=combineOptions)
        
     
        #tag, label = "mumu_cat1", "#mu^{#plus}#mu^{#minus}, central-central"
        #mhMin, mhMax = 124.99, 125.01
        #doFit_mass("%s/%s" % (combineDir, tag), mhMin=mhMin, mhMax=mhMax, npoints=50, combineOptions=combineOptions)
        #analyzeMass("%s/%s" % (combineDir, tag), "%s/%s/" % (outDir, tag), label=label, xMin=mhMin, xMax=mhMax)
        #
        #tag, label = "mumu_cat2", "#mu^{#plus}#mu^{#minus}, central-forward"
        #mhMin, mhMax = 124.98, 125.02
        #doFit_mass("%s/%s" % (combineDir, tag), mhMin=mhMin, mhMax=mhMax, npoints=50, combineOptions=combineOptions)
        #analyzeMass("%s/%s" % (combineDir, tag), "%s/%s/" % (outDir, tag), label=label, xMin=mhMin, xMax=mhMax)
        #
        #tag, label = "mumu_cat3", "#mu^{#plus}#mu^{#minus}, forward-forward"
        #mhMin, mhMax = 124.98, 125.02
        #doFit_mass("%s/%s" % (combineDir, tag), mhMin=mhMin, mhMax=mhMax, npoints=50, combineOptions=combineOptions)
        #analyzeMass("%s/%s" % (combineDir, tag), "%s/%s/" % (outDir, tag), label=label, xMin=mhMin, xMax=mhMax)
        #
        #tag, label = "mumu_combined", "#mu^{#plus}#mu^{#minus}, combined"
        #mhMin, mhMax = 124.99, 125.01
        #combineCards("%s/%s" % (combineDir, tag), [combineDir+"/mumu_cat1/datacard_parametric.txt", combineDir+"/mumu_cat2/datacard_parametric.txt", combineDir+"/mumu_cat3/datacard_parametric.txt"])
        #doFit_mass("%s/%s" % (combineDir, tag), mhMin=mhMin, mhMax=mhMax, npoints=50, combineOptions=combineOptions)
        #analyzeMass("%s/%s" % (combineDir, tag), "%s/%s/" % (outDir, tag), label=label, xMin=mhMin, xMax=mhMax)
        

    
    ############### ELECTRON
    if False:
    
        combineOptions = "--freezeParameters r --setParameters ,r=1.067"
        combineOptions = ""
        if not doSyst:
            combineOptions = "--freezeParameters BES,ISR,SQRTS,LEPSCALE_EL"
    
        tag, label = "ee_cat0", "e^{#plus}e^{#minus}, inclusive"
        mhMin, mhMax = 124.98, 125.02
        rMin, rMax = 0.98, 1.02
        doFit_mass("%s/%s" % (combineDir, tag), mhMin=mhMin, mhMax=mhMax, npoints=50, combineOptions=combineOptions)
        analyzeMass("%s/%s" % (combineDir, tag), "%s/%s/" % (outDir, tag), label=label, xMin=mhMin, xMax=mhMax)
        #doFitDiagnostics_mass("%s/%s" % (combineDir, tag), mhMin=mhMin, mhMax=mhMax, combineOptions=combineOptions)
        
        tag, label = "ee_cat1", "e^{#plus}e^{#minus}, central-central"
        mhMin, mhMax = 124.98, 125.02
        doFit_mass("%s/%s" % (combineDir, tag), mhMin=mhMin, mhMax=mhMax, npoints=50, combineOptions=combineOptions)
        analyzeMass("%s/%s" % (combineDir, tag), "%s/%s/" % (outDir, tag), label=label, xMin=mhMin, xMax=mhMax)
       
        tag, label = "ee_cat2", "e^{#plus}e^{#minus}, central-forward"
        mhMin, mhMax = 124.98, 125.02
        doFit_mass("%s/%s" % (combineDir, tag), mhMin=mhMin, mhMax=mhMax, npoints=50, combineOptions=combineOptions)
        analyzeMass("%s/%s" % (combineDir, tag), "%s/%s/" % (outDir, tag), label=label, xMin=mhMin, xMax=mhMax)
        
        tag, label = "ee_cat3", "e^{#plus}e^{#minus}, forward-forward"
        mhMin, mhMax = 124.95, 125.05
        doFit_mass("%s/%s" % (combineDir, tag), mhMin=mhMin, mhMax=mhMax, npoints=50, combineOptions=combineOptions)
        analyzeMass("%s/%s" % (combineDir, tag), "%s/%s/" % (outDir, tag), label=label, xMin=mhMin, xMax=mhMax)
        
        tag, label = "ee_combined", "e^{#plus}e^{#minus}, combined"
        mhMin, mhMax = 124.99, 125.01
        combineCards("%s/%s" % (combineDir, tag), [combineDir+"/ee_cat1/datacard_parametric.txt", combineDir+"/ee_cat2/datacard_parametric.txt", combineDir+"/ee_cat3/datacard_parametric.txt"])
        doFit_mass("%s/%s" % (combineDir, tag), mhMin=mhMin, mhMax=mhMax, npoints=50, combineOptions=combineOptions)
        analyzeMass("%s/%s" % (combineDir, tag), "%s/%s/" % (outDir, tag), label=label, xMin=mhMin, xMax=mhMax)
        
    
    ############### MUON+ELECTRON
    if False:
        combineOptions = ""
        if not doSyst:
            combineOptions = "--freezeParameters BES,ISR,SQRTS,LEPSCALE_MU,LEPSCALE_EL,bkg_norm --setParameters bkg_norm=0"
    
        tag, label = "mumu_ee_combined_inclusive", "#mu^{#plus}#mu^{#minus}+e^{#plus}e^{#minus}, inclusive"
        mhMin, mhMax = 124.99, 125.01
        combineCards("%s/%s" % (combineDir, tag), [combineDir+"/mumu_cat0/datacard_parametric.txt", combineDir+"/ee_cat0/datacard_parametric.txt"])
        doFit_mass("%s/%s" % (combineDir, tag), mhMin=mhMin, mhMax=mhMax, npoints=50, combineOptions=combineOptions)
        analyzeMass("%s/%s" % (combineDir, tag), "%s/%s/" % (outDir, tag), label=label, xMin=mhMin, xMax=mhMax)
        
        tag, label = "mumu_ee_combined_categorized", "#mu^{#plus}#mu^{#minus}+e^{#plus}e^{#minus}, categorized"
        mhMin, mhMax = 124.99, 125.01
        combineCards("%s/%s" % (combineDir, tag), [combineDir+"/mumu_combined/datacard.txt", combineDir+"/ee_combined/datacard.txt"])
        doFit_mass("%s/%s" % (combineDir, tag), mhMin=mhMin, mhMax=mhMax, npoints=50, combineOptions=combineOptions)
        analyzeMass("%s/%s" % (combineDir, tag), "%s/%s/" % (outDir, tag), label=label, xMin=mhMin, xMax=mhMax)
        
        
        plotMultiple(["%s/mumu_cat0/"%outDir, "%s/ee_cat0/"%outDir, "%s/mumu_ee_combined_inclusive/"%outDir], ["#mu^{#plus}#mu^{#minus}, inclusive", "e^{#plus}e^{#minus}, inclusive", "#mu^{#plus}#mu^{#minus} + e^{#plus}e^{#minus}, inclusive"], "%s/mumu_ee_inclusive"%outDir, xMin=124.99, xMax=125.01)
        
        plotMultiple(["%s/mumu_combined/"%outDir, "%s/ee_combined/"%outDir, "%s/mumu_ee_combined_categorized/"%outDir], ["#mu^{#plus}#mu^{#minus}, categorized", "e^{#plus}e^{#minus}, categorized", "#mu^{#plus}#mu^{#minus} + e^{#plus}e^{#minus}, categorized"], "%s/mumu_ee_categorized"%outDir, xMin=124.99, xMax=125.01)
        
        
        plotMultiple(["%s/mumu_cat0/"%outDir, "%s/mumu_combined/"%outDir, "%s/ee_cat0/"%outDir, "%s/ee_combined/"%outDir], ["#mu^{#plus}#mu^{#minus}, inclusive", "#mu^{#plus}#mu^{#minus}, categorized", "e^{#plus}e^{#minus}, inclusive", "e^{#plus}e^{#minus}, categorized"], "%s/mumu_ee_inclusive_categorized"%outDir, xMin=124.99, xMax=125.01)
        
        
        
    combineDir = "combine/run_mc"
    outDir = "/eos/user/j/jaeyserm/www/FCCee/ZH_mass_xsec/combine_mc/"
    
    ############### MUON
    if False:
    
        #combineOptions = "--setParameters MH=125.02"
        #combineOptions = "--setParameters MH=125.02,shapeBkg_bkg_bin1__norm=0,r=1.06"
        #combineOptions = "--setParameters shapeBkg_bkg_bin1__norm=0,r=1.06"
        combineOptions = "--freezeParameters r,shapeBkg_bkg_bin1__norm --setParameters MH=125.00,shapeBkg_bkg_bin1__norm=0"
    
        tag, label = "mumu_cat0", "#mu^{#plus}#mu^{#minus}, inclusive"
        xMin, xMax = 124.9, 125.1
        #doFitDiagnostics_mass("%s/%s" % (combineDir, tag), mhMin=xMin, mhMax=xMax, combineOptions=combineOptions)
        #doFit_mass("%s/%s" % (combineDir, tag), mhMin=xMin, mhMax=xMax, npoints=50, combineOptions=combineOptions)
        #analyzeMass("%s/%s" % (combineDir, tag), "%s/%s/" % (outDir, tag), label=label, xMin=xMin, xMax=xMax)
        
        tag, label = "ee_cat0", "e^{#plus}e^{#minus}, inclusive"
        xMin, xMax = 124.9, 125.1
        doFitDiagnostics_mass("%s/%s" % (combineDir, tag), mhMin=xMin, mhMax=xMax, combineOptions=combineOptions)
        #doFit_mass("%s/%s" % (combineDir, tag), mhMin=xMin, mhMax=xMax, npoints=50, combineOptions=combineOptions)
        #analyzeMass("%s/%s" % (combineDir, tag), "%s/%s/" % (outDir, tag), label=label, xMin=xMin, xMax=xMax)
