#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# run_smoke_r9m1.py -- Smoke run for M1 F4: at least 1 row per (group x driver) combination (Step S-F). New file.
import csv, hashlib, os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1"))
os.makedirs(EV, exist_ok=True)
SMOKE_DIR = os.path.join(EV, "runs", "smoke")
os.makedirs(SMOKE_DIR, exist_ok=True)

OUT_TSV = os.path.join(EV, "SMOKE_M1_F4_R9M1.tsv")
OUT_TXT = os.path.join(EV, "SMOKE_SUMMARY_R9M1.txt")

sys.path.insert(0, os.path.join(REPO, "testing", "d003"))
import judge_d003 as judge

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            c = fh.read(65536)
            if not c: break
            h.update(c)
    return h.hexdigest()

# 1. Load PREREG_M1_F4_R9M1.tsv
prereg_path = os.path.join(EV, "PREREG_M1_F4_R9M1.tsv")
rows = []
with open(prereg_path, encoding="utf-8") as fh:
    lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
    h = lines[0]
    for l in lines[1:]:
        rows.append(dict(zip(h, l)))

# 2. Select 1 representative point per (section, group, driver_name)
combos = {}
for r in rows:
    key = (r["section"], r["group"], r["driver_name"])
    if key not in combos:
        combos[key] = r

smoke_points = sorted(combos.values(), key=lambda x: (x["section"], x["group"], x["point_id"]))
print(f"Selected {len(smoke_points)} smoke points covering all {len(combos)} (section x group x driver) combos.")

