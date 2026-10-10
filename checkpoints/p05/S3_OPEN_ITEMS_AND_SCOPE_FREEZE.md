# P05 / S3：关闭开放项并冻结 D003 范围

> 基线：`5b72793051eb705f0e9b2e5398e1a5f0484da0cb`（Master）
> 门禁起点：`9fee83d`（工作区干净，相对基线仅改 `checkpoints/p05/`）
> 来源标注：**实测** = 本轮运行或读取的原始输出；**代码阅读** = 只读源码；**文本比对** = 只读文本对照；**推断** = 由实测加代码阅读得出，未直接验证；**未确定** = 证据不足，不下结论。
> 证据：`checkpoints/p05/evidence/s3/`（被 `.git/info/exclude` 忽略，**未提交**）；清单 `EVIDENCE.sha256`（154 个文件，`sha256sum -c` 全部 OK）；归档见第 7 节。

---

## 0. 结论摘要

- **T11 结论撤回，由 T12 取代。** S2 的 T11 比较的是重试调用的输出，它不能回答"失败那次调用写了什么"。S2 的摘要与第 5 节把它说成"静默吞掉未造成错误数值"，这个结论**不成立**。
- **T12（第一次调用输出）**：注入后第一次调用的 E/H 输出与无注入对照**逐位相同**（scratch1、scratch2 各 144/144）。但**中间量已经错误**：`Epsilon_inv[0]` 从对照的 `0.4591` 变为 `1`，`solve_info` 从 `0` 变为 `1`（求解失败，无人读取）。**结论：中间量错误已证实；最终输出未被传播（仅 NB=1 已测）。**
- **T13（FMM 归属）**：NB=9 的 FFT 运行中，`S4_malloc` 共 **18** 次（与 S2 的 T10 一致）。其中 FMM 文件内 **2** 次（`fmm_FFT.cpp:74`、`:81`，都在 `FMMGetEpsilon_FFT` 开头），`Simulation_ComputeLayerModes` 直接调用 **5** 次，其余 **11** 次在非 FMM 路径。**当前注入器不能覆盖这些 FMM 点**（它们在 `fft_plan_*` 窗口之外）。
- **T14（O-1 补测）**：VL、ClosedForm，NB=5、6、7、8 **全部成功**，且 `n_G` 都等于 5；NB=9 成功（`n_G=9`）。O-1 的因果变量应是**实际 G 向量数 `n_G`，不是 NumBasis**。NB=1–4 的 `n_G` 未直接测（失败时无输出）。
- **T15（过时表述）**：共列出 **16** 处已提交文件中被后续证据推翻或修正的表述（第 6 节），历史文件未改写。
- **NB1 双字段（替代原 `NB1-REACHABLE`，该字段作废）**：`NB1-EXPLICIT-FAIL = YES`；`NB1-NONFINITE = NOT-REPRODUCED`。
- **D003 范围冻结**：纳入"plan 失败 → NULL 计划被执行 → 崩溃"（5 分支）；纳入"执行期分配失败 → 中间量 `Epsilon_inv` 错误且求解失败未被上报"（**中间量层面已证实**）；**开放**"中间量错误是否传播到最终输出"；不纳入 exec 边界（模拟）、O-1、历史 VL 非有限。

---

## 1. 门禁与环境

- 门禁：`HEAD=9fee83d`，工作区为空，exclude 中 p05 行 1 条（**本轮未新增 exclude 条目**），stash 为空。
- 驱动与注入器副本从 `/home/jackal/s4-fmm-accept/src/` 只读复制，原件校验和未变（`driver.cpp` `1be57c35…`，`inject.cpp` `13b2cbf5…`）。
- 所有构建与运行在同一后台作业内完成（`/tmp` 在工具调用之间被清空，本轮至少 6 次）。证据在作业结束后复制到 `checkpoints/p05/evidence/s3/`。
- `S4/` 源码未改动：`S4/fmm/fmm_FFT.cpp` 的 blob 哈希在工作区与 `9fee83d` 中一致（`6bed7ade…`）。

### 1.1 副本构成（实测，diff 存证）

| 副本 | 构成（按顺序，均相对历史原件） | diff 文件 |
|---|---|---|
| 驱动 `driver-s3` | ① S2 增量（`S4FMM_DUMP`，E/H 重试输出）② S1B 删除 FieldCache 循环 ③ **T12 新增**（`S4FMM_DUMP1`，第一次调用输出，锚点唯一，1 处） | `s3/drv/driver-s3-vs-history.diff`（3 个 hunk） |
| 注入器 `inject-s3` | **T13 新增**（三层返回地址 + arm 状态，仅 `S4FMM_MALLOC_LOG` 设置时输出；决策行数 8 = 8，未改） | `s3/drv/inject-s3-vs-history.diff`（1 个 hunk） |

