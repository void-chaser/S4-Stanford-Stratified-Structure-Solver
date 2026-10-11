# P05-S3 报告：最小修复（D003 错误传播）

> **状态：未完成，等待用户审核。** 本报告不宣布 P05-S1、P05-S2、P05-S3 中任何一个完成。
> 本阶段**不做验证**。下列"构建"与"兼容性检查"只是最低限度的编译与语法/锚点检查，不得称为验证。验证属于 P05-S4。
> 分支：`codex/p05-d003-fft-error-propagation`
> 基线：`5b72793051eb705f0e9b2e5398e1a5f0484da0cb`（5b72793 是当前 HEAD 的祖先，已核对）
> 开始 HEAD：`37a82e8be894ef27ba081cada1da71df2a24f4de`（工作区干净）
> 代码提交后 HEAD：`de52142`（本报告提交后见 §2）
> 证据目录：`checkpoints/p05/evidence/p05-s3/`（被 `.git/info/exclude` 忽略，**未提交**）

来源标注：**[实测]** 本轮运行或读取的原始输出；**[源码]** 只读阅读源码（已逐行回查）；**[推断]** 由实测加源码得出，未直接验证；**[未验证]** 本阶段无证据。

---

## 0. 编号对照（历史轮次 与 正式阶段）

P05 固定五阶段：P05-S1、P05-S2、P05-S3、P05-S4、P05-S5（见 `MEMORY` 中的阶段约束）。本阶段 = 正式阶段 **P05-S3（最小修复）**。

| 历史轮次（文件名） | 归属正式阶段 |
|---|---|
| S1 / S1B / S2 / S3 / S4 / S5 / S5b（`S1_*.md` … `S5B_*.md`） | P05-S1 的证据扩展 |
| 历史 `S3_OPEN_ITEMS_AND_SCOPE_FREEZE.md`（T11–T15） | **P05-S1 证据扩展**（与本阶段 P05-S3 **不是同一件事**） |
| P05-S2（测试装置，`P05_S2_TEST_HARNESS.md`） | P05-S2 |
| **本报告（P05-S3 最小修复）** | **P05-S3** |

- 文件名 `S3_OPEN_ITEMS_AND_SCOPE_FREEZE.md` 中的"S3"是历史轮次名，不改写。
- 本报告中未加前缀的"S3"指正式阶段，不指历史轮次。
- 本阶段内的额外工作（候选比对、缺口清单、静态走查、D2 锚点检查）只作为 P05-S3 的**子任务**，未引入 P05-S6 或其他新阶段。

---

## 1. 状态与范围

| 项 | 结果 |
|---|---|
| 任务 A 移植依据与差异清单 | **完成**（`evidence/p05-s3/PORT_PLAN.txt`，附录 `PORT_PLAN_ADDENDUM_candidate_S4cpp.txt`） |
| 任务 B FMM 最小修复（提交 1） | **完成**（代码层面；未验证） |
| 任务 C S4.cpp 调用点（提交 2） | **完成**（代码层面；未验证） |
| 任务 D 构建与最低限度自检 | **完成**（编译与锚点检查；**不是验证**） |
| 任务 E 报告与提交（提交 3） | 本报告；见 §2 |
| 阶段状态 | **未完成，等待用户审核** |

允许路径：`S4/fmm/`、`S4/S4.cpp`、`S4/S4_internal.h`（本阶段未改动）、`checkpoints/p05/`。`testing/d003/` 未改动。

---

## 2. 提交

| 序 | 哈希 | 信息 | 文件数 | 行数（+/-） |
|---|---|---|---|---|
| 1 | `b00b630` | fix(fmm): propagate fft plan/exec failure and check FMM allocations | 6 | +54 / −15 |
| 2 | `de52142` | fix(s4): check FMM epsilon return in Simulation_ComputeLayerModes | 1 | +18 / −12 |
| 3 | 见下 | 本报告与 digest 追加（仅 `checkpoints/p05/`） | — | — |

