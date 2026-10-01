#!/usr/bin/env python3
"""line-replace.py <file> <exact-line> <replacement-line>

Replaces the first line identical to <exact-line> with <replacement-line>.
Exits 3 when the anchor is missing or not unique, so a mis-targeted mutation
can never silently no-op.
"""
import io
import sys

path, anchor, repl = sys.argv[1], sys.argv[2], sys.argv[3]
with io.open(path, encoding="utf-8") as fh:
    lines = fh.read().splitlines(keepends=True)

hits = [i for i, l in enumerate(lines) if l.rstrip("\n") == anchor]
if len(hits) != 1:
    sys.exit("ANCHOR COUNT %d (want 1) for %r" % (len(hits), anchor))
lines[hits[0]] = repl + "\n"
with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
    fh.write("".join(lines))
print("replaced line %d" % (hits[0] + 1))
