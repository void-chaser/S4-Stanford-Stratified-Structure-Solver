#!/usr/bin/env python3
# copy_registries_r8m2a.py -- P05-S4 R8 M2a section 8.2: copy the small result tables to
# checkpoints/p05/registries/s4r8/M2/r8m2a/ with their ORIGINAL names (U226), write SHA256SUMS.txt and verify
# every copy against its source sha256.  All inputs are checked for existence before the target directory is made.
# Files over 1 MB would be recorded by sha256 only (none expected).  Refuses to overwrite (U17).
import hashlib
import os
import shutil
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a")
DST = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a")
INPUTS = [
    "GATE_R8_M2a_start.txt",
    "GATE_DIFF_R8_M2a.txt",
    "A10_CONTROL_CROSSWALK_R8_M2a.tsv",
    "A10_CONTROL_CROSSWALK_R8_M2a_R2.tsv",
    "APPARATUS_INVENTORY_R8_M2a.tsv",
    "M2_DESIGN_R8_M2a.tsv",
    "M2_DESIGN_R8_M2a_R2.tsv",
    "M2_DESIGN_R8_M2a_R2.md",
    "PREREG_M2_R8_M2a_R2.tsv",
    "PREREG_M2_R8_M2a_R2.sha256",
    "PREREG_M2_R8_M2a_R2_TIMESTAMP_UTC.txt",
    "PREREG_M2_COUNT_R8_M2a_R2.txt",
    "POSCTRL_M2_R8_M2a.txt",
    "POSCTRL_M2_R8_M2a_R2.txt",
    "REPORT_COUNT_CHECK_R8_M2a.txt",
    "RULINGS_APPEND_R8_M2a.tsv",
    "ERRATA_APPEND_R8_M2a.txt",
    "EXPORT_R8_M2a.txt",
    "STATE_BYTES_R8_M2a_R3.txt",
]
SRC_DIFF_GLOB = "SRC_DIFF"  # none in M2a (no copies of historical sources were made)


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    missing = [n for n in INPUTS if not os.path.isfile(os.path.join(EV, n))]
    if missing:
        print("copy_registries_r8m2a: REFUSED missing inputs: %s" % ", ".join(missing))
        return 2
    if os.path.exists(DST):
        print("copy_registries_r8m2a: REFUSED exists (U17): %s" % DST)
        return 2
    os.makedirs(DST)
    entries = []
    for n in INPUTS:
        src = os.path.join(EV, n)
        dst = os.path.join(DST, n)  # ORIGINAL name (U226)
        shutil.copyfile(src, dst)
        entries.append((sha256_file(src), n))
    with open(os.path.join(DST, "SHA256SUMS.txt"), "x", encoding="utf-8") as fh:
        for digest, n in entries:
            fh.write("%s  %s\n" % (digest, n))
    bad = []
    for digest, n in entries:
        if sha256_file(os.path.join(DST, n)) != digest:
            bad.append(n)
    print("copy_registries_r8m2a: copied=%d verify=%s" % (len(entries), "ALL_OK" if not bad else "BAD: " + ",".join(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
