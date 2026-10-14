REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_m1a_r8m1a3c_B.sh -- P05-S4 R8 M1a CONT2c section 6: copy the B-segment small tables to registries/s4r8/M1a/.  New file.
# Inputs: the 13 *_M1a3c.* and *M1A3C* outputs of section 5 and the startB gate (checked to exist before the target is used).
# Targets must not exist (no overwrite).  Each copy is compared with cmp.  Writes SHA256SUMS_M1a3c_B.txt for these copies only;
# it does not touch SHA256SUMS.txt or SHA256SUMS_M1a3c_A.txt.
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/copy_m1a_r8m1a3c_B.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "copy_m1a_r8m1a3c_B: first argument must be p05-s4r8" >&2; exit 2; }
SRC=checkpoints/p05/evidence/p05-s4r8
DST=checkpoints/p05/registries/s4r8/M1a
OUT="$EV/COPY_M1A_R8_M1a3c_B.txt"
SUMS="$DST/SHA256SUMS_M1a3c_B.txt"
test ! -e "$OUT" || { echo "copy_m1a_r8m1a3c_B: REFUSED: exists (U17): $OUT" >&2; exit 2; }
test ! -e "$SUMS" || { echo "copy_m1a_r8m1a3c_B: REFUSED: exists (U17): $SUMS" >&2; exit 2; }
test -d "$DST" || { echo "copy_m1a_r8m1a3c_B: REFUSED: target directory missing" >&2; exit 2; }
NAMES="EXPECT_LINEMAP_R8_M1a3c.txt LINEMAP_F2_F3_R8_M1a3c.tsv PARSER_SELFCHECK_R8_M1a3c.tsv FUNC_BP_SYMBOLS_R8_M1a3c.tsv LINEMAP_CHECK_R8_M1a3c.txt LINEMAP_V3_V3C_DIFF_R8_M1a3c.txt MAP_V3_V3C_SRC_DIFF_R8_M1a3c.txt GATE_R8_M1a3c_STARTB.txt S4R7_RECHECK_GATE_R8_M1A3C_STARTB.tsv"
MISSING=0
for b in $NAMES; do
    f=""
    case "$b" in
        MAP_V3_V3C_SRC_DIFF_R8_M1a3c.txt) f="$EV/MAP_V3_V3C_SRC_DIFF_R8_M1a3c.txt" ;;
        *) f="$SRC/$b" ;;
    esac
    [ -f "$f" ] || { echo "MISSING_INPUT $f" >&2; MISSING=$((MISSING+1)); }
done
[ "$MISSING" = 0 ] || { echo "copy_m1a_r8m1a3c_B: REFUSED: $MISSING input(s) missing" >&2; exit 2; }
for b in $NAMES; do
    test ! -e "$DST/$b" || { echo "copy_m1a_r8m1a3c_B: REFUSED: target exists $b" >&2; exit 2; }
done
{
    printf 'utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'INPUTS_OK=%s\n' "$(echo $NAMES | wc -w | tr -d ' ')"
} > "$OUT"
COPIED=0
for b in $NAMES; do
    case "$b" in
        MAP_V3_V3C_SRC_DIFF_R8_M1a3c.txt) f="$EV/$b" ;;
        *) f="$SRC/$b" ;;
    esac
    cp "$f" "$DST/$b"
    if cmp -s "$f" "$DST/$b"; then COPIED=$((COPIED+1)); printf 'COPIED %s\n' "$b" >> "$OUT"
    else printf 'CMP_FAIL %s\n' "$b" >> "$OUT"; fi
done
printf 'COPIED=%s\n' "$COPIED" >> "$OUT"
(cd "$DST" && for x in $NAMES; do sha256sum "$x"; done) > "$SUMS"
echo "copy_m1a_r8m1a3c_B: COPIED=$COPIED -> $OUT"
exit 0
