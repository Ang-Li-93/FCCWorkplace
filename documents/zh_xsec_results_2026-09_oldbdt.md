# ZH_XSec Paper reproduction vs arXiv:2512.21290 (JHEP Table 2, MVA-based configuration)

Generated 2026-09-30 by collect_results.py from /gpfs/mnt/gpfs01/usfcc/ali3/FCCWorkplace/analysis/ZH_XSec/Paper (run-dir suffix '_oldbdt'). All numbers are relative uncertainties on sigma_ZH in %; precision = half the distance between the 2*deltaNLL = 1 crossings around the best fit (fit_precision.py logic); ratios = reproduction / paper. 'Paper total (stat)' = Table 2, MVA-based column, total (stat-only). Mapping: 'Repro total (paper def.)' = xsecSTATshapes (only the shape nuisances frozen, the background normalizations float = stat + the 1% lnN normalizations, the only nuisance parameters of the paper's fit - Sec. 5.3: 'each with a normalization uncertainty of 1% included as a nuisance parameter in the fit', 'Shape uncertainties are not included as nuisance parameters'; for the July-style cross-check cards the normalization is a free rateParam instead); 'Repro stat (paper def.)' = xsecSTAT (all constrained nuisances + all rateParams frozen, i.e. background normalizations fixed - the paper's stat-only); bkg-norm syst = sqrt(total^2 - stat^2) in these definitions. '+ regular syst profiled' = xsec (nothing frozen: BES, the lepton / jet momentum scale and sqrt(s) profiled in addition) - beyond the paper's quoted precision, which evaluated these effects separately (0.095% combined, Sec. 5.3); full syst = sqrt(xsec^2 - stat^2).

## sqrt(s) = 240 GeV

Paper-spec fits (recoil mass in two BDT regions for the leptonic channels, 2D m_recoil x m_jj for qq):

| Channel | Paper total (stat) | Repro total (paper def.: stat + bkg norm) | Repro stat (paper def.) | Ratio total | Ratio stat | bkg-norm syst sqrt(total^2 - stat^2) | + regular syst profiled (xsec, beyond the paper) | full syst sqrt(xsec^2 - stat^2) |
|---|---|---|---|---|---|---|---|---|
| Z(mumu)H (recoil, 2 BDT regions) | 0.68 (0.66) | 0.679 | 0.660 | 1.00 | 1.00 | 0.160 | 0.685 | 0.181 |
| Z(ee)H (recoil, 2 BDT regions) | 0.81 (0.78) | 0.805 | 0.783 | 0.99 | 1.00 | 0.184 | 0.817 | 0.231 |
| Z(ll)H = ee+mumu (recoil, 2 BDT regions) | 0.52 (0.50) | 0.523 | 0.505 | 1.01 | 1.01 | 0.136 | 0.529 | 0.159 |
| Z(qq)H (2D m_recoil x m_jj) | 0.38 (0.30) | 0.404 | 0.311 | 1.06 | 1.04 | 0.258 | 0.404 | 0.258 |
| combination ee+mumu+qq | 0.31 (0.26) | 0.318 | 0.265 | 1.03 | 1.02 | 0.176 | 0.318 | 0.177 |

Cross-checks (July-2026 style: binned BDT-score fits with a lumped free-rateParam background; qq 2D with the July signal definition, ZH-other as bkg_ZH, no BES):

| Channel | Paper total (stat) | Repro total (paper def.: stat + bkg norm) | Repro stat (paper def.) | Ratio total | Ratio stat | bkg-norm syst sqrt(total^2 - stat^2) | + regular syst profiled (xsec, beyond the paper) | full syst sqrt(xsec^2 - stat^2) |
|---|---|---|---|---|---|---|---|---|
| Z(mumu)H (binned BDT score) | 0.68 (0.66) | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Z(ee)H (binned BDT score) | 0.81 (0.78) | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Z(ll)H = ee+mumu (binned BDT score) | 0.52 (0.50) | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Z(qq)H 2D, ZH-other as bkg (July def.) | 0.38 (0.30) | 0.457 | 0.358 | 1.20 | 1.19 | 0.284 | 0.457 | 0.284 |
| Z(qq)H (1D BDT score) | 0.38 (0.30) | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| combination ee+mumu+qq (BDT-score leptonic cards) | 0.31 (0.26) | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

