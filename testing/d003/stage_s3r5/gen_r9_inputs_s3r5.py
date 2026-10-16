#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gen_r9_inputs_s3r5.py -- Generate R9_INPUTS_S3R5.tsv and REGRESSION_PLAN_F4_S3R5.tsv (S-J, U290).
import os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s3r5")
EV = os.path.join(REPO, EV_REL)
R9_INPUTS_TSV = os.path.join(EV, "R9_INPUTS_S3R5.tsv")
REG_PLAN_TSV = os.path.join(EV, "REGRESSION_PLAN_F4_S3R5.tsv")

# Artifacts from BUILD_S3R5.tsv
LIB_DBG_SHA = "6a711fbbec84d1fb322ee1d9c678ae6750a04f647e3f1eba7840c8c7502fae26"
LIB_SAN_SHA = "ce057b5065bb5ac487d66992930991c1f09f17431abfc957777f375436be0fbd"
LIB_PLAIN_SHA = "5a4bfa601bf14b896b9c0c25807c0a38c05d040a17268cf0669902763cda5757"
DRV_DBG_SHA = "a4643e7e67ad74019104466ff9773ec2cfc1e684e488705a16a4a8f32526aca2"
DRV_SAN_SHA = "33a230029df224ddecb64f0884833e7e20251c461f0459ce315122d5987666c3"
DRV_SAN_AL_SHA = "f14c536ea54d81348dd4f53f36c5c2eba65c0ca15fdb16160b8296186d7f5f8e"
INIT_B_DBG_SHA = "3ccc2897fae2ce293d3c656e2a334dad05e53fe7f622b749a71e19bfd021b0b8"

