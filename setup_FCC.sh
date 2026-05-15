#!/bin/bash

# Source Key4hep and setup script
source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2024-03-10
cd FCCAnalyses
source ./setup.sh

# Check if the build directory exists
if [ ! -d "build" ]; then
    fccanalysis build -j 8
else
    echo "FCCAnalyses is already built."
    echo "If you want to rebuild it, please run:"
    echo "cd FCCAnalyses"
    echo "source ./setup.sh"
    echo "fccanalysis build -j 8"
    echo "cd .."
fi

cd ../

# Set LOCAL_DIR to the directory of this script
export LOCAL_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
export PYTHONPATH=${LOCAL_DIR}/python:${PYTHONPATH}