Sources (/gpfs/mnt/gpfs01/usfcc/ali3/FCCWorkplace/analysis/ZH_XSec/Paper/S240/combine/<dir>_oldbdt/):
- Z(mumu)H (recoil, 2 BDT regions) [run_recoil_2cat_mumu_oldbdt]: total: higgsCombinexsec.MultiDimFit.mH125.root (r=1.0000, 119 pts in [0.970, 1.030], 2dNLL=1 at [0.9931, 1.0068]); stat: higgsCombinexsecSTAT.MultiDimFit.mH125.root (r=1.0000, 120 pts in [0.970, 1.030], 2dNLL=1 at [0.9934, 1.0066]); shapes: higgsCombinexsecSTATshapes.MultiDimFit.mH125.root (r=1.0000, 120 pts in [0.970, 1.030], 2dNLL=1 at [0.9932, 1.0068])
- Z(ee)H (recoil, 2 BDT regions) [run_recoil_2cat_ee_oldbdt]: total: higgsCombinexsec.MultiDimFit.mH125.root (r=1.0000, 119 pts in [0.970, 1.030], 2dNLL=1 at [0.9919, 1.0082]); stat: higgsCombinexsecSTAT.MultiDimFit.mH125.root (r=1.0000, 120 pts in [0.970, 1.030], 2dNLL=1 at [0.9922, 1.0078]); shapes: higgsCombinexsecSTATshapes.MultiDimFit.mH125.root (r=1.0000, 120 pts in [0.970, 1.030], 2dNLL=1 at [0.9920, 1.0081])
- Z(ll)H = ee+mumu (recoil, 2 BDT regions) [run_recoil_2cat_combined_oldbdt]: total: higgsCombinexsec.MultiDimFit.mH125.root (r=1.0000, 158 pts in [0.980, 1.020], 2dNLL=1 at [0.9947, 1.0053]); stat: higgsCombinexsecSTAT.MultiDimFit.mH125.root (r=1.0000, 160 pts in [0.980, 1.020], 2dNLL=1 at [0.9950, 1.0051]); shapes: higgsCombinexsecSTATshapes.MultiDimFit.mH125.root (r=1.0000, 160 pts in [0.980, 1.020], 2dNLL=1 at [0.9948, 1.0052])
- Z(qq)H (2D m_recoil x m_jj) [run_2D_mrecoil_mjj_qq_oldbdt]: total: higgsCombinexsec.MultiDimFit.mH125.root (r=1.0000, 116 pts in [0.970, 1.030], 2dNLL=1 at [0.9960, 1.0040]); stat: higgsCombinexsecSTAT.MultiDimFit.mH125.root (r=1.0000, 120 pts in [0.970, 1.030], 2dNLL=1 at [0.9969, 1.0031]); shapes: higgsCombinexsecSTATshapes.MultiDimFit.mH125.root (r=1.0000, 120 pts in [0.970, 1.030], 2dNLL=1 at [0.9960, 1.0040])
- combination ee+mumu+qq [run_240_all_oldbdt]: total: higgsCombinexsec.MultiDimFit.mH125.root (r=1.0000, 200 pts in [0.985, 1.015], 2dNLL=1 at [0.9968, 1.0032]); stat: higgsCombinexsecSTAT.MultiDimFit.mH125.root (r=1.0000, 200 pts in [0.985, 1.015], 2dNLL=1 at [0.9974, 1.0027]); shapes: higgsCombinexsecSTATshapes.MultiDimFit.mH125.root (r=1.0000, 200 pts in [0.985, 1.015], 2dNLL=1 at [0.9968, 1.0032])
- Z(mumu)H (binned BDT score): run_binned_BDTScore_mumu_oldbdt missing
- Z(ee)H (binned BDT score): run_binned_BDTScore_ee_oldbdt missing
- Z(ll)H = ee+mumu (binned BDT score): run_binned_BDTScore_combined_oldbdt missing
- Z(qq)H 2D, ZH-other as bkg (July def.) [run_2D_mrecoil_mjj_qq_zhbkg_oldbdt]: total: higgsCombinexsec.MultiDimFit.mH125.root (r=1.0000, 119 pts in [0.970, 1.030], 2dNLL=1 at [0.9954, 1.0046]); stat: higgsCombinexsecSTAT.MultiDimFit.mH125.root (r=1.0000, 120 pts in [0.970, 1.030], 2dNLL=1 at [0.9964, 1.0036]); shapes: higgsCombinexsecSTATshapes.MultiDimFit.mH125.root (r=1.0000, 119 pts in [0.970, 1.030], 2dNLL=1 at [0.9954, 1.0046])
- Z(qq)H (1D BDT score): run_binned_BDTScore_qq_oldbdt missing
- combination ee+mumu+qq (BDT-score leptonic cards): run_240_all_bdt_oldbdt missing