- 提交 2 依赖提交 1（提交 2 的信息中已注明）。提交 1 单独时，FMM 失败仍被调用方丢弃，这是任务书规定的分两提交的结果，已在提交信息中说明。
- 未 amend、未 rebase、未 push、未改动 master、origin 及其他分支、未合并。

提交 1 的文件：`S4/fmm/fmm_FFT.cpp`、`fmm_kottke.cpp`、`fmm_PolBasisJones.cpp`、`fmm_PolBasisNV.cpp`、`fmm_PolBasisVL.cpp`、`fmm_closed.cpp`。
提交 2 的文件：`S4/S4.cpp`（12 个 hunk，全部位于 `Simulation_ComputeLayerModes` 内）。

---

## 3. 任务 A：移植依据

### 3.1 候选与当前树的 sha256 对照 [实测]

候选目录只读（未构建、未运行、未写入）。被引用文件的 sha256 见 `evidence/p05-s3/candidate_sha256_start.txt`。

| 文件 | 与候选 A/B 的关系 | 判断 |
|---|---|---|
| `fft_iface.cpp`、`fft_iface.h` | 相同 | 不适用（候选未改）；其返回契约已存在，直接依赖 |
| `fmm_closed.cpp`、`fmm_experimental.cpp`、`fmm_common.cpp`、`fmm.h` | 相同 | 不适用（候选未改） |
| `fmm_FFT.cpp` | 不同 | **手工移植**错误传播（plan NULL、exec 返回值）；候选未覆盖 S4_malloc 与 solve_info |
| `fmm_kottke.cpp` | 不同 | **手工移植**同上 |
| `fmm_PolBasisJones/NV/VL.cpp` | 不同 | **手工移植**plan/exec 检查；失败时不进入 AddFieldToCache（A4） |
| `S4.cpp` | 不同（候选为 P04 之前版本） | **不整文件复制**；候选的 FMM 返回检查段有结构问题（`fmm_cleanup` 标签位于嵌套块内部，且回退了候选中缺失的特征值返回码路径）。仅按当前树手工实现（见 `PORT_PLAN_ADDENDUM_candidate_S4cpp.txt`） |
| `S4_internal.h`、`rcwa.cpp` | 不同（P04 前后版本差） | **不移植、不复制**。`rcwa.cpp:2180–2276`（P04 已修复）仅作参照实现 |

**候选的 P04 前版本不得整文件复制**（停止规则）：本阶段没有整文件复制任何候选文件。

### 3.2 候选新增的错误传播与 P04 前后版本差的区分 [实测]

- **候选新增（错误传播，已移植）**：`fmm_FFT.cpp` 与 `fmm_kottke.cpp` 的 plan 循环 NULL 检查、两处（kottke 两处）`fft_plan_exec` 返回值检查、`cleanup` 标签与 `return ret`。
- **P04 前后版本差（不属本任务，未触碰）**：候选 `S4.cpp` 与当前树在 `rcwa.cpp`、`Simulation_ComputeLayerModes` 特征值路径等处的差异。候选 `Simulation_ComputeLayerModes` 缺少当前树的 `return 20` 特征值失败处理，因此**不得覆盖**。

### 3.3 错误传播约定 [源码]

- FMM 函数返回非零表示失败。调用方（`Simulation_ComputeLayerModes`）统一映射为 **20**（现有码，三处既有 `return 20` 之一，表示层模式计算失败）。
- **未新增任何错误码。** FMM 内部返回的 `1` 或 `Pattern_GenerateFlowField` 的 `error` 不外泄为公共 API 码。
- 上层原样传递（[源码]，已核对）：`Simulation_ComputeLayerSolution`（`S4.cpp:1856–1859`、`1886–1889`）与 `Simulation_GetLayerSolution`（`1806–1809`）。

### 3.4 失败后的状态约定 [源码]（逐调用点，见 §5 走查表）

