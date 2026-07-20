import sys
import argparse
import re
import os
import math
import ROOT

from re import search
from ROOT import *
#from ROOT import TCanvas, TFile, gDirectory
#from ROOT import gSystem
#from ROOT import RooFit, RooRealVar, RooCurve, RooCBShape
# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ----
if __name__ == "__main__":

	if len(sys.argv) != 5:
		print ("usage:\n")
		print ("python ",sys.argv[0], " path_to_files", " histogram name", " fit function", "channel", "\n")
		print ("For example: python fit.py outputs/FCCee/higgs/mH-recoil/mumu_IDEAtrkCov leptonic_recoil_m_zoom6 DCB ALL\n")
		print ("Fit function:")
		print ("\tlandau \t\tfor landau distribution")
		print ("\tGaussian \tfor Gaussian distribution")
		print ("\tBW \t\tfor Breit-Wigner distribution")
		print ("\tCBR \t\tfor Crystal Ball distribution with tail on hte right bande")
		print ("\tCBL \t\tfor Crystal Ball distribution with tail on hte left bande")
		print ("\tDCB \t\tfor Double Sided Crystal Ball distribution")
		print ("Channels:")
		print ("\tZH\tZZ\tWW\tALL(ZH+ZZ+WW)")
		sys.exit(0)

	channel = sys.argv[4]
	func = sys.argv[3]
	histName = sys.argv[2]
	baseDir = sys.argv[1]

	baseDir = os.path.join(baseDir, "")
	
	print("\n--->Will apply fit function" + func + "\n")
	print("\n--->Working at " + baseDir + "\n")
	
	rootDir = {}
	rootDir['ZH'] = os.path.join(baseDir, "wzp6_ee_mumuH_ecm240_sel_Baseline_histo.root")
	rootDir['ZZ'] = os.path.join(baseDir, "p8_ee_ZZ_ecm240_sel_Baseline_histo.root")
	rootDir['WW'] = os.path.join(baseDir, "p8_ee_WW_ecm240_sel_Baseline_histo.root")
	print("------>\n")
	#histName = "leptonic_recoil_m_zoom6"
	
	ROOT.gROOT.SetBatch()
	ROOT.gSystem.Load( 'libRooFit' )

	f = {}
	for key in rootDir:
		print("------>Loading " + rootDir[key] + "\n")
		f[key] = ROOT.TFile.Open(rootDir[key])
	
	histo = {}
	for key in f:
		print("--------->Loading " + histName + "\n")
		histo[key] = f[key].Get(histName)
		print("--------->" + str(histo[key].Integral()))
	print("--------->Channel: " + channel + "\n")

	sum_histo = ROOT.TH1D() 
	if (channel == 'ALL'):
		sum_histo = histo['ZZ'].Clone()
		for key in histo:
			if key != 'ZZ':
				sum_histo.Add(histo[key])
	else:
		sum_histo = histo[channel].Clone()

	x = ROOT.RooRealVar("m leptonic recoil", "m leptonic recoil", sum_histo.GetXaxis().GetXmin(), sum_histo.GetXaxis().GetXmax())
	peak = sum_histo.GetXaxis().GetBinCenter(sum_histo.GetMaximumBin())
	mean = ROOT.RooRealVar("mean", "mean", peak-1.0, peak - 5.0, peak + 5.0)
	sigma = ROOT.RooRealVar("sigma", "width", 0.3, 0.1, 5.0)
	alphaR = ROOT.RooRealVar("alpha", "alpha of Crystal Ball", -0.3, -5.0, 0.0)
	alphaL = ROOT.RooRealVar("alpha", "alpha of Crystal Ball", 0.3, 0.0, 5.0)
	n = ROOT.RooRealVar("n", "n of Crystal Ball", 5.0, 0.0, 100.0)
	mean2 = ROOT.RooRealVar("mean2", "mean of gaussian", peak, peak -5.0, peak + 5.0)
	sigma2 = ROOT.RooRealVar("sigma2", "width of gaussian", 0.3, 0.0, 5.0)

	alpha_L = ROOT.RooRealVar("alphaL", "alpha of Crystal Ball", 5, 0.3, 5.0)
	n_L = ROOT.RooRealVar("nL", "n of Crystal Ball", 5, 0.0, 200.0)
	alpha_H = ROOT.RooRealVar("alphaH", "alpha of Crystal Ball", 5, 0.3, 5.0)
	n_H = ROOT.RooRealVar("nH", "n of Crystal Ball", 5, 0.0, 200.0)


	if (channel == 'ALL'):
		nsig_init = histo['ZZ'].Integral()
		nbkg_init = 0.0
		nmax = 0.0
		for key in histo:
			nmax += histo[key].Integral()
			if key != 'ZZ':
				nbkg_init += histo[key].Integral()
	else:
		nsig_init = 0.0
		nbkg_init = 0.0
		nmax = histo[channel].Integral()
		
	nsig  = ROOT.RooRealVar("nsig", "number of signal events", nsig_init*7200000.0, 0., 1.2*nmax*7200000.0)
	nbkg  = ROOT.RooRealVar("nbkg", "number of background events", nbkg_init*7200000.0, 0, 1.2*nmax*7200000.0)

	if (func == 'CBR'): 
		signal = ROOT.RooCBShape("Crystal Ball", "Crystal Ball PDF", x, mean, sigma, alphaR, n)
	elif (func == 'CBL'):
		signal = ROOT.RooCBShape("Crystal Ball", "Crystal Ball PDF", x, mean, sigma, alphaL, n)
	elif (func == 'BW'):
		signal = ROOT.RooBreitWigner("BreitWigner", "RooBreitWigner PDF", x, mean, sigma)
	elif (func == 'landau'):
		signal = ROOT.RooLandau("Landau", "Landau PDF", x, mean, sigma)
	elif (func == 'Gaussian'):
		signal = ROOT.RooGaussian("Gaussian", "Gaussian PDF", x, mean, sigma)
	elif (func == 'DCB'):
		signal = ROOT.RooCrystalBall("Double Crystal Ball", "Double Crystal Ball PDF", x, mean, sigma, alpha_L, n_L,alpha_H, n_H)
	elif (func == 'BWXGauss'):
		x.setBins(sum_histo.GetNbinsX(), "cache");
		#x.setBins(10000, "cache")
		signal1 = ROOT.RooBreitWigner("BreitWigner", "RooBreitWigner PDF", x, mean, sigma)
		signal2 = ROOT.RooGaussian("Gaussian", "Gaussian PDF", x, mean2, sigma2)
		signal = ROOT.RooFFTConvPdf("BWXGauss","Breit-Wigner (X) gauss",x ,signal1, signal2)
	else:
		print('fit function ' + func + ' is not supported. Please implment it!')
		exit(1)
	
	#c = ROOT.RooRealVar("c", "constant of Exponential", -0.3, -0.4, 0.0)
	#p0 = ROOT.RooRealVar("p0", "p0 of polynomial", -5.0, 5.0)
	#p1 = ROOT.RooRealVar("p1", "p1 of polynomial", -2.0, 2.0)
	#p2 = ROOT.RooRealVar("p2", "p2 of polynomial", -3.0, 3.0)
	c = ROOT.RooRealVar("c", "constant of Exponential", -0.00901)
	p0 = ROOT.RooRealVar("p0", "p0 of polynomial", 3.967)
	p1 = ROOT.RooRealVar("p1", "p1 of polynomial", -0.063757)
	p2 = ROOT.RooRealVar("p2", "p2 of polynomial", 0.00010023)
	p3 = ROOT.RooRealVar("p3", "p3 of polynomial", 0.0000027478)
	p4 = ROOT.RooRealVar("p4", "p4 of polynomial", -0.000000011696)

	#pol2 = ROOT.RooPolynomial("Pol2", "Pol2", x, ROOT.RooArgList(p0, p1, p2))
	#exp =  ROOT.RooExponential("Exp", "Exp", x, c)
	#fracPol2 = ROOT.RooRealVar("fracPol2", "pol2 fraction", 0.443)
	#background = ROOT.RooExponential("Exponential", "Exponential", x, c)
	#background = ROOT.RooPolynomial("Pol1", "Pol1", x, ROOT.RooArgList(p0, p1))
	background = ROOT.RooPolynomial("Pol2", "Pol2", x, ROOT.RooArgList(p0, p1, p2, p3, p4))
	#background = ROOT.RooAddPdf("Pol2_Exp", "Pol2_Exp",ROOT.RooArgList(pol2,exp),ROOT.RooArgList(fracPol2))

	xframe = x.frame(ROOT.RooFit.Title(func + " + Pol2_Exp pdf with data"))  # RooPlot
	
	
	hist = ROOT.RooDataHist("data", "data", ROOT.RooArgList(x), sum_histo, 7200000.0)
	hist.plotOn(xframe, ROOT.RooFit.Name("Data_temp"), ROOT.RooFit.DrawOption("Z"), ROOT.RooFit.MarkerSize(0.2))


	x.setRange("SBL",110,120)
	x.setRange("SBR",140,150)
	#if (channel == "ALL"):
	#	fsig = ROOT.RooRealVar("fsig", "signal fraction", 0.5, 0., 1.)
	#else:
	#	fsig = ROOT.RooRealVar("fsig", "signal fraction", 1., 1., 1.)
	fsig = ROOT.RooRealVar("fsig", "signal fraction", 0.5, 0., 1.)
	model = ROOT.RooAddPdf("total_pdf","total_pdf",ROOT.RooArgList(signal,background),ROOT.RooArgList(nsig, nbkg))
	#model = ROOT.RooAddPdf("total_pdf","total_pdf",ROOT.RooArgList(background),ROOT.RooArgList(nbkg))
	#model = ROOT.RooAddPdf("total_pdf","total_pdf",ROOT.RooArgList(signal,background),ROOT.RooArgList(fsig))
	#4
	#fit_result = model.fitTo(hist, RooFit.Minos(ROOT.kTRUE), ROOT.RooFit.SumW2Error(ROOT.kTRUE), ROOT.RooFit.Save(True),ROOT.RooFit.Extended(True),ROOT.RooFit.Optimize(False),ROOT.RooFit.Offset(True),ROOT.RooFit.Minimizer("Minuit2","mgrad"),ROOT.RooFit.Strategy(2))
	#5
	fit_result = model.fitTo(hist, RooFit.Minos(ROOT.kTRUE), ROOT.RooFit.SumW2Error(ROOT.kFALSE), ROOT.RooFit.Save(True),ROOT.RooFit.Extended(True),ROOT.RooFit.Optimize(False),ROOT.RooFit.Offset(True),ROOT.RooFit.Minimizer("Minuit2","mgrad"),ROOT.RooFit.Strategy(2))
	
	model.plotOn(xframe, ROOT.RooFit.Name("SB"), ROOT.RooFit.LineColor(ROOT.kOrange))
	hist.plotOn(xframe, ROOT.RooFit.Name("Data"), ROOT.RooFit.DrawOption("Z"), ROOT.RooFit.MarkerSize(0.2))
	ndf =  fit_result.floatParsFinal().getSize()
	chi2 = xframe.chiSquare("SB", "Data", ndf)
	
	ras_bkg = ROOT.RooArgSet(background)
	ras_sig = ROOT.RooArgSet(signal)
	model.plotOn(xframe, ROOT.RooFit.Name("S"), ROOT.RooFit.Components(ras_sig), ROOT.RooFit.LineStyle(ROOT.kDashed), ROOT.RooFit.LineColor(ROOT.kRed))
	model.plotOn(xframe, ROOT.RooFit.Name("B"), ROOT.RooFit.Components(ras_bkg), ROOT.RooFit.LineStyle(ROOT.kDashed), ROOT.RooFit.LineColor(ROOT.kGreen))

	mean.Print()
	sigma.Print()
	alphaL.Print()
	alphaR.Print()
	n.Print()
	c.Print()
	nsig.Print()
	nbkg.Print()
	alpha_L.Print()
	n_L.Print()
	alpha_H.Print()
	n_H.Print()
	p0.Print()
	p1.Print()
	p2.Print()

	# Draw all frames on a canvas
	c1 = TCanvas('c1','',800,800)
	padFrac=0.45;
	uppPad=TPad("uppPad","",0,padFrac,1,1);
	lowPad=TPad("lowPad","",0,0,1,padFrac);
	uppPad.SetBottomMargin(0.01);
	lowPad.SetTopMargin(0.01)
	lowPad.SetBottomMargin(0.3);
	uppPad.Draw();
	lowPad.SetFillColor(0);
	lowPad.Draw();
			   
	uppPad.cd()
	model.paramOn(xframe, ROOT.RooFit.Layout(0.60), ROOT.RooFit.Format("NEU",ROOT.RooFit.AutoPrecision(2)));
	xframe.SetYTitle('Events / (' + str(sum_histo.GetBinWidth(1)) + ' GeV)')
	xframe.GetYaxis().SetTitleFont(43)
	xframe.GetYaxis().SetTitleSize(26)
	xframe.Draw();
	t = TLatex();
	t.SetNDC();
	t.SetTextFont(43);
	t.SetTextSize(26);
	t.DrawLatex(0.70,0.37, ('#chi^{{2}}/NDF: {0:0.2f}'.format(chi2)) )
	if (channel == 'ALL'):
		t.DrawLatex(0.15,0.80, " ")
	else:
		t.DrawLatex(0.15,0.80, channel )
	t.DrawLatex(0.15,0.70, 'L = 7.2 ab^{-1}' )
	leg = ROOT.TLegend(0.7,0.15,1.0,0.35,baseDir.split('/')[-2])
	leg.AddEntry("Data","Data")
	leg.AddEntry("SB","S + B Fit")
	leg.AddEntry("S","Sig. Fit")
	leg.AddEntry("B","Bkg. Fit")
	leg.Draw();
	lowPad.cd()
	#dataHist  = xframe.getHist("Data_temp")
	#curve1 = xframe.getObject(4)  # 1 is index in the list of RooPlot items (see printout from massplot->Print("V")  
	#curve2 = xframe.getObject(5)
	#hresid1 =  dataHist.makePullHist(curve1,True);
	#hresid2 =  dataHist.makePullHist(curve2,True);
	hpull = xframe.pullHist("Data", "SB");
	xframe2 = x.frame() ;
	#xframe2.addPlotable(hresid1,"P")
	#xframe2.addPlotable(hresid2,"P")
	xframe2.SetTitle('');
	xframe2.GetYaxis().SetRangeUser(-10,10);
	xframe2.GetXaxis().SetTitleOffset(3.0)
	xframe2.GetYaxis().SetTitleFont(43)
	xframe2.GetYaxis().SetTitleSize(26)
	xframe2.GetXaxis().SetTitleFont(43)
	xframe2.GetXaxis().SetTitleSize(26)
	
	if 'recoil' in histName: 
		xframe2.SetXTitle('M_{leptonic recoil} [GeV]')
	elif 'mz' in histName:
		xframe2.SetXTitle('M_{Z} [GeV]')
	else:
		xframe2.SetXTitle(sum_histo.GetXaxis().GetTitle())

	xframe2.SetYTitle('#frac{Data-Fit}{Error}');
	hpull.SetMarkerSize(0.5)
	xframe2.addPlotable(hpull, 'Z p')
	xframe2.Draw();
	flat = ROOT.TF1("flat","0",0,200);
	flat.SetLineColor(kRed)
	flat.Draw('same')
	xframe2.Draw("same");
	
	
	
	if not os.path.exists(os.path.join(baseDir,"fitResults")):
		os.system('mkdir ' + os.path.join(baseDir,"fitResults"))
	c1.SaveAs(os.path.join(baseDir,"fitResults",baseDir.split('/')[-2] + "_" + channel + "_" + histName + "_" + str(int(sum_histo.GetXaxis().GetXmin())) + "_" +  str(int(sum_histo.GetXaxis().GetXmax())) + "_" + func + "_fit_result.pdf"))

	print("--->Adjust the parameters if needed")
