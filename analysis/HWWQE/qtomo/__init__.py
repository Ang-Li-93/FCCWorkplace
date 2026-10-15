"""qtomo: quantum tomography of H -> W W* at FCC-ee.

Modules (see ../CONVENTIONS.md for every convention and normalisation):
    basis       Gell-Mann basis, rho <-> (f, g, h), spin-1 analyser functions
    sm          analytic tree-level SM state of H -> W W* and the W* mass spectrum
    frames      Higgs rest frame, {n, r, k} axes and decay angles from four-vectors
    toy         accept-reject toy generator and analyser mistag
    tomography  moment estimators of f, g, h and their covariance
    bell        CGLMP operator, optimised I3 and the concurrence bound C2
    reweight    decay-angle reweighting between spin states
    response    linear response and unfolding of the moments
    stats       bootstrap, pseudo-experiments and significances
    config      YAML configuration loader
    plotting    common plot style and labels
"""
