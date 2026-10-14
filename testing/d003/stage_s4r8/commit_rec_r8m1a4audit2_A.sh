#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_rec_r8m1a4audit2_A.sh -- P05-S4 R8 M1a CONT3a audit part 2, phase A: as-is record commit of the existing
# 31 round-prior items plus U183-U187, E8-66 and the start gate copy (U186).  New file.  Usage (through safe_run):
#   sh testing/d003/safe_run.sh p05-s4r8/m1a4audit2 -- sh testing/d003/stage_s4r8/commit_rec_r8m1a4audit2_A.sh p05-s4r8
# Refuses unless the phase-A end gate reports FAILS=0.  Adds paths one by one; never uses -A or '.'.
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "commit_rec_r8m1a4audit2_A: first arg must be p05-s4r8" >&2; exit 2; }
ENDFILE="$EV/GATE_R8_M1a4_AUDIT2_END_A.txt"
test -f "$ENDFILE" || { echo "commit_rec_r8m1a4audit2_A: end gate missing: $ENDFILE" >&2; exit 2; }
[ "$(tail -n 1 "$ENDFILE")" = "FAILS=0" ] || { echo "commit_rec_r8m1a4audit2_A: end gate is not FAILS=0" >&2; exit 2; }
[ -z "$(git diff --cached --name-only 2>&1)" ] || { echo "commit_rec_r8m1a4audit2_A: index already has staged files" >&2; exit 2; }

FILES_TO_ADD="
checkpoints/p05/STATE.md
checkpoints/p05/registries/RULINGS.tsv
checkpoints/p05/registries/s4r8/ERRATA_8.txt
checkpoints/p05/P05_S4R8_REPORT_M1a_CONT3a_AUDIT.md
checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a_AUDIT.md
checkpoints/p05/registries/s4r8/M1a/ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT.tsv
checkpoints/p05/registries/s4r8/M1a/ADDITIONS_STRICT_R8_M1a4AUDIT_FIRSTRUN_MISMATCH3.tsv
checkpoints/p05/registries/s4r8/M1a/ADDITIONS_STRICT_R8_M1a4AUDIT_R2_MATCH9.tsv
checkpoints/p05/registries/s4r8/M1a/ADDITIONS_STRICT_R8_M1a4AUDIT_R2_MATCH9_SUMMARY.txt
checkpoints/p05/registries/s4r8/M1a/AUDIT_UNITS_VS_HISTORY_R8_M1a4AUDIT.tsv
checkpoints/p05/registries/s4r8/M1a/CALLSEQ_KMAX_R8_M1a4_R3.tsv
checkpoints/p05/registries/s4r8/M1a/CALLSEQ_POINT_COVERAGE_CHECK_R8_M1a4_R3.tsv
checkpoints/p05/registries/s4r8/M1a/CALLSEQ_VALIDITY_R8_M1a4_R3.tsv
checkpoints/p05/registries/s4r8/M1a/COMPARE_UNITS_VS_HISTORY_R8_M1a4AUDIT.tsv
checkpoints/p05/registries/s4r8/M1a/DRIVER_TAG_AUDIT_R8_M1a4.tsv
checkpoints/p05/registries/s4r8/M1a/PRERUN_CHECKS_R8_M1a4AUDIT.txt
checkpoints/p05/registries/s4r8/M1a/SHA256SUMS_M1a4AUDIT.txt
checkpoints/p05/registries/s4r8/M1a/STRICT_RECHECK_CALLSEQ_R8_M1a4AUDIT.tsv
checkpoints/p05/registries/s4r8/M1a/STRICT_RECHECK_CALLSEQ_R8_M1a4AUDIT_SUMMARY.txt
testing/d003/stage_s4r8/append_errata_r8m1a4audit.py
testing/d003/stage_s4r8/audit_driver_tags_r8m1a4.py
testing/d003/stage_s4r8/audit_units_vs_history_r8m1a4audit.py
testing/d003/stage_s4r8/compare_units_vs_history_r8m1a4audit.py
testing/d003/stage_s4r8/copy_registries_r8m1a4audit.py
testing/d003/stage_s4r8/copy_registries_r8m1a4audit_b.py
testing/d003/stage_s4r8/manifest_evidence_r8m1a4audit.py
testing/d003/stage_s4r8/manifest_final_r8m1a4.sh
testing/d003/stage_s4r8/manifest_registries_r8m1a4audit.py
testing/d003/stage_s4r8/map22_strict_r8m1a4audit.py
testing/d003/stage_s4r8/prerun_log_r8m1a4audit.sh
testing/d003/stage_s4r8/strict_recheck_callseq_r8m1a4audit.py
testing/d003/stage_s4r8/summarize_additions_strict_r8m1a4audit.py
checkpoints/p05/registries/s4r8/M1a/GATE_R8_M1a4_AUDIT2_START_A.txt
testing/d003/stage_s4r8/gate10_r8m1a4audit2.sh
testing/d003/stage_s4r8/gate_allow_r8m1a4audit2_A.txt
testing/d003/stage_s4r8/append_rulings_r8m1a4audit2.py
testing/d003/stage_s4r8/append_errata_r8m1a4audit2.py
"

for f in $FILES_TO_ADD; do
    test -f "$REPO/$f" || { echo "commit_rec_r8m1a4audit2_A: file to add missing: $f" >&2; exit 2; }
    git add -- "$REPO/$f" || { echo "commit_rec_r8m1a4audit2_A: git add failed: $f" >&2; exit 2; }
done

STAGED=$(git diff --cached --name-only 2>&1)
[ -z "$(printf '%s\n' "$STAGED" | grep '^S4/' )" ] || { echo "commit_rec_r8m1a4audit2_A: S4/ was staged" >&2; exit 2; }
[ -z "$(git diff --cached --name-only --diff-filter=MD -- testing/d003 2>&1)" ] || { echo "commit_rec_r8m1a4audit2_A: a tracked testing/d003 file is modified or deleted" >&2; exit 2; }
[ -z "$(git diff --cached --name-only -- testing/d003/judge_d003.py 2>&1)" ] || { echo "commit_rec_r8m1a4audit2_A: judge is staged" >&2; exit 2; }

MSG="P05-S4 R8 M1a cont3a audit part1 stop record (as-is) + rulings U183-U187 + E8-66; awaiting user review"
git commit -q -m "$MSG" || { echo "commit_rec_r8m1a4audit2_A: commit failed" >&2; exit 2; }
echo "commit_rec_r8m1a4audit2_A: committed $(git rev-parse HEAD)"
echo "commit_rec_r8m1a4audit2_A: HEAD_PARENT=$(git rev-parse HEAD^)"
exit 0
