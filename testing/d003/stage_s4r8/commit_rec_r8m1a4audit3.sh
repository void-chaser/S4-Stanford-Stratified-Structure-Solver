#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a4audit3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_rec_r8m1a4audit3.sh -- P05-S4 R8 M1a CONT3a audit part 3: record commit.  New file.
# Usage (through safe_run):
#   sh testing/d003/safe_run.sh p05-s4r8/m1a4audit3 -- sh testing/d003/stage_s4r8/commit_rec_r8m1a4audit3.sh p05-s4r8
# Refuses unless the closing end gate GATE_R8_M1a4_AUDIT3_END.txt reports FAILS=0 and the index is empty.
# Adds each listed path one by one with "git add --" (never -A, never "."), verifies the staged set equals the list,
# and commits with a message ending in "awaiting user review".  The list includes this script itself.
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "commit_rec_r8m1a4audit3: first arg must be p05-s4r8" >&2; exit 2; }
ENDFILE="$REPO/checkpoints/p05/evidence/p05-s4r8/GATE_R8_M1a4_AUDIT3_END_R2.txt"
test -f "$ENDFILE" || { echo "commit_rec_r8m1a4audit3: closing end gate missing: $ENDFILE" >&2; exit 2; }
[ "$(tail -n 1 "$ENDFILE")" = "FAILS=0" ] || { echo "commit_rec_r8m1a4audit3: closing end gate is not FAILS=0" >&2; exit 2; }
[ -z "$(git diff --cached --name-only 2>&1)" ] || { echo "commit_rec_r8m1a4audit3: index already has staged files" >&2; exit 2; }

FILES_TO_ADD="
checkpoints/p05/STATE.md
checkpoints/p05/registries/RULINGS.tsv
checkpoints/p05/registries/s4r8/ERRATA_8.txt
checkpoints/p05/P05_S4R8_REPORT_M1a_CONT3a_AUDIT3.md
checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a_AUDIT3.md
checkpoints/p05/registries/s4r8/M1a/APPEND_ERRATA_E8_67_R8_M1a4AUDIT3.txt
checkpoints/p05/registries/s4r8/M1a/CONCLUSION44_R8_M1a4AUDIT3.tsv
checkpoints/p05/registries/s4r8/M1a/DIFF_AUDIT2_AUDIT3_R8_M1a4AUDIT3.tsv
checkpoints/p05/registries/s4r8/M1a/GAP_TABLE_R8_M1a4AUDIT3.tsv
checkpoints/p05/registries/s4r8/M1a/K_SOURCE_119_R8_M1a4AUDIT3.tsv
checkpoints/p05/registries/s4r8/M1a/K_SOURCE_G5F2_R8_M1a4AUDIT3.tsv
checkpoints/p05/registries/s4r8/M1a/REQUEST_TARGETS_R8_M1a4AUDIT3.tsv
checkpoints/p05/registries/s4r8/M1a/RERUN_WITHDRAWAL_R8_M1a4AUDIT3.txt
checkpoints/p05/registries/s4r8/M1a/SHA256SUMS_M1a4AUDIT3.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_INDEX_R8_M1a4AUDIT3.tsv
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT3_41fa0d6cf88f.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT3_4c882f730c79.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT3_79a3d3e7abd7.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT3_7cd9edfad8be.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT3_8b269be6e21f.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT3_a4061e4c429d.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT3_a9fccfa39dd2.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT3_afd4adb303ac.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT3_b049ed64ede8.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT3_bad127bfa8d2.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT3_be478d9063e5.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT3_c691acd71db3.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT3_cddc41c1cd00.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT3_d35bf64a11a0.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT3_e0739a05b26e.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT3_e6ee5b6af691.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT3_f4c3a33c4cda.txt
checkpoints/p05/registries/s4r8/M1a/SYMQ_R8_M1a4AUDIT3_f7d445cc2a48.txt
checkpoints/p05/registries/s4r8/M1a/TRACER_PAIRING_R8_M1a4AUDIT3.tsv
testing/d003/stage_s4r8/append_errata_r8m1a4audit3.py
testing/d003/stage_s4r8/append_rulings_r8m1a4audit3.py
testing/d003/stage_s4r8/classify_requests_r8m1a4audit3.py
testing/d003/stage_s4r8/copy_registries_r8m1a4audit3.sh
testing/d003/stage_s4r8/export_tables_r8m1a4audit3.py
testing/d003/stage_s4r8/gate11_r8m1a4audit3.sh
testing/d003/stage_s4r8/k_source_g5f2_r8m1a4audit3.py
testing/d003/stage_s4r8/manifest_r8m1a4audit3.sh
testing/d003/stage_s4r8/symq_r8m1a4audit3.sh
testing/d003/stage_s4r8/tracer_pairing_r8m1a4audit3.py
testing/d003/stage_s4r8/commit_rec_r8m1a4audit3.sh
"

for f in $FILES_TO_ADD; do
    test -f "$REPO/$f" || { echo "commit_rec_r8m1a4audit3: file to add missing: $f" >&2; exit 2; }
    git add -- "$REPO/$f" || { echo "commit_rec_r8m1a4audit3: git add failed: $f" >&2; exit 2; }
done

EXPECTED=$(printf '%s\n' $FILES_TO_ADD | LC_ALL=C sort)
STAGED=$(git diff --cached --name-only | LC_ALL=C sort)
[ "$EXPECTED" = "$STAGED" ] || { echo "commit_rec_r8m1a4audit3: staged set differs from the list" >&2; exit 2; }
[ -z "$(git diff --cached --name-only -- S4/ 2>&1)" ] || { echo "commit_rec_r8m1a4audit3: S4/ was staged" >&2; exit 2; }
[ -z "$(git diff --cached --name-only --diff-filter=MD -- testing/d003 2>&1)" ] || { echo "commit_rec_r8m1a4audit3: a tracked testing/d003 file is modified or deleted" >&2; exit 2; }

MSG="P05-S4 R8 M1a cont3a audit part3: U188-U191 applied (plan N by nth-call malloc count, 44 EXPECTED_NOT_REACHED; G5-F2 K from agreed history, 119 REACHED; tracer gap 0, rerun prereg WITHDRAWN, not executed; 18 drivers symbol-checked; K0 EVIDENCE_INSUFFICIENT to M1b); awaiting user review"
git commit -q -m "$MSG" || { echo "commit_rec_r8m1a4audit3: commit failed" >&2; exit 2; }
echo "commit_rec_r8m1a4audit3: committed $(git rev-parse HEAD)"
echo "commit_rec_r8m1a4audit3: HEAD_PARENT=$(git rev-parse HEAD^)"
exit 0
