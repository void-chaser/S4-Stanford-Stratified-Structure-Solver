#!/usr/bin/env python3
# s5r5_sha_sums.py -- write the round evidence manifest $EV/SHA256SUMS.txt (AGENTS.md section 7).
# Covers every non-binary evidence file (logs/tsv/txt) except the transient trees documented in the header:
# tmp/ (scratch), gate/ (gate outputs are recorded in the registries and the report), shakedown/ (staging
# copies), posctrl/gate/ + posctrl/gate_out/ (transient mutation fixtures; their summary is POSCTRL_GATE_S5R5.txt).
import os, sys, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r5")
EXCLUDE_DIRS = ("tmp", "gate", "shakedown", "trees")
EXCLUDE_PREFIX = ("posctrl/gate/", "posctrl/gate_out/")
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
        dirs[:] = sorted(d for d in dirs if not (rel_root == "." and d in EXCLUDE_DIRS))
        for f in sorted(fs):
            rel = os.path.normpath(os.path.join(rel_root, f)) if rel_root != "." else f
            if rel in ("SHA256SUMS.txt", "safe_run.log"):
                continue
            if any(rel.startswith(p) for p in EXCLUDE_PREFIX):
                continue
            files.append(rel)
    files.sort()
    body = ["# SHA256SUMS.txt -- P05-S5 R5 evidence manifest",
            "# excludes tmp/, gate/, shakedown/, trees/ and the transient mutation fixtures posctrl/gate/ + posctrl/gate_out/",
            "# safe_run.log is kept as the wrapper log and is not listed here"]
    for rel in files:
        body.append(sha_f(os.path.join(EV, rel)) + "  " + rel)
    open(os.path.join(EV, "SHA256SUMS.txt"), "w", encoding="utf-8").write(NL.join(body) + NL)
    print("EVIDENCE items=%d" % len(files))
    print("WROTE " + os.path.relpath(os.path.join(EV, "SHA256SUMS.txt"), REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
