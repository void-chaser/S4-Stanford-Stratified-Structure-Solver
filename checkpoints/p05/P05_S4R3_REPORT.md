# P05-S4 R3 报告（子轮次）：调用序发现、站点映射、预注册 v3、穷举注入

**状态：本轮未完成，等待用户审核。P05-S4 未签收。** 本报告是 P05-S4 的子轮次记录，不是新阶段。本报告不宣布 P05-S4 或任何其他阶段完成。R3 的注入结果只说明"在该注入下 rc1≠0"（REPORTED_FAILURE）或"该注入未被触达"（INVALID），不说明任何树已修好或已验证。B 列（37a82e8）是未修复基线，不是修复证据。

## 1. 完成项与未完成项

| 项 | 状态 | 证据（`checkpoints/p05/evidence/p05-s4r3/`） |
|---|---|---|
| R3-0 开工门禁（分支、HEAD、干净工作区、S4 树哈希、judge sha256） | 完成，全部一致 | 第 2 节 |
| R3-0 ERRATA_3（a 至 g） | 完成 | `ERRATA_3.txt` |
| R3-1 发现轮：gdb 调用序（B、F，8 模式，两条路由，两次重复） | 完成，B 与 F 在规范字段上一致，重复可复现 | `CALLSEQ.tsv`（2100 行），`discovery/`，`discovery_fc/` |
| R3-1 字段调用边界（FIELDCALL_MAP） | 完成（为选择 inj_call 而新增，只读断点） | `FIELDCALL_MAP.tsv`（525 行） |
| R3-2 站点映射 SITEMAP（525 点：141 范围内，384 范围外） | 完成 | `SITEMAP.tsv` |
| R3-2 R1 对照 与 UNMAPPED_R1 | 完成：62 个 R1 ID，32 个有映射，30 个 UNMAPPED（原因见第 6 节） | `COVERAGE_R3.tsv` |
| R3-3 预注册 v3（注入之前写入并记录 sha256） | 完成：282 行（141 点 × B、F） | `REGISTRY_S4_PRE_R3.tsv`，`REGISTRY_S4_PRE_R3.sha256` |
| R3-4 穷举注入：范围内 141 点 × B、F（282 次）+ 控制 8 模式 × B、F、A（24 次） | 完成（306 次运行） | `sweep_yes/`，`RESULTS_R3.tsv` |
| R3-4 范围外点观察（384 点 × B、F，无期望，不计 MATCH） | 完成（768 次运行） | `sweep_out/`，`RESULTS_R3_OUTSCOPE.raw.tsv` |
| R3-4 A 树仅控制行 | 完成 | `sweep_yes/RESULTS_R3.raw.tsv`（CTL 行） |
| R3-4 判定只用 judge_d003.classify 的事实，不读驱动 PASS/FAIL | 完成（判定由 classify 给出，见第 9.4 节关于 summarize_r6.py 的偏离） | — |
| R3-5 覆盖表 | 完成 | `COVERAGE_R3.tsv` |
| R3-5 红点表 | 完成（F 上 22 点，全部为未命中；F 上无 CRASH、无 SILENT_SWALLOW） | `RED_POINTS_R3.tsv` |
| R3-5 范围外计数表 | 完成（S4_malloc 的范围外计数为静态源码计数，见第 7 节；观察计数为 GetFieldOnGrid 的 plan/exec） | `OUTSCOPE_COUNT_R3.tsv` |
| R3-6 提交与报告 | 本报告；提交范围见第 12 节 | — |
| SI01–SI02、FE01–FE10、info=NULL 七处、CLM1–4、ACF1、AL18、K1A/K1B、D016、RNV1 | **未覆盖**（原因见第 6 节，R4 建议见第 11 节） | `COVERAGE_R3.tsv` |
| 注入器 plan 的 NTH ≥ 3 | **未覆盖**（测量不可达，见 ERRATA_3 f） | `RED_POINTS_R3.tsv` |

## 2. 门禁与快照

- 分支 `codex/p05-d003-fft-error-propagation`；HEAD `33b8bf8`；开工时 `git status --short` 为空；`git rev-parse HEAD:S4` 为 `4a6f64927a30537740dd0c8f11f9a5aae5e46ba4`；`testing/d003/judge_d003.py` sha256 `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`。**全部一致，门禁通过。**
- `/tmp` 顶层快照：START 与 END 均为 0 条目，sha256 `e3b0c442…`（空列表），**未变**。快照写入 `GATE_R3.txt`（经 safe_run）。
- 本轮期间 `/tmp` 第 3 层内无新增或修改条目（`find -newer` 核对为 0）。