## sqrt(s) = 365 GeV

Paper-spec fits (recoil mass in two BDT regions for the leptonic channels, 2D m_recoil x m_jj for qq):

| Channel | Paper total (stat) | Repro total (paper def.: stat + bkg norm) | Repro stat (paper def.) | Ratio total | Ratio stat | bkg-norm syst sqrt(total^2 - stat^2) | + regular syst profiled (xsec, beyond the paper) | full syst sqrt(xsec^2 - stat^2) |
|---|---|---|---|---|---|---|---|---|
| Z(mumu)H (recoil, 2 BDT regions) | 1.79 (1.79) | 1.775 | 1.728 | 0.99 | 0.97 | 0.404 | 1.775 | 0.404 |
| Z(ee)H (recoil, 2 BDT regions) | 1.91 (1.90) | 1.889 | 1.838 | 0.99 | 0.97 | 0.432 | 1.905 | 0.498 |
| Z(ll)H = ee+mumu (recoil, 2 BDT regions) | 1.32 (1.30) | 1.307 | 1.259 | 0.99 | 0.97 | 0.349 | 1.308 | 0.354 |
| Z(qq)H (2D m_recoil x m_jj) | 0.56 (0.47) | 0.513 | 0.432 | 0.92 | 0.92 | 0.277 | 0.513 | 0.277 |
| combination ee+mumu+qq | 0.52 (0.44) | 0.482 | 0.409 | 0.93 | 0.93 | 0.254 | 0.482 | 0.254 |

Cross-checks (July-2026 style: binned BDT-score fits with a lumped free-rateParam background; qq 2D with the July signal definition, ZH-other as bkg_ZH, no BES):

| Channel | Paper total (stat) | Repro total (paper def.: stat + bkg norm) | Repro stat (paper def.) | Ratio total | Ratio stat | bkg-norm syst sqrt(total^2 - stat^2) | + regular syst profiled (xsec, beyond the paper) | full syst sqrt(xsec^2 - stat^2) |
|---|---|---|---|---|---|---|---|---|
| Z(mumu)H (binned BDT score) | 1.79 (1.79) | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Z(ee)H (binned BDT score) | 1.91 (1.90) | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Z(ll)H = ee+mumu (binned BDT score) | 1.32 (1.30) | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Z(qq)H 2D, ZH-other as bkg (July def.) | 0.56 (0.47) | 0.535 | 0.479 | 0.96 | 1.02 | 0.239 | 0.535 | 0.239 |
| Z(qq)H (1D BDT score) | 0.56 (0.47) | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| combination ee+mumu+qq (BDT-score leptonic cards) | 0.52 (0.44) | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

