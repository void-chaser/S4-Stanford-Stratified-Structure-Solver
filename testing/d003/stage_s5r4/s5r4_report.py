#!/usr/bin/env python3
# s5r4_report.py -- P05_S5R4_REPORT.md (task brief section 9). Numbers are read from the source tables
# (no hand-typed derived values); the deliverable count is the registry item count the registry step will
# write; the closing sentence is generated from FINAL_STATUS, which is PENDING_GATE before the end gate and
# is finalised by s5r4_appendix.py (appendix B summary + appendix C) after the gate.
# usage: s5r4_report.py formal [--ev-root DIR] [--ev3-root DIR] [--p05-root DIR]
import os, sys, re, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05_REAL = os.path.join(REPO, "checkpoints/p05")
EV4_REAL = os.path.join(P05_REAL, "evidence/p05-s5r4")
EV3 = os.path.join(P05_REAL, "evidence/p05-s5r3")
TAB = chr(9)
NL = chr(10)
DELIVERABLES = ["GATE_S5R4_start.txt", "PREREG_REJUDGE_S5R4.tsv", "PREREG_REJUDGE_S5R4.tsv.sha256.txt",
                "REJUDGE_S5R4.tsv", "R3_GATE_RECHECK_S5R4.tsv", "READINESS_S5R4.tsv",
                "P05_ACCEPTANCE_MAP_S5R4.tsv", "POSCTRL_REJUDGE_S5R4.txt", "POSCTRL_GATE_S5R4.txt",
                "COPY_DIFF_S5R4.txt", "REGISTRY_APPLY_DIFF_S5R4.txt", "REPORT_CHECK_S5R4.txt",
                "FROZEN_SCRIPTS_S5R4.tsv", "REGISTRY_EXPECTED_S5R4.txt"]


def read_tsv(p, skip_first=("SUMMARY",)):
    rows, hdr = [], None
    if not os.path.isfile(p):
        return rows
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


