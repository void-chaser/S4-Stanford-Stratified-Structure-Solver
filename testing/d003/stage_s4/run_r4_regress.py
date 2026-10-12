#!/usr/bin/env python3
# run_r4_regress.py -- P05-S4 R4-4 step 3: regression of the NEW injector (inject_r4_plan.cpp) against R3.
# New file.  run_r3_sweep.py, matrix_r2.py and judge_d003.py are IMPORTED, not modified.
#
#   python3 -I -B testing/d003/stage_s4/run_r4_regress.py SUBSET_POINTS PREREG_R3 FIELDCALL_MAP RESULTS_R3 \
#           DRIVER_B DRIVER_F OUTDIR
#
# For each point of the subset (R3 point ids), and for trees B and F, the run uses exactly the rules of
# run_r3_sweep.py (request = INJECT[category], NTH from the registry, NG 9, stack pattern, inj_call from the
# field-call map, twice-route case prefix t4/).  The class is judge_d003.classify on facts only.
# The observed class is then compared with the observed class of RESULTS_R3.tsv for the same point and tree.
# Any difference is written, and the run exits with status 3 (the R4-4 rule: stop on any difference).
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
D003 = os.path.join(REPO, "testing", "d003")
sys.path.insert(0, D003)
sys.path.insert(0, HERE)

import judge_d003 as J  # noqa: E402
import matrix_r2 as M  # noqa: E402
import run_r3_sweep as R3  # noqa: E402  (only its read helpers are used)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_results_r3(path):
    """RESULTS_R3.tsv: point_id tree mode category nth expected observed match rc rc1 signal hit inj_call."""
    res = {}
    with open(path, encoding="utf-8") as fh:
        header = None
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            f = line.rstrip("\n").split("\t")
            if header is None:
                header = f
                continue
            d = dict(zip(header, f))
            res[(d["point_id"], d["tree"])] = d
    return res


def main(argv):
    if len(argv) != 8:
        raise SystemExit("usage: run_r4_regress.py SUBSET PREREG_R3 FIELDCALL RESULTS_R3 DRIVER_B DRIVER_F OUTDIR")
    subset_path, prereg, fc_path, res_path, drv_b, drv_f, outdir = argv[1:8]
    drivers = {"B": drv_b, "F": drv_f}
    for t, p in drivers.items():
        if not (os.path.isfile(p) and os.access(p, os.X_OK)):
            raise SystemExit("REFUSED: driver missing for %s: %s" % (t, p))
    os.makedirs(outdir, exist_ok=True)
    runs = os.path.join(outdir, "runs")
    os.makedirs(runs, exist_ok=True)
    with open(os.path.join(outdir, "driver_sha256.txt"), "w", encoding="utf-8") as fh:
        for t in ("B", "F"):
            fh.write("%s\t%s\t%s\n" % (t, sha256(drivers[t]), drivers[t]))
    exp, meta = R3.load_prereg(prereg)
    fcmap = R3.load_fieldcall(fc_path)
    r3 = load_results_r3(res_path)
    with open(subset_path, encoding="utf-8") as fh:
        subset = [l.strip() for l in fh if l.strip()]
    out = []
    diffs = []
    for pid in subset:
        m = meta[pid]
        route = R3.route_of(pid)
        cat, nth, mode = m["category"], int(m["nth"]), m["mode"]
        inj_call = fcmap[(route, mode, cat, nth)]
        case = ("t4/" if route == "twice" else "r3/") + pid
        for tree in ("B", "F"):
            row = {"case": case, "family": "R3", "tree": tree, "request": R3.INJECT[cat], "nth": str(nth),
                   "stack": "pattern", "mode": mode, "ng": "9", "expected": exp[pid][tree],
                   "basis": "prereg", "lineno": 0}
            rc, log = M.run_row(drivers[tree], row, runs)
            facts = R3.read_facts(log)
            cls, label, reason = J.classify(rc, facts["rc1"], facts["rc2"], facts["hit"],
                                            control=False, real=(cat != "exec"), inj_call=inj_call)
            ref = r3[(pid, tree)]["observed_class"]
            same = (cls == ref)
            if not same:
                diffs.append((pid, tree, ref, cls, rc, facts["rc1"], facts["hit"]))
            out.append((pid, tree, mode, cat, nth, ref, cls, "SAME" if same else "DIFF", rc, facts["rc1"],
                        facts["rc2"], facts["hit"], inj_call))
    path = os.path.join(outdir, "REGRESS_R4.tsv")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# REGRESS_R4.tsv -- R4-4 regression of inject_r4_plan.cpp against RESULTS_R3.tsv (observed_class).\n")
        fh.write("point_id\ttree\tmode\tcategory\tnth\tr3_observed\tr4_observed\tsame\trc\trc1\trc2\thit\tinj_call\n")
        for row in out:
            fh.write("\t".join(str(x) for x in row) + "\n")
    print("regress rows=%d same=%d diff=%d" % (len(out), len(out) - len(diffs), len(diffs)))
    for d in diffs:
        print("DIFF", d)
    return 3 if diffs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
