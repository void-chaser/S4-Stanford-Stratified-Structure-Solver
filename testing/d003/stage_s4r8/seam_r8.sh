#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# seam_r8.sh -- P05-S4 R8 M0 step 3.3: F3 seam trees (plain only), patch order as R7 (new file; from p05-s4r7/safe_run.log 10-15).
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/seam_r8.sh p05-s4r8
# seamF-F3   : git archive 8d8202a -> apply_seam_r2.py --families A,C,D -> apply_seam_b2.py   (B2 is NOT omitted, ES3R4-26(b))
# fmmret-F3  : git archive 8d8202a -> apply_seam_r5_fmmret.py --tree A
# Each apply writes its report to $EV/seam_r8/apply-<VARIANT>-*.txt and its stdout/stderr to $EV/seam_r8/<VARIANT>-*.log.
# A tree directory that already exists is refused (U17).  No file in S4/ of the repository is touched: the applies
# refuse --repo S4 paths and every edit goes to the export copy.
# Then the comparison with R7 (brief 3.3) is written by a separate script (compare_seam_r8.sh).
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "seam_r8: first argument must be p05-s4r8" >&2; exit 2; }
F3=8d8202a
F3_TREE=6cff923a02baf19e01966b2339755cbf3a5deeef
GOT_TREE=$(git rev-parse "$F3:S4" 2>&1)
if [ "$GOT_TREE" != "$F3_TREE" ]; then echo "seam_r8: REFUSED: $F3:S4 is $GOT_TREE" >&2; exit 2; fi
for f in testing/d003/seam/apply_seam_r2.py testing/d003/seam/apply_seam_b2.py testing/d003/seam/apply_seam_r5_fmmret.py; do
    test -f "$REPO/$f" || { echo "seam_r8: REFUSED: input missing: $f" >&2; exit 2; }
done
OUT="$EV/seam_r8"
test ! -e "$OUT" || { echo "seam_r8: REFUSED exists: $OUT" >&2; exit 2; }
mkdir -p "$OUT" || exit 2
SAFE="$REPO/testing/d003/safe_run.sh"
PY="$REPO/testing/d003/seam"

# step 1: exports (each target must be new)
sh "$SAFE" p05-s4r8 -- sh -c 'test ! -e "$1" && mkdir -p "$1" && git -C "$2" archive "$3" | tar -x -C "$1"' sh "$OUT/F3-seamF" "$REPO" "$F3" || exit 2
sh "$SAFE" p05-s4r8 -- sh -c 'test ! -e "$1" && mkdir -p "$1" && git -C "$2" archive "$3" | tar -x -C "$1"' sh "$OUT/F3-fmmret" "$REPO" "$F3" || exit 2
echo "exports: done"

# step 2: seamF-F3 = A,C,D then B2 (both with --report and logs); fmmret-F3 = --tree A.
# The redirections are inside the string given to sh -c, so they run under safe_run as well.
sh "$SAFE" p05-s4r8 -- sh -c 'python3 -I -B "$1/apply_seam_r2.py" --root "$2" --repo "$3" --families A,C,D --report "$4" > "$5" 2>&1' sh "$PY" "$OUT/F3-seamF" "$REPO" "$OUT/apply-F3-seamF-ACD.txt" "$OUT/F3-seamF-ACD.log" || { echo "FAIL ACD seamF-F3" >&2; exit 1; }
sh "$SAFE" p05-s4r8 -- sh -c 'python3 -I -B "$1/apply_seam_b2.py" --root "$2" --repo "$3" --report "$4" > "$5" 2>&1' sh "$PY" "$OUT/F3-seamF" "$REPO" "$OUT/apply-F3-seamF-B2.txt" "$OUT/F3-seamF-B2.log" || { echo "FAIL B2 seamF-F3" >&2; exit 1; }
echo "seamF-F3 applied (A,C,D then B2)"
sh "$SAFE" p05-s4r8 -- sh -c 'python3 -I -B "$1/apply_seam_r5_fmmret.py" --tree A --root "$2" --repo "$3" --report "$4" > "$5" 2>&1' sh "$PY" "$OUT/F3-fmmret" "$REPO" "$OUT/apply-F3-fmmret.txt" "$OUT/F3-fmmret.log" || { echo "FAIL fmmret-F3" >&2; exit 1; }
echo "fmmret-F3 applied (--tree A)"
echo "seam_r8: done"
exit 0
