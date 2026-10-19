#!/usr/bin/env python3
# relr1_maketest.py -- one segment of the four formal make test passes of REL-R1 (B pass 1/2, F4 pass 1/2).
# Adapted from testing/d003/stage_s5r3/run_maketest_s5r3.py (same method: full 'make test' in the exported
# tree, log kept verbatim under $EV/maketest, a .done marker with the raw rc).  A segment whose log and
# .done marker already exist is skipped so an interrupted run can continue.
# usage: relr1_maketest.py B:1|B:2|F4:1|F4:2
import os, sys, subprocess, datetime, hashlib

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r1")
TREES = os.path.join(EV, "trees")
OUT = os.path.join(EV, "maketest")
NL = chr(10)
SEGMENTS = ("B:1", "B:2", "F4:1", "F4:2")


def sha_f(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in SEGMENTS:
        print("usage: relr1_maketest.py " + "|".join(SEGMENTS))
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
    env["TMPDIR"] = os.path.join(EV, "tmp")
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(logname, "w", encoding="utf-8") as fh:
        fh.write("# make test %s pass %s, utc=%s, cwd=%s, command=make test PYTHON=python3" % (tree, pas, utc, os.path.relpath(tdir, REPO)) + NL)
        fh.flush()
        p = subprocess.run(["make", "test", "PYTHON=python3"], cwd=tdir, env=env,
                           stdout=fh, stderr=subprocess.STDOUT)
    out = ("segment=%s rc=%d utc=%s log_sha256=%s" % (sys.argv[1], p.returncode,
           datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), sha_f(logname)) + NL)
    open(done, "w", encoding="utf-8").write(out)
    print("  rc=%d" % p.returncode)
    return 0 if p.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
