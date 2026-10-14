#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# build_seam_r8m1.sh -- P05-S4 R8 M1a, section 5.2: F3 seam debug libraries seamF-F3 and fmmret-F3 (-O0 -g).  New file.
# Copy of testing/d003/stage_s4r7/build_seam_s4r7.sh (committed, not modified).  Changes against the original:
#   (1) the standard first line (brief section 0.2) replaces the R7 first line;
#   (2) the source trees are the M0 seam trees $EV/seam_r8/F3-seamF and $EV/seam_r8/F3-fmmret (read only; brief section 5.2:
#       not applied again);
#   (3) the output directory is $EV/build_r8m1/seam_dbg/ and the tags are F3 (not F, F2);
#   (4) the recursive removal of the private build directory (R7 form) becomes a test for absence (U17): an existing directory is refused, never removed.
#   Macros and flags are those of the R7 seam debug build (seamF: four S4_TEST_* macros; fmmret: S4_TEST_FMMRET_SEAM).
#
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/build_seam_r8m1.sh p05-s4r8
#
# Output: $EV/build_r8m1/seam_dbg/<TAG>/ (library, build log) and $EV/build_r8m1/seam_dbg/BUILD_SEAM_DBG_R8_M1a.tsv
set -u
OUT_ARG=${1:?"usage: build_seam_r8m1.sh p05-s4r8"}
[ "$OUT_ARG" = p05-s4r8 ] || { echo "build_seam_r8m1: first argument must be p05-s4r8" >&2; exit 2; }
OUT="$EV/build_r8m1/seam_dbg"
JOBS=${JOBS:-$(nproc)}
SAFE="$REPO/testing/d003/safe_run.sh"
SRCSEAM="$EV/seam_r8"

# every input must exist before the output directory is created (brief 0.2)
test -d "$SRCSEAM/F3-seamF/S4" || { echo "missing seam source F3-seamF" >&2; exit 2; }
test -d "$SRCSEAM/F3-fmmret/S4" || { echo "missing seam source F3-fmmret" >&2; exit 2; }
test ! -e "$OUT" || { echo "REFUSED: exists (U17): $OUT" >&2; exit 2; }

sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1" && : > "$1/BUILD_SEAM_DBG_R8_M1a.tsv"' sh "$OUT" || exit 2

build_seam() {
    TAG=$1; SRC=$2; MACROS=$3
    CF="-O0 -g -Wall -fPIC -fcx-limited-range -fno-exceptions"
    CXF="-O0 -g -Wall -fcx-limited-range -fno-exceptions -fPIC"
    WD="$OUT/$TAG"
    LOG="$OUT/build-$TAG.log"
    # sources only: exclude build/, objects and archives so that no artifact of the source tree is reused
    sh "$SAFE" "$OUT_ARG" -- sh -c 'test ! -e "$1" && mkdir -p "$1" && tar -C "$2" --exclude=./build --exclude="*.o" --exclude="*.a" -cf - . | tar -C "$1" -xf -' sh "$WD" "$SRC" || return 1
    sh "$SAFE" "$OUT_ARG" -- sh -c 'cd "$1" && make objdir > "$2" 2>&1 && make -j"$3" CPPFLAGS="$6 -IS4 -IS4/RNP -IS4/kiss_fft" CFLAGS="$4" CXXFLAGS="$5" build/libS4.a >> "$2" 2>&1; echo "make rc=$?" >> "$2"' sh "$WD" "$LOG" "$JOBS" "$CF" "$CXF" "$MACROS"
    W=$(grep -c 'warning:' "$LOG")
    RC=$(sed -n 's/^make rc=//p' "$LOG" | tail -n 1)
    SHA=$(sha256sum "$WD/build/libS4.a" 2>&1 | cut -d' ' -f1)
    sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\t%s\n" "$1" "$2" "$3" "$4" >> "$5/BUILD_SEAM_DBG_R8_M1a.tsv"' sh "$TAG" "$W" "$RC" "$SHA" "$OUT" || return 1
    echo "$TAG warnings=$W make_rc=$RC lib_sha256=$SHA"
}

build_seam seamF-F3  "$SRCSEAM/F3-seamF"  "-DS4_TEST_LINEARSOLVE_SEAM -DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2 -DS4_TEST_ALLOC_SEAM -DS4_TEST_KOTTKE_SEAM"
build_seam fmmret-F3 "$SRCSEAM/F3-fmmret" "-DS4_TEST_FMMRET_SEAM"
echo "build_seam_r8m1: done"
exit 0
