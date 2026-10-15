# SLIDE SOURCE — MAPS/PixESL: LCC V106.2 IPC background (study conclusion)
#          — bibstudies-plot edition —

> **ERRATA (2026-10-05, after the 4 Aug review).** Corrected statements and the answers to the
> review comments are in [BIB_LCC_FOLLOWUP_SLIDES_TEXT.md](BIB_LCC_FOLLOWUP_SLIDES_TEXT.md).
> Slide numbers are those of this file; the deck as presented has one more slide (the geometry
> table), so its numbers are one higher from "Where the hits land" on. What is wrong below:
> - footer and slide 7: the central sample is **not** "no threshold" — ddsim drops every Geant4
>   step below 1 keV; there is no sub-keV tail;
> - slide 5: `avg_occ` is fired pixels ÷ number of sensors, not an occupancy ("L0 ≈ 27%" is
>   meaningless; true pixel occupancy is 8e-7 on L0, 4e-10 / 1.5e-10 on L3 / L4 at 20 µm);
>   per cm² of sensitive silicon the rates are 1.13e-4 (L3) and 4.70e-5 (L4), ratio 2.40, and
>   L4 has 4.43× the silicon (1.1e-4, 4.4e-5, 2.6 and 4.8 are bare-cylinder values);
> - slide 6: the map colours are hits per map cell of an edge-on projection, not hits per unit area;
> - slide 7: "99% e±" names the stored ancestor; "MIP-like, ~15 keV" holds for L0–L2 only;
>   the particle-ID bars are hits per BX;
> - slide 8: "prompt, within 1–2 ns" holds for the five-layer sum only (L3/L4 medians 4.4 / 7.0 ns);
>   "58% of BXs empty" is for L3+L4 while h_occ_tot is the whole barrel;
> - slide 9: the table mixes fired cells and hits, and the reference chart is the same events and
>   script with a 1.8 keV threshold (reproduced exactly), not an independent analysis;
> - slides 10–11: the central ddsim configuration is not unknown — it is stored in the `runs` tree
>   of every central file (FTFP_BERT_EMZ, range cut 0.05 mm, low-energy EM commands, 1 keV
>   per-step tracker filter, keepAllParticles False). The "matched" test of slide 10 used FTFP_BERT
>   with the default range cut, so it was not matched;
> - headline: "~4× (L3) / ~8× (L4) below GHC" compares different hit definitions (GHC had no 1 keV
>   cut); like-for-like it is about 2.5× and 5–6×;
> - catalogue: the `*_map` histograms of energy, species and time are (quantity × layer) histograms,
>   not spatial maps; `h_avg_hits_x_layer1–4_x_module` are broken by an axis offset.
<!-- Instructions for the slide-making assistant ("ppt Claude"):
  - One H2 (##) = one slide. "BULLETS" go on the slide; "NOTES" are speaker notes.
  - "PLOT:" lines name image files to place. Prefer the OFFICIAL-FORMAT bib-studies
    plots (drawhits, ROOT style) — that is what this edition uses. They live at:
      local: /gpfs/.../FCCWorkplace/outputs/BIB/bibstudies_LCC/<name>.png
      web:   https://angli-share.web.cern.ch/FCC/MAPS/BIB_IPC_LCC/bibstudies/<name>.png
    Every bibstudies file is prefixed `ipc_lcc_19673evt_` and suffixed
    `_VertexBarrelCollection.png` — I abbreviate to the middle stem in PLOT: lines;
    expand it to the full filename. Use the .png (not .pdf) for slides.
  - A few custom matplotlib plots (clearer axes/labels) are offered as ALTERNATES
    under "ALT PLOT:" from outputs/BIB/plots_LCC/<name>.png — use whichever reads
    better on the slide.
  - NUMBERS ARE THE SOURCE OF TRUTH, PLOTS ARE PICTURES: the bib-studies plots carry
    their own internal normalization (esp. the rateDensity MHz/cm² plots — see the
    catalogue caveat). Quote the audited per-BX numbers in the HEADLINE box below;
    use the plots for shapes, spectra, and spatial pictures.
  - DO NOT USE the empty/misleading plots — see "AVOID" list at the very bottom.
  - Full plot catalogue (filename -> what it shows -> caption) is appended after
    the slides.
  - Suggested footer on every slide:
      "LCC V106.2 IPC @ Z · central mdi_v2 sim · raw SIM hits, no threshold · 19,673 BX"

  AUDITED HEADLINE NUMBERS (recomputed from the central CSV 2026-07-20):
    - 19,673 bunch crossings · 17,141 raw SIM hits · 13,849 unique fired pixels
    - L3 (r=131 mm):   0.306 hits/BX  = 1.1e-4 hits/cm^2/BX   (raw total 6,019)
    - L4 (r=315.5 mm): 0.565 hits/BX  = 4.4e-5 hits/cm^2/BX   (raw total 11,122)
    - per cm^2 L3 is ~2.6x busier than L4; totals ratio L4/L3 = 1.85 (lattice-dependent)
    - 8,240/19,673 BXs (42%) non-empty; mean 2.1 hits per non-empty BX; max 112 in one BX
    - ~4x (L3) / ~8x (L4) lower than the old GHC V24.4 baseline
    - inner barrel avg firing cells/evt: L0 24.0 · L1 7.8 · L2 4.9 · L3 0.31 · L4 0.57
    - hits are ~99% e+/e- ; deposited energy per hit peaks ~15 keV (MIP in 50 um Si)
    - BX rate 37.04 MHz (LCC v106)
-->

## Slide 1 — Title
Beam-Induced Background for the MAPS Vertex Demonstrator
The LCC V106.2 IPC study, concluded — a validated per-bunch-crossing background hit stream on the 20 µm MAPS outer vertex layers
Ang Li (BNL) — LDRD WP1: AI-Enabled Tracking Demonstrator for FCC-ee
NOTES: Verdict — baseline dataset delivered, chain validated against the official
analysis, detector-variant scan unlocked. Data + plots public at
angli-share.web.cern.ch/FCC/MAPS/BIB_IPC_LCC/.

## Slide 2 — Why background sets the design
BULLETS:
- At the FCC-ee Z pole background arrives EVERY bunch crossing (~27 ns, 37.04 MHz);
  Z→physics events are rare — pixel occupancy & readout bandwidth are set by background
- Dominant vertex source: Incoherent Pair Creation (IPC) — soft e+e- pairs from the
  beam-beam field, ~1200/BX, spiralling in the 2 T solenoid
- Goal: real per-BX hit streams for the PixESL SystemC readout sim on the 20×20 µm
  MAPS outer layers — L3 (r=131 mm) and L4 (r=315.5 mm)
NOTES: Generator GuineaPig++. Other sources (SR, beam-gas, RB, injection) live in the
same MDI sample tree — future work; IPC dominates the vertex layers.

## Slide 3 — Baseline & approach
BULLETS:
- Baseline moved to the LCC V106.2 lattice + A. Ciarma's mdi_v2 CAD MDI (per A. Ilg /
  vertex group); GHC V24.4 is superseded
