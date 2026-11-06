# IPC background chain — hands-on walkthrough

How to run the incoherent-pair-creation (IPC) background chain of the MAPS/PixESL
work package yourself, one step at a time, with the commands checked on SDCC on
2026-11-04. Companion to [BIB_STUDIES.md](BIB_STUDIES.md), which holds the history,
the audited numbers and the quoting rules; this file is only about *doing* it.
Every path below is absolute so a command can be pasted from any directory.

```
REPO=/gpfs/mnt/gpfs01/usfcc/ali3/FCCWorkplace
STORE=/gpfs/mnt/gpfs01/usfcc/MAPS_storage
```

## 0. What the chain produces

IPC is the dominant beam background in the vertex region: at each bunch crossing
(BX) the electromagnetic field of one bunch converts photons of the other into
soft e+e- pairs, about 1,200 per BX at the Z, which spiral in the 2 T solenoid.
We want, per BX, the pixel hits they leave on the two **MAPS layers** = outer vertex
barrel layers L3 (r = 131 mm) and L4 (r = 315.5 mm) of our `BNL_MAPS` detector
(ALLEGRO_o1_v03 with those two layers re-pitched to 20 x 20 um). The deliverable is
the PixESL table

```
BX,COL,ROW,h_time,qin        # bunch-crossing id, pixel column/row, time [ps], charge [e-]
```

plus a row-aligned `_extended.csv` with `layer,module,sensor,r_mm,z_mm`.

Two ways to get there, both in the repo:

| track | input | Geant4? | what it is for |
|---|---|---|---|
| **A** central conversion | official ALLEGRO mdi_v2 sim files (1 file = 1 BX) | no | the baseline dataset (19,673 BX, delivered July 2026) |
| **B** own simulation | GuineaPig `.pairs` files (1 file = 1 BX) | yes, ddsim | anything that changes the detector: radius / pitch variants |

The baseline sample is **LCC V106.2 IPC at the Z** with A. Ciarma's **mdi_v2** CAD
interaction region. The older GHC V24.4 production (3,996 BX) is archived and
superseded; it needs a vertex reset and the v1 MDI geometry (see 9.).

Data flow:

```
STORE/BIB/LCC/V106.2/IPC/Z/output_<bx>.pairs      GuineaPig, 20,501 BX, read-only mirror of EOS
      |  (track B)  ddsim + maps_bib_steer.py + MAPS_o1_v01_BIB_v2.xml   ~10 min/BX
      v
bx_<bx>.edm4hep.root                               SimTrackerHits (+ calo hits, MCParticles)
      |             convert_simhits_to_pixesl.py --mode decode_cellid    ~75 s (geometry load)
      v
bx_<bx>.csv  bx_<bx>_extended.csv  bx_<bx>.metadata.json
      |             harvest_bib.sh  (concatenate in BX order, coverage, ledger)
      v
outputs/BIB/pixesl_<tag>.csv (+_extended)          -> plots, truth ntuple, share site

STORE/BIB_central/ALLEGRO_o1_v03_mdi_v2_CAD/IPC_LCC_V106p2/output_<bx>.root   central sim, 19,673 BX
      |  (track A)  convert_simhits_to_pixesl.py --mode resegment  (same CSVs as above)
```

Where things live:

| what | where |
|---|---|
| code | `$REPO/fcc_maps_wrapper_pixesl/{simulation,conversion,analysis}/` |
| geometry | `$REPO/k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/` (git submodule, fork Ang-Li-93/k4geo) |
| raw inputs | `$STORE/BIB/` (mirror of `/eos/project/f/fcc-ee-mdi/BIB`, read-only) and `$STORE/BIB_central/` |
| bulk outputs | `$STORE/BIB_derived/{sim,convert,truth}/<production>/` |
| merged CSVs, plots | `$REPO/outputs/BIB/` (git-ignored) |
| published copies | https://angli-share.web.cern.ch/FCC/MAPS/BIB_IPC_LCC/ |
| the official tooling | `$REPO/bib-studies/` (clone of HEP-FCC/bib-studies with a 6-line MAPS patch) |

