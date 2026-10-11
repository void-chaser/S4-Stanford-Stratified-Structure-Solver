#!/bin/sh
# J1 full-matrix dump runner (P05-S1R2).  gdb reads memory and dumps it to EV/J1_DUMP only.
# Usage: sh j1_dump_run.sh EV
EV=$1
D="$EV/J1_DUMP"
mkdir -p "$D"
for t in B A H; do
  for ch in fftjones fftnv fftvl; do
    case "$ch" in
      fftjones) PB=Jones;;
      fftnv) PB=NV;;
      fftvl) PB=VL;;
    esac
    for inj in none 3 4 5; do
      tag="$t-$ch-nth$inj"
      if [ "$inj" = "none" ]; then envinj=""; else envinj="S4FMM_INJECT=s4malloc S4FMM_NTH=$inj"; fi
      g="$D/dump-$tag.gdb"
      mkdir -p "$D/$tag"
      sed -e "s/FMMGetEpsilon_PolBasisVL/FMMGetEpsilon_PolBasis$PB/" \
          -e "s#OUTDIR#$D/$tag#g" "$EV/tmp/gdb_j1_dump.gdb" > "$g"
      env FMM_MODE=$ch S4FMM_NG=9 $envinj timeout 180 gdb -q -batch -x "$g" \
        --args "$EV/drivers/driver-d003-$t" pattern both 4 3 > "$D/gdb-dump-$tag.txt" 2>&1
      echo "dump $tag exit=$?"
    done
  done
done
echo "dump run complete"
