REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# export_r8m2a2.sh -- P05-S4 R8 M2a2 section 4.1: export the F3 and B trees with git archive (read-only in the repo).
# New file (copied from export_r8m2a.sh; original unchanged).
# Output: $EV/tree_F3/S4 (from 8d8202a) and $EV/tree_B/S4 (from 37a82e8); each tree's S4 hash is checked against its pin.
# Output list: $EV/EXPORT_R8_M2a2.txt.  Refuses to overwrite (U17).
set -u
refuse() { echo "export_r8m2a2: REFUSED: $1" >&2; exit 2; }
[ "${1:-}" = p05-s4r8/m2a2 ] || refuse "first argument must be p05-s4r8/m2a2"
OUTF="$EV/EXPORT_R8_M2a2.txt"
test ! -e "$OUTF" || refuse "exists (U17): $OUTF"
test ! -e "$EV/tree_F3" || refuse "exists (U17): tree_F3"
test ! -e "$EV/tree_B" || refuse "exists (U17): tree_B"
mkdir -p "$EV/tree_F3" "$EV/tree_B" || refuse "cannot create tree dirs"
git archive 8d8202a S4 | tar -x -C "$EV/tree_F3" || refuse "F3 archive failed"
git archive 37a82e8 S4 | tar -x -C "$EV/tree_B" || refuse "B archive failed"
F3H=$(git rev-parse 8d8202a:S4)
BH=$(git rev-parse 37a82e8:S4)
{
    echo "# EXPORT_R8_M2a2 -- git archive exports (P05-S4 R8 M2a2 section 4.1)"
    echo "tree_F3	8d8202a	S4	$F3H	expected=6cff923a02baf19e01966b2339755cbf3a5deeef	$( [ "$F3H" = 6cff923a02baf19e01966b2339755cbf3a5deeef ] && echo MATCH || echo MISMATCH )"
    echo "tree_B	37a82e8	S4	$BH	expected=1d738e64f9864a475fdb3de34cd3601605df2c64	$( [ "$BH" = 1d738e64f9864a475fdb3de34cd3601605df2c64 ] && echo MATCH || echo MISMATCH )"
} > "$OUTF"
echo "export_r8m2a2: wrote $OUTF"
exit 0