- Lesson: a first LCC run on the OLD MDI disagreed 3–12× — fix was to match BOTH
  lattice and MDI version
- Two-track attack:
  - Track A (deliverable): convert the official central SimHits directly — no
    re-simulation — re-binned onto the 20 µm MAPS grid → 19,673-BX PixESL dataset
  - Track B (capability): port mdi_v2 into our own ddsim (MAPS_o1_v01_BIB_v2) to
    validate + enable detector variants (radius/pitch scans)
NOTES: Sensor geometry/material identical central↔BNL_MAPS; only readout pitch differs,
invisible to Geant4 — that is why Track A reuses the central SimHits unchanged.

## Slide 4 — The baseline dataset (Track A)
BULLETS:
- All 19,673 central bunch crossings converted — 394-job condor campaign, ZERO failures
- cellID decode (layer/module/sensor) + position re-segmentation to 20 µm; validated on
  native-pitch files (80% within one pixel)
- Deliverables: pixesl_ipc_LCC_V106p2_central.csv (BX, COL, ROW, h_time, qin) +
  row-aligned _extended.csv (+ layer/module/sensor/r/z)
- 17,141 raw SIM hits = 13,849 unique fired pixels; 8,240/19,673 BXs (42%) have ≥1 hit
NOTES: Published to the share with README + provenance; GHC V24.4 kept as superseded
reference. Same pixel-address convention as the qq physics sample → overlay is trivial.

## Slide 5 — Hits & occupancy per layer   [bib-studies summary]
PLOT: per_layer_h_avg_hits_x_layer            (left — avg hits/evt vs layer index; ROOT
                                               axis runs 0–5, but only 0–4 are real layers)
PLOT: per_layer_h_avg_occ_x_layer             (right — avg occupancy %/evt vs layer index)
BULLETS:
- Steep radial fall-off across the FIVE vertex-barrel layers: the innermost layer
  carries the load, the outer MAPS layers (3,4) are a thin slice of it
  << the VertexBarrel has 5 layers, indices 0-4:
       L0 r=13.7 mm | L1 r=23.7 mm | L2 r=34.0 mm   (inner barrel VTXIB, 25x25 um)
       L3 r=130 mm  | L4 r=315 mm                   (outer barrel VTXOB = our MAPS, 20x20 um)
     There is NO layer 5 — the bibstudies histograms just have a 6-bin ROOT axis
     (-0.5..5.5) and bin 5 is always empty. Never say "six layers". >>
