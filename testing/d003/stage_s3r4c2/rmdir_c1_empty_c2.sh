#!/bin/sh
# rmdir_c1_empty_c2.sh -- P05-S3R4 CONT2, U105: remove the empty directory testing/d003/stage_s3r4c1/ (new file).
#
#   sh testing/d003/safe_run.sh p05-s3r4c2 -- sh testing/d003/stage_s3r4c2/rmdir_c1_empty_c2.sh
#
# rmdir only (it refuses a non-empty directory; then this script stops and the round reports).
# The log records the ls -d and the entry count before and after.
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
D=$REPO/testing/d003/stage_s3r4c1
OUT=$EV/RMDIR_C1_U105.txt
{
printf 'utc_before\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'ls_d_before:\n'
ls -d testing/d003/stage_s3r4c1
printf 'entries_before\t%s\n' "$(ls -A testing/d003/stage_s3r4c1 | wc -l)"
rmdir "$D"
RC=$?
printf 'rmdir_rc\t%s\n' "$RC"
printf 'utc_after\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'ls_d_after:\n'
ls -d testing/d003/stage_s3r4c1
printf 'ls_d_after_rc\t%s\n' "$?"
} > "$OUT" 2>&1
echo "rmdir_c1_empty_c2 written: $OUT"
exit 0
