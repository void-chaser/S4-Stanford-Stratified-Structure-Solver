# P05 交付轮 REL-R4 报告（原版 S4 / 当前三方对照 + MPI + C API 对照）

> 轮次标识：**P05 交付轮 REL-R4**（rel-r4）。它是交付验证轮，**不是** P05 的新阶段；S1–S5、REL-R1、REL-R2、REL-R3 的历史文件一律未改。
> **本轮不修任何东西**：`S4/`、`examples/`、Makefile 与产品分支 `p05/d003-fft-error-propagation` 均未改；**没有推送任何 ref，没有改 PR #17**；只有两个本地提交（见附录 C）。
> 本报告正文在提交 (i) 冻结；正式 end 门禁结果只追加在结尾的附录 C（提交 (ii)）。

## 1 范围与判定口径

用户裁决 U399–U403（本轮任务书 §1，原文追加在 `checkpoints/p05/registries/RULINGS.tsv`）：

- **U399**：对照基准从"P05 修复前（B）"扩大到"原版 S4（U，上游 victorliu/S4 master `7fd00a2`）"。目标是确认原版能跑通的，当前 F4 也能跑通；原版跑不通、当前能跑通的，记为改进。
- **U400**：原版克隆放在本轮证据目录内（`$EV/upstream/S4`），保留为证据、不提交。
- **U401**：U 只因 gcc 15 把 `int-conversion` 当错误而不能编译；允许构建环境变量加 `CFLAGS=-Wno-error=int-conversion`，不改 U 的源文件与 Makefile；并须核实没有任何 example 调用 `GetAmplitudes`。
- **U402**：MPI 示例这轮必须实际运行。
- **U403**：C API 按原 `examples/C_api/main.c` 的逻辑、用当前公开 C API 新写测试程序（P13 的提前检查，不算完成/修复 P13）。

三棵树：**U** = 上游原版 master `7fd00a2`；**B** = 本仓库 `5b72793`（D003/D001/D002 未修复基线，`S4/` 与 `37a82e8` 相同）；**F4** = 本仓库 `3de6d8b`（P05 冻结被测树，`S4/` = `589e15eb`）。U≠F4 时按需构建中间树 **M** = `b97f639`（"原版 + Lua/Python 前端修复"）做归因；为定位来源提交又构建了 **M2** = `963ccf1`、**M3** = `5cf534c`（§7）。

判定类别按任务书 §4：SAME / DIFF_WITHIN_TOL / DIFF_ATTRIBUTED / REGRESSION / IMPROVED / BOTH_FAIL / U_UNAVAILABLE / FLAKY。
**REGRESSION 不是停止条件**（任务书 §9）；本轮照实记录、跑完全部矩阵后报告。

**"有效通过"口径（见 ERRATA ER4-1）**：U 的 Lua 前端在脚本出错时仍以 rc=0 退出（stderr 有 Lua 错误与 traceback），B/F4 的同类错误 rc=1（P04 前端重写修正了退出码）。因此本轮"通过"= rc==0 **且** stderr 无 Lua 错误标记；否则 U 的 7 个既有失败会被误记为 REGRESSION。该口径是对判定实现的澄清，未改任何预注册类别或容差。

## 2 三棵树、构建与环境

三棵树都用**独立克隆**（不在工作树内用 `git archive` 导出）：U 为网络只读克隆，B/F4 为同一仓库的本地 `git clone --revision <commit>`。每棵树的 `S4/` 目录都用 git tree-object 算法从克隆文件重算哈希，与主仓库 `git rev-parse <commit>:S4` 一致（`TREES_RELR4.tsv`）。

| 树 | 提交 | `S4/` 树哈希 | 克隆方式 | `make -j16 build/S4` | `build/S4` sha256（节选） |
|---|---|---|---|---|---|
| U | `7fd00a2` | `06553f72e93aaef1a5c9294f358a7f5afbd42bb1` | `git clone https://github.com/victorliu/S4.git $EV/upstream/S4` | OK（环境变量 `CFLAGS=-Wno-error=int-conversion`） | `a724441ae1453cebb62d7b6f6b456258e65eb6ada0b6a47e1db8d770e6605d5e` |
| B | `5b72793` | `1d738e64f9864a475fdb3de34cd3601605df2c64` | `git clone --revision 5b72793 $REPO $EV/trees/B` | OK | `9b05692e7b340d3009e7411f1a5c220245ba85bdd0f7a2af77c3b1798a62e983` |
| F4 | `3de6d8b` | `589e15eb11fcb04e031b524f25a443e7921946cf` | `git clone --revision 3de6d8b $REPO $EV/trees/F4` | OK | `fb375c726101ae2d935e929fece54b1867aa0435b24e9fe92bdeda77314396f2` |

