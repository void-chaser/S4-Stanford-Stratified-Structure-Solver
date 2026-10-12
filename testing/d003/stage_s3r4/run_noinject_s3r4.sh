#!/bin/sh
# run_noinject_s3r4.sh -- P05-S3R4 self-check (C): no-injection byte equivalence F2 vs F3 (new file).
#
#   sh testing/d003/safe_run.sh p05-s3r4 -- sh testing/d003/stage_s3r4/run_noinject_s3r4.sh p05-s3r4 run1
#
# Pattern of testing/d003/stage_s4r7/run_noinject_equiv_r7.sh (R7 4.3), with two changes:
#   - trees are F2 and F3 (S3R4 self-check);
#   - mode closed2d replaces closed (task brief section 4, C).
# Modes: closed2d, fft, kottke, experimental, tensor, closed1d, jones, nv, vl, fftjones, fftnv, fftvl; NG 1, 5, 9 (square).
# Tri lattice: driver_s3r3_tri for nv, vl, jones at NG 9.  Polygon driver (B) is run separately (run_poly_s3r4.sh).
# Output: $EV/noinject_s3r4/<run>/<tree>/<mode>-ng<NG>[-tri]/ and $EV/RESULTS_S3R4_NOINJECT_<run>.tsv.
# Nothing is overwritten (U17): the run label and every directory are new.
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "noinject_s3r4: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: run_noinject_s3r4.sh p05-s3r4 run1"}
RUN=${2:?"run label"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
DRV_F2="$EV/drivers/state-F2/driver"
DRV_F3="$EV/drivers/state-F3/driver"
DRVT_F2="$EV/drivers/tri-F2/driver"
DRVT_F3="$EV/drivers/tri-F3/driver"
RES="$EV/RESULTS_S3R4_NOINJECT_$RUN.tsv"
test -x "$DRV_F2" && test -x "$DRV_F3" && test -x "$DRVT_F2" && test -x "$DRVT_F3" || { echo "drivers missing" >&2; exit 2; }
if [ -e "$RES" ]; then echo "REFUSED: exists (U17): $RES" >&2; exit 2; fi
ROOT="$EV/noinject_s3r4/$RUN"
if [ -e "$ROOT" ]; then echo "REFUSED: exists (U17): $ROOT" >&2; exit 2; fi
mkdir -p "$ROOT/F2" "$ROOT/F3" || exit 2
printf 'mode\tNG\tlattice\ttree\trc_first\trc_retry\tfile\tcmp\n' > "$RES"

# one MODE NG LATTICE TREE DRIVER : run once, record the rc lines and the run exit status
one() {
    D="$ROOT/$4/$1-ng$2-$3"
    mkdir -p "$D" || return 1
    env -i PATH="$PATH" FMM_MODE="$1" S4FMM_NG="$2" S4FMM_DUMP_DIR="$D" "$5" pattern both 4 3 > "$D/stdout.txt" 2> "$D/stderr.txt"
    RC=$?
    RF=$(sed -n 's/^RC first \(-*[0-9][0-9]*\)[[:space:]]*$/\1/p' "$D/stdout.txt" | head -1)
    RR=$(sed -n 's/^RC retry \(-*[0-9][0-9]*\)[[:space:]]*$/\1/p' "$D/stdout.txt" | head -1)
    printf '%s\t%s\t%s\t%s\t%s\t%s\trun_rc=%s\t-\n' "$1" "$2" "$3" "$4" "$RF" "$RR" "$RC" >> "$RES"
}

# cmpdir MODE NG LATTICE : compare the three dump files of F2 and F3 byte by byte
cmpdir() {
    for F in call1.txt call2.txt call3.txt; do
        A="$ROOT/F2/$1-ng$2-$3/$F"; B="$ROOT/F3/$1-ng$2-$3/$F"
        if [ -f "$A" ] && [ -f "$B" ] && cmp -s "$A" "$B"; then CMP=IDENTICAL; else CMP=NOT_IDENTICAL_OR_MISSING; fi
        printf '%s\t%s\t%s\tF2-vs-F3\t-\t-\t%s\t%s\n' "$1" "$2" "$3" "$F" "$CMP" >> "$RES"
    done
}

for MODE in closed2d fft kottke experimental tensor closed1d jones nv vl fftjones fftnv fftvl; do
    for NG in 1 5 9; do
        one "$MODE" "$NG" square F2 "$DRV_F2"
        one "$MODE" "$NG" square F3 "$DRV_F3"
        cmpdir "$MODE" "$NG" square
    done
done

for MODE in nv vl jones; do
    one "$MODE" 9 tri F2 "$DRVT_F2"
    one "$MODE" 9 tri F3 "$DRVT_F3"
    cmpdir "$MODE" 9 tri
done
echo "run_noinject_s3r4: done -> $RES"
exit 0
