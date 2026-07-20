
import analysis, functions
import ROOT
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--nThreads", type=int, help="number of threads", default=None)
parser.add_argument("--maxFiles", type=int, help="Max number of files (per dataset)", default=-1)
parser.add_argument("--flavor", type=str, help="Flavor (mumu or ee)", default="mumu")
args = parser.parse_args()

functions.set_threads(args)

# define histograms
bins_p_mu = (20000, 0, 200) # 10 MeV bins
bins_m_ll = (300, 0, 300) # 1 GeV bins
bins_p_ll = (200, 0, 200) # 1 GeV bins
bins_recoil = (200000, 0, 200) # 1 MeV bins 
bins_cosThetaMiss = (100000, -1, 1)

bins_theta = (500, -5, 5)
bins_eta = (600, -3, 3)
bins_phi = (500, -5, 5)

bins_count = (50, 0, 50)
bins_pdgid = (60, -30, 30)
bins_charge = (10, -5, 5)
bins_iso = (500, 0, 5)
bins_dR = (1000, 0, 10)

bins_massweights = (5, 0, 5)

bins_resolution = (10000, 0.95, 1.05)

bins_theta_abs = (100, 0, 2)


def build_graph(df, dataset):

    print("build graph", dataset.name)
    results = []
    sigProcs = ["wzp6_ee_mumuH_ecm240", "wzp6_ee_mumuH_ecm240_winter", "p8_ee_ZH_ecm240", "wzp6_ee_mumuH_ecm240_prefall", "wz3p6_ee_mumuH_ecm240_prefall", "wz3p6_ee_mumuH_ecm240_winter", "wz3p6_ee_mumuH_ecm240_winter_v2", "wzp6_ee_eeH_ecm240_winter", "wzp6_ee_eeH_ecm240_winter_v2", "wz2p6_ee_mumuH_ecm240_winter_v2", "wzp6_ee_eeH_ecm240"]
    
    df = df.Define("weight", "1.0")
    weightsum = df.Sum("weight")
    
    
    df = df.Alias("Particle0", "Particle#0.index")
    df = df.Alias("Particle1", "Particle#1.index")
    df = df.Alias("MCRecoAssociations0", "MCRecoAssociations#0.index")
    df = df.Alias("MCRecoAssociations1", "MCRecoAssociations#1.index")
    df = df.Alias("Photon0", "Photon#0.index")
    if args.flavor == "mumu":
        df = df.Alias("Muon0", "Muon#0.index")
    else:
        df = df.Alias("Muon0", "Electron#0.index")
     
    
    # prompt gen muons
    # in Whizard, the mumuH process does not directly involve Z processes, hence they are not present in the gen particles
    # the muons either directly come from the hard scatter (electrons as mothers) or from Higgs decays
    ###df = df.Define("gen_prompt_muons_idx", "FCCAnalyses::select_prompt_leptons_idx(13, Particle, Particle0)")
    df = df.Define("gen_prompt_muons", "FCCAnalyses::select_prompt_leptons_gen(13, Particle, Particle0)")
    df = df.Define("gen_prompt_muons_p", "FCCAnalyses::MCParticle::get_p(gen_prompt_muons)")
    df = df.Define("gen_prompt_muons_theta", "FCCAnalyses::MCParticle::get_theta(gen_prompt_muons)")
    df = df.Define("gen_prompt_muons_phi", "FCCAnalyses::MCParticle::get_phi(gen_prompt_muons)")
    df = df.Define("gen_prompt_muons_charge", "FCCAnalyses::MCParticle::get_charge(gen_prompt_muons)")
    df = df.Define("gen_prompt_muons_no", "FCCAnalyses::MCParticle::get_n(gen_prompt_muons)")
    
    # photons
    df = df.Define("photons", "FCCAnalyses::ReconstructedParticle::get(Photon0, ReconstructedParticles)")
    df = df.Define("photons_p", "FCCAnalyses::ReconstructedParticle::get_p(photons)")
    df = df.Define("photons_theta", "FCCAnalyses::ReconstructedParticle::get_theta(photons)")
    df = df.Define("photons_phi", "FCCAnalyses::ReconstructedParticle::get_phi(photons)")
    df = df.Define("photons_no", "FCCAnalyses::ReconstructedParticle::get_n(photons)")
    
    df = df.Define("gen_photons", "FCCAnalyses::get_photons(Particle)")
    df = df.Define("gen_photons_p", "FCCAnalyses::MCParticle::get_p(gen_photons)")
    df = df.Define("gen_photons_theta", "FCCAnalyses::MCParticle::get_theta(gen_photons)")
    df = df.Define("gen_photons_phi", "FCCAnalyses::MCParticle::get_phi(gen_photons)")
    df = df.Define("gen_photons_no", "FCCAnalyses::MCParticle::get_n(gen_photons)")
    
    
    df = df.Define("deltaR_gen_leps", "FCCAnalyses::deltaR_gen_leps(Particle, Particle0, Particle1)")
    df = df.Define("mll_gen_leps", "FCCAnalyses::mll_gen_leps(Particle, Particle0, Particle1)")
    
    #df = df.Define("is_VBF", "FCCAnalyses::is_VBF(Particle, Particle0, Particle1)")
    #df = df.Filter("!is_VBF")

    
    # select muons
    df = df.Define("muons", "FCCAnalyses::ReconstructedParticle::get(Muon0, ReconstructedParticles)")
    df = df.Define("muons_p", "FCCAnalyses::ReconstructedParticle::get_p(muons)")
    df = df.Define("muons_theta", "FCCAnalyses::ReconstructedParticle::get_theta(muons)")
    df = df.Define("muons_eta", "FCCAnalyses::ReconstructedParticle::get_eta(muons)")
    df = df.Define("muons_phi", "FCCAnalyses::ReconstructedParticle::get_phi(muons)")
    df = df.Define("muons_charge", "FCCAnalyses::ReconstructedParticle::get_charge(muons)")
    df = df.Define("muons_no", "FCCAnalyses::ReconstructedParticle::get_n(muons)")
    df = df.Define("muons_iso", "FCCAnalyses::coneIsolation(0.01, 0.5)(muons, ReconstructedParticles)") 
    
    df = df.Define("muons_p_gen", "FCCAnalyses::gen_p_from_reco(muons, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
    
    
    #df = df.Define("selected_muons", "FCCAnalyses::excluded_Higgs_decays(muons, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0, Particle1)") # was 10
    df = df.Define("selected_muons_", "FCCAnalyses::ReconstructedParticle::sel_p(20)(muons)")
    df = df.Define("selected_muons", "FCCAnalyses::sel_iso(99)(selected_muons_, muons_iso)") # 0.25
    
    df = df.Define("selected_muons_p", "FCCAnalyses::ReconstructedParticle::get_p(selected_muons)")
    df = df.Define("selected_muons_theta", "FCCAnalyses::ReconstructedParticle::get_theta(selected_muons)")
    df = df.Define("selected_muons_phi", "FCCAnalyses::ReconstructedParticle::get_phi(selected_muons)")
    df = df.Define("selected_muons_charge", "FCCAnalyses::ReconstructedParticle::get_charge(selected_muons)")
    df = df.Define("selected_muons_no", "FCCAnalyses::ReconstructedParticle::get_n(selected_muons)")
    df = df.Define("selected_muons_iso", "FCCAnalyses::coneIsolation(0.01, 0.5)(selected_muons, ReconstructedParticles)")
    
    # prompt muons
    df = df.Define("prompt_muons", "FCCAnalyses::whizard_zh_select_prompt_leptons(muons, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0, Particle1)")
    df = df.Define("prompt_muons_p", "FCCAnalyses::ReconstructedParticle::get_p(prompt_muons)")
    df = df.Define("prompt_muons_theta", "FCCAnalyses::ReconstructedParticle::get_theta(prompt_muons)")
    df = df.Define("prompt_muons_phi", "FCCAnalyses::ReconstructedParticle::get_phi(prompt_muons)")
    df = df.Define("prompt_muons_charge", "FCCAnalyses::ReconstructedParticle::get_charge(prompt_muons)")
    df = df.Define("prompt_muons_no", "FCCAnalyses::ReconstructedParticle::get_n(prompt_muons)")
    df = df.Define("prompt_muons_iso", "FCCAnalyses::coneIsolation(0.01, 0.5)(prompt_muons, ReconstructedParticles)")
    
    df = df.Define("missingMass", "FCCAnalyses::missingMass(240, ReconstructedParticles)")
    
   
    #df = df.Filter("selected_muons_no >= 2")
    
    
    #df = df.Define("muons_from_higgs", "FCCAnalyses::from_Higgsdecay(selected_muons, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0, Particle1)")
    #df = df.Define("muons_from_prompt", "FCCAnalyses::from_prompt(selected_muons, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0, Particle1)")
    #df = df.Filter("muons_from_higgs == false")
    #df = df.Filter("muons_from_prompt == true")
        

    # muon resolution
    df = df.Define("muons_reso", "FCCAnalyses::leptonResolution_p(muons, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
    df = df.Define("selected_muons_reso", "FCCAnalyses::leptonResolution_p(selected_muons, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
    df = df.Define("prompt_muons_reso", "FCCAnalyses::leptonResolution_p(prompt_muons, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
    
    # build the Z resonance and recoil using MC information from the selected muons
    #df = df.Define("zed_leptonic_MC", "FCCAnalyses::resonanceZBuilder2(91, true)(selected_muons, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
    df = df.Define("zed_leptonic_MC", "FCCAnalyses::resonanceBuilder(91)(selected_muons)")
    df = df.Define("zed_leptonic_m_MC", "FCCAnalyses::ReconstructedParticle::get_mass(zed_leptonic_MC)")
    df = df.Define("zed_leptonic_recoil_MC",  "FCCAnalyses::ReconstructedParticle::recoilBuilder(240)(zed_leptonic_MC)")
    df = df.Define("zed_leptonic_recoil_m_MC", "FCCAnalyses::ReconstructedParticle::get_mass(zed_leptonic_recoil_MC)")
        
    # gen analysis
    if dataset.name in sigProcs:
        df = df.Define("higgs_MC", "FCCAnalyses::gen_sel_pdgIDInt(25,false)(Particle)")
        df = df.Define("daughter_higgs", "FCCAnalyses::gen_decay_list(higgs_MC, Particle, Particle1)")
        df = df.Define("daughter_higgs_collapsed", "daughter_higgs.size()>1 ? ((abs(daughter_higgs[0])+abs(daughter_higgs[1]))*0.5) : -1000 ")
        
        
    # baseline selections and histograms
    results.append(df.Histo1D(("muons_p_cut0", "", *bins_p_mu), "muons_p"))
    results.append(df.Histo1D(("muons_p_gen_cut0", "", *bins_p_mu), "muons_p_gen"))
    results.append(df.Histo1D(("muons_theta_cut0", "", *bins_theta), "muons_theta"))
    results.append(df.Histo1D(("muons_eta_cut0", "", *bins_eta), "muons_eta"))
    results.append(df.Histo1D(("muons_phi_cut0", "", *bins_phi), "muons_phi"))
    results.append(df.Histo1D(("muons_charge_cut0", "", *bins_charge), "muons_charge"))
    results.append(df.Histo1D(("muons_no_cut0", "", *bins_count), "muons_no"))
    results.append(df.Histo1D(("muons_iso_cut0", "", *bins_iso), "muons_iso"))
    results.append(df.Histo1D(("muons_reso_cut0", "", *bins_resolution), "muons_reso"))
    
    df = df.Define("muons_theta_abs", "FCCAnalyses::theta_abs(muons_theta)")
    
    
    #df = df.Filter("muons_theta.size() == muons_reso.size()")
    results.append(df.Histo2D(("muons_theta_reso_cut0", "", *(bins_theta_abs + bins_resolution)), "muons_theta_abs", "muons_reso"))
    
    
    results.append(df.Histo1D(("selected_muons_p_cut0", "", *bins_p_mu), "selected_muons_p"))
    results.append(df.Histo1D(("selected_muons_theta_cut0", "", *bins_theta), "selected_muons_theta"))
    results.append(df.Histo1D(("selected_muons_phi_cut0", "", *bins_phi), "selected_muons_phi"))
    results.append(df.Histo1D(("selected_muons_charge_cut0", "", *bins_charge), "selected_muons_charge"))
    results.append(df.Histo1D(("selected_muons_no_cut0", "", *bins_count), "selected_muons_no"))
    results.append(df.Histo1D(("selected_muons_iso_cut0", "", *bins_iso), "selected_muons_iso"))
    results.append(df.Histo1D(("selected_muons_reso_cut0", "", *bins_resolution), "selected_muons_reso"))
    '''
    results.append(df.Histo1D(("prompt_muons_p_cut0", "", *bins_p_mu), "prompt_muons_p"))
    results.append(df.Histo1D(("prompt_muons_theta_cut0", "", *bins_theta), "prompt_muons_theta"))
    results.append(df.Histo1D(("prompt_muons_phi_cut0", "", *bins_phi), "prompt_muons_phi"))
    results.append(df.Histo1D(("prompt_muons_charge_cut0", "", *bins_charge), "prompt_muons_charge"))
    results.append(df.Histo1D(("prompt_muons_no_cut0", "", *bins_count), "prompt_muons_no"))
    results.append(df.Histo1D(("prompt_muons_iso_cut0", "", *bins_iso), "prompt_muons_iso"))
    results.append(df.Histo1D(("prompt_muons_reso_cut0", "", *bins_resolution), "prompt_muons_reso"))
    
    results.append(df.Histo1D(("gen_prompt_muons_p_cut0", "", *bins_p_mu), "gen_prompt_muons_p"))
    results.append(df.Histo1D(("gen_prompt_muons_theta_cut0", "", *bins_theta), "gen_prompt_muons_theta"))
    results.append(df.Histo1D(("gen_prompt_muons_phi_cut0", "", *bins_phi), "gen_prompt_muons_phi"))
    results.append(df.Histo1D(("gen_prompt_muons_charge_cut0", "", *bins_charge), "gen_prompt_muons_charge"))
    results.append(df.Histo1D(("gen_prompt_muons_no_cut0", "", *bins_count), "gen_prompt_muons_no"))
    '''
    results.append(df.Histo1D(("photons_p", "", *bins_p_mu), "photons_p"))
    results.append(df.Histo1D(("photons_theta", "", *bins_theta), "photons_theta"))
    results.append(df.Histo1D(("photons_phi", "", *bins_phi), "photons_phi"))
    results.append(df.Histo1D(("photons_no", "", *bins_count), "photons_no"))
    
    results.append(df.Histo1D(("gen_photons_p", "", *bins_p_mu), "gen_photons_p"))
    results.append(df.Histo1D(("gen_photons_theta", "", *bins_theta), "gen_photons_theta"))
    results.append(df.Histo1D(("gen_photons_phi", "", *bins_phi), "gen_photons_phi"))
    results.append(df.Histo1D(("gen_photons_no", "", *bins_count), "gen_photons_no"))
    
    #results.append(df.Histo1D(("deltaR_gen_leps", "", *bins_dR), "deltaR_gen_leps"))
    #results.append(df.Histo1D(("mll_gen_leps", "", *bins_m_ll), "mll_gen_leps"))
    
    #results.append(df.Histo1D(("missingMass", "", *bins_m_ll), "missingMass"))
    #return results, weightsum
    
    # forward/central resolution
    '''
    df = df.Define("muons_central", "FCCAnalyses::sel_eta(0,0.8,1)(muons)")
    df = df.Define("muons_forward", "FCCAnalyses::sel_eta(0.8,20,1)(muons)")
    df = df.Define("muons_forward_m", "FCCAnalyses::sel_eta(-20,-0.8,0)(muons)")
    df = df.Define("muons_forward_p", "FCCAnalyses::sel_eta(0.8,20,0)(muons)")
    df = df.Define("muons_central_theta", "FCCAnalyses::ReconstructedParticle::get_theta(muons_central)")
    df = df.Define("muons_forward_theta", "FCCAnalyses::ReconstructedParticle::get_theta(muons_forward)")
    df = df.Define("muons_forward_theta_m", "FCCAnalyses::ReconstructedParticle::get_theta(muons_forward_m)")
    df = df.Define("muons_forward_theta_p", "FCCAnalyses::ReconstructedParticle::get_theta(muons_forward_p)")
    df = df.Define("muons_central_reso", "FCCAnalyses::leptonResolution_p(muons_central, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
    df = df.Define("muons_forward_reso", "FCCAnalyses::leptonResolution_p(muons_forward, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
    df = df.Define("muons_forward_m_reso", "FCCAnalyses::leptonResolution_p(muons_forward_m, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
    df = df.Define("muons_forward_p_reso", "FCCAnalyses::leptonResolution_p(muons_forward_p, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
    
    results.append(df.Histo1D(("muons_central_reso_cut0", "", *bins_resolution), "muons_central_reso"))
    results.append(df.Histo1D(("muons_forward_reso_cut0", "", *bins_resolution), "muons_forward_reso"))
    results.append(df.Histo1D(("muons_forward_m_reso_cut0", "", *bins_resolution), "muons_forward_m_reso"))
    results.append(df.Histo1D(("muons_forward_p_reso_cut0", "", *bins_resolution), "muons_forward_p_reso"))
    results.append(df.Histo1D(("muons_central_theta_cut0", "", *bins_theta), "muons_central_theta"))
    results.append(df.Histo1D(("muons_forward_theta_cut0", "", *bins_theta), "muons_forward_theta"))
    results.append(df.Histo1D(("muons_forward_m_theta_cut0", "", *bins_theta), "muons_forward_theta_m"))
    results.append(df.Histo1D(("muons_forward_p_theta_cut0", "", *bins_theta), "muons_forward_theta_p"))
    
    # p dependent resolution
    df = df.Define("muons_0_30", "FCCAnalyses::ReconstructedParticle::sel_p(0,30)(muons)")
    df = df.Define("muons_30_50", "FCCAnalyses::ReconstructedParticle::sel_p(30,50)(muons)")
    df = df.Define("muons_50_70", "FCCAnalyses::ReconstructedParticle::sel_p(50,70)(muons)")
    df = df.Define("muons_70_100", "FCCAnalyses::ReconstructedParticle::sel_p(70,100)(muons)")
    df = df.Define("muons_0_30_reso", "FCCAnalyses::leptonResolution_p(muons_0_30, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
    df = df.Define("muons_30_50_reso", "FCCAnalyses::leptonResolution_p(muons_30_50, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
    df = df.Define("muons_50_70_reso", "FCCAnalyses::leptonResolution_p(muons_50_70, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
    df = df.Define("muons_70_100_reso", "FCCAnalyses::leptonResolution_p(muons_70_100, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
    results.append(df.Histo1D(("muons_0_30_reso_cut0", "", *bins_resolution), "muons_0_30_reso"))
    results.append(df.Histo1D(("muons_30_50_reso_cut0", "", *bins_resolution), "muons_30_50_reso"))
    results.append(df.Histo1D(("muons_50_70_reso_cut0", "", *bins_resolution), "muons_50_70_reso"))
    results.append(df.Histo1D(("muons_70_100_reso_cut0", "", *bins_resolution), "muons_70_100_reso"))
    
    if dataset.name in sigProcs: results.append(df.Histo1D(("higgs_decay_cut0", "", *bins_count), "daughter_higgs_collapsed"))
    
    # bare plots
    '''
   
    #########
    ### CUT 1
    #########
    df = df.Filter("selected_muons_no >= 1")
    if dataset.name in sigProcs: results.append(df.Histo1D(("higgs_decay_cut1", "", *bins_count), "daughter_higgs_collapsed"))
        
    #########
    ### CUT 2
    #########
    df = df.Filter("selected_muons_no >= 2")
    if dataset.name in sigProcs: results.append(df.Histo1D(("higgs_decay_cut2", "", *bins_count), "daughter_higgs_collapsed"))
        
    #########
    ### CUT 3
    #########    
    # build the Z resonance and recoil  resonanceZBuilderHiggsPairs
    #df = df.Define("zed_leptonic", "FCCAnalyses::resonanceZBuilder2(91, false)(selected_muons, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
    df = df.Define("zbuilder_result", "FCCAnalyses::resonanceBuilder_mass_recoil(91.2, 125, 0.4, 240, true)(selected_muons, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0, Particle1)")
    df = df.Define("zed_leptonic", "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result[0]}") # the Z
    df = df.Define("zed_leps", "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result[1],zbuilder_result[2]}") # the leptons
    df = df.Define("zed_leptonic_m", "FCCAnalyses::ReconstructedParticle::get_mass(zed_leptonic)[0]")
    df = df.Define("zed_leptonic_p", "FCCAnalyses::ReconstructedParticle::get_p(zed_leptonic)[0]")
    df = df.Define("zed_leptonic_recoil", "FCCAnalyses::ReconstructedParticle::recoilBuilder(240)(zed_leptonic)")
    df = df.Define("zed_leptonic_recoil_m", "FCCAnalyses::ReconstructedParticle::get_mass(zed_leptonic_recoil)[0]")
    
    df = df.Define("zed_leptonic_m_", "zed_leptonic_m")
    df = df.Define("zed_leptonic_p_", "zed_leptonic_p")
    df = df.Define("zed_leptonic_recoil_m_", "zed_leptonic_recoil_m")
    
    #df = df.Filter("zed_leptonic_m.size() > 0") # was ==1
    if dataset.name in sigProcs:
        results.append(df.Histo2D(("higgs_decay_zed_leptonic_m_cut3", "", *(bins_count + bins_m_ll)), "daughter_higgs_collapsed", "zed_leptonic_m_"))
        results.append(df.Histo2D(("higgs_decay_zed_leptonic_p_cut3", "", *(bins_count + bins_m_ll)), "daughter_higgs_collapsed", "zed_leptonic_p_"))
        results.append(df.Histo1D(("zed_leptonic_m_cut3", "", *bins_m_ll), "zed_leptonic_m_"))
        results.append(df.Histo1D(("zed_leptonic_recoil_m_cut3", "", *bins_recoil), "zed_leptonic_recoil_m"))
        results.append(df.Histo1D(("higgs_decay_cut3", "", *bins_count), "daughter_higgs_collapsed"))
        results.append(df.Histo1D(("zed_leptonic_p_cut3", "", *bins_p_ll), "zed_leptonic_p_"))
        
        results.append(df.Histo1D(("photons_p_cut3", "", *bins_p_mu), "photons_p"))
        results.append(df.Histo1D(("photons_theta_cut3", "", *bins_theta), "photons_theta"))
        results.append(df.Histo1D(("photons_no_cut3", "", *bins_count), "photons_no"))        
    
    
    #########
    ### CUT 4
    #########  
    df = df.Filter("zed_leptonic_m > 86 &&  zed_leptonic_m < 96")
    #df = df.Filter("zed_leptonic_m[0] > 73 &&  zed_leptonic_m[0] < 120")
    results.append(df.Histo1D(("zed_leptonic_m_cut4", "", *bins_m_ll), "zed_leptonic_m"))
    results.append(df.Histo1D(("zed_leptonic_recoil_m_cut4", "", *bins_recoil), "zed_leptonic_recoil_m"))
    results.append(df.Histo1D(("zed_leptonic_p_cut4", "", *bins_p_ll), "zed_leptonic_p"))
    results.append(df.Histo1D(("selected_muons_p_cut4", "", *bins_p_mu), "selected_muons_p"))
    if dataset.name in sigProcs:
        results.append(df.Histo2D(("higgs_decay_zed_leptonic_m_cut4", "", *(bins_count + bins_m_ll)), "daughter_higgs_collapsed", "zed_leptonic_m_"))
        results.append(df.Histo2D(("higgs_decay_zed_leptonic_p_cut4", "", *(bins_count + bins_m_ll)), "daughter_higgs_collapsed", "zed_leptonic_p_"))
        results.append(df.Histo1D(("zed_leptonic_m_cut4", "", *bins_m_ll), "zed_leptonic_m"))
        results.append(df.Histo1D(("zed_leptonic_recoil_m_cut4", "", *bins_recoil), "zed_leptonic_recoil_m"))
        results.append(df.Histo1D(("higgs_decay_cut4", "", *bins_count), "daughter_higgs_collapsed")) 
    
    #########
    ### CUT 5
    #########  
    df = df.Filter("zed_leptonic_p > 20 && zed_leptonic_p < 70")
    if dataset.name in sigProcs:
        results.append(df.Histo1D(("zed_leptonic_p_cut5", "", *bins_p_ll), "zed_leptonic_p"))
        results.append(df.Histo1D(("selected_muons_p_cut5", "", *bins_p_mu), "selected_muons_p"))
        results.append(df.Histo2D(("higgs_decay_zed_leptonic_m_cut5", "", *(bins_count + bins_m_ll)), "daughter_higgs_collapsed", "zed_leptonic_m_"))
        results.append(df.Histo2D(("higgs_decay_zed_leptonic_p_cut5", "", *(bins_count + bins_m_ll)), "daughter_higgs_collapsed", "zed_leptonic_p_"))
        results.append(df.Histo1D(("zed_leptonic_m_cut5", "", *bins_m_ll), "zed_leptonic_m"))
        results.append(df.Histo1D(("zed_leptonic_recoil_m_cut5", "", *bins_recoil), "zed_leptonic_recoil_m"))
        results.append(df.Histo1D(("higgs_decay_cut5", "", *bins_count), "daughter_higgs_collapsed")) 
    
    #########
    ### CUT 6
    #########  
    df = df.Define("cosTheta_miss", "FCCAnalyses::get_cosTheta_miss(MissingET)")
    #df = df.Filter("cosTheta_miss[0] < 0.98")
    if dataset.name in sigProcs: 
        results.append(df.Histo1D(("zed_leptonic_p_cut6", "", *bins_p_ll), "zed_leptonic_p"))
        results.append(df.Histo1D(("selected_muons_p_cut6", "", *bins_p_mu), "selected_muons_p"))
        results.append(df.Histo1D(("cosThetaMiss_cut6", "", *bins_cosThetaMiss), "cosTheta_miss"))
        results.append(df.Histo2D(("higgs_decay_zed_leptonic_m_cut6", "", *(bins_count + bins_m_ll)), "daughter_higgs_collapsed", "zed_leptonic_m_"))
        results.append(df.Histo2D(("higgs_decay_zed_leptonic_p_cut6", "", *(bins_count + bins_m_ll)), "daughter_higgs_collapsed", "zed_leptonic_p_"))
        results.append(df.Histo1D(("zed_leptonic_m_cut6", "", *bins_m_ll), "zed_leptonic_m"))
        results.append(df.Histo1D(("zed_leptonic_recoil_m_cut6", "", *bins_recoil), "zed_leptonic_recoil_m"))
        results.append(df.Histo1D(("higgs_decay_cut6", "", *bins_count), "daughter_higgs_collapsed")) 
    
    
    #df = df.Filter("muons_theta[0] < 2.14 && muons_theta[0] > 1.0 && muons_theta[1] < 2.14 && muons_theta[1] > 1.0")
    #df = df.Filter("muons_theta[0] < 2.0 && muons_theta[0] > 1.15")
    #df = df.Filter("mll_gen_leps < 93 && mll_gen_leps > 88")
    
    # final selection and histograms
    df = df.Filter("zed_leptonic_recoil_m < 140 && zed_leptonic_recoil_m > 120")
    results.append(df.Histo1D(("zed_leptonic_m", "", *bins_m_ll), "zed_leptonic_m"))
    results.append(df.Histo1D(("zed_leptonic_recoil_m", "", *bins_recoil), "zed_leptonic_recoil_m"))
    results.append(df.Histo1D(("zed_leptonic_p", "", *bins_p_ll), "zed_leptonic_p"))
    results.append(df.Histo1D(("selected_muons_p", "", *bins_p_mu), "selected_muons_p"))
    results.append(df.Histo1D(("cosThetaMiss", "", *bins_cosThetaMiss), "cosTheta_miss"))
    if dataset.name in sigProcs: 
        results.append(df.Histo1D(("higgs_decay", "", *bins_count), "daughter_higgs_collapsed")) 
    
    # MC based recoil
    results.append(df.Histo1D(("zed_leptonic_m_MC", "", *bins_m_ll), "zed_leptonic_m_MC"))
    results.append(df.Histo1D(("zed_leptonic_recoil_m_MC", "", *bins_recoil), "zed_leptonic_recoil_m_MC"))
    

    if dataset.name not in sigProcs:
        return results, weightsum
        
        
    
    

 
    return results, weightsum
    
    


if __name__ == "__main__":

    datasets = []

    # import spring2021 IDEA samples
    import FCCee_spring2021_IDEA
    import FCCee_winter2023_IDEA_ecm240
    import FCCee_preproduction_IDEA
    
    #datasets = FCCee_spring2021_IDEA.getDatasets(filt="p8_ee_ZH_ecm240") # p8_ee_ZH_ecm240 
    #datasets += FCCee_spring2021_IDEA.getDatasets(filt="wzp6_ee_mumuH_ecm240")
    #datasets += FCCee_spring2021_IDEA.getDatasets(filt="p8_ee_Zmumu_ecm91")
    #datasets = FCCee_spring2021_IDEA.getDatasets(filt="wzp6_ee_mumuH_*ecm240")
    baseDir = functions.get_basedir() 
    
    if args.flavor == "mumu": 
        
        datasets_preproduction_IDEA = FCCee_preproduction_IDEA.get_datasets() # nominal
        datasets += functions.filter_datasets(datasets_preproduction_IDEA, ["wzp6_ee_mumuH_ecm240", "wzp6_ee_mumuH_ecm240_winter"])
        #datasets += FCCee_preproduction_IDEA.getDatasets(filt="wzp6_ee_mumuH_ecm240_prefall") # muon iso fix
        #datasets += FCCee_preproduction_IDEA.getDatasets(filt="wz3p6_ee_mumuH_ecm240_prefall")
        ####datasets += FCCee_preproduction_IDEA.getDatasets(filt="wz3p6_ee_mumuH_ecm240_winter") # muon reso fix
        #datasets += FCCee_preproduction_IDEA.getDatasets(filt="wz3p6_ee_mumuH_ecm240_winter_v2") # electron fix
        #datasets += FCCee_preproduction_IDEA.getDatasets(filt="wzp6_ee_mumuH_ecm240")
        #datasets = FCCee_preproduction_IDEA.getDatasets(filt="muon_gun")
        #datasets += FCCee_preproduction_IDEA.getDatasets(filt="muon_gun_smear2x")
        
        #datasets += FCCee_preproduction_IDEA.getDatasets(filt="p8_ee_ZZ_Zll_ecm240")
        
    
    if args.flavor == "ee":
        #
        #datasets += FCCee_preproduction_IDEA.getDatasets(filt="wzp6_ee_eeH_ecm240") 
        datasets += FCCee_preproduction_IDEA.getDatasets(filt="wzp6_ee_eeH_ecm240_v1")
        datasets += FCCee_preproduction_IDEA.getDatasets(filt="wzp6_ee_eeH_ecm240_v2") 
        datasets += FCCee_preproduction_IDEA.getDatasets(filt="wzp6_ee_eeH_ecm240_v3") 
        datasets += FCCee_preproduction_IDEA.getDatasets(filt="wzp6_ee_eeH_ecm240_v4") 
        #datasets += FCCee_preproduction_IDEA.getDatasets(filt="wzp6_ee_eeH_ecm240_winter_v2") # 2x reso
    
        #datasets = FCCee_preproduction_IDEA.getDatasets(filt="electron_gun")
        
        #datasets += FCCee_preproduction_IDEA.getDatasets(filt="p8_ee_ZZ_Zll_ecm240")

    result = functions.build_and_run(datasets, build_graph, "tmp/validation_%s.root" % args.flavor, maxFiles=args.maxFiles, norm=True, lumi=5000000)
    
