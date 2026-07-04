"""
Site-aware paths for the ZH_XSec Paper analysis.

Lets the SAME stage1 / combine scripts run on both SDCC and CERN lxplus without
editing: the site is auto-detected (override with env var FCC_SITE=sdcc|lxplus)
and the appropriate BDT-model path, output base, and condor accounting group are
returned. The lxplus paths are the original ones, left untouched.

Usage in a stage1 script:
    import os, sys
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    from site_config import bdt_model, output_dir, ACCOUNTING_GROUP, SITE
    model = bdt_model(240, "mumu")        # -> GPFS copy on SDCC, /eos on lxplus
"""
import os
import socket


def detect_site():
    """Return 'sdcc' or 'lxplus'."""
    forced = os.environ.get("FCC_SITE")
    if forced:
        return forced.lower()
    host = socket.getfqdn().lower()
    if any(tag in host for tag in ("sdcc", "bnl.gov", "usatlas")):
        return "sdcc"
    if "cern.ch" in host:
        return "lxplus"
    # fallback: if /eos/user is visible we're effectively on lxplus, else SDCC
    return "lxplus" if os.path.isdir("/eos/user") else "sdcc"


SITE = detect_site()

# SDCC GPFS base for everything we stage locally (models + outputs)
SDCC_BASE = "/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper"

ACCOUNTING_GROUP = "group_usfcc" if SITE == "sdcc" else "group_u_FCC.local_gen"


def bdt_model(ecm, flavor):
    """Path to the (existing, pre-trained) xgb BDT model for a given ecm/flavor."""
    if flavor == "qq":
        # hadronic channel: model staged on GPFS (original at MIT /ceph, not reachable);
        # TMVAHelperXGB format (SaveXGBoost + variables TList)
        return f"{SDCC_BASE}/models/S{ecm}/qq/bdt_model_ecm{ecm}.root"
    if SITE == "sdcc":
        # winter2023 stack (old TMVA/ROOT): the original xgb_bdt.root loads natively
        # via RBDT<>. (A converted new-format model xgb_bdt_rbdt.root also exists from
        # models/convert_bdt.py, only needed if ever running on the latest ROOT stack.)
        return f"{SDCC_BASE}/models/S{ecm}/{flavor}/xgb_bdt.root"
    # lxplus: original locations (240 = MidTerm, 365 = TopHiggs storage)
    if int(ecm) == 240:
        return f"/eos/user/l/lia/FCCee/MidTerm/{flavor}/BDT/xgb_bdt.root"
    return ("/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/mass_xsec/"
            f"lia/FCCee/TopHiggs/{flavor}/BDT/xgb_bdt.root")


def output_dir(ecm, flavor, stage):
    """
    Output directory for a stage ('MVAInputs', 'BDT_analysis_samples', 'final', ...).
    SDCC -> local GPFS (no /eos); lxplus -> the original /eos layout.
    """
    if SITE == "sdcc":
        return f"{SDCC_BASE}/S{ecm}/{flavor}/{stage}"
    if int(ecm) == 240:
        return f"/eos/user/l/lia/FCCee/MidTerm/{flavor}/{stage}"
    return ("/eos/experiment/fcc/ee/analyses_storage/Higgs_and_TOP/mass_xsec/"
            f"lia/FCCee/TopHiggs/{flavor}/{stage}")
