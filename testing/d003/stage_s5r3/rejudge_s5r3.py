#!/usr/bin/env python3
# rejudge_s5r3.py -- independent re-judgement of the S5R3 E2E and D016 verdicts (task brief section 5).
# It reads the pre-registration AND the per-point JSON records (merged before judging), re-implements the
# category/verdict rules from scratch (it does not import judge_e2e_s5r3.py or d016_run_s5r3.py) and
# compares its verdicts with the two recorded verdict tables. REJUDGE_DIFFS must be 0.
import os, sys, json, re, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r3")
TAB = chr(9)
NL = chr(10)
TOL = 1e-12


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


def eqvals(a, b):
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


def get_json_line(run):
    for line in reversed((run.get("stdout") or "").strip().splitlines()):
        try:
            return json.loads(line)
        except Exception:
            continue
    return None


def lua_values(stdout, key=None):
    for line in (stdout or "").splitlines():
        if key is not None:
            if not line.startswith(key + " "):
                continue
            vals = [None if p == "nil" else float(p) for p in line.split()[1:5]]
            while len(vals) < 4:
                vals.append(None)
            return vals
        if line.startswith("VALUES "):
            return [float(x) for x in line.split()[1:5]]
    return None


def hits(run):
    return [ln for ln in (run.get("stderr") or "").splitlines() if "S4FMM HIT" in ln]


def classify_e2e(pr, rec):
    """pr = merged pre-registration row; rec = on-disk per-point record."""
    fe = pr["frontend"]
    st = rec["steps"]
    ctl = pr.get("is_control") == "YES"
    if fe == "py":
        ref = (get_json_line(st["ref"]) or {}).get("steps", {}).get("ref")
        inj = (get_json_line(st["inject"]) or {}).get("steps", {})
        r2 = (get_json_line(st["r2"]) or {}).get("steps", {}).get("fresh")
        if ctl:
            ok = (ref is not None and ref.get("ok") and r2 is not None and r2.get("ok")
                  and st["inject"].get("rc") == 0 and not hits(st["inject"])
                  and all(inj.get(k) is not None and inj[k].get("ok") for k in ("A_inject", "B_retry_same", "C_retry_fresh_obj"))
                  and eqvals(ref.get("values"), inj["B_retry_same"].get("values"))
                  and eqvals(ref.get("values"), inj["C_retry_fresh_obj"].get("values"))
                  and eqvals(ref.get("values"), r2.get("values")))
            return "CONTROL_OK" if ok else "CONTROL_BAD"
        if ref is None or not ref.get("ok"):
            return "INVALID"
        if not hits(st["inject"]):
            return "INVALID"
        if not off_target(pr, st["inject"]):
            return "HIT_OFF_TARGET"
        a = inj.get("A_inject")
        if not (a is not None and a.get("ok") is False and a.get("error_type") == "RuntimeError"
                and "GetPowerFlux" in (a.get("error_msg") or "")):
            return "API_SILENT"
        b = inj.get("B_retry_same")
        c = inj.get("C_retry_fresh_obj")
        if b is None or b.get("ok") is False or c is None or c.get("ok") is False or r2 is None or r2.get("ok") is False:
            return "RETRY_FAIL"
        if not (eqvals(ref.get("values"), b.get("values")) and eqvals(ref.get("values"), c.get("values"))
                and eqvals(ref.get("values"), r2.get("values"))):
            return "RETRY_DIFF"
        return "E2E_OK"
    if fe == "lua_batch":
        ref = lua_values(st["ref"].get("stdout"))
        r2 = lua_values(st["r2"].get("stdout"))
        inj = st["inject"]
        if ctl:
            ok = (ref is not None and r2 is not None and eqvals(ref, r2) and inj.get("rc") == 0
                  and not hits(inj) and eqvals(ref, lua_values(inj.get("stdout"))))
            return "CONTROL_OK" if ok else "CONTROL_BAD"
        if ref is None:
            return "INVALID"
        if not hits(inj):
            return "INVALID"
        if not off_target(pr, inj):
            return "HIT_OFF_TARGET"
        vis = any(ln.startswith("GetPoyntingFlux: ") for ln in (inj.get("stderr") or "").splitlines())
        if not (vis and inj.get("rc") not in (0, None)):
            return "API_SILENT"
        if pr.get("exp_retry_same") == "NOT_APPLICABLE_PROCESS_EXIT":
            pass  # batch mode exits on the reported error; only the fresh process is observed
        if r2 is None or st["r2"].get("rc") != 0:
            return "RETRY_FAIL"
        if not eqvals(ref, r2):
            return "RETRY_DIFF"
        return "E2E_OK"
    # lua_repl
    refA = lua_values(st["ref"].get("stdout"), "A")
    injA = lua_values(st["inject"].get("stdout"), "A")
    injB = lua_values(st["inject"].get("stdout"), "B")
    r2A = lua_values(st["r2"].get("stdout"), "A")
    if ctl:
        ok = (refA is not None and None not in refA and st["inject"].get("rc") == 0 and not hits(st["inject"])
              and injA is not None and None not in injA and eqvals(refA, injA)
              and eqvals(refA, injB) and eqvals(refA, r2A))
        return "CONTROL_OK" if ok else "CONTROL_BAD"
    if refA is None or None in refA:
        return "INVALID"
    if not hits(st["inject"]):
        return "INVALID"
    if not off_target(pr, st["inject"]):
        return "HIT_OFF_TARGET"
    if not any(ln.startswith("GetPoyntingFlux: ") for ln in (st["inject"].get("stderr") or "").splitlines()):
        return "API_SILENT"
    if injA is not None and None not in injA:
        return "INVALID"
    if injB is None or None in injB:
        return "RETRY_FAIL"
    if r2A is None or None in r2A or st["r2"].get("rc") != 0:
        return "RETRY_FAIL"
    if not eqvals(refA, injB) or not eqvals(refA, r2A):
        return "RETRY_DIFF"
    return "E2E_OK"


