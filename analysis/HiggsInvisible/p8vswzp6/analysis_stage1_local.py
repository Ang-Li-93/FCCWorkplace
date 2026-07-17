#fccanalysis run recoiljj.py --output recoiljj-new.root --files-list ../data/reco-cld/hinvjj.2002_20000/hinvjj.2002_20000_*.rec_edm4hep.root  2>&1|tee log-recoiljj-new
#fccanalysis run recoiljj.py --output recoiljj-old.root --files-list ../data/reco-cld/hinvjj.2002_20000-save/*.rec.root  2>&1|tee log-recoiljj-old

import ROOT
code = open ('analysis/HiggsInvisible/recoil.cc').read()
ROOT.gInterpreter.Declare(code)

outputDir   = "outputs_HInvjj/stage1/test"

class RDFanalysis:
    def analysers (df):
        df2 = (
            df
            #.Alias("_MCParticles_daughters", "MCParticles#1")
            #.Define("eventNumber", "EventHeader[0].eventNumber")
            .Define("mcp1", "MCParticle::sel_genStatus(1)(MCParticles)")
            .Define("mcp2", "MCParticle::sel_pt(5)(mcp1)")
            .Define('mcisrgam', 'sel_isrgam()(MCParticles, _MCParticles_daughters)')
            .Define('mcisrgamz1', 'calc_mcisrgamz1(mcisrgam)')
            .Define('mcisrgamz2', 'calc_mcisrgamz2(mcisrgam)')
            .Define('x1', '1 - mcisrgamz1/120.')
            .Define('x2', '1 + mcisrgamz2/120.')
            .Define('beta', '(x1-x2)/(x1+x2)')
            .Define('truesqrts0', 'calc_truesqrts()(MCParticles)')
            .Define('truesqrts', '240.*sqrt(x1*x2)')

            .Define("jet_pt", "ReconstructedParticle::get_pt(RefinedVertexJets)")
            .Define("z", "resonanceBuilder(91)(RefinedVertexJets)")
            .Define("z_pt", "ReconstructedParticle::get_pt(z)")
            .Define("z_m", "ReconstructedParticle::get_mass(z)")
            .Define('h', 'recoilBuilder()(240, z)')
            .Define("h_pt", "ReconstructedParticle::get_pt(h)")
            .Define("h_m", "ReconstructedParticle::get_mass(h)")
            .Define('ht', 'recoilBuilder()(truesqrts, z)')
            .Define("ht_pt", "ReconstructedParticle::get_pt(ht)")
            .Define("ht_m", "ReconstructedParticle::get_mass(ht)")
            )
        return df2


    def output():
        return [
            #'eventNumber',
            'mcisrgam',
            'mcisrgamz1',
            'mcisrgamz2',
            'x1',
            'x2',
            'beta',
            'truesqrts0',
            'truesqrts',

            'jet_pt',
            'z',
            'z_pt',
            'z_m',
            'h',
            'h_pt',
            'h_m',
            'ht',
            'ht_pt',
            'ht_m',
            ]
