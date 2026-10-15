#!/bin/bash
# Smoke-test ONE radius variant: 1 BX ddsim on the variant master geometry.
# Verifies: (1) the DD4hep floor() stave/module formulas evaluate; (2) the
# geometry builds with no fatal overlap; (3) ddsim produces VertexBarrel hits.
#   Usage: smoke_variant.sh <tag>        e.g. smoke_variant.sh r070
set --   # clear args so setup_MAPS.sh does not parse them
TAG="${SMOKE_TAG}"
REPO=/gpfs/mnt/gpfs01/usfcc/ali3/FCCWorkplace
OUT=/tmp/claude-101884/-gpfs-mnt-gpfs01-usfcc-ali3-FCCWorkplace/1d3b3875-8e00-4fe1-8670-4d3d484fd29f/scratchpad/smoke
mkdir -p "$OUT"
COMPACT="$REPO/k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01_BIB_v2_${TAG}.xml"
STEER="$REPO/fcc_maps_wrapper_pixesl/simulation/maps_bib_steer.py"
INPUT=/gpfs/mnt/gpfs01/usfcc/MAPS_storage/BIB/LCC/V106.2/IPC/Z/output_100003.pairs
ROOT="$OUT/smoke_${TAG}.edm4hep.root"
LOG="$OUT/smoke_${TAG}.log"

source "$REPO/setup_MAPS.sh" >/dev/null 2>&1
echo "[smoke $TAG] compact=$COMPACT" | tee "$LOG"
BIB_SEED=42 timeout -k 30 1800 \
  ddsim --steeringFile "$STEER" \
        --compactFile  "$COMPACT" \
        --inputFiles   "$INPUT" \
        --numberOfEvents 1 \
        --outputFile   "$ROOT" >>"$LOG" 2>&1
rc=$?
echo "[smoke $TAG] ddsim rc=$rc" | tee -a "$LOG"
echo "[smoke $TAG] OVERLAP lines:" | tee -a "$LOG"
grep -ic 'overlap' "$LOG" | tee -a "$LOG"
echo "[smoke $TAG] FATAL/ERROR lines:" | tee -a "$LOG"
grep -iE 'fatal|Exception| ERROR ' "$LOG" | grep -v 'ERROR 0' | head -5 | tee -a "$LOG"
# count VertexBarrel SimTrackerHits in the output
python3 - "$ROOT" "$TAG" <<'PY' 2>>"$LOG" | tee -a "$LOG"
import sys, uproot
f, tag = sys.argv[1], sys.argv[2]
try:
    t = uproot.open(f)["events"]
    br = [b for b in t.keys() if "VertexBarrel" in b and b.endswith(".cellID")]
    n = len(t[br[0]].array(library="np")[0]) if br else 0
    print(f"[smoke {tag}] VertexBarrel SimHits in evt0: {n}  (branch={br[0] if br else 'NONE'})")
except Exception as e:
    print(f"[smoke {tag}] READ ERROR: {e}")
PY
echo "[smoke $TAG] DONE rc=$rc" | tee -a "$LOG"
