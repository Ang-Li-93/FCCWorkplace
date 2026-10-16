#!/usr/bin/env python3
"""Write the dedicated-generation WHIZARD cards of PLAN.md Sec. 5.3 into config/generation/.

Every card is derived from the official winter2023 FCC-config card of the same Z decay mode
(FCC-config/winter2023/FCCee/Generator/Whizard/v3.0.3/wzp6_ee_<Z>H_HWW_ecm240.sin): the
production process, aliases, beams (Gaussian beam-energy spread (x) ISR), the ISR photon
handler, the beam/remnant switches and the PYTHIA6 PYGIVE string are copied verbatim and
checked, so ISR, beam-energy spread and shower settings match the central production.
Manual references are to the WHIZARD 3.1.5 manual (share/doc/manual.tex of whizard-3.1.5,
the version in the Key4hep stack used by EventProducer generation jobs).

  pass-1 cards  hwwqe_zh_lvqq_<Z>.sin      S1 'sm_full' / S2 'iso_decay' / S3 'diag_decay'
                (factorised e+e- -> Z H x 'unstable H' with the H -> l nu q q' 1->4 matrix
                element; partonic LHEF; then gen/randomise_w_decays.py and the Pythia8 + Delphes
                step, see gen/README.md)
  S4 cards      hwwqe_bkg6f_<chan>_<part>_<Z>_<lw>.sin   S4 'bkg_6f': complete 2 -> 6 matrix
                elements, non-Higgs ($restrictions = "!H") and full, shower/hadronisation by
                WHIZARD's PYTHIA6 interface with the production PYGIVE string (standard
                EventProducer --STDHEP job: 'whizard card.sin' -> proc.stdhep)

    python3 gen/make_cards.py [--check-only]
"""
import argparse
import re
import sys
from pathlib import Path

HWWQE = Path(__file__).resolve().parents[1]
REPO = HWWQE.parents[1]
OFFICIAL = REPO / "FCC-config/winter2023/FCCee/Generator/Whizard/v3.0.3"
OUTDIR = HWWQE / "config/generation"

# Z decay mode -> official winter2023 card (config/samples.yaml signal samples)
Z_MODES = {"mumu": "wzp6_ee_mumuH_HWW_ecm240", "ee": "wzp6_ee_eeH_HWW_ecm240",
           "qq": "wzp6_ee_qqH_HWW_ecm240", "ss": "wzp6_ee_ssH_HWW_ecm240",
           "cc": "wzp6_ee_ccH_HWW_ecm240", "bb": "wzp6_ee_bbH_HWW_ecm240"}

# W decays: leptons l = e, mu (PLAN Sec. 5.3; tau only if needed later); quarks with CKM
# mixing (model SM_CKM) u/c x d/s.  W -> u bbar / c bbar (|V_ub|^2, |V_cb|^2 < 2e-3) omitted.
# WHIZARD requires equal masses inside a flavour list (FATAL ERROR 'mass values in flavor
# combination do not coincide' with ms, mc /= 0), so every combination is spelled out.
LEPTONS = {"e": ("e1", "E1", "n1", "N1"), "mu": ("e2", "E2", "n2", "N2")}
UP = ("u", "c")
DOWN = ("d", "s")

MANUAL = """\
# WHIZARD 3.1.5 manual sections used (share/doc/manual.tex of whizard-3.1.5):
#   5.4.1 process definition, 5.4.3.2 $restrictions (O'Mega diagram selection),
#   5.5.1 beams, 5.5.6 lepton ISR structure function (isr_alpha, isr_mass), 5.5.9 Gaussian
#   beam-energy spread (gaussian_spread1/2 = sigma per beam), 5.5.14 concatenation
#   'gaussian => isr', 10.4 ISR photon handler ($isr_handler_mode = "recoil"),
#   5.8.2 factorised decays with 'unstable' (narrow-width approximation, on-shell
#   intermediate particle), 5.8.2.2 spin correlations (?isotropic_decay / ?diagonal_decay
#   act on the factorised decay of an on-shell particle in its rest frame), 10.6.3 factorised
#   processes ("invariant masses ... exactly equal to the Z mass"), 10.6.4 resonance insertion
#   (?resonance_history), 11.5 event formats (lhef, stdhep), A.1 exec, A.2 variables.
"""


