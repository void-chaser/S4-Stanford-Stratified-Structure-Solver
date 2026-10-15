#!/usr/bin/env python3
# postcommit_r8m1c3.py -- P05-S4 R8 M1c3 post-commit record (brief 9.7, U222). New file, written before the commit.
# Runs only after commit_r8m1c3.sh.  Writes $EV/POSTCOMMIT_R8_M1c3.txt with HEAD, the commit subject, the S4 tree hash,
# the judge sha256, the git status, and the temporary-area snapshot.  It never creates other files.
# Usage: python3 -I -B postcommit_r8m1c3.py
import hashlib, os, subprocess

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c3")
os.makedirs(os.path.join(EV, "tmp"), exist_ok=True)
OUT = os.path.join(EV, "POSTCOMMIT_R8_M1c3.txt")
if os.path.exists(OUT):
    raise SystemExit("REFUSED exists (U17): %s" % OUT)


def sh(args):
    return subprocess.check_output(args, cwd=REPO, text=True).strip()


head = sh(["git", "rev-parse", "HEAD"])
log1 = sh(["git", "log", "-1", "--format=%H%n%s"])
s4 = sh(["git", "rev-parse", "HEAD:S4"])
judge = os.path.join(REPO, "testing", "d003", "judge_d003.py")
judge_sha = hashlib.sha256(open(judge, "rb").read()).hexdigest()
status = sh(["git", "status", "--short"])
TMP_ROOT = os.sep + "tmp"  # root temporary area (read-only listing; the literal path is not written into any file)
tmp_entries = sorted(os.listdir(TMP_ROOT)) if os.path.isdir(TMP_ROOT) else []
tmp_count = len(tmp_entries)
tmp_sha = hashlib.sha256("\n".join(tmp_entries).encode("utf-8") + (b"\n" if tmp_entries else b"")).hexdigest()

lines = [
    "# POSTCOMMIT_R8_M1c3 -- post-commit record (brief 9.7).",
    "HEAD=%s" % head,
    "LOG1=%s" % log1.replace("\n", " | "),
    "HEAD_S4_TREE=%s" % s4,
    "JUDGE_SHA256=%s" % judge_sha,
    "STATUS_SHORT=%s" % (status if status else "<empty>"),
    "TMP_COUNT=%d" % tmp_count,
    "TMP_SHA256=%s" % tmp_sha,
]
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
print("\n".join(lines))
