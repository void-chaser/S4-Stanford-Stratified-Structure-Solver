#!/bin/bash
# Negative test harness for S4 Lua regression runner (testing/runtests.sh)
# Enforces healthy baseline first, then asserts specific failure modes and error strings.

set -u

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
RUNTESTS="$REPO_ROOT/testing/runtests.sh"
S4_BIN="$REPO_ROOT/build/S4"
NUMDIFF="$REPO_ROOT/testing/numdiff"

if [ ! -f "$RUNTESTS" ]; then
    echo "ERROR: runtests.sh not found at $RUNTESTS"
    exit 1
fi

if [ ! -x "$S4_BIN" ]; then
    echo "ERROR: S4 binary not found or not executable at $S4_BIN"
    exit 1
fi

if [ ! -x "$NUMDIFF" ]; then
    echo "ERROR: numdiff tool not found or not executable at $NUMDIFF"
    exit 1
fi

TMP_DIR="$(mktemp -d /tmp/s4_lua_neg_XXXXXX)"
trap 'rm -rf "$TMP_DIR"' EXIT INT TERM HUP

EXAMPLES_DIR="$TMP_DIR/examples"
mkdir -p "$EXAMPLES_DIR"

echo "=== S4 Lua Regression Negative Test Suite ==="

# -----------------------------------------------------------------------------
# 1. HEALTHY CONTROL
# -----------------------------------------------------------------------------
echo "[1/12] Testing Healthy Control (valid script, valid baseline)..."
cat << 'EOF' > "$EXAMPLES_DIR/healthy.lua"
print("1.000000 2.000000 3.000000")
EOF

cat << 'EOF' > "$EXAMPLES_DIR/healthy.txt"
1.000000 2.000000 3.000000
EOF

cat << 'EOF' > "$TMP_DIR/manifest_healthy.txt"
healthy.lua healthy.txt 1e-12
EOF

HEALTHY_OUT=$(cd "$REPO_ROOT/testing" && TEST_MANIFEST="$TMP_DIR/manifest_healthy.txt" TEST_EXAMPLES_DIR="$EXAMPLES_DIR" "$RUNTESTS" 2>&1)
HEALTHY_CODE=$?

if [ $HEALTHY_CODE -ne 0 ]; then
    echo "FATAL: Healthy control failed with exit code $HEALTHY_CODE!"
    echo "Output:"
    echo "$HEALTHY_OUT"
    exit 1
fi

if ! echo "$HEALTHY_OUT" | grep -q "Lua regression tests PASSED"; then
    echo "FATAL: Healthy control did not output 'Lua regression tests PASSED'!"
    echo "Output:"
    echo "$HEALTHY_OUT"
    exit 1
fi
echo "  -> PASS: Healthy control passed with exit code 0."

# Helper function to run negative cases
# Arguments: test_name, manifest_file, expected_pattern
run_negative_case() {
    local name="$1"
    local manifest="$2"
    local expected_pattern="$3"

    echo "Running: $name..."
    local out
    out=$(cd "$REPO_ROOT/testing" && TEST_MANIFEST="$manifest" TEST_EXAMPLES_DIR="$EXAMPLES_DIR" "$RUNTESTS" 2>&1)
    local code=$?

    if [ $code -eq 0 ]; then
        echo "  -> FAIL: Expected failure (non-zero exit code), but returned 0!"
        echo "Output was:"
        echo "$out"
        exit 1
    fi

    if ! echo "$out" | grep -E -q "$expected_pattern"; then
        echo "  -> FAIL: Failed with code $code, but expected error pattern '$expected_pattern' not found in output!"
        echo "Output was:"
        echo "$out"
        exit 1
    fi

    echo "  -> PASS: Correctly failed with exit code $code, error matched '$expected_pattern'."
}

# -----------------------------------------------------------------------------
# 2. Numerical drift
# -----------------------------------------------------------------------------
cat << 'EOF' > "$EXAMPLES_DIR/drift.lua"
print("1.000000 2.000000")
EOF
cat << 'EOF' > "$EXAMPLES_DIR/drift.txt"
1.000000 2.005000
EOF
cat << 'EOF' > "$TMP_DIR/manifest_drift.txt"
drift.lua drift.txt 1e-6
EOF
run_negative_case "[2/12] Numerical drift" "$TMP_DIR/manifest_drift.txt" "!=.*\(tol"

# -----------------------------------------------------------------------------
# 3. Missing lines (Script output has fewer lines than baseline)
# -----------------------------------------------------------------------------
cat << 'EOF' > "$EXAMPLES_DIR/missing_lines.lua"
print("1.0 2.0")
EOF
cat << 'EOF' > "$EXAMPLES_DIR/missing_lines.txt"
1.0 2.0
3.0 4.0
EOF
cat << 'EOF' > "$TMP_DIR/manifest_missing_lines.txt"
missing_lines.lua missing_lines.txt 1e-6
EOF
run_negative_case "[3/12] Missing lines in output" "$TMP_DIR/manifest_missing_lines.txt" "Different number of lines"

