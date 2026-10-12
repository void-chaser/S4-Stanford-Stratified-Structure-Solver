#!/bin/sh
# run_r3_discovery.sh -- P05-S4 R3-1 discovery runner (new file, R3).
#
# Runs the R2 driver UNDER gdb with NO injection, once per (tree, mode, repetition).  gdb reads
# testing/d003/stage_s4/r3_callseq.gdb, which records the call sequence of S4_malloc, fft_plan_dft_2d
# and fft_plan_exec.  The discovery is a measurement of the call order only; its output is never
# evidence that any tree is repaired or verified.
#
#   sh testing/d003/safe_run.sh p05-s4r3 -- sh testing/d003/stage_s4/run_r3_discovery.sh once
#   sh testing/d003/safe_run.sh p05-s4r3 -- sh testing/d003/stage_s4/run_r3_discovery.sh twice
#
# ROUTE once  : S4FMM_TWICE unset (the two field calls of the driver, as in R2 and the historical runs).
# ROUTE twice : S4FMM_TWICE=slab (layer 1 modes destroyed between the two calls; reaches the cache-hit
#               routes of PolBasis).  Same route as the R2 "t4/" cases.
#
# Trees: B (plain-B) and F (plain-F), both from checkpoints/p05/evidence/p05-s4r2/run2/drivers.
# Modes: fft kottke jones nv vl experimental closed1d closed2d (the R3 mode list).
# Repetitions: REPS, default "1 2" (reproducibility check of the call order).
#
# Output (under $EV/discovery/):  <ROUTE>-<TREE>-<MODE>-r<REP>.log   raw gdb output
#                                 INDEX_<ROUTE>.tsv                  route, tree, mode, rep, gdb status
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "run_r3_discovery: not inside a git work tree" >&2; exit 2; }
EV=$REPO/checkpoints/p05/evidence/p05-s4r3
ROUTE=${1:-once}
case "$ROUTE" in
    once|twice) ;;
    *) echo "run_r3_discovery: ROUTE must be once or twice" >&2; exit 2;;
esac
REP_LIST=${REPS:-"1 2"}
R2=$REPO/checkpoints/p05/evidence/p05-s4r2/run2/drivers
GDB=$REPO/testing/d003/stage_s4/r3_callseq.gdb
DIR=$EV/discovery
mkdir -p "$DIR" "$EV/tmp" || exit 2
TMPDIR=$EV/tmp
export TMPDIR
IDX=$DIR/INDEX_$ROUTE.tsv
printf '# route\ttree\tmode\trep\tgdb_status\tdriver_sha256\n' > "$IDX"

for tree in B F; do
    drv=$R2/plain-$tree/driver-d003
    dsha=$(sha256sum "$drv" | cut -d' ' -f1)
    for mode in fft kottke jones nv vl experimental closed1d closed2d; do
        for rep in $REP_LIST; do
            log=$DIR/$ROUTE-$tree-$mode-r$rep.log
            if [ "$ROUTE" = twice ]; then
                env -i PATH="$PATH" LANG=C LC_ALL=C TMPDIR="$TMPDIR" FMM_MODE="$mode" S4FMM_NG=9 S4FMM_TWICE=slab \
                    gdb -batch -nx -x "$GDB" --args "$drv" pattern both 4 3 > "$log" 2>&1
            else
                env -i PATH="$PATH" LANG=C LC_ALL=C TMPDIR="$TMPDIR" FMM_MODE="$mode" S4FMM_NG=9 \
                    gdb -batch -nx -x "$GDB" --args "$drv" pattern both 4 3 > "$log" 2>&1
            fi
            st=$?
            printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$ROUTE" "$tree" "$mode" "$rep" "$st" "$dsha" >> "$IDX"
        done
    done
done
echo "run_r3_discovery: route $ROUTE done"
exit 0
