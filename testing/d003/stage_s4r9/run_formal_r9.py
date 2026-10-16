#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# run_formal_r9.py -- Formal two-pass execution of 191 points (Section 4 S-L).
import csv, hashlib, os, shutil, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2"))
os.makedirs(EV, exist_ok=True)

FORMAL_DIR = os.path.join(EV, "formal")
RUN_DIR = os.path.join(FORMAL_DIR, "run")
os.makedirs(RUN_DIR, exist_ok=True)

M0_EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m0")
PREREG_SOLN = os.path.join(M0_EV, "PREREG_SOLN_F4_R9.tsv")
PREREG_REGRESS = os.path.join(M0_EV, "PREREG_REGRESS_F4_R9.tsv")
BLD_TSV = os.path.join(M0_EV, "BUILD_R9.tsv")
CTRL_MAP = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a3", "CONTROL_MAPPING_R8_M2a3.tsv")

FACTS_PY = os.path.join(REPO, "testing", "d003", "stage_s4r9", "facts_m2_r9.py")
STATE_JUDGE_PY = os.path.join(REPO, "testing", "d003", "stage_s4r9", "state_judge_m2_r9.py")
VERDICT_PY = os.path.join(REPO, "testing", "d003", "stage_s4r9", "verdict_m2_r9.py")

OUT_FACTS1 = os.path.join(EV, "FACTS_pass1_R9.tsv")
OUT_FACTS2 = os.path.join(EV, "FACTS_pass2_R9.tsv")
OUT_STATE1 = os.path.join(EV, "STATE_pass1_R9.tsv")
OUT_STATE2 = os.path.join(EV, "STATE_pass2_R9.tsv")
OUT_STATE_RES = os.path.join(EV, "RESULTS_STATE_R9.tsv")
OUT_STATE_SUM = os.path.join(EV, "STATE_SUMMARY_R9.txt")
OUT_VERDICT = os.path.join(EV, "VERDICT_R9.tsv")
OUT_SUMMARY = os.path.join(EV, "SUMMARY_R9.txt")