- **关于 S2 的 diff 叠加问题（实测，已纠正）**：S2 的驱动 diff 以原件为基准生成，其第二个 hunk 与 S1B 的删除是同一改动。把它直接叠加在 S1B 副本上会失败（1/2 hunk）。正确做法是只取 S2 的第一个 hunk（E/H 导出）作为增量，再应用 S1B。此时链条生成的 hunk 内容与 S2 的驱动 diff **逐行相同**（已验证）。
- **关于 S2 注入器的 diff 与 S2 的 O0 实验（实测，已披露）**：S2 的 `inject-s2-vs-history.diff` 只记录单层 `caller=`。S2 的 O0 映射实际用的是两层 `caller0/caller1`，那一版没有单独存证。S3 的注入器改为三层 `caller0/1/2`，格式为 `MALLOC_CALL3`，与 S2 的 `MALLOC_CALL` 不同，后续分析只用 `MALLOC_CALL3`。

---

## 2. T12–T15 结果

### 2.1 T12：被注入失败的那次调用的输出（实测）

**设计**：`FMM_MODE=fft`，`S4FMM_NG=1`（NB=1），每组同时记录第一次调用（`S4FMM_DUMP1`，在 `RC first` 之后、重试之前）与重试调用（`S4FMM_DUMP`）的 E/H。缓冲区初值为哨兵 `SENTINEL = -98765.4321`（源码 `driver.cpp:17`，在第一次调用之前由 `Buf` 构造填充，`driver.cpp:117`）。哨兵的判定用精确数值相等。

| 场景 | 证据 | RC first | HIT | 第一次调用的 E/H 元素（144 个） | 与对照比较 |
|---|---|---|---|---|---|
| control-fft-ng1（无注入） | `s3/t12/control-fft-ng1.first` | 0 | 0 | 144 写入，0 个仍为哨兵 | — |
| scratch1-fft-ng1 | `s3/t12/scratch1-fft-ng1.first` | 0 | 1 | 144 写入，0 个仍为哨兵 | **相同 144/144** |
| scratch2-fft-ng1 | `s3/t12/scratch2-fft-ng1.first` | 0 | 1 | 144 写入，0 个仍为哨兵 | **相同 144/144** |

- 四种情形的判定：未写入（仍哨兵）= 0；部分写入 = 0；写入但不同 = 0；完全相同 = 144。
- **最终 E/H 相同不等于中间量相同**。第一次调用的 E/H 是在 `FMMGetEpsilon_FFT` 之后、被后续成功执行覆盖之后的结果，它已经不是失败那次的中间状态（见下）。

**中间量（实测，gdb，O0 构建，`s3/t12solve/`、`s3/t12mid/`）**

读取点 1：`fmm_FFT.cpp:205`（`LinearSolve` 之后；gdb 实际把断点落在第 207 行，因为 205 为空行，见 `s3/t12solve/` 的 `Breakpoint 1 at … line 207`）。

| 量 | 对照（无注入） | scratch1（注入） |
|---|---|---|
| `solve_info` | **0** | **1** |
| `Epsilon_inv[0]` | `0.45911632377820932 + 0i` | **`1 + 0i`**（单位矩阵初值） |
| `Epsilon2[0]` | `2.1780972450961724 + 0i` | **`0 + 0i`** |

读取点 2：`S4.cpp:2375`（`FMMGetEpsilon_FFT` 返回之后）。

| 量 | 对照 | scratch1 |
|---|---|---|
| `Epsilon2[0..3]` | `2.178, 0, 0, 2.178` | `2.178, 0, 0, 2.178` |
| `Epsilon_inv[0]` | `0.4591` | **`1`** |

- **解释（实测 + 代码阅读，一致）**：注入的 16 字节分配是 `kf_bfly_generic` 的 scratch（gdb 栈，`kiss_fft.c:216`，见 2.2）。它返回 NULL 后执行 `*err = 1; return;`（`kiss_fft.c:217`），在写 `Fout` 之前返回。`err` 经 `kf_work` 与 `kiss_fft_stride_checked` 传到 `return (0 != err)`（`kiss_fft.c:401`）。`FMMGetEpsilon_FFT` 丢弃 `fft_plan_exec` 的返回值（`fmm_FFT.cpp:183`，不消费），于是 `FMMGetEpsilon_FFT` 返回 0。
- `Epsilon_inv` 在 `fmm_FFT.cpp:202` 被置为单位矩阵，再由 `LinearSolve` 求逆（`:204`）。`solve_info=1`（求解失败）时，`Epsilon_inv` 保留为单位矩阵，**求逆结果没有写回**。注入组正是如此（实测）。
- `Epsilon2[0]` 的两个读数来自**两次独立的 gdb 运行**，配置相同但不是同一次执行的前后两个时刻：`s3/t12solve/`（`fmm_FFT.cpp:205`，读得 0）与 `s3/t12mid/`（`S4.cpp:2375`，读得 2.178）。两次读数都是确定的。据此推断：后续的 `plans[w]` 成功执行（`fmm_FFT.cpp:212`，写块 227）覆盖了 `Epsilon2[0]`。这是推断，未在同一次运行中连续读取验证。**`Epsilon2` 最终正确，`Epsilon_inv` 永久错误**（后者的 `1` 与 `solve_info=1` 在两次运行中都是同一值，结论的这一部分不依赖该推断）。
- **`solve_info` 被写入但无人读取**（`fmm_FFT.cpp:203–204`，F6）。这是中间量错误没有被上报的直接原因。

