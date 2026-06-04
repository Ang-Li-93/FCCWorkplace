#!/usr/bin/env bash
#
# run_particle_gun_test.sh
# ------------------------
# Fire single muons through the ALLEGRO barrel to confirm that the silicon
# wrapper (SiWrBCollection) records SimTrackerHits.
#
#   bash simulation/run_particle_gun_test.sh [N_EVENTS]
#
# Muons are thrown around theta = 90 deg (central, crossing the barrel) over
# full phi so the cylindrical wrapper at r = 2040 mm gets hit.
#
# Geometry resolution honors $ALLEGRO_XML / $ALLEGRO_VERSION / $K4GEO
# (and thus $LOCAL_K4GEO). See simulation/_resolve_geometry.sh.
#
# Output: outputs/particle_gun_maps_wrapper.root

set -euo pipefail

HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REPO_ROOT="$( cd "$HERE/.." >/dev/null 2>&1 && pwd )"
OUTDIR="${REPO_ROOT}/outputs"
mkdir -p "$OUTDIR"

# shellcheck source=/dev/null
source "$HERE/_resolve_geometry.sh"

N_EVENTS="${1:-200}"
PARTICLE="${GUN_PARTICLE:-mu-}"
ENERGY="${GUN_ENERGY:-10*GeV}"
OUTFILE="${OUTDIR}/particle_gun_maps_wrapper.root"
SEED="${RANDOM_SEED:-42}"

if ! command -v ddsim >/dev/null 2>&1; then
    echo "ERROR: ddsim not found. Run: source setup/setup_key4hep.sh" >&2
    exit 1
fi

if ! resolve_allegro_compact; then
    exit 1
fi

echo "[gun] geometry : $ALLEGRO_COMPACT"
echo "[gun] particle : $PARTICLE  energy=$ENERGY  events=$N_EVENTS"
echo "[gun] output   : $OUTFILE"

# theta 80-100 deg (central) -> crosses the barrel wrapper; full phi.
ddsim \
    --compactFile "$ALLEGRO_COMPACT" \
    --enableGun \
    --gun.particle "$PARTICLE" \
    --gun.energy "$ENERGY" \
    --gun.distribution uniform \
    --gun.thetaMin "80*deg" \
    --gun.thetaMax "100*deg" \
    --gun.phiMin "0*deg" \
    --gun.phiMax "360*deg" \
    --numberOfEvents "$N_EVENTS" \
    --random.enableEventSeed \
    --random.seed "$SEED" \
    --outputFile "$OUTFILE"

echo "[gun] done. Inspect with:"
echo "      python simulation/check_sim_output.py $OUTFILE"
