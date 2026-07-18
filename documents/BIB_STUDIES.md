# Beam-Induced Background (BIB) for the MAPS/PixESL study

Explainer + run book for the BIB work package of WP1 (FCC-ee pixel hit streams
for the PixESL readout simulation). Companion to
[MAPS_PIXESL.md](MAPS_PIXESL.md), which documents the physics (Z→qq) chain.

## 1. What BIB is and why it drives the MAPS design

At FCC-ee the collider itself creates particles unrelated to the e+e- → Z
physics — **beam-induced background**. For a MAPS vertex detector this is *the*
design driver: BIB arrives **every bunch crossing** (every ~20–30 ns at the Z
pole), while physics events are comparatively rare. Detector occupancy, pixel
readout bandwidth, and the PixESL readout architecture are stressed by BIB,
not by physics.

The five BIB sources (as documented in the per-source READMEs shipped with the
datasets, see §3):

| Source | Mechanism | Format | Crossing-angle boost? | Key caveat |
|---|---|---|---|---|
| **IPC** (incoherent pair creation) | Bunch EM fields at collision radiate photons that convert to e+e- pairs — O(1000)/BX, low energy, spiral in the solenoid into the innermost layers. Generator: **GuineaPig++** | `.pairs`, 1 file = 1 BX | **Yes** (0.015 rad) | GuineaPig has no solenoid field: pre-2026 files need vertices reset to (0,0,0) (`bib-studies/simulation/set_vertex_000.py`) |
| **RB** (radiative Bhabha) | e+e- scatter radiating a hard photon (generator BBBREM); off-energy particles lost downstream | text `.out` (x y z px/p py/p p) | already lab/beam frame | Not ddsim-readable directly — needs conversion. Normalize with the BBBREM cross-section in `bbbrem.log` |
| **SR** (synchrotron radiation) | Photons radiated in the final bends, entering from ±2.2 m | `.hepevt` | no | One file = one *huge* "event" (Z-mode 5-min-lifetime: 1.5M photons) representing a beam condition, not one BX |
| **Beam-gas** | Coulomb scattering off residual gas; losses on the SR collimators ~5.3 m from the IP shower into the detector (Xsuite tracking) | `.hepevt` | **No** (explicitly) | Scale with quoted ⟨rate⟩ at MDI = 17.9 GHz |
| **Injection** | Top-up injection losses (imperfect injection + scraped halo) on collimators 400–700 m away | `.hepevt` | no | Several variants (injbeam 12% loss, 1% halo, "8 m dump" corrections) |

For the MAPS/VTXOB layers, **IPC dominates**; SR and beam-gas are the usual
second-order checks.

## 2. GHC vs LCC — two competing accelerator designs

The dataset tree is organized **lattice design → lattice version → BIB
source**. GHC and LCC are two independent designs of the FCC-ee optics
(chromaticity-correction schemes) still in competition:

- **GHC** — Global Hybrid Correction (K. Oide)
- **LCC** — Local Chromatic Correction (P. Raimondi)

They produce different beam distributions at the IP and different loss maps,
hence different BIB. The MDI group's **blessed reference versions** (from the
top-level EOS README, 2026):

| BIB source | Reference dataset |
|---|---|
| SR | `GHC/V23` |
| IPC, beam-gas, RB | `GHC/V24.4` |
| Injection | `GHC/V25.1` |
| (LCC) | no blessed reference yet |

**Our plan: baseline on GHC, keep LCC as comparison.**
1. Validate on the reference `GHC/V24.4/IPC/Z` — these are the samples the
   official ALLEGRO/IDEA occupancy plots use, so our numbers are directly
   comparable (cross-check before trusting PixESL CSVs).
2. High-stats production / systematics on `LCC/V106.2/IPC/Z` when useful: it is
   the newest and largest set (20,501 BXs vs ~4,000; vertices already fixed at
   generation, no `set_vertex_000` step).
3. A GHC-vs-LCC occupancy comparison in the MAPS layers is itself a useful
   deliverable — the lattice choice is an open machine question and PixESL
   readout numbers for both feed into it.

## 3. The local data mirror

The full MDI BIB tree is mirrored on SDCC gpfs (copied 2026-07-04, 157,063
files / 253 GB, byte-size verified):

