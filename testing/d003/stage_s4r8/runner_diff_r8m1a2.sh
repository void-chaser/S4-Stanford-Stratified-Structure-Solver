#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# runner_diff_r8m1a2.sh -- P05-S4 R8 M1a CONT1 section 4.1 (E8-25): diff -u of each M1a and CONT1 copy against its original.  New file.
# Pairs (copy, original).  diff exits 1 when the files differ; that is the expected result here.
#   build_seam_r8m1.sh     <- stage_s4r7/build_seam_s4r7.sh
#   link_drivers_r8m1.sh   <- stage_s4r7/link_drivers_s4r7.sh
#   strip_equiv_r8m1.sh    <- stage_s4r7/check_dbg_strip_equiv_r7.sh
#   gate4_r8m1.sh          <- stage_s4r8/gate3_r8.sh
#   recheck_s4r7_r8m1a2.py <- recheck_s4r7_r8m1.py
#   gate5_r8m1a2.sh        <- gate4_r8m1.sh
# The static-map script of CONT1 (section 4.3) is not compared here; its own run records its origin.
# Only pairs whose both files exist are compared; a missing input stops the run before the output is created (exit 2).
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "runner_diff_r8m1a2: first argument must be p05-s4r8" >&2; exit 2; }
OUT="$EV/RUNNER_DIFF_R8_M1a.txt"
test ! -e "$OUT" || { echo "runner_diff_r8m1a2: REFUSED exists: $OUT" >&2; exit 2; }
S7="$REPO/testing/d003/stage_s4r7"
S8="$REPO/testing/d003/stage_s4r8"
# every input of every pair must exist before the output is created (brief 0.2)
for f in "$S7/build_seam_s4r7.sh" "$S8/build_seam_r8m1.sh" \
         "$S7/link_drivers_s4r7.sh" "$S8/link_drivers_r8m1.sh" \
         "$S7/check_dbg_strip_equiv_r7.sh" "$S8/strip_equiv_r8m1.sh" \
         "$S8/gate3_r8.sh" "$S8/gate4_r8m1.sh" \
         "$S8/recheck_s4r7_r8m1.py" "$S8/recheck_s4r7_r8m1a2.py" \
         "$S8/gate5_r8m1a2.sh"; do
    test -f "$f" || { echo "runner_diff_r8m1a2: REFUSED: input missing: $f" >&2; exit 2; }
done
{
    echo "# RUNNER_DIFF_R8_M1a.txt -- diff -u of each M1a (and CONT1) copy against its original (CONT1 section 4.1; E8-25; written after the run)."
    echo "# Paths in the headers are repository paths.  diff exits 1 when a pair differs; that is the expected result."
    echo "# ===== build_seam_r8m1.sh vs build_seam_s4r7.sh"
    diff -u "$S7/build_seam_s4r7.sh" "$S8/build_seam_r8m1.sh"; true
    echo "# ===== link_drivers_r8m1.sh vs link_drivers_s4r7.sh"
    diff -u "$S7/link_drivers_s4r7.sh" "$S8/link_drivers_r8m1.sh"; true
    echo "# ===== strip_equiv_r8m1.sh vs check_dbg_strip_equiv_r7.sh"
    diff -u "$S7/check_dbg_strip_equiv_r7.sh" "$S8/strip_equiv_r8m1.sh"; true
    echo "# ===== gate4_r8m1.sh vs gate3_r8.sh"
    diff -u "$S8/gate3_r8.sh" "$S8/gate4_r8m1.sh"; true
    echo "# ===== recheck_s4r7_r8m1a2.py vs recheck_s4r7_r8m1.py"
    diff -u "$S8/recheck_s4r7_r8m1.py" "$S8/recheck_s4r7_r8m1a2.py"; true
    echo "# ===== gate5_r8m1a2.sh vs gate4_r8m1.sh"
    diff -u "$S8/gate4_r8m1.sh" "$S8/gate5_r8m1a2.sh"; true
} > "$OUT" 2>&1
echo "runner_diff_r8m1a2: done -> $OUT"
exit 0
