#!/usr/bin/env bash
#
# inspect_allegro_geometry.sh
# ---------------------------
# Inspect a DD4hep compact detector XML: list included files, detectors,
# readouts, segmentations and sensitive components. Follows <include ref=...>
# one level deep so sub-detector files (e.g. the silicon wrapper) are covered.
#
#   bash geometry/inspect_allegro_geometry.sh [/path/to/ALLEGRO_o1_v03.xml]
#
# If no path is given, the latest ALLEGRO_o1_v0N.xml under $K4GEO is used.
# Results are printed and saved to outputs/allegro_geometry_inspect.txt

set -u

REPO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." >/dev/null 2>&1 && pwd )"
OUTDIR="${REPO_ROOT}/outputs"
mkdir -p "$OUTDIR"
OUT="${OUTDIR}/allegro_geometry_inspect.txt"

XML="${1:-}"

# Auto-pick the latest ALLEGRO top-level XML if none was given.
if [ -z "$XML" ]; then
    if [ -z "${K4GEO:-}" ]; then
        echo "ERROR: no XML given and \$K4GEO unset. Run: source setup/setup_key4hep.sh" >&2
        echo "       or pass a path:  bash $0 /path/to/ALLEGRO_o1_v03.xml" >&2
        exit 1
    fi
    XML=$(find "$K4GEO" -path "*ALLEGRO*/compact/*/ALLEGRO_*.xml" 2>/dev/null | sort | tail -1)
    if [ -z "$XML" ]; then
        echo "ERROR: could not auto-find an ALLEGRO XML under \$K4GEO." >&2
        echo "       Run geometry/find_allegro_geometry.sh to see what's available." >&2
        exit 1
    fi
    echo "[inspect] No path given; using latest: $XML"
fi

if [ ! -f "$XML" ]; then
    echo "ERROR: file not found: $XML" >&2
    exit 1
fi

XMLDIR="$( cd "$( dirname "$XML" )" && pwd )"

# Build the list of files to scan: the top file + its (resolved) includes.
declare -a FILES=("$XML")
while IFS= read -r ref; do
    # strip xml comments-only lines already excluded by grep below
    case "$ref" in
        /*)        cand="$ref" ;;                       # absolute
        \$*)       cand=$(eval echo "$ref") ;;          # ${VAR}/...
        *)         cand="${XMLDIR}/${ref}" ;;           # relative
    esac
    # Resolve symlinks; only keep existing files.
    if [ -f "$cand" ]; then
        FILES+=("$(readlink -f "$cand")")
    fi
done < <(grep -oE 'include ref="[^"]+"' "$XML" | sed -E 's/include ref="([^"]+)"/\1/' | grep -v '^<!--')

{
    echo "# ALLEGRO geometry inspection"
    echo "# date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "# top XML: $XML"
    echo

    echo "=== Included XML files (from top-level) ==="
    grep -nE 'include ref=' "$XML" | sed 's/^/  /'
    echo

    echo "=== Files scanned below (top + resolved includes) ==="
    printf '  %s\n' "${FILES[@]}"
    echo

    echo "=== Detectors (name / type / id / readout / sensitive) ==="
    grep -HnE '<detector ' "${FILES[@]}" 2>/dev/null | sed 's/^/  /'
    echo

    echo "=== Readout definitions ==="
    grep -HnE '<readout |<readout$|name=".*Collection"' "${FILES[@]}" 2>/dev/null | sed 's/^/  /'
    echo

    echo "=== CellID encodings (<id>...) ==="
    grep -HnE '<id>' "${FILES[@]}" 2>/dev/null | sed 's/^/  /'
    grep -HnE 'GlobalTrackerReadoutID' "${FILES[@]}" 2>/dev/null | sed 's/^/  /'
    echo

    echo "=== Segmentation definitions ==="
    grep -HnE '<segmentation' "${FILES[@]}" 2>/dev/null | sed 's/^/  /'
    echo "  (none listed above = no pixel-level DD4hep segmentation; pixelize in the converter)"
    echo

    echo "=== Sensitive components / silicon / Si ==="
    grep -HnE 'sensitive="[Tt]rue"|sensitive_type|material="Silicon"|material="Si"' "${FILES[@]}" 2>/dev/null | head -60 | sed 's/^/  /'
    echo

    echo "=== Wrapper-specific keywords (SiWr / wrapper) ==="
    grep -HniE 'SiWr|wrapper' "${FILES[@]}" 2>/dev/null | grep -iE 'detector |readout|constant name|Sensitive_Thickness|inner_radius|outer_radius|half_length' | head -60 | sed 's/^/  /'
} | tee "$OUT"

echo
echo "[inspect] Results saved to: $OUT"
