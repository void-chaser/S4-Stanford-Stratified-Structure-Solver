#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# run_noinject_equiv_r8.sh -- P05-S4 R8 M0 step 5: no-injection equivalence F2 against F3 (new file; copied from
# run_noinject_equiv_r7.sh).
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/run_noinject_equiv_r8.sh p05-s4r8 run1
# Changes against run_noinject_equiv_r7.sh (RUNNER_DIFF_R8_M0.txt; ERRATA_8 E8-5):
#   - the first line is the standard header; the output directories are created only if they do not exist (U17);
#   - the tree labels are F2 (first) and F3 (second) instead of F and F2;
#   - the drivers are r6bstate-F2-plain (reused from R7, U126) and r6bstate-F3-plain (linked in this round); tri likewise;
#   - the mode closed of the R7 matrix is replaced by closed2d (E7-3, U40): the driver accepts closed2d and closed1d only.
# Matrix otherwise unchanged: closed2d, fft, kottke, experimental, tensor, closed1d, jones, nv, vl, fftjones, fftnv, fftvl x NG 1/5/9;
# tri nv, vl, jones at NG 9.  The expectation is EXPECT_R8_NOINJECT.txt (written before this run).
# Output: $EV/noinject_r8/<RUN>/<tree>/<mode>-ng<NG>[-tri]/ and $EV/RESULTS_R8_NOINJECT_<RUN>.tsv (new, refused if it exists).
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "run_noinject_equiv_r8: first argument must be p05-s4r8" >&2; exit 2; }
RUN=${2:?"run label"}
R7EV="$REPO/checkpoints/p05/evidence/p05-s4r7"
DRV_F2="$R7EV/drivers_r7/r6bstate-F2-plain/driver"
DRV_F3="$EV/drivers_r8/r6bstate-F3-plain/driver"
DRVT_F2="$R7EV/drivers_r7/tri-F2-plain/driver"
DRVT_F3="$EV/drivers_r8/tri-F3-plain/driver"
RES="$EV/RESULTS_R8_NOINJECT_$RUN.tsv"
test -x "$DRV_F2" && test -x "$DRV_F3" && test -x "$DRVT_F2" && test -x "$DRVT_F3" || { echo "state or tri drivers missing" >&2; exit 2; }
test -f "$EV/EXPECT_R8_NOINJECT.txt" || { echo "expectation file missing" >&2; exit 2; }
if [ -e "$RES" ]; then echo "REFUSED: exists (U17): $RES" >&2; exit 2; fi
ROOT="$EV/noinject_r8/$RUN"
if [ -e "$ROOT" ]; then echo "REFUSED: exists (U17): $ROOT" >&2; exit 2; fi
mkdir -p "$ROOT/F2" "$ROOT/F3" || exit 2
printf 'mode\tNG\tlattice\ttree\trc_first\trc_retry\tfile\tcmp\n' > "$RES"

# one MODE NG LATTICE TREE DRIVER : run once, record rc lines and the dump directory name
one() {
    D="$ROOT/$4/$1-ng$2-$3"
    mkdir -p "$D" || return 1
    env -i PATH="$PATH" FMM_MODE="$1" S4FMM_NG="$2" S4FMM_DUMP_DIR="$D" "$5" pattern both 4 3 > "$D/stdout.txt" 2> "$D/stderr.txt"
    RC=$?
    RF=$(sed -n 's/^RC first \(-*[0-9][0-9]*\)[[:space:]]*$/\1/p' "$D/stdout.txt" | head -n 1)
    RR=$(sed -n 's/^RC retry \(-*[0-9][0-9]*\)[[:space:]]*$/\1/p' "$D/stdout.txt" | head -n 1)
    printf '%s\t%s\t%s\t%s\t%s\t%s\trun_rc=%s\t-\n' "$1" "$2" "$3" "$4" "$RF" "$RR" "$RC" >> "$RES"
}

# cmpdir MODE NG LATTICE : compare the three dump files of F2 and F3
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
echo "run_noinject_equiv_r8: done -> $RES"
exit 0
