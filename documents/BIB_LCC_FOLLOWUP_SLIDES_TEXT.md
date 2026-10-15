# SLIDE SOURCE — MAPS/PixESL: follow-up to the 4 Aug 2026 comments on the LCC IPC background
<!-- Same convention as BIB_LCC_SLIDES_TEXT.md: one H2 = one slide, BULLETS go on the slide,
     NOTES are speaker notes, PLOT lines name image files.
       new plots (explicit axes):   outputs/BIB/plots_LCC_truth/<name>.png
       bib-studies plots, relabelled: outputs/BIB/bibstudies_LCC_labelled/<name>.png
       event displays:              fcc_maps_wrapper_pixesl/results/bib_ipc_lcc_truth/event_displays/<name>.png
       web: https://angli-share.web.cern.ch/FCC/MAPS/BIB_IPC_LCC/truth_ntuple/{plots,bibstudies_labelled,event_displays}/
     Slide numbers of the 4 Aug deck refer to the PDF as presented (2026_08_04_MAPS.pdf).
     Numbers come from outputs/BIB/plots_LCC_truth/summary_numbers.md (all 19,673 BX) and from the two
     studies behind it (axis audit; why L4 > L3); each was re-derived independently and the whole text
     fact-checked. Errors are BX-to-BX (bursts included).
     BIB_LCC_SLIDES_TEXT.md numbers its slides one lower from "Where the hits land" on, because the
     presented deck has an extra slide (the geometry table).
     Suggested footer: "IPC @ Z · LCC V106.2 · central mdi_v2 simulation · 19,673 BX · SimTrackerHits, 1 keV simulation cut"
     NOT "no threshold": see slide 5.
     Built deck: 2026_10_06_MAPS.pptx (+ .pdf render) at the workspace root, generated from this file by
     documents/build_bib_followup_deck.py on the BNL template 2026_08_04_MAPS.pptx; the appendix is slides 14-15. -->

## Slide 1 — Title
Beam-induced background for the MAPS vertex demonstrator — answers to the 4 Aug comments
What the axes mean · why layer 4 is above layer 3 · ROOT files for event displays
Ang Li, Chris Rasmussen, Punit Sharma — LDRD WP1

## Slide 2 — The two comments and the short answers
BULLETS:
- "Do all the Y axes make sense?" — Of the nine plots shown, two are right as labelled and three only lack labels or units. The two "occupancy" plots are not occupancies and the two hit maps are not densities. Every axis is now defined and checked against an independent recount; 54 of the 69 histograms are redrawn with correct labels.
- "Why is layer 4 higher than layer 3 — low-pT loopers?" — It is real, but it is not loopers. 94% of the layer-4 hits are made by sub-MeV secondary electrons, not by particles from the beam line; about half are tagged directly as photons absorbed in the silicon. Per cm² they are only 39% rarer on layer 4 than on layer 3, and layer 4 has 4.4 times more silicon.
- The calculation from field and geometry: a particle needs pT > 39 MeV to reach layer 3 and > 95 MeV to reach layer 4. Per bunch crossing 0.024 and 0.0036 primaries do, and the simulation confirms them one by one.
- With a pT cut of 1 MeV on the track that makes the hit: layer 3 has 0.103 and layer 4 has 0.028 hits per crossing — the expected order.
- ROOT files with all hits and their truth, plus an event-display script, are public.
NOTES: "Primaries" = the e+/e- pairs from GuineaPig, about 1,120 per bunch crossing, median pT 1 MeV.

