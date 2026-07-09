#!/usr/bin/env bash
#
# submit_gun_condor.sh - HTCondor particle-gun production (chunked).
#
#   bash submit_gun_condor.sh [--submit]
#
# Queues NJOBS = NEVENTS/NPER self-contained jobs (run_gun_chunk.sh -> the
# reviewed run_particle_gun.sh chain): each simulates NPER gun events with its
# own seed (SEEDBASE+chunk) and BX range (chunk*NPER + [0,NPER)) and converts
# to a PixESL CSV chunk. Already-completed chunks are skipped inside the
# runner, so re-running with --submit after failures only redoes the missing
# ones. Dry-run unless --submit.
#
# Safety (carried over from the BIB submit audit + gun review, do not regress):
#   - --submit REFUSES to queue while jobs from a previous submission of this
#     OUTDIR are still in the queue (FORCE=1 to override)
#   - initialdir pins the jobs' Iwd to a shared path
#   - NEVENTS must be an exact multiple of NPER (chunks own fixed BX windows;
#     a ragged last chunk would break the BX bookkeeping)
#   - the FULL production config is locked into OUTDIR/production_config.txt
#     on first --submit; any later --submit with a differing config (incl.
#     NPER, which silently remaps BX windows, and theta/phi/mult, which the
#     SAMPLE name alone cannot fully encode) is a HARD error - no override.
#     Different config => different SAMPLE/OUTDIR, always.
#
# Env config:
#   NEVENTS    total events               (default 10000)
#   NPER       events per job             (default 250; ~15 min/job)
#   SEEDBASE   chunk seed base            (default 1000; chunk i -> 1000+i.
#              Do NOT reuse a seed range already spent on another sample of
#              the same gun config - per-event RNG replays.)
#   PARTICLE   gun particle               (default mu-)
#   PMIN/PMAX  flat |p| bounds            (default 20*GeV / 70*GeV;
#              PMIN==PMAX = fixed |p|)
#   SAMPLE     sample name                (default derived from config)
#   OUTDIR     production root            (default MAPS_storage/gun_derived/<SAMPLE>)
#   GUN_THETA_MIN/MAX, GUN_PHI_MIN/MAX, GUN_MULT   forwarded to the jobs if set
#   ACCT_GROUP / REQUEST_MEMORY / REQUEST_DISK / MAXRUNTIME / FORCE
#
# After completion:  SAMPLE=<name> bash harvest_gun.sh   (merge chunk CSVs)

set -euo pipefail
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

NEVENTS="${NEVENTS:-10000}"
NPER="${NPER:-250}"
SEEDBASE="${SEEDBASE:-1000}"
PARTICLE="${PARTICLE:-mu-}"
PMIN="${PMIN:-20*GeV}"
PMAX="${PMAX:-70*GeV}"
ACCT_GROUP="${ACCT_GROUP:-group_usfcc}"
REQUEST_MEMORY="${REQUEST_MEMORY:-8192}"   # MB; ALLEGRO geometry, same margin as qq
REQUEST_DISK="${REQUEST_DISK:-1048576}"    # KB = 1 GB (outputs go straight to gpfs)
MAXRUNTIME="${MAXRUNTIME:-14400}"          # s = 4 h (geo load + NPER*~2s + margin)
FORCE="${FORCE:-0}"

if [ $(( NEVENTS % NPER )) -ne 0 ]; then
    echo "ERROR: NEVENTS ($NEVENTS) must be an exact multiple of NPER ($NPER)" >&2
    exit 1
fi
NJOBS=$(( NEVENTS / NPER ))

# sample name: config fingerprint like the local runner's default TAG
# (theta and mult included: they change the physics but are only forwarded via
# the job environment, so the name must encode them too)
TH_MIN="${GUN_THETA_MIN:-45*deg}"; TH_MAX="${GUN_THETA_MAX:-135*deg}"
MULTTAG=""; [ "${GUN_MULT:-1}" != "1" ] && MULTTAG="_m${GUN_MULT}"
SAMPLE="${SAMPLE:-$(printf '%s_p%sto%s_th%s-%s%s_s%s_n%s' \
    "$PARTICLE" "$PMIN" "$PMAX" \
    "$(printf '%s' "$TH_MIN" | sed 's/[*]deg//')" \
    "$(printf '%s' "$TH_MAX" | sed 's/[*]deg//')" \
    "$MULTTAG" "$SEEDBASE" "$NEVENTS" \
    | sed 's/[.]/p/g; s/[*]//g; s|[/ ]||g')}"
OUTDIR="${OUTDIR:-/gpfs/mnt/gpfs01/usfcc/MAPS_storage/gun_derived/${SAMPLE}}"

RUNNER="${HERE}/run_gun_chunk.sh"
SUBDIR="${OUTDIR}/condor"; LOGDIR="${SUBDIR}/logs"
STAMP="$(date +%Y%m%d_%H%M%S)"
SUBFILE="${SUBDIR}/maps_gun_${STAMP}.sub"

