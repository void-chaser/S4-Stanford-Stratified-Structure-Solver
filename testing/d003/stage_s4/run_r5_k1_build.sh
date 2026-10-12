#!/bin/sh
# run_r5_k1_build.sh -- P05-S4 R5-4 (K1A, K1B): PLAIN (repository default options) libraries of trees B (37a82e8) and
# F (1c11905), and the S3R2 kottke probe kottke_probe_dump.cpp linked against each.  Exported copies under $EV only.
# Nothing is written to the repository S4/ tree.  The probe source is NOT modified (it is compiled from
# testing/d003/stage_s3r2/kottke_probe_dump.cpp, as the S3R2 R2-4c run did).
#
#   sh testing/d003/safe_run.sh p05-s4r5 -- sh testing/d003/stage_s4/run_r5_k1_build.sh p05-s4r5
#
# Output: $EV/k1/trees/{B,F}, $EV/k1/libS4-plain-{B,F}.sha256, $EV/k1/kpd-{B,F} (probe binaries), $EV/k1/STAGES.txt
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "run_r5_k1_build: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: run_r5_k1_build.sh p05-s4r5"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
OUT="$EV/k1"
TMPDIR="$EV/tmp"
export TMPDIR
JOBS=${JOBS:-$(nproc)}
SAFE="$REPO/testing/d003/safe_run.sh"
ST="$OUT/STAGES.txt"

record() {
    sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$4" && printf "%s\t%s\t%s\t%s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$2" "$1" "$3" >> "$4/STAGES.txt"' sh "$1" "$2" "$3" "$OUT"
}
stage_fail() { echo "run_r5_k1_build: $TAG STAGE $1 FAILED: $2" >&2; record "FAILED-$TAG" "$1" "$2"; exit 1; }

build_one() {
    TAG=$1; COMMIT=$2
    sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1/trees/$2" && rm -rf "$1/trees/$2" && mkdir -p "$1/trees/$2" && git -C "$3" archive "$4" | tar -x -C "$1/trees/$2"' sh "$OUT" "$TAG" "$REPO" "$COMMIT" || stage_fail export "archive of $COMMIT failed"
    test -d "$OUT/trees/$TAG/S4" || stage_fail export "S4 directory missing"
    record "DONE-$TAG" export "tree=$TAG commit=$COMMIT"

    sh "$SAFE" "$OUT_ARG" -- sh -c 'cd "$1/trees/$2" && make objdir > "$1/build-plain-$2.log" 2>&1 && make -j"$3" CPPFLAGS="-IS4 -IS4/RNP -IS4/kiss_fft" build/libS4.a >> "$1/build-plain-$2.log" 2>&1' sh "$OUT" "$TAG" "$JOBS" || stage_fail build "make failed (see build-plain-$TAG.log)"
    test -f "$OUT/trees/$TAG/build/libS4.a" || stage_fail build "libS4.a missing"
    sh "$SAFE" "$OUT_ARG" -- sh -c 'sha256sum "$1/trees/$2/build/libS4.a" > "$1/libS4-plain-$2.sha256"' sh "$OUT" "$TAG" || stage_fail build "sha256 failed"
    record "DONE-$TAG" build "plain $TAG"

    # probe: the S3R2 kottke probe (unmodified source), linked against the plain library of this tree
    sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1" && g++ -O1 -Wall -Wextra -Wno-unused-parameter -I "$2/trees/$3/S4" -I "$2/trees/$3/S4/fmm" "$4/testing/d003/stage_s3r2/kottke_probe_dump.cpp" -o "$1/kpd-$3" -L "$2/trees/$3/build" -lS4 -llapack -lblas' sh "$OUT" "$OUT" "$TAG" "$REPO" || stage_fail probe "kpd link failed"
    test -x "$OUT/kpd-$TAG" || stage_fail probe "kpd not executable"
    record "DONE-$TAG" probe "kpd-$TAG"
}

build_one B 37a82e8
build_one F 1c11905
echo "run_r5_k1_build: B and F plain libraries and probes done"
exit 0