## 1. Environment

```bash
cd /gpfs/mnt/gpfs01/usfcc/ali3/FCCWorkplace
source setup_MAPS.sh
bash fcc_maps_wrapper_pixesl/setup/check_environment.sh
```

What `setup_MAPS.sh` does: sources the **fixed** Key4hep release 2026-04-08
(DD4hep 1.36, which reads `.pairs` natively), registers the locally built `k4geo`
fork with `k4_local_repo` (the stable stack lacks the `_o1_v03` vertex plugin), and
points `K4GEO` at the fork's *source* XML so geometry edits need no rebuild. The
k4geo build already exists (`k4geo/build`, `k4geo/install`); only after a `git pull`
that touches C++ would you rerun `source setup_MAPS.sh --build-k4geo`.

Two things to know before writing any script around it:

- it **overwrites generic shell variables** (`OUTDIR`, `REPO_ROOT`, ...). Read your
  own variables before sourcing, or prefix them (the runners use `BIB_*`);
- it **parses positional arguments**, so a script must `set --` before sourcing it.
  Capture `$1 $2` first.

Do not source `setup.sh`, `env.sh`, `setup_hbs.sh` or `setup_winter2023.sh` in the
same shell: the four environments are not mixable.

## 2. Look at the input

```bash
P=/gpfs/mnt/gpfs01/usfcc/MAPS_storage/BIB/LCC/V106.2/IPC
head -40 $P/README.log               # GuineaPig version, beam parameters, "boosted frame"
ls $P/Z | wc -l                      # 20501 files, ids 100003 ... 999977 (not contiguous)
wc -l  $P/Z/output_100003.pairs      # 1182 particles = 1 bunch crossing
head -3 $P/Z/output_100003.pairs
```

One line = one particle: `E[GeV] (sign = charge)  beta_x beta_y beta_z  x y z [nm]  ...`.
The frame is GuineaPig's boosted frame, hence `crossingAngleBoost = 0.015` in the
steering. These 2026 files were generated **with** the 2 T field and the 10 mm pipe, so
the positions are right and nothing is reset. (GHC V24.4 files are in
`data<bx>/pairs.pairs` directories, lack the field, and get x,y,z set to 0 first.)

The central simulation of the same crossings: 19,673 files
`$STORE/BIB_central/ALLEGRO_o1_v03_mdi_v2_CAD/IPC_LCC_V106p2/output_<bx>.root`
(828 of the 20,501 are missing centrally, see the upstream note). Every file carries
the complete ddsim configuration in its `runs` tree; that is where the central settings
(FTFP_BERT_EMZ, 0.05 mm range cut, low-energy EM commands, **1 keV per-step tracker
filter**, keepAllParticles False) were read off.

## 3. Track B by hand: one crossing through ddsim

```bash
cd /gpfs/mnt/gpfs01/usfcc/ali3/FCCWorkplace && source setup_MAPS.sh
BX=100003
OUT=/gpfs/mnt/gpfs01/usfcc/ali3/FCCWorkplace/outputs/BIB/hands_on; mkdir -p $OUT
BIB_SEED=$((42+BX)) ddsim \
   --steeringFile fcc_maps_wrapper_pixesl/simulation/maps_bib_steer.py \
   --compactFile  k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01_BIB_v2.xml \
   --inputFiles   /gpfs/mnt/gpfs01/usfcc/MAPS_storage/BIB/LCC/V106.2/IPC/Z/output_${BX}.pairs \
   --numberOfEvents -1 \
   --outputFile   $OUT/bx_${BX}.edm4hep.root  2>&1 | tee $OUT/ddsim_bx${BX}.log
```

What the pieces are:

