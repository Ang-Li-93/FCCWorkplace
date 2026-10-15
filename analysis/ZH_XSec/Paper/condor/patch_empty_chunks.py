#!/usr/bin/env python3
"""
patch_empty_chunks.py - repair 'key-less' stage1 chunk files of a condor stage.

Background
----------
The winter2023 `fccanalysis run` writes its output with RDataFrame::Snapshot (implicit
multithreading on) and then re-opens the file to add the TParameter<int> 'eventsProcessed'
and 'eventsSelected'.  When the selection keeps ZERO events (e.g. at 365 GeV the purely-
dileptonic backgrounds have no hadronic acceptance) the multithreaded Snapshot writes NO
'events' key at all, so the job leaves a file that holds only the two parameters (or, for
a hand-made file, nothing).  The stage2 `fccanalysis final` step aborts on a chunk without
an 'events' tree, and the sample normalization is the sum of 'eventsProcessed' over the
chunks, so such a chunk has to be replaced by an EMPTY tree with the full branch list that
carries the correct eventsProcessed.  This is what was done by hand for the July-2026
campaign, cf. S365/qq/BDT_analysis_samples.jul2026/wzp6_gaga_ee_60_ecm365/chunk_0.root
(events: 0 entries, 29 branches; eventsProcessed = 1100000).  check_chunks.py reports such
files as NO_TREE.

What it does
------------
Expected outputs come from <condor-dir>/wrappers.txt (run_<process>_chunk_<i>.sh; the
position among the non-blank lines = condor $(Process) index).  For every
<out-dir>/<process>/chunk_<i>.root:
  * the file has an 'events' tree               -> OK / OK_EMPTY: never touched
  * the file exists but has no 'events' tree    -> KEYLESS  (candidate)
  * ROOT cannot read it (0 bytes, not a ROOT
    file, truncated, recovered)                 -> ZOMBIE   (candidate)
  * the file is missing                         -> MISSING: reported separately, patched
                                                   only with --apply --include-missing
The job log is <condor-dir>/log/<cluster>.<idx>.err whose 'Output file path' names this
chunk (several clusters are fine, the newest matching log wins; a log under another index,
e.g. from a partial resubmission, is found by scanning).  A candidate is patchable only if
that log is complete and clean:
  - it has the input count: '----> INFO: Number of local events: N', or the two-line form
    'Number of events: - original: O / - local: N' that the runner prints when the inputs
    already carry an eventsProcessed key (then O is what it stores, as in run_analysis.py:
    nevents_orig if nevents_orig != 0 else evtcount_init),
  - it has the SUMMARY block, 'Total events processed' equals N and 'No. result events'
    is 0 (a key-less file of a job that DID select events is corrupt: rerun it),
  - it has no Python traceback and no error line other than the known-benign xrootd
    'Error in <TNetXNGFile::Close>: [ERROR] Socket timeout' (printed by healthy jobs),
  - if the file itself carries eventsProcessed / eventsSelected (a real key-less file
    does), they must equal the log's value / 0.
The log, not the file, is the authority on what the job did: an unreadable (ZOMBIE) file
whose log is clean and reports 0 result events is patched like a key-less one (its content
is unusable anyway and the original is kept); with any other log it is refused.

Patch (only with --apply): <out-dir>/<process>/chunk_<i>.root is replaced by a file with
  events          TTree           = ref.CloneTree(0): same branch names/types, 0 entries
  eventsProcessed TParameter<int> = N (from the log)
  eventsSelected  TParameter<int> = 0
written to a temporary file in the same directory, verified (branch names AND types equal
to the reference, 0 entries, parameter values), then moved into place with os.replace.
The original key-less file is kept as chunk_<i>.root.keyless (never deleted; .keyless.1,
.keyless.2 ... if that name is taken).  A patched file is OK_EMPTY on the next run, so
running the tool again never touches it (idempotent).

Reference tree: --ref, else the first expected chunk of this stage (wrappers.txt order,
also outside an --only selection) whose 'events' tree is non-empty.  Every chunk of the
stage that has an 'events' tree must share one branch list, and the reference must match
it; otherwise the tool refuses to patch (exit 2) instead of writing a wrong structure.
Only when the stage has no chunk with an events tree at all is --ref taken unchecked.

Without --apply this is a DRY RUN: it only lists what would be done.

Usage (key4hep 2024-03-10 + FCCAnalyses-winter2023 environment: python3 + ROOT)
-----
  python3 condor/patch_empty_chunks.py --ecm 365 --flavor qq                    # dry run
  python3 condor/patch_empty_chunks.py --ecm 365 --flavor qq --apply
  python3 condor/patch_empty_chunks.py --ecm 240 --flavor mumu --stage MVAInputs \\
          --apply --include-missing
  python3 condor/patch_empty_chunks.py --ecm 365 --flavor qq --condor-dir D --out-dir O --ref F

Exit code: 0 = nothing left to do (no candidate, or every candidate patched);
           1 = something needs attention (candidate refused, output of a failed/incomplete
               job missing, patch failure, MISSING candidate skipped for lack of
               --include-missing);
           2 = setup error (missing wrappers.txt / log dir / reference, unusable or
               mismatching reference, inconsistent stage, protected out-dir, no PyROOT).
"""
import argparse
import fnmatch
import glob
import os
import re
import sys

