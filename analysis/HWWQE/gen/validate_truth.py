#!/usr/bin/env python3
"""Truth validation of dedicated HWWQE samples (PLAN.md Sec. 5.3, gen/README.md): record checks
and qtomo truth tomography of stage1/truth_hww.py ntuples.  H frame = W+ W- rest frame.

    python gen/validate_truth.py --out summary.json [--toys 2000] [--seed 1] \
        [--paired LABEL,LABEL,...] [--reweight S2LABEL,S1LABEL] LABEL:TARGET:TRUTH.root[:EDM4HEP.root] ...

TARGET is the expected spin state: sm (S1, --mode copy), iso (S2, 1/9), diag (S3, decohered SM).
Run from the analysis root in the repository's setup.sh environment (Key4hep 2026-04-08).

Record checks per sample: all slots filled; W = analyser + partner (stage1 slots 3, 4 are the
decaying W copies); m(W+ + W-) = m(recorded H); recorded H (slot 2) = W+ + W-; decay classes;
Z-fermion flavours; fraction with M* = min(m_W+, m_W-) below --mstar-cut; e+ beam direction.
With the EDM4hep file: number of events, events in which a W has copies (it radiated a photon or
recoiled against one: TimeShower:QEDshowerByOther) and photons emitted by W bosons.

Tomography per sample (CONVENTIONS.md; kappa from each event's m(W+ W-), m_W+, m_W-): the 80
coefficients against the target, chi^2/80 and chi^2/18 (rotation-invariant subspace) with three
p-values: asymptotic chi^2; Hotelling, for a covariance estimated from the same N events,
F = (N - k) chi^2 / (k N) ~ F(k, N - k) (exact for Gaussian per-event estimators); and
pseudo-experiments: decay angles drawn from the target at each event's kappa (qtomo.toy), same
estimator and statistic, p = (1 + #{toy >= observed}) / (1 + n_toys).  Also h44, I3 at fixed
settings (optimal for the SM state of the same events; expectation 0 for 1/9) and the unbiased
C2 arguments 2 (Tr rho^2 - Tr rho_W+^2) and 2 (Tr rho^2 - Tr rho_W-^2) (-4/9 for 1/9), with
their pseudo-experiment mean, spread and two-sided p-values.

--paired: samples generated with the same seed (one WHIZARD event stream, different --mode)
must have identical W four-momenta event by event; the largest difference is reported.
--reweight: the S2 sample reweighted to the SM, w = 9 Tr[rho_SM(kappa) Pi+ x Pi-]
(qtomo.reweight), compared with the S1 sample (chi^2 of the difference, independent errors).
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats as st

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ANALYSIS_ROOT))
from qtomo import basis, bell, config, frames, reweight, sm, stats, tomography, toy  # noqa: E402

SLOT = {name: i for i, name in enumerate(
    ("beam_em", "beam_ep", "H", "Wp", "Wm", "ana_p", "partner_p", "ana_m", "partner_m", "zf1", "zf2"))}
REQUIRED = ("beam_ep", "H", "Wp", "Wm", "ana_p", "partner_p", "ana_m", "partner_m")
TARGETS = ("sm", "iso", "diag")
ROT = basis.subspace("rotation_invariant")
H44 = basis.COEFF_LABELS.index("h44")
CHUNK = 50_000


# --------------------------------------------------------------------------
# Input
# --------------------------------------------------------------------------
def load_truth(path):
    """Truth four-vectors (n, 11, 4) as (E, px, py, pz) in GeV and PDG codes (n, 11)."""
    import uproot
    a = uproot.open(path)["events"].arrays(["truth_e", "truth_px", "truth_py", "truth_pz", "truth_pdg"],
                                           library="np")
    p4 = np.stack([np.stack(a[k]) for k in ("truth_e", "truth_px", "truth_py", "truth_pz")], axis=-1)
    return p4.astype(float), np.stack(a["truth_pdg"]).astype(int)


def scan_record(path):
    """Events of an EDM4hep file and how many contain W copies / photons emitted by a W."""
    import uproot
    t = uproot.open(path)["events"]
    keys = set(t.keys())
    dau_key = next(k for k in ("_Particle_daughters/_Particle_daughters.index", "Particle#1/Particle#1.index")
                   if k in keys)
    a = t.arrays(["Particle/Particle.PDG", "Particle/Particle.daughters_begin",
                  "Particle/Particle.daughters_end", dau_key], library="np")
    n_copy = n_gamma_ev = n_gamma = 0
    for pdg, db, de, dau in zip(a["Particle/Particle.PDG"], a["Particle/Particle.daughters_begin"],
                                a["Particle/Particle.daughters_end"], a[dau_key]):
        has_copy = has_gamma = False
        for i in np.flatnonzero(np.abs(pdg) == 24):
            d = dau[db[i]:de[i]]
            has_copy |= bool(np.any(pdg[d] == pdg[i]))
            k = int(np.sum(pdg[d] == 22))
            has_gamma |= k > 0
            n_gamma += k
        n_copy += has_copy
        n_gamma_ev += has_gamma
    n = len(a["Particle/Particle.PDG"])
    return {"file": str(path), "n_events": n, "relations": dau_key.split("/")[0],
            "n_events_with_W_copies": int(n_copy), "n_events_with_photon_from_W": int(n_gamma_ev),
            "n_photons_from_W": int(n_gamma)}


# --------------------------------------------------------------------------
# Record checks
# --------------------------------------------------------------------------
def _flavour(code):
    a = np.abs(code)
    return np.where(a == 11, "e", np.where(a == 13, "mu", np.where(a == 15, "tau",
                    np.where(np.isin(a, [1, 3, 5]), "had", np.where(code == 0, "none", "other")))))


def record_checks(p4, pdg, mstar_cut, tol):
    n = len(p4)
    complete = np.all(pdg[:, [SLOT[s] for s in REQUIRED]] != 0, axis=1)
    wp, wm, h = p4[:, SLOT["Wp"]], p4[:, SLOT["Wm"]], p4[:, SLOT["H"]]
    d_wp = np.max(np.abs(wp - p4[:, SLOT["ana_p"]] - p4[:, SLOT["partner_p"]]), axis=1)
    d_wm = np.max(np.abs(wm - p4[:, SLOT["ana_m"]] - p4[:, SLOT["partner_m"]]), axis=1)
    d_w = np.maximum(d_wp, d_wm)
    m_ww = frames.invariant_mass(wp + wm)
    m_h = frames.invariant_mass(h)
    d_h = np.max(np.abs(h - wp - wm), axis=1)
    mstar = np.minimum(frames.invariant_mass(wp), frames.invariant_mass(wm))
    f_p, f_m = _flavour(pdg[:, SLOT["ana_p"]]), _flavour(pdg[:, SLOT["ana_m"]])
    lep_p, lep_m = np.isin(f_p, ["e", "mu"]), np.isin(f_m, ["e", "mu"])
    lvqq = (lep_p & (f_m == "had")) | (lep_m & (f_p == "had"))
    beam = p4[:, SLOT["beam_ep"], 1:]
    k = int(np.sum(mstar < mstar_cut))
    zf = {f"{a}/{b}": int(np.sum((pdg[:, SLOT["zf1"]] == a) & (pdg[:, SLOT["zf2"]] == b)))
          for a, b in sorted(set(zip(pdg[:, SLOT["zf1"]].tolist(), pdg[:, SLOT["zf2"]].tolist())))}
    return {
        "n_events": n, "n_complete": int(complete.sum()),
        "tolerance_GeV": tol,
        "W_eq_analyser_plus_partner": {"n_fail": int(np.sum(d_w > tol)), "max_abs_diff_GeV": float(d_w.max())},
        "m_WW_minus_m_recorded_H": {"n_fail": int(np.sum(np.abs(m_ww - m_h) > tol)),
                                    "max_abs_diff_GeV": float(np.max(np.abs(m_ww - m_h)))},
        "m_WW_GeV": {"mean": float(m_ww.mean()), "min": float(m_ww.min()), "max": float(m_ww.max())},
        "m_recorded_H_GeV": {"mean": float(m_h.mean()), "min": float(m_h.min()), "max": float(m_h.max())},
        "recorded_H_eq_WW": {"n_fail": int(np.sum(d_h > tol)), "max_abs_diff_GeV": float(d_h.max())},
        "lvqq_emu": {"n": int(lvqq.sum()), "W+_leptonic": int(np.sum(lvqq & lep_p)),
                     "W-_leptonic": int(np.sum(lvqq & lep_m)),
                     "e_analyser": int(np.sum(lvqq & ((f_p == "e") | (f_m == "e")))),
                     "mu_analyser": int(np.sum(lvqq & ((f_p == "mu") | (f_m == "mu"))))},
        "z_fermions_pdg": zf,
        "mstar_below_cut": {"cut_GeV": mstar_cut, "n": k, "fraction": k / n,
                            "fraction_err": float(np.sqrt(max(k, 1) * (n - k) / n) / n),
                            "min_mstar_GeV": float(mstar.min())},
        "beam_ep_direction_mean": (beam / np.linalg.norm(beam, axis=1)[:, None]).mean(axis=0).tolist(),
    }


# --------------------------------------------------------------------------
# Tomography
# --------------------------------------------------------------------------
def _chunked(fn, kappa):
    return np.concatenate([fn(kappa[i:i + CHUNK]) for i in range(0, len(kappa), CHUNK)])


def _sm_vectors(kappa):
    return basis.pack(*sm.coefficients(kappa))


def _decohered_vectors(kappa):
    return basis.coefficient_vector(sm.decohered(sm.density_matrix(kappa)))


def prediction(target, kappa):
    """Expected coefficient vector of the sample: mean of the per-event target states."""
    if target == "iso":
        return np.zeros(basis.N_COEFF)
    return _chunked(_sm_vectors if target == "sm" else _decohered_vectors, kappa).mean(axis=0)


class ToySampler:
    """Decay angles drawn from the target state at each event's kappa (conditional on the W masses)."""

    def __init__(self, target, kappa):
        self.target, self.n = target, len(kappa)
        if target == "sm":
            self.states, self.weights = toy.sm_weights(kappa)
        elif target == "diag":
            self.states = sm.decohered(sm.density_matrix(np.array([1.0, 20.0])))   # 1-d affine family
            self.weights = toy.affine_weights(self.states, _chunked(_decohered_vectors, kappa))

    def __call__(self, rng):
        if self.target == "iso":
            return toy.isotropic(self.n, rng)
        return toy.generate_per_event(self.states, self.weights, rng)


