#!/bin/bash
# FCCWorkplace setup: sources Key4hep, builds FCCAnalyses if needed,
# creates/activates the local Python venv (layered on Key4hep).
#
# Usage:
#   source setup.sh                  # normal setup (auto-build on first run)
#   source setup.sh --rebuild-fcc    # force FCCAnalyses rebuild
#   source setup.sh --rebuild-venv   # force venv rebuild
#   source setup.sh --rebuild        # force both
#   source setup.sh --help

REBUILD_FCC=0
REBUILD_VENV=0
for arg in "$@"; do
    case "$arg" in
        --rebuild-fcc)  REBUILD_FCC=1 ;;
        --rebuild-venv) REBUILD_VENV=1 ;;
        --rebuild)      REBUILD_FCC=1; REBUILD_VENV=1 ;;
        -h|--help)
            echo "Usage: source setup.sh [--rebuild-fcc] [--rebuild-venv] [--rebuild]"
            return 0 2>/dev/null || exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            return 1 2>/dev/null || exit 1
            ;;
    esac
done

export LOCAL_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Key4hep stack
source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2026-04-08

# FCCAnalyses — wrap in a function so our positional args don't reach
# FCCAnalyses/setup.sh (which errors on unknown options).
_fccana_setup() {
    cd "$LOCAL_DIR/FCCAnalyses" || return 1
    source ./setup.sh
    if [ "$REBUILD_FCC" -eq 1 ] || [ ! -d "build" ]; then
        fccanalysis build -j 8
    else
        echo "FCCAnalyses already built (pass --rebuild-fcc to force rebuild)."
    fi
    cd "$LOCAL_DIR"
}
_fccana_setup
unset -f _fccana_setup

# Local Python venv, layered on Key4hep's python so Key4hep packages remain visible
if [ "$REBUILD_VENV" -eq 1 ] && [ -d "$LOCAL_DIR/local_env" ]; then
    echo "Removing existing venv at $LOCAL_DIR/local_env"
    rm -rf "$LOCAL_DIR/local_env"
fi
if [ ! -d "$LOCAL_DIR/local_env" ]; then
    echo "Creating local_env with --system-site-packages"
    python3 -m venv --system-site-packages "$LOCAL_DIR/local_env"
    source "$LOCAL_DIR/local_env/bin/activate"
    pip install --upgrade pip
    pip install -r "$LOCAL_DIR/requirements.txt"
else
    source "$LOCAL_DIR/local_env/bin/activate"
fi

export PYTHONPATH=${PYTHONPATH}:${LOCAL_DIR}/python
