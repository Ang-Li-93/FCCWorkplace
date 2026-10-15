#!/usr/bin/env python3
"""
Re-score the leptonic (Z->mumu / Z->ee) BDT of an EXISTING stage1 analysis stage
(BDT_analysis_samples*: the flat ntuples of stage1_analysis_ntuples.py) chunk by chunk,
without re-running stage1 over the EDM4hep samples.

Purpose (2026-10): quantify the effect of the acolinearity DEFINITION fed to the original
CERN-trained leptonic models. The models were trained (and stage1 scores them) with
    zll_leptons_acolinearity = |theta_1 - theta_2|          (HiggsTools::acolinearity)
whereas the FCCPhysics histmaker (J. Eysermans, functions.h), with which the paper's fits
were made, feeds the SAME models with
    acolinearity = acos( -(v1.v2)/(|v1||v2|) ) = pi - opening angle of the two leptons.
The second definition depends on the lepton DIRECTIONS only, so it is computed exactly
from the stored leading/subleading theta/phi (nominal, _scaleup, _scaledw).

For every <in-stage>/<process>/<chunk>.root the script writes <out-stage>/<process>/<chunk>.root
with
  - ALL original branches, in the original order, BDTscore / BDTscore_scaleup / BDTscore_scaledw
    REPLACED by the re-scored values (--acol jan: acol_jan in place of zll_leptons_acolinearity,
    every other input unchanged; --acol training: the stored training-definition variable, i.e.
    a pure re-scoring check that must reproduce the stored scores),
  - the original scores kept as BDTscore_orig / BDTscore_orig_scaleup / BDTscore_orig_scaledw,
  - acol_jan / acol_jan_scaleup / acol_jan_scaledw,
  - the TParameters of the input file (eventsProcessed, eventsSelected, ...) rewritten unchanged,
and copies tree-less chunks (TParameters only, zero selected events) byte for byte. The output
stage can then be used by stage2_histograms_syst.py (inputDir override) exactly like the input.

Scorer: the SAME one as stage1_analysis_ntuples.py - TMVA::Experimental::RBDT<> loaded from the
SaveXGBoost file + TMVA::Experimental::Compute<9, float> (jitted branchless forest), with the
TRAIN_VARS order of leptonic_training_config.py - so '--acol training' reproduces the stored
BDTscore bit for bit (verified: max |diff| = 0); the per-chunk report prints max|new - orig|
and the number of events differing by more than 1e-3 in any case.

Parallelism: --threads worker PROCESSES (multiprocessing 'spawn', one single-threaded ROOT each;
every worker jit-compiles the model once, ~7 s), so the entry order of every chunk is preserved.
Resumable: existing output chunks are skipped unless --overwrite.

Usage (key4hep 2024-03-10 + FCCAnalyses-winter2023 env):
  python3 rescore_leptonic.py --ecm 240 --flavor mumu --acol jan --threads 3 \
      --in-stage  $STORE/S240/mumu/BDT_analysis_samples_cernbdt \
      --out-stage $STORE/S240/mumu/BDT_analysis_samples_janacol [--model <xgb_bdt.root>] \
      [--procs 'wzp6_ee_*H_*'] [--max-chunks N] [--summary-json FILE]
"""
import argparse
import fnmatch
import glob
import json
import multiprocessing as mp
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from leptonic_training_config import TRAIN_VARS  # noqa: E402
from site_config import bdt_model, output_dir  # noqa: E402

ACOL_VAR = "zll_leptons_acolinearity"
SYSTS = ["", "_scaleup", "_scaledw"]
# extra branches appended after the original ones
EXTRA_BRANCHES = ([f"BDTscore_orig{s}" for s in SYSTS] + [f"acol_jan{s}" for s in SYSTS])
IN_STAGE_DEFAULT = "BDT_analysis_samples_cernbdt"

# C++ helpers declared in every worker: Jan's acolinearity from the two lepton directions
# (FCCPhysics functions.h: acos(v1.v2/(|v1||v2|) * (-1)); massless/direction-only, so the
# stored theta/phi determine it exactly), clamped against rounding at |cos| = 1.
CPP_HELPERS = r"""
float rescore_acol_jan(float t1, float p1, float t2, float p2) {
    double c = std::sin((double)t1) * std::sin((double)t2) * std::cos((double)p1 - (double)p2)
             + std::cos((double)t1) * std::cos((double)t2);
    if (c > 1.) c = 1.;
    if (c < -1.) c = -1.;
    return (float)std::acos(-c);
}
"""

