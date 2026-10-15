#!/usr/bin/env python3
"""
Validate the outputs of a condor fan-out produced by submit_stage1.py.

For every wrapper listed in <condor-dir>/wrappers.txt the expected chunk file is
opened once (ROOT only, no tree data read beyond the header) and cross-checked
against the job's condor .err log. Run it in the key4hep/winter2023 env:

    python3 condor/check_chunks.py --ecm 240 --flavor mumu                 # analysis stage
    python3 condor/check_chunks.py --ecm 240 --flavor qq --stage MVA_ntuples
    python3 condor/check_chunks.py --ecm 365 --flavor qq --json /path/summary.json --write-resubmit

    # on a read-only reference snapshot (never write into *.jul2026):
    python3 condor/check_chunks.py --ecm 240 --flavor mumu \\
        --condor-dir  $STORE/S240/mumu/condor.jul2026/BDT_analysis_samples \\
        --out-dir     $STORE/S240/mumu/BDT_analysis_samples.jul2026 \\
        --json        $SCRATCH/mumu240.json --write-resubmit --resubmit-dir $SCRATCH

Layout (written by submit_stage1.py, STORE = /gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper):
    <condor-dir> = STORE/S{ecm}/{flavor}/condor/<stage>/
        wrappers.txt                one wrapper path per line; condor $(Process) = line number - 1
        stage1.sub                  submit description ("queue filename from wrappers.txt")
        run_<process>_chunk_<i>.sh  job wrappers
        log/<cluster>.<idx>.{out,err}, log/<cluster>.log
    <out-dir>    = STORE/S{ecm}/{flavor}/<stage>/<process>/chunk_<i>.root

The expected output file of a wrapper is derived from the wrapper NAME
(run_<process>_chunk_<i>.sh -> <out-dir>/<process>/chunk_<i>.root), not from the
--output line inside it, so a renamed condor/output dir pair (e.g. *.jul2026) can be
checked by overriding --condor-dir / --out-dir.

Per-chunk status
    OK           'events' TTree with > 0 entries + 'eventsProcessed', consistent with the log
    EMPTY_TREE   valid 'events' TTree with 0 entries (informational: e.g. the 365 GeV
                 dileptonic backgrounds after the hadronic lepton veto); still needs
                 eventsProcessed == log count
    NO_LOG       file is OK/EMPTY_TREE but no usable .err log was found (reported, not fatal)
    MISSING      expected chunk file does not exist
    ZERO_BYTE    file exists with size 0
    NO_TREE      file opens but has no 'events' TTree; a job that selects 0 events writes a
                 ROOT file WITHOUT any keys ('key-less') - detected here so the companion
                 patch tool can write an empty tree + eventsProcessed
    NO_EP        'events' present but no 'eventsProcessed' TParameter (stage2 normalization
                 would break; treated as bad)
    UNREADABLE   ROOT cannot open the file (zombie) or had to recover it (not closed)
    EP_MISMATCH  eventsProcessed != the value the runner stored according to the log:
                 'Number of events: - original: N' if printed (inputs already carried
                 eventsProcessed), else the SUMMARY's 'Total events processed: N', else
                 '----> INFO: Number of local events: N' (same rule as run_analysis.py)

Non-fatal warnings (fatal with --strict):
    EXTRA        chunk*.root files in a process dir that no wrapper accounts for
                 (fccanalysis final globs <process>/chunk*.root, so they WOULD be double
                 counted in stage2 - delete or move them)
    SEL_MISMATCH tree entries != 'No. result events' of the log (stale file / log pair)

Log association: every .err in <condor-dir>/log is parsed once (16 threads: cold GPFS
opens dominate). A log is bound to a chunk primarily by the '----> INFO: Output file
path:' line it prints (<process>/chunk_<i>.root), which stays correct when a resubmit
cluster was queued from resubmit.txt and therefore carries different $(Process) indices.
Logs that died before printing that line fall back to the index rule
(log/<cluster>.<idx>.err <-> wrappers.txt line idx+1), but only if the input file they
printed ('Creating dataframe object from files: - ...') is one of the wrapper's
--files-list inputs (or they printed none): a died-early log of a resubmit job whose
$(Process) collides with another chunk's index is never applied to that chunk. Among the
candidates the highest cluster number wins (path-bound logs take precedence over
index-bound ones). Missing, foreign-only or count-less logs give NO_LOG, which is not
fatal if the file itself is fine.

--jobs N (default 4) checks the files in N forked workers (each imports ROOT itself);
the run time is GPFS open latency, ~40 ms per file single-threaded. If a worker dies
(ROOT crash on a corrupt file) the run aborts with exit 2 instead of hanging; rerun with
--jobs 1 to see which file it was.

Exit code: 0 iff no chunk is MISSING/ZERO_BYTE/NO_TREE/NO_EP/UNREADABLE/EP_MISMATCH
(and, with --strict, no warning); 2 on usage errors (no or empty wrappers.txt, ...).

--write-resubmit writes resubmit.txt (wrapper paths of the bad chunks, one per line) and
resubmit.sub (copy of stage1.sub whose queue line reads resubmit.txt) into --resubmit-dir
(default: <condor-dir>). Submit with `condor_submit <dir>/resubmit.sub`; the new cluster's
logs land in the same log/ dir and are matched by output path on the next check. The
wrapper path written is <condor-dir>/<basename> when that exists (wrappers.txt may still
list the pre-rename location), else the path as listed.

Safety: this tool never writes into a path containing a *.jul2026 or models_backup*
component (read-only reference snapshots; symlinks are resolved before the check);
--json/--resubmit-dir must point elsewhere.
"""
import argparse
import json
import os
import re
import signal
import sys
import time

