# P05-S2R5：FMMGetEpsilon 返回接收点与 AddFieldToCache 检查的装置补齐（D003）

> **状态：未完成，等待用户审核。** 本报告不宣布 P05-S1、P05-S2、P05-S3、P05-S4 任一阶段完成，也不代替用户判定"S2 已完成"。第 6 节给出更新后的 S2 收敛核对表，签收由用户决定。
> 本轮所有结果称"装置观察"，不称"验证"。本报告不处理 S3 的 Jones a/b/c 取舍，只提供数据。

## 0. 定位与未完成声明

- 本报告属于正式阶段 **P05-S2** 的补充子任务 S2R5，不是新阶段。P05 固定五阶段 S1–S5，本轮未引入 S6。历史报告与文件名未改写。
- 阶段定义依据：用户提示词（P05-S2 测试装置：扩展注入器覆盖 S4_malloc、LinearSolve 与两步分支，接入仓库测试目录，源码仅改 testing/ 并允许必要的测试专用 seam）。仓库内无 P05 原始计划文档，未搜索原文。
- 起点：HEAD = `e583998`；分支 `codex/p05-d003-fft-error-propagation`；`S4/` 相对 `64eb0b5` 改动为 0；开工时工作区干净；`judge_d003.py` sha256 `d2d04145e0561638`（未改）。
- 结束核对：见第 8 节。

## 1. 授权、边界与用户决定

**授权与边界**：不修改 `S4/` 下任何文件（相对 `64eb0b5` 保持 0 改动）。可修改 `testing/d003/` 与 `checkpoints/p05/`。seam 只应用于 `git archive` 导出副本。判定器只依赖事实（rc1、rc2、信号、输出字节、命中数），不读取驱动 PASS/FAIL 退出码。

**沿用的决定**：D-U1（H 上无 family-B 等价点，结构性差异）、B2 请求前缀批准、U-1（公开 API 缓存命中为已知限制）、U-2（B 上 vfield 分裂保持 [未验证]）。

**本轮新增的用户决定**：

| 决定 | 内容 | 本轮处理 |
|---|---|---|
| L9 | `driver-all` 与 `driver-all-t4` 同名不同版本：已由 `--driver-sha256` 固定机制缓解，接受 | 第 4.4 节核实该机制仍然生效（错误哈希拒绝测试） |
| L10 | 配置范围仅 NB=9、固定几何、θ=0：接受为已知限制；NB=1..8 记录沿用 `R2C_NB_REACHABILITY.txt`，不扩展 | 第 6 节写为已接受为已知限制，并写入 P05-S4 输入 |

## 2. 起点、开工与第 0 步快照

- **第 0 步（在任何其他命令之前）**：`/tmp` 顶层快照（开始）：**0 条目，sha256 `e3b0c442…`**。抽样 strace（开始，对只读的 `git status --porcelain`）：**280 事件，`/tmp` 相关 0，仓库外写入型 open 0**。记录于 `checkpoints/p05/evidence/p05-s2r5/`（`strace-start-git-status.strace`、`PROGRESS_CHECKPOINT.txt`）。
- 开工核对（`OPENING_CHECK.txt`）：HEAD `e583998`；分支正确；`S4/` 相对 `64eb0b5` 为 0；工作区干净；`judge_d003.py` sha256 `d2d04145…`。
- CPU：AMD Ryzen 7 3800X；指令集标志含 `fma`、`avx`、`avx2`、`bmi2`、`f16c`，**不含 avx512**（只读 `/proc/cpuinfo`）。编译器 g++ 15.2.0。构建选项：仓库默认 `-O3 -march=native -fcx-limited-range`（同一台机器）。

## 3. R5-1：FMMGetEpsilon 返回接收点（L5）

### 3.1 清点（[源码]，三棵树，只读）

`git show <commit>:S4/S4.cpp` 逐行检查。三棵树的 `FMMGetEpsilon_*` 调用均为 **10 处**（非注释行）。证据：`r5-1/R5_1_SITE_FACTS.txt`。

| 树 | 分发形式 | 接收点 | 失败时的行为 |
|---|---|---|---|
| B `37a82e8` | 裸调用语句（2368–2393） | **无**（无 `fmm_ret` 变量，无检查） | 返回值被丢弃；继续进入 `SolveLayerEigensystem`（2399–2420） |
| A `876181c` | `fmm_ret = FMMGetEpsilon_*(...)`（2369–2394） | 2400：`if(0 != fmm_ret){ DiscardLayerModes; return 20; }` | 返回 20 |
| H `64eb0b5` | `fmm_ret = FMMGetEpsilon_*(...)`（2382–2407） | 2413：`if(0 != fmm_ret){ DiscardLayerModes; return 20; }` | 返回 20 |

**对任务前提的更正**：任务书称"A/B 的强制 fmm_ret=1 在丢弃返回值的代码里本来就不会被检查"。这对 **B** 成立，对 **A 不成立**：A 与 H 一样在分发之后有单一检查（A 2400），强制 `fmm_ret=1` 会走到 `return 20`。因此 A 是**状态树**，不是丢弃树。

### 3.2 十个点与驱动模式的可达性（[源码]，并经控制运行 [实测]）

