#!/usr/bin/env python3
# copy_registries_r8m2a3.py -- P05-S4 R8 M2a3 Section 9: copy small tables to registries/s4r8/M2/r8m2a3/.
# Preserves original filenames (U226). Writes SHA256SUMS.txt in registries dir and verifies all copies.
# Refuses to overwrite any existing file (U17).
import hashlib
import os
import shutil
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a3")
DST = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a3")

INPUTS = [
    "GATE_R8_M2a3_start.txt",
    "GATE_DIFF_R8_M2a3.txt",
    "STRAY_BASELINE_R8_M2a3.tsv",
    "PREREG_EXECUTABILITY_AUDIT_R8_M2a3.tsv",
    "PREREG_M2_EFFECTIVE_R8_M2a3.tsv",
    "PREREG_M2_EFFECTIVE_R8_M2a3.tsv.sha256",
    "PREREG_M2_EFFECTIVE_R8_M2a3_TIMESTAMP_UTC.txt",
    "PREREG_DIFF_R8_M2a3.tsv",
    "CONTROL_MAPPING_R8_M2a3.tsv",
    "INVARIANT_SPEC_R8_M2a3.md",
    "STATE_COLLECTION_PLAN_R8_M2a3.tsv",
    "POSCTRL_M2_R8_M2a3.txt",
    "POSCTRL_M2_R8_M2a3_R2.txt",
    "COMPLETENESS_R8_M2a3.tsv",
    "ERRATA_APPEND_R8_M2a3.txt",
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    missing = [n for n in INPUTS if not os.path.isfile(os.path.join(EV, n))]
    if missing:
        print("copy_registries_r8m2a3: REFUSED missing inputs: %s" % ", ".join(missing))
        return 2

    existing = [n for n in INPUTS if os.path.exists(os.path.join(DST, n))]
    if existing:
        print("copy_registries_r8m2a3: REFUSED existing targets (U17): %s" % ", ".join(existing))
        return 2

    os.makedirs(DST, exist_ok=True)
    entries = []

    for n in INPUTS:
        src = os.path.join(EV, n)
        dst = os.path.join(DST, n)
        shutil.copyfile(src, dst)
        entries.append((sha256_file(src), n))

    for extra in sorted(os.listdir(DST)):
        if extra not in INPUTS and extra != "SHA256SUMS.txt" and os.path.isfile(os.path.join(DST, extra)):
            entries.append((sha256_file(os.path.join(DST, extra)), extra))

    entries.sort(key=lambda x: x[1])

    sums_path = os.path.join(DST, "SHA256SUMS.txt")
    if os.path.exists(sums_path):
        print("copy_registries_r8m2a3: REFUSED SHA256SUMS.txt exists in DST")
        return 2

    with open(sums_path, "x", encoding="utf-8") as fh:
        for digest, n in entries:
            fh.write("%s  %s\n" % (digest, n))

    bad = []
    for digest, n in entries:
        if sha256_file(os.path.join(DST, n)) != digest:
            bad.append(n)

    print("copy_registries_r8m2a3: copied=%d total_sums=%d verify=%s" %
          (len(INPUTS), len(entries), "ALL_OK" if not bad else "BAD: " + ",".join(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
