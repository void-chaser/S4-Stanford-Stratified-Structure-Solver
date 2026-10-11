# P05-S3R2 收尾报告：S3 补充子任务（D-J / D-D / D-N / D-K / D-138）

> **状态：未完成，等待用户审核。** 本报告不宣布 P05-S1、P05-S2、P05-S3、P05-S4 任一阶段完成。本轮所有结果称"开发检查"或"探针观察"，不称"验证"。验证属于 P05-S4。

## 1. 状态与定位

- 本轮是正式阶段 **P05-S3**（最小修复）的第二个补充子任务，不是新阶段。P05 固定五阶段 S1–S5，本轮未引入 S6。
- 阶段定义依据用户给出的提示词（仓库内无原始计划文档，本轮未搜索原文）。
- 起点：HEAD `d262520`（S1R2 收尾）；分支 `codex/p05-d003-fft-error-propagation`；工作区开工时干净。
- 本轮完成：三个源码提交（D016、R-NV-1、K-1）；D-138 的几何后果实测（结论 B，未改源码）；七处 info=NULL 的 seam 不可测（R2-2b，未证明）；R2-4 的正常路径、D016、K-1 检查；范围外草稿；复现包。
- 未完成或未证明：七处 info=NULL 的修前→修后运行对照（R2-4d）；D016 的公共异常文本（仅源码映射，未经 Python 实测）；张量路径 K-1 覆盖；其它见第 6 节。

## 2. 提交表

| 顺序 | 提交 | 内容 | 文件 | 说明 |
|---|---|---|---|---|
| 1 | `3e77aa9` | `fix(p05): D016 zero-field error at root cause (P05-S3R2 commit 1, awaiting user review)` | `S4/pattern/pattern.c`（+6） | 返回 −10；−9 已被 `pattern_discretize_cell` 占用，未复用 |
| 2 | `44bcf1c` | `fix(p05): NV checks pattern error before normalization (P05-S3R2 commit 2, awaiting user review)` | `S4/fmm/fmm_PolBasisNV.cpp`（+10 含 2 行注释，−8） | 仅调整位置，正常路径语句顺序不变 |
| 3 | `ff6dd7c` | `fix(p05): kottke rejects non-finite Epsilon2 before eigen-solve (P05-S3R2 commit 3, awaiting user review)` | `S4/fmm/fmm_kottke.cpp`（+9） | 求解前检查 Epsilon2 与 Epsilon_inv 有限性；无阈值；`SetMaterial` 未改 |
| 4 | `a6cd0a2` | `test(p05): S3R2 probes, comparison scripts and README under testing/d003/stage_s3r2 (awaiting user review)` | `testing/d003/stage_s3r2/`（12 个文件，+616） | 探针与比较脚本 |
| 5 | 本报告的文档提交 | `docs(p05): S3R2 closeout, registries/s3r2, MANIFEST and digest (awaiting user review)` | 报告、期望与结果文件（证据目录外的已提交部分）、`registries/s3r2/`（25 个文件）、`MANIFEST.tsv`（+25）、`S1_evidence_digest.txt`（+22） | 见第 9 节 |

- S4 改动（相对 `35cd7b3`）：3 个文件，共 25 行新增、8 行删除；越界 S4 路径数 0。
- 三个源码提交各自做了干净导出构建（`git archive` 后 `make`），警告多重集与前一状态逐行比较（`LC_ALL=C sort` 后 `comm -3`）：差异 0（71 行对 71 行）。编译错误 0。
- CRLF：三个源码文件编辑后逐一核对，CR 数等于行数，无纯 LF 行。

## 3. 各裁决项的执行结果

### 3.1 D-J：Jones 舍入序（接受 `df3bb02` 的 info 传递；Jones 用逐元素相对差 ≤ 1e-10）

- 结果（[实测]）：`start`（35cd7b3）与 `new`（ff6dd7c）的 Jones 与 fftjones 共 24 个用例、48 个场转储，**逐字节相同**。
  - 实际最大相对差：**0**；实际中位相对差：**0**；超过 1e-10 的值：**0**；非有限对：0。
  - 数据：`R2-4a_jones_numeric.tsv`；汇总方法见第 4.3 节与表二第 10 行。