[ -e "$RUNNER" ] || { echo "ERROR: missing $RUNNER" >&2; exit 1; }
command -v condor_submit >/dev/null 2>&1 || { echo "ERROR: condor_submit not found" >&2; exit 1; }
mkdir -p "${OUTDIR}/chunks" "$LOGDIR"; chmod +x "$RUNNER" "${HERE}/run_particle_gun.sh"

# Guard: previous submission of this OUTDIR still in the queue?
NQUEUED=$(condor_q -af Cmd Args 2>/dev/null \
          | awk -v r="$RUNNER" -v o="$OUTDIR" '$1==r && $NF==o' | wc -l)
NQUEUED=${NQUEUED:-0}

# forward optional gun knobs to the jobs (condor 'environment' k=v list)
ENVLINE=""
for v in GUN_THETA_MIN GUN_THETA_MAX GUN_PHI_MIN GUN_PHI_MAX GUN_MULT; do
    if [ -n "${!v:-}" ]; then ENVLINE="${ENVLINE} ${v}=${!v}"; fi
done

cat > "$SUBFILE" <<EOF
# MAPS particle-gun production ${STAMP} -- ${NJOBS} jobs x ${NPER} evt = ${NEVENTS} events
# sample: ${SAMPLE}   particle: ${PARTICLE}   p: [${PMIN}, ${PMAX}]   seeds: ${SEEDBASE}+chunk
universe                = vanilla
executable              = ${RUNNER}
arguments               = \$(Process) ${NPER} ${SEEDBASE} ${PARTICLE} ${PMIN} ${PMAX} ${OUTDIR}
environment             = "${ENVLINE# }"
initialdir              = ${LOGDIR}
should_transfer_files   = NO
getenv                  = False
request_cpus            = 1
request_memory          = ${REQUEST_MEMORY}
request_disk            = ${REQUEST_DISK}
accounting_group        = ${ACCT_GROUP}
accounting_group_user   = ${USER}
+MaxRuntime             = ${MAXRUNTIME}
output                  = ${LOGDIR}/job_${STAMP}_\$(Process).out
error                   = ${LOGDIR}/job_${STAMP}_\$(Process).err
log                     = ${LOGDIR}/job_${STAMP}_\$(Process).log
queue ${NJOBS}
EOF

echo "================================================================"
echo "[submit] gun production: ${NJOBS} jobs x ${NPER} evt = ${NEVENTS} events"
echo "[submit] sample   : ${SAMPLE}"
echo "[submit] particle : ${PARTICLE}   p: [${PMIN}, ${PMAX}]   seeds: ${SEEDBASE}..$(( SEEDBASE + NJOBS - 1 ))"
echo "[submit] extra env: ${ENVLINE:-<none>}"
echo "[submit] outdir   : ${OUTDIR}"
echo "[submit] acct grp : ${ACCT_GROUP}   sub: ${SUBFILE}"
echo "================================================================"

if [ "${1:-}" = "--submit" ]; then
    if [ "$NQUEUED" -gt 0 ] && [ "$FORCE" != "1" ]; then
        echo "ERROR: $NQUEUED job(s) from a previous submission of this OUTDIR are" >&2
        echo "       still in the condor queue. Concurrent jobs on the same chunks race" >&2
        echo "       on the same output files. Wait, condor_rm them, or FORCE=1." >&2
        exit 1
    fi
    # production-config lock: identical resubmits (failure recovery) pass;
    # ANY config drift onto an existing OUTDIR is refused, no override
    LOCK="${OUTDIR}/production_config.txt"
    LOCKTMP="${LOCK}.candidate.$$"
    {
        echo "PARTICLE=${PARTICLE}"; echo "PMIN=${PMIN}"; echo "PMAX=${PMAX}"
        echo "SEEDBASE=${SEEDBASE}"; echo "NPER=${NPER}"; echo "NEVENTS=${NEVENTS}"
        echo "THETA_MIN=${TH_MIN}"; echo "THETA_MAX=${TH_MAX}"
        echo "PHI_MIN=${GUN_PHI_MIN:-0*deg}"; echo "PHI_MAX=${GUN_PHI_MAX:-360*deg}"
        echo "MULT=${GUN_MULT:-1}"
    } > "$LOCKTMP"
    if [ -s "$LOCK" ] && ! cmp -s "$LOCK" "$LOCKTMP"; then
        echo "ERROR: config differs from the production already in ${OUTDIR}:" >&2
        diff "$LOCK" "$LOCKTMP" >&2 || true
        echo "       A changed config over existing chunks silently corrupts the" >&2
        echo "       sample (stale sims reused, BX windows remapped). Use a new" >&2
        echo "       SAMPLE/OUTDIR, or restore the locked values." >&2
        rm -f "$LOCKTMP"; exit 1
    fi
    mv "$LOCKTMP" "$LOCK"
    echo "[submit] submitting ${NJOBS} jobs ..."
    condor_submit "$SUBFILE"
    echo "[submit] monitor:  condor_q ;  tail -f ${LOGDIR}/job_${STAMP}_0.err"
    echo "[submit] then:     SAMPLE=${SAMPLE} bash ${HERE}/harvest_gun.sh"
else
    echo "[submit] DRY RUN -- wrote ${SUBFILE} but did NOT submit. Re-run with --submit."
fi
