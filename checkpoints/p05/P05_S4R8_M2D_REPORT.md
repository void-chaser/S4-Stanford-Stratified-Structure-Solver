# P05-S4 R8 M2d（r8m2d）执行报告：红点分诊改正 + 装置升级（bt 24 与事实列提取）+ S4_malloc 映射 + 真实冒烟与停机报告 + S3R5 修复设计规范

> 轮次标识：`r8m2d`（P05-S4 R8 M2d）  
> 开工基线 HEAD：`8f47dc605bfc086ba34aea144bc6157876c2d97d`  
> 冻结被测树：F3（`6cff923a02baf19e01966b2339755cbf3a5deeef`）；基线树 B（`37a82e8`，`1d738e64…`，非修复证据）  
> 判定器 sha256：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`  
> 证据目录：`checkpoints/p05/evidence/p05-s4r8/m2d/`  
> 小表提交目录：`checkpoints/p05/registries/s4r8/M2/r8m2d/`  
> 规范约束：严格遵循 `AGENTS.md`。不宣布任何阶段完成，不询问是否签收，不修改 `S4/`。

---

## 1. 开工门禁执行结果（`GATE_R8_M2d_start.txt`）

开工门禁经 `sh testing/d003/safe_run.sh p05-s4r8/m2d -- sh testing/d003/stage_s4/gate_r8m2d.sh p05-s4r8/m2d GATE_R8_M2d_start.txt start 0 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` 严格执行：
- **HEAD 校验**：`8f47dc605bfc086ba34aea144bc6157876c2d97d`（PASS）；
- **HEAD:S4 校验**：`6cff923a02baf19e01966b2339755cbf3a5deeef`（F3 冻结树，PASS）；
- **判定器 sha256**：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`（PASS）；
- **工作区基线**：开工前 `git status --short` 为空；创建脚本后与 `gate_allow_r8m2d_start.txt` 完全一致（PASS）；
- **r8m2c 清单比对**：`checkpoints/p05/registries/s4r8/M2/r8m2c/SHA256SUMS.txt` 28 项全数校验通过（PASS）；
- **临时目录快照**：条目数 0，sha256 `e3b0c442…`（PASS）；
- **构建残留基线**：扫描记录 `testing/d003/__pycache__` 3 项历史产物，生成 `STRAY_BASELINE_R8_M2d.tsv`（PASS）；
- **门禁结论**：`FAILS=0`，门禁全数通过。

---

## 2. S-A：18 行 SOLN-1764/1765 分诊改正（`TRIAGE_R8_M2d.tsv`，`ERRATA_R8_M2d.txt`）

依据任务书 §2 输入事实 F-1 至 F-7 及用户裁决 U271，全面更正 r8m2c 分诊记录：
1. **预注册错误改正**：`driver_r6b_state.cpp` 使用全缓冲 `std::printf`；当进程被 SIGSEGV 击毙时，stdout 缓冲未及刷新即丢失，rc1/rc2 在进程崩溃场景下客观不可观测（恒为 `MISSING`）。原预注册对预期 `CRASH` / `SAN_CRASH` 行填写数值期望（如 `rc1=1, rc2=0`）属预注册错误，更正为 `exp_rc1="-"`、`exp_rc2="-"`（不判），改由崩溃信号、崩溃调用次序（`exp_crash_call=2`）、崩溃位置（`exp_crash_site`）与调用 1 后方案状态（`exp_post_call1_solution=NONNULL`）进行严格断言。
2. **装置标签错误改正**：`init-F3-san` 驱动在 `S4_HAVE_ASAN` 编译条件下，`numalloc.c` 中 `malloc_aligned` 直接调用 `posix_memalign`，未经过链接器的 `--wrap=malloc` 拦截。因此 `MALLOC_MAP_R8_M2c.tsv` 中 closed2d san k=8、fft/kottke san k=9 实际命中的均为 1765（`solved=NULL`）。原 `SOLN-1764-*-F3-san` 3 行实际注入了 1765，属装置标签错误。按 U273 将原行标为 `SUPERSEDED_BY`，改用 `S4_FAIL_ALLOC_AT` 注入并建 `-FA` 行。
3. **崩溃位置机理纠正**：纠正 r8m2c 分诊表误写的 "S4.cpp:1773 memset(NULL)"。实测堆栈证实：1765 崩于调用 2 中 `S4.cpp:2021 sol->solved`（B 为 2012）；1764 崩于调用 2 中 libc `__memset_avx2_unaligned_erms`（实测帧 #1 确认为 `S4.cpp:1995 memset(pab)`，B 为 1986）。
4. **勘误登记**：以上改正记录于 `TRIAGE_R8_M2d.tsv`，并作为 `E8-114` 记录于 `ERRATA_R8_M2d.txt` 及 `ERRATA_8.txt`。