- `Simulation_ComputeLayerModes` 失败时：`Simulation_DiscardLayerModes(layer_modes)` 释放 `q`（唯一分配块）与结构体，并置 `*layer_modes = NULL`。`kp/phi/Epsilon2/Epsilon_inv` 是 `q` 块的内部指针，不单独释放。
- 调用方只在返回 0 时才执行 `L->modes = *layer_modes`（`S4.cpp:1811–1812`），因此失败时层不安装模式。
- FMM 失败时不继续使用 `Epsilon2/Epsilon_inv`（失败分支在 `SolveLayerEigensystem` 之前返回）。
- FMM 失败时不调用 `Simulation_AddFieldToCache`（PolBasis 的 `plan_done` 之后、`AddFieldToCache` 之前有 `ret` 检查）。
- 不释放缓存的 `P`（属于 `S`，既有 ownership）。

### 3.5 停止条件核对 [源码 + 实测]

| 条件 | 结果 |
|---|---|
| 需要新增错误码 | 否（复用 20） |
| 需要改 `S4/` 之外的文件 | 否 |
| 需要整文件复制候选 | 否 |
| 候选与当前 API 不兼容 | 否（`FMMGetEpsilon_*` 签名相同，`fft_iface` 相同） |
| 锚点行必须改动 | 否（LinearSolve 行逐字保留，见 §5.3） |
| 需要新增正式阶段 | 否 |
| 需要写 /tmp | **有一次违规尝试**，见 §8 偏离项 D-1（写入被只读文件系统拒绝，未落盘） |

---

## 4. 缺口清单与处理状态

### 4.1 与 S1 的 47 点对账 [实测]

S1 报告的静态统计为 47 点（`S1_BASELINE_AND_ENUMERATION.md` §2.7）。本阶段 grep 复核（修复前，HEAD `37a82e8`）得 44 点。差 3 点的原因已记入 `evidence/p05-s3/S1_47_RECONCILIATION.txt`：

| 类别 | S1 | grep 复核 | 差 | 原因 |
|---|---|---|---|---|
| fft_plan_dft_2d 无 NULL 检查 | 5 | 5 | 0 | — |
| fft_plan_exec 丢弃返回值 | 12 | 10 | −2 | S1 §2.2 计数口径偏高（FMM 目录实际 10 个调用点） |
| FMMGetEpsilon_* 丢弃返回值 | 11 | 10 | −1 | S1 偏高 1（S4.cpp 实际 10 个调用行） |
| FMM 目录 S4_malloc 无 NULL 检查 | 17 | 17 | 0 | — |
| solve_info 写入未读 | 2 | 2 | 0 | — |
| **合计** | **47** | **44** | **−3** | 以 grep 为准；S1 计数偏高，并非遗漏 |

另补充 S1 未计入的 7 个同类点（见 §4.3）。

### 4.2 47/44 点的处理状态 [实测]

| 类别 | 点数（grep） | 已修复 | 未修复 | 不适用/不修复的理由 |
|---|---|---|---|---|
| fft_plan_dft_2d NULL | 5 | **5** | 0 | — |
| fft_plan_exec 返回值 | 10 | **10** | 0 | — |
| FMMGetEpsilon_* 返回值 | 10 | **10**（经 `fmm_ret`，提交 2） | 0 | 2368 行（Experimental）驱动不可达，仍接收返回值以保持一致（改动结构相同） |
| FMM 目录 S4_malloc | 17 | **16** | **1** | `fmm_experimental.cpp:40`：驱动不可达（S2b 表，五分支计数 0），B1 不改 |
| solve_info | 2 | **2** | 0 | — |
| **合计** | **44** | **43** | **1** | — |

### 4.3 S1 未计入的同类点 [实测]

| 点 | 类别 | 处理 |
|---|---|---|
| `fmm_kottke.cpp:78` `fft_alloc_complex(6*ng2)` | 分配无 NULL 检查（不经 S4_malloc） | **已修复** |
| `S4.cpp:2267` `*layer_modes = malloc(...)` | ComputeLayerModes 开头分配 | 未修复（非 FMM 返回值；C2 决定） |
| `S4.cpp:2295` `pB->q = S4_malloc(...)` | 同上 | 未修复（同上） |
| `S4.cpp:2402` `rwork = S4_malloc(...)` | 特征分解（非 FMM） | 未修复（同上） |
| `S4.cpp:2419` `work = S4_malloc(...)` | 特征分解（非 FMM） | 未修复（同上） |
| `S4.cpp:3977` `Simulation_AddFieldToCache` 的 `S4_malloc` | 缓存安装，失败时直接解引用 | **未修复，需用户决定**（见 §9.1） |
| `LinearSolve(..., NULL, NULL)` info 为 NULL 的 7 处 | 零主元不上报 | 未修复（B1：记录；P04 之外既有行为） |

