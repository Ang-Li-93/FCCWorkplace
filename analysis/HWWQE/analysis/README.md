# analysis/

Study and channel drivers (Python, configuration from `config/`). Run from the analysis root
after `source setup.sh` at the repository root.

Phase 0 (`config/phase0.yaml`; pseudo-experiment output in `outputs/phase0/`, git-ignored):

```shell
python analysis/phase0_analytic.py                  # analytic SM validation figures
python analysis/phase0_reach.py asymptotic          # exact asymptotic reach (local, seconds)
python analysis/phase0_closure.py run --state sm_m30 --n 1000 --count 3 --out /tmp/t.npz   # local test
python analysis/phase0_closure.py submit            # HTCondor (analysis/batch.py); skips finished jobs
python analysis/phase0_reach.py submit
python analysis/phase0_closure.py summarise && python analysis/phase0_closure.py plot
python analysis/phase0_reach.py summarise && python analysis/phase0_reach.py plot
```

Later: `chA_lvqq_Zll.py`, `chB_lvqq_Zqq.py`, ...
