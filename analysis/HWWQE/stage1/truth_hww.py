"""Phase 1 truth stage1 (PLAN.md Sec. 5.2): beams, H, W+, W-, W analysers and partners,
and Z decay products of ZH, H -> WW* events, for truth tomography with qtomo.

Standard FCCAnalyses stage script for the winter2023 environment (setup_hbs.sh):
    fccanalysis run stage1/truth_hww.py --files-list <file> --output <out.root> [--nevents 1000]
Batch: analysis/phase1_truth.py submit (SDCC HTCondor, xrootd input, GPFS output).

Output per event: arrays of length 11 in the slot order of truth_functions.h
(beam e-, beam e+, H, W+, W-, analyser+, partner+, analyser-, partner-, Z fermion, Z antifermion);
empty slots have pdg 0.
"""

# Channel A (Z -> ee, mumu) and B (Z -> qq) signal samples, winter2023 IDEA (config/samples.yaml)
processList = {
    "wzp6_ee_mumuH_HWW_ecm240": {"chunks": 4},
    "wzp6_ee_eeH_HWW_ecm240": {"chunks": 4},
    "wzp6_ee_qqH_HWW_ecm240": {"chunks": 11},
    "wzp6_ee_ssH_HWW_ecm240": {"chunks": 12},
    "wzp6_ee_ccH_HWW_ecm240": {"chunks": 12},
    "wzp6_ee_bbH_HWW_ecm240": {"chunks": 10},
}
prodTag = "FCCee/winter2023/IDEA/"
outputDir = "outputs/phase1/truth"
includePaths = ["truth_functions.h"]
nCPUS = 1
runBatch = False

SLOTS = ("beam_em", "beam_ep", "H", "Wp", "Wm", "ana_p", "partner_p", "ana_m", "partner_m", "zf1", "zf2")


class RDFanalysis():

    def analysers(df):
        df2 = (
            df
            .Alias("Particle0", "Particle#0.index")
            .Alias("Particle1", "Particle#1.index")
            .Define("truth_idx", "HWWQE::truth_hww_indices(Particle, Particle0, Particle1)")
            .Define("truth", "HWWQE::select(Particle, truth_idx)")
            .Define("truth_px", "FCCAnalyses::MCParticle::get_px(truth)")
            .Define("truth_py", "FCCAnalyses::MCParticle::get_py(truth)")
            .Define("truth_pz", "FCCAnalyses::MCParticle::get_pz(truth)")
            .Define("truth_e", "FCCAnalyses::MCParticle::get_e(truth)")
            .Define("truth_pdg", "FCCAnalyses::MCParticle::get_pdg(truth)")
        )
        return df2

    def output():
        return ["truth_idx", "truth_px", "truth_py", "truth_pz", "truth_e", "truth_pdg"]
