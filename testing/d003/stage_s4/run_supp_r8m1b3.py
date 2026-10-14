#!/usr/bin/env python3
# run_supp_r8m1b3.py -- P05-S4 R8 M1b3 section 6: preflight and supplementary run. New file.
# Imports judge_d003 (not modified). Runs the drivers of PREREG_SUPP_R8_M1b3.tsv, two passes, strictly serial.
# Writes $EV/RESULTS_SUPP_R8_M1b3.tsv only. Does not touch any r8m1b1 file.
import csv, hashlib, importlib.util, os, re, subprocess, sys, time

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1b3")
REG = os.path.join(REPO, "checkpoints", "p05", "registries")
R8A = os.path.join(REG, "s4r8", "M1a")
S4R7_DIR = os.path.join(REPO, "testing", "d003", "stage_s4r7")
PREREG = os.path.join(EV, "PREREG_SUPP_R8_M1b3.tsv")
PREREG_RECORD = os.path.join(EV, "PREREG_SUPP_RECORD_R8_M1b3.txt")
DRIVERS_CATALOG = os.path.join(R8A, "DRIVERS_R8_M1a.tsv")
OUT = os.path.join(EV, "RESULTS_SUPP_R8_M1b3.tsv")
GRID = ["pattern", "both", "4", "3"]  # same grid as the M1b1 runner (plan_and_run_m1b_r8m1b1.py:15)
TIMEOUT_S = 120  # same as the M1b1 runner (plan_and_run_m1b_r8m1b1.py:16)
EXPECTED_PREREG_SHA = "712a5547d1257d456b295281e7df00642a49d8f9c4ed97210502127a50985738"
EXPECTED_JUDGE_SHA = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXPECTED_TOTAL_CALLS = 684


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def stop(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
    header = lines[0].split("\t")
    return [dict(zip(header, l.split("\t"))) for l in lines[1:]]


def clean_env(env_str):
    """Same rule as clean_env in plan_and_run_m1b_r8m1b1.py:31-41: inherited FMM_* and S4FMM_* removed first."""
    env = {k: v for k, v in os.environ.items() if not (k.startswith("FMM_") or k.startswith("S4FMM_"))}
    for part in env_str.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            env[k] = v
    return env


def env_str_of(d):
    return ";".join("%s=%s" % (k, d[k]) for k in sorted(d))


def parse_env(env_str):
    d = {}
    for part in env_str.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            d[k] = v
    return d


def load_drivers():
    drv = {}
    for r in read_tsv(DRIVERS_CATALOG):
        p = r.get("driver_path", "")
        if not os.path.isabs(p):
            p = os.path.join(REPO, p)
        drv[r["driver"]] = (r["driver_sha256"], p)
    return drv


RE_HITC = None


def facts(judge, text):
    f = judge.facts_from_log(text)
    return f


def judge_class(judge, run_rc, rc1, rc2, hit, real, inj_call):
    """judge_d003.classify with control=False (all 342 rows are injection rows)."""
    return judge.classify(run_rc, rc1, rc2, hit, control=False, real=real, inj_call=inj_call)


def evaluate_verdict(contract, exp_cls, exp_rc1, exp_rc2, exp_run_rc, exp_hit,
                     act_cls, act_rc1, act_rc2, act_run_rc, act_hit):
    """Rewrite of evaluate_verdict (plan_and_run_m1b_r8m1b1.py:75-115), same branches.
    Branch lines of the original: NOT_RUN 77-78 (not used here), BASELINE_RC_EQUAL 80-85 (not used here),
    NOT_REACHED_AS_EXPECTED 87-90, CONTROL_OK 92-95 (not used here), IDENTICAL 97-100 (not used here),
    REPORTED_FAILURE/CRASH/SILENT_SWALLOW 102-111, fallback 113-115.
    """
    if contract == "NOT_REACHED_AS_EXPECTED":  # original 87-90
        if act_cls == "INVALID" and act_hit == 0 and act_run_rc is not None:
            return "NOT_REACHED_AS_EXPECTED"
        return "MISMATCH"
    if contract in ("REPORTED_FAILURE", "CRASH", "SILENT_SWALLOW"):  # original 102-111
        if act_cls == exp_cls:
            if exp_rc1 not in ("-", "", None):
                if str(act_rc1) != str(exp_rc1):
                    return "MISMATCH"
            if exp_rc2 not in ("-", "", None) and str(exp_rc2) != "0":
                if str(act_rc2) != str(exp_rc2):
                    return "MISMATCH"
            return "MATCH"
        return "MISMATCH"
    if act_cls == exp_cls:  # original 113-114
        return "MATCH"
    return "MISMATCH"


def run_once(drv_path, env_str, inj_text_check):
    child_env = clean_env(env_str)
    cmd = [drv_path] + GRID
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, env=child_env, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=TIMEOUT_S)
        raw_rc = proc.returncode
        out = proc.stdout.decode("utf-8", errors="replace")
        err = proc.stderr.decode("utf-8", errors="replace")
    except subprocess.TimeoutExpired as exc:
        raw_rc = 124
        out = (exc.stdout or b"").decode("utf-8", errors="replace")
        err = (exc.stderr or b"").decode("utf-8", errors="replace")
    dt = time.time() - t0
    if raw_rc < 0:
        sig = -raw_rc
        run_rc = 128 + sig
    elif raw_rc >= 128:
        sig = raw_rc - 128
        run_rc = raw_rc
    else:
        sig = 0
        run_rc = raw_rc
    return {"run_rc": run_rc, "signal": sig, "out": out, "err": err, "secs": round(dt, 2)}


