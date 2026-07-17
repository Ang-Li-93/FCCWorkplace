# in tuple
#fccanalysis run ../hinv-fullsim-ana.py --output hinv-ee.root --files-list ../../data/reco-cld/hinvee.2001_20000/hinvee.2001_20000_*.rec_edm4hep.root  2>&1|tee log-hinv-ee
#fccanalysis run ../hinv-fullsim-ana.py --output hinv-mm.root --files-list ../../data/reco-cld/hinvmm.2003_20000/hinvmm.2003_20000_*.rec_edm4hep.root  2>&1|tee log-hinv-mm
#fccanalysis run ../hinv-fullsim-ana.py --output hinv-qq.root --files-list ../../data/reco-cld/hinvjj.2002_20000/hinvjj.2002_20000_*.rec_edm4hep.root  2>&1|tee log-hinv-qq

#fccanalysis run ../hinv-fullsim-ana.py --output zh_nneenn.root --files-list ../../data/reco-cld/zh_nneenn.2011_18000/zh_nneenn.2011_18000_*.rec_edm4hep.root  2>&1|tee log-zh_nneenn
#fccanalysis run ../hinv-fullsim-ana.py --output zh_nnmmnn.root --files-list ../../data/reco-cld/zh_nnmmnn.2013_18000/zh_nnmmnn.2013_18000_*.rec_edm4hep.root  2>&1|tee log-zh_nnmmnn
#fccanalysis run ../hinv-fullsim-ana.py --output zh_nnqqnn.root --files-list ../../data/reco-cld/zh_nnqqnn.2012_18000/zh_nnqqnn.2012_18000_*.rec_edm4hep.root  2>&1|tee log-zh_nnqqnn
#fccanalysis run ../hinv-fullsim-ana.py --output zh_nnqq.root --files-list ../../data/reco-cld/zh_nnqq.2014_18000/zh_nnqq.2014_18000_*.rec_edm4hep.root  2>&1|tee log-zh_nnqq

#fccanalysis run ../hinv-fullsim-ana.py --output zz_eenn.root --files-list ../../data/reco-cld/zz_eenn.2021_18000/zz_eenn.2021_18000_*.rec_edm4hep.root  2>&1|tee log-zz_eenn
#fccanalysis run ../hinv-fullsim-ana.py --output zz_mmnn.root --files-list ../../data/reco-cld/zz_mmnn.2023_18000/zz_mmnn.2023_18000_*.rec_edm4hep.root  2>&1|tee log-zz_mmnn
#fccanalysis run ../hinv-fullsim-ana.py --output zz_qqnn.root --files-list ../../data/reco-cld/zz_qqnn.2022_18000/zz_qqnn.2022_18000_*.rec_edm4hep.root  2>&1|tee log-zz_qqnn
#fccanalysis run ../hinv-fullsim-ana.py --output zz_eeqq.root --files-list ../../data/reco-cld/zz_eeqq.2024_18000/zz_eeqq.2024_18000_*.rec_edm4hep.root  2>&1|tee log-zz_eeqq
#fccanalysis run ../hinv-fullsim-ana.py --output zz_mmqq.root --files-list ../../data/reco-cld/zz_mmqq.2026_18000/zz_mmqq.2026_18000_*.rec_edm4hep.root  2>&1|tee log-zz_mmqq
#fccanalysis run ../hinv-fullsim-ana.py --output zz_qqqq.root --files-list ../../data/reco-cld/zz_qqqq.2025_18000/zz_qqqq.2025_18000_*.rec_edm4hep.root  2>&1|tee log-zz_qqqq


import sys
import os
import ROOT
ROOT.gROOT.SetBatch (True)
mydir = "/afs/cern.ch/work/l/lia/private/FCC/FCCWorkplace/analysis/HiggsInvisible/"
#mydir = os.path.dirname (sys.argv[2])
code = open (os.path.join (mydir, 'recoil.cc')).read()
ROOT.gInterpreter.Declare(code)

