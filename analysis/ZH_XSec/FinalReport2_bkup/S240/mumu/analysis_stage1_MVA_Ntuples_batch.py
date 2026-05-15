import os
import importlib
import utils

# Define final_state and ecm
final_state = "mumu"
ecm = "240"

# Load userConfig and replace placeholders
userConfig = importlib.import_module("userConfig")
userConfig = utils.replace_placeholders(userConfig, final_state, ecm)

# Now you can use userConfig.loc and userConfig.mode_names with the actual values of final_state and ecm
outputDir = userConfig.loc.TRAIN
outputDirEos = userConfig.loc.EOS

#Mandatory: List of processes
processList = {
    f'wzp6_ee_{final_state}H_ecm{ecm}':{'chunks':10},
    #f"p8_ee_WW_{final_state}_ecm{ecm}":{'chunks':10},
    #f"p8_ee_ZZ_ecm{ecm}":{'chunks':10},
    ##f"wzp6_ee_{final_state}_Mee_30_150_ecm240":{'chunks':10},
    #f"wzp6_egamma_eZ_Z{final_state}_ecm{ecm}":{'chunks':10},
    #f"wzp6_gammae_eZ_Z{final_state}_ecm{ecm}":{'chunks':10},
    #f"wzp6_gaga_{final_state}_60_ecm{ecm}":{'chunks':10},
    #f'wzp6_ee_{final_state}H_ecm{ecm}':{'fraction':0.1},
}

#if final_state == "mumu":
#    processList.update({
#        f"wzp6_ee_mumu_ecm{ecm}":{'chunks':10}
#    })
#elif final_state == "ee":
#    processList.update({
#        f"wzp6_ee_ee_Mee_30_150_ecm{ecm}":{'chunks':10}
#    })
#Mandatory: Production tag when running over EDM4Hep centrally produced events, this points to the yaml files for getting sample statistics
prodTag     = "FCCee/winter2023_training/IDEA/"

#Optional: output directory, default is local dir
eosType = "eosuser"
#Optional: ncpus, default is 4
nCPUS       = 10

#Optional running on HTCondor, default is False
runBatch    = True
#runBatch    = False
#Optional batch queue name when running on HTCondor, default is workday
batchQueue = "longlunch"

#Optional computing account when running on HTCondor, default is group_u_FCC.local_gen
compGroup = "group_u_FCC.local_gen"

