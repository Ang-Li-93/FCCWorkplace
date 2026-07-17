#!/usr/bin/env bash
# Run a combine command inside the FCCSW combine-standalone Singularity image.
#
# Usage:
#   ./run_combine.sh <command> [args...]
#
# Examples:
#   ./run_combine.sh text2workspace.py datacard.txt
#   ./run_combine.sh combine -M MultiDimFit datacard.root --algo grid
#   ./run_combine.sh combineTool.py -M Impacts -d ws.root -m 125 --doInitialFit
#
# Override the image with COMBINE_IMG=/path/to/other.sif if needed.

set -euo pipefail

IMG="${COMBINE_IMG:-/eos/project/f/fccsw-web/www/analysis/auxiliary/combine-standalone_v9.2.1.sif}"

if [[ $# -eq 0 ]]; then
    sed -n '2,12p' "$0"
    exit 2
fi

if [[ ! -f "$IMG" ]]; then
    echo "Combine image not found: $IMG" >&2
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

exec "$RUNNER" exec --bind /afs,/eos,/cvmfs,/tmp --pwd "$PWD" "$IMG" "$@"
