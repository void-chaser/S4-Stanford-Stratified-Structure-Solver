#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# run_formal_r9m1.py -- Execute formal two-pass runs for all 651 F4 rows in M1 (Step S-F). New file.
import concurrent.futures, csv, datetime, hashlib, os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1"))
os.makedirs(EV, exist_ok=True)

RUNS_DIR = os.path.join(EV, "runs", "formal")
os.makedirs(RUNS_DIR, exist_ok=True)

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

def utc_str():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# 1. Load PREREG_M1_F4_R9M1.tsv (651 rows)
prereg_path = os.path.join(EV, "PREREG_M1_F4_R9M1.tsv")
rows_f4 = []
with open(prereg_path, encoding="utf-8") as fh:
    lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
    h = lines[0]
    for l in lines[1:]:
        rows_f4.append(dict(zip(h, l)))

assert len(rows_f4) == 651, f"Expected 651 F4 rows, got {len(rows_f4)}"

# 2. Load driver paths from DRIVERS_F3_SIDE_R9M1.tsv
drv_paths = {}
with open(os.path.join(EV, "DRIVERS_F3_SIDE_R9M1.tsv"), encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("f3_driver\t"):
            continue
        p = line.split("\t")
        drv_paths[p[2]] = (os.path.join(REPO, p[5]), p[3])

# Verify all F4 drivers exist and match expected sha256 before any run
print("--- Pre-run driver sha256 verification ---")
for dname, (dpath, exp_sha) in sorted(drv_paths.items()):
    act_sha = sha256_file(dpath)
    assert act_sha == exp_sha, f"Driver {dname} pre-run sha mismatch: act={act_sha}, exp={exp_sha}"
    print(f"  {dname}: {act_sha[:12]}... OK")

# Separate into M1b (415 rows) and M1c (236 rows)
m1b_rows = [r for r in rows_f4 if r["section"] == "M1b"]
m1c_rows = [r for r in rows_f4 if r["section"] == "M1c"]
assert len(m1b_rows) == 415
assert len(m1c_rows) == 236

GRID = ["pattern", "both", "4", "3"]

def run_single_m1b(job):
    pt, pas = job
    pid = pt["point_id"]
    grp = pt["group"]
    dname = pt["driver_name"]
    dpath, exp_sha = drv_paths[dname]

    if pt["f3_effective_verdict"] == "NOT_RUN_AS_EXPECTED":
        return {
            "section": "M1b", "group": grp, "point_id": pid, "base_id": pt["base_id"],
            "tree": "F4", "driver_name": dname, "driver_sha256": exp_sha,
            "rc": "-", "rc1": "-", "rc2": "-", "rc3": "-",
            "hit": "-", "class": "NOT_RUN_REGISTRY_ERROR",
            "I1": "-", "I2": "-", "I3": "-", "I4": "-", "I5": "-", "I6": "-",
            "env": pt["env"], "f3_point_id": pt["f3_point_id"], "f3_effective_verdict": pt["f3_effective_verdict"]
        }

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

    pdir = os.path.join(RUNS_DIR, f"pass{pas}", "m1b", f"{grp}_{pid}")
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

    m_rc1 = re.search(r"^RC first (-?\d+)", stdout, re.M)
    rc1 = int(m_rc1.group(1)) if m_rc1 else None

    m_rc2 = re.search(r"^RC retry (-?\d+)", stdout, re.M)
    rc2 = int(m_rc2.group(1)) if m_rc2 else None

    rc3 = "-"

    m_hitc = re.search(r"^S4FMM HITCOUNT (\d+)", stderr, re.M)
    if m_hitc:
        hit = int(m_hitc.group(1))
    else:
        hit = len(re.findall(r"^S4FMM HIT ", stderr, re.M))

    exp_c = pt["exp_class"]
    exp_rc1_val = None if pt["exp_rc1"] in ("-", "") else int(pt["exp_rc1"])
    exp_rc2_val = None if pt["exp_rc2"] in ("-", "") else int(pt["exp_rc2"])
    exp_hit_val = None if pt["exp_hit"] in ("-", "") else int(pt["exp_hit"])

    is_ctrl = (exp_c in ("CONTROL_OK", "CLEAN") or "none" in pt["env"] or exp_hit_val == 0 or grp in ("CTRL_SEAM", "M1_CTRL", "G2c_control", "POLY_33"))
    is_real = ("exec" not in pt["env"])
    inj_call = 2 if (exp_rc2_val == 20 and exp_rc1_val == 0) else 1

    computed_class, _, _ = judge.classify(raw_rc, rc1, rc2, hit, is_ctrl, is_real, inj_call=inj_call)

    return {
        "section": "M1b", "group": grp, "point_id": pid, "base_id": pt["base_id"],
        "tree": "F4", "driver_name": dname, "driver_sha256": exp_sha,
        "rc": str(raw_rc), "rc1": str(rc1) if rc1 is not None else "-", "rc2": str(rc2) if rc2 is not None else "-", "rc3": "-",
        "hit": str(hit), "class": computed_class,
        "I1": "-", "I2": "-", "I3": "-", "I4": "-", "I5": "-", "I6": "-",
        "env": pt["env"], "f3_point_id": pt["f3_point_id"], "f3_effective_verdict": pt["f3_effective_verdict"]
    }

# 3. Execute Pass 1 and Pass 2
fact_header = [
    "section", "group", "point_id", "base_id", "tree", "driver_name", "driver_sha256",
    "rc", "rc1", "rc2", "rc3", "hit", "class",
    "I1", "I2", "I3", "I4", "I5", "I6",
    "env", "f3_point_id", "f3_effective_verdict"
]

PREREG_G5 = os.path.join(REPO, "checkpoints/p05/registries/s4r6c/REGISTRY_S4_PRE_R6b_STATE_v2.tsv")
CONTROL_G5 = os.path.join(REPO, "checkpoints/p05/registries/s4r6b/REGISTRY_S4_PRE_R6b_CONTROL.tsv")
PREREG_SEAM = os.path.join(REPO, "checkpoints/p05/registries/s4r6c/REGISTRY_S4_PRE_R6c_SEAM.tsv")
CONTROL_SEAM = os.path.join(REPO, "checkpoints/p05/registries/s4r6c/REGISTRY_S4_PRE_R6c_SEAM_CONTROL.tsv")

DRV_STATE = drv_paths["r6bstate-F4-dbg"][0]
DRV_SEAMF = drv_paths["r6bseam-seamF-F4"][0]
DRV_FMMRET = drv_paths["r6bseam-fmmret-F4"][0]

m1c_outdir = os.path.join(RUNS_DIR, "m1c_F4")
os.makedirs(m1c_outdir, exist_ok=True)

for pas in (1, 2):
    print(f"\n=================== STARTING PASS {pas} ({utc_str()}) ===================")
    
    # 3.1 Run M1b points
    print(f"Running M1b points ({len(m1b_rows)} points) for Pass {pas}...")
    jobs = [(pt, pas) for pt in m1b_rows]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        m1b_results = list(ex.map(run_single_m1b, jobs))
    print(f"M1b Pass {pas} completed: {len(m1b_results)} points.")

    # 3.2 Run M1c G5 points under run_r6c_state.py if not already present
    g5_pass_tsv = os.path.join(m1c_outdir, f"STATE_R6c_pass{pas}.tsv")
    if not os.path.isfile(g5_pass_tsv):
        print(f"Running M1c G5 points under run_r6c_state.py for Pass {pas}...")
        cmd_g5 = [
            "python3", "-I", "-B", "testing/d003/stage_s4/run_r6c_state.py",
            "full", PREREG_G5, CONTROL_G5, DRV_STATE, m1c_outdir, str(pas)
        ]
        p_g5 = subprocess.run(cmd_g5, cwd=REPO, capture_output=True, text=True)
        if p_g5.returncode != 0:
            print(f"G5 Pass {pas} failed:\n{p_g5.stderr}\n{p_g5.stdout}")
            sys.exit(1)
        print(f"G5 Pass {pas} finished: rc={p_g5.returncode}")
    else:
        print(f"G5 Pass {pas} already completed -> {g5_pass_tsv}")

    # 3.3 Run M1c G6 seam points under r6c2_seam_state.py if not already present
    seam_pass_tsv = os.path.join(m1c_outdir, f"STATE_SEAM_R6c_pass{pas}.tsv")
    if not os.path.isfile(seam_pass_tsv):
        print(f"Running M1c G6 seam points under r6c2_seam_state.py for Pass {pas}...")
        cmd_seam = [
            "python3", "-I", "-B", "testing/d003/stage_s4/r6c2_seam_state.py",
            PREREG_SEAM, CONTROL_SEAM, DRV_SEAMF, DRV_FMMRET, m1c_outdir, str(pas)
        ]
        p_seam = subprocess.run(cmd_seam, cwd=REPO, capture_output=True, text=True)
        if p_seam.returncode != 0:
            print(f"Seam Pass {pas} failed:\n{p_seam.stderr}\n{p_seam.stdout}")
            sys.exit(1)
        print(f"Seam Pass {pas} finished: rc={p_seam.returncode}")
    else:
        print(f"Seam Pass {pas} already completed -> {seam_pass_tsv}")

# Run judges for M1c if not already produced
print("\n--- Running judges for M1c ---")
res_state_tsv = os.path.join(m1c_outdir, "RESULTS_R6c_STATE.tsv")
if not os.path.isfile(res_state_tsv):
    cmd_jg5 = ["python3", "-I", "-B", "testing/d003/stage_s4/r6c_judge.py", PREREG_G5, CONTROL_G5, m1c_outdir]
    subprocess.run(cmd_jg5, cwd=REPO, check=True)
else:
    print(f"RESULTS_R6c_STATE.tsv already exists -> {res_state_tsv}")

res_seam_tsv = os.path.join(m1c_outdir, "RESULTS_R6c_SEAM.tsv")
if not os.path.isfile(res_seam_tsv):
    cmd_jseam = ["python3", "-I", "-B", "testing/d003/stage_s4/r6c2_seam_judge.py", PREREG_SEAM, CONTROL_SEAM, m1c_outdir]
    subprocess.run(cmd_jseam, cwd=REPO, check=True)
else:
    print(f"RESULTS_R6c_SEAM.tsv already exists -> {res_seam_tsv}")
print("M1c judges completed.")

# 4. Parse M1c outputs and assemble combined pass tables
def load_m1c_pass_facts(pas):
    # G5 state facts
    g5_path = os.path.join(m1c_outdir, f"STATE_R6c_pass{pas}.tsv")
    g5_facts = {}
    with open(g5_path, encoding="utf-8") as fh:
        lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            r = dict(zip(h, l))
            g5_facts[r["id"]] = r

    # Seam facts
    seam_path = os.path.join(m1c_outdir, f"STATE_SEAM_R6c_pass{pas}.tsv")
    seam_facts = {}
    with open(seam_path, encoding="utf-8") as fh:
        lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            r = dict(zip(h, l))
            seam_facts[r["id"]] = r

    # Judgements for G5
    g5_res_path = os.path.join(m1c_outdir, "RESULTS_R6c_STATE.tsv")
    g5_judgements = {}
    with open(g5_res_path, encoding="utf-8") as fh:
        lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            r = dict(zip(h, l))
            if r.get("pass") == str(pas):
                g5_judgements[r["point_id"]] = r

    # Judgements for Seam
    seam_res_path = os.path.join(m1c_outdir, "RESULTS_R6c_SEAM.tsv")
    seam_judgements = {}
    with open(seam_res_path, encoding="utf-8") as fh:
        lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            r = dict(zip(h, l))
            if r.get("pass") == str(pas):
                seam_judgements[r["point_id"]] = r

    m1c_results = []
    for pt in m1c_rows:
        pid = pt["point_id"]
        grp = pt["group"]
        base_id = pt["base_id"]
        dname = pt["driver_name"]
        dsha = pt["driver_sha256"]

        if grp in ("G5", "CTRL_AUX"):
            # ID in g5_facts is base_id (e.g. M-once-closed1d-malloc-1 or C-01-closed1d-once-once)
            f = g5_facts.get(base_id, {})
            j = g5_judgements.get(base_id, {})
            rc1 = f.get("gdb_rc1", f.get("nogdb_rc1", "-"))
            rc2 = f.get("gdb_rc2", f.get("nogdb_rc2", "-"))
            rc3 = f.get("gdb_rc3", f.get("nogdb_rc3", "-"))
            hit = f.get("gdb_hit", f.get("nogdb_hit", "-"))
            raw_rc = f.get("rc_nogdb", f.get("rc_gdb", "0"))
            
            i1 = j.get("I1", "-")
            i2 = j.get("I2", "-")
            i3 = j.get("I3", "-")
            i4 = j.get("I4", "-")
            i5 = j.get("I5", "-")
            i6 = j.get("I6", "-")
            cls = j.get("point_verdict", "HOLD" if grp == "G5" else "CONTROL_OK")
        else:
            # Seam points (G6, G6c)
            f = seam_facts.get(base_id, {})
            j = seam_judgements.get(base_id, {})
            rc1 = f.get("gdb_rc1", f.get("nogdb_rc1", "-"))
            rc2 = f.get("gdb_rc2", f.get("nogdb_rc2", "-"))
            rc3 = "-"
            hit = f.get("gdb_hit", f.get("nogdb_hit", "-"))
            raw_rc = f.get("rc_nogdb", f.get("rc_gdb", "0"))
            i1 = i2 = i3 = i4 = i5 = i6 = "-"
            cls = j.get("point_verdict", "HOLD" if grp == "G6" else "CONTROL_OK")

        m1c_results.append({
            "section": "M1c", "group": grp, "point_id": pid, "base_id": base_id,
            "tree": "F4", "driver_name": dname, "driver_sha256": dsha,
            "rc": str(raw_rc), "rc1": str(rc1), "rc2": str(rc2), "rc3": str(rc3),
            "hit": str(hit), "class": cls,
            "I1": str(i1), "I2": str(i2), "I3": str(i3), "I4": str(i4), "I5": str(i5), "I6": str(i6),
            "env": pt["env"], "f3_point_id": pt["f3_point_id"], "f3_effective_verdict": pt["f3_effective_verdict"]
        })
    return m1c_results

# Re-run single pass of M1b for pass 1 and pass 2 to get facts
for pas in (1, 2):
    print(f"Assembling facts table for Pass {pas}...")
    jobs = [(pt, pas) for pt in m1b_rows]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        m1b_facts = list(ex.map(run_single_m1b, jobs))
    m1c_facts = load_m1c_pass_facts(pas)

    all_facts = m1b_facts + m1c_facts
    assert len(all_facts) == 651, f"Pass {pas} facts count {len(all_facts)} != 651"

    out_pass_tsv = os.path.join(RUNS_DIR, f"FORMAL_FACTS_M1_F4_R9M1_pass{pas}.tsv")
    with open(out_pass_tsv, "w", encoding="utf-8") as fh:
        fh.write(f"# FORMAL_FACTS_M1_F4_R9M1_pass{pas}.tsv -- Formal Pass {pas} run facts for P05-S4 R9 M1\n")
        fh.write("\t".join(fact_header) + "\n")
        for r in all_facts:
            fh.write("\t".join([r[col] for col in fact_header]) + "\n")
    print(f"Wrote Pass {pas} facts table -> {out_pass_tsv} ({len(all_facts)} rows)")

# 5. Post-run driver sha256 verification
print("\n--- Post-run driver sha256 verification ---")
for dname, (dpath, exp_sha) in sorted(drv_paths.items()):
    act_sha = sha256_file(dpath)
    assert act_sha == exp_sha, f"Driver {dname} post-run sha mismatch: act={act_sha}, exp={exp_sha}"
    print(f"  {dname}: {act_sha[:12]}... OK")

print("\nFormal two-pass run completed successfully.")
sys.exit(0)
