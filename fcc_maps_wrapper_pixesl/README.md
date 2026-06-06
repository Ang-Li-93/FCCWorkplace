# fcc_maps_wrapper_pixesl

**FCC-ee MAPS vertex → PixESL hit-stream workflow** — WP1 of the LDRD
*"Integrated AI-Enabled Tracking Demonstrator for FCC-ee."*

Goal: produce realistic FCC-ee pixel hit streams (for **PixESL/SystemC** readout
simulation) from a MAPS-instrumented ALLEGRO vertex detector. Generate
`e+e- → Z → q q̄` at the Z pole, full-simulate it (Geant4/ddsim), and convert the
`SimTrackerHit`s into the PixESL table:

```
BX,COL,ROW,h_time,qin
```

---

## 1. What this is (final design)

- **Sensor target:** the **2 outer barrel layers of the vertex detector (`VTXOB`,
  layer ids 3 & 4)** given a **20 × 20 µm² MAPS pixel pitch**, 50 µm sensitive Si.
  *(Not the silicon wrapper — that was the original idea; we moved to the outer
  vertex layers.)*
- **Detector:** `BNL_MAPS / MAPS_o1_v01` = `ALLEGRO_o1_v03` with **only the vertex
  include swapped** to a 20 µm variant. ALLEGRO/IDEA geometry kept pristine.
- **Generator:** WHIZARD + Pythia6 (`wzp6`), `e+e- → Z/γ* → q q̄` inclusive over
  u,d,s,c,b at √s = 91.2 GeV.
- **Readout:** the vertex barrel already has a real `CartesianGridXY` segmentation,
  so PixESL `COL/ROW` come from **decoding the cellID** (`layer,x,y`), not from
  position mapping.
- **Production:** self-contained, chunked **HTCondor** jobs on the SDCC pool
  (`group_usfcc`), each job = WHIZARD + ddsim for one chunk.

End-to-end chain:
```
WHIZARD (wzp6 qq @91.2)  →  ddsim (BNL_MAPS, 20 µm VTXOB)  →  decode cellID  →  PixESL CSV  →  PDF plots
```

---

## 2. Repository / data layout

```
fcc_maps_wrapper_pixesl/
  setup/        setup_key4hep.sh, check_environment.sh, clone_local_forks.sh
  geometry/     find/inspect ALLEGRO geometry; README_geometry.md
  generation/   WHIZARD card notes (the real cards live in FCC-config, see below)
  simulation/   maps_steer.py, run_chunk.sh, submit_ddsim_condor.sh,
                harvest_pixesl.sh, gen_whizard_chunks.sh (alt 2-step), check_sim_output.py
  conversion/   convert_simhits_to_pixesl.py, geometry_config.yaml, collections_config.yaml
  analysis/     summarize_pixesl_hits.py, plot_pixesl_hits.py
  outputs/      local scratch / logs

# top-level FCCWorkplace (this repo's parent), git submodules (SSH):
  ../setup_MAPS.sh                         # the one-shot environment entry point
  ../k4geo/                                # fork (Ang-Li-93/k4geo), holds BNL_MAPS geometry
  ../k4Reco/                               # fork (Ang-Li-93/k4Reco)
  ../FCC-config/winter2023/                # wzp6 cards incl. wzp6_ee_qq_ecm91p2.sin
  ../EventProducer/                        # (reference; SDCC-patched param_FCCee.py)

# BNL_MAPS geometry (in the k4geo fork):
  k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01.xml          # top-level detector
  k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/VertexComplete_o1_v01.xml # vertex w/ 20 µm VTXOB

# storage (SDCC gpfs, group usfcc):
  /gpfs/mnt/gpfs01/usfcc/MAPS_storage/generation/stdhep/.../wzp6_ee_qq_ecm91p2/
  /gpfs/mnt/gpfs01/usfcc/MAPS_storage/generation/edm4hep/.../wzp6_ee_qq_ecm91p2/
```

---

## 3. Environment

Reproducible setup = **fixed stable Key4hep release + locally-built k4geo fork**
(the fork's `VertexBarrel_detailed_o1_v03` plugin isn't in the stable lib, so k4geo
must be built and registered via `k4_local_repo`; the editable XML comes from the
source tree).

```bash
cd /gpfs/mnt/gpfs01/usfcc/ali3/FCCWorkplace

# one-time: pull the forks as submodules (needs GitHub SSH)
bash fcc_maps_wrapper_pixesl/setup/clone_local_forks.sh
git submodule update --init --recursive

# one-time: build k4geo (so its _o1_v03 plugins exist on the stable stack)
source setup_MAPS.sh --build-k4geo        # ~10-20 min

# every session:
source setup_MAPS.sh                       # stable release + k4geo build + editable XML + k4Reco
bash fcc_maps_wrapper_pixesl/setup/check_environment.sh
```
`setup_MAPS.sh` pins `KEY4HEP_RELEASE=2026-04-08`, builds/registers `k4geo`
(`K4GEO_DIR`), points `K4GEO` at the editable source XML (`LOCAL_K4GEO`), and
registers `k4Reco` (`K4RECO_DIR`).

