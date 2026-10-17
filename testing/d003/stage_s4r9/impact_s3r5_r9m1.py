#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# impact_s3r5_r9m1.py -- Enumerate all M1 F3-side rows affected by S3R5 (F3 lines 1754-1774) (Rule U308). New file.
import csv, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1"))
os.makedirs(EV, exist_ok=True)
OUT_TSV = os.path.join(EV, "IMPACT_S3R5_R9M1.tsv")

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
    eff_m1b = [dict(zip(lines[0], l)) for l in lines[1:] if dict(zip(lines[0], l))["tree"] == "F3"]

# 2. Load M1c F3 rows
with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv"), encoding="utf-8") as f:
    lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
    h = lines[0]
    eff_m1c = [dict(zip(h, l)) for l in lines[1:] if dict(zip(h, l))["tree"] == "F3"]

assert len(eff_m1b) == 415
assert len(eff_m1c) == 236
total_f3 = len(eff_m1b) + len(eff_m1c)
assert total_f3 == 651

# 3. Check for any points in Simulation_InitSolution (lines 1754-1774 in F3)
# S3R5 modification was strictly inside Simulation_InitSolution (S4.cpp 1760-1774 in F3).
# In M2, these were SOLN-01 to SOLN-18 (M2-01-01 to M2-01-18) targeting malloc at lines 1763, 1764, 1765.
impacted_rows = []

for r in eff_m1b:
    pid = r["point_id"]
    src = r["source"]
    if src in ("M1b1_ENV_AGREE", "M1b1_NOT_RUN"):
        row_data = plan_b1[pid]
    elif src == "SUPP_R8_M1b3":
        row_data = supp_b3[pid]
    s = " ".join(f"{k}={v}" for k, v in row_data.items())
    for lnum in range(1754, 1775):
        if f":{lnum}" in s or f"-{lnum}" in s or f"alloc:{lnum}" in s:
            impacted_rows.append(("M1b", pid, r["group"], lnum, s))

for r in eff_m1c:
    pid = r["point_id_r8"]
    s = " ".join(f"{k}={v}" for k, v in r.items())
    for lnum in range(1754, 1775):
        if f":{lnum}" in s or f"-{lnum}" in s or f"alloc:{lnum}" in s:
            impacted_rows.append(("M1c", pid, r["group"], lnum, s))

print(f"Total F3-side rows examined: {total_f3}")
print(f"Total impacted rows in lines 1754-1774: {len(impacted_rows)}")

# Write output TSV
header = ["table", "point_id", "group", "matched_line", "rule_application", "basis"]
with open(OUT_TSV, "w", encoding="utf-8") as fh:
    fh.write("# IMPACT_S3R5_R9M1.tsv -- S3R5 change impact list for M1 F3 side (Rule U308)\n")
    fh.write(f"# S3R5 change scope: Simulation_InitSolution (F3 lines 1754-1774 in S4.cpp)\n")
    fh.write(f"# Total M1 F3-side rows examined: {total_f3} (M1b: 415, M1c: 236)\n")
    fh.write(f"# Total impacted rows: {len(impacted_rows)} 行\n")
    fh.write("\t".join(header) + "\n")
    for r in impacted_rows:
        fh.write("\t".join(str(x) for x in r) + "\n")

print(f"Wrote {OUT_TSV}: {len(impacted_rows)} 行")
sys.exit(0)