- `MAPS_o1_v01_BIB_v2.xml`: ALLEGRO_o1_v03 + mdi_v2 CAD beam pipe and masks
  (STL meshes in `k4geo/FCCee/MDI/compact/stl_files/`), LCC final-focus quads, the
  anti-solenoid field map, world volume = vacuum, and the single swap of the vertex
  include to the 20 um `VertexComplete_o1_v01.xml`. The plain `MAPS_o1_v01.xml` is
  the physics geometry (shape-based pipe); `MAPS_o1_v01_BIB.xml` is the GHC-era v1 MDI.
  **Lattice and MDI version must match**: LCC pairs on the v1 MDI gave 3-12x too many hits.
- `maps_bib_steer.py`: the bib-studies recipe. FTFP_BERT_EMZ, range cut 0.05 mm,
  `/cuts/setLowEdge 50 eV`, Auger on, tracker filter `edep0` (keep every deposit),
  `keepAllParticles`, boost 0.015, no vertex smearing, one `.pairs` file = one event
  (`particlesPerEvent = -1`), weighted tracker action. The seed comes from the
  `BIB_SEED` environment variable (production uses 42 + bx, the retry
  42 + bx + 1,000,000) because `--random.seed` on the command line crashes ddsim.
- `--numberOfEvents -1`: read the whole file (one event).

Expect about 80 s of geometry loading, then 5-10 min of tracking; a BX is "done" when
the log ends with the Geant4 run summary and the file is a few MB. About 4 % of
crossings make Geant4 loop forever in the CAD geometry (deterministic per event); the
production runner kills those after 40 min and retries once with the other seed.
Interactively, if nothing is printed for 15 min, Ctrl-C and try another BX.

Look at what came out:

```bash
python3 fcc_maps_wrapper_pixesl/simulation/check_sim_output.py $OUT/bx_${BX}.edm4hep.root
```

lists the 21 collections and the hit counts per tracker collection
(`VertexBarrelCollection` is ours; L0-L2 are in it too) and prints a few hits with
position [mm], time [ns] and EDep [GeV].

## 4. Convert to the PixESL table

```bash
python3 fcc_maps_wrapper_pixesl/conversion/convert_simhits_to_pixesl.py \
   --input  $OUT/bx_${BX}.edm4hep.root \
   --output $OUT/bx_${BX}.csv \
   --mode decode_cellid \
   --compact     k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01_BIB_v2.xml \
   --geometry    fcc_maps_wrapper_pixesl/conversion/geometry_config.yaml \
   --collections fcc_maps_wrapper_pixesl/conversion/collections_config.yaml \
   --allow-empty --col-offset 465 --row-offset 495 --bx-offset $BX
cat $OUT/bx_${BX}.csv; cat $OUT/bx_${BX}_extended.csv; python3 -m json.tool $OUT/bx_${BX}.metadata.json
```

- `decode_cellid`: the vertex readout is a real `CartesianGridXY`, so COL/ROW are
  the `x`/`y` fields of the cellID (signed, centred on the sensor) and `layer`,
  `module`, `sensor` are the other fields. The compact XML is loaded only to build
  the bit-field decoder, which costs ~70 s.
- `--col-offset 465 --row-offset 495`: half the sensor pixel count (18.6 mm / 20 um
  = 930, 19.8 mm / 20 um = 990), so every BX lands in the **same** local frame,
  COL 0-930 and ROW 0-990 inclusive, identical to the qq physics CSVs. Without fixed
  offsets the converter shifts each file by its own minimum, which breaks merging.
- `--bx-offset $BX`: the BX column is the true crossing id (events in the file are
  numbered from 0).
- `--allow-empty`: 58 % of LCC crossings leave no hit on L3+L4; a header-only CSV is
  a valid, complete result.
- `keep_layers: [3, 4]` in `geometry_config.yaml` drops the inner barrel; `qin` =
  EDep / 3.6 eV, `h_time` = time x 1000.
- the `*_extended.csv` is row-aligned with the strict one; `*.metadata.json` records
  input, collection, counts, offsets and the converter's git hash.

Checked 2026-11-04 on BX 100003 with the commands above: ddsim 541 s, conversion 74 s,
33 vertex-barrel SimHits, 0 on L3/L4 (header-only CSV). The July smoke test of the same
crossing with seed 42 gave 3 L4 hits and the central file has 1: the MAPS layers see
0.9 hits per crossing on average, so a single crossing tells you only that the chain runs.
A `G4Exception GeomSolids1001` warning from the CAD solids in the log is normal.

