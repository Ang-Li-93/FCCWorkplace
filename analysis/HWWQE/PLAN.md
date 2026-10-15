# Quantum tomography of H→WW* at FCC-ee: analysis plan for Claude Code

Owner: Ang Li (BNL). Read this whole file before doing anything. Work phase by phase. Each phase ends with a **GATE**: stop, write the gate report, and wait for human approval before starting the next phase.

---

## 0. Scope and goals

Measure the spin density matrix ρ of the W⁺W⁻* system in e⁺e⁻ → ZH, H → WW* at √s = 240 GeV (10.8 ab⁻¹, IDEA Delphes fast simulation). Extract:

- the 80 coefficients f_a, g_a, h_ab (Gell-Mann basis), restricted to the SM/CP-allowed subset for fits;
- the CGLMP Bell observable I₃ (optimised over local unitaries);
- the concurrence lower bound 𝒞₂ (entanglement witness);
- the Δm = 2 coherence witness (h₄₄, h₅₅; cos 2Δφ between decay planes), which survives d/u-type confusion;

with expected significances, including bias calibrated on separable "null" samples.

Channel priority (do not reorder without approval):

| Priority | H→WW* | Z decay | Reason |
|---|---|---|---|
| A | ℓνqq | ℓℓ (e, μ) | single ν overconstrained via recoil, clean pilot |
| B | ℓνqq | qq | ~10× statistics, same ν treatment, jet pairing |
| C | qqqq | νν | H fully visible, flavour-blind rank-2 witness |
| D | ℓνℓν | ℓℓ, qq | two-ν ambiguity, last |

Dead categories (do not study): ℓνℓν + Z→νν, ℓνqq + Z→νν. qqqq + Z→qq is optional, only after C.

Frame this as quantum tomography / entanglement within QFT, not a loophole-free locality test (see Abel, Dreiner, Sengupta, Ubaldi, JHEP08(2026)067).

---

## 1. Rules for the agent

1. Never invent sample names, file paths, cross sections or tool options. List directories, read docs and source, then use what exists. If something is missing, stop and report.
2. Every physics convention (frames, signs, normalisations) must be fixed by a passing unit test against the analytic SM result (Section 3) before it is used on MC.
3. Never change a convention to make a downstream number look better. If an MC result disagrees with the analytic expectation, report it.
4. Every number in a report carries a statistical uncertainty (bootstrap or pseudo-experiments) and the sample/version it came from.
5. Keep all configuration in `config/*.yaml`. No hard-coded paths in analysis code.
6. Commit after each completed task with a descriptive message. Keep a running `LOG.md` (date, what was done, what failed, open questions).
7. Large jobs go to HTCondor. Test every job type on ≤ 1k events locally first.
8. Plots: matplotlib, PDF + PNG, axis labels with units, "FCC-ee simulation (Delphes IDEA), √s = 240 GeV" label.
9. British spelling in all text output.

---

## 2. Environment and repository

```
source /cvmfs/sw.hsf.org/key4hep/setup.sh      # use the current stable release; record its version in LOG.md
```
FCCAnalyses (`fccanalysis run`) for EDM4hep → flat ntuples. Downstream analysis in Python: uproot, awkward, numpy, scipy, matplotlib, pytest.

Repository layout to create:

```
config/          samples.yaml, selection_*.yaml, generation/*.sin
gen/             Whizard sindarin cards, Pythia cmnd files, submission scripts
stage1/          FCCAnalyses scripts (EDM4hep → flat ntuples), one per channel
qtomo/           Python package: basis.py, frames.py, tomography.py, bell.py,
                 reweight.py, toy.py, response.py, stats.py
tests/           pytest unit tests (must all pass before any MC phase)
analysis/        channel drivers: chA_lvqq_Zll.py, ...
reports/         gate reports (markdown) + figures
LOG.md
```

---

## 3. Physics conventions (implement in `qtomo/`, test in `tests/`)

