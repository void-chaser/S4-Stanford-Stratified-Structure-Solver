#!/usr/bin/env python3
# postcommit_r8m2a4.py -- P05-S4 R8 M2a4 post-commit record (run AFTER commit_r8m2a4.sh; never before).
# Writes $EV/POSTCOMMIT_R8_M2a4.txt: HEAD, HEAD:S4, git status, and sha256 of key registries.
# Refuses to overwrite (U17). Reads only; creates no other file.
import hashlib
import os
import subprocess
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a4")
REG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a4")
OUT = os.path.join(EV, "POSTCOMMIT_R8_M2a4.txt")


def git(*args):
    return subprocess.check_output(["git"] + list(args), cwd=REPO, text=True).strip()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if os.path.exists(OUT):
        print("postcommit_r8m2a4: REFUSED exists (U17): %s" % OUT)
        return 2
    lines = []
    lines.append("HEAD=%s" % git("rev-parse", "HEAD"))
    lines.append("HEAD_S4=%s" % git("rev-parse", "HEAD:S4"))
    lines.append("LOG=%s" % git("log", "-1", "--format=%H%n%s").replace("\n", " | "))
    st = git("status", "--short")
    lines.append("STATUS=%s" % ("EMPTY" if st == "" else st.replace("\n", " | ")))

    key_tables = [
        "PREREG_M2_EFFECTIVE_R8_M2a4.tsv",
        "PREREG_M2_EFFECTIVE_R8_M2a4.tsv.sha256",
        "PREREG_DIFF_R8_M2a4.tsv",
        "COMMAND_PLAN_R8_M2a4.tsv",
        "COMPLETENESS_R8_M2a4.tsv",
        "VERDICT_AUDIT_R8_M2a4.tsv",
        "WIN64_DIAG_PLAN_R8_M2a4.md",
        "INVARIANT_SPEC_R8_M2a4.md",
        "POSCTRL_M2_R8_M2a4_R4.txt",
        "REPLAY_R6c_R8_M2a4.tsv",
        "GATE_R8_M2a4_end.txt",
    ]
    for name in key_tables:
        path = os.path.join(REG, name)
        if os.path.isfile(path):
            lines.append("SHA256 %s=%s" % (name, sha256_file(path)))
        else:
            lines.append("MISSING %s in %s" % (name, REG))

    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