- 参考（[实测]，不作为本轮判据）：`base`（37a82e8）与 `start`（35cd7b3）的 Jones 与 fftjones 的 pattern 栈用例（12 个中的 6 个，dump1 有差异）存在舍入级差异；`jones-pattern-s-nb9` 的最大相对差 **1.04e-12**（中位 2.9e-14），与 S3R 6.3 的 1.18e-12 同量级。该差异属于 S2R/S3R 的既有修改，与本轮无关。
- 注：`base`→`start` 的 fftnv、fftvl 的 pattern 栈用例（各 6 个）也有舍入级差异，最大 2.26e-11（`fftvl`）与 1.14e-11（`fftnv`），中位 1e-14 量级。这与 S3R 6.3 的"NV、VL 全部一致"的表述不同：该表述只适用于纯 NV、纯 VL 模式（各 12 个用例，base→start 差异为 0）。**本轮修正该叙述**（见第 5.4 节）。
- 结论：D-J 的容差在本矩阵上满足（且本矩阵的实际差异为 0，比容差严格）。

### 3.2 D-D：D016（pattern.c，`max_field` 检查，返回 −10）

- 改动：`S4/pattern/pattern.c` 第 2145 行 `max_field = 1./max_field;` 之前加入 `if(!(max_field > 0) || !isfinite(max_field)){ return -10; }`。不新增公共错误码。
- 核对 −9：`pattern.c:1066` 的 `return -9` 属于 `pattern_discretize_cell`，仍然占用；本改动未复用。
- 调用方（静态走查，[源码]）：VL、Jones、NV 的 `if(0 != error)` 路径释放 `vfield`、`work`、`ivalues`（各带 NULL 检查）后返回 `error`，故 −10 经既有路径返回；无双重释放、无泄漏。`ComputeLayerModes` 的 `if(0 != fmm_ret)` 将其映射为 20（`S4.cpp` 2413–2416）。
- 实测（[实测]，`R2-4bc_SUMMARY.txt` 与 `R2-4b_runs/`）：
  - 新树 VL n_G=1：`pattern_generate_flow_field` 返回 **−10**（两次，含重试），`SolveLayerEigensystem` 调用 **0** 次。
  - 修前树（start、base、以及 S1R2 的 A、B 驱动）VL n_G=1：返回 **0**（无检查），求解调用 **4** 次。
  - 驱动级 rc：修前 20，修后 **20**（不变）；进程退出码均为 1（驱动检查失败，属预期；判定不以此为准）。
  - TRACE（`ENABLE_S4_TRACE` 构建，精确字符串计数）：修前 `SolveLayerEigensystem returned 2)` 出现 2 次；修后 **0** 次（info=2 的 TRACE 消失）。修后出现 `Pattern_GenerateFlowField returned -10` 2 次。
  - 正常路径不误拦截：VL、Jones、NV 在 NG = 5、6、7、8、9 上 `pattern_generate_flow_field` 均返回 **0**，求解调用 2 次（`R2-4bc_SUMMARY.txt`）。
- 公共异常文本：驱动不经 Python，未观测。源码映射（[源码]，`main_python.c` 137 行）：码 20 的文本为 "The layer eigensystem could not be solved; no solution was returned"。**[推断] 修后异常文本不变**，未经 Python 实测。
- 三树（A、H、B）的 D016：A 与 B 为修前树，不含 D016（期望 D16-2 的修后行为未运行；修前行为见上）。H 树（64eb0b5）未在本轮导出，修前行为见 S1R2 J6_NG1（返回 0）。

### 3.3 D-N：R-NV-1（NV 先检查 error，再归一化）

- 改动：`fmm_PolBasisNV.cpp` 中把 `if(0 != error){...return error;}` 块移到归一化循环之前（另加 2 行注释）。代码语句未改，只改位置（diff 核对：删除 8 行代码与新增 8 行代码逐行相同）。
- 正常路径字节一致（R2-4a，[实测]）：纯 NV 的 12 个用例（NB ∈ {5, 9}，s/p/mix，pattern 与 flat 两栈）中，new 与 start 的 dump1 与 dump2 全部逐字节相同。fftnv 的 12 个用例同样在 new 与 start 之间逐字节相同（R2-4a 的 108 个非 Jones 用例全部一致）。
- error 路径：D016 修改后 NV 的 NG = 1 在 pattern.c 处返回 −10（`R2-4b`：NV NG=1 的 `pattern_generate_flow_field` 返回 0，因 max_field 非零，故 NV 的 error 路径在本轮未被触发；**error 路径的顺序变化未经运行验证**，见第 6 节）。
- 结论：正常路径输出不变（实测）；error 路径的读取顺序修正为静态结论（[源码]）。

### 3.4 D-K：K-1（kottke 在求解前检查 Epsilon2 与 Epsilon_inv 有限性，失败返回 1 → 经 ComputeLayerModes 为 20）

