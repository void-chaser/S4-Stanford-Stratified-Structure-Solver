# P05-S1R2 收尾报告：S1R 遗留项独立检验轮

> **状态：未完成，等待用户审核。** 本报告不宣布 P05-S1、P05-S2、P05-S3、P05-S4 任一阶段完成。本轮所有结果称"装置观察"或"探针观察"，不称"验证"。

## 1. 定位

- 本轮是正式阶段 **P05-S1** 的补充子任务，不是新阶段。P05 固定五阶段 S1–S5，本轮不引入 S6。
- 历史报告与文件名未改写；更正只写在新文件中。
- 起点：HEAD `812d6b7`（含 D016、R-P05-01 的提前登记提交）；分支 `codex/p05-d003-fft-error-propagation`；`S4/` 相对 `64eb0b5` 改动 0；开工工作区干净。
- 本轮对 S1R 对账报告第 4 节"悬而未决项"中的第 3、4、5、7 项逐个检验（J1–J4），第 1、2、8、9 项记录在案（J5）。
- 本轮不修改源码（`S4/` 相对 `64eb0b5` 保持 0 改动）。发现的问题只记录、分类、给出建议与最小复现，不处理。

## 2. 阶段定义依据

- 阶段定义依据用户给出的提示词（任务书）。仓库内无 P05 原始计划文档，本报告不再搜索原文。
- P05-S1：基线与复现（枚举调用点、在 Master 上复现静默吞错、核实 VL NB1，交付报告与原始日志，不改源码）。
- P05-S3：最小修复（从候选分支移植到 Master，补齐缺口，FMM 改动与 `S4.cpp` 调用点改动分开提交，源码需修改）。
- 本轮不实施 S3 的任何修复。

## 3. 授权、边界与用户决定

### 3.1 授权边界（任务书第 1 节）
- 不修改 `S4/` 下任何文件；不修改已提交的报告原文；不修改 `testing/s4test/ISSUE_REGISTRY.md` 与 `PROJECT_ROADMAP.md`（只读引用）。
- 可修改：`testing/d003/`（仅新增脚本，位于 `testing/d003/stage_s1r2/`）、`checkpoints/p05/`（新文件）。
- 不修改 `testing/d003/judge_d003.py`（sha256 应为 `d2d04145…`，见第 13 节路径清单的核对）。

### 3.2 O-1（VL NB=1）归属（用户已确认并已登记，本轮只引用）
- 根因（零场除零得到 NaN）属数值边界；"NaN 产生后仍返回成功、错误信号在传播链上丢失"属于 D003 失败传播范围，已登记为 **D016**，最小修法进入 S3。
- **R-P05-01**（"让 VL NB=1 真正可计算"）暂不处理，不进 S3，不阻塞 P05。
- 登记位置：`testing/s4test/ISSUE_REGISTRY.md` 的 D016 行（第 41 行）与"后续登记"表的 R-P05-01 行（第 114 行）；`PROJECT_ROADMAP.md` 第 6 节（第 145–146 行）。

### 3.3 范围判据（用户已定）
凡属于求解器 FMM/FFT 路径上的缺陷，即其失败影响"模式或缓存是否被安装"，或位于 FMM/FFT 失败传播链上，发现问题都进入 S3 输入。
- 第 3 项（半覆盖）：属于，进 S3 输入（本轮结果：未观察到混合状态，无新 S3 输入，见 J1）。
- 第 4 项（kottke 除数）：属于，进 S3 输入（见 J2）。
- 第 5 项（`shape_get_normal` 下标）：属于，发现的是差一而非越界，归属需用户裁决（见 J3）。

### 3.4 用户决定（任务书第 1 节第 3 条，已知限制来源）
见第 10 节。

## 4. 起点哈希与开工核对

