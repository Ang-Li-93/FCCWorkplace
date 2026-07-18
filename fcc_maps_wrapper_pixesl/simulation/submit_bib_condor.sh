#!/usr/bin/env bash
#
# submit_bib_condor.sh  -  HTCondor production over IPC bunch crossings.
#
#   bash submit_bib_condor.sh [--submit]
#
# Scans SRCDIR for data<bx>/pairs.pairs, writes a NEW TIMESTAMPED bx list, and
# queues NJOBS = ceil(NBXTOTAL/NBX) self-contained jobs (run_bib_chunk.sh):
# each does vertex-reset + ddsim (BIB geometry, .pairs native, per-BX seed) +
# PixESL conversion for NBX bunch crossings. Already-completed BXs are skipped
# inside the runner, so re-running with --submit after failures only redoes
# the missing ones. Dry-run unless --submit.
#
# Safety (audit findings, do not regress):
#   - the bx list is written to a fresh bxlist_<timestamp>.txt and that exact
#     name is baked into the .sub: a re-run NEVER rewrites a list that queued
#     jobs are still reading (a truncated live list made jobs silently no-op)
#   - --submit REFUSES to queue while jobs from a previous submission of this
#     OUTDIR are still in the queue (concurrent same-BX jobs; override FORCE=1
#     only if you know the old cluster is drained/removed)
#   - initialdir pins the jobs' Iwd to a shared path (otherwise Iwd = cwd of
#     condor_submit; a node-local cwd holds every job with 'Failed to chdir')
#
# Env config:
#   SRCDIR     IPC source tree            (default: reference GHC/V24.4 IPC Z)
#   OUTDIR     output root on gpfs        (sim/ + csv/ + condor/ under here)
#   NBX        bunch crossings per job    (default 5; ~10 min each)
#   NBXTOTAL   cap on total BXs, -1=all   (default -1)
#   BXFILE     explicit bx-id list file (one id per line) instead of scanning
#              SRCDIR -- e.g. the harvest's missing_bx.txt for a sweep run
#   COMPACT    BIB compact xml            (MAPS_o1_v01_BIB.xml)
#   STEERING   BIB ddsim steering         (maps_bib_steer.py)
#   ACCT_GROUP / REQUEST_MEMORY / REQUEST_DISK / MAXRUNTIME / FORCE
#
# After completion:  bash harvest_bib.sh   (merge per-BX CSVs)

set -euo pipefail
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REPO_ROOT="$( cd "$HERE/../.." >/dev/null 2>&1 && pwd )"

# BASELINE (per A. Ilg / vertex group, July 2026): LCC V106.2 lattice.
# 2026+ GuineaPig files: flat output_<bx>.pairs naming, vertices already
# correct (generated with 2T field) -> NO vertex reset.
# For the old GHC V24.4 sample set: SRCDIR=.../BIB/GHC/V24.4/IPC/Z,
# OUTDIR=.../BIB_derived/sim/GHC_V24.4_IPC_Z, VTXRESET=1.
SRCDIR="${SRCDIR:-/gpfs/mnt/gpfs01/usfcc/MAPS_storage/BIB/LCC/V106.2/IPC/Z}"
OUTDIR="${OUTDIR:-/gpfs/mnt/gpfs01/usfcc/MAPS_storage/BIB_derived/sim/LCC_V106.2_IPC_Z}"
NBX="${NBX:-5}"
NBXTOTAL="${NBXTOTAL:--1}"
COMPACT="${COMPACT:-${REPO_ROOT}/k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01_BIB.xml}"
STEERING="${STEERING:-${REPO_ROOT}/fcc_maps_wrapper_pixesl/simulation/maps_bib_steer.py}"
ACCT_GROUP="${ACCT_GROUP:-group_usfcc}"
REQUEST_MEMORY="${REQUEST_MEMORY:-8192}"   # MB; EMZ + CAD geometry, same margin as qq
REQUEST_DISK="${REQUEST_DISK:-2097152}"    # KB = 2 GB (pairs + one edm4hep in scratch)
MAXRUNTIME="${MAXRUNTIME:-28800}"          # s = 8 h (NBX * ~10 min + margin)
FORCE="${FORCE:-0}"

RUNNER="${HERE}/run_bib_chunk.sh"
SUBDIR="${OUTDIR}/condor"; LOGDIR="${SUBDIR}/logs"
STAMP="$(date +%Y%m%d_%H%M%S)"
BXLIST="${SUBDIR}/bxlist_${STAMP}.txt"
SUBFILE="${SUBDIR}/maps_bib_ipc_${STAMP}.sub"

for f in "$COMPACT" "$STEERING" "$RUNNER"; do
    [ -e "$f" ] || { echo "ERROR: missing $f" >&2; exit 1; }
done
[ -d "$SRCDIR" ] || { echo "ERROR: missing SRCDIR $SRCDIR" >&2; exit 1; }
command -v condor_submit >/dev/null 2>&1 || { echo "ERROR: condor_submit not found" >&2; exit 1; }
mkdir -p "$OUTDIR/sim" "$OUTDIR/csv" "$LOGDIR"; chmod +x "$RUNNER"

