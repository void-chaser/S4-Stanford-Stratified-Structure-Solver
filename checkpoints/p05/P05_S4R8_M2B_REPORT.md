# P05-S4 R8 M2b（r8m2b）执行报告：执行链修正 + 真实冒烟 + win:64 诊断 + M2 正式两遍运行

> 轮次标识：`r8m2b`（P05-S4 R8 M2b）  
> 开工基线 HEAD：`e57a2f38705e0c385eeab175a3c6a7442cab84fc`  
> 冻结被测树：F3（`6cff923a02baf19e01966b2339755cbf3a5deeef`）；M2-10 树 B（`37a82e8`，`1d738e64…`）  
> 判定器 sha256：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`  
> 证据目录：`checkpoints/p05/evidence/p05-s4r8/m2b/`  
> 小表提交目录：`checkpoints/p05/registries/s4r8/M2/r8m2b/`  
> 规范约束：严格遵循 `AGENTS.md` 与本任务书。不宣布任何阶段完成或签收。

---

## 1. 审核发现 A1–A8 的核实结果与处置

本轮在开工后首先对任务书 §4 指出的 8 项审核发现进行了全面源码核实与实测验证，结果记录于 `$EV/AUDIT_R8_M2b.tsv`：

| 编号 | 涉及文件与位置 | 核实结果 | 处置方案 |
|---|---|---|---|
| **A1** | `facts_m2_r8m2a4.py:90-105` | **VERIFIED**：经最小脚本测试 `gdb -batch` 跑 `/bin/sh -c 'exit 20'`（见 `a1_verify.txt`），gdb 默认退出码恒为 0，程序自身 rc 仅作为八进制打印在 `gdb.log`（`exited with code 024`）。原 facts 仅读 `exitcode.txt` 导致 dbg 行 rc/信号恒为 0。 | 按 U256 成对运行：(a) gdb 下产出 `gdb.log` 与 dump；(b) 不挂 gdb 产出 `stdout/stderr/exitcode`。rc/信号取自 (b)，并从 (a) 解析八进制退出码/信号交叉核对。任何不一致判定为 `GDB_DIVERGENT`。 |
| **A2** | `run_m2_r8m2a4.py:119-123`; `state_judge_m2_r8m2a4.py:466-471` | **VERIFIED**：运行器计划未定义 `gdb.log` 文件名（仅 stdout/stderr），而状态分析器首要查找 `gdb.log`，导致分析器必然全报 `UNJUDGED`。 | 新运行器 `run_m2_r8m2b.py` 将 (a) 的输出严格落盘为 `$EV/run/pass<n>/<pid>/gdb.log`，dump 写入同一目录，使原状态分析器 `state_judge_m2_r8m2a4.py` 无需修改直接可用。 |
| **A3** | `run_m2_r8m2a4.py:131-134`; `PREREG_M2_EFFECTIVE_R8_M2a4.tsv:23-53` | **VERIFIED**：预注册 `san_options` 中含字面量 `$EV`，运行器仅替换 `{pass}` 与 `{point_id}`，未展开 `$EV`，导致日志路径落空。 | 新运行器将 `$EV` 严格展开为绝对路径，并断言计划命令与环境变量中不含任何 `$` 字符。明确 ASAN/UBSAN 仅在有报告时生成日志，不作为存在性门禁。 |
| **A4** | `PREREG_M2_EFFECTIVE_R8_M2a4.tsv:151`; `COMPLETENESS_R8_M2a4.tsv:151` | **VERIFIED**：M2-10 登记 gdb 脚本 sha 为 `bbab8579…`（来自生成器硬编码），而仓库中 `m210_b_r8m2a2_R2.gdb`（提交 `c66b7d2`）实际 sha 为 `d1fc5498…`。身份核对必然失败，原 COMPLETENESS 表却误登 PASS。 | 按 U254 处置：预注册 v3 身份列更正为真实 sha `d1fc5498…`（非 exp 列），追加 ERRATA E8-104。 |
| **A5** | `verdict_m2_r8m2a4.py:211-215` | **VERIFIED**：r8m2a4 判定器在冻结后添加了针对 `M2-07-CTRL-vl-ng1-F3` 的硬编码特判，同时容纳 `CONTROL_OK` 与 `INVALID`，违背判定器冻结纪律。 | 按 U255 处置：删除判定器中的单点特判代码；预注册 v3 为该点新设 `class_rule=NATIVE_FAIL_CONTROL`，严格要求 rc1=20、rc2=20、信号0、hit=0、classify==INVALID；exp_class 原值不改。追加 ERRATA E8-105。 |
| **A6** | `ERRATA_APPEND_R8_M2a4.txt:5,8`; `ERRATA_8.txt:590,593` | **VERIFIED**：r8m2a4 提交附件误写 sha 为 `d917b3e2…` 与 `becf0ab5…`，与实际有效值 `ee46fecf…` 与 `89f00f0e…` 不符。 | 追加 ERRATA E8-106 予以更正澄清，原条目与历史附件不改。 |
| **A7** | `verdict_m2_r8m2a4.py:200-240`; `state_judge_m2_r8m2a4.py:460-500` | **VERIFIED**：verdict 未断言 `exp_hit1`，state_judge 未断言 `fail_layer1`。 | 新判定器 `verdict_m2_r8m2b.py` 严格断言 `exp_hit1`（与 facts 中 `hit1` 比较）和 `fail_layer1`（与 state 表中 `failing_layer` 比较）。 |
| **A8** | `facts_m2_r8m2a4.py:80-110` | **VERIFIED**：事实提取器未解析 gdb 日志中的 `M210_HIT` 断点行。 | 新事实提取器解析 `M210_HIT: Simulation_ComputeLayerModes line <N> returns 20` 行号与次数并登记为 `m210_hits`；`BASELINE_ONLY_RULE` 要求 rc1=20、信号0且至少命中一个 return 20 断点。 |

---

## 2. 执行链 v3 各脚本与装置

执行链脚本全部采用 `r8m2b` 后缀新增，历史脚本保持只读不变：

| 脚本 / 装置 | 路径 | sha256 | 相对 r8m2a4 的 diff 摘要 |
|---|---|---|---|
| 运行器 | `testing/d003/stage_s4/run_m2_r8m2b.py` | `0e326bfd05a415ff64ec8fe7ae262bf64db424f469fe91e77d079495bca2249e` | 支持 `--dry-run` 与 `--execute`；执行前核对驱动与 gdb 脚本 sha（IDENTITY_FAIL 拒绝运行）；清除继承的 `FMM_*`、`S4FMM_*`、`ASAN_*`、`UBSAN_*`；展开 `$EV` 绝对路径并断言无 `$`；按 U256 成对执行 dbg 任务（(a) gdb -> `gdb.log`，(b) nogdb -> `stdout/stderr/exitcode`）；输出目录非空拒绝覆盖。 |
| 事实提取器 | `testing/d003/stage_s4/facts_m2_r8m2b.py` | `cb3ee64c5d519b59620576359f4fbb4e5a31a980562f039a8c1760c441584db8` | rc 和信号严格取自 run (b)；解析 run (a) gdb 日志中八进制退出码（`exited with code 024` $\to$ 20）及信号进行交叉核对；核对 (a) 与 (b) 的 rc1/rc2/rc3/hit 一致性，不一致置 `gdb_divergent=1`；增加 `hit1`（总 hit 减 hit2）、`m210_hits` 提取。 |
| 判定器 | `testing/d003/stage_s4/verdict_m2_r8m2b.py` | `6c10e137107bf4572242137936166ca0b29ce459bc7631da70ff83bfdf356860` | 实现严格互斥优先级：`GDB_DIVERGENT > MISMATCH > FLAKY > UNJUDGED_MISSING > UNJUDGED_BY_DESIGN > MATCH`；实现 U255 `NATIVE_FAIL_CONTROL` 无单点特判代码；实现 U257 参照点比对；实现 A7 `exp_hit1` 与 `fail_layer1` 断言；严格合计断言。 |
| 状态分析器 | `testing/d003/stage_s4/state_judge_m2_r8m2a4.py` | `89f00f0ef91b927066bad059b58073a47cbf34594d65a35ee7bdddb576a6ff1f` | **原样复用**（冒烟证明其完美识别 `run_m2_r8m2b.py` 生成的 `gdb.log` 与 dump 格式，Gate 3 产生 0 UNJUDGED，无需重建）。 |
| 阳性对照 | `testing/d003/stage_s4/posctrl_m2_r8m2b.py` | `901fdb8eebe87b3e18a050df887754d92415d97746816a75ff87bb7b6ec711a1` | 包含原 19 例基线并新增 8 项专用用例（S1–S8），共 27 例。全部经 safe_run 调用正式脚本运行。 |
| 核心判定器 | `testing/d003/judge_d003.py` | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` | 冻结装置，保持逐字节不变。 |

