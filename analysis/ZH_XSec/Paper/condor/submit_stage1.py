#!/usr/bin/env python3
"""
SDCC HTCondor submitter for the ZH_XSec Paper stage1 scripts (stage1_analysis_ntuples.py,
or stage1_training_ntuples.py with --stage MVA_ntuples) on the winter2023 stack.

Why custom: the winter2023 framework's built-in runBatch emits CERN-only condor config
(+JobFlavour / +AccountingGroup / eos output). SDCC needs accounting_group=group_usfcc
(+accounting_group_user) and local GPFS output. This fans out one `fccanalysis run` per
chunk (which works with the old-style scripts), reading winter2023 samples over xrootd
and writing ntuples to GPFS.

Per-process file lists come from xrdfs over eospublic; chunk counts come from the
analysis script's processList (extracted via AST, so we don't import ROOT here).

Usage:
  python submit_stage1.py S240/mumu/stage1_analysis_ntuples.py [--dry-run] [--queue tomorrow] [--max-files-per-job N]
  python submit_stage1.py S240/qq/stage1_training_ntuples.py --stage MVA_ntuples

Output: <SDCC_BASE>/S<ecm>/<flavor>/BDT_analysis_samples/<process>/chunk_<i>.root
(ecm/flavor are inferred from the script path .../Paper/S<ecm>/<flavor>/...).
"""
import argparse
import ast
import os
import subprocess
import sys

LOCAL_DIR   = "/gpfs/mnt/gpfs01/usfcc/ali3/FCCWorkplace"
FCCANA_DIR  = f"{LOCAL_DIR}/FCCAnalyses-winter2023"
KEY4HEP     = "/cvmfs/sw.hsf.org/key4hep/setup.sh -r 2024-03-10"
SDCC_BASE   = "/gpfs/mnt/gpfs01/usfcc/ali3/storage/ZH_XSec_Paper"
XRD         = "root://eospublic.cern.ch/"
SAMPLE_BASE = "/eos/experiment/fcc/ee/generation/DelphesEvents/winter2023/IDEA"
ACCT_GROUP  = "group_usfcc"


def extract_processlist(script_path):
    """
    Return (processList dict, prodTag str) from the analysis script without importing it.

    The config section (everything before the first import, i.e. before the ROOT/user
    code) is executed statement by statement in an isolated namespace, so processList
    may be a literal dict (leptonic scripts) or built in loops (qq scripts, where a
    plain ast.literal_eval of the `processList = {}` seed would yield zero jobs).
    """
    src = open(script_path).read()
    tree = ast.parse(src)
    ns = {}
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            break  # config section ends where the user code (ROOT etc.) starts
        exec(compile(ast.Module(body=[node], type_ignores=[]), script_path, "exec"), ns)
    plist = ns.get("processList")
    if not plist:
        sys.exit("ERROR: could not find a non-empty processList in %s" % script_path)
    return plist, ns.get("prodTag"), ns.get("outputDir")


def list_files(process, sample_base=SAMPLE_BASE):
    """xrdfs ls a winter2023 sample dir; return full xrootd file URLs (real events_*.root)."""
    cmd = ["xrdfs", "root://eospublic.cern.ch", "ls", f"{sample_base}/{process}"]
    try:
        out = subprocess.check_output(cmd, text=True, timeout=120)
    except Exception as e:
        print(f"  WARNING: xrdfs failed for {process}: {e}")
        return []
    files = []
    for line in out.splitlines():
        line = line.strip()
        if line.endswith(".root") and "/events_" in line and "sys.v" not in line:
            files.append(XRD + line)
    return files


