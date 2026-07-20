"""
Shared stage1 graph for the ZH hadronic (Z->qq) channel, S240 and S365.

Adapted from jeyserma/FCCPhysics h_zh_hadronic.py to the Paper workflow:
  - old-style winter2023 `fccanalysis run` RDFanalysis scripts (like the leptonic channels),
  - all custom C++ compiled into HiggsTools (FCCAnalyses-winter2023), no JIT headers,
  - THETA-based cone isolation (HiggsTools::coneIsolationTheta) for the lepton veto,
    consistent with the leptonic channels (the original used a deltaR-based cone),
  - leptonic-style systematics branches in the analysis ntuples:
      * jet momentum scale +-1e-5 (zqq_m/p/recoil_m_scaleup/scaledw); NB the down
        variation correctly uses -1e-5 (the leptonic scripts use +1e-5 for both),
      * sqrt(s) +-2 MeV (zqq_recoil_m_sqrtsup/sqrtsdw).
    No BES / mH-shifted samples exist in winter2023 for hadronic Z decays, so
    sample-based systematics are not available in this channel.

Process-dependent MC-truth filters (HZZ->invisible removal, WW->leptonic removal)
follow the process name from the FCCANA_PROCESS environment variable, exported by
condor/submit_stage1.py in each job wrapper.
"""


def lepton_veto(df, flavor, ecm):
    """Orthogonality veto w.r.t. the leptonic (ee/mumu) channels."""
    coll = "muons_all" if flavor == "muon" else "electrons_all"
    df = df.Define(f"leps_{flavor}", f"FCCAnalyses::ReconstructedParticle::sel_p(20)({coll})")
    df = df.Define(f"leps_{flavor}_q", f"FCCAnalyses::ReconstructedParticle::get_charge(leps_{flavor})")
    df = df.Define(f"leps_{flavor}_no", f"FCCAnalyses::ReconstructedParticle::get_n(leps_{flavor})")
    # theta-based isolation, as in the leptonic channels
    df = df.Define(f"leps_{flavor}_iso", f"HiggsTools::coneIsolationTheta(0.01, 0.5)(leps_{flavor}, ReconstructedParticles)")
    df = df.Define(f"leps_{flavor}_sel_iso", f"HiggsTools::sel_isol(0.25)(leps_{flavor}, leps_{flavor}_iso)")

    # The resonance builder must be guarded: it exit(1)s on < 2 leptons (most hadronic
    # events!) and returns an empty RVec when no opposite-charge pair exists. Events
    # failing the guard get 3 default particles (mass 0 -> the veto mll/recoil windows
    # below fail -> the event is correctly kept in the hadronic channel).
    guard = f"(leps_{flavor}_no >= 2 && abs(Sum(leps_{flavor}_q)) < (int)leps_{flavor}_q.size())"
    df = df.Define(f"zbuilder_result_{flavor}", f"{guard} ? HiggsTools::resonanceBuilder_mass_recoil(91.2, 125, 0.4, {ecm}, false)(leps_{flavor}, MCRecoAssociations0, MCRecoAssociations1, ReconstructedParticles, Particle, Particle0, Particle1) : ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>(3)")
    df = df.Define(f"zll_{flavor}", f"ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{{zbuilder_result_{flavor}[0]}}")
    df = df.Define(f"zll_m_{flavor}", f"FCCAnalyses::ReconstructedParticle::get_mass(zll_{flavor})[0]")
    df = df.Define(f"zll_p_{flavor}", f"FCCAnalyses::ReconstructedParticle::get_p(zll_{flavor})[0]")
    df = df.Define(f"zll_recoil_{flavor}", f"FCCAnalyses::ReconstructedParticle::recoilBuilder({ecm})(zll_{flavor})")
    df = df.Define(f"zll_recoil_m_{flavor}", f"FCCAnalyses::ReconstructedParticle::get_mass(zll_recoil_{flavor})[0]")

    sel_leps = f"leps_{flavor}_no >= 2 && leps_{flavor}_sel_iso.size() > 0 && abs(Sum(leps_{flavor}_q)) < leps_{flavor}_q.size()"
    sel_mll = f"zll_m_{flavor} > 86 && zll_m_{flavor} < 96"
    # p_ll window must cover the leptonic-channel acceptance at each energy: at 240 the
    # leptonic baseline is 20 < p_ll < 70; at 365 it is p_ll > 20 with no upper bound
    # (ZH kinematics give p_ll ~ 146 GeV there, far above the 240-era window).
    if ecm == 240:
        sel_pll = f"zll_p_{flavor} > 20 && zll_p_{flavor} < 70"
    else:
        sel_pll = f"zll_p_{flavor} > 20"
    sel_recoil = f"zll_recoil_m_{flavor} < 150 && zll_recoil_m_{flavor} > 100"
    df = df.Filter(f"!({sel_leps} && {sel_mll} && {sel_pll} && {sel_recoil})")
    return df


