#!/usr/bin/env python3
# sums_ev_r8m1c2.py -- writes $EV/SHA256SUMS.txt covering all non-binary evidence files of R8 M1c2 (brief section 8.2).
# Excludes: the tmp/ scratch area, SHA256SUMS.txt itself, and binary files (any NUL byte in the first 8 KiB).
# Lines are "<sha256>  <path relative to EV>", sorted by path.  Verifies every line after writing.
# Usage: python3 -I -B sums_ev_r8m1c2.py
import hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c2")
OUT = os.path.join(EV, "SHA256SUMS.txt")

if os.path.exists(OUT):
    print("REFUSED exists (U17): %s" % OUT)
    sys.exit(2)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def is_binary(path):
    with open(path, "rb") as fh:
        return b"\x00" in fh.read(8192)


entries = []
skipped_binary = []
for root, dirs, files in os.walk(EV):
    dirs[:] = [d for d in dirs if d != "tmp"]
    for f in files:
        full = os.path.join(root, f)
        rel = os.path.relpath(full, EV)
        if rel == "SHA256SUMS.txt":
            continue
        if is_binary(full):
            skipped_binary.append(rel)
            continue
        entries.append((rel, sha256_file(full)))

entries.sort()
with open(OUT, "w", encoding="utf-8") as fh:
    for rel, s in entries:
        fh.write("%s  %s\n" % (s, rel))

# verify every line
bad = []
with open(OUT, encoding="utf-8") as fh:
    for line in fh:
        s, rel = line.rstrip("\n").split("  ", 1)
        if sha256_file(os.path.join(EV, rel)) != s:
            bad.append(rel)
print("LISTED=%d" % len(entries))
print("SKIPPED_BINARY=%d" % len(skipped_binary))
for b in skipped_binary:
    print("SKIPPED_BINARY_FILE\t%s" % b)
print("VERIFY_BAD=%d" % len(bad))
sys.exit(1 if bad else 0)