### 3.1 Basis
- Spin-1 states ordered (+1, 0, −1). T¹…T⁸ standard Gell-Mann matrices, Tr[TᵃTᵇ] = 2δᵃᵇ.
- ρ = 𝟙/9 + Σ fₐ (Tᵃ⊗𝟙) + Σ gₐ (𝟙⊗Tᵃ) + Σ hₐᵦ (Tᵃ⊗Tᵇ)
- fₐ = Tr[ρ(Tᵃ⊗𝟙)]/6, gₐ = Tr[ρ(𝟙⊗Tᵃ)]/6, hₐᵦ = Tr[ρ(Tᵃ⊗Tᵇ)]/4.
- First factor = W⁺, second factor = W⁻.

### 3.2 Frames
- Work in the Higgs rest frame (truth: H four-momentum; reco: recoil or visible H system depending on channel).
- k̂ = W⁺ direction in the H frame. p̂ = e⁺ beam direction boosted into the H frame. r̂ = (p̂ − cosΘ k̂)/sinΘ, n̂ = r̂ × k̂ (right-handed {n̂, r̂, k̂}). The same axes are used for both W bosons.
- Decay angles (θ±, φ±): direction of the analyser in the respective W rest frame (boost H frame → W frame), polar angle w.r.t. k̂, azimuth w.r.t. n̂ in the (n̂, r̂) plane.
- Analysers: W⁺ → ℓ⁺ (leptonic) or the down-type **antiquark** (hadronic, W⁺→u d̄); W⁻ → ℓ⁻ or the down-type **quark**.
- Off-shell labelling: M = max(m_W⁺, m_W⁻), f = min/max. Store both W masses and which one is off-shell.

### 3.3 Decay analysers and projection functions (Fabbrichesi et al., 2302.00683, App. B)
Π± = 𝟙/3 + Σ q±ᵃ Tᵃ, with

```
q1 = (1/√2) sinθ (cosθ ± 1) cosφ        q2 = (1/√2) sinθ (cosθ ± 1) sinφ
q3 = (1/8)(1 ± 4cosθ + 3cos2θ)          q4 = (1/2) sin²θ cos2φ
q5 = (1/2) sin²θ sin2φ                  q6 = (1/√2) sinθ (−cosθ ± 1) cosφ
q7 = (1/√2) sinθ (−cosθ ± 1) sinφ       q8 = (1/(8√3))(−1 ± 12cosθ − 3cos2θ)
```
Dual (Wigner P) functions:
```
p1 = √2 sinθ (5cosθ ± 1) cosφ           p2 = √2 sinθ (5cosθ ± 1) sinφ
p3 = (1/4)(5 ± 4cosθ + 15cos2θ)         p4 = 5 sin²θ cos2φ
p5 = 5 sin²θ sin2φ                      p6 = √2 sinθ (−5cosθ ± 1) cosφ
p7 = √2 sinθ (−5cosθ ± 1) sinφ          p8 = (1/(4√3))(−5 ± 12cosθ − 15cos2θ)
```
Estimators: fₐ = ⟨p₊ᵃ⟩, gₐ = ⟨p₋ᵃ⟩, hₐᵦ = ⟨p₊ᵃ p₋ᵇ⟩ (event means).

These formulas were transcribed by hand. Unit tests must verify them:
- (3/4π)∫ p±ⁿ q±ᵐ dΩ = δⁿᵐ numerically;
- Π± is Hermitian, Tr Π± = 1, Π± is a rank-1 projector for every (θ, φ);
- the moment estimator recovers the input ρ from toy events (Section 3.6).
If any test fails, fix the transcription against the paper and report it.

### 3.4 Analytic SM state (validation target)
ϰ = (m_H² − M₁² − M₂²)/(2 M₁ M₂), |Ψ_H⟩ = (|+−⟩ − ϰ|00⟩ + |−+⟩)/√(2+ϰ²).
Also implement the closed forms of 2302.00683 Eqs. (3.5)–(3.6) for fₐ, hₐᵦ vs f = M₂/M₁, and test that they agree with the coefficients computed directly from |Ψ_H⟩ (phase conventions may differ by local unitaries: compare invariant quantities such as purity, Tr[ρ_A²], 𝒞₂, and the set of |hₐᵦ| if needed, and report which).

