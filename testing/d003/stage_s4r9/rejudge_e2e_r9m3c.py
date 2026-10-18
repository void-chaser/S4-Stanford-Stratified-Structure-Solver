#!/usr/bin/env python3
# rejudge_e2e_r9m3c.py -- independent read-only re-judgement of the M3b E2E point records (new implementation; it does
# not import or invoke any r9m3b script). Every category is recomputed from the raw per-point JSON, the pre-registration
# and the calibration table, and compared with the M3b verdict table. New file (r9m3c).
# usage: rejudge_e2e_r9m3c.py formal [--runs-root DIR] [--out TSV] [--verdict PATH] [--compare-out PATH]
#                                   [--prereg PATH] [--no-compare]
import os, sys, json, re
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3c")
M3B = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b")
TAB = chr(9)
NL = chr(10)
TOL = 1e-12


def read_table(path):
    rows = []
    hdr = None
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        rows.append(dict(zip(hdr, f)))
    return rows


def rel(a, b):
    if a is None or b is None or len(a) != len(b):
        return 999.0
    m = 0.0
    for x, y in zip(a, b):
        if x is None or y is None:
            return 999.0
        if x == y:
            continue
        m = max(m, abs(x - y) / max(1.0, abs(x), abs(y)))
    return m


def fmt(x):
    return ("%.3e" % x) if isinstance(x, float) else str(x)


def close_str(x):
    try:
        return float(x) <= TOL
    except Exception:
        return False


def json_of(run):
    for line in reversed(((run or {}).get("stdout") or "").strip().splitlines()):
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
            out = []
            for p in line.split()[1:5]:
                out.append(None if p == "nil" else float(p))
            while len(out) < 4:
                out.append(None)
            return out
    return None


def hit_lines(run):
    return [ln for ln in ((run or {}).get("stderr") or "").splitlines() if "S4FMM HIT" in ln]


def parse_seq(line):
    m = re.search(r"\(hit=(\d+)\)", line)
    if m:
        return int(m.group(1))
    e = re.search(r"\(exec call=(\d+)\)", line)
    return int(e.group(1)) if e else None


def parse_size(line):
    m = re.search(r"(\d+) B \(hit=", line)
    return int(m.group(1)) if m else None


def visible_expected(rec, run):
    exp = rec.get("exp_visible", "")
    fe = rec.get("frontend")
    if exp.startswith("RuntimeError:text~"):
        m = re.search(r'text~"([^"]+)"', exp)
        want = m.group(1) if m else ""
        a = ((json_of(run) or {}).get("steps", {}) or {}).get("A_inject")
        return (a is not None and a.get("ok") is False and a.get("error_type") == "RuntimeError"
                and want in (a.get("error_msg") or "")), want
    if exp.startswith("stderr_line~"):
        m = re.search(r'~\^(?:"([^"]*)"|(\S+))', exp)
        want = (m.group(1) if m and m.group(1) is not None else (m.group(2) if m else "")).strip()
        got = any(ln.startswith(want) for ln in ((run or {}).get("stderr") or "").splitlines())
        if fe == "lua_batch":
            got = got and (run.get("rc") not in (0, None))
        return got, want
    return False, exp


