#!/usr/bin/env bash
#
# run_particle_gun.sh - LOCAL end-to-end particle-gun chain on the BNL_MAPS
#                       detector: ddsim gun -> PixESL CSV (+extended, metadata).
#
#   bash fcc_maps_wrapper_pixesl/simulation/run_particle_gun.sh [N_EVENTS] [TAG]
#
#   N_EVENTS  events to generate (default 100); 1 event = 1 CSV BX
#   TAG       output subdirectory name. Default = a fingerprint of the FULL gun
#             config (particle, |p|, theta, mult if >1, seed, N), so different
#             configs can never silently share a directory. If you pass your
#             own TAG, YOU own that guarantee - check gun_config.json in the
#             output dir before reusing it.
#
# Gun configuration via GUN_* env vars (uniquely-prefixed on purpose: sourcing
# setup_MAPS.sh overwrites generic names like OUTDIR / REPO_ROOT - BIB lesson):
#   GUN_P           fixed momentum magnitude |p|, ddsim unit syntax
#                   (default 10*GeV). NOTE: ddsim's underlying --gun.energy is
#                   MISNAMED - in DD4hep 1.36 it is a fixed |p|, not kinetic
#                   and not total energy (verified in source + empirically).
#   GUN_PMIN/GUN_PMAX  flat |p| spectrum mode: set BOTH for p uniform in
#                   [PMIN,PMAX] (e.g. 20*GeV 70*GeV); setting only one is an
#                   ERROR (a silent fallback to fixed-|p| bit us in review)
#   GUN_THETA_MIN/GUN_THETA_MAX  polar window, sampled FLAT IN THETA (ddsim
#                   'uniform' distribution; uniform incidence-angle coverage,
#                   NOT isotropic). Default 45*deg / 135*deg = every track
#                   crosses BOTH MAPS layers (VTXOB barrel edges: 38.6 deg L3,
#                   44.0 deg L4).
#   GUN_PHI_MIN/GUN_PHI_MAX      (default 0*deg / 360*deg)
#   GUN_MULT        particles per event(=BX)         (default 1)
#   GUN_SEED        RNG seed, per-event seeds derived (default 42)
#   GUN_BXOFF       CSV BX offset: BX = event index + GUN_BXOFF (default 0;
#                   set per chunk in condor production so merged chunk CSVs
#                   have disjoint BX ranges)
#   GUN_OUTBASE     output base dir     (default <FCCWorkplace>/outputs/gun)
#   GUN_COMPACT     geometry            (default BNL_MAPS MAPS_o1_v01.xml,
#                   the standard-beampipe variant - guns don't need the CAD pipe)
#
# Output in $GUN_OUTBASE/$TAG/ :
#   gun_<TAG>.edm4hep.root                       full sim
#   gun_config.json                              provenance: the exact gun
#                                                config that produced the sim
#   pixesl_gun_<TAG>.csv                         strict  BX,COL,ROW,h_time,qin
#   pixesl_gun_<TAG>_extended.csv                + layer,module,sensor,r_mm,z_mm
#   pixesl_gun_<TAG>.metadata.json
# COL/ROW use the standard fixed per-sensor frame [0,930)x[0,990) (offsets
# 465/495), same as the delivered qq and BIB CSVs.
#
# Resume contract:
#   - sim + all three converter outputs exist -> the run is COMPLETE and this
#     script exits immediately without touching any file (so condor resubmits
#     over finished chunks are no-ops; GUN_RECONVERT=1 forces reconversion,
#     e.g. after a converter change)
#   - sim exists, converter outputs missing/partial -> ddsim skipped (loudly),
#     conversion reruns ATOMICALLY (scratch subdir + mv, metadata LAST = the
#     done marker harvest_gun.sh keys on)
# With the default TAG this is always safe (the TAG pins the config); with a
# custom TAG make sure gun_config.json matches what you are asking for.
#
# Examples:
#   bash .../run_particle_gun.sh 500                                # p=10 GeV mu-
#   GUN_PARTICLE=pi- GUN_P='1*GeV'        bash .../run_particle_gun.sh 200
#   GUN_PMIN='20*GeV' GUN_PMAX='70*GeV'   bash .../run_particle_gun.sh 1000
#
# MINIMAL env handling on purpose (plain source + plain ddsim, no `set -e/-u`):
# those crash ddsim (validated production lesson). Manual rc checks instead.

