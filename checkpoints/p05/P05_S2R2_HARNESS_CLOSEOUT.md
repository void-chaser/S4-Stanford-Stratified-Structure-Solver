# P05-S2R2 补充轮收尾报告：D003 测试装置缺口补齐

> **状态：未完成，等待用户审核。**
> 本报告不宣布 P05-S1、P05-S2、P05-S3、P05-S4 中任何一个阶段完成。
> 本轮是正式阶段 **P05-S2（测试装置）** 的补充轮收尾子任务，**不是新阶段**。P05 固定五阶段 S1–S5，未引入 S6。
> 本报告只记录装置的灵敏度与红/绿事实，**不对 D003 修复效果作验证结论**。修复属于 P05-S3 补充轮，验证属于 P05-S4。
>
> 分支：`codex/p05-d003-fft-error-propagation`
> 起点 HEAD：`aa1c51d`（已核对：工作区干净，`S4/` 相对 `8d60dfb` 改动为 0）
> 基线：`37a82e8`（`8d60dfb` 的祖先，已核对）
> 证据目录：`checkpoints/p05/evidence/p05-s2r2/`（被 `.git/info/exclude` 忽略，**未提交**）

**证据类型标注**：[源码] 只读阅读源码并逐行回查；[实测] 本轮运行或 gdb 测量的原始输出；[推断] 由实测与源码得出，未直接验证；[未验证] 本轮无证据。

---

## 0. 定位、阶段定义依据与未完成声明

- **阶段定义依据用户提示词**。仓库内无 P05 原始计划文档（S2R 已搜索确认，本轮按要求不再搜索）。
- P05-S2 的定义（用户提示词）：扩展注入器覆盖 S4_malloc、LinearSolve 与两步分支，接入仓库测试目录，源码仅改 testing/ 并允许必要的测试专用 seam。
- 本轮目的：补齐 S2R 报告 §9.3 与 D-11、D-12 所列的装置缺口，使 P05-S3 补充轮的"修前红、修后绿"证据完整。**不修复任何产品缺陷。**
- 用户对 S2R 三个裁决点的决定（本轮登记归属依据）：info=NULL 的 7 处纳入 D003；`fmm_experimental:40` 纳入但验证标"仅静态走查/驱动不可达"；ComputeLayerModes 4 点与 AddFieldToCache 由 S3 补充轮接手。

---

## 1. 起点核对 [实测]

| 项 | 结果 |
|---|---|
| HEAD | `aa1c51d`，分支 `codex/p05-d003-fft-error-propagation`（核对一致） |
| 工作区开始状态 | 干净（0 条目） |
| `S4/` 相对 `8d60dfb` 改动 | 0（git 树哈希 `85feec1151b3` 在两个提交相同） |
| 基线 `libS4.a` sha256（`37a82e8` 导出构建） | `fb9ac3f5fd2c121619bb6cd464816f97a3085c8e4a2795a2b5037b370110ffba`（**与要求值一致，门禁通过**） |
| 当前树 `libS4.a` sha256（`aa1c51d` 导出构建） | `865c58938e18220a3e7f02f7cb7b05cf83bce36ec28005fcf0bb4f1b4701b1da` |
| 基线导出与 git 对象 | 70 个 S4 文件逐字节一致（差异 0），导出中无任何 seam 宏 |
| `/tmp` 顶层快照（开始） | sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`，条目 0 |

---

## 2. T1：`fmm_kottke.cpp:78` 的 `fft_alloc_complex`

### 2.1 范围判定 [源码 + 实测 census]

`fft_alloc_complex` 是普通函数（不走 `S4_malloc`），`--wrap` 不可达；它在两处被调用：

| 调用点 | 次数（kottke 一次运行） | 调用者 | 判定 |
|---|---|---|---|
| `rcwa.cpp:2204/2206`（GetFieldOnGrid） | 24 次，size=12 | 场输出路径（`S4.cpp:3494`、`:4308`） | **范围外**：非模式/缓存安装，非 FMM/FFT 失败传播链；且 rcwa.cpp:51/:53 已做 NULL 检查 |
| `fmm_kottke.cpp:78`（FMMGetEpsilon_Kottke） | 1 次，size=384（=6·ng2） | FMM 介电张量生成 | **范围内**：目标点 |

**因此注入必须只作用于 kottke 这一个站点**（站点级钩子）。若用全局 `--wrap`，第 k 次命中会落在 24 次场输出调用中，计数失去意义。

### 2.2 家族 D seam [源码 + 实测]

- 宏 `S4_TEST_KOTTKE_SEAM`，钩子 `S4_TEST_KOTTKE_HOOK(31, n)`，请求前缀 `kottke_alloc:`，与家族 A/B/C 互不为前缀（已核对）。
- 站点替换：`#ifdef S4_TEST_KOTTKE_SEAM` … `#else` 保留原行 `#endif`。
- **叠加问题（已用探针证明并修复）**：家族 A 与家族 D 都改 `fmm_kottke.cpp`。若各自从磁盘原文独立生成，后写者覆盖先写者。探针显示 A 的钩子在独立计划中丢失。修复：D 叠加在 A/B 输出之上（`plan_replace(base_text=…)`），组合应用后两家族钩子各 1 个，均存在。

