
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
            
        'topRight'          : "#sqrt{s} = 240 GeV,  7.2 ab^{#minus1}", 
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

    if not os.path.exists(outDir): os.makedirs(outDir)
    if not os.path.exists(runDir): os.makedirs(runDir)
    fIn = ROOT.TFile("%s/higgsCombinexsec.MultiDimFit.mH125.root" % runDir, "READ")
    t = fIn.Get("limit")
    
    ref_xsec = 0.201868 # pb, for pythia
    ref_xsec = 0.0067656 # whizard, Z->mumu
    ref_xsec = 1.0000000000

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
            
        'topRight'          : "#sqrt{s} = 240 GeV,  7.2 ab^{#minus1}", 
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
    leg.AddEntry(g, "%s, #delta(#sigma) = %.4f %%" % (label, unc*100.), "LP")
    leg.Draw()
              
    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/xsec%s.png" % (outDir, suffix))
    canvas.SaveAs("%s/xsec%s.pdf" % (outDir, suffix))
    
    # write values to text file
    str_out = "%.16f %.16f %.16f %.16f\n" % (unc_m, unc_p, unc, xsec)
    for i in range(0, len(xv)): str_out += "%.16f %.16f\n" % (xv[i], yv[i])
    tFile = open("%s/xsec%s.txt" % (outDir, suffix), "w")
    tFile.write(str_out)
    tFile.close()
    tFile = open("%s/xsec%s.txt" % (runDir, suffix), "w")
    print "writing to %s/xsec%s.txt" % (runDir, suffix)
    tFile.close()


def doFit_xsec(runDir, rMin=0.98, rMax=1.02, npoints=50, combineOptions = ""):
    os.makedirs(runDir) if not os.path.exists(runDir) else None
    # scan for signal strength (= xsec)
    cmd = "combine -M MultiDimFit -t -1 --setParameterRanges r=%f,%f --points=%d --algo=grid ws.root --expectSignal=1 -m 125 --X-rtd TMCSO_AdaptivePseudoAsimov -v 10 --X-rtd ADDNLL_CBNLL=0 -n xsec %s" % (rMin, rMax, npoints, combineOptions)
    
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

def doFitDiagnostics_xsec(runDir, rMin=0.98, rMax=1.02, combineOptions = ""):

    # scan for signal mass
    cmd = "combine -M FitDiagnostics -t -1 --setParameterRanges r=%f,%f ws.root --expectSignal=1 -m 125 --redefineSignalPOIs r --X-rtd TMCSO_AdaptivePseudoAsimov -v 10 --X-rtd ADDNLL_CBNLL=0 -n xsec %s" % (rMin, rMax, combineOptions)
    
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
            
        'topRight'          : "#sqrt{s} = 240 GeV,  7.2 ab^{#minus1}", 
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
 

