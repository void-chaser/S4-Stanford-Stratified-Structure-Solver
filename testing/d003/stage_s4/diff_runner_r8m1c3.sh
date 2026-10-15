REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# diff_runner_r8m1c3.sh -- P05-S4 R8 M1c3: unified diffs of the runner and record scripts (r8m1c2 originals vs r8m1c3 copies).
# Output: $EV/RUNNER_DIFF_R8_M1c3.txt (diff exit 1 = differences, expected).
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m1c3 -- sh testing/d003/stage_s4/diff_runner_r8m1c3.sh
set -u
S=$REPO/testing/d003/stage_s4
OUT=$EV/RUNNER_DIFF_R8_M1c3.txt
test ! -e "$OUT" || { echo "diff_runner_r8m1c3: REFUSED exists (U17): $OUT" >&2; exit 2; }
{
    echo "# RUNNER_DIFF_R8_M1c3 -- diff -u of r8m1c2 originals against r8m1c3 copies"
    echo "## run_m1c_r8m1c2.sh -> run_m1c_r8m1c3.sh"
    diff -u "$S/run_m1c_r8m1c2.sh" "$S/run_m1c_r8m1c3.sh"
    echo "## record_drivers_r8m1c2.py -> record_drivers_r8m1c3.py"
    diff -u "$S/record_drivers_r8m1c2.py" "$S/record_drivers_r8m1c3.py"
} > "$OUT"
echo "diff_runner_r8m1c3: wrote $OUT"
exit 0
