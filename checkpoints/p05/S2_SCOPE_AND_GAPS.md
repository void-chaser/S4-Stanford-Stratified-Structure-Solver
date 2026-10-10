# P05 / S2：补测与范围裁决

> 基线：`5b72793051eb705f0e9b2e5398e1a5f0484da0cb`（Master）
> 门禁起点：`dc3be83`（工作区干净，相对基线仅改 `checkpoints/p05/`）
> 来源标注：**实测** = 本轮运行的原始输出；**代码阅读** = 只读源码；**文本比对** = 只读日志/源码的文本对照；**推断** = 由实测加其它事实得出，未直接验证；**未确定** = 证据不足，不下结论。
> 证据：`checkpoints/p05/evidence/s2/`（被 `.git/info/exclude` 忽略，**未提交**）；清单 `checkpoints/p05/evidence/EVIDENCE.sha256`（105 个文件，`sha256sum -c` 全部 OK）。

---

## 0. 结论摘要

- **NB1-REACHABLE（建议裁决：YES（显式异常）；非有限输出子判据：NOT-REPRODUCED）**。VL 基、NB=1 在默认公共 API、默认选项（ClosedForm 与 FFT 两条路径）下确定性失败，错误为 LAPACK 特征值分解 `info=2`。三个独立入口（ClosedForm Python、FFT Python、驱动）复现了同一失败；其中 ClosedForm Python 经 S1 与 S2 两次独立运行复现，驱动同时在 NB=1 与 NB=4 上复现。**没有任何主矩阵用例产生非有限数值。** 是否采用 YES，取决于主脑对 NB1-REACHABLE 的定义（见第 4 节）。
- **T7**：FFT 路径下 VL NB=1（θ=0°、30°）全部**异常**（info=2）；VL NB=9 全部**正常**（flux、amp 有限，真实布尔 True）。与 S1 的 ClosedForm 结论一致。
- **T8**：NB=4 全部**异常**（Python info=2；驱动 RC first=20）。O-1 的阈值因此修正为：**在已测点上，NB ≤ 4 失败，NB ≥ 5 成功**（已测点为 1,2,3,4,5,9；6–8 未测，阈值的精确位置不止于 4/5 之间的单一分界，需要更多点才能确认）。
- **T9**：历史驱动与现行副本的源码差异仅为 S1B 补丁。历史日志无法确定 NB 与频率；历史 `san/` 源码树与 Master 不同（未提交改动）。结论只能是"未确定"的部分已标注。
- **T10**：**是**。`S4_malloc` 调用的 `malloc` 经过 `malloc` 符号，`--wrap=malloc` 能计数。O0 映射给出 **18** 次 `S4_malloc → malloc_aligned → malloc`，全部 91 次 `malloc` 均已映射。**注意**：计数覆盖 ≠ 可注入（见 F9）。
- **T11**：`scratch1` 注入后的重试输出与无注入对照**逐位相同**（144/144，最大相对差 0）。**静默吞掉在该用例中未造成错误数值。**
- **D003 范围建议**：**纳入**"plan 失败导致 NULL 计划被执行而崩溃"（5 个分支，gdb 实测）。**暂不纳入**"静默吞掉 → 错误数值"，因为 T11 未能证明它。**不纳入** O-1。

---

## 1. 门禁与环境

- 门禁：`HEAD=dc3be83`，`git status --porcelain` 为空，`BASE` 为祖先，相对基线改动仅 `checkpoints/p05/`，产品源码无差异，`stash` 为空，`.git/info/exclude` 中 p05 行仍为 1 条（**本轮未新增任何 exclude 条目**）。
- 工具链：gcc/g++ 15.2.0，GNU Make 4.4.1，Python 3.14.4，`setarch`、`addr2line`、`nm`、`readelf`、`gdb` 可用。
- 所有构建与运行在同一后台作业内完成（`/tmp` 在工具调用之间会被清空）。证据在作业结束后复制到 `checkpoints/p05/evidence/s2/`。

