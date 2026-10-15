REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c4; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# diff_compare_r8m1c4.sh -- P05-S4 R8 M1c4: diff -u of compare_m1c_f3_r8m1c3.py against compare_m1c_f3_r8m1c4.py (U227).
# Output: $EV/COMPARE_DIFF_R8_M1c4.txt (diff exit 1 = differences, expected).
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m1c4 -- sh testing/d003/stage_s4/diff_compare_r8m1c4.sh
set -u
S=$REPO/testing/d003/stage_s4
OUT=$EV/COMPARE_DIFF_R8_M1c4.txt
test ! -e "$OUT" || { echo "diff_compare_r8m1c4: REFUSED exists (U17): $OUT" >&2; exit 2; }
{
    echo "# COMPARE_DIFF_R8_M1c4 -- diff -u of compare_m1c_f3_r8m1c3.py against compare_m1c_f3_r8m1c4.py (U227)"
    diff -u "$S/compare_m1c_f3_r8m1c3.py" "$S/compare_m1c_f3_r8m1c4.py"
} > "$OUT"
echo "diff_compare_r8m1c4: wrote $OUT"
exit 0
