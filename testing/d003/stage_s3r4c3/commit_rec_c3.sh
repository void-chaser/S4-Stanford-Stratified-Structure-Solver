REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_rec_c3.sh -- CONT3 record commit (section 2 of the brief).  Stages only the listed files, commits with the message file.
cd "$REPO" || exit 2
git add -- checkpoints/p05/registries/RULINGS.tsv checkpoints/p05/ERRATA_S3R4.txt checkpoints/p05/briefs/P05_S3R4_CONT3_BRIEF.md testing/d003/stage_s3r4c2/link_c2.sh testing/d003/stage_s3r4c2/link_init_c2.sh testing/d003/stage_s3r4c2/run_a_c2.sh > "$EV/commit_rec_c3_add.txt" 2>&1
echo "add rc=$?"
git commit -q -F "$EV/COMMIT_MSG_CONT3_REC.txt" > "$EV/commit_rec_c3_stdout.txt" 2>&1
echo "commit rc=$?"
git log -1 --format=%H > "$EV/commit_rec_c3_hash.txt" 2>&1
git log -1 --oneline > "$EV/commit_rec_c3_oneline.txt" 2>&1
echo "done"
