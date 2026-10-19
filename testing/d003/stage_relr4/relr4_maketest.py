#!/usr/bin/env python3
# relr4_maketest.py -- T5 of REL-R4: run 'make test' once on the F4 clone only (task brief section 5.6),
# confirming rc=0, unit_count=265 and no failures, so that the environment has not drifted.
# U has no 'test' target (recorded as U_UNAVAILABLE in the pre-registration).  Writes only under $EV.
import os, sys, subprocess, hashlib, datetime, re

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r4")
F4 = os.path.join(EV, "trees", "F4")
LOGS = os.path.join(EV, "maketest")
UNITS = os.path.join(EV, "units_t5")
TAB = chr(9)
NL = chr(10)


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def write_unit(rec):
    os.makedirs(UNITS, exist_ok=True)
    keys = ["unit_id", "suite", "tree", "status", "rc", "unit_count", "ran_lines", "failures", "stage_units", "detail",
            "log", "log_sha256", "utc"]
    out = os.path.join(UNITS, rec["unit_id"] + ".tsv")
    lines = ["# per-unit observation for REL-R4 T5; read by column name by relr4_verdict.py"]
    for k in keys:
        lines.append(k + TAB + str(rec.get(k, "")))
    open(out, "w", encoding="utf-8").write(NL.join(lines) + NL)


def main():
    os.makedirs(LOGS, exist_ok=True)
    log = os.path.join(LOGS, "F4_make_test.log")
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["TMPDIR"] = os.path.join(EV, "tmp")
    t0 = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(log, "w", encoding="utf-8") as fh:
        fh.write("# F4 make test (cwd=%s utc=%s PYTHON=python3)" % (os.path.relpath(F4, REPO), t0) + NL)
        p = subprocess.run(["make", "test", "PYTHON=python3"], cwd=F4, env=env, stdout=fh, stderr=subprocess.STDOUT)
    rc = p.returncode
    txt = open(log, encoding="utf-8", errors="replace").read()
    ran = [int(m.group(1)) for m in re.finditer(r"^Ran (\d+) tests?", txt, re.M)]
    # unit count follows the REL-R1/REL-R2 convention (and the S5R3 number 265): the unittest units plus
    # the four shell/selftest stages of 'make test': test-fast selftest, runtests.sh, the Lua negative
    # regression script and the Lua API negative script.
    STAGE_MARKERS = ["=== analytic reference self-check ===",
                     "=== S4 Lua test suite ===",
                     "=== S4 Lua test suite negative ===",
                     "=== S4 Lua API negative ==="]
    stage_units = len([m for m in STAGE_MARKERS if m in txt])
    unit_count = (sum(ran) if ran else 0) + stage_units
    failures = len(re.findall(r"^(FAIL|ERROR):", txt, re.M)) + len(re.findall(r"^FAILED \(", txt, re.M))
    ok = rc == 0 and unit_count == 265 and failures == 0
    write_unit({"unit_id": "T5_F4_make_test", "suite": "T5_make_test", "tree": "F4",
                "status": "PASS" if ok else "FAIL", "rc": rc, "unit_count": unit_count,
                "ran_lines": ",".join(str(x) for x in ran), "failures": failures, "stage_units": stage_units,
                "detail": "make test on the F4 clone; expected rc=0, unit_count=265, no FAIL/ERROR lines",
                "log": os.path.relpath(log, REPO), "log_sha256": sha_f(log),
                "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
    # record the U unavailability fact (U's Makefile has no 'test' target)
    mt = open(os.path.join(F4, "Makefile.common"), encoding="utf-8", errors="replace").read()
    write_unit({"unit_id": "T5_U_make_test", "suite": "T5_make_test", "tree": "U", "status": "U_UNAVAILABLE",
                "rc": "", "unit_count": "", "ran_lines": "", "failures": "",
                "detail": "U tree (7fd00a2) has no 'test' target; recorded as U_UNAVAILABLE per task brief section 5.6",
                "log": "", "log_sha256": "", "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
    print("MAKETEST rc=%d unit_count=%d failures=%d status=%s" % (rc, unit_count, failures, "PASS" if ok else "FAIL"))
    print("WROTE " + os.path.relpath(os.path.join(UNITS, "T5_F4_make_test.tsv"), REPO))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())