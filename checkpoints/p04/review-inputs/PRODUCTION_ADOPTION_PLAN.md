# 生产采纳差异准备（只读，未 apply、未提交）

- 报告目录：`/srv/nvme/projects/S4-Stanford-Stratified-Structure-Solver/codex-review/P04-CLAUDE-RECOVERY-DIAGNOSTIC-CLOSEOUT-20261009T071842Z-d5f1a3/native-acceptance-20261009T075603Z/`
- 验收结论见 `ACCEPTANCE_CORRECTION.md`（出口 `ISOLATED_NATIVE_INTEGRATION_ACCEPTED_WITH_DECLARED_LIMITS`）。
- 本文件不关闭 P04/D001/D002，不启动 P05，不生产 apply，不 Git 写入。
- 证据：`PRODUCTION_ADOPTION_COMPARE.json`（`production_adoption_compare.py` 的只读三方比较）。

---

## 1. 事实基线

| 项 | 值 |
|---|---|
| 补丁 | `package/engineering/PRODUCTION_ENGINEERING.patch`，SHA `1adef26caf8765eb9392091a26548cfce3318e4b9f82f6c1442cba07b621076e`（与 `LANDING_MANIFEST.json` 一致） |
| base | `963ccf153855734de968e6cf71477f324e33329c`（生产 HEAD；`git status` 显示 S4/ 无修改） |
| 变更数 | 102：产品源码/文档 13（874 行新增、199 行删除）；测试与工具 89（约 5.3 万行新增） |
| 生产当前状态 | 102/102 仍为 base（modify 的 before_sha 一致；add 的路径不存在） |
| 候选源码 `package/source` | 102/102 为 after |
| 候选 run 树 `object-RUN/candidate` | 102/102 为 after（用于 ord/asan 构建的 `candidate/S4/RNP/Eigensystems.cpp` SHA = `71817d22…353`，与 after 一致） |

**结论**：生产中没有任何一项已采纳。差异范围是全部 13 个产品文件，不只是此前核对的 4 个文件。

---

## 2. 产品源码的 hunk 分类

分类依据：`ISSUE_REGISTRY.md` 的 D001–D015 定义、`PROJECT_ROADMAP.md` 的 P04 范围，以及补丁中每个 hunk 的实际改动。

类别：
- **A** = Phase 1 必要修复（D001 或 D002，或其直接状态传播）。
- **B** = GetWaves 公共接口变更（**没有对应登记项**，需先登记并单独决定）。
- **C** = 兼容 / 死代码 / UB 清理（不关闭任何登记项）。
- **X** = 测试专用，不应进入生产。

