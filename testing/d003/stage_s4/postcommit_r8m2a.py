#!/usr/bin/env python3
# postcommit_r8m2a.py -- P05-S4 R8 M2a post-commit record (run AFTER commit_r8m2a.sh; never before).
# Writes $EV/POSTCOMMIT_R8_M2a.txt: HEAD, HEAD:S4, git status, and the sha256 of the prereg, posctrl and count files.
# Refuses to overwrite (U17).  Reads only; creates no other file.
import hashlib
import os
import subprocess
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a")
OUT = os.path.join(EV, "POSTCOMMIT_R8_M2a.txt")


def git(*args):
    return subprocess.check_output(["git"] + list(args), cwd=REPO, text=True).strip()


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main():
    if os.path.exists(OUT):
        print("postcommit_r8m2a: REFUSED exists (U17): %s" % OUT)
        return 2
    lines = []
    lines.append("HEAD=%s" % git("rev-parse", "HEAD"))
    lines.append("HEAD_S4=%s" % git("rev-parse", "HEAD:S4"))
    lines.append("LOG=%s" % git("log", "-1", "--format=%H%n%s").replace("\n", " | "))
    st = git("status", "--short")
    lines.append("STATUS=%s" % ("EMPTY" if st == "" else st.replace("\n", " | ")))
    for name in ("PREREG_M2_R8_M2a_R2.tsv", "PREREG_M2_R8_M2a_R2.sha256", "PREREG_M2_COUNT_R8_M2a_R2.txt",
                 "POSCTRL_M2_R8_M2a_R2.txt", "M2_DESIGN_R8_M2a_R2.tsv"):
        path = os.path.join(EV, name)
        if os.path.isfile(path):
            lines.append("SHA256 %s=%s" % (name, sha256_file(path)))
        else:
            lines.append("MISSING %s" % name)
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
