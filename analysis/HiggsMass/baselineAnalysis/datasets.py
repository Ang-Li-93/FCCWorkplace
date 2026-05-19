
import ROOT, copy

datasets = {}




#####################################
### IDEA
#####################################
dir_ = "/eos/experiment/fcc/ee/generation/DelphesEvents/spring2021/IDEA/"

## signal samples
datasets['wzp6_ee_mumuH_ecm240_reweighted'] = {
    "eos"       : "%s/wzp6_ee_mumuH_ecm240" % dir_,
    "nevents"   : 1000000,
    "xsec"      : 0.0067656
}

datasets['wzp6_ee_mumuH_ecm240'] = {
    "eos"       : "%s/wzp6_ee_mumuH_ecm240" % dir_,
    "nevents"   : 1000000,
    "xsec"      : 0.0067656
}

datasets['wzp6_ee_mumuH_mH-lower-50MeV_ecm240'] = {
    "eos"       : "%s/wzp6_ee_mumuH_mH-lower-50MeV_ecm240" % dir_,
    "nevents"   : 1000000,
    "xsec"      : 0.0067738
}

datasets['wzp6_ee_mumuH_mH-lower-100MeV_ecm240'] = {
    "eos"       : "%s/wzp6_ee_mumuH_mH-lower-100MeV_ecm240" % dir_,
    "nevents"   : 1000000,
    "xsec"      : 0.0067849
}

datasets['wzp6_ee_mumuH_mH-higher-100MeV_ecm240'] = {
    "eos"       : "%s/wzp6_ee_mumuH_mH-higher-100MeV_ecm240" % dir_,
    "nevents"   : 1000000,
    "xsec"      : 0.0067393
}

datasets['wzp6_ee_mumuH_mH-higher-50MeV_ecm240'] = {
    "eos"       : "%s/wzp6_ee_mumuH_mH-higher-50MeV_ecm240" % dir_,
    "nevents"   : 1000000,
    "xsec"      : 0.0067488
}

datasets['wzp6_ee_mumuH_noISR_ecm240'] = {
    "eos"       : "%s/wzp6_ee_mumuH_noISR_ecm240" % dir_,
    "nevents"   : 1000000,
    "xsec"      : 0.0079757
}

datasets['wzp6_ee_mumuH_ISRnoRecoil_ecm240'] = {
    "eos"       : "%s/wzp6_ee_mumuH_ISRnoRecoil_ecm240" % dir_,
    "nevents"   : 1000000,
    "xsec"      : 0.0067223
}

datasets['wzp6_ee_mumuH_noFSR_ecm240'] = {
    "eos"       : "%s/wzp6_ee_mumuH_noFSR_ecm240" % dir_,
    "nevents"   : 1000000,
    "xsec"      : 0.0067602
}

datasets['wzp6_noBES_ee_mumuH_ecm240'] = {
    "eos"       : "%s/wzp6_noBES_ee_mumuH_ecm240" % dir_,
    "nevents"   : 1000000,
    "xsec"      : 0.0067643
}

datasets['wzp6_ee_mumuH_BES-higher-6pc_ecm240'] = {
    "eos"       : "%s/wzp6_ee_mumuH_BES-higher-6pc_ecm240" % dir_,
    "nevents"   : 1000000,
    "xsec"      : 0.00676052
}

datasets['wzp6_ee_mumuH_BES-lower-6pc_ecm240'] = {
    "eos"       : "%s/wzp6_ee_mumuH_BES-lower-6pc_ecm240" % dir_,
    "nevents"   : 1000000,
    "xsec"      : 0.00676602
}

datasets['wzp6_ee_mumuH_BES-higher-1pc_ecm240'] = {
    "eos"       : "%s/wzp6_ee_mumuH_BES-higher-1pc_ecm240" % dir_,
    "nevents"   : 1000000,
    "xsec"      : 0.0067614
}

datasets['wzp6_ee_mumuH_BES-lower-1pc_ecm240'] = {
    "eos"       : "%s/wzp6_ee_mumuH_BES-lower-1pc_ecm240" % dir_,
    "nevents"   : 1000000,
    "xsec"      : 0.0067609
}

datasets['wzp6_ee_tautauH_ecm240'] = {
    "eos"       : "%s/wzp6_ee_tautauH_ecm240" % dir_,
    "nevents"   : 900000,
    "xsec"      : 0.0067518
}

