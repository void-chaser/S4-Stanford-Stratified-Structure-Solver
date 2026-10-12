#!/bin/sh
# run_s4r2_build.sh -- P05-S4 R2 build step for tree F (1c11905).  Adds nothing to run_all.sh.
#
#   sh testing/d003/safe_run.sh p05-s4r2/run1 -- sh testing/d003/stage_s4/run_s4r2_build.sh p05-s4r2/run1
#
# Stages (each one records DONE or FAILED in OUT/STAGES.txt):
#   export   git archive 1c11905 S4 (+ the build files) into OUT/trees/F; testing/ is HEAD's testing/
#   build    plain library OUT/trees/F/build/libS4.a with the repository default options
#            (the same make invocation as run_all.sh build_lib); sha256 recorded
#   driver   the driver and injector of testing/d003/src linked against the plain F library with the
#            link flags of run_all.sh (LIBFLAGS); sha256 recorded in OUT/drivers/DRIVERS.tsv
# Every write goes through safe_run.sh (the caller invokes this script that way).  Nothing is written
# outside OUT, and S4/ of the repository is never written.
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "run_s4r2_build: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: run_s4r2_build.sh OUT_ARG (relative to checkpoints/p05/evidence)"}
OUT="$REPO/checkpoints/p05/evidence/$OUT_ARG"
TMPDIR="$OUT/tmp"
export TMPDIR
JOBS=${JOBS:-$(nproc)}
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
SAFE="$REPO/testing/d003/safe_run.sh"

# record STATUS STAGE REASON: one line in OUT/STAGES.txt, written through safe_run.sh
record() {
    sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\t%s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$2" "$1" "$3" >> "$4/STAGES.txt"' sh "$1" "$2" "$3" "$OUT"
}
stage_fail() { echo "run_s4r2_build: STAGE $1 FAILED: $2" >&2; record FAILED "$1" "$2"; exit 1; }
stage_done() { record DONE "$1" "$2"; }

# export: the tree F = git archive of 1c11905; testing/ from HEAD (the harness is not re-exported)
sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1/trees/F" "$1/tmp" && rm -rf "$1/trees/F" && mkdir -p "$1/trees/F" && git -C "$2" archive 1c11905 | tar -x -C "$1/trees/F"' sh "$OUT" "$REPO" || stage_fail export "archive of 1c11905 failed"
test -d "$OUT/trees/F/S4" || stage_fail export "S4 directory missing after export"
stage_done export "tree=F commit=1c11905"

# build: plain library, same make invocation as run_all.sh build_lib (repository defaults)
sh "$SAFE" "$OUT_ARG" -- sh -c 'cd "$1/trees/F" && make objdir > "$2/build-plain-F.log" 2>&1 && make -j"$3" CPPFLAGS="-IS4 -IS4/RNP -IS4/kiss_fft" build/libS4.a >> "$2/build-plain-F.log" 2>&1' sh "$OUT" "$OUT" "$JOBS" || stage_fail build "make of libS4.a failed (see $OUT/build-plain-F.log)"
test -f "$OUT/trees/F/build/libS4.a" || stage_fail build "libS4.a missing"
sh "$SAFE" "$OUT_ARG" -- sh -c 'sha256sum "$1/trees/F/build/libS4.a" > "$1/libS4-plain-F.sha256"' sh "$OUT" || stage_fail build "sha256 of libS4.a failed"
stage_done build "plain F"

# driver: link the committed driver and injector against the plain F library
sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1/drivers/plain-F" && g++ -O1 -Wall -Wextra -Wno-unused-parameter -I "$2/trees/F/S4" -I "$2/trees/F/S4/fmm" "$3/testing/d003/src/driver_d003.cpp" "$3/testing/d003/src/inject_d003.cpp" -o "$1/drivers/plain-F/driver-d003" -L "$2/trees/F/build" -lS4 '"$LIBFLAGS" sh "$OUT" "$OUT" "$REPO" || stage_fail driver "link of driver failed"
test -x "$OUT/drivers/plain-F/driver-d003" || stage_fail driver "driver not executable"
DSHA=$(sha256sum "$OUT/drivers/plain-F/driver-d003" | cut -d' ' -f1)
sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\n" "plain-F" "$1" "$2/drivers/plain-F/driver-d003" >> "$2/drivers/DRIVERS.tsv"' sh "$DSHA" "$OUT" || stage_fail driver "could not record driver sha"
stage_done driver "plain-F sha256=$DSHA"
echo "run_s4r2_build: export, build, driver done for F"
exit 0
