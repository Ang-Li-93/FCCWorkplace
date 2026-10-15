# HWWQE: quantum tomography of H → WW* at FCC-ee

Spin density matrix of the W⁺W⁻* system in e⁺e⁻ → ZH, H → WW* at √s = 240 GeV
(IDEA Delphes fast simulation): Gell-Mann coefficients, the CGLMP observable I₃,
the concurrence bound 𝒞₂ and the Δm = 2 coherence witness.

- Plan (phases and gates): [PLAN.md](PLAN.md)
- Conventions and normalisations, each fixed by a unit test: [CONVENTIONS.md](CONVENTIONS.md)
- Running log: [LOG.md](LOG.md)
- Gate reports: [reports/](reports/)

## Environment

```shell
source setup.sh            # repository root: Key4hep 2026-04-08 + FCCAnalyses + local venv
cd analysis/HWWQE
python -m pytest           # all tests must pass before any MC phase
```

## Layout

| Path | Content |
|---|---|
| `config/` | all configuration (`constants.yaml`, `plotting.yaml`, per-study and per-channel YAML; `generation/` for cards) |
| `qtomo/` | Python package: `basis`, `sm`, `frames`, `toy`, `tomography`, `bell`, `reweight`, `response`, `stats`, `config`, `plotting` |
| `tests/` | pytest unit tests |
| `analysis/` | study and channel drivers (`phase0_*.py`, later `chA_lvqq_Zll.py`, …) |
| `stage1/` | FCCAnalyses stage scripts (EDM4hep → flat ntuples), one per channel |
| `gen/` | dedicated generation (Whizard cards, Pythia settings, submission) |
| `reports/` | gate reports (markdown) and their figures |

## Workflow

Phase 0 (machinery, toys) is pure Python. From Phase 1 on the analysis stays on the
standard FCC-ee workflow: `stage1/` scripts are class-based FCCAnalyses analyses run
with `fccanalysis run` (processList/prodTag taken from `config/samples.yaml`), batch
jobs use FCCAnalyses' HTCondor submission (accounting group `group_usfcc.ali3` at SDCC),
and any dedicated generation uses EventProducer with FCC-config cards. Downstream
tomography reads the flat ntuples with uproot.