### 4.4 与 P05-S2 装置的关系 [源码]

- `S4_malloc` 的 `--wrap` 只能截获 FMM 调用方的 2 个运行时点（`fmm_FFT:74`、`81`），非 FMM 的 16 个运行时点不被截获（S2 报告 §4.1）。
- 本阶段的修复对 `S4_malloc` 的覆盖判断以源码为准；装置覆盖范围未扩展（不改 `testing/d003/`）。

---

## 5. 静态走查（B2）与关键行核对

### 5.1 走查表 [源码 + 静态走查]

完整逐条表：`evidence/p05-s3/B2_STATIC_WALKTHROUGH.txt`。摘要：

| 函数 | 失败点 | 释放内容 | 双重释放 | 结论 |
|---|---|---|---|---|
| `FMMGetEpsilon_FFT` | work NULL（:75）、discval NULL（:83）、plan NULL（:90）、exec（:188/:218）、solve_info（:210） | work；discval；plans[*]（NULL 安全） | 无 | OK |
| `FMMGetEpsilon_Kottke` | work（fft_alloc，:79）、discval（:88）、plan（:94）、exec（:268/:293）、solve_info（:285） | fft_free(work)；discval；plans | 无 | OK |
| `FMMGetEpsilon_PolBasisJones` | ivalues（:109）、work（:158）、vfield（:171）、plan（:250）、exec×4、缓存 work（:345） | 按失败点逐级释放；plan_done 处统一 | 无（成功出口在失败出口之后不可达） | OK |
| `FMMGetEpsilon_PolBasisNV` | ivalues（:60）、work（:113）、vfield（:126）、plan（:195）、exec（:211）、缓存 work（:233） | 同上 | 无 | OK |
| `FMMGetEpsilon_PolBasisVL` | ivalues（:59）、work（:118）、vfield（:131）、plan（:205）、exec（:220）、缓存 work（:242） | 同上 | 无 | OK |
| `FMMGetEpsilon_ClosedForm` | ivalues（:41） | 无其他资源 | 无 | OK |
| `Simulation_ComputeLayerModes` | FMM 返回非零（提交 2） | `Simulation_DiscardLayerModes(layer_modes)`；返回 20 | 无（调用方不再释放） | OK |

**走查方法的限制 [未验证]**：本表是人工静态走查，不是测试验证。它不能证明运行时无泄漏。

### 5.2 `goto` 与初始化的 C++ 约束 [实测]

- 为避免"goto 跨越带初始化的声明"，Jones/NV/VL 在 `plan_done` 之后不新增顶层带初始化声明，失败分支内联释放（不跨越 `const double ing2` 等）。
- 6 个 FMM 文件与 `S4.cpp` 的 `-fsyntax-only -Wall -Wextra` 均 rc=0、零错误（日志在 `evidence/p05-s3/logs/` 与 `tmp/`）。

### 5.3 LinearSolve 锚点 [实测]

- `fmm_FFT.cpp` 与 `fmm_kottke.cpp` 的 `RNP::LinearSolve<'N'>(n,n, Epsilon2,n, Epsilon_inv,n, &solve_info, NULL);` 与 HEAD 逐字节相同，各 1 处精确匹配。
- 检查放在该行之后（`if(0 != solve_info){ ret = 1; goto cleanup; }`）。
- `#include "fft_iface.h"` 锚点各 1 处精确匹配。
- 行号已漂移：FFT 204→209，kottke 279→284（因提交 1 插入行；`apply_seam.py` 按内容匹配，不依赖行号）。

---

## 6. 修复前后的代码行为变化（[源码]，未运行）

