#!/usr/bin/env python3
# judge_e2e_r9m3a.py -- classify E2E point records; and a positive control over synthetic records.
# categories: E2E_OK, API_SILENT, RETRY_DIFF, RETRY_FAIL, INVALID, FLAKY, CONTROL_OK
# usage: judge_e2e_r9m3a.py posctrl OUT.txt | formal RUN1.json [RUN2.json] OUT.tsv
import os, sys, json

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3a")
TAB = chr(9)
NL = chr(10)
TOL = 1e-12


def parse_values(text):
    for line in (text or "").splitlines():
        if line.startswith("VALUES"):
            parts = line.split()[1:]
            try:
                return [float(x) for x in parts]
            except ValueError:
                return None
    return None


def close(a, b):
    if a is None or b is None:
        return False
    if len(a) != len(b):
        return False
    for x, y in zip(a, b):
        if x == y:
            continue
        if abs(x - y) > TOL * max(1.0, abs(x), abs(y)):
            return False
    return True


def py_step(run, name):
    try:
        data = json.loads(run["stdout"].strip().splitlines()[-1])
    except Exception:
        return None
    return data.get("steps", {}).get(name)


def classify_py(rec):
    run = rec["steps"]["run"]
    ref = py_step(run, "1_clean_ref")
    inj = py_step(run, "2_inject")
    same = py_step(run, "3_retry_same")
    fresh = py_step(run, "4_retry_fresh")
    control = rec.get("is_control", "NO") == "YES"
    hits = run["n_hits"]
    if control:
        ok = (hits == 0 and run["rc"] == 0 and ref and ref.get("ok") and same and fresh and close(ref["values"], same["values"]) and close(ref["values"], fresh["values"]))
        return "CONTROL_OK" if ok else "CONTROL_BAD", {"hits": hits, "rc": run["rc"]}
    if hits < 1:
        return "INVALID", {"hits": hits}
    visible = (inj is not None) and (inj.get("ok") is False)
    if not visible:
        return "API_SILENT", {"hits": hits, "inj": inj}
    if same is None or fresh is None or same.get("ok") is False or fresh.get("ok") is False:
        return "RETRY_FAIL", {"hits": hits}
    if close(ref["values"], same["values"]) and close(ref["values"], fresh["values"]):
        return "E2E_OK", {"hits": hits, "err": inj.get("error_type")}
    return "RETRY_DIFF", {"hits": hits}


def classify_lua(rec):
    clean = rec["steps"]["clean"]
    fresh = rec["steps"]["fresh"]
    ref = parse_values(clean["stdout"])
    fv = parse_values(fresh["stdout"])
    control = rec.get("is_control", "NO") == "YES"
    if control:
        ok = (clean["rc"] == 0 and clean["n_hits"] == 0 and fresh["rc"] == 0 and close(ref, fv))
        return "CONTROL_OK" if ok else "CONTROL_BAD", {"rc": clean["rc"], "hits": clean["n_hits"]}
    inj = rec["steps"].get("inject")
    if inj is None:
        return "INVALID", {"hits": 0}
    if inj["n_hits"] < 1:
        return "INVALID", {"hits": inj["n_hits"]}
    visible = (inj["rc"] != 0) and ("Error" in inj["stderr"] or "error" in inj["stderr"] or len(inj["stderr"].strip()) > 0)
    if not visible:
        return "API_SILENT", {"hits": inj["n_hits"], "rc": inj["rc"]}
    if fresh["rc"] != 0 or not close(ref, fv):
        return "RETRY_FAIL" if fresh["rc"] != 0 else "RETRY_DIFF", {"hits": inj["n_hits"]}
    return "E2E_OK", {"hits": inj["n_hits"], "stderr_head": inj["stderr"].strip().splitlines()[:1]}


def classify(rec):
    if rec["frontend"] == "py":
        return classify_py(rec)
    return classify_lua(rec)


