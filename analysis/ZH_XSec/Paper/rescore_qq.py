#!/usr/bin/env python3
"""
Re-score an existing hadronic (Z->qq) stage1 analysis stage with another BDT model,
chunk by chunk, into a NEW stage directory (the input stage is never touched).

For every <in-stage>/<process>/chunk_<i>.root:
  - chunks with an 'events' tree: the BDT inputs (the model's 'variables' TList, i.e.
    zqq_stage1_common.TRAIN_VARS) are taken from the stored branches, transformed according
    to the BDT-input variant (zqq_bdt_variant.py: --variant, default = ZQQ_BDT_VARIANT; the
    nominal inputs are the identity), and scored with the SAME scorer stage1 uses
    (tmva_helper_xgb / TMVA RBDT, one single-threaded interpreter per worker). The output
    tree holds exactly the input branches, with mva_score replaced by the new score and the
    stored one kept as mva_score_orig (RVec<float> like mva_score). The input's compression
    settings are reused; entry order is preserved (single-threaded event loop per chunk).
  - tree-less chunks (TParameters only, e.g. nunuH_Hinv at 240) are copied unchanged.
  - the TParameters (eventsProcessed, eventsSelected, ...) are re-written into every output.
Per chunk the script also records, in the same event loop, max|new - stored| of the score,
the number of events with |diff| > 1e-3 and > 1e-2, and the counts above the BDT working
point for the stored and the new score; the per-process and global totals go to
<out-stage>/rescore_summary.json and to stdout.

Validation: run with the ORIGINAL model and --variant none: the new score must reproduce
the stored one (max|diff| = 0 up to the float round trip; the RBDT thresholds of ROOT 6.28 are
the very ones stage1 used, so no 6-digit rounding difference arises).

Usage (key4hep env):
  python3 rescore_qq.py --ecm 240 --in-stage <STORE>/S240/qq/BDT_analysis_samples_oldbdt \
      --out-stage <STORE>/S240/qq/BDT_analysis_samples_bugw \
      --model <STORE>/models_variants/bugw/S240/qq/bdt_model_ecm240.root --variant bugw --threads 3
  [--procs 'wzp6_ee_qqH_*'] [--wp 0.75] [--limit N] [--chunks-per-proc N] [--overwrite]
(--procs / --limit / --chunks-per-proc restrict the chunk list: the summary is then written as
rescore_summary_partial.json)
"""
import argparse
import glob
import json
import os
import shutil
import sys
import time
from multiprocessing import get_context

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from site_config import SDCC_BASE                     # noqa: E402
import zqq_bdt_variant as bdt_variant                 # noqa: E402  (no ROOT import at module level)

DEFAULT_WP = {240: 0.75, 365: 0.95}   # stage2 MVA_WP (arXiv:2512.21290)

_G = {}   # per-worker state (ROOT, model helper, input expressions, working point)


def _worker_init(model, variant, wp):
    import ROOT
    ROOT.gROOT.SetBatch(True)
    ROOT.gErrorIgnoreLevel = ROOT.kWarning
    # the python TMVAHelperXGB loads libTMVAHelper and reads the 'variables' TList; the thread
    # pool is not enabled in the workers, so the helper builds a single RBDT interpreter
    from addons.TMVAHelper.TMVAHelper import TMVAHelperXGB
    helper = TMVAHelperXGB(model, "bdt_model")
    _G.update(ROOT=ROOT, helper=helper, wp=wp,
              exprs=bdt_variant.input_expressions(helper.variables, variant))


def _read_params(ROOT, fname):
    """(has_events_tree, [(class template arg, name, value), ...], compression settings)."""
    tf = ROOT.TFile.Open(fname)
    if not tf or tf.IsZombie():
        raise RuntimeError(f"cannot open {fname}")
    has_tree = False
    nentries = 0
    params = []
    for key in tf.GetListOfKeys():
        name, cls = key.GetName(), key.GetClassName()
        if name == "events":
            if cls == "TTree":
                has_tree = True
                nentries = int(key.ReadObj().GetEntries())
            continue
        if cls.startswith("TParameter<"):
            params.append((cls[len("TParameter<"):-1], name, key.ReadObj().GetVal()))
        else:
            raise RuntimeError(f"{fname}: unexpected key {name} of class {cls}")
    comp = (tf.GetCompressionAlgorithm(), tf.GetCompressionLevel())
    tf.Close()
    return has_tree, nentries, params, comp


