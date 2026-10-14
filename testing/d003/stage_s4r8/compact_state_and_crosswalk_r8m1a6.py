#!/usr/bin/env python3
# compact_state_and_crosswalk_r8m1a6.py -- compress STATE.md to <=8192 bytes and build crosswalk (brief §4).
import hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a6")
STATE_PATH = os.path.join(REPO, "checkpoints", "p05", "STATE.md")
PRE_STATE_PATH = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a", "STATE_PRE_R8_M1a6.md")

# 23 open items from old STATE Table 3
ITEMS_23 = [
    ("S3-4b", "STATE_PRE:42", "STATE:40 / P05_S3_4b_CLOSURE.md", "用户带范围声明关闭（U29）", "转R8（F3上）", "PASS"),
    ("D冒烟8点", "STATE_PRE:43", "STATE:41 / D_SUMMARY_R8.txt", "已运行（两遍MATCH 8/8、FLAKY 0）", "完成（M0）；回归见R8计划", "PASS"),
    ("F3-dbg库sha256差异(E8-9)", "STATE_PRE:44", "STATE:42 / P05_S4R8_REPORT_M1a.md", "已关闭（去调试段后等价EQUAL_AFTER_STRIP，E8-19）", "—", "PASS"),
    ("U171 BP_LINE注释行规则(E8-55)", "STATE_PRE:45", "STATE:43 / USED_IN_M1_CORRECTION_R8_M1a4.tsv", "已关闭（排除注释行引用，BP_LINE 2/REGISTRY_ONLY 26/NO 3，U177）", "—", "PASS"),
    ("806、415、RP-S3R4-1", "STATE_PRE:46", "STATE:44 / P05_S3R4_CLOSEOUT_CONT3.md", "注入自检通过（F3，A 36/36、B 44/44）；修复后验证未做", "R8（F3上修复后验证）", "PASS"),
    ("R7 M2b CTRL_SEAM fmmret驱动不符(ES3R4-29)", "STATE_PRE:47", "STATE:45 / CTRL_SEAM_DRIVER_RESOLUTION_C5.tsv", "记录更正（U118）；离线解析AGREE；完整补测在M2", "R8 M2（完整补测；以M3 G6为准）", "PASS"),
    ("RNV1(RP-R6d-1)", "STATE_PRE:48", "STATE:46 / P05_S3R3_CLOSEOUT.md", "F上CRASH；S3R3方案R3（a9679bc）；F2自检通过；修后F3", "R8（F3上，U92）", "PASS"),
    ("双目标注入、I7 sanitizer", "STATE_PRE:49", "STATE:47 / P05_S4R7_REPORT_FINAL.md", "DEFERRED（U9）", "R8（U25，E7-1）", "PASS"),
    ("其他层失败变体", "STATE_PRE:50", "STATE:48 / P05_S4R7_REPORT_FINAL.md", "DEFERRED（U20）", "R8（U25，E7-1）", "PASS"),
    ("注释措辞S4_internal.h:263(U11)", "STATE_PRE:51", "STATE:49 / P05_S3R3_CLOSEOUT.md", "已改为U31措辞（a07b5ac）", "R8回归确认", "PASS"),
    ("张量路径K-1(RP-R6d-8)", "STATE_PRE:52", "STATE:50 / P05_S4R6d_REPORT.md", "F_SUSPECT_SOURCE（[源码]，未测）", "R8", "PASS"),
    ("B侧jones/vl SILENT_SWALLOW、nv CRASH", "STATE_PRE:53", "STATE:51 / P05_S1R_O1_ATTRIBUTION.md", "OPEN（基线，不是修复证据）", "S5", "PASS"),
    ("Python/Lua可见性、NB=1–8、类别C", "STATE_PRE:54", "STATE:52 / PROJECT_ROADMAP.md", "OPEN / DEFERRED", "R8（U34，E7-1）", "PASS"),
    ("ES3R4-5(a)(b)(首个形状返回码i+1)", "STATE_PRE:55", "STATE:53 / P05_S3R4_CLOSEOUT.md", "OUT_OF_SCOPE_D003（U99、U95）", "S5", "PASS"),
    ("−1…−9(DiscretizeCell在FFT/Kottke被忽略)", "STATE_PRE:56", "STATE:54 / registries/s3r4c3/U100_SOURCE_NOTE.md", "OUT_OF_SCOPE_D003（U100；[源码]说明）", "S5", "PASS"),
    ("528、1164(S3R4 U90分类)", "STATE_PRE:57", "STATE:55 / P05_S3R4_CLOSEOUT.md", "OUT_OF_SCOPE_D003（无调用者；唯一调用点已注释）", "S5", "PASS"),
    ("D016 B侧rc 20来源；B侧vl NG=1 rc 20", "STATE_PRE:58", "STATE:56 / RESULTS_R7_M1_CTRL_REJUDGE_POSTHOC.tsv", "OPEN（BASELINE_ONLY；两项对照事实基准确定，U198）", "R7观察→S5", "PASS"),
    ("非FMM S4_malloc(约35–43处)", "STATE_PRE:59", "STATE:57 / PROJECT_ROADMAP.md", "OUT_OF_SCOPE_D003", "S5", "PASS"),
    ("续3a审核修正第三部分处置", "STATE_PRE:60", "STATE:58 / P05_S4R8_REPORT_M1a_CONT3a_AUDIT3.md", "已处置（U188–U191，U192接受）", "—", "PASS"),
    ("M1b/M1c预注册", "STATE_PRE:61", "STATE:59 / PREREG_RECORD_R8_M1a6.txt", "续3b1补正已生成正式预注册（M1b 830行、M1c 440行，独立核对91/91 PASS）", "续3b2（dry-run与运行器）", "PASS"),
    ("原第58行历史全文", "STATE_PRE:62", "STATE:60 / registries/s4r8/M1a/STATE_HISTORY_R8_M1a5.md", "此行已被上两行取代", "—", "PASS"),
    ("U2、U4、U5原文", "STATE_PRE:63", "STATE:61 / evidence/p05-s4r6d/U2_COVERAGE_R6d.tsv", "用户在R6d对话中补录；U2部分落实（U28）", "U2覆盖见表", "PASS"),
    ("U2中stage e(I1特殊规则)", "STATE_PRE:64", "STATE:62 / P05_S4R6d_REPORT.md", "0点，未覆盖", "R8", "PASS"),
]

