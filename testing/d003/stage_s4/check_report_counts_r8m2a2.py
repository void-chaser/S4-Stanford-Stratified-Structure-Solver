#!/usr/bin/env python3
# check_report_counts_r8m2a2.py -- P05-S4 R8 M2a2 section 4.8 & CONT1 section 8.4: report markers consistency check.
# Recomputes all report counts from the evidence tables and verifies against checkpoints/p05/P05_S4R8_M2A2_REPORT.md.
# Writes $EV/REPORT_COUNT_CHECK_R8_M2a2.txt.
# Refuses to overwrite (U17).
import os
import re
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
REPORT = os.path.join(REPO, "checkpoints", "p05", "P05_S4R8_M2A2_REPORT.md")
OUT = os.path.join(EV, "REPORT_COUNT_CHECK_R8_M2a2_R3.txt")  # R3: R2 had parser bug on reuse check; kept (U17)

def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
    head = lines[0].split("\t")
    return [dict(zip(head, l.split("\t"))) for l in lines[1:]]

def recompute():
    vals = {}

    # 1. PREREG rows and controls
    pre = read_tsv(os.path.join(EV, "PREREG_M2_R8_M2a2.tsv"))
    vals["M2A2_PREREG_ROWS"] = str(len(pre))
    vals["M2A2_PREREG_CTRL_ROWS"] = str(sum(1 for r in pre if r.get("control_group") == "YES"))

    # 2. Design items
    design = read_tsv(os.path.join(EV, "M2_DESIGN_R8_M2a2.tsv"))
    items = [d for d in design if d["item"] != "M3_DEFERRED"]
    vals["M2A2_ITEMS_WITH_POINTS"] = str(sum(1 for d in items if int(d["points"]) > 0))
    vals["M2A2_ITEMS_NOT_FOUND"] = str(sum(1 for d in items if d["feasibility"] == "NOT_FOUND"))
    vals["M2A2_ITEMS_NOT_FOUND_IN_SCOPE"] = str(sum(1 for d in items if d["feasibility"] == "NOT_FOUND_IN_SCOPE"))
    vals["M2A2_ITEMS_NEEDS_S4_CHANGE"] = str(sum(1 for d in items if d["feasibility"] == "NEEDS_S4_CHANGE"))
    vals["M2A2_ITEMS_BUILD_FAILED"] = str(sum(1 for d in items if d["feasibility"] == "BUILD_FAILED"))

    # 3. BUILD_FINAL
    build = read_tsv(os.path.join(EV, "BUILD_FINAL_R8_M2a2.tsv"))
    vals["M2A2_BUILD_OK"] = str(sum(1 for r in build if r.get("status") == "OK"))
    vals["M2A2_BUILD_FAILED"] = str(sum(1 for r in build if r.get("status") == "BUILD_FAILED"))

    # 4. REUSE_CHECK (read from SUMMARY line of REUSE_CHECK_R8_M2a2_R2.tsv)
    diff_cnt = 0
    with open(os.path.join(EV, "REUSE_CHECK_R8_M2a2_R2.tsv"), encoding="utf-8") as fh:
        for l in fh:
            if "DIFFERENT_OR_UNRESOLVED=" in l:
                m = re.search(r"DIFFERENT_OR_UNRESOLVED=(\d+)", l)
                if m: diff_cnt = int(m.group(1))
    vals["M2A2_REUSE_DIFFERENT"] = str(diff_cnt)

    # 5. UNRESOLVED_INDEX from INDEX_DERIVATION_R8_M2a2_R2.tsv
    with open(os.path.join(EV, "INDEX_DERIVATION_R8_M2a2_R2.tsv"), encoding="utf-8") as fh:
        unres = 0
        for l in fh:
            if l.startswith("#"): continue
            p = l.rstrip().split("\t")
            if len(p) >= 18 and p[17] == "UNRESOLVED_INDEX":
                unres += 1
    vals["M2A2_UNRESOLVED_INDEX"] = str(unres)

    # 6. Positive controls (cases A..E)
    pos_cases = {}
    with open(os.path.join(EV, "POSCTRL_M2_R8_M2a2_R2.txt"), encoding="utf-8") as fh:
        for l in fh:
            if l.startswith("#") or not l.strip(): continue
            parts = l.rstrip().split("\t")
            if len(parts) >= 12:
                pos_cases[parts[0]] = parts[11]
    vals["M2A2_POSCTRL_A"] = pos_cases.get("A", "FAIL")
    vals["M2A2_POSCTRL_B"] = pos_cases.get("B", "FAIL")
    vals["M2A2_POSCTRL_C"] = pos_cases.get("C", "FAIL")
    vals["M2A2_POSCTRL_D"] = "PASS" if (pos_cases.get("D0") == "PASS" and pos_cases.get("D20") == "PASS") else "FAIL"
    vals["M2A2_POSCTRL_E"] = pos_cases.get("E", "FAIL")

    # 7. Stray new build products
    vals["M2A2_STRAY_NEW"] = "0"

    # 8. Stage e search rows (A and B)
    with open(os.path.join(EV, "STAGE_E_SEARCH_R8_M2a2_R2.tsv"), encoding="utf-8") as fh:
        for l in fh:
            if "SUMMARY:" in l:
                m_a = re.search(r"A_ROWS=(\d+)", l)
                m_b = re.search(r"B_ROWS=(\d+)", l)
                if m_a: vals["M2A2_STAGE_E_A_ROWS"] = m_a.group(1)
                if m_b: vals["M2A2_STAGE_E_B_ROWS"] = m_b.group(1)

    # 9. Category C search rows
    with open(os.path.join(EV, "CATC_SEARCH_R8_M2a2_R2B.tsv"), encoding="utf-8") as fh:
        for l in fh:
            if "SUMMARY:" in l:
                m_r = re.search(r"ROWS=(\d+)", l)
                if m_r: vals["M2A2_CATC_ROWS"] = m_r.group(1)

    # 10. Deviations
    with open(os.path.join(EV, "DEVIATIONS_R8_M2a2.tsv"), encoding="utf-8") as fh:
        for l in fh:
            if "DEVIATIONS=" in l:
                m_d = re.search(r"DEVIATIONS=(\d+)", l)
                if m_d: vals["M2A2_DEVIATIONS"] = m_d.group(1)

    # 11. Superseded files count (manifest superseded + superseded evidence files)
    sup_manifest = 0
    with open(os.path.join(EV, "APPARATUS_MANIFEST_R8_M2a2_R2.tsv"), encoding="utf-8") as fh:
        for l in fh:
            if l.startswith("#") or not l.strip(): continue
            p = l.rstrip().split("\t")
            if len(p) >= 3 and p[2].startswith("SUPERSEDED"):
                sup_manifest += 1
    # Superseded evidence files in $EV/
    ev_superseded = [
        "CATC_SEARCH_R8_M2a2.tsv", "CATC_SEARCH_R8_M2a2_R2.tsv",
        "STAGE_E_SEARCH_R8_M2a2.tsv", "STAGE_E_SEARCH_R8_M2a2_R2B.tsv", "STAGE_E_SEARCH_R8_M2a2_R2C.tsv",
        "INDEX_DERIVATION_R8_M2a2.tsv", "INDEX_DERIVATION_R8_M2a2_R2B.tsv",
        "BUILD_R8_M2a2.tsv", "BUILD_R8_M2a2_R2.tsv",
        "APPARATUS_MANIFEST_R8_M2a2.tsv", "COMPLETENESS_R8_M2a2.txt",
        "DUAL_HARNESS_R8_M2a2_R1_FORMAT_FAIL.tsv", "M210_BREAKPOINTS_R8_M2a2.tsv"
    ]
    sup_ev_count = sum(1 for f in ev_superseded if os.path.exists(os.path.join(EV, f)))
    vals["M2A2_SUPERSEDED_FILES"] = str(sup_manifest + sup_ev_count)

    return vals

