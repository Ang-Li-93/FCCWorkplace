
import sys, os, glob, shutil, json, math, re, random, time
import ROOT


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../python")
import loader
import functions
import datasets as ds


def doAnalysis(files, fOut):

    rdf = ROOT.RDataFrame("events", files)
    
    rdf = (rdf
        .Define("nevents", "1.0")
        .Alias("Particle0", "Particle#0.index")
        .Alias("Particle1", "Particle#1.index")
        .Alias("MCRecoAssociations0", "MCRecoAssociations#0.index")
        .Alias("MCRecoAssociations1", "MCRecoAssociations#1.index")
        .Alias("Muon0", "Muon#0.index")
        #.Alias("Jet0", "Muon#0.index")
        #.Alias("Electron0", "Muon#0.index")
        #.Alias("Photon0", "Muon#0.index")
        #.Alias("MissingET0", "MissingET#0.index")

        # baseline muon selection (Delphes cuts off muons at 2 GeV)
        .Define("muons", "ReconstructedParticle::get(Muon0, ReconstructedParticles)")
     
        .Define("muons_pt", "ReconstructedParticle::get_pt(muons)")
        .Define("selected_muons", "ReconstructedParticle::sel_pt(10.)(muons)")
        #.Define("selected_muons", "muon_quality_check(muons)")
        .Define("muons_no", "ReconstructedParticle::get_n(muons)")
        
        .Define("selected_muons_pt", "ReconstructedParticle::get_pt(selected_muons)") 
        .Define("selected_muons_no", "ReconstructedParticle::get_n(selected_muons)")

             
        # event variables
        .Define("cosTheta_miss", "get_cosTheta_miss(MissingET)")
        
        
        # build the Z resonance
        .Define("zed_leptonic", "resonanceZBuilder2(91, false)(selected_muons, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
        .Define("zed_leptonic_m", "ReconstructedParticle::get_mass(zed_leptonic)")
        .Define("zed_leptonic_no", "ReconstructedParticle::get_n(zed_leptonic)")
        .Define("zed_leptonic_pt", "ReconstructedParticle::get_pt(zed_leptonic)")
        .Define("zed_leptonic_charge", "ReconstructedParticle::get_charge(zed_leptonic)")
        
        # build the recoil
        .Define("zed_leptonic_recoil",  "ReconstructedParticle::recoilBuilder(240)(zed_leptonic)")
        .Define("zed_leptonic_recoil_m", "ReconstructedParticle::get_mass(zed_leptonic_recoil)")


        # Z resonance and recoil using MC information from the selected muons
        .Define("zed_leptonic_MC", "resonanceZBuilder2(91, true)(selected_muons, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
        .Define("zed_leptonic_m_MC", "ReconstructedParticle::get_mass(zed_leptonic_MC)")
        .Define("zed_leptonic_pt_MC", "ReconstructedParticle::get_pt(zed_leptonic_MC)")
        .Define("zed_leptonic_charge_MC", "ReconstructedParticle::get_charge(zed_leptonic_MC)")
        .Define("zed_leptonic_recoil_MC",  "ReconstructedParticle::recoilBuilder(240)(zed_leptonic_MC)")
        .Define("zed_leptonic_recoil_m_MC", "ReconstructedParticle::get_mass(zed_leptonic_recoil_MC)")
        
        # systematics
        
        
        # muon momentum scale
        .Define("muons_muscaleup", "momentum_scale(1e-5)(muons)")
        .Define("muons_muscaledw", "momentum_scale(-1e-5)(muons)")
        .Define("selected_muons_muscaleup", "ReconstructedParticle::sel_pt(10.)(muons_muscaleup)")
        .Define("selected_muons_muscaledw", "ReconstructedParticle::sel_pt(10.)(muons_muscaledw)")
        #.Define("selected_muons_muscaleup", "muon_quality_check(muons_muscaleup)")
        #.Define("selected_muons_muscaledw", "muon_quality_check(muons_muscaledw)")
        .Define("selected_muons_pt_muscaleup", "ReconstructedParticle::get_pt(selected_muons_muscaleup)")
        .Define("selected_muons_pt_muscaledw", "ReconstructedParticle::get_pt(selected_muons_muscaledw)")
               
        .Define("zed_leptonic_muscaleup", "resonanceZBuilder2(91, false)(selected_muons_muscaleup, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
        .Define("zed_leptonic_m_muscaleup", "ReconstructedParticle::get_mass(zed_leptonic_muscaleup)")
        .Define("zed_leptonic_no_muscaleup", "ReconstructedParticle::get_n(zed_leptonic_muscaleup)")
        .Define("zed_leptonic_pt_muscaleup", "ReconstructedParticle::get_pt(zed_leptonic_muscaleup)")
        .Define("zed_leptonic_charge_muscaleup", "ReconstructedParticle::get_charge(zed_leptonic_muscaleup)")
               
        .Define("zed_leptonic_muscaledw", "resonanceZBuilder2(91, false)(selected_muons_muscaledw, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
        .Define("zed_leptonic_m_muscaledw", "ReconstructedParticle::get_mass(zed_leptonic_muscaledw)")
        .Define("zed_leptonic_no_muscaledw", "ReconstructedParticle::get_n(zed_leptonic_muscaledw)")
        .Define("zed_leptonic_pt_muscaledw", "ReconstructedParticle::get_pt(zed_leptonic_muscaledw)")
        .Define("zed_leptonic_charge_muscaledw", "ReconstructedParticle::get_charge(zed_leptonic_muscaledw)")
               
        .Define("zed_leptonic_recoil_muscaleup", "ReconstructedParticle::recoilBuilder(240)(zed_leptonic_muscaleup)")
        .Define("zed_leptonic_recoil_muscaledw", "ReconstructedParticle::recoilBuilder(240)(zed_leptonic_muscaledw)")
        .Define("zed_leptonic_recoil_m_muscaleup", "ReconstructedParticle::get_mass(zed_leptonic_recoil_muscaleup)")
        .Define("zed_leptonic_recoil_m_muscaledw", "ReconstructedParticle::get_mass(zed_leptonic_recoil_muscaledw)")
        
        
        # sqrt uncertainty
        .Define("zed_leptonic_recoil_sqrtsup", "ReconstructedParticle::recoilBuilder(240.002)(zed_leptonic)")
        .Define("zed_leptonic_recoil_sqrtsdw", "ReconstructedParticle::recoilBuilder(239.998)(zed_leptonic)")
        .Define("zed_leptonic_recoil_m_sqrtsup", "ReconstructedParticle::get_mass(zed_leptonic_recoil_sqrtsup)")
        .Define("zed_leptonic_recoil_m_sqrtsdw", "ReconstructedParticle::get_mass(zed_leptonic_recoil_sqrtsdw)")
               
               

        # .Define("zed_leptonic_recoil_mc",  "ReconstructedParticle::recoilBuilder(240)(zed_leptonic_mc)")
        # .Define("zed_leptonic_recoil_m_mc","ReconstructedParticle::get_mass(zed_leptonic_recoil_mc)")
        #.Define("selected_muons_mc", "MC_to_reco(MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, selected_muons, Particle)")
        #.Define("muon_resolution", "get_resolution(MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, selected_muons, Particle)")
               
               
        #.Define("zed_leptonic_recoil_MC",  "ReconstructedParticle::recoilBuilder(240)( zed_leptonic_MC )")
        #.Define("zed_leptonic_recoil_MC_mass",   "ReconstructedParticle::get_mass( zed_leptonic_recoil_MC )")
        #.Define("zed_leptonic",         "APCHiggsTools::resonanceZBuilder(91)(selected_muons)")   
        #
               
        #.Define("selected_muons_all", "ReconstructedParticle::sel_pt(10.)(muons_all)")
        # create branch with muon transverse momentum
               
        #.Define("selected_muons_pt_mc", "ReconstructedParticle::get_pt(selected_muons_mc)")
        # create branch with muon rapidity
               

        # create branch with muon total momentum
        #.Define("selected_muons_p",     "ReconstructedParticle::get_p(selected_muons)")
        #.Define("selected_muons_p_mc",     "ReconstructedParticle::get_p(selected_muons_mc)")
        #.Define("selected_muons_p_muscaleup",     "ReconstructedParticle::get_p(selected_muons_muscaleup)")
        #.Define("selected_muons_p_muscaledw",     "ReconstructedParticle::get_p(selected_muons_muscaledw)")
               
               
        #.Define("ISR_gamma_E", "ISR_gamma_E(selected_muons)")
        #.Define("ISR_costhetas", "ISR_costhetas(selected_muons)")
               
               
               
               
        #.Define("event_ht",     "ReconstructedParticle::get_ht(muons, electrons, photons, jets, met)")
        # create branch with muon energy 
               
        # find zed candidates from  di-muon resonances  , returns the best candidate, closest to the Z
               
               
               
        #.Define("zed_leptonic_mc",           "ReconstructedParticle::resonanceBuilder(91)(selected_muons_mc)")
               
        #.Define("zed_leptonic_pair",    "ReconstructedParticle::resonancePairBuilder(91)(selected_muons)")
        #.Define("acoplanarity",      "ReconstructedParticle::acoplanarity(zed_leptonic_pair)")
        #.Define("acolinearity",      "ReconstructedParticle::acolinearity(zed_leptonic_pair)")
        # write branch with zed mass
               
               
        #.Define("zed_leptonic_m_mc",             "ReconstructedParticle::get_mass(zed_leptonic_mc)")
        # write branch with zed transverse momenta
        #.Define("zed_leptonic_pt",      "ReconstructedParticle::get_pt(zed_leptonic)")
        #.Define("zed_leptonic_pt_mc",      "ReconstructedParticle::get_pt(zed_leptonic_mc)")

        #.Define("stable",  "MCParticle::sel_genStatus(2) (Particle)")
        #.Define("theGenLevelMuminus",  "MCParticle::sel_pdgID( 13, false) (stable)")
        #.Define("theGenLevelMuplus",  "MCParticle::sel_pdgID( -13, false) (stable)")
        #.Define("theGenLevelHiggs", "MCParticle::sel_pdgID( 25, false) (stable)")
        #.Define("theGenLevelMuminus_tlv", "MCParticle::get_tlv(theGenLevelMuminus) ")
        #.Define("theGenLevelMuplus_tlv", "MCParticle::get_tlv(theGenLevelMuplus) ")
        #.Define("theGenLevelHiggs_tlv", "MCParticle::get_tlv(theGenLevelHiggs) ")
        #.Define("gen_pt_mumu", "return ( theGenLevelMuminus_tlv[0] + theGenLevelMuplus_tlv[0]).Pt() ;" )
        #.Define("gen_mass_mumu", "return ( theGenLevelMuminus_tlv[0] + theGenLevelMuplus_tlv[0]).M() ;" )
        #.Define("gen_pt_ZH", "return ( theGenLevelMuminus_tlv[0] + theGenLevelMuplus_tlv[0] + theGenLevelHiggs_tlv[0] ).Pt() ;" )
        #.Define("gen_mass_ZH", "return ( theGenLevelMuminus_tlv[0] + theGenLevelMuplus_tlv[0] + theGenLevelHiggs_tlv[0] ).M() ;" )
        #.Define("sf_kkmcp8_wzp6", "Reweighting_wzp_kkmc(gen_pt_ZH,gen_mass_ZH)")
    )
    

               

    
    # select branches for output file
    branchesToSave = [

        # muons
        "selected_muons_pt", "selected_muons_pt_muscaleup", "selected_muons_pt_muscaledw",
        "selected_muons_no",
        
        # event variables
        "cosTheta_miss",
        
        # Z variables
        "zed_leptonic_m", "zed_leptonic_m_muscaleup", "zed_leptonic_m_muscaledw",
        "zed_leptonic_no", "zed_leptonic_no_muscaleup", "zed_leptonic_no_muscaledw", 
        "zed_leptonic_pt", "zed_leptonic_pt_muscaleup", "zed_leptonic_pt_muscaledw", 
        "zed_leptonic_charge", "zed_leptonic_charge_muscaleup", "zed_leptonic_charge_muscaledw",

        
        # recoil
        "zed_leptonic_recoil_m", "zed_leptonic_recoil_m_muscaleup", "zed_leptonic_recoil_m_muscaledw", "zed_leptonic_recoil_m_sqrtsup", "zed_leptonic_recoil_m_sqrtsdw",
        #"zed_leptonic_recoil_m_mc", "zed_leptonic_m_mc"
        "zed_leptonic_m_MC", "zed_leptonic_pt_MC", "zed_leptonic_charge_MC", "zed_leptonic_recoil_m_MC"
        #"acoplanarity",
        #"acolinearity",
        #
        #"daughter_higgs",
        #
        #"muon_resolution",
                
        #"muons_no", "selected_muons_no",
        #"zed_leptonic_m_optimized", "zed_leptonic_pt_optimized", "zed_leptonic_charge_optimized", "zed_leptonic_recoil_m_optimized",
        #"compare", 
        #"higgs_pair_truth",
                
        #"muons_pt", "muons_h_pt", "muons_nh_pt", "muons_no", "muons_h_no", "muons_nh_no", 
        #"selected_muons_h_pt", "selected_muons_nh_pt", "selected_muons_no", "selected_muons_h_no", "selected_muons_nh_no", 


        #"sf_kkmcp8_wzp6"

    ]
   
    branchList = ROOT.vector('string')()
    for branch in branchesToSave: branchList.push_back(branch)
    
    start_time = time.time()
    print("Executing the RDF for %s" % fOut)
    rdf.Snapshot("events", fOut, branchList)
    end_time = time.time()
    print("Finished in %d seconds" % (end_time-start_time))
    print("Number of initial events: %d" % rdf.Sum("nevents").GetValue())
     
    
    
    
    


if __name__ == "__main__":

    outDir = "/eos/user/l/lia/FCCee/mumu_Combine"
    procs = []
    
    #procs.append("wzp6_ee_mumuH_ecm240")
    #procs.append("wzp6_ee_mumuH_mH-lower-50MeV_ecm240")
    #procs.append("wzp6_ee_mumuH_mH-lower-100MeV_ecm240")
    #procs.append("wzp6_ee_mumuH_mH-higher-100MeV_ecm240")
    #procs.append("wzp6_ee_mumuH_mH-higher-50MeV_ecm240")
    #
    #procs.append("wzp6_ee_mumuH_noISR_ecm240")
    #procs.append("wzp6_ee_mumuH_ISRnoRecoil_ecm240")
    #procs.append("wzp6_noBES_ee_mumuH_ecm240")
    #
    #procs.append("wzp6_ee_mumuH_noFSR_ecm240")
    #
    #procs.append("wzp6_ee_mumuH_BES-higher-6pc_ecm240")
    #procs.append("wzp6_ee_mumuH_BES-lower-6pc_ecm240")
    #procs.append("wzp6_ee_mumuH_BES-higher-1pc_ecm240")
    #procs.append("wzp6_ee_mumuH_BES-lower-1pc_ecm240")
    #
    #procs.append("wzp6_ee_tautauH_ecm240")
    #procs.append("wzp6_ee_eeH_ecm240")
    #procs.append("wzp6_ee_nunuH_ecm240")
    #procs.append("wzp6_ee_qqH_ecm240")
    #
    #
    #procs.append("p8_ee_WW_mumu_ecm240")
    #procs.append("p8_ee_ZZ_ecm240")
    #procs.append("p8_ee_ZZ_Zll_ecm240")
    #
    #procs.append("p8_ee_Zll_ecm240")
    #
    #
    #procs.append("wzp6_egamma_eZ_Zmumu_ecm240")
    #procs.append("wzp6_gammae_eZ_Zmumu_ecm240")
    #procs.append("wzp6_gaga_mumu_60_ecm240")
    #procs.append("wzp6_gaga_tautau_60_ecm240")
    
    #procs.append("p8_noBES_ee_ZZ_ecm240")
    #procs.append("p8_ee_WW_ecm240")
    #procs.append("p8_noBES_ee_WW_ecm240")
    #procs.append("p8_ee_Zqq_ecm240") # empty
   
    
    for proc in procs:
    
        if not proc in ds.datasets: 
            
            print("Process %s not found in datasets" % proc)
            continue
    
        eos = ds.datasets[proc]['eos']
        files = functions.findEOS(eos)
        fOut = "%s/%s_tree.root" % (outDir, proc)
        doAnalysis(files, fOut)

          
