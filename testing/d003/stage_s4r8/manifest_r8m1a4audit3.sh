#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a4audit3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# manifest_r8m1a4audit3.sh -- write the two SHA256SUMS manifests of the audit3 round (section 7 of AGENTS.md).  New file.
#   (1) registries:  checkpoints/p05/registries/s4r8/M1a/SHA256SUMS_M1a4AUDIT3.txt  (the copied audit3 tables and the withdrawal
#                    record; NO live file: RULINGS.tsv, ERRATA_8.txt and STATE.md are append-only and are checked by prefix in the gate)
#   (2) evidence:    $EV/SHA256SUMS.txt  (every non-binary evidence file of the round, excluding tmp, safe_run.log and this manifest)
# Each manifest is verified with sha256sum -c; the verification output is written to $EV/MANIFEST_CHECK_R8_M1a4AUDIT3.txt.
# Usage (through safe_run):
#   sh testing/d003/safe_run.sh p05-s4r8/m1a4audit3 -- sh testing/d003/stage_s4r8/manifest_r8m1a4audit3.sh
# Refuses if either manifest already exists (U17).
set -u
REG="$REPO/checkpoints/p05/registries/s4r8/M1a"
MREG="$REG/SHA256SUMS_M1a4AUDIT3.txt"
MEV="$EV/SHA256SUMS.txt"
test ! -e "$MREG" || { echo "manifest3: exists (U17): $MREG" >&2; exit 2; }
test ! -e "$MEV" || { echo "manifest3: exists (U17): $MEV" >&2; exit 2; }
CHK="$EV/MANIFEST_CHECK_R8_M1a4AUDIT3.txt"
test ! -e "$CHK" || { echo "manifest3: exists (U17): $CHK" >&2; exit 2; }

# (1) registries manifest: the names copied by copy_registries_r8m1a4audit3.sh plus the withdrawal record
{
    for f in $(ls "$REG" | grep -E '^(APPEND_ERRATA_E8_67_R8_M1a4AUDIT3|CONCLUSION44_R8_M1a4AUDIT3|DIFF_AUDIT2_AUDIT3_R8_M1a4AUDIT3|GAP_TABLE_R8_M1a4AUDIT3|K_SOURCE_119_R8_M1a4AUDIT3|K_SOURCE_G5F2_R8_M1a4AUDIT3|REQUEST_TARGETS_R8_M1a4AUDIT3|SYMQ_INDEX_R8_M1a4AUDIT3|TRACER_PAIRING_R8_M1a4AUDIT3)\.(txt|tsv)$|^SYMQ_R8_M1a4AUDIT3_.*\.txt$|^RERUN_WITHDRAWAL_R8_M1a4AUDIT3\.txt$' | LC_ALL=C sort); do
        echo "$(sha256sum "$REG/$f" | cut -d' ' -f1)  $f"
    done
} > "$MREG"
# (2) evidence manifest: every regular file of the round evidence except tmp, safe_run.log and the manifests
(
    cd "$EV" || exit 2
    for f in $(ls -p | grep -v '/$' | grep -v -E '^(safe_run\.log|SHA256SUMS\.txt|MANIFEST_CHECK_R8_M1a4AUDIT3\.txt)$' | LC_ALL=C sort); do
        echo "$(sha256sum "$f" | cut -d' ' -f1)  $f"
    done
) > "$MEV"
{
    echo "# manifest check (sha256sum -c) of the two manifests of round r8m1a4audit3"
    echo "# registries manifest entries: $(grep -c . "$MREG")"
    (cd "$REG" && sha256sum -c "$MREG" 2>&1) | sed 's/^/REG /'
    echo "# evidence manifest entries: $(grep -c . "$MEV")"
    (cd "$EV" && sha256sum -c "$MEV" 2>&1) | sed 's/^/EVI /'
} > "$CHK"
echo "manifest3: REG_LINES=$(grep -c . "$MREG") EVI_LINES=$(grep -c . "$MEV") REG_OK=$(grep -c ': OK$' "$CHK" | head -1)"
exit 0
