#Mandatory: List of processes

processList = {
    #signal
    "wzp6_ee_mumuH_ecm240":{'chunks':10},
    "wzp6_ee_mumuH_HZZ_ecm240":{'chunks':10},
    ##background: 
    "p8_ee_WW_ecm240":{'chunks':80},
    "p8_ee_ZZ_ecm240":{'chunks':20},
    "wzp6_ee_mumu_ecm240":{'chunks':20},
    "wzp6_ee_tautau_ecm240":{'chunks':20},
    #rare backgrounds:
    "wzp6_egamma_eZ_Zmumu_ecm240":{'chunks':20},
    "wzp6_gammae_eZ_Zmumu_ecm240":{'chunks':20},
    "wzp6_gaga_mumu_60_ecm240":{'chunks':20},
    "wzp6_gaga_tautau_60_ecm240":{'chunks':20},
    "wzp6_ee_nuenueZ_ecm240":{'chunks':20},
    }
#Mandatory: Production tag when running over EDM4Hep centrally produced events, this points to the yaml files for getting sample statistics
prodTag     = "FCCee/winter2023/IDEA/"

#from userConfig import loc
#outputDir="/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/HiggsInvisible/lia/muon_comparison/stage1"
outputDirEos= "/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/HiggsInvisible/lia/muon_comparison/stage1"
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
            .Alias("Particle0", "Particle#0.index")
            .Alias("Particle1", "Particle#1.index")

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

            #############################################
            ## Define the collections of jets          ##
            #############################################
            .Define("jets", "ReconstructedParticle::sel_p(15)(Jet)")
            .Define("jets_p", "FCCAnalyses::ReconstructedParticle::get_p(jets)")
            .Define("jets_theta", "FCCAnalyses::ReconstructedParticle::get_theta(jets)")
            .Define("jets_phi", "FCCAnalyses::ReconstructedParticle::get_phi(jets)")
            .Define("jets_no", "FCCAnalyses::ReconstructedParticle::get_n(jets)")

            #############################################
            ## Define which object to use              ##
            #############################################
            .Alias("leps_all", "muons")
            .Define("leps", "FCCAnalyses::ReconstructedParticle::sel_p(10)(leps_all)")
            .Define("leps_iso", "HiggsTools::coneIsolation(0.01, 0.5)(leps, ReconstructedParticles)")
            .Define("leps_sel_iso", "HiggsTools::sel_isol(0.25)(leps, leps_iso)")

            #############################################
            ## Z builder                               ##
            #############################################
            .Define("Z", "HiggsTools::resonanceZBuilder2(91, true)(leps, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")  
            .Define("Z_p", "FCCAnalyses::ReconstructedParticle::get_p(Z)")
            .Define("Z_m", "FCCAnalyses::ReconstructedParticle::get_mass(Z)")
            .Define("Z_theta", "FCCAnalyses::ReconstructedParticle::get_theta(Z)")
            .Define("Z_phi", "FCCAnalyses::ReconstructedParticle::get_phi(Z)")

            #############################################
            ## reocil builder                          ##
            #############################################
            .Define("Z_recoil", "FCCAnalyses::ReconstructedParticle::recoilBuilder(240)(Z)")
            .Define("Z_recoil_m", "FCCAnalyses::ReconstructedParticle::get_mass(Z_recoil)")
            .Define("Z_recoil_p", "FCCAnalyses::ReconstructedParticle::get_p(Z_recoil)")
            .Define("Z_recoil_theta", "FCCAnalyses::ReconstructedParticle::get_theta(Z_recoil)")
            .Define("Z_recoil_phi", "FCCAnalyses::ReconstructedParticle::get_phi(Z_recoil)")

            #############################################
            # Missing information
            #############################################
            .Define("missing", "HiggsTools::missing(ReconstructedParticles, 240., 0.)")
            .Define("missing_mass", "FCCAnalyses::ReconstructedParticle::get_mass(missing)")
            .Define("missing_e", "FCCAnalyses::ReconstructedParticle::get_e(missing)")
            .Define("missing_p", "FCCAnalyses::ReconstructedParticle::get_p(missing)")
            .Define("missing_theta", "FCCAnalyses::ReconstructedParticle::get_theta(missing)")
            .Define("missing_phi", "FCCAnalyses::ReconstructedParticle::get_phi(missing)")
            .Define("missing_px", "FCCAnalyses::ReconstructedParticle::get_px(missing)")
            .Define("missing_py", "FCCAnalyses::ReconstructedParticle::get_py(missing)")
            .Define("missing_pz", "FCCAnalyses::ReconstructedParticle::get_pz(missing)")
            .Define("missing_pt", "FCCAnalyses::ReconstructedParticle::get_pt(missing)")
            .Define("missing_costheta", "HiggsTools::get_cosTheta(missing)") 

            #############################################
            # Visible information
            #############################################
            .Define("visible", "HiggsTools::visible(ReconstructedParticles, 0.)")
            .Define("visible_mass", "FCCAnalyses::ReconstructedParticle::get_mass(visible)")
            .Define("visible_e", "FCCAnalyses::ReconstructedParticle::get_e(visible)")
            .Define("visible_p", "FCCAnalyses::ReconstructedParticle::get_p(visible)")
            .Define("visible_theta", "FCCAnalyses::ReconstructedParticle::get_theta(visible)")
            .Define("visible_phi", "FCCAnalyses::ReconstructedParticle::get_phi(visible)")
            .Define("visible_px", "FCCAnalyses::ReconstructedParticle::get_px(visible)")
            .Define("visible_py", "FCCAnalyses::ReconstructedParticle::get_py(visible)")
            .Define("visible_pz", "FCCAnalyses::ReconstructedParticle::get_pz(visible)") 

            #First imput to Z, second to Higgs
            .Define("ZHChi2", "HiggsTools::ZHChi2(visible_mass[0], missing_mass[0])")
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

            #jets
            "jets_p",
            "jets_theta",
            "jets_phi",
            "jets_no",

            #lepton
            "leps_iso",

            #Z
            "Z_p",
            "Z_m",
            "Z_theta",
            "Z_phi",

            #recoil
            "Z_recoil_m",
            "Z_recoil_p",
            "Z_recoil_theta",
            "Z_recoil_phi",

            #missing
            "missing_mass",
            "missing_e",
            "missing_p",
            "missing_theta",
            "missing_phi",
            "missing_px",
            "missing_py",
            "missing_pz",
            "missing_pt",
            "missing_costheta",

            #visible
            "visible_mass",
            "visible_e",
            "visible_p",
            "visible_theta",
            "visible_phi",
            "visible_px",
            "visible_py",
            "visible_pz",

            "ZHChi2"
        ]
        return branchList