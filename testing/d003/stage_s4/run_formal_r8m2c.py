#!/usr/bin/env python3
# run_formal_r8m2c.py -- P05-S4 R8 M2c formal two-pass execution.
# Executes pass 1 completely, then pass 2 completely.
# Refuses to run if output directories exist and are non-empty.
import csv, os, shutil, subprocess, sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2c")
EV = os.environ.get("EV", os.path.join(REPO, EV_REL))

DELTA_PREREG = os.path.join(EV, "PREREG_M2_DELTA_R8_M2c.tsv")
CTRL_MAP = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a3", "CONTROL_MAPPING_R8_M2a3.tsv")

RUNNER_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "run_m2_r8m2c.py")
FACTS_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "facts_m2_r8m2c.py")
STATE_JUDGE_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "state_judge_m2_r8m2c.py")
VERDICT_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "verdict_m2_r8m2c.py")

R8M2B_EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2b")
CONTROLS = ["M2-01-CTRL-01-F3", "M2-01-CTRL-02-F3", "M2-01-CTRL-03-F3", "M2-05-CTRL-P0-F3"]

def main():
    run_dir = os.path.join(EV, "run")
    if os.path.exists(run_dir) and os.listdir(run_dir):
        sys.exit(f"REFUSED: Formal run directory already exists and is non-empty (U17): {run_dir}")

    # 1. Populate historical controls into run/pass1 and run/pass2
    for pas in ("1", "2"):
        pas_dir = os.path.join(run_dir, f"pass{pas}")
        os.makedirs(pas_dir, exist_ok=True)
        for cid in CONTROLS:
            src_c = os.path.join(R8M2B_EV, "run", f"pass{pas}", cid)
            dst_c = os.path.join(pas_dir, cid)
            if os.path.isdir(src_c) and not os.path.exists(dst_c):
                shutil.copytree(src_c, dst_c)

    # 2. Plan generation (full plan across both passes)
    plan_tsv = os.path.join(EV, "COMMAND_PLAN_R8_M2c.tsv")
    r_plan = subprocess.run([sys.executable, "-I", "-B", RUNNER_PY,
                             "--prereg", DELTA_PREREG,
                             "--ev", EV,
                             "--out-plan", plan_tsv,
                             "--dry-run"],
                            capture_output=True, text=True)
    if r_plan.returncode != 0:
        sys.exit(f"run_formal_r8m2c: plan dry-run failed:\n{r_plan.stderr}")
    print("Command plan dry-run completed successfully.")

    # 3. Execute pass 1 completely
    print("\nStarting execution of pass 1...")
    r_p1 = subprocess.run([sys.executable, "-I", "-B", RUNNER_PY,
                           "--prereg", DELTA_PREREG,
                           "--ev", EV,
                           "--out-plan", plan_tsv,
                           "--pass", "1",
                           "--execute"],
                          capture_output=True, text=True)
    print(r_p1.stdout)
    if r_p1.returncode != 0:
        sys.exit(f"run_formal_r8m2c: pass 1 execution failed:\n{r_p1.stderr}")
    print("Pass 1 execution completed.")

    # 4. Execute pass 2 completely
    print("\nStarting execution of pass 2...")
    r_p2 = subprocess.run([sys.executable, "-I", "-B", RUNNER_PY,
                           "--prereg", DELTA_PREREG,
                           "--ev", EV,
                           "--out-plan", plan_tsv,
                           "--pass", "2",
                           "--execute"],
                          capture_output=True, text=True)
    print(r_p2.stdout)
    if r_p2.returncode != 0:
        sys.exit(f"run_formal_r8m2c: pass 2 execution failed:\n{r_p2.stderr}")
    print("Pass 2 execution completed.")

    # 5. Extract facts
    print("\nExtracting facts for pass 1 and pass 2...")
    f1_tsv = os.path.join(EV, "FACTS_R8_M2c_pass1.tsv")
    f2_tsv = os.path.join(EV, "FACTS_R8_M2c_pass2.tsv")

    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", DELTA_PREREG,
                    "--run-dir", os.path.join(run_dir, "pass1"), "--pass", "1", "--out", f1_tsv], check=True)
    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", DELTA_PREREG,
                    "--run-dir", os.path.join(run_dir, "pass2"), "--pass", "2", "--out", f2_tsv], check=True)

    # Append control facts from r8m2b
    fieldnames = [
        "point_id", "pass", "tree", "rc", "signal", "rc1", "rc2", "rc3",
        "hit", "hit1", "hit2", "inject2_invalid", "inject2_suppressed", "san_reports",
        "san_crash", "init_clean",
        "gdb_divergent", "m210_hits",
        "call1_sha256", "call2_sha256", "call3_sha256",
        "call1_nonfinite", "call2_nonfinite", "call3_nonfinite",
        "status", "notes"
    ]
    for p_num, ft in [("1", f1_tsv), ("2", f2_tsv)]:
        r8m2b_f = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2b", f"FACTS_R8_M2b_pass{p_num}.tsv")
        if os.path.isfile(r8m2b_f):
            with open(r8m2b_f, encoding="utf-8") as fh:
                c_rows = [r for r in csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t") if r["point_id"] in CONTROLS]
            with open(ft, "a", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
                for cr in c_rows:
                    cr["san_crash"] = "-"
                    cr["init_clean"] = "-"
                    writer.writerow({k: cr.get(k, "-") for k in fieldnames})

    # 6. State analysis
    print("\nRunning state analysis...")
    s1_tsv = os.path.join(EV, "STATE_R8_M2c_pass1.tsv")
    s2_tsv = os.path.join(EV, "STATE_R8_M2c_pass2.tsv")
    s_sum = os.path.join(EV, "STATE_SUMMARY_R8_M2c.txt")

    r_sj = subprocess.run([sys.executable, "-I", "-B", STATE_JUDGE_PY,
                           "--prereg", DELTA_PREREG,
                           "--control", CTRL_MAP,
                           "--ev", EV,
                           "--facts1", f1_tsv,
                           "--facts2", f2_tsv,
                           "--state-dir", run_dir,
                           "--dumps-dir", run_dir,
                           "--out-res", s1_tsv,
                           "--out-sum", s_sum],
                          capture_output=True, text=True)
    print(r_sj.stdout)
    if r_sj.returncode != 0:
        sys.exit(f"run_formal_r8m2c: state_judge failed:\n{r_sj.stderr}")

    shutil.copyfile(s1_tsv, s2_tsv)

    # 7. Verdict v4
    print("\nRunning verdict engine v4...")
    v_tsv = os.path.join(EV, "VERDICT_R8_M2c.tsv")
    v_sum = os.path.join(EV, "SUMMARY_R8_M2c.txt")

    r_v = subprocess.run([sys.executable, "-I", "-B", VERDICT_PY,
                          "--prereg", DELTA_PREREG,
                          "--facts1", f1_tsv,
                          "--facts2", f2_tsv,
                          "--state1", s1_tsv,
                          "--state2", s2_tsv,
                          "--control-map", CTRL_MAP,
                          "--out-verdict", v_tsv,
                          "--out-summary", v_sum,
                          "--assert-total", "54"],
                         capture_output=True, text=True)
    print(r_v.stdout)
    if r_v.returncode != 0:
        sys.exit(f"run_formal_r8m2c: verdict failed:\n{r_v.stderr}")

    print("\nrun_formal_r8m2c: FORMAL TWO-PASS RUN AND VERDICT COMPLETED SUCCESSFULLY.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
