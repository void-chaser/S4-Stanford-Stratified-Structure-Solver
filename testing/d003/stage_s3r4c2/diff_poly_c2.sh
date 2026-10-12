#!/bin/sh
# diff_poly_c2.sh -- P05-S3R4 CONT2: line diff of the poly driver against its source (new file).
#
#   sh testing/d003/safe_run.sh p05-s3r4c2 -- sh testing/d003/stage_s3r4c2/diff_poly_c2.sh
#
# Writes $EV/POLY_DRIVER_DIFF.txt (unified diff, pattern branch only is allowed to differ)
# and $EV/POLY_DRIVER_DIFF_SUMMARY.txt (counts of changed lines, and sha256 of both files).
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
SRC=$REPO/testing/d003/stage_s4/driver_r6b_state.cpp
NEW=$REPO/testing/d003/stage_s3r4c2/driver_s3r4c2_poly.cpp
diff -u "$SRC" "$NEW" > "$EV/POLY_DRIVER_DIFF.txt" 2>&1
RC=$?
{
printf 'diff_rc\t%s\n' "$RC"
printf 'removed_lines\t%s\n' "$(grep -c '^-[^-]' "$EV/POLY_DRIVER_DIFF.txt")"
printf 'added_lines\t%s\n' "$(grep -c '^+[^+]' "$EV/POLY_DRIVER_DIFF.txt")"
printf 'hunks\t%s\n' "$(grep -c '^@@' "$EV/POLY_DRIVER_DIFF.txt")"
printf 'sha256_source\t%s\n' "$(sha256sum "$SRC" | cut -d' ' -f1)"
printf 'sha256_poly\t%s\n' "$(sha256sum "$NEW" | cut -d' ' -f1)"
} > "$EV/POLY_DRIVER_DIFF_SUMMARY.txt" 2>&1
echo "diff_poly_c2 done rc=$RC"
exit 0
