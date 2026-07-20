
def get_datasets(baseDir = ""):

    datasets = []
    baseDir = "/eos/experiment/fcc/ee/generation/DelphesEvents/pre_fall2022_training/IDEA/"

    datasets.append({
        "name"      : "p8_ee_ZH_Znunu_Hbb_ecm240",
        "datadir"   : "%s/p8_ee_ZH_Znunu_Hbb_ecm240" % baseDir,
        "xsec"      : 0.201868
    })
    
    datasets.append({
        "name"      : "p8_ee_ZH_Znunu_Hcc_ecm240",
        "datadir"   : "%s/p8_ee_ZH_Znunu_Hcc_ecm240" % baseDir,
        "xsec"      : 0.201868
    })
    
    datasets.append({
        "name"      : "p8_ee_ZH_Znunu_Hdd_ecm240",
        "datadir"   : "%s/p8_ee_ZH_Znunu_Hdd_ecm240" % baseDir,
        "xsec"      : 0.201868
    })
    
    datasets.append({
        "name"      : "p8_ee_ZH_Znunu_Hgg_ecm240",
        "datadir"   : "%s/p8_ee_ZH_Znunu_Hgg_ecm240" % baseDir,
        "xsec"      : 0.201868
    })
    
    datasets.append({
        "name"      : "p8_ee_ZH_Znunu_Hss_ecm240",
        "datadir"   : "%s/p8_ee_ZH_Znunu_Hss_ecm240" % baseDir,
        "xsec"      : 0.201868
    })
    
    datasets.append({
        "name"      : "p8_ee_ZH_Znunu_Htautau_ecm240",
        "datadir"   : "%s/p8_ee_ZH_Znunu_Htautau_ecm240" % baseDir,
        "xsec"      : 0.201868
    })
    
    datasets.append({
        "name"      : "p8_ee_ZH_Znunu_Huu_ecm240",
        "datadir"   : "%s/p8_ee_ZH_Znunu_Huu_ecm240" % baseDir,
        "xsec"      : 0.201868
    })


    # pre-fall (fixed muon isolation)
    datasets.append({
        "name"      : "wzp6_ee_mumuH_ecm240_prefall",
        "datadir"   : "/eos/experiment/fcc/ee/generation/DelphesEvents/pre_fall2022_training/IDEA/wzp6_ee_mumuH_ecm240",
        "xsec"      : 0.201868
    })
    
    datasets.append({
        "name"      : "wz3p6_ee_mumuH_ecm240_prefall",
        "datadir"   : "/eos/experiment/fcc/ee/generation/DelphesEvents/pre_fall2022/IDEA/wzp6_ee_mumuH_ecm240",
        "xsec"      : 0.201868
    })
    
    
    # winter v1 (fixed muon resolution)
    datasets.append({
        "name"      : "wz3p6_ee_mumuH_ecm240_winter",
        "datadir"   : "/eos/experiment/fcc/ee/generation/DelphesStandalone/Edm4Hep/pre_winter2023_tests_v1/wz3p6_ee_mumuH_ecm240",
        "xsec"      : 0.201868
    })
    
    datasets.append({
        "name"      : "wzp6_ee_eeH_ecm240_winter",
        "datadir"   : "/eos/experiment/fcc/ee/generation/DelphesStandalone/Edm4Hep/pre_winter2023_tests_v1/wzp6_ee_eeH_ecm240",
        "xsec"      : 0.201868
    })
    
    ##############################################################
    # winter v2 (electrons smeared with twice the resolution)
    winter_v2 = "/eos/experiment/fcc/ee/generation/DelphesStandalone/Edm4Hep/pre_winter2023_tests_v2"
    #winter_v2 = "/data/shared/jaeyserm/fccee/pre_winter2023_tests_v2"
    winter_v1 = "/eos/experiment/fcc/ee/generation/DelphesStandalone/Edm4Hep/pre_winter2023_tests_v1"
    
    # muon signal
    datasets.append({
        "name"      : "wz3p6_ee_mumuH_ecm240",
        "datadir"   : "%s/wz3p6_ee_mumuH_ecm240" % winter_v2,
        "xsec"      : 0.0067643
    })
    
    datasets.append({
        "name"      : "wzp6_ee_mumuH_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_ecm240/" % winter_v2,
        "xsec"      : 0.0067643
    })
    
    datasets.append({
        "name"      : "wzp6_ee_mumuH_ecm240_winter",
        "datadir"   : "/eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA//wzp6_ee_mumuH_ecm240/",
        "xsec"      : 0.0067643
    })
    
    datasets.append({
        "name"      : "wzp6_ee_mumuH_mH-higher-100MeV_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_mH-higher-100MeV_ecm240" % winter_v2,
        "xsec"      : 0.0067393
    })
    
    datasets.append({
        "name"      : "wzp6_ee_mumuH_mH-higher-50MeV_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_mH-higher-50MeV_ecm240" % winter_v2,
        "xsec"      : 0.0067488
    })
    
    datasets.append({
        "name"      : "wzp6_ee_mumuH_mH-lower-100MeV_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_mH-lower-100MeV_ecm240" % winter_v2,
        "xsec"      : 0.0067849
    })
    
    datasets.append({
        "name"      : "wzp6_ee_mumuH_mH-lower-50MeV_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_mH-lower-50MeV_ecm240" % winter_v2,
        "xsec"      : 0.0067738
    })

    # electron signal
    datasets.append({
        "name"      : "wzp6_ee_eeH_ecm240",
        "datadir"   : "%s/wzp6_ee_eeH_ecm240" % winter_v2,
        "xsec"      : 0.0071611
    })
    
    datasets.append({
        "name"      : "wzp6_ee_eeH_mH-higher-100MeV_ecm240",
        "datadir"   : "%s/wzp6_ee_eeH_mH-higher-100MeV_ecm240" % winter_v2,
        "xsec"      : 0.007137
    })
    
    datasets.append({
        "name"      : "wzp6_ee_eeH_mH-higher-50MeV_ecm240",
        "datadir"   : "%s/wzp6_ee_eeH_mH-higher-50MeV_ecm240" % winter_v2,
        "xsec"      : 0.007152
    })
    
    datasets.append({
        "name"      : "wzp6_ee_eeH_mH-lower-100MeV_ecm240",
        "datadir"   : "%s/wzp6_ee_eeH_mH-lower-100MeV_ecm240" % winter_v2,
        "xsec"      : 0.007188
    })
    
    datasets.append({
        "name"      : "wzp6_ee_eeH_mH-lower-50MeV_ecm240",
        "datadir"   : "%s/wzp6_ee_eeH_mH-lower-50MeV_ecm240" % winter_v2,
        "xsec"      : 0.007169
    })
    
    
    datasets.append({
        "name"      : "wzp6_ee_eeH_ecm240_v1",
        "datadir"   : "%s/wzp6_ee_eeH_ecm240" % winter_v1,
        "xsec"      : 0.0071611
    })
    
    datasets.append({
        "name"      : "wzp6_ee_eeH_ecm240_v2",
        "datadir"   : "%s/wzp6_ee_eeH_ecm240" % winter_v2,
        "xsec"      : 0.0071611
    })
    
    datasets.append({
        "name"      : "wzp6_ee_eeH_ecm240_v3",
        "datadir"   : "/eos/experiment/fcc/ee/generation/DelphesStandalone/Edm4Hep/pre_winter2023_tests_v3//wzp6_ee_eeH_ecm240",
        "xsec"      : 0.0071611
    })

    datasets.append({
        "name"      : "wzp6_ee_eeH_ecm240_v4",
        "datadir"   : "/eos/experiment/fcc/ee/generation/DelphesStandalone/Edm4Hep/pre_winter2023_tests_v4/wzp6_ee_eeH_ecm240",
        "xsec"      : 0.0071611
    })



    
    # backgrounds
    datasets.append({
        "name"      : "p8_ee_WW_ecm240",
        "datadir"   : "%s/p8_ee_WW_ecm240" % winter_v2,
        "xsec"      : 16.4385
    })
    
    datasets.append({
        "name"      : "p8_ee_WW_mumu_ecm240",
        "datadir"   : "%s/p8_ee_WW_mumu_ecm240" % winter_v2,
        "xsec"      : 0.25792
    })
    
    datasets.append({
        "name"      : "p8_ee_ZZ_ecm240",
        "datadir"   : "%s/p8_ee_ZZ_ecm240" % winter_v2,
        "xsec"      : 1.35899
    })
    
    datasets.append({
        "name"      : "p8_ee_ZZ_Zll_ecm240", # Z to e, mu, tau
        "datadir"   : "%s/p8_ee_ZZ_Zll_ecm240" % winter_v2,
        "xsec"      : 0.027
    })
    
    
    datasets.append({
        "name"      : "wzp6_ee_mumu_ecm240", # Z/gamma* to mumu, ecm=240 GeV
        "datadir"   : "%s/wzp6_ee_mumu_ecm240" % winter_v2,
        "xsec"      : 5.288
    })
    
    datasets.append({
        "name"      : "wzp6_ee_ee_Mee_30_150_ecm240", # ee (s and t), ecm=240 GeV
        "datadir"   : "%s/wzp6_ee_ee_Mee_30_150_ecm240" % winter_v2,
        "xsec"      : 8.305
    })
    
    datasets.append({
        "name"      : "wzp6_ee_tautau_ecm240", # Z/gamma* to tautau, ecm=240 GeV
        "datadir"   : "%s/wzp6_ee_tautau_ecm240" % winter_v2,
        "xsec"      : 4.668
    })
    
    datasets.append({
        "name"      : "p8_ee_Zll_ecm240", # Z/Gamma* ecm=240GeV, leptonic decays (e/mu/tau) - replaced by Whizard
        "datadir"   : "%s/p8_ee_Zll_ecm240" % winter_v2,
        "xsec"      : 13.7787
    })
    
    
    # particle guns
    datasets.append({
        "name"      : "muon_gun",
        "datadir"   : "/data/shared/jaeyserm/fccee/pre_winter2023_tests_v2/guns/muon/",
        "xsec"      : 1
    })
    
    datasets.append({
        "name"      : "muon_gun_smear2x",
        "datadir"   : "/data/shared/jaeyserm/fccee/pre_winter2023_tests_v2/guns/muon_smear2x/",
        "xsec"      : 1
    })
    
    datasets.append({
        "name"      : "electron_gun",
        "datadir"   : "/data/shared/jaeyserm/fccee/pre_winter2023_tests_v2/guns/electron/",
        "xsec"      : 1
    })
    
    
    
    
    # othters   
    datasets.append({
        "name"      : "p8_ee_ZH_Zmumu_Hinv_ecm240_winter_v2",
        "datadir"   : "/eos/experiment/fcc/ee/generation/DelphesStandalone/Edm4Hep/pre_winter2023_tests_v2/p8_ee_ZH_Zmumu_Hinv_ecm240",
        "xsec"      : 0.201868
    })
    
    
    return datasets