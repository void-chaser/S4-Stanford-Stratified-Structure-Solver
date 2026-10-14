#!/usr/bin/env python3
# summarize_m1b_r8m1b1.py -- P05-S4 R8 M1b summary & cross-check (brief §6). New file.
import os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV") or os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1b1")

def load_tsv(fname):
    p = os.path.join(EV, fname)
    rows = []
    header = None
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\r\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if header is None:
                header = parts
                continue
            rows.append(dict(zip(header, parts)))
    return header, rows

def main():
    _, plan = load_tsv("PLAN_M1B_R8_M1b1.tsv")
    _, res = load_tsv("RESULTS_M1B_R8_M1b1.tsv")
    _, verd = load_tsv("VERDICT_M1B_R8_M1b1.tsv")
    _, cons = load_tsv("CONSISTENCY_M1B_R8_M1b1.tsv")
    _, diff = load_tsv("F2_F3_DIFF_M1B_R8_M1b1.tsv")
    _, cov = load_tsv("COVERAGE_M1B_R8_M1b1.tsv")
    _, anom = load_tsv("ANOMALIES_M1B_R8_M1b1.tsv")

    print("=================== M1B EXECUTION AUDIT ===================")
    print("1. Counts:")
    print("   Total preregistered rows: %d (F2: %d, F3: %d)" % (
        len(plan), sum(1 for r in plan if r["tree"] == "F2"), sum(1 for r in plan if r["tree"] == "F3")
    ))
    print("   Total executed rows:      %d (F2: %d, F3: %d)" % (
        sum(1 for r in res if r["status"] == "COMPLETED"),
        sum(1 for r in res if r["status"] == "COMPLETED" and r["tree"] == "F2"),
        sum(1 for r in res if r["status"] == "COMPLETED" and r["tree"] == "F3")
    ))
    print("   Not-run rows (G2c_ctrl):  %d (F2: %d, F3: %d)" % (
        sum(1 for r in res if r["status"] == "NOT_RUN"),
        sum(1 for r in res if r["status"] == "NOT_RUN" and r["tree"] == "F2"),
        sum(1 for r in res if r["status"] == "NOT_RUN" and r["tree"] == "F3")
    ))
    print("   Physical process calls:   %d (Pass 1: %d, Pass 2: %d)" % (
        sum(1 for r in res if r["status"] == "COMPLETED") * 2,
        sum(1 for r in res if r["status"] == "COMPLETED"),
        sum(1 for r in res if r["status"] == "COMPLETED")
    ))
    print("   Unique test cases:        %d pairs" % len(diff))

    print("\n2. Verdicts:")
    print("   MATCH:                    %d" % sum(1 for r in verd if r["verdict_overall"] == "MATCH"))
    print("   NOT_RUN_AS_EXPECTED:      %d" % sum(1 for r in verd if r["verdict_overall"] == "NOT_RUN_AS_EXPECTED"))
    print("   NOT_REACHED_AS_EXPECTED:  %d" % sum(1 for r in verd if r["verdict_overall"] == "NOT_REACHED_AS_EXPECTED"))
    print("   MISMATCH:                 %d" % sum(1 for r in verd if r["verdict_overall"] == "MISMATCH"))
    print("   FLAKY:                    %d" % sum(1 for r in verd if r["verdict_overall"] == "FLAKY"))

    print("\n3. Consistency across passes:")
    flaky_c = sum(1 for r in cons if r["pass_consistent"] == "NO")
    print("   Flaky (pass1 != pass2):   %d" % flaky_c)
    print("   Consistent passes:        %d" % (len(cons) - flaky_c))

    print("\n4. F2 vs F3 paired comparison:")
    from collections import Counter
    diff_cats = Counter(r["diff_category"] for r in diff)
    for cat, cnt in sorted(diff_cats.items()):
        print("   %-26s %d" % (cat + ":", cnt))

    print("\n5. BASELINE_RC_EQUAL controls (U198):")
    bl_rows = [r for r in verd if r["comparison_contract"] == "BASELINE_RC_EQUAL"]
    print("   Total rows: %d" % len(bl_rows))
    for r in bl_rows:
        print("   %s: class_p1=%s class_p2=%s rc1_p1=%s rc2_p1=%s run_rc=%s hit=%s verdict=%s" % (
            r["point_id"], r["actual_class_p1"], r["actual_class_p2"],
            r["actual_rc1_p1"], r["actual_rc2_p1"], r["actual_run_rc_p1"], r["actual_hit_p1"], r["verdict_overall"]
        ))

    print("\n6. Anomalies breakdown:")
    anom_cats = Counter(r["group"] for r in anom)
    for g, cnt in sorted(anom_cats.items()):
        print("   Group %-15s: %d MISMATCH rows" % (g, cnt))
    print("===========================================================")

if __name__ == "__main__":
    main()
