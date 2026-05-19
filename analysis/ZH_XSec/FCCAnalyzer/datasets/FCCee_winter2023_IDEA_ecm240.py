
# http://fcc-physics-events.web.cern.ch/fcc-physics-events/FCCee/winter2023/Delphesevents_IDEA.php

def get_datasets(baseDir = ""):

    datasets = []
    subDir = "/winter2023/IDEA/"
    baseDir = "%s/%s" % (baseDir, subDir)

    ## muon signal samples
    datasets.append({
        "name"      : "wzp6_ee_mumuH_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_ecm240" % baseDir,
        "xsec"      : 0.0067643
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
        "name"      : "wzp6_ee_mumuH_BES-higher-1pc_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_BES-higher-1pc_ecm240" % baseDir,
        "xsec"      : 0.0067614
    })
    
    datasets.append({
        "name"      : "wzp6_ee_mumuH_BES-lower-1pc_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_BES-lower-1pc_ecm240" % baseDir,
        "xsec"      : 0.00676093
    })
    
    # electron signal samples
    datasets.append({
        "name"      : "wzp6_ee_eeH_ecm240",
        "datadir"   : "%s/wzp6_ee_eeH_ecm240" % baseDir,
        "xsec"      : 0.0071611
    })
    
    datasets.append({
        "name"      : "wzp6_ee_eeH_mH-higher-100MeV_ecm240",
        "datadir"   : "%s/wzp6_ee_eeH_mH-higher-100MeV_ecm240" % baseDir,
        "xsec"      : 0.007137
    })
    
    datasets.append({
        "name"      : "wzp6_ee_eeH_mH-higher-50MeV_ecm240",
        "datadir"   : "%s/wzp6_ee_eeH_mH-higher-50MeV_ecm240" % baseDir,
        "xsec"      : 0.007152
    })
    
    datasets.append({
        "name"      : "wzp6_ee_eeH_mH-lower-100MeV_ecm240",
        "datadir"   : "%s/wzp6_ee_eeH_mH-lower-100MeV_ecm240" % baseDir,
        "xsec"      : 0.007188
    })
    
    datasets.append({
        "name"      : "wzp6_ee_eeH_mH-lower-50MeV_ecm240",
        "datadir"   : "%s/wzp6_ee_eeH_mH-lower-50MeV_ecm240" % baseDir,
        "xsec"      : 0.007169
    })
    
    datasets.append({
        "name"      : "wzp6_ee_eeH_BES-higher-1pc_ecm240",
        "datadir"   : "%s/wzp6_ee_eeH_BES-higher-1pc_ecm240" % baseDir,
        "xsec"      : 0.007159
    })
    
    datasets.append({
        "name"      : "wzp6_ee_eeH_BES-lower-1pc_ecm240",
        "datadir"   : "%s/wzp6_ee_eeH_BES-lower-1pc_ecm240" % baseDir,
        "xsec"      : 0.007169
    })
    
    
    # other ZH production mode samples
    #datasets.append({
    #    "name"      : "wzp6_ee_tautauH_ecm240",
    #    "datadir"   : "%s/wzp6_ee_tautauH_ecm240" % baseDir,
    #    "xsec"      : 0.0067518
    #})
    
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
    
    
   

    ## diboson backgrounds
    datasets.append({
        "name"      : "p8_ee_WW_ecm240",
        "datadir"   : "%s/p8_ee_WW_ecm240" % baseDir,
        "xsec"      : 16.4385
    })
    
    datasets.append({
        "name"      : "p8_ee_ZZ_ecm240",
        "datadir"   : "%s/p8_ee_ZZ_ecm240" % baseDir,
        "xsec"      : 1.35899
    })
    
   

    datasets.append({ # zero events after selection
        "name"      : "p8_ee_Zqq_ecm240",
        "datadir"   : "%s/p8_ee_Zqq_ecm240" % baseDir,
        "xsec"      : 52.6539
    })
    
    
    # dilepton backgrounds
    datasets.append({
        "name"      : "wzp6_ee_mumu_ecm240",
        "datadir"   : "%s/wzp6_ee_mumu_ecm240" % baseDir,
        "xsec"      : 5.288
    })
    
    datasets.append({
        "name"      : "wzp6_ee_tautau_ecm240",
        "datadir"   : "%s/wzp6_ee_tautau_ecm240" % baseDir,
        "xsec"      : 4.668
    })
    
    datasets.append({
        "name"      : "wzp6_ee_ee_Mee_30_150_ecm240",
        "datadir"   : "%s/wzp6_ee_ee_Mee_30_150_ecm240" % baseDir,
        "xsec"      : 8.305
    })
    
    datasets.append({
        "name"      : "wzp6_ee_nuenueZ_ecm240",
        "datadir"   : "%s/wzp6_ee_nuenueZ_ecm240" % baseDir,
        "xsec"      : 0.033274
    })
      
     
     
   


    ## e-gamma backgrounds
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
        "name"      : "wzp6_egamma_eZ_Zee_ecm240",
        "datadir"   : "%s/wzp6_egamma_eZ_Zee_ecm240" % baseDir,
        "xsec"      : 0.05198
    })
    
    datasets.append({
        "name"      : "wzp6_gammae_eZ_Zee_ecm240",
        "datadir"   : "%s/wzp6_gammae_eZ_Zee_ecm240" % baseDir,
        "xsec"      : 0.05198
    })
  
    
    # gamma-gamma backgrounds
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
    
    datasets.append({
        "name"      : "wzp6_gaga_ee_60_ecm240",
        "datadir"   : "%s/wzp6_gaga_ee_60_ecm240" % baseDir,
        "xsec"      : 0.873
    })

    return datasets