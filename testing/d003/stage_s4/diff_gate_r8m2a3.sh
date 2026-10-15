REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# diff_gate_r8m2a3.sh -- P05-S4 R8 M2a3: unified diffs of the gate scripts against the r8m2a2 originals.
# New file (copied from diff_gate_r8m2a2.sh; original unchanged).
# Output: $EV/GATE_DIFF_R8_M2a3.txt (diff exit 1 = differences, expected).
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m2a3 -- sh testing/d003/stage_s4/diff_gate_r8m2a3.sh
set -u
S=$REPO/testing/d003/stage_s4
OUT=$EV/GATE_DIFF_R8_M2a3.txt
test ! -e "$OUT" || { echo "diff_gate_r8m2a3: REFUSED exists (U17): $OUT" >&2; exit 2; }
{
    echo "# GATE_DIFF_R8_M2a3 -- diff -u of r8m2a2 originals against r8m2a3 copies"
    echo "## gate_r8m2a2.sh -> gate_r8m2a3.sh"
    diff -u "$S/gate_r8m2a2.sh" "$S/gate_r8m2a3.sh"
    echo "## gate_check_r8m2a2.py -> gate_check_r8m2a3.py"
    diff -u "$S/gate_check_r8m2a2.py" "$S/gate_check_r8m2a3.py"
    echo "## gate_allow_r8m2a2_start.txt -> gate_allow_r8m2a3_start.txt"
    diff -u "$S/gate_allow_r8m2a2_start.txt" "$S/gate_allow_r8m2a3_start.txt"
    echo "## gate_allow_r8m2a2_end.txt -> gate_allow_r8m2a3_end.txt"
    diff -u "$S/gate_allow_r8m2a2_end.txt" "$S/gate_allow_r8m2a3_end.txt"
    echo "## diff_gate_r8m2a2.sh -> diff_gate_r8m2a3.sh"
    diff -u "$S/diff_gate_r8m2a2.sh" "$S/diff_gate_r8m2a3.sh"
} > "$OUT"
echo "diff_gate_r8m2a3: wrote $OUT"
exit 0