**关于 T12 的适用性（实测）**：NB=9 的适用性运行（`s3/t12/scratch1-fft-ng9-applicability.log`，`num_basis=9`，网格 `8x8`）`HIT=0`。进一步，T13 的 NB=9 计数（`s3/t13/counter-fft-nb9.log`）的 91 次 `malloc` 全部在 `arm` 窗口之外（`arm==1` 为 0 次，`arm==2` 为 0 次）。**NB=9 的执行期窗口内没有任何分配**，所以执行期 scratch 注入在 NB=9 上不适用（有运行证据，不只是注释）。

**T12 的 `scratch2` 中间量未读取**（只做了 `scratch1` 的 gdb 中间量读取）。

### 2.2 T12 的调用栈（实测，gdb，`s3/t12gdb/scratch1-stack.gdb.txt`）

断点：`inject.cpp:43`（当前副本的 scratch `return NULL`），条件 `arm == 2 && n == 16`，即注入器自己的判定。

```
#0  __wrap_malloc (n=16)
#1  kf_bfly_generic (fstride=1, m=1, p=1, err=...)  kiss_fft.c:216   <- scratch 分配行
#2  kf_work (...)                                    kiss_fft.c:311
#3  kiss_fft_stride_checked (fin=..., fout=...)      kiss_fft.c:399   <- fin != fout 分支
#4  kiss_fftnd_checked                               kiss_fftnd.c:186
#5  fft_plan_exec                                    fft_iface.cpp:131
#6  __wrap__fft_plan_exec                            inject.cpp:70
#7  FMMGetEpsilon_FFT                                fmm_FFT.cpp:183    <- plans[4]，计算 Epsilon_inv 的那次
```

- `$1 = arm = 2`，`$2 = n = 16`。`finish` 返回 `0x0`（注入生效）。

### 2.3 T13：`S4_malloc` 的 FMM 归属（实测，`s3/t13map/mapped.txt`）

运行：NB=9，FFT，O0 构建（`-O0 -fno-inline -fno-omit-frame-pointer`）。计数器记录三层返回地址 `caller0/1/2`，`addr2line -f` 映射。映射覆盖 91 次调用，归并为 30 个不同的三元组，计数和为 91。

**与 S2 的交叉核对**：`S4_malloc` 的调用总数为 **18**，与 S2 的 T10（同一配置、O0）一致。

| 归属（`S4_malloc` 的调用者） | 次数 | 位置 | 是否属于 `fmm_*.cpp` | 是否在 `fft_plan_*` 窗口内 |
|---|---|---|---|---|
| `FMMGetEpsilon_FFT` | **2** | `fmm_FFT.cpp:74`（`work`，6·ng2）、`:81`（`discval`） | **是** | 否（在 `fft_plan_*` 之外） |
| `Simulation_ComputeLayerModes` | 5 | `S4.cpp` 内多处（含 `:2267`、`:2295`、`:2402`、`:2419`） | 否 | 否 |
| 其它 `S4.cpp` 调用者 | 11 | `Simulation_InitSolution`、`Simulation_ComputeLayerSolution`、`S4_Simulation_New`、`S4_Simulation_GetFieldPlane`（`:4290`） | 否 | 否 |

