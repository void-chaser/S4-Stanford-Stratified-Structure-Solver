#!/usr/bin/env python3
# sha_sums_r9m3b.py -- evidence SHA256SUMS with a truncation header for the log prefix. New file (r9m3b).
# usage: python3 -I -B testing/d003/stage_s4r9/sha_sums_r9m3b.py
import os, sys, hashlib

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b")
NL = chr(10)
SKIP = ("SHA256SUMS.txt", "safe_run.log")
SKIP_DIRS = ("trees", "tmp", "runs", "shakedown", "posctrl")


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
    log = os.path.join(EV, "safe_run.log")
    lines = open(log, encoding="utf-8", errors="replace").read().splitlines()
    n = len(lines)
    log_sha = hashlib.sha256((NL.join(lines) + NL).encode("utf-8")).hexdigest()
    items = []
    for root, dirs, files in os.walk(EV):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            if f in SKIP:
                continue
            fp = os.path.join(root, f)
            items.append((sha(fp), os.path.relpath(fp, EV)))
    items.sort(key=lambda x: x[1])
    out = os.path.join(EV, "SHA256SUMS.txt")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# SHA256SUMS.txt -- evidence manifest for P05-S4 R9 M3b (trees/, tmp/, runs/, shakedown/, posctrl/ hold exported trees and raw run records; their sha256 are recorded in E2E_BUILD/VERDICT tables)" + NL)
        fh.write("# safe_run.log up to line %d: %s" % (n, log_sha) + NL)
        for h, name in items:
            fh.write("%s  %s" % (h, name) + NL)
    print("log_lines=%d log_sha=%s items=%d" % (n, log_sha, len(items)))
    print("WROTE " + out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
