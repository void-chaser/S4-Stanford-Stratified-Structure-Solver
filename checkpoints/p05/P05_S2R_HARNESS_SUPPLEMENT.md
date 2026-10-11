# P05-S2R 补充轮报告：D003 测试装置补强（P05-S2 子任务）

> **状态：未完成，等待用户审核。** 本报告不宣布 P05-S1、P05-S2、P05-S3、P05-S4 中任何一个阶段完成。
> 本轮是正式阶段 **P05-S2（测试装置）** 的补充子任务，不是新阶段；P05 固定五阶段 S1–S5，未引入 S6。
> 本报告只报告装置的灵敏度与红/绿事实，**不对 D003 的修复效果作验证结论**。修复属于 P05-S3 补充轮，验证属于 P05-S4。
> 分支：`codex/p05-d003-fft-error-propagation`
> 起点 HEAD：`8d60dfb9ece24994b65db0e3c7a3fdf6be286ebd`（已核对，工作区开始时干净）
> 基线：`37a82e8`（5b72793 的后继，`8d60dfb` 的祖先，已核对）
> 证据目录：`checkpoints/p05/evidence/p05-s2r/`（被 `.git/info/exclude` 忽略，**未提交**）

来源标注：**[实测]** 本轮运行或读取的原始输出；**[源码]** 只读阅读源码并逐行回查；**[推断]** 由实测与源码得出，未直接验证；**[未验证]** 本轮无证据。

---

## 0. 阶段定义依据、编号对照与未完成声明

### 0.1 阶段定义的依据 [用户提示]

- P05 五阶段定义**依据用户提示词**（本轮任务书给出的 P05-S1 至 P05-S5 定义）。
- **仓库内不存在 P05 原始计划文档。** 这是已核实的事实：`step0_search_for_original_plan.txt` 记录了工作树（`*.md` 与非 md 文本）、`PROJECT_ROADMAP.md`（其 P05 为项目级 P01–P14 编号，"Phase 2 A：D003"，与五阶段编号体系不同）、git 历史（`-S"P05-S"` 唯一命中 `P05_S2_TEST_HARNESS.md`）与本地归档的搜索结果。
- 因此本报告**不**声称阶段定义来自仓库原文。本轮未凭记忆转述原文；阶段定义直接引用用户提示词。
- 用户已确认该定义（任务书第 0 节）。

### 0.2 与本轮相关的阶段定义（用户提示词，逐字摘录）

- **P05-S2 测试装置**：扩展注入器覆盖 S4_malloc、LinearSolve 与两步分支，接入仓库测试目录，源码仅改 testing/ 并允许必要的测试专用 seam。
- **P05-S3 最小修复**：从候选分支移植到 Master，补齐缺口，FMM 改动与 S4.cpp 调用点改动分开提交，源码需修改。

### 0.3 新旧编号对照表（编号与文件名，不重做 S1–S5 内容对账）

| 历史轮次 / 文件名 | 归属正式阶段 |
|---|---|
| S1 / S1B / S2 / S3 / S4 / S5 / S5b（`S1_*.md` … `S5B_*.md`，历史轮次文件名） | P05-S1 证据扩展 |
| 历史 `S3_OPEN_ITEMS_AND_SCOPE_FREEZE.md`（T11–T15） | P05-S1 证据扩展（与正式阶段 P05-S3 **不是同一件事**） |
| P05-S2 报告 `P05_S2_TEST_HARNESS.md`（含 S2.6 附录） | 正式阶段 P05-S2 |
| P05-S3 报告 `P05_S3_MINIMAL_FIX.md` | 正式阶段 P05-S3 |
| **本报告 `P05_S2R_HARNESS_SUPPLEMENT.md`** | **正式阶段 P05-S2 的补充子任务（S2R）** |

- 本轮补充内容全部写入新文件；历史报告与文件名未改写。
- 文件名中的 "S2R" 是本轮子任务标识，不是新阶段。

### 0.4 起点核对 [实测]

- `git rev-parse HEAD` = `8d60dfb9ece24994b65db0e3c7a3fdf6be286ebd`，分支 `codex/p05-d003-fft-error-propagation`。
- `git merge-base --is-ancestor 37a82e8 HEAD` = yes。
- 基线树 `37a82e8` 用 `git archive` 导出后构建 `libS4.a`，sha256 = `fb9ac3f5fd2c121619bb6cd464816f97a3085c8e4a2795a2b5037b370110ffba`，**与要求的值完全一致**（门禁通过）。
- 当前树 `8d60dfb` 导出构建的 `libS4.a`，sha256 = `865c58938e18220a3e7f02f7cb7b05cf83bce36ec28005fcf0bb4f1b4701b1da`（与基线不同，预期：FMM 与 S4.cpp 的修复改变了目标代码）。

---

## 1. 用户授权（本轮）

- 用户批准 LinearSolve 注入 seam，方式限定为：补丁由 `testing/d003/seam/` 下的脚本**仅**应用到 `git archive` 导出的副本；生产树 `S4/` 零改动。
- 宏未定义时，导出副本的预处理输出与无补丁逐字节一致，并给出阳性对照（本报告 R2-B）。
- 本轮**未修改 `S4/` 下任何文件**（R2-F 收尾核对，见第 10 节）。
- 用户要求"最高标准"：每个结论有基线与修复树两侧证据；每个注入点有命中确认；所有限制逐项披露。

---

## 2. R2-A 注入点总表（INJECTION_POINTS.txt）[源码 + 实测复核]

产出文件：`checkpoints/p05/evidence/p05-s2r/INJECTION_POINTS.txt`（证据目录，未提交）。

### 2.1 方法 [源码]