### 1.1 构建产物（实测）

| 产物 | 配方 | 结果 | 证据 |
|---|---|---|---|
| 基线 `libS4.a`（-O3） | `make -j16 build/libS4.a …` | rc=0 | `s2/drv/build-lib.log` |
| 基线 Python 扩展 | `python3 setup.py build_ext --inplace` | rc=0 | `s2/py/build-pyext.log` |
| 驱动 `driver-s2`（-O1） | `g++ driver.cpp inject.cpp -Wl,--wrap=…` | rc=0，日志为空 | `s2/drv/build-driver-s2.log` |
| 基线库 `libS4.a`（-O0 -fno-inline -fno-omit-frame-pointer） | `make CFLAGS=… CXXFLAGS=…` | rc=0；`-O3` 出现 1 次（仅在 `RCWA.so` 的 Lua 扩展编译行），`-O0` 26 次 | `s2/t10o0/build-lib-O0.log` |

---

## 2. T7–T11 结果

### 2.1 T7：FFT 路径下的 VL NB=1（实测）

配置：`PolarizationDecomposition=True`，`PolarizationBasis='Default'`（VL），**`DiscretizedEpsilon=True`**，f=0.427，θ∈{0°,30°}。每个用例独立子进程（stderr 与用例一一对应）。ClosedForm 对照见 2.1 末尾。

| 场景 | 路径 | 结果 | info | flux 有限 | amp 有限 | 证据 | sha256 |
|---|---|---|---|---|---|---|---|
| fft-VL-nb1-th0 | VL NB=1 θ=0° f=0.427 | **异常** | 2 | — | — | `s2/t7/fft-VL-nb1-th0.json` | `97f91050…81c11a23` |
| fft-VL-nb1-th30 | VL NB=1 θ=30° f=0.427 | **异常** | 2 | — | — | `s2/t7/fft-VL-nb1-th30.json` | `c12f6fa2…30abc7eb` |
| fft-VL-nb9-th0 | VL NB=9 θ=0° f=0.427 | 正常 | — | True | True | `s2/t7/fft-VL-nb9-th0.json` | `c9d0d241…35897c30` |
| fft-VL-nb9-th30 | VL NB=9 θ=30° f=0.427 | 正常 | — | True | True | `s2/t7/fft-VL-nb9-th30.json` | `e0896c43…9f7a8c3d` |
| closed-VL-nb1-th0（对照） | VL NB=1 θ=0° | 异常 | 2 | — | — | `s2/t7/closed-VL-nb1-th0.json` | `3845b969…e582c644` |
| closed-VL-nb1-th30（对照） | VL NB=1 θ=30° | 异常 | 2 | — | — | `s2/t7/closed-VL-nb1-th30.json` | `23a280aa…ef170827` |
| closed-VL-nb9-th0（对照） | VL NB=9 θ=0° | 正常 | — | True | True | `s2/t7/closed-VL-nb9-th0.json` | `f154ecad…ee282385` |
| closed-VL-nb9-th30（对照） | VL NB=9 θ=30° | 正常 | — | True | True | `s2/t7/closed-VL-nb9-th30.json` | `9085b4af…b2d1a3f0` |

