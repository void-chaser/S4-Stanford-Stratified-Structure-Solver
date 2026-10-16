# P05-S4 R8 M2e（r8m2e）执行报告：-FA 装置纠偏（malloc_aligned 注入）、v5/v6 增量正式两遍、合并总表 v6、事件补披露、F4 回归清单更正

> 轮次标识：`r8m2e`（P05-S4 R8 M2e）  
> 开工基线 HEAD：`be00bf20484d76e84f6ddfcb228032dadd8dcc3c`  
> 冻结被测树：F3（`6cff923a02baf19e01966b2339755cbf3a5deeef`）；基线树 B（`37a82e8`，`1d738e64…`，仅基线，非修复证据）  
> 判定器 sha256：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`  
> 证据目录：`checkpoints/p05/evidence/p05-s4r8/m2e/`  
> 小表提交目录：`checkpoints/p05/registries/s4r8/M2/r8m2e/`  
> 规范约束：严格遵循 `AGENTS.md`。不宣布任何阶段完成，不询问是否签收，不修改 `S4/`。本轮不开始 S3R5，也不开始 M3。  
> 任务书存档：本任务书原文存为 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M2e.md`。注：M2d 任务书原文缺失，待用户提供后补存，不要自行重构。

---

## 1. 开工门禁执行结果（`GATE_R8_M2e_start.txt`）

开工门禁严格执行，各项核验全部通过（`FAILS=0`）：
- **HEAD 校验**：`be00bf20484d76e84f6ddfcb228032dadd8dcc3c`（PASS）；
- **HEAD:S4 校验**：`6cff923a02baf19e01966b2339755cbf3a5deeef`（F3 冻结树，PASS）；
- **判定器 sha256**：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`（PASS）；
- **工作区基线**：开工前 `git status --short` 为空；创建任务书与门禁脚本后与 `gate_allow_r8m2e_start.txt` 6 项完全一致（PASS）；
- **r8m2d 清单比对**：`checkpoints/p05/registries/s4r8/M2/r8m2d/SHA256SUMS.txt` 23 项全数校验通过（PASS）；
- **临时目录快照**：条目数 0，sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`（PASS）；
- **构建残留基线**：扫描记录 `testing/d003/__pycache__` 3 项历史产物，生成 `STRAY_BASELINE_R8_M2e.tsv`（PASS）；
- **门禁结论**：`PYTHON_CHECKS_FAILS=0`，`FAILS=0`，门禁全数通过。

---

## 2. S-B：分诊改正与勘误登记（`TRIAGE_R8_M2e.tsv`、`ERRATA_R8_M2e.txt`、`ERRATA_8.txt` E8-115、`RULINGS.tsv` U276–U282）

依据任务书 §2 输入事实 G-1 至 G-8 及用户裁决 U276：
1. **分诊改正**：
   - 3 个 `-FA` 行在 r8m2d 报 MISMATCH，其物理根因为任务书 U273 依据错误：`S4_FAIL_ALLOC_AT` 在 `S4/S4.cpp:65-71` 受 `!s4_fail_alloc_armed` 保护，仅在 `S4_Simulation_Clone` 作用域被置 1；`driver_r6b_state.cpp` 不调用 Clone，armed 恒为 0；且驱动仅在 `s4fmm_inject_requested()` 为真时打印 HITCOUNT；此外 `-FA` 行原登记的 `k_fail=9` 抄自 1765 行。
   - 依据 U276 将 3 个 `-FA` 行分诊改正为"装置错误（任务书 U273 依据错误：S4_FAIL_ALLOC_AT 仅在 Clone 作用域打开；HITCOUNT 不可观测；k_fail 抄错）"，写入 `TRIAGE_R8_M2e.tsv`。原 `-FA` 行保持原记录，标 `SUPERSEDED_BY`，改由 `-AL` 行替代。
