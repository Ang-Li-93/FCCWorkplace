# m(bb) cross-check: Whizard ME decay vs Pythia6 resonance decay

**Process:** `ee → μμH`, √s = 240 GeV, winter2023 IDEA fast-sim.
**Framework:** FCCAnalyses histmaker — one RDataFrame pass per sample produces every
observable (truth + detector together) from the edm4hep files.

| Label | Card | How H→bb is done |
|-------|------|------------------|
| Pythia6 resonance decay | `wzp6_ee_mumuH_Hbb_ecm240` | on-shell `H` from Whizard, **Pythia6** decays it |
| Whizard ME decay | `wzp6_ee_mumuH_Hbb_MEdecay_ecm240` | H→bb in the **Whizard matrix element** (`5+6~H`) |

## Motivation

The reconstructed b b̄ dijet mass peaks at **~126 GeV** for the Whizard-ME-decay sample
but **~125 GeV** for the Pythia6-resonance-decay sample. This study localizes the shift
and identifies its cause, on both the **b-jet side** and the **muon (Z) side**.

## Observables and levels

Three levels are compared:
- **parton** — the hard b/b̄ and μ⁻/μ⁺ from the matrix element (pre-shower).
- **particle** — stable particles (`generatorStatus==1`) after parton shower + hadronization.
- **detector** — Delphes IDEA: Durham exclusive n=2 jets, reconstructed muons.

**b-jet side:** `m_parton` (hard b b̄), `m_vis` (particle, no ν), `m_full` (particle, +ν),
`m_bdesc` (mass of the stable descendants of the hard b/b̄ — the cause check),
`m_dijet` (Durham n=2), `m_dijet_met` (dijet + missing 4-momentum).

**muon (Z) side:** `mll_parton` / `mll_gen` / `mll_reco` (dimuon mass at the three levels),
`recoil_parton` / `recoil_gen` / `m_recoil` (μμ recoil mass at the three levels).

## Results (peak / mean, GeV)

| observable | Pythia6 resonance decay | Whizard ME decay |
|------------|-------------------------|------------------|
| **b-jet side** | | |
| m_parton (hard b b̄)        | 125.0 / 125.0 | 125.0 / 125.0 |
| m_vis (particle, no ν)      | 125.0 / 120.1 | 126.0 / 122.8 |
| m_full (particle, +ν)       | 125.0 / 124.5 | 126.0 / **127.6** |
| m_bdesc (b/b̄ descendants)   | 125.0 / 125.0 | 125.5 / **128.4** |
| m_dijet (Durham n=2)        | 125.0 / 119.5 | 126.0 / 122.6 |
| m_dijet_met (dijet + MET)   | 125.0 / 126.8 | 126.0 / 129.9 |
| **muon (Z) side** | | |
| mll_parton (hard μμ)        | 91.2 / 90.5 | 91.2 / 90.5 |
| mll_gen (particle μμ)       | 91.2 / 89.4 | 89.8 / **87.0** |
| mll_reco (detector μμ)      | 91.2 / 89.4 | 89.8 / **87.0** |
| recoil_parton (hard)        | 125.0 / 126.7 | 125.0 / 126.7 |
| recoil_gen (particle)       | 125.0 / 127.6 | 126.0 / **130.8** |
| m_recoil (detector)         | 125.0 / 127.6 | 126.0 / **130.8** |

## Conclusion

1. **At parton level the two samples are identical** — m(bb)=125.0, m(μμ)=90.5,
   recoil=126.7 in both. The hard matrix element produces the same b b̄ and muons.

2. **The difference is introduced by the Pythia6 parton shower**, proven by `m_bdesc`:
   the stable descendants of the hard b/b̄ have mass **125.0 (stock)** vs **128.4 (ME)**.
   - Stock: H→bb is a **colour-singlet resonance decay**, showered in the Higgs rest
     frame with the resonance 4-momentum conserved → descendants always sum to 125.
   - ME: the Higgs is an internal propagator (no `H` in the record), so the b/b̄ are
     showered as ordinary partons with **global recoil** against the whole event →
     the bb system is unconstrained and its mass inflates.

3. **The muon side sees the same effect** — and it is *not* jet-related. The recoil mass
   uses only the muons and √s, yet it also shifts (125→126). By 4-momentum conservation
   the recoil mass *equals* the mass of everything-except-the-muons = the bb-system mass.
   The shower's global recoil transfers momentum off the muons (mll drops 89.4→87.0,
   E_μμ falls) and into the bb system, so the muons report the same inflated mass.
   The muon pair is identical at parton level and only splits at particle level —
   confirming the shower, not the detector or the jet algorithm, is responsible.

4. **MET does not remove it** (`m_dijet_met`, `m_full`): adding the neutrinos pulls the
   peak back toward 125 but the ME value stays ~1 GeV high, because the excess is real
   recoil momentum, not lost neutrinos.

**Which is "real world":** the hard ME is more correct in the Whizard-ME sample
(off-shell + interference); the reconstructed mass peak is faithful in the Pythia6
resonance-decay sample. The ~1 GeV inflation is a parton-shower artifact of generating
H→bb at matrix-element level without an explicit resonance for Pythia to decay.

## Implementation notes

- Standard FCCAnalyses helpers used throughout: `ExclusiveJetClusteringHelper` (Durham
  n=2), `JetConstituentsUtils::compute_tlv_jets` + `InvariantMass`, `resonanceBuilder` /
  `recoilBuilder`, `MCParticle::get_tlv` / `sel_pdgID` / `sel_genStatus`.
- MET: the Delphes `MissingET` collection is unusable here (absent in the ME-level reco,
  RDF-unreadable `covMatrix` leaf in the stock reco), so the missing 4-momentum is built
  from the visible `ReconstructedParticles` (p_miss = √s − Σ visible) and added to the
  dijet by plain TLorentzVector addition.
- The two samples were reconstructed with different stacks (podio 0.16.2 vs 0.99), so the
  histmaker auto-detects the relation naming (`Particle#1`/`Muon#0` vs
  `_Particle_daughters`/`Muon_objIdx`).

## Plots

b-jet side: `m_parton`, `m_vis`, `m_full`, `m_bdesc`, `m_dijet`, `m_dijet_met`
muon side: `mll_parton`, `mll_gen`, `mll_reco`, `recoil_parton`, `recoil_gen`, `m_recoil`
(each as .pdf for slides and .png for web)
