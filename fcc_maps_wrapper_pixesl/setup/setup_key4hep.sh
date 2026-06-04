#!/usr/bin/env bash
#
# setup_key4hep.sh
# ----------------
# Source the Key4hep software stack from CVMFS and (optionally) point the
# geometry environment at a *local, editable* k4geo clone.
#
# Usage:
#   source setup/setup_key4hep.sh            # stable CVMFS stack + central k4geo
#   LOCAL_K4GEO=/path/to/k4geo/share/k4geo source setup/setup_key4hep.sh
#   K4RECO_DIR=/gpfs/.../Allegro/k4Reco       source setup/setup_key4hep.sh
#
# Environment knobs (all optional, set before sourcing):
#   KEY4HEP_SETUP  CVMFS setup script (default: stable sw.hsf.org)
#   LOCAL_K4GEO    directory containing FCCee/  -> overrides K4GEO (editable geom)
#   K4RECO_DIR     a locally-built k4 repo (e.g. k4Reco) -> runs `k4_local_repo`
#
# After sourcing, the following are printed and saved to
#   outputs/environment_used.txt
#     KEY4HEP_STACK, K4GEO, LD_LIBRARY_PATH, PYTHONPATH, ddsim, k4run, python
#
# NOTE: this script must be *sourced*, not executed, so the environment
# persists in your shell.

# ---------------------------------------------------------------------------
# Resolve the repository root (works whether sourced from bash or zsh).
# ---------------------------------------------------------------------------
if [ -n "${BASH_SOURCE[0]:-}" ]; then
    _SETUP_SRC="${BASH_SOURCE[0]}"
else
    _SETUP_SRC="${(%):-%x}"   # zsh
fi
REPO_ROOT="$( cd "$( dirname "$_SETUP_SRC" )/.." >/dev/null 2>&1 && pwd )"
OUTDIR="${REPO_ROOT}/outputs"
mkdir -p "$OUTDIR"

# ---------------------------------------------------------------------------
# CVMFS Key4hep setup script (override with KEY4HEP_SETUP if needed).
# ---------------------------------------------------------------------------
KEY4HEP_SETUP="${KEY4HEP_SETUP:-/cvmfs/sw.hsf.org/key4hep/setup.sh}"

if [ ! -f "$KEY4HEP_SETUP" ]; then
    echo "ERROR: Key4hep setup script not found at:" >&2
    echo "         $KEY4HEP_SETUP" >&2
    echo "       Is CVMFS mounted? Try: ls /cvmfs/sw.hsf.org/key4hep/" >&2
    echo "       Or set KEY4HEP_SETUP to a valid path before sourcing." >&2
    return 1 2>/dev/null || exit 1
fi

# Optionally pin a release date (e.g. KEY4HEP_RELEASE=2026-04-08 -> `-r 2026-04-08`).
if [ -n "${KEY4HEP_RELEASE:-}" ]; then
    echo "[setup] Sourcing Key4hep stack from: $KEY4HEP_SETUP  (-r $KEY4HEP_RELEASE)"
    # shellcheck disable=SC1090
    source "$KEY4HEP_SETUP" -r "$KEY4HEP_RELEASE"
else
    echo "[setup] Sourcing Key4hep stack from: $KEY4HEP_SETUP"
    # shellcheck disable=SC1090
    source "$KEY4HEP_SETUP"
fi

# ---------------------------------------------------------------------------
# Optional: override K4GEO with a local editable clone.
#   LOCAL_K4GEO should point at the directory that contains FCCee/ALLEGRO/...
#   For a git clone of k4geo this is usually:   <clone>/k4geo   (the share dir)
#   i.e. the dir holding "FCCee". We sanity-check that below.
# ---------------------------------------------------------------------------
if [ -n "${LOCAL_K4GEO:-}" ]; then
    if [ -d "${LOCAL_K4GEO}/FCCee/ALLEGRO" ]; then
        export K4GEO="${LOCAL_K4GEO}"
        echo "[setup] Overriding K4GEO with local clone: $K4GEO"
    else
        echo "[setup] WARNING: LOCAL_K4GEO is set but '${LOCAL_K4GEO}/FCCee/ALLEGRO' was not found." >&2
        echo "[setup]          Falling back to CVMFS K4GEO: ${K4GEO}" >&2
        echo "[setup]          (LOCAL_K4GEO should be the directory that contains 'FCCee/'.)" >&2
    fi
fi

# ---------------------------------------------------------------------------
# Optional: register a locally-built k4 repository (e.g. k4Reco) so its
# libraries/algorithms take precedence over the CVMFS ones.
#   `k4_local_repo` is a helper provided by the Key4hep stack; it must be run
#   from inside the local repo directory.
# ---------------------------------------------------------------------------
if [ -n "${K4RECO_DIR:-}" ]; then
    if [ -d "${K4RECO_DIR}" ]; then
        if command -v k4_local_repo >/dev/null 2>&1; then
            echo "[setup] Registering local repo via k4_local_repo: $K4RECO_DIR"
            ( cd "${K4RECO_DIR}" && k4_local_repo ) || \
                echo "[setup] WARNING: k4_local_repo returned non-zero (is it built/installed?)." >&2
        else
            echo "[setup] WARNING: k4_local_repo not available in this stack; skipping K4RECO_DIR." >&2
        fi
    else
        echo "[setup] WARNING: K4RECO_DIR does not exist: ${K4RECO_DIR}" >&2
    fi
fi

# ---------------------------------------------------------------------------
# Report and persist the environment actually used.
# ---------------------------------------------------------------------------
{
    echo "# Key4hep environment recorded by setup/setup_key4hep.sh"
    echo "# date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "# host: $(hostname)"
    echo
    echo "KEY4HEP_STACK=${KEY4HEP_STACK:-<unset>}"
    echo "K4GEO=${K4GEO:-<unset>}"
    echo "LOCAL_K4GEO=${LOCAL_K4GEO:-<unset>}"
    echo "K4RECO_DIR=${K4RECO_DIR:-<unset>}"
    echo
    echo "ddsim=$(command -v ddsim || echo '<not found>')"
    echo "k4run=$(command -v k4run || echo '<not found>')"
    echo "python=$(command -v python || echo '<not found>')"
    echo "ddsim_version=$(ddsim --version 2>/dev/null | head -1 || true)"
    echo
    echo "# --- LD_LIBRARY_PATH ---"
    echo "${LD_LIBRARY_PATH:-<unset>}" | tr ':' '\n'
    echo
    echo "# --- PYTHONPATH ---"
    echo "${PYTHONPATH:-<unset>}" | tr ':' '\n'
} > "${OUTDIR}/environment_used.txt"

echo "[setup] KEY4HEP_STACK = ${KEY4HEP_STACK:-<unset>}"
echo "[setup] K4GEO         = ${K4GEO:-<unset>}"
echo "[setup] ddsim         = $(command -v ddsim || echo '<not found>')"
echo "[setup] k4run         = $(command -v k4run || echo '<not found>')"
echo "[setup] python        = $(command -v python || echo '<not found>')"
echo "[setup] Environment written to: ${OUTDIR}/environment_used.txt"
