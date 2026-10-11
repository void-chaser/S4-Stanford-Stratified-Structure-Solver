#!/bin/sh
# J1 probe matrix runner (P05-S1R2).  Read-only probe: gdb reads memory and never writes program state.
# Usage: sh j1_matrix_run.sh EV   (EV = evidence dir; must be absolute, inside the repository)
# For each tree in (B A H), chain in (fftjones fftnv fftvl), injection in (none, NTH 3, 4, 5):
#   1) gdb run: entry and finish state of FMMGetEpsilon_PolBasis* (Epsilon_inv, Epsilon2 blocks)
#   2) driver run without gdb: rc first/retry, hit count, RESULT line
# All outputs go to EV/J1/.  Nothing is written outside EV.
EV=$1
OUTD="$EV/J1"
mkdir -p "$OUTD"
TREES="B A H"
CHAINS="fftjones fftnv fftvl"
for t in $TREES; do
  case "$t" in
    B|A|H) ;;
    *) echo "bad tree $t" >&2; exit 2;;
  esac
  for ch in $CHAINS; do
    case "$ch" in
      fftjones) PB=Jones;;
      fftnv) PB=NV;;
      fftvl) PB=VL;;
    esac
    for inj in none 3 4 5; do
      tag="$t-$ch-nth$inj"
      if [ "$inj" = "none" ]; then
        envinj=""
      else
        envinj="S4FMM_INJECT=s4malloc S4FMM_NTH=$inj"
      fi
      # 1) gdb probe on the PolBasis of this chain
      sed "s/FMMGetEpsilon_PolBasisVL/FMMGetEpsilon_PolBasis$PB/" "$EV/tmp/gdb_j1_full.gdb" > "$EV/tmp/gdb_j1_$tag.gdb"
      env FMM_MODE=$ch S4FMM_NG=9 $envinj timeout 180 gdb -q -batch -x "$EV/tmp/gdb_j1_$tag.gdb" \
        --args "$EV/drivers/driver-d003-$t" pattern both 4 3 > "$OUTD/gdb-$tag.txt" 2>&1
      echo "gdb $tag exit=$?"
      # 2) driver run (no gdb): rc, hit count, result
      env FMM_MODE=$ch S4FMM_NG=9 $envinj timeout 180 "$EV/drivers/driver-d003-$t" pattern both 4 3 > "$OUTD/drv-$tag.txt" 2>&1
      echo "drv $tag exit=$?"
    done
  done
done
echo "matrix run complete"
