REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2b; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# diff_gate_r8m2b.sh -- P05-S4 R8 M2b: unified diffs of the gate scripts against the r8m2a4 originals.
# New file (copied from diff_gate_r8m2a4.sh; original unchanged).
# Output: $EV/GATE_DIFF_R8_M2b.txt (diff exit 1 = differences, expected).
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m2b -- sh testing/d003/stage_s4/diff_gate_r8m2b.sh
set -u
S=$REPO/testing/d003/stage_s4
OUT=$EV/GATE_DIFF_R8_M2b.txt
test ! -e "$OUT" || { echo "diff_gate_r8m2b: REFUSED exists (U17): $OUT" >&2; exit 2; }
{
    echo "# GATE_DIFF_R8_M2b -- diff -u of r8m2a4 originals against r8m2b copies"
    echo "## gate_r8m2a4.sh -> gate_r8m2b.sh"
    diff -u "$S/gate_r8m2a4.sh" "$S/gate_r8m2b.sh"
    echo "## gate_check_r8m2a4.py -> gate_check_r8m2b.py"
    diff -u "$S/gate_check_r8m2a4.py" "$S/gate_check_r8m2b.py"
    echo "## gate_allow_r8m2a4_start.txt -> gate_allow_r8m2b_start.txt"
    diff -u "$S/gate_allow_r8m2a4_start.txt" "$S/gate_allow_r8m2b_start.txt"
    echo "## gate_allow_r8m2a4_end.txt -> gate_allow_r8m2b_end.txt"
    diff -u "$S/gate_allow_r8m2a4_end.txt" "$S/gate_allow_r8m2b_end.txt"
    echo "## diff_gate_r8m2a4.sh -> diff_gate_r8m2b.sh"
    diff -u "$S/diff_gate_r8m2a4.sh" "$S/diff_gate_r8m2b.sh"
} > "$OUT"
echo "diff_gate_r8m2b: wrote $OUT"
exit 0
