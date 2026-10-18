#!/usr/bin/env python3
# judge_e2e_s5r3.py -- classify E2E point records for the three frontends, and the positive control over
# tampered on-disk records. New file (s5r3).
# categories: E2E_OK, API_SILENT, RETRY_DIFF, RETRY_FAIL, INVALID, HIT_OFF_TARGET, FLAKY, CONTROL_OK, CONTROL_BAD
# visible criteria are concrete: Python = RuntimeError whose text contains "GetPowerFlux"; Lua = a stderr line
# starting with "GetPoyntingFlux: " (WITNESS/HIT lines never satisfy it).
# usage: judge_e2e_s5r3.py posctrl OUT.txt
#        judge_e2e_s5r3.py formal PASS1_DIR PASS2_DIR OUT.tsv
import os, sys, json, re, shutil

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r3")
PREREG = os.path.join(EV, "PREREG_E2E_S5R3.tsv")
POSCTRL = os.path.join(EV, "posctrl/e2e")
TAB = chr(9)
NL = chr(10)
TOL = 1e-12


def close(a, b):
    if a is None or b is None:
        return False
    if isinstance(a, (int, float)) or isinstance(b, (int, float)):
        a, b = [a], [b]
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x is None or y is None:
            return False
        if x == y:
            continue
        if abs(x - y) > TOL * max(1.0, abs(x), abs(y)):
            return False
    return True


def json_of(run):
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
            parts = line.split()[1:5]
            out = []
            for p in parts:
                out.append(None if p == "nil" else float(p))
            while len(out) < 4:
                out.append(None)
            return out
    return None


def hit_lines(run):
    return [ln for ln in (run.get("stderr") or "").splitlines() if "S4FMM HIT" in ln]


def has_lua_error(run):
    return any(ln.startswith("GetPoyntingFlux: ") for ln in (run.get("stderr") or "").splitlines())


def off_target(rec, inject_run):
    mode = rec.get("inject_mode")
    try:
        nth = int(rec.get("nth"))
    except Exception:
        nth = None
    calib = str(rec.get("calib_size", "NA"))
    hs = hit_lines(inject_run)
    if len(hs) != 1:
        return True
    line = hs[0]
    m = re.search(r"\(hit=(\d+)\)", line)
    e = re.search(r"\(exec call=(\d+)\)", line)
    seq = int(m.group(1)) if m else (int(e.group(1)) if e else None)
    if seq is None or nth is None or seq != nth:
        return True
    if mode in ("s4malloc", "plan"):
        m2 = re.search(r"(\d+) B \(hit=", line)
        if calib in ("", "NA"):
            return False
        if m2 is None or int(m2.group(1)) != int(calib):
            return True
    if mode == "exec":
        if not e:
            return True
    return False


def classify_py(rec):
    st = rec["steps"]
    ref = (json_of(st["ref"]) or {}).get("steps", {}).get("ref")
    inj = (json_of(st["inject"]) or {}).get("steps", {})
    r2 = (json_of(st["r2"]) or {}).get("steps", {}).get("fresh")
    a = inj.get("A_inject")
    b = inj.get("B_retry_same")
    c = inj.get("C_retry_fresh_obj")
    inj_run = st["inject"]
    if rec.get("is_control") == "YES":
        ok = (ref is not None and ref.get("ok") and r2 is not None and r2.get("ok")
              and a is not None and a.get("ok") and b is not None and b.get("ok") and c is not None and c.get("ok")
              and inj_run.get("rc") == 0 and len(hit_lines(inj_run)) == 0
              and close(ref.get("values"), b.get("values")) and close(ref.get("values"), c.get("values"))
              and close(ref.get("values"), r2.get("values")))
        return ("CONTROL_OK" if ok else "CONTROL_BAD"), {"rc": inj_run.get("rc"), "hits": len(hit_lines(inj_run))}
    if ref is None or not ref.get("ok"):
        return "INVALID", {"reason": "clean reference failed in its own process"}
    if len(hit_lines(inj_run)) < 1:
        return "INVALID", {"hits": 0}
    if off_target(rec, inj_run):
        return "HIT_OFF_TARGET", {"hit": hit_lines(inj_run)[:1], "nth": rec.get("nth"), "calib_size": rec.get("calib_size")}
    visible = (a is not None and a.get("ok") is False and a.get("error_type") == "RuntimeError"
               and "GetPowerFlux" in (a.get("error_msg") or ""))
    if not visible:
        return "API_SILENT", {"a": a}
    if b is None or b.get("ok") is False or c is None or c.get("ok") is False or r2 is None or r2.get("ok") is False:
        return "RETRY_FAIL", {"b": b is not None and b.get("ok"), "c": c is not None and c.get("ok"), "r2": r2 is not None and r2.get("ok")}
    if not (close(ref.get("values"), b.get("values")) and close(ref.get("values"), c.get("values"))
            and close(ref.get("values"), r2.get("values"))):
        return "RETRY_DIFF", {"ref": ref.get("values"), "b": b.get("values"), "c": c.get("values"), "r2": r2.get("values")}
    return "E2E_OK", {"error_type": a.get("error_type"), "hit": hit_lines(inj_run)[:1]}


