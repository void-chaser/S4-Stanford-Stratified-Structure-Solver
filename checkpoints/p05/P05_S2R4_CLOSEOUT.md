# P05-S2R4：收敛收尾（D003）报告

> **状态：未完成，等待用户审核。** 本报告不宣布 P05-S1、P05-S2、P05-S3、P05-S4 任一阶段完成。本报告不代替用户判定"S2 已完成"；第 7 节给出逐行的 S2 收敛核对表，签收由用户决定。
> 本轮所有结果称"装置观察"，不称"验证"。本报告不处理 S3 的 Jones a/b/c 取舍，只提供数据。

## 0. 定位与未完成声明

- 本报告属于正式阶段 **P05-S2** 的补充子任务 S2R4（收敛收尾），不是新阶段。P05 固定五阶段 S1–S5，本轮未引入 S6。历史报告与文件名未改写。
- 阶段定义依据：用户提示词（P05-S2 测试装置：扩展注入器覆盖 S4_malloc、LinearSolve 与两步分支，接入仓库测试目录，源码仅改 testing/ 并允许必要的测试专用 seam）。仓库内无 P05 原始计划文档，未搜索原文。
- 起点：HEAD = `1509c41`；分支 `codex/p05-d003-fft-error-propagation`；`S4/` 相对 `64eb0b5` 改动为 0；开工时工作区干净。
- 结束核对：见第 9 节。

## 1. 授权、边界与用户决定

**授权与边界**：不修改 `S4/` 下任何文件（相对 `64eb0b5` 保持 0 改动，第 9 节核对）。可修改范围为 `testing/d003/` 与 `checkpoints/p05/`。seam 只应用于 `git archive` 导出副本。判定器只依赖事实（rc1、信号、输出字节、命中数），不读取驱动的 PASS/FAIL 退出码；判定器自检输出逐行不变（已核对）。

**沿用的决定**（S2R3 续作二）：

| 决定 | 内容 | 本轮执行 |
|---|---|---|
| D-U1 | H 上无 family-B 等价点，记为结构性差异，不计入方向差异 | 沿用。第 7 节 S2 核对表与 R4-2 映射中明确标注。 |
| B2 前缀批准 | 运行器追加 `linearsolve_null2:`（S2R3 `d8b4276`） | 沿用。 |

**本轮新增的用户决定**：

| 决定 | 内容 | 在本报告中的处理 |
|---|---|---|
| U-1 | 公开 API 路径上的缓存命中：接受为已知限制（内部路由 `S4_Simulation_DestroyLayerModes` 覆盖），不再追查；写入对 P05-S4 的输入 | 第 7 节列为"已接受为已知限制"；第 8 节写入 P05-S4 输入。 |
| U-2 | 基线 B 上 fftnv 与 fftjones/fftvl 的 vfield 类别分裂：保持 [未验证]，不追查 | 第 7 节列为"已接受为已知限制（[未验证]，不追查）"。 |

## 2. 起点、开工与第 0 步快照

- **第 0 步（在任何其他命令之前）**：取得 `/tmp` 顶层快照（开始）：**0 条目，sha256 `e3b0c442…`**。抽样 strace（开始，对只读的 `git status`）：**269 事件，`/tmp` 相关 0，仓库外写入型 open 0**。两者记录于 `checkpoints/p05/evidence/p05-s2r4/`（`PROGRESS_CHECKPOINT.txt`、`strace-start-git-status.strace`）。
- 开工核对（`OPENING_CHECK.txt`）：HEAD `1509c41`；分支正确；`S4/` 相对 `64eb0b5` 为 0；工作区干净。
- CPU：AMD Ryzen 7 3800X；指令集标志含 `fma`、`avx`、`avx2`、`bmi2`、`f16c`，**不含 avx512**（只读 `/proc/cpuinfo`）。编译器：g++ 15.2.0（Ubuntu）。构建选项：仓库默认 `-O3 -march=native -fcx-limited-range`（同一台机器）。

## 3. R4-1：分离"模型"与"修复"（信息点七处）

### 3.1 新增的测试模式与运行器改动

- **注入器**（`testing/d003/src/inject_d003.cpp`，提交 `06acd66`）：新增 family **B2-buf**，请求前缀 `linearsolve_null2buf:ID:K`，钩子 `S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER(id, b, n, ld, model)`。它与 family B 的写入逻辑相同（去掉注释与空白后逐字一致，已核对），**不接收 solve 状态**，不写 `*info`。改动为**纯新增**（删除行 0）。
- **导出副本的 seam 脚本**（`testing/d003/seam/apply_seam_r4_buf.py`，新文件）：复用 `apply_seam_b2.py` 的七个站点锚点与插入位置，只改钩子调用（不传 `&solve_info`）。`apply_seam_b2.py` 未改动。
- **运行器**（`testing/d003/matrix_r2.py`）：`REQUEST_PREFIXES` 追加 `linearsolve_null2buf:`，仅此一项。
- **无请求控制**：改动后的 buf 驱动在无请求时（jones、nv、fft）的 stdout 与两个转储，与改动前的 H 控制（同一树）**字节一致**。
- **判定器自检**：`selftest` 与 `selftest-sensitivity` 的输出与改动前逐行一致；`judge_d003.py` 的 sha256 仍为 `d2d04145…`（未改）。
- **BASE 与 CUR 回归**：用改动后的运行器重跑 R2D 的 BASE 与 CUR 行，与 S2R3 基线的逐字段比较差异均为 **0**（matched 11/13 与 12/13，与 S2R3 一致）。

### 3.2 七站点的输出缓冲等价（gdb 只读块转储，默认选项）

每个站点在钩子返回后，用 gdb 读取输出缓冲的完整有效块（9×9 复数，81 个元素，`checkpoints/p05/evidence/p05-s2r4/r4-1/blocks/`）。比较对象为 A 树 family B、H 树 buf-only、H 树完整 B2。

