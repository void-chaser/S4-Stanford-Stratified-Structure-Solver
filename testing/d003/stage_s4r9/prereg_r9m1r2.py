#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# prereg_r9m1r2.py -- Pre-registration freeze for F4 regression (651 rows) and cited F2 (651 rows) (Rules U313, U314, U317). New file.
import csv, datetime, hashlib, os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r2"))
os.makedirs(EV, exist_ok=True)

OUT_F4 = os.path.join(EV, "PREREG_M1_F4_R9M1R2.tsv")
OUT_F4_SHA = os.path.join(EV, "PREREG_M1_F4_R9M1R2.tsv.sha256")
OUT_F4_TIME = os.path.join(EV, "PREREG_M1_F4_R9M1R2_TIMESTAMP_UTC.txt")

OUT_F2 = os.path.join(EV, "PREREG_M1_CITED_F2_R9M1R2.tsv")
OUT_F2_SHA = os.path.join(EV, "PREREG_M1_CITED_F2_R9M1R2.tsv.sha256")
OUT_F2_TIME = os.path.join(EV, "PREREG_M1_CITED_F2_R9M1R2_TIMESTAMP_UTC.txt")

OUT_DIFF = os.path.join(EV, "PREREG_VS_R9M1_DIFF_R9M1R2.tsv")
OUT_ENG = os.path.join(EV, "ENGINE_COLUMNS_R9M1R2.txt")

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