- **U401 证据**：U 不带 override 单独编译 `S4/main_lua.c` 时**恰好 1 个 error**：
  `S4/main_lua.c:2207:17: error: passing argument 2 of 'Simulation_GetAmplitudes' makes pointer from integer without a cast [-Wint-conversion]`；
  带 `CFLAGS=-Wno-error=int-conversion` 后 rc=0（`U_PROBE_RELR4.tsv`、`u_probe/main_lua_no_override.log`）。该 bug 在 fork 中由 `93b1c90` 修复。
  **没有任何 example 调用 `GetAmplitudes`**：U/B/F4 三棵树的 `examples/**/*.lua` 各 51 个，命中数均为 0（`U_PROBE_RELR4.tsv`）。
- **构建警告差异**：U 37 条、B 35 条、F4 35 条；**B→F4 新增 0、减少 0**（与 REL-R1 一致）；U→B/F4 唯一"新增"警告是 U 的 `SingularLinearSolve` unused，U 独有 3 条（`info may be used uninitialized`、`comparison between pointer and integer`、`GetAmplitudes int-conversion`），后两条正是被 fork 修掉的（`WARN_DIFF_RELR4.txt`）。
- **U 的 Python 接口（只尝试一次）**：`sh gensetup.py.sh build build/libS4.a` rc=0，`python3 setup.py build` **rc=1**：`S4/main_python.c:342:40: error: implicit declaration of function 'PyInt_AsLong'`（Python 2 API，Python 3.14 已移除）→ 归类 **U_PY_UNAVAILABLE**（`U_PY_RELR4.tsv`）。
- **环境**：Python 3.14.4、Lua 5.2.4（系统 lua5.2）、gcc/g++ 15.2.0、LAPACK/BLAS 3.12.1-7ubuntu1、nproc=16、git 2.53.0、OpenMPI（`mpicc`/`mpirun` 见 `GATE_RELR4_start.txt` 的 RECORD 行）。
- **/tmp 顶层快照**：开始 0 项（sha256 `01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b`），结束同样 0 项、sha 相同；OpenMPI/PMIx 会话目录落在 `$EV/tmp`（见 §9 表二），未写仓库外路径。

## 3 预注册

`PREREG_RELR4.tsv`：**493 个单元**（T1 运行单元 306 + T1 比较 99（含 1 条 M 归因条件行）+ T2 13 + T2 比较 6 + T3 33 + T3 比较 20 + T4 13 + T4 比较 1 + T5 2 + 其余条件行），
sha256 = `90bb8884b7346857e29e22e1d3cc53aeff748bdddd0774240337ad1b02d939df`（`PREREG_RELR4.tsv.sha256.txt`），状态 **INFLUENCED**。
期望来自源码阅读（`EXPECT_SCAN_RELR4.tsv`：注册的 Lua API、`loadstring`/`GetRealMaterial`/语法错误分类）、REL-R1 的 B/F4 结论、U401 裁决与三树构建日志，**不是**盲试。
预注册之后没有任何期望被改写；执行/判定口径的补充与两次执行事件记在 `ERRATA_RELR4.txt`（ER4-1…ER4-5）。

## 4 运行矩阵与结果

### 4.1 T1 全部 examples × U/B/F4 × 2 遍（306 次运行）

51 个 `.lua`（含 2 个 MPI 示例，本节用非 MPI 的 `build/S4` 跑，MPIRank=0、MPISize=1，作为 5.4 的单进程参考），每棵树 2 遍，每例独立 cwd，超时 3600 s、并发 4。
306/306 完成，**0 超时**；每树状态：U 90 RAN_OK / 12 RAN_FAIL，B 80/22，F4 80/22（U 的 RAN_FAIL 是 Li 4 例 + fig4 + threading/parallel 的 SIGSEGV，每例 2 遍）。

**B vs F4（REL-R1 复现）**：49 个非 MPI 示例 = **SAME 38、BOTH_FAIL 11、DIFF 0**，与 REL-R1 完全一致 → **环境没有漂移**（`NON_REGRESSION_B=PASS`）。

