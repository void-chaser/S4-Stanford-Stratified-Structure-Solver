# E2E_API_SURVEY_R9M3A.md — 公共 API（Python / Lua）对 S4 内部返回码的处理与可达失败点族调研（S-D1，只读源码）

> 本文件全部结论来自只读源码，标注 [源码]；未运行的路径不写成已验证。行号由本轮按原文件核对。

## 1. Python 扩展（S4/main_python.c）

[源码] 统一错误出口：`HandleSolutionErrorCode(const char *fname, int code)`，见 S4/main_python.c:134-146。
- code 在 1..20 之间时用 errstr 表（S4/main_python.c:112-132）取文案，然后 `PyErr_Format(PyExc_RuntimeError, "%s: %s", fname, str)`（:142）；
- 其他非零 code 走 `PyErr_Format(PyExc_RuntimeError, "%s: %s, error code: %d", ...)`（:144）。
- 因此 S4 内部的非零返回码在 Python 侧**转成 RuntimeError 异常**，不是忽略。

逐个求解入口（`ret != 0` → HandleSolutionErrorCode → 抛异常）：

| API | 调用行 | 错误处理行 | 结论 |
|---|---|---|---|
| `Simulation.GetAmplitudes` | `Simulation_GetAmplitudes(self->S, layer, offset, amp, ...)` :1316 | :1319 | 非零 ret 抛 RuntimeError |
| `Simulation.GetPowerFlux` | `S4_Simulation_GetPowerFlux(self->S, layer, &offset, power)` :1351 | :1353 | 非零 ret 抛 RuntimeError |
| `Simulation.GetPowerFluxByOrder` | 同一求解链 :1384 附近 | :1384 | 非零 ret 抛 RuntimeError |
| `Simulation.GetFields` | `Simulation_GetFields(...)` :1502-1506 | :1506 | 非零 ret 抛 RuntimeError |
| `Simulation.GetFieldsOnGrid` | :1597-1639 | :1639 | 非零 ret 抛 RuntimeError；非有限结果另见 :1646 |
| `Simulation.SetOptions` | :1739-1819 | :1817-1819 | 不触发求解；非法 `PolarizationBasis` 抛 ValueError |

## 2. Lua 前端（S4/main_lua.c）

[源码] `HandleSolutionErrorCode(lua_State *L, const char *fname, int code)` 定义在 S4/main_lua.c:284；文件头注释（:243）写明它“reports and, outside interactive mode, exits”。即 Lua 侧对非零返回码**报错并（非交互模式下）退出进程**，不是忽略。

| API | 错误处理行 | 结论 |
|---|---|---|
| `Simulation:GetAmplitudes` | :2318、:2334 | HandleSolutionErrorCode → 报错/退出 |
| `Simulation:GetFields` | :2788 | 同上 |
| `Simulation:GetPowerFlux` | :2227 附近的求解返回值处理 | 同上 |
| `Simulation:SetOptions` | 选项解析，非法值走 S4L_error | 不触发求解 |

## 3. 可从公共 API 选择的选项（SetOptions kwlist，[源码] S4/main_python.c:1740-1749）

`Verbosity`、`LatticeTruncation`、`DiscretizedEpsilon`、`DiscretizationResolution`、`PolarizationDecomposition`、`PolarizationBasis`、`LanczosSmoothing`、`SubpixelSmoothing`、`ConserveMemory`。

`PolarizationBasis` 只接受 `"Default"`、`"Normal"`、`"Jones"`（[源码] :1805-1819）。源码中不存在名为 `"VL"` 的选项值。

## 4. 可达的失败点族（公共 API 可达）

| 失败点族 | 可达方式 | 依据 |
|---|---|---|
| FFT 离散化（plan / exec） | `SetOptions(DiscretizedEpsilon=True, DiscretizationResolution=…)` 后求解 | [源码] S4.cpp 模式安装路径；D003 注入器 `--wrap` 覆盖 `_Z15fft_plan_dft_2d…`、`_Z13fft_plan_exec…` |
| FMM 内 `S4_malloc` 失败 | 任意一次求解（注入器 `s4malloc`） | [源码] testing/d003/src/inject_d003.cpp 的 `__wrap__Z9S4_mallocm` |
| PolBasis **Jones** | `PolarizationDecomposition=True, PolarizationBasis="Jones"` | [源码] main_python.c:1811-1814 置 `use_jones_vector_basis=1`；S4.cpp:2412/2424 走 `FMMGetEpsilon_PolBasisJones` |
| PolBasis **Normal(NV)** | `PolarizationBasis="Normal"` | [源码] :1808-1810；S4.cpp:2414/2426 走 `FMMGetEpsilon_PolBasisNV` |
| PolBasis **VL** | `PolarizationBasis="Default"`（两个标志都为 0） | [源码] S4.cpp:2417/2429 在非 Jones、非 Normal 时调用 `FMMGetEpsilon_PolBasisVL`；没有名为 “VL” 的选项值 |

## 5. 不可从公共 API 到达的点族（NOT_REACHABLE_VIA_API）

| 点族 | 结论 | 理由 |
|---|---|---|
| `ClosedForm`（`FMMGetEpsilon_ClosedForm`，[源码] S4.cpp:2422） | NOT_REACHABLE_VIA_API | SetOptions 的 9 个选项里没有 FMM 模式/ClosedForm 开关；该分支由 S4 内部按层几何自行选择，公共 API 无法确定性选定 |
| `LinearSolve` 家族 A / B / B2 / B2-buf（seam 宏 `S4_TEST_LINEARSOLVE_SEAM` / `..._NULLINFO` 等） | NOT_REACHABLE_VIA_API | [源码] 这些调用点只在 testing/d003/seam 补丁后的导出树上存在；未打补丁的 F4 公共 API 没有触发入口 |
| FMM 返回码族 E（`fmmret:`/`fmmbuf:`，ID 150..159） | NOT_REACHABLE_VIA_API | 同上：hook 由 seam 补丁插入 `Simulation_ComputeLayerModes`，未打补丁树没有该 hook |
| 分配 seam 家族 C（`alloc:` ID 21..25，含 AddFieldToCache:3977） | NOT_REACHABLE_VIA_API | [源码] 站点与 `S4_malloc` 同翻译单元，`--wrap` 不可达，需 seam 补丁（testing/d003/seam/apply_seam_r2.py） |

## 6. 对 M3a 预注册的含义

- 公共 API 可达且 M1/M2 已覆盖的族是：FFT 离散化（plan/exec）、FMM 内 S4_malloc、PolBasis Jones/Normal/VL 三条 FMM 分支；
- 因此 E2E 预注册按“可达族 × 前端（py/lua）”布点，ClosedForm 与 LinearSolve 各族单列为 NOT_REACHABLE_VIA_API；
- 本轮只构建与预注册，不运行任何注入点（仅允许 1 次无注入对照冒烟）。