Sources (/gpfs/mnt/gpfs01/usfcc/ali3/FCCWorkplace/analysis/ZH_XSec/Paper/S365/combine/<dir>_oldbdt/):
- Z(mumu)H (recoil, 2 BDT regions) [run_recoil_2cat_mumu_oldbdt]: total: higgsCombinexsec.MultiDimFit.mH125.root (r=1.0000, 160 pts in [0.920, 1.079], 2dNLL=1 at [0.9823, 1.0178]); stat: higgsCombinexsecSTAT.MultiDimFit.mH125.root (r=1.0000, 160 pts in [0.920, 1.079], 2dNLL=1 at [0.9828, 1.0173]); shapes: higgsCombinexsecSTATshapes.MultiDimFit.mH125.root (r=1.0000, 160 pts in [0.920, 1.079], 2dNLL=1 at [0.9823, 1.0178])
- Z(ee)H (recoil, 2 BDT regions) [run_recoil_2cat_ee_oldbdt]: total: higgsCombinexsec.MultiDimFit.mH125.root (r=1.0000, 160 pts in [0.920, 1.079], 2dNLL=1 at [0.9809, 1.0190]); stat: higgsCombinexsecSTAT.MultiDimFit.mH125.root (r=1.0000, 160 pts in [0.920, 1.079], 2dNLL=1 at [0.9817, 1.0185]); shapes: higgsCombinexsecSTATshapes.MultiDimFit.mH125.root (r=1.0000, 160 pts in [0.920, 1.079], 2dNLL=1 at [0.9812, 1.0190])
- Z(ll)H = ee+mumu (recoil, 2 BDT regions) [run_recoil_2cat_combined_oldbdt]: total: higgsCombinexsec.MultiDimFit.mH125.root (r=1.0000, 160 pts in [0.950, 1.050], 2dNLL=1 at [0.9869, 1.0131]); stat: higgsCombinexsecSTAT.MultiDimFit.mH125.root (r=1.0000, 160 pts in [0.950, 1.050], 2dNLL=1 at [0.9874, 1.0126]); shapes: higgsCombinexsecSTATshapes.MultiDimFit.mH125.root (r=1.0000, 160 pts in [0.950, 1.050], 2dNLL=1 at [0.9870, 1.0131])
- Z(qq)H (2D m_recoil x m_jj) [run_2D_mrecoil_mjj_qq_oldbdt]: total: higgsCombinexsec.MultiDimFit.mH125.root (r=1.0000, 160 pts in [0.950, 1.050], 2dNLL=1 at [0.9949, 1.0051]); stat: higgsCombinexsecSTAT.MultiDimFit.mH125.root (r=1.0000, 160 pts in [0.950, 1.050], 2dNLL=1 at [0.9957, 1.0043]); shapes: higgsCombinexsecSTATshapes.MultiDimFit.mH125.root (r=1.0000, 160 pts in [0.950, 1.050], 2dNLL=1 at [0.9949, 1.0051])
- combination ee+mumu+qq [run_365_all_oldbdt]: total: higgsCombinexsec.MultiDimFit.mH125.root (r=1.0000, 200 pts in [0.975, 1.025], 2dNLL=1 at [0.9952, 1.0048]); stat: higgsCombinexsecSTAT.MultiDimFit.mH125.root (r=1.0000, 200 pts in [0.975, 1.025], 2dNLL=1 at [0.9959, 1.0041]); shapes: higgsCombinexsecSTATshapes.MultiDimFit.mH125.root (r=1.0000, 200 pts in [0.975, 1.025], 2dNLL=1 at [0.9952, 1.0048])
- Z(mumu)H (binned BDT score): run_binned_BDTScore_mumu_oldbdt missing
- Z(ee)H (binned BDT score): run_binned_BDTScore_ee_oldbdt missing
- Z(ll)H = ee+mumu (binned BDT score): run_binned_BDTScore_combined_oldbdt missing
- Z(qq)H 2D, ZH-other as bkg (July def.) [run_2D_mrecoil_mjj_qq_zhbkg_oldbdt]: total: higgsCombinexsec.MultiDimFit.mH125.root (r=1.0000, 160 pts in [0.950, 1.050], 2dNLL=1 at [0.9946, 1.0054]); stat: higgsCombinexsecSTAT.MultiDimFit.mH125.root (r=1.0000, 160 pts in [0.950, 1.050], 2dNLL=1 at [0.9952, 1.0048]); shapes: higgsCombinexsecSTATshapes.MultiDimFit.mH125.root (r=1.0000, 160 pts in [0.950, 1.050], 2dNLL=1 at [0.9946, 1.0054])
- Z(qq)H (1D BDT score): run_binned_BDTScore_qq_oldbdt missing
- combination ee+mumu+qq (BDT-score leptonic cards): run_365_all_bdt_oldbdt missing