---

## 4. Geometry — the 20 µm MAPS outer vertex

- `MAPS_o1_v01.xml` includes every ALLEGRO subdetector **in place** and swaps only
  the vertex → `VertexComplete_o1_v01.xml`.
- `VertexComplete_o1_v01.xml` = IDEA vertex with **`VTXOB_pitch_phi = VTXOB_pitch_z
  = 0.020 mm`** (was 50 × 150 µm ATLASPix3). To change the pitch, edit those two
  constants — pure XML, no rebuild.
- VTXOB layers: **layer 3 at r ≈ 130 mm** (half-length ≈ 163 mm), **layer 4 at
  r ≈ 315 mm** (half-length ≈ 326 mm). Inner vertex (layers 0–2 = `VTXIB`) is
  unchanged and dropped by the converter.
- cellID = `system:5,side:-2,layer:5,module:12,sensor:8,x:32:-16,y:-16`.

---

## 5. Run it (small / interactive)

```bash
source setup_MAPS.sh
ST=/gpfs/mnt/gpfs01/usfcc/MAPS_storage/generation/stdhep/winter2023/wzp6_ee_qq_ecm91p2/events_000000000.stdhep

# full sim (use the UNCOMPRESSED .stdhep; ddsim does NOT read .stdhep.gz)
ddsim --steeringFile fcc_maps_wrapper_pixesl/simulation/maps_steer.py \
      --compactFile k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01.xml \
      --inputFiles "$ST" --numberOfEvents 100 \
      --outputFile outputs/z_qq_MAPS.edm4hep.root

# convert -> PixESL CSV (decode cellID, keep VTXOB layers 3,4)
python fcc_maps_wrapper_pixesl/conversion/convert_simhits_to_pixesl.py \
      --input outputs/z_qq_MAPS.edm4hep.root --output outputs/pixesl.csv \
      --compact k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01.xml

# summary + PDF plots
python fcc_maps_wrapper_pixesl/analysis/summarize_pixesl_hits.py outputs/pixesl.csv
python fcc_maps_wrapper_pixesl/analysis/plot_pixesl_hits.py     outputs/pixesl.csv --outdir outputs/plots
```

Outputs: `pixesl.csv` (strict `BX,COL,ROW,h_time,qin`), `pixesl_extended.csv`
(`+layer,module,sensor,r_mm,z_mm`), `pixesl.metadata.json`, and PDF plots:
per-layer occupancy maps, `qin` (Landau), `h_time` (per-layer time-of-flight),
hits/event, r-z hit map, hits/layer.

---

## 6. Production (HTCondor, self-contained chunks)

Each job runs **WHIZARD (its own NPER events, own scratch) + ddsim** → one
`events_<i>.edm4hep.root`. No shared stdhep, no skip, no grid reuse.

```bash
source setup_MAPS.sh

# dry-run (writes the .sub, submits nothing)
bash fcc_maps_wrapper_pixesl/simulation/submit_ddsim_condor.sh

# canary, then full overnight run (200 jobs x 50 evt = 10k)
NEVENTS=100   NPER=50 bash fcc_maps_wrapper_pixesl/simulation/submit_ddsim_condor.sh --submit
NEVENTS=10000 NPER=50 bash fcc_maps_wrapper_pixesl/simulation/submit_ddsim_condor.sh --submit

condor_q                                   # monitor

# when done: merge all chunks -> one PixESL CSV (global BX) + summary + PDF plots
NPER=50 bash fcc_maps_wrapper_pixesl/simulation/harvest_pixesl.sh --plot
```
Tunables (env): `NEVENTS`, `NPER` (jobs = ⌈NEVENTS/NPER⌉), `ACCT_GROUP`
(`group_usfcc`), `REQUEST_MEMORY` (3 GB), `MAXRUNTIME`, `SEED_BASE`. Wall-clock ≈
total CPU (≈330 CPU-h for 10k) / parallel slots; keep `NPER` small for short jobs +
parallelism (each job ≈ 30 min integrate + NPER × ~2 min sim).

`should_transfer_files=NO` (gpfs is shared on workers); each job sources
`setup_MAPS.sh` itself.

---

## 7. Conversion details

- `geometry_config.yaml`: `target.mode = decode_cellid`, `keep_layers: [3,4]`,
  20 µm pitch, per-layer radii. A `barrel_position` fallback exists for collections
  without a segmentation.