| 场景 | 修复前 | 修复后（代码层面） |
|---|---|---|
| `fft_plan_dft_2d` 返回 NULL | 继续执行，`fft_plan_exec(NULL)` 解引用 | 返回非零 → 20；不计算 |
| `fft_plan_exec` 返回非零 | 丢弃，继续写 `Epsilon2`、返回 0 | 返回非零 → 20；不安装，不缓存 |
| `solve_info != 0` | 无人读取，`Epsilon_inv` 为单位阵 | 返回非零 → 20 |
| `S4_malloc` 返回 NULL（FMM 内 16 点） | 解引用 NULL。S2 只实测了 `fmm_FFT.cpp:74,81` 两点导致崩溃（rc=139，[实测]）；其余 14 点的崩溃为 [源码] 推断 | 返回非零 → 20 |
| `Simulation_AddFieldToCache` 分配失败 | 解引用 NULL | **未修复**（§9.1） |

**注意**：以上是"修复后代码应有的行为"，**[源码] 推断**，未经运行验证。

---

## 7. 构建与兼容性检查（D）

> 以下全部是**编译与锚点检查**，不是验证。不运行矩阵、不分类、不对修复效果下结论。

### 7.1 构建 [实测]

导出对象：`git archive de52142` → `evidence/p05-s3/export-HEAD/`（899 个文件）。全部构建在证据目录内进行。

| 项 | rc | error | warning | 说明 |
|---|---|---|---|---|
| `make build/libS4.a` | 0 | 0 | 71 | 产物 776142 字节 |
| `python3 setup.py build_ext --inplace` | 0 | 0 | 3 | pyext 产物 742408 字节；3 条均在 `S4/main_python.c`（未修改） |

### 7.2 新增警告对照 [实测]

- `S4/S4.cpp` 标准 `-Wall`：修改前（`37a82e8`）与修改后（`de52142`）均 8 条；去行号后警告消息多重集**相同**。**新增 0 条**。（`-Wextra` 同样 8 条、多重集相同。）
- FMM 7 个文件：`-Wall -Wextra` 修改前后均 rc=0、0 条。**新增 0 条**。

### 7.3 `apply_seam.py` 仅应用检查 [实测]

| 步骤 | 结果 |
|---|---|
| `--check-only`（副本 `d2-seamed`） | rc=0；`fmm_FFT.cpp` site=1（hook 于第 209 行后），`fmm_kottke.cpp` site=2（第 284 行后）；两个锚点各唯一匹配 |
| 写入副本（`d2-seamed`，非仓库） | rc=0；仅两个文件与 `d2-pristine` 不同；仓库 `git status` 为空 |

### 7.4 宏未定义时预处理逐字节一致 [实测]

| 文件 | 修复后未插桩 vs 插桩（`g++ -E -P`，宏未定义） | 字节 |
|---|---|---|
| `fmm_FFT.cpp` | **逐字节一致** | 1310077 |
| `fmm_kottke.cpp` | **逐字节一致** | 1309267 |

阳性对照：宏定义（`-DS4_TEST_LINEARSOLVE_SEAM`）时两文件各出现 2 处 `S4_TEST_LINEARSOLVE_AFTER` 文本，宏未定义时 0 处。因此"一致"不是平凡结论。

---

## 8. 偏离项（逐条如实披露）

### D-1 违规：一次未设置 TMPDIR 的写入尝试 [实测]

- **事实**：在构建检查后的一次命令中，我编写了 `"$TMPDIR/t_$f.cpp"` 的重定向，但**该命令的 shell 未先 `export TMPDIR`**。`$TMPDIR` 展开为空，目标变为根目录 `/t_fmm_*.cpp`。
- **结果**：写入被只读文件系统拒绝（`Read-only file system`），**未产生任何文件**（已核对 `/` 下无 `t_fmm_*`）。
- **性质**：这违反了硬性约束"禁止写 /tmp 或仓库外任何路径（包括重定向）"。尝试本身即为违规，我如实列出。
- **后续处理**：此后每条命令都显式 `export TMPDIR=...`；重做的审计在仓库内 TMPDIR 下完成，结论一致（§5.1、`B2_STATIC_WALKTHROUGH.txt`）。
- **/tmp 快照**：结束快照与开始快照一致（sha256 `e3b0c442…`，条目数 0）。注意这只是 `ls -A /tmp` 的顶层条目快照，不能排除工具内部或其他进程在 /tmp 的写入。

