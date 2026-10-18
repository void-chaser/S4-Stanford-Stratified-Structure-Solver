#!/usr/bin/env python3
# sha_sums_r9m3d.py -- evidence SHA256SUMS with a truncation header for the log prefix. New file (r9m3d).
# Coverage: every text file under $EV except SHA256SUMS.txt files, safe_run.log, and the directories tmp/ and
# gate/ (the end-gate output directory is excluded by the task book). The formal call must be the last write
# anywhere under $EV. usage: sha_sums_r9m3d.py [OUT.txt]
import os, sys, hashlib
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3d")
NL = chr(10)
SKIP_NAMES = ("SHA256SUMS.txt", "safe_run.log")
SKIP_DIRS = ("tmp", "gate")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            b = fh.read(65536)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EV, "SHA256SUMS.txt")
    log = os.path.join(EV, "safe_run.log")
    lines = open(log, encoding="utf-8", errors="replace").read().splitlines()
    n = len(lines)
    log_sha = hashlib.sha256((NL.join(lines) + NL).encode("utf-8")).hexdigest()
    ev_abs = os.path.abspath(EV)
    out_abs = os.path.abspath(out)
    items = []
    for root, dirs, files in os.walk(EV):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            if f in SKIP_NAMES:
                continue
            fp = os.path.join(root, f)
            if os.path.abspath(fp) == out_abs:
                continue
            items.append((sha(fp), os.path.relpath(fp, EV)))
    items.sort(key=lambda x: x[1])
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# SHA256SUMS.txt -- evidence manifest for P05-S4 R9 M3d (only gate/ and tmp/ are excluded;"
                 " shakedown/ and posctrl/ raw records ARE covered)" + NL)
        fh.write("# safe_run.log up to line %d: %s" % (n, log_sha) + NL)
        for h, name in items:
            fh.write("%s  %s" % (h, name) + NL)
        fh.write("# UNIQUE=%d ROWS=%d" % (len(items), len(items)) + NL)
    print("log_lines=%d log_sha=%s items=%d" % (n, log_sha, len(items)))
    print("WROTE " + out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
