# P05 / S1 报告

> 状态：**部分完成（停在 T4/T5；T1、T2 静态、T3、T6 已完成）**
> 基线：`5b72793051eb705f0e9b2e5398e1a5f0484da0cb`（Master）
> 分支：`codex/p05-d003-fft-error-propagation`
> 来源标注：**[实测]** 本轮运行的原始输出；**[代码阅读]** 只读阅读源码得出，未经运行验证；**[历史日志]** 引用旧目录内容；**[未知]** 本阶段无法判定。

---

## 0. 结论摘要

- **NB1-REACHABLE: 未出现非有限输出；但 VL NB=1 在默认公共 API 下稳定失败（显式异常）**。这不符合 spec 的四类判定中的任何一类，**需要主脑裁决**（见第 7 节）。
  - 主矩阵（f=0.427）中 VL NB=1 的两个入射角（0°、30°）**均抛出 `RuntimeError`**，5 次重复一致。[实测]
  - 没有任何主矩阵用例产生非有限数值。[实测]
  - 失败是特征值分解返回 `info=2`（stderr 实测；具体打印位置 `rcwa.cpp:666` 或 `:883` 未经运行确认），并被映射为错误码 20 显式上报。不是 FFT 失败，也不是静默 NaN。[实测 + 代码阅读]
  - 失败在均匀空层（无图案、不经过 FMM 构造）上同样出现，因此与 FFT/FMM 构造无关。[实测]
- **基线缺陷复现：未运行（T5 未执行）。** 历史驱动在 Master 上编译失败，T4/T5 全部标记为**无效**。
  - 静默吞掉 **0** / 崩溃 **0** / 已报告失败（待核验） **0** / 无效 **全部**（T5 计划的用例数未运行）。
- **T5 停止原因**：`driver.cpp` 访问不完整类型 `struct FieldCache` 的成员（4 个编译错误，第 151、152 行）。[实测]
- **需要修复的调用点数量（静态统计，未经运行验证）**：`fft_plan_dft_2d` 无 NULL 检查 **5**；`fft_plan_exec` 丢弃返回值 **12**；`FMMGetEpsilon_*` 丢弃返回值 **11**；FMM 目录 `S4_malloc` 无 NULL 检查 **17**；`solve_info` 写入未读 **2**。合计 **47** 个点位（不含 `S4.cpp` 与 `Simulation_AddFieldToCache` 中未计入的分配点）。见第 2.7 节。
- **现有注入器能/不能覆盖的部分**：注入器本身与 Master API 兼容（独立编译通过，`nm` 符号一致，第 4.8 节）。它能覆盖 `fft_plan_dft_2d` 的 plan 失败与 `fft_plan_exec` 的 scratch/exec 边界（第 4.1 节）。**不能**覆盖 `LinearSolve` 的 `solve_info`（第 4.5 节）。对 `S4_malloc` 的覆盖性（`--wrap=malloc`）在普通构建中**理论可行**，但未经运行验证（第 4.4 节，已修正）。
- **F10（历史 VL 非有限）**：历史日志中 VL 注入后的重试与 `Layer eigensystem returned info = 2` 同时出现，**时序相关，因果未确认**（第 8 节）。
- **下一阶段（S2）建议输入**：(1) 决定 VL NB=1 的显式特征值失败是否属于 D003 范围；(2) 修复或替换历史驱动的 `FieldCache` 访问，且不得修改 `S4/`；(3) 在不依赖 `/tmp` 持久化的前提下运行 T4/T5；(4) 用运行证据确认 `S4_malloc` 是否经过 `malloc` 符号（这决定 `--wrap` 能否覆盖 FMM 分配）。

---

## 1. 环境与加载身份

### 1.1 运行环境 [实测]
证据：`checkpoints/p05/evidence/logs/00-env.txt`

| 项 | 值 |
|---|---|
| 内核 | Linux 7.0.0-38-generic x86_64 |
| gcc / g++ | 15.2.0 (Ubuntu 15.2.0-16ubuntu1) |
| make | GNU Make 4.4.1 |
| python3 | 3.14.4 |
| lua5.2 | 5.2.4（可用） |
| nproc | 16 |
| sanitizer / CFLAGS / CXXFLAGS 环境变量 | 无 |

### 1.2 构建与产物 [实测]
- 基线导出：`git archive 5b72793… | tar -x -C /tmp/S4-p05-baseline`，文件数 878，树哈希 `6a75e1f04bab6d1ba9f9c0548e6356c3fc002c2a45e13d923196e40985fe9472`。证据：`logs/baseline_manifest.txt`。
- 构建命令与 `testing/p04_run_all.sh` 第 61–62 行一致：
  - `make -j16 build/libS4.a build/S4 build/RCWA.so build/FunctionSampler2D.so` → **rc=0**（`logs/10-build-lib.log`）
  - `python3 setup.py build_ext --inplace` → **rc=0**（`logs/10-build-pyext.log`）
- 产物 sha256（`logs/11-artifacts.sha256`）：
  - `build/libS4.a` = `fb9ac3f5fd2c121619bb6cd464816f97a3085c8e4a2795a2b5037b370110ffba`
  - `build/S4` = `9b05692e7b340d3009e7411f1a5c220245ba85bdd0f7a2af77c3b1798a62e983`
  - `S4.cpython-314-x86_64-linux-gnu.so` = `6f3a8cacb422713e2a507791e51918789ec31caac706e874adc118fa5e6e93dc`

### 1.3 FFT 后端 [实测 + 代码阅读]
- `grep HAVE_LIBFFTW3` 在 `setup.py`、`Makefile.common`、`S4/config.h` 中**无匹配**（rc=1）。编译命令行中无 `-DHAVE_LIBFFTW3`（`logs/12-fftw-check.txt`）。
- 因此本次构建走 **kiss FFT**。`fft_plan_exec` 可以返回非零（`kiss_fftnd_checked`）。FFTW 构建下 `fft_plan_exec` 永远返回 0（`fft_iface.cpp:122–127`，代码阅读）。
- **第 3 节分支表仅对默认构建（kiss）有效。**

### 1.4 加载身份 [实测]
- T6 Python 进程中：`S4.__file__ = /tmp/S4-p05-baseline/S4.cpython-314-x86_64-linux-gnu.so`，`startswith baseline = True`（`logs/60-t6-main.log`）。

