#!/usr/bin/env python3
# copy_registries_r8m2b.py -- Copies small result tables to registries and verifies sha256 sums (Section 5 S-H).
# Never renames files. Strictly compares sha256 before and after copy.
import hashlib
import os
import shutil
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2b"))
REG_DIR = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2b")


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
    mismatches = 0

    # List of files in EV root to copy
    for fname in sorted(os.listdir(EV)):
        fpath = os.path.join(EV, fname)
        if os.path.isfile(fpath) and not fname.startswith(".") and fname != "SHA256SUMS.txt":
            # Check file size < 1MB
            sz = os.path.getsize(fpath)
            if sz > 1048576:
                print(f"SKIP (size > 1MB): {fname} ({sz} bytes)")
                continue

            dest = os.path.join(REG_DIR, fname)
            shutil.copy2(fpath, dest)
            s_orig = sha256_file(fpath)
            s_dest = sha256_file(dest)
            if s_orig != s_dest:
                print(f"FATAL SHA MISMATCH: {fname}: {s_orig} != {s_dest}")
                mismatches += 1
            else:
                copied += 1

    if mismatches != 0:
        sys.exit(f"FATAL: {mismatches} copy sha256 mismatches detected!")

    # Write SHA256SUMS.txt in registries
    sums_lines = []
    for fname in sorted(os.listdir(REG_DIR)):
        fpath = os.path.join(REG_DIR, fname)
        if os.path.isfile(fpath) and fname != "SHA256SUMS.txt":
            sh = sha256_file(fpath)
            sums_lines.append(f"{sh}  {fname}")

    sums_path = os.path.join(REG_DIR, "SHA256SUMS.txt")
    with open(sums_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(sums_lines) + "\n")

    # Also write SHA256SUMS.txt in evidence directory
    ev_sums_lines = []
    for root, dirs, files in os.walk(EV):
        if "tmp" in dirs:
            dirs.remove("tmp")
        for f in files:
            if f.endswith(".txt") or f.endswith(".tsv") or f.endswith(".md") or f.endswith(".sha256") or f.endswith(".log"):
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, EV)
                if rel != "SHA256SUMS.txt":
                    sh = sha256_file(fp)
                    ev_sums_lines.append(f"{sh}  {rel}")

    ev_sums_lines.sort(key=lambda x: x.split()[-1])
    with open(os.path.join(EV, "SHA256SUMS.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(ev_sums_lines) + "\n")

    print(f"copy_registries: copied {copied} files to {REG_DIR} with 0 sha mismatches.")
    print(f"Registries SHA256SUMS written: {len(sums_lines)} entries.")
    print(f"Evidence SHA256SUMS written: {len(ev_sums_lines)} entries.")


if __name__ == "__main__":
    main()
