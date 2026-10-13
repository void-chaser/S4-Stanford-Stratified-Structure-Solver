#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# compare_seam_r8.sh -- P05-S4 R8 M0 step 3.3: seam difference check, F3 against F2 by normalised diff (new file).
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/compare_seam_r8.sh p05-s4r8
# Method (brief 3.3): diff -ru of each F3 seam tree against its clean F3 tree; then the lines "diff -ru", "---", "+++"
# are removed and every "@@ ... @@" header is replaced by "@@" (the F3 files have line offsets); the same normalisation
# is applied to the R7 reference diffs p05-s4r7/seam_r7/seamdiff_F2_{seamF,fmmret}.diff (read only).
# Output: $EV/SEAM_DIFF_F2_vs_F3_R8.txt (new file): per variant IDENTICAL or DIFFERS, with the first 40 differing lines.
# Raw and normalised intermediate files go to $EV/seam_r8/ (new) and $EV/tmp/.
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "compare_seam_r8: first argument must be p05-s4r8" >&2; exit 2; }
OUT="$EV/SEAM_DIFF_F2_vs_F3_R8.txt"
test ! -e "$OUT" || { echo "compare_seam_r8: REFUSED exists: $OUT" >&2; exit 2; }
R7_SEAMF="$REPO/checkpoints/p05/evidence/p05-s4r7/seam_r7/seamdiff_F2_seamF.diff"
R7_FMMRET="$REPO/checkpoints/p05/evidence/p05-s4r7/seam_r7/seamdiff_F2_fmmret.diff"
test -f "$R7_SEAMF" && test -f "$R7_FMMRET" || { echo "compare_seam_r8: REFUSED: R7 reference diffs missing" >&2; exit 2; }
test -d "$EV/seam_r8/F3-seamF" && test -d "$EV/seam_r8/F3-fmmret" || { echo "compare_seam_r8: REFUSED: seam trees missing" >&2; exit 2; }
test -d "$EV/trees/F3" || { echo "compare_seam_r8: REFUSED: clean F3 tree missing" >&2; exit 2; }
RAW_A="$EV/seam_r8/diff_F3_seamF.raw"
RAW_B="$EV/seam_r8/diff_F3_fmmret.raw"
test ! -e "$RAW_A" && test ! -e "$RAW_B" || { echo "compare_seam_r8: REFUSED: raw diff exists" >&2; exit 2; }
SAFE="$REPO/testing/d003/safe_run.sh"
# raw diffs: diff exits 1 when files differ; that is the expected result, so the status is not treated as an error
sh "$SAFE" p05-s4r8 -- sh -c 'diff -ru "$1" "$2" > "$3" 2>&1; true' sh "$EV/trees/F3" "$EV/seam_r8/F3-seamF" "$RAW_A" || exit 2
sh "$SAFE" p05-s4r8 -- sh -c 'diff -ru "$1" "$2" > "$3" 2>&1; true' sh "$EV/trees/F3" "$EV/seam_r8/F3-fmmret" "$RAW_B" || exit 2
# normalisation (awk, reading the files; output to new files under $EV/tmp)
NORM_A="$EV/tmp/norm_F3_seamF.txt"
NORM_B="$EV/tmp/norm_F3_fmmret.txt"
NORM_R7A="$EV/tmp/norm_R7_F2_seamF.txt"
NORM_R7B="$EV/tmp/norm_R7_F2_fmmret.txt"
NF="$REPO/testing/d003/stage_s4r8/normalise_diff_r8.awk"
test -f "$NF" || { echo "compare_seam_r8: REFUSED: normalise script missing" >&2; exit 2; }
sh "$SAFE" p05-s4r8 -- sh -c 'awk -f "$1" "$2" > "$3" && awk -f "$1" "$4" > "$5" && awk -f "$1" "$6" > "$7" && awk -f "$1" "$8" > "$9"' sh "$NF" "$RAW_A" "$NORM_A" "$RAW_B" "$NORM_B" "$R7_SEAMF" "$NORM_R7A" "$R7_FMMRET" "$NORM_R7B" || { echo "compare_seam_r8: normalisation failed" >&2; exit 2; }
verdict() {
    # $1 = normalised F3 file, $2 = normalised R7 file, $3 = label
    if cmp -s "$1" "$2"; then echo "$3: IDENTICAL (normalised content; $(wc -l < "$1") lines)"; else echo "$3: DIFFERS"; fi
}
{
    echo "# SEAM_DIFF_F2_vs_F3_R8 -- P05-S4 R8 M0 seam difference check (brief 3.3)."
    echo "# Method: diff -ru of each F3 seam tree against the clean F3 tree; diff header lines removed; @@ headers reduced to @@;"
    echo "# compared with the same normalisation of p05-s4r7/seam_r7/seamdiff_F2_{seamF,fmmret}.diff (R7, F2)."
    echo "# Raw F3 diffs: evidence/p05-s4r8/seam_r8/diff_F3_{seamF,fmmret}.raw; normalised: the TMPDIR of the round (evidence/p05-s4r8, tmp subdirectory)."
    echo "# verdict per variant (only IDENTICAL or DIFFERS; DIFFERS also lists the first 40 lines of the normalised F3 content)."
    echo "variant seamF:"
    verdict "$NORM_A" "$NORM_R7A" "seamF"
    echo "variant fmmret:"
    verdict "$NORM_B" "$NORM_R7B" "fmmret"
    if ! cmp -s "$NORM_A" "$NORM_R7A"; then echo "--- seamF normalised F3 (first 40 lines)"; head -n 40 "$NORM_A"; fi
    if ! cmp -s "$NORM_B" "$NORM_R7B"; then echo "--- fmmret normalised F3 (first 40 lines)"; head -n 40 "$NORM_B"; fi
} > "$OUT"
grep -c 'DIFFERS' "$OUT" | sed 's/^/differs_lines=/'
echo "compare_seam_r8: done"
exit 0
