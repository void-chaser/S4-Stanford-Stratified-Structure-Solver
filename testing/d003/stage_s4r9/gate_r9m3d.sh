#!/bin/sh
# gate_r9m3d.sh -- P05-S4 R9 M3d gate entry point. Modes: start, start_recheck, end.
# usage: gate_r9m3d.sh <mode> [--shakedown] [--commit-i HASH] [--evidence-sums PATH] [--registries-dir PATH]
#        [--report-check PATH] [--events PATH]
# The end-gate output lives in $EV/gate/ and is excluded from SHA256SUMS (task book section 1).
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m3d; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
set -u
MODE=${1:-}
if [ -z "$MODE" ]; then MODE=start; fi
case "$MODE" in
  start) OUTNAME="GATE_R9M3D_start.txt" ;;
  start_recheck) OUTNAME="GATE_R9M3D_start_RECHECK.txt" ;;
  end) OUTNAME="GATE_R9M3D_end.txt" ;;
  *) echo "gate_r9m3d: mode must be start, start_recheck or end" >&2; exit 2 ;;
esac
shift
SHK=0
if [ "${1:-}" = "--shakedown" ]; then SHK=1; shift; fi
if [ "$SHK" = "1" ]; then
  OUT="$EV/shakedown/$OUTNAME"
  mkdir -p "$EV/shakedown"
elif [ "$MODE" = "end" ]; then
  OUT="$EV/gate/$OUTNAME"
  mkdir -p "$EV/gate"
else
  OUT="$EV/$OUTNAME"
fi
if [ -e "$OUT" ] && [ "$SHK" != "1" ]; then
  echo "gate_r9m3d: output exists, refusing to overwrite: $OUT" >&2
  exit 2
fi
STARTF="$EV/GATE_R9M3D_start.txt"
if [ "$SHK" = "1" ]; then
  set -- "$@" --mode-shakedown
fi
python3 -I -B "$REPO/testing/d003/stage_s4r9/gate_check_r9m3d.py" "$MODE" "$OUT" "$STARTF" "$EV" "$@"
RC=$?
echo "gate_r9m3d: mode=$MODE out=$OUT rc=$RC"
exit $RC
