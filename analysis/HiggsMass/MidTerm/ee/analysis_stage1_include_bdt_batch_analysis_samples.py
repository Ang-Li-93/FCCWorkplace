#Mandatory: List of processes

processList = {
    #signal
    "wzp6_ee_eeH_ecm240":{'chunks':10},
    #singl_mass
    "wzp6_ee_eeH_mH-higher-100MeV_ecm240":{'chunks':20},
    "wzp6_ee_eeH_mH-higher-50MeV_ecm240":{'chunks':20},
    "wzp6_ee_eeH_mH-lower-100MeV_ecm240":{'chunks':20},
    "wzp6_ee_eeH_mH-lower-50MeV_ecm240":{'chunks':20},
    #signal_syst
    "wzp6_ee_eeH_BES-higher-1pc_ecm240":{'chunks':20},
    "wzp6_ee_eeH_BES-lower-1pc_ecm240":{'chunks':20},
    #background
    "p8_ee_WW_ecm240":{'chunks':80},
    "p8_ee_ZZ_ecm240":{'chunks':20},
    "wzp6_ee_ee_Mee_30_150_ecm240":{'chunks':20},
    "wzp6_ee_tautau_ecm240":{'chunks':20},
    #background rare
    "wzp6_egamma_eZ_Zee_ecm240":{'chunks':20},
    "wzp6_gammae_eZ_Zee_ecm240":{'chunks':20},
    "wzp6_gaga_ee_60_ecm240":{'chunks':20},
    "wzp6_gaga_tautau_60_ecm240":{'chunks':20},
    "wzp6_ee_nuenueZ_ecm240":{'chunks':20}
    }
#Mandatory: Production tag when running over EDM4Hep centrally produced events, this points to the yaml files for getting sample statistics
prodTag     = "FCCee/winter2023/IDEA/"

#from userConfig import loc
#Optional: output directory, default is local dir
#outputDir="/afs/cern.ch/work/l/lia/private/FCC/NewWorkFlow/FCCeePhysicsPerformance/case-studies/higgs/mH-recoil/test/flatNtuples_test"
outputDirEos= "/eos/user/l/lia/FCCee/MidTerm/ee/BDT_analysis_samples_full/"
eosType = "eosuser"
#Optional: ncpus, default is 4
nCPUS       = 4

#Optional running on HTCondor, default is False
runBatch    = True
#runBatch    = False
#Optional batch queue name when running on HTCondor, default is workday
batchQueue = "longlunch"

#Optional computing account when running on HTCondor, default is group_u_FCC.local_gen
compGroup = "group_u_FCC.local_gen"

