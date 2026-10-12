#!/bin/sh
# build_s3r3.sh -- P05-S3R3-1 compile check (new file).
#
#   sh testing/d003/safe_run.sh p05-s3r3 -- sh testing/d003/stage_s3r3/build_s3r3.sh p05-s3r3
#
# Builds two trees into $EV (the only write target besides $EV/tmp):
#   F   = HEAD:S4 (= tree F, 4a6f649...), exported with git archive
#   F2  = the working-tree S4/ after the S3R3 edits (pattern.c and S4_internal.h); copied from the
#         working tree (read only), with the two approved files from the working tree
# Two builds per tree:
#   dbg   : -O0 -g   (same overrides as run_r5_dbg_build.sh)
#   plain : -O3 -march=native (the Makefile default, as in R4 build-plain-*.log)
# Output: $EV/build/{F,F2}-{dbg,plain}/ (library, build log), $EV/build/WARNINGS_*.tsv
# Nothing is written to the repository S4/ tree.
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "build_s3r3: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: build_s3r3.sh p05-s3r3"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
OUT="$EV/build"
TMPDIR="$EV/tmp"
export TMPDIR
JOBS=${JOBS:-$(nproc)}
SAFE="$REPO/testing/d003/safe_run.sh"

# 1) export F (git archive of HEAD:S4 is not needed: export the whole HEAD tree, S4 is a subdirectory)
sh "$SAFE" "$OUT_ARG" -- sh -c 'rm -rf "$1/trees/F" && mkdir -p "$1/trees/F" && git -C "$2" archive HEAD | tar -x -C "$1/trees/F"' sh "$OUT" "$REPO" || { echo "export F failed" >&2; exit 1; }

# 2) export F2 = F + the two working-tree files (read from the working tree; written only under $OUT)
sh "$SAFE" "$OUT_ARG" -- sh -c 'rm -rf "$1/trees/F2" && cp -r "$1/trees/F" "$1/trees/F2" && cp "$2/S4/pattern/pattern.c" "$1/trees/F2/S4/pattern/pattern.c" && cp "$2/S4/S4_internal.h" "$1/trees/F2/S4/S4_internal.h"' sh "$OUT" "$REPO" || { echo "export F2 failed" >&2; exit 1; }

# 3) builds
build_one() {
    TAG=$1; MODE=$2
    if [ "$MODE" = dbg ]; then
        CF="-O0 -g -Wall -fPIC -fcx-limited-range -fno-exceptions"
        CXF="-O0 -g -Wall -fcx-limited-range -fno-exceptions -fPIC"
    else
        CF="-O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC"
        CXF="-O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC"
    fi
    # one private copy per (tree, mode), so that the two builds do not share build/ objects
    WD="$OUT/trees/${TAG}-${MODE}"
    LOG="$OUT/build-${TAG}-${MODE}.log"
    sh "$SAFE" "$OUT_ARG" -- sh -c 'rm -rf "$1" && cp -r "$2" "$1"' sh "$WD" "$OUT/trees/$TAG" || return 1
    sh "$SAFE" "$OUT_ARG" -- sh -c 'cd "$1" && make objdir > "$2" 2>&1 && make -j"$3" CPPFLAGS="-IS4 -IS4/RNP -IS4/kiss_fft" CFLAGS="$4" CXXFLAGS="$5" build/libS4.a >> "$2" 2>&1; echo "make rc=$?" >> "$2"' sh "$WD" "$LOG" "$JOBS" "$CF" "$CXF"
    echo "warnings: $(grep -c 'warning:' "$LOG")"
    tail -1 "$LOG"
}

for T in F F2; do
    for M in dbg plain; do
        echo "== build $T $M"
        build_one "$T" "$M"
    done
done
echo "build_s3r3: done"
exit 0
