"""Phase 0 task 3: ideal statistical reach (PLAN.md Sec. 4).

State: the tree-level SM averaged over the W* mass spectrum (qtomo.sm.OffShellSpectrum);
for angle-only observables, sampling the averaged state is exactly equivalent to sampling
kappa per event.  Perfect analysers, except for a down/up-type mistag rate w on the
hadronic legs of each category (config/phase0.yaml); the estimators are corrected for w
(rank-1 terms rescaled by 1/(1-2w)), which is impossible at w = 1/2, where only rank-(2,2)
quantities such as h44 remain measurable.

    python analysis/phase0_reach.py asymptotic          # exact sigmas from the per-event covariance
    python analysis/phase0_reach.py run --category A --w 0.1 --first 0 --count 3   # local test
    python analysis/phase0_reach.py submit [--dry-run]  # pseudo-experiments on HTCondor
    python analysis/phase0_reach.py summarise
    python analysis/phase0_reach.py plot
"""
import argparse
import json
from pathlib import Path

import numpy as np

import batch
import phase0_common as pc
from qtomo import basis, bell, config, plotting, stats, tomography, toy

STUDY = 2


def categories(cfg):
    """{name: (index, entry, expected yield)} with yield = N(H -> WW* mode) x BR(Z mode)."""
    rc = cfg["reach"]
    out = {}
    for i, (name, e) in enumerate(rc["categories"].items()):
        out[name] = (i, e, int(round(rc["yields_hww"][e["hww"]] * rc["z_branching"][e["z"]])))
    return out


def _measurable(entry, w):
    """Rank-1 information (hence I3, C2) survives unless a hadronic leg has w = 1/2."""
    return entry["hadronic"] == "none" or abs(1.0 - 2.0 * w) > 1e-12


def expected_moments(rho, entry, w):
    """Exact per-event mean and covariance of the estimator vector for a category: one
    hadronic leg (W+ or W- with equal probability), both legs, or none.  At w = 1/2 the
    estimators are left uncorrected (mean = diluted coefficients)."""
    corr = w if _measurable(entry, w) else 0.0
    had = entry["hadronic"]
    if had == "none":
        return tomography.expected_moments(rho)
    if had == "both":
        return tomography.expected_moments(rho, w, w, correct_p=corr, correct_m=corr)
    m1, c1 = tomography.expected_moments(rho, w, 0.0, correct_p=corr, correct_m=0.0)
    m2, c2 = tomography.expected_moments(rho, 0.0, w, correct_p=0.0, correct_m=corr)
    mean = 0.5 * (m1 + m2)
    second = 0.5 * (c1 + np.outer(m1, m1) + c2 + np.outer(m2, m2))
    return mean, second - np.outer(mean, mean)


def asymptotic_sigmas(rho, ref, entry, w, n_events):
    """sigma(I3) from the linearisation at the optimal settings of the true state (envelope
    theorem), sigma(C2) = 2 sigma(unbiased C2 argument) (Hoeffding, exact for the argument),
    sigma(h44); NaN where rank-1 information is lost."""
    mean, cov = expected_moments(rho, entry, w)
    s_h44 = float(np.sqrt(cov[pc.H44, pc.H44] / n_events))
    if not _measurable(entry, w):
        return {"i3": np.nan, "c2": np.nan, "h44": s_h44}
    g = bell.i3_weights(ref["i3_result"].u, ref["i3_result"].v)
    inv = tomography.expected_invariant_sigma(mean, cov, n_events)
    return {"i3": float(np.sqrt(g @ cov @ g / n_events)),
            "c2": 2.0 * max(inv.c2_arg_wplus, inv.c2_arg_wminus), "h44": s_h44}