- 次数由 `mapped.txt` 经脚本统计得出（`s3/t13map/`），不是手数。（初稿中我曾手数为 3，脚本给出 5，已以脚本为准。）
- **注入器覆盖判定（实测）**：`arm` 只在 `fft_plan_dft_2d` 的**被选中的那一次**调用（`n_plan_calls == nth()`）中置 1，在 `fft_plan_exec` 的**每一次**调用中置 2（`inject.cpp:49–51, 64–66`）。FMM 的两个 `S4_malloc` 点（`fmm_FFT.cpp:74`、`81`）发生在 `FMMGetEpsilon_FFT` 的开头，**不在任何 `fft_plan_*` 调用之内**，因此 `plan` 与 `scratch` 注入都不覆盖它们。**结论：当前注入器不能覆盖 FMM 的 `S4_malloc` 点。**
- **`fft_plan_dft_2d` 内部的分配**（如 `kiss_fftnd_alloc`，计数 17）处于 `fft_plan_dft_2d` 的调用栈内，但 `arm==1` 只对选中的那一次计划有效。因此它们只能被 `plan` 注入的 `nth` 选中，不能被"任意一次"覆盖。
- **F5 的修正（实测）**：S1 的 "17 个 `S4_malloc` 无 NULL 检查" 是 `fmm/*.cpp` 中的**静态调用点计数**。本次 FFT 运行中，FMM 文件里实际执行的 `S4_malloc` 点只有 **2** 个（`fmm_FFT.cpp:74`、`81`）。PolBasis 与 Kottke 的 `S4_malloc` 点在 `fft` 模式下没有执行。

### 2.4 T14：O-1 的 NB=6、7、8 补测，以及 NB=5、9 的 `n_G`（实测，`s3/t14/`）

配置：`VL`（`PolarizationBasis='Default'`），`DiscretizedEpsilon` 未设（ClosedForm+PolBasis），`f=0.427`，`θ=0°`，每个用例独立子进程。

| NB | status | `n_G`（由 `amp_len/2`） | flux 有限 | amp 有限 | 证据 | sha256 |
|---|---|---|---|---|---|---|
| 5 | ok | **5** | True | True | `s3/t14/closed-VL-nb5-th0.json` | 见清单 |
| 6 | ok | **5** | True | True | `s3/t14/closed-VL-nb6-th0.json` | 见清单 |
| 7 | ok | **5** | True | True | `s3/t14/closed-VL-nb7-th0.json` | 见清单 |
| 8 | ok | **5** | True | True | `s3/t14/closed-VL-nb8-th0.json` | 见清单 |
| 9 | ok | **9** | True | True | `s3/t14/closed-VL-nb9-th0.json` | 见清单 |

- `flux_top[1]` 对 NB=5、6、7、8 都是 `(-0.02254946600556442-5.42e-20j)`（同一 `n_G`，同一结果）。
- **O-1 因果变量**：`G_select` 把 `*NG` 作为上限，实际数目由圆形截断的壳层决定（`gsel.c:155`，`*NG = i`，代码阅读）。因此 NumBasis 不是决定 `n_G` 的直接因素。**NB=5–8 都选出 `n_G=5`，全部成功**，说明阈值的表述应当用 `n_G`。
- **未确定**：NB=1–4 的 `n_G`。它们失败，输出中没有 `amp_len`，无法从运行直接得到。NB=1 时 `G_select` 直接返回 `n_G=1`（`gsel.c:172–173`，代码阅读），NB=2–4 的 `n_G` 未确定。
- **首次 T14 运行无效（已披露，见第 5 节）**：第一次 T14 的 NB=6–8 全部报 `AttributeError: module 'S4' has no attribute 'New'`，原因是那个作业没有构建 Python 扩展。这些结果**已作废**，由第二次运行（扩展构建成功、前提检查 `hasattr(S4,'New')` 通过）替代。

### 2.5 T15：过时表述清单

按要求只列出，不改写历史文件。每条给出位置、原文摘要、修正证据、当前正确表述。