## 3. 树与驱动（路径偏差已披露）

R2 的树与驱动实际位于 `checkpoints/p05/evidence/p05-s4r2/run2/`，不在任务书写的 `p05-s4r2/trees/` 下（ERRATA_3 d1）。使用的 libS4 与驱动 sha256 与 R2 记录一致：

| 树 | libS4.a sha256 | 驱动 sha256 |
|---|---|---|
| B（37a82e8） | `fb9ac3f5…` | `f2261175…` |
| F（1c11905） | `be17f469…` | `08f48df5…` |
| A（876181c，仅控制） | `865c5893…` | `5dd45f8b…` |

驱动**无调试段**（readelf 无 `.debug_*`，file 显示 not stripped）。因此 gdb 只能给出调用者的**函数名**，不能给出行号；`caller_file` 写为 NONE（ERRATA_3 d2）。S4/ 的构建未改动。

## 4. ERRATA_3 摘要

- **a. R2 的 "45 行"** 是 15 个用例 × 3 棵树（RESULTS_R2.tsv 45 数据行）。F 列精确计数：15 行，其中 **11 行 hit ≥ 1**（11 个点：AL01 AL02 AL03 AL04 AL06 AL07 AL09 AL10 EX01 EX02 P01），4 行 hit = 0（C0-F 与 AL05/AL08/AL11 的 NTH5）。
- **b. R2 的 AL01–AL11 与 R1 的 AL01–AL18 同名不同义**。本轮不复用 "ALxx" 作为新编号；新点位 ID 为 `M-<路由>-<模式>-<类别>-<NTH>`；对照表见 ERRATA_3 e 节。
- **c. R2 的 T-2、T-3、T-8 是违反写入规则的事件**（见第 10 节表二），不是"目标合法"的例外。T-3 另含 `2>/dev/null`。
- **d. 其它勘误**：R2 树路径（d1）；驱动无调试段（d2）；R1 行号是 B 树（37a82e8）的行号，不是 F 的（d3，已用 `git grep` 核对）；分配大小公式（d4）；GetFieldOnGrid 为非 FMM 且在 B 与 F 上都检查返回值（d5，已修正为两树）；discovery 不可见 S4.o 内的 S4_malloc（d7）。
- **e. R2 AL05/AL08/AL11 的 "NTH5" 标签是错的**：在 route once 上 NTH5 不可达（只有 4 次 malloc）；在 route twice 上 NTH5 是 ClosedForm 的 192 B ivalues，不是 vfield。
- **f. plan 注入可达性（实测修正）**：NTH 1 与 2 在所有测试模式中可达（hit = 1）；NTH 3 至 16 不可达（hit = 0）。此前"只能命中 NTH 1"的读法**撤回**（f2）。"hit=2" 的日志行是 n_plan_alloc，不是命中次数（f3）。机理（每次 plan 调用可截获的 malloc 数）**未测量，是推断**（f4）。
- **g. 四个 MISMATCH 行**：B 树 jones 与 vl 的 NTH4（1024 B vfield）观察为 SILENT_SWALLOW，预注册期望为 CRASH。R2 已观察到同样的 SILENT_SWALLOW（AL04-B、AL10-B），R3 与 R2 完全一致；nv NTH4 为 CRASH，与 R2 的 AL07-B 一致。**预注册 basis 没有写出这一已知观察，这是预注册 basis 的遗漏**（g3），注册表未改，行保持 MISMATCH。机理未确定（g4）。

## 5. 调用序摘要（CALLSEQ，发现轮，无注入）

每个模式在 F 树、重复 1 上的调用数（B 与 F 的规范字段完全相同，两次重复完全相同）。FMM 侧是调用者在 `S4/fmm/` 下的调用；GetFieldOnGrid 是 `S4/rcwa.cpp` 的非 FMM 调用。

