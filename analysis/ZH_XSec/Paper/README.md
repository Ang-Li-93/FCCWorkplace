# ZH cross-section analysis (FCC-ee, winter2023 fastsim) — SDCC

Model-independent σ_ZH via the recoil method in Z→μμ/ee/qq̄ at √s = 240 and 365 GeV,
following arXiv:2512.21290. Detailed run book with results, conventions and
gotchas: `FCCWorkplace/documents/ZH_XSEC_RUNS.md`. Everything below is per energy;
replace `S240` by `S365` for the 365 GeV point (WPs, windows, luminosity are set
inside the per-energy scripts).

## Results (2026-09)

Paper-spec reproduction of arXiv:2512.21290 with the **original BDT models** (CERN-trained
leptonic `xgb_bdt.root`, July-2026 local hadronic `bdt_model_ecm*.root`; the six retrained
2026-09-29 models are archived as a cross-check only) and **no tt̄ template at 365 GeV** (as
the paper; `makeWS_2D_qq.py --exclude p8_ee_tt_ecm365`). Numbers, sources and the recipe:
`documents/zh_xsec_table2_2026-09_oldbdt.md` / `.tex` (5-column Table 2 incl. JES/JER,
`table2_full.py`), `documents/zh_xsec_results_2026-09_oldbdt.md` (Table 2 + all Table 3
columns, `collect_results.py`), run book section "Reproduction campaign 2026-09-29/30".
Cut-based fits (paper Table 2 'Cut-based': one recoil region per final state, hadronic
recoil-only — `makeWS_recoil_2cat.py --single-region`, `makeWS_2D_qq.py --recoil-only`) and the
paper-layout comparison of all four Table-2 columns: `documents/zh_xsec_table2_paper_layout_2026-09_oldbdt.md`
/ `.tex` (`table2_paper_layout.py`; paper total ↔ `xsecSTATshapes` = stat + 1% bkg norm, stat-only
↔ `xsecSTAT`; the `xsec` scan with BES / scale / √s profiled is beyond the paper's quoted precision).
Run dirs: `S{ecm}/combine/run_*_oldbdt/` (paper-spec fits, bias tests), `run_*_oldbdt_jesjer/`
(+ `_jes`, `_jer`: hadronic JES/JER nuisances added), `run_*_oldbdt_cutbased/` (cut-based
single-region fits); the same names without suffix are the retrained-model cross-check,
`*.jul2026` the July-2026 results.

## Environments

```bash
# analysis (stage1/stage2/training/makeWS)
source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2024-03-10
source FCCAnalyses-winter2023/setup.sh
# fits (text2workspace/combine): CMS combine-standalone container via the wrapper at the
# repo root (documents/COMBINE.md) — cwd preserved; never source key4hep inside it
./run_combine.sh text2workspace.py datacard.txt          # any combine command
./run_combine.sh ./run_fit_leptonic.sh mumu              # any script that calls combine
./run_combine.sh bash                                    # interactive shell in the image
```

## Full hadronic chain (the complete analysis, ~½ day incl. two condor rounds)

```bash
cd analysis/ZH_XSec/Paper                                # key4hep env
# 1.-3. BDT training: NOT part of the paper reproduction (the July-2026 model in
#    storage/.../models/ is the one behind the quoted numbers; retraining changes the
#    categorization). Only when a new model is wanted on purpose:
python3 condor/submit_stage1.py S240/qq/stage1_training_ntuples.py --stage MVA_ntuples
# 2. (optional) BDT-input validation
fccanalysis final analysis/ZH_XSec/Paper/S240/qq/stage2_mva_inputs.py
fccanalysis plots analysis/ZH_XSec/Paper/S240/qq/stage3_mva_inputs_plots.py
# 3. training set (50/50 split) -> train -> evaluation plots
cd S240/qq
python3 process_sig_bkg_samples_for_xgb.py && python3 train_xgb.py && python3 evaluation.py
cd ../..
# 4. analysis ntuples (BDT from storage/.../models/; condor fan-out, 1105 jobs @240 / 1517 @365
#    incl. the 24 inclusive/BES sets), then validate + repair the tree-less zero-selection chunks
python3 condor/submit_stage1.py S240/qq/stage1_analysis_ntuples.py
python3 condor/check_chunks.py --ecm 240 --flavor qq --jobs 8      # then, per NO_TREE process:
python3 condor/patch_empty_chunks.py --ecm 240 --flavor qq --only <process> --apply   # and re-check
# 5. stage2 histograms (all selections + systematics, 2D fit observables)
fccanalysis final analysis/ZH_XSec/Paper/S240/qq/stage2_histograms_syst.py
# 6. fit templates: primary 2D m_recoil x m_jj in two BDT categories, paper spec: signal =
#    all ZH final states, bkg_WW/ZZ/Zqq/rare with 1% lnN, shapes JETSCALE / SQRTS / BES (BES
#    shape-only from the inclusive samples; --bes-keep-norm = raw). --zh-other-as-bkg = the
#    July definition (cross-check); --input-base DIR / --out-base DIR for tests on *.jul2026;
#    --tag SFX = run dir suffix (the 2026-09 results: _oldbdt); at 365 add --exclude p8_ee_tt_ecm365
#    (no tt template, as the paper: the Pythia8 tt sample would inflate the 365 result to 0.757%)
cd S240/combine && python3 makeWS_2D_qq.py && python3 makeWS_BDT_binned.py qq
```

```bash
cd analysis/ZH_XSec/Paper/S240/combine                   # combine container: RC=<repo>/run_combine.sh
$RC ./run_fit_qq.sh                    # primary 2D fit: scans xsec / xsecSTAT / xsecSTATshapes + precision + audit
$RC ./run_fit_qq.sh 2d-zhbkg           # July-definition cross-check (after makeWS_2D_qq.py --zh-other-as-bkg)
$RC ./run_fit_qq.sh bdt                # 1D BDT-score cross-check;  FIT_BASE=<dir> RANGE=r=a,b POINTS=n override
$RC python3 bias_test_generic.py qq    # model-independence bias test (paper 7.2, 1% injection); qq-zhbkg = July
# suffixed run dirs (makeWS --tag SFX): QQ_RUNDIR_SUFFIX=SFX $RC ./run_fit_qq.sh 2d ; $RC python3 bias_test_generic.py qq --tag SFX
```

## Leptonic channels

Stage1/stage2 identical pattern with `S240/mumu` / `S240/ee`
(`stage1_analysis_ntuples.py`, `stage2_histograms_syst.py`; the process list carries the 87
exclusive ZH sets since 2026-09-29: 494 / 507 / 488 / 481 jobs, check/patch the chunks as for
qq). BDT models: every quoted result (July 2026 and the 2026-09 reproduction) uses the
ORIGINAL CERN-trained ones in `storage/.../models/` (= `models_backup_2026-09-29/`, md5 in
its `MD5SUMS.txt`); the set retrained on SDCC on 2026-09-29 is archived in
`models_retrained_2026-09-29/` as a cross-check only — do not retrain for the paper numbers.
Retraining, when wanted on purpose: treemaker with `--stage MVAInputs`, then the same trio
as qq (config from `leptonic_training_config.make(ecm, flavor)`; env notes in the run book,
Tooling). Variant fits: `makeWS_recoil_2cat.py <fl> --tag SFX` + `RUNDIR_SUFFIX=SFX` on the
drivers + `bias_test_generic.py <ch> --tag SFX` (the 2026-09 results: `_oldbdt`).
Paper-spec datacards (recoil mass in two BDT regions, per-component 1% lnN backgrounds,
signal = all ZH final states): `python3 makeWS_recoil_2cat.py mumu|ee`; the binned
BDT-score cards `python3 makeWS_BDT_binned.py mumu|ee` are the cross-check. Fits:
`$RC ./run_fit_leptonic.sh mumu|ee [recoil|bdt]`, `$RC ./run_fit_combination.sh ll|all [recoil|bdt]`
(`recoil` = paper-spec cards, default; `bdt` = the BDT-score cross-check cards, run dirs
`run_binned_BDTScore_*` / `run_<ecm>_all_bdt`; three scans: `xsec` (everything profiled,
beyond the paper's quoted precision) / `xsecSTAT` (paper stat-only) / `xsecSTATshapes` (stat + 1% bkg
= the paper's quoted total; 'stat-only' in the July run book)).
`makeWS_recoil_2cat.py` options: `--rebin N` (recoil-mass bins, default 1 = 0.5 GeV),
`--input-base <stage2 syst dir>` / `--out-base <dir>` (tests on the July `*.jul2026`
histograms into a scratch dir, then `FIT_BASE=<out-base>` for the drivers and
`bias_test_generic.py`), `FCC_ALLOW_MISSING=1` (missing inputs -> warning; a variation
with no input at all becomes a nominal copy). `signal_by_decay.root` (per-H-decay
templates, bias test only) is written only when the exclusive ZH samples went through
stage1/stage2; without them the file is skipped and the bias test refuses to run
(`--synthetic-by-decay` = BR-split of the fit template, a mechanics check only; its fits go
to `bias_synthetic_<H>/` with a `channel=<ch>-synthetic` log header, which `collect_results.py` ignores).
Bias test: `$RC python3 bias_test_generic.py mumu|ee|ll|qq|qq-zhbkg|all [--x X] [--decays Hbb,...] [--br sample|table]`
(paper 7.2; X = 5% for mumu/ee/ll, 1% for qq/all; ll/all need the combined card from
`run_fit_combination.sh` first; `bias_test_qq.py` is a deprecated shim for `qq-zhbkg`).
BR convention of the injection X/BR_h: `--br sample` (default) takes BR_h from the winter2023
exclusive-sample cross sections (`FCCee_procDict_winter2023_IDEA.json`, `$FCCDICTSDIR` then
cvmfs; summed over the 8 Z decays, nunuH_Hinv kept in the sums) — the fractions the per-decay
templates actually carry; `--br table` is the SM table of the July-2026 logs, up to 4% off
(Hss 0.00025 vs 0.000239), which shows up as an apparent −0.24% Hss bias at X = 5% (paper
Table 3: −0.01). The log header prints both sets and their ratio per decay.

## Combination, baseline, robustness

```bash
# 3-channel combination (combine container): $RC ./run_fit_combination.sh all
# (combineCards mumu+ee+qq(2D), three scans; results in run_240_all/; 'll' for mumu+ee).
# Optional JES / JER nuisances of the hadronic fit (paper Sec 5.3 evaluated a 1% jet energy scale
# shift and an additional 1% jet energy smearing without including them in the quoted precision):
# STAGE=/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper/S240/qq/BDT_analysis_samples_oldbdt : the templates' default stage dir;
# makeWS_2D_qq.py defaults to BDT_analysis_samples/syst instead, so name the same dir on both commands
python3 ../qq/stage2_jesjer_templates.py --input-dir $STAGE --ncpu 8 --check    # key4hep env: jesup/jesdw/jerup files into $STAGE/syst/
python3 makeWS_2D_qq.py --jesjer --input-base $STAGE/syst --tag _oldbdt_jesjer  # (or --jes-only --tag _oldbdt_jes / --jer-only --tag _oldbdt_jer;
#   at 365 add --exclude p8_ee_tt_ecm365) -> run_2D_mrecoil_mjj_qq_oldbdt_jesjer/
# QQ_RUNDIR_SUFFIX=_oldbdt_jesjer $RC ./run_fit_qq.sh 2d ; RUNDIR_SUFFIX=_oldbdt QQ_RUNDIR_SUFFIX=_oldbdt_jesjer ALL_RUNDIR_SUFFIX=_oldbdt_jesjer $RC ./run_fit_combination.sh all
# (JES/JER float in xsec, are frozen with the other shape nuisances in xsecSTATshapes = stat + 1% bkg; run book: Systematics)
# Referee baseline (no BDT anywhere, 1D recoil fit, sideband-constrained bkg):
python3 makeWS_noBDT_baseline.py qq   # + mumu / ee    (key4hep env)
# fits as run_fit_qq.sh does, dirs run_noBDT_recoil_*/ and run_240_noBDT_all/
# Robustness / QA tools:
python3 jes_morph_test.py             # jet-energy-scale morphing (1e-4, 1e-3)
python3 audit_scans.py <dirs>         # scan reliability: parabola touches 0, etc.
python3 ../../collect_results.py [--suffix .jul2026]  # markdown table of all scans vs paper Table 2 + bias tests vs Table 3 (python3+ROOT, either env)
```

## Outputs

- GPFS data: `/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper/S{ecm}/{flavor}/`
  (ntuples, `syst/` histograms, `training/`, condor logs) and `models/` (originals, live;
  `models_backup_2026-09-29/` = the same files with md5 sums, `models_retrained_2026-09-29/`
  = the archived retrained set). Stage-dir variants of the 2026-09 reproduction:
  `{mumu,ee}/BDT_analysis_samples_cernbdt` (exclusive ZH sets scored with the original
  models + symlinks to the July chunks), `qq/BDT_analysis_samples_oldbdt` (inclusive/BES
  sets with the original model + symlinks; `syst/` also holds the JES/JER templates);
  `*.jul2026` = the July-2026 production (read-only); campaign logs and driver scripts in
  `storage/ZH_XSec_Paper/{oldbdt_logs,jesjer_logs,scripts_oldbdt,scripts_cernbdt}/`.
- Fit workspaces/scans: `S{ecm}/combine/run_*/` (`fit_summary.txt`, three scans, `bias_H*/`).
- Paper figures (exact-style reproductions + originals): `paper_plots/` (git-ignored).
- LaTeX for the referee-baseline addition: `paper_edits/`.

## Key conventions (details in the run book)

- All angular quantities θ-based; hadronic veto orthogonal to ee/μμ (energy-dependent
  p_ll window); W-pair rejection at m_W = 80.4; nunuH_Hinv (and, at 365, the fully
  dileptonic backgrounds) have zero hadronic acceptance by construction.
- Datacards: qq = per-component backgrounds with 1% lnN, signal = all ZH final states,
  BES shape-only (`datacard_2d_qq.txt`; `datacard_2d_qq_zhbkg.txt` = July definition);
  leptonic paper-spec (`makeWS_recoil_2cat.py`) = per-component 1% lnN as well, signal =
  all ZH final states; the binned BDT-score cross-check keeps the lumped background
  with a free rateParam.
- Condor: `request_memory = 4000` required by the qq graph; the submitter guards
  stage/outputDir consistency, follows the script's prodTag, and refuses qq analysis
  submissions without a trained model.
  After a fan-out, validate the chunks before stage2:
  `python3 condor/check_chunks.py --ecm 240 --flavor qq [--stage MVA_ntuples] [--write-resubmit]`
  (opens every chunk once, cross-checks eventsProcessed against the job .err log, flags
  key-less/zero-byte/missing chunks, exit 0 iff clean; `--json` for the full report,
  `--condor-dir/--out-dir` to check a reference snapshot, `--resubmit-dir` to keep the
  resubmit files out of it).