| # | 文件:行 | 原文摘要 | 修正证据 | 当前正确表述 |
|---|---|---|---|---|
| 1 | `S1B_T4_T5_ADDENDUM.md:159`（b.3） | "`S4_malloc` 是否经过 `--wrap=malloc` **未验证**" | S2 §2.4（18 次，O0 映射）；S3 §2.3（18 次，一致） | 已验证：经过 `malloc`，`--wrap` 能计数；但注入不覆盖 FMM 点（S3 §2.3） |
| 2 | `S1B_T4_T5_ADDENDUM.md:224`（F9） | "`S4_malloc` 是否经过 `--wrap` **未验证**（见 b.3）" | 同上 | 同 #1 |
| 3 | `S1_BASELINE_AND_ENUMERATION.md:430`（F9 行） | "`--wrap=malloc` 对 `S4_malloc` **无效**（4.4）" | 与 S1 §4.4（254 行起，已修正为"普通构建走 malloc"）自相矛盾；S2 §2.4 | 计数覆盖成立；注入覆盖不成立（窗口外） |
| 4 | `S1_BASELINE_AND_ENUMERATION.md:17–18`（§0 摘要） | "基线缺陷复现：未运行……静默吞掉 0 / 崩溃 0 / 无效全部" | S1B 补跑（T4/T5 已运行，见 `S1B_T4_T5_ADDENDUM.md` b.2） | 已运行：崩溃 5，静默 2 真实 + 5 边界，报告 0，无效 0 |
| 5 | `S1_BASELINE_AND_ENUMERATION.md:292–295`（§5） | "控制运行结果（T4）— **未运行**" | S1B 运行 T4（10 例，附录 b.1） | 已运行 |
| 6 | `S1_BASELINE_AND_ENUMERATION.md:307`（§6） | "基线故障复现结果（T5）— **未运行**" | S1B 运行 T5（12 例，附录 b.2） | 已运行 |
| 7 | `S1_BASELINE_AND_ENUMERATION.md:241` | "驱动不可编译，**未运行验证**" | S1B 修复副本后编译运行 | 驱动副本可编译运行（需注明副本构成，S3 §1.1） |
| 8 | `S1_BASELINE_AND_ENUMERATION.md:215`（§3.1） | "半覆盖场景……**未运行验证**" | S2 gdb（五份栈）；S3 T12 中间量（`Epsilon_inv` 错误，`solve_info=1`） | 半覆盖的中间量层面已验证；最终输出层面未验证（S3 §2.1） |
| 9 | `S2_SCOPE_AND_GAPS.md:17`（§0 摘要） | "静默吞掉在该用例中**未造成错误数值**" | S3 T12：中间量 `Epsilon_inv` 错误（`0.4591`→`1`），`solve_info=1` | **撤回**。中间量已错误；最终输出仅 NB=1 未传播 |
| 10 | `S2_SCOPE_AND_GAPS.md:18`（§0 D003） | "暂不纳入'静默吞掉→错误数值'，因为 T11 未能证明它" | T11 比较的是重试调用，不能回答问题（用户指出，已核实）；T12 给出中间量证据 | 见 S3 §4 的 D003 冻结表 |
| 11 | `S2_SCOPE_AND_GAPS.md:208`（§4.3） | "依据：**4 条**独立入口、2 条路径" | 用户指出；独立入口实为三个（ClosedForm Python、FFT Python、驱动），ClosedForm 经 S1/S2 两次复现 | "三个独立入口" |
| 12 | `S2_SCOPE_AND_GAPS.md:220`（§5 表） | "**S2 T11 显示重试输出与无注入对照逐位相同**"（作为暂不纳入的依据） | 同 #9 | 该依据撤回；T12 给出第一次调用与中间量的证据 |
| 13 | `S2_SCOPE_AND_GAPS.md:261`（§8 第 2 条） | "推荐：暂不纳入。先找到输出确实错误的用例（候选：`scratch2`……）" | T12 已测 scratch2（第一次调用输出相同）；中间量层面的错误已证实 | 决策点已改变，见 S3 §4 |
| 14 | `S2_SCOPE_AND_GAPS.md:§2.5`（局限） | "只覆盖 `scratch1`……" | 局限本身正确，但未说明 T11 比较的调用不对 | 补充：T11 比较的是重试，不是失败调用（已由 T12 替代） |
| 15 | `S2_SCOPE_AND_GAPS.md:§2.2` / §0 的 NB 阈值 | "NB ≤ 4 失败，NB ≥ 5 成功" | S3 T14：NB=5–8 同为 `n_G=5`；阈值的因果变量是 `n_G` | 阈值应以 `n_G` 表述；NB=1–4 的 `n_G` 未确定 |
| 16 | `S1_evidence_digest.txt`（S2 追加段，第 118 行） | "T11 ... 144/144 elements bit-identical" 与 "S2 T11 ... 未造成" 的解读 | 同 #9 | 以 S3 的 T12 为准。数字本身（144/144）正确，但它比较的是重试 |

- 条目 4–6 是 S1 时期的状态，被 S1B 取代；它们本身不是错误，但在 S1 摘要中仍被读作当前状态，所以列入。
- 条目 7 与 8 是 S1 的"未验证"在 S1B/S2/S3 之后已部分被推翻，列入。

---

## 3. NB1 双字段与 O-1 的最终记录

**原字段 `NB1-REACHABLE` 作废**（定义歧义：它被同时用来表达"显式失败"与"非有限输出"，下游容易误读为后者）。

| 字段 | 取值 | 定义 | 依据 |
|---|---|---|---|
| **NB1-EXPLICIT-FAIL** | **YES** | VL NB=1 在默认公共 API 与默认选项下**确定性**失败（显式报告，不依赖注入）。 | 三个独立入口：ClosedForm Python（S1、S2 两次独立运行，异常文本逐字相同）；FFT Python（S2，`DiscretizedEpsilon=True`）；驱动 `vl`（S1B，无注入，rc=1，RC 20）。另有 NB=4 的驱动与 Python 复现（S2）。 |
| **NB1-NONFINITE** | **NOT-REPRODUCED** | 默认配置下 VL NB=1 产生**非有限数值**。 | 主矩阵（S1，12 项）与 S2 的全部 FFT 与 ClosedForm 用例（S2 T7）中，没有任何非有限数值。VL NB=1 的每个用例要么异常（无输出）、要么有限（无此情形）。 |

