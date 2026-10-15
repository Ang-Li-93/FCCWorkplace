#!/bin/bash
# Leptonic (Z->mumu / Z->ee) combine fit, ecm 240. Run INSIDE the combine container, from this dir:
#   cd analysis/ZH_XSec/Paper/S240/combine && /gpfs/mnt/gpfs01/usfcc/ali3/FCCWorkplace/run_combine.sh ./run_fit_leptonic.sh mumu
# Usage: ./run_fit_leptonic.sh <mumu|ee> [recoil|bdt]     [FIT_BASE=<dir>: parent of the run dirs, default this dir]
#                                                          [RUNDIR_SUFFIX=<sfx>: run dir run_recoil_2cat_<flavor><sfx>, default none - the variant
#                                                           dirs of 'makeWS_recoil_2cat.py --tag <sfx>' (e.g. _excl); recoil mode only, rejected for bdt]
#   recoil (default) paper spec (arXiv:2512.21290 Sec 5.2/5.3): recoil mass 100-150 GeV in two BDT
#                    regions, signal = all ZH final states, per-component 1% lnN backgrounds.
#                    Input: run_recoil_2cat_<flavor>/{datacard.root,datacard_recoil_2cat_<flavor>.txt}
#                    from 'python3 makeWS_recoil_2cat.py <flavor>' (key4hep env)
#   bdt              July-2026 cross-check: binned BDT-score fit, lumped background with a free rateParam.
#                    Input: run_binned_BDTScore_<flavor>/{datacard.root,datacard_binned_<flavor>.txt}
#                    from 'python3 makeWS_BDT_binned.py <flavor>' (key4hep env)
#
# text2workspace + three Asimov MultiDimFit grid scans of r = sigma_ZH / SM, then the 1-sigma
# precisions (fit_precision.py) and the scan-reliability audit (audit_scans.py), tee'd to
# <rundir>/fit_summary.txt:
#   xsec           total: every nuisance floating
#   xsecSTAT       stat-only, paper definition: background normalization fixed, i.e.
#                  allConstrainedNuisances + every rateParam of the card frozen
#   xsecSTATshapes stat-only, July-2026 run-book definition (documents/ZH_XSEC_RUNS.md): only the
#                  shape nuisances frozen (MUSCALE|ELSCALE, BES, SQRTS; the bkg rateParam / norm_* float)
# The freeze lists are parsed from the card (rateParam / shape lines), not hard-coded; the recoil
# cards have no rateParam (paper: constrained normalizations), so there xsecSTAT freezes
# allConstrainedNuisances only.
# Do NOT source the key4hep env inside the container.
set -euo pipefail
ECM=240   # the S365 copy differs only in this line and the header
FLAVOR="${1:-}"
MODE="${2:-recoil}"
case "$FLAVOR" in
  mumu|ee) ;;
  *) echo "usage: $0 <mumu|ee> [recoil|bdt]"; exit 1 ;;
esac
HERE="$(cd "$(dirname "$0")" && pwd)"
[ -d "${FIT_BASE:-$HERE}" ] || { echo "ERROR: FIT_BASE=${FIT_BASE:-$HERE} is not a directory"; exit 1; }
FIT_BASE="$(cd "${FIT_BASE:-$HERE}" && pwd)"
RUNDIR_SUFFIX="${RUNDIR_SUFFIX:-}"
case "$RUNDIR_SUFFIX" in *[[:space:]/]*) echo "ERROR: RUNDIR_SUFFIX=$RUNDIR_SUFFIX must be a plain name fragment (no whitespace or /)"; exit 1 ;; esac
case "$MODE" in
  recoil) RUNDIR="$FIT_BASE/run_recoil_2cat_$FLAVOR$RUNDIR_SUFFIX"
          CARD="datacard_recoil_2cat_$FLAVOR.txt"    # copy made by makeWS_recoil_2cat.py; shapes -> ./datacard.root
          MAKEWS="python3 makeWS_recoil_2cat.py $FLAVOR${RUNDIR_SUFFIX:+ --tag $RUNDIR_SUFFIX}" ;;
  bdt)    [ -z "$RUNDIR_SUFFIX" ] || { echo "ERROR: RUNDIR_SUFFIX=$RUNDIR_SUFFIX applies to the recoil (paper-spec) cards only: makeWS_BDT_binned.py has no --tag, so no run_binned_BDTScore_$FLAVOR$RUNDIR_SUFFIX can exist"; exit 1; }
          RUNDIR="$FIT_BASE/run_binned_BDTScore_$FLAVOR"
          CARD="datacard_binned_$FLAVOR.txt"         # copy made by makeWS_BDT_binned.py (bkg -> bkg_<flavor>); shapes -> ./datacard.root
          MAKEWS="python3 makeWS_BDT_binned.py $FLAVOR" ;;
  *)      echo "usage: $0 <mumu|ee> [recoil|bdt]"; exit 1 ;;
