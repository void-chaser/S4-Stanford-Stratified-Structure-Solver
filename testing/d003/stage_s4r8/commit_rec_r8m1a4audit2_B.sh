#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_rec_r8m1a4audit2_B.sh -- P05-S4 R8 M1a CONT3a audit part 2, phase B: second record commit.  New file.
# Usage (through safe_run):
#   sh testing/d003/safe_run.sh p05-s4r8/m1a4audit2 -- sh testing/d003/stage_s4r8/commit_rec_r8m1a4audit2_B.sh p05-s4r8
# Refuses unless the closing end gate GATE_R8_M1a4_AUDIT2_END_B2.txt reports FAILS=0 and the index is empty.
# Adds each listed path one by one with "git add --" (never -A, never "."), verifies the staged set equals the list,
# and commits with a message ending in "awaiting user review".
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "commit_rec_r8m1a4audit2_B: first arg must be p05-s4r8" >&2; exit 2; }
ENDFILE="$EV/GATE_R8_M1a4_AUDIT2_END_B2.txt"
test -f "$ENDFILE" || { echo "commit_rec_r8m1a4audit2_B: closing end gate missing: $ENDFILE" >&2; exit 2; }
[ "$(tail -n 1 "$ENDFILE")" = "FAILS=0" ] || { echo "commit_rec_r8m1a4audit2_B: closing end gate is not FAILS=0" >&2; exit 2; }
[ -z "$(git diff --cached --name-only 2>&1)" ] || { echo "commit_rec_r8m1a4audit2_B: index already has staged files" >&2; exit 2; }

FILES_TO_ADD="
checkpoints/p05/STATE.md
checkpoints/p05/P05_S4R8_REPORT_M1a_CONT3a_AUDIT2.md
checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a_AUDIT2.md
checkpoints/p05/registries/s4r8/M1a/ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT2.tsv
checkpoints/p05/registries/s4r8/M1a/ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT2_RUN1_SUPERSEDED.tsv
checkpoints/p05/registries/s4r8/M1a/ADDITIONS_STRICT_R8_M1a4AUDIT2.tsv
checkpoints/p05/registries/s4r8/M1a/ADDITIONS_STRICT_R8_M1a4AUDIT2_RUN1_SUPERSEDED.tsv
checkpoints/p05/registries/s4r8/M1a/CONFIG_CHECK_R8_M1a4AUDIT2.tsv
checkpoints/p05/registries/s4r8/M1a/CONFIG_CHECK_R8_M1a4AUDIT2_RUN1_SUPERSEDED.tsv
checkpoints/p05/registries/s4r8/M1a/DIFF_OLD_NEW_R8_M1a4AUDIT2.tsv
checkpoints/p05/registries/s4r8/M1a/GATE_R8_M1a4_AUDIT2_END_A.txt
checkpoints/p05/registries/s4r8/M1a/GATE_R8_M1a4_AUDIT2_START_B.txt
checkpoints/p05/registries/s4r8/M1a/INVALID44_R8_M1a4AUDIT2.tsv
checkpoints/p05/registries/s4r8/M1a/K0_RULE_R8_M1a4AUDIT2.txt
checkpoints/p05/registries/s4r8/M1a/REQUEST_RECON_R8_M1a4AUDIT2.tsv
checkpoints/p05/registries/s4r8/M1a/REQUEST_TARGETS_R8_M1a4AUDIT2.tsv
checkpoints/p05/registries/s4r8/M1a/RERUN_PREREG_R8_M1a4AUDIT2.txt
checkpoints/p05/registries/s4r8/M1a/RERUN_SCOPE_R8_M1a4AUDIT2.tsv
checkpoints/p05/registries/s4r8/M1a/SEQCOMPARE_DIFF_R8_M1a4AUDIT2.tsv
checkpoints/p05/registries/s4r8/M1a/SEQCOMPARE_R8_M1a4AUDIT2.tsv
checkpoints/p05/registries/s4r8/M1a/SHA256SUMS_M1a4AUDIT2.txt
checkpoints/p05/registries/s4r8/M1a/SHA256SUMS_M1a4AUDIT2_EVIDENCE_R2.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_ADDR_R8_M1a4AUDIT2_F2_d003plain.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_ADDR_R8_M1a4AUDIT2_F3_r6dnv1.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_DBG_R8_M1a4AUDIT2_F2_d003plain.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_DBG_R8_M1a4AUDIT2_F3_r6dnv1.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT2_F2_d003plain.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT2_F2_r6dnv1.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT2_F3_r6dnv1.txt
checkpoints/p05/registries/s4r8/M1a/TRACER_AUDIT_R8_M1a4AUDIT2.tsv
testing/d003/stage_s4r8/check_manifest_r8m1a4audit2.sh
testing/d003/stage_s4r8/check_manifest_r8m1a4audit2_r2.sh
testing/d003/stage_s4r8/check_registries_r8m1a4audit2.sh
testing/d003/stage_s4r8/classify_requests_r8m1a4audit2.py
testing/d003/stage_s4r8/commit_rec_r8m1a4audit2_A.sh
testing/d003/stage_s4r8/config_check_r8m1a4audit2.py
testing/d003/stage_s4r8/copy_registries_r8m1a4audit2.py
testing/d003/stage_s4r8/diff_gate10_r2_r8m1a4audit2.sh
testing/d003/stage_s4r8/export_tables_r8m1a4audit2.py
testing/d003/stage_s4r8/gate10_r8m1a4audit2_r2.sh
testing/d003/stage_s4r8/gate_allow_r8m1a4audit2_A_commit.txt
testing/d003/stage_s4r8/manifest_evidence_r8m1a4audit2.py
testing/d003/stage_s4r8/map22_strict_r8m1a4audit2.py
testing/d003/stage_s4r8/prerun_log_r8m1a4audit2.sh
testing/d003/stage_s4r8/reconstruct_requests_r8m1a4audit2.py
testing/d003/stage_s4r8/rerun_scope_r8m1a4audit2.py
testing/d003/stage_s4r8/seqcompare_r8m1a4audit2.py
testing/d003/stage_s4r8/summarize_additions_strict_r8m1a4audit2.py
testing/d003/stage_s4r8/summary_counts_r8m1a4audit2.py
testing/d003/stage_s4r8/symq_addr_r8m1a4audit2.sh
testing/d003/stage_s4r8/symq_dbg_r8m1a4audit2.sh
testing/d003/stage_s4r8/symq_r8m1a4audit2.sh
testing/d003/stage_s4r8/tracer_audit_r8m1a4audit2.py
testing/d003/stage_s4r8/commit_rec_r8m1a4audit2_B.sh
"