ROOT = None   # imported lazily (in the workers when --jobs > 1): PyROOT must not see argv

SDCC_BASE = "/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper"

# read-only reference snapshots: refuse to write anything below a path component that
# ends with / starts with one of these
PROTECTED_MARKERS = (".jul2026", "models_backup")

BAD_STATUSES = ("MISSING", "ZERO_BYTE", "NO_TREE", "NO_EP", "UNREADABLE", "EP_MISMATCH")
ALL_STATUSES = ("OK", "EMPTY_TREE", "NO_LOG") + BAD_STATUSES

WRAPPER_RE = re.compile(r"^run_(?P<proc>.+)_chunk_(?P<idx>\d+)\.sh$")
LOG_RE     = re.compile(r"^(?P<cluster>\d+)\.(?P<idx>\d+)\.err$")
LOCAL_RE   = re.compile(r"Number of local events:\s*([\d,]+)")
ORIG_RE    = re.compile(r"Number of events:\s*\n\s*- original:\s*([\d,]+)\s*\n\s*- local:\s*([\d,]+)")
TOTAL_RE   = re.compile(r"Total events processed:\s*([\d,]+)")
RESULT_RE  = re.compile(r"No\. result events:\s*([\d,]+)")
OUTPATH_RE = re.compile(r"Output file path:\s*\n\s*(\S+\.root)")
INPUT_RE   = re.compile(r"Creating dataframe object from files:\s*\n\s*-\s*(\S+)")
FILELIST_RE = re.compile(r"--files-list\s+(.*)", re.S)


# --------------------------------------------------------------------------- helpers
def die(msg):
    """Usage / environment error: message on stderr, exit code 2."""
    print(msg, file=sys.stderr)
    sys.exit(2)


def is_protected(path):
    """
    True if any component of the absolute OR symlink-resolved path marks a read-only
    reference snapshot (a symlink from elsewhere into a snapshot must not bypass the guard).
    """
    for p in {os.path.abspath(path), os.path.realpath(path)}:
        for comp in p.split(os.sep):
            if any(comp.endswith(m) or comp.startswith(m) for m in PROTECTED_MARKERS):
                return True
    return False


def refuse_if_protected(path, what):
    if is_protected(path):
        die(f"ERROR: refusing to write {what} into a read-only reference snapshot: {path}\n"
                 f"       (path component matching {PROTECTED_MARKERS}); use --json/--resubmit-dir "
                 f"pointing elsewhere.")


def to_int(s):
    return int(s.replace(",", ""))


def chunk_key(process, idx):
    """Directory-independent identity of a chunk file: '<process>/chunk_<i>.root'."""
    return f"{process}/chunk_{idx}.root"