- **O-1 的最终记录**：VL 基的特征值分解在 `n_G` 较小时失败（显式，`info=2`，rc=20）。已测：NB=1–4 失败（`n_G` 对 NB=2–4 未确定）；NB=5–9 成功（`n_G`=5、5、5、5、9）。**阈值以 `n_G` 表述**：`n_G=5` 成功，`n_G≤?` 失败（上界未确定，需测 NB=1–4 的 `n_G`，见第 8 节）。
- **O-1 不并入 D003**（主指示）。它是显式报告的，不是静默错误数值。

---

## 4. D003 范围冻结

| 缺陷类别 | 决定 | 依据（证据） | 修复阶段的最小验证用例 |
|---|---|---|---|
| **A. plan 失败 → NULL 计划被执行 → 崩溃**（`fft_plan_dft_2d` 返回 NULL 未检查，`fft_plan_exec(NULL)` 解引用） | **纳入** | S1B：5 分支 SIGSEGV（rc=139）；S2：gdb 五份栈，`fft_plan_exec(p=0x0)`；调用者按分支不同（FFT/Kottke/PolBasis×3） | `plan1` 注入（`S4FMM_INJECT=plan S4FMM_NTH=1`），5 分支，NB=9；期望：不崩溃，RC 非零且 `RC retry` 恢复 |
| **B. 执行期分配失败 → 中间量错误，求解失败未上报**（`fmm_FFT.cpp:183/212` 丢弃 `fft_plan_exec` 返回；`solve_info` 无人读取） | **纳入（中间量层面）** | S3 T12：`Epsilon_inv` 0.4591→1，`solve_info` 0→1（gdb，实测）；F6 | `scratch1` 注入（NB=1，fft），检查 `Epsilon_inv` 与 `solve_info`；期望：失败被上报，`Epsilon_inv` 不被错误地留作单位矩阵 |
| **C. 中间量错误 → 最终输出错误**（传播） | **开放** | NB=1：最终 E/H 与对照逐位相同（S3 T12，144/144，两个用例）；NB=9：执行期窗口内无分配，注入不适用（S3 T13） | 需要：(i) NB≥2 且执行期有分配的配置；或 (ii) 找到使 `Epsilon_inv` 错误进入输出的配置。**未找到，不关闭。** |
| **D. exec 边界（模拟）** | **不纳入** | 注入器注释："BOUNDARY SIMULATION…not a real failure" | 仅可用于探测"调用者是否消费返回值"，不计为真实缺陷 |
| **E. O-1**（VL NB=1 显式特征值失败，`info=2`） | **不纳入** | 显式报告，不依赖注入，多入口复现（第 3 节） | — |
| **F. 历史 VL "注入后重试非有限"**（F10） | **不纳入** | 历史负载的 NB、频率、库未确定（S2 T9） | 待历史负载可重现后再判 |
| **G. S4_malloc 的 FMM 点不可注入**（注入覆盖范围） | **不纳入缺陷，记为限制** | S3 T13：2 个 FMM 点在窗口外 | 若要注入这些点，需改注入器的窗口定义（超出本轮范围，不修复） |

- **B 的决定为本轮最重要的变化**。S2 的建议是"暂不纳入静默吞掉→错误数值"。S3 的 T12 表明：中间量已经错误，求解失败被静默丢弃。因此**中间量层面的 D003 危险模式已经证实**，纳入 B 是基于实测，不是推断。
- **C 仍开放**。C 是"错误是否传播到输出"，它决定 B 的危害等级。在本轮的唯一可测配置（NB=1）中没有传播。在 NB≥2 时执行期窗口内有分配（T13 只测了 NB=9，其窗口内为 0，所以 NB=9 不适用）。**NB 2–8 的执行期分配情况未测**，这是 C 的主要缺口。

---

## 5. 偏离项

