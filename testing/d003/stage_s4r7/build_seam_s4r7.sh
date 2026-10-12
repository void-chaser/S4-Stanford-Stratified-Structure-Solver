#!/bin/sh
# build_seam_s4r7.sh -- P05-S4 R7-1 step 3: seam libraries seamF-F2 and fmmret-F2, -O0 -g (new file).
#
#   sh testing/d003/safe_run.sh p05-s4r7 -- sh testing/d003/stage_s4r7/build_seam_s4r7.sh p05-s4r7
#
# Sources: the seam trees $EV/seam_r7/F-seamF, F2-seamF, F-fmmret, F2-fmmret (created by git archive of 1c11905 / a07b5ac and
# the R4/R5 seam apply scripts; see SEAM_DIFF_F_vs_F2_R7.txt).  Each is copied (sources only, no build/, *.o, *.a) to a
# private build directory.  Macros and flags follow run_r6c_seam_dbg_build.sh:
#   seamF    : -DS4_TEST_LINEARSOLVE_SEAM -DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2 -DS4_TEST_ALLOC_SEAM -DS4_TEST_KOTTKE_SEAM
#   fmmret   : -DS4_TEST_FMMRET_SEAM
#   CFLAGS / CXXFLAGS "-O0 -g ..." as in the dbg build.
# Output: $EV/build_r7/seam/<TAG>/ and $EV/build_r7/seam/BUILD_SEAM_R7.tsv
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "build_seam_s4r7: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: build_seam_s4r7.sh p05-s4r7"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
OUT="$EV/build_r7/seam"
TMPDIR="$EV/tmp"
export TMPDIR
JOBS=${JOBS:-$(nproc)}
SAFE="$REPO/testing/d003/safe_run.sh"

sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1" && : > "$1/BUILD_SEAM_R7.tsv"' sh "$OUT" || exit 2

build_seam() {
    TAG=$1; SRC=$2; MACROS=$3
    CF="-O0 -g -Wall -fPIC -fcx-limited-range -fno-exceptions"
    CXF="-O0 -g -Wall -fcx-limited-range -fno-exceptions -fPIC"
    WD="$OUT/$TAG"
    LOG="$OUT/build-$TAG.log"
    # sources only: exclude build/, objects and archives so that no -O3 artifact of the copy is reused
    sh "$SAFE" "$OUT_ARG" -- sh -c 'rm -rf "$1" && mkdir -p "$1" && tar -C "$2" --exclude=./build --exclude="*.o" --exclude="*.a" -cf - . | tar -C "$1" -xf -' sh "$WD" "$SRC" || return 1
    sh "$SAFE" "$OUT_ARG" -- sh -c 'cd "$1" && make objdir > "$2" 2>&1 && make -j"$3" CPPFLAGS="$6 -IS4 -IS4/RNP -IS4/kiss_fft" CFLAGS="$4" CXXFLAGS="$5" build/libS4.a >> "$2" 2>&1; echo "make rc=$?" >> "$2"' sh "$WD" "$LOG" "$JOBS" "$CF" "$CXF" "$MACROS"
    W=$(grep -c 'warning:' "$LOG")
    RC=$(sed -n 's/^make rc=//p' "$LOG" | tail -1)
    SHA=$(sha256sum "$WD/build/libS4.a" 2>/dev/null | cut -d' ' -f1)
    sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\t%s\n" "$1" "$2" "$3" "$4" >> "$5/BUILD_SEAM_R7.tsv"' sh "$TAG" "$W" "$RC" "$SHA" "$OUT" || return 1
    echo "$TAG warnings=$W make_rc=$RC lib_sha256=$SHA"
}

build_seam seamF-F  "$EV/seam_r7/F-seamF"  "-DS4_TEST_LINEARSOLVE_SEAM -DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2 -DS4_TEST_ALLOC_SEAM -DS4_TEST_KOTTKE_SEAM"
build_seam seamF-F2 "$EV/seam_r7/F2-seamF" "-DS4_TEST_LINEARSOLVE_SEAM -DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2 -DS4_TEST_ALLOC_SEAM -DS4_TEST_KOTTKE_SEAM"
build_seam fmmret-F  "$EV/seam_r7/F-fmmret"  "-DS4_TEST_FMMRET_SEAM"
build_seam fmmret-F2 "$EV/seam_r7/F2-fmmret" "-DS4_TEST_FMMRET_SEAM"
echo "build_seam_s4r7: done"
exit 0
