#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2e; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# run_formal_r8m2e.py -- P05-S4 R8 M2e formal two-pass execution (28 rows x 2 passes).
import csv, os, shutil, subprocess, sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2e")
EV = os.environ.get("EV", os.path.join(REPO, EV_REL))
FORMAL_DIR = os.path.join(EV, "formal")

PREREG_FORMAL = os.path.join(EV, "PREREG_EFFECTIVE_FORMAL_R8_M2e.tsv")
CTRL_MAP = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a3", "CONTROL_MAPPING_R8_M2a3.tsv")

RUNNER_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "run_m2_r8m2e.py")
FACTS_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "facts_m2_r8m2e.py")
STATE_JUDGE_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "state_judge_m2_r8m2e.py")
VERDICT_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "verdict_m2_r8m2e.py")

R8M2B_EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2b")
CONTROLS = ["M2-01-CTRL-01-F3", "M2-01-CTRL-02-F3", "M2-01-CTRL-03-F3", "M2-05-CTRL-P0-F3"]


def main():
    if os.path.exists(FORMAL_DIR) and os.listdir(FORMAL_DIR):
        sys.exit(f"REFUSED: Formal directory already exists and is non-empty (U17): {FORMAL_DIR}")
    os.makedirs(FORMAL_DIR, exist_ok=True)

    run_dir = os.path.join(FORMAL_DIR, "run")

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
    plan_tsv = os.path.join(FORMAL_DIR, "COMMAND_PLAN_FORMAL_R8_M2e.tsv")
    r_plan = subprocess.run([sys.executable, "-I", "-B", RUNNER_PY,
                             "--prereg", PREREG_FORMAL,
                             "--ev", FORMAL_DIR,
                             "--out-plan", plan_tsv,
                             "--dry-run"],
                            capture_output=True, text=True)
    if r_plan.returncode != 0:
        sys.exit(f"run_formal_r8m2e: plan dry-run failed:\n{r_plan.stderr}")
    print("Command plan dry-run completed successfully.")

    # 3. Execute pass 1 completely
    print("\nStarting execution of pass 1...")
    r_p1 = subprocess.run([sys.executable, "-I", "-B", RUNNER_PY,
                           "--prereg", PREREG_FORMAL,
                           "--ev", FORMAL_DIR,
                           "--out-plan", plan_tsv,
                           "--pass", "1",
                           "--execute"],
                          capture_output=True, text=True)
    print(r_p1.stdout)
    if r_p1.returncode != 0:
        sys.exit(f"run_formal_r8m2e: pass 1 execution failed:\n{r_p1.stderr}")
    print("Pass 1 execution completed.")

    # 4. Execute pass 2 completely
    print("\nStarting execution of pass 2...")
    r_p2 = subprocess.run([sys.executable, "-I", "-B", RUNNER_PY,
                           "--prereg", PREREG_FORMAL,
                           "--ev", FORMAL_DIR,
                           "--out-plan", plan_tsv,
                           "--pass", "2",
                           "--execute"],
                          capture_output=True, text=True)
    print(r_p2.stdout)
    if r_p2.returncode != 0:
        sys.exit(f"run_formal_r8m2e: pass 2 execution failed:\n{r_p2.stderr}")
    print("Pass 2 execution completed.")

    # 5. Extract facts
    print("\nExtracting facts for pass 1 and pass 2...")
    f1_tsv = os.path.join(FORMAL_DIR, "FACTS_pass1.tsv")
    f2_tsv = os.path.join(FORMAL_DIR, "FACTS_pass2.tsv")

    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", PREREG_FORMAL,
                    "--run-dir", os.path.join(run_dir, "pass1"), "--pass", "1", "--out", f1_tsv], check=True)
    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", PREREG_FORMAL,
                    "--run-dir", os.path.join(run_dir, "pass2"), "--pass", "2", "--out", f2_tsv], check=True)

    fieldnames = [
        "point_id", "pass", "tree", "rc", "signal", "rc1", "rc2", "rc3",
        "hit", "hit1", "hit2", "inject2_invalid", "inject2_suppressed", "san_reports",
        "san_crash", "init_clean", "gdb_divergent", "m210_hits",
        "crash_call", "crash_site", "post_call1_solution",
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
                    cr["crash_call"] = "NONE"
                    cr["crash_site"] = "-"
                    cr["post_call1_solution"] = "-"
                    writer.writerow({k: cr.get(k, "-") for k in fieldnames})

    # 6. State analysis
    print("\nRunning state analysis...")
    s1_tsv = os.path.join(FORMAL_DIR, "STATE_pass1.tsv")
    s2_tsv = os.path.join(FORMAL_DIR, "STATE_pass2.tsv")
    s_sum = os.path.join(FORMAL_DIR, "STATE_SUMMARY_R8_M2e.txt")

    r_sj = subprocess.run([sys.executable, "-I", "-B", STATE_JUDGE_PY,
                           "--prereg", PREREG_FORMAL,
                           "--control", CTRL_MAP,
                           "--ev", FORMAL_DIR,
                           "--facts1", f1_tsv,
                           "--facts2", f2_tsv,
                           "--state-dir", run_dir,
                           "--dumps-dir", run_dir,
                           "--out-res", s1_tsv,
                           "--out-sum", s_sum],
                          capture_output=True, text=True)
    print(r_sj.stdout)
    if r_sj.returncode != 0:
        sys.exit(f"run_formal_r8m2e: state_judge failed:\n{r_sj.stderr}")

    shutil.copyfile(s1_tsv, s2_tsv)

    # 7. Verdict v6
    print("\nRunning verdict engine v6...")
    v_tsv = os.path.join(FORMAL_DIR, "VERDICT_R8_M2e.tsv")
    v_sum = os.path.join(FORMAL_DIR, "SUMMARY_R8_M2e.txt")

    r_v = subprocess.run([sys.executable, "-I", "-B", VERDICT_PY,
                          "--prereg", PREREG_FORMAL,
                          "--facts1", f1_tsv,
                          "--facts2", f2_tsv,
                          "--state1", s1_tsv,
                          "--state2", s2_tsv,
                          "--control-map", CTRL_MAP,
                          "--out-verdict", v_tsv,
                          "--out-summary", v_sum,
                          "--assert-total", "28"],
                         capture_output=True, text=True)
    print(r_v.stdout)
    if r_v.returncode != 0:
        sys.exit(f"run_formal_r8m2e: verdict failed:\n{r_v.stderr}")

    # 8. Check FLAKY and GDB_DIVERGENT
    with open(v_tsv, encoding="utf-8") as fh:
        v_rows = list(csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"))

    n_flaky = sum(1 for r in v_rows if r["verdict"] == "FLAKY")
    n_gdb_div = sum(1 for r in v_rows if r["verdict"] == "GDB_DIVERGENT")
    n_match = sum(1 for r in v_rows if r["verdict"] == "MATCH")
    n_mismatch = sum(1 for r in v_rows if r["verdict"] == "MISMATCH")

    print(f"\nFormal Run Summary: MATCH={n_match}, MISMATCH={n_mismatch}, FLAKY={n_flaky}, GDB_DIVERGENT={n_gdb_div}")

    if n_flaky > 0:
        sys.stderr.write(f"HARD STOP: FLAKY rows observed in formal run ({n_flaky})\n")
        return 2
    if n_gdb_div > 0:
        sys.stderr.write(f"HARD STOP: GDB_DIVERGENT rows observed in formal run ({n_gdb_div})\n")
        return 2

    print("\nrun_formal_r8m2e: FORMAL TWO-PASS RUN AND VERDICT COMPLETED SUCCESSFULLY.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