### 1.5 运行环境的限制 [实测]
- **`/tmp` 在每次工具调用之间被清空**（同一后台作业内可保留）。证据：多次探针，包括 `bgtest` 与 `ttl-probe`（作业内存活 150 秒，跨调用消失）。
- 因此所有构建、驱动编译、实验都必须在**同一个作业**内完成。证据全部落在仓库内被忽略的 `checkpoints/p05/evidence/`。
- 按主脑批准，在 `.git/info/exclude` 中加入 `checkpoints/p05/evidence/`（仅本地，未改 `.gitignore`）。

---

## 2. 调用点枚举表（T1） [代码阅读 + grep]

> 行号均对应 Master `5b72793`。"检查"列：是 = 检查返回值；否 = 完全忽略；部分 = 有检查但不完整。

### 2.1 `fft_plan_dft_2d`（计划创建）

| 文件:行 | 调用者 | 返回值检查 | 失败时清理 |
|---|---|---|---|
| `S4/rcwa.cpp:2209` | 场重建 | **是**（`if(NULL == plan[i]){ ret = 1; goto cleanup; }`） | 是（统一 cleanup，`rcwa.cpp:2266–2270`） |
| `S4/fmm/fmm_FFT.cpp:85` | `FMMGetEpsilon_FFT` | **否** | 否（`plans[i]` 直接用于 `fft_plan_exec`） |
| `S4/fmm/fmm_kottke.cpp:89` | `FMMGetEpsilon_Kottke` | **否** | 否 |
| `S4/fmm/fmm_PolBasisJones.cpp:245` | `FMMGetEpsilon_PolBasisJones` | **否** | 否 |
| `S4/fmm/fmm_PolBasisNV.cpp:190` | `FMMGetEpsilon_PolBasisNV` | **否** | 否 |
| `S4/fmm/fmm_PolBasisVL.cpp:200` | `FMMGetEpsilon_PolBasisVL` | **否** | 否 |

- 底层：`fft_plan_dft_2d` 在 kiss 下对 `kiss_fftnd_alloc` 失败与 `malloc` 失败均返回 NULL（`fft_iface.cpp:105–117`，代码阅读）。

### 2.2 `fft_plan_exec`（执行）— 13 个调用点（不含定义）

| 文件:行 | 返回值是否消费 |
|---|---|
| `S4/rcwa.cpp:2245` | **是**（`if(0 != fft_plan_exec(plan[i])){ ret = 1; goto cleanup; }`） |
| `S4/fmm/fmm_FFT.cpp:183` | **否** |
| `S4/fmm/fmm_FFT.cpp:212` | **否** |
| `S4/fmm/fmm_kottke.cpp:263` | **否** |
| `S4/fmm/fmm_kottke.cpp:287` | **否** |
| `S4/fmm/fmm_PolBasisJones.cpp:258` | **否** |
| `S4/fmm/fmm_PolBasisJones.cpp:277` | **否** |
| `S4/fmm/fmm_PolBasisJones.cpp:296` | **否** |
| `S4/fmm/fmm_PolBasisJones.cpp:315` | **否** |
| `S4/fmm/fmm_PolBasisVL.cpp:215` | **否** |
| `S4/fmm/fmm_PolBasisNV.cpp:206` | **否** |

- **12 个 FMM 侧调用点全部丢弃返回值**。[实测 grep + 代码阅读]
- 执行失败后，调用者继续使用 `Fto`（部分变换），并写入 `Epsilon2`/`Epsilon_inv`，然后调用 `Simulation_AddFieldToCache`。见 2.5 与第 8 节。

### 2.3 `fft_plan_destroy` / `fft_alloc_complex`

| 文件:行 | 说明 |
|---|---|
| `fmm_FFT.cpp:232–233`、`fmm_kottke.cpp:301–302` | 循环 `i=0..4` 销毁 5 个 plan。对 NULL 安全（`fft_iface.cpp:136`）。 |
| `fmm_PolBasisJones.cpp:326`、`fmm_PolBasisNV.cpp:217`、`fmm_PolBasisVL.cpp:226` | 销毁单个 plan。 |
| `fmm_kottke.cpp:77` | `fft_alloc_complex(6*ng2)` 的结果**未检查**。 |
| `rcwa.cpp` | 分配的 `from/to/plan` 按 `goto cleanup` 统一释放（代码阅读）。 |

### 2.4 `S4_malloc` 在 `S4/fmm/*.cpp`（17 个活跃调用点，不含注释） [grep + 逐行核对]

| 文件:行 | 用途 | NULL 检查 |
|---|---|---|
| `fmm_closed.cpp:40` | `ivalues` | 否 |
| `fmm_experimental.cpp:40` | `ivalues` | 否 |
| `fmm_FFT.cpp:74` | `work`（6·ng2） | 否 |
| `fmm_FFT.cpp:81` | `discval` | 否 |
| `fmm_kottke.cpp:85` | `discval` | 否 |
| `fmm_PolBasisJones.cpp:107` | `ivalues` | 否 |
| `fmm_PolBasisJones.cpp:153` | `work` | 否 |
| `fmm_PolBasisJones.cpp:167` | `vfield` | 否 |
| `fmm_PolBasisJones.cpp:337` | `work` | 否 |
| `fmm_PolBasisNV.cpp:58` | `ivalues` | 否 |
| `fmm_PolBasisNV.cpp:110` | `work` | 否 |
| `fmm_PolBasisNV.cpp:122` | `vfield` | 否 |
| `fmm_PolBasisNV.cpp:225` | `work` | 否 |
| `fmm_PolBasisVL.cpp:57` | `ivalues` | 否 |
| `fmm_PolBasisVL.cpp:115` | `work` | 否 |
| `fmm_PolBasisVL.cpp:127` | `vfield` | 否 |
| `fmm_PolBasisVL.cpp:234` | `work` | 否 |

