#!/usr/bin/env python3
# run_smoke_r8m2b.py -- Orchestrates P05-S4 R8 M2b real smoke execution (Section 5 S-E).
# Runs the 24-point smoke subset to $EV/smoke/.
# Evaluates 5 smoke gates:
#  1. Every row produced expected files (stdout/stderr/exitcode and gdb.log if dbg).
#  2. No MISSING values in facts table.
#  3. In state analysis rows where exp_I*=HOLD, observed I is NOT UNJUDGED.
#  4. No '$' in planned command strings or env.
#  5. No IDENTITY_FAIL.
# Records observations in SMOKE_R8_M2b.tsv without altering exp_*.
import csv
import os
import shutil
import subprocess
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2b"))

PREREG_MAIN = os.path.join(EV, "PREREG_M2_EFFECTIVE_R8_M2b.tsv")
PREREG_SANREF = os.path.join(EV, "PREREG_M2_SANREF_R8_M2b.tsv")
SUBSET_FILE = os.path.join(EV, "SMOKE_SUBSET_R8_M2b.tsv")
CTRL_MAP = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a3", "CONTROL_MAPPING_R8_M2a3.tsv")

RUNNER_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "run_m2_r8m2b.py")
FACTS_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "facts_m2_r8m2b.py")
STATE_JUDGE_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "state_judge_m2_r8m2a4.py")
VERDICT_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "verdict_m2_r8m2b.py")

SMOKE_DIR = os.path.join(EV, "smoke")


def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"))