| 点（ID） | H/A 行 | 调用 | 驱动模式（可达） | 依据 |
|---|---|---|---|---|
| 150 | 2382 / 2369 | `FMMGetEpsilon_Experimental` | `experimental` | `use_experimental_fmm`（驱动第 84 行） |
| 151 | 2386 / 2373 | `FMMGetEpsilon_Kottke` | `kottke` | `discretized` + `subpixel`（驱动第 81 行） |
| 152 | 2388 / 2375 | `FMMGetEpsilon_FFT` | `fft`、`fftjones`、`fftnv`、`fftvl` | `discretized`、无 subpixel（驱动第 80、85–88 行） |
| 153 | 2391 / 2378 | `FMMGetEpsilon_PolBasisJones`（FFT 链） | `fftjones` | FFT 后的 PolBasis 分支 |
| 154 | 2393 / 2380 | `FMMGetEpsilon_PolBasisNV`（FFT 链） | `fftnv` | 同上 |
| 155 | 2395 / 2382 | `FMMGetEpsilon_PolBasisVL`（FFT 链） | `fftvl` | 同上 |
| 156 | 2403 / 2390 | `FMMGetEpsilon_PolBasisJones`（ClosedForm 链） | `jones` | 非离散、polarization（驱动第 82 行） |
| 157 | 2405 / 2392 | `FMMGetEpsilon_PolBasisNV`（ClosedForm 链） | `nv` | 同上 |
| 158 | 2407 / 2394 | `FMMGetEpsilon_PolBasisVL`（ClosedForm 链） | `vl` | 同上 |
| 159 | 2400 / 2387 | `FMMGetEpsilon_ClosedForm` | `closed1d`、`closed2d`、`tensor`、`jones`、`nv`、`vl` | 非离散分支（驱动第 75、93、102 行） |

**不可达判定**：**无**。每个点在每棵树上都有实测命中（第 3.5 节）。S2R3 的 T1 可达性表（`evidence/p05-s2r3/t1/T1_REACHABILITY_TABLE.tsv`）记录了 FMM 内部点与 FFT 链的可达性，但**未测量 `fmm_ret` 返回接收点本身**，因此本轮从源码与控制运行建立该点的可达性，并检索了 `REG_3C2_FFTCHAIN.tsv` 的路由。

### 3.3 注入路由（family E，导出副本 seam，[源码] 锚点）

- **锚点**：每个点用"缩进加完整语句文本"的精确行匹配，在三棵树中各唯一（A 10/10、H 10/10、B 10/10）。**不使用行号**。PolBasis 三条调用文本在 FFT 链与 ClosedForm 链各出现一次，靠缩进（7 个制表符与 6 个）区分，这是内容差异而非行号。
- **A 与 H**：在每条 `fmm_ret = FMMGetEpsilon_X(...);` 之后插入 `#ifdef S4_TEST_FMMRET_SEAM` 守卫的 `fmm_ret = S4_TEST_FMMRET_AFTER(ID, fmm_ret);`。钩子在请求匹配时返回 1，否则原样返回。真实的 FMM 函数仍然执行，其输出是真实的。请求前缀 `fmmret:ID:K`。
- **B**：无 `fmm_ret`，无法强制状态。B 的种子为裸调用之后的钩子。**两种模型**见第 3.4 节。
- **检查**（`apply_seam_r5_fmmret.py`，`--check-only` 与写入均 rc 0）：三树各 10 个点唯一匹配。

### 3.4 B 列的模型（选择，有先例，已披露）

**发现（实测）**：仅观察的 `fmmbuf` 钩子使导出输出与无请求控制**完全相同**（`r5-1/bufcheck`，SAME）。因此最初为 B 设计的"观察"列并未测量任何扰动：其 SILENT_SWALLOW 来自未扰动运行，不是失败证据。该设计被替换，原始结果保留并披露为零测量（null）。

**源码事实（[源码]）**：B 没有失败模型可取。B 的 FFT 在其所有路径上都返回 0（`fmm_FFT.cpp` 第 238 行），不存在"未写入"的确定值；缓冲在调用前的内容依赖前序状态（`S4.cpp` 2330–2368 的均匀分支以 `SetMatrix` 写入）。因此 **B 的失败模型无法由源码确定**，任何缓冲值都是模型选择。

**选择**：恒等模型，即仓库 family B 模型 1 的先例（注入器头注释，"the solve's output b is overwritten with the identity"；family B faithful 的 "Epsilon_inv := identity … models a real singular … result"）。应用于 FMM 输出：`Epsilon_inv := I`，`Epsilon2` 的四个 n×n 块（偏移 `(0,0)`、`(n,0)`、`(0,n)`、`(n,n)`，与均匀分支的布局一致）`:= I`。请求前缀 `fmmpert:ID:K`。**这是选择，不是 FMM 源码定义的失败值**，报告中 B 列均据此标注。设计文件：`r5-1/B_MODEL_DESIGN.txt`。

### 3.5 运行结果（三列，每点两次）

