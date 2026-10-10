# P05-S2 报告：测试装置（D003 故障注入装置）

> 状态：**P05-S2 未完成，等待用户审核。** 本报告只汇报事实，不宣布 P05-S1 或 P05-S2 完成。
> 基线：`5b72793051eb705f0e9b2e5398e1a5f0484da0cb`（Master）；开始门禁提交：`17d151c9764ff908a3e5cb7f1248341523e186e1`
> 分支：`codex/p05-d003-fft-error-propagation`
> 来源标注：**[实测]** 本轮运行的原始输出；**[源码]** 只读阅读源码，已逐行回查；**[推断]** 由实测加源码得出，未直接验证；**[未验证]** 本阶段无证据。
> 证据目录：`checkpoints/p05/evidence/p05-s2/`（被 `.git/info/exclude` 忽略，**不提交**）。

---

## 0. 编号对照表（S2.5）

本阶段是 P05 原始计划的正式阶段 **P05-S2（测试装置）**。下列历史轮次的文件名与阶段名**与本阶段同名不等同**，不改写。

| 历史轮次 | 历史报告文件 | 归属 |
|---|---|---|
| S1 | `S1_BASELINE_AND_ENUMERATION.md` | P05-S1 |
| S1B | `S1B_T4_T5_ADDENDUM.md` | P05-S1 证据扩展 |
| S2 | `S2_SCOPE_AND_GAPS.md` | P05-S1 证据扩展（与 P05-S2 不同） |
| S3 | `S3_OPEN_ITEMS_AND_SCOPE_FREEZE.md` | P05-S1 证据扩展 |
| S4 | `S4_SENSITIVITY_AND_REACHABILITY.md` | P05-S1 证据扩展 |
| S5 | `S5_OBLIQUE_AND_REACHABILITY.md` | P05-S1 证据扩展 |
| S5b | `S5B_POLARIZATION_SENSITIVITY.md` | P05-S1 证据扩展 |
| **新轮次（本报告）** | `P05_S2_TEST_HARNESS.md` | **P05-S2** |

> 本报告中所有"S2"若未加前缀，指 P05-S2 正式阶段的子任务，**不指**历史 S2 轮次。本报告引用历史轮次时一律写全称（如"S1B 附录"）。
> 本阶段内的额外调查只作为 P05-S2 的子任务，见第 9 节，未自立新阶段。

---

## 1. 状态（只报告事实）

| 项 | 结果 |
|---|---|
| S2.1 装置入仓 | **已完成**（历史源码只读复制、PROVENANCE、整理版驱动、入口脚本）。默认输出与 S1B 补丁版二进制逐字节一致（10/10 控制）。 |
| S2.2 注入覆盖扩展 | **部分完成**。`S4_malloc`：FMM 路径 2 个点可注入（已实测）。**LinearSolve：未覆盖，需要生产侧 seam，等待批准（第 7 节）。** plan/exec 两步：沿用并保留。命中计数：已输出。 |
| S2.3 覆盖 5 个分支与偏振 | **部分完成**。5 个分支的注入/控制已跑；p/s/mix 输出敏感性已测；PolBasis（vl/jones/nv）输出敏感性用例已补。 |
| S2.4 基线失败判定器 | **已完成**（可执行判定器、夹具自测、灵敏度检验）。22 个 S1B 用例**类别 22/22 一致**；原始字段 15/22 一致，7/22 的 `rc` 因驱动修正而不同（第 6 节）。 |
| S2.5 编号对照表 | **已完成**（第 0 节）。 |
| 证据归档与清单 | **已完成**：`EVIDENCE.sha256` 1048 条 `sha256sum -c` 全部通过；归档 `archive/evidence-p05-s2.tar.gz` 解压后 414 个文件逐一比对，0 处不一致。 |

**未完成与未关闭的事项：**
- LinearSolve 的注入覆盖需要生产侧 seam，**未经批准不实施**（第 7 节）。
- 22 个 S1B 用例中有 7 个的 `rc` 字段与 S1B 不同（驱动修正所致，第 6 节）。这是披露的差异，不是回归，但**不是逐字段一致**。
- 本阶段不宣布 P05-S1 或 P05-S2 完成。

---

## 2. 提交

本阶段分两个提交：

- **装置提交 `e18854c`**（父提交 `17d151c`）：`testing/d003/` 共 10 个文件、1582 行新增。提交信息：`test(p05): S2 fault-injection harness for D003 baseline`。提交后核对：提交内容与工作区逐字节一致；提交范围越界文件为 0。
- **报告提交**：`checkpoints/p05/P05_S2_TEST_HARNESS.md` 与 `checkpoints/p05/S1_evidence_digest.txt` 的 S2 追加段。提交哈希与信息见第 10 节（报告提交完成后补写）。

> 提交后 `git diff --stat 5b72793 HEAD` 的结果见第 10 节。

