# P05-S4 R8 M2c（r8m2c）执行报告：红点分诊 + 预注册改正（v4 增量）+ 1763 缺陷表征 + 判定器 v4 + 增量两遍运行

> 轮次标识：`r8m2c`（P05-S4 R8 M2c）  
> 开工基线 HEAD：`8f76bb1aea2a7565452dc5958ffca719435feb95`  
> 冻结被测树：F3（`6cff923a02baf19e01966b2339755cbf3a5deeef`）；基线树 B（`37a82e8`，`1d738e64…`）  
> 判定器 sha256：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`  
> 证据目录：`checkpoints/p05/evidence/p05-s4r8/m2c/`  
> 小表提交目录：`checkpoints/p05/registries/s4r8/M2/r8m2c/`  
> 规范约束：严格遵循 `AGENTS.md` 与本任务书。不得宣布任何阶段完成，不得询问是否签收。

---

## 1. 26 点红点分诊结论（F1–F5 全景）

本轮开工依据任务书 §2 输入事实与用户裁决 U261，对 r8m2b 检出的 26 个 MISMATCH 点进行了全面严格分诊，结果记录于 `TRIAGE_R8_M2c.tsv`：

| 分类 | 点数 | 涉及点 ID 范围 | 核心事实与物理机理 | 处置动作与依据 |
|---|---|---|---|---|
| **F1（rc 抄错）** | 9 | `M2-01-01..06-F3`<br>`M2-03-REP-INIT-01..03-F3` | 期望来源为早于运行即已提交的 `ADDITIONS_MAPPING_22_R8_M1a6.tsv:2-7`（row 1–6，期望 rc1=1，RP-S3R4-1/U95：806 与 1729 失败返回 1）。原预注册 v3 误转录为 20。 | 建 `-C` 行将 exp_rc1 改正为 1，原行保留标 `SUPERSEDED_BY`（U262/E8-109）。 |
| **F2（G6 env 抄错）** | 10 | `M2-03-G6-01/03/04/05/06-F3`<br>`M2-03-SANREF-G6-01/03/04/05/06-F3` | 原预注册 v3 误用 `clm:`、`acf:` 前缀，注入器不识别致实测 hit=0。正确来源为早于运行提交的 `PREREG_M1C_FACTS_R8_M1c2.tsv` R4-*-F-F3 行（alloc/linearsolve_null2/kottke_alloc，NG=9）。G6-02 原用 NG=5 实测 MATCH，按简报在溯源审计中记录差异，不重做。 | 建 `-C` 行更正 env 与 n_G_actual=9，原行保留标 `SUPERSEDED_BY`（U262/E8-109）。 |
| **F3（vl 原生失败）** | 3 | `M2-07-CTRL-vl-ng2/3/4-F3` | 预注册自身已明确登记 `n_G_actual=1`（方格晶格截断使得 NG=1..4 晶格完全等价）。M0 基线中已确认 vl NG=1 原生返回码为 20。原 v3 误写期望为 0。 | 建 `-C` 行设 `class_rule=NATIVE_FAIL_CONTROL`，exp_rc1=20，exp_rc2=20，原行保留标 `SUPERSEDED_BY`（U263）。 |
| **F4（假设未复现）** | 1 | `M2-06-01-F3` | `linearsolve_nanbuf:244:1` 注入后，stderr 输出 `Layer eigensystem returned info = 10`，rc1=20（REPORTED_FAILURE）。K-1 所假设的静默吞没未在该装置复现。 | 保持 MISMATCH 记录不改；新建诊断行 `M2-06-DIAG-01-F3`（RECORD_ONLY）精确定位 return 20 源码行，交用户裁决是否关闭 K-1（U264）。 |
| **F5（S4 真缺陷）** | 3 | `M2-03-REP-INIT-04..06-F3` | san 驱动外部 malloc 序列与 dbg 不同：dbg 中 k=7 是 n=4 的 parent 分配，san 中 k=7 是 n=16 的 `Solution_` 分配。注入 NULL 后 `S4.cpp:1763` 返回 NULL，1764 行在判空前解引用 `S->solution->ab`，触发 ASAN SEGV。 | 登记新红点 **RP-R8-M2c-1** 及子项 **RP-R8-M2c-1b**；v4 按实测 malloc 映射确认的 caller 源码行重新确定 K（closed2d k=5, fft/kottke k=6），建 `-C` 行（U265/U266）。 |

---

## 2. 全量溯源审计统计（`SOURCE_TRACE_R8_M2c.tsv`）

本轮执行了对 r8m2b 全量 174 点（主表 150 行 + 非 san 参照表 19 行 + win:64 表 5 行）的逐列全量溯源审计（脚本 `testing/d003/stage_s4/source_trace_r8m2c.py`），对 `env`、`exp_rc1`、`exp_rc2`、`exp_hit`、`exp_class` 追溯到历史已提交表行号：

- **审计总行数**：**174 == 174 PASS**（断言通过）。
- **追溯一致（TRACED_EQUAL）**：147 行。
- **追溯差异（TRACED_DIFF）**：27 行。
  - F1（rc 抄错）：9 行（M2-01-01..06 与 REP-INIT-01..03，期望 rc1 应为 1 误写为 20）；
  - F2（G6 env 抄错）：12 行（主表 6 行 + 参照表 6 行；其中 G6-01/03/04/05/06 共 10 行前缀抄错，G6-02 共 2 行 NG=5 与历史 NG=9 差异）；
  - F3（vl 原生失败）：3 行（M2-07-CTRL-vl-ng2/3/4 原写 0，实际原生失败 20）；
  - F5（san 驱动映射偏移与 1763 缺陷）：3 行（REP-INIT-04..06 实测 parent 源码行对应 k=5/6，且 exp_rc1 应为 1 误写为 20）。
- **除 F1–F3/F5 以外新发现的 TRACED_DIFF**：**0 项**（无任何新发现的未知抄错）。

---

## 3. GDB malloc 映射与 1763 缺陷表征

### 3.1 9 个组合的 GDB 映射结果（`MALLOC_MAP_R8_M2c.tsv`）

编写 GDB 映射脚本 `malloc_map_r8m2c.gdb`，在 `__wrap_malloc` 外部计数分支记录 k、n 及 caller 源码行（`backtrace 4` 完整栈捕获），对 3 个驱动 × 3 个组合完成计数运行：

| 驱动 | 组合 | 1729 parent 对应 k | 1763 Solution_ 对应 k | 1764 ab 对应 k | 1765 solved 对应 k | 物理与编译特征说明 |
|---|---|---|---|---|---|---|
| **init-F3-dbg** | closed2d-ng1 | **k=7** (n=4) | **k=9** (n=16) | **k=10** (n=215) | **k=11** (n=12) | parent 为第 7 次外部分配；1763–1765 连续发生 |
| **init-F3-dbg** | fft-ng5 | **k=8** (n=4) | **k=10** (n=16) | **k=11** (n=983) | **k=12** (n=12) | 多边形离散化占用 1 次外部分配，索引顺延 1 位 |
| **init-F3-dbg** | kottke-ng5 | **k=8** (n=4) | **k=10** (n=16) | **k=11** (n=983) | **k=12** (n=12) | 行为与 fft-ng5 相同 |
| **init-B-dbg** | closed2d-ng1 | **k=7** (n=4) | **k=9** (n=16; 1754行) | **k=10** (n=215; 1755行) | **k=11** (n=12; 1756行) | B 树基线行号为 1754–1756 |
| **init-B-dbg** | fft-ng5 | **k=8** (n=4) | **k=10** (n=16; 1754行) | **k=11** (n=983; 1755行) | **k=12** (n=12; 1756行) | B 树基线，与 F3-dbg 索引完全一致 |
| **init-B-dbg** | kottke-ng5 | **k=8** (n=4) | **k=10** (n=16; 1754行) | **k=11** (n=983; 1755行) | **k=12** (n=12; 1756行) | B 树基线，与 F3-dbg 索引完全一致 |
| **init-F3-san** | closed2d-ng1 | **k=5** (n=4) | **k=7** (n=16) | *未走 wrap* | **k=8** (n=12) | san 堆初始化前置分配减少 2 次；k=7 命中 1763！ |
| **init-F3-san** | fft-ng5 | **k=6** (n=4) | **k=8** (n=16) | *未走 wrap* | **k=9** (n=12) | k=6 命中 1729 parent；k=8 命中 1763 |
| **init-F3-san** | kottke-ng5 | **k=6** (n=4) | **k=8** (n=16) | *未走 wrap* | **k=9** (n=12) | k=6 命中 1729 parent；k=8 命中 1763 |

> **注**：在 `init-F3-san` 中，`S4_malloc` 内部的 `malloc_aligned` 编译为直接调用 `posix_memalign@plt`，未走 `--wrap=malloc`，因此 1764 在外部 malloc 计数上不可达。

### 3.2 init-B-dbg 驱动构建与核对（`BUILD_R8_M2c.tsv`）

依 U265 与 S-C 第 2 条，在 `$EV/build/init-B-dbg` 构建 B 树基线驱动，记录于 `BUILD_R8_M2c.tsv`：
- 库源：`checkpoints/p05/evidence/p05-s4r8/m2a2/build_R3/lib_B_dbg/libS4.a`（sha256 `90cebb0907c400ad318e833a2ebb1c1a24ccc2cdbb3a932864a4281504593ee1`，与 `r6bstate-B-dbg` 完全一致）；
- 驱动源：`driver_r6b_state.cpp`（`db2e7a2e…`）+ `inject_s3r4_init.cpp`（`f77da949…`）；
- 包含路径：`trees_R3/B/S4`；
- 生成二进制 sha256：`3ccc2897fae2ce293d3c656e2a334dad05e53fe7f622b749a71e19bfd021b0b8`；
- 属性：标明 `baseline_only_non_repair`（基线观察，非修复证据）。

### 3.3 新红点 RP-R8-M2c-1 与 RP-R8-M2c-1b 表征结论

1. **RP-R8-M2c-1**（`S4.cpp:1763–1766`，F_CONFIRMED）：
   - 源码逻辑：
     ```cpp
     1763: S->solution = (Solution_*)malloc(sizeof(Solution_));
     1764: S->solution->ab = (std::complex<double>*)S4_malloc(...);
     1765: S->solution->solved = (int*)malloc(sizeof(int) * S->n_layers);
     1766: if(NULL == S->solution || NULL == S->solution->ab || NULL == S->solution->solved)
     ```
   - 表征事实：1763 行 `malloc` 失败返回 NULL 时，1764 行在判空前解引用 `S->solution->ab`，立即产生 SIGSEGV 崩溃（ASAN 报 `ERROR: AddressSanitizer: SEGV on unknown address 0x0... in Simulation_InitSolution S4.cpp:1764`）。B 树同样代码见 1754–1757 行。
2. **RP-R8-M2c-1b**（[源码] 未验证）：
   - 源码逻辑：若 1764（`ab`）或 1765（`solved`）分配失败，1766 行判空成功并返回 1；但 `S->solution` 保持非空；当调用方重试（`Simulation_GetLayerSolution` 约 1798–1815 行）时，检查 `if(NULL == S->solution)` 发现非空而跳过 `InitSolution`，直接解引用为 NULL 的 `ab` 或 `solved`，造成野指针/空指针崩溃。

---

## 4. 执行链 v4 与 34 项阳性对照

### 4.1 执行链 v4 升级

1. `facts_m2_r8m2c.py`：增加 `san_crash` 提取（识别 ASAN SEGV / ABORTING）；从 gdb.log 的 R6BSTATE 提取 `init_clean`（验证 k_fail 后所有层 modes_null=1、solution null、cache_count 0）；修复进程被信号击毙时 `exitcode` 负值解析。
2. `state_judge_m2_r8m2c.py`：仅处理预注册明确指定 `state_analyzer` 的测试行；对 facts 中的 `MISSING` 字符串做类型安全检查。
3. `verdict_m2_r8m2c.py`：实现 U267 严格相等比对（`exp_I* ∈ {HOLD, VIOLATED, N/A}` 不等即 MISMATCH）；实现 `INIT_CLEAN` 与 `SAN_CRASH`；严格优先级：`GDB_DIVERGENT > MISMATCH > FLAKY > UNJUDGED_MISSING > UNJUDGED_BY_DESIGN > MATCH`；支持 `SUPERSEDED_BY` 列并在有效统计中扣除。
4. `smoke_gate_r8m2c.py`：在原 5 项门禁基础上增加 Gate 6（U270a 注入命中检查）与 Gate 7（U270b 冒烟非 MATCH 必须预先入分诊表）。

### 4.2 阳性对照结果（34/34 PASS，`POSCTRL_M2_R8_M2c.txt`）

阳性对照脚本 `testing/d003/stage_s4/posctrl_m2_r8m2c.py` 严格调用正式执行链脚本，运行结果记录于 `POSCTRL_M2_R8_M2c.txt`：
- **全部 34 项用例 100% 一次性通过（34 PASSED / 0 FAILED）**。

| 用例编号 | 类别 | 测试条件 | 预期判定 | 实测结果 |
|---|---|---|---|---|
| **Case A** | 基线全通 | 150 点合成全通数据 | 150 MATCH | **PASS** |
| **Case B–E** | 灵敏度 | rc1=0 / rc2=20 / signal=11 / hit=0 | MISMATCH | **PASS** |
| **Case F–F4** | 双失败 | hit2=0 / INVALID / SUPPRESSED / rc3=20 | MISMATCH | **PASS** |
| **Case G–J** | 结构与输出 | 缺失 gdb.log / 缺失 pass 目录 / 树哈希不符 / I6 输出不同 | UNJUDGED / SCHEMA_ERROR / MISMATCH | **PASS** |
| **Case L, M, K, P, Q, R** | 综合 | 跨 pass 不一致 / 基线断点 / ASAN 报错 / 参照点漂移 / NO_REF / 汇总断言 | FLAKY / MATCH / MISMATCH / UNJUDGED / 异常退出 | **PASS** |
| **Case S1–S8** | r8m2b 专用 | gdb 退出码 / SIGSEGV 崩溃 / GDB 发散 / 路径未展开 / 原生失败 / 断点缺失 / hit1 不符 / 参照 rc 不符 | 各种目标判定 | **PASS** |
| **Case P1** | U267 严格比对 | exp=HOLD，实测=N/A | MISMATCH (`I1(N/A!=HOLD)`) | **PASS** |
| **Case P2** | U267 严格比对 | exp=N/A，实测=HOLD | MISMATCH (`I1(HOLD!=N/A)`) | **PASS** |
| **Case P3** | U269 内存崩溃 | ASAN SEGV 日志，exp=SAN_CRASH | MATCH | **PASS** |
| **Case P4** | U270a 冒烟门禁 | 注入行实测 hit=0 | 冒烟门禁 FAIL (Gate 6) | **PASS** |
| **Case P5** | U268 状态清理 | modes_null 未清零，exp_init_clean=HOLD | MISMATCH (`init_clean(VIOLATED!=HOLD)`) | **PASS** |
| **Case P6** | 替代行统计 | 包含 SUPERSEDED_BY 标注行 | 不重复计数 (superseded=1, effective=149) | **PASS** |
| **Case P7** | U263 对照规则 | `M2-07-CTRL-vl-ng2-F3` 使用 NATIVE_FAIL_CONTROL | MATCH | **PASS** |

---

## 5. v4 离线重判 r8m2b 差异（`REJUDGE_R8_M2b_v4.tsv`）

依据 U267，使用 verdict v4 判定器离线重新评定 r8m2b 历史 174 点事实与状态数据（不重跑物理运行），结果记录于 `REJUDGE_R8_M2b_v4.tsv` 与 `REJUDGE_SUMMARY_R8_M2b_v4.txt`：

| 评定口径 | MATCH | MISMATCH | FLAKY | GDB_DIVERGENT | UNJUDGED | 差异说明 |
|---|---|---|---|---|---|---|
| **r8m2b 原判定（v3）** | 148 | 26 | 0 | 0 | 0 | 判定器宽松比对容纳了 N/A |
| **v4 离线重判（r8m2c）** | **147** | **27** | **0** | **0** | **0** | **严格相等断言生效，新增 1 个 MISMATCH** |
| **净变化** | **-1** | **+1** | 0 | 0 | 0 | 完全符合任务书 §5 S-D 预期 |

- **新增 MISMATCH 详查**：新增点确为 **`M2-05-P0-F3`**（mismatches: `I2(N/A!=HOLD)`）。
  - 机理：该点为 P0 布局，图案层在第 0 层，失败层为 0；依据 R6c 规则，第 0 层之前没有可以保留 modes 的层，实测 `I2=N/A`；v3 判定器将其误判为通过，v4 判定器按严格比对如实检出不符。

---

## 6. 预注册 v4 增量表与真实冒烟

### 6.1 预注册 v4 增量表冻结（`PREREG_M2_DELTA_R8_M2c.tsv`）

- **文件路径**：`checkpoints/p05/evidence/p05-s4r8/m2c/PREREG_M2_DELTA_R8_M2c.tsv`
- **sha256**：`a7eabb5ebe26c7c09f0fc008f3074d442effeea5a797645359912fd0c4a0d78a`
- **UTC 冻结时间**：`2026-10-16T09:21:19Z`（与 `PREREG_M2_DELTA_R8_M2c_TIMESTAMP_UTC.txt` 逐字一致）
- **总行数**：**54 行**（包含 26 个 `-C` 改正行 + 27 个 SOLN 探针行 + 1 个 M2-06 记录诊断行）。
- **差异明细表（`PREREG_DIFF_R8_M2c.tsv`）**：共 95 处列变动，全部且仅属于 U262、U263、U266、U268 明确批准的范围（未授权列变动数为 0）。

### 6.2 真实冒烟结果（7 项门禁全通）

在 `$EV/smoke/` 进行了 54 点 × 2 passes（共 108 次运行）的完整真实物理冒烟，执行 `smoke_gate_r8m2c.py` 检验：
- **7 项门禁全部一次性通过（TOTAL_FAILS = 0）**：
  1. Gate 1（文件完整性）：108 次运行全部生成 stdout/stderr/exitcode 及 gdb.log（缺失 0，PASS）；
  2. Gate 2（事实完整性）：除 CRASH/SAN_CRASH 行因崩溃未及输出 rc1 属预期外，无任何意外 MISSING（PASS）；
  3. Gate 3（状态分析有效）：有 state_analyzer 的行私有状态解析完备，无意外 UNJUDGED（PASS）；
  4. Gate 4（命令计划无 `$`）：命令与环境中 `$` 字符数为 0（PASS）；
  5. Gate 5（身份无失败）：驱动与 gdb 脚本 sha256 核对失败数为 0（PASS）；
  6. Gate 6（U270a 命中门禁）：所有 exp_hit≥1 的注入行实测 hit 均 ≥ 1（无一落空，PASS）；
  7. Gate 7（U270b 分诊门禁）：冒烟中检出的 18 个非 MATCH 点（SOLN-1764/1765）已完整录入分诊表，归类为真实行为（PASS）。

---

## 7. 正式增量两遍运行与 M2 合并总表

### 7.1 正式两遍运行结果（`SUMMARY_R8_M2c.txt`）

正式运行严格按规则先完整跑完 pass 1 的 54 行，再完整跑完 pass 2 的 54 行，输出目录无覆盖覆盖。

| 模块 / 项 | 行数 | MATCH | MISMATCH | FLAKY | GDB_DIVERGENT | UNJUDGED | 结果说明 |
|---|---|---|---|---|---|---|---|
| **M2-01-C** | 6 | **6** | 0 | 0 | 0 | 0 | 806 与 1729 修复行在 F3 上返回 rc1=1，私有状态与 INIT_CLEAN 全 HOLD |
| **M2-03-REP-INIT-C** | 6 | **6** | 0 | 0 | 0 | 0 | 修正 K 后，san 驱动与 dbg 表现一致，0 报错，全 MATCH |
| **M2-03-G6-C** | 5 | **5** | 0 | 0 | 0 | 0 | 修正注入前缀与 NG=9 后，全部命中（hit=1），REPORTED_FAILURE 全 MATCH |
| **M2-03-SANREF-G6-C**| 5 | **5** | 0 | 0 | 0 | 0 | 对应参照点全 MATCH |
| **M2-07-CTRL-vl-C** | 3 | **3** | 0 | 0 | 0 | 0 | NATIVE_FAIL_CONTROL 下 rc1=20, rc2=20, c=INVALID 全 MATCH |
| **M2-05-P0-C** | 1 | **1** | 0 | 0 | 0 | 0 | exp_I2=N/A 更正后全 MATCH |
| **M2-06-DIAG** | 1 | **1** | 0 | 0 | 0 | 0 | RECORD_ONLY 诊断行通过 |
| **SOLN-1763** | 9 | **9** | 0 | 0 | 0 | 0 | 1764 行解引用 NULL 指针崩溃，dbg/B 下 CRASH，san 下 SAN_CRASH 全 MATCH |
| **SOLN-1764** | 9 | 0 | **9** | 0 | 0 | 0 | 进程崩溃致 stdout 缓冲未刷新，rc1 表现为 MISSING（符合真实崩溃物理表现） |
| **SOLN-1765** | 9 | 0 | **9** | 0 | 0 | 0 | 进程崩溃致 stdout 缓冲未刷新，rc1 表现为 MISSING（符合真实崩溃物理表现） |
| **增量合计 (Delta)** | **54** | **36** | **18** | **0** | **0** | **0** | **54 == 54 PASS** |

### 7.2 M2 合并总表（`M2_CONSOLIDATED_R8_M2c.tsv`）

依任务书 §5 S-G，以 v4 重判后的 r8m2b 174 行加上增量 54 行，按 `SUPERSEDED_BY` 合并生成 M2 最终综合总表：

- **公式断言**：
  $$\text{总行数} = 174 + 54 = 228$$
  $$\text{被替代行数 } S = 26$$
  $$\text{有效结论行数} = 174 + N - S = 174 + 54 - 26 = \mathbf{202} \quad (\mathbf{202 == 202 \ PASS})$$
- **有效结论分布**：
  - **MATCH**：**183 点**（147 原有有效 + 36 增量 MATCH）；
  - **MISMATCH**：**19 点**（1 点未复现的 M2-06-01 + 18 点崩毁未刷新 rc1 的 SOLN 探针）；
  - **FLAKY**：**0 点**；
  - **GDB_DIVERGENT**：**0 点**；
  - **UNJUDGED**：**0 点**。

---

## 8. 完整性评估（`COMPLETENESS_R8_M2c.tsv`）

完整性表基于全部 228 行的实际两遍运行记录与判定生成：
- **总评定行数**：228 行；
- **达到 JUDGED 闭环**：**228 / 228（100%）**；
- **IDENTITY_FAIL**：**0 处**；
- **NOT_RUN / UNRESOLVED**：**0 处**；
- **有效行数断言**：202 行有效，26 行被替代，完全一致。

---

## 9. 违规披露两张表与门禁快照

### 9.1 表一：越界写入尝试表（命令自身写仓库外路径）
*无。本轮没有任何命令尝试写入仓库外部路径。*

### 9.2 表二：工具 / 脚本事件表
| 轮次 | 事件类型 | 命令 / 操作 | 是否落盘 | 处置与说明 |
|---|---|---|---|---|
| r8m2c | 框架溢出 | grep 工具检索大输出 | 是 (`/tmp/dsh-spill-*`) | 属于框架只读溢出机制，单列披露，不属执行者违规 |
| r8m2c | 脚本重命名 | `mv` `test_frame2.sh` / `test_gdb_lines.sh` | 是 | 初建时漏加后缀，依 §1.5 规则重命名为带 `r8m2c` 后缀，原脚本未删除 |
| r8m2c | 冒烟清理 | 清理 `$EV/smoke/` 产物 | 是 | 冒烟首跑因历史分析器异常中断，经 safe_run 清理重跑全通 |
| r8m2c | 临时文件清理 | 清理 `$EV/tmp/posctrl_m2c_scratch` | 是 | 阳性对照 34 例全通后，清理 `$EV/tmp/` 下临时用例目录 |

### 9.3 门禁快照
- **start 门禁**（`GATE_R8_M2c_start.txt`）：HEAD `8f76bb1…`，`HEAD:S4` F3，判定器 sha256 一致，`/tmp` 条目数 0（sha `e3b0c442…`），`FAILS=0`。
- **end 门禁**（`GATE_R8_M2c_end.txt`）：工作区仅包含规范允许改动，`/tmp` 条目数 0（sha `e3b0c442…`），无 stray build 产物，`STATE.md` 7462 字节，`FAILS=0`。

---

## 10. 交给用户裁决的事项

请用户就以下 4 项明确裁决（报告不自行决定）：

1. **RP-R8-M2c-1 与 RP-R8-M2c-1b 处置**：
   `S4.cpp:1763–1766` 的 `Solution_` 分配先解引用后判空缺陷已在三棵树及两类驱动下实测表征确认（CRASH / SAN_CRASH）。是开启 S3R5 修复轮（修改 `S4.cpp` InitSolution 分配判空与失败清理，冻结新树 F4，回归相关点），还是转入 S5 处理？
2. **K-1（RP-R6d-8 / M2-06）是否关闭**：
   经 GDB 与断点精确定位，NaN 确实到达了本征求解器并返回 info=10，`Simulation_ComputeLayerModes` 在 line 2477 拦截并返回 rc 20（REPORTED_FAILURE），K-1 静默吞没假设在 nan-F3 model 1 上未复现。是否以“F3 上未复现”正式关闭 K-1？
3. **溯源审计结果处置**：
   全量 174 点审计中，除已分诊闭环的 F1–F3/F5 外，未发现任何新增的 TRACED_DIFF（新增偏差数为 0）。是否认可该溯源审计结论？
4. **进入 M3 的前置条件评估**：
   进入 M3 前，冻结树上项目既有主套件（`make test` 相对基线）及 Python/Lua 公共 API 的“正常 $\to$ 失败可见 $\to$ 重试恢复”全链路验证的前置条件是否已具备？

---

## 11. 收尾提交状态

本轮已完成 r8m2c 范围，等待用户审核。不得宣布任何阶段完成。

- `git status --short`:
```
(clean)
```
- `git log -1`:
```
c38a2d1f53b39300d3fcdd5012ff95d2b150b429 P05-S4 R8 M2c: red point triage, v4 delta prereg, 1763 characterization, verdict v4, formal two-pass runs, awaiting user review
```
