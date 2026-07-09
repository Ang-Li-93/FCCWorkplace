# MAPS particle-gun samples

**Single-particle gun → PixESL hit streams on the BNL_MAPS detector** — clean,
truth-labeled input for the **AI tracking studies** of the LDRD *"Integrated
AI-Enabled Tracking Demonstrator for FCC-ee"* (WP1), complementing the physics
(`wzp6 qq`) and beam-background (BIB) samples documented in
[MAPS_PIXESL.md](MAPS_PIXESL.md) and [BIB_STUDIES.md](BIB_STUDIES.md).

```
ddsim particle gun (BNL_MAPS)  →  decode cellID  →  PixESL CSV  (1 event = 1 BX)
```

Built and validated 2026-07-08 (chain smoke-tested end-to-end; scripts
adversarially reviewed against the installed DD4hep 1.36 source).

---

## 1. What the samples are

- **Detector:** `k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01.xml` —
  the standard-beampipe variant (same geometry as the qq production; the CAD
  MDI beampipe is only needed for BIB, and costs ~80 s load + stuck-track
  retries). MAPS = VTXOB layers 3 & 4, 20 µm pitch, 50 µm sensitive Si.
- **Steering:** `fcc_maps_wrapper_pixesl/simulation/maps_gun_steer.py` — same
  physics as the qq signal sim (FTFP_BERT, 1 keV tracker threshold, weighted
  tracker action) so gun CSVs are directly comparable, but **no crossing-angle
  boost and no vertex smearing**: point source at (0,0,0), t = 0, so `h_time`
  is pure time-of-flight (L3 r=130 mm → 0.44 ns, L4 r=315 mm → 1.05 ns at 90°).
- **Default kinematics:** 1 µ⁻ per event, θ ∈ [45°, 135°] sampled **flat in θ**
  (see §4), full φ. In that window every track from the origin crosses BOTH
  MAPS layers (barrel edge angles: L3 atan(130/163)=38.6°, L4
  atan(315/326)=44.0°), so hits/event ≈ 1 per layer and **BX doubles as the
  truth track label** — every hit in a BX belongs to that BX's single muon
  (plus its own delta rays). Layer 4 misses ~5 % of tracks (real φ gaps in the
  sensor coverage).
- **Output format:** identical to the qq/BIB deliverables — strict CSV
  `BX,COL,ROW,h_time,qin` (+ `_extended.csv` with
  `layer,module,sensor,r_mm,z_mm`, row-aligned), COL/ROW = per-sensor local
  addresses in [0,930)×[0,990) (fixed offsets 465/495), h_time in **ps**, qin
  in **electrons**. The EDM4hep sim ROOT files are kept, so full MC truth
  (SimTrackerHit→MCParticle links, exact crossing points, true momenta) is
  always recoverable.

## 2. Samples produced

| sample | events | config | location |
|---|---|---|---|
| `mu-_p20GeVto70GeV` | 1 000 | µ⁻, p flat 20–70 GeV, θ 45–135°, seed 42 (local run) | `outputs/gun/mu-_p20GeVto70GeV/` |
| `mu-_p20GeVto70GeV_th45-135_s1000_n10000` | 10 000 | µ⁻, p flat 20–70 GeV, θ 45–135°, seeds 1000–1039 (condor, 40×250) | CSVs: `outputs/gun/<sample>/`, chunks+ROOT: `MAPS_storage/gun_derived/<sample>/` |

QA of the 1k sample: 2 198 MAPS hits (L3 1 145 / L4 1 053), 999/1000 BXs with
≥1 hit; p verified flat (5 GeV bins); qin median ≈ 4.5 ke⁻ with a clean MIP
Landau (q10 ≈ 3 k, q90 ≈ 9 k); h_time starts exactly at the TOF floor (L3
436 ps, L4 1052 ps) with a small late tail from delta rays.

QA of the 10k sample (cluster 770584, harvested 2026-07-08, 40/40 chunks):
**21 115 hits** (L3 10 885 / L4 10 230), 9 977/10 000 BXs with ≥1 hit; BX
range exactly [0, 9999] with zero out-of-range (chunk offsets verified);
p flat in [20, 70] GeV and θ flat in [45°, 135°] (10-bin checks, all within
~±5 %); qin median 4 490/4 484 e⁻ (L3/L4), h_time floors 435/1052 ps = TOF.
**Seed independence proven at scale: all 10 000 primary (p, θ) tuples are
unique** — no event replay across the 40 chunk seeds. Dominant topology:
exactly 1 hit/layer (8 345 BXs with 2 hits); 928 single-hit BXs (mostly L4
φ-gap misses); delta-ray tail up to 69 hits/BX.

Every output directory contains a `gun_config.json` provenance sidecar with
the exact configuration that produced the sim file.

## 3. How to run

