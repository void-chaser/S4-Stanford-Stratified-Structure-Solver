REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_m1a_r8m1a3c_A.sh -- P05-S4 R8 M1a CONT2c A3: fill the gaps of the earlier copy (U173) and copy this round's A-segment files.  New file.
# Copies: strip_cmp_r8m1/STRIP_EQUIV_R8_M1a.tsv (the main table missing since E8-49), GATE_R8_M1a3c_START.txt (and _R2 if present),
# S4R7_RECHECK_GATE_R8_M1A3C_START.tsv, APPEND_R8_M1a3c.txt.  De-duplicated; an existing target is refused (no overwrite).
# Every input is checked to exist before the copy starts; each copy is compared with cmp.  Existing SHA256SUMS.txt is not touched.
# This script does not write SHA256SUMS_M1a3c_A.txt; that list is written by commit_rec_r8m1a3c_A.sh, which covers all files of the A segment.
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/copy_m1a_r8m1a3c_A.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "copy_m1a_r8m1a3c_A: first argument must be p05-s4r8" >&2; exit 2; }
SRC=checkpoints/p05/evidence/p05-s4r8
DST=checkpoints/p05/registries/s4r8/M1a
OUT="$EV/COPY_M1A_R8_M1a3c_A.txt"
test ! -e "$OUT" || { echo "copy_m1a_r8m1a3c_A: REFUSED: exists (U17): $OUT" >&2; exit 2; }
# ---- (1) inputs: every name must exist before the target directory is used ----
MISSING=0
for f in "$SRC/strip_cmp_r8m1/STRIP_EQUIV_R8_M1a.tsv" "$SRC/GATE_R8_M1a3c_START.txt" "$SRC/S4R7_RECHECK_GATE_R8_M1A3C_START.tsv" "$SRC/APPEND_R8_M1a3c.txt"; do
    [ -f "$f" ] || { echo "MISSING_INPUT $f" >&2; MISSING=$((MISSING+1)); }
done
[ "$MISSING" = 0 ] || { echo "copy_m1a_r8m1a3c_A: REFUSED: $MISSING input(s) missing" >&2; exit 2; }
test -d "$DST" || { echo "copy_m1a_r8m1a3c_A: REFUSED: target directory missing" >&2; exit 2; }
# _R2 copy only if the file exists (not in this round: no _R2 was needed)
if [ -f "$SRC/GATE_R8_M1a3c_START_R2.txt" ]; then EXTRA="$SRC/GATE_R8_M1a3c_START_R2.txt"; else EXTRA=""; fi
# ---- (2) targets must not exist ----
for b in STRIP_EQUIV_R8_M1a.tsv GATE_R8_M1a3c_START.txt S4R7_RECHECK_GATE_R8_M1A3C_START.tsv APPEND_R8_M1a3c.txt; do
    test ! -e "$DST/$b" || { echo "copy_m1a_r8m1a3c_A: REFUSED: target exists $b" >&2; exit 2; }
done
{
    printf 'utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'INPUTS_OK=4 EXTRA=%s\n' "${EXTRA:-none}"
} > "$OUT"
# ---- (3) copy and cmp ----
COPIED=0
for f in "$SRC/strip_cmp_r8m1/STRIP_EQUIV_R8_M1a.tsv" "$SRC/GATE_R8_M1a3c_START.txt" "$SRC/S4R7_RECHECK_GATE_R8_M1A3C_START.tsv" "$SRC/APPEND_R8_M1a3c.txt" $EXTRA; do
    b=$(basename "$f")
    cp "$f" "$DST/$b"
    if cmp -s "$f" "$DST/$b"; then COPIED=$((COPIED+1)); printf 'COPIED %s sha256=%s\n' "$b" "$(sha256sum "$DST/$b" | cut -d' ' -f1)" >> "$OUT"
    else printf 'CMP_FAIL %s\n' "$b" >> "$OUT"; fi
done
printf 'COPIED=%s\n' "$COPIED" >> "$OUT"
echo "copy_m1a_r8m1a3c_A: COPIED=$COPIED -> $OUT"
exit 0