- **F5 得到确认**：17 处全部没有 NULL 检查。[grep + 代码阅读]
- 另有两处 `malloc`（`fmm_PolBasisJones/NV/VL` 中的 `filename`，仅在 `vector_field_dump_filename_prefix` 非空时执行）也无检查，代码阅读。
- `S4/S4.cpp` 的 `Simulation_ComputeLayerModes` 中，`malloc`（2267）、`S4_malloc`（2295、2402、2419）同样无检查（代码阅读）。
- `Simulation_AddFieldToCache`（`S4.cpp:3971`）中的 `S4_malloc` 同样无检查，随后直接 `memcpy`（代码阅读）。

### 2.5 `FMMGetEpsilon_*` 调用点 — 11 个，全部丢弃返回值 [grep]

| 文件:行 | 调用 | 返回值 |
|---|---|---|
| `S4/S4.cpp:2368` | `FMMGetEpsilon_Experimental` | 丢弃 |
| `S4/S4.cpp:2372` | `FMMGetEpsilon_Kottke` | 丢弃 |
| `S4/S4.cpp:2374` | `FMMGetEpsilon_FFT` | 丢弃 |
| `S4/S4.cpp:2377` | `FMMGetEpsilon_PolBasisJones` | 丢弃 |
| `S4/S4.cpp:2379` | `FMMGetEpsilon_PolBasisNV` | 丢弃 |
| `S4/S4.cpp:2381` | `FMMGetEpsilon_PolBasisVL` | 丢弃 |
| `S4/S4.cpp:2386` | `FMMGetEpsilon_ClosedForm` | 丢弃 |
| `S4/S4.cpp:2389` | `FMMGetEpsilon_PolBasisJones` | 丢弃 |
| `S4/S4.cpp:2391` | `FMMGetEpsilon_PolBasisNV` | 丢弃 |
| `S4/S4.cpp:2393` | `FMMGetEpsilon_PolBasisVL` | 丢弃 |

- 调用者只有 `S4.cpp`（`grep -rn FMMGetEpsilon` 确认，其他文件只有定义与声明）。
- **F4 得到确认。** 2367–2397 行的所有调用均无赋值、无条件判断；随后 2399 行直接进入特征值分解。[代码阅读 S4.cpp:2365–2397]

### 2.6 `RNP::LinearSolve` 的 `solve_info`

| 文件:行 | info 参数 | 之后是否读取 |
|---|---|---|
| `fmm_FFT.cpp:204`（声明 203） | `&solve_info` | **否** |
| `fmm_kottke.cpp:279`（声明 278） | `&solve_info` | **否** |
| `fmm_closed.cpp:129,132,137,234` | `NULL` | — |
| `fmm_PolBasisJones.cpp:361`、`VL:260`、`NV:252` | `NULL` | — |
| `S4.cpp:1953` | `NULL` | — |
| `S4.cpp:2190` | `&dipole_solve_info` | 代码阅读：未核对（本阶段未展开） |

- **F6 得到确认**：`fmm_FFT.cpp` 与 `fmm_kottke.cpp` 的 `solve_info` 被写入，**之后从未被读取**（grep 确认）。[实测 grep]
- `fmm_PolBasisJones/VL/NV`、`fmm_closed` 则完全传 `NULL`，不记录求解状态。

### 2.7 修复范围汇总（静态估计，未经验证）

| 类别 | 数量 |
|---|---|
| `fft_plan_dft_2d` 无 NULL 检查 | 5（FMM 侧） |
| `fft_plan_exec` 丢弃返回值 | 12（FMM 侧） |
| `FMMGetEpsilon_*` 丢弃返回值 | 11（S4.cpp） |
| `S4_malloc` 无 NULL 检查（FMM 目录） | 17 |
| `solve_info` 写入但未读 | 2 |

