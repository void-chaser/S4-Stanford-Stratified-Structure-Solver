#!/usr/bin/env python3
# rejudge_s5r4.py -- independent re-judgement of the S5R3 E2E and D016 recorded verdicts, S5R4 (U379).
#
# It does NOT import judge_e2e_s5r3.py, d016_run_s5r3.py or any other judge/comparator script. It reads
# the S5R3 pre-registration tables and the per-point JSON observations (read only; no injection is re-run)
# and re-derives every verdict from the pre-registered semantics, then compares with the recorded tables.
#
# Rule mapping (pre-registration semantics -> implementation):
#   E2E, 42 points = 25 injected + 17 injection-free controls (column is_control)
#     * injected point: the injection must hit (a "S4FMM HIT" stderr line whose hit=/exec call= sequence
#       equals nth and, for s4malloc/plan, whose size equals calib_size), the clean reference in its own
#       process must have succeeded, the failure must be visible (Python: RuntimeError whose text contains
#       "GetPowerFlux"; Lua: a stderr line starting with "GetPoyntingFlux: "), and both retries (same
#       object B, fresh object C, plus the separate fresh process r2) must succeed and equal the reference
#       values element-wise at rel<=1e-12. Result: E2E_OK; otherwise the most specific category
#       (INVALID / HIT_OFF_TARGET / API_SILENT / RETRY_FAIL / RETRY_DIFF).
#     * control point: reference, injected run, B, C and r2 must all succeed, return the same values and
#       show no hit. Result: CONTROL_OK / CONTROL_BAD.
#     * both passes are classified separately; equal verdicts -> that verdict, different -> FLAKY, a pass
#       without a point record -> MISSING_RUN. Every point is compared with the recorded verdict.
#   D016, 36 pre-registered rows: 3 ARTIFACT rows are build-table rows, not behaviour rows, and are not
#     re-judged (they appear only as a comment line). The remaining 33 behaviour rows are re-judged:
#     PROCESS rows compare the observed rc / stderr occurrence count with expected_rc or expected_count;
#     FAILURE/RETRY_SAME_OBJECT rows require the pre-registered failure (exception type+text for Python,
#     the pre-registered text in the Lua stderr for Lua); CONTROL/REFERENCE rows require returned finite
#     values; RECOVERY rows require returned finite values whose max relative difference against the
#     VL_NB9_REF row is <= rel_err_threshold. Two passes: equal observed evidence -> MATCH when both pass
#     checks hold, MISMATCH otherwise; different observed evidence -> FLAKY. ROOT_CAUSE_RC is a
#     [源码] RECORD row that is not in the pre-registration: it is written as NOT_JUDGED_SOURCE_RECORD,
#     never silently dropped. The recorded D016 table has 34 rows (33 behaviour + ROOT_CAUSE_RC).
#
# TSV reading: '#' comment lines, the header row and rows whose first field is SUMMARY are skipped and
# all values are read BY COLUMN NAME (the S5R3 crash was the SUMMARY row being read as a data row).
#
# usage: rejudge_s5r4.py formal [--ev3-root DIR] [--out PATH]
#   --ev3-root  directory holding the S5R3 evidence inputs (default checkpoints/p05/evidence/p05-s5r3)
#   --out       output TSV (default checkpoints/p05/evidence/p05-s5r4/REJUDGE_S5R4.tsv)
import os, sys, re, json, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV4 = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r4")
EV3 = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r3")
TAB = chr(9)
NL = chr(10)
TOL = 1e-12


def read_table(path, skip_first=("SUMMARY",)):
    """Read a TSV by column name. Skips blank lines, '#' comments, the header line (also when the file
    repeats it) and rows whose first field is in skip_first (e.g. SUMMARY)."""
    rows = []
    hdr = None
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        if f[0] == hdr[0]:
            continue
        if f[0] in skip_first:
            continue
        rows.append(dict(zip(hdr, f + [""] * (len(hdr) - len(f)))))
    return rows


def read_kv(path):
    d = {}
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if len(f) >= 2:
            d[f[0]] = f[1]
    return d


