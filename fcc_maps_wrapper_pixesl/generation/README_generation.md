# Generation: e+e- → Z → inclusive @ 91.2 GeV

`whizard_z_inclusive.sin` steers WHIZARD; `run_whizard.sh` runs it and drops the
generator file at `outputs/z_inclusive_gen.hepmc` (what `run_ddsim_zinclusive.sh`
expects by default).

```bash
source setup/setup_key4hep.sh
bash generation/run_whizard.sh 1000      # 1000 events for debugging
```

## Two process options (pick one in the `.sin`)
1. **Hadronic** `e+e- → Z → q qbar` (u,d,s,c,b) — commented out.
2. **All-fermion inclusive** (quarks + charged leptons + neutrinos) — **default**.

Toggle by commenting/uncommenting the `process`/`integrate`/`simulate` blocks.
`run_whizard.sh` only patches `n_events`; everything else is edited in the `.sin`.

## Hadronization caveat
The default output is **parton level** (+ISR). It already yields wrapper hits and
is fine for first-pass debugging. For realistic charged-track multiplicity in the
wrapper, enable a parton shower + hadronization:
- WHIZARD's built-in PYTHIA6 shower (`?ps_fsr_active`, `?hadronization_active`, …), or
- hand the events to PYTHIA8 separately.

Turn this on **after** the full chain (gen → ddsim → convert → analyze) is validated.

## Output format
`sample_format = hepmc` → `ddsim --inputFiles outputs/z_inclusive_gen.hepmc`.
Alternatives (`stdhep`, `lcio`, `lhef`) work too — change `sample_format` and pass
the resulting file as the 2nd argument to `run_ddsim_zinclusive.sh`.

## If WHIZARD is not in your stack
Some Key4hep builds don't bundle WHIZARD. Alternatives:
- use `KKMC`/`Pythia8` Z-pole generation, or a pre-generated FCC sample, then point
  `run_ddsim_zinclusive.sh` at that file;
- the FCC `FullSim` examples under `FCC-config/.../ALLEGRO` show standard recipes.
The downstream steps only need *some* hepmc/stdhep/edm4hep event file.
