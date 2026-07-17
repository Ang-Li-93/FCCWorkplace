import os
import sys

# Get the directory of the current script and add it to Python's search path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from userConfig import loc, train_vars
import os, copy, urllib.request

#Mandatory: List of processes

processList = {
    #background
    'wzp6_ee_mumuH_ecm240':           {'chunks': 20},# 'fraction':0.01},

    'p8_ee_WW_ecm240':                {'chunks': 80},#, 'fraction':0.10},
    'wzp6_egamma_eZ_Zmumu_ecm240':    {'chunks': 20},#, 'fraction':0.10},
    'wzp6_gammae_eZ_Zmumu_ecm240':    {'chunks': 20},#, 'fraction':0.10},
    'wzp6_ee_mumu_ecm240':            {'chunks': 20},#, 'fraction':0.10},
    'p8_ee_ZZ_ecm240':                {'chunks': 20},#, 'fraction':0.10},
    'wzp6_gaga_mumu_60_ecm240':       {'chunks': 20},#, 'fraction':0.10},

    #Diagonal Higgs Decays
    'wzp6_ee_mumuH_Hbb_ecm240':       {'chunks': 20},#, 'fraction':0.01},
    'wzp6_ee_mumuH_Hss_ecm240':        {'chunks': 20},#, 'fraction':0.01},
    'wzp6_ee_mumuH_Hcc_ecm240':        {'chunks': 20},#, 'fraction':0.01},
    'wzp6_ee_mumuH_Hgg_ecm240':       {'chunks': 20},#, 'fraction':0.01},
    'wzp6_ee_mumuH_HWW_ecm240':       {'chunks': 20},#, 'fraction':0.01},
    'wzp6_ee_mumuH_HZZ_ecm240':       {'chunks': 20},#, 'fraction':0.01},
    'wzp6_ee_mumuH_HZa_ecm240':       {'chunks': 20},#, 'fraction':0.01},
    'wzp6_ee_mumuH_Hgg_ecm240':       {'chunks': 20},
    'wzp6_ee_mumuH_HWW_ecm240':         {'chunks': 20},
    'wzp6_ee_mumuH_HZZ_noInv_ecm240':   {'chunks': 20},
    'wzp6_ee_mumuH_HZa_ecm240':         {'chunks': 20},
    'wzp6_ee_mumuH_Htautau_ecm240':     {'chunks': 20},
    }
    
#Mandatory: Production tag when running over EDM4Hep centrally produced events, this points to the yaml files for getting sample statistics
prodTag     = "FCCee/winter2023/IDEA/"
outputDirEos= "/eos/user/d/dduan/FCCee/Hbs/mumu/BDT_analysis_samples"
eosType = "eosuser"
nCPUS       = 4
batchQueue = 'workday' #"longlunch"
compGroup = "group_u_FCC.local_gen"
runBatch    = True

outputDir = "/eos/user/d/dduan/FCCee/Hbs/mumu/temp_files_for_bdt_batch"
#userBatchConfig = "/afs/cern.ch/user/d/dduan/private/FCCWorkplace/analysis/ZH_XSec/FinalReport/S240/mumu/userBatch.Config"

import ROOT
vars_list = train_vars
num_features = len(train_vars)
ROOT.gInterpreter.ProcessLine(f'''
  TMVA::Experimental::RBDT<> bdt("Z_Recoil_BDT", "/eos/user/d/dduan/FCCee/Hbs/mumu/BDT/xgb_bdt.root");
  computeModel1 = TMVA::Experimental::Compute<{num_features}, float>(bdt);
''')

## ParticleNet flavor tagger model (winter2023), trained on 9M jets
model_name = 'fccee_flavtagging_edm4hep_wc'
url_model_dir = "https://fccsw.web.cern.ch/fccsw/testsamples/jet_flavour_tagging/winter2023/wc_pt_7classes_12_04_2023/"
model_dir = '/eos/experiment/fcc/ee/jet_flavour_tagging/winter2023/wc_pt_7classes_12_04_2023/'

#Old Model without u and d tags
# model_name    = "fccee_flavtagging_edm4hep_wc_v1"
# url_model_dir = "https://fccsw.web.cern.ch/fccsw/testsamples/jet_flavour_tagging/winter2023/wc_pt_13_01_2022/"
# model_dir     = "/eos/experiment/fcc/ee/jet_flavour_tagging/winter2023/wc_pt_13_01_2022/"

def get_file_path(url, filename):
    if os.path.exists(filename):
        return os.path.abspath(filename)
    urllib.request.urlretrieve(url, os.path.basename(url))
    return os.path.basename(url)

weaver_preproc = get_file_path("{}/{}.json".format(url_model_dir, model_name),
                               "{}/{}.json".format(model_dir,     model_name))
weaver_model   = get_file_path("{}/{}.onnx".format(url_model_dir, model_name),
                               "{}/{}.onnx".format(model_dir,     model_name))

from addons.ONNXRuntime.jetFlavourHelper import JetFlavourHelper
from addons.FastJet.jetClusteringHelper import ExclusiveJetClusteringHelper

jetFlavourHelper    = None
jetClusteringHelper = None

