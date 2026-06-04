# fcc_maps_wrapper_pixesl

FCC-ee MAPS silicon-wrapper → **PixESL** hit-stream workflow for WP1 of the LDRD
*"Integrated AI-Enabled Tracking Demonstrator for FCC-ee"*.

Goal: produce realistic FCC-ee pixel hit streams (for PixESL/SystemC readout
simulation) from the **ALLEGRO** detector concept. Generate `e+e- → Z →`
inclusive at the Z pole, simulate hits in the silicon wrapper outside the gaseous
(drift-chamber) tracker, and convert `SimTrackerHit`s into the PixESL table:

```
BX,COL,ROW,h_time,qin
```

## Key finding (geometry already exists)
ALLEGRO `o1_v03` **already ships a sensitive silicon wrapper** outside the drift
chamber, producing `edm4hep::SimTrackerHit`s:

- barrel collection **`SiWrBCollection`** (r = 2040/2060 mm, half length 2400 mm,
  sensitive Si **50 µm** — matches the WP1 baseline exactly)
- disk collection `SiWrDCollection`

There is **no 20 µm pixel segmentation** in the readout (cellID resolves to the
sensor tile), so pixelization is done in the converter for the first milestone.
Full details + how to add a real `CartesianGridXY` segmentation in your local
k4geo fork: [geometry/README_geometry.md](geometry/README_geometry.md).

## Repository layout
```
setup/        environment setup + local-fork cloning
geometry/     discover/inspect ALLEGRO geometry; MAPS wrapper template
generation/   WHIZARD Z-inclusive steering
simulation/   ddsim particle-gun test + Z-inclusive run + output checker
conversion/   SimTrackerHit -> PixESL CSV converter (+ YAML configs)
analysis/     summary table + plots
outputs/      all generated files land here
```

## Environment

Decision for this setup: **stable Key4hep release + local `k4_local_repo`**, with
optional **local k4geo / k4Reco forks** for editing geometry.

```bash
# (one-time) clone your editable forks:
#   k4geo : git@github.com:Ang-Li-93/k4geo.git
#   k4Reco: git@github.com:Ang-Li-93/k4Reco.git
bash setup/clone_local_forks.sh                 # -> /gpfs/.../Allegro/{k4geo,k4Reco}

# each session:
export LOCAL_K4GEO=/gpfs/mnt/gpfs01/usfcc/ali3/Allegro/k4geo   # dir containing FCCee/
export K4RECO_DIR=/gpfs/mnt/gpfs01/usfcc/ali3/Allegro/k4Reco    # built repo (optional)
source setup/setup_key4hep.sh                   # stable stack + overrides
bash   setup/check_environment.sh               # sanity check
```
Omit `LOCAL_K4GEO`/`K4RECO_DIR` to use the central CVMFS geometry. The environment
actually used is recorded in `outputs/environment_used.txt`.

## End-to-end run

```bash
# 1. setup
source setup/setup_key4hep.sh

# 2-3. find & inspect ALLEGRO geometry
bash geometry/find_allegro_geometry.sh
bash geometry/inspect_allegro_geometry.sh        # auto-picks latest ALLEGRO XML

# 4. (only if you want a standalone MAPS layer) edit geometry/MAPSWrapper_o1_v00.xml
#    -- not needed for the first milestone; use SiWrBCollection.

# 5. particle-gun test -> confirm wrapper hits
bash   simulation/run_particle_gun_test.sh 200
python simulation/check_sim_output.py outputs/particle_gun_maps_wrapper.root

# 6. generate Z-inclusive (1000 -> 10000 -> 100000)
bash generation/run_whizard.sh 1000

# 7. full simulation through ALLEGRO + wrapper
bash simulation/run_ddsim_zinclusive.sh 1000

# 8. convert to PixESL CSV
python conversion/convert_simhits_to_pixesl.py \
  --input outputs/z_inclusive_maps_wrapper_edm4hep.root \
  --output outputs/pixesl_hits_zinclusive.csv \
  --geometry conversion/geometry_config.yaml \
  --collections conversion/collections_config.yaml \
  --edep-unit GeV

# 9. summarize
python analysis/summarize_pixesl_hits.py outputs/pixesl_hits_zinclusive.csv

# 10. plot
python analysis/plot_pixesl_hits.py outputs/pixesl_hits_zinclusive.csv
```

### Quick smoke test (no generation/simulation needed)
An existing reference sim file already has wrapper hits:
```bash
python conversion/convert_simhits_to_pixesl.py \
  --input /gpfs/mnt/gpfs01/usfcc/ali3/Allegro/ALLEGRO_sim.root \
  --output outputs/pixesl_test.csv --collection SiWrBCollection
python analysis/summarize_pixesl_hits.py outputs/pixesl_test.csv
```
This is verified to work (≈148 accepted hits; qin median ≈ 4900 e⁻; h_time 6.8–39 ns).

## First milestone (achieved on the reference file)
- [x] ROOT file with MAPS-wrapper `SimTrackerHit`s (`SiWrBCollection`)
- [x] PixESL CSV `BX,COL,ROW,h_time,qin`
- [x] summary + plots with nonzero hits and reasonable qin/time distributions

## Planned improvements
real ALLEGRO module geometry · real cellID decoding (add `CartesianGridXY`) ·
multiple modules / wrapper layers · beam-background overlay · real BX spacing ·
charge sharing / clustering · noise hits · module-by-module PixESL files.

## Configuration knobs
- `conversion/geometry_config.yaml` — pitch, grid, radius/half-length, `tile_mode`
  (`wrap`/`single`), timing, charge model.
- `conversion/collections_config.yaml` — candidate collection priority list.
- env: `LOCAL_K4GEO`, `K4RECO_DIR`, `ALLEGRO_XML`, `ALLEGRO_VERSION`,
  `GUN_PARTICLE`, `GUN_ENERGY`, `RANDOM_SEED`, `KEY4HEP_SETUP`.
No local username is hard-coded; all outputs go under `outputs/`.
```