datasets['wzp6_ee_eeH_ecm240'] = {
    "eos"       : "%s/wzp6_ee_eeH_ecm240" % dir_,
    "nevents"   : 900000,
    "xsec"      : 0.0071611
}

datasets['wzp6_ee_nunuH_ecm240'] = {
    "eos"       : "%s/wzp6_ee_nunuH_ecm240" % dir_,
    "nevents"   : 3000000,
    "xsec"      : 0.046191
}

datasets['wzp6_ee_qqH_ecm240'] = {
    "eos"       : "%s/wzp6_ee_qqH_ecm240" % dir_,
    "nevents"   : 9900000,
    "xsec"      : 0.13635
}

datasets['p8_ee_ZH_ecm240'] = {
    "eos"       : "%s/p8_ee_ZH_ecm240" % dir_,
    "nevents"   : 1e7,
    "xsec"      : 0.201868 # *0.1086*0.1086 *0.033662
}

datasets['p8_ee_ZH_ecm240_noBES'] = {
    "eos"       : "%s/p8_ee_ZH_ecm240_noBES" % dir_,
    "nevents"   : 1e7,
    "xsec"      : 0.201037 # *0.1086*0.1086 *0.033662
}


## main backgrounds
datasets['p8_ee_WW_ecm240'] = {
    "eos"       : "%s/p8_ee_WW_ecm240" % dir_,
    "nevents"   : 10000000,
    "xsec"      : 16.4385
}

datasets['p8_noBES_ee_WW_ecm240'] = {
    "eos"       : "%s/p8_noBES_ee_WW_ecm240" % dir_,
    "nevents"   : 10000000,
    "xsec"      : 16.4385
}

datasets['p8_ee_WW_mumu_ecm240'] = {
    "eos"       : "%s/p8_ee_WW_mumu_ecm240" % dir_,
    "nevents"   : 10000000,
    "xsec"      : 0.25792
}

datasets['p8_ee_ZZ_ecm240'] = {
    "eos"       : "%s/p8_ee_ZZ_ecm240" % dir_,
    "nevents"   : 10000000,
    "xsec"      : 1.35899
}

datasets['p8_ee_ZZ_Zll_ecm240'] = {
    "eos"       : "%s/p8_ee_ZZ_Zll_ecm240" % dir_,
    "nevents"   : 1e7,
    "xsec"      : 0.027
}

datasets['p8_noBES_ee_ZZ_ecm240'] = {
    "eos"       : "%s/p8_noBES_ee_ZZ_ecm240" % dir_,
    "nevents"   : 10000000,
    "xsec"      : 1.35899
}

datasets['p8_ee_Zll_ecm240'] = {
    "eos"       : "%s/p8_ee_Zll_ecm240" % dir_,
    "nevents"   : 9900000,
    "xsec"      : 13.7787
}

datasets['p8_ee_Zqq_ecm240'] = { ## no events in selection ?
    "eos"       : "%s/p8_ee_Zqq_ecm240" % dir_,
    "nevents"   : 10000000,
    "xsec"      : 52.6539
}




## rare backgrounds
datasets['wzp6_egamma_eZ_Zmumu_ecm240'] = {
    "eos"       : "%s/wzp6_egamma_eZ_Zmumu_ecm240" % dir_,
    "nevents"   : 5000000,
    "xsec"      : 0.10368
}

datasets['wzp6_gammae_eZ_Zmumu_ecm240'] = {
    "eos"       : "%s/wzp6_gammae_eZ_Zmumu_ecm240" % dir_,
    "nevents"   : 5000000,
    "xsec"      : 0.10368
}

datasets['wzp6_gaga_mumu_60_ecm240'] = {
    "eos"       : "%s/wzp6_gaga_mumu_60_ecm240" % dir_,
    "nevents"   : 30000000,
    "xsec"      : 1.5523
}

datasets['wzp6_gaga_tautau_60_ecm240'] = {
    "eos"       : "%s/wzp6_gaga_tautau_60_ecm240" % dir_,
    "nevents"   : 20000000,
    "xsec"      : 0.836
}







#####################################
### IDEA 3T
#####################################

datasets['IDEA_FS_wzp6_ee_mumuH_ecm240'] = {
    "file"      : "output_hists/IDEA_FS_wzp6_ee_mumuH_ecm240_{sel}.root",
    "nevents"   : 1000000,
    "name"      : "ZH, WZP6, nominal",
    "color"     : ROOT.kOrange,
    "xsec"      : 0.0067656
}


