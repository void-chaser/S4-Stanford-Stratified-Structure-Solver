# P05-S3R5 修复前源码确认（PRE_FIX_SOURCE_S3R5）

> 依据：P05-S3R5 任务书 §4 S-C，硬停止条件 2，用户裁决 U283、U284。  
> 结论标注：[源码]。

---

## 1. F3 树中 S4/S4.cpp:1755–1775 行原文

在当前冻结树 F3（`6cff923a02baf19e01966b2339755cbf3a5deeef`）中，`Simulation_InitSolution` 位于 `S4/S4.cpp:1738–1790`。第 1755–1775 行原文如下：

```cpp
1755: 			S->msg(S->msgdata, "Simulation_InitSolution", S4_MSG_ERROR, "Excitation layer not found");
1756: 		}
1757: 		return 13;
1758: 	}
1759: 
1760: 	if(NULL != S->solution){
1761: 		Simulation_DestroySolution(S);
1762: 	}
1763: 	S->solution = (Solution_*)malloc(sizeof(Solution_));
1764: 	S->solution->ab = (std::complex<double>*)S4_malloc(sizeof(std::complex<double>) * S->n_layers * 4 * S->n_G);
1765: 	S->solution->solved = (int*)malloc(sizeof(int) * S->n_layers);
1766: 	if(NULL == S->solution || NULL == S->solution->ab || NULL == S->solution->solved){
1767: 		S4_TRACE("< Simulation_InitSolution (failed; could not allocate S->solution) [omega=%f]\n", S->omega[0]);
1768: 		if(NULL != S->msg){
1769: 			S->msg(S->msgdata, "Simulation_InitSolution", S4_MSG_ERROR, "Could not allocate solution memory");
1770: 		}
1771: 		return 1;
1772: 	}
1773: 	memset(S->solution->solved, 0, sizeof(int) * S->n_layers);
1774: 
1775: 	S4_TRACE("I  Simulation_InitSolution G: (%d) [omega=%f]\n", S->n_G, S->omega[0]);
```

---

## 2. H-3 中 7 个调用点对 InitSolution 返回值的处理

对全仓所有 7 处 `Simulation_InitSolution` 调用点进行逐行核查，每处均检查了非零返回码并立即终止后续执行 [源码]：

### 2.1 `S4/S4.cpp:1803`（位于 `Simulation_GetLayerSolution`）
```cpp
1802: 	if(NULL == S->solution){
1803: 		error = Simulation_InitSolution(S);
1804: 		if(0 != error){
1805: 			S4_TRACE("< Simulation_GetLayerSolution (failed; Simulation_InitSolution returned %d) [omega=%f]\n", error, S->omega[0]);
1806: 			return error;
1807: 		}
1808: 	}
1809: 	sol = S->solution;
```
- **检查确认**：`if(0 != error)` 立即返回 `error`，不执行第 1809 行的解引用与后续求解。

### 2.2 `S4/S4.cpp:2969`（位于 `Simulation_OutputStructurePOVRay`）
```cpp
2968: 	if(NULL == S->solution){
2969: 		ret = Simulation_InitSolution(S);
2970: 		if(0 != ret){
2971: 			S4_TRACE("< Simulation_OutputStructurePOVRay (failed; Simulation_InitSolution returned %d)\n", ret);
2972: 			return ret;
2973: 		}
2974: 	}
```
- **检查确认**：`if(0 != ret)` 立即返回 `ret`。

### 2.3 `S4/S4.cpp:3318`（位于 `Simulation_OutputLayerPatternRealization`）
```cpp
3317: 	if(NULL == S->solution){
3318: 		int error = Simulation_InitSolution(S);
3319: 		if(0 != error){
3320: 			S4_TRACE("< Simulation_OutputLayerPatternRealization (failed; Simulation_InitSolution returned %d)\n", error);
3321: 			return error;
3322: 		}
3323: 	}
```
- **检查确认**：`if(0 != error)` 立即返回 `error`。

### 2.4 `S4/S4.cpp:3565`（位于 `Simulation_GetEpsilon`）
```cpp
3564: 	if(NULL == S->solution){
3565: 		int error = Simulation_InitSolution(S);
3566: 		if(0 != error){
3567: 			S4_TRACE("< Simulation_OutputLayerPatternRealization (failed; Simulation_InitSolution returned %d)\n", error);
3568: 			return error;
3569: 		}
3570: 	}
```
- **检查确认**：`if(0 != error)` 立即返回 `error`。

