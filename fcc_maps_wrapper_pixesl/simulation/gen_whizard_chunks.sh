#!/usr/bin/env bash
#
# gen_whizard_chunks.sh  -  make N independent stdhep files for per-file chunking.
#
#   bash gen_whizard_chunks.sh [NFILES] [NPER] [SEED_BASE]
#
# Re-runs WHIZARD NFILES times (seed = SEED_BASE+i), each producing NPER events,
# reusing the cached integration grid in the work dir (so each run is fast -- only
# event generation, no re-integration). Writes:
#   STDHEPDIR/events_00000.stdhep ... events_<NFILES-1>.stdhep   (uncompressed)
#
# These feed run_ddsim_chunk.sh (one ddsim per file, NO --skipNEvents).
#
# Env overrides:
#   CARD       WHIZARD .sin card  (default: wzp6_ee_qq_ecm91p2)
#   STDHEPDIR  output dir for the per-file stdheps
#   GRIDWORK       WHIZARD work dir holding the cached grid (default outputs/whizard_qq)

set -euo pipefail
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REPO_ROOT="$( cd "$HERE/../.." >/dev/null 2>&1 && pwd )"

NFILES="${1:-100}"
NPER="${2:-100}"
SEED_BASE="${3:-42}"
CARD="${CARD:-${REPO_ROOT}/FCC-config/winter2023/FCCee/Generator/Whizard/v3.0.3/wzp6_ee_qq_ecm91p2.sin}"
STDHEPDIR="${STDHEPDIR:-/gpfs/mnt/gpfs01/usfcc/MAPS_storage/generation/stdhep/winter2023/wzp6_ee_qq_ecm91p2/chunks}"
GRIDWORK="${GRIDWORK:-${REPO_ROOT}/outputs/whizard_qq}"

[ -f "$CARD" ] || { echo "ERROR: card not found: $CARD" >&2; exit 1; }
# source env in the current shell. Clear positional args (set --) first so
# setup_MAPS.sh does not parse THIS script's args (e.g. "2") as options; relax
# set -e/-u (the setup scripts are interactive-style, not -e clean).
set +eu
set --
# shellcheck source=/dev/null
source "${REPO_ROOT}/setup_MAPS.sh" >/dev/null 2>&1
set -eu
command -v whizard >/dev/null 2>&1 || { echo "ERROR: whizard not found (source setup_MAPS.sh)" >&2; exit 1; }

mkdir -p "$STDHEPDIR" "$GRIDWORK"
cd "$GRIDWORK"

echo "[gen-chunks] NFILES=$NFILES NPER=$NPER seed_base=$SEED_BASE"
echo "[gen-chunks] card=$CARD"
echo "[gen-chunks] out =$STDHEPDIR"
echo "[gen-chunks] work=$GRIDWORK  (reuses cached integration grid)"

for i in $(seq 0 $((NFILES - 1))); do
    tag=$(printf '%05d' "$i")
    out="${STDHEPDIR}/events_${tag}.stdhep"
    if [ -s "$out" ]; then echo "[gen-chunks] $tag exists, skip"; continue; fi
    printf 'n_events = %d\nseed = %d\n' "$NPER" "$((SEED_BASE + i))" > header.sin
    cat header.sin "$CARD" > card.sin
    rm -f proc.stdhep
    if whizard card.sin > "whizard_chunk_${tag}.log" 2>&1 && [ -f proc.stdhep ]; then
        mv -f proc.stdhep "$out"
        echo "[gen-chunks] $tag -> $out ($(du -h "$out" | cut -f1))"
    else
        echo "[gen-chunks] ERROR chunk $tag (see $GRIDWORK/whizard_chunk_${tag}.log)" >&2
    fi
done
echo "[gen-chunks] done. $(ls "$STDHEPDIR"/events_*.stdhep 2>/dev/null | wc -l) files in $STDHEPDIR"
