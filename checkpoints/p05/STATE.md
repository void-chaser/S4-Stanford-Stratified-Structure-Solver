# P05 当前状态（每轮结束更新，一页以内）

> 规则见仓库根 `AGENTS.md`。本文件是摘要，细节以各轮报告为准。签收只由用户在对话中给出。

## 1. 当前位置

| 项 | 值 |
|---|---|
| 分支 | `codex/p05-d003-fft-error-propagation` |
| 开工基线 HEAD（P05-S4 R8 M0 开工） | `3ab56801e697910bdff9fbe6056807c2e41841b5`（S3R4 续5 收尾；R8 M0 记录提交 `2875c55`） |
| 本轮开工基线 HEAD | `fc3e8ca1100184e2ae0f3604869265067b4d3035`（r8m1c3 收尾提交） |
| 收尾提交查询 | 修改本文件的最后一次提交（`git log -1 --format=%H -- checkpoints/p05/STATE.md`） |
| `HEAD:S4`（当前冻结被测树 F3） | `6cff923a02baf19e01966b2339755cbf3a5deeef`（F3 提交 `8d8202a`；前一冻结树 F2 `e124925f…` = `a07b5ac`；F `4a6f649…` = `1c11905`） |
| 判定器 sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` |
| 阶段签收 | S1、S2 已签收（带范围声明，`P05_S1_S2_SIGNOFF.md`）；S3、S4、S5 未签收 |
| 当前轮次 | **P05-S4 R8 M1c（r8m1c1–c4，本轮 r8m1c4 已完成范围）**：U223–U228、E8-83–87 登记；F3 独立重比 DIFFS=0；M1 总表修正为 1302 行；修复覆盖按 U225；阳性对照与名称对照完成；待用户审核。 |

## 2. 关键数字（每轮一行）

| 轮 | 关键数字 | 报告 |
|---|---|---|
| R1–R5 | R1 门禁预注册；R2 三列 45 行；R3 141 点；R4 seam 25/25；R5 等价 24/24、M=2 36 点、V4 0 发现、V3 132 点 | `P05_S4R2_REPORT.md` … `P05_S4R5_REPORT.md` |
| R6–R6d | R6 twice 48 MATCH；R6b 177 预注册；R6c 177 HOLD；R6c2 U18 18 行与自检；R6d 202 一致，RNV1 F_CONFIRMED | `P05_S4R6_REPORT.md` … `P05_S4R6d_REPORT.md` |
| S3R3–S3R4 | S3R3 a9679bc 冻结 F2，自检 36/36；S3R4 806/415 冻结 F3 8d8202a，自检 117/117、多边形 99/99 | `P05_S3R3_CLOSEOUT.md` / `P05_S3R4_CLOSEOUT.md` |
| S4R7 | M1、M2（run7：CTRL_SEAM 4/4、G2c 60、G1 254+44 NOT_REACHED、G2a 50，MISMATCH 0）；M3（G5 177、G6 25 HOLD） | `P05_S4R7_REPORT_FINAL.md` |
| S4R8 M0–M1a | M0 F3 构建与冒烟 8/8；M1a 续1-3a 静态/动态 99 对 IDENTICAL；续3b1 U193/U196 通过；续3b1补正 M1b/M1c 冻结（91 PASS） | `P05_S4R8_REPORT_M0.md` … `P05_S4R8_REPORT_M1a_CONT3b1_FIX.md` |
| S4R8 M1b（r8m1b1–b3） | 首轮 830 行全覆盖，经补充预注册与补跑后数据闭合（U212）；FLAKY 0、MISMATCH 0（有效表）；M1c 日志核对 440/440 AGREE | `P05_S4R8_M1B1_REPORT.md`、`…M1B2…`、`…M1B3…` |
| S4R8 M1c（r8m1c1–c3） | r8m1c1 停止（heredoc 写入）；r8m1c2 F2 基线 DIFFS=0、GDB_DIVERGENT=0；r8m1c3 F3 运行 rc 全 0，F3 vs 冻结 DIFFS=0、F2↔F3 DIFFS=0、GDB_DIVERGENT=0；阳性对照 PASS；判定运行后规则修正三次（见报告） | `P05_S4R8_M1C1_REPORT.md`、`P05_S4R8_M1C2_REPORT.md`、`P05_S4R8_M1C3_REPORT.md` |
| S4R8 M1 总表（r8m1c4） | 1302 行 = MATCH 1252 + NOT_REACHED_AS_EXPECTED 44 + NOT_RUN_AS_EXPECTED 6（U224）；MISMATCH 0、FLAKY 0；U212 单列 SILENT 6、CRASH 14 | `registries/s4r8/M1c/r8m1c4/M1_SUMMARY_R8_M1c4.tsv` |

## 3. 开放问题（状态 · 去向 · 详情链接；完整台账见 RED_POINTS_LEDGER_R6c）

| 项 | 状态 | 去向 | 详情链接 |
|---|---|---|---|
| S3-4b（失败后模式/缓存不安装） | **由用户带范围声明关闭（U29）**，不代表整阶段签收 | 转 R8（F3 上） | `P05_S3_4b_CLOSURE.md` |
| D 冒烟 8 点 | 已运行（两遍 MATCH 8/8、FLAKY 0） | 完成（M0）；回归见 R8 计划 | `D_SUMMARY_R8.txt` |
| F3-dbg 库 sha256 差异（E8-9） | **已关闭（E8-19）**：去调试段后等价 EQUAL_AFTER_STRIP | — | `P05_S4R8_REPORT_M1a.md` |
| U171 BP_LINE 注释行规则（E8-55） | **已关闭（U177/E8-56）**：排除注释行引用，BP_LINE 2/REG 26/NO 3 | — | `USED_IN_M1_CORRECTION_R8_M1a4.tsv` |
| 806、415、RP-S3R4-1 | M1 已覆盖（返回码与类别口径，U225；F3 行均 MATCH）；I1–I6 未测（局限） | 不转 M2（I1–I6 未测，待用户裁决） | `registries/s4r8/M1c/r8m1c4/FIX_COVERAGE_M1_R8_M1c4_R2.tsv` |
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
| D016 B 侧 rc 20 来源；B 侧 vl NG=1 rc 20 | OPEN（BASELINE_ONLY；两项对照事实基准确定 U198，但无注入首调返回 rc=20 机理未解释） | R7 观察 → S5 | `RESULTS_R7_M1_CTRL_REJUDGE_POSTHOC.tsv` |
| 非 FMM `S4_malloc`（约 35–43 处） | OUT_OF_SCOPE_D003 | S5 | `PROJECT_ROADMAP.md` |
| 续3a 审核修正第三部分处置 | **已处置（U188–U191，U192 接受）** | — | `P05_S4R8_REPORT_M1a_CONT3a_AUDIT3.md` |
| M1b 已数据闭合（U212） | 补充预注册 342 行、补跑 684 次；MISMATCH 0、FLAKY 0；50 行 SILENT 假象（U206）在正确环境为 REPORTED_FAILURE，不进红点台账 | 待用户审核（M1b3 报告） | `P05_S4R8_M1B3_REPORT.md` / `CROSSWALK_M1B1_SUPP_R8_M1b3.tsv` |
| M1c 结果（F3 vs 冻结） | F3 236 MATCH（U223，以独立重比为条件）；独立重比 DIFFS=0（CHECKS=6840） | 待用户审核（M1c4 报告） | `P05_S4R8_M1C4_REPORT.md` / `registries/s4r8/M1c/r8m1c4/RECHECK_F3_R8_M1c4.tsv` |
| ADD22 中 -3→1 返回码跨树变化 | [源码]/未验证（两树均为 REPORTED_FAILURE，机理解释标[源码/未验证]，E8-77） | R8 回归确认 | `F2_F3_DIFF_M1B_R8_M1b1.tsv` / `E8-77` |
| U2、U4、U5 原文 | 用户在 R6d 对话中补录；U2 部分落实（U28） | U2 覆盖见表 | `evidence/p05-s4r6d/U2_COVERAGE_R6d.tsv` |
| U2 中 stage e（I1 特殊规则） | 0 点，**未覆盖** | R8 | `P05_S4R6d_REPORT.md` |

## 4. 证据位置

只列最近三轮证据与清单位置，其余指向各轮报告：
- **S4 R8 M1c4（r8m1c4）**：证据 `checkpoints/p05/evidence/p05-s4r8/m1c4/`（`SHA256SUMS.txt`，收尾生成）；小表与清单 `checkpoints/p05/registries/s4r8/M1c/r8m1c4/`（`SHA256SUMS.txt`，end 门禁文件见 `SHA256SUMS_END.txt`）；报告 `P05_S4R8_M1C4_REPORT.md`。
- **S4 R8 M1c3（r8m1c3）**：证据 `checkpoints/p05/evidence/p05-s4r8/m1c3/`；小表与清单 `checkpoints/p05/registries/s4r8/M1c/r8m1c3/`（`SHA256SUMS.txt`）；报告 `P05_S4R8_M1C3_REPORT.md`。registries 名称与证据不一致，见 `REGISTRY_NAME_MAP_R8_M1c3.tsv`（在 `r8m1c4/`）。
- **S4 R8 M1c2（r8m1c2）**：证据 `checkpoints/p05/evidence/p05-s4r8/m1c2/`；小表与清单 `checkpoints/p05/registries/s4r8/M1c/r8m1c2/`（`SHA256SUMS.txt`）；报告 `P05_S4R8_M1C2_REPORT.md`。
- 更早轮次证据与清单位置：详见各轮报告（`checkpoints/p05/P05_S4R*_REPORT*.md`）。完整台账：`RED_POINTS_LEDGER_R6c.tsv`；裁决总表：`registries/RULINGS.tsv`。