2. **勘误与裁决登记**：
   - 在 `ERRATA_R8_M2e.txt` 编写 `E8-115`，并追加到 `checkpoints/p05/registries/s4r8/ERRATA_8.txt`；
   - 在 `checkpoints/p05/registries/RULINGS.tsv` 追加用户裁决 `U276` 至 `U282`（共 7 条，严格保持 5 列格式，前缀逐字节不变）。

---

## 3. S-C：装置构建与无注入对照实测（`inject_r8m2e_aligned.cpp`、`init-F3-san-AL`、`BUILD_R8_M2e.tsv`、`test_noinj_control_r8m2e.txt`）

1. **注入器实现 (`inject_r8m2e_aligned.cpp`)**：
   - 复制自 `inject_s3r4_init.cpp`，保留全部 transparent wrap 转发（`malloc`, `fft_plan_exec`, `fft_plan_dft_2d`, `S4_malloc`, `Pattern_GetContainmentTree`）；
   - 新增 `__wrap_malloc_aligned` 与 `__real_malloc_aligned`；
   - 新增 `S4FMM_INJECT=aligned:K` 请求解析：第 K 次 `malloc_aligned` 返回 NULL，进程最多命中一次，计入 `n_hits`，并在 stderr 打印 `S4FMM HIT real malloc failure: malloc_aligned <k>, <size> B (hit=<n_hits>)`；
   - 每次调用均在 stderr 记录调用序号、大小、对齐与调用方指针（`S4FMM S4_MALLOC_ALIGNED k=... size=... alignment=... caller=...`）。
2. **驱动构建 (`init-F3-san-AL`)**：
   - 驱动源文件：`driver_r6b_state.cpp`；注入器：`inject_r8m2e_aligned.cpp`；库：现有 F3 san 库（sha256 `2775b9b2c279f51f1be0594c6ea9f635c96e3ba37e9d1638174fa380b45a6986`，不重编）；
   - 编译参数：`-fsanitize=address,undefined -fno-omit-frame-pointer -O0 -g -Wall -Wno-unused-parameter`；
   - 链接参数：`WRAP_INIT` 加 `-Wl,--wrap=malloc_aligned`；
   - 构建脚本 `build_r8m2e.py` 成功产出 `$EV/build/init-F3-san-AL`（sha256 `90f4445330773c13c569bd15a0e1fd5cfa5a735070d4442523bed2b1636841b3`），记录于 `BUILD_R8_M2e.tsv`（rc=0，0 warnings）。
3. **无注入装置对照实测 (`test_noinj_control_r8m2e.py`)**：
   - 对 3 个组合（closed2d-ng1、fft-ng5、kottke-ng5）进行无注入对照运行，输出落盘于 `$EV/probe/test_noinj_control_r8m2e.txt`；
   - 实测结果：3 个组合全部 `rc=0`，无 `S4FMM HIT`，无 `S4FMM HITCOUNT`（因未设 `S4FMM_INJECT`），无任何 ASAN 报告，装置对照全数通过。

---

## 4. S-D：GDB 堆栈映射确定 K 值（`ALIGNED_MAP_R8_M2e.tsv`、`ALIGNED_MAP_RAW_R8_M2e.txt`）

依据 U278 硬规则，K 值由 GDB 断点在 `__wrap_malloc_aligned` 打 `bt 4` 按 caller 源码行严格确定，不得假设：
- 运行脚本：`generate_aligned_map_r8m2e.py`；
- 原始 GDB 日志：落盘于 `$EV/ALIGNED_MAP_RAW_R8_M2e.txt` 及 `$EV/probe/generate_aligned_map_r8m2e.txt`；
- 映射结果汇总表：`ALIGNED_MAP_R8_M2e.tsv`；
- 实测映射结果：
  - **closed2d-ng1**：第 3 次调用（K=3），size=192，帧 #1 为 `S4.cpp:111 S4_malloc`，帧 #2 确认为 `S4.cpp:1764 Simulation_InitSolution`（唯一匹配，size 与 `S4MALLOC_MAP_R8_M2d.tsv` 中 1764 行 192 完全一致）；
  - **fft-ng5**：第 3 次调用（K=3），size=960，帧 #2 确认为 `S4.cpp:1764 Simulation_InitSolution`（唯一匹配，size 与 1764 行 960 完全一致）；
  - **kottke-ng5**：第 3 次调用（K=3），size=960，帧 #2 确认为 `S4.cpp:1764 Simulation_InitSolution`（唯一匹配，size 与 1764 行 960 完全一致）；