---

## 3. 预注册 v3、SANREF 表与 WIN64 表

本轮生成并冻结三张预注册表，均记录 sha256 与 UTC 时间戳，并写入差异明细表 `PREREG_DIFF_R8_M2b.tsv`：

| 预注册表 | 行数 | sha256 | UTC 冻结时间 | `exp_*` 改动数 |
|---|---|---|---|---|
| **有效预注册 v3** (`PREREG_M2_EFFECTIVE_R8_M2b.tsv`) | 150 | `8f58484abfef9663684b87ab0e32f372080cd2851a7e9d7268cc9976d9c40ba5` | `2026-10-16T06:50:52Z` | **0**（自动断言通过） |
| **非 san 参照表** (`PREREG_M2_SANREF_R8_M2b.tsv`) | 19 | `f5db08d858f64d25f9a6ea27597dee300357eadd343620a19df3ee1b41fc0322` | `2026-10-16T06:50:52Z` | 新建表（状态 `INFLUENCED`） |
| **win:64 诊断增补表** (`PREREG_M2_WIN64_R8_M2b.tsv`) | 5 | `d9951b25358aef3ef86c3881ef0f7810b64d6c9ac9611d1e7e0ada845f65cf68` | `2026-10-16T07:11:53Z` | 新建表（状态 `INFLUENCED`） |

