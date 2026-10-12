#!/bin/sh
# check_sha_s3r4_c2.sh -- P05-S3R4 CONT2: verify the ES3R4-13 facts before ES3R4-15 is written (new file).
#
#   sh testing/d003/safe_run.sh p05-s3r4c2 -- sh testing/d003/stage_s3r4c2/check_sha_s3r4_c2.sh
#
# Reads the S3R4 manifest and safe_run.log of evidence/p05-s3r4 (read only) and writes only
# $EV/SHA256SUMS_CHECK_p05-s3r4.txt.  The manifest is not rewritten.
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
S=$REPO/checkpoints/p05/evidence/p05-s3r4
OUT=$EV/SHA256SUMS_CHECK_p05-s3r4.txt
{
printf 'check_utc\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'source_manifest\t%s\n' "$S/SHA256SUMS.txt"
printf 'manifest_line_safe_run_log:\n'
grep 'safe_run.log' "$S/SHA256SUMS.txt"
printf 'safe_run_log_lines\t%s\n' "$(wc -l < "$S/safe_run.log")"
printf 'safe_run_log_sha256_full\t%s\n' "$(sha256sum "$S/safe_run.log" | cut -d' ' -f1)"
printf 'safe_run_log_head60_sha256\t%s\n' "$(head -n 60 "$S/safe_run.log" | sha256sum | cut -d' ' -f1)"
printf 'safe_run_log_line61:\n'
sed -n 61p "$S/safe_run.log"
printf 'safe_run_log_line62:\n'
sed -n 62p "$S/safe_run.log"
printf 'manifest_sha256_check_read_only:\n'
(cd "$S" && sha256sum -c SHA256SUMS.txt)
} > "$OUT" 2>&1
echo "check_sha_s3r4_c2 written: $OUT"
exit 0