def official_block(name):
    """Production-relevant lines of an official card, verbatim, checked."""
    text = (OFFICIAL / f"{name}.sin").read_text()
    lines = [l.rstrip() for l in text.splitlines()]
    pick = {}

    def grab(key, pattern):
        hits = [l for l in lines if re.match(pattern, l.strip()) and not l.strip().startswith("#")]
        if not hits:
            raise SystemExit(f"{name}: no line matching {pattern!r}")
        pick[key] = hits
    grab("aliases", r"alias\s")
    grab("process", r"process\s+proc\s*=")
    grab("beams", r"beams\s*=")
    grab("spread", r"gaussian_spread[12]\s*=")
    grab("isr_handler", r"\?isr_handler\s*=")
    grab("isr_mode", r"\$isr_handler_mode\s*=")
    grab("isr_alpha", r"isr_alpha\s*=")
    grab("isr_mass", r"isr_mass\s*=")
    grab("keep_beams", r"\?keep_beams\s*=")
    grab("pygive", r"\$ps_PYTHIA_PYGIVE\s*=")
    grab("integrate", r"integrate\s*\(proc\)")
    grab("keep_remnants", r"\?keep_remnants\s*=")
    # consistency with config/samples.yaml (Gaussian 0.185 % per beam, ISR, MDME(226,1)=1)
    assert any("gaussian => isr" in b for b in pick["beams"]), name
    assert all("0.185%" in s for s in pick["spread"]), name
    assert "MDME(226,1)=1" in pick["pygive"][0], name
    return pick


def h_decays():
    """(name, process line) of H -> l nu q q' (both charge assignments)."""
    out = []
    for lname, (lm, lp, nu, nub) in LEPTONS.items():
        for up in UP:
            for dn in DOWN:
                # W+ -> l+ nu, W- -> d ubar ; W+ -> u dbar, W- -> l- nubar
                out.append((f"h_{lname}p_{dn}{up}b", f"H => {lp}, {nu}, {dn}, {up.upper()}"))
                out.append((f"h_{lname}m_{up}{dn}b", f"H => {lm}, {nub}, {up}, {dn.upper()}"))
    return out


def beam_block(pk, isr_handler=True):
    lines = pk["beams"] + pk["keep_beams"] + pk["keep_remnants"] + pk["spread"]
    lines += ([] if isr_handler else ["# ISR handler applied later"]) + pk["isr_handler"] + pk["isr_mode"]
    lines += pk["isr_alpha"] + pk["isr_mass"]
    return "\n".join(lines)


