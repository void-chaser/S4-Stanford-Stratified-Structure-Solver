#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# driver_inventory_r9m1.py -- Inventory of F3 drivers used in M1 (F3 side, 651 rows) and map to F4. New file.
import csv, hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1"))
os.makedirs(EV, exist_ok=True)
OUT_TSV = os.path.join(EV, "DRIVERS_F3_SIDE_R9M1.tsv")

def sha256_file(p):
    if not os.path.isfile(p):
        return "MISSING"
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            c = fh.read(65536)
            if not c: break
            h.update(c)
    return h.hexdigest()

# 1. Load M1b F3 rows
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

m1b_f3 = [r for r in eff_m1b if r["tree"] == "F3"]
assert len(m1b_f3) == 415, f"Expected 415 F3 rows in M1b, got {len(m1b_f3)}"

f3_drivers = {}
for r in m1b_f3:
    pid = r["point_id"]
    src = r["source"]
    if src in ("M1b1_ENV_AGREE", "M1b1_NOT_RUN"):
        drv = plan_b1[pid]["driver_name"]
        sha = plan_b1[pid]["driver_sha256"]
        p = plan_b1[pid]["driver_path"]
    elif src == "SUPP_R8_M1b3":
        drv = supp_b3[pid]["driver_name"]
        sha = supp_b3[pid]["driver_sha256"]
        p = supp_b3[pid].get("driver_path", "")
    else:
        raise ValueError(f"Unknown source {src}")
    if drv not in f3_drivers:
        f3_drivers[drv] = {"sha": sha, "path": p, "m1b_count": 0, "m1c_count": 0}
    f3_drivers[drv]["m1b_count"] += 1

# 2. Load M1c F3 rows
with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv"), encoding="utf-8") as f:
    lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
    h = lines[0]
    m1c_f3 = [dict(zip(h, l)) for l in lines[1:] if dict(zip(h, l))["tree"] == "F3"]
assert len(m1c_f3) == 236, f"Expected 236 F3 rows in M1c, got {len(m1c_f3)}"

for r in m1c_f3:
    drv = r["driver_name"]
    sha = r["driver_sha256"]
    if drv not in f3_drivers:
        f3_drivers[drv] = {"sha": sha, "path": "", "m1b_count": 0, "m1c_count": 0}
    f3_drivers[drv]["m1c_count"] += 1

assert sum(d["m1b_count"] for d in f3_drivers.values()) == 415
assert sum(d["m1c_count"] for d in f3_drivers.values()) == 236
assert sum(d["m1b_count"] + d["m1c_count"] for d in f3_drivers.values()) == 651

# 3. Known M0 mapping
M0_MAP = {
    "d003-F3-plain": ("d003-F4-plain", "checkpoints/p05/evidence/p05-s4r9/m0/build/d003-F4-plain", "e39e4b0f4a66b7bf6d19b558636ffbdb76b1e35eec4825c2398600eb35e0d9f6"),
    "d003plan-F3-plain": ("d003plan-F4-plain", "checkpoints/p05/evidence/p05-s4r9/m0/build/d003plan-F4-plain", "41d2d579715c77d595831fde670c171880f198e37eaf52ad27477d65673292e3"),
    "r6bstate-F3-dbg": ("r6bstate-F4-dbg", "checkpoints/p05/evidence/p05-s4r9/m0/build/r6bstate-F4-dbg", "2bce13d9f23276a0153ea8fa30464bf2cbfd99798f5d8336c1c1f8e285b15aa2"),
    "r6bseam-seamF-F3": ("r6bseam-seamF-F4", "checkpoints/p05/evidence/p05-s4r9/m0/build/r6bseam-seamF-F4", "e53560673269090865be502f96aa06fb693f867afdbbfdd3c109eb759547911d"),
    "seam-fmmret-F3": ("seam-fmmret-F4", "checkpoints/p05/evidence/p05-s4r9/m0/build/seam-fmmret-F4", "10e4f2ce7f4df4fb688d032a2b72e784d41fccfe25337a396009a11994178b1c"),
}

# 4. Drivers to build for F4
TO_BUILD_MAP = {
    "init-F3": ("init-F4-plain", "checkpoints/p05/evidence/p05-s4r9/m1/build/init-F4-plain"),
    "poly-F3": ("poly-F4-plain", "checkpoints/p05/evidence/p05-s4r9/m1/build/poly-F4-plain"),
    "polyinj-F3": ("polyinj-F4-plain", "checkpoints/p05/evidence/p05-s4r9/m1/build/polyinj-F4-plain"),
    "r6dnv1-F3-plain": ("r6dnv1-F4-plain", "checkpoints/p05/evidence/p05-s4r9/m1/build/r6dnv1-F4-plain"),
    "seam-seamF-F3": ("seam-seamF-F4", "checkpoints/p05/evidence/p05-s4r9/m1/build/seam-seamF-F4"),
    "tri-F3-dbg": ("tri-F4-dbg", "checkpoints/p05/evidence/p05-s4r9/m1/build/tri-F4-dbg"),
    "r6bseam-fmmret-F3": ("r6bseam-fmmret-F4", "checkpoints/p05/evidence/p05-s4r9/m1/build/r6bseam-fmmret-F4"),
}

rows = []
unmappable_count = 0

for drv in sorted(f3_drivers.keys()):
    v = f3_drivers[drv]
    f3_sha = v["sha"]
    m1b_c = v["m1b_count"]
    m1c_c = v["m1c_count"]
    tot_c = m1b_c + m1c_c
    if drv in M0_MAP:
        f4_drv, f4_path, f4_exp_sha = M0_MAP[drv]
        act_sha = sha256_file(os.path.join(REPO, f4_path))
        assert act_sha == f4_exp_sha, f"M0 artifact {f4_drv} sha mismatch: act={act_sha}, exp={f4_exp_sha}"
        status = "ALREADY_EXISTS"
        f4_sha = act_sha
        target_path = f4_path
    elif drv in TO_BUILD_MAP:
        f4_drv, target_path = TO_BUILD_MAP[drv]
        status = "TO_BUILD"
        f4_sha = "PENDING_BUILD"
    else:
        status = "UNMAPPABLE"
        f4_drv = "NONE"
        target_path = "NONE"
        f4_sha = "NONE"
        unmappable_count += 1
    rows.append([drv, f3_sha, f4_drv, f4_sha, status, target_path, str(m1b_c), str(m1c_c), str(tot_c)])

header = ["f3_driver", "f3_sha256", "f4_driver", "f4_sha256", "status", "f4_target_path", "m1b_rows", "m1c_rows", "total_f3_rows"]

with open(OUT_TSV, "w", encoding="utf-8") as fh:
    fh.write("# DRIVERS_F3_SIDE_R9M1.tsv -- Inventory of F3 drivers used in M1 and their F4 mapping (Step S-B-1)\n")
    fh.write("\t".join(header) + "\n")
    for r in rows:
        fh.write("\t".join(r) + "\n")

print(f"DRIVERS_F3_SIDE_R9M1 written: {len(rows)} drivers, unmappable={unmappable_count} -> {OUT_TSV}")
if unmappable_count != 0:
    print(f"STOP: unmappable drivers found: {unmappable_count}", file=sys.stderr)
    sys.exit(unmappable_count)
sys.exit(0)