---

## 3. S2.1 装置入仓 [实测 + 源码]

### 3.1 历史源码的只读复制与哈希
| 文件 | 来源 | sha256 | 核对 |
|---|---|---|---|
| `testing/d003/src/history/driver.history.cpp` | `/home/jackal/s4-fmm-accept/src/driver.cpp` | `1be57c35f66e6822fdb21f2ea1d0c36f684d4b1860240cb5a4728841282f3b4d` | `cmp` 与原件逐字节一致 |
| `testing/d003/src/history/inject.history.cpp` | `/home/jackal/s4-fmm-accept/src/inject.cpp` | `13b2cbf5c23489c7203dcbdeb71e47103889a6fde7df6cccf6569c852da733da` | `cmp` 与原件逐字节一致 |
| `testing/d003/src/history/run-faults.history.sh` | `/home/jackal/s4-fmm-accept/run-faults.sh` | `f95b1a5b3ffe21ce3dd01b92599ba4f2a90909e75b3e11fb117cd2bc428dfaa1` | `cmp` 与原件逐字节一致 |
| `testing/d003/src/history/driver.s1b-patched.reference.cpp` | 历史原件 + `checkpoints/p05/evidence/s1b/driver-patch.diff` 重建 | `8db5afcfb99360697639346347eefdd673428a75eec6840f4d3ffbd0dfb8ab56` | 与重建结果 `cmp` 逐字节一致 |

历史原件在本轮**全程只读**（只执行了 `cp` 与 `cmp`、`sha256sum`，未写入）。

### 3.2 各轮次对驱动副本的改动（逐条标注来源）

历史驱动与注入器的改动由 S1B~S5b 的 diff 给出（证据：`checkpoints/p05/evidence/*/drv/*.diff`、`s5b/driver-s5b-vs-s5-base.diff`）。整理版驱动（`testing/d003/src/driver_d003.cpp`）逐条带标注：

| 改动 | 来源轮次 | 环境变量 | 未设置时的行为 | 证据 |
|---|---|---|---|---|
| 删除访问 `FieldCache` 的循环（`struct` 不透明） | **S1B** | — | 总是生效（必需，否则不编译） | `s1b/driver-patch.diff` |
| 重试 E/H 转储 | **S2** | `S4FMM_DUMP` | 不写文件 | `s2/drv/driver-s2-vs-history.diff` |
| 第一次调用 E/H 转储 | **S3** | `S4FMM_DUMP1` | 不写文件 | `s3/drv/driver-s3-vs-history.diff` |
| 斜入射 θ/φ | **S5** | `S4FMM_THETA`、`S4FMM_PHI` | 使用原字面量 | `s5/drv/driver-s5-vs-history.diff` |
| 偏振 s/p/mix | **S5b** | `S4FMM_POL` | 使用原字面量（s） | `s5b/driver-s5b-vs-s5-base.diff` |
| `else` 分支命中修正、`HITCOUNT` 输出 | **P05-S2** | 仅在请求注入（`S4FMM_INJECT`）时输出 | 不改变控制用例输出 | 本报告第 4.4 节 |

**默认行为核对（实测）：** 未设置任何新环境变量时，`driver-d003` 与 `driver-s1b-ref` 在全部 10 个控制用例（5 分支 × NG{9,1}）上输出**逐字节一致（10/10）**。这证明 S2–S5b 的新增代码在默认路径上透明，整理版的默认行为与 S1B 补丁版相同。

**注入相关的已知差异（实测）：** 注入用例的输出在两处不同（见第 6 节）：请求注入时输出 `S4FMM HITCOUNT n`；`else` 分支的误报文本被替换。

### 3.3 入口脚本 [实测]
`testing/d003/run_d003.sh OUT_DIR [BASE_COMMIT]`，步骤与输出：
1. `git archive` 导出基线到 `OUT/baseline-src`（不依赖工作区）。
2. 构建基线库与 pyext（仅在 `OUT` 内）。
3. 编译整理版驱动与注入器、以及参照驱动（`-Wall -Wextra` 无诊断）。
4. 运行矩阵（`matrix_d003.py run`），每个用例的原始返回码由进程直接取得。
5. 判定器自测、输出敏感性自测、分类（`classify`）、敏感性（`sensitivity`）。
6. 摘要：`SHA256SUMS`，再记录 `digests rc=`（真实返回码）。