def facts(prereg, pointrec):
    rec = dict(prereg)
    rec.update(pointrec)
    steps = rec.get("steps", {})
    st_ref = steps.get("ref", {})
    st_inj = steps.get("inject", {})
    st_r2 = steps.get("r2", {})
    fe = rec.get("frontend")
    f = {"rc": st_inj.get("rc"), "hits": len(hit_lines(st_inj)), "hit_seq": None, "hit_size": None,
         "same_rel": "NA", "freshobj_rel": "NA", "freshproc_rel": "NA", "inj_rel": "NA",
         "visible": False, "ref_ok": False, "a_ok": False,
         "retry_same_ok": None, "freshobj_ok": None, "replay_ok": None, "injA_nonnull": None}
    if fe == "py":
        ref = (json_of(st_ref) or {}).get("steps", {}).get("ref")
        sh = (json_of(st_inj) or {}).get("steps", {}) or {}
        a, b, c = sh.get("A_inject"), sh.get("B_retry_same"), sh.get("C_retry_fresh_obj")
        r2 = (json_of(st_r2) or {}).get("steps", {}).get("fresh")
        rv = ref.get("values") if ref else None
        f["ref_ok"] = bool(ref and ref.get("ok") and rv is not None and None not in rv)
        f["a_ok"] = bool(a is not None and a.get("ok"))
        if b is not None and b.get("ok") and rv:
            f["same_rel"] = fmt(rel(rv, b.get("values")))
        if c is not None and c.get("ok") and rv:
            f["freshobj_rel"] = fmt(rel(rv, c.get("values")))
        if r2 is not None and r2.get("ok") and rv:
            f["freshproc_rel"] = fmt(rel(rv, r2.get("values")))
        f["retry_same_ok"] = bool(b is not None and b.get("ok"))
        f["freshobj_ok"] = bool(c is not None and c.get("ok"))
        f["replay_ok"] = bool(r2 is not None and r2.get("ok"))
        f["visible"], f["want"] = visible_expected(rec, st_inj)
    elif fe == "lua_batch":
        rv = values_line(st_ref.get("stdout"))
        injv = values_line(st_inj.get("stdout"))
        r2v = values_line(st_r2.get("stdout"))
        f["ref_ok"] = rv is not None
        f["retry_same_ok"] = "N/A"
        if rv is not None and injv is not None:
            f["inj_rel"] = fmt(rel(rv, injv))
        f["replay_ok"] = bool(r2v is not None and st_r2.get("rc") == 0)
        if rv is not None and r2v is not None:
            f["freshproc_rel"] = fmt(rel(rv, r2v))
        f["visible"], f["want"] = visible_expected(rec, st_inj)
    else:
        refA = repl_values(st_ref.get("stdout"), "A")
        injA = repl_values(st_inj.get("stdout"), "A")
        injB = repl_values(st_inj.get("stdout"), "B")
        r2A = repl_values(st_r2.get("stdout"), "A")
        f["ref_ok"] = bool(refA is not None and None not in refA)
        if refA is not None and injA is not None and None not in injA:
            f["inj_rel"] = fmt(rel(refA, injA))
        if refA is not None and injB is not None and None not in injB:
            f["same_rel"] = fmt(rel(refA, injB))
        if refA is not None and r2A is not None and None not in r2A:
            f["freshproc_rel"] = fmt(rel(refA, r2A))
        f["retry_same_ok"] = bool(injB is not None and None not in injB)
        f["replay_ok"] = bool(r2A is not None and None not in r2A and st_r2.get("rc") == 0)
        f["injA_nonnull"] = bool(injA is not None and None not in injA)
        f["visible"], f["want"] = visible_expected(rec, st_inj)
    hs = hit_lines(st_inj)
    if len(hs) == 1:
        f["hit_seq"] = parse_seq(hs[0])
        f["hit_size"] = parse_size(hs[0])
    return f


def on_target(rec, f):
    try:
        nth = int(rec.get("nth"))
    except Exception:
        nth = None
    if f["hits"] != 1 or f["hit_seq"] != nth:
        return False
    mode = rec.get("inject_mode")
    calib = str(rec.get("calib_size", "NA"))
    if mode in ("s4malloc", "plan") and calib not in ("", "NA") and f["hit_size"] != int(calib):
        return False
    return True


def decide(rec, f, fe):
    if rec.get("is_control") == "YES":
        ok = bool(f["ref_ok"] and f["rc"] == 0 and f["hits"] == 0)
        if fe == "py":
            ok = ok and f["a_ok"] and f["retry_same_ok"] and f["freshobj_ok"] and f["replay_ok"] \
                and close_str(f["same_rel"]) and close_str(f["freshobj_rel"]) and close_str(f["freshproc_rel"])
        elif fe == "lua_batch":
            ok = ok and f["replay_ok"] and close_str(f["inj_rel"]) and close_str(f["freshproc_rel"])
        else:
            ok = ok and close_str(f["inj_rel"]) and close_str(f["same_rel"]) and close_str(f["freshproc_rel"])
        return "CONTROL_OK" if ok else "CONTROL_BAD"
    if not f["ref_ok"]:
        return "INVALID"
    if f["hits"] < 1:
        return "INVALID"
    if not on_target(rec, f):
        return "HIT_OFF_TARGET"
    if not f["visible"]:
        return "API_SILENT"
    if fe == "lua_repl" and f["injA_nonnull"]:
        return "INVALID"
    if fe != "lua_batch" and f["retry_same_ok"] is False:
        return "RETRY_FAIL"
    if fe == "py" and f["freshobj_ok"] is False:
        return "RETRY_FAIL"
    if f["replay_ok"] is False:
        return "RETRY_FAIL"
    if fe == "py":
        if not (close_str(f["same_rel"]) and close_str(f["freshobj_rel"]) and close_str(f["freshproc_rel"])):
            return "RETRY_DIFF"
    elif fe == "lua_repl":
        if not (close_str(f["same_rel"]) and close_str(f["freshproc_rel"])):
            return "RETRY_DIFF"
    else:
        if not close_str(f["freshproc_rel"]):
            return "RETRY_DIFF"
    return "E2E_OK"


def load_points(root, phase):
    d = os.path.join(root, phase, "points")
    out = {}
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json"):
            out[fn[:-5]] = json.load(open(os.path.join(d, fn), encoding="utf-8"))
    return out


