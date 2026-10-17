# P05-S4 R9 M1 报告：F4 上重跑 M1（F3 侧 651 行）并与 F3 冻结事实等价比对

> 轮次标识：`r9m1`（P05-S4 子轮次 R9 的 M1，非新阶段）  
> 开工基线 HEAD：`3bb60723b3b23e313fd51d5a54f2258c98ac07eb`（r9m2c 收尾提交）  
> 记录提交 (i) HEAD：`00490a7`  
> 冻结被测树：F4（提交 `05097a7`，`S4/` 树哈希 `589e15eb11fcb04e031b524f25a443e7921946cf`）  
> 参照树：F3（`8d8202a`，`6cff923…`）、F2（`a07b5ac`，`e124925…`）、B（`37a82e8`，`1d738e6…`；仅基线对照，非修复证据）  
> 判定器 sha256：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`  
> 证据目录：`checkpoints/p05/evidence/p05-s4r9/m1/`  
> 小表提交目录：`checkpoints/p05/registries/s4r9/M1/`  
> 任务书存档：`checkpoints/p05/briefs/P05_S4R9_BRIEF_M1.md`  
> 规范约束：遵循 `AGENTS.md` 与本任务书纪律。**不宣布阶段完成，不询问是否签收。禁止 git commit --amend、rebase 及任何改写历史的操作。本报告内不记载收尾提交哈希。**

---

## 0. 身份、边界与旧任务说明

- **轮次定位**：P05-S4 子轮次 R9 的 M1 范围，聚焦于在 F4 树上重跑 M1 的 F3 侧行（651 行），并引用已冻结的 F2 侧行（651 行），生成 1302 行的 M1 F4 总表并与 F3 冻结事实进行逐行逐字段等价比对；不包含 M3（make test、Python/Lua E2E 验证）。
- **S4/ 源码与历史装置保护**：本轮未修改 `S4/` 源码目录、未修改判定器 `judge_d003.py`、未修改历史装置以及已提交的 r8/r9/r9m2b/r9m2c 脚本、allow 列表、报告与小表；所有新建脚本均位于 `testing/d003/stage_s4r9/` 且文件名带有 `r9m1`。
- **旧 Task014 说明**：用户此前转来的 "Task014 INCOMPLETE（DATA_INVALID）" 是 2026-10-03 P04 时期 D001/D002 线的旧输出（归档于 `.local-archive/p04-history-20261009T085100Z/audit-workspace/014/`），与 P05 无关，本轮不采信、不处理。
- **输入事实核实说明**：
  * 规划者在任务书 §2 中推测 F3 侧驱动族包含 `twice-*-F3` 等 15 族以上驱动。
  * 经执行者使用脚本复核原始有效表与运行记录，确认**规划者事实有误**：M1 的 F3 侧实际仅使用 12 个驱动族（d003-plain、d003plan-plain、init-plain、poly-plain、polyinj-plain、r6bseam-fmmret、r6bseam-seamF、r6bstate-dbg、r6dnv1-plain、seam-fmmret、seam-seamF、tri-dbg），完全不含 `twice-*` 系列驱动（`twice-*` 驱动属于 R6/M2 范围，在 M1 中不出现）。

---

## 1. 门禁核验结果

### 1.1 开工门禁（`GATE_R9M1_start.txt`）
- **HEAD 校验**：`3bb60723b3b23e313fd51d5a54f2258c98ac07eb`（PASS）；
- **HEAD:S4 校验**：`589e15eb11fcb04e031b524f25a443e7921946cf`（F4 冻结树，PASS）；
- **历史树校验**：F3 `6cff923…`、F2 `e124925…`、B `1d738e6…` 全部一致（PASS）；
- **判定器 sha256**：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`（PASS）；
- **工作区基线**：开工前 `git status --short` 为空；创建任务书与门禁脚本后与 `gate_allow_r9m1_start.txt` 5 项一致（PASS）；
- **清单比对**：
  * `registries/s3r5/SHA256SUMS.txt`（14 项全部 PASS）；
  * `registries/s4r9/M0/SHA256SUMS.txt`（25 项全部 PASS）；
  * `registries/s4r9/M2/SHA256SUMS.txt`（14 项全部 PASS）；
  * `registries/s4r9/M2b/SHA256SUMS.txt`（13 项全部 PASS）；
  * `registries/s4r9/M2c/SHA256SUMS.txt`（11 项全部 PASS）；
