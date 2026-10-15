#!/bin/bash
# Channel-combination combine fit, ecm 365. Run INSIDE the combine container, from this dir:
#   cd analysis/ZH_XSec/Paper/S365/combine && /gpfs/mnt/gpfs01/usfcc/ali3/FCCWorkplace/run_combine.sh ./run_fit_combination.sh all
# Usage: ./run_fit_combination.sh <ll|all> [recoil|bdt]    [FIT_BASE=<dir>: parent of the run dirs, default this dir]
#                                                           [RUNDIR_SUFFIX=<sfx>: the leptonic channel dirs run_recoil_2cat_{mumu,ee}<sfx> and the
#                                                            output dir get the suffix; the qq dir takes QQ_RUNDIR_SUFFIX instead. Default none; the
#                                                            variants of 'makeWS_recoil_2cat.py --tag <sfx>'; recoil cards only, rejected for bdt]
#                                                           [QQ_RUNDIR_SUFFIX=<sfx>: 'all' only - the qq input dir run_2D_mrecoil_mjj_qq<sfx> (the
#                                                            variants of 'makeWS_2D_qq.py --tag <sfx>', e.g. _nott: 365 GeV without the ttbar
#                                                            template) and the output dir run_<ecm>_all[_bdt]<RUNDIR_SUFFIX><sfx>; default none]
#                                                           [ALL_RUNDIR_SUFFIX=<sfx>: 'all' only - EXPLICIT suffix of the output dir
#                                                            run_<ecm>_all[_bdt]<sfx>, overriding the automatic composition
#                                                            <RUNDIR_SUFFIX><QQ_RUNDIR_SUFFIX> (identical suffixes not doubled), e.g.
#                                                            RUNDIR_SUFFIX=_oldbdt QQ_RUNDIR_SUFFIX=_oldbdt_jesjer ALL_RUNDIR_SUFFIX=_oldbdt_jesjer
#                                                            -> run_<ecm>_all_oldbdt_jesjer; may be empty (= no suffix)]
#   ll = mumu+ee, all = mumu+ee+qq(2D m_recoil x m_jj card run_2D_mrecoil_mjj_qq/, makeWS_2D_qq.py)
#   recoil (default) paper-spec leptonic cards run_recoil_2cat_{mumu,ee}/datacard_recoil_2cat_<flavor>.txt
#                    (makeWS_recoil_2cat.py) -> run_recoil_2cat_combined/datacard_combined.txt (ll)
#                    or run_<ecm>_all/datacard_all.txt (all)
#   bdt              July-2026 cross-check cards run_binned_BDTScore_{mumu,ee}/datacard_binned_<flavor>.txt
#                    (makeWS_BDT_binned.py) -> run_binned_BDTScore_combined/datacard_combined.txt (ll)
#                    or run_<ecm>_all_bdt/datacard_all.txt (all)
#
# combineCards.py on the ABSOLUTE channel-card paths (so the shapes lines of the combined card are
# absolute and resolve from anywhere); text2workspace; three Asimov MultiDimFit grid scans of
# r = sigma_ZH / SM; then fit_precision.py + audit_scans.py, tee'd to <rundir>/fit_summary.txt:
#   xsec           total: every nuisance floating
#   xsecSTAT       stat-only, paper definition: background normalizations fixed, i.e.
#                  allConstrainedNuisances + every rateParam of the combined card frozen
#                  (bdt cards: background_norm, bkg_ee_norm, ... - parsed from the card, not hard-coded;
#                  the recoil cards have none: constrained norm_* lnN, frozen via allConstrainedNuisances)
#   xsecSTATshapes stat-only, July-2026 run-book definition (documents/ZH_XSEC_RUNS.md): only the
#                  shape nuisances frozen (MUSCALE, ELSCALE, BES, SQRTS[, JETSCALE][, JES, JER]);
#                  rateParams/norm_* float = stat + 1% background normalizations. Parsed from the
#                  combined card: BES,ELSCALE,JETSCALE,MUSCALE,SQRTS for the nominal qq card (the former
#                  hard-coded string), plus JES,JER when the qq run dir holds datacard_2d_qq_jesjer.txt
# The combined recoil card correlates BES/SQRTS across mumu+ee (and BES, SQRTS, norm_WW, norm_ZZ,
# norm_rare with the qq card) through the shared nuisance names. The qq card is the paper-spec one
# from 'python3 makeWS_2D_qq.py' (signal = all ZH final states, BES from the inclusive samples); a
# July-definition qq card (bkg_ZH process, no BES; makeWS_2D_qq.py --zh-other-as-bkg writes it to
# run_2D_mrecoil_mjj_qq_zhbkg/, never here) in run_2D_mrecoil_mjj_qq/ is refused. The qq card is
# datacard_2d_qq.txt, or datacard_2d_qq_jesjer.txt when the qq run dir holds that one instead (written
# by makeWS_2D_qq.py --jesjer|--jes-only|--jer-only: JES / JER shape nuisances on every qq process,
# profiled in xsec, frozen in xsecSTATshapes); both present = error.
# Do NOT source the key4hep env inside the container.
set -euo pipefail
ECM=365   # the S240 copy differs only in this line and the header
MODE="${1:-}"
CARDS="${2:-recoil}"
HERE="$(cd "$(dirname "$0")" && pwd)"
[ -d "${FIT_BASE:-$HERE}" ] || { echo "ERROR: FIT_BASE=${FIT_BASE:-$HERE} is not a directory"; exit 1; }
FIT_BASE="$(cd "${FIT_BASE:-$HERE}" && pwd)"
case "$FIT_BASE" in *[[:space:]]*) echo "ERROR: FIT_BASE=$FIT_BASE contains whitespace - combine datacards are whitespace-delimited, the combined card cannot reference such shapes paths"; exit 1 ;; esac
RUNDIR_SUFFIX="${RUNDIR_SUFFIX:-}"
case "$RUNDIR_SUFFIX" in *[[:space:]/]*) echo "ERROR: RUNDIR_SUFFIX=$RUNDIR_SUFFIX must be a plain name fragment (no whitespace or /)"; exit 1 ;; esac
QQ_RUNDIR_SUFFIX="${QQ_RUNDIR_SUFFIX:-}"
case "$QQ_RUNDIR_SUFFIX" in *[[:space:]/]*) echo "ERROR: QQ_RUNDIR_SUFFIX=$QQ_RUNDIR_SUFFIX must be a plain name fragment (no whitespace or /)"; exit 1 ;; esac
QQ_TAGOPT="${QQ_RUNDIR_SUFFIX:+ --tag $QQ_RUNDIR_SUFFIX}"
# output-dir suffix of 'all': <RUNDIR_SUFFIX><QQ_RUNDIR_SUFFIX> (identical suffixes are not doubled),
# or ALL_RUNDIR_SUFFIX verbatim when that variable is set (even empty)
ALL_SFX="$RUNDIR_SUFFIX$([ "$QQ_RUNDIR_SUFFIX" = "$RUNDIR_SUFFIX" ] || printf %s "$QQ_RUNDIR_SUFFIX")"
if [ -n "${ALL_RUNDIR_SUFFIX+set}" ]; then
  case "$ALL_RUNDIR_SUFFIX" in *[[:space:]/]*) echo "ERROR: ALL_RUNDIR_SUFFIX=$ALL_RUNDIR_SUFFIX must be a plain name fragment (no whitespace or /)"; exit 1 ;; esac
  ALL_SFX="$ALL_RUNDIR_SUFFIX"
