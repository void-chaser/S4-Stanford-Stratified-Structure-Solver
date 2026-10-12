#!/usr/bin/env python3
"""P05-S4 R7 M2: compare F(R7) with F2 point by point, field by field (new file; read only).

For each point id present on both trees in pass 1 of a group, compares class, verdict, rc, rc1, rc2 and hit.
Writes one new file.  A row is ENV_DRIFT-free when every field is equal.  Any unequal row is listed as UNEQUAL.
Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r7/compare_trees_r7.py EVDIR GROUP PASS OUT.tsv
Exit status 0 only if every point id is on both trees and every field is equal.
"""
import os
import sys

FIELDS = ["class", "verdict", "rc", "rc1", "rc2", "hit"]


def base_id(pid, tree):
    """The point id without its tree suffix.  The result tables write the tree into the id (e.g. ...-F-F for tree F,
    ...-F-F2 for tree F2), so the base is the id with the trailing "-<tree>" removed, once for the F2 form ("-F2") and
    once for the F form ("-F") after that.  Refuses if the id does not end in the tree's own suffix."""
    suffix = "-" + tree
    if not pid.endswith(suffix):
        raise ValueError("id %r does not end with %r" % (pid, suffix))
    base = pid[: -len(suffix)]
    # the table id is <source-id>-F for tree F and <source-id>-F2 for tree F2; the source id itself may end in -F
    # (e.g. R6T-twice-fft-plan-12-F), so the base keeps that -F.  Keep the base as the id without the tree suffix only.
    return base


def load(path):
    header, rows = None, {}
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            d = dict(zip(header, f))
            rows[(base_id(d["point_id"], d["tree"]), d["tree"])] = d
    return rows


def main(argv):
    if len(argv) != 5:
        raise SystemExit("usage: compare_trees_r7.py EVDIR GROUP PASS OUT.tsv")
    ev, group, pas, out = argv[1], argv[2], argv[3], argv[4]
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    rows = load(os.path.join(ev, "RESULTS_R7_%s_pass%s_run4.tsv" % (group, pas)))
    pids = sorted({k[0] for k in rows})
    lines = ["# F(R7) vs F2 per point, group %s pass %s (run4).  Fields: %s." % (group, pas, ", ".join(FIELDS)),
             "point_id\tstatus\t" + "\t".join("F_" + f + "\tF2_" + f for f in FIELDS)]
    unequal = absent = 0
    for pid in pids:
        f, f2 = rows.get((pid, "F")), rows.get((pid, "F2"))
        if f is None or f2 is None:
            absent += 1
            lines.append("\t".join([pid, "ABSENT_ON_ONE_TREE"] + ["-"] * (2 * len(FIELDS))))
            continue
        same = all(f[x] == f2[x] for x in FIELDS)
        if not same:
            unequal += 1
        cells = []
        for x in FIELDS:
            cells += [f[x], f2[x]]
        lines.append("\t".join([pid, "EQUAL" if same else "UNEQUAL"] + cells))
    lines.append("# points=%d unequal=%d absent_on_one_tree=%d" % (len(pids), unequal, absent))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("group=%s pass=%s points=%d unequal=%d absent=%d -> %s" % (group, pas, len(pids), unequal, absent, out))
    return 0 if (unequal == 0 and absent == 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
