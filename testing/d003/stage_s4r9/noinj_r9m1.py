#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# noinj_r9m1.py -- No-injection control runs for all newly built F4 drivers x env combinations. New file.
import csv, glob, os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1"))
os.makedirs(EV, exist_ok=True)

OUT_TSV = os.path.join(EV, "NOINJ_R9M1.tsv")
OUT_TXT = os.path.join(EV, "noinj_r9m1.txt")

# 1. Load built drivers from DRIVERS_F3_SIDE_R9M1.tsv
inv_path = os.path.join(EV, "DRIVERS_F3_SIDE_R9M1.tsv")
built_drivers = {}
with open(inv_path, "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("f3_driver\t"):
            continue
        parts = line.split("\t")
        f3_d, f3_sha, f4_d, f4_sha, status, f4_path = parts[:6]
        if status in ("BUILT_VERIFIED", "TO_BUILD"):
            built_drivers[f3_d] = (f4_d, os.path.join(REPO, f4_path))

print(f"Loaded {len(built_drivers)} built drivers to test under no-injection.")

# 2. Extract unique base envs for each driver from M1b and M1c tables
plan_b1 = {}
with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b1/PLAN_M1B_R8_M1b1.tsv"), encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        plan_b1[r["point_id"]] = r

supp_b3 = {}
with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b3/PREREG_SUPP_R8_M1b3.tsv"), encoding="utf-8") as f:
    lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
    h = lines[0]
    for l in lines[1:]:
        supp_b3[dict(zip(h, l))["point_id"]] = dict(zip(h, l))

with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b3/EFFECTIVE_M1B_R8_M1b3.tsv"), encoding="utf-8") as f:
    lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
    eff_m1b = [dict(zip(lines[0], l)) for l in lines[1:]]

def clean_base_env(env_str):
    parts = [p.strip() for p in env_str.split(";") if p.strip()]
    kept = []
    for p in parts:
        k = p.split("=")[0]
        if k.startswith("S4FMM_INJECT") or k.startswith("S4FMM_NTH") or k.startswith("S4FMM_TWICE"):
            continue
        kept.append(p)
    return ";".join(sorted(kept))

combos = []
seen = set()

for r in eff_m1b:
    if r["tree"] != "F3":
        continue
    pid = r["point_id"]
    src = r["source"]
    if src in ("M1b1_ENV_AGREE", "M1b1_NOT_RUN"):
        drv = plan_b1[pid]["driver_name"]
        raw_env = plan_b1[pid]["env_str"]
    elif src == "SUPP_R8_M1b3":
        drv = supp_b3[pid]["driver_name"]
        raw_env = supp_b3[pid]["env"]
    else:
        continue
    if drv in built_drivers:
        be = clean_base_env(raw_env)
        key = (drv, be)
        if key not in seen:
            seen.add(key)
            combos.append((drv, be))

with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv"), encoding="utf-8") as f:
    lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
    h = lines[0]
    for l in lines[1:]:
        r = dict(zip(h, l))
        if r["tree"] != "F3":
            continue
        drv = r["driver_name"]
        if drv in built_drivers:
            be = clean_base_env(r["env_expected"])
            key = (drv, be)
            if key not in seen:
                seen.add(key)
                combos.append((drv, be))

combos.sort()
print(f"Total non-injection driver x env combinations: {len(combos)}")

# 3. Run each combination
GRID = ["pattern", "both", "4", "3"]
results = []
log_lines = [
    "# noinj_r9m1.txt -- Non-injection control run for newly built F4 drivers (Step S-B-3)\n",
    f"# Total combinations: {len(combos)}\n\n"
]

fails = 0
for idx, (f3_drv, be) in enumerate(combos, 1):
    f4_drv, exe_path = built_drivers[f3_drv]
    assert os.path.isfile(exe_path), f"Executable missing: {exe_path}"

    child_env = os.environ.copy()
    for k in list(child_env.keys()):
        if k.startswith("S4FMM_"):
            del child_env[k]
    for pair in be.split(";"):
        if "=" in pair:
            k, v = pair.split("=", 1)
            child_env[k] = v

    cmd = [exe_path] + GRID
    proc = subprocess.run(cmd, cwd=REPO, env=child_env, capture_output=True, text=True, timeout=120)
    rc = proc.returncode

    # Check sanitizer output
    combined = proc.stdout + "\n" + proc.stderr
    san_reports = len(re.findall(r"ERROR:s*(?:AddressSanitizer|LeakSanitizer|UndefinedBehaviorSanitizer)", combined))

    status = "PASS" if rc == 0 and san_reports == 0 else "FAIL"
    if status == "FAIL":
        fails += 1

    results.append([f4_drv, f3_drv, be, str(rc), str(san_reports), status])
    log_lines.append(f"[{idx}/{len(combos)}] {f4_drv} (f3: {f3_drv}) env='{be}' rc={rc} san={san_reports} -> {status}\n")
    if rc != 0:
        log_lines.append(f"  STDOUT: {proc.stdout[:200]}\n  STDERR: {proc.stderr[:200]}\n")

print(f"Completed {len(combos)} noinj runs. Fails={fails}")

# 4. Write output files
with open(OUT_TSV, "w", encoding="utf-8") as fh:
    fh.write("# NOINJ_R9M1.tsv -- Non-injection control runs for newly built F4 drivers\n")
    fh.write("f4_driver\tf3_driver\tbase_env\trc\tsan_reports\tstatus\n")
    for r in results:
        fh.write("\t".join(r) + "\n")

with open(OUT_TXT, "w", encoding="utf-8") as fh:
    fh.writelines(log_lines)

print(f"Wrote NOINJ_R9M1.tsv -> {OUT_TSV}")
print(f"Wrote noinj_r9m1.txt -> {OUT_TXT}")
sys.exit(fails)