```bash
# local, end-to-end (ddsim + conversion), all knobs are GUN_* env vars:
bash fcc_maps_wrapper_pixesl/simulation/run_particle_gun.sh 500          # p=10 GeV mu-
GUN_PMIN='20*GeV' GUN_PMAX='70*GeV' \
  bash fcc_maps_wrapper_pixesl/simulation/run_particle_gun.sh 1000       # flat spectrum

# condor production (10k default; dry-run first, then --submit):
bash fcc_maps_wrapper_pixesl/simulation/submit_gun_condor.sh
bash fcc_maps_wrapper_pixesl/simulation/submit_gun_condor.sh --submit
# when drained: merge chunks -> one CSV pair (+ completeness check):
SAMPLE=mu-_p20GeVto70GeV_th45-135_s1000_n10000 bash fcc_maps_wrapper_pixesl/simulation/harvest_gun.sh
```

Knobs (see script headers for the full list): `GUN_PARTICLE`, `GUN_P`
(fixed |p|) **or** `GUN_PMIN`+`GUN_PMAX` (flat |p|; setting only one is an
error), `GUN_THETA_MIN/MAX`, `GUN_PHI_MIN/MAX`, `GUN_MULT`, `GUN_SEED`,
`GUN_BXOFF`. Condor: `NEVENTS` (multiple of `NPER`), `NPER`, `SEEDBASE`,
`PARTICLE`, `PMIN/PMAX`, `SAMPLE`, `OUTDIR`.

Resume/failure handling: chunks are self-contained and per-step resumable —
a fully complete chunk is a **no-op** on resubmit (delivered files never
touched; `GUN_RECONVERT=1` forces reconversion), a chunk with a sim but
missing/partial CSVs reruns only the conversion, **atomically** (scratch
subdir + mv, metadata last = harvest's done marker). Re-running `--submit`
after failures therefore only redoes missing work; the harvest writes
`missing_chunks.txt` and exits nonzero while chunks are missing. The full
config is locked into `OUTDIR/production_config.txt` on first submit — a
later submit with ANY different knob (incl. `NPER`, which would remap BX
windows) is refused; new config ⇒ new `SAMPLE`.

## 4. Verified ddsim gun semantics (do not re-learn these)

Adversarially verified against the pinned stack (key4hep 2026-04-08,
DD4hep 1.36) — source-level AND empirically:

- **`--gun.energy` is a fixed MOMENTUM magnitude |p|** — not kinetic energy,
  not total energy (the DDG4 property doc says "Fixed momentum value";
  `Geant4ParticleGun` sets `momentumMin=momentumMax=energy`; a 1 GeV "energy"
  proton comes out with |p| = 1.000 GeV, E_kin = 0.433 GeV). Even ddsim's own
  `--help` ("total energy") is wrong. Our knob is therefore named `GUN_P`, and
  `GUN_ENERGY` errors out.
- **A non-None `gun.energy` silently OVERRIDES `momentumMin/Max`** — the
  steering must not set it; the runner passes exactly one mode.
- **`--gun.distribution "uniform"` is flat in θ**, NOT isotropic
  (`Geant4IsotropeGenerator`: `theta = min + (max-min)*rnd`). Flat-in-θ =
  uniform incidence-angle coverage, which is what we want for response/tracking
  studies; sample-averaged quantities carry a 1/sinθ weighting relative to
  isotropic. For true isotropic use `--gun.distribution "cos(theta)"`.
- **Seeding:** `--random.seed` on the CLI SIGSEGVs ddsim (long-standing
  production lesson) → the seed comes from the `GUN_SEED` env var read inside
  the steering. With `enableEventSeed`, per-event RNG derives from
  (seed, event#), so **the same seed exactly replays the same events**
  (verified: seed-42 runs reproduce byte-identical kinematics). Hence:
  - chunk *i* of a condor production uses `SEEDBASE + i` (all distinct);
  - **never reuse a seed range already spent on another sample of the same
    config** (the 10k production uses `SEEDBASE=1000` because seed 42 already
    produced the 1k sample). Verified: seeds 1000/1001/42 produce fully
    disjoint kinematics.

## 5. BX bookkeeping (chunked production)

Each ddsim job numbers events from 0, so chunk CSVs are shifted with
`GUN_BXOFF = chunk × NPER` before merging: chunk *i* owns BX
[i·NPER, (i+1)·NPER) — disjoint, gap-free, and after the merge each BX still
holds exactly one muon (the truth-label property). This mirrors the qq
convention (`--bx-offset chunk*NPER`) and the BIB per-BX ids — and exists
because an unused-offset bug (all BX = 0) was one of the original BIB audit
findings.

## 6. For the AI tracking studies

- Hit-to-track truth in the CSV = group by BX (single-particle samples).
- Precise truth (crossing positions, momenta, per-hit particle for
  delta-ray discrimination) → read the chunk EDM4hep files; an opt-in truth
  column in the converter is a small extension if needed.
- Harder setups when ready: `GUN_MULT=N` (N muons/BX, combinatorics), the qq
  sample (realistic topology), BIB CSVs (background overlay) — all share the
  same format and pixel frame, so they can be mixed per-BX.
