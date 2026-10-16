# gen/ — dedicated generation (PLAN.md Sec. 5.3)

Status (2026-10-15): **proposal for GATE 1, nothing submitted.** The central winter2023 signal
passed the truth validation (outcome A), so S1 is not needed to replace it; Phase 2 needs
S2 `iso_decay` (reweighting base and the 𝟙/9 null), optionally S3 `diag_decay`, and S4 `bkg_6f`.

| File | Purpose |
|---|---|
| `make_cards.py` | writes every card in `config/generation/` from the official winter2023 FCC-config cards (production process, beams, beam-energy spread, ISR, ISR handler, keep-beams/remnants and the PYTHIA6 PYGIVE string are copied verbatim and checked) |
| `randomise_w_decays.py` | re-draws the W decay directions in the partonic LHEF (`copy` = S1, `iso` = S2, `diag` = S3); numpy only, runs in the plain Key4hep job environment |
| `run_hwwqe_job.sh` | one S1/S2/S3 job: WHIZARD pass 1 → randomiser → Pythia8 + Delphes IDEA (EDM4hep) |
| `submit_hwwqe.sh` | writes (does not submit) the SDCC HTCondor description for N such jobs |

## Software

- Generation: WHIZARD **3.1.5** (Key4hep 2026-04-08 = EventProducer `defaultstack`,
  `/cvmfs/sw.hsf.org/key4hep/setup.sh`). The central winter2023 samples were made with
  WHIZARD 3.0.3 + its PYTHIA6 interface. Manual: `share/doc/manual.tex` of whizard-3.1.5
  (no docs are installed on cvmfs; same chapter structure as the online 3.2 manual,
  https://whizard.hepforge.org/manual/). Section numbers below refer to it.
- Reconstruction: Key4hep 2024-03-10 (EventProducer `prodTag['winter2023']`), Pythia 8.310,
  `DelphesPythia8_EDM4HEP` with `card_IDEA.tcl` / `edm4hep_IDEA.tcl` from FCC-config winter2023.

## S2 (and S1, S3): route (b), decay-angle randomisation before the shower

**Route (a), WHIZARD's switches, cannot work for H → WW\*.** `?isotropic_decay` and
`?diagonal_decay` (manual 5.8.2.2) act on factorised decays declared with `unstable`
(5.8.2), and "a natural restriction of the factorized approach is the implied narrow-width
approximation ... all involved matrix elements must be evaluated on-shell" (5.8.2); "the
invariant ... masses will be always exactly equal to the Z mass. There is no Breit-Wigner
shape involved" (10.6.3). An H → W⁺W⁻ chain with both W on shell is closed at m_H = 125 GeV;
WHIZARD 3.1.5 stops with `ERROR: Mass sum of outgoing particles is more than available
energy` / `FATAL ERROR: Phase-space: generation failed` (tested). Declaring the *H* unstable
with an isotropic decay changes nothing: a spin-0 decay is already isotropic, and the
H → 4f matrix element keeps the W⁺W⁻\* correlations. The isotropic/diagonal options are
also defined relative to an on-shell particle's rest frame and helicity, i.e. for a resonance
in the narrow-width limit, not for an off-shell W\*.

**Route (b) is exact for an off-shell W\*.** For H → W⁺W⁻\* → 4f the conditional decay-angle
density given the W four-momenta is (3/4π)² Tr[ρ(ϰ) Π₊⊗Π₋] (CONVENTIONS.md §2, 5), so
drawing each W's decay direction uniformly in its rest frame, at fixed W four-momenta and
fixed |p\*|, gives ρ = 𝟙/9 exactly and leaves the joint W-momentum distribution (the m_W\*
spectrum, the H and Z kinematics, ISR photons) untouched; reweighting with
w = 9 Tr[ρ_SM(ϰ) Π₊⊗Π₋] restores the SM sample. Isotropy is frame independent (a Wigner
rotation maps the uniform distribution onto itself). `--mode diag` draws the helicity pair
(+−, 00, −+) with probabilities (1, ϰ², 1)/(2+ϰ²) and each analyser from |d¹_{m,±1}(θ)|²
about k̂ (W frames reached from the W⁺W⁻ rest frame by pure boosts, as in `qtomo.frames`):
the decohered SM state, generated without weights.

**Chain** (`run_hwwqe_job.sh`):
1. Pass 1, `config/generation/hwwqe_zh_lvqq_<Z>.sin` (Z = mumu, ee, qq, ss, cc, bb): the
   official production process (e⁺e⁻ → ℓℓH / qq̄H, Gaussian beam-energy spread 0.185 % per beam
   ⊗ ISR, ISR handler "recoil", keep beams/remnants) and `unstable H (...)` with sixteen
   H → ℓνqq′ decay processes (ℓ = e, μ; u/c × d/s with CKM, model SM_CKM), i.e. the complete
   1→4 matrix element with off-shell W\* and full spin correlations (5.8.2.2 option 1);
   narrow-width approximation for the H only (Γ_H/m_H = 3×10⁻⁵). Shower off; partonic LHEF.
   WHIZARD's flavour lists need equal masses (`mass values in flavor combination do not
   coincide` with m_s, m_c ≠ 0), so the combinations are spelled out.
2. `randomise_w_decays.py --flatten-higgs --insert-resonances --beams-as-incoming --mode iso`:
   the H line is replaced by the explicit H → W⁺W⁻ → 4f resonance chain (status 2; the shower
   then evolves each W pair from its own virtuality and the record carries H → W⁺W⁻ → 4f with
   p_H = p_W⁺ + p_W⁻ exactly), and the beams (WHIZARD ISTUP = −9) become the incoming
   particles (Pythia 8.310 aborts with `vector::_M_range_check` on the WHIZARD beam lines).
3. `DelphesPythia8_EDM4HEP card_IDEA.tcl edm4hep_IDEA.tcl p8_lhe_hwwqe_ecm240.cmnd`
   (`config/generation/`, derived from the official LHE card `p8_ee_Hww_ecm240.cmd`).

**Why Pythia8 and not WHIZARD's PYTHIA6.** Showering the modified partonic events inside
WHIZARD needs `rescan "<file>" (proc) { $rescan_input_format = "lhef"  ?update_event = true }`
(manual 11.7). In 3.1.5 this fails for every variant tried (stdhep or LHEF output, with or
without resonance history, shower on/off, beams kept or not): `WHIZARD BUG: HEPEVT: event
incomplete` / `HEPEUP: event incomplete`; with `?update_sqme` the events are not even matched
to the process. Without `?update_event` the rescan is only a format conversion (no shower).
So S1, S2 and S3 are all produced through the same Pythia8 chain (S1 = `--mode copy`), and
the Pythia8-vs-PYTHIA6 difference is measured as S1 vs central at reco level (Phase 2
systematic). A production-identical PYTHIA6 alternative for S2 would be a user-modified
`$method = "template"` H → 4f matrix element with |M|² depending only on the two pair masses
(manual 9.2) — not tested.

**Normalisation.** Pass 1 prints σ(e⁺e⁻ → ZH) (identical to the central sample: 6.764 fb for
μμH, 53.35 fb for (uū+dd̄)H) and the sixteen partial widths; WHIZARD distributes the decays by
their branching ratios. Normalise a sample to σ_central(ZH, H→WW) × f_ℓνqq with
f_ℓνqq = 0.29163 ± 0.00020 (ℓ = e, μ, central truth record, 5.3 M events).

**Validation (local tests, 2026-10-15; numbers in the GATE 1 notes).** Generator level
(4000 events each, qtomo, H frame = W⁺W⁻ rest frame): S1 vs analytic SM, S2 vs 𝟙/9 and
S3 vs decohered SM all χ²/80 with p > 0.5; W masses unchanged to 10⁻⁸ GeV; S2 reweighted to
the SM agrees with S1. After Pythia8 + Delphes + `stage1/truth_hww.py` (adapted to the 2024
podio branch names, see below): S2 p = 0.84 (channel A), 0.72 (channel B); S1 p = 0.72.

**Known differences w.r.t. the central sample.** (i) M\* = min(m_W) extends below 12 GeV
(6 % of events); PYTHIA6 generated W masses only in [12.0, 111.8] GeV. (ii) m_W = 80.419,
Γ_W = 2.049 GeV (WHIZARD SM) vs 80.45, 2.071 GeV (PYTHIA6 defaults). (iii) Pythia8 vs PYTHIA6
shower and hadronisation. (iv) EDM4hep written by the 2024-03-10 stack names the MC relations
`_Particle_parents` / `_Particle_daughters`; the winter2023 files use `Particle#0` /
`Particle#1`: `stage1/truth_hww.py` needs the alias switched (or a check for either name).

## S4 `bkg_6f`: complete 2 → 6 matrix elements with WHIZARD + PYTHIA6

`config/generation/hwwqe_bkg6f_<A|B>_<nonH|full>_<Z>_<ℓ>.sin`: e⁺e⁻ → (Z-pair fermions) +
ℓνqq′, non-Higgs (`$restrictions = "!H"`, manual 5.4.3.2) and full; channel B electroweak
only (`!gl`; Z → bb̄ given as the example without identical quarks). Beams and the PYTHIA6
PYGIVE string verbatim from production, `?resonance_history` as in the official winter2023
top-pair cards (10.6.4), fiducial generator cuts (`all M > 4 GeV`, `any 70 < M < 110 GeV` on
the Z-flavour pairs, and |cos θ_e| < 0.99875 when electrons can come from t-channel photons,
as in the official munumuqq cards), stdhep output: a standard EventProducer `--STDHEP` job.

Cost: ≈ 850 phase-space channels per component (416 diagrams for μμ + μνud, 1248 for
ee + eνud); the test integration (5×50k + 2×100k calls per component, 22 min with 2 threads
for two components) reached only 0.04 % unweighting efficiency. Integrate once with many
more calls and reuse the grids in all jobs: WHIZARD discards grids whose seed differs
("VAMP: parameter mismatch"), but a fixed integration seed with the job seed restored before
`simulate` reuses them (tested):

    int job_seed = seed      ! seed prepended by the job
    seed = 20261015          ! fixed: the .vg grids copied into the job directory match
    integrate (proc) { ... }
    seed = job_seed
    simulate (proc)

The `.vg` files can be copied into the job directory with `exec ("cp <grid dir>/proc.m*.vg .")`
(manual A.1) before `integrate`.

## Seeds

WHIZARD 3.1.5 reduces the seed to 16 bits (`src/rng/dispatch_rng_sub.f90`:
`s = int (mod (seed, 32768), i16)`; a job with seed 424242 logs "Setting seed ... to 31026")
and uses seed, seed+1, ... for its successive integrations and the simulation. EventProducer's
9-digit random job ids therefore give only 32768 distinct streams (two jobs of the same card
collide with probability ≈ N²/65536 for N jobs). `submit_hwwqe.sh` assigns seeds
first_seed + 50 i below 32768; give each card its own range. The same seed range for S1, S2
and S3 of one card gives event-by-event paired samples (identical W four-momenta), useful for
the reweighting closure; disjoint ranges give independent samples.

## Deployment after approval

1. `python3 gen/make_cards.py` (already run; cards in `config/generation/`).
2. Grid/integration check of each pass-1 card: one local job, `gen/run_hwwqe_job.sh <card> iso 1000 <seed> <dir>`.
3. `gen/submit_hwwqe.sh <card> <copy|iso|diag> <n_jobs> <events_per_job> <out_dir>` and
   `condor_submit -name spoolsub02.sdcc.bnl.gov <out_dir>/condor/hwwqe.sub`.
4. S4: register the process names in `EventProducer/config/param_FCCee.py` and copy the cards
   to `FCC-config/winter2023/FCCee/Generator/Whizard/v3.0.3/` (EventProducer reads
   `<whizardcards_dir>/v3.0.3/<process>.sin`), then the usual `--STDHEP` and `--reco` steps
   (documents/WINTER2023_FASTSIM.md).

## Tests 2026-10-16 (PLAN rule 7, channel A, fixed Pythia8 settings)
`outputs/phase1/gen_tests_20261016/run_tests.sh` (git-ignored outputs): 1000 events each of
`hwwqe_zh_lvqq_{mumu,ee}.sin` × `{copy,iso,diag}` (seeds 101 and 202, one WHIZARD stream per card),
then `stage1/truth_hww.py` (winter2023 env) and
`python gen/validate_truth.py --toys 500 --seed 7 --paired mumu_copy,mumu_iso,mumu_diag --reweight mumu_iso,mumu_copy LABEL:TARGET:truth.root:events.root ...`.

| Sample | Target | χ²/80 | p (pseudo-experiments) | χ²/18 rotation-invariant (p) |
|---|---|---|---|---|
| mumu copy (S1) | SM | 96.8 | 0.35 | 13.5 (0.76) |
| mumu iso (S2) | 𝟙/9 | 73.4 | 0.87 | 15.4 (0.63) |
| mumu diag (S3) | decohered SM | 73.8 | 0.89 | 10.9 (0.93) |
| ee copy (S1) | SM | 83.0 | 0.67 | 11.7 (0.86) |
| ee iso (S2) | 𝟙/9 | 77.4 | 0.77 | 10.9 (0.92) |
| ee diag (S3) | decohered SM | 93.6 | 0.38 | 22.5 (0.23) |

- S2 null: I₃ at fixed SM settings −0.03 ± 0.40 (μμ), 0.25 ± 0.34 (ee); expected 0.
- S2 reweighted to the SM vs S1 (μμ): χ²/80 = 68.0 (p = 0.83); weights ≤ 3.26, n_eff 573/1000.
- Paired modes: W four-momenta identical event by event (max difference 0).
- Record: in all 6000 events W = analyser + partner, m(W⁺+W⁻) = m_H, no W copies, no photons from W
  (TimeShower:QEDshowerByOther = off; the default 'on' made a W radiate in 12 % of events).
- M* < 12 GeV present: 5.8 ± 0.7 % (μμ), 6.5 ± 0.8 % (ee); lowest M* 1.5 / 0.55 GeV.
- Timing per 1000-event job: WHIZARD 163–179 s (fixed setup), randomiser 1–3 s, Pythia8 + Delphes
  23–26 s; 8.3–8.5 MB per 1000 events.
