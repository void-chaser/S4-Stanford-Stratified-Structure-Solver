#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT1 gate5: repeat of the registries/s4r7 manifest checks, read only.  New file (U17, U150(c)).

Copy of recheck_s4r7_r8m1.py (committed in M1a, not modified).  The only change: the accepted output names are
S4R7_RECHECK_R8_M1A2_(START|END).tsv, because the M1a file names are already in use (GATE_R8_M1a file set).
check_s4r7_manifests_r8.py (committed, not modified) is imported; its main() is not called.

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/recheck_s4r7_r8m1a2.py OUT_NAME
OUT_NAME must match S4R7_RECHECK_R8_M1A2(_START|_END)?.tsv and must not exist.  Writes only $EV/OUT_NAME.
The last line of the file is "fails=<n>".  No temporary file, no shell.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
sys.path.insert(0, HERE)
import check_s4r7_manifests_r8 as C  # noqa: E402  imported, not modified; its main() is not called

OUT_RE = re.compile(r"^S4R7_RECHECK_R8_M1A2(_START|_END)?\.tsv$")


def main(argv):
    if len(argv) != 2 or not OUT_RE.match(argv[1]):
        raise SystemExit("usage: recheck_s4r7_r8m1a2.py S4R7_RECHECK_R8_M1A2(_START|_END).tsv")
    out = os.path.join(EV, argv[1])
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    for name in C.DIRECT:
        C.check_direct(name)
    for name in sorted(C.SNAP_MANIFESTS):
        C.check_snapshot(name)
    for name in sorted(C.STD_MANIFESTS):
        C.check_std(name)
    C.check_set()
    lines = ["# recheck of registries/s4r7 manifests (gate5 M1a CONT1, read only; check_s4r7_manifests_r8 functions, imported)",
             "manifest\tcheck\texpected\tactual\tresult"]
    for row in C.ROWS:
        lines.append("\t".join(row))
    lines.append("fails=%d" % C.FAILS[0])
    with open(out, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("fails=%d -> %s" % (C.FAILS[0], out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
