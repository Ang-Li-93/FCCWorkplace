"""HTCondor submission of Python jobs at SDCC (PLAN.md rule 7).

Same pattern as the repository's ZH_XSec submitter: one wrapper script per job,
a clean worker environment that sources the repository ``setup.sh``, and output
written directly to the shared GPFS area. Settings come from the ``batch`` block
of a study configuration.
"""
import os
import subprocess
import sys
from pathlib import Path

ANALYSIS_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ANALYSIS_ROOT.parents[1]
sys.path.insert(0, str(ANALYSIS_ROOT))


def write_jobs(job_dir, commands, batch_cfg, setup="setup.sh"):
    """Write one wrapper per command plus ``jobs.sub``; return the submit file path.
    Commands run from the analysis root after sourcing ``setup`` from the repository root
    (setup.sh: Key4hep 2026-04-08 for qtomo; setup_hbs.sh: winter2023 stack for stage1)."""
    job_dir = Path(job_dir).resolve()
    (job_dir / "log").mkdir(parents=True, exist_ok=True)
    wrappers = []
    for i, cmd in enumerate(commands):
        wrapper = job_dir / f"job_{i:04d}.sh"
        wrapper.write_text("#!/bin/bash\nset -e\n"
                           f"source {REPO_ROOT}/{setup} >/dev/null 2>&1\n"
                           f"cd {ANALYSIS_ROOT}\n{cmd}\n")
        wrapper.chmod(0o755)
        wrappers.append(str(wrapper))
    (job_dir / "wrappers.txt").write_text("\n".join(wrappers) + "\n")
    sub = job_dir / "jobs.sub"
    sub.write_text(
        "executable            = $(filename)\n"
        f"output                = {job_dir}/log/$(Cluster).$(Process).out\n"
        f"error                 = {job_dir}/log/$(Cluster).$(Process).err\n"
        f"log                   = {job_dir}/log/$(Cluster).log\n"
        "getenv                = False\n"
        "request_cpus          = 1\n"
        f"request_memory        = {batch_cfg['request_memory']}\n"
        f"requirements          = {batch_cfg['requirements']}\n"
        f"accounting_group      = {batch_cfg['accounting_group']}\n"
        f"accounting_group_user = {os.environ['USER']}\n"
        "should_transfer_files = NO\n"
        f"queue filename from {job_dir}/wrappers.txt\n")
    return sub


def submit(sub):
    """Submit and return condor_submit's stdout (success is 'submitted to cluster')."""
    out = subprocess.run(["condor_submit", str(sub)], check=True, capture_output=True, text=True)
    if "submitted to cluster" not in out.stdout:
        raise RuntimeError(f"condor_submit did not confirm submission:\n{out.stdout}\n{out.stderr}")
    return out.stdout
