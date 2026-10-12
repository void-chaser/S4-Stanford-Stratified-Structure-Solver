#!/bin/sh
# run_r5_dbg_build.sh -- P05-S4 R5-2: DEBUG build (-O0 -g) of trees B (37a82e8) and F (1c11905), plain library
# and plain driver, for gdb investigation.  Exported copies only, under $EV.  Nothing is written to the repository
# S4/ tree.  Same make invocation and link flags as run_s4r2_build.sh / build_tree_r2.sh, except that CXXFLAGS and
# CFLAGS are overridden with "-O0 -g" (the Makefile uses += so the override is appended after -O3 and wins).
#
#   sh testing/d003/safe_run.sh p05-s4r5 -- sh testing/d003/stage_s4/run_r5_dbg_build.sh p05-s4r5
#
# Output: $EV/dbg/trees/{B,F}, $EV/dbg/build-dbg-{B,F}.log, $EV/dbg/libS4-dbg-{B,F}.sha256,
#         $EV/dbg/drivers/dbg-{B,F}/driver-d003, $EV/dbg/DRIVERS_DBG.tsv, $EV/dbg/STAGES.txt
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "run_r5_dbg_build: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: run_r5_dbg_build.sh p05-s4r5"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
OUT="$EV/dbg"
TMPDIR="$EV/tmp"
export TMPDIR
JOBS=${JOBS:-$(nproc)}
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
SAFE="$REPO/testing/d003/safe_run.sh"
ST="$OUT/STAGES.txt"

record() {
    sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$4" && printf "%s\t%s\t%s\t%s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$2" "$1" "$3" >> "$4/STAGES.txt"' sh "$1" "$2" "$3" "$OUT"
}
stage_fail() { echo "run_r5_dbg_build: $TAG STAGE $1 FAILED: $2" >&2; record "FAILED-$TAG" "$1" "$2"; exit 1; }
stage_done() { record "DONE-$TAG" "$1" "$2"; }

build_one() {
    TAG=$1; COMMIT=$2
    sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1/trees/$2" "$1/drivers" && rm -rf "$1/trees/$2" && mkdir -p "$1/trees/$2" && git -C "$3" archive "$4" | tar -x -C "$1/trees/$2"' sh "$OUT" "$TAG" "$REPO" "$COMMIT" || stage_fail export "archive of $COMMIT failed"
    test -d "$OUT/trees/$TAG/S4" || stage_fail export "S4 directory missing"
    stage_done export "tree=$TAG commit=$COMMIT"

    sh "$SAFE" "$OUT_ARG" -- sh -c 'cd "$1/trees/$2" && make objdir > "$1/build-dbg-$2.log" 2>&1 && make -j"$3" CPPFLAGS="-IS4 -IS4/RNP -IS4/kiss_fft" CFLAGS="-O0 -g -Wall -fPIC -fcx-limited-range -fno-exceptions" CXXFLAGS="-O0 -g -Wall -fcx-limited-range -fno-exceptions -fPIC" build/libS4.a >> "$1/build-dbg-$2.log" 2>&1' sh "$OUT" "$TAG" "$JOBS" || stage_fail build "make failed (see build-dbg-$TAG.log)"
    test -f "$OUT/trees/$TAG/build/libS4.a" || stage_fail build "libS4.a missing"
    sh "$SAFE" "$OUT_ARG" -- sh -c 'sha256sum "$1/trees/$2/build/libS4.a" > "$1/libS4-dbg-$2.sha256"' sh "$OUT" "$TAG" || stage_fail build "sha256 failed"
    stage_done build "dbg $TAG"

    # injector: testing/d003/stage_s4/inject_r4_plan.cpp (the R4 injector with plancall:K:M; the same file that
    # built the R4 plain drivers regress/plain-r4-{B,F}).  inject_d003.cpp does not know plancall:K:M.
    sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1/drivers/dbg-$2" && g++ -O0 -g -Wall -Wextra -Wno-unused-parameter -I "$3/S4" -I "$3/S4/fmm" "$4/testing/d003/src/driver_d003.cpp" "$4/testing/d003/stage_s4/inject_r4_plan.cpp" -o "$1/drivers/dbg-$2/driver-d003" -L "$3/build" -lS4 '"$LIBFLAGS" sh "$OUT" "$TAG" "$OUT/trees/$TAG" "$REPO" || stage_fail driver "link failed"
    test -x "$OUT/drivers/dbg-$TAG/driver-d003" || stage_fail driver "driver not executable"
    DSHA=$(sha256sum "$OUT/drivers/dbg-$TAG/driver-d003" | cut -d' ' -f1)
    sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\n" "dbg-$2" "$1" "$3/drivers/dbg-$2/driver-d003" >> "$3/DRIVERS_DBG.tsv"' sh "$DSHA" "$TAG" "$OUT" || stage_fail driver "could not record driver"
    stage_done driver "dbg-$TAG sha256=$DSHA"
}

build_one B 37a82e8
build_one F 1c11905
echo "run_r5_dbg_build: B and F debug builds done"
exit 0