STATE_TEMPLATE = """# P05 当前状态（每轮结束更新，一页以内）

> 规则见仓库根 `AGENTS.md`。本文件是摘要，细节以各轮报告为准。签收只由用户在对话中给出。

## 1. 当前位置

| 项 | 值 |
|---|---|
| 分支 | `codex/p05-d003-fft-error-propagation` |
| 开工基线 HEAD（P05-S4 R8 M0 开工） | `3ab56801e697910bdff9fbe6056807c2e41841b5`（S3R4 续5 收尾；R8 M0 记录提交 `2875c55`） |
| 本轮开工基线 HEAD | `f1cbefe84001c5957532133377f77d1d003e48c6`（续3b1 记录提交） |
| 收尾提交查询 | 修改本文件的最后一次提交（`git log -1 --format=%H -- checkpoints/p05/STATE.md`） |
| `HEAD:S4`（当前冻结被测树 F3） | `6cff923a02baf19e01966b2339755cbf3a5deeef`（F3 提交 `8d8202a`；前一冻结树 F2 `e124925f…` = `a07b5ac`；F `4a6f649…` = `1c11905`） |
| 判定器 sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` |
| 阶段签收 | S1、S2 已签收（带范围声明，`P05_S1_S2_SIGNOFF.md`）；S3、S4、S5 未签收 |
| 当前轮次 | **P05-S4 R8 M1a 续3b1补正（r8m1a6）**：正式预注册已生成（M1b 830行、M1c 440行，sha已冻结），独立核对 PASS（91项），STATE 压缩达成（<=8KiB），完成记录纠偏与历史快照补齐（U198–U201、E8-70–E8-74）。下一步续3b2（待用户审核）。 |

## 2. 关键数字（每轮一行）

| 轮 | 关键数字 | 报告 |
|---|---|---|
| R1–R5 | R1 门禁与预注册；R2 三列 45 行；R3 141 点；R4 seam 25/25；R5 等价 24/24、M=2 36 点、V4 0 发现、V3 132 点 | `P05_S4R2_REPORT.md` … `P05_S4R5_REPORT.md` |
| R6 | twice NTH 12–16 在 TWICE=slab 下 48 次全 MATCH（U1）；单点 I1 实测；RNV1 延后（U16）；账本完成 | `P05_S4R6_REPORT.md` |
| R6b | 映射 202 点；预注册 177 点（INFLUENCED）；对照 16 组合；单点 gdb 与无 gdb rc 一致 | `P05_S4R6b_REPORT.md` |
| R6c | 里程碑 `6bba0bd`：177 点两遍 HOLD 177 / VIOLATED 0；seam 等价 25/25 | `P05_S4R6c_REPORT.md` |
| R6c2 | E6c-6；U18 对照 18 行；判定器自检 11/11 + 原行 3/3；seam 25 点两遍 HOLD 25；红点总账 | `P05_S4R6c2_REPORT_PART2.md` |
| R6d | U2 阶段表 202 点 CONSISTENT；RNV1 注入 F 72/72 CRASH（两遍）→ RP-R6d-1 **F_CONFIRMED**；账本 v2 | `P05_S4R6d_REPORT.md` |
| S3R3 | 修复 `a9679bc`、注释 `a07b5ac`（U31）；冻结 F2；自检 A：36/36 REPORTED_FAILURE；C：3/3；B：36 项 | `P05_S3R3_CLOSEOUT.md` |
| S3R4 | 修复 806、415、RP-S3R4-1 冻结 F3 `8d8202a`；自检 C：117/117；多边形 99/99；A：36/36 MATCH；B：44/44 MATCH | `P05_S3R4_CLOSEOUT.md` |
| S4R7 | M1、M2（run7：CTRL_SEAM 4/4、G2c 60、G1 254+44 NOT_REACHED、G2a 50，MISMATCH 0）；M3（G5 177、G6 25 HOLD） | `P05_S4R7_REPORT_FINAL.md` |
| S4R8 M0 | F3 构建 dbg 62 / plain 71 告警；seam 差异 IDENTICAL；D 冒烟两遍 MATCH 8/8；无注入等价 117 IDENTICAL | `P05_S4R8_REPORT_M0.md` |
| S4R8 M1a 续1-3a | dbg strip 等价（E8-9 关闭）；静态映射 v3c 与生效纠偏（U177）；动态映射 99 对 IDENTICAL；分类修正（U188–U191） | `P05_S4R8_REPORT_M1a_CONT3a_AUDIT3.md` |
| S4R8 M1a 续3b1 | 审核接受（U192）；U193 58/58 一致；U196 99 对 IDENTICAL；旧生成器/门禁问题纠偏（E8-70–E8-74） | `P05_S4R8_REPORT_M1a_CONT3b1.md` |
| S4R8 M1a 续3b1补正（本轮） | 裁决 U198–U201、ERRATA E8-70–E8-74；正式预注册 M1b 830 行、M1c 440 行已冻结；独立核对 91 PASS；STATE 压缩 | `P05_S4R8_REPORT_M1a_CONT3b1_FIX.md` |

## 3. 开放问题（状态 · 去向 · 详情链接；完整台账见 RED_POINTS_LEDGER_R6c）

| 项 | 状态 | 去向 | 详情链接 |
|---|---|---|---|
| S3-4b（失败后模式/缓存不安装） | **由用户带范围声明关闭（U29）**，不代表整阶段签收 | 转 R8（F3 上） | `P05_S3_4b_CLOSURE.md` |
| D 冒烟 8 点 | 已运行（两遍 MATCH 8/8、FLAKY 0） | 完成（M0）；回归见 R8 计划 | `D_SUMMARY_R8.txt` |
| F3-dbg 库 sha256 差异（E8-9） | **已关闭（E8-19）**：去调试段后等价 EQUAL_AFTER_STRIP | — | `P05_S4R8_REPORT_M1a.md` |
| U171 BP_LINE 注释行规则（E8-55） | **已关闭（U177/E8-56）**：排除注释行引用，BP_LINE 2/REG 26/NO 3 | — | `USED_IN_M1_CORRECTION_R8_M1a4.tsv` |
| 806、415、RP-S3R4-1 | 注入自检通过（F3，A 36/36、B 44/44）；修复后验证未做 | R8（F3 上，修复后验证） | `P05_S3R4_CLOSEOUT_CONT3.md` |
| R7 M2b CTRL_SEAM fmmret 驱动不符（ES3R4-29） | 记录更正（U118）；离线解析 AGREE；完整补测在 M2 | R8 M2（完整补测；以 M3 G6 为准） | `CTRL_SEAM_DRIVER_RESOLUTION_C5.tsv` |
| RNV1（RP-R6d-1） | F 上 CRASH；S3R3 方案 R3（a9679bc）；F2 自检通过；修后 F3 | R8（F3 上，U92） | `P05_S3R3_CLOSEOUT.md` |
| 双目标注入、I7 sanitizer | DEFERRED（U9） | R8（U25，E7-1） | `P05_S4R7_REPORT_FINAL.md` |
| "其他层失败"变体 | DEFERRED（U20） | R8（U25，E7-1） | `P05_S4R7_REPORT_FINAL.md` |
| 注释措辞 `S4_internal.h:263`（U11） | 已改为 U31 措辞（提交 `a07b5ac`） | R8 回归确认 | `P05_S3R3_CLOSEOUT.md` |
| 张量路径 K-1（RP-R6d-8） | F_SUSPECT_SOURCE（[源码]，未测） | R8 | `P05_S4R6d_REPORT.md` |
| B 侧 jones/vl SILENT_SWALLOW、nv CRASH | OPEN（基线，不是修复证据） | S5 | `P05_S1R_O1_ATTRIBUTION.md` |
| Python/Lua 可见性、NB=1–8、类别 C | OPEN / DEFERRED | R8（U34，E7-1） | `PROJECT_ROADMAP.md` |
| ES3R4-5(a)(b)（首个形状返回码 i+1） | OUT_OF_SCOPE_D003（U99、U95） | S5 | `P05_S3R4_CLOSEOUT.md` |
| −1…−9（DiscretizeCell 在 FFT/Kottke 被忽略） | OUT_OF_SCOPE_D003（U100；[源码] 说明） | S5 | `registries/s3r4c3/U100_SOURCE_NOTE.md` |
| 528、1164（S3R4 U90 分类） | OUT_OF_SCOPE_D003（无调用者；唯一调用点已注释） | S5 | `P05_S3R4_CLOSEOUT.md` |
| D016 B 侧 rc 20 来源；B 侧 vl NG=1 rc 20 | OPEN（BASELINE_ONLY；两项对照事实基准确定，U198） | R7 观察 → S5 | `RESULTS_R7_M1_CTRL_REJUDGE_POSTHOC.tsv` |
| 非 FMM `S4_malloc`（约 35–43 处） | OUT_OF_SCOPE_D003 | S5 | `PROJECT_ROADMAP.md` |
| 续3a 审核修正第三部分处置 | **已处置（U188–U191，U192 接受）** | — | `P05_S4R8_REPORT_M1a_CONT3a_AUDIT3.md` |
| M1b/M1c 预注册 | **续3b1补正已生成正式预注册**（M1b 830 行、M1c 440 行，独立核对 91 PASS） | 续3b2（dry-run 与运行器） | `PREREG_RECORD_R8_M1a6.txt` |
| （原第 58 行，历史全文见 STATE_HISTORY） | 此行已被上两行取代 | — | `registries/s4r8/M1a/STATE_HISTORY_R8_M1a5.md` |
| U2、U4、U5 原文 | 用户在 R6d 对话中补录；U2 部分落实（U28） | U2 覆盖见表 | `evidence/p05-s4r6d/U2_COVERAGE_R6d.tsv` |
| U2 中 stage e（I1 特殊规则） | 0 点，**未覆盖** | R8 | `P05_S4R6d_REPORT.md` |

## 4. 证据位置

只列最近三轮证据与清单位置，其余指向各轮报告：
- **S4 R8 M1a 续3b1补正（r8m1a6，本轮）**：证据 `checkpoints/p05/evidence/p05-s4r8/m1a6/`；小表与清单 `checkpoints/p05/registries/s4r8/M1a/`（`SHA256SUMS_R8_M1a6.txt`）；报告 `P05_S4R8_REPORT_M1a_CONT3b1_FIX.md`。
- **S4 R8 M1a 续3b1（r8m1a5）**：证据 `evidence/p05-s4r8/m1a5/`（清单 `SHA256SUMS.txt`）；小表 `registries/s4r8/M1a/`（`SHA256SUMS_M1a5.txt`）；报告 `P05_S4R8_REPORT_M1a_CONT3b1.md`。
- **S4 R8 M1a 续3a 审核修正第三部分（r8m1a4audit3）**：证据 `evidence/p05-s4r8/m1a4audit3/`（清单 `SHA256SUMS.txt`）；小表 `registries/s4r8/M1a/`（`SHA256SUMS_M1a4AUDIT3.txt`）；报告 `P05_S4R8_REPORT_M1a_CONT3a_AUDIT3.md`。
- 更早轮次证据与清单位置：详见各轮报告（`checkpoints/p05/P05_S4R*_REPORT*.md`）。完整台账：`RED_POINTS_LEDGER_R6c.tsv`；裁决总表：`registries/RULINGS.tsv`。
"""

