#!/usr/bin/env bash
#
# find_allegro_geometry.sh
# ------------------------
# Discover ALLEGRO detector compact XML files from $K4GEO (CVMFS or a local
# editable clone). Never hard-codes a path.
#
#   bash geometry/find_allegro_geometry.sh
#
# Results are printed and saved to outputs/allegro_geometry_search.txt
#
# Honors a local clone: if you sourced setup_key4hep.sh with LOCAL_K4GEO,
# $K4GEO already points at your local k4geo/share/k4geo.

set -u

REPO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
OUTDIR="${REPO_ROOT}/outputs"
mkdir -p "$OUTDIR"
OUT="${OUTDIR}/allegro_geometry_search.txt"

if [ -z "${K4GEO:-}" ]; then
    echo "ERROR: \$K4GEO is not set. Run:  source setup/setup_key4hep.sh" >&2
    exit 1
fi
if [ ! -d "$K4GEO" ]; then
    echo "ERROR: \$K4GEO points to a non-existent directory: $K4GEO" >&2
    exit 1
fi

{
    echo "# ALLEGRO geometry search"
    echo "# date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "# K4GEO=${K4GEO}"
    echo

    echo "=== ALLEGRO compact XML files (top-level detector descriptions) ==="
    # The runnable top-level files are named ALLEGRO_*.xml inside compact/<ver>/
    find "$K4GEO" -path "*ALLEGRO*/compact/*/ALLEGRO_*.xml" 2>/dev/null | sort
    echo

    echo "=== All files/dirs matching *allegro* (case-insensitive) ==="
    find "$K4GEO" -iname "*allegro*" 2>/dev/null | sort
    echo

    echo "=== Wrapper / silicon / tracker components referenced in ALLEGRO XML ==="
    # Look inside the ALLEGRO tree for the interesting sub-detectors.
    allegro_dirs=$(find "$K4GEO" -type d -ipath "*ALLEGRO*/compact/*" 2>/dev/null)
    if [ -n "$allegro_dirs" ]; then
        grep -RniE "wrapper|silicon|SiWr|tracker|DriftChamber|drift|gas|outer" \
            $allegro_dirs 2>/dev/null \
            | grep -iE "detector |readout|include ref|<constant" \
            | head -80
    fi
    echo

    echo "=== Other FCC-ee detector concepts available (for reference) ==="
    find "$K4GEO/FCCee" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | sort
} | tee "$OUT"

echo
echo "[find] Results saved to: $OUT"

# Helpful fallback if nothing was found.
if ! find "$K4GEO" -path "*ALLEGRO*/compact/*/ALLEGRO_*.xml" 2>/dev/null | grep -q .; then
    echo
    echo "WARNING: no ALLEGRO compact XML found under \$K4GEO." >&2
    echo "         Available FCC-ee detectors are listed above." >&2
fi