SDCC_BASE = "/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper"   # as in submit_stage1.py
PROTECTED = (".jul2026", "models_backup")   # read-only reference dirs: never written to

RE_WRAPPER   = re.compile(r"^run_(?P<process>.+)_chunk_(?P<chunk>\d+)\.sh$")
# 'Number of events:\n\t- original: O\n\t- local: N' is printed when the inputs carry an
# eventsProcessed key (a later stage), 'Number of local events: N' otherwise (stage1)
RE_ORIG      = re.compile(r"Number of events:\s*\n\s*- original:\s*([\d,]+)\s*\n\s*- local:\s*([\d,]+)")
RE_LOCAL     = re.compile(r"Number of local events:\s*([\d,]+)")
RE_PROCESSED = re.compile(r"Total events processed:\s*([\d,]+)")
RE_RESULT    = re.compile(r"No\. result events:\s*([\d,]+)")
RE_OUTPATH   = re.compile(r"Output file path:\s*\n\s*(\S+)")
TRACEBACK    = "Traceback (most recent call last)"
# error lines printed by healthy July-2026 jobs (xrootd close timeout after all events were read)
BENIGN_ERRORS = (re.compile(r"Error in <TNetXNGFile::Close>"),)

ROOT = None  # imported in main() so that --help works without the analysis stack


class Job:
    """One expected chunk file of the stage."""

    def __init__(self, idx, process, chunk, wrapper, out_file):
        self.idx = idx            # condor $(Process) index = position in wrappers.txt
        self.process = process
        self.chunk = chunk
        self.wrapper = wrapper
        self.out_file = out_file
        self.tail = f"/{process}/chunk_{chunk}.root"   # how the log names the output
        self.status = None        # OK / OK_EMPTY / KEYLESS / ZOMBIE / MISSING
        self.detail = None        # entries for OK*, note for ZOMBIE/KEYLESS
        self.info = {"sig": None, "ep": None, "sel": None}   # from classify_file()
        self.log = None           # matching .err path
        self.loginfo = None       # parse_log() result
        self.reason = None        # why it cannot be patched (None = patchable)
        self.action = None        # PATCH / PATCH-MISSING / REFUSE / MISSING-FAILED
        self.result = None        # after --apply: 'patched' / 'skipped' / 'FAILED: ...'
        self.kept = None          # where the original key-less file was moved

    @property
    def n_processed(self):
        """eventsProcessed as run_analysis.py stores it: nevents_orig if != 0 else the
        SUMMARY's 'Total events processed' (falls back to the input count for display)."""
        li = self.loginfo
        if not li:
            return None
        if li["orig"]:
            return li["orig"]
        return li["processed"] if li["processed"] is not None else li["local"]