**入口脚本的已验证事实：**
- **边界审计（`strace`，覆盖整个入口脚本一次完整运行，实测）：** 证据 `p05-s2/strace-check/entry.strace` 与 `entry-chdir.strace`（运行 `run-5`、`run-6`）。
  - `/tmp`：**打开 0 次**（含失败的打开）。
  - `/home/jackal`：成功打开 6 次，全部由 **git 子进程**（pid 15、17）读取 `~/.gitconfig` 与 `~/.config/git/ignore`。这是 `git archive` 的正常行为，**不是装置的文件依赖**；装置自身不读取 `/home/jackal` 下的任何文件。报告不把它写成"0 次"。
  - 写入：以 `chdir` 还原工作目录后，AT_FDCWD 写入共 130 次，**仓库外目标 0 个**；目录 fd 相对写入 878 次，**目录 fd 来自 `/tmp` 或 `/home` 的为 0**。
  - `execve`：装置执行的 25 个不同程序全部位于 `/usr/bin`、`/usr/libexec` 与输出目录内生成的驱动；**来自 `/tmp` 或 `/home` 的 execve 为 0**。
  - gcc 的临时文件（`cc*.s`、`cc*.o`）落在 `OUT/tmp` 内，证明 `TMPDIR` 重定向有效。
- 一次完整运行（run-4）11 个步骤全部返回 `rc=0`，摘要 956/956 通过。
- 基线构建可复现：`run-3` 与 `run-4` 的 `libS4.a` 与 `driver-d003` 逐字节一致；`libS4.a` 的 sha256 `fb9ac3f5fd2c121619bb6cd464816f97a3085c8e4a2795a2b5037b370110ffba` 与 S1 报告第 1.2 节**完全相同**（S1 报告第 48 行）。

---

## 4. S2.2 注入覆盖扩展

### 4.1 S4_malloc：链接期 `--wrap` 可行，覆盖 FMM 路径 2 个点 [实测 + 源码]

**可行性的依据（实测）：**
- `libS4.a` 中 `fmm_*.o` 对 `_Z9S4_mallocm` 有**未定义引用**（`nm -A`），可被 `--wrap` 截获。S4.o 内定义该符号（`T`）。
- `--wrap=_Z9S4_mallocm` 链接成功（rc=0）。
- 运行探针（NB=9，FFT，无注入）：经包裹的 `S4_malloc` 调用**恰好 2 次**，大小为 **6144 B** 与 **16 B**，与源码 `fmm_FFT.cpp:74`（`6*ng2` 个复数，ng2=64 → 6144 B）与 `:81`（`nshapes+1` 个 double，nshapes=1 → 16 B）一致。
- `fmm_FFT.o` 中对 `_Z9S4_mallocm` 的 `R_X86_64_PLT32` 重定位恰好两处，偏移 `0x19d` 与 `0x1ff`（`objdump -dr build/S4k/fmm_FFT.o`，对应 `call` 指令在 `0x19c` 与 `0x1fe`）。对应上述两行，行号由 debug 对象 `fmm_FFT_dbg.o` 的行表给出（`objdump --dwarf=decodedline`：`fmm_FFT.cpp` 第 74 行与第 81 行）。

**与 S3 T13 的关系（均为运行时计数）：** S3 T13 记录 NB=9 FFT 运行中 `S4_malloc` 共 18 次，其中经 FMM 调用方的 2 次（`fmm_FFT.cpp:74`、`:81`），其余 16 次经非 FMM 路径（`S4.cpp` 等）。本轮 `--wrap` 只截获 FMM 的 2 次，**不截获非 FMM 的 16 次**。这与 S3 的口径一致，但意味着 `--wrap` 的覆盖范围是"FMM 调用方的 S4_malloc"，**不是**"全部 S4_malloc"。

**注入结果（实测）：**

| 用例 | 注入 | HIT | rc | 类别 |
|---|---|---|---|---|
| `s2/s4malloc1-fft-ng9` | 第 1 次 FMM `S4_malloc`（6144 B，`fmm_FFT.cpp:74`） | 1 | 139 | **CRASH** |
| `s2/s4malloc2-fft-ng9` | 第 2 次 FMM `S4_malloc`（16 B，`fmm_FFT.cpp:81`） | 2 | 139 | **CRASH** |
| `s2/s4malloc3-fft-ng9` | 第 3 次（不存在，FMM 只有 2 个点） | 0 | 1 | **INVALID**（未命中，驱动报告 `requested injection was reached` 失败） |

**崩溃的机制 [源码]：** `FMMGetEpsilon_FFT` 直接使用 `S4_malloc` 的返回值，不检查 NULL（`fmm_FFT.cpp:74,81` 无检查，与 S1 报告第 2.4 节一致）。这是被测代码的缺陷表现，不是注入器造成。

> **口径说明：** 上表 `s2/s4malloc1/2/3` 的期望类别是在手工运行观察到结果**之后**写入矩阵表的（`matrix_d003.py` 中已标注 `observed`）。它们是"已观察的复现"，不是盲测预先登记。

### 4.2 LinearSolve：**未覆盖，需要生产侧 seam，等待批准** [实测 + 源码]

任务书要求评估三种做法。结论如下（每种都有实测）：