### 2.3 默认构建字节一致性 [实测]

| 检查 | 结果 |
|---|---|
| 四家族全部叠加、宏未定义，`g++ -E -P`（kottke/S4.cpp/FFT/closed） | **4/4 逐字节一致**（kottke 1309267 B、S4.cpp 1403658 B、FFT 1310077 B、closed 1295197 B） |
| 四家族叠加、宏未定义，全部 24 个目标文件 vs 纯净 `cur-aa1c51d` | **24/24 逐字节一致** |
| 仅定义家族 D 宏，目标文件 | **仅 `fmm_kottke.o` 改变**（归属正确） |
| 家族 C 重构前后 `S4.cpp` sha256 | 均为 `0edb534c93bc103a`（重构不改变行为） |

### 2.4 命中确认与红/绿结果 [实测]

| 树 | 请求 | rc | HITCOUNT | RC first | 判定 |
|---|---|---|---|---|---|
| BASE 37a82e8 | `kottke_alloc:31:1` | 139（SIGSEGV） | 1 | — | **CRASH** |
| CUR aa1c51d | `kottke_alloc:31:1` | 1 | 1 | **20** | **REPORTED_FAILURE** |
| 两树 | `kottke_alloc:31:2`（第 2 次，单次运行只调用 1 次） | 1 | 0 | 0 | INVALID（未命中） |

- BASE 的 CRASH 与源码走查预期一致：`kottke.cpp:79` 无检查，`work` 为 NULL 时首个写入在 `:119`（`fxx[...] = …`）。
- CUR 的 `RC first 20` 来自 `fmm_kottke.cpp:79` 的 `return 1` 经 `S4.cpp:2400–2403` 传播为 20。
- 两轮运行（T5）结果一致（见 §6）。

---

## 3. T2：15 个可达 FMM S4_malloc 调用行的预注册

### 3.1 调用行清单与覆盖 [源码 + 实测]

- 15 个调用行 = (模式, 调用序号)：`fft` 2、`kottke` 1、`jones` 4、`nv` 4、`vl` 4。由 gdb 按 `%rdi` 尺寸与回溯测得（S2R `R2C_FMM_S4MALLOC_RUNTIME_REACH.txt`，本轮以 `attr-kottke/`、`attr-closed/` 复核）。
- 15 行映射到 **13 个不同源码站点**（`closed.cpp:40` 被 jones/nv/vl 三个模式共享）。

### 3.2 源码推导的方法 [源码]

- 每个点的基线预期 = **分配指针的第一个真实解引用**（或确认永不发生）。读取方法：内容匹配定位行号（不依赖记忆行号），追踪指针别名，检查分配与解引用之间的分支/返回。
- 当前树预期 = 分配后的 NULL 检查返回 1，经 `S4.cpp:2400–2403` 变为 20（REPORTED_FAILURE）。
- 工作表 v3（`T2_SOURCE_WORKSHEET_v3.txt`）逐点记录依据。

### 3.3 预注册的性质 [必须披露]

- **登记不是盲预注册。** 本轮在运行前已读取 S2R 的结论（它在上下文中）。登记文件逐行标注 `DERIVED`（读源码时未见 S2R 结果）或 `INFLUENCED`（已见 S2R 结果）。INFLUENCED 行共 9 行（见 `REGISTRY_T2_v2.tsv` 第 4 列之后的标注）。
- 对 INFLUENCED 行，"预期与运行一致"只能说明它与此后的重复测量相符，**不能证明它是独立预测**。

### 3.4 登记文件与完整性 [实测]

| 文件 | 行数 | 登记时间戳（UTC） | sha256（登记时记录值 = 当前值，已核对 UNCHANGED） |
|---|---|---|---|
| `REGISTRY_T2_v2.tsv` | 28 | 2026-10-11T05:20:27Z | `a582e149d0744af553e31693ac585673c1118b9ab13e81d9e9e10e482156fd5e` |
| `REGISTRY_T2_v2_SUPPLEMENT.tsv` | 4 | 2026-10-11T05:21:01Z | `7d9d9aca71d274bd0c7b8fb40dbf4f8c0afe61de8abfd5ac5c542ed14f0e02de` |

- **覆盖遗漏（已披露）**：原登记对 `closed:40` 只为 jones 登记了一次，遗漏了 nv 与 vl 的同一站点调用。由覆盖检查发现，经补充文件修正（另存、不改原文件，原哈希保持）。补充行依据与 jones 行相同，并标注为"在原登记之后写入"。

### 3.5 T2 运行结果 [实测]