_ROOT = None


def worker_init(model):
    """Spawned-process initializer: load ROOT, jit the RBDT model and the helpers once."""
    global _ROOT
    import ROOT
    ROOT.gROOT.SetBatch(True)
    ROOT.gErrorIgnoreLevel = ROOT.kWarning
    ROOT.gInterpreter.ProcessLine(
        f'TMVA::Experimental::RBDT<> rescore_bdt("ZH_Recoil_BDT", "{model}");'
        f'auto rescore_compute = TMVA::Experimental::Compute<{len(TRAIN_VARS)}, float>(rescore_bdt);')
    ROOT.gInterpreter.Declare(CPP_HELPERS)
    _ROOT = ROOT


def process_chunk(job):
    """Re-score one chunk (or copy it when tree-less). Returns a status dict."""
    fin, fout, acol = job["in"], job["out"], job["acol"]
    ROOT = _ROOT
    t0 = time.time()
    res = {"process": job["process"], "chunk": os.path.basename(fin), "in": fin, "out": fout}
    tmp = fout + ".part"
    try:
        f = ROOT.TFile.Open(fin)
        if not f or f.IsZombie():
            raise RuntimeError(f"cannot open {fin}")
        params = []
        for k in f.GetListOfKeys():
            cls = k.GetClassName()
            if cls.startswith("TParameter<"):
                obj = f.Get(k.GetName())
                params.append((k.GetName(), cls[len("TParameter<"):-1], obj.GetVal()))
        tree = f.Get("events")
        # tree-less chunk (TParameters only) or an 'events' tree with zero entries (the stage1 /
        # patch_empty_chunks.py convention for zero-selection chunks: full branch list, no entries;
        # a Snapshot of it would write a branch-less tree): copy the file byte for byte
        if not tree or tree.GetEntries() == 0:
            status = "treeless" if not tree else "empty"
            f.Close()
            shutil.copyfile(fin, tmp)
            os.rename(tmp, fout)
            res.update(status=status, entries=0, params=params, seconds=time.time() - t0)
            return res
        branches = [b.GetName() for b in tree.GetListOfBranches()]
        f.Close()
        missing = [v + s for s in SYSTS for v in TRAIN_VARS if v + s not in branches]
        if missing:
            raise RuntimeError(f"missing BDT input branches {missing}")
        for extra in EXTRA_BRANCHES:
            if extra in branches:
                raise RuntimeError(f"input already holds {extra} (re-scoring a re-scored stage is refused)")

        df = ROOT.RDataFrame("events", fin)
        idx_acol = TRAIN_VARS.index(ACOL_VAR)
        for s in SYSTS:
            df = df.Define(f"acol_jan{s}",
                           f"rescore_acol_jan(leading_zll_lepton_theta{s}, leading_zll_lepton_phi{s}, "
                           f"subleading_zll_lepton_theta{s}, subleading_zll_lepton_phi{s})")
            inputs = [v + s for v in TRAIN_VARS]
            if acol == "jan":
                inputs[idx_acol] = f"acol_jan{s}"
            df = df.Define(f"rescore_mva{s}", ROOT.rescore_compute, inputs)
            # keep the stored score, then replace the branch by the new one
            df = df.Define(f"BDTscore_orig{s}", f"BDTscore{s}")
            df = df.Redefine(f"BDTscore{s}", f"rescore_mva{s}.at(0)")
        df = df.Define("rescore_diff", "std::abs(BDTscore - BDTscore_orig)")
        n = df.Count()
        dmax = df.Max("rescore_diff")
        n_gt3 = df.Filter("rescore_diff > 1e-3").Count()
        n_gt0 = df.Filter("rescore_diff > 0").Count()
        df.Snapshot("events", tmp, branches + EXTRA_BRANCHES)
        fo = ROOT.TFile.Open(tmp, "UPDATE")
        for name, ctype, val in params:
            ROOT.TParameter(ctype)(name, val).Write()
        fo.Close()
        os.rename(tmp, fout)
        res.update(status="ok", entries=int(n.GetValue()), max_diff=float(dmax.GetValue()),
                   n_diff_gt_1e3=int(n_gt3.GetValue()), n_diff_gt_0=int(n_gt0.GetValue()),
                   params=params, seconds=time.time() - t0)
    except Exception as ex:  # report, never abort the pool
        if os.path.exists(tmp):
            os.remove(tmp)
        res.update(status="error", error=repr(ex), seconds=time.time() - t0)
    return res


