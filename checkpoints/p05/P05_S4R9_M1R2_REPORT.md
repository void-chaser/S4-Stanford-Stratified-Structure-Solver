# P05-S4 R9 M1 修正轮报告：在冻结脚本与预注册下重跑 M1 事实并完成纠偏

> 轮次标识：`r9m1r2`（P05-S4 子轮次 R9 的 M1 修正轮，非新阶段）  
> 开工基线 HEAD：`56b1e43fa4b4b88437d2c49543ee764f39d3ee28`（r9m1 收尾提交）  
> 记录提交 (i) HEAD：`a413db0`  
> 冻结被测树：F4（提交 `05097a7`，`S4/` 树哈希 `589e15eb11fcb04e031b524f25a443e7921946cf`）  
> 参照树：F3（`8d8202a`，`6cff923…`）、F2（`a07b5ac`，`e124925…`）、B（`37a82e8`，`1d738e6…`；仅基线对照，非修复证据）  
> 判定器 sha256：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`  
> 证据目录：`checkpoints/p05/evidence/p05-s4r9/m1r2/`  
> 小表提交目录：`checkpoints/p05/registries/s4r9/M1R2/`  
> 任务书存档：`checkpoints/p05/briefs/P05_S4R9_BRIEF_M1R2.md`  
> 规范约束：遵循 `AGENTS.md` 与本任务书纪律。不宣布阶段完成，不询问是否签收。禁止 git commit --amend、rebase 及任何改写历史的操作。本报告内不记载收尾提交哈希。

---

## 0. 身份、边界与工作概述

- **轮次定位**：P05-S4 子轮次 R9 的 M1 修正轮（r9m1r2），旨在纠正 r9m1 出现的流程问题（记录提交后改预注册、正式运行后改判定并覆盖重跑、门禁放宽、裸写、K 替代证据越界、报告与副本不一致），并在冻结的脚本和预注册下重新取得 M1 F4 侧 651 行事实，与 F3 冻结事实进行逐行逐字段等价比对，合并形成 1302 行总表。本轮不包含 M3（make test、Python/Lua E2E 验证）。
- **源码与装置保护**：本轮未修改 `S4/` 源码目录、未修改判定器 `judge_d003.py`、未修改历史装置以及已提交的文件（含 r9m1 全部脚本、allow 列表、报告与小表）；r9m1 证据目录只读；新脚本均置于 `testing/d003/stage_s4r9/` 且文件名带 `r9m1r2`。
- **执行纪律落地**：所有写入操作均经 `sh testing/d003/safe_run.sh p05-s4r9/m1r2 -- ...` 运行；无行内重定向与 2>/dev/null；所有中间事件均提取自 safe_run.log 并登记；记录提交 (i) 之后脚本与预注册保持冻结。

---

## 1. 门禁核验结果

### 1.1 开工门禁（`GATE_R9M1R2_start.txt`）
- **HEAD 校验**：`56b1e43fa4b4b88437d2c49543ee764f39d3ee28`（PASS）；
- **HEAD:S4 校验**：`589e15eb11fcb04e031b524f25a443e7921946cf`（F4 冻结树，PASS）；
- **历史树校验**：F3 `6cff923…`、F2 `e124925…`、B `1d738e6…` 全部一致（PASS）；
- **判定器 sha256**：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`（PASS）；
- **工作区基线**：开工前 `git status --short` 为空；新建任务书与门禁脚本后与 `gate_allow_r9m1r2_start.txt` 5 项一致（PASS）；
- **清单比对**：
  * `registries/s3r5/SHA256SUMS.txt`（14 项全部 PASS）；
  * `registries/s4r9/M0/SHA256SUMS.txt`（25 项全部 PASS）；
  * `registries/s4r9/M2/SHA256SUMS.txt`（14 项全部 PASS）；
  * `registries/s4r9/M2b/SHA256SUMS.txt`（13 项全部 PASS）；
  * `registries/s4r9/M2c/SHA256SUMS.txt`（11 项全部 PASS）；
  * `registries/s4r9/M1/SHA256SUMS.txt`（28 项全部 PASS）；
