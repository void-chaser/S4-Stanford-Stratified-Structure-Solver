REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# check_sums_m1a3c_B.sh -- P05-S4 R8 M1a CONT2c section 6: run sha256sum -c on SHA256SUMS_M1a3c_B.txt and count the OK lines.  New file.
# Writes $EV/CHECK_SUMS_M1A3C_B.txt (refused if it exists).  Read only apart from that record.
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/check_sums_m1a3c_B.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "check_sums_m1a3c_B: first argument must be p05-s4r8" >&2; exit 2; }
DST=checkpoints/p05/registries/s4r8/M1a
OUT="$EV/CHECK_SUMS_M1A3C_B.txt"
test ! -e "$OUT" || { echo "check_sums_m1a3c_B: REFUSED: exists (U17): $OUT" >&2; exit 2; }
test -f "$DST/SHA256SUMS_M1a3c_B.txt" || { echo "check_sums_m1a3c_B: REFUSED: list missing" >&2; exit 2; }
(cd "$DST" && sha256sum -c SHA256SUMS_M1a3c_B.txt) > "$EV/tmp/check_sums_m1a3c_B_raw.txt" 2>&1
NLINES=$(grep -c . "$DST/SHA256SUMS_M1a3c_B.txt")
NOK=$(grep -c ': OK$' "$EV/tmp/check_sums_m1a3c_B_raw.txt")
{
    printf 'utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    cat "$EV/tmp/check_sums_m1a3c_B_raw.txt"
    printf 'LINES=%s OK=%s\n' "$NLINES" "$NOK"
} > "$OUT"
echo "check_sums_m1a3c_B: LINES=$NLINES OK=$NOK -> $OUT"
[ "$NLINES" = "$NOK" ] || exit 3
exit 0