| 模式 | 路由 | malloc（FMM） | plan（FMM） | exec（FMM） | plan（GetFieldOnGrid） | exec（GetFieldOnGrid） |
|---|---|---|---|---|---|---|
| fft | once | 2 | 5 | 5 | 12 | 12 |
| kottke | once | 1 | 5 | 5 | 12 | 12 |
| jones | once | 4 | 1 | 4 | 12 | 12 |
| nv | once | 4 | 1 | 4 | 12 | 12 |
| vl | once | 4 | 1 | 4 | 12 | 12 |
| experimental | once | 1 | 0 | 0 | 12 | 12 |
| closed1d | once | 1 | 0 | 0 | 12 | 12 |
| closed2d | once | 1 | 0 | 0 | 12 | 12 |
| fft | twice | 4 | 10 | 10 | 12 | 12 |
| kottke | twice | 2 | 10 | 10 | 12 | 12 |
| jones | twice | 7 | 1 | 4 | 12 | 12 |
| nv | twice | 7 | 1 | 4 | 12 | 12 |
| vl | twice | 7 | 1 | 4 | 12 | 12 |
| experimental | twice | 2 | 0 | 0 | 12 | 12 |
| closed1d | twice | 2 | 0 | 0 | 12 | 12 |
| closed2d | twice | 2 | 0 | 0 | 12 | 12 |

要点：
- **B 与 F 调用序一致**：以 (类别, NTH, 大小, 调用者函数) 比较，两条路由、八个模式全部相同。之前出现的差异只来自函数内偏移量（`+NNN`），不是调用序差异。F 没有新增或删除 S4_malloc、plan、exec 调用。
- **可复现**：每个 (路由, 树, 模式) 组的两次重复调用序哈希相同。共 32 组（2 路由 × 2 树 × 8 模式），全部一致（rep1 = rep2）。
- **route twice 的第二次字段调用**（`S4_Simulation_GetFieldPlane` 的第二次入口，FIELDCALL_MAP）包含 cache-hit 的分配（Jones/NV/VL NTH 5–7：ClosedForm 192 B、PolBasis 192 B、cache-hit work 1296 B 或 2592 B）以及 FFT/kottke 的第二次 plan 与 exec（NTH 12–16）。
- **驱动每次运行调用两次字段计算**（driver_d003.cpp 第 193 行与第 220 行）；`once` 路由与 `twice` 路由都是两次调用，区别只在第二次调用前是否销毁 layer 1 的 modes（`S4FMM_TWICE=slab`）。

## 6. 站点映射（SITEMAP）与 R1 对照

**SITEMAP：525 点 = 141 范围内（YES）+ 384 范围外（NO）。** point_id 为 `M-<路由>-<模式>-<类别>-<NTH>`。

- **范围内（YES，141）**：调用者为 `FMMGetEpsilon_*`（`S4/fmm/`）。类别：exec 54、malloc 51、plan 36。
- **范围外（NO，384）**：全部为 `GetFieldOnGrid` 的 plan（192）与 exec（192）。**范围外没有任何 malloc 点**（见第 7 节）。

**R1 对照（COVERAGE_R3.tsv）**：REGISTRY_S4_PRE.tsv 共 62 个 ID。

- **有映射（32 个 ID）**：P01–P05、EX01–EX10（EX05–EX08 合并为一组集合，见下）、AL01、AL03–AL17（AL02 见下）、EXP40。
- **EX05–EX08 集合标签**：Jones exec 有 4 个不同的返回地址，但它们与源码行 258/277/296/315 的一一对应**未确认**。因此 EX05–EX08 合为一组（8 个 R3 点），不各自声称覆盖。
- **UNMAPPED（30 个 ID）**，原因逐个列在 COVERAGE_R3.tsv 的 note 列：
  - AL02：与 EXP40 同一源码站点（experimental.cpp:40），R1 重复登记。
  - AL18：fmm_kottke.cpp:78 的 fft_alloc_complex 不经 S4_malloc，需 kottke_alloc 通道（R2 族 D），本轮未用。
  - FE01–FE10：fmm_ret 状态，需 fmmret seam，plain 构建中不存在。
  - SI01–SI02：solve_info，需 linearsolve seam。
  - CL01–CL04、PJ01、PN01、PV01：info=NULL，需 linearsolve_null seam。
  - CLM1：libc malloc（S4.cpp:2267）；注入器与 discovery 只挂 S4_malloc、fft_plan、fft_plan_exec 的包装，不能观察或选择该 libc 调用。
  - CLM2–CLM4、ACF1：S4.o 内的 S4_malloc，--wrap 不能截获（P05_S2_TEST_HARNESS.md 第 115、488 行）；需分配 seam。
  - K1A、K1B、D016、RNV1：数值或零场检查，不是分配/plan/exec 点，不在 R3 穷举范围。

