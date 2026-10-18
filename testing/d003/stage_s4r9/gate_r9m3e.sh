#!/bin/sh
# gate_r9m3e.sh -- P05-S4 R9 M3e end gate entry point (output in $EV/gate/, excluded from SHA256SUMS).
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m3e; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
set -u
MODE=${1:-end}
if [ "$MODE" != "end" ]; then echo "gate_r9m3e: only end mode is used in M3e" >&2; exit 2; fi
shift
mkdir -p "$EV/gate"
python3 -I -B "$REPO/testing/d003/stage_s4r9/gate_check_r9m3e.py" "$EV/gate/GATE_R9M3E_end.txt" "$@"
RC=$?
echo "gate_r9m3e: mode=end rc=$RC"
exit $RC
