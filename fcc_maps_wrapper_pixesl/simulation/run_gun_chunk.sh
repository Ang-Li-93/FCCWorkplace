#!/usr/bin/env bash
#
# run_gun_chunk.sh - one SELF-CONTAINED HTCondor job of the particle-gun
#                    production: NPER gun events -> sim + PixESL CSV chunk.
#
#   run_gun_chunk.sh PROC NPER SEEDBASE PARTICLE PMIN PMAX OUTDIR
#
#   PROC      condor $(Process): chunk index
#   NPER      events in this chunk (1 event = 1 BX)
#   SEEDBASE  chunk seed = SEEDBASE + PROC (choose SEEDBASE so no chunk seed
#             collides with other samples of the same config: per-event RNG
#             derives from (seed, event#), so a reused seed replays events)
#   PMIN/PMAX flat |p| spectrum bounds, ddsim unit syntax; PMIN == PMAX gives
#             a fixed-|p| sample (ddsim momentumMin==momentumMax)
#   OUTDIR    production root; chunk output -> OUTDIR/chunks/chunk_<PROC>/
#             (OUTDIR is the LAST argument on purpose: the submit script's
#             already-queued guard matches on it)
#
# BX uniqueness across the merged sample: GUN_BXOFF = PROC*NPER, so chunk i
# owns BX [i*NPER, (i+1)*NPER). Resume comes free from run_particle_gun.sh
# (sim exists -> converter-only; csv is written last = done marker), so
# re-submitting after failures only redoes missing chunks.
#
# Optional gun knobs (GUN_THETA_MIN/MAX, GUN_PHI_MIN/MAX, GUN_MULT) pass
# through from the condor job environment untouched.
#
# Wrapper vars are GC_-prefixed; the GUN_* names are the runner's interface
# (the runner itself guards against the setup_MAPS.sh clobber gotcha).

GC_PROC="$1"
GC_NPER="$2"
GC_SEEDBASE="$3"
GC_PARTICLE="$4"
GC_PMIN="$5"
GC_PMAX="$6"
GC_OUT="$7"

if [ -z "$GC_OUT" ]; then
    echo "[gunchunk] ERROR: usage: run_gun_chunk.sh PROC NPER SEEDBASE PARTICLE PMIN PMAX OUTDIR" >&2
    exit 1
fi

GC_HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
GC_TAG=$(printf 'chunk_%05d' "$GC_PROC")

export GUN_PARTICLE="$GC_PARTICLE"
export GUN_PMIN="$GC_PMIN"
export GUN_PMAX="$GC_PMAX"
export GUN_SEED=$(( GC_SEEDBASE + GC_PROC ))
export GUN_BXOFF=$(( GC_PROC * GC_NPER ))
export GUN_OUTBASE="${GC_OUT}/chunks"

echo "[gunchunk] host=$(hostname)  chunk=$GC_PROC  nper=$GC_NPER  seed=$GUN_SEED  bxoff=$GUN_BXOFF"
exec bash "${GC_HERE}/run_particle_gun.sh" "$GC_NPER" "$GC_TAG"