def main():
    if len(sys.argv) < 2 or sys.argv[1] != "formal":
        print("usage: rejudge_e2e_r9m3c.py formal [options]", file=sys.stderr)
        return 2
    args = sys.argv[2:]
    runs_root = os.path.join(M3B, "runs")
    out = os.path.join(EV, "REJUDGE_E2E_R9M3C.tsv")
    verdict_p = os.path.join(M3B, "E2E_VERDICT_R9M3B.tsv")
    compare_out = os.path.join(EV, "REJUDGE_COMPARE_R9M3C.txt")
    prereg_p = os.path.join(M3B, "PREREG_E2E_R9M3B.tsv")
    do_compare = True
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--runs-root":
            runs_root = args[i + 1]; i += 2
        elif a == "--out":
            out = args[i + 1]; i += 2
        elif a == "--verdict":
            verdict_p = args[i + 1]; i += 2
        elif a == "--compare-out":
            compare_out = args[i + 1]; i += 2
        elif a == "--prereg":
            prereg_p = args[i + 1]; i += 2
        elif a == "--no-compare":
            do_compare = False; i += 1
        else:
            print("unknown arg " + a, file=sys.stderr); return 2
    prereg = read_table(prereg_p)
    p1 = load_points(runs_root, "pass1")
    p2 = load_points(runs_root, "pass2")
    verdicts = {}
    if os.path.isfile(verdict_p):
        for r in read_table(verdict_p):
            verdicts[r.get("point_id")] = r.get("verdict")
    rows = []
    counts = {}
    for rec in prereg:
        pid = rec.get("point_id")
        fe = rec.get("frontend")
        if pid not in p1 or pid not in p2:
            rows.append((pid, fe, "MISSING_RUN", "MISSING_RUN", "MISSING_RUN", "-", "-", "-", "-", "-", "-", "-", "-", "-", verdicts.get(pid, ""), "DIFF"))
            counts["MISSING_RUN"] = counts.get("MISSING_RUN", 0) + 1
            continue
        f1 = facts(rec, p1[pid])
        f2 = facts(rec, p2[pid])
        c1 = decide(rec, f1, fe)
        c2 = decide(rec, f2, fe)
        verdict = c1 if c1 == c2 else "FLAKY"
        counts[verdict] = counts.get(verdict, 0) + 1
        m3 = verdicts.get(pid, "")
        row = (pid, fe, c1, c2, verdict,
               "%d/%d" % (f1["hits"], f2["hits"]),
               "%s/%s" % (f1["hit_seq"], f2["hit_seq"]),
               "%s/%s" % (f1["hit_size"], f2["hit_size"]),
               "%s/%s" % (on_target(rec, f1), on_target(rec, f2)),
               "%s/%s" % (f1["visible"], f2["visible"]),
               "%s/%s" % (f1["same_rel"], f2["same_rel"]),
               "%s/%s" % (f1["freshobj_rel"], f2["freshobj_rel"]),
               "%s/%s" % (f1["freshproc_rel"], f2["freshproc_rel"]),
               "%s/%s" % (f1["rc"], f2["rc"]),
               m3, "MATCH" if verdict == m3 else "DIFF")
        rows.append(row)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# REJUDGE_E2E_R9M3C.tsv -- independent re-judgement from m3b/runs/pass{1,2}/points and the pre-registration" + NL)
        fh.write(TAB.join(["point_id", "frontend", "pass1_category", "pass2_category", "verdict",
                           "hits_p1_p2", "hit_seq_p1_p2", "hit_size_p1_p2", "on_target_p1_p2", "visible_p1_p2",
                           "retry_same_rel_p1_p2", "retry_fresh_obj_rel_p1_p2", "fresh_proc_rel_p1_p2", "rc_p1_p2",
                           "m3b_verdict", "match"]) + NL)
        for r in rows:
            fh.write(TAB.join(str(x) for x in r) + NL)
    diffs = [r for r in rows if r[-1] != "MATCH"]
    counts_txt = ", ".join("%s=%d" % (k, v) for k, v in sorted(counts.items()))
    print("COUNTS " + counts_txt)
    print("DIFFS=%d" % len(diffs))
    for r in diffs[:10]:
        print("DIFF " + TAB.join([str(r[0]), str(r[4]), str(r[-2])]))
    if do_compare:
        with open(compare_out, "w", encoding="utf-8") as fh:
            fh.write("# REJUDGE_COMPARE_R9M3C.txt -- point-wise comparison of the independent verdict with E2E_VERDICT_R9M3B.tsv" + NL)
            fh.write("POINTS=%d" % len(rows) + NL)
            fh.write("DIFFS=%d" % len(diffs) + NL)
            for r in diffs:
                fh.write("DIFF\t%s\tindependent=%s\tm3b=%s" % (r[0], r[4], r[-2]) + NL)
            fh.write("VERDICT_COUNTS " + counts_txt + NL)
        print("COMPARE_WROTE " + compare_out)
    print("WROTE " + out)
    return 0 if not diffs else 1


if __name__ == "__main__":
    sys.exit(main())