1. **驱动副本的累积改动**：S1B 删除 FieldCache；S2 增加 `S4FMM_DUMP`（重试 E/H）与单层 malloc 计数；S3 增加 `S4FMM_DUMP1`（第一次调用 E/H）与注入器的三层计数。全部仅在环境变量设置时输出，注入决策未改（决策行数核对为 8=8）。超出 S1B 授权的"一处最小修改"，属于 S2、S3 为 T10–T13 新增的观测代码，已逐条存证。
2. **S2 驱动 diff 的基准问题**：S2 的 diff 以原件为基准，把 S1B 的删除重复记录为第二个 hunk。叠加会失败。S3 改为只取第一个 hunk 作增量（第 1.1 节）。**S2 的存证文件本身未改写**，结论不受影响（hunk 内容已核对相同）。
3. **S2 注入器 diff 与 S2 O0 实验不一致**：S2 的存证 diff 是单层，S2 的 O0 映射实际用两层。未单独存证那一版（第 1.1 节）。
4. **O0 构建的变量**：S2 早先误用 `OPT=-O0`（未生效，已废弃）；S3 用 `CFLAGS/CXXFLAGS` 覆盖，经 `-O3`/`-O0` 计数核对（S3 的 O0 构建 `-O0` 为 26 次，`-O3` 仅 Lua 扩展行）。
5. **T12 的两次 gdb 失败（已披露，结果已作废）**：
   - 断点行号：第一次用原件行号 38，在当前副本中停在第 39 行（`n=344`，普通分配，非注入点）。改用当前副本行号 43 并加条件 `arm == 2 && n == 16`，之后命中正确。
   - 表达式：第一次中间量读取用 `Epsilon2[0]`（`No symbol "Epsilon2" in current context`），应为 `pB->Epsilon2[0]`。修正后读取成功（5 个值）。
6. **T14 的首次运行无效（已披露）**：未构建 Python 扩展，`S4.New` 不存在，NB=6–8 的 `AttributeError` 结果**作废**。第二次运行先构建扩展，并以 `hasattr(S4,'New')` 作为前提检查，之后才运行。
7. **NB=9 适用性的核查**：`scratch1-fft-ng9-applicability.log` 与 NB=1 对照的大小相同（923 字节）。我怀疑它是对照的副本，用 `cmp` 排除（第 1 字节起不同，DRIVER 头为 `num_basis=9`，网格 `8x8`）。大小相同只是巧合，**大小不能作为内容相同的证据**。
8. **一次误导性的手数**：T13 归属中 `Simulation_ComputeLayerModes` 的次数，我初稿手数为 3，脚本统计为 5。以脚本为准。
9. **未执行的操作**：未修改 `S4/`、`Makefile*`、`setup.py`；未运行 `/home/jackal/s4-fmm-*` 下的任何二进制；未新增 exclude 条目；未 push、reset、clean、stash。

---

## 6. 修复设计输入（只列位置，不写补丁）

纳入的缺陷类别与它们的位置。修复设计阶段需要以此为起点。

**A. plan 失败 → NULL 计划被执行**（纳入）

| 文件:行 | 现状 | 需要的行为（待设计） |
|---|---|---|
| `S4/fmm/fmm_FFT.cpp:85` | `plans[i] = fft_plan_dft_2d(...)` 不检查 NULL，随后 `fft_plan_exec(plans[4])`（`:183`）直接使用 | 检查每个 plan；失败时清理已创建的 plan 并返回错误 |
| `S4/fmm/fmm_kottke.cpp:89` | 同上（`fft_plan_exec` 于 `:263`、`:287`） | 同上 |
| `S4/fmm/fmm_PolBasisJones.cpp:245` | `plan` 不检查，`fft_plan_exec` 于 `:258/277/296/315` | 同上 |
| `S4/fmm/fmm_PolBasisNV.cpp:190` | 同上（`fft_plan_exec` 于 `:206`） | 同上 |
| `S4/fmm/fmm_PolBasisVL.cpp:200` | 同上（`fft_plan_exec` 于 `:215`） | 同上 |
| `S4/rcwa.cpp:2209` | **参照实现**：`if(NULL == plan[i]){ ret = 1; goto cleanup; }` | 无需修改，作为参照 |

**B. 执行期失败 → 中间量错误，求解失败未上报**（纳入中间量层面）

| 文件:行 | 现状 | 需要的行为（待设计） |
|---|---|---|
| `S4/fmm/fmm_FFT.cpp:183`、`:212` | `fft_plan_exec(...)` 返回值丢弃 | 消费返回值；非零时返回错误，不继续写 `Epsilon2`/`Epsilon_inv` |
| `S4/fmm/fmm_kottke.cpp:263`、`:287` | 同上 | 同上 |
| `S4/fmm/fmm_PolBasis{Jones,NV,VL}.cpp`（见 A） | 同上 | 同上 |
| `S4/fmm/fmm_FFT.cpp:203–204`、`fmm_kottke.cpp:278–279` | `solve_info` 写入但无人读取（F6） | 读取 `solve_info`，非零时返回错误 |
| `S4/S4.cpp:2374–2394` | `FMMGetEpsilon_*` 返回值全部丢弃（F4） | 消费返回值并向上传播 |
| `S4/S4.cpp:2399` 起 | 特征值分解在 FMMGetEpsilon 失败后仍执行 | 仅在 FMM 构造成功后进入 |

