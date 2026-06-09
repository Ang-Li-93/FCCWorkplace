#!/usr/bin/env bash
#
# run_rz_plots.sh  -  self-contained condor job: build the r-z layout/occupancy
# plots over ALL chunk files (reads gpfs directly, writes to results/).
#
# Minimal env on purpose (no set -e/-u): plain `set --` so setup_MAPS.sh does not
# parse condor args, plain source, plain python.

set --
REPO=/gpfs/mnt/gpfs01/usfcc/ali3/FCCWorkplace
source "$REPO/setup_MAPS.sh"

echo "[rz-condor] host=$(hostname)  $(date)"
python "$REPO/fcc_maps_wrapper_pixesl/analysis/plot_rz_layout.py" \
    --indir   /gpfs/mnt/gpfs01/usfcc/MAPS_storage/generation/edm4hep/winter2023/wzp6_ee_qq_ecm91p2 \
    --compact "$REPO/k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01.xml" \
    --outdir  "$REPO/fcc_maps_wrapper_pixesl/results/qq_10k" \
    --nfiles 200 --mode both --refresh
rc=$?
echo "[rz-condor] python exit=$rc  $(date)"
exit $rc
