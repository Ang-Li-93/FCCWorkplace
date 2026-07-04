# ZH cross-section analysis — SDCC runs

FCC-ee ZH cross-section measurement (recoil method) on the winter2023 fastsim samples,
ported from CERN lxplus to SDCC/BNL. Leptonic channels (Z→ee, Z→μμ) at √s = 240 and
365 GeV are complete end-to-end; the hadronic channel (Z→qq) is set up and waiting on
the pre-trained BDT model.

## Layout

```
Paper/
├── site_config.py            # site detection (sdcc/lxplus): BDT-model paths, output dirs
├── zqq_stage1_common.py      # shared selection graph for the hadronic (qq) channel
├── condor/submit_stage1.py   # SDCC HTCondor fan-out for any stage1 script
├── S240/ S365/               # per-energy: mumu/ ee/ qq/ combine/
│   ├── <flavor>/analysis_stage1_include_bdt_batch_analysis_samples.py   # stage1 ntuples + BDT + syst
│   ├── <flavor>/analysis_stage1_trained_final_analysis_samples_syst.py  # stage2 syst histograms
│   ├── qq/analysis_stage1_MVA_Ntuples_batch.py                          # qq BDT training trees
│   ├── qq/train_xgb.py                                                  # qq BDT training
│   └── combine/makeWS_BDT_binned.py, datacard_binned_{ee,mumu}.txt, fitAnalysis.py
├── functions_hadronic/       # reference copies of the jeyserma/FCCPhysics hadronic C++
└── models/convert_bdt.py     # RBDT format conversion utility
```

Storage (GPFS): `/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper/`
(`models/S{ecm}/{flavor}/` staged BDTs, `S{ecm}/{flavor}/BDT_analysis_samples/` ntuples + `syst/` histograms,
`S{ecm}/{flavor}/condor/` job wrappers/logs).

## Environments

| Step | Environment |
|---|---|
| stage1, stage2, makeWS | `source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2024-03-10` then `source FCCAnalyses-winter2023/setup.sh` |
| text2workspace / combine | `cd HiggsAnalysis/CombinedLimit && source env_standalone.sh` (CMS cvmfs toolchain, ROOT 6.30 — do **not** mix with key4hep) |

Custom C++ (leptonic `HiggsTools::*` incl. `coneIsolationTheta`, and all hadronic helpers)
is compiled into `FCCAnalyses-winter2023` (`analyzers/dataframe/{FCCAnalyses/HiggsTools.h,src/HiggsTools.cc}`).
Rebuild after edits: `cd FCCAnalyses-winter2023/build && cmake --build . --target install -j8`.

## Run book (leptonic, per channel)

1. **Stage1** (ntuples with BDTscore + systematics branches), fans out to condor
   (`accounting_group=group_usfcc`, xrootd input from eospublic, GPFS output):
   ```
   python condor/submit_stage1.py S240/mumu/analysis_stage1_include_bdt_batch_analysis_samples.py [--dry-run]
   ```
   Job counts: S240/mumu 321, S240/ee 334, S365/mumu 314, S365/ee 307 (~10 min wall on a hot queue).
   The wrapper exports `FCCANA_PROCESS=<process>` (used by the qq channel's MC-truth filters).

2. **Stage2** (BDT-score histograms for all selections incl. syst variations):
   ```
   fccanalysis final analysis/ZH_XSec/Paper/S240/mumu/analysis_stage1_trained_final_analysis_samples_syst.py
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
| **S240 ee+μμ** | **0.511%** | 0.505% | 0.079% |
| S365 μμ | 1.938% | 1.904% | 0.360% |
| S365 ee | 2.190% | 2.115% | 0.566% |
| **S365 ee+μμ** | **1.468%** | 1.412% | 0.402% |

Integrated luminosities: 10.8 ab⁻¹ (240), 3 ab⁻¹ (365).

## Systematics

| Nuisance | Source | Implementation |
|---|---|---|
| MUSCALE / ELSCALE | lepton momentum scale | ±1e-5 via `lepton_momentum_scale(±1e-5)`, Z/recoil/BDT recomputed (**down variation is −1e-5**; a legacy bug where both used +1e-5 was fixed 2026-07-04 and stage1 fully re-run) |
| SQRTS | √s knowledge | recoil rebuilt at √s ± 2 MeV |
| BES | beam energy spread | dedicated samples, ±1% (240); ±10pc variants used at 365 |
| bkg norm | background yield | free rateParam in the fit |

Conventions: all angular quantities are θ-based (isolation = `coneIsolationTheta(0.01, 0.5)` +
`sel_isol(0.25)`; acolinearity = |θ₁−θ₂|; no η anywhere in selections or BDT inputs).
The mH-shifted samples (±50/100 MeV) are for the mass measurement, not the xsec fit.

## Hadronic (Z→qq) channel — status

Ported from jeyserma/FCCPhysics `h_zh_hadronic.py` into this workflow
(shared graph `zqq_stage1_common.py`; helpers compiled into HiggsTools, including the
3-D `acolinearity_scalar`; θ-based lepton veto for orthogonality with ee/μμ; jet-scale
±1e-5 and √s ± 2 MeV systematics — winter2023 has no BES/mH samples for hadronic Z decays).
Sample mapping: `wzp6_ee_qq` replaces the missing `wz3p6_ee_{uu,dd,ss,cc,bb}`;
signals are the 8 Z-decay × 11 H-decay wzp6 sets; `p8_ee_tt` added at 365.

**Blocked on** the pre-trained BDT models `bdt_model_ecm{240,365}.root`
(MIT `/ceph/submit/data/group/fcc/ee/analyses/zh/hadronic/training/`, not publicly
reachable). Once obtained, stage to `storage/.../models/S{ecm}/qq/` and run:
treemaker smoke-test → full stage1 (`--stage MVA_ntuples` for training trees if
retraining instead: `train_xgb.py` reproduces the reference training) → stage2 → fit
(TH3 recoil × m_qq × BDT, `combine_xsec_hadronic.py` in the FCCPhysics reference).
Known upstream quirk kept for model compatibility: `W2_costheta` duplicates
`W1_costheta` (both `abs(W1.Theta())`, i.e. θ not cos θ) — fix only if retraining.
