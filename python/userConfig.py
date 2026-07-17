import os

# Placeholders for final_state and ecm
final_state_placeholder = "{final_state}"
ecm_placeholder = "{ecm}"

repo = f"/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/mass_xsec/lia/FCCee/FinalReport2/S{ecm_placeholder}/{final_state_placeholder}"

#repo can be changed, but by default writes locally
class loc : pass
loc.ROOT = repo+'/'
loc.OUT = loc.ROOT+'output_trained/'
loc.DATA = loc.ROOT+'data'
loc.CSV = loc.DATA+'/csv'
loc.PKL = loc.DATA+'/pkl'
loc.PKL_Val = loc.DATA+'/pkl_val'
loc.ROOTFILES = loc.DATA+'/ROOT'
loc.PLOTS = loc.DATA+'/plots'
#loc.PLOTS = loc.OUT+'plots'
loc.PLOTS_Val = loc.OUT+'plots_val'
loc.TEX = loc.OUT+'tex'
loc.JSON = loc.OUT+'json'

#EOS location for files used in analysis
loc.EOS = f"/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/mass_xsec/lia/FCCee/FinalReport2/S{ecm_placeholder}/{final_state_placeholder}"

#Output BDT model location - used in official sample production to assign MVA weights
loc.BDT = f"{loc.EOS}/BDT"

#Loaction of prod_04 tuples used in analysis
loc.PROD = f"{loc.EOS}"

#Samples for first stage BDT training
loc.TRAIN = f"{loc.PROD}/MVAInputs"

#Samples for second stage training
loc.TRAIN2 = f"{loc.PROD}/Training_4stage2/"

#Samples for final analysis
loc.ANALYSIS = f"{loc.PROD}/BDT_analysis_samples/"

#First stage BDT including event-level vars
train_vars = [
              #leptons
              "leading_zll_lepton_p",
              "leading_zll_lepton_theta",
              "subleading_zll_lepton_p",
              "subleading_zll_lepton_theta",
              "zll_leptons_acolinearity",
              "zll_leptons_acoplanarity",
              #Zed
              "zll_m",
              "zll_p",
              "zll_theta"
              #Higgsstrahlungness
              #"H",
              ]
latex_mapping = {
    'leading_zll_lepton_p': r'$p_{\ell_1}$',
    'leading_zll_lepton_theta': r'$\theta_{\ell_1}$',
    'subleading_zll_lepton_p': r'$p_{\ell_2}$',
    'subleading_zll_lepton_theta': r'$\theta_{\ell_2}$',
    'zll_leptons_acolinearity': r'$|\Delta\theta_{\ell\ell}|$',
    'zll_leptons_acoplanarity': r'$|\Delta\phi_{\ell\ell}|$',
    'zll_m': r'$m_{\ell\ell}$',
    'zll_p': r'$p_{\ell\ell}$',
    'zll_theta': r'$\theta_{\ell\ell}$',
    'H': r'$H$'
}

#final_states = "mumu"

#First stage BDT including event-level vars and vertex vars

#Decay modes used in first stage training and their respective file names
mode_names = {f"{final_state_placeholder}H": f"wzp6_ee_{final_state_placeholder}H_ecm{ecm_placeholder}",
              "ZZ": f"p8_ee_ZZ_ecm{ecm_placeholder}",
              f"WW{final_state_placeholder}": f"p8_ee_WW_{final_state_placeholder}_ecm{ecm_placeholder}",
              "Zll": f"wzp6_ee_{final_state_placeholder}_ecm{ecm_placeholder}",
              "egamma": f"wzp6_egamma_eZ_Z{final_state_placeholder}_ecm{ecm_placeholder}",
              "gammae": f"wzp6_gammae_eZ_Z{final_state_placeholder}_ecm{ecm_placeholder}",
              f"gaga_{final_state_placeholder}": f"wzp6_gaga_{final_state_placeholder}_60_ecm{ecm_placeholder}"}

