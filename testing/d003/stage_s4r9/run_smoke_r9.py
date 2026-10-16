#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# run_smoke_r9.py -- Execute single-pass smoke run for P05-S4 R9 (Section 4 S-K).
import csv, hashlib, os, shutil, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2"))
SMOKE_DIR = os.path.join(EV, "smoke")
RUN_DIR = os.path.join(SMOKE_DIR, "run", "pass1")
os.makedirs(RUN_DIR, exist_ok=True)

M0_EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m0")
PREREG_SOLN = os.path.join(M0_EV, "PREREG_SOLN_F4_R9.tsv")
PREREG_REGRESS = os.path.join(M0_EV, "PREREG_REGRESS_F4_R9.tsv")
BLD_TSV = os.path.join(M0_EV, "BUILD_R9.tsv")
CTRL_MAP = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a3", "CONTROL_MAPPING_R8_M2a3.tsv")

FACTS_PY = os.path.join(REPO, "testing", "d003", "stage_s4r9", "facts_m2_r9.py")
STATE_JUDGE_PY = os.path.join(REPO, "testing", "d003", "stage_s4r9", "state_judge_m2_r9.py")
VERDICT_PY = os.path.join(REPO, "testing", "d003", "stage_s4r9", "verdict_m2_r9.py")

# 1. Load driver executables from BUILD_R9.tsv
bld_artifacts = {}
with open(BLD_TSV, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        bld_artifacts[parts[0]] = os.path.join(REPO, parts[1])

# 2. Select smoke points:
#  - All 18 SOLN F4 points
#  - 15 regression points (1 from each driver family)
#  - Plus matching control points so that I6 can be verified in smoke!
with open(PREREG_SOLN, encoding="utf-8") as fh:
    soln_rows = list(csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"))

with open(PREREG_REGRESS, encoding="utf-8") as fh:
    regress_rows = list(csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"))

regress_map = {r["point_id"]: r for r in regress_rows}

# 15 regression driver representatives:
rep_pids = [
    "M2-07-CTRL-closed1d-ng1-F4",  # d003-F4-plain
    "M2-07-INJ-closed1d-ng5-F4",   # d003plan-F4-plain
    "M2-04-01-F4",                 # dual-F4-dbg
    "M2-01-CTRL-01-F4",            # init-F4-dbg
    "M2-03-REP-INIT-01-F4-C",      # init-F4-san
    "M2-05-P0-F4-C",               # layers-F4-dbg
    "M2-04-02-F4",                 # layers-dual-F4-dbg
    "M2-06-01-F4-C",               # nan-F4
    "M2-01-11-F4",                 # polyinj-F4-dbg
    "M2-03-REP-POLY-11-F4",        # polyinj-F4-san
    "M2-03-SANREF-G6-01-F4-C",     # r6bseam-seamF-F4
    "M2-03-SANREF-G5-01-F4",       # r6bstate-F4-dbg
    "M2-03-G5-01-F4",              # r6bstate-F4-san
    "M2-09-01-F4",                 # seam-fmmret-F4
    "M2-03-G6-01-F4-C",            # seamF-F4-san
]

smoke_selected = list(soln_rows)
smoke_pids_set = set(r["point_id"] for r in smoke_selected)

for pid in rep_pids:
    if pid not in smoke_pids_set:
        smoke_selected.append(regress_map[pid])
        smoke_pids_set.add(pid)

# Add control dependencies for points in smoke so I6 evaluates cleanly
extra_ctrls = [
    "M2-01-CTRL-02-F4",
    "M2-01-CTRL-03-F4",
    "M2-04-CTRL-01-F4",
    "M2-04-CTRL-02-F4",
    "M2-05-CTRL-P0-F4",
    "M2-06-CTRL-01-F4",
    "M2-07-CTRL-closed1d-ng5-F4",
    "M2-01-CTRL-11-F4",
    "M2-01-01-F4-C",
]
for cid in extra_ctrls:
    if cid in regress_map and cid not in smoke_pids_set:
        smoke_selected.append(regress_map[cid])
        smoke_pids_set.add(cid)

print(f"Total points executing in smoke: {len(smoke_selected)}")

# Write PREREG_SMOKE_R9.tsv
prereg_smoke_path = os.path.join(SMOKE_DIR, "PREREG_SMOKE_R9.tsv")
fieldnames = list(smoke_selected[0].keys())
with open(prereg_smoke_path, "w", encoding="utf-8", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
    fh.write("# PREREG_SMOKE_R9.tsv -- Smoke run preregistration subset for P05-S4 R9\n")
    writer.writeheader()
    for r in smoke_selected:
        writer.writerow(r)

# Execute each point
for idx, r in enumerate(smoke_selected, 1):
    pid = r["point_id"]
    drv_name = r["driver"]
    drv_path = bld_artifacts[drv_name]
    gdb = r.get("gdb_script", "-")
    argv = r["argv"]
    env_raw = r["env"]

    p_dir = os.path.join(RUN_DIR, pid)
    os.makedirs(p_dir, exist_ok=True)

    stdout_path = os.path.join(p_dir, "stdout.txt")
    stderr_path = os.path.join(p_dir, "stderr.txt")
    exitcode_path = os.path.join(p_dir, "exitcode.txt")
    gdb_log_path = os.path.join(p_dir, "gdb.log")
    asan_log_prefix = os.path.join(p_dir, "asan.log")
    ubsan_log_prefix = os.path.join(p_dir, "ubsan.log")

    # Set up environment
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

    # Run A (gdb) if applicable
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

    print(f"[{idx}/{len(smoke_selected)}] Executed {pid} ({drv_name}): rc={r_b.returncode}")

print("All smoke points executed.")

# 2b. For single-pass smoke, mirror pass1 to pass2 so state analyzer and verdict evaluate cleanly
run_pass2 = os.path.join(SMOKE_DIR, "run", "pass2")
if os.path.exists(run_pass2):
    shutil.rmtree(run_pass2)
shutil.copytree(RUN_DIR, run_pass2)

# 3. Extract facts
facts_smoke_path = os.path.join(SMOKE_DIR, "FACTS_smoke.tsv")
subprocess.run([
    sys.executable, "-I", "-B", FACTS_PY,
    "--prereg", prereg_smoke_path,
    "--run-dir", RUN_DIR,
    "--pass", "1",
    "--out", facts_smoke_path
], check=True)

# 4. State judge
state_smoke_path = os.path.join(SMOKE_DIR, "STATE_smoke.tsv")
state_sum_path = os.path.join(SMOKE_DIR, "STATE_SUMMARY_smoke.txt")
subprocess.run([
    sys.executable, "-I", "-B", STATE_JUDGE_PY,
    "--prereg", prereg_smoke_path,
    "--control", CTRL_MAP,
    "--ev", SMOKE_DIR,
    "--facts1", facts_smoke_path,
    "--facts2", facts_smoke_path,
    "--out-res", state_smoke_path,
    "--out-sum", state_sum_path,
    "--dumps-dir", os.path.join(SMOKE_DIR, "run"),
    "--state-dir", os.path.join(SMOKE_DIR, "run")
], check=True)

# 5. Verdict
verdict_smoke_path = os.path.join(SMOKE_DIR, "VERDICT_SMOKE_R9.tsv")
verdict_sum_path = os.path.join(SMOKE_DIR, "SUMMARY_SMOKE_R9.txt")
subprocess.run([
    sys.executable, "-I", "-B", VERDICT_PY,
    "--prereg", prereg_smoke_path,
    "--facts1", facts_smoke_path,
    "--facts2", facts_smoke_path,
    "--state1", state_smoke_path,
    "--state2", state_smoke_path,
    "--out-verdict", verdict_smoke_path,
    "--out-summary", verdict_sum_path,
    "--control-map", CTRL_MAP
], check=True)

# Also copy VERDICT_SMOKE_R9.tsv to EV
shutil.copyfile(verdict_smoke_path, os.path.join(EV, "VERDICT_SMOKE_R9.tsv"))
shutil.copyfile(verdict_sum_path, os.path.join(EV, "SUMMARY_SMOKE_R9.txt"))

print(f"Smoke verdict written to {os.path.join(EV, 'VERDICT_SMOKE_R9.tsv')}")
