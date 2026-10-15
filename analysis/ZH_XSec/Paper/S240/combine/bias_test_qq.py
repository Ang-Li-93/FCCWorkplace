#!/usr/bin/env python3
"""
DEPRECATED shim, ecm 240: the hadronic bias test lives in bias_test_generic.py.

The July-2026 body of this script ran on run_2D_mrecoil_mjj_qq/ with the hadronic-Z
signal convention (signal = Z(qq/ss/cc/bb)H, per-decay templates over the hadronic Z
decays only). Since makeWS_2D_qq.py builds the PAPER-SPEC templates there (signal =
all ZH final states, BES), the old body would silently mix the two conventions. The
July convention now lives in 'makeWS_2D_qq.py --zh-other-as-bkg' +
'bias_test_generic.py qq-zhbkg' (run_2D_mrecoil_mjj_qq_zhbkg/), which this shim execs
after printing a deprecation line, forwarding every extra argument (--x, --decays,
--br, --base; FIT_BASE is honoured by bias_test_generic.py). The paper-spec bias test is
'bias_test_generic.py qq'. Same log format as before (collect_results.py); the
qq-zhbkg block is a cross-check, not a paper column.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODE = "qq-zhbkg"   # July hadronic-Z signal convention; see bias_test_generic.py SETUPS

print(f"DEPRECATED: bias_test_qq.py is a shim -> python3 bias_test_generic.py {MODE} "
      f"{' '.join(sys.argv[1:])} (July hadronic-Z signal convention, run_2D_mrecoil_mjj_qq_zhbkg/); "
      "the paper-spec test is 'bias_test_generic.py qq'", file=sys.stderr, flush=True)
os.execv(sys.executable, [sys.executable, os.path.join(HERE, "bias_test_generic.py"), MODE] + sys.argv[1:])
