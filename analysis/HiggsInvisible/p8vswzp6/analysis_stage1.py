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
outputDir   = "outputs_HInvjj/test2"

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

            .Define('electrons', 'ReconstructedParticle::sel_absType(11)(TightSelectedPandoraPFOs)')
            # define number of electrons
            .Define("n_electrons",  "ReconstructedParticle::get_n( electrons ) ")
            # Filter at on the number of electrons
            .Filter("n_electrons==0")

            # get reconstructed muons
            .Define('muons', 'ReconstructedParticle::sel_absType(13)(TightSelectedPandoraPFOs)')
            # define number of muons
            .Define("n_muons",  "ReconstructedParticle::get_n( muons ) ")
            # Filter at on the number of muons
            .Filter("n_muons==0")

            # define an alias for muon index collection
            .Alias("Jet", "RefinedVertexJets")
            # define the muon collection
            #.Define("jets",  "ReconstructedParticle::get(Jet2, ReconstructedParticles)")
            .Define("jets", "ReconstructedParticle::sel_pt(15)(Jet)") # Loosest selection at this stage

            # define number of jets
            .Define("n_jets",  "ReconstructedParticle::get_n( jets ) ")
            # Filter at on the number of electrons
            .Filter("n_jets==2")


            # ?? Split qq channel into jet multiplicity
            # ?? in bb channel to improve Mmiss resolution, scale visible 4 vector by 91 / Mvis and recalculate Mmiss


            .Define("jets_pt", "ReconstructedParticle::get_pt(jets)")
            # create branch with jets rapidity
            .Define("jets_y",  "ReconstructedParticle::get_y(jets)")
            # create branch with jets total momentum
            .Define("jets_p",   "ReconstructedParticle::get_p(jets)")
            # create branch with jets energy
            .Define("jets_e",   "ReconstructedParticle::get_e(jets)")

            ####
            .Define("status1", "MCParticle::sel_genStatus(1)(MCParticles)") 
            .Define("status2",  'MCParticle::sel_genStatus(2)(MCParticles)')
            .Define("Z_MC",  "MCParticle::sel_pdgID( 23, false) ( status2 )")
            .Define("Z_MC_GenID", "MCParticle::get_genStatus(Z_MC)")  
            .Define("Z_MC_tlv", "MCParticle::get_tlv( Z_MC )")
            .Define("Z_MC_no", "Z_MC.size()")
            .Define("Z_MC_m", "MCParticle::get_mass(Z_MC)")
            .Define("Z_MC_p", "MCParticle::get_p(Z_MC)")

            # build a candidate Z boson
            .Define("ZCandidate",    "ReconstructedParticle::resonanceBuilder(91)(jets)")
            # Z boson pt
            .Define("ZBosonPt",   "ReconstructedParticle::get_pt(ZCandidate)")
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
            "jets_pt",
            "jets_y",
            "jets_p",
            "jets_e",
            "ZBosonPt",
            "ZBosonMass",
            #"MET",
            "recoil_M",
            "Z_MC_no",
            "Z_MC_m",
            "Z_MC_p",
            "Z_MC_GenID"
        ]
        return branchList