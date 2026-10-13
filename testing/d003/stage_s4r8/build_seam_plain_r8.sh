#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# build_seam_plain_r8.sh -- P05-S4 R8 M0 step 3.3: PLAIN seam libraries for F3 (copied from build_seam_plain_s4r7.sh; new file).
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/build_seam_plain_r8.sh p05-s4r8
# Only seamF-F3-plain and fmmret-F3-plain are built (brief 3.3).  Macros and flags are those of R7 (BUILD_SEAM_PLAIN_R7.tsv):
#   CFLAGS = CXXFLAGS = -O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC
# Sources: $EV/seam_r8/F3-seamF and $EV/seam_r8/F3-fmmret (exported and patched by seam_r8.sh).  Each is copied without
# build/, *.o, *.a into a new private directory before the build.
# Changes against build_seam_plain_s4r7.sh (RUNNER_DIFF_R8_M0.txt): standard first line; the R7 tags F and F2 become F3 only;
# forced removal replaced by test ! -e (U17); output directory $EV/build_r8/seam_plain.
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "build_seam_plain_r8: first argument must be p05-s4r8" >&2; exit 2; }
SAFE="$REPO/testing/d003/safe_run.sh"
JOBS=${JOBS:-$(nproc)}
CF="-O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC"
OUT="$EV/build_r8/seam_plain"
test -d "$EV/seam_r8/F3-seamF" && test -d "$EV/seam_r8/F3-fmmret" || { echo "build_seam_plain_r8: REFUSED: seam sources missing" >&2; exit 2; }
test ! -e "$OUT" || { echo "build_seam_plain_r8: REFUSED exists: $OUT" >&2; exit 2; }
mkdir -p "$OUT" || exit 2
: > "$OUT/BUILD_SEAM_PLAIN_R8_RESULT.tsv"

build_seam() {
    TAG=$1; SRC=$2; MACROS=$3
    WD="$OUT/$TAG"
    LOG="$OUT/build-$TAG.log"
    sh "$SAFE" p05-s4r8 -- sh -c 'test ! -e "$1" && mkdir -p "$1" && tar -C "$2" --exclude=./build --exclude="*.o" --exclude="*.a" -cf - . | tar -C "$1" -xf -' sh "$WD" "$SRC" || return 1
    sh "$SAFE" p05-s4r8 -- sh -c 'cd "$1" && make objdir > "$2" 2>&1 && make -j"$3" CPPFLAGS="$6 -IS4 -IS4/RNP -IS4/kiss_fft" CFLAGS="$4" CXXFLAGS="$5" build/libS4.a >> "$2" 2>&1; echo "make rc=$?" >> "$2"' sh "$WD" "$LOG" "$JOBS" "$CF" "$CF" "$MACROS" || return 1
    W=$(grep -c 'warning:' "$LOG")
    RC=$(sed -n 's/^make rc=//p' "$LOG" | tail -n 1)
    SHA=$(sha256sum "$WD/build/libS4.a" 2>&1 | cut -d' ' -f1)
    sh "$SAFE" p05-s4r8 -- sh -c 'printf "%s\t%s\t%s\t%s\n" "$1" "$2" "$3" "$4" >> "$5/BUILD_SEAM_PLAIN_R8_RESULT.tsv"' sh "$TAG" "$W" "$RC" "$SHA" "$OUT" || return 1
    echo "$TAG warnings=$W make_rc=$RC lib_sha256=$SHA"
}

build_seam seamF-F3-plain  "$EV/seam_r8/F3-seamF"  "-DS4_TEST_LINEARSOLVE_SEAM -DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2 -DS4_TEST_ALLOC_SEAM -DS4_TEST_KOTTKE_SEAM"
build_seam fmmret-F3-plain "$EV/seam_r8/F3-fmmret" "-DS4_TEST_FMMRET_SEAM"
echo "build_seam_plain_r8: done"
exit 0
