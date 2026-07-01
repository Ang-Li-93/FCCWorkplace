#!/bin/bash
# Quick-source the latest FCCAnalyses environment (AngDev) — NO build, NO venv rebuild.
# Sources Key4hep + the FCCAnalyses checkout and activates the existing local_env.
#
# Use this for everyday work once things are built.
# For a first-time build or to force a rebuild, use ./setup.sh (--rebuild-fcc / --rebuild).
#
# Usage:  source env.sh

export LOCAL_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Key4hep stack (skip if already set up in this shell)
if [ -z "${KEY4HEP_STACK}" ]; then
    source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2026-04-08
else
    echo "----> Key4hep stack already set up. Skipping."
fi

# FCCAnalyses environment (latest checkout). Its setup.sh cd's internally, so restore PWD.
_here="$PWD"
cd "$LOCAL_DIR/FCCAnalyses" && source ./setup.sh
cd "$_here"; unset _here

# Local Python venv, layered on Key4hep's python
if [ -d "$LOCAL_DIR/local_env" ]; then
    source "$LOCAL_DIR/local_env/bin/activate"
else
    echo "----> Note: $LOCAL_DIR/local_env not found; run 'source setup.sh' once to create it."
fi

export PYTHONPATH=${PYTHONPATH}:${LOCAL_DIR}/python