sets['IDEA_FS_wzp6_ee_mumuH_ecm240'] = {
    "file"      : "output_hists/IDEA_FS_wzp6_ee_mumuH_ecm240_{sel}.root",
    "nevents"   : 1000000,
    "name"      : "ZH, WZP6, nominal",
    "color"     : ROOT.kOrange,
    "xsec"      : 0.0067656
}

#####################################
### IDEA FullSilicon
#####################################



datasets['IDEA_3T_wzp6_ee_mumuH_mH-lower-50MeV_ecm240'] = {
    "file"      : "output_hists/IDEA_3T_wzp6_ee_mumuH_mH-lower-50MeV_ecm240_{sel}.root",
    "nevents"   : 1000000,
    "name"      : "ZH, WZP6, BES 6% Up",
    "color"     : ROOT.kOrange,
    "xsec"      : 0.0067738
}

datasets['IDEA_3T_wzp6_ee_mumuH_mH-lower-100MeV_ecm240'] = {
    "file"      : "output_hists/IDEA_3T_wzp6_ee_mumuH_mH-lower-100MeV_ecm240_{sel}.root",
    "nevents"   : 1000000,
    "name"      : "ZH, WZP6, BES 6% Down",
    "color"     : ROOT.kOrange,
    "xsec"      : 0.0067849
}


datasets['IDEA_3T_wzp6_ee_mumuH_mH-higher-100MeV_ecm240'] = {
    "file"      : "output_hists/IDEA_3T_wzp6_ee_mumuH_mH-higher-100MeV_ecm240_{sel}.root",
    "nevents"   : 1000000,
    "name"      : "ZH, WZP6, BES 1% Up",
    "color"     : ROOT.kOrange,
    "xsec"      : 0.0067393
}

datasets['IDEA_3T_wzp6_ee_mumuH_mH-higher-50MeV_ecm240'] = {
    "file"      : "output_hists/IDEA_3T_wzp6_ee_mumuH_mH-higher-50MeV_ecm240_{sel}.root",
    "nevents"   : 1000000,
    "name"      : "ZH, WZP6, BES 1% Down",
    "color"     : ROOT.kOrange,
    "xsec"      : 0.0067488
}




datasets['IDEA_3T_wzp6_ee_mumuH_ecm240'] = {
    "file"      : "output_hists/IDEA_3T_wzp6_ee_mumuH_ecm240_{sel}.root",
    "nevents"   : 1000000,
    "name"      : "ZH, WZP6, nominal",
    "color"     : ROOT.kOrange,
    "xsec"      : 0.0067656
}

datasets['IDEA_FS_wzp6_ee_mumuH_mH-lower-50MeV_ecm240'] = {
    "file"      : "output_hists/IDEA_FS_wzp6_ee_mumuH_mH-lower-50MeV_ecm240_{sel}.root",
    "nevents"   : 1000000,
    "name"      : "ZH, WZP6, BES 6% Up",
    "color"     : ROOT.kOrange,
    "xsec"      : 0.0067738
}

datasets['IDEA_FS_wzp6_ee_mumuH_mH-lower-100MeV_ecm240'] = {
    "file"      : "output_hists/IDEA_FS_wzp6_ee_mumuH_mH-lower-100MeV_ecm240_{sel}.root",
    "nevents"   : 1000000,
    "name"      : "ZH, WZP6, BES 6% Down",
    "color"     : ROOT.kOrange,
    "xsec"      : 0.0067849
}


datasets['IDEA_FS_wzp6_ee_mumuH_mH-higher-100MeV_ecm240'] = {
    "file"      : "output_hists/IDEA_FS_wzp6_ee_mumuH_mH-higher-100MeV_ecm240_{sel}.root",
    "nevents"   : 1000000,
    "name"      : "ZH, WZP6, BES 1% Up",
    "color"     : ROOT.kOrange,
    "xsec"      : 0.0067393
}

datasets['IDEA_FS_wzp6_ee_mumuH_mH-higher-50MeV_ecm240'] = {
    "file"      : "output_hists/IDEA_FS_wzp6_ee_mumuH_mH-higher-50MeV_ecm240_{sel}.root",
    "nevents"   : 1000000,
    "name"      : "ZH, WZP6, BES 1% Down",
    "color"     : ROOT.kOrange,
    "xsec"      : 0.0067488
}



