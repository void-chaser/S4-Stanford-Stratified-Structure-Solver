#!/usr/bin/env python3
# append_end_registries_r8m1c2.py -- copies GATE_R8_M1c2_END.txt into registries/s4r8/M1c/r8m1c2/ and APPENDS its
# line to that directory's SHA256SUMS.txt (append only; U17).  Then verifies the listed set equals the directory set
# (excluding SHA256SUMS.txt) and every sha256.  The end gate must have passed (FAILS=0) before this runs.
# Usage: python3 -I -B append_end_registries_r8m1c2.py
import hashlib, os, shutil, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c2")
DST = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c2")
SRC = os.path.join(EV, "GATE_R8_M1c2_END.txt")
NAME = "GATE_R8_M1c2_END.txt"
SUMS = os.path.join(DST, "SHA256SUMS.txt")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# the end gate must have passed
with open(SRC, encoding="utf-8") as fh:
    last = fh.read().rstrip("\n").split("\n")[-1]
if last != "FAILS=0":
    print("REFUSED end gate not FAILS=0: %s" % last)
    sys.exit(2)
if os.path.exists(os.path.join(DST, NAME)):
    print("REFUSED exists (U17): %s" % NAME)
    sys.exit(2)

shutil.copyfile(SRC, os.path.join(DST, NAME))
s_src, s_dst = sha256_file(SRC), sha256_file(os.path.join(DST, NAME))
bad = []
if s_src != s_dst:
    bad.append("copy sha256 mismatch: %s" % NAME)
with open(SUMS, "a", encoding="utf-8") as fh:
    fh.write("%s  %s\n" % (s_dst, NAME))

listed = {}
with open(SUMS, encoding="utf-8") as fh:
    for line in fh:
        s, n = line.rstrip("\n").split("  ", 1)
        listed[n] = s
dir_names = sorted(n for n in os.listdir(DST) if n != "SHA256SUMS.txt")
if sorted(listed) != dir_names:
    bad.append("SHA256SUMS list differs from directory")
for n, s in listed.items():
    if sha256_file(os.path.join(DST, n)) != s:
        bad.append("SHA256SUMS mismatch: %s" % n)
print("APPENDED %s sha256=%s" % (NAME, s_dst))
print("BAD=%d" % len(bad))
for b in bad:
    print("BAD\t%s" % b)
sys.exit(1 if bad else 0)
