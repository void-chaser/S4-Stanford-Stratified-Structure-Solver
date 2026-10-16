# P05 当前状态（每轮结束更新，一页以内）

> 规则见仓库根 `AGENTS.md`。本文件是摘要，细节以各轮报告为准。签收只由用户在对话中给出。

## 1. 当前位置

| 项 | 值 |
|---|---|
| 分支 | `codex/p05-d003-fft-error-propagation` |
| 开工基线 HEAD（P05-S4 R8 M0 开工） | `3ab56801e697910bdff9fbe6056807c2e41841b5`（S3R4 续5 收尾；R8 M0 记录提交 `2875c55`） |
| 本轮开工基线 HEAD（s3r5） | `73c9b7b9c3a9e008c214c7cb333212c8ca3856a5`（r8m2e 收尾提交） |
| 收尾提交查询 | 修改本文件的最后一次提交（`git log -1 --format=%H -- checkpoints/p05/STATE.md`） |
| `HEAD:S4`（当前冻结被测树 F4） | `589e15eb11fcb04e031b524f25a443e7921946cf`（F4 提交 `05097a7`；前一树 F3 `6cff923…`；F2 `e124925…`；F `4a6f649…`） |
| 判定器 sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` |
| 阶段签收 | S1、S2 已签收（带范围声明，`P05_S1_S2_SIGNOFF.md`）；S3、S4、S5 未签收 |
| 当前轮次 | **P05-S3 R5（s3r5）完成，待用户审核**：InitSolution 分配失败清理修复（RP-R8-M2c-1/1b）完成并冻结 F4 树（提交 `05097a7`，树 `589e15e…`，U283–U285）；导出树构建 F4 dbg/san/plain 库与驱动（init-F4-dbg、init-F4-san、init-F4-san-AL），告警与 F3 完全一致无新增（U286/U289）；diff 严格限定于 S4.cpp:1760-1774；无注入对照 9 组全过（rc=0，0 san）；GDB 实测 K 映射 18 点全部与 F3 精确一致（K_MAP_F4_S3R5.tsv）；自检 D 9 点实测全部 rc1=1、rc2=0、signal=0、post_call1_sol=NULL、crash_call=NONE（只记事实不判 MATCH）；输出 R9 全部输入清单与 F4 回归计划（U290）；AGENTS 第 6 节更新（U287）；小表与证据清单就绪。不宣布阶段完成。 |

## 2. 关键数字（每轮一行）

| 轮 | 关键数字 | 报告 |
|---|---|---|
| R1–R5 | R1 预注册；R2 45 行；R3 141 点；R4 seam 25/25；R5 等价 24/24、M=2 36 点、V3 132 点 | `P05_S4R2_REPORT.md` … `P05_S4R5_REPORT.md` |
| R6–R6d | R6 twice 48 MATCH；R6b/c 177 预注册与 HOLD；R6c2 U18 自检；R6d 202 一致，RNV1 确认 | `P05_S4R6_REPORT.md` … `P05_S4R6d_REPORT.md` |
| S3R3–S3R4 | S3R3 冻结 F2（36/36）；S3R4 806/415 冻结 F3 8d8202a（117/117、多边形 99/99） | `P05_S3R3_CLOSEOUT.md` / `P05_S3R4_CLOSEOUT.md` |
| S4R7 | M1/M2（run7：CTRL_SEAM 4/4、G2c 60、G1 254+44、G2a 50，MISMATCH 0）；M3（G5 177、G6 25 HOLD） | `P05_S4R7_REPORT_FINAL.md` |
| S4R8 M0–M1a | M0 冒烟 8/8；M1a 静态/动态 99 对 IDENTICAL；续3b1 通过；M1b/M1c 冻结（91 PASS） | `P05_S4R8_REPORT_M0.md` … `P05_S4R8_REPORT_M1a_CONT3b1_FIX.md` |
| S4R8 M1b–c | 830 行全覆盖（U212）；F3 vs 冻结 DIFFS=0；阳性对照 PASS；M1 总表 1302 行全闭环 | `P05_S4R8_M1B3_REPORT.md` … `M1C3` |
| S4R8 M2a–a4 | 预注册 150 行 v2 sha `ee46fecf…`；R6c 回放 2124/0；阳性对照 19/19 PASS | `P05_S4R8_M2A_REPORT.md` … `M2A4` |
| S4R8 M2b（r8m2b） | 正式两遍 174 点（主 150 + 参 19 + win64 5）；主 129 MATCH / 21 MISMATCH；win64 5/5 MATCH；参 14/5；FLAKY 0 | `P05_S4R8_M2B_REPORT.md` |
| S4R8 M2c（r8m2c） | 增量 54 点（36 MATCH / 18 MISMATCH / 0 FLAKY / 0 GDB_DIV）；阳性对照 34/34 PASS；合并总表 228 点（有效 202 点：183 MATCH / 19 MISMATCH，26 点 SUPERSEDED）；完整性 228 JUDGED | `P05_S4R8_M2C_REPORT.md` |
| S4R8 M2d（r8m2d） | 增量 28 点冒烟 25 MATCH / 3 MISMATCH（停于未 arm 保护）；阳性对照 41/41 PASS；合并总表 256 点（有效 202：199 MATCH / 3 MISMATCH，54 SUPERSEDED）；1b 升 F_CONFIRMED；K-1 关闭；S3R5 设计完成 | `P05_S4R8_M2D_REPORT.md` |
| S4R8 M2e（r8m2e） | -FA 装置纠偏（init-F3-san-AL，K=3）；对照 PASS；冒烟 3/3 MATCH；正式两遍 28/28 MATCH（0 FLAKY / 0 GDB_DIV）；总表 259 点（有效 202 全 MATCH，57 SUPERSEDED，有效行 100% formal 来源）；维持 1b F_CONFIRMED 与 K-1 关闭；更正 F4 回归清单；补披露事件 | `P05_S4R8_M2E_REPORT.md` |
| S3R5（s3r5） | 冻结 F4 05097a7（树 589e15e…）；3 库告警无新增（0 diff）；无注入对照 9/9 PASS；K 映射 18/18 一致；自检 D 9/9 事实（rc1=1, rc2=0, sol=NULL, crash=NONE） | `P05_S3R5_CLOSEOUT.md` |

## 3. 开放问题（状态 · 去向 · 详情链接；完整台账见 RED_POINTS_LEDGER_R6c）

| 项 | 状态 | 去向 | 详情链接 |
|---|---|---|---|
| S3-4b（模式/缓存安装） | **由用户带范围声明关闭（U29）** | 转 R8（F3 上） | `P05_S3_4b_CLOSURE.md` |
| 806、415、RP-S3R4-1 | M1 已覆盖（U225）；M2-01 增量 6 点全 MATCH (6/6) | 完成（M2-01/F1） | `TRIAGE_R8_M2c.tsv` |
| R7 M2b CTRL_SEAM 驱动不符 | 记录更正（U118）；M2-09 预注册 2 对照点（F3、F2），CONTROL_OK | M2-09（U239） | `PREREG_M2_EFFECTIVE_R8_M2a4.tsv` |
| RNV1（RP-R6d-1） | F 上 CRASH；S3R3 方案 R3（a9679bc）；F2 自检通过；修后 F3 | R8（F3 上，U92） | `P05_S3R3_CLOSEOUT.md` |
| 双目标（M2-04）、sanitizer（M2-03） | M2-04 MATCH 2/2；M2-03 31 点全 MATCH | 完成（M2-04/M2-03） | `M2_CONSOLIDATED_R8_M2c.tsv` |
| "其他层失败"变体（M2-05） | layers-F3-dbg 8 点实测完成（P0 依据 R6c 更正 exp_I2=N/A 后全 MATCH） | 完成（M2-05） | `VERDICT_R8_M2c.tsv` |
| 注释措辞 `S4_internal.h:263` | 已改为 U31 措辞（提交 `a07b5ac`） | R8 回归确认 | `P05_S3R3_CLOSEOUT.md` |
| 张量路径 K-1（RP-R6d-8） | **已由用户裁决带范围声明关闭（U274，U281维持）**：F3 nan-F3 未复现静默吞没，info=10，return 20，M2-06-01-F3-C 实测 MATCH | 关闭（U274/U281） | `M206_DIAG_SUMMARY.txt` |
| RP-R8-M2c-1 / 1b（新红点） | **S3R5 已修改源码 [源码]，待 R9 修后验证** | 转 R9（F4 上） | `P05_S3R5_CLOSEOUT.md` |
| B 侧 jones/vl SILENT、nv CRASH | OPEN（基线，不是修复证据） | S5 | `P05_S1R_O1_ATTRIBUTION.md` |
| NB=1–8（RP-R6d-16）、类别 C | M2-07 81 点全 MATCH；M2-08 转 S5（U249） | M2-07 / S5 | `VERDICT_R8_M2c.tsv` |
| Python/Lua 可见性（RP-R6d-15） | 按 U235 在 M3 做 | M3（U235） | `PROJECT_ROADMAP.md` |
| ES3R4-5(a)(b), −1…−9, 528/1164 | OUT_OF_SCOPE_D003（U90, U95, U99, U100） | S5 | `P05_S3R4_CLOSEOUT.md` |
| D016 B 侧 rc 20；vl NG=1 rc 20 | M2-10 事实核实断点与 rc 20，BASE_ONLY 判 MATCH（非修复证据，U247/U254） | M2-10（非修复证据） | `VERDICT_R8_M2b.tsv` |
| 非 FMM `S4_malloc`（约 35–43 处） | OUT_OF_SCOPE_D003 | S5 | `PROJECT_ROADMAP.md` |
| ADD22 中 -3→1 返回码跨树变化 | [源码]/未验证（E8-77）；M2-01 实测确认 rc1=1 且状态保持 | 已核实（E8-77） | `VERDICT_R8_M2b.tsv` |
| U2 中 stage e（I1 特殊规则） | M2-02 NOT_FOUND_IN_SCOPE 裁决在 S4 不出点，转 S5（U248） | 转 S5（U248） | `STAGE_E_SEARCH_R8_M2a2_R2.tsv` |
| r8m2c/d SOLN 18/28 点分诊与更正 | U276-U282 裁决落实；-FA 装置纠偏完成（aligned:3）；正式两遍 28 点全 MATCH；合并总表 259 行全闭环 | 已闭合（U276-U282） | `M2_CONSOLIDATED_R8_M2e.tsv` |

## 4. 证据位置

只列最近三轮证据与清单位置，其余指向各轮报告：
- **S3 R5（s3r5）**：证据 `checkpoints/p05/evidence/p05-s3r5/`（`SHA256SUMS.txt`）；小表与清单 `checkpoints/p05/registries/s3r5/`（`SHA256SUMS.txt`）；报告 `P05_S3R5_CLOSEOUT.md`。
- **S4 R8 M2e（r8m2e）**：证据 `checkpoints/p05/evidence/p05-s4r8/m2e/`（`SHA256SUMS.txt`）；小表与清单 `checkpoints/p05/registries/s4r8/M2/r8m2e/`（`SHA256SUMS.txt`）；报告 `P05_S4R8_M2E_REPORT.md`。
- **S4 R8 M2d（r8m2d）**：证据 `checkpoints/p05/evidence/p05-s4r8/m2d/`（`SHA256SUMS.txt`）；小表与清单 `checkpoints/p05/registries/s4r8/M2/r8m2d/`（`SHA256SUMS.txt`）；报告 `P05_S4R8_M2D_REPORT.md`。
- 更早轮次证据与清单位置：详见各轮报告（`checkpoints/p05/P05_S4R*_REPORT*.md`）。完整台账：`RED_POINTS_LEDGER_R6c.tsv`；裁决总表：`registries/RULINGS.tsv`。
