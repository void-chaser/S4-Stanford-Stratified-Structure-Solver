#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_final_r8_m0.sh -- P05-S4 R8 M0, final commit (closing brief section 5).  New file.
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/commit_final_r8_m0.sh p05-s4r8
# 1) writes git status to $EV/status_before_final_r8.txt (new; refused if it exists)
# 2) writes the commit message to $EV/COMMIT_MSG_R8_M0_FINAL.txt (new)
# 3) checks that the working tree is exactly the expected set (refuses otherwise)
# 4) git add of the listed paths only (no add -A, no add .), then git commit -F
# 5) writes $EV/FINAL_GIT_R8_M0.txt (new): git log -3 --oneline and git status --short after the commit
# Git writes only .git/index and .git/objects.  The commit message is passed with -F.
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "commit_final_r8_m0: first argument must be p05-s4r8" >&2; exit 2; }
test ! -e "$EV/status_before_final_r8.txt" || { echo "commit_final_r8_m0: REFUSED exists: status_before_final_r8.txt" >&2; exit 2; }
test ! -e "$EV/COMMIT_MSG_R8_M0_FINAL.txt" || { echo "commit_final_r8_m0: REFUSED exists: COMMIT_MSG_R8_M0_FINAL.txt" >&2; exit 2; }
test ! -e "$EV/FINAL_GIT_R8_M0.txt" || { echo "commit_final_r8_m0: REFUSED exists: FINAL_GIT_R8_M0.txt" >&2; exit 2; }
git status --short > "$EV/status_before_final_r8.txt" 2>&1 || { echo "commit_final_r8_m0: git status failed" >&2; exit 2; }
MSG='P05-S4 R8 M0 on F3: builds, seam plain, D smoke 8/8 MATCH (U113/U119/U124), F2-F3 no-injection 117/117 IDENTICAL, closeout gate per U133, rulings U133-U136, STATE updated. awaiting user review'
printf '%s\n' "$MSG" > "$EV/COMMIT_MSG_R8_M0_FINAL.txt"
EXPECT_SET="checkpoints/p05/STATE.md
checkpoints/p05/P05_S4R8_REPORT_M0.md
checkpoints/p05/briefs/P05_S4R8_BRIEF_M0_CLOSE.md
checkpoints/p05/registries/RULINGS.tsv
checkpoints/p05/registries/s4r8/BUILD_R8.tsv
checkpoints/p05/registries/s4r8/DRIVERS_R8.tsv
checkpoints/p05/registries/s4r8/DRIVERS_R8_F2_REUSED.tsv
checkpoints/p05/registries/s4r8/DRIVER_MAP_R8_D.tsv
checkpoints/p05/registries/s4r8/D_PREPARE_CHECK_R8.tsv
checkpoints/p05/registries/s4r8/D_SUMMARY_R8.txt
checkpoints/p05/registries/s4r8/ERRATA_8.txt
checkpoints/p05/registries/s4r8/EXPECT_R8_D.txt
checkpoints/p05/registries/s4r8/EXPECT_R8_NOINJECT.txt
checkpoints/p05/registries/s4r8/GATE3_VS_GATE2_DIFF_R8.txt
checkpoints/p05/registries/s4r8/GATE_R8_M0.txt
checkpoints/p05/registries/s4r8/GATE_R8_M0_R2.txt
checkpoints/p05/registries/s4r8/GATE_R8_M0_R2_END.txt
checkpoints/p05/registries/s4r8/GATE_R8_M0_R3_END.txt
checkpoints/p05/registries/s4r8/PRERUN_CHECKS_R8_M0.txt
checkpoints/p05/registries/s4r8/RESULTS_R8_D_pass1.tsv
checkpoints/p05/registries/s4r8/RESULTS_R8_D_pass2.tsv
checkpoints/p05/registries/s4r8/RESULTS_R8_NOINJECT_run1.tsv
checkpoints/p05/registries/s4r8/RUNNER_DIFF_R8_M0.txt
checkpoints/p05/registries/s4r8/S4R7_MANIFEST_CHECK_R8_R2.tsv
checkpoints/p05/registries/s4r8/S4R7_MANIFEST_CHECK_R8_R2_END.tsv
checkpoints/p05/registries/s4r8/S4R7_RECHECK_R8_R3_END.txt
checkpoints/p05/registries/s4r8/SEAM_DIFF_F2_vs_F3_R8.txt
checkpoints/p05/registries/s4r8/SHA256SUMS.txt
checkpoints/p05/registries/s4r8/TREE_CHECK_R8.txt
checkpoints/p05/registries/s4r8/status_before_rec_r8.txt
testing/d003/stage_s4r8/build_s4r8.sh
testing/d003/stage_s4r8/build_seam_plain_r8.sh
testing/d003/stage_s4r8/commit_final_r8_m0.sh
testing/d003/stage_s4r8/compare_build_r8.sh
testing/d003/stage_s4r8/compare_seam_r8.sh
testing/d003/stage_s4r8/copy_registries_r8.sh
testing/d003/stage_s4r8/expect_noinject_r8.py
testing/d003/stage_s4r8/export_r8.sh
testing/d003/stage_s4r8/gate3_diff_r8.sh
testing/d003/stage_s4r8/gate3_r8.sh
testing/d003/stage_s4r8/link_drivers_r8.sh
testing/d003/stage_s4r8/manifest_r8.sh
testing/d003/stage_s4r8/normalise_diff_r8.awk
testing/d003/stage_s4r8/prepare_d_r8.py
testing/d003/stage_s4r8/recheck_s4r7_r8_r3.py
testing/d003/stage_s4r8/reuse_f2_drivers_r8.sh
testing/d003/stage_s4r8/run_d_r8.py
testing/d003/stage_s4r8/run_noinject_equiv_r8.sh
testing/d003/stage_s4r8/runner_diff_r8.sh
testing/d003/stage_s4r8/seam_r8.sh
testing/d003/stage_s4r8/summarize_d_r8.py"
GOT=$(git status --short --untracked-files=all 2>&1 | sed 's/^...//' | LC_ALL=C sort)
WANT=$(printf '%s\n' "$EXPECT_SET" | LC_ALL=C sort)
if [ "$GOT" != "$WANT" ]; then
    echo "commit_final_r8_m0: REFUSED: working tree differs from the expected final set" >&2
    echo "$GOT" >&2
    exit 2
