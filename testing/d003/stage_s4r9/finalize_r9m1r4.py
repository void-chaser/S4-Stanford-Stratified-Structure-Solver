#!/usr/bin/env python3
# finalize_r9m1r4.py -- Closeout finalization script for P05-S4 R9 M1R4 (Step S-G). New file.
# Baseline HEAD: 4e9ff8be523bbf52a6b11757a6e04405a4a114e9
import os, sys, shutil, hashlib, subprocess

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r4"))
REG_DIR = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M1R4")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def main():
    # 1. Copy gate files into registries
    for gname in ["GATE_R9M1R4_end.txt", "GATE_R9M1R4_start_v2.txt"]:
        src = os.path.join(EV, gname)
        if os.path.isfile(src):
            dst = os.path.join(REG_DIR, gname)
            shutil.copyfile(src, dst)
            assert sha256_file(src) == sha256_file(dst)
            print(f"Copied {gname} to registries.")

    # 2. Re-write registries SHA256SUMS.txt
    entries = []
    for f in os.listdir(REG_DIR):
        if f == "SHA256SUMS.txt": continue
        fp = os.path.join(REG_DIR, f)
        if os.path.isfile(fp):
            entries.append((f, sha256_file(fp)))

    entries.sort(key=lambda x: x[0])
    sums_file = os.path.join(REG_DIR, "SHA256SUMS.txt")
    with open(sums_file, "w", encoding="utf-8") as f:
        for fname, h in entries:
            f.write(f"{h}  {fname}\n")

    # 3. Verify sha256sum -c SHA256SUMS.txt
    proc = subprocess.run(["sha256sum", "-c", "SHA256SUMS.txt"], cwd=REG_DIR, capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"Finalize check failed: {proc.stderr}", file=sys.stderr)
        sys.exit(1)

    print(f"Finalize complete: {len(entries)} items verified in {REG_DIR}/SHA256SUMS.txt.")

if __name__ == "__main__":
    main()
