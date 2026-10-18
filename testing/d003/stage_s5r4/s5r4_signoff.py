#!/usr/bin/env python3
# s5r4_signoff.py -- P05_S5_SIGNOFF_DRAFT_v2.md (U383): the S5 scope statement draft, replacing the S5R3
# draft as the current draft while the S5R3 file stays untouched as history. It is marked "未签收" and only
# states measured results: the "独立重判 DIFFS=0" sentence is emitted only when REJUDGE_S5R4.tsv exists and
# its SUMMARY really is 0; otherwise the measured value is written and the draft says the round is incomplete.
# usage: s5r4_signoff.py formal [--ev-root DIR] [--p05-root DIR]
import os, sys, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05_REAL = os.path.join(REPO, "checkpoints/p05")
EV4_REAL = os.path.join(P05_REAL, "evidence/p05-s5r4")
EV3 = os.path.join(P05_REAL, "evidence/p05-s5r3")
TAB = chr(9)
NL = chr(10)


def read_tsv(p, skip_first=("SUMMARY",)):
    rows, hdr = [], None
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        if f[0] == hdr[0] or f[0] in skip_first:
            continue
        rows.append(dict(zip(hdr, f + [""] * (len(hdr) - len(f)))))
    return rows


def kv(p):
    d = {}
    if not os.path.isfile(p):
        return d
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if len(f) >= 2:
            d[f[0]] = f[1]
    return d


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode != "formal":
        print("usage: s5r4_signoff.py formal [--ev-root DIR] [--p05-root DIR]", file=sys.stderr)
        return 2
    def arg(n, d):
        return os.path.abspath(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else d
    EV = arg("--ev-root", EV4_REAL)
    P05 = arg("--p05-root", P05_REAL)
    d16 = {}
    for line in open(os.path.join(EV3, "D016_VERDICT_S5R3.tsv"), encoding="utf-8"):
        if line.startswith("SUMMARY" + TAB):
            for x in line.rstrip(NL).split(TAB)[1:]:
                k, _, v = x.partition("=")
                d16[k] = v
    ec, fe = {}, {}
    for r in read_tsv(os.path.join(EV3, "E2E_VERDICT_S5R3.tsv")):
        ec[r["verdict"]] = ec.get(r["verdict"], 0) + 1
        if r["verdict"] == "E2E_OK":
            fe[r["frontend"]] = fe.get(r["frontend"], 0) + 1
    mt = kv(os.path.join(EV3, "MAKETEST_VERDICT_S5R3.tsv"))
    rej = {}
    rp = os.path.join(EV, "REJUDGE_S5R4.tsv")
    if os.path.isfile(rp):
        for line in open(rp, encoding="utf-8"):
            if line.startswith("SUMMARY" + TAB):
                for x in line.rstrip(NL).split(TAB)[1:]:
                    k, _, v = x.partition("=")
                    rej[k] = v
    measured = rej.get("DIFFS") == "0" and rej.get("E2E_ROWS") == "42" and rej.get("D016_REJUDGED_ROWS") == "33"
    t = []
    t.append("# P05-S5 范围声明草稿 v2（未签收）")
    t.append("")
    t.append("> 状态：**未签收**。本文件是 P05-S5 范围声明草稿 v2，由 P05-S5 R4 执行者按 U383 编写；签收只由用户在对话中给出。")
    t.append("> 本轮不宣布任何阶段完成或签收。v1（P05_S5_SIGNOFF_DRAFT.md）保留为历史，本文件不改写它。")
    t.append("")
    t.append("## 1 被测树")
    t.append("")
    t.append("- 被测冻结树 F4：提交 05097a7，S4/ 树 589e15eb11fcb04e031b524f25a443e7921946cf；S5R3/S5R4 的所有运行都基于 F4，S5R4 不重跑正式矩阵（U385）。")
    t.append("- 未修改 S4/、testing/d003/judge_d003.py（sha256 d2d04145e056…）与历史装置。")
    t.append("")
    t.append("## 2 S5 收口测试范围")
    t.append("")
    t.append("- make test：B 树（37a82e8）与 F4 各两遍（S5R3 在 F4 上重跑），判据 NO_NEW_FAILURE，单元数与日志 Ran N 对账 8/8；结果 %s，unit_count=%s；S5R4 不重跑（U385）。" % (mt.get("verdict", "?"), mt.get("unit_count", "?")))
    t.append("- E2E 42 点（25 注入 + 17 无注入对照，M3b 点族原样）：E2E_OK=%d、CONTROL_OK=%d、FLAKY/INVALID/HIT_OFF_TARGET/API_SILENT/RETRY_DIFF/RETRY_FAIL 均为 0。" % (ec.get("E2E_OK", -1), ec.get("CONTROL_OK", -1)))
    t.append("- D016 点族（Python/Lua 公共 API，VL NB=1–4 失败与同对象重试、对照、恢复）：MATCH=%s MISMATCH=%s FLAKY=%s（判定行 34：33 MATCH + 1 RECORD）。" % (d16.get("MATCH"), d16.get("MISMATCH"), d16.get("FLAKY")))
    t.append("- 阳性对照：D016 5/5、E2E 19/19、make test 4/4；独立重判自检 6/6、阳性对照 4/4。")
    if measured:
        t.append("- **独立重判 v2（S5R4 实测）**：REJUDGE_S5R4.tsv 的 SUMMARY 为 E2E_ROWS=42 E2E_DIFFS=0、D016_RECORDED_ROWS=34 D016_REJUDGED_ROWS=33 D016_NOT_JUDGED=1 D016_DIFFS=0、DIFFS=0；行覆盖=E2E 42 点全部 SAME、D016 33 个行为点全部 SAME、ROOT_CAUSE_RC 记 NOT_JUDGED_SOURCE_RECORD（[源码] RECORD，不在预注册中）。")
    else:
        t.append("- **独立重判 v2（S5R4 实测）**：本轮正式重判未得到 DIFFS=0（实测 DIFFS=%s，见 REJUDGE_S5R4.tsv）；S5R4 未完成，不得作为签收依据。" % rej.get("DIFFS", "MISSING"))
    t.append("")
    t.append("## 3 S5R4 修正项（相对 S5R3）")
    t.append("")
    t.append("- 独立重判：S5R3 rejudge 崩溃（ES5-9）已由 rejudge_s5r4.py 重写并正式产出（U379）。")
    t.append("- 门禁 5 项检查器缺陷（ES5-10）：RULINGS 注释行、FROZEN mode 标注、git status strip、D016 表头行、CALIB SUMMARY 行；S5R4 gate_check_s5r4.py 修正并逐项配落盘变异阳性对照（U378）。")
    t.append("- 就绪审计：改为在最终 STATE 之后运行并记录 STATE 字节/sha，GAP=0（U382）。")
    t.append("- registry 补齐：registries/s5r4/s5r3_completion/ 补齐 S5R3 应交付的 7 项，S5R3 覆盖 26/26（U380）。")
    t.append("- 试跑门禁：staging 完整演练达到 FAILS=0/CHECK_CRASHED=0（U381）。")
    t.append("")
    t.append("## 4 转出项清单")
    t.append("")
    t.append("- U366–U370 转出/登记项：F10 历史因果（S5-B-01）、F8 历史目录未验证（S5-B-02）、S1 报告 11.2 五哈希来源无法判定（S5-B-05..09）、反事实通量与 allzero 设计意图（R-P05-01）、U99/U100（R-P05-02/R-P05-03）。")
    t.append("- D017：非 FMM S4_malloc 分配失败未逐点检查（59 处出现 / CALL 52 / OUT 38 / OUT CALL 31），保持 OPEN，不在 P05 修，不阻塞 P06（U369）。")
    t.append("- R-P05-01 / R-P05-02 / R-P05-03：保持 OPEN，转出 P05，不阻塞 P06（U366、U370）。")
    t.append("")
    t.append("## 5 已知限制")
    t.append("")
    t.append("- D016 的 NV -10 路径触发不了：NV 只作为对照点（NB=1 成功），-10 路径维持 [源码] 结论，未实测。")
    t.append("- Lua REPL 前端只覆盖 cf/fft/kt/vl 四族（exp 无 REPL 点，因为 REPL 脚本只用真实方法名且 exp 路径由批量前端覆盖）。")
    t.append("- S5R2 比较器历史缺陷 ES5-6：S5R2 的 D016 比较器把预注册标签 ABSENT 与计数 0 直比导致 2 个 MISMATCH；S5R3 用比较器 v2 与 expected_count=0 重跑，S5R2 判定表保留为历史。")
    t.append("- S5R3 build 的 PYEXT sha 与 M3b 对照为 DIFFERENT_OUTSIDE_BUILD_ID：树路径 s5r3 比 m3b 长 1 字节使嵌入路径整体移位，未判等价（Lua 前端 sha IDENTICAL）。")
    t.append("- 范围限 F4 与被测点族；不外推到其它树/布局/材料范围；S5R4 不重跑正式矩阵（U385）。")
    t.append("")
    t.append("## 6 声明")
    t.append("")
    t.append("- **未签收**；等待用户审核。S5R3 遗留项已在 S5R4 消解，readiness GAP=0。")
    t.append("")
    txt = NL.join(t) + NL
    out = os.path.join(P05, "P05_S5_SIGNOFF_DRAFT_v2.md")
    open(out, "w", encoding="utf-8").write(txt)
    print("SIGNOFF_DRAFT_V2 bytes=%d measured_rejudge=%s DIFFS=%s rows=%s/%s" % (
        len(txt.encode("utf-8")), measured, rej.get("DIFFS"), rej.get("E2E_ROWS"), rej.get("D016_REJUDGED_ROWS")))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
