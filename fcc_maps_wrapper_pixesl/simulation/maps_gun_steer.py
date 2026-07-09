"""
maps_gun_steer.py - ddsim steering for PARTICLE-GUN runs on the BNL_MAPS
detector (MAPS_o1_v01.xml, standard beampipe).

Controlled single-particle input for MAPS/PixESL response studies (charge,
timing, hits/track vs species/momentum/angle), complementing the qq physics
sample (maps_steer.py) and the BIB samples (maps_bib_steer.py).

Identical to the physics steering (maps_steer.py) EXCEPT:
  - particle gun enabled (defaults below; run_particle_gun.sh overrides them
    with --gun.* CLI flags)
  - NO crossing-angle boost: gun directions are specified directly in the
    detector frame; a boost would distort the requested theta/phi/momentum.
  - NO vertex smearing: point source at (0,0,0), t=0, so h_time in the CSV is
    pure time-of-flight + drift (L3 r=130mm -> 0.43ns, L4 r=315mm -> 1.05ns
    for beta~1).
  - seed from the GUN_SEED env var (CLI --random.seed SIGSEGVs ddsim - qq
    production lesson; same pattern as BIB_SEED in maps_bib_steer.py).
  - no rejectPDGs/zeroTimePDGs blocks: the gun emits only the requested
    species, DDSim defaults apply.

Kept identical ON PURPOSE so gun CSVs are directly comparable with the qq
signal CSV: physics list FTFP_BERT, weighted tracker action, 1 keV tracker
filter, 1 MeV minimalKineticEnergy. (For BIB-style no-threshold hits override
on the CLI: --filter.tracker edep0)

Usage (via the runner, recommended):
  bash fcc_maps_wrapper_pixesl/simulation/run_particle_gun.sh 100
or directly:
  GUN_SEED=42 ddsim --steeringFile fcc_maps_wrapper_pixesl/simulation/maps_gun_steer.py \
        --compactFile k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01.xml \
        --gun.particle mu- --gun.energy "10*GeV" \
        --numberOfEvents 100 --outputFile gun.edm4hep.root
"""
import os

from DDSim.DD4hepSimulation import DD4hepSimulation
from g4units import mm, GeV, MeV, keV, deg

SIM = DD4hepSimulation()

SIM.runType = "batch"
# Same physics as the qq signal sim (NOT the BIB precision-EM list).
SIM.physics.list = "FTFP_BERT"
SIM.physics.rangecut = None

# Detector-frame source: no boost, no vertex smearing (defaults = disabled).
SIM.crossingAngleBoost = 0.0

# --- particle gun -----------------------------------------------------------
# Defaults = single mu-, distribution "uniform" = FLAT IN THETA (NOT isotropic;
# verified in DD4hep 1.36 Geant4IsotropeGenerator: theta = min + (max-min)*rnd.
# Flat-in-theta = uniform incidence-angle sampling, which is what we want for
# response studies; pass --gun.distribution "cos(theta)" for true isotropic) in
# a theta window where every track crosses BOTH MAPS layers (VTXOB barrel
# edges: L3 atan(130/163)=38.6deg, L4 atan(315/326)=44.0deg -> [45,135] is
# inside both), full phi, from the origin. run_particle_gun.sh overrides via CLI.
# gun.energy is deliberately NOT set here, for two reasons (both verified in
# the pinned stack):
#   - despite the name it is a fixed MOMENTUM magnitude |p| (Geant4ParticleGun
#     sets momentumMin=momentumMax=energy; the DDG4 property doc says "Fixed
#     momentum value") - it is NOT kinetic and NOT total energy;
#   - when set (non-None) it OVERRIDES momentumMin/Max inside ddsim, which
#     would silently break the runner's flat-momentum mode.
# The runner always passes exactly one of --gun.energy (= fixed |p|) or
# --gun.momentumMin/Max (flat |p| spectrum); pass one yourself in direct use.
SIM.enableGun = True
SIM.gun.particle = "mu-"
SIM.gun.multiplicity = 1
SIM.gun.distribution = "uniform"
SIM.gun.thetaMin = 45 * deg
SIM.gun.thetaMax = 135 * deg
SIM.gun.position = (0.0, 0.0, 0.0)

# --- sensitive-detector actions (same as physics steering) ------------------
SIM.action.tracker = (
    "Geant4TrackerWeightedAction",
    {"HitPositionCombination": 2, "CollectSingleDeposits": False},
)
SIM.action.trackerSDTypes = ["tracker"]
SIM.action.calo = "Geant4CalorimeterAction"
SIM.action.calorimeterSDTypes = ["calorimeter"]

# --- filters: 1 keV tracker threshold (qq signal convention) ----------------
SIM.filter.filters = {
    "edep1kev": {"name": "EnergyDepositMinimumCut", "parameter": {"Cut": 1.0 * keV}},
}
SIM.filter.tracker = "edep1kev"
SIM.filter.calo = ""

# --- particle handler (same as physics steering) ----------------------------
SIM.part.minimalKineticEnergy = 1.0 * MeV
SIM.part.keepAllParticles = False
SIM.part.saveProcesses = ["Decay"]

# --- reproducibility ---------------------------------------------------------
# Seed via GUN_SEED env (ddsim --random.seed on the CLI SIGSEGVs). With
# enableEventSeed the per-event seed derives from (seed, run, event) -> any
# event reproduces exactly.
SIM.random.enableEventSeed = True
SIM.random.seed = int(os.environ.get("GUN_SEED", "42"))

SIM.outputConfig.forceEDM4HEP = True