def _process_chunk(job):
    fin, fout = job
    ROOT, helper, exprs, wp = _G["ROOT"], _G["helper"], _G["exprs"], _G["wp"]
    t0 = time.time()
    os.makedirs(os.path.dirname(fout), exist_ok=True)
    has_tree, nentries, params, comp = _read_params(ROOT, fin)
    rec = {"in": fin, "out": fout, "treeless": not has_tree, "empty": has_tree and nentries == 0,
           "n": 0, "maxdiff": 0.0, "n_gt_1e-3": 0, "n_gt_1e-2": 0, "n_hi_orig": 0, "n_hi_new": 0,
           "sum_orig": 0.0, "sum_new": 0.0}
    if not has_tree:
        shutil.copyfile(fin, fout)
        rec["seconds"] = time.time() - t0
        return rec
    if nentries == 0:
        # empty tree (the patched zero-selection chunks, e.g. the dileptonic processes at 365): a
        # zero-entry Snapshot would write a BRANCH-LESS tree and break stage2's column lookup for
        # processes whose chunks are all empty, so clone the full tree structure instead (every
        # input branch, no mva_score_orig: nothing to keep) and re-write the TParameters
        fi = ROOT.TFile.Open(fin)
        fo = ROOT.TFile.Open(fout, "RECREATE")
        fo.cd()
        tc = fi.Get("events").CloneTree(0)
        tc.Write()
        for targ, name, val in params:
            fo.WriteTObject(ROOT.TParameter(targ)(name, val), name)
        fo.Close()
        fi.Close()
        rec["seconds"] = time.time() - t0
        return rec

    df = ROOT.RDataFrame("events", fin)
    cols_in = [str(c) for c in df.GetColumnNames()]
    if "mva_score" not in cols_in:
        raise RuntimeError(f"{fin}: no mva_score branch")
    df = df.Define("mva_score_orig", "mva_score")
    names = []
    for var in helper.variables:
        if var not in cols_in:
            raise RuntimeError(f"{fin}: BDT input {var} not in the tree")
        cn = f"bdtin_{var}"
        df = df.Define(cn, f"(float)({exprs[var]})")
        names.append(cn)
    df = df.Define("bdtin_vec", "ROOT::VecOps::RVec<float>{" + ", ".join(names) + "}")
    df = df.Redefine("mva_score", helper.tmva_helper, ["bdtin_vec"])
    df = df.Define("mva_new0", "mva_score[0]")
    df = df.Define("mva_orig0", "mva_score_orig[0]")
    df = df.Define("mva_absdiff", "std::abs(mva_new0 - mva_orig0)")

    n = df.Count()
    mx = df.Max("mva_absdiff")
    n3 = df.Filter("mva_absdiff > 1e-3").Count()
    n2 = df.Filter("mva_absdiff > 1e-2").Count()
    nho = df.Filter(f"mva_orig0 >= {wp!r}").Count()
    nhn = df.Filter(f"mva_new0 >= {wp!r}").Count()
    so = df.Sum("mva_orig0")
    sn = df.Sum("mva_new0")

    opts = ROOT.RDF.RSnapshotOptions()
    opts.fLazy = True
    opts.fCompressionAlgorithm, opts.fCompressionLevel = comp
    snap = df.Snapshot("events", fout, cols_in + ["mva_score_orig"], opts)
    snap.GetValue()   # one event loop for the snapshot and every statistic above

    nn = int(n.GetValue())
    rec.update(n=nn, maxdiff=float(mx.GetValue()) if nn else 0.0,
               **{"n_gt_1e-3": int(n3.GetValue()), "n_gt_1e-2": int(n2.GetValue())},
               n_hi_orig=int(nho.GetValue()), n_hi_new=int(nhn.GetValue()),
               sum_orig=float(so.GetValue()), sum_new=float(sn.GetValue()))

    fo = ROOT.TFile.Open(fout, "UPDATE")
    for targ, name, val in params:
        fo.WriteTObject(ROOT.TParameter(targ)(name, val), name)
    fo.Close()
    rec["seconds"] = time.time() - t0
    return rec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ecm", type=int, required=True, choices=(240, 365))
    ap.add_argument("--in-stage", default=None,
                    help="stage1 analysis stage to re-score (default <STORE>/S<ecm>/qq/BDT_analysis_samples_oldbdt)")
    ap.add_argument("--out-stage", required=True, help="output stage dir (created; must not be the input)")
    ap.add_argument("--model", required=True, help="TMVA-format xgb model (bdt_model + variables TList)")
    ap.add_argument("--variant", default=bdt_variant.VARIANT or "none",
                    choices=("none",) + bdt_variant.KNOWN_VARIANTS,
                    help="BDT-input transform applied before inference (default: ZQQ_BDT_VARIANT or none)")
    ap.add_argument("--threads", type=int, default=3, help="worker processes (one single-threaded event loop each)")
    ap.add_argument("--procs", default="*", help="glob of process dirs to re-score (default all)")
    ap.add_argument("--wp", type=float, default=None, help="BDT working point for the above-WP counts (default per ecm)")
    ap.add_argument("--limit", type=int, default=0, help="only the first N chunks (tests)")
    ap.add_argument("--chunks-per-proc", type=int, default=0,
                    help="only the first N chunks of every process (validation subsets)")
    ap.add_argument("--overwrite", action="store_true", help="overwrite existing output chunks")
    args = ap.parse_args()

    variant = "" if args.variant == "none" else args.variant
    wp = DEFAULT_WP[args.ecm] if args.wp is None else args.wp
    in_stage = os.path.abspath(args.in_stage or f"{SDCC_BASE}/S{args.ecm}/qq/BDT_analysis_samples_oldbdt")
    out_stage = os.path.abspath(args.out_stage)
    if os.path.realpath(in_stage) == os.path.realpath(out_stage):
        sys.exit("ERROR: --out-stage is the input stage")
    if not os.path.isdir(in_stage):
        sys.exit(f"ERROR: input stage {in_stage} does not exist")
    if not os.path.isfile(args.model):
        sys.exit(f"ERROR: model {args.model} does not exist")

    files = sorted(glob.glob(f"{in_stage}/{args.procs}/chunk_*.root"))
    if not files:
        sys.exit(f"ERROR: no chunks match {in_stage}/{args.procs}/chunk_*.root")
    if args.chunks_per_proc > 0:
        files = [f for f in files
                 if int(os.path.basename(f)[len("chunk_"):-len(".root")]) < args.chunks_per_proc]
    if args.limit > 0:
        files = files[:args.limit]
    partial = args.procs != "*" or args.limit > 0 or args.chunks_per_proc > 0
    jobs = []
    for fin in files:
        rel = os.path.relpath(fin, in_stage)
        fout = os.path.join(out_stage, rel)
        if os.path.exists(fout) and not args.overwrite:
            sys.exit(f"ERROR: {fout} exists (use --overwrite)")
        jobs.append((fin, fout))
    # biggest chunks first: better load balance across the workers
    jobs.sort(key=lambda j: -os.path.getsize(j[0]))

    print(f"== rescore_qq: ecm {args.ecm}, variant {variant or 'none'}, model {args.model}")
    print(f"== in  {in_stage}\n== out {out_stage}\n== {len(jobs)} chunks, {args.threads} workers, WP {wp}")
    sys.stdout.flush()
    t0 = time.time()
    os.makedirs(out_stage, exist_ok=True)
    ctx = get_context("fork")
    results = []
    with ctx.Pool(args.threads, initializer=_worker_init, initargs=(args.model, variant, wp)) as pool:
        for i, rec in enumerate(pool.imap_unordered(_process_chunk, jobs), 1):
            results.append(rec)
            if i % 50 == 0 or i == len(jobs):
                done_ev = sum(r["n"] for r in results)
                print(f"   {i}/{len(jobs)} chunks, {done_ev} events, {time.time() - t0:.0f}s")
                sys.stdout.flush()

    # per-process and global summary
    per_proc = {}
    for r in results:
        p = os.path.basename(os.path.dirname(r["in"]))
        d = per_proc.setdefault(p, {"chunks": 0, "treeless": 0, "n": 0, "maxdiff": 0.0, "n_gt_1e-3": 0,
                                    "n_gt_1e-2": 0, "n_hi_orig": 0, "n_hi_new": 0, "sum_orig": 0.0, "sum_new": 0.0})
        d["chunks"] += 1
        d["treeless"] += int(r["treeless"])
        d["empty"] = d.get("empty", 0) + int(r.get("empty", False))
        for k in ("n", "n_gt_1e-3", "n_gt_1e-2", "n_hi_orig", "n_hi_new", "sum_orig", "sum_new"):
            d[k] += r[k]
        d["maxdiff"] = max(d["maxdiff"], r["maxdiff"])
    tot = {"chunks": len(results), "treeless": sum(r["treeless"] for r in results),
           "empty": sum(int(r.get("empty", False)) for r in results),
           "n": sum(r["n"] for r in results), "maxdiff": max([r["maxdiff"] for r in results] + [0.0]),
           "n_gt_1e-3": sum(r["n_gt_1e-3"] for r in results), "n_gt_1e-2": sum(r["n_gt_1e-2"] for r in results),
           "n_hi_orig": sum(r["n_hi_orig"] for r in results), "n_hi_new": sum(r["n_hi_new"] for r in results),
           "sum_orig": sum(r["sum_orig"] for r in results), "sum_new": sum(r["sum_new"] for r in results),
           "seconds": time.time() - t0}
    summary = {"ecm": args.ecm, "variant": variant or "none", "model": args.model, "in_stage": in_stage,
               "out_stage": out_stage, "wp": wp, "total": tot, "per_process": per_proc, "chunks": results}
    sname = f"{out_stage}/rescore_summary{'_partial' if partial else ''}.json"
    with open(sname, "w") as f:
        json.dump(summary, f, indent=1)

    n = tot["n"] or 1
    print(f"== done: {tot['chunks']} chunks ({tot['treeless']} tree-less copied, {tot['empty']} empty trees cloned), "
          f"{tot['n']} events, "
          f"{tot['seconds']:.0f}s")
    print(f"== score vs stored: max|diff| = {tot['maxdiff']:.3e}, frac(|diff| > 1e-3) = {tot['n_gt_1e-3'] / n:.3e}, "
          f"frac(|diff| > 1e-2) = {tot['n_gt_1e-2'] / n:.3e}")
    print(f"== above WP {wp}: stored {tot['n_hi_orig']} ({tot['n_hi_orig'] / n:.4f}), "
          f"new {tot['n_hi_new']} ({tot['n_hi_new'] / n:.4f}); mean score stored {tot['sum_orig'] / n:.4f}, "
          f"new {tot['sum_new'] / n:.4f}")
    print(f"== summary written to {sname}")


if __name__ == "__main__":
    main()
