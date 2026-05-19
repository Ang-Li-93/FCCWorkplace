#python examples/FCCee/higgs/mH-recoil/mumu/finalSel.py 

from config.common_defaults import deffccdicts

import sys, os
import ROOT

###Input directory where the files produced at the pre-selection level are
#baseDir  = "outputs/FCCee/higgs/mH-recoil/mumu/"
baseDir = "/eos/home-l/lia/FCCee/mumu/"
###Link to the dictonary that contains all the cross section informations etc...
#procDict = os.path.join(os.getenv('FCCDICTSDIR', deffccdicts), '') + "FCCee_procDict_fcc_tmp.json"
procDict = os.path.join(os.getenv('FCCDICTSDIR', deffccdicts), '') + "FCCee_procDict_spring2021_IDEA.json"
#procDict = "/afs/cern.ch/work/l/lia/private/FCC/test/FCCAnalyses_0519/FCCee_procDict_spring2021_IDEA.json"
#process_list=['p8_ee_ZH_ecm240']
#process_list=['p8_ee_ZZ_ecm240','p8_ee_WW_ecm240','p8_ee_ZH_ecm240']
#process_list=['p8_noBES_ee_ZZ_ecm240','p8_noBES_ee_WW_ecm240','p8_noBES_ee_ZH_ecm240']
#process_list=['p8_ee_ZZ_ecm240','p8_ee_WW_mumu_ecm240','p8_ee_ZH_ecm240']
#process_list=['wzp6_ee_mumuH_ecm240_v2']
#process_list=['p8_ee_Zqq_ecm240','p8_ee_Zll_ecm240','p8_ee_ZZ_ecm240','p8_ee_WW_mumu_ecm240','p8_ee_ZH_ecm240']
#process_list=['wzp6_gammae_eZ_Zmumu_ecm240','wzp6_egamma_eZ_Zmumu_ecm240','p8_ee_Zqq_ecm240','p8_ee_Zll_ecm240','p8_ee_ZZ_ecm240','p8_ee_WW_mumu_ecm240','wzp6_ee_mumuH_ecm240','wzp6_ee_tautauH_ecm240','wzp6_ee_qqH_ecm240']
#process_list=['p8_ee_ZH_ecm240','wzp6_gaga_mumu_60_ecm240','wzp6_gaga_tautau_60_ecm240','wzp6_gammae_eZ_Zmumu_ecm240','wzp6_egamma_eZ_Zmumu_ecm240','p8_ee_Zqq_ecm240','p8_ee_Zll_ecm240','p8_ee_ZZ_ecm240','p8_ee_WW_mumu_ecm240','wzp6_ee_mumuH_ecm240','wzp6_ee_tautauH_ecm240','wzp6_ee_qqH_ecm240','wzp6_ee_nunuH_ecm240','wzp6_ee_eeH_ecm240']
#process_list=['wzp6_gaga_mumu_60_ecm240','wzp6_gaga_tautau_60_ecm240','wzp6_gammae_eZ_Zmumu_ecm240','wzp6_egamma_eZ_Zmumu_ecm240','p8_ee_Zqq_ecm240','p8_ee_Zll_ecm240','p8_ee_ZZ_ecm240','p8_ee_WW_mumu_ecm240','p8_ee_ZH_ecm240']
#process_list=['wzp6_ee_mumuH_noISR_ecm240','wzp6_noBES_ee_mumuH_ecm240']
#process_list=['kkmcp8_ee_mumu_ecm240']
#process_list=['wzp6_ee_mumu_ecm240', 'wzp6_ee_tautau_ecm240', 'wzp6_ee_ee_Mee_30_150_ecm240']
#process_list=['kkmcp8_ee_mumu_noFSR_ecm240']
#process_list=['wzp6_ee_mumu_noFSR_ecm240']
#process_list=['wzp6_ee_mumuH_noFSR_ecm240']
#process_list=['wzp6_ee_mumuH_ecm240']
#process_list=['wzp6_ee_mumuH_ecm240_reweighted']
#process_list=['kkmcp8_ee_mumu_noFSR_ecm240','wzp6_ee_mumu_noFSR_ecm240']
#process_list=['events_075322554_xing','events_075322554_headon','events_075322554']
#process_list=['events_075322554_Delphes_headon','events_075322554_FullSim_headon','events_075322554_Delphes_xing','events_075322554_FullSim_xing']
#process_list=['events_075322554_Delphes_headon','events_075322554_FullSim_headon','events_045918595_Delphes_AllMuons','events_045918595_Delphes_IsoMuons']
#*100/97
#process_list=['events_045918595_FullSim_AllMuons','events_045918595_FullSim_IsoMuons']
#*100/99
#process_list=['events_075322554_FullSim_xing','events_075322554_FullSim_xing_1up','events_075322554_FullSim_xing_1down']
process_list=['events_075322554_FullSim_xing_noboost']
ROOT.gInterpreter.Declare("""
bool myFilter(ROOT::VecOps::RVec<float> z_mass,ROOT::VecOps::RVec<float> muon_pT,ROOT::VecOps::RVec<TLorentzVector> muon_tlv) {
  //cout << "begin" << endl;
  //cout << "z_mass.size() = " << z_mass.size() << endl;
  //cout << "z" << endl;
  //if(z_mass.size()>1||z_mass.size()<1) return false;
  if(z_mass.size()<2) return false;
  //cout << "e" << endl;
  //if (z_mass.at(0)<80. || z_mass.at(0)>100.) return false;
  //cout << "c" << endl;
  //for (ROOT::VecOps::RVec<float>::iterator it = muon_pT.begin(); it != muon_pT.end(); ++it){
  //for (size_t i = 0; i < muon_pT.size(); ++i){
  //  if (muon_pT.at(i) < 20){
  //    return false;
  //  }
  //}
  //cout << "d" << endl;
  //if (muon_tlv.size()!=2) return false;
  //cout << "a" << endl;
  //float angle = (muon_tlv.at(0).Px()*muon_tlv.at(1).Px()+muon_tlv.at(0).Py()*muon_tlv.at(1).Py()+muon_tlv.at(0).Pz()*muon_tlv.at(1).Pz())/(muon_tlv.at(0).P()*muon_tlv.at(1).P());
  //cout << "b" << endl;
  //if (angle < -0.99619469809) return false;
  return true;
}
""")

