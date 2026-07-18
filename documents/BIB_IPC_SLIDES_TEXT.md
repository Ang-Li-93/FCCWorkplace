# SLIDE SOURCE — MAPS/PixESL: IPC beam-induced background production
<!-- Instructions for the slide-making assistant ("ppt Claude"):
  - One H2 (##) = one slide. "BULLETS" go on the slide; "NOTES" are speaker notes.
  - "PLOT:" lines name image files to place. All exist in BOTH pdf and png at:
      web:   https://angli-share.web.cern.ch/FCC/MAPS/BIB_IPC/{plots,bibstudies}/
      local: /gpfs/mnt/gpfs01/usfcc/ali3/FCCWorkplace/outputs/BIB/{plots,bibstudies}/
    Use the .png files for slides.
  - Numbers are final and audited; do not round beyond what is written.
  - Suggested footer on every slide: "GHC V24.4 IPC @ Z, raw SIM hits, no threshold"
-->

## Slide 1 — Title
Beam-Induced Background for the MAPS Vertex Demonstrator
IPC production on the ALLEGRO-based BNL_MAPS detector — first PixESL background stream
Ang Li (BNL) — LDRD WP1: AI-Enabled Tracking Demonstrator for FCC-ee
NOTES: 3,996 bunch crossings of the official reference IPC sample through full
Geant4, delivering per-BX pixel hit streams for the PixESL readout simulation.

## Slide 2 — Why beam background drives the MAPS design
BULLETS:
- At the FCC-ee Z pole, backgrounds arrive EVERY bunch crossing (~20 ns);
  physics events are rare — occupancy & readout bandwidth are set by background
- Dominant source for the vertex region: Incoherent Pair Creation (IPC) —
  e+e- pairs from beam-beam interaction, O(1000) per BX, spiraling in the 2 T field
- Goal: real per-BX background hit streams for PixESL (SystemC readout sim)
  on the 20×20 µm MAPS outer vertex layers (r = 131 / 315.5 mm)
NOTES: Other sources (synchrotron radiation, beam-gas, radiative Bhabha,
injection) exist in the same MDI sample space — future work; IPC first because
it dominates vertex occupancy.

## Slide 3 — Inputs: official MDI reference samples
BULLETS:
- Full MDI BIB sample tree mirrored from CERN EOS to SDCC: 253 GB, 157k files
  (/eos/project/f/fcc-ee-mdi/BIB → gpfs, kept read-only)
- IPC reference: GHC V24.4, Z pole — GuineaPig (A. Ciarma), 3,996 bunch
  crossings, 1 file = 1 BX, ~1,350 pairs/BX
- Pre-2026 files: particle vertices reset to (0,0,0) (GuineaPig has no solenoid
  field) — official bib-studies prescription
NOTES: Two lattice designs exist (GHC = Oide, LCC = Raimondi); reference
blessed by MDI group for IPC is GHC V24.4. LCC V106.2 (20,501 BXs) available
locally for a future comparison — background levels are lattice-dependent.

## Slide 4 — Simulation workflow
BULLETS:
- Chain: .pairs (1 BX) → ddsim (Key4hep 2026-04-08, DD4hep 1.36) → EDM4hep →
  PixESL CSV (BX, COL, ROW, h_time, qin)
- Detector: BNL_MAPS = ALLEGRO_o1_v03 with outer vertex barrel re-pitched to
  20×20 µm MAPS (everything else stock)
- BIB-specific setup (HEP-FCC/bib-studies recipe): CAD-imported beampipe,
  world = vacuum, FTFP_BERT_EMZ, 0.05 mm range cut, low-energy EM
  (50 eV cut edge, Auger), NO hit-energy threshold (edep0)
- HTCondor at SDCC: 800 jobs × 5 BX, per-BX reproducible seeds,
  atomic outputs, per-step resume; adversarially audited workflow
NOTES: Audit (multi-agent) found and fixed: BX-id bug in converter, per-file
pixel-frame bug, seed not varying, non-atomic writes, harvest coverage bug.
CAD beampipe causes ~1% transient Geant4 stuck-track aborts — automatic
retry (alternate deterministic seed); only 1 BX of 3,996 needed it.

## Slide 5 — Production summary
BULLETS:
- 3,996 / 3,996 bunch crossings complete (zero missing; coverage verified)
- ~10 min/BX (8.5 ddsim + 1.5 conversion); ~8 h wall on ~100 slots
- Deliverables: pixesl_ipc_GHC_V24p4_Z.csv (+ extended with
  layer/module/sensor/r/z, row-aligned)
- 23,926 raw SIM hits = 14,958 unique fired pixels; 2,909/3,996 BXs have ≥1 hit
- Same local pixel-address convention as the qq sample: COL∈[0,930), ROW∈[0,990)
NOTES: 1,087 BXs have zero MAPS-layer hits — legitimately empty, counted in
all per-BX rates (divide by 3,996). Byte-identical determinism verified: any
BX reproduces exactly from its logged seed.

## Slide 6 — Hit rates per layer (full vertex barrel)
PLOT: bibstudies/ipc_avg_hits_x_layer_400evt_VertexBarrel.png (left)
PLOT: plots/hits_per_layer.png (right)
BULLETS:
- Inner barrel (stock IDEA/ALLEGRO, layers 0–2): 34 / 12 / 8 hits/BX
- MAPS layers: L3 (r=131 mm) 1.32 hits/BX; L4 (r=315.5 mm) 4.67 hits/BX
- Peak rate density layer 0: ~235 MHz/cm² (published: "up to 200 MHz/cm²") —
  our chain reproduces the official inner-barrel picture
NOTES: hits_per_layer.png shows RAW TOTALS on the two MAPS layers — see
slide 8 for why L4 > L3 is expected in this metric.

## Slide 7 — Occupancy maps and timing
PLOT: plots/rz_occupancy_vertex.png (left)
PLOT: plots/h_time_hist.png (right)
BULLETS:
- r–z occupancy: hits/cm²/BX across the vertex region (400 BXs of raw sim)
- Hit times: median 9.3 ns (L3) / 14.3 ns (L4) — far beyond the ~1 ns
  straight-line TOF: background is dominated by loopers & backsplash, not
  prompt tracks; tails reach ~2.2 µs
- Rate densities (mean): L3 0.42 MHz/cm², L4 0.28 MHz/cm² — ~300× below the
  innermost layer: MAPS layers live in a mild environment
NOTES: occupancy_map_L3/L4.png (pixel-level) and hitdensity_vs_z /
rate_per_layer / occupancy_vs_window plots available in the same folder for
backup slides.

## Slide 8 — Why layer 4 collects more raw hits than layer 3
PLOT: plots/rate_per_layer.png (or hitdensity_vs_z.png)
BULLETS:
- Raw totals: L4/L3 = 3.54 — fully decomposed as
  (4.4–4.8× more silicon area) × (0.73–0.80× per-area rate)
- Per cm², layer 4 is ~25% QUIETER than layer 3 (expected radial ordering)
- Prompt hits (h_time < 2 ns) obey the solid-angle expectation: L4/L3 = 0.74
- The totals excess is late: MeV-electron loopers/backsplash leaving 3–31-hit
  strings; 52.6% of L4 hits sit at |z| > 163 mm — beyond L3's entire z-extent
NOTES: 7-probe independent audit (raw-file recounts with independent decoders,
geometry/sensor arithmetic, converter review, threshold/window scans, qq
cross-check, sim settings, official references): unanimous "physics, not bug".
5 busiest BXs: 133 hits from just 14 particles. Ratio invariant (3.4–3.6)
under every threshold/window/dedup; drops to 2.85 at unique-particle level.

## Slide 9 — Validation against the official analysis
BULLETS (table):
| layer | official (A. Ilg, Jan 2026) | this work |
| 0 | 34.3 hits/BX | ~34 |
| 1 | 12.1 | ~12 |
| 2 | 8.0 | ~8 |
| 3 | 1.37 | 1.32 |
| 4 | 4.71 | 4.67 |
- Independent people, samples, geometry files, analyzer — agreement ~4% on all
  5 layers (same convention: raw SIM hits, no threshold, IPC@Z, GHC lattice)
- Official TDAQ team independently flagged the same effect (Nov 2025):
  "IPC barrel occupancy inflation, maybe due to loopers!"
NOTES: links —
Ilg (match): https://indico.cern.ch/event/1588696/contributions/6856981/attachments/3208537/5714124/Studies%20of%20backgrounds%20in%20vertex%20detectors_Armin%20Ilg.pdf
TDAQ looper note: https://indico.cern.ch/event/1583755/contributions/6727403/attachments/3168257/5631576/FCC-TDAQ%20workshop%20ALLEGRO%20occupancy%20studies.pdf
Lattice dependence (Ilg FCC Week 2026, LCC v106.2: L3=L4=0.31 hits/BX):
https://indico.cern.ch/event/1552126/contributions/7128843/attachments/3290966/5884415/Vertex%20backgrounds_FCC%20Week%202026_Armin%20Ilg.pdf

## Slide 10 — Caveats & conventions (how to quote these numbers)
BULLETS:
- Label: "GHC V24.4 IPC @ Z, raw SIM hits, no threshold" — the L4/L3 ratio is
  lattice-dependent (newest LCC v106.2: L3 = L4 = 0.31 hits/BX)
- Raw rows overstate fired-pixel occupancy ~1.6× (Geant4 step-splitting,
  layer-symmetric) — use unique-pixel counts (3.74/BX) for occupancy
- No charge threshold in this CSV (qq sample used 1 keV ≈ 278 e) — apply
  qin ≥ 278 for threshold-consistent comparisons (ratio robust: 3.58)
- Rates depend on readout window (h_time tails to ~2.2 µs); divide by all
  3,996 BXs
NOTES: shared-Geant4-stack caveat: official match uses the same ddsim/Geant4;
common-mode transport modeling of MeV loopers not excluded by cross-comparison.

## Slide 11 — Summary & next steps
BULLETS:
- Complete, audited, officially-validated IPC background production:
  3,996 BXs → per-BX PixESL hit streams on the 20 µm MAPS layers
- MAPS layers see 1.3 / 4.7 hits/BX (0.42 / 0.28 MHz/cm²) — a mild
  environment ~300× below the innermost layer
- All data + plots public: https://angli-share.web.cern.ch/FCC/MAPS/BIB_IPC/
- Next: PixESL readout studies on the background stream; physics ⊕ BIB overlay;
  other sources (SR, beam-gas, RB); GHC vs LCC lattice comparison
NOTES: the qq physics stream (10k Z→qq) uses the identical CSV convention —
overlay is a concatenation + BX-window exercise.
