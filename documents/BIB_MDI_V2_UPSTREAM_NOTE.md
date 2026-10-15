# Note for MDI/software team (A. Ciarma, J. Eysermans, A. Ilg) — mdi_v2 findings
<!-- Draft for Ang to edit/send. All numbers reproducible; paths on SDCC gpfs. -->

Context: we (BNL LDRD, MAPS vertex demonstrator) ported the `mdi_v2` branch
(aciarma/k4geo) into our ALLEGRO-based detector variant and validated our own
ddsim chain against the central production
(`/eos/experiment/fcc/ee/simulation/key4hep_2026_04_08/91GeV/ALLEGRO_o1_v03_mdi_v2_CAD`,
IPC LCC V106.2), running the **same GuineaPig bunch crossings** through
key4hep 2026-04-08 stable. Three findings:

## 1. Geant4 hangs (endless navigation loop) in the mdi_v2 CAD geometry
On ~4–5% of IPC bunch crossings, Geant4 enters an apparently infinite
navigation loop mid-event (no abort, no exception; job runs forever). With the
v1 CAD MDI the same class of events *aborted* (GeomNav1002 stuck-track, rc 133)
at the ~1% level; in v2 they hang instead. The behavior is largely
**deterministic per event**: retrying with a different RNG seed rescues only a
minority.
- Observed: 400-BX batch → 377 ok, 4 recovered by seed retry, **19 hung on
  both seeds** (watchdog-killed after 40 min each). Also reproduced with plain
  FTFP_BERT (2/60) — not related to EMZ/low-energy-EM settings.
- Deterministic reproducers (GuineaPig file id + our seeds) available for all
  19, e.g. BXs 100769, 101668, 101688, 103745, 104809 …
  (full list + seeds: SDCC `BIB_derived/sim/LCC_V106p2_v2_validation/ledger/`).
- Question: is this known? Was any navigator tolerance / tessellation fix
  applied in the central production?

## 2. The central IPC sample silently lacks ~4% of bunch crossings
`IPC_LCC_V106p2` contains 19,673 sim files vs 20,501 GuineaPig `.pairs` inputs
(828 missing, ~4.0%). Of 19 BXs that hang for us, only 4 have central output
files — consistent with the missing central BXs being (at least partly) the
same hang pathology, silently dropped. If hang-prone events correlate with
mask-grazing topologies, their loss could bias occupancy estimates downward.
Worth documenting in the sample README either way.

## 3. Request: exact central ddsim configuration
Running the same pairs through (as far as we know) the same geometry and
stack, with FTFP_BERT / default range cut / 1 keV tracker filter /
crossing-angle boost 0.015, we reproduce the outer vertex-barrel layers
(r = 13/31.5 cm) at the few-% level, but see a layer-dependent excess of
raw VertexBarrel SimHits on the inner barrel: +9% (L0), +23% (L1), +34% (L2)
(57 matched BXs; same-sign result on 376 BXs with our BIB-recipe settings).
The excess persists at unique-(particle,cell)-crossing level, so it is not
hit-row splitting. We would like to run the *identical* configuration — could
you point us to the production scripts / steering used for
`ALLEGRO_o1_v03_mdi_v2_CAD` (tracker action + parameters, particle handler
thresholds, exact stack build)?

Thanks! — Ang (BNL)

---

## Addendum 2026-10-05 — found while building a hit-level truth ntuple of the central IPC sample
<!-- Draft for Ang to edit/send. Everything below was checked against the DD4hep v01-36 source
     and the central files; details in documents/BIB_STUDIES.md section 9. -->

**Item 3 above is answered by the files themselves:** the `runs` tree of every central file
stores the complete ddsim configuration and the steering text. The production used
FTFP_BERT_EMZ, range cut 0.05 mm, the four low-energy EM UI commands (Auger on),
`Geant4TrackerWeightedAction` (HitPositionCombination 2), `keepAllParticles = False`
(`minimalKineticEnergy = 1 MeV`). Our "matched" test (FTFP_BERT, default range cut) was
therefore not matched; a like-for-like rerun with the verbatim central steering is still to do.

### 4. The central steering sets the tracker filter twice — the sample has a 1 keV per-step cut
`steering.py` contains `SIM.filter.tracker = "edep0"` (line 189, as in the bib-studies
recipe) and, nine lines later, the template default `SIM.filter.tracker = "edep1kev"`
(line 198), which wins. `EnergyDepositMinimumCut` is applied to each Geant4 step before the
sensitive detector sees it, so in the central IPC sample:
- no SimTrackerHit is below 1 keV (0 of 2,745,527 tracker hits);
- for e± below 100 MeV about 70% of the steps in a 50 µm sensor are dropped: hits keep ~90%
  of the energy and ~82% of the path (the loss vanishes above 100 MeV, where the multiple-
  scattering model changes and the sensor is crossed in one step);
- because the boundary step is almost always dropped, a hit is not closed when the track
  leaves the sensor; a track that re-enters the same sensor is merged into the old hit
  (6–11% of the vertex-barrel hits, position up to ~16 mm off).
Question: was `edep0` intended? If so the other central BIB samples made with this steering
are affected in the same way.

### 5. `part.keepAllParticles = True` has no effect with `Geant4TCUserParticleHandler`
`setReason()` zeroes the keep-reason of every sub-threshold secondary born inside the tracking
cylinder, including KEEP_ALWAYS. To store every track one needs `userParticleHandler = ""`
(or `minimalKineticEnergy = 0`). Relevant for the recipe in bib-studies/simulation/README.md.

### 6. What dominates the outer vertex layers (may interest the vertex/MDI groups)
On the outer barrel 65% (r = 13 cm) and 94% (r = 31.5 cm) of the SimTrackerHits are sub-MeV
electrons released in the silicon by X-rays and soft photons (photo-electron + 1.6 keV Si
Auger electron counted as two hits in one pixel), not charged particles from the IP. About a
third of them descend from primaries that end at |z| = 1.3–1.5 m, around the copper crotch
where the two beam pipes separate. The rate therefore depends on the sensitive thickness,
the Auger setting and the CAD beam pipe.

### 7. bib-studies `drawhits.py` issues seen with this geometry
- "occupancy" divides distinct cellIDs (pixels here: the readout has x,y fields) by
  `det_element_cells` (number of sensors): 27% for layer 0 instead of 8e-7;
- `h_avg_hits_x_layerN_x_module` is booked with a cumulative module offset but filled with
  the per-layer module id: layers 3 and 4 are 100% underflow (cf. slide 5 of the FCC Week talk);
- `h_hit_rateDensity` carries 52 MHz × 3 × 5 and an ideal-cylinder area;
- with `--e_cut` a cellID is marked as fired before the energy cut, so thresholded firing
  cells are 30–40% low on the outer layers;
- `python/ALLEGRO.py` takes the sensor area as GetDY × GetDZ, which is thickness × length
  for the o1_v03 vertex builder; phi binning is 99 bins; `hit_zphi` axis titles are swapped;
  bin sizes are printed with %d (11.28 mm → "11").
