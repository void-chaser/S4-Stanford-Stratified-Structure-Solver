#!/bin/sh
# build_f3_s3r4.sh -- P05-S3R4 build of the frozen tree F3 from git archive (new file).
#
#   sh testing/d003/safe_run.sh p05-s3r4 -- sh testing/d003/stage_s3r4/build_f3_s3r4.sh p05-s3r4 <F3_COMMIT>
#
# F3 is exported with git archive from the commit given as the second argument (never from the working tree).
# The S4 tree of that commit must equal the value recorded by the caller (checked here before building).
# Output: $EV/build_f3/{dbg,plain}/ (library and log); $EV/build_f3/BUILD_F3.tsv
# Nothing is written to the repository S4/ tree.
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "build_f3: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: build_f3_s3r4.sh p05-s3r4 COMMIT"}
COMMIT=${2:?"usage: build_f3_s3r4.sh p05-s3r4 COMMIT"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
OUT="$EV/build_f3"
TMPDIR="$EV/tmp"
export TMPDIR
JOBS=${JOBS:-$(nproc)}
SAFE="$REPO/testing/d003/safe_run.sh"

TREE=$(git -C "$REPO" rev-parse "$COMMIT:S4") || { echo "build_f3: cannot resolve $COMMIT:S4" >&2; exit 2; }
echo "F3 commit $(git -C "$REPO" rev-parse "$COMMIT") S4 tree $TREE"

sh "$SAFE" "$OUT_ARG" -- sh -c 'rm -rf "$1/src" && mkdir -p "$1/src" && git -C "$2" archive "$3" | tar -x -C "$1/src"' sh "$OUT" "$REPO" "$COMMIT" || { echo "export F3 failed" >&2; exit 1; }

build_one() {
    MODE=$1
    if [ "$MODE" = dbg ]; then
        CF="-O0 -g -Wall -fPIC -fcx-limited-range -fno-exceptions"
        CXF="-O0 -g -Wall -fcx-limited-range -fno-exceptions -fPIC"
    else
        CF="-O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC"
        CXF="-O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC"
    fi
    WD="$OUT/$MODE"
    LOG="$OUT/build-F3-$MODE.log"
    sh "$SAFE" "$OUT_ARG" -- sh -c 'rm -rf "$1" && cp -r "$2" "$1"' sh "$WD" "$OUT/src" || return 1
    sh "$SAFE" "$OUT_ARG" -- sh -c 'cd "$1" && make objdir > "$2" 2>&1 && make -j"$3" CPPFLAGS="-IS4 -IS4/RNP -IS4/kiss_fft" CFLAGS="$4" CXXFLAGS="$5" build/libS4.a >> "$2" 2>&1; echo "make rc=$?" >> "$2"' sh "$WD" "$LOG" "$JOBS" "$CF" "$CXF"
    echo "F3 $MODE warnings: $(grep -c 'warning:' "$LOG") $(tail -1 "$LOG")"
}

build_one dbg
build_one plain
echo "build_f3_s3r4: done"
exit 0
