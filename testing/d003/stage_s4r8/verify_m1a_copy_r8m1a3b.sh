REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# verify_m1a_copy_r8m1a3b.sh -- P05-S4 R8 M1a CONT2b section 6: check the copies in registries/s4r8/M1a/ (read only except the output file).  New file.
# (1) sha256sum -c of registries/s4r8/M1a/SHA256SUMS.txt (all lines must be OK);
# (2) cmp of every copy with its original in the evidence directory (the original is named in the list).
# Output: $EV/VERIFY_M1A_COPY_R8_M1a3b.txt (refused if it exists, U17).
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/verify_m1a_copy_r8m1a3b.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "verify_m1a_copy_r8m1a3b: first argument must be p05-s4r8" >&2; exit 2; }
SRC=checkpoints/p05/evidence/p05-s4r8
DST=checkpoints/p05/registries/s4r8/M1a
OUT="$EV/VERIFY_M1A_COPY_R8_M1a3b.txt"
test ! -e "$OUT" || { echo "verify_m1a_copy_r8m1a3b: REFUSED: exists (U17): $OUT" >&2; exit 2; }
BAD=0
N=0
OK=$(cd "$DST" && sha256sum -c SHA256SUMS.txt 2>&1 | grep -c ': OK$')
TOT=$(grep -c . "$DST/SHA256SUMS.txt")
{
    printf 'utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'SHA256SUMS_OK=%s of TOTAL=%s\n' "$OK" "$TOT"
} > "$OUT"
for f in "$DST"/*; do
    b=$(basename "$f")
    [ "$b" = SHA256SUMS.txt ] && continue
    N=$((N+1))
    if [ -f "$SRC/$b" ]; then
        if cmp -s "$f" "$SRC/$b"; then echo "CMP_OK $b" >> "$OUT"; else echo "CMP_DIFF $b" >> "$OUT"; BAD=$((BAD+1)); fi
    else
        echo "CMP_NO_ORIGIN_IN_EVIDENCE $b (copied from a subdirectory or renamed; see report)" >> "$OUT"
    fi
done
echo "COPIES=$N CMP_BAD=$BAD" >> "$OUT"
echo "verify_m1a_copy_r8m1a3b: OK=$OK TOTAL=$TOT COPIES=$N CMP_BAD=$BAD -> $OUT"
exit 0
