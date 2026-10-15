REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# diff_gate_r8m2a.sh -- P05-S4 R8 M2a: unified diffs of the gate scripts against the r8m1c4 originals.
# Output: $EV/GATE_DIFF_R8_M2a.txt (diff exit 1 = differences, expected).
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m2a -- sh testing/d003/stage_s4/diff_gate_r8m2a.sh
set -u
S=$REPO/testing/d003/stage_s4
OUT=$EV/GATE_DIFF_R8_M2a.txt
test ! -e "$OUT" || { echo "diff_gate_r8m2a: REFUSED exists (U17): $OUT" >&2; exit 2; }
{
    echo "# GATE_DIFF_R8_M2a -- diff -u of r8m1c4 originals against r8m2a copies"
    echo "## gate_r8m1c4.sh -> gate_r8m2a.sh"
    diff -u "$S/gate_r8m1c4.sh" "$S/gate_r8m2a.sh"
    echo "## gate_check_r8m1c4.py -> gate_check_r8m2a.py"
    diff -u "$S/gate_check_r8m1c4.py" "$S/gate_check_r8m2a.py"
    echo "## gate_allow_r8m1c4_start.txt -> gate_allow_r8m2a_start.txt"
    diff -u "$S/gate_allow_r8m1c4_start.txt" "$S/gate_allow_r8m2a_start.txt"
    echo "## gate_allow_r8m1c4_end.txt -> gate_allow_r8m2a_end.txt"
    diff -u "$S/gate_allow_r8m1c4_end.txt" "$S/gate_allow_r8m2a_end.txt"
    echo "## diff_gate_r8m1c4.sh -> diff_gate_r8m2a.sh"
    diff -u "$S/diff_gate_r8m1c4.sh" "$S/diff_gate_r8m2a.sh"
} > "$OUT"
echo "diff_gate_r8m2a: wrote $OUT"
exit 0