- **有效预注册 v3 允许改动核对**：
  1. `M2-10-01-B`：gdb 脚本 sha 更正为 `d1fc5498…`（U254/E8-104）；
  2. `M2-07-CTRL-vl-ng1-F3`：`class_rule` 更正为 `NATIVE_FAIL_CONTROL`（U255/E8-105）；
  3. M2-03 19 行：`san_ref_point_id` 由 `NO_REF` 映射为 `M2-03-SANREF-*`（U257/E8-108）；
  4. `basis` 列对应说明追加。
  除上述四项外，所有 150 点的全部 `exp_*` 期望值保持绝对不变（差异数为 0）。

---

## 4. 参照驱动复用与证明（U257 / S-D）

依据 U257，M2-03 的 19 个原 `NO_REF` 点需在同环境非 sanitizer 参照驱动下对比。经查证历史构建台账（`DRIVERS_R8.tsv`、`BUILD_R8_M2a2_R3.tsv`、`BUILD_SEAM_DBG_R8_M1a.tsv`、`link_r6b_seam_r8m1.sh`），已有驱动完全满足 U257 条件，直接复用，记录于 `BUILD_SANREF_R8_M2b.tsv`：

1. **G5 组（13 点）参照驱动**：`r6bstate-F3-dbg`
   - 驱动路径：`checkpoints/p05/evidence/p05-s4r8/drivers_r8m1/r6bstate-F3-dbg/driver`
   - 驱动 sha256：`8b269be6e21f7c74fa40a268ed6226e91e481e06000523e8cf0f9942b6e06cdd`
   - 依赖库：F3 `-O0 -g` 库 `56f72c58…`（`build_r8/F3-dbg/build/libS4.a`）
   - 源文件：`driver_r6b_state.cpp`（`db2e7a2e…`）+ `inject_r4_plan.cpp`（`90bf45ce…`）
   - 证明：与 `r6bstate-F3-san`（`BUILD_R8_M2a2_R3.tsv:15`）相比，源文件、宏、4 个 wrap 完全一致，仅去掉了 `-fsanitize=address,undefined -fno-omit-frame-pointer`，复用成立。
