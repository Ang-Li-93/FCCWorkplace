# run as: fccanalysis run analysis_HInvjj_CLD_stage1.py

#Mandatory: List of processes
processList = {
    #'p8_ee_ZZ_ecm240':{},#Run the full statistics in one output file named <outputDir>/p8_ee_ZZ_ecm240.root
    #'p8_ee_WW_ecm240':{'fraction':0.5, 'chunks':2}, #Run 50% of the statistics in two files named <outputDir>/p8_ee_WW_ecm240/chunk<N>.root
    'wzp6_ee_qqH_ecm240':{'fraction':1., 'output':'wzp6_ee_qqH_ecm240'} #Run 100% of the statistics in one file named <outputDir>/p8_ee_ZH_ecm240_out.root (example on how to change the output name)
    #'wzp6_ee_qqH_ecm240':{'chunks':20, 'output':'wzp6_ee_qqH_ecm240'} #Run 100% of the statistics in one file named <outputDir>/p8_ee_ZH_ecm240_out.root (example on how to change the output name)

}

#Mandatory: Production tag when running over EDM4Hep centrally produced events, this points to the yaml files for getting sample statistics
prodTag     = "FCCee/winter2023/IDEA/"

#Optional: output directory, default is local running directory
outputDir   = "outputs_HInvjj/Validation/"

#Optional: analysisName, default is ""
#analysisName = "My Analysis"

#Optional: ncpus, default is 4
nCPUS       = 1

#Optional running on HTCondor, default is False
runBatch    = False

#Optional batch queue name when running on HTCondor, default is workday
batchQueue = "longlunch"

#Optional computing account when running on HTCondor, default is group_u_FCC.local_gen
#compGroup = "group_u_FCC.local_gen"

#Optional test file
#testFile ="root://eospublic.cern.ch//eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA/wzp6_ee_mumuH_ecm240/events_017670037.root"

import ROOT

ROOT.gInterpreter.Declare("""
#include "FCCAnalyses/ReconstructedParticle.h"
struct sel_type {
  int m_id;
  sel_type (int id) : m_id(id) {}
  ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> operator() (ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in)
  {
    ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> result;
    result.reserve(in.size());
    for (size_t i = 0; i < in.size(); ++i) {
      auto & p = in[i];
      if (std::abs(p.type) == m_id) {
        result.emplace_back(p);
      }
    }
    return result;
  }
};

struct sel_eles {
  ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> operator() (ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in)
  {
    ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> result;
    result.reserve(in.size());
    int typ1 = 0;
    for (size_t i = 0; i < in.size(); ++i) {
      auto & p = in[i];
      if (std::abs(p.type) == 11) {
        if (typ1 == 0) {
          result.emplace_back(p);
          typ1 = p.type;
        }
        else if (typ1 == -p.type) {
          result.emplace_back(p);
          typ1 = -999999;
        }
      }
    }
    return result;
  }
};

struct sel_byPDGID {
  ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> operator() (ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in, int PDGID)
  {
    ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> result;
    result.reserve(in.size());
    int typ1 = 0;
    for (size_t i = 0; i < in.size(); ++i) {
      auto & p = in[i];
      if (std::abs(p.type) == PDGID) {
        if (typ1 == 0) {
          result.emplace_back(p);
          typ1 = p.type;
        }
        else if (typ1 == -p.type) {
          result.emplace_back(p);
          typ1 = -999999;
        }
      }
    }
    return result;
  }
};

struct calc_trues
{
  float operator() (ROOT::VecOps::RVec<edm4hep::MCParticleData> mcp)
  {
    if (mcp.size() < 2) return 0;
    return std::abs(mcp[0].momentum.z) + std::abs(mcp[1].momentum.z);
  }
};

struct calc_trues_recoil
{
  ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> 
  operator() (float trues, ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData> in)
  {
    return FCCAnalyses::ReconstructedParticle::recoilBuilder(trues)(in);
  }
};
""")


