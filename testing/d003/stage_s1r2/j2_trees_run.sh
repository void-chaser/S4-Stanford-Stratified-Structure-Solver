#!/bin/sh
# J2 three-tree check at key eps values (read-only probe).  Usage: sh j2_trees_run.sh EV
EV=$1
D="$EV/J2_TREES"
mkdir -p "$D"
for t in B A H; do
  for e in 0 1e-100 1e-300; do
    tag="$t-eps$e"
    env FMM_MODE=kottke J2_MAT=scalar_real J2_EPS=$e timeout 120 gdb -q -batch -x "$EV/tmp/gdb_j2_inv8.gdb" \
      --args "$EV/drivers/j2-kottke-probe-$t" > "$D/trace-$tag.txt" 2>&1
    echo "trees $tag gdb_exit=$?"
    env FMM_MODE=kottke J2_MAT=scalar_real J2_EPS=$e timeout 120 "$EV/drivers/j2-kottke-probe-$t" > "$D/probe-$tag.txt" 2>&1
    echo "trees $tag probe_exit=$?"
  done
done
echo "trees complete"
