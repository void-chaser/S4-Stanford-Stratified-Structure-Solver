# P05 当前状态（每轮结束更新，一页以内）

> 规则见仓库根 `AGENTS.md`。本文件是摘要，细节以各轮报告为准。

## 1. 当前位置

| 项 | 值 |
|---|---|
| 分支 | `codex/p05-d003-fft-error-propagation` |
| 本轮开工基线 HEAD（r9m3a） | `2f86aa11c7ee1bb16f663abf03ddbf04674a6912`（r9m1r4 收尾提交） |
| `HEAD:S4`（冻结被测树 F4） | `589e15eb11fcb04e031b524f25a443e7921946cf`（F4 提交 `05097a7`） |
| 判定器 sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` |
| 阶段状态 | S1、S2 已由用户确认（带范围声明）；S3、S4、S5 未确认 |
| 当前轮次 | **P05-S4 R9 M3a（r9m3a）**：M1R4 勘误收口（J-1..J-6 属实 → E9-35..E9-44，U328–U333）+ 导出树 make test 回归 + Python/Lua E2E 装置与预注册（不运行 E2E 点）。M3b 待用户审核预注册后执行。 |

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
| S4R9 M3a | J-1..J-6 属实（E9-35..E9-44、E9-45，U328–U333）；make test 四遍 rc=0、175 单元、**NO_NEW_FAILURE**；E2E 装置+预注册 18 点（不运行、冒烟 1 次） | `P05_S4R9_M3a_REPORT.md` |

## 3. 开放问题（状态 · 去向 · 详情链接）

| 项 | 状态 | 去向 | 详情链接 |
|---|---|---|---|
| S3-4b（模式/缓存安装） | 用户带范围声明关闭（U29） | 已回归 | `P05_S3_4b_CLOSURE.md` |
| 806、415、RP-S3R4-1 | M1/M2 已覆盖（U225） | 完成 | `TRIAGE_R8_M2c.tsv` |
| RNV1（RP-R6d-1） | F2/F3/F4 全部 MATCH | 完成 | `P05_S3R3_CLOSEOUT.md` |
| 双目标（M2-04）、sanitizer（M2-03） | MATCH / 31 点全 MATCH | 完成 | `M2_CONSOLIDATED_F4_R9.tsv` |
| 张量路径 K-1（RP-R6d-8） | 用户带范围声明关闭（U274/U281） | 关闭 | `M206_DIAG_SUMMARY.txt` |
| RP-R8-M2c-1/1b | 按 U304 关闭（18 点全 MATCH） | 关闭 | `P05_S4R9_M2c_REPORT.md` |
| B 侧 jones/vl SILENT、nv CRASH | OPEN（基线，不是修复证据） | S5 | `P05_S1R_O1_ATTRIBUTION.md` |
| NB=1–8、类别 C | M2-07 81 点全 MATCH；M2-08 转 S5（U249） | S5 | `VERDICT_R9.tsv` |
| Python/Lua 可见性（RP-R6d-15） | 装置与预注册完成（M3a）；执行待用户审核 | M3b | `PREREG_E2E_R9M3A.tsv` |
| ES3R4-5/528/1164 | OUT_OF_SCOPE_D003（U90/U95/U99/U100） | S5 | `P05_S3R4_CLOSEOUT.md` |
| U38 缺陷分类 | U38 已由 U90 裁决（806、415 已修；528、1164 转 S5），M3 只核对台账，不重新分类 | 已裁决（U90/U333c） | `registries/RULINGS.tsv` |
| 非 FMM `S4_malloc`（约 35–43 处） | OUT_OF_SCOPE_D003 | S5 | `PROJECT_ROADMAP.md` |
| ADD22 -3→1 返回码跨树变化 | 已核实（E8-77） | 已核实 | `VERDICT_R9.tsv` |
| U2 stage e（I1 特殊规则） | NOT_FOUND_IN_SCOPE，S4 不出点（U248） | S5 | `STAGE_E_SEARCH_R8_M2a2_R2.tsv` |
| r8m2c/d SOLN 18/28 点 | U276-U282 落实，R9 F4 18 点全 MATCH | 已闭合 | `M2_CONSOLIDATED_F4_R9.tsv` |
| ClosedForm / LinearSolve 族 E2E 可达性 | NOT_REACHABLE_VIA_API（M3a 调研结论） | M3b 复核 | `E2E_API_SURVEY_R9M3A.md` |

> 说明：本轮完成 R9 M3a（勘误收口 + make test 回归 NO_NEW_FAILURE/175 单元 + E2E 装置与预注册 18 点，未运行 E2E 点），不宣布阶段完成；预注册、不可达点族与 end 门禁 FAIL 项的处置等待用户审核后进入 M3b。

## 4. 证据位置

- **S4 R9 M3a（r9m3a）**：证据 `checkpoints/p05/evidence/p05-s4r9/m3a/`（`SHA256SUMS.txt`）；小表 `checkpoints/p05/registries/s4r9/M3a/`（`SHA256SUMS.txt`）；报告 `P05_S4R9_M3a_REPORT.md`。
- **S4 R9 M1R4/M1R3/M1R2/M1**：证据 `checkpoints/p05/evidence/p05-s4r9/{m1r4,m1r3,m1r2,m1}/`；小表 `checkpoints/p05/registries/s4r9/{M1R4,M1R3,M1R2,M1}/`；报告见 §2 表。
- 更早轮次与完整台账：各轮报告；`RED_POINTS_LEDGER_R6c.tsv`；裁决总表 `registries/RULINGS.tsv`；勘误 `registries/s4r9/ERRATA_9.txt`。