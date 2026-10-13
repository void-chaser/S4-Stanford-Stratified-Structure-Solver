#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_rec_r8.sh -- P05-S4 R8 M0 restart 2, records commit (RESTART2 section 4).  New file.
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/commit_rec_r8.sh p05-s4r8
# 1) writes git status to $EV/status_before_rec_r8.txt (new file; refused if it exists)
# 2) writes the commit message to $EV/COMMIT_MSG_R8_REC.txt (new file)
# 3) checks that every untracked or modified path is one of the expected records (refuses otherwise)
# 4) git add of the listed paths only (no add -A, no add .), then git commit with the message from step 2
# Git writes only .git/index and .git/objects through the commit.  The commit message is passed with -F.
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "commit_rec_r8: first argument must be p05-s4r8" >&2; exit 2; }
test ! -e "$EV/status_before_rec_r8.txt" || { echo "commit_rec_r8: REFUSED exists: status_before_rec_r8.txt" >&2; exit 2; }
test ! -e "$EV/COMMIT_MSG_R8_REC.txt" || { echo "commit_rec_r8: REFUSED exists: COMMIT_MSG_R8_REC.txt" >&2; exit 2; }
git status --short > "$EV/status_before_rec_r8.txt" 2>&1 || { echo "commit_rec_r8: git status failed" >&2; exit 2; }
MSG='P05-S4 R8 M0 records (restart 2): rulings U121-U132, errata ES3R4-31 and ERRATA_8 (E8-1..E8-4); gate per U128/U132; briefs archived. awaiting user review'
printf '%s\n' "$MSG" > "$EV/COMMIT_MSG_R8_REC.txt"
EXPECT_SET="checkpoints/p05/ERRATA_S3R4.txt
checkpoints/p05/briefs/P05_S4R8_BRIEF_M0.md
checkpoints/p05/briefs/P05_S4R8_BRIEF_M0_RESTART.md
checkpoints/p05/briefs/P05_S4R8_BRIEF_M0_RESTART2.md
checkpoints/p05/registries/RULINGS.tsv
checkpoints/p05/registries/s4r8/ERRATA_8.txt
testing/d003/stage_s4r8/check_s4r7_manifests_r8.py
testing/d003/stage_s4r8/commit_rec_r8.sh
testing/d003/stage_s4r8/gate2_r8.sh
testing/d003/stage_s4r8/gate_r8.sh
testing/d003/stage_s4r8/prerun_log_r8.sh"
GOT=$(git status --short --untracked-files=all 2>&1 | sed 's/^...//' | LC_ALL=C sort)
WANT=$(printf '%s\n' "$EXPECT_SET" | LC_ALL=C sort)
if [ "$GOT" != "$WANT" ]; then
    echo "commit_rec_r8: REFUSED: working tree differs from the expected record set" >&2
    echo "$GOT" >&2
    exit 2
fi
git add -- checkpoints/p05/ERRATA_S3R4.txt checkpoints/p05/briefs/P05_S4R8_BRIEF_M0.md checkpoints/p05/briefs/P05_S4R8_BRIEF_M0_RESTART.md checkpoints/p05/briefs/P05_S4R8_BRIEF_M0_RESTART2.md checkpoints/p05/registries/RULINGS.tsv checkpoints/p05/registries/s4r8/ERRATA_8.txt testing/d003/stage_s4r8/check_s4r7_manifests_r8.py testing/d003/stage_s4r8/commit_rec_r8.sh testing/d003/stage_s4r8/gate2_r8.sh testing/d003/stage_s4r8/gate_r8.sh testing/d003/stage_s4r8/prerun_log_r8.sh || { echo "commit_rec_r8: git add failed" >&2; exit 2; }
git commit -F "$EV/COMMIT_MSG_R8_REC.txt" || { echo "commit_rec_r8: git commit failed" >&2; exit 2; }
echo "commit_rec_r8: committed"
exit 0
