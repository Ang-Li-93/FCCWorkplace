import os

repo = "/eos/user/l/lia/FCCee/Hbs/mumu"

class loc: pass
loc.ROOT        = repo + '/'
loc.OUT         = loc.ROOT + 'output_trained/'
loc.DATA        = loc.ROOT + 'data'
loc.CSV         = loc.DATA + '/csv'
loc.PKL         = loc.DATA + '/pkl'
loc.PKL_Val     = loc.DATA + '/pkl_val'
loc.ROOTFILES   = loc.DATA + '/ROOT'
loc.PLOTS       = loc.DATA + '/plots'
loc.PLOTS_Val   = loc.OUT  + 'plots_val'
loc.TEX         = loc.OUT  + 'tex'
loc.JSON        = loc.OUT  + 'json'

loc.EOS      = repo
loc.BDT      = loc.EOS + '/BDT'
loc.PROD     = loc.EOS
loc.STAGE1   = loc.PROD + '/firstlook'
loc.TRAIN    = loc.PROD + '/MVAInputs'
loc.TRAIN2   = loc.PROD + '/Training_4stage2/'
loc.ANALYSIS = loc.PROD + '/BDT_analysis_samples/'

# BDT input variables
train_vars = [
    # Z leptonic system
    "zll_m",
    "zll_p",
    "zll_theta",
    "zll_recoil_m",           # primary discriminant: recoil mass peaks at mH for ZH
    # Z leptons
    "leading_zll_lepton_p",
    "leading_zll_lepton_theta",
    "subleading_zll_lepton_p",
    "subleading_zll_lepton_theta",
    "zll_leptons_acolinearity",
    "zll_leptons_acoplanarity",
    # Higgs candidate
    "higgs_m",                # dijet invariant mass, peaks at mH for H->bs
    # Jets
    "jet1_p", "jet1_theta", "jet1_mass",
    "jet2_p", "jet2_theta", "jet2_mass",
    # Flavor tagging — essential for H->bs vs H->bb/cc/gg separation
    "btag_max",               # b-tag of the more b-like jet
    "stag_other",             # s-tag of the remaining jet
]

latex_mapping = {
    "zll_m":                        r"$m_{\ell\ell}$",
    "zll_p":                        r"$p_{\ell\ell}$",
    "zll_theta":                    r"$\theta_{\ell\ell}$",
    "zll_recoil_m":                 r"$m_{\mathrm{recoil}}$",
    "leading_zll_lepton_p":         r"$p_{\ell_1}$",
    "leading_zll_lepton_theta":     r"$\theta_{\ell_1}$",
    "subleading_zll_lepton_p":      r"$p_{\ell_2}$",
    "subleading_zll_lepton_theta":  r"$\theta_{\ell_2}$",
    "zll_leptons_acolinearity":     r"$|\Delta\theta_{\ell\ell}|$",
    "zll_leptons_acoplanarity":     r"$|\Delta\phi_{\ell\ell}|$",
    "higgs_m":                      r"$m_{jj}$",
    "jet1_p":                       r"$p_{j_1}$",
    "jet1_theta":                   r"$\theta_{j_1}$",
    "jet1_mass":                    r"$m_{j_1}$",
    "jet2_p":                       r"$p_{j_2}$",
    "jet2_theta":                   r"$\theta_{j_2}$",
    "jet2_mass":                    r"$m_{j_2}$",
    "btag_max":                     r"$\mathrm{btag}_{\max}$",
    "stag_other":                   r"$\mathrm{stag}_{\mathrm{other}}$",
}

final_states = "mumu"

# Process names mapped to file names.
# mumuH_Hbs and mumuH_Hother share the same ROOT files;
# they are split at training time via the gen-level is_Hbs branch.
mode_names = {
    "mumuH_Hbs":    "wzp6_ee_mumuH_Hbs_ecm240",  # signal: dedicated H->bs sample
    "mumuH_Hother": "wzp6_ee_mumuH_ecm240",        # background: other H decays (gen-filtered via is_Hbs)
    "ZZ":           "p8_ee_ZZ_ecm240",
    "WWmumu":       "p8_ee_WW_mumu_ecm240",
    "Zll":          "wzp6_ee_mumu_ecm240",
    "egamma":       "wzp6_egamma_eZ_Zmumu_ecm240",
    "gammae":       "wzp6_gammae_eZ_Zmumu_ecm240",
    "gaga_mumu":    "wzp6_gaga_mumu_60_ecm240",
}