| 做法 | 结论 | 依据（实测） |
|---|---|---|
| (a) 链接期替换（`--wrap`） | **不可行** | `fmm_FFT.o` 与 `fmm_kottke.o` 中 `RNP::LinearSolve<'N'>::LinearSolve<std::complex<double>>` 为**本地弱符号 `W`**（`nm`），没有未定义引用可供 `--wrap` 改写。构造函数是头文件内的模板，每个翻译单元各自实例化。 |
| (b) 测试专用头 | **不可行** | `fmm_FFT.cpp:28` 与 `fmm_kottke.cpp:30` 使用相对包含 `"../RNP/LinearSolve.h"`。用 `-I` 放置的同名覆盖头（内含 `#error`）**未被包含**（`g++ -fsyntax-only` rc=0，无 `#error` 输出）。 |
| (c) 构造奇异输入，不注入 | **未找到可行输入** | `eps=0` 的材料（`t4_zero_eps` 探针）运行 rc=0，未触发零主元。`LinearSolve` 在奇异矩阵上确实返回 `info=2`（`t5_sing` 探针，正确），但要让 `Epsilon2` 在 `fmm_FFT.cpp:204` / `fmm_kottke.cpp:279` 奇异，需要特定几何，且无法保证只落在这两处。 |

**结论：** 按任务书第一节的停止规则，LinearSolve 的注入需要**生产侧的测试专用 seam**。本阶段**未实施**，见第 7 节。

**LinearSolve 的依据补充 [源码]：** 默认 Linux 构建未定义 `RNP_HAVE_LAPACK`（`Makefile.common` 与 `Makefile.Linux` 中无该定义，`grep` 核对），因此 `S4/RNP/LinearSolve.h:56` 的 `#ifdef RNP_HAVE_LAPACK` 分支不生效，使用**通用模板**。通用模板在零主元时设 `info = j+1` 并跳过三角求解（`LinearSolve.h` 第 12–44 行）。

### 4.3 plan / exec 两步分支 [实测]
- **plan**（`fft_plan_dft_2d` 内的真实分配，`arm==1`）：保留。5 个分支的 `plan1` 用例全部 CRASH（NB=9）。
- **scratch**（`fft_plan_exec` 内 16 B 真实分配，`arm==2`）：保留。`scratch1`、`scratch2`（fft NB=1）为 SILENT_SWALLOW。
- **exec**（`fft_plan_exec` 直接返回 1，**边界模拟**）：保留，并在判定中标注 `(boundary simulation)`，不计入真实缺陷。`exec1` 五个分支为 SILENT_SWALLOW（边界模拟）。

### 4.4 命中计数与"未命中判无效" [实测]
- 注入器维护只读计数 `s4fmm_inject_hits()`（`inject_d003.cpp:43`）。
- 请求注入时（`S4FMM_INJECT` 非空），驱动输出 `S4FMM HITCOUNT n`（`driver_d003.cpp:208`）。
- **未命中判无效**：`driver_d003.cpp:231` 与 `:249` 在"请求了注入但 hits=0"时输出 `RESULT injection requested but not reached` 并判 FAIL。实测见 `s2/s4malloc3`（HITCOUNT 0，rc=1）。

---

## 5. S2.3 覆盖 5 个分支与偏振

### 5.1 分支与驱动配置的准确表述（勘误）
驱动 `FMM_MODE` 的映射（`driver_d003.cpp:53–57` 的 `make_stack` 中，与历史驱动 `driver.history.cpp:54–56` 相同）：
- `fft` → 仅设 `use_discretized_epsilon=1`，**不进入 PolBasis**。
- `kottke` → `use_discretized_epsilon=1` 且 `use_subpixel_smoothing=1`。
- `jones` / `nv` / `vl` → `use_polarization_basis=1` 并设对应基标志。

**勘误：** S5 与 S5b 把驱动配置写成"VL 分支"是不准确的。驱动 `fft` 模式**不**进入 `PolBasis`（`S4.cpp:2374–2381`，`fft` 只调用 `FMMGetEpsilon_FFT`）。"VL 分支"的证据来自 S5 的 **Python 矩阵**与 gdb 计数（`s5/t21/branch-VL-count.gdb.txt`，`VL=1, NV=0, Jones=0`），而不是驱动的 fft 模式。本报告的驱动 fft 结果**不得**被解读为"VL 分支"。

### 5.2 五个分支的注入与控制 [实测]
| 分支 | 控制（NG9） | plan1（NG9） | exec1（NG9，边界） |
|---|---|---|---|
| fft | CONTROL_OK | CRASH | SILENT_SWALLOW |
| kottke | CONTROL_OK | CRASH | SILENT_SWALLOW |
| jones | CONTROL_OK | CRASH | SILENT_SWALLOW |
| nv | CONTROL_OK | CRASH | SILENT_SWALLOW |
| vl | CONTROL_OK | CRASH | SILENT_SWALLOW |