def statistic(angles, pred, g, weights=None):
    res = tomography.estimate(*angles, weights=weights)
    resid = res.c - pred
    chi2, ndf, p = stats.chi_square(resid, res.cov)
    chi2_r, ndf_r, p_r = stats.chi_square(ROT.T @ resid, ROT.T @ res.cov @ ROT)
    inv, inv_s = res.invariants, res.invariants_sigma
    return res, {"chi2": chi2, "ndf": ndf, "p_asymptotic": p, "chi2_rot": chi2_r, "ndf_rot": ndf_r,
                 "p_rot_asymptotic": p_r, "max_abs_pull": float(np.max(np.abs(resid) / res.sigma)),
                 "h44": float(res.c[H44]), "h44_err": float(res.sigma[H44]),
                 "i3_fixed": float(g @ res.c), "i3_fixed_err": float(np.sqrt(g @ res.cov @ g)),
                 "c2_arg_wplus": 2.0 * inv.c2_arg_wplus, "c2_arg_wplus_err": 2.0 * inv_s.c2_arg_wplus,
                 "c2_arg_wminus": 2.0 * inv.c2_arg_wminus, "c2_arg_wminus_err": 2.0 * inv_s.c2_arg_wminus}


def hotelling_p(chi2, k, n):
    """p-value of chi^2 = N (mean - mu)^T S_ML^-1 (mean - mu) with S_ML estimated from the same N events."""
    return float(st.f.sf((n - k) * chi2 / (k * n), k, n - k)) if n > k else float("nan")


