#!/usr/bin/env python3
# relr1_t5.py -- T5 of REL-R1: the two P04 unit suites run from each exported tree.
#   relr1_t5.py <tree> p04_aggregate|d002
import os, sys, subprocess, hashlib

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r1")
TREES = os.path.join(EV, "trees")
UNITS = os.path.join(EV, "units")
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
    keys = ["unit_id", "suite", "tree", "pass", "status", "rc", "signal", "timed_out",
            "stdout_sha256", "stderr_sha256", "stdout_path", "stderr_path", "reference_path",
            "numdiff_rc", "numdiff_relmax", "dur_s", "extra"]
    out = os.path.join(UNITS, rec["unit_id"] + ".tsv")
    lines = ["# per-unit observation for REL-R1; read by column name by relr1_verdict.py"]
    for k in keys:
        lines.append(k + TAB + str(rec.get(k, "")))
    open(out, "w", encoding="utf-8").write(NL.join(lines) + NL)


def relmax(p1, p2):
    try:
        a = open(p1, encoding="utf-8", errors="replace").read().split()
        b = open(p2, encoding="utf-8", errors="replace").read().split()
    except OSError:
        return "NONE"
    if len(a) != len(b):
        return "LEN_DIFF"
    m = 0.0
    for x, y in zip(a, b):
        try:
            fx, fy = float(x), float(y)
        except ValueError:
            if x != y:
                return "NONNUMERIC_DIFF"
            continue
        m = max(m, abs(fx - fy) / max(abs(fx), abs(fy), 1e-300))
    return "%.3e" % m


def run(cmd, cwd, out_path, err_path, timeout, env=None):
    import subprocess, time
    t0 = time.time()
    e = dict(os.environ)
    if env:
        e.update(env)
    e["TMPDIR"] = os.path.join(EV, "tmp")
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        with open(out_path, "wb") as fo, open(err_path, "wb") as fe:
            p = subprocess.run(cmd, cwd=cwd, env=e, stdin=subprocess.DEVNULL, stdout=fo, stderr=fe,
                               timeout=timeout)
        rc, signal, timed_out = p.returncode, ("NONE" if p.returncode >= 0 else str(-p.returncode)), "NO"
        if rc < 0:
            rc = "SIGNAL"
    except Exception as exc:
        if exc.__class__.__name__ == "TimeoutExpired":
            rc, signal, timed_out = "TIMEOUT", "TIMEOUT", "YES"
        else:
            raise
    return {"rc": rc, "signal": signal, "timed_out": timed_out, "dur_s": "%.3f" % (time.time() - t0)}


def numdiff(tree, f1, f2, tol):
    import subprocess
    tool = os.path.join(TREES, tree, "testing", "numdiff")
    p = subprocess.run(["perl", tool, f1, f2, tol], cwd=EV, capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip().replace(NL, " ")[:300]



def main():
    a = sys.argv[1:]
    if len(a) != 2:
        print("usage: relr1_t5.py <tree> p04_aggregate|d002")
        return 2
    tree, name = a
    tdir = os.path.join(TREES, tree)
    paths = {"p04_aggregate": "testing/p04_aggregate_test.py", "d002": "testing/d002/test_run_d002.py"}
    if name not in paths:
        print("unknown test " + name)
        return 2
    script = os.path.join(tdir, paths[name])
    cwd = os.path.join(EV, "run", "t5", tree, name)
    os.makedirs(cwd, exist_ok=True)
    outp = os.path.join(cwd, "out.stdout")
    errp = os.path.join(cwd, "out.stderr")
    unit_id = "T5_%s_%s" % (tree, name)
    r = run(["python3", "-I", "-B", script], cwd=cwd, out_path=outp, err_path=errp, timeout=1800)
    status = "PASS" if r["rc"] == 0 else ("TIMEOUT" if r["timed_out"] == "YES" else "FAIL")
    rec = {"unit_id": unit_id, "suite": "T5_p04_unit_tests", "tree": tree, "pass": "1",
           "status": status, "rc": r["rc"], "signal": r["signal"], "timed_out": r["timed_out"],
           "stdout_sha256": sha_f(outp), "stderr_sha256": sha_f(errp),
           "stdout_path": os.path.relpath(outp, REPO), "stderr_path": os.path.relpath(errp, REPO),
           "reference_path": "", "numdiff_rc": "", "numdiff_relmax": "", "dur_s": r["dur_s"],
           "extra": "script=" + paths[name]}
    write_unit(rec)
    print("UNIT %s status=%s rc=%s" % (unit_id, status, r["rc"]))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