ROOT.gInterpreter.Declare("""
bool myFilter1(ROOT::VecOps::RVec<float> mass) {
  if (mass.size()<2) return false;
  for (size_t i = 0; i < mass.size(); ++i) {
  if (mass.at(i)<80. || mass.at(i)>100.)
    return false;
  }
  return true;
}
""")

ROOT.gInterpreter.Declare("""
bool pTmuFilter(ROOT::VecOps::RVec<float> pTmuon, float min) {
  for (size_t i = 0; i < pTmuon.size(); ++i) {
    if (pTmuon.at(i) < min){
      return false;
    }
  }
  return true;
}
""")

###Dictionnay of the list of cuts. The key is the name of the selection that will be added to the output file
cut_list = {"sel0":"return true;",
            #"Gen_mass_220": "gen_mass_mumu > 220",
            #"Gen_mass_220": "gen_mass_ZH > 220",
            #"sel1":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 80 &&  zed_leptonic_m[0] < 100",
            #"sel2":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 80 &&  zed_leptonic_m[0] < 100 && zed_leptonic_recoil_m[0] > 40 && zed_leptonic_recoil_m[0] <160 ",
            #"sel3":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 80 &&  zed_leptonic_m[0] < 100 && zed_leptonic_recoil_m[0] > 40 && zed_leptonic_recoil_m[0] <160 && zed_leptonic_pt[0] > 20",
            #"sel4":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 80 &&  zed_leptonic_m[0] < 100 && zed_leptonic_recoil_m[0] > 120 && zed_leptonic_recoil_m[0] <140 ",
            #"sel5":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 80 &&  zed_leptonic_m[0] < 100 && zed_leptonic_recoil_m[0] > 120 && zed_leptonic_recoil_m[0] <140 && zed_leptonic_recoil_m[0] <140 && missingET_costheta.size() ==1 && missingET_costheta[0] > -0.98 && missingET_costheta[0] < 0.98",
            #"sel6":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 80 &&  zed_leptonic_m[0] < 100 && zed_leptonic_recoil_m[0] > 120 && zed_leptonic_recoil_m[0] <140 && zed_leptonic_pt[0] > 20",
            #"sel7":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 80 &&  zed_leptonic_m[0] < 100 && zed_leptonic_recoil_m[0] > 120 && zed_leptonic_recoil_m[0] <140 && zed_leptonic_pt[0] > 20 && zed_leptonic_pt[0] <100 " ,
            #"sel8":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 80 &&  zed_leptonic_m[0] < 100 && zed_leptonic_recoil_m[0] > 120 && zed_leptonic_recoil_m[0] <140 && zed_leptonic_pt[0] > 20 && zed_leptonic_pt[0] <80 " ,
            #"sel9":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 80 &&  zed_leptonic_m[0] < 100 && zed_leptonic_recoil_m[0] > 120 && zed_leptonic_recoil_m[0] <140 && zed_leptonic_pt[0] > 20 && zed_leptonic_pt[0] <70 " ,
            #"sel10":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 80 &&  zed_leptonic_m[0] < 100 && zed_leptonic_recoil_m[0] > 120 && zed_leptonic_recoil_m[0] <140 && zed_leptonic_pt[0] > 20 && zed_leptonic_pt[0] <70 && missingET_costheta.size() ==1 && missingET_costheta[0] > -0.98 && missingET_costheta[0] < 0.98",
            #"sel11":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 80 &&  zed_leptonic_m[0] < 100 && zed_leptonic_recoil_m[0] > 124 && zed_leptonic_recoil_m[0] <126 ",
            #"sel12":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 80 &&  zed_leptonic_m[0] < 100 && zed_leptonic_recoil_m[0] > 124 && zed_leptonic_recoil_m[0] <126 && zed_leptonic_pt[0] > 20",
            #"sel13":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 86 &&  zed_leptonic_m[0] < 96",
            #"sel14":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 86 &&  zed_leptonic_m[0] < 96 && zed_leptonic_recoil_m[0] > 40 && zed_leptonic_recoil_m[0] <160 ",
            #"sel15":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 86 &&  zed_leptonic_m[0] < 96 && zed_leptonic_recoil_m[0] > 40 && zed_leptonic_recoil_m[0] <160 && zed_leptonic_pt[0] > 20",
            #"sel16":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 86 &&  zed_leptonic_m[0] < 96 && zed_leptonic_recoil_m[0] > 120 && zed_leptonic_recoil_m[0] <140 ",
            #"sel17":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 86 &&  zed_leptonic_m[0] < 96 && zed_leptonic_recoil_m[0] > 120 && zed_leptonic_recoil_m[0] <140 && missingET_costheta.size() ==1 && missingET_costheta[0] > -0.98 && missingET_costheta[0] < 0.98",
            #"sel18":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 86 &&  zed_leptonic_m[0] < 96 && zed_leptonic_recoil_m[0] > 120 && zed_leptonic_recoil_m[0] <140 && zed_leptonic_pt[0] > 20",
            #"sel19":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 86 &&  zed_leptonic_m[0] < 96 && zed_leptonic_recoil_m[0] > 120 && zed_leptonic_recoil_m[0] <140 && zed_leptonic_pt[0] > 20 && missingET_costheta.size() ==1 && missingET_costheta[0] > -0.98 && missingET_costheta[0] < 0.98",
            #"sel20":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 86 &&  zed_leptonic_m[0] < 96 && zed_leptonic_recoil_m[0] > 120 && zed_leptonic_recoil_m[0] <140 && zed_leptonic_pt[0] > 20 && zed_leptonic_pt[0] <100 ",
            #"sel21":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 86 &&  zed_leptonic_m[0] < 96 && zed_leptonic_recoil_m[0] > 120 && zed_leptonic_recoil_m[0] <140 && zed_leptonic_pt[0] > 20 && zed_leptonic_pt[0] <80 ",
            #"sel22":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 86 &&  zed_leptonic_m[0] < 96 && zed_leptonic_recoil_m[0] > 120 && zed_leptonic_recoil_m[0] <140 && zed_leptonic_pt[0] > 20 && zed_leptonic_pt[0] <70 ",
            "sel23":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 86 &&  zed_leptonic_m[0] < 96 && zed_leptonic_recoil_m[0] > 120 && zed_leptonic_recoil_m[0] <140 && zed_leptonic_pt[0] > 20 && zed_leptonic_pt[0] <70 && missingET_costheta.size() ==1 && missingET_costheta[0] > -0.98 && missingET_costheta[0] < 0.98",
            #"sel24":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 86 &&  zed_leptonic_m[0] < 96 && zed_leptonic_recoil_m[0] > 124 && zed_leptonic_recoil_m[0] <126 ",
            #"sel25":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 86 &&  zed_leptonic_m[0] < 96 && zed_leptonic_recoil_m[0] > 124 && zed_leptonic_recoil_m[0] <126 && zed_leptonic_pt[0] > 20",
            #"sel26":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 73 &&  zed_leptonic_m[0] < 120 && zed_leptonic_recoil_m[0] > 110 && zed_leptonic_recoil_m[0] <155 && zed_leptonic_pt[0] > 10 && zed_leptonic_pt[0] <70 && missingET_costheta.size() ==1 && missingET_costheta[0] > -0.98 && missingET_costheta[0] < 0.98",
            "sel27":"zed_leptonic_m.size() == 1 && zed_leptonic_m[0] > 86 &&  zed_leptonic_m[0] < 96 && zed_leptonic_pt[0] > 20 && zed_leptonic_pt[0] <70 && missingET_costheta.size() ==1 && missingET_costheta[0] > -0.98 && missingET_costheta[0] < 0.98",
            "sel28":"zed_leptonic_m.size() == 1 && zed_leptonic_recoil_m[0] > 120 && zed_leptonic_recoil_m[0] <140 && zed_leptonic_pt[0] > 20 && zed_leptonic_pt[0] <70 && missingET_costheta.size() ==1 && missingET_costheta[0] > -0.98 && missingET_costheta[0] < 0.98",  
            #"sel29":"zed_leptonic_m.size() == 1 && zed_leptonic_recoil_m[0] > 124 && zed_leptonic_recoil_m[0] <126 && zed_leptonic_pt[0] > 20 && zed_leptonic_pt[0] <70 && missingET_costheta.size() ==1 && missingET_costheta[0] > -0.98 && missingET_costheta[0] < 0.98",
            #"MC_sel1":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 80 &&  zed_leptonic_MC_mass[0] < 100",
            #"MC_sel2":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 80 &&  zed_leptonic_MC_mass[0] < 100 && zed_leptonic_recoil_MC_mass[0] > 40 && zed_leptonic_recoil_MC_mass[0] <160 ",
            #"MC_sel3":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 80 &&  zed_leptonic_MC_mass[0] < 100 && zed_leptonic_recoil_MC_mass[0] > 40 && zed_leptonic_recoil_MC_mass[0] <160 && zed_leptonic_MC_pt[0] > 20",
            #"MC_sel4":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 80 &&  zed_leptonic_MC_mass[0] < 100 && zed_leptonic_recoil_MC_mass[0] > 120 && zed_leptonic_recoil_MC_mass[0] <140 ",
            #"MC_sel5":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 80 &&  zed_leptonic_MC_mass[0] < 100 && zed_leptonic_recoil_MC_mass[0] > 120 && zed_leptonic_recoil_MC_mass[0] <140 && zed_leptonic_recoil_MC_mass[0] <140 && missingET_costheta.size() ==1 && missingET_costheta[0] > -0.98 && missingET_costheta[0] < 0.98",
            #"MC_sel6":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 80 &&  zed_leptonic_MC_mass[0] < 100 && zed_leptonic_recoil_MC_mass[0] > 120 && zed_leptonic_recoil_MC_mass[0] <140 && zed_leptonic_MC_pt[0] > 20",
            #"MC_sel7":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 80 &&  zed_leptonic_MC_mass[0] < 100 && zed_leptonic_recoil_MC_mass[0] > 120 && zed_leptonic_recoil_MC_mass[0] <140 && zed_leptonic_MC_pt[0] > 20 && zed_leptonic_MC_pt[0] <100 " ,
            #"MC_sel8":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 80 &&  zed_leptonic_MC_mass[0] < 100 && zed_leptonic_recoil_MC_mass[0] > 120 && zed_leptonic_recoil_MC_mass[0] <140 && zed_leptonic_MC_pt[0] > 20 && zed_leptonic_MC_pt[0] <80 " ,
            #"MC_sel9":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 80 &&  zed_leptonic_MC_mass[0] < 100 && zed_leptonic_recoil_MC_mass[0] > 120 && zed_leptonic_recoil_MC_mass[0] <140 && zed_leptonic_MC_pt[0] > 20 && zed_leptonic_MC_pt[0] <70 " ,
            #"MC_sel10":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 80 &&  zed_leptonic_MC_mass[0] < 100 && zed_leptonic_recoil_MC_mass[0] > 120 && zed_leptonic_recoil_MC_mass[0] <140 && zed_leptonic_MC_pt[0] > 20 && zed_leptonic_MC_pt[0] <70 && missingET_costheta.size() ==1 && missingET_costheta[0] > -0.98 && missingET_costheta[0] < 0.98",
            #"MC_sel11":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 80 &&  zed_leptonic_MC_mass[0] < 100 && zed_leptonic_recoil_MC_mass[0] > 124 && zed_leptonic_recoil_MC_mass[0] <126 ",
            #"MC_sel12":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 80 &&  zed_leptonic_MC_mass[0] < 100 && zed_leptonic_recoil_MC_mass[0] > 124 && zed_leptonic_recoil_MC_mass[0] <126 && zed_leptonic_MC_pt[0] > 20",
            #"MC_sel13":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 86 &&  zed_leptonic_MC_mass[0] < 96",
            #"MC_sel14":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 86 &&  zed_leptonic_MC_mass[0] < 96 && zed_leptonic_recoil_MC_mass[0] > 40 && zed_leptonic_recoil_MC_mass[0] <160 ",
            #"MC_sel15":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 86 &&  zed_leptonic_MC_mass[0] < 96 && zed_leptonic_recoil_MC_mass[0] > 40 && zed_leptonic_recoil_MC_mass[0] <160 && zed_leptonic_MC_pt[0] > 20",
            #"MC_sel16":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 86 &&  zed_leptonic_MC_mass[0] < 96 && zed_leptonic_recoil_MC_mass[0] > 120 && zed_leptonic_recoil_MC_mass[0] <140 ",
            #"MC_sel17":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 86 &&  zed_leptonic_MC_mass[0] < 96 && zed_leptonic_recoil_MC_mass[0] > 120 && zed_leptonic_recoil_MC_mass[0] <140 && missingET_costheta.size() ==1 && missingET_costheta[0] > -0.98 && missingET_costheta[0] < 0.98",
            #"MC_sel18":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 86 &&  zed_leptonic_MC_mass[0] < 96 && zed_leptonic_recoil_MC_mass[0] > 120 && zed_leptonic_recoil_MC_mass[0] <140 && zed_leptonic_MC_pt[0] > 20",
            #"MC_sel19":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 86 &&  zed_leptonic_MC_mass[0] < 96 && zed_leptonic_recoil_MC_mass[0] > 120 && zed_leptonic_recoil_MC_mass[0] <140 && zed_leptonic_MC_pt[0] > 20 && missingET_costheta.size() ==1 && missingET_costheta[0] > -0.98 && missingET_costheta[0] < 0.98",
            #"MC_sel20":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 86 &&  zed_leptonic_MC_mass[0] < 96 && zed_leptonic_recoil_MC_mass[0] > 120 && zed_leptonic_recoil_MC_mass[0] <140 && zed_leptonic_MC_pt[0] > 20 && zed_leptonic_MC_pt[0] <100 ",
            #"MC_sel21":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 86 &&  zed_leptonic_MC_mass[0] < 96 && zed_leptonic_recoil_MC_mass[0] > 120 && zed_leptonic_recoil_MC_mass[0] <140 && zed_leptonic_MC_pt[0] > 20 && zed_leptonic_MC_pt[0] <80 ",
            #"MC_sel22":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 86 &&  zed_leptonic_MC_mass[0] < 96 && zed_leptonic_recoil_MC_mass[0] > 120 && zed_leptonic_recoil_MC_mass[0] <140 && zed_leptonic_MC_pt[0] > 20 && zed_leptonic_MC_pt[0] <70 ",
            #"MC_sel23":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 86 &&  zed_leptonic_MC_mass[0] < 96 && zed_leptonic_recoil_MC_mass[0] > 120 && zed_leptonic_recoil_MC_mass[0] <140 && zed_leptonic_MC_pt[0] > 20 && zed_leptonic_MC_pt[0] <70 && missingET_costheta.size() ==1 && missingET_costheta[0] > -0.98 && missingET_costheta[0] < 0.98",
            #"MC_sel24":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 86 &&  zed_leptonic_MC_mass[0] < 96 && zed_leptonic_recoil_MC_mass[0] > 124 && zed_leptonic_recoil_MC_mass[0] <126 ",
            #"MC_sel25":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 86 &&  zed_leptonic_MC_mass[0] < 96 && zed_leptonic_recoil_MC_mass[0] > 124 && zed_leptonic_recoil_MC_mass[0] <126 && zed_leptonic_MC_pt[0] > 20",
            #"MC_sel26":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 73 &&  zed_leptonic_MC_mass[0] < 120 && zed_leptonic_recoil_MC_mass[0] > 110 && zed_leptonic_recoil_MC_mass[0] <155 && zed_leptonic_MC_pt[0] > 10 && zed_leptonic_MC_pt[0] <70 && missingET_costheta.size() ==1 && missingET_costheta[0] > -0.98 && missingET_costheta[0] < 0.98",
            #"MC_sel27":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_MC_mass[0] > 86 &&  zed_leptonic_MC_mass[0] < 96 && zed_leptonic_MC_pt[0] > 20 && zed_leptonic_MC_pt[0] <70 && missingET_costheta.size() ==1 && missingET_costheta[0] > -0.98 && missingET_costheta[0] < 0.98",
            #"MC_sel28":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_recoil_MC_mass[0] > 120 && zed_leptonic_recoil_MC_mass[0] <140 && zed_leptonic_MC_pt[0] > 20 && zed_leptonic_MC_pt[0] <70 && missingET_costheta.size() ==1 && missingET_costheta[0] > -0.98 && missingET_costheta[0] < 0.98",  
            #"MC_sel29":"zed_leptonic_MC_mass.size() == 1 && zed_leptonic_recoil_MC_mass[0] > 124 && zed_leptonic_recoil_MC_mass[0] <126 && zed_leptonic_MC_pt[0] > 20 && zed_leptonic_MC_pt[0] <70 && missingET_costheta.size() ==1 && missingET_costheta[0] > -0.98 && missingET_costheta[0] < 0.98"
    
    }