**U vs F4（49 个非 MPI 示例）**：

| 类别 | 数 | 清单（细节见 `VERDICT_RELR4.tsv`） |
|---|---|---|
| SAME | 27 | fig6、table1m2g2、transmission_spectrum、Bi fig3a、Liu fig2a/3a/3b/3c/3d/3e/3f/4e、Oliva fig1c、Pietarinen fig2a、Li ex3、Suh fig2a/2b、Integrate、patterns ×6、polarization_basis ×2、spectrum_sampler |
| DIFF_WITHIN_TOL | 3 | fabry_perot/slab_resonances（3.201e-13）、Fan fig12（1.356e-13）、interpolator（数值同、非逐字节） |
| DIFF_ATTRIBUTED | 6 | Antonoyiannakis fig3_4、fabry_perot/fresnel、tir、tir_field、magneto/halfspace、simple；stdout 相对差 1.0–1.999（U 在若干分量上输出 0，而 F4 非零）。归因见 §7 |
| REGRESSION | **0** | — |
| IMPROVED | 2 | Tikhodeev fig4（U rc=-11 段错误，F4 rc=0）、threading/parallel（U rc=-11，F4 rc=0） |
| BOTH_FAIL | 10 | Christ fig2b（U 静默 rc=0 + Lua 错误；F4 rc=1）、Li ex1_new/ex1_normal/ex1_orig（U SIGSEGV；F4 rc=1）、convergence/1d/binary_grating、cellA、cellB、ex2/fig2、resonance_pos/ref、magneto/slab（U 静默 rc=0；F4 rc=1） |
| FLAKY | 1 | Li ex2：U 两遍都 SIGSEGV（-11），崩溃前未刷新 stdout 的部分输出在两遍间不同 → 按"同一棵树两遍不同"记 FLAKY；**F4 无 FLAKY**（`FLAKY_F4=0`） |
| U_UNAVAILABLE | 0 | — |

### 4.2 T2 参考例（3 例 × 3 树，用 F4 树的 `testing/runtests.sh` 指定 `S4_BIN`）

| 树 | simple（1e-12） | fresnel（1e-12） | Fan fig12（1e-10） | `runtests.sh` |
|---|---|---|---|---|
| U | **FAIL_REF**（relmax 1.0） | **FAIL_REF**（relmax 1.0） | PASS_REF（1.277e-13） | **FAIL**（rc=1） |
| B | PASS_REF（0） | PASS_REF（0） | PASS_REF（1.277e-13） | PASS |
| F4 | PASS_REF（0） | PASS_REF（0） | PASS_REF（1.277e-13） | PASS |

即：B/F4 与提交的参考数据在容差内一致；**U 在 simple/fresnel 上不一致（相对差 1.0）**，与 §4.1 的 6 个 DIFF_ATTRIBUTED 同源（§7）。
**原版自带的回归测试不可运行**（逐项核实，见 `EXPECT_SCAN_RELR4.tsv`、`T2_U_OWN_MANIFEST`）：U 的 `testing/runtests.sh` 是 CRLF 行尾（`` 21 处），在 `sh` 下直接语法错误（`runtests.sh: 2: : not found` … `Syntax error: "done" unexpected`，rc=2）；`testing/testcases.txt` 的 10 个用例里 **10 个参考文件全部缺失**、**7/10 的脚本路径不存在**（如 `fabry_perot/fresnel.lua` 实际在 `0d/fabry_perot/`）；旧脚本还把 `S4_BIN` 硬编码为 `../S4`（旧的构建布局）。

### 4.3 T3 MPI（B、F4、U 三棵树都构建并实际运行 S4mpi）

