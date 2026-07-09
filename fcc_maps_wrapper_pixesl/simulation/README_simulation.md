# Simulation (ddsim on the BNL_MAPS detector)

Target: the MAPS layers = outer two vertex-barrel layers (VTXOB, layer ids 3,4;
20 µm pitch), collection `VertexBarrelCollection`, geometry
`k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01.xml`
(`MAPS_o1_v01_BIB.xml` = CAD-beampipe variant, BIB only).

Environment: `source setup_MAPS.sh` at the FCCWorkplace root (one-time
`--build-k4geo` first). All runners source it themselves; note it clobbers
generic shell vars (`OUTDIR`, `REPO_ROOT`, …), hence the prefixed variable
names in every script.

Three input modes, one steering file each (shared conventions: weighted
tracker action, EDM4hep output, seed via env var because `--random.seed` on
the CLI SIGSEGVs ddsim):

| mode | steering | filter | physics | runner |
|------|----------|--------|---------|--------|
| particle gun | `maps_gun_steer.py` | 1 keV | FTFP_BERT | `run_particle_gun.sh` (local) |
| qq physics (WHIZARD) | `maps_steer.py` | 1 keV | FTFP_BERT | `run_chunk.sh` + `submit_ddsim_condor.sh` + `harvest_pixesl.sh` |
| BIB (GuineaPig/hepevt) | `maps_bib_steer.py` | edep0 | FTFP_BERT_EMZ | `run_bib_chunk.sh` + `submit_bib_condor.sh` + `harvest_bib.sh` |

## 1. Particle gun (local, end-to-end to PixESL CSV)
```bash
bash simulation/run_particle_gun.sh 500                # 500 x p=10 GeV mu-
GUN_PARTICLE=pi- GUN_P='1*GeV'      bash simulation/run_particle_gun.sh 200
GUN_PMIN='20*GeV' GUN_PMAX='70*GeV' bash simulation/run_particle_gun.sh 1000
```
One command = ddsim gun + PixESL conversion. Defaults: single mu⁻, |p| = 10 GeV,
θ ∈ [45°, 135°] sampled **flat in θ** (uniform incidence-angle coverage, NOT
isotropic — that's what ddsim's `uniform` distribution means; every track
crosses both MAPS layers), full φ, point source at the origin (no boost, no
vertex smearing → `h_time` is pure TOF: ~0.43 ns L3, ~1.05 ns L4). 1 event =
1 CSV BX. Momentum knobs are true |p| (ddsim's `--gun.energy` is a misnamed
fixed |p| in DD4hep 1.36 — verified in source + empirically). Output under
`outputs/gun/<TAG>/` (git-ignored): sim ROOT + `gun_config.json` provenance +
strict/extended CSV + metadata, COL/ROW in the standard fixed frame
[0,930)×[0,990). All knobs are `GUN_*` env vars — see the header of
`run_particle_gun.sh`.

## 2. qq physics production (condor)
Self-contained jobs: WHIZARD (`wzp6_ee_qq_ecm91p2.sin`, qq-only — leptonic
channels FATAL in full sim) + ddsim per chunk; vertex smearing at ddsim level
(`SIM.vertexSigma`), crossing-angle boost 0.015. See `documents/` and the
script headers for the full run book.

## 3. BIB production (condor)
Per-BX jobs over the mirrored MDI samples
(`/gpfs/mnt/gpfs01/usfcc/MAPS_storage/BIB/`): vertex reset (pre-2026 files) +
ddsim on the CAD-beampipe geometry + conversion with `--bx-offset <bx>`.
Precision-EM recipe per HEP-FCC/bib-studies. See `run_bib_chunk.sh` header.

## Inspecting sim output
```bash
python simulation/check_sim_output.py <file.edm4hep.root>
```
lists collections, flags `SimTrackerHit` ones, prints first hits
(position mm, time ns, EDep GeV — the converter's default units).