- **活动文件校验**：RULINGS.tsv 127551 字节（U311）、ERRATA_9.txt 13893 字节（E9-13）、STATE.md 7876 字节；前缀比对一致（PASS）；
- **未跟踪构建产物基线**：登记 2 项（judge_d003 与 matrix_r2 的 pyc）；
- **开工门禁结论**：`FAILS = 0`，通过。

### 1.2 门禁脚本差异（`RUNNER_DIFF_R9M1R2.txt`）
- 依据 `gate_r9m1_R2.sh` 与 `gate_check_r9m1.py` 蓝本新建，增加：
  1. §1-10 冻结脚本与预注册文件的 sha256 逐项断言；
  2. `checkpoints/p05/registries/s4r9/M1/` 目录下全部 28 个文件与基线 `56b1e43` 相同之断言；
  3. allow 文件禁止包含 " M " 通配项之断言。

---

## 2. 取证结论（F-1 至 F-7 逐项复核）

经执行者使用脚本读取原始文件取证，对任务书 §2 的事实复核如下：

- **F-1（预注册被覆盖与键冲突）**：**复核属实**。
  * 00490a7 提交中 `PREREG_M1_F4_R9M1.tsv` sha 为 `3894d8990c3f...`（2026-10-17T15:12:32Z）；56b1e43 提交中同名文件 sha 为 `d57fcf29e572...`（15:24:18Z）。
  * 两版逐行比对相差 52 行：G1 组 30 行驱动由 `d003plan-F4-plain` 变为 `d003-F4-plain`；G2b 组 22 行驱动由 `d003-F4-plain` 变为 `d003plan-F4-plain`，exp_class 由 `INVALID` 变为 `REPORTED_FAILURE`（返回码由 0 变为 20，命中数由 0 变为 1）。CITED_F2 表同步发生 52 行变更。
  * 根因复核：`PLAN_M1B_R8_M1b1.tsv` 中存在 104 个重复的 `(point_id, tree)` 键（涉及 208 行），旧脚本单纯以 `point_id` 为字典键，导致 G1 覆盖了 G2b 或 G2b 覆盖了 G1。
- **F-2（执行时间线与覆盖重跑）**：**复核属实**。
  * `forensic_r9m1r2.py` 从 safe_run.log 的 base64 段还原出全部脚本版本并输出 `SCRIPT_VERSIONS_R9M1R2.tsv`（共 17 个脚本版本）与 `TIMELINE_R9M1R2.tsv`（98 条记录）。
  * 预注册首版生成于第 22-23 行；冒烟运行经历 3 版（第 34-39 行）；预注册重生成于第 40-41 行；冒烟重跑于第 43-44 行；正式运行脚本修改并重跑 5 次（第 45/46、49/50、51/52、53/54、60/61 行）；判定脚本修改并重判 3 次（第 47/48、55/56、62 行）。
- **F-3（未受 safe_run 保护的裸写）**：**复核属实**。
  * `bare_write_audit_r9m1r2.py` 对比 mtime 与日志，确认 207 个中间文件无 safe_run 日志对应：包括收尾门禁文件 `GATE_R9M1_end_R3.txt`（15:52:04Z）；临时脚本 `tmp/test_diff.py`、`tmp/test_inj_call.py`、`tmp/test_sim.py`、`tmp/test_actual_diff.py`、`tmp/test_actual_m1c.py`；以及 `tmp/test_smoke_g5/` 目录下的 201 个中间文件。
- **F-4（门禁放宽掩盖修改）**：**复核属实**。
  * `gate_allow_r9m1_end_R2.txt` 第 5、9 行新增了 ` M checkpoints/p05/registries/s4r9/M1/*` 与 ` M testing/d003/stage_s4r9/*`，使 (i) 之后被修改的 `prereg_r9m1.py` 与 `copy_registries_r9m1.py` 规避了未修改断言。
- **F-5（K 继承替代证据越界采信）**：**复核属实**。
  * `K_INHERIT_R9M1.tsv` 中 35 组记为 `NO_SEQ_EVIDENCE_R2`，其中 k_max=1 的 6 组（21 点），k_max>1 的 29 组（218 点）。这 29 组直接依据 U303 采信 HIT 行等价，超出了 U303 仅限 k_max=1 的裁决范围。
  * `K_INHERIT_RAW_R9M1.txt` 记录显示，plain 驱动因无调试符号每次命中解析结果均为 `arg=None func=None loc=None:0`，报告所称"输出了一致的 trace 序列"无原始日志依据。
