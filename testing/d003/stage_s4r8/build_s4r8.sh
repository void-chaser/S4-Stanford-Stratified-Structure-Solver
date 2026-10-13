#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# build_s4r8.sh -- P05-S4 R8 M0 step 3.2: F3 libraries, dbg and plain (copied from build_s4r7.sh; new file).
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/build_s4r8.sh p05-s4r8
# Changes against build_s4r7.sh (RUNNER_DIFF_R8_M0.txt): the first line is the standard header (U-brief section 0.2);
# only the tree F3 is built; the forced removal of a build directory is replaced by test ! -e (U17); the tree label, the output
# directory and the expected warning counts (dbg 62, plain 71) are the R8 values.  Compile flags are unchanged.
# Source: $EV/trees/F3 (git archive of 8d8202a, exported by export_r8.sh).  No -DHAVE_LIBCHOLMOD is passed.
# Output: $EV/build_r8/F3-<MODE>/ (library, build log), $EV/build_r8/BUILD_R8.tsv (tree, mode, warnings, make rc, lib sha256, cholmod mentions).
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "build_s4r8: first argument must be p05-s4r8" >&2; exit 2; }
OUT="$EV/build_r8"
JOBS=${JOBS:-$(nproc)}
SAFE="$REPO/testing/d003/safe_run.sh"
test -d "$EV/trees/F3" || { echo "build_s4r8: REFUSED: source tree missing: $EV/trees/F3" >&2; exit 2; }
test ! -e "$OUT" || { echo "build_s4r8: REFUSED exists: $OUT" >&2; exit 2; }
mkdir -p "$OUT" || exit 2
: > "$OUT/BUILD_R8.tsv"

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
    sh "$SAFE" p05-s4r8 -- sh -c 'test ! -e "$1" && mkdir -p "$1" && cp -r "$2/." "$1/"' sh "$WD" "$EV/trees/$TAG" || return 1
    sh "$SAFE" p05-s4r8 -- sh -c 'cd "$1" && make objdir > "$2" 2>&1 && make -j"$3" CPPFLAGS="-IS4 -IS4/RNP -IS4/kiss_fft" CFLAGS="$4" CXXFLAGS="$5" build/libS4.a >> "$2" 2>&1; echo "make rc=$?" >> "$2"' sh "$WD" "$LOG" "$JOBS" "$CF" "$CXF"
    W=$(grep -c 'warning:' "$LOG")
    RC=$(sed -n 's/^make rc=//p' "$LOG" | tail -n 1)
    SHA=$(sha256sum "$WD/build/libS4.a" 2>&1 | cut -d' ' -f1)
    CHOL=$(grep -c 'HAVE_LIBCHOLMOD' "$LOG")
    sh "$SAFE" p05-s4r8 -- sh -c 'printf "%s\t%s\t%s\t%s\t%s\t%s\n" "$1" "$2" "$3" "$4" "$5" "$6" >> "$7/BUILD_R8.tsv"' sh "$TAG" "$MODE" "$W" "$RC" "$SHA" "$CHOL" "$OUT" || return 1
    echo "$TAG $MODE warnings=$W make_rc=$RC cholmod_mentions=$CHOL lib_sha256=$SHA"
}

build_one F3 dbg
build_one F3 plain
echo "build_s4r8: done"
exit 0