- 用一个只读的 grep 式枚举器（`enum_base-37a82e8.json`、`enum_cur-8d60dfb.json`，机器生成，**未手抄**）在两棵树上复核全部分配与调用点。
- 范围判据（任务书第 1 节）：一个点，只要处于 D003 验收路径（其失败影响"模式是否被安装"或"缓存是否被安装"），或位于 FMM/FFT 失败传播链上，即纳入；边界不清的标 **边界待用户裁决**，本报告不自行裁决。

### 2.2 两树复核的数字 [源码，机器计数]

| 类别 | BASE (37a82e8) | CUR (8d60dfb) |
|---|---|---|
| S4_malloc（FMM 目录） | 17 | 17（其中 16 已检查、1 未检查 `fmm_experimental:40`） |
| fft_alloc_complex（kottke） | 1 | 1（已检查） |
| fft_plan_dft_2d | 5 | 5（全部已检查） |
| fft_plan_exec | 10 | 10（全部已检查） |
| FMMGetEpsilon 返回（S4.cpp） | 10（全部丢弃） | 10（全部接收到 fmm_ret） |
| LinearSolve：solve_info | 2 | 2（已消费） |
| LinearSolve：info=NULL | 7 | 7（未处理，边界） |
| ComputeLayerModes 通用分配（S4.cpp） | 4 | 4（未处理） |
| AddFieldToCache 分配（S4.cpp） | 1 | 1（未处理） |
| **合计** | **57** | **57** |

**与 S1 的 47、S3 的 44 对账 [源码 + 算术]：**
- S1 的 47 = plan 5 + exec 12 + FMMGetEpsilon 11 + FMM S4_malloc 17 + solve_info 2。grep 复核得 5 + 10 + 10 + 17 + 2 = **44**，与 S3 的 44 一致。S1 偏高（exec 12 → 10，FMMGetEpsilon 11 → 10），原因见 `checkpoints/p05/evidence/p05-s3/S1_47_RECONCILIATION.txt`（P05-S3 轮次证据）。
- 本轮新增类别：info=NULL 7 + fft_alloc_complex 1 + ComputeLayerModes 4 + AddFieldToCache 1 = **13**。
- 44 + 13 = **57**，与枚举器行数一致。

### 2.3 当前树状态与边界 [源码]

- 已处理（handled）：44 行。未处理（not-handled）：13 行（ComputeLayerModes 4、AddFieldToCache 1、info=NULL 7、fmm_experimental S4_malloc 1）。
- **边界待用户裁决（8 行）**：info=NULL 的 7 处（它们是 FMM 数值链上的点，但对"模式/缓存是否安装"的直接作用未确立）；fmm_experimental:40（驱动不可达）。

### 2.4 驱动可达性的修正 [源码 + 实测]

- 驱动（`driver_d003.cpp`）的 lattice 固定为 `{1,0,0,1}`（2-D）；`FMM_MODE` 只设置 `use_discretized_epsilon` / `use_subpixel_smoothing` / `use_polarization_basis`；材料只有 `SCALAR_REAL`。
- `use_experimental_fmm` 默认 0（`S4.cpp:348`），只有 Lua 前端会设置（`main_lua.c:2552/2554`）。驱动不设置 → `fmm_experimental` **驱动不可达**（与 S2b 一致）。
- 驱动 `pattern` 栈会在 Slab 层放一个圆形夹杂（`nshapes=1`），因此只有 `pattern` 栈能进入 FMM 非均匀分支；`flat` 栈只走均匀分支（`nshapes=0`）。这一点在 R2-B/C 中曾因误用 `flat` 而出错，已在第 6 节披露。

---

## 3. R2-B LinearSolve seam 落地 [源码 + 实测]

### 3.1 产物

- `testing/d003/seam/apply_seam_r2.py`（新文件，本轮提交）。**不修改**既有的 `apply_seam.py` 与 `linearsolve_seam.patch`（sha256 复核保持不变，见第 10 节）。
- `testing/d003/src/inject_d003.cpp`（扩展：新增家族 B 与家族 C 的钩子；家族 A 原样保留）。

### 3.2 三个互相独立的家族 [源码]

| 家族 | 宏 | 钩子 | 站点 | 说明 |
|---|---|---|---|---|
| A（solve_info） | `S4_TEST_LINEARSOLVE_SEAM` | `S4_TEST_LINEARSOLVE_AFTER(site,&solve_info,…)` | fmm_FFT:209（site 1）、fmm_kottke:284（site 2） | 与 S2.6 seam 相同锚点与钩子 |
| B（info=NULL） | `S4_TEST_LINEARSOLVE_SEAM_NULLINFO` | `S4_TEST_LINEARSOLVE_NULLINFO_AFTER(id,out,n,ld,model)` | closed:130/133/138/235、PolBasisJones:369、NV:260、VL:268（id 11–17） | 模型 1（RHS 在求解前被置为单位阵）与模型 2（RHS 为计算值）分开，见 `R2B_LINEARSOLVE_SITE_MODEL.txt` |
| C（S4.cpp 分配） | `S4_TEST_ALLOC_SEAM` | `S4_TEST_ALLOC_HOOK(id,size)` | S4.cpp:2267/2295/2408(BASE 2402)/2425(BASE 2419)/3977(BASE 3971)（id 21–25） | 以 `#ifdef/#else/#endif` 包裹，`#else` 为原始文本 |

- 家族之间的前缀不相互冲突（已核对：`linearsolve:`、`linearsolve_null:`、`alloc:` 互不为前缀）。

### 3.3 锚点唯一性 [实测]

