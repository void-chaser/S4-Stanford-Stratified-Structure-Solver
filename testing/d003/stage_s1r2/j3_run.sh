#!/bin/sh
# J3 three-tree x two-layout gdb run (read-only probe).  Usage: sh j3_run.sh EV
EV=$1
D="$EV/J3_RUNS"
mkdir -p "$D"
for t in B A H; do
  for lay in concentric two_disjoint; do
    tag="$t-$lay-n2"
    env FMM_MODE=kottke J3_NSHAPES=2 J3_LAYOUT=$lay timeout 120 gdb -q -batch -x "$EV/tmp/gdb_j3_normal.gdb" \
      --args "$EV/drivers/j3-shape-probe-$t" > "$D/trace-$tag.txt" 2>&1
    echo "j3 $tag gdb_exit=$?"
  done
done
echo "j3 run complete"
