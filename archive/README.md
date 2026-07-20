# Archive — bookkeeping of retired analysis trees

Kept for reference only; nothing here is part of an active workflow.

- `ZH_XSec_FinalReport_Reproduce/` — reproduction scripts (plots + fits) for the
  published ZH cross-section FinalReport paper, moved out of
  `analysis/ZH_XSec/FinalReport/` during the 2026-07 cleanup. The active analysis
  lives in `analysis/ZH_XSec/Paper/` (run book: `documents/ZH_XSEC_RUNS.md`).

Removed in the same cleanup (recoverable from git history, commit that introduced
this file): `analysis/ZH_XSec/{FinalReport,FinalReport2_bkup,MidTerm,TopHiggs}`
(pre-Paper lxplus script trees, no data) and `analysis/ZH_XSec/FCCAnalyzer`
(its `plotter.py` now lives at `Paper/plotter.py`; the jeyserma reference
histmakers/headers/datasets at `Paper/reference_fccanalyzer/`).
