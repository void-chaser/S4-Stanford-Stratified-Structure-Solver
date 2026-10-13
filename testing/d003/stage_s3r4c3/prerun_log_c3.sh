REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# prerun_log_c3.sh -- appends one pre-run check record to $EV/PRERUN_CHECKS_C3.txt (argument: script name and result text).
# Usage: sh testing/d003/safe_run.sh p05-s3r4c3 -- sh testing/d003/stage_s3r4c3/prerun_log_c3.sh NAME RESULT
NAME=${1:?"script name"}
RESULT=${2:?"result text"}
printf '%s\t%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$NAME" "$RESULT" >> "$EV/PRERUN_CHECKS_C3.txt"
echo "logged: $NAME"
