#!/bin/sh
# gate_r9m3b.sh -- P05-S4 R9 M3b gate entry point (modes: start, start_recheck, end).
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m3b; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
set -u
MODE=$1
if [ -z "$MODE" ]; then MODE=start; fi
case "$MODE" in
  start) OUTNAME="GATE_R9M3B_start.txt" ;;
  start_recheck) OUTNAME="GATE_R9M3B_start_RECHECK.txt" ;;
  end) OUTNAME="GATE_R9M3B_end.txt" ;;
  *) echo "gate_r9m3b: mode must be start, start_recheck or end" >&2; exit 2 ;;
esac
shift
if [ "$#" -gt 0 ]; then
  case "$1" in
    --*) ;;
    _*) OUTNAME="${OUTNAME}${1}"; shift ;;
  esac
fi
OUT="$EV/$OUTNAME"
if [ -e "$OUT" ]; then echo "gate_r9m3b: output exists, refusing to overwrite: $OUTNAME" >&2; exit 2; fi
STARTF="$EV/GATE_R9M3B_start.txt"
python3 -I -B "$REPO/testing/d003/stage_s4r9/gate_check_r9m3b.py" "$MODE" "$OUT" "$STARTF" "$EV" "$@"
RC=$?
echo "gate_r9m3b: mode=$MODE out=$OUTNAME rc=$RC"
exit $RC