```
/gpfs/mnt/gpfs01/usfcc/MAPS_storage/BIB/          # = /eos/project/f/fcc-ee-mdi/BIB/
├── GHC/{V23, V24.4, V25.1, V25.2, V25.3-4}
│     e.g. V24.4/IPC/Z/dataN/pairs.pairs          # ~4,000 BXs, ~1,350 pairs/BX
│          V24.4/{RB, beamgas}/..., V23/SR/*.hepevt
└── LCC/{V105, V106.2}
      e.g. V106.2/IPC/Z/output_N.pairs            # 20,501 BXs (2026 files, vertices OK)
           V106.2/{SR/{core,halo}, beamgas, collimation}
```

Each source directory carries its own `README`/`ReadMe.md`/`README.log` with
generation details and normalization — read it before using a sample.

Mirror machinery (kept for re-syncs when MDI publishes new versions):
`/gpfs/mnt/gpfs01/usfcc/MAPS_storage/BIB_mirror/{mirror_bib_job.sh,mirror_bib.sub}`
— a condor job doing parallel BFS enumeration of the EOS tree (16 `xrdfs`
workers) + 12 parallel `xrdcp` streams, size-checked and resumable
(`condor_submit mirror_bib.sub` re-syncs, copying only new/changed files).
Gotchas that cost time, don't rediscover them:
- No `/eos` mount at SDCC: access is `xrdcp`/`xrdfs` against
  `root://eosproject-f.cern.ch` (or `eospublic` for `/eos/experiment/fcc/...`)
  with the `lia@CERN.CH` Kerberos ticket.
- A naive `xrdcp --recursive` (or `xrdfs ls -R`) stalls for hours: serial WAN
  round-trips over ~157k entries. Parallelize the walk.
- Condor does not forward Kerberos: the job exports
  `KRB5CCNAME=FILE:/usatlas/u/ali3/krb5cc_101884` (ticket file on the shared
  home, visible to workers; a fresh `kinit` on the login node is picked up
  live by a running job).
- Use `accounting_group = group_usfcc` + `accounting_group_user = ali3`; a raw
  `+AccountingGroup = "group_usfcc"` (no user suffix) never matches.
- `.pairs` format (GuineaPig): one particle/line — energy (sign = charge),
  velocities βx βy βz, position x y z in **nanometers**, process labels.

## 4. The bib-studies code

Official detector-agnostic tooling: https://github.com/HEP-FCC/bib-studies
(cloned at `FCCWorkplace/bib-studies/`). Three pieces:

- **`simulation/`** — `submit_pairs.py` makes one condor job per `.pairs`
  file (per BX), each running `ddsim` → one EDM4hep file per BX (written for
  lxplus; needs the same SDCC adaptations as our qq production).
  `set_vertex_000.py` fixes pre-2026 IPC vertices. The README documents the
  **BIB simulation recipe** (see §5).
- **`plotting/`** — `xml2json.py` digests a compact XML into a detector
  dictionary (`detectors_dicts/*.json`: layer radii, areas, channel counts);
  `drawhits.py` reads EDM4hep with podio, decodes cellIDs via
  `python/{ALLEGRO,IDEA,CLD,ILD_FCCee}.py` and fills per-layer occupancy
  (e.g. `drawhits.py -s VertexBarrel`); `hits2highLevelEstimations.py` turns
  that into hits/cm²/BX and data rates.
- **`python/`** — shared cellID-decoding / geometry-lookup layer.

We reuse the *recipe* and the occupancy plots as cross-check; the hit → CSV
step stays our `convert_simhits_to_pixesl.py`.

## 5. BIB simulation recipe (differs from physics sim!)

Low-energy secondaries matter for BIB, so (per `bib-studies/simulation/README.md`):

- k4geo built with `-DINSTALL_BEAMPIPE_STL_FILES=ON`; swap the **CAD beampipe**
  (real engineered MDI shape) into the compact XML and set the **world volume
  to vacuum** (workaround: the CAD pipe contains air).
- Steering: `SIM.physics.list = "FTFP_BERT_EMZ"`, `SIM.physics.rangecut =
  0.05*mm`, `SIM.filter.tracker = "edep0"`, `--part.keepAllParticles True`,
  UI commands `/cuts/setLowEdge 50 eV`, `/process/em/lowestElectronEnergy 1 eV`,
  `/process/em/auger true`, `/process/em/deexcitationIgnoreCut true`.
