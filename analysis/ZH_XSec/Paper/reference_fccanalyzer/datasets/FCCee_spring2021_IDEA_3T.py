
import ROOT # switch to hex colors
import copy
import fnmatch

# http://fcc-physics-events.web.cern.ch/fcc-physics-events/FCCee/spring2021/Delphesevents_IDEA.php

def getDatasets(filt=None):

    datasets = []
    baseDir = "/eos/experiment/fcc/ee/generation/DelphesEvents/spring2021/IDEA_3T/"


    ## signal samples
    datasets.append({
        "name"      : "wzp6_ee_mumuH_ecm240_3T",
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
        "name"      : "wzp6_ee_mumuH_mH-higher-50MeV_ecm240	",
        "datadir"   : "%s/wzp6_ee_mumuH_mH-higher-50MeV_ecm240	" % baseDir,
        "xsec"      : 0.0067488
    })
    
    datasets.append({
        "name"      : "wzp6_ee_mumuH_mH-higher-100MeV_ecm240",
        "datadir"   : "%s/wzp6_ee_mumuH_mH-higher-100MeV_ecm240" % baseDir,
        "xsec"      : 0.0067393
    })
    
    


    if filt == None: return datasets
    else: return [dataset for dataset in datasets if fnmatch.fnmatch(dataset['name'], filt)]

    
    
