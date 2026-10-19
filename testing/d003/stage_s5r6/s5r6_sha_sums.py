#!/usr/bin/env python3
# s5r6_sha_sums.py -- write the round evidence manifest $EV/SHA256SUMS.txt (AGENTS.md section 7).
# Covers every non-binary evidence file (logs/tsv/txt) except tmp/ (scratch) and safe_run.log (wrapper log).
import os, sys, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r6")
NL = chr(10)


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    files = []
    for root, dirs, fs in os.walk(EV):
        rel_root = os.path.relpath(root, EV)
        dirs[:] = sorted(d for d in dirs if not (rel_root == "." and d == "tmp"))
        for f in sorted(fs):
            rel = os.path.normpath(os.path.join(rel_root, f)) if rel_root != "." else f
            if rel in ("SHA256SUMS.txt", "safe_run.log"):
                continue
            files.append(rel)
    files.sort()
    body = ["# SHA256SUMS.txt -- P05-S5 R6 evidence manifest",
            "# excludes tmp/ (scratch); safe_run.log is kept as the wrapper log and is not listed here"]
    for rel in files:
        body.append(sha_f(os.path.join(EV, rel)) + "  " + rel)
    open(os.path.join(EV, "SHA256SUMS.txt"), "w", encoding="utf-8").write(NL.join(body) + NL)
    print("EVIDENCE items=%d" % len(files))
    for rel in files:
        print("ITEM " + rel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