def read_wrappers(condor_dir):
    """
    Parse wrappers.txt -> list of dicts (idx, process, chunk, listed wrapper path, expected
    wrapper path in condor_dir). idx = condor $(Process) = position among non-blank lines.
    """
    listfile = os.path.join(condor_dir, "wrappers.txt")
    if not os.path.isfile(listfile):
        die(f"ERROR: no wrappers.txt in {condor_dir} (not a submit_stage1.py condor dir?)")
    entries = []
    with open(listfile) as lf:
        lines = [l.strip() for l in lf if l.strip() and not l.lstrip().startswith("#")]
    for idx, listed in enumerate(lines):
        base = os.path.basename(listed)
        m = WRAPPER_RE.match(base)
        if not m:
            die(f"ERROR: wrappers.txt line {idx+1} is not run_<process>_chunk_<i>.sh: {listed}")
        local = os.path.join(condor_dir, base)
        entries.append({
            "idx": idx,
            "process": m.group("proc"),
            "chunk": int(m.group("idx")),
            "wrapper_listed": listed,
            # the location to (re)submit: this condor dir if the wrapper is here, else as listed
            "wrapper": local if os.path.isfile(local) else listed,
            "wrapper_exists": os.path.isfile(local) or os.path.isfile(listed),
            "inputs": False,   # lazily parsed --files-list (set of '<process>/<file>'), None if unreadable
        })
    if not entries:
        die(f"ERROR: {listfile} lists no wrappers (nothing to check)")
    return entries


def input_key(path):
    """Directory-independent identity of an input file: '<process>/<basename>'."""
    parts = path.rstrip("/").split("/")
    return "/".join(parts[-2:]) if len(parts) >= 2 else parts[-1]


def wrapper_inputs(entry):
    """
    The --files-list inputs of a wrapper as a set of input_key()s (parsed once, cached);
    None if the wrapper cannot be read.
    """
    if entry["inputs"] is False:
        entry["inputs"] = None
        for cand in (entry["wrapper"], entry["wrapper_listed"]):
            try:
                with open(cand) as f:
                    m = FILELIST_RE.search(f.read())
            except OSError:
                continue
            if m:
                toks = [t for t in m.group(1).split() if t != "\\" and not t.startswith("--")]
                entry["inputs"] = {input_key(t) for t in toks}
            else:
                entry["inputs"] = set()
            break
    return entry["inputs"]


def parse_err(path):
    """
    Extract from a job's .err log the eventsProcessed the runner stored, the number of
    result events and the output-file key. Mirrors FCCAnalyses-winter2023 run_analysis.py:
    eventsProcessed = nevents_orig ('Number of events: - original: N', only when the inputs
    already carry an eventsProcessed key) if > 0, else inn ('Total events processed: N' of
    the SUMMARY); 'Number of local events: N' is the pre-run input count and is used only
    when the SUMMARY is absent.
    """
    info = {"events": None, "local": None, "original": None, "total": None,
            "selected": None, "outkey": None, "input": None}
    try:
        with open(path, errors="replace") as f:
            txt = f.read()
    except OSError:
        return info
    m = ORIG_RE.search(txt)
    if m:
        info["original"], info["local"] = to_int(m.group(1)), to_int(m.group(2))
    else:
        m = LOCAL_RE.search(txt)
        if m:
            info["local"] = to_int(m.group(1))
    m = TOTAL_RE.search(txt)
    if m:
        info["total"] = to_int(m.group(1))
    m = RESULT_RE.search(txt)
    if m:
        info["selected"] = to_int(m.group(1))
    if info["original"]:
        info["events"] = info["original"]
    elif info["total"] is not None:
        info["events"] = info["total"]
    else:
        info["events"] = info["local"]
    m = OUTPATH_RE.search(txt)
    if m:
        parts = m.group(1).rstrip("/").split("/")
        if len(parts) >= 2:
            info["outkey"] = "/".join(parts[-2:])   # <process>/chunk_<i>.root
    m = INPUT_RE.search(txt)
    if m:
        info["input"] = input_key(m.group(1))       # <process>/events_<...>.root
    return info


def index_logs(log_dir):
    """
    Parse every <cluster>.<idx>.err once. Returns
        by_key  : outkey -> [(cluster, idx, errpath, info)]  (logs that printed their output path)
        by_idx  : idx    -> [(cluster, idx, errpath, info)]  (logs without an output path line)
        clusters: sorted list of cluster ids seen
    """
    by_key, by_idx, clusters = {}, {}, set()
    if not os.path.isdir(log_dir):
        return by_key, by_idx, [], 0
    logs = []
    for name in sorted(os.listdir(log_dir)):
        m = LOG_RE.match(name)
        if m:
            logs.append((int(m.group("cluster")), int(m.group("idx")), os.path.join(log_dir, name)))
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=16) as ex:
        infos = list(ex.map(lambda l: parse_err(l[2]), logs))
    for (cluster, idx, errpath), info in zip(logs, infos):
        clusters.add(cluster)
        rec = (cluster, idx, errpath, info)
        if info["outkey"]:
            by_key.setdefault(info["outkey"], []).append(rec)
        else:
            by_idx.setdefault(idx, []).append(rec)
    return by_key, by_idx, sorted(clusters), len(logs)


