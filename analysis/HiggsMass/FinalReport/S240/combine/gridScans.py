
import sys,copy,array,os,subprocess,math
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../python")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../baselineAnalysis")
import functions
import datasets as ds
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

def analyzeMass(tag):

    fIn = ROOT.TFile("%s/higgsCombine%s_mass.MultiDimFit.mH125.root" % (runDir, tag), "READ")
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
    unc_m = findCrossing(xv, yv, left=True)
    unc_p = findCrossing(xv, yv, left=False)
    unc = 0.5*(abs(mass-unc_m) + abs(unc_p-mass))
    

       
    ########### PLOTTING ###########
    cfg = {

        'logy'              : False,
        'logx'              : False,
        
        'xmin'              : min(xv),
        'xmax'              : max(xv),
        'ymin'              : min(yv),
        'ymax'              : 2 , # max(yv)
            
        'xtitle'            : "m_{h} (GeV)",
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
    
    leg = ROOT.TLegend(.20, 0.82, 0.90, .9)
    leg.SetBorderSize(0)
    leg.SetTextSize(0.035)
    leg.SetMargin(0.15)
    leg.SetBorderSize(1)
    leg.AddEntry(g,  "m_{h} = %.3f GeV #pm  %.2f MeV" % (mass, unc*1000.), "L")
    leg.Draw()
        
    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/mass_%s.png" % (outDir, tag))
    canvas.SaveAs("%s/mass_%s.pdf" % (outDir, tag))
    
    
    # write values to text file
    str_out = "%f %f %f %f\n" % (unc_m, unc_p, unc, mass)
    for i in range(0, len(xv)): str_out += "%f %f\n" % (xv[i], yv[i])
    tFile = open("%s/mass_%s.txt" % (outDir, tag), "w")
    tFile.write(str_out)
    tFile.close()
    tFile = open("%s/mass_%s.txt" % (runDir, tag), "w")
    tFile.write(str_out)
    tFile.close()
        
def analyzeXsec(tag):

    fIn = ROOT.TFile("%s/higgsCombine%s_xsec.MultiDimFit.mH125.root" % (runDir, tag), "READ")
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
    
    leg = ROOT.TLegend(.20, 0.82, 0.90, .9)
    leg.SetBorderSize(0)
    leg.SetTextSize(0.035)
    leg.SetMargin(0.15)
    leg.SetBorderSize(1)
    leg.AddEntry(g, "#sigma = %.5f #pm  %.5f" % (xsec, unc), "L")
    leg.Draw()
              
    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/xsec_%s.png" % (outDir, tag))
    canvas.SaveAs("%s/xsec_%s.pdf" % (outDir, tag))
    
    
    # write values to text file
    str_out = "%f %f %f %f\n" % (unc_m, unc_p, unc, xsec)
    for i in range(0, len(xv)): str_out += "%f %f\n" % (xv[i], yv[i])
    tFile = open("%s/xsec_%s.txt" % (outDir, tag), "w")
    tFile.write(str_out)
    tFile.close()
    tFile = open("%s/xsec_%s.txt" % (runDir, tag), "w")
    tFile.write(str_out)
    tFile.close()

def calculateXsec(tag, combineOptions = "", rMin=0.95, rMax=1.05, npoints=50):

    # scan for signal strength (= xsec)
    cmd = "combine -M MultiDimFit -t -1 --setParameterRanges r=%f,%f --points=%d --algo=grid ws.root --expectSignal=1 -m 125 --X-rtd TMCSO_AdaptivePseudoAsimov -v 10 --X-rtd ADDNLL_CBNLL=0 -n %s_xsec %s" % (rMin, rMax, npoints, tag, combineOptions)
    
    subprocess.call(cmd, shell=True, cwd=runDir)
     
def calculateMass(tag, combineOptions = "", mhMin=124.99, mhMax=125.01, npoints=50):

    # scan for signal mass
    cmd = "combine -M MultiDimFit -t -1 --setParameterRanges MH=%f,%f --points=%d --algo=grid ws.root --expectSignal=1 -m 125 --redefineSignalPOIs MH --X-rtd TMCSO_AdaptivePseudoAsimov -v 10 --X-rtd ADDNLL_CBNLL=0 -n %s_mass %s" % (mhMin, mhMax, npoints, tag, combineOptions)
    
    subprocess.call(cmd, shell=True, cwd=runDir)
    
def plotMultiple(tags, labels, fOut):

    best_mass, best_xsec = [], []
    unc_mass, unc_xsec = [], []
    g_mass, g_xsec = [], []

    
    for tag in tags:
    
        xv, yv = [], []
        fIn = open("%s/xsec_%s.txt" % (runDir, tag), "r")
        for i,line in enumerate(fIn.readlines()):

            line = line.rstrip()
            if i == 0: 
                best_xsec.append(float(line.split(" ")[3]))
                unc_xsec.append(float(line.split(" ")[2]))
            else:
                
                xv.append(float(line.split(" ")[0]))
                yv.append(float(line.split(" ")[1]))
    
        g = ROOT.TGraph(len(xv), array.array('d', xv), array.array('d', yv))    
        g_xsec.append(g)
        
        
        
        xv, yv = [], []
        fIn = open("%s/mass_%s.txt" % (runDir, tag), "r")
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
        
        'xmin'              : 124.99,
        'xmax'              : 125.01,
        'ymin'              : 0,
        'ymax'              : 2,
            
        'xtitle'            : "m_{h} (GeV)",
        'ytitle'            : "-2#DeltaNLL",
            
        'topRight'          : "#sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Simulation}}",
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
    
    colors = [ROOT.kBlack, ROOT.kRed, ROOT.kBlue]
    for i,g in enumerate(g_mass):
    
        g.SetMarkerStyle(20)
        g.SetMarkerColor(colors[i])
        g.SetMarkerSize(1)
        g.SetLineColor(colors[i])
        g.SetLineWidth(4)
        g.Draw("SAME L")
        leg.AddEntry(g,  "%s m_{h}=%.3f GeV #pm %.2f MeV" % (labels[i], best_mass[i], unc_mass[i]*1000.), "L")
    
    leg.Draw()
    line = ROOT.TLine(float(cfg['xmin']), 1, float(cfg['xmax']), 1)
    line.SetLineColor(ROOT.kBlack)
    line.SetLineWidth(2)
    line.Draw("SAME")

    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/mass_%s.png" % (outDir, fOut))
    canvas.SaveAs("%s/mass_%s.pdf" % (outDir, fOut))
    
    del dummy
    del canvas
    del leg
    
    
    ########### PLOTTING ###########
    cfg = {

        'logy'              : False,
        'logx'              : False,
        
        'xmin'              : 0.985, # 0.985 0.975
        'xmax'              : 1.015, # 1.015 1.025
        'ymin'              : 0,
        'ymax'              : 2 , # max(yv)
            
        'xtitle'            : "#sigma(ZH, Z#rightarrow#mu#mu)/#sigma_{ref}",
        'ytitle'            : "-2#DeltaNLL",
            
        'topRight'          : "#sqrt{s} = 240 GeV, 5 ab^{#minus1}", 
        'topLeft'           : "#bf{FCCee} #scale[0.7]{#it{Simulation}}",
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
    leg.SetTextSize(0.035)
    leg.SetMargin(0.15)
    leg.SetBorderSize(1)
    
    colors = [ROOT.kBlack, ROOT.kRed, ROOT.kBlue]
    for i,g in enumerate(g_xsec):
    
        g.SetMarkerStyle(20)
        g.SetMarkerColor(colors[i])
        g.SetMarkerSize(1)
        g.SetLineColor(colors[i])
        g.SetLineWidth(4)
        g.Draw("SAME L")
        leg.AddEntry(g,  "%s #sigma=%.5f #pm %.5f" % (labels[i], best_xsec[i], unc_xsec[i]), "L")
    
    leg.Draw()
    line = ROOT.TLine(float(cfg['xmin']), 1, float(cfg['xmax']), 1)
    line.SetLineColor(ROOT.kBlack)
    line.SetLineWidth(2)
    line.Draw("SAME")

    plotter.aux()
    
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/xsec_%s.png" % (outDir, fOut))
    canvas.SaveAs("%s/xsec_%s.pdf" % (outDir, fOut))
    
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
    params = ["IDEA_ISR", "IDEA_FSR", "IDEA_BES", "IDEA_SQRTS", "IDEA_MUSCALE", "IDEA_ISR_FSR_BES_SQRTS_MUSCALE"]
    labels = ["ISR (pT rewei.)", "FSR", "BES 1%", "#sqrt{s} #pm 2 MeV", "Muon scale (~10^{-5})", "#splitline{Syst. combined}{(BES 1%)}"]
    
    
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
    params = ["IDEA_ISR", "IDEA_FSR", "IDEA_BES", "IDEA_SQRTS", "IDEA_MUSCALE", "IDEA_ISR_FSR_BES_SQRTS_MUSCALE"]
    labels = ["ISR (pT rewei.)", "FSR", "BES 1%", "#sqrt{s} #pm 2 MeV", "Muon scale (~10^{-5})", "#splitline{Syst. combined}{(BES 1%)}"]
    
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
    
    
if __name__ == "__main__":

    runDir = "fitAnalysis/combine"
    outDir = "/eos/user/l/lia/FCCee/mumu_Combine/plots"


    tag = "IDEA_STAT"
    combineOptions = "--freezeParameters=BES,ISR,FSR,SQRTS,MUSCALE"
    calculateXsec(tag, combineOptions, rMin=0.97, rMax=1.03, npoints=100)
    calculateMass(tag, combineOptions, mhMin=124.99, mhMax=125.01, npoints=100)
    analyzeXsec(tag)
    analyzeMass(tag)
    
    tag = "IDEA_BES"
    combineOptions = "--freezeParameters=ISR,FSR,SQRTS,MUSCALE"
    calculateXsec(tag, combineOptions, rMin=0.97, rMax=1.03, npoints=100)
    calculateMass(tag, combineOptions, mhMin=124.99, mhMax=125.01, npoints=100)
    analyzeXsec(tag)
    analyzeMass(tag)
    
    tag = "IDEA_ISR"
    combineOptions = "--freezeParameters=BES,FSR,SQRTS,MUSCALE"
    calculateXsec(tag, combineOptions, rMin=0.97, rMax=1.03, npoints=100)
    calculateMass(tag, combineOptions, mhMin=124.99, mhMax=125.01, npoints=100)
    analyzeXsec(tag)
    analyzeMass(tag)
    
    tag = "IDEA_FSR"
    combineOptions = "--freezeParameters=BES,ISR,SQRTS,MUSCALE"
    calculateXsec(tag, combineOptions, rMin=0.97, rMax=1.03, npoints=100)
    calculateMass(tag, combineOptions, mhMin=124.99, mhMax=125.01, npoints=100)
    analyzeXsec(tag)
    analyzeMass(tag)
 
    tag = "IDEA_MUSCALE"
    combineOptions = "--freezeParameters=BES,ISR,FSR,SQRTS"
    calculateXsec(tag, combineOptions, rMin=0.97, rMax=1.03, npoints=100)
    calculateMass(tag, combineOptions, mhMin=124.99, mhMax=125.01, npoints=100)
    analyzeXsec(tag)
    analyzeMass(tag)
    
    tag = "IDEA_SQRTS"
    combineOptions = "--freezeParameters=BES,ISR,FSR,MUSCALE"
    calculateXsec(tag, combineOptions, rMin=0.97, rMax=1.03, npoints=100)
    calculateMass(tag, combineOptions, mhMin=124.99, mhMax=125.01, npoints=100)
    analyzeXsec(tag)
    analyzeMass(tag)

    tag = "IDEA_ISR_FSR_BES_SQRTS_MUSCALE"
    combineOptions = ""
    calculateXsec(tag, combineOptions, rMin=0.97, rMax=1.03, npoints=100)
    calculateMass(tag, combineOptions, mhMin=124.99, mhMax=125.01, npoints=100)
    analyzeXsec(tag)
    analyzeMass(tag)


    # combine STAT and STAT+SYST plots
    plotMultiple(["IDEA_STAT", "IDEA_ISR_BES_SQRTS_MUSCALE"], ["Stat. only", "Stat.+Syst."], "IDEA_summary")
    plotMultiple(["IDEA_STAT", "IDEA_ISR"], ["Stat. only", "Stat.+ISR rewei."], "IDEA_ISR_rewei_summary")
    plotMultiple(["IDEA_STAT", "IDEA_FSR"], ["Stat. only", "Stat.+FSR"], "IDEA_FSR_summary")
    # systematics breakdown plot
    breakDown()