| 站点（A 树 id / H 树 id / 模式） | A family B 块 | H buf-only 块 | H 完整 B2 块 | 三者块的关系 |
|---|---|---|---|---|
| closed 11 / 134 / closed1d（model 2） | 81 元素 | 81 元素 | 81 元素 | 逐元素文本一致 |
| closed 12 / 138 / closed1d（model 1） | 81 | 81 | 81 | 逐元素文本一致 |
| closed 13 / 144 / closed2d（model 1） | 81 | 81 | 81 | 逐元素文本一致 |
| closed 14 / 244 / tensor（model 1） | 81 | 81 | 81 | 逐元素文本一致 |
| Jones 15 / 375 / jones（model 1） | 81 | 81 | 81 | 逐元素文本一致 |
| NV 16 / 265 / nv（model 1） | 81 | 81 | 81 | 逐元素文本一致 |
| VL 17 / 273 / vl（model 1） | 81 | 81 | 81 | 逐元素文本一致 |

**结论（输出缓冲层）**：七站点中，A family B、H buf-only、H 完整 B2 写入的输出缓冲逐元素相同。因此 A 与 H 之间的"输出模型"在这七个站点上相同；H 完整 B2 与 buf-only 的唯一差异是 `*info = 1` 的状态写入。

**机理边界**：closed 11 为 model 2（两侧都不写缓冲，缓冲保持原值）；closed 12 在 closed1d 下写入缓冲（gdb 实测写前 `b[0]=0.6016`、写后 `b[0]=1`），但**场转储对它不敏感**（见 3.3）。

### 3.3 场层等价（第一次调用转储，逐分量）

| 站点 | 选项 | A family B vs H buf-only | 分量差异 | max rel | median rel | 字节一致 |
|---|---|---|---|---|---|---|
| closed 11 / 134 | 默认 | A vs H | 0 / 144 | 0 | 0 | 是 |
| closed 12 / 138 | 默认 | A vs H | 0 / 144 | 0 | 0 | 是 |
| closed 13 / 144 | 默认 | A vs H | 0 / 144 | 0 | 0 | 是 |
| closed 14 / 244 | 默认 | A vs H | 0 / 144 | 0 | 0 | 是 |
| NV 16 / 265 | 默认 | A vs H | 0 / 144 | 0 | 0 | 是 |
| VL 17 / 273 | 默认 | A vs H | 0 / 144 | 0 | 0 | 是 |
| **Jones 15 / 375** | 默认 | A vs H | **144 / 144** | **4.9144e-12** | **1.8552e-14** | 否 |
| **Jones 15 / 375** | **选项 c**（`-O3 -mno-fma -fcx-limited-range`） | A seam vs H buf | **0 / 144** | **0** | **0** | **是** |

- **选项 c 的构建方法**：只重编译 `fmm_PolBasisJones.cpp`（各树带对应 seam 宏），用 `ar` 替换各自库副本中名为 `fmm_PolBasisJones.o` 的一个成员，`ranlib`，再链接相同的驱动源码。无注入的选项 c 对照（A 与 H）同样字节一致（144/144，stdout 一致）。
- **场层的一个区分力边界**：closed 12（closed1d）的缓冲被写入，但场对它不敏感，因此场一致**不能**单独证明该站点的模型等价；缓冲层比较（3.2）是该站点的主要证据。这一点对所有站点都适用：场层一致是缓冲一致的必要结果，但对不敏感站点不充分。

### 3.4 运行器结果（POST-HOC 登记，两次运行，全部 hit = 1）

登记文件 `checkpoints/p05/evidence/p05-s2r4/r4-1/REG_R4_1_POSTHOC.tsv`（sha256 `064bb180…`，时间戳 2026-10-11T08:19:54Z，只读）。**全部行为 POST-HOC**：期望在探索性运行之后才写入（见第 6 节偏离 D-1）。

| 站点 | A family B（CUR，`linearsolve_null`） | H buf-only（`linearsolve_null2buf`） | H 完整 B2（`linearsolve_null2`） |
|---|---|---|---|
| closed 134 / 11 / 138 / 12 / 144 / 13 / 244 / 14 | SILENT_SWALLOW（rc1 0，hit 1） | SILENT_SWALLOW（rc1 0，hit 1） | REPORTED_FAILURE（rc1 20，hit 1） |
| Jones 375 / 15 | SILENT_SWALLOW | SILENT_SWALLOW | REPORTED_FAILURE |
| NV 265 / 16 | SILENT_SWALLOW | SILENT_SWALLOW | REPORTED_FAILURE |
| VL 273 / 17 | SILENT_SWALLOW | SILENT_SWALLOW | REPORTED_FAILURE |

两次运行之间差异 **0**（三个子集各两次）。

### 3.5 R4-1 的结论（只陈述数据，不替用户裁决）

- **三列表**（任务第 5 节第 3 项）：每站点为"A 树 / H buf-only / H 完整 B2"。A 树与 H buf-only 同为 SILENT_SWALLOW；H 完整 B2 为 REPORTED_FAILURE。
- **差异的来源**：A 与 H buf-only 的输出缓冲逐元素相同（3.2）；H buf-only 与 H 完整 B2 的输出缓冲逐元素相同（3.2）。因此 SILENT_SWALLOW → REPORTED_FAILURE 的变化，纯由"是否设置 solve 状态（`*info = 1`）"引起。该状态检查来自 S3R 修复（`df3bb02` 将 PolBasis 与 closed 的求解改为检查 `solve_info`）。
- **未隔离的维度**：H 的 Jones 还包含 `AddFieldToCache` 返回值检查（S3R `e83255f`，H 树 `64eb0b5` 的 `S4/fmm/fmm_PolBasisJones.cpp` 第 340–342 行）。它在正常分配成功时不改变输出（选项 e、f 下 A 与 H 字节一致，3.3 与 R4-4 第 5 节），但**本轮没有对它做单独隔离**。失败路径由 id 25 的分配注入覆盖（S2R3 3b，见第 7 节）。
- **[推断]**：在"输出模型"维度上，A family B 与 H buf-only 等价；这一结论的依据是 3.2 的缓冲比较，而非场比较。

## 4. R4-2：历史期望的新映射（POST-HOC，不改历史文件）

### 4.1 清点数（任务书写"20 条"为估计；按实际清点）

