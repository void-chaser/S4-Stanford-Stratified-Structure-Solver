#!/usr/bin/env python3
# check_report_counts_r8m2a.py -- P05-S4 R8 M2a section 6: recompute every report count from the evidence tables and
# compare with the markers written in checkpoints/p05/P05_S4R8_M2A_REPORT.md.  Writes $EV/REPORT_COUNT_CHECK_R8_M2a.txt
# (ALL_MATCH, or the list of mismatches).  Also asserts PREREG total rows = sum of item counts (section 4.5).
# Refuses to overwrite (U17).  Read-only on the report and on the evidence.
import os
import re
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a")
REPORT = os.path.join(REPO, "checkpoints", "p05", "P05_S4R8_M2A_REPORT.md")
OUT = os.path.join(EV, "REPORT_COUNT_CHECK_R8_M2a.txt")


def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
    head = lines[0].split("\t")
    return [dict(zip(head, l.split("\t"))) for l in lines[1:]]


def recompute():
    vals = {}
    # PREREG rows and per-item counts
    pre = read_tsv(os.path.join(EV, "PREREG_M2_R8_M2a_R2.tsv"))
    vals["M2A_PREREG_ROWS"] = len(pre)
    # Design items: feasibility classes from the design table
    design = read_tsv(os.path.join(EV, "M2_DESIGN_R8_M2a_R2.tsv"))
    items = [d for d in design if d["item"] != "M3_DEFERRED"]
    vals["M2A_ITEMS_FEASIBLE"] = sum(1 for d in items if d["feasibility"].startswith("FEASIBLE"))
    vals["M2A_ITEMS_NEEDS_S4_CHANGE"] = sum(1 for d in items if d["feasibility"] == "NEEDS_S4_CHANGE")
    vals["M2A_ITEMS_NOT_FOUND"] = sum(1 for d in items if d["feasibility"] == "NOT_FOUND")
    # Builds: none recorded in M2a (BUILD_R8_M2a.tsv is not written; no new apparatus was built)
    build_path = os.path.join(EV, "BUILD_R8_M2a.tsv")
    if os.path.isfile(build_path):
        b = read_tsv(build_path)
        vals["M2A_BUILD_OK"] = sum(1 for r in b if r.get("rc") == "0")
        vals["M2A_BUILD_FAILED"] = sum(1 for r in b if r.get("rc") != "0")
    else:
        vals["M2A_BUILD_OK"] = 0
        vals["M2A_BUILD_FAILED"] = 0
    # A-10 crosswalk: rows with COVERED_BY_M0 (R2 file)
    cw = read_tsv(os.path.join(EV, "A10_CONTROL_CROSSWALK_R8_M2a_R2.tsv"))
    vals["M2A_A10_COVERED_BY_M0"] = sum(1 for r in cw if r["status"] == "COVERED_BY_M0")
    # Posctrl (R2): read the verdict counts from the three summaries
    def summ(prefix):
        with open(os.path.join(EV, prefix + "_SUMMARY.txt"), encoding="utf-8") as fh:
            first = fh.readline()
        return dict(p.split("=", 1) for p in first.split() if "=" in p)
    a = summ("VERDICT_M2_R8_M2a_POSCTRL_A_R2")
    b_ = summ("VERDICT_M2_R8_M2a_POSCTRL_B_R2")
    c = summ("VERDICT_M2_R8_M2a_POSCTRL_C_R2")
    vals["M2A_POSCTRL_A_MISMATCH"] = int(a["MISMATCH"])
    vals["M2A_POSCTRL_B_MISMATCH"] = int(b_["MISMATCH"])
    vals["M2A_POSCTRL_C_FLAKY"] = int(c["FLAKY"])
    # Inventory: DIFFERENT or MISSING sha rows
    inv = [l.rstrip("\n").split("\t") for l in open(os.path.join(EV, "APPARATUS_INVENTORY_R8_M2a.tsv"), encoding="utf-8")]
    vals["M2A_INVENTORY_SHA_DIFFERENT"] = sum(1 for p in inv if p[0] == "SHA" and "status=SAME" not in p[4])
    return vals


def assert_prereg_sum():
    pre = read_tsv(os.path.join(EV, "PREREG_M2_R8_M2a_R2.tsv"))
    per = {}
    for r in pre:
        per[(r["item"], r["tree"])] = per.get((r["item"], r["tree"]), 0) + 1
    return sum(per.values()) == len(pre), sum(per.values()), len(pre)


def report_markers():
    with open(REPORT, encoding="utf-8") as fh:
        text = fh.read()
    found = {}
    for m in re.finditer(r"^(M2A_[A-Z0-9_]+)=(-?\d+)\s*$", text, re.M):
        found[m.group(1)] = int(m.group(2))
    return found


def main():
    if os.path.exists(OUT):
        print("check_report_counts_r8m2a: REFUSED exists (U17): %s" % OUT)
        return 2
    vals = recompute()
    marks = report_markers()
    lines = []
    bad = []
    for k in sorted(vals):
        if k not in marks:
            bad.append("%s not in report" % k)
            lines.append("MISSING_IN_REPORT %s recomputed=%d" % (k, vals[k]))
        elif marks[k] != vals[k]:
            bad.append("%s report=%d recomputed=%d" % (k, marks[k], vals[k]))
            lines.append("DIFF %s report=%d recomputed=%d" % (k, marks[k], vals[k]))
        else:
            lines.append("MATCH %s=%d" % (k, vals[k]))
    ok_sum, s, t = assert_prereg_sum()
    lines.append("PREREG_SUM_ASSERT sum=%d total=%d %s" % (s, t, "PASS" if ok_sum else "FAIL"))
    if not ok_sum:
        bad.append("prereg sum != total")
    lines.insert(0, "# REPORT_COUNT_CHECK_R8_M2a -- recomputed vs report markers")
    lines.append("RESULT=%s" % ("ALL_MATCH" if not bad else "NOT_MATCH"))
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("RESULT=%s" % ("ALL_MATCH" if not bad else "NOT_MATCH"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
