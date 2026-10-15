#!/usr/bin/env python3
# summarize_m1_r8m1c4.py -- P05-S4 R8 M1c4 M1 totals (corrected). New file.
# Output: $EV/M1_SUMMARY_R8_M1c4.tsv. Assertions: M1b class sum = 830, M1c class sum = 472, total = 1302.
# If any assertion fails, no output file is written and the script prints FAIL.
# Run: sh testing/d003/safe_run.sh p05-s4r8/m1c4 -- python3 -I -B testing/d003/stage_s4/summarize_m1_r8m1c4.py
import os
import sys
from collections import Counter

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c4")
REG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8")
M1B = os.path.join(REG, "M1b", "r8m1b3", "EFFECTIVE_M1B_R8_M1b3.tsv")
M1C = os.path.join(REG, "M1c", "r8m1c3", "VERDICT_M1C_R8_M1c3.tsv")
OUT = os.path.join(EV, "M1_SUMMARY_R8_M1c4.tsv")
CLASSES = ["MATCH", "NOT_REACHED_AS_EXPECTED", "NOT_RUN_AS_EXPECTED", "MISMATCH", "FLAKY"]


def read_rows(path, header_token):
    """Return dict rows. Skips '#' comment lines and 'ROWS=' lines; the header is the first line starting with header_token."""
    rows = []
    header = None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#") or line.startswith("ROWS="):
                continue
            parts = line.split("\t")
            if header is None:
                if parts[0] != header_token:
                    raise SystemExit("unexpected header in %s: %s" % (path, parts[0]))
                header = parts
                continue
            if len(parts) != len(header):
                raise SystemExit("column count mismatch in %s" % path)
            rows.append(dict(zip(header, parts)))
    return rows


def bucket(v):
    return v if v in CLASSES else "OTHER"


def main():
    m1b = read_rows(M1B, "row_id")
    m1c = read_rows(M1C, "group")
    if len(m1b) != 830:
        print("FAIL M1b rows=%d != 830" % len(m1b))
        return 1
    if len(m1c) != 472:
        print("FAIL M1c rows=%d != 472" % len(m1c))
        return 1

    b_verdict = Counter(bucket(r["effective_verdict"]) for r in m1b)
    b_grp_tree_class = Counter((r["group"], r["tree"], r["effective_class_p1"]) for r in m1b)
    c_verdict = Counter(bucket(r["verdict"]) for r in m1c)
    c_grp_tree = Counter((r["group"], r["tree"], r["verdict"]) for r in m1c)

    total = Counter()
    for c in CLASSES + ["OTHER"]:
        total[c] = b_verdict.get(c, 0) + c_verdict.get(c, 0)

    # assertions
    ok = True
    b_sum = sum(b_verdict.values())
    c_sum = sum(c_verdict.values())
    if b_sum != 830:
        print("FAIL M1b class sum %d != 830" % b_sum)
        ok = False
    if c_sum != 472:
        print("FAIL M1c class sum %d != 472" % c_sum)
        ok = False
    if sum(total.values()) != 1302:
        print("FAIL total %d != 1302" % sum(total.values()))
        ok = False
    if not ok:
        return 1

    # SILENT_SWALLOW and CRASH rows of ADD22 (U212), listed per point
    silent = [r for r in m1b if r["group"] == "ADDITIONS_22" and r["effective_class_p1"] == "SILENT_SWALLOW"]
    crash = [r for r in m1b if r["group"] == "ADDITIONS_22" and r["effective_class_p1"] == "CRASH"]

    if os.path.exists(OUT):
        print("REFUSED exists (U17): %s" % OUT)
        return 2
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("# M1_SUMMARY_R8_M1c4 -- corrected M1 totals (supersedes M1_SUMMARY_R8_M1c3 which omitted G2c_control NOT_RUN rows, U224)\n")
        fh.write("# sources: M1b = registries/s4r8/M1b/r8m1b3/EFFECTIVE_M1B_R8_M1b3.tsv (830 rows); M1c = registries/s4r8/M1c/r8m1c3/VERDICT_M1C_R8_M1c3.tsv (472 rows; the _R3 content, U226)\n")
        fh.write("section\tgroup\ttree\tclass\tcount\n")
        for k in sorted(b_grp_tree_class):
            fh.write("M1B_CLASS_P1\t%s\t%s\t%s\t%d\n" % (k[0], k[1], k[2], b_grp_tree_class[k]))
        for k in sorted(c_grp_tree):
            fh.write("M1C_VERDICT\t%s\t%s\t%s\t%d\n" % (k[0], k[1], k[2], c_grp_tree[k]))
        fh.write("section\tsource\tclass\tcount\n")
        for c in CLASSES + ["OTHER"]:
            fh.write("M1B_VERDICT\teffective_verdict\t%s\t%d\n" % (c, b_verdict.get(c, 0)))
        for c in CLASSES + ["OTHER"]:
            fh.write("M1C_VERDICT\tverdict\t%s\t%d\n" % (c, c_verdict.get(c, 0)))
        fh.write("TOTAL\tall\tMATCH\t%d\n" % total["MATCH"])
        fh.write("TOTAL\tall\tNOT_REACHED_AS_EXPECTED\t%d\n" % total["NOT_REACHED_AS_EXPECTED"])
        fh.write("TOTAL\tall\tNOT_RUN_AS_EXPECTED\t%d\n" % total["NOT_RUN_AS_EXPECTED"])
        fh.write("TOTAL\tall\tMISMATCH\t%d\n" % total["MISMATCH"])
        fh.write("TOTAL\tall\tFLAKY\t%d\n" % total["FLAKY"])
        fh.write("TOTAL\tall\tOTHER\t%d\n" % total["OTHER"])
        fh.write("ASSERT\tM1B_SUM\t%d\t830\n" % b_sum)
        fh.write("ASSERT\tM1C_SUM\t%d\t472\n" % c_sum)
        fh.write("ASSERT\tTOTAL\t%d\t1302\n" % sum(total.values()))
        fh.write("# U212 single list: SILENT_SWALLOW (ADD22-A-7/8/9)\n")
        for r in silent:
            fh.write("U212_SILENT\t%s\t%s\t%s\t%s\n" % (r["point_id"], r["tree"], r["effective_verdict"], r["effective_class_p1"]))
        fh.write("# U212 single list: CRASH (ADD22 F2 rows)\n")
        for r in crash:
            fh.write("U212_CRASH\t%s\t%s\t%s\t%s\n" % (r["point_id"], r["tree"], r["effective_verdict"], r["effective_class_p1"]))
        fh.write("U212_COUNT\tSILENT_SWALLOW\t%d\n" % len(silent))
        fh.write("U212_COUNT\tCRASH\t%d\n" % len(crash))
    print("M1_SUMMARY OK: M1b=%d M1c=%d TOTAL=%d MATCH=%d NRAE=%d NRUN=%d MISMATCH=%d FLAKY=%d OTHER=%d SILENT=%d CRASH=%d"
          % (b_sum, c_sum, sum(total.values()), total["MATCH"], total["NOT_REACHED_AS_EXPECTED"], total["NOT_RUN_AS_EXPECTED"],
             total["MISMATCH"], total["FLAKY"], total["OTHER"], len(silent), len(crash)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
