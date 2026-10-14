REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_r8m1a3c_B.sh -- P05-S4 R8 M1a CONT2c section 6: append E8-53..E8-55 to ERRATA_8.txt.  New file.
# Pre-checks (exit 2, nothing written if any fails): the first 34208 bytes of ERRATA_8 keep sha256 60b592bb... (the bytes
# recorded at the start of the segment; the A-segment append of E8-47..E8-52 was after them and is kept); the text file ends with a newline.
# The current size of ERRATA_8 is not fixed (it grew by the A-segment append); it is recorded before and after.
# Post-checks: the first 34208 bytes keep their sha256; the size grows by exactly the size of the text file.
# Writes $EV/APPEND_R8_M1a3c_B.txt once (refused if it exists).
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/append_r8m1a3c_B.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "append_r8m1a3c_B: first argument must be p05-s4r8" >&2; exit 2; }
ERR=checkpoints/p05/registries/s4r8/ERRATA_8.txt
ETX=testing/d003/stage_s4r8/append_errata_r8m1a3c_B.txt
OUT="$EV/APPEND_R8_M1a3c_B.txt"
test ! -e "$OUT" || { echo "append_r8m1a3c_B: REFUSED: exists (U17): $OUT" >&2; exit 2; }
test -f "$ETX" || { echo "append_r8m1a3c_B: REFUSED: text missing" >&2; exit 2; }
# ---- (1) pre-checks: the A-segment state of ERRATA_8 (must be the file committed by b39135e) ----
PRE_HEAD_SHA=$(head -c 34208 "$ERR" | sha256sum | cut -d' ' -f1)
[ "$PRE_HEAD_SHA" = 60b592bb6b1530a4c8a02197f30a4fa257e7b73d90582d8972dc2363cdad91d5 ] || { echo "append_r8m1a3c_B: PRE FAIL ERRATA_8 prefix 34208" >&2; exit 2; }
[ "$(tail -c 1 "$ETX" | od -An -c | tr -d ' ')" = '\n' ] || { echo "append_r8m1a3c_B: PRE FAIL text no final newline" >&2; exit 2; }
PRE_SIZE=$(wc -c < "$ERR" | tr -d ' ')
{
    printf 'utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'PRE ERRATA_8_bytes=%s prefix34208_sha256=%s\n' "$PRE_SIZE" "$PRE_HEAD_SHA"
} > "$OUT"
# ---- (2) append ----
cat "$ETX" >> "$ERR" || { echo "append_r8m1a3c_B: APPEND FAIL" >&2; exit 2; }
# ---- (3) post-checks ----
POST_PREFIX=$(head -c 34208 "$ERR" | sha256sum | cut -d' ' -f1)
POST_SIZE=$(wc -c < "$ERR" | tr -d ' ')
FAILS=0
[ "$POST_PREFIX" = 60b592bb6b1530a4c8a02197f30a4fa257e7b73d90582d8972dc2363cdad91d5 ] || { echo "POST FAIL prefix" >&2; FAILS=$((FAILS+1)); }
[ "$POST_SIZE" = $((PRE_SIZE + $(wc -c < "$ETX" | tr -d ' '))) ] || { echo "POST FAIL size" >&2; FAILS=$((FAILS+1)); }
{
    printf 'POST ERRATA_8_bytes=%s prefix34208_sha256=%s\n' "$POST_SIZE" "$POST_PREFIX"
    printf 'POST ERRATA_8_sha256=%s\n' "$(sha256sum "$ERR" | cut -d' ' -f1)"
    printf 'FAILS=%s\n' "$FAILS"
} >> "$OUT"
echo "append_r8m1a3c_B: done FAILS=$FAILS -> $OUT"
[ "$FAILS" = 0 ] || exit 3
exit 0