import ROOT
ROOT.gInterpreter.Declare("""
// Gen-level H->bs tag: 1 if H -> bs+sb, 0 otherwise, -1 if no Higgs found
int hbs_gen_tag(ROOT::VecOps::RVec<int> daughters) {
    if (daughters.size() < 2) return -1;
    int id0 = abs(daughters[0]), id1 = abs(daughters[1]);
    if ((id0 == 5 && id1 == 3) || (id0 == 3 && id1 == 5)) return 1;
    return 0;
}

// ── gen-quark lookup for whizard H->qq BSM samples ───────────────────────────
// In wzp6_ee_mumuH_Hxx samples the Higgs is only an s-channel propagator
// (whizard restriction "5+6~h1"), so it is never stored in the MC record.
// The H decay products instead appear as direct e+e- daughters of the hard
// process. This helper finds the b and s quarks among them and returns their
// indices [b_idx, s_idx] (or empty if not found).
ROOT::VecOps::RVec<int> find_hbs_quark_indices(
    const ROOT::VecOps::RVec<edm4hep::MCParticleData>& Particle,
    const ROOT::VecOps::RVec<int>& Particle0)
{
    int b_idx = -1, s_idx = -1;
    for (size_t i = 0; i < Particle.size(); ++i) {
        int apdg = std::abs(Particle[i].PDG);
        if (apdg != 3 && apdg != 5) continue;
        // require exactly two parents, both electrons (whizard hard-process partons)
        int pb = Particle[i].parents_begin;
        int pe = Particle[i].parents_end;
        if (pe - pb != 2) continue;
        bool all_e = true;
        for (int j = pb; j < pe; ++j) {
            int pidx = Particle0[j];
            if (pidx < 0 || pidx >= (int)Particle.size() ||
                std::abs(Particle[pidx].PDG) != 11) { all_e = false; break; }
        }
        if (!all_e) continue;
        if      (apdg == 5 && b_idx < 0) b_idx = (int)i;
        else if (apdg == 3 && s_idx < 0) s_idx = (int)i;
        if (b_idx >= 0 && s_idx >= 0) break;
    }
    ROOT::VecOps::RVec<int> result;
    if (b_idx >= 0 && s_idx >= 0) { result.push_back(b_idx); result.push_back(s_idx); }
    return result;
}

// Sentinel-returning accessors for a single MCParticle by index.
// Used to fill gen_{b,s}_* with -999 when the quark wasn't found
// (e.g. non-BSM samples or events where the helper fails).
int   safe_at(const ROOT::VecOps::RVec<int>& v, size_t i) { return i < v.size() ? v[i] : -1; }
float gen_q_p(const ROOT::VecOps::RVec<edm4hep::MCParticleData>& P, int idx) {
    if (idx < 0 || idx >= (int)P.size()) return -999.f;
    const auto& p = P[idx];
    return std::sqrt(p.momentum.x*p.momentum.x + p.momentum.y*p.momentum.y + p.momentum.z*p.momentum.z);
}
float gen_q_theta(const ROOT::VecOps::RVec<edm4hep::MCParticleData>& P, int idx) {
    if (idx < 0 || idx >= (int)P.size()) return -999.f;
    const auto& p = P[idx];
    float pm = std::sqrt(p.momentum.x*p.momentum.x + p.momentum.y*p.momentum.y + p.momentum.z*p.momentum.z);
    return pm > 0 ? std::acos(p.momentum.z / pm) : -999.f;
}
float gen_q_phi(const ROOT::VecOps::RVec<edm4hep::MCParticleData>& P, int idx) {
    if (idx < 0 || idx >= (int)P.size()) return -999.f;
    return std::atan2(P[idx].momentum.y, P[idx].momentum.x);
}
int gen_q_pdg(const ROOT::VecOps::RVec<edm4hep::MCParticleData>& P, int idx) {
    return (idx < 0 || idx >= (int)P.size()) ? 0 : P[idx].PDG;
}
""")