def off_target(pr, run):
    hs = hits(run)
    if len(hs) != 1:
        return False
    line = hs[0]
    m = re.search(r"\(hit=(\d+)\)", line)
    e = re.search(r"\(exec call=(\d+)\)", line)
    seq = int(m.group(1)) if m else (int(e.group(1)) if e else None)
    try:
        nth = int(pr["nth"])
    except Exception:
        nth = None
    if seq is None or nth is None or seq != nth:
        return False
    mode = pr.get("inject_mode")
    calib = str(pr.get("calib_size", "NA"))
    if mode in ("s4malloc", "plan"):
        m2 = re.search(r"(\d+) B \(hit=", line)
        if calib in ("", "NA"):
            return True
        return m2 is not None and int(m2.group(1)) == int(calib)
    if mode == "exec":
        return e is not None
    return True


def rejudge_e2e():
    prereg = {r["point_id"]: r for r in read_tsv(os.path.join(EV, "PREREG_E2E_S5R3.tsv"))}
    rec1 = {}
    rec2 = {}
    for passno, d in (("1", os.path.join(EV, "e2e/pass1/points")), ("2", os.path.join(EV, "e2e/pass2/points"))):
        for f in sorted(os.listdir(d)):
            if f.endswith(".json"):
                rec = json.load(open(os.path.join(d, f)))
                (rec1 if passno == "1" else rec2)[rec["point_id"]] = rec
    verdict = {}
    for r in read_tsv(os.path.join(EV, "E2E_VERDICT_S5R3.tsv")):
        verdict[r["point_id"]] = r["verdict"]
    rows = []
    diffs = 0
    for pid in sorted(set(prereg) | set(rec1) | set(rec2)):
        if pid not in rec1 or pid not in rec2:
            mine = "MISSING_RUN"
        else:
            c1 = classify_e2e(prereg[pid], rec1[pid])
            c2 = classify_e2e(prereg[pid], rec2[pid])
            mine = c1 if c1 == c2 else "FLAKY"
        rec = verdict.get(pid, "ABSENT_IN_VERDICT")
        same = mine == rec
        if not same:
            diffs += 1
        rows.append(("E2E", pid, rec, mine, "SAME" if same else "DIFF"))
    return rows, diffs