GUN_NEV="${1:-100}"

if [ -n "${GUN_ENERGY:-}" ]; then
    echo "[gun] ERROR: GUN_ENERGY was renamed to GUN_P (ddsim's gun.energy is a" >&2
    echo "      fixed momentum magnitude |p|, not an energy - set GUN_P instead)" >&2
    exit 1
fi
# flat-momentum mode needs BOTH bounds; a half-set pair must not silently
# fall back to fixed-|p| mode
if { [ -n "${GUN_PMIN:-}" ] && [ -z "${GUN_PMAX:-}" ]; } || \
   { [ -z "${GUN_PMIN:-}" ] && [ -n "${GUN_PMAX:-}" ]; }; then
    echo "[gun] ERROR: set BOTH GUN_PMIN and GUN_PMAX for a flat spectrum (got only one)" >&2
    exit 1
fi

GUN_PARTICLE="${GUN_PARTICLE:-mu-}"
GUN_P="${GUN_P:-10*GeV}"
GUN_THETA_MIN="${GUN_THETA_MIN:-45*deg}"
GUN_THETA_MAX="${GUN_THETA_MAX:-135*deg}"
GUN_PHI_MIN="${GUN_PHI_MIN:-0*deg}"
GUN_PHI_MAX="${GUN_PHI_MAX:-360*deg}"
GUN_MULT="${GUN_MULT:-1}"
GUN_SEED="${GUN_SEED:-42}"
GUN_BXOFF="${GUN_BXOFF:-0}"

# Fixed pixel-frame offsets = half the sensor pixel count -> local addresses
# in [0,930)x[0,990), identical to the qq / BIB CSV convention.
GUN_COLOFF=465
GUN_ROWOFF=495

GUN_HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
GUN_REPO_ROOT="$( cd "$GUN_HERE/../.." >/dev/null 2>&1 && pwd )"
GUN_COMPACT="${GUN_COMPACT:-${GUN_REPO_ROOT}/k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01.xml}"
GUN_STEER="${GUN_HERE}/maps_gun_steer.py"
GUN_CONVERTER="${GUN_REPO_ROOT}/fcc_maps_wrapper_pixesl/conversion/convert_simhits_to_pixesl.py"
GUN_OUTBASE="${GUN_OUTBASE:-${GUN_REPO_ROOT}/outputs/gun}"

# default TAG = full config fingerprint ('.'->'p', drop '*' and unit words we
# repeat anyway), e.g. mu-_p20GeVto70GeV_th45-135_s42_n1000
if [ -n "${GUN_PMIN:-}" ]; then
    GUN_KIN="p${GUN_PMIN}to${GUN_PMAX}"
else
    GUN_KIN="p${GUN_P}"
fi
GUN_THTAG=$(printf 'th%s-%s' "$GUN_THETA_MIN" "$GUN_THETA_MAX" | sed 's/[*]deg//g')
GUN_MULTTAG=""
[ "$GUN_MULT" != "1" ] && GUN_MULTTAG="_m${GUN_MULT}"
GUN_TAG="${2:-$(printf '%s_%s_%s%s_s%s_n%s' \
    "$GUN_PARTICLE" "$GUN_KIN" "$GUN_THTAG" "$GUN_MULTTAG" "$GUN_SEED" "$GUN_NEV" \
    | sed 's/[.]/p/g; s/[*]//g; s|[/ ]||g')}"

GUN_DIR="${GUN_OUTBASE}/${GUN_TAG}"
GUN_SIMOUT="${GUN_DIR}/gun_${GUN_TAG}.edm4hep.root"
GUN_CSVOUT="${GUN_DIR}/pixesl_gun_${GUN_TAG}.csv"
GUN_EXTOUT="${GUN_CSVOUT%.csv}_extended.csv"
GUN_METAOUT="${GUN_CSVOUT%.csv}.metadata.json"
GUN_CONFJSON="${GUN_DIR}/gun_config.json"
mkdir -p "$GUN_DIR" || exit 1

echo "[gun] particle=$GUN_PARTICLE  kin=$GUN_KIN  theta=[$GUN_THETA_MIN,$GUN_THETA_MAX] (flat in theta)  mult=$GUN_MULT"
echo "[gun] events=$GUN_NEV  seed=$GUN_SEED  ->  $GUN_DIR"

