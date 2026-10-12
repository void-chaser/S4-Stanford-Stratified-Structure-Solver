#!/bin/sh
# run_r3_discovery_fc.sh -- P05-S4 R3-1 discovery with field-call boundaries (new file, R3).  NO injection.
# Runs the R2 driver under gdb with r3_callseq_fc.gdb (R3FC lines mark the two entries of
# S4_Simulation_GetFieldPlane).  Used only to assign each call of the discovery to the first or the second field call.
#
#   sh testing/d003/safe_run.sh p05-s4r3 -- sh testing/d003/stage_s4/run_r3_discovery_fc.sh
#
# Output: $EV/discovery_fc/<route>-<tree>-<mode>-r1.log  and  $EV/discovery_fc/INDEX_fc.tsv
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "run_r3_discovery_fc: not inside a git work tree" >&2; exit 2; }
EV=$REPO/checkpoints/p05/evidence/p05-s4r3
R2=$REPO/checkpoints/p05/evidence/p05-s4r2/run2/drivers
GDB=$REPO/testing/d003/stage_s4/r3_callseq_fc.gdb
DIR=$EV/discovery_fc
mkdir -p "$DIR" "$EV/tmp" || exit 2
TMPDIR=$EV/tmp
export TMPDIR
IDX=$DIR/INDEX_fc.tsv
printf '# route\ttree\tmode\trep\tgdb_status\tdriver_sha256\n' > "$IDX"
for route in once twice; do
    for tree in B F; do
        drv=$R2/plain-$tree/driver-d003
        dsha=$(sha256sum "$drv" | cut -d' ' -f1)
        for mode in fft kottke jones nv vl experimental closed1d closed2d; do
            log=$DIR/$route-$tree-$mode-r1.log
            if [ "$route" = twice ]; then
                env -i PATH="$PATH" LANG=C LC_ALL=C TMPDIR="$TMPDIR" FMM_MODE="$mode" S4FMM_NG=9 S4FMM_TWICE=slab \
                    gdb -batch -nx -x "$GDB" --args "$drv" pattern both 4 3 > "$log" 2>&1
            else
                env -i PATH="$PATH" LANG=C LC_ALL=C TMPDIR="$TMPDIR" FMM_MODE="$mode" S4FMM_NG=9 \
                    gdb -batch -nx -x "$GDB" --args "$drv" pattern both 4 3 > "$log" 2>&1
            fi
            st=$?
            printf '%s\t%s\t%s\t1\t%s\t%s\n' "$route" "$tree" "$mode" "$st" "$dsha" >> "$IDX"
        done
    done
done
echo "run_r3_discovery_fc: done"
exit 0