## 5. Track A by hand: convert one central file

```bash
BX=217846     # the busiest crossing of the central sample: one positron looping for 1.4 us, 112 MAPS hits
python3 fcc_maps_wrapper_pixesl/conversion/convert_simhits_to_pixesl.py \
   --input  /gpfs/mnt/gpfs01/usfcc/MAPS_storage/BIB_central/ALLEGRO_o1_v03_mdi_v2_CAD/IPC_LCC_V106p2/output_${BX}.root \
   --output $OUT/central_bx_${BX}.csv \
   --mode resegment \
   --compact     k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01_BIB_v2.xml \
   --geometry    fcc_maps_wrapper_pixesl/conversion/geometry_config.yaml \
   --collections fcc_maps_wrapper_pixesl/conversion/collections_config.yaml \
   --allow-empty --col-offset 465 --row-offset 495 --bx-offset $BX
diff $OUT/central_bx_${BX}.csv /gpfs/mnt/gpfs01/usfcc/MAPS_storage/BIB_derived/convert/IPC_LCC_V106p2_central/csv/bx_${BX}.csv && echo identical
```

`resegment` takes layer/module/sensor from the cellID but **re-bins COL/ROW from the
hit position** at the pitch in the YAML, through the sensor's local frame
(dd4hep VolumeManager). It is needed because the central files were simulated with the
stock 50 x 150 um readout; the sensors themselves are identical, and the sensor is
all Geant4 sees. Checked 2026-11-04 on BX 100045 (no MAPS hit): 72 s, identical to the production copy.
The production did this for all 19,673 files with `run_central_convert.sh` (394 condor
jobs of 50 files, `$STORE/BIB_derived/convert/IPC_LCC_V106p2_central/`).

## 6. Track B at scale: the condor production

Three scripts in `fcc_maps_wrapper_pixesl/simulation/`:

| script | role |
|---|---|
| `run_bib_chunk.sh PROC NBX BXLIST COMPACT STEERING SRCDIR OUTDIR VTXRESET` | one job: for its NBX crossings, (vertex reset) + ddsim + convert, per-BX seed, 40 min watchdog, 2 seeds, atomic writes, per-step resume, outcome ledger |
| `submit_bib_condor.sh [--submit]` | scans SRCDIR, writes a timestamped BX list and a `.sub`, submits only with `--submit` |
| `harvest_bib.sh` | concatenates the per-BX CSVs in BX order, reports coverage against the submitted list, tallies the ledger, counts unique pixels |

Everything is configured through environment variables; **set them explicitly**, the
defaults are not the baseline (default `COMPACT` is the GHC-era `MAPS_o1_v01_BIB.xml`
and default `OUTDIR` is a directory that no longer exists):

```bash
cd /gpfs/mnt/gpfs01/usfcc/ali3/FCCWorkplace && source setup_MAPS.sh
export SRCDIR=/gpfs/mnt/gpfs01/usfcc/MAPS_storage/BIB/LCC/V106.2/IPC/Z
export COMPACT=$PWD/k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01_BIB_v2.xml
export OUTDIR=/gpfs/mnt/gpfs01/usfcc/MAPS_storage/BIB_derived/sim/LCC_V106p2_handson

# 1) dry run: writes OUTDIR/condor/{bxlist_<stamp>.txt, maps_bib_ipc_<stamp>.sub}, submits nothing
bash fcc_maps_wrapper_pixesl/simulation/submit_bib_condor.sh
cat $OUTDIR/condor/maps_bib_ipc_*.sub          # read what would be submitted

# 2) canary: 10 crossings, 1 per job
NBXTOTAL=10 NBX=1 bash fcc_maps_wrapper_pixesl/simulation/submit_bib_condor.sh --submit
condor_q; tail -f $OUTDIR/condor/logs/job_*_0.err

# 3) results so far (safe while jobs run) and the merged CSV
OUTDIR=$OUTDIR TAG=ipc_LCC_V106p2_handson bash fcc_maps_wrapper_pixesl/simulation/harvest_bib.sh
cat $OUTDIR/ledger/bx_*.status | awk '{print $1}' | sort | uniq -c

# 4) the real thing: NBX=5 per job (~1 h), all BX in SRCDIR -> 4,101 jobs; cap with NBXTOTAL
NBXTOTAL=400 NBX=5 bash fcc_maps_wrapper_pixesl/simulation/submit_bib_condor.sh --submit
```