###Dictionary for the ouput variable/hitograms. The key is the name of the variable in the output files. "name" is the name of the variable in the input file, "title" is the x-axis label of the histogram, "bin" the number of bins of the histogram, "xmin" the minimum x-axis value and "xmax" the maximum x-axis value.
variables = {
    "MET_costheta":{"name":"missingET_costheta","title":"cos#theta_{missing}","bin":200,"xmin":-1,"xmax":1},
    "Nmu_plus":{"name":"selected_muons_plus_n","title":"muon plus number","bin":12,"xmin":-1.5,"xmax":10.5},
    "Nmu_minus":{"name":"selected_muons_minus_n","title":"muon minus number","bin":12,"xmin":-1.5,"xmax":10.5},
    "Nmu":{"name":"selected_muons_n","title":"muon number","bin":12,"xmin":-1.5,"xmax":10.5},
    "Cz":{"name":"zed_leptonic_charge","title":"Reconstructed Z charge","bin":23,"xmin":-11.5,"xmax":11.5},
    "Nz":{"name":"zed_leptonic_n","title":"#mu^{+}#mu^{-} pair number","bin":12,"xmin":-1.5,"xmax":10.5},
    "mz":{"name":"zed_leptonic_m","title":"m_{#mu^{+}#mu^{-}} [GeV]","bin":250,"xmin":0,"xmax":250},
    "mz_zoom1":{"name":"zed_leptonic_m","title":"m_{#mu^{+}#mu^{-}} [GeV]","bin":40,"xmin":80,"xmax":100},
    "mz_zoom2":{"name":"zed_leptonic_m","title":"m_{#mu^{+}#mu^{-}} [GeV]","bin":470,"xmin":73,"xmax":120},
    "mz_zoom3":{"name":"zed_leptonic_m","title":"m_{#mu^{+}#mu^{-}} [GeV]","bin":300,"xmin":80,"xmax":110},
    "mz_zoom4":{"name":"zed_leptonic_m","title":"m_{#mu^{+}#mu^{-}} [GeV]","bin":200,"xmin":80,"xmax":100},
    "mz_zoom5":{"name":"zed_leptonic_m","title":"m_{#mu^{+}#mu^{-}} [GeV]","bin":140,"xmin":84,"xmax":98},
    "mz_zoom6":{"name":"zed_leptonic_m","title":"m_{#mu^{+}#mu^{-}} [GeV]","bin":100,"xmin":86,"xmax":96},
    "mz_zoom7":{"name":"zed_leptonic_m","title":"m_{#mu^{+}#mu^{-}} [GeV]","bin":470,"xmin":73,"xmax":120},
    "mz_zoom8":{"name":"zed_leptonic_m","title":"m_{#mu^{+}#mu^{-}} [GeV]","bin":100,"xmin":80,"xmax":100},
    "z_pt":{"name":"zed_leptonic_pt","title":"p_{T}^{#mu^{+}#mu^{-}} [GeV]","bin":125,"xmin":0,"xmax":125},
    "z_mass":{"name":"zed_leptonic_m","title":"m_{#mu^{+}#mu^{-}} [GeV]","bin":250,"xmin":0,"xmax":250},
    "z_y":{"name":"zed_leptonic_y","title":"y^{#mu^{+}#mu^{-}} [GeV]","bin":120,"xmin":-3.0,"xmax":3.0},
    "z_p":{"name":"zed_leptonic_p","title":"p^{#mu^{+}#mu^{-}} [GeV]","bin":300,"xmin":0,"xmax":150.0},
    "z_e":{"name":"zed_leptonic_e","title":"E^{#mu^{+}#mu^{-}} [GeV]","bin":300,"xmin":0,"xmax":150.0},
    "leptonic_recoil_m":{"name":"zed_leptonic_recoil_m","title":"M_{recoil} [GeV]","bin":100,"xmin":0,"xmax":200},
    "leptonic_recoil_m_zoom1":{"name":"zed_leptonic_recoil_m","title":"M_{recoil} [GeV]","bin":240,"xmin":116,"xmax":140},
    "leptonic_recoil_m_zoom2":{"name":"zed_leptonic_recoil_m","title":"M_{recoil} [GeV]","bin":200,"xmin":120,"xmax":140},
    "leptonic_recoil_m_zoom3":{"name":"zed_leptonic_recoil_m","title":"M_{recoil} [GeV]","bin":200,"xmin":116,"xmax":136},
    "leptonic_recoil_m_zoom4":{"name":"zed_leptonic_recoil_m","title":"M_{recoil} [GeV]","bin":40,"xmin":124,"xmax":128},
    "leptonic_recoil_m_zoom5":{"name":"zed_leptonic_recoil_m","title":"M_{recoil} [GeV]","bin":120,"xmin":128,"xmax":140},
    "leptonic_recoil_m_zoom6":{"name":"zed_leptonic_recoil_m","title":"M_{recoil} [GeV]","bin":300,"xmin":80,"xmax":110},
    "leptonic_recoil_m_zoom7":{"name":"zed_leptonic_recoil_m","title":"M_{recoil} [GeV]","bin":200,"xmin":80,"xmax":100},
    "leptonic_recoil_m_zoom8":{"name":"zed_leptonic_recoil_m","title":"M_{recoil} [GeV]","bin":100,"xmin":86,"xmax":96},
    "leptonic_recoil_m_zoom9":{"name":"zed_leptonic_recoil_m","title":"M_{recoil} [GeV]","bin":600,"xmin":40,"xmax":160},
    "leptonic_recoil_m_zoom10":{"name":"zed_leptonic_recoil_m","title":"M_{recoil} [GeV]","bin":400,"xmin":0,"xmax":200},
    "leptonic_recoil_m_zoom11":{"name":"zed_leptonic_recoil_m","title":"M_{recoil} [GeV]","bin":450,"xmin":110,"xmax":155},
    "leptonic_recoil_m_zoom12":{"name":"zed_leptonic_recoil_m","title":"M_{recoil} [GeV]","bin":240,"xmin":40,"xmax":160},
    "leptonic_recoil_m_zoom13":{"name":"zed_leptonic_recoil_m","title":"M_{recoil} [GeV]","bin":200,"xmin":80,"xmax":120},
    "leptonic_recoil_m_zoom14":{"name":"zed_leptonic_recoil_m","title":"M_{recoil} [GeV]","bin":100,"xmin":120,"xmax":140},
    "leptonic_recoil_m_zoom15":{"name":"zed_leptonic_recoil_m","title":"M_{recoil} [GeV]","bin":150,"xmin":80,"xmax":140},
    "leptonic_recoil_m_zoom16":{"name":"zed_leptonic_recoil_m","title":"M_{recoil} [GeV]","bin":100,"xmin":80,"xmax":120},
    "leptonic_recoil_pt":{"name":"zed_leptonic_recoil_pt","title":"p_{T}^{recoil} [GeV]","bin":55,"xmin":0,"xmax":110},
    #"Cz_MC":{"name":"zed_leptonic_MC_charge","title":"MC Reconstructed Z charge","bin":23,"xmin":-11.5,"xmax":11.5},
    #"Nz_MC":{"name":"zed_leptonic_MC_n","title":"MC #mu^{+}#mu^{-} pair number","bin":12,"xmin":-1.5,"xmax":10.5},
    #"mz_MC":{"name":"zed_leptonic_MC_mass","title":"MC m_{#mu^{+}#mu^{-}} [GeV]","bin":250,"xmin":0,"xmax":250},
    #"mz_MC_zoom1":{"name":"zed_leptonic_MC_mass","title":"MC m_{#mu^{+}#mu^{-}} [GeV]","bin":40,"xmin":80,"xmax":100},
    #"mz_MC_zoom2":{"name":"zed_leptonic_MC_mass","title":"MC m_{#mu^{+}#mu^{-}} [GeV]","bin":470,"xmin":73,"xmax":120},
    #"mz_MC_zoom3":{"name":"zed_leptonic_MC_mass","title":"MC m_{#mu^{+}#mu^{-}} [GeV]","bin":300,"xmin":80,"xmax":110},
    #"mz_MC_zoom4":{"name":"zed_leptonic_MC_mass","title":"MC m_{#mu^{+}#mu^{-}} [GeV]","bin":200,"xmin":80,"xmax":100},
    #"mz_MC_zoom5":{"name":"zed_leptonic_MC_mass","title":"MC m_{#mu^{+}#mu^{-}} [GeV]","bin":140,"xmin":84,"xmax":98},
    #"mz_MC_zoom6":{"name":"zed_leptonic_MC_mass","title":"MC m_{#mu^{+}#mu^{-}} [GeV]","bin":100,"xmin":86,"xmax":96},
    #"mz_MC_zoom7":{"name":"zed_leptonic_MC_mass","title":"MC m_{#mu^{+}#mu^{-}} [GeV]","bin":470,"xmin":73,"xmax":120},
    #"z_MC_pt":{"name":"zed_leptonic_MC_pt","title":"MC p_{T}^{#mu^{+}#mu^{-}} [GeV]","bin":125,"xmin":0,"xmax":125},
    #"z_MC_mass":{"name":"zed_leptonic_MC_mass","title":"MC m_{#mu^{+}#mu^{-}} [GeV]","bin":250,"xmin":0,"xmax":250},
    #"z_MC_y":{"name":"zed_leptonic_MC_y","title":"MC y^{#mu^{+}#mu^{-}} [GeV]","bin":120,"xmin":-3.0,"xmax":3.0},
    #"z_MC_p":{"name":"zed_leptonic_MC_p","title":"MC p^{#mu^{+}#mu^{-}} [GeV]","bin":300,"xmin":0,"xmax":150.0}, 
    #"z_MC_e":{"name":"zed_leptonic_e","title":"MC E^{#mu^{+}#mu^{-}} [GeV]","bin":300,"xmin":0,"xmax":150.0},
    #"leptonic_recoil_m_MC":{"name":"zed_leptonic_recoil_MC_mass","title":"MC M_{recoil} [GeV]","bin":100,"xmin":0,"xmax":200},
    #"leptonic_recoil_m_MC_zoom1":{"name":"zed_leptonic_recoil_MC_mass","title":"MC M_{recoil} [GeV]","bin":240,"xmin":116,"xmax":140},
    #"leptonic_recoil_m_MC_zoom2":{"name":"zed_leptonic_recoil_MC_mass","title":"MC M_{recoil} [GeV]","bin":200,"xmin":120,"xmax":140},
    #"leptonic_recoil_m_MC_zoom3":{"name":"zed_leptonic_recoil_MC_mass","title":"MC M_{recoil} [GeV]","bin":200,"xmin":116,"xmax":136},
    #"leptonic_recoil_m_MC_zoom4":{"name":"zed_leptonic_recoil_MC_mass","title":"MC M_{recoil} [GeV]","bin":40,"xmin":124,"xmax":128},
    #"leptonic_recoil_m_MC_zoom5":{"name":"zed_leptonic_recoil_MC_mass","title":"MC M_{recoil} [GeV]","bin":120,"xmin":128,"xmax":140},
    #"leptonic_recoil_m_MC_zoom6":{"name":"zed_leptonic_recoil_MC_mass","title":"MC M_{recoil} [GeV]","bin":300,"xmin":80,"xmax":110},
    #"leptonic_recoil_m_MC_zoom7":{"name":"zed_leptonic_recoil_MC_mass","title":"MC M_{recoil} [GeV]","bin":200,"xmin":80,"xmax":100},
    #"leptonic_recoil_m_MC_zoom8":{"name":"zed_leptonic_recoil_MC_mass","title":"MC M_{recoil} [GeV]","bin":100,"xmin":86,"xmax":96},
    #"leptonic_recoil_m_MC_zoom9":{"name":"zed_leptonic_recoil_MC_mass","title":"MC M_{recoil} [GeV]","bin":600,"xmin":40,"xmax":160},
    #"leptonic_recoil_m_MC_zoom10":{"name":"zed_leptonic_recoil_MC_mass","title":"MC M_{recoil} [GeV]","bin":400,"xmin":0,"xmax":200},
    #"leptonic_recoil_m_MC_zoom11":{"name":"zed_leptonic_recoil_MC_mass","title":"MC M_{recoil} [GeV]","bin":450,"xmin":110,"xmax":155},
    #"leptonic_recoil_m_MC_zoom12":{"name":"zed_leptonic_recoil_MC_mass","title":"MC M_{recoil} [GeV]","bin":240,"xmin":40,"xmax":160},
    "muon_y":{"name":"selected_muons_y","title":"y_{#mu}","bin":160,"xmin":-4,"xmax":4},
    "muon_pt":{"name":"selected_muons_pt","title":"p_{T}^{#mu} [GeV]","bin":110,"xmin":0,"xmax":110},
    "muon_pt_zoom1":{"name":"selected_muons_pt","title":"p_{T}^{#mu} [GeV]","bin":55,"xmin":0,"xmax":110},
    "muon_p":{"name":"selected_muons_p","title":"p^{#mu} [GeV]","bin":400,"xmin":0,"xmax":200},
    "muon_costheta":{"name":"selected_muons_costheta","title":"cos#theta_{#mu}","bin":200,"xmin":-1,"xmax":1},
    "muon_e":{"name":"selected_muons_e","title":"E_{#mu} [GeV]","bin":200,"xmin":0,"xmax":100},  
    "muon_m":{"name":"selected_muons_m","title":"m_{#mu}","bin":200,"xmin":0,"xmax":100},
    #"Gen_pt_mumu":{"name":"gen_pt_mumu","title":"Gen_level p_{T}^{#mu^{+}#mu^{-}} [GeV]","bin":125,"xmin":0,"xmax":125},
    #"Gen_pt_mumu_025":{"name":"gen_pt_mumu","title":"Gen_level p_{T}^{#mu^{+}#mu^{-}} [GeV]","bin":25,"xmin":0,"xmax":25},
    #"Gen_mass_mumu":{"name":"gen_mass_mumu","title":"Gen_level m_{#mu^{+}#mu^{-}} [GeV]","bin":250,"xmin":0,"xmax":250},
    #"Gen_mass_mumu_Z":{"name":"gen_mass_mumu","title":"Gen_level m_{#mu^{+}#mu^{-}} [GeV]","bin":200,"xmin":80,"xmax":100},
    #"Gen_pt_ZH":{"name":"gen_pt_ZH","title":"Gen_level p_{T}^{ZH} [GeV]","bin":125,"xmin":0,"xmax":125},
    #"Gen_pt_ZH_025":{"name":"gen_pt_ZH","title":"Gen_level p_{T}^{ZH} [GeV]","bin":25,"xmin":0,"xmax":25},
    #"Gen_mass_ZH":{"name":"gen_mass_ZH","title":"Gen_level m_{ZH} [GeV]","bin":250,"xmin":0,"xmax":250},
    #"SF_kkmcp8_wzp6":{"name":"sf_kkmcp8_wzp6","title":"Gen_level sf_kkmc_wzp","bin":50,"xmin":0.8,"xmax":1.3}    
  }

###Number of CPUs to use
NUM_CPUS = 5

###This part is standard to all analyses
import config.runDataFrameFinal as rdf
myana=rdf.runDataFrameFinal(baseDir,procDict,process_list,cut_list,variables)
myana.run(ncpu=NUM_CPUS)