fi
case "$CARDS" in
  recoil) CH_MUMU="mumu=$FIT_BASE/run_recoil_2cat_mumu$RUNDIR_SUFFIX/datacard_recoil_2cat_mumu.txt"
          CH_EE="ee=$FIT_BASE/run_recoil_2cat_ee$RUNDIR_SUFFIX/datacard_recoil_2cat_ee.txt"
          LL_DIR="run_recoil_2cat_combined$RUNDIR_SUFFIX"; ALL_DIR="run_${ECM}_all$ALL_SFX"
          MAKEWS="python3 makeWS_recoil_2cat.py <flavor>${RUNDIR_SUFFIX:+ --tag $RUNDIR_SUFFIX}" ;;
  bdt)    [ -z "$RUNDIR_SUFFIX" ] || { echo "ERROR: RUNDIR_SUFFIX=$RUNDIR_SUFFIX applies to the recoil (paper-spec) cards only: makeWS_BDT_binned.py has no --tag, so no run_binned_BDTScore_<flavor>$RUNDIR_SUFFIX can exist"; exit 1; }
          CH_MUMU="mumu=$FIT_BASE/run_binned_BDTScore_mumu/datacard_binned_mumu.txt"
          CH_EE="ee=$FIT_BASE/run_binned_BDTScore_ee/datacard_binned_ee.txt"
          LL_DIR="run_binned_BDTScore_combined"; ALL_DIR="run_${ECM}_all_bdt$ALL_SFX"
          MAKEWS="python3 makeWS_BDT_binned.py <flavor>" ;;
  *)      echo "usage: $0 <ll|all> [recoil|bdt]"; exit 1 ;;
