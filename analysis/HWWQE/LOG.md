# HWWQE log

## 2026-10-15 — Phase 0 started

**Environment.** Key4hep 2026-04-08 (the current stable release: the default
`/cvmfs/sw.hsf.org/key4hep/setup.sh` resolves to it, and the repository `setup.sh`
pins `-r 2026-04-08`). Python 3.13.8, numpy 2.2.6, scipy 1.16.3, matplotlib 3.10.7,
pytest 9.0.0, uproot 5.6.3, awkward 2.8.5. Work on git branch `hwwqe`.

**Done.**
- Checked the transcription in PLAN.md Sec. 3.3 against 2302.00683 v3 (App. A–B,
  Eqs. 2.23–2.48, 3.5–3.13). Eqs. (B.1)/(B.2) are transcribed exactly.
- Found that three normalisation statements copied from the paper's Sec. 2.4 are
  inconsistent with its Appendix B (details and evidence in CONVENTIONS.md §2):
  Π needs a factor ½, the p–q duality has 2δ, the estimators are
  fₐ = ⟨p₊ᵃ⟩/6, gₐ = ⟨p₋ᵃ⟩/6, hₐᵦ = ⟨p₊ᵃp₋ᵇ⟩/4. Fixed in the estimators, functions kept verbatim.
- The paper's closed forms Eqs. (3.5)–(3.6) agree with the plan's |Ψ_H⟩ coefficient by
  coefficient; its figure labels (entropy, 𝒞₂, I₃ vs M_W*) are reproduced with
  m_H = 125.0, M_W = 80.4 GeV.
- Created the repository layout, `qtomo/basis.py`, `qtomo/sm.py`, config loader,
  plotting helper, `tests/test_basis.py`, `tests/test_sm.py` (43 tests pass).
- The Key4hep GaudiTesting pytest plugins print CTest XML; disabled in `pytest.ini`.

