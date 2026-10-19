#!/usr/bin/env python3
# relr3_sha_sums.py -- write $EV/SHA256SUMS.txt for P05 delivery round REL-R3 (AGENTS.md section 7.2).
# Scope: every non-binary evidence file under $EV (root *.txt/*.tsv/*.log/*.md plus logs/*), EXCEPT:
#   safe_run.log            (appended by every safe_run call, so not static)
#   GATE_RELR3_pre.txt      (produced by the pre-run of the end gate, recorded in the report appendix C)
#   GATE_RELR3_end.txt      (produced by the formal end gate itself, recorded in the registry and appendix C)
#   SHA256SUMS.txt          (this file)
# The clone directory (remoteclone/) and tmp/ are not files and are not listed; the clone is recorded by
# HEAD/sha in REMOTE_CLONE_RELR3.tsv.  No binary is hashed into git.
import os, sys, hashlib, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r3")
OUT = os.path.join(EV, "SHA256SUMS.txt")
EXCLUDE = ("safe_run.log", "GATE_RELR3_pre.txt", "GATE_RELR3_end.txt", "SHA256SUMS.txt")
EXTS = (".txt", ".tsv", ".log", ".md")


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    names = []
    for name in sorted(os.listdir(EV)):
        p = os.path.join(EV, name)
        if os.path.isfile(p) and name not in EXCLUDE and name.endswith(EXTS):
            names.append(name)
    logd = os.path.join(EV, "logs")
    if os.path.isdir(logd):
        for name in sorted(os.listdir(logd)):
            if os.path.isfile(os.path.join(logd, name)) and name.endswith(EXTS):
                names.append("logs/" + name)
    lines = ["# SHA256SUMS.txt -- P05 delivery round REL-R3 evidence directory",
             "# Every non-binary evidence file (.txt/.tsv/.log/.md) under $EV is listed, except safe_run.log",
             "# (appended by every safe_run call), the two end-gate outputs GATE_RELR3_pre.txt /",
             "# GATE_RELR3_end.txt (their sha256 are recorded in the report appendix C and the rel-r3 registry)",
             "# and SHA256SUMS.txt itself.  The remote clone (remoteclone/) and tmp/ are not listed; the clone",
             "# is recorded by HEAD commit id in REMOTE_CLONE_RELR3.tsv.  Generated " +
             datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")]
    for rel in names:
        lines.append(sha_f(os.path.join(EV, rel)) + "  " + rel)
    open(OUT, "w", encoding="utf-8").write(chr(10).join(lines) + chr(10))
    print("WROTE", os.path.relpath(OUT, REPO), "items=%d" % len(names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
