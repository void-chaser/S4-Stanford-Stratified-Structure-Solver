#!/usr/bin/env python3
# plan_and_run_m1b_r8m1b1.py -- P05-S4 R8 M1b first execution runner (r8m1b1, brief §4-§6). New file.
# Reads only frozen REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv and DRIVERS_R8_M1a.tsv.
# Does NOT modify any existing registries or product source.
import hashlib, os, re, subprocess, sys, time

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "testing", "d003"))
import judge_d003 as J

M1A_DIR = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")
REGISTRY_PATH = os.path.join(M1A_DIR, "REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv")
DRIVERS_CATALOG_PATH = os.path.join(M1A_DIR, "DRIVERS_R8_M1a.tsv")

GRID = ["pattern", "both", "4", "3"]
TIMEOUT_S = 120

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def clean_env(env_str):
    env = {k: v for k, v in os.environ.items() if not (k.startswith("FMM_") or k.startswith("S4FMM_"))}
    if env_str and env_str != "NOT_RUN":
        for part in env_str.split(";"):
            if "=" in part:
                k, v = part.split("=", 1)
                # "none" is a harness token meaning no injection; do not pass to driver as S4FMM_INJECT
                if k == "S4FMM_INJECT" and v == "none":
                    continue
                env[k] = v
    return env

