#!/bin/bash
# One HWWQE dedicated-generation job (PLAN.md Sec. 5.3, samples S1 / S2 / S3), gen/README.md:
#   1) WHIZARD 3.1.5 pass-1 card (config/generation/hwwqe_zh_lvqq_<Z>.sin): e+e- -> Z H with
#      the winter2023 production settings x H -> l nu q q' (1->4 matrix element), partonic LHEF;
#   2) gen/randomise_w_decays.py: W decay directions re-drawn (copy = S1, iso = S2, diag = S3),
#      H -> W+ W- resonance lines inserted, beams written as the incoming particles;
#   3) DelphesPythia8_EDM4HEP (Pythia8 shower + hadronisation + Delphes IDEA, EDM4hep) in the
#      winter2023 reconstruction stack of EventProducer (prodTag['winter2023'] = 2024-03-10).
# Each step runs in its own clean shell: the generation stack (EventProducer 'defaultstack',
# Key4hep 2026-04-08: WHIZARD 3.1.5) and the reconstruction stack are never mixed.
#
#   run_hwwqe_job.sh <card.sin> <copy|iso|diag> <n_events> <seed> <output_dir> [detector]
#
# <seed> must lie in [1, 32767]: WHIZARD 3.1.5 reduces it modulo 32768 and uses seed, seed+1, ...,
# seed+18 for the integrations and the simulation of the pass-1 cards (gen/README.md, Seeds).
# The randomiser and Pythia8 use the same seed.
#
# Output: <output_dir>/events_<seed>.root (EDM4hep, pre-edm4hep1: MC relations are the
# '_Particle_parents/_Particle_daughters' branches of podio 2024), <output_dir>/lhe/
# events_<seed>.lhe.gz (randomised partonic events) and <output_dir>/logs/<seed>.tar.gz.
set -euo pipefail

if [ $# -lt 5 ]; then
    sed -n '2,20p' "$0"; exit 1
fi
CARD=$(readlink -f "$1"); MODE=$2; NEV=$3; SEED=$4; OUT=$(readlink -f "$5"); DET=${6:-IDEA}
case "$MODE" in copy|iso|diag) ;; *) echo "mode must be copy, iso or diag" >&2; exit 1 ;; esac
if ! [[ "$SEED" =~ ^[0-9]+$ ]] || [ "$SEED" -lt 1 ] || [ "$SEED" -ge 32768 ]; then
    echo "seed must be an integer in [1, 32767] (WHIZARD 3.1.5 uses seed mod 32768, gen/README.md)" >&2; exit 1
fi

HWWQE=$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)
REPO=$(cd "$HWWQE/../.." && pwd)
FCCCFG=$REPO/FCC-config/winter2023/FCCee
GEN_STACK="/cvmfs/sw.hsf.org/key4hep/setup.sh -r 2026-04-08"   # EventProducer defaultstack (WHIZARD 3.1.5)
RECO_STACK="/cvmfs/sw.hsf.org/key4hep/setup.sh -r 2024-03-10"  # EventProducer prodTag['winter2023']

WORK=$(mktemp -d "${_CONDOR_SCRATCH_DIR:-${TMPDIR:-/tmp}}/hwwqe_${SEED}_XXXX")
mkdir -p "$OUT/lhe" "$OUT/logs"
cd "$WORK"
clean() { env -u LD_LIBRARY_PATH -u PYTHONHOME -u PYTHONPATH -u KEY4HEP_STACK OMP_NUM_THREADS=1 bash -c "$1"; }
now() { date +%s.%N; }
T0=$(now)

# 1) WHIZARD pass 1 (n_events, seed prepended as EventProducer does)
printf 'n_events = %d\nseed = %d\n' "$NEV" "$SEED" > header.sin
cat header.sin "$CARD" > card.sin
clean "source $GEN_STACK >/dev/null 2>&1 && whizard card.sin > whizard.log 2>&1"
test -s partonic.lhe
T1=$(now)

# 2) re-draw the W decays
clean "source $GEN_STACK >/dev/null 2>&1 && python3 $HWWQE/gen/randomise_w_decays.py --flatten-higgs \
       --insert-resonances --beams-as-incoming --mode $MODE --seed $SEED partonic.lhe events.lhe" 2> randomise.log
T2=$(now)

# 3) Pythia8 + Delphes
cp "$HWWQE/config/generation/p8_lhe_hwwqe_ecm240.cmnd" p8.cmd
printf 'Main:numberOfEvents = %d\nRandom:seed = %d\n' "$NEV" $(( SEED % 900000000 )) >> p8.cmd
cp "$FCCCFG/Delphes/card_${DET}.tcl" card.tcl
cp "$FCCCFG/Delphes/edm4hep_${DET}.tcl" edm4hep_output_config.tcl
clean "source $RECO_STACK >/dev/null 2>&1 && DelphesPythia8_EDM4HEP card.tcl edm4hep_output_config.tcl p8.cmd events_${SEED}.root > delphes.log 2>&1"
T3=$(now)
awk -v a="$T0" -v b="$T1" -v c="$T2" -v d="$T3" -v n="$NEV" 'BEGIN { printf "timing [s]: whizard %.1f, randomise %.1f, pythia8+delphes %.1f, total %.1f (%d events)\n", b - a, c - b, d - c, d - a, n }' | tee timing.txt

cp "events_${SEED}.root" "$OUT/"
gzip -c events.lhe > "$OUT/lhe/events_${SEED}.lhe.gz"
tar czf "$OUT/logs/${SEED}.tar.gz" card.sin whizard.log randomise.log p8.cmd delphes.log timing.txt
cd /
rm -r -- "$WORK"
echo "done: $OUT/events_${SEED}.root"