| 点（基线→当前树） | 基线 | 当前树 |
|---|---|---|
| FFT work（fmm_FFT:74） | CRASH | REPORTED_FAILURE |
| FFT discval（:81） | CRASH | REPORTED_FAILURE |
| kottke discval（:85） | CRASH | REPORTED_FAILURE |
| closed ivalues（:40，jones/nv/vl 各一行） | CRASH ×3 | REPORTED_FAILURE ×3 |
| Jones ivalues（:107） | CRASH | REPORTED_FAILURE |
| Jones work merge（:155） | CRASH | REPORTED_FAILURE |
| Jones vfield（:167） | **SILENT_SWALLOW** | REPORTED_FAILURE |
| NV ivalues（:58） | CRASH | REPORTED_FAILURE |
| NV work（:110） | CRASH | REPORTED_FAILURE |
| NV vfield（:122） | CRASH | REPORTED_FAILURE |
| VL ivalues（:57） | CRASH | REPORTED_FAILURE |
| VL work（:115） | CRASH | REPORTED_FAILURE |
| VL vfield（:127） | **SILENT_SWALLOW** | REPORTED_FAILURE |

- 所有 16 个 T2 行（每树 16）在**两轮运行**与**两种驱动**（`driver-all` 与 `driver-all-t4`）下，事实（类别、rc、rc1、rc2、hit）逐行一致（差异 0）。

### 3.6 vfield 的 SILENT 与 CRASH 的机理 [源码]

- **Jones/VL vfield（SILENT）**：`Pattern_GenerateFlowField(NULL)` 返回 −8 且不写入；函数有 `if(0 != error)` 检查并 `return error`；但基线 `S4.cpp` 对 `FMMGetEpsilon_PolBasis*` 的调用是裸调用（丢弃返回值），因此静默继续。
- **NV vfield（CRASH）**：流场调用后**无错误检查**，归一化循环 `hypot(vfield[0], …)` 第一次读取即解引用 NULL。

---

## 4. T3：静态登记、INJECTION_POINTS v2、驱动不可达点

### 4.1 驱动不可达点（仅静态走查，**无运行结果**）[源码]

登记文件 `REGISTRY_T3_static.tsv`（5 行，sha256 `f1afb7183a8c7cd0…`，时间戳 2026-10-11T05:23:09Z）：

| 点 | 驱动可达性 | 基线/当前树状态 | 完成判据（S3 补充轮） |
|---|---|---|---|
| closed:130（id 11） | 不可达（驱动 Lr={1,0,0,1}，1-D 分支不进入） | 未检查 | `&info` 传入、检查、失败返回 20、不安装缓存 |
| closed:133（id 12） | 不可达（同上） | 未检查 | 同上 |
| closed:138（id 13） | 不可达（需 `!use_polarization_basis`，驱动 ClosedForm 模式均置位） | 未检查 | 同上 |
| closed:235（id 14） | 不可达（张量分支，驱动仅标量材料） | 未检查 | 同上 |
| fmm_experimental:40 | 不可达（`use_experimental_fmm` 驱动不设置，仅 Lua 前端） | 未检查 | 检查 NULL、返回 20、不解引用 |

- 源码核实：closed 四处的下一行均为数值语句（无 `info` 检查）；`grep` 无 `solve_info|&info|iinfo`。
- **experimental:40 的基线失败类别未确定**：我未读完其循环结构，因此不声称 CRASH 或 SILENT（规则：不得编造）。

### 4.2 INJECTION_POINTS v2（另存，原文件未改）[实测]

- 新文件 `INJECTION_POINTS_v2.txt`：57 个数据行（与 S2R 一致），未处理（not-handled）13 行，**每个未处理点都有完成判据**（核对：0 缺失）。
- S2R 原文件 sha256 `665f3c73201cf4e443b1e7f4c08952f3c347f46ac2499ff479788d24e747a6a0`，本轮未改动（核对一致）。
- 纠正：S2R 报告曾写"57 行"，我在核对时用 `grep -vc '^#'` 得到 58，原因是头部注释行计数口径不同；Python 只数数据行，结果为 57，S2R 的说法正确。

### 4.3 S4.cpp:2369 的未闭合缺口 [源码]

- S2R 清单把 `S4/S4.cpp:2369`（FMMGetEpsilon 返回值接收）标为"handled"，但它的**注入路由从未建立**（S2R R2-C 的缺口）。v2 清单注释中已标注。本轮未补它的注入。

---

## 5. T4：缓存命中路径（jones:344）

### 5.1 结论：**能覆盖，需新增驱动模式**（已测量确认）[实测 + 源码]

缓存命中分支（`fmm_PolBasisJones.cpp:334–340`，分配在 `:344`）只在第二次求解时到达，因为：

