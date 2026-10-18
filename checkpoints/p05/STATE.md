# P05 当前状态（每轮结束更新，一页以内）

> 规则见仓库根 AGENTS.md。本文件是摘要，细节以各轮报告为准。

## 1. 当前位置

| 项 | 值 |
|---|---|
| 分支 | codex/p05-d003-fft-error-propagation |
| 本轮开工基线 HEAD（s5r3） | 29dfd1c04e18d351e72d50f57deb0299f8f74d08（P05-S5 R2 (ii)） |
| HEAD:S4（冻结被测树 F4） | 589e15eb11fcb04e031b524f25a443e7921946cf（F4 提交 05097a7） |
| 判定器 sha256 | d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb |
| 阶段状态 | S1–S4 已由用户签收（带范围声明）；S5 进行中（R3：S5 收口轮，未签收） |
| 当前轮次 | P05-S5 R3（s5r3）；不宣布 S5 或 P05 阶段完成 |

## 2. 关键数字（每轮一行）

| 轮 | 关键数字 | 报告/证据 |
|---|---|---|
| S4R9 M3c–M3e | 独立复核 DIFFS=0；签收落账 U359–U363 | M3c/M3d/M3e 报告 |
| S5R1 | 输入 25 行；分类；勘误 E9-78/79 | P05_S5R1_REPORT.md |
| S5R2 | 裁决 U364–U371；勘误 ES5-1..5；D017 清单；D016 公共 API 实测（MATCH=31 MISMATCH=2，比较器缺陷） | P05_S5R2_REPORT.md |
| S5R3（进行中，冻结已记录） | 裁决 U372–U377；勘误 ES5-6..8；D016/E2E/make test 预注册已冻结；正式运行在冻结期执行 | P05_S5R3_REPORT.md（收尾时生成） |

## 3. 开放问题（状态 · 去向 · 详情链接）

| 项 | 状态 | 去向 | 详情链接 |
|---|---|---|---|
| S5 输入 25 行的最终处置 | 落位（已转出/已登记/已关闭） | 本表为唯一入口 | checkpoints/p05/P05_S5_OPEN_ITEMS.tsv |
| D017 非 FMM S4_malloc | OPEN（不在 P05 修） | 转出 P05，不阻塞 P06（U369） | registries/s5r2/D017_S4MALLOC_INVENTORY_S5R2.tsv |
| R-P05-01 / R-P05-02 / R-P05-03 | OPEN（不在 P05 修） | 转出 P05，不阻塞 P06（U366/U370） | ISSUE_REGISTRY；ERRATA_S5.txt ES5-6..8 |
| F10/F8/反事实通量/allzero/11.2 五哈希 | OPEN / 未验证 | 经 U366–U368 转出 P05 | P05_S5_OPEN_ITEMS.tsv；ERRATA_S5.txt |
| S5 签收 | 等待用户审核 | S5R3 收口范围在冻结期执行；签收只由用户给出 | P05_S5_SIGNOFF_DRAFT.md（未签收） |

## 4. 证据位置

- **P05-S5 R3（s5r3）**：证据 checkpoints/p05/evidence/p05-s5r3/；小表 checkpoints/p05/registries/s5r3/；报告 P05_S5R3_REPORT.md（收尾时）；门禁附录 P05_S5R3_GATE_APPENDIX.md（门禁后）；签收草稿 P05_S5_SIGNOFF_DRAFT.md（收尾时）。
- **P05-S5 R2（s5r2）**：证据 checkpoints/p05/evidence/p05-s5r2/；小表 checkpoints/p05/registries/s5r2/；报告 P05_S5R2_REPORT.md。
- 裁决总表 registries/RULINGS.tsv（追加 U372–U377）；S5 勘误 registries/s5r2/ERRATA_S5.txt（追加 ES5-6..8）。

