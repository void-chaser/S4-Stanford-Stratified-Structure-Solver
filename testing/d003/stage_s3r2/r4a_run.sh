#!/bin/sh
# P05-S3R2 R2-4a: normal-path field comparison matrix (read-only probe).
# Usage: sh r4a_run.sh EV
# Requires: $EV/r4drv/driver-{base,start,new} and $EV/r4drv/DRIVER_PIN.sha256 (pinned before the run).
# Writes only under $EV/R2-4a_runs/.  Judgement is made later from field data and rc, never from PASS/FAIL.
EV=$1
D="$EV/R2-4a_runs"
mkdir -p "$D"
cd "$EV/r4drv" || { echo "cannot enter r4drv" >&2; exit 2; }
sha256sum -c DRIVER_PIN.sha256 > "$D/pin-check.txt" 2>&1 || { echo "DRIVER PIN MISMATCH: stop" >&2; exit 3; }
NONJ="fft kottke nv vl fftnv fftvl closed2d experimental tensor"
JONES="jones fftjones"
for kind in nonjones jones; do
  if [ "$kind" = nonjones ]; then MODES="$NONJ"; else MODES="$JONES"; fi
  for mode in $MODES; do
    for stack in pattern flat; do
      for pol in s p mix; do
        for ng in 5 9; do
          case_id="$mode-$stack-$pol-nb$ng"
          for tree in base start new; do
            drv="$EV/r4drv/driver-$tree"
            env FMM_MODE=$mode S4FMM_NG=$ng S4FMM_POL=$pol \
              S4FMM_DUMP1="$D/$case_id-$tree.dump1" S4FMM_DUMP="$D/$case_id-$tree.dump2" \
              timeout 120 "$drv" $stack both 4 3 > "$D/$case_id-$tree.out" 2>&1
            echo $? > "$D/$case_id-$tree.proc"
          done
        done
      done
    done
  done
done
echo "r4a run complete"