### 3.5 Observables
- 𝒞₂ = 2 max(0, Tr[ρ²] − Tr[ρ_A²], Tr[ρ²] − Tr[ρ_B²]).
- Unrotated CGLMP operator, consistent with 2302.00683 Eq. (2.40) and the normalisation hₐᵦ = Tr[ρ TᵃTᵇ]/4:
  B = T⁴⊗T⁴ + T⁵⊗T⁵ − (1/√3)[T¹⊗T¹ + T¹⊗T⁶ + T⁶⊗T¹ + T⁶⊗T⁶ + T²⊗T² + T²⊗T⁷ + T⁷⊗T² + T⁷⊗T⁷]
- I₃ = max over U, V ∈ U(3) of Tr[ρ (U⊗V)† B (U⊗V)], numerical optimisation (scipy, multiple random starts).
- Unit tests: maximally entangled qutrit state (Σ|ii⟩/√3) gives I₃ ≈ 2.873 after optimisation; no state exceeds ≈ 2.915; product states and 𝟙/9 give I₃ ≤ 2 and 𝒞₂ = 0. If these fail, B or the optimiser is wrong: stop.
- Physical-ρ handling: a reconstructed ρ may have negative eigenvalues. Report the raw result and the result after projection to the nearest physical state; quote both.

### 3.6 Toy generator (`qtomo/toy.py`)
Sample (Ω₊, Ω₋) from (3/4π)² Tr[ρ (Π₊⊗Π₋)] by accept–reject (bound: 9/(4π)²). Used for all closure tests and for statistical-power studies independent of MC.

### 3.7 Reweighting (`qtomo/reweight.py`)
For a base sample with isotropic decays (ρ_base = 𝟙/9): w = 9 Tr[ρ_target (Π₊⊗Π₋)], bounded by 9. For a non-isotropic base: w = Tr[ρ_t ΠΠ]/Tr[ρ_b ΠΠ], reject if the denominator < ε and report the fraction.
Targets: SM (m_W*-dependent), decohered SM (coherences zeroed), 𝟙/9, single basis elements (one coefficient = ±ε), anomalous HWW (later).

---

## 4. Phase 0: machinery (no MC)

Tasks:
1. Implement Section 3 in `qtomo/` with full pytest coverage.
2. Toy closure: for SM states at several m_W*, generate 10⁴…10⁶ toy events, reconstruct f, g, h, I₃, 𝒞₂; show bias → 0 and σ ∝ 1/√N.
3. Ideal statistical reach: with the yields below, quote σ(I₃), σ(𝒞₂), σ(h₄₄) per category for perfect analysers, and for a hadronic leg with d-type mistag rate w ∈ {0, 0.1, 0.2, 0.3, 0.5} (rank-1 terms dilute by (1−2w); rank-2 terms do not).

Indicative pre-selection yields (verify against sample metadata later): N(ZH, H→WW*) ≈ 4.6×10⁵; ℓνℓν ≈ 2.1×10⁴, ℓνqq ≈ 1.3×10⁵, qqqq ≈ 2.1×10⁵, before Z branching (ℓℓ 6.7%, νν 20%, qq 70%).

**GATE 0** report: test results, closure plots, reach table. Wait.

---

## 5. Phase 1: samples

### 5.1 Central samples
1. List `/eos/experiment/fcc/ee/generation/DelphesEvents/` (find the latest IDEA production) and the corresponding sample-info pages. Record exact names, cross sections, event counts, generator, and whether beam-energy spread/ISR/beamstrahlung are included in `config/samples.yaml`.
2. Identify: ZH with H→WW* for each Z decay mode; ZH with H→ZZ*, H→ττ, H→bb/cc/gg (backgrounds); WW, ZZ, Zγ/qq, ττ inclusive.

### 5.2 Truth validation of the central signal (decides whether we generate signal)
1. Stage1 script dumping truth H, W⁺, W⁻ (or fermion pairs) and decay fermions.
2. Truth tomography in bins of m_W*: compare to Section 3.4. Metric: per-coefficient pulls and invariant quantities.
3. Outcome A: agreement within stat → central samples usable for signal. Outcome B: disagreement → flag to the FCC MC contact, proceed with 5.3 for signal.

### 5.3 Dedicated generation (Whizard, from the key4hep stack)
Start from the official FCC-ee sindarin cards (HEP-FCC/FCC-config repository) so ISR, beamstrahlung (CIRCE2) and beam settings match production. Read the Whizard manual for the exact syntax of every option used and cite the manual section in comments.

