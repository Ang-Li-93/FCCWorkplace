# H → bs (FCNC) analysis — Z(μμ)H at FCC-ee

Search for flavour-changing neutral-current Higgs decays (H→bs, H→bd, H→cu, H→sd)
in the Z(→μ⁺μ⁻)H recoil channel at √s = 240 GeV, FCC-ee winter2023 IDEA fast simulation,
normalised to 10.8 ab⁻¹.

The analysis selects a Z→μμ candidate, clusters the rest of the event into exactly two
Durham jets, runs the 7-class ParticleNet flavour tagger
(`fccee_flavtagging_edm4hep_wc`, the `wc_pt_7classes_12_04_2023` model with u/d tags)
on them, and trains an 8-class XGBoost BDT to separate H→bs from the other FCNC modes,
the SM Higgs decays, and the non-Higgs backgrounds.

## Multiclass BDT labels

| Class | Content |
|-------|---------|
| 0 | H→bs (signal) |
| 1 | H→uu |
| 2 | H→dd |
| 3 | H→cu |
| 4 | H→sd |
| 5 | H→bd |
| 6 | SM Higgs decays (bb, cc, ss, gg, WW, ZZ(noInv), ττ, Zγ) |
| 7 | non-Higgs SM backgrounds (ZZ, WW, Z/γ→μμ, e±γ→eZ(μμ), γγ→μμ) |

## Environment

The winter2023 samples require the **key4hep 2024-03-10 stack** with the
pre-edm4hep1 FCCAnalyses. Newer stacks (2026-xx) silently mis-read
`MCParticleData::momentum` from winter2023 files (edm4hep 1.x schema change) —
do **not** run this analysis on the latest stack.

- **On SDCC (this repo):** `source setup_hbs.sh` from the repo root. It loads the
  2024-03-10 stack, builds/activates `FCCAnalyses-winter2023/`, and activates the
  `local_env_winter2023/` venv (xgboost, uproot, seaborn, …).
- **On lxplus:** `source /cvmfs/sw.hsf.org/key4hep/setup.sh -r 2024-03-10`, then set up
  a pre-edm4hep1 FCCAnalyses build, plus a venv with `xgboost`, `uproot`, `joblib`,
  `seaborn`, `matplotlib` for the training scripts.
- **Combine (step 9 only):** neither key4hep nor FCCAnalyses ship Combine. Use the
  CMS `combine-standalone` container through the `run_combine.sh` wrapper at the repo
  root: it picks the image unpacked on cvmfs
  (`/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/cms-cloud/combine-standalone:latest`,
  Combine 10.2.1 — works on SDCC and lxplus) or, failing that, the FCCSW `.sif` on
  `/eos`. No environment to source; the wrapper works from any shell, including the
  `setup_hbs.sh` one. See [documents/COMBINE.md](../../../documents/COMBINE.md).

## Paths to configure

All I/O paths are centralised in [userConfig.py](userConfig.py) via
`repo = "/eos/user/d/dduan/FCCee/Hbs/mumu"` — change `repo` to your own area.
The FCCAnalyses stage scripts additionally hardcode their own `outputDir` /
`outputDirEos` (and `stage1_include_bdt_*.py` hardcodes the BDT model path
`<repo>/BDT/xgb_bdt.root` inside a `gInterpreter.ProcessLine` block) — grep for
`/eos/user/d/dduan` and update every script you run.

Inputs:
- Official winter2023 samples are resolved from `prodTag = "FCCee/winter2023/IDEA/"`
  (streamed from `eospublic.cern.ch`; works from SDCC too).
- Custom FCNC signal samples (`wzp6_ee_mumuH_H{bs,bd,cu,sd}_W4p1MeV_ecm240`, plus
  Huu/Hdd) live in
  `/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/HiggsFCNC/`
  (world-readable via `root://eospublic.cern.ch/`).
- The flavour-tagger ONNX model auto-downloads from `fccsw.web.cern.ch` into the
  working directory on first run.

## Pipeline

Run everything from `analysis/Hbs/mumu/`. Steps 1, 2 and 6 submit HTCondor jobs
(`runBatch = True`, lxplus flavours/groups) — for local tests see the smoke-test
section below.

