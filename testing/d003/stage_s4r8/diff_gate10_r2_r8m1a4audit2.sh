#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a4audit2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# diff_gate10_r2_r8m1a4audit2.sh -- show the difference between the committed gate10 and gate10_r2 (read only; the diff is
# written into the round evidence directory).  New file.  Usage (through safe_run):
#   sh testing/d003/safe_run.sh p05-s4r8/m1a4audit2 -- sh testing/d003/stage_s4r8/diff_gate10_r2_r8m1a4audit2.sh DIFF_GATE10_R2.txt
set -u
OUTNAME=${1:?"out name"}
case "$OUTNAME" in
    DIFF_GATE10_R2_*.txt) ;;
    *) echo "diff_gate10: OUT must be DIFF_GATE10_R2_<name>.txt" >&2; exit 2 ;;
esac
test ! -e "$EV/$OUTNAME" || { echo "diff_gate10: exists (U17): $OUTNAME" >&2; exit 2; }
diff "$REPO/testing/d003/stage_s4r8/gate10_r8m1a4audit2.sh" "$REPO/testing/d003/stage_s4r8/gate10_r8m1a4audit2_r2.sh" > "$EV/$OUTNAME"
echo "diff_gate10: diff exit=$? written to $EV/$OUTNAME"
exit 0
