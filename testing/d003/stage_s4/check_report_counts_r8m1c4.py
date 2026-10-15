#!/usr/bin/env python3
# check_report_counts_r8m1c4.py -- P05-S4 R8 M1c4 report number check (brief section 6). New file.
# Recomputes every C4_ marker from the evidence tables (never from the report), compares each marker value written in
# the report with the recomputed value, and asserts C4_TOTAL_ROWS = 1302.
# Input: checkpoints/p05/P05_S4R8_M1C4_REPORT.md (marker lines: "C4_NAME=value").
# Output: $EV/REPORT_COUNT_CHECK_R8_M1c4<SUFFIX>.txt   (SUFFIX from argv[1], default empty; the first run uses ""
#         and a rerun after an edit uses "_R2"). Last line ALL_MATCH or MISMATCH: <names>.
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m1c4 -- python3 -I -B testing/d003/stage_s4/check_report_counts_r8m1c4.py [_R2]
import os
import re
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c4")
REPORT = os.path.join(REPO, "checkpoints", "p05", "P05_S4R8_M1C4_REPORT.md")
SUFFIX = sys.argv[1] if len(sys.argv) > 1 else ""
OUT = os.path.join(EV, "REPORT_COUNT_CHECK_R8_M1c4%s.txt" % SUFFIX)

if os.path.exists(OUT):
    print("REFUSED exists (U17): %s" % OUT)
    sys.exit(2)


def rows_tsv(path):
    out = []
    with open(path, encoding="utf-8") as fh:
        for l in fh:
            l = l.rstrip("\n")
            if l and not l.startswith("#"):
                out.append(l.split("\t"))
    return out


# ---- recompute from the evidence tables ----
recheck_last = None
with open(os.path.join(EV, "RECHECK_F3_R8_M1c4.tsv"), encoding="utf-8") as fh:
    for l in fh:
        if l.startswith("CHECKS="):
            recheck_last = l.strip()
m = re.match(r"CHECKS=(\d+) DIFFS=(\d+)", recheck_last or "")
recheck_diffs = int(m.group(2)) if m else -1

summary = rows_tsv(os.path.join(EV, "M1_SUMMARY_R8_M1c4.tsv"))
totals = {}
for r in summary:
    if r and r[0] == "TOTAL" and len(r) == 4:
        totals[r[2]] = int(r[3])
asserts = {r[1]: (int(r[2]), int(r[3])) for r in summary if r and r[0] == "ASSERT" and len(r) == 4}
assert_ok = all(a == b for a, b in asserts.values())

fix = rows_tsv(os.path.join(EV, "FIX_COVERAGE_M1_R8_M1c4_R2.tsv"))
fix_f3 = {}
header = None
for r in fix:
    if r and r[0] == "item":
        header = r
        continue
    if header and r and len(r) == len(header) and r[0] not in ("item",):
        fix_f3[r[0]] = (int(r[1]), int(r[2]), r[-1])

posc = {}
with open(os.path.join(EV, "POSCTRL_M1C_R8_M1c4.txt"), encoding="utf-8") as fh:
    for l in fh:
        p = l.rstrip("\n").split("\t")
        if len(p) >= 2 and p[0] in ("A_DIFFS", "A2_DIFFS", "B_DIFFS"):
            posc[p[0]] = int(p[1])

cmp_line = None
with open(os.path.join(EV, "CMP_OUTPUTS_R8_M1c4.txt"), encoding="utf-8") as fh:
    for l in fh:
        if l.startswith("CMP_REAL_SAME="):
            cmp_line = l.strip()
m2 = re.match(r"CMP_REAL_SAME=(\d+)/(\d+)", cmp_line or "")
cmp_same = int(m2.group(1)) if m2 else -1

recomputed = {
    "C4_RECHECK_DIFFS": recheck_diffs,
    "C4_TOTAL_MATCH": totals.get("MATCH", -1),
    "C4_TOTAL_NOT_REACHED_AS_EXPECTED": totals.get("NOT_REACHED_AS_EXPECTED", -1),
    "C4_TOTAL_NOT_RUN_AS_EXPECTED": totals.get("NOT_RUN_AS_EXPECTED", -1),
    "C4_TOTAL_MISMATCH": totals.get("MISMATCH", -1),
    "C4_TOTAL_FLAKY": totals.get("FLAKY", -1),
    "C4_TOTAL_ROWS": sum(totals.get(k, 0) for k in ("MATCH", "NOT_REACHED_AS_EXPECTED", "NOT_RUN_AS_EXPECTED", "MISMATCH", "FLAKY", "OTHER")),
    "C4_COV_806_F3_MATCH": fix_f3.get("A-806", (0, -1, ""))[1],
    "C4_COV_1729_F3_MATCH": fix_f3.get("A-1729", (0, -1, ""))[1],
    "C4_COV_415_F3_MATCH": fix_f3.get("B-415", (0, -1, ""))[1],
    "C4_POSCTRL_A_DIFFS": posc.get("A_DIFFS", -1),
    "C4_POSCTRL_A2_DIFFS": posc.get("A2_DIFFS", -1),
    "C4_POSCTRL_B_DIFFS": posc.get("B_DIFFS", -1),
    "C4_CMP_REAL_SAME": cmp_same,
}

# ---- markers as written in the report ----
written = {}
if os.path.isfile(REPORT):
    with open(REPORT, encoding="utf-8") as fh:
        for l in fh:
            for mm in re.finditer(r"(C4_[A-Z0-9_]+)=(-?\d+)", l):
                written.setdefault(mm.group(1), []).append(int(mm.group(2)))

lines = []
fails = []
lines.append("# REPORT_COUNT_CHECK_R8_M1c4%s -- recomputed from evidence tables; compared with report markers" % SUFFIX)
lines.append("marker\trecomputed\treport_values\tresult")
for k in sorted(recomputed):
    vals = written.get(k, [])
    if not vals:
        res = "MISSING_IN_REPORT"
        fails.append(k)
    elif all(v == recomputed[k] for v in vals):
        res = "MATCH"
    else:
        res = "MISMATCH"
        fails.append(k)
    lines.append("%s\t%s\t%s\t%s" % (k, recomputed[k], vals, res))
# independent assertion: total rows = 1302
rows_ok = recomputed["C4_TOTAL_ROWS"] == 1302
lines.append("ASSERT_TOTAL_ROWS_1302\t%s\t%s" % (recomputed["C4_TOTAL_ROWS"], "PASS" if rows_ok else "FAIL"))
if not rows_ok:
    fails.append("C4_TOTAL_ROWS_1302")
if not assert_ok:
    lines.append("ASSERT_M1_SUMMARY\tFAIL")
    fails.append("M1_SUMMARY_ASSERT")
else:
    lines.append("ASSERT_M1_SUMMARY\tPASS")

status = "ALL_MATCH" if not fails else "MISMATCH: " + ",".join(fails)
lines.append(status)
with open(OUT, "x", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
print(status)
sys.exit(0 if not fails else 1)
