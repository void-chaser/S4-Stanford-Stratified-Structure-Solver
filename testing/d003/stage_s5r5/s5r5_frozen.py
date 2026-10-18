#!/usr/bin/env python3
# s5r5_frozen.py -- write the frozen-script list of P05-S5 R5 (task brief section 7: freeze starts after commit (i)).
# Every *.py of testing/d003/stage_s5r5/ (including this generator and the end gate) is listed with its sha256;
# the end gate re-verifies every listed sha, so a post-freeze script edit would fail the formal gate.
import os, sys, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r5")
STAGE = os.path.join(REPO, "testing/d003/stage_s5r5")
TAB = chr(9)
NL = chr(10)


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    files = sorted(f for f in os.listdir(STAGE) if f.endswith(".py"))
    rows = []
    for f in files:
        p = os.path.join(STAGE, f)
        rows.append((os.path.relpath(p, REPO), sha_f(p)))
    out = os.path.join(EV, "FROZEN_SCRIPTS_S5R5.tsv")
    body = ["# FROZEN_SCRIPTS_S5R5.tsv -- P05-S5 R5 frozen scripts (every *.py of testing/d003/stage_s5r5/)",
            "# freeze begins after record commit (i); the end gate re-verifies these sha256 values",
            TAB.join(["path", "sha256", "mode"])]
    for (rel, sha) in rows:
        body.append(TAB.join([rel, sha, "-"]))
    open(out, "w", encoding="utf-8").write(NL.join(body) + NL)
    print("FROZEN rows=%d" % len(rows))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