Samples (240 GeV, ℓ = e, μ, plus τ only if needed later):
- S1 `sm_full`: e⁺e⁻ → Z H with full H → WW* → 4f matrix element and spin correlations, Z → ℓℓ / qq / νν. Prefer the full 6-fermion process restricted to Higgs-resonant diagrams; if impractical, factorised production × decay chain with spin correlations kept. Document which.
- S2 `iso_decay`: identical, with isotropic W decays (Whizard isotropic-decay switch for factorised chains; verify it behaves for an off-shell W*). This is the reweighting base and the 𝟙/9 null.
- S3 `diag_decay` (optional): diagonal-decay switch (coherences removed), to cross-check reweighting to the decohered state.
- S4 `bkg_6f`: e⁺e⁻ → same 6-fermion final states, non-Higgs diagrams (ZWW, ZZ), and the full set including interference, for Channel A/B final states. Needed for the coherent continuum under the recoil peak.

Pipeline: Whizard (LHE or HepMC) → Pythia8 shower/hadronisation (no re-decay of H/W) → `DelphesPythia8_EDM4HEP` with the IDEA card and EDM4hep output card used in the central production. Validate a few hundred events end to end before submitting.
Target statistics: ≥ 10× expected data yield per category for S1/S2.

Validation:
- S1 truth tomography vs analytic (as 5.2).
- Reweight S2 → SM and compare to S1 (all coefficients, m_W* spectrum unaffected).
- S2 truth: all coefficients consistent with zero, I₃ ≤ 2, 𝒞₂ = 0.

**GATE 1** report: sample table, validation plots, decision on central vs dedicated signal. Wait.

---

## 6. Phase 2: Channel A (H→ℓνqq, Z→ℓℓ)

### 6.1 Selection (FCCAnalyses stage1 → stage2)
- Exactly 3 isolated leptons (e/μ), p > 5 GeV; Z candidate = OS same-flavour pair with m closest to m_Z, require m_ℓℓ ∈ [86, 96] GeV and recoil mass ∈ [120, 140] GeV (tune later). Remaining lepton = W lepton.
- Remove the 3 leptons, cluster the rest exclusively into 2 jets (Durham / ee_genkt exclusive; also test N=2 with larger-R inclusive per 2604.16218).
- Missing four-momentum p_miss = (√s, 0⃗) − Σ(all reconstructed particles).
- Run the FCCAnalyses jet-flavour tagger on both jets; store all class scores and jet charge (momentum-weighted, κ = 0.3, 0.5, 1).
- Background samples: ZZ, WW, ZH(other decays incl. ZZ*, ττ), S4.
- Optionally a BDT on kinematic variables only (no decay angles, to avoid sculpting ρ). Check explicitly that selection efficiency vs (θ±, φ±) is reported.

### 6.2 Reconstruction
- ν = p_miss (baseline). Variant: kinematic fit with m_ν = 0, m_H constraint, and one unmeasured ISR photon along the beam. Compare resolutions of θ±, φ± for both.
- H frame from recoil vs from visible+ν: compare.
- W charges from the lepton charge.
- d-type assignment on the hadronic W: for W→cs, s-jet from tagger scores; for W→ud, there is no kinematic discriminant in the W rest frame (equal-energy back-to-back quarks), so use flavour scores + jet charge only. Define a per-event d-type probability and measure the mistag rate w on truth-matched MC, binned in jet energy and in whether the hadronic W is on- or off-shell.
- Categories: hadronic W on-shell vs off-shell; W→cs-tagged vs untagged.

### 6.3 Tomography and calibration
1. Truth-level ρ after selection (acceptance effects only).
2. Reco-level moments. Build the linear response R: reco moments = R · (true coefficients) + b, using S2 reweighted to basis elements (Section 3.7). Restrict to the SM/CP-allowed subset for inversion; keep the full 80 for diagnostics.
3. Invert (regularised if needed; report condition number). Closure: unfold the S1 reco sample and the reweighted-SM S2 sample, compare to truth.
4. Background: subtract (template-based) or include as a component with its own ρ; ZZ* and continuum 6f treated explicitly. Report impact of each choice.
5. Null calibration: run the full chain on S2 (𝟙/9) and on decohered-SM pseudo-data; the observed I₃, 𝒞₂ distributions define the bias and the p-values.
6. Significance: ≥ 10³ pseudo-experiments at 10.8 ab⁻¹ (bootstrap of MC with Poisson weights), for I₃ > 2, 𝒞₂ > 0, and the h₄₄/h₅₅ witness. Quote median expected significance and its spread.

