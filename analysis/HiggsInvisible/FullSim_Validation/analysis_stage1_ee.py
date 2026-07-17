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
            .Alias("parents", "_MCParticles_parents.index")#parent
            .Alias("daughters", "_MCParticles_daughters.index")#daughter
            
            .Define('electron', 'ReconstructedParticle::sel_absType(11)(TightSelectedPandoraPFOs)')
            .Define('electrons','HiggsTools::sort_greater_p(electron)')
            .Define("n_electrons",  "ReconstructedParticle::get_n( electrons ) ")
            .Define("electrons_y",  "ReconstructedParticle::get_y(electrons)")
            .Define("electrons_p",   "ReconstructedParticle::get_p(electrons)")
            .Define("electrons_e",   "ReconstructedParticle::get_e(electrons)") 
            .Define("electrons_tlv", "ReconstructedParticle::get_tlv(electrons)")

   
            .Define('muon', 'ReconstructedParticle::sel_absType(13)(TightSelectedPandoraPFOs)')
            .Define('muons','HiggsTools::sort_greater_p(muon)')
            .Define("n_muons",  "ReconstructedParticle::get_n( muons ) ")
            .Define("muons_y",  "ReconstructedParticle::get_y(muons)")
            .Define("muons_p",   "ReconstructedParticle::get_p(muons)")
            .Define("muons_e",   "ReconstructedParticle::get_e(muons)")
            .Define("muons_tlv", "ReconstructedParticle::get_tlv(muons)")


            # define an alias for muon index collection
            .Alias("Jet", "RefinedVertexJets")
            .Define('Jets','HiggsTools::sort_greater_p(Jet)')
            .Define("jets", "ReconstructedParticle::sel_p(15)(Jets)")
            .Define("n_jets",  "ReconstructedParticle::get_n( jets ) ")
            .Define("jets_y",  "ReconstructedParticle::get_y(jets)")
            .Define("jets_p",   "ReconstructedParticle::get_p(jets)")
            .Define("jets_e",   "ReconstructedParticle::get_e(jets)")
            .Define("jets_tlv", "ReconstructedParticle::get_tlv(jets)")

            # To check if jets are muons
            .Define("deltaR_muJet_00", "(muons_tlv.size()>0 && jets_tlv.size()>0) ? muons_tlv[0].DeltaR(jets_tlv[0]) : -1000")
            .Define("deltaR_muJet_01", "(muons_tlv.size()>0 && jets_tlv.size()>1) ? muons_tlv[0].DeltaR(jets_tlv[1]) : -1000")
            .Define("deltaR_muJet_10", "(muons_tlv.size()>1 && jets_tlv.size()>0) ? muons_tlv[1].DeltaR(jets_tlv[0]) : -1000")
            .Define("deltaR_muJet_11", "(muons_tlv.size()>1 && jets_tlv.size()>1) ? muons_tlv[1].DeltaR(jets_tlv[1]) : -1000")
            .Define("deltaR_eJet_00", "(electrons_tlv.size()>0 && jets_tlv.size()>0) ? electrons_tlv[0].DeltaR(jets_tlv[0]) : -1000")
            .Define("deltaR_eJet_01", "(electrons_tlv.size()>0 && jets_tlv.size()>1) ? electrons_tlv[0].DeltaR(jets_tlv[1]) : -1000")
            .Define("deltaR_eJet_10", "(electrons_tlv.size()>1 && jets_tlv.size()>0) ? electrons_tlv[1].DeltaR(jets_tlv[0]) : -1000")
            .Define("deltaR_eJet_11", "(electrons_tlv.size()>1 && jets_tlv.size()>1) ? electrons_tlv[1].DeltaR(jets_tlv[1]) : -1000")

            # MCParticle
            ####
            .Define("MC_GenID", "MCParticle::get_genStatus(MCParticles)") 
            #.Define("status1", "MCParticle::sel_genStatus(1)(MCParticles)") 
            .Define("status2",  'MCParticle::sel_genStatus(2)(MCParticles)')
            .Define("pdgID", "MCParticle::get_pdg(status2)")
            .Define("W_MC",  "MCParticle::sel_pdgID( 24, true) ( MCParticles )")
            .Define("W_MC_GenID", "MCParticle::get_genStatus(W_MC)")  
            .Define("W_MC_tlv", "MCParticle::get_tlv( W_MC )")
            .Define("W_MC_no", "W_MC.size()")
            .Define("W_MC_m", "MCParticle::get_mass(W_MC)")
            .Define("W_MC_p", "MCParticle::get_p(W_MC)") 
            #.Define("W_MC_daughters", "MCParticle::list_of_stable_particles_from_decay(W_MC, MCParticles, Particle1)")

            
            .Define("Wp_MC", "HiggsTools::gen_sel_pdgIDInt(24,false)(MCParticles)")
            .Define("Wp_MC_no", "Wp_MC.size()")
            .Define("daughter_Wp", "HiggsTools::gen_decay_list(Wp_MC, MCParticles, daughters)")
            .Define("daughter_Wp_no", "daughter_Wp.size()")
            .Define("daughter_Wp_0_pid", "daughter_Wp.size()>0 ? daughter_Wp[0] : -1000")
            .Define("daughter_Wp_1_pid", "daughter_Wp.size()>1 ? daughter_Wp[1] : -1000")

            .Define("Wm_MC", "HiggsTools::gen_sel_pdgIDInt(-24,false)(MCParticles)")
            .Define("Wm_MC_no", "Wm_MC.size()")
            .Define("daughter_Wm", "HiggsTools::gen_decay_list(Wm_MC, MCParticles, daughters)")
            .Define("daughter_Wm_no", "daughter_Wm.size()")
            .Define("daughter_Wm_0_pid", "daughter_Wm.size()>0 ? daughter_Wm[0] : -1000")
            .Define("daughter_Wm_1_pid", "daughter_Wm.size()>1 ? daughter_Wm[1] : -1000")

            .Alias("particles", "electrons")

            .Define("ZCandidate",    "ReconstructedParticle::resonanceBuilder(91)(particles)")
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
            
            # muons
            "n_muons",
            "muons_p",
            "muons_y",
            "muons_e",
            # electrons
            "n_electrons",
            "electrons_p",
            "electrons_y",
            "electrons_e",
            # jets
            "n_jets",
            "jets_p",
            "jets_y",
            "jets_e",
            # deltaR
            "deltaR_muJet_00",
            "deltaR_muJet_01",
            "deltaR_muJet_10",
            "deltaR_muJet_11",
            "deltaR_eJet_00",
            "deltaR_eJet_01",
            "deltaR_eJet_10",
            "deltaR_eJet_11",
            
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