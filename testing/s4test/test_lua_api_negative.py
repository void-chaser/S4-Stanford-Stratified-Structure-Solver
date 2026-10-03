#!/usr/bin/env python3
"""
Negative test suite for S4 Lua API.
Enforces that:
1. A healthy control script using the Interpolator API succeeds with returncode 0.
2. Invalid API calls do NOT crash with signals (e.g., segfault/abort), exit with non-zero
   (specifically returncode 1 from S4L_error/docall), and output the expected error message.
"""

import subprocess
import os
import sys
import tempfile

def main():
    repo_root = os.environ.get('S4_TEST_REPO_ROOT', os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    s4_bin = os.path.join(repo_root, 'build', 'S4')
    
    if not os.path.isfile(s4_bin):
        print(f"ERROR: S4 binary not found at {s4_bin}")
        sys.exit(1)

    print("=== S4 Lua API Negative Test Suite ===")

    # 1. Healthy Control
    print("[1] Running Healthy Control (valid interpolation API call)...")
    healthy_script = """
    local interp = S4.NewInterpolator('linear', {
        {0.0, {10.0, 20.0}},
        {1.0, {30.0, 40.0}}
    })
    local y1, y2 = interp:Get(0.5)
    if math.abs(y1 - 20.0) > 1e-12 or math.abs(y2 - 30.0) > 1e-12 then
        error("Value mismatch: expected 20 and 30")
    end
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False) as tf:
        tf.write(healthy_script)
        healthy_path = tf.name

    try:
        p = subprocess.run([s4_bin, healthy_path], capture_output=True, text=True)
    finally:
        if os.path.exists(healthy_path):
            os.remove(healthy_path)

    if p.returncode != 0:
        print(f"FATAL: Healthy control failed with exit code {p.returncode}!")
        print("Stdout:", p.stdout)
        print("Stderr:", p.stderr)
        sys.exit(1)

    print("  -> PASS: Healthy control succeeded with exit code 0.")

    # 2. Negative Cases
    # Tuple: (description, lua_code, expected_exit_code, expected_err_substring)
    negative_tests = [
        (
            "Missing arg 2 (table)",
            "S4.NewInterpolator('linear')",
            1,
            "Table expected for argument 2"
        ),
        (
            "Bad interpolator type",
            "S4.NewInterpolator('invalid_type', {{0.0, {1.0}}, {1.0, {2.0}}})",
            1,
            "type should be"
        ),
        (
            "Non-table arg 2",
            "S4.NewInterpolator('linear', 'not_a_table')",
            1,
            "Table expected for argument 2"
        ),
        (
            "Table length < 2",
            "S4.NewInterpolator('linear', {{0.0, {1.0}}})",
            1,
            "Table must be of length 2 or more"
        ),
        (
            "Non-table row item",
            "S4.NewInterpolator('linear', {1.0, 2.0})",
            1,
            "Table must contain tables"
        ),
        (
            "Bad x type (string)",
            "S4.NewInterpolator('linear', {{'not_a_num', {1.0}}, {1.0, {2.0}}})",
            1,
            "x value must be a number"
        ),
        (
            "Bad y type (string)",
            "S4.NewInterpolator('linear', {{0.0, {'not_a_num'}}, {1.0, {2.0}}})",
            1,
            "y value must be a number"
        ),
        (
            "x not finite (NaN/Inf)",
            "S4.NewInterpolator('linear', {{0.0/0.0, {1.0}}, {1.0, {2.0}}})",
            1,
            "x values must be finite numbers"
        ),
        (
            "y not finite (NaN/Inf)",
            "S4.NewInterpolator('linear', {{0.0, {1.0/0.0}}, {1.0, {2.0}}})",
            1,
            "y values must be finite numbers"
        ),
        (
            "Non-monotonic x",
            "S4.NewInterpolator('linear', {{1.0, {1.0}}, {0.0, {2.0}}})",
            1,
            "strictly monotonically increasing"
        ),
        (
            "Row dimension mismatch",
            "S4.NewInterpolator('linear', {{0.0, {1.0}}, {1.0, {2.0, 3.0}}})",
            1,
            "expected"
        ),
        (
            "Empty Get() argument",
            "local i = S4.NewInterpolator('linear', {{0.0, {0.0}}, {1.0, {1.0}}}); i:Get()",
            1,
            "Get"
        ),
        (
            "Bad Get() argument type",
            "local i = S4.NewInterpolator('linear', {{0.0, {0.0}}, {1.0, {1.0}}}); i:Get('bad')",
            1,
            "Get"
        ),
        (
            "Get() coordinate not finite",
            "local i = S4.NewInterpolator('linear', {{0.0, {0.0}}, {1.0, {1.0}}}); i:Get(0.0/0.0)",
            1,
            "x must be finite"
        ),
    ]

    failed = False
    for idx, (desc, script, exp_code, exp_err) in enumerate(negative_tests, 2):
        print(f"[{idx}] Testing: {desc}...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.lua', delete=False) as tf:
            tf.write(script)
            tmp_path = tf.name

        try:
            p = subprocess.run([s4_bin, tmp_path], capture_output=True, text=True)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        all_output = p.stdout + "\n" + p.stderr

        if p.returncode < 0:
            print(f"  -> FAIL: Process crashed with signal {-p.returncode}!")
            failed = True
            continue

        if p.returncode == 0:
            print(f"  -> FAIL: Expected failure with code {exp_code}, but returned 0!")
            failed = True
            continue

        if p.returncode != exp_code:
            print(f"  -> FAIL: Returned code {p.returncode}, expected {exp_code}!")
            failed = True
            continue

        if exp_err not in all_output:
            print(f"  -> FAIL: Returned code {p.returncode}, but expected error substring '{exp_err}' not in output!")
            print("Output was:", all_output)
            failed = True
            continue

        print(f"  -> PASS: Correctly exited with code {p.returncode}, error matched '{exp_err}'.")

    if failed:
        print("ERROR: Some Lua API negative tests failed!")
        sys.exit(1)

    print("=== All 15 Lua API tests (1 healthy control + 14 negative cases) PASSED ===")
    sys.exit(0)

if __name__ == "__main__":
    main()
