#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# export_r8.sh -- P05-S4 R8 M0 step 3.1: export of the F3 tree (8d8202a) by git archive; new file.
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/export_r8.sh p05-s4r8
# Inputs are checked first (commit 8d8202a exists, its S4 tree is 6cff923a...), then the target is created.
# The target $EV/trees/F3 must not exist (U17).  Outputs: $EV/trees/F3 (source tree, not committed),
# $EV/TREE_MANIFEST_R8.tsv (tree, path, sha256 per file), $EV/TREE_CHECK_R8.txt (blob check against git ls-tree).
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "export_r8: first argument must be p05-s4r8" >&2; exit 2; }
F3=8d8202a
F3_TREE=6cff923a02baf19e01966b2339755cbf3a5deeef
GOT_TREE=$(git rev-parse "$F3:S4" 2>&1)
if [ "$GOT_TREE" != "$F3_TREE" ]; then echo "export_r8: REFUSED: $F3:S4 is $GOT_TREE" >&2; exit 2; fi
test ! -e "$EV/trees/F3" || { echo "export_r8: REFUSED exists: $EV/trees/F3" >&2; exit 2; }
test ! -e "$EV/TREE_MANIFEST_R8.tsv" || { echo "export_r8: REFUSED exists: TREE_MANIFEST_R8.tsv" >&2; exit 2; }
test ! -e "$EV/TREE_CHECK_R8.txt" || { echo "export_r8: REFUSED exists: TREE_CHECK_R8.txt" >&2; exit 2; }
mkdir -p "$EV/trees/F3" || exit 2
git archive "$F3" | tar -x -C "$EV/trees/F3" || { echo "export_r8: git archive or tar failed" >&2; exit 2; }
cd "$EV/trees/F3" && find S4 -type f | LC_ALL=C sort | while read -r f; do
    printf 'F3\t%s\t%s\n' "$f" "$(sha256sum "$f" | cut -d' ' -f1)"
done > "$EV/TREE_MANIFEST_R8.tsv" 2>&1
cd "$REPO" || exit 2
# blob check: every S4 file of the export equals the blob of git ls-tree -r 8d8202a S4
LSTREE="$EV/tmp/lstree_F3_r8.txt"
git ls-tree -r "$F3" S4 | LC_ALL=C sort > "$LSTREE" 2>&1
N_FILES=$(wc -l < "$EV/TREE_MANIFEST_R8.tsv")
N_LSTREE=$(wc -l < "$LSTREE")
{
    echo "TREE_CHECK_R8 (export F3 = $F3, S4 tree $GOT_TREE)"
    echo "files in export (S4/): $N_FILES"
    echo "entries in git ls-tree -r $F3 S4: $N_LSTREE"
    MISS=0
    while read -r mode type blob path; do
        ex=$(git rev-parse "$F3:$path" 2>&1)
        got=$(git hash-object "$EV/trees/F3/$path" 2>&1)
        if [ "$ex" != "$blob" ] || [ "$got" != "$blob" ]; then MISS=$((MISS + 1)); echo "MISMATCH $path blob=$blob export=$got"; fi
    done < "$LSTREE"
    echo "blob mismatches: $MISS"
} > "$EV/TREE_CHECK_R8.txt" 2>&1
tail -n 1 "$EV/TREE_CHECK_R8.txt"
echo "export_r8: done -> $EV/trees/F3 files=$N_FILES"
exit 0