for f in $FILES_TO_ADD; do
    test -f "$REPO/$f" || { echo "commit_rec_r8m1a4audit2_B: file to add missing: $f" >&2; exit 2; }
    git add -- "$REPO/$f" || { echo "commit_rec_r8m1a4audit2_B: git add failed: $f" >&2; exit 2; }
done

EXPECTED=$(printf '%s\n' $FILES_TO_ADD | LC_ALL=C sort)
STAGED=$(git diff --cached --name-only | LC_ALL=C sort)
[ "$EXPECTED" = "$STAGED" ] || { echo "commit_rec_r8m1a4audit2_B: staged set differs from the list" >&2; exit 2; }
[ -z "$(git diff --cached --name-only -- S4/ 2>&1)" ] || { echo "commit_rec_r8m1a4audit2_B: S4/ was staged" >&2; exit 2; }
[ -z "$(git diff --cached --name-only --diff-filter=MD -- testing/d003 2>&1)" ] || { echo "commit_rec_r8m1a4audit2_B: a tracked testing/d003 file is modified or deleted" >&2; exit 2; }

MSG="P05-S4 R8 M1a cont3a audit part2: stop record (no-injection checks; rerun gap pre-registered, not executed; K0 INFLUENCED, EVIDENCE_INSUFFICIENT; 44 INVALID rows and 119 G5-F2 rows open for ruling); awaiting user review"
git commit -q -m "$MSG" || { echo "commit_rec_r8m1a4audit2_B: commit failed" >&2; exit 2; }
echo "commit_rec_r8m1a4audit2_B: committed $(git rev-parse HEAD)"
echo "commit_rec_r8m1a4audit2_B: HEAD_PARENT=$(git rev-parse HEAD^)"
exit 0