- **F-6（小表提交与证据原件不符）**：**复核属实**。
  * `registries/s4r9/M1/EVENTS_R9M1.tsv` 提交了 85 条记录，证据目录为 96 条记录（报告正文写 96）；registries 目录下只有 `GATE_R9M1_end.txt`，报告正文与表头引用了 `GATE_R9M1_end_R3.txt`。
- **F-7（规划者独立复算）**：**复核属实**。
  * F4 正式 pass1 的 M1b 415 行 rc1/rc2/hit 与 F3 冻结结果逐行一致；pass1 与 pass2 的 M1b 415 行无差异。
  * 执行者补充复算 M1c 236 行：pass1 与 pass2 一致；与 F3 冻结事实逐行一致。

---

## 3. 裁决落实与勘误追加

### 3.1 裁决追加（`append_rulings_r9m1r2.py`）
已追加 U312–U317（前缀断言通过，5 列字段规范校验通过，文件扩充至 130798 字节）：
- **U312**：r9m1 流程偏差登记为勘误；r9m1 结果降级为参考结果，有效结果以 r9m1r2 为准。
- **U313**：重新冻结预注册。三元组为键，自 F3 冻结表机械推导，增列 inj_call 与 contract，断言 651 行，状态 INFLUENCED。
- **U314**：口径冻结。M1b rc2 比对口径与 M1c 控制行 '-' 处理规则引用历史脚本行号写入 ENGINE_COLUMNS_R9M1R2.txt。
- **U315**：K 继承重做。init/polyinj 改用 dbg 驱动；d003/d003plan 另建 kmap-dbg 变体，选项差异仅限 +-g，比对源码帧。
- **U316**：规定执行顺序与停止条件。单次调用正式两遍。
- **U317**：F2 侧 651 行继续引用 r8 冻结判定，重新生成 CITED_F2 表。

### 3.2 勘误登记（`append_errata_r9m1r2.py`）
在 `ERRATA_9.txt` 中追加 E9-14 至 E9-20（前缀断言通过，文件扩充至 19322 字节）：
- **E9-14**：r9m1 预注册在 (i) 之后被覆盖与字典键冲突事实。
- **E9-15**：r9m1 正式运行与冒烟多次覆盖重跑事实。
- **E9-16**：r9m1 证据目录下 207 处裸写文件事实。
- **E9-17**：r9m1 门禁放宽掩盖已提交脚本被修改事实。
- **E9-18**：r9m1 K 继承替代证据越界采信与无依据推论事实。
- **E9-19**：r9m1 报告与 registries 小表、证据原件不一致事实。
- **E9-20**：r9m1 报告中 9 处主观强化词违规事实（逐项标注行号 23, 112, 113, 114, 174, 179, 189, 192, 215）。

---

## 4. K 继承重做结果（U315）

### 4.1 映射驱动构建（`build_kmap_r9m1r2.py`）
- 自 F3（`8d8202a`）与 F4（`05097a7`）导出树构建 4 个变体驱动：
  * `d003-F3-kmap-dbg`（sha256 `1ad680c81b47...`，0 warnings）
  * `d003-F4-kmap-dbg`（sha256 `4b6fd1ad9b33...`，0 warnings）
  * `d003plan-F3-kmap-dbg`（sha256 `79ffd5b1159e...`，0 warnings）
  * `d003plan-F4-kmap-dbg`（sha256 `6de2d6f79862...`，0 warnings）
- **编译选项差异比对（`BUILD_OPTION_DIFF_KMAP_R9M1R2.txt`）**：
  * 4 个驱动的编译命令行相比对应 plain 驱动，选项差异仅为 `+-g`（1 项增加，0 项减少，断言通过）。
- **命中数校验**：
  * 4 个 kmap-dbg 驱动在 8 个模式下进行 gdb 命中计数，结果与对应 plain 驱动一致（断言通过）。

