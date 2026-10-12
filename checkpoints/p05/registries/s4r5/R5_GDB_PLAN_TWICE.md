# R5-2 gdb 机理调查:plan twice NTH 12–16(fft、kottke)

证据目录:`checkpoints/p05/evidence/p05-s4r5/`(不提交)。调试构建:`dbg/`(B = 37a82e8,F = 1c11905,`-O0 -g`)。

## 0. 先说明两件事(影响结论的前提)

**0.1 等价性检查(R5-2 步骤 2)通过。** 调试构建在 12 点 × B/F 上重跑 R4 plancall pass1 的全部 24 条(另含 K=3 对照),`rc/rc1/rc2/hit` 与 R4 全部相同(24/24 SAME)。文件:`equiv/EQUIV_R5_DBG_vs_R4.tsv`。
- 首次等价性检查 24/24 DIFF,原因是我的调试构建脚本链接了旧注入器 `src/inject_d003.cpp`(不识别 `plancall:K:M`),已改为 R4 的 `stage_s4/inject_r4_plan.cpp` 并重建,之后 24/24 SAME。此事记入 ERRATA_5 与报告的工具事件表。

**0.2 R4 plancall 的 "twice" 行没有设置 `S4FMM_TWICE=slab`。** 这是任务书前提与实际记录的主要差异,也是本轮最重要的发现:
- `run_r4_plancall.py` 生成的 case 名为 `R4B-…`;`matrix_r2.build_env` 只在 case 以 `t4/` 开头时才设置 `S4FMM_TWICE=slab`。因此 R4 的 twice 行是**无 TWICE** 条件下跑的。
- 任务书背景写的是"在 `S4FMM_TWICE=slab` 时 B 与 F 的 rc/rc1/rc2 都是 1/0/1"。**实测不符**:TWICE=slab 下 F 为 `1/0/20`,B 为 **SIGSEGV**(见下)。
- 因此本报告对两种条件分别给出结论:**A 条件 = R4 实际(无 TWICE)**,**B 条件 = 任务书条件(TWICE=slab)**。

## 1. 两种条件下,第 12 次 plan 的调用者(gdb backtrace,`gdb_F_bt_plan.log`、`gdb_F_bt_plan_slab.log`)

| 条件 | plan 12 的调用者 | 注入分配大小 |
|---|---|---|
| 无 TWICE(R4 实际) | `GetFieldOnGrid`(rcwa.cpp:2209),由 `S4_Simulation_GetFieldPlane` 第二次调用(驱动 retry) | 888 B |
| TWICE=slab | `FMMGetEpsilon_FFT`(fmm_FFT.cpp:89),经 `Simulation_ComputeLayerModes`(S4.cpp:2388) | 1864 B |

这与 R3 `CALLSEQ.tsv` 一致:twice fft/kottke 的 NTH 12–16 在 CALLSEQ 中归为 FMMGetEpsilon_*。**但 CALLSEQ 对应的是 TWICE=slab 条件**(R3 的 twice 路由设置了 TWICE);R4 的 plancall 没有设置,所以 R4 的 twice 行测的是 GetFieldOnGrid 的 plan。

## 2. 逐点回答 Q1–Q5

### 条件 B(任务书条件,S4FMM_TWICE=slab)

**Q1. 被注入的 malloc 失败后,fft_plan_dft_2d 在 B 和 F 上分别返回什么?**
- F:`PLAN k=12_RET value=0x0`(NULL)。`gdb_F_twice12_slab.log:90`。
- B:`PLAN k=12_RET value=0x0`(NULL)。`gdb_B_twice12_slab.log:79`。
- 两者都是 NULL。

