"""Phase 0 task 2: toy closure (PLAN.md Sec. 4).

For each state of ``closure.states`` (config/phase0.yaml) and each sample size N,
pseudo-experiments are generated with qtomo.toy, the 80 coefficients estimated with
qtomo.tomography, and I3 / C2 (raw and physical), the unbiased C2 and h44 evaluated.
The summary shows bias -> 0 and sigma ~ 1/sqrt(N).

    python analysis/phase0_closure.py run --state sm_m30 --n 1000 --first 0 --count 3   # local test
    python analysis/phase0_closure.py submit [--dry-run]                                 # HTCondor
    python analysis/phase0_closure.py summarise
    python analysis/phase0_closure.py plot
"""
import argparse
import json
from pathlib import Path

import numpy as np

import batch
import phase0_common as pc
from qtomo import basis, bell, config, plotting, stats, tomography, toy

STUDY = 1


def _states(cfg):
    return {s["name"]: (i, s) for i, s in enumerate(cfg["closure"]["states"])}


def _outdir(cfg):
    return config.resolve(cfg["output_dir"]) / "closure"


def run(args):
    cfg = pc.cfg()
    idx, entry = _states(cfg)[args.state]
    rho = pc.state(entry)
    ref = pc.reference(rho, cfg["i3"]["n_starts_reference"])
    n_starts = cfg["i3"]["n_starts_toy"]
    rng = np.random.default_rng(pc.seed_sequence(STUDY, idx, args.n, args.first))
    rows, cs, sigmas = [], [], []
    for _ in range(args.count):
        res = tomography.estimate(*toy.generate(rho, args.n, rng))
        rows.append(pc.evaluate(res, ref, n_starts, rng))
        cs.append(res.c)
        sigmas.append(res.sigma)
    out = Path(args.out) if args.out else _outdir(cfg) / f"{args.state}_N{args.n}_{args.first:04d}.npz"
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, c=np.array(cs), sigma=np.array(sigmas), c_true=ref["c"],
             truth=np.array([ref["i3"], ref["c2"], ref["h44"]]),
             **{f: np.array([r[f] for r in rows]) for f in pc.FIELDS})
    print(f"wrote {out} ({args.count} pseudo-experiments, N = {args.n})")


def submit(args):
    cfg = pc.cfg()
    cc = cfg["closure"]
    outdir = _outdir(cfg)
    cmds = []
    for name in _states(cfg):
        for n in cc["n_events"]:
            for first in range(0, cc["n_pseudo"], cc["pseudo_per_job"]):
                out = outdir / f"{name}_N{n}_{first:04d}.npz"
                if out.exists():
                    continue
                cmds.append(f"python analysis/phase0_closure.py run --state {name} --n {n} "
                            f"--first {first} --count {cc['pseudo_per_job']} --out {out}")
    sub = batch.write_jobs(outdir / "jobs", cmds, cfg["batch"])
    print(f"{len(cmds)} jobs written: {sub}")
    if cmds and not args.dry_run:
        print(batch.submit(sub))


def _load(cfg):
    data = {}
    for f in sorted(_outdir(cfg).glob("*_N*_*.npz")):
        name, n = f.stem.rsplit("_", 2)[0], int(f.stem.rsplit("_", 2)[1][1:])
        with np.load(f) as z:
            d = {k: z[k] for k in z.files}
        acc = data.setdefault((name, n), {k: [] for k in d})
        for k, v in d.items():
            acc[k].append(v)
    out = {}
    for key, acc in data.items():
        merged = {k: (np.concatenate(v) if np.ndim(v[0]) and k not in ("c_true", "truth") else v[0])
                  for k, v in acc.items()}
        out[key] = merged
    return out


def _bias_sigma(values, truth):
    v = values[np.isfinite(values)]
    s = stats.summarise(v)
    return {"bias": float(s.mean - truth), "bias_err": float(s.std / np.sqrt(s.n)),
            "sigma": float(s.std), "sigma_err": float(s.std / np.sqrt(2 * (s.n - 1))), "n": int(s.n)}