def close(a, b):
    if a is None or b is None or len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x is None or y is None:
            return False
        if x == y:
            continue
        if abs(x - y) > TOL * max(1.0, abs(x), abs(y)):
            return False
    return True


def json_line(run):
    for line in reversed((run.get("stdout") or "").strip().splitlines()):
        try:
            return json.loads(line)
        except Exception:
            continue
    return None


def values_line(stdout):
    for line in (stdout or "").splitlines():
        if line.startswith("VALUES "):
            try:
                return [float(x) for x in line.split()[1:5]]
            except ValueError:
                return None
    return None


def repl_values(stdout, key):
    for line in (stdout or "").splitlines():
        if line.startswith(key + " "):
            out = [None if p == "nil" else float(p) for p in line.split()[1:5]]
            while len(out) < 4:
                out.append(None)
            return out
    return None


def hits(run):
    return [ln for ln in (run.get("stderr") or "").splitlines() if "S4FMM HIT" in ln]


def lua_error(run):
    return any(ln.startswith("GetPoyntingFlux: ") for ln in (run.get("stderr") or "").splitlines())


def on_target(pr, run):
    """True iff the single hit line matches the pre-registered nth / calib_size."""
    hs = hits(run)
    if len(hs) != 1:
        return False
    line = hs[0]
    m = re.search(r"\(hit=(\d+)\)", line)
    e = re.search(r"\(exec call=(\d+)\)", line)
    seq = int(m.group(1)) if m else (int(e.group(1)) if e else None)
    if seq is None or str(seq) != str(pr.get("nth", "")).strip():
        return False
    mode = pr.get("inject_mode")
    calib = str(pr.get("calib_size", "NA")).strip()
    if mode in ("s4malloc", "plan"):
        m2 = re.search(r"(\d+) B \(hit=", line)
        if calib in ("", "NA"):
            return True
        return m2 is not None and int(m2.group(1)) == int(calib)
    return True


def classify_e2e(pr, rec):
    fe = pr["frontend"]
    ctl = pr.get("is_control") == "YES"
    st = rec["steps"]
    if fe == "py":
        ref = (json_line(st["ref"]) or {}).get("steps", {}).get("ref")
        inj = (json_line(st["inject"]) or {}).get("steps", {})
        r2 = (json_line(st["r2"]) or {}).get("steps", {}).get("fresh")
        a, b, c = inj.get("A_inject"), inj.get("B_retry_same"), inj.get("C_retry_fresh_obj")
        if ctl:
            ok = (ref is not None and ref.get("ok") and r2 is not None and r2.get("ok")
                  and a is not None and a.get("ok") and b is not None and b.get("ok")
                  and c is not None and c.get("ok") and st["inject"].get("rc") == 0
                  and not hits(st["inject"])
                  and close(ref.get("values"), b.get("values"))
                  and close(ref.get("values"), c.get("values"))
                  and close(ref.get("values"), r2.get("values")))
            return "CONTROL_OK" if ok else "CONTROL_BAD"
        if ref is None or not ref.get("ok"):
            return "INVALID"
        if not hits(st["inject"]):
            return "INVALID"
        if not on_target(pr, st["inject"]):
            return "HIT_OFF_TARGET"
        if not (a is not None and a.get("ok") is False and a.get("error_type") == "RuntimeError"
                and "GetPowerFlux" in (a.get("error_msg") or "")):
            return "API_SILENT"
        if b is None or b.get("ok") is False or c is None or c.get("ok") is False or r2 is None or r2.get("ok") is False:
            return "RETRY_FAIL"
        if not (close(ref.get("values"), b.get("values")) and close(ref.get("values"), c.get("values"))
                and close(ref.get("values"), r2.get("values"))):
            return "RETRY_DIFF"
        return "E2E_OK"
    if fe == "lua_batch":
        ref = values_line(st["ref"].get("stdout"))
        r2 = values_line(st["r2"].get("stdout"))
        inj = st["inject"]
        if ctl:
            ok = (ref is not None and r2 is not None and close(ref, r2) and inj.get("rc") == 0
                  and not hits(inj) and close(ref, values_line(inj.get("stdout"))))
            return "CONTROL_OK" if ok else "CONTROL_BAD"
        if ref is None:
            return "INVALID"
        if not hits(inj):
            return "INVALID"
        if not on_target(pr, inj):
            return "HIT_OFF_TARGET"
        if not (lua_error(inj) and inj.get("rc") not in (0, None)):
            return "API_SILENT"
        if r2 is None or st["r2"].get("rc") != 0:
            return "RETRY_FAIL"
        if not close(ref, r2):
            return "RETRY_DIFF"
        return "E2E_OK"
    if fe == "lua_repl":
        refA = repl_values(st["ref"].get("stdout"), "A")
        inj = st["inject"]
        injA = repl_values(inj.get("stdout"), "A")
        injB = repl_values(inj.get("stdout"), "B")
        r2A = repl_values(st["r2"].get("stdout"), "A")
        if ctl:
            ok = (refA is not None and None not in refA and inj.get("rc") == 0 and not hits(inj)
                  and injA is not None and None not in injA and close(refA, injA)
                  and injB is not None and None not in injB and close(refA, injB)
                  and r2A is not None and None not in r2A and close(refA, r2A))
            return "CONTROL_OK" if ok else "CONTROL_BAD"
        if refA is None or None in refA:
            return "INVALID"
        if not hits(inj):
            return "INVALID"
        if not on_target(pr, inj):
            return "HIT_OFF_TARGET"
        if not lua_error(inj):
            return "API_SILENT"
        if injA is not None and None not in injA:
            return "INVALID"
        if injB is None or None in injB:
            return "RETRY_FAIL"
        if r2A is None or None in r2A or st["r2"].get("rc") != 0:
            return "RETRY_FAIL"
        if not close(refA, injB) or not close(refA, r2A):
            return "RETRY_DIFF"
        return "E2E_OK"
    raise SystemExit("unknown frontend " + str(fe))


