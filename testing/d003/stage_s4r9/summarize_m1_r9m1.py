#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# summarize_m1_r9m1.py -- Combine F4 regression results with cited F2 baseline to produce M1 summary (Rule U306). New file.
import csv, os, sys
from collections import Counter

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1"))
os.makedirs(EV, exist_ok=True)

OUT_TSV = os.path.join(EV, "M1_SUMMARY_F4_R9M1.tsv")

# 1. Load F4 formal verdicts (651 rows)
f4_verdict_path = os.path.join(EV, "VERDICT_M1_F4_R9M1.tsv")
f4_rows = []
with open(f4_verdict_path, encoding="utf-8") as fh:
    lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
    h = lines[0]
    for l in lines[1:]:
        f4_rows.append(dict(zip(h, l)))

assert len(f4_rows) == 651, f"Expected 651 F4 verdict rows, got {len(f4_rows)}"

# 2. Load cited F2 baseline rows (651 rows)
f2_cited_path = os.path.join(EV, "PREREG_M1_CITED_F2_R9M1.tsv")
f2_rows = []
with open(f2_cited_path, encoding="utf-8") as fh:
    lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
    h = lines[0]
    for l in lines[1:]:
        f2_rows.append(dict(zip(h, l)))

assert len(f2_rows) == 651, f"Expected 651 F2 cited rows, got {len(f2_rows)}"
assert len(f4_rows) + len(f2_rows) == 1302

# 3. Build section aggregates
# M1b: 830 rows = F2 415 + F4 415
m1b_f4 = [r for r in f4_rows if r["section"] == "M1b"]
m1b_f2 = [r for r in f2_rows if r["section"] == "M1b"]
assert len(m1b_f4) == 415
assert len(m1b_f2) == 415
assert len(m1b_f4) + len(m1b_f2) == 830

# M1c: 472 rows = F2 236 + F4 236
m1c_f4 = [r for r in f4_rows if r["section"] == "M1c"]
m1c_f2 = [r for r in f2_rows if r["section"] == "M1c"]
assert len(m1c_f4) == 236
assert len(m1c_f2) == 236
assert len(m1c_f4) + len(m1c_f2) == 472

# Aggregate counts
# Part 1: M1b class breakdown
m1b_class_counts = Counter()
for r in m1b_f2:
    m1b_class_counts[(r["group"], "F2", r["f2_class"])] += 1
for r in m1b_f4:
    m1b_class_counts[(r["group"], "F4", r["pass1_class"])] += 1

assert sum(m1b_class_counts.values()) == 830, f"M1b class sum {sum(m1b_class_counts.values())} != 830"

# Part 2: M1c verdict breakdown
m1c_verdict_counts = Counter()
for r in m1c_f2:
    m1c_verdict_counts[(r["group"], "F2", r["f2_verdict"])] += 1
for r in m1c_f4:
    m1c_verdict_counts[(r["group"], "F4", r["verdict"])] += 1

assert sum(m1c_verdict_counts.values()) == 472, f"M1c verdict sum {sum(m1c_verdict_counts.values())} != 472"

# Part 3: M1b verdict breakdown
m1b_verdict_counts = Counter()
for r in m1b_f2:
    m1b_verdict_counts[r["f2_verdict"]] += 1
for r in m1b_f4:
    m1b_verdict_counts[r["verdict"]] += 1

assert sum(m1b_verdict_counts.values()) == 830, f"M1b verdict sum {sum(m1b_verdict_counts.values())} != 830"
assert m1b_verdict_counts["MATCH"] == 780
assert m1b_verdict_counts["NOT_REACHED_AS_EXPECTED"] == 44
assert m1b_verdict_counts["NOT_RUN_AS_EXPECTED"] == 6

# Part 4: M1c total verdicts
m1c_total_verdicts = Counter()
for r in m1c_f2:
    m1c_total_verdicts[r["f2_verdict"]] += 1
for r in m1c_f4:
    m1c_total_verdicts[r["verdict"]] += 1

assert sum(m1c_total_verdicts.values()) == 472, f"M1c total sum {sum(m1c_total_verdicts.values())} != 472"
assert m1c_total_verdicts["MATCH"] == 472