- 结论：3 个组合均找到**唯一确定的 1764 调用（K=3）**，且分配 size 完全吻合，未触发硬停止条件。

---

## 5. S-E：预注册 v6 冻结（`PREREG_M2_DELTA_R8_M2e.tsv`、`PREREG_EFFECTIVE_FORMAL_R8_M2e.tsv`）

1. **增量表 v6 (`PREREG_M2_DELTA_R8_M2e.tsv`, 3 行)**：
   - 登记 3 行 `SOLN-1764-<combo>-F3-san-AL`；
   - 驱动：`init-F3-san-AL`；环境：`S4FMM_INJECT=aligned:3`；`k_fail=3`；
   - 期望：`exp_rc1/2/3="-", exp_signal=0, exp_hit=1, exp_class=SAN_CRASH, exp_san=1, exp_crash_call=2, exp_crash_site="S4.cpp:1995", exp_post_call1_solution="-", status=INFLUENCED`；
   - basis 列完整引用前期落盘探针：`ALIGNED_MAP_R8_M2e.tsv:k=3; test_noinj_control_r8m2e.txt; generate_aligned_map_r8m2e.txt; U277, U278, U279; G-3, G-8`；
   - 冻结 sha256：`4af9da60eba58c80ea081543472e11ea0d96e624064b3b6869a4aedf41ca41c3`，时间戳 `2026-10-16T14:59:19Z`。
2. **正式两遍有效预注册表 (`PREREG_EFFECTIVE_FORMAL_R8_M2e.tsv`, 28 行)**：
   - 由 v5 中 25 个非 `-FA` 行原样转录 + 3 个 v6 `-AL` 行组成；
   - 逐行比对证实：25 个非 `-AL` 行与源表 `PREREG_M2_DELTA_R8_M2d.tsv` **逐字节完全一致**；
   - 冻结 sha256：`cff6b38a14589ee34e2ef0d1c26a8bdc9f7288b26f141860a34f407cd65b2e22`，时间戳 `2026-10-16T14:59:19Z`。

---

## 6. S-F：阳性对照实测（`posctrl_m2_r8m2e.py`）

阳性对照调用全部正式脚本（`facts_m2_r8m2e.py`、`state_judge_m2_r8m2e.py`、`verdict_m2_r8m2e.py`、`run_m2_r8m2e.py`、`smoke_gate_r8m2e.py`、`generate_summary_tables_r8m2e.py`）：
- **历史回归**：r8m2d 的 41 项（Case A..R, S1..S8, P1..P7, D1..D7）**全部通过 (41/41 PASS)**；
- **新增断言**：
  - **Case E1**：ASAN 拦截帧（`__interceptor_memset`, `__asan_memset`）被正确识别并跳过，成功提取下层首个 S4 源码帧 `S4.cpp:1995` 且 `crash_call=2`（PASS）；
  - **Case E2**：`S4FMM_INJECT=aligned:3` 注入请求被注入器正确解析并触发 K=3 注入与 HIT 报告（PASS）；
  - **Case E3**：facts 提取器正确解析 stdout 中的 `S4FMM HITCOUNT 1` 为 `hit=1`（PASS）；
  - **Case E4**：合并总表生成器产出新列 `verdict_source ∈ {formal_r8m2b, formal_r8m2c, formal_r8m2e, smoke_r8m2d}`（PASS）；
  - **Case E5**：合并总表有效行中无 `smoke_*` 来源，仅 3 个 SUPERSEDED `-FA` 行保留 `smoke_r8m2d`（PASS）；
  - **Case E6**：合并总表合计断言满足（总行数 259，SUPERSEDED 57，有效行 202）（PASS）；