- **预检**：`mpirun -np 2 true` rc=0；最小 MPI 程序（`mpi_probe_relr4.c`）打印 rank 0、1，rc=0（`mpi/PRECHECK_RELR4.tsv`）。没有出现 TMPDIR 路径过长或 PMIx 安装不全的问题，也没有把 TMPDIR 改到仓库外。
- **构建**：三棵树都用任务书 §5.4.2 的命令（只通过命令行传 `CC=mpicc CXX=mpicxx MPI_INC=… MPI_LIB=…`，不改 Makefile；U 另加 `CFLAGS=-Wno-error=int-conversion`）构建出 `build/S4mpi`，rc=0；`build/S4mpi -v` 横幅三棵树都含 **"With MPI support"**。
- **运行**：两个 MPI 示例 × 树 × `-np 1`/`-np 4` × 2 遍 = **24/24 RAN_OK**，每次独立 cwd，产出 `out0..3.txt`。
- **判据 a**（`-np 4` 按频率合并 vs `-np 1` 的 `out0.txt` vs 5.1 非 MPI 的 `out0.txt`）：**12/12 PASS**。在 IEEE double 完全相同的频点（23 个，均为 rank0 覆盖段）上最大相对差 **0**；覆盖情况只记录（合并 92 点，仅 23 点与单进程频点完全相同，67 点只差最后几位；参考侧 67 点无对应）。把"打印后相同文本"当相同频率会错配 1-ulp 不同频点、在陡峭处得到 1.458e-12 的观测值，按 ER4-2 仅记录、不判失败。
- **判据 b**：B 与 F4 的同名 MPI 输出（np1 与 np4）**逐字节一致**（4/4 SAME）。
- **判据 c**：U 对 F4 **SAME**（np1、np4 的输出文件逐字节一致，4/4）→ 无 DIFF_ATTRIBUTED，MPI 路径不需要额外归因。
- **判据 d**：README 指向的 `examples/1d/binary_grating.txt` 在三棵树里都不存在——只记录，不作为判据（`MPI_RELR4.tsv` 的 T3_RECORD_MISSING_1D_REFERENCE）。

### 4.4 T4 C API（P13 提前检查，不是完成或修复 P13）

新程序 `testing/d003/stage_relr4/capi_fig12_relr4.c`：按 `examples/C_api/main.c` 的物理设定（见下）用**当前公开 C API**（只用 `S4/S4.h`）重写；原示例未动。

物理设定与源码依据：
- 晶格 `{1,0;0,1}`、NumG=100、air ε=1、Si ε=12；above（厚 0，air）、slab（厚 0.5，Si 背景，圆心 (0,0)、半径 0.2 的 air 圆）、below = above 的复制（`S4_Simulation_SetLayer(..., copy=above_id, material=-1)`，与 Lua `AddLayerCopy` 相同）。
- 圆区域半宽：Lua `SetLayerPatternCircle` 用 `S4_REGION_TYPE_ELLIPSE` + `{radius,radius}`，而 `Simulation_AddLayerPatternCircle` 存 `vtab.circle.radius=radius`；公开 C 路径 `S4_Layer_SetRegionHalfwidths(..., S4_REGION_TYPE_CIRCLE, hw, ...)` 用 `halfwidths[0]` 作半径，故 `hw={0.2,0.2}`（`S4/S4.cpp`、`S4/main_lua.c`、`testing/s4test/capi_field_plane_driver.cpp` 的等价性注释）。
- 平面波：Lua `SetExcitationPlanewave({0,0},{1,0},{0,0})`（正入射、只有 s、幅度 1）；公开 C API 的等价参数为 `kdir={0,0,1}, udir={0,1,0}, amp_u={1,0}, amp_v={0,0}`（同上 driver 的 documented equivalence）。
- 频率：`S4_Simulation_SetFrequency` 收的是频率 f（cycles/单位长度）并存 ω=2πf（`S4/S4.cpp`），Lua `SetFrequency` 调用同一函数，故传 f 不传 ω。
- 透射功率：below 层 offset 0 的前向功率 = `S4_Simulation_GetPowerFlux` 返回的 `power[0]`（Lua `GetPoyntingFlux` 同一函数）。
- 主模式 `printf("%g\t%g\n", freq, forward)`；另有 `--lua-sweep` 模式按 fig12.lua 的频点打印 `%.17g` 供 1e-10 阳性对照（不改变主模式行为）。

结果：

| 项 | B | F4 | U |
|---|---|---|---|
| 新程序构建（`gcc -O0 -g -IS4 … -Lbuild -lS4 -llapack -lblas -lstdc++ -lm`） | BUILD_OK | BUILD_OK | BUILD_OK（U 的公开 C API 也够用） |
| 原 `examples/C_api/Makefile` 原样跑 | rc=2 | rc=2 | rc=2（macOS 专用 `-framework Accelerate -lc++`，Linux 下 make 失败） |
| 原 `examples/C_api/main.c` 用三树各自头文件编译 | rc=1 | rc=1 | rc=1（`unknown type name 'Simulation'; did you mean 'S4_Simulation'?`——示例用的是 P04 之前的 API 名字） |
| `spec.awk`（未修改，35 频点）vs 提交的 `spec.awk.out` | **PASS_REF** | **PASS_REF** | **PASS_REF** |
| 与 spec.awk.out 偏差 | 行数 35/35、频率列一致、超容差行 0、max_abs=0、max_rel=0 | 同 B | 同 B |
| 阳性对照 C vs Lua fig12.lua（7 频点） | max rel **3.796e-15** | 3.796e-15 | 3.796e-15 |
| B 与 F4 C 输出逐字节一致 | **SAME**（spec.awk.out sha256 `1050b45f…`） | — | U 与 F4 也逐字节一致（`max_rel=0`） |

