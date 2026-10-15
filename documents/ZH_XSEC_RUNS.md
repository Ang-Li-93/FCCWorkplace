# ZH cross-section analysis — SDCC runs

FCC-ee ZH cross-section measurement (recoil method) on the winter2023 fastsim samples,
ported from CERN lxplus to SDCC/BNL. Leptonic channels (Z→ee, Z→μμ) at √s = 240 and
365 GeV are complete end-to-end; the hadronic channel (Z→qq) is fully set up with a
local BDT training (the reference pre-trained MIT model is unreachable, so the BDT is
retrained here — see the hadronic section). The paper-spec reproduction of 2026-09-29/30
(original BDT models, Tables 2 and 3 at both energies, JES/JER) is the last section of
this file; its numbers live in `documents/zh_xsec_table2_2026-09_oldbdt.md` and
`documents/zh_xsec_results_2026-09_oldbdt.md`.

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
| text2workspace / combine | `./run_combine.sh <cmd>` from the repo root (CMS combine-standalone container from cvmfs, see [COMBINE.md](COMBINE.md)); or `./run_combine.sh bash` for a shell — do **not** source key4hep inside it |

Custom C++ (leptonic `HiggsTools::*` incl. `coneIsolationTheta`, and all hadronic helpers)
is compiled into `FCCAnalyses-winter2023` (`analyzers/dataframe/{FCCAnalyses/HiggsTools.h,src/HiggsTools.cc}`).
Rebuild after edits: `cd FCCAnalyses-winter2023/build && cmake --build . --target install -j8`.

## Run book (leptonic, per channel)

