#!/bin/sh
# run_c_poly_c2_run2.sh -- P05-S3R4 CONT2 (C polygon), run2: same runs as run_c_poly_c2.sh with the printf format fixed (new file).
#
#   sh testing/d003/safe_run.sh p05-s3r4c2 -- sh testing/d003/stage_s3r4c2/run_c_poly_c2_run2.sh
#
# Defect of run_c_poly_c2.sh (run1, recorded in ERRATA ES3R4-18): the printf in one() had 7 conversion
# specifiers for 8 arguments.  printf reused the format for the eighth argument (the rc of the run), so each
# call wrote a spurious second row "0-ng<TAB><TAB><TAB>F_<TAB>..." and the run_rc column was lost.
# rc_first and rc_retry are correct in run1 (they are the 5th and 6th arguments).  Dump files are not affected.
# run2 changes only that printf (8 specifiers, 8 arguments, 9 columns).  Expected values are unchanged.
# Output: $EV/c_poly_run2/<tree>/<mode>-ng<NG>/ ; $EV/RESULTS_S3R4C2_C_POLY_run2.tsv.  Nothing is overwritten.
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
DRV_F2=$EV/drivers/poly-F2/driver
DRV_F3=$EV/drivers/poly-F3/driver
RES=$EV/RESULTS_S3R4C2_C_POLY_run2.tsv
ROOT=$EV/c_poly_run2
test -x "$DRV_F2" && test -x "$DRV_F3" || { echo "poly drivers missing"; exit 2; }
test -f "$EV/REGISTRY_S3R4C2_C_POLY.tsv" || { echo "registry missing"; exit 2; }
if [ -e "$RES" ]; then echo "REFUSED: exists $RES"; exit 2; fi
if [ -e "$ROOT" ]; then echo "REFUSED: exists $ROOT"; exit 2; fi
mkdir -p "$ROOT/F2" "$ROOT/F3" || exit 2
printf 'combo\tmode\tNG\ttree\trc_first\trc_retry\trun_rc\tfile\tcmp\n' > "$RES"

# one MODE NG TREE DRIVER : run once, record rc first, rc retry and the run exit status (8 arguments, 8 specifiers)
one() {
    D="$ROOT/$3/$1-ng$2"
    mkdir -p "$D" || return 1
    env -i PATH="$PATH" FMM_MODE="$1" S4FMM_NG="$2" S4FMM_DUMP_DIR="$D" "$4" pattern both 4 3 > "$D/stdout.txt" 2> "$D/stderr.txt"
    RC=$?
    RF=$(sed -n 's/^RC first \(-*[0-9][0-9]*\)[[:space:]]*$/\1/p' "$D/stdout.txt" | head -1)
    RR=$(sed -n 's/^RC retry \(-*[0-9][0-9]*\)[[:space:]]*$/\1/p' "$D/stdout.txt" | head -1)
    printf '%s-ng%s\t%s\t%s\tF_%s\t%s\t%s\t%s\t-\t-\n' "$1" "$2" "$1" "$2" "$3" "$RF" "$RR" "$RC" >> "$RES"
}

# cmpdir MODE NG : compare call1-3 of F2 and F3 byte by byte (6 specifiers, 6 arguments; 9 columns in all)
cmpdir() {
    for F in call1.txt call2.txt call3.txt; do
        A="$ROOT/F2/$1-ng$2/$F"; B="$ROOT/F3/$1-ng$2/$F"
        if [ -f "$A" ] && [ -f "$B" ] && cmp -s "$A" "$B"; then CMP=IDENTICAL; else CMP=NOT_IDENTICAL_OR_MISSING; fi
        printf '%s-ng%s\t%s\t%s\tF2-vs-F3\t-\t-\t-\t%s\t%s\n' "$1" "$2" "$1" "$2" "$F" "$CMP" >> "$RES"
    done
}

for MODE in closed2d fft kottke experimental tensor jones nv vl fftjones fftnv fftvl; do
    for NG in 1 5 9; do
        one "$MODE" "$NG" F2 "$DRV_F2"
        one "$MODE" "$NG" F3 "$DRV_F3"
        cmpdir "$MODE" "$NG"
    done
done
echo "run_c_poly_c2_run2: done -> $RES"
exit 0