def pass1_card(zmode):
    name = Z_MODES[zmode]
    pk = official_block(name)
    dec = h_decays()
    names = ", ".join(n for n, _ in dec)
    return f"""\
# HWWQE dedicated generation, pass 1 (PLAN.md Sec. 5.3: S1 'sm_full', S2 'iso_decay',
# S3 'diag_decay'), Z -> {zmode}, H -> W+ W-* -> l nu q q' (l = e, mu), sqrt(s) = 240 GeV.
# Generated by gen/make_cards.py from the official card {name}.sin
# (FCC-config winter2023, WHIZARD v3.0.3 directory): production process, beams, beam-energy
# spread, ISR and ISR handler copied verbatim.
#
# Route (b) of gen/README.md: WHIZARD produces e+e- -> Z H exactly as the central sample
# and decays the H with the complete H -> l nu q q' matrix element (full W+ W-* spin
# correlations and off-shell W*; narrow-width approximation for the H only, manual 5.8.2,
# Gamma_H/m_H = 3e-5).  Output: partonic LHEF 'partonic.lhe' (manual 11.5); parton shower
# OFF here.  Then gen/randomise_w_decays.py (--mode copy: S1, iso: S2, diag: S3) and the
# Pythia8 + Delphes IDEA step (config/generation/p8_lhe_hwwqe_ecm240.cmnd).
# WHIZARD's own ?isotropic_decay / ?diagonal_decay (manual 5.8.2.2) cannot be used: they act
# only on factorised decays of on-shell particles, and H -> W+ W- with both W on shell is
# closed (tested: 'Mass sum of outgoing particles is more than available energy').
#
# n_events and seed are prepended by the job (EventProducer convention).
#
{MANUAL}
model = SM_CKM          # official card: SM; CKM needed for W -> u sbar, c dbar (central: Pythia6 W decays with CKM)
sqrts = 240 GeV

{chr(10).join(pk['aliases'])}

# Production: verbatim from {name}.sin (manual 5.4.1)
{pk['process'][0]}

# H -> l nu q q' decay processes (manual 5.8.2); their integrals are the partial widths
""" + "\n".join(f"process {n} = {p}" for n, p in dec) + f"""
integrate ({names}) {{ iterations = 5:20000:"gw", 3:40000:"" }}

# Beams: verbatim from {name}.sin (manual 5.5.1, 5.5.6, 5.5.9, 5.5.14, 10.4)
{beam_block(pk)}

# No shower here: the W decay directions are re-drawn on the partonic record first
?ps_fsr_active          = false
?ps_isr_active          = false
?hadronization_active   = false

# Factorised H decay with full spin correlations (manual 5.8.2, 5.8.2.2 option 1)
unstable H ({names})

{pk['integrate'][0]}

sample_format = lhef
simulate (proc) {{ $sample = "partonic" }}
"""


def s4_components(zmode, lw):
    """Final-state components (Z pair first, then the W pair of the W lepton and the quark pair)."""
    zf = {"mumu": ("e2", "E2"), "ee": ("e1", "E1"), "uu": ("u", "U"), "dd": ("d", "D"),
          "ss": ("s", "S"), "cc": ("c", "C"), "bb": ("b", "B")}[zmode]
    lm, lp, nu, nub = LEPTONS[lw]
    comps = []
    for up in UP:
        for dn in DOWN:
            comps.append(f"({zf[0]}, {zf[1]}, {lp}, {nu}, {dn}, {up.upper()})")
            comps.append(f"({zf[0]}, {zf[1]}, {lm}, {nub}, {up}, {dn.upper()})")
    return comps


