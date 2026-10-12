#!/bin/sh
# run_r6c_seam_dbg_build.sh -- P05-S4 R6c-2: DEBUG (-O0 -g) rebuild of the two F seam libraries that the 25 R4 seam points use
# (seamF: 15 points; fmmret-F: 10 points).  BUILD ONLY: no injection, no matrix run.
#
#   sh testing/d003/safe_run.sh p05-s4r6c -- sh testing/d003/stage_s4/run_r6c_seam_dbg_build.sh p05-s4r6c
#
# Sources: COPIES (cp -a) of the R4 seam export trees checkpoints/p05/evidence/p05-s4r4/seam/F-seamF and F-fmmret, made
# into $EV/seam_dbg/<name>/.  The R4 trees and their R4 libraries are NOT modified.  Before the copy, every source file of
# the two trees is compared with the R4 manifest (SHA256SUMS.txt) by testing/d003/stage_s4/r6c_seam_src_verify.py (run first;
# its output SEAM_SRC_VERIFY_R6c.tsv must show manifest bad=0 and diff_vs_F equal).
#
# Flags: the same macros as R4 (run_r4_seam.sh: seamF = LINEARSOLVE_SEAM + LINEARSOLVE_SEAM_NULLINFO2 + ALLOC_SEAM +
# KOTTKE_SEAM; fmmret-F = FMMRET_SEAM); the same CPPFLAGS and LIBFLAGS; CFLAGS and CXXFLAGS overridden to "-O0 -g" as in
# run_r5_dbg_build.sh.  Driver: testing/d003/src/driver_d003.cpp + testing/d003/src/inject_d003.cpp (the injector that
# understands linearsolve:, linearsolve_null2:, alloc:, kottke_alloc:, fmmret: requests, as in R4 link_driver).
#
# Outputs: $EV/seam_dbg/<name>/build/libS4.a, $EV/seam_dbg/libS4-dbg-<name>.sha256, $EV/seam_dbg/drivers/<name>/driver-d003,
#          $EV/seam_dbg/DRIVERS_DBG_SEAM.tsv, $EV/seam_dbg/STAGES.txt, $EV/seam_dbg/build-<name>.log
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "run_r6c_seam_dbg_build: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: run_r6c_seam_dbg_build.sh p05-s4r6c"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
OUT="$EV/seam_dbg"
TMPDIR="$EV/tmp"
export TMPDIR
JOBS=${JOBS:-$(nproc)}
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
SAFE="$REPO/testing/d003/safe_run.sh"
R4SEAM="$REPO/checkpoints/p05/evidence/p05-s4r4/seam"
ST="$OUT/STAGES.txt"

record() {
    sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$4" && printf "%s\t%s\t%s\t%s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$2" "$1" "$3" >> "$4/STAGES.txt"' sh "$1" "$2" "$3" "$OUT"
}
stage_fail() { echo "run_r6c_seam_dbg_build: $TAG STAGE $1 FAILED: $2" >&2; record "FAILED-$TAG" "$1" "$2"; exit 1; }
stage_done() { record "DONE-$TAG" "$1" "$2"; }

# build_one NAME SRC_TREE MACROS
build_one() {
    TAG=$1; SRC=$2; MACROS=$3
    # The copy EXCLUDES build/, *.o and *.a: the R4 trees contain -O3 objects and a build/ directory whose timestamps
    # would make make reuse them (the -O0 -g build would silently not happen).  Only sources are copied.
    sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1/$2" && rm -rf "$1/$2/src" && mkdir -p "$1/$2/src" && tar -C "$3" --exclude=./build --exclude="*.o" --exclude="*.a" -cf - . | tar -C "$1/$2/src" -xf -' sh "$OUT" "$TAG" "$SRC" || stage_fail copy "source copy of $SRC failed"
    test -d "$OUT/$TAG/src/S4" || stage_fail copy "S4 directory missing in copy"
    stage_done copy "tree=$TAG from=$SRC"

    sh "$SAFE" "$OUT_ARG" -- sh -c 'cd "$1/$2/src" && make objdir > "$1/build-$2.log" 2>&1 && make -j"$3" CPPFLAGS="$4 -IS4 -IS4/RNP -IS4/kiss_fft" CFLAGS="-O0 -g -Wall -fPIC -fcx-limited-range -fno-exceptions" CXXFLAGS="-O0 -g -Wall -fcx-limited-range -fno-exceptions -fPIC" build/libS4.a >> "$1/build-$2.log" 2>&1' sh "$OUT" "$TAG" "$JOBS" "$MACROS" || stage_fail build "make failed (see build-$TAG.log)"
    test -f "$OUT/$TAG/src/build/libS4.a" || stage_fail build "libS4.a missing"
    sh "$SAFE" "$OUT_ARG" -- sh -c 'sha256sum "$1/$2/src/build/libS4.a" > "$1/libS4-dbg-$2.sha256"' sh "$OUT" "$TAG" || stage_fail build "sha256 failed"
    stage_done build "dbg $TAG"

    sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1/drivers/$2" && g++ -O0 -g -Wall -Wextra -Wno-unused-parameter -I "$3/S4" -I "$3/S4/fmm" "$4/testing/d003/src/driver_d003.cpp" "$4/testing/d003/src/inject_d003.cpp" -o "$1/drivers/$2/driver-d003" -L "$3/build" -lS4 '"$LIBFLAGS" sh "$OUT" "$TAG" "$OUT/$TAG/src" "$REPO" || stage_fail driver "link failed"
    test -x "$OUT/drivers/$TAG/driver-d003" || stage_fail driver "driver not executable"
    DSHA=$(sha256sum "$OUT/drivers/$TAG/driver-d003" | cut -d' ' -f1)
    sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\n" "$2" "$1" "$3/drivers/$2/driver-d003" >> "$3/DRIVERS_DBG_SEAM.tsv"' sh "$DSHA" "$TAG" "$OUT" || stage_fail driver "could not record driver"
    stage_done driver "dbg-$TAG sha256=$DSHA"
}

# the source trees are the R4 seam trees (their manifest was verified by r6c_seam_src_verify.py before this script runs)
sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1" && : > "$1/STAGES.txt"' sh "$OUT" || { echo "cannot prepare $OUT" >&2; exit 2; }
build_one seamF "$R4SEAM/F-seamF" "-DS4_TEST_LINEARSOLVE_SEAM -DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2 -DS4_TEST_ALLOC_SEAM -DS4_TEST_KOTTKE_SEAM"
build_one fmmret-F "$R4SEAM/F-fmmret" "-DS4_TEST_FMMRET_SEAM"
echo "run_r6c_seam_dbg_build: seamF and fmmret-F debug builds done"
exit 0
