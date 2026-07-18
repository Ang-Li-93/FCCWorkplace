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
