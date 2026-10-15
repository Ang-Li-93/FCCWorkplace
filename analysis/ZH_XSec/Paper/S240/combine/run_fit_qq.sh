#!/bin/bash
# Hadronic (Z->qq) combine fit, ecm 240. Run INSIDE the combine container, from this dir:
#   cd analysis/ZH_XSec/Paper/S240/combine && /gpfs/mnt/gpfs01/usfcc/ali3/FCCWorkplace/run_combine.sh ./run_fit_qq.sh
# Usage: ./run_fit_qq.sh [2d|2d-jesjer|2d-zhbkg|bdt]     [FIT_BASE=<dir>: parent of the run dirs, default this dir]
#                                              [QQ_RUNDIR_SUFFIX=<sfx>: the 2d / 2d-zhbkg run dir gets the suffix,
#                                               run_2D_mrecoil_mjj_qq[_zhbkg]<sfx> = the variants of 'makeWS_2D_qq.py
#                                               --tag <sfx>' (e.g. _nott: 365 GeV without the ttbar template); default
#                                               none; rejected for bdt (makeWS_BDT_binned.py has no --tag)]
#   2d        (default) paper spec (arXiv:2512.21290 Sec 5.2/5.3): unrolled m_recoil x m_jj in two
#             BDT-score categories, signal = all ZH final states, per-component 1% lnN backgrounds
#             (norm_WW/ZZ/Zqq/rare), shapes JETSCALE / SQRTS / BES.
#             Input: run_2D_mrecoil_mjj_qq/{datacard.root,datacard_2d_qq.txt}
#             from 'python3 makeWS_2D_qq.py' (key4hep env). A run dir written by 'makeWS_2D_qq.py
#             --jesjer|--jes-only|--jer-only --tag <sfx>' holds datacard_2d_qq_jesjer.txt INSTEAD
#             (JES / JER shape nuisances on every process): 2d fits whichever of the two cards the
#             run dir holds (both present = error), so QQ_RUNDIR_SUFFIX=_oldbdt_jesjer ./run_fit_qq.sh 2d
#             fits run_2D_mrecoil_mjj_qq_oldbdt_jesjer/ with JES and JER profiled in xsec and frozen
#             in xsecSTATshapes (with every other shape nuisance).
#             A run dir written by 'makeWS_2D_qq.py --recoil-only --tag <sfx>' (CUT-BASED hadronic fit, paper
#             Table 2 'Cut-based': one region sel_Baseline_nomva, the m_recoil projection as the observable)
#             holds the ONE-bin derivation of datacard_2d_qq.txt (bin nomva) under the same names: 2d fits it
#             unchanged with QQ_RUNDIR_SUFFIX=<sfx> (nothing here depends on the number of bins; the '2D' in
#             the run dir name is historical there) and marks the log and fit_summary.txt 'ONE-bin card'.
#   2d-jesjer as 2d, but REQUIRES datacard_2d_qq_jesjer.txt in the run dir (explicit JES/JER fit).
#   2d-zhbkg  July-2026 definition, cross-check: signal = Z(qq/ss/cc/bb)H only, ZH with a
#             non-hadronic Z as the background bkg_ZH (norm_ZH), no BES.
#             Input: run_2D_mrecoil_mjj_qq_zhbkg/{datacard.root,datacard_2d_qq_zhbkg.txt}
#             from 'python3 makeWS_2D_qq.py --zh-other-as-bkg'
#   bdt       cross-check: full-range binned BDT-score shape, lumped background with a free rateParam.
#             Input: run_binned_BDTScore_qq/{datacard.root,datacard_binned_qq.txt}
#             from 'python3 makeWS_BDT_binned.py qq'
#
# text2workspace + three Asimov MultiDimFit grid scans of r = sigma_ZH / SM, then the 1-sigma
# precisions (fit_precision.py) and the scan-reliability audit (audit_scans.py), tee'd to
# <rundir>/fit_summary.txt:
#   xsec           total: every nuisance floating
#   xsecSTAT       stat-only, paper definition: background normalizations fixed, i.e.
#                  allConstrainedNuisances + every rateParam of the card frozen. For the 2d cards
#                  (no rateParam) this is what the July driver called 'stat' (it froze the five
#                  norm_* lnN plus JETSCALE,SQRTS by name = every constrained nuisance).
#   xsecSTATshapes stat-only, July-2026 run-book definition (documents/ZH_XSEC_RUNS.md): only the
#                  shape nuisances frozen (JETSCALE, SQRTS[, BES][, JES, JER]; the norm_* / rateParam
#                  float) = stat + 1% background normalizations
# The freeze lists are parsed from the card (rateParam / shape lines), not hard-coded: for
# datacard_2d_qq.txt the derived xsecSTATshapes list is BES,JETSCALE,SQRTS (the former hard-coded
# string), for datacard_2d_qq_jesjer.txt BES,JES,JER,JETSCALE,SQRTS; both are printed.
# Do NOT source the key4hep env inside the container.
set -euo pipefail
ECM=240   # the S365 copy differs only in this line and the header
MODE="${1:-2d}"
HERE="$(cd "$(dirname "$0")" && pwd)"
[ -d "${FIT_BASE:-$HERE}" ] || { echo "ERROR: FIT_BASE=${FIT_BASE:-$HERE} is not a directory"; exit 1; }
FIT_BASE="$(cd "${FIT_BASE:-$HERE}" && pwd)"
QQ_RUNDIR_SUFFIX="${QQ_RUNDIR_SUFFIX:-}"
case "$QQ_RUNDIR_SUFFIX" in *[[:space:]/]*) echo "ERROR: QQ_RUNDIR_SUFFIX=$QQ_RUNDIR_SUFFIX must be a plain name fragment (no whitespace or /)"; exit 1 ;; esac
TAGOPT="${QQ_RUNDIR_SUFFIX:+ --tag $QQ_RUNDIR_SUFFIX}"
case "$MODE" in
  2d)       RUNDIR="$FIT_BASE/run_2D_mrecoil_mjj_qq$QQ_RUNDIR_SUFFIX"
            # makeWS_2D_qq.py leaves ONE card in the run dir: datacard_2d_qq.txt, or with --jesjer /
            # --jes-only / --jer-only datacard_2d_qq_jesjer.txt (JES/JER shape lines); fit the one present
            if [ -f "$RUNDIR/datacard_2d_qq_jesjer.txt" ]; then
              [ -f "$RUNDIR/datacard_2d_qq.txt" ] && { echo "ERROR: $RUNDIR holds both datacard_2d_qq.txt and datacard_2d_qq_jesjer.txt - ambiguous; rebuild it with makeWS_2D_qq.py (which leaves one card) or use 2d-jesjer"; exit 1; }
              CARD="datacard_2d_qq_jesjer.txt"      # copy made by makeWS_2D_qq.py --jesjer|--jes-only|--jer-only [--tag]
              MAKEWS="python3 makeWS_2D_qq.py --jesjer$TAGOPT"
            else
              CARD="datacard_2d_qq.txt"             # copy made by makeWS_2D_qq.py [--tag]; shapes -> ./datacard.root
              MAKEWS="python3 makeWS_2D_qq.py$TAGOPT"
            fi ;;
  2d-jesjer) RUNDIR="$FIT_BASE/run_2D_mrecoil_mjj_qq$QQ_RUNDIR_SUFFIX"
            CARD="datacard_2d_qq_jesjer.txt"        # copy made by makeWS_2D_qq.py --jesjer|--jes-only|--jer-only [--tag]
            MAKEWS="python3 makeWS_2D_qq.py --jesjer$TAGOPT" ;;
  2d-zhbkg) RUNDIR="$FIT_BASE/run_2D_mrecoil_mjj_qq_zhbkg$QQ_RUNDIR_SUFFIX"
            CARD="datacard_2d_qq_zhbkg.txt"         # copy made by makeWS_2D_qq.py --zh-other-as-bkg [--tag]
            MAKEWS="python3 makeWS_2D_qq.py --zh-other-as-bkg$TAGOPT" ;;
  bdt)      [ -z "$QQ_RUNDIR_SUFFIX" ] || { echo "ERROR: QQ_RUNDIR_SUFFIX=$QQ_RUNDIR_SUFFIX applies to the 2d / 2d-zhbkg run dirs only (makeWS_BDT_binned.py has no --tag, so no run_binned_BDTScore_qq$QQ_RUNDIR_SUFFIX can exist)"; exit 1; }
            RUNDIR="$FIT_BASE/run_binned_BDTScore_qq"
            CARD="datacard_binned_qq.txt"           # copy made by makeWS_BDT_binned.py qq
            MAKEWS="python3 makeWS_BDT_binned.py qq" ;;
  *)        echo "usage: $0 [2d|2d-jesjer|2d-zhbkg|bdt]"; exit 1 ;;