- **最终结论**：**47 项测试全数通过（47/47 PASS，0 FAIL）**，生成 `POSCTRL_M2_R8_M2e.txt`。

---

## 7. S-G：冒烟测试（3 个 `-AL` 行 × 2 遍）与 7 项门禁检验

在 `$EV/smoke/` 运行 3 个 `-AL` 行 × 2 遍（共 6 次物理运行），结果由 `smoke_gate_r8m2e.py` 检验：
1. **实测判定（`VERDICT_SMOKE.tsv`）**：
   - `SOLN-1764-closed2d-ng1-F3-san-AL`：**MATCH**（实测 san_crash=1, crash_call=2, crash_site=S4.cpp:1995, hit=1）；
   - `SOLN-1764-fft-ng5-F3-san-AL`：**MATCH**（实测 san_crash=1, crash_call=2, crash_site=S4.cpp:1995, hit=1）；
   - `SOLN-1764-kottke-ng5-F3-san-AL`：**MATCH**（实测 san_crash=1, crash_call=2, crash_site=S4.cpp:1995, hit=1）；
2. **7 项门禁核验结果**：
   - Gate 1（文件完整性）：PASS（missing=0）；
   - Gate 2（事实完整性）：PASS（missing_rc=0）；
   - Gate 3（状态分析有效性）：PASS（unjudged=0）；
   - Gate 4（命令计划展开无 `$`）：PASS（count=0）；
   - Gate 5（驱动与脚本标识一致性）：PASS（fails=0）；
   - Gate 6（U270a 命中数校验）：PASS（3/3 均实测 hit=1）；
   - Gate 7（U270b 非 MATCH 分诊门禁）：PASS（0 non-MATCH）；
   - **门禁结论**：`SMOKE_GATE_V3_TOTAL_FAILS=0`，冒烟全数通过，准予进入正式两遍运行。

---

## 8. S-H：正式两遍运行结果（28 行 × 2 遍，`$EV/formal/`）

在全新目录 `$EV/formal/` 运行 28 行 × 2 遍（共 56 次物理运行，按 U256 执行 dbg 成对运行）：
- 产出文件：`COMMAND_PLAN_FORMAL_R8_M2e.tsv`、`FACTS_pass1.tsv`、`FACTS_pass2.tsv`、`STATE_pass1.tsv`、`STATE_pass2.tsv`、`STATE_SUMMARY_R8_M2e.txt`、`VERDICT_R8_M2e.tsv`、`SUMMARY_R8_M2e.txt`；
- **判定分布（`VERDICT_R8_M2e.tsv`）**：
  - **表征吻合（MATCH）**：**28 点（28/28，100%）**！
    - `M2-06-01-F3-C`：**MATCH**（实测 rc1=20，REPORTED_FAILURE，U274 确认）；
    - `SOLN-1763-*`（9 点，含 6 dbg + 3 san）：**全部 MATCH**（实测：调用 1 崩于 `S4.cpp:1764`，B 为 1755）；
    - `SOLN-1764-*-dbg-C`（6 点，含 F3-dbg 3 点 + B-dbg 3 点）：**全部 MATCH**（实测：调用 1 返回 1 且 post_call1_solution=NONNULL；调用 2 重试触发崩于 `S4.cpp:1995`，B 为 1986）；
    - `SOLN-1764-*-F3-san-AL`（3 点）：**全部 MATCH**（实测：malloc_aligned 注入命中，san_crash=1，调用 2 重试崩于 `S4.cpp:1995`）；
    - `SOLN-1765-*`（9 点，含 6 dbg + 3 san）：**全部 MATCH**（实测：调用 1 返回 1 且 post_call1_solution=NONNULL；调用 2 重试崩于 `S4.cpp:2021`，B 为 2012）；
  - **异常计数**：`FLAKY = 0`，`GDB_DIVERGENT = 0`，`MISMATCH = 0`；
  - 未触发任何硬停止条件。

---

## 9. S-I：M2 合并总表 v6（`M2_CONSOLIDATED_R8_M2e.tsv`）与状态拆解（`M2_F3_STATUS_R8_M2e.tsv`）