def resolve_log(by_key, by_idx, entry):
    """
    Pick the log for a chunk: path-bound logs first, else index-bound logs whose printed
    input file belongs to this wrapper (or that printed none); highest cluster wins.
    Returns (record or None, foreign): foreign is True when index-bound logs existed but
    all belonged to other jobs (e.g. a resubmit cluster's $(Process) colliding with idx).
    """
    cands = by_key.get(chunk_key(entry["process"], entry["chunk"]))
    foreign = False
    if not cands:
        cands = []
        for rec in by_idx.get(entry["idx"], []):
            inp = rec[3]["input"]
            if inp is not None:
                inputs = wrapper_inputs(entry)
                ok = (inp in inputs) if inputs else (inp.split("/")[0] == entry["process"])
                if not ok:
                    foreign = True
                    continue
            cands.append(rec)
    if not cands:
        return None, foreign
    return max(cands, key=lambda r: r[0]), foreign


def check_file(ROOT, path):
    """
    Open one chunk file once; return (status, entries, eventsProcessed, eventsSelected, note).
    status is one of OK / EMPTY_TREE / MISSING / ZERO_BYTE / UNREADABLE / NO_TREE / NO_EP.
    """
    if not os.path.exists(path):
        return "MISSING", None, None, None, ""
    try:
        size = os.path.getsize(path)
    except OSError as e:
        return "UNREADABLE", None, None, None, str(e)
    if size == 0:
        return "ZERO_BYTE", None, None, None, ""
    try:
        tf = ROOT.TFile.Open(path, "READ")   # PyROOT raises OSError when the open fails
    except OSError as e:
        return "UNREADABLE", None, None, None, f"TFile::Open failed: {e}"
    try:
        if not tf or tf.IsZombie() or not tf.IsOpen():
            return "UNREADABLE", None, None, None, "TFile::Open failed (zombie)"
        if tf.TestBit(ROOT.TFile.kRecovered):
            return "UNREADABLE", None, None, None, "file was not closed properly (ROOT recovered it)"
        keys = {k.GetName(): k.GetClassName() for k in tf.GetListOfKeys()}
        if not keys:
            return "NO_TREE", None, None, None, "key-less file (job selected 0 events)"
        if keys.get("events") != "TTree":
            return "NO_TREE", None, None, None, "keys: " + ", ".join(sorted(keys))
        entries = int(tf.Get("events").GetEntries())
        if "eventsProcessed" not in keys:
            return "NO_EP", entries, None, None, "no eventsProcessed key"
        ep = int(tf.Get("eventsProcessed").GetVal())
        es = int(tf.Get("eventsSelected").GetVal()) if "eventsSelected" in keys else None
        return ("EMPTY_TREE" if entries == 0 else "OK"), entries, ep, es, ""
    finally:
        if tf:
            tf.Close()


def _init_root():
    """Import ROOT into this process (called in each worker, or once in-process)."""
    global ROOT
    import ROOT as _R
    _R.PyConfig.IgnoreCommandLineOptions = True
    _R.gROOT.SetBatch(True)
    _R.gErrorIgnoreLevel = _R.kError   # hide Info/Warning chatter; real errors still print
    ROOT = _R


def _check_one(path):
    return check_file(ROOT, path)


def check_files(paths, jobs, progress=None):
    """
    check_file() over all paths, in order. jobs > 1 forks a pool of workers that each
    import ROOT themselves (the parent never imports it, so fork is safe); the time is
    dominated by GPFS open latency, not CPU, so a handful of workers is enough.
    """
    results = []
    if jobs <= 1:
        _init_root()
        for i, p in enumerate(paths):
            results.append(check_file(ROOT, p))
            if progress:
                progress(i + 1)
        return results
    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor, process
    ctx = mp.get_context("fork")
    try:
        with ProcessPoolExecutor(jobs, mp_context=ctx, initializer=_init_root) as pool:
            for i, r in enumerate(pool.map(_check_one, paths, chunksize=4)):
                results.append(r)
                if progress:
                    progress(i + 1)
    except process.BrokenProcessPool:
        # multiprocessing.Pool would hang forever here; fail loudly instead
        die(f"ERROR: a file-check worker died (ROOT crash?) after {len(results)}/{len(paths)} "
            f"files; rerun with --jobs 1 to identify the file")
    return results


