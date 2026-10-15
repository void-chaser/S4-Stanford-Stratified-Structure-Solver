#!/usr/bin/env python3
# summarize_m1_r8m1c3.py -- P05-S4 R8 M1c3 M1 summary (brief section 7). New file.
# Outputs (in $EV): M1_SUMMARY_R8_M1c3.tsv, FIX_COVERAGE_M1_R8_M1c3.tsv.
# M1b: 830 rows from registries/s4r8/M1b/r8m1b3/EFFECTIVE_M1B_R8_M1b3.tsv (effective_verdict, effective_class_p1),
#      counted by group x tree x class; the U212 rows (SILENT_SWALLOW, CRASH) are listed separately.
# M1c: 472 rows from VERDICT_M1C_R8_M1c3_R3.tsv (the verdict run of this round), counted by group x tree.
# Totals: MATCH, NOT_REACHED_AS_EXPECTED, NOT_RUN, MISMATCH, FLAKY.
# Coverage of 806, 415, RP-S3R4-1: rows whose point id or fix link matches, per the R8 M1a ADDITIONS/SITEMAP tables.
# Usage: python3 -I -B summarize_m1_r8m1c3.py
import os, sys
from collections import Counter, defaultdict

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c3")
REG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8")
os.makedirs(os.path.join(EV, "tmp"), exist_ok=True)
OUT_S = os.path.join(EV, "M1_SUMMARY_R8_M1c3_R2.tsv")
OUT_C = os.path.join(EV, "FIX_COVERAGE_M1_R8_M1c3_R2.tsv")
for p in (OUT_S, OUT_C):
    if os.path.exists(p):
        print("REFUSED exists (U17): %s" % p)
        sys.exit(2)


def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        ls = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
    head = ls[0].split("\t")
    return [dict(zip(head, l.split("\t"))) for l in ls[1:]]


m1b = read_tsv(os.path.join(REG, "M1b", "r8m1b3", "EFFECTIVE_M1B_R8_M1b3.tsv"))
m1c = [r for r in read_tsv(os.path.join(EV, "VERDICT_M1C_R8_M1c3_R3.tsv")) if not r.get("group", "").startswith("ROWS=")]
assert len(m1b) == 830, "M1b rows != 830: %d" % len(m1b)
assert len(m1c) == 472, "M1c rows != 472: %d" % len(m1c)

lines = []
lines.append("# M1_SUMMARY_R8_M1c3 -- M1 totals (M1b effective table 830 rows; M1c frozen table 472 rows).")
lines.append("section\tgroup\ttree\tclass_or_verdict\tcount")

# ---- M1b: group x tree x effective_class_p1 ----
b_cnt = Counter()
b_verdict = Counter()
for r in m1b:
    b_cnt[(r["group"], r["tree"], r["effective_class_p1"])] += 1
    b_verdict[r["effective_verdict"]] += 1
for (g, t, c), n in sorted(b_cnt.items()):
    lines.append("M1b\t%s\t%s\t%s\t%d" % (g, t, c, n))
for v, n in sorted(b_verdict.items()):
    lines.append("M1b_VERDICT\tALL\tALL\t%s\t%d" % (v, n))

# ---- U212 separately: SILENT_SWALLOW and CRASH rows ----
silent = [r for r in m1b if r["effective_class_p1"] == "SILENT_SWALLOW"]
crash = [r for r in m1b if r["effective_class_p1"] == "CRASH"]
lines.append("M1b_U212\tSILENT_SWALLOW\tALL\tALL\t%d" % len(silent))
lines.append("M1b_U212\tCRASH\tALL\tALL\t%d" % len(crash))

# ---- M1c: group x tree x verdict ----
c_cnt = Counter()
c_total = Counter()
for r in m1c:
    c_cnt[(r["group"], r["tree"], r["verdict"])] += 1
    c_total[r["verdict"]] += 1