---

## 3. S-B：装置升级（GDB bt 24、Facts v5、Verdict v5、运行器）

1. **GDB bt 24 装置**：复制 `testing/d003/stage_s4/r6c_state_r8m2a3.gdb` 为 `r6c_state_bt_r8m2d.gdb`，严格仅在 `run` 与 `quit` 之间加入 `bt 24`。`diff -u` 证实仅存在这一处变动（sha256 `e5e92799…`）。
2. **Facts 提取器 v5 (`facts_m2_r8m2d.py`)**：
   - 提取 `crash_call ∈ {1, 2, 3, NONE, UNKNOWN}`：由 GDB `bt 24` 或 ASAN 栈中的 `driver_r6b_state.cpp` 帧行号映射（211 为调用 1，227 为调用 2，238 为调用 3）；
   - 提取 `crash_site`：遍历栈帧，跳过 libc 库函数帧（如 `__memset_avx2_unaligned_erms`），提取首个 `S4/` 源文件帧（`S4.cpp:<line>` 等）；
   - 提取 `post_call1_solution ∈ {NULL, NONNULL, -}`：由 GDB 日志中 `R6BSTATE 1 solution` 解析。
3. **Verdict 评定引擎 v5 (`verdict_m2_r8m2d.py`)**：
   - 支持 `exp="-"` 不判规则；
   - 严格比对 `exp_crash_call`、`exp_crash_site`、`exp_post_call1_solution`；支持 `[源码] 推断` 标注归一化比对；
   - 优先级：`GDB_DIVERGENT > MISMATCH > FLAKY > UNJUDGED_MISSING > UNJUDGED_BY_DESIGN > MATCH`。
4. **运行器升级 (`run_m2_r8m2d.py`)**：计划内展开全部绝对路径，清除 `$` 字面量，驱动搜索路径包含 `m2d/build` 与 `m2c/build`。

---

## 4. S-C：S4_malloc 映射结果（`S4MALLOC_MAP_R8_M2d.tsv`）

编写并在 GDB 下运行 `generate_s4malloc_map_r8m2d.py`，对 3 驱动 × 3 组合（共 9 个配置）下每次 `S4_malloc` 调用的序号 k、申请字节数与 caller 源码行进行完整映射：

| 驱动 | 组合 | `S4.cpp:1764` (ab) 对应 k | caller 源码行与函数 | 判定结论 |
|---|---|---|---|---|
| **init-F3-san** | closed2d-ng1 | **k = 3** (size=192) | `S4/S4.cpp:1764` in `Simulation_InitSolution` | **唯一确定 K=3** |
| **init-F3-san** | fft-ng5 | **k = 3** (size=960) | `S4/S4.cpp:1764` in `Simulation_InitSolution` | **唯一确定 K=3** |
| **init-F3-san** | kottke-ng5 | **k = 3** (size=960) | `S4/S4.cpp:1764` in `Simulation_InitSolution` | **唯一确定 K=3** |
| **init-F3-dbg** | closed2d-ng1 | **k = 3** (size=192) | `S4/S4.cpp:1764` in `Simulation_InitSolution` | 交叉核对一致 (K=3) |
| **init-F3-dbg** | fft-ng5 | **k = 3** (size=960) | `S4/S4.cpp:1764` in `Simulation_InitSolution` | 交叉核对一致 (K=3) |
| **init-F3-dbg** | kottke-ng5 | **k = 3** (size=960) | `S4/S4.cpp:1764` in `Simulation_InitSolution` | 交叉核对一致 (K=3) |
| **init-B-dbg** | closed2d-ng1 | **k = 3** (size=192) | `S4/S4.cpp:1755` in `Simulation_InitSolution` | B 树基线核对一致 (K=3) |
| **init-B-dbg** | fft-ng5 | **k = 3** (size=960) | `S4/S4.cpp:1755` in `Simulation_InitSolution` | B 树基线核对一致 (K=3) |
| **init-B-dbg** | kottke-ng5 | **k = 3** (size=960) | `S4/S4.cpp:1755` in `Simulation_InitSolution` | B 树基线核对一致 (K=3) |

