#!/usr/bin/env python3
# run_r3_sweep.py -- P05-S4 R3-4 exhaustive injection sweep (new file, R3).
#
# Reads (read-only):
#   REGISTRY_S4_PRE_R3.tsv   the pre-registration (expected class per point and tree; written and hashed BEFORE any run)
#   FIELDCALL_MAP.tsv        the field call (1 or 2) of each discovered (route, mode, category, NTH)
# Imports (read-only, not modified): matrix_r2.run_row (the same environment, grid and timeout as R2) and
# judge_d003.classify / facts_from_log (facts only; the driver PASS/FAIL line is never read).
#
# For every pre-registered point and tree (B or F) it runs one injection and classifies the run with the field
# call taken from FIELDCALL_MAP as inj_call.  Control rows (no injection) are run for B, F and A per mode.  The
# expected class is taken only from the pre-registration; this run does not change it.
#
#   python3 -I -B testing/d003/stage_s4/run_r3_sweep.py PREREG FIELDCALL_MAP OUTDIR DRV_B DRV_F DRV_A SHA_B SHA_F SHA_A
#
# Writes OUTDIR/RESULTS_R3.raw.tsv (one line per run), OUTDIR/runs/ (driver logs) and OUTDIR/driver_manifest.json.
# A driver whose sha256 differs from the pinned value is refused before any run.
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
D003 = os.path.join(REPO, "testing", "d003")
sys.path.insert(0, D003)

import judge_d003 as J  # noqa: E402
import matrix_r2 as M  # noqa: E402

TREES = ("B", "F", "A")
INJECT = {"malloc": "s4malloc", "plan": "plan", "exec": "exec"}
EXPECTED_OK = set(J.CLASSES) | {"REPORTED_FAILURE", "CRASH", "SILENT_SWALLOW", "CONTROL_OK"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_prereg(path):
    """Return ({point_id: {tree: expected}}, {point_id: {mode, category, nth}})."""
    exp = {}
    meta = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#") or line.startswith("point_id\t"):
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) != 8:
                raise SystemExit("prereg row has %d fields" % len(f))
            pid, tree, mode, cat, nth, expected, basis, status = f
            if expected not in EXPECTED_OK:
                raise SystemExit("prereg: bad expected %r for %s" % (expected, pid))
            exp.setdefault(pid, {})[tree] = expected
            meta[pid] = {"mode": mode, "category": cat, "nth": nth}
    return exp, meta


def load_fieldcall(path):
    fc = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#") or line.startswith("route\t"):
                continue
            route, mode, cat, nth, call = line.rstrip("\n").split("\t")
            fc[(route, mode, cat, int(nth))] = int(call)
    return fc


def route_of(pid):
    # point ids are M-<route>-<mode>-<category>-<NTH>; the route is the second field
    return pid.split("-")[1]


def read_facts(log):
    with open(log, "rb") as fh:
        return J.facts_from_log(fh.read().decode("utf-8", errors="replace"))


def main(argv):
    if len(argv) != 10:   # program name + 9 arguments
        print("usage: run_r3_sweep.py PREREG FIELDCALL_MAP OUTDIR DRV_B DRV_F DRV_A SHA_B SHA_F SHA_A", file=sys.stderr)
        return 2
    prereg, fc_path, outdir = argv[1], argv[2], argv[3]
    drv = {"B": argv[4], "F": argv[5], "A": argv[6]}
    pin = {"B": argv[7], "F": argv[8], "A": argv[9]}
    os.makedirs(outdir, exist_ok=True)
    runs = os.path.join(outdir, "runs")
    os.makedirs(runs, exist_ok=True)
    # refuse before any run: driver identity by content
    manifest = {}
    for t in TREES:
        if not (os.path.isfile(drv[t]) and os.access(drv[t], os.X_OK)):
            raise SystemExit("REFUSED: driver missing for %s: %s" % (t, drv[t]))
        got = sha256(drv[t])
        if got != pin[t].lower():
            raise SystemExit("REFUSED: driver sha256 mismatch for %s: pinned %s actual %s" % (t, pin[t], got))
        manifest[t] = {"driver": drv[t], "sha256": got}
    with open(os.path.join(outdir, "driver_manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write("\n")
    exp, meta = load_prereg(prereg)
    fcmap = load_fieldcall(fc_path)
    out = []
    for pid in sorted(exp):
        m = meta[pid]
        route = route_of(pid)
        cat, nth, mode = m["category"], int(m["nth"]), m["mode"]
        key = (route, mode, cat, nth)
        if key not in fcmap:
            raise SystemExit("no field-call entry for %s" % (key,))
        inj_call = fcmap[key]
        # twice-route cases start with t4/ (driver S4FMM_TWICE=slab); once-route cases do not
        case = ("t4/" if route == "twice" else "r3/") + pid
        for tree in ("B", "F"):
            row = {"case": case, "family": "R3", "tree": tree, "request": INJECT[cat], "nth": str(nth),
                   "stack": "pattern", "mode": mode, "ng": "9", "expected": exp[pid][tree],
                   "basis": "prereg", "lineno": 0}
            rc, log = M.run_row(drv[tree], row, runs)
            facts = read_facts(log)
            cls, label, reason = J.classify(rc, facts["rc1"], facts["rc2"], facts["hit"],
                                            control=False, real=(cat != "exec"), inj_call=inj_call)
            out.append((pid, tree, mode, cat, str(nth), row["expected"], cls, rc, facts["rc1"], facts["rc2"],
                        facts["hit"], inj_call, reason + (" " + label if label else ""), log))
    # control rows: one per mode and tree, no request (A is a control only)
    for mode in sorted({meta[p]["mode"] for p in meta}):
        for tree in TREES:
            row = {"case": "r3/ctl-%s-%s" % (mode, tree), "family": "C", "tree": tree, "request": "-", "nth": "-",
                   "stack": "pattern", "mode": mode, "ng": "9", "expected": "CONTROL_OK", "basis": "control",
                   "lineno": 0}
            rc, log = M.run_row(drv[tree], row, runs)
            facts = read_facts(log)
            cls, label, reason = J.classify(rc, facts["rc1"], facts["rc2"], facts["hit"], control=True)
            out.append(("CTL-%s" % mode, tree, mode, "control", "-", "CONTROL_OK", cls, rc, facts["rc1"],
                        facts["rc2"], facts["hit"], 1, reason, log))
    with open(os.path.join(outdir, "RESULTS_R3.raw.tsv"), "w", encoding="utf-8") as fh:
        fh.write("# RESULTS_R3.raw.tsv -- P05-S4 R3-4 run facts.  Written by run_r3_sweep.py.\n")
        fh.write("point_id\ttree\tmode\tcategory\tnth\texpected_class\tobserved_class\trc\trc1\trc2\thit\tinj_call\treason\tlog\n")
        for r in out:
            fh.write("\t".join(str(x) for x in r) + "\n")
    print("runs=%d" % len(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