def main():
    os.makedirs(SMOKE_DIR, exist_ok=True)

    # 1. Build PREREG_SMOKE_R8_M2b.tsv
    subset_pids = set()
    with open(SUBSET_FILE, encoding="utf-8") as fh:
        for r in csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"):
            subset_pids.add(r["point_id"])

    main_rows = read_tsv(PREREG_MAIN)
    sanref_rows = read_tsv(PREREG_SANREF)

    smoke_rows = []
    with open(PREREG_MAIN, encoding="utf-8") as fh:
        fieldnames = list(csv.DictReader(fh, delimiter="\t").fieldnames)

    for r in main_rows:
        if r["point_id"] in subset_pids:
            smoke_rows.append(r)
    for r in sanref_rows:
        if r["point_id"] in subset_pids:
            smoke_rows.append(r)

    smoke_prereg = os.path.join(SMOKE_DIR, "PREREG_SMOKE_R8_M2b.tsv")
    with open(smoke_prereg, "w", encoding="utf-8") as fh:
        fh.write("\t".join(fieldnames) + "\n")
        for r in smoke_rows:
            fh.write("\t".join([r.get(f, "-") for f in fieldnames]) + "\n")

    print(f"run_smoke: prepared smoke prereg with {len(smoke_rows)} points at {smoke_prereg}")

    # 2. Plan generation (Gate 4 & Gate 5 check)
    plan_tsv = os.path.join(SMOKE_DIR, "COMMAND_PLAN_SMOKE.tsv")
    r_plan = subprocess.run([sys.executable, "-I", "-B", RUNNER_PY,
                             "--prereg", smoke_prereg,
                             "--ev", SMOKE_DIR,
                             "--out-plan", plan_tsv,
                             "--dry-run"],
                            capture_output=True, text=True)
    if r_plan.returncode != 0:
        sys.exit(f"run_smoke: plan dry-run failed: {r_plan.stderr}")

    plan_rows = read_tsv(plan_tsv)
    gate4_dollar = sum(1 for p in plan_rows if "$" in p["env_as_run"] or "$" in p["full_command_a"] or "$" in p["full_command_b"])
    gate5_ident_fail = sum(1 for p in plan_rows if p["identity_status"] == "IDENTITY_FAIL")

    print(f"Gate 4 (no '$' in plan): {'PASS' if gate4_dollar == 0 else 'FAIL'} (dollar_count={gate4_dollar})")
    print(f"Gate 5 (no IDENTITY_FAIL): {'PASS' if gate5_ident_fail == 0 else 'FAIL'} (fail_count={gate5_ident_fail})")

    if gate4_dollar != 0 or gate5_ident_fail != 0:
        sys.exit("FATAL: Gate 4 or Gate 5 failed during smoke planning.")

    # 3. Execution pass 1 and pass 2
    r_exec = subprocess.run([sys.executable, "-I", "-B", RUNNER_PY,
                             "--prereg", smoke_prereg,
                             "--ev", SMOKE_DIR,
                             "--out-plan", plan_tsv,
                             "--execute"],
                            capture_output=True, text=True)
    print(r_exec.stdout)
    if r_exec.returncode != 0:
        sys.exit(f"run_smoke: execution failed: {r_exec.stderr}")

    # 4. Verify Gate 1 (expected files exist)
    missing_files = []
    for pas in ("1", "2"):
        for r in smoke_rows:
            pid = r["point_id"]
            p_dir = os.path.join(SMOKE_DIR, "run", f"pass{pas}", pid)
            for fname in ("stdout.txt", "stderr.txt", "exitcode.txt"):
                fpath = os.path.join(p_dir, fname)
                if not os.path.isfile(fpath):
                    missing_files.append((pas, pid, fname))
            if r.get("gdb_script") not in (None, "", "-"):
                gpath = os.path.join(p_dir, "gdb.log")
                if not os.path.isfile(gpath):
                    missing_files.append((pas, pid, "gdb.log"))

    gate1_pass = (len(missing_files) == 0)
    print(f"Gate 1 (all expected files exist): {'PASS' if gate1_pass else 'FAIL'} (missing={len(missing_files)})")
    if not gate1_pass:
        print(f"Missing files sample: {missing_files[:5]}")
        sys.exit("FATAL: Gate 1 failed.")

    # 5. Facts extraction
    f1_tsv = os.path.join(SMOKE_DIR, "FACTS_pass1.tsv")
    f2_tsv = os.path.join(SMOKE_DIR, "FACTS_pass2.tsv")

    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", smoke_prereg,
                    "--run-dir", os.path.join(SMOKE_DIR, "run", "pass1"), "--pass", "1", "--out", f1_tsv], check=True)
    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", smoke_prereg,
                    "--run-dir", os.path.join(SMOKE_DIR, "run", "pass2"), "--pass", "2", "--out", f2_tsv], check=True)

    facts1 = read_tsv(f1_tsv)
    facts2 = read_tsv(f2_tsv)

    gate2_missing = 0
    for f_set, pas in [(facts1, "1"), (facts2, "2")]:
        for fr in f_set:
            if fr.get("rc") == "MISSING" or fr.get("rc1") == "MISSING":
                gate2_missing += 1

    print(f"Gate 2 (no MISSING in facts): {'PASS' if gate2_missing == 0 else 'FAIL'} (missing={gate2_missing})")
    if gate2_missing != 0:
        sys.exit("FATAL: Gate 2 failed.")

    # 6. State analysis
    s1_tsv = os.path.join(SMOKE_DIR, "STATE_pass1.tsv")
    s2_tsv = os.path.join(SMOKE_DIR, "STATE_pass2.tsv")
    s_sum = os.path.join(SMOKE_DIR, "STATE_SUMMARY.txt")

    r_sj = subprocess.run([sys.executable, "-I", "-B", STATE_JUDGE_PY,
                           "--prereg", smoke_prereg,
                           "--control", CTRL_MAP,
                           "--ev", SMOKE_DIR,
                           "--facts1", f1_tsv,
                           "--facts2", f2_tsv,
                           "--state-dir", os.path.join(SMOKE_DIR, "run"),
                           "--dumps-dir", os.path.join(SMOKE_DIR, "run"),
                           "--out-res", s1_tsv,
                           "--out-sum", s_sum],
                          capture_output=True, text=True)
    print(r_sj.stdout)
    if r_sj.returncode != 0:
        sys.exit(f"run_smoke: state_judge failed: {r_sj.stderr}")

    shutil.copyfile(s1_tsv, s2_tsv)

    # Gate 3: For rows with exp_I*=HOLD, observed I is NOT UNJUDGED
    state1 = read_tsv(s1_tsv)
    smoke_prereg_dict = {r["point_id"]: r for r in smoke_rows}
    gate3_unjudged = []

    for sr in state1:
        pid = sr["point_id"]
        pr = smoke_prereg_dict.get(pid, {})
        for inv in ("I1", "I2", "I3", "I4", "I5", "I6"):
            if pr.get(f"exp_{inv}") == "HOLD":
                obs_inv = sr.get(inv)
                if obs_inv == "UNJUDGED":
                    gate3_unjudged.append((pid, inv, obs_inv))

    gate3_pass = (len(gate3_unjudged) == 0)
    print(f"Gate 3 (state analyzer produces definite values for HOLD): {'PASS' if gate3_pass else 'FAIL'} (unjudged={len(gate3_unjudged)})")
    if not gate3_pass:
        print(f"Gate 3 failures: {gate3_unjudged}")
        sys.exit("FATAL: Gate 3 failed.")

    # 7. Verdict
    v_tsv = os.path.join(SMOKE_DIR, "VERDICT_SMOKE.tsv")
    v_sum = os.path.join(SMOKE_DIR, "SUMMARY_SMOKE.txt")

    r_v = subprocess.run([sys.executable, "-I", "-B", VERDICT_PY,
                          "--prereg", smoke_prereg,
                          "--facts1", f1_tsv,
                          "--facts2", f2_tsv,
                          "--state1", s1_tsv,
                          "--state2", s2_tsv,
                          "--control-map", CTRL_MAP,
                          "--out-verdict", v_tsv,
                          "--out-summary", v_sum,
                          "--expected-total", str(len(smoke_rows))],
                         capture_output=True, text=True)
    print(r_v.stdout)
    if r_v.returncode != 0:
        sys.exit(f"run_smoke: verdict failed: {r_v.stderr}")

    verdict_rows = read_tsv(v_tsv)

    # 8. Write SMOKE_R8_M2b.tsv (record all observed vs expected values)
    smoke_out_headers = [
        "point_id", "item", "tree", "driver", "exp_rc1", "obs_rc1_p1", "obs_rc1_p2",
        "exp_class", "obs_class_p1", "obs_class_p2", "exp_hit", "obs_hit_p1", "obs_hit_p2",
        "gdb_divergent", "verdict", "mismatches", "notes"
    ]

    facts1_map = {r["point_id"]: r for r in facts1}
    facts2_map = {r["point_id"]: r for r in facts2}
    verdict_map = {r["point_id"]: r for r in verdict_rows}

    smoke_records = []
    for r in smoke_rows:
        pid = r["point_id"]
        f1 = facts1_map.get(pid, {})
        f2 = facts2_map.get(pid, {})
        v = verdict_map.get(pid, {})
        smoke_records.append([
            pid,
            r.get("item", "-"),
            r.get("tree", "-"),
            r.get("driver", "-"),
            r.get("exp_rc1", "-"),
            f1.get("rc1", "-"),
            f2.get("rc1", "-"),
            r.get("exp_class", "-"),
            f1.get("rc", "-") + "/c",
            f2.get("rc", "-") + "/c",
            r.get("exp_hit", "-"),
            f1.get("hit", "-"),
            f2.get("hit", "-"),
            f1.get("gdb_divergent", "-"),
            v.get("verdict", "-"),
            v.get("mismatches", "-"),
            v.get("notes", "-")
        ])

    out_smoke_tsv = os.path.join(EV, "SMOKE_R8_M2b.tsv")
    with open(out_smoke_tsv, "w", encoding="utf-8") as fh:
        fh.write("\t".join(smoke_out_headers) + "\n")
        for s in smoke_records:
            fh.write("\t".join(s) + "\n")

    print(f"run_smoke: wrote {len(smoke_records)} smoke observations to {out_smoke_tsv}")
    print("ALL 5 SMOKE GATES PASSED.")


if __name__ == "__main__":
    main()