**注册**：`REG_R5_1_FMMRET.tsv`（sha256 `70464ca3…`，`2026-10-11T08:53:20Z`，在任何注入运行之前冻结）；`REG_R5_1_BPERT.tsv`（sha256 `51c3a633…`，`2026-10-11T08:59:49Z`，在 B 的剩余运行之前冻结）。更正：`REG_R5_1_FMMRET_CORRECTION_1.tsv`（sha256 `a116f694…`，仅更正依据，类别不变）。

**三列表**（由正式运行的 raw 文件机械生成，`r5-1/R5_1_THREE_COLUMN.tsv`）：

| 点 | 模式 | H（状态，fmmret） | A（状态，fmmret） | B（恒等扰动，fmmpert，**不同模型**） | 重复（H/A/B） | B 的非有限值（首次输出） |
|---|---|---|---|---|---|---|
| 150 | experimental | REPORTED_FAILURE（rc1 20，hit 1） | REPORTED_FAILURE（rc1 20，hit 1） | SILENT_SWALLOW（rc1 0，hit 1） | 一致/一致/一致 | 72 / 144 |
| 151 | kottke | REPORTED_FAILURE | REPORTED_FAILURE | SILENT_SWALLOW | 一致/一致/一致 | 72 |
| 152 | fft | REPORTED_FAILURE | REPORTED_FAILURE | SILENT_SWALLOW | 一致/一致/一致 | 72 |
| 153 | fftjones | REPORTED_FAILURE | REPORTED_FAILURE | SILENT_SWALLOW | 一致/一致/一致 | 72 |
| 154 | fftnv | REPORTED_FAILURE | REPORTED_FAILURE | SILENT_SWALLOW | 一致/一致/一致 | 72 |
| 155 | fftvl | REPORTED_FAILURE | REPORTED_FAILURE | SILENT_SWALLOW | 一致/一致/一致 | 72 |
| 156 | jones | REPORTED_FAILURE | REPORTED_FAILURE | SILENT_SWALLOW | 一致/一致/一致 | 72 |
| 157 | nv | REPORTED_FAILURE | REPORTED_FAILURE | SILENT_SWALLOW | 一致/一致/一致 | 72 |
| 158 | vl | REPORTED_FAILURE | REPORTED_FAILURE | SILENT_SWALLOW | 一致/一致/一致 | 72 |
| 159 | closed1d | REPORTED_FAILURE | REPORTED_FAILURE | SILENT_SWALLOW | 一致/一致/一致 | 0 |

**读法**：

- H 与 A 在全部 10 点上为 REPORTED_FAILURE（`rc1 20`、`hit 1`）。这是**状态路径**：强制的状态在源码的单一检查处返回 20。
- B 在全部 10 点上为 SILENT_SWALLOW（`rc1 0`、`hit 1`）。这是**恒等扰动下的装置观察**：每个点的首次输出都与无请求控制不同（10/10），且运行不报告任何失败。
- **B 的非有限值是实测事实**：点 150–158 的首次输出含 72/144 个非有限值（150 处为 E 的 48 个与 H 的 24 个）；点 159 为有限值（0 个非有限，120/144 分量不同）。判定器据事实给出 SILENT_SWALLOW，**不替换该事实**；相对差统计对非有限项无定义，未杜撰数值。
- **因此 B 列的 SILENT 与 H/A 的 REPORTED 不是同一模型下的修复效应**：它们分别是"输出被破坏但不报告"与"状态被报告"两种观察，模型不同（3.4）。

**重复**：三棵树的两次运行在类别、rc1、rc2、命中数上**逐行一致**（facts 层面，`facts-differing rows: 0`）。

**全部点的命中证明**（第 3.5 节前置）：每个点在每棵树上都有实测命中（`hit ≥ 1`），因此没有点被判为不可达。扇出：152 与 159 在 H/A 上分别由 4 与 6 个模式运行命中。

### 3.6 正对照与不改变正常输出的证明

- **正对照**：H `fmmret:150:1`（experimental）：`S4FMM HIT fmmret id=150 call=1 ret=0->1`，`RC first 20`，判定器自 facts 给出 REPORTED_FAILURE（忽略驱动的 FAIL 行）。B `fmmpert:150:1`：`HIT 1`，首次输出与控制不同，判定 SILENT_SWALLOW。
- **无请求控制**：A、B、H 三树各 12 个模式，stdout 与两个转储与对应明文驱动**全部相同**（36/36，`r5-1/noreq`，`r5-1/noreq-bpert`）。
- **无宏导出与明文导出的比较（修正，见 D-R5-8）**：按路径逐对象比较时，A 与 B 为 23/24（`S4.o` 不同），family F 的 H 为 21/24（三个 PolBasis 目标不同）。这些差异来自各目标内嵌的源文件路径，**不是代码差异**：将两侧预处理后的源码在相同文件名下编译，**A、B 及 H 的三个 PolBasis 文件全部逐字节相同**。因此"无宏即惰性"的结论以同名编译为准。早先写的"24/24"为路径敏感比较，已撤回。
- **宏开启时仅预期目标改变**：family E 三树仅 `S4.o`；family F 为三个 PolBasis 目标（`fmm_PolBasisJones.o`、`fmm_PolBasisNV.o`、`fmm_PolBasisVL.o`），`S4.o` 不变。
- **既有家族宏互不激活**：family E 插入的文本只引用 `S4_TEST_FMMRET_*`、`S4_TEST_FMMBUF_*` 与 `S4_TEST_FMMPERT_*`，不引用 `S4_TEST_LINEARSOLVE_*`、`S4_TEST_ALLOC_*`、`S4_TEST_KOTTKE_*`（计数为 0）。