def tomography_check(p4, pdg, target, n_toys, rng, i3_starts):
    good = np.all(pdg[:, [SLOT[s] for s in REQUIRED]] != 0, axis=1)
    p_ww = p4[:, SLOT["Wp"]] + p4[:, SLOT["Wm"]]
    ang = frames.decay_angles(p_ww, p4[:, SLOT["Wp"]], p4[:, SLOT["Wm"]], p4[:, SLOT["ana_p"]],
                              p4[:, SLOT["ana_m"]], p4[:, SLOT["beam_ep"]])
    kappa = sm.kappa(frames.invariant_mass(p_ww), ang["m_Wp"], ang["m_Wm"])
    good &= np.isfinite(ang["theta_p"]) & np.isfinite(ang["theta_m"]) & np.isfinite(kappa)
    angles = tuple(ang[k][good] for k in ("theta_p", "phi_p", "theta_m", "phi_m"))
    kappa = kappa[good]
    n = int(good.sum())
    pred = prediction(target, kappa)
    pred_sm = pred if target == "sm" else prediction("sm", kappa)
    ref = bell.i3_optimise(basis.density_matrix_from_vector(pred_sm), n_starts=i3_starts, full_output=True)
    g = bell.i3_weights(ref.u, ref.v)
    res, out = statistic(angles, pred, g)
    out.update(n_events=n, target=target, h44_pred=float(pred[H44]), i3_fixed_pred=float(g @ pred),
               i3_sm_optimum=float(ref.value), c2_arg_pred=[2.0 * float(x) for x in
                                                            bell.c2_terms(basis.density_matrix_from_vector(pred))],
               p_hotelling=hotelling_p(out["chi2"], out["ndf"], n),
               p_rot_hotelling=hotelling_p(out["chi2_rot"], out["ndf_rot"], n),
               min_eigenvalue=float(res.min_eigenvalue))
    if n_toys > 0:
        sampler = ToySampler(target, kappa)
        keys = ("chi2", "chi2_rot", "i3_fixed", "c2_arg_wplus", "c2_arg_wminus")
        toys = {k: np.empty(n_toys) for k in keys}
        t0 = time.time()
        for i in range(n_toys):
            _, s = statistic(tuple(sampler(rng)), pred, g)
            for k in keys:
                toys[k][i] = s[k]
        out["toys"] = {"n": n_toys, "seconds": round(time.time() - t0, 1)}
        for k in ("chi2", "chi2_rot"):
            out["toys"][f"p_{k}"] = float((1 + np.sum(toys[k] >= out[k])) / (1 + n_toys))
            out["toys"][f"{k}_mean"] = float(toys[k].mean())
        for k in ("i3_fixed", "c2_arg_wplus", "c2_arg_wminus"):
            mu, sd = float(toys[k].mean()), float(toys[k].std(ddof=1))
            out["toys"][k] = {"mean": mu, "std": sd, "pull": (out[k] - mu) / sd,
                              "p_two_sided": float((1 + np.sum(np.abs(toys[k] - mu) >= abs(out[k] - mu)))
                                                   / (1 + n_toys))}
    return out, {"angles": angles, "kappa": kappa, "good": good, "pred_sm": pred_sm}