- 异常文本（全部相同）：`RuntimeError('GetPowerFlux: The layer eigensystem could not be solved; no solution was returned')`，stderr `Layer eigensystem returned info = 2`。
- 正常用例的 `flux_all_finite` 与 `amp_all_finite` 为真实布尔值 `True`。异常用例中这两个字段为 `None`，表示**没有可检查的输出**，**不等于**"非有限"。
- **S2 对 S1 的复现（实测）**：ClosedForm VL NB=1 的异常文本与 S1 的 `60-t6-results.json` 逐字相同；VL NB=9 的 `flux_top[1]` 为 `(-0.02046114055244115-1.3552527156068805e-20j)`，S1 与 S2 逐位相同。
- **关于 FFT 路径是否真的执行（推断）**：Python 扩展不链接注入器，因此 Python 运行没有 `WITNESS` 行，**无法直接观测 FFT plan 调用**。但驱动的 FFT 无偏振对照（`s2/t11/control-fft-ng1.log`）出现 17 次 `plan call`（前 5 次 `grid=1x1`，即 FFT 的 5 个 plan），证明 NB=1 的 FFT 路径确实会调用 `fft_plan_dft_2d`。Python FFT+VL NB=1 到达了特征值分解（`info=2`），而特征值分解在 FFT 之后执行（`S4.cpp:2399`，代码阅读），因此 FFT 步骤**被推断为已完成**。
- **结论：异常。** VL NB=1 的失败不依赖 FFT 路径：ClosedForm 与 FFT 两条路径在同一处失败。

### 2.2 T8：NB=4（实测）

| 场景 | 路径 | 结果 | 证据 | sha256 |
|---|---|---|---|---|
| closed-VL-nb4-th0 | Python，ClosedForm+PolBasisVL，θ=0° | **异常**，info=2 | `s2/t8/closed-VL-nb4-th0.json` | `83eab283…333fdc9c` |
| driver-vl-nb4 | 驱动 `FMM_MODE=vl S4FMM_NG=4` | **rc=1，RC first=20，RC retry=20** | `s2/t8/driver-vl-nb4.log` | 见清单 |

- 两条入口给出同一内部失败码（特征值失败 20/info=2）。
- **O-1 阈值修正**：S1B 的 T6b 测得 NB∈{1,2,3} 失败、NB∈{5,9} 成功，阈值区间为 [4,5)。本轮 NB=4 **失败**，因此阈值为：**NB ≤ 4 失败，NB ≥ 5 成功**（仅在已测点上成立：1,2,3,4 失败；5,9 成功）。

### 2.3 T9：历史驱动与现行副本的文本比对（文本比对）

**2.3.1 驱动源码（文本比对，已确认）**
- 历史原件 `/home/jackal/s4-fmm-accept/src/driver.cpp` 校验和 `1be57c35…`，与 S1 记录一致（只读）。
- 现行副本 = 历史原件 + S1B 补丁。`s2/drv/driver-s2-vs-history.diff` 与 `s2/drv/inject-s2-vs-history.diff` 记录了 S2 新增的两处（E/H 导出仅在 `S4FMM_DUMP` 设置时生效；注入器计数器仅在 `S4FMM_MALLOC_LOG` 设置时输出，**决策逻辑未改**）。
- **调用序列、NB 来源、VL 选项、频率、网格在两者之间完全相同。**（源码事实）
  - NB：环境变量 `S4FMM_NG` → `S4_Simulation_New`（`driver.cpp:51,107`）。
  - VL：`FMM_MODE=vl` 只设 `use_polarization_basis=1`，**不设** `use_discretized_epsilon`（`driver.cpp:56`），因此走 ClosedForm+PolBasis。
  - 频率固定 0.999（`driver.cpp:114`）；网格固定 `nu=4,nv=3`。
  - 调用序列：`New` → 选项 → 层 → `ExcitationPlanewave` → `SetFrequency` → `GetFieldPlane`（第一次）→ `GetFieldPlane`（retry）→ `Destroy`。

**2.3.2 历史日志（文本比对，已读全部 6 份 VL 日志）**

