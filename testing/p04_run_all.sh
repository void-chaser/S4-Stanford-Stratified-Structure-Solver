#!/bin/sh
# P04 D001/D002 verification pipeline.  Run from any checkout of the product branch:
#
#     sh testing/p04_run_all.sh OUT_DIR
#
# OUT_DIR must not exist or must be empty; an existing run is never overwritten.
#
# It exports the baseline commit 963ccf1 into OUT_DIR/baseline-src, builds the
# candidate (this tree) and the baseline, builds a TEST-ONLY seam library of the
# candidate, and runs every check.  Each step's raw return code is appended to
# OUT_DIR/STEPS.txt and is never rewritten.  The last step, testing/p04_aggregate.py,
# reads STEPS.txt and each step's judgement file, classifies every step as ok,
# expected_defect (a baseline that reproduces the registered defect) or unexpected,
# writes OUT_DIR/AGGREGATE.json, and this script exits with its status (0 = PASS).
#
# Requires: git, make, gcc/g++, python3 (3.14 used), liblapack/libblas, lua5.2 headers.

if [ "$#" -ne 1 ]; then
    echo "usage: sh testing/p04_run_all.sh OUT_DIR" >&2
    exit 2
fi
ROOT=$(cd "$(dirname "$0")/.." && pwd -P)
if [ -e "$1" ] && [ -n "$(ls -A "$1" 2>/dev/null)" ]; then
    echo "refusing to reuse non-empty output directory: $1" >&2
    exit 2
fi
if ! OUT=$(mkdir -p "$1" && cd "$1" && pwd -P) || [ -z "$OUT" ]; then
    echo "cannot create output directory: $1" >&2
    exit 2
fi
BASE=963ccf153855734de968e6cf71477f324e33329c
PY=${PYTHON:-python3}
JOBS=${JOBS:-$(nproc)}
LOG="$OUT/logs"
if ! { mkdir -p "$LOG" "$OUT/d001" "$OUT/d002" "$OUT/error20" "$OUT/regress" && : > "$OUT/STEPS.txt"; }; then
    echo "cannot initialise output directory: $OUT" >&2
    exit 2
fi

# run NAME COMMAND...  : log output, record the raw return code, keep going
run() {
    _run_name=$1
    shift
    "$@" > "$LOG/$_run_name.log" 2>&1
    _run_rc=$?
    echo "$_run_name rc=$_run_rc" >> "$OUT/STEPS.txt"
    echo "[$_run_rc] $_run_name"
}

echo "root=$ROOT out=$OUT"
echo "root_commit=$(git -C "$ROOT" rev-parse HEAD 2>/dev/null)" >> "$OUT/STEPS.txt"

# 1. baseline source (the exact base commit, nothing else)
rm -rf "$OUT/baseline-src"
mkdir -p "$OUT/baseline-src"
run export_baseline sh -c "git -C '$ROOT' archive '$BASE' | tar -x -C '$OUT/baseline-src'"

# 2. normal builds: candidate and baseline, same flags, from clean build directories
for tree in "$ROOT" "$OUT/baseline-src"; do
    if [ "$tree" = "$ROOT" ]; then name=candidate; else name=baseline; fi
    run build_${name}_lib sh -c "cd '$tree' && rm -rf build && make -j$JOBS build/libS4.a build/S4 build/RCWA.so build/FunctionSampler2D.so"
    run build_${name}_pyext sh -c "cd '$tree' && rm -f S4.*.so && $PY setup.py build_ext --inplace"
done

# 3. TEST-ONLY seam build of the candidate: S4_TEST_EIGEN_INFO + test seam header
run build_seam_lib sh -c "cd '$ROOT' && rm -rf build-seam && CPPFLAGS='-DS4_TEST_EIGEN_INFO -I$ROOT/testing/s4test/test_seams' make -j$JOBS OBJDIR=build-seam build-seam/libS4.a build-seam/S4"
run build_seam_pyext $PY -I -B "$ROOT/testing/s4test/error20/link_seam_ext.py" --root "$ROOT" --lib "$ROOT/build-seam/libS4.a" --out-dir "$ROOT/build-seam/py"

# 4. D001 physical matrix (frozen 12 cases) and extension (108 + 5 cases)
run d001_frozen_candidate sh -c "cd '$ROOT/testing/d001' && $PY -I -B run_d001_matrix.py --s4-dir '$ROOT' --out '$OUT/d001/frozen-candidate' --label candidate"
run d001_frozen_baseline sh -c "cd '$ROOT/testing/d001' && $PY -I -B run_d001_matrix.py --s4-dir '$OUT/baseline-src' --out '$OUT/d001/frozen-baseline' --label baseline"
run d001_ext_candidate sh -c "cd '$ROOT/testing/d001' && $PY -I -B run_d001_extension.py --s4-dir '$ROOT' --out '$OUT/d001/ext-candidate' --label candidate"
run d001_ext_baseline sh -c "cd '$ROOT/testing/d001' && $PY -I -B run_d001_extension.py --s4-dir '$OUT/baseline-src' --out '$OUT/d001/ext-baseline' --label baseline"
run d001_oracle_selfcheck sh -c "cd '$ROOT/testing/d001' && $PY -I -B oracle_d001_ext.py"