- MAPS layers: L3 0.306 hits/BX (1.1e-4 hits/cm²/BX), L4 0.565 hits/BX (4.4e-5 hits/cm²/BX)
- Per cm², L3 is ~2.6× busier than L4 — the expected radial ordering (inner = noisier)
- L4 leads in RAW TOTALS (11,122 vs 6,019 hits) only because it is a bigger detector:
  ~4.8× more silicon area and twice the z-coverage
  (r 315.5 mm × half-length 326 mm  vs  r 131 mm × half-length 163 mm)
  << do NOT condense this to shorthand like "(~5× Si, 2× z)" — it reads as jargon and
     overflows the bullet; keep the two claims as two separate bullets >>
- ~4× (L3) / ~8× (L4) below the old GHC V24.4 baseline — the lattice + MDI update
  genuinely reduces vertex background
NOTES: avg_hits reads L0≈24 / L1≈8 / L2≈5 / L3≈0.3 / L4≈0.6; avg_occ reads L0≈27% /
L1≈3.3% / L2≈0.9% / L3,L4≈0 (a MAPS layer's per-event occupancy is negligible at 20 µm).
ALT PLOT: plots_LCC/hits_per_layer.png (MAPS-only raw totals, labelled 6,019 / 11,122).

## Slide 6 — Where the hits land   [HERO PICTURES — bib-studies hit maps]
PLOT: maps_hit_xy            (left — end-on x–y view: three concentric barrel rings)
PLOT: maps_hit_zr            (right — r–z cross-section: horizontal barrel bands)
BULLETS:
- End-on (x–y): the vertex barrel as concentric rings — a hot core (inner layers) and
  the two faint MAPS rings at r = 131 and 315.5 mm
- Cross-section (r–z): each horizontal band is one barrel layer, seen edge-on. The
  innermost bands glow; the two outermost bands — the MAPS layers at r = 131 and
  315.5 mm — are almost empty on the same colour scale
- Hit density falls steeply with radius: the outer layers live in a mild environment
  << avoid saying the MAPS bands are "below" the inner barrel — in an r-z plot they are
     the OUTERMOST bands (top/bottom of the frame). They are lower in DENSITY, not in
     position. Also note this map has a LINEAR colour scale, so don't quote orders of
     magnitude off it — use the log-scale rz_occupancy_vertex.png for that claim >>
- (Colour = hits per unit area per event; VertexBarrel collection only)
NOTES: These are the official drawhits maps. For the FULL tracker (barrel + forward
disks + drift chamber, log-scale hits/cm²/BX) use the custom r–z occupancy instead:
ALT PLOT: plots_LCC/rz_occupancy_vertex.png (shows disks + η guide-lines — great hero).
maps_hit_zphi is a good backup (z vs φ, shows the module segmentation stripes).

## Slide 7 — What makes the hits   [NEW — enabled by bib-studies]
PLOT: h_hit_particle_ID       (left — particle species producing the hits)
PLOT: h_hit_E_keV             (right — deposited energy per hit)
BULLETS:
- ~99% of background hits are e⁺/e⁻ — the IPC pairs and their soft EM secondaries;
  a per-mille tail of photons/neutrons, essentially no hadrons or muons
- Deposited energy per hit peaks at ~15 keV — a MIP-like Landau in the 50 µm sensor,
  tailing to ~150 keV
- Justifies the readout picture: a soft-electron field, well above a ~1 keV (≈278 e⁻)
  charge threshold but with a real sub-keV edep0 tail in the no-threshold CSV
NOTES: particle_ID bars: e-≈20.7, e+≈17.3 (arb. norm), gamma tiny. Companion spectra:
h_hit_particle_pt (secondary pT), h_hit_E_MeV / h_hit_E_eV (same edep, other ranges).
DO NOT use h_hit_particle_E — it renders blank (all secondaries are sub-GeV, off its
0–50 GeV axis); use particle_pt or the keV energy plot instead.

## Slide 8 — Sparse in space, structured in time
PLOT: hist_hit_t              (left — hit-time distribution, prompt peak + fast fall)
PLOT: h_occ_tot              (right — total fired-cell / occupancy distribution per BX)
BULLETS:
- Timing is prompt-dominated: a sharp peak near the crossing, falling within ~1–2 ns;
  L4 carries a later looper/backsplash population (see per-layer timing / TOF)
- Most BXs are empty (58%); mean 2.1 hits per non-empty BX, steeply falling, rare bursts
  to 112 hits — the tail the PixESL buffering must absorb
NOTES: hist_hit_t is in ns (peak ≲1 ns). For the split L3-prompt vs L4-late story the
custom TOF plot is clearer:
ALT PLOT: plots_LCC/h_time_hist.png (L3 prompt ~500 ps vs L4 late looper tail, ps axis).
ALT PLOT: plots_LCC/hits_per_event.png (hits/BX, mean 2.1, tail to ~100).
hist_hit_t_corr = TOF-corrected time (subtracts straight-line flight) if wanted.

## Slide 9 — Validated against the official analysis
PLOT: per_layer_h_avg_firing_cells_x_layer   (right — avg cellsFired/evt vs layer index)
BULLETS (table — avg firing cells/event, IPC@Z, LCC V106.2):
| layer | A. Ilg (FCC Week 2026) | this work |
| 0 (r 14 mm) | ~24   | 24.0 |
| 1           | ~7.5  | 7.8  |
| 2           | ~4.7  | 4.9  |
| 3 (MAPS)    | ~0.30 | 0.31 |
| 4 (MAPS)    | ~0.45–0.50 | 0.57 |
- Independent people, sample subset, and analyzer — agreement within plot-reading
  precision on ALL FIVE layers (Ilg used a 2,129-BX subset of the same events)
NOTES: Ilg, "Vertex backgrounds", FCC Week 2026:
https://indico.cern.ch/event/1552126/contributions/7128843/attachments/3290966/5884415/Vertex%20backgrounds_FCC%20Week%202026_Armin%20Ilg.pdf
This firing-cells plot IS the direct analogue of his per-layer bar chart.

## Slide 10 — Our own mdi_v2 chain, validated (Track B)
BULLETS:
- Ran the IDENTICAL GuineaPig crossings through our own MAPS_o1_v01_BIB_v2 ddsim over a
  400-BX validation batch
- Outcome ledger: 377 clean / 4 rescued by seed retry / 19 deterministic hangs
- With a matched 1 keV threshold the MAPS layers AGREE with the central sample:
  L3 ×1.28 (+1.8σ), L4 ×0.94 — the absolute scale we quote is anchored
- Inner barrel keeps a layer-dependent excess (+9/+23/+34% for L0/L1/L2) traced to an
  UNKNOWN central production config, not our geometry → common-mode for variant studies
NOTES: Validates Track B as the engine for the LDRD endgame — radius/pitch detector
variants now run on a trusted chain. (This slide is text/ledger; no bibstudies plot.)

## Slide 11 — Two findings for the MDI / software team
BULLETS:
- Finding 1 — Geant4 hangs in the mdi_v2 CAD geometry: ~4–5% of IPC crossings enter an
  endless navigation loop mid-event (no abort). DETERMINISTIC per event; reproduced with
  plain FTFP_BERT → geometry, not physics-list settings. (19/400 hung on both seeds.)
- Finding 2 — the central IPC sample is silently ~4% short: 19,673 sim files vs 20,501
  GuineaPig inputs (828 missing) — consistent with the same hangs being dropped silently
- A note with deterministic reproducers + a request for the exact central ddsim config is
  DRAFTED and ready to send (A. Ciarma / J. Eysermans / A. Ilg)
NOTES: draft at documents/BIB_MDI_V2_UPSTREAM_NOTE.md; ledger+seeds on SDCC
BIB_derived/sim/LCC_V106p2_v2_validation/ledger/.

## Slide 12 — LCC IPC study concluded
BULLETS:
- ✓ Baseline dataset delivered — per-BX PixESL stream on the 20 µm MAPS layers
  (L3 0.306, L4 0.565 hits/BX over all 19,673 crossings)
- ✓ Validated vs the official five-layer occupancy; ✓ own mdi_v2 chain agrees on MAPS
- ✓ Public: angli-share.web.cern.ch/FCC/MAPS/BIB_IPC_LCC/ (README + CSVs + plots)
- Next: radius/pitch detector-variant scan on the validated Track-B chain (LDRD endgame);
  PixESL readout studies on the stream; physics ⊕ BIB overlay with Z→qq; send the MDI note
NOTES: the qq physics stream (10k Z→qq) uses the identical CSV convention → overlay is a
concatenation + BX-window exercise.

---

# APPENDIX — bibstudies_LCC PLOT CATALOGUE
<!-- All names below take prefix `ipc_lcc_19673evt_` and suffix
     `_VertexBarrelCollection.png`. Local dir: outputs/BIB/bibstudies_LCC/.
     69 png + 69 pdf + merged ROOT + detector dict live there. -->

## RECOMMENDED — per-layer summaries (headline / validation)
| stem | shows | one-line caption |
|---|---|---|
| per_layer_h_avg_hits_x_layer | avg hits/evt vs layer index (0–4 real; bin 5 always empty) | steep radial fall-off; L0≈24 → L4≈0.6 |
| per_layer_h_avg_firing_cells_x_layer | avg fired cells/evt vs layer | the validation plot (matches A. Ilg) |
| per_layer_h_avg_occ_x_layer | avg occupancy [%] /evt vs layer | L0≈27% → MAPS layers ≈0 at 20 µm |

## RECOMMENDED — spatial "pictures" (hit maps)
| stem | shows | one-line caption |
|---|---|---|
| maps_hit_xy | end-on x–y density | concentric barrel rings; hot core + faint MAPS rings |
| maps_hit_zr | r–z density | horizontal barrel bands; density collapses with radius |
| maps_hit_zphi | z vs φ density | central bright band + module-segmentation stripes |
| maps_hit_E_MeV_map / _keV_map / _eV_map | energy-weighted x–y map | where the energy is deposited (3 ranges) |
| maps_hit_particle_ID_map | dominant species per cell | e± everywhere |
| maps_hit_t_corr_map | TOF-corrected time map | timing structure across the map |

## RECOMMENDED — spectra (what the hits are)
| stem | shows | one-line caption |
|---|---|---|
| h_hit_particle_ID | species producing hits | ~99% e⁺/e⁻, per-mille γ/n |
| h_hit_E_keV | deposited energy/hit [keV] | MIP-like Landau, peak ~15 keV, tail ~150 keV |
| h_hit_E_MeV / h_hit_E_eV | same edep, other ranges | use keV for the readable peak |
| h_hit_particle_pt | secondary pT | soft spectrum |
| h_hit_particle_eta / h_hit_eta | (particle / hit) η | barrel acceptance |
| h_hit_r_mm / h_hit_z_mm / h_hit_x_mm / h_hit_y_mm | hit position projections | layer radii show as spikes in r |

## RECOMMENDED — timing & occupancy distributions
| stem | shows | one-line caption |
|---|---|---|
| hist_hit_t | hit time [ns] | sharp prompt peak, falls within ~1–2 ns |
| hist_hit_t_corr | TOF-corrected time | straight-line flight subtracted |
| h_occ_tot | total occupancy / BX | per-crossing spread |

## RECOMMENDED — per-layer detail (backup / technical slides)
| stem (…layerN…) | shows | note |
|---|---|---|
| per_layer_h_hit_rateDensity_layerN_VS_eta | rate density [MHz/cm²] vs |η| | flat across barrel |η|≲0.9, sharp cut at layer edge. ⚠ ABSOLUTE SCALE: the bib-studies MHz/cm² here does NOT match the CSV-audited per-area rate (different normalization) — use for SHAPE only; quote the audited hits/cm²/BX for numbers. |
| per_layer_hist_phi_density_vsN | φ density per layer | L4 shows periodic module gaps |
| per_layer_hist_z_density_vsN_mm | z density per layer | flat-ish over the ladder length |
| per_layer_hist_xy_vsN / hist_zphi_vsN | per-layer x–y / z–φ maps | single-layer versions of the maps above |
| per_layer_h_occ_x_layerN | occupancy dist. for layer N | tails for the busy inner layers |
| per_layer_h_avg_hits_x_layerN_x_module | avg hits vs module id, layer N | module-level uniformity / gaps |

## ⚠ AVOID — empty or misleading (do NOT put on slides)
- h_hit_particle_E — renders BLANK (secondaries are sub-GeV, off the 0–50 GeV axis).
  Use h_hit_particle_pt or h_hit_E_keV instead.
- per_layer_h_avg_pu_x_layer — EMPTY (entries = 0; pile-up not computed here).
- h_tot_pu, per_layer_h_pu_x_layerN — same pile-up family, EMPTY.

## NORMALIZATION REMINDER (tell ppt-Claude)
The bib-studies plots are per-event–weighted over the full 19,673-BX statistics and are
the right SHAPES/PICTURES. For any QUOTED NUMBER (hits/BX, hits/cm²/BX, ratios,
occupancy) use the AUDITED HEADLINE block at the top of this file — it was recomputed
straight from the delivered CSV. Where a bib-studies axis (notably rateDensity MHz/cm²)
disagrees with the audited value, the audited value wins on the slide.
