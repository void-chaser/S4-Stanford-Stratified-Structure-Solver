#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a6; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# record_prereg_r8m1a6.sh -- record sha256 and UTC for formal preregistrations immediately upon generation.
set -u
refuse() { echo "record_prereg_r8m1a6: REFUSED: $1" >&2; exit 2; }

M1B="$EV/REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv"
M1C="$EV/REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv"
REC="$EV/PREREG_RECORD_R8_M1a6.txt"

test -f "$M1B" || refuse "M1b missing: $M1B"
test -f "$M1C" || refuse "M1c missing: $M1C"
test ! -e "$REC" || refuse "record exists (U17): $REC"

M1B_SHA=$(sha256sum "$M1B" | cut -d' ' -f1)
M1C_SHA=$(sha256sum "$M1C" | cut -d' ' -f1)
UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)

: > "$REC"
printf '# PREREG_RECORD_R8_M1a6.txt -- frozen preregistration record\n' >> "$REC"
printf 'record_utc\t%s\n' "$UTC" >> "$REC"
printf 'registry_m1b\t%s\tsha256=%s\tbytes=%s\n' "REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv" "$M1B_SHA" "$(wc -c < "$M1B" | tr -d ' ')" >> "$REC"
printf 'registry_m1c\t%s\tsha256=%s\tbytes=%s\n' "REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv" "$M1C_SHA" "$(wc -c < "$M1C" | tr -d ' ')" >> "$REC"

echo "record_prereg_r8m1a6: SUCCESS -> $REC"
exit 0
