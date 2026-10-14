#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_errata_r8m1a4_r3.sh -- append E8-61 and E8-62 to ERRATA_8.txt.  New file.
# Pre-checks: ERRATA_8 is 40135 bytes; ends with newline; first 37669 bytes sha256 ff958d24...;
# Append text has exactly 2 entries (E8-61 and E8-62) and ends with newline.
# Post-checks: first 40135 bytes unchanged; new bytes = 40135 + data bytes.
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "append_errata_r8m1a4_r3: first argument must be p05-s4r8" >&2; exit 2; }
ERR=checkpoints/p05/registries/s4r8/ERRATA_8.txt
ETX=testing/d003/stage_s4r8/append_errata_r8m1a4_r3.txt
OUT="$EV/APPEND_ERRATA_R8_M1a4_R3.txt"
test ! -e "$OUT" || { echo "append_errata_r8m1a4_r3: REFUSED: exists: $OUT" >&2; exit 2; }

# pre-checks
[ "$(wc -c < "$ERR" | tr -d ' ')" = 40135 ] || { echo "PRE FAIL ERR bytes" >&2; exit 2; }
[ "$(head -c 37669 "$ERR" | sha256sum | cut -d' ' -f1)" = ff958d246e6fb967e2c8f524c9376d48d34833c861fd83651ebff581d6eab725 ] || { echo "PRE FAIL ERR 37669 sha" >&2; exit 2; }
PRE_ERR_SHA=$(sha256sum "$ERR" | cut -d' ' -f1)
[ "$(tail -c 1 "$ERR" | od -An -c | tr -d ' ')" = '\n' ] || { echo "PRE FAIL ERR no newline" >&2; exit 2; }
[ "$(tail -c 1 "$ETX" | od -An -c | tr -d ' ')" = '\n' ] || { echo "PRE FAIL ETX no newline" >&2; exit 2; }
[ "$(grep -c '^E8-' "$ETX")" = 2 ] || { echo "PRE FAIL ETX entry count" >&2; exit 2; }

{
    printf 'utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'PRE ERRATA_8_bytes=40135 sha256=%s\n' "$PRE_ERR_SHA"
    printf 'PRE ETX_bytes=%s sha256=%s\n' "$(wc -c < "$ETX" | tr -d ' ')" "$(sha256sum "$ETX" | cut -d' ' -f1)"
} > "$OUT"

cat "$ETX" >> "$ERR" || { echo "APPEND FAIL" >&2; exit 2; }

POST_BYTES=$(wc -c < "$ERR" | tr -d ' ')
POST_PREFIX_SHA=$(head -c 40135 "$ERR" | sha256sum | cut -d' ' -f1)
FAILS=0
[ "$POST_PREFIX_SHA" = "$PRE_ERR_SHA" ] || { echo "POST FAIL prefix sha" >&2; FAILS=$((FAILS+1)); }
[ "$POST_BYTES" = $((40135 + $(wc -c < "$ETX" | tr -d ' '))) ] || { echo "POST FAIL total bytes" >&2; FAILS=$((FAILS+1)); }

{
    printf 'POST ERRATA_8_bytes=%s sha256=%s\n' "$POST_BYTES" "$(sha256sum "$ERR" | cut -d' ' -f1)"
    printf 'POST ERRATA_8_prefix_40135_sha256=%s\n' "$POST_PREFIX_SHA"
    printf 'FAILS=%s\n' "$FAILS"
} >> "$OUT"

echo "append_errata_r8m1a4_r3: done FAILS=$FAILS -> $OUT"
[ "$FAILS" = 0 ] || exit 3
exit 0
