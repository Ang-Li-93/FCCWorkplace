
import sys, os, glob, shutil, json, math, re, random, time
import ROOT

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../python")
import loader
import functions
import datasets as ds


if __name__ == "__main__":

    outDir = "/eos/user/l/lia/FCCee/mumu_Combine"
    procs = []
    
    procs.append("wzp6_ee_mumuH_ecm240")
    #procs.append("wzp6_ee_mumuH_ecm240_reweighted")
    #procs.append("wzp6_ee_mumuH_mH-lower-50MeV_ecm240")
    #procs.append("wzp6_ee_mumuH_mH-lower-100MeV_ecm240")
    #procs.append("wzp6_ee_mumuH_mH-higher-100MeV_ecm240")
    #procs.append("wzp6_ee_mumuH_mH-higher-50MeV_ecm240")
    #
    #procs.append("wzp6_ee_mumuH_noISR_ecm240")
    #procs.append("wzp6_ee_mumuH_ISRnoRecoil_ecm240")
    #procs.append("wzp6_noBES_ee_mumuH_ecm240")
    #procs.append("wzp6_ee_mumuH_noFSR_ecm240")
    #
    #procs.append("wzp6_ee_mumuH_BES-higher-6pc_ecm240")
    #procs.append("wzp6_ee_mumuH_BES-lower-6pc_ecm240")
    #procs.append("wzp6_ee_mumuH_BES-higher-1pc_ecm240")
    #procs.append("wzp6_ee_mumuH_BES-lower-1pc_ecm240")
    #
    #procs.append("wzp6_ee_tautauH_ecm240")
    #procs.append("wzp6_ee_eeH_ecm240")
    #procs.append("wzp6_ee_nunuH_ecm240")
    #procs.append("wzp6_ee_qqH_ecm240")
    #
    #
    #procs.append("p8_ee_WW_mumu_ecm240")
    #procs.append("p8_ee_ZZ_ecm240")
    #procs.append("p8_ee_ZZ_Zll_ecm240")
    #
    #procs.append("p8_ee_Zll_ecm240")
    #
    #
    #procs.append("wzp6_egamma_eZ_Zmumu_ecm240")
    #procs.append("wzp6_gammae_eZ_Zmumu_ecm240")
    #procs.append("wzp6_gaga_mumu_60_ecm240")
    #procs.append("wzp6_gaga_tautau_60_ecm240")
    #
    ##procs.append("p8_noBES_ee_ZZ_ecm240")
    ##procs.append("p8_ee_WW_ecm240")
    ##procs.append("p8_noBES_ee_WW_ecm240")
    ##procs.append("p8_ee_Zqq_ecm240") # empty
    
    
    
    # define cuts
    cuts = {}
    cuts["sel0"] = "true"
    cuts["sel1"] = cuts["sel0"] + " && zed_leptonic_m.size() == 1 && zed_leptonic_charge[0] == 0"
    cuts["sel2"] = cuts["sel1"] + " && zed_leptonic_m[0] > 86 &&  zed_leptonic_m[0] < 96"
    cuts["sel3"] = cuts["sel2"] + " && zed_leptonic_pt[0] > 20 && zed_leptonic_pt[0] < 70"
    cuts["sel4"] = cuts["sel3"] + " && cosTheta_miss[0] < 0.98"
    cuts["sel5"] = cuts["sel4"] + " && zed_leptonic_recoil_m[0] < 140 && zed_leptonic_recoil_m[0] > 120"
    cuts["sel6"] = "zed_leptonic_m_MC.size() == 1 && zed_leptonic_charge_MC[0] == 0 && zed_leptonic_m_MC[0] > 86 &&  zed_leptonic_m_MC[0] < 96 && zed_leptonic_pt_MC[0] > 20 && zed_leptonic_pt_MC[0] < 70 && cosTheta_miss[0] < 0.98 && zed_leptonic_recoil_m_MC[0] < 140 && zed_leptonic_recoil_m_MC[0] > 120"
    # define output histograms
    hists = {}
    hists["selected_muons_pt"]               = {"name": "selected_muons_pt", "title": "", "bin": 20000, "xmin": 0, "xmax": 200 }
    hists["selected_muons_pt_muscaleup"]        = {"name": "selected_muons_pt_muscaleup", "title": "", "bin": 20000, "xmin": 0, "xmax": 200 }
    hists["selected_muons_pt_muscaledw"]        = {"name": "selected_muons_pt_muscaledw", "title": "", "bin": 20000, "xmin": 0, "xmax": 200 }
    
    hists["selected_muons_no"]                  = {"name": "selected_muons_no", "title": "", "bin": 10, "xmin": 0, "xmax": 10 }
    
    hists["zed_leptonic_m"]                     = {"name": "zed_leptonic_m", "title": "", "bin":300000,"xmin":00,"xmax":300 }
    hists["zed_leptonic_m_muscaleup"]           = {"name": "zed_leptonic_m_muscaleup", "title": "", "bin":300000,"xmin":00,"xmax":300 }
    hists["zed_leptonic_m_muscaledw"]           = {"name": "zed_leptonic_m_muscaledw", "title": "", "bin":300000,"xmin":00,"xmax":300 }
    
    hists["zed_leptonic_no"]                    = {"name": "zed_leptonic_no", "title": "", "bin":10,"xmin":0,"xmax":10 }
    hists["zed_leptonic_no_muscaleup"]          = {"name": "zed_leptonic_no_muscaleup", "title": "", "bin":10,"xmin":0,"xmax":10 }
    hists["zed_leptonic_no_muscaledw"]          = {"name": "zed_leptonic_no_muscaledw", "title": "", "bin":10,"xmin":0,"xmax":10 }
    
    hists["zed_leptonic_pt"]                    = {"name": "zed_leptonic_pt", "title": "", "bin":200000,"xmin":0,"xmax":200 }
    hists["zed_leptonic_pt_muscaleup"]          = {"name": "zed_leptonic_pt_muscaleup", "title": "", "bin":200000,"xmin":0,"xmax":200 }
    hists["zed_leptonic_pt_muscaledw"]          = {"name": "zed_leptonic_pt_muscaledw", "title": "", "bin":200000,"xmin":0,"xmax":200 }
    
    hists["zed_leptonic_recoil_m"]              = {"name": "zed_leptonic_recoil_m", "title": "", "bin":200000,"xmin":0,"xmax":200 }
    hists["zed_leptonic_recoil_m_muscaleup"]    = {"name": "zed_leptonic_recoil_m_muscaleup", "title": "", "bin":200000,"xmin":0,"xmax":200 }
    hists["zed_leptonic_recoil_m_muscaledw"]    = {"name": "zed_leptonic_recoil_m_muscaledw", "title": "", "bin":200000,"xmin":0,"xmax":200 }
    hists["zed_leptonic_recoil_m_sqrtsup"]      = {"name": "zed_leptonic_recoil_m_sqrtsup", "title": "", "bin":200000,"xmin":0,"xmax":200 }
    hists["zed_leptonic_recoil_m_sqrtsdw"]      = {"name": "zed_leptonic_recoil_m_sqrtsdw", "title": "", "bin":200000,"xmin":0,"xmax":200 }
    
    hists["cosTheta_miss"]                      = {"name": "cosTheta_miss", "title": "", "bin":100000,"xmin":-1,"xmax":1 }
    #hists["sf_kkmcp8_wzp6"]                     = {"name": "sf_kkmcp8_wzp6", "title": "", "bin":4000,"xmin":0.8,"xmax":1.2 }
    
 
    hists["zed_leptonic_m_MC"]                     = {"name": "zed_leptonic_m_MC", "title": "", "bin":300000,"xmin":00,"xmax":300 }
    hists["zed_leptonic_recoil_m_MC"]              = {"name": "zed_leptonic_recoil_m_MC", "title": "", "bin":200000,"xmin":0,"xmax":200 }

    # prepare the RDFs and histograms
    graphs = {}
    histsToRun = []
    for proc in procs:
    
        graphs[proc] = []
        treeFile = "%s/%s_tree.root" % (outDir, proc)
        
        for cut in cuts:
        
            rdf = ROOT.RDataFrame("events", treeFile)
            rdf = rdf.Filter(cuts[cut])
            for h in hists:
            
                model = ROOT.RDF.TH1DModel("%s_%s" % (h, cut), ";{};".format(hists[h]["title"]), hists[h]["bin"], hists[h]["xmin"], hists[h]["xmax"])
                #histo = rdf.Histo1D(model, hists[h]["name"],'sf_kkmcp8_wzp6')
                histo = rdf.Histo1D(model, hists[h]["name"])
                graphs[proc].append(histo)
                histsToRun.append(histo)
  
    # execute the RDFs
    start_time = time.time()
    print("Executing the RDF")
    ROOT.RDF.RunGraphs(histsToRun)
    end_time = time.time()
    print("Finished in %d seconds" % (end_time-start_time))
    
    # save histograms (1 file per process, holding all the cuts)
    for proc in procs:
    
        fOutName = "%s/%s_hists.root" % (outDir, proc)
        fOut = ROOT.TFile(fOutName, "RECREATE")
        for g in graphs[proc]: g.Write()
        fOut.Close()
    
          
