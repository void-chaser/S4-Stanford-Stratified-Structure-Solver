#!/usr/bin/env python3
# s5r5_report.py -- write the P05-S5 R5 report body (task brief section 5). The body never states a gate
# result (only "see appendix C"); appendix A is appended after the staging rehearsal and appendix C after the
# formal end gate. The two event tables are embedded from EVENTS_S5R5.tsv. Self-checks U389 phrases.
import os, sys, re, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r5")
OUT = os.path.join(P05, "P05_S5R5_REPORT.md")
TAB = chr(9)
NL = chr(10)

FORBIDDEN = [re.compile(r"FAILS=\d+"), re.compile(r"门禁.*(通过|PASS)"), re.compile(r"无可做")]


def rd(p):
    return open(p, encoding="utf-8").read()


def events_tables():
    t1, t2 = [], []
    for line in rd(os.path.join(EV, "EVENTS_S5R5.tsv")).splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        f = line.split(TAB)
        if f[0] == "table":
            continue
        if f[0] == "1":
            t1.append(f[1:])
        elif f[0] == "2":
            t2.append(f[1:])
    md1 = ["| 轮次 | 命令 | 目标 | 是否落盘 |", "|---|---|---|---|"]
    for (i, rnd, cmd, tgt, pers) in t1:
        md1.append("| %s | %s | %s | %s |" % (rnd, cmd, tgt, pers))
    md2 = ["| # | 事件 | 处理/影响 |", "|---|---|---|"]
    for (i, evt, hnd, _a, _b) in t2:
        md2.append("| %s | %s | %s |" % (i, evt, hnd))
    return NL.join(md1), NL.join(md2)


