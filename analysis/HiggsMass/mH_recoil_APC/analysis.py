import sys
import ROOT

print ("Load cxx analyzers ... ",)
ROOT.gSystem.Load("libedm4hep")
ROOT.gSystem.Load("libpodio")
ROOT.gSystem.Load("libFCCAnalyses")
ROOT.gSystem.Load("libFCCAnalysesHiggs")
ROOT.gErrorIgnoreLevel = ROOT.kFatal
_edm  = ROOT.edm4hep.ReconstructedParticleData()
_pod  = ROOT.podio.ObjectID()
_fcc  = ROOT.dummyLoader
_higgs  = ROOT.dummyLoaderHiggs
print ('edm4hep  ',_edm)
print ('podio    ',_pod)
print ('fccana   ',_fcc)
print ('higgs   ',_higgs)

class analysis():

    #__________________________________________________________
    def __init__(self, inputlist, outname, ncpu):
        self.outname = outname
        if ".root" not in outname:
            self.outname+=".root"

        ROOT.ROOT.EnableImplicitMT(ncpu)

        self.df = ROOT.RDataFrame("events", inputlist)
        print (" done")
    #__________________________________________________________
    def run(self):
        df2 = (self.df
               # retrieve the muons (isolated and non isolated) :
               #.Define("b_TightSelectedPandoraPFOs",  "ReconstructedParticle::BoostAngle( -0.01485 ) ( TightSelectedPandoraPFOs )")
               .Define("Allmuons",  "ReconstructedParticle::sel_type(13, true) ( TightSelectedPandoraPFOs )" )
               #.Define("muons",  "ReconstructedParticle::sel_type(13, true) ( TightSelectedPandoraPFOs )" )
               # The Delphes "Muons" are isolated muons. Hence one should, out of the "Allmuons" particles
               # just retrieved, extract the subset that pass the same isolation cut as applied in Delphes :
               .Define("isolation",  "ReconstructedParticle::Isolation( Allmuons, TightSelectedPandoraPFOs  ) ")
               .Define("muons",  "ReconstructedParticle::sel_isol(0.25) ( Allmuons, isolation ) ")
               # The "muons" that we have just defined are equivalent to the "muons" in the Delphes-like analysis.py
               
               ## define an alias for muon indeix collection
               #.Alias("Muon0", "Muon#0.index")
               ## define an alias for muon indeix collection
               #.Alias("AllMuon0", "AllMuon#0.index")
               ## define the muon collection
               #.Define("muons",  "ReconstructedParticle::get(AllMuon0, ReconstructedParticles)")
               #.Define("muons",  "ReconstructedParticle::get(AllMuons, ReconstructedParticles)")
               #.Define("muons",  "ReconstructedParticle::get(Muon0, ReconstructedParticles)")
               ## get cosTheta miss
               .Define("MissingET", "ReconstructedParticle::Merger( TightSelectedPandoraPFOs ) " )
               .Define('missingET_costheta', 'APCHiggsTools::get_cosTheta(MissingET)')
               ##select muons on pT
               ##.Define("selected_muons", "ReconstructedParticle::sel_pt(10.)(muons)")
              
               #muon quality check at least one muon plus and one muon minus
               .Define("selected_muons", "APCHiggsTools::muon_quality_check(muons)")
							 #select muons +
							 .Define("selected_muons_plus", "ReconstructedParticle::sel_charge(1.0,false)(selected_muons)")
							 #select muons -
							 .Define("selected_muons_minus", "ReconstructedParticle::sel_charge(-1.0,false)(selected_muons)")
							 #muons + numbers
							 .Define("selected_muons_plus_n", "ReconstructedParticle::get_n(selected_muons_plus)")
							 #muons - numbers
							 .Define("selected_muons_minus_n", "ReconstructedParticle::get_n(selected_muons_minus)")
							 #muons numbers
							 .Define("selected_muons_n", "ReconstructedParticle::get_n(selected_muons)")
							 # create branch with muon transverse momentum
               .Define("selected_muons_pt", "ReconstructedParticle::get_pt(selected_muons)") 
               # create branch with muon rapidity
               .Define("selected_muons_y",  "ReconstructedParticle::get_y(selected_muons)") 
               # create branch with muon total momentum
               .Define("selected_muons_p",     "ReconstructedParticle::get_p(selected_muons)")
               # create branch with muon energy 
               .Define("selected_muons_e",     "ReconstructedParticle::get_e(selected_muons)")
               # create branch with muon mass
               .Define("selected_muons_m",     "ReconstructedParticle::get_mass(selected_muons)")
               # create branch with muon costheta
               .Define("selected_muons_costheta",  "APCHiggsTools::get_cosTheta(selected_muons)")
               # find zed candidates from  di-muon resonances  
               .Define("zed_leptonic",         "APCHiggsTools::resonanceZBuilder(91)(selected_muons)")      
               # write branch with zed mass
               .Define("zed_leptonic_m",       "ReconstructedParticle::get_mass(zed_leptonic)")
							 # write branch with zed number
							 .Define("zed_leptonic_n",       "ReconstructedParticle::get_n(zed_leptonic)")
							 # write branch with zed charge
							 .Define("zed_leptonic_charge",   "ReconstructedParticle::get_charge(zed_leptonic)")
               # write branch with zed transverse momenta
               .Define("zed_leptonic_pt",      "ReconstructedParticle::get_pt(zed_leptonic)")
               # write branch with zed rapidity
               .Define("zed_leptonic_y",      "ReconstructedParticle::get_y(zed_leptonic)")
               # write branch with zed total momentum
               .Define("zed_leptonic_p",      "ReconstructedParticle::get_p(zed_leptonic)")
               # write branch with zed energy
               .Define("zed_leptonic_e",      "ReconstructedParticle::get_e(zed_leptonic)")
               # write branch with zed costheta
               .Define("zed_leptonic_costheta",  "APCHiggsTools::get_cosTheta(zed_leptonic)")
               # calculate recoil of zed_leptonic
               .Define("zed_leptonic_recoil",  "ReconstructedParticle::recoilBuilder(240)(zed_leptonic)")
               # write branch with recoil mass
               .Define("zed_leptonic_recoil_m","ReconstructedParticle::get_mass(zed_leptonic_recoil)") 
               .Define("zed_leptonic_recoil_n","ReconstructedParticle::get_n(zed_leptonic_recoil)")
               .Define("zed_leptonic_recoil_charge","ReconstructedParticle::get_charge(zed_leptonic_recoil)")
               .Define("zed_leptonic_recoil_pt","ReconstructedParticle::get_pt(zed_leptonic_recoil)")
               .Define("zed_leptonic_recoil_y","ReconstructedParticle::get_y(zed_leptonic_recoil)")
               .Define("zed_leptonic_recoil_p","ReconstructedParticle::get_p(zed_leptonic_recoil)")
               .Define("zed_leptonic_recoil_e","ReconstructedParticle::get_e(zed_leptonic_recoil)")
               .Define("zed_leptonic_recoil_costheta","APCHiggsTools::get_cosTheta(zed_leptonic_recoil)")
               # Recoil mass with the MC muons kinematics
               #.Alias("MCRecoAssociations0", "MCRecoAssociations#0.index")
               #.Alias("MCRecoAssociations1", "MCRecoAssociations#1.index")
               #.Define("zed_leptonic_MC",   "APCHiggsTools::resonanceZBuilder2(91, true)(selected_muons, MCRecoAssociations0,MCRecoAssociations1,ReconstructedParticles,Particle)")
 							 ## write branch with zed number
							 #.Define("zed_leptonic_MC_n",       "ReconstructedParticle::get_n(zed_leptonic_MC)")
							 ## write branch with zed charge
							 #.Define("zed_leptonic_MC_charge",   "ReconstructedParticle::get_charge(zed_leptonic_MC)")
               ## write branch with zed transverse momenta
               #.Define("zed_leptonic_MC_pt",      "ReconstructedParticle::get_pt(zed_leptonic_MC)")
               ## write branch with zed rapidity
               #.Define("zed_leptonic_MC_y",      "ReconstructedParticle::get_y(zed_leptonic_MC)")
               ## write branch with zed total momentum
               #.Define("zed_leptonic_MC_p",      "ReconstructedParticle::get_p(zed_leptonic_MC)")
               ## write branch with zed energy
               #.Define("zed_leptonic_MC_e",      "ReconstructedParticle::get_e(zed_leptonic_MC)")
               ## write branch with zed costheta
               #.Define("zed_leptonic_MC_costheta",  "APCHiggsTools::get_cosTheta(zed_leptonic_MC)")
               # 
               #.Define("zed_leptonic_MC_mass",    "ReconstructedParticle::get_mass(zed_leptonic_MC)" )
               #.Define("zed_leptonic_recoil_MC",  "ReconstructedParticle::recoilBuilder(240)( zed_leptonic_MC )")
               #.Define("zed_leptonic_recoil_MC_mass",   "ReconstructedParticle::get_mass( zed_leptonic_recoil_MC )")
               #
               ##.Define("stable",  "MCParticle::sel_genStatus(1) (Particle)")
               #.Define("stable",  "MCParticle::sel_genStatus(2) (Particle)")
               #.Define("theGenLevelMuminus",  "MCParticle::sel_pdgID( 13, false) (stable)")
               #.Define("theGenLevelMuplus",  "MCParticle::sel_pdgID( -13, false) (stable)")
               #.Define("theGenLevelHiggs", "MCParticle::sel_pdgID( 25, false) (stable)")
               #.Define("theGenLevelMuminus_tlv", "MCParticle::get_tlv(theGenLevelMuminus) ")
               #.Define("theGenLevelMuplus_tlv", "MCParticle::get_tlv(theGenLevelMuplus) ")
               #.Define("theGenLevelHiggs_tlv", "MCParticle::get_tlv(theGenLevelHiggs) ")
               #.Define("gen_pt_mumu", "return ( theGenLevelMuminus_tlv[0] + theGenLevelMuplus_tlv[0]).Pt() ;" )
               #.Define("gen_mass_mumu", "return ( theGenLevelMuminus_tlv[0] + theGenLevelMuplus_tlv[0]).M() ;" )
               #.Define("gen_pt_ZH", "return ( theGenLevelMuminus_tlv[0] + theGenLevelMuplus_tlv[0] + theGenLevelHiggs_tlv[0] ).Pt() ;" )
               #.Define("gen_mass_ZH", "return ( theGenLevelMuminus_tlv[0] + theGenLevelMuplus_tlv[0] + theGenLevelHiggs_tlv[0] ).M() ;" )
               #.Define("sf_kkmcp8_wzp6", "APCHiggsTools::Reweighting_wzp_kkmc(gen_pt_ZH,gen_mass_ZH)")
               #.Define("sf_kkmcp8_wzp6", "APCHiggsTools::Reweighting_wzp_kkmc(gen_pt_mumu,gen_mass_mumu)")
               #.Define("gen_pt_mumu", "if ( theGenLevelMuminus_tlv.size() == 1 && theGenLevelMuplus_tlv.size() == 1) return  (theGenLevelMuminus_tlv[0] + theGenLevelMuplus_tlv[0]).Pt(); else return -999. ")
               #.Define("gen_mass_mumu", "if ( theGenLevelMuminus_tlv.size() == 1 && theGenLevelMuplus_tlv.size() == 1) return ( theGenLevelMuminus_tlv[0] + theGenLevelMuplus_tlv[0]).M(); else return -999. ")
            
        )

        


        # select branches for output file
        branchList = ROOT.vector('string')()
        for branchName in [
                "selected_muons_costheta",
                "selected_muons_pt",
                "selected_muons_y",
                "selected_muons_p",
                "selected_muons_e",
								"selected_muons_m",
                "selected_muons_n",
								"selected_muons_plus_n",
								"selected_muons_minus_n",
                "zed_leptonic_pt",
                "zed_leptonic_y",
                "zed_leptonic_p",
                "zed_leptonic_e",
                "zed_leptonic_m",
								"zed_leptonic_n",
								"zed_leptonic_costheta",
                "zed_leptonic_charge",
                "zed_leptonic_recoil_m",
                "zed_leptonic_recoil_y",
                "zed_leptonic_recoil_p",
                "zed_leptonic_recoil_e",
                "zed_leptonic_recoil_n",
                "zed_leptonic_recoil_costheta",
                "zed_leptonic_recoil_charge",
                "zed_leptonic_recoil_pt",
                "missingET_costheta"
                #"zed_leptonic_MC_mass",
                #"zed_leptonic_MC_pt",
                #"zed_leptonic_MC_y",
                #"zed_leptonic_MC_p",
                #"zed_leptonic_MC_e",
								#"zed_leptonic_MC_n",
								#"zed_leptonic_MC_costheta",
                #"zed_leptonic_MC_charge",
                #"zed_leptonic_recoil_MC_mass",
                #"gen_pt_mumu",
                #"gen_mass_mumu",
                #"gen_pt_ZH",
                #"gen_mass_ZH",
                #"sf_kkmcp8_wzp6"
            ]:
            branchList.push_back(branchName)
        df2.Snapshot("events", self.outname, branchList)

# example call for standalone file
# python examples/FCCee/higgs/mH-recoil/mumu/analysis.py /eos/experiment/fcc/ee/generation/DelphesEvents/fcc_tmp/p8_ee_ZH_ecm240/events_058720051.root
if __name__ == "__main__":

    if len(sys.argv)==1:
        print ("usage:")
        print ("python ",sys.argv[0]," file.root")
        sys.exit(3)
    infile = sys.argv[1]
    #outDir = sys.argv[0].replace(sys.argv[0].split('/')[0],'outputs/FCCee').replace('analysis.py','')+'/'
    outDir = "/eos/home-l/lia/FCCee/mumu/"
    import os
    os.system("mkdir -p {}".format(outDir))
    outfile = outDir+infile.split('/')[-1]
    ncpus = 10
    analysis = analysis(infile, outfile, ncpus)
    analysis.run()

    tf = ROOT.TFile(infile)
    entries = tf.events.GetEntries()
    p = ROOT.TParameter(int)( "eventsProcessed", entries)
    outf=ROOT.TFile(outfile,"UPDATE")
    p.Write()
