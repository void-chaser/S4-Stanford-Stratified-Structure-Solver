#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate3_diff_r8.sh -- diff -u of gate3_r8.sh against the committed gate2_r8.sh (U133; closing brief section 2).  New file.
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/gate3_diff_r8.sh p05-s4r8
# Output: $EV/GATE3_VS_GATE2_DIFF_R8.txt (new, refused if it exists).  diff exits 1 when the files differ (expected).
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "gate3_diff_r8: first argument must be p05-s4r8" >&2; exit 2; }
OUT="$EV/GATE3_VS_GATE2_DIFF_R8.txt"
test ! -e "$OUT" || { echo "gate3_diff_r8: REFUSED exists: $OUT" >&2; exit 2; }
test -f "$REPO/testing/d003/stage_s4r8/gate2_r8.sh" && test -f "$REPO/testing/d003/stage_s4r8/gate3_r8.sh" || { echo "gate3_diff_r8: REFUSED: input missing" >&2; exit 2; }
{
    printf '# GATE3_VS_GATE2_DIFF_R8.txt -- diff -u gate2_r8.sh gate3_r8.sh (closing brief section 2; U133).\n'
    diff -u "$REPO/testing/d003/stage_s4r8/gate2_r8.sh" "$REPO/testing/d003/stage_s4r8/gate3_r8.sh"
    true
} > "$OUT" 2>&1
echo "gate3_diff_r8: done -> $OUT"
exit 0
