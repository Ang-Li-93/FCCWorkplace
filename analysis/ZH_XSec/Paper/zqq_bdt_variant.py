"""
Opt-in variants of the hadronic (Z->qq) BDT INPUT definitions, selected with the
environment variable ZQQ_BDT_VARIANT. Unset / empty = the nominal (corrected) inputs:
every script that imports this module keeps its default behaviour bit-identical.

Honoured by S{ecm}/qq/process_sig_bkg_samples_for_xgb.py, train_xgb.py, evaluation.py
(training set, model and plots of a variant go to separate directories, never to the
nominal training/ and models/ trees) and by rescore_qq.py (re-scoring of an existing
analysis stage with a variant model; the transform is applied before inference, the
stored branches are left untouched).

Variants
--------
bugw   Emulates the W-polar-angle inputs of the upstream reference histmaker
       (jeyserma/FCCPhysics h_zh_hadronic.py, lines 547-548 - the configuration behind the
       paper's hadronic fits):
           W1_costheta = std::abs(W1.Theta())    (the polar ANGLE of W1, not its cosine)
           W2_costheta = std::abs(W1.Theta())    (a copy of the W1 angle: no W2 information)
       The stored ntuples (zqq_stage1_common.py) only carry |cos theta| of W1 and W2; theta
       itself is not stored, so the emulation uses the FOLDED angle
           theta_f = acos(|cos theta(W1)|)  in [0, pi/2]
       for BOTH columns. Approximation: the reference |theta| in [0, pi] still distinguishes
       the forward and backward hemispheres of W1 (|.| is a no-op on TLorentzVector::Theta()),
       the folded angle does not. The loss of the W2 direction (the duplicated column) is
       reproduced exactly. Since a tree ensemble is invariant under a monotone transformation
       of an input (up to the quantile binning of the histogram method), the variant is in
       effect "the nominal 15 inputs with W2_costheta replaced by a copy of W1_costheta",
       i.e. the W2 polar angle is removed from the BDT.

Paths (nominal -> variant)
--------------------------
  training set   <STORE>/S{ecm}/qq/training/              -> <STORE>/S{ecm}/qq/training_<variant>/
  model          <STORE>/models/S{ecm}/qq/bdt_model_ecm{ecm}.root
                 -> <STORE>/models_variants/<variant>/S{ecm}/qq/bdt_model_ecm{ecm}.root
"""
import os

from site_config import SDCC_BASE, bdt_model, output_dir

KNOWN_VARIANTS = ("bugw",)

VARIANT = os.environ.get("ZQQ_BDT_VARIANT", "").strip()
if VARIANT and VARIANT not in KNOWN_VARIANTS:
    raise SystemExit(f"ERROR: ZQQ_BDT_VARIANT={VARIANT!r} unknown (known: {', '.join(KNOWN_VARIANTS)})")

# C++ (RDataFrame) expression of the folded W1 polar angle, from the stored |cos theta(W1)|
_THETA_F_W1 = "std::acos(std::min(1.0, std::max(-1.0, (double)W1_costheta)))"


def suffix(variant=VARIANT):
    """'' for the nominal inputs, '_<variant>' otherwise."""
    return f"_{variant}" if variant else ""


def training_dir(ecm, variant=VARIANT):
    """Training-set directory (preprocessed.pkl, logs/, plots/) of the nominal or variant BDT."""
    return output_dir(ecm, "qq", "training" + suffix(variant))


def model_path(ecm, variant=VARIANT):
    """TMVA-format model file: site_config.bdt_model(ecm, 'qq') for the nominal BDT, else the
    models_variants/<variant>/ tree (never the live models/ tree)."""
    if not variant:
        return bdt_model(ecm, "qq")
    return f"{SDCC_BASE}/models_variants/{variant}/S{ecm}/qq/bdt_model_ecm{ecm}.root"


def input_expressions(train_vars, variant=VARIANT):
    """
    Mapping BDT input name -> C++ expression (in terms of the stored branches) that yields
    the value fed to the BDT for this variant. Identity for the nominal inputs.
    """
    exprs = {v: v for v in train_vars}
    if variant == "bugw":
        exprs["W1_costheta"] = _THETA_F_W1
        exprs["W2_costheta"] = _THETA_F_W1
    return exprs


def apply_variant(df, variant=VARIANT):
    """
    Apply the variant transform IN PLACE to a pandas DataFrame holding the stored branches
    (process_sig_bkg_samples_for_xgb.py). Returns the frame. No-op for the nominal inputs.
    The double-precision acos is what the C++ expression above computes as well.
    """
    if variant == "bugw":
        import numpy as np
        theta_f = np.arccos(np.clip(df["W1_costheta"].to_numpy(dtype="float64"), -1.0, 1.0))
        df["W1_costheta"] = theta_f
        df["W2_costheta"] = theta_f
    return df


def latex_overrides(variant=VARIANT):
    """Axis labels of the transformed inputs (evaluation.py importance plot)."""
    if variant == "bugw":
        return {"W1_costheta": r"$\theta_{W_1}$ (folded)", "W2_costheta": r"$\theta_{W_1}$ (copy)"}
    return {}


def describe(variant=VARIANT):
    return f"ZQQ_BDT_VARIANT={variant}" if variant else "nominal inputs (ZQQ_BDT_VARIANT unset)"