esac
for f in "$RUNDIR/datacard.root" "$RUNDIR/$CARD"; do
  [ -f "$f" ] || { echo "ERROR: $f missing - run '$MAKEWS' first (key4hep env)"; exit 1; }
done

# scan range/points: fit_precision.py and audit_scans.py warn if the 2dNLL=1 crossings fall
# outside the range - widen here (or override with RANGE=r=a,b POINTS=n) and re-run
case "$ECM" in
  240) RANGE="${RANGE:-r=0.97,1.03}"; POINTS="${POINTS:-120}" ;;
  365) RANGE="${RANGE:-r=0.92,1.08}"; POINTS="${POINTS:-160}" ;;
  *)   echo "ERROR: unsupported ECM=$ECM"; exit 1 ;;
esac

cd "$RUNDIR"
strip() { sed 's/#.*//' "$CARD"; }
RATEPARAMS="$(strip | awk '$2=="rateParam"{print $1}' | sort -u | paste -sd,)"
SHAPES="$(strip | awk '$2=="shape"{print $1}' | sort -u | paste -sd,)"
if [ "$MODE" = bdt ]; then
  [ -n "$RATEPARAMS" ] || { echo "ERROR: no rateParam line found in $RUNDIR/$CARD (the binned-BDT card has a free background rateParam)"; exit 1; }
fi
[ -n "$SHAPES" ]     || { echo "ERROR: no shape nuisance found in $RUNDIR/$CARD"; exit 1; }
FREEZE_STAT="allConstrainedNuisances${RATEPARAMS:+,$RATEPARAMS}"
FREEZE_SHAPES="$SHAPES"
echo "== $FLAVOR @ $ECM GeV ($MODE)  rundir=$RUNDIR  card=$CARD${RUNDIR_SUFFIX:+  suffix=$RUNDIR_SUFFIX}"
echo "== range=$RANGE points=$POINTS"
echo "== xsecSTAT freeze:       $FREEZE_STAT"
echo "== xsecSTATshapes freeze: $FREEZE_SHAPES"

text2workspace.py "$CARD" -o ws.root

COMMON=(-M MultiDimFit -t -1 --setParameterRanges "$RANGE" --points="$POINTS" --algo=grid ws.root
        --expectSignal=1 -m 125 --X-rtd TMCSO_AdaptivePseudoAsimov --X-rtd ADDNLL_CBNLL=0
        --cminDefaultMinimizerStrategy 0)
combine "${COMMON[@]}" -n xsec
combine "${COMMON[@]}" --freezeParameters="$FREEZE_STAT"   -n xsecSTAT
combine "${COMMON[@]}" --freezeParameters="$FREEZE_SHAPES" -n xsecSTATshapes

{
  echo "== $FLAVOR @ $ECM GeV ($MODE): total vs xsecSTAT (paper stat-only: $FREEZE_STAT)"
  python3 "$HERE/fit_precision.py" higgsCombinexsec.MultiDimFit.mH125.root higgsCombinexsecSTAT.MultiDimFit.mH125.root
  echo "== $FLAVOR @ $ECM GeV ($MODE): total vs xsecSTATshapes (July run-book stat-only: $FREEZE_SHAPES)"
  python3 "$HERE/fit_precision.py" higgsCombinexsec.MultiDimFit.mH125.root higgsCombinexsecSTATshapes.MultiDimFit.mH125.root
  echo "== scan audit ($RUNDIR)"
  python3 "$HERE/audit_scans.py" "$RUNDIR"
} 2>&1 | tee fit_summary.txt
