# P05 当前状态（每轮结束更新，一页以内）

> 规则见仓库根 AGENTS.md。本文件是摘要，细节以各轮报告为准。

## 1. 当前位置

| 项 | 值 |
|---|---|
| 分支 | codex/p05-d003-fft-error-propagation |
| 本轮开工基线 HEAD（s5r4） | e6a65ab4751c5ba5a5d6e2e0c093826d37312064（P05-S5 R3 (ii)） |
| HEAD:S4（冻结被测树 F4） | 589e15eb11fcb04e031b524f25a443e7921946cf（F4 提交 05097a7） |
| 判定器 sha256 | d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb |
| 阶段状态 | S1–S4 已由用户签收（带范围声明）；S5 收口 R4 完成收口补齐，未签收 |
| 当前轮次 | P05-S5 R4（s5r4，S5 收口补齐轮）；不宣布 S5 或 P05 阶段完成 |

## 2. 关键数字（每轮一行）

| 轮 | 关键数字 | 报告/证据 |
|---|---|---|
| S5R3 | 裁决 U372–U377；勘误 ES5-6..8；D016 MATCH=33 MISMATCH=0 FLAKY=0；E2E E2E_OK=25 CONTROL_OK=17；make test NO_NEW_FAILURE（unit_count=265）；独立重判缺失、readiness GAP=2、end 门禁 8 FAIL（见 R3 附录 C） | P05_S5R3_REPORT.md |
| S5R4 | 裁决 U378–U385；勘误 ES5-9..14；独立重判 DIFFS=0（E2E 42 点 SAME，D016 33 行为点 SAME + ROOT_CAUSE_RC NOT_JUDGED_SOURCE_RECORD）；S5R3 end 门禁 8 项 FAIL 全部消解（数据 sha 不变）；readiness GAP=0；S5R3 registry 覆盖 26/26；试跑 end 门禁 FAILS=0/CHECK_CRASHED=0；正式 end 门禁 FAILS=0（见 checkpoints/p05/evidence/p05-s5r4/gate/GATE_S5R4_end.txt） | P05_S5R4_REPORT.md；registries/s5r4/ |

## 3. 开放问题（状态 · 去向 · 详情链接）

| 项 | 状态 | 去向 | 详情链接 |
|---|---|---|---|
| S5 输入 25 行的最终处置 | 落位（已转出/已登记/已关闭） | 本表为唯一入口 | checkpoints/p05/P05_S5_OPEN_ITEMS.tsv |
| D017 非 FMM S4_malloc | OPEN（不在 P05 修） | 转出 P05，不阻塞 P06（U369） | registries/s5r2/D017_S4MALLOC_INVENTORY_S5R2.tsv |
| R-P05-01 / R-P05-02 / R-P05-03 | OPEN（不在 P05 修） | 转出 P05，不阻塞 P06（U366/U370） | ISSUE_REGISTRY；ERRATA_S5.txt ES5-9..14 |
| F10/F8/反事实通量/allzero/11.2 五哈希 | OPEN / 未验证 | 经 U366–U368 转出 P05 | P05_S5_OPEN_ITEMS.tsv；ERRATA_S5.txt |
| S5R3 遗留（独立重判缺失、readiness GAP、registry 清单不完整、8 项门禁 FAIL） | 已消解（R4） | S5R4 独立重判/recheck/readiness/registry 补齐 | P05_S5R4_REPORT.md 附录 B；registries/s5r4/ |
| S5 签收 | 等待用户审核 | S5R4 收口范围完成（无可做，GAP=0）；签收只由用户给出 | P05_S5_SIGNOFF_DRAFT_v2.md（未签收） |

## 4. 证据位置

- **P05-S5 R4（s5r4）**：证据 checkpoints/p05/evidence/p05-s5r4/（SHA256SUMS.txt）；小表 checkpoints/p05/registries/s5r4/（含 s5r3_completion/）；报告 P05_S5R4_REPORT.md；签收范围声明草稿 v2 P05_S5_SIGNOFF_DRAFT_v2.md（未签收）。
- **P05-S5 R3（s5r3）**：证据 checkpoints/p05/evidence/p05-s5r3/（只读，sha 不变）；小表 checkpoints/p05/registries/s5r3/（历史）；报告 P05_S5R3_REPORT.md；签收草稿 v1 P05_S5_SIGNOFF_DRAFT.md（历史）。
- 裁决总表 registries/RULINGS.tsv（追加 U378–U385）；S5 勘误 registries/s5r2/ERRATA_S5.txt（追加 ES5-9..14）；R3 终版 ERRATA 快照 registries/s5r4/s5r3_completion/ERRATA_S5_R3FINAL.txt。

（本文件由 s5r4_state.py 在 formal 链中生成，utc=2026-10-18T11:12:20Z）
