#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# diff_gate_r8m1c2.sh -- writes the diff -u of the four gate-file pairs (r8m1c1 -> r8m1c2) to
# $EV/GATE_DIFF_R8_M1c2.txt.  diff returns 1 when files differ; that is normal here.
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m1c2 -- sh testing/d003/stage_s4/diff_gate_r8m1c2.sh
set -u
S=$REPO/testing/d003/stage_s4
OUT=$EV/GATE_DIFF_R8_M1c2.txt
test ! -e "$OUT" || { echo "diff_gate_r8m1c2: REFUSED exists (U17): $OUT" >&2; exit 2; }
{
    diff -u "$S/gate_r8m1c1.sh" "$S/gate_r8m1c2.sh"
    diff -u "$S/gate_check_r8m1c1.py" "$S/gate_check_r8m1c2.py"
    diff -u "$S/gate_allow_r8m1c1_start.txt" "$S/gate_allow_r8m1c2_start.txt"
    diff -u "$S/gate_allow_r8m1c1_end.txt" "$S/gate_allow_r8m1c2_end.txt"
} > "$OUT"
echo "diff_gate_r8m1c2: wrote $OUT"
exit 0
