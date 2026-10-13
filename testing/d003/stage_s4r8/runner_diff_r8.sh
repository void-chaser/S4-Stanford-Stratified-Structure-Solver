#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# runner_diff_r8.sh -- P05-S4 R8 M0: diff -u of each R8 copy against its R7 original (brief section 0.2).  New file.
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/runner_diff_r8.sh p05-s4r8
# Output: $EV/RUNNER_DIFF_R8_M0.txt (new).  diff exits 1 when the files differ; that is the expected result here.
# Pairs (copy, original): build_s4r8.sh <- build_s4r7.sh; build_seam_plain_r8.sh <- build_seam_plain_s4r7.sh;
# link_drivers_r8.sh <- link_drivers_s4r7.sh; run_noinject_equiv_r8.sh <- run_noinject_equiv_r7.sh.
# Scripts with no R7 script original (their R7 counterpart was an inline command in safe_run.log) are listed in ERRATA_8.
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "runner_diff_r8: first argument must be p05-s4r8" >&2; exit 2; }
OUT="$EV/RUNNER_DIFF_R8_M0.txt"
test ! -e "$OUT" || { echo "runner_diff_r8: REFUSED exists: $OUT" >&2; exit 2; }
S7="$REPO/testing/d003/stage_s4r7"
S8="$REPO/testing/d003/stage_s4r8"
for f in "$S7/build_s4r7.sh" "$S7/build_seam_plain_s4r7.sh" "$S7/link_drivers_s4r7.sh" "$S7/run_noinject_equiv_r7.sh" \
         "$S8/build_s4r8.sh" "$S8/build_seam_plain_r8.sh" "$S8/link_drivers_r8.sh" "$S8/run_noinject_equiv_r8.sh"; do
    test -f "$f" || { echo "runner_diff_r8: REFUSED: input missing: $f" >&2; exit 2; }
done
{
    echo "# RUNNER_DIFF_R8_M0.txt -- diff -u of each R8 copy against its R7 original (brief section 0.2; ERRATA_8 E8-5)."
    echo "# Paths in the headers are repository paths; the R7 and R8 files are compared as they are in the repository."
    echo "# ===== build_s4r8.sh vs build_s4r7.sh"
    diff -u "$S7/build_s4r7.sh" "$S8/build_s4r8.sh"; true
    echo "# ===== build_seam_plain_r8.sh vs build_seam_plain_s4r7.sh"
    diff -u "$S7/build_seam_plain_s4r7.sh" "$S8/build_seam_plain_r8.sh"; true
    echo "# ===== link_drivers_r8.sh vs link_drivers_s4r7.sh"
    diff -u "$S7/link_drivers_s4r7.sh" "$S8/link_drivers_r8.sh"; true
    echo "# ===== run_noinject_equiv_r8.sh vs run_noinject_equiv_r7.sh"
    diff -u "$S7/run_noinject_equiv_r7.sh" "$S8/run_noinject_equiv_r8.sh"; true
} > "$OUT" 2>&1
echo "runner_diff_r8: done -> $OUT"
exit 0