**1. Stage 1 ntuples — official samples** (backgrounds + diagonal Higgs decays):
```bash
fccanalysis run analysis_stage1_batch.py
```
Muon selection (p > 20 GeV, isolated, opposite charge), 2-jet exclusive clustering with
muons removed, 7-flavour tagging, Z/recoil/MET/d_merge observables → flat ntuples in
`<repo>/batch_5/<sample>/chunk*.root`. No Z-window cuts are applied at this stage
(they are applied later, at step 7).

**2. Stage 1 ntuples — custom FCNC samples:**
```bash
fccanalysis run analysis_stage1_outsideData.py
```
Same observables, reading the HiggsFCNC EOS area via `inputDir` (these samples use the
new-style `Muon_objIdx` branch links, hence the separate script).

**3. Build training dataset:**
```bash
python process_sig_bkg_samples_for_multi.py
```
Reads all modes in `userConfig.mode_names` from `loc.TRAIN`, assigns the 8 class
labels, balances classes by cross-section (FCNC modes kept equal), writes a pickle to
`loc.PKL`.

**4. Train the multiclass BDT:**
```bash
python train_multi.py
```
XGBoost on `userConfig.train_vars` (54 variables). Saves
`loc.BDT/xgb_bdt.joblib` and a TMVA-compatible `loc.BDT/xgb_bdt.root`.

**5. Evaluate the training:**
```bash
python multi_evaluation.py
```
ROC curves, confusion matrix, per-class score distributions (overtraining check),
feature importance → `loc.PLOTS`.

**6. Re-run stage 1 with BDT scores attached:**
```bash
fccanalysis run stage1_include_bdt_batch_samples.py       # official samples
fccanalysis run stage1_include_bdt_batch_outside_data.py  # FCNC samples
```
Evaluates `xgb_bdt.root` inline via `TMVA::Experimental::RBDT`, adding
`BDTscore_class0..7` and normalised probabilities → `<repo>/BDT_analysis_samples/`.

**7. Final selections + histograms:**
```bash
fccanalysis final analysis_stage1_trained_final_analysis_samples.py
```
Two selections — `No_Cuts` and `sel_Baseline_no_costhetamiss`
(86 < m_μμ < 96, 120 < m_recoil < 140, 20 < p_μμ < 70 GeV) — scaled to 10.8 ab⁻¹
→ `<repo>/Histo_Files/`.

**8. Stacked plots:**
```bash
fccanalysis plots analysis_stage1_trained_plot_analysis_samples.py
```
All kinematic, tagging and BDT-score variables, lin/log × stack/nostack
→ `<repo>/Final_Plots/`.

**9. Datacards + expected limits (Combine):**
```bash
# from the repo root; both scripts locate their inputs/outputs relative to themselves
./run_combine.sh python3 analysis/Hbs/mumu/combine/make_datacards.py   # -> combine/cards/<scenario>/{shapes.root,datacard.txt}
./run_combine.sh python3 analysis/Hbs/mumu/combine/run_fits.py         # text2workspace + limits + significance, all scenarios (~4 min)
```
`make_datacards.py` reads the step-7 histograms from `analysis/Hbs/mumu/Histo_Files/`
(the local SDCC copies are sufficient) and writes one card per one-rare-vs-all-SM scenario (Hbs, Huu,
Hdd, Hcu, Hsd, Hbd): a 20-bin shape fit of the renormalised score
`norm_prob{i} = P(rare_i) / (P(rare_i) + P(SM))` at `sel_Baseline_no_costhetamiss`,
scaled to 10.8 ab⁻¹. The SM Higgs decays are merged into a single `ZH` process, the
non-Higgs backgrounds stay separate, with a 0.5% lumi `lnN` and `autoMCStats`.
`data_obs` is the SM-only Asimov sum, so every fit is blind by construction.

`run_fits.py` runs, per scenario, `text2workspace.py`, the expected 68% and 95% CL
upper limits on the signal strength `r`, and a fixed-point search for the `r` that
gives 3σ / 5σ expected significance, then prints a BR table. `r` is relative to the
placeholder generator cross-section stored in the histo files (0.01 pb for the FCNC
modes, 1 pb for Huu/Hdd), so BR = r × σ_placeholder / σ(ee→μμH) with
σ(ee→μμH) = 0.0067643 pb; the conversion factor is written in the header of each
`datacard.txt`.