# Part 5: Grand totals
total_match = m1b_verdict_counts["MATCH"] + m1c_total_verdicts["MATCH"]
total_not_reached = m1b_verdict_counts["NOT_REACHED_AS_EXPECTED"] + m1c_total_verdicts["NOT_REACHED_AS_EXPECTED"]
total_not_run = m1b_verdict_counts["NOT_RUN_AS_EXPECTED"] + m1c_total_verdicts["NOT_RUN_AS_EXPECTED"]
total_mismatch = m1b_verdict_counts.get("MISMATCH", 0) + m1c_total_verdicts.get("MISMATCH", 0)
total_flaky = m1b_verdict_counts.get("FLAKY", 0) + m1c_total_verdicts.get("FLAKY", 0)
grand_total = total_match + total_not_reached + total_not_run + total_mismatch + total_flaky

assert total_match == 1252, f"Expected 1252 MATCH, got {total_match}"
assert total_not_reached == 44, f"Expected 44 NOT_REACHED_AS_EXPECTED, got {total_not_reached}"
assert total_not_run == 6, f"Expected 6 NOT_RUN_AS_EXPECTED, got {total_not_run}"
assert total_mismatch == 0, f"Expected 0 MISMATCH, got {total_mismatch}"
assert total_flaky == 0, f"Expected 0 FLAKY, got {total_flaky}"
assert grand_total == 1302, f"Expected grand total 1302, got {grand_total}"

print("=== M1 GRAND TOTALS VERIFIED ===")
print(f"  MATCH:                   {total_match}")
print(f"  NOT_REACHED_AS_EXPECTED: {total_not_reached}")
print(f"  NOT_RUN_AS_EXPECTED:     {total_not_run}")
print(f"  MISMATCH:                {total_mismatch}")
print(f"  FLAKY:                   {total_flaky}")
print(f"  TOTAL:                   {grand_total}")

# Write M1_SUMMARY_F4_R9M1.tsv
lines = [
    "# M1_SUMMARY_F4_R9M1.tsv -- Consolidated M1 summary: F4 regression (651) + Cited F2 baseline (651) = 1302 rows (Rule U306)",
    "# sources: M1b = VERDICT_M1_F4_R9M1.tsv (F4 415) + PREREG_M1_CITED_F2_R9M1.tsv (F2 415); M1c = VERDICT_M1_F4_R9M1.tsv (F4 236) + PREREG_M1_CITED_F2_R9M1.tsv (F2 236)",
    "section\tgroup\ttree\tclass\tcount"
]

for (grp, tree, cls), count in sorted(m1b_class_counts.items()):
    lines.append(f"M1B_CLASS_P1\t{grp}\t{tree}\t{cls}\t{count}")

for (grp, tree, v), count in sorted(m1c_verdict_counts.items()):
    lines.append(f"M1C_VERDICT\t{grp}\t{tree}\t{v}\t{count}")

lines.append("section\tsource\tclass\tcount")
for v in ["MATCH", "NOT_REACHED_AS_EXPECTED", "NOT_RUN_AS_EXPECTED", "MISMATCH", "FLAKY", "OTHER"]:
    c = m1b_verdict_counts.get(v, 0)
    lines.append(f"M1B_VERDICT\teffective_verdict\t{v}\t{c}")

for v in ["MATCH", "NOT_REACHED_AS_EXPECTED", "NOT_RUN_AS_EXPECTED", "MISMATCH", "FLAKY", "OTHER"]:
    c = m1c_total_verdicts.get(v, 0)
    lines.append(f"M1C_VERDICT\tverdict\t{v}\t{c}")

lines.append("section\tmetric\tvalue")
lines.append(f"TOTALS\tMATCH\t{total_match}")
lines.append(f"TOTALS\tNOT_REACHED_AS_EXPECTED\t{total_not_reached}")
lines.append(f"TOTALS\tNOT_RUN_AS_EXPECTED\t{total_not_run}")
lines.append(f"TOTALS\tMISMATCH\t{total_mismatch}")
lines.append(f"TOTALS\tFLAKY\t{total_flaky}")
lines.append(f"TOTALS\tTOTAL\t{grand_total}")
lines.append(f"ASSERTION\tM1B_SUM_EQ_830\tTRUE")
lines.append(f"ASSERTION\tM1C_SUM_EQ_472\tTRUE")
lines.append(f"ASSERTION\tGRAND_TOTAL_EQ_1302\tTRUE")

with open(OUT_TSV, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")

print(f"Wrote {OUT_TSV} (Total = 1302 rows confirmed).")
sys.exit(0)