def load_points(root, passno):
    d = os.path.join(root, "e2e/pass%d/points" % passno)
    out = {}
    if not os.path.isdir(d):
        return out
    for f in sorted(os.listdir(d)):
        if f.endswith(".json"):
            out[f[:-5]] = json.load(open(os.path.join(d, f), encoding="utf-8"))
    return out


def rejudge_e2e(root):
    prereg = {r["point_id"]: r for r in read_table(os.path.join(root, "PREREG_E2E_S5R3.tsv"))}
    p1, p2 = load_points(root, 1), load_points(root, 2)
    recorded = {r["point_id"]: r["verdict"] for r in read_table(os.path.join(root, "E2E_VERDICT_S5R3.tsv"))}
    rows = []
    diffs = 0
    for pid in sorted(set(prereg) | set(p1) | set(p2) | set(recorded)):
        if pid not in prereg:
            mine, note = "NO_PREREG", "point has no pre-registration row"
        elif pid not in p1 or pid not in p2:
            mine, note = "MISSING_RUN", "missing in pass1=%s pass2=%s" % (pid in p1, pid in p2)
        else:
            c1, c2 = classify_e2e(prereg[pid], p1[pid]), classify_e2e(prereg[pid], p2[pid])
            mine = c1 if c1 == c2 else "FLAKY"
            note = "pass1=%s pass2=%s" % (c1, c2)
        rec = recorded.get(pid, "ABSENT_IN_VERDICT")
        same = (mine == rec)
        if not same:
            diffs += 1
        rows.append(("E2E", pid, rec, mine, "SAME" if same else "DIFF", note))
    return rows, diffs


def d016_sem(o, fe, pid):
    src = o["py_ref"] if pid.endswith("_REF") else o["py"]
    if fe == "py":
        p = src.get(pid)
        if p is None:
            return {"status": "MISSING"}
        if p.get("status") == "EXCEPTION":
            return {"status": "EXCEPTION", "exc_type": p.get("exc_type"), "text": p.get("message")}
        return {"status": "RETURNED", "values": p.get("values"), "all_finite": p.get("all_finite")}
    src = o["lua_ref"] if pid.endswith("_REF") else o["lua"]
    p = src.get(pid)
    if p is None:
        return {"status": "MISSING"}
    if p.get("status") == "FAIL_VISIBLE":
        return {"status": "FAIL_VISIBLE", "text": None}
    return {"status": "VALUES", "values": p.get("values"), "all_finite": p.get("all_finite")}