- 两棵树的 `--check-only` 均 rc=0，**锚点失败 0**（`grep -c 'ANCHOR ERROR'` = 0）。
- 站点数：两棵树各 **14**（家族 A 2 + 家族 B 7 + 家族 C 5）。
- 重复的调用文本（`closed.cpp:138` 与 `:235`，文本逐字相同）以"调用行 + 其后一行"作为唯一锚点，已用精确字节核对。
- 行号漂移（基线与当前树的 S4.cpp 行号不同，例如家族 C 的 BASE 2402/2419/3971 对应 CUR 2408/2425/3977）：锚点按内容匹配，两树都正确解析。

### 3.4 默认路径的字节一致性（R2-B 要求）[实测]

| 检查 | 结果 |
|---|---|
| 宏未定义，修复后未插桩 vs 插桩，`g++ -E -P`（6 个 FMM 文件，当前树） | **6/6 逐字节一致**（FFT 1310077 B 等） |
| 同上，基线树 37a82e8 | **6/6 逐字节一致** |
| 宏未定义，S4.cpp（家族 C 的编辑所在文件），当前树 | **逐字节一致**（1403658 B） |
| 所有 24 个目标文件（三家族全部插桩、宏未定义），对照纯净构建 | **24/24 目标文件逐字节一致** |

### 3.5 阳性对照（宏定义时必须不同）[实测]

| 检查 | 结果 |
|---|---|
| 宏定义（家族 A+B），FFT/closed 预处理 | 与纯净版**不同**（预期） |
| 仅定义家族 C，目标文件 | 仅 **`S4.o`** 改变（归属正确：只有 S4.cpp 含家族 C 的站点） |
| 三家族全部定义，目标文件 | 24 个中 **17 个逐字节一致、7 个不同**：`fmm_closed.o`、`fmm_FFT.o`、`fmm_kottke.o`、`fmm_PolBasisJones.o`、`fmm_PolBasisNV.o`、`fmm_PolBasisVL.o`、`S4.o`，恰为被插桩的 6 个 FMM 文件加 S4.cpp（`objcmp5/`，[实测]） |

### 3.6 独立性与旧制品的保留 [实测]

- 家族 A/B/C 的宏互不激活其他家族（已测：仅定义家族 A 时，closed.cpp 中家族 B 钩子计数为 0）。
- 既有 `apply_seam.py` 与 `linearsolve_seam.patch` 的 sha256 与本轮开始前相同（见第 10 节）。

---

## 4. R2-C 分配类注入扩展 [实测 + 源码]

### 4.1 `--wrap` 与同翻译单元的限制 [实测]

- `S4.o` **定义** `_Z9S4_mallocm`（`T`），`S4.o` 内对它的调用在同一目标文件内解析，**`--wrap` 无法截获**（`nm`：S4.o 中该符号为 T，且其 undefined 引用为 0）。
- 7 个 FMM 目标文件对 `_Z9S4_mallocm` 有 `U` 引用；对应 17 个调用重定位（fft 2、kottke 1、closed 1、jones 4、nv 4、vl 4、experimental 1），与 17 个 S4_malloc 调用点一一对应（objdump 核对）。
- 因此：FMM 的 16 个可达 S4_malloc 点可由 `--wrap` 截获；S4.cpp 的 5 个分配点只能由家族 C 的 seam 注入。

### 4.2 家族 C 的可行性门 [源码]

- 锚点唯一：5 个站点在两棵树上均唯一匹配。
- 忠实性：每个站点的 NULL 之后紧随解引用（2267→`pB=*layer_modes`；2295→`pB->kp=pB->q+n2`；2408/2425→作为工作区传入 `SolveLayerEigensystem`；3977→`f->P=(f+1)` 与 `memcpy`）。因此注入的 NULL 忠实地模拟真实分配失败。
- 授权：只作用于导出副本，符合用户授权。
- 2295 的多行调用：其尺寸表达式为纯算术（无 `++`/`--`/函数调用），在钩子调用中重复求值是安全的（已核对）。

### 4.3 命中确认（每个注入点）[实测]

- 家族 C 的人口普查（`census-r4/`、`R2C_CENSUS_FAMILY_C.txt`）：

| 栈 | 模式 | id | 站点 | rc | HITCOUNT | RC first | 观察 |
|---|---|---|---|---|---|---|---|
| pattern | fft | 21 | S4.cpp:2267 | 139 | (未打印) | — | 命中后 SIGSEGV |
| pattern | jones | 21 | 同上 | 139 | — | — | 命中后 SIGSEGV |
| pattern | fft | 22 | S4.cpp:2295 | 139 | — | — | 命中后 SIGSEGV |
| pattern | jones | 22 | 同上 | 139 | — | — | 命中后 SIGSEGV |
| pattern | fft | 23 | S4.cpp:2408 | 1 | 1 | 0 | 命中，调用返回 0（静默） |
| pattern | fft | 24 | S4.cpp:2425 | 1 | 1 | 0 | 命中，调用返回 0（静默） |
| pattern | fft | 25 | S4.cpp:3977 | 1 | 0 | 0 | **未命中**（fft 不调用缓存安装） |
| pattern | jones | 25 | 同上 | 139 | — | — | 命中后 SIGSEGV |
| flat | fft | 21/22 | 同上 | 139 | — | — | 均匀层上仍命中后崩溃（每层都经过） |
| flat | fft | 23/24/25 | 同上 | 1 | 0 | 0 | **未命中**（均匀层无特征分解、无缓存安装） |

- 对照（无注入）：fft/jones × pattern/flat 均 rc=0、PASS。

### 4.4 NB=1..8 可达性 [实测]

