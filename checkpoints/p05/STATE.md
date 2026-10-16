# P05 当前状态（每轮结束更新，一页以内）

> 规则见仓库根 `AGENTS.md`。本文件是摘要，细节以各轮报告为准。签收只由用户在对话中给出。

## 1. 当前位置

| 项 | 值 |
|---|---|
| 分支 | `codex/p05-d003-fft-error-propagation` |
| 开工基线 HEAD（P05-S4 R8 M0 开工） | `3ab56801e697910bdff9fbe6056807c2e41841b5`（S3R4 续5 收尾；R8 M0 记录提交 `2875c55`） |
| 本轮开工基线 HEAD（r8m2b） | `e57a2f38705e0c385eeab175a3c6a7442cab84fc`（r8m2a4 记录提交） |
| 收尾提交查询 | 修改本文件的最后一次提交（`git log -1 --format=%H -- checkpoints/p05/STATE.md`） |
| `HEAD:S4`（当前冻结被测树 F3） | `6cff923a02baf19e01966b2339755cbf3a5deeef`（F3 提交 `8d8202a`；前一冻结树 F2 `e124925f…` = `a07b5ac`；F `4a6f649…` = `1c11905`） |
| 判定器 sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` |
| 阶段签收 | S1、S2 已签收（带范围声明，`P05_S1_S2_SIGNOFF.md`）；S3、S4、S5 未签收 |
| 当前轮次 | **P05-S4 R8 M2b（r8m2b）完成，待规划者审核**：执行链修正（成对运行 U256、gdb 退出码交叉核对、展开 $EV）；审计 8 项发现（A1–A8）；有效预注册 v3（150行，exp改动0）与参照表（19行）及 win:64 表（5行）冻结；阳性对照 27/27 PASS；真实冒烟 24 点 5 项门禁全通；win:64 诊断确认 5 点全为 inj_call=1、k_fail=1；正式两遍运行完成（主表 150 点：129 MATCH / 21 MISMATCH / 0 FLAKY / 0 GDB_DIVERGENT / 0 UNJUDGED；参照表 19 点：14 MATCH / 5 MISMATCH；win:64 表 5 点：5 MATCH / 0 MISMATCH；合计 174 点：148 MATCH / 26 MISMATCH）；完整性 174 点全部 JUDGED。不宣布阶段完成。 |

## 2. 关键数字（每轮一行）

| 轮 | 关键数字 | 报告 |
|---|---|---|
| R1–R5 | R1 预注册；R2 45 行；R3 141 点；R4 seam 25/25；R5 等价 24/24、M=2 36 点、V3 132 点 | `P05_S4R2_REPORT.md` … `P05_S4R5_REPORT.md` |
| R6–R6d | R6 twice 48 MATCH；R6b/c 177 预注册与 HOLD；R6c2 U18 自检；R6d 202 一致，RNV1 确认 | `P05_S4R6_REPORT.md` … `P05_S4R6d_REPORT.md` |
| S3R3–S3R4 | S3R3 冻结 F2（36/36）；S3R4 806/415 冻结 F3 8d8202a（117/117、多边形 99/99） | `P05_S3R3_CLOSEOUT.md` / `P05_S3R4_CLOSEOUT.md` |
| S4R7 | M1/M2（run7：CTRL_SEAM 4/4、G2c 60、G1 254+44、G2a 50，MISMATCH 0）；M3（G5 177、G6 25 HOLD） | `P05_S4R7_REPORT_FINAL.md` |
| S4R8 M0–M1a | M0 冒烟 8/8；M1a 静态/动态 99 对 IDENTICAL；续3b1 通过；M1b/M1c 冻结（91 PASS） | `P05_S4R8_REPORT_M0.md` … `P05_S4R8_REPORT_M1a_CONT3b1_FIX.md` |
| S4R8 M1b（r8m1b1–b3） | 830 行全覆盖，补预注册与补跑闭合（U212）；FLAKY 0、MISMATCH 0 | `P05_S4R8_M1B1_REPORT.md`…`M1B3` |
| S4R8 M1c（r8m1c1–c3） | F2 基线 DIFFS=0；F3 rc 全 0，F3 vs 冻结 DIFFS=0；阳性对照 PASS | `P05_S4R8_M1C1…M1C3_REPORT.md` |
| S4R8 M1 总表（r8m1c4） | 1302 行 = MATCH 1252 + NOT_REACHED 44 + NOT_RUN 6（U224）；MISMATCH 0、FLAKY 0；SILENT 6、CRASH 14 | `registries/s4r8/M1c/r8m1c4/M1_SUMMARY_R8_M1c4.tsv` |
| S4R8 M2a（部分+r8m2a2） | 预注册 150 行 sha `1b60f95c…`；构建 OK 18；设计 12 项；阶段 e/类别 C 搜索完成 | `P05_S4R8_M2A_REPORT.md` / `P05_S4R8_M2A2_REPORT.md` |
| S4R8 M2a3（r8m2a3） | 静态审计缺口 174 项；有效预注册 150 行 sha `27e33b27…`；对照映射 28 对；自检 11/11 PASS | `P05_S4R8_M2A3_REPORT.md` |
| S4R8 M2a4（r8m2a4） | 审计缺陷 12 项；有效预注册 v2 150 行 sha `ee46fecf…`；R6c 回放 2124/0；阳性对照 19/19 PASS；完整性 131 PASS + 19 UNJUDGED | `P05_S4R8_M2A4_REPORT.md` |
| S4R8 M2b（r8m2b） | 正式两遍 174 点（主 150 + 参 19 + win64 5）；主 129 MATCH / 21 MISMATCH；win64 5/5 MATCH；参 14/5；FLAKY 0、GDB_DIV 0；完整性 174 JUDGED | `P05_S4R8_M2B_REPORT.md` |

## 3. 开放问题（状态 · 去向 · 详情链接；完整台账见 RED_POINTS_LEDGER_R6c）

| 项 | 状态 | 去向 | 详情链接 |
|---|---|---|---|
| S3-4b（模式/缓存安装） | **由用户带范围声明关闭（U29）** | 转 R8（F3 上） | `P05_S3_4b_CLOSURE.md` |
| D 冒烟 8 点 | 已运行（两遍 MATCH 8/8、FLAKY 0） | 完成（M0） | `D_SUMMARY_R8.txt` |
| F3-dbg 库差异 / BP_LINE | **已关闭（E8-19 / U177）** | — | `P05_S4R8_REPORT_M1a.md` |
| 806、415、RP-S3R4-1 | M1 已覆盖（U225）；M2-01 实测完成（16 MATCH / 6 MISMATCH，FLAKY 0），5 点 win:64 诊断确认全部 MATCH | 完成（M2-01） | `PREREG_M2_WIN64_R8_M2b.tsv` |
| R7 M2b CTRL_SEAM 驱动不符 | 记录更正（U118）；M2-09 预注册 2 对照点（F3、F2），CONTROL_OK | M2-09（U239） | `PREREG_M2_EFFECTIVE_R8_M2a4.tsv` |
| RNV1（RP-R6d-1） | F 上 CRASH；S3R3 方案 R3（a9679bc）；F2 自检通过；修后 F3 | R8（F3 上，U92） | `P05_S3R3_CLOSEOUT.md` |
| 双目标（M2-04）、sanitizer（M2-03） | M2-04 MATCH 2/2；M2-03 31 点（20 MATCH / 11 MISMATCH，19 参照点补跑 14 MATCH / 5 MISMATCH） | 完成（M2-04/M2-03） | `PREREG_M2_SANREF_R8_M2b.tsv` |
| "其他层失败"变体（M2-05） | layers-F3-dbg 8 点实测完成（MATCH 8/8、FLAKY 0） | 完成（M2-05） | `VERDICT_R8_M2b.tsv` |
| 注释措辞 `S4_internal.h:263` | 已改为 U31 措辞（提交 `a07b5ac`） | R8 回归确认 | `P05_S3R3_CLOSEOUT.md` |
| 张量路径 K-1（RP-R6d-8） | F_SUSPECT_SOURCE（[源码]）；nan-F3 与 bufseam 库实测完成（M2-06-01 MISMATCH） | M2-06（红点） | `VERDICT_R8_M2b.tsv` |
| B 侧 jones/vl SILENT、nv CRASH | OPEN（基线，不是修复证据） | S5 | `P05_S1R_O1_ATTRIBUTION.md` |
| NB=1–8（RP-R6d-16）、类别 C | M2-07 81 点实测完成（78 MATCH / 3 MISMATCH）；M2-08 裁决转 S5（U249） | M2-07 / S5（U249） | `VERDICT_R8_M2b.tsv` |
| Python/Lua 可见性（RP-R6d-15） | 按 U235 在 M3 做 | M3（U235） | `PROJECT_ROADMAP.md` |
| ES3R4-5(a)(b), −1…−9, 528/1164 | OUT_OF_SCOPE_D003（U90, U95, U99, U100） | S5 | `P05_S3R4_CLOSEOUT.md` |
| D016 B 侧 rc 20；vl NG=1 rc 20 | M2-10 事实核实断点与 rc 20，BASE_ONLY 判 MATCH（非修复证据，U247/U254） | M2-10（非修复证据） | `VERDICT_R8_M2b.tsv` |
| 非 FMM `S4_malloc`（约 35–43 处） | OUT_OF_SCOPE_D003 | S5 | `PROJECT_ROADMAP.md` |
| 续3a 修正 / M1b 数据 / M1c 结果 | **已闭合（U192 / U229）** | — | `P05_S4R8_REPORT_M1a_CONT3a_AUDIT3.md` |
| ADD22 中 -3→1 返回码跨树变化 | [源码]/未验证（E8-77）；M2-01 实测确认 rc1=1 且状态保持 | 已核实（E8-77） | `VERDICT_R8_M2b.tsv` |
| U2、U4、U5 原文 | 用户在 R6d 补录；U2 部分落实（U28） | U2 覆盖见表 | `evidence/p05-s4r6d/U2_COVERAGE_R6d.tsv` |
| U2 中 stage e（I1 特殊规则） | M2-02 NOT_FOUND_IN_SCOPE 裁决在 S4 不出点，转 S5（U248） | 转 S5（U248） | `STAGE_E_SEARCH_R8_M2a2_R2.tsv` |
| r8m2a2 历史 14 项偏离 | 裁决按执行偏离接受，不追认为合规（U250） | 已闭合（U250） | `RULINGS.tsv` |
| r8m2a3 COMPLETENESS 判定缺陷 | r8m2a3 150 PASS 不成立（U252），由 r8m2b COMPLETENESS v3 取代 | 已修正（r8m2b） | `COMPLETENESS_R8_M2b.tsv` |

## 4. 证据位置

只列最近三轮证据与清单位置，其余指向各轮报告：
- **S4 R8 M2b（r8m2b）**：证据 `checkpoints/p05/evidence/p05-s4r8/m2b/`（`SHA256SUMS.txt`）；小表与清单 `checkpoints/p05/registries/s4r8/M2/r8m2b/`（`SHA256SUMS.txt`）；报告 `P05_S4R8_M2B_REPORT.md`。
- **S4 R8 M2a4（r8m2a4）**：证据 `checkpoints/p05/evidence/p05-s4r8/m2a4/`（`SHA256SUMS.txt`）；小表与清单 `checkpoints/p05/registries/s4r8/M2/r8m2a4/`（`SHA256SUMS.txt`）；报告 `P05_S4R8_M2A4_REPORT.md`。
- **S4 R8 M2a3（r8m2a3）**：证据 `checkpoints/p05/evidence/p05-s4r8/m2a3/`（`SHA256SUMS.txt`）；小表与清单 `checkpoints/p05/registries/s4r8/M2/r8m2a3/`（`SHA256SUMS.txt`）；报告 `P05_S4R8_M2A3_REPORT.md`。
- 更早轮次证据与清单位置：详见各轮报告（`checkpoints/p05/P05_S4R*_REPORT*.md`）。完整台账：`RED_POINTS_LEDGER_R6c.tsv`；裁决总表：`registries/RULINGS.tsv`。