## Slide 3 — Y axes of the plots shown on 4 Aug
BULLETS (table):
| 4 Aug slide | plot | axis as shown | what it is | verdict |
|---|---|---|---|---|
| 5 left | h_avg_hits_x_layer | avg hits/evt | SimTrackerHits per bunch crossing, summed over the whole layer | correct; a layer total, not a density |
| 5 right | h_avg_occ_x_layer | avg occupancy/evt [%] | 100 × fired pixels ÷ number of sensors | not an occupancy |
| 7 left | hit_xy | hits/(11×11) mm² per event | hits per crossing in an 11.28 mm map cell of the end-on projection, summed along z | not a density |
| 7 right | hit_zr | hits/(8×11) mm² per event | hits per crossing in an 8.64 × 11.28 mm cell; "r" is r × sign(x), one band = half a layer | not a density |
| 8 left | h_hit_particle_ID | (none) | hits per crossing by species of the stored MC particle the hit is linked to | label missing; names the ancestor |
| 8 right | h_hit_E_keV | hits | hits per crossing per keV, five layers summed | unit missing; describes L0–L2 |
| 9 left | hist_hit_t | (none) | hits per crossing per 0.1 ns, five layers summed, 0–20 ns | label missing; hides the late MAPS hits |
| 9 right | h_occ_tot | (none) | fraction of crossings per bin of 100 × fired pixels ÷ 4,870 sensors | not an occupancy |
| 10 | h_avg_firing_cells_x_layer | avg cellsFired/evt | distinct fired pixels per crossing (25 µm inner, 50×150 µm outer) | correct; the table beside it was not |
- "evt" always means one bunch crossing. A "hit" is one Geant4 track in one sensor, not a particle and not a pixel.
- Every filled histogram closes bin by bin against an independent recount from the truth ntuple, which matches the raw files hit by hit.
NOTES: The missing labels come from how the plots were drawn: drawhits.py sets readable axis titles only in its own draw step, and our merged redraw used the titles stored in the histograms. All 69 histograms are audited in the appendix; 54 are redrawn with correct titles in bibstudies_LCC_labelled/; 15 are not redrawn: 9 empty, 4 broken by a module-axis offset, 2 uninformative (listed in SKIPPED.md).
PLOT: bibstudies_LCC_labelled/h_avg_hits_x_layer   (same plot as slide 5 left, relabelled)

## Slide 4 — "Occupancy [%]" was fired pixels divided by sensors
PLOT: plots_LCC_truth/occupancy_per_layer
BULLETS:
- bib-studies counts distinct cellIDs (pixels in this sample) and divides by the number of sensors. Layer 0: 24.0 fired pixels ÷ 90 sensors = 26.7 "%".
- True pixel occupancy per bunch crossing (fired pixels ÷ all pixels): 8.1e-7 in layer 0 (25 µm pixels), 6.9e-9 in layer 3 and 2.6e-9 in layer 4 (the 50×150 µm pixels of the sample).
- At the 20 µm MAPS pitch: 3.8e-10 (layer 3) and 1.5e-10 (layer 4).
- Sensors with at least one hit per crossing: 27.7 of 4,870 (0.57%), not "0.8% of modules". Layer 3: 0.23 of 736. Layer 4: 0.41 of 3,264.
- 85% of crossings leave layer 3 empty and 68% leave layer 4 empty.
NOTES: The "27%" would even exceed 100% for one crossing (95 pixels in 90 sensors). These occupancies count one pixel per hit: no charge sharing or cluster size is simulated.