（NG1 控制：fft、kottke、jones、nv 为 CONTROL_OK；`vl` NG1 为 INVALID，原生失败 rc=20，与 O-1 一致，见第 6 节。）

### 5.3 偏振 s / p / mix 的输出敏感性 [实测]
驱动 `S4FMM_POL`（`driver_d003.cpp` 的 `make_stack`），θ=30°，NB=1，fft，first-call E/H（144 个元素，阈值 1e-12）：

| 比较 | 判定 | 元素超阈值 | max\|diff\| | 期望 | 依据 |
|---|---|---|---|---|---|
| s vs s（控制） | INSENSITIVE | 0 / 144 | 0 | INSENSITIVE | 对照 |
| p vs s | SENSITIVE | 144 / 144 | 1.0925 | SENSITIVE | 预先登记 |
| mix vs s | **MIXED** | 72 / 144 | 1.0925 | MIXED | **修正期望**，依据 S5b digest 第 16 行 `mix-phi0 n_diff=72` |

**关于 mix 的期望修正（必须披露）：** 我最初把 mix 的期望写为 SENSITIVE。核对 S5b 的 digest（`S5B_DIGEST_SECTION.txt` 第 16 行，`mix-phi0 B(vs A): n_diff= 72`）与 S5b 原始文件（`A-s-phi0.eh` 与 `A-mix-phi0.eh` 复算，同为 72）后，修正为 MIXED。这一修正发生在**看到本装置结果之后**，依据是独立的 S5b 记录，不是盲测预先登记。

**S5b 的 P1 与本轮数字的关系（已厘清）：** S5b 的 P1 比较的是"p 偏振的 A（无改值）"与"B（手动写入 `Epsilon_inv[0]=1`）"，`max|A−B|=0.2634`（S5b 原始文件复算一致，72 个元素超阈值）。本轮的 1.0925 是"p 偏振与 s 偏振"的差异，**两者测量的量不同**。本报告不把它们混用。

### 5.4 PolBasis 路径的输出敏感性（新增用例，基线判定的一部分）[实测]
NB=9，θ=30°，first-call E/H，s vs p：

| 分支 | 判定 | 超阈值 | max\|diff\| | 期望 |
|---|---|---|---|---|
| vl | SENSITIVE | 144 / 144 | 2.7097 | SENSITIVE（预先登记） |
| jones | SENSITIVE | 144 / 144 | 2.6122 | SENSITIVE（预先登记） |
| nv | SENSITIVE | 144 / 144 | 2.9180 | SENSITIVE（预先登记） |

**篡改检验（实测）：** 把真实的 p 输出替换为 s 输出（模拟偏振输入被吞掉），判定变为 INSENSITIVE，并被规则检出为失败（`judge_d003.py` 与 `p05-s2/run-4` 的敏感性表）。

### 5.5 未覆盖项 [实测]
- **Epsilon_inv 的手动写入敏感性**（S5b P1/P4 的完整复现）：未在本装置中重做。原因：S5b 的手动写入使用 gdb 断点，依赖带调试信息的 O0 构建（`S4.cpp:2375`、`rcwa.cpp:823`），本装置的基线为 O3 无调试信息。重做需要新的 O0 构建，属于 S5b 的内容，**S2 不自立新阶段**，故未做。S5b 的结论保持原状，不被本报告改写。

---

## 6. S2.4 基线失败判定器

### 6.1 判定器 [源码 + 实测]
`testing/d003/judge_d003.py`。类别（优先级自上而下）：

| 类别 | 条件 |
|---|---|
| INVALID | 控制用例不干净（hit≠0 或 rc1≠0 或非信号的 rc≠0）；或注入未命中（hit=0） |
| CRASH | 注入命中且 `rc ≥ 128`（信号终止） |
| SILENT_SWALLOW | 注入命中且 `rc1 == 0`（非信号终止）。**不读取驱动自身的 PASS/FAIL 退出码** |
| REPORTED_FAILURE | 注入命中且 `rc1 ≠ 0` |
| CONTROL_OK | 控制用例，rc=0，rc1=0，hit=0 |

**关于"不读取驱动退出码"的修改（必须披露）：** 第一版判定器把 SILENT_SWALLOW 写成 `rc == 0 and rc1 == 0`。驱动修正后对"命中但静默"判 FAIL（rc=1），导致 7 个真实的静默吞掉被误判为 INVALID（`run-1-before-judge-fix/index.txt`，保留为证据）。根因是判定器把驱动的判定退出码当作被测代码的行为。修正为只依赖事实（`rc1` 与是否信号终止）。该修正由设计错误引起，**不是**为迎合期望值而改；修正后的规则在 S1B 的原始定义（rc=0）下与之前相同，只改变了 S1B 中不存在的"rc=1 且 rc1=0 且命中"情形。

