"""Phase 1, PLAN.md Sec. 5.2: how strong is the truth-validation statement?

    python analysis/phase1_validation.py prepare      [--out DIR]   # per-event angles, masses, flavours
    python analysis/phase1_validation.py check        [--out DIR]   # reproduce phase1_truth; test MassiveModel
    python analysis/phase1_validation.py calibration  [--out DIR]   # 1. calibration of the chi^2 test
    python analysis/phase1_validation.py sensitivity  [--out DIR]   # 2. Fisher reach + injection tests
    python analysis/phase1_validation.py subsets      [--out DIR]   # 3. subset consistency, mass effects
    python analysis/phase1_validation.py moments      [--out DIR]   # 3b. direct single-W moments (masses)
    python analysis/phase1_validation.py plot         [--out DIR]
    python analysis/phase1_validation.py all          [--out DIR]   # calibration ... plot (after prepare)

Runtime on one core: prepare 3 min (GPFS reads), calibration 0.5 min, sensitivity 6 min, subsets 6 min,
moments 4 min; peak memory 3 GB (subsets).

Inputs: the truth stage1 ntuples of analysis/phase1_truth.py (config/phase1.yaml output_dir).  The
H frame is the W+ W- rest frame and each event is compared with the tree-level SM state at its own
kappa_i (m_H, m_W+, m_W- of the event), exactly as in ``phase1_truth.py tomography``.  Results go to
DIR (default: <output_dir>/validation) as JSON; figures to <figure_dir>/validation_*.

Study parameters (seeds, splits, confidence levels, injection scan, quadrature, tested subsets and pairs,
mass grids) are the ``validation:`` block of config/phase1.yaml (PLAN rule 5); the channel-A samples are
the signal samples of config/samples.yaml with channel A.  Fermion masses are read off the truth
four-vectors (Pythia6 values), not set here.

Mass effects (task 3).  For W -> f1 fbar2 through a V-A current the spin-summed tensor
L^{mu nu} = Tr[(p1slash + m1) gamma^mu P_L (p2slash - m2) P_R gamma^nu] = Tr[p1slash gamma^mu p2slash
gamma^nu P_L] has the massless form, so the tree-level |M|^2 of H -> W+ W- -> 4f is the massless
(p_partner+ . p_ana-)(p_partner- . p_ana+) evaluated with the massive momenta, up to terms
O(m_f^2 / m_W^2) < 5e-4 from the q^mu q^nu / m_W^2 part of the propagators (Goldstone exchange).
``MassiveModel`` integrates the moment estimators against it exactly (product quadrature; the
integrand is a polynomial of degree 4 on each sphere) for each event's masses; ``check`` tests it.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy import optimize
from scipy import stats as st

from qtomo import basis, bell, config, frames, plotting, reweight, sm, stats, tomography, toy

SLOTS = ("beam_em", "beam_ep", "H", "Wp", "Wm", "ana_p", "partner_p", "ana_m", "partner_m", "zf1", "zf2")
SLOT = {name: i for i, name in enumerate(SLOTS)}
FERMION_SLOTS = ("ana_p", "partner_p", "ana_m", "partner_m")
H44 = basis.COEFF_LABELS.index("h44")
CHUNK = 100_000


def cfg():
    """(config/phase1.yaml, its ``validation:`` block)."""
    c = config.load("phase1")
    return c, c["validation"]


def channel_samples(channel):
    """Names of the signal samples of config/samples.yaml with this channel."""
    return tuple(n for n, s in config.load("samples")["samples"].items()
                 if s["role"] == "signal" and s.get("channel") == channel)


def _omni_key(ndf, alpha):
    return f"eps_omnibus{ndf}_alpha{alpha:g}"


def _outdir(args, c):
    out = Path(args.out) if args.out else config.resolve(c["output_dir"]) / "validation"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _dump(path, obj):
    def conv(x):
        if isinstance(x, dict):
            return {str(k): conv(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [conv(v) for v in x]
        if isinstance(x, np.ndarray):
            return conv(x.tolist())
        if isinstance(x, (np.floating, float)):
            return float(x)
        if isinstance(x, (np.integer,)):
            return int(x)
        if isinstance(x, (np.bool_,)):
            return bool(x)
        return x
    Path(path).write_text(json.dumps(conv(obj), indent=1))
    print(f"wrote {path}")


# --------------------------------------------------------------------------
# Preparation: per-event quantities from the truth ntuples
# --------------------------------------------------------------------------
def _read_truth(path):
    """Truth four-vectors (n, 11, 4) as (E, px, py, pz) in float64 and PDG codes (n, 11)."""
    import awkward as ak
    import uproot
    branches = ["truth_e", "truth_px", "truth_py", "truth_pz", "truth_pdg"]
    arr = uproot.open(path)["events"].arrays(branches, library="ak")
    if not np.all(ak.to_numpy(ak.num(arr["truth_e"])) == len(SLOTS)):
        raise RuntimeError(f"{path}: events without {len(SLOTS)} truth slots")
    flat = {k: ak.to_numpy(ak.flatten(arr[k])).reshape(-1, len(SLOTS)) for k in arr.fields}
    p4 = np.stack([flat[k] for k in ("truth_e", "truth_px", "truth_py", "truth_pz")], axis=-1).astype(float)
    return p4, flat["truth_pdg"].astype(int)


def prepare(args):
    """Per-event decay angles in the W+W- rest frame (as phase1_truth.py), masses, flavours."""
    c, _ = cfg()
    out = _outdir(args, c)
    samples = [n for n, s in config.load("samples")["samples"].items() if s["role"] == "signal"]
    truth_dir = config.resolve(c["output_dir"]) / "truth"
    cols = {k: [] for k in ("theta_p", "phi_p", "theta_m", "phi_m", "m_Wp", "m_Wm", "m_H", "sample",
                            "complete")}
    for k in FERMION_SLOTS:
        cols[f"pdg_{k}"] = []
        cols[f"mass_{k}"] = []
    for isam, name in enumerate(samples):
        files = sorted((truth_dir / name).glob("chunk_*.root"))
        for f in files:
            p4, pdg = _read_truth(f)
            p_h = p4[:, SLOT["Wp"]] + p4[:, SLOT["Wm"]]
            ang = frames.decay_angles(p_h, p4[:, SLOT["Wp"]], p4[:, SLOT["Wm"]], p4[:, SLOT["ana_p"]],
                                      p4[:, SLOT["ana_m"]], p4[:, SLOT["beam_ep"]])
            for k in ("theta_p", "phi_p", "theta_m", "phi_m", "m_Wp", "m_Wm"):
                cols[k].append(ang[k])
            cols["m_H"].append(frames.invariant_mass(p_h))
            cols["sample"].append(np.full(len(p4), isam, dtype=np.int8))
            need = [SLOT[s] for s in ("H", "Wp", "Wm", "ana_p", "ana_m", "beam_ep")]
            cols["complete"].append(np.all(pdg[:, need] != 0, axis=1))
            for k in FERMION_SLOTS:
                cols[f"pdg_{k}"].append(pdg[:, SLOT[k]].astype(np.int8))
                cols[f"mass_{k}"].append(frames.invariant_mass(p4[:, SLOT[k]]).astype(np.float32))
            print(f"{name}: {f.name} {len(p4)} events")
    data = {k: np.concatenate(v) for k, v in cols.items()}
    data["samples"] = np.array(samples)
    np.savez(out / "events.npz", **data)
    print(f"wrote {out / 'events.npz'}: {len(data['m_H'])} events")


class Events:
    """The prepared per-event arrays plus derived quantities (kappa, M*, decay classes)."""

    def __init__(self, path):
        with np.load(path) as d:
            self.__dict__.update({k: d[k] for k in d.files})
        self.n = len(self.m_H)
        self.kappa = sm.kappa(self.m_H, self.m_Wp, self.m_Wm)
        self.mstar = np.minimum(self.m_Wp, self.m_Wm)
        self.good = (self.complete & np.isfinite(self.theta_p) & np.isfinite(self.theta_m)
                     & np.isfinite(self.kappa))
        self.leg_p = self._leg(self.pdg_ana_p)
        self.leg_m = self._leg(self.pdg_ana_m)
        self.is_A = np.isin(self.samples[self.sample], channel_samples("A"))
        # fermion masses: per-PDG median of the truth invariant masses (float32 rounding
        # smears massless particles by ~0.02 GeV), clipped at zero
        self.mass_table = {}
        for k in FERMION_SLOTS:
            codes = getattr(self, f"pdg_{k}")
            masses = getattr(self, f"mass_{k}")
            for code in np.unique(codes):
                med = float(np.median(masses[codes == code]))
                self.mass_table[int(code)] = max(med, 0.0) if med > 0.05 else 0.0
        self.m_f = {k: np.vectorize(self.mass_table.get, otypes=[float])(getattr(self, f"pdg_{k}"))
                    for k in FERMION_SLOTS}

    @staticmethod
    def _leg(code):
        a = np.abs(code)
        out = np.full(code.shape, "had", dtype=object)
        out[a == 11], out[a == 13], out[a == 15] = "e", "mu", "tau"
        out[code == 0] = "none"
        return out

    def angles(self, idx):
        return tuple(getattr(self, k)[idx] for k in ("theta_p", "phi_p", "theta_m", "phi_m"))

    def masks(self):
        """Named event selections used by the studies (all within ``good``)."""
        lp, lm = self.leg_p, self.leg_m
        lep_p, lep_m = np.isin(lp, ["e", "mu"]), np.isin(lm, ["e", "mu"])
        lvqq = self.good & ((lep_p & (lm == "had")) | (lep_m & (lp == "had")))
        tvqq = self.good & (((lp == "tau") & (lm == "had")) | ((lm == "tau") & (lp == "had")))
        # hadronic leg of l nu q q / tau nu q q: analyser (down-type) and partner (up-type) flavours
        had_is_p = (lp == "had")
        ana_had = np.abs(np.where(had_is_p, self.pdg_ana_p, self.pdg_ana_m))
        par_had = np.abs(np.where(had_is_p, self.pdg_partner_p, self.pdg_partner_m))
        lep_flav = np.where(had_is_p, lm, lp)
        m_had = np.where(had_is_p, self.m_Wp, self.m_Wm)
        m_lep = np.where(had_is_p, self.m_Wm, self.m_Wp)
        out = {
            "lvqq_emu": lvqq,
            "had_ud": lvqq & (ana_had == 1) & (par_had == 2),
            "had_cs": lvqq & (ana_had == 3) & (par_had == 4),
            "had_us": lvqq & (ana_had == 3) & (par_had == 2),
            "had_cd": lvqq & (ana_had == 1) & (par_had == 4),
            "had_xb": lvqq & (ana_had == 5),
            "lep_e": lvqq & (lep_flav == "e"),
            "lep_mu": lvqq & (lep_flav == "mu"),
            "lep_Wplus": lvqq & ~had_is_p,
            "lep_Wminus": lvqq & had_is_p,
            "channelA_samples": lvqq & self.is_A,
            "channelB_samples": lvqq & ~self.is_A,
            "had_offshell": lvqq & (m_had < m_lep),
            "had_onshell": lvqq & (m_had >= m_lep),
            "tvqq": tvqq,
            "tvqq_tau_Wplus": tvqq & (lp == "tau"),
            "tvqq_tau_Wminus": tvqq & (lm == "tau"),
            "tvqq_tau_offshell": tvqq & (m_lep < m_had),
            "tvqq_tau_onshell": tvqq & (m_lep >= m_had),
            "tvqq_had_cs": tvqq & (ana_had == 3) & (par_had == 4),
            "tvlv": self.good & (((lp == "tau") & np.isin(lm, ["e", "mu"])) | ((lm == "tau") & np.isin(lp, ["e", "mu"]))),
            "tvtv": self.good & (lp == "tau") & (lm == "tau"),
            "all_decays": self.good.copy(),
        }
        out["lvqq_cs_offshell"] = out["had_cs"] & (m_had < m_lep)
        out["lvqq_ud_offshell"] = out["had_ud"] & (m_had < m_lep)
        return out


def _load(args, c):
    return Events(_outdir(args, c) / "events.npz")


# --------------------------------------------------------------------------
# Moment sums against the per-event SM prediction
# --------------------------------------------------------------------------
def sm_vectors(kappa):
    """Coefficient vectors (n, 80) of rho_SM(kappa_i)."""
    return basis.pack(*sm.coefficients(kappa))


class Fit:
    """Tomography of one event set against the per-event SM prediction.

    c, cov       moment estimates and their covariance (as tomography.estimate, ``phase1_truth``)
    pred         mean of the rho_SM(kappa_i) coefficients over the events (weighted if weights)
    cov_cond     covariance of the mean residual x_i - c_SM(kappa_i), i.e. conditional on the
                 observed kappa_i (from which the prediction is computed); cov - cov_cond is the
                 spread of c_SM(kappa_i) over the events / N, which the standard test includes
    """

    def __init__(self, angles, kappa, weights=None):
        acc_x, acc_r = tomography.MomentAccumulator(), tomography.MomentAccumulator()
        sum_pred = np.zeros(basis.N_COEFF)
        n = len(kappa)
        for start in range(0, n, CHUNK):
            sl = slice(start, start + CHUNK)
            x = basis.estimator_vector(*(a[sl] for a in angles))
            s = sm_vectors(kappa[sl])
            w = None if weights is None else weights[sl]
            acc_x.add_vectors(x, w)
            acc_r.add_vectors(x - s, w)
            sum_pred += s.sum(axis=0) if w is None else w @ s
        self.n = n
        self.acc = acc_x
        self.c, self.cov = acc_x.mean, acc_x.cov
        self.pred = sum_pred / acc_x.sum_w
        self.cov_cond = acc_r.cov
        self.resid = self.c - self.pred
        self.sigma = np.sqrt(np.diag(self.cov))
        self.n_eff = acc_x.n_eff

    @classmethod
    def of(cls, ev, mask, weights=None):
        idx = np.flatnonzero(mask) if np.asarray(mask).dtype == bool else np.asarray(mask)
        return cls(ev.angles(idx), ev.kappa[idx], weights)

    def chi2(self, cov=None, resid=None, sub=None):
        """(chi2, ndf, p) of the residual; ``sub`` 'rot' = rotation-invariant subspace."""
        cov = self.cov if cov is None else cov
        r = self.resid if resid is None else resid
        if sub == "rot":
            rot = basis.subspace("rotation_invariant")
            return stats.chi_square(rot.T @ r, rot.T @ cov @ rot)
        return stats.chi_square(r, cov)


def whiten(resid, cov):
    """Residual components in the eigenbasis of cov divided by the square roots of the
    eigenvalues: independent N(0, 1) under the null hypothesis."""
    lam, vec = np.linalg.eigh(cov)
    return (vec.T @ resid) / np.sqrt(lam)


def _gls(d, cov, r=None):
    """Fisher information F = d^T C^-1 d of a shift along d and, with a residual r, the
    one-parameter estimate mu = d^T C^-1 r / F (sigma 1/sqrt(F))."""
    cd = np.linalg.solve(cov, d)
    f = float(d @ cd)
    return (f, None) if r is None else (f, float(cd @ r) / f)


def observables(pred, c, cov, n_starts):
    """I3 at the optimal settings of the predicted state (fixed settings: linear, unbiased) and h44,
    with standard deviations from cov, and the predicted I3, C2, h44; also returns the I3 weights.
    (The unbiased C2 and its uncertainty come from the accumulator, see ``fit_summary``.)"""
    rho_pred = basis.density_matrix_from_vector(pred)
    ref = bell.i3_optimise(rho_pred, n_starts=n_starts, full_output=True)
    g = bell.i3_weights(ref.u, ref.v)
    return {"i3_pred": ref.value, "i3": float(g @ c), "i3_err": float(np.sqrt(g @ cov @ g)),
            "h44_pred": float(pred[H44]), "h44": float(c[H44]), "h44_err": float(np.sqrt(cov[H44, H44])),
            "c2_pred": float(bell.c2(rho_pred))}, g


def fit_summary(fit, n_starts, with_obs=True):
    """chi^2 (80 and rotation-invariant 18) against the per-event SM prediction, plus observables."""
    chi, ndf, p = fit.chi2()
    chi_r, ndf_r, p_r = fit.chi2(sub="rot")
    out = {"n_events": fit.n, "chi2": chi, "ndf": ndf, "p": p, "chi2_rot": chi_r, "ndf_rot": ndf_r,
           "p_rot": p_r, "max_abs_pull": float(np.max(np.abs(fit.resid) / fit.sigma))}
    if with_obs:
        obs, _ = observables(fit.pred, fit.c, fit.cov, n_starts)
        res = fit.acc.result()
        obs["c2"] = 2.0 * max(res.invariants.c2_arg_wplus, res.invariants.c2_arg_wminus)
        obs["c2_err"] = 2.0 * max(res.invariants_sigma.c2_arg_wplus, res.invariants_sigma.c2_arg_wminus)
        out.update(obs)
    return out


def _bins(c):
    b = np.array(c["mstar_bins"], dtype=float)
    return list(zip(b[:-1], b[1:]))


def _bin_name(lo, hi):
    return f"{lo:g}-{hi:g}"


# --------------------------------------------------------------------------
# 1. Calibration of the chi^2 test on disjoint subsamples
# --------------------------------------------------------------------------
def calibration(args):
    c, par = cfg()
    ev = _load(args, c)
    idx = np.flatnonzero(ev.masks()["lvqq_emu"])
    rng = np.random.default_rng(par["seed"])
    rot = basis.subspace("rotation_invariant")
    out = {"n_events": len(idx), "sample": "l nu q q (l = e, mu), all six winter2023 signal samples",
           "splits": {}}
    for label, k in (("main", par["n_subsamples"]), ("fine", par["n_subsamples_fine"])):
        parts = np.array_split(rng.permutation(idx), k)
        rows, white, white_rot = [], [], []
        for part in parts:
            fit = Fit.of(ev, np.sort(part))
            row = {"n": fit.n}
            for tag, cov in (("", fit.cov), ("_cond", fit.cov_cond)):
                row["chi2" + tag], row["ndf"], row["p" + tag] = fit.chi2(cov=cov)
                row["chi2_rot" + tag], row["ndf_rot"], row["p_rot" + tag] = fit.chi2(cov=cov, sub="rot")
            rows.append(row)
            white.append(whiten(fit.resid, fit.cov))
            white_rot.append(whiten(rot.T @ fit.resid, rot.T @ fit.cov @ rot))
        white, white_rot = np.concatenate(white), np.concatenate(white_rot)
        summary = {}
        for key, ndf_key in (("", "ndf"), ("_cond", "ndf"), ("_rot", "ndf_rot"), ("_rot_cond", "ndf_rot")):
            pk = "p" + key
            p = np.array([r[pk] for r in rows])
            chi = np.array([r["chi2" + key] for r in rows])
            ndf = rows[0][ndf_key]
            ks = st.kstest(p, "uniform")
            tot = chi.sum()
            summary[key.strip("_") or "full"] = {
                "ks_stat": float(ks.statistic), "ks_p": float(ks.pvalue),
                "p_values": p.tolist(), "chi2_sum": float(tot), "ndf_sum": int(ndf * len(rows)),
                "p_chi2_sum": float(st.chi2.sf(tot, ndf * len(rows))),
                "mean_chi2_over_ndf": float(chi.mean() / ndf),
                "mean_chi2_over_ndf_err": float(np.sqrt(2.0 / ndf / len(rows))),
                "fisher_combined_p": float(st.combine_pvalues(p, method="fisher").pvalue),
                "n_p_below_0.05": int(np.sum(p < 0.05)), "min_p": float(p.min())}
        for name, w in (("whitened_full", white), ("whitened_rot", white_rot)):
            ks = st.kstest(w, "norm")
            # (eigenvector signs are arbitrary, so only the spread and the shape are meaningful)
            summary[name] = {"n": len(w), "std": float(w.std(ddof=1)),
                             "std_err": float(1 / np.sqrt(2 * (len(w) - 1))),
                             "ks_p": float(ks.pvalue), "values": w.tolist()}
        out["splits"][label] = {"n_subsamples": k, "events_per_subsample": int(np.mean([r["n"] for r in rows])),
                                "rows": rows, "summary": summary}
        s = summary
        print(f"[{label}] {k} subsamples: KS p (80) = {s['full']['ks_p']:.3f}, (18) = {s['rot']['ks_p']:.3f}; "
              f"sum chi2 = {s['full']['chi2_sum']:.0f}/{s['full']['ndf_sum']} (p = {s['full']['p_chi2_sum']:.3f}), "
              f"rot {s['rot']['chi2_sum']:.0f}/{s['rot']['ndf_sum']} (p = {s['rot']['p_chi2_sum']:.3f}); "
              f"whitened std {s['whitened_full']['std']:.3f} "
              f"KS p {s['whitened_full']['ks_p']:.3f}")
    # the full-sample test itself and the Hotelling correction for an estimated covariance
    fit = Fit.of(ev, idx)
    n, k = fit.n, basis.N_COEFF
    out["full_sample"] = {"chi2": fit.chi2(), "chi2_rot": fit.chi2(sub="rot"), "chi2_cond": fit.chi2(cov=fit.cov_cond),
                          "hotelling_factor": (n - 1) * k / (n - k) / k}
    _dump(_outdir(args, c) / "validation_calibration.json", out)


# --------------------------------------------------------------------------
# 2. Sensitivity: Fisher reach for admixtures, precision, injection tests
# --------------------------------------------------------------------------
ALT_LABELS = {"decohered": "decohered SM", "isotropic": "$\\mathbb{1}/9$",
              "cp_odd": "CP-odd $(|{+}{-}\\rangle - |{-}{+}\\rangle)/\\sqrt{2}$"}


def alternatives(par):
    """The admixed alternative states of the ``validation:`` block (implemented: ALT_LABELS)."""
    names = tuple(par["alternatives"])
    unknown = set(names) - set(ALT_LABELS)
    if unknown:
        raise ValueError(f"validation.alternatives: no implementation for {sorted(unknown)}")
    return names


def cp_odd_state():
    psi = np.zeros(9, dtype=complex)
    psi[sm.I_PM], psi[sm.I_MP] = 1 / np.sqrt(2), -1 / np.sqrt(2)
    return np.outer(psi, psi.conj())


def alt_mean(name, pred):
    """Mean over the events of the alternative state's coefficients, given the mean SM
    coefficients ``pred`` (the decohered state is linear in rho)."""
    if name == "decohered":
        return basis.coefficient_vector(sm.decohered(basis.density_matrix_from_vector(pred)))
    if name == "isotropic":
        return np.zeros(basis.N_COEFF)
    if name == "cp_odd":
        return basis.coefficient_vector(cp_odd_state())
    raise ValueError(name)


def alt_states(name, kappa):
    """Per-event alternative state for the reweighting (PerEventStates or a fixed matrix)."""
    if name == "decohered":
        return reweight.target_decohered_sm(kappa)
    if name == "isotropic":
        return reweight.target_isotropic()
    return cp_odd_state()


def noncentrality_for_median(ndf, alpha):
    """lambda with median(chi^2'_ndf(lambda)) = chi^2_ndf quantile 1 - alpha: the admixture
    detected by the omnibus test at level alpha in half of the experiments."""
    crit = st.chi2.isf(alpha, ndf)
    return optimize.brentq(lambda lam: st.ncx2.median(ndf, lam) - crit, 1e-6, 1e4)


def reach(fit, par, alpha_cfg, n_starts):
    """Fisher 95% CL admixtures and omnibus-test reach for one event set."""
    rot = basis.subspace("rotation_invariant")
    lam80 = {a: noncentrality_for_median(80, a) for a in (par["alpha"], alpha_cfg)}
    lam18 = {a: noncentrality_for_median(18, a) for a in (par["alpha"], alpha_cfg)}
    obs, g = observables(fit.pred, fit.c, fit.cov, n_starts)
    res = fit.acc.result()
    c2_err = 2.0 * max(res.invariants_sigma.c2_arg_wplus, res.invariants_sigma.c2_arg_wminus)
    rho_pred = basis.density_matrix_from_vector(fit.pred)
    out = {"n_events": fit.n, "i3_err": obs["i3_err"], "c2_err": c2_err, "h44_err": obs["h44_err"],
           "i3_pred": obs["i3_pred"], "c2_pred": obs["c2_pred"], "h44_pred": obs["h44_pred"], "alt": {}}
    zs = par["single_observable_z"]
    for name in alternatives(par):
        d = alt_mean(name, fit.pred) - fit.pred
        f, mu = _gls(d, fit.cov, fit.resid)
        f_rot, mu_rot = _gls(rot.T @ d, rot.T @ fit.cov @ rot, rot.T @ fit.resid)
        z = np.sqrt(par["fisher_delta_chi2"])
        e = {"fisher_info": f, "eps95_fisher": z / np.sqrt(f), "eps95_fisher_rot": z / np.sqrt(f_rot),
             "eps_hat": mu, "eps_hat_err": 1 / np.sqrt(f), "eps_hat_rot": mu_rot, "eps_hat_rot_err": 1 / np.sqrt(f_rot)}
        for a in lam80:
            e[_omni_key(80, a)] = float(np.sqrt(lam80[a] / f))
            e[_omni_key(18, a)] = float(np.sqrt(lam18[a] / f_rot))
        # single observables: eps that shifts them by zs = 1.96 sigma (linear for I3 at fixed settings, h44;
        # C2 exactly as a function of eps on the predicted mixture)
        e["eps95_i3"] = zs * obs["i3_err"] / abs(g @ d) if abs(g @ d) > 0 else np.inf
        e["eps95_h44"] = zs * obs["h44_err"] / abs(d[H44]) if abs(d[H44]) > 0 else np.inf
        rho_alt = basis.density_matrix_from_vector(fit.pred + d)
        c2_0 = bell.c2(rho_pred)

        def c2_shift(eps):
            return abs(bell.c2((1 - eps) * rho_pred + eps * rho_alt) - c2_0) - zs * c2_err
        grid = np.linspace(0.0, 1.0, 2001)
        vals = np.array([c2_shift(x) for x in grid])
        first = np.flatnonzero(vals > 0)
        e["eps95_c2"] = (optimize.brentq(c2_shift, grid[first[0] - 1], grid[first[0]])
                         if first.size else np.inf)          # first crossing (C2 need not be monotonic)
        e["slope_i3"], e["slope_h44"] = float(g @ d), float(d[H44])
        out["alt"][name] = e
    out["lambda_median_80"] = {str(a): v for a, v in lam80.items()}
    out["lambda_median_18"] = {str(a): v for a, v in lam18.items()}
    return out


def _weight_diagnostics(r, rejected, w, fit_range):
    """Ratio/weight tail: CCDF P(R > W) on a log grid, its power-law slope for W in ``fit_range``
    (config: [10, 1000]) where at least 20 events remain (a pure base gives slope -2), and variance
    concentration."""
    tail_w = np.logspace(-1, 4, 51)
    rs = np.sort(r)
    ccdf = 1.0 - np.searchsorted(rs, tail_w, side="right") / len(rs)
    ok = (tail_w >= fit_range[0]) & (tail_w <= fit_range[1]) & (ccdf * len(rs) >= 20)
    slope = np.polyfit(np.log(tail_w[ok]), np.log(ccdf[ok]), 1)[0] if ok.sum() > 2 else np.nan
    dev2 = (w - w.mean()) ** 2
    top = np.sort(dev2)[::-1]
    return {"rejected_fraction": float(rejected.mean()), "mean_ratio": float(r.mean()),
            "max_ratio": float(r.max()), "ratio_quantiles": np.quantile(r, [0.5, 0.9, 0.99, 0.999, 0.9999]).tolist(),
            "tail_W": tail_w.tolist(), "tail_ccdf": ccdf.tolist(), "tail_slope": float(slope),
            "n_eff_over_n": float(w.sum() ** 2 / (w @ w) / len(w)),
            "var_share_top_1e-4": float(top[:max(1, len(w) // 10000)].sum() / dev2.sum()),
            "var_share_top_1e-3": float(top[:max(1, len(w) // 1000)].sum() / dev2.sum()),
            "max_weight": float(w.max())}


def _replace_angles(name, kappa, angles, frac, rng):
    """Injection by replacement (unit weights): a random fraction ``frac`` of the events gets
    analyser directions drawn from the alternative state at its own kappa (qtomo.toy)."""
    n = len(kappa)
    sel = rng.uniform(size=n) < frac
    m = int(sel.sum())
    if name == "isotropic":
        new = toy.isotropic(m, rng)
    elif name == "cp_odd":
        new = toy.generate(cp_odd_state(), m, rng)
    else:
        # decohered SM = t (|+-><+-| + |-+><-+|) + (1 - 2t) |00><00|, t = 1/(2 + kappa^2): affine in t,
        # spanned by two of its members (weights exact; checked against toy.affine_weights)
        ref_k = np.array([1.0, 20.0])
        states = np.array([sm.decohered(sm.density_matrix(k)) for k in ref_k])
        t, t_ref = 1 / (2 + kappa[sel] ** 2), 1 / (2 + ref_k ** 2)
        a = (t - t_ref[1]) / (t_ref[0] - t_ref[1])
        weights = np.column_stack([a, 1 - a])
        chk = slice(0, min(m, 1000))
        targets = basis.coefficient_vector(sm.decohered(sm.density_matrix(kappa[sel][chk])))
        if not np.allclose(toy.affine_weights(states, targets), weights[chk], atol=1e-9):
            raise RuntimeError("decohered-SM affine weights do not reproduce the target states")
        new = toy.generate_per_event(states, weights, rng)
    out = [a.copy() for a in angles]
    for a, b in zip(out, new):
        a[sel] = b
    return tuple(out), m


def sensitivity(args):
    c, par = cfg()
    ev = _load(args, c)
    masks = ev.masks()
    lvqq = masks["lvqq_emu"]
    alpha_cfg = c["p_value_threshold"]
    omni = _omni_key(80, par["alpha"])
    alts = alternatives(par)
    out = {"sets": {}}
    for lo, hi in [(None, None)] + _bins(c):
        sel = lvqq if lo is None else lvqq & (ev.mstar >= lo) & (ev.mstar < hi)
        if sel.sum() < par["min_events_bin"]:
            continue
        name = "inclusive" if lo is None else _bin_name(lo, hi)
        out["sets"][name] = reach(Fit.of(ev, sel), par, alpha_cfg, c["i3_n_starts"])
        r = out["sets"][name]
        print(f"{name:10s} N={r['n_events']:8d} sigma(I3)={r['i3_err']:.4f} sigma(C2)={r['c2_err']:.4f} "
              f"sigma(h44)={r['h44_err']:.4f} | " + "  ".join(
                  f"{a}: eps95 {r['alt'][a]['eps95_fisher']:.4f} omni {r['alt'][a][omni]:.4f} "
                  f"hat {r['alt'][a]['eps_hat']:+.4f}+-{r['alt'][a]['eps_hat_err']:.4f}" for a in alts))

    # injection tests on the inclusive sample
    idx = np.flatnonzero(lvqq)
    angles, kappa = ev.angles(idx), ev.kappa[idx]
    fit0 = Fit(angles, kappa)
    base = reweight.target_sm(kappa)
    inc = out["sets"]["inclusive"]
    rng = np.random.default_rng(par["seed"] + 1)
    parts = np.array_split(rng.permutation(len(idx)), par["n_subsamples"])
    inj = {}
    for name in alts:
        d = alt_mean(name, fit0.pred) - fit0.pred
        f, eps_hat0 = _gls(d, fit0.cov, fit0.resid)
        eps_main = inc["alt"][name][omni]
        # ratio weights R = Tr[rho_alt Pi Pi] / Tr[rho_SM(kappa_i) Pi Pi] with qtomo.reweight
        r_alt, rejected, _ = reweight.weights_ratio(alt_states(name, kappa), base, *angles)
        # the prescribed call for the chosen eps: target (1 - eps) rho_SM + eps rho_alt per event
        alt_pe = alt_states(name, kappa)
        sm_pe = base

        def make(i, eps=eps_main, alt_pe=alt_pe):
            a = alt_pe.coefficients(i) if isinstance(alt_pe, reweight.PerEventStates) else \
                np.broadcast_to(basis.coefficient_vector(alt_pe), (len(i), basis.N_COEFF))
            return (1 - eps) * sm_pe.coefficients(i) + eps * a
        target = reweight.PerEventStates(make, np.arange(len(idx)))
        w_main, rej_main, frac_main = reweight.weights_ratio(target, base, *angles)
        lin = np.where(rejected, 0.0, 1 - eps_main + eps_main * r_alt)
        e = {"eps_main": eps_main, "fisher_info": f, "eps_hat0": eps_hat0,
             "weights_linear_check_max_abs_diff": float(np.max(np.abs(lin - w_main))),
             "rejected_fraction": frac_main,
             "ratio_weights": _weight_diagnostics(r_alt[~rejected], rejected, r_alt[~rejected],
                                                  par["weight_tail_fit_range"]),
             "weights_main": _weight_diagnostics(w_main[~rej_main], rej_main, w_main, par["weight_tail_fit_range"]),
             "scan": []}
        # reweighting noise per unit eps: s = mean (R - 1) x versus its expectation d
        s_shift = Fit(angles, kappa, np.where(rejected, 0.0, r_alt)).c - fit0.c
        e["reweight_noise_chi2_per_eps2"] = float((s_shift - d) @ np.linalg.solve(fit0.cov, s_shift - d))
        e["signal_chi2_per_eps2"] = f
        for mult in par["injection_scan"]:
            eps = min(1.0, mult * eps_main)
            w = np.where(rejected, 0.0, 1 - eps + eps * r_alt)
            fw = Fit(angles, kappa, w)
            chi, ndf, p = fw.chi2()
            chi_r = fw.chi2(sub="rot")
            fw_f, eps_hat = _gls(d, fw.cov, fw.resid)
            pred_cond = float((fit0.resid + eps * d) @ np.linalg.solve(fit0.cov, fit0.resid + eps * d))
            lam = eps ** 2 * f
            # replacement injection (unit weights)
            ang_r, n_rep = _replace_angles(name, kappa, angles, eps, np.random.default_rng(par["seed"] + 7))
            fr = Fit(ang_r, kappa)
            chi_rep = fr.chi2()
            _, eps_hat_rep = _gls(d, fr.cov, fr.resid)
            e["scan"].append({
                "eps": eps, "chi2_reweight": chi, "p_reweight": p, "chi2_rot_reweight": chi_r[0],
                "eps_hat_reweight": eps_hat, "eps_hat_reweight_err": 1 / np.sqrt(fw_f),
                "chi2_replace": chi_rep[0], "p_replace": chi_rep[2], "eps_hat_replace": eps_hat_rep,
                "n_replaced": n_rep, "chi2_pred_conditional": pred_cond, "lambda": lam,
                "chi2_pred_mean": 80 + lam, "chi2_pred_q16": st.ncx2.ppf(0.16, 80, lam),
                "chi2_pred_q84": st.ncx2.ppf(0.84, 80, lam), "n_eff_over_n": fw.n_eff / fw.n})
            print(f"  {name:9s} eps={eps:.4f}: chi2 reweight {chi:.1f} (pred cond {pred_cond:.1f}, mean {80 + lam:.1f}) "
                  f"replace {chi_rep[0]:.1f}; eps_hat rw {eps_hat:+.4f} rep {eps_hat_rep:+.4f} (+-{1/np.sqrt(f):.4f}) "
                  f"n_eff/n {fw.n_eff / fw.n:.3f}")
        # closure of the reweighted estimate on disjoint subsamples, against the injected truth
        for tag, eps in (("eps_main", eps_main), ("eps_1", 1.0)):
            chis = []
            for part in parts:
                part = np.sort(part)
                ang_k = tuple(a[part] for a in angles)
                w = np.where(rejected[part], 0.0, 1 - eps + eps * r_alt[part])
                fk = Fit(ang_k, kappa[part], w)
                pk = Fit(ang_k, kappa[part])        # unweighted SM prediction of the subsample
                truth = pk.pred + eps * (alt_mean(name, pk.pred) - pk.pred)
                chis.append(stats.chi_square(fk.c - truth, fk.cov)[0])
            chis = np.array(chis)
            pv = st.chi2.sf(chis, 80)
            e[f"closure_{tag}"] = {"eps": eps, "chi2": chis.tolist(), "mean_chi2_over_ndf": float(chis.mean() / 80),
                                   "mean_err": float(np.sqrt(2 / 80 / len(chis))),
                                   "ks_p": float(st.kstest(pv, "uniform").pvalue)}
            print(f"  {name:9s} closure at eps={eps:.3f}: <chi2>/80 = {chis.mean() / 80:.3f} +- "
                  f"{np.sqrt(2 / 80 / len(chis)):.3f}, KS p = {st.kstest(pv, 'uniform').pvalue:.3f}")
        inj[name] = e
    out["injection"] = inj
    _dump(_outdir(args, c) / "validation_sensitivity.json", out)


# --------------------------------------------------------------------------
# Fermion-mass effects: exact tree-level prediction with massive momenta
# --------------------------------------------------------------------------
_MINK = np.array([1.0, -1.0, -1.0, -1.0])


class MassiveModel:
    """Expected moment-estimator vector E[x] for H -> W+ W- -> 4 fermions with massive fermions.

    Weight (tree level, V-A; see the module docstring): |M|^2 ∝ (p_partner+ . p_ana-)(p_partner- . p_ana+)
    with the exact massive four-momenta, uniform in the two analyser directions (two-body phase
    space in each W rest frame).  Kinematics in the H rest frame with axes (n, r, k) = (x, y, z):
    W+ along +k, W- along -k, each analyser at (theta, phi) in its W rest frame reached by a pure
    boost along k (as frames.decay_angles undoes).  E[x] is a ratio of two integrals of
    polynomials of degree <= 4 on each sphere, done exactly by product quadrature.
    Tested by ``check``: with all fermion masses zero it equals the coefficients of rho_SM(kappa)
    (to 1e-15), it does not depend on the quadrature order, and an accept-reject sample of explicit
    massive four-vectors with this weight, analysed with frames.decay_angles, reproduces it.
    """

    def __init__(self, n_cos, n_phi):
        th, ph, wt = basis.sphere_quadrature(n_cos, n_phi)
        self.u = np.stack([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)], axis=-1)
        j = th.size
        self.x = basis.estimator_vector(np.repeat(th, j), np.repeat(ph, j), np.tile(th, j), np.tile(ph, j))
        self.w2 = np.outer(wt, wt).ravel()

    def _leg(self, m_w, m_a, m_b, e_w, p_w, sign):
        e_a = (m_w ** 2 + m_a ** 2 - m_b ** 2) / (2 * m_w)
        p = np.sqrt(np.maximum(sm.kallen(m_w ** 2, m_a ** 2, m_b ** 2), 0.0)) / (2 * m_w)
        gam, bgam = e_w / m_w, sign * p_w / m_w
        out = []
        for e, s in ((e_a, 1.0), (m_w - e_a, -1.0)):           # analyser, partner
            q = s * p[:, None, None] * self.u[None]               # (n, J, 3) in the W rest frame
            e = np.broadcast_to(e[:, None], q.shape[:2])
            four = np.empty(q.shape[:2] + (4,))
            four[..., 0] = gam[:, None] * e + bgam[:, None] * q[..., 2]
            four[..., 1], four[..., 2] = q[..., 0], q[..., 1]
            four[..., 3] = gam[:, None] * q[..., 2] + bgam[:, None] * e
            out.append(four)
        return out

    def expect(self, m_h, m_p, m_m, ma_p, mb_p, ma_m, mb_m):
        """E[x] (n, 80) for per-event H and W masses and analyser/partner masses (GeV)."""
        e_p = (m_h ** 2 + m_p ** 2 - m_m ** 2) / (2 * m_h)
        p_w = np.sqrt(np.maximum(sm.kallen(m_h ** 2, m_p ** 2, m_m ** 2), 0.0)) / (2 * m_h)
        a_p, b_p = self._leg(m_p, ma_p, mb_p, e_p, p_w, +1.0)
        a_m, b_m = self._leg(m_m, ma_m, mb_m, m_h - e_p, p_w, -1.0)
        d1 = np.einsum("nia,nja->nij", b_p * _MINK, a_m)          # partner+ . analyser-
        d2 = np.einsum("nia,nja->nij", a_p * _MINK, b_m)          # analyser+ . partner-
        w = (d1 * d2).reshape(len(m_h), -1) * self.w2
        return (w @ self.x) / w.sum(axis=1, keepdims=True)


def mass_shift_sums(ev, groups, model, chunk=20_000):
    """Sum over the events of each group of delta_i = E_massive[x] - c_SM(kappa_i), the
    expected change of the moments from the fermion masses; returns {group: (sum, count)}."""
    union = np.zeros(ev.n, bool)
    for m in groups.values():
        union |= m
    idx = np.flatnonzero(union)
    sums = {g: np.zeros(basis.N_COEFF) for g in groups}
    for start in range(0, len(idx), chunk):
        sl = idx[start:start + chunk]
        mf = [ev.m_f[k][sl] for k in FERMION_SLOTS]
        delta = model.expect(ev.m_H[sl], ev.m_Wp[sl], ev.m_Wm[sl], *mf) - sm_vectors(ev.kappa[sl])
        for g, m in groups.items():
            sel = m[sl]
            if sel.any():
                sums[g] += delta[sel].sum(axis=0)
    return {g: (sums[g], int(groups[g].sum())) for g in groups}


def analytic_marginal(kappa, x_a, x_b):
    """First-order (in x = m^2/M^2) single-W marginal with the other W integrated out:
    density ∝ (1 + k^2 - x) + 2 k sqrt(k^2 - 1)(x_a - x_b) cos(theta) - (k^2 - 1)(1 - 2x) cos^2(theta),
    x = x_a + x_b (a = analyser, b = partner).  Returns (ratio of the tensor (cos^2) analysing power to
    the massless one, <cos theta>)."""
    x = x_a + x_b
    k2 = kappa ** 2
    a, b, cc = 1 + k2 - x, 2 * kappa * np.sqrt(np.maximum(k2 - 1, 0)) * (x_a - x_b), -(k2 - 1) * (1 - 2 * x)
    a0, c0 = 1 + k2, -(k2 - 1)
    tensor = (cc / (a + cc / 3)) / (c0 / (a0 + c0 / 3))
    mean_cos = (b / 3) / (a + cc / 3)
    return tensor, mean_cos


# --------------------------------------------------------------------------
# 3. Subset consistency and fermion-mass effects
# --------------------------------------------------------------------------
def subsets(args):
    c, par = cfg()
    ev = _load(args, c)
    masks = ev.masks()
    bins = _bins(c)
    edges = np.array(c["mstar_bins"], dtype=float)
    bin_idx = np.digitize(ev.mstar, edges) - 1          # -1 below, len(bins) above the last edge
    model = MassiveModel(*par["quadrature"])
    obs_in_bins = set(par["subsets_observables_in_bins"])
    groups = {}
    for name in par["subsets"]:
        groups[(name, "inclusive")] = masks[name]
        for b, (lo, hi) in enumerate(bins):
            groups[(name, _bin_name(lo, hi))] = masks[name] & (bin_idx == b)
    groups = {k: v for k, v in groups.items() if v.sum() >= par["min_events_subset"]}
    shifts = mass_shift_sums(ev, groups, model)
    res = {"mass_table_GeV": {str(k): v for k, v in sorted(ev.mass_table.items())}, "sets": {}, "pairs": {}}
    fits = {}
    for (name, b), m in groups.items():
        fit = Fit.of(ev, m)
        fits[(name, b)] = fit
        delta = shifts[(name, b)][0] / shifts[(name, b)][1]
        out = fit_summary(fit, c["i3_n_starts"], with_obs=(b == "inclusive" or name in obs_in_bins))
        lam, mu = _gls(delta, fit.cov, fit.resid)
        chi_m = stats.chi_square(fit.resid - delta, fit.cov)
        chi_m_rot = fit.chi2(resid=fit.resid - delta, sub="rot")
        out.update({"mass_lambda": lam, "mass_mu": mu, "mass_mu_err": 1 / np.sqrt(lam) if lam > 0 else np.inf,
                    "chi2_massive": chi_m[0], "p_massive": chi_m[2], "chi2_rot_massive": chi_m_rot[0],
                    "p_rot_massive": chi_m_rot[2], "delta_h44": float(delta[H44]),
                    "delta_rel_max": float(np.max(np.abs(delta) / np.maximum(np.abs(fit.pred), 1e-3))),
                    "delta_pull_max": float(np.max(np.abs(delta) / fit.sigma)),
                    "delta": delta.tolist(), "resid": fit.resid.tolist(), "sigma": fit.sigma.tolist(),
                    "pred": fit.pred.tolist()})
        res["sets"].setdefault(name, {})[b] = out
        print(f"{name:20s} {b:10s} N={fit.n:8d} chi2={out['chi2']:6.1f}/80 p={out['p']:.3f} rot p={out['p_rot']:.3f} "
              f"| mass: lambda={lam:6.2f} mu={mu:+.2f}+-{1 / np.sqrt(lam) if lam > 0 else np.inf:.2f} "
              f"chi2_massive={chi_m[0]:6.1f} p={chi_m[2]:.3f}")
    for a, b2 in par["pairs"]:
        for b in ["inclusive"] + [_bin_name(lo, hi) for lo, hi in bins]:
            if (a, b) not in fits or (b2, b) not in fits:
                continue
            fa, fb = fits[(a, b)], fits[(b2, b)]
            da = shifts[(a, b)][0] / shifts[(a, b)][1]
            db = shifts[(b2, b)][0] / shifts[(b2, b)][1]
            diff, cov = fa.resid - fb.resid, fa.cov + fb.cov
            chi, ndf, p = stats.chi_square(diff, cov)
            rot = basis.subspace("rotation_invariant")
            chi_r, ndf_r, p_r = stats.chi_square(rot.T @ diff, rot.T @ cov @ rot)
            chi_m, _, p_m = stats.chi_square(diff - (da - db), cov)
            lam, mu = _gls(da - db, cov, diff)
            res["pairs"].setdefault(f"{a}|{b2}", {})[b] = {
                "n_a": fa.n, "n_b": fb.n, "chi2": chi, "ndf": ndf, "p": p, "chi2_rot": chi_r, "ndf_rot": ndf_r,
                "p_rot": p_r, "chi2_massive": chi_m, "p_massive": p_m, "mass_lambda": lam, "mass_mu": mu,
                "mass_mu_err": 1 / np.sqrt(lam) if lam > 0 else np.inf,
                "max_abs_pull": float(np.max(np.abs(diff) / np.sqrt(np.diag(cov))))}
            print(f"PAIR {a:18s} vs {b2:18s} {b:10s} chi2={chi:6.1f}/{ndf} p={p:.3f} rot {chi_r:5.1f}/{ndf_r} p={p_r:.3f} "
                  f"| mass lambda={lam:5.2f} mu={mu:+.2f}")
    # analytic first-order single-W analysing powers versus M (the other W integrated out, massless)
    ap = par["analysing_power"]
    m_grid = np.array(ap["w_masses"], dtype=float)
    m_on, m_typ = ap["m_onshell"], ap["m_offshell_typical"]
    m_h = c["generator"]["m_H"]
    table = {}
    for label, (ana, partner) in ap["channels"].items():
        ma = ev.mass_table[ana] if ana else 0.0
        mb = ev.mass_table[partner] if partner else 0.0
        rows = []
        for mw in m_grid:
            other = m_on if mw < 60 else m_typ       # off-shell leg: partner on shell; on-shell leg: typical M*
            k = float(sm.kappa(m_h, mw, other))
            ten, mcos = analytic_marginal(k, (ma / mw) ** 2, (mb / mw) ** 2)
            ex = model.expect(np.array([m_h]), np.array([other]), np.array([mw]), np.zeros(1), np.zeros(1),
                              np.array([ma]), np.array([mb]))[0]
            ref = sm_vectors(np.array([k]))[0]
            gt = basis.RANK2 @ ex[8:16]
            gt0 = basis.RANK2 @ ref[8:16]
            rows.append({"M": mw, "M_other": other, "kappa": k, "x": (ma ** 2 + mb ** 2) / mw ** 2,
                         "tensor_ratio_first_order": float(ten), "mean_cos_first_order": float(mcos),
                         "tensor_ratio_exact": float(np.linalg.norm(gt) / np.linalg.norm(gt0)),
                         "h44_ratio_exact": float(ex[H44] / ref[H44])})
        table[label] = rows
    res["analytic_analysing_power"] = table
    _dump(_outdir(args, c) / "validation_subsets.json", res)


# --------------------------------------------------------------------------
# 3b. Direct single-W moments of the analyser on the off-shell W (model-independent mass test)
# --------------------------------------------------------------------------
# For the W+ (W-) analyser the marginal density is (3/4pi)[1/3 + 3 f.q+] ([1/3 + 3 g.q-]), so
#   <cos theta+> = (3/2)(f3 + sqrt3 f8),   <cos theta-> = -(3/2)(g3 + sqrt3 g8)     (vector polarisation)
#   <P2(cos theta)> = (9/10)(f3 - f8/sqrt3) for the W+, the same with g for the W-   (tensor polarisation)
# The massless SM gives <cos theta> = 0 and <P2> = (1 - kappa^2)/(5 (2 + kappa^2)).
# Species (analyser |PDG|, required partner |PDG|), mass bins and sets: validation.moments in config.
_I = {k: basis.COEFF_LABELS.index(k) for k in ("f3", "f8", "g3", "g8")}


def _leg_moments(vec, leg):
    if leg == "p":
        f3, f8 = vec[..., _I["f3"]], vec[..., _I["f8"]]
        return 1.5 * (f3 + np.sqrt(3) * f8), 0.9 * (f3 - f8 / np.sqrt(3))
    g3, g8 = vec[..., _I["g3"]], vec[..., _I["g8"]]
    return -1.5 * (g3 + np.sqrt(3) * g8), 0.9 * (g3 - g8 / np.sqrt(3))


def moments(args):
    c, par = cfg()
    ev = _load(args, c)
    model = MassiveModel(*par["quadrature"])
    mp = par["moments"]
    species = {k: tuple(v) for k, v in mp["species"].items()}
    edges = np.array(mp["mass_edges"], dtype=float)
    off_p = ev.good & (ev.m_Wp < ev.m_Wm)
    off_m = ev.good & (ev.m_Wm < ev.m_Wp)
    partner_ok = mp["partners"]
    out = {"edges": edges.tolist(), "groups": {}}
    for sp, codes in species.items():
        for leg, off in (("p", off_p), ("m", off_m)):
            ana = np.abs(getattr(ev, f"pdg_ana_{leg}"))
            sel0 = off & np.isin(ana, codes)
            if sp in partner_ok:
                sel0 &= np.abs(getattr(ev, f"pdg_partner_{leg}")) == partner_ok[sp]
            theta = getattr(ev, f"theta_{leg}")
            mw = getattr(ev, f"m_W{leg}")
            rows = []
            for lo, hi in zip(edges[:-1], edges[1:]):
                sel = np.flatnonzero(sel0 & (mw >= lo) & (mw < hi))
                if len(sel) < mp["min_events"]:
                    continue
                cth = np.cos(theta[sel])
                p2 = 0.5 * (3 * cth ** 2 - 1)
                pred_cos, pred_p2, mass_cos, mass_p2 = 0.0, 0.0, 0.0, 0.0
                for start in range(0, len(sel), 20_000):
                    sl = sel[start:start + 20_000]
                    s0 = sm_vectors(ev.kappa[sl])
                    mf = [ev.m_f[k][sl] for k in FERMION_SLOTS]
                    sm_ = model.expect(ev.m_H[sl], ev.m_Wp[sl], ev.m_Wm[sl], *mf)
                    a0, b0 = _leg_moments(s0, leg)
                    a1, b1 = _leg_moments(sm_, leg)
                    pred_cos += a0.sum()
                    pred_p2 += b0.sum()
                    mass_cos += a1.sum()
                    mass_p2 += b1.sum()
                n = len(sel)
                rows.append({"lo": lo, "hi": hi, "n": n, "mean_mass": float(mw[sel].mean()),
                             "cos": float(cth.mean()), "cos_err": float(cth.std(ddof=1) / np.sqrt(n)),
                             "p2": float(p2.mean()), "p2_err": float(p2.std(ddof=1) / np.sqrt(n)),
                             "cos_massless": pred_cos / n, "p2_massless": pred_p2 / n,
                             "cos_massive": mass_cos / n, "p2_massive": mass_p2 / n})
            out["groups"][f"{sp}_{'Wplus' if leg == 'p' else 'Wminus'}"] = rows
            for r in rows:
                print(f"{sp:10s} W{'+' if leg == 'p' else '-'} M*[{r['lo']:4.0f},{r['hi']:4.0f}) N={r['n']:7d} "
                      f"<cos>={r['cos']:+.4f}+-{r['cos_err']:.4f} (massless {r['cos_massless']:+.4f}, "
                      f"massive {r['cos_massive']:+.4f}) <P2>={r['p2']:+.4f}+-{r['p2_err']:.4f} "
                      f"(massless {r['p2_massless']:+.4f}, massive {r['p2_massive']:+.4f})")
    # combined fit per species of the mass-effect strength from the two single-leg moments
    for sp in species:
        num = den = 0.0
        chi0 = chi1 = 0.0
        for leg in ("Wplus", "Wminus"):
            for r in out["groups"].get(f"{sp}_{leg}", []):
                for k in ("cos", "p2"):
                    d = r[f"{k}_massive"] - r[f"{k}_massless"]
                    res = r[k] - r[f"{k}_massless"]
                    w = 1 / r[f"{k}_err"] ** 2
                    num += w * d * res
                    den += w * d * d
                    chi0 += w * res ** 2
                    chi1 += w * (res - d) ** 2
        ndf = 2 * sum(len(out["groups"].get(f"{sp}_{lg}", [])) for lg in ("Wplus", "Wminus"))
        out.setdefault("mu", {})[sp] = {"mu": num / den if den else np.nan, "mu_err": den ** -0.5 if den else np.inf,
                                        "chi2_massless": chi0, "chi2_massive": chi1, "ndf": ndf}
        m = out["mu"][sp]
        print(f"{sp:10s} single-leg moments: mu = {m['mu']:+.3f} +- {m['mu_err']:.3f}; "
              f"chi2 massless {m['chi2_massless']:.1f}, massive {m['chi2_massive']:.1f} (ndf {m['ndf']})")
    # imaginary (CP-odd-interference / absorptive) rotation-invariant directions in independent sets
    rot, rot_re = basis.subspace("rotation_invariant"), basis.subspace("rotation_invariant_real")
    imag = rot - rot_re @ (rot_re.T @ rot)
    u, sv, _ = np.linalg.svd(imag, full_matrices=False)
    imag = u[:, sv > 1e-8]
    masks = ev.masks()
    out["imaginary_subspace_dim"] = int(imag.shape[1])
    out["imaginary"] = {}
    for name in mp["imaginary_sets"]:
        fit = Fit.of(ev, masks[name])
        chi = stats.chi_square(imag.T @ fit.resid, imag.T @ fit.cov @ imag)
        h45, h54 = basis.COEFF_LABELS.index("h45"), basis.COEFF_LABELS.index("h54")
        v = np.zeros(basis.N_COEFF)
        v[h45], v[h54] = 1.0, -1.0
        im, im_err = float(v @ fit.resid), float(np.sqrt(v @ fit.cov @ v))
        out["imaginary"][name] = {"chi2": chi[0], "ndf": chi[1], "p": chi[2], "h45_minus_h54": im, "err": im_err}
        print(f"imaginary subspace {name:16s} chi2 = {chi[0]:5.1f}/{chi[1]} p = {chi[2]:.3f}; "
              f"h45 - h54 = {im:+.5f} +- {im_err:.5f}")
    _dump(_outdir(args, c) / "validation_moments.json", out)


# --------------------------------------------------------------------------
# Figures
# --------------------------------------------------------------------------
COLORS = {"decohered": "tab:blue", "isotropic": "tab:orange", "cp_odd": "tab:green"}


def plot(args):
    import matplotlib.pyplot as plt
    c, par = cfg()
    out = _outdir(args, c)
    figdir = Path(c["figure_dir"])
    cal = json.loads((out / "validation_calibration.json").read_text())
    sen = json.loads((out / "validation_sensitivity.json").read_text())
    sub = json.loads((out / "validation_subsets.json").read_text())

    # 1. calibration of the chi^2 test
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.3))
    main, fine = cal["splits"]["main"], cal["splits"]["fine"]
    ax = axes[0]
    for key, lab, col in (("full", "80 coefficients", "tab:blue"), ("rot", "18 rotation-invariant", "tab:red")):
        pv = np.sort(main["summary"][key]["p_values"])
        ax.step(np.concatenate([[0], pv, [1]]), np.concatenate([[0], np.arange(1, len(pv) + 1) / len(pv), [1]]),
                where="post", color=col, label=f"{lab} (KS p = {main['summary'][key]['ks_p']:.2f})")
    ax.plot([0, 1], [0, 1], "k:", lw=1, label="uniform")
    ax.set_xlabel(f"$\\chi^2$ p-value of a subsample ({main['n_subsamples']} x {main['events_per_subsample']} events)")
    ax.set_ylabel("cumulative fraction of subsamples")
    ax.legend(fontsize=7, loc="upper left")
    plotting.add_label(ax, kind="mc", title=True)
    ax = axes[1]
    edges = np.linspace(0, 1, 11)
    for key, lab, col in (("full", "80 coefficients", "tab:blue"), ("rot", "18 rotation-invariant", "tab:red")):
        pv = fine["summary"][key]["p_values"]
        ax.hist(pv, bins=edges, histtype="step", color=col, lw=1.5,
                label=f"{lab} (KS p = {fine['summary'][key]['ks_p']:.2f})")
    ax.axhline(fine["n_subsamples"] / 10, color="k", ls=":", lw=1, label="uniform")
    ax.set_xlabel(f"$\\chi^2$ p-value of a subsample ({fine['n_subsamples']} x {fine['events_per_subsample']} events)")
    ax.set_ylabel("subsamples / 0.1")
    ax.set_ylim(0, fine["n_subsamples"] / 10 * 2.2)
    ax.legend(fontsize=7, loc="upper left")
    ax = axes[2]
    w = np.array(fine["summary"]["whitened_full"]["values"])
    xs = np.linspace(-4.5, 4.5, 37)
    wf = fine["summary"]["whitened_full"]
    ax.hist(w, bins=xs, histtype="step", color="tab:blue", lw=1.5,
            label=f"whitened residuals, {len(w)} values\n(std {w.std(ddof=1):.3f} $\\pm$ "
                  f"{wf['std_err']:.3f}, KS p = {wf['ks_p']:.2f})")
    xx = np.linspace(-4.5, 4.5, 400)
    ax.plot(xx, len(w) * (xs[1] - xs[0]) * st.norm.pdf(xx), "k:", lw=1, label="N(0, 1)")
    ax.set_yscale("log")
    ax.set_ylim(0.5, len(w) * 3.0)
    ax.set_xlabel("whitened residual component")
    ax.set_ylabel("components / 0.25")
    ax.legend(fontsize=7, loc="upper left")
    plotting.save(fig, figdir / "validation_calibration")

    # 2. Fisher reach per M* bin
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.3))
    sets = sen["sets"]
    bins = [k for k in sets if k != "inclusive"]
    centres = np.array([np.mean([float(x) for x in b.split("-")]) for b in bins])
    halfw = np.array([np.diff([float(x) for x in b.split("-")])[0] / 2 for b in bins])
    ax = axes[0]
    alts = alternatives(par)
    for a in alts:
        f95 = [sets[b]["alt"][a]["eps95_fisher"] for b in bins]
        om = [sets[b]["alt"][a][_omni_key(80, par["alpha"])] for b in bins]
        ax.errorbar(centres, f95, xerr=halfw, fmt="o", color=COLORS[a], label=ALT_LABELS[a])
        ax.plot(centres, om, "s", mfc="none", color=COLORS[a])
        inc = sets["inclusive"]["alt"][a]
        ax.axhline(inc["eps95_fisher"], color=COLORS[a], lw=0.8, ls="--")
    ax.plot([], [], "ko", label=f"one-parameter fit ($\\Delta\\chi^2$ = {par['fisher_delta_chi2']:g})")
    ax.plot([], [], "ks", mfc="none", label=f"80-coefficient $\\chi^2$ test, median at p = {par['alpha']:g}")
    ax.plot([], [], "k--", lw=0.8, label="inclusive $M^*$, one-parameter fit")
    ax.set_yscale("log")
    ax.set_ylim(1e-3, 0.08)
    ax.set_xlabel("$M^* = \\min(m_{W^+}, m_{W^-})$ [GeV]")
    ax.set_ylabel("admixture $\\epsilon$ detectable at 95% CL")
    ax.legend(fontsize=6.5, loc="upper right", ncol=1)
    plotting.add_label(ax, kind="mc", title=True)
    ax = axes[1]
    for key, lab, mk in (("i3_err", "$\\sigma(I_3)$ (fixed settings)", "o"), ("c2_err", "$\\sigma(\\mathcal{C}_2)$", "s"),
                         ("h44_err", "$\\sigma(h_{44})$", "^")):
        ax.errorbar(centres, [sets[b][key] for b in bins], xerr=halfw, fmt=mk, label=lab)
    ax.set_yscale("log")
    ax.set_xlabel("$M^* = \\min(m_{W^+}, m_{W^-})$ [GeV]")
    ax.set_ylabel("statistical uncertainty of the truth measurement")
    ax.legend(fontsize=7)
    plotting.save(fig, figdir / "validation_sensitivity")

    # 3. injection tests
    inj = sen["injection"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.3), sharey=True)
    crit05, crit001 = st.chi2.isf(0.05, 80), st.chi2.isf(c["p_value_threshold"], 80)
    for ax, a in zip(axes, alts):
        scan = inj[a]["scan"]
        eps = np.array([r["eps"] for r in scan])
        grid = np.linspace(0, eps.max() * 1.05, 200)
        f = inj[a]["fisher_info"]
        lam = grid ** 2 * f
        ax.fill_between(grid, st.ncx2.ppf(0.16, 80, lam), st.ncx2.ppf(0.84, 80, lam), color="0.85",
                        label="expected, new sample (68%)")
        ax.plot(grid, 80 + lam, color="0.5", lw=1)
        e0 = inj[a]["eps_hat0"]
        chi0 = cal["full_sample"]["chi2"][0]
        # (r0 + eps d)^T C^-1 (r0 + eps d) = chi2_0 + 2 eps F eps_hat_0 + eps^2 F for the same events
        ax.plot(grid, chi0 + 2 * grid * f * e0 + grid ** 2 * f, "k-", lw=1,
                label="expected, this sample (shared fluctuation)")
        ax.plot(eps, [r["chi2_reweight"] for r in scan], "o", color=COLORS[a], label="reweighted truth (qtomo.reweight)")
        ax.plot(eps, [r["chi2_replace"] for r in scan], "s", mfc="none", color=COLORS[a],
                label="replacement by toy decays (unit weights)")
        ax.axhline(crit05, color="tab:red", ls=":", lw=1)
        ax.axhline(crit001, color="tab:red", ls="--", lw=1)
        ax.axvline(inj[a]["eps_main"], color=COLORS[a], ls=":", lw=1)
        ax.set_xlabel("injected admixture $\\epsilon$")
        ax.text(0.97, 0.06, f"alternative: {ALT_LABELS[a]}", transform=ax.transAxes, ha="right", fontsize=8)
    axes[0].set_ylabel("$\\chi^2$ of the 80 coefficients vs SM (ndf = 80)")
    axes[0].legend(fontsize=6.5, loc="upper left")
    axes[0].text(0.97, 0.13, f"red: p = 0.05 (dotted), {c['p_value_threshold']:g} (dashed)",
                 transform=axes[0].transAxes, ha="right", fontsize=7)
    plotting.add_label(axes[0], kind="mc", title=True)
    plotting.save(fig, figdir / "validation_injection")

    # 4. ratio-weight tails
    fig, ax = plt.subplots(figsize=(6.2, 4.3))
    for a in alts:
        rw = inj[a]["ratio_weights"]
        tw, cc = np.array(rw["tail_W"]), np.array(rw["tail_ccdf"])
        ok = cc > 0
        ax.loglog(tw[ok], cc[ok], "-", color=COLORS[a], label=f"{ALT_LABELS[a]} (slope {rw['tail_slope']:.2f})")
    ref = np.logspace(1, 4, 10)
    ax.loglog(ref, 0.3 * ref ** -2.0, "k:", lw=1, label="$\\propto W^{-2}$")
    ax.set_xlabel("ratio weight $W = \\mathrm{Tr}[\\rho_{alt}\\Pi\\Pi] / \\mathrm{Tr}[\\rho_{SM}(\\varkappa_i)\\Pi\\Pi]$")
    ax.set_ylabel("fraction of events with $R > W$")
    ax.set_xlim(0.1, 1e4)
    ax.set_ylim(1e-7, 2.0)
    ax.legend(fontsize=7)
    plotting.add_label(ax, kind="mc", title=True)
    plotting.save(fig, figdir / "validation_weights")

    # 5. subset consistency
    fig, axes = plt.subplots(1, 3, figsize=(17, 6), gridspec_kw={"width_ratios": [1.15, 1.0, 0.8]})
    names = [n for n in par["subsets"] if "inclusive" in sub["sets"].get(n, {})]
    ax = axes[0]
    y = np.arange(len(names))[::-1]
    for key, lab, mk, col in (("p", "80 coefficients", "o", "tab:blue"), ("p_rot", "18 rotation-invariant", "s", "tab:red")):
        ax.plot([sub["sets"][n]["inclusive"][key] for n in names], y, mk, color=col, mfc="none" if mk == "s" else col,
                label=lab)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{n} ({sub['sets'][n]['inclusive']['n_events'] / 1e3:.0f}k)" for n in names], fontsize=7)
    ax.set_xscale("log")
    ax.set_xlim(1e-3, 1.2)
    ax.axvline(0.05, color="0.6", ls=":", lw=1)
    ax.axvline(c["p_value_threshold"], color="0.6", ls="--", lw=1)
    ax.set_xlabel("$\\chi^2$ p-value against the own per-event SM prediction")
    ax.legend(fontsize=7, loc="lower left")
    plotting.add_label(ax, kind="mc", title=True)
    ax = axes[1]
    pairs = list(sub["pairs"])
    yy = np.arange(len(pairs))[::-1]
    ax.plot([sub["pairs"][pr]["inclusive"]["p"] for pr in pairs], yy, "o", color="tab:blue", label="80 coefficients")
    ax.plot([sub["pairs"][pr]["inclusive"]["p_rot"] for pr in pairs], yy, "s", mfc="none", color="tab:red",
            label="18 rotation-invariant")
    ax.set_yticks(yy)
    ax.set_yticklabels([pr.replace("|", "\nvs ") for pr in pairs], fontsize=6.5)
    ax.set_xscale("log")
    ax.set_xlim(1e-3, 1.2)
    ax.axvline(0.05, color="0.6", ls=":", lw=1)
    ax.set_xlabel("$\\chi^2$ p-value of the difference of residuals")
    ax.set_title("pairwise, inclusive in $M^*$", fontsize=8, loc="right")
    ax.legend(fontsize=7, loc="lower left")
    ax = axes[2]
    p_sets = [x[k] for n, d in sub["sets"].items() if n not in ("lvqq_emu", "all_decays")
              for b, x in d.items() if b != "inclusive" for k in ("p", "p_rot")]
    p_pairs = [x[k] for d in sub["pairs"].values() for b, x in d.items() if b != "inclusive" for k in ("p", "p_rot")]
    edges = np.linspace(0, 1, 11)
    ax.hist([p_sets, p_pairs], bins=edges, stacked=True, color=["tab:blue", "tab:orange"],
            label=[f"subsets x $M^*$ bins ({len(p_sets)})", f"pairs x $M^*$ bins ({len(p_pairs)})"])
    ax.axhline((len(p_sets) + len(p_pairs)) / 10, color="k", ls=":", lw=1, label="uniform")
    ax.set_xlabel("$\\chi^2$ p-value (all $M^*$ bins, 80 and 18 coefficients)")
    ax.set_ylabel("tests / 0.1")
    ax.legend(fontsize=7, loc="lower right")
    plotting.save(fig, figdir / "validation_subsets")

    # 6. fermion-mass effects: analytic analysing powers and the direct single-W moments
    mom = json.loads((out / "validation_moments.json").read_text())
    from matplotlib.ticker import FixedLocator, NullFormatter, ScalarFormatter
    fig, axes = plt.subplots(1, 3, figsize=(18, 4.8))
    fig.subplots_adjust(wspace=0.32)
    ax = axes[0]
    for lab, col in (("tau nu", "tab:purple"), ("s cbar", "tab:brown"), ("d ubar", "tab:gray"), ("mu nu", "tab:cyan")):
        rows = sub["analytic_analysing_power"][lab]
        m = [r["M"] for r in rows]
        ax.plot(m, [r["tensor_ratio_exact"] for r in rows], "o-", color=col, label=f"W $\\to$ {lab}: exact tree level")
        ax.plot(m, [r["tensor_ratio_first_order"] for r in rows], "--", color=col, lw=1)
    ax.plot([], [], "k--", lw=1, label="first order in $m_f^2/M^2$")
    ax.set_xscale("log")
    ax.set_xlabel("mass $M$ of the decaying W [GeV]")
    ax.set_ylabel("tensor analysing power / massless value")
    ax.legend(fontsize=7, loc="lower right")
    plotting.add_label(ax, kind="mc", title=True)
    species = (("tau", "$\\tau$", "tab:purple"), ("s_from_cs", "s (W $\\to cs$)", "tab:brown"),
               ("e_mu", "e, $\\mu$", "tab:cyan"), ("d_from_ud", "d (W $\\to ud$)", "tab:gray"))
    for ax, key in ((axes[1], "cos"), (axes[2], "p2")):
        for k, (sp, lab, col) in enumerate(species):
            g_p, g_m = mom["groups"][f"{sp}_Wplus"], mom["groups"][f"{sp}_Wminus"]
            xs, ys, es, ms = [], [], [], []
            for rp, rm in zip(g_p, g_m):
                vals = []
                for r, sign in ((rp, -1.0), (rm, 1.0)):
                    if key == "cos":       # sign-adjusted so that W+ and W- legs add up
                        vals.append((sign * r["cos"], r["cos_err"], sign * r["cos_massive"]))
                    else:                  # relative change of the tensor moment
                        vals.append((r["p2"] / r["p2_massless"] - 1, r["p2_err"] / abs(r["p2_massless"]),
                                     r["p2_massive"] / r["p2_massless"] - 1))
                w = np.array([1 / v[1] ** 2 for v in vals])
                ys.append(np.sum(w * [v[0] for v in vals]) / w.sum())
                es.append(w.sum() ** -0.5)
                ms.append(np.mean([v[2] for v in vals]))
                xs.append(0.5 * (rp["mean_mass"] + rm["mean_mass"]))
            xs = np.array(xs) * (1 + 0.012 * (k - 1.5))
            mu = mom["mu"][sp]
            ax.errorbar(xs, ys, es, fmt="o", ms=4, color=col,
                        label=f"{lab}: $\\mu$ = {mu['mu']:+.2f} $\\pm$ {mu['mu_err']:.2f}" if sp in ("tau", "s_from_cs")
                        else f"{lab}")
            if sp in ("tau", "s_from_cs"):
                ax.plot(xs, ms, "-", color=col, lw=1.2)
        ax.axhline(0, color="k", lw=0.8)
        ax.set_xscale("log")
        ax.set_xlabel("mean mass of the off-shell W in the bin [GeV]")
    axes[1].plot([], [], "k-", lw=1.2, label="exact tree level, massive fermions")
    axes[1].set_ylabel("$\\langle\\cos\\theta\\rangle$ of the W* analyser (sign flipped for W$^+$)")
    axes[2].set_ylabel("$\\langle P_2(\\cos\\theta)\\rangle$ / massless SM $-$ 1")
    axes[2].plot([], [], "k-", lw=1.2, label="exact tree level, massive fermions")
    for ax, ticks in ((axes[0], [12, 15, 20, 30, 40, 60, 80]), (axes[1], [12, 15, 20, 30, 40, 50]),
                      (axes[2], [12, 15, 20, 30, 40, 50])):
        ax.xaxis.set_major_locator(FixedLocator(ticks))
        ax.xaxis.set_major_formatter(ScalarFormatter())
        ax.xaxis.set_minor_formatter(NullFormatter())
    axes[1].legend(fontsize=7, loc="upper right")
    axes[2].legend(fontsize=7, loc="lower right")
    plotting.save(fig, figdir / "validation_mass_effects")
    print(f"figures in {figdir}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("prepare", "calibration", "sensitivity", "subsets", "moments", "plot", "all",
                                    "check"))
    ap.add_argument("--out", default=None, help="results directory (default <output_dir>/validation)")
    args = ap.parse_args()
    cmds = {"prepare": prepare, "check": check, "calibration": calibration, "sensitivity": sensitivity,
            "subsets": subsets, "moments": moments, "plot": plot}
    if args.cmd == "all":
        for name in ("calibration", "sensitivity", "subsets", "moments", "plot"):
            cmds[name](args)
        return
    cmds[args.cmd](args)


def check(args):
    """Reproduce the chi^2 of phase1_truth.py (l nu q q: 88.3/80; all decays: 72.5/80) and test
    ``MassiveModel``: massless limit, quadrature order, explicit accept-reject four-vectors."""
    c, par = cfg()
    ev = _load(args, c)
    m = ev.masks()
    print("mass table (GeV):", ev.mass_table)
    for name in ("lvqq_emu", "all_decays"):
        fit = Fit.of(ev, m[name])
        print(name, fit.n, "chi2", fit.chi2(), "rot", fit.chi2(sub="rot"), "cond", fit.chi2(cov=fit.cov_cond))
    rng = np.random.default_rng(par["seed"])
    n = 2000
    m1 = rng.uniform(12.0, 100.0, n)
    m2 = rng.uniform(12.0, 125.0 - m1 - 0.1)
    mh, zero = np.full(n, 125.0), np.zeros(n)
    ref = sm_vectors(sm.kappa(mh, m1, m2))
    model = MassiveModel(*par["quadrature"])
    dev0 = np.abs(model.expect(mh, m1, m2, zero, zero, zero, zero) - ref).max()
    mt = np.full(n, ev.mass_table[15])
    a = model.expect(mh, m1, m2, mt, zero, 0.5 * mt, mt)
    b = MassiveModel(7, 14).expect(mh, m1, m2, mt, zero, 0.5 * mt, mt)
    print(f"MassiveModel: massless limit max|dev| = {dev0:.2e}; quadrature (4,6) vs (7,14) max|dev| = "
          f"{np.abs(a - b).max():.2e}")
    # explicit four-vectors: W+ (70 GeV) -> massless pair, W- (13 GeV) -> tau nu, accept-reject on the weight
    big, mp, mm, mtau = 2_000_000, 70.0, 13.0, ev.mass_table[15]

    def unit(k):
        ct, ph = rng.uniform(-1, 1, k), rng.uniform(0, 2 * np.pi, k)
        st_ = np.sqrt(1 - ct * ct)
        return np.stack([st_ * np.cos(ph), st_ * np.sin(ph), ct], -1)
    e_p = (125.0 ** 2 + mp ** 2 - mm ** 2) / 250.0
    p_w = np.sqrt(sm.kallen(125.0 ** 2, mp ** 2, mm ** 2)) / 250.0
    one = lambda v: np.full(1, v)       # noqa: E731
    model1 = MassiveModel(1, 1)
    four = {}
    for tag, mw, ma, mb, ew, sign in (("p", mp, 0.0, 0.0, e_p, 1.0), ("m", mm, mtau, 0.0, 125.0 - e_p, -1.0)):
        model1.u = unit(big)
        ana, par_ = model1._leg(one(mw), one(ma), one(mb), one(ew), one(p_w), sign)
        four[tag] = (ana[0], par_[0])
    dot = lambda x, y: x[:, 0] * y[:, 0] - np.sum(x[:, 1:] * y[:, 1:], axis=1)     # noqa: E731
    w = dot(four["p"][1], four["m"][0]) * dot(four["m"][1], four["p"][0])
    keep = rng.uniform(0, w.max() * 1.0001, big) < w
    wp, wm = four["p"][0] + four["p"][1], four["m"][0] + four["m"][1]
    beam = np.array([120.0, 0.0, 120.0 * np.sin(0.7), 120.0 * np.cos(0.7)])
    ang = frames.decay_angles((wp + wm)[keep], wp[keep], wm[keep], four["p"][0][keep], four["m"][0][keep], beam)
    x = basis.estimator_vector(ang["theta_p"], ang["phi_p"], ang["theta_m"], ang["phi_m"])
    mc, err = x.mean(0), x.std(0) / np.sqrt(len(x))
    exp = model.expect(one(125.0), one(mp), one(mm), one(0.0), one(0.0), one(mtau), one(0.0))[0]
    ml = sm_vectors(sm.kappa(125.0, mp, mm))
    print(f"explicit four-vectors ({keep.sum()} events): sum pull^2 vs MassiveModel {np.sum(((mc - exp) / err) ** 2):.1f}"
          f", vs massless SM {np.sum(((mc - ml) / err) ** 2):.1f} (80 coefficients)")


if __name__ == "__main__":
    main()
