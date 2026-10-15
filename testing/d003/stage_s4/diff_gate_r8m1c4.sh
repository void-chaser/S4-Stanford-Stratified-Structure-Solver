REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c4; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# diff_gate_r8m1c4.sh -- P05-S4 R8 M1c4: unified diffs of the gate scripts against the r8m1c3 originals.
# Output: $EV/GATE_DIFF_R8_M1c4.txt (diff exit 1 = differences, expected).
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m1c4 -- sh testing/d003/stage_s4/diff_gate_r8m1c4.sh
set -u
S=$REPO/testing/d003/stage_s4
OUT=$EV/GATE_DIFF_R8_M1c4.txt
test ! -e "$OUT" || { echo "diff_gate_r8m1c4: REFUSED exists (U17): $OUT" >&2; exit 2; }
{
    echo "# GATE_DIFF_R8_M1c4 -- diff -u of r8m1c3 originals against r8m1c4 copies"
    echo "## gate_r8m1c3.sh -> gate_r8m1c4.sh"
    diff -u "$S/gate_r8m1c3.sh" "$S/gate_r8m1c4.sh"
    echo "## gate_check_r8m1c3.py -> gate_check_r8m1c4.py"
    diff -u "$S/gate_check_r8m1c3.py" "$S/gate_check_r8m1c4.py"
    echo "## gate_allow_r8m1c3_start.txt -> gate_allow_r8m1c4_start.txt"
    diff -u "$S/gate_allow_r8m1c3_start.txt" "$S/gate_allow_r8m1c4_start.txt"
    echo "## gate_allow_r8m1c3_end.txt -> gate_allow_r8m1c4_end.txt"
    diff -u "$S/gate_allow_r8m1c3_end.txt" "$S/gate_allow_r8m1c4_end.txt"
    echo "## diff_gate_r8m1c3.sh -> diff_gate_r8m1c4.sh"
    diff -u "$S/diff_gate_r8m1c3.sh" "$S/diff_gate_r8m1c4.sh"
} > "$OUT"
echo "diff_gate_r8m1c4: wrote $OUT"
exit 0
