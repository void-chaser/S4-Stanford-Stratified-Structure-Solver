# P05 当前状态（每轮结束更新，一页以内）

> 规则见仓库根 `AGENTS.md`。本文件是摘要，细节以各轮报告为准。签收只由用户在对话中给出。

## 1. 当前位置

| 项 | 值 |
|---|---|
| 分支 | `codex/p05-d003-fft-error-propagation` |
| 开工基线 HEAD（P05-S4 R8 M0 开工） | `3ab56801e697910bdff9fbe6056807c2e41841b5`（S3R4 续5 收尾；R8 M0 记录提交 `2875c55`） |
| 本轮开工基线 HEAD（r8m2a4） | `2395f669359795c126f4f4fc2223804c900b06f5`（r8m2a3 记录提交） |
| 收尾提交查询 | 修改本文件的最后一次提交（`git log -1 --format=%H -- checkpoints/p05/STATE.md`） |
| `HEAD:S4`（当前冻结被测树 F3） | `6cff923a02baf19e01966b2339755cbf3a5deeef`（F3 提交 `8d8202a`；前一冻结树 F2 `e124925f…` = `a07b5ac`；F `4a6f649…` = `1c11905`） |
| 判定器 sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` |
| 阶段签收 | S1、S2 已签收（带范围声明，`P05_S1_S2_SIGNOFF.md`）；S3、S4、S5 未签收 |
| 当前轮次 | **P05-S4 R8 M2a4 完成，待规划者审核**：补齐执行链（运行器 dry-run 300 行计划、事实提取、状态分析器、判定器 v2）；审计 12 项判定缺陷；有效预注册 v2（150 行）冻结（sha `ee46fecf…`）；历史 R6c 回放 2124 项 0 差异；合成阳性对照 19/19 PASS；完整性 131 PASS + 19 UNJUDGED = 150，BLOCKER 0；未运行任何 S4/gdb。不宣布阶段完成。 |

## 2. 关键数字（每轮一行）

| 轮 | 关键数字 | 报告 |
|---|---|---|
| R1–R5 | R1 预注册；R2 45 行；R3 141 点；R4 seam 25/25；R5 等价 24/24、M=2 36 点、V3 132 点 | `P05_S4R2_REPORT.md` … `P05_S4R5_REPORT.md` |
| R6–R6d | R6 twice 48 MATCH；R6b/c 177 预注册与 HOLD；R6c2 U18 自检；R6d 202 一致，RNV1 确认 | `P05_S4R6_REPORT.md` … `P05_S4R6d_REPORT.md` |
| S3R3–S3R4 | S3R3 a9679bc 冻结 F2（36/36）；S3R4 806/415 冻结 F3 8d8202a（117/117、多边形 99/99） | `P05_S3R3_CLOSEOUT.md` / `P05_S3R4_CLOSEOUT.md` |
| S4R7 | M1/M2（run7：CTRL_SEAM 4/4、G2c 60、G1 254+44、G2a 50，MISMATCH 0）；M3（G5 177、G6 25 HOLD） | `P05_S4R7_REPORT_FINAL.md` |
| S4R8 M0–M1a | M0 F3 冒烟 8/8；M1a 静态/动态 99 对 IDENTICAL；续3b1 U193/U196 通过；M1b/M1c 冻结（91 PASS） | `P05_S4R8_REPORT_M0.md` … `P05_S4R8_REPORT_M1a_CONT3b1_FIX.md` |
| S4R8 M1b（r8m1b1–b3） | 830 行全覆盖，补预注册与补跑闭合（U212）；FLAKY 0、MISMATCH 0 | `P05_S4R8_M1B1_REPORT.md`…`M1B3` |
| S4R8 M1c（r8m1c1–c3） | F2 基线 DIFFS=0；F3 rc 全 0，F3 vs 冻结 DIFFS=0；阳性对照 PASS | `P05_S4R8_M1C1…M1C3_REPORT.md` |
| S4R8 M1 总表（r8m1c4） | 1302 行 = MATCH 1252 + NOT_REACHED 44 + NOT_RUN 6（U224）；MISMATCH 0、FLAKY 0；SILENT 6、CRASH 14 | `registries/s4r8/M1c/r8m1c4/M1_SUMMARY_R8_M1c4.tsv` |
| S4R8 M2a（部分+r8m2a2） | 预注册 150 行（对照 90）sha `1b60f95c…`；构建 OK 18 / FAILED 0；设计 12 项；阶段 e/类别 C 搜索完成；完整性 PASS | `P05_S4R8_M2A_REPORT.md` / `P05_S4R8_M2A2_REPORT.md` |
| S4R8 M2a3（r8m2a3） | 静态审计缺口 174 项；有效预注册 150 行（对照 90）sha `27e33b27…`；对照映射 28 对；合成自检 11/11 PASS；完整性 PASS | `P05_S4R8_M2A3_REPORT.md` |
| S4R8 M2a4（r8m2a4） | 审计缺陷 12 项；有效预注册 v2 150 行 sha `ee46fecf…`；R6c 回放 2124 项 0 差异；阳性对照 19/19 PASS；dry-run 300 行；完整性 131 PASS + 19 UNJUDGED = 150 | `P05_S4R8_M2A4_REPORT.md` |

## 3. 开放问题（状态 · 去向 · 详情链接；完整台账见 RED_POINTS_LEDGER_R6c）

| 项 | 状态 | 去向 | 详情链接 |
|---|---|---|---|
| S3-4b（模式/缓存安装） | **由用户带范围声明关闭（U29）** | 转 R8（F3 上） | `P05_S3_4b_CLOSURE.md` |
| D 冒烟 8 点 | 已运行（两遍 MATCH 8/8、FLAKY 0） | 完成（M0） | `D_SUMMARY_R8.txt` |
| F3-dbg 库差异 / BP_LINE | **已关闭（E8-19 / U177）** | — | `P05_S4R8_REPORT_M1a.md` |
| 806、415、RP-S3R4-1 | M1 已覆盖（U225）；I1–I6 纳入 M2-01（U232）：预注册 21 行，5 行 win:64 转 M2b 诊断 | M2-01（U232）/ M2b 诊断（U251） | `PREREG_M2_EFFECTIVE_R8_M2a4.tsv`；`WIN64_DIAG_PLAN_R8_M2a4.md` |
| R7 M2b CTRL_SEAM 驱动不符 | 记录更正（U118）；M2-09 预注册 2 对照点（F3、F2），CONTROL_OK | M2-09（U239） | `PREREG_M2_EFFECTIVE_R8_M2a4.tsv` |
| RNV1（RP-R6d-1） | F 上 CRASH；S3R3 方案 R3（a9679bc）；F2 自检通过；修后 F3 | R8（F3 上，U92） | `P05_S3R3_CLOSEOUT.md` |
| 双目标（M2-04）、sanitizer（M2-03） | 新装置已建；预注册 v2 补齐双失败 8 列、san_ref（12 参照 + 19 NO_REF）及 san_options | M2-04 / M2-03（转 M2b） | `PREREG_M2_EFFECTIVE_R8_M2a4.tsv`；`INVARIANT_SPEC_R8_M2a4.md` |
| "其他层失败"变体（M2-05） | 新驱动已构建（layers-F3-dbg）；预注册 8 点（4 测试 + 4 对照） | M2-05（转 M2b 运行） | `PREREG_M2_EFFECTIVE_R8_M2a4.tsv` |
| 注释措辞 `S4_internal.h:263` | 已改为 U31 措辞（提交 `a07b5ac`） | R8 回归确认 | `P05_S3R3_CLOSEOUT.md` |
| 张量路径 K-1（RP-R6d-8） | F_SUSPECT_SOURCE（[源码]）；nan-F3 与 bufseam 库已建，预注册 2 点（RECORD_ONLY） | M2-06（转 M2b 运行） | `PREREG_M2_EFFECTIVE_R8_M2a4.tsv` |
| B 侧 jones/vl SILENT、nv CRASH | OPEN（基线，不是修复证据） | S5 | `P05_S1R_O1_ATTRIBUTION.md` |
| NB=1–8（RP-R6d-16）、类别 C | M2-07 预注册 81 点；M2-08 搜索表 NOT_FOUND 已裁决转 S5 登记（U249） | M2-07（转 M2b）/ M2-08（转 S5，U249） | `CATC_SEARCH_R8_M2a2_R2B.tsv` |
| Python/Lua 可见性（RP-R6d-15） | 按 U235 在 M3 做 | M3（U235） | `PROJECT_ROADMAP.md` |
| ES3R4-5(a)(b), −1…−9, 528/1164 | OUT_OF_SCOPE_D003（U99, U100, U95, U90；[源码] 说明） | S5 | `P05_S3R4_CLOSEOUT.md` |
| D016 B 侧 rc 20；vl NG=1 rc 20 | M2-10 补建同族 r6dnv1-B-dbg，预注册 1 点（BASELINE_ONLY_RULE，U247） | M2-10（转 M2b，非修复证据） | `m210_b_r8m2a2_R2.gdb` |
| 非 FMM `S4_malloc`（约 35–43 处） | OUT_OF_SCOPE_D003 | S5 | `PROJECT_ROADMAP.md` |
| 续3a 修正 / M1b 数据 / M1c 结果 | **已闭合（U192 / U229）**：第三部分已处置；M1b/M1c 结果已接受 | — | `P05_S4R8_REPORT_M1a_CONT3a_AUDIT3.md` |
| ADD22 中 -3→1 返回码跨树变化 | [源码]/未验证（E8-77） | R8 回归确认 | `E8-77` |
| U2、U4、U5 原文 | 用户在 R6d 对话中补录；U2 部分落实（U28） | U2 覆盖见表 | `evidence/p05-s4r6d/U2_COVERAGE_R6d.tsv` |
| U2 中 stage e（I1 特殊规则） | M2-02 搜索结论 NOT_FOUND_IN_SCOPE 已裁决在 S4 不出点，转 S5（U248） | 转 S5（U248） | `STAGE_E_SEARCH_R8_M2a2_R2.tsv` |
| r8m2a2 历史 14 项偏离 | 已由用户裁决按执行偏离接受，不追认为合规（U250） | 已闭合（U250） | `RULINGS.tsv` |
| r8m2a3 COMPLETENESS 判定缺陷 | r8m2a3 150 PASS 声明不成立（U252），由 r8m2a4 COMPLETENESS v2 取代 | 已修正（U252 / r8m2a4） | `COMPLETENESS_R8_M2a4.tsv` |

## 4. 证据位置

只列最近三轮证据与清单位置，其余指向各轮报告：
- **S4 R8 M2a4（r8m2a4）**：证据 `checkpoints/p05/evidence/p05-s4r8/m2a4/`（`SHA256SUMS.txt`）；小表与清单 `checkpoints/p05/registries/s4r8/M2/r8m2a4/`（`SHA256SUMS.txt`）；报告 `P05_S4R8_M2A4_REPORT.md`。
- **S4 R8 M2a3（r8m2a3）**：证据 `checkpoints/p05/evidence/p05-s4r8/m2a3/`（`SHA256SUMS.txt`）；小表与清单 `checkpoints/p05/registries/s4r8/M2/r8m2a3/`（`SHA256SUMS.txt`）；报告 `P05_S4R8_M2A3_REPORT.md`。
- **S4 R8 M2a2（r8m2a2）**：证据 `checkpoints/p05/evidence/p05-s4r8/m2a2/`（`SHA256SUMS.txt`）；小表与清单 `checkpoints/p05/registries/s4r8/M2/r8m2a2/`（`SHA256SUMS.txt`）；报告 `P05_S4R8_M2A2_REPORT.md`。
- 更早轮次证据与清单位置：详见各轮报告（`checkpoints/p05/P05_S4R*_REPORT*.md`）。完整台账：`RED_POINTS_LEDGER_R6c.tsv`；裁决总表：`registries/RULINGS.tsv`。