### 6.2 判定器自测 [实测]
- `judge_d003.py selftest`：**19 项全部 ok**（日志 `run-4/logs/judge.log`，按 `judge_d003.py` 中 `expect(...)` 的实际条目分组：夹具 9 项，覆盖 CRASH、SILENT_SWALLOW（边界与真实）、驱动 FAIL 但静默（边界与真实）、REPORTED_FAILURE、CONTROL_OK、未命中 INVALID、VL NB1 原生失败 INVALID；篡改/灵敏度 5 项；解析 5 项）。
- `judge_d003.py selftest-sensitivity`：**7 项全部 ok**（相同输入 INSENSITIVE、全部元素变化 SENSITIVE、部分变化 MIXED、篡改检出、低于阈值的噪声、重复键与未知标签拒绝）。

### 6.3 S1B 22 个用例的对照 [实测]

S1B 索引共 27 行：T4 对照 10 行、T5 注入 12 行、T6b 5 行。任务书的"22 个用例"对应 **T4 + T5（10 + 12 = 22）**；T6b 为 VL NB 阈值扫描，不计入。

**类别对照：22/22 一致（0 处不一致）。**

**原始字段对照（rc / rc1 / rc2 / hit）：** 归一化 `none`/`None` 后，**15/22 完全相同，7/22 不同**，全部为 `rc` 字段：

| 用例 | S1B rc | 新装置 rc | rc1/rc2/hit |
|---|---|---|---|
| t5/exec1-fft-ng9 | 0 | **1** | 0/0/1（一致） |
| t5/exec1-kottke-ng9 | 0 | **1** | 0/0/1（一致） |
| t5/exec1-jones-ng9 | 0 | **1** | 0/0/1（一致） |
| t5/exec1-nv-ng9 | 0 | **1** | 0/0/1（一致） |
| t5/exec1-vl-ng9 | 0 | **1** | 0/0/1（一致） |
| t5/scratch1-fft-ng1 | 0 | **1** | 0/0/1（一致） |
| t5/scratch2-fft-ng1 | 0 | **1** | 0/0/1（一致） |

这 7 个 `rc` 变化是**驱动修正的直接结果**：驱动在"命中但 rc1=0"时判 FAIL（退出码 1），而 S1B 旧驱动在同一情形输出 PASS（退出码 0）。`rc1`、`rc2`、`hit` 三项均未变。

**S1B 的 PASS 为误报（实测，7 个日志）：** S1B 的 `exec1` ×5、`scratch1`、`scratch2` 日志同时含 `HIT≥1`、`RESULT no injection fired` 与 `RESULT ... PASS`。这正是 S1B 附录 b.1 指出的"PASS 对注入用例没有判别力"，新装置已修正（判 FAIL，文本为 `injection reached, rc1 0 (failure swallowed)`）。

**与 S1B index 的字段差异的第二个来源：** 新装置的 `plan1` 的 `rc1/rc2` 输出为 `None`（Python 字符串化），S1B 为 `none`。这是表示差异，已归一化，不是数值差异。

### 6.4 修正前后的证据保留 [实测]
- `run-1-before-judge-fix/`：判定器第一版（依赖驱动退出码）的结果，7 个 INVALID 误判被保留。该目录由 `run-1` 改名而来，**内部记录引用旧目录名**（已在第 8 节披露）。
- `run-2/`：修正后的判定器，但缺敏感性步骤。`run-2` 的摘要在 `digests` 时序缺陷下有 `STEPS.txt: FAILED`（同 run-3）。
- `run-3/`：加入敏感性步骤后的完整运行，摘要仍有 `STEPS.txt: FAILED`（摘要时序缺陷，第 8 节）。
- `run-4/`：修正摘要时序后的最终运行。**`sha256sum -c` 956/956 通过。**

---

## 7. 需要停下来等批准的事项

### 7.1 LinearSolve 的生产侧 seam（**需要批准，未实施**）

按任务书第一节，`LinearSolve` 的注入必须有生产侧 seam，**先停止**，附上所需的最小 seam：

- **文件与行：** `S4/fmm/fmm_FFT.cpp:204`、`S4/fmm/fmm_kottke.cpp:279`（`RNP::LinearSolve<'N'>(n,n, Epsilon2,n, Epsilon_inv,n, &solve_info, NULL);`）。
- **最小改动（草案，未实施）：** 在 `S4/RNP/LinearSolve.h` 的通用模板的 LU 循环之后、`*info = iinfo` 之前，增加一个由宏控制的测试钩子，例如：
  ```c
  #ifdef S4_TEST_LINEARSOLVE_SEAM
  extern int s4_test_linearsolve_force_info(void);  /* returns 0 = no injection */
  if (0 != s4_test_linearsolve_force_info()) { iinfo = s4_test_linearsolve_force_info(); }
  #endif
  ```
  或者在 `fmm_FFT.cpp:204` 与 `fmm_kottke.cpp:279` 的调用点包一层 `#ifdef` 的测试函数。两者都需要改 `S4/`。