> 注：spec 写 "约 20 处" 的 `S4_malloc`，本次核对为 17（fmm/*.cpp）。另外 `S4.cpp` 与 `Simulation_AddFieldToCache` 中还有若干无检查分配，未计入此表。

---

## 3. 分支表（T2）

> **本表只对默认构建（kiss FFT，无 `HAVE_LIBFFTW3`）有效。** [实测构建配置]
> **所有计数均为静态推导**（源码阅读）。动态计数需要驱动或 `--wrap`，而驱动不兼容（见第 5 节），因此**未做动态计数**。

驱动（`S4.cpp:2365–2397`）的决策顺序：

1. `use_experimental_fmm` → `Experimental`（**无 FFT**，`fmm_experimental.cpp` 无 FFT 调用）。
2. 否则若 `use_discretized_epsilon`：
   - 若 `use_subpixel_smoothing` → `Kottke`（**FFT 计划 5、执行 5**，静态）。
   - 否则 → `FFT`（计划 5、执行 5），且若 `use_polarization_basis`，**再**调用一个 PolBasis。
3. 否则（`use_discretized_epsilon = 0`，即 ClosedForm）→ `ClosedForm`（无 FFT），且若 `use_polarization_basis`，**再**调用一个 PolBasis。

| 选项组合 | 调用链 | FFT 计划数 / 执行次数（静态） | 备注 |
|---|---|---|---|
| `use_experimental_fmm=1` | `FMMGetEpsilon_Experimental` | 0 / 0 | 无 FFT |
| `discretized=1, subpixel=1` | `Kottke` | 5 / 5 | 计划 `i=0..4`；执行 `plans[4]` 一次 + `plans[0..3]` 各一次 |
| `discretized=1, subpixel=0, polarization_basis=0` | `FFT` | 5 / 5 | 同上 |
| `discretized=1, subpixel=0, pb=1, jones` | `FFT` **→** `PolBasisJones` | FFT 5/5 + Jones 1/4 | **两次调用，第二次覆盖第一次的 `Epsilon2`/`Epsilon_inv`**（见下） |
| `discretized=1, subpixel=0, pb=1, normal` | `FFT` **→** `PolBasisNV` | FFT 5/5 + NV 1/4 | 同上 |
| `discretized=1, subpixel=0, pb=1, default(VL)` | `FFT` **→** `PolBasisVL` | FFT 5/5 + VL 1/4 | 同上 |
| `discretized=0`（ClosedForm），pb=0 | `ClosedForm` | 0 / 0 | 无 FFT |
| `discretized=0`，pb=1，jones | `ClosedForm` **→** `PolBasisJones` | Jones 1/4 | 无 FFT 在 ClosedForm 中，但 Jones 本身用 FFT |
| `discretized=0`，pb=1，normal | `ClosedForm` **→** `PolBasisNV` | NV 1/4 | 同上 |
| `discretized=0`，pb=1，default(VL) | `ClosedForm` **→** `PolBasisVL` | VL 1/4 | 同上 |

- **注意：** `discretized=0` 时，PolBasis 内部仍调用 FFT（它们自己做 `fft_plan_dft_2d`）。因此 ClosedForm + PolBasis 组合也**有 FFT**，而不是无 FFT。上表已标注。
- **注意：** "polarization_basis=1" 时，`FFT`/`Kottke` 之后的 PolBasis 与前一步**顺序执行**（见 `S4.cpp:2374–2381`）。即 FFT 成功、PolBasis 失败（或反之）时，`Epsilon2`/`Epsilon_inv` 处于**半覆盖**状态。这是 D003 的关键场景（代码阅读 + 2.2 的丢弃返回值证明可以发生）。
- **注意：** `Kottke`、`FFT` 对 `Epsilon_inv` 使用 `LinearSolve`，其 `solve_info` 不被检查（2.6）。

### 3.1 半覆盖场景（代码阅读，**未运行验证**）
- 执行顺序（代码阅读，已核对 `fmm_FFT.cpp`）：`fft_plan_exec(plans[4])`（183 行）→ 写 `Epsilon2` 的 n×n 块（197 行）→ `LinearSolve` 求 `Epsilon_inv`（204 行）→ `fft_plan_exec(plans[w])`（212 行）→ 写 `Epsilon2` 其余块（227 行）→ 返回 0。
- 若 183 或 212 行的 `fft_plan_exec` 失败：变换输出是**部分结果**，但函数仍写入 `Epsilon2`/`Epsilon_inv` 并返回 0（`fmm_FFT.cpp:238`）。
- 随后 `S4.cpp:2377–2381` 进入 PolBasis（若启用），它再次覆盖 `Epsilon2`。
- 最终 `Simulation_ComputeLayerModes` 对这些矩阵做特征值分解，**不检查 FMMGetEpsilon 的返回值**（2.5）。
- **这是代码阅读推导。要确认"静默错误数值"，需要注入运行，本阶段未完成（第 6 节）。**

---

## 4. 历史注入器/驱动评估（T3）

证据：`checkpoints/p05/evidence/` 中的 `driver.log`、`logs/19-driver-src.sha256`、`logs/20-build-driver-baseline.log`、`logs/21-driver-syntax-diagnostic.log`；源文件来自 `/home/jackal/s4-fmm-accept/src/`（只读复制，未修改）。

- `driver.cpp`：`1be57c35f66e6822fdb21f2ea1d0c36f684d4b1860240cb5a4728841282f3b4d`
- `inject.cpp`：`13b2cbf5c23489c7203dcbdeb71e47103889a6fde7df6cccf6569c852da733da`

### 4.1 注入器注入的三类失败
[代码阅读 `inject.cpp` 头注释 + 实现]
- **scratch**：第 k 次 `fft_plan_exec` 内部的 16 字节分配失败（`__wrap_malloc` 在 `arm==2` 时对 `n==16` 计数）。注释称"真实分配点"（`kf_bfly_generic` 的临时缓冲）。
- **plan**：第 k 次 `fft_plan_dft_2d` 内部的 `malloc` 失败（`arm==1`）。注释称"准备阶段"的真实失败。
- **exec**：第 k 次 `fft_plan_exec` 直接返回 1，**不执行变换**。注释明确写为**边界模拟**，"no execution-time allocation exists there, so it is not a real failure"。
- **判定：** `plan` 与 `scratch` 是真实分配失败（在 kiss 下对应真实 malloc）；`exec` 是**边界模拟**，不是真实故障。

### 4.2 驱动调用的公共 API
- 驱动调用 `S4_Simulation_GetFieldPlane`（`driver.cpp:122`）。该函数在 Master 中存在（`S4.cpp:4167`）。[代码阅读 + 实测 grep]
- 调用链：`GetFieldPlane` → `Simulation_GetLayerSolution`（`S4.cpp:4284`）→ `Simulation_ComputeLayerModes`（`S4.cpp:1856/1886`，代码阅读）。
- **因此，若驱动可编译，它会经过 FMM 路径。** 但这是代码阅读结论，驱动不可编译，**未运行验证**。
- 1×1 网格走 `Simulation_GetField`（`S4.cpp:4248`），`nxy` 非 1×1 走 `GetFieldOnGrid`。驱动使用 `nu=4, nv=3`，即 grid 路径。[代码阅读]

### 4.3 驱动对"失败后重试"的断言（`driver.cpp:135–145`）
- `rc1 == 1`（失败码 1）
- 失败调用未写 E/H（`untouched()`）
- 哨兵未被破坏（`sentinels_ok()`）
- 同一对象的重试返回 0（`rc2 == 0`）
- 重试输出已写入且全部有限（`all_finite()`）
- 失败层不保留部分模式（`partial_modes == 0`）
- 不检查 `constructed_cache_entries`（仅打印 WITNESS，`driver.cpp:155`，**不是断言**）

### 4.4 注入器能否覆盖 F5 的 `S4_malloc` 点
- **代码阅读结论（已修正）：** `S4_malloc`（`S4.cpp:107`）→ `malloc_aligned`（`S4/numalloc.c:56`）。`malloc_aligned` 的分支由宏决定（`numalloc.c:38–71`）：
  - Windows：`_aligned_malloc`；
  - **ASan 构建（`S4_HAVE_ASAN`）：`posix_memalign`**（`numalloc.c:40–43`）；
  - **其他（包括本次的普通 Linux 构建）：`pa = malloc(...)`**（`numalloc.c:49` 起）。
- 因此在**普通构建**中，`S4_malloc` **经过 `malloc` 符号**，`-Wl,--wrap=malloc` **理论上可以拦截** `S4_malloc` 的分配。此前"在 Linux 上走 posix_memalign"的说法**是错误的**，已更正。
- 但是：注入器的 `__wrap_malloc` 只在 `arm` 状态下生效，且只对 `plan`（`arm==1`）与 `scratch`（`arm==2`，且 `n==16`）计数。它**没有**针对 FMM 的 `S4_malloc` 设计计数逻辑，因此 F5 的 17 个点**当前注入器不会有针对性地注入**。
- 这一点**未经运行验证**。要确认，需要在 T5 中运行（当前不可用，见第 6 节）。
- **建议（仅建议，未实现）：** 若要覆盖 17 个 `S4_malloc` 点，需要一个针对 FMM 路径的 armed 开关（类似 `S4FailAllocScopeGuard`，但覆盖 `Simulation_ComputeLayerModes` 的 FMM 分支），这必须修改 `S4/`，属于 S2 的范围。

### 4.5 注入器能否注入 `LinearSolve` 失败
- **不能。** 注入器只包装 `fft_plan_dft_2d` 与 `fft_plan_exec`，不包装 `RNP::LinearSolve`（`inject.cpp` 全文）。
- `solve_info` 的失败（2.6）无法由当前注入器触发。

### 4.6 F7：`S4_FAIL_ALLOC_AT` 的作用域 [代码阅读]
- `S4FailAllocScopeGuard` 仅在 `S4_Simulation_Clone` 中实例化（`S4.cpp:733`，全部引用见 `grep`）。
- `s4_fail_alloc_trip()` 仅在 armed 时返回非零（`S4.cpp:69–73`）。
- **FMM 路径不在 armed 作用域内，因此对 FMM 无效。F7 确认。**

### 4.7 驱动与 Master API 的兼容性 [实测]
- **驱动编译失败**（`logs/20-build-driver-baseline.log`，rc=1）。
- 错误（`logs/21-driver-syntax-diagnostic.log`，共 4 个，`-fsyntax-only` 复现）：
  - `driver.cpp:151`：`invalid use of incomplete type 'struct FieldCache'`（访问 `f->next`）
  - `driver.cpp:152`：`invalid use of incomplete type 'struct FieldCache'`（访问 `f->layer`，`f->n`，3 处）
- 原因：`S4_internal.h:95` 仅前向声明 `struct FieldCache;`，完整定义在 `S4.cpp:203`（不可见）。[代码阅读]
- **历史核对（已更正）**：`git log -S 'struct FieldCache{'` 显示该定义引入于 `c0a8e69`，当时它已位于 `S4.cpp:76`，**不在头文件中**。因此"驱动曾经能看到 FieldCache、后来被移走"的说法**没有证据支持**，已撤回。驱动为何与当前 API 不兼容，**未核实**；本阶段也未确定驱动在哪个历史版本上可编译。
- **按 spec，未修改驱动以适配。** 这是停止条件，已记录。

### 4.8 注入器与 Master 的兼容性 [实测]
- `inject.cpp` 单独 `g++ -c` 编译通过（rc=0，`-I S4 -I S4/fmm`），`nm` 显示其引用的 `__real__Z13fft_plan_execP12tag_fft_plan` 与 `__real__Z15fft_plan_dft_2dPiPSt7complexIdES2_i` 与 Master `fft_iface.cpp` 定义的 mangled 名称**一致**（`nm` 的 `T` 符号）。
- **结论：注入器与 Master 符号层面兼容，只有驱动不兼容。**

### 4.9 历史 `run-faults.sh` 的判定口径（供 S2 参考）
- strict 模式：`fault` 用例要求 `rc1=1`、`rc2=0`、`hit` 精确等于声明值、驱动 PASS、完成标记存在、无 sanitizer 行。
- baseline 模式：`fault` 用例要求 `hit≥1` 且（`rc=0 且 rc1=0`）或崩溃，才判为"缺陷复现"。
- 这些口径**未修改**（spec 禁止放宽）。

---

## 5. 控制运行结果（T4） — **未运行**

- **原因：** 驱动编译失败（第 4.7 节）。
- 按 spec 第 5 节："若某分支控制失败，该分支的 T5 全部标无效"；此处更上游的是"驱动不兼容"，T4 的 10 个控制用例**均未运行**，无日志、无退出码。
- 证据：`rc.txt` 中只有 `build_driver_baseline rc=1`，**没有** `control-*` 记录。
- **未完成项。**

| 分支 | NG=9 | NG=1 |
|---|---|---|
| fft | 未运行 | 未运行 |
| kottke | 未运行 | 未运行 |
| jones | 未运行 | 未运行 |
| nv | 未运行 | 未运行 |
| vl | 未运行 | 未运行 |

---

## 6. 基线故障复现结果（T5） — **未运行**

- **原因：** 同第 5 节。驱动不可编译，无法在基线上注入。
- 所有 T5 用例（plan / exec / scratch / PolBasis 第二次调用）均**无效：驱动不可用**。
- **因此：本报告不包含任何"静默吞掉 / 崩溃 / 已报告失败"的判定。** 第 3.1 节的半覆盖场景仍是**代码阅读推导**，不得作为缺陷证据。

| 计数 | 数量 |
|---|---|
| 静默吞掉 | **0**（未运行） |
| 崩溃 | **0**（未运行） |
| 已报告失败（待核验） | **0**（未运行） |
| 无效 | 全部 T5 用例（驱动不可用） |

---

## 7. VL NB1 核对（T6） [实测]

### 7.1 方法
- 公共 Python API，基线构建（`S4.__file__` 已确认，第 1.4 节）。
- 每个用例**新建对象**（`S4.New`），选项在构造后由 `SetOptions` 一次性设置，**不在构造后修改选项**（避开 D004）。
- 几何：周期 1×1，圆半径 0.25，eps=4 圆在 eps=1 背景，厚度 0.5，垂直/斜入射。
- API 注意（已对照 `S4/main_python.c`）：
  - `SetExcitationPlanewave` 角度为**度数**（`main_python.c` 内部乘 π/180）。
  - `SetRegionCircle` 为位置参数 `(layer, material, center, radius)`。
  - `AddLayer` 关键字为 `S4_Material`。
- **选项组合（已更正）**：只设置 `PolarizationDecomposition=True` 与 `PolarizationBasis`（VL 为 `'Default'`），**不设置 `DiscretizedEpsilon`**。默认值为 0（`S4.cpp:337`），因此图案层走 **ClosedForm + PolBasisVL** 路径（`S4.cpp:2385–2395`）。这与 spec 规定的选项一致。
- 脚本：`checkpoints/p05/evidence/t6_vl_nb1.py`、`t6_diag_layer.py`、`t6_repeat.py`。
- **历史修正（为避免误读数字）**：本阶段的 T6 数值经过三次修正。
  1. 初版 API 调用与 Master 不符（角度、关键字），已修正（`main_python.c` 核对）。
  2. 初版误设 `DiscretizedEpsilon=True`，使图案层走 FFT 路径，**偏离 spec**。已删除，所有 T6 脚本统一为 ClosedForm 路径。
  3. 初版 `GetAmplitudes` 检查抛 `TypeError`（把内层元组当复数），导致 `amp_all_finite` 为 `None`。已修正为两层展开，现为布尔值。
- 因此，**本报告采用的数值仅来自第三轮（ClosedForm + 修正后的 `GetAmplitudes` 检查）的运行**。更早的 FFT 路径数值已从报告中全部移除。

### 7.2 主矩阵（verdict-bearing）：f = 0.427，共 12 项 [实测]

| 基 | NumBasis | θ | 状态 | flux_top（前向，后向） | flux_bot（前向，后向） | 有限 |
|---|---|---|---|---|---|---|
| VL (Default) | 1 | 0° | **EXCEPTION** | — | — | — |
| VL (Default) | 1 | 30° | **EXCEPTION** | — | — | — |
| VL (Default) | 9 | 0° | ok | (1+1.3552527156068805e-20j), (-0.02046114055244115-1.3552527156068805e-20j) | (0.979538859447551+0j), 0j | 是（amp 长度 [18, 18]） |
| VL (Default) | 9 | 30° | ok | (0.8660254037844386+0j), (-0.029910902101953983+0j) | (0.8349893023929059+0j), 0j | 是（amp 长度 [18, 18]） |
| Jones | 1 | 0° | ok | (1-8.673617379884035e-19j), (-0.028643644391032563+8.673617379884035e-19j) | (0.9713563556089675+0j), 0j | 是（amp 长度 [2, 2]） |
| Jones | 1 | 30° | ok | (0.8660254037844386+0j), (-0.03817366931099224+0j) | (0.8278517344734458+0j), 0j | 是（amp 长度 [2, 2]） |
| Jones | 9 | 0° | ok | (1+0j), (-0.014611716741595416+0j) | (0.9858502908561179+0j), 0j | 是（amp 长度 [18, 18]） |
| Jones | 9 | 30° | ok | (0.8660254037844386-1.734723475976807e-18j), (-0.020361779293793975+1.734723475976807e-18j) | (0.8452586817660184+0j), 0j | 是（amp 长度 [18, 18]） |
| Normal | 1 | 0° | ok | (1+0j), (-0.02559004066097157+0j) | (0.9744099593390286+0j), 0j | 是（amp 长度 [2, 2]） |
| Normal | 1 | 30° | ok | (0.8660254037844386-1.734723475976807e-18j), (-0.03480707823540623+1.734723475976807e-18j) | (0.8312183255490323+0j), 0j | 是（amp 长度 [2, 2]） |
| Normal | 9 | 0° | ok | (1+0j), (-0.017577025169325446+0j) | (0.9824229748305989+0j), 0j | 是（amp 长度 [18, 18]） |
| Normal | 9 | 30° | ok | (0.8660254037844386+1.734723475976807e-18j), (-0.025796034033115176-1.734723475976807e-18j) | (0.8381469251633369+0j), 0j | 是（amp 长度 [18, 18]） |

- 来源：`logs/60-t6-results.json`，`logs/60-t6-main.log`。
- 物理参照：正入射前向通量 = 1，斜入射 30° 时 = cos30° = 0.8660（与解析一致）。这只作为数值健全性参照，**不作为判据**。

### 7.3 异常的确切文本与来源
- Python [实测]：`RuntimeError('GetPowerFlux: The layer eigensystem could not be solved; no solution was returned')`
- C 层 stderr [实测]：`Layer eigensystem returned info = 2`。
- 打印位置有两处（`S4/rcwa.cpp:666` 与 `:883`），分别属于两个函数：
  - `rcwa.cpp:666`：`SolveLayerEigensystem_real`（532 行起），调用 `RNP::Eigensystem_real`（659 行）。
  - `rcwa.cpp:883`：`SolveLayerEigensystem`（731 行起），调用 `RNP::Eigensystem`（876 行，复数）。
- **哪一处实际打印，本次未用调试器确认。** 代码阅读推导：
  - `n_G` 的取值：二维晶格走 `G_select`（`S4.cpp:365`）。`G_select` 在 `*NG == 1` 时直接返回 `G=(0,0)`（`gsel.c:167–173`），因此 **NumBasis=1 对应 n_G=1**（代码阅读，已核对）。
  - `isreal` 初值 `(n > 10)`（`rcwa.cpp:749`）。`n=1` 时为 false，**应走复数分支**，即 `rcwa.cpp:883`（`SolveLayerEigensystem`，876 行的 `RNP::Eigensystem`）。
  - **此推导未经运行验证**（未用调试器或打印 `n` 确认）。若主脑需要确定性证据，可在 S2 的运行中加入 `n_G` 打印。
- Python 把错误码 20 映射为上述文本（`main_python.c:137`，`/* 20 */`）。错误码 20 由 `Simulation_ComputeLayerModes` 返回（`S4.cpp:2362、2416、2432`）。[代码阅读]

### 7.4 分层溯源 [实测]（`logs/61-t6-diag-layer.log`）

| 基 | NumBasis | Air_above（均匀） | Slab（图案） | Air_below（均匀） |
|---|---|---|---|---|
| VL | 1 | **EXC** info=2 | **EXC** info=2 | **EXC** info=2 |
| VL | 9 | ok | ok | ok |
| Jones | 1 | ok | ok | ok |
| Jones | 9 | ok | ok | ok |
| Normal | 1 | ok | ok | ok |
| Normal | 9 | ok | ok | ok |

- **失败不是只发生在图案层。** 均匀空层（`Air_above`、`Air_below`，无图案）也失败。
- 均匀层不经过 FMM 的 `FMMGetEpsilon_*`，因此 **VL NB=1 的失败与 FFT/FMM 构造无关**。[实测 + 代码阅读 `S4.cpp:2332–2364`]
- 异常发生在 `Simulation_ComputeLayerModes` 的特征值分解环节，而不是 FFT 环节。

### 7.5 重复性 [实测]（`logs/62-t6-repeat.log`）
- VL NB=1，f=0.427，θ=0：5 次独立新建对象，**5 次均为相同异常**（`distinct outcome kinds: ['EXC']`）。
- VL NB=9，同条件：5 次均 OK，且数值**逐位相同**（`(−0.02046114055244115−1.36e−20j)`）。
- 结论：失败是**确定性**的，不是偶发。

### 7.6 近截止对照（f = 0.999，单独成组，不与主矩阵混合） [实测]
- VL NB=1：EXCEPTION（同上异常）。
- VL NB=9：ok，有限。
- Jones/Normal NB=1、9：ok，有限。
- **近截止对照不能单独解释 VL NB=1 的失败：** 主矩阵 f=0.427（非截止）同样失败，所以失败与 f=0.999 的截止接近性无关。
- 与旧日志（F10）的关系：旧日志报告的是"非有限"，本次复现的是"显式异常"。两者**不是同一现象**，除非旧环境下异常被吞掉并产生 NaN（**未知，未验证**）。

### 7.7 NB1-REACHABLE 判定 — **需要主脑裁决**

按 spec 的判定：

| spec 类别 | 本次结果 |
|---|---|
| `YES`（主矩阵出现非有限） | **否**：主矩阵没有任何非有限数值。 |
| `NOT-REPRODUCED-IN-THIS-MATRIX`（主矩阵全部有限） | **否**：VL NB=1 在主矩阵中**失败**（异常），不是"全部有限"。 |
| `ONLY-NEAR-CUTOFF` | **否**：主矩阵 f=0.427 即复现失败。 |
| `UNDETERMINED` | 部分适用：类别本身不覆盖"显式异常"。 |

- **我的裁定：`NB1-REACHABLE：未出现非有限输出；VL NB=1 在默认公共 API 与默认选项下确定性地失败（显式 RuntimeError，LAPACK info=2）。`**
- **这不是 spec 预期的"非有限输出"，因此不能直接套用 spec 的四个类别。** 需要主脑决定：(a) 把"显式失败"视为与"非有限"同等的 D003 相关问题；(b) 视为与 D003 无关的独立问题（特征值分解对 VL NB=1 不稳定）。
- **注意：** 此失败在 Master 上是**显式报告**的，因此它**不是** D003 所描述的"静默错误数值"（那种危险模式）。它可能是另一个缺陷，也可能是合法的数值拒绝。**本阶段不判断其对错。**

---

## 8. 与主脑给定事实 F1–F11 的对照

| 编号 | 主脑事实 | 结论 | 依据 |
|---|---|---|---|
| F1 | FFT 底层已有错误传递（`fft_plan_exec` 返回状态；`kiss_fftnd_checked`；`fft_plan_dft_2d` 返回 NULL） | **确认** | `fft_iface.cpp:73–133`、`kiss_fftnd.c:165–205`（代码阅读） |
| F2 | `rcwa.cpp` 场重建（约 2190–2275 行）已逐点检查并统一清理 | **确认（范围修正）** | `rcwa.cpp:2204–2270` 逐点检查 plan（2209）、exec（2245）；`2266` 统一 cleanup。行号略有偏移，结论成立。 |
| F3 | 5 个 FMM 文件不检查 `fft_plan_dft_2d` 返回 NULL，丢弃 `fft_plan_exec` 返回值 | **确认（数量细化）** | 5 个 plan 无检查（2.1）；12 个 exec 全部丢弃（2.2），比"丢弃"更具体。`fmm_closed.cpp`、`fmm_experimental.cpp` 不含 FFT，不属于此类。 |
| F4 | `Simulation_ComputeLayerModes` 约 2367–2394 行丢弃全部 `FMMGetEpsilon_*` 返回值，然后直接特征值分解 | **确认** | `S4.cpp:2368–2393` 共 11 处（2.5）；2399 行起进入特征值分解。 |
| F5 | FMM 文件中约 20 处 `S4_malloc` 无 NULL 检查，含 `fmm_closed.cpp`、`fmm_experimental.cpp` | **确认（数量修正为 17）** | 17 处（2.4），含 `fmm_closed.cpp:40`、`fmm_experimental.cpp:40`。 |
| F6 | `fmm_FFT.cpp` 的 `RNP::LinearSolve` 的 `solve_info` 被忽略 | **确认（扩展）** | `fmm_FFT.cpp:203–204` 写入但未读；`fmm_kottke.cpp:278–279` 同样（2.6）。 |
| F7 | `S4.cpp` 的 `S4_FAIL_ALLOC_AT` 仅在 clone 范围内武装，对 FMM 无效 | **确认** | `S4.cpp:733`（唯一实例化），`S4.cpp:69–73`（armed 检查）（4.6）。 |
| F8 | 历史候选 `/home/jackal/s4-fmm-20260930T132345Z`：六文件 SHA256 与记录一致；其 `S4.cpp` 是 P04 之前版本 | **未验证** | 本阶段未访问该目录（spec 禁止访问）。 |
| F9 | 历史注入器/驱动在 `/home/jackal/s4-fmm-accept/`，原理为 `--wrap=malloc` 与 `--wrap` FFT 函数 | **确认（但有限制）** | 4.1、4.8：符号兼容；`--wrap=malloc` 对 `S4_malloc` 无效（4.4）。 |
| F10 | 旧日志中 VL 在注入失败后重试输出"非有限"（`CHECK retry output is finite FAILED`），其他分支没有；未确认是否等于"VL NB1 既有非有限" | **部分确认：时序相关，因果未确认** | [历史日志] `after-vl-plan-1.log`、`after-vl-exec-1.log`、`after-vl-scratch-1.log` 三份均含 `RC first 1`、`RC retry 0`、`CHECK retry output is finite FAILED`，**且同一次运行中出现 `Layer eigensystem returned info = 2`**（第 4 行）。这与本次 T6 中的特征值失败（info=2）是同一现象。但 (a) 历史日志的 `info=2` 出现在构造期 1×1 网格的 plan 调用中，驱动的 grid 路径（nu=4,nv=3）并非其直接来源；(b) 代码阅读显示 `Simulation_ComputeLayerSolution` 对 `Simulation_ComputeLayerModes` 的错误码有传播（`S4.cpp:1855–1862`），因此 `info=2` 不应被静默转为 0；**"重试返回 0 且输出非有限"的成因未知**。`before-vl-*` 对照日志只包含注入行，不含重试。 |
| F11 | `S4.cpp`、`fmm_*.cpp` 为 CRLF 行尾 | **确认** | `file` 输出：`C source, ASCII text, with CRLF line terminators`（`S4.cpp`、`fmm_FFT.cpp`、`fmm_kottke.cpp`、`fmm_PolBasisVL.cpp`、`fmm_PolBasisNV.cpp`、`fmm_PolBasisJones.cpp`、`fmm_closed.cpp`、`fmm_experimental.cpp`、`fft_iface.cpp`、`rcwa.cpp`）。`kiss_fftnd.c` 为 "very long lines"，非 CRLF 标注。 |

---

## 9. 发现的、但本阶段不处理的问题

1. **驱动与 Master API 不兼容**：`driver.cpp:151–152` 访问不完整类型 `struct FieldCache`。修复需要改驱动或改 API 可见性，属于 S2 范围。
2. **VL NB=1 显式特征值失败**（第 7 节）：确定性失败，未被 D003 描述，性质未知。
3. **半覆盖的 `Epsilon2`/`Epsilon_inv`**（3.1）：FFT 失败后 PolBasis 会覆盖，且 `Simulation_AddFieldToCache` 会缓存半成品。代码阅读推导，未验证。
4. **`Simulation_AddFieldToCache` 的 `S4_malloc` 无检查 + `memcpy`**（2.4）：分配失败会崩溃（代码阅读）。
5. **`fmm_kottke.cpp:77` 的 `fft_alloc_complex` 未检查**（2.3）。
6. **`fmm_kottke.cpp:179–190` 的分子分母**：`abcd[0][0]` 等除法未检查为零（代码阅读，未展开）。
7. **`fmm_FFT.cpp:133`**：`shape_get_normal(&(L->pattern.shapes[imat[0]]), ...)` 的下标是否越界未核对（代码阅读，未展开）。
8. **`Simulation_ComputeLayerModes` 的 `malloc` 与 `S4_malloc`**（2267、2295、2402、2419）无检查（代码阅读）。

---

## 10. 未完成项与已知限制

### 10.1 未完成
- **T4（无注入控制）：未运行**。原因：驱动编译失败（停止条件）。
- **T5（基线故障复现）：未运行**。原因：同上。
- **T2 动态计数：未做**。仅有静态推导（第 3 节）。
- **F8：未验证**（spec 禁止访问历史候选目录）。
- **F10 的旧日志：未展开读取**。

### 10.2 已知限制
- `/tmp` 在工具调用之间清空，所有证据必须在同一作业内生成（第 1.5 节）。
- 本阶段**未修改任何 `S4/` 源码**，`git status` 在整个过程中保持干净（见第 11 节）。
- `.git/worktrees/` 按主脑授权删除（见 11.3）。
- 基线 worktree 无法创建（`/srv/nvme` 只读），改用 `git archive` 导出（按主脑批准的替代方案）。
- 静态计数（2、3 节）是**源码推导**，不能当作运行计数。

---

## 11. 原始证据索引

### 11.1 目录
- 仓库内（被 `.git/info/exclude` 忽略）：`checkpoints/p05/evidence/`
- 基线导出（易失，`/tmp`）：`/tmp/S4-p05-baseline/`（作业结束后可能消失）

### 11.2 证据文件与 sha256
见 `checkpoints/p05/evidence/EVIDENCE.sha256`（19 个文件）。关键项：

| 文件 | sha256 |
|---|---|
| `logs/60-t6-results.json` | 5e2eb52b0d15b891ef12d779e645b20768614d3b38dcf0dff4111f52e45897d6 |
| `logs/60-t6-main.log` | 792c82d87872639815e553bd49efb573ff430bc978052731dbf788628e0e8bb5 |
| `logs/61-t6-diag-layer.log` | 3e32da67da57b88d90fc2639d09bd1b157b0e3234ce3a0deb0c26bb20c62d149 |
| `logs/62-t6-repeat.log` | ad0f7934b8043912718881c61cc4345e320b55f7fb77628b4d415a55ebaeac1e |
| `logs/20-build-driver-baseline.log` | 5a9a736dd4f03cc0241d5b34b6aacddeb1515249026f4b3d7c874dc1c0dde091 |
| `logs/21-driver-syntax-diagnostic.log` | 5a9a736dd4f03cc0241d5b34b6aacddeb1515249026f4b3d7c874dc1c0dde091 |
| `rc.txt` | e1d638eba3c57d6bfec8ce612a26e415a24b2a503b883d4c211566f34cf94489 |
| `s1_run.sh` | f250b2d4b04a7c1f2c13fb423093f8b6f7cd1575e9c63a93a89fcefe8a93220a |

### 11.3 仓库状态与清理记录
- `.git/worktrees/`：原为本次失败 `git worktree add` 留下的空目录。按主脑授权，经 `ls -A` 确认为空、`worktree list` 只有主工作区后，**已 `rmdir`**（绝对路径 `/srv/nvme/projects/S4-Stanford-Stratified-Structure-Solver/.git/worktrees`）。
- `checkpoints/p05/evidence/`：本次新建，经 `.git/info/exclude` 忽略。

### 11.4 本轮 `git status`
- 收尾时 `git status --porcelain` 为空（证据被忽略，报告与摘要为新增文件，待提交）。

---

## 12. 需要主脑决定的事项

1. **VL NB=1 的显式特征值失败**：是否纳入 D003 范围？它是确定性、显式报告的，**不是**静默错误数值。
2. **驱动与 Master API 不兼容**：是否授权修改驱动（仅驱动，不改 `S4/`）以访问 `FieldCache`，或者接受 T4/T5 在 S1 无法完成，改在 S2 处理？
3. **`/tmp` 易失性**：批准的 `$BASE_DIR`/`$RUN` 在 `/tmp` 不跨调用保留。是否接受在仓库内被忽略的证据目录作为持久位置（已采用）？
