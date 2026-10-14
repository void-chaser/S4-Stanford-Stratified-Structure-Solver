#!/usr/bin/env python3
"""P05-S4 R8 M1a 续3a audit (r8m1a4audit): evidence manifest of the audit round.  New file.

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/manifest_evidence_r8m1a4audit.py

Writes checkpoints/p05/evidence/p05-s4r8/m1a4audit/SHA256SUMS_M1a4AUDIT.txt covering the non-binary evidence files of
this audit round, listed explicitly (no globbing).  The manifest does not list itself.  Two files are live logs that are
appended by every safe_run call (safe_run.log and PRERUN_CHECKS_R8_M1a4AUDIT.txt); for them the manifest records a
snapshot length and hash, marked LIVE, and does not claim that they stay unchanged.  The one file written by a
non-wrapped command (tmp/unit_sha_set.txt, see the report, disclosed event) is listed and marked UNWRAPPED_WRITE_PRODUCT,
it is not used as evidence.  The manifest refuses to overwrite an existing manifest (U17) and verifies every line by
re-reading the written file.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EVA = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a4audit")
OUT = os.path.join(EVA, "SHA256SUMS_M1a4AUDIT.txt")

# (relative path under EVA, marker).  Marker: FIXED for ordinary evidence; LIVE for appended logs;
# UNWRAPPED_WRITE_PRODUCT for the disclosed non-wrapped write.
FILES = [
    ("DRIVER_TAG_AUDIT_R8_M1a4.tsv", "FIXED"),
    ("AUDIT_UNITS_VS_HISTORY_R8_M1a4AUDIT.tsv", "FIXED"),
    ("COMPARE_UNITS_VS_HISTORY_R8_M1a4AUDIT.tsv", "FIXED"),
    ("APPEND_ERRATA_E8_63_TEXT.txt", "FIXED"),
    ("APPEND_ERRATA_E8_64_TEXT.txt", "FIXED"),
    ("APPEND_ERRATA_E8_65_TEXT.txt", "FIXED"),
    ("STRICT_RECHECK_CALLSEQ_R8_M1a4AUDIT.tsv", "FIXED"),
    ("STRICT_RECHECK_CALLSEQ_R8_M1a4AUDIT_SUMMARY.txt", "FIXED"),
    ("ADDITIONS_STRICT_R8_M1a4AUDIT.tsv", "FIXED"),
    ("ADDITIONS_STRICT_R8_M1a4AUDIT_SUMMARY.txt", "FIXED"),
    ("additions_strict_r2/ADDITIONS_STRICT_R8_M1a4AUDIT.tsv", "FIXED"),
    ("additions_strict_r2/ADDITIONS_STRICT_R8_M1a4AUDIT_SUMMARY.txt", "FIXED"),
    ("additions_strict_r2/ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT.tsv", "FIXED"),
    ("tmp/unit_sha_set.txt", "UNWRAPPED_WRITE_PRODUCT"),
    ("safe_run.log", "LIVE"),
    ("PRERUN_CHECKS_R8_M1a4AUDIT.txt", "LIVE"),
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv):
    if len(argv) != 1:
        raise SystemExit("usage: manifest_evidence_r8m1a4audit.py")
    if os.path.exists(OUT):
        raise SystemExit("REFUSED: exists (U17): %s" % OUT)
    lines = []
    for rel, marker in FILES:
        p = os.path.join(EVA, rel)
        if not os.path.isfile(p):
            raise SystemExit("REFUSED: file missing: %s" % p)
        size = os.path.getsize(p)
        digest = sha256_file(p)
        if marker == "LIVE":
            lines.append("%s  %s  LIVE snapshot_bytes=%d" % (digest, rel, size))
        else:
            lines.append("%s  %s  %s" % (digest, rel, marker))
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    # verify by re-reading the written manifest
    with open(OUT, encoding="utf-8") as fh:
        written = fh.read().splitlines()
    bad = 0
    for line in written:
        digest = line.split("  ", 1)[0]
        rel = line.split("  ", 2)[1]
        if sha256_file(os.path.join(EVA, rel)) != digest:
            if "LIVE" not in line:
                bad += 1
    print("MANIFEST_EVIDENCE_R8_M1a4AUDIT entries=%d non_live_bad=%d" % (len(written), bad))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