## Model-independence bias test (paper Sec 7.2, Table 3 at 240 GeV; bias = r_fit - (1+X) in % of sigma_ZH)

Injection X = mumu 5%, ee 5%, ll 5%, qq 1%, all 1%.

### Z(mumu)H (X = 5%)

| H decay | Paper (240) | Repro 240 | Delta vs paper | Repro 365 |
|---|---|---|---|---|
| bb | -0.01 | -0.019 | -0.009 | +0.004 |
| cc | +0.00 | -0.010 | -0.010 | -0.002 |
| ss | -0.01 | -0.013 | -0.003 | -0.020 |
| gg | +0.00 | -0.002 | -0.002 | -0.013 |
| mumu | +0.09 | +0.130 | +0.040 | +0.067 |
| tautau | -0.01 | -0.002 | +0.008 | -0.008 |
| ZZ | +0.34 | +0.337 | -0.003 | +0.077 |
| WW | -0.01 | -0.003 | +0.007 | -0.012 |
| Za | +0.36 | +0.355 | -0.005 | +0.332 |
| aa | +0.00 | -0.002 | -0.002 | -0.007 |
| inv | +0.01 | +0.005 | -0.005 | -0.008 |

- 240 GeV: 11 modes from run_recoil_2cat_mumu_oldbdt/bias_H*/ (X = 5%); largest |bias| Za (+0.355%); largest |delta vs paper| mumu (+0.040%)
- 365 GeV: 11 modes from run_recoil_2cat_mumu_oldbdt/bias_H*/ (X = 5%); largest |bias| Za (+0.332%)

### Z(ee)H (X = 5%)

| H decay | Paper (240) | Repro 240 | Delta vs paper | Repro 365 |
|---|---|---|---|---|
| bb | +0.00 | -0.006 | -0.006 | -0.003 |
| cc | -0.02 | -0.033 | -0.013 | +0.018 |
| ss | -0.01 | -0.036 | -0.026 | +0.004 |
| gg | -0.03 | -0.042 | -0.012 | -0.010 |
| mumu | -0.01 | -0.021 | -0.011 | +0.008 |
| tautau | -0.01 | -0.015 | -0.005 | +0.007 |
| ZZ | +0.33 | +0.331 | +0.001 | +0.076 |
| WW | -0.03 | -0.032 | -0.002 | -0.000 |
| Za | +0.32 | +0.332 | +0.012 | +0.317 |
| aa | -0.01 | -0.016 | -0.006 | -0.008 |
| inv | +0.01 | -0.007 | -0.017 | +0.017 |

- 240 GeV: 11 modes from run_recoil_2cat_ee_oldbdt/bias_H*/ (X = 5%); largest |bias| Za (+0.332%); largest |delta vs paper| ss (-0.026%)
- 365 GeV: 11 modes from run_recoil_2cat_ee_oldbdt/bias_H*/ (X = 5%); largest |bias| Za (+0.317%)

### Z(ll)H (X = 5%)