2. **G6 组（6 点）参照驱动**：`r6bseam-seamF-F3`
   - 驱动路径：`checkpoints/p05/evidence/p05-s4r8/drivers_r8m1/r6bseam-seamF-F3/driver`
   - 驱动 sha256：`4c882f730c7966f8ff2bead0ec9119ca78969ccb69c635d4c63f0c0ea46ea5f1`
   - 依赖库：F3 seamF `-O0 -g` 库 `16d43d3c…`（`build_r8m1/seam_dbg/seamF-F3/build/libS4.a`）
   - 源文件：`driver_r6b_state.cpp`（`db2e7a2e…`）+ `inject_r4_plan.cpp`（`90bf45ce…`）
   - 证明：库与驱动编译宏含 4 个 seam 宏（`-DS4_TEST_LINEARSOLVE_SEAM` 等），编译为 `-O0 -g`，4 个 wrap 完全一致，无 sanitizer，复用成立。

---

## 5. 合成阳性对照结果（27 例）

阳性对照脚本 `posctrl_m2_r8m2b.py` 严格调用正式执行链脚本，运行结果记录于 `POSCTRL_M2_R8_M2b.txt`，保留全部历史运行原始记录：
- **R1 运行**（`POSCTRL_M2_R8_M2b_R1.txt`）：26 PASS / 1 FAIL。Case A 因未在 facts 提取时合并 SANREF 参照点，导致 19 个 san 点报告 `UNJUDGED_MISSING`。
- **R2 运行**（`POSCTRL_M2_R8_M2b_R2.txt` / `POSCTRL_M2_R8_M2b.txt`）：**27 PASS / 0 FAIL**（100% 通过）。

