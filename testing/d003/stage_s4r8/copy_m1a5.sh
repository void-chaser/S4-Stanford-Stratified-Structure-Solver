#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_m1a5.sh -- copies this round's small tables to registries/s4r8/M1a/ and writes SHA256SUMS_M1a5.txt (brief 6.2).  New file.
# Copies: PREREG_COUNTS_R8_M1a5.tsv, PREREG_STOP_R8_M1a5.tsv, PREREG_INPUTS_R8_M1a5.tsv, K_SOURCE_PLANCALL58_R8_M1a5.tsv,
# GATE_R8_M1a5_START.txt, FINAL_GIT_R8_M1a4AUDIT3_POST.txt, FINAL_GIT_R8_M1a5.txt (if present), SURVEY_R8_M1a5.txt.
# The two formal pre-registrations and PREREG_RECORD are NOT copied: they were not written (stop items, report).
# Each copy is checked with cmp against its original.  No copy may exist already (U17).
set -u
DST="$REPO/checkpoints/p05/registries/s4r8/M1a"
SUMS="$DST/SHA256SUMS_M1a5.txt"
test ! -e "$SUMS" || { echo "copy_m1a5: SHA256SUMS_M1a5.txt exists (U17)" >&2; exit 2; }
for f in PREREG_COUNTS_R8_M1a5.tsv PREREG_STOP_R8_M1a5.tsv PREREG_INPUTS_R8_M1a5.tsv K_SOURCE_PLANCALL58_R8_M1a5.tsv \
         GATE_R8_M1a5_START.txt FINAL_GIT_R8_M1a4AUDIT3_POST.txt SURVEY_R8_M1a5.txt; do
    test -f "$EV/$f" || { echo "copy_m1a5: missing original $f" >&2; exit 2; }
    test ! -e "$DST/$f" || { echo "copy_m1a5: copy exists (U17) $f" >&2; exit 2; }
done
for f in PREREG_COUNTS_R8_M1a5.tsv PREREG_STOP_R8_M1a5.tsv PREREG_INPUTS_R8_M1a5.tsv K_SOURCE_PLANCALL58_R8_M1a5.tsv \
         GATE_R8_M1a5_START.txt FINAL_GIT_R8_M1a4AUDIT3_POST.txt SURVEY_R8_M1a5.txt; do
    cp "$EV/$f" "$DST/$f" || exit 2
    cmp "$EV/$f" "$DST/$f" || { echo "copy_m1a5: cmp failed $f" >&2; exit 2; }
done
cd "$DST" || exit 2
sha256sum PREREG_COUNTS_R8_M1a5.tsv PREREG_STOP_R8_M1a5.tsv PREREG_INPUTS_R8_M1a5.tsv K_SOURCE_PLANCALL58_R8_M1a5.tsv \
          GATE_R8_M1a5_START.txt FINAL_GIT_R8_M1a4AUDIT3_POST.txt SURVEY_R8_M1a5.txt > "$SUMS"
echo "copy_m1a5: copied and compared 7 files; wrote $SUMS"
exit 0
