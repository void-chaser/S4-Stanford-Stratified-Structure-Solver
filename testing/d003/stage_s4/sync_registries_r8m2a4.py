#!/usr/bin/env python3
# sync_registries_r8m2a4.py -- Sync small tables from evidence to registries and write SHA256SUMS.txt.
import hashlib
import os
import shutil
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a4"))
REG_DIR = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a4")

TABLES = [
    "COMMAND_PLAN_R8_M2a4.tsv",
    "COMPLETENESS_R8_M2a4.tsv",
    "COMPLETENESS_SUMMARY_R8_M2a4.txt",
    "ERRATA_APPEND_R8_M2a4.txt",
    "GATE_DIFF_R8_M2a4.txt",
    "GATE_R8_M2a4_start.txt",
    "INVARIANT_SPEC_R8_M2a4.md",
    "POSCTRL_M2_R8_M2a4.txt",
    "POSCTRL_M2_R8_M2a4_R2.txt",
    "POSCTRL_M2_R8_M2a4_R3.txt",
    "POSCTRL_M2_R8_M2a4_R4.txt",
    "PREREG_DIFF_R8_M2a4.tsv",
    "PREREG_M2_EFFECTIVE_R8_M2a4.tsv",
    "PREREG_M2_EFFECTIVE_R8_M2a4.tsv.sha256",
    "PREREG_M2_EFFECTIVE_R8_M2a4_TIMESTAMP_UTC.txt",
    "REPLAY_R6c_R8_M2a4.tsv",
    "REPLAY_R6c_SUMMARY_R8_M2a4.txt",
    "RESULTS_R6c_REPLAY_RAW.tsv",
    "RULINGS_APPEND_R8_M2a4.tsv",
    "SRC_DIFF_STATE_JUDGE_R8_M2a4.txt",
    "STATE_SUMMARY_R6c_REPLAY_RAW.txt",
    "STRAY_BASELINE_R8_M2a4.tsv",
    "VERDICT_AUDIT_R8_M2a4.tsv",
    "WIN64_DIAG_PLAN_R8_M2a4.md",
]


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

    copied = 0
    sums_lines = []

    # Copy tables to registry without renaming
    for name in sorted(TABLES):
        src = os.path.join(EV, name)
        dst = os.path.join(REG_DIR, name)
        if not os.path.isfile(src):
            print(f"WARNING: source not found: {name}")
            continue
        src_sha = sha256_file(src)
        shutil.copy2(src, dst)
        dst_sha = sha256_file(dst)
        if src_sha != dst_sha:
            sys.exit(f"FATAL: sha mismatch after copy for {name}: {src_sha} != {dst_sha}")
        sums_lines.append(f"{dst_sha}  {name}\n")
        copied += 1

    # If GATE_R8_M2a4_end.txt exists, include it
    end_gate = os.path.join(EV, "GATE_R8_M2a4_end.txt")
    if os.path.isfile(end_gate):
        dst = os.path.join(REG_DIR, "GATE_R8_M2a4_end.txt")
        shutil.copy2(end_gate, dst)
        dst_sha = sha256_file(dst)
        sums_lines.append(f"{dst_sha}  GATE_R8_M2a4_end.txt\n")
        copied += 1

    sums_lines.sort(key=lambda x: x.split()[1])

    reg_sums_path = os.path.join(REG_DIR, "SHA256SUMS.txt")
    with open(reg_sums_path, "w", encoding="utf-8") as fh:
        fh.writelines(sums_lines)

    # Also generate evidence SHA256SUMS.txt covering all non-dir files in EV
    ev_sums = []
    for fname in sorted(os.listdir(EV)):
        fpath = os.path.join(EV, fname)
        if os.path.isfile(fpath) and fname != "SHA256SUMS.txt":
            ev_sums.append(f"{sha256_file(fpath)}  {fname}\n")

    ev_sums_path = os.path.join(EV, "SHA256SUMS.txt")
    with open(ev_sums_path, "w", encoding="utf-8") as fh:
        fh.writelines(ev_sums)

    print(f"sync_registries_r8m2a4: copied {copied} tables to {REG_DIR}.")
    print(f"Written {reg_sums_path} ({len(sums_lines)} entries).")
    print(f"Written {ev_sums_path} ({len(ev_sums)} entries).")


if __name__ == "__main__":
    main()