#userBatchConfig="/afs/cern.ch/work/l/lia/private/FCC/NewWorkFlow/FCCeePhysicsPerformance/case-studies/higgs/mH-recoil/FCCAnalyses-config/Winter2023/userBatch.Config"
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
        df2 = df
        if final_state == "mumu":
            df2 = df2.Alias("Lepton0", "Muon#0.index")
        elif final_state == "ee":
            df2 = df2.Alias("Lepton0", "Electron#0.index")
        else:
            raise ValueError(f"final_state {final_state} not supported")
        df2 = df2.Alias("MCRecoAssociations0", "MCRecoAssociations#0.index")
        df2 = df2.Alias("MCRecoAssociations1", "MCRecoAssociations#1.index")
        df2 = df2.Alias("Particle0", "Particle#0.index")
        df2 = df2.Alias("Particle1", "Particle#1.index")
        df2 = df2.Alias("Photon0", "Photon#0.index")
        
        # photons
        df2 = df2.Define("photons", "FCCAnalyses::ReconstructedParticle::get(Photon0, ReconstructedParticles)")
        df2 = df2.Define("photons_p", "FCCAnalyses::ReconstructedParticle::get_p(photons)")
        df2 = df2.Define("photons_theta", "FCCAnalyses::ReconstructedParticle::get_theta(photons)")
        df2 = df2.Define("photons_phi", "FCCAnalyses::ReconstructedParticle::get_phi(photons)")
        df2 = df2.Define("photons_no", "FCCAnalyses::ReconstructedParticle::get_n(photons)")
        
        df2 = df2.Define("gen_photons", "HiggsTools::get_photons(Particle)")
        df2 = df2.Define("gen_photons_p", "FCCAnalyses::MCParticle::get_p(gen_photons)")
        df2 = df2.Define("gen_photons_theta", "FCCAnalyses::MCParticle::get_theta(gen_photons)")
        df2 = df2.Define("gen_photons_phi", "FCCAnalyses::MCParticle::get_phi(gen_photons)")
        df2 = df2.Define("gen_photons_no", "FCCAnalyses::MCParticle::get_n(gen_photons)")
        
        # Missing ET
        df2 = df2.Define("cosTheta_miss", "HiggsTools::get_cosTheta(MissingET)") 
        
        # all leptons (bare)
        df2 = df2.Define("leps_all", "FCCAnalyses::ReconstructedParticle::get(Lepton0, ReconstructedParticles)")
        df2 = df2.Define("leps_all_p", "FCCAnalyses::ReconstructedParticle::get_p(leps_all)")
        df2 = df2.Define("leps_all_theta", "FCCAnalyses::ReconstructedParticle::get_theta(leps_all)")
        df2 = df2.Define("leps_all_phi", "FCCAnalyses::ReconstructedParticle::get_phi(leps_all)")
        df2 = df2.Define("leps_all_q", "FCCAnalyses::ReconstructedParticle::get_charge(leps_all)")
        df2 = df2.Define("leps_all_no", "FCCAnalyses::ReconstructedParticle::get_n(leps_all)")
        df2 = df2.Define("leps_all_iso", "HiggsTools::coneIsolation(0.01, 0.5)(leps_all, ReconstructedParticles)") 
        df2 = df2.Define("leps_all_p_gen", "HiggsTools::gen_p_from_reco(leps_all, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
        
        # cuts on leptons
        df2 = df2.Define("leps", "FCCAnalyses::ReconstructedParticle::sel_p(20)(leps_all)")
        df2 = df2.Define("leps_p", "FCCAnalyses::ReconstructedParticle::get_p(leps)")
        df2 = df2.Define("leps_theta", "FCCAnalyses::ReconstructedParticle::get_theta(leps)")
        df2 = df2.Define("leps_phi", "FCCAnalyses::ReconstructedParticle::get_phi(leps)")
        df2 = df2.Define("leps_q", "FCCAnalyses::ReconstructedParticle::get_charge(leps)")
        df2 = df2.Define("leps_no", "FCCAnalyses::ReconstructedParticle::get_n(leps)")
        df2 = df2.Define("leps_iso", "HiggsTools::coneIsolation(0.01, 0.5)(leps, ReconstructedParticles)")
        df2 = df2.Define("leps_sel_iso", "HiggsTools::sel_isol(0.25)(leps, leps_iso)")
        df2 = df2.Define("leps_all_reso_p", "HiggsTools::leptonResolution_p(leps_all, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
        df2 = df2.Define("leps_reso_p", "HiggsTools::leptonResolution_p(leps, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
        
        # build the Z resonance and recoil using MC information from the selected muons
        df2 = df2.Define("zed_leptonic_MC", "HiggsTools::resonanceZBuilder2(91, true)(leps, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
        df2 = df2.Define("zed_leptonic_m_MC", "FCCAnalyses::ReconstructedParticle::get_mass(zed_leptonic_MC)")
        df2 = df2.Define("zed_leptonic_recoil_MC", "FCCAnalyses::ReconstructedParticle::recoilBuilder(240)(zed_leptonic_MC)")
        df2 = df2.Define("zed_leptonic_recoil_m_MC", "FCCAnalyses::ReconstructedParticle::get_mass(zed_leptonic_recoil_MC)")
        
        # gen analysis
        df2 = df2.Filter("leps_no >= 1 && leps_sel_iso.size() > 0")
        df2 = df2.Filter("leps_no >= 2 && abs(Sum(leps_q)) < leps_q.size()")
        df2 = df2.Define("zbuilder_result_Hll", "HiggsTools::resonanceBuilder_mass_recoil2(125, 91.2, 0.4, 240, false)(leps, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0, Particle1)")
        df2 = df2.Define("zll_Hll", "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result_Hll[0]}") # the Z
        df2 = df2.Define("zll_Hll_m", "FCCAnalyses::ReconstructedParticle::get_mass(zll_Hll)[0]")
        df2 = df2.Define("zll_leps_Hll", "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result_Hll[1],zbuilder_result_Hll[2]}") # the leptons
        df2 = df2.Define("zll_leps_dummy", "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{}") # the leptons
        df2 = df2.Define("leps_to_remove", "return (zll_Hll_m > (125-3) && zll_Hll_m < (125+3)) ? zll_leps_Hll : zll_leps_dummy")
        df2 = df2.Define("leps_good", "FCCAnalyses::ReconstructedParticle::remove(leps, leps_to_remove)") 
        df2 = df2.Filter("leps_no >= 2 && abs(Sum(leps_q)) < leps_q.size()") 
        df2 = df2.Define("zbuilder_result", "HiggsTools::resonanceBuilder_mass_recoil2(91.2, 125, 0.4, 240, false)(leps_good, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0, Particle1)")
        df2 = df2.Define("zll", "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result[0]}") # the Z
        df2 = df2.Define("zll_leps", "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result[1],zbuilder_result[2]}") # the leptons
        df2 = df2.Define("zll_m", "FCCAnalyses::ReconstructedParticle::get_mass(zll)[0]")
        df2 = df2.Define("zll_p", "FCCAnalyses::ReconstructedParticle::get_p(zll)[0]")
        df2 = df2.Define("zll_theta", "FCCAnalyses::ReconstructedParticle::get_theta(zll)[0]")
        df2 = df2.Define("zll_phi", "FCCAnalyses::ReconstructedParticle::get_phi(zll)[0]") 
        
        # recoil
        df2 = df2.Define("zll_recoil", "FCCAnalyses::ReconstructedParticle::recoilBuilder(240)(zll)")
        df2 = df2.Define("zll_recoil_m", "FCCAnalyses::ReconstructedParticle::get_mass(zll_recoil)[0]")
        
        # Z leptons informations
        df2 = df2.Define("sorted_zll_leptons", "HiggsTools::sort_greater_p(zll_leps)")
        df2 = df2.Define("sorted_zll_leptons_p", "FCCAnalyses::ReconstructedParticle::get_p(sorted_zll_leptons)")
        df2 = df2.Define("sorted_zll_leptons_m", "FCCAnalyses::ReconstructedParticle::get_mass(sorted_zll_leptons)")
        df2 = df2.Define("sorted_zll_leptons_theta", "FCCAnalyses::ReconstructedParticle::get_theta(sorted_zll_leptons)")
        df2 = df2.Define("sorted_zll_leptons_phi", "FCCAnalyses::ReconstructedParticle::get_phi(sorted_zll_leptons)")
        df2 = df2.Define("leading_zll_lepton_p", "return sorted_zll_leptons_p.at(0)")
        df2 = df2.Define("leading_zll_lepton_m", "return sorted_zll_leptons_m.at(0)")
        df2 = df2.Define("leading_zll_lepton_theta", "return sorted_zll_leptons_theta.at(0)")
        df2 = df2.Define("leading_zll_lepton_phi", "return sorted_zll_leptons_phi.at(0)")
        df2 = df2.Define("subleading_zll_lepton_p", "return sorted_zll_leptons_p.at(1)")
        df2 = df2.Define("subleading_zll_lepton_m", "return sorted_zll_leptons_m.at(1)")
        df2 = df2.Define("subleading_zll_lepton_theta", "return sorted_zll_leptons_theta.at(1)")
        df2 = df2.Define("subleading_zll_lepton_phi", "return sorted_zll_leptons_phi.at(1)")
        
        df2 = df2.Define("zll_Leptons_acolinearity", "HiggsTools::acolinearity(sorted_zll_leptons)")
        df2 = df2.Define("zll_Leptons_acoplanarity", "HiggsTools::acoplanarity(sorted_zll_leptons)") 
        df2 = df2.Define("zll_leptons_acolinearity", "if(zll_Leptons_acolinearity.size()>0) return zll_Leptons_acolinearity.at(0); else return -std::numeric_limits<float>::max()") 
        df2 = df2.Define("zll_leptons_acoplanarity", "if(zll_Leptons_acoplanarity.size()>0) return zll_Leptons_acoplanarity.at(0); else return -std::numeric_limits<float>::max()") 
        
        # Higgsstrahlungness
        df2 = df2.Define("H", "HiggsTools::Higgsstrahlungness(zll_m, zll_recoil_m)")
        df2 = df2.Filter("zll_m > 86 && zll_m < 96") 
        df2 = df2.Filter("zll_p > 20 && zll_p < 70")
        df2 = df2.Filter("zll_recoil_m < 150 && zll_recoil_m > 100")
        
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
