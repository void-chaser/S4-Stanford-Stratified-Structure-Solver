#!/bin/sh
# prereg_a_c2.sh -- P05-S3R4 CONT2 self-check (A): write the pre-registration REGISTRY_S3R4C2_A.tsv (new file).
#
#   sh testing/d003/safe_run.sh p05-s3r4c2 -- sh testing/d003/stage_s3r4c2/prereg_a_c2.sh
#
# Written before any injection run.  One row per (combination, tree, point).  K from the A1 maps
# (a1map2_<tree>_<combo>/stderr.txt and callers.tsv; K is identical on F2 and F3 for every combination):
#   closed2d NG1 : K_init = 7 (n=4, nshapes=1 layer), K0 = 6 (n=0, nshapes=0 layer)
#   fft NG5      : K_init = 8, K0 = 7
#   kottke NG5   : K_init = 8, K0 = 7
# Points: A-806 = win:1 ; A-1729 = init:K_init ; A-U96 = init:K0 (BOUNDARY_U96_BY_DESIGN).
# Expected (brief CONT1 section 3, unchanged):
#   A-806   F2: CRASH                       F3: REPORTED_FAILURE, rc1 = 1
#   A-1729  F2: REPORTED_FAILURE, rc1 = -3  F3: REPORTED_FAILURE, rc1 = 1
#   A-U96   F2 and F3: rc1 = 0, class SILENT_SWALLOW
# Side observations (recorded, not in the judgement): side_rc2 expected 0 for F3 A-806, F3 A-1729 and F2 A-1729.
# The file is written once (refused if it exists); its sha256 and UTC time are recorded at write time.
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
REG=$EV/REGISTRY_S3R4C2_A.tsv
REC=$EV/PREREG_A_RECORD.txt
if [ -e "$REG" ]; then echo "REFUSED: exists $REG"; exit 2; fi
{
printf 'combo\tmode\tNG\ttree\tpoint_id\tinj_spec\tk_index\texpected_rc1\texpected_class\texpected_side_rc2\tnote\tstatus\n'
for COMBO in "closed2d-ng1 closed2d 1 7 6" "fft-ng5 fft 5 8 7" "kottke-ng5 kottke 5 8 7"; do
    set -- $COMBO
    CID=$1; MODE=$2; NG=$3; KI=$4; K0=$5
    # A-806 (win:1)
    printf '%s\t%s\t%s\tF2\tA-806\twin:1\t1\t-\tCRASH\t-\t-\tINFLUENCED\n' "$CID" "$MODE" "$NG"
    printf '%s\t%s\t%s\tF3\tA-806\twin:1\t1\t1\tREPORTED_FAILURE\t0\t-\tINFLUENCED\n' "$CID" "$MODE" "$NG"
    # A-1729 (init:K_init)
    printf '%s\t%s\t%s\tF2\tA-1729\tinit:%s\t%s\t-3\tREPORTED_FAILURE\t0\t-\tINFLUENCED\n' "$CID" "$MODE" "$NG" "$KI" "$KI"
    printf '%s\t%s\t%s\tF3\tA-1729\tinit:%s\t%s\t1\tREPORTED_FAILURE\t0\t-\tINFLUENCED\n' "$CID" "$MODE" "$NG" "$KI" "$KI"
    # A-U96 (init:K0, n=0, nshapes=0 layer)
    printf '%s\t%s\t%s\tF2\tA-U96\tinit:%s\t%s\t0\tSILENT_SWALLOW\t-\tBOUNDARY_U96_BY_DESIGN\tINFLUENCED\n' "$CID" "$MODE" "$NG" "$K0" "$K0"
    printf '%s\t%s\t%s\tF3\tA-U96\tinit:%s\t%s\t0\tSILENT_SWALLOW\t-\tBOUNDARY_U96_BY_DESIGN\tINFLUENCED\n' "$CID" "$MODE" "$NG" "$K0" "$K0"
done
} > "$REG"
{
printf 'written_utc\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'registry\t%s\n' "$REG"
printf 'registry_sha256\t%s\n' "$(sha256sum "$REG" | cut -d' ' -f1)"
printf 'rows\t%s\n' "$(($(wc -l < "$REG") - 1))"
} > "$REC"
echo "prereg_a_c2 written: $REG"
exit 0
