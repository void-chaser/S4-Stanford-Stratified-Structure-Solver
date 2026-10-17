#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# prereg_r9m1.py -- Freeze pre-registration for F4 regression (651 rows) and cited F2 baseline (651 rows) (Rules U306, U307). New file.
import csv, datetime, hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1"))
os.makedirs(EV, exist_ok=True)

OUT_F4 = os.path.join(EV, "PREREG_M1_F4_R9M1.tsv")
OUT_F4_SHA = os.path.join(EV, "PREREG_M1_F4_R9M1.tsv.sha256")
OUT_F4_TIME = os.path.join(EV, "PREREG_M1_F4_R9M1_TIMESTAMP_UTC.txt")

OUT_F2 = os.path.join(EV, "PREREG_M1_CITED_F2_R9M1.tsv")
OUT_F2_SHA = os.path.join(EV, "PREREG_M1_CITED_F2_R9M1.tsv.sha256")
OUT_F2_TIME = os.path.join(EV, "PREREG_M1_CITED_F2_R9M1_TIMESTAMP_UTC.txt")

OUT_ENG = os.path.join(EV, "ENGINE_COLUMNS_R9M1.txt")

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
with open(os.path.join(EV, "DRIVERS_F3_SIDE_R9M1.tsv"), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("f3_driver\t"):
            continue
        p = line.split("\t")
        f3_d, f3_sha, f4_d, f4_sha = p[0], p[1], p[2], p[3]
        f3_to_f4[f3_d] = (f4_d, f4_sha)

# 2. Load M1b tables
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

# 4. Build PREREG_M1_F4_R9M1 rows (651 rows)
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
    eff_cls = r["effective_class_p1"]

    if src in ("M1b1_ENV_AGREE", "M1b1_NOT_RUN"):
        info = plan_b1[pid]
        f3_drv = info["driver_name"]
        f3_sha = info["driver_sha256"]
        env = info["env_str"]
        base_id = info["base_id"] if "base_id" in info else pid.replace("-F3", "").replace("F3-", "")
        exp_rc1 = info["expected_rc1"]
        exp_rc2 = info["expected_rc2"]
        exp_hit = info["expected_hit"]
        exp_cls = info["expected_class"]
    elif src == "SUPP_R8_M1b3":
        info = supp_b3[pid]
        f3_drv = info["driver_name"]
        f3_sha = info["driver_sha256"]
        env = info["env"]
        base_id = info["base_id"]
        exp_rc1 = info["expected_rc1"]
        exp_rc2 = info["expected_rc2"]
        exp_hit = info["expected_hit"]
        exp_cls = info["expected_class"]
    else:
        raise ValueError(f"Unknown M1b source {src}")

    f4_drv, f4_sha = f3_to_f4[f3_drv]
    f4_pid = map_f4_pid(pid)
    basis = f"R9 M1 regression of {pid}"

    f4_rows.append([
        "M1b", grp, f4_pid, base_id, "F4", f4_drv, f4_sha, env, "pattern both 4 3",
        exp_cls, exp_rc1, exp_rc2, "-", exp_hit, exp_cls,
        "-", "-", "-", "-", "-", "-",
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

    f4_drv, f4_sha = f3_to_f4[f3_drv]
    f4_pid = map_f4_pid(pid)
    basis = f"R9 M1 regression of {pid}"

    f4_rows.append([
        "M1c", grp, f4_pid, base_id, "F4", f4_drv, f4_sha, env, "pattern both 4 3",
        exp_p_verdict, exp_rc1, exp_rc2, exp_rc3, exp_hit, exp_p_verdict,
        i1, i2, i3, i4, i5, i6,
        "INFLUENCED", basis, pid, f3_drv, f3_sha, eff_v
    ])

assert len(f4_rows) == 651

# 5. Build PREREG_M1_CITED_F2_R9M1 rows (651 rows)
f2_rows = []
m1b_f2 = [r for r in eff_m1b if r["tree"] == "F2"]
m1c_f2 = [r for r in verdict_m1c.values() if r["tree"] == "F2"]

assert len(m1b_f2) == 415, f"M1b F2 expected 415, got {len(m1b_f2)}"
assert len(m1c_f2) == 236, f"M1c F2 expected 236, got {len(m1c_f2)}"

for r in m1b_f2:
    pid = r["point_id"]
    grp = r["group"]
    src = r["source"]
    eff_v = r["effective_verdict"]
    eff_cls = r["effective_class_p1"]

    if src in ("M1b1_ENV_AGREE", "M1b1_NOT_RUN"):
        info = plan_b1[pid]
        f2_drv = info["driver_name"]
        f2_sha = info["driver_sha256"]
        env = info["env_str"]
        base_id = info["base_id"] if "base_id" in info else pid.replace("-F2", "").replace("F2-", "")
    elif src == "SUPP_R8_M1b3":
        info = supp_b3[pid]
        f2_drv = info["driver_name"]
        f2_sha = info["driver_sha256"]
        env = info["env"]
        base_id = info["base_id"]
    else:
        raise ValueError(f"Unknown M1b F2 source {src}")

    f2_rows.append([
        "M1b", grp, pid, base_id, "F2", f2_drv, f2_sha, env, "pattern both 4 3",
        eff_cls, eff_v, "checkpoints/p05/registries/s4r8/M1b/r8m1b3/EFFECTIVE_M1B_R8_M1b3.tsv",
        "CITED_R8", "Cited from R8 M1b frozen verdicts (Rule U306)"
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
    exp_p_verdict = facts["exp_point_verdict"]

    f2_rows.append([
        "M1c", grp, pid, base_id, "F2", f2_drv, f2_sha, env, "pattern both 4 3",
        exp_p_verdict, eff_v, "checkpoints/p05/registries/s4r8/M1c/r8m1c3/VERDICT_M1C_R8_M1c3.tsv",
        "CITED_R8", "Cited from R8 M1c frozen verdicts (Rule U306)"
    ])

assert len(f2_rows) == 651
assert len(f4_rows) + len(f2_rows) == 1302

# Assert verdict counts match F3 facts
m1b_f4_verdicts = {}
for r in f4_rows:
    if r[0] == "M1b":
        v = r[-1]
        m1b_f4_verdicts[v] = m1b_f4_verdicts.get(v, 0) + 1
assert m1b_f4_verdicts == {"MATCH": 390, "NOT_REACHED_AS_EXPECTED": 22, "NOT_RUN_AS_EXPECTED": 3}, f"M1b F4 verdicts mismatch: {m1b_f4_verdicts}"

m1c_f4_verdicts = {}
for r in f4_rows:
    if r[0] == "M1c":
        v = r[-1]
        m1c_f4_verdicts[v] = m1c_f4_verdicts.get(v, 0) + 1
assert m1c_f4_verdicts == {"MATCH": 236}, f"M1c F4 verdicts mismatch: {m1c_f4_verdicts}"

# 6. Write PREREG_M1_F4_R9M1.tsv
f4_header = [
    "section", "group", "point_id", "base_id", "tree", "driver_name", "driver_sha256", "env", "argv",
    "exp_class", "exp_rc1", "exp_rc2", "exp_rc3", "exp_hit", "exp_point_verdict",
    "exp_I1", "exp_I2", "exp_I3", "exp_I4", "exp_I5", "exp_I6",
    "status", "basis", "f3_point_id", "f3_driver", "f3_driver_sha256", "f3_effective_verdict"
]

with open(OUT_F4, "w", encoding="utf-8") as fh:
    fh.write("# PREREG_M1_F4_R9M1.tsv -- Pre-registration of F4 M1 regression runs (651 rows; Rule U307)\n")
    fh.write("\t".join(f4_header) + "\n")
    for r in f4_rows:
        fh.write("\t".join(r) + "\n")

f4_sha = sha256_file(OUT_F4)
with open(OUT_F4_SHA, "w", encoding="utf-8") as fh:
    fh.write(f"{f4_sha}  {os.path.basename(OUT_F4)}\n")

now_utc = utc_str()
with open(OUT_F4_TIME, "w", encoding="utf-8") as fh:
    fh.write(f"{now_utc}\n")

print(f"Wrote {OUT_F4} ({len(f4_rows)} rows), sha256={f4_sha}, time={now_utc}")

# 7. Write PREREG_M1_CITED_F2_R9M1.tsv
f2_header = [
    "section", "group", "point_id", "base_id", "tree", "driver_name", "driver_sha256", "env", "argv",
    "f2_class", "f2_verdict", "cited_source", "status", "basis"
]

with open(OUT_F2, "w", encoding="utf-8") as fh:
    fh.write("# PREREG_M1_CITED_F2_R9M1.tsv -- Cited F2 frozen verdicts for M1 baseline (651 rows; Rule U306)\n")
    fh.write("\t".join(f2_header) + "\n")
    for r in f2_rows:
        fh.write("\t".join(r) + "\n")

f2_sha = sha256_file(OUT_F2)
with open(OUT_F2_SHA, "w", encoding="utf-8") as fh:
    fh.write(f"{f2_sha}  {os.path.basename(OUT_F2)}\n")

with open(OUT_F2_TIME, "w", encoding="utf-8") as fh:
    fh.write(f"{now_utc}\n")

print(f"Wrote {OUT_F2} ({len(f2_rows)} rows), sha256={f2_sha}, time={now_utc}")

# 8. Write ENGINE_COLUMNS_R9M1.txt
engine_text = f"""# ENGINE_COLUMNS_R9M1.txt -- Audit of exp_* columns evaluated by M1 verdict engines (Step S-D)
# Generated: {now_utc}
# References: judge_d003.py, recheck_f3_r8m1c4.py, verdict_m1c_r8m1c3.py

1. Columns read and strictly compared across all points:
   - exp_rc1: Checked for equality against first run return code rc1.
   - exp_rc2: Checked for equality against retry return code rc2.
   - exp_hit: Checked for equality against fault injection hit count.
   - exp_class / exp_point_verdict: Checked against judge_d003 classification or point verdict.

2. Columns conditionally read for specific subsets:
   - exp_rc3:
     * Read for: M1c G5 3-call state points (r6bstate driver with third call).
     * Ignored for: M1b all points (1-call/2-call drivers without rc3) and M1c G6/G6c/CTRL_AUX (seam points without rc3). Marked as '-' in those rows.
   - exp_I1, exp_I2, exp_I3, exp_I4, exp_I5, exp_I6 (State Invariants):
     * Read for: M1c G5 points where state analyzer executes and dumps call states.
     * Ignored for: M1b all points (no state analyzer dump) and M1c G6/G6c/CTRL_AUX (seam tests without state analyzer; evaluated as N/A). Marked as '-' in those rows.

3. Columns not read by the verdict engine across any row:
   - exp_I7:
     * Status in frozen table: Marked as 'DEFERRED'.
     * Engine behavior: Not included in invariant check list INV = [I1..I6]. Never evaluated.
   - exp_san:
     * Not present in M1 fact tables (M1 contains no AddressSanitizer/UBSan fault injection points).

Summary of Totals:
   - PREREG_M1_F4_R9M1.tsv: 651 rows (M1b: 415, M1c: 236)
   - PREREG_M1_CITED_F2_R9M1.tsv: 651 rows (M1b: 415, M1c: 236)
   - Combined total: 1302 rows
"""

with open(OUT_ENG, "w", encoding="utf-8") as fh:
    fh.write(engine_text)

print(f"Wrote {OUT_ENG}")
sys.exit(0)
