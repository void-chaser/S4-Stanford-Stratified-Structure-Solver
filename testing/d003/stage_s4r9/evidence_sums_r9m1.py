#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# evidence_sums_r9m1.py -- Generate SHA256SUMS.txt for evidence/p05-s4r9/m1/ (Step S-H). New file.
import hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1"))
OUT_FILE = os.path.join(EV, "SHA256SUMS.txt")

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            c = fh.read(65536)
            if not c: break
            h.update(c)
    return h.hexdigest()

entries = []
for root, dirs, files in os.walk(EV):
    # Skip tmp/
    if os.path.relpath(root, EV).startswith("tmp"):
        continue
    for f in files:
        if f == "SHA256SUMS.txt":
            continue
        full_p = os.path.join(root, f)
        rel_p = os.path.relpath(full_p, EV)
        # Skip sockets/pipes if any
        if not os.path.isfile(full_p):
            continue
        sha = sha256_file(full_p)
        entries.append((rel_p, sha))

entries.sort()
with open(OUT_FILE, "w", encoding="utf-8") as fh:
    for rel_p, sha in entries:
        fh.write(f"{sha}  {rel_p}\n")

print(f"Wrote {OUT_FILE} with {len(entries)} items.")