| 用例编号 | 类别与目的 | 注入特征与测试条件 | 判定器预期分类 | 实测结果 |
|---|---|---|---|---|
| **Case A** | 基线全通 | 150 点标准合成输出（参照点匹配） | 150 MATCH | **PASS**（MATCH=150/150） |
| **Case B** | 灵敏度 | M2-01-01-F3 篡改 `rc1=0`（两遍一致，无 divergence） | MISMATCH (exp_rc1) | **PASS** |
| **Case C** | 灵敏度 | M2-01-01-F3 篡改 `rc2=20`（两遍一致，无 divergence） | MISMATCH (exp_rc2) | **PASS** |
| **Case D** | 灵敏度 | M2-01-01-F3 篡改 `signal=11`（SIGSEGV） | MISMATCH (exp_signal) | **PASS** |
| **Case E** | 灵敏度 | M2-01-01-F3 篡改 `hit=0` | MISMATCH (exp_hit) | **PASS** |
| **Case F** | 双失败 | M2-04-01-F3 篡改 `hit2=0` | MISMATCH (exp_hit2) | **PASS** |
| **Case F2** | 双失败 | M2-04-01-F3 出现 `S4FMM INJECT2 INVALID` | MISMATCH (exp_inject2_invalid) | **PASS** |
| **Case F3** | 双失败 | M2-04-01-F3 出现 `S4FMM INJECT2 SUPPRESSED` | MISMATCH (exp_inject2_suppressed) | **PASS** |
| **Case F4** | 双失败恢复 | M2-04-01-F3 篡改恢复调用 `rc3=20` | MISMATCH (exp_rc3) | **PASS** |
| **Case G** | 状态缺失 | M2-01-01-F3 缺失 `gdb.log` | UNJUDGED (UNJUDGED_MISSING) | **PASS** |
| **Case H** | 结构缺失 | M2-01-01-F3 pass 1 缺失数据目录 | SCHEMA_ERROR (MISSING_IN_PASS1) | **PASS** |
| **Case I** | 树哈希不符 | M2-01-01-F3 facts 篡改 tree=B | SCHEMA_ERROR (TREE_MISMATCH_PASS1) | **PASS** |
| **Case J** | 输出比较 | M2-01-01-F3 恢复调用 `call2.txt` 数据篡改 | MISMATCH (I6=VIOLATED) | **PASS** |
| **Case L** | 跨遍不稳定 | M2-01-01-F3 仅 pass 2 篡改 `rc1=0` | FLAKY (rc1) | **PASS** |
| **Case M** | 基线规则 | M2-10-01-B 正常命中 line 2362 断点且 rc=20 | MATCH (BASELINE_ONLY_RULE) | **PASS** |
| **Case K** | 内存安全 | M2-03-G5-01-F3 注入 ASAN 报错行 | MISMATCH (exp_san) | **PASS** |
| **Case P** | 参照比对 | M2-03-REP-INIT-01-F3 篡改 `rc1=0` | MISMATCH (san_ref_rc1) | **PASS** |
| **Case Q** | 设计未决 | 构造 `san_ref_point_id=NO_REF` | UNJUDGED (UNJUDGED_BY_DESIGN) | **PASS** |
| **Case R** | 汇总断言 | 构造 149 点预注册输入 | 触发 FATAL 退出 (Total!=150) | **PASS** |
| **Case S1** | GDB退出码 | gdb 退出码 0，日志写 `exited with code 024` | facts 正确解析 rc=20, gdb_divergent=0 | **PASS** |
| **Case S2** | 信号崩溃 | 不挂 gdb 的运行退出码 139（SIGSEGV） | classify 为 CRASH -> MISMATCH | **PASS** |
| **Case S3** | GDB发散 | gdb 日志 rc1=0 与 nogdb rc1=20 不一致 | GDB_DIVERGENT (优先级高于MISMATCH) | **PASS** |
| **Case S4** | 路径安全 | 构造 `san_options` 含未展开 `$OTHER_VAR` | 运行器 dry-run 拒绝运行退出 | **PASS** |
| **Case S5** | 原生失败对照 | `M2-07-CTRL-vl-ng1-F3` 在 `rc1=0` 时 | MISMATCH (native_fail_rc1) | **PASS** |
| **Case S6** | M2-10断点 | M2-10-01-B 日志中缺失 `M210_HIT` 断点行 | MISMATCH (baseline_m210_hits_none) | **PASS** |
| **Case S7** | 分项命中 | `M2-04-01-F3` 篡改 `hit1=2`（exp=1） | MISMATCH (exp_hit1) | **PASS** |
| **Case S8** | 参照返回码 | `M2-03-REP-INIT-01-F3` 参照点 rc1 改变 | MISMATCH (san_ref_rc1) | **PASS** |

---

## 6. 真实冒烟（S-E）门禁与观察记录

在正式运行前，选取涵盖每个“项 × 驱动 × 是否对照组”的 24 点代表性子集（名单见 `SMOKE_SUBSET_R8_M2b.tsv`）在 `$EV/smoke/` 进行了两遍真实物理执行：
- **5 项冒烟门禁全部一次性通过**：
  1. **文件完整性**：48 次运行（24 点 × 2 passes）全部产出预期的 `stdout.txt`、`stderr.txt`、`exitcode.txt` 及 dbg 行的 `gdb.log`（缺失数 0，PASS）；
  2. **事实无缺失**：两遍事实表中无任何 `MISSING`（MISSING 数 0，PASS）；
  3. **状态分析有效**：状态分析器 `state_judge_m2_r8m2a4.py` 成功解析全部私有状态，在 `exp_I*=HOLD` 的行中无任何 `UNJUDGED`（UNJUDGED 数 0，PASS）；
  4. **计划无 `$`**：生成的命令计划中没有任何未展开的 `$` 字符（0 处，PASS）；
  5. **身份无失败**：驱动与 gdb 脚本 sha256 核对无一失败（0 处，PASS）。

