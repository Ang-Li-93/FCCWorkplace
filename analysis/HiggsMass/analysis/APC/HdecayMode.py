import os
import ROOT
import matplotlib.pyplot as plt
from tempfile import TemporaryFile
import numpy as np

print ("----> Load cxx analyzers from libFCCAnalyses... ",)
ROOT.gSystem.Load("libFCCAnalyses")
ROOT.gSystem.Load("libFCCAnalysesHiggs")
ROOT.gErrorIgnoreLevel = ROOT.kFatal
#Is this still needed?? 01/04/2022 still to be the case
_fcc  = ROOT.dummyLoader
_higgs  = ROOT.dummyLoaderHiggs

ROOT.gInterpreter.ProcessLine('''
  TMVA::Experimental::RBDT<> bdt("ZH_Recoil_BDT", "/eos/user/l/lia/FCCee/NewWorkFlow/BDT/xgb_bdt.root");
  computeModel1 = TMVA::Experimental::Compute<9, float>(bdt);
''')

path = "/eos/user/l/lia/FCCee/NewWorkFlow/BDT_analysis_samples/wzp6_ee_mumuH_ecm240"
path_or = "/eos/experiment/fcc/ee/generation/DelphesEvents/spring2021/IDEA/wzp6_ee_mumuH_ecm240/"
cuts = ["true", 
        "leps_no >= 1 && leps_sel_iso.size() > 0",
        "leps_no >= 2 && abs(Sum(leps_q)) < leps_q.size()",
        "zll_m > 73 && zll_m < 120",
        "zll_p > 5",
        "zll_recoil_m < 140 && zll_recoil_m > 120",
        "BDTscore > 0.3"
        ]
pid_map = {
            "cc":4,
            "bb":5,
            "mumu":13,
            "tautau":15,
            "gg":21,
            "gaga":22,
            "ZZ":23,
            "WW":24,
          }
decays = ["cc","bb","mumu","tautau","gg","gaga","ZZ","WW"]

def makePlot(g_pulls, h_pulls, avg=0):

    canvas = ROOT.TCanvas("c", "c", 800, 800)
    canvas.SetTopMargin(0.08)
    canvas.SetBottomMargin(0.1)
    canvas.SetLeftMargin(0.15)
    canvas.SetRightMargin(0.05)
    canvas.SetFillStyle(4000) # transparency?
    canvas.SetGrid(1, 0)
    canvas.SetTickx(1)

    xTitle = "Selection efficiency Z(#mu^{#plus}#mu^{#minus})H  (%)"

    h_pulls.GetXaxis().SetTitleSize(0.04)
    h_pulls.GetXaxis().SetLabelSize(0.035)
    h_pulls.GetXaxis().SetTitle(xTitle)
    h_pulls.GetXaxis().SetTitleOffset(1)
    h_pulls.GetYaxis().SetLabelSize(0.055)
    h_pulls.GetYaxis().SetTickLength(0)
    h_pulls.GetYaxis().LabelsOption('v')
    h_pulls.SetNdivisions(506, 'XYZ')
    h_pulls.Draw("HIST 0")
   

    maxx = 9
    line = ROOT.TLine(avg, 0, avg, maxx)
    line.SetLineColor(ROOT.kGray)
    line.SetLineWidth(2)
    #line.Draw("SAME")
    

    
    shade = ROOT.TGraph()
    shade.SetPoint(0, avg*0.999, 0)
    shade.SetPoint(1, avg*1.001, 0)
    shade.SetPoint(2, avg*1.001, maxx)
    shade.SetPoint(3, avg*0.999, maxx)
    shade.SetPoint(4, avg*0.999, 0)
    #shade.SetFillStyle(3013)
    shade.SetFillColor(16)
    shade.SetFillColorAlpha(16, 0.35);
    shade.Draw("SAME F")

    g_pulls.SetMarkerSize(1.2)
    g_pulls.SetMarkerStyle(20)
    g_pulls.SetLineWidth(2)
    g_pulls.Draw('P0 SAME')
    
    
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
    latex.DrawLatex(0.15, 0.96, "#bf{FCC-ee} #scale[0.7]{#it{Simulation}}")
    
    latex.SetTextAlign(13)
    latex.SetTextFont(42)
    latex.SetTextSize(0.045)
    latex.SetTextColor(ROOT.kGray+1)
    latex.DrawLatex(0.2, 0.17, "avg. #pm 0.1 %")
    
    canvas.SaveAs("/eos/user/l/lia/FCCee/ZH_mass_xsec/plots_mumu/decay_mode_independence.png" % flavor)
    canvas.SaveAs("/eos/user/l/lia/FCCee/ZH_mass_xsec/plots_mumu/decay_mode_independence.pdf" % flavor)    
 
