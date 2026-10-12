#!/bin/sh
# build_tree_r2.sh -- P05-S4 R2: export, plain build and plain driver for one tree (B, A, H or F).
# Same steps and make invocation as run_all.sh (build_lib, driver_for) and run_s4r2_build.sh.  Nothing
# in run_all.sh, matrix_r2.py or any other historical file is changed.
#
#   sh testing/d003/safe_run.sh p05-s4r2 -- sh testing/d003/stage_s4/build_tree_r2.sh p05-s4r2 TAG COMMIT
#
# TAG is a single letter (B, A, H or F); COMMIT is the commit of that tree.  Output: OUT/trees/TAG,
# OUT/build-plain-TAG.log, OUT/libS4-plain-TAG.sha256, OUT/drivers/plain-TAG/driver-d003,
# OUT/drivers/DRIVERS.tsv (one line per driver), OUT/STAGES.txt (DONE or FAILED per stage).
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "build_tree_r2: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: build_tree_r2.sh OUT_ARG TAG COMMIT"}
TAG=${2:?"TAG required"}
COMMIT=${3:?"COMMIT required"}
case "$TAG" in B|A|H|F) ;; *) echo "build_tree_r2: TAG must be B, A, H or F" >&2; exit 2;; esac
OUT="$REPO/checkpoints/p05/evidence/$OUT_ARG"
TMPDIR="$OUT/tmp"
export TMPDIR
JOBS=${JOBS:-$(nproc)}
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
SAFE="$REPO/testing/d003/safe_run.sh"
ST="$OUT/STAGES.txt"

record() {
    sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\t%s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$2" "$1" "$3" >> "$4"' sh "$1" "$2" "$3" "$ST"
}
stage_fail() { echo "build_tree_r2: $TAG STAGE $1 FAILED: $2" >&2; record "FAILED-$TAG" "$1" "$2"; exit 1; }
stage_done() { record "DONE-$TAG" "$1" "$2"; }

sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1/trees/$2" "$1/tmp" "$1/drivers" && rm -rf "$1/trees/$2" && mkdir -p "$1/trees/$2" && git -C "$3" archive "$4" | tar -x -C "$1/trees/$2"' sh "$OUT" "$TAG" "$REPO" "$COMMIT" || stage_fail export "archive of $COMMIT failed"
test -d "$OUT/trees/$TAG/S4" || stage_fail export "S4 directory missing"
if [ "$TAG" = "H" ]; then
    # H's testing/ is HEAD's testing/ (as in run_all.sh export_tree)
    sh "$SAFE" "$OUT_ARG" -- sh -c 'rm -rf "$1/trees/H/testing" && mkdir -p "$1/trees/H/testing" && git -C "$2" archive HEAD testing | tar -x -C "$1/trees/H"' sh "$OUT" "$REPO" || stage_fail export "testing/ for H failed"
fi
stage_done export "tree=$TAG commit=$COMMIT"

sh "$SAFE" "$OUT_ARG" -- sh -c 'cd "$1/trees/$2" && make objdir > "$1/build-plain-$2.log" 2>&1 && make -j"$3" CPPFLAGS="-IS4 -IS4/RNP -IS4/kiss_fft" build/libS4.a >> "$1/build-plain-$2.log" 2>&1' sh "$OUT" "$TAG" "$JOBS" || stage_fail build "make failed (see build-plain-$TAG.log)"
test -f "$OUT/trees/$TAG/build/libS4.a" || stage_fail build "libS4.a missing"
sh "$SAFE" "$OUT_ARG" -- sh -c 'sha256sum "$1/trees/$2/build/libS4.a" > "$1/libS4-plain-$2.sha256"' sh "$OUT" "$TAG" || stage_fail build "sha256 failed"
stage_done build "plain $TAG"

sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1/drivers/plain-$2" && g++ -O1 -Wall -Wextra -Wno-unused-parameter -I "$3/S4" -I "$3/S4/fmm" "$4/testing/d003/src/driver_d003.cpp" "$4/testing/d003/src/inject_d003.cpp" -o "$1/drivers/plain-$2/driver-d003" -L "$3/build" -lS4 '"$LIBFLAGS" sh "$OUT" "$TAG" "$OUT/trees/$TAG" "$REPO" || stage_fail driver "link failed"
test -x "$OUT/drivers/plain-$TAG/driver-d003" || stage_fail driver "driver not executable"
DSHA=$(sha256sum "$OUT/drivers/plain-$TAG/driver-d003" | cut -d' ' -f1)
sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\n" "plain-$2" "$1" "$3/drivers/plain-$2/driver-d003" >> "$3/drivers/DRIVERS.tsv"' sh "$DSHA" "$TAG" "$OUT" || stage_fail driver "could not record driver"
stage_done driver "plain-$TAG sha256=$DSHA"
echo "build_tree_r2: $TAG done"
exit 0