基于正式两遍运行结果生成合并总表 v6，严格通过各项数学与逻辑断言：
- **总行数**：$$174 (	ext{r8m2b}) + 54 (	ext{r8m2c}) + 28 (	ext{r8m2d}) + 3 (	ext{r8m2e}) = mathbf{259} quad (mathbf{259 == 259  PASS})$$
- **被替代行数（SUPERSEDED）**：$$mathbf{57}$$
  - 列式说明一（按历史轮次）：$$26 (	ext{r8m2b 在 r8m2c 被替代}) + 28 (	ext{r8m2c/b 在 r8m2d 被替代}) + 3 (	ext{r8m2d -FA 在 r8m2e 被替代}) = mathbf{57}$$
  - 列式说明二（按原行归属）：$$27 (	ext{r8m2b 原行}) + 27 (	ext{r8m2c 原行}) + 3 (	ext{r8m2d -FA 原行}) = mathbf{57}$$
- **有效行数（ACTIVE）**：$$	ext{有效行} = 259 - 57 = mathbf{202} quad (mathbf{202 == 202  PASS})$$
- **各类别之和断言**：$$	ext{MATCH } (202) + 	ext{MISMATCH } (0) + 	ext{FLAKY } (0) + 	ext{GDB_DIV } (0) = mathbf{202} quad (mathbf{202 == 202  PASS})$$
- **有效行来源断言**：有效 202 行中 **0 行来自 `smoke_*`**，100% 具备正式两遍运行来源（`formal_r8m2b`: 147 行，`formal_r8m2c`: 27 行，`formal_r8m2e`: 28 行；PASS）。

### 9.1 有效点状态拆解（`M2_F3_STATUS_R8_M2e.tsv`）

将有效 202 个 MATCH 点按性质拆解：
- **健康 MATCH**：**175 点**（正常 API 成功或经设计预期报告失败）；
- **红点表征 MATCH**：**27 点**（全部为确认崩溃缺陷的表征吻合，非功能健康）：
  - `RP-R8-M2c-1` 表征行：9 点（SOLN-1763 崩溃表征）；
  - `RP-R8-M2c-1b` 表征行：18 点（SOLN-1764 dbg 6 点 + SOLN-1764 san-AL 3 点 + SOLN-1765 9 点，重试野指针崩溃表征）。

---

## 10. S-J：F4 回归清单更正（`REGRESSION_PLAN_F4_R8_M2e.tsv`）与 S3R5 收口测试登记

依据任务书 §4 S-J 及 G-7 进行全面更正与登记：
1. **G-7 更正**：9 个 `-B-dbg` 行的驱动更正为 `init-B-dbg`，标为 `BASELINE_ONLY 仅基线，非修复证据`；
2. **1764-san 注入方式更新**：更正为 `init-F4-san-AL` 驱动（采用 `inject_r8m2e_aligned.cpp` 注入器，库替换为 F4 san 库），注入指令为 `S4FMM_INJECT=aligned:K`，并明确注明：**F4 上 K 需重新映射**（经 GDB 确认 caller 源码行后确定，不得假设沿用 F3 的 K=3）；
3. **S3R5 收口测试登记（只登记，不执行）**：
   - `S3R5-CLOSEOUT-MAKE-TEST`：冻结树 F4 上 `make test` 相对未修复基线 B 无新增失败（主套件功能回归）；
   - `S3R5-CLOSEOUT-E2E-API`：经 Python/Lua 公共 API 的"失败→可见报错→重试恢复"全链路端到端恢复测试。

---

## 11. S-K：收尾、红点台账与门禁

1. **红点台账更新 (`RED_POINTS_LEDGER_APPEND_R8_M2e.tsv`)**：
   - `RP-R8-M2c-1`：状态维持 `F_CONFIRMED`，补登正式运行 9 点全 MATCH（SOLN-1763 崩溃表征）；
   - `RP-R8-M2c-1b`：状态维持 `F_CONFIRMED`，补登正式运行 18 点全 MATCH（SOLN-1764 9点 + SOLN-1765 9点，重试崩溃表征）；
   - `K-1`：维持 U274 关闭结论，补登正式运行 `M2-06-01-F3-C` 实测 MATCH。
