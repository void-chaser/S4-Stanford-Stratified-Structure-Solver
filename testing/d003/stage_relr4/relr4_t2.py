#!/usr/bin/env python3
# relr4_t2.py -- T2 of REL-R4: the project's three committed reference cases (testing/testcases.txt).
# Per task brief section 5.2 each tree runs the F4 tree's test harness with its own binary:
#   case --tree T --case C : run tree T's build/S4 on the F4 tree's script, numdiff against the F4
#                            tree's committed reference with the committed tolerance
#   sh --tree T            : the F4 tree's testing/runtests.sh with S4_BIN=<tree>/build/S4
#   u-own                  : the ORIGINAL U tree's own testing/runtests.sh + testing/testcases.txt,
#                            read-only recording of whether the original regression suite can run
import os, sys, subprocess, hashlib, datetime, time

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r4")
TREES = {"U": os.path.join(EV, "upstream", "S4"),
         "B": os.path.join(EV, "trees", "B"),
         "F4": os.path.join(EV, "trees", "F4"),
         "M": os.path.join(EV, "trees", "M"),
         "M2": os.path.join(EV, "trees", "M2"),
         "M3": os.path.join(EV, "trees", "M3")}
REF = TREES["F4"]
UNITS = os.path.join(EV, "units_t2")
TAB = chr(9)
NL = chr(10)
CASES = {
    "simple": ("examples/simple/simple.lua", "examples/simple/simple.txt", "1e-12"),
    "fresnel": ("examples/0d/fabry_perot/fresnel.lua", "examples/0d/fabry_perot/fresnel.txt", "1e-12"),
    "fanfig12": ("examples/2d/Fan_PRB_65_2002/fig12.lua", "examples/2d/Fan_PRB_65_2002/fig12.txt", "1e-10"),
}


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def write_unit(rec):
    os.makedirs(UNITS, exist_ok=True)
    keys = ["unit_id", "suite", "tree", "pass", "status", "rc", "signal", "timed_out", "stdout_sha256",
            "stderr_sha256", "stdout_path", "stderr_path", "reference_path", "numdiff_rc", "numdiff_relmax",
            "dur_s", "utc", "extra"]
    out = os.path.join(UNITS, rec["unit_id"] + ".tsv")
    lines = ["# per-unit observation for REL-R4 T2; read by column name by relr4_verdict.py"]
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
    return "%.6e" % m


def run(cmd, cwd, out_path, err_path, timeout, env_extra=None):
    e = dict(os.environ)
    e["TMPDIR"] = os.path.join(EV, "tmp")
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    e.pop("S4_BIN", None)
    if env_extra:
        e.update(env_extra)
    t0 = time.time()
    timed_out = "NO"
    try:
        with open(out_path, "wb") as fo, open(err_path, "wb") as fe:
            p = subprocess.run(cmd, cwd=cwd, env=e, stdin=subprocess.DEVNULL, stdout=fo, stderr=fe, timeout=timeout)
        rc = p.returncode
        signal = "NONE" if rc >= 0 else str(-rc)
    except subprocess.TimeoutExpired:
        rc, signal, timed_out = "TIMEOUT", "TIMEOUT", "YES"
    return rc, signal, timed_out, "%.3f" % (time.time() - t0)


