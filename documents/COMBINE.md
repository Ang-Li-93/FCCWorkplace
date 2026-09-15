# Combine (`run_combine.sh`)

CMS Combine is not part of the key4hep / FCCSW stack, and the `fccanalysis combine`
stage only writes datacards — it never runs a fit. The CMS `combine-standalone`
container is used instead, through the wrapper at the repo root:

```shell
./run_combine.sh text2workspace.py datacard.txt
./run_combine.sh combine -M MultiDimFit datacard.root
./run_combine.sh python3 analysis/Hbs/mumu/combine/run_fits.py   # any script that calls combine
./run_combine.sh bash                                             # interactive shell in the image
```

The wrapper uses the first image that exists, or `COMBINE_IMG=/path/to/image` to
override:

1. `/cvmfs/unpacked.cern.ch/gitlab-registry.cern.ch/cms-cloud/combine-standalone:latest`
   — Combine 10.2.1, ROOT 6.36, AlmaLinux 9. Available on SDCC and lxplus; verified on
   SDCC (September 2026).
2. `/eos/project/f/fccsw-web/www/analysis/auxiliary/combine-standalone_v9.2.1.sif`
   — the FCCSW-hosted image, lxplus only.

The working directory is preserved inside the container, and `/afs`, `/eos`, `/cvmfs`,
`/tmp`, `/gpfs`, `/usatlas` are bound when they exist on the host. `combine`,
`text2workspace.py`, `combineTool.py` and a Python 3 with ROOT and the
`HiggsAnalysis.CombinedLimit` package are on PATH inside the image, so plain Python
scripts that import ROOT and call `combine` via `subprocess` run unmodified. Do not
source any key4hep setup inside the container.

There is no local build to maintain; `HiggsAnalysis/` is git-ignored and can be removed.