def asymptotic(args):
    cfg = pc.cfg()
    rc = cfg["reach"]
    spec = pc.spectrum()
    rho = pc.state({"kind": "sm_spectrum"}, spec=spec)
    ref = pc.reference(rho, cfg["i3"]["n_starts_reference"])
    rows = []
    for name, (_, entry, n) in categories(cfg).items():
        for w in (rc["mistag_rates"] if entry["hadronic"] != "none" else [0.0]):
            rows.append({"category": name, "n_events": n, "w": w, **{f"sigma_{k}": v for k, v in
                         asymptotic_sigmas(rho, ref, entry, w, n).items()}})
    scan = []
    for cut in rc["mstar_cuts"]:
        rho_c, frac = spec.average_density_matrix((cut, np.inf))
        ref_c = pc.reference(rho_c, cfg["i3"]["n_starts_reference"])
        for name, (_, entry, n) in categories(cfg).items():
            n_c = n * frac
            for w in sorted({0.0, 0.3} if entry["hadronic"] != "none" else {0.0}):
                s = asymptotic_sigmas(rho_c, ref_c, entry, w, n_c)
                scan.append({"mstar_min": cut, "fraction": frac, "category": name, "w": w,
                             "n_events": n_c, "i3": ref_c["i3"], "c2": ref_c["c2"], "h44": ref_c["h44"],
                             **{f"sigma_{k}": v for k, v in s.items()}})
    out = {"state": "SM averaged over the W* spectrum",
           "truth": {"i3": ref["i3"], "c2": ref["c2"], "h44": ref["h44"],
                     "c": ref["c"].tolist()}, "rows": rows, "mstar_scan": scan}
    path = config.resolve(cfg["output_dir"]) / "reach_asymptotic.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=1))
    print(f"truth: I3 = {ref['i3']:.4f}, C2 = {ref['c2']:.4f}, h44 = {ref['h44']:.4f}")
    for r in rows:
        print(f"{r['category']:5s} N = {r['n_events']:6d} w = {r['w']:.1f}: sigma(I3) = {r['sigma_i3']:.4f}"
              f"  sigma(C2) = {r['sigma_c2']:.4f}  sigma(h44) = {r['sigma_h44']:.5f}")
    print(f"wrote {path}")


def _outdir(cfg):
    return config.resolve(cfg["output_dir"]) / "reach"


def run(args):
    cfg = pc.cfg()
    idx, entry, n = categories(cfg)[args.category]
    n = args.n or n            # --n: local tests on a small sample (PLAN.md rule 7)
    w = args.w
    rho = pc.state({"kind": "sm_spectrum"})
    ref = pc.reference(rho, cfg["i3"]["n_starts_reference"])
    measurable = _measurable(entry, w)
    if not measurable:          # uncorrected estimators: compare with the diluted coefficients
        ref = dict(ref, c=expected_moments(rho, entry, w)[0])
    corr = w if measurable else 0.0
    rng = np.random.default_rng(pc.seed_sequence(STUDY, idx, round(100 * w), args.first))
    rows = []
    for _ in range(args.count):
        tp, pp, tm, pm = toy.generate(rho, n, rng)
        had = entry["hadronic"]
        if had == "none":
            wp = wm = 0.0
        elif had == "both":
            wp = wm = w
        else:
            plus = rng.uniform(size=n) < 0.5           # W+ is the hadronic W
            wp, wm = np.where(plus, w, 0.0), np.where(plus, 0.0, w)
        if had != "none":
            tp, pp, _ = toy.apply_mistag(tp, pp, wp, rng)
            tm, pm, _ = toy.apply_mistag(tm, pm, wm, rng)
        cp = np.where(np.asarray(wp) > 0, corr, 0.0) if np.ndim(wp) else (corr if wp else 0.0)
        cm = np.where(np.asarray(wm) > 0, corr, 0.0) if np.ndim(wm) else (corr if wm else 0.0)
        res = tomography.estimate(tp, pp, tm, pm, mistag_p=cp, mistag_m=cm)
        rows.append(pc.evaluate(res, ref, cfg["i3"]["n_starts_toy"], rng, with_i3=measurable))
    out = Path(args.out) if args.out else _outdir(cfg) / f"{args.category}_w{w:.2f}_{args.first:04d}.npz"
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, **{f: np.array([r[f] for r in rows]) for f in pc.FIELDS})
    print(f"wrote {out} ({args.count} pseudo-experiments, N = {n}, w = {w})")


def submit(args):
    cfg = pc.cfg()
    rc = cfg["reach"]
    outdir = _outdir(cfg)
    cmds = []
    for name, (_, entry, _) in categories(cfg).items():
        for w in (rc["mistag_rates"] if entry["hadronic"] != "none" else [0.0]):
            for first in range(0, rc["n_pseudo"], rc["pseudo_per_job"]):
                out = outdir / f"{name}_w{w:.2f}_{first:04d}.npz"
                if not out.exists():
                    cmds.append(f"python analysis/phase0_reach.py run --category {name} --w {w} "
                                f"--first {first} --count {rc['pseudo_per_job']} --out {out}")
    sub = batch.write_jobs(outdir / "jobs", cmds, cfg["batch"])
    print(f"{len(cmds)} jobs written: {sub}")
    if cmds and not args.dry_run:
        print(batch.submit(sub))


