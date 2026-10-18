# D016_TRACE_S5R2.md -- read-only source trace of the D016 -10 path on F4 ([源码]).
# F4 = 05097a7:S4 (tree 589e15eb11fcb04e031b524f25a443e7921946cf). Nothing was run for this trace;
# the line numbers below are asserted by the generator against the F4 working tree before writing.
# written: 2026-10-18T09:36:24Z

## 1 链路（文件:行号，均为 F4）

| 步 | 文件:行 | 作用 | 关键文本（[源码]） |
|---|---|---|---|
| 1 | S4/pattern/pattern.c:2212-2215 | D016 零场/非有限检查：返回 -10（在 1./max_field 之前） | if(!(max_field > 0) \|\| !isfinite(max_field)){ ; return -10; |
| 2 | S4/fmm/fmm_PolBasisVL.cpp:144-152 | PolBasisVL 调用 Pattern_GenerateFlowField；error 非零时释放并原样返回 | int error = Pattern_GenerateFlowField( ; if(0 != error){ ; return error; |
| 3 | S4/S4.cpp:2422-2429 | 默认选项（ClosedForm）后进入 PolBasisVL | fmm_ret = FMMGetEpsilon_ClosedForm( ; fmm_ret = FMMGetEpsilon_PolBasisVL( |
| 4 | S4/S4.cpp:2435-2438 | FMMGetEpsilon 返回非零 → ComputeLayerModes 返回 20 | if(0 != fmm_ret){ ; return 20; |
| 5 | S4/S4.cpp:1878-1881 | ComputeLayerSolution 原样传播 20 | Simulation_ComputeLayerModes(S, L, layer_modes) ; return modes_error; |
| 6 | S4/S4.cpp:1828-1831 | GetLayerSolution 原样传播 | Simulation_ComputeLayerSolution(S, L, layer_modes, layer_solution) |
| 7 | S4/S4.cpp:2518-2522 | GetPowerFlux 返回 ret=20 | Simulation_GetLayerSolution(S, layer, &Lmodes, &Lsoln) ; return ret; |
| 8 | S4/main_python.c:114-137 | Python 前端：错误码 20 映射为 RuntimeError 文本 | void HandleSolutionErrorCode(const char *fname, int code){ ; The layer eigensystem could not be solved; no solution was returned |
| 9 | S4/main_python.c:1351-1354 | Python GetPowerFlux 用 fname=GetPowerFlux 报错 | ret = S4_Simulation_GetPowerFlux(self->S, layer, &offset, power); ; HandleSolutionErrorCode("GetPowerFlux", ret); |
| 10 | S4/main_lua.c:269-270 | Lua 前端：错误码 20 文本（句末带点） | The layer eigensystem could not be solved; no solution was returned |
| 11 | S4/main_lua.c:284-291 | Lua HandleSolutionErrorCode → S4L_error 打印（非交互模式退出） | void HandleSolutionErrorCode(lua_State *L, const char *fname, int code){ ; S4L_error(L, |
| 12 | S4/main_lua.c:2227-2232 | Lua GetPoyntingFlux 用 fname=GetPoyntingFlux 报错 | ret = S4_Simulation_GetPowerFlux(S, ; HandleSolutionErrorCode(L, "GetPoyntingFlux", ret); |
| 13 | S4/rcwa.cpp:882-884 | info=2 的 stderr 打印只在 SolveLayerEigensystem 实际运行且 info!=0 时发生 | fprintf(stderr, "Layer eigensystem returned info = %d |

## 2 由此推出的公共 API 期望（[源码]，未运行）

- 根因返回值：pattern.c 第 2214 行返回 -10（此前 S3R2 提交 3e77aa9 实施）。
- 传播：fmm_PolBasisVL.cpp 第 151 行原样返回 -10 → S4.cpp 第 2438 行统一转成 20。
- Python：S4.cpp 第 2522 行返回 20 → main_python.c 第 137 行文本 → HandleSolutionErrorCode 抛 RuntimeError，fname=GetPowerFlux，文本为：
  GetPowerFlux: The layer eigensystem could not be solved; no solution was returned
- Lua：同一 20 → main_lua.c 第 269 行文本 → HandleSolutionErrorCode（fname=GetPoyntingFlux，main_lua.c 第 2232 行）经 S4L_error 打印到 stderr，文本为（句末带点）：
  GetPoyntingFlux: The layer eigensystem could not be solved; no solution was returned.
- REPL 交互模式（无脚本参数、stdin 输入）下 S4L_error 只打印并返回，不退出进程；批处理模式下退出码为 1。因此 Lua 公共 API 实测使用 REPL，才能在同一进程内做重试与新对象恢复。
- stderr 的 Layer eigensystem returned info = 2：只在 SolveLayerEigensystem 实际运行且 info!=0 时由 rcwa.cpp 第 883 行打印。本链路在 2438 行提前返回 20，特征值求解没有被调用，因此该行不应出现。
- NV 的 -10 路径：NV 的 NG=1 max_field 非零（S1R [源码]），不触发 -10；维持 [源码] 结论（U365）。
