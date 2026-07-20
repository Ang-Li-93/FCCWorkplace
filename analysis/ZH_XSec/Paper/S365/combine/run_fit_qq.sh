#!/bin/bash
# Hadronic (Z->qq) combine fit, ecm 365. Run INSIDE the combine env:
#   cd HiggsAnalysis/CombinedLimit && source env_standalone.sh
# (do NOT mix with the key4hep env).
#
# Usage: ./run_fit_qq.sh [2d|bdt]
#   2d  (default) primary fit per arXiv:2512.21290: unrolled m_recoil x m_jj in two
#       BDT-score categories, per-component backgrounds with 1% normalization
#       nuisances (makeWS_2D_qq.py + datacard_2d_qq.txt)
#   bdt cross-check: full-range binned BDT-score shape (makeWS_BDT_binned.py qq)
#
# Runs text2workspace + Asimov MultiDimFit grid scans (total, and stat-only with the
# scale/sqrts shapes and the background normalization nuisances frozen), then prints
# the 1-sigma precision via fit_precision.py.
set -e
MODE="${1:-2d}"
HERE="$(cd "$(dirname "$0")" && pwd)"
case "$MODE" in
  2d)  RUNDIR="$HERE/run_2D_mrecoil_mjj_qq"
       CARD="datacard_2d_qq.txt"
       FREEZE="JETSCALE,SQRTS,norm_WW,norm_ZZ,norm_Zqq,norm_ZH,norm_rare" ;;
  bdt) RUNDIR="$HERE/run_binned_BDTScore_qq"
       CARD="datacard_binned_qq.txt"
       FREEZE="JETSCALE,SQRTS" ;;
  *)   echo "usage: $0 [2d|bdt]"; exit 1 ;;
esac
[ -f "$RUNDIR/datacard.root" ] || { echo "ERROR: $RUNDIR/datacard.root missing - run the makeWS step first (key4hep env)"; exit 1; }
cd "$RUNDIR"

# scan range: fit_precision.py warns if the 2dNLL=1 crossings fall outside - widen here
RANGE="r=0.97,1.03"
POINTS=60

text2workspace.py "$CARD" -o ws.root

combine -M MultiDimFit -t -1 --setParameterRanges "$RANGE" --points=$POINTS --algo=grid ws.root \
        --expectSignal=1 -m 125 --X-rtd TMCSO_AdaptivePseudoAsimov --X-rtd ADDNLL_CBNLL=0 --cminDefaultMinimizerStrategy 0 -n xsec

combine -M MultiDimFit -t -1 --setParameterRanges "$RANGE" --points=$POINTS --algo=grid ws.root \
        --expectSignal=1 -m 125 --X-rtd TMCSO_AdaptivePseudoAsimov --X-rtd ADDNLL_CBNLL=0 --cminDefaultMinimizerStrategy 0 \
        --freezeParameters="$FREEZE" -n xsecSTAT

python3 "$HERE/fit_precision.py" \
    higgsCombinexsec.MultiDimFit.mH125.root \
    higgsCombinexsecSTAT.MultiDimFit.mH125.root
