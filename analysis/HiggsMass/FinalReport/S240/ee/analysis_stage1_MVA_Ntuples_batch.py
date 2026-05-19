#Mandatory: List of processes
processList = {
    'wzp6_ee_eeH_ecm240':{'chunks':10},
    "p8_ee_WW_ee_ecm240":{'chunks':10},
    "p8_ee_ZZ_ecm240":{'chunks':10},
    "wzp6_ee_ee_Mee_30_150_ecm240":{'chunks':10},
    "wzp6_egamma_eZ_Zee_ecm240":{'chunks':10},
    "wzp6_gammae_eZ_Zee_ecm240":{'chunks':10},
    "wzp6_gaga_ee_60_ecm240":{'chunks':10},
}

#Mandatory: Production tag when running over EDM4Hep centrally produced events, this points to the yaml files for getting sample statistics
prodTag     = "FCCee/winter2023_training/IDEA/"

#from userConfig import loc
#Optional: output directory, default is local dir
#outputDir="/afs/cern.ch/work/l/lia/private/FCC/NewWorkFlow/FCCeePhysicsPerformance/case-studies/higgs/mH-recoil/ZH_mumu_recoil_batch/stage1/flatNtuples_test"
outputDirEos= "/eos/user/l/lia/FCCee/MidTerm/ee/MVAInputs/"
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
ROOT.gInterpreter.Declare("""
bool Selection(ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in){
    //at least one muon + and one muon - in each event
    int n_muon_plus = 0;
	int n_muon_minus = 0;
	int n = in.size();
	for (int i = 0; i < n; ++i) {
	    if (in[i].charge == 1.0){
	        ++n_muon_plus;
	    }
	    else if (in[i].charge == -1.0){
	        ++n_muon_minus;
	    }
	}
	if (n_muon_plus >= 1 && n_muon_minus >= 1){
		return true;
	}
    else{
        return false;
    }
}
""")
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
            #.Alias("Lepton0", "AllMuon#0.index")
            #.Alias("Lepton0", "Muon#0.index")
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
            #df = df.Define("selected_muons", "FCCAnalyses::excluded_Higgs_decays(muons, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0, Particle1)") # was 10
            #.Define("leps_sel_p", "FCCAnalyses::ReconstructedParticle::sel_p(20)(leps_all)")
            #.Define("leps_sel_iso", "FCCAnalyses::sel_iso(99)(leps_sel_p, leps_all_iso)") # 0.25
            #.Define("leps_sel_iso", "HiggsTools::sel_isol(0.25)(leps_all, leps_all_iso)")
            #.Alias("leps", "leps_sel_iso") 
            #.Alias("leps", "leps_all") 
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
            
            # build the Z resonance and recoil using MC information from the selected muons
            .Define("zed_leptonic_MC", "HiggsTools::resonanceZBuilder2(91, true)(leps, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
            .Define("zed_leptonic_m_MC", "FCCAnalyses::ReconstructedParticle::get_mass(zed_leptonic_MC)")
            .Define("zed_leptonic_recoil_MC",  "FCCAnalyses::ReconstructedParticle::recoilBuilder(240)(zed_leptonic_MC)")
            .Define("zed_leptonic_recoil_m_MC", "FCCAnalyses::ReconstructedParticle::get_mass(zed_leptonic_recoil_MC)")
            
            # gen analysis
            #.Define("higgs_MC", "HiggsTools::gen_sel_pdgIDInt(25,false)(Particle)")
            #.Define("daughter_higgs", "HiggsTools::gen_decay_list(higgs_MC, Particle, Particle1)")
            #.Define("daughter_higgs_collapsed", "daughter_higgs.size()>1 ? ((abs(daughter_higgs[0])+abs(daughter_higgs[1]))*0.5) : -1000 ")
           
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
            #.Define("zll_category", "FCCAnalyses::polarAngleCategorization(0.8, 2.34)(zll_leps)")
            
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
            .Filter("zll_m > 86 && zll_m < 96") 
            #.Define("cut3", "3")
            .Filter("zll_p > 20 && zll_p <70")
            #.Define("cut4", "4")
            .Filter("zll_recoil_m < 140 && zll_recoil_m > 120")
            #.Define("cut5", "5")
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
            #missing Information
            "cosTheta_miss",
            #Higgsstrahlungness
            "H",
            ##Cutflow
            #"cut0",
            #"cut1",
            #"cut2",
            #"cut3",
            #"cut4",
            #"cut5"
        ]
        return branchList
