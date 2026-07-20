
import analysis, functions
import ROOT
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--nThreads", type=int, help="number of threads", default=None)
parser.add_argument("--maxFiles", type=int, help="Max number of files (per dataset)", default=-1)
args = parser.parse_args()

ROOT.EnableImplicitMT()
if args.nThreads: 
    ROOT.DisableImplicitMT()
    ROOT.EnableImplicitMT(int(args.nThreads))
print(ROOT.GetThreadPoolSize())

# define histograms
bins_p = (2000, 0, 200) # 100 MeV bins
bins_m_gaga = (3000, 0, 300) # 100 MeV bins
bins_p_gaga = (2000, 0, 200) # 100 MeV bins
bins_recoil = (2000, 0, 200) # 100 MeV bins 

bins_theta = (500, -5, 5)
bins_phi = (500, -5, 5)

bins_count = (50, 0, 50)
bins_pdgid = (60, -30, 30)





def build_graph(df, dataset):

    print("build graph", dataset.name)
    results = []
    sigProcs = ["wzp6_ee_mumuH_ecm240"]
    
    df = df.Define("weight", "1.0")
    weightsum = df.Sum("weight")
    
    
    df = df.Alias("Particle0", "Particle#0.index")
    df = df.Alias("Particle1", "Particle#1.index")
    df = df.Alias("MCRecoAssociations0", "MCRecoAssociations#0.index")
    df = df.Alias("MCRecoAssociations1", "MCRecoAssociations#1.index")
    df = df.Alias("Photon0", "Photon#0.index")
    
    
    # all photons
    df = df.Define("photons", "FCCAnalyses::ReconstructedParticle::get(Photon0, ReconstructedParticles)")
    df = df.Define("photons_p", "FCCAnalyses::ReconstructedParticle::get_p(photons)")
    df = df.Define("photons_theta", "FCCAnalyses::ReconstructedParticle::get_theta(photons)")
    df = df.Define("photons_phi", "FCCAnalyses::ReconstructedParticle::get_phi(photons)")
    df = df.Define("photons_no", "FCCAnalyses::ReconstructedParticle::get_n(photons)")

    results.append(df.Histo1D(("photons_p", "", *bins_p), "photons_p"))
    results.append(df.Histo1D(("photons_theta", "", *bins_theta), "photons_theta"))
    results.append(df.Histo1D(("photons_phi", "", *bins_phi), "photons_phi"))
    results.append(df.Histo1D(("photons_no", "", *bins_count), "photons_no"))
    
    
    # select photons with momentum p > 30 GeV 
    # Higgs -> gamma gamma produces on average 125/2 = 62.5 GeV photons
    df = df.Define("selected_photons", "FCCAnalyses::ReconstructedParticle::sel_p(30)(photons)")
    df = df.Define("selected_photons_p", "FCCAnalyses::ReconstructedParticle::get_p(selected_photons)")
    df = df.Define("selected_photons_theta", "FCCAnalyses::ReconstructedParticle::get_theta(selected_photons)")
    df = df.Define("selected_photons_phi", "FCCAnalyses::ReconstructedParticle::get_phi(selected_photons)")
    df = df.Define("selected_photons_no", "FCCAnalyses::ReconstructedParticle::get_n(selected_photons)")
    
    results.append(df.Histo1D(("selected_photons_p", "", *bins_p), "selected_photons_p"))
    results.append(df.Histo1D(("selected_photons_theta", "", *bins_theta), "selected_photons_theta"))
    results.append(df.Histo1D(("selected_photons_phi", "", *bins_phi), "selected_photons_phi"))
    results.append(df.Histo1D(("selected_photons_no", "", *bins_count), "selected_photons_no"))
    
    
    # require at least 2 photons
    df = df.Filter("selected_photons_no >= 2")
    
    # make the resonance
    df = df.Define("resonance", "FCCAnalyses::resonanceHBuilder(125)(selected_photons)")
    df = df.Filter("resonance.size() > 0")
    
    df = df.Define("resonance_m", "FCCAnalyses::ReconstructedParticle::get_mass(resonance)")
    df = df.Define("resonance_p", "FCCAnalyses::ReconstructedParticle::get_p(resonance)")
    df = df.Define("resonance_recoil",  "FCCAnalyses::ReconstructedParticle::recoilBuilder(240)(resonance)")
    df = df.Define("recoil_m", "FCCAnalyses::ReconstructedParticle::get_mass(resonance_recoil)")

    results.append(df.Histo1D(("resonance_m", "", *bins_m_gaga), "resonance_m"))
    results.append(df.Histo1D(("resonance_p", "", *bins_p_gaga), "resonance_p"))
    results.append(df.Histo1D(("resonance_recoil", "", *bins_recoil), "recoil_m"))
     

 
    return results, weightsum
    
    


if __name__ == "__main__":

    # import spring2021 IDEA samples
    import FCCee_spring2021_IDEA
    datasets = FCCee_spring2021_IDEA.getDatasets(filt="wzp6_ee_mumuH_ecm240")
    
    
    #import FCCee_preproduction_IDEA
    #datasets += FCCee_preproduction_IDEA.getDatasets(filt="wz2p6_ee_mumuH_ecm240_winter_v2")
    #datasets += FCCee_preproduction_IDEA.getDatasets(filt="wz3p6_ee_mumuH_ecm240_winter_v2")
 


    result = functions.build_and_run(datasets, build_graph, "tmp/output_higgs_gaga.root", maxFiles=args.maxFiles)
    
