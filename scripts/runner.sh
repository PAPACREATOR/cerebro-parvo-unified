#!/usr/bin/env bash
# scripts/runner.sh - simple shell runner that invokes the Python job runner, with locking and logging
# Usage: ./scripts/runner.sh <process> <text> <run_dir>
set -euo pipefail
proc="$1"
text="$2"
run_dir="$3"
lockfile="$run_dir/.lock"
logfile="$run_dir/runner.log"
mkdir -p "$run_dir"
# simple flock by creating directory or file
if [ -e "$lockfile" ]; then
  echo "Run already in progress (lockfile exists): $lockfile" | tee -a "$logfile"
  exit 1
fi
# create lock
trap 'rm -f "$lockfile"' EXIT
echo $$ > "$lockfile"
# persist invocation
echo "runner start: $(date -u)" | tee -a "$logfile"
echo "process: $proc" | tee -a "$logfile"
echo "text: $text" | tee -a "$logfile"
# call python runner
python -m nexus.run_job --process "$proc" --text "$text" --run-dir "$run_dir" | tee -a "$logfile"
rc=$?
if [ $rc -eq 0 ]; then
  echo "runner: OK" | tee -a "$logfile"
  exit 0
elif [ $rc -eq 2 ]; then
  echo "runner: UNKNOWN (missing tools or needs clarification)" | tee -a "$logfile"
  exit 2
else
  echo "runner: FAIL (exit $rc)" | tee -a "$logfile"
  exit $rc
fi
