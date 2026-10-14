REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_m1a_r8m1a3b.sh -- P05-S4 R8 M1a CONT2b section 6: copy the small tables to registries/s4r8/M1a/ and write SHA256SUMS.txt.  New file.
# Copy of copy_registries_r8m1a2 style; checks every input exists before the target directory is used (brief 0.2).
# Large files (over 1 MB) are not copied: their sha256 is recorded in the list and written to E8.
# F2_S4.cpp.txt is not copied: only its sha256 is recorded.
# Each copy is compared with cmp after copying.  The target directory must exist (created by the caller, after input check).
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/copy_m1a_r8m1a3b.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "copy_m1a_r8m1a3b: first argument must be p05-s4r8" >&2; exit 2; }
SRC=checkpoints/p05/evidence/p05-s4r8
DST=checkpoints/p05/registries/s4r8/M1a
LIST="$EV/tmp/copy_list_m1a_r8m1a3b.txt"
OUT="$EV/COPY_M1A_R8_M1a3b.txt"
test ! -e "$OUT" || { echo "copy_m1a_r8m1a3b: REFUSED: exists (U17): $OUT" >&2; exit 2; }
test -d "$DST" || { echo "copy_m1a_r8m1a3b: REFUSED: target directory missing" >&2; exit 2; }
{
    ls "$SRC"/GATE_R8_M1a*.txt
    ls "$SRC"/PRERUN_CHECKS_R8_M1a.txt "$SRC"/APPEND_R8_M1a3.txt "$SRC"/PRECHECK_START_R8_M1a3.txt
    ls "$SRC"/STRIP_EQUIV_*_R8_M1a.* "$SRC"/strip_cmp_r8m1/STRIP_EQUIV_*_R8_M1a.* 2>&1
    ls "$SRC"/NEEDS_R8_M1a.tsv "$SRC"/BUILD_OPTION_DIFF_R8_M1a.txt "$SRC"/DRIVERS_R8_M1a*.tsv "$SRC"/DRIVER_R6B_SEAM_R8_M1a.tsv
    ls "$SRC"/DRIVERS_S3R4_R8_M1a_F3.tsv "$SRC"/LINEMAP_F2_F3_R8_M1a.tsv "$SRC"/LINEMAP_F2_F3_R8_M1a2.tsv "$SRC"/EXPECT_LINEMAP_R8_M1a2.txt
    ls "$SRC"/RUNNER_DIFF_R8_M1a.txt "$SRC"/S4R7_RECHECK_R8_M1A*.tsv
    ls "$SRC"/EXPECT_LINEMAP_R8_M1a3.txt "$SRC"/PARSER_SELFCHECK_R8_M1a3.tsv "$SRC"/FUNC_BP_SYMBOLS_R8_M1a3.tsv
    ls "$SRC"/LINEMAP_F2_F3_R8_M1a3.tsv "$SRC"/LINEMAP_CHECK_R8_M1a3.txt "$SRC"/LINEMAP_V2_V3_DIFF_R8_M1a3.txt
    ls "$SRC"/APPEND_R8_M1a3b.txt "$SRC"/GATE_R8_M1a3b.txt "$SRC"/GATE_R8_M1a3b_END.txt
} > "$LIST" 2>"$EV/tmp/copy_ls_err_m1a_r8m1a3b.txt" || true
MISSING=0
while read -r f; do
    [ -n "$f" ] || continue
    if [ ! -f "$f" ]; then echo "MISSING_INPUT $f"; MISSING=$((MISSING+1)); fi
done < "$LIST"
{
    printf 'utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'MISSING_INPUTS=%s\n' "$MISSING"
} > "$OUT"
# copy (small text tables only; the sizes are checked against 1 MB)
COPIED=0
BIG=0
while read -r f; do
    [ -n "$f" ] && [ -f "$f" ] || continue
    sz=$(wc -c < "$f" | tr -d ' ')
    if [ "$sz" -gt 1048576 ]; then
        echo "BIG_SHA_ONLY $f $(sha256sum "$f" | cut -d' ' -f1) bytes=$sz" >> "$OUT"
        BIG=$((BIG+1))
        continue
    fi
    b=$(basename "$f")
    cp "$f" "$DST/$b"
    cmp -s "$f" "$DST/$b" && COPIED=$((COPIED+1)) || echo "CMP_FAIL $b" >> "$OUT"
done < "$LIST"
echo "COPIED=$COPIED BIG_SHA_ONLY=$BIG" >> "$OUT"
# manifest of the copies
(cd "$DST" && for x in *; do [ "$x" = SHA256SUMS.txt ] || sha256sum "$x"; done) > "$DST/SHA256SUMS.txt"
echo "copy_m1a_r8m1a3b: COPIED=$COPIED BIG=$BIG MISSING=$MISSING -> $OUT"
exit 0
