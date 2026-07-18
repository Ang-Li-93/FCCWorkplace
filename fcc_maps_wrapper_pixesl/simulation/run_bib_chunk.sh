#!/usr/bin/env bash
#
# run_bib_chunk.sh  -  one SELF-CONTAINED HTCondor job: N IPC bunch crossings
#                      through vertex-reset + ddsim (BIB geometry) + PixESL convert.
#
#   run_bib_chunk.sh PROC NBX BXLIST COMPACT STEERING SRCDIR OUTDIR
#
#   PROC      condor $(Process): this job handles lines [PROC*NBX, PROC*NBX+NBX)
#             of BXLIST (one bunch-crossing id per line)
#   BXLIST    text file with one bx id per line (from submit_bib_condor.sh;
#             the submit script creates a NEW timestamped list per submission,
#             so a running job's list is never rewritten under it)
#   SRCDIR    IPC source tree containing data<bx>/pairs.pairs (GuineaPig)
#   OUTDIR    output root; writes OUTDIR/sim/bx_<bx>.edm4hep.root and
#             OUTDIR/csv/bx_<bx>{.csv,_extended.csv,.metadata.json}
#
# Per BX:
#   1) vertex reset (x,y,z -> 0; GuineaPig has no B-field; needed for pre-2026
#      files) with awk into per-job scratch, exit + line-count checked
#      [= bib-studies set_vertex_000.py]
#   2) ddsim: .pairs read natively (1 file = 1 BX = 1 event). Per-BX random
#      seed via BIB_SEED env (read by maps_bib_steer.py) -> deterministic
#      reproduction of any bx. (--random.seed on the CLI SIGSEGVs ddsim, and
#      --meta.runNumberOffset does NOT touch the seed - only file metadata.)
#   3) convert_simhits_to_pixesl.py with --bx-offset <bx> (CSV BX column = bx
#      id) and FIXED --col-offset/--row-offset 1024 so all per-BX CSVs share
#      one pixel coordinate frame (per-file auto-shift would not).
#
# ATOMIC finalization: every output is copied to a hidden .tmp name in its
# FINAL gpfs directory, then mv'd (same-filesystem rename = atomic). A killed/
# evicted job can never leave a partial file under a final name, so the
# per-step resume gates ([ -s final ]) are reliable, and a duplicate job
# racing the same BX at worst wastes CPU - never corrupts.
# The csv (resume marker) is finalized LAST, after extended+metadata.
#
# Already-done BXs are SKIPPED per-step -> resubmission is cheap.
# MINIMAL env handling on purpose (plain source, no `set -e/-u`): those crash
# ddsim. All paths absolute; per-job scratch.
#
# ALL variables read after `source setup_MAPS.sh` carry a BIB_ prefix:
# setup_key4hep.sh overwrites generic names (OUTDIR, REPO_ROOT, ...) when
# sourced, silently redirecting outputs (bit us with OUTDIR -> repo outputs/).

BIB_PROC="$1"
BIB_NBX="$2"
BIB_LIST="$3"
BIB_COMPACT="$4"
BIB_STEER="$5"
BIB_SRC="$6"
BIB_OUT="$7"
# 8th arg: vertex reset to (0,0,0). 1 = pre-2026 GuineaPig files (GHC V24.4:
# no B-field at generation, positions wrong). 0 = 2026+ files (LCC V106.2:
# generated WITH the 2T field + 10mm beampipe, positions correct - do NOT touch).
BIB_VTXRESET="${8:-1}"

BIB_SEED_BASE=42
# walltime watchdog per ddsim attempt (s); hang -> exit 124 -> retry logic
BIB_DDSIM_TIMEOUT="${BIB_DDSIM_TIMEOUT:-2400}"
# Fixed pixel-frame offsets = half the sensor pixel count, so local addresses
# land in [0,930)x[0,990) exactly like the delivered qq CSVs:
#   COL: VTXOB_sens_rphi_sensitive 18.6mm / 20um = 930 px -> offset 465
#   ROW: VTXOB_sens_z_sensitive    19.8mm / 20um = 990 px -> offset 495
BIB_COLOFF=465
BIB_ROWOFF=495

BIB_REPO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../.." >/dev/null 2>&1 && pwd )"
BIB_CONVERTER="${BIB_REPO_ROOT}/fcc_maps_wrapper_pixesl/conversion/convert_simhits_to_pixesl.py"
BIB_SCRATCH="${_CONDOR_SCRATCH_DIR:-$(mktemp -d)}/bib_${BIB_PROC}"

echo "[bib $BIB_PROC] host=$(hostname)  nbx=$BIB_NBX  scratch=$BIB_SCRATCH"
mkdir -p "$BIB_OUT/sim" "$BIB_OUT/csv" "$BIB_SCRATCH"

