# P05 当前状态（每轮结束更新，一页以内）

> 规则见仓库根 `AGENTS.md`。本文件是摘要，细节以各轮报告为准。

## 1. 当前位置

| 项 | 值 |
|---|---|
| 分支 | `codex/p05-d003-fft-error-propagation` |
| 本轮开工基线 HEAD（r9m3e） | `37fbc0f2b9c48010b81ad220293fe6f3af5c02bd`（M3d 收尾提交） |
| `HEAD:S4`（冻结被测树 F4） | `589e15eb11fcb04e031b524f25a443e7921946cf`（F4 提交 `05097a7`） |
| 判定器 sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` |
| 阶段状态 | S1、S2、S3、S4 已由用户确认（带范围声明，见签收文件）；S5 未开始 |
| 签收文件 | `P05_S3_S4_SIGNOFF.md`（§1 签收表、§2 范围声明逐字照录） |
| 当前轮次 | **P05-S4 R9 M3e（r9m3e）**：用户签收 P05-S3/P05-S4 落账（U359–U363，签收日期 2026-10-18）、勘误 E9-74–E9-77、签收文件、STATE 收尾 |

## 2. 关键数字（每轮一行）

| 轮 | 关键数字 | 报告 |
|---|---|---|
| R1–R5 | R2 45 行；R3 141 点；R4 seam 25/25；R5 等价 24/24 | `P05_S4R2_REPORT.md` … `P05_S4R5_REPORT.md` |
| R6–R6d | twice 48 MATCH；R6d 202 一致 | `P05_S4R6_REPORT.md` … `R6d` |
| S3R3–S3R4 | F2 36/36；F3 8d8202a 117/117 | `P05_S3R3_CLOSEOUT.md` / `P05_S3R4_CLOSEOUT.md` |
| S4R7 | M1/M2 MISMATCH 0；M3 G5 177、G6 25 HOLD | `P05_S4R7_REPORT_FINAL.md` |
| S4R8 M0–M1c | 830 行全覆盖；M1 总表 1302 行闭环 | `P05_S4R8_REPORT_M0.md` … `M1C3` |
| S4R8 M2a–e | 正式两遍 202 点全 MATCH | `P05_S4R8_M2A_REPORT.md` … `M2E` |
| S3R5 | 冻结 F4 `05097a7`（树 `589e15e…`）；无注入 9/9 PASS | `P05_S3R5_CLOSEOUT.md` |
| S4R9 M0+M2 | 16 驱动+7 库；无注入 146/146；正式两遍 191/191 MATCH | `P05_S4R9_M2_REPORT.md` |
| S4R9 M2b | E9-1..6（U299）；HIT 等价 173/173 | `P05_S4R9_M2b_REPORT.md` |
| S4R9 M2c | E9-7..13（U302–U305）；RP 关闭（U304） | `P05_S4R9_M2c_REPORT.md` |
| S4R9 M1/M1R2 | 参考结果（U312/U318），不作为 M1 有效结果 | `P05_S4R9_M1_REPORT.md` / `M1R2` |
| S4R9 M1R3 | 物理事实有效；651 点两遍全 MATCH；F3/F4 0 DIFFS；总表 1302 行 | `P05_S4R9_M1R3_REPORT.md` |
| S4R9 M1R4 | r9m1r4 复核结果经 U328 采纳；流程缺陷见 E9-35.. | `P05_S4R9_M1R4_REPORT.md` |
| S4R9 M3a | J-1..J-6 属实（E9-35..E9-44、E9-45，U328–U333）；make test 四遍 rc=0、175 单元、**NO_NEW_FAILURE**；E2E 装置+预注册 18 点 | `P05_S4R9_M3a_REPORT.md` |
| S4R9 M3b | U334–U342、E9-46–E9-57；make test NO_NEW_FAILURE；E2E 正式两遍 CONTROL_OK=17, E2E_OK=25；新红点 0 | `P05_S4R9_M3b_REPORT.md` |
| S4R9 M3c | U343–U350、E9-58–E9-66；M3b 独立复核 DIFFS=0；READINESS MET=14 GAP=0 TRANSFERRED_S5=5；S5 移交 10 项 | `P05_S4R9_M3c_REPORT.md` |
| S4R9 M3d | U351–U358、E9-67–E9-73；§3 P 项复核 6/6 属实；红点唯一 id 26、TRANSFERRED_S5=6；去重 S5 移交 7 项 | `P05_S4R9_M3d_REPORT.md` |
| S4R9 M3e | U359–U363（签收落账）；E9-74–E9-77；签收文件 §2 逐字；S5 移交 7 项按 S5_HANDOFF_R9M3D | `P05_S4R9_M3e_REPORT.md` |

## 3. 开放问题（状态 · 去向 · 详情链接）

| 项 | 状态 | 去向 | 详情链接 |
|---|---|---|---|
| B 侧 jones/vl SILENT、nv CRASH | OPEN（基线，不是修复证据） | S5 | `S5_HANDOFF_R9M3D.tsv`（S5-M3D-01） |
| NB=1–8、类别 C | M2-07 81 点全 MATCH；M2-08 转 S5 | S5 | `S5_HANDOFF_R9M3D.tsv`（S5-M3D-02） |
| ES3R4-5/528/1164 | OUT_OF_SCOPE_D003 | S5 | `S5_HANDOFF_R9M3D.tsv`（S5-M3D-03；E9-76） |
| 非 FMM S4_malloc（约 35–43 处） | OUT_OF_SCOPE_D003 | S5 | `S5_HANDOFF_R9M3D.tsv`（S5-M3D-04） |
| U2 stage e（I1 特殊规则） | NOT_FOUND_IN_SCOPE | S5 | `S5_HANDOFF_R9M3D.tsv`（S5-M3D-05；E9-76） |
| RP-R6d-3 no-TWICE 路径 | OUT_OF_SCOPE_D003 | S5 | `S5_HANDOFF_R9M3D.tsv`（S5-M3D-06；来源按 E9-76 记 U5） |
| RP-R6d-7 D016（B 侧 rc 来源未追踪） | B 侧基线观察；F 侧归 D016/D003 | S5 | `S5_HANDOFF_R9M3D.tsv`（S5-M3D-07） |

已关闭项（S3-4b、806/415/RP-S3R4-1、RNV1、双目标/sanitizer、K-1、RP-R8-M2c-1、其他层失败变体、七处 info=NULL seam、Python/Lua 可见性、ClosedForm/LinearSolve 可达性、U38 分类、ADD22、r8m2c/d SOLN 18/28 点等）压缩为一行：均已按对应 U 编号关闭，见 `P05_S3_S4_SIGNOFF.md` §1/§3 与各轮报告。

## 4. 证据位置

- **S4 R9 M3e（r9m3e）**：证据 `checkpoints/p05/evidence/p05-s4r9/m3e/`（`SHA256SUMS.txt`）；小表 `checkpoints/p05/registries/s4r9/M3e/`（`SHA256SUMS.txt`）；报告 `P05_S4R9_M3e_REPORT.md`；签收 `P05_S3_S4_SIGNOFF.md`。
- **S4 R9 M3d（r9m3d）**：证据 `checkpoints/p05/evidence/p05-s4r9/m3d/`；小表 `checkpoints/p05/registries/s4r9/M3d/`；报告 `P05_S4R9_M3d_REPORT.md`。
- **S4 R9 M3c/M3b/M3a**：证据 `checkpoints/p05/evidence/p05-s4r9/{m3c,m3b,m3a}/`；小表 `checkpoints/p05/registries/s4r9/{M3c,M3b,M3a}/`。
- **S4 R9 M1R4/M1R3/M1R2/M1**：证据 `checkpoints/p05/evidence/p05-s4r9/{m1r4,m1r3,m1r2,m1}/`；小表 `checkpoints/p05/registries/s4r9/{M1R4,M1R3,M1R2,M1}/`。
- 更早轮次与完整台账：各轮报告；`RED_POINTS_LEDGER_R6c.tsv`；裁决总表 `registries/RULINGS.tsv`；勘误 `registries/s4r9/ERRATA_9.txt`；S5 移交 `registries/s4r9/M3d/S5_HANDOFF_R9M3D.tsv`。
