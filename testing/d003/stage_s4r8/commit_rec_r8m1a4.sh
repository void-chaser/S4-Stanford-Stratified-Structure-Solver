#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_rec_r8m1a4.sh -- P05-S4 R8 M1a CONT3a record commit.  New file.
# Usage (through safe_run):
#   sh testing/d003/stage_s4r8/commit_rec_r8m1a4.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "commit_rec_r8m1a4: first arg must be p05-s4r8" >&2; exit 2; }

# 1. Verify gate end FAILS=0
ENDFILE="$EV/GATE_R8_M1a4_END.txt"
test -f "$ENDFILE" || { echo "commit_rec_r8m1a4: end gate missing: $ENDFILE" >&2; exit 2; }
[ "$(tail -n 1 "$ENDFILE")" = "FAILS=0" ] || { echo "commit_rec_r8m1a4: end gate is not FAILS=0" >&2; exit 2; }

# 2. Add files explicitly one by one
FILES_TO_ADD="
checkpoints/p05/STATE.md
checkpoints/p05/registries/RULINGS.tsv
checkpoints/p05/registries/s4r8/ERRATA_8.txt
checkpoints/p05/P05_S4R8_HANDOVER_M1a_CONT3a_PAUSE.md
checkpoints/p05/P05_S4R8_REPORT_M1a_CONT3a.md
checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a.md
checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a_RESUME.md
checkpoints/p05/registries/s4r8/M1a/ADDITIONS_MAPPING_22_R8_M1a4.tsv
checkpoints/p05/registries/s4r8/M1a/APPEND_ERRATA_R8_M1a4_R3.txt
checkpoints/p05/registries/s4r8/M1a/APPEND_R8_M1a4.txt
checkpoints/p05/registries/s4r8/M1a/CALLSEQ_ADDITIONS_R8_M1a4.tsv
checkpoints/p05/registries/s4r8/M1a/CALLSEQ_F2_F3_R8_M1a4_R2.tsv
checkpoints/p05/registries/s4r8/M1a/CALLSEQ_KMAX_R8_M1a4_R2.tsv
checkpoints/p05/registries/s4r8/M1a/CALLSEQ_POINT_COVERAGE_CHECK_R8_M1a4_R2.tsv
checkpoints/p05/registries/s4r8/M1a/CALLSEQ_POINT_COVERAGE_R8_M1a4_R3.tsv
checkpoints/p05/registries/s4r8/M1a/CALLSEQ_RUNS_R8_M1a4_R3.tsv
checkpoints/p05/registries/s4r8/M1a/CALLSEQ_UNITS_R8_M1a4_R3.tsv
checkpoints/p05/registries/s4r8/M1a/CALLSEQ_VALIDITY_R8_M1a4_R2.tsv
checkpoints/p05/registries/s4r8/M1a/COUNTED_FAMILIES_R8_M1a4_R3.tsv
checkpoints/p05/registries/s4r8/M1a/EXPECT_ADDITIONS_R8_M1a4.txt
checkpoints/p05/registries/s4r8/M1a/EXPECT_CALLSEQ_R8_M1a4_R3.txt
checkpoints/p05/registries/s4r8/M1a/GATE_R8_M1a4_RESUME_R2.txt
checkpoints/p05/registries/s4r8/M1a/GATE_R8_M1a4_START.txt
checkpoints/p05/registries/s4r8/M1a/GATE_R8_M1a4_END.txt
checkpoints/p05/registries/s4r8/M1a/RUNNER_DIFF_R8_M1a4.txt
checkpoints/p05/registries/s4r8/M1a/S4R7_RECHECK_GATE_R8_M1A4_RESUME_R2.tsv
checkpoints/p05/registries/s4r8/M1a/S4R7_RECHECK_GATE_R8_M1A4_START.tsv
checkpoints/p05/registries/s4r8/M1a/S4R7_RECHECK_GATE_R8_M1A4_END.tsv
checkpoints/p05/registries/s4r8/M1a/SHA256SUMS_M1a4.txt
checkpoints/p05/registries/s4r8/M1a/SHA256SUMS_M1a4_END.txt
checkpoints/p05/registries/s4r8/M1a/SOURCE_HASHES_R8_M1a4_R3.tsv
checkpoints/p05/registries/s4r8/M1a/USED_IN_M1_CORRECTION_R8_M1a4.tsv
testing/d003/stage_s4r8/a1map_r8m1a4.gdb
testing/d003/stage_s4r8/a1map_r8m1a4.sh
testing/d003/stage_s4r8/append_errata_r8m1a4.txt
testing/d003/stage_s4r8/append_errata_r8m1a4_r3.sh
testing/d003/stage_s4r8/append_errata_r8m1a4_r3.txt
testing/d003/stage_s4r8/append_r8m1a4.sh
testing/d003/stage_s4r8/append_rulings_r8m1a4.tsv
testing/d003/stage_s4r8/b_map_r8m1a4.gdb
testing/d003/stage_s4r8/b_map_r8m1a4.sh
testing/d003/stage_s4r8/callseq_r8m1a4_gdb.py
testing/d003/stage_s4r8/callseq_runner_r8m1a4.py
testing/d003/stage_s4r8/commit_rec_r8m1a4.sh
testing/d003/stage_s4r8/compare_callseq_r8m1a4.py
testing/d003/stage_s4r8/copy_end_m1a4.sh
testing/d003/stage_s4r8/copy_m1a4.sh
testing/d003/stage_s4r8/counted_families_r8m1a4.py
testing/d003/stage_s4r8/gate9_r8m1a4.sh
testing/d003/stage_s4r8/gate9_resume_r8m1a4.sh
testing/d003/stage_s4r8/recheck_s4r7_r8m1a4.py
testing/d003/stage_s4r8/summarize_additions_r8m1a4.py
"

for f in $FILES_TO_ADD; do
    test -f "$REPO/$f" || { echo "commit_rec_r8m1a4: file to add missing: $f" >&2; exit 2; }
    git add "$REPO/$f" || { echo "commit_rec_r8m1a4: git add failed: $f" >&2; exit 2; }
done

# 3. Verify staged files only
STAGED_DIFF=$(git diff --cached --name-only -- S4/ 2>&1)
[ -z "$STAGED_DIFF" ] || { echo "commit_rec_r8m1a4: S4/ was staged!" >&2; exit 2; }

# Verify no historical tracked testing/d003 files were modified
TRACKED_MOD=$(git diff --cached --name-only --diff-filter=M -- testing/d003 2>&1)
[ -z "$TRACKED_MOD" ] || { echo "commit_rec_r8m1a4: tracked testing/d003 modified: $TRACKED_MOD" >&2; exit 2; }

MSG="P05-S4 R8 M1a cont3a: complete no-injection F2-F3 counter/site sequence mapping and S3R4 additions map recheck; E8-55 clarification; awaiting user review"

git commit -m "$MSG" || { echo "commit_rec_r8m1a4: git commit failed" >&2; exit 2; }

FINAL_FILE="$EV/FINAL_GIT_R8_M1a4.txt"
{
    printf '=== git log -3 ===\n'
    git log -3
    printf '\n=== git rev-parse HEAD ===\n'
    git rev-parse HEAD
    printf '\n=== git rev-parse HEAD^ ===\n'
    git rev-parse HEAD^
    printf '\n=== git rev-parse HEAD:S4 ===\n'
    git rev-parse HEAD:S4
    printf '\n=== git status --short ===\n'
    git status --short
} > "$FINAL_FILE"

echo "commit_rec_r8m1a4: commit successful -> $FINAL_FILE"
exit 0
