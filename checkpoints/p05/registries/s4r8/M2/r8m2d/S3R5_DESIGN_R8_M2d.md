# S3R5 修复设计规范（P05-S3R5 轮候选设计）

> 依据：P05-S4 R8 M2d 任务书 §4 S-I，用户裁决 U275。  
> 约束：本轮不改 `S4/`，不得在 `S4/` 下生成文件或补丁文件。本文件仅记录文字方案与伪代码，供用户审核。

---

## 1. 缺陷物理机理与实测证据总结

在 P05-S4 R8 M2c/M2d 轮次中，通过物理实测（GDB 堆栈追踪与 ASAN 日志）完整表征了 `S4.cpp` 中 `Simulation_InitSolution` 的两处级联内存缺陷：

### 1.1 RP-R8-M2c-1（第 1 次调用崩溃，F_CONFIRMED）
- **位置**：`S4/S4.cpp:1763–1766`（冻结基线 B 见 `S4.cpp:1754–1757`）。
- **原代码缺陷**：
  ```cpp
  1763: S->solution = (Solution_*)malloc(sizeof(Solution_));
  1764: S->solution->ab = (std::complex<double>*)S4_malloc(...);
  1765: S->solution->solved = (int*)malloc(sizeof(int) * S->n_layers);
  1766: if(NULL == S->solution || NULL == S->solution->ab || NULL == S->solution->solved)
  ```
  1763 行 `malloc` 分配 `S->solution` 失败返回 `NULL` 时，1764 行在判空前直接解引用 `S->solution->ab`。
- **实测表现**：在第 1 次调用（`driver_r6b_state.cpp:211`）立即触发 SIGSEGV（ASAN 报 `ERROR: AddressSanitizer: SEGV on unknown address 0x0... in Simulation_InitSolution S4.cpp:1764`）。

### 1.2 RP-R8-M2c-1b（第 2 次重试崩溃，F_CONFIRMED）
- **位置**：`S4/S4.cpp:1764,1765; 1802; 1995,2021`。
- **原代码缺陷**：
  若 1764 行（`ab`）或 1765 行（`solved`）分配失败，1766 行判空条件虽然成立并进入错误分支返回 1，但**未将已分配的脏指针释放，且 `S->solution` 保持非空野状态**。
  在第 2 次调用重试时（`Simulation_GetLayerSolution:1802`）：
  ```cpp
  if(NULL == S->solution){
      ret = Simulation_InitSolution(S);
      if(ret){ return ret; }
  }
  ```
  检查发现 `S->solution != NULL`，错误判定方案已初始化，直接跳过 `InitSolution`。随后进入 `Simulation_ComputeLayerSolution`：
  - 若 `ab == NULL`（1764 失败）：1995 行 `memset(pab, 0, ...)` 传入空指针，崩于 libc `__memset_avx2_unaligned_erms`；
  - 若 `solved == NULL`（1765 失败）：2021 行解引用 `sol->solved[layer_idx]`，立即触发 SIGSEGV。
- **实测表现**：r8m2d 实测证实 `R6BSTATE 1` 中 `solution` 保持非 NULL，第 2 次重试调用（`driver_r6b_state.cpp:227`）必然崩溃。

---

## 2. S3R5 修复设计方案

### 2.1 核心修复原则
1. **立即判空原则**：每次 `malloc` 或 `S4_malloc` 分配后，必须立即检查返回值是否为 `NULL`，严禁在未判空前对结构体成员进行解引用。
2. **完全清理原则**：任何后置分配失败时，必须逆向释放前序已分配的内存，并将 `S->solution` 指针置为 `NULL`。
3. **保持错误通报原则**：分配失败时保持原有 `S4_MSG_ERROR` 通报与 `S4_TRACE` 日志，返回码保持为 1。

### 2.2 修复伪代码设计（针对 `S4/S4.cpp:1760–1774`）

