#!/usr/bin/env bash
#
# submit_ddsim_condor.sh  -  chunked HTCondor production, SELF-CONTAINED jobs.
#
#   bash submit_ddsim_condor.sh [--submit]
#
# NJOBS = ceil(NEVENTS/NPER) condor jobs. Each job (run_chunk.sh) generates its
# OWN NPER events with WHIZARD (seed = SEED_BASE+i) and runs ddsim, writing
# OUTDIR/events_<i>.edm4hep.root. No pre-generation, no shared stdhep, no grid
# reuse -- fully independent (EventProducer-style). Dry-run unless --submit.
#
# Env config:
#   NEVENTS    total events            (default 10000)
#   NPER       events per job          (default 200  -> 50 jobs)
#   CARD       WHIZARD .sin            (default wzp6_ee_qq_ecm91p2)
#   COMPACT    detector compact xml    (MAPS_o1_v01)
#   STEERING   ddsim steering          (maps_steer.py)
#   OUTDIR     edm4hep output dir (gpfs, writable)
#   ACCT_GROUP condor accounting group (default group_usfcc)
#   SEED_BASE / REQUEST_MEMORY / REQUEST_DISK / MAXRUNTIME

set -euo pipefail
HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REPO_ROOT="$( cd "$HERE/../.." >/dev/null 2>&1 && pwd )"

NEVENTS="${NEVENTS:-10000}"
NPER="${NPER:-200}"
CARD="${CARD:-${REPO_ROOT}/FCC-config/winter2023/FCCee/Generator/Whizard/v3.0.3/wzp6_ee_qq_ecm91p2.sin}"
COMPACT="${COMPACT:-${REPO_ROOT}/k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01.xml}"
STEERING="${STEERING:-${REPO_ROOT}/fcc_maps_wrapper_pixesl/simulation/maps_steer.py}"
OUTDIR="${OUTDIR:-/gpfs/mnt/gpfs01/usfcc/MAPS_storage/generation/edm4hep/winter2023/wzp6_ee_qq_ecm91p2}"
ACCT_GROUP="${ACCT_GROUP:-group_usfcc}"
SEED_BASE="${SEED_BASE:-42}"
REQUEST_MEMORY="${REQUEST_MEMORY:-8192}"     # MB; ALLEGRO full sim peaks >3 GB (cgroup-enforced at SDCC); 8 GB = safe margin
REQUEST_DISK="${REQUEST_DISK:-3145728}"      # KB = 3 GB (stdhep scratch + output)
MAXRUNTIME="${MAXRUNTIME:-28800}"            # s = 8 h (integration + sim per job)

NJOBS=$(( (NEVENTS + NPER - 1) / NPER ))
RUNNER="${HERE}/run_chunk.sh"
SUBDIR="${OUTDIR}/condor"; LOGDIR="${SUBDIR}/logs"; SUBFILE="${SUBDIR}/maps_qq.sub"

for f in "$CARD" "$COMPACT" "$STEERING" "$RUNNER"; do
    [ -e "$f" ] || { echo "ERROR: missing $f" >&2; exit 1; }
done
command -v condor_submit >/dev/null 2>&1 || { echo "ERROR: condor_submit not found" >&2; exit 1; }
mkdir -p "$OUTDIR" "$LOGDIR"; chmod +x "$RUNNER"

cat > "$SUBFILE" <<EOF
# MAPS qq self-contained production -- ${NJOBS} jobs x ${NPER} evt = ${NEVENTS} events
universe                = vanilla
executable              = ${RUNNER}
arguments               = \$(Process) ${NPER} ${CARD} ${COMPACT} ${STEERING} ${OUTDIR} ${SEED_BASE}
should_transfer_files   = NO
getenv                  = False
request_cpus            = 1
request_memory          = ${REQUEST_MEMORY}
request_disk            = ${REQUEST_DISK}
accounting_group        = ${ACCT_GROUP}
accounting_group_user   = ${USER}
+MaxRuntime             = ${MAXRUNTIME}
output                  = ${LOGDIR}/job_\$(Process).out
error                   = ${LOGDIR}/job_\$(Process).err
log                     = ${LOGDIR}/job_\$(Process).log
queue ${NJOBS}
EOF

echo "================================================================"
echo "[submit] SELF-CONTAINED: ${NJOBS} jobs x ${NPER} evt = ${NEVENTS} events"
echo "[submit] each job: WHIZARD(${NPER} evt) + ddsim  (no pre-gen, no reuse)"
echo "[submit] card     : ${CARD}"
echo "[submit] compact  : ${COMPACT}"
echo "[submit] steering : ${STEERING}"
echo "[submit] outdir   : ${OUTDIR}"
echo "[submit] acct grp : ${ACCT_GROUP}   sub: ${SUBFILE}"
echo "================================================================"

if [ "${1:-}" = "--submit" ]; then
    echo "[submit] submitting ${NJOBS} jobs ..."
    condor_submit "$SUBFILE"
    echo "[submit] monitor:  condor_q ;  tail -f ${LOGDIR}/job_0.err"
    echo "[submit] then:     NPER=${NPER} bash ${HERE}/harvest_pixesl.sh --plot"
else
    echo "[submit] DRY RUN -- wrote ${SUBFILE} but did NOT submit. Re-run with --submit."
fi