def write_r9_inputs():
    rows = [
        ("F4_LIBRARY", "lib_F4_dbg", LIB_DBG_SHA, "checkpoints/p05/evidence/p05-s3r5/build/lib_F4_dbg/libS4.a; -O0 -g; warnings=62"),
        ("F4_LIBRARY", "lib_F4_san", LIB_SAN_SHA, "checkpoints/p05/evidence/p05-s3r5/build/lib_F4_san/libS4.a; ASAN/UBSAN -O0 -g; warnings=62"),
        ("F4_LIBRARY", "lib_F4_plain", LIB_PLAIN_SHA, "checkpoints/p05/evidence/p05-s3r5/build/lib_F4_plain/libS4.a; -O3 -march=native; warnings=71"),
        ("F4_DRIVER", "init-F4-dbg", DRV_DBG_SHA, "checkpoints/p05/evidence/p05-s3r5/build/init-F4-dbg; driver_r6b_state + inject_s3r4_init + lib_F4_dbg; warnings=0"),
        ("F4_DRIVER", "init-F4-san", DRV_SAN_SHA, "checkpoints/p05/evidence/p05-s3r5/build/init-F4-san; driver_r6b_state + inject_s3r4_init + lib_F4_san; warnings=0"),
        ("F4_DRIVER", "init-F4-san-AL", DRV_SAN_AL_SHA, "checkpoints/p05/evidence/p05-s3r5/build/init-F4-san-AL; driver_r6b_state + inject_r8m2e_aligned + lib_F4_san; warnings=0"),
        ("F4_DRIVER", "init-B-dbg", INIT_B_DBG_SHA, "checkpoints/p05/evidence/p05-s4r8/m2c/build/init-B-dbg; reused (U286)"),
        ("F4_K_MAPPING", "closed2d-ng1:1763:init-F4-dbg", "k=9", "size=16 B; S4.cpp:1763"),
        ("F4_K_MAPPING", "closed2d-ng1:1764:init-F4-dbg", "k=10", "size=215 B (outer 192 B); S4.cpp:1771"),
        ("F4_K_MAPPING", "closed2d-ng1:1765:init-F4-dbg", "k=11", "size=12 B; S4.cpp:1772"),
        ("F4_K_MAPPING", "closed2d-ng1:1763:init-F4-san", "k=7", "size=16 B; S4.cpp:1763"),
        ("F4_K_MAPPING", "closed2d-ng1:1765:init-F4-san", "k=8", "size=12 B; S4.cpp:1772"),
        ("F4_K_MAPPING", "closed2d-ng1:1764:init-F4-san-AL", "k=3", "size=192 B; S4.cpp:1771 (malloc_aligned)"),
        ("F4_K_MAPPING", "fft-ng5:1763:init-F4-dbg", "k=10", "size=16 B; S4.cpp:1763"),
        ("F4_K_MAPPING", "fft-ng5:1764:init-F4-dbg", "k=11", "size=983 B (outer 960 B); S4.cpp:1771"),
        ("F4_K_MAPPING", "fft-ng5:1765:init-F4-dbg", "k=12", "size=12 B; S4.cpp:1772"),
        ("F4_K_MAPPING", "fft-ng5:1763:init-F4-san", "k=8", "size=16 B; S4.cpp:1763"),
        ("F4_K_MAPPING", "fft-ng5:1765:init-F4-san", "k=9", "size=12 B; S4.cpp:1772"),
        ("F4_K_MAPPING", "fft-ng5:1764:init-F4-san-AL", "k=3", "size=960 B; S4.cpp:1771 (malloc_aligned)"),
        ("F4_K_MAPPING", "kottke-ng5:1763:init-F4-dbg", "k=10", "size=16 B; S4.cpp:1763"),
        ("F4_K_MAPPING", "kottke-ng5:1764:init-F4-dbg", "k=11", "size=983 B (outer 960 B); S4.cpp:1771"),
        ("F4_K_MAPPING", "kottke-ng5:1765:init-F4-dbg", "k=12", "size=12 B; S4.cpp:1772"),
        ("F4_K_MAPPING", "kottke-ng5:1763:init-F4-san", "k=8", "size=16 B; S4.cpp:1763"),
        ("F4_K_MAPPING", "kottke-ng5:1765:init-F4-san", "k=9", "size=12 B; S4.cpp:1772"),
        ("F4_K_MAPPING", "kottke-ng5:1764:init-F4-san-AL", "k=3", "size=960 B; S4.cpp:1771 (malloc_aligned)"),
        ("F4_LINEMAP", "S4/S4.cpp:1..1759", "offset=0", "Pre-fix lines unchanged"),
        ("F4_LINEMAP", "S4/S4.cpp:1760..1774", "MODIFIED_BY_FIX", "14 lines in F3 -> 27 lines in F4 (net +13 lines)"),
        ("F4_LINEMAP", "S4/S4.cpp:1775+", "offset=+13", "Post-fix lines shifted by +13 (e.g. 1995->2008, 2021->2034)"),
        ("GDB_SCRIPT_AUDIT", "r6c_state_bt_r8m2d.gdb", "NO_LINE_BREAKPOINTS", "Uses function breakpoints (r6_probe, CLM, GetLayerSolution); safe for F4 without rewrite"),
        ("GDB_SCRIPT_AUDIT", "r6c_state_r8m2a3.gdb", "NO_LINE_BREAKPOINTS", "Uses function breakpoints; safe for F4"),
        ("GDB_SCRIPT_AUDIT", "r6c_state_gdb_r8m2a3.py", "NO_LINE_BREAKPOINTS", "Uses symbol breakpoints; safe for F4"),
        ("GDB_SCRIPT_AUDIT", "malloc_map_r8m2c.gdb", "INJECTOR_LINE_BP", "Break at inject_s3r4_init.cpp:79; not in S4/, unchanged"),
        ("GDB_SCRIPT_AUDIT", "OVERALL_STATUS", "NO_REWRITE_NEEDED", "0 gdb scripts require line number rewriting for F4"),
    ]
    with open(R9_INPUTS_TSV, "w", encoding="utf-8") as fh:
        fh.write("# R9_INPUTS_S3R5.tsv -- All inputs required for P05-S4 R9 on F4 apparatus (U290)\n")
        fh.write("category\titem\tvalue\tnote\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    print("Wrote %s (%d rows)" % (R9_INPUTS_TSV, len(rows)))

def write_regression_plan():
    # 27 SOLN points + 2 additional regression items + 2 closeout items = 31 rows
    rows = [
        ("point_id", "f4_driver", "k_fail", "f4_exp_rc1", "f4_exp_rc2", "f4_exp_class", "f4_exp_post_call1_solution", "f4_exp_crash_call", "b_baseline_behavior", "f4_recovery_requirement", "notes"),
        ("SOLN-1763-closed2d-ng1-F4-dbg", "init-F4-dbg", "取 K_MAP_F4_S3R5.tsv (k=9)", "1", "0", "REPORTED_FAILURE", "NULL", "NONE", "未修复基线B行为：崩于第1次调用 (1763) [仅基线，非修复证据]", "调用2输出与无注入对照逐字节一致 (I6)", "S3R5修后：调用1失败置S->solution=NULL并返回1；调用2重试进入InitSolution成功"),
        ("SOLN-1763-closed2d-ng1-B-dbg", "init-B-dbg", "9", "-", "-", "CRASH", "-", "1", "CRASH at call 1 (1763) [仅基线，非修复证据]", "N/A (基线对照)", "基线驱动使用 init-B-dbg (sha 3ccc2897...)，非修复证据"),
        ("SOLN-1763-closed2d-ng1-F4-san", "init-F4-san", "取 K_MAP_F4_S3R5.tsv (k=7)", "1", "0", "REPORTED_FAILURE", "NULL", "NONE", "未修复基线B行为：崩于第1次调用 (1763) [仅基线，非修复证据]", "调用2输出与无注入对照逐字节一致 (I6)", "S3R5修后：调用1失败置S->solution=NULL并返回1；调用2重试进入InitSolution成功"),
        ("SOLN-1763-fft-ng5-F4-dbg", "init-F4-dbg", "取 K_MAP_F4_S3R5.tsv (k=10)", "1", "0", "REPORTED_FAILURE", "NULL", "NONE", "未修复基线B行为：崩于第1次调用 (1763) [仅基线，非修复证据]", "调用2输出与无注入对照逐字节一致 (I6)", "S3R5修后：调用1失败置S->solution=NULL并返回1；调用2重试进入InitSolution成功"),
        ("SOLN-1763-fft-ng5-B-dbg", "init-B-dbg", "10", "-", "-", "CRASH", "-", "1", "CRASH at call 1 (1763) [仅基线，非修复证据]", "N/A (基线对照)", "基线驱动使用 init-B-dbg (sha 3ccc2897...)，非修复证据"),
        ("SOLN-1763-fft-ng5-F4-san", "init-F4-san", "取 K_MAP_F4_S3R5.tsv (k=8)", "1", "0", "REPORTED_FAILURE", "NULL", "NONE", "未修复基线B行为：崩于第1次调用 (1763) [仅基线，非修复证据]", "调用2输出与无注入对照逐字节一致 (I6)", "S3R5修后：调用1失败置S->solution=NULL并返回1；调用2重试进入InitSolution成功"),
        ("SOLN-1763-kottke-ng5-F4-dbg", "init-F4-dbg", "取 K_MAP_F4_S3R5.tsv (k=10)", "1", "0", "REPORTED_FAILURE", "NULL", "NONE", "未修复基线B行为：崩于第1次调用 (1763) [仅基线，非修复证据]", "调用2输出与无注入对照逐字节一致 (I6)", "S3R5修后：调用1失败置S->solution=NULL并返回1；调用2重试进入InitSolution成功"),
        ("SOLN-1763-kottke-ng5-B-dbg", "init-B-dbg", "10", "-", "-", "CRASH", "-", "1", "CRASH at call 1 (1763) [仅基线，非修复证据]", "N/A (基线对照)", "基线驱动使用 init-B-dbg (sha 3ccc2897...)，非修复证据"),
        ("SOLN-1763-kottke-ng5-F4-san", "init-F4-san", "取 K_MAP_F4_S3R5.tsv (k=8)", "1", "0", "REPORTED_FAILURE", "NULL", "NONE", "未修复基线B行为：崩于第1次调用 (1763) [仅基线，非修复证据]", "调用2输出与无注入对照逐字节一致 (I6)", "S3R5修后：调用1失败置S->solution=NULL并返回1；调用2重试进入InitSolution成功"),
        ("SOLN-1764-closed2d-ng1-F4-dbg", "init-F4-dbg", "取 K_MAP_F4_S3R5.tsv (k=10)", "1", "0", "REPORTED_FAILURE", "NULL", "NONE", "未修复基线B行为：崩于第2次调用 (1764) [仅基线，非修复证据]", "调用2输出与无注入对照逐字节一致 (I6)", "S3R5修后：调用1失败置S->solution=NULL并返回1；调用2重试进入InitSolution成功"),
        ("SOLN-1764-closed2d-ng1-B-dbg", "init-B-dbg", "10", "-", "-", "CRASH", "-", "2", "CRASH at call 2 (1764) [仅基线，非修复证据]", "N/A (基线对照)", "基线驱动使用 init-B-dbg (sha 3ccc2897...)，非修复证据"),
        ("SOLN-1764-closed2d-ng1-F4-san-AL", "init-F4-san-AL", "取 K_MAP_F4_S3R5.tsv (k=3)", "1", "0", "REPORTED_FAILURE", "NULL", "NONE", "未修复基线B行为：崩于第2次调用 (1764) [仅基线，非修复证据]", "调用2输出与无注入对照逐字节一致 (I6)", "S3R5修后：驱动 init-F4-san-AL; malloc_aligned 注入; 调用1失败置NULL并返回1; 重试成功"),
        ("SOLN-1764-fft-ng5-F4-dbg", "init-F4-dbg", "取 K_MAP_F4_S3R5.tsv (k=11)", "1", "0", "REPORTED_FAILURE", "NULL", "NONE", "未修复基线B行为：崩于第2次调用 (1764) [仅基线，非修复证据]", "调用2输出与无注入对照逐字节一致 (I6)", "S3R5修后：调用1失败置S->solution=NULL并返回1；调用2重试进入InitSolution成功"),
        ("SOLN-1764-fft-ng5-B-dbg", "init-B-dbg", "11", "-", "-", "CRASH", "-", "2", "CRASH at call 2 (1764) [仅基线，非修复证据]", "N/A (基线对照)", "基线驱动使用 init-B-dbg (sha 3ccc2897...)，非修复证据"),
        ("SOLN-1764-fft-ng5-F4-san-AL", "init-F4-san-AL", "取 K_MAP_F4_S3R5.tsv (k=3)", "1", "0", "REPORTED_FAILURE", "NULL", "NONE", "未修复基线B行为：崩于第2次调用 (1764) [仅基线，非修复证据]", "调用2输出与无注入对照逐字节一致 (I6)", "S3R5修后：驱动 init-F4-san-AL; malloc_aligned 注入; 调用1失败置NULL并返回1; 重试成功"),
        ("SOLN-1764-kottke-ng5-F4-dbg", "init-F4-dbg", "取 K_MAP_F4_S3R5.tsv (k=11)", "1", "0", "REPORTED_FAILURE", "NULL", "NONE", "未修复基线B行为：崩于第2次调用 (1764) [仅基线，非修复证据]", "调用2输出与无注入对照逐字节一致 (I6)", "S3R5修后：调用1失败置S->solution=NULL并返回1；调用2重试进入InitSolution成功"),
        ("SOLN-1764-kottke-ng5-B-dbg", "init-B-dbg", "11", "-", "-", "CRASH", "-", "2", "CRASH at call 2 (1764) [仅基线，非修复证据]", "N/A (基线对照)", "基线驱动使用 init-B-dbg (sha 3ccc2897...)，非修复证据"),
        ("SOLN-1764-kottke-ng5-F4-san-AL", "init-F4-san-AL", "取 K_MAP_F4_S3R5.tsv (k=3)", "1", "0", "REPORTED_FAILURE", "NULL", "NONE", "未修复基线B行为：崩于第2次调用 (1764) [仅基线，非修复证据]", "调用2输出与无注入对照逐字节一致 (I6)", "S3R5修后：驱动 init-F4-san-AL; malloc_aligned 注入; 调用1失败置NULL并返回1; 重试成功"),
        ("SOLN-1765-closed2d-ng1-F4-dbg", "init-F4-dbg", "取 K_MAP_F4_S3R5.tsv (k=11)", "1", "0", "REPORTED_FAILURE", "NULL", "NONE", "未修复基线B行为：崩于第2次调用 (1765) [仅基线，非修复证据]", "调用2输出与无注入对照逐字节一致 (I6)", "S3R5修后：调用1失败置S->solution=NULL并返回1；调用2重试进入InitSolution成功"),
        ("SOLN-1765-closed2d-ng1-B-dbg", "init-B-dbg", "11", "-", "-", "CRASH", "-", "2", "CRASH at call 2 (1765) [仅基线，非修复证据]", "N/A (基线对照)", "基线驱动使用 init-B-dbg (sha 3ccc2897...)，非修复证据"),
        ("SOLN-1765-closed2d-ng1-F4-san", "init-F4-san", "取 K_MAP_F4_S3R5.tsv (k=8)", "1", "0", "REPORTED_FAILURE", "NULL", "NONE", "未修复基线B行为：崩于第2次调用 (1765) [仅基线，非修复证据]", "调用2输出与无注入对照逐字节一致 (I6)", "S3R5修后：调用1失败置S->solution=NULL并返回1；调用2重试进入InitSolution成功"),
        ("SOLN-1765-fft-ng5-F4-dbg", "init-F4-dbg", "取 K_MAP_F4_S3R5.tsv (k=12)", "1", "0", "REPORTED_FAILURE", "NULL", "NONE", "未修复基线B行为：崩于第2次调用 (1765) [仅基线，非修复证据]", "调用2输出与无注入对照逐字节一致 (I6)", "S3R5修后：调用1失败置S->solution=NULL并返回1；调用2重试进入InitSolution成功"),
        ("SOLN-1765-fft-ng5-B-dbg", "init-B-dbg", "12", "-", "-", "CRASH", "-", "2", "CRASH at call 2 (1765) [仅基线，非修复证据]", "N/A (基线对照)", "基线驱动使用 init-B-dbg (sha 3ccc2897...)，非修复证据"),
        ("SOLN-1765-fft-ng5-F4-san", "init-F4-san", "取 K_MAP_F4_S3R5.tsv (k=9)", "1", "0", "REPORTED_FAILURE", "NULL", "NONE", "未修复基线B行为：崩于第2次调用 (1765) [仅基线，非修复证据]", "调用2输出与无注入对照逐字节一致 (I6)", "S3R5修后：调用1失败置S->solution=NULL并返回1；调用2重试进入InitSolution成功"),
        ("SOLN-1765-kottke-ng5-F4-dbg", "init-F4-dbg", "取 K_MAP_F4_S3R5.tsv (k=12)", "1", "0", "REPORTED_FAILURE", "NULL", "NONE", "未修复基线B行为：崩于第2次调用 (1765) [仅基线，非修复证据]", "调用2输出与无注入对照逐字节一致 (I6)", "S3R5修后：调用1失败置S->solution=NULL并返回1；调用2重试进入InitSolution成功"),
        ("SOLN-1765-kottke-ng5-B-dbg", "init-B-dbg", "12", "-", "-", "CRASH", "-", "2", "CRASH at call 2 (1765) [仅基线，非修复证据]", "N/A (基线对照)", "基线驱动使用 init-B-dbg (sha 3ccc2897...)，非修复证据"),
        ("SOLN-1765-kottke-ng5-F4-san", "init-F4-san", "取 K_MAP_F4_S3R5.tsv (k=9)", "1", "0", "REPORTED_FAILURE", "NULL", "NONE", "未修复基线B行为：崩于第2次调用 (1765) [仅基线，非修复证据]", "调用2输出与无注入对照逐字节一致 (I6)", "S3R5修后：调用1失败置S->solution=NULL并返回1；调用2重试进入InitSolution成功"),
        ("M2-HEALTH-175-F4-REGRESSION", "multi-driver-F4", "-", "-", "-", "MATCH", "-", "NONE", "历史有效175点在F3全闭环", "F4上175点结果与F3逐点一致", "追加登记项1（只登记，不执行）：M2健康175点在F4上回归测试，确保修复无负面影响"),
        ("M1-EQUIVALENCE-F3-F4", "equivalence_runner", "-", "-", "-", "MATCH", "-", "NONE", "M1在F3上1302点全闭环", "F3与F4之间等价对比无分歧", "追加登记项2（只登记，不执行）：M1在F3与F4之间等价对比，确保F4未破坏M1任何修复"),
        ("S3R5-CLOSEOUT-MAKE-TEST", "make_test_runner", "-", "0", "-", "CONTROL_OK", "-", "NONE", "相对未修复基线B无新增失败", "make test 全套件通过", "收口测试项1（只登记，不执行）：在 $EV 导出树上运行 make test，主套件相对基线B无新增失败"),
        ("S3R5-CLOSEOUT-E2E-API", "e2e_api_runner", "-", "0", "-", "CONTROL_OK", "-", "NONE", "经公共API验证全链路", "Python/Lua端到端链路顺畅", "收口测试项2（只登记，不执行）：Python/Lua 公共 API 的“失败→可见报错→重试恢复”全链路端到端恢复测试（并入 M3）"),
    ]
    with open(REG_PLAN_TSV, "w", encoding="utf-8") as fh:
        fh.write("# REGRESSION_PLAN_F4_S3R5.tsv -- F4 regression plan for SOLN 27 points, M2/M1 regression, and closeout items (S-J, U290)\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    print("Wrote %s (%d rows)" % (REG_PLAN_TSV, len(rows)))

def main():
    write_r9_inputs()
    write_regression_plan()
    return 0

if __name__ == "__main__":
    sys.exit(main())
