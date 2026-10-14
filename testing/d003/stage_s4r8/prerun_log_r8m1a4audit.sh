#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a4audit; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# prerun_log_r8m1a4audit.sh -- appends one pre-run record to $EV/PRERUN_CHECKS_R8_M1a4AUDIT.txt.  New file (r8m1a4audit).
# The forbidden-pattern grep is run with the grep tool over the script before this script is called.
# This script records: script name, UTC time, grep hit count, and the script's sha256 at the time of the record.
#   sh testing/d003/safe_run.sh p05-s4r8/m1a4audit -- sh testing/d003/stage_s4r8/prerun_log_r8m1a4audit.sh <script_name> <grep_hits>
set -u
SCRIPT=${1:?"script name"}
HITS=${2:?"grep hit count"}
SCRIPT_PATH="$REPO/testing/d003/stage_s4r8/$SCRIPT"
test -f "$SCRIPT_PATH" || { echo "prerun_log_r8m1a4audit: missing $SCRIPT_PATH" >&2; exit 2; }
SHA=$(sha256sum "$SCRIPT_PATH" | awk '{print $1}')
printf '%s\tutc=%s\tgrep_hits=%s\tscript_sha256=%s\tscope=testing/d003/stage_s4r8/\n' "$SCRIPT" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$HITS" "$SHA" >> "$EV/PRERUN_CHECKS_R8_M1a4AUDIT.txt"
echo "prerun_log_r8m1a4audit: $SCRIPT grep_hits=$HITS sha256=$SHA"
exit 0
