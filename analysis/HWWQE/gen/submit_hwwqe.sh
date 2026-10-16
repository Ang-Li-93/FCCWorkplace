#!/bin/bash
# Write (do not submit) an SDCC HTCondor description for N jobs of gen/run_hwwqe_job.sh.
#
#   submit_hwwqe.sh <card.sin> <copy|iso|diag> <n_jobs> <events_per_job> <output_dir> <first_seed>
#
# Seeds: WHIZARD 3.1.5 uses seed mod 32768 (src/rng/dispatch_rng_sub.f90: s = mod(seed, 32768))
# and consumes seed, seed+1, ... for its successive integrations and the simulation, so the jobs
# of one card get seeds first_seed + 50 i, all below 32768 (at most ~650 jobs per card); give each
# card/mode its own range.  The randomiser and Pythia8 take the same seed (full range).
#
# The description goes to <output_dir>/condor/hwwqe.sub; submit it yourself after approval:
#   condor_submit -name spoolsub02.sdcc.bnl.gov <output_dir>/condor/hwwqe.sub
# Settings follow the SDCC adaptations of documents/WINTER2023_FASTSIM.md: accounting group
# group_usfcc (+ accounting_group_user), getenv = False (clean worker environment, no
# "already set up" Key4hep failures), AlmaLinux9 + AVX2 workers.
set -euo pipefail
if [ $# -lt 6 ]; then sed -n '2,18p' "$0"; exit 1; fi
CARD=$(readlink -f "$1"); MODE=$2; NJOBS=$3; NEV=$4; OUT=$(readlink -m "$5"); SEED0=$6
STRIDE=50
LAST=$(( SEED0 + STRIDE * (NJOBS - 1) ))
if [ "$SEED0" -lt 1 ] || [ "$LAST" -ge 32768 ]; then
    echo "seeds $SEED0 .. $LAST must lie in [1, 32767] (WHIZARD uses seed mod 32768)" >&2; exit 1
fi
JOB=$(readlink -f "$(dirname "$0")/run_hwwqe_job.sh")
mkdir -p "$OUT/condor"
SUB="$OUT/condor/hwwqe.sub"
cat > "$SUB" <<EOF
executable            = $JOB
arguments             = $CARD $MODE $NEV \$(seed) $OUT
output                = $OUT/condor/job.\$(Cluster).\$(Process).out
error                 = $OUT/condor/job.\$(Cluster).\$(Process).err
log                   = $OUT/condor/job.\$(Cluster).log
getenv                = False
request_cpus          = 1
request_memory        = 2000
requirements          = ( (OpSysAndVer =?= "AlmaLinux9") && (TARGET.has_avx2 =?= True) )
accounting_group      = group_usfcc
accounting_group_user = $USER
on_exit_remove        = (ExitBySignal == False) && (ExitCode == 0)
max_retries           = 2
queue seed from (
$(seq "$SEED0" "$STRIDE" "$LAST")
)
EOF
echo "wrote $SUB ($NJOBS jobs x $NEV events, mode $MODE, card $(basename "$CARD"))"
echo "submit after approval: condor_submit -name spoolsub02.sdcc.bnl.gov $SUB"
