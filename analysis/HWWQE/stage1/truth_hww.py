"""Truth stage1 (PLAN.md Sec. 5.2, 5.3): beams, H, W+, W-, W analysers and partners, and Z decay
products of ZH, H -> WW* events, for truth tomography with qtomo.

Standard FCCAnalyses stage script for the winter2023 environment (setup_hbs.sh):
    fccanalysis run stage1/truth_hww.py --files-list <file> --output <out.root> [--nevents 1000]
Batch (central samples): analysis/phase1_truth.py submit (SDCC HTCondor, xrootd input, GPFS output).

Inputs: the central winter2023 files, whose MC relations are the branches 'Particle#0' (parents)
and 'Particle#1' (daughters), and the dedicated samples written by the Key4hep 2024-03-10 stack
(gen/run_hwwqe_job.sh), where they are '_Particle_parents' and '_Particle_daughters'.  The
pair present in the input file is chosen from the dataframe's columns.

Output per event: arrays of length 11 in the slot order of truth_functions.h
(beam e-, beam e+, H, W+, W-, analyser+, partner+, analyser-, partner-, Z fermion, Z antifermion);
empty slots have truth_idx -1 and pdg 0.
  - Slot 2 (H) is the RECORDED H, the H line whose daughters are the W+ W- pair.  In the winter2023
    record it is the pre-shower documentation copy with the WHIZARD momentum; it differs from
    W+ + W- when the shower of the Z decay products rescaled the (Z system, H) pair.  The physical
    H rest frame is that of W+ + W- (slots 3 + 4): use it for the decay angles.
  - Slots 3, 4 (W+, W-) are the decaying (last) copies of the W bosons, so W = analyser + partner
    always holds (a Pythia8 W that radiates a photon, or recoils against one, is copied; the
    winter2023 W bosons have a single copy).
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

# (parents, daughters) index columns of the MC collection 'Particle': winter2023 central files
# (podio of Key4hep 2022-12-23), then files written by the Key4hep 2024-03-10 stack.
MC_RELATIONS = (("Particle#0.index", "Particle#1.index"),
                ("_Particle_parents.index", "_Particle_daughters.index"))


def mc_relation_columns(df):
    """The (parents, daughters) index columns of 'Particle' present in the input file."""
    columns = {str(c) for c in df.GetColumnNames()}
    for parents, daughters in MC_RELATIONS:
        if parents in columns and daughters in columns:
            return parents, daughters
    raise RuntimeError("truth_hww.py: no MC parent/daughter columns in the input (tried "
                       + ", ".join(" / ".join(pair) for pair in MC_RELATIONS) + ")")


class RDFanalysis():

    def analysers(df):
        parents, daughters = mc_relation_columns(df)
        df2 = (
            df
            .Alias("Particle0", parents)
            .Alias("Particle1", daughters)
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