if __name__ == "__main__":
  df_decays = {}
  Eff = []
  Err = []
  Eff_avg = []
  Err_avg = [] 
  N = []
  N_err = []
  xsec=0.0067643
  Lumi = 5000000.
  N_entries = 1000000
  #Read the root file
  df = ROOT.RDataFrame("events", os.path.join(path_or,"*.root"))
  df = df.Alias("Lepton0", "AllMuon#0.index")
  df = df.Alias("MCRecoAssociations0", "MCRecoAssociations#0.index")
  df = df.Alias("MCRecoAssociations1", "MCRecoAssociations#1.index")
  df = df.Alias("Particle0", "Particle#0.index")
  df = df.Alias("Particle1", "Particle#1.index")
  #df = df.Alias("Photon0", "Photon#0.index")

  # Missing ET
  #df = df.Define("cosTheta_miss", "HiggsTools::get_cosTheta(MissingET)") 
  # all leptons (bare)
  df = df.Define("leps_all", "FCCAnalyses::ReconstructedParticle::get(Lepton0, ReconstructedParticles)")
  #df = df.Define("leps_all_p", "FCCAnalyses::ReconstructedParticle::get_p(leps_all)")
  #df = df.Define("leps_all_theta", "FCCAnalyses::ReconstructedParticle::get_theta(leps_all)")
  #df = df.Define("leps_all_phi", "FCCAnalyses::ReconstructedParticle::get_phi(leps_all)")
  #df = df.Define("leps_all_q", "FCCAnalyses::ReconstructedParticle::get_charge(leps_all)")
  #df = df.Define("leps_all_no", "FCCAnalyses::ReconstructedParticle::get_n(leps_all)")
  df = df.Define("leps_all_iso", "HiggsTools::coneIsolation(0.01, 0.5)(leps_all, ReconstructedParticles)") 
  #df = df.Define("leps_all_p_gen", "HiggsTools::gen_p_from_reco(leps_all, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
  df = df.Alias("leps", "leps_all")  

  df = df.Define("leps_p", "FCCAnalyses::ReconstructedParticle::get_p(leps)")
  df = df.Define("leps_theta", "FCCAnalyses::ReconstructedParticle::get_theta(leps)")
  df = df.Define("leps_phi", "FCCAnalyses::ReconstructedParticle::get_phi(leps)")
  df = df.Define("leps_q", "FCCAnalyses::ReconstructedParticle::get_charge(leps)")
  df = df.Define("leps_no", "FCCAnalyses::ReconstructedParticle::get_n(leps)")
  df = df.Define("leps_iso", "HiggsTools::coneIsolation(0.01, 0.5)(leps, ReconstructedParticles)")
  df = df.Define("leps_sel_iso", "HiggsTools::sel_isol(0.25)(leps, leps_iso)")
  # momentum resolution
  #df = df.Define("leps_all_reso_p", "HiggsTools::leptonResolution_p(leps_all, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
  #df = df.Define("leps_reso_p", "HiggsTools::leptonResolution_p(leps, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
  # track Higgs decays
  df = df.Define("higgs_MC", "HiggsTools::gen_sel_pdgIDInt(25,false)(Particle)")
  df = df.Define("daughter_higgs", "HiggsTools::gen_decay_list(higgs_MC, Particle, Particle1)")
  df = df.Define("daughter_higgs_collapsed", "daughter_higgs.size()>1 ? ((abs(daughter_higgs[0])+abs(daughter_higgs[1]))*0.5) : -1000 ")
  # build the Z resonance and recoil using MC information from the selected muons
  #df = df.Define("zed_leptonic_MC", "HiggsTools::resonanceZBuilder2(91, true)(leps, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
  #df = df.Define("zed_leptonic_m_MC", "FCCAnalyses::ReconstructedParticle::get_mass(zed_leptonic_MC)")
  #df = df.Define("zed_leptonic_recoil_MC",  "FCCAnalyses::ReconstructedParticle::recoilBuilder(240)(zed_leptonic_MC)")
  #df = df.Define("zed_leptonic_recoil_m_MC", "FCCAnalyses::ReconstructedParticle::get_mass(zed_leptonic_recoil_MC)")

  df = df.Define("weight", f"{xsec*Lumi/N_entries}")
  #y = h.GetBinContent(15+1)
  #########
  ### CUT 1: at least a lepton
  #########
  print("--> Counting pre-selection")
  for cur_cut in cuts[:3]:
    print(f"---->Working on cut {cur_cut}")
    N_tmp = []
    N_err_tmp = []
    df = df.Filter(cur_cut)
    for cur_decay in decays:
      print(f"---->Working on decay channel {cur_decay}")
      N_tmp.append(df.Filter(f"daughter_higgs_collapsed == {pid_map[cur_decay]}" ).Sum("weight").GetValue())
      N_err_tmp.append(df.Filter(f"daughter_higgs_collapsed == {pid_map[cur_decay]}" ).Sum("weight").GetValue()**0.5)
    N.append(N_tmp)
    N_err.append(N_err_tmp)

  df = df.Define("zbuilder_result", "HiggsTools::resonanceBuilder_mass_recoil(91.2, 125, 0, 240, false)(leps, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0,     Particle1)")
  df = df.Define("zll", "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result[0]}") # the Z
  df = df.Define("zll_leps", "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result[1],zbuilder_result[2]}") # the leptons
  df = df.Define("zll_m", "FCCAnalyses::ReconstructedParticle::get_mass(zll)[0]")
  df = df.Define("zll_p", "FCCAnalyses::ReconstructedParticle::get_p(zll)[0]")
  df = df.Define("zll_theta", "FCCAnalyses::ReconstructedParticle::get_theta(zll)[0]")
  #df = df.Define("zll_phi", "FCCAnalyses::ReconstructedParticle::get_phi(zll)[0]")

  # recoil
  df = df.Define("zll_recoil", "FCCAnalyses::ReconstructedParticle::recoilBuilder(240)(zll)")
  df = df.Define("zll_recoil_m", "FCCAnalyses::ReconstructedParticle::get_mass(zll_recoil)[0]")
  # Z leptons informations
  df = df.Define("sorted_zll_leptons",  "HiggsTools::sort_greater_p(zll_leps)")
  df = df.Define("sorted_zll_leptons_p",     "FCCAnalyses::ReconstructedParticle::get_p(sorted_zll_leptons)")
  df = df.Define("sorted_zll_leptons_m",     "FCCAnalyses::ReconstructedParticle::get_mass(sorted_zll_leptons)")
  df = df.Define("sorted_zll_leptons_theta",  "FCCAnalyses::ReconstructedParticle::get_theta(sorted_zll_leptons)")
  df = df.Define("sorted_zll_leptons_phi",  "FCCAnalyses::ReconstructedParticle::get_phi(sorted_zll_leptons)")
  df = df.Define("leading_zll_lepton_p",  "return sorted_zll_leptons_p.at(0)")
  df = df.Define("leading_zll_lepton_m",  "return sorted_zll_leptons_m.at(0)")
  df = df.Define("leading_zll_lepton_theta",  "return sorted_zll_leptons_theta.at(0)")
  df = df.Define("leading_zll_lepton_phi",  "return sorted_zll_leptons_phi.at(0)")
  df = df.Define("subleading_zll_lepton_p",  "return sorted_zll_leptons_p.at(1)")
  df = df.Define("subleading_zll_lepton_m",  "return sorted_zll_leptons_m.at(1)")
  df = df.Define("subleading_zll_lepton_theta",  "return sorted_zll_leptons_theta.at(1)")
  df = df.Define("subleading_zll_lepton_phi",  "return sorted_zll_leptons_phi.at(1)")
  
  df = df.Define("zll_Leptons_acolinearity", "HiggsTools::acolinearity(sorted_zll_leptons)")
  df = df.Define("zll_Leptons_acoplanarity", "HiggsTools::acoplanarity(sorted_zll_leptons)") 
  df = df.Define("zll_leptons_acolinearity", "if(zll_Leptons_acolinearity.size()>0) return zll_Leptons_acolinearity.at(0); else return -std::numeric_limits<float>::max()") 
  df = df.Define("zll_leptons_acoplanarity", "if(zll_Leptons_acoplanarity.size()>0) return zll_Leptons_acoplanarity.at(0); else return -std::numeric_limits<float>::max()") 
           
  
  
  df = df.Define("MVAVec", ROOT.computeModel1, (
          #leptons
          "leading_zll_lepton_p",
          "leading_zll_lepton_theta",
          "subleading_zll_lepton_p",
          "subleading_zll_lepton_theta",
          "zll_leptons_acolinearity",
          "zll_leptons_acoplanarity",
          #Zed
          "zll_m",
          "zll_p",
          "zll_theta"
          #Higgsstrahlungness
          #"H"
          ))
  df = df.Define("BDTscore", "MVAVec.at(0)")
  #Build the cut flow
  print("--> Counting selections")
  print("--> Counting pre-selection")
  for cur_cut in cuts[3:]:
    print(f"---->Working on cut {cur_cut}")
    N_tmp = []
    N_err_tmp = []
    df = df.Filter(cur_cut)
    for cur_decay in decays:
      print(f"---->Working on decay channel {cur_decay}")
      N_tmp.append(df.Filter(f"daughter_higgs_collapsed == {pid_map[cur_decay]}" ).Sum("weight").GetValue())
      N_err_tmp.append(df.Filter(f"daughter_higgs_collapsed == {pid_map[cur_decay]}" ).Sum("weight").GetValue()**0.5)
    N.append(N_tmp)
    N_err.append(N_err_tmp)
  

  # Calculate efficiencies
  N_ref = N[0][:]
  N_err_ref = N_err[0][:]
  N_avg_ref = np.sum(N[0])
  N_avg_err_ref = N_avg_ref**0.5

  for i_cut in range(len(cuts)):
    Eff_tmp = []
    Err_tmp = []
    for i_decay in range(len(decays)): 
      Eff_tmp.append(N[i_cut][i_decay]/N_ref[i_decay])
      Err_tmp.append(Eff_tmp[i_decay]*((N_err_ref[i_decay]/N_ref[i_decay])**2 + (N_err[i_cut][i_decay]/N[i_cut][i_decay])**2)**0.5)
    Eff.append(Eff_tmp)
    Err.append(Err_tmp)
    N_avg_tmp = np.sum(N[i_cut])
    N_avg_err_tmp = N_avg_tmp**0.5
    Eff_avg.append(np.sum(N[i_cut])/np.sum(N[0]))
    Err_avg.append(Eff_avg[i_cut]*((N_avg_err_ref/N_avg_ref)**2 + (N_avg_err_tmp/N_avg_tmp)**2)**0.5)
  print(Eff)
  print(Err)



  print("--> Branching ratios")
  for decay in decays:
    print(f"{decay}\t", end=" ")
  print("----------------------------------------------------------")
  print("----------------------------------------------------------")
  for i_cut in range(len(cuts)):
    Sum = sum(cuts[i_decay])
    for i_decay in range(len(decays)):
      print(f'{cuts[i_decay][i_cut]/Sum:.2f}\t', end=" ")
    print("----------------------------------------------------------")

  print("--> Cut Efficiency")
  for decay in decays:
    print(f"{decay}\t", end=" ")
  print("----------------------------------------------------------")
  print("----------------------------------------------------------") 
  for i_cut in range(len(cuts)): 
    for i_decay in range(len(decays)): 
      print(rf'{Eff[i_decay][i_cut]*100:.3f} $pm$ {Err[i_decay][i_cut]*100:.3f}\t', end=" ")


  print("")
  print("Cut efficiencies")
  print("")
  print("& Average ", end=" ")
  for cur_decay in decays:
    print(" & f{cur_decay} ", end=" ")
  print(r" \\  \hline \hline")
  ###print("Average ", end=" ")
  ###for pdg in decay_names: print(" %s\t" % pdg, end=" ")
  ###print("")
  ip = 0
  for i,cut in enumerate(cuts):
      print("%s & " % cuts[i], end=" ")
      ###print("%s\t" % cut, end=" ")
      idx = 0 if i == 0 else i-1
      idx = 0
      h_ref = fIn.Get("%s/higgs_decay%s" % (proc, cuts[idx]))
      h_cut = fIn.Get("%s/higgs_decay%s" % (proc, cut))
      
      
      y_ref_tot_err = ctypes.c_double(1.)
      y_ref_tot = h_ref.IntegralAndError(0, h_ref.GetNbinsX() + 1, y_ref_tot_err)
      y_ref_tot_err = y_ref_tot_err.value
      
      y_cut_tot_err = ctypes.c_double(1.)
      y_cut_tot = h_cut.IntegralAndError(0, h_cut.GetNbinsX() + 1, y_cut_tot_err)
      y_cut_tot_err = y_cut_tot_err.value


      
      sel_eff_tot = y_cut_tot / y_ref_tot
      sel_eff_tot_err = sel_eff_tot * ( (y_cut_tot_err/y_cut_tot)**2 + (y_ref_tot_err/y_ref_tot)**2)**0.5

      ###print("%.3f\t" % (sel_eff_tot), end=" ")
      if sel_eff_tot == 1: print(r"%.1f $\pm$ %.2f" % (sel_eff_tot*100., sel_eff_tot_err*100.), end=" ")
      else: print(r"%.2f $\pm$ %.2f" % (sel_eff_tot*100., sel_eff_tot_err*100.), end=" ")
       
  #for i_cut in range(len(cuts)):
  #   plt.plot(Eff[i_cut], y, ls='dotted', c='red', lw=5)
  xMin, xMax = 65, 75#55, 75
  h_pulls = ROOT.TH2F("pulls", "pulls", (xMax-xMin)*10, xMin, xMax, len(decays)+1, 0, len(decays)+1)
  g_pulls = ROOT.TGraphErrors(len(decays)+1)
  ip = 0
  for i,cut in enumerate(cuts):
    if i == len(cuts)-1:
      g_pulls.SetPoint(ip, *100., float(ip) + 0.5)
            #g_pulls.SetPointError(ip, sel_eff_tot_err*100., sel_eff_tot_err*100., 0., 0.)
            g_pulls.SetPointError(ip, sel_eff_tot_err*100., 0.)
            h_pulls.GetYaxis().SetBinLabel(ip + 1, "Average")
            ip += 1