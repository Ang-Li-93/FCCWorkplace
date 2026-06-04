#!/usr/bin/env bash
#
# run_ddsim_zinclusive.sh
# -----------------------
# Run ddsim on a generated Z-inclusive event file through the ALLEGRO geometry
# (including the silicon wrapper), producing EDM4hep output for the converter.
#
#   bash simulation/run_ddsim_zinclusive.sh [N_EVENTS] [INPUT_FILE]
#
#   N_EVENTS    number of events to simulate (default: 1000; -1 = all)
#   INPUT_FILE  generator file (.hepmc/.hepmc3/.stdhep/.slcio).
#               default: outputs/z_inclusive_gen.hepmc  (from run_whizard.sh)
#
# Output: outputs/z_inclusive_maps_wrapper_edm4hep.root

set -euo pipefail

HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REPO_ROOT="$( cd "$HERE/.." >/dev/null 2>&1 && pwd )"
OUTDIR="${REPO_ROOT}/outputs"
mkdir -p "$OUTDIR"

# shellcheck source=/dev/null
source "$HERE/_resolve_geometry.sh"

N_EVENTS="${1:-1000}"
INPUT_FILE="${2:-${OUTDIR}/z_inclusive_gen.hepmc}"
OUTFILE="${OUTDIR}/z_inclusive_maps_wrapper_edm4hep.root"
SEED="${RANDOM_SEED:-42}"

if ! command -v ddsim >/dev/null 2>&1; then
    echo "ERROR: ddsim not found. Run: source setup/setup_key4hep.sh" >&2
    exit 1
fi
if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: generator input not found: $INPUT_FILE" >&2
    echo "       Generate it first, e.g.:  bash generation/run_whizard.sh $N_EVENTS" >&2
    echo "       or pass a path:  bash $0 $N_EVENTS /path/to/events.hepmc" >&2
    exit 1
fi
if ! resolve_allegro_compact; then
    exit 1
fi

echo "[zsim] geometry : $ALLEGRO_COMPACT"
echo "[zsim] input    : $INPUT_FILE"
echo "[zsim] events   : $N_EVENTS"
echo "[zsim] output   : $OUTFILE"

NEV_ARG=()
if [ "$N_EVENTS" != "-1" ]; then
    NEV_ARG=(--numberOfEvents "$N_EVENTS")
fi

ddsim \
    --compactFile "$ALLEGRO_COMPACT" \
    --inputFiles "$INPUT_FILE" \
    "${NEV_ARG[@]}" \
    --random.enableEventSeed \
    --random.seed "$SEED" \
    --outputFile "$OUTFILE"

echo "[zsim] done -> $OUTFILE"
echo "[zsim] next:"
echo "   python conversion/convert_simhits_to_pixesl.py \\"
echo "     --input $OUTFILE \\"
echo "     --output ${OUTDIR}/pixesl_hits_zinclusive.csv \\"
echo "     --geometry conversion/geometry_config.yaml \\"
echo "     --collections conversion/collections_config.yaml --edep-unit GeV"