## Slide 5 — Corrections to statements on the 4 Aug slides
BULLETS:
- "Raw SIM hits, no threshold" → the central simulation drops every Geant4 step below 1 keV. No hit is below 1 keV; there is no sub-keV tail in the CSV.
- "MIP-like Landau, peak ~15 keV" → true for layers 0–2. On the MAPS layers 20% (L3) and 29% (L4) of the hits deposit 1–2 keV.
- "~99% of hits are e+/e-" → that is the species of the stored ancestor. On layer 4 only 6% of the hits are made by that particle itself.
- "Timing is prompt, within 1–2 ns" → true for the five-layer sum. Median hit time is 4.4 ns on layer 3 and 7.0 ns on layer 4; 9% and 13% arrive after the next crossing (27 ns).
- "Per cm² L3 is ~2.6× busier; L4 has ~4.8× more silicon" → 2.40× and 4.43× with the sensitive area (2.6 and 4.8 are for bare cylinders).
- "Validated against the official analysis, independent analyzer" → the reference chart is the same events and the same script with a 1.8 keV threshold; we reproduce it exactly (78,506 entries in the first 2,129 crossings).
NOTES: Like-for-like table for the validation slide, SimTrackerHits per crossing, L0…L4:
Same 2,129 BX and 1.8 keV cut as A. Ilg (his chart has 78,506 entries, which we reproduce exactly); our values for that subset: 24.00 / 7.55 / 4.65 / 0.279 ± 0.042 / 0.390 ± 0.017.
This work, all 19,673 BX, 1.8 keV: 24.05 / 7.73 / 4.82 / 0.246 / 0.404. Without the threshold: 24.32 / 7.91 / 4.98 / 0.306 / 0.565.
The old "this work" column (24.0 / 7.8 / 4.9 / 0.31 / 0.57) mixed fired cells and hits. Layer 4 is above layer 3 in his subset too (0.39 vs 0.28).
Hit rates on sensitive silicon: 1.13e-4 (L3) and 4.70e-5 (L4) hits/cm²/BX = 4.2 and 1.7 kHz/cm² at 37.04 MHz (the crossing rate assumed for LCC V106 in A. Ilg's talk).

## Slide 6 — The calculation: which primaries can reach each layer
PLOT: plots_LCC_truth/helix_prediction_vs_sim
BULLETS:
- In a 2 T field a particle from the beam line reaches radius r only if pT [GeV] > 0.15 × B [T] × r [m]: 39 MeV for layer 3 (131 mm), 95 MeV for layer 4 (316 mm). Below about 600 MeV it cannot leave the tracker radially: it loops unless it leaves along z.
- Each of the 22 million primaries was propagated as a helix from where GuineaPig hands it over. Reaching the layer inside its length, per crossing: 0.024 (layer 3) and 0.0036 (layer 4).
- The simulation agrees particle by particle: 91% (L3) and 86% (L4) of the predicted primaries leave a hit there; the misses are explained by sensor gaps and energy loss.
- So field and geometry put layer 4 about seven times below layer 3. The simulation has it 1.85 times above.
NOTES: Counting also the return arc and later turns of loopers in vacuum, the calculation still puts layer 4 three to seven times below layer 3. Most primaries with high pT are very forward and leave along z: 41 per crossing have enough pT for layer 3, but only 0.06% of them cross it inside its length. The helix code was checked against a brute-force stepper and re-implemented independently (identical counts in all 19,673 BX). The field in the barrel is 2 T to within 1% (solenoid plus anti-solenoid map), and so are the thresholds.

## Slide 7 — What makes the hits
PLOT: plots_LCC_truth/hits_per_layer_by_origin
PLOT: plots_LCC_truth/pt_spectrum_L3_L4
BULLETS:
- Layer 3: 0.306 hits per crossing = 0.108 from charged particles that are stored in the truth + 0.198 from sub-MeV secondary electrons (65%).
- Layer 4: 0.565 = 0.033 + 0.532 (94%).
- Hits made by the stored charged particles follow the expected order: three times fewer on layer 4 (six times fewer for the primaries themselves). The whole excess is in the sub-MeV electrons.
- 82% of the layer-3 hits and 97% of the layer-4 hits are made by tracks below the pT needed to reach the layer.
NOTES: "Sub-MeV secondary" = a track created in the simulation below 1 MeV; these are not stored in the truth record, the hit is flagged, and its momentum is known from the hit itself. Blue = the GuineaPig primary itself, orange = a stored secondary (> 1 MeV).

## Slide 8 — The pT cut
PLOT: plots_LCC_truth/hits_vs_ptcut
BULLETS (table, SimTrackerHits per crossing):
| cut on the pT of the track at the hit | layer 3 | layer 4 | L4 / L3 |
|---|---|---|---|
| none | 0.306 | 0.565 | 1.85 ± 0.06 |
| > 1 MeV | 0.103 | 0.028 | 0.27 ± 0.05 |
| > 10 MeV | 0.087 | 0.022 | 0.26 ± 0.05 |
| > the layer's own reach threshold (39 / 95 MeV) | 0.055 | 0.018 | 0.34 ± 0.05 |
- A pT cut does restore the expected order. It works because it removes the keV electrons, not because it removes loopers.
- It is a truth-level cut. A charge threshold does not do the same: above 1,000 e⁻ (3.6 keV) the ratio is still 1.61.
NOTES: The stored hit momentum is the mean of entry and exit momentum, so for an electron that stops in the sensor it is half the entry value; this only matters for cuts below 1 MeV. A cut at the generator level on the pT of the primary behind the hit gives 1.76 (> 1 MeV), 1.64 (> 5 MeV), 0.87 (> 10 MeV), 0.31 (> 20 MeV): the layer-4 hits do descend from low-pT pairs (median 5 MeV), but those pairs never reach layer 4; they act through the radiation they produce where they hit material. For a common cut above 95 MeV layer 4 is higher again (1.5 ± 0.1): the few loopers that do reach it cross the twice longer layer more often (0.018 vs 0.012 hits per crossing).

## Slide 9 — What does and does not change the order
PLOT: plots_LCC_truth/ratio_summary
BULLETS:
- Layer 4 stays above layer 3 however hits are counted: fired 20 µm pixels (0.445 vs 0.259), with a charge threshold, within one bunch spacing.
- Limiting layer 4 to the length of layer 3 brings it just below (0.27 vs 0.31): both the larger circumference and the doubled length are needed.
- Only truth-level selections of charged particles (stored particle, or track pT > 1 MeV) bring the ratio down to the 0.15–0.3 expected for particles from the beam line.
NOTES: L4 − L3 = 0.259 ± 0.012 hits per crossing, 21 standard deviations above zero, and not carried by a few crossings: removing the 20 busiest crossings raises L4/L3 to 2.0, because the bursts (loopers) sit mainly on layer 3. A very early window also reverses the order (hits before 2 ns: 0.115 vs 0.065), partly by geometry: light needs 1.0 ns to reach layer 4. Relative to the light time of flight, layer 3 is higher only for windows up to about 1.5 ns; the layer-4 excess arrives later.

## Slide 10 — The sub-MeV electrons are made by photons in the silicon
PLOT: plots_LCC_truth/density_vs_radius
PLOT: plots_LCC_truth/edep_L3_L4
BULLETS:
- About two thirds start and stop inside the 50 µm sensor: 29% are 1.6 keV silicon Auger electrons and 35–39% are electrons of a few tens of keV (median 17 keV) whose deposited energy equals their kinetic energy. The rest cross a sensor face.
- About half are tagged directly as photon absorptions: a photo-electron plus the Auger electron at the same point. The Auger electrons are 19% (L3) and 27% (L4) of all "hits".
- From layer 3 to layer 4 their density per cm² falls to 0.61 of its value; for charged-particle hits it falls to 0.07. On the silicon wrapper at 2 m it is still half the layer-4 value.
- Hits ∝ photon field × silicon: layer 4 has 2.2 times the silicon per unit length and twice the length of layer 3.
NOTES: Where the primaries behind these hits end (the photons are often emitted upstream of that point, or arrive after a detour): forward pairs (median 130 MeV, 33 mrad) follow the field along the beam pipe and shower in it — conical beam pipe at |z| = 0.28–1.16 m (27% of the layer-4 soft hits), front of the compensating-solenoid cryostat beyond 1.39 m (19%), the tip of the copper "crotch" where the beam pipes separate at 1.32 m (18%), copper pipes behind and before it (20%), LumiCal (5%). About 30% of the layer-4 soft hits arrive later than 14 ns; for the 18–24 ns peak (13%) timing and direction show radiation returning from the outer detector (the outer barrel at R ≈ 2 m or the endcap-calorimeter face at |z| ≈ 3 m; the truth record cannot separate them). The photons themselves are not in the truth record (below 1 MeV nothing is stored), so the photon origin is an inference from the Auger pairs, the uniform depth in the silicon, the isolation from any charged track and the timing.
This component depends on simulation choices: 50 µm sensitive thickness (it is a volume effect), Auger emission on, the 1 keV cut, and the CAD model of the beam pipe.

## Slide 11 — Loopers exist, but they sit mostly on layer 3
PLOT: event_displays/bib_display_bx217846_full   (whole tracker: one positron spiralling in the drift chamber)
PLOT: event_displays/bib_display_bx100003        (ordinary crossing with a MAPS hit: one isolated soft hit on layer 4; 58% of crossings have no MAPS hit at all)
PLOT: event_displays/bib_display_bx566681        (rare, 0.3% of crossings: one 127 MeV primary crossing layers 3 and 4)
BULLETS:
- Second and later crossings of a looping particle are 23% of the layer-3 hits and 3.6% of the layer-4 hits.
- They make the bursts: the busiest 1% of crossings hold 30% of the hits on layer 3 but 10% on layer 4.
- The busiest crossing (112 MAPS hits) is one 477 MeV positron with almost no pz: 75 hits on layer 4 and 24 on layer 3 over 1.4 µs, and 4,000 drift-chamber hits.
NOTES: A looper that reaches layer 4 does cross it more often than layer 3 because layer 4 is twice as long (265 vs 182 hits for the 70 primaries that reach it). That is the reviewers' mechanism; it is worth +0.004 hits per crossing, 1.6% of the difference.

## Slide 12 — ROOT files for event displays
BULLETS:
- https://angli-share.web.cern.ch/FCC/MAPS/BIB_IPC_LCC/truth_ntuple/ (README, files, script, examples)
- ipc_LCC_V106p2_central_truth_vertex.root (117 MB): every vertex hit of all 19,673 crossings with position, time, deposited energy, momentum (and the 20 µm pixel address on the MAPS layers), and the truth: particle barcode, species, origin, primary ancestor.
- ipc_LCC_V106p2_central_truth.root (574 MB): the same for the whole tracker (Si wrapper, drift chamber).
- bib_event_display.py: needs only uproot and matplotlib. `--bx 217846 --tracks`, `--tmax 27`, `--busiest 5`, `--full`.
- 12 original EDM4hep files (the 6 crossings with most MAPS hits and 6 ordinary ones) for Key4hep displays; the full set is on EOS.
NOTES: The barcode column is the truth label asked for AI training (unique per stored particle). For track-finding truth use hits with by_secondary == 0. On layers 3 and 4 the other hits are isolated (97–99.8% have no charged-track hit within 1 mm); on layers 0–2 a quarter to a half of them accompany a track. The displays show all hits of a simulated crossing whatever their time; --tmax 27 keeps one bunch spacing. Plain ROOT works too: hits->Draw("y:x","bx==217846 && det==0").

## Slide 13 — What this means for the MAPS study, and open points
BULLETS:
- Readout load on the MAPS layers: 0.26 (L3) and 0.44 (L4) fired 20 µm pixels per crossing, mostly isolated hits of several thousand electrons. A charge threshold does not remove them; being isolated, they should be rejected by pattern recognition (not tested here).
- The inner layers are different: 85–91% of their hits are real charged-particle crossings.
- The soft-photon component must be checked against thickness, Auger setting and the beam-pipe model before it is used for design numbers.
- Caveats of the central sample to keep in mind: 1 keV per-step cut (charge 10–20% low below 100 MeV), merged re-entry hits, truth stored only above 1 MeV, 828 of 20,501 crossings missing, no charge sharing between pixels.
- Next: re-simulate a subset with full truth and no step cut; SR background; PixESL on the stream with the late hits moved to their crossing.
NOTES: For a full-truth re-simulation `--part.keepAllParticles` alone does nothing with the default particle handler; it needs SIM.part.userParticleHandler = "" (or minimalKineticEnergy = 0), and SIM.filter.tracker = "edep0". The exact central ddsim configuration is stored in the `runs` tree of every central file.

---

# APPENDIX — axis audit of all 69 bib-studies histograms (VertexBarrelCollection)
<!-- "hits" = SimTrackerHits; hit-level histograms are filled with weight 1/19,673 per hit, so their contents are hits
     per bunch crossing per bin; the occupancy, firing-cell, rate-density and pile-up families are per-crossing or
     specially weighted quantities, as listed.
     Relabelled versions: outputs/BIB/bibstudies_LCC_labelled/<name>.png -->

| histogram | y (or colour) axis really is | verdict |
|---|---|---|
| h_avg_hits_x_layer | hits per crossing, whole layer. Stored error bars are 1.6–3.2× too small (hits come in bursts). The sixth bin is not a layer | correct |
| h_avg_firing_cells_x_layer | distinct fired pixels per crossing at the sample's segmentation (L3 0.249, L4 0.418; at 20 µm 0.259, 0.445) | correct |
| h_avg_occ_x_layer | 100 × fired pixels ÷ number of sensors | not an occupancy |
| h_occ_x_layer0–4, h_occ_tot | fraction of crossings per log-spaced bin of the same ratio, drawn on a linear axis | not an occupancy |
| h_avg_hits_x_layer0_x_module | hits per crossing per module | correct |
| h_avg_hits_x_layer1–4_x_module | module axis shifted: 38% (L1), 61% (L2), 100% (L3, L4) of the hits in the underflow | broken |
| h_tot_pu, h_avg_pu_x_layer, h_pu_x_layer0–4 | pile-up was not computed | empty |
| hit_xy, hist_xy_vs_layer0–4 | hits per crossing per 11.28 mm square of the end-on projection, summed along z. Read as a density it is 13–43× too high | not a density |
| hit_zr | hits per crossing per 8.64 × 11.28 mm cell; r carries the sign of x; one cell = half a ring. Compresses the radial fall-off (L0/L3 looks 126:1, is 1,169:1) | not a density |
| hit_zphi | hits per crossing per (8.64 mm × 0.0707 rad) cell, five layers on top of each other; stored axis titles swapped | mislabelled |
| hist_zphi_vs_layer0–4 | the same for one layer; proportional to a real density (one cell = 0.81 cm² on L3, 1.79 cm² on L4). Too finely binned for L3/L4 (< 2 hits per cell) | labels missing |
| h_hit_E_keV | hits per crossing per keV, five layers. Empty below 1 keV (simulation cut); line at 1.5–1.75 keV = silicon Auger electrons | unit missing |
| h_hit_E_MeV, h_hit_E_MeV_map | 100 keV bins: 90% of the hits in the first bin | uninformative |
| h_hit_E_eV, h_hit_E_eV_map | covers 0–1 keV, below the simulation cut | empty |
| h_hit_E_keV_map | hits per crossing per keV, by layer (not a spatial map) | labels missing |
| h_hit_particle_ID, h_hit_particle_ID_map | hits per crossing by species of the linked stored MC particle (the nearest stored ancestor) | labels missing |
| h_hit_particle_pt, h_hit_particle_E, h_hit_particle_ID_E_MeV | properties at production of that linked particle, in GeV with 0.1 GeV bins (97–99.8% in the first bin); not the particle at the sensor | misleading |
| h_hit_particle_eta | direction (η) at production of that linked particle, hits per crossing per 0.1; not the direction at the sensor (median |η| 1.7 for L3 hits, 3.2 for L4 hits) | mislabelled |
| hist_hit_t | hits per crossing per 0.1 ns, 0–20 ns; 16% (L3) and 23% (L4) of the hits are beyond the axis | labels missing |
| hist_hit_t_corr, hist_hit_t_corr_map | hit time minus light time from the origin; negative for 47% of the hits because the pairs do not start at the origin; the map version starts at 0 and loses them | labels missing / misleading |
| h_hit_x_mm, h_hit_y_mm, h_hit_z_mm, h_hit_r_mm, h_hit_eta | hits per crossing per bin (0.11 mm, 0.086 mm, 0.05); "r" is signed by x | unit missing |
| h_hit_rateDensity_layer0–4_VS_eta | hits/BX/cm² of an ideal cylinder × 52 MHz × 3 (safety) × 5 (cluster size): 19–23× the simulated hit rate at 37.04 MHz | misleading |
| hist_z_density_vs_layer0–4_mm, hist_phi_density_vs_layer0–4 | hits per crossing per 8.64 mm (z) or 0.0707 rad (φ) bin; not divided by area | labels missing |
