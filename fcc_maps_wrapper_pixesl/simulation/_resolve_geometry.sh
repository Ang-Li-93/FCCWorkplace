#!/usr/bin/env bash
# _resolve_geometry.sh  (sourced helper, not run directly)
# --------------------------------------------------------
# Resolve the ALLEGRO compact XML to use, honoring (in order):
#   1. $ALLEGRO_XML        explicit path to a top-level ALLEGRO_*.xml
#   2. $ALLEGRO_VERSION    version dir name, e.g. ALLEGRO_o1_v03 (under $K4GEO)
#   3. latest ALLEGRO_o1_v0N.xml found under $K4GEO
# Sets the variable  ALLEGRO_COMPACT  on success; exits 1 with advice otherwise.
#
# Because $K4GEO follows your LOCAL_K4GEO override (see setup_key4hep.sh), this
# automatically picks up an edited local k4geo geometry.

resolve_allegro_compact() {
    if [ -n "${ALLEGRO_XML:-}" ]; then
        if [ -f "$ALLEGRO_XML" ]; then
            ALLEGRO_COMPACT="$ALLEGRO_XML"
            return 0
        fi
        echo "ERROR: ALLEGRO_XML set but not found: $ALLEGRO_XML" >&2
        return 1
    fi

    if [ -z "${K4GEO:-}" ]; then
        echo "ERROR: \$K4GEO unset and \$ALLEGRO_XML not given." >&2
        echo "       Run: source setup/setup_key4hep.sh" >&2
        return 1
    fi

    local ver="${ALLEGRO_VERSION:-}"
    if [ -n "$ver" ]; then
        ALLEGRO_COMPACT="${K4GEO}/FCCee/ALLEGRO/compact/${ver}/${ver}.xml"
        if [ -f "$ALLEGRO_COMPACT" ]; then
            return 0
        fi
        echo "ERROR: ALLEGRO_VERSION='$ver' not found at:" >&2
        echo "         $ALLEGRO_COMPACT" >&2
        return 1
    fi

    ALLEGRO_COMPACT=$(find "$K4GEO" -path "*ALLEGRO*/compact/*/ALLEGRO_*.xml" \
                        2>/dev/null | sort | tail -1)
    if [ -z "$ALLEGRO_COMPACT" ]; then
        echo "ERROR: no ALLEGRO compact XML under \$K4GEO=$K4GEO" >&2
        echo "       Available FCC-ee detectors:" >&2
        find "$K4GEO/FCCee" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | sed 's/^/         /' >&2
        return 1
    fi
    return 0
}