| 项 | 值 | 来源 |
|---|---|---|
| HEAD | `812d6b7580d98a19e46f42cb484b1824d3a8820f`（短 `812d6b7`） | `git rev-parse HEAD` |
| 分支 | `codex/p05-d003-fft-error-propagation` | `git branch --show-current` |
| `S4/` 相对 `64eb0b5` 的 diff 行数 | 0 | `git diff 64eb0b5 HEAD -- S4/` |
| 工作区 | 干净 | `git status --short` 开工时为空 |
| `B = 37a82e8` 的 `S4/` 树哈希 | `1d738e64f9864a475fdb3de34cd3601605df2c64` | `git rev-parse 37a82e8:S4` |
| `5b72793` 的 `S4/` 树哈希 | `1d738e64f9864a475fdb3de34cd3601605df2c64`（与 B 相同） | `git rev-parse 5b72793:S4` |
| `testing/d003/judge_d003.py` sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`（一致） | `sha256sum` |

- 三棵树：B = `37a82e8`（库哈希 `fb9ac3f5…`），A = `876181c`（库哈希 `865c5893…`），H = `64eb0b5`（库哈希 `f053bfea…`）。三棵树均由 `git archive` 导出到证据目录后各自构建。
- B 的 `S4/` 与 `5b72793` 树哈希相同，开工时已核对（一致）。

## 5. 已知限制（用户决定，来源标注）

以下限制由用户确认（任务书第 1 节第 3 条），写入本轮报告，来源标为"用户决定"：

- **(a)** 驱动二进制不能由历史记录逐字节复现（原因：注入器修订不同）。S3、S4 使用当前注入器重新构建并重新固定哈希。
- **(b)** 历史 38 案只能分类重放（运行记录无驱动路径，信息已丢失）。
- **(c)** S2R2 的 17 案与 R2-D 的 13 案保持独立步骤，不并入统一入口。
- **(d)** 违规表第 1 行（S2R3 `/tmp/__never_write`）定稿为：当前未发现落盘痕迹；无法证明历史时刻未落盘。
- **(e)** 新尺子（当前注入器、当前统一入口）在 B/A/H 三树上重新得到的结果，可用于核对结论（类别），不用于还原历史过程。

## 6. 偏离与说明

- **6.1 J1 期望更正（运行前）**：初稿写"A 树 FFT 与 PolBasis 之间没有串接"，经核对（`876181c` 的 `S4.cpp` 第 2376 行 `if(0 == fmm_ret && …)`）为错误。已在期望文件正文更正，并以注记 C1、C2 保留原误述。未运行任何探针时更正，故不构成 POST-HOC。
- **6.2 J1 分类器两次修正**（运行后，已保留旧版输出）：
  - v1（`J1_classification_v1_PRE_FIX.tsv`）把 `Epsilon_inv` 计入矩阵判定，正常路径误判为 MIXED；v2 只以 Epsilon2 的四个块判定。
  - v2 把有信号的 PolBasis 返回（SIGSEGV）误判为 FFT_ORIGINAL；v3 以信号判为 CRASHED（`J1_full_matrix_compare_v1_PRE_CRASH_FIX.tsv` 保留旧版）。
  - 两次修正都发生在统计之后、结论之前，结论按修正后版本写出。这些修正在本节披露。
- **6.3 J2 期望与实测不一致（运行后，已对照）**：E5（非有限被映为 0、不进入输出）不成立；Y1（除零）不成立，Y2（溢出阈值）成立。期望文件未修改，对照记录见 `J2_EXPECTATION_VS_OBSERVED.txt`，标注 **INFLUENCED**。
- **6.4 J3 期望补充（运行后）**：首轮 J3 运行后发现"重叠区域"未被覆盖（同心为父子，两不相交圆无公共像素）。补充期望 S-OVL 于补跑前（12:34:55Z）固定。
  - 注意：`J3_EXPECTATIONS.sha256`（12:25:55Z）对当前 `J3_EXPECTATIONS.txt` 校验为 FAILED，原因是在其后追加了 S-OVL 段（追加，正文未改）。首轮 J3 的期望对照以 12:25:55Z 版本为准；S-OVL 为事后补充期望，已在其运行前固定，并以 `J3_OVERLAP_EXPECTATIONS.sha256` 记录。
  - 另：J3 的两个探针二进制在 `overlap` 分支加入后重新编译（`j3-shape-probe-{B,A,H}` 哈希已变）。首轮 concentric 与 two_disjoint 的运行使用旧二进制；新分支不改变已有布局的代码路径（仅新增分支）。
- **6.5 J3 的 gdb 脚本修改**：`gdb_j3_normal.gdb` 与 `shape_index_stats.py` 在运行后做过一次修正（单形状的 stride 处理），修正前输出保留为 `J3_index_stats_n1_PRE_FIX.tsv`。
- **6.6 J2 期间的编译链接错误**：探针最初带 `--wrap` 链接，产生大量 `undefined reference`；已改为不带 `--wrap` 的公共 API 探针（记入第 9 节表二）。
- **6.7 J6 的 gdb 栈读取失败**：`pattern_generate_flow_field` 的第 8 个参数未能用 `rsp+16` 读取（得到栈地址）。未用于任何结论；max_field 的数值引用 S1R 的实测并标注（见 J6 前提标注）。

## 7. J1：半覆盖场景（S1R 对账第 4 节第 3 项）

### 7.1 期望（运行前登记）
- 文件：`checkpoints/p05/evidence/p05-s1r2/J1_EXPECTATIONS.txt`。登记时间戳 `12:13:22Z`（`J1_EXPECTATIONS_TIMESTAMP_UTC.txt`），哈希 `f8a7ba02…`（`J1_EXPECTATIONS.sha256`）。
- B：失败发生在 PolBasis 内部分配之后；FFT 已写 Epsilon2 与 Epsilon_inv；PolBasis 的 `S4_malloc` 无 NULL 检查；FFT 与 PolBasis 返回值在 `ComputeLayerModes` 中被丢弃。
- A：FFT 与 PolBasis 已串接（更正 C1）；PolBasis 返回值写入 `fmm_ret`；失败时 `DiscardLayerModes` 并返回 20。
- H：PolBasis 失败时 `ComputeLayerModes` 返回 20 并 `DiscardLayerModes`，矩阵不被安装。
- 期望中"若出现混合状态，记为新观察"——实测未出现混合状态（见 7.3）。

### 7.2 探针设计与方法
- 三树（B、A、H）× 三链（`fftjones`、`fftnv`、`fftvl`）× 注入（无注入、`S4_malloc` 的 NTH 3、4、5）。
- NTH 对应点位由 gdb 回溯直接确认（`J1_nth_map_fftvl_H.txt`）：NTH1、2 为 FFT（6144、16 字节），NTH3、4、5 为 PolBasis（192、11872、1024 字节）。与 REG_3C2 一致。
- 读取：gdb 在 `FMMGetEpsilon_PolBasis*` 入口与返回（`finish`）处读取 **Epsilon2 的全部 324 个元素** 与 **Epsilon_inv 的全部 81 个元素**，逐位比较（`J1_DUMP/`，`compare_j1_dump.py`）。
- 驱动运行（不经 gdb）取 rc1、命中数、RESULT 行。
- 比较基准：入口状态即 FFT 写入后的状态（PolBasis 前）。

### 7.3 矩阵内容与最终类别（[实测]）

| 树 | 链 | 注入 | 矩阵内容（Epsilon2，324 元素） | PolBasis 返回 | 驱动 rc1 | 命中 | 最终类别 |
|---|---|---|---|---|---|---|---|
| B | fftjones | NTH3 | CRASHED（SIGSEGV 于 PolBasis 内） | 无 | — | 1 | CRASH |
| B | fftjones | NTH4 | CRASHED | 无 | — | 1 | CRASH |
| B | fftjones | NTH5 | FFT 原值（逐位不变） | eax = −8 | 0 | 1 | SILENT_SWALLOW |
| B | fftnv | NTH3 | CRASHED | 无 | — | 1 | CRASH |
| B | fftnv | NTH4 | CRASHED | 无 | — | 1 | CRASH |
| B | fftnv | NTH5 | CRASHED | 无 | — | 1 | CRASH |
| B | fftvl | NTH3 | CRASHED | 无 | — | 1 | CRASH |
| B | fftvl | NTH4 | CRASHED | 无 | — | 1 | CRASH |
| B | fftvl | NTH5 | FFT 原值（逐位不变） | eax = −8 | 0 | 1 | SILENT_SWALLOW |
| A | 三链 | NTH3/4/5（9 格） | FFT 原值（逐位不变） | eax = 1 | 20 | 1 | REPORTED_FAILURE |
| H | 三链 | NTH3/4/5（9 格） | FFT 原值（逐位不变） | eax = 1 | 20 | 1 | REPORTED_FAILURE |

- "FFT 原值"：Epsilon2 的 324 元素与入口逐位相同，Epsilon_inv 的 81 元素亦不变（`J1_full_matrix_compare.tsv`，v3 判定）。
- 无注入对照（nthnone，PolBasis 成功）：Epsilon2 的 324 元素全部改变（NEW_VALUES），Epsilon_inv 不变，与源码（PolBasis 写 Epsilon2、不写 Epsilon_inv）一致。
- 入口状态：Q00 与 Q11 块为 FFT 写入的非零值；Q10 与 Q01 块为 0（标量材料下 `fxy = fyx = 0`，`fmm_FFT.cpp` 第 119–122 行，[源码]）。
- B 的 `eax = −8`：来自 `pattern_generate_flow_field` 的参数检查（`pattern.c:2106`，`field == NULL` → −8），由 gdb 在该函数的 `ret` 处读取确认（`FLOW_RET k=1 eax=-8`，`J1_flowret_B_fftvl_nth5.txt`，[实测]）。B 的 PolBasis 不检查 `vfield`，把 −8 原样返回，`ComputeLayerModes` 丢弃之。
- 注意：REG_3C2 的历史类别与上表一致（B: CRASH / SILENT_SWALLOW；A、H: REPORTED_FAILURE）。

### 7.4 归属与"是否继续使用"（[实测]）
- **证据等级**：逐条交错顺序（`CLM_RET` 与 `SOLVE_CALL` 的先后）只在 H-fftvl-NTH3 上逐条记录（`J1_install_H_fftvl_nth3.txt`，`order-H-fftvl-nth3.txt`）。其余格为计数证据（`J1_CLM/` 与 `J1_CLM_order_check.txt`）。
- **A、H（18 个注入格）**：第 2 次 `ComputeLayerModes` 返回 20，且其之前 `SolveLayerEigensystem` 调用次数为 0。失败的矩阵未送入求解。
- **无注入对照（6 格）**：第 2 次返回 0，且之前已有 2 次求解。
- **B NTH5（SILENT_SWALLOW）**：PolBasis 返回 −8，`ComputeLayerModes` 返回 0，随后 `SolveLayerEigensystem` 被调用 2 次。即 B 上失败被吞，FFT 原值被直接用于求解。
- **B NTH3/4（CRASH）**：崩溃于 PolBasis 内，`ComputeLayerModes` 未返回，无求解调用。

### 7.5 缓存（[实测]）
- H-fftvl 的 `Simulation_AddFieldToCache` 调用次数：无注入 1、NTH3 1、NTH4 1、NTH5 1（`J1_CACHE/cache-H-fftvl-*.txt`）。
- NTH3 的交错顺序（`order-H-fftvl-nth3.txt`）：`CLM_RET k=1 eax=0` → HIT → `CLM_RET k=2 eax=20` → **`ADDCACHE k=1`** → `CLM_RET k=3 eax=0` → `CLM_RET k=4 eax=0`。
- 即：唯一的一次缓存写入发生在失败的那次调用**返回之后**，属于重试（第二次 `GetFieldPlane`）中的成功 PolBasis 计算。**失败路径未写入缓存。**
- 源码顺序（[源码]）：`AddFieldToCache` 位于 `fmm_PolBasisVL.cpp` 第 237 行，三个注入分配（第 58、117、130 行）均位于其之前。
- 未覆盖：PolBasis 内 `AddFieldToCache` 之后的分配（第 243 行，缓存命中分支）未注入（超出 NTH 1..5）。

### 7.6 结论（按任务书第 J1-4 条格式）
- **半覆盖（混合状态）：未观察到。** 在所有有返回的注入格中，矩阵均为完整的 FFT 原值，没有任何块被部分改写。因此**不写"半覆盖已证实"**。
- 理由：PolBasis 的分配失败点（`ivalues`、`work`、`vfield`）位于它写入 Epsilon2 之前，失败不会留下部分写入。该理由由源码（写入顺序）与实测（逐位不变）共同支持。
- 对 CRASHED 格：矩阵内容不可断言（崩溃时刻的状态，gdb 的 `finish` 在 SIGSEGV 后读取的值不是正常返回的值）。
- 对每个（树，链）：
  - B fftjones：NTH3/4 崩溃；NTH5 矩阵为 FFT 原值，失败被吞。
  - B fftnv：NTH3/4/5 全部崩溃。
  - B fftvl：NTH3/4 崩溃；NTH5 矩阵为 FFT 原值，失败被吞。
  - A、H 三链：NTH3/4/5 矩阵为 FFT 原值，返回 20，不进入求解，不缓存。

### 7.7 停止条件检查（任务书第 5 条）
- **H 上失败后矩阵仍被安装或缓存**：否（见 7.4、7.5）。未触发停止条件。

### 7.8 J1 的未闭合
- PolBasis 内 `AddFieldToCache` 之后的分配（缓存命中分支）矩阵状态未测。
- 单一几何（圆形图案，NB=9，4×3 采样）与单一标量材料对；未测其他几何与张量材料。
- Jones、NV 的 CRASH 格的崩溃后状态未进一步探测。

## 8. J2：kottke 除数安全性（S1R 对账第 4 节第 4 项）

### 8.1 除法位置（按内容，`fmm_kottke.cpp`；B、A、H 的除法行相同，三对树的 diff 中除法行改动数均为 0）
kottke 平均段（仅 `nnz == 2`、`imat` 不同、`nvec` 非零时执行）：

| 编号 | 表达式（按内容） | 除数来源 |
|---|---|---|
| D1 | `-1./abcd[0][0]` | `abcd[0][0]` = 第 1 材料旋转后的 e11 = `nᵀ M₁ n` |
| D2 | `-1./abcd[1][0]` | `abcd[1][0]` = 第 2 材料旋转后的 e11 |
| D3 | `abcd[0][1]/abcd[0][0]`、`abcd[0][2]/abcd[0][0]` 等 | `abcd[0][0]` |
| D4 | `abcd[1][1]/abcd[1][0]`、`abcd[1][2]/abcd[1][0]` 等 | `abcd[1][0]` |
| D5 | `abcd[0][1]*abcd[0][2]/abcd[0][0]`、`abcd[1][1]*abcd[1][2]/abcd[1][0]` | 同上 |
| D7 | `-1./abcde[0][0]` | `abcde[0][0]` = `fill·(−1/abcd₀₀) + (1−fill)·(−1/abcd₁₀)`（平均后的 τ 的 e11，由 `fill` 决定） |
| D8/D9 | `-abcde[0][1]/abcde[0][0]`、`-abcde[0][2]/abcde[0][0]`、`abcde[0][1]*abcde[0][2]/abcde[0][0]` | `abcde[0][0]`（同 D7） |

其它除法（与材料无关，不属 J2 范围）：`1./(double)ng2`；`/(double)ngrid[·]`（网格数恒正）。

### 8.2 取值范围（[源码]）
- 材料类型：标量实（2）、标量复（3）、张量实（4）、张量复（5）（`S4.h` 150–153）。
- `S4_Simulation_SetMaterial`（`S4.cpp` 888–965）：标量与张量各分量直接复制，**无零值、无非有限值、无正定性校验**。唯一拒绝的是 `type` 不在四种类型内。
- `sym2x2rot`（`fmm_kottke.cpp` 44–53）：`abcd[i][0] = nx²M₀₀ + nx·ny(M₀₁+M₁₀) + ny²M₁₁`。
- 标量材料：`abcd[·][0] = eps`（|n| = 1）。因此 eps 为 0 时 D1、D2 的除数为 0。
- 因 API 不校验，`eps = 0` 与极小 eps 的材料均可被构造。

### 8.3 探针（运行前登记：`J2_EXPECTATIONS.txt`、`J2_P2C_EXPECTATIONS.txt`、`J2_P2D_EXPECTATIONS.txt`）
- 探针程序 `testing/d003/stage_s1r2/kottke_probe.cpp`：仅调用公共 API（`S4.h`），不依赖注入器；图案为圆（半径 0.25，与驱动一致），背景 eps = 1，kottke 模式，NB = 9。
- 求解器入口检查（gdb，`SolveLayerEigensystem` 的 `Epsilon2` 与 `Epsilon_inv` 前 8 个复数）。

| 探针 | 标量 eps | 求解器入口 Epsilon2 | 崩溃 | 驱动退出码 |
|---|---|---|---|---|
| 对照（P2 烟测） | 4 | 有限 | 否 | 0 |
| P2-A | 0 | **NaN（8/8）** | **是**（zlaqr0_） | 139 |
| P2-B（张量 e11=−1, e22=1, ezz=1） | — | 有限 | 否 | 0 |
| P2-C1 | 1e-300 | **NaN（8/8）** | **是** | 139 |
| P2-D 扫描 | 1e-6 | 有限 | 否 | 0 |
| P2-D 扫描 | 1e-12 | 有限 | 否 | 0 |
| P2-D 扫描 | 1e-100 | 有限 | 否 | 0 |
| P2-D 扫描 | 1e-300 | **NaN（8/8）** | **是** | 139 |

- **三树一致**（`J2_TREES/`）：B、A、H 上 eps = 0 与 1e-300 均 NaN + SIGSEGV（退出 139），eps = 1e-100 均正常（退出 0）。
- 栈追踪（[实测]）：`Simulation_GetLayerSolution` → `Simulation_ComputeLayerSolution` → `Simulation_ComputeLayerModes` → `SolveLayerEigensystem`（2 次进入）→ `zlaqr0_`（SIGSEGV）。

### 8.4 期望与实测（`J2_EXPECTATION_VS_OBSERVED.txt`，INFLUENCED）
- E5（非有限被 `-1/x` 映为 0，不进入输出）**不成立**：NaN 确已进入 Epsilon2 并送入求解器。
- Y1（除零，与 eps 量级无关）**不成立**：eps = 1e-6 至 1e-100 入口有限。
- Y2（存在溢出阈值）**成立**：阈值在 1e-100 与 1e-300 之间。
- 机理 [推断]：阈值与 `(1/eps)²` 超过 double 上限（约 1.8e308）的量级相符（eps 约 1e-154 量级）。**未经逐元素实测确认**，中间量在 kottke 的局部变量中未能直接读取。P2-A（eps = 0）与 P2-C1（eps = 1e-300）同样产生 NaN，二者的 NaN 机理（除零 vs 溢出）未逐元素区分。

### 8.5 分类（按 J2 第 4 条）
- 不可达（输入校验阻止）：**否**（API 无校验，且 eps = 0 实测成功构造、运行）。
- 可达且产生非有限值但被后续检查报告：**否**（无检查；进程 SIGSEGV，无错误码）。
- **可达，且产生非有限值，未被拦截，进入求解器后进程崩溃。** 这属于最严重的一类（无报告的崩溃）。
- 静默：不是（它是崩溃）。
- 不可判定：机理的逐元素来源（除零 vs 溢出）不可判定。

### 8.6 范围判据
kottke 在 FMM 路径内，非有限值进入 Epsilon2 并导致求解器崩溃，影响"模式是否被安装"（模式未被安装，进程终止）。按判据**列入 S3 输入**（见第 12 节）。

### 8.7 张量路径（未验证）
- D7 为零的条件为 `fill·abcd₁₀ + (1−fill)·abcd₀₀ = 0`。对 `fill = 0.5`，需 `abcd₁₀ = −abcd₀₀`。
- 仅测了一个非正定张量（P2-B，e11 = −1）：正常返回，Epsilon2 有限。**未证实张量路径的可达性**，单点结果不能推广。

### 8.8 最小复现
- `FMM_MODE=kottke J2_MAT=scalar_real J2_EPS=0 ./j2-kottke-probe-H` → 退出 139（SIGSEGV）。
- `FMM_MODE=kottke J2_MAT=scalar_real J2_EPS=1e-100 ./j2-kottke-probe-H` → 退出 0（对照）。
- 探针源码：`testing/d003/stage_s1r2/kottke_probe.cpp`；二进制：`evidence/p05-s1r2/drivers/j2-kottke-probe-{B,A,H}`。

## 9. J3：`shape_get_normal` 下标界限（S1R 对账第 4 节第 5 项）

### 9.1 源码事实（[源码]，H 树）
- `discval` 长 `nshapes+1`，索引 `i ∈ [0, nshapes]`；`i = 0` 为背景，形状 `k` 写入 `discval[k+1]`（`pattern.c` 的 `pattern_discretize_cell`：`value[0] = 1`，`value[k+1] += a`）。
- `imat[0]` 为 `i` 升序遍历中第一个 `|discval[i]| > 2ε` 的索引；`imat[1]` 为第二个。
- `nnz < 2`：不调用 `shape_get_normal`（单材料分支）。
- `nnz ≥ 2`：调用 `shape_get_normal(&(L->pattern.shapes[imat[0]]), xvec, nvec)`（`fmm_FFT.cpp` 第 138 行）。
- 由 `imat[1] > imat[0]` 且 `imat[1] ≤ nshapes`，得 `imat[0] ≤ nshapes − 1`：**下标合法，不越界**（逻辑论证）。

### 9.2 差一（独立于越界的发现）
- 同文件第 112–115 行的单材料分支使用 `shapes[imat[0]−1]`，与 `discval` 约定（`discval[i]` ↔ `shapes[i−1]`）一致。
- 第 138 行使用 `shapes[imat[0]]`，与约定**不一致**（差一）。
- `shape_get_normal`（`pattern.c` 199 起）对 CIRCLE 返回 `x − center`（未归一化），不检查 `x` 是否位于该形状边界上。
- 后果：[推断] 在相邻形状界面上几何碰巧一致；非相邻或背景界面上可能给出错误法线。**未经实测后果。**

### 9.3 探针（运行前登记：`J3_EXPECTATIONS.txt`，`J3_OVERLAP_EXPECTATIONS.sha256`）
- 探针 `testing/d003/stage_s1r2/shape_probe.cpp`：仅用公共 API（每个形状一次 `S4_Layer_SetRegionHalfwidths`，源码 `S4.cpp` 1158 起为 `n = nshapes++`，追加形状）构造；读取形状基址用内部头文件（只读，记为"内部只读"）。
- 布局：`concentric`（父子包含）、`two_disjoint`（无公共像素）、`overlap`（两圆相交，互不包含，补充期望 S-OVL）。
- gdb 在 `shape_get_normal` 入口记录指针；下标 = (指针 − 基址) / 56（`sizeof(shape)`，由探针两地址差实测得 56）。

### 9.4 结果（[实测]）

| 追踪 | nshapes | 调用次数 | 下标集合 | 全部在 [0, nshapes−1] | 映射失败 |
|---|---|---|---|---|---|
| B/A/H, nshapes = 1（同心） | 1 | 12（各树） | {0} | 是 | 0 |
| B/A/H, concentric | 2 | 28（各树） | {0, 1} | 是 | 0 |
| B/A/H, two_disjoint | 2 | 12（各树） | {0, 1} | 是 | 0 |
| B/A/H, overlap | 2 | 16（各树） | {0, 1} | 是 | 0 |

- 下标 2 从未出现（nshapes = 2 时的越界位置）。
- 下标 1（`imat[0] = 1`）出现，与差一的源码事实一致。
- 三树结果一致。

### 9.5 期望对照
- X1（单形状下标恒为 0）：成立。
- X2（不出现下标 nshapes）：成立。
- X3（出现 `imat[0] = 1` 的调用）：成立。
- S-OVL O1（重叠区域被覆盖）：**间接成立**（几何论证：两圆相交的交集内像素有两个非零分量；与同时出现下标 0、1 相符；未直接读取 `imat`）。
- S-OVL O2（不越界）：成立。O3（差一观测）：成立。

### 9.6 分类（按 J3 第 3 条）
- 恒在 `[0, nshapes−1]`：**是**（三树、三个布局、nshapes = 1、2；源码论证）。
- 可能越界：**否**。
- 不可判定：不适用（越界判定有实测与源码两方证据）。

### 9.7 对 S3 的输入判断
- 越界：不列入 S3（不可能发生）。
- 差一：位于 FMM 路径内，但**不影响失败传播链，也不影响"模式或缓存是否被安装"**。按判据可进入 S3，但其归属需用户裁决（见第 12 节，待用户批准事项）。
- 建议最小修复方向（不实施）：第 138 行改为与第 112–115 行一致的 `imat[0]−1`；但 `imat[0] = 0`（背景）分支需先定义几何语义，故不是单行替换。

### 9.8 未闭合
- 差一的几何后果未经实测（需读取 `imat[1]`，或在不改源码的前提下比较两种下标的 `nvec`）。
- `nshapes ≥ 3` 未测（推理为一般性，实测仅 1、2）。
- 张量材料与 kottke 组合下 `nvec` 的影响未测。

## 10. J4：`EVIDENCE.sha256` 逐条复核（S1R 对账第 4 节第 7 项）

- 清单 `checkpoints/p05/evidence/EVIDENCE.sha256` 共 **1293 条**（路径互不相同）。§11.2 称"19 个文件"，为某一时刻的口径，清单中未体现；本轮对全部 1293 条复核，不依赖"19"的口径。
- `sha256sum -c`（在证据目录内执行）：OK = 1293，FAILED = 0，缺失 = 0（`J4_sha256_check_raw.txt`）。
- 逐条表（`J4_hash_table.tsv`，`testing/d003/stage_s1r2/j4_hash_table.py` 独立计算）：OK = 1293，MISMATCH = 0，MISSING = 0。两种方法一致。
- **§11.2 的 8 个哈希与清单比较**：
  - 一致（3）：`logs/20-build-driver-baseline.log`、`logs/21-driver-syntax-diagnostic.log`、`rc.txt`。
  - 不一致（5）：`logs/60-t6-results.json`、`logs/60-t6-main.log`、`logs/61-t6-diag-layer.log`、`logs/62-t6-repeat.log`、`s1_run.sh`。
  - 这 5 个 §11.2 哈希只出现在 `S1_BASELINE_AND_ENUMERATION.md` 中（全仓库只读检索），git 历史中无这些文件的已跟踪版本（证据目录被 `.git/info/exclude` 忽略）。
  - **不匹配的原因无法判定**：可能是 §11.2 手工抄写错误；也可能是 §11.2 记录的是较早时刻的内容，之后文件与清单被同步更新。现有证据不能区分。
- 关闭范围：S1R 第 7 项"19 个证据文件未复核"已关闭（清单全部条目已复核，当前内容与清单一致）。**未关闭**：清单本身何时生成、§11.2 的 5 个哈希来源。

## 11. J5：记录在案的四项（S1R 对账第 4 节第 1、2、8、9 项）

本轮不解决，只原样列出。现状均引自 S1R 报告（[记录]），本轮只核对了引用位置存在且内容一致。完整记录见 `J5_RECORDED_ITEMS.txt`。

| 项 | 现状 | 需要用户提供 | 不提供的后果 | 是否阻塞 S3 | 依据 |
|---|---|---|---|---|---|
| 1. F10：历史 VL 非有限的因果 | 历史 VL 非有限与 info=2 同时出现，时序相关，因果未确认；历史负载的 NB 与频率在日志中无 DRIVER 行 | 历史负载的原始输入（NB 与频率），或允许独立复现 | 因果保持未确定；不能证明历史失败由 D016 所致 | **不阻塞 D016 实施**（D016 对任何 NB 都是正确的防御）；阻塞"证明历史因果"这一表述 | RECONCILIATION §4 第 1 行；§9 第 1 条 |
| 2. F8：历史候选目录六文件 SHA256 | 按 spec 不访问该目录，未验证 | 用户授权访问，或用户提供比对结果 | 历史候选目录与当前树的一致性未验证 | **不阻塞**（S3 修复都以当前仓库源码为对象） | RECONCILIATION §4 第 2 行 |
| 8. VL NB=1 反事实通量正确性 | 仅改 `allzero` 分支的草稿树使 NG=1 通量为 0.95890；Jones 0.97136、Normal 0.97441；三者公式不同，无独立参考 | 独立参考解（NB 收敛序列外推，或解析参考） | 让 NG=1 可计算的修法不能判定正确 | **不阻塞**：只影响"让 VL NB=1 可计算"的一半；D016 的"在根因处报错"一半不需要通量正确性 | ATTRIBUTION 第 8 节第 1 条、第 81 行；R-P05-01 |
| 9. `allzero` 分支的设计意图 | 源码无注释；历史仅见宽泛提交 `c0a8e69`；FFT 路径有相同约定 | 原作者或用户确认 1×1 是否有意 | 无法判断"让 NG=1 可计算"应改 allzero 还是改归一化 | **不阻塞**：同第 8 项；若确认 1×1 有意，零场归一化仍是 D016 覆盖的缺陷 | ATTRIBUTION 第 8 节第 2 条；R-P05-01 |

- 第 8、9 项对应 R-P05-01（第 1 节第 5 条）。二者只影响"让 VL NB=1 可计算"的一半，不影响 D016（"在根因处报错"）的一半。
- 行号说明：`allzero` 分支按内容定位，H 树约第 102–107 行，B 树约第 100–105 行（两树不同）。

## 12. J6：对 S3 的输入

### 12.1 汇总表

| 编号 | 点位（按内容） | 触发条件 | 现象 | 证据类型 | 建议最小修复方向（不实施） | 预计涉及文件 | 需用户批准 |
|---|---|---|---|---|---|---|---|
| **D016** | `pattern_generate_flow_field` 中 `max_field = 1./max_field;` 之前 | VL 基 n_G = 1（`allzero` → 1×1 网格，场为零） | 函数返回 0；`1./0` 后场被写为 NaN；NaN 进入 PolBasis 的 Epsilon_inv/Epsilon2 与特征值求解；`info=2`，公共 API 码 20 | [源码] 前置事实；[实测] VL NG=1 返回码 0（`J6_NG1/`）；max_field = 0 与 NaN 的数值引用 S1R（[实测]） | 见 12.2（a 至 f） | `S4/pattern/pattern.c`；三个调用方（只读核对，见 12.2(c)） | 见 12.2(f) |
| **K-1** | `fmm_kottke.cpp` 平均段：D1、D2、D7 等以 `abcd`/`abcde` 为除数的表达式（三树相同） | 标量 eps = 0，或 eps ≤ 1e-300 量级（阈值在 1e-100 与 1e-300 之间）；界面像素进入平均段 | Epsilon2 入口含 NaN；`zlaqr0_` SIGSEGV；退出码 139；无报告 | [实测]（求解器入口、栈追踪、三树）；机理（除零 vs 溢出）[推断] | 在平均段入口检查除数的有限性与量级（|x| 小于阈值或非有限），拒绝（返回错误码）或退化为面积加权；阈值与语义需先定义 | `S4/fmm/fmm_kottke.cpp`；可能 `S4/S4.cpp`（ComputeLayerModes 的非有限检查，影响面更大） | 阈值与语义；是否加通用非有限检查（属 S4 阶段） |
| **D-138** | `fmm_FFT.cpp` 第 138 行 `shape_get_normal(&shapes[imat[0]], …)` | nnz ≥ 2 且 `imat[0] ≥ 1` 的界面像素 | `shape_get_normal` 收到 `shapes[imat[0]]`，按 discval 约定应为 `shapes[imat[0]−1]`（差一） | [源码] 约定不一致；[实测] 下标 1 出现；几何后果 [推断] 未实测 | 第 138 行改为 `imat[0]−1`，但 `imat[0] = 0` 分支需先定义几何语义，非单行替换 | `S4/fmm/fmm_FFT.cpp` | 是否列入 S3（不影响失败传播）；背景界面的几何语义 |
| **R-NV-1** | `fmm_PolBasisNV.cpp` 的 `Pattern_GenerateFlowField` 调用后 | `error != 0` 时（D016 修法后经过此路径；H 树已有参数错误路径） | NV 先对未写入的 `vfield` 做归一化，再检查 `error`（与 VL、Jones 的顺序不同） | [源码]（`J6C_CALLER_CONSISTENCY.txt`） | 把 `if(0 != error)` 移到归一化之前 | `S4/fmm/fmm_PolBasisNV.cpp` | 是否同时处理（位于 FMM 路径内） |

本轮探针未发现问题的项：
- **J1**：未观察到半覆盖（混合状态）。A、H 失败路径不安装、不缓存；B 的失败被吞与崩溃与 REG_3C2 一致。理由与证据：`J1_RESULT.txt`，`J1_full_matrix_compare.tsv`，`J1_CLM/`，`J1_CACHE/`。
- **J3 的越界**：未发现越界。理由与证据：`J3_index_stats.tsv`、`J3_index_stats_n1.tsv`、`J3_OVERLAP_index_stats.tsv`。

### 12.2 D016 的准备内容（a 至 f；本轮不实施）

**(a) 修改点与建议代码形状**
- 位置（按内容）：`S4/pattern/pattern.c` 中 `pattern_generate_flow_field`，在语句 `max_field = 1./max_field;` 之前（H 树约第 2145 行）。
- 前置事实（[源码]）：`max_field` 来自 `pattern_generate_flow_field_rect`（约 1638 行）或 `_tri`（约 2086 行）的返回值；两者均以 0 初始化，仅在 `af > max_field` 时更新（rect 1624/1633；tri 2061/2080）。场为零，或元素全为 NaN（比较为假）时，返回 0。
- 建议形状（伪代码，不写入 `S4/`）：
  ```c
  if(!(max_field > 0) || !isfinite(max_field)){   /* catches 0, NaN, Inf */
      return <ERRCODE>;                            /* no multiply on the field */
  }
  max_field = 1./max_field;
  /* existing loop unchanged */
  return 0;
  ```
  `!(max_field > 0)` 同时覆盖 0 与 NaN；`isfinite` 覆盖 Inf。
- 证据类型：前置事实 [源码]；形状 [推断]，待 S3 实施后验证。

**(b) 错误码选取**
- 现有码：`pattern_generate_flow_field` 参数检查为 −1 至 −8（`pattern.c` 2099–2106，[源码]）。
- −9 的核对：
  - 命令：`git show 64eb0b5:<file> | grep -n -- '-9[^0-9.]'`（pattern.c、pattern.h、fmm_PolBasisVL/Jones/NV.cpp、S4.cpp）。
  - 结果：`pattern.c:1066` 有 `return -9`，属于 `pattern_discretize_cell` 的 `NULL == value` 检查；其余文件为 0。
- −10、−11 的核对：同方法（`grep -E '(return|=|\()[[:space:]]*-1[01][^0-9.]'`），六文件均为 0。
- 核对范围限制：只覆盖 return、赋值、调用形式；未覆盖宏定义形式，未覆盖其他目录。S3 实施前应做全目录 grep。
- **建议**：使用 −9。三个调用方与 `ComputeLayerModes` 只判断非零（`if(0 != error)`，[源码]），码值与 `pattern_discretize_cell` 的 −9 重复不会造成判断错误；但在同一文件中含义不同，若 S4 需要区分，改用 −10（已核对空闲）。
- 需用户批准：−9 或 −10。

**(c) 调用方一致性**（`J6C_CALLER_CONSISTENCY.txt`，H 树，[源码]）
- VL、Jones：`error != 0` 时释放 `vfield`、`work`、`ivalues`（各带 NULL 检查），`return error`。无遗漏、无重复释放。
- NV：**先归一化**（对 `vfield` 做 `hypot` 与除法），**后检查** `error`。顺序与 VL、Jones 不同（风险 R-NV-1）。
- 释放项核对：三个调用方对 `work`、`ivalues`、`vfield` 各释放一次，无双重释放。
- R-NV-1 不是 D016 引入的（H 树的参数错误路径同样存在），但 D016 修法后仍会经过它。外部可见性：NV 返回非零，`ComputeLayerModes` 得到 20，归一化结果不被使用；风险限于未定义行为本身 [推断]。

**(d) 修后预期（三树 B/A/H；VL NB = 1–4，即 n_G = 1）**
- 前提的证据等级：
  - VL n_G = 1 时 `pattern_generate_flow_field` 返回 0：[实测]（`J6_NG1/ng1-{B,A,H}.txt`，`eax=0`）。
  - max_field = 0、vfield = NaN、`1./max_field = inf`：[实测] 引自 S1R 归属文件第 71–72 行（本轮未重算 max_field；`_rect` 无符号，`field` 参数未能可靠读取，见 `J6_NG1/README.txt`）。
  - Jones、NV 在 NG = 1 的 max_field = 0.0402：[实测] 引自同文件第 79 行。
- 以下预期均为 [推断]（修法未实施）：
  - 失败位置：`pattern_generate_flow_field` 的新检查，经 VL 的 `if(0 != error)` 路径返回。
  - 不再发生：场乘以 Inf、NaN 写入 `vfield`、NaN 进入 PolBasis 的 `Epsilon_inv`/`Epsilon2`、进入特征值求解。
  - 驱动 rc：预期仍为 **20**（`S4.cpp` 2413–2417，PolBasis 的任何非零返回映射为 20）。
  - 公共 API 异常文本：预期仍为"层特征系统无法求解"（码 20，`main_python.c:137`）。
  - `info=2` 的 TRACE 文本（仅在 `ENABLE_S4_TRACE` 构建中出现，`S4_internal.h:43`）：预期不再出现，因为求解不再进行。
  - 最终错误码：预期仍为 20，新码只出现在 TRACE 中。
  - Jones、NV 在 NG = 1：max_field 非零，行为不变。VL NB = 5–9：行为不变。

**(e) 验证方法建议（留给 S3 与 S4，不在本轮实施）**
1. VL n_G = 1（NB = 1–4）：用 J1 的 gdb 方法在 `SolveLayerEigensystem` 入口计数；修后应为 0（不到达求解）。
2. VL NB = 5–9、Jones、NV：修前后正常路径的驱动输出与 FieldPlane 结果逐字节比对（sha256）。
3. 三树（B、A、H）均测。B 的 VL 在 NG = 1 同样经过 `pattern_generate_flow_field`，修法须在三树生效。
4. 对新检查的单元测试：需要一个非零形状但场为零的几何；**本轮未找到此类几何的构造方式**（未验证）。

**(f) 需要用户批准的事项**
1. 具体改动文本（12.2(a) 的检查形状与返回位置）。
2. 错误码取值（−9 或 −10，见 12.2(b)）。
3. NV 的 error 检查顺序（R-NV-1，见 12.2(c)）是否同时修改。
4. D016 的修改位于 `S4/`，属 P05-S3 实施范围；按用户既定决定，需用户批准具体文本后实施。

## 13. 仍未闭合缺口

1. J1：PolBasis 内 `AddFieldToCache` 之后的分配（缓存命中分支，第 243 行）未注入；其矩阵状态未测。
2. J1：单一几何与单一标量材料对；张量材料未测。
3. J2：机理（除零 vs 溢出）未逐元素确定；中间量未直接读取。
4. J2：张量路径（D7 为零）的可达性未证实，仅一个非正定张量点（正常返回）。
5. J3：差一的几何后果未经实测（需读取 `imat[1]` 或比较两种下标的 `nvec`）。
6. J3：`nshapes ≥ 3` 未测；张量与 kottke 组合下的 `nvec` 未测。
7. J4：清单何时生成未知；§11.2 的 5 个哈希来源无法判定。
8. J6(d)：max_field 的数值与 field 内容未在本轮直接测得（引用 S1R）。
9. J6(e)4：对新检查的单元测试所需几何未找到。
10. 复现包：运行器依赖模板的路径约定（见 `testing/d003/stage_s1r2/README.md` 第 4 节）。
11. 第 1、2、8、9 项（J5）：需用户输入。
12. 证据目录 `checkpoints/p05/evidence/p05-s1r2/` 被 `.git/info/exclude` 忽略，不提交；其内容的完整性依赖其自身清单（`J1_EXPECTATIONS.sha256` 等）。

## 14. 对 S2 签收判断的输入

**结论：本轮发现未改变 S2 的任一已闭合结论。** 理由与范围界定如下：

- **J1 与 S2 的 REG_3C2 类别一致**：B 的 SILENT_SWALLOW（NTH5）与 CRASH（NTH3/4、fftnv NTH5）、A 与 H 的 REPORTED_FAILURE 均与 REG_3C2 相同。本轮增加的是矩阵内容维度，结论是"未观察到混合状态"，它与 S2 的类别结论不冲突。
- **J2 与 S2 的 kottke 闭合**：S2R4 第 240、257 行与 S2R2 第 298 行把 `fmm_kottke.cpp` 的分配点（`discval`、`fft_alloc_complex`）与 `solve_info` 记为"已闭合"。这些闭合针对的是**分配失败与 solve_info 的失败传播**（注入 `kottke_alloc`、`linearsolve`）。J2 的发现（除数产生非有限值）是**另一类失败**，不否定上述闭合。
- **但需要明确范围界定**：S2 对 kottke 的闭合**不覆盖除数的数值安全性**。S2 签收时应注明此范围，否则读者可能误以为 kottke 整体已安全。
- **J3 与 S2**：S1R 把 `shape_get_normal` 下标列为未评估，S2 中没有对应的闭合结论。本轮的差一不是 S2 的闭合结论所依赖的内容。
- **S1R 对账已指出的 S2 引用错误（G3）**：不受本轮影响。

**未发现的情形**：未发现"S2 某个已闭合结论在源码上实际不成立"（任务书第 5 节停止条件未触发）。

## 15. 偏离与违规

### 15.1 表一：越界写入尝试（命令自身把仓库外路径作为写入目标）

延续 S1R 收尾报告第 8 节第 1–6 行，本轮从第 9 行起编号。

| # | 轮次 | 完整命令（要点） | 是否落盘 | 如何核实 |
|---|---|---|---|---|
| 9 | S1R2 / J2（kottke 除法计数核对） | `git show $c:S4/fmm/fmm_kottke.cpp \| grep -E '(/abcd\|/abcde\|-1\./abcd\|-1\./abcde)' \| sed ... > "/tmp_placeholder_not_used_$c.txt"`（三次，`$c` 为 37a82e8、876181c、64eb0b5；同一条命令） | **否**：stderr 为 `Read-only file system`；`grep: write error: Broken pipe` 为其后果 | `test -e` 对三个路径逐个核对：均 absent；根目录 `/` 的 mtime 为 2026-07-19（早于本轮），`ls -d /tmp_*` 无结果 |

说明：
- 该命令的写入目标是根目录下的占位路径，违反"凡以 `/` 开头但不在 `$REPO` 下的路径不得出现在任何命令里"。这是执行者的错误，已披露。
- 我在一条只需统计的命令里误加了重定向，这是动作上的错误，而非试图测试写入是否被拦截。
- 同一命令的 `grep -c` 统计部分本身不写文件，其结果已由重跑的干净命令得到。

### 15.2 表二：工具与脚本事件

| # | 轮次 | 现象 | 是否涉及仓库外写入 | 处理 |
|---|---|---|---|---|
| 1 | 第 0 步 | 无。`/tmp` 快照为 0 条目；strace 抽样无仓库外写入 | 否 | — |
| 2 | J1 | gdb 烟测脚本 `run` 参数错误（`fftvl_smoke`），`No frame selected` | 否 | 修正参数，重跑 |
| 3 | J1 | `write` 工具拒绝覆盖未读取的文件（`file has not been read`） | 否 | 先读后写 |
| 4 | J2 | 探针以 `--wrap` 链接，产生大量 `undefined reference` | 否 | 去掉 `--wrap`，改为公共 API 探针（探针不依赖注入器） |
| 5 | J2 | 探针运行 SIGSEGV，输出 `core dumped` 消息 | 否（`ulimit -c 0`；仓库内无 core 文件；`/var/crash` 无本轮新文件，只读核对） | 记录；改用 gdb 取回溯 |
| 6 | J1 | `sed` 替换因空格未匹配，生成的脚本偏移错误（`+1087` 未替换） | 否 | 改用带空格的替换，按树生成脚本 |
| 7 | J1 | 分类器 v1 把 `Epsilon_inv` 计入判定，正常路径误判为 MIXED | 否 | 修正为 v2（保留旧版输出） |
| 8 | J1 | 分类器 v2 把 SIGSEGV 组判为 FFT_ORIGINAL | 否 | 修正为 v3（CRASHED），保留旧版输出 |
| 9 | J3 | 统计脚本对单形状（`stride=None`）误判为不可映射 | 否 | 修正（单形状以基址为下标 0），保留旧版输出 |
| 10 | J4 | `sha256sum -c` 工作目录错误（`No such file`） | 否 | 改为在证据目录内运行 |
| 11 | J5 | awk 字段匹配字符串错误两次（`CLM_RET k=2` 与 `k=2`） | 否 | 改为锚定正则；统计结果已核对 |
| 12 | J2 | 用 heredoc 写 gdb 脚本（`gdb_j1_cache.gdb`），违反规则第 7 条 | 否（写入证据 tmp；内容核对无 EOF 残留，`^EOF` 计数 0） | 此后脚本一律用 write 工具 |
| 13 | J4 | 后台 grep 范围过大（包括 `.p04-review` 等），输出长时间不返回 | 否（只读） | 终止（`bash-2995`，已确认状态为 killed）；改用窄范围 |
| 14 | 收尾 | `/tmp` 目录本身的 mtime 在本轮内变化（23:35:42 +1100，即 12:35:42Z），当前为空，无残留；来源无法归属（可能为框架在调用之间清理 `/tmp`，见 `run_d003.sh` 注释） | 不能证实是执行者操作；无残留 | 披露；收尾快照为空，哈希与开始快照相同 |
| 15 | J3 | 探针重新编译后，`j3-shape-probe-*` 哈希改变（加入 overlap 分支） | 否 | 披露（6.4） |
| 16 | 框架 | 长输出（gdb 反汇编、dump 日志）经文件重定向写入证据目录，stdout 用 head/tail 限制；未观察到框架向 `/tmp/dsh-spill-*` 落盘的提示 | 否（未观察到） | 披露；本项为"未观察到"，不是"未发生" |
| 17 | 收尾（复现包） | 第一次校验 MANIFEST 行时路径拼接错误（去掉 `s1r2/` 前缀后拼回 `registries/`），59 行报"No such file"并显示为 BAD | 否（只读校验） | 修正路径（保留 `s1r2/`）后重算，59 行全部一致（ok=59，bad=0）；MANIFEST 未受影响（追加在校验之后，且追加内容由包内文件生成） |

- 框架落盘：未观察到 `/tmp/dsh-spill-*` 的提示或残留（收尾快照为空）。
- 限制输出措施：所有 gdb 与驱动运行的 stdout 经重定向至证据目录；查看时用 `head`、`tail`、`grep`、`cut` 限定范围。

## 16. 路径清单

### 16.1 提交范围（可提交）
- `testing/d003/stage_s1r2/`（新增：探针源码、分类器、统计、J4 表、gdb 模板、运行器、README）
- `checkpoints/p05/P05_S1R2_CLOSEOUT.md`（本报告）
- `checkpoints/p05/registries/s1r2/`（复现包，见 16.3）
- `checkpoints/p05/registries/MANIFEST.tsv`（追加）
- `checkpoints/p05/S1_evidence_digest.txt`（追加段落）

### 16.2 证据目录（不提交，被 `.git/info/exclude` 忽略）
- `checkpoints/p05/evidence/p05-s1r2/`：三树导出（`trees/`）、构建日志、驱动（`drivers/`）、J1–J6 的全部原始输出与中间文件、`PROGRESS_CHECKPOINT.txt`、`safe_run.log`、`tmp_top_snapshot_{START,END}.txt`、`strace_sample_{START,END}.txt`。

### 16.3 复现包（可提交，只拷贝文本小文件并核对 sha256）
复现包 `checkpoints/p05/registries/s1r2/` 与 `MANIFEST.tsv` 的追加行在第 19 节提交前生成；复制后逐个 sha256 核对（核对结果记入 `PROGRESS_CHECKPOINT.txt`）。

### 16.4 未修改的对象（核对）
- `S4/`：相对 `64eb0b5` 的 diff 行数为 0（见第 17 节收尾核对）。
- `testing/d003/judge_d003.py`：sha256 `d2d04145…`（不变）。
- 既有驱动与注入器（`testing/d003/src/`）：未修改。
- 已提交报告原文：未修改。
- `testing/s4test/ISSUE_REGISTRY.md`、`PROJECT_ROADMAP.md`：未修改（只读引用）。

## 17. 收尾核对

- `git status --short`（提交前，报告写入后）：` M checkpoints/p05/S1_evidence_digest.txt`、` M checkpoints/p05/registries/MANIFEST.tsv`、`?? checkpoints/p05/P05_S1R2_CLOSEOUT.md`、`?? checkpoints/p05/registries/s1r2/`、`?? testing/d003/stage_s1r2/`。无其他变更；证据目录被忽略，不出现。
- `S4/` 相对 `64eb0b5`：`git diff 64eb0b5 -- S4/ | wc -l` = **0**。
- 复现包：59 个文件，与证据源逐个 sha256 一致（59 对，0 不一致）；MANIFEST 追加 59 行，每行 sha256 经包内文件重算核对（59 行，0 不一致）。
- 越界路径数：表一 1 条（未落盘，见 15.1）；`safe_run.log` 的 68 条记录均指向证据目录（`out=` 字段）。
- `/tmp` 顶层快照：开始与结束均为 0 条目，哈希 `e3b0c442…`（空目录）。
- strace 抽样：开始与结束各 12 行；仓库外写入模式打开 0 次；`/tmp` 提及 0 次。
- `/tmp` 顶层快照三次（证据文件 `tmp_top_snapshot_{START,END,FINAL}.txt`）：均为 0 条目，哈希 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`（空目录）。
  - 最终快照时刻（12:39:53Z）的 `find /tmp -xdev -newermt` 仍报告 1 条，即 `/tmp` 目录本身（mtime 变化，内容为空，见表二第 14 条）。
- 收尾 strace 与快照的开始、结束、最终三对记录均已保存在证据目录（不提交）。

## 18. 提交表

提交待执行（见第 19 节的提交顺序）。提交哈希将在提交后记入 `PROGRESS_CHECKPOINT.txt`，本报告不回填哈希。

## 19. 提交顺序与信息

1. `test(p05): S1R2 J1-J6 probe and analysis scripts under testing/d003/stage_s1r2 (awaiting user review)` — 仅 `testing/d003/stage_s1r2/`。
2. `docs(p05): S1R2 closeout report, registries/s1r2 package and digest (awaiting user review)` — `checkpoints/p05/P05_S1R2_CLOSEOUT.md`、`checkpoints/p05/registries/s1r2/`、`MANIFEST.tsv`、`S1_evidence_digest.txt`。

提交范围仅限 `testing/d003/` 与 `checkpoints/p05/`；不 amend、不 rebase、不 push、不合并、不动 master 或 origin。
