
# http://fcc-physics-events.web.cern.ch/fcc-physics-events/FCCee/spring2021/Delphesevents_IDEA.php

def get_datasets(baseDir = ""):

    datasets = []
    subDir = "/spring2021/IDEA/"
    baseDir = "%s/%s" % (baseDir, subDir)

    datasets.append({
        "name"      : "p8_ee_Zee_ecm91",
        "datadir"   : "%s/p8_ee_Zee_ecm91" % baseDir,
        "xsec"      : 1462.09
    })
    
    datasets.append({
        "name"      : "p8_ee_Zmumu_ecm91",
        "datadir"   : "%s/p8_ee_Zmumu_ecm91" % baseDir,
        "xsec"      : 1462.08
    })
    
    datasets.append({
        "name"      : "p8_ee_Ztautau_ecm91",
        "datadir"   : "%s/p8_ee_Ztautau_ecm91" % baseDir,
        "xsec"      : 1476.58
    })
    
    
    
    datasets.append({
        "name"      : "p8_ee_Zuds_ecm91",
        "datadir"   : "%s/p8_ee_Zuds_ecm91" % baseDir,
        "xsec"      : 18616.5
    })
    
    datasets.append({
        "name"      : "p8_ee_Zcc_ecm91",
        "datadir"   : "%s/p8_ee_Zcc_ecm91" % baseDir,
        "xsec"      : 5215.46
    })
    
    datasets.append({
        "name"      : "p8_ee_Zbb_ecm91",
        "datadir"   : "%s/p8_ee_Zbb_ecm91" % baseDir,
        "xsec"      : 6645.46
    })
    
    datasets.append({
        "name"      : "wzp6_gaga_mumu_5_ecm91p2",
        "datadir"   : "/eos/cms/store/user/jaeyserm/fccee/DelphesEvents/winter2023/IDEA//wzp6_gaga_mumu_5_ecm91p2/",
        "xsec"      : 5.3393669E+02
    })
    
    datasets.append({
        "name"      : "wzp6_ee_mumu_ecm91p2",
        "datadir"   : "/eos/cms/store/user/jaeyserm/fccee/DelphesEvents/winter2023/IDEA//wzp6_ee_mumu_ecm91p2/",
        "xsec"      : 1462.09
    })
    
    datasets.append({
        "name"      : "wzp6_ee_qq_ecm91p2",
        "datadir"   : "/eos/cms/store/user/jaeyserm/fccee/DelphesEvents/winter2023/IDEA//wzp6_ee_qq_ecm91p2/",
        "xsec"      : 1462.09
    })
    
    return datasets