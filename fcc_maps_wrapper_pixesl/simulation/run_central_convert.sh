#!/usr/bin/env bash
#
# run_central_convert.sh  -  one HTCondor job: convert N centrally-simulated
#                            BIB bunch crossings to PixESL CSV (NO Geant4).
#
#   run_central_convert.sh PROC NBX BXLIST COMPACT SRCDIR OUTDIR
#
#   BXLIST    one bx id per line; this job handles lines [PROC*NBX, PROC*NBX+NBX)
#   SRCDIR    central sim files: output_<bx>.root (EDM4hep, 1 event = 1 BX)
#   OUTDIR    writes OUTDIR/csv/bx_<bx>{.csv,_extended.csv,.metadata.json}
#
# Converter runs in --mode resegment: layer/module/sensor decoded from the
# cellID (pitch-independent), COL/ROW re-binned from the hit POSITION on the
# 20um MAPS grid (central files were simulated at the stock 50x150um pitch;
# sensor material/geometry identical, so the SimHits are valid for our
# detector - validated vs native 20um files 2026-07-09).
# Fixed frame offsets 465/495 -> local addresses [0,930)x[0,990) as always.
#
# Same reliability rules as run_bib_chunk.sh: BIB_-prefixed vars (setup
# clobbers generic names), atomic finalize (csv LAST = resume marker),
# per-BX skip -> resubmission-safe. Reads the READ-ONLY central mirror.

BIB_PROC="$1"
BIB_NBX="$2"
BIB_LIST="$3"
BIB_COMPACT="$4"
BIB_SRC="$5"
BIB_OUT="$6"

BIB_COLOFF=465
BIB_ROWOFF=495

BIB_REPO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." >/dev/null 2>&1 && pwd )"
BIB_CONVERTER="${BIB_REPO_ROOT}/fcc_maps_wrapper_pixesl/conversion/convert_simhits_to_pixesl.py"
BIB_SCRATCH="${_CONDOR_SCRATCH_DIR:-$(mktemp -d)}/cc_${BIB_PROC}"

echo "[cc $BIB_PROC] host=$(hostname)  nbx=$BIB_NBX  scratch=$BIB_SCRATCH"
mkdir -p "$BIB_OUT/csv" "$BIB_SCRATCH"

set --
# shellcheck source=/dev/null
source "${BIB_REPO_ROOT}/setup_MAPS.sh" >/dev/null 2>&1
command -v python3 >/dev/null 2>&1 || { echo "[cc $BIB_PROC] ERROR: no python3" >&2; exit 1; }
[ -f "$BIB_COMPACT" ]   || { echo "[cc $BIB_PROC] ERROR: missing compact $BIB_COMPACT" >&2; exit 1; }
[ -f "$BIB_LIST" ]      || { echo "[cc $BIB_PROC] ERROR: missing bx list $BIB_LIST" >&2; exit 1; }
[ -f "$BIB_CONVERTER" ] || { echo "[cc $BIB_PROC] ERROR: missing converter $BIB_CONVERTER" >&2; exit 1; }

BIB_FIRST=$(( BIB_PROC * BIB_NBX + 1 ))
BIB_IDS=$(sed -n "${BIB_FIRST},$(( BIB_FIRST + BIB_NBX - 1 ))p" "$BIB_LIST")
[ -n "$BIB_IDS" ] || { echo "[cc $BIB_PROC] nothing to do"; exit 0; }

bib_finalize() {
    bib_fin_tmp="$(dirname "$2")/.$(basename "$2").tmp.$$"
    cp "$1" "$bib_fin_tmp" && mv "$bib_fin_tmp" "$2"
}

bib_nfail=0
for bx in $BIB_IDS; do
    bib_src="${BIB_SRC}/output_${bx}.root"
    bib_csvout="${BIB_OUT}/csv/bx_${bx}.csv"

    if [ -s "$bib_csvout" ]; then
        echo "[cc $BIB_PROC] bx $bx already done, skipping"
        continue
    fi
    if [ ! -s "$bib_src" ]; then
        echo "[cc $BIB_PROC] ERROR: missing input $bib_src" >&2
        bib_nfail=$((bib_nfail+1)); continue
    fi

    bib_csvtmp="${BIB_SCRATCH}/bx_${bx}.csv"
    python3 "$BIB_CONVERTER" \
        --input "$bib_src" \
        --output "$bib_csvtmp" \
        --mode resegment \
        --compact "$BIB_COMPACT" \
        --geometry    "${BIB_REPO_ROOT}/fcc_maps_wrapper_pixesl/conversion/geometry_config.yaml" \
        --collections "${BIB_REPO_ROOT}/fcc_maps_wrapper_pixesl/conversion/collections_config.yaml" \
        --allow-empty \
        --col-offset "$BIB_COLOFF" --row-offset "$BIB_ROWOFF" \
        --bx-offset "$bx"
    bib_rc=$?
    if [ $bib_rc -ne 0 ] || [ ! -f "$bib_csvtmp" ]; then
        echo "[cc $BIB_PROC] ERROR: converter failed for bx $bx (rc=$bib_rc)" >&2
        bib_nfail=$((bib_nfail+1)); continue
    fi
    bib_ok=1
    bib_finalize "${BIB_SCRATCH}/bx_${bx}_extended.csv" "${BIB_OUT}/csv/bx_${bx}_extended.csv" || bib_ok=0
    bib_finalize "${BIB_SCRATCH}/bx_${bx}.metadata.json" "${BIB_OUT}/csv/bx_${bx}.metadata.json" || bib_ok=0
    if [ $bib_ok -eq 1 ]; then
        bib_finalize "$bib_csvtmp" "$bib_csvout" || bib_ok=0
    fi
    if [ $bib_ok -ne 1 ]; then
        echo "[cc $BIB_PROC] ERROR: finalize failed for bx $bx" >&2
        bib_nfail=$((bib_nfail+1)); continue
    fi
    rm -f "$bib_csvtmp" "${BIB_SCRATCH}/bx_${bx}_extended.csv" "${BIB_SCRATCH}/bx_${bx}.metadata.json"
    echo "[cc $BIB_PROC] bx $bx done -> $(( $(wc -l < "$bib_csvout") - 1 )) hits"
done

[ -n "${_CONDOR_SCRATCH_DIR:-}" ] || rm -rf "$BIB_SCRATCH"
echo "[cc $BIB_PROC] finished, failures: $bib_nfail"
exit $(( bib_nfail > 0 ? 1 : 0 ))
