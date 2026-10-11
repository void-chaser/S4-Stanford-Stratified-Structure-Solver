# P05-S3R 补充轮报告：D003 剩余缺陷最小修复（已停止，未完成）

> **状态：未完成，等待用户审核。本轮于正常路径检查处按停止规则停止，未完成 R3-D 与 R3-E。**
> 本报告不宣布 P05-S1、P05-S2、P05-S3、P05-S4 任何一个阶段完成。
> 本轮是正式阶段 **P05-S3** 的补充子任务，**不是新阶段**。P05 固定五阶段 S1–S5，未引入 S6。
> 本轮所有结果称"开发检查"，不称"验证"。验证属于 P05-S4，以本轮冻结后的 HEAD 为准。

**证据类型标注**：[源码] 只读阅读并逐行回查；[实测] 本轮运行、编译或反汇编的原始输出；[推断] 由实测得出，未直接验证；[未验证] 本轮无证据。

---

## 0. 定位与阶段定义依据

- 阶段定义依据**用户提示词**。仓库内无原始 P05 计划文档，本轮未再搜索。
- 输入为 S2R2 收尾报告 `checkpoints/p05/P05_S2R2_HARNESS_CLOSEOUT.md` 的红点清单与完成判据（起点 HEAD `876181c`，已核对）。
- 本轮结论只覆盖：**(a)** 四个源码提交的编译与静态走查，**(b)** 修前红测量，**(c)** 正常路径比对。**不覆盖**修后红转绿的完整矩阵（见 §6）。

## 1. 用户授权（逐项，本轮执行范围）

| 授权项 | 位置 | 本轮结果 |
|---|---|---|
| 1 `Simulation_AddFieldToCache` 返回 int，声明两处同步 | `S4/S4.cpp` ≈226，`S4/S4_internal.h` ≈243 | **已完成**（提交 `e83255f`） |
| 2 三个 PolBasis 调用方检查返回值，走既有清理路径，返回既有码 | `fmm_PolBasisJones/NV/VL.cpp` 缓存安装处 | **已完成**（`e83255f`） |
| 3 `ComputeLayerModes` 通用分配 4 点，返回 20 并经 `Simulation_DiscardLayerModes` 清理 | `S4/S4.cpp`（2267/2295/2408/2425，按内容定位） | **已完成**（提交 `73e00ef`） |
| 4 info=NULL 的 7 处 LinearSolve 传 `&info` 并检查 | `fmm_PolBasisJones/NV/VL.cpp`，`fmm_closed.cpp`（4 处） | **已完成**（提交 `df3bb02`）——**但该提交改变了 Jones 正常路径输出，见 §5 与 §7** |
| 5 `fmm_experimental.cpp:40` NULL 检查，返回 20 | `S4/fmm/fmm_experimental.cpp` | **已完成**（提交 `35cd7b3`，仅静态） |
| 6 保留 `FMMGetEpsilon_Experimental` 返回值接收 | `S4/S4.cpp` dispatch | **未改动**（符合 D-4 决定） |

**未授权且未改动**：非 FMM 的其他 `S4_malloc`（约 43 处，范围外）；`RNP/` 任何文件；`rcwa.cpp`；`DiscardLayerModes`；新增错误码。

## 2. 起点核对 [实测]

