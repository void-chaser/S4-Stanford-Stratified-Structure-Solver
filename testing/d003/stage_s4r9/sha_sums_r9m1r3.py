#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# sha_sums_r9m1r3.py -- Generate SHA256SUMS.txt for evidence directory (Step S-I, Rule §1-6). New file.
import hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r3"))
OUT_FILE = os.path.join(EV, "SHA256SUMS.txt")

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            c = fh.read(65536)
            if not c: break
            h.update(c)
    return h.hexdigest()

def main():
    entries = []
    safe_log_trunc_sha = ""
    safe_log_trunc_lines = 0

    # Rule §1-6: safe_run.log 单独记录"截至第 N 行的 sha256"
    log_p = os.path.join(EV, "safe_run.log")
    if os.path.isfile(log_p):
        lines = open(log_p, "rb").read().splitlines(keepends=True)
        safe_log_trunc_lines = len(lines)
        h = hashlib.sha256()
        for l in lines:
            h.update(l)
        safe_log_trunc_sha = h.hexdigest()

    for root, dirs, files in os.walk(EV):
        rel_root = os.path.relpath(root, EV)
        if rel_root == "tmp" or rel_root.startswith("tmp/") or rel_root.startswith("tmp\\"):
            continue
        for f in files:
            if f == "SHA256SUMS.txt" or f == "safe_run.log":
                continue
            full_p = os.path.join(root, f)
            if not os.path.isfile(full_p): continue
            rel_p = os.path.relpath(full_p, EV)
            sha = sha256_file(full_p)
            entries.append((rel_p, sha))

    entries.sort()
    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        fh.write(f"# SHA256SUMS.txt -- Evidence file checksums for P05-S4 R9 M1R3 (Rule §1-6)\n")
        fh.write(f"# safe_run.log truncated sha256 up to line {safe_log_trunc_lines}: {safe_log_trunc_sha}\n")
        for rel_p, sha in entries:
            fh.write(f"{sha}  {rel_p}\n")

    print(f"Wrote {OUT_FILE} with {len(entries)} items.")
    print(f"Recorded safe_run.log up to line {safe_log_trunc_lines} sha256: {safe_log_trunc_sha}")

if __name__ == "__main__":
    main()
