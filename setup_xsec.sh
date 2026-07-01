#!/bin/bash
# ZH cross-section (ZH_XSec) environment.
#
# This is the LATEST stack used for the ZH cross-section paper work:
#   Key4hep 2026-04-08 + FCCAnalyses/ on the AngDev branch (synced to upstream),
#   which carries the HiggsTools additions (coneIsolation, coneIsolationRapidity,
#   resonance/recoil builders, ...).
#
# It is the same stack as setup.sh, but labeled for the x-section analysis and it
# checks that FCCAnalyses is on AngDev. Do NOT mix with setup_hbs.sh (winter2023).
#
# Note on libraries:
#   `fccanalysis run <script>.py` auto-loads libFCCAnalyses and the analyzer headers.
#   A bare `python script.py` does NOT — such a script must do, near the top:
#       ROOT.gSystem.Load("libFCCAnalyses")
#       ROOT.gInterpreter.Declare('#include "FCCAnalyses/ReconstructedParticle.h"')
#       ROOT.gInterpreter.Declare('#include "FCCAnalyses/HiggsTools.h"')
#   This script puts the lib/headers on LD_LIBRARY_PATH / ROOT_INCLUDE_PATH (via
#   FCCAnalyses/setup.sh) so both forms resolve the symbols.
#
# Usage:
#   source setup_xsec.sh                  # normal setup (auto-build on first run)
#   source setup_xsec.sh --rebuild-fcc    # force FCCAnalyses rebuild
#   source setup_xsec.sh --rebuild-venv   # force venv rebuild
#   source setup_xsec.sh --rebuild        # force both
#   source setup_xsec.sh --help

REBUILD_FCC=0
REBUILD_VENV=0
for arg in "$@"; do
    case "$arg" in
        --rebuild-fcc)  REBUILD_FCC=1 ;;
        --rebuild-venv) REBUILD_VENV=1 ;;
        --rebuild)      REBUILD_FCC=1; REBUILD_VENV=1 ;;
        -h|--help)
            echo "Usage: source setup_xsec.sh [--rebuild-fcc] [--rebuild-venv] [--rebuild]"
            return 0 2>/dev/null || exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            return 1 2>/dev/null || exit 1
            ;;
    esac
done

XSEC_LOCAL_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
FCCANA_DIR="$XSEC_LOCAL_DIR/FCCAnalyses"
VENV_DIR="$XSEC_LOCAL_DIR/local_env"

# Key4hep stack (latest pinned)
source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2026-04-08

# Warn if FCCAnalyses is not on the expected AngDev branch
_xsec_branch=$(git -C "$FCCANA_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null)
if [ "$_xsec_branch" != "AngDev" ]; then
    echo "----> Warning: FCCAnalyses is on '$_xsec_branch', expected 'AngDev'."
    echo "      Run: git -C $FCCANA_DIR checkout AngDev"
fi
unset _xsec_branch

# FCCAnalyses (AngDev). FCCAnalyses/setup.sh re-exports LOCAL_DIR to its own dir,
# so run it in a function and restore LOCAL_DIR afterwards.
_fccana_setup() {
    cd "$FCCANA_DIR" || return 1
    source ./setup.sh
    if [ "$REBUILD_FCC" -eq 1 ] || [ ! -d "build" ]; then
        fccanalysis build -j 8
    else
        echo "FCCAnalyses already built (pass --rebuild-fcc to force rebuild)."
    fi
}
_fccana_setup
unset -f _fccana_setup
export LOCAL_DIR="$XSEC_LOCAL_DIR"  # restore after FCCAnalyses overrode it
cd "$LOCAL_DIR"

# Local Python venv, layered on Key4hep's python
if [ "$REBUILD_VENV" -eq 1 ] && [ -d "$VENV_DIR" ]; then
    echo "Removing existing venv at $VENV_DIR"
    rm -rf "$VENV_DIR"
fi
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating $(basename "$VENV_DIR") with --system-site-packages"
    python3 -m venv --system-site-packages "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip
    pip install -r "$LOCAL_DIR/requirements.txt"
else
    source "$VENV_DIR/bin/activate"
fi

export PYTHONPATH=${PYTHONPATH}:${LOCAL_DIR}/python

echo
echo "==> ZH_XSec environment ready"
echo "    Key4hep stack: 2026-04-08  (latest)"
echo "    FCCAnalyses:   FCCAnalyses/ @ $(git -C "$FCCANA_DIR" rev-parse --short HEAD 2>/dev/null) ($(git -C "$FCCANA_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null))"
echo "    venv:          $(basename "$VENV_DIR")/"
echo
