'''
FCCAnalyses histmaker: H->bb m(bb) cross-check, Whizard ME decay vs Pythia6
resonance decay (ee->mumuH, 240 GeV, winter2023 IDEA fast-sim).

All five stages are produced in ONE RDataFrame pass per sample, from the edm4hep
files (truth + reco together):
  m_parton  parton m(b,bbar)               (gen)
  m_vis     particle-level visible (no nu)  (gen, MET-blind)
  m_full    particle-level full (+nu)       (gen, MET-corrected)
  m_bdesc   stable descendants of hard b/bbar (gen, the CAUSE)
  m_dijet   Durham exclusive n=2 dijet mass (detector)
  m_recoil  mu+mu- recoil mass              (detector, cross-check)

Run:  fccanalysis run histmaker.py
'''
import os
from addons.FastJet.jetClusteringHelper import ExclusiveJetClusteringHelper

_HERE = os.path.dirname(os.path.abspath(__file__))

# Two samples staged as local subdirs (see samples/). Both winter2023 IDEA, but
# reconstructed with different stacks -> different podio relation naming, handled
# per-sample below.
inputDir  = os.path.join(_HERE, "samples")
outputDir = os.path.join(_HERE, "output")

processList = {
    'wzp6_ee_mumuH_Hbb_ecm240':         {'fraction': 1},   # Pythia6 resonance decay (central)
    'wzp6_ee_mumuH_Hbb_MEdecay_ecm240': {'fraction': 1},   # Whizard ME decay (local)
}

nCPUS   = -1
doScale = False                       # shape comparison only -> no xsec/lumi scaling
includePaths = ["functions.h"]

# procDict is mandatory in this FCCAnalyses version even with doScale=False, and
# must be a file path (inline dict is not accepted). Dummy metadata (scaling off).
procDict = os.path.join(_HERE, "procDict.json")

# binning aligned so that 125 GeV sits at a bin CENTRE (an edge at 125 -/+ w/2),
# never on a bin edge.
bins_parton = (41, 123.975, 126.025)  # 0.05 GeV bins, edges at 124.975 / 125.025
bins_wide   = (50,  94.5,   144.5)    # 1.0  GeV bins, edges at 124.5   / 125.5
bins_desc   = (50, 114.75,  139.75)   # 0.5  GeV bins, edges at 124.75  / 125.25
bins_mll    = (60,  66.0,    96.0)    # 0.5  GeV bins, dimuon (Z) mass region


