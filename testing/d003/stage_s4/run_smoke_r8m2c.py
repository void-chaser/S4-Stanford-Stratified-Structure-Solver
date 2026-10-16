#!/usr/bin/env python3
# run_smoke_r8m2c.py -- Orchestrates P05-S4 R8 M2c real smoke execution.
# Runs all 54 delta points to $EV/smoke/.
# Evaluates 7 smoke gates via smoke_gate_r8m2c.py.
import csv, os, shutil, subprocess, sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2c")
EV = os.environ.get("EV", os.path.join(REPO, EV_REL))
SMOKE_DIR = os.path.join(EV, "smoke")

DELTA_PREREG = os.path.join(EV, "PREREG_M2_DELTA_R8_M2c.tsv")
TRIAGE_TSV = os.path.join(EV, "TRIAGE_R8_M2c.tsv")
CTRL_MAP = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a3", "CONTROL_MAPPING_R8_M2a3.tsv")

RUNNER_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "run_m2_r8m2c.py")
FACTS_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "facts_m2_r8m2c.py")
STATE_JUDGE_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "state_judge_m2_r8m2c.py")
VERDICT_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "verdict_m2_r8m2c.py")
SMOKE_GATE_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "smoke_gate_r8m2c.py")

R8M2B_EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2b")
CONTROLS = ["M2-01-CTRL-01-F3", "M2-01-CTRL-02-F3", "M2-01-CTRL-03-F3", "M2-05-CTRL-P0-F3"]

def main():
    os.makedirs(SMOKE_DIR, exist_ok=True)

    # 1. Populate historical controls into smoke/run/pass<n>
    for pas in ("1", "2"):
        pas_dir = os.path.join(SMOKE_DIR, "run", f"pass{pas}")
        os.makedirs(pas_dir, exist_ok=True)
        for cid in CONTROLS:
            src_c = os.path.join(R8M2B_EV, "run", f"pass{pas}", cid)
            dst_c = os.path.join(pas_dir, cid)
            if os.path.isdir(src_c) and not os.path.exists(dst_c):
                shutil.copytree(src_c, dst_c)

    # 2. Plan generation (Gate 4 & Gate 5 check)
    plan_tsv = os.path.join(SMOKE_DIR, "COMMAND_PLAN_SMOKE.tsv")
    r_plan = subprocess.run([sys.executable, "-I", "-B", RUNNER_PY,
                             "--prereg", DELTA_PREREG,
                             "--ev", SMOKE_DIR,
                             "--out-plan", plan_tsv,
                             "--dry-run"],
                            capture_output=True, text=True)
    if r_plan.returncode != 0:
        sys.exit(f"run_smoke_r8m2c: plan dry-run failed:\n{r_plan.stderr}")

    # 3. Execution pass 1 and pass 2
    r_exec = subprocess.run([sys.executable, "-I", "-B", RUNNER_PY,
                             "--prereg", DELTA_PREREG,
                             "--ev", SMOKE_DIR,
                             "--out-plan", plan_tsv,
                             "--execute"],
                            capture_output=True, text=True)
    print(r_exec.stdout)
    if r_exec.returncode != 0:
        sys.exit(f"run_smoke_r8m2c: execution failed:\n{r_exec.stderr}")

    # 4. Facts extraction
    f1_tsv = os.path.join(SMOKE_DIR, "FACTS_pass1.tsv")
    f2_tsv = os.path.join(SMOKE_DIR, "FACTS_pass2.tsv")

    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", DELTA_PREREG,
                    "--run-dir", os.path.join(SMOKE_DIR, "run", "pass1"), "--pass", "1", "--out", f1_tsv], check=True)
    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", DELTA_PREREG,
                    "--run-dir", os.path.join(SMOKE_DIR, "run", "pass2"), "--pass", "2", "--out", f2_tsv], check=True)

    # Append control facts from r8m2b to smoke facts so I6 and state judge can resolve controls
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

    # 5. State analysis
    s1_tsv = os.path.join(SMOKE_DIR, "STATE_pass1.tsv")
    s2_tsv = os.path.join(SMOKE_DIR, "STATE_pass2.tsv")
    s_sum = os.path.join(SMOKE_DIR, "STATE_SUMMARY.txt")

    r_sj = subprocess.run([sys.executable, "-I", "-B", STATE_JUDGE_PY,
                           "--prereg", DELTA_PREREG,
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
        sys.exit(f"run_smoke_r8m2c: state_judge failed:\n{r_sj.stderr}")

    shutil.copyfile(s1_tsv, s2_tsv)

    # 6. Verdict v4
    v_tsv = os.path.join(SMOKE_DIR, "VERDICT_SMOKE.tsv")
    v_sum = os.path.join(SMOKE_DIR, "SUMMARY_SMOKE.txt")

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
        sys.exit(f"run_smoke_r8m2c: verdict failed:\n{r_v.stderr}")

    # 7. Smoke gate v2
    r_gate = subprocess.run([sys.executable, "-I", "-B", SMOKE_GATE_PY,
                             "--prereg", DELTA_PREREG,
                             "--smoke-dir", SMOKE_DIR,
                             "--triage", TRIAGE_TSV],
                            capture_output=True, text=True)
    print(r_gate.stdout)
    if r_gate.returncode != 0:
        sys.exit(f"run_smoke_r8m2c: smoke gate v2 FAILED with exit code {r_gate.returncode}")

    print("run_smoke_r8m2c: SMOKE GATE V2 ALL PASSED.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