def summarise(args):
    cfg = pc.cfg()
    asym = json.loads((config.resolve(cfg["output_dir"]) / "reach_asymptotic.json").read_text())
    truth = asym["truth"]
    rows = []
    for r in asym["rows"]:
        files = sorted(_outdir(cfg).glob(f"{r['category']}_w{r['w']:.2f}_*.npz"))
        if not files:
            continue
        d = {}
        for f in files:
            with np.load(f) as z:
                for k in z.files:
                    d.setdefault(k, []).append(z[k])
        d = {k: np.concatenate(v) for k, v in d.items()}
        row = dict(r, n_pseudo=int(len(d["h44"])))
        if not np.isfinite(r["sigma_i3"]):     # w = 1/2: uncorrected estimators, only rank-(2,2) is meaningful
            for key in ("c2", "c2_physical", "c2_unbiased", "c2_unbiased_arg"):
                d[key] = np.full_like(d[key], np.nan)
        for key, t in (("i3", truth["i3"]), ("i3_physical", truth["i3"]), ("c2_unbiased_arg", truth["c2"]),
                       ("c2_unbiased", truth["c2"]), ("c2_physical", truth["c2"]), ("h44", truth["h44"])):
            v = d[key][np.isfinite(d[key])]
            if v.size < 2:
                continue
            s = stats.summarise(v)
            row[key] = {"mean": float(s.mean), "bias": float(s.mean - t), "sigma": float(s.std),
                        "sigma_err": float(s.std / np.sqrt(2 * (s.n - 1))), "median": float(s.median),
                        "q16": float(s.q16), "q84": float(s.q84), "n": int(s.n)}
        if np.isfinite(d["i3"]).any():
            row["frac_i3_physical_gt2"] = float(np.mean(d["i3_physical"][np.isfinite(d["i3_physical"])] > 2))
        rows.append(row)
    path = config.resolve(cfg["output_dir"]) / "reach_summary.json"
    path.write_text(json.dumps({"truth": {k: truth[k] for k in ("i3", "c2", "h44")}, "rows": rows,
                                "mstar_scan": asym["mstar_scan"]}, indent=1))
    print(f"wrote {path} ({len(rows)} rows)")


def plot(args):
    import matplotlib.pyplot as plt
    cfg = pc.cfg()
    summ = json.loads((config.resolve(cfg["output_dir"]) / "reach_summary.json").read_text())
    figdir = Path(cfg["figure_dir"])
    cats = list(cfg["reach"]["categories"])
    for key, pe_keys, name in (("sigma_i3", ("i3", "i3_physical"), "$I_3$"),
                               ("sigma_c2", ("c2_unbiased_arg",), r"$\mathcal{C}_2$"),
                               ("sigma_h44", ("h44",), "$h_{44}$")):
        fig, ax = plt.subplots(figsize=(6.6, 4.6))
        for i, c in enumerate(cats):
            rows = [r for r in summ["rows"] if r["category"] == c]
            if not rows:
                continue
            w = np.array([r["w"] for r in rows])
            ax.plot(w, [r[key] for r in rows], "-", marker="_", ms=12, color=f"C{i}",
                    label=f"{c} (N = {rows[0]['n_events']})")
            for pe_key, fill in zip(pe_keys, ("full", "none")):
                pe = np.array([(r["w"], r[pe_key]["sigma"], r[pe_key]["sigma_err"]) for r in rows if pe_key in r])
                if len(pe):
                    ax.errorbar(pe[:, 0], pe[:, 1], pe[:, 2], fmt="o", ms=4, color=f"C{i}", fillstyle=fill)
        ax.set_yscale("log")
        ax.set_xlabel("down/up-type mistag rate $w$ on hadronic legs")
        ax.set_ylabel(rf"$\sigma$({name})")
        note = ("lines: asymptotic; filled: pseudo-exp. (raw); open: pseudo-exp. (physical)"
                if len(pe_keys) > 1 else "lines: asymptotic; points: pseudo-experiments")
        ax.legend(fontsize=7, title=note, title_fontsize=6.5, ncol=2)
        plotting.add_label(ax, title=True)
        plotting.save(fig, figdir / f"reach_{key}")
    print(f"figures in {figdir}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("asymptotic")
    r = sp.add_parser("run")
    r.add_argument("--category", required=True)
    r.add_argument("--w", type=float, default=0.0)
    r.add_argument("--first", type=int, default=0)
    r.add_argument("--count", type=int, default=1)
    r.add_argument("--n", type=int, default=0, help="override the category yield (local tests)")
    r.add_argument("--out")
    s = sp.add_parser("submit")
    s.add_argument("--dry-run", action="store_true")
    sp.add_parser("summarise")
    sp.add_parser("plot")
    args = ap.parse_args()
    {"asymptotic": asymptotic, "run": run, "submit": submit, "summarise": summarise, "plot": plot}[args.cmd](args)


if __name__ == "__main__":
    main()
