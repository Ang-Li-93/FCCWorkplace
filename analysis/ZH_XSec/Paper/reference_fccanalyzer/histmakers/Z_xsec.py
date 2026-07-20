
import analysis, functions
import ROOT
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--nThreads", type=int, help="number of threads", default=None)
parser.add_argument("--maxFiles", type=int, help="Max number of files (per dataset)", default=-1)
parser.add_argument("--flavor", type=str, choices=["ee", "mumu", "qq"], help="Flavor (ee, mumu, qq)", default="mumu")
parser.add_argument("--jetAlgo", type=str, choices=["kt", "valencia", "genkt"], default="genkt", help="Jet clustering algorithm")
args = parser.parse_args()

functions.set_threads(args)

# define histograms
bins_p_mu = (20000, 0, 200) # 10 MeV bins
bins_m_ll = (20000, 0, 300) # 10 MeV bins
bins_p_ll = (20000, 0, 200) # 10 MeV bins

bins_theta = (500, -5, 5)
bins_phi = (500, -5, 5)

bins_count = (100, 0, 100)
bins_pdgid = (60, -30, 30)
bins_charge = (10, -5, 5)

bins_resolution = (10000, 0.95, 1.05)

bins_resolution_1 = (20000, 0, 2)

jet_energy = (1000, 0, 100) # 100 MeV bins
dijet_m = (2000, 0, 200) # 100 MeV bins
visMass = (2000, 0, 200) # 100 MeV bins
missEnergy  = (2000, 0, 200) # 100 MeV bins

dijet_m_final = (500, 50, 100) # 100 MeV bins

