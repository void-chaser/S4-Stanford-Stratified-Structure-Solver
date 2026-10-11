#!/bin/sh
# J1 ComputeLayerModes return and eigensolve-count runner (P05-S1R2).  gdb reads only.
# Usage: sh j1_clm_run.sh EV
EV=$1
D="$EV/J1_CLM"
mkdir -p "$D"
for t in B A H; do
  for ch in fftjones fftnv fftvl; do
    for inj in none 3 4 5; do
      tag="$t-$ch-nth$inj"
      if [ "$inj" = "none" ]; then envinj=""; else envinj="S4FMM_INJECT=s4malloc S4FMM_NTH=$inj"; fi
      env FMM_MODE=$ch S4FMM_NG=9 $envinj timeout 180 gdb -q -batch -x "$EV/tmp/gdb_j1_clmret_$t.gdb" \
        --args "$EV/drivers/driver-d003-$t" pattern both 4 3 > "$D/clm-$tag.txt" 2>&1
      echo "clm $tag exit=$?"
    done
  done
done
echo "clm run complete"