1. 驱动的两次 `S4_Simulation_GetFieldPlane`（rc1、rc2）之间，层解被**复用**（`Simulation_GetLayerSolution` 第 1805 行的复用条件）。**单次运行中第二次不进入 PolBasis**（gdb 测量：EPS 1 次，GET 1 次，ADD 1 次）。
2. `S4_Simulation_SetFrequency` 同时销毁层模式、解与场缓存（`Simulation_InvalidateFieldCache`），因此**不能用它触发命中**。
3. `S4_Simulation_DestroyLayerModes(S, id)` 对**单层**只清该层模式，**不使场缓存失效**（源码 `S4.cpp:1364–1372`，函数体无 field_cache 操作）。
4. 层序由 `make_stack` 决定：`Above=0, Slab=1, Below=2`。**圆形夹杂的是 Slab（层 1）**。销毁层 0 无效（我最初的探测用错了索引，已修正并披露）。

### 5.2 测量确认的序列 [实测，gdb]

| 序列 | 事件 |
|---|---|
| 无干预 | GFP#1: COMPUTE → EPS → GET（未命中）→ ADD；GFP#2: **无事件**（复用） |
| 在 GFP#2 前销毁层 1 | GFP#2: COMPUTE → EPS → GET（**命中**，因 field_cache 保留）→ 进入 cache-hit 分支 |
| 分配尺寸序列（销毁层 1） | 第一次：192, 192, 10720, 1024；第二次：192, 192, **1296**（= 16·81，cache-hit `work`，nn = n² = 81，`fmm_PolBasisJones.cpp:104`） |

### 5.3 驱动改动（默认关闭）与历史保持 [实测]

- `testing/d003/src/driver_d003.cpp`：新增 11 行可选块，仅当 `S4FMM_TWICE=slab` 时调用 `S4_Simulation_DestroyLayerModes(S, 1)`。接口声明于 `S4/S4_internal.h:181`（驱动已包含该头文件，无需改动任何 S4 头文件）。**这是内部接口**：T4 证明的是"内部调用序列能到达 cache-hit"，**不是"用户经公开 API 可触达"**。
- **历史输出逐字节比对**：改动前后，10 个历史控制（fft/kottke/jones/nv/vl × pattern/flat，全部 rc=0）输出 sha256 **10/10 一致**。
- **二进制未逐字节一致**（新增一个分支，编译产物必然不同）。本报告只声称**输出**一致，不声称二进制一致。

### 5.4 运行器与判定器的两处修正 [实测]

- **判定器读错返回码（已修正）**：`classify` 原先只用 `rc1` 判定类别。cache-hit 注入发生在第二次调用（`rc2=20`，`rc1=0`），若用 rc1 会得 SILENT_SWALLOW（错误）。新增 `inj_call` 参数：默认 1（既有行为，自检输出逐行相同），`inj_call=2` 改用 rc2，非法值 fail-closed 为 INVALID。
- **运行器缺口（已修正）**：S2R 运行器的 `REQUEST_PREFIXES` 不含 `kottke_alloc:`，T1 行会被判为 unparseable。加入白名单（唯一的前缀改动）。S2R 26 行回归在两树上逐行复现（差异 0）。

### 5.5 T4 的两棵树结果与登记性质 [实测]

| 树 | 请求 | 结果 | 判定 | 事实 |
|---|---|---|---|---|
| BASE | `s4malloc` NTH=7 + `S4FMM_TWICE=slab` | rc 139 | **CRASH** | hit=1，1296 B |
| CUR | 同上 | rc 1 | **REPORTED_FAILURE** | rc1=0，rc2=20，hit=1 |

- 两轮（T5）一致。
- **登记性质（偏离 D-T4-1）**：T4 登记（`REGISTRY_T4.tsv`，时间戳 2026-10-11T05:28:47Z，sha256 `034295df326d6505…`）**写于探测之后**。两行均标 INFLUENCED。它不是盲预注册。


### 5.6 nv 与 vl 的缓存命中（探测性测量，登记于测量之后）[实测]

- **路由同样可用**：对 nv 与 vl 使用同样的 `S4FMM_TWICE=slab`，第二次求解出现 `GET（命中）` 与 **2592 字节**的缓存命中分配（`2·nn`，nn=81）。
- **源码核实**（内容读出）：`fmm_PolBasisNV.cpp:232` 与 `fmm_PolBasisVL.cpp:241` 为 `work = S4_malloc(sizeof(complex)*2*nn)`，其后 `:233` / `:242` 为 `if(NULL == work){ S4_free(ivalues); return 1; }`。注意：此前我在报告中写的 "nv:225、vl:234" 行号**错误**，已更正。
- **红绿（注入第 7 次 FMM 分配 = 2592 B）**：

| 树 | 模式 | rc | RC first | RC retry | 判定 |
|---|---|---|---|---|---|
| BASE | nv | 139 | — | — | **CRASH** |
| BASE | vl | 139 | — | — | **CRASH** |
| CUR | nv | 1 | 0 | 20 | **REPORTED_FAILURE** |
| CUR | vl | 1 | 0 | 20 | **REPORTED_FAILURE** |

