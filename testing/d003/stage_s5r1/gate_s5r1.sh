#!/bin/sh
# gate_s5r1.sh -- P05-S5 R1 end gate entry point (output in $EV/gate/, or $EV/shakedown/gate/ in shakedown; excluded from SHA256SUMS).
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s5r1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
set -u
MODE="end"
if [ "$#" -ge 1 ]; then MODE="$1"; fi
if [ "$MODE" != "end" ]; then echo "gate_s5r1: only end mode is used in S5R1" >&2; exit 2; fi
shift
GATEDIR="$EV/gate"
for a in "$@"; do if [ "$a" = "--shakedown" ]; then GATEDIR="$EV/shakedown/gate"; fi; done
mkdir -p "$GATEDIR"
python3 -I -B "$REPO/testing/d003/stage_s5r1/gate_check_s5r1.py" "$GATEDIR/GATE_S5R1_end.txt" "$@"
RC=$?
echo "gate_s5r1: mode=end rc=$RC"
exit $RC