- **冒烟观察差异（严格记录于 `SMOKE_R8_M2b.tsv`，0 改动 `exp_*`）**：
  冒烟中 19 点 MATCH，5 点观察到与期望不同（只记录，不改期望）：
  - `M2-01-01-F3` 与 `M2-03-REP-INIT-01-F3`：实测 `rc1=1`（期望 20）。此为 F3 树上已知 `-3 -> 1` 返回码归一化现象（E8-77 / STATE.md 行 55）。
  - `M2-03-G6-01-F3` 与 `M2-03-SANREF-G6-01-F3`：实测 `rc1=0, hit=0`（INVALID，期望 20）。
  - `M2-06-01-F3`：实测 `rc1=20`（REPORTED_FAILURE，期望 0 SILENT_SWALLOW）。

---

## 7. win:64 诊断结论与索引确认（U259 / S-F）

针对 M1 遗留的 5 个 `win:64` 测试点，按 `WIN64_DIAG_PLAN_R8_M2a4.md` 在专用环境进行了带有断点跟踪的诊断运行，结果记录于 `WIN64_DIAG_R8_M2b.tsv`：

| 诊断点 | 驱动与环境 | 64th malloc 命中调用 | 触发时的快照区间 | 确认的索引方案 | 诊断结论 |
|---|---|---|---|---|---|
| `M2-01-13-F3` | `polyinj-F3-dbg`; fft NG=5; win:64 | **call 1** | `r6_probe(0)` 与 `r6_probe(1)` 之间 | `inj_call=1, k_before=0, k_fail=1, k_preretry=2, k_retry=3, retry_call=2` | **INDEX_CONFIRMED** |
| `M2-01-15-F3` | `polyinj-F3-dbg`; fft NG=9; win:64 | **call 1** | `r6_probe(0)` 与 `r6_probe(1)` 之间 | `inj_call=1, k_before=0, k_fail=1, k_preretry=2, k_retry=3, retry_call=2` | **INDEX_CONFIRMED** |
| `M2-01-17-F3` | `polyinj-F3-dbg`; kottke NG=1; win:64 | **call 1** | `r6_probe(0)` 与 `r6_probe(1)` 之间 | `inj_call=1, k_before=0, k_fail=1, k_preretry=2, k_retry=3, retry_call=2` | **INDEX_CONFIRMED** |
| `M2-01-19-F3` | `polyinj-F3-dbg`; kottke NG=5; win:64 | **call 1** | `r6_probe(0)` 与 `r6_probe(1)` 之间 | `inj_call=1, k_before=0, k_fail=1, k_preretry=2, k_retry=3, retry_call=2` | **INDEX_CONFIRMED** |
| `M2-01-21-F3` | `polyinj-F3-dbg`; kottke NG=9; win:64 | **call 1** | `r6_probe(0)` 与 `r6_probe(1)` 之间 | `inj_call=1, k_before=0, k_fail=1, k_preretry=2, k_retry=3, retry_call=2` | **INDEX_CONFIRMED** |

- **诊断物理依据**：
  GDB 日志明确记录：在 `r6_probe(0)` 执行后，程序进入 `call1` 的 `Simulation_ComputeLayerModes(layer 1)`；在多边形离散化窗口内连续发生 64 次 `malloc`，在第 64 次精准触发 `S4FMM HIT real malloc failure`，`ComputeLayerModes` 在 line 1894 拦截并返回 `rc=20`；随后触发 `r6_probe(1)`。所有 5 个点的第 64 次分配全部发生在 `call1`，未进入 `call2`。
