# HWWQE conventions

Every convention used by `qtomo/` is fixed here and pinned down by a unit test
(PLAN.md rule 2). Section numbers refer to PLAN.md; "the paper" is
Fabbrichesi, Floreanini, Gabrielli, Marzola, EPJC 83 (2023) 823 [2302.00683], v3.

## 1. Spin basis and coefficients (Sec. 3.1) — `qtomo/basis.py`

- Single-W states ordered (+1, 0, −1). Two-W states |m₊ m₋⟩, first factor = W⁺,
  second = W⁻; flat index 3·i(m₊) + i(m₋) with i(+1)=0, i(0)=1, i(−1)=2
  (so |+−⟩, |00⟩, |−+⟩ are indices 2, 4, 6).
- Tᵃ: standard Gell-Mann matrices (paper Eq. A.4), Tr[TᵃTᵇ] = 2δᵃᵇ; `GELL_MANN[a-1]`.
- ρ = 𝟙/9 + Σ fₐ Tᵃ⊗𝟙 + Σ gₐ 𝟙⊗Tᵃ + Σ hₐᵦ Tᵃ⊗Tᵇ,
  fₐ = Tr[ρ Tᵃ⊗𝟙]/6, gₐ = Tr[ρ 𝟙⊗Tᵃ]/6, hₐᵦ = Tr[ρ Tᵃ⊗Tᵇ]/4 (paper Eqs. 2.37–2.38).
- Coefficient vector (80): [f₁..f₈, g₁..g₈, h₁₁, h₁₂, …, h₈₈] (`basis.pack`, `basis.COEFF_LABELS`).
- Spin matrices: S_x = (T¹+T⁶)/√2, S_y = (T²+T⁷)/√2, S_z = T³/2 + (√3/2)T⁸ (paper Eq. A.2).

## 2. Decay analysers (Sec. 3.3) — `qtomo/basis.py`

- Analysers: W⁺ → ℓ⁺ or the down-type **antiquark** (W⁺ → u d̄); W⁻ → ℓ⁻ or the
  down-type **quark**. A W⁺ analyser emitted along n̂ (in the W⁺ rest frame) projects
  the W⁺ spin on |+1_n̂⟩; a W⁻ analyser on |−1_n̂⟩, with
  |m_n̂⟩ = exp(−iφS_z) exp(−iθS_y)|m⟩. The decay distribution is
  (1/σ) dσ/dΩ₊dΩ₋ = (3/4π)² Tr[ρ (Π₊⊗Π₋)], Π₊ = |+1_n̂₊⟩⟨+1_n̂₊|, Π₋ = |−1_n̂₋⟩⟨−1_n̂₋|.
- `q_functions` and `p_functions` are paper Eqs. (B.1) and (B.2) **verbatim**; PLAN.md
  Sec. 3.3 transcribes them correctly. They satisfy qᵃ = Tr[Π Tᵃ].

