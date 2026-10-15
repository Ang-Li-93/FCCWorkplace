# Gate 0 report — 2026-10-15

Phase 0 (machinery, no MC) of [PLAN.md](../PLAN.md). Code on branch `hwwqe`, commits
801885b…ee84d3a. Toy results: qtomo pseudo-experiments, seed 20261015 (`config/phase0.yaml`),
Key4hep 2026-04-08. Constants: PDG 2024 (m_H = 125.20, m_W = 80.3692, Γ_W = 2.085 GeV).
Statistical uncertainties of pseudo-experiment results are quoted as ±; asymptotic values
are exact for the stated model.

## Done

1. **Section 3 implemented in `qtomo/`, 197 pytest tests pass** (100 s; per file: basis 30,
   sm 17, frames 36, toy 13, tomography 27, bell 26, reweight 22, response 13, stats 13).
   Conventions are collected in [CONVENTIONS.md](../CONVENTIONS.md). Each module group was
   reviewed independently for physics/conventions and for numerics; verified findings were fixed.
2. **Transcription check against 2302.00683 v3.** Eqs. (B.1)/(B.2) in PLAN.md Sec. 3.3 are
   exact, but three normalisation statements copied from the paper's Sec. 2.4 are not
   consistent with them, so the Sec. 3.3 tests failed as written (see Deviations, item 1).
3. **Toy closure** (task 2): 7 states × N = 10⁴, 3·10⁴, 10⁵, 3·10⁵, 10⁶ × 200 pseudo-experiments.
4. **Ideal statistical reach** (task 3): 6 categories × w ∈ {0, 0.1, 0.2, 0.3, 0.5}; exact
   asymptotic σ from the per-event covariance and 1000 pseudo-experiments per point.
5. Side check requested by Ang: the jet flavour tagger works correctly only in the winter2023
   environment (details in [LOG.md](../LOG.md); Problems, item 2).

## Key numbers

### Analytic validation (exact, no statistical uncertainty)

| Check | Result |
|---|---|
| Π± from Eq. (B.1) with the factor ½ vs \|±1_n̂⟩⟨±1_n̂\| built with D(φ,θ,0) | equal to 1e-13; Hermitian, Tr = 1, rank-1 projector |
| (3/4π)∫pⁿqᵐ dΩ (exact quadrature) | 2δⁿᵐ (off-diagonal < 1e-12) |
| ⟨p₊ᵃ⟩, ⟨p₋ᵃ⟩, ⟨p₊ᵃp₋ᵇ⟩ for random ρ (exact quadrature) | 6fₐ, 6gₐ, 4hₐᵦ to 1e-12 |
| Paper Eqs. (3.5)–(3.6) vs coefficients of \|Ψ_H⟩ | agree coefficient by coefficient (all 80) to 1e-13; no local unitary needed |
| First-principles matrix element: \|M\|² ∝ (p_ν·p_ℓ⁻)(p_ν̄·p_ℓ⁺) vs Tr[ρ_SM(Π₊⊗Π₋)] at the `frames.py` angles | constant ratio, relative residual < 1e-11; breaks if the analyser is swapped or the frame is left-handed |
| Generic HVV coupling (incl. ε-tensor term), spinor currents vs polarisation-vector ρ | agree; fixes frame handedness and the phases of \|Ψ_H⟩ |
| λ_max(B) | 2.9149 = 1 + √(11/3) |
| I₃(Σ\|ii⟩/√3) after optimisation | 2.8729 = 4/(6√3 − 9) |
| Product states / 𝟙/9 | I₃ ≤ 1.474 (product maximum), 𝒞₂ = 0 |
| SM I₃ at M_W* = 4, 12, 20, 40 GeV (m_H = 125.0, M_W = 80.4) | 1.673, 2.082, 2.444, 2.885 (paper Fig. 4: 1.67, 2.08, 2.44, 2.89) |
| SM 𝒞₂ at the same masses | 0.039, 0.315, 0.714, 1.316 (paper: 0.039, 0.31, 0.71, 1.3) |

SM state averaged over the tree-level W* mass spectrum (PDG constants): **I₃ = 2.643,
𝒞₂ = 0.952, h₄₄ = 0.0988**. At fixed mass, I₃ > 2 requires M_W* > 10.4 GeV.

