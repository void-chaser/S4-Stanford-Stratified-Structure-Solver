#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# strip_equiv_r8m1.sh -- P05-S4 R8 M1a, step 0 (brief section 4; U141, U136; closes or keeps open E8-9).  New file.
# Copy of testing/d003/stage_s4r7/check_dbg_strip_equiv_r7.sh (committed, not modified), with these changes only:
#   (1) the standard first line (brief section 0.2) replaces the R7 first line (the one with the stderr discard);
#   (2) the comparison objects: the R8 F3 debug library and the S3R4 F3 debug library (U141), not the R5/R6c pairs;
#   (3) the driver pairs (drvG5, drvG6) are removed: U141 asks for the libraries only;
#   (4) the output directory is $EV/strip_cmp_r8m1/, the output names carry _R8_M1a.
# Method (U84, U87, as in R7): copies of both libraries are made, --strip-debug runs on the COPIES only, each static-library
# member is extracted with ar x and compared after stripping.  Originals are not modified.  Nothing outside $EV is written.
#
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/strip_equiv_r8m1.sh p05-s4r8
#
# Output: $EV/strip_cmp_r8m1/STRIP_EQUIV_R8_M1a.tsv (one line per member)
#         $EV/strip_cmp_r8m1/STRIP_EQUIV_SUMMARY_R8_M1a.txt (member count, EQUAL_AFTER_STRIP count, other count)
# Exit 0 iff every member is equal after stripping and nothing is missing.
set -u
OUT_ARG=${1:?"usage: strip_equiv_r8m1.sh p05-s4r8"}
[ "$OUT_ARG" = p05-s4r8 ] || { echo "strip_equiv_r8m1: first argument must be p05-s4r8" >&2; exit 2; }
OBJCOPY=${OBJCOPY:-objcopy}
AR=${AR:-ar}
SC="$EV/strip_cmp_r8m1"
[ -e "$SC" ] && { echo "REFUSED: $SC exists (U17)" >&2; exit 2; }

# the two libraries compared (read only)
R8_LIB_F3_DBG="$EV/build_r8/F3-dbg/build/libS4.a"
HIST_LIB_F3_DBG="$REPO/checkpoints/p05/evidence/p05-s3r4/build_f3/dbg/build/libS4.a"
[ -f "$R8_LIB_F3_DBG" ] || { echo "missing $R8_LIB_F3_DBG" >&2; exit 2; }
[ -f "$HIST_LIB_F3_DBG" ] || { echo "missing $HIST_LIB_F3_DBG" >&2; exit 2; }
test "$(sha256sum "$HIST_LIB_F3_DBG" | cut -d' ' -f1)" = 10ea03b37ccdb6f256bd65904763520e6570e297ba2060416f28253e1f065afa || { echo "S3R4 F3-dbg library sha256 differs from U141" >&2; exit 2; }

mkdir -p "$SC" || exit 2
TSV="$SC/STRIP_EQUIV_R8_M1a.tsv"
printf 'pair\tkind\tmember\tsha_raw_equal\tsha_stripped_equal\tstatus\n' > "$TSV"
FAILS=0
MISSING=0
NMEMB=0
NEQ=0

sha() { if [ -f "$1" ]; then sha256sum "$1" | cut -d' ' -f1; else echo ""; fi; }

# compare_lib NAME R8LIB HISTLIB : member by member after ar extraction and strip
compare_lib() {
    NAME=$1; A=$2; B=$3
    D="$SC/$NAME"
    mkdir -p "$D/r8" "$D/hist" || return
    cp "$A" "$D/r8.a" && cp "$B" "$D/hist.a" || { printf '%s\tlib\t-\t-\t-\tCOPY_FAILED\n' "$NAME" >> "$TSV"; FAILS=$((FAILS+1)); return; }
    (cd "$D/r8" && "$AR" x "../r8.a") || { printf '%s\tlib\t-\t-\t-\tAR_FAILED\n' "$NAME" >> "$TSV"; FAILS=$((FAILS+1)); return; }
    (cd "$D/hist" && "$AR" x "../hist.a") || { printf '%s\tlib\t-\t-\t-\tAR_FAILED\n' "$NAME" >> "$TSV"; FAILS=$((FAILS+1)); return; }
    NA=$(cd "$D/r8" && ls | LC_ALL=C sort | tr '\n' ' ')
    NB=$(cd "$D/hist" && ls | LC_ALL=C sort | tr '\n' ' ')
    if [ "$NA" != "$NB" ]; then
        printf '%s\tlib\tMEMBER_LIST\t-\t-\tMEMBER_NAMES_DIFFER\n' "$NAME" >> "$TSV"; FAILS=$((FAILS+1)); return
    fi
    printf '%s\tlib\tMEMBER_LIST\tNA\tNA\tSAME_NAMES(%s)\n' "$NAME" "$(echo $NA | wc -w)" >> "$TSV"
    for m in $NA; do
        NMEMB=$((NMEMB + 1))
        RAW=$([ "$(sha "$D/r8/$m")" = "$(sha "$D/hist/$m")" ] && echo yes || echo no)
        "$OBJCOPY" --strip-debug "$D/r8/$m" "$D/r8/$m.s" && "$OBJCOPY" --strip-debug "$D/hist/$m" "$D/hist/$m.s" \
            || { printf '%s\tlib\t%s\t%s\t-\tSTRIP_FAILED\n' "$NAME" "$m" "$RAW" >> "$TSV"; FAILS=$((FAILS+1)); continue; }
        SS=$([ "$(sha "$D/r8/$m.s")" = "$(sha "$D/hist/$m.s")" ] && echo yes || echo no)
        if [ "$SS" = yes ]; then ST=EQUAL_AFTER_STRIP; NEQ=$((NEQ + 1)); else ST=DIFFERENT_AFTER_STRIP; FAILS=$((FAILS+1)); fi
        printf '%s\tlib\t%s\t%s\t%s\t%s\n' "$NAME" "$m" "$RAW" "$SS" "$ST" >> "$TSV"
    done
}

compare_lib libF3-dbg-R8-vs-S3R4 "$R8_LIB_F3_DBG" "$HIST_LIB_F3_DBG"

OTHER=$((NMEMB - NEQ))
{
    echo "strip_equiv_r8m1.sh (U141, U136): members=$NMEMB equal_after_strip=$NEQ other=$OTHER failing_or_differing_items=$FAILS missing_pairs=$MISSING"
    echo "objcopy: $($OBJCOPY --version | head -n 1)"
    if [ "$FAILS" -eq 0 ] && [ "$MISSING" -eq 0 ] && [ "$NMEMB" -gt 0 ]; then echo "RESULT PASS: every member equal after --strip-debug"; else echo "RESULT NOT_PASS"; fi
} > "$SC/STRIP_EQUIV_SUMMARY_R8_M1a.txt"
cat "$SC/STRIP_EQUIV_SUMMARY_R8_M1a.txt"
[ "$FAILS" -eq 0 ] && [ "$MISSING" -eq 0 ] && [ "$NMEMB" -gt 0 ] || exit 1
exit 0
