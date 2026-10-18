#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# finalize_r9m1r3.py -- Copy end gate files to registries and rewrite registries/SHA256SUMS.txt (Rule §1-6). New file.
import hashlib, os, shutil, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r3"))
REG_DIR = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M1R3")

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            c = fh.read(65536)
            if not c: break
            h.update(c)
    return h.hexdigest()

def main():
    # 1. Copy end gate files from EV to registries
    gate_files = [f for f in os.listdir(EV) if f.startswith("GATE_R9M1R3_end") and f.endswith(".txt")]
    assert len(gate_files) >= 1, f"Expected at least one end gate file in {EV}, found: {gate_files}"

    for gf in gate_files:
        src = os.path.join(EV, gf)
        dst = os.path.join(REG_DIR, gf)
        shutil.copy2(src, dst)
        assert sha256_file(src) == sha256_file(dst), f"Copy sha mismatch for {gf}"
        print(f"Copied gate file -> {dst}")

    # 2. Rewrite registries/SHA256SUMS.txt
    reg_entries = []
    for f in sorted(os.listdir(REG_DIR)):
        if f == "SHA256SUMS.txt": continue
        fp = os.path.join(REG_DIR, f)
        if not os.path.isfile(fp): continue
        sha = sha256_file(fp)
        reg_entries.append((f, sha))

    sums_path = os.path.join(REG_DIR, "SHA256SUMS.txt")
    with open(sums_path, "w", encoding="utf-8") as fh:
        for f, sha in reg_entries:
            fh.write(f"{sha}  {f}\n")

    # Verify each
    for f, sha in reg_entries:
        fp = os.path.join(REG_DIR, f)
        assert sha256_file(fp) == sha, f"Post-write verify failed: {f}"

    print(f"Rewrote and verified {sums_path} ({len(reg_entries)} files all OK).")

if __name__ == "__main__":
    main()