- **性质（必须披露）**：这些是**探测性测量**。它们的登记 `REGISTRY_T4_NVVL.tsv`（4 行，时间戳 2026-10-11T05:35:05Z，sha256 `839cb9fcf1ce23110da7c3a39729cc5c7b61efea9716eacaafa3c233e67d81a3`）**写于测量之后**，每行标 INFLUENCED。它们**尚未纳入 T5 的两轮正式运行**。若用户要求正式化，需按 T5 方法在两树各跑两次。
- 原 `REGISTRY_T4.tsv`（sha256 `034295df326d6505…`）未改动。
- 依据记录：`T4_NVVL_PROBE_RECORD.txt`。
---

## 6. T5：红绿对照复跑与三方一致性

### 6.1 统一驱动下的正式运行 [实测]

- 唯一驱动：`seam4-*/bin-t4/driver-all-t4`（两树各一个，同一构建配置）。
- T5 视图 34 行 = 17 个 case × 2 树（已用 `(case, tree)` 键核对：每对恰一行）。
- 两棵树各运行两次：

| 树 | 运行 | 匹配登记 | 与另一轮逐行一致 | 类别分布 |
|---|---|---|---|---|
| BASE | 1、2 | 17/17、17/17 | 是（差异 0） | CRASH 15，SILENT_SWALLOW 2 |
| CUR | 1、2 | 17/17、17/17 | 是（差异 0） | REPORTED_FAILURE 17 |

### 6.2 历史 38 案矩阵 [实测]

| 树 | 不一致 | 与 S2R 对照 |
|---|---|---|
| BASE 37a82e8 | **0** | S2R 记录 0，一致 |
| CUR aa1c51d | **18** | S2R 记录 18，**同一组案例，且每案 (观察, 期望) 相同**（逐行比对） |

18 个当前树不一致项全部为 REPORTED_FAILURE，属于 S3 修复改变的行为（fft plan 5、fft exec 5、fft scratch 2、fft S4_malloc 2、solve_info 4），**无不可解释项**。

### 6.3 S2R 26 行矩阵回归 [实测]

- 扩展后的运行器在两树上复跑 S2R 登记（13 行/树）：BASE 匹配 11/13、CUR 匹配 12/13，**与 S2R 逐行事实一致（差异 0）**。

### 6.4 三方一致性 [实测 + 源码 + 清单]

三方：（A）装置结果；（B）INJECTION_POINTS v2 的已处理/未处理；（C）源码状态（`S4/` 树哈希在 `8d60dfb` 与 `aa1c51d` 相同 `85feec1151b3`，故 S2R 红结果可延续）。

| 类别 | 装置（A） | 清单（B） | 源码（C） | 一致？ |
|---|---|---|---|---|
| 已处理点：17 个 case（对应 15 个不同源码站点：`closed:40` 被 jones/nv/vl 三个 case 共用，其余 14 个站点各对应一个 case；含 T1 的 `kottke:78`、T4 的 `jones:344`；T1/T2/T4 测量） | CUR 全部 REPORTED_FAILURE | handled | 每点有 NULL 检查（T2 依据逐行读出） | **是** |
| 未处理点 13 个（清单） | 由 S2R R2-E 测得 CUR 为红（ComputeLayerModes 4、AddFieldToCache 1、info=NULL PolBasis 3）；closed 4 与 experimental 1 驱动不可达（仅静态） | not-handled | 无检查（S2R 与本轮核实） | **是** |

**关键限制**：T5 的"全绿"**只覆盖 17 个 case（对应 15 个源码站点）**。它**不能**用来证明未处理点已修复。本轮 T5 未覆盖任何未处理点。

**对不上并已解释的一处（检查本身的错误，非数据矛盾）**：早先的对照把基线行号与当前树行号混用，产生了虚假的 "NOT IN INVENTORY"。改用当前树行号（由内容读出）后，11 个 FMM 点全部在清单中找到（handled）。这是我的检查错误，已披露。

---

## 7. 偏离、违规与披露（逐条）