**Q2. F 上 NULL 检查分支是否执行?B 上是否执行 fft_plan_exec(NULL),返回值是什么?**
- F:**执行**。`FFT_NULLCHK_L90 k=6 i=0 plans[i]=0x0`(`gdb_F_twice12_slab.log:91`)。随后 `ret=1; goto cleanup`,`FMMGetEpsilon_FFT` 返回 1(`:92`)。F 上没有 `fft_plan_exec(NULL)`。
- B:**无检查**。plan 12 返回 NULL 后,B 继续创建 plan 13–16(`gdb_B_twice12_slab.log:80–88`)。随后执行 `EXEC_ENTER k=12 $rdi=93824993103952`(`:92`,即 plan 12 之前一个非 NULL 的 plan 的 exec,返回 0)与 `EXEC_ENTER k=13 $rdi=0`(`:94`),即 **`fft_plan_exec(NULL)`**,随即 **SIGSEGV** 于 `fft_iface.cpp:131`(`plan=0x0`,`:96`)。B 的进程以信号结束,rc=139。
- 注意:B 的 `fft_plan_exec(NULL)` 返回值**不存在**(进程在该调用内崩溃)。哪一个 `plans[i]` 为 NULL、为何第 13 次 exec 是第一次撞上 NULL,本轮未直接观察(未在 B 上打印 plans 数组),因此不作断言。

**Q3. 第二次 GetFieldPlane 返回的值来自哪个 return?逐层返回值:**
- `FMMGetEpsilon_FFT` 返回 **1**(`fmm_FFT.cpp:245`,`return ret`,ret=1 来自第 90 行);
- `Simulation_ComputeLayerModes` 在 `S4.cpp:2413` 看到 `fmm_ret=1`,返回 **20**(`CLM k=4_RET value=20`,`:94`);
- `Simulation_GetLayerSolution` 原样传出 20;
- `S4_Simulation_GetFieldPlane` 返回 **20**(`GFP k=2_RET value=20`,`:95`);
- 驱动 `RC retry 20`(`:98`)。
- 因此在条件 B 下,F 的第二次返回是 **20**,不是 1。

**Q4. 第一次和第二次调用里,FMMGetEpsilon_* 与 ComputeLayerModes 的返回值:**
- 第一次(`GFP k=1`):FMMGetEpsilon_FFT = 0(`FFT_EPS k=1_RET value=0`),ComputeLayerModes = 0(`CLM k=2_RET value=0`);GetFieldPlane = 0(`GFP k=1_RET value=0`),驱动 `RC first 0`。
- 第二次(`GFP k=2`):FMMGetEpsilon_FFT = **1**(`FFT_EPS k=2_RET`),ComputeLayerModes = **20**(`CLM k=4_RET`),GetFieldPlane = **20**。
- 任务书所说"第一次调用的返回码是 20"指的是 **GetFieldPlane 第一次返回 20**,这在条件 B 下不成立(第一次是 0,第二次才是 20)。

**Q5. 结论类别(条件 B)**:**(i)** — F 的检查被执行,并且是 F 返回非零的原因。F 在第二次调用中走的是 `fmm_FFT.cpp:90` → `ret=1` → `ComputeLayerModes` 返回 20。B 没有此检查,且使用了 NULL 计划,导致段错误。

### 条件 A(R4 实际条件,S4FMM_TWICE 未设置)

**Q1.** 同条件 B:plan 12 返回 NULL(B 与 F)。`gdb_F_twice12_notwice3.log:65`,`gdb_B_twice12_notwice.log:81`。

**Q2.**
- F:`fmm_FFT.cpp:90` **不适用**(plan 12 不是 FMM plan;它由 `GetFieldOnGrid` 创建,`rcwa.cpp:2209`)。`GetFieldOnGrid` 的 NULL 检查 `rcwa.cpp:2210` 对应的执行**未定**(见 2.1)。
- B:同样不适用。`GetFieldOnGrid` 的 plan 在 B 上有相同的检查(`rcwa.cpp:2210`,B 与 F 的 rcwa.cpp 完全相同,`git diff` 为空)。
- B 上 `fft_plan_exec(NULL)`:**不执行**。B 的第二次 GetFieldOnGrid 中,plan 12 之后没有 `EXEC_ENTER k=12`(`gdb_B_twice12_notwice.log`:仅 `EXEC k=6..11`,之后直接 `GOFG k=2_RET value=1`)。