- 对照（无注入）NB=1..8 × 五模式（`nb-r4/nb_table.txt`）：除 **VL 在 NB=1–4 时 RC first = 20**（rc=1，显式报告的特征值失败码）外，其余全部 rc=0。VL NB=5–8 正常。这与早期阶段 O-1 的观察一致（以 NG 为口径）。
- 家族 A（fft、kottke，NB=1..8）：**全部 HITCOUNT=1**（`nb_hits_familyA.txt`）。
- 家族 B（jones 15、nv 16、vl 17，NB=1..8）：**全部 HITCOUNT=1**（`nb_hits_familyB.txt`）。注意 VL NB=1–4 的注入虽然命中，但该运行的控制已因 RC 20 而失败，因此这些 VL 行不能作为注入结果（见第 5 节）。
- 家族 C（23 fft、25 jones，NB=1..8）：全部命中（`nb_hits_familyC.txt`）；21/25-jones 命中后崩溃，23 命中后静默。

### 4.5 FMM S4_malloc 的运行时可达性 [实测]

- 用 gdb 对 `__wrap__Z9S4_mallocm` 计数（尺寸取自 `%rdi`，见 `R2C_FMM_S4MALLOC_RUNTIME_REACH.txt`）；函数人口普查用 gdb 对 7 个 `FMMGetEpsilon_*` 断点（`s4m-r4/fa_fft.txt`、`fa_kottke.txt`、`fa_jones.txt`、`fa_nv.txt`、`fa_vl.txt`；breakpoint 行数核对为 7）。
- 结果：fft 2 次（FFT）；kottke 1 次（Kottke）；jones 4 次（ClosedForm + PolBasisJones）；nv 4 次；vl 4 次。Experimental 从未被调用。
- 尺寸与源码的函数算术一致（例如 192 B = `(2+10)*(nshapes+1)*8` 中 nshapes+1=2），这是站点归属的主要依据。

### 4.6 未闭合的缺口（明确披露）[实测]

- **缓存命中路径的 `work`（Jones:337、NV:225、VL:234）未被实测**：单次运行只走缓存未命中路径；命中路径需要第二次调用。本轮未做两次调用的测量。标 **[未验证]**。
- `fmm_kottke.cpp:78` 的 `fft_alloc_complex` 不是 `S4_malloc`，`--wrap` 不可达；本轮未为它单独建立家族 C 的钩子（它由 S3 修复，未在 R2 注册表中）。标 **[未验证]**，列为后续输入。

---

## 5. R2-D 判定器与期望登记扩展 [源码 + 实测]

### 5.1 判定器（不改类别，扩充自检）

- 现有判定器（`judge_d003.py`）的类别集合 `INVALID / CRASH / SILENT_SWALLOW / REPORTED_FAILURE / CONTROL_OK` 已能正确分类本轮全部新观察（10 个事实模式，0 个不一致；见自检结果）。
- 因此**没有修改分类规则**。新增的是自检用例与登记行。判定器仍只读取事实（rc、rc1、rc2、hit），不读驱动的 PASS/FAIL 退出码。

### 5.2 自检计数（分别报告）[实测]

| 自检 | 原有 | 本轮新增 | 合计 | 结果 |
|---|---|---|---|---|
| `judge_d003.py selftest`（类别与解析） | **19/19**（原有，保持不变） | 6/6（R2 new） | 25/25 | PASSED，rc=0 |
| `judge_d003.py selftest-sensitivity`（输出灵敏度） | **7/7**（原有，保持不变） | 3/3（R2 new） | 10/10 | PASSED，rc=0 |

- 原有的 19/19 与 7/7 数字经核对是"打印的 ok 行数"，而非 `expect()` 调用数（代码里 `expect(` 的计数包含 `def expect` 定义行）；该口径在本报告 §5.2 中说明。

### 5.3 期望登记（运行前登记，之后有修正）[源码]

- 登记文件：`R2D_EXPECTATIONS.tsv`（26 行，10 个制表符字段）。登记时间（UTC）：`2026-10-11T04:05:33Z`（`R2D_REGISTRY_TIMESTAMP_UTC.txt`）。
- 每行标注基线预期（BASE）与当前树预期（CUR），以及依据标签：**PRE** = 运行前由源码分析得出；**OBS** = 在 R2-B/C 的探测中已观察到（非盲预测，已如实标注）。
- **登记后的修正（已披露）**：
  - 修正 1：`R2D_EXPECTATIONS.preaudit.tsv` → 当前文件的格式转换（空格分隔 → 制表符分隔，新增 NTH 列）。期望类别经核对未改变（26 行中 24 行逐字段一致；另 2 行为 family-F 行，其请求含空格，原始空格版本无法按字段解析，其期望类别由原始依据文本确认为 CRASH / REPORTED_FAILURE）。
  - 修正 2：6 行的依据文本从 PRE 改为 OBS/PRE-SRC（仅依据标签，**期望类别未改**）。
  - 修正 3：两行在格式转换中损坏，已从源数据重建（见 `R2D_AUDIT_CORRECTIONS.txt`）。
  - 登记文件的最终 sha256：`ec8fafbc5ff7f54fbc6db2b4fd283467d7c05e598141bd8790bc68fe265cefb6`；修正前为 `879d1007a4e158a8598fc8ff0d564c5323fee2705a035afd0ebeaaea07bb51a4`（两者均保留）。
- **注册表 CUR 行中 `N-vl-id17-k1` 的期望类别（INVALID）经运行被证明是登记错误**（见第 6 节偏离 D-1）。按规则未改写该行。

### 5.4 登记行格式校验 [实测]

- 校验器确认：每行 10 字段、mode/stack/class 取值合法、请求前缀合法（`linearsolve:`、`linearsolve_null:`、`alloc:`、`s4malloc`）。
- 校验器发现并修复的格式错误：family-F 行的请求含空格（已拆分到 NTH 列）。

