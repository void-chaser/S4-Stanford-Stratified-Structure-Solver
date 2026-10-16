REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2c; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# diff_gate_r8m2c.sh -- P05-S4 R8 M2c: unified diffs of the gate scripts against the r8m2b originals.
# New file.
# Output: $EV/GATE_DIFF_R8_M2c.txt (diff exit 1 = differences, expected).
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m2c -- sh testing/d003/stage_s4/diff_gate_r8m2c.sh
set -u
S=$REPO/testing/d003/stage_s4
OUT=$EV/GATE_DIFF_R8_M2c.txt
test ! -e "$OUT" || { echo "diff_gate_r8m2c: REFUSED exists (U17): $OUT" >&2; exit 2; }
{
    echo "# GATE_DIFF_R8_M2c -- diff -u of r8m2b originals against r8m2c copies"
    echo "## gate_r8m2b.sh -> gate_r8m2c.sh"
    diff -u "$S/gate_r8m2b.sh" "$S/gate_r8m2c.sh"
    echo "## gate_check_r8m2b.py -> gate_check_r8m2c.py"
    diff -u "$S/gate_check_r8m2b.py" "$S/gate_check_r8m2c.py"
    echo "## gate_allow_r8m2b_start.txt -> gate_allow_r8m2c_start.txt"
    diff -u "$S/gate_allow_r8m2b_start.txt" "$S/gate_allow_r8m2c_start.txt"
    echo "## gate_allow_r8m2b_end.txt -> gate_allow_r8m2c_end.txt"
    diff -u "$S/gate_allow_r8m2b_end.txt" "$S/gate_allow_r8m2c_end.txt"
    echo "## diff_gate_r8m2b.sh -> diff_gate_r8m2c.sh"
    diff -u "$S/diff_gate_r8m2b.sh" "$S/diff_gate_r8m2c.sh"
} > "$OUT"
echo "diff_gate_r8m2c: wrote $OUT"
exit 0