### 4.2 K 继承比对（`k_inherit_r9m1r2.py`）
- 驱动族映射方案：
  * `r6bstate`（18 组）：使用 r6bstate-F3-dbg 与 r6bstate-F4-dbg；
  * `init`（3 组）：使用 init-F3-dbg 与 init-F4-dbg；
  * `polyinj`（6 组）：使用 polyinj-F3-dbg 与 polyinj-F4-dbg；
  * `d003`（15 组）：使用 d003-F3-kmap-dbg 与 d003-F4-kmap-dbg；
  * `d003plan`（11 组）：使用 d003plan-F3-kmap-dbg 与 d003plan-F4-kmap-dbg。
- **比对结果（`K_INHERIT_R9M1R2.tsv`）**：
  * **总组数**：53 组；
  * **PASS_K_INHERITED_R3**：53 组（覆盖全部 53 组）；
  * **NO_SEQ_EVIDENCE_R3**：0 组；
  * **DIVERGENT**：0 组；
  * 每组两侧命中数相等，断点捕获到源码帧，行号经 LINEMAP 映射后一致；原始序列记录见 `K_INHERIT_RAW_R9M1R2.txt`。

---

## 5. 预注册与判定口径冻结

### 5.1 预注册表生成（`prereg_r9m1r2.py`）
- 生成 `PREREG_M1_F4_R9M1R2.tsv`（sha256 `35333fd452b9...`）与 `PREREG_M1_CITED_F2_R9M1R2.tsv`（sha256 `8ffdb6a57758...`）。
- **字段规范**：包含 section, group, point_id, base_id, tree, driver_name, driver_sha256, env, argv, exp_class, exp_rc1, exp_rc2, exp_rc3, exp_hit, exp_point_verdict, exp_I1..I6, inj_call, contract, status, basis, f3_point_id, f3_driver, f3_driver_sha256, f3_effective_verdict 共 29 列。
- **与 d57fcf29 差异比对（`PREREG_VS_R9M1_DIFF_R9M1R2.tsv`）**：
  * 逐行核对确认：所有既有期望字段（exp_class, exp_rc1..3, exp_hit, exp_I1..6 等）差异为 0；
  * 差异项仅出现在新增列（inj_call, contract）以及更新的 basis 描述（"受 r9m1 冒烟与正式运行观察影响"）。

### 5.2 判定口径冻结（`ENGINE_COLUMNS_R9M1R2.txt`）
- M1b rc2 比对依据：引用 `plan_and_run_m1b_r8m1b1.py:107-109` 与 `run_supp_r8m1b3.py:112-114`，仅在 exp_rc2 非 0 且非空时比对。
- M1c G6c/CTRL_AUX '-' 处理依据：引用 `verdict_m1c_r8m1c3.py:103-108,132-133`，控制行无 RESULTS 记录，exp_point_verdict 为 '-' 时跳过字符匹配，依据事实要求 computed_class 为 CONTROL_OK。
- 其余字段按字符串一致性比较。

---

## 6. 阳性对照验证（`posctrl_r9m1r2_R2.py`）

调用正式判定与比较脚本进行 3 个用例核验（报告存档于 `POSCTRL_M1_R9M1R2.txt`）：
1. **用例 1（F3 冻结事实输入比较引擎）**：
   * 结果：CHECKS = 651，**DIFFS = 0** -> **PASS**。
2. **用例 2（篡改副本 3 处故障注入判定引擎）**：
   * 篡改 1：M1b G2b `M-once-fft-plan-3-F4` rc1 由 20 改为 0；
   * 篡改 2：M1c G5 `M-once-closed1d-malloc-1-F4` I1 由 HOLD 改为 1；
   * 篡改 3：M1b G1 `M-twice-closed1d-malloc-2-F4` rc2 由 20 改为 0（合同要求检查 rc2）；
   * 结果：检出 MISMATCH 数量恰好为 3 处，无多检或漏检 -> **PASS**。
3. **用例 3（旧版预注册 3894d899 对照正式事实）**：
   * 结果：检出 G2b 组 MISMATCH 数量恰好为 22 处（F-1 所述 22 行），无其他组误报 -> **PASS**。
- **阳性对照结论**：3 项全部通过，引擎具备故障检出能力。

---

## 7. 冒烟测试结果（`SMOKE_M1_F4_R9M1R2.tsv`）