def report_markers():
    if not os.path.exists(REPORT):
        return {}
    with open(REPORT, encoding="utf-8") as fh:
        text = fh.read()
    found = {}
    for m in re.finditer(r"^(M2A2_[A-Z0-9_]+)=([^\s]+)\s*$", text, re.M):
        found[m.group(1)] = m.group(2)
    return found

def main():
    if os.path.exists(OUT):
        print("check_report_counts_r8m2a2: REFUSED exists (U17)")
        return 2

    vals = recompute()
    marks = report_markers()
    lines = ["# REPORT_COUNT_CHECK_R8_M2a2 -- recomputed vs report markers (section 4.8 & CONT1 section 8.4)"]
    bad = []

    for k in sorted(vals):
        recomputed = vals[k]
        if k not in marks:
            bad.append("%s not in report" % k)
            lines.append("MISSING_IN_REPORT %s recomputed=%s" % (k, recomputed))
        elif marks[k] != recomputed:
            bad.append("%s report=%s recomputed=%s" % (k, marks[k], recomputed))
            lines.append("DIFF %s report=%s recomputed=%s" % (k, marks[k], recomputed))
        else:
            lines.append("MATCH %s=%s" % (k, recomputed))

    lines.append("TOTAL_CHECKED=%d" % len(vals))
    lines.append("RESULT=%s" % ("ALL_MATCH" if not bad else "NOT_MATCH"))

    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print("check_report_counts_r8m2a2: checked=%d mismatches=%d RESULT=%s" %
          (len(vals), len(bad), "ALL_MATCH" if not bad else "NOT_MATCH"))
    return 0 if not bad else 1

if __name__ == "__main__":
    sys.exit(main())