- 改动：`fmm_kottke.cpp` 中，w 循环写完 Epsilon2 的四个块之后、`cleanup:` 之前，检查 `Epsilon2`（n2×n2）与 `Epsilon_inv`（n×n）的实部与虚部；非有限则 `ret = 1; goto cleanup;`。无 eps 阈值；`SetMaterial` 未改。
- 静态走查（[源码]）：`cleanup` 释放 `plans[0..4]`（`fft_plan_destroy` 对 NULL 安全，`fft_iface.cpp` 136 行）、`discval`、`work`，各一次；检查只在 `discval` 与 `work` 分配成功之后才可达。无双重释放、无泄漏。
- 实测（[实测]，`R2-4bc_SUMMARY.txt`）：

| eps | start（修前）退出码 | new（修后）退出码 | new 的 RC first / retry | 场（修前对修后） |
|---|---|---|---|---|
| 0 | **139**（SIGSEGV，无 RC 行） | 0 | **20 / 20** | 未写入（哨兵值） |
| 1e-300 | **139** | 0 | **20 / 20** | 未写入 |
| 1e-100 | 0 | 0 | 0 / 0 | **逐字节相同**（144 行） |
| 4 | 0 | 0 | 0 / 0 | **逐字节相同**（144 行） |

- 说明：探针进程的退出码（0 或 139）只是记录，判定依据是 rc（20、0）与场数据。
- 结论：K-1 把 kottke 的非有限中间值在求解器之前拦截，失败经既有路径返回 rc 20；正常值（eps=1e-100、eps=4）不被误拦截，场逐字节一致。

### 3.5 D-138：fmm_FFT.cpp 第 138 行的下标（先实测，默认不改源码）

- 结论：**B 类（无数值差异）。** 不修改 `fmm_FFT.cpp`。
- 证据（[实测]与[源码]）：
  - 源码（[源码]）：`fmm_FFT.cpp` 中 `nvec` 只出现在第 132 行（声明）与第 138 行（输出参数），之后无读取；第 140–171 行的面积加权块不使用 `nvec`。
  - 实测：双形状 bigoverlap 布局（两圆半径 0.8，中心 ±0.3，fft 模式）。`shape_get_normal` 共 20 次调用；原版使用下标 0 与 1，受限对照（`imat[0]>=1` 时取 `imat[0]-1`）只用下标 0。**9 次调用的返回法向不同，最大夹角 49.635°**（`R2-1_runs/nvec-compare.txt`）。
  - 实测：Epsilon2、Epsilon_inv 在 FFT 返回处的转储 **逐字节相同**（`cmp IDENTICAL`，sha256 相同；`R2-1_runs/dump-*/`）；场 144 个值文本相同（`compare-bigoverlap.txt`）。
  - 回溯（[实测]）：fft 模式下调用者为 `FMMGetEpsilon_FFT`，即 D-138 所在路径确实执行。
- 期望与修正（运行前，均已固定，均标注 INFLUENCED）：
  - `R2-1_D138_EXPECTATIONS.txt`（12:51:43Z，`8d975e16…`）：原始期望，未修改。
  - `R2-1_D138_AMENDMENT_1.txt`（12:52:54Z，`ffff99bd…`）：因源码阅读发现 `imat[0]=0` 时对照会取 `shapes[-1]`（越界），改为受限形式，并改用双形状探针。
  - 第一次 overlap 运行（运行后，记录为事实）：只观测到下标 0，未覆盖 `imat[0]>=1`。
  - `R2-1_D138_AMENDMENT_2.txt`（12:54:18Z，`9fc84153…`）：布局改为 bigoverlap。
- 修正的 S1R2 叙述（见第 5.4 节）：S1R2 J3 把第 138 行差一归属为"可能影响 kottke 法线"。核对：kottke 的 `shape_get_normal` 调用在 `fmm_kottke.cpp` 第 148 行，已使用 `imat[0]-1`，与约定一致，不存在该差一。S1R2 观测到的下标 1 来自 kottke 之外的调用（当时用的是 kottke 模式，其调用为 `imat[0]-1`，下标 1 对应 `imat[0]=2`）。**差一的位置在 FFT（第 138 行），不在 kottke。**

## 4. R2-4 对照表

### 4.1 正常路径（R2-4a）

