# H→bs environment (`setup_hbs.sh`) — winter2023 samples

The H→bs analysis (under `analysis/Hbs/`) uses the same winter2023 samples as
the other analyses, but its **flavor-tagging pipeline** is incompatible with the
current Key4hep stack. The renames in EDM4hep 1.0 (`TrackerHitData` →
`TrackerHit3DData`) and the FCCAnalyses changes in PR
[#481](https://github.com/HEP-FCC/FCCAnalyses/pull/481) (new `TrackDqdxHandler`
requiring a `_<dNdx>_track` association absent from winter2023) both break the
`JetFlavourHelper` on these samples.

The FCCAnalyses maintainer Juraj Smiesko documented the official workaround in
the FCCSW forum:
[FCC tutorial 2.4.2 — TrackerHitData error](https://fccsw-forum.web.cern.ch/t/fcc-tutorial-2-4-2-part-ii-produce-a-flat-tree-and-analyse-events-error-no-member-named-trackerhitdata-in-namespace-edm4hep/253/2):
use the older Key4hep stack `2024-03-10` together with the `pre-edm4hep1` branch
of FCCAnalyses. We pin a commit (`af5cf61`) that also carries our `HiggsTools`
and Z-builder additions, so the Hbs script uses the same API as ZH_XSec /
HiggsMass.

This lives in a separate submodule (`FCCAnalyses-winter2023/`) and a parallel
setup script — they do not interfere with `setup.sh`.

```shell
source setup_hbs.sh
fccanalysis run analysis/Hbs/mumu/analysis_stage1_batch.py
```

Same flags as `setup.sh` (`--rebuild-fcc`, `--rebuild-venv`, `--rebuild`,
`--help`). The Hbs venv lives in `local_env_winter2023/` and the FCCAnalyses
build under `FCCAnalyses-winter2023/build/`.

When a winter2023-replacement sample campaign lands (planned by the FCC team),
this whole side environment becomes obsolete: switch the Hbs `processList` to the
new samples and run everything from `setup.sh`.