# -----------------------------------------------------------------------------
# 4. Extra lines (Script output has more lines than baseline)
# -----------------------------------------------------------------------------
cat << 'EOF' > "$EXAMPLES_DIR/extra_lines.lua"
print("1.0 2.0")
print("3.0 4.0")
EOF
cat << 'EOF' > "$EXAMPLES_DIR/extra_lines.txt"
1.0 2.0
EOF
cat << 'EOF' > "$TMP_DIR/manifest_extra_lines.txt"
extra_lines.lua extra_lines.txt 1e-6
EOF
run_negative_case "[4/12] Extra lines in output" "$TMP_DIR/manifest_extra_lines.txt" "Different number of lines"

# -----------------------------------------------------------------------------
# 5. Column count mismatch (Different number of values)
# -----------------------------------------------------------------------------
cat << 'EOF' > "$EXAMPLES_DIR/col_mismatch.lua"
print("1.0 2.0 3.0")
EOF
cat << 'EOF' > "$EXAMPLES_DIR/col_mismatch.txt"
1.0 2.0
EOF
cat << 'EOF' > "$TMP_DIR/manifest_col_mismatch.txt"
col_mismatch.lua col_mismatch.txt 1e-6
EOF
run_negative_case "[5/12] Column count mismatch" "$TMP_DIR/manifest_col_mismatch.txt" "Different number of values"

# -----------------------------------------------------------------------------
# 6. NaN / Inf
# -----------------------------------------------------------------------------
cat << 'EOF' > "$EXAMPLES_DIR/nan.lua"
print("nan 2.0")
EOF
cat << 'EOF' > "$EXAMPLES_DIR/nan.txt"
1.0 2.0
EOF
cat << 'EOF' > "$TMP_DIR/manifest_nan.txt"
nan.lua nan.txt 1e-6
EOF
run_negative_case "[6/12] NaN output" "$TMP_DIR/manifest_nan.txt" "!=|Lua regression tests FAILED"

# -----------------------------------------------------------------------------
# 7. Non-numeric output
# -----------------------------------------------------------------------------
cat << 'EOF' > "$EXAMPLES_DIR/non_numeric.lua"
print("NOT_A_NUMBER 2.0")
EOF
cat << 'EOF' > "$EXAMPLES_DIR/non_numeric.txt"
1.0 2.0
EOF
cat << 'EOF' > "$TMP_DIR/manifest_non_numeric.txt"
non_numeric.lua non_numeric.txt 1e-6
EOF
run_negative_case "[7/12] Non-numeric text" "$TMP_DIR/manifest_non_numeric.txt" "Non-numeric field encountered"

# -----------------------------------------------------------------------------
# 8. Missing baseline
# -----------------------------------------------------------------------------
cat << 'EOF' > "$TMP_DIR/manifest_missing_baseline.txt"
healthy.lua nonexistent_baseline.txt 1e-12
EOF
run_negative_case "[8/12] Missing baseline" "$TMP_DIR/manifest_missing_baseline.txt" "Baseline file .* not found"

# -----------------------------------------------------------------------------
# 9. Missing Lua script
# -----------------------------------------------------------------------------
cat << 'EOF' > "$TMP_DIR/manifest_missing_script.txt"
nonexistent_script.lua healthy.txt 1e-12
EOF
run_negative_case "[9/12] Missing Lua script" "$TMP_DIR/manifest_missing_script.txt" "Lua script .* not found"

# -----------------------------------------------------------------------------
# 10. Malformed manifest (Too few fields)
# -----------------------------------------------------------------------------
cat << 'EOF' > "$TMP_DIR/manifest_too_few.txt"
healthy.lua healthy.txt
EOF
run_negative_case "[10/12] Malformed manifest (too few fields)" "$TMP_DIR/manifest_too_few.txt" "Invalid manifest line"

# -----------------------------------------------------------------------------
# 11. Malformed manifest (Too many fields)
# -----------------------------------------------------------------------------
cat << 'EOF' > "$TMP_DIR/manifest_too_many.txt"
healthy.lua healthy.txt 1e-12 extra_column
EOF
run_negative_case "[11/12] Malformed manifest (too many fields)" "$TMP_DIR/manifest_too_many.txt" "Invalid manifest line"

# -----------------------------------------------------------------------------
# 12. Empty manifest
# -----------------------------------------------------------------------------
cat << 'EOF' > "$TMP_DIR/manifest_empty.txt"
# This manifest contains only comments and blank lines

EOF
run_negative_case "[12/12] Empty manifest" "$TMP_DIR/manifest_empty.txt" "No test cases found"

echo "=== All 12 Lua regression tests (1 healthy control + 11 negative cases) PASSED ==="
exit 0
