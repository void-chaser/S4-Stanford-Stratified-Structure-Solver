# P05 当前状态（每轮结束更新，一页以内）

> 规则见仓库根 AGENTS.md。本文件是摘要，细节以各轮报告为准。

## 1. 当前位置

| 项 | 值 |
|---|---|
| 分支 | codex/p05-d003-fft-error-propagation |
| 本轮开工基线 HEAD（s5r1） | 59e742d5b918b9c194f3aec10148801f7839f263（P05-S4 R9 M3e (ii)） |
| HEAD:S4（冻结被测树 F4） | 589e15eb11fcb04e031b524f25a443e7921946cf（F4 提交 05097a7） |
| 判定器 sha256 | d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb |
| 阶段状态 | S1–S4 已由用户签收（带范围声明，见 P05_S1_S2_SIGNOFF.md、P05_S3_S4_SIGNOFF.md）；S5 进行中（R1 盘点） |
| 签收文件 | P05_S1_S2_SIGNOFF.md、P05_S3_S4_SIGNOFF.md（第 2 节范围声明逐字照录） |
| 当前轮次 | P05-S5 R1（s5r1）：S5 输入只读盘点、分类分流、登记表补丁草案、勘误 E9-78/E9-79、S5 计划草案；未运行 S4 任何程序 |

## 2. 关键数字（每轮一行）

| 轮 | 关键数字 | 报告/证据 |
|---|---|---|
| R1–R5 | R2 45 行；R3 141 点；R4 seam 25/25；R5 等价 24/24 | P05_S4R2…S4R5_REPORT.md |
| R6–R6d | twice 48 MATCH；R6d 202 一致 | P05_S4R6…R6d |
| S3R3–S3R5 | F2 36/36；F3 117/117；F4 05097a7 | S3R3/S3R4/S3R5 CLOSEOUT |
| S4R7–R8 | MISMATCH 0；正式两遍 202 点全 MATCH | P05_S4R7/S4R8 报告 |
| S4R9 M0–M2 | 无注入 146/146；正式两遍 191/191 MATCH | P05_S4R9_M2_REPORT.md |
| S4R9 M2b–M2c | HIT 等价 173/173；READINESS MET=14 GAP=0 | M2b/M2c 报告 |
| S4R9 M3a–M3b | make test 175 单元 NO_NEW_FAILURE；E2E_OK=25、CONTROL_OK=17 | M3a/M3b 报告 |
| S4R9 M3c–M3e | 独立复核 DIFFS=0；签收落账 U359–U363 | M3c/M3d/M3e 报告 |
| S5R1 | 输入 25 行（去重前 29）；分类 REGISTRY_ONLY=5 NEEDS_TEST=3 NEEDS_FIX_NEW_DEFECT=1 RECORD_ONLY_OPEN=6 NEEDS_USER_RULING=10；勘误 E9-78/79 | P05_S5R1_REPORT.md |

## 3. 开放问题（状态 · 去向 · 详情链接）

| 项 | 状态 | 去向 | 详情链接 |
|---|---|---|---|
| S5 输入分类（25 行；12 行需用户裁决） | OPEN | 用户裁决 + S5R2 | registries/s5r1/S5_TRIAGE_S5R1.tsv |
| 验收映射 AC-3/AC-4（M3a/M3b E2E 能否作 S5 证据） | NEEDS_USER_RULING | 用户裁决 | registries/s5r1/P05_ACCEPTANCE_MAP_S5R1.tsv |
| P05 收口所需 Q1–Q8 | OPEN | 用户裁决 | P05_S5_PLAN_DRAFT.md 第 5 节 |
| 历史已关闭项 | CLOSED | 各轮报告 | P05_S3_S4_SIGNOFF.md 第 1/3 节 |

## 4. 证据位置

- **P05-S5 R1（s5r1）**：证据 checkpoints/p05/evidence/p05-s5r1/（SHA256SUMS.txt）；小表 checkpoints/p05/registries/s5r1/（SHA256SUMS.txt）；报告 P05_S5R1_REPORT.md；草案 P05_S5_REGISTRY_PATCH_DRAFT.md、P05_S5_PLAN_DRAFT.md。
- **P05-S4 R9 M3e**：证据 checkpoints/p05/evidence/p05-s4r9/m3e/；小表 checkpoints/p05/registries/s4r9/M3e/；报告 P05_S4R9_M3e_REPORT.md；签收 P05_S3_S4_SIGNOFF.md。
- 更早轮次：各轮报告；裁决总表 registries/RULINGS.tsv；勘误 registries/s4r9/ERRATA_9.txt；S5 移交 registries/s4r9/M3d/S5_HANDOFF_R9M3D.tsv。