**GATE 2** report: selection cutflow (signal and backgrounds), resolution plots, mistag table, response matrix, closure, null distributions, expected significances. Wait.

---

## 7. Phase 3: Channel B (H→ℓνqq, Z→qq)

Same as Phase 2 with: exclusive 4-jet clustering after removing the lepton; Z/W jet pairing (χ² on m_Z, m_H, recoil; also test a pairing BDT/GNN); ν from p_miss (insensitive to Z resolution); additional backgrounds (WW→ℓνqq, ZZ, qq, ττ). Report pairing efficiency and the resulting dilution separately from d-type mistag.

**GATE 3.**

---

## 8. Phase 4: Channel C (H→qqqq, Z→νν)

- Missing mass ≈ m_Z selection; exclusive 4-jet clustering; W⁺/W* pairing (start from the published FCC-ee fully hadronic H→WW/ZZ pairing, Eysermans et al. 2610.04397; contact the authors for code rather than reimplementing).
- Stage 1: flavour-blind analysis, rank-2 observables only (h₄₄, h₅₅ and other rank-2 terms; cos 2Δφ), as an entanglement witness.
- Stage 2: add d-type and W-charge identification (s-tagging, kaon charge, jet charge) to recover rank-1 terms; measure w and charge mistag on MC.
- Backgrounds: ZZ, WW→4q with ISR, ZH(other), qq.

**GATE 4.**

---

## 9. Phase 5: Channel D (H→ℓνℓν, Z→ℓℓ / qq)

- Two neutrinos: p_miss gives the νν̄ four-vector; impose m_ν = 0 and one on-shell W mass → one-parameter family (two assignments of which W is off-shell). Compare: (i) analytic scan with likelihood weighting, (ii) regression NN, (iii) diffusion-style unfolding as in 2605.19754.
- Same calibration and null procedure as Phase 2.

**GATE 5.**

---

## 10. Phase 6: combination and theory systematics

- Combine categories (stat. covariance from shared pseudo-experiments).
- Theory: compare LO vs NLO EW angular coefficients (2506.19951; Prophecy4f if available) and the subtraction approach of 2603.11288. Treat non-resonant/interference residuals (not reweightable) as a systematic.
- Detector: lepton/jet angular resolution ±X%, flavour-tag efficiency/mistag variations, p_miss scale, beam-energy spread.
- Optional: anomalous HWW / CP-odd admixture sensitivity via reweighting.

**GATE 6:** draft results note (figures + tables), not a paper.

---

## 11. Gate report template

```
# Gate N report — <date>
## Done
## Key numbers (with uncertainties, sample versions)
## Figures (paths)
## Deviations from PLAN.md and why
## Problems / open questions for Ang
## Proposed next step
```

## 12. References

- Barr, PLB 825 (2022) 136866 [2106.01377]
- Fabbrichesi, Floreanini, Gabrielli, Marzola, EPJC 83 (2023) 823 [2302.00683]
- Aguilar-Saavedra, PRD 107 (2023) 076016 [2209.14033]; tripartite [2403.13942]; beyond LO [2603.11288]
- Fabbri, Howarth, Maurin, EPJC 84 (2024) 20 [2307.13783]
- Grossi, Pelliccioli, Vicini, JHEP12(2024)120 [2409.16731]
- Gonçalves, Kaladharan, Navarro, JHEP11(2025)158 [2506.19951]; semileptonic higher orders [2604.16218]
- Hypothesis tests for H→WW* entanglement at the LHC [2605.19754]
- Wu et al., CEPC H→ZZ* [2410.17025]
- Eysermans et al., FCC-ee fully hadronic H→WW/ZZ [2610.04397]
- Abel, Dreiner, Sengupta, Ubaldi, JHEP08(2026)067 [2507.15949]