# ----------------------------------------------------------------------------- helpers
def read_text(path):
    with open(path, errors="replace") as fh:
        return fh.read()


def to_int(m, group=1):
    return int(m.group(group).replace(",", "")) if m else None


def die(msg, code=2):
    """Setup error: message on stderr, exit 2 (exit 1 is reserved for 'needs attention')."""
    print(msg, file=sys.stderr)
    sys.exit(code)


def parse_log(txt):
    """Extract the counts and the health of a job's .err text."""
    m_orig = RE_ORIG.search(txt)
    info = {
        "orig": to_int(m_orig, 1),
        "local": to_int(m_orig, 2) if m_orig else to_int(RE_LOCAL.search(txt)),
        "processed": to_int(RE_PROCESSED.search(txt)),
        "result": to_int(RE_RESULT.search(txt)),
        "traceback": TRACEBACK in txt,
        "errors": [],
        "benign": [],
    }
    for line in txt.splitlines():
        if "Error" in line or "ERROR" in line:
            if any(b.search(line) for b in BENIGN_ERRORS):
                info["benign"].append(line.strip())
            else:
                info["errors"].append(line.strip())
    return info


def judge(job):
    """Return None if the job's log (and the file's own parameters) allow patching, else a
    short reason."""
    li = job.loginfo
    if li is None:
        return "NO_LOG"
    if li["traceback"]:
        return "TRACEBACK"
    if li["errors"]:
        return "ERROR:" + li["errors"][0][:60]
    if li["local"] is None:
        return "NO_COUNT"           # no input count line: count unavailable
    if li["processed"] is None or li["result"] is None:
        return "INCOMPLETE"         # no SUMMARY block: job still running / evicted / killed
    if li["processed"] != li["local"]:
        return f"COUNT_MISMATCH(local={li['local']},processed={li['processed']})"
    if li["result"] != 0:
        return f"RESULT_NONZERO({li['result']})"   # events were selected: output is corrupt, rerun
    # a key-less file of a completed job carries the parameters the runner stored: they
    # must agree with the log, otherwise the log and the file are not the same run
    n = job.n_processed
    if job.info["ep"] is not None and job.info["ep"] != n:
        return f"FILE_EP_MISMATCH(file={job.info['ep']},log={n})"
    if job.info["sel"] is not None and job.info["sel"] != 0:
        return f"FILE_SEL_NONZERO({job.info['sel']})"
    return None


def read_wrappers(condor_dir, out_dir):
    listfile = os.path.join(condor_dir, "wrappers.txt")
    if not os.path.isfile(listfile):
        die(f"ERROR: {listfile} not found (run submit_stage1.py [--dry-run] first)")
    jobs = []
    with open(listfile) as fh:
        # condor 'queue filename from <file>' skips blank and '#' lines: $(Process) counts the rest
        lines = [ln.strip() for ln in fh if ln.strip() and not ln.lstrip().startswith("#")]
    for idx, wrapper in enumerate(lines):
        m = RE_WRAPPER.match(os.path.basename(wrapper))
        if not m:
            die(f"ERROR: cannot parse wrapper name (entry {idx + 1} of wrappers.txt): {wrapper}")
        process, chunk = m.group("process"), int(m.group("chunk"))
        out_file = os.path.join(out_dir, process, f"chunk_{chunk}.root")
        jobs.append(Job(idx, process, chunk, wrapper, out_file))
    return jobs


def branch_signature(tree):
    """[(name, class, leaf type, title)] - what 'same branches' means for the check."""
    sig = []
    for b in tree.GetListOfBranches():
        leaves = b.GetListOfLeaves()
        ltype = leaves.At(0).GetTypeName() if leaves.GetEntries() else ""
        sig.append((b.GetName(), b.GetClassName(), ltype, b.GetTitle()))
    return tuple(sig)