esac
for f in "$RUNDIR/datacard.root" "$RUNDIR/$CARD"; do
  [ -f "$f" ] || { echo "ERROR: $f missing - run '$MAKEWS' first (key4hep env)"; exit 1; }
done

# scan range/points: fit_precision.py and audit_scans.py warn if the 2dNLL=1 crossings fall
# outside the range - widen here (or override with RANGE=r=a,b POINTS=n) and re-run
case "$ECM" in
  240) RANGE="${RANGE:-r=0.97,1.03}"; POINTS="${POINTS:-120}" ;;
  365) RANGE="${RANGE:-r=0.95,1.05}"; POINTS="${POINTS:-160}" ;;
  *)   echo "ERROR: unsupported ECM=$ECM"; exit 1 ;;
esac

cd "$RUNDIR"
strip() { sed 's/#.*//' "$CARD"; }
RATEPARAMS="$(strip | awk '$2=="rateParam"{print $1}' | sort -u | paste -sd,)"
SHAPES="$(strip | awk '$2=="shape"{print $1}' | sort -u | paste -sd,)"
if [ "$MODE" = bdt ]; then
  [ -n "$RATEPARAMS" ] || { echo "ERROR: no rateParam line found in $RUNDIR/$CARD (the binned-BDT card has a free background rateParam)"; exit 1; }
