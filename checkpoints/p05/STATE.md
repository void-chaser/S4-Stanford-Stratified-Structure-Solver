# P05 当前状态（每轮结束更新，一页以内）

> 规则见仓库根 `AGENTS.md`。本文件是摘要，细节以各轮报告为准。签收只由用户在对话中给出。

## 1. 当前位置

| 项 | 值 |
|---|---|
| 分支 | `codex/p05-d003-fft-error-propagation` |
| 开工基线 HEAD（P05-S4 R8 M0 开工） | `3ab56801e697910bdff9fbe6056807c2e41841b5`（S3R4 续5 收尾；R8 M0 记录提交 `2875c55`） |
| 收尾提交 | 修改本文件的最后一次提交（`git log -1 --format=%H -- checkpoints/p05/STATE.md`） |
| `HEAD:S4`（当前冻结被测树 F3） | `6cff923a02baf19e01966b2339755cbf3a5deeef`（F3 提交 `8d8202a`，P05-S3R4 修复候选；前一冻结树 F2 `e124925f…` = `a07b5ac`；F `4a6f649…` = `1c11905`） |
| 判定器 sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` |
| 阶段签收 | S1、S2 已签收（带范围声明，`P05_S1_S2_SIGNOFF.md`）；S3、S4、S5 未签收 |
| 当前轮次 | **P05-S4 R8 M1a 续3a 审核修正（r8m1a4audit）：技术停止，未完成，不进入续3b。** 已核实：U176–U182/E8-56–E8-62 已记录；E8-55 经 U177 更正生效（有效统计 BP_LINE 2/REGISTRY_ONLY 26/NO 3；v3c 历史统计 BP_LINE 4/REGISTRY_ONLY 26/NO 1，两者并存，历史统计不改）；原续3a 报告中 S3R4 新增项"9/9 MATCH"依赖硬编码 n_values=36 与默认 0，**作废**（E8-64）；非硬编码重算已完成，9 组合 MATCH 9、MISMATCH 0（首次运行 3 个 MISMATCH 为判据与键名缺陷，修正后重跑，事后修正已披露，E8-65）；原报告引用的 `_R2` 覆盖检查为修正前版本，有效版本为 `_R3`（E8-64）；`_R3` 运行前准备自检未满足恢复补充第 8 条全部要求，gdb 运行时序是否有效待用户裁决（E8-63）。 |
| 前一轮次 | **P05-S4 子轮次 R8 M0（F3，第 3 次开工）**（非新阶段）：D 冒烟 8 点两遍 MATCH 8/8、FLAKY 0（U113、U119、U124、U125）；F2↔F3 无注入等价 117/117 IDENTICAL（39 组合，0 NOT_IDENTICAL；closed→closed2d 依据 E7-3/U40）；F3 构建 dbg 62 / plain 71 告警；seam 差异 IDENTICAL（seamF 237 行、fmmret 72 行）。门禁历史：首次 FAILS=6（U128/U129）、第 2 次越界停止（U130）、收尾 R2_END FAILS=1（U133 规则疏漏）、收尾 R3_END FAILS=0。下一步：R8 M1（含 dbg 库 strip 等价，U136；待用户审核）。报告：`P05_S4R8_REPORT_M0.md`。 |
| 历史 | S3R4 首轮：修复 806、415 链路、RP-S3R4-1 冻结 F3 `8d8202a`（U91 四个文件，U96 单提交）；编译告警零新增。P05-S4 R7 完成 M1–M3（F2 回归；M3 收尾 `cc49c6b`，建议待裁决）。未签收。 |

## 2. 关键数字（每轮一行）

| 轮 | 关键数字 | 报告 |
|---|---|---|
| R1–R5 | R1 门禁与预注册；R2 三列 45 行（34 MATCH）；R3 范围内 141 点；R4 seam 25/25 REPORTED_FAILURE；R5 等价 24/24、M=2 36 点 MATCH、V4 sanitizer 0 发现、V3 132 点 IDENTICAL | `P05_S4R2_REPORT.md` … `P05_S4R5_REPORT.md` |
| R6 | R6-1 twice NTH 12–16 在 TWICE=slab 下 48 次全 MATCH（U1）；R6-2 单点 I1 实测；R6-3 RNV1 延后（U16）；R6-4 账本于 R6c2 完成 | `P05_S4R6_REPORT.md` |
| R6b | 映射 202 点；预注册 177 点（INFLUENCED）；对照 16 组合；单点 gdb 与无 gdb rc 一致 | `P05_S4R6b_REPORT.md` |
| R6c | 里程碑 `6bba0bd`：177 点两遍 HOLD 177 / VIOLATED 0 / FLAKY 0 / GDB_DIVERGENT 0；seam 等价 25/25、inj_call 全为 1 | `P05_S4R6c_REPORT.md`、`P05_S4R6c_REPORT_ADDENDUM_seam.md` |
| R6c2 | E6c-6 哈希勘误（前 64 行字节一致）；U18 对照 18 行；判定器自检 11/11 + 原行 3/3；seam 25 点两遍 HOLD 25 / VIOLATED 0 / FLAKY 0 / GDB_DIVERGENT 0；红点总账；修复方案（无 F_CONFIRMED 候选） | `P05_S4R6c2_REPORT_PART2.md` |
| R6d | U2 阶段表 202 点 CONSISTENT / 0 CONFLICT / 0 UNRESOLVED（a2 b197 c1 d2 e0；e 未覆盖，去向 R8）；RNV1 注入 F 72/72 CRASH（两遍）→ RP-R6d-1 **F_CONFIRMED**；账本 v2 20 行；方案 v2（S4/ 未改） | `P05_S4R6d_REPORT.md` |
| S3R3 | 修复 `a9679bc`（pattern.c，方案 R3）、注释 `a07b5ac`（U31）；冻结 F2 `e124925f…`；编译告警 62/71 零新增；自检 A：F2 RNV1 36 点 REPORTED_FAILURE 36/36（未经 S4 验证）；自检 C：F tri 3 点 CRASH、F2 3 点 REPORTED_FAILURE；B 无注入 36 项 IDENTICAL；D：nv/vl NG9 冒烟 rc 0 | `P05_S3R3_CLOSEOUT.md` |
| S3R4 | 修复 806、415、RP-S3R4-1，冻结 F3 `8d8202a`（编译告警 62/71 零新增）；自检 C 圆形/三角 117/117 IDENTICAL（首轮）；续1 停止（U103）；续2：C 多边形 99/99 IDENTICAL、驱动 rc 66/66 为 0；A1 映射 K 唯一（closed2d NG1 K=7、fft/kottke NG5 K=8，K0=6/7）；A 预注册 18 行；续3：**A 36/36 MATCH、对照 6/6**；**B 44/44 MATCH、对照 12/12**（F3 REPORTED_FAILURE rc1=20，F2 CRASH）；Mfirst（fft NG1 = 1，其余 = 64）；窗口 malloc n = 36；续4 停止（U116）；续5：CONT3 交付物补齐（只读），**D 转入 R8 第 0 步**（U113） | `P05_S3R4_CLOSEOUT.md`、`_CONT1`、`_CONT2`、`_CONT3`、`_CONT4`、`_CONT5.md` |
| S4R7 | M1、M2（run7：CTRL_SEAM 4/4、G2c 60、G1 254 MATCH + 44 NOT_REACHED、G2a 50，MISMATCH 0、FLAKY 0）、M3（G5 177、G6 25，VIOLATED 0） | `P05_S4R7_REPORT_FINAL.md`、`P05_S4R7_REPORT_M2_FINAL.md` |
| S4R8 M1a（F3，续3a 审核修正，技术停止） | 原续3a 数字区分：历史静态统计 BP_LINE 4/REGISTRY_ONLY 26/NO 1（v3c，保留）；U177 有效统计 BP_LINE 2/REGISTRY_ONLY 26/NO 3。`_R3` 单元 198（99 对，运行前准备自检不完整，E8-63）；gdb 运行 198 次 trace_error NONE、比较 99 IDENTICAL（运行数据内部一致，时序有效性待裁决）。历史规则比较：1026 MAPPED 行 OK 1026、MISMATCH 0（TWICE 一项来源弱于其余三项，E8-63）。覆盖检查 `_R3`：1026 REACHED、22 DEFERRED、80 N/A、0 UNKNOWN（`_R2` 为修正前版本，不作依据，E8-64）。S3R4 新增项 9 组合旧"MATCH"依赖硬编码，**作废**（E8-64）；非硬编码重算 9/9 MATCH（修正后，事后修正已披露，E8-65）；22 行映射严格关联 22 MAPPING_VERIFIED_STRICT（仅无注入映射，不是 22 次注入验证）。严格离线复算 198 单元 PASS 198、FAIL 0、事件 19182（E8-65）。未完成：§二 完整请求语义重建（逐行 1128、44 行 INVALID_NOT_REACHED、旧 1026 差异表）；§四 追踪器符号证据表与缺口补跑；未做注入回归。 | P05_S4R8_REPORT_M1a_CONT3a_AUDIT.md（补充报告，原报告保留） |
| S4R8 M0（F3） | F3 构建 dbg 62 / plain 71 告警（plain 库与 S3R4 SAME，dbg DIFFERENT 已记录）；seam 差异 IDENTICAL；D 冒烟两遍 MATCH 8/8、FLAKY 0；F2↔F3 无注入等价 117 IDENTICAL、0 NOT_IDENTICAL（39 组合）；门禁首次 FAILS=6、重启 FAILS=0 | `P05_S4R8_REPORT_M0.md` |

## 3. 开放问题（状态 · 去向 · 链接；细节见报告附录 A 与总账）

| 项 | 状态 | 去向 |
|---|---|---|
| S3-4b（失败后模式/缓存不安装） | **由用户带范围声明关闭（U29）**，只关闭此项，不代表 P05-S3/S4 签收；范围声明见 `P05_S3_4b_CLOSURE.md`；未覆盖：阶段 e、I7、双目标注入、其他层失败变体 | 转 R8（F3 上） |
| D 冒烟 8 点 | 已运行（R8 M0，两遍）：MATCH 8/8、FLAKY 0（`D_SUMMARY_R8.txt`）；登记 `REGISTRY_S3R4C3_D.tsv` 原样保留；驱动规则 U124；范围：冒烟，不是修复验证 | 完成（M0）；M1 起的回归见 R8 计划 |
| F3-dbg 库 sha256 与 S3R4 首次记录不同（E8-9） | **已关闭（R8 M1a，E8-19）**：去调试段后 24 成员 EQUAL_AFTER_STRIP，差异只来自调试段；不是修复验证 | — |
| U171 BP_LINE 规则是否计注释行（E8-55；映射 v3c 中 S4/fmm/fmm_FFT.cpp:90、fmm_kottke.cpp:94 依赖 stage_s4/r6_plan14_caller.gdb 的文件名出现在 s4r7 LINEMAP_M3_R7.tsv 第 13 行注释中） | **已关闭（R8 M1a 续3a，U177/E8-56）**：排除注释行引用后，有效分类改为 NO，有效统计 BP_LINE 2、REGISTRY_ONLY 26、NO 3；生成 USED_IN_M1_CORRECTION_R8_M1a4.tsv，原静态映射不重跑 | — |
| 806、415、RP-S3R4-1 | 注入自检通过（F3，A 36/36、B 44/44）；修复后验证未做 | R8（F3 上，修复后验证） |
| R7 M2b CTRL_SEAM fmmret 两行驱动与登记不符（ES3R4-29） | 记录更正（U118）；离线解析 seamF 驱动、AGREE/DISAGREE 如期望（`CTRL_SEAM_DRIVER_RESOLUTION_C5.tsv`）；R8 M0 中 D 的 `CTRL-SEAM-fmmret-F` 在 F3 plain 上用 fmmret 族驱动 `seam-fmmret-F3` 运行，CONTROL_OK、MATCH 两遍（干净对照的一项）；fmmret plain 干净对照的完整补测仍在 M2 | R8 M2（完整补测；以 M3 G6 为准） |
| RNV1（pattern malloc 无 NULL 检查，RP-R6d-1） | F 上 CRASH（R6d）；S3R3 采用方案 R3（U30，提交 `a9679bc`）；F2 自检通过，未经 S4 验证；S3R4 修复后 F3 | R8（F3 上，U92） |
| 双目标注入、I7 sanitizer | DEFERRED（U9） | R8（U25，E7-1） |
| "其他层失败"变体 | DEFERRED（U20） | R8（U25，E7-1） |
| 注释措辞 `S4/S4_internal.h:263`（U11） | 已改为 U31 措辞（提交 `a07b5ac`） | R8 回归确认 |
| 张量路径 K-1（RP-R6d-8） | F_SUSPECT_SOURCE（[源码]，未测） | R8 |
| B 侧 jones/vl SILENT_SWALLOW、nv CRASH | OPEN（基线，不是修复证据） | S5 |
| Python/Lua 可见性、NB=1–8、类别 C | OPEN / DEFERRED | R8（U34，E7-1） |
| ES3R4-5(a)(b)（首个形状返回码 i+1；pattern.c:798 循环变量 i/j） | OUT_OF_SCOPE_D003（U99、U95） | S5 |
| −1…−9（Pattern_DiscretizeCell 在 FFT/Kottke 中被忽略） | OUT_OF_SCOPE_D003（U100；[源码] 说明已写：`registries/s3r4c3/U100_SOURCE_NOTE.md`） | S5 |
| 528、1164（S3R4 U90 分类） | OUT_OF_SCOPE_D003（无调用者；唯一调用点已注释） | S5 |
| D016 B 侧 rc 20 来源；B 侧 vl NG=1 rc 20 | OPEN（BASELINE_ONLY） | R7 观察 → S5 |
| 非 FMM `S4_malloc`（约 35–43 处） | OUT_OF_SCOPE_D003 | S5 |
| U2、U4、U5 原文 | 用户在 R6d 对话中补录；U2 部分落实（U28） | U2 覆盖见 `evidence/p05-s4r6d/U2_COVERAGE_R6d.tsv` |
| U2 中 stage e（I1 特殊规则） | 0 点，**未覆盖** | R8 |

完整台账：`evidence/p05-s4r6c/RED_POINTS_LEDGER_R6c.tsv`；裁决总表：`registries/RULINGS.tsv`（U103–U120 已追加）。

## 4. 证据位置

证据目录 `checkpoints/p05/evidence/<轮次>/`（不提交）；小型结果表与清单 `checkpoints/p05/registries/<轮次>/`（提交）。S4 R8 M0：证据 `evidence/p05-s4r8/`（清单 `SHA256SUMS.txt`，不提交），小表与清单 `registries/s4r8/SHA256SUMS.txt`（提交）；门禁 `GATE_R8_M0.txt`（首次，停止）、`GATE_R8_M0_R2.txt`、`GATE_R8_M0_R2_END.txt`（收尾停止）、`GATE_R8_M0_R3_END.txt`（收尾，FAILS=0）。S3R4 续5：证据 `evidence/p05-s3r4c5/`（清单 `SHA256SUMS.txt`），小表与清单 `registries/s3r4c5/`。S3R4 续3：证据 `evidence/p05-s3r4c3/`，小表与清单 `registries/s3r4c3/`（续5 只读补齐的交付物在 `p05-s3r4c5/`）。S3R4 续2：证据 `evidence/p05-s3r4c2/`，小表与清单 `registries/s3r4c2/`。S3R4 续1：证据 `evidence/p05-s3r4c1/`（仅门禁与 safe_run 日志）。R6c2：`evidence/p05-s4r6c/`，清单 `registries/s4r6c/SHA256SUMS_closeout.txt`。R6d：`evidence/p05-s4r6d/`，小表与清单 `registries/s4r6d/`。各轮清单见各目录的 `SHA256SUMS*.txt`。