def summarise(args):
    cfg = pc.cfg()
    data = _load(cfg)
    summary = []
    for (name, n), d in sorted(data.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        i3_t, c2_t, h44_t = d["truth"]
        pulls = (d["c"] - d["c_true"]) / d["sigma"]
        row = {"state": name, "n_events": n, "n_pseudo": int(len(d["chi2"])),
               "i3_true": float(i3_t), "c2_true": float(c2_t), "h44_true": float(h44_t),
               "chi2_mean_over_ndf": float(np.mean(d["chi2"] / d["ndf"])),
               "pull_mean": float(np.mean(pulls)), "pull_width": float(np.std(pulls)),
               "frac_unphysical": float(np.mean(d["min_eigenvalue"] < 0))}
        # unclipped C2 argument 2 max(Tr rho^2 - Tr rho_A^2, Tr rho^2 - Tr rho_B^2) of the truth
        c2_arg_t = 2.0 * float(max(bell.c2_terms(basis.density_matrix_from_vector(d["c_true"]))))
        i3_unrot_t = float(np.dot(bell.i3_weights(), d["c_true"]))
        row.update(c2_arg_true=c2_arg_t, i3_unrotated_true=i3_unrot_t)
        for key, truth in (("i3", i3_t), ("i3_physical", i3_t), ("i3_unrotated", i3_unrot_t),
                           ("c2", c2_t), ("c2_physical", c2_t), ("c2_unbiased", c2_t),
                           ("c2_unbiased_arg", c2_arg_t), ("h44", h44_t)):
            row[key] = _bias_sigma(d[key], truth)
        summary.append(row)
    out = config.resolve(cfg["output_dir"]) / "closure_summary.json"
    out.write_text(json.dumps(summary, indent=1))
    print(f"wrote {out} ({len(summary)} (state, N) points)")


def plot(args):
    import matplotlib.pyplot as plt
    cfg = pc.cfg()
    summary = json.loads((config.resolve(cfg["output_dir"]) / "closure_summary.json").read_text())
    figdir = Path(cfg["figure_dir"])
    states = [s["name"] for s in cfg["closure"]["states"]]
    label = {"sm_m10": "SM, $M^*$ = 10 GeV", "sm_m20": "SM, $M^*$ = 20 GeV", "sm_m30": "SM, $M^*$ = 30 GeV",
             "sm_m40": "SM, $M^*$ = 40 GeV", "sm_spectrum": "SM, $M^*$ spectrum",
             "decohered_m30": "decohered SM, $M^*$ = 30 GeV", "isotropic": r"$\mathbb{1}/9$"}
    observables = (("i3", "$I_3$ (raw)"), ("i3_physical", "$I_3$ (physical)"), ("c2", r"$\mathcal{C}_2$ (raw)"),
                   ("c2_physical", r"$\mathcal{C}_2$ (physical)"), ("c2_unbiased_arg", r"$\mathcal{C}_2$ (unbiased, unclipped)"),
                   ("h44", "$h_{44}$"))
    for key, name in observables:
        fig, (ax_b, ax_s) = plt.subplots(1, 2, figsize=(11, 4.2))
        for st in states:
            rows = sorted((r for r in summary if r["state"] == st), key=lambda r: r["n_events"])
            if not rows:
                continue
            n = np.array([r["n_events"] for r in rows], dtype=float)
            ax_b.errorbar(n, [r[key]["bias"] for r in rows], [r[key]["bias_err"] for r in rows],
                          marker="o", ms=3, capsize=2, label=label.get(st, st))
            ax_s.errorbar(n, [r[key]["sigma"] * np.sqrt(r["n_events"]) for r in rows],
                          [r[key]["sigma_err"] * np.sqrt(r["n_events"]) for r in rows],
                          marker="o", ms=3, capsize=2, label=label.get(st, st))
        ax_b.axhline(0, color="k", lw=0.8)
        for ax in (ax_b, ax_s):
            ax.set_xscale("log")
            ax.set_xlabel("events per pseudo-experiment $N$")
        ax_b.set_ylabel(f"bias of {name}")
        ax_s.set_ylabel(rf"$\sigma\sqrt{{N}}$ of {name}")
        ax_s.legend(fontsize=7, loc="best")
        plotting.add_label(ax_b, title=True)
        plotting.save(fig, figdir / f"closure_{key}")
    print(f"figures in {figdir}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run")
    r.add_argument("--state", required=True)
    r.add_argument("--n", type=int, required=True)
    r.add_argument("--first", type=int, default=0)
    r.add_argument("--count", type=int, default=1)
    r.add_argument("--out")
    s = sp.add_parser("submit")
    s.add_argument("--dry-run", action="store_true")
    sp.add_parser("summarise")
    sp.add_parser("plot")
    args = ap.parse_args()
    {"run": run, "submit": submit, "summarise": summarise, "plot": plot}[args.cmd](args)


if __name__ == "__main__":
    main()