1. **Stage1** (ntuples with BDTscore + systematics branches), fans out to condor
   (`accounting_group=group_usfcc`, xrootd input from eospublic, GPFS output):
   ```
   python condor/submit_stage1.py S240/mumu/stage1_analysis_ntuples.py [--dry-run]
   ```
   Job counts since 2026-09-29 (the process list includes the 87 exclusive ZH sets, 1–2 chunks
   each; `wzp6_ee_bbH_Hbb_ecm240` is a single file): S240/mumu 494, S240/ee 507, S365/mumu 488, S365/ee 481 (July, inclusive signal +
   backgrounds only: 321 / 334 / 314 / 307; ~10 min wall on a hot queue).
   The wrapper exports `FCCANA_PROCESS=<process>` (used by the qq channel's MC-truth filters).
   After the fan-out: `python3 condor/check_chunks.py --ecm 240 --flavor mumu --jobs 8`, then
   `condor/patch_empty_chunks.py --ecm 240 --flavor mumu --only <process> --apply` for every
   NO_TREE process (zero-selection jobs write tree-less files) and re-check before stage2.

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

   Steps 3–4 above are the July-2026 flow (binned BDT score, lumped background with a
   free rateParam), kept as the `bdt` cross-check. **Paper-spec flow (default since
   2026-09-29, see Tooling):** `python3 makeWS_recoil_2cat.py mumu|ee` (key4hep env;
   recoil mass 100–150 GeV in `sel_Baseline_{lo,hi}BDT`, signal = inclusive sample +
   other-Z exclusive sets, `norm_WW/ZZ/Zll/rare` 1% lnN, MUSCALE|ELSCALE / BES / SQRTS;
   `--rebin N`, `--input-base`, `--out-base`, `FCC_ALLOW_MISSING=1`), then
   `$RC ./run_fit_leptonic.sh mumu|ee`, `$RC ./run_fit_combination.sh ll|all` and
   `$RC python3 bias_test_generic.py mumu|ee|ll|qq|all` (the ll/all combined cards
   come from `run_fit_combination.sh`). `signal_by_decay.root` requires the exclusive
   ZH samples in stage1/stage2 (skipped otherwise; the per-decay own-flavor part is
   renormalized by k = I(inclusive)/I(Σ_h exclusive_h) so that Σ_h sig_h matches the
   fit signal in total yield — the BR-weighted exclusive sum only approximates the
   inclusive template). BES in the recoil templates: signal_BESUp = signal +
   (incl_BESup − incl_nominal), the other-Z part carries no BES variation. No
   autoMCStats (high-statistics MC templates; the paper's nuisance list has none).
   Dry run on the July histograms (nominal templates only, no exclusive samples,
   `FCC_ALLOW_MISSING=1 ... --input-base .../BDT_analysis_samples.jul2026/syst --out-base <scratch>`;
   2026-09-29): 240 μμ 0.683% (stat 0.662%), ee 0.815% (0.785%), ℓℓ 0.528% (0.506%),
   all with the July qq card 0.343% (0.293%); 365 μμ 1.762% (1.729%, July `zll_p > 20`
   window, 1pc BES) — paper 0.68/0.66, 0.81/0.78, 0.52/0.50, 0.31/0.26, 1.79/1.79.

## Results — July-2026 campaign (history: superseded by the 2026-09 reproduction below; Asimov, expected precision on σ_ZH; run dirs and ntuples preserved as `*.jul2026`)

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
Bias test (§7.2, 1% injection, `bias_test_qq.py`, SM-table BRs = today's `--br table`): dominant modes |bias| < 0.09%
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
S365 bias test (1% injection, SM-table BRs): all modes within ±0.34% (largest H→ττ), well inside the
0.75% uncertainty — model independence confirmed at 365.
All scans audited (parabola touches 0, minimum at r = 1).

## Systematics

| Nuisance | Source | Implementation |
|---|---|---|
| MUSCALE / ELSCALE | lepton momentum scale | ±1e-5 via `lepton_momentum_scale(±1e-5)`, Z/recoil/BDT recomputed (**down variation is −1e-5**; a legacy bug where both used +1e-5 was fixed 2026-07-04 and stage1 fully re-run) |
| JETSCALE (qq) | jet momentum scale | ±1e-5 on the Z(qq) jets, Z/recoil recomputed; BDT score **not** recomputed (enters via selection migration). NB 1e-5 is a placeholder inherited from the muon treatment (no report motivates 1e-5 for jets); the morphed-JES robustness test (`jes_morph_test.py`, linear morphing of the stored templates to 1e-4 and 1e-3) shows the fitted precision is **unchanged (0.457%) even at JES = 1e-3** — the m_jj Z peak in the fit observable self-calibrates the scale, so JETSCALE is a non-systematic for this measurement at any plausible magnitude |
| JES / JER (qq, **optional**, 2026-09-30) | jet energy scale ±1% / additional 1% jet energy smearing | the two effects arXiv:2512.21290 §5.3 evaluated (+3.9% / +3.2% relative degradation, i.e. enlargement, of the hadronic uncertainty at 240 GeV) **without** including them in the quoted precision. Built as profiled shape nuisances of the 2D m_recoil × m_jj fit on the signal **and every background component** (one nuisance each, correlated across processes): `S{ecm}/qq/stage2_jesjer_templates.py` (per-energy wrapper of `PAPER/qq_jesjer_templates.py --ecm <ecm>`) re-reads the stage1 ntuples once and writes stage2-style files `<proc>_sel_Baseline_<cat>_{jesup,jesdw,jerup}_histo.root` (TH2 `mrecoil_mjj_<tag>`) next to the stage2 output; `makeWS_2D_qq.py --jesjer` (or `--jes-only` / `--jer-only`) adds `JES` / `JER` to the card (`datacard_2d_qq_jesjer.txt`), the JER Down template being the bin-wise mirror of Up around the nominal (one-sided smearing). JES: both jets scaled by k = 1 ± 0.01 → m′ = k m, p′ = k p, E′ = k E, recoil recomputed; JER: p_i′ = p_i (1 + 0.01 g_i), g_i ~ N(0,1) with deterministic per-event draws (Box-Muller normals from a 64-bit hash of `--seed` and the event's stored kinematics: identical across runs, thread counts and file orders). The BDT score is **not** recomputed (JETSCALE convention); the stage1 m_jj / p_jj windows make the edge migration one-way (events outside the stage1 windows cannot migrate in; `--self-check` prints the edge migrations, ≲0.1% of the signal, ~1.5% of WW in loBDT at 240). Not part of the nominal (paper-spec) fit: separate run dirs `*_jesjer` |
| SQRTS | √s knowledge | recoil rebuilt at √s ± 2 MeV |
| BES | beam energy spread | dedicated samples, ±1% (240); ±10pc variants used at 365; 1% BES samples exist for **all** Z decays (inclusive in H decays, `wzp6_ee_{z}H_BES-{higher,lower}-1pc`); used for the qq BES nuisance since 2026-09, shape-only (hadronic step 8; the hadronic-Z/ττ/νν BES sets were produced on 2026-09-07, after the July campaign, whose note that none existed was correct at the time) |
| bkg components (qq) | per-component normalization | 1% lnN each on WW / ZZ / Z⁠γ* / rare (`norm_WW/ZZ/Zqq/rare`, arXiv:2512.21290; paper spec: the non-hadronic-Z ZH sets are signal, not background); ZH-other (`norm_ZH`) only in the July `--zh-other-as-bkg` definition |
| bkg components (leptonic, paper spec) | per-component normalization | 1% lnN each on WW / ZZ / Z⁠γ*→ℓℓ+ττ / rare (`norm_WW`, `norm_ZZ`, `norm_Zll`, `norm_rare`; `makeWS_recoil_2cat.py`, names shared with the qq card) |
| bkg norm (BDT-score cross-check cards) | background yield | free rateParam in the fit |

Conventions: all angular quantities are θ-based (isolation = `coneIsolationTheta(0.01, 0.5)` +
`sel_isol(0.25)`; acolinearity = |θ₁−θ₂|; no η anywhere in selections or BDT inputs).
The mH-shifted samples (±50/100 MeV) are for the mass measurement, not the xsec fit.

## Hadronic (Z→qq) channel

Ported from jeyserma/FCCPhysics `h_zh_hadronic.py` into this workflow
(shared graph `zqq_stage1_common.py`; helpers compiled into HiggsTools, including the
3-D `acolinearity_scalar`; θ-based lepton veto for orthogonality with ee/μμ).
Sample mapping: `wzp6_ee_qq` replaces the missing `wz3p6_ee_{uu,dd,ss,cc,bb}`;
signals are the 8 Z-decay × 11 H-decay wzp6 sets. `p8_ee_tt` was added at 365 by the
July port (stage1/stage2 still run it), but since 2026-09-29 the paper-spec fit **excludes
it** (`makeWS_2D_qq.py --exclude p8_ee_tt_ecm365`; author decision, the reference analysis
and the paper's fit had no tt̄ template — see the reproduction section).
Two veto details differ from the reference: the resonance builder is guarded
(the C++ helper `exit(1)`s on events with <2 leptons — i.e. most hadronic events —
and returns an empty vector without an opposite-charge pair), and the veto's p_ll
window is energy-dependent (20–70 GeV at 240; >20 GeV with no upper bound at 365,
where ZH kinematics put p_ll ≈ 146 GeV — the reference 240-era window would never
veto genuine Z(ℓℓ)H there and orthogonality with ee/μμ would be lost).

The BDT is **trained locally** (the reference pre-trained model at MIT `/ceph` is not
reachable); the July-2026 models `models/S{ecm}/qq/bdt_model_ecm{240,365}.root` are the
ones behind every quoted hadronic number, including the 2026-09 reproduction (do not
retrain for the paper numbers). The upstream `W2_costheta` bug — both `W1_costheta` and `W2_costheta` were
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
   MC-truth filters; jet-scale ±1e-5 and √s ± 2 MeV syst branches). 1105 jobs at 240 /
   1517 at 365 since the 24 inclusive / BES sets were added (July: 865 / 1279). Validate
   with `condor/check_chunks.py` and repair the tree-less zero-selection chunks with
   `condor/patch_empty_chunks.py` before stage2 (7 chunks at 240, 151 at 365).
7. **Stage2**: `fccanalysis final analysis/ZH_XSec/Paper/S240/qq/stage2_histograms_syst.py`
8. **Fit templates**: `cd S240/combine && python3 makeWS_2D_qq.py [--zh-other-as-bkg] [--bes-keep-norm] [--input-base DIR] [--out-base DIR]`
   — the **primary hadronic fit is 2D in m_recoil × m_jj** (as in the FCCPhysics
   reference), inside the stage2 baseline windows, fitted simultaneously in the two
   BDT-score regions `sel_Baseline_{lo,hi}BDT` (`MVA_WP` in `stage2_histograms_syst.py`:
   0.75 at 240, 0.95 at 365, the paper's boundaries). The TH2 templates (240: 25×24
   bins over [100,150]×[20,140]; 365: 20×18 over [100,180]×[20,200]) are summed over
   processes and unrolled to TH1 for combine, into `run_2D_mrecoil_mjj_qq/`
   (`datacard.root`, `signal_by_decay.root` for the bias test, `templates_2d.root`
   for inspection, a copy of the card).
   **Paper-spec definition** (arXiv:2512.21290 §5.2–5.3, default since 2026-09-29):
   signal = **all ZH final states** passing the hadronic selection (the 87 exclusive
   Z(qq/ss/cc/bb/ee/μμ/ττ/νν)H × H-decay sets, one POI r); backgrounds as the
   components `bkg_WW`, `bkg_ZZ`, `bkg_Zqq`, `bkg_rare`, each with a 1% lnN
   (`norm_WW/ZZ/Zqq/rare`, names shared with the leptonic cards), no rateParam, no
   autoMCStats; shape nuisances on the signal: JETSCALE (jet momentum scale) and
   SQRTS (√s ± 2 MeV) from the stage2 varied selections, BES (±1%) from the
   inclusive-H samples `wzp6_ee_<z>H[_BES-{higher,lower}-1pc]` of all 8 Z decays,
   signal_BESUp = signal + Σ_z (incl_BESup − incl_nominal), **shape-only**: each BES
   template is rescaled to the nominal signal integral of its category, because the
   two independently generated ~1M-event inclusive samples differ in normalization
   by a statistical O(1e-3) that is not a BES effect (the pre-scaling shift and the
   factor are printed; `--bes-keep-norm` keeps the raw normalization).
   `--zh-other-as-bkg` = the July-2026 definition, kept as a cross-check: signal =
   Z(qq/ss/cc/bb)H only, the other ZH sets as `bkg_ZH` (`norm_ZH` 1% lnN), no BES
   (`datacard_2d_qq_zhbkg.txt` → `run_2D_mrecoil_mjj_qq_zhbkg/`; reproduces the July
   templates bit for bit). A missing stage2 file for any process **aborts** template
   building (a gap means the production is incomplete and would bias the templates);
   `FCC_ALLOW_MISSING=1` downgrades that to a warning (a variation with no input at
   all becomes a copy of the nominal, i.e. a no-op nuisance). `--input-base`/`--out-base`:
   tests on the `*.jul2026` histograms into a scratch dir (then `FIT_BASE=<out-base>`
   for the drivers and the bias test).
   Cross-check: `python3 makeWS_BDT_binned.py qq` builds the 1D binned BDT-score
   datacard (leptonic-style) in `run_binned_BDTScore_qq/`.
   **JES / JER nuisances (optional, 2026-09-30; paper §5.3 evaluated them but did not
   include them in the quoted precision):**
   `python3 ../qq/stage2_jesjer_templates.py [--input-dir <stage dir>] [--ncpu 8] [--check]`
   (key4hep env; the per-energy wrapper of `PAPER/qq_jesjer_templates.py --ecm <ecm>`, default
   stage dir `BDT_analysis_samples_oldbdt`, `--nthreads`/`--ncpu` = ROOT implicit MT; `--check`
   (= `--check-nominal`) refills the nominal `mrecoil_mjj` through the same code path and
   requires it bit-identical to the stage2 file of every process, else exit 1; `--self-check` =
   the full validation; `--procs P1,P2,...` for tests) writes the `jesup` / `jesdw` / `jerup`
   files into the stage dir's `syst/` (new names only), then
   `python3 makeWS_2D_qq.py --jesjer --input-base <syst> --tag <sfx>_jesjer` (or
   `--jes-only --tag <sfx>_jes` / `--jer-only --tag <sfx>_jer`) builds
   `run_2D_mrecoil_mjj_qq<sfx>_jesjer/` with `datacard_2d_qq_jesjer.txt` (JES and JER on every
   process; strict missing-file policy as usual; the JES/JER integral ratios per template
   are printed). Fits: `QQ_RUNDIR_SUFFIX=<sfx>_jesjer $RC ./run_fit_qq.sh 2d` (the driver
   takes the jesjer card when the run dir holds it; `2d-jesjer` requires it) and
   `RUNDIR_SUFFIX=<sfx> QQ_RUNDIR_SUFFIX=<sfx>_jesjer ALL_RUNDIR_SUFFIX=<sfx>_jesjer $RC ./run_fit_combination.sh all recoil`
   (`ALL_RUNDIR_SUFFIX` = explicit output-dir suffix → `run_<ecm>_all<sfx>_jesjer/`). In
   both drivers `xsecSTATshapes` freezes every shape nuisance of the card (JES and JER
   included) = stat + 1% background normalizations, `xsec` floats them all; the freeze
   lists are derived from the card (for the nominal cards they equal the former
   hard-coded `BES,JETSCALE,SQRTS` / `BES,ELSCALE,JETSCALE,MUSCALE,SQRTS`).
9. **Fit** (combine container): `$RC ./run_fit_qq.sh [2d|2d-zhbkg|bdt]` — `2d`
   (default) fits the paper-spec card, `2d-zhbkg` the July-definition card, `bdt` the
   binned BDT-score cross-check; `FIT_BASE=<dir>` relocates the run dirs,
   `RANGE=r=a,b POINTS=n` override the scan (defaults r=0.97,1.03 / 120 points at 240,
   r=0.95,1.05 / 160 at 365). text2workspace + three Asimov MultiDimFit grid scans:
   `xsec` (everything profiled — beyond the paper's quoted precision), `xsecSTAT` (paper
   stat-only: `allConstrainedNuisances` + every rateParam of the card frozen, i.e. background
   normalizations fixed), `xsecSTATshapes` (only the shape nuisances JETSCALE, SQRTS[, BES]
   frozen = stat + 1% bkg, the paper's quoted total; the July run-book 'stat-only'
   definition); the freeze lists are parsed from the card. Then the precision
   printout from `fit_precision.py` (python3, generic — also works on the leptonic
   scan files, unlike the python2-era `fitAnalysis.py`) and the scan audit
   (`audit_scans.py`), tee'd to `<rundir>/fit_summary.txt`; both warn if the
   2ΔNLL = 1 crossings fall outside the range — widen and re-run.

10. **Bias test** (combine container, arXiv:2512.21290 §7.2): `$RC python3 bias_test_generic.py qq`
    (paper spec: per-decay templates summed over all 8 Z decays; `qq-zhbkg` = the July
    convention on `run_2D_mrecoil_mjj_qq_zhbkg/`, a cross-check, not a paper column)
    — perturbs each H-decay BR so the total σ_ZH shifts by 1%, refits each
    pseudo-dataset with the nominal templates, prints the per-mode bias table and
    the per-decay yield/efficiency spread. `bias_test_qq.py` is a deprecated shim
    that execs `bias_test_generic.py qq-zhbkg`. BR convention of the injection
    X/BR_h (`--br`, since 2026-09-29): `sample` (default) = the cross-section
    fractions of the winter2023 exclusive sets (`FCCee_procDict_winter2023_IDEA.json`
    via `$FCCDICTSDIR`/cvmfs, summed over the 8 Z decays, nunuH_Hinv kept in the
    sums) — the BRs the per-decay templates actually carry, Σ_h BR_h = 1; `table` =
    the SM table of the July-2026 logs (up to 4% off: Hss 0.00025 vs 0.000239 →
    an apparent −0.24% Hss bias at X = 5% in ee@240, paper Table 3: −0.01; HWW/HZZ
    ±0.03%). Both sets and their ratio are printed in the log header.

    Channel combination: `$RC ./run_fit_combination.sh all` (μμ+ee+qq(2D) →
    `run_240_all/`; the `norm_*`, BES and SQRTS nuisances are correlated across the
    channels by name; see Tooling).

Submitter guards (`condor/submit_stage1.py`): the script's own `outputDir` must match
`--stage` (prevents training trees clobbering analysis ntuples), the sample campaign
follows the script's `prodTag` (winter2023_training for the leptonic treemakers), and
a qq analysis submission refuses to fan out if the BDT model file does not exist yet.
Since 2026-09 a process whose sample dir lists no files (xrdfs failure/timeout, empty or
nonexistent dir) **aborts the submission before anything is written** (the list is
printed); `--allow-missing` restores the old behaviour (skip and continue).
`FCC_SUBMIT_BASE=<dir>` relocates the storage base (dry runs / tests outside the
production tree; default unchanged).

The hadronic fit observable is the unrolled 2D m_recoil × m_jj shape after the BDT
working-point cut (makeWS_2D_qq.py); the leptonic-style binned BDT-score datacard
(makeWS_BDT_binned.py qq) is retained as a cross-check of the extracted precision.

## Tooling (2026-09)

Tools added for the September reproduction campaign. Everything runs in the key4hep env
except the fit drivers and the bias tests, which run inside the combine container
(`RC=/gpfs/mnt/gpfs01/usfcc/ali3/FCCWorkplace/run_combine.sh`, see [COMBINE.md](COMBINE.md));
`collect_results.py` works in either.

| Tool (under `analysis/ZH_XSec/Paper/`) | One-line usage | What it does |
|---|---|---|
| `condor/submit_stage1.py` (2026-09-29 additions) | `FCC_MODELS_BASE=<dir> python3 condor/submit_stage1.py <script> --stage <NEW_STAGE> --stage-override` | `FCC_MODELS_BASE` (honoured by `site_config.bdt_model()`, default `storage/ZH_XSec_Paper/models`) picks the BDT-model tree and is exported into every job wrapper, e.g. `models_backup_2026-09-29` to score with the original CERN-trained leptonic models; `--stage-override` accepts a `--stage` that differs from the script's own `outputDir` (variant production into a NEW stage dir instead of the refusal). Job scripts must live on GPFS (a `/tmp` scratch copy is invisible to the workers). Used for the CERN-BDT cross-check (`storage/ZH_XSec_Paper/scripts_cernbdt/`, stage `BDT_analysis_samples_cernbdt`: the 87 exclusive ZH sets rescored with the CERN models + symlinks to the July chunks of the inclusive/background processes, fits under `storage/ZH_XSec_Paper/fits_cernbdt/`) |
| `condor/check_chunks.py` | `python3 condor/check_chunks.py --ecm 240 --flavor mumu [--stage MVAInputs] [--json F] [--write-resubmit]` | validates every chunk of a fan-out against `wrappers.txt` and the job `.err` logs (OK / EMPTY_TREE / MISSING / ZERO_BYTE / NO_TREE / NO_EP / UNREADABLE / EP_MISMATCH); exit 0 iff clean; `--condor-dir/--out-dir` check a `*.jul2026` snapshot read-only |
| `condor/patch_empty_chunks.py` | `python3 condor/patch_empty_chunks.py --ecm 365 --flavor qq [--stage S] [--apply] [--include-missing]` | replaces key-less / unreadable chunks of jobs whose log is clean and reports 0 selected events by an empty `events` tree (branch list cloned from a good chunk) + `eventsProcessed` from the log; dry run by default, keeps the original as `.keyless`, refuses to write into `*.jul2026`; supersedes the channel-level `S365/qq/patch_empty_chunks.py` (deleted 2026-09-29) |
| `S{ecm}/combine/makeWS_recoil_2cat.py` | `python3 makeWS_recoil_2cat.py mumu\|ee` (key4hep env, from `S{ecm}/combine`) | **paper-spec leptonic fit inputs** (arXiv:2512.21290 §5.2–5.3): recoil mass 100–150 GeV in two BDT-score regions (0.83 μμ / 0.88 ee at 240, 0.66 / 0.76 at 365), backgrounds as separate components (`bkg_WW`, `bkg_ZZ`, `bkg_Zll` = Z/γ*→ℓℓ + ττ, `bkg_rare`; `norm_*` lnN 1% each, names shared with the qq card so the combination correlates them; no rateParam), signal = **all ZH final states** passing the selection (Z(ℓℓ)H + Z(ττ/νν/qq̄)H, one POI r), shape nuisances BES / MUSCALE|ELSCALE / SQRTS, `signal_by_decay.root` (`<cat>_sig_<Hdecay>`) for the bias test, strict missing-process abort (`FCC_ALLOW_MISSING=1`) — mirrors `makeWS_2D_qq.py`; writes `run_recoil_2cat_<flavor>/`. The binned BDT-score fit (`makeWS_BDT_binned.py`, lumped background with a free rateParam) is now the **cross-check** |
| `S{ecm}/combine/run_fit_leptonic.sh` | `$RC ./run_fit_leptonic.sh mumu\|ee [recoil\|bdt]` (from `S{ecm}/combine`; `FIT_BASE=<dir>` relocates the run dirs, `RANGE=r=a,b POINTS=n` override the scan) | `recoil` (default) fits the paper-spec card in `run_recoil_2cat_<flavor>/`, `bdt` the July-style binned BDT-score card in `run_binned_BDTScore_<flavor>/` (the collector's cross-check rows); text2workspace + three Asimov MultiDimFit grid scans: `xsec` (everything profiled — beyond the paper's quoted precision), `xsecSTAT` (**paper stat-only**: `allConstrainedNuisances` + every rateParam of the card frozen = background normalizations fixed; the recoil cards have no rateParam), `xsecSTATshapes` (shape nuisances only frozen = stat + 1% bkg, **the paper's quoted total**; the July run-book 'stat-only' definition), then `fit_precision.py` + `audit_scans.py` → `<rundir>/fit_summary.txt`; freeze lists parsed from the card |
| `S{ecm}/combine/run_fit_combination.sh` | `$RC ./run_fit_combination.sh ll\|all [recoil\|bdt]` | `combineCards.py` on absolute channel-card paths (`recoil`, default: ll = μμ+ee → `run_recoil_2cat_combined/`, all = μμ+ee+qq(2D) → `run_<ecm>_all/`; `bdt`: the binned BDT-score leptonic cards → `run_binned_BDTScore_combined/` / `run_<ecm>_all_bdt/`, the cross-check rows), then the same three scans and printouts |
| `S{ecm}/qq/stage2_jesjer_templates.py` (2026-09-30) | `python3 stage2_jesjer_templates.py [--stage-dir\|--input-dir D] [--out-dir D] [--ref-dir D] [--procs P1,P2,...] [--nthreads\|--ncpu N] [--seed S] [--self-check \| --check-nominal\|--check] [--compare-dir D]` (key4hep env; per-energy wrapper of `PAPER/qq_jesjer_templates.py --ecm <ecm>`, one implementation for both energies) | JES / JER templates for the hadronic 2D fit (see Systematics): one RDataFrame pass per process over the stage1 chunks (default stage dir `STORE/S<ecm>/qq/BDT_analysis_samples_oldbdt`, output `<stage-dir>/syst`), stage2 selection re-applied with the varied m_jj / p_jj / m_recoil (windows, `MVA_WP`, binning, process list and procDict imported from `S<ecm>/qq/stage2_histograms_syst.py`), `fccanalysis final` normalization (σ·k·ε / Σ eventsProcessed, intLumi 1), output `<proc>_sel_Baseline_<cat>_<tag>_histo.root` (cat hiBDT / loBDT / nomva, tag jesup / jesdw / jerup) with `mrecoil_mjj_<tag>` + 1D controls + the TParameters; `--check-nominal` / `--check` = the nominal `mrecoil_mjj` refilled through the same code path must be bit-identical (rel. diff < 1e-9) to the stage2 file of every process, else exit 1; `--self-check` = the full validation (JES at 1e-5 vs the stored scaleup/scaledw branches, JER at σ = 0 vs the nominal, massless-rebuild diagnostic per clustering hypothesis, edge migrations); `--compare-dir` = bin-by-bin reproducibility against another production; the JER draws are a pure function of `--seed` and the event content (MT- and file-order-invariant). The process list is the stage2 config's (inclusive-H / BES samples included); makeWS reads the JES/JER files of the signal and background components only (BES stays nominal) |
| `S{ecm}/combine/makeWS_2D_qq.py --jesjer` / `--jes-only` / `--jer-only` (2026-09-30) | `python3 makeWS_2D_qq.py --jesjer --input-base <syst> --tag _oldbdt_jesjer [--exclude ...]` | JES / JER shape nuisances on the signal and every background component from the jesup/jesdw/jerup files (JER Down = mirror of Up around the nominal, clipped at 0, clipped bins counted); card `datacard_2d_qq_jesjer.txt` (= `datacard_2d_qq.txt` + two shape lines) copied into the run dir instead of `datacard_2d_qq.txt` (with `--jes-only` / `--jer-only` without the other line; a stale card of the other kind is removed) |
| `run_fit_qq.sh 2d` / `2d-jesjer`, `run_fit_combination.sh` `ALL_RUNDIR_SUFFIX` (2026-09-30) | `QQ_RUNDIR_SUFFIX=_oldbdt_jesjer $RC ./run_fit_qq.sh 2d`; `RUNDIR_SUFFIX=_oldbdt QQ_RUNDIR_SUFFIX=_oldbdt_jesjer ALL_RUNDIR_SUFFIX=_oldbdt_jesjer $RC ./run_fit_combination.sh all recoil` | both drivers fit whichever of `datacard_2d_qq.txt` / `datacard_2d_qq_jesjer.txt` the qq run dir holds (both = error; `2d-jesjer` requires the latter) and print the JES/JER nuisances found; `ALL_RUNDIR_SUFFIX` = explicit output-dir suffix of `all` (default: `<RUNDIR_SUFFIX><QQ_RUNDIR_SUFFIX>`, identical suffixes not doubled; `bias_test_generic.py all` honours it for its default `--tag`; `bias_test_generic.py qq` falls back to the jesjer card) |
| `S{ecm}/combine/bias_test_generic.py` | `$RC python3 bias_test_generic.py mumu\|ee\|ll\|qq\|qq-zhbkg\|all [--br sample\|table]` | §7.2 bias test for any channel/combination: perturbs each H-decay BR so that σ_ZH shifts by X (5% for μμ/ee/ℓℓ, 1% for qq/all), refits with the nominal templates, bias = r_fit − (1+X); prints `=== bias test: channel=<ch> X = <X>% br=<mode> ...` + `  Hbb  BR= ...  r_fit=...  bias=...%` lines and leaves `<rundir>/bias_<H>/higgsCombinebiastest.MultiDimFit.mH125.root` (`qq-zhbkg` = the July hadronic-Z convention on `run_2D_mrecoil_mjj_qq_zhbkg/`, a cross-check the collector skips; `bias_test_qq.py` = deprecated shim that execs it). `--br sample` (default): BR_h of the injection = winter2023 exclusive-set cross-section fractions from the procDict on cvmfs (what the templates carry); `--br table`: the SM table of the July logs (Hss 4% off → apparent −0.2% bias at X = 5%); both sets printed in the header |
| `collect_results.py` | `python3 collect_results.py [--suffix .jul2026] [--base DIR] [--bias-logs [ECM:]FILE ...] [--out F]` | markdown summary of every scan vs paper Table 2 (paper total ↔ `xsecSTATshapes` = stat + bkg norm, stat-only ↔ `xsecSTAT`, ratios, bkg-norm component; `xsec` = + regular syst profiled, shown as beyond the paper; `--cut-based`, implied by a suffix containing `cutbased`, compares with the Cut-based columns) and of the bias tests vs Table 3 (all five columns, from the `bias_<H>/` fit files or the stdout logs); paper-spec rows `run_recoil_2cat_{mumu,ee,combined}`, `run_2D_mrecoil_mjj_qq`, `run_<ecm>_all`, July-style rows (`run_binned_BDTScore_*`, `run_<ecm>_all_bdt`) as cross-checks; `--suffix .jul2026` reproduces the July table above |
| `S{ecm}/combine/makeWS_recoil_2cat.py --single-region` (2026-09-30) | `python3 makeWS_recoil_2cat.py mumu\|ee --single-region --input-base <syst> --tag _oldbdt_cutbased` | the paper's **cut-based** leptonic configuration (Table 2 'Cut-based'): ONE region `noBDT` = loBDT + hiBDT summed (checked = `sel_Baseline_wide` per process and bin, WARNING above 1e-6), one-bin derivative of `datacard_recoil_2cat_<flavor>.txt` under the same name; the run dir keeps the name `run_recoil_2cat_<flavor><tag>` ('2cat' historical) so that the drivers and `bias_test_generic.py` work unchanged through `RUNDIR_SUFFIX` / `--tag`; give it a `--tag` (else the two-region dir is overwritten); the default build is bit-identical |
| `S{ecm}/combine/makeWS_2D_qq.py --recoil-only` (2026-09-30) | `python3 makeWS_2D_qq.py --recoil-only --input-base <syst> --tag _oldbdt_cutbased [--exclude ...]` | the paper's **cut-based** hadronic configuration: ONE region `nomva` (stage2 `sel_Baseline_nomva`, no BDT cut), observable = the m_recoil projection of `mrecoil_mjj` (in-range m_jj bins summed), same signal / background / nuisance definitions, BES shape-only on the projection, one-bin derivation of `datacard_2d_qq.txt` in `run_2D_mrecoil_mjj_qq<tag>` ('2D' historical; `templates_recoil.root` instead of `templates_2d.root`); refuses `--jesjer` / `--jes-only` / `--jer-only` and a missing `--tag`; `run_fit_qq.sh 2d` fits the one-bin card unchanged and prints a ONE-bin marker line into `fit_summary.txt` |
| `table2_paper_layout.py` (2026-09-30) | `python3 table2_paper_layout.py --suffix _oldbdt --cut-suffix _oldbdt_cutbased --label 'original models' --out F.md --tex F.tex` | Table 2 in the paper's own layout (rows ee / μμ / ℓℓ / qq / combination, columns Cut-based / MVA-based × 240 / 365, cells total (stat-only)): paper vs reproduction with the mapping paper total ↔ `xsecSTATshapes`, stat-only ↔ `xsecSTAT`; second table = differences, third = every scan at three decimals incl. `xsec` and the JES/JER dirs (beyond the paper); booktabs LaTeX with two numbers per cell; built on `table2.py`'s readers; `--cut-suffix` defaults to `<suffix>_cutbased` |

Environment notes (leptonic training trio `process_sig_bkg_samples_for_xgb.py` /
`train_xgb.py` / `evaluation.py`, verified 2026-09-29):

```bash
export MPLCONFIGDIR=/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper/S240/mumu/training/mplconfig   # S{ecm}/{flavor}; any GPFS/tmp dir works (matplotlib cache; home is not writable from the batch/agent shells)
export PATH=/cvmfs/sft.cern.ch/lcg/external/texlive/2016/bin/x86_64-linux:$PATH   # dvipng for the usetex .png output; the system texlive lacks it
```

`evaluation.py` (all four leptonic copies) scores the validation set with the **full
booster** (`predict_proba(X, iteration_range=(0, num_boosted_rounds))`) — the deployed
TMVA RBDT model written by `SaveXGBoost` contains every boosted round, whereas
`predict_proba` alone stops at `best_iteration+1` when early stopping triggered (July
μμ model: 349 vs 350 rounds, scores differ by up to 2e-3); it prints both numbers.

## Reproduction campaign 2026-09-29/30 — paper-spec results with the original models

Full re-run of the arXiv:2512.21290 (JHEP) analysis on SDCC: both energies, all three
channels, paper-spec fits, Table 2 and Table 3, plus the JES/JER evaluation of §5.3.
Campaign log: `storage/ZH_XSec_Paper/reproduce_2026-09-29.log`; the tools are described
once in [Tooling (2026-09)](#tooling-2026-09) and only referenced here.

### Purpose and decisions

- **Original BDT models** for every final number (author decision, 2026-09-29): leptonic =
  the CERN-trained `xgb_bdt.root` files, hadronic = the July-2026 locally trained
  `bdt_model_ecm{240,365}.root`. The live `storage/ZH_XSec_Paper/models/` is the restored
  copy of `models_backup_2026-09-29/` (`MD5SUMS.txt`: S240 μμ `2e73ce79…`, S240 ee
  `eb89b7c4…`, S365 μμ `6b8b3396…`, S365 ee `0c3d13b4…`, S240 qq `87f7df68…`, S365 qq
  `6927a09e…`). All six BDTs had also been retrained earlier that day (archived with their
  own `MD5SUMS.txt` in `models_retrained_2026-09-29/`); those results are kept only as a
  cross-check (live run dirs without suffix): they differ from the original-model numbers
  by < 0.01 in every comparable Table-2 cell, the retrained leptonic models being
  near-copies of the originals (same training samples and hyperparameters, score
  correlation 0.98). **Do not retrain for the paper numbers.**
- **No tt̄ template at 365 GeV** (author decision: "the ttbar should be negligible"). The
  reference FCCPhysics analysis, and hence the paper's fit, had none; the July port had added
  `p8_ee_tt_ecm365` (Pythia8, 0.8 pb) to `bkg_rare`. That sample passes the hadronic
  selection at 73% (hiBDT: 2.8× the signal, the BDT never saw tt̄) and would inflate the 365
  hadronic total to 0.757% — a documented caveat for the author (the paper quotes the WHIZARD
  WbWb sample, 0.46 pb, as negligible). Implemented as `makeWS_2D_qq.py --exclude p8_ee_tt_ecm365`.
- **Paper-spec fits everywhere.** Leptonic: recoil mass 100–150 GeV in two BDT-score regions
  (boundaries 0.83 μμ / 0.88 ee at 240, 0.66 / 0.76 at 365; the 365 selections use the paper's
  50 < p_ℓℓ < 150 GeV window), signal = all ZH final states (inclusive sample + the 87 exclusive
  sets of the other Z decays), backgrounds WW / ZZ / Z(ℓℓ) / rare with 1% lnN (`norm_*`), shape
  nuisances BES (dedicated 1pc samples), MUSCALE|ELSCALE (1e-5), SQRTS (2 MeV). Hadronic: 2D
  m_recoil × m_jj in two BDT regions (WP 0.75 / 0.95), signal = all 87 ZH sets, backgrounds
  WW / ZZ / Z(qq) / rare with 1% lnN, shapes BES (inclusive-sample difference, shape-only),
  JETSCALE (1e-5 placeholder), SQRTS. Combination cards share BES, SQRTS, `norm_WW`, `norm_ZZ`
  and `norm_rare` across the channels. Uncertainty definitions: **stat only** = every
  constrained nuisance frozen (`xsecSTAT`; the paper's stat-only, "obtained by fixing the
  background normalization parameters"), **stat + 1% bkg** = shape nuisances frozen, `norm_*`
  floating (`xsecSTATshapes`; **the paper's quoted total** — the 1% normalizations are the only
  nuisance parameters of the paper's fit, §5.3), **+ regular syst** = nothing frozen (`xsec`: BES,
  momentum scale, √s profiled in addition — beyond the paper's quoted precision, which evaluated
  these effects separately at 0.095% combined; mapping corrected 2026-09-30, see the
  paper-layout subsection below).
- **Bias tests with `--br sample`** (BR_h = winter2023 exclusive-sample cross-section
  fractions, i.e. the fractions the per-decay templates carry); X = 5% for μμ / ee / ℓℓ, 1%
  for qq and the combination.

### Table 2 — relative uncertainty on σ_ZH in % (Asimov, 2ΔNLL = 1 crossings; paper value with its stat-only in brackets)

240 GeV (10.8 ab⁻¹):

| Channel | Paper total (stat) | stat only (= paper stat) | stat + 1% bkg (= paper total) | + regular syst (beyond the paper) | + JES/JER (beyond the paper) |
|---|---|---|---|---|---|
| Z(ee)H | 0.81 (0.78) | 0.783 | 0.805 | 0.817 | 0.817* |
| Z(μμ)H | 0.68 (0.66) | 0.660 | 0.679 | 0.685 | 0.685* |
| Z(ℓℓ)H | 0.52 (0.50) | 0.505 | 0.523 | 0.529 | 0.529* |
| Z(qq)H | 0.38 (0.30) | 0.311 | 0.404 | 0.404 | 0.408 |
| Combination | 0.31 (0.26) | 0.265 | 0.318 | 0.318 | 0.321 |

365 GeV (3.12 ab⁻¹, no tt̄ template):

| Channel | Paper total (stat) | stat only (= paper stat) | stat + 1% bkg (= paper total) | + regular syst (beyond the paper) | + JES/JER (beyond the paper) |
|---|---|---|---|---|---|
| Z(ee)H | 1.91 (1.90) | 1.838 | 1.889 | 1.905 | 1.905* |
| Z(μμ)H | 1.79 (1.79) | 1.728 | 1.775 | 1.775 | 1.775* |
| Z(ℓℓ)H | 1.32 (1.30) | 1.259 | 1.307 | 1.308 | 1.308* |
| Z(qq)H | 0.56 (0.47) | 0.432 | 0.513 | 0.513 | 0.515 |
| Combination | 0.52 (0.44) | 0.409 | 0.482 | 0.482 | 0.484 |

(*) leptonic final states have no jets: the JES/JER column repeats the previous one by
construction (no `_oldbdt_jesjer` run dir). Regular syst = BES, lepton / jet momentum scale,
√s. The 1% background normalizations dominate the systematic budget (in quadrature 0.26% for
qq and 0.18% for the combination at 240 GeV); the regular shape nuisances add 0.01–0.14%.
The paper's quoted total is the "stat + 1% bkg" column (`xsecSTATshapes`) and its stat-only the
"stat only" column (`xsecSTAT`); "+ regular syst" and "+ JES/JER" go beyond the paper's quoted
precision (mapping corrected 2026-09-30 — an earlier note here equated the paper's total with
"+ regular syst"; details and the cut-based columns in the next subsection).
Every number is the `fit_summary.txt` value of its run dir (`table2_full.py` cross-checks all
66 values against the scan files, "all match"; the collector document repeats the
paper-definition columns from the same files).

Cross-checks: the July-definition hadronic card (`--zh-other-as-bkg`: Z(qq/ss/cc/bb)H signal,
the other ZH sets as `bkg_ZH`, no BES) with the original model gives 240: 0.457 / 0.358 (= July
2026 exactly) and 365 (no tt̄): 0.535 / 0.479 (total / stat only). The retrained-model
campaign (live run dirs without suffix, campaign log) gives 240: every channel within 0.005
of the table (combination 0.318 / 0.265); 365: qq without tt̄ 0.516 / 0.433, combination with
tt̄ 0.656 / 0.516 (its qq part 0.757 / 0.565).

### Table 2 in the paper's layout (cut-based / MVA-based)

Paper Table 2 (JHEP, §6) next to the reproduction with the original models — both energies, all
four columns, every cell "total (stat-only)" in % of σ_ZH. Document:
`documents/zh_xsec_table2_paper_layout_2026-09_oldbdt.md` / `.tex` (`table2_paper_layout.py`:
this table, the differences, every scan at three decimals, freeze lists and sources; 72 values
cross-checked against the `fit_summary.txt` files, all match).

**Mapping (corrected 2026-09-30).** The paper's fit carries the 1% background normalizations as
its only nuisance parameters ("each with a normalization uncertainty of 1% included as a
nuisance parameter in the fit"; "Shape uncertainties are not included as nuisance parameters in
this study", §5.3) and its stat-only numbers "are obtained by fixing the background normalization
parameters in the likelihood fit" (§6). Hence **paper total = `xsecSTATshapes`** (shape nuisances
frozen, `norm_*` floating = stat + 1% bkg) and **paper stat-only = `xsecSTAT`** (everything
frozen). The `xsec` scan (nothing frozen: BES, momentum scale, √s profiled in addition) and the
JES/JER run dirs go **beyond the paper's quoted precision** — the paper evaluated those effects
separately by repeating the fit with shifted inputs (0.095% combined) and left JES/JER out. The
"+ regular syst" column of the 5-column table above is therefore not the paper's total; the
earlier note that equated the two was wrong. MVA-based = run dirs `*_oldbdt`; cut-based =
`*_oldbdt_cutbased` (recipe below).

| Final state | | 240 Cut-based | 240 MVA-based | 365 Cut-based | 365 MVA-based |
|---|---|---|---|---|---|
| Z(ee)H | paper | 1.01 (0.97) | 0.81 (0.78) | 2.27 (2.16) | 1.91 (1.90) |
| | reproduction | 1.14 (1.08) | 0.80 (0.78) | 3.40 (2.87) | 1.89 (1.84) |
| Z(μμ)H | paper | 0.84 (0.80) | 0.68 (0.66) | 2.11 (2.03) | 1.79 (1.79) |
| | reproduction | 0.86 (0.82) | 0.68 (0.66) | 3.34 (2.86) | 1.77 (1.73) |
| Z(ℓℓ)H | paper | 0.64 (0.62) | 0.52 (0.50) | 1.56 (1.48) | 1.32 (1.30) |
| | reproduction | 0.69 (0.65) | 0.52 (0.50) | 2.45 (2.03) | 1.31 (1.26) |
| Z(qq)H | paper | 1.20 (0.63) | 0.38 (0.30) | 1.42 (0.63) | 0.56 (0.47) |
| | reproduction | 1.41 (0.68) | 0.40 (0.31) | 1.41 (0.62) | 0.51 (0.43) |
| Combination | paper | 0.56 (0.44) | 0.31 (0.26) | 1.06 (0.58) | 0.52 (0.44) |
| | reproduction | 0.62 (0.47) | 0.32 (0.26) | 1.23 (0.60) | 0.48 (0.41) |

Reproduction cells rounded to the paper's two decimals (0.805 → 0.80 and 1.415 → 1.41 sit on the
rounding edge). Three decimals, cut-based, `xsecSTAT` / `xsecSTATshapes` / `xsec`: 240 ee 1.077 /
1.138 / 1.154, μμ 0.825 / 0.865 / 0.884, ℓℓ 0.655 / 0.688 / 0.709, qq 0.677 / 1.414 / 1.417,
combination 0.471 / 0.618 / 0.637; 365 ee 2.874 / 3.403 / 3.414, μμ 2.861 / 3.341 / 3.342, ℓℓ
2.027 / 2.446 / 2.451, qq 0.624 / 1.415 / 1.564, combination 0.597 / 1.227 / 1.310 (MVA-based:
the 5-column table above). Differences reproduction − paper, total (stat), in % points:

| Final state | 240 Cut-based | 240 MVA-based | 365 Cut-based | 365 MVA-based |
|---|---|---|---|---|
| Z(ee)H | +0.128 (+0.107) | −0.005 (+0.003) | +1.133 (+0.714) | −0.021 (−0.062) |
| Z(μμ)H | +0.025 (+0.025) | −0.001 (+0.000) | +1.231 (+0.831) | −0.015 (−0.062) |
| Z(ℓℓ)H | +0.048 (+0.035) | +0.003 (+0.005) | +0.886 (+0.547) | −0.013 (−0.041) |
| Z(qq)H | +0.214 (+0.047) | +0.024 (+0.011) | −0.005 (−0.006) | −0.047 (−0.038) |
| Combination | +0.058 (+0.031) | +0.008 (+0.005) | +0.167 (+0.017) | −0.038 (−0.031) |

Reading of the comparison:
- **MVA-based**: 240 GeV within 0.01 in every leptonic cell, qq +0.024 (+0.011), combination
  +0.008 (+0.005); 365 GeV 0.01–0.06 below the paper everywhere (qq 0.513 / 0.432 vs 0.56 / 0.47,
  combination 0.482 / 0.409 vs 0.52 / 0.44).
- **Cut-based 240 GeV**: μμ (+0.025 / +0.025) and ℓℓ (+0.048 / +0.035) reproduce, ee is 0.13 / 0.11
  worse (1.14 / 1.08 vs 1.01 / 0.97); qq 1.414 / 0.677 vs 1.20 / 0.63 (+18% / +7%): the excess is
  the background-normalization component (1.24% vs the paper's √(1.20² − 0.63²) = 1.02%; S/B =
  0.011 in the single region, `norm_ZZ` / `norm_rare` unconstrained by the fit), binning excluded as
  the cause (0.5-GeV templates: 1.401 / 0.676); combination 0.618 / 0.471 vs 0.56 / 0.44. The 240
  leptonic numbers coincide to within 0.003 with the July referee baseline (`run_noBDT_recoil_*.jul2026`:
  μμ 0.881 / 0.863, ee 1.154 / 1.138 — `xsec` / the July `xsecSTAT`, which froze the shape nuisances
  only with the background rateParam floating, i.e. today's `xsecSTATshapes` definition; ℓℓ 0.709 =
  `xsec` of `run_240_noBDT_ll.jul2026`, its only scan), as expected: lo + hi = wide makes the
  cut-based templates independent of the BDT model (the `_oldbdt` part of the tag only names the
  stage2 production).
- **Cut-based 365 GeV**: qq 1.415 / 0.624 vs 1.42 / 0.63 reproduces to better than 0.01 (−0.005 / −0.006); the leptonic
  channels do not — μμ 3.34 / 2.86 vs 2.11 / 2.03, ee 3.40 / 2.87 vs 2.27 / 2.16, ℓℓ 2.45 / 2.03 vs
  1.56 / 1.48; combination 1.23 / 0.60 vs 1.06 / 0.58. Diagnosis (`cutbased_logs/07_fisher_stat_diagnostic.log`,
  `08_fisher_selections.log`): an exact Asimov Fisher calculation on the templates reproduces every
  combine stat-only to 0.001 and attributes the whole single-region loss to the Z/γ*→ℓℓ sample
  under the recoil peak (without it: 365 μμ 2.20, ee 2.03 stat-only, so removing that sample alone
  does not reach the paper's μμ value; the July tight selection with |cos θ_miss| < 0.98 and
  120–140 GeV gives 1.63 / 1.79 — the paper's 2.03 / 2.16 lie between the tight and the wide
  (paper-stated, 2.86 / 2.87 stat-only) selections; the recoil window 100–150 vs 120–140 GeV alone
  is irrelevant, the |cos θ_miss| cut is what changes the single-region result). The paper's stated leptonic selection (§4.2) is exactly
  loBDT + hiBDT, i.e. the events of the two-region fit that reproduces the MVA column at both
  energies, so the paper's 365 cut-based leptonic numbers correspond to a smaller fermion-pair
  contamination than that selection gives in one region (an additional cut used only in the
  cut-based fit would do it) — an inference from the numbers, not documented in the paper.
  Follow-up scan (`cutbased_logs/12_cosmiss_scan_*`, recoil × |cos θ_miss| refilled from the stage1
  ntuples, closure on the stage2 wide histograms at 1e-16): a |cos θ_miss| cut does NOT reproduce the
  paper's column. The collinear population sits in a spike at |cos θ_miss| = 1, so even the loosest cut
  (0.9999) gives 240 μμ 0.64 (0.61), ee 0.78 (0.74), 365 μμ 1.95 (1.81), ee 2.12 (1.95), better than the
  paper everywhere. Dropping a whole sample group does not either (365 μμ / ee stat-only: no Z/γ*→ℓℓ
  2.20 / 2.03, no rare 2.42 / 2.65). Matching the paper's stat-only needs the Z/γ*→ℓℓ + rare yield
  scaled by 0.94 (240 μμ), 0.75 (240 ee), 0.29 (365 μμ), 0.33 (365 ee): the paper's cut-based fit saw
  about a third of that background at 365 and nearly all of it at 240. Its configuration is not in
  this repository (the only original baseline script fits the BDT score); open question for the author.
  The p_ℓℓ window is not the cause either (`cutbased_logs/13_pwin_*`): with the original requirement
  p_ℓℓ > 20 GeV only, or no momentum cut, the single-region stat-only stays at 0.81 / 1.06 (240 μμ / ee)
  and 2.86 / 2.87 (365); only the 365 totals improve (3.34 → 3.16, 3.40 → 3.21) from the extra lower
  sideband below 116 GeV that p_ℓℓ < 150 removes. The original lumped-background card with a free
  normalization gives the same stat-only and 0.85 / 1.12 / 3.53 / 3.67 totals on the paper selection.
- **Origin of the published fits (2026-09-30)**: the paper's Table 2 comes from Jan Eysermans'
  FCCPhysics `analyses/h_zh` (github.com/jeyserma/FCCPhysics, commit fc3316f 2026-09-16; copy in
  `storage/ZH_XSec_Paper/reference_FCCPhysics_h_zh/`), run at MIT on `/ceph/submit/.../winter2023/IDEA`.
  Differences to the SDCC chain that matter for a single-region fit: (1) the fermion-pair backgrounds
  are the WHIZARD 3 samples `wz3p6_ee_{mumu,ee_Mee_30_150,tautau,uu,dd,ss,cc,bb,nunu}` (the paper's
  §3.1 says WHIZARD3), which exist neither in the cvmfs winter2023 procDict nor in any campaign under
  `/eos/experiment/fcc/ee/generation/DelphesEvents` nor on SDCC — the SDCC chain uses the older
  `wzp6_*` samples; (2) `p8_ee_WW` with `is_ww_leptonic` events removed plus the separate
  `p8_ee_WW_{mumu,ee}` samples; (3) H→ℓℓ candidate pairs (|m_ℓℓ − 125| < 3 GeV) removed before the
  Z pairing (`leps_good`); (4) cos θ_miss from `missingEnergy(ecm, ReconstructedParticles)`, not from
  the MissingET collection (the cut itself is commented out in the histmaker); (5) `intLumi = 3e6`
  pb⁻¹ at 365 GeV in both histmakers, i.e. 3.0 ab⁻¹ while the paper text says 3.12 ab⁻¹ (√(3.12/3.0)
  = 1.02, which accounts for most of the 2–3% by which the SDCC MVA-based 365 numbers are better);
  (6) `combine.py` has no single-region option left in the committed code (the recoil-only lines are
  commented out; `--freezeBackgrounds` = the paper's stat-only). The MVA column is insensitive to
  (1)–(4) because the BDT removes the fermion-pair events.
- **Direct test with Jan's histmaker on SDCC (2026-09-30, `storage/ZH_XSec_Paper/jan_histmaker/`,
  logs + `code/analyze.py`)**: the author states wz3p6 = wzp6 (same central samples). His
  `h_zh_leptonic.py` run here at 365 GeV over the same 14 central samples (68 M events; ZZ/WW file
  subsets) reproduces the SDCC stage2 single-region yields per process to ≤ 0.3% (v3 variant = SDCC
  chain inside his histmaker: exact) and the same single-region stat-only 2.858 / 2.869% (μμ / ee);
  cut flows agree step by step. The isolation cone (η–φ vs θ–φ: ≤ 0.3% at cut1, 0 at cut5), the
  H→ℓℓ candidate removal (≤ 0.05%) and the resonance builders (identical) are excluded. The user's
  own 2024 EOS `FinalReport/S{ecm}/{fl}/BDT_analysis_samples/final` histograms give the same
  (365 no-cos-θ_miss: 2.92 / 2.95 stat-only; |cos θ_miss| < 0.98: ee 1.80). No selection, window,
  binning, p_ℓℓ window, background subset or card structure available in either code base gives the
  paper's 2.03 / 2.16 (365) or 0.97 (240 ee); the cut-based column of the JHEP Table 2 is therefore
  not reproducible from the stated inputs. Two side findings for the paper: Jan's histmaker feeds
  the BDT an `acolinearity` = acos(−cos ∠) (mean 1.86) whereas the model was trained on
  HiggsTools' |θ₁ − θ₂| (mean 0.77) — the hi-score signal fraction becomes 0.74 instead of 0.86 (365
  μμ), two-region stat-only 1.745 vs 1.729 —, and his 365 histograms are normalised to 3.0 ab⁻¹
  while the text says 3.12 ab⁻¹.
  Categorization gain (stat-only, single / two regions): 240 μμ 1.25, ee 1.38 (paper 1.21 / 1.24);
  365 μμ 1.66, ee 1.56 (paper 1.13 / 1.14). Hadronic cut-based / MVA ratio of the totals: 3.5 (240)
  and 2.8 (365), paper 3.2 and 2.5.
- **365 hadronic `xsec` caveat**: 1.564 vs `xsecSTATshapes` 1.415 — the 0.667% (quadrature)
  difference is entirely the BES nuisance (freeze scans, `04_diag_freeze_scans_S365.log`), whose 365
  templates are pathological in one dimension (Up and Down same-sided in 17 of 20 bins, peak bin
  +1.1%, χ²/bin ≈ 10 against the MC noise of the inclusive-sample difference; the 2D fit constrains
  the same nuisance to 0.005%). At 240 the same difference is 0.090%. The 365 profiles are asymmetric
  (2ΔNLL = 1 at −1.713 / +1.415 around r = 1 for qq, −1.392 / +1.228 for the combination 1.310), so neither
  `xsec` value is a symmetric precision; the generated document flags them. Not paper-comparable numbers.

### What makes the remaining differences (2026-10-01)

Variants run to explain the reproduction-vs-paper gaps (original models unless stated; run dirs under
`PAPER/S{ecm}/combine/`; logs in `storage/ZH_XSec_Paper/{lumi3p0,janacol,bugw}_logs/` and
`cutbased_logs/14_*`, `15_hadronic_binning/`). Cells are total (stat-only) in %, paper convention
(`xsecSTATshapes` / `xsecSTAT`).

- **Luminosity 3.0 ab⁻¹ at 365 GeV** (`--lumi-scale 0.961538` added to both makeWS builders, tags
  `_oldbdt_lumi3p0` / `_oldbdt_cutbased_lumi3p0`, 30 scans audited): every stat-only value scales by
  √(3.12/3.0) = 1.020 within ±0.1%. MVA-based: ee 1.925 (1.875), μμ 1.809 (1.763), ℓℓ 1.332 (1.284),
  qq 0.523 (0.440), ZH 0.491 (0.417) vs paper 1.91 (1.90), 1.79 (1.79), 1.32 (1.30), 0.56 (0.47),
  0.52 (0.44): the leptonic totals bracket the paper (−0.01…−0.02 at 3.12, +0.01…+0.02 at 3.0); the
  cut-based leptonic cells stay ~1 point worse at either luminosity.
- **Leptonic BDT applied as the paper did** (`PAPER/rescore_leptonic.py --acol jan`: the original
  models re-scored with acolinearity = acos(−cos ∠) instead of the training |Δθ|; stage dirs
  `BDT_analysis_samples_janacol`, tag `_oldbdt_janacol`; validation with the training definition
  reproduces the stored scores bit-exactly): 240 μμ 0.679 (0.660), ee 0.809 (0.787), ℓℓ 0.524
  (0.506); 365 μμ 1.794 (1.751), ee 1.916 (1.861), ℓℓ 1.322 (1.275) — **all six paper totals
  reproduced within 0.01** (0.68/0.81/0.52, 1.79/1.91/1.32) at 3.12 ab⁻¹. The mismatch moves the
  hi-score signal fraction from 0.856 → 0.741 (365 μμ), 0.739 → 0.765 (365 ee), 0.678 → 0.682
  (240 μμ), 0.560 → 0.601 (240 ee), exactly as Jan's histmaker run showed. The paper's 365 stat-only
  parentheses (1.79/1.90/1.30 = its totals) remain unexplained: every configuration here keeps a
  background-normalisation component of 0.35–0.45 in quadrature at 365, the same relative size the
  paper itself shows at 240, so they look like a bookkeeping slip, not a physics difference.
- **Leptonic BDT retrained with Jan's acolinearity and applied consistently** (`LEP_ACOL=jan` in the
  training trio, models `models_variants/janacol/S{ecm}/{fl}/xgb_bdt.root`, stage dirs
  `BDT_analysis_samples_janacol_retrained`, tag `_janacol_retrained`; chain log
  `janacol_logs/chain_janacol_retrained.log`, 18 scans audited OK): 240 μμ 0.678 (0.659), ee 0.805
  (0.783), ℓℓ 0.523 (0.504); 365 μμ 1.777 (1.729), ee 1.889 (1.839), ℓℓ 1.307 (1.260) — identical to
  the original-model reproduction within 0.002 (valid AUC 0.9575 vs 0.9560 at 240 μμ). The definition
  of the variable is irrelevant when training and application agree; the paper's 1–1.5% loss at 365
  comes only from the train/apply mismatch.
- **Hadronic BDT with the duplicated |θ(W₁)| input** (`ZQQ_BDT_VARIANT=bugw`: `PAPER/zqq_bdt_variant.py`,
  training `training_bugw/`, models `models_variants/bugw/`, `PAPER/rescore_qq.py`, stage dirs
  `BDT_analysis_samples_bugw`, stage2 on condor (clusters 494/495), tags `_bugw`): valid log-loss
  0.2429 / 0.2990 vs 0.2415 / 0.2975 (July); above-WP fraction 0.1326 → 0.1317 (240), 0.3340 → 0.3306
  (365). Fits: 240 qq 0.405 (0.312), ZH 0.319 (0.266); 365 qq 0.516 (0.433), ZH 0.485 (0.411) vs
  0.404 (0.311) / 0.318 (0.265) / 0.513 (0.432) / 0.482 (0.409): **≤ 0.6%, not the cause.** (Folded
  θ ∈ [0, π/2] used for both inputs since the ntuples only store |cos θ|; the loss of the W₂ direction
  is reproduced exactly.)
- **Fit observable / binning / cuts of Jan's hadronic fit** (Fisher on the `_oldbdt` ntuples,
  `cutbased_logs/15_hadronic_binning/`; the SDCC binning reproduces combine to 0.001): his 1 × 1 GeV
  recoil × m_jj histogram (m_jj 40–140, recoil 100–150 / 100–200) gives 240 0.393 (0.308) [SDCC 0.404
  (0.311), paper 0.38 (0.30)] and 365 0.492 (0.415) [0.514 (0.433), paper 0.56 (0.47)]; his 0.70
  working point at 240 (code; text says 0.75) and the 365 `p_jj > 60` cut change nothing. Finer
  binning closes half of the 240 gap and widens the 365 one.
- **Bin-by-bin MC-statistics terms** (combinetf `--binByBinStat`, an option of the paper's fitter):
  Fisher with Barlow-Beeston-lite variances on Jan's binning gives 365 **0.579 (0.498)** — within 0.03
  of the paper's 0.56 (0.47) — but 240 1.396 (1.110): the MC variance is 98% the Z/γ*→qq sample,
  which at 240 has 10 M processed events (weight 59 per event) vs 56 M (1.3) at 365; even with infinite
  Z→qq statistics the 240 value stays at 0.452 (0.357) > paper 0.38 (0.30). So the two energies of the
  paper's hadronic column are compatible with different fit configurations (240: fine binning, no
  MC-stat; 365: with MC-stat, or a weaker BDT than ours); only Jan's fit outputs can settle it.
- **Table 3 with the paper-like BDTs (2026-10-02; `janacol_logs/20_bias_*`, `22_bias_*`)**: bias tests
  at 240 GeV with Jan's acolinearity application (μμ, ee, ℓℓ: tag `_oldbdt_janacol`), the
  duplicated-W hadronic BDT (qq: `_bugw`) and their combination (`run_240_all_paperlike`, 0.319
  (0.266)) change the biases by ≤ 0.015: max |Δ to paper| μμ 0.043 (was 0.040), ee 0.016 (0.026),
  ℓℓ 0.023 (0.025), qq 0.067 (0.062), all 0.052 (0.061) — the BDT variants are not the origin of
  the Table-3 residuals. **The H→μμ entries are explained by the H→ℓℓ candidate removal of Jan's
  histmaker** (lepton pairs with |m − 125| < 3 GeV are dropped before the Z pairing; absent from the
  SDCC stage1): his histmaker run on the eight `wzp6_ee_*H_Hmumu_ecm240` samples
  (`jan_histmaker/output_240hmumu`, `logs/hmumu_removal_240.txt`; the SDCC-chain variant inside it
  reproduces the SDCC stage2 yields exactly, 16.35 events) gives 2.4% fewer H→μμ events in the μμ
  channel (hi-BDT −1.0%, lo-BDT −4.4%; Z(ττ)H −41%, Z(bb)H −13%, Z(μμ)H −1.5%). With his H→μμ
  per-decay templates in `signal_by_decay.root` (run dirs `*_oldbdt_janacol_hllrm`) the bias test
  gives **μμ +0.094% (paper +0.09; was +0.133)** and **ℓℓ +0.042% (paper +0.04; was +0.063)**.
  The remaining hadronic residuals (H→ZZ, γγ, inv: 0.05–0.07) would need Jan's own BDT and binning.
- **Fitter (combinetf run on SDCC, 2026-10-02; `storage/ZH_XSec_Paper/combinetf/`, `RESULTS.md`,
  wrapper `run_combinetf.sh`)**: the paper's numbers come from combinetf (`text2hdf5.py` +
  `combinetf.py -t 0 --expectSignal=1`, Hessian uncertainties; `--freezeBackgrounds` = stat-only).
  Installed here as CMSSW_10_6_19_patch2 + bendavid/HiggsAnalysis-CombinedLimit `tensorflowfit`
  (HEAD 4529e97) in the cvmfs cc7 container. On our cards (paper-like variants: only the 1% lnN /
  no background nuisance) its Hessian equals the combine scans **within 0.001 for all 16 cards at
  both energies** (`-t -1` = `-t 0`; combinetf scan = minos = Hessian for the norm cards): 240 μμ
  0.679 (0.660), ee 0.809 (0.787), ℓℓ 0.525 (0.506), qq 0.404 (0.311), all 0.318 (0.265); 365 μμ
  1.795 (1.752), ee 1.916 (1.861), ℓℓ 1.322 (1.276), qq 0.514 (0.433), all 0.482 (0.409); cut-based
  identical to combine too. The fitter is therefore not a source of any difference, and it does not
  remove the 365 leptonic normalisation component (0.39 / 0.46 / 0.35 in quadrature vs ≤ 0.2–0.3
  allowed by the paper's rounding). With `--binByBinStat`: qq 365 0.610 (0.522), qq 240 1.487
  (1.196), all 365 0.567 (0.490), all 240 0.557 (0.523), leptonic +9–18% — every channel moves away
  from the paper except qq 365, whose 0.56 (0.47) lies between the two; our Z→qq 240 template has an
  MC weight of 59, so the option's effect in the paper depends on Jan's sample sizes. Shape
  nuisances (`full` cards) agree to ≤ 0.013; the 365 cut-based qq `full` card is the asymmetric
  case (−1.80 / +1.42; Hessian 1.416 vs half-width 1.564).

Cut-based recipe (both energies, as run on 2026-09-30; `RC=<repo>/run_combine.sh`,
`STORE=/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper`, key4hep env for the `makeWS` steps;
leptonic chain `$STORE/scripts_oldbdt/lep_cutbased_chain.sh <e>`, logs `$STORE/cutbased_logs/`;
`<e>` = 240 | 365, `EXCL=""` at 240 and `EXCL="--exclude p8_ee_tt_ecm365"` at 365):

```bash
cd analysis/ZH_XSec/Paper/S<e>/combine
for fl in mumu ee; do
  python3 makeWS_recoil_2cat.py $fl --single-region --input-base $STORE/S<e>/$fl/BDT_analysis_samples_cernbdt/syst --tag _oldbdt_cutbased
  RUNDIR_SUFFIX=_oldbdt_cutbased $RC ./run_fit_leptonic.sh $fl recoil
done
RUNDIR_SUFFIX=_oldbdt_cutbased $RC ./run_fit_combination.sh ll recoil
python3 makeWS_2D_qq.py --recoil-only --input-base $STORE/S<e>/qq/BDT_analysis_samples_oldbdt/syst --tag _oldbdt_cutbased $EXCL
QQ_RUNDIR_SUFFIX=_oldbdt_cutbased $RC ./run_fit_qq.sh 2d
$RC python3 bias_test_generic.py qq --tag _oldbdt_cutbased    # mechanics check of the one-bin card only (Table 3 is MVA-based)
RUNDIR_SUFFIX=_oldbdt_cutbased QQ_RUNDIR_SUFFIX=_oldbdt_cutbased $RC ./run_fit_combination.sh all recoil   # -> run_<e>_all_oldbdt_cutbased
cd <repo>
python3 analysis/ZH_XSec/Paper/table2_paper_layout.py --suffix _oldbdt --cut-suffix _oldbdt_cutbased --label 'original models' \
    --out documents/zh_xsec_table2_paper_layout_2026-09_oldbdt.md --tex documents/zh_xsec_table2_paper_layout_2026-09_oldbdt.tex
```

What the builders do and the closure checks they report (the single region holds exactly the
events of the two-region fit):
- Leptonic (`makeWS_recoil_2cat.py --single-region`, category `noBDT`): every template is the sum
  of the loBDT and hiBDT stage2 histograms; lo + hi = `sel_Baseline_wide` (the baseline selection
  without the BDT condition) is checked per process and bin for the nominal and the four varied
  selections — max relative bin difference 3.45e-16 over 99 (240) / 100 (365) processes, standalone
  check 2.2e-16 on 14 / 15 processes (`01_closure_standalone.log`); one-bin card derived from
  `datacard_recoil_2cat_<fl>.txt` under the same name; per-decay templates `noBDT_sig_<h>` with
  Σ_h sig_h = fit signal (residual +0.0000%; k = 0.99771 / 0.99525 / 0.99724 / 0.99615 for 240 μμ /
  ee / 365 μμ / ee); the default two-region build is bit-identical after the patch (24 + 22 + 206
  histograms, card and stdout; `00_bitcheck_*`). Yields (signal / background, S/B): 240 μμ 55 674 /
  1 345 405 (0.041), ee 52 072 / 2 173 760 (0.024); 365 μμ 7 073 / 86 643 (0.082), ee 6 477 / 64 118
  (0.101).
- Hadronic (`makeWS_2D_qq.py --recoil-only`, category `nomva`): one region = stage2
  `sel_Baseline_nomva`, observable = the m_recoil projection of the TH2 `mrecoil_mjj` (25 × 2 GeV
  over 100–150 at 240, 20 × 4 GeV over 100–180 at 365), the same 87 ZH signal sets,
  `bkg_WW/ZZ/Zqq/rare` with 1% lnN, shapes JETSCALE / SQRTS / BES (shape-only), one-bin derivation of
  `datacard_2d_qq.txt`; closure proj(hi) + proj(lo) = proj(nomva) to 6.0e-16 for the 55 / 60
  (process, variation) pairs checked (`02_closure_stage2_*`), end-to-end `nomva` templates vs the
  projection of the existing 2D templates ≤ 8.4e-16 (BES up to 8e-4 by construction: clipping and
  rescaling in 2D vs 1D, integrals identical; `03_closure_templates_*`), unit tests PASS, the default
  2D build bit-identical (24 / 22 / 74 histograms); binning cross-check 0.5 / 1 / 2 GeV at 240:
  1.401 / 1.406 / 1.414 (stat 0.676 / 0.676 / 0.677), 365 (0.5 / 1 / 4 GeV): 1.404 / 1.405 / 1.415
  (0.623 / 0.624 / 0.624). Yields: 240 signal 1 491 605 / background 138 137 143 (S/B 0.011), 365
  199 143 / 1 610 635 (0.124). Bias test on the one-bin card (mechanics only): largest 240 H→inv
  +0.47, H→γγ +0.41; 365 H→ττ −0.45.
- Combination: `combineCards.py` of the three one-bin cards (bins mumu / ee / qq, 10 nuisances BES,
  ELSCALE, JETSCALE, MUSCALE, SQRTS, `norm_WW/ZZ/Zll/Zqq/rare`), 200-point scans, audit OK, no
  combine warnings (`11_all_S{240,365}_oldbdt_cutbased.log`, ~20 s each).
- All 30 scans (10 run dirs × 3) audited OK: minima at r = 0.9998–1.0005, min 2ΔNLL ≤ 0.0025, both
  crossings inside the ranges, no grid gaps; no WARNING / error line in any fit log.

Pointers: run dirs `S{240,365}/combine/run_recoil_2cat_{mumu,ee,combined}_oldbdt_cutbased`,
`run_2D_mrecoil_mjj_qq_oldbdt_cutbased` (one-bin `datacard_2d_qq.txt`, `templates_recoil.root`,
`bias_H*/`), `run_{240,365}_all_oldbdt_cutbased`; logs, diagnostics and the archived builder
patches in `$STORE/cutbased_logs/` (`makeWS_recoil_2cat_single_region_S*.diff`,
`diffs/makeWS_2D_qq_S*.diff`, `diffs/run_fit_qq_S*.diff`); `collect_results.py --suffix
_oldbdt_cutbased` (Cut-based paper columns implied by the suffix) gives the collector view of the
same run dirs.

### Table 3 — model-independence bias at 240 GeV (bias = r_fit − (1+X) in % of σ_ZH; reproduction (paper); original models, `--br sample`)

| H decay | Z(μμ)H, X = 5% | Z(ee)H, X = 5% | Z(ℓℓ)H, X = 5% | Z(qq)H, X = 1% | Combination, X = 1% |
|---|---|---|---|---|---|
| bb | −0.02 (−0.01) | −0.01 (+0.00) | −0.01 (−0.01) | +0.05 (+0.04) | +0.03 (+0.02) |
| cc | −0.01 (+0.00) | −0.03 (−0.02) | −0.02 (−0.01) | −0.06 (−0.08) | −0.04 (−0.06) |
| ss | −0.01 (−0.01) | −0.04 (−0.01) | −0.02 (−0.01) | −0.14 (−0.17) | −0.09 (−0.12) |
| gg | −0.00 (+0.00) | −0.04 (−0.03) | −0.02 (−0.01) | −0.03 (−0.04) | −0.02 (−0.03) |
| μμ | +0.13 (+0.09) | −0.02 (−0.01) | +0.07 (+0.04) | +0.22 (+0.26) | +0.14 (+0.18) |
| ττ | −0.00 (−0.01) | −0.02 (−0.01) | −0.01 (−0.01) | −0.06 (−0.04) | −0.04 (−0.03) |
| ZZ | +0.34 (+0.34) | +0.33 (+0.33) | +0.34 (+0.33) | −0.04 (+0.02) | −0.00 (+0.03) |
| WW | −0.00 (−0.01) | −0.03 (−0.03) | −0.01 (−0.02) | −0.10 (−0.07) | −0.06 (−0.05) |
| Zγ | +0.36 (+0.36) | +0.33 (+0.32) | +0.34 (+0.32) | −0.18 (−0.17) | −0.09 (−0.09) |
| γγ | −0.00 (+0.00) | −0.02 (−0.01) | −0.01 (+0.00) | +0.37 (+0.43) | +0.23 (+0.28) |
| inv | +0.01 (+0.01) | −0.01 (+0.01) | −0.00 (+0.01) | +0.45 (+0.51) | +0.28 (+0.34) |

Every entry is within 0.07% of the paper (leptonic and ℓℓ within 0.04%). The pattern is the
paper's: the dominant modes are unbiased; H→ZZ / H→Zγ in the leptonic channels (up to +0.36%
at X = 5%) and H→γγ / H→inv in the hadronic channel (up to +0.45% at X = 1%) are shifted by
at most the order of the respective total uncertainty. The residuals (μμ H→μμ +0.13 vs +0.09,
ee cc / gg −0.03 / −0.04 vs −0.02 / −0.03) persist within 0.01% with the retrained models and with
the `--signal exclusive` template construction, i.e. they come from the template / fit
implementation, not from the BDT. With the SM BR table instead (`--br table`) the H→ss entries
come out ≈ −0.2% (BR-table convention artifact: 0.00025 vs the sample fraction 0.000239);
those runs are preserved as `bias_test_brtable.log` / `bias_brtable_<H>/` in the live
`run_recoil_2cat_{mumu,ee}` dirs. 3-decimal values, the 365 columns and the per-run sources:
`documents/zh_xsec_results_2026-09_oldbdt.md`.

365 GeV (no paper column): Z(qq)H largest biases H→ττ −0.41, H→μμ −0.36, H→γγ −0.31,
H→inv −0.27 (all within 1 σ of the 0.51% total; every other mode |bias| ≤ 0.19); combination
H→ττ −0.36, H→μμ −0.32, H→γγ −0.27, H→inv −0.24; Z(ℓℓ)H H→Zγ +0.32, H→ZZ +0.08 (μμ +0.33 /
+0.08, ee +0.32 / +0.08); every other ℓℓ entry |bias| ≤ 0.04 (μμ: H→μμ +0.07; ee: all ≤ 0.02).

### JES / JER (hadronic, paper §5.3)

Method: 1% JES (both jets scaled by k = 1 ± 0.01, m_jj / p_jj / m_recoil recomputed — exact on
the jet pair) and 1% JER (each jet momentum smeared, p′ = p (1 + 0.01 g), deterministic
g ~ N(0,1) drawn from a 64-bit hash of `--seed` and the event's stored kinematics; Down =
bin-wise mirror of Up) are derived from the stored stage1 ntuple quantities by
`PAPER/qq_jesjer_templates.py` (`S{ecm}/qq/stage2_jesjer_templates.py --input-dir <stage dir>
--ncpu 8 --check`; the self-check refills the nominal stage2 histograms bit-exactly) and
profiled as shape nuisances on the signal and every background component of the hadronic
card (`datacard_2d_qq_jesjer.txt`; `makeWS_2D_qq.py --jesjer` / `--jes-only` / `--jer-only`;
run dirs `*_oldbdt_jesjer`, `_jes`, `_jer`). The BDT score is not recomputed under JES/JER
(JETSCALE convention, no hiBDT/loBDT migration). Result — degradation of the `xsec` precision
(every regular nuisance profiled, i.e. the column beyond the paper's quoted total):
240 GeV hadronic JES +0.43%, JER +0.32%, both +0.96% (0.404 → 0.408), combination +0.67%
(0.318 → 0.321); 365 GeV hadronic JES +0.06%, JER +0.31%, both +0.40% (0.513 → 0.515),
combination +0.35% (0.482 → 0.484). The paper's §5.3 quotes +3.9% / +3.2% (240 GeV, hadronic)
from an unprofiled evaluation. Profiled, the Asimov templates constrain JES to ±0.0011 and JER
to ±0.0048 (units of the unit prior; Fisher-information estimates 0.0010 / 0.0045 agree)
through the m_jj / m_recoil shape response of the 132M loBDT + 6.7M hiBDT events (about
−1.3 GeV in the recoil and +0.9 GeV in m_jj per 1% JES), so a profiled nuisance cannot
reproduce the paper's figures by construction. Unprofiled-style scratch estimates give the
paper's order of magnitude: with the model templates replaced by the shifted ones (no
nuisance) the precision changes by +1.8% / −1.4% (JES up / down) and +1.6% / +0.9% (JER up /
down); shifted pseudo-data fitted with the nominal model bias r by −2.7% / −1.3% (JES, signal
only shifted) and ∓1.3% (JER). The remaining gap is plausibly the BDT score not being
recomputed here and the paper's full-object smearing. Caveat: a ~1% relative degradation of a
0.404% precision is at the level of interval-method differences (grid-scan crossing +0.96%,
parabola fit +0.95%, Hesse singles −0.30%, robustFit singles +2.41%); the drivers' profile grid
scan is the convention of every column, so read the fifth column as "JES/JER add ~(0.5–1)%
relative". Tables: `documents/zh_xsec_table2_2026-09_oldbdt.md` / `.tex` (`table2_full.py`),
`storage/ZH_XSec_Paper/jesjer_logs/05_jesjer_summary_oldbdt.md` (`jesjer_summary.py`).

### Findings and caveats

1. The BES nuisance built from the dedicated ±1% samples carries a mostly one-sided
   MC-statistics normalization offset of a few per mille (up to ~0.5%: the leptonic recoil
   templates shift by −0.37% to +0.48%, Up and Down mostly in the same direction, e.g. S365 ee
   hiBDT +0.38% / +0.48%; ~96% of the ≈0.25% BES effect in S365 ee is this offset, measured on
   the retrained-model fit as 1.910% → 1.895% with a symmetrized BES; the hadronic pre-scaling
   shifts printed by `makeWS_2D_qq.py` range from +0.05% to −0.36%, seven of the eight negative). Inherited from the original analysis: the hadronic card rescales the BES
   templates to the nominal integral (shape-only; `--bes-keep-norm` = raw), the leptonic cards
   do not (paper-faithful).
2. The 1% BES samples exist for **all** Z decays (`wzp6_ee_{z}H_BES-{higher,lower}-1pc`,
   produced 2026-09-07); the old run-book statement that none existed for the hadronic Z
   decays was wrong for the September state (Systematics table corrected). The hadronic
   BES templates carry essentially no shape information (the BES-higher / lower inclusive
   samples are statistically indistinguishable in m_recoil × m_jj), so the nuisance costs
   nothing in the hadronic fit; JETSCALE at 1e-5 is a placeholder (see Systematics).
3. ROOT 6.28's jitted `RBDT<>` reader rounds the tree thresholds to 6 digits: ~0.1% of the
   events shift by up to 1e-2 in BDT score with respect to xgboost — the same for the original
   models; not a defect.
4. Zero-selection stage1 chunks are tree-less (TParameters only) and break `fccanalysis
   final`; repaired with `condor/patch_empty_chunks.py` (leptonic: 202 chunks over the four
   channels; hadronic: 7 at 240 (nunuH_Hinv) + 151 at 365 (the dileptonic / nunuH processes,
   as in July); training S365/ee γγ→ee: 9). Run `condor/check_chunks.py` after every fan-out.
5. The JES/JER templates inherit the one-sided stage1 m_jj / p_jj windows (events outside
   them cannot migrate in) and no BDT recomputation: not what a re-simulation would give.
6. The bias-test residuals of Table 3 (item above) survive both model sets and the
   `--signal exclusive` construction (`_excl` run dirs under `storage/ZH_XSec_Paper/fits_cernbdt/`).
7. Nothing is committed to git (2026-09-30, after the cut-based work: 41 modified + 32 untracked
   files under `analysis/ZH_XSec/Paper/` and `documents/`, the new ones being
   `table2_paper_layout.py` and the two paper-layout documents; the working tree also carries
   unrelated BIB / EventProducer changes).

### Reproducibility recipe (original models, from the stage dirs onward)

Prerequisites: key4hep env for everything but the fits and bias tests (`RC=<repo>/run_combine.sh`
for those); `STORE=/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper`; `$STORE/models/`
identical to `models_backup_2026-09-29/` (compare with its `MD5SUMS.txt`). Commands from
`analysis/ZH_XSec/Paper/` unless stated; `<e>` = 240 | 365, `<fl>` = mumu | ee. After **every**
condor fan-out, before stage2:
`python3 condor/check_chunks.py --ecm <e> --flavor <fl|qq> --stage <STAGE> --jobs 8 --json <log>.json`,
then `python3 condor/patch_empty_chunks.py --ecm <e> --flavor <fl|qq> --stage <STAGE> --only <process> --apply`
for each NO_TREE process (one `--only` glob per call) and re-check until `RESULT : PASS`.

1. **Leptonic stage1** — the 87 exclusive ZH sets scored with the original models:
   `FCC_MODELS_BASE=$STORE/models_backup_2026-09-29 python3 condor/submit_stage1.py $STORE/scripts_cernbdt/S<e>/<fl>/stage1_analysis_ntuples.py --stage BDT_analysis_samples_cernbdt --stage-override`
   (config copy listing only the exclusive sets; the inclusive / BES / mH signal and the
   background chunks are symlinks to `BDT_analysis_samples.jul2026`, scored with the same
   models). Equivalent from scratch with the restored live models: `python3 condor/submit_stage1.py S<e>/<fl>/stage1_analysis_ntuples.py`
   (full list, 494 / 507 / 488 / 481 jobs for S240 μμ / ee, S365 μμ / ee) into `BDT_analysis_samples`.
2. **Leptonic stage2**: `fccanalysis final $STORE/scripts_cernbdt/S<e>/<fl>/stage2_histograms_syst.py`
   (the live `S<e>/<fl>/stage2_histograms_syst.py` with the stage dir renamed) →
   `$STORE/S<e>/<fl>/BDT_analysis_samples_cernbdt/syst/`.
3. **Leptonic fits** (`cd S<e>/combine`; `$STORE/scripts_oldbdt/lep240_chain.sh`):
   `python3 makeWS_recoil_2cat.py <fl> --input-base $STORE/S<e>/<fl>/BDT_analysis_samples_cernbdt/syst --tag _oldbdt`;
   `RUNDIR_SUFFIX=_oldbdt $RC ./run_fit_leptonic.sh <fl> recoil`;
   `$RC python3 bias_test_generic.py <fl> --tag _oldbdt | tee run_recoil_2cat_<fl>_oldbdt/bias_test.log`.
4. **ℓℓ combination** (`ll_chain.sh`): `RUNDIR_SUFFIX=_oldbdt $RC ./run_fit_combination.sh ll recoil`;
   `$RC python3 bias_test_generic.py ll --tag _oldbdt | tee run_recoil_2cat_combined_oldbdt/bias_test.log`.
5. **Hadronic stage1** — the 24 inclusive / BES sets with the original model:
   `python3 condor/submit_stage1.py $STORE/scripts_oldbdt/S<e>/qq/stage1_analysis_ntuples.py --stage BDT_analysis_samples_oldbdt --stage-override`
   (240 / 238 jobs; the exclusive ZH sets and the backgrounds are symlinks to the July chunks,
   scored with the same model); check / patch as above. From scratch: the live
   `S<e>/qq/stage1_analysis_ntuples.py` (1105 / 1517 jobs) into `BDT_analysis_samples`.
6. **Hadronic stage2**: `fccanalysis final $STORE/scripts_oldbdt/S<e>/qq/stage2_histograms_syst_oldbdt.py`
   → `$STORE/S<e>/qq/BDT_analysis_samples_oldbdt/syst/`, then the closure check
   hiBDT + loBDT = nomva for every process and variation (inline in `qq_chain.sh`,
   `oldbdt_logs/07_validate_stage2_*.log`).
7. **Hadronic fits and full combination** (`qq_chain.sh <e>`; `SYST=$STORE/S<e>/qq/BDT_analysis_samples_oldbdt/syst`;
   `EXCL=""` at 240, `EXCL="--exclude p8_ee_tt_ecm365"` at 365):
   `python3 makeWS_2D_qq.py --input-base $SYST --tag _oldbdt $EXCL` (+ `--zh-other-as-bkg` for the July-definition cross-check);
   `QQ_RUNDIR_SUFFIX=_oldbdt $RC ./run_fit_qq.sh 2d` (and `2d-zhbkg`);
   `$RC python3 bias_test_generic.py qq --tag _oldbdt | tee run_2D_mrecoil_mjj_qq_oldbdt/bias_test.log`;
   `RUNDIR_SUFFIX=_oldbdt QQ_RUNDIR_SUFFIX=_oldbdt $RC ./run_fit_combination.sh all recoil`;
   `$RC python3 bias_test_generic.py all --tag _oldbdt | tee run_<e>_all_oldbdt/bias_test.log`.
8. **JES / JER** (`jesjer_logs/prod_templates.sh`, `run_jesjer_fits.sh <e>`):
   `python3 S<e>/qq/stage2_jesjer_templates.py --input-dir $STORE/S<e>/qq/BDT_analysis_samples_oldbdt --ncpu 8 --check`
   (writes the `jesup` / `jesdw` / `jerup` files into that stage dir's `syst/`); then for
   `<v>` = jesjer | jes | jer (`--jesjer` | `--jes-only` | `--jer-only`):
   `python3 makeWS_2D_qq.py --<opt> --input-base $SYST --tag _oldbdt_<v> $EXCL`;
   `QQ_RUNDIR_SUFFIX=_oldbdt_<v> $RC ./run_fit_qq.sh 2d`;
   `RUNDIR_SUFFIX=_oldbdt QQ_RUNDIR_SUFFIX=_oldbdt_<v> ALL_RUNDIR_SUFFIX=_oldbdt_<v> $RC ./run_fit_combination.sh all recoil`;
   `python3 audit_scans.py run_*_oldbdt_jes*`.
9. **Cut-based fits** (paper Table 2 'Cut-based': one recoil region per final state, hadronic
   recoil-only; `$STORE/scripts_oldbdt/lep_cutbased_chain.sh <e>` runs the leptonic part, logs in
   `$STORE/cutbased_logs/`; the full command list is in the paper-layout subsection above):
   `python3 makeWS_recoil_2cat.py <fl> --single-region --input-base $STORE/S<e>/<fl>/BDT_analysis_samples_cernbdt/syst --tag _oldbdt_cutbased`;
   `RUNDIR_SUFFIX=_oldbdt_cutbased $RC ./run_fit_leptonic.sh <fl> recoil`;
   `RUNDIR_SUFFIX=_oldbdt_cutbased $RC ./run_fit_combination.sh ll recoil`;
   `python3 makeWS_2D_qq.py --recoil-only --input-base $SYST --tag _oldbdt_cutbased $EXCL`;
   `QQ_RUNDIR_SUFFIX=_oldbdt_cutbased $RC ./run_fit_qq.sh 2d`;
   `RUNDIR_SUFFIX=_oldbdt_cutbased QQ_RUNDIR_SUFFIX=_oldbdt_cutbased $RC ./run_fit_combination.sh all recoil`
   (→ `run_<e>_all_oldbdt_cutbased`; no bias test needed, Table 3 is MVA-based).
10. **Tables** (either env, from the repo root): `python3 analysis/ZH_XSec/Paper/collect_results.py --suffix _oldbdt --out documents/zh_xsec_results_2026-09_oldbdt.md`;
   `python3 analysis/ZH_XSec/Paper/table2_full.py --suffix _oldbdt --label 'original models' --out documents/zh_xsec_table2_2026-09_oldbdt.md --tex documents/zh_xsec_table2_2026-09_oldbdt.tex`;
   `python3 analysis/ZH_XSec/Paper/table2_paper_layout.py --suffix _oldbdt --cut-suffix _oldbdt_cutbased --label 'original models' --out documents/zh_xsec_table2_paper_layout_2026-09_oldbdt.md --tex documents/zh_xsec_table2_paper_layout_2026-09_oldbdt.tex`;
   `python3 analysis/ZH_XSec/Paper/jesjer_summary.py --suffix _oldbdt`. The `--out` documents are regenerated from
   scratch on every run, so hand-written notes do not survive in them — this section is the
   place for notes; the documents carry the numbers and their sources.

### Where things are

- Documents: `documents/zh_xsec_table2_2026-09_oldbdt.md` / `.tex` (5-column Table 2 for both
  energies, quadrature decomposition, JES/JER degradations, freeze lists, sources —
  `table2_full.py`); `documents/zh_xsec_table2_paper_layout_2026-09_oldbdt.md` / `.tex` (Table 2
  in the paper's own layout, paper vs reproduction for all four columns incl. the cut-based
  fits, differences, every scan — `table2_paper_layout.py`); `documents/zh_xsec_results_2026-09_oldbdt.md`
  (Table 2 comparison in the paper definition, all five Table-3 columns at 240 plus the 365
  columns with 3 decimals, sources — `collect_results.py`); campaign log
  `storage/ZH_XSec_Paper/reproduce_2026-09-29.log`.
- Fit run dirs (`Paper/S{240,365}/combine/`): `run_recoil_2cat_{mumu,ee,combined}_oldbdt`,
  `run_2D_mrecoil_mjj_qq_oldbdt` (+ `_zhbkg_oldbdt`, `_oldbdt_jes`, `_oldbdt_jer`,
  `_oldbdt_jesjer`), `run_{240,365}_all_oldbdt` (+ `_jes`, `_jer`, `_jesjer`); cut-based
  (single region, 2026-09-30): `run_recoil_2cat_{mumu,ee,combined}_oldbdt_cutbased`,
  `run_2D_mrecoil_mjj_qq_oldbdt_cutbased`, `run_{240,365}_all_oldbdt_cutbased`; each holds
  `fit_summary.txt`, the three scans, the card and `bias_H*/` + `bias_test.log` (the S365
  `run_recoil_2cat_{mumu,ee}_oldbdt` bias logs are `storage/ZH_XSec_Paper/oldbdt_logs/04_bias_S365_*_oldbdt.log`).
  Retrained-model cross-check: the same names without suffix (S365 qq `_nott` = without tt̄);
  `_excl` = the exclusive-sum signal construction; `*.jul2026` = July 2026 (read-only).
- Stage dirs (`storage/ZH_XSec_Paper/S{ecm}/`): `{mumu,ee}/BDT_analysis_samples_cernbdt` (the
  87 exclusive sets scored with the original models + symlinks to the July chunks),
  `qq/BDT_analysis_samples_oldbdt` (the 24 inclusive / BES sets with the original model +
  symlinks to the July chunks; its `syst/` also holds the JES/JER templates);
  `BDT_analysis_samples` = the retrained-model production; `*.jul2026` = July.
- Models: `models/` (originals, live) = `models_backup_2026-09-29/`; `models_retrained_2026-09-29/`.
- Logs and driver scripts: `storage/ZH_XSec_Paper/{oldbdt_logs,jesjer_logs,cutbased_logs,nott365_logs,bias_identity_logs,scripts_oldbdt,scripts_cernbdt,fits_cernbdt}/`.
