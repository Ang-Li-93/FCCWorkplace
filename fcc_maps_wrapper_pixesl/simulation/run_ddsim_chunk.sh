#!/usr/bin/env bash
#
# run_ddsim_chunk.sh  -  one HTCondor job: ddsim on ONE per-chunk stdhep file.
#
#   run_ddsim_chunk.sh CHUNK STDHEPDIR COMPACT STEERING OUTDIR [SEED_BASE]
#
# Per-file chunking (no --skipNEvents): chunk i reads STDHEPDIR/events_<i>.stdhep
# and writes OUTDIR/events_<i>.edm4hep.root, processing ALL events in the file.
#
# Deliberately MINIMAL: it mirrors the known-good interactive invocation
# (source the env, then run ddsim) with no `set -e/-u` and no extra ddsim flags,
# because those were found to perturb ddsim into a crash. Self-contained on a
# worker node (CVMFS + local k4geo build on gpfs); all paths absolute.

CHUNK="$1"
STDHEPDIR="$2"
COMPACT="$3"
STEERING="$4"
OUTDIR="$5"
SEED_BASE="${6:-42}"

REPO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." >/dev/null 2>&1 && pwd )"
TAG=$(printf '%05d' "$CHUNK")
STDHEP="${STDHEPDIR}/events_${TAG}.stdhep"
OUT="${OUTDIR}/events_${TAG}.edm4hep.root"

echo "[chunk $CHUNK] host=$(hostname)  in=$STDHEP  out=$OUT"
mkdir -p "$OUTDIR"

# Source the project env. Clear positional args first (set --) so setup_MAPS.sh
# does not parse THIS script's args as its own options. Plain source -- no set -e.
set --
# shellcheck source=/dev/null
source "${REPO_ROOT}/setup_MAPS.sh" >/dev/null 2>&1

if ! command -v ddsim >/dev/null 2>&1; then
    echo "[chunk $CHUNK] ERROR: ddsim not found after sourcing setup_MAPS.sh" >&2
    exit 1
fi
if [ ! -f "$STDHEP" ]; then echo "[chunk $CHUNK] ERROR: missing $STDHEP" >&2; exit 1; fi

# Match the validated interactive ddsim invocation exactly (seeding comes from
# the steering's random.enableEventSeed; the input events already differ per file).
ddsim --steeringFile "$STEERING" \
      --compactFile  "$COMPACT" \
      --inputFiles   "$STDHEP" \
      --numberOfEvents -1 \
      --outputFile   "$OUT"
rc=$?
echo "[chunk $CHUNK] ddsim exit=$rc -> $OUT"
exit $rc