# COMPLETE run -> exit without touching anything (delivered files stay
# byte-identical; a resubmitted condor job over a finished chunk is a no-op)
if [ -z "${GUN_RECONVERT:-}" ] && [ -s "$GUN_SIMOUT" ] && [ -s "$GUN_CSVOUT" ] \
   && [ -s "$GUN_EXTOUT" ] && [ -s "$GUN_METAOUT" ]; then
    echo "[gun] already complete ($(( $(wc -l < "$GUN_CSVOUT") - 1 )) hits) -> nothing to do."
    echo "[gun] (GUN_RECONVERT=1 to force reconversion, e.g. after a converter change)"
    exit 0
fi

# Env: clear positional args (so setup_MAPS.sh doesn't parse them), plain source.
set --
# shellcheck source=/dev/null
source "${GUN_REPO_ROOT}/setup_MAPS.sh" >/dev/null 2>&1
command -v ddsim >/dev/null 2>&1 || { echo "[gun] ERROR: ddsim not found (setup_MAPS.sh failed?)" >&2; exit 1; }
[ -f "$GUN_COMPACT" ]   || { echo "[gun] ERROR: missing compact $GUN_COMPACT" >&2; exit 1; }
[ -f "$GUN_STEER" ]     || { echo "[gun] ERROR: missing steering $GUN_STEER" >&2; exit 1; }
[ -f "$GUN_CONVERTER" ] || { echo "[gun] ERROR: missing converter $GUN_CONVERTER" >&2; exit 1; }

# --- 1) ddsim gun (tmp name in the final dir, atomic mv; .root suffix required
#        for the EDM4hep writer selection) --------------------------------------
if [ -s "$GUN_SIMOUT" ]; then
    echo "[gun] ============================================================"
    echo "[gun] WARNING: sim exists -> SKIPPING ddsim, converter only."
    echo "[gun]          The gun knobs of THIS invocation are NOT applied."
    echo "[gun]          Verify $GUN_CONFJSON"
    echo "[gun]          matches what you want, or delete the dir / change TAG."
    echo "[gun] ============================================================"