| 文件 | hunk 数 | 类别 | hunk 内容 | 关联 |
|---|---|---|---|---|
| `S4/RNP/Eigensystems.cpp` | 8（+14/−12） | A | 1–2：`zgebak_` 置换索引 `ilo-1-ii`、`scale[i]-1`（左右两支） | **D001 根因**（逆平衡索引） |
| | | A | 3–7：`zlaqr3_`/`zlaqr0_` 的 `z_offset` 移除，`wantz` 守卫，传入 `_z__` | D002 相邻 UB（N1：compz='N' 时对 NULL z 做指针偏移）。候选 48 条 stderr 中无 N1 文本 |
| | | A | 8：`Eigensystem` 中 `info = zhseqr_(...)` 接收返回值 | **D002 状态**（仅值分支返回值） |
| `S4/rcwa.cpp` | 12（+327/−13） | A | 2：`SolveLayerEigensystem_real` 返回 `int` | D002 状态（返回契约） |
| | | A | 3、5、6：real 支路 `owns_work`（N3）、`info!=0` 时不做 q 后处理、提前返回 | D002 内存所有权 / 状态 |
| | | A | 7、8、10、11：complex 支路返回 `int`，`owns_work`（N3），循环守卫 | D002 内存所有权 / 状态 |
| | | X | 1、4、9：`#ifdef S4_TEST_EIGEN_INFO`，`#include "seam.h"` 与 `s4c_seam_resolve` 调用 | 测试专用注入，**不进入生产** |
| | | B | 12：`GetRayleighWaveRows` 与静态辅助函数（+286 行） | GetWaves |
| `S4/rcwa.h` | 2（+74/−1） | A | 1：`SolveLayerEigensystem` 返回 `int` 及注释 | D002 状态 |
| | | B | 2：`GetRayleighWaveRows` 声明、`RCWA_WAVE_UNSUPPORTED` | GetWaves |
| `S4/S4.cpp` | 10（+259/−152） | A | 2：新增 `Simulation_DiscardLayerModes`（失败时释放未安装的 modes） | D002 状态 / 失败不安装 |
| | | A | 3、4：`Simulation_ComputeLayerSolution` 检查 `Simulation_ComputeLayerModes` 返回值 | D002 状态传播 |
| | | A | 5、6、7：`Simulation_ComputeLayerModes` 捕获 `SolveLayerEigensystem` 返回值，失败返回 20 | D002 状态传播 |
| | | A | 8：`Simulation_GetPropagationConstants` 传播错误 | D002 状态传播 |
| | | A | 10：`Simulation_GetSMatrix` 传播错误 | D002 状态传播 |
| | | B | 1：删除文件顶部 `geom_*3d` 辅助函数（仅旧 GetWaves 正文使用） | GetWaves（与 hunk 9 绑定） |
| | | B | 9：`S4_Simulation_GetWaves` 重写（守卫、单波 11 字段、错误码 19） | GetWaves |
| `S4/S4.h` | 1（+30） | B | GetWaves 公共文档（返回码、缓冲区不变） | GetWaves（文档） |
| `S4/S4_internal.h` | 2（+9） | B | 错误码 18/19 文档；`Simulation_GetWaves` 内部声明说明 | GetWaves |
| `S4/main_python.c` | 3（+3/−15） | A | 1：错误表增加 19、20 条目；上限 18→20 | D002 状态（码 20 可达） |
| | | C | 2：删除死函数 `S4Sim_ConvertUnits`（静态、无引用；旧代码 `PyArg_ParseTuple` 以 NULL 作输出） | 死代码清理，**不关闭 D008** |
| | | C | 3：`S4_SolveInParallel` 删除未用的 `kwlist`/`layerName` | 编译警告清理，**D012 仍为静默 no-op，不关闭** |
| `S4/main_lua.c` | 3（+18/−2） | A | 1–2：`S4L_SOLUTION_ERROR_CODES` 18→20，增加 19、20 文本 | D002 状态（码 20）；19 为 B 的前置 |
| | | B | 3：`S4L_Simulation_GetWaves` 错误路径 | GetWaves |
| `S4/ext_lua.c` | 1（+23/−1） | B | `lua_S4_Layer_GetWaves` 分配检查与错误路径 | GetWaves |
| `S4/cubature.c` | 1（+1） | C | `make_region` 初始化 `R.errmax=0.0` | 未初始化读的 UB 清理，不关闭登记项 |
| `modules/function_sampler_2d.c` | 1（+1） | C | `(void)nrm2;` | 未用变量警告，无行为变化 |
| `S4/seam.h` | 新增（+101） | X | TEST-ONLY seam 头文件，`static` 函数，只在 `S4_TEST_EIGEN_INFO` 下包含 | **不应放入生产 `S4/`** |
| `doc/S4v2lua.md` | 1（+14/−3） | B | GetWaves 文档 | GetWaves（文档） |

汇总（产品侧共 46 个 hunk，含 `seam.h` 新文件）：A 28 个（D001 2 个，其余为 D002 及其直接状态传播）；B 10 个（GetWaves，全部未登记）；C 4 个；X 4 个（rcwa.cpp 的 3 个宏块与 1 个新文件）。

**关键依赖**：`S4.cpp` 的 hunk 1 与 hunk 9 绑定（删除的 geom 函数只被被替换的旧 GetWaves 使用）。因此 A 类 `S4.cpp` 的改动不能直接取整个文件，需要基于 post-change 文件去掉 GetWaves 段后构造子补丁，并独立编译。

---

## 3. 测试与工具（89 项，不关闭登记项）

| 路径 | 数量 | 建议 |
|---|---|---|
| `testing/phase1-d001/cases/` | 2（`d001_extension_16.json`、`d001_stage2_plan.json`） | 作为 D001 测试输入纳入（A） |
| `testing/phase1-d001/authority/` | 2（`BUILD_PLAN.json`、`REQUIRED_TESTS.json`） | 清单已列为 **excluded_runtime_authority**，不提交 |
| `testing/phase1-d002/` | 80 | D002 的 adapters、tools、cases 与 specs；按 D001/D002 的最小子集纳入，其余 P03 历史工具单列 |
| `testing/s4test/` | 7（含 `adapters/tmm_oblique.py`、`d12/` 的 stimulus、`p04_mapping_driver.cpp` 等） | `d12/` 为 D12 的测试装置，建议随 A 或单独审核；不得作为产品代码 |

这些文件是测试与工具，它们本身不能证明 D001/D002 已在生产关闭。

---

## 4. 采纳前必须修正或决定的具体事项

