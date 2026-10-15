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

## 8. LCC V106.2 IPC study — CONCLUDED (2026-07-20)

The LCC IPC study is closed. Approach settled on two tracks (the first LCC
attempt used the GHC-era MDI and disagreed 3–12× — the fix was to match **both
lattice and MDI version**, see the MDI-version incident notes):

- **Track A — the deliverable (central-sample conversion).** The mdi_v2 CAD
  central production is reused directly (no re-simulation; sensor geometry/material
  identical, only readout pitch differs, invisible to Geant4). All **19,673**
  central BXs converted (394-job campaign, 0 failures) and re-segmented to the
  20 µm MAPS grid. Deliverables `outputs/BIB/pixesl_ipc_LCC_V106p2_central{,_extended}.csv`.
  Headline (recomputed from the CSV 2026-07-20, over all 19,673 BXs):
  17,141 raw SIM hits = 13,849 unique pixels; **L3 (r=131 mm) 0.306 hits/BX**
  (1.1e-4 hits/cm²/BX), **L4 (r=315.5 mm) 0.565 hits/BX** (4.4e-5 hits/cm²/BX);
  per-cm² L3 is ~2.6× busier than L4 (raw totals L3 6,019 / L4 11,122 — L4 wins
  only via ~5× area + 2× z-extent). 8,240/19,673 BXs (42%) non-empty; mean 2.1
  hits per non-empty BX; max 112 in one BX. ~4×(L3)/~8×(L4) lower than GHC V24.4.
  Validated layer-by-layer vs A. Ilg FCC Week 2026 (avg firing cells/evt:
  L0 24.0, L1 7.8, L2 4.9, L3 0.31, L4 0.57 vs his ~24/7.5/4.7/0.30/0.45–0.50).
  Published to share `BIB_IPC_LCC/`.

- **Track B — the capability (our own mdi_v2 ddsim), VALIDATED.** Same GuineaPig
  crossings through our `MAPS_o1_v01_BIB_v2`, 400-BX batch. Ledger 377 clean /
  4 seed-retry / **19 deterministic hangs**. With matched 1 keV threshold the
  MAPS layers agree with central (L3 ×1.28 +1.8σ, L4 ×0.94) → absolute scale
  anchored; inner barrel keeps +9/+23/+34% (L0/L1/L2) from an unknown central
  config, common-mode for variant comparisons. This unlocks the LDRD endgame:
  radius/pitch detector variants now run on a trusted chain.

- **Upstream, still open:** `documents/BIB_MDI_V2_UPSTREAM_NOTE.md` (Geant4-hang
  reproducers + central sample ~4% short: 19,673 sim vs 20,501 GuineaPig inputs
  + request for exact central ddsim config) is **drafted, for Ang to send** to
  A. Ciarma / J. Eysermans / A. Ilg.

**Group-update slides:** `documents/BIB_LCC_SLIDES_TEXT.md` (11-slide source, same
convention as the GHC `BIB_IPC_SLIDES_TEXT.md`) + a ready-to-present HTML deck with
the plots embedded (`scratchpad/lcc_bib_update.html`, published as a Claude artifact
2026-07-20). LCC plots: `outputs/BIB/{plots_LCC,bibstudies_LCC}/`.

**Next:** variant scan (Track B) · PixESL readout on the stream · physics⊕BIB
overlay with Z→qq · send the MDI note · other sources (SR, beam-gas) as needed.

## 9. Follow-up to the 4 Aug 2026 review: axes, L4 vs L3, truth ntuple (2026-10-05)

Two review comments on the LCC deck — "do the Y axes make sense?" and "why is layer 4
above layer 3, is it low-pT loopers?" — plus a request for ROOT files for event displays.
Slide source with all numbers: `documents/BIB_LCC_FOLLOWUP_SLIDES_TEXT.md`.

**Truth ntuple (the tool for everything below).** `analysis/make_bib_truth_ntuple.py` reads
the central EDM4hep files with uproot (no geometry load; 100 condor slices of about a minute
each; runner + submit file in `MAPS_storage/BIB_derived/truth/IPC_LCC_V106p2_central/condor/`),
`analysis/merge_bib_truth_ntuple.py` merges them into flat ROOT files one level up, in
`MAPS_storage/BIB_derived/truth/IPC_LCC_V106p2_central/`:
`ipc_LCC_V106p2_central_truth.root` (whole tracker, 2,745,527 hits),
`..._truth_vertex.root` (`--dets 0,1`, 117 MB) and `..._truth_primaries.root` (all primaries
above 1 MeV pT). Trees `hits` (hit + linked MC particle + primary ancestor + barcode +
20 µm pixel address), `particles`, `bx`. Plots and tables: `analysis/plot_bib_truth.py` →
`outputs/BIB/plots_LCC_truth/` (+ `summary_numbers.md`); event displays:
`analysis/bib_event_display.py` (uproot + matplotlib only); bib-studies histograms with
correct axis titles: `analysis/redraw_bibstudies_labelled.py` → `outputs/BIB/bibstudies_LCC_labelled/`.
Published at share `BIB_IPC_LCC/truth_ntuple/` (staging: `fcc_maps_wrapper_pixesl/results/bib_ipc_lcc_truth/`).

