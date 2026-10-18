#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# summarize_m1_r9m1r2.py -- Consolidate M1 summary table across F4 regression and cited F2 baseline (Step S-H, Rule U316). New file.
import csv, os, sys
from collections import Counter

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r2"))
os.makedirs(EV, exist_ok=True)

OUT_TSV = os.path.join(EV, "M1_SUMMARY_F4_R9M1R2.tsv")

# 1. Load F4 verdict rows
f4_path = os.path.join(EV, "VERDICT_M1_F4_R9M1R2.tsv")
with open(f4_path, encoding="utf-8") as fh:
    lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
    h4 = lines[0]
    f4_rows = [dict(zip(h4, l)) for l in lines[1:]]

assert len(f4_rows) == 651, f"Expected 651 F4 rows, got {len(f4_rows)}"

# 2. Load Cited F2 rows
f2_path = os.path.join(EV, "PREREG_M1_CITED_F2_R9M1R2.tsv")
with open(f2_path, encoding="utf-8") as fh:
    lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
    h2 = lines[0]
    f2_rows = [dict(zip(h2, l)) for l in lines[1:]]

assert len(f2_rows) == 651, f"Expected 651 F2 rows, got {len(f2_rows)}"

total_rows = len(f4_rows) + len(f2_rows)
assert total_rows == 1302, f"Total rows {total_rows} != 1302"

# 3. Aggregate M1b and M1c breakdown
m1b_f4 = [r for r in f4_rows if r["section"] == "M1b"]
m1b_f2 = [r for r in f2_rows if r["section"] == "M1b"]
m1c_f4 = [r for r in f4_rows if r["section"] == "M1c"]
m1c_f2 = [r for r in f2_rows if r["section"] == "M1c"]

assert len(m1b_f4) == 415 and len(m1b_f2) == 415
assert len(m1c_f4) == 236 and len(m1c_f2) == 236
assert len(m1b_f4) + len(m1b_f2) == 830
assert len(m1c_f4) + len(m1c_f2) == 472

# Counts by group, tree, class for M1b
m1b_class_counts = Counter()
for r in m1b_f4:
    # use pass1 class
    m1b_class_counts[(r["group"], "F4", r["pass1_class"])] += 1
for r in m1b_f2:
    m1b_class_counts[(r["group"], "F2", r["exp_class"])] += 1

# Counts by group, tree, verdict for M1c
m1c_verdict_counts = Counter()
for r in m1c_f4:
    m1c_verdict_counts[(r["group"], "F4", r["verdict"])] += 1
for r in m1c_f2:
    m1c_verdict_counts[(r["group"], "F2", r["f3_effective_verdict"])] += 1

# Verdict overall counts
m1b_v_counts = Counter()
for r in m1b_f4: m1b_v_counts[r["verdict"]] += 1
for r in m1b_f2: m1b_v_counts[r["f3_effective_verdict"]] += 1

m1c_v_counts = Counter()
for r in m1c_f4: m1c_v_counts[r["verdict"]] += 1
for r in m1c_f2: m1c_v_counts[r["f3_effective_verdict"]] += 1

totals = Counter()
for k, v in m1b_v_counts.items(): totals[k] += v
for k, v in m1c_v_counts.items(): totals[k] += v

# Assertions
assert m1b_v_counts["MATCH"] == 780
assert m1b_v_counts["NOT_REACHED_AS_EXPECTED"] == 44
assert m1b_v_counts["NOT_RUN_AS_EXPECTED"] == 6
assert m1c_v_counts["MATCH"] == 472
assert totals["MATCH"] == 1252
assert totals["NOT_REACHED_AS_EXPECTED"] == 44
assert totals["NOT_RUN_AS_EXPECTED"] == 6
assert totals["MISMATCH"] == 0
assert totals["FLAKY"] == 0
assert sum(totals.values()) == 1302

# Write TSV
with open(OUT_TSV, "w", encoding="utf-8") as fh:
    fh.write("# M1_SUMMARY_F4_R9M1R2.tsv -- Consolidated M1 summary: F4 regression (651) + Cited F2 baseline (651) = 1302 rows (Rule U316)\n")
    fh.write("# sources: M1b = VERDICT_M1_F4_R9M1R2.tsv (F4 415) + PREREG_M1_CITED_F2_R9M1R2.tsv (F2 415); M1c = VERDICT_M1_F4_R9M1R2.tsv (F4 236) + PREREG_M1_CITED_F2_R9M1R2.tsv (F2 236)\n")
    fh.write("section\tgroup\ttree\tclass\tcount\n")
    for (grp, tree, cls), cnt in sorted(m1b_class_counts.items()):
        fh.write(f"M1B_CLASS_P1\t{grp}\t{tree}\t{cls}\t{cnt}\n")
    for (grp, tree, v), cnt in sorted(m1c_verdict_counts.items()):
        fh.write(f"M1C_VERDICT\t{grp}\t{tree}\t{v}\t{cnt}\n")

    fh.write("section\tsource\tclass\tcount\n")
    for v in ["MATCH", "NOT_REACHED_AS_EXPECTED", "NOT_RUN_AS_EXPECTED", "MISMATCH", "FLAKY", "OTHER"]:
        fh.write(f"M1B_VERDICT\teffective_verdict\t{v}\t{m1b_v_counts.get(v, 0)}\n")
    for v in ["MATCH", "NOT_REACHED_AS_EXPECTED", "NOT_RUN_AS_EXPECTED", "MISMATCH", "FLAKY", "OTHER"]:
        fh.write(f"M1C_VERDICT\tverdict\t{v}\t{m1c_v_counts.get(v, 0)}\n")

    fh.write("section\tmetric\tvalue\n")
    fh.write(f"TOTALS\tMATCH\t{totals['MATCH']}\n")
    fh.write(f"TOTALS\tNOT_REACHED_AS_EXPECTED\t{totals['NOT_REACHED_AS_EXPECTED']}\n")
    fh.write(f"TOTALS\tNOT_RUN_AS_EXPECTED\t{totals['NOT_RUN_AS_EXPECTED']}\n")
    fh.write(f"TOTALS\tMISMATCH\t{totals.get('MISMATCH', 0)}\n")
    fh.write(f"TOTALS\tFLAKY\t{totals.get('FLAKY', 0)}\n")
    fh.write(f"TOTALS\tTOTAL\t{sum(totals.values())}\n")

    fh.write("ASSERTION\tM1B_SUM_EQ_830\tTRUE\n")
    fh.write("ASSERTION\tM1C_SUM_EQ_472\tTRUE\n")
    fh.write("ASSERTION\tGRAND_TOTAL_EQ_1302\tTRUE\n")

print(f"M1 Summary: 1302 total rows (MATCH {totals['MATCH']}, NOT_REACHED {totals['NOT_REACHED_AS_EXPECTED']}, NOT_RUN {totals['NOT_RUN_AS_EXPECTED']}, MISMATCH 0, FLAKY 0).")
print(f"Wrote {OUT_TSV}.")
