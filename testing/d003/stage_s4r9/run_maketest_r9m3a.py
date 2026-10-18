#!/usr/bin/env python3
# run_maketest_r9m3a.py -- the four formal make test passes in the frozen order B p1, F4 p1, B p2, F4 p2.
# usage: python3 -I -B testing/d003/stage_s4r9/run_maketest_r9m3a.py
import os, sys, subprocess, datetime

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3a")
TREES = os.path.join(EV, "trees")
OUT = os.path.join(EV, "maketest")
NL = chr(10)


def main():
    os.makedirs(OUT, exist_ok=True)
    rcs = []
    for tree, pas in (("B", 1), ("F4", 1), ("B", 2), ("F4", 2)):
        tdir = os.path.join(TREES, tree)
        if not os.path.isdir(tdir):
            print("HARD_STOP: tree missing " + tdir)
            return 2
        if os.path.commonpath([os.path.realpath(tdir), os.path.realpath(TREES)]) != os.path.realpath(TREES):
            print("HARD_STOP: tree is not under $EV/trees: " + tdir)
            return 2
        logname = os.path.join(OUT, "%s_p%d.log" % (tree, pas))
        print("RUN %s pass %d -> %s" % (tree, pas, logname))
        sys.stdout.flush()
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        with open(logname, "w", encoding="utf-8") as fh:
            fh.write("# make test %s pass %d, utc=%s" % (tree, pas, datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")) + NL)
            p = subprocess.run(["make", "-C", tdir, "test", "PYTHON=python3"], env=env, stdout=fh, stderr=subprocess.STDOUT)
        rcs.append((tree, pas, p.returncode))
        print("  rc=%d" % p.returncode)
    with open(os.path.join(OUT, "MAKETEST_RCS_R9M3A.txt"), "w", encoding="utf-8") as fh:
        for tree, pas, rc in rcs:
            fh.write("%s_p%d rc=%d" % (tree, pas, rc) + NL)
    print("RC_SUMMARY " + str(rcs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
