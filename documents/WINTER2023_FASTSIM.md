# winter2023 IDEA fast-sim MC generation (SDCC)

How to generate winter2023 FCC-ee **fast-sim** MC (WHIZARD/Pythia → stdhep →
Delphes/IDEA → EDM4hep) on BNL **SDCC** via the `EventProducer` submodule.

This is the **production** side. It is distinct from:
- `setup.sh` / `setup_hbs.sh` — *analysing* samples with FCCAnalyses,
- `setup_MAPS.sh` — the ALLEGRO/BNL_MAPS **full-sim** (ddsim/Geant4) chain.

Each of these is a different Key4hep stack; **do not mix them in one shell.**

---

## TL;DR

```shell
source setup_winter2023.sh

# 1) generator: WHIZARD -> stdhep  (PRODTAG is exported by the setup script)
python EventProducer/bin/run.py --FCCee --STDHEP --send --condor \
    --typestdhep wzp6 -p wzp6_ee_mumuH_Hbs_W4p1MeV_ecm240 \
    -n 10000 -N 10 --prodtag $PRODTAG

# 2) once step 1 jobs finish, register them, then run Delphes/IDEA fast-sim
python EventProducer/bin/run.py --FCCee --STDHEP --check --force \
    --typestdhep wzp6 -p wzp6_ee_mumuH_Hbs_W4p1MeV_ecm240 --prodtag $PRODTAG

python EventProducer/bin/run.py --FCCee --reco --send --condor \
    --type stdhep -p wzp6_ee_mumuH_Hbs_W4p1MeV_ecm240 \
    -n 10000 -N 10 --prodtag $PRODTAG --detector IDEA
```

