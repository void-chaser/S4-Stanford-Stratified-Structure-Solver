#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_m1a4.sh -- copy small registry tables for CONT3a to checkpoints/p05/registries/s4r8/M1a/.  New file.
# Usage (through safe_run):
#   sh testing/d003/stage_s4r8/copy_m1a4.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "copy_m1a4: first arg must be p05-s4r8" >&2; exit 2; }

REG="$REPO/checkpoints/p05/registries/s4r8/M1a"
test -d "$REG" || { echo "copy_m1a4: registry dir missing: $REG" >&2; exit 2; }

FILES="
GATE_R8_M1a4_START.txt
S4R7_RECHECK_GATE_R8_M1A4_START.tsv
GATE_R8_M1a4_RESUME_R2.txt
S4R7_RECHECK_GATE_R8_M1A4_RESUME_R2.tsv
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

for f in $FILES; do
    src="$EV/$f"
    dst="$REG/$f"
    test -f "$src" || { echo "copy_m1a4: source missing: $src" >&2; exit 2; }
    if [ -e "$dst" ]; then
        echo "copy_m1a4: destination exists, checking cmp: $f"
        cmp -s "$src" "$dst" || { echo "copy_m1a4: destination exists and differs: $dst" >&2; exit 2; }
    else
        cp "$src" "$dst" || { echo "copy_m1a4: copy failed: $f" >&2; exit 2; }
        cmp -s "$src" "$dst" || { echo "copy_m1a4: cmp mismatch: $f" >&2; exit 2; }
        echo "copy_m1a4: copied $f"
    fi
done

# Write SHA256SUMS_M1a4.txt in registry
MAN="$REG/SHA256SUMS_M1a4.txt"
test ! -e "$MAN" || { echo "copy_m1a4: manifest already exists: $MAN" >&2; exit 2; }

(
    cd "$REG"
    for f in $FILES; do
        sha256sum "$f"
    done
) > "$MAN"

# Verify all lines in SHA256SUMS_M1a4.txt
(
    cd "$REG"
    sha256sum -c SHA256SUMS_M1a4.txt
) || { echo "copy_m1a4: sha256 check failed" >&2; exit 2; }

echo "copy_m1a4: all 21 files copied, cmp verified, and SHA256SUMS_M1a4.txt verified OK"
exit 0