def writehists (filename, hists):
    if not hists: return
    fout = ROOT.TFile.Open (filename, 'UPDATE')
    for h in hists:
        h.Write()
    fout.Close()

    pdfname = os.path.splitext (filename)[0] + '.pdf'
    c = ROOT.TCanvas('c')
    c.Print (pdfname + '[')
    for h in hists:
        h.Draw()
        c.Print (pdfname, 'Title: ' + h.GetName())
    c.Print (pdfname + ']', 'Title: ' + hists[-1].GetName())
    return


def patchdf (df):
    if not hasattr (df.__class__.Snapshot, '__name__'):
        oldsnap = df.__class__.Snapshot
        def mysnap (self, treename, filename, *args):
            ret = oldsnap (self, treename, filename, *args)
            writehists (filename, self.hists)
            self.ee.Report().Print()
            self.mm.Report().Print()
            self.qq.Report().Print()
            return ret
        df.__class__.Snapshot = mysnap
    return


def addhist (df, h):
    if not hasattr (df, 'hists'):
        df.hists = []
    df.hists.append (h)
    return
def h1 (df, name, nx, xlo, xhi, expr = None, title = None):
    if not expr: expr = name
    if not title: title = name
    h = df.Histo1D (ROOT.RDF.TH1DModel (name, title, nx, xlo, xhi), expr)
    addhist (df, h)
    return


class Histmaker:
    def __init__ (self, df, final, prefix = ''):
        self.df = df
        self.prefix = prefix
        if not hasattr (final, 'hists'):
            final.hists = []
        self.hists = final.hists
        return

    def h1 (self, name, nx, xlo, xhi, expr = None, title = None):
        if not expr: expr = name
        if not title: title = name
        h = self.df.Histo1D (ROOT.RDF.TH1DModel (self.prefix + name, title, nx, xlo, xhi), expr)
        self.hists.append (h)
        return


    def kin (self, name):
        self.h1 (name + '_p', 80, 0, 200)
        self.h1 (name + '_pt', 80, 0, 200)
        self.h1 (name + '_m', 80, 0, 200)
        self.h1 (name + '_mhigh', 75, 0, 300, expr = name + '_m')
        self.h1 (name + '_theta', 50, 0, 3.5)
        self.h1 (name + '_phi', 50, -3.5, 3.5)
        return