**Flavour-tagger environment check (Ang's question; ≤ 1000-event tests in both stacks).**
- Confirmed: the tagger runs correctly only in the winter2023 environment
  (`setup_hbs.sh`: Key4hep 2024-03-10 + FCCAnalyses-winter2023). On official
  winter2023 H→bb / H→WW files the 7-class scores sum to 1, true b jets get mean B score
  0.90, and MC truth reads correctly (final-state energy sum 240.00 GeV).
- Current stack (`setup.sh`, 2026-04-08) fails in two independent ways:
  1. winter2023 files under EDM4hep 1: tagger JIT errors (`_EFlowTrack_2_track`,
     TrackerHitData, type→PDG), track covariance and MC momenta silently lost;
  2. a build-level bug: with GCC 14.2 an unqualified `abs(double)` resolves to `int abs(int)`
     (probe: `abs(0.4937-0.1396)` = 0). In the compiled libFCCAnalyses `get_isMu/El/ChargedHad`
     return 1 for every particle, `ReconstructedParticle::remove` removes the wrong particle,
     `resonanceBuilder` and `HiggsTools::acolinearity` are wrong — on any file format.
     Upstream develop (37da2c4) fixes the tagger PID functions only.
- Models: use the winter2023 7-class model `wc_pt_7classes_12_04_2023` (G, U, S, C, B, TAU, D;
  copy in `analysis/Hbs/mumu/`); the v1 model merges u and d. 1k-event performance on H→WW:
  s vs u+d AUC ≈ 0.90 (0.84 for W* jets), c vs s 0.98, d vs u only 0.61–0.63; W→cs: s jet
  correct in 94 %; W→ud: d jet correct in 68 % (scores) / 59 % (jet charge κ = 0.3).
- No EDM4hep-1 ZH(ℓℓ) or H→WW samples exist; channel A signal is `wzp6_ee_{mumu,ee}H_HWW_ecm240`
  (winter2023, 400k each).
- Proposed for Phase 1 (deviation from PLAN Sec. 2, needs approval): stage1 in the winter2023
  environment as standard `fccanalysis run` scripts; qtomo and all Python downstream in `setup.sh`.

**Machinery (PLAN Sec. 3) complete — 197 tests pass (100 s).** Built per module group,
then each group got an independent physics review and a numerics review, and the findings
were verified and fixed:
- `frames.py`: H frame, {n̂, r̂, k̂}, decay angles, `construct_event` (inverse). Key test:
  first-principles matrix element |M|² ∝ (p_ν·p_ℓ⁻)(p_ν̄·p_ℓ⁺) equals
  Tr[ρ_SM(ϰ)(Π₊⊗Π₋)] at the frames.py angles to < 1e-9 relative residual; a generic
  HVV coupling (with the ε-tensor term) built from explicit spinor currents agrees with the
  polarisation-vector ρ — this fixes the frame handedness and the phases of |Ψ_H⟩.
- `toy.py`, `tomography.py`: accept-reject generator, per-event SM spectrum, mistag flips;
  chunked moment accumulator with covariance and unbiased (U-statistic) squares.
- `bell.py`: CGLMP operator, I₃ optimiser (exact gradient/Newton, 48 random starts + warm
  start), 𝒞₂, entropy. λ_max(B) = 2.9149, maximally entangled 2.8729, product states ≤ 1.474,
  paper Fig. 4 values reproduced. Review finding: 4 random starts per pseudo-experiment miss
  the global maximum in 1–12 % of toys (by up to 0.07), so toys use the default 48.
- `reweight.py`, `response.py`, `stats.py`. The response fixer was interrupted mid-rewrite;
  restored the reviewed version (tests green). Two real findings deferred to Phase 2:
  a single response matrix is biased when the state depends on m_W* (needs m_W*-binned
  response), and weighting the GLS fit by the observed covariance biases small samples
  (use model second moments). The untested rewrite is kept in `outputs/drafts/`.
  Fixed myself: `stats` significance beyond the null range is now a flagged lower limit
  by default (Gaussian-tail extrapolation overstated Z for skewed nulls) and failed (NaN)
  pseudo-experiments are excluded and counted; the flaky pure-base ratio-weight test was
  replaced by a bounded-base test plus a check of the W⁻² weight tail.
- End-to-end chain (toy → lab ZH events → frames → tomography → bell): angle round trip
  2e-12; closure χ²/ndf = 70.6/80 against the spectrum-averaged SM state (N = 2e5).

**Toy closure and ideal reach (PLAN Sec. 4 tasks 2-3) — done, GATE 0 report written.**
- Drivers `analysis/phase0_{closure,reach,analytic}.py`; local ≤ 1k-event tests of every job
  type, one condor test job, then 140 closure + 220 reach jobs on SDCC (clusters 565, 566),
  all succeeded.
- Closure: 80 coefficients close (χ²/ndf 0.985–1.027, pulls N(0,1)); σ ∝ N^-0.5 everywhere;
  all biases → 0, but raw I₃ is biased by ≈ +2σ at every N (bias ∝ 1/√N, from maximising
  over U, V on an unphysical ρ̂); physical-projected I₃ ≈ −0.8σ. Null calibration essential.
- Reach (spectrum-averaged SM: I₃ = 2.643, 𝒞₂ = 0.952, h₄₄ = 0.0988): e.g. A σ(I₃) = 0.114,
  B 0.035; asymptotic σ agree with pseudo-experiments for raw I₃, 𝒞₂, h₄₄ (conservative for
  I₃ at w ≥ 0.2). Mistag w = 0.3 costs +19 % (one leg) / +57 % (two legs) in σ(I₃) (asymptotic).
- Report: `reports/gate0.md`. **Waiting for Ang's approval at GATE 0.**

**Open questions.**
- e⁺ beam direction and crossing angle in the IDEA samples (needed for p̂): read off
  the generator record in Phase 1.
- Generator masses and widths of the samples (for truth validation, Phase 1).
- Jet-charge normalisation (Σ|p|^κ vs |p_jet|^κ) to be fixed in Phase 2.