**C. 开放（不列入修复）**：中间量错误是否传播到输出。待 S4 或之后的阶段找到可测配置后再决定。

**相关但不属于 D003 的位置（记录，不修复）**
- `S4/fmm/fmm_*.cpp` 中 17 个 `S4_malloc` 调用点无 NULL 检查（F5，静态计数；FFT 运行中实际执行的 FMM 点为 2 个，`fmm_FFT.cpp:74`、`81`）。
- `S4/S4.cpp:2267`、`:2295`、`:2402`、`:2419` 的 `malloc`/`S4_malloc` 无 NULL 检查。
- O-1：`S4/rcwa.cpp:666` 与 `:883`（特征值失败的打印点），`S4/S4.cpp:2362`、`:2416`、`:2432`（返回 20）。

---

## 7. F1–F11 的最新状态（只列有变化的）

| 编号 | 变化 | 状态（S3 后） | 依据 |
|---|---|---|---|
| **F4** | 增加中间量证据 | 实测：FMMGetEpsilon 返回值丢弃，`Epsilon_inv` 因此错误 | S3 §2.1 |
| **F5** | 静态计数与执行计数区分 | 推断：17 为静态调用点；FFT 运行中执行的 FMM `S4_malloc` 点为 2 | S3 §2.3 |
| **F6** | 由推断升为实测 | **实测**：`solve_info` 注入时为 1，无人读取，导致中间量错误未上报 | S3 §2.1（gdb，`fmm_FFT.cpp:205`） |
| **F7** | 无变化 | 推断（代码阅读） | — |
| **F9** | 补充 FMM 归属 | **实测**：计数覆盖成立（18 次）；注入覆盖对 FMM 点不成立（窗口外，2 个点） | S3 §2.3；S2 §2.4 |
| **F10** | 排除一种解释 | 未确定（因果）；历史负载与库未确定 | S2 §2.3；S3 无新证据 |

- F1、F2、F3、F8、F11：本轮无新证据，状态不变。

---

## 8. 未关闭的开放项与需要补充的证据

- **C（中间量 → 输出）**：需要执行期有分配的 NB≥2 配置。NB=9 窗口内无分配（实测），NB 2–8 的执行期分配情况**未测**。
- **O-1 的上界**：需要测 NB=1–4 的 `n_G`。它们失败，无输出，需要从 `G_select` 的截断推断或换一种读取方式（例如在 `Simulation_ComputeLayerModes` 入口读取 `n`，在 gdb 中）。
- **T13 的注入覆盖范围**：本轮只确认 FMM 的两个 `S4_malloc` 点不可注入。是否需要扩展注入器的窗口，是修复设计阶段的决定，不在本轮范围。

---

## 9. 需要主脑决定的事项

1. **B 的纳入（中间量层面）**。推荐：纳入。依据是 gdb 实测的 `Epsilon_inv` 错误与 `solve_info` 未读。危害等级（C）保持开放。
2. **C 的处理**。推荐：保持开放，并把"找到传播配置"列为修复设计的前置任务。不要把"NB=1 未传播"外推为"不传播"。
3. **O-1 的阈值表述**。推荐：以 `n_G` 表述，并记为"`n_G=5` 成功；`n_G` 上界未确定（NB=1–4 失败，`n_G` 未测）"。
4. **证据外存**。推荐：外存 `evidence-s1-s2-s3.tar.gz`（119000 字节，sha256 `d500f7af…febe86`）。这是唯一的完整副本，仓库内被忽略的目录与沙箱 `/tmp` 都不是持久位置。命令：`cp <仓库>/checkpoints/p05/evidence/archive/evidence-s1-s2-s3.tar.gz ~/` 并校验。
5. **注入器窗口是否扩展**（T13）。推荐：不在 D003 修复中扩展。它是测试工具的范围，不是产品缺陷。

---

## 10. 证据路径与校验

- 证据目录：`checkpoints/p05/evidence/s3/`（被忽略，未提交）。
- 清单：`checkpoints/p05/evidence/EVIDENCE.sha256`，**154 个文件**，`s3/` 下 49 个；`sha256sum -c` 结果 **154 OK、0 失败**（`checkpoints/p05/evidence/logs/s3-verify.txt`）。
- 归档（新文件名，未覆盖旧归档）：`checkpoints/p05/evidence/archive/evidence-s1-s2-s3.tar.gz`
  - 大小：**119000 字节**
  - sha256：`d500f7afb5ab332f839dfed884122045e33dd1282b60f00ef40b86d966febe86`
  - 成员：不含归档自身；从归档解出后 **154/154 与清单一致**。
  - 旧归档 `evidence-s1-s2.tar.gz`（71185 字节，`2cacdc0a…a1a5f75f`）未触碰。
  - 未移到仓库外，未提交。是否外存由主脑决定。
