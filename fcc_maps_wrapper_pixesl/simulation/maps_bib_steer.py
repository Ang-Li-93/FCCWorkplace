"""
maps_bib_steer.py - ddsim steering for BEAM-INDUCED-BACKGROUND runs on the
BNL_MAPS detector (use with MAPS_o1_v01_BIB.xml, the CAD-beampipe variant).

Follows the HEP-FCC/bib-studies simulation recipe (simulation/README.md):
BIB occupancy is driven by low-energy secondaries (fluorescence photons, soft
e+-), so precision EM physics and no tracker energy threshold are required.
Differences vs the physics steering (maps_steer.py):
  - physics list FTFP_BERT_EMZ (precision EM) instead of FTFP_BERT
  - range cut 0.05 mm; low-energy EM UI commands (50 eV cut edge, 1 eV
    lowest e- energy, Auger, deexcitation everywhere)
  - tracker filter "edep0" (keep ANY energy deposit) instead of 1 keV
  - keepAllParticles = True (full MC-particle record for provenance)
  - NO vertex smearing (BIB input files carry their own vertices/timing)
  - crossingAngleBoost = 0.015 rad: correct for IPC and RB (GuineaPig frame);
    OVERRIDE to 0 on the CLI for beam-gas/injection/SR (already in lab frame):
      ddsim ... --crossingAngleBoost 0

Input: GuineaPig .pairs files are read natively (Geant4EventReaderGuineaPig,
selected by the .pairs extension); 1 file = 1 bunch crossing = 1 event
(guineapig.particlesPerEvent = -1). .hepevt inputs also work.

NOTE (pre-2026 IPC files, e.g. GHC/V24.4): GuineaPig has no solenoid field,
particle positions are wrong -> reset vertices to (0,0,0) first
(bib-studies/simulation/set_vertex_000.py). Newer files (LCC/V106.2) are fine.

Usage:
  ddsim --steeringFile fcc_maps_wrapper_pixesl/simulation/maps_bib_steer.py \
        --compactFile k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01_BIB.xml \
        --inputFiles <pairs.pairs> -N -1 --outputFile <out_edm4hep.root>
"""
import os

from DDSim.DD4hepSimulation import DD4hepSimulation
from g4units import mm, GeV, MeV, keV, eV

SIM = DD4hepSimulation()

SIM.runType = "batch"

# --- BIB physics: precision EM --------------------------------------------
SIM.physics.list = "FTFP_BERT_EMZ"
SIM.physics.rangecut = 0.05 * mm

# GuineaPig IPC frame -> detector frame (half crossing angle). For beam-gas /
# injection / SR override on the CLI: --crossingAngleBoost 0
SIM.crossingAngleBoost = 0.015  # rad

# NO vertex smearing / offset: BIB files carry their own vertices and timing.
# (SIM.vertexSigma / vertexOffset intentionally left at defaults = disabled.)

# Read the whole .pairs file (1 bunch crossing) as a single event.
SIM.guineapig.particlesPerEvent = "-1"

# --- MC particle selection -------------------------------------------------
# BIB files contain only real particles (e+-, photons); keep the parton/diquark
# reject list anyway (harmless, protects against odd hepevt content).
SIM.physics.rejectPDGs = {
    1, 2, 3, 4, 5, 6, 21, 23, 24, 25,
    1103, 2101, 2103, 2203, 3101, 3103, 3201, 3203, 3303,
    4101, 4103, 4201, 4203, 4301, 4303, 4403,
    5101, 5103, 5201, 5203, 5301, 5303, 5401, 5403, 5503,
}

# --- sensitive-detector actions (same as physics steering) -----------------
SIM.action.tracker = (
    "Geant4TrackerWeightedAction",
    {"HitPositionCombination": 2, "CollectSingleDeposits": False},
)
SIM.action.trackerSDTypes = ["tracker"]
SIM.action.calo = "Geant4CalorimeterAction"
SIM.action.calorimeterSDTypes = ["calorimeter"]

# --- filters: NO energy threshold on tracker hits (BIB recipe) --------------
# "edep0" is predefined by DDSim (EnergyDepositMinimumCut/Cut0). Do NOT redefine
# SIM.filter.filters here: a second bare "EnergyDepositMinimumCut" instance
# collides with the default registration (Filter-Already-Registered).
SIM.filter.tracker = "edep0"
SIM.filter.calo = ""

# --- particle handler: keep everything for provenance -----------------------
SIM.part.keepAllParticles = True

# --- low-energy EM treatment (bib-studies recipe) ---------------------------
SIM.ui.commandsConfigure = [
    "/cuts/setLowEdge 50 eV",
    "/process/em/lowestElectronEnergy 1 eV",
    "/process/em/auger true",
    "/process/em/deexcitationIgnoreCut true",
]

# --- reproducibility ---------------------------------------------------------
# Per-BX seed via the BIB_SEED env var (set by run_bib_chunk.sh to
# seed_base + bx): any bunch crossing reproduces exactly by re-exporting the
# same value. This is env-driven because `ddsim --random.seed` on the CLI
# SIGSEGVs (qq production lesson) and --meta.runNumberOffset does NOT feed the
# seed (checked in DD4hep 1.36: it only changes output-file metadata).
SIM.random.enableEventSeed = True
SIM.random.seed = int(os.environ.get("BIB_SEED", "42"))

SIM.outputConfig.forceEDM4HEP = True
