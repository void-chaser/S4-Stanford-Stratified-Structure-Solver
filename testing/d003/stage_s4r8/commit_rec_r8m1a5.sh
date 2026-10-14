#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_rec_r8m1a5.sh -- record commit of CONT3b1 (brief section 6.6).  New file.
# Adds each path explicitly with git add -- (never -A or .), this script included.  Commit message per brief.
# It does NOT write FINAL_GIT_R8_M1a5.txt: run final_git_r8m1a5.sh POST afterwards (brief 6.6, after the commit).
# It refuses to run if any listed path is missing.
set -u
MSG="P05-S4 R8 M1a cont3b1: audit3 accepted (U192), STATE compacted, E8-68/E8-69, M1b/M1c formal pre-registration and counts (no runs); awaiting user review"
test ! -e "$EV/FINAL_GIT_R8_M1a5.txt" || { echo "commit_rec: FINAL_GIT_R8_M1a5.txt exists (U17)" >&2; exit 2; }
PATHS="
checkpoints/p05/STATE.md
checkpoints/p05/registries/RULINGS.tsv
checkpoints/p05/registries/s4r8/ERRATA_8.txt
checkpoints/p05/P05_S4R8_REPORT_M1a_CONT3b1.md
checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3b1.md
checkpoints/p05/registries/s4r8/M1a/FINAL_GIT_R8_M1a4AUDIT3_POST.txt
checkpoints/p05/registries/s4r8/M1a/GATE_R8_M1a5_START.txt
checkpoints/p05/registries/s4r8/M1a/K_SOURCE_PLANCALL58_R8_M1a5.tsv
checkpoints/p05/registries/s4r8/M1a/PREREG_COUNTS_R8_M1a5.tsv
checkpoints/p05/registries/s4r8/M1a/PREREG_INPUTS_R8_M1a5.tsv
checkpoints/p05/registries/s4r8/M1a/PREREG_STOP_R8_M1a5.tsv
checkpoints/p05/registries/s4r8/M1a/SHA256SUMS_M1a5.txt
checkpoints/p05/registries/s4r8/M1a/STATE_HISTORY_R8_M1a5.md
checkpoints/p05/registries/s4r8/M1a/SURVEY_R8_M1a5.txt
testing/d003/stage_s4r8/append_r8m1a5.sh
testing/d003/stage_s4r8/check_facts_r8m1a5.py
testing/d003/stage_s4r8/compact_state_r8m1a5.py
testing/d003/stage_s4r8/copy_m1a5.sh
testing/d003/stage_s4r8/final_git_r8m1a5.sh
testing/d003/stage_s4r8/gate12_r8m1a5.sh
testing/d003/stage_s4r8/gate_allow_r8m1a5_end.txt
testing/d003/stage_s4r8/gate_allow_r8m1a5_start.txt
testing/d003/stage_s4r8/make_prereg_r8m1a5.py
testing/d003/stage_s4r8/manifest_r8m1a5.sh
testing/d003/stage_s4r8/report_facts_r8m1a5.py
testing/d003/stage_s4r8/state_history_r8m1a5.sh
testing/d003/stage_s4r8/survey_r8m1a5.py
testing/d003/stage_s4r8/commit_rec_r8m1a5.sh
"
cd "$REPO" || exit 2
for p in $PATHS; do
    test -e "$p" || { echo "commit_rec: missing path $p" >&2; exit 2; }
done
for p in $PATHS; do
    git add -- "$p" || { echo "commit_rec: git add failed for $p" >&2; exit 2; }
done
git commit -m "$MSG" || { echo "commit_rec: git commit failed" >&2; exit 2; }
echo "commit_rec_r8m1a5: committed"
exit 0