| H decay | Paper (240) | Repro 240 | Delta vs paper | Repro 365 |
|---|---|---|---|---|
| bb | -0.01 | -0.010 | -0.000 | +0.004 |
| cc | -0.01 | -0.021 | -0.011 | +0.011 |
| ss | -0.01 | -0.019 | -0.009 | -0.005 |
| gg | -0.01 | -0.015 | -0.005 | -0.008 |
| mumu | +0.04 | +0.065 | +0.025 | +0.042 |
| tautau | -0.01 | -0.005 | +0.005 | +0.002 |
| ZZ | +0.33 | +0.339 | +0.009 | +0.076 |
| WW | -0.02 | -0.013 | +0.007 | -0.003 |
| Za | +0.32 | +0.339 | +0.019 | +0.318 |
| aa | +0.00 | -0.007 | -0.007 | -0.004 |
| inv | +0.01 | -0.003 | -0.013 | +0.007 |

- 240 GeV: 11 modes from run_recoil_2cat_combined_oldbdt/bias_H*/ (X = 5%); largest |bias| ZZ (+0.339%); largest |delta vs paper| mumu (+0.025%)
- 365 GeV: 11 modes from run_recoil_2cat_combined_oldbdt/bias_H*/ (X = 5%); largest |bias| Za (+0.318%)

### Z(qq)H (X = 1%)

| H decay | Paper (240) | Repro 240 | Delta vs paper | Repro 365 |
|---|---|---|---|---|
| bb | +0.04 | +0.052 | +0.012 | +0.066 |
| cc | -0.08 | -0.060 | +0.020 | +0.060 |
| ss | -0.17 | -0.144 | +0.026 | +0.035 |
| gg | -0.04 | -0.028 | +0.012 | +0.107 |
| mumu | +0.26 | +0.220 | -0.040 | -0.363 |
| tautau | -0.04 | -0.064 | -0.024 | -0.412 |
| ZZ | +0.02 | -0.041 | -0.061 | -0.079 |
| WW | -0.07 | -0.102 | -0.032 | -0.098 |
| Za | -0.17 | -0.182 | -0.012 | -0.187 |
| aa | +0.43 | +0.371 | -0.059 | -0.309 |
| inv | +0.51 | +0.448 | -0.062 | -0.271 |

- 240 GeV: 11 modes from run_2D_mrecoil_mjj_qq_oldbdt/bias_H*/ (X = 1%); largest |bias| inv (+0.448%); largest |delta vs paper| inv (-0.062%)
- 365 GeV: 11 modes from run_2D_mrecoil_mjj_qq_oldbdt/bias_H*/ (X = 1%); largest |bias| tautau (-0.412%)

### combination (X = 1%)

| H decay | Paper (240) | Repro 240 | Delta vs paper | Repro 365 |
|---|---|---|---|---|
| bb | +0.02 | +0.032 | +0.012 | +0.059 |
| cc | -0.06 | -0.039 | +0.021 | +0.054 |
| ss | -0.12 | -0.092 | +0.028 | +0.031 |
| gg | -0.03 | -0.019 | +0.011 | +0.094 |
| mumu | +0.18 | +0.137 | -0.043 | -0.320 |
| tautau | -0.03 | -0.038 | -0.008 | -0.362 |
| ZZ | +0.03 | -0.003 | -0.033 | -0.068 |
| WW | -0.05 | -0.064 | -0.014 | -0.088 |
| Za | -0.09 | -0.091 | -0.001 | -0.159 |
| aa | +0.28 | +0.229 | -0.051 | -0.272 |
| inv | +0.34 | +0.279 | -0.061 | -0.241 |

- 240 GeV: 11 modes from run_240_all_oldbdt/bias_H*/ (X = 1%); largest |bias| inv (+0.279%); largest |delta vs paper| inv (-0.061%)
- 365 GeV: 11 modes from run_365_all_oldbdt/bias_H*/ (X = 1%); largest |bias| tautau (-0.362%)