| 日志 | 注入 | `Layer eigensystem … info = 2` | `RC first` | `RC retry` | `retry output is finite` |
|---|---|---|---|---|---|
| `before-vl-plan-1` | plan | 无 | 无（日志在注入后截止） | 无 | — |
| `after-vl-plan-1` | plan | 有（plan call=2 之后） | 1 | 0 | FAILED |
| `before-vl-exec-1` | exec（边界） | 有（plan call=1 之后） | **0** | 0 | FAILED |
| `after-vl-exec-1` | exec（边界） | 有（plan call=2 之后） | 1 | 0 | FAILED |
| `before-vl-scratch-1` | scratch | 有（plan call=1 之后） | **0** | 0 | FAILED |
| `after-vl-scratch-1` | scratch | 有（plan call=2 之后） | 1 | 0 | FAILED |

- 历史日志**没有** `S4FMM DRIVER` 行（S1 已确认），因此**无法直接读出**历史负载的 NB、频率与模式。
- `grid=1x1` 的 plan 调用出现在 `info=2` 附近。`grid=1x1` 与 NB=1 的 FFT 网格相符，但**只是相符，不是证明**。
- `before-*` 中 `RC first 0` 与 `info = 2` 同时出现，`after-*` 中 `RC first 1`。两组的差别与"before/after"的代码版本相关，但**这两个版本的源码未在本轮比对**。

**2.3.3 历史 `san/` 源码树（文本比对，已确认）**
- `/home/jackal/s4-fmm-accept/san/` 含一份完整 S4 源码树，`git HEAD=b97f639`，**工作区有未提交改动**（5 个文件，927 行新增、136 行删除，包括 `S4/S4.cpp`、`S4/RNP/Eigensystems.cpp`、`S4/S4.h`、`S4/Interpolator.c`、`Makefile.common`）。
- `san/S4/S4.cpp` 的 sha256 `9e044e1c…` 与 Master 的 `c58a9c5d…` 不同。
- `san/S4/RNP/Eigensystems.cpp` 与 Master 同路径文件的 sha256 不同（`76db4bb7…` 对 `71817d22…`）。**这是特征值分解所在的文件。**
- **历史二进制链接的是哪一棵树，未确定。** `strings` 只显示源文件名（如 `Eigensystems.cpp`、`fmm_FFT.cpp`），不含完整路径。

**2.3.4 T9 结论（只读比对）**
- 驱动源码层面：**无差异**（仅 S1B 的 FieldCache 段）。
- 运行时输入层面：NB 与频率**未确定**（日志无 DRIVER 行）。
- 库层面：历史 `san/` 与 Master 的特征值相关源码**不同**，历史二进制链接的库**未确定**。
- 因此，"历史 VL 负载 RC=0 而现行副本 RC=20"的差异，**不能归因于驱动源码**；它可能来自库版本、NB 或频率。**本轮无法确定**。

### 2.4 T10：`S4_malloc` 是否经过 `malloc` 符号（代码阅读 + 实测）

**2.4.1 代码阅读（已读 `S4/S4.cpp:107–113` 与 `S4/numalloc.c:20–71`）**
- `S4_malloc`（`S4.cpp:107`）：先调用 `s4_fail_alloc_trip()`，然后 `ret = malloc_aligned(size, 16)`（`S4.cpp:111`）。
- `malloc_aligned`（`numalloc.c:20`）：宏分支。Windows → `_aligned_malloc`；ASan（`S4_HAVE_ASAN`）→ `posix_memalign`；**其它 → `pa = malloc((size+alignment-1)+sizeof(void*))`（`numalloc.c:68`）**。
- 本构建未定义 `S4_HAVE_ASAN`（`Makefile.common`、`setup.py`、`Makefile.Linux` 中无相关定义）。因此**普通构建走 `malloc`**。（代码阅读）

**2.4.2 运行证据（实测，O0 构建，映射两层返回地址）**

计数器：`s2/t10o0/` 的注入器副本在 `__wrap_malloc` 开头输出 `caller0`（直接调用者）与 `caller1`（其上一层）。O0 构建 `-O0 -fno-inline -fno-omit-frame-pointer`，经 `CFLAGS/CXXFLAGS` 覆盖确认（`-O0` 26 次，`-O3` 仅 Lua 扩展行）。驱动 `pattern`、`FMM_MODE=fft`、`S4FMM_NG=9`，`setarch -R` 固定地址。