def exclusive_clustering(df, njets):
    if njets == 0:  # inclusive
        df = df.Define("clustered_jets_N0", "JetClustering::clustering_kt(0.6, 0, 5, 1, 0)(pseudo_jets)")
    else:
        df = df.Define(f"clustered_jets_N{njets}", f"JetClustering::clustering_ee_kt(2, {njets}, 0, 10)(pseudo_jets)")
    df = df.Define(f"jets_N{njets}", f"FCCAnalyses::JetClusteringUtils::get_pseudoJets(clustered_jets_N{njets})")
    df = df.Define(f"njets_N{njets}", f"jets_N{njets}.size()")
    df = df.Define(f"jetconstituents_N{njets}", f"FCCAnalyses::JetClusteringUtils::get_constituents(clustered_jets_N{njets})")
    df = df.Define(f"jets_e_N{njets}", f"FCCAnalyses::JetClusteringUtils::get_e(jets_N{njets})")
    df = df.Define(f"jets_px_N{njets}", f"FCCAnalyses::JetClusteringUtils::get_px(jets_N{njets})")
    df = df.Define(f"jets_py_N{njets}", f"FCCAnalyses::JetClusteringUtils::get_py(jets_N{njets})")
    df = df.Define(f"jets_pz_N{njets}", f"FCCAnalyses::JetClusteringUtils::get_pz(jets_N{njets})")
    df = df.Define(f"jets_m_N{njets}", f"FCCAnalyses::JetClusteringUtils::get_m(jets_N{njets})")
    df = df.Define(f"jets_rp_N{njets}", f"HiggsTools::jets2rp(jets_px_N{njets}, jets_py_N{njets}, jets_pz_N{njets}, jets_e_N{njets}, jets_m_N{njets})")
    df = df.Define(f"jets_rp_cand_N{njets}", f"HiggsTools::select_jets(jets_rp_N{njets}, jetconstituents_N{njets}, {njets}, ReconstructedParticles)")
    df = df.Define(f"njets_cand_N{njets}", f"jets_rp_cand_N{njets}.size()")
    return df


def define_zqq(df, njets, ecm):
    df = df.Define(f"zbuilder_result_N{njets}", f"HiggsTools::resonanceBuilder_mass_recoil_hadronic(91.2, 125, 0.0, {ecm})(jets_rp_cand_N{njets})")
    df = df.Define(f"zqq_N{njets}", f"ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{{zbuilder_result_N{njets}[0]}}")
    df = df.Define(f"zqq_jets_N{njets}", f"ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{{zbuilder_result_N{njets}[1], zbuilder_result_N{njets}[2]}}")
    df = df.Define(f"zqq_m_N{njets}", f"FCCAnalyses::ReconstructedParticle::get_mass(zqq_N{njets})[0]")
    df = df.Define(f"zqq_p_N{njets}", f"FCCAnalyses::ReconstructedParticle::get_p(zqq_N{njets})[0]")
    df = df.Define(f"zqq_recoil_N{njets}", f"FCCAnalyses::ReconstructedParticle::recoilBuilder({ecm})(zqq_N{njets})")
    df = df.Define(f"zqq_recoil_m_N{njets}", f"FCCAnalyses::ReconstructedParticle::get_mass(zqq_recoil_N{njets})[0]")
    return df