1. **移出 `S4/seam.h`**（X 类）。候选把测试专用头文件放进了生产 `S4/`。应移到 `testing/` 下，或在采纳补丁中删除该文件，并同步删除 `rcwa.cpp` 中的三处 `S4_TEST_EIGEN_INFO` 宏块。测试装置改为通过 `-I` 指向测试目录。
2. **GetWaves 必须先登记再决定**（B 类）。`ISSUE_REGISTRY.md` 中 D001–D015 没有对应条目。它改变了 `S4_Simulation_GetWaves` 的公共行为（非均匀层返回错误码 19，不再返回部分记录）。在登记并审核前，不要把 B 类与 A 类捆绑。若决定延后，A 类的错误表仍需保留 19 的占位（见 3）。
3. **错误表 19 条目的文本**（A 类内部一致性）。`main_python.c` 的 `errstr[19]` 是通用 `def`（"An unknown error occurred"），而 `main_lua.c` 有专门文本。Python 绑定目前没有暴露 GetWaves，因此该码在 Python 端不可达，这不是用户可见缺陷；但表项应保持一致，采纳时补上专门文本。
4. **`HAVE_LAPACK` 实数分支**（A 类 rcwa.cpp / Eigensystems.cpp / S4.cpp 中 real 支路）。默认 Linux 构建未定义该宏（仅 `Makefile.Msys2`、`Makefile.old` 定义），因此这部分仍是 `NATIVE_UNVERIFIED`。采纳说明必须写明，且不能把它写成已验证。
5. **D012、D008 不因本补丁关闭**。`S4_SolveInParallel` 仍是 `Py_RETURN_NONE`；`ConvertUnits` 只是删除死代码。它们留在 P11/P10 处理。
6. **覆盖边界**（来自 `ACCEPTANCE_CORRECTION.md` 3.2）：本次注册的 helper 只有 H-01/H-08（恒等置换），非恒等置换的 helper 与 API case 未在注册运行中。采纳前若要声称上下置换已覆盖，需要新的注册，这需要用户授权。

---

## 5. 建议的分批顺序（只是计划，不执行）

| 批次 | 内容 | 前置 |
|---|---|---|
| A1 | D001：`Eigensystems.cpp` zgebak 两 hunk；对应的测试输入（`testing/phase1-d001/cases`） | 无 |
| A2 | D002 状态与内存：`Eigensystems.cpp` 其余 hunk、`rcwa.cpp`/`rcwa.h` 中 A 类 hunk、`S4.cpp` A 类 hunk（需子补丁）、`main_python.c`/`main_lua.c` 错误码 20（含 19 占位） | A1；决定 `S4/seam.h` 的去向 |
| C | 兼容清理：`cubature.c`、`function_sampler_2d.c`、`main_python.c` 的 ConvertUnits 与 SolveInParallel 清理 | 无；不计入任何登记项 |
| B | GetWaves：`S4.cpp` 的 geom 删除与 GetWaves 重写、`rcwa.cpp` hunk 12、`rcwa.h` hunk 2、`S4.h`、`S4_internal.h`、`ext_lua.c`、`main_lua.c` hunk 3、`doc/S4v2lua.md` | 先在 ISSUE_REGISTRY 登记；用户决定是否纳入本阶段 |
| T | 测试与工具（89 项，排除 authority 两个文件） | 随对应批次审核 |
| X | `S4/seam.h` 与 `S4_TEST_EIGEN_INFO` 宏块 | 不进入生产 |

**不得**一次性整体采纳 102 项：A 与 B 在 `S4.cpp`、`rcwa.cpp`、`rcwa.h`、`S4_internal.h` 中交错，整体采纳会把未登记的 GetWaves 行为改变与 D001/D002 绑在一起。

---

## 6. 采纳后的验证（本轮未执行，需要新授权）

这些步骤都会启动新的构建或原生运行，超出本轮授权，因此只列出，不执行：

1. 在提交树上做全新 clean build；记录实际 flags、编译器、源文件 SHA、库与 extension 路径和 SHA。
2. D001 生产矩阵（f=0.427、N=1/9、s 偏振、A/B/C），在独立进程中重复；与独立 Airy/TMM 比较 R/T。
3. D002 原生契约：ASan/UBSan 的 ord/asan 构建、真实 RNP 入口、仅值分支的错误传播。
4. Python、Lua、C 公共路径的错误码 20 可见性（以及 B 批次时的码 19）。
5. 主套件（s4test、Python、Lua、test_structures），记录 pass/fail/skip 与理由。
6. 按批次做独立复核，然后才能在 `ISSUE_REGISTRY.md` 中更新 D001/D002 的关闭范围。

---

## 7. 未做的事（明确声明）

- 没有 `git apply`、没有 `git add/commit/push/reset/clean/stash`；`DEFECTS.md` 与 `ISSUE_REGISTRY.md` 未修改。
- 没有修改 `package/source`、`object-RUN`、`staging`、`engineering`。
- `PRODUCTION_ENGINEERING.patch` 只读使用；本计划中的 hunk 编号来自对补丁的只读解析。
- 没有宣称任何产品修复“已生产修复 / 已提交”。