**P13 提前发现（只写"发现"，不写"已修好"）**：(1) 仓库自带的 C API 示例不可用——Makefile 仅适用于 macOS，且 `main.c` 用的是 P04 之前的 API 名字（三棵树编译均 rc=1）；(2) 公开 C API 能把 `examples/C_api/main.c` 的物理设定原样表达出来，且三棵树的 35 频点结果与 2015 年的 `spec.awk.out` 在预注册容差内一致（实际 max_abs=0），与 Lua 的同一结构结果相对差 ≤3.8e-15；(3) 本轮**没有**补齐或改写 `examples/C_api/`（U403 明确它只是提前检查）。

### 4.5 T5 主套件（只在 F4 上跑一遍）

`make test` rc=0，**unit_count=265**（4 个 shell/selftest 阶段 + 261 个 unittest 单元），无失败/错误行——与 S5R3/REL-R1 的 265 一致，**环境没有漂移**。U 的 Makefile 没有 `test` 目标，记 **U_UNAVAILABLE**。

## 5 差异归因（§5.3）

U vs F4 的 DIFF_ATTRIBUTED 共 **8** 个（T1 6 + T2 2）。全部逐个单元跑 U / M / M2 / M3 / B / F4 六棵树（M = `b97f639`；M2 = `963ccf1`，M 之后第一个改 `S4/` 的提交；M3 = `5cf534c`，采纳 D001/D002 修复 `44f4a09` 的提交），按同一套类别规则比较（`ATTRIB_RELR4.tsv`）：

| 单元 | U vs M | M vs M2 | M2 vs M3 | M3 vs B | B vs F4 | 来源 |
|---|---|---|---|---|---|---|
| T1 Antonoyiannakis fig3_4 | SAME | DIFF_ATTRIBUTED | SAME | SAME | SAME | M→M2：提交 **963ccf1** |
| T1 fabry_perot/fresnel | SAME | DIFF_ATTRIBUTED | SAME | SAME | SAME | 同上 |
| T1 fabry_perot/tir | SAME | DIFF_ATTRIBUTED | SAME | SAME | SAME | 同上 |
| T1 fabry_perot/tir_field | SAME | DIFF_ATTRIBUTED | SAME | SAME | SAME | 同上 |
| T1 magneto/halfspace | SAME | DIFF_ATTRIBUTED | SAME | SAME | SAME | 同上 |
| T1 simple/simple | SAME | DIFF_ATTRIBUTED | SAME | SAME | SAME | 同上 |
| T2 simple | SAME | DIFF_ATTRIBUTED | SAME | SAME | SAME | 同上 |
| T2 fresnel | SAME | DIFF_ATTRIBUTED | SAME | SAME | SAME | 同上 |

**来源提交**：差异在 **`963ccf1`**（"checkpoint: preserve 014RF limited offline evidence acceptance"，2026-10-03）首次出现；`963ccf1` 的说明明确写 "not D001/D002 closure"，`M..B` 之间对 `S4/` 的两次改动分别是 `963ccf1` 与 `5cf534c`，而 `M2(=963ccf1) vs M3(=5cf534c)` 在所有这些单元上 SAME —— 所以**不是** D001/D002 采纳（`5cf534c`）引入的，而是 `963ccf1` 所保留的 P04 `S4/`（含 `main_lua.c`/`main_python.c`/`rcwa.cpp`/`S4.cpp` 的大改）带来的输出变化。`B→F4` 全部 SAME（D003 在这些路径上确实不改输出）。
**任务书对 M 的描述**（"原版 + Lua/Python 前端修复，不含 D001/D002 物理修复"）与实测不完全一致：`b97f639` 只是早期 Python 3.14 绑定修复；体量最大的 `S4/` 改动（含前端重写）实际在 `963ccf1`。本轮按实测记录来源提交，不按任务书假设改写结论。