| 用例族 | 用例数 | new 对 start（dump1 与 dump2） | 判据 | 结果 |
|---|---|---|---|---|
| 非 Jones：fft、kottke、nv、vl、fftnv、fftvl、closed2d、experimental、tensor | 108 | 逐字节相同 | 字节一致 | **通过**（108/108，两个转储） |
| Jones、fftjones | 24 | 逐字节相同 | D-J ≤ 1e-10 | **通过**；实际最大相对差 **0**，中位 **0** |
| 驱动检查失败（tensor、flat 栈，18 用例）| 18 | 三树相同（含 NaN，字节相同） | 字节一致 | 既有行为：驱动的 "successful output is finite" 检查在三树均失败；rc 为 0；这些用例的场含 NaN，非正常基准（见第 6 节） |

- 运行规模：11 模式 × 2 栈 × 3 偏振 × 2 NB = 132 用例，每用例三树，共 396 条进程记录（`R2-4a_runs/*.proc`，即 132 × 3）。另有 1 个烟测输出（`smoke-base.out`），故 `RC first` 行共 397 条。全部 `RC first 0`、`RC retry 0`。
- 运行时间：矩阵由后台作业 `bash-3157` 执行，`.proc` 文件的修改时间自 13:04:29 至 13:04:32 UTC（由文件时间得到，精度为秒）。
- 停止规则：未触发（非 Jones 的字节差异为 0）。

### 4.2 D016 与 K-1 的对照

| 检查 | 修前（start 或 base） | 修后（new） | 判据与结论 |
|---|---|---|---|
| D16：VL n_G=1，`pattern_generate_flow_field` 返回码 | 0（无检查） | **−10** | 在根因处报错 ✓ |
| D16：VL n_G=1，`SolveLayerEigensystem` 调用 | 4 | **0** | 失败前移，未进入求解 ✓ |
| D16：VL n_G=1，驱动 rc | 20 | **20** | 不变 ✓ |
| D16：info=2 TRACE（精确字符串） | 2 | **0** | 消失 ✓（需 TRACE 构建） |
| D16：Jones、NV NG=1 | — | 返回 0，求解 2 次 | 不误拦截 ✓ |
| D16：VL、Jones、NV，NG=5–9 | — | 返回 0，求解 2 次 | 不误拦截 ✓（停止规则未触发） |
| K1：eps=0 | 退出 139 | rc 20 / 20 | 失败且不崩溃 ✓ |
| K1：eps=1e-300 | 退出 139 | rc 20 / 20 | 同上 ✓ |
| K1：eps=1e-100 | rc 0 | rc 0；场逐字节相同 | 不误拦截 ✓ |
| K1：eps=4 | rc 0 | rc 0；场逐字节相同 | 不误拦截 ✓ |
| R-NV-1：NV 正常路径 | — | 36 用例逐字节相同 | 不改变正常输出 ✓ |
| 七处 info=NULL：修前红→修后绿 | 无法运行（R2-2b） | 静态核对：无 NULL-info 调用；各检查存在 | **未证明**（[未验证]） |

### 4.3 对照表中的数字来源

- 矩阵：`R2-4a_summary.tsv`（132 行）、`R2-4a_jones_numeric.tsv`（48 行）、`R2-4a_runs/*.proc`（396 个）。
- D016 与 K-1：`R2-4bc_SUMMARY.txt`，原始输出在 `R2-4b_runs/`、`trace-drv/`、`R2-4c_runs/`。
- D-138：`R2-1_RESULT.txt`、`R2-1_runs/nvec-compare.txt`、`R2-1_runs/compare-bigoverlap.txt`、`R2-1_runs/SHA256SUMS_R2-1.txt`。

## 5. 偏离与违规

### 5.1 偏离（运行前后、期望与顺序）

| # | 内容 | 时点 | 处理与披露 |
|---|---|---|---|
| D1 | `REGISTRY_S3R2_PRE.tsv` 的固定（记录为 12:58:31Z）晚于 R2-1 的 bigoverlap 运行（rc 文件修改时间约 12:54:30Z，nvec 运行约 12:55:34Z）。该表不满足"先于任何运行"的字面要求。 | 运行后固定 | 其中 D138 组以 R2-1 的前置期望文件（12:51:43Z）与修正 1（12:52:54Z）、修正 2（12:54:18Z）为准；其余组（D016、K-1、RNV、Jones）的运行发生在该表固定之后，但其判定规则在表中已写明。INFLUENCED 标注保留。 |
| D2 | R2-1 的期望修正 1 与 2（`AMENDMENT_1`、`AMENDMENT_2`）。修正 1 在运行前由源码阅读触发；修正 2 在第一次 overlap 运行之后由 gdb 计数触发。 | 1：运行前；2：运行后 | 均固定哈希、标注 INFLUENCED；原期望文件未修改。 |
| D3 | R2-4a 的 `R2-4a_MATRIX_EXPECTATIONS.txt` 固定于 13:04:00Z（记录），早于矩阵运行（`.proc` 修改时间自 13:04:29Z 起）。 | 运行前 | 无偏离。 |
| D4 | `DRIVER_PIN.sha256` 与 `R2-4a_MATRIX_EXPECTATIONS` 中 E-A1 的 base 与 start 比较：E-A1 的判据是 new 与 start 字节一致（已满足）。base 与 start 的差异（fftnv、fftvl、Jones）按期望"参考，列出"处理。 | 运行后 | 披露：base→start 的差异存在（见 5.3）。 |
| D5 | R2-2b 的 seam 未构建（不可测）。 | — | 按规则记录，不改锚点语义。 |