# Env: clear positional args (so setup_MAPS.sh doesn't parse them), plain source.
set --
# shellcheck source=/dev/null
source "${BIB_REPO_ROOT}/setup_MAPS.sh" >/dev/null 2>&1
command -v ddsim >/dev/null 2>&1 || { echo "[bib $BIB_PROC] ERROR: ddsim not found" >&2; exit 1; }
[ -f "$BIB_COMPACT" ]   || { echo "[bib $BIB_PROC] ERROR: missing compact $BIB_COMPACT" >&2; exit 1; }
[ -f "$BIB_LIST" ]      || { echo "[bib $BIB_PROC] ERROR: missing bx list $BIB_LIST" >&2; exit 1; }
[ -f "$BIB_CONVERTER" ] || { echo "[bib $BIB_PROC] ERROR: missing converter $BIB_CONVERTER" >&2; exit 1; }

BIB_FIRST=$(( BIB_PROC * BIB_NBX + 1 ))          # sed line numbers are 1-based
BIB_IDS=$(sed -n "${BIB_FIRST},$(( BIB_FIRST + BIB_NBX - 1 ))p" "$BIB_LIST")
[ -n "$BIB_IDS" ] || { echo "[bib $BIB_PROC] nothing to do (list exhausted)"; exit 0; }

# finalize SRC DST: same-dir tmp copy + atomic rename onto gpfs
bib_finalize() {
    bib_fin_tmp="$(dirname "$2")/.$(basename "$2").tmp.$$"
    cp "$1" "$bib_fin_tmp" && mv "$bib_fin_tmp" "$2"
}

