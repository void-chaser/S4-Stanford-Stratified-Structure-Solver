#!/usr/bin/env python3
# relr1_t2.py -- T2 of REL-R1: the project's three committed reference cases (testing/testcases.txt).
#   relr1_t2.py <tree> simple|fresnel|fanfig12   run build/S4 on the script, numdiff against the
#                                                committed reference with the committed tolerance
#   relr1_t2.py <tree> script                    run the project's own testing/runtests.sh
import os, sys, subprocess, datetime, hashlib

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

CASES = {
    "simple": ("examples/simple/simple.lua", "examples/simple/simple.txt", "1e-12"),
    "fresnel": ("examples/0d/fabry_perot/fresnel.lua", "examples/0d/fabry_perot/fresnel.txt", "1e-12"),
    "fanfig12": ("examples/2d/Fan_PRB_65_2002/fig12.lua", "examples/2d/Fan_PRB_65_2002/fig12.txt", "1e-10"),
}


def main():
    a = sys.argv[1:]
    if len(a) != 2:
        print("usage: relr1_t2.py <tree> <simple|fresnel|fanfig12|script>")
        return 2
    tree, case = a
    tdir = os.path.join(TREES, tree)
    cwd = os.path.join(EV, "run", "t2", tree, case)
    os.makedirs(cwd, exist_ok=True)
    outp = os.path.join(cwd, "out.stdout")
    errp = os.path.join(cwd, "out.stderr")
    if case == "script":
        unit_id = "T2_%s_runtests_sh" % tree
        r = run(["sh", "runtests.sh"], cwd=os.path.join(tdir, "testing"), out_path=outp, err_path=errp,
                timeout=600, env={"S4_BIN": "../build/S4", "TEST_MANIFEST": "testcases.txt"})
        status = "PASS" if r["rc"] == 0 else ("TIMEOUT" if r["timed_out"] == "YES" else "FAIL")
        rec = {"unit_id": unit_id, "suite": "T2_runtests_reference", "tree": tree, "pass": "1",
               "status": status, "rc": r["rc"], "signal": r["signal"], "timed_out": r["timed_out"],
               "stdout_sha256": sha_f(outp), "stderr_sha256": sha_f(errp),
               "stdout_path": os.path.relpath(outp, REPO), "stderr_path": os.path.relpath(errp, REPO),
               "reference_path": "", "numdiff_rc": "", "numdiff_relmax": "", "dur_s": r["dur_s"],
               "extra": "tmpfile.* written by runtests.sh inside the exported tree/testing and removed by its trap"}
        write_unit(rec)
        print("UNIT %s status=%s rc=%s" % (unit_id, status, r["rc"]))
        return 0 if status == "PASS" else 1
    if case not in CASES:
        print("unknown case " + case)
        return 2
    script, ref, tol = CASES[case]
    unit_id = "T2_%s_%s" % (tree, case)
    r = run([os.path.join(tdir, "build", "S4"), os.path.join(tdir, script)], cwd=cwd,
            out_path=outp, err_path=errp, timeout=600)
    nd_rc, nd_txt = numdiff(tree, os.path.join(tdir, ref), outp, tol)
    rel = relmax(os.path.join(tdir, ref), outp)
    status = "PASS" if r["rc"] == 0 and nd_rc == 0 else ("TIMEOUT" if r["timed_out"] == "YES" else "FAIL")
    rec = {"unit_id": unit_id, "suite": "T2_runtests_reference", "tree": tree, "pass": "1",
           "status": status, "rc": r["rc"], "signal": r["signal"], "timed_out": r["timed_out"],
           "stdout_sha256": sha_f(outp), "stderr_sha256": sha_f(errp),
           "stdout_path": os.path.relpath(outp, REPO), "stderr_path": os.path.relpath(errp, REPO),
           "reference_path": os.path.relpath(os.path.join(tdir, ref), REPO),
           "numdiff_rc": nd_rc, "numdiff_relmax": rel, "dur_s": r["dur_s"],
           "extra": "tol=%s numdiff_output=%s" % (tol, nd_txt)}
    write_unit(rec)
    print("UNIT %s status=%s rc=%s numdiff_rc=%s relmax=%s" % (unit_id, status, r["rc"], nd_rc, rel))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
