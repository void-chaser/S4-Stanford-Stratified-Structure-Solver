#!/usr/bin/env python3
# s5r3_build_trees.py -- export the two make-test trees with git archive (no injection):
#   $EV/trees/B   <- commit 37a82e8 (unmodified baseline)
#   $EV/trees/F4  <- commit 05097a7 (frozen F4 tree; its S4/ tree hash is checked)
# and record the git/export facts in TREES_S5R3.tsv.
import os, sys, subprocess, hashlib, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r3")
TREES = os.path.join(EV, "trees")
TAB = chr(9)
NL = chr(10)
JOBS = (("B", "37a82e8", "1d738e64f9864a475fdb3de34cd3601605df2c64"),
        ("F4", "05097a7", "589e15eb11fcb04e031b524f25a443e7921946cf"))


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def sh(cmd):
    return subprocess.check_output(cmd, text=True, cwd=REPO).strip()


def main():
    os.makedirs(TREES, exist_ok=True)
    rows = ["# TREES_S5R3.tsv -- make-test trees exported with git archive (task brief section 4)",
            "# tree/label is not a pass/fail field; S4 tree hashes are asserted below",
            TAB.join(["tree", "commit", "commit_subject", "s4_tree", "s4_tree_expected", "export", "file_count", "marker_sha256"])]
    bad = 0
    for name, commit, exp in JOBS:
        got = sh(["git", "rev-parse", commit + ":S4"])
        if got != exp:
            print("HARD_STOP S4 tree mismatch %s %s" % (name, got))
            return 2
        tdir = os.path.join(TREES, name)
        if os.path.isdir(os.path.join(tdir, "S4")) and os.path.isfile(os.path.join(tdir, "Makefile")):
            export = "exists"
            n = sum(len(fs) for _, _, fs in os.walk(tdir))
        else:
            os.makedirs(tdir, exist_ok=True)
            with open(os.path.join(tdir, "EXPORT_COMMAND.txt"), "w", encoding="utf-8") as fh:
                fh.write("git archive %s | tar -x -C %s" % (commit, os.path.relpath(tdir, REPO)) + NL)
            p = subprocess.run("git archive " + commit + " | tar -x -C " + tdir, shell=True,
                               cwd=REPO, capture_output=True, text=True)
            if p.returncode != 0:
                print("HARD_STOP export failed %s rc=%d %s" % (name, p.returncode, p.stderr[:300]))
                return 2
            export = "ok"
            n = sum(len(fs) for _, _, fs in os.walk(tdir))
        subj = sh(["git", "log", "-1", "--format=%s", commit])[:80]
        rows.append(TAB.join([name, commit, subj, got, exp, export, str(n), sha_f(os.path.join(tdir, "Makefile"))]))
        print("TREE %s commit=%s files=%d s4=%s" % (name, commit, n, got))
    out = os.path.join(EV, "TREES_S5R3.tsv")
    open(out, "w", encoding="utf-8").write(NL.join(rows) + NL)
    print("WROTE " + os.path.relpath(out, REPO))
    return bad


if __name__ == "__main__":
    sys.exit(main())
