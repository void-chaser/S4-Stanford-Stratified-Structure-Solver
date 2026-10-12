#!/usr/bin/env python3
# run_r3_sweep_out.py -- P05-S4 R3-4, out-of-scope points (new file, R3).  Observation only.
#
# Runs every in_D003_scope=NO point of SITEMAP.tsv on trees B and F (one injection per point and tree).  These
# points have NO expected class (R3-3 says: "不登记期望"), so this runner records the observed class and never
# writes MATCH or MISMATCH.  Out-of-scope results are not red points.
#
# Reads (read-only): SITEMAP.tsv (the NO rows), FIELDCALL_MAP.tsv (inj_call).  Imports matrix_r2 and judge_d003
# (read-only).  Writes OUTDIR/RESULTS_R3_OUTSCOPE.raw.tsv and OUTDIR/runs/.
#
#   python3 -I -B testing/d003/stage_s4/run_r3_sweep_out.py SITEMAP FIELDCALL_MAP OUTDIR DRV_B DRV_F SHA_B SHA_F
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
D003 = os.path.join(REPO, "testing", "d003")
sys.path.insert(0, D003)
sys.path.insert(0, HERE)

import judge_d003 as J  # noqa: E402
import matrix_r2 as M  # noqa: E402
from run_r3_sweep import INJECT, load_fieldcall, read_facts, sha256  # noqa: E402


def main(argv):
    if len(argv) != 8:   # program name + 7 arguments
        print("usage: run_r3_sweep_out.py SITEMAP FIELDCALL_MAP OUTDIR DRV_B DRV_F SHA_B SHA_F", file=sys.stderr)
        return 2
    sitemap, fc_path, outdir = argv[1], argv[2], argv[3]
    drv = {"B": argv[4], "F": argv[5]}
    pin = {"B": argv[6], "F": argv[7]}
    os.makedirs(outdir, exist_ok=True)
    runs = os.path.join(outdir, "runs")
    os.makedirs(runs, exist_ok=True)
    manifest = {}
    for t in ("B", "F"):
        if not (os.path.isfile(drv[t]) and os.access(drv[t], os.X_OK)):
            raise SystemExit("REFUSED: driver missing for %s: %s" % (t, drv[t]))
        got = sha256(drv[t])
        if got != pin[t].lower():
            raise SystemExit("REFUSED: driver sha256 mismatch for %s: pinned %s actual %s" % (t, pin[t], got))
        manifest[t] = {"driver": drv[t], "sha256": got}
    with open(os.path.join(outdir, "driver_manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write("\n")
    fcmap = load_fieldcall(fc_path)
    pts = []
    with open(sitemap, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#") or line.startswith("point_id\t"):
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) != 9:
                raise SystemExit("SITEMAP row has %d fields" % len(f))
            pid, mode, cat, nth, size, caller, scope, r1, note = f
            if scope == "NO":
                pts.append((pid, mode, cat, int(nth), caller))
    out = []
    for pid, mode, cat, nth, caller in sorted(pts):
        route = pid.split("-")[1]
        key = (route, mode, cat, nth)
        if key not in fcmap:
            raise SystemExit("no field-call entry for %s" % (key,))
        inj_call = fcmap[key]
        case = ("t4/" if route == "twice" else "r3/") + pid
        for tree in ("B", "F"):
            row = {"case": case, "family": "R3-OUT", "tree": tree, "request": INJECT[cat], "nth": str(nth),
                   "stack": "pattern", "mode": mode, "ng": "9", "expected": "-", "basis": "outscope",
                   "lineno": 0}
            rc, log = M.run_row(drv[tree], row, runs)
            facts = read_facts(log)
            cls, label, reason = J.classify(rc, facts["rc1"], facts["rc2"], facts["hit"],
                                            control=False, real=(cat != "exec"), inj_call=inj_call)
            out.append((pid, tree, mode, cat, str(nth), caller, cls, str(rc), str(facts["rc1"]),
                        str(facts["rc2"]), str(facts["hit"]), str(inj_call), reason + (" " + label if label else ""),
                        log))
    with open(os.path.join(outdir, "RESULTS_R3_OUTSCOPE.raw.tsv"), "w", encoding="utf-8") as fh:
        fh.write("# RESULTS_R3_OUTSCOPE.raw.tsv -- out-of-scope observations (no expectation; not red points).\n")
        fh.write("point_id\ttree\tmode\tcategory\tnth\tcaller\tobserved_class\trc\trc1\trc2\thit\tinj_call\treason\tlog\n")
        for r in out:
            fh.write("\t".join(r) + "\n")
    print("outscope_runs=%d" % len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