| 编号 | 类别 | 内容 | 处理 |
|---|---|---|---|
| D-T4-1 | 预注册顺序 | T4 探测在 T4 登记之前运行，登记写于探测之后 | 登记行标 INFLUENCED；本报告声明其非盲预注册 |
| D-T2-1 | 覆盖遗漏 | T2 登记遗漏 nv/vl 的 `closed:40` 调用行 | 覆盖检查发现；另存补充文件修正，原文件哈希保持 |
| D-T2-2 | 预注册性质 | T2 的部分预期在读过 S2R 结果后推导 | 逐行标注 INFLUENCED（9 行） |
| D-REG-1 | 登记后编辑 | S2R 登记在时间戳后有格式与依据文本修正（S2R 报告 D-3，本轮沿用披露） | 不再重复修改 |
| D-JUDGE-1 | 判定器缺陷 | `classify` 只读 rc1，注入在第二次调用时类别错误 | 新增 `inj_call`（默认不变）；自检输出逐行相同 |
| D-RUN-1 | 运行器缺陷 | `REQUEST_PREFIXES` 缺 `kottke_alloc:` | 加入白名单；S2R 26 行回归差异 0 |
| D-RUN-2 | 配置错误 | 运行器误用旧驱动 `driver-all`（不含 `S4FMM_TWICE`），T4 首轮 4 次均 INVALID | 改用 `bin-t4/driver-all-t4`；另验证 T2 行在两驱动上事实一致（差异 0） |
| D-DRV-1 | 驱动同名不同版本 | `driver-all` 与 `driver-all-t4` 同名前缀，易误用 | 本轮 T5 统一为 `driver-all-t4`；本条为后续风险 |
| D-CHK-1 | 检查错误 | 三方对照混用两棵树的行号，产生虚假 "NOT IN INVENTORY" | 改用当前树行号（内容读出）；已披露 |
| D-CHK-2 | 检查错误 | 注册表完整性检查用了错误的边车文件名，首次报告 "no recorded hash" | 用正确文件名重查，四份登记 UNCHANGED |
| D-CHK-3 | 检查错误 | 提交前冒烟检查的 `(case)` 键误判为重复，实为每树一行 | 改用 `(case, tree)` 键，数据无误 |
| D-CHK-4 | 估计值 | 三方记录中一处未核对的计数（"CRASH x15, SILENT x2"） | 用测量值替换；数值碰巧一致，但此前未核对 |
| D-EDIT-1 | 编辑失败 | `edit` 因未先 `read` 或缩进/CRLF 不匹配被拒绝（多次） | 重读后以精确字节重试；无错误写入 |
| D-GREP-1 | 工具误用 | `grep` 模式不覆盖 `.c` 源文件（`pattern.c`），误判定义缺失 | 改用精确文件定位 |
| D-LINE-1 | 行号误读 | 多次凭记忆使用行号（kottke:78/79/85/87，Jones:337/344，NV:225、VL:234 等；NV/VL 的实际缓存命中分配为 232 与 241） | 逐次以内容匹配重新读出；修正的行号已写入登记依据与本报告 |
| D-GDB-1 | 工具误用 | gdb 断点名错误（`Simulation_GetFieldCache` 不存在，正确为 `Simulation_GetCachedField`）；`call` 因无调试类型失败 | 改用正确符号与地址调用；断点数量核对为 3 |
| D-PROBE-1 | 探测索引错误 | 首次销毁层 0（Above）而非层 1（Slab） | 由源码层序修正；已披露 |
| D-STACK-1 | 栈误用 | 首次探测误用 `flat` 栈（不进入 FMM 非均匀分支） | 改为 `pattern`；已披露 |
| D-SRC-1 | 结构性偏离 | T4 需改驱动源码（任务允许，要求历史输出不变） | 历史输出 10/10 一致；二进制不一致已声明 |
| D-PATH-1 | 写入路径 | 本轮命令均在同一命令内 `export TMPDIR=<仓库内证据目录>` 并确认存在；`glob`/`grep` 工具的结果可能由框架落盘（工具行为，非本代理 shell） | 见 §9 `/tmp` 审计；发现 0 次仓库外写入（抽样） |

---

## 8. 已闭合与仍未闭合缺口

### 8.1 已闭合（有实测支撑）

| 缺口（S2R §9.3 / D-11 / D-12） | 状态 |
|---|---|
| fmm_kottke:78 `fft_alloc_complex` 无注入 | **已闭合**：家族 D，基线 CRASH、当前树 REPORTED_FAILURE，两轮一致 |
| 15 个 FMM 调用行仅观察性 | **已闭合（预注册）**：T2 登记（含 INFLUENCED 标注与一处覆盖遗漏修正） |
| closed/experimental 无登记行 | **已闭合（静态）**：`REGISTRY_T3_static.tsv`，无运行结果 |
| INJECTION_POINTS 缺完成判据 | **已闭合**：v2 每个未处理点有判据 |
| 缓存命中路径（jones:344、nv:232、vl:241）未测 | **已闭合（探测 + 登记）**：三者均已测，基线 CRASH、当前树 REPORTED_FAILURE；nv/vl 登记另存为 `REGISTRY_T4_NVVL.tsv`，标 INFLUENCED（见 §5.6） |

### 8.2 仍未闭合

