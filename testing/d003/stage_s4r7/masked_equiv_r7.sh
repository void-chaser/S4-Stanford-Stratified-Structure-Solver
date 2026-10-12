#!/bin/sh
# masked_equiv_r7.sh -- P05-S4 R7 cont9 ADD2 (U87, new file).
# For the three driver pairs whose stripped copies differed only in .note.gnu.build-id (STRIP_EQUIV_R7.tsv):
#   copy each $EV/strip_cmp/<pair>/{r7,hist}.stripped to {r7,hist}.stripped.masked (copies only),
#   zero the build-id descriptor of each copy with mask_build_id_r7.py, compare sha256 of the two .masked copies.
# Output: $EV/strip_cmp/MASKED_EQUIV_R7.tsv and $EV/strip_cmp/MASKED_EQUIV_SUMMARY_R7.txt
#
#   sh testing/d003/safe_run.sh p05-s4r7 -- sh testing/d003/stage_s4r7/masked_equiv_r7.sh p05-s4r7
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "masked_equiv_r7: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: masked_equiv_r7.sh p05-s4r7"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
TMPDIR="$EV/tmp"
export TMPDIR
SC="$EV/strip_cmp"
MASK="$REPO/testing/d003/stage_s4r7/mask_build_id_r7.py"
TSV="$SC/MASKED_EQUIV_R7.tsv"
SUM="$SC/MASKED_EQUIV_SUMMARY_R7.txt"

[ -e "$TSV" ] && { echo "REFUSED: $TSV exists (U17)" >&2; exit 2; }
[ -f "$SC/drvG5-r6bstate-F/r7.stripped" ] || { echo "missing strip copies in $SC" >&2; exit 2; }

printf 'pair\tr7_stripped_sha256\thist_stripped_sha256\tr7_masked_sha256\thist_masked_sha256\tbuild_id_bytes_differing_before\tstatus\n' > "$TSV"
FAILS=0
for P in drvG5-r6bstate-F drvG6-seamF drvG6-fmmret-F; do
    D="$SC/$P"
    test -f "$D/r7.stripped" && test -f "$D/hist.stripped" || { printf '%s\t-\t-\t-\t-\t-\tMISSING\n' "$P" >> "$TSV"; FAILS=$((FAILS+1)); continue; }
    cp "$D/r7.stripped" "$D/r7.stripped.masked" && cp "$D/hist.stripped" "$D/hist.stripped.masked" || { printf '%s\t-\t-\t-\t-\t-\tCOPY_FAILED\n' "$P" >> "$TSV"; FAILS=$((FAILS+1)); continue; }
    python3 -I -B "$MASK" "$D/r7.stripped.masked" "$D/hist.stripped.masked" > "$D/mask.log" 2>&1 || { printf '%s\t-\t-\t-\t-\t-\tMASK_FAILED\n' "$P" >> "$TSV"; FAILS=$((FAILS+1)); continue; }
    A0=$(sha256sum "$D/r7.stripped" | cut -d' ' -f1)
    B0=$(sha256sum "$D/hist.stripped" | cut -d' ' -f1)
    A=$(sha256sum "$D/r7.stripped.masked" | cut -d' ' -f1)
    B=$(sha256sum "$D/hist.stripped.masked" | cut -d' ' -f1)
    # bytes that differ between the two stripped copies (must lie inside the build-id descriptor)
    NDIFF=$(cmp -l "$D/r7.stripped" "$D/hist.stripped" | wc -l)
    if [ "$A" = "$B" ]; then ST=EQUAL_AFTER_MASK; else ST=DIFFERENT_AFTER_MASK; FAILS=$((FAILS+1)); fi
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$P" "$A0" "$B0" "$A" "$B" "$NDIFF" "$ST" >> "$TSV"
done

{
    echo "masked_equiv_r7.sh (U87): pairs=3 not_equal_after_mask=$FAILS"
    if [ "$FAILS" -eq 0 ]; then echo "RESULT PASS: driver pairs equal after --strip-debug and build-id zeroing"; else echo "RESULT NOT_PASS"; fi
} > "$SUM"
cat "$SUM"
[ "$FAILS" -eq 0 ] || exit 1
exit 0