def reweight_check(base, ref):
    """S2 (base) reweighted to the SM against S1 (ref): chi^2 of the coefficient difference."""
    w = reweight.weights_from_isotropic(reweight.target_sm(base["kappa"]), *base["angles"])
    r_w = tomography.estimate(*base["angles"], weights=w)
    r_1 = tomography.estimate(*ref["angles"])
    chi2, ndf, p = stats.chi_square(r_w.c - r_1.c, r_w.cov + r_1.cov)
    chi2_r, ndf_r, p_r = stats.chi_square(ROT.T @ (r_w.c - r_1.c), ROT.T @ (r_w.cov + r_1.cov) @ ROT)
    return {"chi2": chi2, "ndf": ndf, "p_asymptotic": p, "chi2_rot": chi2_r, "ndf_rot": ndf_r, "p_rot_asymptotic": p_r,
            "weight_max": float(w.max()), "weight_mean": float(w.mean()), "n_eff": float(w.sum() ** 2 / np.sum(w * w)),
            "h44_reweighted": float(r_w.c[H44]), "h44_reweighted_err": float(r_w.sigma[H44]),
            "h44_s1": float(r_1.c[H44]), "h44_s1_err": float(r_1.sigma[H44])}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("samples", nargs="+", help="LABEL:TARGET:TRUTH.root[:EDM4HEP.root], TARGET in sm, iso, diag")
    ap.add_argument("--out", required=True, help="summary JSON")
    ap.add_argument("--toys", type=int, default=2000, help="pseudo-experiments per sample (0: none)")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--mstar-cut", type=float, default=12.0,
                    help="GeV; lower W* mass of the central winter2023 samples (PYTHIA6 CKIN(45) = CKIN(47) = 12 GeV)")
    ap.add_argument("--tol", type=float, default=1e-3, help="GeV, tolerance of the four-momentum identities")
    ap.add_argument("--paired", action="append", default=[], help="comma-separated labels with one WHIZARD stream")
    ap.add_argument("--reweight", action="append", default=[], help="S2LABEL,S1LABEL")
    args = ap.parse_args(argv)
    i3_starts = config.load("phase1")["i3_n_starts"]
    rng = np.random.default_rng(args.seed)
    summary, cache, raw = {"toys": args.toys, "seed": args.seed, "i3_n_starts": i3_starts, "samples": {}}, {}, {}
    for item in args.samples:
        label, target, truth, *rec = item.split(":")
        if target not in TARGETS:
            raise SystemExit(f"{label}: target must be one of {TARGETS}")
        p4, pdg = load_truth(truth)
        raw[label] = p4
        entry = {"truth_file": truth, "record": record_checks(p4, pdg, args.mstar_cut, args.tol)}
        if rec:
            entry["edm4hep"] = scan_record(rec[0])
        entry["tomography"], cache[label] = tomography_check(p4, pdg, target, args.toys, rng, i3_starts)
        summary["samples"][label] = entry
        t, r = entry["tomography"], entry["record"]
        tp = t.get("toys", {})
        print(f"{label:12s} {target:4s} N={t['n_events']:5d}  chi2/80 = {t['chi2']:6.1f} (p {t['p_asymptotic']:.3f}, "
              f"Hotelling {t['p_hotelling']:.3f}, toys {tp.get('p_chi2', float('nan')):.3f});  chi2/18 = "
              f"{t['chi2_rot']:5.1f} (p {t['p_rot_asymptotic']:.3f}, toys {tp.get('p_chi2_rot', float('nan')):.3f});  "
              f"I3fix = {t['i3_fixed']:.3f} +- {t['i3_fixed_err']:.3f} (pred {t['i3_fixed_pred']:.3f});  "
              f"W!=a+p: {r['W_eq_analyser_plus_partner']['n_fail']}, |m(WW)-mH|>tol: "
              f"{r['m_WW_minus_m_recorded_H']['n_fail']}, H!=WW: {r['recorded_H_eq_WW']['n_fail']}")
    for group in args.paired:
        labels = group.split(",")
        ref = raw[labels[0]][:, [SLOT["Wp"], SLOT["Wm"]]]
        summary.setdefault("paired", {})[group] = {
            lab: {"n_events": len(raw[lab]), "max_abs_diff_W_GeV": float(np.max(np.abs(raw[lab][:, [SLOT["Wp"], SLOT["Wm"]]]
                                                                                        - ref)))
                  if len(raw[lab]) == len(ref) else None} for lab in labels[1:]}
        print(f"paired {group}: {summary['paired'][group]}")
    for pair in args.reweight:
        base, ref = pair.split(",")
        summary.setdefault("reweight", {})[pair] = reweight_check(cache[base], cache[ref])
        print(f"reweight {pair}: {summary['reweight'][pair]}")
    Path(args.out).write_text(json.dumps(summary, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