bib_nfail=0
for bx in $BIB_IDS; do
    # input layout: GHC-style data<bx>/pairs.pairs OR flat output_<bx>.pairs (LCC 2026+)
    bib_src_pairs="${BIB_SRC}/data${bx}/pairs.pairs"
    [ -f "$bib_src_pairs" ] || bib_src_pairs="${BIB_SRC}/output_${bx}.pairs"
    bib_simout="${BIB_OUT}/sim/bx_${bx}.edm4hep.root"
    bib_csvout="${BIB_OUT}/csv/bx_${bx}.csv"

    if [ -s "$bib_simout" ] && [ -s "$bib_csvout" ]; then
        echo "[bib $BIB_PROC] bx $bx already done, skipping"
        continue
    fi
    if [ ! -s "$bib_src_pairs" ]; then
        echo "[bib $BIB_PROC] ERROR: missing input $bib_src_pairs" >&2
        bib_nfail=$((bib_nfail+1)); continue
    fi

    # 1+2) vertex reset + ddsim, skipped if the sim output already exists
    #      (e.g. resubmission after a converter-only failure)
    if [ -s "$bib_simout" ]; then
        echo "[bib $BIB_PROC] bx $bx: sim exists, skipping ddsim"
    else
        if [ "$BIB_VTXRESET" = "1" ]; then
            # vertex reset -> scratch (.pairs extension required for the reader)
            bib_pairs="${BIB_SCRATCH}/vtx000_${bx}.pairs"
            bib_pairs_rm="$bib_pairs"      # ours to clean up
            if ! awk '{$5=0; $6=0; $7=0; print}' "$bib_src_pairs" > "$bib_pairs" \
               || [ "$(wc -l < "$bib_pairs")" != "$(wc -l < "$bib_src_pairs")" ]; then
                echo "[bib $BIB_PROC] ERROR: vertex reset failed for bx $bx" >&2
                bib_nfail=$((bib_nfail+1)); rm -f "$bib_pairs"; continue
            fi
        else
            # 2026+ files carry correct vertices: feed the READ-ONLY source
            # directly and never try to remove it
            bib_pairs="$bib_src_pairs"
            bib_pairs_rm=""
        fi

        # ddsim (write to local scratch, then atomic finalize onto gpfs).
        # WORKFLOW CONTRACT (permanent, not a patch): pathological events in
        # CAD geometries either ABORT Geant4 (v1 MDI: GeomNav1002 rc=133,
        # ~1%/BX) or HANG it in an endless navigation loop (v2 MDI, ~4%/BX).
        # Every attempt therefore runs under a WALLTIME WATCHDOG
        # (BIB_DDSIM_TIMEOUT, default 2400 s ~ 4x the p99 BX time; timeout
        # -> exit 124), and gets up to 2 DETERMINISTIC attempts (attempt 2:
        # seed+1000000). Every BX ends either complete on disk or classified
        # in the ledger: OUTDIR/ledger/bx_<id>.status
        #   = ok-seed1 | ok-seed2 | failed-timeout | failed-crash
        bib_tmproot="${BIB_SCRATCH}/bx_${bx}.edm4hep.root"
        bib_rc=1
        bib_outcome="failed-crash"
        for bib_try in 0 1; do
            bib_seed=$(( BIB_SEED_BASE + bx + bib_try * 1000000 ))
            echo "[bib $BIB_PROC] bx $bx: ddsim ($(wc -l < "$bib_pairs") pairs, seed $bib_seed, attempt $((bib_try+1)), timeout ${BIB_DDSIM_TIMEOUT}s) ..."
            BIB_SEED=$bib_seed \
            timeout -k 60 "$BIB_DDSIM_TIMEOUT" \
            ddsim --steeringFile "$BIB_STEER" \
                  --compactFile  "$BIB_COMPACT" \
                  --inputFiles   "$bib_pairs" \
                  --numberOfEvents -1 \
                  --outputFile   "$bib_tmproot"
            bib_rc=$?
            if [ $bib_rc -eq 0 ] && [ -s "$bib_tmproot" ]; then
                bib_outcome="ok-seed$((bib_try+1))"
                break
            fi
            if [ $bib_rc -eq 124 ] || [ $bib_rc -eq 137 ]; then
                bib_kind="TIMEOUT after ${BIB_DDSIM_TIMEOUT}s (hung navigation)"
                bib_outcome="failed-timeout"
            else
                bib_kind="crash"
                bib_outcome="failed-crash"
            fi
            echo "[bib $BIB_PROC] WARN: ddsim attempt $((bib_try+1)) for bx $bx: ${bib_kind} (rc=$bib_rc)" >&2
            rm -f "$bib_tmproot"
        done
        mkdir -p "${BIB_OUT}/ledger"
        echo "$bib_outcome rc=$bib_rc seeds=$((BIB_SEED_BASE + bx)),$((BIB_SEED_BASE + bx + 1000000)) $(date -u +%FT%TZ)" \
            > "${BIB_OUT}/ledger/.bx_${bx}.status.tmp.$$" \
            && mv "${BIB_OUT}/ledger/.bx_${bx}.status.tmp.$$" "${BIB_OUT}/ledger/bx_${bx}.status"
        if [ $bib_rc -ne 0 ] || [ ! -s "$bib_tmproot" ]; then
            echo "[bib $BIB_PROC] ERROR: ddsim failed for bx $bx (both seeds, outcome=$bib_outcome)" >&2
            bib_nfail=$((bib_nfail+1)); rm -f "$bib_tmproot" $bib_pairs_rm; continue
        fi
        bib_finalize "$bib_tmproot" "$bib_simout" \
            || { echo "[bib $BIB_PROC] ERROR: finalize sim failed for bx $bx" >&2
                 bib_nfail=$((bib_nfail+1)); rm -f "$bib_tmproot" $bib_pairs_rm; continue; }
        rm -f "$bib_tmproot" $bib_pairs_rm
    fi

    # 3) PixESL conversion into scratch, then atomic finalize (csv LAST:
    #    it is the resume/done marker)
    bib_csvtmp="${BIB_SCRATCH}/bx_${bx}.csv"
    echo "[bib $BIB_PROC] bx $bx: convert ..."
    python3 "$BIB_CONVERTER" \
        --input "$bib_simout" \
        --output "$bib_csvtmp" \
        --mode decode_cellid \
        --compact "$BIB_COMPACT" \
        --geometry    "${BIB_REPO_ROOT}/fcc_maps_wrapper_pixesl/conversion/geometry_config.yaml" \
        --collections "${BIB_REPO_ROOT}/fcc_maps_wrapper_pixesl/conversion/collections_config.yaml" \
        --allow-empty \
        --col-offset "$BIB_COLOFF" --row-offset "$BIB_ROWOFF" \
        --bx-offset "$bx"
    bib_rc=$?
    if [ $bib_rc -ne 0 ] || [ ! -f "$bib_csvtmp" ]; then
        echo "[bib $BIB_PROC] ERROR: converter failed for bx $bx (rc=$bib_rc)" >&2
        bib_nfail=$((bib_nfail+1)); continue
    fi
    bib_ok=1
    bib_finalize "${BIB_SCRATCH}/bx_${bx}_extended.csv" "${BIB_OUT}/csv/bx_${bx}_extended.csv" || bib_ok=0
    bib_finalize "${BIB_SCRATCH}/bx_${bx}.metadata.json" "${BIB_OUT}/csv/bx_${bx}.metadata.json" || bib_ok=0
    if [ $bib_ok -eq 1 ]; then
        bib_finalize "$bib_csvtmp" "$bib_csvout" || bib_ok=0
    fi
    if [ $bib_ok -ne 1 ]; then
        echo "[bib $BIB_PROC] ERROR: finalize csv failed for bx $bx" >&2
        bib_nfail=$((bib_nfail+1)); continue
    fi
    rm -f "$bib_csvtmp" "${BIB_SCRATCH}/bx_${bx}_extended.csv" "${BIB_SCRATCH}/bx_${bx}.metadata.json"
    echo "[bib $BIB_PROC] bx $bx done -> $(( $(wc -l < "$bib_csvout") - 1 )) hits"
done

[ -n "${_CONDOR_SCRATCH_DIR:-}" ] || rm -rf "$BIB_SCRATCH"
echo "[bib $BIB_PROC] finished, failures: $bib_nfail"
exit $(( bib_nfail > 0 ? 1 : 0 ))
