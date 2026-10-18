#!/bin/sh
# gate_r9m3c.sh -- P05-S4 R9 M3c gate entry point. Modes: start, start_recheck, end.
# usage: gate_r9m3c.sh <mode> [--shakedown] [--commit-i HASH]
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m3c; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
set -u
MODE=$1
if [ -z "$MODE" ]; then MODE=start; fi
case "$MODE" in
  start) OUTNAME="GATE_R9M3C_start.txt" ;;
  start_recheck) OUTNAME="GATE_R9M3C_start_RECHECK.txt" ;;
  end) OUTNAME="GATE_R9M3C_end.txt" ;;
  *) echo "gate_r9m3c: mode must be start, start_recheck or end" >&2; exit 2 ;;
esac
shift
OUT="$EV/$OUTNAME"
if [ "$#" -gt 0 ] && [ "$1" = "--shakedown" ]; then
  mkdir -p "$EV/shakedown"
  OUT="$EV/shakedown/$OUTNAME"
  shift
fi
if [ -e "$OUT" ]; then echo "gate_r9m3c: output exists, refusing to overwrite: $OUT" >&2; exit 2; fi
STARTF="$EV/GATE_R9M3C_start.txt"
python3 -I -B "$REPO/testing/d003/stage_s4r9/gate_check_r9m3c.py" "$MODE" "$OUT" "$STARTF" "$EV" "$@"
RC=$?
echo "gate_r9m3c: mode=$MODE out=$OUT rc=$RC"
exit $RC
