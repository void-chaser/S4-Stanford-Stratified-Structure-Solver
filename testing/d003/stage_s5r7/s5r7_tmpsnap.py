#!/usr/bin/env python3
# s5r7_tmpsnap.py -- P05-S5 R7: the ONLY read-only top-level temporary-directory snapshot command
# of the round (task brief section 0/3; AGENTS.md section 3).  It lists the top level of the system
# temporary directory, computes (count, sha256 of the newline-joined sorted names) and writes the
# result ONLY under the round evidence directory checkpoints/p05/evidence/p05-s5r7/.
# It never creates a file anywhere else; an output path outside that directory is refused.
import os, sys, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r7")
TOPDIR = "/tmp"
TAB = chr(9)
NL = chr(10)


def sha_b(b):
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def main():
    args = sys.argv[1:]
    label = "start"
    out = os.path.join(EV, "TMP_SNAPSHOT_S5R7.tsv")
    i = 0
    while i < len(args):
        if args[i] == "--label":
            label = args[i + 1]
            i += 2
        elif args[i] == "--out":
            out = args[i + 1]
            i += 2
        else:
            print("HARD_STOP unknown argument: " + args[i])
            return 2
    if label not in ("start", "end"):
        print("HARD_STOP --label must be start or end")
        return 2
    real_ev = os.path.realpath(EV)
    real_out = os.path.realpath(out)
    if not (real_out.startswith(real_ev + os.sep)):
        print("HARD_STOP snapshot output must stay under the round evidence directory")
        return 2
    names = sorted(os.listdir(TOPDIR))
    count = len(names)
    sha = sha_b((NL.join(names) + NL).encode("utf-8"))
    body = ["# TMP_SNAPSHOT_S5R7.tsv -- top-level temporary-directory snapshot (%s) at P05-S5 R7" % label,
            "# captured by s5r7_tmpsnap.py, the only read-only snapshot command of the round; read only",
            "# count = number of top-level entries; sha256 = sha256 of the newline-joined sorted names",
            "key" + TAB + "value",
            "LABEL" + TAB + label,
            "TMP_COUNT" + TAB + str(count),
            "TMP_SHA256" + TAB + sha]
    os.makedirs(os.path.dirname(real_out), exist_ok=True)
    open(real_out, "w", encoding="utf-8").write(NL.join(body) + NL)
    print("TMP snapshot label=%s count=%d sha256=%s" % (label, count, sha))
    return 0


if __name__ == "__main__":
    sys.exit(main())
