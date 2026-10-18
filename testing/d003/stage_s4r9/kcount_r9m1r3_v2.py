#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# kcount_r9m1r3_v2.py -- K hit count supplementary verification and coverage table for M1 (Rule U321, Step S-D). New file per Rule 3.
import csv, hashlib, os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r3"))
EV_TMP = os.path.join(EV, "tmp")
os.makedirs(EV_TMP, exist_ok=True)

OUT_K_COUNT = os.path.join(EV, "K_COUNT_R9M1R3.tsv")
OUT_K_COVERAGE = os.path.join(EV, "K_COVERAGE_R9M1R3.tsv")

# 1. Verify kmap driver sha256 against BUILD_KMAP_R9M1R2.tsv
kmap_build_tsv = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M1R2/BUILD_KMAP_R9M1R2.tsv")
kmap_expected_sha = {}
with open(kmap_build_tsv, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("driver_name\t"):
            continue
        parts = line.split("\t")
        kmap_expected_sha[parts[0]] = parts[2]

def sha256_file(p):
    if not os.path.isfile(p): return "MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            c = f.read(65536)
            if not c: break
            h.update(c)
    return h.hexdigest()

kmap_paths = {
    "d003-F3-kmap-dbg": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1r2/build/d003-F3-kmap-dbg"),
    "d003-F4-kmap-dbg": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1r2/build/d003-F4-kmap-dbg"),
    "d003plan-F3-kmap-dbg": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1r2/build/d003plan-F3-kmap-dbg"),
    "d003plan-F4-kmap-dbg": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1r2/build/d003plan-F4-kmap-dbg"),
}

for name, p in kmap_paths.items():
    exp_sha = kmap_expected_sha[name]
    act_sha = sha256_file(p)
    assert act_sha == exp_sha, f"SHA256 mismatch for kmap driver {name}: expected {exp_sha}, got {act_sha}"
print("Verified all 4 kmap drivers sha256 match BUILD_KMAP_R9M1R2.tsv.")

# 2. Plain driver paths
plain_paths = {
    "d003-F3-plain": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r8/drivers_r8/d003-F3-plain/driver"),
    "d003-F4-plain": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m0/build/d003-F4-plain"),
    "d003plan-F3-plain": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r8/drivers_r8/d003plan-F3-plain/driver"),
    "d003plan-F4-plain": os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m0/build/d003plan-F4-plain"),
}

# 3. Load 26 d003/d003plan groups from K_INHERIT_R9M1R2.tsv
k_path = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M1R2/K_INHERIT_R9M1R2.tsv")
lines = [l.strip().split("\t") for l in open(k_path, encoding="utf-8") if l.strip() and not l.startswith("#")]
k_header = lines[0]
all_k_groups = [dict(zip(k_header, l)) for l in lines[1:]]
d003_groups = [g for g in all_k_groups if g["driver_family"] in ("d003", "d003plan")]
assert len(d003_groups) == 26, f"Expected 26 groups, got {len(d003_groups)}"

def count_hits(exe, env_str, bp):
    cmd_file = os.path.join(EV_TMP, f"cmd_{os.path.basename(exe)}.cmd")
    with open(cmd_file, "w") as f:
        f.write("set pagination off\n")
        f.write("set confirm off\n")
        f.write("set $cnt = 0\n")
        f.write(f"break {bp}\n")
        f.write("commands\n")
        f.write("silent\n")
        f.write("set $cnt = $cnt + 1\n")
        f.write("continue\n")
        f.write("end\n")
        f.write("run pattern both 4 3\n")
        f.write('printf "TOTAL_HITS=%d\\n", $cnt\n')
        f.write("quit\n")
    
    env = os.environ.copy()
    for item in env_str.split(";"):
        if "=" in item:
            k, v = item.split("=", 1)
            env[k.strip()] = v.strip()
    
    cmd = ["gdb", "-batch", "-x", cmd_file, "--args", exe, "pattern", "both", "4", "3"]
    r = subprocess.run(cmd, env=env, cwd=REPO, capture_output=True, text=True)
    for l in r.stdout.splitlines():
        if "TOTAL_HITS=" in l:
            try:
                return int(l.split("=")[1])
            except ValueError:
                pass
    return -1

# Run hit counting for all 26 groups
k_count_rows = []
mismatch_groups = []
print(f"Running GDB hit count verification for 26 groups...")

for g in d003_groups:
    gid = g["group_id"]
    fam = g["driver_family"]
    env_str = g["clean_env"]
    bp = g["bp_symbol"]
    k_max = g["k_max"]
    
    f3_plain_exe = plain_paths[f"{fam}-F3-plain"]
    f4_plain_exe = plain_paths[f"{fam}-F4-plain"]
    f3_kmap_exe = kmap_paths[f"{fam}-F3-kmap-dbg"]
    f4_kmap_exe = kmap_paths[f"{fam}-F4-kmap-dbg"]
    
    h_f3_p = count_hits(f3_plain_exe, env_str, bp)
    h_f3_k = count_hits(f3_kmap_exe, env_str, bp)
    h_f4_p = count_hits(f4_plain_exe, env_str, bp)
    h_f4_k = count_hits(f4_kmap_exe, env_str, bp)
    
    match = (h_f3_p == h_f3_k == h_f4_p == h_f4_k and h_f3_p >= 0)
    status = "PASS_EQUAL_HITS" if match else "MISMATCH"
    details = f"F3: plain={h_f3_p} kmap={h_f3_k}; F4: plain={h_f4_p} kmap={h_f4_k}"
    if not match:
        mismatch_groups.append(gid)
    
    k_count_rows.append([
        gid, fam, env_str, bp, str(k_max),
        str(h_f3_p), str(h_f3_k), str(h_f4_p), str(h_f4_k),
        status, details
    ])
    print(f"  {gid} ({fam}): {details} -> {status}")

with open(OUT_K_COUNT, "w", encoding="utf-8") as f:
    f.write("# K_COUNT_R9M1R3.tsv -- Supplementary GDB hit count verification for 26 d003/d003plan groups (Rule U321)" + chr(10))
    f.write(chr(9).join([
        "group_id", "driver_family", "clean_env", "bp_symbol", "k_max",
        "f3_plain_hits", "f3_kmap_hits", "f4_plain_hits", "f4_kmap_hits",
        "status", "details"
    ]) + chr(10))
    for r in k_count_rows:
        f.write(chr(9).join(r) + chr(10))

print(f"Wrote K_COUNT_R9M1R3.tsv ({len(k_count_rows)} rows). Mismatches: {len(mismatch_groups)}.")

# 4. Generate K_COVERAGE_R9M1R3.tsv
prereg_path = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M1R2/PREREG_M1_F4_R9M1R2.tsv")
prereg_lines = [l.strip().split("\t") for l in open(prereg_path, encoding="utf-8") if l.strip() and not l.startswith("#")]
prereg_header = prereg_lines[0]
prereg_rows = [dict(zip(prereg_header, l)) for l in prereg_lines[1:]]

# Build map from group_id to points count
k_groups_map = {g["group_id"]: g for g in all_k_groups}

# Run the exact historical mapping from k_inherit_r9m1.py to reconstruct point assignment
plan_b1_by_pid = {}
with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b1/PLAN_M1B_R8_M1b1.tsv"), encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        plan_b1_by_pid[r["point_id"]] = r

supp_b3_by_pid = {}
with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b3/PREREG_SUPP_R8_M1b3.tsv"), encoding="utf-8") as f:
    lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
    h = lines[0]
    for l in lines[1:]:
        supp_b3_by_pid[dict(zip(h, l))["point_id"]] = dict(zip(h, l))

with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b3/EFFECTIVE_M1B_R8_M1b3.tsv"), encoding="utf-8") as f:
    lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
    eff_m1b = [dict(zip(lines[0], l)) for l in lines[1:] if dict(zip(lines[0], l))["tree"] == "F3"]

with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv"), encoding="utf-8") as f:
    lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
    eff_m1c = [dict(zip(lines[0], l)) for l in lines[1:] if dict(zip(lines[0], l))["tree"] == "F3"]

def clean_base_env(env_str):
    parts = [p.strip() for p in env_str.split(";") if p.strip()]
    kept = []
    for p in parts:
        k = p.split("=")[0]
        if k.startswith("S4FMM_INJECT") or k.startswith("S4FMM_NTH") or k.startswith("S4FMM_TWICE"):
            continue
        kept.append(p)
    return ";".join(sorted(kept))

k_key_to_gid = {(g["driver_family"], g["clean_env"], g["bp_symbol"]): g["group_id"] for g in all_k_groups}

point_key_to_gid = {}

def add_point(sec, grp, drv, env, site, nth, pid):
    if nth == "-" and not site.startswith("init:") and not site.startswith("win:") and not site.startswith("plancall:"):
        return
    if site.startswith("init:") or site.startswith("win:"):
        bp = "__wrap_malloc"
    elif "s4malloc" in site or (nth != "-" and "s4malloc" in env):
        bp = "__wrap__Z9S4_mallocm"
    elif "exec" in site or (nth != "-" and "exec" in env):
        bp = "__wrap__Z13fft_plan_execP12tag_fft_plan"
    elif "plan" in site or (nth != "-" and "plan" in env):
        bp = "__wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i"
    else:
        bp = "__wrap_malloc"

    be = clean_base_env(env)
    fam = drv.replace("-F3-dbg", "").replace("-F3-plain", "").replace("-F3", "")
    key = (fam, be, bp)
    gid = k_key_to_gid.get(key)
    if gid:
        point_key_to_gid[(sec, grp, pid)] = gid

for r in eff_m1b:
    pid = r["point_id"]
    grp = r["group"]
    src = r["source"]
    if src in ("M1b1_ENV_AGREE", "M1b1_NOT_RUN"):
        p = plan_b1_by_pid.get(pid)
        if p:
            add_point("M1b", grp, p["driver_name"], p["env_str"], p["inject_site"], p["k_nth"], pid)
    elif src == "SUPP_R8_M1b3":
        p = supp_b3_by_pid.get(pid)
        if p:
            drv = p["driver_name"]
            env = p["env"]
            site, nth = "none", "-"
            for part in env.split(";"):
                if part.startswith("S4FMM_INJECT="): site = part.split("=")[1]
                if part.startswith("S4FMM_NTH="): nth = part.split("=")[1]
            add_point("M1b", grp, drv, env, site, nth, pid)

for r in eff_m1c:
    drv = r["driver_name"]
    env = r["env_expected"]
    site, nth = "none", "-"
    for part in env.split(";"):
        if part.startswith("S4FMM_INJECT="): site = part.split("=")[1]
        if part.startswith("S4FMM_NTH="): nth = part.split("=")[1]
    add_point("M1c", r["group"], drv, env, site, nth, r["point_id_r8"])

print(f"Mapped {len(point_key_to_gid)} points to K groups.")
assert len(point_key_to_gid) == 416, f"Expected 416 mapped points, got {len(point_key_to_gid)}"

# Verify count reconciliation with all 53 groups
gid_counts = {}
for k, gid in point_key_to_gid.items():
    gid_counts[gid] = gid_counts.get(gid, 0) + 1

for g in all_k_groups:
    gid = g["group_id"]
    exp = int(g["m1_points_count"])
    act = gid_counts.get(gid, 0)
    assert exp == act, f"Group {gid} points count mismatch: expected {exp}, got {act}"

coverage_rows = []
points_in_k = 0
points_no_k = 0

for r in prereg_rows:
    sec = r["section"]
    grp = r["group"]
    pid_f4 = r["point_id"]
    pid_f3 = r["f3_point_id"]
    drv = r["driver_name"]
    env = r["env"]
    eff_v = r["f3_effective_verdict"]

    lookup_key = (sec, grp, pid_f3)
    gid = point_key_to_gid.get(lookup_key)
    if gid is not None:
        needs_k = "YES"
        reason_or_gid = gid
        kg = k_groups_map[gid]
        k_max = kg["k_max"]
        m1_cnt = kg["m1_points_count"]
        points_in_k += 1
    else:
        needs_k = "NO"
        if eff_v == "NOT_RUN_AS_EXPECTED" or env == "NOT_RUN":
            reason = "未运行控制点无需K映射"
        elif grp in ("CTRL_SEAM", "G2c_control", "M1_CTRL", "G6c", "CTRL_AUX"):
            reason = "无注入/控制对照点无需K映射"
        elif "none" in env or r["exp_hit"] == "0":
            reason = "无注入/未触碰点无需K映射"
        elif drv.startswith("seam-") or drv.startswith("r6bseam-"):
            reason = "seam断言桩驱动无需malloc/fft包装K映射"
        elif drv.startswith("tri-") or drv.startswith("poly-"):
            reason = "多边形/几何驱动无需malloc/fft包装K映射"
        elif drv.startswith("r6dnv1-"):
            reason = "张量/RNV1驱动无需malloc/fft包装K映射"
        else:
            reason = "无故障注入单次调用基线点无需K映射"
        reason_or_gid = f"不需要K ({reason})"
        k_max = "-"
        m1_cnt = "-"
        points_no_k += 1

    coverage_rows.append([
        sec, grp, pid_f4, pid_f3, drv, needs_k, reason_or_gid, str(k_max), str(m1_cnt)
    ])

assert len(coverage_rows) == 651, f"Expected 651 coverage rows, got {len(coverage_rows)}"
assert points_in_k == 416, f"Expected 416 points in K, got {points_in_k}"
assert points_no_k == 235, f"Expected 235 points not in K, got {points_no_k}"

with open(OUT_K_COVERAGE, "w", encoding="utf-8") as f:
    f.write("# K_COVERAGE_R9M1R3.tsv -- K group assignment and coverage table for all 651 M1 points (Rule U321)" + chr(10))
    f.write(chr(9).join([
        "section", "group", "point_id_f4", "point_id_f3", "driver_name",
        "needs_k", "k_group_or_reason", "k_max", "group_total_points"
    ]) + chr(10))
    for r in coverage_rows:
        f.write(chr(9).join(r) + chr(10))

print(f"Wrote K_COVERAGE_R9M1R3.tsv (651 rows: 416 in K groups, 235 no-K). Reconciled perfectly with 416.")
