#!/usr/bin/env python3
"""P05-S4 R7 cont6 (section 2.3): ENV_DRIFT check for M2b (new file; read only except OUT).

ENV_DRIFT = the R7 build of F does not reproduce the historical F class of the same point.  Checked per (base point id, group)
(E7-21(h): G1 and G2c share 60 base ids, so the group is part of the key).  The R7 class comes from the M2b results (tree F,
pass 1 and pass 2).  The historical class comes from:
  G2c : registries/s4r4/REGRESS_R4.tsv   column r4_observed, tree F   (point_id has no tree suffix)
  G1  : registries/s4r3/RESULTS_R3.tsv   column observed_class, tree F
  G2a : registries/s4r4/RESULTS_R4.tsv   columns obs_pass1 and obs_pass2, tree F
The base id is compare_trees_r7.base_id (no separate rule).  CTRL_SEAM and G2c-control are not compared (their expected class is
CONTROL_OK; the control check is inside the run).

Output (one new file, U17): one row per compared point, and a final line with points, env_drift, absent.
Exit status 0 only if absent == 0 and env_drift == 0 (cont6 section 5 stops on absent != 0).
Usage (through safe_run, absolute paths):
  python3 -I -B testing/d003/stage_s4r7/check_env_drift_m2b_r7.py EVDIR OUT.tsv
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
from compare_trees_r7 import base_id  # noqa: E402  imported, not copied (U66)

REG = os.path.join(REPO, "checkpoints", "p05", "registries")
SOURCES = {
    "G2c": (os.path.join(REG, "s4r4", "REGRESS_R4.tsv"), "r4_observed", None),
    "G1": (os.path.join(REG, "s4r3", "RESULTS_R3.tsv"), "observed_class", None),
    "G2a": (os.path.join(REG, "s4r4", "RESULTS_R4.tsv"), "obs_pass1", "obs_pass2"),
}


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


def historical_f(group):
    """{base_id: (class_or_None, class2_or_None)} of the F rows of the historical source of this group."""
    path, col1, col2 = SOURCES[group]
    out = {}
    for d in table(path):
        if d.get("tree") != "F":
            continue
        pid = d["point_id"]
        out[pid] = (d[col1], d[col2] if col2 else None)
    return out


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: check_env_drift_m2b_r7.py EVDIR RUNTAG OUT.tsv")
    ev, tag, out = argv[1], argv[2], argv[3]
    if not os.path.isabs(out):
        raise SystemExit("REFUSED: OUT must be an absolute path under the evidence directory")
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    lines = ["# ENV_DRIFT check, M2b (G2c, G1, G2a): R7 F class (pass 1 and pass 2) vs historical F class, per (base id, group).",
             "group\tbase_id\thistorical_F_pass1\thistorical_F_pass2\tR7_F_pass1\tR7_F_pass2\tenv_drift"]
    points = drift = absent = 0
    missing_groups = []
    for g in ("G2c", "G1", "G2a"):
        hist = historical_f(g)
        cur = {"1": {}, "2": {}}
        group_missing = False
        for p in ("1", "2"):
            path = os.path.join(ev, "RESULTS_R7_%s_pass%s_%s.tsv" % (g, p, tag))
            if not os.path.isfile(path):
                group_missing = True  # U72: report this group as MISSING, keep checking the others
                continue
            for d in table(path):
                if d["tree"] != "F":
                    continue
                cur[p][(base_id(d["point_id"], "F"), g)] = d["class"]
        if group_missing:
            # U72: the group has no result file for this tag; reported as MISSING, not as absent points
            missing_groups.append(g)
            lines.append("%s\tMISSING_GROUP\t-\t-\t-\t-\tMISSING" % g)
            continue
        # historical keys are the source point ids; the R7 base ids must match them
        for pid, (h1, h2) in sorted(hist.items()):
            points += 1
            c1 = cur["1"].get((pid, g))
            c2 = cur["2"].get((pid, g))
            if c1 is None or c2 is None:
                absent += 1
                lines.append("\t".join([g, pid, h1, h2 or "-", c1 or "ABSENT", c2 or "ABSENT", "ABSENT"]))
                continue
            # U68 / ADD1 3: a historical INVALID and an R7 verdict NOT_REACHED_AS_EXPECTED are the same class (INVALID),
            # so a class-string comparison is the rule here; the verdict is not re-decided in this script.
            ok1 = (c1 == h1)
            ok2 = (c2 == h2) if h2 is not None else True
            flag = "-" if (ok1 and ok2) else "DRIFT"
            if flag == "DRIFT":
                drift += 1
            lines.append("\t".join([g, pid, h1, h2 or "-", c1, c2, flag]))
    lines.append("# points=%d env_drift=%d absent=%d missing_groups=%s"
                 % (points, drift, absent, ",".join(missing_groups) or "none"))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("points=%d env_drift=%d absent=%d missing_groups=%s -> %s"
          % (points, drift, absent, ",".join(missing_groups) or "none", out))
    return 0 if (absent == 0 and drift == 0 and not missing_groups and points > 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
