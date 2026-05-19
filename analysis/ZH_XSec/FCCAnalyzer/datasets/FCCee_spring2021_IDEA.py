
# http://fcc-physics-events.web.cern.ch/fcc-physics-events/FCCee/spring2021/Delphesevents_IDEA.php

def get_datasets(baseDir = ""):

    datasets = []
    subDir = "/spring2021/IDEA/"
    baseDir = "%s/%s" % (baseDir, subDir)

    ## signal samples
    datasets.append({
        "name"      : "wzp6_ee_mumuH_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_ecm240" % baseDir,
        "xsec"      : 0.0067643
    })
    

    datasets.append({
        "name"      : "p8_ee_ZH_ecm240",
        "datadir"   : "%s/p8_ee_ZH_ecm240" % baseDir,
        "xsec"      : 0.201868
    })

    datasets.append({
        "name"      : "p8_ee_Zmumu_ecm91",
        "datadir"   : "%s/p8_ee_Zmumu_ecm91" % baseDir,
        "xsec"      : 1462.08
    })


    
    datasets.append({
        "name"      : "wzp6_ee_mumuH_mH-lower-50MeV_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_mH-lower-50MeV_ecm240" % baseDir,
        "xsec"      : 0.0067738
    })

    datasets.append({
        "name"      : "wzp6_ee_mumuH_mH-lower-100MeV_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_mH-lower-100MeV_ecm240" % baseDir,
        "xsec"      : 0.0067849
    })

    datasets.append({
        "name"      : "wzp6_ee_mumuH_mH-higher-100MeV_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_mH-higher-100MeV_ecm240" % baseDir,
        "xsec"      : 0.0067393
    })
    
    datasets.append({
        "name"      : "wzp6_ee_mumuH_mH-higher-50MeV_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_mH-higher-50MeV_ecm240" % baseDir,
        "xsec"      : 0.0067488
    })

    datasets.append({
        "name"      : "wzp6_ee_mumuH_noISR_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_noISR_ecm240" % baseDir,
        "xsec"      : 0.0079757
    })

    datasets.append({
        "name"      : "wzp6_ee_mumuH_ISRnoRecoil_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_ISRnoRecoil_ecm240" % baseDir,
        "xsec"      : 0.0067223
    })
    
    datasets.append({
        "name"      : "wzp6_noBES_ee_mumuH_ecm240",
        "datadir"   : "%s/wzp6_noBES_ee_mumuH_ecm240" % baseDir,
        "xsec"      : 0.0067626
    })
    
    datasets.append({
        "name"      : "wzp6_ee_mumuH_BES-higher-6pc_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_BES-higher-6pc_ecm240" % baseDir,
        "xsec"      : 0.00676052
    })

    datasets.append({
        "name"      : "wzp6_ee_mumuH_BES-lower-6pc_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_BES-lower-6pc_ecm240" % baseDir,
        "xsec"      : 0.00676602
    })
    
    datasets.append({
        "name"      : "wzp6_ee_mumuH_BES-higher-1pc_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_BES-higher-1pc_ecm240" % baseDir,
        "xsec"      : 0.0067614
    })
    
    datasets.append({
        "name"      : "wzp6_ee_mumuH_BES-lower-1pc_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_BES-lower-1pc_ecm240" % baseDir,
        "xsec"      : 0.00676093
    })
    
    datasets.append({
        "name"      : "wzp6_ee_tautauH_ecm240",
        "datadir"   : "%s/wzp6_ee_tautauH_ecm240" % baseDir,
        "xsec"      : 0.0067518
    })
    
    datasets.append({
        "name"      : "wzp6_ee_eeH_ecm240",
        "datadir"   : "%s/wzp6_ee_eeH_ecm240" % baseDir,
        "xsec"      : 0.0071611
    })
    
    datasets.append({
        "name"      : "wzp6_ee_nunuH_ecm240",
        "datadir"   : "%s/wzp6_ee_nunuH_ecm240" % baseDir,
        "xsec"      : 0.046191
    })

    
    datasets.append({
        "name"      : "wzp6_ee_qqH_ecm240",
        "datadir"   : "%s/wzp6_ee_qqH_ecm240" % baseDir,
        "xsec"      : 0.13635
    })
    
    datasets.append({
        "name"      : "p8_ee_ZH_ecm240",
        "datadir"   : "%s/p8_ee_ZH_ecm240" % baseDir,
        "xsec"      : 0.201868
    })
    
    datasets.append({
        "name"      : "p8_ee_ZH_ecm240_noBES",
        "datadir"   : "%s/p8_ee_ZH_ecm240_noBES" % baseDir,
        "xsec"      : 0.201037
    })
    
   

    ## main backgrounds
    datasets.append({
        "name"      : "p8_ee_WW_ecm240",
        "datadir"   : "%s/p8_ee_WW_ecm240" % baseDir,
        "xsec"      : 16.4385
    })
    
    datasets.append({
        "name"      : "p8_noBES_ee_WW_ecm240",
        "datadir"   : "%s/p8_noBES_ee_WW_ecm240" % baseDir,
        "xsec"      : 16.4385
    })
    
    datasets.append({
        "name"      : "p8_ee_WW_mumu_ecm240",
        "datadir"   : "%s/p8_ee_WW_mumu_ecm240" % baseDir,
        "xsec"      : 0.25792
    })
    
    datasets.append({
        "name"      : "p8_ee_ZZ_ecm240",
        "datadir"   : "%s/p8_ee_ZZ_ecm240" % baseDir,
        "xsec"      : 1.35899
    })
    
    datasets.append({
        "name"      : "p8_ee_ZZ_Zll_ecm240",
        "datadir"   : "%s/p8_ee_ZZ_Zll_ecm240" % baseDir,
        "xsec"      : 0.027
    })
    
    datasets.append({
        "name"      : "p8_noBES_ee_ZZ_ecm240",
        "datadir"   : "%s/p8_noBES_ee_ZZ_ecm240" % baseDir,
        "xsec"      : 1.35899
    })
    
    datasets.append({
        "name"      : "p8_ee_Zll_ecm240",
        "datadir"   : "%s/p8_ee_Zll_ecm240" % baseDir,
        "xsec"      : 13.7787
    })
    
    datasets.append({
        "name"      : "p8_ee_Zqq_ecm240",
        "datadir"   : "%s/p8_ee_Zqq_ecm240" % baseDir,
        "xsec"      : 52.6539
    })
   


    ## rare backgrounds
    datasets.append({
        "name"      : "wzp6_egamma_eZ_Zmumu_ecm240",
        "datadir"   : "%s/wzp6_egamma_eZ_Zmumu_ecm240" % baseDir,
        "xsec"      : 0.10368
    })
    
    datasets.append({
        "name"      : "wzp6_gammae_eZ_Zmumu_ecm240",
        "datadir"   : "%s/wzp6_gammae_eZ_Zmumu_ecm240" % baseDir,
        "xsec"      : 0.10368
    })
    
    datasets.append({
        "name"      : "wzp6_gaga_mumu_60_ecm240",
        "datadir"   : "%s/wzp6_gaga_mumu_60_ecm240" % baseDir,
        "xsec"      : 1.5523
    })

    datasets.append({
        "name"      : "wzp6_gaga_tautau_60_ecm240",
        "datadir"   : "%s/wzp6_gaga_tautau_60_ecm240" % baseDir,
        "xsec"      : 0.836
    })

    return datasets