### D-2 S1 计数与 grep 不一致（47 vs 44）[实测]

见 §4.1。S1 偏高 3 点（exec 2、FMMGetEpsilon 1），以 grep 为准。

### D-3 `fmm_experimental.cpp:40` 未修复 [实测 + 源码]

B1 要求"不改，除非可达"。它驱动不可达（S2b 表）。已按 B1 不修改。这意味着 FMM 目录 S4_malloc 为 16/17，不是 17/17。

### D-4 `FMMGetEpsilon_Experimental` 调用（S4.cpp:2368）的返回值接收 [源码]

该函数驱动不可达。为保持与其他 FMM 调用点结构一致，我也接收了其返回值（C1）。这超出"驱动可达路径"的最小改动，但是 1 行结构改动，不改变其行为（它的返回值目前恒为 0）。**如用户认为超出范围，可撤回此行。**

### D-5 修复阶段中改动的 `S4.cpp` 其他 FMM 调用点的结构改动 [源码]

为避免嵌套标签（候选 A 的 `fmm_cleanup`），我采用了统一的 `fmm_ret` 变量与一处失败检查，并把 PolBasis 调用加上 `0 == fmm_ret &&` 守卫（FFT 失败后不调用 PolBasis，保留首个失败码）。这是比 B1/C1 字面要求更多的结构改动（守卫条件），但不改变成功路径。

### D-6 `Simulation_AddFieldToCache` 未修复 [源码]

见 §9.1。这是 A4 的一个未闭合点。

### D-7 行号漂移 [实测]

S2 报告引用的 `fmm_FFT:204`、`kottke:279`、`S4.cpp:2374` 等行号因本阶段插入而漂移（新行号见 §5.3 与 `D4_P05_S4_INPUTS.txt`）。S2 报告本身未改写。

### D-8 候选 S4.cpp 的结构问题 [源码]

候选 A 的 S4.cpp 把 `fmm_cleanup` 标签放在嵌套块内部，且 `Simulation_ComputeLayerModes` 缺少当前树的特征值失败返回码路径（P04 回退风险）。本阶段**未复制**该段（见 `PORT_PLAN_ADDENDUM_candidate_S4cpp.txt`）。

### D-9 PortBasis 中既有的 `Pattern_GenerateFlowField` 错误路径未改 [源码]

- NV 的归一化在错误检查之前执行（既有行为，`fmm_PolBasisNV.cpp:139–160`）。
- 该路径的释放代码已正确（`if(NULL != ...)` 守卫）。本阶段未改它，因其不属于 D003 缺口。

### D-10 提交 1 的信息中的依赖说明 [源码]

提交 1 单独时，FMM 返回值仍被调用方丢弃。提交信息已说明这是两提交系列的第一步。

---

## 9. 仍待用户决定的事项

### 9.1 `Simulation_AddFieldToCache` 的 `S4_malloc` 无检查（S4.cpp:3977）

- 当前：分配失败时 `f->P = ...` 直接解引用 NULL。
- A4 要求失败不缓存；FMM 侧已保证失败时不调用它，但该函数自身的分配失败仍会崩溃。
- 修复需把函数改为返回 `int`（`S4.cpp` 内部 static 化不必要，但需要改声明 `S4.cpp:226` 与 3 个 PolBasis 调用方）。调用方位于 `S4/fmm/`，超出提交 2 的"仅 S4.cpp"范围。
- **请用户决定**：(a) 允许扩展到 FMM 调用方（一次性小改动）；或 (b) 接受此点作为未修复，记为 P05-S4 输入。

### 9.2 非 FMM 的 S4_malloc 点（ComputeLayerModes 的 2267/2295/2402/2419 与其他 S4.cpp 点）

