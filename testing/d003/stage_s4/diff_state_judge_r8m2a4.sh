REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a4; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# diff_state_judge_r8m2a4.sh -- unified diff between r6c_judge.py and state_judge_m2_r8m2a4.py
set -u
OUT=$EV/SRC_DIFF_STATE_JUDGE_R8_M2a4.txt
diff -u "$REPO/testing/d003/stage_s4/r6c_judge.py" "$REPO/testing/d003/stage_s4/state_judge_m2_r8m2a4.py" > "$OUT" || true
echo "diff_state_judge_r8m2a4: wrote $OUT"
exit 0