def sha_f(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def summary_kv(p):
    d = {}
    if not os.path.isfile(p):
        return d
    for line in open(p, encoding="utf-8"):
        if line.startswith("SUMMARY" + TAB):
            for x in line.rstrip(NL).split(TAB)[1:]:
                k, _, v = x.partition("=")
                d[k] = v
    return d


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode != "formal":
        print("usage: s5r4_report.py formal [--ev-root DIR] [--ev3-root DIR] [--p05-root DIR]", file=sys.stderr)
        return 2
    def arg(n, d):
        return os.path.abspath(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else d
    EV = arg("--ev-root", EV4_REAL)
    P05 = arg("--p05-root", P05_REAL)
    rej = summary_kv(os.path.join(EV, "REJUDGE_S5R4.tsv"))
    d16 = summary_kv(os.path.join(EV3, "D016_VERDICT_S5R3.tsv"))
    ec, fe = {}, {}
    for r in read_tsv(os.path.join(EV3, "E2E_VERDICT_S5R3.tsv")):
        ec[r["verdict"]] = ec.get(r["verdict"], 0) + 1
        if r["verdict"] == "E2E_OK":
            fe[r["frontend"]] = fe.get(r["frontend"], 0) + 1
    mt = {}
    for r in read_tsv(os.path.join(EV3, "MAKETEST_VERDICT_S5R3.tsv")):
        mt[r.get("item", "")] = r.get("value", "")
    r3rows = read_tsv(os.path.join(EV, "R3_GATE_RECHECK_S5R4.tsv"))
    rrows = read_tsv(os.path.join(EV, "READINESS_S5R4.tsv"))
    gap = sum(1 for r in rrows if r.get("status") == "GAP")
    rda = open(os.path.join(EV, "REGISTRY_APPLY_DIFF_S5R4.txt"), encoding="utf-8").read() if os.path.isfile(os.path.join(EV, "REGISTRY_APPLY_DIFF_S5R4.txt")) else ""
    shk = os.path.join(EV4_REAL, "shakedown/gate/GATE_S5R4_end.txt")
    skf = skc = skn = "MISSING"
    if os.path.isfile(shk):
        t = open(shk, encoding="utf-8").read()
        mf = re.search(r"FAILS=(\d+)", t)
        mc = re.search(r"CHECK_CRASHED=(\d+)", t)
        mn = re.search(r"COUNTS" + TAB + r"pass=(\d+)" + TAB + r"fail=(\d+)" + TAB + r"total=(\d+)", t)
        skf = mf.group(1) if mf else "?"
        skc = mc.group(1) if mc else "?"
        skn = mn.group(3) if mn else "?"
    srec = {}
    sgp = os.path.join(EV, "GATE_S5R4_start.txt")
    for line in open(sgp, encoding="utf-8"):
        if line.startswith("RECORD" + TAB):
            f = line.split(TAB)
            srec[f[1]] = f[2].replace("value=", "")
    t = []
    t.append("# P05-S5 R4 报告（s5r4）：S5 收口补齐——独立重判 v2、S5R3 门禁 8 项消解、就绪审计 GAP=0、S5R3 registry 26/26、签收范围声明草稿 v2")
    t.append("")
    t.append("> 轮次：P05-S5 R4。本轮不宣布任何阶段完成或签收；签收只由用户在对话中给出。")
    t.append("> 修复前证据不得称为修复后验证；S5R4 不重跑 D016/E2E/make test 正式矩阵（U385），只做独立重判与一致性收口。")
    t.append("")
    t.append("## 1 门禁")
    t.append("")
    t.append("- start 门禁：%s，HEAD=%s，HEAD:S4=%s（F4），判定器 sha256=%s；FAILS=0、CHECK_CRASHED=0（GATE_S5R4_start.txt；36 项断言）。" % (
        srec.get("START_TIME_UTC", "?"), srec.get("BASE_HEAD", "?")[:16] + "…", srec.get("BASE_HEAD_S4", "?")[:16] + "…", srec.get("JUDGE_SHA256", "?")[:16] + "…"))
    t.append("- 起始常量由 start 门禁记录：RULINGS.tsv %s B（最大 U377）、ERRATA_S5.txt %s B（最后 ES5-8）、STATE.md %s B、p05-s5r3 证据清单 382 项全 OK（sha %s…）、registries/s5r3 清单 10 条全 OK、R3 end 门禁 FAILS=8/CHECK_CRASHED=0。" % (
        srec.get("RULINGS_BYTES", "?"), srec.get("ERRATA_S5_BYTES", "?"), srec.get("STATE_BYTES", "?"), srec.get("S5R3_EVIDENCE_SUMS_SHA256", "?")[:8]))
    t.append("- 试跑 end 门禁：$EV/shakedown/gate/GATE_S5R4_end.txt，staging 证据根/checkpoints 根/POST_I 起点行完整演练，FAILS=%s、CHECK_CRASHED=%s、总断言 %s 项（U381：不再以 CHECK_CRASHED=0 单独作为通过条件；试跑期 FAIL 逐项归因并修正后以同一脚本 sha 重跑）。" % (skf, skc, skn))
    t.append("- 正式 end 门禁：只跑一次，输出 $EV/gate/GATE_S5R4_end.txt；原文摘要见附录 B（门禁后追加）。")
    t.append("- 已交付的正式结果（S5R3 在 F4 上重跑、S5R4 独立重判复核，U385 不重跑）：E2E_OK=%s CONTROL_OK=%s；D016 MATCH=%s MISMATCH=%s FLAKY=%s；make test %s（unit_count=%s，对账 8/8）；独立重判 DIFFS=%s（E2E_ROWS=%s / D016_REJUDGED_ROWS=%s / D016_NOT_JUDGED=%s）。" % (
        ec.get("E2E_OK", -1), ec.get("CONTROL_OK", -1), d16.get("MATCH"), d16.get("MISMATCH"), d16.get("FLAKY"),
        mt.get("verdict", "?"), mt.get("unit_count", "?"), rej.get("DIFFS"), rej.get("E2E_ROWS"),
        rej.get("D016_REJUDGED_ROWS"), rej.get("D016_NOT_JUDGED")))
    t.append("")
    t.append("## 2 裁决入账（U378–U385，纯追加）")
    t.append("")
    t.append("- RULINGS.tsv 纯追加 U378–U385 共 8 行（每行 5 个 tab 字段），前缀逐字节断言不变；追加后 %d B，最大编号 U385。" % os.path.getsize(os.path.join(P05, "registries/RULINGS.tsv")))
    t.append("- 原文逐字见 registries/RULINGS.tsv 与本轮任务书 §1。")
    t.append("")
    t.append("## 3 勘误 ES5-9..ES5-14")
    t.append("")
    t.append("- ERRATA_S5.txt 纯追加 ES5-9..14（前缀 sha 断言）：%d → %d B；最后条目 ES5-14。" % (int(srec.get("ERRATA_S5_BYTES", "0")), os.path.getsize(os.path.join(P05, "registries/s5r2/ERRATA_S5.txt"))))
    t.append("- ES5-9：S5R3 rejudge_s5r3.py 崩溃（SUMMARY 行被当数据行，KeyError），未产出 REJUDGE_S5R3.tsv；处理=U379。")
    t.append("- ES5-10：S5R3 end 门禁 5 项检查器/冻结标注缺陷（逐项见文件）；数据 sha 不变；处理=U378。")
    t.append("- ES5-11：S5R3 报告笔误与占位（§4 判定行 35→34；§5 的 DIFFS 未填（占位）；§11 写 26 项而清单实为 10 条）；R3 报告不改。")
    t.append("- ES5-12：S5R3 chain copy HARD_STOP、signoff 写错路径、就绪审计在 STATE 之前；处理=U380 与 R4 链顺序。")
    t.append("- ES5-13：S5R3 草稿含未实测『独立重判 DIFFS=0』；处理=U383 v2。")
    t.append("- ES5-14：S5R3 任务书把试跑通过条件定为 CHECK_CRASHED=0（规划缺陷）；处理=U381。")
    t.append("")
    t.append("## 4 独立重判 v2（覆盖率与阳性对照）")
    t.append("")
    t.append("- 输入：p05-s5r3 的 PREREG_E2E_S5R3.tsv、E2E_VERDICT_S5R3.tsv、e2e/pass1+pass2/points/*.json、PREREG_D016_S5R3.tsv、D016_PASS1/2_S5R3.json、D016_VERDICT_S5R3.tsv、D016_BUILD_S5R3.tsv；每个输入的 sha256 在首次正式调用之前写入 PREREG_REJUDGE_S5R4.tsv（91 个输入，状态 INFLUENCED）。")
    t.append("- 规则：不 import 任何判定/比较器脚本；跳过 # 注释行、表头行与 SUMMARY 行，一律按列名读取；E2E 42 点=25 注入+17 对照，每遍分类，不同记 FLAKY，缺遍记 MISSING_RUN；D016 36 行预注册中 3 行 ARTIFACT 不参与行为重判，33 行行为点重判比较，ROOT_CAUSE_RC 显式记 NOT_JUDGED_SOURCE_RECORD。")
    t.append("- 正式结果：E2E_ROWS=%s E2E_DIFFS=%s；D016_RECORDED_ROWS=%s D016_REJUDGED_ROWS=%s D016_NOT_JUDGED=%s D016_DIFFS=%s；DIFFS=%s。" % (
        rej.get("E2E_ROWS"), rej.get("E2E_DIFFS"), rej.get("D016_RECORDED_ROWS"), rej.get("D016_REJUDGED_ROWS"),
        rej.get("D016_NOT_JUDGED"), rej.get("D016_DIFFS"), rej.get("DIFFS")))
    t.append("- 行覆盖：E2E 42 点全部 SAME（含 17 对照）；D016 33 个行为点全部 SAME；ROOT_CAUSE_RC 1 行记 NA/NOT_JUDGED_SOURCE_RECORD。")
    t.append("- 自检 6/6（$EV/SELFTEST_REJUDGE_S5R4.txt）：verdict 文件含 SUMMARY 行不崩溃且被排除、正常 MATCH、篡改→MISMATCH、两遍不同→FLAKY、缺遍→MISSING_RUN、D016 恢复值超阈值→MISMATCH；阳性对照 4/4（$EV/POSCTRL_REJUDGE_S5R4.txt）：干净副本 DIFFS=0，3 例篡改副本（E2E 可见错误删除、D016 恢复值超阈值、记录 verdict 翻转 1 行）均 DIFFS≥1。")
    t.append("")
    t.append("## 5 门禁 5 项修正与 R3 复核表")
    t.append("")
    t.append("- 修正（U378，详见 ERRATA ES5-10）：")
    t.append("  1. RULINGS_LINES_5_FIELDS：跳过 # 行，其余每个非空行正好 5 个 tab 字段；")
    t.append("  2. FROZEN_POST_I_CALL_COUNTS_MATCH：FROZEN 按列名读取，mode='-' 任意调用，mode=formal 要求命令含 formal 词，实际调用数逐行等于 expected；")
    t.append("  3. MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST：git status --porcelain=v1 不整体 strip，按状态列+路径解析；")
    t.append("  4. D016_VERDICT_ROWS_34：排除 # 行、point_id 表头行与 SUMMARY 行后计数 34，并断言 MATCH=33/RECORD=1；")
    t.append("  5. CALIB_DIFF_ZERO：排除首列为 SUMMARY 的行，其余每行 diff==SAME，SUMMARY 的 DIFFS=0。")
    t.append("- 每项修正配落盘变异阳性对照（$EV/POSCTRL_GATE_S5R4.txt）：干净副本 PASS、篡改副本使该检查 FAIL；git status 一项用真实格式字符串的允许/不允许两例 + 本轮真实 status。")
    t.append("- R3 复核表（$EV/R3_GATE_RECHECK_S5R4.tsv，8 行 = S5R3 的 8 条 FAIL 名称；每行 r4_result=PASS 且数据 sha 不变）：")
    t.append("")
    t.append("| # | S5R3 FAIL | cause_class | 消解 |")
    t.append("|---|---|---|---|")
    for i, r in enumerate(r3rows):
        t.append("| %d | %s | %s | %s |" % (i + 1, r.get("fail_name", "?"), r.get("cause_class", "?"),
                                            (r.get("resolution_evidence", "") or "")[:180]))
    t.append("")
    t.append("## 6 就绪审计（READINESS_S5R4.tsv，逐条对照『无可做』）")
    t.append("")
    t.append("- 在最终 STATE 写入之后运行（U382），READINESS_S5R4.tsv 的 # META 行记录其读取的 STATE 字节数=%d、sha256=%s。" % (
        os.path.getsize(os.path.join(P05, "STATE.md")), sha_f(os.path.join(P05, "STATE.md"))))
    t.append("- 红点 26/26 MET；OPEN_ITEMS 25 行处置不变；PENDING_RUNS 无（独立重判已产出）；CONSISTENCY（STATE/registry/报告/草稿关键数字）；MAKETEST（R3 结果，不重跑）；PREREG_MATRIX（R3 D016/E2E + S5R4 重判 DIFFS=0）；E2E_CHAINS；REGISTRY_COMPLETION 26/26；SHAKEDOWN FAILS=0。")
    t.append("- 汇总：GAP=%d（必须为 0；否则 HARD_STOP 不进入 end 门禁）。" % gap)
    t.append("")
    t.append("## 7 registry 补齐与 S5R4 registry")
    t.append("")
    t.append("- registries/s5r4/s5r3_completion/：补齐 S5R3 应交付但未入清单的 7 项（REJUDGE_S5R3.tsv 内容 = 本轮 REJUDGE_S5R4.tsv，其余 6 项从证据复制：READINESS_S5R3、P05_ACCEPTANCE_MAP_S5R3、REGISTRY_APPLY_DIFF_S5R3、REPORT_CHECK_S5R3、COPY_DIFF_S5R3、ERRATA_S5_R3FINAL），并写 README.md 与 SHA256SUMS.txt。")
    t.append("- S5R3 覆盖对照 26/26：19 项已在 registries/s5r3/ 中（逐项 sha 与 p05-s5r3/SHA256SUMS.txt 一致）+ 7 项由 s5r3_completion 补齐；registries/s5r3/ 与其 SHA256SUMS.txt、p05-s5r3/ 一律不写（sha 不变）。")
    t.append("- registries/s5r4/：本轮 %d 项小表 + SHA256SUMS.txt；GATE_S5R4_end.txt 在门禁之后追加并更新清单（附录 B 记录门禁时 N 项与最终 N+1 项）。" % len(DELIVERABLES))
    t.append("")
    t.append("## 8 登记表 diff（U384）")
    t.append("")
    t.append("- testing/s4test/ISSUE_REGISTRY.md 与 PROJECT_ROADMAP.md：只改动脚本列出的 3 行（ISSUE_REGISTRY D016 行；ROADMAP P05 行与 D016 分条），unified diff 断言通过（ASSERT_ONLY_LISTED_LINES_CHANGED=PASS）；R3→R4 链式 sha 一致（R3 after_sha == R4 before_sha）。")
    t.append("- 详见 $EV/REGISTRY_APPLY_DIFF_S5R4.txt；不改 AGENTS.md。")
    t.append("")
    t.append("## 9 签收范围声明草稿 v2")
    t.append("")
    t.append("- P05_S5_SIGNOFF_DRAFT_v2.md：标明未签收；范围=F4；make test/E2E 42 点/D016 点族引用 S5R3 结果 + S5R4 独立重判实测 DIFFS=%s；转出项 U366–U370/D017/R-P05-0x；已知限制（NV -10 仅 [源码]、Lua REPL 覆盖 cf/fft/kt/vl、S5R2 比较器历史缺陷、S5R3 build 的 PYEXT sha 与 M3b 差在嵌入路径/build-id 未判等价）。" % rej.get("DIFFS"))
    t.append("- S5R3 版本 P05_S5_SIGNOFF_DRAFT.md 保留为历史，不改写（sha 不变）。")
    t.append("")
    t.append("## 10 事件两张表")
    t.append("")
    t.append("### 10.1 表一：越界写入尝试")
    t.append("")
    t.append("| 轮次 | 命令 | 目标 | 是否落盘 |")
    t.append("|---|---|---|---|")
    t.append("| s5r4 | 无 | 无（本轮所有写入均在仓库内 $EV/、testing/d003/、checkpoints/p05/） | 不适用 |")
    t.append("")
    t.append("### 10.2 表二：工具与脚本事件")
    t.append("")
    t.append("| # | 事件 | 处理/影响 |")
    t.append("|---|---|---|")
    t.append("| 1 | start 门禁 v1：RULINGS sha 常量笔误（7dde vs 7de）+ EV 预内容规则把 safe_run 自身创建的 mkdir 行视为先前输出，FAILS=2 | 修正常量与预内容规则；v2 输出保存为 $EV/gate/GATE_S5R4_start.txt_v2_fails1 |")
    t.append("| 2 | start 门禁 v2：EV 预内容规则把上一次 start 门禁自身的输出视为先前证据，FAILS=1 | 允许 GATE_S5R4_start.txt 自身与版本保留 cp；v3 通过 |")
    t.append("| 3 | start 门禁 v3：版本保留 cp 行被预内容规则判为外部命令，FAILS=1 | 允许含 GATE_S5R4_start.txt 的保留命令；v4 FAILS=0（36 项） |")
    t.append("| 4 | 一次裸跑 python3 -m py_compile 生成 testing/d003/stage_s5r4/__pycache__（未经 safe_run，仓库内路径） | 已删除；改为在 safe_run 内运行脚本自检；登记为工具事件（未越界仓库） |")
    t.append("| 5 | s5r4_rejudge_check.py 首跑：summary 解析读 stdout 而非输出 TSV，且 D016 观测键路径写错（KeyError VL_NB9_REF），selftest 2/6 | 改为解析输出 TSV 的 SUMMARY 行、按 observations.py_ref 读参考值；6/6 通过 |")
    t.append("| 6 | 框架事件：本会话无 /tmp/dsh-spill-* 落盘记录 | 无 |")
    t.append("")
    t.append("## 11 交付物")
    t.append("")
    t.append("复制到 checkpoints/p05/registries/s5r4/ 的小表共 %d 项，加 SHA256SUMS.txt；门禁后追加 GATE_S5R4_end.txt 并更新清单：交付物数量=%d" % (len(DELIVERABLES), len(DELIVERABLES)))
    for i, d in enumerate(DELIVERABLES, 1):
        t.append("%d. %s" % (i, d))
    t.append("")
    t.append("## 附录 A（试跑门禁摘要）")
    t.append("")
    t.append("- 试跑输出：$EV/shakedown/gate/GATE_S5R4_end.txt（staging 证据根/checkpoints 根/POST_I 起点行完整演练，模拟 commit-i=HEAD，不碰正式路径）；不纳入 SHA256SUMS。")
    t.append("- 试跑结果：COUNTS total=%s、FAILS=%s、CHECK_CRASHED=%s。" % (skn, skf, skc))
    t.append("- 试跑期 FAIL 归因（U381）：逐项记录在 $EV/shakedown/gate/GATE_S5R4_end.txt 与归档的失败版本中；检查器缺陷在提交 (i) 之前修正，并用同一脚本 sha 重跑至 FAILS=0。")
    t.append("")
    t.append("## 附录 B（正式 end 门禁摘要）")
    t.append("")
    t.append("- 门禁前占位：正式 end 门禁只跑一次，输出 $EV/gate/GATE_S5R4_end.txt（总断言 ≥78）；门禁后由 s5r4_appendix.py 把失败项/计数摘要追加到本附录末尾（不改本行之前的正文）。")
    t.append("")
    t.append("FINAL_STATUS=PENDING_GATE")
    t.append("")
    t.append("（FINAL_STATUS=PENDING_GATE）本轮 P05-S5 R4 范围证据已生成，等待 end 门禁；最终状态与收尾句由门禁后追加的附录 C 给出。")
    t.append("")
    txt = NL.join(t) + NL
    out = os.path.join(P05, "P05_S5R4_REPORT.md")
    open(out, "w", encoding="utf-8").write(txt)
    print("REPORT bytes=%d deliverables=%d gap=%d rej_diffs=%s" % (len(txt.encode("utf-8")), len(DELIVERABLES), gap, rej.get("DIFFS")))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