- **结论**：所有驱动与组合下，`S4.cpp:1764`（B 为 1755）均严格且唯一对应第 3 次 `S4_malloc` 分配（前两次分配分别为 `S4.cpp:311` 和 `381` 的晶格网格初始化）。**K=3 唯一确定，未触发猜忌停止条件**。

---

## 5. S-D：预注册 v5 增量表与冻结（`PREREG_M2_DELTA_R8_M2d.tsv`）

依据 S-C 确定的 K=3、任务书 §3 U271–U275，生成并冻结增量预注册表：
- **路径**：`checkpoints/p05/evidence/p05-s4r8/m2d/PREREG_M2_DELTA_R8_M2d.tsv`
- **sha256**：`43db298bf27647a53f5a09764b4efecde4b862d55a05099cb427edcc926151b2`
- **UTC 冻结时间**：`2026-10-16T13:33:30Z`
- **总行数**：**28 行**（M2-06-01-F3-C 1 行 + SOLN-1763-C 9 行 + SOLN-1764 9 行 [含 3 个 -FA] + SOLN-1765-C 9 行）。
- **差异明细（`PREREG_DIFF_R8_M2d.tsv`）**：共记录 207 处列变动，全部且仅属于 U271、U272、U273、U274 授权范围，**未授权列变动数为 0**。

---

## 6. S-E：阳性对照测试（41/41 PASS，`POSCTRL_M2_R8_M2d.txt`）

阳性对照脚本 `testing/d003/stage_s4/posctrl_m2_r8m2d.py` 严格调用正式执行链脚本：
- **回归测试**：r8m2c 的全部 34 项用例 100% 通过（Case A–R, S1–S8, P1–P7）；
- **新增用例**：
  - Case D1（`crash_call` 不符，实测 1 预期 2）：**PASS**（MISMATCH）；
  - Case D2（`crash_site` 不符，实测 2021 预期 1995）：**PASS**（MISMATCH）；
  - Case D3（`exp_rc1="-"` 时 `rc1=MISSING` 不判）：**PASS**（MATCH）；
  - Case D4（`post_call1_solution` 不符，实测 NULL 预期 NONNULL）：**PASS**（MISMATCH）；
  - Case D5（libc 帧跳过并提取首个 S4/ 帧 `S4.cpp:1995`）：**PASS**；
  - Case D6（`SUPERSEDED` 统计与有效点计算）：**PASS**（total=2, sup=1, eff=1）；
  - Case D7（`exp_crash_site` 带 `[源码] 推断` 归一化比对）：**PASS**（MATCH）。
- **总计**：**41 PASSED / 0 FAILED**。

---

## 7. S-F：真实冒烟测试与停止条件触发详查

在 `$EV/smoke/` 进行了 28 行 × 2 遍（共 56 次物理运行），严格按 U256 执行 dbg 成对运行。运行结果由 `smoke_gate_r8m2d.py` 检验：

### 7.1 冒烟判定分布（`VERDICT_SMOKE.tsv`）

- **表征吻合（MATCH）**：**25 点**
  1. `M2-06-01-F3-C`：**MATCH**（实测 rc1=20，REPORTED_FAILURE，U274 确认）；
  2. `SOLN-1763-*`（全部 9 点，含 6 dbg + 3 san）：**全部 MATCH**（表征吻合：调用 1 崩溃，`crash_call=1`，`crash_site=S4.cpp:1764`，B 为 1755）；
  3. `SOLN-1764-*-dbg-C`（6 点，含 F3-dbg 3 点 + B-dbg 3 点）：**全部 MATCH**（表征吻合：调用 1 成功返回 1 且 `post_call1_solution=NONNULL`；调用 2 重试触发崩溃，`crash_call=2`；经 GDB `bt 24` 实测捕获栈帧，跳过 libc `__memset_avx2` 后帧 #1 **确认为 `S4.cpp:1995`（B 为 1986）**！完全吻合事前推断）；
  4. `SOLN-1765-*`（全部 9 点，含 6 dbg + 3 san）：**全部 MATCH**（表征吻合：调用 1 返回 1 且 `post_call1_solution=NONNULL`；调用 2 重试崩溃，`crash_call=2`，`crash_site=S4.cpp:2021`，B 为 2012）。

### 7.2 冒烟未吻合点详查（MISMATCH 3 点）与物理根因

