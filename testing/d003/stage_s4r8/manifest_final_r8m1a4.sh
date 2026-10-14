#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# manifest_final_r8m1a4.sh -- generate post-commit FINAL evidence manifest.  New file.
# Usage (through safe_run):
#   sh testing/d003/stage_s4r8/manifest_final_r8m1a4.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "manifest_final_r8m1a4: first arg must be p05-s4r8" >&2; exit 2; }

OUT="$EV/SHA256SUMS_M1a4_FINAL.txt"
test ! -e "$OUT" || { echo "manifest_final_r8m1a4: already exists: $OUT" >&2; exit 2; }

FILES="
FINAL_GIT_R8_M1a4.txt
GATE_R8_M1a4_START.txt
S4R7_RECHECK_GATE_R8_M1A4_START.tsv
GATE_R8_M1a4_RESUME_R2.txt
S4R7_RECHECK_GATE_R8_M1A4_RESUME_R2.tsv
GATE_R8_M1a4_END.txt
S4R7_RECHECK_GATE_R8_M1A4_END.tsv
APPEND_R8_M1a4.txt
APPEND_ERRATA_R8_M1a4_R3.txt
USED_IN_M1_CORRECTION_R8_M1a4.tsv
SOURCE_HASHES_R8_M1a4_R3.tsv
COUNTED_FAMILIES_R8_M1a4_R3.tsv
CALLSEQ_UNITS_R8_M1a4_R3.tsv
CALLSEQ_POINT_COVERAGE_R8_M1a4_R3.tsv
EXPECT_CALLSEQ_R8_M1a4_R3.txt
EXPECT_ADDITIONS_R8_M1a4.txt
CALLSEQ_RUNS_R8_M1a4_R3.tsv
CALLSEQ_F2_F3_R8_M1a4_R2.tsv
CALLSEQ_VALIDITY_R8_M1a4_R2.tsv
CALLSEQ_KMAX_R8_M1a4_R2.tsv
CALLSEQ_POINT_COVERAGE_CHECK_R8_M1a4_R2.tsv
RUNNER_DIFF_R8_M1a4.txt
CALLSEQ_ADDITIONS_R8_M1a4.tsv
ADDITIONS_MAPPING_22_R8_M1a4.tsv
"

(
    cd "$EV"
    for f in $FILES; do
        test -f "$f" || { echo "manifest_final_r8m1a4: missing evidence file: $f" >&2; exit 2; }
        sha256sum "$f"
    done
) > "$OUT"

(
    cd "$EV"
    sha256sum -c SHA256SUMS_M1a4_FINAL.txt
) || { echo "manifest_final_r8m1a4: verify failed" >&2; exit 2; }

echo "manifest_final_r8m1a4: SHA256SUMS_M1a4_FINAL.txt created and verified OK"
exit 0