**What a hit is in the central sample** (read from the DD4hep v01-36 source and confirmed on
the files; the full ddsim configuration is in the `runs` tree of every central file):
one Geant4 track during one stay in one sensor; position = midpoint of first and last stored
step; momentum = mean of the momenta there (half the entry value for a stopping track);
steps below 1 keV are dropped *before* the hit is built (`filter.tracker = edep1kev` acts per
step: no hit below 1 keV, charge 10–20% low for e± below 100 MeV, and a track re-entering a
sensor can be merged into one hit, 6–11% of vertex-barrel hits); secondaries created below
1 MeV are not stored — a hit made by one has quality bit 30 set and links to its nearest
stored ancestor. `--part.keepAllParticles` alone has **no effect** with
`Geant4TCUserParticleHandler`; full truth needs `SIM.part.userParticleHandler = ""` (or
`minimalKineticEnergy = 0`).

**Axes.** bib-studies "occupancy [%]" = fired pixels ÷ number of sensors (cellIDs carry
pixel indices, the dictionary counts sensors) — not an occupancy. The x–y / r–z map colours
are hits per map cell of an edge-on projection, not densities. `sensor_size_map` of our
`MAPS_o1_v01_DetectorDimensions.json` is thickness × length (wrong by 128× / 372×; unused by
drawhits). The rateDensity plots carry 52 MHz × 3 × 5 (21× the simulated rate at 37.04 MHz).

**L4 > L3.** Real (0.565 vs 0.306 hits/BX, 20σ) and not loopers. Field + geometry: pT > 39 MeV
(L3) / 95 MeV (L4) to arrive from the beam line; 0.024 / 0.0036 primaries per BX do, confirmed
particle by particle (91% / 86%). 65% (L3) and 94% (L4) of the hits are sub-MeV electrons
released in the silicon by X-rays and soft photons from showers of the forward pairs in the
beam pipe / MDI (plus a late part returning from the outer detector); per cm² they fall only
×0.61 from L3 to L4 (charged-particle hits ×0.07) and L4 has 4.43× the silicon. A pT cut of
1 MeV on the hit-making track gives L3 0.103 vs L4 0.028; a charge threshold does not change
the order. Loopers are 23% of L3 and 3.6% of L4 hits.

**Quoting rules (replace the LCC ones of July):**
- label "LCC V106.2 IPC @ Z, central mdi_v2 sim, SimTrackerHits, 1 keV simulation cut" — not "no threshold";
- hits ≠ fired pixels: 0.306 / 0.565 hits are 0.259 / 0.445 fired 20 µm pixels per BX; the
  duplicates are 1.6 keV silicon Auger electrons next to a photo-electron (not step splitting);
- per area use the sensitive silicon: 2,710.5 cm² (L3), 12,020.7 cm² (L4) → 1.13e-4 and
  4.70e-5 hits/cm²/BX, 4.2 and 1.7 kHz/cm² at 37.04 MHz;
- PixESL CSV addresses run 0–930 × 0–990 inclusive (half-width edge pixels), not [0,930)×[0,990);
- 9% (L3) / 13% (L4) of the hits are later than one bunch spacing and sit in their original BX;
- the Ilg FCC Week 2026 chart is hits with a 1.8 keV threshold on the first 2,129 BX
  (reproduced exactly): 24.00 / 7.55 / 4.65 / 0.279 / 0.390.

**Open:** dependence of the soft-photon component on sensitive thickness, Auger setting and
the beam-pipe CAD model (needs a full-truth re-simulation without the step cut); decide how
PixESL should treat duplicate-pixel rows, edge addresses, merged hits and late hits.
The central steering sets `SIM.filter.tracker` twice (`edep0`, then the template default
`edep1kev`, which wins), so the 1 keV per-step cut is probably unintended; and our July
"central-matched" test (`maps_central_steer.py`: FTFP_BERT, default range cut) was not
matched — the real central config is our BIB recipe with `edep1kev` and
`keepAllParticles = False`. With the per-step cut 8–11% of the central L0–L2 hits are merged
re-entries (each hiding at least one crossing), which our `edep0` chain keeps separate; this
probably explains part of the inner-barrel excess of our chain. A rerun of the 400-BX
validation with the verbatim central steering would settle it. Both points are in the
addendum of `BIB_MDI_V2_UPSTREAM_NOTE.md` (for Ang to send).

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