| 类别 | 条数 | 来源 |
|---|---|---|
| 历史 38 案中 H 观察与历史期望不符 | **18** | `hist38-H-r3/index.txt`（本轮复跑）；与 S2R3 r1 逐条一致（rc 与日志 sha256 差异 0） |
| R2-D 13 案中 H 观察与历史期望不符 | **7** | `r2d-H-r3/raw_H.json`（本轮复跑）：5 条 C-alloc（id 21–25）+ 2 条 N-*（结构性，D-U1） |
| 替代行（不是不匹配，见 4.4） | **1** | N-vl-id17-k1（巧合匹配，不计为一致） |
| **映射行合计** | **26** | `checkpoints/p05/evidence/p05-s2r4/r4-2/MAP_4_POSTFIX.tsv`（sha256 `059b7c0f…`，时间戳 2026-10-11T08:22:26Z，只读，**全部行 POST-HOC**） |

### 4.2 映射内容与分类

映射给出每行的 H 新期望、方向、修复来源与证据等级。方向：23 条为"→ REPORTED_FAILURE"，2 条为结构性（H 无等价点，D-U1），1 条为登记错误加结构性（N-vl-id17）。

| 修复来源（commit） | 行数 | 覆盖的行 |
|---|---|---|
| `b00b630`（S2 修复：FFT plan/exec 传播与 FMM 分配检查；solve_info 检查） | 18 | 历史 38 案中的 18 行（t5 plan/exec/scratch、s2 FFT、s2b FFT/kottke solve_info） |
| `73e00ef`（S3R：ComputeLayerModes 四处分配检查） | 4 | R2-D C-alloc id 21、22、23、24 |
| `e83255f`（S3R：AddFieldToCache 分配检查） | 1 | R2-D C-alloc id 25（jones） |
| 结构性（`df3bb02` 去除 H 上的 family-B 点） | 2 | N-jones-id15、N-nv-id16 |
| 登记错误（S2R D-1）加结构性 | 1 | N-vl-id17 |

**证据等级**：历史 18 行的变化在 B（`37a82e8`）→ A（`876181c`）之间已**实测**（`hist38-base/index.txt` 与 `hist38-cur/index.txt` 逐条比较，恰好 18 条不同，与 H 的不匹配集合相同）；把它们归于 `b00b630` 是 **[推断]**（文件与请求位置对应；`de52142` 只改 `S4.cpp` 的 ComputeLayerModes epsilon 返回，不被这些请求触及），不是单 commit 二分。S3R 的 `73e00ef`、`e83255f` 对 C-alloc 行的归因有 H 源码行号支持（`S4.cpp:2270–2272`、`2305–2310`、`2422–2428`、`2447–2454`、`4010–4012`）与 R4-1 之前的实测（rc1 20）。

### 4.3 复跑与比对结果

| 复跑 | 运行 | 结果 | 映射覆盖 | 映射新期望 = H 观察 |
|---|---|---|---|---|
| 历史 38 案，H，本轮（r3，**一次运行**） | `matrix_d003.py run`，classify | expectation_mismatches 18 | 18/18 | 18/18 |
| R2-D 13 案，H，本轮（r3） | `matrix_r2.py run`（冻结 `MAP_3D_R2D_H.tsv`） | matched 6，mismatched 7 | 7/7 | 7/7 |

**未声明差异**：0。**H 与 S2R3 r1 的历史 38 案比较**：rc 与日志 sha256 逐条相同（差异 0），说明 R4-1 的注入器改动未改变历史 38 案的任何一条运行结果。

### 4.4 N-* 与 N-vl-id17 的替代行（D-U1 的措辞沿用）

- **N-jones-id15-k1、N-nv-id16-k1**：H 上 family-B 钩子引用数为 0（S2R3 第 8.6 节），运行得到 INVALID（hit 0）。替代行指向 R4-1 的 H buf-only 行（SILENT_SWALLOW，hit 1）与 H 完整 B2 行（REPORTED_FAILURE，hit 1）。**这是 D-U1 所称的"结构性差异"**，不计入方向差异，也不计为一致。
- **N-vl-id17-k1**：历史期望 INVALID 为 S2R 的登记错误（D-1，CUR 实测 SILENT_SWALLOW）。它在 H 上为 INVALID 是**巧合匹配**（H 上 family B 不存在，与登记错误叠加），不计为一致。替代行指向 A 树 family B 行（`R4-1-A17`，SILENT_SWALLOW，实测）与 H buf-only 行（`R4-1-Hbuf273`，SILENT_SWALLOW，实测）。
- 替代行的正式观察（R4-1 冻结登记运行）：N-jones、N-nv、N-vl 的 A 与 H buf-only 均为 SILENT_SWALLOW，H 完整 B2 均为 REPORTED_FAILURE（已核对）。

### 4.5 历史文件未改

`MAP_3D_HIST38_H.tsv`（sha256 `06e9d003…`）、`MAP_3D_R2D_H.tsv`（`2f668b83…`）、`R2D_EXPECTATIONS.tsv`、`REGISTRY_T4*.tsv`、`hist38-*/index.txt` 在本轮保持不变（sha256 与记录一致，已核对）。映射是新文件，只声明期望，不是运行输入（字段数 8，非运行器格式，文件头已注明）。

## 5. R4-3：S2R2 的 17 个 case 在 A 树（CUR）上的同方法复跑

### 5.1 方法与输入

- 运行器与驱动机制与 H 复跑相同：`matrix_r2.py run`，驱动为 A 树 seam 驱动 `build3a/bin-A/driver-d003-seam`（sha256 `d70aa165…` 的 plain 版本不用于本项）。
- 输入：`MAP_R4_3_S2R2_CUR.tsv`（sha256 `40cebc12…`，时间戳 2026-10-11T08:23:00Z，只读），由冻结的 `MAP_3D_S2R2_H.tsv`（sha256 `dc228a92…`）机械派生，**只把树名由 H 改为 CUR**。因此期望列即 S2R2 的 CUR 期望（来自 `REGISTRY_T4.tsv`、`REGISTRY_T4_NVVL.tsv`、`REGISTRY_T2_v2.tsv`），**不构成新期望**。派生件来源已在 `MAP_R4_3_S2R2_CUR.source.txt` 说明。
- 两次运行（`s2r2-CUR-r1`、`s2r2-CUR-r2`）。

### 5.2 结果

