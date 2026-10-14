#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# prerun_chk_r8m1a3_pre.sh -- read-only pre-check of the CONT2 start values (brief CONT2 section 3).
# Writes one new file $EV/PRECHECK_START_R8_M1a3.txt (refused if it exists, U17).  Reads only.
# Purpose: confirm the byte counts and sha256 values that gate6 start mode will compare, before gate6 is written.
set -u
OUT="$EV/PRECHECK_START_R8_M1a3.txt"
test ! -e "$OUT" || { echo "REFUSED: exists (U17): $OUT" >&2; exit 2; }
ERR=checkpoints/p05/registries/s4r8/ERRATA_8.txt
RUL=checkpoints/p05/registries/RULINGS.tsv
{
    printf 'utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'ERRATA_8_bytes=%s\n' "$(wc -c < "$ERR" | tr -d ' ')"
    printf 'ERRATA_8_sha256_whole=%s\n' "$(sha256sum "$ERR" | cut -d' ' -f1)"
    printf 'ERRATA_8_sha256_first13990=%s\n' "$(head -c 13990 "$ERR" | sha256sum | cut -d' ' -f1)"
    printf 'ERRATA_8_sha256_first20474=%s\n' "$(head -c 20474 "$ERR" | sha256sum | cut -d' ' -f1)"
    printf 'ERRATA_8_sha256_first23046=%s\n' "$(head -c 23046 "$ERR" | sha256sum | cut -d' ' -f1)"
    printf 'RULINGS_bytes=%s\n' "$(wc -c < "$RUL" | tr -d ' ')"
    printf 'RULINGS_sha256_whole=%s\n' "$(sha256sum "$RUL" | cut -d' ' -f1)"
    printf 'RULINGS_sha256_first55304=%s\n' "$(head -c 55304 "$RUL" | sha256sum | cut -d' ' -f1)"
    printf 'RULINGS_HEAD_bytes=%s\n' "$(git show HEAD:$RUL | wc -c | tr -d ' ')"
} > "$OUT"
echo "prerun_chk_r8m1a3_pre: wrote $OUT"
exit 0
