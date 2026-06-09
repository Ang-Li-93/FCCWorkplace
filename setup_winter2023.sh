#!/bin/bash
# setup_winter2023.sh
# ===================
# Environment for GENERATING winter2023 FCC-ee fastsim MC (Pythia8 + Delphes)
# through the EventProducer driver. This is the *production* side.
#
#   - setup_winter2023.sh  -> generate winter2023 fastsim samples (this file)
#   - setup_hbs.sh         -> ANALYSE winter2023 samples with FCCAnalyses
# These are different stacks; do not mix them in one shell.
#
# What this sets up:
#   1. The EventProducer driver environment (Key4hep stack + PYTHONPATH so that
#      `import EventProducer.common...` resolves, EVENTPRODUCER, EOS_MGM_URL).
#      This comes straight from EventProducer/init.sh, the canonical (SDCC-
#      adapted) setup, so the submission node matches the rest of the repo.
#   2. PRODTAG=winter2023 — the production tag passed to run.py. The actual
#      generation *jobs* source the winter2023 Key4hep stack
#      (spackages6/.../2022-12-23, see prodTag['winter2023'] in
#      config/param_FCCee.py); this happens inside the job script, not here.
#
# Cards live in FCC-config/winter2023/FCCee/ (Pythia8 *.cmd, Delphes *.tcl).
# I/O is redirected to the local group area under
#   /gpfs/mnt/gpfs01/usfcc/MAPS_storage/   (see param_FCCee.py).
#
# Usage:
#   source setup_winter2023.sh
#   source setup_winter2023.sh --help
#
# Then drive production from this directory (FCCWorkplace), e.g.:
#
#   # Submit 10 jobs x 10000 events of a Pythia8 process, IDEA fastsim, condor:
#   python EventProducer/bin/run.py --FCCee --reco --send --condor \
#       -p p8_ee_Hbb_ecm240 -n 10000 -N 10 \
#       --prodtag $PRODTAG --detector IDEA
#
#   # Local test of a single job (no condor):
#   python EventProducer/bin/run.py --FCCee --reco --send --local \
#       -p p8_ee_Hbb_ecm240 -n 100 -N 1 \
#       --prodtag $PRODTAG --detector IDEA
#
#   # Bookkeeping (check / merge yaml / make proc dict):
#   python EventProducer/bin/run.py --FCCee --reco --check  --prodtag $PRODTAG --detector IDEA
#   python EventProducer/bin/run.py --FCCee --reco --merge  --prodtag $PRODTAG --detector IDEA
#
# Detector choices: IDEA, IDEA_3T, IDEA_FullSilicon.

for arg in "$@"; do
    case "$arg" in
        -h|--help)
            echo "Usage: source setup_winter2023.sh"
            echo "  Sets up the EventProducer driver env and PRODTAG=winter2023"
            echo "  for generating FCC-ee winter2023 fastsim (Pythia8 + Delphes) MC."
            echo "  Drive with: python EventProducer/bin/run.py --FCCee --reco --send ... \\"
            echo "                  --prodtag \$PRODTAG --detector IDEA"
            return 0 2>/dev/null || exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            return 1 2>/dev/null || exit 1
            ;;
    esac
done

export LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_EP_DIR="${LOCAL_DIR}/EventProducer"

if [ ! -f "${_EP_DIR}/init.sh" ]; then
    echo "ERROR: cannot find ${_EP_DIR}/init.sh" >&2
    echo "       Is the EventProducer submodule checked out?" >&2
    echo "       Try: git submodule update --init EventProducer" >&2
    return 1 2>/dev/null || exit 1
fi

# EventProducer/init.sh sources the driver Key4hep stack and sets EVENTPRODUCER,
# PYTHONPATH (= EventProducer's parent, so the package imports), and EOS_MGM_URL.
# It uses $PWD, so source it from inside the EventProducer dir, then return.
_winter2023_setup() {
    cd "${_EP_DIR}" || return 1
    # shellcheck source=/dev/null
    source ./init.sh
    cd "${LOCAL_DIR}" || return 1
}
_winter2023_setup
_rc=$?
unset -f _winter2023_setup
if [ "${_rc}" -ne 0 ]; then
    echo "ERROR: EventProducer/init.sh failed." >&2
    return 1 2>/dev/null || exit 1
fi
unset _rc

# Production tag selecting winter2023 cards + the winter2023 Key4hep stack on
# the worker (config/param_FCCee.py: prodTag['winter2023']).
export PRODTAG="winter2023"

echo
echo "==> winter2023 fastsim MC-generation environment ready"
echo "    EVENTPRODUCER : ${EVENTPRODUCER}"
echo "    PRODTAG       : ${PRODTAG}"
echo "    cards         : ${LOCAL_DIR}/FCC-config/winter2023/FCCee/"
echo "    drive from    : ${LOCAL_DIR}  (python EventProducer/bin/run.py ...)"
echo "    example       : python EventProducer/bin/run.py --FCCee --reco --send --condor \\"
echo "                        -p p8_ee_Hbb_ecm240 -n 10000 -N 10 --prodtag \$PRODTAG --detector IDEA"
echo