To run a single scenario by hand, open a shell inside the container (the working
directory is preserved and the datacard's shape path is relative, so `cd` into the card):
```bash
./run_combine.sh bash
cd analysis/Hbs/mumu/combine/cards/Hbs
text2workspace.py datacard.txt -o workspace.root
combine -M AsymptoticLimits workspace.root --cl 0.95 --rAbsAcc 1e-8 --rRelAcc 0.002 -n _cl0.95
combine -M Significance     workspace.root -t -1 --expectSignal 1e-3
```

Combine gotchas (both already handled in `run_fits.py`):
- The `r` limits are ~10⁻⁴, far below Combine's default `--rAbsAcc 5e-4`. Without
  `--rAbsAcc 1e-8 --rRelAcc 0.002`, `AsymptoticLimits` returns the same `r` for every
  `--cl` and skips the expected band.
- Do **not** add `-t -1` to `AsymptoticLimits`: `data_obs` is already Asimov, and with
  `-t -1` only the "observed" entry is written to the `limit` tree (no quantiles).

All outputs under `cards/` are git-ignored. Provisional expected results (July 2026,
merged-exclusive ZH background): BR(H→bs), BR(H→bd) < 6×10⁻⁴ at 95% CL, 5σ at
≈1.6×10⁻³; H→uu/dd ≈ 3×10⁻³ at 95% CL. The SM-Higgs background is meant to be replaced
by the true inclusive `wzp6_ee_mumuH_ecm240` histogram once it is produced — swap the
`SM_HIGGS` list in `make_datacards.py` for that single process.

**Auxiliary scripts** (plain python, read stage-1 / BDT ntuples with uproot):
- [visualize.py](../../../visualize.py) (repo root) — normalised shape overlays of every
  branch for all samples.
- [correlation.py](correlation.py) — input-variable correlation matrix on the signal.
- [Jet_Checks/](Jet_Checks/) — standalone m(bb) Whizard-vs-Pythia6 cross-check (own README).
- `process_sig_bkg_samples_for_xgb.py` / `train_xgb.py` / `evaluation.py` — legacy
  binary (Hbs-vs-rest) BDT chain, superseded by the multiclass chain above.
- [combine/](combine/) — datacard builder + fit runner for the rare-decay limits
  (step 9 above; runs inside the Combine container via `run_combine.sh`).

## Local smoke tests (no condor, no /eos)

`--files-list` + an absolute `--output` bypass the processList/condor machinery and the
EOS output paths (harmless `mkdir /eos` warnings will be printed). Verified on SDCC:

```bash
source setup_hbs.sh
cd analysis/Hbs/mumu

# official-format sample (local copy of an official winter2023 file):
fccanalysis run analysis_stage1_batch.py \
  --files-list Jet_Checks/samples/wzp6_ee_mumuH_Hbb_ecm240/events_008395310.root \
  --output /tmp/smoke_stage1_Hbb.root --nevents 1000

# FCNC signal streamed from CERN eospublic:
fccanalysis run analysis_stage1_outsideData.py \
  --files-list root://eospublic.cern.ch//eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/HiggsFCNC/wzp6_ee_mumuH_Hbs_W4p1MeV_ecm240/events_032096179.root \
  --output /tmp/smoke_stage1_Hbs.root --nevents 500
```

Expected: ~92–94% of events pass the muon preselection; on H→bb/bs the output shows
m_μμ ≈ 91, m_recoil ≈ 125–129, btag_max ≈ 0.95; on H→bs additionally `is_Hbs == 1`
and stag_other ≈ 0.5.

The plots stage (step 8) can be run on SDCC against the local histogram copies in
`analysis/Hbs/mumu/Histo_Files/` by pointing `inputDir`/`outdir` there. Note the local
copies (July 2026) predate the addition of inclusive `wzp6_ee_mumuH_ecm240` to the
plot config — comment out its `'mumuH'` entry in `plots['ZH']['backgrounds']` or
re-copy the histograms from EOS.

## Known quirks

- `analysis_stage1_batch.py` had `jet1_charge`/`jet2_charge` in the output branch list
  while their `Define`s are commented out (crash at Snapshot). Fixed by commenting the
  branches out too — keep the two lists in sync if jet charge is reinstated.
- Steps 3–5 need the full `batch_5` stage-1 ntuples; they cannot run without access to
  the producing user's EOS area (or a re-run of steps 1–2 into your own area).
- `stage1_include_bdt_*.py` load `xgb_bdt.root` at import time — they fail immediately
  (JIT error) if the model path does not exist.
- The `--Mode`/`--Folds` arguments of `process_sig_bkg_samples_for_multi.py` are
  vestigial; the mode list actually comes from `userConfig.mode_names`.