- **涉及点**：
  - `SOLN-1764-closed2d-ng1-F3-san-FA`
  - `SOLN-1764-fft-ng5-F3-san-FA`
  - `SOLN-1764-kottke-ng5-F3-san-FA`
- **实测表现**：进程正常退出（`exitcode=0`），`RC first 0`，未触发崩溃（`san_crash=0`），未触发命中（`hit=0`）。
- **物理根因定位**：
  查阅 `S4/S4.cpp:69–73` 源码：
  ```cpp
  static int s4_fail_alloc_trip(void){
      const long at = s4_fail_alloc_at();
      if(at <= 0 || !s4_fail_alloc_armed){ return 0; }
      return (++s4_fail_alloc_step == at);
  }
  ```
  `s4_fail_alloc_trip` 内部受静态变量 `!s4_fail_alloc_armed` 保护。该变量在全局初始化为 0，并且**仅在 `S4_Simulation_Clone` 的局部作用域内被 `S4FailAllocScopeGuard` 置为 1**。
  在 `driver_r6b_state.cpp`（以及整个场计算和 `Simulation_InitSolution`）流程中，从未调用 `S4_Simulation_Clone`，因此 `s4_fail_alloc_armed` 恒为 0。在原生独立执行时，`S4_FAIL_ALLOC_AT=3` 处于完全惰性状态，根本不会触发注入。
- **门禁检验结论**：
  - Gate 1–5：PASS；
  - **Gate 6（U270a 命中门禁）**：**FAIL**（3 点实测 hit 为 MISSING/0，预期为 1）；
  - **Gate 7（U270b 分诊门禁）**：该 3 点已被录入 `TRIAGE_R8_M2d.tsv`，归类为**「预注册错误（S4.cpp:71 !s4_fail_alloc_armed 限制；驱动未 arm 使 S4_FAIL_ALLOC_AT 惰性不生效）」**。

### 7.3 触发硬停止条件报告

依据任务书 §4 S-F：
> "7 项门禁全过才进入正式运行。冒烟中出现的任何非 MATCH 先写分诊表；归为预注册错误的必须停下报告，不得自行改期望。"  
及任务书 §5 停止条件：  
> "冒烟出现被归为预注册错误的非 MATCH"

**执行者严格遵守硬停机规则，停止正式两遍运行（S-G），不自行修改预注册期望，就地停下向用户完整报告**。

---

## 8. S-H：M2 合并总表 v5（`M2_CONSOLIDATED_R8_M2d.tsv`）与状态表

基于全量历史数据与 r8m2d 冒烟实测结果生成合并总表，严格通过数学公式断言：
- **总行数**：$$174 (\text{r8m2b}) + 54 (\text{r8m2c}) + 28 (\text{r8m2d}) = \mathbf{256} \quad (\mathbf{256 == 256 \ PASS})$$
- **被替代行数**：$$26 (\text{r8m2c}) + 28 (\text{r8m2d 替代行}) = \mathbf{54}$$
- **有效行数**：$$\text{有效行} = 256 - 54 = \mathbf{202} \quad (\mathbf{202 == 202 \ PASS})$$
- **各类别之和断言**：
  $$\text{MATCH } (199) + \text{MISMATCH } (3) = \mathbf{202} \quad (\mathbf{202 == 202 \ PASS})$$
  （其中 FLAKY=0, GDB_DIVERGENT=0, UNJUDGED=0）。

### 8.1 有效点状态拆解（`M2_F3_STATUS_R8_M2d.tsv`）

将有效 199 个 MATCH 点按性质拆解：
- **健康 MATCH**：**175 点**（正常 API 成功或经设计预期报告失败）；
- **红点表征 MATCH**：**24 点**（全部为确认崩溃缺陷的表征吻合，非功能健康）：
  - `RP-R8-M2c-1` 表征行：9 点（SOLN-1763 崩溃表征）；
  - `RP-R8-M2c-1b` 表征行：15 点（SOLN-1764 dbg 6 点 + SOLN-1765 9 点，重试崩溃表征）。
- **待裁决未命中行**：3 点（`SOLN-1764-*-FA`，受 `s4_fail_alloc_armed` 保护限制未命中）。

---

## 9. S-I：红点台账更新、S3R5 修复设计规范与 F4 回归清单

