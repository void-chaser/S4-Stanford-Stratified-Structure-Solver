#!/usr/bin/env python3
# s5r7_state.py -- regenerate checkpoints/p05/STATE.md for P05-S5 R7 (task brief section 2.4).
# The user gave the P05-S5 sign-off text in the conversation.  The STATE records S1-S5 as signed by the
# user, the S5 open-issue row as signed (U391), keeps the transferred items OPEN, and projects NO gate
# result: the R7 gate result is written only to P05_S5R7_REPORT.md appendix C after the formal gate.
# The script self-checks the STATE for forbidden projected-result phrases and for the 8 KB size cap.
import os, sys, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r7")
OUT = os.path.join(P05, "STATE.md")
NL = chr(10)
TAB = chr(9)

TEXT = """# P05 当前状态（每轮结束更新，一页以内）

> 规则见仓库根 AGENTS.md。本文件是摘要，细节以各轮报告为准。S5R5/S5R6 门禁结果见各自报告附录 C；
> S5R7 门禁结果见 P05_S5R7_REPORT.md 附录 C（门禁后追加），本文件不预写 S5R7 门禁结果。

## 1 当前位置

| 项 | 值 |
|---|---|
| 分支 | codex/p05-d003-fft-error-propagation |
| 本轮开工基线 HEAD（s5r7） | 0358a06ee41f0b78984834bfdb758dd1a793296c（P05-S5 R6 (ii)） |
| HEAD:S4（冻结被测树 F4） | 589e15eb11fcb04e031b524f25a443e7921946cf（F4 提交 05097a7） |
| 判定器 sha256 | d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb |
| 阶段状态 | S1–S5 已由用户签收（带范围声明；S5 见 P05_S5_SIGNOFF.md 与 U391） |
| 当前轮次 | P05-S5 R7（s5r7，纯文档子轮：P05-S5 签收入账 U391、入口同步；不是新阶段） |

## 2 关键数字（每轮一行）

| 轮 | 关键数字 | 报告/证据 |
|---|---|---|
| S5R3 | 裁决 U372–U377；勘误 ES5-6..8；D016 MATCH=33 MISMATCH=0 FLAKY=0；E2E 25 注入 + 17 对照；make test NO_NEW_FAILURE（unit_count=265）；独立重判缺失、readiness GAP=2、end 门禁 8 项 FAIL（见 R3 附录 C） | P05_S5R3_REPORT.md |
| S5R4 | 裁决 U378–U385；勘误 ES5-9..14；独立重判 DIFFS=0（E2E 42 点 SAME，D016 33 行为点 SAME + ROOT_CAUSE_RC NOT_JUDGED_SOURCE_RECORD）；S5R3 的 8 项门禁 FAIL 全部消解（数据 sha 不变）；readiness GAP=0；S5R3 registry 覆盖 26/26；试跑 139/139。更正（R5）：正式 end 门禁唯一 1 项 FAIL 为检查器字符串缺陷 ES5-15，FINAL_STATUS=INCOMPLETE（P05_S5R4_REPORT.md 附录 C）；R5 在 R4 冻结数据上的重判见 RECHECK_STAGING_S5R5.tsv | P05_S5R4_REPORT.md；registries/s5r4/ |
| S5R5 | 裁决 U386–U390；勘误 ES5-15/16；同类缺陷静态普查 SWEEP_ROWS=139、SELF_BRANCH_ROWS=2、VACUOUS=0；R4 冻结数据重判：修正逻辑成立、R4 原逻辑 not_staging；重判阳性对照 4/4；就绪审计见 READINESS_S5R5.tsv；end 门禁 36/36 FINAL_STATUS=COMPLETE（P05_S5R5_REPORT.md 附录 C） | P05_S5R5_REPORT.md；registries/s5r5/ |
| S5R6 | 无用户 P05-S5 签收原文：任务书第 2 节跳过，U391 未写，P05_S5_SIGNOFF.md 未创建；勘误 ES5-17（三条文字更正：(a) R5 表一命令管道符转义、(b) POSCTRL_GATE_S5R5.txt 只在证据目录交付、registries/s5r5 为 12 项、(c) R5 附录 A 的 COUNTS 重复）；R5 报告只追加附录 D（前 95 行 sha 不变）；入口同步 PROJECT_ROADMAP.md 与 ISSUE_REGISTRY.md；门禁结果见 P05_S5R6_REPORT.md 附录 C | P05_S5R6_REPORT.md；registries/s5r6/ |
| S5R7 | 用户给出 P05-S5 签收原文：checkpoints/p05/P05_S5_SIGNOFF.md §2 逐字照录（原文 sha256 c7af2fb2…；S1–S5 五行签收表）；RULINGS.tsv 追加 U391（5 字段，旧前缀 sha 不变）；STATE/ROADMAP/ISSUE 入口同步；转出项保持 OPEN；P05 五个正式阶段全部由用户签收，P06 可启动；门禁结果见 P05_S5R7_REPORT.md 附录 C | P05_S5R7_REPORT.md；registries/s5r7/ |

## 3 开放问题（状态 · 去向 · 详情链接）

| 项 | 状态 | 去向 | 详情链接 |
|---|---|---|---|
| S5 输入 25 行的最终处置 | 落位（已转出/已登记/已关闭） | 本表为唯一入口 | checkpoints/p05/P05_S5_OPEN_ITEMS.tsv |
| D017 非 FMM S4_malloc | OPEN（不在 P05 修） | 转出 P05，不阻塞 P06（U369） | registries/s5r2/D017_S4MALLOC_INVENTORY_S5R2.tsv |
| R-P05-01 / R-P05-02 / R-P05-03 | OPEN（不在 P05 修） | 转出 P05，不阻塞 P06（U366/U370） | ISSUE_REGISTRY；registries/s5r2/ERRATA_S5.txt |
| F10/F8/反事实通量/allzero/11.2 五哈希 | OPEN / 未验证 | 经 U366–U368 转出 P05 | P05_S5_OPEN_ITEMS.tsv；ERRATA_S5.txt |
| S5R3 遗留（独立重判缺失、readiness GAP、registry 清单不完整、8 项门禁 FAIL） | 已消解（R4） | S5R4 独立重判/recheck/readiness/registry 补齐 | P05_S5R4_REPORT.md 附录 B；registries/s5r4/ |
| R4 正式 end 门禁唯一 FAIL（检查器字符串缺陷，ES5-15） | 已重判（R5，R4 冻结数据只读） | U386/U388；R5 门禁不重跑 R4 门禁 | RECHECK_STAGING_S5R5.tsv；registries/s5r5/ |
| R5 报告文字瑕疵（ES5-17 三条） | 已更正（文字，不影响任何判定） | R6 追加勘误 ES5-17 与 R5 报告附录 D | registries/s5r2/ERRATA_S5.txt；P05_S5R5_REPORT.md 附录 D |
| S5 签收 | 已签收（U391） | 用户签收原文见 P05_S5_SIGNOFF.md §2；P05 收口，P06 可启动 | RULINGS.tsv U391；P05_S5_SIGNOFF.md |

## 4 证据位置

- **P05-S5 R7（s5r7）**：证据 checkpoints/p05/evidence/p05-s5r7/（SHA256SUMS.txt）；小表 checkpoints/p05/registries/s5r7/；报告 P05_S5R7_REPORT.md（门禁结果见附录 C）；签收文件 P05_S5_SIGNOFF.md；裁决 U391。
- **P05-S5 R6（s5r6）**：证据 checkpoints/p05/evidence/p05-s5r6/（只读，sha 不变）；小表 checkpoints/p05/registries/s5r6/；报告 P05_S5R6_REPORT.md；勘误 ES5-17 见 registries/s5r2/ERRATA_S5.txt 与 P05_S5R5_REPORT.md 附录 D。
- **P05-S5 R5（s5r5）**：证据 checkpoints/p05/evidence/p05-s5r5/（只读，sha 不变）；小表 checkpoints/p05/registries/s5r5/（含 r4_final/）；报告 P05_S5R5_REPORT.md；签收范围声明草稿 v3 P05_S5_SIGNOFF_DRAFT_v3.md（历史，未签收）。
- **P05-S5 R4（s5r4）**：证据 checkpoints/p05/evidence/p05-s5r4/（只读，sha 不变）；小表 checkpoints/p05/registries/s5r4/（历史）；报告 P05_S5R4_REPORT.md；草稿 v2 P05_S5_SIGNOFF_DRAFT_v2.md（历史，未签收）。
- **P05-S5 R3（s5r3）**：证据 checkpoints/p05/evidence/p05-s5r3/（只读，sha 不变）；报告 P05_S5R3_REPORT.md；草稿 v1 P05_S5_SIGNOFF_DRAFT.md（历史）。
- 裁决总表 registries/RULINGS.tsv（S5R7 追加 U391）；S5 勘误 registries/s5r2/ERRATA_S5.txt（末条 ES5-17，本轮未改）；R4 终版 ERRATA 快照 registries/s5r5/r4_final/ERRATA_S5_R4FINAL.txt。

（本文件由 s5r7_state.py 在正式链中生成）
"""

