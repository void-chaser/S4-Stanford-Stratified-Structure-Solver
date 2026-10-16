#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m0; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# effective_set_r9.py -- Extract 202 effective F3 rows for P05-S4 R9 and assert H-3 counts.
import os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m0"))
os.makedirs(EV, exist_ok=True)
OUT_TSV = os.path.join(EV, "M2_EFFECTIVE_F3_R9.tsv")

def read_tsv(path):
    rows = []
    header = None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\r\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if header is None:
                header = parts
            else:
                row = dict(zip(header, parts))
                rows.append(row)
    return header, rows

# 1. Read consolidated table
cons_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2e", "M2_CONSOLIDATED_R8_M2e.tsv")
_, cons_rows = read_tsv(cons_path)

# Filter effective rows (consolidation_status does not contain SUPERSEDED)
effective_rows = [r for r in cons_rows if "SUPERSEDED" not in r.get("consolidation_status", "")]
if len(effective_rows) != 202:
    raise AssertionError(f"Expected 202 effective rows, got {len(effective_rows)}")

# 2. Read prereg sources
prereg_b_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2b", "PREREG_M2_COMBINED_174_R8_M2b.tsv")
prereg_c_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2c", "PREREG_M2_DELTA_R8_M2c.tsv")
prereg_d_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2d", "PREREG_M2_DELTA_R8_M2d.tsv")
prereg_e_formal_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2e", "PREREG_EFFECTIVE_FORMAL_R8_M2e.tsv")
prereg_e_delta_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2e", "PREREG_M2_DELTA_R8_M2e.tsv")

_, b_rows = read_tsv(prereg_b_path)
_, c_rows = read_tsv(prereg_c_path)
_, d_rows = read_tsv(prereg_d_path)
canonical_header, e_formal_rows = read_tsv(prereg_e_formal_path)
_, e_delta_rows = read_tsv(prereg_e_delta_path)

map_b = {r["point_id"]: r for r in b_rows}
map_c = {r["point_id"]: r for r in c_rows}
map_d = {r["point_id"]: r for r in d_rows}
map_e_formal = {r["point_id"]: r for r in e_formal_rows}
map_e_delta = {r["point_id"]: r for r in e_delta_rows}

# Canonical columns (57 columns from PREREG_EFFECTIVE_FORMAL_R8_M2e.tsv)
full_header = canonical_header + ["origin", "verdict_source", "consolidation_status"]

resolved_rows = []
driver_tree_counts = {}
gdb_counts = {}
soln_f3_count = 0
non_soln_f3_count = 0
non_soln_b_f2_count = 0
soln_b_count = 0

for eff in effective_rows:
    pid = eff["point_id"]
    src = eff["verdict_source"]
    prereg = None
    if src == "formal_r8m2b":
        prereg = map_b.get(pid)
    elif src == "formal_r8m2c":
        prereg = map_c.get(pid)
    elif src == "formal_r8m2d":
        prereg = map_d.get(pid)
    elif src == "formal_r8m2e":
        prereg = map_e_formal.get(pid) or map_e_delta.get(pid)
    
    if not prereg:
        raise AssertionError(f"Could not resolve prereg row for {pid} with verdict_source={src}")

    row = {}
    for col in canonical_header:
        row[col] = prereg.get(col, "-")
    row["origin"] = eff.get("origin", "-")
    row["verdict_source"] = src
    row["consolidation_status"] = eff.get("consolidation_status", "-")
    resolved_rows.append(row)

    tree = row["tree"]
    driver = row["driver"]
    pair = f"{tree}:{driver}"
    driver_tree_counts[pair] = driver_tree_counts.get(pair, 0) + 1

    gdb = row.get("gdb_script", "-")
    gdb_counts[gdb] = gdb_counts.get(gdb, 0) + 1

    is_soln = pid.startswith("SOLN-")
    if tree == "F3":
        if is_soln:
            soln_f3_count += 1
        else:
            non_soln_f3_count += 1
    elif tree in ("B", "F2"):
        if is_soln:
            soln_b_count += 1
        else:
            non_soln_b_f2_count += 1

# Assertions per H-3:
expected_tree_drivers = {
    "B:init-B-dbg": 9,
    "B:r6dnv1-B-dbg": 1,
    "F2:seam-fmmret-F2": 1,
    "F3:d003-F3-plain": 72,
    "F3:d003plan-F3-plain": 9,
    "F3:dual-F3-dbg": 2,
    "F3:init-F3-dbg": 18,
    "F3:init-F3-san": 12,
    "F3:init-F3-san-AL": 3,
    "F3:layers-F3-dbg": 8,
    "F3:layers-dual-F3-dbg": 2,
    "F3:nan-F3": 3,
    "F3:polyinj-F3-dbg": 17,
    "F3:polyinj-F3-san": 6,
    "F3:r6bseam-seamF-F3": 6,
    "F3:r6bstate-F3-dbg": 13,
    "F3:r6bstate-F3-san": 13,
    "F3:seam-fmmret-F3": 1,
    "F3:seamF-F3-san": 6,
}

if driver_tree_counts != expected_tree_drivers:
    raise AssertionError(f"Driver/tree distribution mismatch: actual={driver_tree_counts}, expected={expected_tree_drivers}")

if soln_f3_count != 18:
    raise AssertionError(f"Expected 18 SOLN on F3, got {soln_f3_count}")
if non_soln_f3_count != 173:
    raise AssertionError(f"Expected 173 non-SOLN on F3, got {non_soln_f3_count}")
if non_soln_b_f2_count != 2:
    raise AssertionError(f"Expected 2 non-SOLN on B/F2, got {non_soln_b_f2_count}")
if soln_b_count != 9:
    raise AssertionError(f"Expected 9 SOLN on B, got {soln_b_count}")

expected_gdb_counts = {
    "-": 145,
    "testing/d003/stage_s4/r6c_state_r8m2a3.gdb": 38,
    "testing/d003/stage_s4/r6c_state_bt_r8m2d.gdb": 18,
    "testing/d003/stage_s4/m210_b_r8m2a2_R2.gdb": 1,
}

if gdb_counts != expected_gdb_counts:
    raise AssertionError(f"GDB script counts mismatch: actual={gdb_counts}, expected={expected_gdb_counts}")

# Write output TSV
with open(OUT_TSV, "w", encoding="utf-8") as fh:
    fh.write("# M2_EFFECTIVE_F3_R9.tsv -- P05-S4 R9 effective 202 F3 points extracted from r8m2e consolidated table\n")
    fh.write("\t".join(full_header) + "\n")
    for row in resolved_rows:
        fh.write("\t".join(str(row[col]) for col in full_header) + "\n")

print(f"SUCCESS: Extracted {len(resolved_rows)} effective rows -> {OUT_TSV}")
print(f"  F3 SOLN: {soln_f3_count}")
print(f"  F3 non-SOLN: {non_soln_f3_count}")
print(f"  B/F2 non-SOLN: {non_soln_b_f2_count}")
print(f"  B SOLN: {soln_b_count}")
print("  All H-3 assertions PASS.")
