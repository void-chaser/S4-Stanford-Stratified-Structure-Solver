#!/usr/bin/env python3
# sha_sums_r9m1r4.py -- Generate SHA256SUMS.txt for evidence directory (Step S-G). New file.
# Baseline HEAD: 4e9ff8be523bbf52a6b11757a6e04405a4a114e9
import os, sys, hashlib

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r4"))
OUT_FILE = os.path.join(EV, "SHA256SUMS.txt")
LOG_PATH = os.path.join(EV, "safe_run.log")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def main():
    if not os.path.isfile(LOG_PATH):
        print(f"safe_run.log missing at {LOG_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(LOG_PATH, "r", encoding="utf-8") as f:
        log_lines_raw = f.read().splitlines(True)
    
    # safe_run.log lines up to the start of this command (all currently flushed lines)
    trunc_n = len(log_lines_raw)
    first_n_bytes = "".join(log_lines_raw[:trunc_n]).encode("utf-8")
    trunc_sha = hashlib.sha256(first_n_bytes).hexdigest()

    entries = []
    for root, dirs, files in os.walk(EV):
        for f in files:
            if f in ("SHA256SUMS.txt", "safe_run.log"):
                continue
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, EV)
            entries.append((rel, sha256_file(fp)))

    entries.sort(key=lambda x: x[0])

    with open(OUT_FILE, "w", encoding="utf-8") as out:
        out.write("# SHA256SUMS.txt -- Evidence file checksums for P05-S4 R9 M1R4 (Rule §1-6)\n")
        out.write(f"# safe_run.log truncated sha256 up to line {trunc_n}: {trunc_sha}\n")
        for rel, h in entries:
            out.write(f"{h}  {rel}\n")

    print(f"Wrote SHA256SUMS.txt ({len(entries)} items, safe_run.log truncated to line {trunc_n}).")

if __name__ == "__main__":
    main()