def load_drivers_catalog():
    drv_map = {}
    with open(DRIVERS_CATALOG_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\r\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 7:
                drv_name = parts[0]
                drv_sha = parts[4]
                drv_path = parts[6]
                if not os.path.isabs(drv_path):
                    drv_path = os.path.join(REPO, drv_path)
                drv_map[drv_name] = (drv_sha, drv_path)
    return drv_map

def load_prereg():
    rows = []
    header = None
    with open(REGISTRY_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\r\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if header is None:
                header = parts
                continue
            rows.append(dict(zip(header, parts)))
    return header, rows

def evaluate_verdict(contract, exp_cls, exp_rc1, exp_rc2, exp_run_rc, exp_hit,
                     actual_cls, actual_rc1, actual_rc2, actual_run_rc, actual_hit):
    if contract == "NOT_RUN_REGISTRY_ERROR":
        return "NOT_RUN_AS_EXPECTED"
    
    if contract == "BASELINE_RC_EQUAL":
        if (actual_cls == "INVALID" and
            actual_rc1 == 20 and actual_rc2 == 20 and
            actual_run_rc == 0 and actual_hit == 0):
            return "MATCH"
        return "MISMATCH"
    
    if contract == "NOT_REACHED_AS_EXPECTED":
        if actual_cls == "INVALID" and actual_hit == 0 and actual_run_rc is not None:
            return "NOT_REACHED_AS_EXPECTED"
        return "MISMATCH"
    
    if contract == "CONTROL_OK":
        if actual_cls == "CONTROL_OK" and actual_run_rc == 0 and actual_rc1 == 0 and actual_hit == 0:
            return "MATCH"
        return "MISMATCH"
    
    if contract == "IDENTICAL":
        if actual_cls == exp_cls and actual_run_rc == 0 and actual_rc1 == 0 and actual_hit == 0:
            return "MATCH"
        return "MISMATCH"
    
    if contract in ("REPORTED_FAILURE", "CRASH", "SILENT_SWALLOW"):
        if actual_cls == exp_cls:
            if exp_rc1 not in ("-", "", None):
                if str(actual_rc1) != str(exp_rc1):
                    return "MISMATCH"
            if exp_rc2 not in ("-", "", None) and str(exp_rc2) != "0":
                if str(actual_rc2) != str(exp_rc2):
                    return "MISMATCH"
            return "MATCH"
        return "MISMATCH"
    
    if actual_cls == exp_cls:
        return "MATCH"
    return "MISMATCH"

def main():
    ev_dir = os.environ.get("EV")
    if not ev_dir or not os.path.isdir(ev_dir):
        print("ERROR: EV environment variable not set or directory missing: %s" % ev_dir, file=sys.stderr)
        return 2

    drv_catalog = load_drivers_catalog()
    _, prereg_rows = load_prereg()

    # Verify all drivers exist and match sha256
    print("Verifying drivers...")
    for r in prereg_rows:
        dname = r["driver_name"]
        dsha = r["driver_sha256"]
        if dname not in drv_catalog:
            print("ERROR: driver not found in catalog: %s" % dname, file=sys.stderr)
            return 2
        rec_sha, drv_path = drv_catalog[dname]
        if rec_sha != dsha:
            print("ERROR: driver sha mismatch in catalog: %s (rec=%s, reg=%s)" % (dname, rec_sha, dsha), file=sys.stderr)
            return 2
        if not os.path.isfile(drv_path):
            print("ERROR: driver binary missing on disk: %s" % drv_path, file=sys.stderr)
            return 2
        act_sha = sha256_file(drv_path)
        if act_sha != dsha:
            print("ERROR: driver binary sha mismatch: %s (act=%s, reg=%s)" % (drv_path, act_sha, dsha), file=sys.stderr)
            return 2
    print("All drivers verified OK on disk.")

    # 1. Build row-level execution plan
    print("Building execution plan PLAN_M1B_R8_M1b1.tsv...")
    plan_rows = []
    plan_header = [
        "row_id", "group", "point_id", "tree", "mode", "ng", "inject_site",
        "k_nth", "twice", "env_str", "driver_name", "driver_path", "driver_sha256",
        "repeat_strategy", "retry_strategy", "inj_call", "is_control",
        "expected_class", "expected_rc1", "expected_rc2", "expected_run_rc",
        "expected_hit", "expected_label", "comparison_contract", "expect_source"
    ]
    for idx, r in enumerate(prereg_rows, start=1):
        env_str = r["env"]
        mode = "-"
        ng = "-"
        inj = "none"
        nth = "-"
        twice = False
        if env_str != "NOT_RUN":
            for part in env_str.split(";"):
                if part.startswith("FMM_MODE="):
                    mode = part.split("=", 1)[1]
                elif part.startswith("S4FMM_NG="):
                    ng = part.split("=", 1)[1]
                elif part.startswith("S4FMM_INJECT="):
                    inj = part.split("=", 1)[1]
                elif part.startswith("S4FMM_NTH="):
                    nth = part.split("=", 1)[1]
                elif part == "S4FMM_TWICE=slab":
                    twice = True
        
        is_ctrl = (r["expected_class"] == "CONTROL_OK" or r["comparison_contract"] == "BASELINE_RC_EQUAL" or env_str == "NOT_RUN")
        inj_call = 2 if (r.get("expected_rc2") == "20" and r.get("expected_rc1") == "0") else 1
        rep_strat = "not_run" if env_str == "NOT_RUN" else "two_pass"
        ret_strat = "not_run" if env_str == "NOT_RUN" else "internal_driver_retry"
        
        _, drv_path = drv_catalog[r["driver_name"]]
        
        plan_rows.append([
            str(idx), r["group"], r["point_id"], r["tree"], mode, ng, inj,
            nth, str(twice), env_str, r["driver_name"], drv_path, r["driver_sha256"],
            rep_strat, ret_strat, str(inj_call), str(is_ctrl),
            r["expected_class"], r["expected_rc1"], r["expected_rc2"], r["expected_run_rc"],
            r["expected_hit"], r["expected_label"], r["comparison_contract"], r["expect_source"]
        ])

    plan_path = os.path.join(ev_dir, "PLAN_M1B_R8_M1b1.tsv")
    with open(plan_path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(plan_header) + "\n")
        for row in plan_rows:
            fh.write("\t".join(row) + "\n")
    plan_sha = sha256_file(plan_path)
    print("PLAN_M1B_R8_M1b1.tsv written: %d rows, sha256=%s" % (len(plan_rows), plan_sha))

    # 2. Execute runs: Pass 1 and Pass 2
    runs_dir = os.path.join(ev_dir, "runs")
    os.makedirs(runs_dir, exist_ok=True)

    results_data = [] # per-row execution facts and classifications
    total_physical_calls = 0
    t_start = time.time()

    print("Beginning test execution for 830 rows across 2 passes...")
    for idx, r in enumerate(prereg_rows, start=1):
        row_id = str(idx)
        grp = r["group"]
        pid = r["point_id"]
        tree = r["tree"]
        dname = r["driver_name"]
        env_str = r["env"]
        exp_cls = r["expected_class"]
        exp_rc1 = r["expected_rc1"]
        exp_rc2 = r["expected_rc2"]
        exp_run_rc = r["expected_run_rc"]
        exp_hit = r["expected_hit"]
        exp_label = r["expected_label"]
        comp_contract = r["comparison_contract"]
        
        is_ctrl = (exp_cls == "CONTROL_OK" or comp_contract == "BASELINE_RC_EQUAL")
        real = not ("-exec-" in pid)
        inj_call = 2 if (exp_rc2 == "20" and exp_rc1 == "0") else 1

        if env_str == "NOT_RUN":
            # 6 G2c_control rows
            results_data.append({
                "row_id": row_id, "group": grp, "point_id": pid, "tree": tree,
                "driver_name": dname, "env": env_str, "status": "NOT_RUN",
                "p1_run_rc": "-", "p1_signal": "-", "p1_rc1": "-", "p1_rc2": "-", "p1_hit": "-",
                "p1_class": "NOT_RUN_REGISTRY_ERROR", "p1_reason": "NOT_RUN per contract U65a",
                "p2_run_rc": "-", "p2_signal": "-", "p2_rc1": "-", "p2_rc2": "-", "p2_hit": "-",
                "p2_class": "NOT_RUN_REGISTRY_ERROR", "p2_reason": "NOT_RUN per contract U65a",
                "pass_consistent": "YES",
                "verdict_p1": "NOT_RUN_AS_EXPECTED", "verdict_p2": "NOT_RUN_AS_EXPECTED",
                "verdict_overall": "NOT_RUN_AS_EXPECTED",
                "expected_class": exp_cls, "expected_rc1": exp_rc1, "expected_rc2": exp_rc2,
                "expected_run_rc": exp_run_rc, "expected_hit": exp_hit, "expected_label": exp_label,
                "comparison_contract": comp_contract, "expect_source": r["expect_source"],
                "callseq_status": r["callseq_status"], "k_source": r["k_source"]
            })
            continue

        _, drv_path = drv_catalog[dname]
        child_env = clean_env(env_str)
        cmd = [drv_path] + GRID

        # Run Pass 1 and Pass 2
        pass_facts = []
        for pas in (1, 2):
            pdir = os.path.join(runs_dir, grp, pid, "pass%d" % pas)
            os.makedirs(pdir, exist_ok=True)
            
            try:
                proc = subprocess.run(cmd, env=child_env, cwd=REPO,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      timeout=TIMEOUT_S)
                raw_rc = proc.returncode
                raw_stdout = proc.stdout
                raw_stderr = proc.stderr
            except subprocess.TimeoutExpired as exc:
                raw_rc = 124
                raw_stdout = exc.stdout or b""
                raw_stderr = exc.stderr or b""

            total_physical_calls += 1
            
            sig = None
            if raw_rc < 0:
                sig = -raw_rc
                run_rc = 128 + sig
            elif raw_rc >= 128:
                sig = raw_rc - 128
                run_rc = raw_rc
            else:
                sig = 0
                run_rc = raw_rc

            with open(os.path.join(pdir, "stdout.txt"), "wb") as fo:
                fo.write(raw_stdout)
            with open(os.path.join(pdir, "stderr.txt"), "wb") as fe:
                fe.write(raw_stderr)
            combined_txt = (raw_stdout + b"\n" + raw_stderr).decode("utf-8", errors="replace")
            with open(os.path.join(pdir, "run.out"), "w", encoding="utf-8") as fr:
                fr.write(combined_txt)

            f = J.facts_from_log(combined_txt)
            rc1 = f["rc1"]
            rc2 = f["rc2"]
            hit = f["hit"]

            cls, label, reason = J.classify(run_rc, rc1, rc2, hit,
                                            control=is_ctrl, real=real, inj_call=inj_call)

            v = evaluate_verdict(comp_contract, exp_cls, exp_rc1, exp_rc2, exp_run_rc, exp_hit,
                                 cls, rc1, rc2, run_rc, hit)
            
            pass_facts.append({
                "run_rc": run_rc, "signal": sig, "rc1": rc1, "rc2": rc2, "hit": hit,
                "class": cls, "reason": reason, "verdict": v
            })

        p1 = pass_facts[0]
        p2 = pass_facts[1]

        is_consistent = (p1["run_rc"] == p2["run_rc"] and
                         p1["rc1"] == p2["rc1"] and
                         p1["rc2"] == p2["rc2"] and
                         p1["hit"] == p2["hit"] and
                         p1["class"] == p2["class"])

        if not is_consistent:
            v_all = "FLAKY"
        elif p1["verdict"] == p2["verdict"]:
            v_all = p1["verdict"]
        else:
            v_all = "MISMATCH"

        results_data.append({
            "row_id": row_id, "group": grp, "point_id": pid, "tree": tree,
            "driver_name": dname, "env": env_str, "status": "COMPLETED",
            "p1_run_rc": str(p1["run_rc"]), "p1_signal": str(p1["signal"]),
            "p1_rc1": str(p1["rc1"]) if p1["rc1"] is not None else "none",
            "p1_rc2": str(p1["rc2"]) if p1["rc2"] is not None else "none",
            "p1_hit": str(p1["hit"]), "p1_class": p1["class"], "p1_reason": p1["reason"],
            "p2_run_rc": str(p2["run_rc"]), "p2_signal": str(p2["signal"]),
            "p2_rc1": str(p2["rc1"]) if p2["rc1"] is not None else "none",
            "p2_rc2": str(p2["rc2"]) if p2["rc2"] is not None else "none",
            "p2_hit": str(p2["hit"]), "p2_class": p2["class"], "p2_reason": p2["reason"],
            "pass_consistent": "YES" if is_consistent else "NO",
            "verdict_p1": p1["verdict"], "verdict_p2": p2["verdict"],
            "verdict_overall": v_all,
            "expected_class": exp_cls, "expected_rc1": exp_rc1, "expected_rc2": exp_rc2,
            "expected_run_rc": exp_run_rc, "expected_hit": exp_hit, "expected_label": exp_label,
            "comparison_contract": comp_contract, "expect_source": r["expect_source"],
            "callseq_status": r["callseq_status"], "k_source": r["k_source"]
        })

        if idx % 100 == 0 or idx == len(prereg_rows):
            print("  Progress: %d / %d rows complete (elapsed: %.1fs)" % (idx, len(prereg_rows), time.time() - t_start))

    elapsed = time.time() - t_start
    print("Execution complete. Total physical invocations: %d, time: %.1fs" % (total_physical_calls, elapsed))

    # 3. Write RESULTS_M1B_R8_M1b1.tsv
    print("Writing RESULTS_M1B_R8_M1b1.tsv...")
    res_path = os.path.join(ev_dir, "RESULTS_M1B_R8_M1b1.tsv")
    res_cols = [
        "row_id", "group", "point_id", "tree", "driver_name", "env", "status",
        "p1_run_rc", "p1_signal", "p1_rc1", "p1_rc2", "p1_hit", "p1_class", "p1_reason",
        "p2_run_rc", "p2_signal", "p2_rc1", "p2_rc2", "p2_hit", "p2_class", "p2_reason",
        "pass_consistent"
    ]
    with open(res_path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(res_cols) + "\n")
        for r in results_data:
            fh.write("\t".join(r[c] for c in res_cols) + "\n")

    # 4. Write VERDICT_M1B_R8_M1b1.tsv
    print("Writing VERDICT_M1B_R8_M1b1.tsv...")
    verd_path = os.path.join(ev_dir, "VERDICT_M1B_R8_M1b1.tsv")
    verd_cols = [
        "row_id", "group", "point_id", "tree", "comparison_contract", "expected_class",
        "expected_rc1", "expected_rc2", "expected_run_rc", "expected_hit",
        "actual_class_p1", "actual_rc1_p1", "actual_rc2_p1", "actual_run_rc_p1", "actual_hit_p1",
        "actual_class_p2", "actual_rc1_p2", "actual_rc2_p2", "actual_run_rc_p2", "actual_hit_p2",
        "verdict_p1", "verdict_p2", "verdict_overall", "p1_reason"
    ]
    with open(verd_path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(verd_cols) + "\n")
        for r in results_data:
            row_vals = [
                r["row_id"], r["group"], r["point_id"], r["tree"], r["comparison_contract"], r["expected_class"],
                r["expected_rc1"], r["expected_rc2"], r["expected_run_rc"], r["expected_hit"],
                r["p1_class"], r["p1_rc1"], r["p1_rc2"], r["p1_run_rc"], r["p1_hit"],
                r["p2_class"], r["p2_rc1"], r["p2_rc2"], r["p2_run_rc"], r["p2_hit"],
                r["verdict_p1"], r["verdict_p2"], r["verdict_overall"], r["p1_reason"]
            ]
            fh.write("\t".join(row_vals) + "\n")

    # 5. Write CONSISTENCY_M1B_R8_M1b1.tsv
    print("Writing CONSISTENCY_M1B_R8_M1b1.tsv...")
    cons_path = os.path.join(ev_dir, "CONSISTENCY_M1B_R8_M1b1.tsv")
    cons_cols = [
        "row_id", "group", "point_id", "tree", "pass_consistent",
        "p1_run_rc", "p2_run_rc", "p1_rc1", "p2_rc1", "p1_rc2", "p2_rc2",
        "p1_hit", "p2_hit", "p1_class", "p2_class"
    ]
    with open(cons_path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(cons_cols) + "\n")
        for r in results_data:
            row_vals = [
                r["row_id"], r["group"], r["point_id"], r["tree"], r["pass_consistent"],
                r["p1_run_rc"], r["p2_run_rc"], r["p1_rc1"], r["p2_rc1"],
                r["p1_rc2"], r["p2_rc2"], r["p1_hit"], r["p2_hit"],
                r["p1_class"], r["p2_class"]
            ]
            fh.write("\t".join(row_vals) + "\n")

    # 6. Pair F2 and F3 rows and write F2_F3_DIFF_M1B_R8_M1b1.tsv
    print("Writing F2_F3_DIFF_M1B_R8_M1b1.tsv...")
    paired_diffs = []
    diff_header = [
        "group", "base_point_id", "f2_point_id", "f3_point_id",
        "f2_class", "f3_class", "f2_rc1", "f3_rc1", "f2_rc2", "f3_rc2",
        "f2_run_rc", "f3_run_rc", "f2_hit", "f3_hit",
        "f2_verdict", "f3_verdict", "diff_category", "detail"
    ]

    for i in range(0, len(results_data), 2):
        r2 = results_data[i]
        r3 = results_data[i+1]
        assert r2["tree"] == "F2" and r3["tree"] == "F3", "Pair order mismatch at %d" % i
        assert r2["group"] == r3["group"], "Group mismatch at pair %d" % (i // 2)

        f2_pid = r2["point_id"]
        f3_pid = r3["point_id"]
        base_id = f2_pid.replace("-F2-", "-").replace("-F2", "")
        
        # Check diff
        same_facts = (r2["p1_class"] == r3["p1_class"] and
                      r2["p1_rc1"] == r3["p1_rc1"] and
                      r2["p1_rc2"] == r3["p1_rc2"] and
                      r2["p1_run_rc"] == r3["p1_run_rc"] and
                      r2["p1_hit"] == r3["p1_hit"])
        
        if same_facts:
            diff_cat = "IDENTICAL"
            detail = "F2 and F3 facts and class identical"
        else:
            # Check if expected fix divergence
            if r2["expected_class"] != r3["expected_class"]:
                diff_cat = "EXPECTED_FIX_DIVERGENCE"
                detail = "Expected fix divergence: F2 exp=%s, F3 exp=%s (actual F2=%s, F3=%s)" % (
                    r2["expected_class"], r3["expected_class"], r2["p1_class"], r3["p1_class"]
                )
            else:
                diff_cat = "UNEXPECTED_DIFF"
                detail = "Facts differ: F2(cls=%s,rc1=%s,rc=%s) vs F3(cls=%s,rc1=%s,rc=%s)" % (
                    r2["p1_class"], r2["p1_rc1"], r2["p1_run_rc"],
                    r3["p1_class"], r3["p1_rc1"], r3["p1_run_rc"]
                )

        paired_diffs.append([
            r2["group"], base_id, f2_pid, f3_pid,
            r2["p1_class"], r3["p1_class"], r2["p1_rc1"], r3["p1_rc1"],
            r2["p1_rc2"], r3["p1_rc2"], r2["p1_run_rc"], r3["p1_run_rc"],
            r2["p1_hit"], r3["p1_hit"], r2["verdict_overall"], r3["verdict_overall"],
            diff_cat, detail
        ])

    diff_path = os.path.join(ev_dir, "F2_F3_DIFF_M1B_R8_M1b1.tsv")
    with open(diff_path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(diff_header) + "\n")
        for row in paired_diffs:
            fh.write("\t".join(row) + "\n")

    # 7. Write COVERAGE_M1B_R8_M1b1.tsv
    print("Writing COVERAGE_M1B_R8_M1b1.tsv...")
    groups = [
        "G7", "G8", "4.2", "M1_CTRL", "G2b", "G3", "G4",
        "CTRL_SEAM", "G2c", "G2c_control", "G1", "G2a",
        "ADDITIONS_22", "POLY_33"
    ]
    cov_path = os.path.join(ev_dir, "COVERAGE_M1B_R8_M1b1.tsv")
    cov_cols = [
        "group", "total_rows", "f2_rows", "f3_rows", "completed_rows", "not_run_rows",
        "match_rows", "not_reached_rows", "mismatch_rows", "flaky_rows", "physical_calls"
    ]
    cov_rows = []
    for g in groups:
        g_rows = [r for r in results_data if r["group"] == g]
        tot = len(g_rows)
        f2_c = sum(1 for r in g_rows if r["tree"] == "F2")
        f3_c = sum(1 for r in g_rows if r["tree"] == "F3")
        comp = sum(1 for r in g_rows if r["status"] == "COMPLETED")
        nr = sum(1 for r in g_rows if r["status"] == "NOT_RUN")
        match_c = sum(1 for r in g_rows if r["verdict_overall"] in ("MATCH", "NOT_RUN_AS_EXPECTED"))
        nr_as_exp = sum(1 for r in g_rows if r["verdict_overall"] == "NOT_REACHED_AS_EXPECTED")
        mism = sum(1 for r in g_rows if r["verdict_overall"] == "MISMATCH")
        flk = sum(1 for r in g_rows if r["verdict_overall"] == "FLAKY")
        phys = comp * 2
        cov_rows.append([
            g, str(tot), str(f2_c), str(f3_c), str(comp), str(nr),
            str(match_c), str(nr_as_exp), str(mism), str(flk), str(phys)
        ])

    with open(cov_path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(cov_cols) + "\n")
        for row in cov_rows:
            fh.write("\t".join(row) + "\n")

    # 8. Write ANOMALIES_M1B_R8_M1b1.tsv
    print("Writing ANOMALIES_M1B_R8_M1b1.tsv...")
    anom_path = os.path.join(ev_dir, "ANOMALIES_M1B_R8_M1b1.tsv")
    anom_cols = ["item_type", "group", "point_id", "tree", "verdict", "facts", "notes"]
    anom_rows = []
    for r in results_data:
        v = r["verdict_overall"]
        if v in ("MISMATCH", "FLAKY"):
            facts_str = "p1(rc=%s,rc1=%s,rc2=%s,hit=%s,cls=%s) p2(rc=%s,rc1=%s,rc2=%s,hit=%s,cls=%s)" % (
                r["p1_run_rc"], r["p1_rc1"], r["p1_rc2"], r["p1_hit"], r["p1_class"],
                r["p2_run_rc"], r["p2_rc1"], r["p2_rc2"], r["p2_hit"], r["p2_class"]
            )
            anom_rows.append([
                "VERDICT_ANOMALY", r["group"], r["point_id"], r["tree"], v, facts_str, r["p1_reason"]
            ])

    with open(anom_path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(anom_cols) + "\n")
        for row in anom_rows:
            fh.write("\t".join(row) + "\n")

    # Summary print
    total_rows = len(results_data)
    completed_rows = sum(1 for r in results_data if r["status"] == "COMPLETED")
    not_run_rows = sum(1 for r in results_data if r["status"] == "NOT_RUN")
    total_match = sum(1 for r in results_data if r["verdict_overall"] == "MATCH")
    total_not_reached = sum(1 for r in results_data if r["verdict_overall"] == "NOT_REACHED_AS_EXPECTED")
    total_not_run_exp = sum(1 for r in results_data if r["verdict_overall"] == "NOT_RUN_AS_EXPECTED")
    total_mismatch = sum(1 for r in results_data if r["verdict_overall"] == "MISMATCH")
    total_flaky = sum(1 for r in results_data if r["verdict_overall"] == "FLAKY")

    print("\n=================== EXECUTION SUMMARY ===================")
    print("Total pre-registered rows: %d" % total_rows)
    print("  Completed rows:          %d" % completed_rows)
    print("  Not-run rows (G2c_ctrl): %d" % not_run_rows)
    print("Physical driver calls:     %d" % total_physical_calls)
    print("Verdicts:")
    print("  MATCH:                   %d" % total_match)
    print("  NOT_REACHED_AS_EXPECTED: %d" % total_not_reached)
    print("  NOT_RUN_AS_EXPECTED:     %d" % total_not_run_exp)
    print("  MISMATCH:                %d" % total_mismatch)
    print("  FLAKY:                   %d" % total_flaky)
    print("Anomalies logged:          %d" % len(anom_rows))
    print("=========================================================\n")

    return 0 if (total_mismatch == 0 and total_flaky == 0) else 1

if __name__ == "__main__":
    sys.exit(main())
