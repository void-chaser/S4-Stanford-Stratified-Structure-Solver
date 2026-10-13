REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# apply_seam_f3_c3.sh -- apply the historical seam scripts to two copies of the F3 export (CTRL_SEAM group, CONT3 D).
# Copies: $EV/seam_f3/seamF and $EV/seam_f3/fmmret (each a copy of $EV/f3_export/S4, never the repository S4/ tree).
# seamF   : apply_seam_r2.py --families A,C,D   (the R7 seamF-F recipe; family B2 not included in R7's ACD apply record)
# fmmret  : apply_seam_r5_fmmret.py --tree A    (the R7 fmmret recipe: same output as --tree H on F, per R7 record)
# Output: apply logs in $EV/seam_f3/, diffs in $EV/seam_f3/*.diff.  Refuses to overwrite.
set -u
SRC="$EV/f3_export"
BASE="$EV/seam_f3"
test -e "$BASE" && { echo "REFUSED: exists $BASE"; exit 2; }
mkdir -p "$BASE/seamF" "$BASE/fmmret" || exit 2
cp -R "$SRC/S4" "$BASE/seamF/S4" > "$BASE/copy_seamF.log" 2>&1 || exit 2
cp -R "$SRC/S4" "$BASE/fmmret/S4" > "$BASE/copy_fmmret.log" 2>&1 || exit 2
python3 "$REPO/testing/d003/seam/apply_seam_r2.py" --root "$BASE/seamF" --repo "$REPO" --families A,C,D --report "$BASE/seamF_apply_report.txt" > "$BASE/apply_seamF.log" 2>&1
echo "apply seamF rc=$?"
python3 "$REPO/testing/d003/seam/apply_seam_r5_fmmret.py" --tree A --root "$BASE/fmmret" --repo "$REPO" --report "$BASE/fmmret_apply_report.txt" > "$BASE/apply_fmmret.log" 2>&1
echo "apply fmmret rc=$?"
echo "done"