def synthetic(frontend, kind):
    if frontend == "py":
        if kind == "E2E_OK":
            step = lambda ok, vals=None, et=None: {"ok": ok, "values": vals, "error_type": et, "error_msg": "x"}
            run = {"rc": 0, "stdout": json.dumps({"steps": {"1_clean_ref": step(True, [1.0, 0.0]), "2_inject": step(False, None, "RuntimeError"), "3_retry_same": step(True, [1.0, 0.0]), "4_retry_fresh": step(True, [1.0, 0.0])}}), "stderr": "S4FMM HIT x", "hits": ["S4FMM HIT x"], "n_hits": 1}
            return {"point_id": "syn_" + kind, "frontend": "py", "spec": "fft", "is_control": "NO", "steps": {"run": run}}
        if kind == "API_SILENT":
            step = lambda ok, vals=None, et=None: {"ok": ok, "values": vals, "error_type": et, "error_msg": ""}
            run = {"rc": 0, "stdout": json.dumps({"steps": {"1_clean_ref": step(True, [1.0, 0.0]), "2_inject": step(True, [1.0, 0.0]), "3_retry_same": step(True, [1.0, 0.0]), "4_retry_fresh": step(True, [1.0, 0.0])}}), "stderr": "S4FMM HIT x", "hits": ["S4FMM HIT x"], "n_hits": 1}
            return {"point_id": "syn_" + kind, "frontend": "py", "spec": "fft", "is_control": "NO", "steps": {"run": run}}
        if kind == "RETRY_DIFF":
            step = lambda ok, vals=None, et=None: {"ok": ok, "values": vals, "error_type": et, "error_msg": "x"}
            run = {"rc": 0, "stdout": json.dumps({"steps": {"1_clean_ref": step(True, [1.0, 0.0]), "2_inject": step(False, None, "RuntimeError"), "3_retry_same": step(True, [2.0, 0.0]), "4_retry_fresh": step(True, [1.0, 0.0])}}), "stderr": "S4FMM HIT x", "hits": ["S4FMM HIT x"], "n_hits": 1}
            return {"point_id": "syn_" + kind, "frontend": "py", "spec": "fft", "is_control": "NO", "steps": {"run": run}}
        if kind == "RETRY_FAIL":
            step = lambda ok, vals=None, et=None: {"ok": ok, "values": vals, "error_type": et, "error_msg": "x"}
            run = {"rc": 0, "stdout": json.dumps({"steps": {"1_clean_ref": step(True, [1.0, 0.0]), "2_inject": step(False, None, "RuntimeError"), "3_retry_same": step(False, None, "RuntimeError"), "4_retry_fresh": step(True, [1.0, 0.0])}}), "stderr": "S4FMM HIT x", "hits": ["S4FMM HIT x"], "n_hits": 1}
            return {"point_id": "syn_" + kind, "frontend": "py", "spec": "fft", "is_control": "NO", "steps": {"run": run}}
        if kind == "INVALID":
            step = lambda ok, vals=None, et=None: {"ok": ok, "values": vals, "error_type": et, "error_msg": "x"}
            run = {"rc": 0, "stdout": json.dumps({"steps": {"1_clean_ref": step(True, [1.0, 0.0]), "2_inject": step(True, [1.0, 0.0]), "3_retry_same": step(True, [1.0, 0.0]), "4_retry_fresh": step(True, [1.0, 0.0])}}), "stderr": "", "hits": [], "n_hits": 0}
            return {"point_id": "syn_" + kind, "frontend": "py", "spec": "fft", "is_control": "NO", "steps": {"run": run}}
        if kind == "CONTROL_OK":
            step = lambda ok, vals=None, et=None: {"ok": ok, "values": vals, "error_type": et, "error_msg": ""}
            run = {"rc": 0, "stdout": json.dumps({"steps": {"1_clean_ref": step(True, [1.0, 0.0]), "2_inject": step(True, [1.0, 0.0]), "3_retry_same": step(True, [1.0, 0.0]), "4_retry_fresh": step(True, [1.0, 0.0])}}), "stderr": "", "hits": [], "n_hits": 0}
            return {"point_id": "syn_" + kind, "frontend": "py", "spec": "fft", "is_control": "YES", "steps": {"run": run}}
    return None


def mode_posctrl(out_txt):
    wants = ["E2E_OK", "API_SILENT", "RETRY_DIFF", "RETRY_FAIL", "INVALID", "CONTROL_OK"]
    results = []
    for w in wants:
        rec = synthetic("py", w)
        got, detail = classify(rec)
        results.append((w, got, got == w, detail))
    # FLAKY is decided across two runs of the same point, not from a single record
    runA = synthetic("py", "E2E_OK")
    runB = synthetic("py", "RETRY_DIFF")
    a, _ = classify(runA)
    b, _ = classify(runB)
    flaky = (a != b)
    results.append(("FLAKY", "FLAKY" if flaky else a, flaky, {"run1": a, "run2": b}))
    all_ok = all(r[2] for r in results)
    with open(out_txt, "w", encoding="utf-8") as fh:
        fh.write("# POSCTRL_E2E_R9M3A.txt -- positive control of judge_e2e_r9m3a.py on synthetic records (S-D5)" + NL)
        for want, got, ok, detail in results:
            fh.write("%s: %s (expected=%s actual=%s)" % (want, "PASS" if ok else "FAIL", want, got) + NL)
        fh.write("OVERALL_POSITIVE_CONTROL: %s (%d/%d)" % ("PASS" if all_ok else "FAIL", sum(1 for r in results if r[2]), len(results)) + NL)
    for want, got, ok, detail in results:
        print("%s -> %s PASS=%s" % (want, got, ok))
    print("OVERALL %s" % ("PASS" if all_ok else "FAIL"))
    return 0 if all_ok else 1


def mode_formal(paths, out_tsv):
    runs = []
    for p in paths:
        runs.append(json.load(open(p, encoding="utf-8")))
    by_id = {}
    for i, run in enumerate(runs):
        for rec in run:
            by_id.setdefault(rec["point_id"], {})[i] = rec
    rows = []
    for pid in sorted(by_id):
        cats = []
        for i in sorted(by_id[pid]):
            c, _d = classify(by_id[pid][i])
            cats.append(c)
        verdict = cats[0] if len(set(cats)) == 1 else ("FLAKY" if len(cats) > 1 else cats[0])
        if len(cats) > 1 and len(set(cats)) > 1:
            verdict = "FLAKY"
        rows.append((pid, ",".join(cats), verdict))
    with open(out_tsv, "w", encoding="utf-8") as fh:
        fh.write("# E2E_VERDICT_R9M3A.tsv -- per point verdict over the runs (M3b)" + NL)
        fh.write(TAB.join(["point_id", "per_run", "verdict"]) + NL)
        for r in rows:
            fh.write(TAB.join(r) + NL)
    for r in rows:
        print(TAB.join(r))
    print("WROTE " + out_tsv)
    return 0


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "posctrl"
    if mode == "posctrl":
        return mode_posctrl(sys.argv[2])
    if mode == "formal":
        return mode_formal(sys.argv[2:-1], sys.argv[-1])
    print("unknown mode", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