- 计数：**91 次** `malloc`，映射为 **15** 个 (frame0, frame1) 对，计数求和 **91**（无遗漏）。
- 关键对（`s2/t10o0/caller-map.txt`，verbatim）：
  - `f0=malloc_aligned (numalloc.c:68) <- f1=_Z9S4_mallocm (S4.cpp:111)`：**`S4_malloc` 调用 `malloc_aligned`，`malloc_aligned` 调用 `malloc`。**
  - `f0=malloc_aligned (numalloc.c:68) <- f1=_ZL11rcwa_mallocm (rcwa.cpp:58)`：`rcwa_malloc` 的同一路径。
- 统计（按 mangled 名，`_Z9S4_mallocm` = `S4_malloc(unsigned long)`）：
  - **18** 次调用的 frame1 为 `S4_malloc`；
  - **2** 次调用的 frame1 为 `rcwa_malloc`；
  - 其余 71 次未归入这两类（见 2.4.4）。
- 修正说明：早先一次统计输出 `S4_malloc … 0`，原因是 grep 用了未 mangled 的名字，**不是数据为零**。本节数字已按 mangled 名修正。

**2.4.3 结论**
- **是**：`S4_malloc` 的分配经过 `malloc` 符号，`--wrap=malloc` 的计数器能捕获它（实测 18 次）。
- 这证明 F9 中"`--wrap=malloc` 对 `S4_malloc` 无效"的判断**不成立**（见第 3 节）。

**2.4.4 边界（未确定）**
- **未确定这 18 次 `S4_malloc` 调用中，有多少服务于 FMM 路径。** 这需要第三层回溯（谁调用了 `S4_malloc`）。本轮只记录了两层。
- 映射表中可见的 `S4_malloc` 调用者只到 `malloc_aligned` 这一层，未追溯到 `fmm_*.cpp`。
- 因此："`S4_malloc` 经过 malloc 符号"已证实；"FMM 的 17 个 `S4_malloc` 点都经过 malloc"**未证实**。

**2.4.5 O0 构建与 -O3 构建的关系**
- 早先的 `-O3` 映射（`s2/t10/`）仅记录 `caller0`、无行号（`??:?`）。它与 O0 映射**在地址上不可比**（编译选项不同）。权威证据以 O0 为准。

### 2.5 T11：输出数值对照（实测）

- 驱动副本输出 `S4FMM_DUMP`：在 `RC retry` 之后写出重试调用的 E、H 各 72 个元素（`n=6·4·3=72`）。
- 对象：`FMM_MODE=fft`，`S4FMM_NG=1`，NB=1 FFT 无偏振（与 T7 的 FFT+VL 不同，见 2.1）。
- `control-fft-ng1`：无注入，`HIT=0`，`RC first 0`，`RC retry 0`。
- `scratch1-fft-ng1`：`S4FMM_INJECT=scratch S4FMM_NTH=1`，`HIT=1`（`FFT execution scratch 16 B`），`RC first 0`，`RC retry 0`。

| 比较项 | 结果 |
|---|---|
| 元素总数（E+H） | 144 |
| 逐位相同 | **144 / 144** |
| 最大绝对差 | **0.0** |
| 最大相对差 | **0.0** |
| E 差异 | 0 / 72 |
| H 差异 | 0 / 72 |

- 证据：`s2/t11/control-fft-ng1.eh`、`s2/t11/scratch1-fft-ng1.eh`、`s2/t11/*.log`。两份 `.eh` 的 sha256 见清单。
- **结论：相同。** 在这个用例中，被吞掉的执行期失败**没有**使最终输出偏离无注入对照。
- **局限**：
  - dump 只写重试调用的输出，**没有保存第一次（失败）调用的输出**。因此"失败调用写入的部分结果是否错误"**未验证**。
  - 只覆盖 `scratch1`。`scratch2`（第二次执行期分配）**未做数值对照**。
  - 只覆盖 NB=1。NB=9 的执行期分配情形**未做数值对照**。