def classify_lua_batch(rec):
    st = rec["steps"]
    ref = values_line(st["ref"].get("stdout"))
    r2 = values_line(st["r2"].get("stdout"))
    inj = st["inject"]
    if rec.get("is_control") == "YES":
        ok = (ref is not None and r2 is not None and close(ref, r2) and inj.get("rc") == 0
              and len(hit_lines(inj)) == 0 and close(ref, values_line(inj.get("stdout"))))
        return ("CONTROL_OK" if ok else "CONTROL_BAD"), {"rc": inj.get("rc"), "hits": len(hit_lines(inj))}
    if ref is None:
        return "INVALID", {"reason": "clean reference failed in its own process"}
    if len(hit_lines(inj)) < 1:
        return "INVALID", {"hits": 0}
    if off_target(rec, inj):
        return "HIT_OFF_TARGET", {"hit": hit_lines(inj)[:1], "nth": rec.get("nth"), "calib_size": rec.get("calib_size")}
    if not (has_lua_error(inj) and inj.get("rc") not in (0, None)):
        return "API_SILENT", {"rc": inj.get("rc"), "stderr": (inj.get("stderr") or "").splitlines()[:2]}
    # same-object retry is not applicable: the batch process exits on the reported error (U341)
    if r2 is None or st["r2"].get("rc") != 0:
        return "RETRY_FAIL", {"r2_rc": st["r2"].get("rc")}
    if not close(ref, r2):
        return "RETRY_DIFF", {"ref": ref, "r2": r2}
    return "E2E_OK", {"rc": inj.get("rc"), "error": [ln for ln in inj.get("stderr", "").splitlines() if ln.startswith("GetPoyntingFlux: ")][:1]}


def classify_lua_repl(rec):
    st = rec["steps"]
    refA = repl_values(st["ref"].get("stdout"), "A")
    inj = st["inject"]
    injA = repl_values(inj.get("stdout"), "A")
    injB = repl_values(inj.get("stdout"), "B")
    r2A = repl_values(st["r2"].get("stdout"), "A")
    if rec.get("is_control") == "YES":
        ok = (refA is not None and None not in refA and inj.get("rc") == 0 and len(hit_lines(inj)) == 0
              and injA is not None and None not in injA and close(refA, injA)
              and injB is not None and close(refA, injB) and r2A is not None and close(refA, r2A))
        return ("CONTROL_OK" if ok else "CONTROL_BAD"), {"rc": inj.get("rc"), "hits": len(hit_lines(inj))}
    if refA is None or None in refA:
        return "INVALID", {"reason": "clean reference failed in its own process"}
    if len(hit_lines(inj)) < 1:
        return "INVALID", {"hits": 0}
    if off_target(rec, inj):
        return "HIT_OFF_TARGET", {"hit": hit_lines(inj)[:1], "nth": rec.get("nth"), "calib_size": rec.get("calib_size")}
    if not has_lua_error(inj):
        return "API_SILENT", {"stderr": (inj.get("stderr") or "").splitlines()[:2]}
    if injA is not None and None not in injA:
        return "INVALID", {"reason": "the failed first solve still returned values"}
    if injB is None or None in injB:
        return "RETRY_FAIL", {"reason": "same-object retry did not return values"}
    if r2A is None or None in r2A or st["r2"].get("rc") != 0:
        return "RETRY_FAIL", {"r2_rc": st["r2"].get("rc")}
    if not close(refA, injB) or not close(refA, r2A):
        return "RETRY_DIFF", {"ref": refA, "retry_same": injB, "r2": r2A}
    return "E2E_OK", {"error": [ln for ln in inj.get("stderr", "").splitlines() if ln.startswith("GetPoyntingFlux: ")][:1]}