class RDFanalysis():

    def analysers(df):

        df = df.Alias("Lepton0",            "Muon#0.index")
        df = df.Alias("MCRecoAssociations0", "MCRecoAssociations#0.index")
        df = df.Alias("MCRecoAssociations1", "MCRecoAssociations#1.index")
        df = df.Alias("Particle0",           "Particle#0.index")
        df = df.Alias("Particle1",           "Particle#1.index")

        # ── muon selection ─────────────────────────────────────────────────────
        df = df.Define("leps_all",    "FCCAnalyses::ReconstructedParticle::get(Lepton0, ReconstructedParticles)")
        df = df.Define("leps",        "FCCAnalyses::ReconstructedParticle::sel_p(20)(leps_all)")
        df = df.Define("leps_no",     "FCCAnalyses::ReconstructedParticle::get_n(leps)")
        df = df.Define("leps_q",      "FCCAnalyses::ReconstructedParticle::get_charge(leps)")
        df = df.Define("leps_iso",    "HiggsTools::coneIsolation(0.01, 0.5)(leps, ReconstructedParticles)")
        df = df.Define("leps_sel_iso","HiggsTools::sel_isol(0.25)(leps, leps_iso)")

        df = df.Filter("leps_no >= 1 && leps_sel_iso.size() > 0")
        df = df.Filter("leps_no >= 2 && abs(Sum(leps_q)) < leps_q.size()")

        # ── remove muons before jet clustering ─────────────────────────────────
        df = df.Define("ReconstructedParticlesNoMuons",
                    "FCCAnalyses::ReconstructedParticle::remove(ReconstructedParticles, leps)")

        # ── exclusive 2-jet clustering on hadronic system ──────────────────────
        global jetClusteringHelper, jetFlavourHelper

        collections = {
            "GenParticles":      "Particle",
            "PFParticles":       "ReconstructedParticles",
            "PFTracks":          "EFlowTrack",
            "PFPhotons":         "EFlowPhoton",
            "PFNeutralHadrons":  "EFlowNeutralHadron",
            "TrackState":        "EFlowTrack_1",
            "TrackerHits":       "TrackerHits",
            "CalorimeterHits":   "CalorimeterHits",
            "dNdx":              "EFlowTrack_2",
            "PathLength":        "EFlowTrack_L",
            "Bz":                "magFieldBz",
        }
        collections_nomuons = copy.deepcopy(collections)
        collections_nomuons["PFParticles"] = "ReconstructedParticlesNoMuons"

        jetClusteringHelper = ExclusiveJetClusteringHelper(collections_nomuons["PFParticles"], 2)
        df = jetClusteringHelper.define(df)

        jetFlavourHelper = JetFlavourHelper(
            collections_nomuons,
            jetClusteringHelper.jets,
            jetClusteringHelper.constituents,
        )
        df = jetFlavourHelper.define(df)
        df = jetFlavourHelper.inference(weaver_preproc, weaver_model, df)

        # require 2 jets
        df = df.Filter("event_njet > 1")

        # ── dijet (Higgs candidate) ─────────────────────────────────────────────
        df = df.Define("jets_p4", "JetConstituentsUtils::compute_tlv_jets({})".format(jetClusteringHelper.jets))
        df = df.Define("higgs_m",     "JetConstituentsUtils::InvariantMass(jets_p4[0], jets_p4[1])")
        df = df.Define("jet1_p",      "jet_p[0]")
        df = df.Define("jet2_p",      "jet_p[1]")
        df = df.Define("jet1_theta",  "jet_theta[0]")
        df = df.Define("jet2_theta",  "jet_theta[1]")
        df = df.Define("jet1_phi",    "jet_phi[0]")
        df = df.Define("jet2_phi",    "jet_phi[1]")
        df = df.Define("jet1_mass",   "jet_mass[0]")
        df = df.Define("jet2_mass",   "jet_mass[1]")
        df = df.Define("jet1_btag",   "recojet_isB[0]")
        df = df.Define("jet2_btag",   "recojet_isB[1]")
        df = df.Define("jet1_stag",   "recojet_isS[0]")
        df = df.Define("jet2_stag",   "recojet_isS[1]")
        # max b-tag and matched s-tag (jet with highest b-score is the b-jet candidate)
        df = df.Define("btag_max",    "std::max(jet1_btag, jet2_btag)")
        df = df.Define("stag_other",  "jet1_btag > jet2_btag ? jet2_stag : jet1_stag")

        #We want more than just b and s tags, our events include much more than that. 
        #At risk of overdoing it, lets include all of them:
        df = df.Define("jet1_utag",   "recojet_isU[0]")
        df = df.Define("jet2_utag",   "recojet_isU[1]")
        df = df.Define("jet1_dtag",   "recojet_isD[0]")
        df = df.Define("jet2_dtag",   "recojet_isD[1]")
        df = df.Define("jet1_ctag",   "recojet_isC[0]")
        df = df.Define("jet2_ctag",   "recojet_isC[1]")
        df = df.Define("jet1_Gtag",   "recojet_isG[0]")
        df = df.Define("jet2_Gtag",   "recojet_isG[1]")
        df = df.Define("jet1_tautag",   "recojet_isTAU[0]")
        df = df.Define("jet2_tautag",   "recojet_isTAU[1]")

        # Other jet variables
        df = df.Define('event_d12', 'JetClusteringUtils::get_exclusive_dmerge(_jet, 1)')
        df = df.Define('event_d23', 'JetClusteringUtils::get_exclusive_dmerge(_jet, 2)')
        df = df.Define('event_d34', 'JetClusteringUtils::get_exclusive_dmerge(_jet, 3)')
        df = df.Define('event_d45', 'JetClusteringUtils::get_exclusive_dmerge(_jet, 4)')  

        df = df.Define('jet1_E', 'jet_e[0]')
        df = df.Define('jet2_E', 'jet_e[1]')

        # df = df.Define('jet1_nconst', 'jet_nconst[0]')
        # df = df.Define('jet2_nconst', 'jet_nconst[1]')
        df = df.Define('jet1_nconst', '(float)jet_nconst[0]')
        df = df.Define('jet2_nconst', '(float)jet_nconst[1]')

        # ── Z resonance from muon pair ──────────────────────────────────────────
        df = df.Define("zbuilder_result",
                    "HiggsTools::resonanceBuilder_mass_recoil(91.2, 125, 0.4, 240, false)"
                    "(leps, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0, Particle1)")
        df = df.Define("zll",      "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result[0]}")
        df = df.Define("zll_leps", "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result[1], zbuilder_result[2]}")
        df = df.Define("zll_m",    "FCCAnalyses::ReconstructedParticle::get_mass(zll)[0]")
        df = df.Define("zll_p",    "FCCAnalyses::ReconstructedParticle::get_p(zll)[0]")
        df = df.Define("zll_theta","FCCAnalyses::ReconstructedParticle::get_theta(zll)[0]")
        df = df.Define("zll_recoil",   "FCCAnalyses::ReconstructedParticle::recoilBuilder(240)(zll)")
        df = df.Define("zll_recoil_m", "FCCAnalyses::ReconstructedParticle::get_mass(zll_recoil)[0]")

        df = df.Define("sorted_zll_leptons",        "HiggsTools::sort_greater_p(zll_leps)")
        df = df.Define("sorted_zll_leptons_p",      "FCCAnalyses::ReconstructedParticle::get_p(sorted_zll_leptons)")
        df = df.Define("sorted_zll_leptons_theta",  "FCCAnalyses::ReconstructedParticle::get_theta(sorted_zll_leptons)")
        df = df.Define("leading_zll_lepton_p",      "sorted_zll_leptons_p.at(0)")
        df = df.Define("leading_zll_lepton_theta",  "sorted_zll_leptons_theta.at(0)")
        df = df.Define("subleading_zll_lepton_p",   "sorted_zll_leptons_p.at(1)")
        df = df.Define("subleading_zll_lepton_theta","sorted_zll_leptons_theta.at(1)")

        df = df.Define("zll_Leptons_acolinearity", "HiggsTools::acolinearity(sorted_zll_leptons)")
        df = df.Define("zll_Leptons_acoplanarity", "HiggsTools::acoplanarity(sorted_zll_leptons)")
        df = df.Define("zll_leptons_acolinearity",
                    "zll_Leptons_acolinearity.size()>0 ? zll_Leptons_acolinearity.at(0) : -999.f")
        df = df.Define("zll_leptons_acoplanarity",
                    "zll_Leptons_acoplanarity.size()>0 ? zll_Leptons_acoplanarity.at(0) : -999.f")

        df = df.Define("cosTheta_miss", "HiggsTools::get_cosTheta(MissingET)[0]")

        # Z selection window
        # df = df.Filter("zll_m > 86 && zll_m < 96")
        # df = df.Filter("zll_p > 20 && zll_p < 70")
        # df = df.Filter("zll_recoil_m > 120 && zll_recoil_m < 140")

        # ── gen-level H->bs tag (auxiliary; not the primary BDT label) ──────────
        #  is_Hbs =  1 : Higgs found in MC, daughters are b+s
        #                (only possible in FCNC/BSM samples; never in SM H decays)
        #  is_Hbs =  0 : Higgs found in MC, daughters are something else
        #                (e.g. inclusive wzp6_ee_mumuH_ecm240, where pythia
        #                produces a real Higgs that decays per SM branching ratios)
        #  is_Hbs = -1 : no PDG=25 Higgs stored in the MC record. This is by
        #                design in the dedicated wzp6_ee_mumuH_Hbs_ecm240 sample:
        #                whizard generates e+e- -> mu+mu- bs̄ (+ c.c.) as a single
        #                2->4 matrix element with the restriction $5+6~h1, so the
        #                Higgs is only an s-channel propagator and never appears
        #                as an on-shell particle. For these events the signal
        #                label comes from the sample name (mode_names["mumuH_Hbs"]
        #                in userConfig.py), not from this branch.
        df = df.Define("higgs_MC",        "HiggsTools::gen_sel_pdgIDInt(25,false)(Particle)")
        df = df.Define("higgs_daughters", "HiggsTools::gen_decay_list(higgs_MC, Particle, Particle1)")
        df = df.Define("is_Hbs",          "hbs_gen_tag(higgs_daughters)")

        # ── gen-quark kinematics for tagger truth-matching (BSM Hbs samples) ───
        # Whizard wzp6_ee_mumuH_Hbs samples don't store the H itself, but the
        # b and s quarks from the H vertex appear as direct e+e- daughters.
        # We save their kinematics so the BDT-prep / efficiency script can
        # ΔR-match them to the reco jets and measure per-jet tagger response.
        # Sentinel -999 (and pdg=0) on samples where the quarks aren't found
        # (e.g. inclusive mumuH, where the H is a real particle and the b/s
        # don't sit as direct e+e- daughters).
        df = df.Define("hbs_q_idx", "find_hbs_quark_indices(Particle, Particle0)")
        df = df.Define("_b_idx",    "safe_at(hbs_q_idx, 0)")
        df = df.Define("_s_idx",    "safe_at(hbs_q_idx, 1)")
        df = df.Define("gen_b_p",     "gen_q_p(Particle, _b_idx)")
        df = df.Define("gen_b_theta", "gen_q_theta(Particle, _b_idx)")
        df = df.Define("gen_b_phi",   "gen_q_phi(Particle, _b_idx)")
        df = df.Define("gen_b_pdg",   "gen_q_pdg(Particle, _b_idx)")
        df = df.Define("gen_s_p",     "gen_q_p(Particle, _s_idx)")
        df = df.Define("gen_s_theta", "gen_q_theta(Particle, _s_idx)")
        df = df.Define("gen_s_phi",   "gen_q_phi(Particle, _s_idx)")
        df = df.Define("gen_s_pdg",   "gen_q_pdg(Particle, _s_idx)")

        #MET
        df = df.Define("met_p",     "FCCAnalyses::ReconstructedParticle::get_p(MissingET)[0]")
        df = df.Define("met_pt",    "FCCAnalyses::ReconstructedParticle::get_pt(MissingET)[0]")
        df = df.Define("met_theta", "FCCAnalyses::ReconstructedParticle::get_theta(MissingET)[0]")
        df = df.Define("met_phi",   "FCCAnalyses::ReconstructedParticle::get_phi(MissingET)[0]")

        #Total Reconstructed Mass/Energy

        df = df.Define("total_p4",
            "auto h = jets_p4[0] + jets_p4[1];"
            "TLorentzVector l1, l2, met;"
            "l1.SetXYZM(zll_leps[0].momentum.x, zll_leps[0].momentum.y, zll_leps[0].momentum.z, zll_leps[0].mass);"
            "l2.SetXYZM(zll_leps[1].momentum.x, zll_leps[1].momentum.y, zll_leps[1].momentum.z, zll_leps[1].mass);"
            "met.SetXYZM(MissingET[0].momentum.x, MissingET[0].momentum.y, MissingET[0].momentum.z, 0);"
            "return h + l1 + l2 + met;")
        df = df.Define("total_m", "total_p4.M()")
        df = df.Define("total_e", "total_p4.E()")

        #partial reconstructions
        df = df.Define("higgs_met", 
            "auto h = jets_p4[0] + jets_p4[1];"
            "TLorentzVector met;"
            "met.SetXYZM(MissingET[0].momentum.x, MissingET[0].momentum.y, MissingET[0].momentum.z, 0);"
            "return h + met;")
        df = df.Define("higgs_met_m", "higgs_met.M()")
        df = df.Define("higgs_met_e", "higgs_met.E()")

        #MET
        df = df.Define("met_px", "MissingET[0].momentum.x")
        df = df.Define("met_py", "MissingET[0].momentum.y")
        df = df.Define("met_pz", "MissingET[0].momentum.z")

        #Charge of jets 
        #Jet substructure

        #Define MVA 

        df = df.Define("MVAVec", ROOT.computeModel1, list(train_vars))
        for i in range(8):
            df = df.Define(f"BDTscore_class{i}", f"MVAVec.at({i})")

        for i in range(6):
            other_decays = [f"BDTscore_class{j}" for j in range(6) if j != i]
            sum_string = " + ".join(other_decays)
            df = df.Define(f"norm_prob{i}", f"BDTscore_class{i} / (1.0 - ({sum_string}))")
        
        # #Following the lead of the sample script, we vary the momentum for the purpose of uncertainty calculations later:

        # # ── Systematics: Muon Momentum Scale Up ─────────────────────────────────
        # df = df.Define("leps_scaleup", "HiggsTools::lepton_momentum_scale(1e-5)(leps)")
        # # Shift MET based on the changed leptons
        # df = df.Define("MissingET_scaleup", 
        #             "auto met = MissingET[0];"
        #             "float dx = 0.0; float dy = 0.0; float dz = 0.0;"
        #             "for(size_t i=0; i<leps.size(); ++i) {"
        #             "  dx += (leps_scaleup[i].momentum.x - leps[i].momentum.x);"
        #             "  dy += (leps_scaleup[i].momentum.y - leps[i].momentum.y);"
        #             "  dz += (leps_scaleup[i].momentum.z - leps[i].momentum.z);"
        #             "}"
        #             "met.momentum.x -= dx; met.momentum.y -= dy; met.momentum.z -= dz;"
        #             "return ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{met};")

        # # Rebuild the Z resonance and its daughters
        # df = df.Define("zbuilder_result_scaleup",
        #             "HiggsTools::resonanceBuilder_mass_recoil(91.2, 125, 0.4, 240, false)"
        #             "(leps_scaleup, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0, Particle1)")
        # df = df.Define("zll_scaleup",      "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result_scaleup[0]}")
        # df = df.Define("zll_leps_scaleup", "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result_scaleup[1], zbuilder_result_scaleup[2]}")
        # df = df.Define("zll_m_scaleup",    "FCCAnalyses::ReconstructedParticle::get_mass(zll_scaleup)[0]")
        # df = df.Define("zll_p_scaleup",    "FCCAnalyses::ReconstructedParticle::get_p(zll_scaleup)[0]")
        # df = df.Define("zll_theta_scaleup","FCCAnalyses::ReconstructedParticle::get_theta(zll_scaleup)[0]")
        # df = df.Define("zll_recoil_scaleup",   "FCCAnalyses::ReconstructedParticle::recoilBuilder(240)(zll_scaleup)")
        # df = df.Define("zll_recoil_m_scaleup", "FCCAnalyses::ReconstructedParticle::get_mass(zll_recoil_scaleup)[0]")

        # # Lepton kinematics
        # df = df.Define("sorted_zll_leptons_scaleup",        "HiggsTools::sort_greater_p(zll_leps_scaleup)")
        # df = df.Define("sorted_zll_leptons_p_scaleup",      "FCCAnalyses::ReconstructedParticle::get_p(sorted_zll_leptons_scaleup)")
        # df = df.Define("sorted_zll_leptons_theta_scaleup",  "FCCAnalyses::ReconstructedParticle::get_theta(sorted_zll_leptons_scaleup)")
        # df = df.Define("leading_zll_lepton_p_scaleup",      "sorted_zll_leptons_p_scaleup.at(0)")
        # df = df.Define("leading_zll_lepton_theta_scaleup",  "sorted_zll_leptons_theta_scaleup.at(0)")
        # df = df.Define("subleading_zll_lepton_p_scaleup",   "sorted_zll_leptons_p_scaleup.at(1)")
        # df = df.Define("subleading_zll_lepton_theta_scaleup","sorted_zll_leptons_theta_scaleup.at(1)")

        # # Angular correlations
        # df = df.Define("zll_Leptons_acolinearity_scaleup", "HiggsTools::acolinearity(sorted_zll_leptons_scaleup)")
        # df = df.Define("zll_Leptons_acoplanarity_scaleup", "HiggsTools::acoplanarity(sorted_zll_leptons_scaleup)")
        # df = df.Define("zll_leptons_acolinearity_scaleup",
        #             "zll_Leptons_acolinearity_scaleup.size()>0 ? zll_Leptons_acolinearity_scaleup.at(0) : -999.f")
        # df = df.Define("zll_leptons_acoplanarity_scaleup",
        #             "zll_Leptons_acoplanarity_scaleup.size()>0 ? zll_Leptons_acoplanarity_scaleup.at(0) : -999.f")

        # # Shifted MET Observables
        # df = df.Define("cosTheta_miss_scaleup", "HiggsTools::get_cosTheta(MissingET_scaleup)[0]")
        # df = df.Define("met_p_scaleup",     "FCCAnalyses::ReconstructedParticle::get_p(MissingET_scaleup)[0]")
        # df = df.Define("met_pt_scaleup",    "FCCAnalyses::ReconstructedParticle::get_pt(MissingET_scaleup)[0]")
        # df = df.Define("met_theta_scaleup", "FCCAnalyses::ReconstructedParticle::get_theta(MissingET_scaleup)[0]")
        # df = df.Define("met_phi_scaleup",   "FCCAnalyses::ReconstructedParticle::get_phi(MissingET_scaleup)[0]")
        # df = df.Define("met_px_scaleup",    "MissingET_scaleup[0].momentum.x")
        # df = df.Define("met_py_scaleup",    "MissingET_scaleup[0].momentum.y")
        # df = df.Define("met_pz_scaleup",    "MissingET_scaleup[0].momentum.z")

        # # Shifted Event-wide Total Reconstruction Energy / Masses
        # df = df.Define("total_p4_scaleup",
        #     "auto h = jets_p4[0] + jets_p4[1];"
        #     "TLorentzVector l1, l2, met;"
        #     "l1.SetXYZM(zll_leps_scaleup[0].momentum.x, zll_leps_scaleup[0].momentum.y, zll_leps_scaleup[0].momentum.z, zll_leps_scaleup[0].mass);"
        #     "l2.SetXYZM(zll_leps_scaleup[1].momentum.x, zll_leps_scaleup[1].momentum.y, zll_leps_scaleup[1].momentum.z, zll_leps_scaleup[1].mass);"
        #     "met.SetXYZM(MissingET_scaleup[0].momentum.x, MissingET_scaleup[0].momentum.y, MissingET_scaleup[0].momentum.z, 0);"
        #     "return h + l1 + l2 + met;")
        # df = df.Define("total_m_scaleup", "total_p4_scaleup.M()")
        # df = df.Define("total_e_scaleup", "total_p4_scaleup.E()")

        # # Shifted Partial Reconstructions (Higgs + MET)
        # df = df.Define("higgs_met_scaleup", 
        #     "auto h = jets_p4[0] + jets_p4[1];"
        #     "TLorentzVector met;"
        #     "met.SetXYZM(MissingET_scaleup[0].momentum.x, MissingET_scaleup[0].momentum.y, MissingET_scaleup[0].momentum.z, 0);"
        #     "return h + met;")
        # df = df.Define("higgs_met_m_scaleup", "higgs_met_scaleup.M()")
        # df = df.Define("higgs_met_e_scaleup", "higgs_met_scaleup.E()")


        # # ── Define MVA Scale Up ─────────────────────────────────────────────────
        # # Generating the list of scaleup variable names to pass into the BDT
        # existing_columns = df.GetColumnNames()
        # train_vars_scaleup = [
        #     f"{var}_scaleup" if f"{var}_scaleup" in existing_columns else var 
        #     for var in train_vars
        # ]
        # df = df.Define("MVAVec_scaleup", ROOT.computeModel1, train_vars_scaleup)
        # df = df.Define("BDTscore_scaleup", "MVAVec_scaleup.at(0)")

        # #–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
        # #Following the lead of the sample script, we vary the momentum again, this time downwards:

        # df = df.Define("leps_scaledw", "HiggsTools::lepton_momentum_scale(-1e-5)(leps)")
        # df = df.Define("MissingET_scaledw", 
        #             "auto met = MissingET[0];"
        #             "float dx = 0.0; float dy = 0.0; float dz = 0.0;"
        #             "for(size_t i=0; i<leps.size(); ++i) {"
        #             "  dx += (leps_scaledw[i].momentum.x - leps[i].momentum.x);"
        #             "  dy += (leps_scaledw[i].momentum.y - leps[i].momentum.y);"
        #             "  dz += (leps_scaledw[i].momentum.z - leps[i].momentum.z);"
        #             "}"
        #             "met.momentum.x -= dx; met.momentum.y -= dy; met.momentum.z -= dz;"
        #             "return ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{met};")

        # df = df.Define("zbuilder_result_scaledw",
        #             "HiggsTools::resonanceBuilder_mass_recoil(91.2, 125, 0.4, 240, false)"
        #             "(leps_scaledw, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0, Particle1)")
        # df = df.Define("zll_scaledw",      "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result_scaledw[0]}")
        # df = df.Define("zll_leps_scaledw", "ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{zbuilder_result_scaledw[1], zbuilder_result_scaledw[2]}")
        # df = df.Define("zll_m_scaledw",    "FCCAnalyses::ReconstructedParticle::get_mass(zll_scaledw)[0]")
        # df = df.Define("zll_p_scaledw",    "FCCAnalyses::ReconstructedParticle::get_p(zll_scaledw)[0]")
        # df = df.Define("zll_theta_scaledw","FCCAnalyses::ReconstructedParticle::get_theta(zll_scaledw)[0]")
        # df = df.Define("zll_recoil_scaledw",   "FCCAnalyses::ReconstructedParticle::recoilBuilder(240)(zll_scaledw)")
        # df = df.Define("zll_recoil_m_scaledw", "FCCAnalyses::ReconstructedParticle::get_mass(zll_recoil_scaledw)[0]")

        # df = df.Define("sorted_zll_leptons_scaledw",        "HiggsTools::sort_greater_p(zll_leps_scaledw)")
        # df = df.Define("sorted_zll_leptons_p_scaledw",      "FCCAnalyses::ReconstructedParticle::get_p(sorted_zll_leptons_scaledw)")
        # df = df.Define("sorted_zll_leptons_theta_scaledw",  "FCCAnalyses::ReconstructedParticle::get_theta(sorted_zll_leptons_scaledw)")
        # df = df.Define("leading_zll_lepton_p_scaledw",      "sorted_zll_leptons_p_scaledw.at(0)")
        # df = df.Define("leading_zll_lepton_theta_scaledw",  "sorted_zll_leptons_theta_scaledw.at(0)")
        # df = df.Define("subleading_zll_lepton_p_scaledw",   "sorted_zll_leptons_p_scaledw.at(1)")
        # df = df.Define("subleading_zll_lepton_theta_scaledw","sorted_zll_leptons_theta_scaledw.at(1)")

        # df = df.Define("zll_Leptons_acolinearity_scaledw", "HiggsTools::acolinearity(sorted_zll_leptons_scaledw)")
        # df = df.Define("zll_Leptons_acoplanarity_scaledw", "HiggsTools::acoplanarity(sorted_zll_leptons_scaledw)")
        # df = df.Define("zll_leptons_acolinearity_scaledw",
        #             "zll_Leptons_acolinearity_scaledw.size()>0 ? zll_Leptons_acolinearity_scaledw.at(0) : -999.f")
        # df = df.Define("zll_leptons_acoplanarity_scaledw",
        #             "zll_Leptons_acoplanarity_scaledw.size()>0 ? zll_Leptons_acoplanarity_scaledw.at(0) : -999.f")

        # df = df.Define("cosTheta_miss_scaledw", "HiggsTools::get_cosTheta(MissingET_scaledw)[0]")
        # df = df.Define("met_p_scaledw",     "FCCAnalyses::ReconstructedParticle::get_p(MissingET_scaledw)[0]")
        # df = df.Define("met_pt_scaledw",    "FCCAnalyses::ReconstructedParticle::get_pt(MissingET_scaledw)[0]")
        # df = df.Define("met_theta_scaledw", "FCCAnalyses::ReconstructedParticle::get_theta(MissingET_scaledw)[0]")
        # df = df.Define("met_phi_scaledw",   "FCCAnalyses::ReconstructedParticle::get_phi(MissingET_scaledw)[0]")
        # df = df.Define("met_px_scaledw",    "MissingET_scaledw[0].momentum.x")
        # df = df.Define("met_py_scaledw",    "MissingET_scaledw[0].momentum.y")
        # df = df.Define("met_pz_scaledw",    "MissingET_scaledw[0].momentum.z")

        # df = df.Define("total_p4_scaledw",
        #     "auto h = jets_p4[0] + jets_p4[1];"
        #     "TLorentzVector l1, l2, met;"
        #     "l1.SetXYZM(zll_leps_scaledw[0].momentum.x, zll_leps_scaledw[0].momentum.y, zll_leps_scaledw[0].momentum.z, zll_leps_scaledw[0].mass);"
        #     "l2.SetXYZM(zll_leps_scaledw[1].momentum.x, zll_leps_scaledw[1].momentum.y, zll_leps_scaledw[1].momentum.z, zll_leps_scaledw[1].mass);"
        #     "met.SetXYZM(MissingET_scaledw[0].momentum.x, MissingET_scaledw[0].momentum.y, MissingET_scaledw[0].momentum.z, 0);"
        #     "return h + l1 + l2 + met;")
        # df = df.Define("total_m_scaledw", "total_p4_scaledw.M()")
        # df = df.Define("total_e_scaledw", "total_p4_scaledw.E()")

        # df = df.Define("higgs_met_scaledw", 
        #     "auto h = jets_p4[0] + jets_p4[1];"
        #     "TLorentzVector met;"
        #     "met.SetXYZM(MissingET_scaledw[0].momentum.x, MissingET_scaledw[0].momentum.y, MissingET_scaledw[0].momentum.z, 0);"
        #     "return h + met;")
        # df = df.Define("higgs_met_m_scaledw", "higgs_met_scaledw.M()")
        # df = df.Define("higgs_met_e_scaledw", "higgs_met_scaledw.E()")

        # # ── Define MVA Scale Down ────────────────────────────────────────────────
        # existing_columns = df.GetColumnNames()
        # train_vars_scaledw = [
        #     f"{var}_scaledw" if f"{var}_scaledw" in existing_columns else var 
        #     for var in train_vars
        # ]
        # df = df.Define("MVAVec_scaledw", ROOT.computeModel1, train_vars_scaledw)
        # df = df.Define("BDTscore_scaledw", "MVAVec_scaledw.at(0)")

        # # sqrt uncertainty
        # df = df.Define("zll_recoil_sqrtsup", "FCCAnalyses::ReconstructedParticle::recoilBuilder(240.002)(zll)")
        # df = df.Define("zll_recoil_sqrtsdw", "FCCAnalyses::ReconstructedParticle::recoilBuilder(239.998)(zll)")
        # df = df.Define("zll_recoil_m_sqrtsup", "FCCAnalyses::ReconstructedParticle::get_mass(zll_recoil_sqrtsup)[0]")
        # df = df.Define("zll_recoil_m_sqrtsdw", "FCCAnalyses::ReconstructedParticle::get_mass(zll_recoil_sqrtsdw)[0]")
        
        return df

    #__________________________________________________________
    #Mandatory: output function, please make sure you return the branchlist as a python list

    def output():
        branchList = [
            #MET
            "met_p", "met_pt", "met_theta", "met_phi",
            "met_px", "met_py", "met_pz",
            "higgs_met_m", "higgs_met_e",
            #total E and mass
            "total_m", "total_e",
            # Z leptonic
            "zll_m", "zll_p", "zll_theta",
            "zll_recoil_m",
            # Z leptons
            "leading_zll_lepton_p",    "leading_zll_lepton_theta",
            "subleading_zll_lepton_p", "subleading_zll_lepton_theta",
            "zll_leptons_acolinearity", "zll_leptons_acoplanarity",
            # Higgs candidate (dijet)
            "higgs_m",
            # Jets
            "jet1_p", "jet1_theta", "jet1_phi", "jet1_mass",
            "jet2_p", "jet2_theta", "jet2_phi", "jet2_mass",
            "event_d12", "event_d23", "event_d34", "event_d45",
            "jet1_E", "jet2_E",
            "jet1_nconst", "jet2_nconst",
            # "jet1_charge", "jet2_charge",
            
            # Flavor tags
            "jet1_btag", "jet2_btag",
            "jet1_stag", "jet2_stag",
            "jet1_ctag", "jet2_ctag",
            "jet1_utag", "jet2_utag",
            "jet1_dtag", "jet2_dtag",
            "jet1_Gtag", "jet2_Gtag",
            "jet1_tautag", "jet2_tautag",
            "btag_max",  "stag_other",
            # Event level
            "cosTheta_miss",
            # Gen tag (used to define signal in training, not a BDT input)
            "is_Hbs",
            # Gen-quark kinematics (for tagger truth-matching on BSM Hbs samples;
            # filled with sentinel -999 / pdg=0 when no e+e- daughter b/s pair)
            "gen_b_p", "gen_b_theta", "gen_b_phi", "gen_b_pdg",
            "gen_s_p", "gen_s_theta", "gen_s_phi", "gen_s_pdg",

            #Non-normalized probability score
            "BDTscore_class0", 
            "BDTscore_class1", 
            "BDTscore_class2", 
            "BDTscore_class3",
            "BDTscore_class4", 
            "BDTscore_class5", 
            "BDTscore_class6", 
            "BDTscore_class7",

            #normalized probability score
            "norm_prob0", 
            "norm_prob1", 
            "norm_prob2", 
            "norm_prob3", 
            "norm_prob4", 
            "norm_prob5",
        ]

        branchList += jetFlavourHelper.outputBranches()
        return branchList