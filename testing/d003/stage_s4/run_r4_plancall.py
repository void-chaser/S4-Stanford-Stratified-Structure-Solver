#!/usr/bin/env python3
# run_r4_plancall.py -- P05-S4 R4-4 step 4: run the 22 R3 INVALID plan points with the new injector (plancall:K:M).
# New file.  judge_d003.py and matrix_r2.py are IMPORTED, not modified.
#
#   python3 -I -B testing/d003/stage_s4/run_r4_plancall.py PREREG_B DRIVER_B DRIVER_F OUTDIR PASS
#
#   PREREG_B : REGISTRY_S4_PRE_R4_B.tsv (hash-locked; 12 columns, 44 rows = 22 points x B,F)
#   PASS     : 1 or 2 (each point is run twice)
# Each row: request = plancall:K:M from the registry; NG 9; stack pattern; NTH "-" (not used by plancall).
# The class is judge_d003.classify on facts (rc, rc1, rc2, hit), with inj_call from the registry (not guessed).
# The request is checked here against the strict form plancall:<K>:<M> (matrix_r2.request_ok does not know it).
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
D003 = os.path.join(REPO, "testing", "d003")
sys.path.insert(0, D003)

import judge_d003 as J  # noqa: E402
import matrix_r2 as M  # noqa: E402

PLANCALL_RE = re.compile(r"^plancall:([1-9][0-9]*):([1-9][0-9]*)$")
HEADER = ["point_id", "r1_id", "tree", "route", "mode", "nth_K", "M", "request", "inj_call", "expected_class", "basis", "status"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    rows = []
    header = None
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                if f != HEADER:
                    raise SystemExit("REFUSED: appendix header mismatch")
                header = f
                continue
            if len(f) != 12:
                raise SystemExit("REFUSED: appendix line %d has %d fields" % (lineno, len(f)))
            d = dict(zip(HEADER, f))
            if d["tree"] not in ("B", "F"):
                raise SystemExit("REFUSED: bad tree at line %d" % lineno)
            if not PLANCALL_RE.match(d["request"]):
                raise SystemExit("REFUSED: request not plancall:K:M at line %d: %r" % (lineno, d["request"]))
            k, m = PLANCALL_RE.match(d["request"]).groups()
            if k != d["nth_K"] or m != d["M"]:
                raise SystemExit("REFUSED: request/K/M disagree at line %d" % lineno)
            if d["inj_call"] not in ("1", "2"):
                raise SystemExit("REFUSED: inj_call must be 1 or 2 at line %d" % lineno)
            rows.append(d)
    return rows


def main(argv):
    if len(argv) != 6:
        raise SystemExit("usage: run_r4_plancall.py PREREG_B DRIVER_B DRIVER_F OUTDIR PASS")
    prereg, drv_b, drv_f, outdir, pas = argv[1:6]
    if pas not in ("1", "2"):
        raise SystemExit("PASS must be 1 or 2")
    drivers = {"B": drv_b, "F": drv_f}
    for t, p in drivers.items():
        if not (os.path.isfile(p) and os.access(p, os.X_OK)):
            raise SystemExit("REFUSED: driver missing for %s: %s" % (t, p))
    os.makedirs(outdir, exist_ok=True)
    runs = os.path.join(outdir, "runs")
    os.makedirs(runs, exist_ok=True)
    rows = load(prereg)
    out = []
    for d in rows:
        mrow = {"case": "R4B-" + d["point_id"] + "-" + d["tree"], "family": "R4B", "tree": d["tree"],
                "request": d["request"], "nth": "-", "stack": "pattern", "mode": d["mode"], "ng": "9",
                "expected": d["expected_class"], "basis": d["basis"], "lineno": 0}
        rc, log = M.run_row(drivers[d["tree"]], mrow, runs)
        with open(log, "rb") as fh:
            text = fh.read().decode("utf-8", errors="replace")
        facts = J.facts_from_log(text)
        cls, label, reason = J.classify(rc, facts["rc1"], facts["rc2"], facts["hit"],
                                        control=False, real=True, inj_call=int(d["inj_call"]))
        if cls == "UNDECLARED":
            raise SystemExit("UNDECLARED for %s: stop" % d["point_id"])
        if facts["hit"] == 0:
            match = "INVALID"
        elif cls == d["expected_class"]:
            match = "MATCH"
        else:
            match = "MISMATCH"
        out.append((d, rc, facts, cls, match, reason + (" " + label if label else ""), log))
    path = os.path.join(outdir, "RESULTS_R4_PLANCALL_pass%s.tsv" % pas)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# RESULTS_R4_PLANCALL_pass%s.tsv -- R4-4 step 4 (22 R3 INVALID plan points, B and F).\n" % pas)
        fh.write("point_id\ttree\troute\tmode\tnth_K\tM\trequest\tinj_call\texpected\tobserved\tmatch\trc\trc1\trc2\thit\treason\tlog_sha256\n")
        for d, rc, facts, cls, match, reason, log in out:
            fh.write("\t".join([d["point_id"], d["tree"], d["route"], d["mode"], d["nth_K"], d["M"], d["request"],
                                d["inj_call"], d["expected_class"], cls, match, str(rc), str(facts["rc1"]),
                                str(facts["rc2"]), str(facts["hit"]), reason, sha256(log)]) + "\n")
    counts = {}
    for item in out:
        counts[item[4]] = counts.get(item[4], 0) + 1
    print("pass=%s rows=%d counts=%s" % (pas, len(out), counts))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
