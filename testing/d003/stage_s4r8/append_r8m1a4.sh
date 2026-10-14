REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_r8m1a4.sh -- P05-S4 R8 M1a CONT3a: append U176-U182 to RULINGS.tsv and E8-56..E8-60 to ERRATA_8.txt.  New file.
# Pre-checks (exit 2, nothing written if any fails): RULINGS 66509 bytes sha256 77ca5867...; ERRATA_8 37669 bytes sha256 ff958d24...;
# both end with a newline; the data file has 7 lines, each with 5 TAB-separated fields, ids U176..U182 in order.
# Post-checks: the first 66509 bytes of RULINGS and the first 37669 bytes of ERRATA_8 keep their hashes; new RULINGS lines have NF=5.
# Writes $EV/APPEND_R8_M1a4.txt once (refused if it exists).  Run only after GATE_R8_M1a4_START.txt has FAILS=0.
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/append_r8m1a4.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "append_r8m1a4: first argument must be p05-s4r8" >&2; exit 2; }
RUL=checkpoints/p05/registries/RULINGS.tsv
ERR=checkpoints/p05/registries/s4r8/ERRATA_8.txt
DAT=testing/d003/stage_s4r8/append_rulings_r8m1a4.tsv
ETX=testing/d003/stage_s4r8/append_errata_r8m1a4.txt
OUT="$EV/APPEND_R8_M1a4.txt"
test ! -e "$OUT" || { echo "append_r8m1a4: REFUSED: exists (U17): $OUT" >&2; exit 2; }

# ---- (1) pre-checks ----
[ "$(wc -c < "$RUL" | tr -d ' ')" = 66509 ] || { echo "append_r8m1a4: PRE FAIL RULINGS bytes" >&2; exit 2; }
[ "$(sha256sum "$RUL" | cut -d' ' -f1)" = 77ca58673d471b8122b7c805cbd77c4aac65923c89c800241118132b426376d5 ] || { echo "append_r8m1a4: PRE FAIL RULINGS sha256" >&2; exit 2; }
[ "$(wc -c < "$ERR" | tr -d ' ')" = 37669 ] || { echo "append_r8m1a4: PRE FAIL ERRATA_8 bytes" >&2; exit 2; }
[ "$(sha256sum "$ERR" | cut -d' ' -f1)" = ff958d246e6fb967e2c8f524c9376d48d34833c861fd83651ebff581d6eab725 ] || { echo "append_r8m1a4: PRE FAIL ERRATA_8 sha256" >&2; exit 2; }
[ "$(tail -c 1 "$RUL" | od -An -c | tr -d ' ')" = '\n' ] || { echo "append_r8m1a4: PRE FAIL RULINGS no final newline" >&2; exit 2; }
[ "$(tail -c 1 "$ERR" | od -An -c | tr -d ' ')" = '\n' ] || { echo "append_r8m1a4: PRE FAIL ERRATA_8 no final newline" >&2; exit 2; }
[ "$(awk -F'\t' 'END{print NR}' "$DAT")" = 7 ] || { echo "append_r8m1a4: PRE FAIL data line count" >&2; exit 2; }
[ "$(awk -F'\t' 'NF!=5{n++} END{print n+0}' "$DAT")" = 0 ] || { echo "append_r8m1a4: PRE FAIL data NF" >&2; exit 2; }
[ "$(cut -f1 "$DAT" | tr '\n' ' ')" = "U176 U177 U178 U179 U180 U181 U182 " ] || { echo "append_r8m1a4: PRE FAIL data ids" >&2; exit 2; }
[ "$(tail -c 1 "$DAT" | od -An -c | tr -d ' ')" = '\n' ] || { echo "append_r8m1a4: PRE FAIL data no final newline" >&2; exit 2; }
[ "$(tail -c 1 "$ETX" | od -An -c | tr -d ' ')" = '\n' ] || { echo "append_r8m1a4: PRE FAIL errata text no final newline" >&2; exit 2; }
[ "$(grep -c '^E8-' "$ETX")" = 5 ] || { echo "append_r8m1a4: PRE FAIL errata entry count" >&2; exit 2; }

