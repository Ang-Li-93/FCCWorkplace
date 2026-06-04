#!/usr/bin/env bash
#
# run_whizard.sh
# --------------
# Generate e+e- -> Z -> inclusive events with WHIZARD for ddsim.
#
#   bash generation/run_whizard.sh [N_EVENTS]
#
# Writes the generator file to outputs/z_inclusive_gen.hepmc (the default that
# simulation/run_ddsim_zinclusive.sh expects). The number of events is patched
# into a temporary copy of generation/whizard_z_inclusive.sin so the committed
# steering file stays clean.

set -euo pipefail

HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REPO_ROOT="$( cd "$HERE/.." >/dev/null 2>&1 && pwd )"
OUTDIR="${REPO_ROOT}/outputs"
mkdir -p "$OUTDIR"

N_EVENTS="${1:-1000}"
SIN_SRC="$HERE/whizard_z_inclusive.sin"
WORKDIR="${OUTDIR}/whizard_work"
mkdir -p "$WORKDIR"

if ! command -v whizard >/dev/null 2>&1; then
    echo "ERROR: 'whizard' not found in PATH." >&2
    echo "       It is part of the Key4hep stack: source setup/setup_key4hep.sh" >&2
    echo "       (If still missing, your stack may not bundle WHIZARD; see" >&2
    echo "        generation/README_generation.md for alternatives.)" >&2
    exit 1
fi
if [ ! -f "$SIN_SRC" ]; then
    echo "ERROR: steering file not found: $SIN_SRC" >&2
    exit 1
fi

# Patch n_events into a working copy.
SIN_RUN="${WORKDIR}/whizard_z_inclusive.sin"
sed -E "s/^n_events = .*/n_events = ${N_EVENTS}/" "$SIN_SRC" > "$SIN_RUN"

echo "[whizard] events    : $N_EVENTS"
echo "[whizard] steering  : $SIN_RUN"
echo "[whizard] workdir   : $WORKDIR"

( cd "$WORKDIR" && whizard "$SIN_RUN" )

# WHIZARD writes z_inclusive_gen.hepmc in the workdir; move it to OUTDIR.
GEN="$WORKDIR/z_inclusive_gen.hepmc"
if [ ! -f "$GEN" ]; then
    # some versions append .hepmc2 / .hepmc3 — grab the newest matching file
    GEN=$(find "$WORKDIR" -maxdepth 1 -name "z_inclusive_gen*.hepmc*" 2>/dev/null \
            | sort | tail -1)
fi
if [ -z "${GEN:-}" ] || [ ! -f "$GEN" ]; then
    echo "ERROR: WHIZARD finished but no z_inclusive_gen*.hepmc produced." >&2
    echo "       Check $WORKDIR for the actual output name/format." >&2
    exit 1
fi

DEST="${OUTDIR}/z_inclusive_gen.hepmc"
cp -f "$GEN" "$DEST"
echo "[whizard] generator file -> $DEST"
echo "[whizard] next: bash simulation/run_ddsim_zinclusive.sh $N_EVENTS $DEST"
