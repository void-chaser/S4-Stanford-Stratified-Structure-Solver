#!/usr/bin/env python3
# s5r7_registry.py -- assemble checkpoints/p05/registries/s5r7/ pre-gate (task brief section 5 / AGENTS.md 7).
# Copies GATE_S5R7_start.txt, RULINGS_APPEND_S5R7.tsv (U391 row and sha256 before/after) and
# TMP_SNAPSHOT_S5R7.tsv from the evidence directory, writes SHA256SUMS.txt and verifies every copied sha
# against its source.  The formal end-gate file is added after the gate by s5r7_appendix_c.py, which also
# refreshes this manifest.
import os, sys, hashlib, shutil, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r7")
REG = os.path.join(P05, "registries/s5r7")
TAB = chr(9)
NL = chr(10)

SOURCES = ["GATE_S5R7_start.txt", "RULINGS_APPEND_S5R7.tsv", "TMP_SNAPSHOT_S5R7.tsv"]


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    os.makedirs(REG, exist_ok=True)
    rows = []
    for rel in SOURCES:
        src = os.path.join(EV, rel)
        if not os.path.isfile(src):
            print("HARD_STOP missing source: " + rel)
            return 2
        dst = os.path.join(REG, rel)
        if os.path.realpath(src) != os.path.realpath(dst):
            shutil.copy2(src, dst)
        if sha_f(src) != sha_f(dst):
            print("HARD_STOP registry copy mismatch: " + rel)
            return 2
        rows.append((rel, sha_f(dst)))
    sums = ["# SHA256SUMS.txt -- P05-S5 R7 registry (pure documentation sub-round: P05-S5 sign-off entry)",
            "# the formal end-gate file GATE_S5R7_end.txt is added after the gate and listed below"]
    for rel, sha in rows:
        sums.append(sha + "  " + rel)
    open(os.path.join(REG, "SHA256SUMS.txt"), "w", encoding="utf-8").write(NL.join(sums) + NL)
    print("REGISTRY files=%d listed=%d" % (len(rows) + 1, len(rows)))
    for rel, sha in rows:
        print("COPY " + rel + " " + sha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
