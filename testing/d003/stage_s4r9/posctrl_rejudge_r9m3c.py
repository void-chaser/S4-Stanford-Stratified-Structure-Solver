#!/usr/bin/env python3
# posctrl_rejudge_r9m3c.py -- positive control for the formal re-judge: write tampered on-disk copies of real M3b point
# records under $EV/posctrl/rejudge/, invoke the formal script on them, and require it to report the tampered category.
# Every frontend covers API_SILENT, RETRY_DIFF, HIT_OFF_TARGET, INVALID, CONTROL_BAD; plus one FLAKY (two run files).
# No constant self-proof: the category is recomputed by the formal script from the file content. New file (r9m3c).
import os, sys, json, subprocess, copy
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3c")
M3B = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b")
PTS = os.path.join(M3B, "runs/pass1/points")
SCRIPT = os.path.join(REPO, "testing/d003/stage_s4r9/rejudge_e2e_r9m3c.py")
OUTDIR = os.path.join(EV, "posctrl/rejudge")
OUT = os.path.join(EV, "POSCTRL_REJUDGE_R9M3C.txt")
TAB = chr(9)
NL = chr(10)


def load(pid):
    return json.load(open(os.path.join(PTS, pid + ".json"), encoding="utf-8"))


def clone(rec):
    return json.loads(json.dumps(rec))


def py_inj(rec):
    return json.loads(rec["steps"]["inject"]["stdout"])


def set_py_inj(rec, d):
    rec["steps"]["inject"]["stdout"] = json.dumps(d)


def refvals(rec):
    d = json.loads(rec["steps"]["ref"]["stdout"])
    return d["steps"]["ref"]["values"]


def hit_replace(rec, old, new):
    rec["steps"]["inject"]["stderr"] = rec["steps"]["inject"]["stderr"].replace(old, new)


def drop_hits(rec):
    rec["steps"]["inject"]["stderr"] = "".join(
        ln + NL for ln in rec["steps"]["inject"]["stderr"].splitlines() if "S4FMM HIT" not in ln)


def mk_py(kind):
    if kind == "CONTROL_BAD":
        rec = clone(load("py_ctl_cf"))
        rec["steps"]["inject"]["rc"] = 1
        rec["steps"]["inject"]["stderr"] = "boom" + NL
        rec["steps"]["inject"]["n_hits"] = 0
        rec["steps"]["inject"]["hit_lines"] = []
        return rec, "py_ctl_cf"
    rec = clone(load("py_fft_s4malloc"))
    rv = refvals(rec)
    if kind == "API_SILENT":
        d = py_inj(rec)
        d["steps"]["A_inject"] = {"ok": True, "values": rv, "error_type": None, "error_msg": None}
        set_py_inj(rec, d)
    elif kind == "RETRY_DIFF":
        d = py_inj(rec)
        bad = list(rv)
        bad[0] = bad[0] * 1.5
        d["steps"]["B_retry_same"] = {"ok": True, "values": bad, "error_type": None, "error_msg": None}
        set_py_inj(rec, d)
    elif kind == "HIT_OFF_TARGET":
        hit_replace(rec, "(hit=1)", "(hit=7)")
    elif kind == "INVALID":
        drop_hits(rec)
    return rec, "py_fft_s4malloc"


def lua_batch_ref(rec):
    for ln in rec["steps"]["ref"]["stdout"].splitlines():
        if ln.startswith("VALUES "):
            return [float(x) for x in ln.split()[1:5]]
    return None


def mk_lua_batch(kind):
    if kind == "CONTROL_BAD":
        rec = clone(load("lua_batch_ctl_fft"))
        rec["steps"]["inject"]["rc"] = 1
        rec["steps"]["inject"]["stderr"] = "boom" + NL
        rec["steps"]["inject"]["n_hits"] = 0
        rec["steps"]["inject"]["hit_lines"] = []
        return rec, "lua_batch_ctl_fft"
    rec = clone(load("lua_batch_fft_s4malloc"))
    rv = lua_batch_ref(rec)
    vals = "VALUES " + " ".join(repr(x) for x in rv) + NL + "BATCH_DONE" + NL
    if kind == "API_SILENT":
        rec["steps"]["inject"]["rc"] = 0
        rec["steps"]["inject"]["stdout"] = vals
        rec["steps"]["inject"]["stderr"] = "".join(
            ln + NL for ln in rec["steps"]["inject"]["stderr"].splitlines() if not ln.startswith("GetPoyntingFlux:"))
    elif kind == "RETRY_DIFF":
        bad = list(rv)
        bad[0] = bad[0] * 1.5
        rec["steps"]["r2"]["stdout"] = "VALUES " + " ".join(repr(x) for x in bad) + NL + "BATCH_DONE" + NL
    elif kind == "HIT_OFF_TARGET":
        hit_replace(rec, "(hit=1)", "(hit=7)")
    elif kind == "INVALID":
        drop_hits(rec)
    return rec, "lua_batch_fft_s4malloc"


def repl_lines(rec, phase, key):
    return rec["steps"][phase]["stdout"].splitlines()