### 3.7 R5-1 的非有限值与 S2 的关系

B 的恒等扰动产生非有限场，这意味着 B 列的"输出被破坏"是强的，而非细微的。但它只是**一种**选定扰动（恒等）下的观察。它不证明 B 的真实失败行为，也不证明其它扰动模型的结果。该限制写入第 7 节 L5 的状态与第 8 节未闭合缺口。

## 4. R5-2：AddFieldToCache 检查维度的隔离（L4）

### 4.1 已有证据的复核（先于设计）

- S2R3 3b 行 `acache3977`（`alloc:25:1`，家族 C）在 jones 下：B 与 A 为 CRASH，H 为 REPORTED_FAILURE。证据：`checkpoints/p05/evidence/p05-s2r3/stage3/REG_3B_THREECOLUMN.tsv`。**该证据注入的是函数内部的分配失败**（`Simulation_AddFieldToCache` 的 FieldCache `S4_malloc`，H 的 `S4.cpp:4010–4012` 检查）。它检验的是函数自身的 NULL 检查，**不隔离调用方的检查**。L4 指的是调用方检查，二者是不同分支。

### 4.2 无等价点（A 与 B）

`Simulation_AddFieldToCache` 在 **A（`876181c`）与 B（`37a82e8`）中均为 `void`**（`S4.cpp` 声明第 226 行；定义分别为 3975 与 3969 行）。没有返回值可供强制，因此 A 与 B 的列写作**"无等价点（void 函数）"**，不伪造 A 列或 B 列。

### 4.3 H 上的调用方检查（[源码]）

三个 PolBasis 调用方在 H 中均为"检查返回值 → 清理 → return 1"：

| 调用方 | 检查行 | 清理 |
|---|---|---|
| `fmm_PolBasisJones.cpp:340` | `if(0 != Simulation_AddFieldToCache(...)){` | `S4_free(work); S4_free(ivalues); return 1;`（341） |
| `fmm_PolBasisNV.cpp:228` | 同上 | 同上（229） |
| `fmm_PolBasisVL.cpp:237` | 同上 | 同上（238） |

每个检查语句在其文件中唯一。证据：`r5-2/R5_2_SITE_FACTS.txt`。

### 4.4 种子与隔离方法

- **家族 F（仅 H）**：在三个调用点，把调用表达式包装为 `S4_TEST_ADDFIELD_AFTER(ID, Simulation_AddFieldToCache(...))`，ID 为 160（Jones）、161（NV）、162（VL）。钩子在请求匹配时返回 1，否则原样返回。**函数本身完整运行**，其内部分配路径与自身的 NULL 检查不受影响；只改变调用方所见的值。请求前缀 `addf:ID:K`。
- **检查**（`apply_seam_r5_addfield.py`）：`--check-only` 与写入均 rc 0；三个调用点各唯一。
- **无宏导出**：与明文 H 同名编译后逐字节相同（三个 PolBasis 文件）；**宏开启时**仅三个 PolBasis 目标改变，`S4.o` 不变（与预测一致）。
- **无请求控制**：family F 驱动在 12 个模式下与明文 H 的 stdout 相同。
- 注册：`REG_R5_2_ADDFIELD.tsv`（sha256 `903e51ba…`，`2026-10-11T09:03:33Z`，运行前冻结）与 `REG_R5_2_ADDFIELD_FFT.tsv`（sha256 `e767d562…`，`2026-10-11T09:04:24Z`，运行前冻结）。

### 4.5 结果（H，每行两次，事实一致）

| 行 | 链 | 类别 | rc1 | rc2 | hit | 重复 |
|---|---|---|---|---|---|---|
| R5-2-H160-jones | ClosedForm（2403 链） | REPORTED_FAILURE | 20 | 0 | 1 | 一致 |
| R5-2-H161-nv | ClosedForm（2405 链） | REPORTED_FAILURE | 20 | 0 | 1 | 一致 |
| R5-2-H162-vl | ClosedForm（2407 链） | REPORTED_FAILURE | 20 | 0 | 1 | 一致 |
| R5-2-H160-fftjones | FFT（2391 链） | REPORTED_FAILURE | 20 | 0 | 1 | 一致 |
| R5-2-H161-fftnv | FFT（2393 链） | REPORTED_FAILURE | 20 | 0 | 1 | 一致 |
| R5-2-H162-fftvl | FFT（2395 链） | REPORTED_FAILURE | 20 | 0 | 1 | 一致 |

**两条链均已覆盖**：FFT 链的三行登记于 `REG_R5_2_ADDFIELD_FFT.tsv`（冻结于运行之前，sha256 `e767d562…`），与 ClosedForm 链的三行（`REG_R5_2_ADDFIELD.tsv`）一并运行。

### 4.6 隔离的实测依据（gdb，只读）

