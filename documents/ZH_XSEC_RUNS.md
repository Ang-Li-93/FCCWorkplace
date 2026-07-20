# ZH cross-section analysis — SDCC runs

FCC-ee ZH cross-section measurement (recoil method) on the winter2023 fastsim samples,
ported from CERN lxplus to SDCC/BNL. Leptonic channels (Z→ee, Z→μμ) at √s = 240 and
365 GeV are complete end-to-end; the hadronic channel (Z→qq) is fully set up with a
local BDT training (the reference pre-trained MIT model is unreachable, so the BDT is
retrained here — see the hadronic section).

## Layout and stage naming

Stage scripts share one naming scheme in every channel directory
(`S{240,365}/{ee,mumu,qq}/`); the old `analysis_stage1_*` names live on in git history
(renamed 2026-07, along with the removal of two stale pre-port duplicates).
`Paper/` is the only active tree under `analysis/ZH_XSec/` — the pre-Paper lxplus
trees (FinalReport, FinalReport2_bkup, MidTerm, TopHiggs, FCCAnalyzer) were retired
in the 2026-07 cleanup (git history; the FinalReport paper-reproduction scripts are
kept at `FCCWorkplace/archive/ZH_XSec_FinalReport_Reproduce/`):

```
Paper/
├── site_config.py            # site detection (sdcc/lxplus): BDT-model paths, output dirs
├── zqq_stage1_common.py      # shared selection graph for the hadronic (qq) channel
├── leptonic_training_config.py  # make(ecm, flavor): single source for the leptonic BDT-training config (site-aware)
├── training_utils.py         # helpers for the leptonic training trio (get_df, ROC, significance scan)
├── plotter.py                # ROOT plotting helpers used by the combine scripts (ex FCCAnalyzer)
├── reference_fccanalyzer/    # jeyserma/FCCAnalyzer reference copies (histmakers, C++ headers, datasets)
├── condor/submit_stage1.py   # SDCC HTCondor fan-out for any stage1 script
├── S240/ S365/               # per-energy: mumu/ ee/ qq/ combine/
│   ├── <flavor>/stage1_training_ntuples.py     # stage1 treemaker for BDT training  (was analysis_stage1_MVA_Ntuples_batch)
│   ├── <flavor>/process_sig_bkg_samples_for_xgb.py + train_xgb.py + evaluation.py   # BDT training
│   ├── <flavor>/stage1_analysis_ntuples.py     # stage1 ntuples + BDT + syst        (was analysis_stage1_include_bdt_batch_analysis_samples)
│   ├── <flavor>/stage2_histograms[_syst].py    # stage2 histograms                  (was analysis_stage1_trained_final_analysis_samples[_syst])
│   ├── <flavor>/stage2_mva_inputs.py           # BDT-input check histograms          (was analysis_stage1_MVA_Inputs_final)
│   ├── <flavor>/stage3_plots.py, stage3_mva_inputs_plots.py                          # plotting
│   ├── <flavor>/stage1_training_estimate.py    # training-yield estimate treemaker  (was analysis_stage1_estimate_training_*)
│   ├── training_estimate.py                    # training-yield estimate reader (per-channel via make())
│   └── combine/makeWS_BDT_binned.py, makeWS_2D_qq.py, datacard_binned_{ee,mumu,qq}.txt,
│       combine/run_fit_qq.sh, fit_precision.py, fitAnalysis.py
├── functions_hadronic/       # reference copies of the jeyserma/FCCPhysics hadronic C++
└── models/convert_bdt.py     # RBDT format conversion utility
```

