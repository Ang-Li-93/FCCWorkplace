# Analysis environment (`setup.sh`)

The default environment for **analysing** FCC-ee samples with FCCAnalyses.

A single entrypoint sources Key4hep, builds FCCAnalyses if needed, and
creates/activates a local Python venv layered on Key4hep (so packages like
`sklearn`, `xgboost`, `uproot` are available alongside the Key4hep stack).

```shell
git clone --recurse-submodules git@github.com:Ang-Li-93/FCCWorkplace.git
cd FCCWorkplace
source setup.sh
```

After each login, just rerun `source setup.sh`.

## Options

| Flag | Effect |
|---|---|
| `--rebuild-fcc`  | Force rebuild of FCCAnalyses |
| `--rebuild-venv` | Force rebuild of the local Python venv |
| `--rebuild`      | Both of the above |
| `--help`         | Show usage |

## The four environments — do not mix

Each uses a different Key4hep stack; **do not mix them in one shell.**

| Script | Purpose | Stack |
|---|---|---|
| `setup.sh` | Analyse samples with FCCAnalyses (default) | current stable Key4hep |
| `setup_hbs.sh` | H→bs analysis on winter2023 fast-sim | `2024-03-10` (pre-edm4hep1) — see [HBS_ENVIRONMENT.md](HBS_ENVIRONMENT.md) |
| `setup_winter2023.sh` | **Produce** winter2023 fast-sim MC | `2024-03-10` reco — see [WINTER2023_FASTSIM.md](WINTER2023_FASTSIM.md) |
| `setup_MAPS.sh` | ALLEGRO / BNL_MAPS **full-sim** (ddsim/Geant4) → PixESL | pinned release + local k4geo build — see [MAPS_PIXESL.md](MAPS_PIXESL.md) |

[Reference note](https://codimd.web.cern.ch/v-2loZ2BSmSurcYI1v-Nkg?both)
