#!/usr/bin/env python3
# sums_ev_r8m1c4.py -- P05-S4 R8 M1c4 evidence checksums (AGENTS.md 7.2). New file (copied from sums_ev_r8m1c3.py; EV changed to m1c4).
# Writes $EV/SHA256SUMS.txt covering all non-binary evidence files under $EV (text by extension or by content),
# excluding SHA256SUMS.txt itself and the tmp directory. Binary files are not in $EV. U17: created once.
# Usage: python3 -I -B testing/d003/stage_s4/sums_ev_r8m1c4.py
import hashlib
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c4")
OUT = os.path.join(EV, "SHA256SUMS.txt")
if os.path.exists(OUT):
    print("REFUSED exists (U17): %s" % OUT)
    sys.exit(2)

TEXT_EXT = (".txt", ".tsv", ".log", ".stdout", ".out", ".py", ".sh", ".gdb", ".md", ".csv")
entries = []
for root, dirs, files in os.walk(EV):
    dirs[:] = [d for d in dirs if d != "tmp"]
    for f in files:
        full = os.path.join(root, f)
        rel = os.path.relpath(full, EV)
        if rel == "SHA256SUMS.txt":
            continue
        with open(full, "rb") as fh:
            head = fh.read(8192)
        is_text = (b"\x00" not in head)
        if not is_text:
            continue  # binary (executables, libraries, objects) is recorded by sha256 elsewhere, not here
        h = hashlib.sha256()
        with open(full, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        entries.append((rel, h.hexdigest()))

entries.sort()
with open(OUT, "x", encoding="utf-8") as fh:
    for rel, sha in entries:
        fh.write("%s  %s\n" % (sha, rel))
print("SUMS_ENTRIES=%d -> %s" % (len(entries), OUT))
