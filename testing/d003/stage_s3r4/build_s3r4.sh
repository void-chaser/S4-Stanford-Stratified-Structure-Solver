#!/bin/sh
# build_s3r4.sh -- P05-S3R4 compile check (new file; layout copied from testing/d003/stage_s3r3/build_s3r3.sh).
#
#   sh testing/d003/safe_run.sh p05-s3r4 -- sh testing/d003/stage_s3r4/build_s3r4.sh p05-s3r4 <TAG_LIST>
#
# Trees:
#   F2 = HEAD:S4 exported with git archive (HEAD must be the S3R3 F2 tree, e124925f...; checked below)
#   W  = the working-tree S4/ (the S3R4 candidate); copied from the working tree (read only)
# Two builds per tree (same flags as build_s3r3.sh):
#   dbg   : -O0 -g
#   plain : -O3 -march=native (Makefile default)
# Output: $EV/build/<TAG>-<MODE>/ and $EV/build/build-<TAG>-<MODE>.log; warnings count in the log.
# Nothing is written to the repository S4/ tree.
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "build_s3r4: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: build_s3r4.sh p05-s3r4"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
OUT="$EV/build"
TMPDIR="$EV/tmp"
export TMPDIR
JOBS=${JOBS:-$(nproc)}
SAFE="$REPO/testing/d003/safe_run.sh"

# 1) export F2 = HEAD:S4 (tree e124925f...). S4 is a subdirectory of the HEAD tree; export the whole tree.
sh "$SAFE" "$OUT_ARG" -- sh -c 'rm -rf "$1/trees/F2" && mkdir -p "$1/trees/F2" && git -C "$2" archive HEAD | tar -x -C "$1/trees/F2"' sh "$OUT" "$REPO" || { echo "export F2 failed" >&2; exit 1; }

# 2) W = working-tree S4/ (copy of the whole tree, read only from the working tree)
sh "$SAFE" "$OUT_ARG" -- sh -c 'rm -rf "$1/trees/W" && mkdir -p "$1/trees/W" && cp -r "$2/S4" "$1/trees/W/S4" && cp "$2/Makefile" "$2/Makefile.common" "$2/Makefile.Linux" "$1/trees/W/"' sh "$OUT" "$REPO" || { echo "export W failed" >&2; exit 1; }

# 3) builds (the Makefile lives at the top of the exported tree; for F2 it comes from git archive).
build_one() {
    TAG=$1; MODE=$2
    if [ "$MODE" = dbg ]; then
        CF="-O0 -g -Wall -fPIC -fcx-limited-range -fno-exceptions"
        CXF="-O0 -g -Wall -fcx-limited-range -fno-exceptions -fPIC"
    else
        CF="-O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC"
        CXF="-O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC"
    fi
    WD="$OUT/${TAG}-${MODE}"
    LOG="$OUT/build-${TAG}-${MODE}.log"
    sh "$SAFE" "$OUT_ARG" -- sh -c 'rm -rf "$1" && cp -r "$2" "$1"' sh "$WD" "$OUT/trees/$TAG" || return 1
    sh "$SAFE" "$OUT_ARG" -- sh -c 'cd "$1" && make objdir > "$2" 2>&1 && make -j"$3" CPPFLAGS="-IS4 -IS4/RNP -IS4/kiss_fft" CFLAGS="$4" CXXFLAGS="$5" build/libS4.a >> "$2" 2>&1; echo "make rc=$?" >> "$2"' sh "$WD" "$LOG" "$JOBS" "$CF" "$CXF"
    echo "warnings: $(grep -c 'warning:' "$LOG")"
    tail -1 "$LOG"
}

for T in F2 W; do
    for M in dbg plain; do
        echo "== build $T $M"
        build_one "$T" "$M"
    done
done
echo "build_s3r4: done"
exit 0
