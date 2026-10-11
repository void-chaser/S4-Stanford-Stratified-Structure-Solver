#!/usr/bin/env python3
"""P05-S1R2 J4: per-entry sha256 table for checkpoints/p05/evidence/EVIDENCE.sha256.

Reads the manifest and, for every entry, computes the SHA-256 of the file it names (read only),
then compares with the recorded value.  Writes a TSV to stdout:
  path  expected_sha256  observed_sha256  result  reason_if_not_ok

result is OK, MISMATCH, or MISSING.  The reason field explains a non-OK result (overwritten,
renamed, missing).  No file in the evidence tree is written or modified.

Usage: python3 -I -B testing/d003/stage_s1r2/j4_hash_table.py EVIDENCE_DIR
  EVIDENCE_DIR must contain EVIDENCE.sha256; entries are relative to EVIDENCE_DIR.
"""
import hashlib
import os
import sys


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if len(sys.argv) != 2:
        sys.stderr.write("usage: j4_hash_table.py EVIDENCE_DIR\n")
        return 2
    base = sys.argv[1]
    manifest = os.path.join(base, "EVIDENCE.sha256")
    print("\t".join(["path", "expected_sha256", "observed_sha256", "result", "reason"]))
    counts = {"OK": 0, "MISMATCH": 0, "MISSING": 0}
    with open(manifest, "r", encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line.strip():
                continue
            parts = line.split(None, 1)
            if len(parts) != 2:
                print("\t".join(["(malformed)", "", "", "MISMATCH", "manifest line not parseable"]))
                counts["MISMATCH"] += 1
                continue
            expected, rel = parts[0], parts[1].strip()
            target = os.path.normpath(os.path.join(base, rel))
            if not os.path.isfile(target):
                print("\t".join([rel, expected, "NA", "MISSING",
                                 "file absent: deleted, renamed, or never present"]))
                counts["MISSING"] += 1
                continue
            observed = sha256_of(target)
            if observed == expected:
                print("\t".join([rel, expected, observed, "OK", ""]))
                counts["OK"] += 1
            else:
                print("\t".join([rel, expected, observed, "MISMATCH",
                                 "content differs: overwritten or regenerated after the manifest was written"]))
                counts["MISMATCH"] += 1
    sys.stderr.write("J4 counts OK=%d MISMATCH=%d MISSING=%d\n" % (counts["OK"], counts["MISMATCH"], counts["MISSING"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
