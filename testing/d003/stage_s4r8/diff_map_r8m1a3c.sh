REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# diff_map_r8m1a3c.sh -- P05-S4 R8 M1a CONT2c 5.2: source diff of map_f2_f3_r8m1a3.py (v3) against map_f2_f3_r8m1a3c.py (v3c).  New file.
# Writes $EV/MAP_V3_V3C_SRC_DIFF_R8_M1a3c.txt (refused if it exists).  git diff --no-index exits 1 when the files differ; that is expected.
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/diff_map_r8m1a3c.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "diff_map_r8m1a3c: first argument must be p05-s4r8" >&2; exit 2; }
V3=testing/d003/stage_s4r8/map_f2_f3_r8m1a3.py
V3C=testing/d003/stage_s4r8/map_f2_f3_r8m1a3c.py
OUT="$EV/MAP_V3_V3C_SRC_DIFF_R8_M1a3c.txt"
test ! -e "$OUT" || { echo "diff_map_r8m1a3c: REFUSED: exists (U17): $OUT" >&2; exit 2; }
test -f "$V3" || { echo "diff_map_r8m1a3c: REFUSED: v3 missing" >&2; exit 2; }
test -f "$V3C" || { echo "diff_map_r8m1a3c: REFUSED: v3c missing" >&2; exit 2; }
{
    printf '# git diff --no-index %s %s (P05-S4 R8 M1a CONT2c 5.2; record only; exit 1 = files differ)\n' "$V3" "$V3C"
    printf '# utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    git diff --no-index -- "$V3" "$V3C"
} > "$OUT"
echo "diff_map_r8m1a3c: written -> $OUT"
exit 0
