"""
Single source for the leptonic (ee/mumu) BDT-training configuration, replacing the
per-directory userConfig.py copies that used to live in S{240,365}/{ee,mumu}/
(and a stale S365 top-level one). The qq channel does not use this: its training
trio has its own site-aware paths.

SITE-AWARE via site_config (like the rest of the Paper workflow):
  - SDCC : everything under storage/ZH_XSec_Paper/S{ecm}/{flavor}/ (training trees
    in MVAInputs/, working data + plots in training/, model to
    models/S{ecm}/{flavor}/xgb_bdt.root = site_config.bdt_model). To retrain on
    SDCC, first fan out the treemaker:
      python condor/submit_stage1.py S240/mumu/stage1_training_ntuples.py --stage MVAInputs
  - lxplus: the original /eos locations (240 = MidTerm, 365 = TopHiggs storage,
    as in site_config; NB the retired S365 userConfig copies pointed at an older
    FinalReport/S365 staging area instead).

ACOLINEARITY VARIANT (env LEP_ACOL=jan, default 'training' = unchanged behaviour): the trio
trains/evaluates with the FCCPhysics-histmaker acolinearity (pi - opening angle, computed by
training_utils.get_df from the stored lepton theta/phi into the zll_leptons_acolinearity
column); working data go to <base>/training_janacol and FCC_MODELS_BASE must point at a
separate model tree (e.g. models_variants/janacol). Downstream: rescore_leptonic.py --acol jan.

Usage (from a channel-directory script):
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    from leptonic_training_config import make
    loc, train_vars, mode_names, latex_mapping, final_states = make(240, "mumu")
"""
import os

from site_config import SITE, bdt_model, output_dir

# first-stage BDT input variables (identical for ee/mumu and both energies)
TRAIN_VARS = [
    # leptons
    "leading_zll_lepton_p",
    "leading_zll_lepton_theta",
    "subleading_zll_lepton_p",
    "subleading_zll_lepton_theta",
    "zll_leptons_acolinearity",
    "zll_leptons_acoplanarity",
    # Zed
    "zll_m",
    "zll_p",
    "zll_theta",
]

LATEX_MAPPING = {
    'leading_zll_lepton_p': r'$p_{\ell_1}$',
    'leading_zll_lepton_theta': r'$\theta_{\ell_1}$',
    'subleading_zll_lepton_p': r'$p_{\ell_2}$',
    'subleading_zll_lepton_theta': r'$\theta_{\ell_2}$',
    'zll_leptons_acolinearity': r'$|\Delta\theta_{\ell\ell}|$',
    'zll_leptons_acoplanarity': r'$|\Delta\phi_{\ell\ell}|$',
    'zll_m': r'$m_{\ell\ell}$',
    'zll_p': r'$p_{\ell\ell}$',
    'zll_theta': r'$\theta_{\ell\ell}$',
    'H': r'$H$',
}


def make(ecm, flavor):
    """Return (loc, train_vars, mode_names, latex_mapping, final_states)."""
    assert int(ecm) in (240, 365) and flavor in ("ee", "mumu"), (ecm, flavor)
    ecm = int(ecm)

    # site-dependent base for this energy/flavor (SDCC GPFS or original lxplus /eos)
    repo = output_dir(ecm, flavor, "").rstrip("/")

    # Acolinearity variant (env LEP_ACOL=jan, see training_utils.get_df): the working data go
    # to a separate '<data>_janacol' dir and the model MUST be redirected with FCC_MODELS_BASE
    # (e.g. .../models_variants/janacol), so the nominal pickles/plots/models are never touched.
    acol = os.environ.get("LEP_ACOL", "training").lower()
    if acol not in ("training", "jan"):
        raise ValueError(f"LEP_ACOL={acol!r}: expected 'training' or 'jan'")
    if acol == "jan" and not os.environ.get("FCC_MODELS_BASE"):
        raise SystemExit("LEP_ACOL=jan requires FCC_MODELS_BASE=<dir> (e.g. <SDCC_BASE>/models_variants/janacol): "
                         "refusing to write a Jan-acolinearity model over the nominal models")
    data_sub = ('/training' if SITE == "sdcc" else '/data') + ('_janacol' if acol == "jan" else '')

    class loc:
        pass
    loc.ROOT = repo + '/'
    loc.OUT = loc.ROOT + 'output_trained/'
    # working data (pickles, plots): 'training' on SDCC (as the qq trio), the
    # original 'data' subdir on lxplus
    loc.DATA = repo + data_sub
    loc.CSV = loc.DATA + '/csv'
    loc.PKL = loc.DATA + '/pkl'
    loc.PKL_Val = loc.DATA + '/pkl_val'
    loc.ROOTFILES = loc.DATA + '/ROOT'
    loc.PLOTS = loc.DATA + '/plots'
    loc.PLOTS_Val = loc.OUT + 'plots_val'
    loc.TEX = loc.OUT + 'tex'
    loc.JSON = loc.OUT + 'json'
    loc.EOS = repo
    loc.BDT = os.path.dirname(bdt_model(ecm, flavor))  # single source for the model path
    loc.PROD = f"{loc.EOS}"
    loc.TRAIN = f"{loc.PROD}/MVAInputs"
    loc.TRAIN2 = f"{loc.PROD}/Training_4stage2/"
    loc.ANALYSIS = f"{loc.PROD}/BDT_analysis_samples/"

    zll = f"wzp6_ee_mumu_ecm{ecm}" if flavor == "mumu" else f"wzp6_ee_ee_Mee_30_150_ecm{ecm}"
    mode_names = {
        f"{flavor}H": f"wzp6_ee_{flavor}H_ecm{ecm}",
        "ZZ": f"p8_ee_ZZ_ecm{ecm}",
        f"WW{flavor}": f"p8_ee_WW_{flavor}_ecm{ecm}",
        "Zll": zll,
        "egamma": f"wzp6_egamma_eZ_Z{flavor}_ecm{ecm}",
        "gammae": f"wzp6_gammae_eZ_Z{flavor}_ecm{ecm}",
        f"gaga_{flavor}": f"wzp6_gaga_{flavor}_60_ecm{ecm}",
    }
    if ecm == 365:
        # as in the original S365 userConfigs: the exclusive WW samples are not used
        # at 365 (and gaga_ee neither, for the ee channel)
        del mode_names[f"WW{flavor}"]
        if flavor == "ee":
            del mode_names["gaga_ee"]

    latex = dict(LATEX_MAPPING)
    if acol == "jan":
        latex['zll_leptons_acolinearity'] = r'$\pi-\alpha_{\ell\ell}$'  # pi - opening angle
    return loc, list(TRAIN_VARS), mode_names, latex, flavor
