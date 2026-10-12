#!/bin/sh
# build_option_diff_r7.sh -- P05-S4 R7 cont9 (M3 section 2.1): compile-option difference between R7 and the historical
# debug builds used by G5 (R5 dbg F, which R6c's driver used) and G6 (R6c seam dbg libraries).  New file.
# Compares the g++ -c command lines of the build logs, after removing absolute path prefixes (DWARF comp_dir only).
# Output: $EV/BUILD_OPTION_DIFF_R7_M3.txt   (one line per pair: lines compared, lines differing; expected 0 differing)
#
#   sh testing/d003/safe_run.sh p05-s4r7 -- sh testing/d003/stage_s4r7/build_option_diff_r7.sh p05-s4r7
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "build_option_diff_r7: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: build_option_diff_r7.sh p05-s4r7"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
TMPDIR="$EV/tmp"
export TMPDIR
OUT="$EV/BUILD_OPTION_DIFF_R7_M3.txt"
[ -e "$OUT" ] && { echo "REFUSED: $OUT exists (U17)" >&2; exit 2; }

norm() { sed -e 's#/srv/[^ ]*/\(S4\|build\|checkpoints\|testing\)#<P>/\1#g' -e 's#-o [^ ]*#-o <OUT>#g'; }

# fixed scratch names under $TMPDIR (inside the evidence directory); written by the shell redirection, which runs under safe_run
cmp_pair() {
    NAME=$1; A=$2; B=$3
    grep '^g++ ' "$A" | norm > "$TMPDIR/cmp_a.txt"
    grep '^g++ ' "$B" | norm > "$TMPDIR/cmp_b.txt"
    NA=$(wc -l < "$TMPDIR/cmp_a.txt"); NB=$(wc -l < "$TMPDIR/cmp_b.txt")
    DIFF=$(diff "$TMPDIR/cmp_a.txt" "$TMPDIR/cmp_b.txt" | grep -c '^[<>]')
    printf '%s\tlines_hist=%s\tlines_r7=%s\tdiff_lines=%s\n' "$NAME" "$NB" "$NA" "$DIFF"
}

{
    echo "BUILD_OPTION_DIFF_R7_M3 (cont9 section 2.1): g++ command lines, path prefixes removed; expected diff_lines=0"
    cmp_pair "G5 R5-dbg-F vs R7-F-dbg" "$REPO/checkpoints/p05/evidence/p05-s4r5/dbg/build-dbg-F.log" "$EV/build_r7/build-F-dbg.log"
    cmp_pair "G6 R6c-seamF vs R7-seamF-F" "$REPO/checkpoints/p05/evidence/p05-s4r6c/seam_dbg/build-seamF.log" "$EV/build_r7/seam/build-seamF-F.log"
    cmp_pair "G6 R6c-fmmret-F vs R7-fmmret-F" "$REPO/checkpoints/p05/evidence/p05-s4r6c/seam_dbg/build-fmmret-F.log" "$EV/build_r7/seam/build-fmmret-F.log"
} > "$OUT"
cat "$OUT"
