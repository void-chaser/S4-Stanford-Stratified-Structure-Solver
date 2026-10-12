#!/usr/bin/env python3
# check_report_counts_cont9_r7.py -- P05-S4 R7 cont9 closeout (new file): recompute the numbers quoted in
# checkpoints/p05/P05_S4R7_REPORT_FINAL.md from the result tables, and compare them with the values written in the report.
# Read-only on all inputs.  Output: one line per check, then "checks_failed N".  Exit 0 iff N == 0.
#
# Usage: python3 -I -B check_report_counts_cont9_r7.py REPO EVDIR REPORT
import collections
import os
import re
import sys


def read_table(path):
    header, rows = None, []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            rows.append(dict(zip(header, f)))
    return rows


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: check_report_counts_cont9_r7.py REPO EVDIR REPORT")
    repo, ev, report = argv[1], argv[2], argv[3]
    text = open(report, encoding="utf-8").read()
    fails = []
    checks = []

    def check(name, computed, quoted):
        ok = (str(computed) == str(quoted))
        checks.append("%s\tcomputed=%s\tquoted=%s\t%s" % (name, computed, quoted, "OK" if ok else "FAIL"))
        if not ok:
            fails.append(name)

    def quoted(pattern):
        m = re.search(pattern, text)
        return m.group(1) if m else "NOT_FOUND"

    # 1. M3 F baseline vs R6c (G5 and G6)
    base = [r for r in read_table(os.path.join(ev, "m3f1", "RESULTS_R6c_STATE.tsv"))]
    check("F_G5_points_pass1_HOLD", sum(1 for r in base if r["pass"] == "1" and r["point_verdict"] == "HOLD"),
          quoted(r"F 基线 G5 点级 HOLD\s*(\d+)"))
    check("F_G5_VIOLATED", sum(1 for r in base if r["point_verdict"] == "VIOLATED"), quoted(r"F 基线 G5 VIOLATED\s*(\d+)"))
    seam = read_table(os.path.join(ev, "m3f1", "RESULTS_R6c_SEAM.tsv"))
    check("F_G6_points_pass1_HOLD", sum(1 for r in seam if r["pass"] == "1" and r["point_verdict"] == "HOLD"),
          quoted(r"F 基线 G6 点级 HOLD\s*(\d+)"))
    cmpf = os.path.join(ev, "M3_F_BASELINE_VS_R6c_FULL.tsv")
    cmp_lines = open(cmpf, encoding="utf-8").read().splitlines()
    res_line = [l for l in cmp_lines if l.startswith("# RESULT:")][0]
    check("F_vs_R6c_invariant_differences", int(re.search(r"invariant_differences=(\d+)", res_line).group(1)),
          quoted(r"F 与 R6c 的不变量差异\s*(\d+)"))

    # 2. F2 regression (section 3.2)
    f2 = read_table(os.path.join(ev, "m3r1", "RESULTS_R6c_STATE.tsv"))
    check("F2_G5_HOLD", sum(1 for r in f2 if r["pass"] == "1" and r["point_verdict"] == "HOLD"), quoted(r"F2 G5 HOLD\s*(\d+)"))
    check("F2_G5_VIOLATED", sum(1 for r in f2 if r["point_verdict"] == "VIOLATED"), quoted(r"F2 G5 VIOLATED\s*(\d+)"))
    f2s = read_table(os.path.join(ev, "m3r1", "RESULTS_R6c_SEAM.tsv"))
    check("F2_G6_HOLD", sum(1 for r in f2s if r["pass"] == "1" and r["point_verdict"] == "HOLD"), quoted(r"F2 G6 HOLD\s*(\d+)"))
    check("F2_G6_VIOLATED", sum(1 for r in f2s if r["point_verdict"] == "VIOLATED"), quoted(r"F2 G6 VIOLATED\s*(\d+)"))
    reg = os.path.join(ev, "REGRESS_R7_M3.tsv")
    reg_text = open(reg, encoding="utf-8").read()
    check("REGRESS_result", "PASS" if "# RESULT: PASS" in reg_text else "NOT_PASS", quoted(r"REGRESS_R7_M3 结果\s*(\w+)"))
    check("GDB_DIVERGENT_lines", sum(1 for name in ("m3f1", "m3r1") for f in os.listdir(os.path.join(ev, name))
                                     if f.endswith(".stdout") for l in open(os.path.join(ev, name, f), encoding="utf-8",
                                                                             errors="replace") if l.startswith("GDB_DIVERGENT")),
          quoted(r"GDB_DIVERGENT 行数\s*(\d+)"))

    # 3. Dry-run and prereg counts
    dr = open(os.path.join(ev, "DRYRUN_M3_R7.txt"), encoding="utf-8").read()
    m = re.search(r"ok=(\d+) fail=(\d+) unparsed=(\d+)", dr)
    check("dryrun_ok", m.group(1), quoted(r"dry-run ok=(\d+)"))
    check("dryrun_fail_unparsed", "%s/%s" % (m.group(2), m.group(3)), quoted(r"fail/unparsed=(\d+/\d+)"))
    pre = [l for l in open(os.path.join(ev, "REGISTRY_S4_PRE_R7_M3.tsv"), encoding="utf-8") if l.strip() and not l.startswith("#")]
    check("prereg_data_rows", len(pre) - 1, quoted(r"预注册 REGISTRY_S4_PRE_R7_M3\.tsv 数据行\s*(\d+)"))

    # 4. Equivalence checks (U84, U87)
    mk = open(os.path.join(ev, "strip_cmp", "MASKED_EQUIV_SUMMARY_R7.txt"), encoding="utf-8").read()
    check("masked_driver_pairs_not_equal", int(re.search(r"not_equal_after_mask=(\d+)", mk).group(1)),
          quoted(r"掩码后不相等的驱动对\s*(\d+)"))
    st = read_table(os.path.join(ev, "strip_cmp", "STRIP_EQUIV_R7.tsv"))
    libs = [r for r in st if r["kind"] == "lib" and r["member"] != "MEMBER_LIST"]
    check("strip_lib_members_equal", sum(1 for r in libs if r["status"] == "EQUAL_AFTER_STRIP"), quoted(r"库成员去调试段后相等\s*(\d+)"))
    check("strip_lib_members_total", len(libs), quoted(r"库成员总数\s*(\d+)"))

    # 5. Build option difference (E7-41): all lines differ 0
    bo = open(os.path.join(ev, "BUILD_OPTION_DIFF_R7_M3.txt"), encoding="utf-8").read()
    check("build_option_diff_lines", sum(int(x) for x in re.findall(r"diff_lines=(\d+)", bo)), quoted(r"编译选项差异行数\s*(\d+)"))

    # 6. M2b run7 G1 MATCH (pass 1), computed from the result table of M2b run7
    g1 = read_table(os.path.join(repo, "checkpoints/p05/registries/s4r7/RESULTS_R7_G1_pass1_run7.tsv")) \
        if os.path.isfile(os.path.join(repo, "checkpoints/p05/registries/s4r7/RESULTS_R7_G1_pass1_run7.tsv")) else []
    check("M2b_run7_G1_rows_pass1", len(g1), quoted(r"M2b G1 行数\s*(\d+)"))

    # 7. U38: number of classified malloc sites (data rows of PATTERN_MALLOC_CLASS_R7.tsv, header excluded)
    # PATTERN_MALLOC_CLASS_R7.tsv has no header row (its column names are in a comment line); every non-comment line is a data row
    cls = [l for l in open(os.path.join(ev, "PATTERN_MALLOC_CLASS_R7.tsv"), encoding="utf-8")
           if l.strip() and not l.startswith("#")]
    check("U38_classified_rows", len(cls), quoted(r"U38 分类行数\s*(\d+)"))

    # 8. E7 and U numbering (ERRATA headers "== E7-n"; RULINGS ids "Un" in column 1)
    err = open(os.path.join(repo, "checkpoints/p05/registries/s4r7/ERRATA_7.txt"), encoding="utf-8").read()
    last_e7 = max(int(x) for x in re.findall(r"^== E7-(\d+)", err, re.M))
    check("E7_last", last_e7, quoted(r"E7 最后编号\s*E7-(\d+)"))
    rul_ids = [l.split("\t")[0] for l in open(os.path.join(repo, "checkpoints/p05/registries/RULINGS.tsv"), encoding="utf-8")
               if re.match(r"^U\d+\t", l)]
    last_u = max(int(x[1:]) for x in rul_ids)
    check("U_last", last_u, quoted(r"U 最后编号\s*U(\d+)"))

    for c in checks:
        print(c)
    print("checks_failed %d" % len(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
