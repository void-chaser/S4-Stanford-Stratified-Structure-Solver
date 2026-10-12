#!/usr/bin/env python3
# r6b_tree_verify.py -- P05-S4 R6b-0.2 (new file).  Verifies that the R5 debug tree used by the R6 driver
# (checkpoints/p05/evidence/p05-s4r5/dbg/trees/F/S4) is byte-identical to the frozen tree F (commit 1c11905, path S4).
# Every file under the debug tree is hashed with `git hash-object` (no -w: no object is written to .git).
# The expected blob ids come from `git ls-tree -r 1c11905 S4`.  Output: EV/TREE_VERIFY_R6b.tsv and a four-way summary.
#
# Usage: python3 -I -B testing/d003/stage_s4/r6b_tree_verify.py EVDIR
import os
import subprocess
import sys

COMMIT = "1c11905"
REL_BASE = "S4"
TREE_DIR = os.path.join("checkpoints", "p05", "evidence", "p05-s4r5", "dbg", "trees", "F", "S4")


def run(args):
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if p.returncode != 0:
        raise SystemExit("command failed: %s\n%s" % (" ".join(args), p.stderr.decode("utf-8", "replace")))
    return p.stdout.decode("utf-8", "replace")


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: r6b_tree_verify.py EVDIR")
    ev = argv[1]
    repo = run(["git", "rev-parse", "--show-toplevel"]).strip()
    # expected: path (relative to S4/) -> blob id, from the frozen commit
    expected = {}
    for line in run(["git", "ls-tree", "-r", COMMIT, REL_BASE]).splitlines():
        meta, path = line.split("\t", 1)
        mode, kind, oid = meta.split()
        if kind != "blob":
            continue
        expected[path[len(REL_BASE) + 1:]] = oid
    # actual: every regular file under the debug tree
    base = os.path.join(repo, TREE_DIR)
    actual = {}
    for dp, _dn, fn in os.walk(base):
        for name in fn:
            full = os.path.join(dp, name)
            rel = os.path.relpath(full, base).replace(os.sep, "/")
            oid = run(["git", "hash-object", "--", full]).strip()
            actual[rel] = oid
    rows = []
    same = diff = missing = extra = 0
    for rel in sorted(set(expected) | set(actual)):
        e = expected.get(rel)
        a = actual.get(rel)
        if e is not None and a is not None:
            if e == a:
                status = "SAME"
                same += 1
            else:
                status = "DIFFERENT"
                diff += 1
        elif e is not None:
            status = "MISSING_IN_TREE"
            missing += 1
        else:
            status = "EXTRA_IN_TREE"
            extra += 1
        rows.append((rel, e or "-", a or "-", status))
    out = os.path.join(ev, "TREE_VERIFY_R6b.tsv")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# TREE_VERIFY_R6b.tsv -- R6b-0.2: %s/%s vs git ls-tree -r %s S4 (git hash-object, no -w)\n"
                 % (TREE_DIR, "*", COMMIT))
        fh.write("path\texpected_blob\tactual_blob\tstatus\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
        fh.write("# SUMMARY same=%d different=%d missing=%d extra=%d\n" % (same, diff, missing, extra))
    print("SUMMARY same=%d different=%d missing=%d extra=%d" % (same, diff, missing, extra))
    return 0 if (diff == 0 and missing == 0 and extra == 0 and same > 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