def mk_lua_repl(kind):
    if kind == "CONTROL_BAD":
        rec = clone(load("lua_repl_ctl_fft"))
        rec["steps"]["inject"]["stdout"] = "A nil nil nil nil" + NL + "B 0.0 0.0 0.0 0.0" + NL + "REPL_DONE" + NL
        return rec, "lua_repl_ctl_fft"
    rec = clone(load("lua_repl_cf_s4malloc"))
    if kind == "API_SILENT":
        rec["steps"]["inject"]["stderr"] = "".join(
            ln + NL for ln in rec["steps"]["inject"]["stderr"].splitlines() if not ln.startswith("GetPoyntingFlux:"))
    elif kind == "RETRY_DIFF":
        out = []
        for ln in rec["steps"]["inject"]["stdout"].splitlines():
            if ln.startswith("B "):
                out.append("B 0.99 0.0 0.0 0.0")
            else:
                out.append(ln)
        rec["steps"]["inject"]["stdout"] = NL.join(out) + NL
    elif kind == "HIT_OFF_TARGET":
        hit_replace(rec, "(hit=1)", "(hit=7)")
    elif kind == "INVALID":
        drop_hits(rec)
    return rec, "lua_repl_cf_s4malloc"


def write_case(name, rec1, rec2, pid):
    for phase, rec in (("pass1", rec1), ("pass2", rec2)):
        d = os.path.join(OUTDIR, name, phase, "points")
        os.makedirs(d, exist_ok=True)
        json.dump(rec, open(os.path.join(d, pid + ".json"), "w", encoding="utf-8"), indent=1)
    return os.path.join(OUTDIR, name)


def judge_case(name, pid):
    case = os.path.join(OUTDIR, name)
    vout = os.path.join(case, "VERDICT.tsv")
    cmd = [sys.executable, "-I", "-B", SCRIPT, "formal", "--runs-root", case, "--out", vout, "--no-compare"]
    p = subprocess.run(cmd, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    got = "NO_ROW"
    if os.path.isfile(vout):
        for line in open(vout, encoding="utf-8"):
            if line.startswith("#") or not line.strip():
                continue
            f = line.rstrip(NL).split(TAB)
            if f[0] == pid:
                got = f[4]
    return got, p.returncode


def main():
    cases = []
    for fe, mk, pid in (("py", mk_py, "py_fft_s4malloc"),
                        ("lua_batch", mk_lua_batch, "lua_batch_fft_s4malloc"),
                        ("lua_repl", mk_lua_repl, "lua_repl_cf_s4malloc")):
        for kind in ("API_SILENT", "RETRY_DIFF", "HIT_OFF_TARGET", "INVALID", "CONTROL_BAD"):
            if kind == "CONTROL_BAD":
                pid2 = {"py": "py_ctl_cf", "lua_batch": "lua_batch_ctl_fft", "lua_repl": "lua_repl_ctl_fft"}[fe]
            else:
                pid2 = pid
            rec, _ = mk(kind)
            write_case(fe + "_" + kind, rec, clone(rec), pid2)
            cases.append((fe + "_" + kind, kind, pid2))
    # FLAKY: two different on-disk runs for the same point
    ok_rec = clone(load("py_fft_s4malloc"))
    bad_rec = mk_py("RETRY_DIFF")[0]
    write_case("py_FLAKY", ok_rec, bad_rec, "py_fft_s4malloc")
    cases.append(("py_FLAKY", "FLAKY", "py_fft_s4malloc"))
    results = []
    for name, want, pid in cases:
        got, rc = judge_case(name, pid)
        results.append((name, want, got, got == want, rc))
    all_ok = all(r[3] for r in results)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("# POSCTRL_REJUDGE_R9M3C.txt -- positive control of rejudge_e2e_r9m3c.py on tampered records written to disk" + NL)
        fh.write("# each case is a real file under checkpoints/p05/evidence/p05-s4r9/m3c/posctrl/rejudge/<case>/pass{1,2}/points/;" + NL)
        fh.write("# the verdict is recomputed by the formal script from the file content (no constant self-proof)." + NL)
        for name, want, got, ok, rc in results:
            fh.write("%s: %s (expected=%s actual=%s rc=%s)" % (name, "PASS" if ok else "FAIL", want, got, rc) + NL)
        fh.write("OVERALL_POSITIVE_CONTROL: %s (%d/%d)" % ("PASS" if all_ok else "FAIL",
                                                           sum(1 for r in results if r[3]), len(results)) + NL)
        fh.write("CATEGORIES_COVERED: " + ",".join(sorted(set(r[1] for r in results))) + NL)
        fh.write("FRONTENDS_COVERED: py,lua_batch,lua_repl" + NL)
    for name, want, got, ok, rc in results:
        print("%-28s want=%-14s got=%-14s %s" % (name, want, got, "PASS" if ok else "FAIL"))
    print("OVERALL %s %d/%d" % ("PASS" if all_ok else "FAIL", sum(1 for r in results if r[3]), len(results)))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
