#!/usr/bin/env python3
"""P05-S4 R8 M1a 续3a audit (r8m1a4audit): second archive batch into registries/s4r8/M1a/.  New file.

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/copy_registries_r8m1a4audit_b.py EVDIR

Copies a fixed list of the strict-recheck and strict-association small tables.  The first-run table (3 MISMATCH) and the
corrected table (9 MATCH) are archived under distinct names, so neither overwrites the other.  Refuses to overwrite any
existing target (U17), removes nothing, and compares every copy byte-for-byte (cmp) before it returns.
"""
import filecmp
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DEST = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")

# (source relative to the evidence directory, archive name).  Fixed list: no globbing.
FILES = [
    ("m1a4audit/STRICT_RECHECK_CALLSEQ_R8_M1a4AUDIT.tsv", "STRICT_RECHECK_CALLSEQ_R8_M1a4AUDIT.tsv"),
    ("m1a4audit/STRICT_RECHECK_CALLSEQ_R8_M1a4AUDIT_SUMMARY.txt", "STRICT_RECHECK_CALLSEQ_R8_M1a4AUDIT_SUMMARY.txt"),
    ("m1a4audit/ADDITIONS_STRICT_R8_M1a4AUDIT.tsv", "ADDITIONS_STRICT_R8_M1a4AUDIT_FIRSTRUN_MISMATCH3.tsv"),
    ("m1a4audit/additions_strict_r2/ADDITIONS_STRICT_R8_M1a4AUDIT.tsv", "ADDITIONS_STRICT_R8_M1a4AUDIT_R2_MATCH9.tsv"),
    ("m1a4audit/additions_strict_r2/ADDITIONS_STRICT_R8_M1a4AUDIT_SUMMARY.txt",
     "ADDITIONS_STRICT_R8_M1a4AUDIT_R2_MATCH9_SUMMARY.txt"),
    ("m1a4audit/additions_strict_r2/ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT.tsv",
     "ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT.tsv"),
]


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: copy_registries_r8m1a4audit_b.py EVDIR")
    ev = argv[1]
    if not os.path.isdir(ev):
        raise SystemExit("REFUSED: evidence dir missing: %s" % ev)
    if not os.path.isdir(DEST):
        raise SystemExit("REFUSED: destination missing: %s" % DEST)
    plan = []
    for rel, name in FILES:
        src = os.path.join(ev, rel)
        if not os.path.isfile(src):
            raise SystemExit("REFUSED: source missing: %s" % src)
        dst = os.path.join(DEST, name)
        if os.path.exists(dst):
            raise SystemExit("REFUSED: exists (U17): %s" % dst)
        plan.append((src, dst))
    for src, dst in plan:
        shutil.copyfile(src, dst)
        if not filecmp.cmp(src, dst, shallow=False):
            raise SystemExit("FAIL: byte comparison failed for %s" % dst)
        print("COPY_OK %s -> %s bytes=%d" % (os.path.relpath(src, REPO), os.path.relpath(dst, REPO), os.path.getsize(dst)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