---

## 6. R2-E 两棵树的运行与三方对照 [实测]

### 6.1 注册表矩阵（26 行，BASE 13 行 + CUR 13 行）

| 树 | 行数 | 与登记期望一致 | 不一致 |
|---|---|---|---|
| BASE 37a82e8 | 13 | 11 | 2（D-2、D-1） |
| CUR 8d60dfb | 13 | 12 | 1（D-1） |

不一致的三行（均为登记错误，不是代码发现；见第 7 节偏离）：
- `A-fft-info-k1` BASE：登记为 REPORTED_FAILURE，观察为 SILENT_SWALLOW（基线无 solve_info 检查，观察正确）。
- `N-vl-id17-k1` BASE 与 CUR：登记为 INVALID，观察为 SILENT_SWALLOW（注入已命中，NB=9 控制干净，应为 SILENT_SWALLOW）。

### 6.2 基线与当前树并列（三方对照的核心）[实测]

| 站点 | BASE 观察 | CUR 观察 | 变化 |
|---|---|---|---|
| FFT solve_info（A-fft） | SILENT_SWALLOW | REPORTED_FAILURE | **红 → 绿** |
| kottke solve_info（A-kottke） | SILENT_SWALLOW | REPORTED_FAILURE | **红 → 绿** |
| FMM work NULL（F-fmm-s4malloc1-fft，fmm_FFT:74） | CRASH | REPORTED_FAILURE | **红 → 绿** |
| PolBasisJones info=NULL（id 15） | SILENT_SWALLOW | SILENT_SWALLOW | 仍红 |
| PolBasisNV info=NULL（id 16） | SILENT_SWALLOW | SILENT_SWALLOW | 仍红 |
| PolBasisVL info=NULL（id 17） | SILENT_SWALLOW | SILENT_SWALLOW | 仍红 |
| closed info=NULL（id 11） | INVALID（未命中） | INVALID（未命中） | 未命中 |
| S4.cpp *layer_modes（id 21） | CRASH | CRASH | 仍红 |
| S4.cpp pB->q（id 22） | CRASH | CRASH | 仍红 |
| S4.cpp rwork（id 23） | SILENT_SWALLOW | SILENT_SWALLOW | 仍红 |
| S4.cpp work（id 24） | SILENT_SWALLOW | SILENT_SWALLOW | 仍红 |
| S4.cpp AddFieldToCache（id 25，jones） | CRASH | CRASH | 仍红 |
| AddFieldToCache（id 25，fft） | INVALID（未命中） | INVALID（未命中） | 未命中 |

### 6.3 FMM 的 15 个可达 S4_malloc 调用（观察性补充，非预注册）[实测]

- 文件：`FMM_S4MALLOC_SUPPLEMENT_OBSERVED.json`（30 次运行：15 个"模式-调用序号"行 × 2 棵树）。原始日志按树命名（`fmm-sup-runs/BASE_*`、`CUR_*`，共 30 个）。
- 注意："15"是模式-调用行数，不是 15 个不同的源码站点。`closed.cpp:40`（ClosedForm 的 ivalues）在 jones、nv、vl 三个模式中各出现一次，因此不同源码站点为 13 个。函数归属已用 gdb 回溯逐一核对（`attr-r5/attr_fft.txt`、`attr_kottke.txt`、`attr_jones.txt`、`attr_nv.txt`、`attr_vl.txt`）：jones/nv/vl 各为 1 次 ClosedForm + 3 次各自的 PolBasis；fft 2 次 FFT；kottke 1 次 Kottke。13 个不同源码站点 = FFT 2 + kottke 1 + closed:40 1 + Jones 3 + NV 3 + VL 3（逐行列于 `fmm_supplement_runner.py` 的 SITES 表）。
- **BASE：15/15 为红**（13 个 CRASH，2 个 SILENT_SWALLOW：`PolBasisJones:167 vfield`、`PolBasisVL:127 vfield`）。
- **CUR：15/15 为绿**（REPORTED_FAILURE，rc1=20）。
- 两次独立运行的 30 个站点在类别、rc、rc1、hit 上**完全一致**（可复现性检查）。

### 6.4 三方一致性（任务书要求）[实测 + 算术]

1. **基线红**：登记行中 BASE 观察为 CRASH/SILENT 的有 11 行（注意：这是观察类别的计数，不是"与期望一致"的计数；与期望一致的 BASE 行为 11/13）；FMM 补充调用行 BASE 红 15/15。
2. **当前树绿**：登记行中 CUR 观察为 REPORTED_FAILURE 的有 3 行（A-fft、A-kottke、F-fmm）；FMM 补充调用行 CUR 绿 15/15。（注意：CUR 与期望一致为 12/13，这是另一个口径。）
3. **当前树仍红**：登记行 CUR 红 8 行（N-jones、N-nv、N-vl、C-21、C-22、C-23、C-24、C-25-jones）；FMM 补充站点 CUR 红 0 行。

**与 R2-A "未处理"列表的对账**（逐行列出，非减法；见 `R2E_NOT_HANDLED_RECONCILIATION.txt`）：

| 未处理行（13） | CUR 观察 |
|---|---|
| S4.cpp:2267 / 2295 / 2408 / 2425（ComputeLayerModes 4） | 红 4 行（21、22、23、24） |
| S4.cpp:3977（AddFieldToCache 1） | 红 1 行（25-jones；fft 未命中） |
| PolBasisJones:369 / NV:260 / VL:268（info=NULL 3） | 红 3 行（15、16、17） |
| closed:130 / 133 / 138 / 235（info=NULL 4） | 未命中 4 行（11 有登记行；12、13、14 仅有人口普查记录，**无登记行**） |
| fmm_experimental:40（S4_malloc 1） | 驱动不可达，无登记行 |

