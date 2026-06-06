"""
maps_steer.py  -  ddsim steering for the BNL_MAPS (ALLEGRO + 20um MAPS vertex) full sim.

Slim, ALLEGRO-appropriate steering for the LDRD WP1 MAPS study. Based on the
TRACKER-relevant parts of k4geo's SteeringFile_IDEA_o1_v03.py, but WITHOUT the
IDEA dual-readout-calorimeter (DRC) specifics (custom DRC EDM4hep output plugin,
optical-photon/Cerenkov physics, scintillator/DRcalo SD actions) -- those do not
apply to ALLEGRO's ECal/HCal and would mis-handle the calos / waste CPU.

Usage:
  ddsim --steeringFile fcc_maps_wrapper_pixesl/simulation/maps_steer.py \
        --compactFile k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01.xml \
        --inputFiles <events.stdhep>  --numberOfEvents 100 \
        --outputFile <out_edm4hep.root>
(compactFile / inputFiles / numberOfEvents / outputFile can be set here or on the CLI.)
"""
from DDSim.DD4hepSimulation import DD4hepSimulation
from g4units import mm, GeV, MeV, keV

SIM = DD4hepSimulation()

SIM.runType = "batch"
# Physics list: standard FTFP_BERT (same as ALLEGRO/IDEA/CLD full sim).
SIM.physics.list = "FTFP_BERT"

# FCC-ee crossing-angle boost: head-on generator events -> detector frame
# (half crossing angle 0.015 rad). Matches CLD/IDEA full-sim steerings. (This was
# NOT the cause of the earlier FATAL -- that was leptonic FSR, fixed via MSTJ(41)=1
# in the WHIZARD card.)
SIM.crossingAngleBoost = 0.015   # rad

# Vertex smearing applied HERE at full-sim level (generator has it OFF via
# MSTP(151)=0), per Brieuc's recipe: ddsim --vertexSigma X Y Z T. Units are
# Geant4-native (mm, mm, mm, ns). Values below = winter2023 FCC-ee Z luminous
# region (matching the card's PARP(151-154): sigma_x=5.96um, sigma_y=23.8nm,
# sigma_z=0.397mm, sigma_t=36.3ps).
#   Brieuc's example values (newer optics): [0.0098, 2.54e-5, 0.646, 0.0063]
# This is safe now that generator-side smearing is off (the DD4hep #1094 trap is
# the double/generator-side smearing, which we removed).
SIM.vertexSigma  = [5.96e-3, 23.8e-6, 0.397, 0.0363]
SIM.vertexOffset = [0.0, 0.0, 0.0, 0.0]

# --- MC particle selection ------------------------------------------------
# Do NOT pass partons / gauge bosons / diquarks to Geant4 (they are not to be
# tracked). Same set as the IDEA steering.
SIM.physics.rejectPDGs = {
    1, 2, 3, 4, 5, 6, 21, 23, 24, 25,
    1103, 2101, 2103, 2203, 3101, 3103, 3201, 3203, 3303,
    4101, 4103, 4201, 4203, 4301, 4303, 4403,
    5101, 5103, 5201, 5203, 5301, 5303, 5401, 5403, 5503,
}
# Documentation FSR leptons with properTime 0 -> not passed to Geant4.
SIM.physics.zeroTimePDGs = {11, 13, 15, 17}
SIM.physics.rangecut = None

# --- sensitive-detector actions ------------------------------------------
# This study only cares about the TRACKER (vertex / MAPS). The weighted tracker
# action gives a good single hit position per sensor crossing
# (HitPositionCombination=2 -> energy-weighted mean of entry/exit).
SIM.action.tracker = (
    "Geant4TrackerWeightedAction",
    {"HitPositionCombination": 2, "CollectSingleDeposits": False},
)
SIM.action.trackerSDTypes = ["tracker"]
# Calo: we do NOT care about it (it's at r>2 m, downstream of every vertex hit).
# Keep the plain standard action just so the calo SDs are valid; its output is
# unused. (NOT the IDEA DRC action.) See note below for skipping calo for speed.
SIM.action.calo = "Geant4CalorimeterAction"
SIM.action.calorimeterSDTypes = ["calorimeter"]

# NOTE on speed: the calo EM/hadronic showers dominate full-sim CPU, yet they
# are irrelevant here. For the big (10k) production we can cut CPU a lot by not
# tracking into the calo (kill particles past the tracker). That needs a region
# kill or a tracker+field-only geometry (ECal hosts the solenoid field, so it
# can't simply be dropped) -- set up separately for the condor jobs.

# --- filters --------------------------------------------------------------
SIM.filter.filters = {
    "edep1kev": {"name": "EnergyDepositMinimumCut", "parameter": {"Cut": 1.0 * keV}},
}
SIM.filter.tracker = "edep1kev"   # 1 keV threshold on tracker hits (vertex/MAPS)
SIM.filter.calo = ""              # no calo filter (don't kill low-E deposits)

# --- particle handler -----------------------------------------------------
SIM.part.minimalKineticEnergy = 1.0 * MeV
SIM.part.keepAllParticles = False
SIM.part.saveProcesses = ["Decay"]

# --- reproducibility ------------------------------------------------------
SIM.random.enableEventSeed = True
SIM.random.seed = 42

# Output: leave the plugin unset so ddsim auto-selects the standard EDM4hep
# writer from the .root output filename (NOT the IDEA DRC plugin).
SIM.outputConfig.forceEDM4HEP = True