def build_graph(df, dataset):
    results = []
    df = df.Define("weight", "1.0")
    weightsum = df.Sum("weight")

    # ---- schema aliases: auto-detect podio relation naming ------------------
    # old (podio 0.16, central winter2023): Muon#0 / Particle#1
    # new (podio 0.99, defaultstack reco):  Muon_objIdx / _Particle_daughters
    cols = set(str(c) for c in df.GetColumnNames())
    if "Muon_objIdx" in cols or "Muon_objIdx.index" in cols:
        df = df.Alias("Muon0", "Muon_objIdx.index")
        df = df.Alias("MCdau", "_Particle_daughters.index")
    else:
        df = df.Alias("Muon0", "Muon#0.index")
        df = df.Alias("MCdau", "Particle#1.index")

    # ---- gen-level (truth) masses -------------------------------------------
    df = df.Define("m_parton", "JetCheck::hard_bb_mass(Particle)")
    df = df.Define("m_vis",    "JetCheck::gen_system_mass(Particle, false)")
    df = df.Define("m_full",   "JetCheck::gen_system_mass(Particle, true)")
    df = df.Define("m_bdesc",  "JetCheck::bdesc_mass(Particle, MCdau)")

    # ---- muon-pair (Z) at gen level: parton (hard) vs particle (post-FSR) ----
    df = df.Define("mll_parton",    "JetCheck::dimuon_mass(Particle, true)")
    df = df.Define("mll_gen",       "JetCheck::dimuon_mass(Particle, false)")
    df = df.Define("recoil_parton", "JetCheck::dimuon_recoil(Particle, true,  240.0)")
    df = df.Define("recoil_gen",    "JetCheck::dimuon_recoil(Particle, false, 240.0)")

    # ---- detector-level: muons + MET ----------------------------------------
    df = df.Define("muons_all", "FCCAnalyses::ReconstructedParticle::get(Muon0, ReconstructedParticles)")
    df = df.Define("muons",     "FCCAnalyses::ReconstructedParticle::sel_p(20)(muons_all)")
    df = df.Filter("FCCAnalyses::ReconstructedParticle::get_n(muons) >= 2", "n_mu>=2")

    # Missing 4-momentum from the visible ReconstructedParticles: the Delphes
    # MissingET collection can't be used here (absent in the ME-level reco, and
    # has an RDF-unreadable covMatrix leaf in the stock reco), so build it as
    # p_miss = (sqrts - E_vis, -p_vis). Works for both samples.
    df = df.Define("RP_px", "FCCAnalyses::ReconstructedParticle::get_px(ReconstructedParticles)")
    df = df.Define("RP_py", "FCCAnalyses::ReconstructedParticle::get_py(ReconstructedParticles)")
    df = df.Define("RP_pz", "FCCAnalyses::ReconstructedParticle::get_pz(ReconstructedParticles)")
    df = df.Define("RP_e",  "FCCAnalyses::ReconstructedParticle::get_e(ReconstructedParticles)")

    # ---- Durham exclusive n=2 dijet via the standard helper -----------------
    df = df.Define("RecoNoMuons", "FCCAnalyses::ReconstructedParticle::remove(ReconstructedParticles, muons)")
    jch = ExclusiveJetClusteringHelper("RecoNoMuons", 2)
    df = jch.define(df)
    df = df.Define("jets_p4", f"JetConstituentsUtils::compute_tlv_jets({jch.jets})")
    df = df.Filter("jets_p4.size() >= 2", "n_jet>=2")
    df = df.Define("m_dijet",     "JetConstituentsUtils::InvariantMass(jets_p4[0], jets_p4[1])")
    df = df.Define("m_dijet_met", "JetCheck::dijet_met_mass(jets_p4, RP_px, RP_py, RP_pz, RP_e, 240.0)")

    # ---- detector-level: dimuon recoil mass (cross-check) -------------------
    df = df.Define("zmumu",   "FCCAnalyses::ReconstructedParticle::resonanceBuilder(91)(muons)")
    df = df.Define("mll_reco","FCCAnalyses::ReconstructedParticle::get_mass(zmumu)[0]")
    df = df.Define("recoil",  "FCCAnalyses::ReconstructedParticle::recoilBuilder(240)(zmumu)")
    df = df.Define("m_recoil","FCCAnalyses::ReconstructedParticle::get_mass(recoil)[0]")

    # ---- histograms ----------------------------------------------------------
    results.append(df.Histo1D(("m_parton", "parton m(b,bbar)",        *bins_parton), "m_parton", "weight"))
    results.append(df.Histo1D(("m_vis",    "particle visible (no nu)",*bins_wide),   "m_vis",    "weight"))
    results.append(df.Histo1D(("m_full",   "particle full (+nu)",     *bins_wide),   "m_full",   "weight"))
    results.append(df.Histo1D(("m_bdesc",  "b/bbar descendants",      *bins_desc),   "m_bdesc",  "weight"))
    results.append(df.Histo1D(("m_dijet",  "Durham n=2 dijet",        *bins_wide),   "m_dijet",  "weight"))
    results.append(df.Histo1D(("m_dijet_met","Durham n=2 dijet + MET", *bins_wide),  "m_dijet_met","weight"))
    results.append(df.Histo1D(("m_recoil", "mumu recoil",             *bins_wide),   "m_recoil", "weight"))
    # muon-pair at three levels
    results.append(df.Histo1D(("mll_parton",    "m(mumu) parton",     *bins_mll),  "mll_parton",    "weight"))
    results.append(df.Histo1D(("mll_gen",       "m(mumu) particle",   *bins_mll),  "mll_gen",       "weight"))
    results.append(df.Histo1D(("mll_reco",      "m(mumu) detector",   *bins_mll),  "mll_reco",      "weight"))
    results.append(df.Histo1D(("recoil_parton", "recoil parton",      *bins_wide), "recoil_parton", "weight"))
    results.append(df.Histo1D(("recoil_gen",    "recoil particle",    *bins_wide), "recoil_gen",    "weight"))
    return results, weightsum