**差异形态**：这 8 个单元里 U（与 M）在若干分量上输出**精确的 0**而 F4 非零（例如 simple 的 below 层透射通量 U=0、F4=1；magneto/halfspace 的某些电场分量 U=0），最大相对差 1.0–1.999。没有独立参考的单元只记录"差异大小 + 来源提交"，**不判断谁对**。
**有独立参考的 T2 simple/fresnel**：对比 `testing/` 提交的参考数据，U、M 的 relmax=1.0，**M2、M3、B、F4 的 relmax=0** —— 即有参考的一侧，**F4 一方更接近参考**；但该参考数据本身就是 fork（P04 之后）产生的，因此这只说明 F4 与提交数据自洽，不等于独立物理验证。

## 6 判定类别计数

下列代码块是报告中的派生数字，end 门禁会逐项与源表（`SUMMARY_RELR4.txt`、`VERDICT_RELR4.tsv`，按列名读取）比对。

<!-- COUNTS:BEGIN -->
REGISTRY_ROWS=193
PREREG_UNITS=493
T1_U_VS_F4_SAME=27
T1_U_VS_F4_DIFF_WITHIN_TOL=3
T1_U_VS_F4_DIFF_ATTRIBUTED=6
T1_U_VS_F4_REGRESSION=0
T1_U_VS_F4_IMPROVED=2
T1_U_VS_F4_BOTH_FAIL=10
T1_U_VS_F4_FLAKY=1
T1_B_VS_F4_SAME=38
T1_B_VS_F4_BOTH_FAIL=11
ALL_U_VS_F4_SAME=33
ALL_U_VS_F4_DIFF_WITHIN_TOL=3
ALL_U_VS_F4_DIFF_ATTRIBUTED=8
ALL_U_VS_F4_REGRESSION=0
ALL_U_VS_F4_IMPROVED=2
ALL_U_VS_F4_BOTH_FAIL=10
ALL_U_VS_F4_FLAKY=1
UNIT_COUNT=265
PREREG_SHA256=90bb8884b7346857e29e22e1d3cc53aeff748bdddd0774240337ad1b02d939df
NON_REGRESSION_U=PASS
NON_REGRESSION_B=PASS
<!-- COUNTS:END -->

口径：`NON_REGRESSION_U=PASS` 表示 **REGRESSION=0 且 F4 无 FLAKY**（`FLAKY_U=1` 是 U 自身崩溃的部分输出差异，`FLAKY_F4=0`）；`NON_REGRESSION_B=PASS` 表示 B/F4 精确复现 REL-R1 的 38 SAME / 11 BOTH_FAIL。

## 7 任务书第 7 节逐条回答

### 7.1 原版能跑通的，当前是否全部能跑通？

**是（就"有效通过"而言）：REGRESSION = 0。** 逐项：
- **SAME 27**：U 与 F4 的 stdout/stderr/产物逐字节一致（归一化树路径后）。
- **DIFF_WITHIN_TOL 3**：两树都通过，差异 ≤ 预注册容差（slab_resonances 3.2e-13、Fan fig12 1.4e-13、interpolator 数值相同但非逐字节）。
- **DIFF_ATTRIBUTED 6**：两树都通过但超出容差，来源提交 `963ccf1`（P04 `S4/` consolidation checkpoint），不属于任何一方的"失败"。
- **IMPROVED 2**：Tikhodeev fig4、threading/parallel——U 段错误（rc=-11），F4 通过；U 的失败原因是 U 自身的崩溃（不是配置问题）。
- **BOTH_FAIL 10**：Christ fig2b（`GetRealMaterial` 在三棵树都不存在）、Li ex1_new/ex1_normal/ex1_orig（U SIGSEGV / F4 报 "singular interface system" 后 rc=1）、convergence/1d/binary_grating、cellA、cellB、ex2/fig2、resonance_pos/ref、magneto/slab（U 静默 rc=0 但有 Lua 错误，F4 rc=1）——都是两树同样失败的既有问题，不是本轮引入。
- **FLAKY 1**：Li ex2 仅在 U 上因"崩溃前 stdout 未刷新"导致两遍部分输出不同；不是数值不稳定，F4 两遍一致。
- 另外：U 自身还有 6 个示例 SIGSEGV、7 个示例"静默 rc=0 + Lua 错误"（有效失败），这些都不构成本轮 REGRESSION；
- **原版跑不通、当前能跑通的**（IMPROVED）：Tikhodeev fig4、threading/parallel，共 2 项。

