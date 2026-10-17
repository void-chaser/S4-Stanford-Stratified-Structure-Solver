#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# posctrl_r9m1.py -- Positive control for comparison/verdict engine (Step S-E). New file.
import os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1"))
TMP_DIR = os.path.join(EV, "tmp")
os.makedirs(TMP_DIR, exist_ok=True)

OUT_TXT = os.path.join(EV, "POSCTRL_M1_R9M1.txt")
CMP_SCRIPT = os.path.join(REPO, "testing/d003/stage_s4r9/compare_f3_f4_r9m1.py")

log_lines = ["# POSCTRL_M1_R9M1.txt -- Positive control for comparison engine (Step S-E)\n\n"]

# --- Step 1: Clean run (F3 frozen facts as input) ---
print("Running Step 1: Clean comparison (expect DIFFS=0)...")
clean_out_tsv = os.path.join(TMP_DIR, "posctrl_clean.tsv")
cmd1 = ["python3", "-I", "-B", CMP_SCRIPT, "--out", clean_out_tsv]
p1 = subprocess.run(cmd1, cwd=REPO, capture_output=True, text=True)
rc1 = p1.returncode

log_lines.append(f"=== Case 1: Untampered F3 facts as input ===\n")
log_lines.append(f"Command: {' '.join(cmd1)}\n")
log_lines.append(f"Exit code: {rc1}\n")
log_lines.append(f"Stdout:\n{p1.stdout}\n")

assert rc1 == 0, f"Case 1 failed: exit code {rc1} != 0"
assert "DIFFS=0" in p1.stdout, f"Case 1 failed: expected DIFFS=0, got: {p1.stdout}"
print("Step 1 PASS: DIFFS=0.")

# --- Step 2: Tampered copy (1 rc1, 1 I-item) ---
print("Preparing Step 2: Tampered copy...")
# Import load_f3_facts from compare_f3_f4_r9m1
sys.path.insert(0, os.path.dirname(CMP_SCRIPT))
import compare_f3_f4_r9m1 as cmp_mod

f3_facts = cmp_mod.load_f3_facts()

# Select 1 row in M1b to tamper rc1
tampered_rc1_key = ("M1b", "G7", "M1-G7-F3-fftnv-ng1-m1")
assert tampered_rc1_key in f3_facts, f"Key {tampered_rc1_key} not in f3_facts"
orig_rc1 = f3_facts[tampered_rc1_key]["rc1"]

# Select 1 row in M1c to tamper I1
tampered_i_key = ("M1c", "G5", "M-once-closed1d-malloc-1-F3")
assert tampered_i_key in f3_facts, f"Key {tampered_i_key} not in f3_facts"
orig_i1 = f3_facts[tampered_i_key]["I1"]

# Create tampered TSV in $EV/tmp
tampered_tsv = os.path.join(TMP_DIR, "posctrl_tampered_facts.tsv")
header = [
    "section", "group", "point_id", "f3_point_id",
    "rc1", "rc2", "rc3", "hit", "class",
    "I1", "I2", "I3", "I4", "I5", "I6", "env"
]

tampered_count = 0
with open(tampered_tsv, "w", encoding="utf-8") as fh:
    fh.write("# Tampered F3 facts copy for positive control\n")
    fh.write("\t".join(header) + "\n")
    for key, f in sorted(f3_facts.items()):
        row = dict(f)
        if key == tampered_rc1_key:
            row["rc1"] = "1" if orig_rc1 != "1" else "20"
            tampered_count += 1
            print(f"  Tampered {key[2]} rc1: {orig_rc1} -> {row['rc1']}")
        if key == tampered_i_key:
            row["I1"] = "RELEASE" if orig_i1 != "RELEASE" else "HOLD"
            tampered_count += 1
            print(f"  Tampered {key[2]} I1: {orig_i1} -> {row['I1']}")
        
        fh.write("\t".join([
            row["section"], row["group"], row["point_id"], row["point_id"],
            row["rc1"], row["rc2"], row["rc3"], row["hit"], row["class"],
            row["I1"], row["I2"], row["I3"], row["I4"], row["I5"], row["I6"], row["env"]
        ]) + "\n")

assert tampered_count == 2, f"Expected 2 tampered items, got {tampered_count}"

print("Running Step 2: Tampered comparison (expect DIFFS=2)...")
tampered_out_tsv = os.path.join(TMP_DIR, "posctrl_tampered.tsv")
cmd2 = ["python3", "-I", "-B", CMP_SCRIPT, "--tamper", tampered_tsv, "--out", tampered_out_tsv]
p2 = subprocess.run(cmd2, cwd=REPO, capture_output=True, text=True)
rc2 = p2.returncode

log_lines.append(f"=== Case 2: Tampered copy (1 rc1, 1 I1) ===\n")
log_lines.append(f"Command: {' '.join(cmd2)}\n")
log_lines.append(f"Exit code: {rc2}\n")
log_lines.append(f"Stdout:\n{p2.stdout}\n")

assert rc2 == 2, f"Case 2 failed: expected exit code 2 (DIFFS=2), got {rc2}"
assert "DIFFS=2" in p2.stdout, f"Case 2 failed: expected DIFFS=2, got: {p2.stdout}"

# Verify exactly the two expected diff fields were found in the output TSV
diff_rows = []
with open(tampered_out_tsv, "r", encoding="utf-8") as fh:
    lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
    h = lines[0]
    for l in lines[1:]:
        r = dict(zip(h, l))
        if r["row_verdict"] == "DIFF":
            diff_rows.append(r)

assert len(diff_rows) == 2, f"Expected 2 DIFF rows, got {len(diff_rows)}"
diff_map = {r["point_id_f3"]: r["difference_fields"] for r in diff_rows}
assert diff_map.get(tampered_rc1_key[2]) == "rc1", f"Expected rc1 diff, got {diff_map.get(tampered_rc1_key[2])}"
assert diff_map.get(tampered_i_key[2]) == "I1", f"Expected I1 diff, got {diff_map.get(tampered_i_key[2])}"

log_lines.append("Verification: Exactly 2 differences detected (1 rc1 in M1b, 1 I1 in M1c G5).\n")
log_lines.append("Positive control PASS.\n")
print("Step 2 PASS: Exactly 2 differences detected at expected locations.")

with open(OUT_TXT, "w", encoding="utf-8") as fh:
    fh.writelines(log_lines)

print(f"Wrote {OUT_TXT}")
sys.exit(0)