**Q3. 第二次 GetFieldPlane 返回 1 的来源(条件 A,F 与 B 相同):**
- `GetFieldOnGrid`(rcwa.cpp)在 plan 12 NULL 时 `ret = 1; goto cleanup`,返回 **1**(`GOFG k=2_RET value=1`,`gdb_F_twice12_notwice3.log:66`)。
- `S4_Simulation_GetFieldPlane` 把 `grid_ret=1` 原样返回(`GFP k=2_RET value=1`,`:67`)。
- 驱动 `RC retry 1`(`:70`)。
- 本次第二次调用中**没有** FMMGetEpsilon_FFT 与 ComputeLayerModes(`fftE=1`、`clm=3`,均只在第一次调用中),因此 **20 的路径在条件 A 的第二次调用中不存在**。

**Q4. (条件 A)**
- 第一次(`GFP k=1`):FMMGetEpsilon_FFT = 0,ComputeLayerModes = 0,GetFieldPlane = 0,驱动 `RC first 0`。
- 第二次(`GFP k=2`):无 FMM 调用;GetFieldOnGrid = 1;GetFieldPlane = 1。ComputeLayerModes 不被调用。
- 这修正了任务书的"第一次调用返回码 20":在条件 A 下,第一次返回 0,第二次返回 1;20 不出现。

**Q5. 结论类别(条件 A)**:**未定**。
- 对 F:第二次返回 1 的唯一路径是 GetFieldOnGrid 的 NULL 检查 `rcwa.cpp:2210 → goto cleanup`。这一路径由函数返回值(`GOFG k=2_RET value=1`)强烈支持,但**行/地址断点没有观察到它**:`rcwa.cpp:2265`(cleanup 标签,唯一出口)的断点在整次运行中只命中 1 次(`gdb_hitcount.log`,`breakpoint already hit 1 time`),而该断点应在两次 GetFieldOnGrid 中都被经过。这一矛盾未能解释(见 2.1)。
- 因此"F 的检查是否执行"在条件 A 下**未定**。
- 对 F 的"NULL 计划被继续使用":**没有**(无 `EXEC_ENTER k=12`),所以不触发硬停。

### 2.1 条件 A 下的断点矛盾(为何写"未定")
- `rcwa.cpp:2211`(plan NULL 检查行)的行断点在 -O0 下映射不准:第一次命中时 `plan[i]` 读出垃圾值(`RCWA_PLAN_NULLCHK_L2211 k=1 … plan[i]=<err>`,`gdb_F_twice12_notwice.log`)。
- `rcwa.cpp:2265`(cleanup,唯一出口)的行断点与地址断点(`GetFieldOnGrid+3730`)都只命中一次(`gdb_F_twice12_notwice2/3.log`;`gdb_hitcount.log` 的 `breakpoint already hit 1 time`)。
- 但 `GOFG k=2_RET value=1` 与 `GOFG k=1_RET value=0` 都被 FinishBreakpoint 观察到。
- 结论:断点计数与返回值观察不一致。**无法在不改变构建的前提下判断第二次 GetFieldOnGrid 是否经过 cleanup。** 证据不足。

### 2.2 为什么不能只用源码推断
源码显示 `GetFieldOnGrid` 只有一个出口(`cleanup:`,`rcwa.cpp:2265`),所有错误路径都是 `goto cleanup`。据此可推断第二次的 return 1 来自 `rcwa.cpp:2210`。但任务书要求不得凭印象补写,且断点证据互相矛盾,因此写为**未定**,不写为"已确认"。

## 3. 结论汇总(供用户裁决)

| 条件 | F 结论 | B 结论 | 硬停? |
|---|---|---|---|
| B:TWICE=slab(任务书) | **(i)**:F 检查被执行并是返回 20 的原因;F 无 NULL 计划被使用 | 无检查;`fft_plan_exec(NULL)` → **SIGSEGV** | 否(F 不是 (iii);F 不使用 NULL) |
| A:无 TWICE(R4 实际) | **未定**:返回 1 的路径是 rcwa.cpp:2210(由返回值支持,断点矛盾) | 相同路径返回 1,无 EXEC(NULL) | 否(F 无 NULL 使用;F 不是 (iii)) |

