REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_final_c5.sh -- CONT5 final commit (brief section 4).  Stages only the listed paths; writes the post-commit
# git log and git status to $EV/FINAL_GIT_C5.txt after the commit (not pre-filled).
cd "$REPO" || exit 2
test -e "$EV/COMMIT_MSG_CONT5_FINAL.txt" || { echo "REFUSED: no message file"; exit 2; }
git add -- checkpoints/p05/STATE.md checkpoints/p05/ERRATA_S3R4.txt checkpoints/p05/P05_S3R4_CLOSEOUT_CONT5.md \
  checkpoints/p05/registries/s3r4c5 testing/d003/stage_s3r4c5 > "$EV/commit_final_c5_add.txt" 2>&1
echo "add rc=$?"
git commit -q -F "$EV/COMMIT_MSG_CONT5_FINAL.txt" > "$EV/commit_final_c5_stdout.txt" 2>&1
echo "commit rc=$?"
{
  echo "# FINAL_GIT_C5 -- read after the final commit (CONT5 section 12)."
  echo "## git log -3 --oneline"
  git log -3 --oneline
  echo "## git status --short"
  git status --short
} > "$EV/FINAL_GIT_C5.txt" 2>&1
echo "final git record written"