def d016_semantics(obs, pid, fe, ref_pid=None):
    if fe == "py":
        src = obs["py_ref"] if pid.endswith("_REF") else obs["py"]
        p = src.get(pid)
        return p or {"status": "MISSING"}
    src = obs["lua_ref"] if pid.endswith("_REF") else obs["lua"]
    return src.get(pid) or {"status": "MISSING"}


def d016_row_ok(pr, obs):
    pid = pr["point_id"]
    fe = pr["frontend"]
    kind = pr["kind"]
    if kind == "PROCESS":
        cnt = pr.get("expected_count", "").strip()
        if pid == "PY_RC":
            return obs["py_main_proc"]["rc"] == int(pr["expected_rc"])
        if pid == "LUA_RC":
            return obs["lua_main_proc"]["rc"] == int(pr["expected_rc"])
        if pid == "PY_STDERR_INFO2":
            return obs["py_main_proc"]["stderr"].count("Layer eigensystem returned info = 2") == int(cnt)
        if pid == "LUA_STDERR_INFO2":
            return obs["lua_main_proc"]["stderr"].count("Layer eigensystem returned info = 2") == int(cnt)
        if pid == "LUA_STDERR_MSG_COUNT":
            return obs["lua_main_proc"]["stderr"].count("GetPoyntingFlux: The layer eigensystem could not be solved; no solution was returned.") == int(cnt)
        return False
    if kind == "ARTIFACT":
        b = {}
        for line in open(os.path.join(EV, "D016_BUILD_S5R3.tsv"), encoding="utf-8"):
            if line.startswith("#") or not line.strip():
                continue
            f = line.rstrip("\n").split(TAB)
            if len(f) >= 2:
                b[f[0]] = f[1]
        key = {"PYEXT_SHA256": "PYEXT_SHA256", "LUA_SHA256": "LUA_FRONTEND_SHA256",
               "LIBS4A_SHA256": "LIB_S4_A_SHA256"}.get(pid, pid)
        return obs["artifacts"].get(pid) == b.get(key)
    sem = d016_semantics(obs, pid, fe)
    if kind in ("FAILURE", "RETRY_SAME_OBJECT"):
        if fe == "py":
            return sem.get("status") == "EXCEPTION" and sem.get("exc_type") == pr["expected_exception"] and sem.get("message") == pr["expected_text"]
        stderr = obs["lua_main_proc"]["stderr"] if not pid.endswith("_REF") else obs["lua_ref_proc"]["stderr"]
        return sem.get("status") == "FAIL_VISIBLE" and pr["expected_text"] in stderr
    want = "RETURNED" if fe == "py" else "VALUES"
    if sem.get("status") != want or sem.get("all_finite") is not True:
        return False
    if kind == "RECOVERY":
        ref = d016_semantics(obs, "VL_NB9_REF", fe)
        vals = sem.get("values")
        rvals = ref.get("values")
        if not vals or not rvals:
            return False
        e = max((abs(x) if y == 0.0 else abs(x - y) / abs(y)) for x, y in zip(vals, rvals))
        return e <= float(pr["rel_err_threshold"])
    return True


