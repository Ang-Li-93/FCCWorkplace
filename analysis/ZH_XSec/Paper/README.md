# ZH cross-section analysis (FCC-ee, winter2023 fastsim) — SDCC

Model-independent σ_ZH via the recoil method in Z→μμ/ee/qq̄ at √s = 240 and 365 GeV,
following arXiv:2512.21290. Detailed run book with results, conventions and
gotchas: `FCCWorkplace/documents/ZH_XSEC_RUNS.md`. Everything below is per energy;
replace `S240` by `S365` for the 365 GeV point (WPs, windows, luminosity are set
inside the per-energy scripts).

## Environments

```bash
# analysis (stage1/stage2/training/makeWS)
source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2024-03-10
source FCCAnalyses-winter2023/setup.sh
# fits (text2workspace/combine) — never mix with the key4hep env
cd HiggsAnalysis/CombinedLimit && source env_standalone.sh
```

## Full hadronic chain (the complete analysis, ~½ day incl. two condor rounds)

```bash
cd analysis/ZH_XSec/Paper                                # key4hep env
# 1. training trees (winter2023_training campaign; condor fan-out)
python3 condor/submit_stage1.py S240/qq/stage1_training_ntuples.py --stage MVA_ntuples
# 2. (optional) BDT-input validation
fccanalysis final analysis/ZH_XSec/Paper/S240/qq/stage2_mva_inputs.py
fccanalysis plots analysis/ZH_XSec/Paper/S240/qq/stage3_mva_inputs_plots.py
# 3. training set (50/50 split) -> train -> evaluation plots
cd S240/qq
python3 process_sig_bkg_samples_for_xgb.py && python3 train_xgb.py && python3 evaluation.py
cd ../..
# 4. analysis ntuples (needs the model from step 3; condor fan-out, ~865 jobs @240)
python3 condor/submit_stage1.py S240/qq/stage1_analysis_ntuples.py
# 5. stage2 histograms (all selections + systematics, 2D fit observables)
fccanalysis final analysis/ZH_XSec/Paper/S240/qq/stage2_histograms_syst.py
# 6. fit templates: primary 2D m_recoil x m_jj in two BDT categories (paper spec)
cd S240/combine && python3 makeWS_2D_qq.py && python3 makeWS_BDT_binned.py qq
```

```bash
cd analysis/ZH_XSec/Paper/S240/combine                   # combine env
./run_fit_qq.sh          # primary 2D fit (total + stat-only + precision printout)
./run_fit_qq.sh bdt      # 1D BDT-score cross-check
python3 bias_test_qq.py  # model-independence bias test (paper 7.2, 1% injection)
```

## Leptonic channels

Stage1/stage2 identical pattern with `S240/mumu` / `S240/ee`
(`stage1_analysis_ntuples.py`, `stage2_histograms_syst.py`); the BDT models are the
original CERN-trained ones staged under `storage/.../models/` (verified byte-identical
to the /eos originals). To retrain on SDCC: treemaker with `--stage MVAInputs`, then
the same trio as qq (config from `leptonic_training_config.make(ecm, flavor)`).
Datacards: `python3 makeWS_BDT_binned.py mumu|ee`; fits as in the run book.

## Combination, baseline, robustness

```bash
# 3-channel combination (combine env): see run book step "combination" -
# combineCards mumu+ee+qq, then MultiDimFit; results in run_240_all/.
# Referee baseline (no BDT anywhere, 1D recoil fit, sideband-constrained bkg):
python3 makeWS_noBDT_baseline.py qq   # + mumu / ee    (key4hep env)
# fits as run_fit_qq.sh does, dirs run_noBDT_recoil_*/ and run_240_noBDT_all/
# Robustness / QA tools:
python3 jes_morph_test.py             # jet-energy-scale morphing (1e-4, 1e-3)
python3 audit_scans.py <dirs>         # scan reliability: parabola touches 0, etc.
```

## Outputs

- GPFS data: `/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper/S{ecm}/{flavor}/`
  (ntuples, `syst/` histograms, `training/`, condor logs) and `models/`.
- Fit workspaces/scans: `S{ecm}/combine/run_*/`.
- Paper figures (exact-style reproductions + originals): `paper_plots/` (git-ignored).
- LaTeX for the referee-baseline addition: `paper_edits/`.

## Key conventions (details in the run book)

- All angular quantities θ-based; hadronic veto orthogonal to ee/μμ (energy-dependent
  p_ll window); W-pair rejection at m_W = 80.4; nunuH_Hinv (and, at 365, the fully
  dileptonic backgrounds) have zero hadronic acceptance by construction.
- Datacards: qq = per-component backgrounds with 1% lnN (`datacard_2d_qq.txt`);
  leptonic = lumped background with free rateParam.
- Condor: `request_memory = 4000` required by the qq graph; the submitter guards
  stage/outputDir consistency, follows the script's prodTag, and refuses qq analysis
  submissions without a trained model.