| 缺口 | 原因 | 证据类型 |
|---|---|---|
| 缓存命中的 T4 路由仅在 jones 上做了 T5 正式运行（nv/vl 为探测性测量，见 §5.6） | 登记性质为 INFLUENCED；未纳入 T5 视图的两轮正式运行 | [实测]（探测）+ 待正式运行 |
| closed 130/133/138/235 运行验证 | 驱动不可达（Lr 与材料类型决定），需 Lua/Python 前端或新驱动 fixture | 仅静态 |
| fmm_experimental:40 基线失败类别 | 未读完其循环结构，不得编造 | [未验证] |
| PolBasis info=NULL 369/260/268 的本轮运行 | 本轮未重测，红结果引用 S2R R2-E | 引用 S2R [实测] |
| ComputeLayerModes 2267/2295/2408/2425、AddFieldToCache 3977 的本轮运行 | 同上，引用 S2R | 引用 S2R [实测] |
| `S4.cpp:2369` FMMGetEpsilon 返回值接收的注入路由 | S2R 未建立，本轮未补 | [未验证] |
| 非 FMM 的 S4.cpp 分配（43 处） | 范围外，列入待登记项 | 范围外 |
| T4 的公开 API 可达性 | 路由为内部接口 | 仅内部测量 |
| T2 预注册的独立性 | 读过 S2R 结果 | 已标注 INFLUENCED |
| `driver-all` 与 `driver-all-t4` 同名不同版本 | 运行器无法分辨驱动是否具备某功能 | 风险，未闭合 |

---

## 9. `/tmp` 审计、收尾核对与路径清单

### 9.1 `/tmp` 审计 [实测]

- 顶层快照：开始与结束各一次。开始 `e3b0c442…`（条目 0）；结束见下（在 9.4 记录）。
- **抽样 strace**（一次 `matrix_r2.py run` 的 `openat/creat/mkdir/rename/unlink`）：`/tmp` 事件 0，仓库外写入型 open 0。**这是抽样，不是整轮的穷尽审计**。
- `glob` 工具在本轮可能把结果落盘到框架 `/tmp/dsh-spill-…`，这是工具框架行为（非本代理 shell 命令），**已披露但无法由 shell 证伪**。

### 9.2 `S4/` 与越界路径 [实测]

- `S4/` 相对 `8d60dfb` 改动：**0**（git 树哈希相同）。
- 越界路径（提交范围仅限 `checkpoints/p05/` 与 `testing/d003/`）：**0**（见 9.4 的最终核对）。

### 9.3 提交

| 提交 | 范围 | 信息要点 |
|---|---|---|
| `f5cae24` | `testing/d003/`（5 文件，+138 / −22） | 家族 D、T4 驱动路由、inj_call、白名单；信息写明增删原因与 awaiting user review |
| *（本报告提交，见 9.4）* | `checkpoints/p05/P05_S2R2_HARNESS_CLOSEOUT.md`、`checkpoints/p05/S1_evidence_digest.txt` | 报告与摘要段 |

删除的 22 行为有意重构（`plan_c` → `plan_replace`，合法家族列表加入 `D`），已在提交信息中说明；家族 C 输出哈希前后一致。

### 9.4 路径清单

| 类别 | 路径 |
|---|---|
| 提交（testing） | `testing/d003/judge_d003.py`、`testing/d003/matrix_r2.py`、`testing/d003/seam/apply_seam_r2.py`、`testing/d003/src/driver_d003.cpp`、`testing/d003/src/inject_d003.cpp` |
| 提交（报告） | `checkpoints/p05/P05_S2R2_HARNESS_CLOSEOUT.md`、`checkpoints/p05/S1_evidence_digest.txt` |
| 证据（不提交） | `checkpoints/p05/evidence/p05-s2r2/`：nv/vl 登记 `REGISTRY_T4_NVVL.tsv`（+ `.sha256`、`_TIMESTAMP_UTC.txt`）、nv/vl 探测记录 `T4_NVVL_PROBE_RECORD.txt`；登记 `REGISTRY_T2_v2.tsv`、`REGISTRY_T2_v2_SUPPLEMENT.tsv`、`REGISTRY_T3_static.tsv`、`REGISTRY_T4.tsv`（及 `.sha256`、`_TIMESTAMP_UTC.txt`）；清单 `INJECTION_POINTS_v2.txt`；工作表 `T2_SOURCE_WORKSHEET_v3.txt`；T5 视图 `T5_VIEW_10col.tsv`；T5 运行 `t5run1-*`、`t5run2-*`；历史 `hist38-*`；S2R 回归 `reg4-s2r-*`；三方记录 `T5_THREE_WAY_CONSISTENCY.txt`；驱动 `seam4-*/bin-t4/driver-all-t4`；运行器 `adapt_registry_t2.py` |
| S2R 证据（引用，未改） | `checkpoints/p05/evidence/p05-s2r/`（`INJECTION_POINTS.txt` sha256 `665f3c73…`、`R2D_EXPECTATIONS.tsv` sha256 `ec8fafbc…`、`R2E-*`） |

### 9.5 收尾核对结果（见下一步）

以下核对在报告提交前执行：`git status` 干净、`S4/` 改动 0、越界路径 0、`/tmp` 结束快照、抽样 strace。结果记录在下方"收尾核对"小节。

---

## 10. 对 P05-S3 补充轮的输入

### 10.1 红点清单（当前树仍红，或未测）