### 7.2 原版自身不可用的能力（每项附证据）

1. **Python 接口**：U 的 `python3 setup.py build` rc=1，`PyInt_AsLong`（Python 2 API 已移除）；`gensetup.py.sh` rc=0 只是生成 setup.py。→ **U_PY_UNAVAILABLE**（`U_PY_RELR4.tsv`、`u_probe/u_py_setup_build.log`）。
2. **`GetAmplitudes`**：U 的 `S4/main_lua.c:2207` 把 `S4_LayerID`（int）传给期望 `S4_Layer*` 的 `Simulation_GetAmplitudes`，gcc 15 下是 `-Wint-conversion` 错误；U 不带 override 编译恰好 1 个 error（`U_PROBE_RELR4.tsv`）；fork 由 `93b1c90` 修复；**没有任何 example 调用它**（三树 51 个 lua，命中 0）。
3. **原版自带回归测试**：U 的 `testing/runtests.sh` 是 CRLF 行尾、在 `sh` 下语法错误 rc=2；`testing/testcases.txt` 的 10 个用例中 10 个参考文件全缺失、7/10 脚本路径不对；旧脚本把 `S4_BIN` 硬编码为 `../S4`。→ **U 自带测试不可运行**（`T2_U_OWN_MANIFEST`、`EXPECT_SCAN_RELR4.tsv`）。
4. **C API 示例**：`examples/C_api/Makefile` 是 macOS 专用（三树 rc=2）；`examples/C_api/main.c` 用 P04 之前的 API 名字（三树编译 rc=1）。注意：**U 的公开 C API 本身可用**——本轮新写的 C 程序在三棵树都构建成功（`CAPI_RELR4.tsv`）。
5. （附加发现）**U 的 Lua 前端退出码不可靠**：脚本出错仍 rc=0（§1、ERRATA ER4-1）——这是 U 不可用的"能力"之一，也是本轮必须用"有效通过"口径的原因。

### 7.3 MPI

见 §4.3：三棵树都构建出带 "With MPI support" 的 `build/S4mpi`，24/24 次 `mpirun` 运行成功；多进程（`-np 4` 合并）与单进程、以及与非 MPI 版单进程参考的一致性判据 **12/12 PASS**（22 个完全相同 double 频点最大相对差 0）；B/F4 同名输出逐字节一致；U vs F4 也逐字节一致。覆盖率与"按打印文本错配"的观测值按要求只记录、不判失败（ER4-2）。

### 7.4 C API

见 §4.4：与 `spec.awk.out` 的偏差为 **0 行超容差、max_abs=0**（三棵树）；与 Lua 的阳性对照 max rel **3.796e-15**（≪1e-10，三棵树）；B 与 F4、U 与 F4 的输出均逐字节一致。P13 的提前发现见 §4.4 末尾：原示例不可用（Makefile/旧 API 名），公开 API 可用且与 2015 参考/ Lua 结构一致；**只写"发现"，本轮没有修 P13**。

### 7.5 口径与局限

1. **没有独立参考的 example 只能写"与原版一致 / 与原版有差异、来源是某个提交"**，不能说物理正确；本报告对所有 T1 单元都遵守此口径。
2. 有独立参考的只有 T2 的 3 例（且参考数据是 fork 在 P04 之后提交的）和 T4 的 2015 `spec.awk.out`（`%g` 6 位有效数字，预注册容差 5e-6 相对 + 1e-6 绝对）；T4 实际偏差为 0，因此也不需要 `REF_DRIFT` 判定。
3. U 的判定依赖"有效通过"口径（ER4-1）；如果只看 rc，U 会把 7 个既有失败误报为通过。
4. 环境局限：只能在本机（Linux/gcc 15.2/LAPACK 3.12.1/Lua 5.2.4/Python 3.14.4/OpenMPI）复现；U 的 Python 接口与自带回归测试在本机不可用（§7.2）；U 的克隆是网络只读克隆，HEAD 与主仓库中的 `7fd00a2` 对象一致。
5. 中间树 M/M2/M3 的构建只是为了归因，不是"P05 的验证树"；它们的 S4 树哈希记录在 `ATTRIB_RELR4.tsv`。
6. T3 的"相同频率"按 IEEE double 完全相同定义（ER4-2）；覆盖率 23/90 是数据本身的限制（Lua 数值 for 的累积方式），不是漏测。