### Toy closure (task 2)

All states, all N: the 80 coefficients close — χ²/ndf = 0.985–1.027 (estimated covariance),
pull widths 0.989–1.012, |mean pull| < 0.01. σ ∝ N^α with fitted α between −0.47 and −0.53 for
I₃ (raw and physical), the unbiased 𝒞₂ and h₄₄ in every state; the unbiased 𝒞₂ of 𝟙/9 scales
as N⁻¹ (degenerate U-statistic at c = 0), as expected.

Bias ± stat. uncertainty (σ of one pseudo-experiment in brackets), SM averaged over the spectrum:

| N | I₃ raw | I₃ physical | 𝒞₂ plug-in | 𝒞₂ physical | 𝒞₂ unbiased | h₄₄ |
|---|---|---|---|---|---|---|
| 10⁴ | +0.243 ± 0.007 (0.102) | −0.082 ± 0.004 (0.057) | +0.084 ± 0.007 (0.096) | −0.113 ± 0.005 (0.071) | +0.016 ± 0.007 (0.096) | +0.0020 ± 0.0014 (0.0195) |
| 10⁵ | +0.071 ± 0.002 (0.033) | −0.023 ± 0.002 (0.021) | +0.013 ± 0.002 (0.031) | −0.033 ± 0.002 (0.025) | +0.006 ± 0.002 (0.031) | +0.0008 ± 0.0004 (0.0058) |
| 10⁶ | +0.020 ± 0.001 (0.011) | −0.007 ± 0.000 (0.006) | +0.002 ± 0.001 (0.009) | −0.010 ± 0.001 (0.008) | +0.002 ± 0.001 (0.009) | −0.0001 ± 0.0001 (0.0018) |

Null states at N = 10⁴ → 10⁶: 𝟙/9 gives raw I₃ = 0.571 ± 0.005 → 0.057 ± 0.001 (true 0);
decohered SM (M* = 30 GeV, true I₃ = 1.472) gives +0.264 ± 0.006 → +0.024 ± 0.001. The fixed-M*
SM states behave like the averaged one (tables in `outputs/phase0/closure_summary.json`).

What this shows:
- Every bias goes to zero. The plug-in 𝒞₂ bias falls as 1/N; the unbiased 𝒞₂ is unbiased up to
  a small max-of-two-arguments effect (≤ 0.2σ).
- **The raw I₃ bias falls only as 1/√N, like σ: it stays at about +2σ of a single experiment
  at every N (2.4σ at 10⁴, 1.9σ at 10⁶).** It comes from maximising over U, V on a noisy, unphysical ρ̂ (100 % of the SM
  reconstructions have a negative eigenvalue at all N). The physical projection reverses the
  sign (about −0.8σ). Hence the null calibration of PLAN Sec. 6.3 item 5 is essential, not
  optional; the linear, fixed-setting Tr[ρ̂ B] is unbiased (bias/uncertainty: mean 0.17, largest 2.4 over
  the 35 state × N points).

Figures: [closure_i3](figures/gate0/closure_i3.png), [closure_i3_physical](figures/gate0/closure_i3_physical.png),
[closure_c2](figures/gate0/closure_c2.png), [closure_c2_physical](figures/gate0/closure_c2_physical.png),
[closure_c2_unbiased_arg](figures/gate0/closure_c2_unbiased_arg.png), [closure_h44](figures/gate0/closure_h44.png).

### Ideal statistical reach (task 3)

Perfect analysers, spectrum-averaged SM state, yields of PLAN Sec. 4 (e, μ; to be verified in
Phase 1), fixed (not Poisson-fluctuated) N. σ = exact asymptotic value; in brackets the
pseudo-experiment σ (±2.2 %) of raw I₃ / unbiased 𝒞₂ / h₄₄. "Z" = expected value over σ,
against I₃ = 2 and 𝒞₂ = h₄₄ = 0 — an orientation only (see the I₃ bias above).

