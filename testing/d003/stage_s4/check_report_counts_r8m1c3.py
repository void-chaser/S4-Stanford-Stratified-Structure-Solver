#!/usr/bin/env python3
# check_report_counts_r8m1c3.py -- P05-S4 R8 M1c3 report count check (brief 7, last paragraph). New file.
# Reads the report $REPO/checkpoints/p05/P05_S4R8_M1C3_REPORT.md and compares the count tokens that the report states
# in sections 6 and 7 with values recomputed from the evidence tables (not with the report itself).
# Output: $EV/REPORT_COUNT_CHECK_R8_M1c3[_Rn].txt, last line RESULT=ALL_MATCH or RESULT=MISMATCHES=<n>.
# Usage: python3 -I -B check_report_counts_r8m1c3.py REPORT_COUNT_CHECK_R8_M1c3[_Rn].txt
import os, re, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c3")
os.makedirs(os.path.join(EV, "tmp"), exist_ok=True)
REPORT = os.path.join(REPO, "checkpoints", "p05", "P05_S4R8_M1C3_REPORT.md")

if len(sys.argv) != 2 or not re.match(r"^REPORT_COUNT_CHECK_R8_M1c3(_R[0-9]+)?\.txt$", sys.argv[1]):
    print("usage: check_report_counts_r8m1c3.py REPORT_COUNT_CHECK_R8_M1c3[_Rn].txt")
    sys.exit(2)
OUT = os.path.join(EV, sys.argv[1])
if os.path.exists(OUT):
    print("REFUSED exists (U17): %s" % OUT)
    sys.exit(2)


def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        ls = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
    head = ls[0].split("\t")
    return [dict(zip(head, l.split("\t"))) for l in ls[1:]]


text = open(REPORT, encoding="utf-8").read()
results = []


def need(name, pattern):
    """Return the first capture of pattern in the report, or None."""
    m = re.search(pattern, text)
    return m.group(1) if m else None


def chk(name, table_value, report_value):
    ok = (report_value is not None) and (str(table_value) == str(report_value))
    results.append("%s\t%s\ttable=%s\treport=%s" % ("MATCH" if ok else "MISMATCH", name, table_value, report_value))


# ---- recomputed from tables ----
# F3 vs frozen comparison and F2-F3 comparison (DIFFS, GDB_DIVERGENT) from the evidence files
def tail_counts(path):
    last = [l for l in open(path, encoding="utf-8").read().splitlines() if l.startswith("DIFFS=")]
    m = re.search(r"DIFFS=(\d+) GDB_DIVERGENT=(\d+)", last[-1]) if last else None
    return (m.group(1), m.group(2)) if m else (None, None)


frozen_d, frozen_g = tail_counts(os.path.join(EV, "COMPARE_M1C_F3_VS_FROZEN_R8_M1c3.tsv"))
f2_d, f2_g = tail_counts(os.path.join(EV, "F2_F3_DIFF_M1C_R8_M1c3.tsv"))

agg = read_tsv(os.path.join(EV, "VERDICT_M1C_R8_M1c3_AGG_R3.tsv"))
agg_f3 = {r["group"]: r for r in agg if r["tree"] == "F3"}
agg_totals = {k: sum(int(r[k]) for r in agg if r["tree"] == "F3") for k in ("MATCH", "MISMATCH", "FLAKY", "NOT_RUN")}

summ = {}
for l in open(os.path.join(EV, "M1_SUMMARY_R8_M1c3_R2.tsv"), encoding="utf-8"):
    p = l.rstrip("\n").split("\t")
    if len(p) == 5 and p[0] == "TOTAL" and p[1] == "M1b+M1c":
        summ[p[3]] = int(p[4])

# ---- report values (sections 6 and 7; each token is a named line in the report) ----
chk("S6_FROZEN_DIFFS", frozen_d, need("a", r"S6_FROZEN_DIFFS=(\d+)"))
chk("S6_FROZEN_GDB_DIVERGENT", frozen_g, need("a", r"S6_FROZEN_GDB_DIVERGENT=(\d+)"))
chk("S6_F2_F3_DIFFS", f2_d, need("a", r"S6_F2_F3_DIFFS=(\d+)"))
chk("S6_F2_F3_GDB_DIVERGENT", f2_g, need("a", r"S6_F2_F3_GDB_DIVERGENT=(\d+)"))
for g in ("G5", "G6", "G6c", "CTRL_AUX"):
    r = agg_f3.get(g, {})
    for k in ("MATCH", "MISMATCH", "FLAKY", "NOT_RUN"):
        chk("S6_F3_%s_%s" % (g, k), r.get(k, "NA"), need("a", r"S6_F3_%s_%s=(\d+)" % (g, k)))
for k in ("MATCH", "MISMATCH", "FLAKY", "NOT_RUN"):
    chk("S6_F3_TOTAL_%s" % k, agg_totals[k], need("a", r"S6_F3_TOTAL_%s=(\d+)" % k))
for k in ("MATCH", "NOT_REACHED_AS_EXPECTED", "NOT_RUN", "MISMATCH", "FLAKY"):
    chk("S7_TOTAL_%s" % k, summ.get(k, "NA"), need("a", r"S7_TOTAL_%s=(\d+)" % k))

n_bad = sum(1 for r in results if r.startswith("MISMATCH"))
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("# REPORT_COUNT_CHECK_R8_M1c3 -- report tokens (S6_*, S7_* lines) vs values recomputed from the evidence tables.\n")
    fh.write("\n".join(results) + "\n")
    fh.write("RESULT=%s\n" % ("ALL_MATCH" if n_bad == 0 else "MISMATCHES=%d" % n_bad))
print("RESULT=%s" % ("ALL_MATCH" if n_bad == 0 else "MISMATCHES=%d" % n_bad))
