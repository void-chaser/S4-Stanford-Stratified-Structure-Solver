#!/usr/bin/env python3
# copy_registries_r8m2c.py -- Copy small tables to registries/s4r8/M2/r8m2c/ and generate SHA256SUMS.txt.
import hashlib, os, shutil, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2c")
EV = os.environ.get("EV", os.path.join(REPO, EV_REL))
REG_DIR = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2c")

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

    # 1. Identify small tables to copy
    files = sorted([f for f in os.listdir(EV) if os.path.isfile(os.path.join(EV, f)) and f != "safe_run.log" and f != "SHA256SUMS.txt"])
    print(f"Copying {len(files)} files from {EV} to {REG_DIR}...")

    copied = []
    for f in files:
        src = os.path.join(EV, f)
        dst = os.path.join(REG_DIR, f)
        shutil.copy2(src, dst)
        src_sha = sha256_file(src)
        dst_sha = sha256_file(dst)
        assert src_sha == dst_sha, f"SHA mismatch on {f}: {src_sha} != {dst_sha}"
        copied.append((dst_sha, f))

    # 2. Write SHA256SUMS.txt in registries
    reg_sums_path = os.path.join(REG_DIR, "SHA256SUMS.txt")
    with open(reg_sums_path, "w", encoding="utf-8") as fh:
        fh.write(f"# SHA256SUMS -- checkpoints/p05/registries/s4r8/M2/r8m2c/\n")
        for sha, fname in sorted(copied, key=lambda x: x[1]):
            fh.write(f"{sha}  {fname}\n")
    print(f"Wrote {reg_sums_path} ({len(copied)} entries).")

    # Verify back
    for sha, fname in copied:
        act_sha = sha256_file(os.path.join(REG_DIR, fname))
        assert sha == act_sha, f"Verification failed for {fname}"
    print("Registries SHA256SUMS.txt verified 100% OK.")

    # 3. Write SHA256SUMS.txt in evidence directory
    ev_files = []
    for root, dirs, fnames in os.walk(EV):
        if root.startswith(os.path.join(EV, "tmp")):
            continue
        if root.startswith(os.path.join(EV, "build")):
            continue # binary executables / libraries
        for fn in fnames:
            if fn in ("SHA256SUMS.txt", "safe_run.log"):
                continue
            full_p = os.path.join(root, fn)
            rel_p = os.path.relpath(full_p, EV)
            # only hash regular text / tsv / log / txt files
            if os.path.isfile(full_p):
                ev_files.append((sha256_file(full_p), rel_p))

    ev_sums_path = os.path.join(EV, "SHA256SUMS.txt")
    with open(ev_sums_path, "w", encoding="utf-8") as fh:
        fh.write(f"# SHA256SUMS -- checkpoints/p05/evidence/p05-s4r8/m2c/\n")
        for sha, rel_p in sorted(ev_files, key=lambda x: x[1]):
            fh.write(f"{sha}  {rel_p}\n")
    print(f"Wrote {ev_sums_path} ({len(ev_files)} entries).")

    return 0

if __name__ == "__main__":
    sys.exit(main())