- **硬停判定**:任务书的硬停条件是"F 的结论是 (iii),或 F 上出现 NULL 计划被继续使用"。两种条件下 F 都**不是 (iii)**,且 **F 上没有 NULL 计划被继续使用**(条件 B 中 F 在 `fmm_FFT:90` 之后 goto cleanup;条件 A 中没有 `EXEC(NULL)`)。因此**按字面规则不触发硬停**。
- 但条件 A 的 F 结论为"未定",不是 (i);按任务书"证据不足时写未定"处理,这一点需要用户知情。

## 4. 与任务书前提的差异(须用户裁决)
1. 任务书:"在 S4FMM_TWICE=slab 时 B 与 F 的 rc/rc1/rc2 都是 1/0/1"。**实测**:TWICE=slab 下 F = 1/0/20,B = SIGSEGV(rc 139)。1/0/1 只在无 TWICE 下出现。
2. 任务书:"F 上 FMM 失败经 ComputeLayerModes 时,第一次调用的返回码是 20"。**实测**:条件 B 下第一次为 0、第二次为 20;条件 A 下 20 不出现。
3. 任务书:"B 的 fmm_FFT.cpp:85 后面没有 NULL 检查"。**属实**(条件 B 下 B 因此崩溃)。但在条件 A 下 B 的 plan 12 不在 fmm_FFT 中。
4. 任务书:"R3 CALLSEQ 显示这几次 plan 调用的调用者是 FMMGetEpsilon_*"。**对 TWICE=slab 属实**(CALLSEQ 来自 TWICE 路由);**对 R4 的 plancall twice 行(无 TWICE)不属实**:调用者是 GetFieldOnGrid。
5. **R4 报告 "B 无检查却不崩溃" 的说法需修正**:在 R4 的条件下 B 不崩溃,因为 plan 12 来自有检查的 rcwa.cpp;崩溃只在 TWICE=slab 下出现。

## 5. 证据清单(相对 `checkpoints/p05/evidence/p05-s4r5/`)
- 等价性:`equiv/EQUIV_R5_DBG_vs_R4.tsv`(24/24 SAME),`equiv/runs/`
- 构建:`dbg_build_stdout2.txt`、`dbg/STAGES.txt`、`dbg/DRIVERS_DBG.tsv`、`dbg/build-dbg-{B,F}.log`、`dbg/libS4-dbg-{B,F}.sha256`
- gdb 脚本:`testing/d003/stage_s4/r5_plan_twice.gdb`(F,TWICE=slab)、`r5_plan_twice_notwice.gdb`(F,无 TWICE)、`r5_plan_twice_B.gdb`(B,TWICE=slab)、`r5_plan_twice_B_notwice.gdb`(B,无 TWICE)、`r5_plan12_bt.gdb`(backtrace)
- gdb 日志:
  - `gdb/gdb_F_twice12_slab.log`(条件 B,F)
  - `gdb/gdb_B_twice12_slab.log`(条件 B,B,SIGSEGV)
  - `gdb/gdb_F_twice12_notwice3.log`(条件 A,F,最终版)
  - `gdb/gdb_B_twice12_notwice.log`(条件 A,B)
  - `gdb/gdb_F_bt_plan.log`(无 TWICE 的 plan 调用栈)、`gdb/gdb_F_bt_plan_slab.log`(TWICE=slab 的 plan 调用栈)
  - `gdb/gdb_hitcount.log`(cleanup 断点命中次数 = 1)
- 驱动:`dbg/drivers/dbg-{B,F}/driver-d003`(sha256 见 `DRIVERS_DBG.tsv`)

## 6. 未完成/缺少的证据(若要关闭"未定")
- 条件 A 下第二次 GetFieldOnGrid 是否经过 `rcwa.cpp:2210`/`2265`:需要单步记录(如 `record` 或逐行 `stepi`),或在不改 S4/ 的前提下用更保守的构建(例如 `-O0 -g -fno-inline`)复测断点命中次数。本轮未做,因为任务书只允许只读 gdb 且调试构建已通过等价性,再增加构建变量会偏离 R4 观察。

本轮未完成/已完成 R5-2 范围,等待用户审核。