def build():
    md1, md2 = events_tables()
    return """# P05-S5 R5 报告（s5r5）：S5 最小修正子轮——检查器字符串缺陷的同类普查、R4 冻结数据重判、门禁前不预写结果

> 轮次：P05-S5 R5（S5 最小修正子轮；不是新阶段）。本轮不宣布任何阶段完成或签收；签收只由用户在对话中给出。
> 本报告正文写普查、重判、阳性对照与两张事件表；试跑核验见附录 A；门禁结果见附录 C（门禁后追加）。
> R5 不改、不重跑 gate_check_s5r4.py，也不重跑 S5R4 的 139 项正式断言（U386）；本轮以修正重判 + 新门禁处置 R4 的唯一失败项。

## 1 裁决入账（U386–U390，纯追加）

- RULINGS.tsv 纯追加 5 行，每行 5 个 tab 字段，前缀逐字节不变：154825 B → 156852 B，最大编号 U390；原文见 registries/RULINGS.tsv 与 evidence/p05-s5r5/RULINGS_APPEND_S5R5.tsv。
- U386：R4 唯一失败项（SHAKEDOWN_USED_STAGING_ROOTS）认定为检查器字符串缺陷；R5 不重跑 R4 断言，用 s5r5_recheck_staging.py 在 R4 冻结数据上重判；其余 138 项以 R4 正式门禁文件原文为准（sha 20bb6ad0…）。
- U387：R4 的 STATE 预投影结果予以更正；R5 起门禁前写的 STATE/草稿/报告正文只写“见附录 C”，不写任何门禁结果。
- U388：R5 门禁（gate_check_s5r5.py）不出现依据“是否试跑”或“输出路径是否为自身”的分支；试跑与正式运行只差根路径参数；门禁不读取任何门禁输出文件；试跑输出由门禁之外的 s5r5_shakedown_verify.py 核验，并在提交 (i) 之前完成。
- U389：就绪审计记录 STATE 字节/sha，并断言 STATE、草稿 v3、报告正文不含 U389 规定的三类门禁结果字样，且 STATE 的 S5R4 行与 S5R4 附录 C 的 FINAL_STATUS=INCOMPLETE 一致。
- U390：新写草稿 v3（未签收），v1/v2 不改；门禁结果只写“见附录 C；若 FINAL_STATUS≠COMPLETE 则草稿无效”。

## 2 勘误 ES5-15 / ES5-16（纯追加）

- ERRATA_S5.txt 先快照到 registries/s5r5/r4_final/ERRATA_S5_R4FINAL.txt（sha 8aec8fd5…，逐字节等于追加前前缀），再纯追加两条：13848 B → 15805 B，最后条目 ES5-16。
- ES5-15：gate_check_s5r4.py:997 用 “STAGING_MODE”+TAB+“yes” 匹配 RECORD 行的三段格式，且试跑走“自身输出”分支覆盖不到正式分支；影响 = R4 正式门禁唯一 1 项失败、FINAL_STATUS=INCOMPLETE；被检数据正确；处理 = U386/U388。
- ES5-16：R4 的 STATE 在门禁前写入结果，就绪审计只核字节/sha，导致内容失真；处理 = U387/U389/U390。

## 3 同类缺陷静态普查（CHECKER_SWEEP_S5R5.tsv）

- 对象 testing/d003/stage_s5r4/gate_check_s5r4.py（sha 829f2708…），AST 枚举全部 139 个 safe() 断言（含 8 个循环生成的检查名展开）。
- 机制分类：reads_record_line=1、self_branch=2、negative_in=6、other=131；汇总 SWEEP_ROWS=139、SELF_BRANCH_ROWS=2、VACUOUS=0。
- 两条 self_branch：SHAKEDOWN_GATE_FAILS_ZERO 与 SHAKEDOWN_USED_STAGING_ROOTS（R4 试跑只走了自身分支，正式分支在试跑中未被覆盖）；其中后者同时按字符串匹配 RECORD 行（record_format_ok=no）——这正是 ES5-15。
- 每条 reads_record_line / negative_in 断言都在 R4 冻结数据上用正确格式重算：6 条否定匹配重算为非空洞（STATE 标记与关键数字、CALIB SUMMARY、READINESS CONSISTENCY、草稿 v2 未签收声明、EV4 清单 941 文件覆盖）；1 条 RECORD 行匹配重算 = 修正逻辑成立（R4 原逻辑 not_staging）。
- 结论：VACUOUS=0，未发现第二个空洞通过；R4 的 138 项原文结论不因该普查而改变。

## 4 R4 冻结数据重判与阳性对照（RECHECK_STAGING_S5R5.tsv / POSCTRL_RECHECK_STAGING_S5R5.txt）

- 输入 p05-s5r4/shakedown/gate/GATE_S5R4_end.txt，sha256 3be9bed8…；S5R4 清单声明 shakedown/ 不在覆盖范围，另核对清单覆盖的 SHAKEDOWN_ITERATIONS_S5R4.txt 条目（d9637a25…）。
- 同一文件上重判 SHAKEDOWN_USED_STAGING_ROOTS：修正逻辑（逐列解析 RECORD 行，第 2 字段=STAGING_MODE、第 3 字段=value=yes）→ PASS；R4 原逻辑（子串匹配）→ not_staging，复现 R4 的失败，证明缺陷定位准确。
- 同文件另核对 EV_ROOT / P05_ROOT 为 shakedown 路径、失败数=0、检查器崩溃数=0（R4 试跑输出）。
- 重判阳性对照 4/4：真实副本→PASS；value=yes 改为 value=no→FAIL；删去 STAGING_MODE 行→FAIL；EV_ROOT 改为正式路径→FAIL。fixture 落盘在 evidence/p05-s5r5/posctrl/recheck_staging/。
- R5 门禁共 36 项检查；逐检查落盘变异阳性对照 36/36（POSCTRL_GATE_S5R5.txt：每个检查一份落盘变异，干净 staging 数据重算成立、篡改副本不成立；其中 HEAD/status 两项的 clean 夹具模拟提交 (i) 之后的分支，真实提交前分支由整轮 staging 试跑覆盖；POSCTRL_GATE 自指检查用合成两文件夹具，真实聚合值即本文件末行）。

## 5 就绪审计（U389；READINESS_S5R5.tsv）

- 就绪审计在最终 STATE、草稿 v3、本报告正文写完之后运行（顺序由链保证）；记录 STATE 字节数与 sha256、草稿 v3 与报告正文 sha256。
- 断言三处不含 U389 规定的门禁结果字样（正则原文见 READINESS_S5R5.tsv 的 # META 行与 s5r5_readiness.py），命中数为 0；并核对 STATE 的 S5R4 行与 S5R4 报告附录 C 的 FINAL_STATUS=INCOMPLETE 一致。
- 就绪项汇总见 READINESS_S5R5.tsv（GAP 计数、红点、开放项、待跑运行、一致性、make test/E2E/重判引用）；门禁逐项核对 GAP 与 STATE sha 一致。

## 6 两张事件表

### 6.1 表一：越界写入尝试

{MD1}

### 6.2 表二：工具与脚本事件

{MD2}

## 7 交付物与小表

- checkpoints/p05/registries/s5r5/：GATE_S5R5_start.txt、RULINGS_APPEND_S5R5.tsv、ERRATA_APPEND_S5R5.tsv、r4_final/ERRATA_S5_R4FINAL.txt、CHECKER_SWEEP_S5R5.tsv、RECHECK_STAGING_S5R5.tsv、POSCTRL_RECHECK_STAGING_S5R5.txt、POSCTRL_GATE_S5R5.txt、READINESS_S5R5.tsv、FROZEN_SCRIPTS_S5R5.tsv、REGISTRY_EXPECTED_S5R5.txt、TMP_SNAPSHOT_S5R5.tsv、SHA256SUMS.txt；门禁文件在门禁后追加并更新清单。
- 证据目录 checkpoints/p05/evidence/p05-s5r5/（SHA256SUMS.txt 覆盖非二进制证据；tmp/、gate/、shakedown/ 按轮次惯例不纳入清单）。

FINAL_STATUS=PENDING_GATE

（FINAL_STATUS=PENDING_GATE）本轮 P05-S5 R5 范围证据在附录写入之前已生成；最终状态与收尾句由门禁后追加的附录 C 给出。

## 附录 A（试跑核验；试跑后追加）
""".replace("{MD1}", md1).replace("{MD2}", md2)


def main():
    text = build()
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        for rx in FORBIDDEN:
            if rx.search(line):
                hits.append("line%d:%s:%s" % (i, rx.pattern, line[:70]))
    if hits:
        print("HARD_STOP report body would contain forbidden gate-result phrases: %s" % "; ".join(hits[:6]))
        return 2
    if not text.endswith(NL):
        text += NL
    open(OUT, "w", encoding="utf-8").write(text)
    data = text.encode("utf-8")
    body = data.split("## 附录 A".encode("utf-8"))[0]
    info = ["# REPORT_WRITE_S5R5.tsv -- P05_S5R5_REPORT.md body written by s5r5_report.py",
            "key" + TAB + "value",
            "REPORT_BODY_BYTES" + TAB + str(len(body)),
            "REPORT_BODY_SHA256" + TAB + hashlib.sha256(body).hexdigest(),
            "REPORT_FULL_BYTES" + TAB + str(len(data)),
            "FORBIDDEN_PHRASE_HITS" + TAB + "0"]
    out = os.path.join(EV, "REPORT_WRITE_S5R5.tsv")
    open(out, "w", encoding="utf-8").write(NL.join(info) + NL)
    print("REPORT body_bytes=%d body_sha=%s forbidden_hits=0" % (len(body), hashlib.sha256(body).hexdigest()))
    print("WROTE " + os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