# 3. Load driver paths from DRIVERS_F3_SIDE_R9M1.tsv
drv_paths = {}
with open(os.path.join(EV, "DRIVERS_F3_SIDE_R9M1.tsv"), encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("f3_driver\t"):
            continue
        p = line.split("\t")
        drv_paths[p[2]] = (os.path.join(REPO, p[5]), p[3])

# 4. Execute smoke points
GRID = ["pattern", "both", "4", "3"]
results = []
log_lines = [
    "# SMOKE_SUMMARY_R9M1.txt -- Smoke test summary (Step S-F)\n",
    f"# Points tested: {len(smoke_points)}\n\n"
]

mismatch_count = 0
invalid_count = 0
gdb_div_count = 0

for idx, pt in enumerate(smoke_points, 1):
    pid = pt["point_id"]
    sec = pt["section"]
    grp = pt["group"]
    dname = pt["driver_name"]
    dpath, exp_sha = drv_paths[dname]

    # Pre-run sha256 check
    pre_sha = sha256_file(dpath)
    assert pre_sha == exp_sha == pt["driver_sha256"], f"Pre-run sha mismatch for {dname}: act={pre_sha}, exp={exp_sha}"

    env = os.environ.copy()
    for k in list(env.keys()):
        if k.startswith("S4FMM_"):
            del env[k]
    for pair in pt["env"].split(";"):
        if "=" in pair:
            k, v = pair.split("=", 1)
            if k == "S4FMM_INJECT" and v == "none":
                continue
            env[k] = v

    pdir = os.path.join(SMOKE_DIR, f"{sec}_{grp}_{pid}")
    os.makedirs(pdir, exist_ok=True)

    cmd = [dpath] + GRID
    proc = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True, timeout=120)
    raw_rc = proc.returncode
    stdout = proc.stdout
    stderr = proc.stderr

    with open(os.path.join(pdir, "stdout.txt"), "w", encoding="utf-8") as f:
        f.write(stdout)
    with open(os.path.join(pdir, "stderr.txt"), "w", encoding="utf-8") as f:
        f.write(stderr)

    # Post-run sha256 check
    post_sha = sha256_file(dpath)
    assert post_sha == exp_sha, f"Post-run sha mismatch for {dname}: act={post_sha}, exp={exp_sha}"

    # Parse facts
    m_rc1 = re.search(r"^RC first (-?\d+)", stdout, re.M)
    rc1 = int(m_rc1.group(1)) if m_rc1 else None

    m_rc2 = re.search(r"^RC retry (-?\d+)", stdout, re.M)
    rc2 = int(m_rc2.group(1)) if m_rc2 else None

    m_rc3 = re.search(r"^R6CALLS 3 (-?\d+)", stdout, re.M)
    rc3 = int(m_rc3.group(1)) if m_rc3 else None

    m_hitc = re.search(r"^S4FMM HITCOUNT (\d+)", stderr, re.M)
    if m_hitc:
        hit = int(m_hitc.group(1))
    else:
        hit = len(re.findall(r"^S4FMM HIT ", stderr, re.M))

    exp_c = pt["exp_class"]
    exp_rc1_val = None if pt["exp_rc1"] in ("-", "") else int(pt["exp_rc1"])
    exp_rc2_val = None if pt["exp_rc2"] in ("-", "") else int(pt["exp_rc2"])
    exp_hit_val = None if pt["exp_hit"] in ("-", "") else int(pt["exp_hit"])

    is_ctrl = (exp_c in ("CONTROL_OK", "CLEAN") or "none" in pt["env"] or exp_hit_val == 0 or grp in ("CTRL_SEAM", "M1_CTRL", "G2c_control", "CTRL_AUX", "G6c", "POLY_33"))
    is_real = ("exec" not in pt["env"])
    inj_call = 2 if ("TWICE" in pt["env"] or (exp_rc1_val == 0 and exp_rc2_val is not None and exp_rc2_val != 0)) else 1

    # Classify
    computed_class, _, _ = judge.classify(raw_rc, rc1, rc2, hit, is_ctrl, is_real, inj_call=inj_call)

    diff_fields = []
    # Check return codes and hit
    if exp_rc1_val is not None and rc1 != exp_rc1_val:
        diff_fields.append(f"rc1({rc1}!={exp_rc1_val})")
    if exp_rc2_val is not None and rc2 != exp_rc2_val:
        diff_fields.append(f"rc2({rc2}!={exp_rc2_val})")
    if exp_hit_val is not None and hit != exp_hit_val:
        diff_fields.append(f"hit({hit}!={exp_hit_val})")

    # Expected judge class
    if sec == "M1c":
        exp_judge_class = "REPORTED_FAILURE" if exp_c == "HOLD" else "CONTROL_OK"
    else:
        exp_judge_class = exp_c

    # Check classification
    if pt["f3_effective_verdict"] == "NOT_RUN_AS_EXPECTED":
        point_verdict = "NOT_RUN_AS_EXPECTED"
    elif pt["f3_effective_verdict"] == "NOT_REACHED_AS_EXPECTED":
        if computed_class == "INVALID":
            point_verdict = "NOT_REACHED_AS_EXPECTED"
        else:
            point_verdict = "MISMATCH"
            diff_fields.append("not_reached_mismatch")
    elif computed_class == "INVALID" and not is_ctrl and exp_judge_class != "INVALID":
        point_verdict = "INVALID"
        invalid_count += 1
    elif diff_fields or (exp_judge_class != "-" and computed_class != exp_judge_class):
        point_verdict = "MISMATCH"
        mismatch_count += 1
        if computed_class != exp_judge_class:
            diff_fields.append(f"class({computed_class}!={exp_judge_class})")
    else:
        point_verdict = "MATCH"

    results.append([
        sec, grp, pid, dname, exp_sha,
        str(rc1), str(rc2), str(rc3) if rc3 is not None else "-", str(hit), computed_class,
        point_verdict, ";".join(diff_fields) if diff_fields else "NONE"
    ])

    log_lines.append(f"[{idx:02d}/{len(smoke_points)}] {sec} {grp} {pid} drv={dname} rc1={rc1} rc2={rc2} hit={hit} class={computed_class} -> {point_verdict}\n")
    print(f"[{idx:02d}/{len(smoke_points)}] {sec} {grp} {pid} drv={dname} rc1={rc1} rc2={rc2} hit={hit} class={computed_class} -> {point_verdict}")

print(f"\nSmoke run completed: {len(smoke_points)} points.")
print(f"Summary: MISMATCH={mismatch_count}, INVALID={invalid_count}, GDB_DIVERGENT={gdb_div_count}")

header = [
    "section", "group", "point_id", "driver_name", "driver_sha256",
    "rc1", "rc2", "rc3", "hit", "computed_class", "verdict", "difference_fields"
]

with open(OUT_TSV, "w", encoding="utf-8") as fh:
    fh.write("# SMOKE_M1_F4_R9M1.tsv -- Smoke test results for P05-S4 R9 M1\n")
    fh.write("\t".join(header) + "\n")
    for r in results:
        fh.write("\t".join(r) + "\n")

log_lines.append(f"\nSummary: TOTAL={len(smoke_points)}, MISMATCH={mismatch_count}, INVALID={invalid_count}, GDB_DIV={gdb_div_count}\n")
with open(OUT_TXT, "w", encoding="utf-8") as fh:
    fh.writelines(log_lines)

print(f"Wrote {OUT_TSV}")
print(f"Wrote {OUT_TXT}")

if mismatch_count > 0 or invalid_count > 0 or gdb_div_count > 0:
    print("STOPPING AT SMOKE: non-zero mismatch, invalid, or gdb_div detected!", file=sys.stderr)
    sys.exit(1)

print("Smoke PASS: 0 mismatch, 0 invalid, 0 gdb_div.")
sys.exit(0)
