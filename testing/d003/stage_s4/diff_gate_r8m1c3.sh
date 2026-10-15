REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# diff_gate_r8m1c3.sh -- P05-S4 R8 M1c3: unified diffs of the gate scripts against the r8m1c2 originals.
# Output: $EV/GATE_DIFF_R8_M1c3.txt (diff exit 1 = differences, expected).
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m1c3 -- sh testing/d003/stage_s4/diff_gate_r8m1c3.sh
set -u
S=$REPO/testing/d003/stage_s4
OUT=$EV/GATE_DIFF_R8_M1c3.txt
test ! -e "$OUT" || { echo "diff_gate_r8m1c3: REFUSED exists (U17): $OUT" >&2; exit 2; }
{
    echo "# GATE_DIFF_R8_M1c3 -- diff -u of r8m1c2 originals against r8m1c3 copies"
    echo "## gate_r8m1c2.sh -> gate_r8m1c3.sh"
    diff -u "$S/gate_r8m1c2.sh" "$S/gate_r8m1c3.sh"
    echo "## gate_check_r8m1c2.py -> gate_check_r8m1c3.py"
    diff -u "$S/gate_check_r8m1c2.py" "$S/gate_check_r8m1c3.py"
    echo "## gate_allow_r8m1c2_start.txt -> gate_allow_r8m1c3_start.txt"
    diff -u "$S/gate_allow_r8m1c2_start.txt" "$S/gate_allow_r8m1c3_start.txt"
    echo "## gate_allow_r8m1c2_end.txt -> gate_allow_r8m1c3_end.txt"
    diff -u "$S/gate_allow_r8m1c2_end.txt" "$S/gate_allow_r8m1c3_end.txt"
} > "$OUT"
echo "diff_gate_r8m1c3: wrote $OUT"
exit 0
