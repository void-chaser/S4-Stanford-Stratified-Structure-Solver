#!/bin/sh
# P04 D001/D002 verification pipeline.  Run from any checkout of the product branch:
#
#     sh testing/p04_run_all.sh OUT_DIR
#
# It exports the baseline commit 963ccf1 into OUT_DIR/baseline-src, builds the
# candidate (this tree) and the baseline, builds a TEST-ONLY seam library of the
# candidate, and then runs every check.  Each step's return code is appended to
# OUT_DIR/STEPS.txt; a non-zero code is recorded, not hidden.  The pass/fail
# judgement of each check is in its own JSON summary under OUT_DIR.
#
# Requires: git, make, gcc/g++, python3 (3.14 used), liblapack/libblas, lua5.2 headers.

ROOT=$(cd "$(dirname "$0")/.." && pwd -P)
OUT=$(mkdir -p "$1" && cd "$1" && pwd -P)
BASE=963ccf153855734de968e6cf71477f324e33329c
PY=${PYTHON:-python3}
JOBS=${JOBS:-$(nproc)}
LOG="$OUT/logs"
mkdir -p "$LOG" "$OUT/d001" "$OUT/d002" "$OUT/error20" "$OUT/regress"
: > "$OUT/STEPS.txt"

# run NAME COMMAND...  : log output, record the return code, keep going
run() {
    name=$1
    shift
    "$@" > "$LOG/$name.log" 2>&1
    rc=$?
    echo "$name rc=$rc" >> "$OUT/STEPS.txt"
    echo "[$rc] $name"
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

# 5. D002 native contract: six driver identities, then sanitizer positive controls
D2="$ROOT/testing/d002/run_d002.py"
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

# 8. identities of every artifact that a result depends on
{
    echo "# sha256 of artifacts used by the checks above"
    for f in "$ROOT/build/libS4.a" "$ROOT/build/S4" "$ROOT/build/RCWA.so" \
             "$ROOT"/S4.cpython-*.so "$ROOT/build-seam/libS4.a" "$ROOT/build-seam/S4" \
             "$ROOT/build-seam/py"/S4*.so \
             "$OUT/baseline-src/build/libS4.a" "$OUT/baseline-src/build/S4" \
             "$OUT"/baseline-src/S4.cpython-*.so \
             "$OUT"/d002/bin/d002_*; do
        [ -f "$f" ] && sha256sum "$f"
    done
    echo "# candidate Eigensystems.cpp: $(sha256sum "$ROOT/S4/RNP/Eigensystems.cpp" | cut -d' ' -f1)"
    echo "# baseline  Eigensystems.cpp: $(sha256sum "$OUT/baseline-src/S4/RNP/Eigensystems.cpp" | cut -d' ' -f1)"
} > "$OUT/ARTIFACTS.sha256"

echo "done; see $OUT/STEPS.txt"
