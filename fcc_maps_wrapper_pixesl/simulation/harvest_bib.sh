#!/usr/bin/env bash
#
# harvest_bib.sh  -  merge per-BX PixESL CSVs from the BIB condor production.
#
#   bash harvest_bib.sh
#
# Takes ONE snapshot of the completed bx ids, then concatenates
# OUTDIR/csv/bx_<bx>.csv (and _extended.csv) in numeric BX order into
# RESULTDIR/pixesl_<TAG>.csv, and reports coverage (vs the newest bxlist) and
# hit stats -- all from the same snapshot, so counts and content agree.
# Safe while jobs run: the runner finalizes CSVs atomically (tmp+rename), so
# only complete files are visible; later files are simply not in the snapshot.
#
# NOTE: comm(1) requires LEXICOGRAPHIC order -- feeding it 'sort -n' output
# aborts with 'not in sorted order' under set -e (audit finding). We sort
# lexicographically for comm and numerically only for display.
#
# Env config:
#   OUTDIR     production output root (default: reference GHC/V24.4 IPC Z)
#   RESULTDIR  merged-output dir      (default: FCCWorkplace/outputs/BIB)
#   TAG        output name tag        (default: ipc_GHC_V24p4_Z)

set -euo pipefail
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REPO_ROOT="$( cd "$HERE/../.." >/dev/null 2>&1 && pwd )"

OUTDIR="${OUTDIR:-/gpfs/mnt/gpfs01/usfcc/MAPS_storage/BIB_derived/sim/LCC_V106.2_IPC_Z}"
RESULTDIR="${RESULTDIR:-${REPO_ROOT}/outputs/BIB}"
TAG="${TAG:-ipc_LCC_V106p2_Z}"

CSVDIR="${OUTDIR}/csv"
[ -d "$CSVDIR" ] || { echo "ERROR: missing $CSVDIR" >&2; exit 1; }
mkdir -p "$RESULTDIR"

MERGED="${RESULTDIR}/pixesl_${TAG}.csv"
MERGED_EXT="${RESULTDIR}/pixesl_${TAG}_extended.csv"
MISSING="${RESULTDIR}/pixesl_${TAG}.missing_bx.txt"

# newest bx list from the submit dir (timestamped since the audit fix)
BXLIST=$(ls -1t "${OUTDIR}/condor/"bxlist_*.txt "${OUTDIR}/condor/bxlist.txt" 2>/dev/null | head -1 || true)

# ---- ONE snapshot of completed bx ids (numeric order) ----------------------
SNAP=$(mktemp)
trap 'rm -f "$SNAP"' EXIT
ls "$CSVDIR" | sed -n 's/^bx_\([0-9]\+\)\.csv$/\1/p' | sort -n > "$SNAP"
NDONE=$(wc -l < "$SNAP")
[ "$NDONE" -gt 0 ] || { echo "ERROR: no bx_<n>.csv in $CSVDIR yet" >&2; exit 1; }

# ---- merge from the snapshot, header from the first file -------------------
merge() {  # $1 = suffix ("" or "_extended"), $2 = output
    local first=1 out="$2" f
    : > "$out"
    while read -r bx; do
        f="${CSVDIR}/bx_${bx}$1.csv"
        [ -s "$f" ] || continue
        if [ $first -eq 1 ]; then cat "$f" >> "$out"; first=0
        else tail -n +2 "$f" >> "$out"; fi
    done < "$SNAP"
}
merge ""          "$MERGED"
merge "_extended" "$MERGED_EXT"

# ---- coverage vs the submitted list (lexicographic sort for comm!) ---------
if [ -n "$BXLIST" ] && [ -s "$BXLIST" ]; then
    comm -23 <(sort "$BXLIST") <(sort "$SNAP") | sort -n > "$MISSING"
    NMISS=$(wc -l < "$MISSING")
else
    NMISS="?"; echo "(no bxlist found - coverage vs submission unknown)"
fi

# ---- workflow-contract ledger tally (ok-seed1/ok-seed2/failed-*) -----------
if [ -d "$OUTDIR/ledger" ]; then
    echo "[harvest] ledger     : $(cat "$OUTDIR"/ledger/bx_*.status 2>/dev/null | awk '{print $1}' | sort | uniq -c | sort -rn | tr '\n' ' ' | sed 's/  */ /g')"
    grep -l "^failed" "$OUTDIR"/ledger/bx_*.status 2>/dev/null | sed 's/.*bx_\([0-9]*\)\.status/\1/' > "${RESULTDIR}/pixesl_${TAG}.failed_bx.txt" || true
fi

NHITS=$(( $(wc -l < "$MERGED") - 1 ))
# unique fired pixels (BX,layer,module,sensor,COL,ROW): Geant4 step-splitting
# makes raw SimHit rows overstate fired-pixel occupancy by ~1.6x. Quote
# NPIX for absolute occupancy; raw rows are the digitization input.
NPIX=$(tail -n +2 "$MERGED_EXT" | awk -F, '{print $1","$6","$7","$8","$2","$3}' | sort -u | wc -l)
echo "================================================================"
echo "[harvest] snapshot   : ${NDONE} BXs   missing vs list: ${NMISS}$( [ "${NMISS}" != "?" ] && [ "${NMISS}" != "0" ] && echo "  (see ${MISSING})" || true )"
echo "[harvest] total hits : ${NHITS}  ($(awk -v n="$NHITS" -v b="$NDONE" 'BEGIN{if(b>0)printf "%.2f", n/b; else print "?"}') raw SimHit rows/BX on MAPS layers)"
echo "[harvest] fired px   : ${NPIX}  ($(awk -v n="$NPIX" -v b="$NDONE" 'BEGIN{if(b>0)printf "%.2f", n/b; else print "?"}') unique pixels/BX; use THIS for occupancy)"
echo "[harvest] merged     -> ${MERGED}"
echo "[harvest] extended   -> ${MERGED_EXT}"
echo "================================================================"
