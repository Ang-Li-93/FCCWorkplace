#!/bin/bash
# setup_MAPS.sh
# =============
# One-shot environment for the FCC-ee MAPS-wrapper -> PixESL project
# (fcc_maps_wrapper_pixesl). Pins the Key4hep release and wires the editable
# k4geo / k4Reco forks, then delegates to the repo's setup script.
#
# Usage:
#   source setup_MAPS.sh                 # stable release + local forks (if present)
#   source setup_MAPS.sh --no-local      # ignore local forks, use CVMFS geometry
#   source setup_MAPS.sh --help
#
# Pinned versions for this project (override by exporting before sourcing):
#   KEY4HEP_RELEASE   stable release date         (default: 2026-04-08)
#   ALLEGRO_BASE      dir holding the k4geo/k4Reco submodules
#                                                  (default: this FCCWorkplace dir)
#   LOCAL_K4GEO       k4geo dir that contains FCCee/  (auto from ALLEGRO_BASE)
#   K4RECO_DIR        built k4Reco repo               (auto from ALLEGRO_BASE)
#   ALLEGRO_VERSION   detector version, e.g. ALLEGRO_o1_v03 (default: latest found)
#
# k4geo / k4Reco live as git submodules under FCCWorkplace (./k4geo, ./k4Reco).
# If missing, add them with:
#   bash fcc_maps_wrapper_pixesl/setup/clone_local_forks.sh   (needs GitHub SSH)

_USE_LOCAL=1
for arg in "$@"; do
    case "$arg" in
        --no-local) _USE_LOCAL=0 ;;
        -h|--help)
            echo "Usage: source setup_MAPS.sh [--no-local]"
            echo "  pins KEY4HEP_RELEASE (default 2026-04-08) and wires the"
            echo "  k4geo/k4Reco forks under ALLEGRO_BASE for this project."
            return 0 2>/dev/null || exit 0
            ;;
        *) echo "Unknown option: $arg"; return 1 2>/dev/null || exit 1 ;;
    esac
done

# --- locate this script / the project repo --------------------------------
export LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
_MAPS_REPO="${LOCAL_DIR}/fcc_maps_wrapper_pixesl"
if [ ! -f "${_MAPS_REPO}/setup/setup_key4hep.sh" ]; then
    echo "ERROR: cannot find ${_MAPS_REPO}/setup/setup_key4hep.sh" >&2
    return 1 2>/dev/null || exit 1
fi

# --- pinned project versions ----------------------------------------------
export KEY4HEP_RELEASE="${KEY4HEP_RELEASE:-2026-04-08}"   # matches setup.sh pin
# k4geo/k4Reco are submodules under FCCWorkplace by default.
ALLEGRO_BASE="${ALLEGRO_BASE:-${LOCAL_DIR}}"

# --- wire local editable forks (only if present) --------------------------
if [ "$_USE_LOCAL" -eq 1 ]; then
    # k4geo geometry dir: prefer a source checkout root, else share/k4geo.
    if [ -z "${LOCAL_K4GEO:-}" ]; then
        for _cand in "${ALLEGRO_BASE}/k4geo" "${ALLEGRO_BASE}/k4geo/share/k4geo"; do
            if [ -d "${_cand}/FCCee/ALLEGRO" ]; then
                export LOCAL_K4GEO="${_cand}"
                break
            fi
        done
    fi
    if [ -z "${K4RECO_DIR:-}" ] && [ -d "${ALLEGRO_BASE}/k4Reco" ]; then
        export K4RECO_DIR="${ALLEGRO_BASE}/k4Reco"
    fi

    if [ -z "${LOCAL_K4GEO:-}" ]; then
        echo "[setup_MAPS] No local k4geo fork found under ${ALLEGRO_BASE}/k4geo;"
        echo "[setup_MAPS]   using central CVMFS geometry. To set up your forks:"
        echo "[setup_MAPS]   bash ${_MAPS_REPO}/setup/clone_local_forks.sh"
    fi
else
    echo "[setup_MAPS] --no-local: ignoring forks, using CVMFS geometry."
    unset LOCAL_K4GEO K4RECO_DIR
fi

echo "[setup_MAPS] KEY4HEP_RELEASE = ${KEY4HEP_RELEASE}"
echo "[setup_MAPS] LOCAL_K4GEO     = ${LOCAL_K4GEO:-<central CVMFS>}"
echo "[setup_MAPS] K4RECO_DIR      = ${K4RECO_DIR:-<none>}"

# --- delegate to the repo setup (sources Key4hep, k4_local_repo, records env)
# shellcheck source=/dev/null
source "${_MAPS_REPO}/setup/setup_key4hep.sh"

echo "[setup_MAPS] Ready. Project repo: ${_MAPS_REPO}"