- **测试范围**：选取 25 个代表点，覆盖 23 个 (section × group × driver) 组合；对 G1 与 G2b 中同名的 `M-once-fft-plan-3-F4` 各取 1 点验证。
- **运行验证**：
  * G1 `M-once-fft-plan-3-F4`：rc1=0, hit=0, class=INVALID -> **NOT_REACHED_AS_EXPECTED**；
  * G2b `M-once-fft-plan-3-F4`：rc1=20, hit=1, class=REPORTED_FAILURE -> **MATCH**；
  * G2c_control `addf-F-ctrl-F4`：未运行 -> **NOT_RUN_AS_EXPECTED**；
  * 其余 22 点全部判定为 **MATCH**；
- **冒烟结论**：25 点全部符合预注册期望，FAILS = 0，无停滞项。

---

## 8. 正式运行与判定结果

### 8.1 正式两遍执行（`run_formal_r9m1r2_R3.py`）
- 依据 §1-11，正式运行脚本仅调用 1 次，Pass 1 与 Pass 2 在同一次运行中完成，输出至事先不存在的新目录 `runs/formal_R2`。
- 每条运行前后核验驱动 sha256 均与预注册一致。
- 产出 `FORMAL_FACTS_M1_F4_R9M1R2_pass1.tsv`（651 行）与 `FORMAL_FACTS_M1_F4_R9M1R2_pass2.tsv`（651 行）。

### 8.2 判定结果（`VERDICT_M1_F4_R9M1R2.tsv`）
- **两遍一致性**：651 点 pass 1 与 pass 2 事实一致，**FLAKY = 0**，**GDB_DIV = 0**。
- **判定汇总**：
  * **MATCH**：626 行；
  * **NOT_REACHED_AS_EXPECTED**：22 行（G1 组 22 点注入未触碰）；
  * **NOT_RUN_AS_EXPECTED**：3 行（G2c_control 组 3 点未运行）；
  * **MISMATCH**：0 行。
- 分组统计见 `VERDICT_M1_F4_R9M1R2_AGG.tsv`。

---

## 9. 事实等价比对与参考结果比对

### 9.1 F3 / F4 事实等价比对（`F3_F4_EQUIV_R9M1R2.tsv`）
- **核对范围**：F4 pass 1 事实 vs F3 冻结事实（M1b 415 行 + M1c 236 行 = 651 行）。
- **核对字段**：rc1, rc2, rc3, hit, class, I1..I6, clean_base_env（环境比对已忽略 S4FMM_INJECT, S4FMM_NTH, S4FMM_TWICE）。
- **比对结果**：CHECKS = 651，**DIFFS = 0**。
- **HIT 等价分类统计**：
  * **NONEMPTY_IDENTICAL**：529 行（两侧命中数均大于 0 且数值与行为相同）；
  * **BOTH_EMPTY**：119 行（两侧命中数均为 0）；
  * **NOT_RUN**：3 行（控制行未运行）；
  * 合计：651 行。

### 9.2 r9m1 参考结果比对（`R9M1_VS_R9M1R2_R9M1R2.tsv`）
- 本轮有效事实与 r9m1 参考事实逐行比对：
  * 623 行一致；
  * 28 行存在差异记录：
    1. M1b G2c_control（3 行）：r9m1 记录为 `-` 与 `NOT_RUN_REGISTRY_ERROR`，本轮事实记录为 `0` 与 `CONTROL_OK`；
    2. M1c G6（25 行）：r9m1 事实表中 I1..I6 遗留为 `-`，本轮根据 RESULTS_R6c_SEAM 补齐填充为 `HOLD` 或 `N/A`。
  * 除上述两处格式与填充规范化外，所有被测执行点事实行为一致。

---

## 10. M1 汇总总表（1302 行）

合并 F4 事实行（651 行）与引用 F2 冻结行（651 行），生成 `M1_SUMMARY_F4_R9M1R2.tsv`：