esac
# qq channel: the run dir of makeWS_2D_qq.py [--tag QQ_RUNDIR_SUFFIX] holds ONE card - datacard_2d_qq.txt,
# or datacard_2d_qq_jesjer.txt (JES/JER nuisances) when written with --jesjer / --jes-only / --jer-only
QQ_DIR="$FIT_BASE/run_2D_mrecoil_mjj_qq$QQ_RUNDIR_SUFFIX"
QQ_CARD="datacard_2d_qq.txt"; QQ_MAKEWS="python3 makeWS_2D_qq.py$QQ_TAGOPT"
if [ -f "$QQ_DIR/datacard_2d_qq_jesjer.txt" ]; then
  [ -f "$QQ_DIR/datacard_2d_qq.txt" ] && { echo "ERROR: $QQ_DIR holds both datacard_2d_qq.txt and datacard_2d_qq_jesjer.txt - ambiguous; rebuild it with makeWS_2D_qq.py (which leaves one card)"; exit 1; }
  QQ_CARD="datacard_2d_qq_jesjer.txt"; QQ_MAKEWS="python3 makeWS_2D_qq.py --jesjer$QQ_TAGOPT"
fi
CH_QQ="qq=$QQ_DIR/$QQ_CARD"
case "$MODE" in
  ll)  [ -z "$QQ_RUNDIR_SUFFIX" ] || { echo "ERROR: QQ_RUNDIR_SUFFIX=$QQ_RUNDIR_SUFFIX applies to 'all' only (ll uses no qq card)"; exit 1; }
       [ -z "${ALL_RUNDIR_SUFFIX+set}" ] || { echo "ERROR: ALL_RUNDIR_SUFFIX applies to 'all' only (the ll output dir is $LL_DIR)"; exit 1; }
       RUNDIR="$FIT_BASE/$LL_DIR";  CARD="datacard_combined.txt"
       CHANNELS=("$CH_MUMU" "$CH_EE") ;;
  all) RUNDIR="$FIT_BASE/$ALL_DIR"; CARD="datacard_all.txt"
       CHANNELS=("$CH_MUMU" "$CH_EE" "$CH_QQ") ;;
  *)   echo "usage: $0 <ll|all> [recoil|bdt]"; exit 1 ;;
esac
for ch in "${CHANNELS[@]}"; do
  card="${ch#*=}"
  hint="$MAKEWS"; [ "${ch%%=*}" = qq ] && hint="$QQ_MAKEWS"
  [ -f "$card" ] || { echo "ERROR: channel card $card missing - run the makeWS step for '${ch%%=*}' first ($hint, key4hep env)"; exit 1; }
  [ -f "$(dirname "$card")/datacard.root" ] || { echo "ERROR: $(dirname "$card")/datacard.root missing - run the makeWS step for '${ch%%=*}' first ($hint, key4hep env)"; exit 1; }
  if [ "${ch%%=*}" = qq ] && sed 's/#.*//' "$card" | awk '$1=="process"' | grep -qw bkg_ZH; then
    echo "ERROR: $card is the July-2026 qq definition (process bkg_ZH, no BES), not the paper-spec card - rebuild run_2D_mrecoil_mjj_qq$QQ_RUNDIR_SUFFIX/ with '$QQ_MAKEWS' (without --zh-other-as-bkg)"; exit 1
  fi
done

# scan range/points: fit_precision.py and audit_scans.py warn if the 2dNLL=1 crossings fall
# outside the range - widen here (or override with RANGE=r=a,b POINTS=n) and re-run
case "$MODE@$ECM" in
  ll@240)  RANGE="${RANGE:-r=0.98,1.02}";   POINTS="${POINTS:-160}" ;;
  ll@365)  RANGE="${RANGE:-r=0.95,1.05}";   POINTS="${POINTS:-160}" ;;
  all@240) RANGE="${RANGE:-r=0.985,1.015}"; POINTS="${POINTS:-200}" ;;
  all@365) RANGE="${RANGE:-r=0.975,1.025}"; POINTS="${POINTS:-200}" ;;
  *)       echo "ERROR: unsupported MODE=$MODE ECM=$ECM"; exit 1 ;;