| Category | N | σ(I₃) | σ(𝒞₂) | σ(h₄₄) | Z(I₃ > 2) | Z(𝒞₂) | Z(h₄₄) |
|---|---|---|---|---|---|---|---|
| A ℓνqq, Z→ℓℓ | 8 710 | 0.114 (0.114) | 0.108 (0.108) | 0.0203 (0.0197) | 5.7 | 8.9 | 4.9 |
| B ℓνqq, Z→qq | 91 000 | 0.0351 (0.0353) | 0.0328 (0.0323) | 0.0063 (0.0063) | 18.3 | 29.0 | 15.8 |
| C qqqq, Z→νν | 42 000 | 0.0517 (0.0504) | 0.0484 (0.0467) | 0.0092 (0.0089) | 12.4 | 19.7 | 10.7 |
| D ℓνℓν, Z→ℓℓ | 1 407 | 0.282 (0.270) | 0.288 (0.284) | 0.0504 (0.0510) | 2.3 | 3.3 | 2.0 |
| D ℓνℓν, Z→qq | 14 700 | 0.0874 (0.0852) | 0.0823 (0.0799) | 0.0156 (0.0153) | 7.4 | 11.6 | 6.3 |
| qqqq, Z→qq (optional) | 147 000 | 0.0276 (0.0287) | 0.0258 (0.0257) | 0.0049 (0.0049) | 23.3 | 36.9 | 20.0 |

d/u mistag rate w on the hadronic legs (one leg in A, B; both in C), asymptotic σ(I₃) with the
pseudo-experiment value in brackets; σ(h₄₄) is independent of w by construction and in the
pseudo-experiments:

| w | A σ(I₃) | B σ(I₃) | C σ(I₃) | A σ(𝒞₂) | C σ(𝒞₂) |
|---|---|---|---|---|---|
| 0 | 0.114 (0.114) | 0.035 (0.035) | 0.052 (0.050) | 0.108 | 0.048 |
| 0.1 | 0.116 (0.116) | 0.036 (0.035) | 0.054 (0.054) | 0.108 | 0.049 |
| 0.2 | 0.121 (0.114) | 0.038 (0.037) | 0.060 (0.054) | 0.110 | 0.052 |
| 0.3 | 0.135 (0.117) | 0.042 (0.037) | 0.081 (0.066) | 0.114 | 0.066 |
| 0.5 | not measurable | not measurable | not measurable | not measurable | not measurable |

- Mistag costs little with one hadronic leg (σ(I₃) +19 % at w = 0.3, asymptotic; +3 % in the
  pseudo-experiments) and more with two (+57 %; +32 % in the pseudo-experiments).
  At w = ½ all rank-1 information on that leg is lost, so I₃ and 𝒞₂ cannot be reconstructed;
  h₄₄ is unaffected (0.0203 in A at every w). w ≈ 0.3 is realistic for W → ud with the
  winter2023 tagger (Problems, item 2).
- The asymptotic σ(I₃) agrees with the pseudo-experiments for raw I₃; at w ≥ 0.2 it is
  conservative (by up to 26 %), because the optimiser re-chooses settings when rank-1 noise is large.
  The physically projected I₃ has about 0.55× the spread but is biased low by about 1.5 times its own σ.
- A lower cut on M* lowers Z(I₃) in all categories (the gain in entanglement is smaller than
  the loss of events); Z(𝒞₂), Z(h₄₄) are flat up to a 20 GeV cut.

Figures: [reach_sigma_i3](figures/gate0/reach_sigma_i3.png), [reach_sigma_c2](figures/gate0/reach_sigma_c2.png),
[reach_sigma_h44](figures/gate0/reach_sigma_h44.png), [reach_mstar_cut](figures/gate0/reach_mstar_cut.png),
[analytic_sm_vs_mstar](figures/gate0/analytic_sm_vs_mstar.png), [analytic_mass_spectrum](figures/gate0/analytic_mass_spectrum.png).

## Figures (paths)

All in `reports/figures/gate0/` as PDF and PNG: `analytic_sm_vs_mstar`, `analytic_mass_spectrum`,
`closure_{i3,i3_physical,c2,c2_physical,c2_unbiased_arg,h44}`, `reach_sigma_{i3,c2,h44}`, `reach_mstar_cut`.

## Deviations from PLAN.md and why