# 1. Load driver map
f3_to_f4 = {}
with open(os.path.join(REPO, "checkpoints/p05/registries/s4r9/M1/DRIVERS_F3_SIDE_R9M1.tsv"), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("f3_driver\t"):
            continue
        p = line.split("\t")
        f3_to_f4[p[0]] = (p[2], p[3])

# 2. Load M1b tables
plan_b1 = {}
with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b1/PLAN_M1B_R8_M1b1.tsv"), encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        plan_b1[(r["group"], r["point_id"])] = r

supp_b3 = {}
with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b3/PREREG_SUPP_R8_M1b3.tsv"), encoding="utf-8") as f:
    lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
    h = lines[0]
    for l in lines[1:]:
        r = dict(zip(h, l))
        supp_b3[(r["group"], r["point_id"])] = r

with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b3/EFFECTIVE_M1B_R8_M1b3.tsv"), encoding="utf-8") as f:
    lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
    eff_m1b = [dict(zip(lines[0], l)) for l in lines[1:]]

# 3. Load M1c tables
prereg_m1c_facts = {}
with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv"), encoding="utf-8") as f:
    lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
    h = lines[0]
    for l in lines[1:]:
        r = dict(zip(h, l))
        prereg_m1c_facts[r["point_id_r8"]] = r

verdict_m1c = {}
with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1c/r8m1c3/VERDICT_M1C_R8_M1c3.tsv"), encoding="utf-8") as f:
    lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#") and not l.startswith("ROWS=")]
    h = lines[0]
    for l in lines[1:]:
        r = dict(zip(h, l))
        verdict_m1c[r["point_id_r8"]] = r

def map_f4_pid(pid):
    if pid.endswith("-F3"):
        return pid[:-3] + "-F4"
    elif "-F3-" in pid:
        return pid.replace("-F3-", "-F4-")
    return pid + "-F4"

# 4. Build PREREG_M1_F4_R9M1R2 rows (651 rows)
f4_rows = []
m1b_f3 = [r for r in eff_m1b if r["tree"] == "F3"]
m1c_f3 = [r for r in verdict_m1c.values() if r["tree"] == "F3"]

assert len(m1b_f3) == 415, f"M1b F3 expected 415, got {len(m1b_f3)}"
assert len(m1c_f3) == 236, f"M1c F3 expected 236, got {len(m1c_f3)}"

# Process M1b F3
for r in m1b_f3:
    pid = r["point_id"]
    grp = r["group"]
    src = r["source"]
    eff_v = r["effective_verdict"]

    if src in ("M1b1_ENV_AGREE", "M1b1_NOT_RUN"):
        info = plan_b1[(grp, pid)]
        f3_drv = info["driver_name"]
        f3_sha = info["driver_sha256"]
        env = info["env_str"]
        base_id = info["base_id"] if "base_id" in info else pid.replace("-F3", "").replace("F3-", "")
        exp_rc1 = info["expected_rc1"]
        exp_rc2 = info["expected_rc2"]
        exp_hit = info["expected_hit"]
        exp_cls = info["expected_class"]
        inj_call = info.get("inj_call", "-")
        contract = info.get("comparison_contract", "-")
    elif src == "SUPP_R8_M1b3":
        info = supp_b3[(grp, pid)]
        f3_drv = info["driver_name"]
        f3_sha = info["driver_sha256"]
        env = info["env"]
        base_id = info["base_id"]
        exp_rc1 = info["expected_rc1"]
        exp_rc2 = info["expected_rc2"]
        exp_hit = info["expected_hit"]
        exp_cls = info["expected_class"]
        inj_call = info.get("inj_call", "-")
        contract = info.get("comparison_contract", "-")
    else:
        raise ValueError(f"Unknown M1b source {src}")

    f4_drv, f4_sha = f3_to_f4[f3_drv]
    f4_pid = map_f4_pid(pid)
    basis = "受 r9m1 冒烟与正式运行观察影响"

    f4_rows.append([
        "M1b", grp, f4_pid, base_id, "F4", f4_drv, f4_sha, env, "pattern both 4 3",
        exp_cls, exp_rc1, exp_rc2, "-", exp_hit, exp_cls,
        "-", "-", "-", "-", "-", "-",
        inj_call, contract,
        "INFLUENCED", basis, pid, f3_drv, f3_sha, eff_v
    ])

# Process M1c F3
for r in m1c_f3:
    pid = r["point_id_r8"]
    grp = r["group"]
    eff_v = r["verdict"]
    base_id = r["base_id"]
    facts = prereg_m1c_facts[pid]

    f3_drv = facts["driver_name"]
    f3_sha = facts["driver_sha256"]
    env = facts["env_expected"]
    exp_rc1 = facts["exp_rc1"]
    exp_rc2 = facts["exp_rc2"]
    exp_rc3 = facts["exp_rc3"]
    exp_hit = facts["exp_hit"]
    exp_p_verdict = facts["exp_point_verdict"]
    i1, i2, i3, i4, i5, i6 = facts["exp_I1"], facts["exp_I2"], facts["exp_I3"], facts["exp_I4"], facts["exp_I5"], facts["exp_I6"]
    inj_call = "-"
    contract = "-"

    f4_drv, f4_sha = f3_to_f4[f3_drv]
    f4_pid = map_f4_pid(pid)
    basis = "受 r9m1 冒烟与正式运行观察影响"

    f4_rows.append([
        "M1c", grp, f4_pid, base_id, "F4", f4_drv, f4_sha, env, "pattern both 4 3",
        exp_p_verdict, exp_rc1, exp_rc2, exp_rc3, exp_hit, exp_p_verdict,
        i1, i2, i3, i4, i5, i6,
        inj_call, contract,
        "INFLUENCED", basis, pid, f3_drv, f3_sha, eff_v
    ])

assert len(f4_rows) == 651

# 5. Build PREREG_M1_CITED_F2_R9M1R2 rows (651 rows)
f2_rows = []
m1b_f2 = [r for r in eff_m1b if r["tree"] == "F2"]
m1c_f2 = [r for r in verdict_m1c.values() if r["tree"] == "F2"]

assert len(m1b_f2) == 415
assert len(m1c_f2) == 236

for r in m1b_f2:
    pid = r["point_id"]
    grp = r["group"]
    src = r["source"]
    eff_v = r["effective_verdict"]

    if src in ("M1b1_ENV_AGREE", "M1b1_NOT_RUN"):
        info = plan_b1[(grp, pid)]
        f2_drv = info["driver_name"]
        f2_sha = info["driver_sha256"]
        env = info["env_str"]
        base_id = info["base_id"] if "base_id" in info else pid.replace("-F2", "").replace("F2-", "")
        exp_rc1 = info["expected_rc1"]
        exp_rc2 = info["expected_rc2"]
        exp_hit = info["expected_hit"]
        exp_cls = info["expected_class"]
        inj_call = info.get("inj_call", "-")
        contract = info.get("comparison_contract", "-")
    elif src == "SUPP_R8_M1b3":
        info = supp_b3[(grp, pid)]
        f2_drv = info["driver_name"]
        f2_sha = info["driver_sha256"]
        env = info["env"]
        base_id = info["base_id"]
        exp_rc1 = info["expected_rc1"]
        exp_rc2 = info["expected_rc2"]
        exp_hit = info["expected_hit"]
        exp_cls = info["expected_class"]
        inj_call = info.get("inj_call", "-")
        contract = info.get("comparison_contract", "-")
    else:
        raise ValueError(f"Unknown M1b source {src}")

    basis = f"CITED from R8 M1b frozen verdict ({src})"
    f2_rows.append([
        "M1b", grp, pid, base_id, "F2", f2_drv, f2_sha, env, "pattern both 4 3",
        exp_cls, exp_rc1, exp_rc2, "-", exp_hit, exp_cls,
        "-", "-", "-", "-", "-", "-",
        inj_call, contract,
        "CITED", basis, pid, f2_drv, f2_sha, eff_v
    ])

for r in m1c_f2:
    pid = r["point_id_r8"]
    grp = r["group"]
    eff_v = r["verdict"]
    base_id = r["base_id"]
    facts = prereg_m1c_facts[pid]

    f2_drv = facts["driver_name"]
    f2_sha = facts["driver_sha256"]
    env = facts["env_expected"]
    exp_rc1 = facts["exp_rc1"]
    exp_rc2 = facts["exp_rc2"]
    exp_rc3 = facts["exp_rc3"]
    exp_hit = facts["exp_hit"]
    exp_p_verdict = facts["exp_point_verdict"]
    i1, i2, i3, i4, i5, i6 = facts["exp_I1"], facts["exp_I2"], facts["exp_I3"], facts["exp_I4"], facts["exp_I5"], facts["exp_I6"]
    inj_call = "-"
    contract = "-"
    basis = f"CITED from R8 M1c frozen verdict ({r['source']})"

    f2_rows.append([
        "M1c", grp, pid, base_id, "F2", f2_drv, f2_sha, env, "pattern both 4 3",
        exp_p_verdict, exp_rc1, exp_rc2, exp_rc3, exp_hit, exp_p_verdict,
        i1, i2, i3, i4, i5, i6,
        inj_call, contract,
        "CITED", basis, pid, f2_drv, f2_sha, eff_v
    ])

assert len(f2_rows) == 651

header = [
    "section", "group", "point_id", "base_id", "tree", "driver_name", "driver_sha256", "env", "argv",
    "exp_class", "exp_rc1", "exp_rc2", "exp_rc3", "exp_hit", "exp_point_verdict",
    "exp_I1", "exp_I2", "exp_I3", "exp_I4", "exp_I5", "exp_I6",
    "inj_call", "contract",
    "status", "basis", "f3_point_id", "f3_driver", "f3_driver_sha256", "f3_effective_verdict"
]

# Write PREREG_M1_F4_R9M1R2.tsv
f4_rows_sorted = sorted(f4_rows, key=lambda x: (x[0], x[1], x[2]))
with open(OUT_F4, "w", encoding="utf-8") as f:
    f.write("# PREREG_M1_F4_R9M1R2.tsv -- Pre-registration of F4 M1 regression runs (651 rows; Rule U313)\n")
    f.write("\t".join(header) + "\n")
    for r in f4_rows_sorted:
        f.write("\t".join(r) + "\n")

f4_sha = sha256_file(OUT_F4)
now_utc = utc_str()
with open(OUT_F4_SHA, "w", encoding="utf-8") as f:
    f.write(f"{f4_sha}  PREREG_M1_F4_R9M1R2.tsv\n")
with open(OUT_F4_TIME, "w", encoding="utf-8") as f:
    f.write(f"{now_utc}\n")

# Write PREREG_M1_CITED_F2_R9M1R2.tsv
f2_rows_sorted = sorted(f2_rows, key=lambda x: (x[0], x[1], x[2]))
with open(OUT_F2, "w", encoding="utf-8") as f:
    f.write("# PREREG_M1_CITED_F2_R9M1R2.tsv -- Pre-registration of cited F2 baseline for M1 (651 rows; Rule U317)\n")
    f.write("\t".join(header) + "\n")
    for r in f2_rows_sorted:
        f.write("\t".join(r) + "\n")

f2_sha = sha256_file(OUT_F2)
with open(OUT_F2_SHA, "w", encoding="utf-8") as f:
    f.write(f"{f2_sha}  PREREG_M1_CITED_F2_R9M1R2.tsv\n")
with open(OUT_F2_TIME, "w", encoding="utf-8") as f:
    f.write(f"{now_utc}\n")

print(f"Generated PREREG_M1_F4_R9M1R2.tsv ({f4_sha[:12]}...) and CITED_F2 ({f2_sha[:12]}...).")

# 6. Compare row-by-row with d57fcf29 (r9m1 version)
r9m1_f4_path = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M1/PREREG_M1_F4_R9M1.tsv")
r9m1_f4_map = {}
with open(r9m1_f4_path, encoding="utf-8") as f:
    lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
    h_r9m1 = lines[0]
    for l in lines[1:]:
        r = dict(zip(h_r9m1, l))
        r9m1_f4_map[(r["section"], r["group"], r["point_id"])] = r

assert len(r9m1_f4_map) == 651

diff_rows = []
for r in f4_rows_sorted:
    key = (r[0], r[1], r[2])
    old_r = r9m1_f4_map[key]
    new_r = dict(zip(header, r))

    # Compare existing expectation columns
    exp_cols_to_check = [
        "base_id", "tree", "driver_name", "driver_sha256", "env", "argv",
        "exp_class", "exp_rc1", "exp_rc2", "exp_rc3", "exp_hit", "exp_point_verdict",
        "exp_I1", "exp_I2", "exp_I3", "exp_I4", "exp_I5", "exp_I6",
        "f3_point_id", "f3_driver", "f3_driver_sha256", "f3_effective_verdict"
    ]
    for col in exp_cols_to_check:
        ov = old_r[col]
        nv = new_r[col]
        if ov != nv:
            diff_rows.append([key[0], key[1], key[2], col, ov, nv, "UNEXPECTED_DIFF"])

    # Basis difference
    if old_r["basis"] != new_r["basis"]:
        diff_rows.append([key[0], key[1], key[2], "basis", old_r["basis"], new_r["basis"], "EXPECTED_BASIS_UPDATE"])

    # New columns
    diff_rows.append([key[0], key[1], key[2], "inj_call", "N/A", new_r["inj_call"], "NEW_COLUMN_U313"])
    diff_rows.append([key[0], key[1], key[2], "contract", "N/A", new_r["contract"], "NEW_COLUMN_U313"])

# Write PREREG_VS_R9M1_DIFF_R9M1R2.tsv
with open(OUT_DIFF, "w", encoding="utf-8") as f:
    f.write("# PREREG_VS_R9M1_DIFF_R9M1R2.tsv -- Comparison between r9m1r2 and r9m1 preregistrations (Rule U313)\n")
    f.write("section\tgroup\tpoint_id\tfield\told_value\tnew_value\tdiff_type\n")
    for r in diff_rows:
        f.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\t{r[4]}\t{r[5]}\t{r[6]}\n")

unexpected_diffs = [r for r in diff_rows if r[6] == "UNEXPECTED_DIFF"]
print(f"Diff vs d57fcf29: total diff records = {len(diff_rows)}, unexpected diffs = {len(unexpected_diffs)}")
assert len(unexpected_diffs) == 0, f"UNEXPECTED DIFFERENCES FOUND AGAINST d57fcf29: {unexpected_diffs}"

# 7. Write ENGINE_COLUMNS_R9M1R2.txt with rule U314 historical citations
engine_text = """# ENGINE_COLUMNS_R9M1R2.txt -- Frozen verdict criteria and citations for P05-S4 R9 M1R2 (Rule U314)
# Generated by prereg_r9m1r2.py before commit (i). Frozen; do not modify.

1. M1b rc2 Comparison Criteria:
- Contract branches:
  * For contract in ("REPORTED_FAILURE", "CRASH", "SILENT_SWALLOW"):
    If expected_rc2 not in ("-", "", "0", None):
        Enforce actual_rc2 == expected_rc2.
    If expected_rc2 in ("-", "", "0", None):
        rc2 is not compared (matches historical evaluation where rc2=0 represents standard un-retried exit).
  * For contract == "NOT_REACHED_AS_EXPECTED":
    Actual class must be INVALID and hit == 0.
  * For contract in ("CONTROL_OK", "IDENTICAL"):
    Actual class must equal expected_class, run_rc == 0, rc1 == 0, hit == 0.
  * For contract == "NOT_RUN_REGISTRY_ERROR":
    Deliberately not run; verdict is NOT_RUN_AS_EXPECTED.
- Historical Citations:
  * testing/d003/stage_s4r8/plan_and_run_m1b_r8m1b1.py:102-111:
    "if contract in ('REPORTED_FAILURE', 'CRASH', 'SILENT_SWALLOW'): ... if exp_rc2 not in ('-', '', None) and str(exp_rc2) != '0': if str(actual_rc2) != str(exp_rc2): return 'MISMATCH'"
  * testing/d003/stage_s4/run_supp_r8m1b3.py:107-115:
    "if contract in ('REPORTED_FAILURE', 'CRASH', 'SILENT_SWALLOW'): ... if exp_rc2 not in ('-', '', None) and str(exp_rc2) != '0': if str(act_rc2) != str(exp_rc2): return 'MISMATCH'"

2. M1c G6c / CTRL_AUX '-' Handling Criteria:
- Control Rows Special Rule:
  * Rows in group G6c and CTRL_AUX are control rows. In the frozen fact tables (PREREG_M1C_FACTS_R8_M1c2.tsv and VERDICT_M1C_R8_M1c3.tsv), exp_point_verdict and exp_I1..exp_I6 are recorded as '-'.
  * These rows have no RESULTS entry; they are judged strictly on execution facts (rc1, rc2, rc3, hit) and clean_env.
  * The engine treats '-' in exp_point_verdict and exp_I1..exp_I6 as 'unconstrained / skip check', rather than matching a literal string '-'.
  * For G6c / CTRL_AUX, when exp_point_verdict == '-', computed_class CONTROL_OK is required.
- Historical Citations:
  * testing/d003/stage_s4/verdict_m1c_r8m1c3.py:103-106:
    "# control rows (G6c, CTRL_AUX) have no RESULTS entry (I1-I6 and point_verdict are '-' in the frozen table); they are judged on facts and env only (brief 6.2). Point rows need both the run record and the RESULTS entry."
  * testing/d003/stage_s4/verdict_m1c_r8m1c3.py:114-115, 124-125, 132-133, 138-139:
    "if fr.get('exp_' + label, '-') in ('', '-'): continue"
    "exp_pv = fr.get('exp_point_verdict', '-'); if exp_pv not in ('', '-') and inv.get('point_verdict', '') != exp_pv: ok = False; diffs.append(...)"
    "if exp in ('', '-'): continue"

3. Columns without Historical Citation:
- All other expectation columns (exp_rc1, exp_hit, exp_class, exp_I1..I6) are compared with strict literal string equality against observed run facts.
"""

with open(OUT_ENG, "w", encoding="utf-8") as f:
    f.write(engine_text.strip() + "\n")

print(f"Wrote {OUT_ENG}.")
