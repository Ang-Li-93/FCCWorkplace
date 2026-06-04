# Analysis: summarize & plot PixESL hits

Both tools read a PixESL CSV (`BX,COL,ROW,h_time,qin`) and, if present, its
sidecar `*.metadata.json` (for the pixel-grid size and barrel geometry).

## Summary table
```bash
python analysis/summarize_pixesl_hits.py outputs/pixesl_hits_zinclusive.csv
```
Prints: number of hits, number of BX, avg/max/min hits per BX, qin
mean/median/percentiles/min/max, h_time min/max/mean, COL/ROW ranges, the 10
hottest pixels, the occupancy per BX (= hits-per-BX / N_pixels), and an estimated
hit rate per cm² per event (barrel lateral area from metadata).

If no metadata JSON is found, pass `--geometry conversion/geometry_config.yaml`
for a grid-size fallback (occupancy then uses the single-tile `n_col×n_row`).

## Plots
```bash
python analysis/plot_pixesl_hits.py outputs/pixesl_hits_zinclusive.csv \
       --outdir outputs/plots
```
Writes to `outputs/plots/`:
- `occupancy_map.png` — COL vs ROW 2D occupancy
- `hits_per_bx.png` — hits-per-BX histogram
- `qin_hist.png` — charge distribution
- `h_time_hist.png` — hit-time distribution
- `hottest_map.png` — coarse-binned hottest-region map

Matplotlib runs headless (`Agg`), so this works over SSH with no display.
`--bins N` sets the 2D-map resolution (default 80).

## Interpreting the first results
For the reference e⁻-gun file the wrapper barrel sees ~1.5 hits/event; for a real
Z-inclusive sample expect higher multiplicity. qin should peak around the MIP value
for 50 µm Si (~4000 e⁻, i.e. ~80 e/µm), with a Landau tail. h_time is dominated by
time-of-flight to r ≈ 2040 mm (~6.8 ns) plus a spread from secondaries.