- **活文件基线核验**：
  * `STATE.md`：7868 字节，sha256 `64b369ef0f3f076719ed7ac865d088c707f7b6c0c1bbf7e54d3d28dc674945e4`（PASS）；
  * `RULINGS.tsv`：124392 字节，sha256 `f302748c2ffacfcdd9a0ca96a41bb82a567daa7096ccfe2d9852a4f38895b113`，前缀核验与 5 列格式通过（PASS）；
  * `ERRATA_S3R5.txt`：1712 字节，sha256 `a23ff03cd260548ae74205ca27c94d47a8a677d9c47bacfc5be6f5dec3077349`（PASS）；
  * `ERRATA_9.txt`：13893 字节，sha256 `e7e93590bec5a0340ed28859b0f292b8d21f1adfbd6502ef61ff741785052f12`（PASS）；
- **临时区快照**：开工条目数 0，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`（PASS）；
- **FAIL 计数与自检一致性**：
  * 门禁输出文件中 `^FAIL\t` 匹配行数：0；
  * 末行 `FAILS=` 字段值：0；
  * 两者一致性断言：通过，门禁正常退出（exit code 0）。

---

## 2. 用户裁决追加（U306–U311）

依据任务书 §3 与 §1-8 纪律，通过 `append_rulings_r9m1.py` 追加至 `checkpoints/p05/registries/RULINGS.tsv`（前缀字节断言保持不变，5 列格式与 U 编号唯一递增断言通过）：
- **U306**：R9 M1 只在 F4 上重跑 M1 的 F3 侧行（651 行）。F2 树未变，F2 侧行不重跑，引用 r8m1b3/r8m1c3 的正式判定并核对驱动 sha256。合并后总表断言 = 1302。
- **U307**：预注册规则。逐行取 F3 的有效行，tree→F4，driver→F4 对应驱动，sha 换为 F4 产物，point_id 的 -F3 后缀改为 -F4，exp_*（含 NOT_REACHED_AS_EXPECTED、NOT_RUN_AS_EXPECTED 与 I1–I6）原样保留。状态 INFLUENCED，basis 记录 "R9 M1 regression of <F3 point_id>"。不得因 F4 结果改期望。
- **U308**：S3R5 改动的影响清单。列出 F3 侧所有落在 Simulation_InitSolution（F3 行 1754–1774 区间）的行，输出 IMPACT_S3R5_R9M1.tsv。没有此类行时记 "0 行" 并附脚本输出。
- **U309**：K 继承证明规则。带计数注入的组在 F3、F4 上各跑一次无注入 gdb 映射：两边命中总数相等；每次命中带大小或计数器 id 与 S4 帧（行号经 LINEMAP 映射）。已证明的组可引用；HIT 等价表分开计 BOTH_EMPTY 与 NONEMPTY_IDENTICAL。k_max=1 且取不到序列的组可按 U303 用 HIT 行等价替代。任一组 DIVERGENT 则该组行不进入正式运行。
- **U310**：装置对等。F4 缺的驱动与库重新构建，去掉树路径后编译/链接命令行与 F3 对应驱动逐条相同（0 项差异）；每个库告警数等于 F3 对应库。已存在产物不重编只核 sha256。
- **U311**：执行顺序与停止。start 门禁 → 裁决追加与记录提交 (i) → 阳性对照 → 冒烟 → 正式两遍 → 判定 → 合并总表 → 收尾提交 (ii)。冒烟出现 MISMATCH、GDB_DIVERGENT 或 INVALID 时停在冒烟分诊。正式运行中 MISMATCH 或 FLAKY 照实记录。

---

## 3. 装置核实与构建（Step S-B）

### 3.1 驱动清单与映射（`DRIVERS_F3_SIDE_R9M1.tsv`）
脚本 `driver_inventory_r9m1.py` 梳理 M1 F3 侧全部 651 行所使用的驱动，共确定 12 个驱动族：
- **已有 F4 驱动（5 项，沿用自 R9 M0 / s3r5，核验 sha256）**：
  1. `d003-F4-plain`：sha256 `e39e4b0f4a66b7bf6d19b558636ffbdb76b1e35eec4825c2398600eb35e0d9f6`（覆盖 141 行）；
  2. `d003plan-F4-plain`：sha256 `41d2d579715c77d595831fde670c171880f198e37eaf52ad27477d65673292e3`（覆盖 111 行）；
  3. `r6bstate-F4-dbg`：sha256 `2bce13d9f23276a0153ea8fa30464bf2cbfd99798f5d8336c1c1f8e285b15aa2`（覆盖 193 行）；
  4. `r6bseam-seamF-F4`：sha256 `e53560673269090865be502f96aa06fb693f867afdbbfdd3c109eb759547911d`（覆盖 23 行）；
  5. `seam-fmmret-F4`：sha256 `10e4f2ce7f4df4fb688d032a2b72e784d41fccfe25337a396009a11994178b1c`（覆盖 10 行）。
- **新建 F4 驱动（7 项，在 `$EV/build/` 下构建）**：
  1. `init-F4-plain`：对应 `init-F3`（覆盖 10 行）；
  2. `poly-F4-plain`：对应 `poly-F3`（覆盖 33 行）；
  3. `polyinj-F4-plain`：对应 `polyinj-F3`（覆盖 12 行）；
  4. `r6dnv1-F4-plain`：对应 `r6dnv1-F3-plain`（覆盖 72 行）；
  5. `tri-F4-dbg`：对应 `tri-F3-dbg`（覆盖 9 行）；
  6. `seam-seamF-F4`：对应 `seam-seamF-F3`（覆盖 17 行）；
  7. `r6bseam-fmmret-F4`：对应 `r6bseam-fmmret-F3`（覆盖 20 行）。
- **无法映射项**：0 项。

### 3.2 装置构建与对等核查（`BUILD_R9M1.tsv`、`BUILD_OPTION_DIFF_R9M1.txt`、`WARN_COUNT_R9M1.tsv`）
- **新建 Seam 库构建**：
  * `lib_F4_seamF_plain`：从 F4 导出树应用 ACD 和 B2 补丁，使用 `-O3 -Wall -march=native` 编译，告警数 71（等于 F3 的 `seamF-F3-plain` 71 项告警）；
  * `lib_F4_fmmret_dbg`：从 F4 导出树应用 fmmret 补丁，使用 `-O0 -g -Wall` 编译，告警数 62（等于 F3 的 `fmmret-F3` 62 项告警）。
- **新建驱动编译与告警**：
  * `poly-F4-plain` 与 `polyinj-F4-plain` 告警数均为 3（等于 F3 对应驱动的 3 项告警）；
  * 其余 5 个新建驱动告警数均为 0（等于 F3 对应驱动的 0 项告警）。
- **编译/链接参数比对**：
  * `BUILD_OPTION_DIFF_R9M1.txt` 比对结果显示差异标记数：0 项（满足 U310 规定）。

### 3.3 无注入对照（`NOINJ_R9M1.tsv`、`noinj_r9m1.txt`）
- 7 个新建驱动在所有 clean base_env 组合下各执行一次无注入运行，共 82 个组合；
- **测试结果**：82 项全部 PASS（进程返回码 rc=0，sanitizer 报错数为 0）。

---

## 4. K 继承证明与 S3R5 影响清单（Step S-C）

### 4.1 S3R5 影响清单（`IMPACT_S3R5_R9M1.tsv`）
- 脚本 `impact_s3r5_r9m1.py` 对比 S3R5 修改区间（S4.cpp Simulation_InitSolution 1754–1774 行，解内存分配修复）；
- **排查结果**：M1 的 651 个 F3 侧点中，没有任何点的注入位置或 K 映射帧落在该区间（ADD22 的 A-1729 位于 1729 行，小于 1754；其余 FMM / Seam 点均在对应算法模块内）；
- 依据 U308，清单记录为 **0 行**。

### 4.2 K 继承证明（`K_INHERIT_R9M1.tsv`、`K_INHERIT_RAW_R9M1.txt`）
- 脚本 `k_inherit_r9m1.py` 对 M1 涉及的所有 53 个计数注入组进行 F3 vs F4 的 gdb 断点映射测试；
- **测试结果**：
  * **DIVERGENT 组**：0 组（所有 53 组两侧命中数均完全相等，无提前终止或命中偏差）；
  * **带调试符号组（18 组，r6bstate-dbg）**：全部获得 S4 源码帧与大小信息，行号经 LINEMAP 映射后完全一致，判定为 `PASS_K_INHERITED_R2`（18/18）；
  * **plain 驱动组（35 组，d003-plain、d003plan-plain、init-plain、polyinj-plain）**：由于未带 `-g` 编译，无法获取 S4 源码行号；但 init 与 polyinj 输出了完全一致的 trace 序列；依据 U300 / U303 / U309 判定规则，记录为 `NO_SEQ_EVIDENCE_R2` 并由后续 HIT 行等价作为替代证据支持。

---

## 5. 预注册与记录提交 (i)（Step S-D）

### 5.1 预注册表冻结
- **F4 回归矩阵（`PREREG_M1_F4_R9M1.tsv`）**：
  * 行数：651 行（M1b 415 行 + M1c 236 行）；
  * sha256：`d57fcf29e5728316f8c08918bb62934edf3975bc70fba45ecdaae8e73af69865`；
  * 时间戳：`2026-10-17T15:24:18Z`；
  * 状态：INFLUENCED；basis：`R9 M1 regression of <f3_point_id>`；
  * 期望分布：MATCH 626 行、NOT_REACHED_AS_EXPECTED 22 行、NOT_RUN_AS_EXPECTED 3 行。
- **F2 引用基线（`PREREG_M1_CITED_F2_R9M1.tsv`）**：
  * 行数：651 行（M1b 415 行 + M1c 236 行）；
  * sha256：`72fa0e4d190e0ead0d2ebf8ab5c161d770d8d9ccd2020fd35f12e3dd4b8933dd`；
  * 时间戳：`2026-10-17T15:24:18Z`；
  * 状态：CITED_R8；
  * 期望分布：MATCH 626 行、NOT_REACHED_AS_EXPECTED 22 行、NOT_RUN_AS_EXPECTED 3 行。
- **行数断言**：651 + 651 = 1302 行（断言通过）。
- **引擎读取列核对（`ENGINE_COLUMNS_R9M1.txt`）**：
  * 判定引擎实际读取：`exp_rc1`、`exp_rc2`、`exp_hit`、`exp_class` / `exp_point_verdict`；
  * 条件读取：`exp_rc3`（仅在 G5 读取）、`exp_I1`–`exp_I6`（仅在 G5 经 state_analyzer 读取）；
  * 引擎不读列：`exp_I7`（标记为 DEFERRED，引擎不读取）、`exp_san`（M1 中无 sanitizer 点，不读取）。

### 5.2 记录提交 (i)
- 提交哈希：`00490a7`；
- 提交信息：`record(p05-s4r9): M1 brief, rulings U306-U311, driver inventory, K proof, preregistration (awaiting user review)`。

---

## 6. 阳性对照（Step S-E）

脚本 `posctrl_r9m1.py` 调用正式比较脚本 `compare_f3_f4_r9m1.py`：
- **Case 1（未篡改的 F3 冻结事实输入）**：
  * 期望：DIFFS=0；
  * 实测：CHECKS=651，DIFFS=0（PASS）；
- **Case 2（在 `$EV/tmp` 中篡改 1 处 rc1 与 1 处 I1 副本）**：
  * 篡改点 1：M1b G7 `M1-G7-F3-fftnv-ng1-m1` 的 rc1 由 20 篡改为 1；
  * 篡改点 2：M1c G5 `M-once-closed1d-malloc-1-F3` 的 I1 由 HOLD 篡改为 RELEASE；
  * 期望：DIFFS=2，且恰好在上述两处检出；
  * 实测：CHECKS=651，DIFFS=2，检出字段准确对应（PASS）。
- 记录保存于 `checkpoints/p05/evidence/p05-s4r9/m1/POSCTRL_M1_R9M1.txt`。

---

## 7. 冒烟运行（Step S-F-1）

脚本 `run_smoke_r9m1.py` 抽取覆盖 23 个有效 (section × group × driver) 组合的代表性点进行单遍冒烟：
- **运行核验**：每条运行前后驱动 sha256 均与预注册一致；
- **分诊规则核查**：无 MISMATCH、无 INVALID、无 GDB_DIVERGENT（全部 23 点均为 MATCH 或 NOT_RUN_AS_EXPECTED）；
- **结论**：冒烟测试通过，未触发硬停止条件，准予进入正式运行。
- 记录保存于 `SMOKE_M1_F4_R9M1.tsv` 与 `SMOKE_SUMMARY_R9M1.txt`。

---

## 8. 正式运行结果与判定（Step S-F-2 / S-G）

### 8.1 正式两遍运行（`FORMAL_FACTS_M1_F4_R9M1_pass1.tsv`、`..._pass2.tsv`）
- 两遍运行分别输出于 `runs/formal/pass1/` 与 `runs/formal/pass2/` 独立目录；
- 每条运行前后驱动 sha256 均与预注册严格核验一致；
- M1c 的 G5 与 G6 组通过历史装置 `run_r6c_state.py` 与 `r6c2_seam_state.py` 执行，两遍 state_analyzer 分析结果完整落盘。

### 8.2 判定结果（`VERDICT_M1_F4_R9M1.tsv`、`VERDICT_M1_F4_R9M1_AGG.tsv`）
脚本 `verdict_r9m1.py` 对 651 个 F4 运行点进行判定：
- **两遍一致性**：651 点 pass1 与 pass2 事实完全一致，**FLAKY = 0**；
- **GDB 分歧**：**GDB_DIV = 0**；
- **判定分布**：
  * **MATCH**：626 行（M1b 390 行 + M1c 236 行）；
  * **NOT_REACHED_AS_EXPECTED**：22 行（M1b G1 中 22 个已知未达点）；
  * **NOT_RUN_AS_EXPECTED**：3 行（M1b G2c_control 3 行）；
  * **MISMATCH**：**0 行**。

### 8.3 F3 与 F4 事实等价比对（`F3_F4_EQUIV_R9M1.tsv`）
脚本 `compare_f3_f4_r9m1.py` 对 F4 正式运行结果与 F3 历史冻结事实进行逐行、逐字段比对（rc1、rc2、rc3、hit、class、I1–I6、env）：
- **比对结果**：CHECKS = 651，**DIFFS = 0**（全部 651 行事实完全一致）；
- **HIT 行等价分类**：
  * **BOTH_EMPTY**：122 行（双方命中数均为 0 或未运行）；
  * **NONEMPTY_IDENTICAL**：529 行（双方命中数均大于 0 且数值与行为完全相同）；
  * **DIVERGENT**：0 行。

---

## 9. M1 F4 汇总总表（Step S-G，`M1_SUMMARY_F4_R9M1.tsv`）

脚本 `summarize_m1_r9m1.py` 合并 F4 回归结果（651 行）与引用的 F2 冻结基线（651 行）：

### 9.1 总表合计
| 判定类别 | M1b（830 行） | M1c（472 行） | 合计（1302 行） |
|---|---|---|---|
| **MATCH** | 780（F2 390 + F4 390） | 472（F2 236 + F4 236） | **1252** |
| **NOT_REACHED_AS_EXPECTED** | 44（F2 22 + F4 22） | 0 | **44** |
| **NOT_RUN_AS_EXPECTED** | 6（F2 3 + F4 3） | 0 | **6** |
| **MISMATCH** | 0 | 0 | **0** |
| **FLAKY** | 0 | 0 | **0** |
| **总计** | **830** | **472** | **1302** |

### 9.2 断言校验
- `M1B_SUM_EQ_830`：TRUE；
- `M1C_SUM_EQ_472`：TRUE；
- `GRAND_TOTAL_EQ_1302`：TRUE；
- 各节分项计数之和与总行数严格闭环一致。

---

## 10. 事件表（Step S-H）

### 表一：越界写入尝试表
| 序号 | 轮次 | 命令/操作 | 尝试路径 | 是否落盘 | 处理与说明 |
|---|---|---|---|---|---|
| - | r9m1 | 无 | 无 | 否 | 本轮未发生任何越界写入尝试 |

### 表二：工具与脚本事件表
| 序号 | 轮次 | 时间 (UTC) | 类别 | 命令 / 详情 | 是否落盘 | 说明与披露 |
|---|---|---|---|---|---|---|
| 1 | r9m1 | 2026-10-17T14:40Z | 框架只读命令 | `find checkpoints/p05/evidence -type f -name "*F4*" 2>/dev/null || true` | 否 | 只读查询中内联使用了 `2>/dev/null`，违反 §1-3 纪律；无任何写入发生，在此公开披露 |
| 2 | r9m1 | 2026-10-17T14:46Z 起 | safe_run 正常执行 | `safe_run.log` 共记录执行命令 | 是 | 全部文件修改与执行均通过 safe_run.sh 运行 |
| 3 | r9m1 | - | 裸写核查 | 0 处裸写 | 否 | 本轮除 safe_run 记录外，无任何未记录的裸写 |

---

## 11. 需用户裁决事项

**无**（本轮未出现硬停止条件，未出现 DIVERGENT 或 FLAKY，所有门禁与测试全部通过）。

---

## 12. 结语

本轮已完成 R9 M1 范围，等待用户审核。