def find_extras(out_dir, entries):
    """chunk*.root files in the process dirs that no wrapper accounts for, per process."""
    expected = {}
    for e in entries:
        expected.setdefault(e["process"], set()).add(f"chunk_{e['chunk']}.root")
    extras = {}
    for proc, names in expected.items():
        pdir = os.path.join(out_dir, proc)
        if not os.path.isdir(pdir):
            continue
        found = [n for n in os.listdir(pdir) if n.startswith("chunk") and n.endswith(".root")]
        unexpected = sorted(n for n in found if n not in names)
        if unexpected:
            extras[proc] = [os.path.join(pdir, n) for n in unexpected]
    return extras


def write_resubmit(condor_dir, resubmit_dir, bad_entries):
    """resubmit.txt (wrapper paths) + resubmit.sub (stage1.sub with the queue line redirected)."""
    refuse_if_protected(resubmit_dir, "resubmit files")
    os.makedirs(resubmit_dir, exist_ok=True)
    txt = os.path.join(resubmit_dir, "resubmit.txt")
    sub = os.path.join(resubmit_dir, "resubmit.sub")
    with open(txt, "w") as f:
        f.write("\n".join(e["wrapper"] for e in bad_entries) + "\n")
    src = os.path.join(condor_dir, "stage1.sub")
    if not os.path.isfile(src):
        print(f"WARNING: {src} not found; wrote {txt} only")
        return txt, None
    lines, replaced = [], False
    with open(src) as f:
        for line in f:
            if line.lstrip().lower().startswith("queue"):
                line = f"queue filename from {txt}\n"
                replaced = True
            lines.append(line)
    if not replaced:
        lines.append(f"queue filename from {txt}\n")
    with open(sub, "w") as f:
        f.writelines(lines)
    return txt, sub


