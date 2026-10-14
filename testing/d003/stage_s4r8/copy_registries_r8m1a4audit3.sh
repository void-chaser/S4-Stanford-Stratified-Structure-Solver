#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a4audit3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_registries_r8m1a4audit3.sh -- copy the small result tables of the audit3 round from the evidence directory to
# checkpoints/p05/registries/s4r8/M1a/ and verify each copy by sha256 (section 7 of AGENTS.md).  New file.
# Usage (through safe_run):
#   sh testing/d003/safe_run.sh p05-s4r8/m1a4audit3 -- sh testing/d003/stage_s4r8/copy_registries_r8m1a4audit3.sh
# Refuses if any destination already exists (U17).  Copies only the names listed below; the safe_run.log and tmp are never copied.
set -u
DST="$REPO/checkpoints/p05/registries/s4r8/M1a"
FILES="
APPEND_ERRATA_E8_67_R8_M1a4AUDIT3.txt
CONCLUSION44_R8_M1a4AUDIT3.tsv
DIFF_AUDIT2_AUDIT3_R8_M1a4AUDIT3.tsv
GAP_TABLE_R8_M1a4AUDIT3.tsv
K_SOURCE_119_R8_M1a4AUDIT3.tsv
K_SOURCE_G5F2_R8_M1a4AUDIT3.tsv
REQUEST_TARGETS_R8_M1a4AUDIT3.tsv
SYMQ_INDEX_R8_M1a4AUDIT3.tsv
TRACER_PAIRING_R8_M1a4AUDIT3.tsv
"
for f in $FILES; do
    test -f "$EV/$f" || { echo "copy3: source missing: $f" >&2; exit 2; }
    test ! -e "$DST/$f" || { echo "copy3: destination exists (U17): $f" >&2; exit 2; }
done
for f in $(ls "$EV" | grep '^SYMQ_R8_M1a4AUDIT3_.*\.txt$'); do
    test ! -e "$DST/$f" || { echo "copy3: destination exists (U17): $f" >&2; exit 2; }
done
for f in $FILES; do
    cp -- "$EV/$f" "$DST/$f" || { echo "copy3: copy failed: $f" >&2; exit 2; }
done
for f in $(ls "$EV" | grep '^SYMQ_R8_M1a4AUDIT3_.*\.txt$'); do
    cp -- "$EV/$f" "$DST/$f" || { echo "copy3: copy failed: $f" >&2; exit 2; }
done
# verify every copy by sha256 against the original
FAIL=0
for f in $FILES $(ls "$EV" | grep '^SYMQ_R8_M1a4AUDIT3_.*\.txt$'); do
    A=$(sha256sum "$EV/$f" | cut -d' ' -f1)
    B=$(sha256sum "$DST/$f" | cut -d' ' -f1)
    if [ "$A" = "$B" ]; then echo "COPY_OK $f $A"; else echo "COPY_DIFF $f"; FAIL=$((FAIL + 1)); fi
done
echo "copy3: fails=$FAIL"
exit 0