| 复跑 | 行数 | 观察类别 | 匹配 |
|---|---|---|---|
| A（CUR），r1 | 17 | REPORTED_FAILURE × 17 | 17/17 |
| A（CUR），r2 | 17 | REPORTED_FAILURE × 17 | 17/17 |

- **A 两次运行之间**：逐字段（class、rc、rc1、rc2、hit、log sha256）差异 **0**。
- **A 与 H 复跑（同一路由、同一运行器）逐条比较**：17 case 的 obs、rc、rc1、rc2、hit、log sha256 **全部相同**（差异 0）。
- **A 的观察与 S2R2 的 T5 记录**（`checkpoints/p05/evidence/p05-s2r2/T5_THREE_WAY_CONSISTENCY.txt` 第 10 行："CUR REPORTED_FAILURE 17"）**一致**。
- 所有 case 的 hit ≥ 1。

### 5.3 对 S2R3 遗留项的关闭

S2R3 报告第 11 节第 7 条记为未闭合："S2R2 的 17 case 缺少同方法的 CUR 复跑"。本轮以 A 树的正式 raw 复跑（两次、逐字段）关闭该项。它证明的是 CUR 观察在同一方法下可复现，并与 H 逐条一致；它不证明 17 case 之外的点。

### 5.4 与 S3R 修复的关系

17 case 的期望与观察在 A 与 H 之间不变，符合"S3R 修复不影响这些点"的预期。这 17 case 覆盖的点是 cache-hit（`t4/`，NTH 7）、kottke work（family D）与 13 个 `s4malloc` 点（T2 登记）；它们不经过 S3R 新增的 `ComputeLayerModes` 与 `AddFieldToCache` 检查，因此一致性是预期结果，不是修复效果的证据。

## 6. R4-4：Jones 舍入差的归因数据（只读，不裁决）

### 6.1 方法

- 脚本 `testing/d003/stage4/opt_jones_r4.sh`（提交 `0782015`）：与 S2R3 的 `opt_jones.sh` 相同的方法（只重编译 `fmm_PolBasisJones.cpp`，用 `ar` 替换库副本中的一个成员，`ranlib`，链接相同驱动源码与 LIBFLAGS），但输出写入 `p05-s2r4/r4-4/`，并**只读**引用 S2R3 的 plain 导出。
- 新增选项：**e** `-O3 -march=native -ffp-contract=off -fcx-limited-range`；**f** `-O3 -march=native -mno-fma -fcx-limited-range`。
- 精度参照：A 树 `-O0`（选项 a，S2R3 已有）。选项 a、b、c、d 的数据沿用 S2R3 阶段 4（`stage4/STAGE4_JONES_TABLE.tsv`），本轮不重算。
- FMA 计数：`objdump -d` 只读反汇编 Jones 目标，统计 `vfmadd|vfnmadd|vfmsub|vfnmsub` 指令条数（**静态计数**，不是执行次数）。
- 默认选项的 Jones 目标已核对：库中成员与独立目标字节相同（A `8177bff9…`，H `fb5f9e33…`），因此 60 与 63 是默认库实际链接的目标上的计数。

### 6.2 数据表（`checkpoints/p05/evidence/p05-s2r4/r4-4/R4_4_TABLE.tsv`）

**第 1 节：A 与 H 的比较**（第一次调用转储，run1；确定性 = 同一二进制 run1 与 run2 相同）

| 选项 | 分量差异（A vs H） | max rel | median rel | 字节一致 | 确定性 A | 确定性 H | FMA A | FMA H |
|---|---|---|---|---|---|---|---|---|
| d `-O3 -march=native -fcx-limited-range`（默认） | 144 / 144 | 1.1829e-12 | 4.3043e-14 | 否 | 是 | 是 | 60 | 63 |
| e `-O3 -march=native -ffp-contract=off -fcx-limited-range` | 0 / 144 | 0 | 0 | **是** | 是 | 是 | 0 | 0 |
| f `-O3 -march=native -mno-fma -fcx-limited-range` | 0 / 144 | 0 | 0 | **是** | 是 | 是 | 0 | 0 |

**第 2 节：精度参照（A 树 `-O0` 转储为参照；只陈述数字，不判断哪方更正确）**

| 对象 | 分量差异（相对参照） | max rel | median rel |
|---|---|---|---|
| A_d（默认） | 144 / 144 | 1.2630e-12 | 4.0610e-14 |
| H_d（默认） | 144 / 144 | 5.7826e-13 | 9.4337e-15 |

数字陈述：H_d 相对参照的最大与中位相对差，分别小于 A_d 相对参照的对应值（5.78e-13 对 1.26e-12；9.43e-15 对 4.06e-14）。这只说明两个非参照对象各自与该参照的距离，不能据此宣称某一方更正确；参照本身也不是真值。

### 6.3 结论（事实）

- 选项 e 与 f 下，A 与 H 的 Jones 场字节一致（144/144，两次运行确定性一致）。
- 选项 d（默认）下，A 与 H 的 Jones 场 144 个分量全部不同，最大相对差 1.1829e-12，与 S3R 报告记录一致。
- 选项 e 与 f 产生的 Jones 目标**字节相同**（A 与 H 各自），FMA 计数均为 0。这两个选项在该函数上等效。
- 默认选项下 FMA 静态计数：A 为 60，H 为 63。

**[推断]**：默认选项下 A 与 H 的差异与编译器对函数体的调度相关（`-march=native` 下的 FMA 融合），而 e、f 去除 FMA 后两侧一致。这与 S2R3 阶段 4 的推断一致。**本轮未验证该机理**（未逐指令比对，未核对 H 的 3 条额外 FMA 与数值差异的对应关系）。

**不在本节决定**：选择 a、b、c、d、e、f 中的哪一个，或是否接受容差，均由用户决定。本节不替用户选择。

## 7. S2 收敛核对表

**判定原则**：**已闭合** = 有实测证据，且证据可复核（文件、命令、哈希可指）；**已接受为已知限制** = 有明确的用户决定，写明限制内容与决定来源；**未闭合** = 证据不足或存在未解决的问题，写明原因。本节**不代替用户判定"S2 已完成"**。

### 7.1 S2 的定义组成（用户提示词）