# --------------------------------------------------------------------------- main
def main():
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)   # `| head` must not raise BrokenPipeError
    ap = argparse.ArgumentParser(
        description="Validate the chunk outputs of a submit_stage1.py condor fan-out.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Layout")[0].split("\n", 2)[2])
    ap.add_argument("--ecm", required=True, type=int, help="240 or 365")
    ap.add_argument("--flavor", required=True, help="mumu, ee or qq")
    ap.add_argument("--stage", default="BDT_analysis_samples",
                    help="stage dir name: BDT_analysis_samples (default), MVAInputs, MVA_ntuples, ...")
    ap.add_argument("--condor-dir", help=f"override {SDCC_BASE}/S<ecm>/<flavor>/condor/<stage>")
    ap.add_argument("--out-dir", help=f"override {SDCC_BASE}/S<ecm>/<flavor>/<stage>")
    ap.add_argument("--json", help="write the full per-chunk report to this JSON file")
    ap.add_argument("--write-resubmit", action="store_true",
                    help="write resubmit.txt + resubmit.sub for the bad chunks")
    ap.add_argument("--resubmit-dir", help="where to write the resubmit files (default: --condor-dir)")
    ap.add_argument("--jobs", type=int, default=4,
                    help="parallel file-checking workers (default 4; 1 = in-process)")
    ap.add_argument("--strict", action="store_true",
                    help="also fail on warnings (EXTRA files, SEL_MISMATCH)")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="list every chunk (default: only problems, NO_LOG and warnings)")
    args = ap.parse_args()

    condor_dir = os.path.abspath(args.condor_dir or f"{SDCC_BASE}/S{args.ecm}/{args.flavor}/condor/{args.stage}")
    out_dir    = os.path.abspath(args.out_dir    or f"{SDCC_BASE}/S{args.ecm}/{args.flavor}/{args.stage}")
    log_dir    = os.path.join(condor_dir, "log")
    if args.json:
        refuse_if_protected(args.json, "the JSON report")
    resubmit_dir = os.path.abspath(args.resubmit_dir or condor_dir)
    if args.write_resubmit:
        refuse_if_protected(resubmit_dir, "resubmit files")
    if not os.path.isdir(condor_dir):
        die(f"ERROR: condor dir not found: {condor_dir}")
    if not os.path.isdir(out_dir):
        die(f"ERROR: output dir not found: {out_dir}")

    entries = read_wrappers(condor_dir)
    by_key, by_idx, clusters, n_logs = index_logs(log_dir)

    print(f"check_chunks: S{args.ecm}/{args.flavor}/{args.stage}")
    print(f"  condor dir : {condor_dir}")
    print(f"  output dir : {out_dir}")
    print(f"  wrappers   : {len(entries)} in wrappers.txt; "
          f"{sum(1 for e in entries if not e['wrapper_exists'])} wrapper file(s) not found")
    print(f"  logs       : {n_logs} .err in {len(clusters)} cluster(s) {clusters}"
          f"{'' if os.path.isdir(log_dir) else '  (no log dir)'}")

    t0 = time.time()
    paths = [os.path.join(out_dir, chunk_key(e["process"], e["chunk"])) for e in entries]

    def progress(n):
        if args.verbose and n % 200 == 0:
            print(f"  ... {n}/{len(entries)} files checked ({time.time()-t0:.1f} s)")

    results = check_files(paths, max(1, args.jobs), progress)

    chunks = []
    for e, path, (status, nent, ep, es, note) in zip(entries, paths, results):

        log, foreign = resolve_log(by_key, by_idx, e)
        cluster = errpath = log_events = log_selected = log_local = None
        if log:
            cluster, _, errpath, info = log
            log_events, log_selected, log_local = info["events"], info["selected"], info["local"]
        if log is None:
            log_status = "foreign" if foreign else "missing"
        elif log_events is None:
            log_status = "no_count"
        else:
            log_status = "ok"

        sel_mismatch = False
        if status in ("OK", "EMPTY_TREE"):
            if log_events is not None and ep != log_events:
                status = "EP_MISMATCH"
                note = f"eventsProcessed {ep} != log {log_events}"
            elif log_status != "ok":
                status = "NO_LOG"
                note = {"missing": "no .err log",
                        "foreign": f"log/*.{e['idx']}.err belong(s) to another job (resubmit cluster?)",
                        }.get(log_status, "log has no event count (job died early?)")
            elif log_selected is not None and nent != log_selected:
                sel_mismatch = True
                note = f"entries {nent} != log result events {log_selected}"

        chunks.append({
            "idx": e["idx"], "process": e["process"], "chunk": e["chunk"],
            "file": path, "wrapper": e["wrapper"], "wrapper_exists": e["wrapper_exists"],
            "status": status, "entries": nent, "eventsProcessed": ep, "eventsSelected": es,
            "log": errpath, "cluster": cluster, "log_status": log_status,
            "log_events": log_events, "log_selected": log_selected, "log_local": log_local,
            "sel_mismatch": sel_mismatch, "note": note,
        })
    dt = time.time() - t0
    print(f"  checked    : {len(chunks)} chunk files in {dt:.1f} s ({max(1, args.jobs)} worker(s))")

    extras = find_extras(out_dir, entries)
    n_extra = sum(len(v) for v in extras.values())
    n_selmm = sum(1 for c in chunks if c["sel_mismatch"])

    # ---- per-chunk listing
    def fmt(c):
        return (f"  {c['idx']:5d}  {c['status']:<11s} {chunk_key(c['process'], c['chunk']):<58s} "
                f"{'-' if c['entries'] is None else c['entries']:>9} "
                f"{'-' if c['eventsProcessed'] is None else c['eventsProcessed']:>10} "
                f"{'-' if c['log_events'] is None else c['log_events']:>10} "
                f"{'-' if c['cluster'] is None else c['cluster']:>8}  {c['note']}")
    listed = [c for c in chunks if args.verbose or c["status"] not in ("OK", "EMPTY_TREE") or c["sel_mismatch"]]
    if listed:
        print(f"\n{'Chunks' if args.verbose else 'Chunks needing attention'} "
              f"({len(listed)}):\n  {'idx':>5s}  {'status':<11s} {'process/chunk':<58s} "
              f"{'entries':>9s} {'evProc':>10s} {'logEvents':>10s} {'cluster':>8s}  note")
        for c in listed:
            print(fmt(c))
    if extras:
        print(f"\nWARNING: {n_extra} EXTRA chunk file(s) not produced by this fan-out "
              f"(fccanalysis final would glob them - remove/move them):")
        for proc, files in sorted(extras.items()):
            for f in files:
                print(f"    {f}")

    # ---- per-process summary
    procs = {}
    for c in chunks:
        p = procs.setdefault(c["process"], {"jobs": 0, "ok": 0, "empty": 0, "nolog": 0, "bad": 0,
                                            "eventsProcessed": 0, "entries": 0, "extra": 0})
        p["jobs"] += 1
        if c["status"] == "OK":
            p["ok"] += 1
        elif c["status"] == "EMPTY_TREE":
            p["empty"] += 1
        elif c["status"] == "NO_LOG":
            p["nolog"] += 1
        else:
            p["bad"] += 1
        p["eventsProcessed"] += c["eventsProcessed"] or 0
        p["entries"] += c["entries"] or 0
    for proc, files in extras.items():
        procs[proc]["extra"] = len(files)
    tot = {k: sum(p[k] for p in procs.values()) for k in
           ("jobs", "ok", "empty", "nolog", "bad", "eventsProcessed", "entries", "extra")}

    print(f"\nPer process:\n  {'process':<40s} {'jobs':>5s} {'ok':>5s} {'empty':>5s} {'nolog':>5s} "
          f"{'bad':>5s} {'sum eventsProcessed':>20s} {'sum entries':>13s}")
    for proc in sorted(procs):
        p = procs[proc]
        flag = "" if p["bad"] == 0 else "  <-- BAD"
        flag += "" if p["extra"] == 0 else f"  (+{p['extra']} extra)"
        print(f"  {proc:<40s} {p['jobs']:5d} {p['ok']:5d} {p['empty']:5d} {p['nolog']:5d} "
              f"{p['bad']:5d} {p['eventsProcessed']:20,d} {p['entries']:13,d}{flag}")
    print(f"  {'TOTAL':<40s} {tot['jobs']:5d} {tot['ok']:5d} {tot['empty']:5d} {tot['nolog']:5d} "
          f"{tot['bad']:5d} {tot['eventsProcessed']:20,d} {tot['entries']:13,d}")

    # ---- overall summary
    hist = {s: sum(1 for c in chunks if c["status"] == s) for s in ALL_STATUSES}
    bad_entries = [c for c in chunks if c["status"] in BAD_STATUSES]
    n_bad = len(bad_entries)
    n_warn = n_extra + n_selmm
    print(f"\nSummary: {len(chunks)} chunks | " +
          ", ".join(f"{s} {hist[s]}" for s in ALL_STATUSES if hist[s] or s in ("OK", "EMPTY_TREE")) +
          f" | bad {n_bad} | warnings: EXTRA {n_extra}, SEL_MISMATCH {n_selmm}")

    # ---- resubmit files
    resub = None
    if args.write_resubmit:
        if bad_entries:
            txt, sub = write_resubmit(condor_dir, resubmit_dir, bad_entries)
            resub = {"txt": txt, "sub": sub, "n": len(bad_entries)}
            print(f"Resubmit : {len(bad_entries)} wrapper(s) -> {txt}\n"
                  f"           submit with: condor_submit {sub}")
        else:
            print("Resubmit : nothing to resubmit (no bad chunks); resubmit files not written")

    # ---- JSON
    if args.json:
        report = {
            "ecm": args.ecm, "flavor": args.flavor, "stage": args.stage,
            "condor_dir": condor_dir, "out_dir": out_dir, "log_dir": log_dir,
            "clusters": clusters, "n_logs": n_logs, "n_wrappers": len(entries),
            "elapsed_s": round(dt, 2),
            "status_counts": hist, "n_bad": n_bad,
            "extra_files": extras, "n_sel_mismatch": n_selmm,
            "processes": procs, "totals": tot,
            "resubmit": resub,
            "chunks": chunks,
        }
        os.makedirs(os.path.dirname(os.path.abspath(args.json)) or ".", exist_ok=True)
        with open(args.json, "w") as f:
            json.dump(report, f, indent=1)
        print(f"JSON     : {args.json}")

    fail = n_bad > 0 or (args.strict and n_warn > 0)
    print(f"RESULT   : {'FAIL' if fail else 'PASS'}"
          + ("" if n_bad == 0 else f" ({n_bad} bad chunk(s))")
          + ("" if n_warn == 0 else f" [{n_warn} warning(s){' - fatal with --strict' if fail and n_bad == 0 else ''}]"))
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
