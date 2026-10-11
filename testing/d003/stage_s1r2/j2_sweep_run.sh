#!/bin/sh
# J2 P2-D eps sweep (read-only probe).  Usage: sh j2_sweep_run.sh EV
EV=$1
D="$EV/J2_P2D_sweep"
mkdir -p "$D"
for e in 1e-6 1e-12 1e-100 1e-300; do
  tag="eps$e"
  env FMM_MODE=kottke J2_MAT=scalar_real J2_EPS=$e timeout 120 gdb -q -batch -x "$EV/tmp/gdb_j2_inv8.gdb" \
    --args "$EV/drivers/j2-kottke-probe-H" > "$D/trace-$tag.txt" 2>&1
  echo "sweep $tag gdb_exit=$?"
  env FMM_MODE=kottke J2_MAT=scalar_real J2_EPS=$e timeout 120 "$EV/drivers/j2-kottke-probe-H" > "$D/probe-$tag.txt" 2>&1
  echo "sweep $tag probe_exit=$?"
done
echo "sweep complete"