合计：**红 8 + 未命中 4 + 不可达 1 = 13**，与 R2-A 未处理行数一致。

### 6.5 历史 38 案矩阵的保留性检查 [实测]

- 历史矩阵 `matrix_d003.py`（未修改，38 案，期望分布 INVALID 11 / SILENT 11 / CONTROL_OK 9 / CRASH 7）在**扩展后**的装置上运行：
  - BASE 37a82e8：**38 案，期望不一致 0**。扩展后的装置完整复现了所有历史期望（在它们所描述的树上）。
  - CUR 8d60dfb：**38 案，期望不一致 18**。
- 18 个当前树不一致项全部观察为 **REPORTED_FAILURE（rc1=20）**，分桶核对（代码计数，非手算）：fft plan 5、fft exec 5、fft scratch 2、fft S4_malloc 2、solve_info（ls）4，合计 18，**无任何不可解释的桶**。这些正是 S3 修复改变的行为，历史期望记录的是修复前行为（保留，未改写）。

---

## 7. 偏离项与违规披露（逐条如实）

### D-1 登记错误：`N-vl-id17-k1`（期望 INVALID，实际 SILENT_SWALLOW）[实测]

- 登记时我把"VL NB=1–4 的控制因 RC 20 而失败"的情形错误地类推到 NB=9 的注入上。
- 实测：VL NB=9 控制干净（rc=0，RC first 0）；id 17 注入命中（HITCOUNT 1），首次调用返回 0。按判定器规则应为 **SILENT_SWALLOW**。
- 处理：登记行未改写（按规则保留原值）；本偏离如实记录。该错误**不是代码发现**。

### D-2 登记错误：`A-fft-info-k1` 的 BASE 期望 [实测]

- 我登记 BASE 为 REPORTED_FAILURE，但基线的 FFT `solve_info` 未检查（R2-A 清单可证），应为 SILENT_SWALLOW。观察与源码一致，期望错误。未改写该行。

### D-3 登记文件在登记时间戳之后被修改 [实测]

- 登记时间戳 `04:05:33Z` 之后，登记文件经历了格式修正（空格 → 制表符、增加 NTH 列）、依据标签修正、两行损坏的重建、family-F 行的格式修复。期望类别经逐字段核对未改变（26 行中 24 行逐字段一致，其余 2 行由原始依据确认）。
- 修正日志：`R2D_AUDIT_CORRECTIONS.txt`；修正前副本：`R2D_EXPECTATIONS.preaudit.tsv`。
- 这违反了"期望先登记、事后修正保留原值并披露"的严格口径：期望**类别**未改，但**文件本身**在登记后被改动。已如实披露，不予掩盖。

### D-4 FMM 补充观测的日志覆盖缺陷（已修复，已披露）[实测]

- 第一次补充运行中，日志文件名不含树标识，BASE 与 CUR 写入**同一文件名**，BASE 的原始日志被 CUR 覆盖。分类结果在每次运行后立即由原始输出计算，因此表格结果未受损；但 **BASE 原始日志丢失**。
- 处理：修复命名（加入树标识），清空并重新运行两棵树；两次运行的 30 个站点完全一致。第一次的 JSON 保留为 `FMM_S4MALLOC_SUPPLEMENT_OBSERVED.run1_overwritten_logs.json`。

### D-5 请求字符串错误（sanity 检查）[实测]

- `S4FMM_INJECT=s4malloc::`（多余冒号）导致注入器不匹配（`strcmp` 精确匹配），`HITCOUNT 0`。这是我的请求字符串错误，不是注入器缺陷。正确请求为 `s4malloc`，此后按正确字符串重测（`HITCOUNT 1`）。

### D-6 模式/栈误用（三次）[实测]

- 误用 `flat` 栈代替 `pattern` 栈（R2-B 的 smoke 与 gdb 人口普查）：flat 只走均匀分支，不进入 FMM 非均匀代码。这导致一次"不可达"的错误解读，随后已更正。
- 在 fft 模式下请求 PolBasis 站点（id 15）：`HITCOUNT 0` 是模式错误的结果，不是基线差异。已在 jones 模式下重测（基线命中）。

### D-7 gdb 人口普查的两次工具错误 [实测]

- 第一次 gdb 断点的 `printf "...", size` 因符号无法解析而不输出（"零次调用"是工具错误，不是事实）。改用 `$rdi` 寄存器后得到正确计数。
- 第一次 gdb 钩子人口普查（`S4_TEST_LINEARSOLVE_NULLINFO_AFTER` 断点）同样输出 0，已确认为工具问题，未作为结果使用。

### D-8 陈旧目标文件导致的无效人口普查 [实测]

- 第一次家族 C 人口普查（`census-r4/` 的初版）全部 HITCOUNT=0，原因是 `make` 复用了未带宏的 `S4.o`（`nm` 显示其中无 `S4_TEST_ALLOC_HOOK`，make 日志中无 `DS4_TEST_ALLOC_SEAM`）。该结果被撤回（`R2C_CENSUS_INVALIDATED.txt`），从空目标目录重建后得到有效数据。

### D-9 一次 `libS4.a` 链接的路径错误 [实测]

- 链接时库名与路径不符（`cannot find -lS4`），以及漏写 `-lS4`（未定义的 API 符号）。均为构建命令错误，已改正；未用于任何结果。

### D-10 错误的 bash 临时目录与 heredoc 语法 [实测]

