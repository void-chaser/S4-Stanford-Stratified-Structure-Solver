#!/usr/bin/env python3
"""P05-S4 R8 M0 closing gate (gate3): repeat of the registries/s4r7 manifest checks, read only.  New file.

check_s4r7_manifests_r8.py (committed) writes a fixed output name and accepts only the names R2 and R2_END, so it cannot
write the closing check under a new name.  This script imports its check functions and runs them again (RESTART2 section
2.1 end item 3, item 7: "repeat"), without modifying the committed script and without writing any file: it prints the
rows and the final line "fails=<n>" to standard output; gate3_r8.sh redirects that output into the evidence directory.
Usage (through safe_run):  python3 -I -B testing/d003/stage_s4r8/recheck_s4r7_r8_r3.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_s4r7_manifests_r8 as C  # noqa: E402  imported, not modified; its main() is not called


def main(argv):
    if len(argv) != 1:
        raise SystemExit("usage: recheck_s4r7_r8_r3.py  (no arguments; output to standard output)")
    for name in C.DIRECT:
        C.check_direct(name)
    for name in sorted(C.SNAP_MANIFESTS):
        C.check_snapshot(name)
    for name in sorted(C.STD_MANIFESTS):
        C.check_std(name)
    C.check_set()
    print("# recheck of registries/s4r7 manifests (gate3, read only; check_s4r7_manifests_r8 functions, imported)")
    print("manifest\tcheck\texpected\tactual\tresult")
    for row in C.ROWS:
        print("\t".join(row))
    print("fails=%d" % C.FAILS[0])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