def s4_card(chan, part, zmode, lw):
    ref = Z_MODES["mumu" if zmode in ("mumu",) else "ee" if zmode == "ee" else "qq"]
    pk = official_block(ref)
    comps = s4_components(zmode, lw)
    restr = {"nonH": '{ $restrictions = "!H" }', "full": ""}[part]
    if chan == "B":
        # electroweak continuum only (ZWW / ZZ-type, O(alpha^6)); QCD 6f (WW + g* -> q qbar)
        # is covered by the Pythia8 WW samples with their parton shower
        restr = {"nonH": '{ $restrictions = "!H && !gl" }', "full": '{ $restrictions = "!gl" }'}[part]
    lepton_z = zmode in ("mumu", "ee")
    zf = "e2, E2" if zmode == "mumu" else "e1, E1" if zmode == "ee" else None
    cuts = []
    if lepton_z:
        lfl = "e2" if zmode == "mumu" else "e1"
        cuts.append(f"all M > 4 GeV [{lfl}, {lfl.upper()}]")
        cuts.append(f"any 70 GeV < M < 110 GeV [{lfl}, {lfl.upper()}]")
        if zmode == "ee" or lw == "e":
            # t-channel photon exchange: final-state e+- collinear with the beams
            cuts.append("(no abs (cos (Theta)) > 0.99875 [e1:E1])")   # as the official munumuqq cards
    else:
        q = zmode[0]
        cuts.append(f"all M > 4 GeV [{q}, {q.upper()}]")
        cuts.append(f"any 70 GeV < M < 110 GeV [{q}, {q.upper()}]")
    cut_txt = "cuts = " + "\n   and ".join(cuts)
    return f"""\
# HWWQE dedicated generation, S4 'bkg_6f' (PLAN.md Sec. 5.3), channel {chan},
# e+e- -> ({zmode}) + l nu q q' with l = {lw}, {'non-Higgs diagrams only' if part == 'nonH' else 'all diagrams (Higgs-resonant + continuum + interference)'}{', electroweak only' if chan == 'B' else ''}.
# Generated by gen/make_cards.py; beams, beam-energy spread, ISR, ISR handler and the PYTHIA6
# PYGIVE string verbatim from the official card {ref}.sin (FCC-config winter2023, v3.0.3).
# Complete 2 -> 6 tree-level matrix element (manual 10.6.1); '!H' removes every Higgs
# propagator (manual 5.4.3.2, Table 'restrictions').  Shower and hadronisation by WHIZARD's
# PYTHIA6 interface as in production; ?resonance_history as in the official winter2023
# top-pair cards (manual 10.6.4) so that W/Z decay products shower from the boson mass.
# Generator-level cuts (fiducial region, regulate gamma* -> f fbar and t-channel photons;
# looser than the Phase-2 selection, PLAN Sec. 6.1): see 'cuts' below (manual 5.7.5).
# Standard EventProducer --STDHEP job ('whizard card.sin' -> proc.stdhep -> Delphes IDEA).
#
{MANUAL}
model = SM_CKM
sqrts = 240 GeV
?resonance_history = true
resonance_on_shell_limit = 10
resonance_background_factor = 0

process proc = e1, E1 => {(chr(10) + '                       + ').join(comps)} {restr}

{cut_txt}

# Beams: verbatim from {ref}.sin
{beam_block(pk)}

! Parton shower and hadronization (verbatim from {ref}.sin)
?ps_fsr_active          = true
?ps_isr_active          = false
?hadronization_active   = true
$shower_method          = "PYTHIA6"
{pk['pygive'][0]}

# 2 -> 6: about 850 phase-space channels per component (wood, manual 5.7.4.1); more
# adaptation than the official 2 -> 3 cards is needed (test: 5x50k + 2x100k calls per
# component gave 0.04 % unweighting efficiency)
# Fixed integration seed so that every job builds (or reads) the same grids; the job seed
# (prepended by EventProducer) is restored for event generation.  WHIZARD discards grids whose
# seed differs ('VAMP: parameter mismatch'); with this pattern pre-computed proc.m*.vg files in
# the job directory are reused (tested, gen/README.md).  Once the grids exist, copy them in:
# exec ("cp <grid directory>/proc.m*.vg .")        (manual A.1)
int job_seed = seed
seed = 20261015
integrate (proc) {{ iterations = 15:200000:"gw", 5:400000:"" }}
seed = job_seed

sample_format = stdhep
$extension_stdhep = "stdhep"
simulate (proc) {{checkpoint = 100}}
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    cards = {f"hwwqe_zh_lvqq_{z}.sin": pass1_card(z) for z in Z_MODES}
    for part in ("nonH", "full"):
        for z in ("mumu", "ee"):
            for lw in ("e", "mu"):
                cards[f"hwwqe_bkg6f_A_{part}_{z}_{lw}.sin"] = s4_card("A", part, z, lw)
        for z in ("bb",):
            for lw in ("e", "mu"):
                cards[f"hwwqe_bkg6f_B_{part}_{z}_{lw}.sin"] = s4_card("B", part, z, lw)
    if args.check_only:
        print("\n".join(sorted(cards)))
        return 0
    OUTDIR.mkdir(parents=True, exist_ok=True)
    for name, text in cards.items():
        (OUTDIR / name).write_text(text)
    print(f"wrote {len(cards)} cards to {OUTDIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
