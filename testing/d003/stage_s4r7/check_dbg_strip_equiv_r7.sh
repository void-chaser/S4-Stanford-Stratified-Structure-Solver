#!/bin/sh
# check_dbg_strip_equiv_r7.sh -- P05-S4 R7 cont9 ADD1, U84 (new file).
#
# Question: do the R7 debug libraries/drivers differ from the historical R5/R6c ones ONLY in debug sections?
# Method: copy every file of each pair into $EV/strip_cmp/, run `objcopy --strip-debug` on the COPIES only, then compare
# sha256 of the stripped copies.  Static libraries are compared member by member (ar x of both copies; member names must
# be identical; each .o is stripped and compared), so that ar headers (timestamps, uid/gid) cannot affect the result.
# Originals are never modified.  Nothing outside $EV/strip_cmp/ and $EV/ is written.
#
#   sh testing/d003/safe_run.sh p05-s4r7 -- sh testing/d003/stage_s4r7/check_dbg_strip_equiv_r7.sh p05-s4r7
#
# Output: $EV/strip_cmp/STRIP_EQUIV_R7.tsv   (pair, kind, member, sha_raw_eq, sha_stripped_eq, status)
#         $EV/strip_cmp/STRIP_EQUIV_SUMMARY_R7.txt
# Exit 0 iff every pair is equal after stripping (and nothing is missing).
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "check_dbg_strip_equiv_r7: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: check_dbg_strip_equiv_r7.sh p05-s4r7"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
TMPDIR="$EV/tmp"
export TMPDIR
SC="$EV/strip_cmp"
OBJCOPY=${OBJCOPY:-objcopy}
AR=${AR:-ar}

[ -d "$EV" ] || { echo "no evidence dir $EV" >&2; exit 2; }
[ -e "$SC" ] && { echo "REFUSED: $SC exists (U17)" >&2; exit 2; }

# Historical and R7 inputs (absolute paths under $REPO; read only)
R7_LIB_F_DBG="$EV/build_r7/F-dbg/build/libS4.a"
HIST_LIB_F_DBG="$REPO/checkpoints/p05/evidence/p05-s4r5/dbg/trees/F/build/libS4.a"
R7_DRV_G5="$EV/drivers_r7/r6bstate-F-dbg/driver"
HIST_DRV_G5="$REPO/checkpoints/p05/evidence/p05-s4r6b/drivers/r6b/driver-r6b-dbgF"
R7_LIB_SEAMF="$EV/build_r7/seam/seamF-F/build/libS4.a"
HIST_LIB_SEAMF="$REPO/checkpoints/p05/evidence/p05-s4r6c/seam_dbg/seamF/src/build/libS4.a"
R7_LIB_FMMRET="$EV/build_r7/seam/fmmret-F/build/libS4.a"
HIST_LIB_FMMRET="$REPO/checkpoints/p05/evidence/p05-s4r6c/seam_dbg/fmmret-F/src/build/libS4.a"
HIST_DRV_SEAMF="$REPO/checkpoints/p05/evidence/p05-s4r6c/seam_dbg/drivers/r6b-seamF/driver-r6b-seamF"
HIST_DRV_FMMRET="$REPO/checkpoints/p05/evidence/p05-s4r6c/seam_dbg/drivers/r6b-fmmret-F/driver-r6b-fmmret-F"

# drivers of G6 (driver-r6b-seamF / driver-r6b-fmmret-F) are not in R7 as r6b drivers; the R7 r6b-linked seam drivers
# are built in step 1 of the G6 preparation (see DRIVERS_R7_M3.tsv).  Pairs whose R7 input is missing are reported MISSING.
R7_DRV_G6_SEAMF="$EV/drivers_r7/r6bseam-seamF-F/driver"
R7_DRV_G6_FMMRET="$EV/drivers_r7/r6bseam-fmmret-F/driver"

mkdir -p "$SC" || exit 2
TSV="$SC/STRIP_EQUIV_R7.tsv"
printf 'pair\tkind\tmember\tsha_raw_equal\tsha_stripped_equal\tstatus\n' > "$TSV"
FAILS=0
MISSING=0
NPAIRS=0

# sha of a file (empty if missing)
sha() { if [ -f "$1" ]; then sha256sum "$1" | cut -d' ' -f1; else echo ""; fi; }

# compare_exe NAME R7FILE HISTFILE : copy both, strip the copies, compare
compare_exe() {
    NAME=$1; A=$2; B=$3
    NPAIRS=$((NPAIRS + 1))
    if [ ! -f "$A" ] || [ ! -f "$B" ]; then
        printf '%s\texe\t-\t-\t-\tMISSING\n' "$NAME" >> "$TSV"; MISSING=$((MISSING + 1)); return
    fi
    D="$SC/$NAME"
    mkdir -p "$D" || return
    cp "$A" "$D/r7.bin" && cp "$B" "$D/hist.bin" || { printf '%s\texe\t-\t-\t-\tCOPY_FAILED\n' "$NAME" >> "$TSV"; FAILS=$((FAILS+1)); return; }
    RAW=$([ "$(sha "$D/r7.bin")" = "$(sha "$D/hist.bin")" ] && echo yes || echo no)
    "$OBJCOPY" --strip-debug "$D/r7.bin" "$D/r7.stripped" && "$OBJCOPY" --strip-debug "$D/hist.bin" "$D/hist.stripped" \
        || { printf '%s\texe\t-\t%s\t-\tSTRIP_FAILED\n' "$NAME" "$RAW" >> "$TSV"; FAILS=$((FAILS+1)); return; }
    SS=$([ "$(sha "$D/r7.stripped")" = "$(sha "$D/hist.stripped")" ] && echo yes || echo no)
    if [ "$SS" = yes ]; then ST=EQUAL_AFTER_STRIP; else ST=DIFFERENT_AFTER_STRIP; FAILS=$((FAILS+1)); fi
    printf '%s\texe\t-\t%s\t%s\t%s\n' "$NAME" "$RAW" "$SS" "$ST" >> "$TSV"
}

