#Mandatory: List of processes

import os

os.environ["FCCDICTSDIR"] = "/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/HiggsInvisible/lia/FCCDicts/"
processList = {
    #signal
    "wzp6_ee_mumuH_HZZ4nu_ecm240":{'chunks':10},
    "wzp6_ee_nunuH_HZZ_mumununu_ecm240":{"chunks":10},
    "wzp6_ee_nunuH_HWW_munumunu_ecm240":{"chunks":10} 
    }
#Mandatory: Production tag when running over EDM4Hep centrally produced events, this points to the yaml files for getting sample statistics
#prodTag     = "/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/HiggsInvisible/lia/FCCDicts/"
prodTag     = "FCCee/winter2023/IDEA/"
#from userConfig import loc
outputDir="/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/HiggsInvisible/lia/MC_Validation/stage1/"
#outputDirEos= "/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/HiggsInvisible/lia/MC_Validation/stage1"
#eosType = "eosuser"
#Optional: ncpus, default is 4
nCPUS       = 4

#Optional running on HTCondor, default is False
#runBatch    = True
runBatch    = False
#Optional batch queue name when running on HTCondor, default is workday
batchQueue = "longlunch"

#Optional computing account when running on HTCondor, default is group_u_FCC.local_gen
compGroup = "group_u_FCC.local_gen"



#from addons.ONNXRuntime.python.jetFlavourHelper import JetFlavourHelper
#from addons.FastJet.python.jetClusteringHelper import ExclusiveJetClusteringHelper

#jetFlavourHelper = None
#jetClusteringHelper = None


def analysis_sequence(df):    
        df = (
            df
            #############################################
            ## Alias for muon and electron and MC truth informations##
            #############################################
            .Alias("Muon0", "Muon#0.index")
            .Alias("Electron0", "Electron#0.index")
            .Alias("MCRecoAssociations0", "MCRecoAssociations#0.index")
            .Alias("MCRecoAssociations1", "MCRecoAssociations#1.index")
            .Alias("Particle0", "Particle#0.index")#parent
            .Alias("Particle1", "Particle#1.index")#daughter

            #############################################
            ## Define the collections of muons ##
            #############################################
            .Define("muons",  "FCCAnalyses::ReconstructedParticle::get(Muon0, ReconstructedParticles)")
            .Define("muons_p", "FCCAnalyses::ReconstructedParticle::get_p(muons)")
            .Define("muons_theta", "FCCAnalyses::ReconstructedParticle::get_theta(muons)")
            .Define("muons_phi", "FCCAnalyses::ReconstructedParticle::get_phi(muons)")
            .Define("muons_q", "FCCAnalyses::ReconstructedParticle::get_charge(muons)")
            .Define("muons_no", "FCCAnalyses::ReconstructedParticle::get_n(muons)")
            
            #############################################
            ## Define the collections of electrons ##
            #############################################
            .Define("electrons",  "FCCAnalyses::ReconstructedParticle::get(Electron0, ReconstructedParticles)")
            .Define("electrons_p", "FCCAnalyses::ReconstructedParticle::get_p(electrons)")
            .Define("electrons_theta", "FCCAnalyses::ReconstructedParticle::get_theta(electrons)")
            .Define("electrons_phi", "FCCAnalyses::ReconstructedParticle::get_phi(electrons)")
            .Define("electrons_q", "FCCAnalyses::ReconstructedParticle::get_charge(electrons)")
            .Define("electrons_no", "FCCAnalyses::ReconstructedParticle::get_n(electrons)")

            .Define("higgs_MC", "HiggsTools::gen_sel_pdgIDInt(25,false)(Particle)")
            .Define("daughter_higgs", "HiggsTools::gen_decay_list(higgs_MC, Particle, Particle1)")
            .Define("daughter_higgs_no", "daughter_higgs.size()")
            .Define("daughter_higgs_0_pid", "daughter_higgs.size()>0 ? daughter_higgs[0] : -1000")
            .Define("daughter_higgs_1_pid", "daughter_higgs.size()>1 ? daughter_higgs[1] : -1000")
            .Define("daughter_higgs_2_pid", "daughter_higgs.size()>2 ? daughter_higgs[2] : -1000")
            .Define("daughter_higgs_3_pid", "daughter_higgs.size()>3 ? daughter_higgs[3] : -1000")

            .Define("Z_MC", "HiggsTools::gen_sel_pdgIDInt(23,false)(Particle)")
            .Define("daughter_Z", "HiggsTools::gen_decay_list(Z_MC, Particle, Particle1)")
            .Define("daughter_Z_no", "daughter_Z.size()")
            .Define("daughter_Z_0_pid", "daughter_Z.size()>0 ? daughter_Z[0] : -1000")
            .Define("daughter_Z_1_pid", "daughter_Z.size()>1 ? daughter_Z[1] : -1000")
            .Define("daughter_Z_2_pid", "daughter_Z.size()>2 ? daughter_Z[2] : -1000")
            .Define("daughter_Z_3_pid", "daughter_Z.size()>3 ? daughter_Z[3] : -1000")
            .Define("daughter_Z_4_pid", "daughter_Z.size()>4 ? daughter_Z[4] : -1000")
            .Define("daughter_Z_5_pid", "daughter_Z.size()>5 ? daughter_Z[5] : -1000")


            .Define("Wp_MC", "HiggsTools::gen_sel_pdgIDInt(24,false)(Particle)")
            .Define("daughter_Wp", "HiggsTools::gen_decay_list(Wp_MC, Particle, Particle1)")
            .Define("daughter_Wp_no", "daughter_Wp.size()")
            .Define("daughter_Wp_0_pid", "daughter_Wp.size()>0 ? daughter_Wp[0] : -1000")
            .Define("daughter_Wp_1_pid", "daughter_Wp.size()>1 ? daughter_Wp[1] : -1000")
            .Define("daughter_Wp_2_pid", "daughter_Wp.size()>2 ? daughter_Wp[2] : -1000")
            .Define("daughter_Wp_3_pid", "daughter_Wp.size()>3 ? daughter_Wp[3] : -1000")

            .Define("Wm_MC", "HiggsTools::gen_sel_pdgIDInt(-24,false)(Particle)")
            .Define("daughter_Wm", "HiggsTools::gen_decay_list(Wm_MC, Particle, Particle1)")
            .Define("daughter_Wm_no", "daughter_Wm.size()")
            .Define("daughter_Wm_0_pid", "daughter_Wm.size()>0 ? daughter_Wm[0] : -1000")
            .Define("daughter_Wm_1_pid", "daughter_Wm.size()>1 ? daughter_Wm[1] : -1000")
            .Define("daughter_Wm_2_pid", "daughter_Wm.size()>2 ? daughter_Wm[2] : -1000")
            .Define("daughter_Wm_3_pid", "daughter_Wm.size()>3 ? daughter_Wm[3] : -1000")

            ####
            .Define("muon_status2",  "MCParticle::sel_genStatus(2) ( Particle )") 
            .Define("muonp_MC", "HiggsTools::gen_sel_pdgIDInt(-13,false)(muon_status2)") 
            .Define("muonp_MC_no", "muonp_MC.size()")
            .Define("muonm_MC", "HiggsTools::gen_sel_pdgIDInt(13,false)(muon_status2)") 
            .Define("muonm_MC_no", "muonm_MC.size()") 




        
            #############################################
            # Cuts
            #############################################
            #.Define("cut0", "0")
            #########
            ### CUT 1: exactly two muons
            #########
            #.Filter("muons_no==2")
            #.Define("cut1", "1")
            #########
            ### CUT 2 : no electron
            #########
            #.Filter("electrons_no==0")
            #.Define("cut2", "2")
            #########
            ### CUT 2 : no jets
            #########
            #.Filter("true")
            #.Define("cut3", "3")
        )
        return df

