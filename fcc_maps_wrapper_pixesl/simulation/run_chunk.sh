#!/usr/bin/env bash
#
# run_chunk.sh  -  one SELF-CONTAINED HTCondor job: WHIZARD + ddsim for one chunk.
#
#   run_chunk.sh CHUNK NPER CARD COMPACT STEERING OUTDIR [SEED_BASE]
#
# No reuse, no shared state: the job generates its OWN NPER events with WHIZARD
# (seed = SEED_BASE+CHUNK, in its own scratch dir -> integrates independently),
# then runs ddsim on them, writing OUTDIR/events_<CHUNK>.edm4hep.root.
#
# MINIMAL env handling on purpose (plain source + plain ddsim, no `set -e/-u`):
# those were found to crash ddsim. Self-contained on a worker (CVMFS + local
# k4geo build on gpfs). All paths absolute. Parallel-safe (per-job scratch).

CHUNK="$1"
NPER="$2"
CARD="$3"
COMPACT="$4"
STEERING="$5"
OUTDIR="$6"
SEED_BASE="${7:-42}"

REPO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." >/dev/null 2>&1 && pwd )"
TAG=$(printf '%05d' "$CHUNK")
SEED=$(( SEED_BASE + CHUNK ))
OUT="${OUTDIR}/events_${TAG}.edm4hep.root"
# per-job scratch (condor gives _CONDOR_SCRATCH_DIR; else a unique tmp dir)
SCRATCH="${_CONDOR_SCRATCH_DIR:-$(mktemp -d)}/whiz_${TAG}"

echo "[chunk $CHUNK] host=$(hostname)  nper=$NPER seed=$SEED  out=$OUT  scratch=$SCRATCH"
mkdir -p "$OUTDIR" "$SCRATCH"

# Env: clear positional args (so setup_MAPS.sh doesn't parse them), plain source.
set --
# shellcheck source=/dev/null
source "${REPO_ROOT}/setup_MAPS.sh" >/dev/null 2>&1
command -v whizard >/dev/null 2>&1 || { echo "[chunk $CHUNK] ERROR: whizard not found" >&2; exit 1; }
command -v ddsim   >/dev/null 2>&1 || { echo "[chunk $CHUNK] ERROR: ddsim not found" >&2; exit 1; }
[ -f "$CARD" ]    || { echo "[chunk $CHUNK] ERROR: missing card $CARD" >&2; exit 1; }
[ -f "$COMPACT" ] || { echo "[chunk $CHUNK] ERROR: missing compact $COMPACT" >&2; exit 1; }

# --- 1) WHIZARD: generate NPER events (own scratch -> own integration) --------
cd "$SCRATCH" || { echo "[chunk $CHUNK] ERROR: cannot cd scratch" >&2; exit 1; }
printf 'n_events = %d\nseed = %d\n' "$NPER" "$SEED" > header.sin
cat header.sin "$CARD" > card.sin
echo "[chunk $CHUNK] WHIZARD ..."
whizard card.sin
if [ ! -f proc.stdhep ]; then
    echo "[chunk $CHUNK] ERROR: WHIZARD produced no proc.stdhep" >&2; exit 1
fi

# --- 2) ddsim: full sim on this chunk's stdhep -------------------------------
echo "[chunk $CHUNK] ddsim ..."
ddsim --steeringFile "$STEERING" \
      --compactFile  "$COMPACT" \
      --inputFiles   "$SCRATCH/proc.stdhep" \
      --numberOfEvents -1 \
      --outputFile   "$OUT"
rc=$?
echo "[chunk $CHUNK] ddsim exit=$rc -> $OUT"
# clean the scratch (condor scratch is auto-removed; mktemp one we remove)
[ -n "${_CONDOR_SCRATCH_DIR:-}" ] || rm -rf "$SCRATCH"
exit $rc