- **`#ifdef` 方案：** 宏 `S4_TEST_LINEARSOLVE_SEAM` 只在测试构建中定义（如 `testing/d003/run_d003.sh` 的专用构建），默认构建不定义，因此默认构建的代码路径与现在**逐字节相同**（需由 `nm` 与输出对比验证）。
- **为什么链接期 `--wrap` 不够（实测，第 4.2 节）：** `RNP::LinearSolve` 的构造函数是头文件中模板的**本地弱符号**，各翻译单元各自实例化，没有可供 `--wrap` 截获的未定义引用。

**需要用户决定：** (i) 是否批准该 seam 进入 `S4/`；(ii) 或接受 LinearSolve 在 D003 装置中**不覆盖**，记为限制。本报告不替用户做这个决定。

### 7.2 其他需要用户确认的事项
- **是否接受"S4_malloc 注入只覆盖 FMM 调用方的 2 个点"**。口径说明（三个数字各自的含义，不可混用）：
  - **17**：`S4/fmm/*.cpp` 中**静态**的活跃调用行（排除以 `//` 开头的注释行后的精确计数，`S1_BASELINE_AND_ENUMERATION.md` 第 2.4 节一致）。原始 grep 为 19，差额为 `fmm_kottke.cpp:76` 与 `fmm_PolBasisJones.cpp:336` 两行注释。
  - **2**：NB=9 FFT 运行中，**经过 FMM 调用方**且被 `--wrap` 截获的**运行时**次数（`fmm_FFT.cpp:74`、`:81`）。
  - **18**：同一运行中 `S4_malloc` 的**运行时**总次数（S3 T13）。其中 16 次不经 FMM 调用方，不在本装置覆盖范围内。
  - 静态的非 FMM 调用点（如 `S4.cpp`）数量更多，本报告未逐一统计，不作结论。
- **是否接受 `rc` 字段的 7 个差异**作为驱动修正的披露（第 6.3 节）。
- **是否接受 mix 的期望修正**（第 5.3 节）。

---

## 8. 偏离项（必须逐条披露）

1. **误写 `/tmp`（至少 4 次，均违反"不写 /tmp"的约束）。** (a) `/tmp/x`：`cp` 的目标，源路径错误导致未创建；(b) `/tmp/__nope`：`sh run_d003.sh … > /tmp/__nope` 的重定向，未生成文件；(c) `/tmp/__ev_check_ignored`：`sha256sum -c … > /tmp/…` 的重定向，未生成文件；(d) `/tmp/__files_a`：检查 run-3 未摘要文件时 `find … > /tmp/__files_a 2>/dev/null` 的重定向，未生成文件。四个路径在报告撰写时均经绝对路径核对为**不存在**，`/tmp` 中无本项目残留。但每一次都是违规操作，如实记录。（初稿写为"共 3 次"，经逐条回查后修正为至少 4 次。）
2. **误判后台运行的状态。** 一条带 `/tmp` 重定向的命令实际运行了完整的入口脚本，并写入 `run-2`。我起初误以为它未执行。`run-2` 因此保留，并作为修正后判定器的运行证据（时间戳 02:42，晚于修正）。
3. **`run-1` 改名为 `run-1-before-judge-fix`。** 该目录内部的记录（`STEPS.txt`、`index.txt`、`SHA256SUMS`）引用旧目录名。改名是为保留"修正前"的证据，**内部路径未改写**，应以此理解。
4. **归档被误生成后删除。** `tar` 的参数顺序错误使一个未经校验的归档被写入；我按绝对路径核对后删除，并用正确命令重新生成、校验（414 条，逐一哈希一致）。
5. **`.git/info/exclude` 未改动**（开始与结束的 sha256 均为 `a18e6a2b…`）。
6. **`/home/jackal/s4-fmm-accept/` 为只读访问**（`cp` 与 `cmp`），未运行其中任何文件（`execve` 审计：来自 `/home` 的 execve 为 0，见第 3.3 节）；历史 `run-faults.sh` 仅作为副本入库，不被执行。
6a. **审计的范围。** `strace` 审计只覆盖入口脚本及其子进程。偏离项 1 中的 `/tmp` 写入尝试发生在交互 shell 的命令重定向中，**不在该审计范围内**，其"未留下文件"的结论依据是逐一的绝对路径核对。
7. **`s4malloc` 行的期望为"已观察"而非"盲测"**（第 4.1 节，矩阵表中已标注）。
8. **mix 的期望在看到结果后修正**（第 5.3 节）。
9. **判定器在中途修改**（第 6.1 节）：由设计错误引起，修改前后的结果均保留。
10. **敏感性自测的结构错误**：`selftest-sensitivity` 的入口块在函数定义之前，执行报 `NameError`（已修正，入口块移到文件末尾）。
11. **摘要的时序缺陷**（run-3 的 `STEPS.txt: FAILED`）：`digests` 在 `STEPS.txt` 追加前计算摘要。已修正（run-4），run-3 保留为缺陷证据。
12. **`digests` 步骤曾硬编码 `rc=0`**：这是我写的错误，违反"记录真实返回码"的要求。已改为 `$?` 捕获，run-4 中为真实值。
13. **报告初稿中的源码行号有误**：`S4.cpp:2390/2395` 实为 2391/2393；`numalloc.c:49` 实为 `:68`。已逐条回查修正（第 9 节列出的行号均已核对）。
14. **`EVIDENCE.sha256` 的覆盖范围初稿不完整**：只含 S2 归档，未含既有 7 个归档。已补入（1048 条）。
15. **文件权限**：`testing/d003/` 的文件曾为 `600`（工具写入的默认值），已统一为 `644`/`755`，内容摘要前后不变（已核对）。

