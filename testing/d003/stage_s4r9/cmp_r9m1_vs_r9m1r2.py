#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# cmp_r9m1_vs_r9m1r2.py -- Compare r9m1 reference facts vs r9m1r2 facts row by row (Step S-H, Rule U316). New file.
import csv, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r2"))
os.makedirs(EV, exist_ok=True)

OUT_TSV = os.path.join(EV, "R9M1_VS_R9M1R2_R9M1R2.tsv")

p_r9m1 = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1/runs/formal/FORMAL_FACTS_M1_F4_R9M1_pass1.tsv")
p_r9m1r2 = os.path.join(EV, "runs/formal_R2/FORMAL_FACTS_M1_F4_R9M1R2_pass1.tsv")

def load(p):
    facts = {}
    with open(p, encoding="utf-8") as f:
        lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            r = dict(zip(h, l))
            facts[(r["section"], r["group"], r["point_id"])] = r
    return facts

f_r9m1 = load(p_r9m1)
f_r9m1r2 = load(p_r9m1r2)

assert len(f_r9m1) == 651 and len(f_r9m1r2) == 651

header = [
    "section", "group", "point_id",
    "r9m1_rc1", "r9m1r2_rc1", "r9m1_rc2", "r9m1r2_rc2", "r9m1_hit", "r9m1r2_hit", "r9m1_class", "r9m1r2_class",
    "r9m1_I1", "r9m1r2_I1", "r9m1_I2", "r9m1r2_I2", "r9m1_I3", "r9m1r2_I3",
    "r9m1_I4", "r9m1r2_I4", "r9m1_I5", "r9m1r2_I5", "r9m1_I6", "r9m1r2_I6",
    "status", "diff_fields"
]

rows = []
diff_count = 0
for k in sorted(f_r9m1r2.keys()):
    r1 = f_r9m1[k]
    r2 = f_r9m1r2[k]

    diffs = []
    for fld in ("rc1", "rc2", "rc3", "hit", "class"):
        if r1[fld] != r2[fld]:
            diffs.append(f"{fld}({r1[fld]}!={r2[fld]})")

    for i in range(1, 7):
        fld = f"I{i}"
        if r1[fld] != r2[fld]:
            diffs.append(f"{fld}({r1[fld]}!={r2[fld]})")

    status = "IDENTICAL" if not diffs else "DIFF"
    if diffs: diff_count += 1
    diff_str = ";".join(diffs) if diffs else "NONE"

    rows.append([
        k[0], k[1], k[2],
        r1["rc1"], r2["rc1"], r1["rc2"], r2["rc2"], r1["hit"], r2["hit"], r1["class"], r2["class"],
        r1["I1"], r2["I1"], r1["I2"], r2["I2"], r1["I3"], r2["I3"],
        r1["I4"], r2["I4"], r1["I5"], r2["I5"], r1["I6"], r2["I6"],
        status, diff_str
    ])

with open(OUT_TSV, "w", encoding="utf-8") as fh:
    fh.write("# R9M1_VS_R9M1R2_R9M1R2.tsv -- Row-by-row fact comparison between r9m1 reference and r9m1r2 (Rule U316)\n")
    fh.write("\t".join(header) + "\n")
    for r in rows:
        fh.write("\t".join(r) + "\n")

print(f"R9M1 vs R9M1R2 fact comparison: {len(rows)} rows, {diff_count} rows with differences.")
print(f"Wrote {OUT_TSV}.")