def relerr(a, b):
    m = 0.0
    for x, y in zip(a, b):
        m = max(m, abs(x) if y == 0.0 else abs(x - y) / abs(y))
    return m


def d016_check(pr, o):
    """Return (ok, observed_key). observed_key is what the recorded table shows as observed evidence."""
    pid, fe, kind = pr["point_id"], pr["frontend"], pr["kind"]
    if kind == "PROCESS":
        main = o["py_main_proc"] if pid.startswith("PY_") else o["lua_main_proc"]
        if pr.get("expected_count", "").strip() != "":
            if pid == "PY_STDERR_INFO2" or pid == "LUA_STDERR_INFO2":
                got = main["stderr"].count("Layer eigensystem returned info = 2")
            elif pid == "LUA_STDERR_MSG_COUNT":
                got = main["stderr"].count("GetPoyntingFlux: The layer eigensystem could not be solved; no solution was returned.")
            else:
                got = None
            return (got is not None and got == int(pr["expected_count"])), "count=%s" % got
        got = main["rc"]
        return (got == int(pr["expected_rc"])), "rc=%d" % got
    sem = d016_sem(o, fe, pid)
    if kind in ("FAILURE", "RETRY_SAME_OBJECT"):
        if fe == "py":
            ok = (sem["status"] == "EXCEPTION" and sem.get("exc_type") == pr["expected_exception"]
                  and sem.get("text") == pr["expected_text"])
            return ok, "EXCEPTION %s %r" % (sem.get("exc_type"), sem.get("text"))
        main = o["lua_ref_proc"] if pid.endswith("_REF") else o["lua_main_proc"]
        ok = (sem["status"] == "FAIL_VISIBLE" and pr["expected_text"] in main["stderr"])
        return ok, "FAIL_VISIBLE"
    want = "RETURNED" if fe == "py" else "VALUES"
    if sem["status"] != want or sem.get("all_finite") is not True:
        return False, "%s finite=%s" % (sem["status"], sem.get("all_finite"))
    if kind == "RECOVERY":
        ref = d016_sem(o, fe, "VL_NB9_REF")
        if not sem.get("values") or not ref.get("values"):
            return False, "MISSING_VALUES"
        e = relerr(sem["values"], ref["values"])
        return (e <= float(pr["rel_err_threshold"])), "rel_err=%.3e" % e
    return True, "%s finite=YES" % want