- **函数完整运行**：强制的 Jones 运行中，`Simulation_AddFieldToCache` 进入 **1 次**；命中记录为 `S4FMM HIT addf id=160 call=1 ret=0->1`，即函数的真实返回为 0，钩子只改变了调用方所见的值。因此调用方检查是**唯一被触发的失败路径**。
- **FFT 链的顺序**：`FMMGetEpsilon_FFT` 先于 `FMMGetEpsilon_PolBasisJones` 进入，两轮（rc1 与 rc2）皆然。FFT 在调用方检查之前完整运行。
- **清理（S4_free）的观察，不宣称无泄漏**：强制 Jones 运行中 `S4_free` 共 **24** 次，控制运行 **21** 次，差 3。按调用方归因：`FMMGetEpsilon_PolBasisJones` +2（调用方清理对：`work`、`ivalues`），`FMMGetEpsilon_ClosedForm` +1，`Simulation_ComputeLayerModes` +1（丢弃路径）。**无泄漏结论属于 P05-S4 的 ASan 范围，本节不作判断。**

### 4.7 L4 的状态

- H 上调用方检查与清理：**已测量**（两条链，各三行，每行两次一致，命中 1）。
- A、B：无等价点（void），这是结构事实，不是未测。
- 因此 L4 的"AddFieldToCache 检查维度"在 H 上**已闭合**；A 与 B 不适用。

## 5. R5-3：L9 机制核对

- 运行器未改动。
- **错误哈希**（pinned 全零）：rc 1；stdout 为空；stderr 为 `REFUSED: driver sha256 mismatch`，并列出 pinned 与 actual。拒绝发生在 `matrix_r2.py` 第 178 行（`_verify_driver`），**早于任何一行的运行**（第 188 行 `run_row`）、**早于 manifest 写入**（179）与 **raw 文件写入**（196）。
- 输出目录在第 177 行创建，拒绝后为**空目录**（0 个文件；无 `raw_BASE.json`、无 `runs/`、无 manifest）。这是先建目录的副作用，无数据写入。
- **正确哈希**：同一驱动与登记，rc 0，13 行运行，写出 `raw_BASE.json`。这个边界检验证明拒绝是真实的，而非运行器总是失败。此运行的匹配数（4/13）**不是回归结果**：它把旧登记与 R5-1 的 B 驱动配对，与 11/13 的基线不是同一配对。

**历史驱动对（S2R2 D-RUN-2 / D-DRV-1 的误用，复现）**：

| 驱动 | 路径（S2R2 证据，未复制） | sha256（前 8 位） |
|---|---|---|
| 旧 `driver-all` | `seam4-cur-aa1c51d/bin/driver-all` | `32f7a032…` |
| 新 `driver-all-t4` | `seam4-cur-aa1c51d/bin-t4/driver-all-t4` | `1aa0c913…` |

以 `driver-all-t4` 的哈希为 pin，传入旧 `driver-all`：rc 1，`REFUSED: driver sha256 mismatch`，**写入 0 个文件**。两个驱动内容不同，内容哈希能区分同名前缀的两个驱动。**L9 的缓解（用户已接受）在本运行器上有效。**


## 6. S2 收敛核对表（更新版）

**判定原则**（沿用 S2R4）：**已闭合** = 有实测证据，且可复核；**已接受为已知限制** = 有明确的用户决定，写明限制与决定来源；**未闭合** = 证据不足或存在未解决问题，写明原因。本表**不代替用户判定"S2 已完成"**。

本轮更新 L4、L5、L9、L10 四行；其余行沿用 S2R4 §7，状态不变。

### 6.1 S2 的定义组成（沿用，状态不变）

| # | 组成 | 状态 | 证据与说明 |
|---|---|---|---|
| G1 | 覆盖 S4_malloc | **已闭合（范围内）；范围外已接受为范围决策** | FMM 翻译单元 17 处真实调用均有注入证据；S4.cpp 中纳入范围的 family C 5 处已闭合；其余按范围决策不在 S2 内（S2R4 §7.2）。 |
| G2 | 覆盖 LinearSolve | **已闭合（范围内）；范围外已接受为范围决策** | FMM 的 9 处 LinearSolve 均有注入证据（S2R4 §7.3）；S4.cpp 2 处与 rcwa.cpp 8 处不在 P05 范围内。 |
| G3 | 覆盖两步分支 | **已闭合**（按 S2 原报告 §4.3） | plan（真实）、scratch（真实）、exec（边界模拟）。 |
| G4 | 接入仓库测试目录 | **已闭合** | `testing/d003/` 内的注入器、运行器、判定器、seam 脚本与 stage4 脚本，已提交（本轮新增 `bb08729`、`bb59558`、`49a71df`）。 |
| G5 | 源码仅改 testing/（允许必要的测试专用 seam） | **已闭合** | `S4/` 相对 `64eb0b5` 为 0 改动；本轮提交越界路径 0。 |

### 6.2 已知遗留项（更新）