### 5.2 表一：越界写入尝试（延续 S1R2 编号，本轮从第 10 行起）

命令自身把仓库外路径作为写入目标的记录（无论是否落盘）。

| # | 轮次 | 完整命令（要点） | 是否落盘 | 如何核实 |
|---|---|---|---|---|
| 10 | S3R2 / R2-4a 比较（第一次） | `sh testing/d003/safe_run.sh p05-s3r2 -- sh "$2/testing/d003/stage_s3r2/r4a_compare.sh" "$1/R2-4a_runs" "$1/R2-4a_summary.tsv" 2>/dev/null` 中 `$1` 在外层展开为空，目标变为 `/R2-4a_summary.tsv` | **否**（`wc` 报 `No such file`） | `test -e /R2-4a_runs` 与 `test -e /R2-4a_summary.tsv`：均 absent |
| 11 | S3R2 / R2-4a 脚本修改后 | `sh -c '...' ... > "/tmp_nonexist_placeholder"`（在统计 NV 的 diff 多重集时误加重定向） | **否**（`Read-only file system`） | `test -e /tmp_nonexist_placeholder`：absent |
| 12 | S3R2 / R2-1 对照副本构建前 | `sed -n ...` 之后的 `cat -n | sed ...` 中算术替换写错，但该命令含 `> "$REPO/.../tmp/closed_A.cpp"`（路径在仓库内，但命令未经 safe_run，且 `2>/dev/null` 用于隐藏 stderr） | 落盘于仓库内证据目录（合规路径，但命令形式违规；列入表二） | 表一不计（目标在仓库内）；见表二第 6 行 |

说明：第 10、11 行的目标是根目录路径，属于真正的越界写入尝试（自身写仓库外路径，未落盘）。第 12 行目标在仓库内，故归入表二。

### 5.3 表二：工具与脚本事件

| # | 轮次 | 现象 | 是否涉及仓库外写入 | 处理 |
|---|---|---|---|---|
| 1 | 门禁 | 无 | 否 | — |
| 2 | R2-1 | 转储运行漏掉 `D138_OUT` 环境变量，探针报 ARGERROR，gdb 因无寄存器失败 | 否 | 补传变量重跑 |
| 3 | R2-1 | 差一的对照副本在 `imat[0]=0` 时取 `shapes[-1]`（设计错误，在运行前由源码阅读发现） | 否 | 写入 AMENDMENT_1，改为受限形式 |
| 4 | R2-1 | 第一次 overlap 布局未覆盖 `imat[0]>=1`，结论不能判 B | 否 | 写入 AMENDMENT_2（INFLUENCED），改布局 |
| 5 | R2-2b | `gdb_d138_nvec.gdb` 初版用单个 ret 断点；`shape_get_normal` 有 5 个 ret | 否 | 改为 5 个断点，并核对无尾调用 |
| 6 | R2-2b | `2>/dev/null` 用于一条含写入的命令（生成 `closed_A.cpp` 前的尝试），违反规则第 5 条；该命令同时含算术替换错误 | 否（仓库内目标） | 改用 safe_run 重做；披露 |
| 7 | R2-2b | 通过 `&`（shell 后台）启动矩阵，进程未留下作业记录；`ps` 确认无遗留进程 | 否 | 改为正式后台作业 `bash-3157` |
| 8 | R2-4a | 比较命令的 `$1` 外层展开为空（见表一第 10 行） | 是（未落盘，表一） | 改为 `sh -c` 内部显式传参 |
| 9 | R2-4a | `2>/dev/null` 用于一条比较命令（违反规则第 5 条） | 否 | 披露；后续改用 safe_run 且不隐藏 stderr |
| 10 | R2-4a | 汇总 Jones 的脚本把多行输出用 `tr` 拼接，字段解析错误，得到错误的"文本不同 48"计数 | 否 | 改为对第三字段按空格拆分重算；结果与 `rel_diff.py` 的原始输出一致 |
| 11 | R2-4b | TRACE 计数：模式 `returned 2` 与 `returned 2 ` 与 `returned 2)` 三次不精确计数，前两次给出错误数字（8、6） | 否 | 改用精确字符串 `SolveLayerEigensystem returned 2)`，结果 start 2、new 0 |
| 12 | R2-3 | `grep -c` 检查 `-10` 时把 `fffffff6` 作为立即数匹配，结论正确（用于确认分支存在） | 否 | 无 |
| 13 | R2-3 | `edit` 工具首次拒绝（"file has not been read"），读取后重试成功 | 否 | 先读后写 |
| 14 | R2-3 | 为核对 NV 的纯重排，曾用写入根目录占位文件的方式比较多重集（见表一第 11 行） | 是（未落盘，表一） | 改用管道与 diff 输出 |
| 15 | R2-3 | 自比较的错误检查（`S4_diff_vs_head_of_tree` 比较同一路径）被误作证据，已在下一步改用两棵不同树的真实比较 | 否 | 披露；以真实比较替代 |
| 16 | R2-5 | `README.md` 的文件表初版缺 5 个文件 | 否 | 补入 |
| 17 | 框架 | 长输出（gdb 反汇编、矩阵日志）经文件重定向写入证据目录，stdout 用 head/tail 限制；未观察到 `/tmp/dsh-spill-*` 落盘 | 否（未观察到） | 披露；本项是"未观察到"，不是"未发生" |
| 18 | 权限 | `chmod +x testing/d003/stage_s3r2/r4a_run.sh` 未经 safe_run（元数据修改，目标在仓库内） | 否 | 披露 |