# ---- record the pre-state ----
{
    printf 'utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'PRE RULINGS_bytes=%s sha256=%s\n' "$(wc -c < "$RUL" | tr -d ' ')" "$(sha256sum "$RUL" | cut -d' ' -f1)"
    printf 'PRE ERRATA_8_bytes=%s sha256=%s\n' "$(wc -c < "$ERR" | tr -d ' ')" "$(sha256sum "$ERR" | cut -d' ' -f1)"
    printf 'PRE DATA_lines=%s sha256=%s\n' "$(wc -l < "$DAT" | tr -d ' ')" "$(sha256sum "$DAT" | cut -d' ' -f1)"
    printf 'PRE ERRATA_APPEND_sha256=%s\n' "$(sha256sum "$ETX" | cut -d' ' -f1)"
} > "$OUT"

# ---- (2) append ----
cat "$DAT" >> "$RUL" || { echo "append_r8m1a4: APPEND FAIL RULINGS" >&2; exit 2; }
cat "$ETX" >> "$ERR" || { echo "append_r8m1a4: APPEND FAIL ERRATA_8" >&2; exit 2; }

# ---- (3) post-checks ----
PRE_RUL_SHA=$(head -c 66509 "$RUL" | sha256sum | cut -d' ' -f1)
PRE_ERR_SHA=$(head -c 37669 "$ERR" | sha256sum | cut -d' ' -f1)
RUL_BYTES=$(wc -c < "$RUL" | tr -d ' ')
ERR_BYTES=$(wc -c < "$ERR" | tr -d ' ')
RUL_LINES=$(wc -l < "$RUL" | tr -d ' ')
NEW_NF_BAD=$(tail -n 7 "$RUL" | awk -F'\t' 'NF!=5{n++} END{print n+0}')
NEW_IDS=$(tail -n 7 "$RUL" | cut -f1 | tr '\n' ' ')
FAILS=0
[ "$PRE_RUL_SHA" = 77ca58673d471b8122b7c805cbd77c4aac65923c89c800241118132b426376d5 ] || { echo "POST FAIL RULINGS prefix" >&2; FAILS=$((FAILS+1)); }
[ "$PRE_ERR_SHA" = ff958d246e6fb967e2c8f524c9376d48d34833c861fd83651ebff581d6eab725 ] || { echo "POST FAIL ERRATA_8 prefix" >&2; FAILS=$((FAILS+1)); }
[ "$NEW_NF_BAD" = 0 ] || { echo "POST FAIL new RULINGS line NF" >&2; FAILS=$((FAILS+1)); }
[ "$NEW_IDS" = "U176 U177 U178 U179 U180 U181 U182 " ] || { echo "POST FAIL new RULINGS ids" >&2; FAILS=$((FAILS+1)); }
[ "$RUL_BYTES" = $((66509 + $(wc -c < "$DAT" | tr -d ' '))) ] || { echo "POST FAIL RULINGS total bytes" >&2; FAILS=$((FAILS+1)); }
[ "$ERR_BYTES" = $((37669 + $(wc -c < "$ETX" | tr -d ' '))) ] || { echo "POST FAIL ERRATA_8 total bytes" >&2; FAILS=$((FAILS+1)); }

# ---- (4) new sha256 and byte counts ----
{
    printf 'POST RULINGS_bytes=%s lines=%s sha256=%s\n' "$RUL_BYTES" "$RUL_LINES" "$(sha256sum "$RUL" | cut -d' ' -f1)"
    printf 'POST RULINGS_prefix_66509_sha256=%s\n' "$PRE_RUL_SHA"
    printf 'POST RULINGS_new_lines_NF_not5=%s\n' "$NEW_NF_BAD"
    printf 'POST RULINGS_new_ids=%s\n' "$NEW_IDS"
    printf 'POST ERRATA_8_bytes=%s sha256=%s\n' "$ERR_BYTES" "$(sha256sum "$ERR" | cut -d' ' -f1)"
    printf 'POST ERRATA_8_prefix_37669_sha256=%s\n' "$PRE_ERR_SHA"
    printf 'FAILS=%s\n' "$FAILS"
} >> "$OUT"
echo "append_r8m1a4: done FAILS=$FAILS -> $OUT"
[ "$FAILS" = 0 ] || exit 3
exit 0