class RDFanalysis:
    @staticmethod
    def hists (hm):
        hm.h1 ('ele_iso', 100, 0, 100)
        hm.h1 ('muo_iso', 100, 0, 100)
        hm.h1 ('ele_iso2', 100, 0, 10, expr = 'ele_iso')
        hm.h1 ('muo_iso2', 100, 0, 10, expr = 'muo_iso')
        hm.h1 ('n_eles', 10, 0, 10)
        hm.h1 ('n_muos', 10, 0, 10)
        hm.h1 ('n_gams', 10, 0, 10)
        hm.h1 ('n_leps', 10, 0, 10)
        hm.h1 ('n_paired_eles', 10, 0, 10)
        hm.h1 ('n_paired_muos', 10, 0, 10)
        hm.h1 ('n_paired_leps', 10, 0, 10)

        hm.kin ('all_eles')
        hm.kin ('sel_eles')
        hm.h1 ('sel_eles_nclust', 10, 0, 10)
        hm.kin ('all_muos')
        hm.kin ('sel_muos')

        hm.kin ('all_gams')
        hm.h1 ('all_gams_angle', 100, 0, 2)
        hm.h1 ('all_gams_angle2', 100, 0, 0.1, expr='all_gams_angle')
        hm.h1 ('all_gams_dist', 100, 0, 100)
        hm.h1 ('all_gams_nclust', 10, 0, 10)

        hm.kin ('ll0')
        hm.kin ('ll')
        hm.kin ('vis')
        hm.kin ('mcvis')
        hm.kin ('llrecoil')
        hm.kin ('visrecoil')
        return


    def analysers (df):
        prefilt = (
            df
            .Define('eventNumber', 'EventHeader[0].eventNumber')

            .Define('mcp1', 'MCParticle::sel_genStatus(1)(MCParticles)')
            .Define("mcp2", 'boost(0.030, mcp1)')
            .Define('mcvis', 'sum(mcp2)')
            .Define('mcvis_pt', 'mcvis.Pt()')
            .Define('mcvis_p', 'mcvis.P()')
            .Define('mcvis_m', 'mcvis.M()')
            .Define('mcvis_theta', 'mcvis.Theta()')
            .Define('mcvis_phi', 'mcvis.Phi()')
            .Define('mcvisraw', 'sum(mcp1)')
            .Define('mcvisraw_pt', 'mcvisraw.Pt()')
            .Define('mcvisraw_p', 'mcvisraw.P()')
            .Define('mcvisraw_m', 'mcvisraw.M()')
            .Define('mcvisraw_theta', 'mcvisraw.Theta()')
            .Define('mcvisraw_phi', 'mcvisraw.Phi()')

            .Define('BoostedPandoraPFOs', 'boost(0.030, PandoraPFOs)')
            .Alias('TightSelectedPandoraPFOsIndex', 'TightSelectedPandoraPFOs_objIdx.index')
            .Define('TightSelectedPandoraPFOs', 'ReconstructedParticle::get (TightSelectedPandoraPFOsIndex, BoostedPandoraPFOs)')

            .Define('all_eles', 'ReconstructedParticle::sel_absType(11)(TightSelectedPandoraPFOs)')
            .Define('ele_iso', 'coneIsolation()(all_eles, BoostedPandoraPFOs)')
            .Define('all_eles_pt', 'ReconstructedParticle::get_pt(all_eles)')
            .Define('all_eles_p', 'ReconstructedParticle::get_p(all_eles)')
            .Define('all_eles_m', 'ReconstructedParticle::get_mass(all_eles)')
            .Define('all_eles_theta', 'ReconstructedParticle::get_theta(all_eles)')
            .Define('all_eles_phi', 'ReconstructedParticle::get_phi(all_eles)')
            .Define('iso_eles', 'sel_iso (0.5, all_eles, ele_iso)')
            .Define('sel_eles', 'ReconstructedParticle::sel_p(10)(iso_eles)')
            .Define('sel_eles_pt', 'ReconstructedParticle::get_pt(sel_eles)')
            .Define('sel_eles_p', 'ReconstructedParticle::get_p(sel_eles)')
            .Define('sel_eles_m', 'ReconstructedParticle::get_mass(sel_eles)')
            .Define('sel_eles_theta', 'ReconstructedParticle::get_theta(sel_eles)')
            .Define('sel_eles_phi', 'ReconstructedParticle::get_phi(sel_eles)')
            .Define('sel_eles_nclust', 'get_nclust(sel_eles)')

            .Define('all_muos', 'ReconstructedParticle::sel_absType(13)(TightSelectedPandoraPFOs)')
            .Define('muo_iso', 'coneIsolation()(all_muos, BoostedPandoraPFOs)')
            .Define('all_muos_pt', 'ReconstructedParticle::get_pt(all_muos)')
            .Define('all_muos_p', 'ReconstructedParticle::get_p(all_muos)')
            .Define('all_muos_m', 'ReconstructedParticle::get_mass(all_muos)')
            .Define('all_muos_theta', 'ReconstructedParticle::get_theta(all_muos)')
            .Define('all_muos_phi', 'ReconstructedParticle::get_phi(all_muos)')
            .Define('iso_muos', 'sel_iso (0.5, all_muos, muo_iso)')
            .Define('sel_muos', 'ReconstructedParticle::sel_p(10)(iso_muos)')
            .Define('sel_muos_pt', 'ReconstructedParticle::get_pt(sel_muos)')
            .Define('sel_muos_p', 'ReconstructedParticle::get_p(sel_muos)')
            .Define('sel_muos_m', 'ReconstructedParticle::get_mass(sel_muos)')
            .Define('sel_muos_theta', 'ReconstructedParticle::get_theta(sel_muos)')
            .Define('sel_muos_phi', 'ReconstructedParticle::get_phi(sel_muos)')


            .Define('all_gams', 'ReconstructedParticle::sel_absType(22)(TightSelectedPandoraPFOs)')
            .Define('all_gams_pt', 'ReconstructedParticle::get_pt(all_gams)')
            .Define('all_gams_p', 'ReconstructedParticle::get_p(all_gams)')
            .Define('all_gams_m', 'ReconstructedParticle::get_mass(all_gams)')
            .Define('all_gams_theta', 'ReconstructedParticle::get_theta(all_gams)')
            .Define('all_gams_phi', 'ReconstructedParticle::get_phi(all_gams)')
            .Define('all_gams_nclust', 'get_nclust(all_gams)')

            .Define('n_eles', 'sel_eles.size()')
            .Define('n_muos', 'sel_muos.size()')
            .Define('n_gams', 'all_gams.size()')
            .Define('n_leps', 'n_eles+n_muos')
            .Define("paired_eles", "sel_leps(11)(sel_eles)")
            .Define("paired_muos", "sel_leps(13)(sel_muos)")
            .Define('n_paired_eles', 'paired_eles.size()')
            .Define('n_paired_muos', 'paired_muos.size()')
            .Define('paired_leps', 'merge(paired_eles, paired_muos)')
            .Define('n_paired_leps', 'paired_leps.size()')

            .Define('gam_match', 'photonLeptonMatch(all_gams, paired_leps, PandoraClusters)')
            .Define('all_gams_angle', 'get_match_angle(gam_match)')
            .Define('all_gams_dist', 'get_match_dist(gam_match)')
            .Define('paired_leps_fsr', 'addfsr(paired_leps,all_gams,gam_match,0.05)')

            .Define('ll0', 'resonanceBuilder(91)(paired_leps)')
            .Define('ll0_pt', 'ReconstructedParticle::get_pt(ll0)')
            .Define('ll0_p', 'ReconstructedParticle::get_p(ll0)')
            .Define('ll0_m', 'ReconstructedParticle::get_mass(ll0)')
            .Define('ll0_theta', 'ReconstructedParticle::get_theta(ll0)')
            .Define('ll0_phi', 'ReconstructedParticle::get_phi(ll0)')

            .Define('ll', 'resonanceBuilder(91)(paired_leps_fsr)')
            .Define('ll_pt', 'ReconstructedParticle::get_pt(ll)')
            .Define('ll_p', 'ReconstructedParticle::get_p(ll)')
            .Define('ll_m', 'ReconstructedParticle::get_mass(ll)')
            .Define('ll_theta', 'ReconstructedParticle::get_theta(ll)')
            .Define('ll_phi', 'ReconstructedParticle::get_phi(ll)')

            .Define('llrecoil', 'recoilBuilder2()(240, ll)')
            .Define('llrecoil_pt', 'llrecoil.Pt()')
            .Define('llrecoil_p', 'llrecoil.P()')
            .Define('llrecoil_m', 'llrecoil.M()')
            .Define('llrecoil_theta', 'llrecoil.Theta()')
            .Define('llrecoil_phi', 'llrecoil.Phi()')

            .Define('visraw', 'sum(PandoraPFOs)')
            .Define('visraw_pt', 'visraw.Pt()')
            .Define('visraw_p', 'visraw.P()')
            .Define('visraw_m', 'visraw.M()')
            .Define('visraw_theta', 'visraw.Theta()')
            .Define('visraw_phi', 'visraw.Phi()')
            .Define('vis', 'sum(BoostedPandoraPFOs)')
            .Define('vis_pt', 'vis.Pt()')
            .Define('vis_p', 'vis.P()')
            .Define('vis_m', 'vis.M()')
            .Define('vis_theta', 'vis.Theta()')
            .Define('vis_phi', 'vis.Phi()')
            .Define('visrecoil', 'recoilBuilder2()(240, vis)')
            .Define('visrecoil_pt', 'visrecoil.Pt()')
            .Define('visrecoil_p', 'visrecoil.P()')
            .Define('visrecoil_m', 'visrecoil.M()')
            .Define('visrecoil_theta', 'visrecoil.Theta()')
            .Define('visrecoil_phi', 'visrecoil.Phi()')
        )

        prefilt.ee = (
            prefilt
             .Filter('n_leps==2 && n_paired_eles==2', 'ee')
             .Filter('vis_pt > 10', 'ee_met')
             .Filter('abs(ll_m[0]-91) < 4', 'ee_mz')
             )
        prefilt.mm = (
            prefilt
             .Filter('n_leps==2 && n_paired_muos==2', 'mm')
             .Filter('vis_pt > 10', 'mm_met')
             .Filter('abs(ll_m[0]-91) < 4', 'mm_mz')
             )
        prefilt.qq = (
            prefilt
             .Filter('n_leps==0', 'qq')
             .Filter('vis_pt > 15', 'qq_met')
             .Filter('abs(vis_m-91) < 5', 'qq_mz')
             )
        
        RDFanalysis.hists (Histmaker (prefilt, prefilt, 'prefilt_'))
        RDFanalysis.hists (Histmaker (prefilt.ee, prefilt, 'ee_'))
        RDFanalysis.hists (Histmaker (prefilt.mm, prefilt, 'mm_'))
        RDFanalysis.hists (Histmaker (prefilt.qq, prefilt, 'qq_'))

        patchdf (prefilt)
        return prefilt


    def output():
        return [
            'eventNumber',
            'ele_iso',
            'muo_iso',
            'sel_eles',
            'sel_muos',
            'n_eles',
            'n_muos',

            'all_gams',
            'all_gams_pt',
            'all_gams_p',
            'all_gams_m',
            'all_gams_theta',
            'all_gams_angle',
            'n_gams',

            'll',
            'll_pt',
            'll_p',
            'll_m',
            'll_theta',
            'll_phi',
            'llrecoil',
            'llrecoil_pt',
            'llrecoil_p',
            'llrecoil_m',
            'llrecoil_theta',
            'llrecoil_phi',

            'mcvis',
            'mcvis_pt',
            'mcvis_p',
            'mcvis_m',
            'mcvis_theta',
            'mcvis_phi',
            'mcvisraw',
            'mcvisraw_pt',
            'mcvisraw_p',
            'mcvisraw_m',
            'mcvisraw_theta',
            'mcvisraw_phi',

            'vis',
            'vis_pt',
            'vis_p',
            'vis_m',
            'vis_theta',
            'vis_phi',
            'visraw',
            'visraw_pt',
            'visraw_p',
            'visraw_m',
            'visraw_theta',
            'visraw_phi',
            'visrecoil',
            'visrecoil_pt',
            'visrecoil_p',
            'visrecoil_m',
            'visrecoil_theta',
            'visrecoil_phi',

            # 'mcisrgam',
            # 'mcisrgamz1',
            # 'mcisrgamz2',
            # 'x1',
            # 'x2',
            # 'beta',
            # 'truesqrts0',
            # 'truesqrts',
            # 'mcele',
            # 'mcgam',
            # 'mcz',
            # 'mcz_p',
            # 'mcz_pt',
            # 'mcz_m',
            # 'mch',
            # 'mch_pt',
            # 'mch_m',
            # 'mcht',
            # 'mcht_pt',
            # 'mcht_m',

            # 'eles',
            # 'ele_pt',
            # 'z',
            # 'z_p',
            # 'z_pt',
            # 'z_m',
            # 'h',
            # 'h_pt',
            # 'h_m',
            # 'ht',
            # 'ht_pt',
            # 'ht_m',
            ]

