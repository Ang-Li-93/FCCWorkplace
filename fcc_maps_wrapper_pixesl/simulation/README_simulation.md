# Simulation (ddsim on ALLEGRO + silicon wrapper)

All scripts resolve the ALLEGRO compact XML via `_resolve_geometry.sh`, honoring
(in order) `$ALLEGRO_XML`, `$ALLEGRO_VERSION`, then the latest `ALLEGRO_*.xml`
under `$K4GEO`. Because `$K4GEO` follows your `LOCAL_K4GEO` override, edits in
your local k4geo fork are picked up automatically.

## 1. Particle-gun test (confirm wrapper hits)
```bash
source setup/setup_key4hep.sh
bash simulation/run_particle_gun_test.sh 200      # central muons, theta 80–100°
python simulation/check_sim_output.py outputs/particle_gun_maps_wrapper.root
```
Muons are thrown around θ = 90° over full φ so the barrel wrapper at r = 2040 mm
is crossed. `check_sim_output.py` lists all collections, flags the
`SimTrackerHit` ones, and prints the first hits (position, time, EDep, cellID).

Knobs (env vars): `GUN_PARTICLE` (default `mu-`), `GUN_ENERGY` (`10*GeV`),
`ALLEGRO_VERSION`, `ALLEGRO_XML`, `RANDOM_SEED`.

## 2. Z-inclusive simulation
```bash
bash simulation/run_ddsim_zinclusive.sh 1000 outputs/z_inclusive_gen.hepmc
# -> outputs/z_inclusive_maps_wrapper_edm4hep.root
```
Args: `N_EVENTS` (default 1000; `-1` = all), `INPUT_FILE` (default
`outputs/z_inclusive_gen.hepmc`). Scale up 1000 → 10000 → 100000 once validated.

## Collections to expect (ALLEGRO o1_v03)
`SiWrBCollection` (wrapper barrel — primary), `SiWrDCollection` (wrapper disks),
`DCHCollection` (drift chamber), `VertexBarrelCollection`, `VertexEndcapCollection`,
plus calorimeter/muon collections.

## Notes
- `--random.enableEventSeed --random.seed` makes runs reproducible.
- EDM4hep units in the output: position **mm**, time **ns**, `EDep` **GeV**
  (these are the converter defaults: `--edep-unit GeV`, `--time-unit ns`).
- An existing reference file (`/gpfs/.../Allegro/ALLEGRO_sim.root`, e- gun) already
  contains `SiWrBCollection`/`SiWrDCollection` and can be fed straight to the
  converter for a quick test.
