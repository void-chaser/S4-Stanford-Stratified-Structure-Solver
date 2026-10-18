#!/usr/bin/env python3
# run_maketest_s5r3.py -- one segment of the four formal make test passes (B p1, F4 p1, B p2, F4 p2).
# Copied from run_maketest_r9m3a.py; the only addition is per-segment resume (task brief section 4):
# a segment whose log and .done marker exist is skipped, so an interrupted run can continue.
# usage: run_maketest_s5r3.py B:1|F4:1|B:2|F4:2
import os, sys, subprocess, datetime, hashlib

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r3")
TREES = os.path.join(EV, "trees")
OUT = os.path.join(EV, "maketest")
NL = chr(10)
SEGMENTS = ("B:1", "F4:1", "B:2", "F4:2")


def sha_f(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in SEGMENTS:
        print("usage: run_maketest_s5r3.py " + "|".join(SEGMENTS))
        return 2
    tree, pas = sys.argv[1].split(":")
    os.makedirs(OUT, exist_ok=True)
    tdir = os.path.join(TREES, tree)
    if not os.path.isdir(tdir):
        print("HARD_STOP: tree missing " + tdir)
        return 2
    logname = os.path.join(OUT, "%s_p%s.log" % (tree, pas))
    done = os.path.join(OUT, "%s_p%s.done" % (tree, pas))
    if os.path.isfile(logname) and os.path.isfile(done):
        print("SKIP segment %s (already complete): %s" % (sys.argv[1], os.path.relpath(done, REPO)))
        return 0
    print("RUN %s -> %s" % (sys.argv[1], os.path.relpath(logname, REPO)))
    sys.stdout.flush()
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    with open(logname, "w", encoding="utf-8") as fh:
        fh.write("# make test %s pass %s, utc=%s" % (tree, pas, datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")) + NL)
        p = subprocess.run(["make", "-C", tdir, "test", "PYTHON=python3"], env=env,
                           stdout=fh, stderr=subprocess.STDOUT)
    with open(done, "w", encoding="utf-8") as fh:
        fh.write("segment=%s rc=%d utc=%s log_sha256=%s" % (sys.argv[1], p.returncode,
                 datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), sha_f(logname)) + NL)
    print("  rc=%d" % p.returncode)
    return 0 if p.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