- `SIM.crossingAngleBoost = 0.015` **for IPC/RB only** (not beam-gas!).
- No vertex smearing (BIB files carry their own vertices/timing).
- Our pinned 2026-04-08 stack's DD4hep 1.36 has `Geant4EventReaderGuineaPig`:
  ddsim reads `.pairs` directly (extension-triggered). `.hepevt` is likewise a
  native ddsim input.

## 6. Pipeline for MAPS/PixESL and status

```
BIB/GHC/V24.4/IPC/Z/dataN/pairs.pairs             (1 BX, local gpfs)
  → ddsim (BIB variant of MAPS_o1_v01 + maps_bib_steer.py)     [TO BUILD]
  → events_N.edm4hep.root (1 BX of SimTrackerHits)
  → convert_simhits_to_pixesl.py (VTXOB layers 3,4)            [reuse as-is]
  → PixESL CSV with BX = N  (+ drawhits.py occupancy cross-check)
```

vs the qq workflow: WHIZARD disappears (generator = pre-made pairs file) and
per-BX bookkeeping is trivial (1 file = 1 BX, no `--bx-offset`).

Status 2026-07-06: **IPC production COMPLETE — 3,996/3,996 BXs** (cluster
770575 + 32-BX sweep 770576). Deliverables in `outputs/BIB/`:
`pixesl_ipc_GHC_V24p4_Z.csv` (+`_extended`, row-aligned): 23,926 hits,
5.99 hits/BX on the MAPS layers (layer 3: 5,275, layer 4: 18,651 — the outer
layer dominates ~3.5:1); 2,909/3,996 BXs have ≥1 hit. CAD-beampipe stuck-track
aborts hit ~1% of BXs; 31/32 were transient (same seed passed on re-run), 1 BX
used the runner's automatic alternate-seed retry. Sweep mode for any future
gaps: `BXFILE=<missing_bx.txt> NBX=1 submit_bib_condor.sh --submit`.
Workflow: `simulation/{run_bib_chunk.sh,submit_bib_condor.sh,harvest_bib.sh}`,
mirror kept read-only (`chmod -R u-w`; restore `u+w` before re-syncing).
Workflow guarantees (from the 2026-07-05 multi-agent audit + fixes):
- CSV `BX` column = true bunch-crossing id (`--bx-offset`, was silently unused)
- one pixel frame for all BXs: fixed `--col-offset 465 --row-offset 495`
  (= half of 930×990 px/sensor), same local-address convention as the qq CSVs
- per-BX reproducible seed via `BIB_SEED` env (byte-identical re-run verified);
  `--random.seed` CLI segfaults, `--meta.runNumberOffset` does not seed
- atomic outputs (same-dir tmp+rename, strict csv finalized last = resume
  marker): per-step resume/resubmission is safe, duplicates can't corrupt
- submit: timestamped bx list per submission; refuses `--submit` while a
  previous cluster on the same OUTDIR is queued (`FORCE=1` overrides)
- ~27% of IPC BXs have zero MAPS hits → header-only CSVs (`--allow-empty`),
  counted as complete by the harvest coverage report
Remaining: SR / beam-gas / RB sources, and the GHC-vs-LCC comparison.

**BASELINE CHANGE 2026-07-09** (A. Ilg, via Ang): the baseline lattice is now
**LCC V106.2** — GHC results below are superseded/archival. LCC production:
cluster 770585, 20,501 BXs (`BIB/LCC/V106.2/IPC/Z`, flat `output_<id>.pairs`,
new GuineaPig with 2 T field at generation → **no vertex reset**; boost 0.015
still applies; ~15× fewer MAPS-layer hits/BX than GHC). Reference: A. Ilg,
*Vertex backgrounds*, FCC Week 2026 (boost applied, 2,129 BXs, key4hep
2026-04-08, BX rate 37.04 MHz, outer barrel ≈0.31 hits/BX per layer):
<https://indico.cern.ch/event/1552126/contributions/7128843/attachments/3290966/5884415/Vertex%20backgrounds_FCC%20Week%202026_Armin%20Ilg.pdf>
Outputs: `BIB_derived/sim/LCC_V106.2_IPC_Z/`, tag `ipc_LCC_V106p2_Z` (new
defaults in submit/harvest scripts; GHC re-runs need SRCDIR/OUTDIR/VTXRESET=1).