- **预注册冻结**：
  依据确认的索引，生成 `PREREG_M2_WIN64_R8_M2b.tsv`（5 行，sha256: `d9951b25…`），期望值取自 M1 F3 观察值（`ADD22-B-13/15/17/19/21-F3`：`exp_rc1=20, exp_rc2=0, exp_hit=1, exp_class=REPORTED_FAILURE`），状态标注为 `INFLUENCED`。

---

## 8. 正式运行结果与分布统计（S-G）

正式两遍运行严格按计划执行：先完整跑完 pass 1 的全部 174 行，再完整跑完 pass 2 的全部 174 行。未发生中断，未重跑覆盖任何数据目录。依次提取事实、状态分析和判定：

### 8.1 三张表合计与断言汇总（`SUMMARY_R8_M2b.txt`）

| 测试矩阵 | 评定行数 | MATCH | MISMATCH | FLAKY | GDB_DIVERGENT | UNJUDGED | 严密合计断言 |
|---|---|---|---|---|---|---|---|
| **主表矩阵 (Main)** | 150 | 129 | 21 | 0 | 0 | 0 | **150 == 150 PASS** |
| **非 san 参照表 (SanRef)** | 19 | 14 | 5 | 0 | 0 | 0 | **19 == 19 PASS** |
| **win:64 表 (Win64)** | 5 | 5 | 0 | 0 | 0 | 0 | **5 == 5 PASS** |
| **综合总计 (Grand Total)** | **174** | **148** | **26** | **0** | **0** | **0** | **174 == 174 PASS** |

### 8.2 分项分布明细

```tsv
item	MATCH	MISMATCH	FLAKY	GDB_DIVERGENT	UNJUDGED_DESIGN	UNJUDGED_MISSING	TOTAL
M2-01	11	6	0	0	0	0	17
M2-01-CTRL	9	0	0	0	0	0	9
M2-03	20	11	0	0	0	0	31
M2-04	2	0	0	0	0	0	2
M2-04-CTRL	2	0	0	0	0	0	2
M2-05	4	0	0	0	0	0	4
M2-05-CTRL	4	0	0	0	0	0	4
M2-06	0	1	0	0	0	0	1
M2-06-CTRL	1	0	0	0	0	0	1
M2-07-CTRL	69	3	0	0	0	0	72
M2-07	9	0	0	0	0	0	9
M2-09-CTRL	2	0	0	0	0	0	2
M2-10	1	0	0	0	0	0	1
M2-03-SANREF	14	5	0	0	0	0	19
```

- **关键专项判定事实**：
  1. **M2-10 基线**：在树 B 上实测两遍均命中 `Simulation_ComputeLayerModes` line 2362 断点（`m210_hits=2362`），`rc1=20`，信号 0，按 `BASELINE_ONLY_RULE` 严密判定为 **MATCH**（非修复证据，依据 U247/U254）。
  2. **M2-07 vl 原生失败对照**：`M2-07-CTRL-vl-ng1-F3` 两遍实测均为 `rc1=20, rc2=20, sig=0, hit=0, c=INVALID`，按 U255 `NATIVE_FAIL_CONTROL` 判定为 **MATCH**。
  3. **M2-04 双目标失败恢复**：`M2-04-01-F3` 与 `M2-04-02-F3` 两遍实测均为 `rc1=20, rc2=20, rc3=0, hit=2, hit1=1, hit2=1, fail_layer1=1`，私有状态 I1–I6 均保持 HOLD，严密判定为 **MATCH 2/2**。
  4. **win:64 补充验证**：诊断确认的 5 个 win:64 点（M2-01-13/15/17/19/21）两遍实测全部 `rc1=20, rc2=0, sig=0, hit=1`，私有状态 I1–I6 全部 HOLD，严密判定为 **MATCH 5/5**。

### 8.3 红点清单（26 点，`RED_POINTS_R8_M2b.tsv`）

所有 26 个红点两遍实测结果绝对一致（FLAKY = 0），无任何 GDB 发散（GDB_DIVERGENT = 0）：