def classify(rec):
    fe = rec.get("frontend")
    if fe == "py":
        return classify_py(rec)
    if fe == "lua_batch":
        return classify_lua_batch(rec)
    if fe == "lua_repl":
        return classify_lua_repl(rec)
    raise SystemExit("unknown frontend " + str(fe))


def load_points(d):
    out = {}
    p = os.path.join(d, "points")
    if not os.path.isdir(p):
        return out
    for f in sorted(os.listdir(p)):
        if f.endswith(".json"):
            out[f[:-5]] = json.load(open(os.path.join(p, f), encoding="utf-8"))
    return out


def formal_verdict(d1, d2, out_tsv):
    p1 = load_points(d1)
    p2 = load_points(d2)
    ids = sorted(set(p1) | set(p2))
    rows = []
    counts = {}
    for pid in ids:
        if pid not in p1 or pid not in p2:
            rows.append((pid, "MISSING_RUN", "", "", "", "missing in pass1=%s pass2=%s" % (pid in p1, pid in p2)))
            counts["MISSING_RUN"] = counts.get("MISSING_RUN", 0) + 1
            continue
        c1, d1i = classify(p1[pid])
        c2, d2i = classify(p2[pid])
        verdict = c1 if c1 == c2 else "FLAKY"
        counts[verdict] = counts.get(verdict, 0) + 1
        rows.append((pid, p1[pid].get("frontend", ""), c1, c2, verdict,
                     json.dumps(d1i, ensure_ascii=False)[:300] + " | " + json.dumps(d2i, ensure_ascii=False)[:300]))
    with open(out_tsv, "w", encoding="utf-8") as fh:
        fh.write("# E2E_VERDICT_S5R3.tsv -- per-point E2E verdict over the two formal passes (S-D)" + NL)
        fh.write(TAB.join(["point_id", "frontend", "pass1", "pass2", "verdict", "detail"]) + NL)
        for r in rows:
            fh.write(TAB.join(str(x) for x in r) + NL)
    for r in rows:
        print(TAB.join(str(x) for x in r[:5]))
    print("COUNTS " + json.dumps(counts, sort_keys=True))
    print("WROTE " + out_tsv)
    return counts, rows


# ---------------------------------------------------------------- positive control
def runrec(rc, stdout="", stderr=""):
    hl = [ln for ln in stderr.splitlines() if "S4FMM HIT" in ln]
    return {"rc": rc, "stdout": stdout, "stderr": stderr, "n_hits": len(hl), "hit_lines": hl, "timed_out": False}


REF = [0.27034542159003894, 0.0, 0.0, 0.0]
HIT_S4M = "S4FMM HIT real S4_malloc failure: FMM call 192 B (hit=3)\n"
HIT_PLAN = "S4FMM HIT real malloc failure: plan preparation 5192 B (hit=1)\n"
HIT_EXEC = "S4FMM HIT exec boundary simulation (exec call=1)\n"
LUA_ERR = "GetPoyntingFlux: The layer eigensystem could not be solved; no solution was returned.\n"
WITNESS = "S4FMM WITNESS plan call=1 grid=16x16\n"


def py_step(ok, vals=None, et=None, msg=None):
    return {"ok": ok, "values": vals, "error_type": et, "error_msg": msg}


