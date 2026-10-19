#!/usr/bin/env python3
# s5r6_registry.py -- assemble checkpoints/p05/registries/s5r6/ (task brief section 5 / AGENTS.md section 7).
# Copies the pre-gate small tables from the evidence directory, writes SHA256SUMS.txt and verifies every
# copied sha against its source. There is no RULINGS_APPEND_S5R6.tsv: no user sign-off text was given, so
# U391 was not written and RULINGS.tsv is unchanged. The formal end-gate file is appended after the gate
# by s5r6_appendix_c.py, which also updates this manifest.
import os, sys, hashlib, shutil, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r6")
REG = os.path.join(P05, "registries/s5r6")
TAB = chr(9)
NL = chr(10)

SOURCES = {
    "GATE_S5R6_start.txt": os.path.join(EV, "GATE_S5R6_start.txt"),
    "ERRATA_APPEND_S5R6.tsv": os.path.join(EV, "ERRATA_APPEND_S5R6.tsv"),
    "TMP_SNAPSHOT_S5R6.tsv": os.path.join(EV, "TMP_SNAPSHOT_S5R6.tsv"),
}


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    os.makedirs(REG, exist_ok=True)
    rows = []
    for rel, src in SOURCES.items():
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
    sums = ["# SHA256SUMS.txt -- P05-S5 R6 registry (pure documentation sub-round)",
            "# RULINGS_APPEND_S5R6.tsv is absent on purpose: no user sign-off text -> U391 not written",
            "# the formal end-gate file GATE_S5R6_end.txt is appended after the gate and added below"]
    for rel, sha in rows:
        sums.append(sha + "  " + rel)
    open(os.path.join(REG, "SHA256SUMS.txt"), "w", encoding="utf-8").write(NL.join(sums) + NL)
    print("REGISTRY files=%d listed=%d" % (len(rows) + 1, len(rows)))
    for rel, sha in rows:
        print("COPY " + rel + " " + sha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