**提交顺序的偏离：** 任务书要求"装置与报告可分两个提交"。本报告引用的 `git diff --stat` 结果（第 10 节）需要在提交后才能填写，因此本报告先于提交写成，其中的提交前后差异需要用户复核。

---

## 9. 路径与可复核清单

### 9.1 装置（将提交）
- `testing/d003/run_d003.sh`（入口）
- `testing/d003/matrix_d003.py`（矩阵运行器，22 + 3 + 6 用例）
- `testing/d003/judge_d003.py`（判定器，含自测与敏感性）
- `testing/d003/src/driver_d003.cpp`（整理版驱动）
- `testing/d003/src/inject_d003.cpp`（整理版注入器）
- `testing/d003/src/history/`（历史副本与参照驱动，逐字节核对）

### 9.2 证据（不提交，被 exclude 忽略）
- `checkpoints/p05/evidence/p05-s2/run-4/`：**最终运行**（index、sensitivity、STEPS、SHA256SUMS、logs、runs）。
- `checkpoints/p05/evidence/p05-s2/run-3/S1B_COMPARE_22_FINAL.txt`：22 个用例与 S1B index 的逐字段比对（该比对由 run-3 的 index 生成；run-4 的 index 与之相同，已核对 `index.txt` 的 case..hit 列逐行一致）。
- `checkpoints/p05/evidence/p05-s2/work/`：LinearSolve 评估探针、`--wrap` 验证、设计底稿（`design/DESIGN_NOTES.txt`、`design/CLASSES.txt`）、敏感性表。
- `checkpoints/p05/evidence/p05-s2/ARCHIVE_LIST.txt`：归档的 414 个文件清单。
- `checkpoints/p05/evidence/p05-s2/run-5/`、`run-6/`：两次独立的完整复跑（审计用），其 index、敏感性与 `libS4.a` 哈希与 run-4 逐项一致；摘要各自 956/956 通过。
- `checkpoints/p05/evidence/p05-s2/strace-check/`：边界审计的原始 `strace` 记录（`entry.strace`、`entry-chdir.strace`）。
- `checkpoints/p05/evidence/p05-s2/AUDIT_EVIDENCE.sha256`：run-5、run-6 与 strace 证据的独立清单（106 条，`AUDIT_EVIDENCE.verify.txt` 全部 OK）。该清单**不纳入** `EVIDENCE.sha256`（1048 条），以保持报告中已引用的哈希与计数不变。
- `checkpoints/p05/evidence/archive/evidence-p05-s2.tar.gz`：本阶段增量归档（sha256 `5144397de84c99396b31c81898f036610e34d9ac174dd13829d7c80b8e8e147c`）。**增量**：只含 S2 新增文件，不替代既有全量证据。
- `checkpoints/p05/evidence/EVIDENCE.sha256`：**1048 条**，`sha256sum -c` 全部 OK（`p05-s2/work/EVIDENCE.verify-final.txt`）。

### 9.3 本阶段的子任务（不自立新阶段）
- S4_malloc 的 `--wrap` 可行性与 FMM 2 点覆盖（S2.2）。
- LinearSolve 三种做法的评估（S2.2）。
- 输出敏感性（p/s/mix 与 PolBasis，S2.3）。
- 判定器自测与灵敏度（S2.4）。
- 基线构建可复现性核对（与 S1 报告第 1.2 节的哈希比对）。

---

## 10. 提交后的复核（待填写）

提交后需要用户复核以下命令的输出（本节在提交前无法填写）：

```
git diff --stat 5b72793 HEAD
```

应当只出现 `checkpoints/p05/` 与 `testing/d003/` 下的文件。

*本节由提交者在提交后补写，或由用户复核。*
