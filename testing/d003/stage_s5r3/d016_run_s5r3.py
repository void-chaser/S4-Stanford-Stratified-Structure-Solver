#!/usr/bin/env python3
# d016_run_s5r3.py -- P05-S5 R3 D016 public-API runs with comparator v2. New file (s5r3, U372).
# The comparator reads every expectation from PREREG_D016_S5R3.tsv BY COLUMN NAME.  A stderr row is
# compared as "pre-registered ABSENT <=> observed count == 0": the pre-registration carries an explicit
# numeric expected_count=0 (no label-vs-number comparison anywhere, no per-row string special case).
# modes:
#   calib                     one injection-free pass for the M1 shakedown-check (not a formal result)
#   shakedown                 one pass, duplicated as pass1/pass2 for the comparator flow (SHAKEDOWN_DUP)
#   formal --pass 1|2         one formal pass, observations written to D016_PASS<N>_S5R3.json
#   judge                     read both formal passes, write D016_VERDICT_S5R3.tsv (SUMMARY line)
#   posctrl --seed-pass1 P --seed-pass2 Q --out OUT
#                             five tampered on-disk copies judged by the same code path (>= 5/5 required)
import os, sys, json, math, subprocess, hashlib, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r3")
SHK = os.path.join(EV, "shakedown")
TREE = os.path.join(EV, "trees/F4")
STAGE = os.path.join(REPO, "testing/d003/stage_s5r3")
PY_SCRIPT = os.path.join(STAGE, "d016_py_s5r3.py")
LUA_SCRIPT = os.path.join(STAGE, "d016_lua_s5r3.lua")
PREREG = os.path.join(EV, "PREREG_D016_S5R3.tsv")
BUILD = os.path.join(EV, "D016_BUILD_S5R3.tsv")
TAB = chr(9)
NL = chr(10)
TAGS = ["VL_NB%d%s" % (n, s) for n in (1, 2, 3, 4) for s in ("", "_RETRY")] + \
       ["VL_NB5", "VL_NB9", "VL_NB9_RECOVER", "VL_NB9_REF", "Jones_NB1", "NV_NB1"]


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def read_tsv(p):
    rows = []
    hdr = None
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        rows.append(dict(zip(hdr, f)))
    return rows


def read_kv(p):
    d = {}
    hdr = None
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        d[f[0]] = f[1]
    return d