FORBIDDEN = ["FAILS=", "无可做"]


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def main():
    hits = [f for f in FORBIDDEN if f in TEXT]
    if hits:
        print("HARD_STOP STATE contains forbidden phrase(s): %s" % ",".join(hits))
        return 2
    if len(TEXT.encode("utf-8")) > 8192:
        print("HARD_STOP STATE too large")
        return 2
    data = (TEXT if TEXT.endswith(NL) else TEXT + NL).encode("utf-8")
    with open(OUT, "wb") as fh:
        fh.write(data)
    body = ["# STATE_WRITE_S5R7.tsv -- checkpoints/p05/STATE.md regenerated by s5r7_state.py",
            "key" + TAB + "value",
            "STATE_BYTES" + TAB + str(len(data)),
            "STATE_SHA256" + TAB + sha_b(data),
            "FORBIDDEN_PHRASE_HITS" + TAB + "0",
            "STATE_MARKERS" + TAB + "S5R7_ROW_S1_S5_SIGNED_U391_OPEN_ITEMS_KEPT",
            "S5_SIGNOFF" + TAB + "SIGNED_BY_USER_U391"]
    open(os.path.join(EV, "STATE_WRITE_S5R7.tsv"), "w", encoding="utf-8").write(NL.join(body) + NL)
    print("STATE bytes=%d sha=%s forbidden_hits=0" % (len(data), sha_b(data)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
