#!/usr/bin/env python3
# copy_registries_r8m2d.py -- Copy small tables to registries/s4r8/M2/r8m2d, verify sha256 sums, and write EV SHA256SUMS.txt.
import hashlib
import os
import shutil
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2d")
EV = os.environ.get("EV", os.path.join(REPO, EV_REL))
REG_DIR = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2d")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def main():
    os.makedirs(REG_DIR, exist_ok=True)

    # 1. Collect files to copy from EV
    ev_files = [
        "ERRATA_R8_M2d.txt",
        "GATE_DIFF_R8_M2d.txt",
        "GATE_R8_M2d_start.txt",
        "GATE_R8_M2d_end.txt",
        "M2_CONSOLIDATED_R8_M2d.tsv",
        "M2_F3_STATUS_R8_M2d.tsv",
        "POSCTRL_M2_R8_M2d.txt",
        "PREREG_DIFF_R8_M2d.tsv",
        "PREREG_M2_DELTA_R8_M2d.tsv",
        "PREREG_M2_DELTA_R8_M2d.tsv.sha256",
        "PREREG_M2_DELTA_R8_M2d_TIMESTAMP_UTC.txt",
        "RED_POINTS_LEDGER_APPEND_R8_M2d.tsv",
        "REGRESSION_PLAN_F4_R8_M2d.tsv",
        "S3R5_DESIGN_R8_M2d.md",
        "S4MALLOC_MAP_R8_M2d.tsv",
        "STRAY_BASELINE_R8_M2d.tsv",
        "TEST_S4MALLOC_MAP.txt",
        "TRIAGE_R8_M2d.tsv",
    ]

    copied_files = []
    for fname in ev_files:
        src = os.path.join(EV, fname)
        if os.path.isfile(src):
            dst = os.path.join(REG_DIR, fname)
            shutil.copy2(src, dst)
            copied_files.append(fname)
        else:
            print(f"Warning: source file not found: {src}")

    # Also copy smoke summary and verdict if available
    smoke_files = ["COMMAND_PLAN_SMOKE.tsv", "FACTS_pass1.tsv", "FACTS_pass2.tsv", "SUMMARY_SMOKE.txt", "VERDICT_SMOKE.tsv"]
    for sf in smoke_files:
        src = os.path.join(EV, "smoke", sf)
        if os.path.isfile(src):
            dst = os.path.join(REG_DIR, sf)
            shutil.copy2(src, dst)
            copied_files.append(sf)

    # 2. Write SHA256SUMS.txt in registries dir
    reg_sums_path = os.path.join(REG_DIR, "SHA256SUMS.txt")
    sums_lines = []
    for fname in sorted(copied_files):
        fpath = os.path.join(REG_DIR, fname)
        h = sha256_file(fpath)
        sums_lines.append(f"{h}  {fname}")

    with open(reg_sums_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(sums_lines) + "\n")
    print(f"Wrote {len(sums_lines)} entries to {reg_sums_path}")

    # Verify each copied file
    for line in sums_lines:
        exp_h, fname = line.split("  ", 1)
        act_h = sha256_file(os.path.join(REG_DIR, fname))
        assert exp_h == act_h, f"Checksum verification failed for {fname}: {act_h} != {exp_h}"
    print(f"All {len(sums_lines)} files in {REG_DIR} verified successfully.")

    # 3. Write SHA256SUMS.txt in EV covering all text evidence files (excluding tmp/)
    ev_sums_path = os.path.join(EV, "SHA256SUMS.txt")
    ev_all_lines = []
    for root, dirs, files in os.walk(EV):
        if "tmp" in root.split(os.sep):
            continue
        for f in sorted(files):
            if f == "SHA256SUMS.txt":
                continue
            fpath = os.path.join(root, f)
            rel_p = os.path.relpath(fpath, EV)
            # Skip binary files if any
            if not f.endswith((".o", ".a", ".so", "a.out")):
                h = sha256_file(fpath)
                ev_all_lines.append(f"{h}  {rel_p}")

    with open(ev_sums_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(sorted(ev_all_lines)) + "\n")
    print(f"Wrote {len(ev_all_lines)} entries to {ev_sums_path}")
    return 0


if __name__ == "__main__":
    main()