def build_graph_ll(df, dataset):

    print("build graph", dataset.name)
    results = []

    df = df.Define("weight", "1.0")
    weightsum = df.Sum("weight")
    
    
    df = df.Alias("Particle0", "Particle#0.index")
    df = df.Alias("Particle1", "Particle#1.index")
    df = df.Alias("MCRecoAssociations0", "MCRecoAssociations#0.index")
    df = df.Alias("MCRecoAssociations1", "MCRecoAssociations#1.index")
    if args.flavor == "mumu":
        df = df.Alias("Lepton0", "Muon#0.index")
    else:
        df = df.Alias("Lepton0", "Electron#0.index")
     
    
    
    # all leptons
    df = df.Define("leps_all", "FCCAnalyses::ReconstructedParticle::get(Lepton0, ReconstructedParticles)")
    df = df.Define("leps_all_p", "FCCAnalyses::ReconstructedParticle::get_p(leps_all)")
    df = df.Define("leps_all_theta", "FCCAnalyses::ReconstructedParticle::get_theta(leps_all)")
    df = df.Define("leps_all_phi", "FCCAnalyses::ReconstructedParticle::get_phi(leps_all)")
    df = df.Define("leps_all_q", "FCCAnalyses::ReconstructedParticle::get_charge(leps_all)")
    df = df.Define("leps_all_no", "FCCAnalyses::ReconstructedParticle::get_n(leps_all)")
    
    # cuts on leptons
    #df = df.Define("selected_muons", "FCCAnalyses::excluded_Higgs_decays(muons, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0, Particle1)") # was 10
    df = df.Define("leps_sel_p", "FCCAnalyses::ReconstructedParticle::sel_p(1)(leps_all)")
    df = df.Alias("leps", "leps_sel_p") 
    
    df = df.Define("leps_p", "FCCAnalyses::ReconstructedParticle::get_p(leps)")
    df = df.Define("leps_theta", "FCCAnalyses::ReconstructedParticle::get_theta(leps)")
    df = df.Define("leps_phi", "FCCAnalyses::ReconstructedParticle::get_phi(leps)")
    df = df.Define("leps_q", "FCCAnalyses::ReconstructedParticle::get_charge(leps)")
    df = df.Define("leps_no", "FCCAnalyses::ReconstructedParticle::get_n(leps)")
    
    # momentum resolution: reco/gen
    df = df.Define("leps_all_reso_p", "FCCAnalyses::leptonResolution_p(leps_all, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
    df = df.Define("leps_reso_p", "FCCAnalyses::leptonResolution_p(leps, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle)")
    

    # lepton kinematic histograms
    results.append(df.Histo1D(("leps_all_p_cut0", "", *bins_p_mu), "leps_all_p"))
    results.append(df.Histo1D(("leps_all_theta_cut0", "", *bins_theta), "leps_all_theta"))
    results.append(df.Histo1D(("leps_all_phi_cut0", "", *bins_phi), "leps_all_phi"))
    results.append(df.Histo1D(("leps_all_q_cut0", "", *bins_charge), "leps_all_q"))
    results.append(df.Histo1D(("leps_all_no_cut0", "", *bins_count), "leps_all_no"))
    results.append(df.Histo1D(("leps_all_reso_p_cut0", "", *bins_resolution), "leps_all_reso_p"))
    

    results.append(df.Histo1D(("leps_p_cut0", "", *bins_p_mu), "leps_p"))
    results.append(df.Histo1D(("leps_theta_cut0", "", *bins_theta), "leps_theta"))
    results.append(df.Histo1D(("leps_phi_cut0", "", *bins_phi), "leps_phi"))
    results.append(df.Histo1D(("leps_q_cut0", "", *bins_charge), "leps_q"))
    results.append(df.Histo1D(("leps_no_cut0", "", *bins_count), "leps_no"))
    results.append(df.Histo1D(("leps_reso_p_cut0", "", *bins_resolution), "leps_reso_p"))
    
   

    
    #########
    ### CUT 0: all events
    #########
    df = df.Define("cut0", "0")
    results.append(df.Histo1D(("cutFlow_cut0", "", *bins_count), "cut0"))
   

    #########
    ### CUT 1: at least a lepton with at least 1 isolated one
    #########
    df = df.Filter("leps_no >= 1").Define("cut1", "1")
    results.append(df.Histo1D(("cutFlow_cut1", "", *bins_count), "cut1"))
    
    
    #########
    ### CUT 2 :at least 2 leptons, and build the resonance
    #########
    df = df.Filter("leps_no >= 2").Define("cut2", "2")
    results.append(df.Histo1D(("cutFlow_cut2", "", *bins_count), "cut2"))
    

    # build the Z resonance from the reconstructed particles
    df = df.Define("zll", "FCCAnalyses::resonanceBuilder(91)(leps)")
    df = df.Define("zll_m", "FCCAnalyses::ReconstructedParticle::get_mass(zll)")
    df = df.Define("zll_no", "FCCAnalyses::ReconstructedParticle::get_n(zll)")
    df = df.Define("zll_p", "FCCAnalyses::ReconstructedParticle::get_p(zll)")
    
    #########
    ### CUT 3 :at least 1 resonance (i.e. one opposite sign pair muon)
    #########
    df = df.Filter("zll_no >= 1").Define("cut3", "3")
    results.append(df.Histo1D(("cutFlow_cut3", "", *bins_count), "cut3"))


    #########
    ### CUT 4 :cut on Z mass
    #########
    df = df.Filter("(zll_m[0] > 73 && zll_m[0] < 109) || true").Define("cut4", "4")
    results.append(df.Histo1D(("cutFlow_cut4", "", *bins_count), "cut4"))
    
    
    ########################
    # Final histograms
    ########################
    results.append(df.Histo1D(("zll_m_cut4", "", *bins_m_ll), "zll_m"))
    results.append(df.Histo1D(("zll_p_cut4", "", *bins_p_ll), "zll_p"))
    results.append(df.Histo1D(("leps_p_cut4", "", *bins_p_mu), "leps_p"))
    
    return results, weightsum
    
    
def build_graph_qq(df, dataset):

    print("build graph", dataset.name)
    results = []

    df = df.Define("weight", "1.0")
    weightsum = df.Sum("weight")
    
    
    df = df.Define("RP_px", "FCCAnalyses::ReconstructedParticle::get_px(ReconstructedParticles)")
    df = df.Define("RP_py", "FCCAnalyses::ReconstructedParticle::get_py(ReconstructedParticles)")
    df = df.Define("RP_pz", "FCCAnalyses::ReconstructedParticle::get_pz(ReconstructedParticles)")
    df = df.Define("RP_e",  "FCCAnalyses::ReconstructedParticle::get_e(ReconstructedParticles)")
    df = df.Define("RP_m",  "FCCAnalyses::ReconstructedParticle::get_mass(ReconstructedParticles)")
    df = df.Define("RP_q",  "FCCAnalyses::ReconstructedParticle::get_charge(ReconstructedParticles)")
    df = df.Define("RP_no",  "FCCAnalyses::ReconstructedParticle::get_n(ReconstructedParticles)")
    
    df = df.Define("pseudo_jets", "FCCAnalyses::JetClusteringUtils::set_pseudoJets(RP_px, RP_py, RP_pz, RP_e)")
    
    
    # sum of reco particles energy
    df = df.Define("Evis",  "FCCAnalyses::visibleEnergy(ReconstructedParticles)")
    df = df.Define("Evis_norm", "Evis/91.188")
    
    results.append(df.Histo1D(("Evis", "", *bins_m_ll), "Evis"))
    results.append(df.Histo1D(("Evis_norm", "", *bins_resolution_1), "Evis_norm"))
    
    results.append(df.Histo1D(("RP_no", "", *bins_count), "RP_no"))
 
    
    # more info: https://indico.cern.ch/event/1173562/contributions/4929025/attachments/2470068/4237859/2022-06-FCC-jets.pdf
    # https://github.com/HEP-FCC/FCCAnalyses/blob/master/addons/FastJet/src/JetClustering.cc
    if args.jetAlgo == "kt":
        df = df.Define("clustered_jets", "JetClustering::clustering_ee_kt(2, 2, 0, 10)(pseudo_jets)")
    elif args.jetAlgo == "valencia":
        df = df.Define("clustered_jets", "JetClustering::clustering_valencia(0.5, 1, 2, 0, 0, 1., 1.)(pseudo_jets)")
    elif args.jetAlgo == "genkt":
        df = df.Define("clustered_jets", "FCCAnalyses::JetClustering::clustering_ee_genkt(1.5, 0, 0, 0, 0, -1)(pseudo_jets)")
          


    df = df.Define("jets", "FCCAnalyses::JetClusteringUtils::get_pseudoJets(clustered_jets)")
    df = df.Define("jetconstituents", "FCCAnalyses::JetClusteringUtils::get_constituents(clustered_jets)")
    df = df.Define("jets_e", "FCCAnalyses::JetClusteringUtils::get_e(jets)")
    df = df.Define("jets_px", "FCCAnalyses::JetClusteringUtils::get_px(jets)")
    df = df.Define("jets_py", "FCCAnalyses::JetClusteringUtils::get_py(jets)")
    df = df.Define("jets_pz", "FCCAnalyses::JetClusteringUtils::get_pz(jets)")
    df = df.Define("jets_phi", "FCCAnalyses::JetClusteringUtils::get_phi(jets)")
    df = df.Define("jets_m", "FCCAnalyses::JetClusteringUtils::get_m(jets)")
        
    df = df.Define("njets", "jets_e.size()")
    results.append(df.Histo1D(("njets", "", *bins_count), "njets"))
    df = df.Filter("njets >= 2")
        
    # reconstruct resonance (jets are pT ordered)
    df = df.Define("jet1", "ROOT::Math::PxPyPzEVector(jets_px[0], jets_py[0], jets_pz[0], jets_e[0])")
    df = df.Define("jet2", "ROOT::Math::PxPyPzEVector(jets_px[1], jets_py[1], jets_pz[1], jets_e[1])")
    df = df.Define("dijet", "jet1+jet2")
    df = df.Define("dijet_m", "dijet.M()")

    results.append(df.Histo1D(("jets_e", "", *jet_energy), "jets_e"))
    results.append(df.Histo1D(("dijet_m", "", *dijet_m), "dijet_m"))
    results.append(df.Histo1D(("dijet_m_final", "", *dijet_m_final), "dijet_m"))
   
    results.append(df.Histo1D(("jets_phi", "", *bins_phi), "jets_phi"))    

    
    df = df.Define("visibleMass", "FCCAnalyses::visibleMass(ReconstructedParticles)") # scalar
    df = df.Define("missingEnergy_vec", "FCCAnalyses::missingEnergy(91.1, ReconstructedParticles)") # returns a vector
    df = df.Define("missingEnergy", "FCCAnalyses::ReconstructedParticle::get_e(missingEnergy_vec)")
    
    results.append(df.Histo1D(("visibleMass", "", *visMass), "visibleMass"))    
    results.append(df.Histo1D(("missingEnergy", "", *missEnergy), "missingEnergy"))    
        
    
    return results, weightsum
    
    
    
    
    
   

if __name__ == "__main__":

    baseDir = functions.get_basedir() # get base directory of samples, depends on the cluster hostname (mit, cern, ...)
    import FCCee_spring2021_ecm91_IDEA
    datasets_spring2021_ecm91 = FCCee_spring2021_ecm91_IDEA.get_datasets(baseDir=baseDir) # list of all datasets
    datasets = [] # list of datasets to be run over

    if args.flavor == "mumu": 
        datasets += functions.filter_datasets(datasets_spring2021_ecm91, ["p8_ee_Zmumu_ecm91", "wzp6_ee_mumu_ecm91p2"])
        #datasets = functions.filter_datasets(datasets_spring2021_ecm91, ["wzp6_gaga_mumu_5_ecm91p2"])
        result = functions.build_and_run(datasets, build_graph_ll, "tmp/output_z_xsec_mumu.root", maxFiles=args.maxFiles) # , norm=True, lumi=150000000

    if args.flavor == "ee":
        datasets += functions.filter_datasets(datasets_spring2021_ecm91, ["p8_ee_Zee_ecm91", "p8_ee_Ztautau_ecm91"])
        result = functions.build_and_run(datasets, build_graph_ll, "tmp/output_z_xsec_ee.root", maxFiles=args.maxFiles, norm=True, lumi=150000000)
 
    if args.flavor == "qq":
        #datasets += functions.filter_datasets(datasets_spring2021_ecm91, ["p8_ee_Zuds_ecm91", "p8_ee_Zcc_ecm91", "p8_ee_Zbb_ecm91"])
        datasets += functions.filter_datasets(datasets_spring2021_ecm91, ["p8_ee_Zuds_ecm91", "wzp6_ee_qq_ecm91p2"])
        result = functions.build_and_run(datasets, build_graph_qq, "tmp/output_z_xsec_qq.root", maxFiles=args.maxFiles, norm=True, lumi=150000000)

    
    