| 项 | 结果 |
|---|---|
| 开工 HEAD | `876181c`，分支 `codex/p05-d003-fft-error-propagation`，工作区干净 |
| 起点 `libS4.a`（`git archive` 导出，干净构建） | sha256 `865c5893…01b1da`（与 S2R2 记录的同一 S4 树一致） |
| `S4/` 相对 `8d60dfb` | 开工时 0 改动 |
| `/tmp` 顶层快照（开始） | sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`，条目 0 |

## 3. R3-0 装置前置

### 3.1 驱动固定（D-DRV-1）——已完成并提交（`37d603a`）

- `matrix_r2.py` 新增必填参数 `--driver-sha256`；驱动哈希不符、缺失或不可执行时**在运行任何行之前报错退出**，不写 raw 文件（已逐项验证四种情形）。
- 输出目录写入 `driver_manifest.json`；同一目录换用不同驱动被拒绝（清单不被覆盖，已验证）。
- 判定逻辑未改：`judge_d003.py` 未修改（哈希 `d2d04145…` 不变），自检输出逐行一致（25/25 与 10/10）。
- 删除了死代码分支（旧的 `driver_ok` 与 INVALID 路径），新增 35 行、删除 5 行，均在驱动选择范围内。
- S2R2 T5 视图经固定驱动重跑，两棵树 17 个 case 的全部事实与 S2R2 记录逐行一致（差异 0）。

### 3.2 S2R2 口径矛盾（nv/vl 缓存命中）——已核对

- **结论**：nv:232 与 vl:241 的缓存命中点**只有探测，未纳入 T5 的 17 个 case**。
- 依据 [实测]：T5 视图 17 个 case 中仅有 `t4/cache-hit-work-k7`（jones 缓存命中）；`case` 列表中无任何 nv/vl 缓存命中 case。
- S2R2 报告 §5.6 的写法（"探测性测量…尚未纳入 T5 两轮正式运行"）**正确**。S2R2 报告 §8.1 把它写成"已闭合（探测 + 登记）"，**口径偏宽**，本报告的补充章节更正之（见 §9）。

### 3.3 修前红测量（本轮自有证据，未引用 S2R）——已完成

- 注册表 `REGISTRY_S3R_PRE.tsv`（16 行 = 8 点 × 2 树，sha256 `655349cc…`，时间戳 2026-10-11T06:07:09Z，**全部标 INFLUENCED**：S2R/S2R2 结果在写入时已在上下文中）。
- 驱动：基线 `seam-base-37a82e8/bin/driver-pin`（sha256 `482f8526…`）；起点 `seam-start-876181c/bin/driver-pin`（sha256 `1aa0c913…`）。
- 两轮运行，每轮事实完全一致。结果 [实测]：

| 点 | 基线 37a82e8 | 起点 876181c |
|---|---|---|
| PolBasisJones:369 | SILENT_SWALLOW | SILENT_SWALLOW |
| PolBasisNV:260 | SILENT_SWALLOW | SILENT_SWALLOW |
| PolBasisVL:268 | SILENT_SWALLOW | SILENT_SWALLOW |
| ComputeLayerModes 2267（LayerModes） | CRASH | CRASH |
| ComputeLayerModes 2295（pB->q） | CRASH | CRASH |
| ComputeLayerModes 2408（rwork） | SILENT_SWALLOW | SILENT_SWALLOW |
| ComputeLayerModes 2425（work） | SILENT_SWALLOW | SILENT_SWALLOW |
| AddFieldToCache 3977（jones） | CRASH | CRASH |

- 结论 [实测]：**基线与起点的红点完全相同**，即 S3 修复未改变这些点。

### 3.4 注入路由覆盖（R3-0 前置核对）

- family B（`linearsolve_null:ID:K`，ID 15/16/17 与 11–14）、family C（`alloc:ID:K`，ID 21–25）均已存在于注入器源码 [源码]。
- `alloc:25:1` 仅在 jones 模式命中（`size=5504`），fft 模式不命中（`HITCOUNT 0`）[实测]。

## 4. R3-A 设计（依据源码，写入 `DESIGN.txt`，200 行）

| 决定 | 内容 | 依据 |
|---|---|---|
| D1 | `AddFieldToCache` 失败返回 1，不修改 `S->field_cache`；三个调用方在合并分支（merge）释放 `work`、`ivalues` 后返回 1 | 失败前链表头未变（F1）；缓存节点为 P 的副本（F2）；调用方在该点持有 `work`、`ivalues`，`vfield` 与 `plan` 已先释放 [源码] |
| D2 | 求解失败时**保留**缓存项 | 缓存在求解前由 LU 完成的 P 复制而来；`LinearSolve` 只写右端与 a 参数，不写 P [源码，RNP/LinearSolve.h 读取] |
| D3 | `ComputeLayerModes` 四个出口各释放其时点仍存活的指针 | `DiscardLayerModes`（S4.cpp:1355）对 NULL 安全 [源码]；`S4_free(NULL)` 为空操作（numalloc.c:117）[源码] |
| D4 | info=NULL：`&info`，失败时释放存活资源并返回 1 | 零主元时模板跳过回代、右端保持输入值 [源码，LinearSolve.h:31,38] |
| D5 | `fmm_experimental:40`：分配后、派生 `values` 前检查，返回 20 | 调用方对非零 `fmm_ret` 报 20 [源码，S4.cpp:2369,2400] |

**边界（记录，未跨越）**：`rcwa.cpp` 的 `SolveLayerEigensystem`（774–800 行）在收到 NULL 的 `work_`/`rwork_` 时自行分配工作区，这是 2408/2425 显示 SILENT 的原因。修复放在调用方，`rcwa.cpp` 未改动。

**更正（设计撰写时发现）**：
- LinearSolve 报告的是**最后一个**零主元列，不是第一个（零矩阵探针：`info=2`）。设计文本"第一个失败列"有误；所有检查只判断"非零"，代码决定不变。
- Jones 的 work 引用：合并分支在 158 检查，缓存命中分支在 345 检查（原设计只引用 158，已更正）。

## 5. R3-B 逐项提交

| 提交 | 内容 | 文件 | 行数（+/−） | 静态走查 | 构建 |
|---|---|---|---|---|---|
| `e83255f` | AddFieldToCache 返回 int；三个调用方检查 | S4.cpp、S4_internal.h、PolBasis×3 | 19 / 6 | 失败路径释放 work、ivalues 各一次；缓存在失败时未链入 | 干净构建 12 目标、0 错误，警告多重集与 876181c 完全相同 |
| `73e00ef` | ComputeLayerModes 四处检查（R1–R4） | S4.cpp | 30 / 0 | 每个释放归属其出口；出口在后续释放前返回，无双重释放 | 同上，相同 |
| `df3bb02` | 七处 info=NULL 传 `&solve_info` 并检查 | PolBasis×3、fmm_closed.cpp | 36 / 7 | 每个 solve 都有状态参数（7/7）；每个检查释放一次并返回 1 | 同上，相同 |
| `35cd7b3` | experimental 分配检查，返回 20 | fmm_experimental.cpp | 4 / 0 | 仅静态：分配后无其他存活指针 | 同上，相同 |

- 每个提交的 CRLF 行尾保持（逐文件核对：每行均为 CRLF）。
- 提交范围全部在授权文件内（`git diff --name-only 8d60dfb HEAD -- S4/` 共 7 个文件，全部在授权清单中）。
- **双重释放检查** [源码]：`ComputeLayerModes` 的全部释放按出口归属（2309、2374、2415、2427、2441–2442、2452–2453、2463–2464、2467），每个出口返回前不会到达其他出口的释放。

## 6. R3-C 兼容检查——**在此停止**

### 6.1 已完成的部分

- **警告**：`e83255f`、`73e00ef`、`df3bb02`、`35cd7b3` 各自的干净完整构建，其警告多重集与 876181c **逐行相同**（71 行，差异 0）。
- **种子补丁**：family A/C/D 在新 HEAD 上锚点唯一、零错误（已验证）。family B 不通过（见 6.3）。
- **正常路径字节比对（日志）**：19 个正常用例（S2R2 的 10 个历史控制 + jones/nv/vl 的 s/p/mix 偏振）在 876181c 与 HEAD 上，**日志字节 19/19 一致**。

### 6.2 日志比对的局限（重要）

日志比对**不足以**证明正常路径未变：偏振 s/p/mix 的日志在两棵树上完全相同，但偏振确实改变计算的场（三种偏振的场转储 sha256 互不相同）。因此本轮改为比对**场转储**（`S4FMM_DUMP1`/`S4FMM_DUMP`），这才是要求的"输出"。

### 6.3 场转储比对——发现正常路径改变，**停止**

- **结果** [实测]：38 个场转储中 **30 个一致，8 个不一致**。8 个全部属于 **Jones** 模式（`ctl-jones-pattern`、`pol-jones-s/p/mix`，各 dump1 与 dump2）。NV、VL 及其余控制全部一致。
- **非噪声** [实测]：HEAD 的三次相同运行产生同一场（1 个不同哈希）。
- **归因** [实测，二分法，相同插桩]：

| 状态 | Jones 场 sha256 |
|---|---|
| `876181c` | `538daf8f…` |
| `e83255f`（提交 1） | `538daf8f…`（未变） |
| `73e00ef`（提交 2） | `538daf8f…`（未变） |
| `df3bb02`（提交 3） | `e6e9d107…`（**改变**） |
| `35cd7b3`（提交 4） | `e6e9d107…`（未变） |

- **隔离** [实测]：`876181c` + 提交 1 的 `AddFieldToCache` + **仅**提交 3 的 `fmm_PolBasisJones.cpp`，即可复现 `e6e9d107…`。
- **性质** [实测]：144 个场分量全部不同，最大相对差 **1.18e-12**，中位数 **4.3e-14**，属于双精度舍入量级，不是算法改变（算法改变通常 ≥1e-8）。
- **机理** [实测]：
  - `LinearSolve` 构造函数的舍入操作数两边相同（50）：求解器自身算术未变。
  - Jones 函数体：142（起点）→ 152（提交 3）。
  - 变体对照（`-ffp-contract=off`，同一源码）：带 `&solve_info` 且带检查 → 152；带 `&solve_info` 去掉检查 → 152；去掉 `&solve_info`、保留检查 → 142。
  - **因此原因是 `info` 参数由 NULL 改为非空指针**，而非检查本身。传入非空 info 使编译器对函数体的标量运算做了不同调度，从而改变舍入顺序。
- **替代方案已排除**：去掉 `&solve_info` 可保持 142，但求解失去报告零主元的能力，检查恒为 0，等同于保留缺陷，**不是修复**，不采用。

### 6.4 为何必须停止

任务要求"正常路径输出与 876181c 逐字节一致；任一差异停下报告"。该差异真实存在，由提交 3 的 Jones 编辑引起，且由当前的 LinearSolve 模板（唯一的状态通道是 info 参数）决定，无法在保留零主元报告的同时保持字节一致。**是否接受舍入序级别的改变，属于用户决定**，本轮不替用户裁决，也不撤销或修改提交 3。

## 7. R3-D 开发检查——未完成

- **三列对照**（基线 / 起点 / 新 HEAD）未完成。原因：
  - family B 注入（七处 info=NULL 与其余）不可测：(i) 种子锚点在 13、14 两处的 solve+检查对完全相同，无法唯一定位；(ii) family B 的钩子只写输出缓冲，从不设置 `solve_info`，因此即使锚点正确，也无法驱动新检查（已用零主元探针确认：真实奇异矩阵会令 info 非零，但注入器不模拟这一点）。
  - 因此七处 info=NULL 的修前红→修后绿**本轮不能用装置证明**。
- **已能测的部分**（family C，分配点）：锚点在新 HEAD 上唯一且位置正确（5 个注入点，以注入文本定位，共 5 个 `S4_TEST_ALLOC_HOOK` 调用 + 1 个声明）。但因正常路径停止，R3-D 三列对照按停止规则未展开。
- **驱动不可达点**（closed 130/133/138/235、experimental:40）：仅静态走查，标 **[未验证-仅静态]**，未编造运行结果。

## 8. R3-E 范围外登记草稿——未开始

按停止规则，R3-E 未开始。草稿要点（待用户决定后撰写）：非 FMM 的 S4_malloc 约 43 处，并列入 `rcwa.cpp` 中被边界排除的 SolveLayerEigensystem 自分配路径（S4.cpp:1993 的 `work` 位于 `Simulation_ComputeLayerSolution`，属范围外，已记录未修）。

## 9. 偏离、违规与披露

| 编号 | 类别 | 内容 | 处理 |
|---|---|---|---|
| D-R3-1 | 停止 | 提交 3 改变 Jones 正常路径场（舍入序） | 停止；未撤销；提交保留，待用户决定（§6.4） |
| D-R3-2 | 种子锚点 | 提交 3 使 family B 的 13/14 锚点不唯一；family B 钩子不设置 solve_info | 记录；family B 不可测（§7） |
| D-R3-3 | 检查错误 | 为 family C 核对时用了错误的搜索窗口（注释中的 `S->field_cache` 误判为代码；随后用去注释的代码重核） | 已更正，见 §5 |
| D-R3-4 | 检查错误 | 警告比较首次用了不完整的增量构建（只编译 1 个目标），"消失"的 63 行为假象 | 改为干净完整构建重比，结论有效 |
| D-R3-5 | 检查错误 | 比较用的 `comm` 输入未排序，首次结论无效 | 以 `LC_ALL=C sort` 重做 |
| D-R3-6 | 检查错误 | 偏振日志比对误作"输出一致"证据（日志与偏振无关） | 改为场转储比对，见 §6.2 |
| D-R3-7 | 隔离错误 | "仅提交 3 的 Jones 文件"首次隔离因依赖提交 1 的返回类型而无法编译 | 改为最小集（提交 1 + 提交 3 Jones），编译通过后得到结论 |
| D-R3-8 | 口径更正 | S2R2 报告 §8.1 把 nv/vl 缓存命中写成"已闭合"，实际仅探测 | 本报告更正（§3.2） |
| D-R3-9 | 工具输出落盘 | `grep`/`sed` 的超长输出被框架落盘到 `/tmp/dsh-spill-…` 与 `/tmp/dsh-subprocess-…`（工具行为，非本代理 shell 写入） | 已披露；此后改用 `read` 的 offset/limit 限定输出 |
| D-R3-10 | 编辑失败 | `edit` 因缩进（制表符层数）不匹配被拒绝 2 次，因未先 `read` 被拒绝 1 次 | 读取精确字节后重试；无错误写入 |
| D-R3-11 | 参数错误 | 工具调用缺必填参数 `description` 2 次、字段名 `descent` 误写 1 次 | 未执行，无副作用，已重做 |
| D-R3-12 | 锚点误写 | 首次种子运行 family B 锚点为旧文本，失败于 `call` 首行 | 已按新文本逐条更新（7/7），并如实记录 |

**未在本轮写入仓库外路径**：本轮所有临时文件均在 `checkpoints/p05/evidence/p05-s3r/tmp`（仓库内、被忽略）。工具框架的超长输出落盘见 D-R3-9，**未由本代理 shell 写入 `/tmp`**，但属于框架行为，无法由 shell 证伪。

## 10. 未修与范围外清单

| 项 | 性质 | 状态 |
|---|---|---|
| 七处 info=NULL 的修后红→绿 | 装置无法测量（§7） | 未证明 |
| closed 130/133/138/235、experimental:40 | 驱动不可达 | 仅静态 [未验证-仅静态] |
| `S4.cpp:1993` `work`（Simulation_ComputeLayerSolution） | 范围外（未授权） | 记录，未修 |
| `rcwa.cpp` SolveLayerEigensystem 的内部自分配 | 授权外文件 | 记录，未修 |
| 非 FMM 的 S4_malloc（约 43 处） | 范围外 | 草稿待写（R3-E 未开始） |
| LAPACK 构建的 LinearSolve info 语义 | 未验证（默认构建外） | [未验证] |
| 提交 3 的 Jones 舍入序改变 | **待用户决定** | §6.4 |

## 11. 对 P05-S4 的输入

- **冻结 HEAD**：未冻结。本轮停止，HEAD `35cd7b3` 含提交 3，其 Jones 正常路径已改变，**不宜直接作为 P05-S4 的冻结基准**，待用户决定。
- **基线**：`37a82e8`（干净导出，与 git 对象逐字节一致，已核对）。
- **被测点清单**：§3.3 的 8 点；§4 的 D1–D5；§5 的四个提交。
- **已知限制**：
  - closed 130/133/138/235 与 experimental:40 驱动不可达，仅静态；
  - 七处 info=NULL 的修后效果无装置证据（family B 不可测）；
  - Jones 正常路径在提交 3 处改变（舍入序，最大相对差 1.2e-12）；
  - 缓存命中的 T4 路由使用内部接口，公开 API 可达性未证；
  - LAPACK 构建未验证；
  - S2R 与 S2R2 的部分登记标注 INFLUENCED，不是盲预注册。

## 12. 路径清单

| 类别 | 路径 |
|---|---|
| 提交 | `37d603a`（testing/d003，R3-0 运行器）；`e83255f`、`73e00ef`、`df3bb02`、`35cd7b3`（S4 源码，见 §5） |
| S4 改动文件（相对 8d60dfb，全部在授权清单内） | `S4/S4.cpp`、`S4/S4_internal.h`、`S4/fmm/fmm_PolBasisJones.cpp`、`S4/fmm/fmm_PolBasisNV.cpp`、`S4/fmm/fmm_PolBasisVL.cpp`、`S4/fmm/fmm_closed.cpp`、`S4/fmm/fmm_experimental.cpp` |
| 未提交的工作改动 | `testing/d003/seam/apply_seam_r2.py`（family B 锚点，未完成） |
| 本报告 | `checkpoints/p05/P05_S3R_MINIMAL_FIX_SUPPLEMENT.md` |
| 证据（忽略，不提交） | `checkpoints/p05/evidence/p05-s3r/`：`DESIGN.txt`、`PRE_FIX_RED_RECORD.txt`、`REGISTRY_S3R_PRE.tsv`（+ `.sha256`、时间戳）、`STOP_STATUS.txt`、`r3c/stop/NORMAL_PATH_DIFFERENCE.txt`、`bisect/`、`r3c/normal/`、`r3c/normal/*_fields/` |

## 13. 收尾核对

| 项 | 结果 |
|---|---|
| HEAD | `35cd7b3` |
| 工作区 | 1 个未提交改动：`testing/d003/seam/apply_seam_r2.py`（有意保留，属未完成工作） |
| `S4/` 相对 `8d60dfb` | 7 个文件，全部在授权清单内，无越界 |
| 越界路径（相对允许范围 `checkpoints/p05/` 与 `testing/d003/`） | 0（S4 源码提交属于授权，见 §1） |
| `/tmp` 顶层快照 | 开始 `e3b0c442…`（条目 0）；结束见下（抽样） |
| 抽样 strace | 未在本轮结束时执行（停止前未完成），**不得称为完整审计** |

**本阶段未完成，等待用户审核。** 决定事项：提交 3 的 Jones 正常路径舍入序改变（§6.4）——请用户在 (a) 接受并重定义该模式的字节比对、(b) 撤销或改写提交 3 中 info 的传递方式、(c) 指定其他处理方式 之间选择。在该决定作出前，本轮不继续 R3-D 与 R3-E。