# 1. Load driver executables
bld_artifacts = {}
with open(BLD_TSV, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        bld_artifacts[parts[0]] = os.path.join(REPO, parts[1])

# 2. Combine 18 SOLN + 173 Regression points into 191 running points
with open(PREREG_SOLN, encoding="utf-8") as fh:
    soln_rows = list(csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"))

with open(PREREG_REGRESS, encoding="utf-8") as fh:
    regress_rows = list(csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"))

all_191_points = soln_rows + regress_rows
if len(all_191_points) != 191:
    raise AssertionError(f"Expected 191 points, got {len(all_191_points)}")

prereg_191_path = os.path.join(FORMAL_DIR, "PREREG_RUN_191_R9.tsv")
fieldnames = list(all_191_points[0].keys())
with open(prereg_191_path, "w", encoding="utf-8", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
    fh.write("# PREREG_RUN_191_R9.tsv -- Combined formal preregistration table for 191 points\n")
    writer.writeheader()
    for r in all_191_points:
        writer.writerow(r)

print(f"Loaded {len(soln_rows)} SOLN + {len(regress_rows)} Regression = {len(all_191_points)} points.")

# 3. Execute 191 points x 2 passes
total_runs = len(all_191_points) * 2
run_count = 0

for p in (1, 2):
    p_pass_dir = os.path.join(RUN_DIR, f"pass{p}")
    os.makedirs(p_pass_dir, exist_ok=True)
    print(f"--- Starting Pass {p} ({len(all_191_points)} points) ---")

    for idx, r in enumerate(all_191_points, 1):
        run_count += 1
        pid = r["point_id"]
        drv_name = r["driver"]
        drv_path = bld_artifacts[drv_name]
        gdb = r.get("gdb_script", "-")
        argv = r["argv"]
        env_raw = r["env"]

        p_dir = os.path.join(p_pass_dir, pid)
        os.makedirs(p_dir, exist_ok=True)

        stdout_path = os.path.join(p_dir, "stdout.txt")
        stderr_path = os.path.join(p_dir, "stderr.txt")
        exitcode_path = os.path.join(p_dir, "exitcode.txt")
        gdb_log_path = os.path.join(p_dir, "gdb.log")
        asan_log_prefix = os.path.join(p_dir, "asan.log")
        ubsan_log_prefix = os.path.join(p_dir, "ubsan.log")

        # Environment
        env = os.environ.copy()
        for k in list(env.keys()):
            if k.startswith("FMM_") or k.startswith("S4FMM_") or k.startswith("ASAN_") or k.startswith("UBSAN_") or k.startswith("S4_FAIL_ALLOC_"):
                del env[k]

        if "-san" in drv_name:
            env["ASAN_OPTIONS"] = f"detect_leaks=0:abort_on_error=0:log_path={asan_log_prefix}"
            env["UBSAN_OPTIONS"] = f"abort_on_error=0:log_path={ubsan_log_prefix}"

        for pair in env_raw.split(";"):
            if pair.strip():
                k, v = pair.strip().split("=", 1)
                env[k] = v

        env["S4FMM_DUMP_DIR"] = p_dir

        # Run A (gdb)
        if gdb != "-":
            gdb_script_path = os.path.join(REPO, gdb) if not os.path.isabs(gdb) else gdb
            gdb_cmd = ["gdb", "-batch", "-x", gdb_script_path, "--args", drv_path] + argv.split()
            r_gdb = subprocess.run(gdb_cmd, env=env, cwd=REPO, capture_output=True, text=True, timeout=600)
            with open(gdb_log_path, "w", encoding="utf-8") as fh:
                fh.write(r_gdb.stdout + "\n" + r_gdb.stderr)

        # Run B (nogdb)
        cmd_b = [drv_path] + argv.split()
        r_b = subprocess.run(cmd_b, env=env, cwd=REPO, capture_output=True, text=True, timeout=600)
        with open(stdout_path, "w", encoding="utf-8") as fh:
            fh.write(r_b.stdout)
        with open(stderr_path, "w", encoding="utf-8") as fh:
            fh.write(r_b.stderr)
        with open(exitcode_path, "w", encoding="utf-8") as fh:
            fh.write(f"{r_b.returncode}\n")

        if idx % 25 == 0 or idx == len(all_191_points):
            print(f"  [Pass {p}] {idx}/{len(all_191_points)} points complete (last: {pid}, rc={r_b.returncode})")

print("All 382 runs completed.")

# 4. Extract facts pass 1 & 2
print("--- Extracting facts ---")
subprocess.run([
    sys.executable, "-I", "-B", FACTS_PY,
    "--prereg", prereg_191_path,
    "--run-dir", os.path.join(RUN_DIR, "pass1"),
    "--pass", "1",
    "--out", OUT_FACTS1
], check=True)

subprocess.run([
    sys.executable, "-I", "-B", FACTS_PY,
    "--prereg", prereg_191_path,
    "--run-dir", os.path.join(RUN_DIR, "pass2"),
    "--pass", "2",
    "--out", OUT_FACTS2
], check=True)

# 5. State judge
print("--- Running state judge ---")
subprocess.run([
    sys.executable, "-I", "-B", STATE_JUDGE_PY,
    "--prereg", prereg_191_path,
    "--control", CTRL_MAP,
    "--ev", EV,
    "--facts1", OUT_FACTS1,
    "--facts2", OUT_FACTS2,
    "--out-res", OUT_STATE_RES,
    "--out-sum", OUT_STATE_SUM,
    "--dumps-dir", RUN_DIR,
    "--state-dir", RUN_DIR
], check=True)

# Split RESULTS_STATE_R9.tsv into STATE_pass1_R9.tsv and STATE_pass2_R9.tsv
with open(OUT_STATE_RES, encoding="utf-8") as fh:
    res_lines = [l for l in fh if not l.startswith("#")]

state_header = res_lines[0]
state1_lines = [state_header]
state2_lines = [state_header]

col_map = {name: i for i, name in enumerate(state_header.strip().split("\t"))}
pass_idx = col_map["pass"]

for l in res_lines[1:]:
    parts = l.strip().split("\t")
    if parts[pass_idx] == "1":
        state1_lines.append(l)
    elif parts[pass_idx] == "2":
        state2_lines.append(l)

with open(OUT_STATE1, "w", encoding="utf-8") as fh:
    fh.write(f"# STATE_pass1_R9.tsv -- P05-S4 R9 state evaluation pass 1\n")
    fh.writelines(state1_lines)

with open(OUT_STATE2, "w", encoding="utf-8") as fh:
    fh.write(f"# STATE_pass2_R9.tsv -- P05-S4 R9 state evaluation pass 2\n")
    fh.writelines(state2_lines)

print(f"Wrote {OUT_STATE1} ({len(state1_lines)-1} rows) and {OUT_STATE2} ({len(state2_lines)-1} rows)")

# 6. Verdict
print("--- Running verdict engine ---")
subprocess.run([
    sys.executable, "-I", "-B", VERDICT_PY,
    "--prereg", prereg_191_path,
    "--facts1", OUT_FACTS1,
    "--facts2", OUT_FACTS2,
    "--state1", OUT_STATE1,
    "--state2", OUT_STATE2,
    "--out-verdict", OUT_VERDICT,
    "--out-summary", OUT_SUMMARY,
    "--control-map", CTRL_MAP,
    "--assert-total", "191"
], check=True)

print(f"Formal two-pass verdict written to {OUT_VERDICT}")
print(f"Summary written to {OUT_SUMMARY}")