**UNMAPPED_R1 的说明**："未确认"只写在没有源码或装置原因的地方；本表中的每个原因都能由源码、装置结构或 ERRATA_3 给出。

## 7. 预注册 v3（REGISTRY_S4_PRE_R3.tsv）

- **sha256**：`fc0c060b44200ee57059c3a0db8c5dae2af11efc6d2e02618731959e7841e428`（记录于 `REGISTRY_S4_PRE_R3.sha256`，写入时间早于任何 R3 注入运行）。
- **行数**：282（141 个范围内点 × B、F）。status 全部为 INFLUENCED（R1、R2 与 discovery 在写入前已读）。
- **期望规则（事先固定）**：F 列 malloc、plan、exec 均为 REPORTED_FAILURE（源码核对：HEAD 上每个 FMM 分配后都有 NULL 检查，plan 与 exec 的返回值都被检查）；B 列 malloc 与 plan 为 CRASH，exec 为 SILENT_SWALLOW。
- **已知冲突**：B 列 jones 与 vl NTH4（1024 B）的已有观察为 SILENT_SWALLOW，预注册 basis 未写出（ERRATA_3 g3）。
- **范围外（NO）**：不登记期望，行数不计入预注册；只记录观察（第 9.3 节）。

**范围外 S4_malloc 静态计数（只读 git grep，不是 discovery 观测）**：HEAD 上 `S4/S4.cpp` 有 36 处非注释的 S4_malloc 调用（B 37a82e8 上同样为 36）；`S4/S4_internal.h` 有 1 处声明。**任务书估计的"约 43 处"与静态计数 36 不一致，差 7，原因未查明。** 这 36 处全部位于 S4.cpp，与 S4_malloc 定义同一翻译单元，因此 --wrap 不能截获。**本轮不能获得它们按模式的观察类别（不可注入），因此范围外 S4_malloc 的"按模式分"计数不适用本轮方法。** FMM 侧非注释 S4_malloc 静态计数（HEAD，S4/fmm/，`git grep` 排除注释行后）为 17 处：fmm_FFT 2、Jones 4、NV 4、VL 4、closed 1、experimental 1、kottke 1（与 ERRATA_2 的 17 一致）。另有 kottke:78 的 `fft_alloc_complex`（AL18）不经 S4_malloc，HEAD 上有 `if(NULL == work){ return 1; }` 检查，B 上无检查。

## 8. 穷举注入结果（RESULTS_R3.tsv 与三张表）

### 8.1 汇总

- **YES 注入（306 次运行 = 282 个注入 + 24 个控制）**：MATCH 258（含 24 个控制）、MISMATCH 4、INVALID 44。
- **范围内 141 点**：在 B 与 F 两树都命中（hit ≥ 1）的点 **119**；未命中（INVALID）的点 **22**。两者合计 141，无混合点。
- **范围外（768 次运行，384 点 × B、F）**：B 与 F 观察类别分布相同（REPORTED_FAILURE 210，INVALID 174），无 CRASH、无 SILENT_SWALLOW。

### 8.2 INVALID（未命中）

全部 44 行（22 点 × B、F）是 plan 类，且全部位于 fft 与 kottke 的 NTH ≥ 3（route once 与 twice）。范围外的 INVALID（174 × 2）同为 plan NTH ≥ 3。**这是注入器对 plan 的覆盖限制（ERRATA_3 f），不是调用序不可复现（调用序已在 32 组重复中核对一致），也不是模式依赖（所有模式 NTH 1 与 2 一致可达）。** 机理（每次 plan 可截获的 malloc 数）未测量，列为 R4 测量项。

### 8.3 MISMATCH（4 行）

B 树 M-once-jones-malloc-4、M-twice-jones-malloc-4、M-once-vl-malloc-4、M-twice-vl-malloc-4：观察 SILENT_SWALLOW（rc 1，rc1 0，hit 1），预注册期望 CRASH。与 R2 的 AL04-B、AL10-B 完全一致（ERRATA_3 g）。**F 列没有 MISMATCH。**

### 8.4 覆盖表（摘录；完整表见 COVERAGE_R3.tsv）