| # | 遗留项 | S2R4 状态 | **S2R5 状态** | 限制内容、来源决定或原因 |
|---|---|---|---|---|
| L1 | 公开 API 路径上的缓存命中 | 已接受为已知限制（U-1） | 已接受为已知限制（U-1）（沿用） | 缓存命中仅经内部接口 `S4_Simulation_DestroyLayerModes` 覆盖（`S4FMM_TWICE=slab` + `s4malloc` NTH 7，inj_call 2）；公开 API 路径未测。**来源：用户决定 U-1。** |
| L2 | B 上 PolBasis vfield 的类别按模式分裂 | 已接受为已知限制（U-2，[未验证]） | 已接受为已知限制（U-2，[未验证]）（沿用） | 源码阅读未完整解释；按用户决定不追查。**来源：用户决定 U-2。** |
| L3 | H 上无 family-B 点 | 已接受为已知限制（D-U1，结构性） | 已接受为已知限制（D-U1，结构性）（沿用） | H 的求解改为 `&solve_info`，family B 锚点消失；以 buf-only 与 B2 替代行覆盖。**来源：用户决定 D-U1。** |
| **L4** | **AddFieldToCache 检查维度未单独隔离** | 未闭合（部分证据） | **已闭合（H 上）；A、B 为无等价点** | H 三个调用方的检查与清理经家族 F 隔离（ClosedForm 链与 FFT 链各三行，每行两次一致，hit 1，rc1 20）；函数本身完整运行（一次进入，真实返回 0）。A 与 B 的 `Simulation_AddFieldToCache` 为 `void`，无返回值可强制，记为"无等价点"（第 4.2 节）。**不宣称无泄漏**（P05-S4 ASan 范围）。 |
| **L5** | **`FMMGetEpsilon` 返回接收点的注入路由未建立** | 未闭合 | **已闭合（范围内，三树）** | 家族 E 为十个分发点（ID 150–159）在 A 与 H 上强制 `fmm_ret`（REPORTED_FAILURE，10/10，两次一致）；B 无状态变量，以恒等扰动（`fmmpert`）观察（SILENT_SWALLOW，10/10）。**B 的失败模型为所选恒等模型（有仓库先例），不是 FMM 源码定义的失败值**；B 的首次输出含非有限值（点 150–158 为 72/144）。S2R2 的行号 `S4.cpp:2369` 是 B/A 行号，H 上应为 `fmm_ret` 接收（2382–2407）。第 3 节。 |
| L6 | 失败模型仅在 H 测得 | 已接受为已知限制（结构性） | 已接受为已知限制（结构性）（沿用） | A 与 B 的 family B 为输出模型；B 无状态。L5 的 B 列为另一种恒等模型（见 L5），**不构成** H 与 B 的同模型对照。 |
| L7 | 驱动 RESULT 文字不一致 | 已接受为已知限制 | 已接受为已知限制（沿用） | 判定只用事实，不读驱动的 PASS/FAIL；历史驱动不改。 |
| L8 | strace 与 `/tmp` 审计为抽样 | 已接受为已知限制 | 已接受为已知限制（沿用） | 抽样不穷尽，不覆盖交互 shell。 |
| **L9** | **`driver-all` 与 `driver-all-t4` 同名不同版本** | 未闭合 | **已接受为已知限制（已由 `--driver-sha256` 缓解）** | **来源：用户决定（本轮）。** 核实（R5-3）：以 `driver-all-t4` 的哈希为 pin 传入旧 `driver-all`，rc 1，`REFUSED`，写入 0 个文件。内容哈希区分两个驱动。 |
| **L10** | **驱动只覆盖 NB=9、固定几何、θ=0** | 未闭合 | **已接受为已知限制** | **来源：用户决定（本轮）。** 记录沿用 `R2C_NB_REACHABILITY.txt`（S2R 记录）：家族 A 16/16 行命中；家族 B 24/24 行命中；家族 C 24 行中 8 行 HITCOUNT=1，16 行崩溃（rc 139，`hitlines=1`，钩子在 SIGSEGV 前触发）。本轮不扩展 NB=1..8。 |
| L11 | 非 FMM 分配 | 已接受为范围决策 | 已接受为范围决策（沿用） | 范围外（S2R4 §7.2）。 |
| L12 | 历史期望映射 | 已闭合 | 已闭合（沿用） | R4-2 POST-HOC 映射。 |
| L13 | S2R2 的 17 case CUR 复跑 | 已闭合 | 已闭合（沿用） | R4-3。 |
| L14 | 开始快照与 strace | 已闭合 | 已闭合（沿用） | 本轮亦已取得开始快照与开始 strace（第 2 节）。 |
| L15 | `S4.cpp:2369` 的行号描述 | 已闭合（更正） | 已闭合（沿用） | S2R2 把 2369 写为 FMMGetEpsilon 返回接收；该行号对应 B/A 树，H 上为 2382–2407（S2R4 §7.5）。 |

### 6.3 更新后的汇总

- **已闭合**：G1–G5（范围内）、L4、L5、L12、L13、L14、L15。
- **已接受为已知限制**：L1、L2、L3、L6、L7、L8、L9、L10；范围决策：L11。
- **未闭合**：**无。**