for (g, t, v), n in sorted(c_cnt.items()):
    lines.append("M1c\t%s\t%s\t%s\t%d" % (g, t, v, n))

# ---- totals (M1b + M1c) ----
# M1b verdict names: MATCH, NOT_REACHED_AS_EXPECTED, NOT_RUN, MISMATCH, FLAKY
tot = Counter()
for k, n in b_verdict.items():
    tot[k] += n
for k, n in c_total.items():
    tot[k] += n
for k in ("MATCH", "NOT_REACHED_AS_EXPECTED", "NOT_RUN", "MISMATCH", "FLAKY"):
    lines.append("TOTAL\tM1b+M1c\tALL\t%s\t%d" % (k, tot.get(k, 0)))
# M1c only and M1b only, for the report
for k in ("MATCH", "NOT_REACHED_AS_EXPECTED", "NOT_RUN", "MISMATCH", "FLAKY"):
    lines.append("TOTAL_M1B\tM1b\tALL\t%s\t%d" % (k, b_verdict.get(k, 0)))
    lines.append("TOTAL_M1C\tM1c\tALL\t%s\t%d" % (k, c_total.get(k, 0)))

with open(OUT_S, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")

# ---- FIX_COVERAGE: 806, 415, RP-S3R4-1 ----
# Coverage is searched in the M1b and M1c registries by the fix identifiers; a row covers an item only when the
# fix identifier appears in its point id or in the R8 M1a ADDITIONS/SITEMAP mapping.  Items without rows are reported as
# NOT_COVERED_IN_M1 -> M2; no claim of verification is made.
items = ["806", "415", "RP-S3R4-1"]
cov = []
addition_path = os.path.join(REG, "M1a")
sitemap_rows = []
for root, _, files in os.walk(addition_path):
    for f in files:
        if "SITEMAP" in f or "ADDITIONS" in f:
            with open(os.path.join(root, f), encoding="utf-8") as fh:
                for l in fh:
                    if l.strip() and not l.startswith("#"):
                        sitemap_rows.append((f, l.rstrip("\n")))
for item in items:
    hits_b = [r["point_id"] for r in m1b if item in r.get("point_id", "")]
    hits_c = [r["point_id_r8"] for r in m1c if item in r.get("point_id_r8", "")]
    hits_map = [f for f, l in sitemap_rows if item in l]
    # Conservative rule (brief 7 / 8): an item is COVERED only when an M1b or M1c row's point id itself names it.
    # Mapping-file hits (ADDITIONS_MAPPING, A-<item>) are recorded as a helper column only: M1b/M1c ids (ADD22-A-<n>-F<tree>,
    # M-*, R4-*, SC*, C-*) do not name the item, so no reliable mapping to M1 rows is established in this round.
    if hits_b or hits_c:
        status = "COVERED_IN_M1_BY_ID"
    else:
        status = "NOT_COVERED_IN_M1 -> M2"
    cov.append("%s\t%s\t%d\t%d\t%d\t%s" % (item, status, len(hits_b), len(hits_c), len(hits_map),
                                           ";".join(sorted(set(hits_map)))[:300]))
with open(OUT_C, "w", encoding="utf-8") as fh:
    fh.write("# FIX_COVERAGE_M1_R8_M1c3 -- coverage of 806 / 415 / RP-S3R4-1 by M1b and M1c rows.\n")
    fh.write("item\tstatus\tm1b_rows\tm1c_rows\tmap_hits\tmap_files\n")
    fh.write("\n".join(cov) + "\n")

print("M1b_ROWS=%d M1c_ROWS=%d U212_SILENT=%d U212_CRASH=%d" % (len(m1b), len(m1c), len(silent), len(crash)))
print("TOTALS " + " ".join("%s=%d" % (k, tot.get(k, 0)) for k in ("MATCH", "NOT_REACHED_AS_EXPECTED", "NOT_RUN", "MISMATCH", "FLAKY")))
for c in cov:
    print("COVER " + c)
