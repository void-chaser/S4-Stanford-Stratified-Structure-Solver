#!/usr/bin/env python3
"""P05-S4 R7 M2a: check every count quoted in P05_S4R7_REPORT_M2.md against the result files (new file; read only).

Prints each check and its result.  Exit status 0 only if every check holds.  Writes nothing.
Usage: python3 -I -B testing/d003/stage_s4r7/verify_m2a_report_counts_r7.py EVDIR
"""
import os
import sys
from collections import Counter


def table(path):
    header, rows = None, []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            rows.append(dict(zip(header, f)))
    return rows


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: verify_m2a_report_counts_r7.py EVDIR")
    ev = argv[1]
    ok = True

    def check(label, got, want):
        nonlocal ok
        good = got == want
        ok = ok and good
        print("%-58s got=%s want=%s %s" % (label, got, want, "OK" if good else "FAIL"))

    expect_rows = {"G2b": 44, "G3": 72, "G4": 24}
    expect_points = {"G2b": 22, "G3": 36, "G4": 12}
    for g in ("G2b", "G3", "G4"):
        for p in ("1", "2"):
            rows = table(os.path.join(ev, "RESULTS_R7_%s_pass%s_run4.tsv" % (g, p)))
            check("%s pass%s rows" % (g, p), len(rows), expect_rows[g])
            check("%s pass%s MATCH" % (g, p), sum(1 for r in rows if r["verdict"] == "MATCH"), expect_rows[g])
            check("%s pass%s class REPORTED_FAILURE" % (g, p),
                  sum(1 for r in rows if r["class"] == "REPORTED_FAILURE"), expect_rows[g])
            check("%s pass%s hit=1" % (g, p), sum(1 for r in rows if r["hit"] == "1"), expect_rows[g])
            rc = Counter((r["rc1"], r["rc2"]) for r in rows if r["tree"] == "F")
            rc2_tree = Counter((r["tree"], r["rc1"], r["rc2"]) for r in rows)
            if g == "G2b":
                check("G2b pass%s F (rc1=0,rc2=20) rows" % p, rc2_tree[("F", "0", "20")], 10)
                check("G2b pass%s F (rc1=20,rc2=0) rows" % p, rc2_tree[("F", "20", "0")], 12)
            if g == "G3":
                check("G3 pass%s F (rc1=0,rc2=20) rows" % p, rc2_tree[("F", "0", "20")], 10)
                check("G3 pass%s F (rc1=20,rc2=0) rows" % p, rc2_tree[("F", "20", "0")], 26)
            if g == "G4":
                check("G4 pass%s F (rc1=0,rc2=20) rows" % p, rc2_tree[("F", "0", "20")], 10)
                check("G4 pass%s F (rc1=20,rc2=0) rows" % p, rc2_tree[("F", "20", "0")], 2)
    for g in ("G2b", "G3", "G4"):
        t = table(os.path.join(ev, "TREES_R7_M2a_%s_pass1_v2.tsv" % g))
        pts = [r for r in t if r.get("status") in ("EQUAL", "UNEQUAL")]
        check("%s tree-compare points (pass1)" % g, len(pts), expect_points[g])
        check("%s tree-compare UNEQUAL (pass1)" % g, sum(1 for r in pts if r["status"] == "UNEQUAL"), 0)
    env = table(os.path.join(ev, "ENV_DRIFT_R7_M2a.tsv"))
    check("ENV_DRIFT points", len(env), 70)
    check("ENV_DRIFT drift", sum(1 for r in env if r["env_drift"] == "DRIFT"), 0)
    hb = table(os.path.join(ev, "HIT_BYTES_R7_M2a.tsv"))
    check("HIT size rows", len(hb), 280)
    check("HIT possibly_in_window", sum(1 for r in hb if r["verdict"] == "POSSIBLY_IN_WINDOW"), 0)
    print("ALL CHECKS OK" if ok else "SOME CHECK FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