---

## 3. F9 与 F10 的更新

### F9（历史注入器用 `--wrap=malloc` 与 FFT 函数）
- **更新为：实测（已验证覆盖）。** `--wrap=malloc` 能包装 `S4_malloc` 的分配（18 次，2.4.2）。
- **S1 报告 F9 行的结论已过时**：S1 写"`--wrap=malloc` 对 `S4_malloc` 无效（4.4）"，该结论依据的是早期的 Linux `posix_memalign` 推断，已在 S1 第 4.4 节修正为"普通构建走 malloc"，但 F9 行未同步。**本报告为准。**
- **仍需区分两件事**：
  1. **计数覆盖**（`__wrap_malloc` 收到调用）：已实测，成立。
  2. **注入覆盖**（注入器在 FMM 的 `S4_malloc` 点制造失败）：**不成立**。注入器的决策只在 `arm` 窗口内（`fft_plan_dft_2d` 与 `fft_plan_exec` 内部，`inject.cpp:26–41`）。FMM 的 `S4_malloc` 点不在该窗口内，因此**当前注入器不会在这些点注入失败**。
- 原 `run-faults.sh` 的参数形式（`S4FMM_STAGE/PLAN_CALL/ALLOC/EXEC`）无效：注入器不读取它们（S1B 已确认）。

### F10（历史 VL 非有限）
- **更新为：部分确认，因果仍未确认，但排除了一种解释。**
- 本轮 T7（FFT 路径）与 ClosedForm 路径都显示 VL NB=1 **不依赖 FFT 即失败**（同一 info=2）。因此，历史"注入后重试非有限"若是 VL NB=1 的同一现象，它也不依赖 FFT 残留——**排除了"FFT 残留导致非有限"的解释**。（推断：排除性推理，非直接证明。）
- 历史负载的 NB 与频率仍**未确定**（2.3.2），因此无法把历史"非有限"与本轮的"显式异常"直接对应。
- 历史 `san/` 库源码与 Master 不同（2.3.3），历史"非有限"可能来自那份库，**未确定**。

---

## 4. NB1-REACHABLE 裁决建议

### 4.1 证据（均为实测，来源见第 2 节）

| 入口 | 配置 | 结果 | 来源 |
|---|---|---|---|
| Python，ClosedForm | VL NB=1，θ=0°、30°，f=0.427 | 异常，info=2 | S1 `60-t6-results.json`；S2 `s2/t7/closed-*` |
| Python，FFT（DiscretizedEpsilon=True） | VL NB=1，θ=0°、30°，f=0.427 | 异常，info=2 | S2 `s2/t7/fft-*` |
| Python，ClosedForm | VL NB=4 | 异常，info=2 | S2 `s2/t8/closed-VL-nb4-th0.json` |
| 驱动 `vl` | NB=1，无注入 | rc=1，RC first/retry=20 | S1B `s1b/t4/control-vl-ng1.log` |
| 驱动 `vl` | NB=4，无注入 | rc=1，RC first/retry=20 | S2 `s2/t8/driver-vl-nb4.log` |
| 主矩阵（全部 12 项）| VL/Jones/Normal × NB {1,9} × θ {0,30} | **无任何非有限数值**；VL NB=1 异常，其余有限 | S1 `60-t6-results.json` |

### 4.2 三类判定（按 spec 的字面类别）

- **YES（主矩阵出现非有限）**：**不成立。** 主矩阵与 S2 的所有用例中，没有任何非有限数值。
- **NOT-REPRODUCED-IN-THIS-MATRIX（主矩阵全部有限）**：**不成立。** VL NB=1 在主矩阵中**确定性失败**（5 次重复一致，S1）。
- **UNDETERMINED**：证据充分，但**指向的类别不在 spec 的四类之中**。

