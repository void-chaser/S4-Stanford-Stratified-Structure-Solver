#!/usr/bin/env python3
# cmp_outputs_r8m1c4.py -- P05-S4 R8 M1c4: line-by-line comparison of the formal reproduction outputs with the
# committed r8m1c3 registries copies. Line 1 (comment header) may differ; all other lines must be identical.
# New file. Output: $EV/CMP_OUTPUTS_R8_M1c4.txt (last line CMP_REAL_SAME=<n>/<total> or FAIL).
# Run: sh testing/d003/safe_run.sh p05-s4r8/m1c4 -- python3 -I -B testing/d003/stage_s4/cmp_outputs_r8m1c4.py
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c4")
R3 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c3")
OUT = os.path.join(EV, "CMP_OUTPUTS_R8_M1c4.txt")

PAIRS = [
    (os.path.join(EV, "CMP_REAL_R8_M1c4_VS_FROZEN.tsv"), os.path.join(R3, "COMPARE_M1C_F3_VS_FROZEN_R8_M1c3.tsv")),
    (os.path.join(EV, "CMP_REAL_R8_M1c4_F2_F3_DIFF.tsv"), os.path.join(R3, "F2_F3_DIFF_M1C_R8_M1c3.tsv")),
]


def lines(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read().split("\n")


def main():
    if os.path.exists(OUT):
        print("REFUSED exists (U17): %s" % OUT)
        return 2
    report = []
    total_lines = 0
    diff_lines = 0
    for mine, ref in PAIRS:
        a = lines(mine)
        b = lines(ref)
        report.append("# %s vs %s" % (os.path.basename(mine), os.path.basename(ref)))
        report.append("#   line counts: mine=%d ref=%d" % (len(a), len(b)))
        if len(a) != len(b):
            report.append("#   LINE_COUNT_DIFFERS")
            diff_lines += abs(len(a) - len(b))
        n = min(len(a), len(b))
        for i in range(1, n):  # index 0 is the comment header and may differ
            total_lines += 1
            if a[i] != b[i]:
                diff_lines += 1
                report.append("DIFF\tline=%d\tmine=%s\tref=%s" % (i + 1, a[i], b[i]))
        report.append("#   header line 1 may differ: mine=%s" % a[0][:120])
        report.append("#   header line 1 may differ: ref=%s" % b[0][:120])
    same = total_lines - diff_lines
    status = "CMP_REAL_SAME=%d/%d" % (same, total_lines) if diff_lines == 0 else "CMP_REAL_DIFF=%d" % diff_lines
    report.append(status)
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("# CMP_OUTPUTS_R8_M1c4 -- formal reproduction vs committed r8m1c3 registries (line 1 excluded)\n")
        for r in report:
            fh.write(r + "\n")
    print(status)
    return 0 if diff_lines == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