def rejudge_d016():
    prereg = read_tsv(os.path.join(EV, "PREREG_D016_S5R3.tsv"))
    o1 = json.load(open(os.path.join(EV, "D016_PASS1_S5R3.json")))["observations"]
    o2 = json.load(open(os.path.join(EV, "D016_PASS2_S5R3.json")))["observations"]
    verdict = {}
    for r in read_tsv(os.path.join(EV, "D016_VERDICT_S5R3.tsv")):
        verdict[r["point_id"] + "/" + r["frontend"]] = r["verdict"]
    judged = [r for r in prereg if r["kind"] in ("FAILURE", "RETRY_SAME_OBJECT", "CONTROL", "RECOVERY", "REFERENCE", "PROCESS", "ARTIFACT")]
    rows = []
    diffs = 0
    for pr in judged:
        if pr["kind"] == "ARTIFACT":
            continue
        key = pr["point_id"] + "/" + pr["frontend"]
        ok1 = d016_row_ok(pr, o1)
        ok2 = d016_row_ok(pr, o2)
        s1 = d016_semantics(o1, pr["point_id"], pr["frontend"])
        s2 = d016_semantics(o2, pr["point_id"], pr["frontend"])
        if pr["kind"] == "PROCESS":
            v1 = "PROC"
            v2 = "PROC"
        else:
            v1 = json.dumps({k: s1.get(k) for k in ("status", "all_finite")}, sort_keys=True)
            if pr["kind"] == "RECOVERY":
                ref1 = d016_semantics(o1, "VL_NB9_REF", pr["frontend"])
                ref2 = d016_semantics(o2, "VL_NB9_REF", pr["frontend"])
                v1 += "/" + str(max(abs(x - y) / (abs(y) if y else 1.0) for x, y in zip(s1.get("values") or [0], ref1.get("values") or [0]))) if s1.get("values") else ""
                v2 += "/" + str(max(abs(x - y) / (abs(y) if y else 1.0) for x, y in zip(s2.get("values") or [0], ref2.get("values") or [0]))) if s2.get("values") else ""
        if pr["kind"] == "PROCESS":
            same_p = (o1 == o2)
        else:
            same_p = (v1 == v2)
        if not same_p:
            mine = "FLAKY"
        elif ok1 and ok2:
            mine = "MATCH"
        else:
            mine = "MISMATCH"
        rec = verdict.get(key, "ABSENT_IN_VERDICT")
        same = mine == rec
        if not same:
            diffs += 1
        rows.append(("D016", key, rec, mine, "SAME" if same else "DIFF"))
    return rows, diffs


def main():
    out = ["# REJUDGE_S5R3.tsv -- independent re-judgement of E2E and D016 verdicts (task brief section 5)",
           "# reimplementation: no import of judge_e2e_s5r3.py / d016_run_s5r3.py; prereg rows merged with the per-point JSON",
           TAB.join(["scope", "point", "recorded_verdict", "rejudged_verdict", "match"])]
    rows_e, de = rejudge_e2e()
    rows_d, dd = rejudge_d016()
    out += [TAB.join(r) for r in rows_e + rows_d]
    out.append("SUMMARY" + TAB + "E2E_ROWS=%d" % len(rows_e) + TAB + "D016_ROWS=%d" % len(rows_d))
    out.append("SUMMARY" + TAB + "E2E_DIFFS=%d" % de + TAB + "D016_DIFFS=%d" % dd + TAB + "DIFFS=%d" % (de + dd))
    open(os.path.join(EV, "REJUDGE_S5R3.tsv"), "w", encoding="utf-8").write(NL.join(out) + NL)
    print("REJUDGE E2E_ROWS=%d E2E_DIFFS=%d D016_ROWS=%d D016_DIFFS=%d DIFFS=%d" % (len(rows_e), de, len(rows_d), dd, de + dd))
    for r in rows_e + rows_d:
        if r[4] == "DIFF":
            print("DIFF " + TAB.join(r))
    print("WROTE " + os.path.relpath(os.path.join(EV, "REJUDGE_S5R3.tsv"), REPO))
    return 0 if de + dd == 0 else 1


if __name__ == "__main__":
    sys.exit(main())