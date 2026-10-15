#!/usr/bin/env python3
# sums_ev_r8m2a.py -- P05-S4 R8 M2a section 8.3: SHA256SUMS.txt for the non-binary evidence of this round.
# Covers every regular file directly in $EV (log, tsv, txt, md, sha256) and excludes tmp/, build/, tree_*/ (section 8.3).
# Writes $EV/SHA256SUMS.txt (refuses to overwrite, U17).  Read-only on the evidence files.
import hashlib
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a")
OUT = os.path.join(EV, "SHA256SUMS.txt")
EXCLUDE_DIRS = ("tmp", "build", "tree_F3", "tree_B")
BINARY_EXT = (".o", ".a", ".so", ".exe", ".bin")


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    if os.path.exists(OUT):
        print("sums_ev_r8m2a: REFUSED exists (U17): %s" % OUT)
        return 2
    names = []
    for n in sorted(os.listdir(EV)):
        p = os.path.join(EV, n)
        if n in EXCLUDE_DIRS or os.path.isdir(p):
            continue
        if n == "SHA256SUMS.txt" or n.endswith(BINARY_EXT):
            continue
        if os.path.isfile(p):
            names.append(n)
    with open(OUT, "x", encoding="utf-8") as fh:
        for n in names:
            fh.write("%s  %s\n" % (sha256_file(os.path.join(EV, n)), n))
    print("sums_ev_r8m2a: entries=%d out=%s" % (len(names), OUT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
