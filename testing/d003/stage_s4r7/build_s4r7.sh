#!/bin/sh
# build_s4r7.sh -- P05-S4 R7-1 builds (new file; command layout copied from testing/d003/stage_s3r3/build_s3r3.sh).
#
#   sh testing/d003/safe_run.sh p05-s4r7 -- sh testing/d003/stage_s4r7/build_s4r7.sh p05-s4r7
#
# Source: the exported trees $EV/trees/F (1c11905) and $EV/trees/F2 (a07b5ac), made by git archive (never from the
# working tree).  Each tree is copied to a private build directory per mode, so the objdir of one build cannot be
# reused by another.  Two modes per tree:
#   dbg   : -O0 -g                 (as run_r5_dbg_build.sh and run_s3r3 build_s3r3.sh)
#   plain : -O3 -march=native      (the Makefile default, as in R4 build-plain-*.log)
# No -DHAVE_LIBCHOLMOD is passed (the build config does not define it; see PRE_FIX_SOURCE_S3R3.md section 2).
# Output: $EV/build_r7/<TAG>-<MODE>/  (library, build log), $EV/build_r7/BUILD_R7.tsv (tree, mode, warnings, make rc, sha256)
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "build_s4r7: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: build_s4r7.sh p05-s4r7"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
OUT="$EV/build_r7"
TMPDIR="$EV/tmp"
export TMPDIR
JOBS=${JOBS:-$(nproc)}
SAFE="$REPO/testing/d003/safe_run.sh"

sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1" && : > "$1/BUILD_R7.tsv"' sh "$OUT" || exit 2

build_one() {
    TAG=$1; MODE=$2
    if [ "$MODE" = dbg ]; then
        CF="-O0 -g -Wall -fPIC -fcx-limited-range -fno-exceptions"
        CXF="-O0 -g -Wall -fcx-limited-range -fno-exceptions -fPIC"
    else
        CF="-O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC"
        CXF="-O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC"
    fi
    WD="$OUT/$TAG-$MODE"
    LOG="$OUT/build-$TAG-$MODE.log"
    sh "$SAFE" "$OUT_ARG" -- sh -c 'rm -rf "$1" && mkdir -p "$1" && cp -r "$2/." "$1/"' sh "$WD" "$EV/trees/$TAG" || return 1
    sh "$SAFE" "$OUT_ARG" -- sh -c 'cd "$1" && make objdir > "$2" 2>&1 && make -j"$3" CPPFLAGS="-IS4 -IS4/RNP -IS4/kiss_fft" CFLAGS="$4" CXXFLAGS="$5" build/libS4.a >> "$2" 2>&1; echo "make rc=$?" >> "$2"' sh "$WD" "$LOG" "$JOBS" "$CF" "$CXF"
    W=$(grep -c 'warning:' "$LOG")
    RC=$(sed -n 's/^make rc=//p' "$LOG" | tail -1)
    SHA=$(sha256sum "$WD/build/libS4.a" 2>/dev/null | cut -d' ' -f1)
    CHOL=$(grep -c 'HAVE_LIBCHOLMOD' "$LOG")
    sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\t%s\t%s\t%s\n" "$1" "$2" "$3" "$4" "$5" "$6" >> "$7/BUILD_R7.tsv"' sh "$TAG" "$MODE" "$W" "$RC" "$SHA" "$CHOL" "$OUT" || return 1
    echo "$TAG $MODE warnings=$W make_rc=$RC cholmod_mentions=$CHOL lib_sha256=$SHA"
}

for T in F F2; do
    for M in dbg plain; do
        build_one "$T" "$M"
    done
done
echo "build_s4r7: done"
exit 0