#Mandatory: RDFanalysis class where the use defines the operations on the TTree
class RDFanalysis():

    #__________________________________________________________
    #Mandatory: analysers funtion to define the analysers to process, please make sure you return the last dataframe, in this example it is df2
    def analysers(df):
        df2 = (

            # it looks like the 'ReconstructedParticles' are implemented as 'ROOT::VecOps::RVec':
            # https://root.cern.ch/doc/master/classROOT_1_1VecOps_1_1RVec.html

            df
            #.Define('BoostedPandoraPFOs', 'boost(0.030, PandoraPFOs)')
            .Alias('TightSelectedPandoraPFOsIndex', 'TightSelectedPandoraPFOs_objIdx.index')
            .Define('TightSelectedPandoraPFOs', 'ReconstructedParticle::get (TightSelectedPandoraPFOsIndex, PandoraPFOs)')
            .Alias("Particle0", "_MCParticles_parents.index")#parent
            .Alias("Particle1", "_MCParticles_daughters.index")#daughter
            
            .Define('electrons', 'ReconstructedParticle::sel_absType(11)(TightSelectedPandoraPFOs)')
            # define number of electrons
            .Define("n_electrons",  "ReconstructedParticle::get_n( electrons ) ")
            # Filter at on the number of electrons
            #.Filter("n_electrons==0")

            # get reconstructed muons
            .Define('muons', 'ReconstructedParticle::sel_absType(13)(TightSelectedPandoraPFOs)')
            # define number of muons
            .Define("n_muons",  "ReconstructedParticle::get_n( muons ) ")
            # Filter at on the number of muons
            #.Filter("n_muons>=2")

            # define an alias for muon index collection
            .Alias("Jet", "RefinedVertexJets")
            # define the muon collection
            #.Define("jets",  "ReconstructedParticle::get(Jet2, ReconstructedParticles)")
            .Define("jets", "ReconstructedParticle::sel_p(15)(Jet)") # Loosest selection at this stage

            # define number of jets
            .Define("n_jets",  "ReconstructedParticle::get_n( jets ) ")
            # Filter at on the number of electrons
            #.Filter("n_jets==0")


            # ?? Split qq channel into jet multiplicity
            # ?? in bb channel to improve Mmiss resolution, scale visible 4 vector by 91 / Mvis and recalculate Mmiss


            .Define("muons_y",  "ReconstructedParticle::get_y(muons)")
            # create branch with jets total momentum
            .Define("muons_p",   "ReconstructedParticle::get_p(muons)")
            # create branch with jets energy
            .Define("muons_e",   "ReconstructedParticle::get_e(muons)")

            ####
            .Define("MC_GenID", "MCParticle::get_genStatus(MCParticles)") 
            #.Define("status1", "MCParticle::sel_genStatus(1)(MCParticles)") 
            .Define("status2",  'MCParticle::sel_genStatus(2)(MCParticles)')
            .Define("pdgID", "MCParticle::get_pdg(status2)")
            .Define("W_MC",  "MCParticle::sel_pdgID( 24, true) ( status2 )")
            .Define("W_MC_GenID", "MCParticle::get_genStatus(W_MC)")  
            .Define("W_MC_tlv", "MCParticle::get_tlv( W_MC )")
            .Define("W_MC_no", "W_MC.size()")
            .Define("W_MC_m", "MCParticle::get_mass(W_MC)")
            .Define("W_MC_p", "MCParticle::get_p(W_MC)") 
            #.Define("W_MC_daughters", "MCParticle::list_of_stable_particles_from_decay(W_MC, MCParticles, Particle1)")

            
            .Define("Wp_MC", "HiggsTools::gen_sel_pdgIDInt(24,false)(MCParticles)")
            .Define("Wp_MC_no", "Wp_MC.size()")
            .Define("daughter_Wp", "HiggsTools::gen_decay_list(Wp_MC, MCParticles, Particle1)")
            .Define("daughter_Wp_no", "daughter_Wp.size()")
            .Define("daughter_Wp_0_pid", "daughter_Wp.size()>0 ? daughter_Wp[0] : -1000")
            .Define("daughter_Wp_1_pid", "daughter_Wp.size()>1 ? daughter_Wp[1] : -1000")

            .Define("Wm_MC", "HiggsTools::gen_sel_pdgIDInt(-24,false)(status2)")
            .Define("Wm_MC_no", "Wm_MC.size()")
            .Define("daughter_Wm", "HiggsTools::gen_decay_list(Wm_MC, MCParticles, Particle1)")
            .Define("daughter_Wm_no", "daughter_Wm.size()")
            .Define("daughter_Wm_0_pid", "daughter_Wm.size()>0 ? daughter_Wm[0] : -1000")
            .Define("daughter_Wm_1_pid", "daughter_Wm.size()>1 ? daughter_Wm[1] : -1000")

            # build a candidate Z boson
            .Define("ZCandidate",    "ReconstructedParticle::resonanceBuilder(91)(muons)")
            # Z boson pt
            .Define("ZBosonP",   "ReconstructedParticle::get_p(ZCandidate)")
            # Z boson mass
            .Define("ZBosonMass",   "ReconstructedParticle::get_mass(ZCandidate)")
            .Define("recoilParticle",  "ReconstructedParticle::recoilBuilder(240)(ZCandidate)")
            # create branch with recoil mass
            .Define("recoil_M","ReconstructedParticle::get_mass(recoilParticle)")



        )
        return df2 

    #__________________________________________________________
    #Mandatory: output function, please make sure you return the branchlist as a python list
    def output():
        branchList = [
            "n_muons",
            "n_electrons",
            "n_jets",
            "muons_p",
            "muons_y",
            "muons_e",
            "ZBosonP",
            "ZBosonMass",
            #"MET",
            "recoil_M",
            "MC_GenID",
            "W_MC_no",
            "W_MC_m",
            "W_MC_p",
            "W_MC_GenID",
            "pdgID",
            "Wp_MC_no",
            "daughter_Wp_no",
            "daughter_Wp_0_pid",
            "daughter_Wp_1_pid",
            "Wm_MC_no",
            "daughter_Wm_no",
            "daughter_Wm_0_pid",
            "daughter_Wm_1_pid",
            #"W_MC_daughters",
        ]
        return branchList