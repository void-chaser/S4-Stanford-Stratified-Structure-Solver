#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# summarize_m1_r9m1r3.py -- Generate official M1 summary table (1302 rows) (Rule U316, U319, Step S-H). New file.
import argparse, csv, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r3"))

def main():
    parser = argparse.ArgumentParser(description="Generate M1 summary table")
    parser.add_argument("--verdict", default=os.path.join(EV, "VERDICT_M1_F4_R9M1R3.tsv"))
    parser.add_argument("--cited-f2", default=os.path.join(EV, "PREREG_M1_CITED_F2_R9M1R3.tsv"))
    parser.add_argument("--out", default=os.path.join(EV, "M1_SUMMARY_F4_R9M1R3.tsv"))
    args = parser.parse_args()

    # 1. Load F4 verdicts
    f4_verdicts = []
    with open(args.verdict, encoding="utf-8") as f:
        lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            f4_verdicts.append(dict(zip(h, l)))

    assert len(f4_verdicts) == 651, f"Expected 651 F4 verdicts, got {len(f4_verdicts)}"

    # 2. Load cited F2
    f2_verdicts = []
    with open(args.cited_f2, encoding="utf-8") as f:
        lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            f2_verdicts.append(dict(zip(h, l)))

    assert len(f2_verdicts) == 651, f"Expected 651 cited F2 rows, got {len(f2_verdicts)}"

    # Summary table counts by section and tree
    summary_data = {
        ("M1b", "F4"): {"MATCH": 0, "NOT_REACHED": 0, "NOT_RUN": 0, "MISMATCH": 0, "FLAKY": 0, "GDB_DIV": 0},
        ("M1b", "F2"): {"MATCH": 0, "NOT_REACHED": 0, "NOT_RUN": 0, "MISMATCH": 0, "FLAKY": 0, "GDB_DIV": 0},
        ("M1c", "F4"): {"MATCH": 0, "NOT_REACHED": 0, "NOT_RUN": 0, "MISMATCH": 0, "FLAKY": 0, "GDB_DIV": 0},
        ("M1c", "F2"): {"MATCH": 0, "NOT_REACHED": 0, "NOT_RUN": 0, "MISMATCH": 0, "FLAKY": 0, "GDB_DIV": 0},
    }

    for r in f4_verdicts:
        sec = r["section"]
        v = r["verdict"]
        key = (sec, "F4")
        if v == "MATCH": summary_data[key]["MATCH"] += 1
        elif v == "NOT_REACHED_AS_EXPECTED": summary_data[key]["NOT_REACHED"] += 1
        elif v == "NOT_RUN_AS_EXPECTED": summary_data[key]["NOT_RUN"] += 1
        elif v == "FLAKY": summary_data[key]["FLAKY"] += 1
        elif v == "GDB_DIVERGENT": summary_data[key]["GDB_DIV"] += 1
        else: summary_data[key]["MISMATCH"] += 1

    for r in f2_verdicts:
        sec = r["section"]
        v = r["f3_effective_verdict"]
        key = (sec, "F2")
        if v == "MATCH": summary_data[key]["MATCH"] += 1
        elif v == "NOT_REACHED_AS_EXPECTED": summary_data[key]["NOT_REACHED"] += 1
        elif v == "NOT_RUN_AS_EXPECTED": summary_data[key]["NOT_RUN"] += 1
        else: summary_data[key]["MISMATCH"] += 1

    # Assertions
    m1b_f4_total = sum(summary_data[("M1b", "F4")].values())
    m1b_f2_total = sum(summary_data[("M1b", "F2")].values())
    m1c_f4_total = sum(summary_data[("M1c", "F4")].values())
    m1c_f2_total = sum(summary_data[("M1c", "F2")].values())

    assert m1b_f4_total == 415, f"M1b F4 total {m1b_f4_total} != 415"
    assert m1b_f2_total == 415, f"M1b F2 total {m1b_f2_total} != 415"
    assert m1c_f4_total == 236, f"M1c F4 total {m1c_f4_total} != 236"
    assert m1c_f2_total == 236, f"M1c F2 total {m1c_f2_total} != 236"

    grand_total = m1b_f4_total + m1b_f2_total + m1c_f4_total + m1c_f2_total
    assert grand_total == 1302, f"Grand total {grand_total} != 1302"

    rows = []
    for (sec, tree) in [("M1b", "F4"), ("M1b", "F2"), ("M1c", "F4"), ("M1c", "F2")]:
        d = summary_data[(sec, tree)]
        tot = sum(d.values())
        rows.append([sec, tree, str(d["MATCH"]), str(d["NOT_REACHED"]), str(d["NOT_RUN"]), str(d["MISMATCH"]), str(d["FLAKY"]), str(d["GDB_DIV"]), str(tot)])

    # Grand total row
    gt_match = sum(r[("MATCH")] for r in summary_data.values())
    gt_not_reached = sum(r[("NOT_REACHED")] for r in summary_data.values())
    gt_not_run = sum(r[("NOT_RUN")] for r in summary_data.values())
    gt_mismatch = sum(r[("MISMATCH")] for r in summary_data.values())
    gt_flaky = sum(r[("FLAKY")] for r in summary_data.values())
    gt_gdb_div = sum(r[("GDB_DIV")] for r in summary_data.values())
    rows.append(["TOTAL", "F4+F2", str(gt_match), str(gt_not_reached), str(gt_not_run), str(gt_mismatch), str(gt_flaky), str(gt_gdb_div), str(grand_total)])

    print("M1 Summary Table (1302 rows):")
    for r in rows:
        print("  " + " | ".join(r))

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("# M1_SUMMARY_F4_R9M1R3.tsv -- Final summary of M1 regression (1302 rows; Rule U316, U319)" + chr(10))
        fh.write(chr(9).join(["section", "tree", "MATCH", "NOT_REACHED", "NOT_RUN", "MISMATCH", "FLAKY", "GDB_DIVERGENT", "total"]) + chr(10))
        for r in rows:
            fh.write(chr(9).join(r) + chr(10))

    print(f"Wrote {args.out}.")

if __name__ == "__main__":
    main()
