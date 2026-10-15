#!/usr/bin/env python3
"""
JES / JER variant histograms for the hadronic 2D fit, ecm 365: per-energy entry point of
../../qq_jesjer_templates.py (one implementation for both energies, --ecm selects the stage2
config S<ecm>/qq/stage2_histograms_syst.py). Every argument is forwarded; see the docstring
and --help of qq_jesjer_templates.py.
  python3 stage2_jesjer_templates.py [--stage-dir|--input-dir DIR] [--out-dir DIR] [--procs P1,P2,...]
                                     [--nthreads|--ncpu N] [--seed S] [--self-check | --check-nominal|--check]
"""
import os
import sys

ecm = 365   # the S365 copy differs only in this line and the header

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "..", "..", "qq_jesjer_templates.py")
if any(a == "--ecm" or a.startswith("--ecm=") for a in sys.argv[1:]):
    sys.exit("ERROR: --ecm is fixed by this wrapper; call qq_jesjer_templates.py directly to choose it")
os.execv(sys.executable, [sys.executable, os.path.abspath(SCRIPT), "--ecm", str(ecm)] + sys.argv[1:])
