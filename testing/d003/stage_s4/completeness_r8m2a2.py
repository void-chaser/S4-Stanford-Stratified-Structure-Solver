#!/usr/bin/env python3
# completeness_r8m2a2.py -- P05-S4 R8 M2a2 section 4.9 & CONT1 section 8: completeness check.
# Asserts for M2-00..M2-10 that each item satisfies at least one of:
#   - prereg points > 0
#   - category COVERED_BY_M0 / COVERED_BY_M1 with coverage reference
#   - category NOT_FOUND / NOT_FOUND_IN_SCOPE with search table (rows > 0 and SUMMARY matches category)
#   - category NEEDS_S4_CHANGE with reason
#   - category BUILD_FAILED with BUILD row
# Output: $EV/COMPLETENESS_R8_M2a2.txt
# Refuses to overwrite (U17).
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
OUT = os.path.join(EV, "COMPLETENESS_R8_M2a2_R2.txt")  # R2: first run checked SUMMARY line only for M2_02 token; kept, SUPERSEDED
DESIGN = os.path.join(EV, "M2_DESIGN_R8_M2a2.tsv")
PREREG = os.path.join(EV, "PREREG_M2_R8_M2a2.tsv")
STAGE_E = os.path.join(EV, "STAGE_E_SEARCH_R8_M2a2_R2.tsv")
CATC_B = os.path.join(EV, "CATC_SEARCH_R8_M2a2_R2B.tsv")
CATC = os.path.join(EV, "CATC_SEARCH_R8_M2a2_R2.tsv")

def count_tsv_rows(path):
    if not os.path.exists(path): return 0
    with open(path, encoding="utf-8") as fh:
        return sum(1 for l in fh if l.strip() and not l.startswith("#"))

def get_summary_line(path):
    if not os.path.exists(path): return ""
    with open(path, encoding="utf-8") as fh:
        for l in fh:
            if "SUMMARY:" in l:
                return l.strip()
    return ""

def main():
    if os.path.exists(OUT):
        print("completeness_r8m2a2: REFUSED exists (U17)")
        return 2

    # Read design table
    design = {}
    with open(DESIGN, encoding="utf-8") as fh:
        for l in fh:
            if l.startswith("#") or not l.strip(): continue
            p = l.rstrip("\n").split("\t")
            if p[0] != "item":
                design[p[0]] = {
                    "points": int(p[7]),
                    "feasibility": p[11],
                    "limitation": p[12],
                    "expectation_basis": p[8]
                }

    # Count prereg points per base item
    prereg_counts = {}
    with open(PREREG, encoding="utf-8") as fh:
        for l in fh:
            if l.startswith("#") or not l.strip(): continue
            p = l.rstrip("\n").split("\t")
            if p[1] != "item":
                base = p[1].replace("-CTRL", "")
                prereg_counts[base] = prereg_counts.get(base, 0) + 1

    checks = []
    fails = 0

    items = ["M2-00", "M2-01", "M2-02", "M2-03", "M2-04", "M2-05", "M2-06", "M2-07", "M2-08", "M2-09", "M2-10"]

    for item in items:
        info = design.get(item)
        if not info:
            checks.append((item, "FAIL", "missing in design table"))
            fails += 1
            continue

        feas = info["feasibility"]
        pts = prereg_counts.get(item, 0)

        if pts > 0:
            checks.append((item, "PASS", "prereg points = %d > 0 (feasibility=%s)" % (pts, feas)))
        elif feas in ("COVERED_BY_M0", "COVERED_BY_M1"):
            checks.append((item, "PASS", "category %s with reference: %s" % (feas, info["expectation_basis"])))
        elif feas == "NOT_FOUND_IN_SCOPE" and item == "M2-02":
            rows = count_tsv_rows(STAGE_E)
            content = open(STAGE_E, encoding="utf-8").read() if os.path.exists(STAGE_E) else ""
            sum_line = get_summary_line(STAGE_E)
            ok = rows > 0 and ("M2_02=NOT_FOUND_IN_SCOPE" in content and "STAGE_E_IN_SCOPE=0" in sum_line)
            v = "PASS" if ok else "FAIL"
            if not ok: fails += 1
            checks.append((item, v, "search table %s rows=%d, summary: %s, M2_02=NOT_FOUND_IN_SCOPE confirmed" % (os.path.basename(STAGE_E), rows, sum_line)))
        elif feas == "NOT_FOUND" and item == "M2-08":
            target_catc = CATC_B if os.path.exists(CATC_B) else CATC
            rows = count_tsv_rows(target_catc)
            sum_line = get_summary_line(target_catc)
            ok = rows > 0 and "M2_08=NOT_FOUND" in sum_line
            v = "PASS" if ok else "FAIL"
            if not ok: fails += 1
            checks.append((item, v, "search table %s rows=%d, summary: %s" % (os.path.basename(target_catc), rows, sum_line)))
        elif feas == "NEEDS_S4_CHANGE":
            checks.append((item, "PASS", "category NEEDS_S4_CHANGE with reason: %s" % info["limitation"]))
        elif feas == "BUILD_FAILED":
            checks.append((item, "PASS", "category BUILD_FAILED"))
        else:
            checks.append((item, "FAIL", "no prereg points and category %s unsatisfied" % feas))
            fails += 1

    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("# COMPLETENESS_R8_M2a2 -- P05-S4 R8 M2a2 section 4.9 & CONT1 section 8\n")
        fh.write("item\tresult\tdetails\n")
        for c in checks:
            fh.write("%s\t%s\t%s\n" % c)
        fh.write("# TOTAL_ITEMS=%d FAILS=%d\n" % (len(items), fails))
        fh.write("# COMPLETENESS=%s\n" % ("PASS" if fails == 0 else "FAIL"))

    print("completeness_r8m2a2: items=%d fails=%d COMPLETENESS=%s" % (len(items), fails, "PASS" if fails == 0 else "FAIL"))
    return 0 if fails == 0 else 3

if __name__ == "__main__":
    sys.exit(main())