Rules the scripts enforce (each one is a bug that cost time once):

- a re-submission on the same OUTDIR is refused while its jobs are still queued
  (`FORCE=1` overrides); the runner skips crossings that already have a CSV, so
  re-submitting after failures only redoes the missing ones;
- every output is written to scratch and renamed into place; the strict CSV is
  written last and is the "done" marker;
- `OUTDIR/ledger/bx_<bx>.status` = `ok-seed1 | ok-seed2 | failed-timeout | failed-crash`
  with the seeds used, so any crossing can be reproduced byte-for-byte;
- `BXFILE=<list> NBX=1 ... --submit` runs an explicit list (the harvest writes
  `pixesl_<tag>.missing_bx.txt` and `.failed_bx.txt` for this);
- condor at SDCC: `accounting_group = group_usfcc` plus `accounting_group_user`,
  `request_memory 8192` (ALLEGRO full sim peaks ~7 GB; cgroups kill above the request),
  `should_transfer_files = NO` (gpfs is shared), `getenv = False` (so anything the
  runner needs from the environment goes through `JOB_ENV`).

Budget: 10 min per crossing, so 400 BX = 67 CPU-h = about 1 h on 80 slots; the
full 20,501 would be ~3,400 CPU-h.

## 7. Radius / pitch variants (the step that was prepared but never run)

The LDRD scan moves both MAPS layers in radius (185 mm gap kept, outer layer capped
by the drift-chamber wall at r < 330 mm) and reads them out at 25 um to match
A. Ilg's detector-variant studies. `make_radius_variants.py` already generated, and
the k4geo fork already contains, the variants r070, r100, r130 (= baseline radii, a
closure check), r145:

```
k4geo/.../MAPS_o1_v01/DectDimensions_<tag>.xml          only VTXOB_r_min/max_layer changed
k4geo/.../MAPS_o1_v01/MAPS_o1_v01_BIB_v2_<tag>.xml      BIB_v2 master with that DectDimensions
fcc_maps_wrapper_pixesl/conversion/geometry_config_<tag>.yaml   resegment, 25 um, variant radii
```

The stave and module counts scale with the radius inside `VertexComplete_o1_v01.xml`
(anchored so that 130/315 mm give exactly 23/51 staves and 8/16 modules). The pitch is
never changed in the geometry; the converter re-bins at 25 um, with frame offsets
372/396 (= 18.6 mm / 25 um / 2, 19.8 mm / 25 um / 2).

Status on 2026-11-04: `$STORE/BIB_derived/sim/LCC_V106p2_radius_{r100,r145}/condor/`
contain dry-run submit files from 2026-07-20 for 400 BX each and **no logs, no
outputs**; nothing was ever submitted. The command that the dry runs encoded:

```bash
TAG=r100
OUTDIR=/gpfs/mnt/gpfs01/usfcc/MAPS_storage/BIB_derived/sim/LCC_V106p2_radius_$TAG \
COMPACT=$PWD/k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01_BIB_v2_$TAG.xml \
JOB_ENV="BIB_CONV_MODE=resegment BIB_GEOMCFG=$PWD/fcc_maps_wrapper_pixesl/conversion/geometry_config_$TAG.yaml BIB_COLOFF=372 BIB_ROWOFF=396" \
NBXTOTAL=400 NBX=5 bash fcc_maps_wrapper_pixesl/simulation/submit_bib_condor.sh   # add --submit
```

