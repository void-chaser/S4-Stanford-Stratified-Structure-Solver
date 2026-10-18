#!/bin/sh
# gate_s5r2.sh -- P05-S5 R2 end gate entry point.
# Output goes to $EV/gate/ (or $EV/shakedown/gate/ with --shakedown); both are excluded from SHA256SUMS.
REPO=$(git rev-parse --show-toplevel)
EV=$REPO/checkpoints/p05/evidence/p05-s5r2
mkdir -p "$EV/tmp"
export TMPDIR="$EV/tmp"
set -u
MODE="end"
if [ "$#" -ge 1 ]; then MODE="$1"; fi
if [ "$MODE" != "end" ]; then echo "gate_s5r2: only end mode is used in S5R2" >&2; exit 2; fi
shift
GATEDIR="$EV/gate"
for a in "$@"; do if [ "$a" = "--shakedown" ]; then GATEDIR="$EV/shakedown/gate"; fi; done
mkdir -p "$GATEDIR"
python3 -I -B "$REPO/testing/d003/stage_s5r2/gate_check_s5r2.py" "$GATEDIR/GATE_S5R2_end.txt" "$@"
RC=$?
echo "gate_s5r2: mode=end rc=$RC"
exit $RC
