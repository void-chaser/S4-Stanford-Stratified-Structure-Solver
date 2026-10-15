#!/usr/bin/env python3
# postcommit_r8m1c2.py -- writes the post-commit git log -1 and git status --short to $EV/POSTCOMMIT_R8_M1c2.txt
# (evidence only; not committed).  Brief section 8.6.
# Usage: python3 -I -B postcommit_r8m1c2.py
import os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c2")
OUT = os.path.join(EV, "POSTCOMMIT_R8_M1c2.txt")
if os.path.exists(OUT):
    print("REFUSED exists (U17): %s" % OUT)
    sys.exit(2)


def run(args):
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True).stdout


log1 = run(["git", "log", "-1"])
st = run(["git", "status", "--short"])
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("# POSTCOMMIT_R8_M1c2 (evidence only; not committed)\n")
    fh.write("## git log -1\n")
    fh.write(log1)
    fh.write("## git status --short\n")
    fh.write(st if st else "(empty)\n")
print(log1.strip())
print("STATUS=%s" % ("EMPTY" if not st.strip() else "NONEMPTY"))
