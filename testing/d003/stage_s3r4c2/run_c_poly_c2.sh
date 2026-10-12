#!/bin/sh
# run_c_poly_c2.sh -- P05-S3R4 CONT2 (C polygon): no-injection byte comparison F2 vs F3 with the poly driver (new file).
#
#   sh testing/d003/safe_run.sh p05-s3r4c2 -- sh testing/d003/stage_s3r4c2/run_c_poly_c2.sh
#
# Pattern of testing/d003/stage_s3r4/run_noinject_s3r4.sh, restricted to the polygon driver and 33 combinations
# (11 modes x NG 1, 5, 9).  Each combination runs once per tree.  The comparison is the three dump files.
# Output: $EV/c_poly/<tree>/<mode>-ng<NG>/ ; $EV/RESULTS_S3R4C2_C_POLY.tsv (one row per combination).
# The registry must exist (written by prereg_c_poly_c2.sh before this run).  Nothing is overwritten.
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
DRV_F2=$EV/drivers/poly-F2/driver
DRV_F3=$EV/drivers/poly-F3/driver
RES=$EV/RESULTS_S3R4C2_C_POLY.tsv
ROOT=$EV/c_poly
test -x "$DRV_F2" && test -x "$DRV_F3" || { echo "poly drivers missing"; exit 2; }
test -f "$EV/REGISTRY_S3R4C2_C_POLY.tsv" || { echo "registry missing"; exit 2; }
if [ -e "$RES" ]; then echo "REFUSED: exists $RES"; exit 2; fi
if [ -e "$ROOT" ]; then echo "REFUSED: exists $ROOT"; exit 2; fi
mkdir -p "$ROOT/F2" "$ROOT/F3" || exit 2
printf 'combo\tmode\tNG\ttree\trc_first\trc_retry\trun_rc\tfile\tcmp\n' > "$RES"

# one MODE NG TREE DRIVER : run once, record rc first and rc retry from stdout
one() {
    D="$ROOT/$3/$1-ng$2"
    mkdir -p "$D" || return 1
    env -i PATH="$PATH" FMM_MODE="$1" S4FMM_NG="$2" S4FMM_DUMP_DIR="$D" "$4" pattern both 4 3 > "$D/stdout.txt" 2> "$D/stderr.txt"
    RC=$?
    RF=$(sed -n 's/^RC first \(-*[0-9][0-9]*\)[[:space:]]*$/\1/p' "$D/stdout.txt" | head -1)
    RR=$(sed -n 's/^RC retry \(-*[0-9][0-9]*\)[[:space:]]*$/\1/p' "$D/stdout.txt" | head -1)
    printf '%s-ng%s\t%s\t%s\tF_%s\t%s\t%s\t-\t-\n' "$1" "$2" "$1" "$2" "$3" "$RF" "$RR" "$RC" >> "$RES"
}

# cmpdir MODE NG : compare call1-3 of F2 and F3 byte by byte
cmpdir() {
    for F in call1.txt call2.txt call3.txt; do
        A="$ROOT/F2/$1-ng$2/$F"; B="$ROOT/F3/$1-ng$2/$F"
        if [ -f "$A" ] && [ -f "$B" ] && cmp -s "$A" "$B"; then CMP=IDENTICAL; else CMP=NOT_IDENTICAL_OR_MISSING; fi
        printf '%s-ng%s\t%s\t%s\tF2-vs-F3\t-\t-\t-\t%s\t%s\n' "$1" "$2" "$1" "$2" "$F" "$CMP" >> "$RES"
        # columns: combo mode NG tree rc_first rc_retry run_rc file cmp (9 columns, as the header)
    done
}

for MODE in closed2d fft kottke experimental tensor jones nv vl fftjones fftnv fftvl; do
    for NG in 1 5 9; do
        one "$MODE" "$NG" F2 "$DRV_F2"
        one "$MODE" "$NG" F3 "$DRV_F3"
        cmpdir "$MODE" "$NG"
    done
done
echo "run_c_poly_c2: done -> $RES"
exit 0
