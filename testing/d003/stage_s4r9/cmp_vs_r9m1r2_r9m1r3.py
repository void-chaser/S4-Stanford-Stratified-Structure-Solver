#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# cmp_vs_r9m1r2_r9m1r3.py -- Compare r9m1r3 facts against r9m1r2 reference results (Step S-H). New file.
import argparse, csv, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r3"))

def main():
    parser = argparse.ArgumentParser(description="Compare r9m1r3 vs r9m1r2 facts")
    parser.add_argument("--r2", default=os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1r2/runs/formal_R2/FORMAL_FACTS_M1_F4_R9M1R2_pass1.tsv"))
    parser.add_argument("--r3", default=os.path.join(EV, "runs", "formal", "FORMAL_FACTS_M1_F4_R9M1R3_pass1.tsv"))
    parser.add_argument("--out", default=os.path.join(EV, "R9M1R2_VS_R9M1R3_R9M1R3.tsv"))
    args = parser.parse_args()

    r2_rows = {}
    with open(args.r2, encoding="utf-8") as f:
        lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            r = dict(zip(h, l))
            r2_rows[(r["section"], r["group"], r["point_id"])] = r

    r3_rows = {}
    with open(args.r3, encoding="utf-8") as f:
        lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            r = dict(zip(h, l))
            r3_rows[(r["section"], r["group"], r["point_id"])] = r

    assert len(r2_rows) == 651
    assert len(r3_rows) == 651

    diff_records = []
    out_rows = []
    fields_to_cmp = ["rc1", "rc2", "rc3", "hit", "class", "I1", "I2", "I3", "I4", "I5", "I6"]

    for key in sorted(r3_rows.keys()):
        sec, grp, pid = key
        r2 = r2_rows[key]
        r3 = r3_rows[key]

        diff_fields = []
        for fld in fields_to_cmp:
            v2 = r2[fld]
            v3 = r3[fld]
            if v2 != v3:
                diff_fields.append(f"{fld}(R2={v2}!=R3={v3})")

        status = "SAME" if not diff_fields else "DIFF"
        diff_str = ";".join(diff_fields) if diff_fields else "NONE"
        out_rows.append([sec, grp, pid, status, diff_str])
        if status == "DIFF":
            diff_records.append((key, diff_str))

    print(f"Comparison vs r9m1r2 complete: TOTAL = {len(out_rows)}, DIFFS = {len(diff_records)}")
    for d in diff_records:
        print(f"  Diff: {d[0]} -> {d[1]}")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("# R9M1R2_VS_R9M1R3_R9M1R3.tsv -- Comparison between r9m1r2 and r9m1r3 F4 facts (Step S-H)" + chr(10))
        fh.write(chr(9).join(["section", "group", "point_id", "status", "differences"]) + chr(10))
        for r in out_rows:
            fh.write(chr(9).join(r) + chr(10))

    print(f"Wrote {args.out}.")

if __name__ == "__main__":
    main()
