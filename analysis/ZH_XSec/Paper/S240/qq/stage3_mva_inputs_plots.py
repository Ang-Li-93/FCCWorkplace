# Stage3: plots of the qq BDT input variables (ecm 240) from the stage2_mva_inputs.py
# histograms. Mirrors the leptonic stage3_mva_inputs_plots.py (fccanalysis plots config).
#
# Run: fccanalysis plots analysis/ZH_XSec/Paper/S240/qq/stage3_mva_inputs_plots.py
import ROOT
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from site_config import output_dir as _sdir

ecm = 240

# global parameters
intLumi        = 10.8e+06  # pb-1
ana_tex        = 'e^{+}e^{-} #rightarrow ZH, Z #rightarrow q#bar{q}'
delphesVersion = '3.4.2'
energy         = 240.0
collider       = 'FCC-ee'
inputDir       = _sdir(ecm, "qq", "MVAInputs_final") + "/"  # do_plots concatenates without separator
outdir         = _sdir(ecm, "qq", "MVAInputs_plots") + "/"
formats        = ['png', 'pdf']
yaxis          = ['lin', 'log']
stacksig       = ['stack', 'nostack']

variables = [
    "zqq_p_best", "zqq_m_best", "zqq_recoil_m_best",
    "leading_jet_p", "subleading_jet_p",
    "leading_jet_costheta", "subleading_jet_costheta", "z_costheta",
    "acolinearity", "acoplanarity",
    "W1_p", "W2_p", "W1_m", "W2_m", "W1_costheta", "W2_costheta",
    "thrust_magn",
]

###Dictionary with the analysis name as key, and the list of selections to be plotted
selections = {}
selections['ZHqq'] = ["sel0"]

extralabel = {}
extralabel["sel0"] = "Hadronic preselection (training trees)"

z_decays = ["qq", "bb", "cc", "ss"]
h_decays = ["Hbb", "Hcc", "Hss", "Hgg", "Hmumu", "Htautau", "HZZ", "HWW", "HZa", "Haa"]
# not produced in winter2023_training at 240 (both exist at 365)
missing_240 = [("bb", "Hcc"), ("bb", "Hmumu")]
_sig_procs = [f"wzp6_ee_{z}H_{h}_ecm{ecm}" for z in z_decays for h in h_decays
              if (z, h) not in missing_240]

colors = {}
colors['ZqqH'] = ROOT.kRed
colors['WW'] = ROOT.kBlue + 1
colors['Zqq'] = ROOT.kCyan

plots = {}
plots['ZHqq'] = {'signal': {'ZqqH': _sig_procs},
                 'backgrounds': {
                     'WW': [f"p8_ee_WW_ecm{ecm}"],
                     'Zqq': [f"wzp6_ee_qq_ecm{ecm}"],
                 }}

legend = {}
legend['ZqqH'] = 'Z(q#bar{q})H'
legend['WW'] = 'W^{+}W^{-}'
legend['Zqq'] = 'Z/#gamma^{*} #rightarrow q#bar{q}'
