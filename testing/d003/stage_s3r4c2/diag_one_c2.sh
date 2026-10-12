#!/bin/sh
# diag_one_c2.sh -- P05-S3R4 CONT2: diagnose the malformed rows of RESULTS_S3R4C2_C_POLY.tsv (new file).
#
#   sh testing/d003/safe_run.sh p05-s3r4c2 -- sh testing/d003/stage_s3r4c2/diag_one_c2.sh
#
# Re-runs ONE combination (closed2d, NG 1, tree F2) with the same environment as run_c_poly_c2.sh, into a
# separate diagnostic directory $EV/diag_one/.  It prints (into $EV/diag_one/report.txt) the number of lines
# written by the printf of one() and the exact bytes of that line.  It does not touch RESULTS_S3R4C2_C_POLY.tsv.
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
DRV_F2=$EV/drivers/poly-F2/driver
D=$EV/diag_one
OUT=$D/report.txt
mkdir -p "$D" || exit 2
{
printf 'utc\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
env -i PATH="$PATH" FMM_MODE=closed2d S4FMM_NG=1 S4FMM_DUMP_DIR="$D" "$DRV_F2" pattern both 4 3 > "$D/stdout.txt" 2> "$D/stderr.txt"
printf 'driver_rc\t%s\n' "$?"
printf 'stdout_lines\t%s\n' "$(wc -l < "$D/stdout.txt")"
printf 'RC_first_line:\n'
grep -n '^RC first' "$D/stdout.txt"
printf 'RC_retry_line:\n'
grep -n '^RC retry' "$D/stdout.txt"
printf 'RC_first_cat_A:\n'
grep '^RC first' "$D/stdout.txt" | cat -A
printf 'RC_retry_cat_A:\n'
grep '^RC retry' "$D/stdout.txt" | cat -A
printf 'sed_RF:\n'
sed -n 's/^RC first \(-*[0-9][0-9]*\)[[:space:]]*$/\1/p' "$D/stdout.txt" | head -1 | cat -A
printf 'sed_RR:\n'
sed -n 's/^RC retry \(-*[0-9][0-9]*\)[[:space:]]*$/\1/p' "$D/stdout.txt" | head -1 | cat -A
} > "$OUT" 2>&1
echo "diag_one_c2 written: $OUT"
exit 0