esac

mkdir -p "$RUNDIR"
cd "$RUNDIR"
echo "== $MODE @ $ECM GeV ($CARDS cards)  rundir=$RUNDIR  card=$CARD${RUNDIR_SUFFIX:+  suffix=$RUNDIR_SUFFIX}${QQ_RUNDIR_SUFFIX:+  qq-suffix=$QQ_RUNDIR_SUFFIX}$([ "$MODE" = all ] && printf '  qq-card=%s' "$QQ_CARD")${ALL_RUNDIR_SUFFIX+  all-suffix=$ALL_RUNDIR_SUFFIX (explicit)}"
echo "== channels: ${CHANNELS[*]}"
combineCards.py "${CHANNELS[@]}" > "$CARD.tmp"
mv "$CARD.tmp" "$CARD"
strip() { sed 's/#.*//' "$CARD"; }
# every shapes file referenced by the combined card must exist (absolute paths from combineCards.py)
for f in $(strip | awk '$1=="shapes"{print $4}' | sort -u); do
  [ -f "$f" ] || { echo "ERROR: shapes file $f referenced by $RUNDIR/$CARD does not exist"; exit 1; }
done
RATEPARAMS="$(strip | awk '$2=="rateParam"{print $1}' | sort -u | paste -sd,)"
SHAPES="$(strip | awk '$2=="shape"{print $1}' | sort -u | paste -sd,)"
if [ "$CARDS" = bdt ]; then
  [ -n "$RATEPARAMS" ] || { echo "ERROR: no rateParam line found in $RUNDIR/$CARD (the binned-BDT cards have free background rateParams)"; exit 1; }
fi
[ -n "$SHAPES" ]     || { echo "ERROR: no shape nuisance found in $RUNDIR/$CARD"; exit 1; }
FREEZE_STAT="allConstrainedNuisances${RATEPARAMS:+,$RATEPARAMS}"
FREEZE_SHAPES="$SHAPES"
echo "== range=$RANGE points=$POINTS"
echo "== xsecSTAT freeze:       $FREEZE_STAT"
echo "== xsecSTATshapes freeze: $FREEZE_SHAPES"
JESJER="$(strip | awk '$2=="shape" && ($1=="JES" || $1=="JER"){print $1}' | sort -u | paste -sd,)"
[ -z "$JESJER" ] || echo "== JES/JER nuisances in $CARD: $JESJER (floating in xsec, frozen in xsecSTATshapes and xsecSTAT)"

text2workspace.py "$CARD" -o ws.root

COMMON=(-M MultiDimFit -t -1 --setParameterRanges "$RANGE" --points="$POINTS" --algo=grid ws.root
        --expectSignal=1 -m 125 --X-rtd TMCSO_AdaptivePseudoAsimov --X-rtd ADDNLL_CBNLL=0
        --cminDefaultMinimizerStrategy 0)
combine "${COMMON[@]}" -n xsec
combine "${COMMON[@]}" --freezeParameters="$FREEZE_STAT"   -n xsecSTAT
combine "${COMMON[@]}" --freezeParameters="$FREEZE_SHAPES" -n xsecSTATshapes

{
  echo "== $MODE @ $ECM GeV ($CARDS cards): total vs xsecSTAT (paper stat-only: $FREEZE_STAT)"
  python3 "$HERE/fit_precision.py" higgsCombinexsec.MultiDimFit.mH125.root higgsCombinexsecSTAT.MultiDimFit.mH125.root
  echo "== $MODE @ $ECM GeV ($CARDS cards): total vs xsecSTATshapes (July run-book stat-only: $FREEZE_SHAPES)"
  python3 "$HERE/fit_precision.py" higgsCombinexsec.MultiDimFit.mH125.root higgsCombinexsecSTATshapes.MultiDimFit.mH125.root
  echo "== scan audit ($RUNDIR)"
  python3 "$HERE/audit_scans.py" "$RUNDIR"
} 2>&1 | tee fit_summary.txt
