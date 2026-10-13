#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# prerun_log_r8.sh -- appends one pre-run check record to $EV/PRERUN_CHECKS_R8_M0.txt (brief section 0.2).
# The grep itself is run with the grep tool over testing/d003/stage_s4r8/ before this script is called;
# this script only records the script name, the UTC time and the hit count that the grep returned.
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/prerun_log_r8.sh p05-s4r8 <script_name> <grep_hits>
set -u
SCRIPT=${2:?"script name"}
HITS=${3:?"grep hit count"}
printf '%s\tutc=%s\tgrep_hits=%s\tscope=testing/d003/stage_s4r8/\n' "$SCRIPT" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$HITS" >> "$EV/PRERUN_CHECKS_R8_M0.txt"
echo "prerun_log_r8: $SCRIPT grep_hits=$HITS"
exit 0