def plotMultiple_xsec(tags, labels, dirIn, fOut, xMin=-1, xMax=-1, yMin=0, yMax=2, name=""):

    best_xsec, unc_xsec, g_xsec = [], [], []
    for n,tag in enumerate(tags):
        
        xv, yv = [], []
        fIn = open("%s/xsec_%s.txt" % (dirIn[n], tag), "r")
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


    xTitle = ""
    if flavor == "mm":
        xTitle = "#sigma(ZH#rightarrow#mu^{#plus}#mu^{#minus})/#sigma_{ref}"
    elif flavor == "ee":
        xTitle = "#sigma(ZH#rightarrow e^{#plus}e^{#minus})/#sigma_{ref}"
    elif flavor == "combine":
        xTitle = "#sigma(ZH#rightarrow l^{#plus}l^{#minus})/#sigma_{ref}"



    cfg = {

        'logy'              : False,
        'logx'              : False,
        
        'xmin'              : 0.98,
        'xmax'              : 1.02,
        'ymin'              : yMin,
        'ymax'              : 2,

        'xtitle'            : xTitle,
        'ytitle'            : "-2#DeltaNLL",
            
        'topRight'          : "#sqrt{s} = 240 GeV,  7.2 ab^{#minus1}", 
        'topLeft'           : "#bf{FCC-ee} #scale[0.7]{#it{Simulation}}",
        }
        
    plotter.cfg = cfg
        
    canvas = plotter.canvas()
    canvas.SetGrid()
    dummy = plotter.dummy()
        
    dummy.GetXaxis().SetNdivisions(507)  
    dummy.Draw("HIST")
    
    totEntries = len(g_xsec)
    leg = ROOT.TLegend(.20, 0.9-totEntries*0.05, 0.90, .9)
    leg.SetBorderSize(0)
    #leg.SetFillStyle(0) 
    leg.SetTextSize(0.03)
    leg.SetMargin(0.15)
    leg.SetBorderSize(1)
    
    colors = [ROOT.kBlack, ROOT.kRed, ROOT.kBlue, ROOT.kGreen+1]
    for i,g in enumerate(g_xsec):
    
        g.SetMarkerStyle(20)
        g.SetMarkerColor(colors[i])
        g.SetMarkerSize(1)
        g.SetLineColor(colors[i])
        g.SetLineWidth(4)
        g.Draw("SAME L")
        leg.AddEntry(g, "%s #delta(#sigma) = %.4f %%" % (labels[i], unc_xsec[i]*100.), "L")
    
    leg.Draw()
    line = ROOT.TLine(float(cfg['xmin']), 1, float(cfg['xmax']), 1)
    line.SetLineColor(ROOT.kBlack)
    line.SetLineWidth(2)
    line.Draw("SAME")

    plotter.aux()
    canvas.Modify()
    canvas.Update()
    canvas.Draw()
    canvas.SaveAs("%s/%s_summary%s.png" % (fOut, flavor, name))
    canvas.SaveAs("%s/%s_summary%s.pdf" % (fOut, flavor, name))
  
    
