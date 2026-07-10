import os
import re
from glob import glob

# Base path containing the timestamp folders
base_log_dir = "/afs/cern.ch/user/d/dduan/private/FCCWorkplace/FCCAnalyses-winter2023/BatchOutputs"

# RegEx to find the exit code in HTCondor .log files
exit_code_re = re.compile(r"Normal termination \(return value (\d+)\)")

failed_jobs = []

print("Scanning nested timestamp directories for HTCondor logs...")

# Using '*/' or '**/' allows us to dig into the subdirectories
# base_log_dir + "/*/*.log" searches every subfolder inside base_log_dir
log_files = glob(os.path.join(base_log_dir, "*", "*", "*.log"))

if not log_files:
    print("No .log files found. Check your paths or if jobs have generated logs yet.")

for log_path in log_files:
    # Get the parent directory name (the timestamp folder) for cleaner printing
    timestamp_dir = os.path.basename(os.path.dirname(log_path))
    job_file_name = os.path.basename(log_path)
    
    with open(log_path, "r") as f:
        content = f.read()
        match = exit_code_re.search(content)
        
        if match:
            exit_code = int(match.group(1))
            if exit_code != 0:
                print(f"❌ [{timestamp_dir}] {job_file_name} failed with Exit Code {exit_code}")
                # Store the absolute path prefix so we can find the matching .err file later
                failed_jobs.append(log_path.replace(".log", ""))
        elif "Abnormal termination" in content:
            print(f"💀 [{timestamp_dir}] {job_file_name} terminated abnormally")
            failed_jobs.append(log_path.replace(".log", ""))

# Extract snippets from corresponding .err files for the failures
if failed_jobs:
    print("\n=== Error Snippets from Timestamps ===")
    for job_prefix in failed_jobs:
        err_path = f"{job_prefix}.error"
        
        # Pull out relative paths for a cleaner display print
        relative_err_path = os.path.relpath(err_path, base_log_dir)
        
        if os.path.exists(err_path) and os.path.getsize(err_path) > 0:
            print(f"\n--- {relative_err_path} ---")
            with open(err_path, "r") as err_file:
                lines = err_file.readlines()
                for line in lines[-10:]:  # Last 10 lines
                    print(line.strip())
        else:
            print(f"\n--- {relative_err_path} is empty or missing ---")
else:
    print("\n✅ All jobs in all timestamp folders finished successfully!")