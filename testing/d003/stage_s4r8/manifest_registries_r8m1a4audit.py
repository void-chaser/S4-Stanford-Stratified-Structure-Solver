#!/usr/bin/env python3
"""P05-S4 R8 M1a 续3a audit (r8m1a4audit): registries manifest for the audit archive batch.  New file.

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/manifest_registries_r8m1a4audit.py

Writes registries/s4r8/M1a/SHA256SUMS_M1a4AUDIT.txt covering exactly the files of this audit round (fixed list).
The historical manifest SHA256SUMS_M1a4.txt is not modified.  The manifest does not list itself.  It refuses to
overwrite an existing manifest (U17), and verifies every line it has written by re-reading the target file.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DEST = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")
OUT = os.path.join(DEST, "SHA256SUMS_M1a4AUDIT.txt")

# Fixed list of this round's archive files (no globbing; the manifest does not list itself).
FILES = [
    "DRIVER_TAG_AUDIT_R8_M1a4.tsv",
    "AUDIT_UNITS_VS_HISTORY_R8_M1a4AUDIT.tsv",
    "COMPARE_UNITS_VS_HISTORY_R8_M1a4AUDIT.tsv",
    "PRERUN_CHECKS_R8_M1a4AUDIT.txt",
    "CALLSEQ_POINT_COVERAGE_CHECK_R8_M1a4_R3.tsv",
    "CALLSEQ_VALIDITY_R8_M1a4_R3.tsv",
    "CALLSEQ_KMAX_R8_M1a4_R3.tsv",
    "STRICT_RECHECK_CALLSEQ_R8_M1a4AUDIT.tsv",
    "STRICT_RECHECK_CALLSEQ_R8_M1a4AUDIT_SUMMARY.txt",
    "ADDITIONS_STRICT_R8_M1a4AUDIT_FIRSTRUN_MISMATCH3.tsv",
    "ADDITIONS_STRICT_R8_M1a4AUDIT_R2_MATCH9.tsv",
    "ADDITIONS_STRICT_R8_M1a4AUDIT_R2_MATCH9_SUMMARY.txt",
    "ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT.tsv",
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv):
    if len(argv) != 1:
        raise SystemExit("usage: manifest_registries_r8m1a4audit.py")
    if os.path.exists(OUT):
        raise SystemExit("REFUSED: exists (U17): %s" % OUT)
    lines = []
    for name in FILES:
        p = os.path.join(DEST, name)
        if not os.path.isfile(p):
            raise SystemExit("REFUSED: file missing: %s" % p)
        lines.append("%s  %s" % (sha256_file(p), name))
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    # verify by re-reading the written manifest and recomputing each hash
    with open(OUT, encoding="utf-8") as fh:
        written = fh.read().splitlines()
    bad = 0
    for line in written:
        digest, name = line.split("  ", 1)
        if sha256_file(os.path.join(DEST, name)) != digest:
            bad += 1
    print("MANIFEST_REGISTRIES_R8_M1a4AUDIT entries=%d verified_ok=%d bad=%d" % (
        len(written), len(written) - bad, bad))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