userBatchConfig="/afs/cern.ch/work/l/lia/private/FCC/NewWorkFlow/FCCeePhysicsPerformance/case-studies/higgs/mH-recoil/FCCAnalyses-config/MidTerm/ee/userBatch.Config"
#USER DEFINED CODE
import ROOT
ROOT.gInterpreter.ProcessLine('''
  TMVA::Experimental::RBDT<> bdt("ZH_Recoil_BDT", "/eos/user/l/lia/FCCee/MidTerm/ee/BDT/xgb_bdt.root");
  computeModel1 = TMVA::Experimental::Compute<9, float>(bdt);
''')
#"sel0_MRecoil_Mll_73_120_pTll_05":"  Z_leptonic_m  > 73 &&  Z_leptonic_m  < 120 &&zed_leptonic_recoil_m.size()==1 && zed_leptonic_recoil_m[0]  > 120 &&zed_leptonic_recoil_m[0]  <140 && Z_leptonic_pt  > 5",
#Mandatory: RDFanalysis class where the use defines the operations on the TTree
class RDFanalysis():

    #__________________________________________________________
    #Mandatory: analysers funtion to define the analysers to process, please make sure you return the last dataframe, in this example it is df2
    def analysers(df):
        df2 = (
            df
            #############################################
            ## Alias for muon and MC truth informations##
            #############################################
            .Alias("Lepton0", "Electron#0.index")
            .Alias("MCRecoAssociations0", "MCRecoAssociations#0.index")
            .Alias("MCRecoAssociations1", "MCRecoAssociations#1.index")
            .Alias("Particle0", "Particle#0.index")
            .Alias("Particle1", "Particle#1.index")
            .Alias("Photon0", "Photon#0.index")
            
            # photons
            .Define("photons", "FCCAnalyses::ReconstructedParticle::get(Photon0, ReconstructedParticles)")
            .Define("photons_p", "FCCAnalyses::ReconstructedParticle::get_p(photons)")
            .Define("photons_theta", "FCCAnalyses::ReconstructedParticle::get_theta(photons)")
            .Define("photons_phi", "FCCAnalyses::ReconstructedParticle::get_phi(photons)")
            .Define("photons_no", "FCCAnalyses::ReconstructedParticle::get_n(photons)")
            
            .Define("gen_photons", "HiggsTools::get_photons(Particle)")
            .Define("gen_photons_p", "FCCAnalyses::MCParticle::get_p(gen_photons)")
            .Define("gen_photons_theta", "FCCAnalyses::MCParticle::get_theta(gen_photons)")
            .Define("gen_photons_phi", "FCCAnalyses::MCParticle::get_phi(gen_photons)")
            .Define("gen_photons_no", "FCCAnalyses::MCParticle::get_n(gen_photons)")
            
            # Missing ET
            .Define("cosTheta_miss", "HiggsTools::get_cosTheta(MissingET)") 
            
            # all leptons (bare)
            .Define("leps_all", "FCCAnalyses::ReconstructedParticle::get(Lepton0, ReconstructedParticles)")
            .Define("leps_all_p", "FCCAnalyses::ReconstructedParticle::get_p(leps_all)")
            .Define("leps_all_theta", "FCCAnalyses::ReconstructedParticle::get_theta(leps_all)")
            .Define("leps_all_phi", "FCCAnalyses::ReconstructedParticle::get_phi(leps_all)")
            .Define("leps_all_q", "FCCAnalyses::ReconstructedParticle::get_charge(leps_all)")
            .Define("leps_all_no", "FCCAnalyses::ReconstructedParticle::get_n(leps_all)")
            .Define("leps_all_iso", "HiggsTools::coneIsolation(0.01, 0.5)(leps_all, ReconstructedParticles)") 
            .Define("leps_all_p_gen", "HiggsTools::gen_p_from_reco(leps_all, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
            
            # cuts on leptons
            .Define("leps", "FCCAnalyses::ReconstructedParticle::sel_p(20)(leps_all)")


            .Define("leps_p", "FCCAnalyses::ReconstructedParticle::get_p(leps)")
            .Define("leps_theta", "FCCAnalyses::ReconstructedParticle::get_theta(leps)")
            .Define("leps_phi", "FCCAnalyses::ReconstructedParticle::get_phi(leps)")
            .Define("leps_q", "FCCAnalyses::ReconstructedParticle::get_charge(leps)")
            .Define("leps_no", "FCCAnalyses::ReconstructedParticle::get_n(leps)")
            .Define("leps_iso", "HiggsTools::coneIsolation(0.01, 0.5)(leps, ReconstructedParticles)")
            .Define("leps_sel_iso", "HiggsTools::sel_isol(0.25)(leps, leps_iso)")
            # momentum resolution
            .Define("leps_all_reso_p", "HiggsTools::leptonResolution_p(leps_all, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
            .Define("leps_reso_p", "HiggsTools::leptonResolution_p(leps, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
           
            #.Define("cut0", "0")
            #########
            ### CUT 1: at least a lepton
            #########
            .Filter("leps_no >= 1 && leps_sel_iso.size() > 0")
            #.Define("cut1", "1")
            #.Filter("leps_no >= 1")
            #########
            ### CUT 2 :at least 2 leptons, and build the resonance
            #########
            .Filter("leps_no >= 2 && abs(Sum(leps_q)) < leps_q.size()")
            #.Define("cut2", "2")
            # build the Z resonance based on the available leptons. Returns the best lepton pair compatible with the Z mass and recoil at 125 GeV
            # technically, it returns a ReconstructedParticleData object with index 0 the di-lepton system, index and 2 the leptons of the pair
            #.Define("zbuilder_result", "HiggsTools::resonanceBuilder_mass_recoil(91.2, 125, 0, 240, false)(leps, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0, Particle1)")
            .Define("zbuilder_result", "HiggsTools::resonanceBuilder_mass_recoil(91.2, 125, 0.4, 240, false)(leps, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0, Particle1)")
            .Define("zll", "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result[0]}") # the Z
            .Define("zll_leps", "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result[1],zbuilder_result[2]}") # the leptons
            .Define("zll_m", "FCCAnalyses::ReconstructedParticle::get_mass(zll)[0]")
            .Define("zll_p", "FCCAnalyses::ReconstructedParticle::get_p(zll)[0]")
            .Define("zll_theta", "FCCAnalyses::ReconstructedParticle::get_theta(zll)[0]")
            .Define("zll_phi", "FCCAnalyses::ReconstructedParticle::get_phi(zll)[0]")
          
            # recoil
            .Define("zll_recoil", "FCCAnalyses::ReconstructedParticle::recoilBuilder(240)(zll)")
            .Define("zll_recoil_m", "FCCAnalyses::ReconstructedParticle::get_mass(zll_recoil)[0]")
            .Define("zll_category", "HiggsTools::polarAngleCategorization(0.8, 2.34)(zll_leps)")

            .Define("zll_leps_p", "FCCAnalyses::ReconstructedParticle::get_p(zll_leps)")
            .Define("zll_leps_dR", "HiggsTools::deltaR(zll_leps)")
            .Define("zll_leps_theta", "FCCAnalyses::ReconstructedParticle::get_theta(zll_leps)")
            
            .Define("prompt_electrons", "HiggsTools::whizard_zh_select_prompt_leptons(zll_leps, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0, Particle1)")
            .Define("prompt_electrons_no", "prompt_electrons.size()")
            #.Filter("prompt_muons.size() == 2") 
            # Z leptons informations
            .Define("sorted_zll_leptons",  "HiggsTools::sort_greater_p(zll_leps)")
            .Define("sorted_zll_leptons_p",     "FCCAnalyses::ReconstructedParticle::get_p(sorted_zll_leptons)")
            .Define("sorted_zll_leptons_m",     "FCCAnalyses::ReconstructedParticle::get_mass(sorted_zll_leptons)")
            .Define("sorted_zll_leptons_theta",  "FCCAnalyses::ReconstructedParticle::get_theta(sorted_zll_leptons)")
            .Define("sorted_zll_leptons_phi",  "FCCAnalyses::ReconstructedParticle::get_phi(sorted_zll_leptons)")
            .Define("leading_zll_lepton_p",  "return sorted_zll_leptons_p.at(0)")
            .Define("leading_zll_lepton_m",  "return sorted_zll_leptons_m.at(0)")
            .Define("leading_zll_lepton_theta",  "return sorted_zll_leptons_theta.at(0)")
            .Define("leading_zll_lepton_phi",  "return sorted_zll_leptons_phi.at(0)")
            .Define("subleading_zll_lepton_p",  "return sorted_zll_leptons_p.at(1)")
            .Define("subleading_zll_lepton_m",  "return sorted_zll_leptons_m.at(1)")
            .Define("subleading_zll_lepton_theta",  "return sorted_zll_leptons_theta.at(1)")
            .Define("subleading_zll_lepton_phi",  "return sorted_zll_leptons_phi.at(1)")
           
            .Define("zll_Leptons_acolinearity", "HiggsTools::acolinearity(sorted_zll_leptons)")
            .Define("zll_Leptons_acoplanarity", "HiggsTools::acoplanarity(sorted_zll_leptons)") 
            .Define("zll_leptons_acolinearity", "if(zll_Leptons_acolinearity.size()>0) return zll_Leptons_acolinearity.at(0); else return -std::numeric_limits<float>::max()") 
            .Define("zll_leptons_acoplanarity", "if(zll_Leptons_acoplanarity.size()>0) return zll_Leptons_acoplanarity.at(0); else return -std::numeric_limits<float>::max()") 
           
            #Higgsstrahlungness
            .Define("H", "HiggsTools::Higgsstrahlungness(zll_m, zll_recoil_m)")
            #.Filter("zll_m > 73 && zll_m < 120") 
            #.Define("cut3", "3")
            #.Filter("zll_p > 5")
            #.Define("cut4", "4")
            #.Filter("zll_recoil_m < 140 && zll_recoil_m > 120")
            #.Define("cut5", "5")
            ###
            #Define MVA 
            ###
            .Define("MVAVec", ROOT.computeModel1, (
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
            .Define("BDTscore", "MVAVec.at(0)")
       
            ########################
            # Systematics
            ########################

            # lepton momentum scale
            #scaleup
            .Define("leps_scaleup", "HiggsTools::lepton_momentum_scale(1e-5)(leps)")
            .Define("zbuilder_result_scaleup", "HiggsTools::resonanceBuilder_mass_recoil(91.2, 125, 0.4, 240, false)(leps_scaleup, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0, Particle1)")
            .Define("zll_scaleup", "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result_scaleup[0]}")
            .Define("zll_recoil_scaleup", "FCCAnalyses::ReconstructedParticle::recoilBuilder(240)(zll_scaleup)")
            .Define("zll_recoil_m_scaleup", "FCCAnalyses::ReconstructedParticle::get_mass(zll_recoil_scaleup)[0]")
            .Define("zll_leps_scaleup", "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result_scaleup[1],zbuilder_result_scaleup[2]}") 

            .Define("zll_m_scaleup", "FCCAnalyses::ReconstructedParticle::get_mass(zll_scaleup)[0]")
            .Define("zll_p_scaleup", "FCCAnalyses::ReconstructedParticle::get_p(zll_scaleup)[0]")
            .Define("zll_theta_scaleup", "FCCAnalyses::ReconstructedParticle::get_theta(zll_scaleup)[0]")
            .Define("zll_phi_scaleup", "FCCAnalyses::ReconstructedParticle::get_phi(zll_scaleup)[0]")
            .Define("zll_category_scaleup", "HiggsTools::polarAngleCategorization(0.8, 2.34)(zll_leps_scaleup)")

            # Z leptons informations
            .Define("sorted_zll_leptons_scaleup",  "HiggsTools::sort_greater_p(zll_leps_scaleup)")
            .Define("sorted_zll_leptons_p_scaleup",     "FCCAnalyses::ReconstructedParticle::get_p(sorted_zll_leptons_scaleup)")
            .Define("sorted_zll_leptons_m_scaleup",     "FCCAnalyses::ReconstructedParticle::get_mass(sorted_zll_leptons_scaleup)")
            .Define("sorted_zll_leptons_theta_scaleup",  "FCCAnalyses::ReconstructedParticle::get_theta(sorted_zll_leptons_scaleup)")
            .Define("sorted_zll_leptons_phi_scaleup",  "FCCAnalyses::ReconstructedParticle::get_phi(sorted_zll_leptons_scaleup)")
            .Define("leading_zll_lepton_p_scaleup",  "return sorted_zll_leptons_p_scaleup.at(0)")
            .Define("leading_zll_lepton_m_scaleup",  "return sorted_zll_leptons_m_scaleup.at(0)")
            .Define("leading_zll_lepton_theta_scaleup",  "return sorted_zll_leptons_theta_scaleup.at(0)")
            .Define("leading_zll_lepton_phi_scaleup",  "return sorted_zll_leptons_phi_scaleup.at(0)")
            .Define("subleading_zll_lepton_p_scaleup",  "return sorted_zll_leptons_p_scaleup.at(1)")
            .Define("subleading_zll_lepton_m_scaleup",  "return sorted_zll_leptons_m_scaleup.at(1)")
            .Define("subleading_zll_lepton_theta_scaleup",  "return sorted_zll_leptons_theta_scaleup.at(1)")
            .Define("subleading_zll_lepton_phi_scaleup",  "return sorted_zll_leptons_phi_scaleup.at(1)")
           
            .Define("zll_Leptons_acolinearity_scaleup", "HiggsTools::acolinearity(sorted_zll_leptons_scaleup)")
            .Define("zll_Leptons_acoplanarity_scaleup", "HiggsTools::acoplanarity(sorted_zll_leptons_scaleup)") 
            .Define("zll_leptons_acolinearity_scaleup", "if(zll_Leptons_acolinearity_scaleup.size()>0) return zll_Leptons_acolinearity_scaleup.at(0); else return -std::numeric_limits<float>::max()") 
            .Define("zll_leptons_acoplanarity_scaleup", "if(zll_Leptons_acoplanarity_scaleup.size()>0) return zll_Leptons_acoplanarity_scaleup.at(0); else return -std::numeric_limits<float>::max()") 
            
            .Define("MVAVec_scaleup", ROOT.computeModel1, (
                                                    #leptons
                                                    "leading_zll_lepton_p_scaleup",
                                                    "leading_zll_lepton_theta_scaleup",
                                                    "subleading_zll_lepton_p_scaleup",
                                                    "subleading_zll_lepton_theta_scaleup",
                                                    "zll_leptons_acolinearity_scaleup",
                                                    "zll_leptons_acoplanarity_scaleup",
                                                    #Zed
                                                    "zll_m_scaleup",
                                                    "zll_p_scaleup",
                                                    "zll_theta_scaleup"
                                                    #Higgsstrahlungness
                                                    #"H"
                                                    ))
            .Define("BDTscore_scaleup", "MVAVec_scaleup.at(0)") 

            #scaledw
            .Define("leps_scaledw", "HiggsTools::lepton_momentum_scale(1e-5)(leps)")
            .Define("zbuilder_result_scaledw", "HiggsTools::resonanceBuilder_mass_recoil(91.2, 125, 0.4, 240, false)(leps_scaledw, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0, Particle1)")
            .Define("zll_scaledw", "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result_scaledw[0]}")
            .Define("zll_recoil_scaledw", "FCCAnalyses::ReconstructedParticle::recoilBuilder(240)(zll_scaledw)")
            .Define("zll_recoil_m_scaledw", "FCCAnalyses::ReconstructedParticle::get_mass(zll_recoil_scaledw)[0]")
            .Define("zll_leps_scaledw", "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result_scaledw[1],zbuilder_result_scaledw[2]}") 

            .Define("zll_m_scaledw", "FCCAnalyses::ReconstructedParticle::get_mass(zll_scaledw)[0]")
            .Define("zll_p_scaledw", "FCCAnalyses::ReconstructedParticle::get_p(zll_scaledw)[0]")
            .Define("zll_theta_scaledw", "FCCAnalyses::ReconstructedParticle::get_theta(zll_scaledw)[0]")
            .Define("zll_phi_scaledw", "FCCAnalyses::ReconstructedParticle::get_phi(zll_scaledw)[0]")

            .Define("zll_category_scaledw", "HiggsTools::polarAngleCategorization(0.8, 2.34)(zll_leps_scaledw)")

            # Z leptons informations
            #scaledw
            .Define("sorted_zll_leptons_scaledw",  "HiggsTools::sort_greater_p(zll_leps_scaledw)")
            .Define("sorted_zll_leptons_p_scaledw",     "FCCAnalyses::ReconstructedParticle::get_p(sorted_zll_leptons_scaledw)")
            .Define("sorted_zll_leptons_m_scaledw",     "FCCAnalyses::ReconstructedParticle::get_mass(sorted_zll_leptons_scaledw)")
            .Define("sorted_zll_leptons_theta_scaledw",  "FCCAnalyses::ReconstructedParticle::get_theta(sorted_zll_leptons_scaledw)")
            .Define("sorted_zll_leptons_phi_scaledw",  "FCCAnalyses::ReconstructedParticle::get_phi(sorted_zll_leptons_scaledw)")
            .Define("leading_zll_lepton_p_scaledw",  "return sorted_zll_leptons_p_scaledw.at(0)")
            .Define("leading_zll_lepton_m_scaledw",  "return sorted_zll_leptons_m_scaledw.at(0)")
            .Define("leading_zll_lepton_theta_scaledw",  "return sorted_zll_leptons_theta_scaledw.at(0)")
            .Define("leading_zll_lepton_phi_scaledw",  "return sorted_zll_leptons_phi_scaledw.at(0)")
            .Define("subleading_zll_lepton_p_scaledw",  "return sorted_zll_leptons_p_scaledw.at(1)")
            .Define("subleading_zll_lepton_m_scaledw",  "return sorted_zll_leptons_m_scaledw.at(1)")
            .Define("subleading_zll_lepton_theta_scaledw",  "return sorted_zll_leptons_theta_scaledw.at(1)")
            .Define("subleading_zll_lepton_phi_scaledw",  "return sorted_zll_leptons_phi_scaledw.at(1)")
           
            .Define("zll_Leptons_acolinearity_scaledw", "HiggsTools::acolinearity(sorted_zll_leptons_scaledw)")
            .Define("zll_Leptons_acoplanarity_scaledw", "HiggsTools::acoplanarity(sorted_zll_leptons_scaledw)") 
            .Define("zll_leptons_acolinearity_scaledw", "if(zll_Leptons_acolinearity_scaledw.size()>0) return zll_Leptons_acolinearity_scaledw.at(0); else return -std::numeric_limits<float>::max()") 
            .Define("zll_leptons_acoplanarity_scaledw", "if(zll_Leptons_acoplanarity_scaledw.size()>0) return zll_Leptons_acoplanarity_scaledw.at(0); else return -std::numeric_limits<float>::max()") 
            
            .Define("MVAVec_scaledw", ROOT.computeModel1, (
                                                    #leptons
                                                    "leading_zll_lepton_p_scaledw",
                                                    "leading_zll_lepton_theta_scaledw",
                                                    "subleading_zll_lepton_p_scaledw",
                                                    "subleading_zll_lepton_theta_scaledw",
                                                    "zll_leptons_acolinearity_scaledw",
                                                    "zll_leptons_acoplanarity_scaledw",
                                                    #Zed
                                                    "zll_m_scaledw",
                                                    "zll_p_scaledw",
                                                    "zll_theta_scaledw"
                                                    #Higgsstrahlungness
                                                    #"H"
                                                    ))
            .Define("BDTscore_scaledw", "MVAVec_scaledw.at(0)")  
            
            # sqrt uncertainty
            .Define("zll_recoil_sqrtsup", "FCCAnalyses::ReconstructedParticle::recoilBuilder(240.002)(zll)")
            .Define("zll_recoil_sqrtsdw", "FCCAnalyses::ReconstructedParticle::recoilBuilder(239.998)(zll)")
            .Define("zll_recoil_m_sqrtsup", "FCCAnalyses::ReconstructedParticle::get_mass(zll_recoil_sqrtsup)[0]")
            .Define("zll_recoil_m_sqrtsdw", "FCCAnalyses::ReconstructedParticle::get_mass(zll_recoil_sqrtsdw)[0]")
        
        )
        return df2

    #__________________________________________________________
    #Mandatory: output function, please make sure you return the branchlist as a python list
    def output():
        branchList = [
            #Reconstructed Particle
            #leptons
            "leading_zll_lepton_p",  
            "leading_zll_lepton_m",  
            "leading_zll_lepton_theta",                    
            "leading_zll_lepton_phi",
            "subleading_zll_lepton_p",
            "subleading_zll_lepton_m",
            "subleading_zll_lepton_theta",
            "subleading_zll_lepton_phi",
            "zll_leptons_acolinearity",
            "zll_leptons_acoplanarity",
            #Zed
            "zll_m",
            "zll_p",
            "zll_theta",
            "zll_phi",
            #Recoil
            "zll_recoil_m",
            #BDT Score
            "BDTscore",
            #Category
            "zll_category",

            #scaleup
            "leading_zll_lepton_p_scaleup",  
            "leading_zll_lepton_m_scaleup",  
            "leading_zll_lepton_theta_scaleup",                    
            "leading_zll_lepton_phi_scaleup",
            "subleading_zll_lepton_p_scaleup",
            "subleading_zll_lepton_m_scaleup",
            "subleading_zll_lepton_theta_scaleup",
            "subleading_zll_lepton_phi_scaleup",
            "zll_leptons_acolinearity_scaleup",
            "zll_leptons_acoplanarity_scaleup",
            #Zed
            "zll_m_scaleup",
            "zll_p_scaleup",
            "zll_theta_scaleup",
            "zll_phi_scaleup",
            #Recoil
            "zll_recoil_m_scaleup",
            #BDT Score
            "BDTscore_scaleup",
            #Category
            "zll_category_scaleup",

            #scaledw
            "leading_zll_lepton_p_scaledw",  
            "leading_zll_lepton_m_scaledw",  
            "leading_zll_lepton_theta_scaledw",                    
            "leading_zll_lepton_phi_scaledw",
            "subleading_zll_lepton_p_scaledw",
            "subleading_zll_lepton_m_scaledw",
            "subleading_zll_lepton_theta_scaledw",
            "subleading_zll_lepton_phi_scaledw",
            "zll_leptons_acolinearity_scaledw",
            "zll_leptons_acoplanarity_scaledw",
            #Zed
            "zll_m_scaledw",
            "zll_p_scaledw",
            "zll_theta_scaledw",
            "zll_phi_scaledw",
            #Recoil
            "zll_recoil_m_scaledw",
            #BDT Score
            "BDTscore_scaledw",
            #Category
            "zll_category_scaledw", 
            
            "zll_recoil_m_sqrtsup",
            "zll_recoil_m_sqrtsdw", 
    
            
            #missing Information
            "cosTheta_miss",
            #Higgsstrahlungness
            "H",
            #number of leptons
            "leps_no"
        ]
        return branchList