Before submitting a variant, smoke-test its geometry on one crossing (the committed
`smoke_variant.sh` writes into a stale scratch path; run the ddsim line of section 3
with `MAPS_o1_v01_BIB_v2_$TAG.xml` instead, and grep the log for `overlap` and
`Exception`). The comparison baseline for a variant is **our own** r130 run with the
same 25 um conversion, not the central sample: our chain has a known +9/+23/+34 %
inner-barrel excess over the central files that is common-mode between variants.

## 8. Looking at the results

Three plot families, all on the merged CSVs or the sim files:

```bash
CSV=outputs/BIB/pixesl_ipc_LCC_V106p2_central         # baseline (strict + _extended)
python3 fcc_maps_wrapper_pixesl/analysis/summarize_pixesl_hits.py ${CSV}.csv
python3 fcc_maps_wrapper_pixesl/analysis/plot_pixesl_hits.py ${CSV}.csv --outdir outputs/BIB/plots_test
python3 fcc_maps_wrapper_pixesl/analysis/plot_readout_metrics.py ${CSV}_extended.csv \
        --outdir outputs/BIB/plots_test --n-events 19673          # --n-events: count the empty BX!
```

`--qin-min 278` applies a 1 keV charge threshold, `--dedup-pixels` counts fired pixels
instead of rows; `--pitch-um 25` for the variants.

The official-format plots come from bib-studies `drawhits.py` on the sim files
(reads EDM4hep with podio, decodes cellIDs with the detector module, needs a detector
dictionary). Our clone carries a 6-line patch so that the `MAPS` detector name maps to
the ALLEGRO decoder (`bib-studies/python/MAPS.py`):

```bash
export PYTHONPATH=$PWD/bib-studies/python:$PYTHONPATH
DICT=outputs/BIB/bibstudies_LCC/MAPS_o1_v01_DetectorDimensions.json   # made once with (writes into the cwd, ~1 min):
#   python3 bib-studies/plotting/xml2json.py -d $REPO/k4geo/FCCee/BNL_MAPS/compact/MAPS_o1_v01/MAPS_o1_v01_BIB_v2.xml
mkdir -p outputs/BIB/bibstudies_test && cd outputs/BIB/bibstudies_test
python3 $REPO/bib-studies/plotting/drawhits.py -i $OUTDIR/sim -n -1 -e 1 -s VertexBarrel \
        -d $REPO/$DICT --sample handson -D 0 -m -p
```

`-e` is events per file (1 here; `-e -1` breaks the per-event normalisation). Output:
`<sample>_<N>evt_VertexBarrel_<input dir basename>.root` plus one PDF per histogram
(48 files for one crossing; checked 2026-11-04). Over the full 19,673-file sample
it was run as 103 condor slices with `-e 103` so that every histogram is exactly
additive under `hadd` (`$STORE/BIB_derived/convert/IPC_LCC_V106p2_central/fullplots/slices/`).
Read `BIB_STUDIES.md` section 9 before quoting any drawhits axis: "occupancy [%]" there
is fired pixels / sensors, and the hit maps are counts per map cell, not densities.
`analysis/redraw_bibstudies_labelled.py MERGED.root` redraws them with honest titles.

The truth ntuple is the tool for "what made this hit" questions
(`$STORE/BIB_derived/truth/IPC_LCC_V106p2_central/*.root`, also on the share):

```bash
T=/gpfs/mnt/gpfs01/usfcc/MAPS_storage/BIB_derived/truth/IPC_LCC_V106p2_central
python3 fcc_maps_wrapper_pixesl/analysis/plot_bib_truth.py $T/ipc_LCC_V106p2_central_truth_vertex.root \
        --full $T/ipc_LCC_V106p2_central_truth.root --outdir outputs/BIB/plots_LCC_truth_test
python3 fcc_maps_wrapper_pixesl/analysis/bib_event_display.py $T/ipc_LCC_V106p2_central_truth_vertex.root --list
python3 fcc_maps_wrapper_pixesl/analysis/bib_event_display.py $T/ipc_LCC_V106p2_central_truth_vertex.root --bx 217846 --tracks
python3 fcc_maps_wrapper_pixesl/analysis/bib_display_3d.py $T/ipc_LCC_V106p2_central_truth_vertex.root --bx 217846 --tracks --layermap --pdf --bxdir --outdir displays3d   # 3D HTML (+PDF) of the vertex barrel + disk 1 and the unrolled L3/L4 maps, one subfolder BX<id> per crossing (--bxdir); --view vertex adds disks 2-3; --color layer: hits by layer; --color particle [--turns 20]: one colour per particle, hits and helix
python3 fcc_maps_wrapper_pixesl/analysis/bib_display_3d.py $T/ipc_LCC_V106p2_central_truth.root --bx 217846 --full --outdir displays3d            # with drift chamber + Si wrapper
```

