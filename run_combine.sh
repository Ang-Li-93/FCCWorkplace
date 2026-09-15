#!/usr/bin/env bash
# Run a command inside the CMS Combine standalone container (the FCCSW
# recommended way to get Combine; neither key4hep nor FCCAnalyses ship it).
#
# Usage:
#   ./run_combine.sh <command> [args...]
#
# Examples:
#   ./run_combine.sh text2workspace.py datacard.txt
#   ./run_combine.sh combine -M MultiDimFit datacard.root --algo grid
#   ./run_combine.sh combineTool.py -M Impacts -d ws.root -m 125 --doInitialFit
#   ./run_combine.sh python3 analysis/Hbs/mumu/combine/run_fits.py
#   ./run_combine.sh bash          # interactive shell inside the image
#
# Image resolution (first that exists), override with COMBINE_IMG=...:
#   1. unpacked image on cvmfs (works on SDCC and lxplus)
#   2. FCCSW .sif on /eos (lxplus only)
# The working directory is preserved; the usual site filesystems are bound
# when present (/afs /eos /cvmfs /tmp /gpfs /usatlas).

set -euo pipefail

CANDIDATES=(
    /cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/cms-cloud/combine-standalone:latest
    /eos/project/f/fccsw-web/www/analysis/auxiliary/combine-standalone_v9.2.1.sif
)

if [[ $# -eq 0 ]]; then
    sed -n '2,20p' "$0"
    exit 2
fi

IMG="${COMBINE_IMG:-}"
if [[ -z "$IMG" ]]; then
    for c in "${CANDIDATES[@]}"; do
        if [[ -e "$c" ]]; then IMG="$c"; break; fi
    done
fi
if [[ -z "$IMG" || ! -e "$IMG" ]]; then
    echo "Combine image not found (tried: ${COMBINE_IMG:-${CANDIDATES[*]}})" >&2
    exit 1
fi

if command -v apptainer >/dev/null 2>&1; then
    RUNNER=apptainer
elif command -v singularity >/dev/null 2>&1; then
    RUNNER=singularity
else
    echo "Neither apptainer nor singularity is on PATH." >&2
    exit 1
fi

BINDS=()
for p in /afs /eos /cvmfs /tmp /gpfs /usatlas; do
    [[ -e "$p" ]] && BINDS+=(--bind "$p")
done

exec "$RUNNER" exec "${BINDS[@]}" --pwd "$PWD" "$IMG" "$@"
