#!/usr/bin/env python3
# make_dual_r8m2a2.py -- P05-S4 R8 M2a2 section 4.3 (U244): build inject_r8m2a2_dual.cpp as an exact copy of
# inject_r4_plan.cpp plus the appended block inject_r8m2a2_dual_append.inc.  New file.
# Checks: the output's first len(base) bytes equal the base byte-for-byte (original branches unchanged),
# and the appended part equals the .inc.  Writes the SRC_DIFF (diff -u of base -> output) to $EV.
# Refuses to overwrite the output (U17) unless --rewrite-fresh is absent and the file is missing.
import difflib
import hashlib
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
S4DIR = os.path.join(REPO, "testing", "d003", "stage_s4")
BASE = os.path.join(S4DIR, "inject_r4_plan.cpp")
APP = os.path.join(S4DIR, "inject_r8m2a2_dual_append.inc")
OUT = os.path.join(S4DIR, "inject_r8m2a2_dual.cpp")
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
DIFF = os.path.join(EV, "SRC_DIFF_R8_M2a2_inject_dual.txt")


def rb(p):
    with open(p, "rb") as fh:
        return fh.read()


def main():
    if os.path.exists(OUT):
        print("make_dual_r8m2a2: REFUSED exists (U17): %s" % OUT)
        return 2
    if os.path.exists(DIFF):
        print("make_dual_r8m2a2: REFUSED exists (U17): %s" % DIFF)
        return 2
    base = rb(BASE)
    app = rb(APP)
    out = base + app
    assert out[:len(base)] == base
    assert out[len(base):] == app
    with open(OUT, "xb") as fh:
        fh.write(out)
    # SRC_DIFF: diff -u of base against the output (the diff is written as text, shown in the report).
    d = difflib.unified_diff(base.decode("utf-8").splitlines(keepends=True),
                             out.decode("utf-8").splitlines(keepends=True),
                             fromfile="a/testing/d003/stage_s4/inject_r4_plan.cpp",
                             tofile="b/testing/d003/stage_s4/inject_r8m2a2_dual.cpp", n=3)
    os.makedirs(EV, exist_ok=True)
    with open(DIFF, "x", encoding="utf-8") as fh:
        fh.write("# SRC_DIFF_R8_M2a2_inject_dual -- base inject_r4_plan.cpp (sha256 %s) -> inject_r8m2a2_dual.cpp (sha256 %s)\n"
                 % (hashlib.sha256(base).hexdigest(), hashlib.sha256(out).hexdigest()))
        fh.write("".join(d))
    lines = sum(1 for _ in out.decode("utf-8").splitlines())
    print("make_dual_r8m2a2: wrote %s (%d lines; base prefix byte-exact; diff %s)" % (OUT, lines, DIFF))
    return 0


if __name__ == "__main__":
    sys.exit(main())