**本核对表不代替用户判定"S2 已完成"。** 三项需用户决定，决定前 S2 不应被签收：
1. **L5 的 B 列模型**：B 的失败模型是所选的恒等扰动，不是 FMM 源码定义的值。用户须决定：接受该恒等模型作为 B 的观察，还是要求另一种扰动（并另立登记）。
2. **L4 的 H 上结论仅限调用方检查**：函数内部分配检查由 S2R3 的 family C 覆盖，二者合在一起才是 AddFieldToCache 的完整失败路径；用户须确认该划分可接受。
3. **L10 的已接受限制**：S2 的覆盖仅对 NB=9、固定几何、θ=0 成立；用户须确认 P05-S4 可在此范围内进行，或要求扩展。


## 7. 偏离与违规（单一表，沿用 S2R4 并追加本轮行）

依据：`checkpoints/p05/evidence/p05-s2r5/VIOLATIONS_AND_DEVIATIONS_S2R5.txt`（证据，不提交）。本表是违规次数的唯一来源。

### 7.1 写仓库外路径的违规尝试（唯一表）

| # | 轮次 | 命令（摘要） | 是否落盘 | 说明 |
|---|---|---|---|---|
| 1 | S2R3 首轮（上一轮已自行披露） | `git show ... > /tmp/__never_write` | **无法确定** | 本仓库检索 `never_write` 无匹配；与 P-1 条目（`/tmp/x`、`/tmp/__nope`、`/tmp/__ev_check_ignored`、`/tmp/__files_a`、`/tmp/__a`、`/tmp/__x`）是否同一次无法确定。 |
| 2 | S2R4 | `find ... > /tmp_no_write_check_placeholder`（文件系统根下路径，不在 `/tmp` 下） | **否** | 文件系统以只读拒绝；`ls -la` 确认不存在。该命令带 `2>/dev/null`，拒绝信息仅在工具 stderr 中可见。 |
| 3 | **S2R5 R5-1** | `git show <commit>:S4/S4.cpp > /tmp_dummy_not_written`（检查命令的输出被误重定向到文件系统根下路径） | **否** | `ls -d` 确认不存在。该命令未带 `2>/dev/null`，但输出中未见拒绝信息，**仓库外路径的写入尝试已披露**。 |

**本轮自查范围**：回顾本轮的 shell 命令记录与进度文件，除第 3 行外，未发现其它写入 `/tmp` 或仓库外路径的命令。含 `/tmp` 字面量的命令均为只读（`ls -A /tmp`、`ls -d`、`test -e`、仓库内检索）。**这是自查，不是系统审计**：交互 shell 的命令不在 strace 覆盖范围内；strace 抽样只覆盖被跟踪的进程。

### 7.2 其它偏离（沿用 S2R4 的 D-1 至 D-12，本轮追加 D-R5-1 至 D-R5-12）

| 编号 | 偏离 | 纠正 |
|---|---|---|
| D-R5-1 | 任务书称"A/B 丢弃返回值"，对 A 不成立（A 有单一状态检查，返回 20） | 设计在登记前更正（`r5-1/R5_1_SITE_FACTS.txt`） |
| D-R5-2 | 第一版 B 设计为仅观察（`fmmbuf`），测得零扰动，其 SILENT 结果不是失败证据 | 在任何扰动运行前替换为恒等扰动（`fmmpert`）；观察版保留为零测量并披露 |
| D-R5-3 | 登记行使用 `OPEN`，judge 不接受 | 冻结前改为预测类别 SILENT_SWALLOW，附预测依据 |
| D-R5-4 | 更正 1：14 条强制行的依据漏写"unforced 重试会运行被屏蔽的 PolBasis 调用" | 另存为新冻结文件；冻结登记未改（`REG_R5_1_FMMRET_CORRECTION_1.tsv`） |
| D-R5-5 | 扰动 B 的表生成首次因格式参数数错误而残缺 | 整表重新生成 |
| D-R5-6 | 相对差统计对非有限项输出 nan | 测得非有限来源（恒等模型，72/144）；未杜撰数值 |
| D-R5-7 | 写入器首版对 B 缓冲使用占位符 | 写入前替换 |
| D-R5-8 | "24/24 宏关闭目标相同"在路径敏感比较下撤回；路径无关的同名编译下 A、B、H 三个 PolBasis 全部逐字节相同 | 报告 3.6 节更正（D-R5-8） |
| D-R5-9 | gdb 的 `finish` 在断点命令块内截断脚本两次 | 改用无 `finish` 的入口顺序断点 |
| D-R5-10 | 运行器 stdout 重定向至不存在的目录（rc 1，未运行） | 在同一命令内先建证据目录；无仓库外写入 |
| D-R5-11 | R5 包清单计数误为 19，实为 18（重复计一行） | 更正；MANIFEST 计数 67 |
| D-R5-12 | R2C NB 记录家族 A 计数 16/17 把图例行计入 | 数据行为 16/16 |

## 8. 仍未闭合缺口与输入

### 8.1 本轮未闭合的项

**无。** 本轮的四个待定项均有状态：L4、L5 已闭合（范围内，见第 6 节）；L9、L10 为用户决定的已知限制。

### 8.2 仍需用户裁决的事项（不影响本报告的事实，但影响 S2 签收）

