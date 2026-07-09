#!/usr/bin/env bash
#
# harvest_gun.sh - merge particle-gun condor chunk CSVs into one master
#                  strict + extended PixESL CSV pair (+ summary metadata).
#
#   SAMPLE=<name> bash harvest_gun.sh
#
# Env config:
#   SAMPLE   sample name (as printed by submit_gun_condor.sh)     [required]
#   OUTDIR   production root   (default MAPS_storage/gun_derived/<SAMPLE>)
#   DEST     merged output dir (default <FCCWorkplace>/outputs/gun/<SAMPLE>)
#   NJOBS    expected chunk count (default: NEVENTS/NPER from the production
#            lock OUTDIR/production_config.txt written by submit --submit;
#            set explicitly to override. NOT parsed from .sub files - dry
#            runs also write those, with whatever NJOBS they previewed.)
#
# A chunk counts as COMPLETE only if its converter metadata json exists (the
# converter writes it LAST -> done marker), its n_events parses, and its
# strict/extended CSVs are row-aligned. Chunks are merged in chunk-index
# order, so master strict row i and extended row i describe the same hit.
# BX ranges are disjoint by construction (chunk i owns [i*NPER,(i+1)*NPER)).
# Missing/incomplete chunks -> missing_chunks.txt + exit 1 (resubmit with
# submit_gun_condor.sh --submit: the runner skips completed chunks).
#
# Single directory snapshot for both merge and counts (BIB harvest lesson);
# merged files written atomically (same-dir tmp + mv).

set -euo pipefail
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REPO_ROOT="$( cd "$HERE/../.." >/dev/null 2>&1 && pwd )"

[ -n "${SAMPLE:-}" ] || { echo "ERROR: set SAMPLE=<name> (see submit_gun_condor.sh output)" >&2; exit 1; }
OUTDIR="${OUTDIR:-/gpfs/mnt/gpfs01/usfcc/MAPS_storage/gun_derived/${SAMPLE}}"
DEST="${DEST:-${REPO_ROOT}/outputs/gun/${SAMPLE}}"
CHUNKDIR="${OUTDIR}/chunks"
[ -d "$CHUNKDIR" ] || { echo "ERROR: missing $CHUNKDIR" >&2; exit 1; }

# expected chunk count: NJOBS env, else NEVENTS/NPER from the production lock
NJOBS="${NJOBS:-}"
if [ -z "$NJOBS" ]; then
    LOCK="${OUTDIR}/production_config.txt"
    if [ -s "$LOCK" ]; then
        L_NEV=$(sed -n 's/^NEVENTS=//p' "$LOCK"); L_NPER=$(sed -n 's/^NPER=//p' "$LOCK")
        if [ -n "$L_NEV" ] && [ -n "$L_NPER" ] && [ "$L_NPER" -gt 0 ]; then
            NJOBS=$(( L_NEV / L_NPER ))
        fi
    fi
fi
[ -n "$NJOBS" ] || { echo "ERROR: cannot determine NJOBS (no production_config.txt lock; set NJOBS=...)" >&2; exit 1; }

mkdir -p "$DEST"
MASTER="${DEST}/pixesl_gun_${SAMPLE}.csv"
MASTEREXT="${DEST}/pixesl_gun_${SAMPLE}_extended.csv"
MASTERMETA="${DEST}/pixesl_gun_${SAMPLE}.metadata.json"
MISSING="${DEST}/missing_chunks.txt"
TMP="${DEST}/.merge_$$"; TMPEXT="${DEST}/.merge_ext_$$"