def run(cmd, stdin_text=None):
    p = subprocess.run(cmd, input=stdin_text, capture_output=True, text=True, cwd=REPO, timeout=600)
    return {"rc": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def pyext():
    out = subprocess.check_output(["python3-config", "--extension-suffix"], text=True).strip()
    return os.path.join(TREE, "S4" + out)


def parse_lua(stdout):
    pts = {}
    for line in stdout.splitlines():
        f = line.split(TAB)
        if not f or not f[0].startswith("POINT "):
            continue
        parts = f[0].split()
        tag = parts[1]
        kind = parts[2]
        if kind == "FAIL_VISIBLE":
            pts[tag] = {"status": "FAIL_VISIBLE"}
        elif kind == "VALUES" and len(f) >= 5:
            vals = [float(x) for x in f[1:5]]
            pts[tag] = {"status": "VALUES", "values": vals, "all_finite": all(math.isfinite(x) for x in vals)}
    return pts


def py_points(js):
    return {p["tag"]: p for p in (js or {}).get("points", [])}


def one_pass(tag, logdir):
    os.makedirs(logdir, exist_ok=True)
    py = pyext()
    lua = os.path.join(TREE, "build/S4")
    if not os.path.isfile(py):
        raise SystemExit("MISSING pyext " + py)
    if not os.path.isfile(lua):
        raise SystemExit("MISSING lua " + lua)
    o = {"pass": tag, "utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    for mode in ("main", "ref"):
        out = os.path.join(logdir, "py_%s_%s.json" % (mode, tag))
        r = run(["python3", "-I", "-B", PY_SCRIPT, "--tree", TREE, "--mode", mode, "--out", out])
        open(os.path.join(logdir, "py_%s_%s.stdout.txt" % (mode, tag)), "w").write(r["stdout"])
        open(os.path.join(logdir, "py_%s_%s.stderr.txt" % (mode, tag)), "w").write(r["stderr"])
        js = json.load(open(out)) if os.path.isfile(out) else None
        o["py_run_" + mode] = {"rc": r["rc"], "stdout": r["stdout"], "stderr": r["stderr"], "json": js}
        if mode == "main":
            o["py"] = py_points(js)
        else:
            o["py_ref"] = py_points(js)
    lua_text = open(LUA_SCRIPT).read()
    for mode in ("main", "ref"):
        r = run([lua, "-a", mode], stdin_text=lua_text)
        open(os.path.join(logdir, "lua_%s_%s.stdout.txt" % (mode, tag)), "w").write(r["stdout"])
        open(os.path.join(logdir, "lua_%s_%s.stderr.txt" % (mode, tag)), "w").write(r["stderr"])
        pts = parse_lua(r["stdout"])
        if mode == "main":
            o["lua"] = pts
            o["lua_main_proc"] = {"rc": r["rc"], "stderr": r["stderr"], "stdout": r["stdout"]}
        else:
            o["lua_ref"] = pts
            o["lua_ref_proc"] = {"rc": r["rc"], "stderr": r["stderr"], "stdout": r["stdout"]}
    o["py_main_proc"] = {"rc": o["py_run_main"]["rc"], "stderr": o["py_run_main"]["stderr"], "stdout": o["py_run_main"]["stdout"]}
    o["py_ref_proc"] = {"rc": o["py_run_ref"]["rc"], "stderr": o["py_run_ref"]["stderr"], "stdout": o["py_run_ref"]["stdout"]}
    o["artifacts"] = {"PYEXT_SHA256": sha_f(py), "LUA_SHA256": sha_f(lua),
                      "LIBS4A_SHA256": sha_f(os.path.join(TREE, "build/libS4.a")) if os.path.isfile(os.path.join(TREE, "build/libS4.a")) else "MISSING"}
    return o


def relerr(a, b):
    m = 0.0
    for x, y in zip(a, b):
        d = abs(x) if y == 0.0 else abs(x - y) / abs(y)
        m = max(m, d)
    return m


def obs_semantic(o, fe, pid):
    src = o["py_ref"] if pid.endswith("_REF") else o["py"]
    if fe == "py":
        p = src.get(pid)
        if p is None:
            return {"status": "MISSING", "text": "MISSING"}
        if p.get("status") == "EXCEPTION":
            return {"status": "EXCEPTION", "exc_type": p.get("exc_type"), "text": p.get("message")}
        return {"status": "RETURNED", "values": p.get("values"), "all_finite": p.get("all_finite")}
    src = o["lua_ref"] if pid.endswith("_REF") else o["lua"]
    p = src.get(pid)
    if p is None:
        return {"status": "MISSING", "text": "MISSING"}
    if p.get("status") == "FAIL_VISIBLE":
        return {"status": "FAIL_VISIBLE", "text": None}
    return {"status": "VALUES", "values": p.get("values"), "all_finite": p.get("all_finite")}


def proc_obs(o, pid):
    if pid == "PY_RC":
        return o["py_main_proc"]["rc"]
    if pid == "LUA_RC":
        return o["lua_main_proc"]["rc"]
    if pid == "PY_STDERR_INFO2":
        return o["py_main_proc"]["stderr"].count("Layer eigensystem returned info = 2")
    if pid == "LUA_STDERR_INFO2":
        return o["lua_main_proc"]["stderr"].count("Layer eigensystem returned info = 2")
    if pid == "LUA_STDERR_MSG_COUNT":
        return o["lua_main_proc"]["stderr"].count("GetPoyntingFlux: The layer eigensystem could not be solved; no solution was returned.")
    raise SystemExit("unknown process row " + pid)


def proc_expected(row):
    return ("count", int(row["expected_count"])) if row.get("expected_count", "").strip() != "" else ("rc", int(row["expected_rc"]))


def check_row(row, o):
    """Return (ok, observed_string, expected_string) -- all expectations read from the prereg row."""
    pid = row["point_id"]
    fe = row["frontend"]
    kind = row["kind"]
    if kind == "PROCESS":
        mode, ev = proc_expected(row)
        got = proc_obs(o, pid)
        return (int(got) == ev), ("count=%d" % got if mode == "count" else "rc=%d" % got), \
               ("count=%d" % ev if mode == "count" else "rc=%d" % ev)
    if kind == "ARTIFACT":
        bld = read_kv(BUILD) if os.path.isfile(BUILD) else {}
        key = {"PYEXT_SHA256": "PYEXT_SHA256", "LUA_SHA256": "LUA_FRONTEND_SHA256",
               "LIBS4A_SHA256": "LIB_S4_A_SHA256"}.get(pid, pid)
        want = bld.get(key, "MISSING")
        got = o["artifacts"].get(pid, "MISSING")
        return (got == want), got, want
    sem = obs_semantic(o, fe, pid)
    if kind in ("FAILURE", "RETRY_SAME_OBJECT"):
        if fe == "py":
            ok = (sem["status"] == "EXCEPTION" and sem.get("exc_type") == row["expected_exception"]
                  and sem.get("text") == row["expected_text"])
            return ok, "EXCEPTION %s %r" % (sem.get("exc_type"), sem.get("text")), \
                   "EXCEPTION %s %r" % (row["expected_exception"], row["expected_text"])
        ok = sem["status"] == "FAIL_VISIBLE" and row["expected_text"] in (o["lua_main_proc"]["stderr"] if not pid.endswith("_REF") else o["lua_ref_proc"]["stderr"])
        return ok, sem["status"], "FAIL_VISIBLE + text"
    # CONTROL / RECOVERY / REFERENCE
    want_status = "RETURNED" if fe == "py" else "VALUES"
    if sem["status"] != want_status or sem.get("all_finite") is not True:
        return False, "%s finite=%s" % (sem["status"], sem.get("all_finite")), want_status + " finite=YES"
    if kind == "RECOVERY":
        ref = obs_semantic(o, fe, "VL_NB9_REF" if fe == "py" else "VL_NB9_REF")
        e = relerr(sem["values"], ref["values"])
        thr = float(row["rel_err_threshold"])
        return (e <= thr), "rel_err=%.3e" % e, "rel_err<=%g vs VL_NB9_REF" % thr
    return True, sem["status"] + " finite=YES", want_status + " finite=YES"


JUDGED_KINDS = ("FAILURE", "RETRY_SAME_OBJECT", "CONTROL", "RECOVERY", "REFERENCE", "PROCESS", "ARTIFACT")


def judged_rows(prereg):
    rows = [r for r in prereg if r["kind"] in JUDGED_KINDS]
    order = {"FAILURE": 0, "RETRY_SAME_OBJECT": 1, "CONTROL": 2, "RECOVERY": 3, "REFERENCE": 4, "PROCESS": 5, "ARTIFACT": 6}
    rows.sort(key=lambda r: (order.get(r["kind"], 9), r["point_id"], r["frontend"]))
    return rows


def compare_passes(prereg, o1, o2):
    rows = []
    m = n = fl = 0
    for row in judged_rows(prereg):
        if row["kind"] == "ARTIFACT":
            continue  # artefacts are checked in the build table; not a behavioural verdict row
        ok1, ob1, exp = check_row(row, o1)
        ok2, ob2, _ = check_row(row, o2)
        det = ""
        if row["kind"] == "RECOVERY" and ok1 and ok2:
            fe = row["frontend"]
            det = "rel_err_pass1=%.3e rel_err_pass2=%.3e" % (
                relerr(obs_semantic(o1, fe, row["point_id"])["values"], obs_semantic(o1, fe, "VL_NB9_REF")["values"]),
                relerr(obs_semantic(o2, fe, row["point_id"])["values"], obs_semantic(o2, fe, "VL_NB9_REF")["values"]))
        if ob1 != ob2:
            verdict = "FLAKY"
        elif ok1 and ok2:
            verdict = "MATCH"
        else:
            verdict = "MISMATCH"
        if verdict == "MATCH":
            m += 1
        elif verdict == "FLAKY":
            fl += 1
        else:
            n += 1
        if row["kind"] == "PROCESS":
            rows.insert(0, (row["point_id"], row["frontend"], exp, ob1, ob2, det, verdict))
        else:
            rows.append((row["point_id"], row["frontend"], exp, ob1, ob2, det, verdict))
    rows.append(("ROOT_CAUSE_RC", "source", "20 (F4 S4.cpp:2435-2438)", "20", "20",
                 "[源码] ComputeLayerModes returns 20 when FMMGetEpsilon returns nonzero", "RECORD"))
    return rows, m, n, fl


def write_verdict(prereg, p1, p2, out, header_extra=""):
    o1 = json.load(open(p1))["observations"]
    o2 = json.load(open(p2))["observations"]
    rows, m, n, fl = compare_passes(prereg, o1, o2)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# D016_VERDICT_S5R3.tsv -- P05-S5 R3 D016 public-API verdict, F4 build, two passes" + NL)
        fh.write("# expectations pre-registered in PREREG_D016_S5R3.tsv (INFLUENCED); comparator v2 (U372)" + NL)
        if header_extra:
            fh.write("# " + header_extra + NL)
        fh.write(TAB.join(["point_id", "frontend", "expected", "observed_pass1", "observed_pass2", "detail", "verdict"]) + NL)
        for r in rows:
            fh.write(TAB.join(str(x) for x in r) + NL)
        fh.write("SUMMARY" + TAB + "MATCH=%d" % m + TAB + "MISMATCH=%d" % n + TAB + "FLAKY=%d" % fl + NL)
    print("VERDICT rows=%d MATCH=%d MISMATCH=%d FLAKY=%d" % (len(rows), m, n, fl))
    print("WROTE " + os.path.relpath(out, REPO))
    return m, n, fl


def save_pass(o, path, pn):
    json.dump({"pass": str(pn), "observations": o}, open(path, "w"), indent=1, default=str)


def mode_calib():
    logdir = os.path.join(SHK, "d016_calib")
    o = one_pass("calib", logdir)
    save_pass(o, os.path.join(logdir, "D016_PASS_SHAKEDOWN.json"), "calib")
    for k, v in (("PYEXT_SHA256", o["artifacts"]["PYEXT_SHA256"]), ("LUA_SHA256", o["artifacts"]["LUA_SHA256"])):
        print("ARTIFACT " + k + "=" + v)
    print("CALIB py_rc=%s lua_rc=%s" % (o["py_main_proc"]["rc"], o["lua_main_proc"]["rc"]))
    return 0


def mode_shakedown():
    logdir = os.path.join(SHK, "d016")
    os.makedirs(logdir, exist_ok=True)
    o = one_pass("shakedown", logdir)
    p1 = os.path.join(logdir, "pass1.json")
    p2 = os.path.join(logdir, "pass2.json")
    save_pass(o, p1, 1)
    save_pass(o, p2, 2)
    open(os.path.join(logdir, "SHAKEDOWN_DUP"), "w").write("pass2 is a byte-copy of pass1 (task brief section 6)" + NL)
    prereg = read_tsv(PREREG)
    m, n, fl = write_verdict(prereg, p1, p2, os.path.join(logdir, "D016_VERDICT_S5R3.tsv"),
                             "SHAKEDOWN_DUP: pass2 is a copy of pass1; this is a gate exercise, not a formal result")
    return 0 if n == 0 and fl == 0 else 1


def mode_formal(pn):
    logdir = os.path.join(EV, "logs")
    o = one_pass("pass" + pn, logdir)
    p = os.path.join(EV, "D016_PASS%s_S5R3.json" % pn)
    save_pass(o, p, pn)
    print("WROTE " + os.path.relpath(p, REPO))
    prereg = read_tsv(PREREG)
    bad = 0
    for row in judged_rows(prereg):
        ok, ob, exp = check_row(row, o)
        print("PASS%s %-22s %-4s %-9s %s" % (pn, row["point_id"], row["frontend"], row["kind"], "OK" if ok else "FAIL"))
        if not ok:
            bad += 1
    return 0 if bad == 0 else 1


def mode_judge():
    p1 = os.path.join(EV, "D016_PASS1_S5R3.json")
    p2 = os.path.join(EV, "D016_PASS2_S5R3.json")
    for p in (p1, p2):
        if not os.path.isfile(p):
            print("HARD_STOP missing " + p)
            return 2
    prereg = read_tsv(PREREG)
    m, n, fl = write_verdict(prereg, p1, p2, os.path.join(EV, "D016_VERDICT_S5R3.tsv"))
    return 0 if n == 0 and fl == 0 else 1


# ---------------------------------------------------------------- positive control
def load_obs(p):
    return json.load(open(p))["observations"]


def dump_case(case, o1, o2):
    d = os.path.join(EV, "posctrl/d016", case)
    os.makedirs(d, exist_ok=True)
    json.dump({"pass": "1", "observations": o1}, open(os.path.join(d, "pass1.json"), "w"), indent=1, default=str)
    json.dump({"pass": "2", "observations": o2}, open(os.path.join(d, "pass2.json"), "w"), indent=1, default=str)
    return d


def mode_posctrl(seed1, seed2, out):
    prereg = read_tsv(PREREG)
    base1 = load_obs(seed1)
    base2 = load_obs(seed2)
    cases = []
    # case 5 (untampered): the seed data as-is
    cases.append(("E_UNTAMPERED_ALL_MATCH", "MATCH", base1, base2))
    # case 1: stderr info-2 count 1 in BOTH passes -> MISMATCH on PY_STDERR_INFO2
    t1 = json.loads(json.dumps(base1))
    t1["py_main_proc"]["stderr"] = t1["py_main_proc"]["stderr"] + "Layer eigensystem returned info = 2" + NL
    t1b = json.loads(json.dumps(base2))
    t1b["py_main_proc"]["stderr"] = t1b["py_main_proc"]["stderr"] + "Layer eigensystem returned info = 2" + NL
    cases.append(("A_STDERR_COUNT_1", "MISMATCH", t1, t1b))
    # case 2: pass2 differs from pass1 on a behavioural point -> FLAKY
    t2 = json.loads(json.dumps(base2))
    t2["lua"]["VL_NB1"]["status"] = "VALUES"
    t2["lua"]["VL_NB1"]["values"] = [1.0, 0.0, 0.0, 0.0]
    t2["lua"]["VL_NB1"]["all_finite"] = True
    cases.append(("B_TWO_PASSES_DIFFER", "FLAKY", base1, t2))
    # case 3: recovery value moved by 2e-12 -> MISMATCH
    t3 = json.loads(json.dumps(base1))
    ref = t3["py_ref"]["VL_NB9_REF"]["values"]
    t3["py"]["VL_NB9_RECOVER"]["values"] = [x * (1.0 + 2e-12) for x in ref]
    cases.append(("C_RECOVER_RELERR_2E12", "MISMATCH", t3, json.loads(json.dumps(t3))))
    # case 4: a failure point returns finite values -> MISMATCH
    t4 = json.loads(json.dumps(base1))
    t4["py"]["VL_NB1"] = {"status": "RETURNED", "values": [1.0, 0.0, 0.0, 0.0], "all_finite": True}
    cases.append(("D_FAILURE_RETURNS_FINITE", "MISMATCH", t4, json.loads(json.dumps(t4))))
    results = []
    for name, want_row_verdict, o1, o2 in cases:
        d = dump_case(name, o1, o2)
        vp = os.path.join(d, "VERDICT.tsv")
        m, n, fl = write_verdict(prereg, os.path.join(d, "pass1.json"), os.path.join(d, "pass2.json"), vp)
        if name.startswith("E_"):
            got = "MATCH" if (n == 0 and fl == 0) else "NOT_ALL_MATCH"
        elif name.startswith("B_"):
            got = "FLAKY" if fl >= 1 else "NO_FLAKY"
        else:
            got = "MISMATCH" if n >= 1 else "NO_MISMATCH"
        results.append((name, want_row_verdict, got, got == want_row_verdict, m, n, fl))
    all_ok = all(r[3] for r in results)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# POSCTRL_D016_S5R3.txt -- positive control of the comparator v2 on tampered JSON copies written to disk" + NL)
        fh.write("# every case is a real file under " + os.path.relpath(os.path.join(EV, "posctrl/d016"), REPO) + "/<case>/pass{1,2}.json" + NL)
        fh.write("# judged by the same compare_passes()/write_verdict() code path as the formal verdict (no constant self-proof)" + NL)
        for name, want, got, ok, m, n, fl in results:
            fh.write("%s: %s (expected=%s actual=%s) MATCH=%d MISMATCH=%d FLAKY=%d" % (
                name, "PASS" if ok else "FAIL", want, got, m, n, fl) + NL)
        fh.write("OVERALL_POSITIVE_CONTROL: %s (%d/%d)" % ("PASS" if all_ok else "FAIL",
                                                           sum(1 for r in results if r[3]), len(results)) + NL)
    for name, want, got, ok, m, n, fl in results:
        print("%-26s want=%-9s got=%-14s %s" % (name, want, got, "PASS" if ok else "FAIL"))
    print("OVERALL %s %d/%d" % ("PASS" if all_ok else "FAIL", sum(1 for r in results if r[3]), len(results)))
    return 0 if all_ok else 1


def main():
    if len(sys.argv) < 2:
        print("usage: d016_run_s5r3.py calib|shakedown|judge|posctrl|formal --pass N")
        return 2
    sub = sys.argv[1]
    if sub == "calib":
        return mode_calib()
    if sub == "shakedown":
        return mode_shakedown()
    if sub == "judge":
        return mode_judge()
    if sub == "formal":
        if "--pass" not in sys.argv:
            print("formal needs --pass 1|2")
            return 2
        return mode_formal(sys.argv[sys.argv.index("--pass") + 1])
    if sub == "posctrl":
        a = sys.argv
        s1 = a[a.index("--seed-pass1") + 1]
        s2 = a[a.index("--seed-pass2") + 1]
        out = a[a.index("--out") + 1]
        return mode_posctrl(s1, s2, out)
    print("unknown mode " + sub)
    return 2


if __name__ == "__main__":
    sys.exit(main())