| # | 组成 | 状态 | 证据与说明 |
|---|---|---|---|
| G1 | 覆盖 S4_malloc | **已闭合（范围内）；范围外已接受为范围决策** | 见 7.2：FMM 翻译单元的 17 处真实调用点均有注入证据；S4.cpp 中纳入范围的 5 处 family C 点已闭合；其余非 FMM 分配按范围决策不在 S2 内。 |
| G2 | 覆盖 LinearSolve | **已闭合（范围内）；范围外已接受为范围决策** | 见 7.3：FMM 的 9 处 LinearSolve 均有注入证据（family A、B、B2、B2-buf）；S4.cpp 2 处与 rcwa.cpp 8 处不在 P05 范围内。 |
| G3 | 覆盖两步分支 | **已闭合**（按 S2 原报告 §4.3 的界定） | plan（真实）、scratch（真实）、exec（边界模拟，不计真实缺陷）；历史 38 案中 `t5/plan1`（5）、`t5/exec1`（5）、`t5/scratch`（2）均有运行与分类（H 复跑 r3 与 S2R3 一致）。 |
| G4 | 接入仓库测试目录 | **已闭合** | 注入器、运行器、判定器、seam 脚本、stage4 脚本均在 `testing/d003/`，已提交（`bdd2b56`、`d8b4276`、`9d29877`、`06acd66`、`0782015`）。 |
| G5 | 源码仅改 testing/（允许必要的测试专用 seam） | **已闭合** | `S4/` 相对 `64eb0b5` 为 0 改动，工作区 `S4/` 相对 HEAD 为 0；本轮提交越界路径 0。seam 只应用于 `git archive` 导出副本。 |

### 7.2 G1 覆盖 S4_malloc 的逐点状态

计数方法：`git show 64eb0b5:<file>`，逐行去掉注释与定义行后计数（只读）。

**FMM 翻译单元（范围内）：17 处真实调用**

| 文件 | 调用点（行，H 树 64eb0b5） | 覆盖证据 | 状态 |
|---|---|---|---|
| `fmm_FFT.cpp` | 75（work）、83（discval） | S2R2 T2 `fft-work-n1`、`fft-discval-n2`；3c.2 NTH 1、2 | 已闭合 |
| `fmm_PolBasisJones.cpp` | 108（ivalues）、155（work）、170（vfield）、346（cache-hit work） | T2 `jones-ivalues-n2`、`jones-work-merge-n3`、`jones-vfield-n4`；T4 `cache-hit-work-k7` | 已闭合（缓存命中为内部路由，见 7.4 U-1） |
| `fmm_PolBasisNV.cpp` | 59、112、125、234 | T2 `nv-ivalues-n2`、`nv-work-n3`、`nv-vfield-n4`；T4 NVVL `cache-hit-work-nv-k7` | 已闭合（同上） |
| `fmm_PolBasisVL.cpp` | 58、117、130、243 | T2 `vl-ivalues-n2`、`vl-work-n3`、`vl-vfield-n4`；T4 NVVL `cache-hit-work-vl-k7` | 已闭合（同上） |
| `fmm_kottke.cpp` | 87（discval；第 77 行为注释） | T2 `kottke-discval-n1`；3c 实测 | 已闭合 |
| `fmm_experimental.cpp` | 40 | 3c.1 `3c1-exp40` | 已闭合 |
| `fmm_closed.cpp` | 40（ivalues） | S2R2 SUPPLEMENT `closed-ivalues-{jones,nv,vl}-n1` | 已闭合 |

**S4.cpp 中纳入范围的 family C 点（5 处）**：`S4.cpp:2267`（id 21，裸 `malloc`，不是 `S4_malloc`）、`2301`（id 22，`S4_malloc`）、`2421`（id 23，`S4_malloc`）、`2446`（id 24，`S4_malloc`）、`4007`（id 25，`S4_malloc`）。依据：S2R 家族 C 可行性（`R2C_S4CPP_FAMILY_C_FEASIBILITY.txt`，Gate 4："五个点在 D003 验收路径上"）。覆盖：S2R3 3b 与 R2D（C-alloc 21–25）。状态：**已闭合**。

**范围外（已接受为范围决策）**：S4.cpp 的 `S4_malloc` 调用共 **36** 处，其中 family C 占 **4** 处（2301、2421、2446、4007），其余 **32** 处为范围外。S4.cpp 的裸 `malloc` 共 12 行（125、286、320、323、1729、1754、1756、2267、3971、3973、4047、4049），其中 2267 属 family C（id 21），其余 11 行为范围外（3971、3973 属 `Simulation_MakeExcitationExterior`）。判据：不在 FMM/FFT 失败传播链上，且不影响模式或缓存的安装（S2R 报告第 8 节与 `P05_S2R_HARNESS_SUPPLEMENT.md` 第 67 行的范围判据）。**此范围划分由用户在 S2R 中确认**，本报告不改写它。

**FMM 翻译单元中未纳入的裸 `malloc`**：PolBasis 的调试文件名分配（Jones 222、NV 170、VL 180）不在模式或缓存安装路径上，不在范围内。`fft_iface.cpp` 的 plan 分配（89、108）经 `--wrap=malloc` 覆盖（S2 plan 注入）。

### 7.3 G2 覆盖 LinearSolve 的逐点状态

**FMM 翻译单元（范围内）：9 处**

| 调用点（H 树） | 请求族（H 或 A） | 覆盖证据 | 状态 |
|---|---|---|---|
| `fmm_FFT.cpp:209`（solve_info） | family A（`linearsolve:1:1:info`，历史 38 案 `s2b/ls-fft-info-k1`） | 历史 38 案 H 复跑 r3 | 已闭合 |
| `fmm_kottke.cpp:284`（solve_info） | family A（`s2b/ls-kottke-info-k1`） | 同上 | 已闭合 |
| `fmm_PolBasisJones.cpp:375` | B2（H，id 375）与 buf-only（id 375）；A 树 family B 15 | R4-1 三列 | 已闭合 |
| `fmm_PolBasisNV.cpp:265` | B2（265）、buf-only（265）；A 树 family B 16 | R4-1 三列 | 已闭合 |
| `fmm_PolBasisVL.cpp:273` | B2（273）、buf-only（273）；A 树 family B 17 | R4-1 三列 | 已闭合 |
| `fmm_closed.cpp:134` | B2（134）、buf-only（134）；A 树 family B 11 | R4-1 三列 | 已闭合 |
| `fmm_closed.cpp:138` | B2（138）、buf-only（138）；A 树 family B 12 | R4-1 三列 | 已闭合 |
| `fmm_closed.cpp:144` | B2（144）、buf-only（144）；A 树 family B 13 | R4-1 三列 | 已闭合 |
| `fmm_closed.cpp:244` | B2（244）、buf-only（244）；A 树 family B 14 | R4-1 三列 | 已闭合 |