It was built by `make_bib_truth_ntuple.py` (100 condor slices over the central files,
uproot only, submit file in `$T/condor/`) and `merge_bib_truth_ntuple.py`. To make one
for a *new* production, point `--indir` at its `sim/` directory; the scripts assume the
central conventions (1 keV per-step cut, 1 MeV particle-storage threshold), so with our
`edep0` / keepAllParticles steering the "sub-MeV secondary" classification changes meaning.

## 9. GHC V24.4 (archived) in one line

Same chain with `SRCDIR=$STORE/BIB/GHC/V24.4/IPC/Z` (layout `data<bx>/pairs.pairs`,
auto-detected), `COMPACT=.../MAPS_o1_v01_BIB.xml` (v1 MDI) and the vertex reset on
(`VTXRESET=1`, automatic for that layout). Results: `outputs/BIB/pixesl_ipc_GHC_V24p4_Z*.csv`,
share folder `BIB_IPC/`. Label them "GHC V24.4 IPC @ Z, raw SIM hits, no threshold".

## 10. Publishing

Results go to https://angli-share.web.cern.ch/FCC/MAPS/BIB_IPC_LCC/ (EOS
`/eos/user/l/lia/www/FCC/MAPS/BIB_IPC_LCC/` on `eosuser.cern.ch`, Kerberos
`lia@CERN.CH`). Stage locally under `fcc_maps_wrapper_pixesl/results/<name>/` (git-ignored),
write a README with the sample label and provenance, then

```bash
kinit lia@CERN.CH
xrdfs root://eosuser.cern.ch mkdir -p /eos/user/l/lia/www/FCC/MAPS/BIB_IPC_LCC/<name>
cd fcc_maps_wrapper_pixesl/results/<name> && for f in *; do xrdcp -f $f root://eosuser.cern.ch//eos/user/l/lia/www/FCC/MAPS/BIB_IPC_LCC/<name>/$f; done
```

To publish a document such as this one, give it a folder of its own and upload it as
`README.md`: the site's root `index.php` renders a folder's `README.md` with Parsedown
(tables, fenced code and links included) at the top of the folder page, while every
other `.md` is only listed as a download and served as plain text.

```bash
xrdfs root://eosuser.cern.ch mkdir -p /eos/user/l/lia/www/FCC/MAPS/BIB_IPC_LCC/walkthrough
xrdcp -f documents/BIB_IPC_WALKTHROUGH.md root://eosuser.cern.ch//eos/user/l/lia/www/FCC/MAPS/BIB_IPC_LCC/walkthrough/README.md
# -> https://angli-share.web.cern.ch/FCC/MAPS/BIB_IPC_LCC/walkthrough/
```

The 3D displays (`outputs/BIB/displays3d/`: top `README.md`, one folder `BX<id>/` per crossing
with its own `README.md` and the two PDFs) go to `BIB_IPC_LCC/displays3d/` with the same layout,
so every folder page shows its README above the files:

```bash
SRC=outputs/BIB/displays3d; DST=/eos/user/l/lia/www/FCC/MAPS/BIB_IPC_LCC/displays3d; X=root://eosuser.cern.ch
xrdfs $X mkdir -p $DST && xrdcp -f $SRC/README.md $X/$DST/README.md
for d in $SRC/BX*/; do b=$(basename $d); xrdfs $X mkdir -p $DST/$b; for f in $d*; do xrdcp -f $f $X/$DST/$b/$(basename $f); done; done
# -> https://angli-share.web.cern.ch/FCC/MAPS/BIB_IPC_LCC/displays3d/
```