| # | 点位 | 类别 | 基线 | 当前树 | 归属 / 性质 | 完成判据 |
|---|---|---|---|---|---|---|
| 1 | `fmm_kottke.cpp:78`（`fft_alloc_complex`） | FMM 分配（本轮新测） | CRASH | **REPORTED_FAILURE（已绿）** | 已绿，但 S3 声称已修；装置已覆盖 | 保持绿 |
| 2 | `PolBasisJones.cpp:369` | info=NULL（纳入 D003） | SILENT（S2R） | SILENT（S2R） | 用户决定纳入 | 传 `&info`、检查、失败返回 20、不安装缓存 |
| 3 | `PolBasisNV.cpp:260` | info=NULL | SILENT（S2R） | SILENT（S2R） | 同上 | 同上 |
| 4 | `PolBasisVL.cpp:268` | info=NULL | SILENT（S2R） | SILENT（S2R） | 同上 | 同上 |
| 5 | `closed.cpp:130/133/138/235` | info=NULL（驱动不可达） | 未检查（静态） | 未检查（静态） | 纳入，仅静态验证 | 同上；**无运行验证** |
| 6 | `S4.cpp:2267` | ComputeLayerModes 通用分配 | CRASH（S2R） | CRASH（S2R） | S3 补充轮接手 | NULL 返回 20，不安装模式，不解引用 `*layer_modes` |
| 7 | `S4.cpp:2295` | ComputeLayerModes | CRASH（S2R） | CRASH（S2R） | 同上 | NULL 返回 20，不解引用 `pB->q` |
| 8 | `S4.cpp:2408` | ComputeLayerModes | SILENT（S2R） | SILENT（S2R） | 同上 | NULL 返回 20，不以 NULL 工作区求解 |
| 9 | `S4.cpp:2425` | ComputeLayerModes | SILENT（S2R） | SILENT（S2R） | 同上 | 同上 |
| 10 | `S4.cpp:3977` | AddFieldToCache（jones 可达） | CRASH（S2R） | CRASH（S2R） | S3 补充轮接手 | NULL 不缓存，失败返回 PolBasis，PolBasis 返回非零并保留首个失败码 |
| 11 | `fmm_experimental.cpp:40` | S4_malloc（驱动不可达） | 未检查（静态） | 未检查（静态） | 纳入，仅静态 | 检查 NULL、返回 20、不解引用 |
| 12 | **`jones:344` cache-hit work** | 缓存命中分配（本轮新测） | CRASH | **REPORTED_FAILURE（已绿）** | 已绿，但 S3 声称已修 | 保持绿 |
| 13 | **`nv:232`、`vl:241` cache-hit work** | 缓存命中分配（2·nn，2592 B） | CRASH（探测） | REPORTED_FAILURE（探测） | 已测（探测），登记 INFLUENCED；待纳入正式两轮运行 | 保持绿（当前树） |
| 14 | `S4.cpp:2369` FMMGetEpsilon 返回接收 | 注入路由缺失 | — | — | 需建立注入 | 待定 |

**注意**：第 1 与第 12 项在本轮**已经是绿的**（REPORTED_FAILURE），它们不属于"红点"，但按任务要求（S3 声称已修的点若装置显示未修好则为最高优先级红点）——它们是**已确认修好**的点，不是红点。本报告未发现 S3 声称已修而装置显示未修好的点。

### 10.2 边界待用户裁决（不由本轮决定）

- info=NULL 的 PolBasis 369/260/268 与 closed 130/133/138/235：用户已决定纳入；closed 四处因驱动不可达，**其修复效果无法由装置验证**，只能静态核对。
- `fmm_experimental:40`：同上。
- `S4.cpp:2369`：注入路由是否纳入本轮之外，需用户决定。

### 10.3 对 S4 阶段的输入

- 驱动不可达的 5 个点（closed 4、experimental 1）的验证手段只能是静态走查，P05-S4 需决定是否接受静态验证，或另建驱动 fixture。
- `driver-all` / `driver-all-t4` 同名风险需在 S4 前消除（建议统一命名）。

---

## 11. 结论与状态

- **T1**：fmm_kottke:78 已覆盖：基线 CRASH，当前树 REPORTED_FAILURE（rc1=20），默认构建 24/24 字节一致，阳性对照仅 `fmm_kottke.o` 改变。
- **T2**：15 个调用行已预注册（含一处覆盖遗漏修正与 INFLUENCED 标注）；T2 实测与预期一致，两轮、两驱动一致。
- **T3**：驱动不可达 5 点仅静态登记；INJECTION_POINTS v2 每个未处理点有完成判据。
- **T4**：jones:344、nv:232、vl:241 缓存命中**均可覆盖**（驱动模式，默认关闭，历史输出 10/10 一致）；nv/vl 结果为探测性测量（见 §5.6）。
- **T5**：统一驱动下 17 案两树两次一致；历史 38 案与 S2R 26 行回归与 S2R 逐案一致；三方对照一致（已处理点全绿，未处理点仍红且不被 T5 覆盖）。

**本阶段未完成，等待用户审核。** P05-S1、P05-S2、P05-S3、P05-S4 均未被宣布完成。
