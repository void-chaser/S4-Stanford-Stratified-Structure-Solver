#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2c; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# audit_gates_r9m2c.py -- Audit all tracked GATE*.txt files in registries for swallowed FAILs (Step S-C-2).
import os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2c"))
os.makedirs(EV, exist_ok=True)
OUT_TSV = os.path.join(EV, "GATE_AUDIT_R9M2c.tsv")

tracked = subprocess.check_output(["git", "ls-files", "checkpoints/p05/registries/"], cwd=REPO, text=True).splitlines()
gate_txts = sorted([p for p in tracked if os.path.basename(p).startswith("GATE") and p.endswith(".txt")])

results = []
swallowed = []

for rel_p in gate_txts:
    full_p = os.path.join(REPO, rel_p)
    raw = open(full_p, "r", errors="replace", encoding="utf-8").read()
    lines = raw.splitlines()
    fail_lines = [l for l in lines if l.startswith("FAIL\t")]
    last_line = ""
    for l in reversed(lines):
        if l.strip():
            last_line = l.strip()
            break
    
    fails_val = None
    m = re.match(r"^FAILS=([0-9]+)", last_line)
    if m:
        fails_val = int(m.group(1))

    if fails_val is None:
        st = "NO_FAILS_LINE"
        val_str = "NO_FAILS_LINE"
    elif len(fail_lines) == fails_val:
        st = "CONSISTENT"
        val_str = str(fails_val)
    else:
        st = "INCONSISTENT"
        val_str = str(fails_val)

    if len(fail_lines) > 0 and fails_val == 0:
        swallowed.append((rel_p, len(fail_lines), val_str, st))

    results.append((rel_p, str(len(fail_lines)), val_str, st))

with open(OUT_TSV, "w", encoding="utf-8") as f:
    f.write("# GATE_AUDIT_R9M2c.tsv -- Complete scan of tracked GATE*.txt files in checkpoints/p05/registries (Step S-C-2)\n")
    f.write("# Total tracked GATE*.txt files: %d\n" % len(results))
    f.write("# Swallowed FAIL files (FAIL lines > 0 and FAILS == 0): %d\n" % len(swallowed))
    for p, c, val, st in swallowed:
        f.write("# SWALLOWED: %s (fail_lines=%s, fails_val=%s, status=%s)\n" % (p, c, val, st))
    f.write("filepath\tfail_lines_count\tlast_line_fails\tconsistency\n")
    for r in results:
        f.write("\t".join(r) + "\n")

print(f"Gate audit complete. Total scanned: {len(results)}. Swallowed count: {len(swallowed)}.")
print(f"Output written to {OUT_TSV}")
