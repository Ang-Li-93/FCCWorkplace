# FCCWorkplace
FCC workplace
## Installation of Software

- [FCCWorkplace](https://github.com/Ang-Li-93/FCCWorkplace)

I am in the process of simplifing these two repos.

Follow the instructions step-by-step.

### Clone the repository

```shell=
git clone --recurse-submodules git@github.com:Ang-Li-93/FCCWorkplace.git
cd FCCWorkplace
```

### Setup

A single entrypoint sources Key4hep, builds FCCAnalyses if needed, and
creates/activates a local Python venv layered on Key4hep (so packages
like `sklearn`, `xgboost`, `uproot` are available alongside the
Key4hep stack).

```shell=
source setup.sh
```

Options:

| Flag | Effect |
|---|---|
| `--rebuild-fcc`  | Force rebuild of FCCAnalyses |
| `--rebuild-venv` | Force rebuild of the local Python venv |
| `--rebuild`      | Both of the above |
| `--help`         | Show usage |

After each login, just rerun `source setup.sh`.

### Combine

The CMS `HiggsAnalysis-CombinedLimit` submodule has been removed in
favour of the FCCSW Singularity image. Use the wrapper:

```shell=
./run_combine.sh combine -M MultiDimFit datacard.root
./run_combine.sh text2workspace.py datacard.txt
```

Override the image with `COMBINE_IMG=/path/to/other.sif` if needed.

[Note](https://codimd.web.cern.ch/v-2loZ2BSmSurcYI1v-Nkg?both)