Monitor: `condor_q -name spoolsub02.sdcc.bnl.gov`
(a bare `condor_q` on a node whose default schedd isn't spoolsub02 shows *empty*).

---

## The chain

| Step | Command | Stack (on worker) | Output |
|---|---|---|---|
| **Gen** | `--STDHEP --send --typestdhep wzp6` | `defaultstack` (stable, WHIZARD 3.x) | `…/generation/stdhep/winter2023/<proc>/events_*.stdhep.gz` |
| **Check** | `--STDHEP --check --force` | (submit node) | per-file yamls marked `DONE` |
| **Reco** | `--reco --send --type stdhep --detector IDEA` | `prodTag['winter2023']` = `key4hep -r 2024-03-10` (pre-edm4hep1) | `…/generation/DelphesEvents/winter2023/IDEA/<proc>/events_*.root` |

- The IDEA fast-sim is `DelphesSTDHEP_EDM4HEP card_IDEA.tcl edm4hep_IDEA.tcl …`
  (parametric Delphes, **no Geant4**). Detectors: `IDEA`, `IDEA_3T`, `IDEA_FullSilicon`.
- The reco stack is **2024-03-10** on purpose: it produces **pre-edm4hep1**
  EDM4hep that `setup_hbs.sh` (winter2023 FCCAnalyses) can read. The current
  stable stack would write podio-1.x EDM4hep that the Hbs analysis cannot read.

### Process name = card name

The `-p` value must exactly match (a) a registered key in
`EventProducer/config/param_FCCee.py` and (b) the card filename
`FCC-config/winter2023/FCCee/Generator/Whizard/v3.0.3/<proc>.sin`.

### H→bs cards (e.g. mumuH @ 240 GeV)

- **`wzp6_ee_mumuH_Hbs_W4p1MeV_ecm240`** — SM on-shell `ee→μμH` + Pythia6
  flavour-violating decay to **bs**. Self-contained (no UFO). **Recommended.**
- `wzp6_ee_mumuH_Hbs_ecm240` — ME-level **bs** via the `THDM_QFV` UFO.

---

## SDCC adaptations baked into this repo

`EventProducer` upstream targets CERN lxplus/EOS. The following changes make it
run on SDCC (all already committed):

**`EventProducer/config/param_FCCee.py`**
- I/O redirected to the group area `/gpfs/.../MAPS_storage/` (in/out, yaml, www).
- `fccconfigdir` → cards + the `THDM_QFV` UFO read from the **repo submodule**
  `FCC-config/winter2023/`, not MAPS_storage. (The 66 ME `.sin` cards also had
  their hardcoded EOS UFO path repointed to this repo UFO dir.)
- `eostest` health probe → local sentinel `/gpfs/.../MAPS_storage/tests/testfile.txt`
  (size 66). **Do not delete it** — `testeos()` needs the exact file+size, else
  every command aborts with *"eos seems to have problems, should check, will exit"*.
- `prodTag['winter2023']` → `key4hep -r 2024-03-10` (el9-compatible pre-edm4hep1;
  CERN original was the centos7 `2022-12-23` stack, which won't run on the
  AlmaLinux9 workers).
- `--priority` default → `group_usfcc` (was the CERN `group_u_FCC.local_gen`).

**`EventProducer/bin/send_*.py`** (all 7 senders)
- condor accounting: write the modern pair
  `accounting_group = group_usfcc` + `accounting_group_user = $USER`
  (→ identity `group_usfcc.ali3`) instead of `+AccountingGroup`.

**`EventProducer/bin/send_fromstdhep.py`** (reco)
- All 4 CERN `eoscopy.py`/EOS paths → local `cp`: stdhep input from gpfs,
  `card_IDEA.tcl` + `edm4hep_IDEA.tcl` from the repo FCC-config, output `.root`
  back to the DelphesEvents area (+ `mkdir -p`).
- `getenv = False` (see gotcha below).

---

## Gotchas (learned the hard way)

1. **Idle jobs that never run = wrong accounting group.** The CERN
   `group_u_FCC.local_gen` is invalid at SDCC; the negotiator finds "no match"
   even though `condor_q -analyze` shows hundreds of able slots. Use
   `group_usfcc` (default now).

2. **Misleading submit counters.** `GOOD SUB 0/10` and `successfully sent 1
   job(s)` are cosmetic — EventProducer counts `condor_submit` *calls*, not jobs.
   All N jobs go in **one cluster** via `queue filename matching files …`.

3. **Reco needs `--check --force` first.** Reco consumes per-file `DONE` yamls,
   not raw stdhep. Plain `--check` silently does nothing unless a `check`
   flag-file exists; `--force` bypasses that gate. (The `nevents: 100000` it
   records is a placeholder — the stdhep checker doesn't really count. Cosmetic.)

4. **`--check` needs the www dir.** It appends a stats HTML to
   `/gpfs/.../MAPS_storage/www/`; create it once (`mkdir -p`). The per-file
   yamls are written before that step, so `DONE` survives even if it errors.

5. **Reco segfault → empty (1–7 KB) outputs = `getenv` + stack.** With
   `getenv = True` the worker inherited the submit shell's Key4hep env, so the
   in-job `source setup.sh` bailed (*"already set up"*) after `LD_LIBRARY_PATH`
   was unset → podio `vector<podio::ObjectID>` dictionaries missing → corrupt
   branches → segfault (but condor still reports exit 0!). Fix = `getenv = False`
   so the worker starts clean and the stack setup actually runs.

---

## Validating a finished batch

```shell
# all jobs gone from the queue?
condor_q -name spoolsub02.sdcc.bnl.gov ali3

# good fast-sim outputs are ~100 MB and have 10000 entries; bad ones are KB
ls -la …/generation/DelphesEvents/winter2023/IDEA/<proc>/events_*.root
python -c "import ROOT; t=ROOT.TFile.Open('events_<uid>.root').Get('events'); print(t.GetEntries())"

# scan THIS round's logs only (BatchOutputs accumulates old clusters too)
grep -l "segmentation violation\|CollectionProxy\|already set up" \
    BatchOutputs/FCCee/winter2023/IDEA/<proc>/condor_job.*.<ClusterId>.*.{out,error}
```

Reference: `wzp6_ee_mumuH_Hbs_W4p1MeV_ecm240`, 10×10k → 10 files, ~104 MB each,
10000 events/file, pre-edm4hep1 EDM4hep, clean. Generator seeds are distinct
random per job (= the uid in the filename).