### 5.4 与 S1R2 叙述的新旧对照

| 位置 | 旧叙述（S1R2 或 S3R） | 新事实（S3R2） | 处理 |
|---|---|---|---|
| S1R2 J3（差一） | 第 138 行差一"可能影响 kottke 法线" | 第 138 行在 FFT 路径；kottke 的对应调用（148 行）已是 `imat[0]-1`；差一对 FFT 输出无数值后果（D-138 B 类） | 本报告更正；不改写 S1R2 原文 |
| S3R 6.3 | "NV、VL 及其余控制全部一致" | 纯 nv、纯 vl、fft、kottke、closed2d、experimental、tensor 的 base→start 全部一致；fftnv、fftvl（pattern）有舍入级差异（最大 2.3e-11） | 本报告更正；S3R 原文不改 |
| S3R 7（七处不可测） | "13、14 两处的 solve+检查对完全相同，无法唯一定位" | 在修前 closed 源码中 13/14 的 call 文本各出现 2 次，可由后续行区分；在 HEAD 中 "call+检查" 对相同。严格地说，"仅凭 solve+检查对无法唯一定位"成立，"无法唯一定位"需限定 | 本报告限定；不改写 S3R 原文 |
| S3R 第 219 行（"未提交改动 apply_seam_r2.py"） | 工作区有未提交改动 | HEAD 时 `apply_seam_r2.py` 与 HEAD 一致，无未提交改动 | 本报告披露：该改动已不在工作区（不知来源，见第 6 节） |

## 6. 仍未闭合缺口

