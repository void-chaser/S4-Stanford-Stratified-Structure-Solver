#!/bin/sh
# D003 fault-injection harness: entry point (P05-S2).
#
#     sh testing/d003/run_d003.sh OUT_DIR [BASE_COMMIT]
#
# OUT_DIR must not exist or must be empty; an existing run is never overwritten.
# BASE_COMMIT defaults to 5b72793051eb705f0e9b2e5398e1a5f0484da0cb (Master).
#
# Steps, all in this one invocation (the sandbox clears /tmp between tool calls):
#   1. export the baseline commit with git archive into OUT_DIR/baseline-src;
#   2. build the baseline library (make) and check the artifact identities;
#   3. compile the consolidated driver and injector against the baseline, and the
#      history reference driver for the byte-identity check;
#   4. run the matrix; each run's raw return code is appended to OUT_DIR/STEPS.txt;
#   5. classify every run with judge_d003.py (raw facts, no hand edits);
#   6. write OUT_DIR/index.txt and OUT_DIR/SHA256SUMS.
#
# It does not read /home/jackal, does not write /tmp (TMPDIR is redirected into
# OUT_DIR), and does not touch S4/, Makefile*, setup.py.  Each step is recorded,
# never rewritten.

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "usage: sh testing/d003/run_d003.sh OUT_DIR [BASE_COMMIT]" >&2
    exit 2
fi
ROOT=$(cd "$(dirname "$0")/../.." && pwd -P)
BASE=${2:-5b72793051eb705f0e9b2e5398e1a5f0484da0cb}
if [ -e "$1" ] && [ -n "$(ls -A "$1" 2>/dev/null)" ]; then
    echo "refusing to reuse non-empty output directory: $1" >&2
    exit 2
fi
if ! OUT=$(mkdir -p "$1" && cd "$1" && pwd -P) || [ -z "$OUT" ]; then
    echo "cannot create output directory: $1" >&2
    exit 2
fi
H="$ROOT/testing/d003"
PY=${PYTHON:-python3}
JOBS=${JOBS:-$(nproc)}
LOG="$OUT/logs"
TMPDIR="$OUT/tmp"
export TMPDIR
PYTHONDONTWRITEBYTECODE=1
export PYTHONDONTWRITEBYTECODE
if ! { mkdir -p "$LOG" "$TMPDIR" "$OUT/bin" "$OUT/runs" && : > "$OUT/STEPS.txt"; }; then
    echo "cannot initialise output directory: $OUT" >&2
    exit 2
fi

# run NAME COMMAND...  : log output, record the raw return code, keep going
run() {
    name=$1; shift
    "$@" > "$LOG/$name.log" 2>&1
    rc=$?
    printf '%s rc=%s\n' "$name" "$rc" >> "$OUT/STEPS.txt"
    return 0
}

# 1. baseline export (git archive: independent of the working tree)
rm -rf "$OUT/baseline-src" && mkdir -p "$OUT/baseline-src"
run export_baseline sh -c "git -C '$ROOT' archive '$BASE' | tar -x -C '$OUT/baseline-src'"
{
    echo "BASE_REQUESTED=$BASE"
    echo "BASE_RESOLVED=$(git -C "$ROOT" rev-parse "$BASE" 2>/dev/null)"
    echo "file_count=$(cd "$OUT/baseline-src" && find . -type f | wc -l)"
} > "$OUT/baseline.txt"

# 2. baseline library and python extension, built only inside OUT_DIR
run build_baseline_lib sh -c "cd '$OUT/baseline-src' && make -j$JOBS build/libS4.a build/S4"
run build_baseline_pyext sh -c "cd '$OUT/baseline-src' && rm -f S4.*.so && $PY setup.py build_ext --inplace"

# 3. driver and injector.  The consolidated sources come from testing/d003 (committed);
#    the history reference is the S1B patched driver (committed, byte-checked below).
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
run build_driver_d003 sh -c "g++ -O1 -Wall -Wextra -Wno-unused-parameter -I '$OUT/baseline-src/S4' -I '$OUT/baseline-src/S4/fmm' '$H/src/driver_d003.cpp' '$H/src/inject_d003.cpp' -o '$OUT/bin/driver-d003' -L '$OUT/baseline-src/build' -lS4 $LIBFLAGS"
run build_driver_s1b_ref sh -c "g++ -O1 -I '$OUT/baseline-src/S4' -I '$OUT/baseline-src/S4/fmm' '$H/src/history/driver.s1b-patched.reference.cpp' '$H/src/inject_d003.cpp' -o '$OUT/bin/driver-s1b-ref' -L '$OUT/baseline-src/build' -lS4 $LIBFLAGS"

# 4. matrix.  The runner writes one log per case into OUT/runs and one record per case.
run matrix "$PY" -I -B "$H/matrix_d003.py" run --bin "$OUT/bin/driver-d003" --ref "$OUT/bin/driver-s1b-ref" --runs "$OUT/runs" --root "$ROOT" --out "$OUT"

# 5. judge the matrix (classification is written next to the runs; compare vs S1B)
run judge "$PY" -I -B "$H/judge_d003.py" selftest
run judge_sensitivity "$PY" -I -B "$H/judge_d003.py" selftest-sensitivity
run classify "$PY" -I -B "$H/matrix_d003.py" classify --runs "$OUT/runs" --out "$OUT"
run sensitivity "$PY" -I -B "$H/matrix_d003.py" sensitivity --bin "$OUT/bin/driver-d003" --runs "$OUT/sens" --out "$OUT"

# 6. digests.  SHA256SUMS covers every file that is FINAL when it is computed.  The
#    records written after it (STEPS.txt, which gains the "digests" line, and
#    DONE.txt) are excluded, so the list can be re-checked with sha256sum -c.  Their
#    content is the step log itself: each line is "<step> rc=<n>" with the raw code.
#    tmp/ holds scratch files and is excluded.
sh -c "cd '$OUT' && find . -type f ! -name SHA256SUMS ! -name STEPS.txt ! -name DONE.txt ! -path './tmp/*' | LC_ALL=C sort | xargs sha256sum > SHA256SUMS" > "$LOG/digests.log" 2>&1
DIG_RC=$?
printf 'digests rc=%s\n' "$DIG_RC" >> "$OUT/STEPS.txt"
echo "D003 harness run complete: $OUT" > "$OUT/DONE.txt"
# Exit status is 0 when the harness ran to completion, whatever the baseline
# results are.  A baseline is EXPECTED to crash or swallow failures; judging those
# results is the job of judge_d003.py and of the reviewer, not of this exit status.
# Read STEPS.txt and index.txt for the outcome.
exit 0
