#!/usr/bin/env python3
# run_r5_planm.py -- P05-S4 R5-3 step 3: run the M>=2 plan points (plancall:K:2) on plain B and plain F, two passes.
# New file.  judge_d003.py is IMPORTED (not modified).  matrix_r2.py is NOT used: its build_env sets S4FMM_TWICE only for
# case names starting with "t4/", and the R4 plancall runner never set it, so the R4 twice rows ran WITHOUT the second-call
# route (R5-2 finding).  This runner sets S4FMM_TWICE=slab explicitly for route "twice" and nothing for "once".
#
#   python3 -I -B testing/d003/stage_s4/run_r5_planm.py PREREG DRV_B DRV_F OUTDIR PASS
#
# Class: judge_d003.classify on facts (rc, rc1, rc2, hit) only; inj_call from the pre-registration (not guessed).
# Output: OUTDIR/RESULTS_R5_PLANM_pass<PASS>.tsv  and  OUTDIR/runs/<point>__<tree>.log
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
D003 = os.path.join(REPO, "testing", "d003")
sys.path.insert(0, D003)

import judge_d003 as J  # noqa: E402

GRID = ["pattern", "both", "4", "3"]
TIMEOUT_S = 300
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
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                if f != HEADER:
                    raise SystemExit("REFUSED: prereg header mismatch")
                header = f
                continue
            if len(f) != 12:
                raise SystemExit("REFUSED: prereg line has %d fields" % len(f))
            d = dict(zip(HEADER, f))
            if d["tree"] not in ("B", "F"):
                raise SystemExit("REFUSED: bad tree")
            m = PLANCALL_RE.match(d["request"])
            if not m or m.group(1) != d["nth_K"] or m.group(2) != d["M"]:
                raise SystemExit("REFUSED: request/K/M disagree for %s" % d["point_id"])
            if d["inj_call"] not in ("1", "2"):
                raise SystemExit("REFUSED: inj_call must be 1 or 2")
            if d["route"] not in ("once", "twice"):
                raise SystemExit("REFUSED: route must be once or twice")
            rows.append(d)
    return rows


def run_one(driver, d, runs_dir):
    env = dict(os.environ)
    env.pop("S4FMM_TWICE", None)
    env["FMM_MODE"] = d["mode"]
    env["S4FMM_NG"] = "9"
    env["S4FMM_INJECT"] = d["request"]
    if d["route"] == "twice":
        env["S4FMM_TWICE"] = "slab"
    name = "%s__%s" % (d["point_id"], d["tree"])
    log = os.path.join(runs_dir, name + ".log")
    rc = None
    out = b""
    try:
        proc = subprocess.run([driver] + GRID, env=env, cwd=runs_dir, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=TIMEOUT_S)
        rc = proc.returncode
        out = proc.stdout
    except subprocess.TimeoutExpired as exc:
        rc = 124
        out = exc.stdout or b""
    except OSError as exc:
        out = ("RUNNER: could not start driver: %s\n" % exc).encode()
    if rc is not None and rc < 0:
        rc = 128 - rc
    with open(log, "wb") as fh:
        fh.write(out)
    return rc, log


def main(argv):
    if len(argv) != 6:
        raise SystemExit("usage: run_r5_planm.py PREREG DRV_B DRV_F OUTDIR PASS")
    prereg, drv_b, drv_f, outdir, pas = argv[1:6]
    if pas not in ("1", "2"):
        raise SystemExit("PASS must be 1 or 2")
    drivers = {"B": drv_b, "F": drv_f}
    for t, p in drivers.items():
        if not (os.path.isfile(p) and os.access(p, os.X_OK)):
            raise SystemExit("REFUSED: driver missing for %s" % t)
    runs = os.path.join(outdir, "runs")
    os.makedirs(runs, exist_ok=True)
    rows = load(prereg)
    out = []
    for d in rows:
        rc, log = run_one(drivers[d["tree"]], d, runs)
        with open(log, "rb") as fh:
            text = fh.read().decode("utf-8", errors="replace")
        facts = J.facts_from_log(text)
        cls, label, reason = J.classify(rc, facts["rc1"], facts["rc2"], facts["hit"],
                                        control=False, real=True, inj_call=int(d["inj_call"]))
        if cls == "UNDECLARED":
            raise SystemExit("UNDECLARED for %s: stop" % d["point_id"])
        if facts["hit"] == 0:
            match = "INVALID"
        elif d["expected_class"] == "UNKNOWN":
            match = "NO_EXPECTATION"
        elif cls == d["expected_class"]:
            match = "MATCH"
        else:
            match = "MISMATCH"
        out.append((d, rc, facts, cls, match, reason + (" " + label if label else ""), log))
    path = os.path.join(outdir, "RESULTS_R5_PLANM_pass%s.tsv" % pas)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# RESULTS_R5_PLANM_pass%s.tsv -- P05-S4 R5-3 step 3 (M=2 plan points, B and F).  Class from judge_d003.classify (facts only).\n" % pas)
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
