REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2e; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# diff_gate_r8m2e.sh -- P05-S4 R8 M2e: unified diffs of the gate scripts against the r8m2d originals.
# New file.
# Output: $EV/GATE_DIFF_R8_M2e.txt (diff exit 1 = differences, expected).
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m2e -- sh testing/d003/stage_s4/diff_gate_r8m2e.sh
set -u
S=$REPO/testing/d003/stage_s4
OUT=$EV/GATE_DIFF_R8_M2e.txt
test ! -e "$OUT" || { echo "diff_gate_r8m2e: REFUSED exists (U17): $OUT" >&2; exit 2; }
{
    echo "# GATE_DIFF_R8_M2e -- diff -u of r8m2d originals against r8m2e copies"
    echo "## gate_r8m2d.sh -> gate_r8m2e.sh"
    diff -u "$S/gate_r8m2d.sh" "$S/gate_r8m2e.sh" || true
    echo "## gate_check_r8m2d.py -> gate_check_r8m2e.py"
    diff -u "$S/gate_check_r8m2d.py" "$S/gate_check_r8m2e.py" || true
    echo "## gate_allow_r8m2d_start.txt -> gate_allow_r8m2e_start.txt"
    diff -u "$S/gate_allow_r8m2d_start.txt" "$S/gate_allow_r8m2e_start.txt" || true
    echo "## gate_allow_r8m2d_end.txt -> gate_allow_r8m2e_end.txt"
    diff -u "$S/gate_allow_r8m2d_end.txt" "$S/gate_allow_r8m2e_end.txt" || true
    echo "## diff_gate_r8m2d.sh -> diff_gate_r8m2e.sh"
    diff -u "$S/diff_gate_r8m2d.sh" "$S/diff_gate_r8m2e.sh" || true
} > "$OUT"
echo "diff_gate_r8m2e: wrote $OUT"
exit 0
