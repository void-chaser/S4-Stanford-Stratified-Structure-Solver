#!/usr/bin/env python3
# copy_registries_r9m1r4.py -- Copy small table artifacts to checkpoints/p05/registries/s4r9/M1R4/ (Step S-G). New file.
# Baseline HEAD: 4e9ff8be523bbf52a6b11757a6e04405a4a114e9
import os, sys, shutil, hashlib

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r4"))
REG_DIR = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M1R4")

TABLES = [
    "AUDIT_R9M1R3_R9M1R4.tsv",
    "UNLOGGED_WRITES_R9M1R3.tsv",
    "RECERT_R9M1R3.tsv",
    "EVENTS_RECALC_R9M1R3.tsv",
    "SHA_RECHECK_R9M1R3.tsv",
    "K_RECON_R9M1R4.tsv",
    "M1_RECERT_SUMMARY_R9M1R4.tsv",
    "POSCTRL_RECERT_R9M1R4.txt",
    "FROZEN_SCRIPTS_R9M1R4.tsv",
    "EVENTS_R9M1R4.tsv",
    "GATE_R9M1R4_start_v2.txt",
]

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def main():
    os.makedirs(REG_DIR, exist_ok=True)
    copied = []
    for fname in TABLES:
        src = os.path.join(EV, fname)
        if not os.path.isfile(src):
            src = os.path.join(REPO, fname)
        if os.path.isfile(src):
            dst = os.path.join(REG_DIR, fname)
            shutil.copyfile(src, dst)
            s_sha = sha256_file(src)
            d_sha = sha256_file(dst)
            assert s_sha == d_sha, f"sha mismatch copying {fname}"
            copied.append((fname, d_sha))
        else:
            print(f"Note: table not yet available: {fname}")

    # Write SHA256SUMS.txt
    reg_sums = os.path.join(REG_DIR, "SHA256SUMS.txt")
    copied.sort(key=lambda x: x[0])
    with open(reg_sums, "w", encoding="utf-8") as f:
        for fname, h in copied:
            f.write(f"{h}  {fname}\n")

    print(f"Copied {len(copied)} tables to {REG_DIR} and updated SHA256SUMS.txt.")

if __name__ == "__main__":
    main()