**Normalisation fixes (the plan's tests failed as written; the cause is in the paper).**
PLAN.md Sec. 3.3 copies three relations from the paper's Sec. 2.4 that are not
consistent with the Appendix B functions:

| Relation | PLAN.md / paper | Correct (used here) | Evidence |
|---|---|---|---|
| projector | Π = 𝟙/3 + Σ qᵃTᵃ (Eq. 2.43) | Π = 𝟙/3 + **½** Σ qᵃTᵃ | literal form has eigenvalues (5/3, −1/3, −1/3); with ½ it is the rank-1 projector \|±1_n̂⟩⟨±1_n̂\|. Also the paper's own Eq. (2.24): v^a = ½Tr[ρTᵃ] |
| duality | (3/4π)∫pⁿqᵐdΩ = δⁿᵐ (Eq. 2.45) | (3/4π)∫pⁿqᵐdΩ = **2**δⁿᵐ | follows from the paper's Eqs. (2.44) + (2.46), whose m uses 3/8π; verified by quadrature |
| estimators | fₐ = ⟨p₊ᵃ⟩, hₐᵦ = ⟨p₊ᵃp₋ᵇ⟩ (Eqs. 2.47–2.48) | fₐ = ⟨p₊ᵃ⟩/**6**, gₐ = ⟨p₋ᵃ⟩/**6**, hₐᵦ = ⟨p₊ᵃp₋ᵇ⟩/**4** | ⟨p₊ᵃ⟩ = Tr[ρTᵃ⊗𝟙], ⟨p₊ᵃp₋ᵇ⟩ = Tr[ρTᵃ⊗Tᵇ]; exact by quadrature for random ρ |

No choice of a single rescaling of p can make both of the plan's estimators true
with the ρ normalisation of Sec. 3.1, so the fix is in the estimators, not in the
functions. Tests: `test_plan_literal_projector_is_not_a_projector`,
`test_pq_duality`, `test_moment_estimators_exact`, `test_q_is_trace_of_coherent_state_projector`.

## 3. Rank-1 / rank-2 polarisation and analyser flips — `qtomo/basis.py`

- The 8 Gell-Mann components split into vector (rank-1: S_x, S_y, S_z directions,
  projector `RANK1`) and tensor (rank-2, `RANK2`) polarisation.
- Flipping the analyser, n̂ → −n̂ (θ → π−θ, φ → φ+π), acts as q → `FLIP` q and
  p → `FLIP` p with `FLIP = RANK2 − RANK1`; also q₊(−n̂) = q₋(n̂).
- d/u confusion on a hadronic W (back-to-back quarks in the W rest frame) with
  probability w gives E[p(n̂_obs)] = D(w) p(n̂), D(w) = RANK2 + (1−2w) RANK1
  (`mistag_dilution`). The per-event corrected functions p̃ = `mistag_correction(w)` p
  are unbiased for any w ≠ ½ (variance grows as 1/(1−2w)²). Rank-(2,2) coefficients,
  e.g. h₄₄, h₅₅, are unaffected by mistag on either leg.

## 4. Frames (Sec. 3.2) — `qtomo/frames.py`

- Four-vectors are arrays (…, 4) ordered (E, p_x, p_y, p_z), in GeV.
- Higgs rest frame: truth H four-momentum, or the reco recoil / visible system
  (chosen by the channel driver and passed in).
- k̂ = W⁺ direction in the H frame; p̂ = e⁺ beam direction boosted into the H frame;
  cosΘ = p̂·k̂; r̂ = (p̂ − cosΘ k̂)/sinΘ; n̂ = r̂ × k̂ = (p̂ × k̂)/sinΘ (paper Eq. 2.26).
  {n̂, r̂, k̂} is right-handed and is used for **both** W bosons (x = n̂, y = r̂, z = k̂).
- Decay angles: boost the analyser from the H frame into its W rest frame (pure boost
  along that W's H-frame momentum, not lab → W), then θ = polar angle w.r.t. k̂ and
  φ = atan2(â·r̂, â·n̂) ∈ [0, 2π), for both the W⁺ and the W⁻ analyser.
- Off-shell labelling: M = max(m_W⁺, m_W⁻), f = min/max; both masses and the flag of
  which W is the lighter one are stored.
- The e⁺ beam four-vector is an input (taken from the generator record or config); its
  direction and any crossing angle in the IDEA samples are to be read off the MC in Phase 1.

## 5. Analytic SM state (Sec. 3.4) — `qtomo/sm.py`

- ϰ = (m_H² − M₁² − M₂²)/(2M₁M₂) ≥ 1; |Ψ_H⟩ = (|+−⟩ − ϰ|00⟩ + |−+⟩)/√(2+ϰ²).
- The paper's closed forms Eqs. (3.5)–(3.6) agree with |Ψ_H⟩ **coefficient by
  coefficient** (all 80; no local unitary needed): non-zero entries are
  f₃ = g₃ = (1−ϰ²)/(6d), f₈ = g₈ = −f₃/√3, h₁₆ = h₆₁ = h₂₇ = h₇₂ = −ϰ/(2d),
  h₃₃ = ϰ²/(4d), h₃₈ = h₈₃ = −1/(4√3), h₄₄ = h₅₅ = 1/(2d), h₈₈ = (ϰ²−4)/(12d), d = 2+ϰ².
- With m_H = 125.0 GeV and M_W = 80.4 GeV the paper's figure labels are reproduced
  (entanglement entropy, 𝒞₂, I₃ at several M_W*).
- Decohered SM: diagonal part of ρ in the |m₊m₋⟩ basis (separable).
- W* mass spectrum (`OffShellSpectrum`): d²Γ/dM₁dM₂ ∝ 4M₁M₂ λ^½ [λ + 12M₁²M₂²] / (BW₁ BW₂),
  λ = λ(m_H², M₁², M₂²), constant-width Breit–Wigner; λ + 12M₁²M₂² = 4M₁²M₂²(2+ϰ²) is the
  helicity sum of the same amplitude. Used only before MC is available.

## 6. Observables (Sec. 3.5) — `qtomo/bell.py`

- 𝒞₂ = 2 max(0, Tr ρ² − Tr ρ_A², Tr ρ² − Tr ρ_B²); in coefficients this is the paper's Eq. (2.39).
- B = T⁴⊗T⁴ + T⁵⊗T⁵ − (1/√3)[T¹⊗T¹ + T¹⊗T⁶ + T⁶⊗T¹ + T⁶⊗T⁶ + T²⊗T² + T²⊗T⁷ + T⁷⊗T² + T⁷⊗T⁷];
  Tr[ρB] = 4(h₄₄+h₅₅) − (4/√3)(h₁₁+h₁₆+h₆₁+h₆₆+h₂₂+h₂₇+h₇₂+h₇₇) = paper Eq. (2.40).
  Largest eigenvalue of B = 1 + √(11/3) = 2.9149.
- I₃ = max_{U,V∈U(3)} Tr[ρ (U⊗V)† B (U⊗V)].
- Reconstructed ρ: results are quoted both raw and after projection onto the nearest
  physical state (Frobenius norm; Smolin–Gambetta–Smith, `basis.nearest_physical`).

## 7. Coefficient subspaces — `basis.subspace`

- `rotation_invariant` (18 dims): ρ commutes with J_k = S_z⊗𝟙 + 𝟙⊗S_z (any spin-0
  parent, CP-odd admixtures, mixtures over kinematics, and 𝟙/9 at the origin).
- `rotation_invariant_real` (13 dims): additionally real in the |m₊m₋⟩ basis
  (contains the tree-level SM). Candidate "SM/CP-allowed subsets" for the
  inversion of Sec. 6.3; the choice is made in Phase 2.