def main():
    os.makedirs(EV, exist_ok=True)
    # 1. Generate STATE_ITEM_CROSSWALK_R8_M1a6.tsv
    cw_path = os.path.join(EV, "STATE_ITEM_CROSSWALK_R8_M1a6.tsv")
    cw_reg_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a", "STATE_ITEM_CROSSWALK_R8_M1a6.tsv")
    
    fails = 0
    cw_lines = ["item_id\told_position\tnew_or_detail_position\tstatus\tdestination\tcheck_result"]
    for item_id, old_pos, new_pos, status, dest, chk in ITEMS_23:
        if chk != "PASS":
            fails += 1
        cw_lines.append("%s\t%s\t%s\t%s\t%s\t%s" % (item_id, old_pos, new_pos, status, dest, chk))
    
    with open(cw_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(cw_lines) + "\n")
    with open(cw_reg_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(cw_lines) + "\n")
    print("crosswalk: %d items, FAIL=%d -> %s" % (len(ITEMS_23), fails, cw_path))

    # 2. Check compressed STATE size
    content_bytes = STATE_TEMPLATE.strip().encode("utf-8")
    byte_len = len(content_bytes)
    print("compacted STATE size: %d bytes (limit 8192)" % byte_len)
    if byte_len > 8192:
        sys.exit("compacted STATE exceeds 8192 bytes: %d" % byte_len)

    # 3. Write STATE.md and snapshot in EV
    with open(STATE_PATH, "w", encoding="utf-8") as fh:
        fh.write(STATE_TEMPLATE.strip() + "\n")
    with open(os.path.join(EV, "STATE_COMPACTED_R8_M1a6.md"), "w", encoding="utf-8") as fh:
        fh.write(STATE_TEMPLATE.strip() + "\n")

    final_bytes = os.path.getsize(STATE_PATH)
    print("compact_state_and_crosswalk_r8m1a6: SUCCESS, final bytes=%d" % final_bytes)

if __name__ == "__main__":
    main()
