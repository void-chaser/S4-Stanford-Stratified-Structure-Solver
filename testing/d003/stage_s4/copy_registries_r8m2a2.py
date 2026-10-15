#!/usr/bin/env python3
# copy_registries_r8m2a2.py -- P05-S4 R8 M2a2 section 7.2 & CONT1 section 8.6: copy results to registries/s4r8/M2/r8m2a2/.
# Preserves original filenames (U226). Writes SHA256SUMS.txt in registries dir and verifies all copies.
# Refuses to overwrite any existing file (U17).
import hashlib
import os
import shutil
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
DST = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a2")

INPUTS = [
    "GATE_R8_M2a2_start.txt",
    "STRAY_BASELINE_R8_M2a2.tsv",
    "REUSE_CHECK_R8_M2a2.tsv",
    "REUSE_CHECK_R8_M2a2_R2.tsv",
    "NM_CHECK_R8_M2a2.tsv",
    "NM_CHECK_R8_M2a2_R2.tsv",
    "NM_CHECK_BUF_R8_M2a2_R2.tsv",
    "K1_ANCHOR_R8_M2a2.tsv",
    "M2_DESIGN_R8_M2a2.tsv",
    "M2_DESIGN_R8_M2a2.md",
    "SRC_DIFF_R8_M2a2_driver_layers.txt",
    "SRC_DIFF_R8_M2a2_driver_layers_srcR2.txt",
    "SRC_DIFF_R8_M2a2_inject_dual.txt",
    "SRC_DIFF_R8_M2a2_inject_dual_R2.txt",
    "SRC_DIFF_R8_M2a2_inject_dual_R3.txt",
    "SRC_DIFF_R8_M2a2_inject_dual_R3_base.txt",
    "SRC_DIFF_R8_M2a2_inject_dual_srcR2.txt",
    "SRC_DIFF_R8_M2a2_inject_nan.txt",
    "SRC_DIFF_R8_M2a2_inject_nan_R2.txt",
    "SRC_DIFF_R8_M2a2_inject_nan_srcR2.txt",
    "SRC_DIFF_R8_M2a2_r6c_state_gdb.txt",
    "BUILD_R8_M2a2.tsv",
    "BUILD_R8_M2a2_R2.tsv",
    "BUILD_R8_M2a2_R3.tsv",
    "BUILD_FINAL_R8_M2a2.tsv",
    "BUILD_B_DBG_R8_M2a2.tsv",
    "SAN_PROBE_R8_M2a2.txt",
    "STAGE_E_SEARCH_R8_M2a2.tsv",
    "STAGE_E_SEARCH_R8_M2a2_R2.tsv",
    "CATC_SEARCH_R8_M2a2.tsv",
    "CATC_SEARCH_R8_M2a2_R2.tsv",
    "CATC_SEARCH_R8_M2a2_R2B.tsv",
    "INDEX_DERIVATION_R8_M2a2.tsv",
    "INDEX_DERIVATION_R8_M2a2_R2.tsv",
    "INDEX_DERIVATION_R8_M2a2_R2B.tsv",
    "PREREG_M2_R8_M2a2.tsv",
    "PREREG_M2_R8_M2a2.sha256",
    "PREREG_M2_R8_M2a2_TIMESTAMP_UTC.txt",
    "PREREG_M2_COUNT_R8_M2a2.txt",
    "POSCTRL_M2_R8_M2a2.txt",
    "POSCTRL_M2_R8_M2a2_R2.txt",
    "COMPLETENESS_R8_M2a2.txt",
    "COMPLETENESS_R8_M2a2_R2.txt",
    "REPORT_COUNT_CHECK_R8_M2a2.txt",
    "REPORT_COUNT_CHECK_R8_M2a2_R2.txt",
    "REPORT_COUNT_CHECK_R8_M2a2_R3.txt",
    "RESUME_CHECK_R8_M2a2.tsv",
    "RESUME_CHECK_R8_M2a2_R2.tsv",
    "RESUME_CHECK_R8_M2a2_R3.tsv",
    "DEVIATIONS_R8_M2a2.tsv",
    "HARNESS_NM_R8_M2a2.tsv",
    "APPARATUS_MANIFEST_R8_M2a2.tsv",
    "APPARATUS_MANIFEST_R8_M2a2_R2.tsv",
    "DUAL_HARNESS_R8_M2a2.tsv",
    "M210_BREAKPOINTS_R8_M2a2.tsv",
    "M210_BREAKPOINTS_R8_M2a2_R2.tsv",
    "STATE_BYTES_R8_M2a2.txt",
    "STATE_BYTES_R8_M2a2_R2.txt",
    "STATE_BYTES_R8_M2a2_R3.txt",
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
        print("copy_registries_r8m2a2: REFUSED missing inputs: %s" % ", ".join(missing))
        return 2

    # Verify no target file already exists (U17)
    existing = [n for n in INPUTS if os.path.exists(os.path.join(DST, n))]
    if existing:
        print("copy_registries_r8m2a2: REFUSED existing targets (U17): %s" % ", ".join(existing))
        return 2

    os.makedirs(DST, exist_ok=True)
    entries = []

    for n in INPUTS:
        src = os.path.join(EV, n)
        dst = os.path.join(DST, n)
        shutil.copyfile(src, dst)
        entries.append((sha256_file(src), n))

    # Also include existing files in DST (e.g. BRIEF_M2a2_CONT1.md)
    for extra in sorted(os.listdir(DST)):
        if extra not in INPUTS and extra != "SHA256SUMS.txt" and os.path.isfile(os.path.join(DST, extra)):
            entries.append((sha256_file(os.path.join(DST, extra)), extra))

    entries.sort(key=lambda x: x[1])

    sums_path = os.path.join(DST, "SHA256SUMS.txt")
    if os.path.exists(sums_path):
        print("copy_registries_r8m2a2: REFUSED SHA256SUMS.txt exists in DST")
        return 2

    with open(sums_path, "x", encoding="utf-8") as fh:
        for digest, n in entries:
            fh.write("%s  %s\n" % (digest, n))

    bad = []
    for digest, n in entries:
        if sha256_file(os.path.join(DST, n)) != digest:
            bad.append(n)

    print("copy_registries_r8m2a2: copied=%d total_sums=%d verify=%s" %
          (len(INPUTS), len(entries), "ALL_OK" if not bad else "BAD: " + ",".join(bad)))
    return 0 if not bad else 1

if __name__ == "__main__":
    sys.exit(main())