**范围外（已接受）**：`S4.cpp:1953`、`2190`（非 FMM 的 LinearSolve）与 `rcwa.cpp` 的 8 处。判据：RCWA 与 dipole 路径，不在 D003 验收路径上。

**H 上的 family B 不存在**（结构性差异，D-U1）：S3R 把 PolBasis 与 closed 的 `NULL` info 改为 `&solve_info`。它的后果已由 R4-1 的 buf-only 与 B2 替代，见 7.4。

### 7.4 G-遗留：已知遗留项

| # | 遗留项 | 状态 | 限制内容 / 原因 | 来源 |
|---|---|---|---|---|
| L1 | 公开 API 路径上的缓存命中 | **已接受为已知限制** | 缓存命中仅经内部接口 `S4_Simulation_DestroyLayerModes` 覆盖（路由 `S4FMM_TWICE=slab` + `s4malloc` NTH 7，inj_call 2）；公开 API 路径未测。 | **用户决定 U-1**（本轮 §1）。不写成"不可达"。 |
| L2 | B 上 PolBasis vfield 的类别按模式分裂（fftnv 段错误；fftjones、fftvl 吞掉） | **已接受为已知限制（[未验证]）** | 源码阅读未完整解释，保持 [未验证]，不追查。 | **用户决定 U-2**（本轮 §1）。 |
| L3 | family B 在 H 上无等价点（`N-jones-id15`、`N-nv-id16`；`N-vl-id17` 登记错误） | **已接受为已知限制（结构性差异）** | H 的 PolBasis 与 closed 求解改为 `&solve_info`，family B 锚点消失。以 R4-1 的 buf-only 与 B2 替代行覆盖（3.5、4.4）。 | **用户决定 D-U1**（S2R3）。 |
| L4 | H 的 family-B 对应 = buf-only：输出缓冲等价已证，**但 AddFieldToCache 检查维度未单独隔离** | **未闭合（已部分证据）** | 输出缓冲层：A family B 与 H buf-only 与 H 完整 B2 逐元素相同（3.2）。场层：选项 e、f 下 A 与 H 字节一致（R4-4）。AddFieldToCache 检查（`e83255f`，H 树 Jones 340–342）未做单独隔离；失败路径由 id 25 覆盖（S2R3 3b）。 | 本轮 R4-1 的限制。 |
| L5 | `S4.cpp` 的 `FMMGetEpsilon` 返回值接收点（S2R 清单"handled (captured to fmm_ret)"） | **未闭合** | 该接收点没有建立注入路由（S2R `INJECTION_POINTS.txt` 第 12 行，"seam NOT built in R2-B"）。它是 FMM 失败传播链上的点，**属于范围内**，因此不能按范围决策排除。见 7.5 的行号说明。 | S2R2 §4.3 与 §8.2；本轮核对。 |
| L6 | 七个 info 站点的失败模型只在 H 上以 B2 测得（B 与 A 无 solve 状态检查） | **已接受为已知限制（结构性）** | A 与 B 的 family B 是输出模型，不是失败模型；失败模型的 B 与 A 对照不存在（B 与 A 无 `solve_info` 检查）。 | S2R3 §7（模型标注）。 |
| L7 | 驱动的 RESULT 文字与判定不一致（cache-hit 只看 rc1；`FAILED` 写死为 1） | **已接受为已知限制** | 判定只用事实（rc1、rc2、信号、命中），不读驱动的 PASS/FAIL；历史驱动不改。 | S2R3 D-13、D-14；本轮 §1 硬约束。 |
| L8 | strace 与 `/tmp` 审计仅为抽样 | **已接受为已知限制** | 两次开始与两次结束抽样，不穷尽，不覆盖交互 shell。 | 本轮 §2、§9。 |
| L9 | `driver-all` 与 `driver-all-t4` 同名不同版本（S2R2 §8.2） | **未闭合** | 运行器无法分辨驱动是否具备某功能。本轮未处理。 | S2R2 §8.2。 |
| L10 | 驱动只覆盖 NB=9、固定几何、θ=0（或 θ=30 的注入运行）（S2 §9 第 4 条） | **未闭合** | 其它配置的可达性未测。 | S2 报告第 9 节。 |
| L11 | 第 `S4_malloc` 运行时总数（18）中 16 次经非 FMM 路径（S2 报告 §4.1） | **已接受为范围决策** | 范围外（见 7.2）。 | S2 报告 §4.1 与 S2R 第 8 节。 |
| L12 | 历史 38 案的 18 条期望与观察不符（写于 S2 修复之前） | **已闭合（映射声明）** | R4-2 的 POST-HOC 映射给出 H 新期望与修复来源；历史文件未改；未声明差异 0。 | 本轮 §4。 |
| L13 | S2R2 的 17 case 缺少同方法的 CUR 复跑（S2R3 第 11 节第 7 条） | **已闭合** | R4-3：A 树两次运行，17/17，与 H 逐条一致（差异 0）。 | 本轮 §5。 |
| L14 | 开始 `/tmp` 快照与开始 strace（S2R3 D-1） | **已闭合** | 本轮第 0 步已取得（§2）。 | 本轮 §2。 |
| L15 | `S4.cpp:2369` 的行号描述（S2R2 §4.3 写为"FMMGetEpsilon 返回值接收"） | **已闭合（更正）** | 见 7.5。 | 本轮核对。 |

### 7.5 L15：S4.cpp:2369 的行号更正（本轮核对）