def main():
    # ---------- preflight ----------
    if not os.path.isfile(PREREG):
        stop("preregistration table missing")
    if sha256_file(PREREG) != EXPECTED_PREREG_SHA:
        stop("preregistration sha256 differs from the frozen value")
    judge_path = os.path.join(REPO, "testing", "d003", "judge_d003.py")
    if sha256_file(judge_path) != EXPECTED_JUDGE_SHA:
        stop("judge sha256 differs")
    sys.path.insert(0, S4R7_DIR)
    judge = load_module("judge_d003", judge_path)
    env_mod = load_module("expected_env_independent_r7", os.path.join(S4R7_DIR, "expected_env_independent_r7.py"))
    m2_mod = load_module("run_m2_r7", os.path.join(S4R7_DIR, "run_m2_r7.py"))
    drivers = load_drivers()

    rows = read_tsv(PREREG)
    if len(rows) != 342:
        stop("row count %d != 342" % len(rows))
    # driver sha and existence, env vs expected_env_from_history, inj_call/real vs source rules
    for r in rows:
        dname = r["driver_name"]
        if dname not in drivers:
            stop("driver %s not in DRIVERS_R8_M1a" % dname)
        dsha, dpath = drivers[dname]
        if dsha != r["driver_sha256"]:
            stop("driver sha differs for %s" % dname)
        if sha256_file(dpath) != dsha:
            stop("driver file sha differs for %s" % dname)
        exp_env = env_mod.expected_env_from_history(r["group"], r["base_id"], "F2")
        if parse_env(r["env"]) != exp_env:
            stop("env differs from expected_env_from_history for %s" % r["point_id"])
        real_now = m2_mod.real_of(r["group"], r["base_id"])
        if (r["real"] == "True") != bool(real_now):
            stop("real differs from run_m2_r7.real_of for %s" % r["point_id"])
    print("PREFLIGHT_OK rows=%d drivers=%d" % (len(rows), len(set(r["driver_name"] for r in rows))))
    if "--preflight-only" in sys.argv:
        return 0

    # ---------- run ----------
    fields = ["row_id", "group", "point_id", "tree", "driver_name", "driver_sha256", "env_as_run", "inj_call", "real",
              "exp_class", "exp_rc1", "exp_rc2", "exp_run_rc", "exp_hit", "contract",
              "p1_run_rc", "p1_signal", "p1_rc1", "p1_rc2", "p1_hit", "p1_driver_line", "p1_class", "p1_hitline_ok",
              "p2_run_rc", "p2_signal", "p2_rc1", "p2_rc2", "p2_hit", "p2_driver_line", "p2_class", "p2_hitline_ok",
              "pass_consistent", "verdict_p1", "verdict_p2", "verdict_overall", "secs_p1", "secs_p2"]
    results = []
    total_calls = 0
    for r in rows:
        dsha, dpath = drivers[r["driver_name"]]
        env_str = env_str_of(parse_env(r["env"]))  # sorted keys, as expected_env_from_history returns them
        inj_call = int(r["inj_call"])
        real = (r["real"] == "True")
        passes = []
        for _pas in (1, 2):
            res = run_once(dpath, env_str, None)
            total_calls += 1
            drv_line = [l for l in res["out"].splitlines() if l.startswith("S4FMM DRIVER")]
            hit_line_ok = ("S4FMM HITCOUNT" in res["out"]) or ("S4FMM HIT" in res["out"])
            f = facts(judge, res["out"])
            cls, label, reason = judge_class(judge, res["run_rc"], f["rc1"], f["rc2"], f["hit"], real, inj_call)
            passes.append({"res": res, "facts": f, "cls": cls, "driver_line": drv_line, "hitline_ok": hit_line_ok})
        p1, p2 = passes
        pass_consistent = "YES" if (p1["cls"] == p2["cls"] and p1["res"]["run_rc"] == p2["res"]["run_rc"]
                                    and p1["facts"] == p2["facts"]) else "NO"
        v1 = evaluate_verdict(r["comparison_contract"], r["expected_class"], r["expected_rc1"], r["expected_rc2"],
                              r["expected_run_rc"], r["expected_hit"], p1["cls"], p1["facts"]["rc1"],
                              p1["facts"]["rc2"], p1["res"]["run_rc"], p1["facts"]["hit"])
        v2 = evaluate_verdict(r["comparison_contract"], r["expected_class"], r["expected_rc1"], r["expected_rc2"],
                              r["expected_run_rc"], r["expected_hit"], p2["cls"], p2["facts"]["rc1"],
                              p2["facts"]["rc2"], p2["res"]["run_rc"], p2["facts"]["hit"])
        overall = "MATCH" if (v1 == "MATCH" or v1 == "NOT_REACHED_AS_EXPECTED") and v1 == v2 else (
            "FLAKY" if pass_consistent == "NO" else "MISMATCH")
        if pass_consistent == "NO":
            overall = "FLAKY"
        if v1 == "NOT_REACHED_AS_EXPECTED" and v2 == "NOT_REACHED_AS_EXPECTED" and pass_consistent == "YES":
            overall = "NOT_REACHED_AS_EXPECTED"
        results.append({
            "row_id": r["row_id"], "group": r["group"], "point_id": r["point_id"], "tree": r["tree"],
            "driver_name": r["driver_name"], "driver_sha256": r["driver_sha256"], "env_as_run": env_str,
            "inj_call": r["inj_call"], "real": r["real"],
            "exp_class": r["expected_class"], "exp_rc1": r["expected_rc1"], "exp_rc2": r["expected_rc2"],
            "exp_run_rc": r["expected_run_rc"], "exp_hit": r["expected_hit"], "contract": r["comparison_contract"],
            "p1_run_rc": p1["res"]["run_rc"], "p1_signal": p1["res"]["signal"], "p1_rc1": p1["facts"]["rc1"],
            "p1_rc2": p1["facts"]["rc2"], "p1_hit": p1["facts"]["hit"],
            "p1_driver_line": "|".join(p1["driver_line"]), "p1_class": p1["cls"], "p1_hitline_ok": p1["hitline_ok"],
            "p2_run_rc": p2["res"]["run_rc"], "p2_signal": p2["res"]["signal"], "p2_rc1": p2["facts"]["rc1"],
            "p2_rc2": p2["facts"]["rc2"], "p2_hit": p2["facts"]["hit"],
            "p2_driver_line": "|".join(p2["driver_line"]), "p2_class": p2["cls"], "p2_hitline_ok": p2["hitline_ok"],
            "pass_consistent": pass_consistent, "verdict_p1": v1, "verdict_p2": v2, "verdict_overall": overall,
            "secs_p1": p1["res"]["secs"], "secs_p2": p2["res"]["secs"],
        })
        print("%s %s %s run_rc=%s rc1=%s hit=%s class=%s verdict=%s" % (
            r["row_id"], r["group"], r["point_id"], p1["res"]["run_rc"], p1["facts"]["rc1"], p1["facts"]["hit"],
            p1["cls"], overall))
        sys.stdout.flush()

    if total_calls != EXPECTED_TOTAL_CALLS:
        stop("physical calls %d != %d" % (total_calls, EXPECTED_TOTAL_CALLS))

    # ---------- write ----------
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write("# RESULTS_SUPP_R8_M1b3.tsv -- P05-S4 R8 M1b3 supplementary run (U205-U207). Judge: judge_d003.classify (imported).\n")
        fh.write("# Two passes, strictly serial; env_as_run = the FMM_*/S4FMM_* set given to the driver (U207). Facts only; verdict per evaluate_verdict rewrite.\n")
        w = csv.writer(fh, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE)
        w.writerow(fields)
        for x in results:
            w.writerow([x[c] for c in fields])
    os.replace(tmp, OUT)
    print("TOTAL_PHYSICAL_CALLS=%d" % total_calls)
    print("RESULTS_WRITTEN=%s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