- 不经 FMM，不在 A2 的 47 点内。覆盖需不同手段（S2 报告 §4.1）。
- **请用户决定**：是否纳入后续阶段，或接受为已知限制。

### 9.3 LinearSolve 的 info 为 NULL（7 处）

- B1 要求"记录，不改，除非 A2 判定为同类缺陷并写明理由"。A2 判定：不属于 47 点；零主元不上报是同类形式，但未经运行证明其在驱动中的可达性。
- **请用户决定**：是否列入 P05-S4 的可达性评估。

### 9.4 LinearSolve 注入 seam（S2 报告 §7）

- 本阶段**未**将 seam 写入 `S4/`。它仅在导出副本中应用（D2）。
- **请用户决定**：是否批准将 seam 引入 `S4/RNP` 或 FMM 调用点（S2 报告 §7 的待批准事项，仍然待决）。

---

## 10. P05-S4 输入（摘要；完整清单见 `evidence/p05-s3/D4_P05_S4_INPUTS.txt`）

1. **已修复（代码层面，未验证）**：FMM 的 plan NULL、exec 返回、solve_info、S4_malloc（16 点）、kottke fft_alloc；ComputeLayerModes 的 FMM 返回检查。
2. **未修复**：`fmm_experimental:40`；`S4.cpp:3977`；ComputeLayerModes 的通用分配 4 点；LinearSolve info=NULL 7 点；非 FMM 的 S4_malloc（驱动可达约 16 点）。
3. **装置扩展需求**：非 FMM 的 `S4_malloc` 需要源码级手段（需改 `S4/`，需批准）；`--wrap` 只覆盖 FMM 2 个运行时点。
4. **NB 覆盖**：运行时计数仅 NB=9；NB=1–8 可达性未测。
5. **faithful 近似的限制**：`info=1` 且 `Epsilon_inv` 置单位阵是人为模拟；"真实奇异时 b 为单位阵"只在一个矩阵上由探针确认；数值仅适用于 θ=30（S2 报告 A-2.4、A-3）。
6. **D003 类别 B 的修复效果**（中间量错误是否改变输出，类别 C）：未判定。需 P05-S4 用 scratch1 注入（NB=1）检查 `solve_info` 与 `Epsilon_inv`。
7. **运行确认项**：失败码传播链、失败后不安装、失败后不缓存部分 P、47 点路径在 NB=1–9 与五分支的行为。**均未运行。**

---

## 11. 路径清单

| 类别 | 路径 |
|---|---|
| 提交 1 | `S4/fmm/fmm_FFT.cpp`、`S4/fmm/fmm_kottke.cpp`、`S4/fmm/fmm_PolBasisJones.cpp`、`S4/fmm/fmm_PolBasisNV.cpp`、`S4/fmm/fmm_PolBasisVL.cpp`、`S4/fmm/fmm_closed.cpp` |
| 提交 2 | `S4/S4.cpp` |
| 本报告（提交 3） | `checkpoints/p05/P05_S3_MINIMAL_FIX.md`、`checkpoints/p05/S1_evidence_digest.txt`（追加 S3 段） |
| 证据（不提交） | `checkpoints/p05/evidence/p05-s3/`（`PORT_PLAN.txt`、`B2_STATIC_WALKTHROUGH.txt`、`C2_S4CPP_MALLOC_DECISION.txt`、`D_BUILD_AND_COMPAT_CHECK.txt`、`D4_P05_S4_INPUTS.txt`、`S1_47_RECONCILIATION.txt`、`candidate_sha256_start.txt`、`tmp_snapshot_start.txt`、`tmp_snapshot_end.txt`、`logs/`、`export-HEAD/`、`d2-pristine/`、`d2-seamed/`、`d2-pp/`、`tmp/`） |
| 候选（只读） | `/home/jackal/s4-fmm-20260930T132345Z`、`/home/jackal/s4-fmm-o1-20260930T183847Z` |

---

## 12. 等待用户审核

本阶段**未完成，等待用户审核**。P05-S1、P05-S2、P05-S3 均未被宣布完成。P05-S4（验证）尚未开始。