The link to `BIB_STUDIES.md` in the header works if that file is uploaded next to it
(plain text), or point it at a second folder that holds `BIB_STUDIES.md` as its `README.md`.
For reading without uploading: VS Code's Markdown preview (Ctrl+Shift+V on the open file),
or GitHub, which renders the file once the branch is pushed.

## 11. Where the study stands (2026-11-04)

Done and published: the LCC V106.2 baseline dataset (track A, 19,673 BX, L3 0.306 /
L4 0.565 SimTrackerHits per BX = 0.259 / 0.445 fired 20 um pixels per BX), its
validation against A. Ilg's FCC Week 2026 numbers, our own mdi_v2 chain validated on
400 BX (377 clean, 4 seed-2, 19 deterministic hangs), the truth ntuple and the answers
to the 4 Aug review (why L4 > L3: sub-MeV electrons from soft photons, not loopers).

Open, in the order they block each other:

1. **Radius scan** (section 7): geometries, configs and dry-run submit files exist;
   nothing simulated. First run r130 (closure against the July validation batch) and
   one other radius on 400 BX, compare L3/L4 hits per cm2 per BX at 25 um.
2. **Send `BIB_MDI_V2_UPSTREAM_NOTE.md`** to A. Ciarma / J. Eysermans / A. Ilg
   (Geant4 hangs, 4 % missing central crossings, the doubled `SIM.filter.tracker`).
   Their answer decides whether the baseline should be re-simulated with `edep0`.
3. **Like-for-like rerun** of the 400-BX validation with the verbatim central steering
   (`maps_central_steer.py` is *not* it: it uses FTFP_BERT and the default range cut;
   the real central config is the BIB recipe plus `edep1kev` and keepAllParticles False).
   Would settle the +9/+23/+34 % inner-barrel excess.
4. PixESL readout study on the stream; physics + BIB overlay with the Z->qq CSV
   (same address convention, so a concatenation with a BX window); other sources
   (SR, beam-gas, radiative Bhabha: `.hepevt` inputs, boost 0 for beam-gas/SR).
5. Physics open point: how much of the soft-photon component depends on sensor
   thickness, the Auger setting and the beam-pipe CAD model (needs a full-truth
   re-simulation with `userParticleHandler = ""`, because `keepAllParticles = True`
   alone stores nothing extra).

## 12. Gotchas, shortest form

- `ddsim --random.seed` segfaults; seed through `BIB_SEED`. `--meta.runNumberOffset` does not seed.
- Never run ddsim under `set -e` / `set -u` in a wrapper; it crashes mid-shower.
- `--skipNEvents N > 0` segfaults on stdhep; chunk per file.
- Do not redefine `SIM.filter.filters` in a steering; `edep0` and `edep1kev` are predefined.
- `SIM.part.keepAllParticles = True` is a no-op with the default particle handler.
- Converter defaults for `--geometry`/`--collections` are relative to the cwd; pass absolute paths.
- `harvest_bib.sh` compares lists with `comm`, which needs lexicographic sort; it handles it, your own scripts must too.
- `plot_readout_metrics.py` divides by distinct BX in the CSV unless `--n-events` says otherwise; empty crossings count.
- Raw CSV rows are not fired pixels: the duplicate rows in the central sample are Si Auger electrons next to a photo-electron.
- Quote the central sample as "SimTrackerHits, 1 keV simulation cut", never "no threshold".
- Condor: `+AccountingGroup = "group_usfcc"` alone never matches; `+MaxRuntime` and `JobFlavour` are inert at SDCC (site cap 3 days).
- No `/eos` mount at SDCC: `xrdcp`/`xrdfs` with the `lia@CERN.CH` ticket; a recursive `xrdcp` of the BIB tree stalls for hours, use the condor mirror job in `$STORE/BIB_mirror/`.