def open_root(path):
    """TFile.Open that returns None instead of raising (PyROOT raises OSError on a file
    ROOT cannot open) or handing back a zombie."""
    try:
        f = ROOT.TFile.Open(path, "READ")
    except OSError:
        return None
    if not f or f.IsZombie():
        return None
    return f


def classify_file(path):
    """(status, detail, info) for an expected chunk file.  info: 'sig' = branch signature
    of the events tree (OK / OK_EMPTY), 'ep' / 'sel' = eventsProcessed / eventsSelected
    values stored in the file if present (KEYLESS files of real jobs carry them)."""
    info = {"sig": None, "ep": None, "sel": None}
    if not os.path.exists(path):
        return "MISSING", None, info
    if os.path.getsize(path) == 0:
        return "ZOMBIE", "0-byte file", info
    f = open_root(path)
    if f is None:
        return "ZOMBIE", "not readable by ROOT (not a ROOT file / truncated)", info
    try:
        if f.TestBit(ROOT.TFile.kRecovered):
            return "ZOMBIE", "not closed properly (ROOT had to recover it)", info
        keys = {k.GetName(): k.GetClassName() for k in f.GetListOfKeys()}
        for name, tag in (("eventsProcessed", "ep"), ("eventsSelected", "sel")):
            if keys.get(name, "").startswith("TParameter"):
                info[tag] = int(f.Get(name).GetVal())
        if keys.get("events") != "TTree":
            shown = [f"{k}={info['ep']}" if k == "eventsProcessed" and info["ep"] is not None
                     else f"{k}={info['sel']}" if k == "eventsSelected" and info["sel"] is not None
                     else k for k in keys]
            return "KEYLESS", "keys: " + (",".join(shown) if shown else "none"), info
        t = f.Get("events")
        info["sig"] = branch_signature(t)
        n = t.GetEntries()
        return ("OK_EMPTY" if n == 0 else "OK"), n, info
    finally:
        f.Close()


class LogIndex:
    """Find the .err of a job: by condor index first, else by scanning for the output path."""

    def __init__(self, log_dir):
        self.log_dir = log_dir
        self._scan = None

    def find(self, job):
        hits = []
        for p in glob.glob(os.path.join(self.log_dir, f"*.{job.idx}.err")):
            txt = read_text(p)
            if job.tail in txt:
                hits.append((os.path.getmtime(p), p, txt))
        if not hits:   # resubmitted under another index? scan every log once
            if self._scan is None:
                self._scan = {}
                for p in glob.glob(os.path.join(self.log_dir, "*.err")):
                    txt = read_text(p)
                    m = RE_OUTPATH.search(txt)
                    if m:
                        self._scan.setdefault(m.group(1), []).append((os.path.getmtime(p), p, txt))
            for out_path, entries in self._scan.items():
                if out_path.endswith(job.tail):
                    hits.extend(entries)
        if not hits:
            return None, None
        hits.sort()
        return hits[-1][1], hits[-1][2]   # newest matching log


def open_reference(path):
    f = open_root(path)
    if f is None:
        die(f"ERROR: cannot open reference file {path}")
    t = f.Get("events")
    if not t:
        f.Close()
        die(f"ERROR: reference file {path} has no 'events' tree")
    return f, t


def describe_sig_diff(sig_a, sig_b, label_a, label_b):
    names_a = {s[0] for s in sig_a}
    names_b = {s[0] for s in sig_b}
    msg = [f"  {label_a}: {len(sig_a)} branches", f"  {label_b}: {len(sig_b)} branches"]
    only_a = sorted(names_a - names_b)
    only_b = sorted(names_b - names_a)
    if only_a:
        msg.append(f"  only in {label_a}: {', '.join(only_a[:8])}{' ...' if len(only_a) > 8 else ''}")
    if only_b:
        msg.append(f"  only in {label_b}: {', '.join(only_b[:8])}{' ...' if len(only_b) > 8 else ''}")
    if not only_a and not only_b:
        diff = [a[0] for a, b in zip(sorted(sig_a), sorted(sig_b)) if a != b]
        msg.append("  same names, different type/title for: " + ", ".join(diff[:8]))
    return "\n".join(msg)


