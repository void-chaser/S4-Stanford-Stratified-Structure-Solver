#!/bin/sh
# gate_r9m3a.sh -- P05-S4 R9 M3a gate entry point. New file (r9m3a).
# usage: sh testing/d003/stage_s4r9/gate_r9m3a.sh start [TAG] [--commit-i REV]
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m3a; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
set -u
MODE=$1
if [ -z "$MODE" ]; then MODE=start; fi
if [ "$MODE" != start ] && [ "$MODE" != end ]; then echo "gate_r9m3a: mode must be start or end" >&2; exit 2; fi
shift
OUTNAME="GATE_R9M3A_$MODE.txt"
if [ "$#" -gt 0 ]; then
  case "$1" in
    --*) ;;
    _*) OUTNAME="GATE_R9M3A_$MODE$1"; shift ;;
    GATE_*) OUTNAME="$1"; shift ;;
    *) OUTNAME="GATE_R9M3A_$MODE"_'$1'.txt;;
  esac
fi
OUT="$EV/$OUTNAME"
if [ -e "$OUT" ]; then echo "gate_r9m3a: output exists, refusing to overwrite: $OUTNAME" >&2; exit 2; fi
STARTF="$EV/GATE_R9M3A_start.txt"
python3 -I -B "$REPO/testing/d003/stage_s4r9/gate_check_r9m3a.py" "$MODE" "$OUT" "$STARTF" "$EV" "$@"
RC=$?
echo "gate_r9m3a: mode=$MODE out=$OUTNAME rc=$RC"
exit $RC
