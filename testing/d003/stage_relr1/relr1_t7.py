#!/usr/bin/env python3
# relr1_t7.py -- T7 of REL-R1: fresh local clone of the repository, then one full 'make test' in the clone.
# The clone is written only under $EV/clone; the source repository is only read.
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

CLONE = os.path.join(EV, "clone", "relr1")
LOG = os.path.join(EV, "maketest", "T7_clone.log")
DONE = os.path.join(EV, "maketest", "T7_clone.done")


def main():
    out = os.path.join(EV, "run", "t7")
    os.makedirs(out, exist_ok=True)
    os.makedirs(os.path.join(EV, "maketest"), exist_ok=True)
    if os.path.isfile(LOG) and os.path.isfile(DONE):
        print("SKIP T7 (already complete)")
        return 0
    if os.path.isdir(CLONE) and os.listdir(CLONE):
        print("HARD_STOP clone directory is not empty: " + CLONE)
        return 2
    pc = subprocess.run(["git", "clone", "--no-hardlinks", REPO, CLONE], cwd=EV,
                        capture_output=True, text=True)
    open(os.path.join(out, "clone.log"), "w", encoding="utf-8").write(pc.stdout + pc.stderr)
    if pc.returncode != 0:
        print("HARD_STOP git clone rc=%d" % pc.returncode)
        return 2
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=CLONE, capture_output=True, text=True).stdout.strip()
    env = dict(os.environ)
    env["TMPDIR"] = os.path.join(EV, "tmp")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(LOG, "w", encoding="utf-8") as fh:
        fh.write("# make test in fresh clone %s (HEAD %s) utc=%s cwd=%s" % (CLONE, head, utc, os.path.join(EV, "clone/relr1")) + NL)
        fh.flush()
        p = subprocess.run(["make", "test", "PYTHON=python3"], cwd=CLONE, env=env,
                           stdout=fh, stderr=subprocess.STDOUT)
    open(DONE, "w", encoding="utf-8").write("clone_rc=%d utc=%s log_sha256=%s clone_head=%s" % (
        p.returncode, datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), sha_f(LOG), head) + NL)
    outp = os.path.join(out, "out.stdout")
    errp = os.path.join(out, "out.stderr")
    open(outp, "w", encoding="utf-8").write("make test rc=%d clone_head=%s" % (p.returncode, head) + NL)
    open(errp, "w", encoding="utf-8").write("")
    status = "PASS" if p.returncode == 0 else "FAIL"
    rec = {"unit_id": "T7_clone_maketest", "suite": "T7_fresh_clone", "tree": "CLONE", "pass": "1",
           "status": status, "rc": p.returncode, "signal": "NONE", "timed_out": "NO",
           "stdout_sha256": sha_f(outp), "stderr_sha256": sha_f(errp),
           "stdout_path": os.path.relpath(outp, REPO), "stderr_path": os.path.relpath(errp, REPO),
           "reference_path": "", "numdiff_rc": "", "numdiff_relmax": "", "dur_s": "recorded",
           "extra": "clone_head=" + head + " log=" + os.path.relpath(LOG, REPO)}
    write_unit(rec)
    print("UNIT T7_clone_maketest status=%s rc=%d clone_head=%s" % (status, p.returncode, head))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
