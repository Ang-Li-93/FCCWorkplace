# FCCWorkplace

Superproject (umbrella git repo) for FCC-ee work at BNL/SDCC: physics analyses,
fast-sim and full-sim MC production, and the detector/analysis frameworks they
depend on — all wired together as git submodules with per-task environment
scripts.

```shell
git clone --recurse-submodules git@github.com:Ang-Li-93/FCCWorkplace.git
cd FCCWorkplace
source setup.sh
```

## Structure

```
FCCWorkplace/
  analysis/                 physics analyses: Hbs, HiggsInvisible, HiggsMass, ZH_XSec
  fcc_maps_wrapper_pixesl/  MAPS vertex -> PixESL full-sim subproject (docs in documents/)
  tools/  python/           shared helpers (kinematics, plotting, configs)
  documents/                detailed documentation (linked below)
  outputs/                  local scratch / logs

  setup.sh                  analysis environment (default)
  setup_hbs.sh              H->bs winter2023 legacy environment
  setup_winter2023.sh       winter2023 fast-sim MC production environment
  setup_MAPS.sh             ALLEGRO/BNL_MAPS full-sim environment
  run_combine.sh            CMS Combine via FCCSW Singularity image

  <submodules — see "Related projects">
```

## Related projects (submodules)

All are personal forks (`Ang-Li-93/*`) pinned to a branch, cloned via SSH.

| Submodule | Branch | Role |
|---|---|---|
| `FCCAnalyses` | `AngDev` | Main FCC-ee analysis framework (used by `setup.sh`) |
| `FCCAnalyses-winter2023` | `pre-edm4hep1` | Legacy FCCAnalyses for H→bs on winter2023 (used by `setup_hbs.sh`) |
| `FCC-config/winter2023` | `winter2023` | Generator cards (WHIZARD/Pythia `.sin`, Delphes/IDEA tcl) |
| `EventProducer` | `SDCC` | Fast-sim MC production driver, patched for SDCC |
| `CLDConfig` | `main` | CLD detector configuration |
| `k4geo` | — | Geometry, including the `BNL_MAPS` detector for the MAPS project |
| `k4Reco` | — | Key4hep reconstruction algorithms |

## Documentation

- [documents/SETUP.md](documents/SETUP.md) — the analysis environment (`setup.sh`), venv, options, and the four non-mixable environments
- [documents/HBS_ENVIRONMENT.md](documents/HBS_ENVIRONMENT.md) — `setup_hbs.sh`: the H→bs winter2023 legacy stack and why it exists
- [documents/WINTER2023_FASTSIM.md](documents/WINTER2023_FASTSIM.md) — `setup_winter2023.sh`: generating winter2023 IDEA fast-sim MC on SDCC
- [documents/COMBINE.md](documents/COMBINE.md) — `run_combine.sh`: CMS Combine via the FCCSW Singularity image
- [documents/MAPS_PIXESL.md](documents/MAPS_PIXESL.md) — the MAPS vertex → PixESL full-sim workflow (`setup_MAPS.sh`, `fcc_maps_wrapper_pixesl/`)
- [documents/ZH_XSEC_RUNS.md](documents/ZH_XSEC_RUNS.md) — ZH cross-section runs on SDCC: full run book (stage1 condor → fits), results, systematics, hadronic-channel status