else
    # fixed-|p| mode vs flat-|p| mode (ddsim's gun.energy = fixed |p| and it
    # would override the momentum range, so pass exactly one of the two)
    if [ -n "${GUN_PMIN:-}" ]; then
        set -- --gun.momentumMin "$GUN_PMIN" --gun.momentumMax "$GUN_PMAX"
    else
        set -- --gun.energy "$GUN_P"
    fi
    GUN_TMPROOT="${GUN_DIR}/.tmp_gun_$$.edm4hep.root"
    export GUN_SEED
    ddsim --steeringFile "$GUN_STEER" \
          --compactFile  "$GUN_COMPACT" \
          --gun.particle "$GUN_PARTICLE" \
          --gun.multiplicity "$GUN_MULT" \
          --gun.thetaMin "$GUN_THETA_MIN" --gun.thetaMax "$GUN_THETA_MAX" \
          --gun.phiMin   "$GUN_PHI_MIN"   --gun.phiMax   "$GUN_PHI_MAX" \
          "$@" \
          --numberOfEvents "$GUN_NEV" \
          --outputFile "$GUN_TMPROOT"
    GUN_RC=$?
    if [ $GUN_RC -ne 0 ] || [ ! -s "$GUN_TMPROOT" ]; then
        echo "[gun] ERROR: ddsim failed (rc=$GUN_RC)" >&2
        rm -f "$GUN_TMPROOT"; exit 1
    fi
    mv "$GUN_TMPROOT" "$GUN_SIMOUT" || exit 1
    # provenance sidecar: the exact config that produced THIS sim file
    # (written only when ddsim actually ran; never overwritten by a reuse run)
    {
        printf '{\n'
        printf '  "particle": "%s",\n'        "$GUN_PARTICLE"
        if [ -n "${GUN_PMIN:-}" ]; then
            printf '  "mode": "flat_momentum",\n  "p_min": "%s",\n  "p_max": "%s",\n' "$GUN_PMIN" "$GUN_PMAX"
        else
            printf '  "mode": "fixed_momentum",\n  "p": "%s",\n' "$GUN_P"
        fi
        printf '  "theta_min": "%s",\n  "theta_max": "%s",\n' "$GUN_THETA_MIN" "$GUN_THETA_MAX"
        printf '  "theta_distribution": "flat in theta (ddsim uniform)",\n'
        printf '  "phi_min": "%s",\n  "phi_max": "%s",\n'     "$GUN_PHI_MIN" "$GUN_PHI_MAX"
        printf '  "multiplicity": %s,\n  "seed": %s,\n  "n_events": %s,\n  "bx_offset": %s,\n' "$GUN_MULT" "$GUN_SEED" "$GUN_NEV" "$GUN_BXOFF"
        printf '  "compact": "%s",\n  "steering": "%s",\n'    "$GUN_COMPACT" "$GUN_STEER"
        printf '  "date": "%s"\n}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    } > "$GUN_CONFJSON"
    echo "[gun] sim done -> $GUN_SIMOUT"
fi

# --- 2) PixESL conversion (BX = event index + GUN_BXOFF; fixed pixel frame).
#        ATOMIC: the converter writes IN PLACE (open 'w'), so it runs in a
#        scratch subdir and the three outputs are mv'd (same fs) into place,
#        metadata LAST = the done marker harvest_gun.sh keys on. A kill can
#        never leave truncated finals under a complete-looking marker. --------
GUN_CONVDIR="${GUN_DIR}/.conv_$$"
mkdir -p "$GUN_CONVDIR" || exit 1
python3 "$GUN_CONVERTER" \
    --input  "$GUN_SIMOUT" \
    --output "${GUN_CONVDIR}/$(basename "$GUN_CSVOUT")" \
    --mode decode_cellid \
    --compact "$GUN_COMPACT" \
    --geometry    "${GUN_REPO_ROOT}/fcc_maps_wrapper_pixesl/conversion/geometry_config.yaml" \
    --collections "${GUN_REPO_ROOT}/fcc_maps_wrapper_pixesl/conversion/collections_config.yaml" \
    --allow-empty \
    --col-offset "$GUN_COLOFF" --row-offset "$GUN_ROWOFF" \
    --bx-offset "$GUN_BXOFF"
GUN_RC=$?
if [ $GUN_RC -ne 0 ] || [ ! -f "${GUN_CONVDIR}/$(basename "$GUN_CSVOUT")" ]; then
    echo "[gun] ERROR: converter failed (rc=$GUN_RC)" >&2
    rm -rf "$GUN_CONVDIR"; exit 1
fi
GUN_OK=1
mv "${GUN_CONVDIR}/$(basename "$GUN_EXTOUT")"  "$GUN_EXTOUT"  || GUN_OK=0
[ $GUN_OK -eq 1 ] && { mv "${GUN_CONVDIR}/$(basename "$GUN_CSVOUT")"  "$GUN_CSVOUT"  || GUN_OK=0; }
[ $GUN_OK -eq 1 ] && { mv "${GUN_CONVDIR}/$(basename "$GUN_METAOUT")" "$GUN_METAOUT" || GUN_OK=0; }
rmdir "$GUN_CONVDIR" 2>/dev/null
if [ $GUN_OK -ne 1 ]; then
    echo "[gun] ERROR: finalize of converter outputs failed" >&2; exit 1
fi

# --- 3) summary (event count from the converter metadata = what is actually
#        in the file, NOT this invocation's request - they differ on reuse) ----
GUN_NEVREAL=$(sed -n 's/.*"n_events": *\([0-9][0-9]*\).*/\1/p' "$GUN_METAOUT" | head -1)
GUN_NHITS=$(( $(wc -l < "$GUN_CSVOUT") - 1 ))
echo "[gun] CSV -> $GUN_CSVOUT"
echo "[gun] hits: $GUN_NHITS in ${GUN_NEVREAL:-?} events(BXs)"
if [ "$GUN_NHITS" -eq 0 ]; then
    echo "[gun] WARNING: 0 MAPS hits - check momentum (p >~ 0.1 GeV to reach L4 at 90 deg in 2 T) and theta window" >&2
else
    awk -F, 'NR>1 { n[$6]++; bx[$1]=1 }
             END  { for (l in n) printf "[gun]   layer %s: %d hits\n", l, n[l]
                    printf "[gun]   BXs with >=1 hit: %d\n", length(bx) }' \
        "$GUN_EXTOUT"
fi