def rejudge_d016(root):
    prereg = read_table(os.path.join(root, "PREREG_D016_S5R3.tsv"))
    o1 = json.load(open(os.path.join(root, "D016_PASS1_S5R3.json")))["observations"]
    o2 = json.load(open(os.path.join(root, "D016_PASS2_S5R3.json")))["observations"]
    build = read_kv(os.path.join(root, "D016_BUILD_S5R3.tsv"))
    recorded = {}
    for r in read_table(os.path.join(root, "D016_VERDICT_S5R3.tsv")):
        recorded[(r["point_id"], r["frontend"])] = r["verdict"]
    rows = []
    diffs = 0
    n_rejudged = 0
    n_artifact = 0
    not_judged = 0
    order = {"FAILURE": 0, "RETRY_SAME_OBJECT": 1, "CONTROL": 2, "RECOVERY": 3, "REFERENCE": 4, "PROCESS": 5}
    for pr in sorted([r for r in prereg if r["kind"] != "ARTIFACT"],
                     key=lambda r: (order.get(r["kind"], 9), r["point_id"], r["frontend"])):
        n_rejudged += 1
        ok1, k1 = d016_check(pr, o1)
        ok2, k2 = d016_check(pr, o2)
        if k1 != k2:
            mine = "FLAKY"
        elif ok1 and ok2:
            mine = "MATCH"
        else:
            mine = "MISMATCH"
        rec = recorded.get((pr["point_id"], pr["frontend"]), "ABSENT_IN_VERDICT")
        same = (mine == rec)
        if not same:
            diffs += 1
        rows.append(("D016", pr["point_id"] + "/" + pr["frontend"], rec, mine,
                     "SAME" if same else "DIFF", "%s obs1=%s obs2=%s" % (pr["kind"], k1, k2)))
    for pr in prereg:
        if pr["kind"] == "ARTIFACT":
            n_artifact += 1
    # ROOT_CAUSE_RC is a [源码] record, explicitly NOT judged from pre-registered behaviour
    rec = recorded.get(("ROOT_CAUSE_RC", "source"), "ABSENT_IN_VERDICT")
    rows.append(("D016", "ROOT_CAUSE_RC", rec, "NOT_JUDGED_SOURCE_RECORD", "NA",
                 "[源码] S4.cpp:2435-2438 ComputeLayerModes returns 20; row is a RECORD, not a behaviour judgement"))
    not_judged += 1
    other = sorted(set(recorded) - {("ROOT_CAUSE_RC", "source")} -
                   {(r["point_id"], r["frontend"]) for r in prereg})
    if other:
        for (pid, fe) in other:
            rows.append(("D016", pid + "/" + fe, recorded[(pid, fe)], "ABSENT_IN_PREREG", "DIFF", "recorded row not pre-registered"))
            diffs += 1
    extra = {"artifact_rows": n_artifact, "build_keys": len(build)}
    return rows, diffs, n_rejudged, not_judged, extra


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] != "formal":
        print("usage: rejudge_s5r4.py formal [--ev3-root DIR] [--out PATH]", file=sys.stderr)
        return 2
    root = EV3
    outp = os.path.join(EV4, "REJUDGE_S5R4.tsv")
    if "--ev3-root" in argv:
        root = os.path.abspath(argv[argv.index("--ev3-root") + 1])
    if "--out" in argv:
        outp = os.path.abspath(argv[argv.index("--out") + 1])
    e_rows, e_diffs = rejudge_e2e(root)
    d_rows, d_diffs, d_judged, d_not, extra = rejudge_d016(root)
    lines = ["# REJUDGE_S5R4.tsv -- independent re-judgement v2 of the S5R3 E2E and D016 recorded verdicts (U379)",
             "# reimplemented from the pre-registration semantics only: no import of judge_e2e_s5r3.py / d016_run_s5r3.py;",
             "# inputs are the S5R3 pre-registration tables and per-point JSON records (read only, no injection re-run).",
             "# reading skips '#' comments, the header row and first-field=SUMMARY rows; values are read by column name.",
             "# D016: 36 prereg rows = 33 behaviour rows re-judged + 3 ARTIFACT rows (build table, not behaviour).",
             "# D016_ARTIFACT_ROWS=%d BUILD_KEYS=%d" % (extra["artifact_rows"], extra["build_keys"]),
             TAB.join(["scope", "point", "recorded_verdict", "rejudged_verdict", "match", "note"])]
    lines += [TAB.join(r) for r in e_rows + d_rows]
    lines.append(TAB.join(["SUMMARY", "E2E_ROWS=%d" % len(e_rows), "E2E_INJECTED=%d" % len([r for r in e_rows if r[2] in ("E2E_OK", "API_SILENT", "RETRY_FAIL", "RETRY_DIFF", "INVALID", "HIT_OFF_TARGET")]), "E2E_DIFFS=%d" % e_diffs]))
    lines.append(TAB.join(["SUMMARY", "D016_RECORDED_ROWS=%d" % (d_judged + d_not), "D016_REJUDGED_ROWS=%d" % d_judged,
                           "D016_NOT_JUDGED=%d" % d_not, "D016_DIFFS=%d" % d_diffs, "DIFFS=%d" % (e_diffs + d_diffs)]))
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    with open(outp, "w", encoding="utf-8") as fh:
        fh.write(NL.join(lines) + NL)
    print("E2E_ROWS=%d E2E_DIFFS=%d D016_REJUDGED=%d D016_NOT_JUDGED=%d D016_DIFFS=%d DIFFS=%d" %
          (len(e_rows), e_diffs, d_judged, d_not, d_diffs, e_diffs + d_diffs))
    for r in e_rows + d_rows:
        if r[4] == "DIFF":
            print("DIFF " + TAB.join(r))
    print("WROTE " + os.path.relpath(outp, REPO))
    return 0 if e_diffs + d_diffs == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