fi
git add -- checkpoints/p05/STATE.md checkpoints/p05/P05_S4R8_REPORT_M0.md checkpoints/p05/briefs/P05_S4R8_BRIEF_M0_CLOSE.md checkpoints/p05/registries/RULINGS.tsv checkpoints/p05/registries/s4r8/BUILD_R8.tsv checkpoints/p05/registries/s4r8/DRIVERS_R8.tsv checkpoints/p05/registries/s4r8/DRIVERS_R8_F2_REUSED.tsv checkpoints/p05/registries/s4r8/DRIVER_MAP_R8_D.tsv checkpoints/p05/registries/s4r8/D_PREPARE_CHECK_R8.tsv checkpoints/p05/registries/s4r8/D_SUMMARY_R8.txt checkpoints/p05/registries/s4r8/ERRATA_8.txt checkpoints/p05/registries/s4r8/EXPECT_R8_D.txt checkpoints/p05/registries/s4r8/EXPECT_R8_NOINJECT.txt checkpoints/p05/registries/s4r8/GATE3_VS_GATE2_DIFF_R8.txt checkpoints/p05/registries/s4r8/GATE_R8_M0.txt checkpoints/p05/registries/s4r8/GATE_R8_M0_R2.txt checkpoints/p05/registries/s4r8/GATE_R8_M0_R2_END.txt checkpoints/p05/registries/s4r8/GATE_R8_M0_R3_END.txt checkpoints/p05/registries/s4r8/PRERUN_CHECKS_R8_M0.txt checkpoints/p05/registries/s4r8/RESULTS_R8_D_pass1.tsv checkpoints/p05/registries/s4r8/RESULTS_R8_D_pass2.tsv checkpoints/p05/registries/s4r8/RESULTS_R8_NOINJECT_run1.tsv checkpoints/p05/registries/s4r8/RUNNER_DIFF_R8_M0.txt checkpoints/p05/registries/s4r8/S4R7_MANIFEST_CHECK_R8_R2.tsv checkpoints/p05/registries/s4r8/S4R7_MANIFEST_CHECK_R8_R2_END.tsv checkpoints/p05/registries/s4r8/S4R7_RECHECK_R8_R3_END.txt checkpoints/p05/registries/s4r8/SEAM_DIFF_F2_vs_F3_R8.txt checkpoints/p05/registries/s4r8/SHA256SUMS.txt checkpoints/p05/registries/s4r8/TREE_CHECK_R8.txt checkpoints/p05/registries/s4r8/status_before_rec_r8.txt testing/d003/stage_s4r8/build_s4r8.sh testing/d003/stage_s4r8/build_seam_plain_r8.sh testing/d003/stage_s4r8/commit_final_r8_m0.sh testing/d003/stage_s4r8/compare_build_r8.sh testing/d003/stage_s4r8/compare_seam_r8.sh testing/d003/stage_s4r8/copy_registries_r8.sh testing/d003/stage_s4r8/expect_noinject_r8.py testing/d003/stage_s4r8/export_r8.sh testing/d003/stage_s4r8/gate3_diff_r8.sh testing/d003/stage_s4r8/gate3_r8.sh testing/d003/stage_s4r8/link_drivers_r8.sh testing/d003/stage_s4r8/manifest_r8.sh testing/d003/stage_s4r8/normalise_diff_r8.awk testing/d003/stage_s4r8/prepare_d_r8.py testing/d003/stage_s4r8/recheck_s4r7_r8_r3.py testing/d003/stage_s4r8/reuse_f2_drivers_r8.sh testing/d003/stage_s4r8/run_d_r8.py testing/d003/stage_s4r8/run_noinject_equiv_r8.sh testing/d003/stage_s4r8/runner_diff_r8.sh testing/d003/stage_s4r8/seam_r8.sh testing/d003/stage_s4r8/summarize_d_r8.py || { echo "commit_final_r8_m0: git add failed" >&2; exit 2; }
git commit -F "$EV/COMMIT_MSG_R8_M0_FINAL.txt" || { echo "commit_final_r8_m0: git commit failed" >&2; exit 2; }
{
    git log -3 --oneline 2>&1
    echo "---"
    git status --short 2>&1
} > "$EV/FINAL_GIT_R8_M0.txt"
echo "commit_final_r8_m0: committed; FINAL_GIT_R8_M0.txt written"
exit 0