1. **红点台账更新（`RED_POINTS_LEDGER_APPEND_R8_M2d.tsv`）**：
   - `RP-R8-M2c-1`：更正崩溃位置为 `S4.cpp:1764`（调用 1 立即解引用空指针崩溃）；
   - `RP-R8-M2c-1b`：**依实测正式升级为 `F_CONFIRMED`**！GDB `bt 24` 与事实列证实：调用 1 失败后 `S->solution` 保持非空，调用 2 重试必然跳过 InitSolution 并解引用空指针崩于 `S4.cpp:1995`（1764）或 `S4.cpp:2021`（1765）；
   - `K-1`（RP-R6d-8）：**依 U274 正式关闭**（带范围声明：本装置与模型下未复现静默吞没，info=10，return 20，由 `M2-06-01-F3-C` 实测 MATCH 确认）。
2. **S3R5 修复设计规范（`S3R5_DESIGN_R8_M2d.md`）**：
   - 确立"立即判空、失败清理并置 NULL、返回 1 且保持 S4_MSG 报错"三项原则；
   - 给出无需修改驱动、彻底解决调用 1 崩溃与调用 2 重试野指针崩溃的伪代码方案；未生成任何 `S4/` 下文件或补丁。
3. **F4 回归清单（`REGRESSION_PLAN_F4_R8_M2d.tsv`）**：
   - 登记 27 个 SOLN 点在修后 F4 树上的统一预期：`rc1=1, rc2=0, exp_init_clean=HOLD, class=REPORTED_FAILURE`；
   - 规划 M2 全量 202 个有效点在 F4 上的全套重跑回归方案。

---

## 10. 违规与事件披露

### 表一：越界写入尝试（命令自身写仓库外路径）
*无（0 处）。*

### 表二：工具框架与运行事件
| 轮次 | 命令/操作 | 是否落盘 | 性质说明 |
|---|---|---|---|
| r8m2d | grep 工具搜索 `>` | 落盘到 `/tmp/dsh-spill-YHUqKB/…-grep-results.txt` | 框架自身大输出 spill，非执行者违规 |
| r8m2d | glob 工具搜索 `*ERRATA*` | 落盘到 `/tmp/dsh-spill-YHUqKB/…-glob-results.txt` | 框架自身大输出 spill，非执行者违规 |
| r8m2d | grep 工具搜索 `R6BSTATE 1 solution` | 落盘到 `/tmp/dsh-spill-YHUqKB/…-grep-results.txt` | 框架自身大输出 spill，非执行者违规 |
| r8m2d | `run_smoke_r8m2d.py` 冒烟运行 | 落盘到 `$EV/smoke/` | 3 个 `-FA` 行实测 hit=0 触发 Gate 6/7 失败，严格按硬规则触发停机并报告 |

---

## 11. 门禁快照与版本状态

### 11.1 门禁快照
- 开工门禁：`checkpoints/p05/evidence/p05-s4r8/m2d/GATE_R8_M2d_start.txt`（`FAILS=0`）
- 完工门禁：`checkpoints/p05/evidence/p05-s4r8/m2d/GATE_R8_M2d_end.txt`（`FAILS=0`，见后文生成记录）

### 11.2 当前 git 状态
- `git log -1`：`8f47dc605bfc086ba34aea144bc6157876c2d97d`
- `git status --short`：严格仅包含经批准的 `STATE.md`、`RULINGS.tsv`、`ERRATA_8.txt`、本报告、`registries/s4r8/M2/r8m2d/` 与 `testing/d003/stage_s4/*r8m2d*`。

---

## 12. 待用户裁决事项

本轮执行未发现任何规划者可查而未查的事项。唯一需用户裁决的事项为：
1. **S3R5 修复轮是否批准开工**：
   RP-R8-M2c-1 及 RP-R8-M2c-1b 缺陷机理与重试崩溃物理事实已 100% 证实（升级为 F_CONFIRMED）；S3R5 修复设计规范（`S3R5_DESIGN_R8_M2d.md`）与 F4 回归清单（`REGRESSION_PLAN_F4_R8_M2d.tsv`）已编制就绪。请用户审核是否批准启动 P05-S3R5（修改 `S4/S4.cpp:1763–1773`，冻结新树 F4 并开展全量回归）。
2. **`init-F3-san` 下 1764 注入处置**：
   因 `S4.cpp` 的 `s4_fail_alloc_trip` 受 `!s4_fail_alloc_armed` 保护，原生运行下 `S4_FAIL_ALLOC_AT` 无法在非 Clone 路径生效。建议在 S3R5 修复轮中同步验收或待 S5 处理。

---

*awaiting user review*
