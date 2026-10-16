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

## 2026-10-15 — Phase 1 started (Ang: focus l nu q q, 240 GeV, standard lumi; kinit renewed)

Ang approved moving on; ℓνqq first (channel A pilot, then B), √s = 240 GeV, 10.8 ab⁻¹
(standard FCC-ee 240 GeV luminosity; same as the repository's ZH analyses). Taken as
approval of the Gate-0 normalisation fix and of the winter2023 stage1 environment.
Ang asked whether Z→ℓℓ or Z→νν is the better start for ℓνqq: Z→ℓℓ — with Z→νν the
missing momentum is the sum of three neutrinos, so the W neutrino and the H frame are
underconstrained (the plan's dead category).

**Samples (Sec. 5.1).** Latest IDEA productions on EOS: winter2023 and pre_summer2026; the
latter has no ZH(H→WW*) at 240 GeV (only νν H→qq), so winter2023 is used.
`config/samples.yaml` (generated by `analysis/phase1_samples.py` from the EOS listing, the
winter2023 procDict and the FCC-config cards): 6 signal + 98 background samples.
Signal: A = wzp6_ee_{mumu,ee}H_HWW_ecm240 (400k each, 25× data), B = wzp6_ee_{qq,ss,cc,bb}H_HWW
(9–22× data). Generator: Whizard 3.0.3 ee → Z H (on-shell H), Gaussian BES 0.185 % per beam +
ISR, no beamstrahlung; H → W⁺W⁻ by Pythia6 (MDME(226)=1, m_H = 125.0, Γ_H = 4.143 MeV,
MSTP(25) default). Pythia8 backgrounds (WW, ZZ, Zqq): ISR on, no BES.
Truth record: e⁻ beam along +z, e⁺ along −z, head-on; H → W⁺W⁻ → pre-shower fermions.

**Truth stage1 (Sec. 5.2).** `stage1/truth_hww.py` + `truth_functions.h` (standard
`fccanalysis run`, winter2023 env); tested on 1k and 20k local events (all slots found);
53 condor jobs over the 6 signal samples (cluster 567).

**Truth validation result (Sec. 5.2).** All 53 stage1 jobs succeeded (5.3M events; 1.55M
ℓνqq with ℓ = e, μ). Finding: the recorded H is Pythia6's documentation copy with the
Whizard momentum; the decaying copy is shifted by the shower recoil, so p_H ≠ p_W⁺ + p_W⁻ in
20 % (Z→μμ) to 99 % (Z→qq) of events. With the recorded H the all-decays comparison failed
(χ²/ndf = 108.7/80, p = 0.018; 3–4σ beam-correlated f₂, f₇, g₂, g₇ and ⟨cosΘ⟩ = 0.008).
With the W⁺W⁻ rest frame (correct for a spin-0 parent): ℓνqq χ²/ndf = 88.3/80 (p = 0.25),
all decays 72.5/80 (p = 0.71), every M* bin p > 0.16; I₃ at fixed optimal settings
2.680 ± 0.010 (ℓνqq) vs analytic 2.695. → Outcome A (central signal usable), pending the
verification workflow. Second finding: Pythia6 generates W masses only in [12.0, 111.8] GeV
(no W* below 12 GeV). Both matter for Phase 2 (reco H frame from the recoil; M* coverage).
Verification, sensitivity, mass-window and dedicated-generation feasibility running.

**Mechanism of the recorded-Higgs shift (verified on 3000 Z→μμ and 1442 clean Z→qq events).**
Whizard generates e⁺e⁻ → f f̄ H with no Z line in the record. Showering/hadronising the Z decay
products raises the invariant mass of the Z system (Z→qq: median +1.49 GeV, 90 % +5.5 GeV;
Z→μμ: 90 % +0.02 GeV, from photon FSR). Energy–momentum is restored by rescaling the (Z system,
H) pair along its common axis in the rest frame of the colliding (post-ISR) beams: the H keeps
its mass and direction (angle 0.000°) but loses momentum (Z→qq median 1.58 GeV, 90 % 6.1 GeV),
then decays. Checks, all to ≤ 3e-5 GeV: hard-process conservation; H shift = −(Z_post − Z_doc);
|p_WW| equals the two-body momentum for the post-shower Z-system mass. The PDG-25 entry is the
pre-rescaling copy. Implications: truth references must be W⁺W⁻-based; the reco recoil against
the complete post-shower Z system targets the correct frame by momentum conservation (smearing
then comes from ISR, mean 1.9 GeV of photons per event, BES, FSR recovery and jet assignment);
the Z→qq system mass is pushed up by ~1.5 GeV by this matching (generator-modelling caveat).

**Channel C truth validation (Z→νν samples; done while the verification workflow runs).**
Truth stage1 on wzp6_ee_{nunu,numunumu,nuenue}H_HWW_ecm240 (36 files, 3.6M events; cluster 568).
Recorded H = W⁺ + W⁻ in 100 % of Z→νν events (no shower of the Z decay products — confirms the
rescaling mechanism). H→qqqq truth vs analytic (W⁺W⁻ frame): 1.65M events, χ²/ndf = 76.9/80
(p = 0.58); pure ZH (ν_μ) p = 0.76, ν_e incl. WW fusion p = 0.38; I₃ fixed-setting 2.696 ± 0.010
vs 2.694; h₄₄ 0.1065 ± 0.0015 vs 0.1043. All decays in these samples p = 0.94 (one M* bin at
p = 0.006 among 14 bin tests). Results: outputs/phase1/truth_tomography_channelC.json
(scratch script copied to outputs/phase1/scripts/truth_C.py; to be folded into phase1_truth.py).

**Channel order (Ang, 2026-10-15).** Ang first suggested A + C (Z→ℓℓ, Z→νν) with B parked, then
asked whether to organise by H→WW decay mode instead: finish H→ℓνqq with Z→ℓℓ (A) and Z→qq (B)
first. That is the plan's original order; recommended (shared H-side machinery, B has 10× A's
statistics, B's truth validation passed in the W⁺W⁻ frame). Awaiting Ang's final choice before
Phase 2; Phase 1 covers A, B (and C's truth validation) either way.

**Decision (Ang, 2026-10-15): one channel first — channel A (Z→ℓℓ, H→ℓνqq) at 240 GeV.**
B, C, D later (C's truth validation already done). Channel-A facts: recorded-H shift in 20.3 %
of Z→ee and Z→μμ events, |Δp_H| median 0.02 GeV, 90 % < 0.9 GeV, 1 % > 5.7 GeV (small);
A-only truth validation 233,897 ℓνqq events χ²/ndf = 72.1/80 (p = 0.72), all M* bins p ≥ 0.21,
I₃ fixed-setting 2.684 ± 0.025 vs 2.694. GATE 1 report to be written for channel A.

**Phase 1 verification workflow (5 investigators + adversarial cross-check; results preserved in
outputs/phase1/workflow_results/, scripts analysis/phase1_validation.py, phase1_kinematics.py).**
- Extraction: an independent Python walk of the record matches the stage1 slots in all 200k events
  of one Z→μμ and one Z→qq file (0 mismatches); independent angle code agrees with qtomo.frames.
- Calibration: χ² test calibrated (20 and 100 subsample splits: uniform p-values; whitened
  residuals std 1.003 ± 0.008). Reach (ℓνqq, one-parameter, 95 % CL): admixture ε ≈ 1.4–1.7×10⁻³
  for decohered / 𝟙/9 / CP-odd; measured ε̂ consistent with 0, upper limits 1.9–2.5×10⁻³ (channel A
  alone σ_ε ≈ 2×10⁻³). Subsets consistent (e/μ, cs/ud, W⁺/W⁻ leptonic, A/B samples, τ modes;
  492 tests, smallest p 0.0013 as expected). Largest feature: Im ρ₊₋,₋₊ (h₄₅ − h₅₄) −3.1σ for
  W⁺-leptonic events only, read as a fluctuation (P- and T-even generator). The generator omits
  fermion-mass effects (Pythia6 massless correlation; excluded > 7σ for τ and s analysers at low
  M*): negligible for channel A (≈ 0.02 χ² units at data statistics).
- Kinematics: the 12 GeV floor is Pythia6's default CKIN(45) = CKIN(47) = 12 GeV (pydata.f, pyresd.f,
  pyofsh.f of Pythia 6.427, verified in source and by a direct decay test). f(M* < 12 GeV) = 5.79 %
  (PDG) – 5.89 % (generator parameters): channel A 548 of 9463 ℓνqq events (10.8 ab⁻¹); procDict
  σ×BR overstates M* ≥ 12 GeV yields by ≈ 6.2 %. Truncated SM reference: I₃ 2.694, 𝒞₂ 1.028, h₄₄ 0.1043
  (full spectrum 2.643, 0.952, 0.0988). Generator W line shape: m_W = 80.449 ± 0.001, Γ_W = 2.077 ±
  0.001 GeV (Pythia6 80.45 / 2.0764), not PDG. Higgs frame for channel A: recoil against the
  post-shower Z system smeared only by ISR (mean photon energy 1.8 GeV, tails) and BES (σ(√s′) =
  0.31 GeV): core ≈ 1–2 mrad, tails 8 %, coefficient shifts ≤ 0.14σ (data stat.), ≤ 0.1σ on I₃, 𝒞₂, h₄₄.
- Sample pages: samples.yaml matches the official pages for all 104 entries; bug: EOS '.sys.v#'
  version directories leak into the file lists of 7 samples (none in channel A signal; Zqq, ZZ).
  BR(H→WW) in the procDict = 0.2152 (YR4 at 125.09 GeV) while the generator uses m_H = 125.0.
  Central production stack: key4hep 2022-12-23 (Delphes 3.5.1pre05).
- Generation (S2/S3/S4 feasibility, channel A first): WHIZARD's isotropic/diagonal switches act only
  on on-shell factorised decays and fail for H→WW* (tested). Route (b): WHIZARD ℓℓH with the full
  H→ℓνqq′ matrix element, then redraw each W decay direction in its rest frame (iso: exactly 𝟙/9; diag:
  decohered SM; copy: S1), then Pythia8 + Delphes IDEA. Tests (4000 events, generator level, channel A):
  S1 vs SM p = 0.75, S2 vs 𝟙/9 p = 0.90, S3 vs decohered p = 0.57, S2 reweighted vs S1 p = 0.93;
  end-to-end through Delphes and stage1 OK; M* < 12 GeV present (6.3 ± 0.4 %). Cost for channel A at
  10× data: ≈ 1.1 CPU-h, 0.8 GB per sample type. S4 (6f continuum): integration dominated,
  ≈ 250–500 CPU-h for the 8 channel-A cards; tested component ≈ 1 % of signal.
- Cross-check findings to fix before any production: Pythia8 lets W bosons radiate photons by
  default (TimeShower:QEDshowerByOther) — 3–4 % of test events have first-copy W ≠ analyser +
  partner; new EDM4hep files use '_Particle_parents/_daughters' branch names; only the μμ channel-A
  card was run (ee untested); the fixed-settings I₃ is ambiguous (degenerate optimal settings) — use
  the χ² tests as the primary metric.

## 2026-10-16 — Phase 1 channel-A fixes (finished by hand after the fix workflow stopped)
The fix workflow stopped (a write of a rewritten analysis/phase1_truth.py was declined, then the
session ended); phase1_truth.py kept unchanged. Verified and committed the partial edits:
stage1 handles both MC-relation conventions and takes the decaying W copies (output identical on
1000 central events); study parameters of phase1_validation.py / phase1_kinematics.py in
config/phase1.yaml (outputs identical to the previous scripts); the unused 'truth:' block removed.
samples.yaml: '.sys.v#' EOS version directories removed from the file lists (1619 entries; the 104
previous entries otherwise unchanged), 102 samples added (exclusive H→ZZ*, BES/mH variations, 4f,
radiative), channel tags, production stack (key4hep 2022-12-23 per the FCC sample pages), signal
generator facts and normalisation notes. Pythia8: TimeShower:QEDshowerByOther = off (Pythia 8.310
xmldoc TimelikeShowers.xml l. 832: "This will also allow the W boson to radiate"). Rule-7 tests of the
channel-A chain (μμ and ee cards, copy/iso/diag, 1000 events each): all targets reproduced, no W
radiation, details in gen/README.md.