## 7. Validation vs official results (2026-07-07 audit)

The layer-4/layer-3 total-hit ratio (~3.5×) was independently audited (7-probe
multi-agent check: raw-file recounts with independent decoders, geometry/sensor
arithmetic, converter review, threshold/window scans, qq cross-check, sim
settings, official references). **Verdict: simulation physics, not a bug.**
Decomposition: 3.54 = (4.4–4.8× more silicon on L4) × (0.73–0.80× per-area
rate — per cm² L4 is ~25% *quieter* than L3). Prompt hits (h_time < 2 ns)
obey the solid-angle expectation (L4/L3 = 0.74); the excess is a late
(median 14 ns) population of 0.5–12 MeV looper/backsplash electrons leaving
3–31-hit strings, plus L4's double z-extent (52.6% of its hits at |z|>163 mm
where L3 has no silicon).

Layer-by-layer agreement with the official analysis (independent samples,
geometry files, and analyzer — A. Ilg, FCC Physics Workshop Jan 2026, "SIM
hits per layer", no threshold, 3,994 BX IPC@Z GHC):

| layer | official [hits/BX] | ours [hits/BX] |
|---|---|---|
| 0 | 34.3 | ~34 |
| 1 | 12.1 | ~12 |
| 2 | 8.0 | ~8 |
| 3 | 1.37 | 1.32 |
| 4 | 4.71 | 4.67 |

Reference talks:
- A. Ilg, *Studies of backgrounds in vertex detectors*, FCC Physics Workshop,
  28 Jan 2026 (the matching "SIM hits per layer" plot):
  <https://indico.cern.ch/event/1588696/contributions/6856981/attachments/3208537/5714124/Studies%20of%20backgrounds%20in%20vertex%20detectors_Armin%20Ilg.pdf>
- S. Franchellucci, A. Koulouris et al., *ALLEGRO rate and occupancy studies*,
  1st FCC TDAQ workshop, 6 Nov 2025 (slide 12: "IPC barrel occupancy
  inflation, maybe due to loopers!" — the same mechanism, flagged
  independently):
  <https://indico.cern.ch/event/1583755/contributions/6727403/attachments/3168257/5631576/FCC-TDAQ%20workshop%20ALLEGRO%20occupancy%20studies.pdf>
- A. Koulouris, *Detector occupancy studies*, FCC Physics Workshop, 29 Jan 2026:
  <https://indico.cern.ch/event/1636499/contributions/6897621/attachments/3205630/5708048/FCC%20physics%20workshop%20-%20Detector%20occupancy%20studies%20(1).pdf>
- A. Ilg, *Vertex backgrounds*, FCC Week 2026, 11 Jun 2026 (newest LCC v106.2
  lattice: L3=L4=0.31 hits/BX — the ratio is LATTICE-DEPENDENT):
  <https://indico.cern.ch/event/1552126/contributions/7128843/attachments/3290966/5884415/Vertex%20backgrounds_FCC%20Week%202026_Armin%20Ilg.pdf>
- J. Eysermans, *IPC background for LCC 25/50 ns*, MDI meeting #78, 4 May 2026
  (primaries-only counting — not comparable to raw SIM-hit totals):
  <https://indico.cern.ch/event/1679640/contributions/7066539/attachments/3267924/5836966/MDI78_GP_IPC_04052026.pdf>
- IDEA concept paper (vertex = same ARCADIA design): <https://arxiv.org/abs/2502.21223>

**Quoting rules (audit hygiene):**
- Always label results "**GHC V24.4 IPC@Z, raw SIM hits, no threshold**" —
  official numbers span ratio 1.0–3.4 depending on lattice and counting
  convention.
- Raw CSV rows overstate *fired-pixel* occupancy ~1.6× (Geant4 step-splitting,
  layer-symmetric): use the harvest's "fired px" line or
  `plot_readout_metrics.py --dedup-pixels` for absolute occupancy.
- BIB CSVs carry NO charge threshold (edep0) while the qq sample used 1 keV:
  use `--qin-min 278` for threshold-consistent comparisons (qin is in
  electrons, 3.6 eV per e-h pair).
- Divide per-BX rates by all 3,996 BXs (1,087 are empty and absent from the
  merged CSV); h_time tails reach ~2.2 µs, so quoted rates depend on the
  readout window.