1. **L5 的 B 列模型**：恒等扰动是所选模型，有仓库 family-B 模型 1 的先例，但不是 FMM 源码定义的失败值。B 的首次输出含非有限值（点 150–158）。是否接受为 B 的观察，或要求另一扰动（另立登记）。
2. **L4 的范围**：H 上的调用方检查经家族 F 隔离；函数内部分配检查经家族 C（`alloc:25:1`）覆盖。二者合起来才是 AddFieldToCache 的完整失败路径，划分是否可接受。
3. **L10 的限制**：S2 覆盖仅对 NB=9、固定几何、θ=0 成立；P05-S4 是否在此范围进行。

### 8.3 其它未闭合或仅部分闭合的说明（非 S2 的完成条件，但须知）

- **家族 C 的 NB 覆盖**：`R2C_NB_REACHABILITY.txt` 中家族 C 的 16 行崩溃（rc 139）只能证明"钩子在崩溃前触发"，不能给出命中计数。
- **B 的非有限场**：一个非有限的 B 输出在 P05-S4 中应视为何种判定，本轮未决定，判定器只读取事实，不作替换。
- **strace 与 `/tmp` 审计**：仅为抽样（第 8.4 节），不覆盖交互 shell。

## 9. 对 S3 补充收尾与 P05-S4 的输入

**对 S3 补充收尾**：
- ComputeLayerModes 的 `fmm_ret` 接收点（L5）现有家族 E 的 H 与 A 状态强制证据（10/10，REPORTED_FAILURE），`e83255f` 所对应的 AddFieldToCache 调用方检查（L4）现有家族 F 的 H 证据（6/6）。这些是**装置观察**，不是修复的验证。
- B 的 SILENT 结果依赖所选恒等模型，不得作为 S3 修复的证据（B 与 H 不是同一模型）。
- Jones 的 `df3bb02` 正常路径差异仍待用户裁决（S2R3/S2R4 的数据，本轮未改变）。

**对 P05-S4 验证的输入**：
- 每个 FMM 分发点的状态失败路径（10 点，A 与 H）已有装置观察；P05-S4 的"失败后模式不安装"判据可使用这些路由，但需注意 `fmm_ret` 强制在 H 上经 `return 20` 退出，而非经真实的 FMM 失败。
- AddFieldToCache 的调用方清理（`S4_free(work)`、`S4_free(ivalues)`）被观察到执行；**是否无泄漏是 P05-S4 ASan 的判定**，本轮未作判断。
- 公开 API 缓存命中（U-1）与配置范围（L10）为已知限制，P05-S4 的覆盖须以此为界。
- B 的非有限输出（点 150–158）提示 P05-S4 需决定非有限场的判定规则。

## 10. 收尾核对与路径清单

### 10.1 收尾核对（提交本报告前后）

| 项 | 开始（第 0 步） | 结束 |
|---|---|---|
| `/tmp` 顶层快照（条目数，sha256 前 16 位） | 0，`e3b0c442…` | 0，`e3b0c442…` |
| strace 抽样（`git status --porcelain`：事件数；`/tmp` 事件；仓库外写入型 open） | 280；0；0 | 284；0；0 |
| `S4/` 相对 `64eb0b5` 改动 | 0 | **0** |
| 本轮提交的越界路径数（相对 `e583998`） | — | **0** |
| 工作区状态（提交本报告前） | 干净 | 仅本报告未跟踪（提交后干净） |

两对快照与抽样均为**抽样**，不是穷尽审计；strace 不覆盖交互 shell 命令（第 7.1 节）。

### 10.2 路径清单

**报告与证据**：
- 报告：`checkpoints/p05/P05_S2R5_CLOSEOUT.md`
- digest 段落：`checkpoints/p05/S1_evidence_digest.txt`（末尾追加）
- 证据（不提交）：`checkpoints/p05/evidence/p05-s2r5/`，其中 `PROGRESS_CHECKPOINT.txt`、`OPENING_CHECK.txt`、`VIOLATIONS_AND_DEVIATIONS_S2R5.txt`、`strace-start-git-status.strace`、`r5-1/`（REG_R5_1_*、R5_1_THREE_COLUMN.tsv、B_MODEL_DESIGN.txt、reach/、noreq/、noreq-bpert/、formal/、bpert-diff/、nested/）、`r5-2/`（REG_R5_2_*、R5_2_SITE_FACTS.txt、formal/、formal-fft/、isolation/、noreq-F/）、`r5-3/`（R5_3_SUMMARY.txt、refuse-out/、accept-out/、misuse-out/）

**提交**（仅 `testing/d003/` 与 `checkpoints/p05/`）：

| 提交 | 内容 |
|---|---|
| `bb08729` | R5-1：家族 E 状态强制、观察版 fmmbuf、运行器前缀 |
| `bb59558` | R5-1：家族 E 的 B 树恒等扰动（fmmpert） |
| `49a71df` | R5-2：家族 F（AddFieldToCache 调用方检查，H） |
| `d6ce435` | R5-4：复现包 `registries/s2r5/` 与追加的 MANIFEST（18 个新条目） |
| 本报告提交 | 报告与 digest 段落（awaiting user review） |

**复现包**：`checkpoints/p05/registries/s2r5/`（18 个文件），`checkpoints/p05/registries/MANIFEST.tsv`（67 条，原 49 条字节不变）。

**状态**：未完成，等待用户审核。P05-S1、P05-S2、P05-S3、P05-S4 均未被宣布完成。
