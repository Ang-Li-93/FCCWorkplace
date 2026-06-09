#!/usr/bin/env bash
#
# harvest_pixesl.sh  -  merge all ddsim chunk files into ONE PixESL CSV + plots.
#
#   NPER=50 bash harvest_pixesl.sh [--plot]
#
# Uses conversion/harvest_convert.py (loads the dd4hep decoder ONCE and streams
# every events_<chunk>.edm4hep.root, global BX = chunk*NPER + event), then runs
# the summary and (with --plot) the PDF plots.
#
# Env: NPER, OUTDIR, COMPACT, GEOMETRY, COLLECTIONS, FINAL_CSV

set -euo pipefail
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REPO_ROOT="$( cd "$HERE/../.." >/dev/null 2>&1 && pwd )"
PKG="${REPO_ROOT}/fcc_maps_wrapper_pixesl"

NPER="${NPER:-50}"
OUTDIR="${OUTDIR:-/gpfs/mnt/gpfs01/usfcc/MAPS_storage/generation/edm4hep/winter2023/wzp6_ee_qq_ecm91p2}"
COMPACT="${COMPACT:-${REPO_ROOT}/k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01.xml}"
GEOMETRY="${GEOMETRY:-${PKG}/conversion/geometry_config.yaml}"
COLLECTIONS="${COLLECTIONS:-${PKG}/conversion/collections_config.yaml}"
FINAL_CSV="${FINAL_CSV:-/gpfs/mnt/gpfs01/usfcc/MAPS_storage/pixesl_qq_10k.csv}"   # large data -> MAPS_storage
PLOTDIR="${PLOTDIR:-${PKG}/results/qq_10k}"  # plots + CSV; git-ignored, published to angli-share.web.cern.ch/FCC/MAPS

command -v python >/dev/null 2>&1 || { echo "ERROR: source setup_MAPS.sh first" >&2; exit 1; }
N=$(ls "${OUTDIR}"/events_*.edm4hep.root 2>/dev/null | wc -l)
[ "$N" -gt 0 ] || { echo "ERROR: no events_*.edm4hep.root in $OUTDIR" >&2; exit 1; }
echo "[harvest] ${N} chunk files in $OUTDIR  (NPER=${NPER})"

python "${PKG}/conversion/harvest_convert.py" \
    --indir "$OUTDIR" --output "$FINAL_CSV" --nper "$NPER" \
    --compact "$COMPACT" --geometry "$GEOMETRY" --collections "$COLLECTIONS"

echo "[harvest] summary:"
python "${PKG}/analysis/summarize_pixesl_hits.py" "$FINAL_CSV" || true
if [ "${1:-}" = "--plot" ]; then
    python "${PKG}/analysis/plot_pixesl_hits.py"    "$FINAL_CSV" --outdir "$PLOTDIR"
    python "${PKG}/analysis/plot_readout_metrics.py" "${FINAL_CSV%.csv}_extended.csv" --outdir "$PLOTDIR"
    echo "[harvest] plots -> $PLOTDIR"
fi
# collect the CSV deliverables next to the plots (results/ is git-ignored, published to the share site)
mkdir -p "$PLOTDIR"
cp -p "$FINAL_CSV" "${FINAL_CSV%.csv}_extended.csv" "${FINAL_CSV%.csv}.metadata.json" "$PLOTDIR"/ 2>/dev/null || true
echo "[harvest] results (plots + CSV) -> $PLOTDIR  (upload to https://angli-share.web.cern.ch/FCC/MAPS/)"
echo "[harvest] bulk CSV master copy -> $FINAL_CSV"
