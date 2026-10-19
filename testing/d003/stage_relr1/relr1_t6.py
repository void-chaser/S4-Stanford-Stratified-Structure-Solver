#!/usr/bin/env python3
# relr1_t6.py -- T6 of REL-R1: examples/C_api built and run from each exported tree.
# The shipped examples/C_api/Makefile is macOS-only (-framework Accelerate -lc++).  The round records a
# make attempt for the record, then builds the same main.c with the Linux libraries of this project
# (reviewed in WRITE_TARGETS_RELR1.tsv before running) and compares against the committed spec.awk.out.
import os, sys, subprocess, shutil, hashlib

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
    if len(a) != 1:
        print("usage: relr1_t6.py <tree>")
        return 2
    tree = a[0]
    tdir = os.path.join(TREES, tree)
    src = os.path.join(tdir, "examples", "C_api")
    cwd = os.path.join(EV, "run", "t6", tree)
    os.makedirs(cwd, exist_ok=True)
    for f in ("main.c", "Makefile", "spec.awk", "spec.awk.out"):
        shutil.copyfile(os.path.join(src, f), os.path.join(cwd, f))
    outp = os.path.join(cwd, "out.stdout")
    errp = os.path.join(cwd, "out.stderr")
    # 1. shipped Makefile attempt (recorded only)
    r_make = run(["make"], cwd=cwd, out_path=os.path.join(cwd, "make.stdout"),
                 err_path=os.path.join(cwd, "make.stderr"), timeout=120)
    # 2. Linux build of the same main.c against this tree's build/libS4.a
    cc = ["cc", "-O0", "-g", "-I" + os.path.join(tdir, "S4"), "main.c", "-o", "fig12",
          "-L" + os.path.join(tdir, "build"), "-lS4", "-llapack", "-lblas", "-lstdc++", "-lm"]
    r_cc = run(cc, cwd=cwd, out_path=os.path.join(cwd, "cc.stdout"), err_path=os.path.join(cwd, "cc.stderr"),
               timeout=300)
    outtxt = os.path.join(cwd, "out.txt")
    status = "FAIL"
    nd_rc = ""
    rel = ""
    r_awk = {"rc": "SKIP", "signal": "SKIP", "timed_out": "NO", "dur_s": "0"}
    if r_cc["rc"] == 0:
        with open(outtxt, "wb") as fh:
            p = subprocess.run(["awk", "-f", "spec.awk"], cwd=cwd, stdin=subprocess.DEVNULL, stdout=fh,
                               stderr=open(errp, "wb"), timeout=600)
        r_awk = {"rc": p.returncode, "signal": "NONE" if p.returncode >= 0 else str(-p.returncode),
                 "timed_out": "NO", "dur_s": "recorded"}
        ref = os.path.join(cwd, "spec.awk.out")
        nd_rc, nd_txt = numdiff(tree, ref, outtxt, "1e-12")
        rel = relmax(ref, outtxt)
        status = "PASS" if (p.returncode == 0 and nd_rc == 0) else "FAIL"
    rec = {"unit_id": "T6_%s_capi" % tree, "suite": "T6_c_api", "tree": tree, "pass": "1",
           "status": status, "rc": r_awk["rc"], "signal": r_awk["signal"], "timed_out": r_awk["timed_out"],
           "stdout_sha256": sha_f(outtxt) if os.path.isfile(outtxt) else "MISSING",
           "stderr_sha256": sha_f(errp) if os.path.isfile(errp) else "MISSING",
           "stdout_path": os.path.relpath(outtxt, REPO) if os.path.isfile(outtxt) else "",
           "stderr_path": os.path.relpath(errp, REPO) if os.path.isfile(errp) else "",
           "reference_path": os.path.relpath(os.path.join(cwd, "spec.awk.out"), REPO),
           "numdiff_rc": nd_rc, "numdiff_relmax": rel, "dur_s": r_awk["dur_s"],
           "extra": "shipped_makefile_rc=%s (macOS-only flags) linux_cc_rc=%s spec_awk_rc=%s" %
                    (r_make["rc"], r_cc["rc"], r_awk["rc"])}
    write_unit(rec)
    print("UNIT T6_%s_capi status=%s make_rc=%s cc_rc=%s awk_rc=%s numdiff_rc=%s relmax=%s" %
          (tree, status, r_make["rc"], r_cc["rc"], r_awk["rc"], nd_rc, rel))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