- 一次 heredoc 的 Python 语法错误（未闭合的 `EOF` 行），未产生任何运行或证据，已重写为独立文件（`fmm_supplement_runner.py`）。
- 一次 `cd` 失败后路径拼接错误（`checkpoints/...` 前缀重复），导致 `ar` 报错与一次"全部 24 个目标文件不同"的假阳性；已改为绝对路径并重做，结论以重做为准（24/24 不同 → 仅 6 个 FMM 目标 + S4.o 不同，见第 3.5 节）。

### D-11 缓存命中路径未测（范围缺口）[实测]

- Jones:337、NV:225、VL:234（缓存命中 `work`）未被任何运行覆盖（单次运行只走缓存未命中路径）。第 4.6 节已列为 **[未验证]**。这是 R2-C 的未完成项，不是已完成的项。

### D-12 registry 覆盖缺口 [实测]

- 登记表只覆盖 1 个可达的 FMM S4_malloc 调用（fmm_FFT:74 的 work）；其余 15 个调用行由观察性补充覆盖（非预注册，见 6.3）。`closed:12/13/14` 与 `fmm_experimental:40` 无登记行。
- 这意味着"每个注入点有命中确认"只对登记表内的点严格成立；对补充观测的调用行，依据是观察而非预注册。已在本报告如实标注。

### D-13 观察性补充的性质 [实测]

- 6.3 节的 30 次 FMM 运行是**观察**，设计于人口普查之后，未在运行前登记。其结果在两次运行间稳定，但它不是盲预测。

### D-14 `/tmp` 与工具落盘 [实测]

- `glob` 工具在本轮早期把完整结果落盘到 `/tmp/dsh-spill-…`（工具框架行为，非本代理的 shell 命令；已在前一轮报告披露）。
- 本轮 shell 命令：每条会产生临时文件的命令均在同一命令内先 `export TMPDIR=<仓库内证据目录>`，并确认目录存在（部分早期命令的 TMPDIR 设置是在同一条命令内，已逐条自查）。
- 任何写仓库外路径的尝试：**本轮未发现**。（上一轮的 D-1 违规已在上一轮报告中披露。）

---

## 8. 范围外清单（登记项草稿）

以下是非 FMM、且不在 D003 验收路径上的 S4_malloc 点。**只列位置与数量，不纳入本轮。**（任务书第 4 节 R2-A：非 FMM 的其他 S4_malloc 不纳入。）

- 数量：S4.cpp 中 `S4_malloc(` 与 `malloc(` 的调用行共 **48** 处（当前树，已 grep 计数，排除 S4_TRACE/S4_VERB 行）；其中 5 处为家族 C 站点（2267、2295、2408、2425、3977），故范围外为 **43 处** [实测计数]。FMM 目录不计入本数（FMM 点单独列于第 2 节）。
- 代表性位置（非穷尽）：`S4.cpp:311`（S4_Simulation_New）、`:381`、`:498`、`:621`、`:625`、`:1303`、`:1642`、`:1755`（InitSolution 的 S->solution->ab）、`:1909–1911`、`:1940`、`:1993–1994`、`:2021`、`:2071`、`:3283`、`:3382`、`:3477`、`:3544`、`:3609`、`:3660`、`:3724`、`:3777`、`:4040–4042`、`:4290`。
- 注：范围外的 43 处已精确计数（[实测]，见上）。上方"代表性位置"为节选，不是完整清单；完整清单可由同一 grep 命令复现。

---

## 9. 对 P05-S3 补充轮的输入

### 9.1 红点清单（当前树仍红，需 S3 补充轮处理或裁决）

| # | 点位 | 类别 | 基线结果 | 当前树结果 | 归属 | 完成判据 |
|---|---|---|---|---|---|---|
| 1 | PolBasisJones:369 | info=NULL（边界） | SILENT_SWALLOW | SILENT_SWALLOW | 边界待用户裁决（是否纳入 D003） | 若纳入：求解 info 被检查，失败返回非零并不安装缓存 |
| 2 | PolBasisNV:260 | info=NULL（边界） | SILENT_SWALLOW | SILENT_SWALLOW | 同上 | 同上 |
| 3 | PolBasisVL:268 | info=NULL（边界） | SILENT_SWALLOW | SILENT_SWALLOW | 同上 | 同上 |
| 4 | S4.cpp:2267 | ComputeLayerModes 通用分配 | CRASH | CRASH | D003 验收路径（模式安装） | NULL 时返回现有码 20，不安装模式，不解引用 |
| 5 | S4.cpp:2295 | ComputeLayerModes 通用分配 | CRASH | CRASH | D003 验收路径（模式安装） | 同上 |
| 6 | S4.cpp:2408 | ComputeLayerModes 通用分配 | SILENT_SWALLOW | SILENT_SWALLOW | D003 验收路径（特征分解工作区） | NULL 时返回 20，不调用求解器 |
| 7 | S4.cpp:2425 | ComputeLayerModes 通用分配 | SILENT_SWALLOW | SILENT_SWALLOW | 同上 | 同上 |
| 8 | S4.cpp:3977 | AddFieldToCache 分配（jones） | CRASH | CRASH | D003 验收路径（缓存安装） | NULL 时不缓存，返回失败给 PolBasis，PolBasis 返回非零 |

### 9.2 边界待用户裁决（不由本轮决定）

- info=NULL 的 7 处（closed 130/133/138/235 与 PolBasis 369/260/268）：它们的失败是否"影响模式或缓存是否被安装"，本报告不自行裁决。其中 closed 130/133/138/235 **驱动不可达**，若纳入 D003 则需要驱动或 Lua/Python 路径的新装置（不在本轮）。
- `fmm_experimental.cpp:40`：驱动不可达（Lua 独有），是否纳入 D003 的驱动装置，需用户裁决。