# --- single snapshot: classify every expected chunk ---------------------------
COMPLETE=()  # tags, in index order
: > "$MISSING.tmp"
TOTEVT=0
for i in $(seq 0 $(( NJOBS - 1 ))); do
    tag=$(printf 'chunk_%05d' "$i")
    d="${CHUNKDIR}/${tag}"
    csv="${d}/pixesl_gun_${tag}.csv"
    ext="${d}/pixesl_gun_${tag}_extended.csv"
    meta="${d}/pixesl_gun_${tag}.metadata.json"
    ok=1
    if [ ! -s "$meta" ] || [ ! -f "$csv" ] || [ ! -f "$ext" ]; then
        ok=0
    else
        nev=$(sed -n 's/.*"n_events": *\([0-9][0-9]*\).*/\1/p' "$meta" | head -1)
        [ -n "$nev" ] || ok=0
        if [ "$ok" = 1 ] && [ "$(wc -l < "$csv")" != "$(wc -l < "$ext")" ]; then
            echo "[harvest] WARN: $tag strict/extended row mismatch -> treated as incomplete" >&2
            ok=0
        fi
    fi
    if [ "$ok" = 1 ]; then
        COMPLETE+=("$tag"); TOTEVT=$(( TOTEVT + nev ))
    else
        echo "$i" >> "$MISSING.tmp"
    fi
done
NDONE=${#COMPLETE[@]}
NMISS=$(( NJOBS - NDONE ))

[ "$NDONE" -gt 0 ] || { echo "ERROR: no complete chunks found under $CHUNKDIR" >&2; rm -f "$MISSING.tmp"; exit 1; }

# --- merge (chunk-index order preserves strict<->extended row alignment) ------
head -1 "${CHUNKDIR}/${COMPLETE[0]}/pixesl_gun_${COMPLETE[0]}.csv"           > "$TMP"
head -1 "${CHUNKDIR}/${COMPLETE[0]}/pixesl_gun_${COMPLETE[0]}_extended.csv"  > "$TMPEXT"
for tag in "${COMPLETE[@]}"; do
    tail -n +2 "${CHUNKDIR}/${tag}/pixesl_gun_${tag}.csv"          >> "$TMP"
    tail -n +2 "${CHUNKDIR}/${tag}/pixesl_gun_${tag}_extended.csv" >> "$TMPEXT"
done
NHITS=$(( $(wc -l < "$TMP") - 1 ))
NBXHIT=$(tail -n +2 "$TMP" | cut -d, -f1 | sort -u | wc -l)

# --- master metadata -----------------------------------------------------------
{
    printf '{\n  "sample": "%s",\n  "chunks_merged": %s,\n  "chunks_expected": %s,\n' "$SAMPLE" "$NDONE" "$NJOBS"
    printf '  "n_events": %s,\n  "n_hits": %s,\n  "n_bx_with_hits": %s,\n' "$TOTEVT" "$NHITS" "$NBXHIT"
    printf '  "chunk_dir": "%s",\n  "gun_config": "see chunks/chunk_00000/gun_config.json (seed/bx_offset vary per chunk)",\n' "$CHUNKDIR"
    printf '  "date": "%s"\n}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "${MASTERMETA}.tmp"

# each mv is atomic but the trio is not; a kill between them can pair a new
# strict with an old extended -- harvest is idempotent, just RE-RUN it.
# metadata (with the counts) goes last.
mv "$TMPEXT" "$MASTEREXT"; mv "$TMP" "$MASTER"; mv "${MASTERMETA}.tmp" "$MASTERMETA"

echo "================================================================"
echo "[harvest] sample : $SAMPLE"
echo "[harvest] chunks : $NDONE / $NJOBS complete"
echo "[harvest] events : $TOTEVT   hits: $NHITS   BXs with >=1 hit: $NBXHIT"
echo "[harvest] master : $MASTER"
echo "================================================================"

if [ "$NMISS" -gt 0 ]; then
    mv "$MISSING.tmp" "$MISSING"
    echo "[harvest] INCOMPLETE: $NMISS chunk(s) missing -> $MISSING" >&2
    echo "[harvest] resubmit:   bash ${HERE}/submit_gun_condor.sh --submit  (same env)" >&2
    exit 1
fi
rm -f "$MISSING.tmp" "$MISSING"
echo "[harvest] all chunks merged."