def collect_jobs(in_stage, out_stage, acol, procs_glob, max_chunks, overwrite):
    jobs, skipped = [], 0
    procs = sorted(p for p in os.listdir(in_stage)
                   if os.path.isdir(os.path.join(in_stage, p)) and p != "syst")
    if procs_glob:
        procs = [p for p in procs if any(fnmatch.fnmatch(p, g) for g in procs_glob)]
    for p in procs:
        files = sorted(glob.glob(os.path.join(in_stage, p, "*.root")))
        if max_chunks:
            files = files[:max_chunks]
        os.makedirs(os.path.join(out_stage, p), exist_ok=True)
        for fin in files:
            fout = os.path.join(out_stage, p, os.path.basename(fin))
            if os.path.exists(fout) and not overwrite:
                skipped += 1
                continue
            jobs.append({"process": p, "in": fin, "out": fout, "acol": acol,
                         "size": os.path.getsize(fin)})
    # biggest chunks first: better load balance over the workers
    jobs.sort(key=lambda j: -j["size"])
    return procs, jobs, skipped


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ecm", type=int, required=True, choices=(240, 365))
    ap.add_argument("--flavor", required=True, choices=("mumu", "ee"))
    ap.add_argument("--in-stage", help=f"input stage dir (default site_config output_dir(ecm, flavor, '{IN_STAGE_DEFAULT}'))")
    ap.add_argument("--out-stage", required=True, help="output stage dir (created; must differ from --in-stage)")
    ap.add_argument("--acol", required=True, choices=("jan", "training"),
                    help="acolinearity fed to the model: 'jan' = acos(-cos opening angle) from the stored "
                         "theta/phi, 'training' = the stored |theta1-theta2| (pure re-scoring check)")
    ap.add_argument("--model", help="SaveXGBoost model file (default site_config.bdt_model(ecm, flavor))")
    ap.add_argument("--threads", type=int, default=3, help="worker processes (default 3)")
    ap.add_argument("--procs", nargs="*", metavar="GLOB", help="only the process dirs matching these globs")
    ap.add_argument("--max-chunks", type=int, default=0, help="only the first N chunks of every process (0 = all)")
    ap.add_argument("--overwrite", action="store_true", help="re-do existing output chunks (default: skip them)")
    ap.add_argument("--summary-json", help="write the per-chunk report to this JSON file")
    args = ap.parse_args()

    in_stage = os.path.abspath(args.in_stage or output_dir(args.ecm, args.flavor, IN_STAGE_DEFAULT))
    out_stage = os.path.abspath(args.out_stage)
    model = os.path.abspath(args.model or bdt_model(args.ecm, args.flavor))
    if not os.path.isdir(in_stage):
        sys.exit(f"ERROR: input stage {in_stage} does not exist")
    if os.path.realpath(in_stage) == os.path.realpath(out_stage):
        sys.exit("ERROR: --out-stage must differ from --in-stage")
    if not os.path.isfile(model):
        sys.exit(f"ERROR: model {model} does not exist")
    os.makedirs(out_stage, exist_ok=True)

    procs, jobs, skipped = collect_jobs(in_stage, out_stage, args.acol, args.procs, args.max_chunks, args.overwrite)
    print(f"== rescore_leptonic S{args.ecm}/{args.flavor}  acol={args.acol}  threads={args.threads}")
    print(f"== model    : {model}")
    print(f"== in-stage : {in_stage}")
    print(f"== out-stage: {out_stage}")
    print(f"== inputs   : {TRAIN_VARS}" + (f"  with {ACOL_VAR} -> acol_jan" if args.acol == "jan" else ""))
    print(f"== {len(procs)} processes, {len(jobs)} chunks to do ({sum(j['size'] for j in jobs) / 1e9:.1f} GB), "
          f"{skipped} existing outputs skipped", flush=True)

    results = []
    t0 = time.time()
    if jobs:
        ctx = mp.get_context("spawn")
        with ctx.Pool(args.threads, initializer=worker_init, initargs=(model,)) as pool:
            for i, r in enumerate(pool.imap_unordered(process_chunk, jobs, chunksize=1), 1):
                results.append(r)
                if r["status"] == "ok":
                    print(f"[{i}/{len(jobs)}] {r['process']}/{r['chunk']}: {r['entries']} entries, "
                          f"max|new-orig| {r['max_diff']:.3g}, n>1e-3 {r['n_diff_gt_1e3']}, n>0 {r['n_diff_gt_0']}, "
                          f"{r['seconds']:.0f} s", flush=True)
                elif r["status"] in ("treeless", "empty"):
                    print(f"[{i}/{len(jobs)}] {r['process']}/{r['chunk']}: {r['status'].upper()} "
                          f"(no entries), copied unchanged (params {r['params']})", flush=True)
                else:
                    print(f"[{i}/{len(jobs)}] {r['process']}/{r['chunk']}: ERROR {r.get('error')}", flush=True)

    # per-process summary (over the chunks done in THIS run)
    per_proc = {}
    for r in results:
        d = per_proc.setdefault(r["process"], {"chunks": 0, "treeless": 0, "errors": 0, "entries": 0,
                                               "max_diff": 0.0, "n_diff_gt_1e3": 0, "n_diff_gt_0": 0})
        d["chunks"] += 1
        if r["status"] in ("treeless", "empty"):   # copied unchanged (counted together)
            d["treeless"] += 1
        elif r["status"] == "error":
            d["errors"] += 1
        else:
            d["entries"] += r["entries"]
            d["max_diff"] = max(d["max_diff"], r["max_diff"])
            d["n_diff_gt_1e3"] += r["n_diff_gt_1e3"]
            d["n_diff_gt_0"] += r["n_diff_gt_0"]
    print("\n== per-process summary (this run): process  chunks treeless errors entries  max|new-orig|  n>1e-3 (frac)  n>0 (frac)")
    tot = {"chunks": 0, "treeless": 0, "errors": 0, "entries": 0, "max_diff": 0.0, "n_diff_gt_1e3": 0, "n_diff_gt_0": 0}
    for p in sorted(per_proc):
        d = per_proc[p]
        for k in tot:
            tot[k] = max(tot[k], d[k]) if k == "max_diff" else tot[k] + d[k]
        fr3 = d["n_diff_gt_1e3"] / d["entries"] if d["entries"] else 0.0
        fr0 = d["n_diff_gt_0"] / d["entries"] if d["entries"] else 0.0
        print(f"   {p:45s} {d['chunks']:4d} {d['treeless']:3d} {d['errors']:3d} {d['entries']:11d}  {d['max_diff']:.3g}  "
              f"{d['n_diff_gt_1e3']} ({fr3:.4%})  {d['n_diff_gt_0']} ({fr0:.4%})")
    fr3 = tot["n_diff_gt_1e3"] / tot["entries"] if tot["entries"] else 0.0
    fr0 = tot["n_diff_gt_0"] / tot["entries"] if tot["entries"] else 0.0
    print(f"   {'TOTAL':45s} {tot['chunks']:4d} {tot['treeless']:3d} {tot['errors']:3d} {tot['entries']:11d}  {tot['max_diff']:.3g}  "
          f"{tot['n_diff_gt_1e3']} ({fr3:.4%})  {tot['n_diff_gt_0']} ({fr0:.4%})")
    print(f"== done in {time.time() - t0:.0f} s, {tot['errors']} errors")
    if args.summary_json:
        with open(args.summary_json, "w") as fj:
            json.dump({"ecm": args.ecm, "flavor": args.flavor, "acol": args.acol, "model": model,
                       "in_stage": in_stage, "out_stage": out_stage, "skipped_existing": skipped,
                       "per_process": per_proc, "total": tot, "chunks": results}, fj, indent=1)
    sys.exit(1 if tot["errors"] else 0)


if __name__ == "__main__":
    main()
