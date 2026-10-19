#!/usr/bin/env python3
# relr4_tmpsnap.py -- P05 delivery round REL-R4: read-only top-level temporary-directory snapshot.
# The START snapshot is taken by relr4_startgate.py (recorded in GATE_RELR4_start.txt); this script takes
# the END snapshot into $EV/TMP_SNAPSHOT_RELR4_end.tsv, and the end gate recomputes the same fact inline.
# It only lists the system temporary directory; it never writes there.
import os, sys, hashlib

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r4")
TAB = chr(9)
NL = chr(10)


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def main():
    label = "end"
    a = sys.argv[1:]
    if "--label" in a:
        label = a[a.index("--label") + 1]
    names = sorted(os.listdir("/tmp"))
    count = len(names)
    sha = sha_b((NL.join(names) + NL).encode("utf-8"))
    out = os.path.join(EV, "TMP_SNAPSHOT_RELR4_end.tsv" if label == "end" else "TMP_SNAPSHOT_RELR4.tsv")
    body = ["# TMP_SNAPSHOT_RELR4%s.tsv -- top-level temporary-directory snapshot (%s) of P05 delivery round REL-R4"
            % ("_end" if label == "end" else "", label),
            "# read only; count = number of top-level entries; sha256 = sha256 of newline-joined Python-sorted names",
            "# calibration identical to s5r7_tmpsnap.py / relr2_tmpsnap.py",
            "key" + TAB + "value",
            "LABEL" + TAB + label,
            "TMP_COUNT" + TAB + str(count),
            "TMP_SHA256" + TAB + sha]
    open(out, "w", encoding="utf-8").write(NL.join(body) + NL)
    print("TMP snapshot label=%s count=%d sha256=%s" % (label, count, sha))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
