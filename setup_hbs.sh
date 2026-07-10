#!/bin/bash
# Hbs (winter2023) environment.
#
# This is the legacy stack used by H->bs studies on winter2023 IDEA fastsim
# samples. It is NOT the same as setup.sh — do not mix.
#
# Why two environments:
#   The current Key4hep stack (2026-02-01+) and recent FCCAnalyses changes
#   (PR #481) are incompatible with winter2023 samples (renamed EDM4hep types,
#   missing dN/dX association branches, TrackerHitData -> TrackerHit3DData).
#   Confirmed by FCCAnalyses maintainer Juraj Smiesko, FCCSW forum thread:
#     https://fccsw-forum.web.cern.ch/t/fcc-tutorial-2-4-2-part-ii-...-trackerhitdata.../253/2
#   The maintainer-recommended workaround is Key4hep 2024-03-10 + the
#   pre-edm4hep1 branch of FCCAnalyses. We pin a commit (af5cf61) on top of
#   pre-edm4hep1 that also carries the HiggsTools and Z-builder additions so
#   the H->bs script can use the same HiggsTools API as ZH_XSec / HiggsMass.
#
# When the upstream "new campaign" samples land, this script and the
# FCCAnalyses-winter2023/ submodule become obsolete: switch Hbs's processList
# to the new samples and run from setup.sh like every other analysis.
#
# Usage:
#   source setup_hbs.sh                  # normal setup (auto-build on first run)
#   source setup_hbs.sh --rebuild-fcc    # force FCCAnalyses rebuild
#   source setup_hbs.sh --rebuild-venv   # force venv rebuild
#   source setup_hbs.sh --rebuild        # force both
#   source setup_hbs.sh --help

REBUILD_FCC=0
REBUILD_VENV=0
for arg in "$@"; do
    case "$arg" in
        --rebuild-fcc)  REBUILD_FCC=1 ;;
        --rebuild-venv) REBUILD_VENV=1 ;;
        --rebuild)      REBUILD_FCC=1; REBUILD_VENV=1 ;;
        -h|--help)
            echo "Usage: source setup_hbs.sh [--rebuild-fcc] [--rebuild-venv] [--rebuild]"
            return 0 2>/dev/null || exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            return 1 2>/dev/null || exit 1
            ;;
    esac
done

HBS_LOCAL_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
FCCANA_DIR="$HBS_LOCAL_DIR/FCCAnalyses-winter2023"
VENV_DIR="$HBS_LOCAL_DIR/local_env_winter2023"  # separate from local_env/ — different Python

# Key4hep stack (winter2023-compatible)
source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2024-03-10

# FCCAnalyses (pre-edm4hep1 era + HiggsTools, pinned at af5cf61).
# Note: FCCAnalyses/setup.sh re-exports LOCAL_DIR to its own dir, so we run it
# inside a subshell-like function and ignore that side effect.
_fccana_setup() {
    cd "$FCCANA_DIR" || return 1
    source ./setup.sh
    if [ "$REBUILD_FCC" -eq 1 ] || [ ! -d "build" ]; then
        fccanalysis build -j 8
    else
        echo "FCCAnalyses-winter2023 already built (pass --rebuild-fcc to force rebuild)."
    fi
}
_fccana_setup
unset -f _fccana_setup

export LOCAL_DIR="$HBS_LOCAL_DIR"  # restore after FCCAnalyses overrode it
cd "$LOCAL_DIR"
# export LOCAL_DIR="$FCCANA_DIR"
#export FCCAnalyses=1  
# cd "$HBS_LOCAL_DIR"


# Local Python venv, separate from setup.sh's local_env/ (different Key4hep
# Python; binaries are not cross-compatible).
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
echo "==> Hbs environment ready"
echo "    Key4hep stack: 2024-03-10  (winter2023-compatible)"
echo "    FCCAnalyses:   FCCAnalyses-winter2023/ @ $(git -C "$FCCANA_DIR" rev-parse --short HEAD 2>/dev/null)"
echo "    venv:          $(basename "$VENV_DIR")/"
echo