1. **七处 info=NULL 的修前→修后运行对照（R2-4d）未证明**。原因：修前树无 solve_info 变量，且 13/14 锚点不能不改语义地唯一定位（R2-2b）。修后仅有静态存在性（[源码]）。
2. **D016 的公共异常文本**未经 Python 实测（[推断]：与修前相同）。需要 Python 扩展构建（在导出副本中），本轮未做。
3. **D016 的 error 路径在 NV 上未运行验证**：NV 的 NG=1 max_field 非零，未触发 −10；NV error 路径的顺序变化只有静态结论（[源码]）。
4. **K-1 的张量路径未证明**：`kottke` 的 Epsilon2 检查覆盖标量材料的探针，张量（`abcde` 的 D7 除数）只测了一个非正定点（S1R2 P2-B，正常返回）。
5. **R2-4a 的 18 个 tensor-flat 用例**：驱动的 "successful output is finite" 检查在三树失败，场含 NaN。它们作为"字节一致"的证据效力弱，应在 S4 另立正常基准。
6. **base→start 的既有差异**（fftnv、fftvl、jones、fftjones 的 pattern 栈，舍入级）：属于 S2R/S3R 修改，本轮不处理；S3R 6.3 的叙述已更正（5.4）。
7. **D-138 的 B 类结论适用范围**：只测了 fft 模式、双形状（bigoverlap）、标量材料与 NB=9。nshapes ≥ 3、张量材料、其它布局未测。B 类的理由（nvec 为死值）与几何无关，但未经全部覆盖的实测证实。
8. **D-138 的 kottke 路径**：第 148 行已是 `imat[0]-1`，本轮未审计 kottke 的其它 `imat` 下标用法（`fmm_kottke.cpp` 第 161 行 `shapes[imat[i]-1]`）。
9. **未运行的 H 树（64eb0b5）D016 对照**：D16 的修前对照使用 start 与 S1R2 的 A、B 驱动；H 树的 VL NG=1 行为来自 S1R2 J6_NG1（返回 0）。
10. **未核对的 `ComputeLayerModes` 其它失败分支**（例如 `S4.cpp` 2426、2440、2451 的 rwork/work 分配失败）：本轮未修改，也未测。
11. **范围外登记草稿（`R2-5_OUT_OF_SCOPE_DRAFT.txt`）**：8 条草稿，均未核对完整性；S5 复核。
12. **digest 与 MANIFEST 的 S1R2 段落**：未改动。
13. **`apply_seam_r2.py` 的未提交改动（已不存在，去向未查明）**：S3R 第 219 行记录该文件有"未提交的工作改动（family B 锚点，未完成）"。本轮核对：该文件与 HEAD 一致；`git stash list` 为空；该文件最近的提交为 `f5cae24`（S2R2 收尾装置）。因此 S3R 所述的未提交改动既不在工作区、也不在 stash、也没有对应提交。去向未查明（可能在 S3R 之后被覆盖或丢弃，本轮无法证明）。它不影响本轮的任何结论（本轮未使用该文件的 family B 模式）。

## 7. 已知限制（用户决定，来源标注）

沿用 S1R2 第 5 节的用户决定（不重复修改）：驱动二进制不可复现（注入器修订不同）、历史 38 案分类重放、S2R2 与 R2-D 的步骤独立、违规表第 1 行定稿、新尺子只用于核对类别。

本轮新增的限制（[实测] 与 [源码] 的边界）：
- 驱动 `driver-base`、`driver-start`、`driver-new` 的哈希由本轮构建并固定（`DRIVER_PIN.sha256`），不与历史驱动比较。
- 本轮的 D-138 与 K-1 的 gdb 偏移（ret 偏移）按每棵树的反汇编取得，未手填；偏移随代码改变，复现时必须重新取值。
- TRACE 的 info=2 核对需要 `ENABLE_S4_TRACE` 构建；默认构建中该文本不输出。

## 8. 对 P05-S4 的输入

### 8.1 被测点清单（本轮）

| 点 | 修改 | S4 应验证的内容 |
|---|---|---|
| `pattern.c` 的 `pattern_generate_flow_field`（max_field 检查） | D016，返回 −10 | VL、Jones、NV 在 NG = 1–9 的零场与非零场；公共异常文本的 Python 实测；与 H 树的对照 |
| `fmm_PolBasisNV.cpp` 的 error 检查位置 | R-NV-1 | NV 的 error 路径（需要能触发 error 的输入，本轮未找到） |
| `fmm_kottke.cpp` 的求解前有限性检查 | K-1 | 标量 eps 的大动态范围与零值；张量路径（D7）的可达性；场逐字节比较的正常基准 |
| `fmm_FFT.cpp` 第 138 行 | D-138（未改） | 决定是否修正下标（B 类，默认不改） |
| 七处 info=NULL（修前 closed 4、Jones、NV、VL） | 修后已改为 `&solve_info` 并带检查（HEAD 静态核对） | 修前红→修后绿的运行对照（需要可用的 seam，本轮不可测） |

### 8.2 冻结 HEAD 候选

- 候选 HEAD：本报告文档提交之后的 HEAD（commit 1–3 为 S3R2 源码提交：`3e77aa9`、`44bcf1c`、`ff6dd7c`；之后为测试与文档提交）。
- 源码范围：相对 `35cd7b3` 为 3 个 S4 文件（`pattern.c`、`fmm_PolBasisNV.cpp`、`fmm_kottke.cpp`）。

### 8.3 需要注意的不可达点与限制