class RDFanalysis():
    def analysers(df):
        #df = jet_sequence(df, njets)
        #df = jet_sequence(df, njets, exclusive) # again, was playing with exclusive parameter here. Don't remember if you need to pass it here.
        df = analysis_sequence(df)

        return df

    #__________________________________________________________
    #Mandatory: output function, please make sure you return the branchlist as a python list
    def output():
        branchList = [
            #Reconstructed Particle
            #leptons
            "muons_p",  
            "muons_theta",
            "muons_phi",
            "muons_no", 
            
            #electrons
            "electrons_p",
            "electrons_theta",
            "electrons_phi",
            "electrons_no",

            #"daughter_higgs_collapsed",
            "daughter_higgs_no",
            "daughter_higgs_0_pid",
            "daughter_higgs_1_pid",
            "daughter_higgs_2_pid",
            "daughter_higgs_3_pid",

            "daughter_Z_no",
            "daughter_Z_0_pid",
            "daughter_Z_1_pid",
            "daughter_Z_2_pid",
            "daughter_Z_3_pid",
            "daughter_Z_4_pid",
            "daughter_Z_5_pid",

            "daughter_Wp_no",
            "daughter_Wp_0_pid",
            "daughter_Wp_1_pid",
            "daughter_Wp_2_pid",
            "daughter_Wp_3_pid",

            "daughter_Wm_no",
            "daughter_Wm_0_pid",
            "daughter_Wm_1_pid",
            "daughter_Wm_2_pid",
            "daughter_Wm_3_pid",
            #muons
            "muonp_MC_no",
            "muonm_MC_no"
        ]
        return branchList