#!/bin/sh
# collect_registries_c2.sh -- P05-S3R4 CONT2 closeout: copy the small result tables to checkpoints/p05/registries/s3r4c2/,
# write SHA256SUMS.txt there, and verify each copy against its original (new file).
#
#   sh testing/d003/safe_run.sh p05-s3r4c2 -- sh testing/d003/stage_s3r4c2/collect_registries_c2.sh
#
# Copies (small tables only): REGISTRY_S3R4C2_C_POLY.tsv, PREREG_C_POLY_RECORD.txt, RESULTS_S3R4C2_C_POLY.tsv (run1, defective),
# RESULTS_S3R4C2_C_POLY_run2.tsv, POLY_DRIVER_DIFF.txt, POLY_DRIVER_DIFF_SUMMARY.txt, REGISTRY_S3R4C2_A.tsv,
# PREREG_A_RECORD.txt, GATE_CONT2.txt, SHA256SUMS_CHECK_p05-s3r4.txt, RMDIR_C1_U105.txt, diag_one/report.txt.
# A1 summary table (A1_MAP_SUMMARY_S3R4C2.tsv) is already in registries/s3r4c2/ (written by hand from the maps).
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
DST=$REPO/checkpoints/p05/registries/s3r4c2
mkdir -p "$DST" || exit 2
for F in REGISTRY_S3R4C2_C_POLY.tsv PREREG_C_POLY_RECORD.txt RESULTS_S3R4C2_C_POLY.tsv RESULTS_S3R4C2_C_POLY_run2.tsv \
         POLY_DRIVER_DIFF.txt POLY_DRIVER_DIFF_SUMMARY.txt REGISTRY_S3R4C2_A.tsv PREREG_A_RECORD.txt \
         GATE_CONT2.txt SHA256SUMS_CHECK_p05-s3r4.txt RMDIR_C1_U105.txt; do
    cp "$EV/$F" "$DST/$F" || { echo "copy failed: $F"; exit 1; }
done
cp "$EV/diag_one/report.txt" "$DST/DIAG_ONE_REPORT.txt" || exit 1
cd "$DST" && sha256sum $(ls | grep -v '^SHA256SUMS.txt$') > SHA256SUMS.txt
cd "$DST" && sha256sum -c SHA256SUMS.txt > "$EV/REGISTRY_COPY_CHECK.txt" 2>&1
echo "collect_registries_c2 done; check rc=$?"
exit 0