| R1 ID | 状态 | R3 点 | B 观察 | F 观察 |
|---|---|---|---|---|
| AL01（closed/PolBasis ClosedForm ivalues 192 B） | 命中 15/15 | 15 点 | CRASH | REPORTED_FAILURE |
| AL03（FFT work 6144 B） | 命中 3/3 | 3 点 | CRASH | REPORTED_FAILURE |
| AL04（FFT discval 16 B） | 命中 3/3 | 3 点 | CRASH | REPORTED_FAILURE |
| AL05（kottke discval 16 B） | 命中 3/3 | 3 点 | CRASH | REPORTED_FAILURE |
| AL06（Jones ivalues 192 B） | 命中 3/3 | 3 点 | CRASH | REPORTED_FAILURE |
| AL07（Jones work 10720 B） | 命中 2/2 | 2 点 | CRASH | REPORTED_FAILURE |
| AL08（Jones vfield 1024 B） | 命中 2/2 | 2 点 | **SILENT_SWALLOW** | REPORTED_FAILURE |
| AL09（Jones cache-hit work 1296 B） | 命中 1/1 | 1 点（twice） | CRASH | REPORTED_FAILURE |
| AL10（NV ivalues 192 B） | 命中 3/3 | 3 点 | CRASH | REPORTED_FAILURE |
| AL11（NV work 11872 B） | 命中 2/2 | 2 点 | CRASH | REPORTED_FAILURE |
| AL12（NV vfield 1024 B） | 命中 2/2 | 2 点 | CRASH | REPORTED_FAILURE |
| AL13（NV cache-hit work 2592 B） | 命中 1/1 | 1 点（twice） | CRASH | REPORTED_FAILURE |
| AL14（VL ivalues 192 B） | 命中 3/3 | 3 点 | CRASH | REPORTED_FAILURE |
| AL15（VL work 11872 B） | 命中 2/2 | 2 点 | CRASH | REPORTED_FAILURE |
| AL16（VL vfield 1024 B） | 命中 2/2 | 2 点 | **SILENT_SWALLOW** | REPORTED_FAILURE |
| AL17（VL cache-hit work 2592 B） | 命中 1/1 | 1 点（twice） | CRASH | REPORTED_FAILURE |
| EXP40（experimental ivalues 192 B） | 命中 3/3 | 3 点 | CRASH | REPORTED_FAILURE |
| P01（FFT plan） | 命中 4/15 | 15 点 | CRASH 或 INVALID | REPORTED_FAILURE 或 INVALID |
| P02（kottke plan） | 命中 4/15 | 15 点 | CRASH 或 INVALID | REPORTED_FAILURE 或 INVALID |
| P03、P04、P05（Jones/NV/VL plan） | 命中 2/2 各 | 2 点 | CRASH | REPORTED_FAILURE |
| EX01–EX10（exec，EX05–EX08 为集合） | 命中（EX01 2/2，EX02 13/13，EX03 2/2，EX04 13/13，集合 8/8，EX09 8/8，EX10 8/8） | — | SILENT_SWALLOW | REPORTED_FAILURE |

"命中"指该点在 B 与 F 上 hit ≥ 1。范围内点总数 141，命中 119，未命中 22。**覆盖表中的 REPORTED_FAILURE 只说明在该注入下 rc1 ≠ 0。它不说明代码已修好或已验证。**

### 8.5 红点表（F 列，范围内；完整表见 RED_POINTS_R3.tsv）

**F 列红点 = 22 点，全部为未命中（INVALID，hit 0）。F 列没有 CRASH，也没有 SILENT_SWALLOW。**

| 点 | 模式 | 类别 | NTH | 调用者 | rc | rc1 | 信号 | hit |
|---|---|---|---|---|---|---|---|---|
| M-once-fft-plan-3/4/5、M-twice-fft-plan-3/4/5 | fft | plan | 3,4,5 | FMMGetEpsilon_FFT | 1 | 0 | - | 0 |
| M-twice-fft-plan-12…16 | fft | plan | 12–16 | FMMGetEpsilon_FFT | 1 | 0 | - | 0 |
| M-once-kottke-plan-3/4/5、M-twice-kottke-plan-3/4/5 | kottke | plan | 3,4,5 | FMMGetEpsilon_Kottke | 1 | 0 | - | 0 |
| M-twice-kottke-plan-12…16 | kottke | plan | 12–16 | FMMGetEpsilon_Kottke | 1 | 0 | - | 0 |