def breakDown():

    def getUnc(tag, type_):

        xv, yv = [], []
        fIn = open("%s/%s_%s.txt" % (runDir, type_, tag), "r")
        print("Opening: %s/%s_%s.txt" % (runDir, type_, tag))
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

    if flavor == "combine":
        xMin, xMax = -0.12, 0.12
    else:
        xMin, xMax = -0.12, 0.12
    if flavor == "mumu":
        xTitle = "#sigma_{syst.}(#sigma(ZH, Z#rightarrow#mu#mu)/#sigma_{ref}) (%)"
    elif flavor == "ee": 
        xTitle = "#sigma_{syst.}(#sigma(ZH, Z#rightarrow ee)/#sigma_{ref}) (%)"
    elif flavor == "combine":
        xTitle = "#sigma_{syst.}(#sigma(ZH, Z#rightarrow ll)/#sigma_{ref}) (%)"

    ref = "STAT"
    best_ref, unc_ref = getUnc(ref, "xsec")
    print("reference")
    print(best_ref, unc_ref)
    if flavor == "mumu":
        params = ["BES", "SQRTS", "MUSCALE", "BES_SQRTS_MUSCALE"]
        labels = ["BES 1%", "#sqrt{s} #pm 2 MeV", "Muon scale (~10^{-5})", "#splitline{Syst. combined}{(BES 1%)}"]
    elif flavor == "ee":
        params = ["BES", "SQRTS", "ELSCALE", "BES_SQRTS_ELSCALE"]
        labels = ["BES 1%", "#sqrt{s} #pm 2 MeV", "Electron scale (~10^{-5})", "#splitline{Syst. combined}{(BES 1%)}"]
    elif flavor == "combine":
        params = ["BES", "SQRTS", "MUSCALE", "ELSCALE", "BES_SQRTS_MUSCALE_ELSCALE"]
        labels = ["BES 1%", "#sqrt{s} #pm 2 MeV", "Muon scale (~10^{-5})", "El. scale (~10^{-5})", "#splitline{Syst. combined}{(BES 1%)}"]

    n_params = len(params)
    h_pulls = ROOT.TH2F("pulls", "pulls", 6, xMin, xMax, n_params, 0, n_params)
    g_pulls = ROOT.TGraphAsymmErrors(n_params)

    i = n_params
    for p in xrange(n_params):

        i -= 1
        best, unc = getUnc(params[p], "xsec")
        print(params[p])
        print(best, unc)
        unc = math.sqrt(abs(unc**2 - unc_ref**2))
        print(unc)
        g_pulls.SetPoint(i, 0, float(i) + 0.5)
        g_pulls.SetPointError(i, unc, unc, 0., 0.)
        #h_pulls.GetYaxis().SetBinLabel(i + 1, labels[p])
        h_pulls.GetYaxis().SetBinLabel(i + 1, "#splitline{%s}{(%.6f %%)}" % (labels[p], unc)) 

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
    latex.DrawLatex(0.95, 0.925, "#sqrt{s} = 240 GeV,  7.2 ab^{#minus1}")

    latex.SetTextAlign(13)
    latex.SetTextFont(42)
    latex.SetTextSize(0.045)
    latex.DrawLatex(0.25, 0.96, "#bf{FCCee} #scale[0.7]{#it{Simulation}}")

        
    canvas.SaveAs("%s/xsec_breakDown.png" % outDir)
    canvas.SaveAs("%s/xsec_breakDown.pdf" % outDir)    
    del canvas, g_pulls, h_pulls

  
    ############## mass
    #canvas = ROOT.TCanvas("c", "c", 800, 800)
    #canvas.SetTopMargin(0.08)
    #canvas.SetBottomMargin(0.1)
    #canvas.SetLeftMargin(0.25)
    #canvas.SetRightMargin(0.05)
    #canvas.SetFillStyle(4000) # transparency?
    #canvas.SetGrid(1, 0)
    #canvas.SetTickx(1)


    #xMin, xMax = -5, 5
    #xTitle = "#sigma_{syst.}(m_{h}) (MeV)"

    #ref = "IDEA_STAT"
    #best_ref, unc_ref = getUnc(ref, "mass")
    #params = ["IDEA_ISR", "IDEA_BES", "IDEA_SQRTS", "IDEA_MUSCALE", "IDEA_ISR_BES_SQRTS_MUSCALE"]
    #labels = ["ISR (conservative)", "BES 1%", "#sqrt{s} #pm 2 MeV", "Muon scale (~10^{-5})", "#splitline{Syst. combined}{(BES 1%)}"]
    
    #n_params = len(params)
    #h_pulls = ROOT.TH2F("pulls", "pulls", 6, xMin, xMax, n_params, 0, n_params)
    #g_pulls = ROOT.TGraphAsymmErrors(n_params)

    #i = n_params
    #for p in xrange(n_params):

    #    i -= 1
    #    best, unc = getUnc(params[p], "mass")
    #    unc = math.sqrt(unc**2 - unc_ref**2)
    #    g_pulls.SetPoint(i, 0, float(i) + 0.5)
    #    g_pulls.SetPointError(i, unc, unc, 0., 0.)
    #    h_pulls.GetYaxis().SetBinLabel(i + 1, labels[p])
    #   


    #h_pulls.GetXaxis().SetTitleSize(0.04)
    #h_pulls.GetXaxis().SetLabelSize(0.03)
    #h_pulls.GetXaxis().SetTitle(xTitle)
    #h_pulls.GetXaxis().SetTitleOffset(1)
    #h_pulls.GetYaxis().SetLabelSize(0.045)
    #h_pulls.GetYaxis().SetTickLength(0)
    #h_pulls.GetYaxis().LabelsOption('v')
    #h_pulls.SetNdivisions(506, 'XYZ')
    #h_pulls.Draw("HIST")
    

    #g_pulls.SetMarkerSize(0.8)
    #g_pulls.SetMarkerStyle(20)
    #g_pulls.SetLineWidth(2)
    #g_pulls.Draw('P SAME')
    
    
    #latex = ROOT.TLatex()
    #latex.SetNDC()
    #latex.SetTextSize(0.045)
    #latex.SetTextColor(1)
    #latex.SetTextFont(42)
    #latex.SetTextAlign(30) # 0 special vertical aligment with subscripts
    #latex.DrawLatex(0.95, 0.925, "#sqrt{s} = 240 GeV,  10 ab^{#minus1}")

    #latex.SetTextAlign(13)
    #latex.SetTextFont(42)
    #latex.SetTextSize(0.045)
    #latex.DrawLatex(0.25, 0.96, "#bf{FCCee} #scale[0.7]{#it{Simulation}}")

    #    
    #canvas.SaveAs("%s/mass_breakDown.png" % outDir)
    #canvas.SaveAs("%s/mass_breakDown.pdf" % outDir)   
    #del canvas, g_pulls, h_pulls
    

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

    combineDir = "combine/run"
    outDir = "/eos/user/j/jaeyserm/www/FCCee/ZH_mass_xsec/combine/"
    doSyst=True
    
    suffix=""
    if not doSyst:
        suffix = "_stat"
    
    ############### BDT
    
    if True:
    
        tag = "BDTScore" # BDT baseline baseline_no_costhetamiss BDTScore
        #rMin, rMax = 0.96, 1.04
        rMin, rMax = 0.98, 1.02
        npoints = 50
        #flavor = "ee"
        flavor = "mumu"
        #flavor = "combine"
        #combineOptions = "--setParameters bkg_mumu_norm=0.1,bkg_ee_norm=0.001"
        combineOptions = ""
        
        combineDir = "combine/run_binned_BDTScore_{flavor}/".format(flavor=flavor)
        outDir = "/eos/user/l/lia/FCCee/MidTerm/{flavor}/ZH_mass_xsec/combine_binned_BDTScore/".format(flavor=flavor)
        if not os.path.exists(outDir):
            os.makedirs(outDir)
        if flavor == "mumu":
            label = "#mu^{#plus}#mu^{#minus}"
        elif flavor == "ee":
            label = "e^{#plus}e^{#minus}"
        elif flavor == "combine":
            label = "#mu^{#plus}#mu^{#minus} + e^{#plus}e^{#minus}"
        
        if flavor == "combine":
           combineCards(combineDir, ["combine/run_binned_BDTScore_mumu/datacard_binned_mumu.txt", "combine/run_binned_BDTScore_ee/datacard_binned_ee.txt"])
 
        
        
        suffix = "_STAT"

        if flavor == "mumu":
            combineOptions = "--freezeParameters=MUSCALE,BES,SQRTS"
        elif flavor == "ee":
            combineOptions = "--freezeParameters=ELSCALE,BES,SQRTS"
        elif flavor == "combine":
            combineOptions = "--freezeParameters=MUSCALE,ELSCALE,BES,SQRTS"
        
        doFit_xsec("%s" % (combineDir), rMin=rMin, rMax=rMax, npoints=npoints, combineOptions=combineOptions)
        analyzeXsec("%s" % (combineDir), "%s" % (outDir), label=label, xMin=rMin, xMax=rMax)

    
        if flavor == "mumu":
            suffix = "_MUSCALE"
        elif flavor == "ee":
            suffix = "_ELSCALE"
        elif flavor == "combine":
            suffix = "_MUSCALE"
            combineOptions = "--freezeParameters=BES,SQRTS,ELSCALE"
            doFit_xsec("%s" % (combineDir), rMin=rMin, rMax=rMax, npoints=npoints, combineOptions=combineOptions)
            analyzeXsec("%s" % (combineDir), "%s" % (outDir), label=label, xMin=rMin, xMax=rMax)
            suffix = "_ELSCALE"
            combineOptions = "--freezeParameters=BES,SQRTS,MUSCALE"
            doFit_xsec("%s" % (combineDir), rMin=rMin, rMax=rMax, npoints=npoints, combineOptions=combineOptions)
            analyzeXsec("%s" % (combineDir), "%s" % (outDir), label=label, xMin=rMin, xMax=rMax)

        if not flavor == "combine":
            combineOptions = "--freezeParameters=BES,SQRTS"
            doFit_xsec("%s" % (combineDir), rMin=rMin, rMax=rMax, npoints=npoints, combineOptions=combineOptions)
            analyzeXsec("%s" % (combineDir), "%s" % (outDir), label=label, xMin=rMin, xMax=rMax)

        suffix = "_BES"
        if flavor == "mumu":
            combineOptions = "--freezeParameters=MUSCALE,SQRTS"
        elif flavor == "ee":
            combineOptions = "--freezeParameters=ELSCALE,SQRTS"
        elif flavor == "combine":
            combineOptions = "--freezeParameters=MUSCALE,ELSCALE,SQRTS"
        doFit_xsec("%s" % (combineDir), rMin=rMin, rMax=rMax, npoints=npoints, combineOptions=combineOptions)
        analyzeXsec("%s" % (combineDir), "%s" % (outDir), label=label, xMin=rMin, xMax=rMax)

        suffix = "_SQRTS"
        if flavor == "mumu":
            combineOptions = "--freezeParameters=MUSCALE,BES"
        elif flavor == "ee":
            combineOptions = "--freezeParameters=ELSCALE,BES"
        elif flavor == "combine":
            combineOptions = "--freezeParameters=MUSCALE,ELSCALE,BES"
        #doFitDiagnostics_xsec("%s" % (combineDir), rMin=rMin, rMax=rMax, combineOptions=combineOptions)
        doFit_xsec("%s" % (combineDir), rMin=rMin, rMax=rMax, npoints=npoints, combineOptions=combineOptions)
        analyzeXsec("%s" % (combineDir), "%s" % (outDir), label=label, xMin=rMin, xMax=rMax)
        
        if flavor == "mumu":
            suffix = "_BES_SQRTS_MUSCALE"
        elif flavor == "ee":
            suffix = "_BES_SQRTS_ELSCALE" 
        elif flavor == "combine":
            suffix = "_BES_SQRTS_MUSCALE_ELSCALE"
        combineOptions = ""
        doFit_xsec("%s" % (combineDir), rMin=rMin, rMax=rMax, npoints=npoints, combineOptions=combineOptions)
        analyzeXsec("%s" % (combineDir), "%s" % (outDir), label=label, xMin=rMin, xMax=rMax)
        #doFitDiagnostics_xsec("%s" % (combineDir), rMin=rMin, rMax=rMax, combineOptions=combineOptions)
        # systematics breakdown plot 
        runDir = outDir 
        breakDown()

        # combine STAT and STAT+SYST plots
        if flavor == "mumu":
            plotMultiple_xsec(["STAT", "BES_SQRTS_MUSCALE"], ["#mu^{+}#mu^{-} Stat. only", "#mu^{+}#mu^{-} Stat.+Syst."], [outDir,outDir], outDir)
        elif flavor == "ee":
            plotMultiple_xsec(["STAT", "BES_SQRTS_ELSCALE"], ["e^{+}e^{-} Stat. only", "e^{+}e^{-} Stat.+Syst."], [outDir,outDir], outDir)
        elif flavor == "combine":
            plotMultiple_xsec(["STAT", "BES_SQRTS_MUSCALE_ELSCALE"], ["l^{+}l^{-} Stat. only", "l^{+}l^{-} Stat.+Syst."], [outDir,outDir], outDir)
            plotMultiple_xsec(["STAT", "STAT", "STAT"], 
                              ["#mu^{+}#mu^{-} Stat. only", "e^{+}e^{-} Stat. Only", "#mu^{+}#mu^{-} + e^{+}e^{-} Stat. Only"], 
                              ["/eos/user/l/lia/FCCee/MidTerm/mumu/ZH_mass_xsec/combine_binned_BDTScore/",
                               "/eos/user/l/lia/FCCee/MidTerm/ee/ZH_mass_xsec/combine_binned_BDTScore/",
                               "/eos/user/l/lia/FCCee/MidTerm/combine/ZH_mass_xsec/combine_binned_BDTScore/"],
                              outDir,
                              name="_STAT")
            plotMultiple_xsec(["BES_SQRTS_MUSCALE", "BES_SQRTS_ELSCALE", "BES_SQRTS_MUSCALE_ELSCALE"], 
                              ["#mu^{+}#mu^{-} Stat.+Syst.", "e^{+}e^{-} Stat.+Syst.", "#mu^{+}#mu^{-} + e^{+}e^{-} Stat.+Syst."], 
                              ["/eos/user/l/lia/FCCee/MidTerm/mumu/ZH_mass_xsec/combine_binned_BDTScore/",
                               "/eos/user/l/lia/FCCee/MidTerm/ee/ZH_mass_xsec/combine_binned_BDTScore/",
                               "/eos/user/l/lia/FCCee/MidTerm/combine/ZH_mass_xsec/combine_binned_BDTScore/"],
                              outDir,
                              name="_SYST") 
        #systematics breakdown plot
        


        #combineDir = "combine/run_binned_{tag}_ee/".format(tag=tag)
        #outDir = "/eos/user/l/lia/FCCee/MidTerm/ee/ZH_mass_xsec/combine_binned_{tag}/".format(tag=tag)
        #label = "e^{#plus}e^{#minus}"
        #doFit_xsec(combineDir, rMin=rMin, rMax=rMax, npoints=50, combineOptions=combineOptions)
        #analyzeXsec(combineDir, outDir, label=label, xMin=rMin, xMax=rMax)
        
        
        #combineDir = "combine/run_binned_{tag}_combined/".format(tag=tag)
        #outDir = "/eos/user/l/lia/FCCee/MidTerm/Combined/ZH_mass_xsec/combine_binned_{tag}/".format(tag=tag)
        #combineCards(combineDir, ["combine/run_binned_{tag}_mumu/datacard_binned_mumu.txt".format(tag=tag), "combine/run_binned_{tag}_ee/datacard_binned_ee.txt".format(tag=tag)])
        #doFit_xsec(combineDir, rMin=rMin, rMax=rMax, npoints=50, combineOptions=combineOptions)
        #analyzeXsec(combineDir, outDir, label=label, xMin=rMin, xMax=rMax)
        
        #plotMultiple_xsec(["combine/run_binned_{tag}_mumu/".format(tag=tag), "combine/run_binned_{tag}_ee/".format(tag=tag), "combine/run_binned_{tag}_combined/".format(tag=tag)], ["#mu^{#plus}#mu^{#minus}", "e^{#plus}e^{#minus}", "#mu^{#plus}#mu^{#minus}+e^{#plus}e^{#minus}"], "%s/summary"%outDir, xMin=rMin, xMax=rMax)
        
        
        #rMin, rMax = 0.98, 1.02
        #outDir = "/eos/user/j/jaeyserm/www/FCCee/ZH_mass_xsec/combine_binned_BDT/"
        #plotMultiple_xsec(["combine/run_binned_BDT_combined/", "combine/run_binned_baseline_combined/", "combine/run_binned_baseline_no_costhetamiss_combined/"], ["BDT", "Baseline (with cos(#theta_{miss}))", "Baseline (without cos(#theta_{miss}))"], "%s/summary"%outDir, xMin=rMin, xMax=rMax)
