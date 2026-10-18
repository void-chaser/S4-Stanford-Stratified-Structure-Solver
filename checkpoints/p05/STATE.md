# P05 当前状态（每轮结束更新，一页以内）

> 规则见仓库根 AGENTS.md。本文件是摘要，细节以各轮报告为准。

## 1. 当前位置

| 项 | 值 |
|---|---|
| 分支 | codex/p05-d003-fft-error-propagation |
| 本轮开工基线 HEAD（s5r2） | 9f537f7c312b2ab7c64d5c0ea82da34e637da5d4（P05-S5 R1 (ii)） |
| HEAD:S4（冻结被测树 F4） | 589e15eb11fcb04e031b524f25a443e7921946cf（F4 提交 05097a7） |
| 判定器 sha256 | d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb |
| 阶段状态 | S1–S4 已由用户签收（带范围声明）；S5 进行中（R2：裁决入账、勘误、D017、登记落实、D016 公共 API 实测） |
| 当前轮次 | P05-S5 R2（s5r2）；不宣布 S5 或 P05 阶段完成 |

## 2. 关键数字（每轮一行）

| 轮 | 关键数字 | 报告/证据 |
|---|---|---|
| S4R9 M3c–M3e | 独立复核 DIFFS=0；签收落账 U359–U363 | M3c/M3d/M3e 报告 |
| S5R1 | 输入 25 行（去重前 29）；分类 REGISTRY_ONLY=5 NEEDS_TEST=3 NEEDS_FIX_NEW_DEFECT=1 RECORD_ONLY_OPEN=6 NEEDS_USER_RULING=10；勘误 E9-78/79 | P05_S5R1_REPORT.md |
| S5R2 | 裁决 U364–U371 入账；勘误 ES5-1..5；D017 只读清单 59 处（CALL 52；OUT 38，OUT CALL 31）；开放项 25 行落位；登记表补丁 v2 应用；D016 公共 API 实测（Python/Lua，F4，正式两遍） | P05_S5R2_REPORT.md |

## 3. 开放问题（状态 · 去向 · 详情链接）

| 项 | 状态 | 去向 | 详情链接 |
|---|---|---|---|
| S5 输入 25 行的最终处置 | 落位 | 本表为唯一入口 | P05_S5_OPEN_ITEMS.tsv |
| D017 非 FMM S4_malloc | OPEN（不在 P05 修） | 保持 OPEN，不阻塞 P06 | registries/s5r2/D017_S4MALLOC_INVENTORY_S5R2.tsv；ISSUE_REGISTRY D017 行 |
| R-P05-02 / R-P05-03 | OPEN（不在 P05 修） | 保持 OPEN，不阻塞 P06 | ISSUE_REGISTRY；ERRATA_S5.txt ES5-2 |
| F10/F8/反事实通量/allzero/11.2 五哈希 | OPEN / 未验证 | 经 U366–U368 转出 P05 | P05_S5_OPEN_ITEMS.tsv；ERRATA_S5.txt ES5-1 |
| S5R3 收口待办 | 待执行 | 下一轮 | 报告第 9 节 |

## 4. S5R3 收口待办

- 在 F4 上重跑一次 make test 与全量 E2E（M3b 42 点加 D016 点），作为 S5 收口的修复后验证（U364）。
- 就绪审计：F4 树、判定器、证据清单、STATE/registries/报告一致；AC-3/AC-4 的最终映射。
- 不宣布阶段完成；签收只由用户在对话中给出。

## 5. 证据位置

- **P05-S5 R2（s5r2）**：证据 checkpoints/p05/evidence/p05-s5r2/（SHA256SUMS.txt）；小表 checkpoints/p05/registries/s5r2/（SHA256SUMS.txt）；报告 P05_S5R2_REPORT.md；门禁附录 P05_S5R2_GATE_APPENDIX.md；开放项总表 P05_S5_OPEN_ITEMS.tsv；补丁 v2 P05_S5_REGISTRY_PATCH_V2.md。
- **P05-S5 R1（s5r1）**：证据 checkpoints/p05/evidence/p05-s5r1/；小表 checkpoints/p05/registries/s5r1/；报告 P05_S5R1_REPORT.md；草案 P05_S5_REGISTRY_PATCH_DRAFT.md、P05_S5_PLAN_DRAFT.md。
- 裁决总表 registries/RULINGS.tsv（追加 U364–U371）；S5 勘误 registries/s5r2/ERRATA_S5.txt；S4 勘误 registries/s4r9/ERRATA_9.txt。