- `--compact` is required for `decode_cellid` (builds the dd4hep bitfield decoder).
- `qin = EDep[eV] / 3.6` (electrons); `h_time = time[ns] × 1000` (ps); `BX = global
  event index` (`--bx-offset` for chunks). EDM4hep units: position mm, time ns,
  EDep GeV.

---

## 8. Results — 10k Z→qq sample (physics only)

Produced 10,000 events (200 condor jobs × 50) → **405,389 VTXOB hits**, harvested to
`MAPS_storage/pixesl_qq_10k.csv` (+ `_extended.csv`). Readout-relevant numbers
(20 µm pixels):

| layer | r | hits/evt | area | hit rate | occupancy/evt (avg) | occupancy/evt (peak BX) |
|---|---|---|---|---|---|---|
| 3 | 130 mm | 20.1 | 2 663 cm² | 7.6×10⁻³ /cm²/evt | 3.0×10⁻⁸ | 2.0×10⁻⁷ |
| 4 | 315 mm | 20.5 | 12 904 cm² | 1.6×10⁻³ /cm²/evt | 6.4×10⁻⁹ | 6.0×10⁻⁸ |

- Hits/layer are **equal** at high statistics (the 5-event L3≠L4 asymmetry was noise).
- **Inner layer (3) drives the readout** — ~5× higher occupancy/rate (same hits, 1/5
  the area). `qin` median ≈ 4800 e⁻ (MIP for 50 µm Si); 76 % prompt / 24 % late.
- **Physics-only occupancy is tiny** (~10⁻⁸/pixel/event; <0.1 % even over a 1000-BX
  frame, see `occupancy_vs_window.pdf`). The design-driving occupancy will come from
  **beam-induced background** (incoherent pairs) — a separate study.

Plots (PDF, kept in the repo at **`plots/qq_10k/`**):
- readout: `occupancy_vs_window`, `occupancy_per_layer`, `rate_per_layer`, `hitdensity_vs_z`
- distributions: `occupancy_map_L3/L4`, `qin_hist`, `h_time_hist`(+`_full`),
  `hits_per_event`, `rz_hitmap`, `hits_per_layer`

5-event spot check (earlier): confirmed 20 µm cellID decode, the two cylinders at
130/315 mm in r-z, and the two TOF peaks (~0.45 / ~1.05 ns) in `h_time`.

---

## 9. Gotchas / lessons learned (important)

- **ddsim reads `.stdhep`, NOT `.stdhep.gz`.** Decompress first.
- **Leptonic wzp6 full sim FATALs** "stable particle with daughters" (DD4hep #1094):
  the `e+e-→e+e-` (Bhabha) channel writes a status-1 electron with daughter pointers
  that Geant4 rejects. Detector-independent (CLD fails too). → use **qq-only**.
- **Vertex smearing the correct way** (Brieuc's recipe): OFF in the generator
  (`MSTP(151)=0` in the card), ON at full sim (`SIM.vertexSigma` in `maps_steer.py`)
  + `crossingAngleBoost=0.015`. Doing it in both places hits #1094.
- **`ddsim --skipNEvents N` (N>0) SIGSEGVs** on stdhep input → do **per-file /
  self-contained chunking**, never skip-slice one file.
- **Keep the condor job script minimal**: plain `source setup_MAPS.sh` + plain
  `ddsim`. Running ddsim under `set -e/-u` crashes it (SIGSEGV mid-shower).
- The fork's `_o1_v03` plugins require the **local k4geo build** on the stable stack
  (`source setup_MAPS.sh --build-k4geo` once).
- Don't shadow shell vars like `WORK` (your login env exports it).
- **SDCC condor accounting group**: use the submit command `accounting_group = group_usfcc`
  (+ `accounting_group_user = <user>`), **not** `+AccountingGroup = "group_usfcc"` — the
  bare form gives no `.user` subgroup → negotiator returns "no match found" (idle forever).
  You must first be added to the group (email `rt-racf-useraccounts@bnl.gov`).
- **Memory**: ALLEGRO full sim actually peaks **~7.3 GB** (the earlier "3 GB" was just the
  cgroup *kill* point). SDCC hard-enforces `request_memory` via cgroups → set **≥8 GB**
  (held jobs report "over cgroup memory limit"). `should_transfer_files = NO` (shared gpfs).
- Keep small artifacts (PDF plots) **in this repo** (`plots/`); put bulk data
  (edm4hep, stdhep, the merged CSV) in **`/gpfs/.../MAPS_storage/`**.

---

## 10. Possible next steps

- **Beam-induced background (BIB) overlay** — incoherent e⁺e⁻ pairs etc.; the real
  occupancy driver at the FCC-ee vertex. *(Handled in a separate effort/chat.)*
- Calo-skip / tracker-only geometry (~10× faster sim, since the calo is unused) ·
  add μμ/ττ channels · real BX spacing · charge sharing / clustering · noise hits ·
  per-module PixESL streams · multiple pitches / layer configs.
