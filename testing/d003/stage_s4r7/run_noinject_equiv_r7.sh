#!/bin/sh
# run_noinject_equiv_r7.sh -- P05-S4 R7-3 step 4.3: no-injection equivalence F vs F2 (new file; revised).
#
#   sh testing/d003/safe_run.sh p05-s4r7 -- sh testing/d003/stage_s4r7/run_noinject_equiv_r7.sh p05-s4r7 run1
#
# Driver: driver_r6b_state (plain, F and F2), which writes call1/call2/call3.txt through S4FMM_DUMP_DIR (as in S3R3 B).
# Modes: closed, fft, kottke, experimental, tensor, closed1d, jones, nv, vl, fftjones, fftnv, fftvl; NG 1, 5, 9 (lattice square).
# Tri lattice: driver_s3r3_tri (plain, F and F2) for nv, vl, jones at NG 9 (lattice {1,0,0.5,0.866}).
# Output: $EV/noinject_r7/<run>/<tree>/<mode>-ng<NG>[-tri]/ and $EV/RESULTS_R7_NOINJECT_<run>.tsv.
# Nothing is overwritten (U17): the run label and every directory are new.
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "noinject_r7: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: run_noinject_equiv_r7.sh p05-s4r7 run1"}
RUN=${2:?"run label"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
DRV_F="$EV/drivers_r7/r6bstate-F-plain/driver"
DRV_F2="$EV/drivers_r7/r6bstate-F2-plain/driver"
DRVT_F="$EV/drivers_r7/tri-F-plain/driver"
DRVT_F2="$EV/drivers_r7/tri-F2-plain/driver"
RES="$EV/RESULTS_R7_NOINJECT_$RUN.tsv"
test -x "$DRV_F" && test -x "$DRV_F2" || { echo "state drivers missing" >&2; exit 2; }
if [ -e "$RES" ]; then echo "REFUSED: exists (U17): $RES" >&2; exit 2; fi
ROOT="$EV/noinject_r7/$RUN"
if [ -e "$ROOT" ]; then echo "REFUSED: exists (U17): $ROOT" >&2; exit 2; fi
mkdir -p "$ROOT/F" "$ROOT/F2" || exit 2
printf 'mode\tNG\tlattice\ttree\trc_first\trc_retry\tfile\tcmp\n' > "$RES"

# one MODE NG LATTICE TREE DRIVER : run once, record rc lines and the dump directory name
one() {
    D="$ROOT/$4/$1-ng$2-$3"
    mkdir -p "$D" || return 1
    env -i PATH="$PATH" FMM_MODE="$1" S4FMM_NG="$2" S4FMM_DUMP_DIR="$D" "$5" pattern both 4 3 > "$D/stdout.txt" 2> "$D/stderr.txt"
    RC=$?
    RF=$(sed -n 's/^RC first \(-*[0-9][0-9]*\)[[:space:]]*$/\1/p' "$D/stdout.txt" | head -1)
    RR=$(sed -n 's/^RC retry \(-*[0-9][0-9]*\)[[:space:]]*$/\1/p' "$D/stdout.txt" | head -1)
    printf '%s\t%s\t%s\t%s\t%s\t%s\trun_rc=%s\t-\n' "$1" "$2" "$3" "$4" "$RF" "$RR" "$RC" >> "$RES"
}

# cmpdir MODE NG LATTICE : compare the three dump files of F and F2
cmpdir() {
    for F in call1.txt call2.txt call3.txt; do
        A="$ROOT/F/$1-ng$2-$3/$F"; B="$ROOT/F2/$1-ng$2-$3/$F"
        if [ -f "$A" ] && [ -f "$B" ] && cmp -s "$A" "$B"; then CMP=IDENTICAL; else CMP=NOT_IDENTICAL_OR_MISSING; fi
        printf '%s\t%s\t%s\tF-vs-F2\t-\t-\t%s\t%s\n' "$1" "$2" "$3" "$F" "$CMP" >> "$RES"
    done
}

for MODE in closed fft kottke experimental tensor closed1d jones nv vl fftjones fftnv fftvl; do
    for NG in 1 5 9; do
        one "$MODE" "$NG" square F  "$DRV_F"
        one "$MODE" "$NG" square F2 "$DRV_F2"
        cmpdir "$MODE" "$NG" square
    done
done

for MODE in nv vl jones; do
    one "$MODE" 9 tri F  "$DRVT_F"
    one "$MODE" 9 tri F2 "$DRVT_F2"
    cmpdir "$MODE" 9 tri
done
echo "run_noinject_equiv_r7: done -> $RES"
exit 0
