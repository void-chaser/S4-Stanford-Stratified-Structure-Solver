#!/bin/sh
# build_four_r2.sh -- builds the four trees B, A, H, F in sequence (shared DRIVERS.tsv, so no parallel run).
#   sh testing/d003/safe_run.sh p05-s4r2 -- sh testing/d003/stage_s4/build_four_r2.sh p05-s4r2/run2
set -u
REPO=$(git rev-parse --show-toplevel)
OUT_ARG=${1:?"usage: build_four_r2.sh OUT_ARG"}
for spec in B:37a82e8 A:876181c H:64eb0b5 F:1c11905; do
    t=${spec%%:*}
    c=${spec##*:}
    sh "$REPO/testing/d003/stage_s4/build_tree_r2.sh" "$OUT_ARG" "$t" "$c" || { echo "build_four_r2: stopped at $t" >&2; exit 1; }
done
echo "build_four_r2: all four trees built"
exit 0