else
  [ -z "$RATEPARAMS" ] || { echo "ERROR: unexpected rateParam ($RATEPARAMS) in $RUNDIR/$CARD (the 2D cards constrain the backgrounds with lnN)"; exit 1; }
fi
[ -n "$SHAPES" ]     || { echo "ERROR: no shape nuisance found in $RUNDIR/$CARD"; exit 1; }
if [ "$MODE" = 2d ] || [ "$MODE" = 2d-jesjer ]; then
  if ! strip | awk '$2=="shape"{print $1}' | grep -qx BES; then
    echo "ERROR: $RUNDIR/$CARD carries no BES shape nuisance - not the paper-spec card (2d-zhbkg for the July definition)"; exit 1
  fi
fi
JESJER="$(strip | awk '$2=="shape" && ($1=="JES" || $1=="JER"){print $1}' | sort -u | paste -sd,)"
if [ "$CARD" = datacard_2d_qq_jesjer.txt ] && [ -z "$JESJER" ]; then
  echo "ERROR: $RUNDIR/$CARD carries neither a JES nor a JER shape line"; exit 1
fi
FREEZE_STAT="allConstrainedNuisances${RATEPARAMS:+,$RATEPARAMS}"
FREEZE_SHAPES="$SHAPES"
# a run dir of 'makeWS_2D_qq.py --recoil-only' holds the ONE-bin derivation of the card (imax 1, bin nomva, the
# m_recoil projection: the cut-based fit); nothing above depends on the number of bins - say so in the log/summary
ONEBIN=""
if [ "$(strip | awk '$1=="imax"{print $2; exit}')" = 1 ]; then
  ONEBIN="== ONE-bin card (imax 1): recoil-only CUT-BASED fit from 'makeWS_2D_qq.py --recoil-only' - one region nomva, m_recoil only; the '2D' in the run dir name is historical"
fi
echo "== qq @ $ECM GeV ($MODE)  rundir=$RUNDIR  card=$CARD${QQ_RUNDIR_SUFFIX:+  suffix=$QQ_RUNDIR_SUFFIX}"
[ -z "$ONEBIN" ] || echo "$ONEBIN"
echo "== range=$RANGE points=$POINTS"
echo "== xsecSTAT freeze:       $FREEZE_STAT"
echo "== xsecSTATshapes freeze: $FREEZE_SHAPES"
[ -z "$JESJER" ] || echo "== JES/JER nuisances in $CARD: $JESJER (floating in xsec, frozen in xsecSTATshapes and xsecSTAT)"

text2workspace.py "$CARD" -o ws.root

COMMON=(-M MultiDimFit -t -1 --setParameterRanges "$RANGE" --points="$POINTS" --algo=grid ws.root
        --expectSignal=1 -m 125 --X-rtd TMCSO_AdaptivePseudoAsimov --X-rtd ADDNLL_CBNLL=0
        --cminDefaultMinimizerStrategy 0)
combine "${COMMON[@]}" -n xsec
combine "${COMMON[@]}" --freezeParameters="$FREEZE_STAT"   -n xsecSTAT
combine "${COMMON[@]}" --freezeParameters="$FREEZE_SHAPES" -n xsecSTATshapes

{
  [ -z "$ONEBIN" ] || echo "$ONEBIN"
  echo "== qq @ $ECM GeV ($MODE): total vs xsecSTAT (paper stat-only: $FREEZE_STAT)"
  python3 "$HERE/fit_precision.py" higgsCombinexsec.MultiDimFit.mH125.root higgsCombinexsecSTAT.MultiDimFit.mH125.root
  echo "== qq @ $ECM GeV ($MODE): total vs xsecSTATshapes (July run-book stat-only: $FREEZE_SHAPES)"
  python3 "$HERE/fit_precision.py" higgsCombinexsec.MultiDimFit.mH125.root higgsCombinexsecSTATshapes.MultiDimFit.mH125.root
  echo "== scan audit ($RUNDIR)"
  python3 "$HERE/audit_scans.py" "$RUNDIR"
} 2>&1 | tee fit_summary.txt
