#!/usr/bin/env python3
# s5r4_sha_sums.py -- SHA256SUMS.txt for the S5R4 evidence directory; MUST be the last write to $EV before
# the end gate (task brief section 3). The header records the safe_run.log line of this call and the sha256 of
# the log prefix, so the end gate can prove that nothing was written after it.
# Excluded: tmp/, gate/, trees/, shakedown/, safe_run.log, SHA256SUMS.txt itself.
# usage: s5r4_sha_sums.py formal [--ev-root DIR]
import os, sys, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV4_REAL = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r4")
NL = chr(10)


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode != "formal":
        print("usage: s5r4_sha_sums.py formal [--ev-root DIR]", file=sys.stderr)
        return 2
    EV = os.path.abspath(sys.argv[sys.argv.index("--ev-root") + 1]) if "--ev-root" in sys.argv else EV4_REAL
    ls = open(os.path.join(EV4_REAL, "safe_run.log"), encoding="utf-8").read().splitlines()
    anchor = 0
    for i in range(len(ls), 0, -1):
        if "s5r4_sha_sums.py formal" in ls[i - 1]:
            anchor = i
            break
    if anchor <= 0:
        print("HARD_STOP no sha_sums anchor")
        return 2
    th = hashlib.sha256((NL.join(ls[:anchor]) + NL).encode("utf-8")).hexdigest()
    items = []
    for root, dirs, files in os.walk(EV):
        dirs[:] = sorted(d for d in dirs if d not in ("tmp", "gate", "trees", "shakedown"))
        for f in sorted(files):
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, EV)
            if rel in ("safe_run.log", "SHA256SUMS.txt"):
                continue
            items.append((sha_f(fp), rel))
    body = ["# SHA256SUMS.txt -- P05-S5 R4 evidence manifest (excludes tmp/, gate/, trees/, shakedown/)",
            "# safe_run.log up to line %d: %s" % (anchor, th)] + ["%s  %s" % (h, rel) for h, rel in items]
    out = os.path.join(EV, "SHA256SUMS.txt")
    open(out, "w", encoding="utf-8").write(NL.join(body) + NL)
    print("SHA256SUMS %d items trunc_line=%d" % (len(items), anchor))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