### 7.6 结论与交付状态

按任务书 §7.6：**本轮已完成 REL-R4 范围，等待用户审核**（正式 end 门禁结果与 `git log -1` / `git status --short` 见附录 C，门禁后只追加）。

## 8 违规披露（两张表）

### 表一 越界写入尝试（命令自身写了仓库外路径，即使被拒绝/未落盘）

| 轮次 | 命令 | 是否落盘 |
|---|---|---|
| rel-r4 | 无 | — |

本轮执行者的所有含写入命令都经 `sh testing/d003/safe_run.sh p05-rel-r4 -- …` 运行，写入目标限于 `$EV/`、`$REPO/testing/d003/`、`$REPO/checkpoints/p05/`；没有出现 `/tmp` 或任何仓库外绝对写入目标。

### 表二 工具/脚本事件

| 轮次 | 事件 | 是否落盘 | 说明 |
|---|---|---|---|
| rel-r4 | 开局门禁 `GATE_RELR4_start.txt` 被 relr4_check.py --phase start 的默认 `--out` 覆盖一次 | 是（同日重新生成） | 见 ERRATA ER4-4；覆盖前的首跑文件保留为 `GATE_RELR4_start_firstrun.txt`（sha256 `f3ae4252…`），check 的 start 相默认输出改为 `GATE_RELR4_check_start.txt`，并用 relr4_startgate.py 重新生成同名开局门禁文件；所有核对哈希都是不可变 git 对象，/tmp 快照前后一致 |
| rel-r4 | relr4_startgate.py 首跑检查器笔误（rel-r3 registry 条数写死 16，实际 18）→ FAILS=1 | 是（保留首跑） | 见 ERRATA ER4-5；更正期望条数后重跑 FAILS=0；数据未改 |
| rel-r4 | 新增脚本、证据表与报告由 agent 的文件写入工具创建 | 是 | 目标都在 `testing/d003/stage_relr4/` 与 `checkpoints/p05/`（含 evidence 目录）内；已有装置未改；一次误生成的 `testing/d003/stage_relr4/__pycache__/` 已当场用 safe_run 删除（未提交） |
| rel-r4 | U 的 Python 尝试由项目自带 `gensetup.py.sh` 在 U 克隆内生成 `setup.py` 与 `build/` | 是（在 `$EV/upstream/S4` 内，证据克隆不提交） | 项目自身生成器行为；`U_PY_RELR4.tsv` 记录了 `git status --porcelain` 的 `?? build/`、`?? setup.py` |
| rel-r4 | OpenMPI/PMIx 在 `$EV/tmp` 建会话目录 `ompi.*`；examples 的 `S4_malloc` 临时目录也落在 `$EV/tmp` | 是（都在 `$EV/tmp`，仓库内） | 工具/框架事件，非执行者违规；未写 `/tmp` 或仓库外路径；`/dev/shm` 顶层为空 |
| rel-r4 | 门禁 `safe_run.log` 随每次调用追加 | 是 | 故不纳入 `SHA256SUMS.txt` 的静态清单（清单头部注明） |
| rel-r4 | framework 的 `/tmp/dsh-spill-*` 类落盘 | 否（未观察到） | 本轮长输出都用 tail/head 限制；`/tmp` 顶层快照开始/结束均为 0 项且 sha 相同 |

## 9 证据与清单位置

- 证据目录：`checkpoints/p05/evidence/p05-rel-r4/`（含 `SHA256SUMS.txt`；U 克隆 `upstream/S4` 与 B/F4/M/M2/M3 克隆 `trees/`、运行 cwd `run/`、`mpi/`、`capi/` 均不提交，克隆与二进制只记哈希）。
- 小表：`checkpoints/p05/registries/rel-r4/`（含 `SHA256SUMS.txt`）。
- 裁决：`checkpoints/p05/registries/RULINGS.tsv` 追加 U399–U403（旧前缀 sha 不变，见 `RULINGS_APPEND_RELR4.tsv`）。
- 勘误：`ERRATA_RELR4.txt`（ER4-1…ER4-5，均在 493 个预注册单元与容差不改的前提下记录口径/执行事件）。

正式 end 门禁结果见附录 C（门禁后追加）。