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
#   KEY4HEP_SETUP   CVMFS setup script (default: stable sw.hsf.org)
#   KEY4HEP_RELEASE pin a release date -> `-r <date>` (reproducible)
#   K4GEO_DIR       a locally-BUILT k4geo repo -> `k4_local_repo` (compiled plugins
#                   like VertexBarrel_detailed_o1_v03 that a fixed stable stack lacks)
#   K4GEO_BUILD=1   build K4GEO_DIR first (one-time cmake build), then register it
#   LOCAL_K4GEO     directory containing FCCee/ -> sets K4GEO to editable source XML
#   K4RECO_DIR      a locally-built k4 repo (e.g. k4Reco) -> runs `k4_local_repo`
#
# Why both K4GEO_DIR and LOCAL_K4GEO? k4geo = compiled plugins (from the BUILD,
# via K4GEO_DIR/k4_local_repo) + XML data (from the SOURCE tree, via LOCAL_K4GEO).
# So you get the right plugins AND live-editable XML (no reinstall to edit XML).
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
# Helper: run `k4_local_repo` in the CURRENT shell (cd in, run, cd back).
#   It must run from inside the repo dir AND its env exports must persist, so a
#   subshell ( ... ) would silently lose them -- save/restore $PWD instead.
# ---------------------------------------------------------------------------
_k4_register() {            # $1 = repo dir, $2 = label
    local _dir="$1" _label="$2" _save="$PWD"
    if ! command -v k4_local_repo >/dev/null 2>&1; then
        echo "[setup] WARNING: k4_local_repo not available; skipping ${_label}." >&2
        return 0
    fi
    echo "[setup] Registering ${_label} via k4_local_repo: ${_dir}"
    cd "${_dir}" || { echo "[setup] WARNING: cannot cd ${_dir}" >&2; return 1; }
    k4_local_repo || echo "[setup] WARNING: k4_local_repo for ${_label} failed (built?)." >&2
    cd "${_save}" || true
}

# ---------------------------------------------------------------------------
# Optional: build the local k4geo fork once (K4GEO_BUILD=1). Needs the stack's
# cmake/dd4hep, which we just sourced above.
# ---------------------------------------------------------------------------
if [ "${K4GEO_BUILD:-0}" = "1" ] && [ -n "${K4GEO_DIR:-}" ] && [ -d "${K4GEO_DIR}" ]; then
    echo "[setup] Building local k4geo (one-time): ${K4GEO_DIR}"
    ( cd "${K4GEO_DIR}" \
        && cmake -B build -S . -DCMAKE_INSTALL_PREFIX="${K4GEO_DIR}/install" \
        && cmake --build build -j"${K4GEO_BUILD_JOBS:-8}" --target install ) \
        || echo "[setup] ERROR: k4geo build failed (see output above)." >&2
fi

# ---------------------------------------------------------------------------
# Register a locally-BUILT k4geo (compiled plugins) then k4Reco. Order matters:
# do these BEFORE the LOCAL_K4GEO override so the source-tree XML wins for K4GEO.
# ---------------------------------------------------------------------------
if [ -n "${K4GEO_DIR:-}" ]; then
    if [ ! -d "${K4GEO_DIR}" ]; then
        echo "[setup] WARNING: K4GEO_DIR does not exist: ${K4GEO_DIR}" >&2
    elif find "${K4GEO_DIR}" -maxdepth 5 -name 'libk4geo*.so*' -print -quit 2>/dev/null | grep -q .; then
        _k4_register "${K4GEO_DIR}" "local k4geo build"
    else
        echo "[setup] NOTE: K4GEO_DIR set but k4geo is not built (no libk4geo found)." >&2
        echo "[setup]       Build once:  source setup_MAPS.sh --build-k4geo" >&2
        echo "[setup]       (needed for _o1_v03 plugins on a fixed stable stack)" >&2
    fi
fi

if [ -n "${K4RECO_DIR:-}" ]; then
    if [ -d "${K4RECO_DIR}" ]; then
        _k4_register "${K4RECO_DIR}" "local k4Reco"
    else
        echo "[setup] WARNING: K4RECO_DIR does not exist: ${K4RECO_DIR}" >&2
    fi
fi

# ---------------------------------------------------------------------------
# Point K4GEO at the editable SOURCE-tree XML LAST, so live XML edits take
# effect with no reinstall. Compiled plugins still come from the build that
# k4_local_repo put on LD_LIBRARY_PATH above.
#   LOCAL_K4GEO must be the directory that contains FCCee/ (e.g. <clone>/k4geo).
# ---------------------------------------------------------------------------
if [ -n "${LOCAL_K4GEO:-}" ]; then
    if [ -d "${LOCAL_K4GEO}/FCCee/ALLEGRO" ]; then
        export K4GEO="${LOCAL_K4GEO}"
        echo "[setup] K4GEO -> local source XML: $K4GEO"
    else
        echo "[setup] WARNING: LOCAL_K4GEO set but '${LOCAL_K4GEO}/FCCee/ALLEGRO' not found; keeping K4GEO=${K4GEO}" >&2
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
    echo "K4GEO_DIR=${K4GEO_DIR:-<unset>}"
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