这些红点**只记录，本轮不修，不改 S4/**。它们是测量不可达，不是 FMM 失败的证据。

### 8.6 范围外计数表（完整表见 OUTSCOPE_COUNT_R3.tsv）

| 类别 | 树 | 观察类别 | 次数 |
|---|---|---|---|
| exec（GetFieldOnGrid） | B | REPORTED_FAILURE | 192 |
| exec（GetFieldOnGrid） | F | REPORTED_FAILURE | 192 |
| plan（GetFieldOnGrid） | B | REPORTED_FAILURE | 18 |
| plan（GetFieldOnGrid） | B | INVALID | 174 |
| plan（GetFieldOnGrid） | F | REPORTED_FAILURE | 18 |
| plan（GetFieldOnGrid） | F | INVALID | 174 |
| S4_malloc（非 FMM，S4.cpp） | — | 观察不可得（wrap 盲区，见第 7 节） | 静态 36 |

范围外不当红点。GetFieldOnGrid 的 exec 在 B 与 F 上都报告失败，与源码（两树都有检查）一致。GetFieldOnGrid 的 plan 只有 NTH 1、2 可达（REPORTED_FAILURE），其余不可达。

## 9. 方法与判定的说明

### 9.1 判定
判定由 `judge_d003.classify` 直接给出（运行器调用它，传入显式的 `inj_call`），只读取 rc、rc1、rc2、hit 等事实，不读驱动的 PASS/FAIL 行。`match` 由 expected、observed 与 hit 派生：hit = 0 为 INVALID；hit ≥ 1 且相等为 MATCH；否则 MISMATCH。控制行 hit = 0 是正确值，按 CONTROL_OK 判定，不计为 INVALID。

### 9.2 inj_call
驱动每次运行调用两次字段计算。判定读取的返回码由注入所在的字段调用决定（FIELDCALL_MAP）：第 1 次用 rc1，第 2 次用 rc2。这一选择来自 discovery，不是猜测。rc1 = 0 的 REPORTED_FAILURE 全部是 inj_call = 2 的点，判定用的 rc2 = 20。

### 9.3 范围外
范围外点不登记期望，只记录观察。它们不计 MATCH 或 MISMATCH，不当红点。

### 9.4 summarize_r6.py 未运行（偏离）
任务书要求判定只用 judge_d003.py 或 summarize_r6.py 的现有输出，并在出现 UNDECLARED 时停止。`summarize_r6.py` 读取 `run_all.sh` 的 matrix 目录布局（`matrix/runs/<tag>/pass<N>/raw_*.json`）与冻结索引，本轮的扫描不产生该布局，强行适配会制造不存在的汇总。因此**未运行 summarize_r6.py**。判定类别直接来自 `judge_d003.classify`，它不产生 UNDECLARED 类别。4 个 MISMATCH 与 R2 的已有观察一致（ERRATA_3 g），但预注册 basis 未写出该观察（g3），因此它是预注册的遗漏，不是未声明的新偏差。**这是需要用户裁决的偏离。**

## 10. 违规披露

### 10.1 表一：越界写入尝试（命令自身写了仓库外路径）

本轮**没有命令写入仓库外路径**。依据：`/tmp` 顶层与第 3 层的 START/END 快照未变（第 2 节）；所有写入目标均在 `$EV`（`checkpoints/p05/evidence/p05-s4r3/`）或 `testing/d003/stage_s4/`（新文件，r3 命名）内；gdb 的 index-cache 警告未产生 `~/.cache/gdb` 或 `/tmp` 下的新条目。

| 编号 | 轮次 | 命令 | 是否落盘 |
|---|---|---|---|
| — | — | 无 | — |

### 10.2 表二：工具与脚本事件

| 编号 | 轮次 | 命令 / 事件 | 是否落盘 | 处理 |
|---|---|---|---|---|
| T-1 | R3-1 之后（单次运行计时） | 一条计时命令（`date` 与 `bc`）中含 `cd /tmp 2>/dev/null` 与 `> /dev/null`：`cd` 切换到仓库外目录，并把 stderr 丢弃 | 否（cd 不写文件；`> /dev/null` 是系统路径；未写入仓库外） | 违反"含写入的命令不得用 2>/dev/null"与"不引入仓库外路径"的精神（该命令不含写入，但仍不符合规则）；已披露 |
| T-2 | R3-0 | `write` 工具创建 `testing/d003/stage_s4/r3_*` 脚本，未经 safe_run | 是（仓库内，路径合规） | 工具写入，非 bash；路径合规；已披露 |
| T-3 | R3-1 | `sh … > "$EV/…"`、`python3 … > …` 的写入命令在第一版中未经 safe_run：`r3_sitemap.py` 首次运行（经 safe_run，写 `SITEMAP.tsv`，因 TypeError 而未完成） | 是（`$EV` 内，部分写入后被覆盖） | 脚本错误；随后经 safe_run 重做；已披露 |
| T-4 | R3-2 | `r3_sitemap.py` 的 CONFLICT 合并键错误（同一 NTH 在两路由指向不同调用） | 否（脚本在写入前退出） | 改为按路由分 point_id；已披露 |
| T-5 | R3-3 | `write` 写入 `ERRATA_3.txt`（checkpoints/p05 下，合规）及其多次 `edit` 修订 | 是（`$EV` 内） | 勘误文件可修订（预注册未变，已用 sha256 核对）；已披露 |
| T-6 | R3-3 | `REGISTRY_S4_PRE_R3.tsv` 的哈希记录写入于 sha256 之后又做了 `sha256sum -c` 核对；ERRATA_3 修订后 `REGISTRY_S4_PRE_R3.sha256` 含 ERRATA 的旧哈希（ERRATA 不属于预注册，不影响预注册的有效性） | 是（`$EV` 内） | 已披露；预注册文件未变 |
| T-7 | R3-4 | 运行器 `run_r3_sweep.py` 第一次调用 argv 计数错误（`usage` 退出） | 否（在建目录前退出） | 修正后重跑；已披露 |
| T-8 | R3-4 | 试验运行 `sweep_pilot/`（1 个 YES 点 + 控制，经 safe_run）发生在正式 sweep 之前 | 是（`$EV/sweep_pilot/`，合规） | 试验在预注册哈希核对之后、正式 sweep 之前运行；试验结果与预注册一致；已披露为时序事实，期望未改 |
| T-9 | R3-5 | `comm` 比较输出 `comm: file 2 is not in sorted order`（stderr 未隐藏），结果不可靠 | 否（只读） | 该结果已撤回，改用 Python 集合差；已披露 |
| T-10 | R3-5 | `r3_tables.py` 第一版把控制行计入红点（8 行 CTL） | 是（`$EV` 内，已覆盖） | 修正为排除控制行；已披露 |
| T-11 | R3-5 | `r3_results.py` 第一版把控制行计为 INVALID（68 行，应为 44 + 控制） | 是（`$EV` 内，已覆盖） | 修正为控制行按 CONTROL_OK 判定；已披露 |
| T-12 | R3-5 | `r3_coverage.py` 第一版对 EX05–EX08 重复声称四个站点各自覆盖 | 是（`$EV` 内，已覆盖） | 改为集合行；已披露 |
| T-13 | R3-1 | gdb 运行时输出 `Couldn't determine a path for the index cache directory`（gdb 内部） | 否（已核对 `~/.cache/gdb` 不存在，`/tmp` 未变） | gdb 行为，非执行者写入；已披露 |

本轮没有出现 `find`/`ls` 等核对命令的 `2>/dev/null` 写入。核对路径只用 `ls -d`、`test -e` 或 `find -newer`（只读）。

## 11. R4 建议

1. **F 上 seam 锚点失败需要重新定位（任务书要求）**。`apply_seam_r2.py --check-only` 在 F 上报 ANCHOR ERROR。R4 应改用"函数名 + 第 n 次出现 + 紧邻上下文"的方式，在导出副本上重新定位，覆盖以下点：SI01–SI02、AL18、FE01–FE10、info=NULL 七处（CL01–CL04、PJ01、PN01、PV01）、CLM1–4、ACF1、EXP40。**这些点在本轮没有覆盖的原因**：SI 与 info=NULL 需要 linearsolve 族 seam（plain 构建中不存在）；FE 需要 fmmret seam；AL18 需要 kottke_alloc 通道；CLM 与 ACF 在 S4.o 内，--wrap 不能截获；EXP40 在本轮已覆盖（3/3 命中），但 R1 的 EXP40 与 AL02 为同一站点，R4 应统一。
2. **plan 注入覆盖（ERRATA_3 f）**。测量每个 fft_plan_dft_2d 调用内可截获的 malloc 数（gdb 断点计数），以确认 NTH ≥ 3 不可达的机理（f4）。若要覆盖 plan 的第 k 次调用，需要新的注入方式（按调用序选择，而非按内部 malloc 序），这需要用户批准修改注入器。
3. **Jones/NV/VL 的 B 树 vfield NTH4 差异（ERRATA_3 g）**：确定 NV 为 CRASH、Jones 与 VL 为 SILENT_SWALLOW 的控制流原因（读 NULL 之后直到第一次 vfield 写入的分支，或 gdb 断点）。同时修正预注册 basis（新文件 `*_R4_ERRATA.txt`，不改 R3 预注册）。
4. **Jones exec 的站点映射（EX05–EX08）**：把四个返回地址与源码行 258/277/296/315 一一对应（gdb 的 `info line *ADDR` 需要调试信息，或反汇编比对），以消除集合标签。
5. **范围外 S4_malloc 计数**：源码静态计数为 36（非 FMM，S4.cpp），与任务书估计的 43 不一致，差 7，需要核对口径。若要获得它们的观察类别，需要 S4.o 内分配的 seam（R2 族 C），而不是 --wrap。
6. **summarize_r6.py 的适配或替代**：本轮未运行它（第 9.4 节）。R4 应明确判定汇总的输入布局，并由用户裁决是否需要 UNDECLARED 检查。
7. **K1A、K1B、D016、RNV1**：数值与零场检查不是本轮的穷举对象，需要由 S3R 与 S3R2 的探针结果单独登记，不混入 R4 的分配/plan/exec 穷举。

## 12. 提交与路径清单

**提交范围（仅此）**：`testing/d003/stage_s4/` 下新增的 13 个 r3 文件，以及本报告 `checkpoints/p05/P05_S4R3_REPORT.md`。证据目录 `checkpoints/p05/evidence/p05-s4r3/` 被 `.git/info/exclude` 忽略，不提交。

新增的 r3 脚本：`r3_callseq.gdb`、`r3_callseq_fc.gdb`、`r3_callseq_parse.py`、`r3_coverage.py`、`r3_fieldcall_map.py`、`r3_prereg.py`、`r3_results.py`、`r3_sitemap.py`、`r3_tables.py`、`run_r3_discovery.sh`、`run_r3_discovery_fc.sh`、`run_r3_sweep.py`、`run_r3_sweep_out.py`。

证据（不提交）：`checkpoints/p05/evidence/p05-s4r3/`：`GATE_R3.txt`、`ERRATA_3.txt`、`CALLSEQ.tsv`、`FIELDCALL_MAP.tsv`、`SITEMAP.tsv`、`REGISTRY_S4_PRE_R3.tsv`、`REGISTRY_S4_PRE_R3.sha256`、`RESULTS_R3.tsv`、`COVERAGE_R3.tsv`、`RED_POINTS_R3.tsv`、`OUTSCOPE_COUNT_R3.tsv`、`discovery/`、`discovery_fc/`、`sweep_pilot/`、`sweep_yes/`、`sweep_out/`、`safe_run.log`。

仓库中已有的 `.git/lost-found/` 仍然存在（`ls -d` 确认）。本轮未运行 fsck，未删除其中的 148 个悬挂对象。

**未修改**：`S4/` 下所有文件、`RNP/`、`rcwa.cpp`、`testing/d003/` 下已有文件（judge_d003.py、matrix_d003.py、matrix_r2.py、run_d003.sh、run_all.sh、safe_run.sh、summarize_r6.py、src/、seam/、stage_s4/ 下 R1/R2 的 8 个脚本）。`git status --short` 仅显示 13 个未跟踪的 r3 脚本。

**结论**：本轮完成了 R3 范围（调用序发现、站点映射、预注册 v3、穷举注入、三张表）。在范围内 141 点中，119 点在 B 与 F 两树都被注入并观察；22 点（plan NTH ≥ 3）因注入器限制未命中。F 列没有 CRASH 与 SILENT_SWALLOW，但这只适用于本轮可注入的点，不构成"已修好"或"已验证"。**本轮未完成，等待用户审核。P05-S4 未签收。**
