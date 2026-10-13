REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_rec_c5.sh -- CONT5 record commit (brief section 2).  Stages only the listed paths; no "git add -A" or "git add .".
# Writes the status before staging, stages, commits with the message file, and records the commit hash.
cd "$REPO" || exit 2
git status --short > "$EV/status_before_rec_c5.txt" 2>&1
echo "status written rc=$?"
test -e "$EV/COMMIT_MSG_CONT5_REC.txt" || { echo "REFUSED: no message file"; exit 2; }
git add -- checkpoints/p05/registries/RULINGS.tsv checkpoints/p05/ERRATA_S3R4.txt \
  checkpoints/p05/briefs/P05_S3R4_CONT4_BRIEF.md checkpoints/p05/briefs/P05_S3R4_CONT5_BRIEF.md \
  checkpoints/p05/P05_S3R4_CLOSEOUT_CONT3.md checkpoints/p05/P05_S3R4_CLOSEOUT_CONT4.md \
  checkpoints/p05/registries/s3r4c3 testing/d003/stage_s3r4c3 > "$EV/commit_rec_c5_add.txt" 2>&1
echo "add rc=$?"
git commit -q -F "$EV/COMMIT_MSG_CONT5_REC.txt" > "$EV/commit_rec_c5_stdout.txt" 2>&1
echo "commit rc=$?"
git log -1 --format=%H > "$EV/commit_rec_c5_hash.txt" 2>&1
git log -1 --oneline > "$EV/commit_rec_c5_oneline.txt" 2>&1
echo "done"