# Guard: previous submission of this OUTDIR still in the queue?
# The runner path is the job's Cmd (NOT part of Args); OUTDIR is the LAST
# runner argument -- match both exactly (field-wise, no substring surprises).
NQUEUED=$(condor_q -af Cmd Args 2>/dev/null \
          | awk -v r="$RUNNER" -v o="$OUTDIR" '$1==r && $NF==o' | wc -l)
NQUEUED=${NQUEUED:-0}

# bx list -> fresh timestamped file: numeric ids of data<bx> dirs with a
# non-empty pairs.pairs, numerically sorted. (if-then, not '[ -s ] &&': under
# pipefail a bad LAST entry would abort the whole script silently)
# With BXFILE: take the ids from that file instead (sweep mode).
# Layout auto-detect: GHC-style data<bx>/pairs.pairs OR flat output_<bx>.pairs.
if [ -n "${BXFILE:-}" ]; then
    [ -s "$BXFILE" ] || { echo "ERROR: BXFILE $BXFILE missing or empty" >&2; exit 1; }
    sed -n 's/^\s*\([0-9]\+\)\s*$/\1/p' "$BXFILE" | sort -n > "$BXLIST"
elif ls "$SRCDIR" | grep -q '^data[0-9]\+$'; then
    SRCLAYOUT="ghc-dirs"
    ls "$SRCDIR" | sed -n 's/^data\([0-9]\+\)$/\1/p' | sort -n | \
        while read -r bx; do
            if [ -s "$SRCDIR/data$bx/pairs.pairs" ]; then echo "$bx"; fi
        done > "$BXLIST"
else
    SRCLAYOUT="flat"
    ls "$SRCDIR" | sed -n 's/^output_\([0-9]\+\)\.pairs$/\1/p' | sort -n | \
        while read -r bx; do
            if [ -s "$SRCDIR/output_$bx.pairs" ]; then echo "$bx"; fi
        done > "$BXLIST"
fi
# vertex reset: default by layout (pre-2026 GHC dirs -> 1; 2026+ flat -> 0)
VTXRESET="${VTXRESET:-$( [ "${SRCLAYOUT:-flat}" = "ghc-dirs" ] && echo 1 || echo 0 )}"
if [ "$NBXTOTAL" -gt 0 ]; then
    head -n "$NBXTOTAL" "$BXLIST" > "${BXLIST}.tmp" && mv "${BXLIST}.tmp" "$BXLIST"
fi
NBXFOUND=$(wc -l < "$BXLIST")
[ "$NBXFOUND" -gt 0 ] || { echo "ERROR: no data<bx>/pairs.pairs found in $SRCDIR" >&2; exit 1; }
NJOBS=$(( (NBXFOUND + NBX - 1) / NBX ))

cat > "$SUBFILE" <<EOF
# MAPS BIB IPC production ${STAMP} -- ${NJOBS} jobs x ${NBX} BX = ${NBXFOUND} bunch crossings
universe                = vanilla
executable              = ${RUNNER}
arguments               = \$(Process) ${NBX} ${BXLIST} ${COMPACT} ${STEERING} ${SRCDIR} ${OUTDIR} ${VTXRESET}
initialdir              = ${LOGDIR}
should_transfer_files   = NO
getenv                  = False
request_cpus            = 1
request_memory          = ${REQUEST_MEMORY}
request_disk            = ${REQUEST_DISK}
accounting_group        = ${ACCT_GROUP}
accounting_group_user   = ${USER}
+MaxRuntime             = ${MAXRUNTIME}
output                  = ${LOGDIR}/job_${STAMP}_\$(Process).out
error                   = ${LOGDIR}/job_${STAMP}_\$(Process).err
log                     = ${LOGDIR}/job_${STAMP}_\$(Process).log
queue ${NJOBS}
EOF

echo "================================================================"
echo "[submit] BIB IPC: ${NJOBS} jobs x ${NBX} BX = ${NBXFOUND} bunch crossings"
echo "[submit] source   : ${SRCDIR}"
echo "[submit] compact  : ${COMPACT}"
echo "[submit] steering : ${STEERING}"
echo "[submit] outdir   : ${OUTDIR}"
echo "[submit] bx list  : ${BXLIST}   vtx-reset: ${VTXRESET}"
echo "[submit] acct grp : ${ACCT_GROUP}   sub: ${SUBFILE}"
echo "================================================================"

if [ "${1:-}" = "--submit" ]; then
    if [ "$NQUEUED" -gt 0 ] && [ "$FORCE" != "1" ]; then
        echo "ERROR: $NQUEUED job(s) from a previous submission of this OUTDIR are" >&2
        echo "       still in the condor queue. Concurrent jobs on the same BXs race" >&2
        echo "       on the same output files. Wait for them to drain, condor_rm them," >&2
        echo "       or re-run with FORCE=1 if you know what you are doing." >&2
        exit 1
    fi
    echo "[submit] submitting ${NJOBS} jobs ..."
    condor_submit "$SUBFILE"
    echo "[submit] monitor:  condor_q ;  tail -f ${LOGDIR}/job_${STAMP}_0.err"
    echo "[submit] then:     bash ${HERE}/harvest_bib.sh"
else
    echo "[submit] DRY RUN -- wrote ${SUBFILE} but did NOT submit. Re-run with --submit."
fi