### 9.3 装置侧的未闭合项（下一轮输入，非 S3 修复）

- 缓存命中路径（Jones:337、NV:225、VL:234）的注入：需要两次调用的驱动或新的注入模式。**[未验证]**。
- `fmm_kottke.cpp:78` 的 `fft_alloc_complex`：`--wrap` 不可达，需家族 C 风格的 seam 或新钩子。**[未验证]**。
- 登记表的覆盖：15 个可达 FMM S4_malloc 调用行需进入预注册登记表（当前仅观察性覆盖）。
- VL NB=1–4 的控制失败（RC 20）：是既有行为，需在 S4 验证中明确其是否属于 D003。

### 9.4 完成判据（对 S3 补充轮）

- 红点 4–8（ComputeLayerModes 与 AddFieldToCache）：修复后，对应登记行的 CUR 观察应为 **REPORTED_FAILURE**（且 rc1 = 20），而非 CRASH 或 SILENT_SWALLOW。
- 红点 1–3（info=NULL）：仅当用户裁决纳入后才有完成判据。
- 所有修复必须以"BASE 红、CUR 绿"的同一装置验证，且历史 38 案的 18 个 S3 变化项继续为 REPORTED_FAILURE（不回归）。

---

## 10. 收尾核对与路径清单

### 10.1 收尾核对 [实测]

- `S4/` 改动（相对 HEAD）：**0**。`S4/` 未跟踪文件：**0**。
- 既有制品保留（sha256 比较，见下表）：`apply_seam.py`、`linearsolve_seam.patch`、`driver_d003.cpp`、`matrix_d003.py` 的 sha256 与本轮开始前一致。
- 本轮修改的既有文件：`judge_d003.py`（扩充自检）、`src/inject_d003.cpp`（新增家族 B、C 钩子，家族 A 原样）。这两个修改是有意的，且为增量。
- /tmp 顶层快照：开始与结束均为 `e3b0c442…`，条目数 0（一致）。**这只是顶层条目快照**，不能排除工具落盘（D-14）。
- 抽样 strace（一次 `matrix_r2.py run`，`openat/creat/mkdir/rename/unlink`）：对 `/tmp` 的事件 **0**；仓库外写入型 open：**0**（排除 /dev/null、/proc、/sys）。**这是一次抽样，不是整轮的穷尽审计。**

### 10.2 路径清单

| 类别 | 路径 |
|---|---|
| 提交（testing/d003） | `testing/d003/judge_d003.py`、`testing/d003/src/inject_d003.cpp`、`testing/d003/matrix_r2.py`、`testing/d003/seam/apply_seam_r2.py` |
| 提交（报告） | `checkpoints/p05/P05_S2R_HARNESS_SUPPLEMENT.md`、`checkpoints/p05/S1_evidence_digest.txt`（追加 S2R 段） |
| 证据（不提交） | `checkpoints/p05/evidence/p05-s2r/`：`INJECTION_POINTS.txt`、`enum_*.json`、`R2B_LINEARSOLVE_SITE_MODEL.txt`、`R2B_BUG1_leading_dimension.txt`、`R2B_REACHABILITY_PREDICTION_closed.txt`、`R2C_CENSUS_FAMILY_C.txt`、`R2C_CENSUS_INVALIDATED.txt`、`R2C_FMM_S4MALLOC_RUNTIME_REACH.txt`、`R2C_NB_REACHABILITY.txt`、`R2C_S4CPP_FAMILY_C_FEASIBILITY.txt`、`R2D_EXPECTATIONS.tsv`（及 preaudit/prefix_fix 副本）、`R2D_AUDIT_CORRECTIONS.txt`、`R2D_REGISTRY_TIMESTAMP_UTC.txt`、`R2E-BASE/`、`R2E-CUR/`、`R2E_NOT_HANDLED_RECONCILIATION.txt`、`R2E_HISTORICAL_MATRIX_PRESERVATION.txt`、`FMM_S4MALLOC_SUPPLEMENT_OBSERVED.json`（及 run1 副本）、`fmm-sup-runs/`、`hist-base/`、`hist-cur/`、`strace-r2/`、`logs/`、`tmp_snapshot_*_s2r.txt`、`base-37a82e8/`、`cur-8d60dfb/`、`r4-seam/`、`bin-*` 等导出与构建产物 |
| 候选（只读，未变更） | `/home/jackal/s4-fmm-20260930T132345Z`、`/home/jackal/s4-fmm-o1-20260930T183847Z`（本轮未使用） |

---

## 11. 结论与状态

- **装置**：三个互相独立的 seam 家族在两棵树上锚点唯一、默认路径字节一致、阳性对照成立；历史 38 案在基线上零不一致（装置保留）。
- **红/绿**：基线上 15/15 个可达 FMM S4_malloc 点为红；当前树上全部绿。登记表中的 S3 变化（FFT solve_info ×2、FMM work ×1）由红变绿，与 S3 修复一致。
- **仍红**：ComputeLayerModes 4 点、AddFieldToCache（jones）、info=NULL（PolBasis 3 点）在两棵树上均为红，与 R2-A 未处理列表一致。
- **未闭合**：缓存命中路径、`fft_alloc_complex`、登记表对 15 个调用行的预注册覆盖、非 FMM 的 S4.cpp 分配范围（43 处，已精确计数）。
- **登记错误**：登记表中有 3 个期望不符（BASE 2 个、CUR 1 个），均为登记错误而非代码发现，已如实披露并保留原值。

**本阶段未完成，等待用户审核。** P05-S1、P05-S2、P05-S3、P05-S4 均未被宣布完成。
