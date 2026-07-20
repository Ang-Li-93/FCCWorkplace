# Draft referee reply — baseline without multivariate selection

> Referee: "...a baseline analysis in the spirit of the LEP searches, with
> sideband-based background determination and without multivariate methods,
> should be shown."

We thank the referee for this suggestion. We have added a dedicated baseline
scenario to the paper (new Table X and accompanying text in Section
"Results"), in which no multivariate information is used at any stage: the
selection is purely cut-based and the cross section is extracted from a
one-dimensional fit to the recoil-mass distribution over the full
100-150 GeV range in a single region. Since this is a projection study with
simulated data, the LEP-style sideband method translates into leaving the
background normalizations free in the fit, so that they are determined in
situ by the sideband regions of the fitted recoil spectrum; only the
background shapes are taken from simulation, as in any sideband-based
technique. The nominal analysis relies on the same in-situ constraint,
implemented through the low-BDT control region.

The baseline yields combined precisions of 0.64% (240 GeV) and 1.31%
(365 GeV), compared to 0.31% and 0.52% for the nominal analysis. The
multivariate selection is thus worth a factor of about two in combined
precision. The gain is largest exactly where the recoil mass alone is
least discriminating: a factor ~2.4 per leptonic channel at 365 GeV,
where ISR and the beam-energy spread broaden the recoil peak, and a
factor ~3 in the hadronic channel at 240 GeV, where without the low-BDT
control region the individual background normalizations become nearly
degenerate under the recoil shape alone. We also note that the
model-independence tests of Section 7.2 apply to the nominal analysis and
bound any Higgs-decay-composition dependence introduced by the
multivariate selection to below the statistical precision.

## Notes for us (not part of the reply)
- Numbers from the SDCC reproduction pipeline (nominal results agree with
  the published Table 1 within 10-20%; per-channel leptonic 240 numbers
  agree to ~1%). Regenerate with the official pipeline if preferred:
  the full machinery is makeWS_noBDT_baseline.py + datacard_recoil_qq.txt
  + run_{240,365}_noBDT_all / run_{240,365}_noBDT_ll in S{240,365}/combine.
- LaTeX drop-in: paper_edits/baseline_paragraph.tex (matches the
  tab:results_xsec style, uses the paper macros; check the section label
  references \ref{sec:evtsel} / \ref{sec:modelindep} against the actual
  label names in the source).