def verify_patched(path, ref_sig, n_processed):
    problems = []
    f = open_root(path)
    if f is None:
        return ["cannot reopen the written file"]
    try:
        t = f.Get("events")
        if not t:
            problems.append("no 'events' tree")
        else:
            if t.GetEntries() != 0:
                problems.append(f"events has {t.GetEntries()} entries")
            if branch_signature(t) != ref_sig:
                problems.append("branch list differs from the reference")
        for name, val in (("eventsProcessed", n_processed), ("eventsSelected", 0)):
            p = f.Get(name)
            if not p:
                problems.append(f"missing {name}")
            elif p.GetVal() != val:
                problems.append(f"{name} = {p.GetVal()} != {val}")
    finally:
        f.Close()
    return problems


def keyless_name(path):
    keep = path + ".keyless"
    n = 1
    while os.path.exists(keep):
        keep = f"{path}.keyless.{n}"
        n += 1
    return keep


def patch(job, ref_tree, ref_sig):
    """Write the empty tree + parameters; returns None on success, else an error string."""
    n = job.n_processed
    if n is None:
        return "no event count from the log (refused)"
    d = os.path.dirname(job.out_file)
    tmp = os.path.join(d, f".{os.path.basename(job.out_file)}.patch.tmp.{os.getpid()}")
    try:
        os.makedirs(d, exist_ok=True)
        out = ROOT.TFile(tmp, "RECREATE")     # PyROOT raises OSError if it cannot be created
        if not out or out.IsZombie():
            raise RuntimeError(f"cannot create {tmp}")
        out.cd()
        tree = ref_tree.CloneTree(0)      # same branches (names/types/titles), no entries
        tree.SetDirectory(out)
        tree.Write()
        p_proc = ROOT.TParameter(int)("eventsProcessed", n)
        p_proc.Write()
        p_sel = ROOT.TParameter(int)("eventsSelected", 0)
        p_sel.Write()
        out.Close()
        problems = verify_patched(tmp, ref_sig, n)
        if problems:
            raise RuntimeError("verification failed: " + "; ".join(problems))
        if os.path.exists(job.out_file):
            job.kept = keyless_name(job.out_file)
            os.replace(job.out_file, job.kept)   # keep the original, never delete it
        os.replace(tmp, job.out_file)
        return None
    except Exception as exc:  # noqa: BLE001 - report anything, leave no temp file behind
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except OSError:
            pass
        return str(exc)


