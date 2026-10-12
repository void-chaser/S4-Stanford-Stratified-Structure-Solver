#!/bin/sh
# prereg_c_poly_c2.sh -- P05-S3R4 CONT2 (C polygon): write the pre-registration REGISTRY_S3R4C2_C_POLY.tsv (new file).
#
#   sh testing/d003/safe_run.sh p05-s3r4c2 -- sh testing/d003/stage_s3r4c2/prereg_c_poly_c2.sh
#
# 11 modes x NG 1, 5, 9 = 33 combinations.  Each combination: tree F2 and tree F3, poly driver, no injection.
# Expected: the call1-3 dumps of F2 and F3 are IDENTICAL for every combination, and rc equal for every combination.
# The file is written once (refused if it exists) and its sha256 and UTC time are recorded at write time.
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
REG=$EV/REGISTRY_S3R4C2_C_POLY.tsv
REC=$EV/PREREG_C_POLY_RECORD.txt
if [ -e "$REG" ]; then echo "REFUSED: exists $REG"; exit 2; fi
{
printf 'combo_id\tmode\tNG\tlattice\tdriver\tinjection\texpected_dump_F2_vs_F3\texpected_rc_F2_vs_F3\tstatus\n'
for MODE in closed2d fft kottke experimental tensor jones nv vl fftjones fftnv fftvl; do
    for NG in 1 5 9; do
        printf '%s-ng%s\t%s\t%s\tsquare\tpoly\tnone\tIDENTICAL\tSAME\tINFLUENCED\n' "$MODE" "$NG" "$MODE" "$NG"
    done
done
} > "$REG"
{
printf 'written_utc\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'registry\t%s\n' "$REG"
printf 'registry_sha256\t%s\n' "$(sha256sum "$REG" | cut -d' ' -f1)"
printf 'rows\t%s\n' "$(($(wc -l < "$REG") - 1))"
} > "$REC"
echo "prereg_c_poly_c2 written: $REG"
exit 0