The qq channel has the stage1 pair, `stage2_mva_inputs.py` + `stage3_mva_inputs_plots.py`
(over the winter2023_training treemaker output) and `stage2_histograms_syst.py` (its
nominal histograms are included there). The leptonic training trio + `training_estimate.py`
are **self-contained and site-aware** (2026-07 consolidation): configuration from
`leptonic_training_config.make(ecm, flavor)` (SDCC → `storage/.../S{ecm}/{flavor}/`
with training trees in `MVAInputs/`, working data in `training/`, model to
`models/S{ecm}/{flavor}/xgb_bdt.root`; lxplus → the original `/eos` locations), and
helpers from `training_utils.py` (reimplementation of the never-committed lxplus
`utils.py`). The six per-directory `userConfig.py` copies, the dead CERN
`userBatch.Config` files, and the dead `import plotting` lines were removed.
To retrain a leptonic BDT on SDCC:
`python condor/submit_stage1.py S240/mumu/stage1_training_ntuples.py --stage MVAInputs`
(reads winter2023_training via the script's prodTag), then the trio as for qq.

Storage (GPFS): `/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper/`
(`models/S{ecm}/{flavor}/` BDTs, `S{ecm}/{flavor}/BDT_analysis_samples/` ntuples + `syst/` histograms,
`S{ecm}/qq/MVA_ntuples/` + `S{ecm}/qq/training/` training set + plots,
`S{ecm}/{flavor}/condor/` job wrappers/logs).

## Environments

| Step | Environment |
|---|---|
| stage1, stage2, makeWS, BDT training | `source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2024-03-10` then `source FCCAnalyses-winter2023/setup.sh` (xgboost 1.6.2) |
| text2workspace / combine | `cd HiggsAnalysis/CombinedLimit && source env_standalone.sh` (CMS cvmfs toolchain, ROOT 6.30 — do **not** mix with key4hep) |

Custom C++ (leptonic `HiggsTools::*` incl. `coneIsolationTheta`, and all hadronic helpers)
is compiled into `FCCAnalyses-winter2023` (`analyzers/dataframe/{FCCAnalyses/HiggsTools.h,src/HiggsTools.cc}`).
Rebuild after edits: `cd FCCAnalyses-winter2023/build && cmake --build . --target install -j8`.

## Run book (leptonic, per channel)

1. **Stage1** (ntuples with BDTscore + systematics branches), fans out to condor
   (`accounting_group=group_usfcc`, xrootd input from eospublic, GPFS output):
   ```
   python condor/submit_stage1.py S240/mumu/stage1_analysis_ntuples.py [--dry-run]
   ```
   Job counts: S240/mumu 321, S240/ee 334, S365/mumu 314, S365/ee 307 (~10 min wall on a hot queue).
   The wrapper exports `FCCANA_PROCESS=<process>` (used by the qq channel's MC-truth filters).

2. **Stage2** (BDT-score histograms for all selections incl. syst variations):
   ```
   fccanalysis final analysis/ZH_XSec/Paper/S240/mumu/stage2_histograms_syst.py
   ```
   Output: `.../S{ecm}/{flavor}/BDT_analysis_samples/syst/<proc>_<sel>_histo.root`.

3. **Datacard** (signal/background/syst templates + control plots + `datacard.root`):
   ```
   cd S240/combine && python3 makeWS_BDT_binned.py mumu     # or ee
   ```

4. **Workspace + fit** (combine env):
   ```
   cd S240/combine/run_binned_BDTScore_mumu
   text2workspace.py datacard_binned_mumu.txt -o ws.root
   combine -M MultiDimFit -t -1 --setParameterRanges r=0.98,1.02 --points=50 --algo=grid ws.root \
           --expectSignal=1 -m 125 --X-rtd TMCSO_AdaptivePseudoAsimov --X-rtd ADDNLL_CBNLL=0 -n xsec
   # stat-only: add --freezeParameters=MUSCALE,BES,SQRTS (ELSCALE for ee) with -n xsecSTAT
   ```
   At 365 use `r=0.94,1.06 --points=60`. Channel combination:
   `combineCards.py mumu=.../datacard_binned_mumu.txt ee=.../datacard_binned_ee.txt`
   (make the shape paths absolute in the combined card before text2workspace).
   The 1σ precision is read off the ΔNLL scan (2ΔNLL = 1 crossings) in
   `higgsCombinexsec.MultiDimFit.mH125.root`.

## Results (Asimov, expected precision on σ_ZH)

| Channel | Total | Stat-only | Syst |
|---|---|---|---|
| S240 μμ | 0.668% | 0.662% | 0.086% |
| S240 ee | 0.786% | 0.782% | 0.080% |
| S240 qq (2D, 2 BDT cats; paper 0.38%) | 0.457% | 0.358% | 0.284% |
| **S240 ee+μμ** (paper 0.52%) | **0.511%** | 0.505% | 0.079% |
| **S240 ee+μμ+qq** (paper 0.31%) | **0.341%** | 0.292% | 0.176% |
| S365 μμ | 1.938% | 1.904% | 0.360% |
| S365 ee | 2.190% | 2.115% | 0.566% |
| S365 qq (2D, 2 BDT cats; paper 0.56%) | 0.751% | 0.621% | 0.423% |
| **S365 ee+μμ** | **1.468%** | 1.412% | 0.402% |
| **S365 ee+μμ+qq** (paper 0.52%) | **0.669%** | 0.570% | 0.350% |

Integrated luminosities: 10.8 ab⁻¹ (240), 3.12 ab⁻¹ (365, arXiv:2512.21290; earlier leptonic 365 fits used 3.0 ab⁻¹ and predate the update).
S240 qq run 2026-07-19 (paper spec, arXiv:2512.21290): local BDT (winter2023_training,
16.4M events, 50/50 split), 865-job stage1 (244.9M selected, m_W = 80.4 in the WW veto),
two BDT categories (WP 0.75), per-component background normalizations (1% lnN).
The syst column is dominated by those five norm nuisances. 1D full-range BDT-score
cross-check: 0.356%. Paper agreement: qq stat 0.358% vs 0.38%; combined 0.341% vs
0.31% (200-point fine scan; the initial coarse 18-point scan gave 0.337% but its
parabola did not reach 2ΔNLL = 0 — scan-reliability audit in `audit_scans.py`) —
consistent given the locally retrained BDT and binning choices.
Bias test (§7.2, 1% injection, `bias_test_qq.py`): dominant modes |bias| < 0.09%
(Hbb +0.04%, HWW −0.09%, Hgg −0.03%, Hcc −0.05%, HZZ −0.06%, Hττ −0.02%); rare modes
Hss −0.15%, HZa −0.16%, Hμμ +0.40%, Hγγ +0.61%, Hinv +0.67% — same pattern and
conclusion as the paper (dominant modes unbiased; small-BR modes within ~1σ of the
0.46% total uncertainty). Model independence confirmed at the achieved precision.

## Referee baseline: no BDT, recoil-only fits (S240)

LEP-style scenario (`makeWS_noBDT_baseline.py` + `datacard_recoil_qq.txt`,
run dirs `run_noBDT_recoil_{mumu,ee,qq}/`, `run_240_noBDT_all/`): cut-based baseline
selection only, 1D recoil-mass fit in 100–150 GeV, background normalizations floating
(leptonic: free rateParam; qq: five 1% lnN components) and constrained by the recoil
sidebands — the in-situ analogue of a data-driven sideband method in an MC projection.
Leptonic wide-window selections: `sel_Baseline_wide*` in the leptonic stage2 configs.

| Channel | no-BDT total | no-BDT stat | paper-spec (BDT) | BDT gain |
|---|---|---|---|---|
| μμ | 0.881% | 0.863% | 0.668% | ×1.3 |
| ee | 1.154% | 1.138% | 0.786% | ×1.5 |
| qq | 1.445% | 0.814% | 0.457% | ×3.2 |
| **ee+μμ+qq** | **0.635%** | 0.527% | 0.341% | ×1.9 |

The qq no-BDT systematic (1.19%) is dominated by the background-normalization
nuisances: with only the recoil shape, the five components are nearly degenerate.

S365 (same scenario): μμ 4.592% (4.399% stat), ee 5.203% (4.965% stat),
qq 1.401% (0.743% stat), **combination 1.308%** (0.741% stat) vs paper-spec 0.669%
— the BDT is worth ×2.4 per leptonic channel and ×2.0 combined at 365 (recoil peak
broadened by ISR + 10× BES), vs ×1.3–1.5/×1.9 at 240.
S365 production note: at 365 the isolated-lepton removal window (20–170 GeV) gives the
purely-dileptonic backgrounds (γγ→ℓℓ, eγ→Zℓℓ, ee→ℓℓ) zero hadronic acceptance; their
empty stage1 chunks are patched with empty trees + correct eventsProcessed (normalization
preserved). S365 qq run: 1279 jobs, 59.1M selected events, zero evictions.
S365 bias test (1% injection): all modes within ±0.34% (largest H→ττ), well inside the
0.75% uncertainty — model independence confirmed at 365.
All scans audited (parabola touches 0, minimum at r = 1).

## Systematics

| Nuisance | Source | Implementation |
|---|---|---|
| MUSCALE / ELSCALE | lepton momentum scale | ±1e-5 via `lepton_momentum_scale(±1e-5)`, Z/recoil/BDT recomputed (**down variation is −1e-5**; a legacy bug where both used +1e-5 was fixed 2026-07-04 and stage1 fully re-run) |
| JETSCALE (qq) | jet momentum scale | ±1e-5 on the Z(qq) jets, Z/recoil recomputed; BDT score **not** recomputed (enters via selection migration). NB 1e-5 is a placeholder inherited from the muon treatment (no report motivates 1e-5 for jets); the morphed-JES robustness test (`jes_morph_test.py`, linear morphing of the stored templates to 1e-4 and 1e-3) shows the fitted precision is **unchanged (0.457%) even at JES = 1e-3** — the m_jj Z peak in the fit observable self-calibrates the scale, so JETSCALE is a non-systematic for this measurement at any plausible magnitude |
| SQRTS | √s knowledge | recoil rebuilt at √s ± 2 MeV |
| BES | beam energy spread | dedicated samples, ±1% (240); ±10pc variants used at 365; **not available for hadronic Z decays** |
| bkg components (qq) | per-component normalization | 1% lnN each on WW / ZZ / Z⁠γ* / ZH-other / rare (arXiv:2512.21290) |
| bkg norm | background yield | free rateParam in the fit |

Conventions: all angular quantities are θ-based (isolation = `coneIsolationTheta(0.01, 0.5)` +
`sel_isol(0.25)`; acolinearity = |θ₁−θ₂|; no η anywhere in selections or BDT inputs).
The mH-shifted samples (±50/100 MeV) are for the mass measurement, not the xsec fit.

## Hadronic (Z→qq) channel

Ported from jeyserma/FCCPhysics `h_zh_hadronic.py` into this workflow
(shared graph `zqq_stage1_common.py`; helpers compiled into HiggsTools, including the
3-D `acolinearity_scalar`; θ-based lepton veto for orthogonality with ee/μμ).
Sample mapping: `wzp6_ee_qq` replaces the missing `wz3p6_ee_{uu,dd,ss,cc,bb}`;
signals are the 8 Z-decay × 11 H-decay wzp6 sets; `p8_ee_tt` added at 365.
Two veto details differ from the reference: the resonance builder is guarded
(the C++ helper `exit(1)`s on events with <2 leptons — i.e. most hadronic events —
and returns an empty vector without an opposite-charge pair), and the veto's p_ll
window is energy-dependent (20–70 GeV at 240; >20 GeV with no upper bound at 365,
where ZH kinematics put p_ll ≈ 146 GeV — the reference 240-era window would never
veto genuine Z(ℓℓ)H there and orthogonality with ee/μμ would be lost).

The BDT is **trained locally** (the reference pre-trained model at MIT `/ceph` is not
reachable). The upstream `W2_costheta` bug — both `W1_costheta` and `W2_costheta` were
`abs(W1.Theta())`, i.e. θ of W₁ twice — is **fixed** in `zqq_stage1_common.py`
(now `|cos θ|` of W₁ and W₂ respectively), so the local model is *not*
weight-compatible with the reference `bdt_model_ecm{240,365}.root`. An earlier
`train_xgb.py` also dropped the per-process event weights from the fit
(`sample_weight` was only passed to the eval sets); fixed with the training split.

Run book (per energy, here 240):

1. **Training trees**: `python condor/submit_stage1.py S240/qq/stage1_training_ntuples.py --stage MVA_ntuples`
   — reads the **dedicated `winter2023_training` campaign** (statistically
   independent of the analysis samples; the submitter follows the script's
   `prodTag`). At 240, `bbH_Hcc` and `bbH_Hmumu` were not produced in that
   campaign and are excluded (both exist at 365).
2. **MVA-input check** (optional but recommended):
   `fccanalysis final analysis/ZH_XSec/Paper/S240/qq/stage2_mva_inputs.py` then
   `fccanalysis plots analysis/ZH_XSec/Paper/S240/qq/stage3_mva_inputs_plots.py`
   (input-variable histograms + stacked plots → `MVAInputs_final/`, `MVAInputs_plots/`).
3. **Training set**: `cd S240/qq && python process_sig_bkg_samples_for_xgb.py`
   (→ `S240/qq/training/preprocessed.pkl`; cross-sections from the
   winter2023_training procDict; reference weighting: signal 0.2·L/N per H decay
   at 240, 0.15 at 365; background σ·L/N)
4. **Train**: `python train_xgb.py` (reference hyperparameters; TMVA-format model +
   variables TList → `models/S240/qq/bdt_model_ecm240.root`, + `.pkl` for evaluation)
5. **Evaluate**: `python evaluation.py` (ROC/overtraining/importance/efficiency →
   `training/plots/`)
6. **Stage1**: `python condor/submit_stage1.py S240/qq/stage1_analysis_ntuples.py`
   (needs `FCCANA_PROCESS`, exported by the wrapper, for the HZZ→inv / WW→leptonic
   MC-truth filters; jet-scale ±1e-5 and √s ± 2 MeV syst branches)
7. **Stage2**: `fccanalysis final analysis/ZH_XSec/Paper/S240/qq/stage2_histograms_syst.py`
8. **Fit templates**: `cd S240/combine && python3 makeWS_2D_qq.py`
   — the **primary hadronic fit is 2D in m_recoil × m_jj** (as in the FCCPhysics
   reference), inside the stage2 baseline windows after the `mva_score > MVA_CUT`
   working point (constant in `stage2_histograms_syst.py`, default 0.5 — tune with
   the evaluation.py significance scan). The TH2 templates (240: 25×24 bins over
   [100,150]×[20,140]; 365: 20×18 over [100,180]×[20,200]) are summed over processes
   and unrolled to TH1 for combine, into `run_2D_mrecoil_mjj_qq/`
   (`datacard.root` + `templates_2d.root` for inspection).
   Signal = Z(qq/ss/cc/bb)H summed over all H decays; ZH with leptonic/invisible Z
   counts as background — orthogonal to ee/μμ via the stage1 lepton veto;
   systs JETSCALE + SQRTS + free `bkg_qq_norm` rateParam. A missing stage2 file for
   any process **aborts** template building (a gap means the production is incomplete
   and would bias the templates); `FCC_ALLOW_MISSING=1` downgrades that to a warning.
   Cross-check: `python3 makeWS_BDT_binned.py qq` builds the 1D binned BDT-score
   datacard (leptonic-style) in `run_binned_BDTScore_qq/`.
9. **Fit** (combine env): `./run_fit_qq.sh` (primary 2D fit; `./run_fit_qq.sh bdt`
   for the BDT-score cross-check) — text2workspace + Asimov MultiDimFit grid scans
   (total, and stat-only with `--freezeParameters=JETSCALE,SQRTS`; `bkg_qq_norm`
   floats in both) followed by the precision printout from `fit_precision.py`
   (python3, generic — also works on the leptonic scan files, unlike the
   python2-era `fitAnalysis.py`). Scan range `r=0.95,1.05` at 240 /
   `0.85,1.15` at 365, set in the script; it warns if the 2ΔNLL = 1 crossings
   fall outside — widen and re-run.

9. **Bias test** (combine env, arXiv:2512.21290 §7.2): `python3 bias_test_qq.py`
   — perturbs each H-decay BR so the total σ_ZH shifts by 1%, refits each
   pseudo-dataset with the nominal templates, prints the per-mode bias table and
   the per-decay yield/efficiency spread.

   Adding qq to the channel combination:
   `combineCards.py mumu=.../datacard_binned_mumu.txt ee=.../datacard_binned_ee.txt qq=.../run_2D_mrecoil_mjj_qq/datacard_binned_qq.txt`
   (shape paths absolute, as for ee+μμ; the background rateParams stay per-channel:
   `background_norm` (μμ), `bkg_ee_norm`, `bkg_qq_norm`; stat-only freeze for the
   combination: `MUSCALE,ELSCALE,BES,SQRTS,JETSCALE`).

Submitter guards (`condor/submit_stage1.py`): the script's own `outputDir` must match
`--stage` (prevents training trees clobbering analysis ntuples), the sample campaign
follows the script's `prodTag` (winter2023_training for the leptonic treemakers), and
a qq analysis submission refuses to fan out if the BDT model file does not exist yet.

The hadronic fit observable is the unrolled 2D m_recoil × m_jj shape after the BDT
working-point cut (makeWS_2D_qq.py); the leptonic-style binned BDT-score datacard
(makeWS_BDT_binned.py qq) is retained as a cross-check of the extracted precision.