### 2.5 `S4/S4.cpp:4070`（位于 `Simulation_GetSMatrix`）
```cpp
4069: 	if(NULL == S->solution){
4070: 		int error = Simulation_InitSolution(S);
4071: 		if(0 != error){
4072: 			S4_TRACE("< Simulation_GetSMatrix (failed; Simulation_InitSolution returned %d)\n", error);
4073: 			return error;
4074: 		}
4075: 	}
```
- **检查确认**：`if(0 != error)` 立即返回 `error`。

### 2.6 `S4/main_lua.c:2184`（位于 `lua_GetDiffractionOrder`）
```c
2184: 	i = Simulation_InitSolution(S);
2185: 	if(0 != i){
2186: 		HandleSolutionErrorCode(L, "GetDiffractionOrder", i);
2187: 		return 0;
2188: 	}
```
- **检查确认**：`if(0 != i)` 记录错误并返回 0（向 Lua 抛出错误/终止）。

### 2.7 `S4/main_python.c:1274`（位于 `S4Sim_GetBasisSet`）
```c
1274: 	ret = Simulation_InitSolution(self->S);
1275: 	if(0 != ret){
1276: 		HandleSolutionErrorCode("GetBasisSet", ret);
1277: 		return NULL;
1278: 	}
```
- **检查确认**：`if(0 != ret)` 记录 Python 异常并返回 NULL。

---

## 3. 全仓 `S->solution` / `->solution` 读写点分析

全仓共检索出 24 处包含 `->solution` 的位置（其中包含 4 处注释）：
1. `S4.cpp:287`（`Simulation_New`）：`S->solution = NULL;`（初始化清空）。
2. `S4.cpp:419`（`Simulation_SetNumG`）：`if(NULL != S->solution){ Simulation_DestroySolution(S); }`（参数改变重置）。
3. `S4.cpp:600`（`Simulation_Clone`）：`T->solution = NULL;`（克隆体初值置空）。
4. `S4.cpp:1760–1773`（`Simulation_InitSolution`）：旧解销毁、内存分配、判空、清零。
5. `S4.cpp:1802, 1809`（`Simulation_GetLayerSolution`）：判空调用 `InitSolution`，成功后赋值 `sol = S->solution;`。
6. `S4.cpp:1889`（`Simulation_ComputeLayerSolution`）：内部静态函数，仅在 `Simulation_GetLayerSolution` 成功返回后调用。
7. `S4.cpp:2844, 2857`（`Simulation_DestroySolution`）：析构函数，先判 `NULL == sol` 保护，最后 `free(S->solution); S->solution = NULL;`。
8. `S4.cpp:2869`（`Simulation_DestroyLayerSolutions`）：显式包含 `if(NULL == sol) return;` 保护。
9. `S4.cpp:2968, 3317, 3564, 4069`：均以 `if(NULL == S->solution)` 守卫后调用 `InitSolution`，且返回值非零立即退出。
10. `S4_internal.h:147`：结构体成员定义 `struct Solution_ *solution;`。

### 核心结论 [源码]
1. **无任何调用方假设"InitSolution 失败后 solution 非空"**。相反，所有调用方均在返回值非零时立即返回错误，绝不解引用 `S->solution`。
2. **正因为 F3 在 1764/1765 失败时将半初始化（野指针）的 `S->solution` 遗留在 `S` 中未清理**，导致重试路径调用 `Simulation_GetLayerSolution` 时，第 1802 行检测到 `NULL != S->solution`，误认为方案已初始化完毕，跳过 `InitSolution`，直接进入计算导致第 2 次调用崩溃（RP-R8-M2c-1b）。
3. **U284 方案在任何分配失败时严格保持 `S->solution == NULL` 并释放中间局部变量**，完全满足调用方前置条件，且彻底杜绝重试路径的悬挂野指针崩溃。
4. **未触发硬停止条件 2**：无调用方依赖"失败后 solution 非空"，无调用方在失败后解引用 `S->solution`。
