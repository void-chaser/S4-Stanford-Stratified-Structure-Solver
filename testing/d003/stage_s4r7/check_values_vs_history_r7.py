#!/usr/bin/env python3
"""P05-S4 R7 cont7 (U71b, U72): value check of the tree-F rows against the historical tables, per group (new file; read only
except OUT).

For each group, compares the F rows of a result file with the historical F rows of its source table, point by point:
rc, rc1 (and rc2 where the historical table has it), and hit.  A difference in any compared field is VALUE_DRIFT, even when the
class is the same (U71b).  A group whose result file is absent is reported as MISSING for that group (U72); the other groups
are still checked.

Sources (U71b):
  G1  : registries/s4r3/RESULTS_R3.tsv      columns rc, rc1, hit   (tree F; point id = source id)
  G2c : registries/s4r4/REGRESS_R4.tsv      columns rc, rc1, rc2, hit (tree F; point id = source id)
  G2a : registries/s4r4/RESULTS_R4.tsv      columns rc_p1, rc1_p1, rc2_p1, hit_p1 (tree F; point id = source id)
The result file is RESULTS_R7_<G>_pass<P>_<RUN>.tsv under EVDIR.  Its F point ids are "<base>-F"; base_id from
compare_trees_r7 gives the source id (U66, no separate rule).

Usage (through safe_run, absolute paths):
  python3 -I -B testing/d003/stage_s4r7/check_values_vs_history_r7.py EVDIR RUNTAG OUT.tsv [pass]
Exit status: 0 if every group that is present has no VALUE_DRIFT and no MISSING group; 1 otherwise.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
from compare_trees_r7 import base_id  # noqa: E402  imported (U66)

REG = os.path.join(REPO, "checkpoints", "p05", "registries")
# group -> (historical file, historical point-id column, {our field: historical column})
SOURCES = {
    "G1": (os.path.join(REG, "s4r3", "RESULTS_R3.tsv"), "point_id", {"rc": "rc", "rc1": "rc1", "hit": "hit"}),
    "G2c": (os.path.join(REG, "s4r4", "REGRESS_R4.tsv"), "point_id", {"rc": "rc", "rc1": "rc1", "rc2": "rc2", "hit": "hit"}),
    "G2a": (os.path.join(REG, "s4r4", "RESULTS_R4.tsv"), "point_id",
            {"rc": "rc_p1", "rc1": "rc1_p1", "rc2": "rc2_p1", "hit": "hit_p1"}),
}
COMPARED = ("rc", "rc1", "rc2", "hit")


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


def history_f(group):
    path, pid_col, colmap = SOURCES[group]
    out = {}
    for d in table(path):
        if d.get("tree") != "F":
            continue
        out[d[pid_col]] = {k: d.get(colmap[k]) for k in colmap}
    return out


def result_f(path):
    out = {}
    for d in table(path):
        if d.get("tree") != "F":
            continue
        out[base_id(d["point_id"], "F")] = d
    return out


def main(argv):
    if len(argv) not in (4, 5):
        raise SystemExit("usage: check_values_vs_history_r7.py EVDIR RUNTAG OUT.tsv [pass]")
    ev, tag, out = argv[1], argv[2], argv[3]
    passes = [argv[4]] if len(argv) == 5 else ["1", "2"]
    if not os.path.isabs(out):
        raise SystemExit("REFUSED: OUT must be an absolute path under the evidence directory")
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    lines = ["# value check of tree-F rows against the historical tables (U71b).  run %s.  Differences in rc, rc1, rc2 or hit are VALUE_DRIFT,"
             " even when the class is the same." % tag,
             "group\tpass\tpoint_id\tfield\tresult\thistory\tstatus"]
    drift = missing = total = 0
    group_status = []
    for g in ("G1", "G2c", "G2a"):
        hist = history_f(g)
        for p in passes:
            path = os.path.join(ev, "RESULTS_R7_%s_pass%s_%s.tsv" % (g, p, tag))
            if not os.path.isfile(path):
                missing += 1
                group_status.append("%s pass%s MISSING" % (g, p))
                lines.append("%s\t%s\t-\t-\t-\t-\tMISSING" % (g, p))
                continue
            res = result_f(path)
            group_status.append("%s pass%s checked" % (g, p))
            for sid, h in sorted(hist.items()):
                total += 1
                r = res.get(sid)
                if r is None:
                    lines.append("%s\t%s\t%s\t-\t-\t-\tABSENT" % (g, p, sid))
                    drift += 1
                    continue
                for field in COMPARED:
                    if field not in h or h[field] is None:
                        continue  # the historical table does not carry this field (e.g. rc2 in RESULTS_R3)
                    hv = h[field]
                    rv = r.get(field)  # RESULTS_R7 columns rc, rc1, rc2, hit (run_m2b_all_r7.COLS) have the same names
                    if str(rv) != str(hv):
                        drift += 1
                        lines.append("%s\t%s\t%s\t%s\t%s\t%s\tVALUE_DRIFT" % (g, p, sid, field, rv, hv))
    lines.append("# groups: %s" % "; ".join(group_status))
    lines.append("# points_compared=%d value_drift=%d missing_groups=%d" % (total, drift, missing))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("points=%d value_drift=%d missing=%d -> %s" % (total, drift, missing, out))
    return 0 if (drift == 0 and missing == 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
