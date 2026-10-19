#!/usr/bin/env python3
# relr1_examples.py -- T3 of REL-R1: run every examples/*.lua (except the two MPI scripts declared
# SKIP_DECLARED) in its own isolated cwd, for both trees and two passes, and record the facts only:
# rc, signal, timeout, stdout/stderr sha256 + paths, files written by the process, duration.
# Modes:
#   run-unit --example REL --tree T --pass P   one unit (this exact command is pre-registered)
#   matrix --tree T [--jobs 4]                 driver: runs the pre-registered run-unit commands of tree T
#                                              with a fixed concurrency of 4 and the pre-registered 3600 s timeout
import os, sys, subprocess, hashlib, datetime, time
from concurrent.futures import ThreadPoolExecutor

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
    """Write the per-unit observation as a two-column key/value TSV read BY COLUMN NAME by relr1_verdict.py."""
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
    """max relative difference over whitespace-separated numeric fields; non-numeric fields must match."""
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
        d = abs(fx - fy) / max(abs(fx), abs(fy), 1e-300)
        m = max(m, d)
    return "%.3e" % m

TIMEOUT_S = 3600
JOBS = 4
EXCLUDED_MPI = ("examples/MPI_example/mpi_simple.lua", "examples/MPI_example/binary_grating_mpi.lua")


def eid_of(rel):
    s = rel[len("examples/"):].replace("/", "__")
    return s[:-4] if s.endswith(".lua") else s


def run_unit(rel, tree, pas):
    uv = UNITS
    tdir = os.path.join(TREES, tree)
    exe = os.path.join(tdir, "build", "S4")
    script = os.path.join(tdir, rel)
    eid = eid_of(rel)
    unit_id = "T3_%s_%s_p%s" % (eid, tree, pas)
    cwd = os.path.join(EV, "run", tree, pas, eid)
    if os.path.isfile(os.path.join(cwd, "unit.json")):
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
            if base in ("out.stdout", "out.stderr", "unit.json"):
                continue
            files.append(base + ":" + sha_f(full))
    status = "TIMEOUT" if timed_out == "YES" else ("RAN_OK" if rc == 0 else "RAN_FAIL")
    rec = {"unit_id": unit_id, "suite": "T3_examples", "tree": tree, "pass": pas, "status": status,
           "rc": rc, "signal": signal, "timed_out": timed_out,
           "stdout_sha256": sha_f(outp), "stderr_sha256": sha_f(errp),
           "stdout_path": os.path.relpath(outp, REPO), "stderr_path": os.path.relpath(errp, REPO),
           "reference_path": "", "numdiff_rc": "", "numdiff_relmax": "", "dur_s": dur,
           "extra": "files=" + (";".join(files) if files else "none")}
    open(os.path.join(cwd, "unit.json"), "w", encoding="utf-8").write(
        NL.join(["unit_id=" + unit_id, "example=" + rel, "tree=" + tree, "pass=" + pas,
                 "rc=" + str(rc), "signal=" + signal, "timed_out=" + timed_out, "dur_s=" + dur,
                 "stdout_sha256=" + rec["stdout_sha256"], "stderr_sha256=" + rec["stderr_sha256"],
                 "utc=" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")]) + NL)
    write_unit(rec)
    print("UNIT %-70s rc=%s signal=%s dur=%ss" % (unit_id, rc, signal, dur))
    return 0


def read_prereg():
    rows = []
    hdr = None
    for line in open(os.path.join(EV, "PREREG_RELR1.tsv"), encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if hdr is None:
            hdr = f
            continue
        rows.append(dict(zip(hdr, f)))
    return rows


def matrix(tree):
    cmds = []
    for r in read_prereg():
        if r["suite"] != "T3_examples" or r["expect_B"] == "SKIP_DECLARED":
            continue
        parts = r["unit_id"].rsplit("_", 2)
        if len(parts) != 3 or parts[1] != tree:
            continue
        cmds.append(r["command"].split())
    cmds.sort(key=lambda c: c[-1] + ":" + c[-3])  # pass then example, deterministic order
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
        print("usage: relr1_examples.py run-unit --example REL --tree T --pass P | matrix --tree T")
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
