REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# sums_m1a_r8m1a3b.sh -- P05-S4 R8 M1a CONT2b section 6: SHA256SUMS_M1a.txt over the non-binary evidence of M1a, CONT1, CONT2 and CONT2b.  New file.
# Covers the evidence files of this round and earlier rounds that are text (tsv, txt, log).  Binary files (build, drivers, trees) are not listed.
# Output: $EV/SHA256SUMS_M1a.txt (refused if it exists, U17).
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/sums_m1a_r8m1a3b.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "sums_m1a_r8m1a3b: first argument must be p05-s4r8" >&2; exit 2; }
OUT="$EV/SHA256SUMS_M1a.txt"
test ! -e "$OUT" || { echo "sums_m1a_r8m1a3b: REFUSED: exists (U17): $OUT" >&2; exit 2; }
cd "$EV" || exit 2
{
    printf '# SHA256SUMS_M1a.txt -- P05-S4 R8 M1a, CONT1, CONT2, CONT2b: non-binary evidence (tsv, txt, log, sh, py, gdb).  Written by sums_m1a_r8m1a3b.sh.\n'
    printf '# Paths are relative to %s.  Binary files (build, drivers, trees) are not listed.\n' "$EV"
    for f in *.tsv *.txt *.log; do
        [ -f "$f" ] || continue
        sha256sum "$f"
    done
} > "$OUT"
echo "sums_m1a_r8m1a3b: lines=$(grep -c '^[0-9a-f]\{64\}  ' "$OUT") -> $OUT"
exit 0
