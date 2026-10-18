# E2E_API_SURVEY_R9M3B.md — 公共 API（Python / Lua）可达失败点族调研 v2（只读源码；标注 [源码]）

> 本文件取代 M3a 的 E2E_API_SURVEY_R9M3A.md（K-4 已判定 M3a 的不可达结论有误，U339）。全部结论来自只读源码，标注 [源码]；
> 行号由本轮按原文件核对。本轮的最终预注册由 PREREG_E2E_R9M3B.tsv 给出，nth 由注入无关的 gdb 校准（CALIB_E2E_R9M3B.tsv）确定。

## 1. 错误如何到达公共 API

### 1.1 Python 扩展（S4/main_python.c）
- [源码] `HandleSolutionErrorCode`（S4/main_python.c:134-146）：非零 code 一律 `PyErr_Format(PyExc_RuntimeError, ...)`；1..20 用 errstr 表（:112-132），其余走 ": ... error code: %d"（:144）。
- [源码] 求解入口的 ret!=0 → HandleSolutionErrorCode：GetAmplitudes :1319、GetPowerFlux :1353、GetPowerFluxByOrder :1384、GetFields :1506、GetFieldsOnGrid :1639。
- [源码] FMM 分配/计划失败在 S4.cpp:2435-2439 转成 20，沿求解链返回，因此 Python 侧表现为 `RuntimeError: GetPowerFlux: ...`。

### 1.2 Lua 前端（S4/main_lua.c）
- [源码] `S4L_error`（:229-240）：错误文本写 stderr；**非交互**模式 `lua_close` 后 `exit(EXIT_FAILURE)`（:236-239）。
- [源码] `HandleSolutionErrorCode`（:284-292）用 fname 前缀输出 `"%s: %s."`；GetPoyntingFlux 的调用点 :2232（fname="GetPoyntingFlux"）。
- [源码] 批处理模式：每个 argv 都被 `luaL_loadfile` 当脚本加载（:3551）；`-a` 的值只出现在局部变量 arg（:3498）并写入 `S4.arg`（:3532）。所以批处理 Lua 出错即退出进程。
- [源码] REPL 模式：`S4L_set_interactive(L,1)`（:3570）后逐行 `luaL_loadbuffer`+`lua_pcall`（:3572-3576），错误只打印不退出；S4L_error 因 interactive 为真不执行 exit。

## 2. FMM 路径选择（S4/S4.cpp:2400-2439，[源码]）

| 选项组合 | 调用 | 首个 S4_malloc 站点 |
|---|---|---|
| 默认（use_discretized_epsilon=0，S4.cpp:337） | FMMGetEpsilon_ClosedForm :2422 | fmm_closed.cpp:40 |
| DiscretizedEpsilon=True，PolarizationDecomposition=False | FMMGetEpsilon_FFT :2410 | fmm_FFT.cpp:75（第二处 :83） |
| DiscretizedEpsilon=True，SubpixelSmoothing=True | FMMGetEpsilon_Kottke :2408 | fmm_kottke.cpp:87（work 走 fft_alloc_complex :78，不经 S4_malloc） |
| DiscretizedEpsilon=True，PolarizationDecomposition=True，Basis=Jones/Normal/Default | FFT :2410 先执行，随后 PolBasisJones :2413 / PolBasisNV :2415 / PolBasisVL :2417 | PolBasis：fmm_PolBasisJones.cpp:108 / fmm_PolBasisNV.cpp:59 / fmm_PolBasisVL.cpp:58（**前两次 S4_malloc 来自 fmm_FFT，K-3**） |
| Lua UseExperimentalFMM | FMMGetEpsilon_Experimental :2404 | fmm_experimental.cpp:40（Python 无此选项，[源码] main_python.c:1740-1749 的 kwlist 无 experimental） |

## 3. 本轮可达且有 E2E 点族的组合（[源码]，实测由 CALIB 与正式两遍给出）

- CF：默认选项 → ClosedForm → s4malloc（fmm_closed.cpp:40），nth=1，calib size 192。
- FFT：DiscretizedEpsilon=True、无 PolDecomp → plan（fmm_FFT.cpp:89）、exec（fmm_FFT.cpp:191）、s4malloc（:75）；nth 1/1/1。
- KT：DiscretizedEpsilon=True + SubpixelSmoothing=True → plan（fmm_kottke.cpp:93）、exec（:271）、s4malloc（:87）；nth 1/1/1。
- JONES / NV / VL：DiscretizedEpsilon=True + PolarizationDecomposition=True + Basis → s4malloc 在 PolBasis 文件内，nth=3（前两次在 fmm_FFT），calib size 192。
- EXP：仅 Lua UseExperimentalFMM → s4malloc（fmm_experimental.cpp:40），nth=1，calib size 192。

## 4. 不可由公共 API 到达、只能靠 seam 补丁的族（标 SEAM_ONLY；覆盖行见 COVERAGE_E2E_R9M3B.tsv）

- LinearSolve A/B/B2/B2-buf：hook 只在 testing/d003/seam 补丁后的导出树存在（[源码] testing/d003/src/inject_d003.cpp:79-97 的注释与 S4_TEST_LINEARSOLVE_AFTER），未打补丁的 F4 没有入口。
- FMM 返回码族 E（fmmret/fmmbuf）：hook 由 seam 补丁插入 Simulation_ComputeLayerModes（[源码] inject_d003.cpp 的 addf/fmmret 家族），未打补丁树无入口。
- 分配 seam 家族 C（alloc: ID 21..25，含 AddFieldToCache）：站点与 S4_malloc 同翻译单元，--wrap 不可达，需 seam 补丁（[源码] inject_d003.cpp:480-496）。
- kottke_alloc:31：由 seam 补丁的 S4_TEST_KOTTKE_HOOK 到达（[源码] inject_d003.cpp:544-553），公共 API 无入口。

## 5. 对 M3b 装置的含义（与 U340/U341 一致）

- 每个前端（py / lua_batch / lua_repl）的点族按第 3 节布点；nth 由 CALIB 校准给出，不在装置里手写；
- visible 判据必须是具体错误文本：Python 为 RuntimeError 且文本含 "GetPowerFlux"；Lua 为以 "GetPoyntingFlux: " 开头的 stderr 行（WITNESS/HIT 行不算）；
- Lua 批处理出错即退出，exp_retry_same=NOT_APPLICABLE_PROCESS_EXIT；同对象重试由 REPL 前端观测（第一次求解返回 nil、第二次等于参考值）；
- 参考值一律由运行器另起无注入进程得到，注入变量只覆盖注入步的注入进程。