def build_graph_zqq(df, ecm, proc="", tmva_helper=None, syst=False):
    """Full Z(qq)H selection. Returns the final dataframe (no histograms: ntuple stage)."""

    df = df.Alias("Particle0", "Particle#0.index")
    df = df.Alias("Particle1", "Particle#1.index")
    df = df.Alias("MCRecoAssociations0", "MCRecoAssociations#0.index")
    df = df.Alias("MCRecoAssociations1", "MCRecoAssociations#1.index")
    df = df.Alias("Muon0", "Muon#0.index")
    df = df.Alias("Electron0", "Electron#0.index")
    df = df.Alias("Photon0", "Photon#0.index")

    # process-dependent MC-truth filters (proc from FCCANA_PROCESS, set by the condor wrapper)
    if "HZZ" in proc:  # remove H(ZZ) invisible decays from HZZ (covered by the Hinv samples)
        df = df.Define("hzz_invisible", "HiggsTools::is_hzz_invisible(Particle, Particle1)")
        df = df.Filter("!hzz_invisible")
    if proc.startswith(f"p8_ee_WW_ecm"):  # remove same-flavor leptonic WW (covered by WW_mumu / WW_ee)
        df = df.Define("ww_leptonic", "HiggsTools::is_ww_leptonic(Particle, Particle1)")
        df = df.Filter("!ww_leptonic")

    df = df.Define("muons_all", "FCCAnalyses::ReconstructedParticle::get(Muon0, ReconstructedParticles)")
    df = df.Define("electrons_all", "FCCAnalyses::ReconstructedParticle::get(Electron0, ReconstructedParticles)")
    df = df.Define("photons_all", "FCCAnalyses::ReconstructedParticle::get(Photon0, ReconstructedParticles)")

    # orthogonality w.r.t. the leptonic channels
    df = lepton_veto(df, "muon", ecm)
    df = lepton_veto(df, "electron", ecm)

    # remove energetic isolated photons/muons/electrons from the clustering inputs
    lo, hi = (40, 95) if ecm == 240 else (20, 170)
    df = df.Define("photons_all_p", "FCCAnalyses::ReconstructedParticle::get_p(photons_all)")
    df = df.Define("photons", f"HiggsTools::sel_range({lo}, {hi}, false)(photons_all, photons_all_p)")
    df = df.Define("muons_all_p", "FCCAnalyses::ReconstructedParticle::get_p(muons_all)")
    df = df.Define("muons", f"HiggsTools::sel_range({lo}, {hi}, false)(muons_all, muons_all_p)")
    df = df.Define("electrons_all_p", "FCCAnalyses::ReconstructedParticle::get_p(electrons_all)")
    df = df.Define("electrons", f"HiggsTools::sel_range({lo}, {hi}, false)(electrons_all, electrons_all_p)")

    df = df.Define("rps_no_photons", "FCCAnalyses::ReconstructedParticle::remove(ReconstructedParticles, photons)")
    df = df.Define("rps_no_photons_muons", "FCCAnalyses::ReconstructedParticle::remove(rps_no_photons, muons)")
    df = df.Define("rps_sel", "FCCAnalyses::ReconstructedParticle::remove(rps_no_photons_muons, electrons)")

    df = df.Define("RP_px", "FCCAnalyses::ReconstructedParticle::get_px(rps_sel)")
    df = df.Define("RP_py", "FCCAnalyses::ReconstructedParticle::get_py(rps_sel)")
    df = df.Define("RP_pz", "FCCAnalyses::ReconstructedParticle::get_pz(rps_sel)")
    df = df.Define("RP_e", "FCCAnalyses::ReconstructedParticle::get_e(rps_sel)")
    df = df.Define("pseudo_jets", "FCCAnalyses::JetClusteringUtils::set_pseudoJets(RP_px, RP_py, RP_pz, RP_e)")

    # clustering hypotheses: inclusive kt + exclusive ee_kt N=2, 4, 6
    for n in (6, 4, 2, 0):
        df = exclusive_clustering(df, n)
        df = define_zqq(df, n, ecm)

    df = df.Define("zqq_all", "std::vector<ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>> r = {zqq_N0, zqq_N2, zqq_N4, zqq_N6}; return r;")
    df = df.Define("zqq_jets_all", "std::vector<ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>> r = {zqq_jets_N0, zqq_jets_N2, zqq_jets_N4, zqq_jets_N6}; return r;")
    df = df.Define("zqq_m_all", "ROOT::VecOps::RVec<float> r = {zqq_m_N0, zqq_m_N2, zqq_m_N4, zqq_m_N6}; return r;")
    df = df.Define("zqq_p_all", "ROOT::VecOps::RVec<float> r = {zqq_p_N0, zqq_p_N2, zqq_p_N4, zqq_p_N6}; return r;")
    df = df.Define("zqq_recoil_m_all", "ROOT::VecOps::RVec<float> r = {zqq_recoil_m_N0, zqq_recoil_m_N2, zqq_recoil_m_N4, zqq_recoil_m_N6}; return r;")
    df = df.Define("njets_all", "ROOT::VecOps::RVec<int> r = {(int)njets_cand_N0, (int)njets_cand_N2, (int)njets_cand_N4, (int)njets_cand_N6}; return r;")
    df = df.Define("njets_target", "ROOT::VecOps::RVec<int> r = {0, 2, 4, 6}; return r;")
    df = df.Define("best_clustering_idx", f"HiggsTools::best_clustering_idx(zqq_m_all, zqq_p_all, zqq_recoil_m_all, njets_all, njets_target, {ecm})")

    df = df.Filter("best_clustering_idx >= 0")

    df = df.Define("zqq_best", "zqq_all[best_clustering_idx]")
    df = df.Define("zqq_jets_best", "zqq_jets_all[best_clustering_idx]")
    df = df.Define("zqq_m_best", "zqq_m_all[best_clustering_idx]")
    df = df.Define("zqq_p_best", "zqq_p_all[best_clustering_idx]")
    df = df.Define("zqq_recoil_m_best", "zqq_recoil_m_all[best_clustering_idx]")
    df = df.Define("zqq_jets_p_best", "FCCAnalyses::ReconstructedParticle::get_p(zqq_jets_best)")
    df = df.Define("zqq_jets_theta_best", "FCCAnalyses::ReconstructedParticle::get_theta(zqq_jets_best)")
    df = df.Define("zqq_jets_costheta_best", "ROOT::VecOps::RVec<float> ret; for(auto & theta: zqq_jets_theta_best) ret.push_back(std::abs(cos(theta))); return ret;")

    df = df.Define("z_theta", "FCCAnalyses::ReconstructedParticle::get_theta(zqq_best)")
    df = df.Define("z_costheta", "std::abs(cos(z_theta[0]))")

    # jet kinematics
    df = df.Define("leading_idx", "(zqq_jets_p_best[0] > zqq_jets_p_best[1]) ? 0 : 1")
    df = df.Define("subleading_idx", "(zqq_jets_p_best[0] > zqq_jets_p_best[1]) ? 1 : 0")
    df = df.Define("leading_jet_p", "zqq_jets_p_best[leading_idx]")
    df = df.Define("subleading_jet_p", "zqq_jets_p_best[subleading_idx]")
    df = df.Define("leading_jet_costheta", "zqq_jets_costheta_best[leading_idx]")
    df = df.Define("subleading_jet_costheta", "zqq_jets_costheta_best[subleading_idx]")

    # WW reconstruction from the 4-jet hypothesis
    df = df.Define("pairs_WW_N4", "HiggsTools::pair_WW_N4(jets_rp_cand_N4)")
    df = df.Define("W1", "pairs_WW_N4[0]")
    df = df.Define("W2", "pairs_WW_N4[1]")
    df = df.Define("W1_m", "W1.M()")
    df = df.Define("W2_m", "W2.M()")
    df = df.Define("W1_p", "W1.P()")
    df = df.Define("W2_p", "W2.P()")
    # NB the upstream reference defined both W*_costheta as abs(W1.Theta()) (theta of W1,
    # twice); kept only for compatibility with the pre-trained MIT model. We retrain the
    # BDT locally (train_xgb.py), so the proper definitions are used.
    df = df.Define("W1_costheta", "std::abs(std::cos(W1.Theta()))")
    df = df.Define("W2_costheta", "std::abs(std::cos(W2.Theta()))")
    # W-pair rejection reference mass 80.4 GeV (arXiv:2512.21290; an earlier port used 78)
    df = df.Define("delta_mWW", "std::sqrt((W1_m-80.4)*(W1_m-80.4) + (W2_m-80.4)*(W2_m-80.4))")

    ##############################################################
    # selection
    ##############################################################
    if ecm == 240:
        df = df.Filter("zqq_m_best > 20 && zqq_m_best < 140")
        df = df.Filter("zqq_p_best < 90 && zqq_p_best > 20")
    else:
        # 365 windows per arXiv:2512.21290: 60 < m_jj < 200, 20 < p_jj < 160
        df = df.Filter("zqq_m_best > 60 && zqq_m_best < 200")
        df = df.Filter("zqq_p_best < 160 && zqq_p_best > 20")

    df = df.Filter("z_costheta < 0.85")

    df = df.Define("acolinearity", "HiggsTools::acolinearity_scalar(zqq_jets_best)")
    df = df.Filter("acolinearity > 0.35")
    df = df.Define("acoplanarity", "HiggsTools::acoplanarity_scalar(zqq_jets_best)")

    df = df.Filter("delta_mWW > 6")

    df = df.Define("missingEnergy_rp", f"HiggsTools::missingEnergy({ecm}, ReconstructedParticles)")
    df = df.Define("missingEnergy", "missingEnergy_rp[0].energy")
    df = df.Define("cosThetaMiss", "HiggsTools::get_cosTheta_miss(missingEnergy_rp)")
    df = df.Filter("cosThetaMiss < 0.995")

    df = df.Define("thrust", "FCCAnalyses::Algorithms::calculate_thrust()(RP_px, RP_py, RP_pz)")
    df = df.Define("thrust_magn", "thrust[0]")
    df = df.Define("thrust_costheta", "abs(thrust[3])")
    if ecm == 365:
        df = df.Filter("thrust_magn < 0.85")

    # BDT inference (analysis stage only; the treemaker runs pre-training, without a model)
    if tmva_helper is not None:
        df = tmva_helper.run_inference(df, col_name="mva_score")

    # systematics branches (analysis stage only), mirroring the leptonic stage1 files
    if syst:
        # jet momentum scale +-1e-5 (note: down variation correctly uses -1e-5)
        for tag, scale in (("scaleup", "1e-5"), ("scaledw", "-1e-5")):
            df = df.Define(f"zqq_jets_{tag}", f"HiggsTools::lepton_momentum_scale({scale})(zqq_jets_best)")
            df = df.Define(f"zbuilder_{tag}", f"HiggsTools::resonanceBuilder_mass_recoil_hadronic(91.2, 125, 0.0, {ecm})(zqq_jets_{tag})")
            df = df.Define(f"zqq_{tag}", f"ROOT::VecOps::RVec<edm4hep::ReconstructedParticleData>{{zbuilder_{tag}[0]}}")
            df = df.Define(f"zqq_m_{tag}", f"FCCAnalyses::ReconstructedParticle::get_mass(zqq_{tag})[0]")
            df = df.Define(f"zqq_p_{tag}", f"FCCAnalyses::ReconstructedParticle::get_p(zqq_{tag})[0]")
            df = df.Define(f"zqq_recoil_{tag}", f"FCCAnalyses::ReconstructedParticle::recoilBuilder({ecm})(zqq_{tag})")
            df = df.Define(f"zqq_recoil_m_{tag}", f"FCCAnalyses::ReconstructedParticle::get_mass(zqq_recoil_{tag})[0]")
        # sqrt(s) +- 2 MeV
        df = df.Define("zqq_recoil_sqrtsup", f"FCCAnalyses::ReconstructedParticle::recoilBuilder({ecm + 0.002})(zqq_best)")
        df = df.Define("zqq_recoil_sqrtsdw", f"FCCAnalyses::ReconstructedParticle::recoilBuilder({ecm - 0.002})(zqq_best)")
        df = df.Define("zqq_recoil_m_sqrtsup", "FCCAnalyses::ReconstructedParticle::get_mass(zqq_recoil_sqrtsup)[0]")
        df = df.Define("zqq_recoil_m_sqrtsdw", "FCCAnalyses::ReconstructedParticle::get_mass(zqq_recoil_sqrtsdw)[0]")

    return df