def mk_py(kind, mode="s4malloc", nth="3", calib="192", control="NO"):
    hit = HIT_S4M if mode == "s4malloc" else (HIT_PLAN if mode == "plan" else HIT_EXEC)
    err = py_step(False, None, "RuntimeError", "GetPowerFlux: An unknown error occurred.")
    ok = py_step(True, REF)
    inj_steps = {"A_inject": err, "B_retry_same": ok, "C_retry_fresh_obj": ok}
    inj = runrec(0, json.dumps({"steps": inj_steps}), hit)
    rec = {"point_id": "syn", "frontend": "py", "spec": "fft", "inject_mode": mode, "nth": nth,
           "calib_size": calib, "is_control": control,
           "steps": {"ref": runrec(0, json.dumps({"steps": {"ref": ok}}), ""),
                     "inject": inj,
                     "r2": runrec(0, json.dumps({"steps": {"fresh": ok}}), "")}}
    if kind == "E2E_OK":
        pass
    elif kind == "API_SILENT":
        rec["steps"]["inject"] = runrec(0, json.dumps({"steps": {"A_inject": ok, "B_retry_same": ok, "C_retry_fresh_obj": ok}}), hit)
    elif kind == "RETRY_DIFF":
        bad = [0.99, 0.0, 0.0, 0.0]
        rec["steps"]["inject"] = runrec(0, json.dumps({"steps": {"A_inject": err, "B_retry_same": py_step(True, bad), "C_retry_fresh_obj": ok}}), hit)
    elif kind == "RETRY_FAIL":
        rec["steps"]["inject"] = runrec(0, json.dumps({"steps": {"A_inject": err, "B_retry_same": err, "C_retry_fresh_obj": ok}}), hit)
    elif kind == "INVALID":
        rec["steps"]["inject"] = runrec(0, json.dumps({"steps": {"A_inject": ok, "B_retry_same": ok, "C_retry_fresh_obj": ok}}), "")
    elif kind == "HIT_OFF_TARGET":
        off = "S4FMM HIT real S4_malloc failure: FMM call 24576 B (hit=1)\n"
        rec["steps"]["inject"] = runrec(0, json.dumps({"steps": {"A_inject": err, "B_retry_same": ok, "C_retry_fresh_obj": ok}}), off)
    elif kind == "CONTROL_OK":
        rec["is_control"] = "YES"
        rec["inject_mode"] = "none"
        rec["nth"] = "0"
        rec["calib_size"] = "NA"
        a = py_step(True, REF)
        rec["steps"]["inject"] = runrec(0, json.dumps({"steps": {"A_inject": a, "B_retry_same": a, "C_retry_fresh_obj": a}}), "")
    elif kind == "CONTROL_BAD":
        rec["is_control"] = "YES"
        rec["inject_mode"] = "none"
        rec["nth"] = "0"
        rec["calib_size"] = "NA"
        rec["steps"]["inject"] = runrec(1, "", "boom\n")
    return rec


def mk_lua_batch(kind):
    ref = runrec(0, "VALUES 0.27034542159003894 0 0 0\nBATCH_DONE\n", WITNESS)
    rec = {"point_id": "syn", "frontend": "lua_batch", "spec": "fft", "inject_mode": "s4malloc", "nth": "3",
           "calib_size": "192", "is_control": "NO",
           "steps": {"ref": ref,
                     "inject": runrec(1, "PHASE batch spec=fft\n", WITNESS + HIT_S4M + LUA_ERR),
                     "r2": runrec(0, "VALUES 0.27034542159003894 0 0 0\nBATCH_DONE\n", WITNESS)}}
    if kind == "E2E_OK":
        pass
    elif kind == "API_SILENT":
        rec["steps"]["inject"] = runrec(0, "VALUES 0.27034542159003894 0 0 0\nBATCH_DONE\n", WITNESS + HIT_S4M)
    elif kind == "RETRY_FAIL":
        rec["steps"]["r2"] = runrec(1, "", LUA_ERR)
    elif kind == "INVALID":
        rec["steps"]["inject"] = runrec(0, "VALUES 0.27034542159003894 0 0 0\nBATCH_DONE\n", WITNESS)
    elif kind == "HIT_OFF_TARGET":
        rec["steps"]["inject"] = runrec(1, "PHASE batch spec=fft\n", WITNESS + "S4FMM HIT real S4_malloc failure: FMM call 24576 B (hit=1)\n" + LUA_ERR)
    elif kind == "CONTROL_OK":
        rec["is_control"] = "YES"
        rec["inject_mode"] = "none"
        rec["nth"] = "0"
        rec["calib_size"] = "NA"
        rec["steps"]["inject"] = runrec(0, "VALUES 0.27034542159003894 0 0 0\nBATCH_DONE\n", WITNESS)
    return rec