1. **Normalisations of Sec. 3.3 corrected** (the functions q, p are kept verbatim):
   Π± = 𝟙/3 + **½**Σqᵃ Tᵃ (as written it has eigenvalues 5/3, −1/3, −1/3);
   (3/4π)∫pⁿqᵐ dΩ = **2**δⁿᵐ; estimators fₐ = ⟨p₊ᵃ⟩/**6**, gₐ = ⟨p₋ᵃ⟩/**6**, hₐᵦ = ⟨p₊ᵃp₋ᵇ⟩/**4**.
   The plan copied these from the paper's Eqs. (2.43), (2.45), (2.47)–(2.48); the paper's own
   Eqs. (2.24) and (2.46) agree with the corrected forms, and no single rescaling of p makes
   both of the plan's estimators hold with the Sec. 3.1 normalisation. Tests pin each relation.
2. **Toy plots carry "FCC-ee toy study (no detector simulation)"** instead of the Delphes IDEA
   label of rule 8, which would be untrue for toys; MC plots will use the plan's label.
3. **Extra modules**: `qtomo/sm.py` (analytic state, closed forms, W* spectrum), `config.py`,
   `plotting.py`; and `basis.subspace` for the "SM/CP-allowed subsets" (rotation-invariant,
   18 dims; additionally real, 13 dims) — the choice is left to Phase 2.
4. **Additional estimators reported**: an unbiased (U-statistic) 𝒞₂ next to the raw and
   physical ones, and the linear fixed-setting I₃; both help the null calibration.
5. **Reach model**: the spectrum average uses the tree-level double-Breit–Wigner H → W W*
   spectrum (same amplitude as |Ψ_H⟩); yields are fixed, qqqq assumes known W charges; the
   optional qqqq + Z→qq row is included for information only.
6. **`response.py`**: the reviewed version is kept. Two real findings are deferred to Phase 2:
   one response matrix is biased when the state depends on m_W* (needs an m_W*-binned response),
   and weighting the GLS fit by the observed covariance biases small samples (use the model's
   second moments). An untested rewrite with both fixes is kept in `outputs/drafts/`.
7. **Proposed (needs approval) for Phase 1**: run stage1 in the winter2023 environment instead of
   the current stable release of PLAN Sec. 2 (Problems, item 2); qtomo stays on Key4hep 2026-04-08.

## Problems / open questions for Ang

1. Please confirm the normalisation reading of item 1 (it changes every coefficient by a
   constant factor, so it must be settled before any MC result).
2. **Flavour tagging and the current stack.** The tagger gives correct scores only in the
   winter2023 environment (`setup_hbs.sh`). In the current stack, (a) winter2023 files lose
   track covariances and MC momenta under EDM4hep 1, and (b) a GCC 14 build issue makes the
   unqualified `abs(double)` in FCCAnalyses integer-valued: `get_isMu/El/ChargedHad`,
   `ReconstructedParticle::remove`, `resonanceBuilder` and `HiggsTools::acolinearity` are wrong
   on any file. ZH_XSec and Hbs ran on the winter2023 stack (unaffected); anything run with these
   helpers via `setup.sh`/`setup_xsec.sh` should be rechecked. 7-class tagger on H→WW (1k events):
   s vs u+d AUC ≈ 0.90, d vs u only 0.61–0.63, d-jet correct in 68 % of W → ud (w ≈ 0.3).
3. The raw I₃ is biased by about +2σ at every N, so a "Z(I₃ > 2)" is meaningless without the
   null calibration; for entanglement the relevant separable bound of this operator is 1.474,
   not 2. How should I₃ significances be defined in Phase 2 (Bell test vs entanglement witness)?
4. h₄₄ ≠ 0 is a coherence test against the decohered and isotropic nulls, not by itself an
   entanglement witness (a product state can have h₄₄ ≠ 0). A flavour-blind entanglement witness
   for channel C needs more thought (Phase 4).
5. Phase 1 inputs: the e⁺ beam direction and any crossing angle in the IDEA samples (for p̂),
   and the generator masses/widths, will be read from the MC record. Listing EOS
   `DelphesEvents/` needs a fresh Kerberos ticket.

## Proposed next step

Phase 1 (samples): list the central IDEA production and record names, cross sections, event
counts and generator settings in `config/samples.yaml`; write the truth stage1 in the standard
FCCAnalyses format (winter2023 environment, if approved) for the ZH, H → WW* samples
(`wzp6_ee_{mumu,ee}H_HWW_ecm240` for channel A); truth tomography in bins of m_W* against the
analytic state; then decide between central and dedicated signal samples (GATE 1).