### 4.3 建议

- **建议裁决（需主脑确认定义）**：
  - 若 NB1-REACHABLE 定义为"VL NB=1 在默认公共 API 与默认选项下，是否会产生失败或非有限结果"：**YES（显式异常）**。依据：4 条独立入口、2 条路径、多次重复，全部一致地失败，无需任何注入。
  - 若定义为"VL NB=1 是否产生非有限输出"：**NOT-REPRODUCED**。依据：主矩阵与 S2 全部用例均无非有限数值。
- **推荐采用"YES（显式异常）+ 非有限子判据 NOT-REPRODUCED"的双字段记法**，避免把"显式异常"误读为"非有限"，也避免把"无非有限"误读为"无问题"。
- **O-1 不并入 D003**（主指示）。本轮证据支持该决定：失败是显式报告的（不是静默的），且不依赖注入。

---

## 5. D003 范围建议

| 类别 | 证据 | 建议 |
|---|---|---|
| **plan 失败导致 NULL 计划被执行而崩溃**（5 个分支） | S1B 实测崩溃（rc=139）；S2 gdb 五份栈显示 `fft_plan_exec(p=0x0)`，调用者为 FMMGetEpsilon_FFT/Kottke/PolBasisJones/NV/VL | **纳入 D003**。确定的缺陷，有 gdb 证据。 |
| **静默吞掉 → 错误数值**（execution-time scratch） | S1B 实测 RC=0；**S2 T11 显示重试输出与无注入对照逐位相同** | **暂不纳入**。本轮没有找到输出确实错误的用例。纳入前需先找到此类用例（候选：`scratch2`、NB=9 的执行期分配、或保存失败调用输出的对照）。 |
| **exec 边界**（模拟） | 注入器自注释为"BOUNDARY SIMULATION" | **不计入真实故障**。只可用于探测"调用者是否检查返回值"。 |
| **O-1**（VL NB=1 显式特征值失败） | T7、T8、驱动、Python 多路径复现；无注入；显式报告 | **不纳入 D003**（主指示）。 |
| **历史 VL "非有限"** | F10：因果未确定；历史负载与库未确定 | **不纳入**，待历史负载可重现后再判。 |

---

## 6. 偏离项

1. **驱动副本（S2）**：除 S1B 补丁外，新增两处改动——(a) `S4FMM_DUMP` 的 E/H 导出（仅在环境变量设置时生效）；(b) 注入器的 malloc 计数器（仅在 `S4FMM_MALLOC_LOG` 设置时输出，**注入决策未改**）。两处 diff 已存证。**这不属于 S1B 授权的"一处最小修改"，属于 S2 为 T10/T11 新增的观测代码。** 默认行为与 S1B 相同。
2. **O0 构建**：T10 需要 `-O0 -fno-inline -fno-omit-frame-pointer` 库。通过 `CFLAGS/CXXFLAGS` 覆盖实现（早先误用 `OPT=-O0`，未生效，已用日志证实并废弃该结果）。
3. **历史 `san/` 树**：本轮只读比对了其源码与 git 状态，**未执行任何历史二进制**（符合规定），也**未修改** `/home/jackal/s4-fmm-*`。
4. **证据打包**：`checkpoints/p05/evidence/archive/evidence-s1-s2.tar.gz`（见第 7 节），位于被忽略的目录内，未提交。
5. **无新增 exclude 条目**（`.git/info/exclude` 中 p05 行仍为 1 条）。
6. **一次误导性的中间结论已更正**：早先 grep 的 `S4_malloc … 0` 与"`-O0` 构建成功"两处，均因模式错误或变量名错误而不成立，已用 mangled 名统计与日志核对后修正。
7. **已提交的历史文件中的过时表述（未改写，仅在此标注）**：
   - `S1B_T4_T5_ADDENDUM.md` 第 159 行（b.3）："`S4_malloc` 是否经过 `--wrap=malloc` **未验证**"——**已被 S2 第 2.4 节推翻**（18 次运行证据）。
   - `S1B_T4_T5_ADDENDUM.md` 第 224 行（F9）："`S4_malloc` 是否经过 `--wrap` **未验证**"——**已被 S2 第 3 节更新**。
   - `S1_BASELINE_AND_ENUMERATION.md` 第 430 行（F9）："`--wrap=malloc` 对 `S4_malloc` 无效"——**与 S1 第 4.4 节的修正及 S2 的运行证据均不一致，已过时**。
   - 以上三处均按规定保留原文，以本报告为准。