def mk_lua_repl(kind):
    refout = "A 0.27034542159004 0.0 0.0 0.0\nB 0.27034542159004 0.0 0.0 0.0\nREPL_DONE\n"
    injout = "A nil nil nil nil\nB 0.27034542159004 0.0 0.0 0.0\nREPL_DONE\n"
    rec = {"point_id": "syn", "frontend": "lua_repl", "spec": "fft", "inject_mode": "s4malloc", "nth": "3",
           "calib_size": "192", "is_control": "NO",
           "steps": {"ref": runrec(0, refout, WITNESS),
                     "inject": runrec(0, injout, WITNESS + HIT_S4M + LUA_ERR),
                     "r2": runrec(0, refout, WITNESS)}}
    if kind == "E2E_OK":
        pass
    elif kind == "RETRY_DIFF":
        rec["steps"]["inject"] = runrec(0, "A nil nil nil nil\nB 0.99 0.0 0.0 0.0\nREPL_DONE\n", WITNESS + HIT_S4M + LUA_ERR)
    elif kind == "INVALID":
        rec["steps"]["inject"] = runrec(0, refout, WITNESS)
    elif kind == "CONTROL_OK":
        rec["is_control"] = "YES"
        rec["inject_mode"] = "none"
        rec["nth"] = "0"
        rec["calib_size"] = "NA"
        rec["steps"]["inject"] = runrec(0, refout, WITNESS)
    return rec


def write_case(name, rec1, rec2=None):
    d1 = os.path.join(POSCTRL, name, "pass1")
    os.makedirs(os.path.join(d1, "points"), exist_ok=True)
    json.dump(rec1, open(os.path.join(d1, "points", rec1["point_id"] + ".json"), "w", encoding="utf-8"), indent=1)
    if rec2 is None:
        rec2 = rec1
    d2 = os.path.join(POSCTRL, name, "pass2")
    os.makedirs(os.path.join(d2, "points"), exist_ok=True)
    json.dump(rec2, open(os.path.join(d2, "points", rec2["point_id"] + ".json"), "w", encoding="utf-8"), indent=1)
    return d1, d2


def mode_posctrl(out_txt):
    cases = [
        ("py_E2E_OK", "E2E_OK", mk_py("E2E_OK")),
        ("py_API_SILENT", "API_SILENT", mk_py("API_SILENT")),
        ("py_RETRY_DIFF", "RETRY_DIFF", mk_py("RETRY_DIFF")),
        ("py_RETRY_FAIL", "RETRY_FAIL", mk_py("RETRY_FAIL")),
        ("py_INVALID", "INVALID", mk_py("INVALID")),
        ("py_HIT_OFF_TARGET", "HIT_OFF_TARGET", mk_py("HIT_OFF_TARGET")),
        ("py_CONTROL_OK", "CONTROL_OK", mk_py("CONTROL_OK")),
        ("py_CONTROL_BAD", "CONTROL_BAD", mk_py("CONTROL_BAD")),
        ("lua_batch_E2E_OK", "E2E_OK", mk_lua_batch("E2E_OK")),
        ("lua_batch_API_SILENT", "API_SILENT", mk_lua_batch("API_SILENT")),
        ("lua_batch_RETRY_FAIL", "RETRY_FAIL", mk_lua_batch("RETRY_FAIL")),
        ("lua_batch_INVALID", "INVALID", mk_lua_batch("INVALID")),
        ("lua_batch_HIT_OFF_TARGET", "HIT_OFF_TARGET", mk_lua_batch("HIT_OFF_TARGET")),
        ("lua_batch_CONTROL_OK", "CONTROL_OK", mk_lua_batch("CONTROL_OK")),
        ("lua_repl_E2E_OK", "E2E_OK", mk_lua_repl("E2E_OK")),
        ("lua_repl_RETRY_DIFF", "RETRY_DIFF", mk_lua_repl("RETRY_DIFF")),
        ("lua_repl_INVALID", "INVALID", mk_lua_repl("INVALID")),
        ("lua_repl_CONTROL_OK", "CONTROL_OK", mk_lua_repl("CONTROL_OK")),
    ]
    results = []
    for name, want, rec in cases:
        d1, d2 = write_case(name, rec)
        out = os.path.join(POSCTRL, name, "VERDICT.tsv")
        counts, rows = formal_verdict(d1, d2, out)
        got = rows[0][4] if rows else "NO_ROWS"
        results.append((name, want, got, got == want))
    # FLAKY needs two different on-disk runs
    d1, d2 = write_case("py_FLAKY", mk_py("E2E_OK"), mk_py("RETRY_DIFF"))
    out = os.path.join(POSCTRL, "py_FLAKY", "VERDICT.tsv")
    counts, rows = formal_verdict(d1, d2, out)
    got = rows[0][4] if rows else "NO_ROWS"
    results.append(("py_FLAKY", "FLAKY", got, got == "FLAKY"))
    all_ok = all(r[3] for r in results)
    with open(out_txt, "w", encoding="utf-8") as fh:
        fh.write("# POSCTRL_E2E_S5R3.txt -- positive control of judge_e2e_s5r3.py on tampered records written to disk" + NL)
        fh.write("# every case is a real file under " + os.path.relpath(POSCTRL, REPO) + "/<case>/pass{1,2}/points/; the verdict is" + NL)
        fh.write("# recomputed by the same formal code path from the file content (no constant self-proof)." + NL)
        for name, want, got, ok in results:
            fh.write("%s: %s (expected=%s actual=%s)" % (name, "PASS" if ok else "FAIL", want, got) + NL)
        fh.write("OVERALL_POSITIVE_CONTROL: %s (%d/%d)" % ("PASS" if all_ok else "FAIL",
                                                           sum(1 for r in results if r[3]), len(results)) + NL)
        fh.write("CATEGORIES_COVERED: " + ",".join(sorted(set(r[1] for r in results))) + NL)
        fh.write("FRONTENDS_COVERED: py,lua_batch,lua_repl" + NL)
    for name, want, got, ok in results:
        print("%-24s want=%-15s got=%-15s %s" % (name, want, got, "PASS" if ok else "FAIL"))
    print("OVERALL %s %d/%d" % ("PASS" if all_ok else "FAIL", sum(1 for r in results if r[3]), len(results)))
    return 0 if all_ok else 1