- 驱动的 pattern 栈为单形状，`nnz >= 2` 时只产生 `imat[0] = 0` 的界面；D-138 的 `imat[0] >= 1` 需要双形状探针（已在本轮做）。
- VL、Jones、NV 的 NG = 1 在 pattern 栈上：VL 为零场（D016 触发），Jones 与 NV 的 max_field 非零（不触发）。
- kottke 的 `Epsilon2` 检查只在 kottke 模式下；FFT、closed 等路径的非有限输出未加同类检查（[源码] 未审计）。
- 驱动的 tensor + flat 栈输出含 NaN（既有行为），需要 S4 提供正常基准。

## 9. 路径清单

### 9.1 源码（提交）
- `S4/pattern/pattern.c`（commit `3e77aa9`）
- `S4/fmm/fmm_PolBasisNV.cpp`（commit `44bcf1c`）
- `S4/fmm/fmm_kottke.cpp`（commit `ff6dd7c`）

### 9.2 测试与脚本（提交）
- `testing/d003/stage_s3r2/`（commit `a6cd0a2`）：`README.md`、`d138_probe.cpp`、`field_compare.py`、`nvec_compare.py`、`gdb_d138_normal.gdb`、`gdb_d138_fft_dump.gdb`、`gdb_d138_nvec.gdb`、`kottke_probe_dump.cpp`、`gdb_d016_ret.gdb`、`r4a_run.sh`、`r4a_compare.sh`、`rel_diff.py`

### 9.3 报告与复现包（本文档提交）
- `checkpoints/p05/P05_S3R2_CLOSEOUT.md`（本报告）
- `checkpoints/p05/registries/s3r2/`（25 个文件；`MANIFEST.tsv` 追加 25 行，每行 sha256 已与包内文件核对）
- `checkpoints/p05/S1_evidence_digest.txt`（追加 22 行）

### 9.4 证据目录（不提交，被 `.git/info/exclude` 忽略）
- `checkpoints/p05/evidence/p05-s3r2/`：`GATE.txt`；期望文件（`R2-1_D138_*`、`R2-4a_MATRIX_*`、`REGISTRY_S3R2_PRE.*`）；结果（`R2-1_RESULT.txt`、`R2-2b_SEAM_RECORD.txt`、`R2-4bc_SUMMARY.txt`、`R2-4a_summary.tsv`、`R2-4a_jones_numeric.tsv`、`R2-5_OUT_OF_SCOPE_DRAFT.txt`）；运行目录（`R2-1_runs/`、`R2-4a_runs/`、`R2-4b_runs/`、`R2-4c_runs/`、`trace-drv/`）；驱动（`drivers/`、`r4drv/`，含 `DRIVER_PIN.sha256`）；构建（`build-p1/`、`build-p2/`、`build-p3/`、`r4trees/`、`trace-trees/`）；快照（`tmp_top_snapshot_{START,END}.txt`）与 strace（`strace_sample_{START,END}.txt`）。

### 9.5 未修改的对象（核对）
- `S4/` 中除 9.1 外的所有文件：未改动（`git diff 35cd7b3 HEAD -- S4/` 的文件清单为 3 个）。
- `testing/d003/judge_d003.py`：sha256 `d2d04145…`（未改）。
- `testing/d003/src/`（驱动与注入器）：自 S1R2 收尾以来无提交（`git log 33bff73..HEAD -- testing/d003/src/` 为 0）。
- `testing/d003/seam/`：未改。
- 已提交报告原文、`testing/s4test/ISSUE_REGISTRY.md`、`PROJECT_ROADMAP.md`：未改。

## 10. 收尾核对（报告写完后的核对，输出摘录）

- S4 改动文件清单（相对 `35cd7b3`）：`S4/fmm/fmm_PolBasisNV.cpp`、`S4/fmm/fmm_kottke.cpp`、`S4/pattern/pattern.c`，共 3 个；授权范围外的 S4 路径数：**0**。
- `/tmp` 快照：开始（12:50:44Z）与结束（13:12:05Z）均为 0 条目，哈希 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`。
- strace 抽样：开始与结束各一次，仓库外写入模式打开 **0**，`/tmp` 提及 **0**。
- judge 哈希：`d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`（与规定一致，未修改）。
- 本报告提交前的 `git status`：4 项（`S1_evidence_digest.txt`、`MANIFEST.tsv` 的修改；本报告与 `registries/s3r2/` 为新增）。提交后应为空。

## 11. 未完成声明

**未完成，等待用户审核。** 本轮不宣布 P05-S1、S2、S3、S4 任一阶段完成。三个源码提交与本轮的开发检查等待用户审核；七处 info=NULL 的修前→修后对照未证明；D016 的异常文本未经 Python 实测。