# -------------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("--ecm", required=True, help="240 or 365")
    ap.add_argument("--flavor", required=True, help="mumu, ee or qq")
    ap.add_argument("--stage", default="BDT_analysis_samples",
                    help="stage dir name: BDT_analysis_samples (default), MVA_ntuples, MVAInputs")
    ap.add_argument("--base", default=SDCC_BASE, help=f"storage base (default {SDCC_BASE})")
    ap.add_argument("--condor-dir", help="default <base>/S<ecm>/<flavor>/condor/<stage>")
    ap.add_argument("--out-dir", help="default <base>/S<ecm>/<flavor>/<stage>")
    ap.add_argument("--ref", help="reference chunk file (default: first non-empty chunk of the stage)")
    ap.add_argument("--only", action="append", default=[],
                    help="only processes matching this glob (repeatable)")
    ap.add_argument("--include-missing", action="store_true",
                    help="with --apply: also create chunks that are missing although the job log is clean")
    ap.add_argument("--apply", action="store_true", help="write the patches (default: dry run)")
    args = ap.parse_args()

    ecm = str(args.ecm).lstrip("S")
    condor_dir = args.condor_dir or f"{args.base}/S{ecm}/{args.flavor}/condor/{args.stage}"
    out_dir = args.out_dir or f"{args.base}/S{ecm}/{args.flavor}/{args.stage}"
    condor_dir, out_dir = os.path.abspath(condor_dir), os.path.abspath(out_dir)
    log_dir = os.path.join(condor_dir, "log")

    if args.apply and any(tag in out_dir for tag in PROTECTED):
        die(f"ERROR: refusing to write into protected reference dir {out_dir}")
    if not os.path.isdir(log_dir):
        die(f"ERROR: log dir {log_dir} not found")
    if not os.path.isdir(out_dir):
        die(f"ERROR: output dir {out_dir} not found")

    global ROOT
    try:
        import ROOT as _ROOT
    except ImportError:
        die("ERROR: PyROOT not available: source the key4hep 2024-03-10 stack and "
            "FCCAnalyses-winter2023/setup.sh first")
    ROOT = _ROOT
    ROOT.PyConfig.IgnoreCommandLineOptions = True
    ROOT.gROOT.SetBatch(True)
    ROOT.gErrorIgnoreLevel = ROOT.kError   # no Info/Warning chatter (recovery attempts); errors still print

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"mode      : {mode}{' (+missing)' if args.include_missing else ''}")
    print(f"condor dir: {condor_dir}")
    print(f"output dir: {out_dir}")

    all_jobs = read_wrappers(condor_dir, out_dir)
    jobs = all_jobs
    if args.only:
        jobs = [j for j in all_jobs if any(fnmatch.fnmatch(j.process, pat) for pat in args.only)]
    print(f"expected  : {len(jobs)} chunk files, {len({j.process for j in jobs})} processes")

    for j in jobs:
        j.status, j.detail, j.info = classify_file(j.out_file)
    counts = {s: sum(1 for j in jobs if j.status == s)
              for s in ("OK", "OK_EMPTY", "KEYLESS", "ZOMBIE", "MISSING")}
    print("found     : " + ", ".join(f"{k}={v}" for k, v in counts.items()))

    # every chunk with an events tree must share one branch list (the stage1 scripts write a
    # fixed list); otherwise no reference can be trusted and `final` would break anyway
    sigs = {}
    for j in jobs:
        if j.info["sig"] is not None:
            sigs.setdefault(j.info["sig"], j.out_file)
    stage_sig = next(iter(sigs)) if len(sigs) == 1 else None
    if len(sigs) > 1:
        print(f"WARNING: the chunks of this stage do not share one branch list "
              f"({len(sigs)} different ones):")
        for sig, path in sigs.items():
            print(f"  {len(sig)} branches: {path}")

    candidates = [j for j in jobs if j.status in ("KEYLESS", "ZOMBIE", "MISSING")]
    if not candidates:
        print("\nNothing to patch.")
        return 0

    # job logs and verdicts
    logs = LogIndex(log_dir)
    for j in candidates:
        j.log, txt = logs.find(j)
        j.loginfo = parse_log(txt) if txt else None
        j.reason = judge(j)
        if j.status == "MISSING":
            j.action = "PATCH-MISSING" if j.reason is None else "MISSING-FAILED"
        else:
            j.action = "PATCH" if j.reason is None else "REFUSE"

    patchable = [j for j in candidates if j.reason is None]

    # reference tree (needed only if something is patchable)
    ref_path = ref_file = ref_tree = ref_sig = None
    if patchable:
        if len(sigs) > 1:
            die("ERROR: cannot choose a reference for a stage with inconsistent branch lists "
                "(see WARNING above); fix or remove the odd chunks first")
        if args.ref:
            ref_path = os.path.abspath(args.ref)
        else:
            ok_jobs = [j for j in jobs if j.status == "OK"]
            if not ok_jobs:   # --only may have excluded every non-empty chunk: look outside it
                for j in all_jobs:
                    if j in jobs:
                        continue
                    j.status, j.detail, j.info = classify_file(j.out_file)
                    if j.status == "OK":
                        ok_jobs.append(j)
                        break
            if not ok_jobs:
                die("ERROR: no chunk of this stage has a non-empty 'events' tree; pass --ref")
            ref_path = ok_jobs[0].out_file
        ref_file, ref_tree = open_reference(ref_path)
        ref_sig = branch_signature(ref_tree)
        print(f"reference : {ref_path} ({ref_tree.GetEntries()} entries, {len(ref_sig)} branches)")
        if stage_sig is not None and ref_sig != stage_sig:
            ref_file.Close()
            die("ERROR: the reference's branch list differs from this stage's chunks; "
                "refusing to write a wrong structure\n"
                + describe_sig_diff(ref_sig, stage_sig, "reference", f"stage ({sigs[stage_sig]})"))
        if stage_sig is None:
            print("WARNING: no chunk of this stage has an 'events' tree, the reference's "
                  "branch list cannot be cross-checked: make sure it is a chunk of this stage")

    # listing
    print()
    hdr = f"{'action':<15}{'idx':>6}  {'process':<36}{'chunk':>5}  {'eventsProcessed':>15}  log / reason"
    print(hdr)
    print("-" * len(hdr))
    for j in candidates:
        n = j.n_processed
        note = os.path.basename(j.log) if j.log else "no matching log"
        if j.reason:
            note = f"{j.reason} [{note}]"
        elif j.loginfo["benign"]:
            note += " (benign xrootd close error)"
        print(f"{j.action:<15}{j.idx:>6}  {j.process:<36}{j.chunk:>5}  "
              f"{(n if n is not None else '-'):>15}  {note}")
        if j.status != "MISSING":
            print(f"{'':<15}{'':>6}  file: {j.out_file} ({j.status}: {j.detail})")

    # apply
    attention = [j for j in candidates if j.reason is not None]
    n_patched = n_failed = n_skipped = 0
    if args.apply:
        print()
        for j in patchable:
            if j.status == "MISSING" and not args.include_missing:
                j.result = "skipped (missing file, no --include-missing)"
                n_skipped += 1
            else:
                err = patch(j, ref_tree, ref_sig)
                if err:
                    j.result = "FAILED: " + err
                    n_failed += 1
                else:
                    j.result = "patched" + (f" (original kept as {j.kept})" if j.kept else " (created)")
                    n_patched += 1
            print(f"  {j.process}/chunk_{j.chunk}.root: {j.result}")
    else:
        n_skipped = sum(1 for j in patchable if j.status == "MISSING")
    if ref_file:
        ref_file.Close()

    # summary
    print("\nSUMMARY")
    print(f"  expected chunks        : {len(jobs)}")
    print(f"  ok (events tree)       : {counts['OK']} non-empty, {counts['OK_EMPTY']} empty")
    print(f"  key-less / unreadable  : {counts['KEYLESS']} / {counts['ZOMBIE']}")
    print(f"  missing                : {counts['MISSING']}")
    print(f"  patchable              : {len(patchable)} "
          f"({sum(1 for j in patchable if j.status != 'MISSING')} existing, "
          f"{sum(1 for j in patchable if j.status == 'MISSING')} missing)")
    print(f"  needs attention        : {len(attention)} "
          f"({sum(1 for j in attention if j.status != 'MISSING')} refused, "
          f"{sum(1 for j in attention if j.status == 'MISSING')} missing with no clean log: "
          f"job not run / failed / incomplete)")
    if args.apply:
        print(f"  patched / failed / skipped : {n_patched} / {n_failed} / {n_skipped}")
    else:
        print(f"  dry run: {len(patchable) - n_skipped} would be patched"
              + (f", {n_skipped} missing need --include-missing" if n_skipped else "")
              + "; add --apply")

    if attention or n_failed:
        return 1
    if args.apply:
        return 1 if n_skipped else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