2. **小表同步与完整性校验**：
   - 复制小型结果表至 `checkpoints/p05/registries/s4r8/M2/r8m2e/`；
   - 生成 registries `SHA256SUMS.txt`（33 项），逐项比对 sha256 100% 一致；
   - 生成证据目录 `checkpoints/p05/evidence/p05-s4r8/m2e/SHA256SUMS.txt`（403 项），覆盖全部非二进制证据文件。
3. **完工门禁 (`GATE_R8_M2e_end.txt`)**：
   - 完工门禁经 `gate_r8m2e.sh end` 执行，各项核验全部通过（`FAILS=0`）。

---

## 12. 违规与事件披露

### 表一：越界写入尝试（命令自身写仓库外路径）
*无（0 处）。*

### 表二：工具框架与运行事件
| 轮次 | 命令/操作 | 是否落盘 | 性质说明 |
|---|---|---|---|
| r8m2d (补) | safe_run.log 第 4、5 行：两个探针 `test_fail_alloc_r8m2d.py`、`test_gdb_arm_r8m2d.py` 运行 | 未落盘 | r8m2d 遗漏，r8m2e 补披露：两探针在预注册冻结前运行，输出未落盘到 probe/ |
| r8m2d (补) | posctrl 运行 4 次（13:37–13:46） | 落盘 | r8m2d 遗漏，r8m2e 补披露：阳性对照反复调试重跑 |
| r8m2d (补) | safe_run.log 第 18 行：`mv generate_m2d_summary_tables.py generate_summary_tables_r8m2d.py` | 文件改名 | r8m2d 遗漏，r8m2e 补披露：因文件名不符合 end 门禁 allow 清单改名 |
| r8m2d (补) | safe_run.log 第 19 行：`rm -f .../GATE_R8_M2d_end.txt` | 删除文件 | r8m2d 遗漏，r8m2e 补披露：改名后删除门禁文件重跑 end 门禁 |
| r8m2d (补) | copy_registries 运行 3 次 | 落盘覆盖 | r8m2d 遗漏，r8m2e 补披露：门禁重跑后重新同步 registries |
| r8m2e | safe_run.log 第 1 行：`gate_r8m2e.sh start` 初次运行报 FAILS=1 | 落盘到 `$EV` | 门禁辅助脚本 `gate_check_r8m2e.py` 换行转义语法错误导致异常退出 |
| r8m2e | safe_run.log 第 2 行：`rm -f .../GATE_R8_M2e_start.txt` | 删除文件 | 清除未通过的 start 门禁文件以备重跑 |
| r8m2e | safe_run.log 第 3 行：`gate_r8m2e.sh start` 再次运行 | 落盘到 `$EV` | 修复语法错误后 start 门禁通过（FAILS=0） |
| r8m2e | safe_run.log 第 5 行：`rm -f .../m2d/STRAY_BASELINE_R8_M2e.tsv` | 删除文件 | 清除第 1 行因 `EV_REL` 初始默认值误写落盘至 m2d 的临时基线文件 |
| r8m2e | safe_run.log 第 6 行：`rm -f .../m2e/GATE_R8_M2e_start.txt` | 删除文件 | 修正 `EV_REL` 为 m2e 后清除旧门禁文件以备重跑 |
| r8m2e | safe_run.log 第 7 行：`gate_r8m2e.sh start` 运行报 FAILS=5 | 落盘到 `$EV` | 中途执行了 S-B 追加 RULINGS/ERRATA 导致工作区非空且基线哈希改变 |
| r8m2e | safe_run.log 第 8 行：`rm -f .../m2e/GATE_R8_M2e_start.txt` | 删除文件 | 清除未通过的门禁文件以备重跑 |
| r8m2e | safe_run.log 第 9 行：`gate_r8m2e.sh start` 运行报 FAILS=1 | 落盘到 `$EV` | 恢复基线后重跑，因第 7 行已生成 STRAY_BASELINE 触发不应存在校验 |
| r8m2e | safe_run.log 第 10 行：`rm -f .../GATE_R8_M2e_start.txt .../STRAY_BASELINE_R8_M2e.tsv` | 删除文件 | 同步删除两项文件彻底复原开工基线状态 |
| r8m2e | safe_run.log 第 11 行：`gate_r8m2e.sh start` 正式通过 | 落盘到 `$EV` | start 门禁全数通过（FAILS=0），基线文件落盘成功 |
| r8m2e | safe_run.log 第 14 行：`generate_aligned_map_r8m2e.py` 初次运行报 rc=2 | 落盘到 `$EV` | GDB 内联脚本中 `\n` 转义问题触发 GDB "Bad format string" 报错 |
| r8m2e | safe_run.log 第 15 行：`generate_aligned_map_r8m2e.py` 修复重跑 | 落盘到 `$EV` | GDB 脚本改为 raw 字符串后执行成功，成功唯一映射 1764 为 K=3 |
| r8m2e | safe_run.log 第 17 行：`posctrl_m2_r8m2e.py` 初次运行 | 未执行 | 命令行漏传必选参数 `--out`，argparse 报错退出 |
| r8m2e | safe_run.log 第 18 行：`posctrl_m2_r8m2e.py --out ...` 运行 | 局部执行 | Case E2 引用全局变量 `EV` 触发 NameError |
| r8m2e | safe_run.log 第 19 行：`rm -rf .../m2d/tmp/posctrl_m2e_scratch` | 删除文件 | 清除第 18 行因参数缺省误写到 m2d/tmp 的 posctrl 临时缓存目录 |
| r8m2e | safe_run.log 第 20 行：`posctrl_m2_r8m2e.py --out ... --ev ...` | 落盘到 `$EV` | 显式传入 `--ev`，posctrl 47/47 项全数通过 |
| r8m2e | safe_run.log 第 24 行：`copy_registries_r8m2e.py` 初次运行 | 落盘覆盖 | 同步小型结果表到 registries 目录 |
| r8m2e | safe_run.log 第 25 行：`gate_r8m2e.sh end` 运行报 FAILS=6 | 落盘到 `$EV` | 因 `tools.read` 默认 limit 截断导致 RULINGS 与 ERRATA 前缀比对失败 |
| r8m2e | safe_run.log 第 26 行：`rm -f .../GATE_R8_M2e_end.txt` | 删除文件 | 清除未通过的 end 门禁文件以备重跑 |
| r8m2e | safe_run.log 第 27 行：`gate_r8m2e.sh end` 修复重跑 | 落盘到 `$EV` | 使用 git cat-file 无截断恢复基线前缀后追加，end 门禁通过（FAILS=0） |
| r8m2e | safe_run.log 第 28 行：`copy_registries_r8m2e.py` 最终运行 | 落盘覆盖 | 同步最终 `GATE_R8_M2e_end.txt` 到 registries 并重新校验 SHA256SUMS |

---

## 13. 需用户裁决事项

本轮执行查阅仓库历史行号与实测数据，所有技术与装置问题已全面闭环。需用户裁决的事项仅为：
1. **是否批准启动 P05-S3R5 修复轮**：
   RP-R8-M2c-1（S4.cpp:1763–1766 立即解引用空指针）与 RP-R8-M2c-1b（S4.cpp:1802 重试野指针崩溃）缺陷机理与崩溃表征已由正式两遍 28 点实测完全证实（维持 F_CONFIRMED）；修复设计规范（`S3R5_DESIGN_R8_M2d.md`）与更正后的 F4 回归清单（`REGRESSION_PLAN_F4_R8_M2e.tsv`）均已就绪。请用户审核是否批准修改 `S4/S4.cpp:1763–1772`，冻结新树 F4 并开展全量回归。

---

本轮已完成 R8 M2e 范围，等待用户审核。
