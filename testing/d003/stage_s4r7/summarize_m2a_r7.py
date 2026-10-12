#!/usr/bin/env python3
"""P05-S4 R7 M2a: summary of the G2b, G3, G4 results (new file; read only).

Reads the pass-1 and pass-2 RESULTS_R7_<G>_pass<P>_run4.tsv files and the TREES_R7_M2a_<G>_pass<P>_v2.tsv files already
written.  Writes one new file REGRESS_R7_M2a.tsv with, for each group: point counts per verdict and per pass, the number
of FLAKY points, and the number of F/F2 field differences.  No driver is run.
Usage (through safe_run):  python3 -I -B testing/d003/stage_s4r7/summarize_m2a_r7.py EVDIR OUT.tsv
"""
import os
import sys

GROUPS = ("G2b", "G3", "G4")


def load_results(path):
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


def count_trees(path):
    eq = uneq = absent = 0
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            if raw.startswith("#") or raw.startswith("point_id\t"):
                continue
            f = raw.rstrip("\n").split("\t")
            if len(f) < 2:
                continue
            if f[1] == "EQUAL":
                eq += 1
            elif f[1] == "UNEQUAL":
                uneq += 1
            elif f[1] == "ABSENT_ON_ONE_TREE":
                absent += 1
    return eq, uneq, absent


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: summarize_m2a_r7.py EVDIR OUT.tsv")
    ev, out = argv[1], argv[2]
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    lines = ["# REGRESS_R7_M2a.tsv -- P05-S4 R7 M2a summary (G2b, G3, G4; run4).  Read-only summary of existing outputs.",
             "# verdict counts are over all F and F2 rows of each pass; tree comparison from TREES_R7_M2a_<G>_pass<P>_v2.tsv.",
             "group\tpass\trows\tMATCH\tnon_MATCH\tF_points_EQUAL_F2\tF_points_UNEQUAL_F2\tabsent"]
    all_ok = True
    for g in GROUPS:
        for p in ("1", "2"):
            res = os.path.join(ev, "RESULTS_R7_%s_pass%s_run4.tsv" % (g, p))
            trees = os.path.join(ev, "TREES_R7_M2a_%s_pass%s_v2.tsv" % (g, p))
            rows = load_results(res)
            m = sum(1 for r in rows if r["verdict"] == "MATCH")
            nm = len(rows) - m
            eq, uneq, absent = count_trees(trees)
            if nm or uneq or absent:
                all_ok = False
            lines.append("\t".join([g, p, str(len(rows)), str(m), str(nm), str(eq), str(uneq), str(absent)]))
    lines.append("# all groups both passes: no non-MATCH, no unequal tree field, no absent point: %s" % ("YES" if all_ok else "NO"))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines[-2:]))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
