#!/usr/bin/env python3
# relr1_t4.py -- T4 of REL-R1: the P04 pipeline (testing/p04_run_all.sh) run inside the F4 exported tree.
# The pipeline is invoked from the exported tree so that ROOT is $EV/trees/F4 and every build it performs
# lands there; its OUT_DIR is $EV/p04run/F4.  The verdict is read from AGGREGATE.json ("overall").
# This is run last in the matrix because the pipeline rebuilds the F4 tree (rm -rf build).
import os, sys, subprocess, json, datetime, hashlib

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

OUT = os.path.join(EV, "p04run", "F4")


def main():
    logdir = os.path.join(EV, "logs")
    os.makedirs(logdir, exist_ok=True)
    log = os.path.join(logdir, "T4_p04_pipeline.log")
    outp = os.path.join(EV, "run", "t4", "out.stdout")
    errp = os.path.join(EV, "run", "t4", "out.stderr")
    os.makedirs(os.path.join(EV, "run", "t4"), exist_ok=True)
    if os.path.isdir(OUT) and os.listdir(OUT):
        print("HARD_STOP p04 output directory is not empty: " + OUT)
        return 2
    # Execution deviation recorded in ERRATA_RELR1.txt: $EV/trees/F4 is a git-archive export located INSIDE
    # the main repository's work tree, so the pipeline's "git -C ROOT archive 963ccf1" would archive the
    # subdirectory prefix (empty).  The same F4 tree is therefore checked out as its own repository via a
    # fresh local clone at $EV/t4src/F4 (HEAD 3de6d8b, S4/ tree hash verified equal to F4 before running).
    SRC = os.path.join(EV, "t4src", "F4")
    if not (os.path.isdir(SRC) and os.path.isfile(os.path.join(SRC, "Makefile"))):
        os.makedirs(os.path.join(EV, "t4src"), exist_ok=True)
        pc = subprocess.run(["git", "clone", "--no-hardlinks", REPO, SRC], cwd=os.path.join(EV, "t4src"),
                            capture_output=True, text=True)
        if pc.returncode != 0:
            print("HARD_STOP git clone for T4 rc=%d %s" % (pc.returncode, pc.stderr[:300]))
            return 2
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=SRC, capture_output=True, text=True).stdout.strip()
    s4 = subprocess.run(["git", "rev-parse", "HEAD:S4"], cwd=SRC, capture_output=True, text=True).stdout.strip()
    if head != "3de6d8bc7a35f036bf5ff6e508f5cdb5ef025505" or s4 != "589e15eb11fcb04e031b524f25a443e7921946cf":
        print("HARD_STOP T4 clone identity head=%s s4=%s" % (head, s4))
        return 2
    script = os.path.join(SRC, "testing", "p04_run_all.sh")
    env = dict(os.environ)
    env["TMPDIR"] = os.path.join(EV, "tmp")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    t0 = __import__("time").time()
    with open(log, "w", encoding="utf-8") as fh:
        fh.write("# sh %s %s cwd=%s utc=%s clone_head=%s clone_s4_tree=%s" % (script, OUT, SRC, utc, head, s4) + NL)
        fh.flush()
        p = subprocess.run(["sh", script, OUT], env=env, stdout=fh, stderr=subprocess.STDOUT)
    dur = "%.3f" % (__import__("time").time() - t0)
    agg = os.path.join(OUT, "AGGREGATE.json")
    overall = "MISSING"
    unexpected = "MISSING"
    if os.path.isfile(agg):
        try:
            j = json.load(open(agg, encoding="utf-8"))
            overall = j.get("overall", "MISSING")
            unexpected = ",".join(j.get("unexpected", [])) or "none"
        except Exception as exc:
            overall = "UNREADABLE:" + repr(exc)[:80]
    open(outp, "w", encoding="utf-8").write("pipeline_rc=%d aggregate_overall=%s unexpected=%s" % (p.returncode, overall, unexpected) + NL)
    open(errp, "w", encoding="utf-8").write("")
    status = "PASS" if (p.returncode == 0 and overall == "PASS") else "FAIL"
    rec = {"unit_id": "T4_F4_p04_pipeline", "suite": "T4_p04_pipeline", "tree": "F4", "pass": "1",
           "status": status, "rc": p.returncode, "signal": "NONE", "timed_out": "NO",
           "stdout_sha256": sha_f(outp), "stderr_sha256": sha_f(errp),
           "stdout_path": os.path.relpath(outp, REPO), "stderr_path": os.path.relpath(errp, REPO),
           "reference_path": "", "numdiff_rc": "", "numdiff_relmax": "", "dur_s": dur,
           "extra": "aggregate_overall=%s unexpected=%s log=%s tree_root=%s" % (overall, unexpected, os.path.relpath(log, REPO), os.path.relpath(SRC, REPO))}
    write_unit(rec)
    print("UNIT T4_F4_p04_pipeline status=%s pipeline_rc=%d aggregate_overall=%s" % (status, p.returncode, overall))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())