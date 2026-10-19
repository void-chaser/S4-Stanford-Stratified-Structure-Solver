#!/usr/bin/env python3
# relr4_examples.py -- T1 of REL-R4: run every examples/*.lua (all 51, including the two MPI_example
# scripts which run here on the NON-MPI build/S4, i.e. MPIRank=0 / MPISize=1) in its own isolated cwd,
# for the three reference trees and two passes, recording facts only: rc, signal, timeout, stdout/stderr
# sha256 and paths, the files the process wrote, duration.
#   run-unit --example REL --tree T --pass P    one unit (this exact command is pre-registered)
#   matrix --tree T [--jobs 4]                   driver: runs the pre-registered run-unit commands of
#                                                tree T with fixed concurrency 4 and the pre-registered 3600 s timeout
import os, sys, subprocess, hashlib, datetime, time
from concurrent.futures import ThreadPoolExecutor

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r4")
TREES = {"U": os.path.join(EV, "upstream", "S4"),
         "B": os.path.join(EV, "trees", "B"),
         "F4": os.path.join(EV, "trees", "F4"),
         "M": os.path.join(EV, "trees", "M"),
         "M2": os.path.join(EV, "trees", "M2"),
         "M3": os.path.join(EV, "trees", "M3")}
UNITS = os.path.join(EV, "units_t1")
TAB = chr(9)
NL = chr(10)
TIMEOUT_S = 3600
JOBS = 4


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def eid_of(rel):
    s = rel[len("examples/"):].replace("/", "__")
    return s[:-4] if s.endswith(".lua") else s


def write_unit(rec):
    os.makedirs(UNITS, exist_ok=True)
    keys = ["unit_id", "suite", "tree", "pass", "example", "status", "rc", "signal", "timed_out",
            "stdout_sha256", "stderr_sha256", "stdout_path", "stderr_path", "files", "dur_s", "utc", "command"]
    out = os.path.join(UNITS, rec["unit_id"] + ".tsv")
    lines = ["# per-unit observation for REL-R4 T1; read by column name by relr4_verdict.py"]
    for k in keys:
        lines.append(k + TAB + str(rec.get(k, "")))
    open(out, "w", encoding="utf-8").write(NL.join(lines) + NL)


def run_unit(rel, tree, pas):
    tdir = TREES[tree]
    exe = os.path.join(tdir, "build", "S4")
    script = os.path.join(tdir, rel)
    eid = eid_of(rel)
    unit_id = "T1_%s_%s_p%s" % (eid, tree, pas)
    cwd = os.path.join(EV, "run", tree, pas, eid)
    done = os.path.join(UNITS, unit_id + ".tsv")
    if os.path.isfile(done):
        print("SKIP %s (already complete)" % unit_id)
        return 0
    os.makedirs(cwd, exist_ok=True)
    if not os.path.isfile(exe):
        raise SystemExit("HARD_STOP missing executable " + exe)
    if not os.path.isfile(script):
        raise SystemExit("HARD_STOP missing script " + script)
    outp = os.path.join(cwd, "out.stdout")
    errp = os.path.join(cwd, "out.stderr")
    t0 = time.time()
    timed_out = "NO"
    rc = None
    signal = "NONE"
    try:
        with open(outp, "wb") as fo, open(errp, "wb") as fe:
            p = subprocess.run([exe, script], cwd=cwd, stdin=subprocess.DEVNULL, stdout=fo, stderr=fe,
                               timeout=TIMEOUT_S)
        rc = p.returncode
        if rc < 0:
            signal = str(-rc)
    except subprocess.TimeoutExpired:
        timed_out = "YES"
        rc = "TIMEOUT"
        signal = "TIMEOUT"
    dur = "%.3f" % (time.time() - t0)
    files = []
    for root, dirs, fs in os.walk(cwd):
        for f in sorted(fs):
            full = os.path.join(root, f)
            base = os.path.relpath(full, cwd)
            if base in ("out.stdout", "out.stderr"):
                continue
            files.append(base + ":" + sha_f(full))
    status = "TIMEOUT" if timed_out == "YES" else ("RAN_OK" if rc == 0 else "RAN_FAIL")
    rec = {"unit_id": unit_id, "suite": "T1_examples", "tree": tree, "pass": pas, "example": rel,
           "status": status, "rc": rc, "signal": signal, "timed_out": timed_out,
           "stdout_sha256": sha_f(outp), "stderr_sha256": sha_f(errp),
           "stdout_path": os.path.relpath(outp, REPO), "stderr_path": os.path.relpath(errp, REPO),
           "files": ";".join(files) if files else "none", "dur_s": dur,
           "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "command": "build/S4 " + rel}
    write_unit(rec)
    print("UNIT %-72s rc=%s signal=%s dur=%ss" % (unit_id, rc, signal, dur))
    return 0


def read_prereg():
    rows, hdr = [], None
    for line in open(os.path.join(EV, "PREREG_RELR4.tsv"), encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if hdr is None:
            hdr = f
            continue
        if len(f) != len(hdr):
            continue
        rows.append(dict(zip(hdr, f)))
    return rows


def matrix(tree):
    cmds = []
    for r in read_prereg():
        if r["suite"] != "T1_examples" or r["tree"] != tree:
            continue
        cmds.append(r["command"].split())
    cmds.sort(key=lambda c: (c[-1], c[-3]))  # pass then example, deterministic order
    print("MATRIX tree=%s units=%d jobs=%d timeout_s=%d" % (tree, len(cmds), JOBS, TIMEOUT_S))
    sys.stdout.flush()
    bad = []

    def one(cmd):
        p = subprocess.run(cmd, cwd=REPO)
        if p.returncode != 0:
            bad.append(" ".join(cmd))
        return p.returncode

    with ThreadPoolExecutor(max_workers=JOBS) as ex:
        list(ex.map(one, cmds))
    if bad:
        print("MATRIX_FAILURES=%d" % len(bad))
        for b in bad[:10]:
            print("FAILED " + b)
        return 1
    print("MATRIX %s DONE %d units" % (tree, len(cmds)))
    return 0


def main():
    a = sys.argv[1:]
    if not a:
        print("usage: relr4_examples.py run-unit --example REL --tree T --pass P | matrix --tree T")
        return 2
    if a[0] == "run-unit":
        rel = a[a.index("--example") + 1]
        tree = a[a.index("--tree") + 1]
        pas = a[a.index("--pass") + 1]
        return run_unit(rel, tree, pas)
    if a[0] == "matrix":
        return matrix(a[a.index("--tree") + 1])
    print("unknown mode " + a[0])
    return 2


if __name__ == "__main__":
    sys.exit(main())