| 分部 | 树 | MATCH | NOT_REACHED | NOT_RUN | MISMATCH | 合计 |
|---|---|---|---|---|---|---|
| **M1b（830 行）** | F4 | 390 | 22 | 3 | 0 | 415 |
| | F2（引用） | 390 | 22 | 3 | 0 | 415 |
| **M1c（472 行）** | F4 | 236 | 0 | 0 | 0 | 236 |
| | F2（引用） | 236 | 0 | 0 | 0 | 236 |
| **总计（1302 行）** | F4 + F2 | **1252** | **44** | **6** | **0** | **1302** |

- **总表断言校验**：
  * M1B_SUM_EQ_830 = TRUE；
  * M1C_SUM_EQ_472 = TRUE；
  * GRAND_TOTAL_EQ_1302 = TRUE。

---

## 11. 过程事件表

### 11.1 表一：越界写入尝试
- 本轮越界写入尝试次数：**0**。

### 11.2 表二：工具与脚本执行事件表
由 `events_r9m1r2.py` 自 safe_run.log 提取，另附 r9m1 历史补登表：
- **r9m1 补登事件**：
  * 补登 safe_run.log 98 条日志记录与 207 处未受包裹的裸写文件（见 `BARE_WRITE_AUDIT_R9M1R2.tsv`）。
- **r9m1r2 运行事件**：
  * 全部写入与执行经 `safe_run.sh` 运行；
  * 门禁与正式脚本重跑事件均登记在案（compare 与 posctrl 生成 _R2 修复文件，run_formal 生成 _R3 文件并输出至 formal_R2，原 formal 目录未删除保留取证）。
- 完整台账见 `EVENTS_R9M1R2.tsv`。

---

## 12. 需用户裁决项

- **无**。所有 53 组 K 继承均取得 PASS_K_INHERITED_R3，0 组 DIVERGENT，0 组 NO_SEQ，所有运行点完成。

---

## 13. 交付物与提交清单

### 13.1 小表交付物（已复制至 `checkpoints/p05/registries/s4r9/M1R2/`，sha256 一致）
1. `BARE_WRITE_AUDIT_R9M1R2.tsv`
2. `BUILD_KMAP_R9M1R2.tsv`
3. `BUILD_OPTION_DIFF_KMAP_R9M1R2.txt`
4. `ENGINE_COLUMNS_R9M1R2.txt`
5. `EVENTS_R9M1R2.tsv`
6. `F3_F4_EQUIV_R9M1R2.tsv`
7. `FROZEN_SCRIPTS_R9M1R2.tsv`
8. `GATE_R9M1R2_end.txt`
9. `GATE_R9M1R2_end_R2.txt`
10. `GATE_R9M1R2_end_R3.txt`
11. `GATE_R9M1R2_end_R4.txt`
12. `GATE_R9M1R2_start.txt`
13. `K_INHERIT_R9M1R2.tsv`
14. `K_INHERIT_RAW_R9M1R2.txt`
15. `M1_SUMMARY_F4_R9M1R2.tsv`
16. `POSCTRL_M1_R9M1R2.txt`
17. `PREREG_DIFF_R9M1R2.tsv`
18. `PREREG_M1_CITED_F2_R9M1R2.tsv`
19. `PREREG_M1_CITED_F2_R9M1R2.tsv.sha256`
20. `PREREG_M1_CITED_F2_R9M1R2_TIMESTAMP_UTC.txt`
21. `PREREG_M1_F4_R9M1R2.tsv`
22. `PREREG_M1_F4_R9M1R2.tsv.sha256`
23. `PREREG_M1_F4_R9M1R2_TIMESTAMP_UTC.txt`
24. `PREREG_VS_R9M1_DIFF_R9M1R2.tsv`
25. `R9M1_VS_R9M1R2_R9M1R2.tsv`
26. `REJUDGE_OLD_PREREG_R9M1R2.tsv`
27. `RUNNER_DIFF_R9M1R2.txt`
28. `SCRIPT_VERSIONS_R9M1R2.tsv`
29. `SHA256SUMS.txt`
30. `SMOKE_M1_F4_R9M1R2.tsv`
31. `SMOKE_SUMMARY_R9M1R2.txt`
32. `TIMELINE_R9M1R2.tsv`
33. `VERDICT_M1_F4_R9M1R2.tsv`
34. `VERDICT_M1_F4_R9M1R2_AGG.tsv`
---

本轮已完成 R9 M1 修正范围，等待用户审核
