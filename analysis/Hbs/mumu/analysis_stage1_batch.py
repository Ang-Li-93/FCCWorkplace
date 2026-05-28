# H->bs at sqrt(s)=240 GeV: e+e- -> ZH -> mumu + (bs~+b~s)
# Stage 1: flat ntuple production
# Modelled on ZH_XSec/FinalReport/S240/mumu and FCCAnalyses/examples/FCCee/higgs/mH-recoil/stage1_flavor.py

import os, copy, urllib.request

processList = {
    #'wzp6_ee_mumuH_ecm240':           {'chunks': 10},
    'wzp6_ee_mumuH_Hbs_ecm240':       {'chunks': 10},
    'p8_ee_WW_mumu_ecm240':           {'chunks': 10},
    'wzp6_egamma_eZ_Zmumu_ecm240':    {'chunks': 10},
    'wzp6_gammae_eZ_Zmumu_ecm240':    {'chunks': 10},
    'wzp6_ee_mumu_ecm240':            {'chunks': 10},
    'p8_ee_ZZ_ecm240':                {'chunks': 10},
    'wzp6_gaga_mumu_60_ecm240':       {'chunks': 10},
}

prodTag     = "FCCee/winter2023/IDEA/"
outputDirEos = "/eos/user/l/lia/FCCee/Hbs/mumu/firstlook/"
eosType     = "eosuser"
nCPUS       = 4
batchQueue  = "longlunch"
compGroup   = "group_u_FCC.local_gen"

## ParticleNet flavor tagger model (winter2023), trained on 9M jets
model_name    = "fccee_flavtagging_edm4hep_wc_v1"
url_model_dir = "https://fccsw.web.cern.ch/fccsw/testsamples/jet_flavour_tagging/winter2023/wc_pt_13_01_2022/"
model_dir     = "/eos/experiment/fcc/ee/jet_flavour_tagging/winter2023/wc_pt_13_01_2022/"

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
        df = df.Filter("zll_m > 86 && zll_m < 96")
        df = df.Filter("zll_p > 20 && zll_p < 70")
        df = df.Filter("zll_recoil_m > 120 && zll_recoil_m < 140")

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

        return df

    def output():
        branchList = [
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
            # Flavor tags
            "jet1_btag", "jet2_btag",
            "jet1_stag", "jet2_stag",
            "btag_max",  "stag_other",
            # Event level
            "cosTheta_miss",
            # Gen tag (used to define signal in training, not a BDT input)
            "is_Hbs",
            # Gen-quark kinematics (for tagger truth-matching on BSM Hbs samples;
            # filled with sentinel -999 / pdg=0 when no e+e- daughter b/s pair)
            "gen_b_p", "gen_b_theta", "gen_b_phi", "gen_b_pdg",
            "gen_s_p", "gen_s_theta", "gen_s_phi", "gen_s_pdg",
        ]
        branchList += jetFlavourHelper.outputBranches()
        return branchList
