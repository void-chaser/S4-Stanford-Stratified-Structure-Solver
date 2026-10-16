REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2d; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# diff_gate_r8m2d.sh -- P05-S4 R8 M2d: unified diffs of the gate scripts against the r8m2c originals.
# New file.
# Output: $EV/GATE_DIFF_R8_M2d.txt (diff exit 1 = differences, expected).
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m2d -- sh testing/d003/stage_s4/diff_gate_r8m2d.sh
set -u
S=$REPO/testing/d003/stage_s4
OUT=$EV/GATE_DIFF_R8_M2d.txt
test ! -e "$OUT" || { echo "diff_gate_r8m2d: REFUSED exists (U17): $OUT" >&2; exit 2; }
{
    echo "# GATE_DIFF_R8_M2d -- diff -u of r8m2c originals against r8m2d copies"
    echo "## gate_r8m2c.sh -> gate_r8m2d.sh"
    diff -u "$S/gate_r8m2c.sh" "$S/gate_r8m2d.sh" || true
    echo "## gate_check_r8m2c.py -> gate_check_r8m2d.py"
    diff -u "$S/gate_check_r8m2c.py" "$S/gate_check_r8m2d.py" || true
    echo "## gate_allow_r8m2c_start.txt -> gate_allow_r8m2d_start.txt"
    diff -u "$S/gate_allow_r8m2c_start.txt" "$S/gate_allow_r8m2d_start.txt" || true
    echo "## gate_allow_r8m2c_end.txt -> gate_allow_r8m2d_end.txt"
    diff -u "$S/gate_allow_r8m2c_end.txt" "$S/gate_allow_r8m2d_end.txt" || true
    echo "## diff_gate_r8m2c.sh -> diff_gate_r8m2d.sh"
    diff -u "$S/diff_gate_r8m2c.sh" "$S/diff_gate_r8m2d.sh" || true
} > "$OUT"
echo "diff_gate_r8m2d: wrote $OUT"
exit 0