1. **M2-01 修复行返回码跨树差异（6 点）**：
   - `M2-01-01-F3` 至 `M2-01-06-F3`：实测 `rc1=1, rc2=0, sig=0, hit=1`（期望 `exp_rc1=20`）。
   - 机理说明：此为 S3R4 修复在 F3 上产生的已知返回码归一化现象（原 -3 $\to$ 1，见 E8-77 / STATE.md 行 55）。
2. **M2-03 G6 组及对应 SANREF 未命中（10 点）**：
   - 主表 `M2-03-G6-01-F3`, `G6-03`, `G6-04`, `G6-05`, `G6-06`（5 点）及其参照表对应点 `M2-03-SANREF-G6-01-F3`, `03`, `04`, `05`, `06`（5 点）：实测 `rc1=0, rc2=0, sig=0, hit=0`（判定为 `INVALID`，期望 `REPORTED_FAILURE`）。
3. **M2-03 对应 M2-01 点同源返回码差异（3 点）**：
   - `M2-03-REP-INIT-01-F3` 至 `03`：实测 `rc1=1`（期望 20）。与 M2-01-01..03 表现完全一致。
4. **M2-03 init:7/8 内存检测异常（3 点）**：
   - `M2-03-REP-INIT-04-F3` 至 `06`：实测 `rc=1, san_reports=2`（期望 `exp_san=0`）。
5. **M2-06 张量路径吞噬（1 点）**：
   - `M2-06-01-F3`：实测 `rc1=20, class=REPORTED_FAILURE`（期望 `exp_class=SILENT_SWALLOW, exp_rc1=0`）。
6. **M2-07 对照组高阶网格原生失败（3 点）**：
   - `M2-07-CTRL-vl-ng2-F3`, `ng3`, `ng4`：实测 `rc1=20, rc2=20, c=INVALID`（期望 `CONTROL_OK`）。

---

## 9. 完整性评估（S-H）

完整性表 `COMPLETENESS_R8_M2b.tsv` 基于实际两遍运行结果：

| 口径 | JUDGED（已决） | UNJUDGED_MISSING | UNJUDGED_BY_DESIGN | NOT_RUN_UNRESOLVED | 合计 |
|---|---|---|---|---|---|
| **主表 (Main)** | 150 (129 MATCH + 21 MISMATCH) | 0 | 0 | 0 | **150** |
| **参照表 (SanRef)** | 19 (14 MATCH + 5 MISMATCH) | 0 | 0 | 0 | **19** |
| **win:64 表 (Win64)** | 5 (5 MATCH) | 0 | 0 | 0 | **5** |
| **总计** | **174 (148 MATCH + 26 MISMATCH)** | **0** | **0** | **0** | **174** |

- **断言**：全矩阵 174 点全部达到 `JUDGED` 闭环，未决与遗漏项为 0（BLOCKER = 0）。

---

## 10. 违规披露表与门禁快照

### 10.1 表一：越界写入尝试表（命令自身写仓库外路径）
*无。本轮没有任何命令尝试写入仓库外部路径。*

### 10.2 表二：工具 / 脚本事件表
| 轮次 | 事件类型 | 命令 / 操作 | 是否落盘 | 处置说明 |
|---|---|---|---|---|
| r8m2b | 框架溢出 | grep 工具检索大输出 | 是 (`/tmp/dsh-spill-*`) | 属于框架只读机制，单列披露，不属执行者违规 |

### 10.3 门禁快照
- **start 门禁**（`GATE_R8_M2b_start.txt`）：HEAD `e57a2f38…`，`HEAD:S4` F3，判定器 sha256 一致，`/tmp` 条目数 0（sha `e3b0c442…`），`FAILS=0`。
- **end 门禁**（`GATE_R8_M2b_end.txt`）：`/tmp` 条目数 0（sha `e3b0c442…`），工作区仅包含允许产物，`FAILS=0`。

---

## 11. 收尾提交与状态

本轮已完成 r8m2b 范围，等待用户审核。不得宣布阶段完成。
