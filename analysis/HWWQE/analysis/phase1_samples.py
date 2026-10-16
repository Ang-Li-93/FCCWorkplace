"""Phase 1, PLAN.md Sec. 5.1: build config/samples.yaml for the 240 GeV l nu q q study.

Sources (nothing typed by hand): the winter2023 IDEA directory listing on EOS (xrdfs),
the standard procDict on cvmfs (cross section, number of events), and the generator
cards in the FCC-config submodule (beam-energy spread, ISR, beamstrahlung, H decay).

    python analysis/phase1_samples.py          # writes config/samples.yaml
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ANALYSIS_ROOT.parents[1]
sys.path.insert(0, str(ANALYSIS_ROOT))
from qtomo import config  # noqa: E402

PRODUCTION = "winter2023"
DETECTOR = "IDEA"
EOS_SERVER = "root://eospublic.cern.ch"
EOS_DIR = f"/eos/experiment/fcc/ee/generation/DelphesEvents/{PRODUCTION}/{DETECTOR}"
PROCDICT = f"/cvmfs/fcc.cern.ch/FCCDicts/FCCee_procDict_{PRODUCTION}_{DETECTOR}.json"
CARDS = REPO_ROOT / "FCC-config/winter2023/FCCee/Generator"

# Roles for the l nu q q study at 240 GeV (PLAN.md Sec. 5.1 item 2, channels A and B).
SIGNAL = {"A": ["wzp6_ee_mumuH_HWW_ecm240", "wzp6_ee_eeH_HWW_ecm240"],
          "B": ["wzp6_ee_qqH_HWW_ecm240", "wzp6_ee_ssH_HWW_ecm240",
                "wzp6_ee_ccH_HWW_ecm240", "wzp6_ee_bbH_HWW_ecm240"]}
BACKGROUND_PATTERNS = {
    "zh_other": r"^wzp6_ee_(ee|mumu|tautau|nunu|nuenue|numunumu|qq|ss|cc|bb)H_H(WW|ZZ|tautau|bb|cc|gg|ss|mumu|Za|aa|inv)(_[A-Za-z]+)?_ecm240$"
                r"|^wzp6_ee_llH_HZZ_[a-z]+_ecm240$|^wzp6_ee_(ee|mumu|tautau|nunu|qq|ss|cc|bb)H_ecm240$|^mgp8_ee_zh_ecm240$",
    "zh_variation": r"^wzp6_ee_(ee|mumu|tautau|nunu|qq|ss|cc|bb)H_(BES-(higher|lower)-1pc|mH-(higher|lower)-(50|100)MeV)_ecm240$",
    "diboson": r"^p8_ee_(WW|ZZ)(_ee|_mumu)?_ecm240$",
    "four_fermion": r"^wzp6_ee_munumuqq_[A-Za-z]+_ecm240$|^wzp6_ee_(WWa|aqqW|aqqZ|allZ|alnuW)_ecm240$",
    "two_fermion": r"^(p8_ee_Zqq|wzp6_ee_(qq|tautau|mumu|ee_Mee_30_150|eea|mumua|tautaua))_ecm240$|^wzp6_gaga_[a-z]+_60_ecm240$",
    "single_boson": r"^wzp6_(egamma|gammae)_eZ_Z(ee|mumu|qq)_ecm240$|^wzp6_ee_nuenueZ_ecm240$",
}

# Channels a sample enters (PLAN.md Sec. 0: A = l nu q q + Z -> ll, B = l nu q q + Z -> qq,
# C = q q q q + Z -> nunu).  ZH samples by their Z decay; the remaining families are generic
# backgrounds whose relevance is decided by the Phase 2 selection.
Z_CHANNEL = {"ee": "A", "mumu": "A", "tautau": "A", "ll": "A", "qq": "B", "ss": "B", "cc": "B", "bb": "B",
             "nunu": "C", "nuenue": "C", "numunumu": "C"}


def channels(name, role):
    m = re.match(r"^wzp6_ee_([a-z]+)H_", name)
    if m and m.group(1) in Z_CHANNEL:
        return [Z_CHANNEL[m.group(1)]]
    if name.startswith("mgp8_ee_zh"):
        return ["A", "B", "C"]
    return ["A", "B"] if role != "signal" else []


def eos_samples():
    out = subprocess.run(["xrdfs", EOS_SERVER.split("//")[1], "ls", EOS_DIR],
                         check=True, capture_output=True, text=True, timeout=300).stdout
    return sorted(line.rsplit("/", 1)[1] for line in out.split())


def eos_files(sample):
    out = subprocess.run(["xrdfs", EOS_SERVER.split("//")[1], "ls", f"{EOS_DIR}/{sample}"],
                         check=True, capture_output=True, text=True, timeout=300).stdout
    # '.sys.v#.<name>' entries are EOS version directories (size 0), not data files
    return sorted(f"{EOS_SERVER}/{p}" for p in out.split()
                  if p.endswith(".root") and not p.rsplit("/", 1)[1].startswith(".sys.v#"))


def generator(sample):
    """Generator and beam settings read from the card of the sample."""
    if sample.startswith("wzp6_"):
        card = CARDS / "Whizard/v3.0.3" / f"{sample}.sin"
        info = {"generator": "Whizard 3.0.3 + Pythia6 (shower, hadronisation, resonance decays)"}
        if not card.exists():
            return dict(info, card=None)
        text = card.read_text()
        beams = re.search(r"^beams\s*=\s*(.+)$", text, re.M)
        spread = re.search(r"^gaussian_spread1\s*=\s*(\S+)", text, re.M)
        info.update(card=str(card.relative_to(REPO_ROOT)),
                    beams=beams.group(1).strip() if beams else None,
                    beam_energy_spread=spread.group(1) if spread else None,
                    isr="isr" in (beams.group(1) if beams else ""),
                    beamstrahlung="circe" in text)
        h = re.search(r"PMAS\(25,1\)=([\d.Ee+-]+);\s*PMAS\(25,2\)=([\d.Ee+-]+)", text)
        if h:
            info.update(m_H=float(h.group(1)), Gamma_H=float(h.group(2)),
                        higgs_decay="Pythia6 PYGIVE MDME switches (see card)")
        return info
    if sample.startswith("p8_"):
        card = CARDS / "Pythia8" / f"{sample}.cmd"
        info = {"generator": "Pythia8"}
        if not card.exists():
            return dict(info, card=None)
        text = "\n".join(l.split("!")[0] for l in card.read_text().splitlines())
        spread = re.search(r"Beams:allowMomentumSpread\s*=\s*(\w+)", text)
        isr = re.search(r"PartonLevel:ISR\s*=\s*(\w+)", text)
        info.update(card=str(card.relative_to(REPO_ROOT)),
                    beam_energy_spread=(spread.group(1) if spread else "off (default)"),
                    isr=(isr.group(1) == "on") if isr else None, beamstrahlung=False)
        return info
    return {"generator": "unknown prefix", "card": None}


def main():
    proc = json.loads(Path(PROCDICT).read_text())
    available = set(eos_samples())
    const = config.load("constants")
    entries = {}

    def add(name, role, channel=None):
        if name not in available:
            print(f"WARNING: {name} not on EOS, skipped")
            return
        e = proc.get(name)
        files = eos_files(name)
        entries[name] = {"role": role, **({"channel": channel} if channel else {}),
                         "channels": [channel] if channel else channels(name, role),
                         "cross_section_pb": e["crossSection"] if e else None,
                         "n_events": e["numberOfEvents"] if e else None,
                         "kfactor": e["kfactor"] if e else None,
                         "matching_efficiency": e["matchingEfficiency"] if e else None,
                         "n_files": len(files), "files": files, **generator(name)}
        if not e:
            print(f"WARNING: {name} not in the procDict")

    for ch, names in SIGNAL.items():
        for n in names:
            add(n, "signal", ch)
    for role, pat in BACKGROUND_PATTERNS.items():
        for n in sorted(available):
            if re.match(pat, n) and n not in entries:
                add(n, f"background_{role}")
    lumi_pb = 10.8e6
    for e in entries.values():
        if e["cross_section_pb"]:
            e["expected_events"] = e["cross_section_pb"] * lumi_pb
            e["mc_over_data"] = e["n_events"] / e["expected_events"]
    out = {"production": PRODUCTION, "detector": DETECTOR, "prodTag": f"FCCee/{PRODUCTION}/{DETECTOR}/",
           "eos_dir": f"{EOS_SERVER}/{EOS_DIR}", "procdict": PROCDICT,
           "sqrt_s_GeV": const["sqrt_s"],
           "luminosity_pb": lumi_pb,
           "luminosity_note": "standard FCC-ee 240 GeV run, 10.8 ab^-1 (PLAN.md; same as the repository's ZH analyses)",
           "beams_note": "generator record: e- along +z, e+ along -z, head-on (no crossing angle) — checked on wzp6_ee_mumuH_HWW_ecm240",
           "production_stack": "key4hep 2022-12-23 (/cvmfs/sw.hsf.org/spackages6/key4hep-stack/2022-12-23/...), all samples, "
                               "per https://fcc-physics-events.web.cern.ch/fcc-ee/rec/winter2023/IDEA/edm4hep-root",
           "signal_generator": dict(config.load("phase1")["generator"],
                                    note="Whizard 3.0.3 (ee -> f f H, on-shell H) + Pythia 6.427 (H -> W W* decay, "
                                         "shower, hadronisation); config/phase1.yaml 'generator'"),
           "normalisation_notes": [
               "procDict sigma x BR uses BR(H -> WW) = 0.2152 (YR4 value at m_H = 125.09 GeV, "
               "https://twiki.cern.ch/twiki/bin/view/LHCPhysics/CERNYellowReportPageBR) while the generator uses m_H = 125.0 GeV",
               "no W* below 12 GeV in the H -> WW* samples (Pythia6 CKIN(45) = CKIN(47) = 12 GeV): the tree-level fraction with "
               "M* = min(m_W) < 12 GeV is 5.79 % (PDG constants) to 5.89 % (generator parameters), so yields with M* >= 12 GeV "
               "are sigma x BR x (1 - f) (LOG.md 2026-10-15, analysis/phase1_kinematics.py window)",
               "the recorded H (PDG 25) of the winter2023 records is the pre-shower documentation copy: use W+ + W- (LOG.md)",
           ],
           "samples": entries}
    path = config.CONFIG_DIR / "samples.yaml"
    path.write_text("# Generated by analysis/phase1_samples.py — do not edit by hand.\n"
                    + yaml.safe_dump(out, sort_keys=False, width=140))
    n_sig = sum(e["role"] == "signal" for e in entries.values())
    print(f"wrote {path}: {len(entries)} samples ({n_sig} signal)")


if __name__ == "__main__":
    main()
