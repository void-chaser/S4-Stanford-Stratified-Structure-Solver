REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_r8m1a3b.sh -- P05-S4 R8 M1a CONT2b section 2 (U160-U167; E8-37..E8-46).  New file.
# Appends the data file to RULINGS.tsv and the errata text to ERRATA_8.txt, with byte-level checks before and after.
# Pre-checks (exit 2, nothing written if any fails): RULINGS 59783 bytes sha256 a314446b...; ERRATA_8 28653 bytes sha256 16024140...;
# the data file has 8 lines, each with 5 TAB-separated fields, ids U160..U167 in order.
# Post-checks: the first 59783 bytes of RULINGS and the first 28653 bytes of ERRATA_8 keep their hashes; new RULINGS lines have NF=5.
# Writes $EV/APPEND_R8_M1a3b.txt once (refused if it exists).
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/append_r8m1a3b.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "append_r8m1a3b: first argument must be p05-s4r8" >&2; exit 2; }
RUL=checkpoints/p05/registries/RULINGS.tsv
ERR=checkpoints/p05/registries/s4r8/ERRATA_8.txt
DAT=testing/d003/stage_s4r8/append_rulings_r8m1a3b.tsv
ETX=testing/d003/stage_s4r8/append_errata_r8m1a3b.txt
OUT="$EV/APPEND_R8_M1a3b.txt"
test ! -e "$OUT" || { echo "append_r8m1a3b: REFUSED: exists (U17): $OUT" >&2; exit 2; }

# ---- (1) pre-checks ----
[ "$(wc -c < "$RUL" | tr -d ' ')" = 59783 ] || { echo "append_r8m1a3b: PRE FAIL RULINGS bytes" >&2; exit 2; }
[ "$(sha256sum "$RUL" | cut -d' ' -f1)" = a314446b80e82dd47c09ff70c4b2f05b92c62f530367fe14ee6b1fc9a932e4f0 ] || { echo "append_r8m1a3b: PRE FAIL RULINGS sha256" >&2; exit 2; }
[ "$(wc -c < "$ERR" | tr -d ' ')" = 28653 ] || { echo "append_r8m1a3b: PRE FAIL ERRATA_8 bytes" >&2; exit 2; }
[ "$(sha256sum "$ERR" | cut -d' ' -f1)" = 16024140abb1bbecfd34fc35471d74b3a94d79e75c3d50f44a98b3b43e8532b0 ] || { echo "append_r8m1a3b: PRE FAIL ERRATA_8 sha256" >&2; exit 2; }
[ "$(awk -F'\t' 'END{print NR}' "$DAT")" = 8 ] || { echo "append_r8m1a3b: PRE FAIL data line count" >&2; exit 2; }
[ "$(awk -F'\t' 'NF!=5{n++} END{print n+0}' "$DAT")" = 0 ] || { echo "append_r8m1a3b: PRE FAIL data NF" >&2; exit 2; }
[ "$(cut -f1 "$DAT" | tr '\n' ' ')" = "U160 U161 U162 U163 U164 U165 U166 U167 " ] || { echo "append_r8m1a3b: PRE FAIL data ids" >&2; exit 2; }
[ "$(tail -c 1 "$DAT" | od -An -c | tr -d ' ')" = '\n' ] || { echo "append_r8m1a3b: PRE FAIL data no final newline" >&2; exit 2; }

# ---- record the pre-state ----
{
    printf 'utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'PRE RULINGS_bytes=%s sha256=%s\n' "$(wc -c < "$RUL" | tr -d ' ')" "$(sha256sum "$RUL" | cut -d' ' -f1)"
    printf 'PRE ERRATA_8_bytes=%s sha256=%s\n' "$(wc -c < "$ERR" | tr -d ' ')" "$(sha256sum "$ERR" | cut -d' ' -f1)"
    printf 'PRE DATA_lines=%s sha256=%s\n' "$(wc -l < "$DAT" | tr -d ' ')" "$(sha256sum "$DAT" | cut -d' ' -f1)"
    printf 'PRE ERRATA_APPEND_sha256=%s\n' "$(sha256sum "$ETX" | cut -d' ' -f1)"
} > "$OUT"

# ---- (2) append ----
cat "$DAT" >> "$RUL" || { echo "append_r8m1a3b: APPEND FAIL RULINGS" >&2; exit 2; }
cat "$ETX" >> "$ERR" || { echo "append_r8m1a3b: APPEND FAIL ERRATA_8" >&2; exit 2; }

# ---- (3) post-checks ----
PRE_RUL_SHA=$(head -c 59783 "$RUL" | sha256sum | cut -d' ' -f1)
PRE_ERR_SHA=$(head -c 28653 "$ERR" | sha256sum | cut -d' ' -f1)
RUL_BYTES=$(wc -c < "$RUL" | tr -d ' ')
ERR_BYTES=$(wc -c < "$ERR" | tr -d ' ')
RUL_LINES=$(wc -l < "$RUL" | tr -d ' ')
NEW_NF_BAD=$(tail -n 8 "$RUL" | awk -F'\t' 'NF!=5{n++} END{print n+0}')
FAILS=0
[ "$PRE_RUL_SHA" = a314446b80e82dd47c09ff70c4b2f05b92c62f530367fe14ee6b1fc9a932e4f0 ] || { echo "POST FAIL RULINGS prefix" >&2; FAILS=$((FAILS+1)); }
[ "$PRE_ERR_SHA" = 16024140abb1bbecfd34fc35471d74b3a94d79e75c3d50f44a98b3b43e8532b0 ] || { echo "POST FAIL ERRATA_8 prefix" >&2; FAILS=$((FAILS+1)); }
[ "$NEW_NF_BAD" = 0 ] || { echo "POST FAIL new RULINGS line NF" >&2; FAILS=$((FAILS+1)); }
[ "$RUL_BYTES" = $((59783 + $(wc -c < "$DAT" | tr -d ' '))) ] || { echo "POST FAIL RULINGS total bytes" >&2; FAILS=$((FAILS+1)); }
[ "$ERR_BYTES" = $((28653 + $(wc -c < "$ETX" | tr -d ' '))) ] || { echo "POST FAIL ERRATA_8 total bytes" >&2; FAILS=$((FAILS+1)); }

# ---- (4) new sha256 and byte counts ----
{
    printf 'POST RULINGS_bytes=%s lines=%s sha256=%s\n' "$RUL_BYTES" "$RUL_LINES" "$(sha256sum "$RUL" | cut -d' ' -f1)"
    printf 'POST RULINGS_prefix_59783_sha256=%s\n' "$PRE_RUL_SHA"
    printf 'POST RULINGS_new_lines_NF_not5=%s\n' "$NEW_NF_BAD"
    printf 'POST ERRATA_8_bytes=%s sha256=%s\n' "$ERR_BYTES" "$(sha256sum "$ERR" | cut -d' ' -f1)"
    printf 'POST ERRATA_8_prefix_28653_sha256=%s\n' "$PRE_ERR_SHA"
    printf 'FAILS=%s\n' "$FAILS"
} >> "$OUT"
echo "append_r8m1a3b: done FAILS=$FAILS -> $OUT"
[ "$FAILS" = 0 ] || exit 3
exit 0