def mode_shakedown(pass1_dir):
    # task brief section 6: one shakedown pass is duplicated as pass1/pass2 for the comparator flow,
    # marked SHAKEDOWN_DUP; this is a gate exercise, not a formal result.
    pass2_dir = os.path.join(os.path.dirname(pass1_dir.rstrip("/")), "pass2")
    if os.path.realpath(pass2_dir) != os.path.realpath(pass1_dir):
        os.makedirs(os.path.join(pass2_dir, "points"), exist_ok=True)
        for f in sorted(os.listdir(os.path.join(pass1_dir, "points"))):
            if f.endswith(".json"):
                shutil.copyfile(os.path.join(pass1_dir, "points", f), os.path.join(pass2_dir, "points", f))
        open(os.path.join(pass2_dir, "SHAKEDOWN_DUP"), "w").write(
            "pass2 is a byte-copy of pass1 (task brief section 6)" + NL)
    out = os.path.join(os.path.dirname(pass1_dir.rstrip("/")), "E2E_VERDICT_S5R3.tsv")
    counts, rows = formal_verdict(pass1_dir, pass2_dir, out)
    print("SHAKEDOWN_DUP verdict written: " + os.path.relpath(out, REPO))
    return 0 if not [r for r in rows if r[4] in ("FLAKY",)] else 1


def main():
    if len(sys.argv) < 2:
        print("usage: judge_e2e_s5r3.py posctrl OUT.txt | formal PASS1_DIR PASS2_DIR OUT.tsv | shakedown PASS1_DIR", file=sys.stderr)
        return 2
    mode = sys.argv[1]
    if mode == "posctrl":
        out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(EV, "POSCTRL_E2E_S5R3.txt")
        return mode_posctrl(out)
    if mode == "formal":
        counts, rows = formal_verdict(sys.argv[2], sys.argv[3], sys.argv[4])
        bad = [r for r in rows if r[4] in ("API_SILENT", "RETRY_DIFF", "RETRY_FAIL", "FLAKY", "INVALID", "HIT_OFF_TARGET", "MISSING_RUN")]
        print("BAD_OR_JUDGEABLE=%d" % len(bad))
        return 0
    if mode == "shakedown":
        return mode_shakedown(sys.argv[2])
    print("unknown mode", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