7. **`/tmp` 反复清空**：本轮至少 5 次出现"调用之间 `/tmp` 被清空"，相关产物均已改为写入仓库证据目录。

---

## 7. 证据路径与校验

- 证据目录：`checkpoints/p05/evidence/s2/`（被忽略，未提交）。
- 清单：`checkpoints/p05/evidence/EVIDENCE.sha256`，**105 个文件**；`sha256sum -c` 结果 **105 OK、0 失败**（`checkpoints/p05/evidence/logs/s2-verify.txt`）。`s2/` 下 45 个文件。
- 归档：`checkpoints/p05/evidence/archive/evidence-s1-s2.tar.gz`
  - 大小：**71185 字节**
  - sha256：`2cacdc0a2d665a853268c899fe90d66d6d76e1b468279df8953aeddee1a5f75f`（完整值见下）
  - 成员：126 项（含目录条目）；不含归档自身；从归档解出后 **105/105 与清单一致**。
  - 未移到仓库外，未提交。是否外存由主脑决定。

完整归档 sha256：`2cacdc0a2d665a853268c899fe90d66d6d76e1b468279df8953aeddee1a5f75f`。

---

## 8. 需要主脑决定的事项

1. **NB1-REACHABLE 的定义与裁决。** 推荐：采用"YES（显式异常）+ 非有限子判据 NOT-REPRODUCED"的双字段记法，并明确定义"可达"指"默认公共 API 下确定性失败"。
2. **是否纳入"静默吞掉 → 错误数值"进 D003。** 推荐：暂不纳入。先找到输出确实错误的用例（候选：`scratch2`、NB=9 执行期分配、保存失败调用输出的对照）再决定。
3. **O-1 阈值的正式记录。** 推荐：记为"已测点 NB∈{1,2,3,4} 失败、NB∈{5,9} 成功"，并注明 NB=4 已在 S2 补测、NB=6–8 未测。不要写成单一分界。
4. **是否授权第三层回溯（T10 的 FMM 归属）。** 推荐：授权，以确定那 18 次 `S4_malloc` 调用中有多少属于 FMM；这是把"可包装"推进到"可用于注入设计"的前提。
5. **证据归档是否外存。** 推荐：外存一份 `evidence-s1-s2.tar.gz`（71185 字节，sha256 见第 7 节），仓库内保留未提交副本。

---

## 9. 更新后的 F1–F11 简表（仅 S2 新增的状态变化）

| 编号 | S2 后状态 | 依据 |
|---|---|---|
| F1 | 不变（实测） | — |
| F2 | 不变（推断） | — |
| F3 | 不变（实测） | — |
| F4 | 不变（实测，间接） | — |
| F5 | 不变（推断，17 处） | — |
| F6 | 不变（未验证） | — |
| F7 | 不变（推断） | — |
| F8 | 不变（未验证） | 禁止访问 |
| **F9** | **更新：计数覆盖已实测；注入覆盖不成立** | 2.4.2、3 |
| **F10** | **更新：排除 FFT 残留解释（推断）；因果仍未确定** | 2.1、3 |
| F11 | 不变（实测） | — |
