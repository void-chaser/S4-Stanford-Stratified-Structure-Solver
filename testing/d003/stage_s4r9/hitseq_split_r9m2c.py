#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2c; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# hitseq_split_r9m2c.py -- Split HITSEQ into BOTH_EMPTY, NONEMPTY_IDENTICAL, DIFFERENT and verify U303 (Step S-C-5).
import os, re, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2c"))
os.makedirs(EV, exist_ok=True)
OUT_TSV = os.path.join(EV, "HITSEQ_SPLIT_R9M2c.tsv")
OUT_SUMMARY = os.path.join(EV, "HITSEQ_SPLIT_SUMMARY_R9M2c.txt")

EMPTY_SHA = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
IN_TSV = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M2b", "HITSEQ_F3_F4_R9M2b.tsv")

rows = []
with open(IN_TSV, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("point_id\t"):
            continue
        parts = line.split("\t")
        p_id, ps, f4_dir, f3_dir, s4, s3, eq = parts
        
        if s4 == EMPTY_SHA and s3 == EMPTY_SHA:
            cat = "BOTH_EMPTY"
        elif s4 == s3:
            cat = "NONEMPTY_IDENTICAL"
        else:
            cat = "DIFFERENT"
            
        rows.append({
            "point_id": p_id,
            "pass": int(ps),
            "f4_dir": f4_dir,
            "f3_dir": f3_dir,
            "f4_hit_sha256": s4,
            "f3_hit_sha256": s3,
            "category": cat
        })

assert len(rows) == 346, f"Expected 346 rows, got {len(rows)}"

# Summary by item
item_summary = {}
for r in rows:
    pid = r["point_id"]
    # Determine item prefix
    # e.g. M2-01-01-F4 -> M2-01
    m = re.match(r"^(M2-[0-9]+[a-z]?)", pid)
    item = m.group(1) if m else "OTHER"
    cat = r["category"]
    
    if item not in item_summary:
        item_summary[item] = {"BOTH_EMPTY": 0, "NONEMPTY_IDENTICAL": 0, "DIFFERENT": 0, "TOTAL": 0}
    item_summary[item][cat] += 1
    item_summary[item]["TOTAL"] += 1

# NO_SEQ 10 groups mapping
NO_SEQ_MAP = [
    ("KGRP-001", ["M2-07-INJ-closed1d-ng5-F4"]),
    ("KGRP-002", ["M2-07-INJ-closed2d-ng5-F4"]),
    ("KGRP-003", ["M2-07-INJ-experimental-ng5-F4"]),
    ("KGRP-004", ["M2-07-INJ-fft-ng5-F4"]),
    ("KGRP-005", ["M2-07-INJ-kottke-ng5-F4"]),
    ("KGRP-006", ["M2-07-INJ-tensor-ng5-F4"]),
    ("KGRP-007", ["M2-07-INJ-jones-ng5-F4"]),
    ("KGRP-008", ["M2-07-INJ-nv-ng5-F4"]),
    ("KGRP-009", ["M2-07-INJ-vl-ng5-F4"]),
    ("KGRP-025", ["M2-06-DIAG-01-F4", "M2-06-01-F4-C"]),
]

# Index rows by (point_id, pass)
row_idx = {}
for r in rows:
    row_idx[(r["point_id"], r["pass"])] = r["category"]

u303_results = []
all_u303_ok = True

for gid, pts in NO_SEQ_MAP:
    grp_ok = True
    pt_details = []
    for pt in pts:
        p1 = row_idx.get((pt, 1), "MISSING")
        p2 = row_idx.get((pt, 2), "MISSING")
        if p1 != "NONEMPTY_IDENTICAL" or p2 != "NONEMPTY_IDENTICAL":
            grp_ok = False
        pt_details.append(f"{pt}(pass1={p1},pass2={p2})")
    
    verdict = "SUBSTITUTE_OK" if grp_ok else "SUBSTITUTE_NOT_MET"
    if not grp_ok:
        all_u303_ok = False
    u303_results.append((gid, "; ".join(pts), "; ".join(pt_details), verdict))

# Write detailed TSV
with open(OUT_TSV, "w", encoding="utf-8") as out:
    out.write("# HITSEQ_SPLIT_R9M2c.tsv -- Detailed HIT classification (Step S-C-5)\n")
    out.write("point_id\tpass\tf4_dir\tf3_dir\tf4_hit_sha256\tf3_hit_sha256\tcategory\n")
    for r in rows:
        out.write(f"{r['point_id']}\t{r['pass']}\t{r['f4_dir']}\t{r['f3_dir']}\t{r['f4_hit_sha256']}\t{r['f3_hit_sha256']}\t{r['category']}\n")

# Write summary text
total_empty = sum(1 for r in rows if r["category"] == "BOTH_EMPTY")
total_nonempty = sum(1 for r in rows if r["category"] == "NONEMPTY_IDENTICAL")
total_diff = sum(1 for r in rows if r["category"] == "DIFFERENT")

with open(OUT_SUMMARY, "w", encoding="utf-8") as out:
    out.write("# HITSEQ_SPLIT_SUMMARY_R9M2c.txt -- Summary of HIT equivalence and U303 evaluation (Step S-C-5)\n\n")
    out.write("=== Overall Totals ===\n")
    out.write(f"Total checked rows: {len(rows)} (173 points x 2 passes)\n")
    out.write(f"BOTH_EMPTY: {total_empty}\n")
    out.write(f"NONEMPTY_IDENTICAL: {total_nonempty}\n")
    out.write(f"DIFFERENT: {total_diff}\n\n")
    
    out.write("=== Per-Item Breakdown ===\n")
    out.write("item\tBOTH_EMPTY\tNONEMPTY_IDENTICAL\tDIFFERENT\tTOTAL\n")
    for item in sorted(item_summary.keys()):
        d = item_summary[item]
        out.write(f"{item}\t{d['BOTH_EMPTY']}\t{d['NONEMPTY_IDENTICAL']}\t{d['DIFFERENT']}\t{d['TOTAL']}\n")
    out.write("\n")
    
    out.write("=== U303 Evaluation for 10 NO_SEQ Groups ===\n")
    out.write("group_id\tpoints\tdetails\tsubstitute_verdict\n")
    for gid, pts_s, det, verd in u303_results:
        out.write(f"{gid}\t{pts_s}\t{det}\t{verd}\n")
    out.write("\n")
    out.write(f"All 10 NO_SEQ groups satisfy U303: {'YES (SUBSTITUTE_OK 10/10)' if all_u303_ok else 'NO'}\n")

print(f"HITSEQ split complete. Total: {len(rows)}, BOTH_EMPTY: {total_empty}, NONEMPTY_IDENTICAL: {total_nonempty}, DIFFERENT: {total_diff}")
print(f"U303 10 groups result: {'ALL SUBSTITUTE_OK' if all_u303_ok else 'SOME NOT MET'}")
print(f"Output TSV: {OUT_TSV}")
print(f"Output summary: {OUT_SUMMARY}")