# 5. D002 native contract: judge self-tests, six driver identities, sanitizer controls
D2="$ROOT/testing/d002/run_d002.py"
run d002_unit_tests $PY -I -B "$ROOT/testing/d002/test_run_d002.py"
run p04_aggregate_selftest $PY -I -B "$ROOT/testing/p04_aggregate_test.py"
for spec in "ord_candidate $ROOT" "asan_candidate $ROOT" "seam_asan_candidate $ROOT" \
            "ord_baseline $OUT/baseline-src" "asan_baseline $OUT/baseline-src" \
            "seam_asan_baseline $OUT/baseline-src"; do
    set -- $spec
    variant=$1
    src=$2
    run d002_build_$variant $PY -I -B "$D2" build --src-root "$src" --variant "$variant" --out-dir "$OUT/d002/bin"
    run d002_run_$variant $PY -I -B "$D2" run --variant "$variant" --bin "$OUT/d002/bin/d002_$variant" --run-dir "$OUT/d002/run"
    run d002_judge_$variant $PY -I -B "$D2" judge --variant "$variant" --run-dir "$OUT/d002/run"
done
run d002_positives $PY -I -B "$D2" positives --out-dir "$OUT/d002/positives"

# 6. S4-level error code 20 propagation: Python (in process), Lua and C
run error20 $PY -I -B "$ROOT/testing/s4test/error20/run_error20.py" \
    --seam-py-dir "$ROOT/build-seam/py" --seam-lua "$ROOT/build-seam/S4" \
    --seam-lib "$ROOT/build-seam/libS4.a" --src-include "$ROOT/S4" \
    --normal-py-dir "$ROOT" --out-dir "$OUT/error20"

# 7. adjacent regressions on both trees: s4test suite, Lua regression, binding smoke
run s4test_candidate sh -c "cd '$ROOT' && PYTHONPATH='$ROOT:$ROOT/testing/s4test' $PY -m unittest discover -s testing/s4test -p 'test_*.py' -v"
run s4test_baseline sh -c "cd '$OUT/baseline-src' && PYTHONPATH='$OUT/baseline-src:$OUT/baseline-src/testing/s4test' $PY -m unittest discover -s testing/s4test -p 'test_*.py' -v"
run lua_regression sh -c "cd '$ROOT/testing' && S4_BIN=../build/S4 sh runtests.sh"
run python_binding_smoke sh -c "cd '$ROOT' && PYTHONPATH='$ROOT' $PY testing/test_python_binding.py"

# 8. identities of every artifact that a result depends on.  One record per label:
#    SHA256<TAB>LABEL<TAB>PATH, or "# MISSING<TAB>LABEL<TAB>PATH" when the file is absent.
#    The aggregator re-hashes every recorded path and rejects any label that is not recorded.
artifact() {
    if [ -f "$2" ]; then
        printf '%s\t%s\t%s\n' "$(sha256sum "$2" | cut -d' ' -f1)" "$1" "$2"
    else
        printf '# MISSING\t%s\t%s\n' "$1" "$2"
    fi
}
set -- "$ROOT"/S4.cpython-*.so
cand_pyext=$1
set -- "$ROOT/build-seam/py"/S4*.so
seam_pyext=$1
set -- "$OUT"/baseline-src/S4.cpython-*.so
base_pyext=$1
{
    artifact candidate-lib "$ROOT/build/libS4.a"
    artifact candidate-cli "$ROOT/build/S4"
    artifact candidate-rcwa "$ROOT/build/RCWA.so"
    artifact candidate-pyext "$cand_pyext"
    artifact candidate-Eigensystems.cpp "$ROOT/S4/RNP/Eigensystems.cpp"
    artifact seam-lib "$ROOT/build-seam/libS4.a"
    artifact seam-cli "$ROOT/build-seam/S4"
    artifact seam-pyext "$seam_pyext"
    artifact baseline-lib "$OUT/baseline-src/build/libS4.a"
    artifact baseline-cli "$OUT/baseline-src/build/S4"
    artifact baseline-pyext "$base_pyext"
    artifact baseline-Eigensystems.cpp "$OUT/baseline-src/S4/RNP/Eigensystems.cpp"
    for v in ord_candidate asan_candidate seam_asan_candidate \
             ord_baseline asan_baseline seam_asan_baseline; do
        artifact "d002-bin-$v" "$OUT/d002/bin/d002_$v"
    done
} > "$OUT/ARTIFACTS.sha256"

# 9. aggregate: classify every step from its raw rc and its judgement file
$PY -I -B "$ROOT/testing/p04_aggregate.py" "$OUT" > "$OUT/AGGREGATE.txt" 2>&1
AGG_RC=$?
cat "$OUT/AGGREGATE.txt"
echo "aggregate rc=$AGG_RC  (details: $OUT/AGGREGATE.json)"
exit $AGG_RC