```cpp
	/* 1. 若已有旧方案，先销毁清理 */
	if(NULL != S->solution){
		Simulation_DestroySolution(S);
	}

	/* 2. 分配主结构体 Solution_，并立即判空 */
	S->solution = (Solution_*)malloc(sizeof(Solution_));
	if(NULL == S->solution){
		S4_TRACE("< Simulation_InitSolution (failed; could not allocate S->solution) [omega=%f]\n", S->omega[0]);
		if(NULL != S->msg){
			S->msg(S->msgdata, "Simulation_InitSolution", S4_MSG_ERROR, "Could not allocate solution memory");
		}
		return 1;
	}
	/* 关键：立即将成员指针置空，防止析构或异常时读取野指针 */
	S->solution->ab = NULL;
	S->solution->solved = NULL;

	/* 3. 分配 ab 数组，并立即判空 */
	S->solution->ab = (std::complex<double>*)S4_malloc(sizeof(std::complex<double>) * S->n_layers * 4 * S->n_G);
	if(NULL == S->solution->ab){
		/* 失败清理：释放主结构体并重置 S->solution = NULL */
		free(S->solution);
		S->solution = NULL;
		S4_TRACE("< Simulation_InitSolution (failed; could not allocate S->solution->ab) [omega=%f]\n", S->omega[0]);
		if(NULL != S->msg){
			S->msg(S->msgdata, "Simulation_InitSolution", S4_MSG_ERROR, "Could not allocate solution memory");
		}
		return 1;
	}

	/* 4. 分配 solved 状态数组，并立即判空 */
	S->solution->solved = (int*)malloc(sizeof(int) * S->n_layers);
	if(NULL == S->solution->solved){
		/* 失败清理：释放 ab 数组与主结构体，重置 S->solution = NULL */
		S4_free(S->solution->ab);
		free(S->solution);
		S->solution = NULL;
		S4_TRACE("< Simulation_InitSolution (failed; could not allocate S->solution->solved) [omega=%f]\n", S->omega[0]);
		if(NULL != S->msg){
			S->msg(S->msgdata, "Simulation_InitSolution", S4_MSG_ERROR, "Could not allocate solution memory");
		}
		return 1;
	}

	/* 5. 全部成功后安全执行初始化 */
	memset(S->solution->solved, 0, sizeof(int) * S->n_layers);
```

---

## 3. 受影响文件与行号清单

| 文件 | 行号范围 | 修改性质 | 说明 |
|---|---|---|---|
| `S4/S4.cpp` | `1763–1773` | 代码逻辑重构 | 逐个分配、立即判空、失败清理并置 `S->solution = NULL` |
| `S4/S4.cpp` | `2837–2859` | 交叉复核 | `Simulation_DestroySolution` 自身已有判空保护，逻辑一致无需修改 |

---

## 4. 修复后预期行为对比（F4 vs F3 vs B）

| 场景 / 注入点 | 基线 B（未修复） | 当前被测树 F3（已表征） | 修复后被测树 F4（预期） |
|---|---|---|---|
| **1763 失败** (`solution=NULL`) | 调用 1 崩溃（`S4.cpp:1755` 解引用空指针） | 调用 1 崩溃（`S4.cpp:1764` 解引用空指针） | **调用 1 返回 1（S4_MSG 报错）；S->solution 为 NULL；调用 2 重试成功返回 0** |
| **1764 失败** (`ab=NULL`) | 调用 1 返回 1，调用 2 重试崩溃于 `memset(pab)` | 调用 1 返回 1，调用 2 重试崩溃于 `S4.cpp:1995 memset(pab)` | **调用 1 返回 1（S4_MSG 报错）；S->solution 为 NULL；调用 2 重试成功返回 0** |
| **1765 失败** (`solved=NULL`) | 调用 1 返回 1，调用 2 重试崩溃于 `S4.cpp:2012` | 调用 1 返回 1，调用 2 重试崩溃于 `S4.cpp:2021` | **调用 1 返回 1（S4_MSG 报错）；S->solution 为 NULL；调用 2 重试成功返回 0** |