def case(tree, cid):
    script, ref, tol = CASES[cid]
    tdir = TREES[tree]
    cwd = os.path.join(EV, "run", "t2", tree, cid)
    os.makedirs(cwd, exist_ok=True)
    outp = os.path.join(cwd, "out.stdout")
    errp = os.path.join(cwd, "out.stderr")
    rc, signal, timed_out, dur = run([os.path.join(tdir, "build", "S4"), os.path.join(REF, script)],
                                     cwd, outp, errp, 600)
    nd = subprocess.run(["perl", os.path.join(REF, "testing", "numdiff"), os.path.join(REF, ref), outp, tol],
                        cwd=EV, capture_output=True, text=True)
    rel = relmax(os.path.join(REF, ref), outp)
    status = "PASS_REF" if rc == 0 and nd.returncode == 0 else ("TIMEOUT" if timed_out == "YES" else "FAIL_REF")
    unit_id = "T2_%s_%s" % (tree, cid)
    rec = {"unit_id": unit_id, "suite": "T2_runtests_reference", "tree": tree, "pass": "1", "status": status,
           "rc": rc, "signal": signal, "timed_out": timed_out, "stdout_sha256": sha_f(outp),
           "stderr_sha256": sha_f(errp), "stdout_path": os.path.relpath(outp, REPO),
           "stderr_path": os.path.relpath(errp, REPO), "reference_path": os.path.relpath(os.path.join(REF, ref), REPO),
           "numdiff_rc": nd.returncode, "numdiff_relmax": rel, "dur_s": dur,
           "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "extra": "tol=%s numdiff_output=%s" % (tol, (nd.stdout or "").strip().replace(NL, " ")[:250])}
    write_unit(rec)
    print("UNIT %s status=%s rc=%s numdiff_rc=%s relmax=%s" % (unit_id, status, rc, nd.returncode, rel))
    return 0 if status == "PASS_REF" else 1


def sh_case(tree):
    tdir = TREES[tree]
    cwd = os.path.join(EV, "run", "t2", tree, "script")
    os.makedirs(cwd, exist_ok=True)
    outp = os.path.join(cwd, "out.stdout")
    errp = os.path.join(cwd, "out.stderr")
    # runs the F4 tree's harness (and its numdiff), with the tree's binary as the system under test
    rc, signal, timed_out, dur = run(["sh", "runtests.sh"], os.path.join(REF, "testing"), outp, errp, 600,
                                     {"S4_BIN": os.path.join(tdir, "build", "S4")})
    status = "PASS_REF" if rc == 0 else ("TIMEOUT" if timed_out == "YES" else "FAIL")
    unit_id = "T2_%s_runtests_sh" % tree
    rec = {"unit_id": unit_id, "suite": "T2_runtests_reference", "tree": tree, "pass": "1", "status": status,
           "rc": rc, "signal": signal, "timed_out": timed_out, "stdout_sha256": sha_f(outp),
           "stderr_sha256": sha_f(errp), "stdout_path": os.path.relpath(outp, REPO),
           "stderr_path": os.path.relpath(errp, REPO), "reference_path": "", "numdiff_rc": "",
           "numdiff_relmax": "", "dur_s": dur,
           "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "extra": "cwd=%s S4_BIN=%s" % (os.path.relpath(os.path.join(REF, "testing"), REPO), os.path.join(tdir, "build", "S4"))}
    write_unit(rec)
    print("UNIT %s status=%s rc=%s" % (unit_id, status, rc))
    return 0 if status == "PASS_REF" else 1


def u_own():
    udir = TREES["U"]
    cwd = os.path.join(EV, "run", "t2", "U", "own_manifest")
    os.makedirs(cwd, exist_ok=True)
    outp = os.path.join(cwd, "out.stdout")
    errp = os.path.join(cwd, "out.stderr")
    rc, signal, timed_out, dur = run(["sh", "runtests.sh"], os.path.join(udir, "testing"), outp, errp, 600,
                                     {"S4_BIN": "../build/S4", "TEST_MANIFEST": "testcases.txt",
                                      "TEST_EXAMPLES_DIR": "../examples", "DIFF": "./numdiff"})
    txt = open(outp, encoding="utf-8", errors="replace").read()
    miss_base = txt.count("Baseline file")
    miss_script = txt.count("Lua script")
    status = "UNRUNNABLE" if rc != 0 else "RAN"
    unit_id = "T2_U_OWN_MANIFEST"
    rec = {"unit_id": unit_id, "suite": "T2_runtests_reference", "tree": "U", "pass": "1", "status": status,
           "rc": rc, "signal": signal, "timed_out": timed_out, "stdout_sha256": sha_f(outp),
           "stderr_sha256": sha_f(errp), "stdout_path": os.path.relpath(outp, REPO),
           "stderr_path": os.path.relpath(errp, REPO), "reference_path": "", "numdiff_rc": "",
           "numdiff_relmax": "", "dur_s": dur,
           "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "extra": "missing_baseline_lines=%d missing_script_lines=%d (original testing/testcases.txt has 10 cases)" % (miss_base, miss_script)}
    write_unit(rec)
    print("UNIT %s status=%s rc=%s missing_baseline=%d missing_script=%d" % (unit_id, status, rc, miss_base, miss_script))
    return 0


def main():
    a = sys.argv[1:]
    if not a:
        print("usage: relr4_t2.py case --tree T --case C | sh --tree T | u-own")
        return 2
    if a[0] == "case":
        return case(a[a.index("--tree") + 1], a[a.index("--case") + 1])
    if a[0] == "sh":
        return sh_case(a[a.index("--tree") + 1])
    if a[0] == "u-own":
        return u_own()
    print("unknown mode " + a[0])
    return 2


if __name__ == "__main__":
    sys.exit(main())