# compare_lib NAME R7LIB HISTLIB : member by member after ar extraction and strip
compare_lib() {
    NAME=$1; A=$2; B=$3
    NPAIRS=$((NPAIRS + 1))
    if [ ! -f "$A" ] || [ ! -f "$B" ]; then
        printf '%s\tlib\t-\t-\t-\tMISSING\n' "$NAME" >> "$TSV"; MISSING=$((MISSING + 1)); return
    fi
    D="$SC/$NAME"
    mkdir -p "$D/r7" "$D/hist" || return
    cp "$A" "$D/r7.a" && cp "$B" "$D/hist.a" || { printf '%s\tlib\t-\t-\t-\tCOPY_FAILED\n' "$NAME" >> "$TSV"; FAILS=$((FAILS+1)); return; }
    (cd "$D/r7" && "$AR" x "../r7.a") || { printf '%s\tlib\t-\t-\t-\tAR_FAILED\n' "$NAME" >> "$TSV"; FAILS=$((FAILS+1)); return; }
    (cd "$D/hist" && "$AR" x "../hist.a") || { printf '%s\tlib\t-\t-\t-\tAR_FAILED\n' "$NAME" >> "$TSV"; FAILS=$((FAILS+1)); return; }
    NA=$(cd "$D/r7" && ls | sort | tr '\n' ' ')
    NB=$(cd "$D/hist" && ls | sort | tr '\n' ' ')
    if [ "$NA" != "$NB" ]; then
        printf '%s\tlib\tMEMBER_LIST\t-\t-\tMEMBER_NAMES_DIFFER\n' "$NAME" >> "$TSV"; FAILS=$((FAILS+1)); return
    fi
    printf '%s\tlib\tMEMBER_LIST\tNA\tNA\tSAME_NAMES(%s)\n' "$NAME" "$(echo $NA | wc -w)" >> "$TSV"
    for m in $NA; do
        RAW=$([ "$(sha "$D/r7/$m")" = "$(sha "$D/hist/$m")" ] && echo yes || echo no)
        "$OBJCOPY" --strip-debug "$D/r7/$m" "$D/r7/$m.s" && "$OBJCOPY" --strip-debug "$D/hist/$m" "$D/hist/$m.s" \
            || { printf '%s\tlib\t%s\t%s\t-\tSTRIP_FAILED\n' "$NAME" "$m" "$RAW" >> "$TSV"; FAILS=$((FAILS+1)); continue; }
        SS=$([ "$(sha "$D/r7/$m.s")" = "$(sha "$D/hist/$m.s")" ] && echo yes || echo no)
        if [ "$SS" = yes ]; then ST=EQUAL_AFTER_STRIP; else ST=DIFFERENT_AFTER_STRIP; FAILS=$((FAILS+1)); fi
        printf '%s\tlib\t%s\t%s\t%s\t%s\n' "$NAME" "$m" "$RAW" "$SS" "$ST" >> "$TSV"
    done
}

compare_lib libF-dbg-vs-R5      "$R7_LIB_F_DBG"  "$HIST_LIB_F_DBG"
compare_exe drvG5-r6bstate-F    "$R7_DRV_G5"     "$HIST_DRV_G5"
compare_lib libseamF-vs-R6c     "$R7_LIB_SEAMF"  "$HIST_LIB_SEAMF"
compare_lib libfmmret-F-vs-R6c  "$R7_LIB_FMMRET" "$HIST_LIB_FMMRET"
compare_exe drvG6-seamF         "$R7_DRV_G6_SEAMF"  "$HIST_DRV_SEAMF"
compare_exe drvG6-fmmret-F      "$R7_DRV_G6_FMMRET" "$HIST_DRV_FMMRET"

{
    echo "check_dbg_strip_equiv_r7.sh (U84): pairs=$NPAIRS failing_or_differing_items=$FAILS missing_pairs=$MISSING"
    echo "objcopy: $($OBJCOPY --version | head -1)"
    if [ "$FAILS" -eq 0 ] && [ "$MISSING" -eq 0 ]; then echo "RESULT PASS: every pair equal after --strip-debug"; else echo "RESULT NOT_PASS"; fi
} > "$SC/STRIP_EQUIV_SUMMARY_R7.txt"
cat "$SC/STRIP_EQUIV_SUMMARY_R7.txt"
[ "$FAILS" -eq 0 ] && [ "$MISSING" -eq 0 ] || exit 1
exit 0
