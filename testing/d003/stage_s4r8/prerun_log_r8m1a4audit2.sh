#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a4audit2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# prerun_log_r8m1a4audit2.sh -- appends one pre-run record to $EV/PRERUN_CHECKS_R8_M1a4AUDIT2.txt.  New file (r8m1a4audit2).
# The forbidden-pattern grep is run with the grep tool over the file before this script is called; the caller passes the hit count.
# The record holds: file name, UTC time, grep hit count, and the file sha256 at the time of the record.
#   sh testing/d003/safe_run.sh p05-s4r8/m1a4audit2 -- sh testing/d003/stage_s4r8/prerun_log_r8m1a4audit2.sh FILE_NAME GREP_HITS
set -u
NAME=${1:?"file name"}
HITS=${2:?"grep hit count"}
case "$NAME" in
    */*) echo "prerun_log_r8m1a4audit2: name must be a bare file name" >&2; exit 2 ;;
esac
FILE_PATH="$REPO/testing/d003/stage_s4r8/$NAME"
test -f "$FILE_PATH" || { echo "prerun_log_r8m1a4audit2: missing $FILE_PATH" >&2; exit 2; }
SHA=$(sha256sum "$FILE_PATH" | awk '{print $1}')
printf '%s\tutc=%s\tgrep_hits=%s\tsha256=%s\tscope=testing/d003/stage_s4r8/\n' "$NAME" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$HITS" "$SHA" >> "$EV/PRERUN_CHECKS_R8_M1a4AUDIT2.txt"
echo "prerun_log_r8m1a4audit2: $NAME grep_hits=$HITS sha256=$SHA"
exit 0