def chunk(lst, n):
    """Split lst into at most n contiguous chunks (n>=1)."""
    n = max(1, min(n, len(lst)))
    k, m = divmod(len(lst), n)
    return [lst[i*k + min(i, m):(i+1)*k + min(i+1, m)] for i in range(n)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--queue", default="tomorrow", help="+JobFlavour (e.g. workday, tomorrow)")
    ap.add_argument("--max-files-per-job", type=int, default=0,
                    help="cap files per job (overrides processList chunks if smaller)")
    ap.add_argument("--stage", default="BDT_analysis_samples",
                    help="output stage directory name (e.g. MVA_ntuples for the training treemaker)")
    args = ap.parse_args()

    script = os.path.abspath(args.script)
    parts = script.split(os.sep)
    ecm    = next(p[1:] for p in parts if p.startswith("S") and p[1:].isdigit())
    flavor = parts[parts.index(f"S{ecm}") + 1]

    plist, prodtag, script_outdir = extract_processlist(script)

    # the script's own (relative) outputDir doubles as the stage tag: refuse a mismatch,
    # which would clobber another stage's chunks (e.g. training trees over analysis ntuples)
    if script_outdir and "/" not in script_outdir.strip("/") and script_outdir != args.stage:
        sys.exit(f"ERROR: script outputDir '{script_outdir}' != --stage '{args.stage}'. "
                 f"Pass --stage {script_outdir}.")

    # follow the script's campaign (e.g. winter2023_training for the leptonic treemakers)
    sample_base = SAMPLE_BASE
    if prodtag:
        tag = prodtag.strip("/")
        if tag.startswith("FCCee/"):
            tag = tag[len("FCCee/"):]
        sample_base = f"/eos/experiment/fcc/ee/generation/DelphesEvents/{tag}"

    # the qq analysis stage constructs TMVAHelperXGB at import: fail at submit time,
    # not in ~500 condor jobs, if the BDT model has not been trained/staged yet
    if flavor == "qq" and args.stage == "BDT_analysis_samples":
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        from site_config import bdt_model
        model = bdt_model(int(ecm), "qq")
        if not os.path.isfile(model):
            sys.exit(f"ERROR: qq BDT model not found: {model}\n"
                     f"Train it first (S{ecm}/qq/train_xgb.py).")

    out_base = f"{SDCC_BASE}/S{ecm}/{flavor}/{args.stage}"
    job_dir  = f"{SDCC_BASE}/S{ecm}/{flavor}/condor/{args.stage}"
    os.makedirs(job_dir, exist_ok=True)
    os.makedirs(out_base, exist_ok=True)

    print(f"script   : {script}")
    print(f"ecm/flav : {ecm} / {flavor}")
    print(f"prodTag  : {prodtag} (samples from {sample_base})")
    print(f"output   : {out_base}")
    print(f"processes: {len(plist)}")

    wrappers = []
    total_jobs = 0
    for proc, cfg in plist.items():
        files = list_files(proc, sample_base)
        if not files:
            print(f"  {proc}: NO FILES — skipped")
            continue
        frac = cfg.get("fraction", 1.0) if isinstance(cfg, dict) else 1.0
        if frac < 1.0:  # emulate the 'fraction' processList option: take the first N files
            files = files[:max(1, int(len(files) * frac))]
        nch = cfg.get("chunks", 10) if isinstance(cfg, dict) else 10
        chunks = chunk(files, nch)
        if args.max_files_per_job > 0:
            # further split any chunk exceeding the cap
            capped = []
            for c in chunks:
                for i in range(0, len(c), args.max_files_per_job):
                    capped.append(c[i:i+args.max_files_per_job])
            chunks = capped
        os.makedirs(f"{out_base}/{proc}", exist_ok=True)
        for i, c in enumerate(chunks):
            out_file = f"{out_base}/{proc}/chunk_{i}.root"
            wrap = f"{job_dir}/run_{proc}_chunk_{i}.sh"
            with open(wrap, "w") as w:
                w.write("#!/bin/bash\n")
                w.write(f"source {KEY4HEP}\n")
                w.write(f"source {FCCANA_DIR}/setup.sh\n")
                w.write(f"export FCCANA_PROCESS={proc}\n")  # process-dependent MC filters (qq channel)
                w.write(f"cd {LOCAL_DIR}\n")
                w.write(f"fccanalysis run {script} \\\n")
                w.write(f"  --output {out_file} \\\n")
                w.write(f"  --files-list {' '.join(c)}\n")
            os.chmod(wrap, 0o755)
            wrappers.append(wrap)
        print(f"  {proc}: {len(files)} files -> {len(chunks)} jobs")
        total_jobs += len(chunks)

    # write the wrapper list + condor submit description
    listfile = f"{job_dir}/wrappers.txt"
    with open(listfile, "w") as lf:
        lf.write("\n".join(wrappers) + "\n")
    sub = f"{job_dir}/stage1.sub"
    with open(sub, "w") as s:
        s.write("executable            = $(filename)\n")
        s.write(f"output                = {job_dir}/log/$(Cluster).$(Process).out\n")
        s.write(f"error                 = {job_dir}/log/$(Cluster).$(Process).err\n")
        s.write(f"log                   = {job_dir}/log/$(Cluster).log\n")
        s.write("getenv                = False\n")   # clean worker env; in-job key4hep source must run
        s.write("request_cpus          = 1\n")
        s.write("request_memory        = 4000\n")  # qq graph (4 clustering hypotheses) exceeds the 2GB default
        s.write(f'+JobFlavour           = "{args.queue}"\n')
        s.write(f"accounting_group      = {ACCT_GROUP}\n")           # SDCC group_usfcc.<user>
        s.write(f"accounting_group_user = {os.getenv('USER')}\n")
        s.write("should_transfer_files = NO\n")       # GPFS is shared; write output directly
        s.write(f"queue filename from {listfile}\n")
    os.makedirs(f"{job_dir}/log", exist_ok=True)

    print(f"\nTotal jobs: {total_jobs}")
    print(f"Submit file: {sub}")
    if args.dry_run:
        print("DRY RUN — not submitting. Inspect the .sub and a wrapper, then drop --dry-run.")
        return
    print("Submitting to SDCC condor...")
    subprocess.run(["condor_submit", sub], check=True)


if __name__ == "__main__":
    main()
