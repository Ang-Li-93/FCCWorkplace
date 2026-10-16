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
    "zh_other": r"^wzp6_ee_(ee|mumu|tautau|nunu|qq|ss|cc|bb)H_H(WW|ZZ|tautau|bb|cc|gg|ss|mumu|Za|aa|inv)_ecm240$",
    "diboson": r"^p8_ee_(WW|ZZ)(_ee|_mumu)?_ecm240$",
    "two_fermion": r"^(p8_ee_Zqq|wzp6_ee_(qq|tautau|mumu|ee_Mee_30_150))_ecm240$",
    "single_boson": r"^wzp6_(egamma|gammae)_eZ_Z(ee|mumu|qq)_ecm240$|^wzp6_ee_nuenueZ_ecm240$",
}


def eos_samples():
    out = subprocess.run(["xrdfs", EOS_SERVER.split("//")[1], "ls", EOS_DIR],
                         check=True, capture_output=True, text=True, timeout=300).stdout
    return sorted(line.rsplit("/", 1)[1] for line in out.split())


def eos_files(sample):
    out = subprocess.run(["xrdfs", EOS_SERVER.split("//")[1], "ls", f"{EOS_DIR}/{sample}"],
                         check=True, capture_output=True, text=True, timeout=300).stdout
    return sorted(f"{EOS_SERVER}/{p}" for p in out.split() if p.endswith(".root"))


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
           "samples": entries}
    path = config.CONFIG_DIR / "samples.yaml"
    path.write_text("# Generated by analysis/phase1_samples.py — do not edit by hand.\n"
                    + yaml.safe_dump(out, sort_keys=False, width=140))
    n_sig = sum(e["role"] == "signal" for e in entries.values())
    print(f"wrote {path}: {len(entries)} samples ({n_sig} signal)")


if __name__ == "__main__":
    main()
