# Conversion: SimTrackerHits → PixESL CSV

`convert_simhits_to_pixesl.py` reads `edm4hep::SimTrackerHit`s (via `podio`,
falling back to `uproot`) and writes the PixESL table `BX,COL,ROW,h_time,qin`,
plus a metadata JSON.

```bash
source setup/setup_key4hep.sh
python conversion/convert_simhits_to_pixesl.py \
  --input outputs/z_inclusive_maps_wrapper_edm4hep.root \
  --output outputs/pixesl_hits_zinclusive.csv \
  --geometry conversion/geometry_config.yaml \
  --collections conversion/collections_config.yaml \
  --edep-unit GeV --time-unit ns
# optional: --collection SiWrBCollection  --max-events 1000
```

## Output columns
| col | meaning |
|---|---|
| `BX` | bunch crossing = event index (first version) |
| `COL` | pixel column from local x (r·Δφ) and 20 µm pitch |
| `ROW` | pixel row from local y (z along barrel) and 20 µm pitch |
| `h_time` | hit time in **ps** (`time_ns × 1000`) |
| `qin` | charge in electrons (`EDep[eV] / 3.6`, or default if EDep≤0) |

Rows are sorted by `BX, h_time, COL, ROW`. A sidecar
`*.metadata.json` records the input file, collection used, counts
(read / accepted / rejected), pitch, grid size, mapping mode, units, and the
script git hash.

## Collection selection
Without `--collection`, the converter picks the **first** collection from
`collections_config.yaml` that is present in the file (priority: `SiWrBCollection`
→ `SiWrDCollection` → `MAPSWrapperBarrelHits` → …). If you pass `--collection X`
and it is absent, the script prints the available collections and exits.

## Mapping (`geometry_config.yaml → wrapper.tile_mode`)
- **`wrap`** (default): the whole cylinder is one big pixel grid — COL spans the
  full 2πr circumference, ROW spans the full 2·half_length. Every barrel hit lands
  somewhere; ideal for a first occupancy/rate look. Grid auto-expands (≈640k×240k
  at r=2040 mm, hl=2400 mm).
- **`single`**: one sensor tile (`n_col×n_row`, 1024² → 20.48 mm) centred at
  `(phi0, z0)`; hits outside the tile window are rejected. Faithful to the literal
  WP1 spec; most Z hits fall outside one tile, so expect many rejects.

Switch modes by editing `wrapper.tile_mode` in `geometry_config.yaml`.

## Units
EDM4hep defaults are position **mm**, time **ns**, EDep **GeV**. Override with
`--edep-unit {GeV,MeV,keV,eV}` and `--time-unit {ns,ps,s,us}` if your input differs.
Charge: `qin = EDep_in_eV / eh_pair_energy_eV` (3.6 eV/pair); if `EDep ≤ 0` or
`use_edep_if_available: false`, `default_qin_electrons` (1500) is used.

## Sanity check (uses the existing reference sim file)
```bash
python conversion/convert_simhits_to_pixesl.py \
  --input /gpfs/mnt/gpfs01/usfcc/ali3/Allegro/ALLEGRO_sim.root \
  --output outputs/pixesl_test.csv --collection SiWrBCollection
```
This was verified to yield ~148 accepted hits (qin median ≈ 4900 e⁻, h_time 6.8–39 ns).