- **B（37a82e8）与 A（876181c）**：`S4/S4.cpp:2368–2369` 为 `FMMGetEpsilon_Experimental` 的调用与 else 分支，2369 行附近是 FMM 调用的返回位置（S2R `INJECTION_POINTS.txt` 第 12 行所记）。
- **H（64eb0b5）**：S3R 的修改使该位置移动。`S4/S4.cpp:2369` 现为 `const int eigen_info = SolveLayerEigensystem(...)`；FMM 调用（`fmm_ret = FMMGetEpsilon_*`）位于 2382–2407。
- **更正**：S2R2 §4.3 与 §8.2 把 `S4.cpp:2369` 写为"FMMGetEpsilon 返回值接收"，这一行号对应的是 B/A 树。在 H 树上，同一 FMM 返回接收位于 2382–2407，**并非 2369**。L5 的注入路由应按 H 树锚点（`fmm_ret = FMMGetEpsilon_*` 行）建立。

### 7.6 S2 收敛核对表（汇总）

| 组成 / 遗留项 | 状态 |
|---|---|
| G1 覆盖 S4_malloc | 已闭合（范围内）；范围外为范围决策 |
| G2 覆盖 LinearSolve | 已闭合（范围内）；范围外为范围决策 |
| G3 覆盖两步分支 | 已闭合 |
| G4 接入仓库测试目录 | 已闭合 |
| G5 源码仅改 testing/ | 已闭合 |
| L1 公开 API 缓存命中 | 已接受为已知限制（U-1） |
| L2 B 上 vfield 分裂 | 已接受为已知限制（U-2，[未验证]） |
| L3 H 上无 family-B 点 | 已接受为已知限制（D-U1，结构性） |
| L4 AddFieldToCache 检查维度未隔离 | **未闭合**（部分证据） |
| L5 FMMGetEpsilon 返回接收的注入路由 | **未闭合** |
| L6 失败模型仅在 H 测得 | 已接受为已知限制（结构性） |
| L7 驱动 RESULT 文字不一致 | 已接受为已知限制 |
| L8 strace 与 /tmp 审计为抽样 | 已接受为已知限制 |
| L9 driver-all 同名不同版本 | **未闭合** |
| L10 配置范围 | **未闭合** |
| L11 非 FMM 分配 | 已接受为范围决策 |
| L12 历史期望映射 | 已闭合 |
| L13 S2R2 17 case CUR 复跑 | 已闭合 |
| L14 开始快照与 strace | 已闭合 |
| L15 2369 行号 | 已闭合（更正） |

**本核对表不代替用户判定"S2 已完成"。** 未闭合项共 **4 项**：L4（AddFieldToCache 检查维度）、L5（FMMGetEpsilon 返回接收的注入路由）、L9（驱动同名不同版本）、L10（配置范围）。这 4 项须由用户裁决：是否纳入 S2，或另立条目。

## 8. 偏离与违规（单一表）

依据：`checkpoints/p05/evidence/p05-s2r4/VIOLATIONS_AND_DEVIATIONS_S2R4.txt`（证据，不提交）。本表是报告中违规次数的唯一来源。

### 8.1 写仓库外路径的违规尝试（唯一的违规次数表）

| # | 轮次 | 命令（摘要） | 是否落盘 | 说明 |
|---|---|---|---|---|
| 1 | S2R3 首轮（上一轮，已自行披露） | `git show ... > /tmp/__never_write` | **无法确定** | 上一轮的执行者在 S2R3 首轮输出中披露。本仓库全文检索 `never_write` 无匹配，无法判断它与更早轮次（`P05_S2_TEST_HARNESS.md` 的 D-1 与 P-1 条目：`/tmp/x`、`/tmp/__nope`、`/tmp/__ev_check_ignored`、`/tmp/__files_a`、`/tmp/__a`、`/tmp/__x`）是否为同一次。按披露记为已披露的尝试，不记为已确认的落盘。 |
| 2 | S2R4 本轮（R4-5 清单） | `find ... > /tmp_no_write_check_placeholder`（重定向到文件系统根下的路径，不在 `/tmp` 下） | **否** | 文件系统返回 `Read-only file system`，`ls -la` 确认路径不存在。同一命令带 `2>/dev/null`，拒绝信息只出现在工具的 stderr 部分。本轮自行披露。 |

**本轮自查**：除上表第 2 行外，本轮的 shell 命令未写入 `/tmp` 或仓库外路径。含 `/tmp` 字面量的命令均为只读（`ls -A /tmp`、仓库内检索）。自查依据是回顾命令历史，**不是系统审计**；strace 抽样只覆盖被跟踪的进程，不覆盖交互 shell。

### 8.2 其它偏离（逐条，均已纠正或披露）

| 编号 | 偏离 | 纠正 |
|---|---|---|
| D-1 | R4-1 的期望未在探索性运行前登记 | 以 POST-HOC 登记补登（`REG_R4_1_POSTHOC.tsv`），所有行标 POST-HOC INFLUENCED。 |
| D-2 | 第一次缓冲比较把 H 的 buf 输出与 A 的 pre-change 对照配对（错误配对） | 改为与同一树（H）的 pre-change 对照比较。未改变注入器行为。 |
| D-3 | 正对照探针使用相对路径进入错误目录，rc 127 | 删除探针目录（绝对路径核对后），改绝对路径重跑。 |
| D-4 | gdb：断点条件用了无调试信息的变量；随后驱动参数未传入（usage，退出码 2） | 改为寄存器传参并使用 `--args`。HOME 重定向到仓库证据目录。 |
| D-5 | 库副本以文件名（而非成员名）插入，成员变为 `A-seam-jones-c.o` | 绝对路径核对后删除副本，以成员名 `fmm_PolBasisJones.o` 重建。 |
| D-6 | 运行器拒绝 `linearsolve_null2buf:`（前缀未追加） | 预期行为，与注入器改动同一提交修正。 |
| D-7 | 第一版 gdb B2 脚本使用 family B 的寄存器映射（B2 多一个 info 参数） | 改为 rdi、rsi、rdx、rcx、r8、r9 的映射。 |
| D-8 | POST-HOC 登记中树名 `A` 被运行器拒绝（bad tree） | 冻结前映射为 `CUR`；草稿保留（未登记）。 |
| D-9 | 任务书的"20 条"为估计 | 按实际清点为 26 行映射（25 条不匹配 + 1 条替代行）。 |
| D-10 | R4-5 清单计数误报为 48 | 错误在于我自己的检查起始行（`NR>7` 应为 `NR>6`）；清单本身完整，实为 49 条。 |
| D-11 | R4-4 的确定性列先写了占位与多余的 `cmp` 行 | 显式重算 run1 与 run2 后重写表格。 |
| D-12 | S2R2 把 `S4.cpp:2369` 写为 FMMGetEpsilon 返回接收 | 在 H 树中 2369 为 `SolveLayerEigensystem`；B 与 A 中 2369 为 FMM 返回。L5 的锚点应为 H 的 `fmm_ret` 接收（2382–2407）。第 7.5 节更正。 |

