#!/usr/bin/env python3
"""Link the Python extension against a seam libS4.a (test-only build).

Same sources and link libraries as setup.py (main_python.c + the static library),
written to BUILD_DIR/py/S4<EXT_SUFFIX>, so the normal build/ products are untouched.

Usage: python3 -I -B link_seam_ext.py --root ROOT --lib ROOT/build-seam/libS4.a
"""
import argparse
import os
import subprocess
import sys
import sysconfig


def main():
    ap = argparse.ArgumentParser(description="link the seam Python extension")
    ap.add_argument("--root", required=True)
    ap.add_argument("--lib", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    root = os.path.realpath(args.root)
    out_dir = os.path.realpath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "S4" + sysconfig.get_config_var("EXT_SUFFIX"))
    argv = ["gcc", "-shared", "-fPIC", "-O3", "-march=native", "-fcx-limited-range",
            "-I" + sysconfig.get_paths()["include"], "-I" + os.path.join(root, "S4"),
            os.path.join(root, "S4", "main_python.c"), os.path.realpath(args.lib),
            "-llapack", "-lblas", "-lstdc++", "-lm", "-o", out]
    pr = subprocess.run(argv, capture_output=True, text=True)
    if pr.returncode != 0:
        sys.stderr.write(pr.stderr)
        return pr.returncode
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