# BDT training variables (final list of the reference training, zh_hadronic_training/train.py)
TRAIN_VARS = [
    "zqq_p_best", "leading_jet_costheta", "subleading_jet_costheta",
    "leading_jet_p", "subleading_jet_p", "acolinearity", "acoplanarity",
    "W1_p", "W2_p", "W1_m", "W2_m", "z_costheta", "thrust_magn",
    "W1_costheta", "W2_costheta",
]

# ntuple output branches: fit observables + BDT inputs (+ a few extras)
TREE_BRANCHES = [
    "zqq_recoil_m_best", "zqq_p_best", "zqq_m_best",
    "leading_jet_costheta", "subleading_jet_costheta", "leading_jet_p", "subleading_jet_p",
    "acolinearity", "acoplanarity",
    "W1_p", "W2_p", "W1_m", "W2_m",
    "z_costheta", "thrust_magn", "W1_costheta", "W2_costheta",
]

ANALYSIS_EXTRA_BRANCHES = [
    "mva_score", "cosThetaMiss", "missingEnergy", "best_clustering_idx",
]

SYST_BRANCHES = [
    "zqq_m_scaleup", "zqq_p_scaleup", "zqq_recoil_m_scaleup",
    "zqq_m_scaledw", "zqq_p_scaledw", "zqq_recoil_m_scaledw",
    "zqq_recoil_m_sqrtsup", "zqq_recoil_m_sqrtsdw",
]