### 8.3 本轮未进行的动作

- 未取得"开始"之外的快照与 strace（结束阶段的快照与抽样见第 9 节）。
- 未修改 `S4/`、未修改历史登记、未修改 `judge_d003.py`、`matrix_d003.py`、`driver_d003.cpp`。
- 未在结束阶段之前宣布任何阶段完成。

## 9. 仍未闭合缺口、收尾核对与路径清单

### 9.1 仍未闭合的缺口（来自第 7.4 节）

| # | 缺口 | 原因 | 需要的决定 |
|---|---|---|---|
| L4 | `AddFieldToCache` 检查维度未单独隔离 | 本轮只隔离了 solve 状态维度（buf-only）；正常路径的场一致（选项 e、f）为间接证据。 | 用户决定是否需要 AddFieldToCache 的单独隔离实验。 |
| L5 | `FMMGetEpsilon` 返回接收点的注入路由未建立 | 该点属于 FMM 失败传播链（范围内），S2R 标注 "seam NOT built"。本轮按任务要求只建立登记与核对表，未新增注入。 | 用户决定是否在 S2 内补建该路由（需 H 树锚点）。 |
| L9 | `driver-all` 与 `driver-all-t4` 同名不同版本 | 运行器无法分辨驱动功能。 | 用户决定是否统一驱动命名。 |
| L10 | 配置范围仅 NB=9、固定几何、θ=0（或 θ=30 注入） | 其它配置未测。 | 用户决定是否扩展配置范围，或接受为限制。 |

已接受为已知限制（不再追查）：L1（公开 API 缓存命中，U-1）、L2（B 上 vfield 分裂，U-2，[未验证]）、L3（H 上无 family-B 点，D-U1）、L6（失败模型仅在 H 测得）、L7（驱动 RESULT 文字）、L8（审计为抽样）。已闭合：L12、L13、L14、L15。

### 9.2 收尾核对（结束阶段）

| 项 | 结果 |
|---|---|
| `git status` | 见 9.4（提交本报告后核对） |
| `S4/` 相对 `64eb0b5` 改动 | **0**（已核对，第 7.1 节 G5） |
| 本轮提交的越界路径数（相对 `1509c41`） | **0**（全部在 `testing/d003/` 与 `checkpoints/p05/` 内） |
| `/tmp` 顶层快照（结束） | 见 9.3 |
| strace 抽样（结束） | 见 9.3 |

### 9.3 `/tmp` 快照与 strace：开始与结束两对

| 时点 | `/tmp` 顶层（条目数，sha256） | strace 抽样（命令，事件数，`/tmp` 事件，仓库外写入型 open） |
|---|---|---|
| 开始（第 0 步） | 0，`e3b0c442…` | `git status --porcelain`，269，0，0 |
| 结束 | 0，`e3b0c442…` | `git status --porcelain`，280，0，0 |

两对结果一致：`/tmp` 顶层在开始与结束均为空；两次抽样中 `/tmp` 事件与仓库外写入型 open 均为 0。证据：`strace-start-git-status.strace`、`strace-end-git-status.strace`。

strace 只跟踪被运行的进程及其子进程，不覆盖交互 shell 命令，也不是穷尽审计。

### 9.4 结束核对与提交

- `S4/` 相对 `64eb0b5` 改动：**0**（提交前核对）。
- 本轮提交的越界路径：**0**。
- 结束 `/tmp` 与 strace：见 9.3。
- 本报告的提交：见 9.5 的提交表；提交后 `git status` 与越界核对在提交后核对（见本轮对话的最终记录）。

### 9.5 路径清单

**报告与证据**：
- 报告：`checkpoints/p05/P05_S2R4_CLOSEOUT.md`
- digest 段落：`checkpoints/p05/S1_evidence_digest.txt`（末尾追加）
- 证据（不提交）：`checkpoints/p05/evidence/p05-s2r4/`
  - `PROGRESS_CHECKPOINT.txt`、`OPENING_CHECK.txt`、`VIOLATIONS_AND_DEVIATIONS_S2R4.txt`
  - `strace-start-git-status.strace`
  - `r4-1/`（REG_R4_1_POSTHOC.tsv、blocks/、fields/、optc/、formal/、ctl-buf-post/、gdb/、regress-r4-1）
  - `r4-2/`（MAP_4_POSTFIX.tsv、hist38-H-r3/、r2d-H-r3/）
  - `r4-3/`（MAP_R4_3_S2R2_CUR.tsv、s2r2-CUR-r1/、s2r2-CUR-r2/）
  - `r4-4/`（R4_4_TABLE.tsv、opt-A-e/、opt-H-e/、opt-A-f/、opt-H-f/、opt-*-d-default.disasm.txt）
  - `r4-5-s2r3-list.txt`、`r4-5-s2r4-list.txt`、`copied-files.txt`、`manifest-files.txt`

**提交（仅 `testing/d003/` 与 `checkpoints/p05/`）**：

| 提交 | 内容 |
|---|---|
| `06acd66` | R4-1：注入器 B2-buf 模式、`apply_seam_r4_buf.py`、运行器前缀 |
| `0782015` | R4-4：`testing/d003/stage4/opt_jones_r4.sh` |
| `3367d4e` | R4-5：`checkpoints/p05/registries/`（s2r3 36 个文件、s2r4 13 个文件、MANIFEST.tsv 49 条，合计 64955 字节） |
| 本报告提交 | 报告与 digest 段落（awaiting user review） |

**复现包**：`checkpoints/p05/registries/MANIFEST.tsv`（49 条，sha256 与字节数已逐条核对）。

**状态**：未完成，等待用户审核。P05-S1、P05-S2、P05-S3、P05-S4 均未被宣布完成。
