# P05-S2R3 续作二：阶段 3–5 报告（装置观察与缺口）

> **状态：未完成，等待用户审核。** 本报告不宣布 P05-S1、P05-S2、P05-S3、P05-S4 任一阶段完成。
> 本轮所有结果称"装置观察"，不称"验证"。本报告只陈述事实与推论，不替用户选择 Jones 的 a/b/c 方案，不撤销或修改任何 S3R 源码提交。

## 0. 定位与编号约束

- 本报告属于正式阶段 **P05-S2** 的补充子任务 S2R3 的续作二（阶段 3、4、5）。P05 固定五阶段 S1–S5，本轮未引入 S6。历史报告与文件名未改写。
- 阶段定义依据：用户提示词（本仓库内无 P05 原始计划文档；未在仓库内搜索原文）。
- 开工核对：HEAD = `5fb66d5`；分支 `codex/p05-d003-fft-error-propagation`；`S4/` 相对 `64eb0b5` 改动为 0；开工时工作区干净。
- 结束核对：见第 12 节。

## 1. 授权与边界

- 不修改 `S4/` 下任何文件。`S4/` 相对 `64eb0b5` 全程保持 0 改动（第 12 节核对）。
- 可修改范围：`testing/d003/`、`checkpoints/p05/`。seam 只应用于 `git archive` 导出副本，不写仓库 `S4/`。
- 判定器只依赖事实（rc、信号、输出字节、rc1/rc2、命中数），不读取驱动的 PASS/FAIL 行。
- 历史登记文件未改写。期望先登记（时间戳 + sha256），登记后冻结（只读）；修正另存新文件并披露。

## 2. 用户对上一轮四个问题的决定（执行依据）

| # | 用户决定 | 本轮执行 |
|---|---|---|
| 1 | 缓存命中点（NV、VL、Jones）不新增注入点，复用 S2R2 路由：`S4FMM_TWICE=slab` + `s4malloc` + NTH=7 + `inj_call=2` | 已执行。命中以**尺寸**确认（jones 1296 B，nv/vl 2592 B），NTH 扫描 1..8 证明序号未移位（第 6.3 节）。命中数核对：本轮与 S2R2 的全部注入类 cache-hit 与 kottke 行（共 50 条，含 3c 与 3d 复跑）**全部 hit = 1**；另有历史 38 案中的 `s2b/ls-kottke-xsite`（跨站点请求，设计上不可达）两条为 hit = 0，按其历史 INVALID 期望判定，属于正确结果而非假匹配。路由属**内部路由覆盖**（使用内部接口 `S4_Simulation_DestroyLayerModes`，声明于 `S4/S4_internal.h:181`，驱动在 `testing/d003/src/driver_d003.cpp:213` 调用），与公开 API 路径分开表述：公开 API 路径此前未测到，**不写成"不可达"**。 |
| 2 | kottke 两个点必须测失败类别，不接受仅可达性观察 | 已执行。`fft_alloc_complex(6*ng2)`（family D `kottke_alloc:31:1`）与 `discval = S4_malloc(...)`（`s4malloc` NTH=1）三树各两次，均有失败类别（第 6.4 节）。 |
| 3 | B/A 列接受 family B 输出模型与 family C；H 列用 B2；每个受影响行标注"模型不同"，不得把 B/A 与 H 的差异写成修复效果的唯一证据 | 已执行。所有 B/A 与 H 不同模型的行标注 `MODEL DIFFERS`，并说明两种模型含义（第 7 节）。 |
| 4 | 运行器与验证器允许新增 `H` 作为第三个树名；(a) BASE/CUR 校验与输出不变；(b) 不改历史登记；(c) 历史矩阵在 H 上复跑用新映射文件声明 H 沿用 CUR 期望，差异逐条标注原因；(d) 不放宽类别规则 | 已执行（提交 `bdd2b56`）。(a) 旧登记、旧驱动、旧输出的逐字段回归差异为 0（第 8.1 节）；(b) 历史登记 sha256 复核不变；(c) 映射文件 `MAP_3D_*` 已登记；(d) `judge_d003.py` 未改（sha256 `d2d04145…`）。 |

**用户在本轮中期追加的两项决定**（在 3d 因 §8 条件停下后提问）：

- **D-U1**：`N-jones-id15-k1` 与 `N-nv-id16-k1` 在 H 上记为"H 无等价点"，不计入方向差异，在报告中列为**结构性差异**（第 8.4 节）。不新增钩子。
- **D-U2**：继续完成 S2R2 的 17 case、阶段 4 与阶段 5。

**超出字面授权的一处延伸（已由用户批准）**：运行器 `REQUEST_PREFIXES` 追加 `linearsolve_null2:`（提交 `d8b4276`），使 H 树的 B2 行可经运行器正式执行。用户在提问中选择了"仅追加该前缀"的推荐方案。

## 3. 阶段 3 与子提交一览

| 子步 | 内容 | 提交 | 状态 |
|---|---|---|---|
| 3a | 运行器加入 H 树名，BASE/CUR 回归 | `bdd2b56` | 已提交，awaiting user review |
| 3b-前缀 | 运行器加入 B2 请求前缀（经用户批准） | `d8b4276` | 已提交，awaiting user review |
| 3b | 8 个红点三列对照 | 无 testing 代码改动；结果与登记在证据目录 | 已完成（不产生新提交，见第 10 节） |
| 3c | fmm_experimental:40、FFT→PolBasis 三链、closed 四点、cache-hit、kottke | 无 testing 代码改动 | 已完成（不产生新提交） |
| 3d | 历史矩阵在 H 上复跑 | 无 testing 代码改动（映射与结果在证据目录） | 已完成（不产生新提交） |
| 4 | Jones 只读对照 | `9d29877`（两个脚本） | 已提交，awaiting user review |
| 5 | 报告与 digest | 本报告与 digest 段落 | 见第 14 节 |

阶段 2 的提交 `5fb66d5` 与阶段 1 的提交 `8643ffe` 属于本续作的起点，未改动。

### 3.1 登记表（时间戳 + sha256，均在登记后冻结为只读）

> **文件名解析规则**：本报告中未带目录的登记文件名（如 `stage3/REG_3B_THREECOLUMN.tsv`、`REG_3C2_FFTCHAIN.tsv`）均相对于证据目录 `checkpoints/p05/evidence/p05-s2r3/`；未带 `stage2/`、`stage3/` 前缀的登记名以上下文为准（登记表中均带前缀）。历史 S2R、S2R2 的文件相对于 `checkpoints/p05/evidence/p05-s2r/`、`checkpoints/p05/evidence/p05-s2r2/`。

| 登记 | 时间戳（UTC） | sha256（前 16 位） | 性质 |
|---|---|---|---|
| `stage2/REG_B2_EXPECTATIONS.tsv` | 2026-10-11T07:09:17Z | `dfa57c1e…` | 阶段 2 登记（未改） |
| `stage3/REG_S3_EXPECTATIONS.tsv` | 2026-10-11T07:14:05Z | `539c6e60…` | 阶段 3 登记（未改） |
| `stage3/CORR_S3_EXPECTATIONS_1.tsv` | 2026-10-11T07:14:22Z | `23b6b994…` | 更正 1（exp40 路由，另存） |
| `stage3/CORR_S3_EXPECTATIONS_2.tsv` | 2026-10-11T07:32:09Z | `c1fbf453…` | 更正 2（cache-hit 与 kottke，另存） |
| `stage3/REG_3B_THREECOLUMN.tsv` | 2026-10-11T07:35:55Z | `e497c4a9…` | 3b 八红点三列 |
| `stage3/REG_3C1_EXPERIMENTAL.tsv` | 2026-10-11T07:37:43Z | `f8322238…` | 3c.1 fmm_experimental:40 |
| `stage3/REG_3C2_FFTCHAIN.tsv` | 2026-10-11T07:40:15Z | `5e46f862…` | 3c.2 FFT→PolBasis 链 |
| `stage3/REG_3C3_CLOSED.tsv` | 2026-10-11T07:41:37Z | `c640f5a3…` | 3c.3 closed 四点 |
| `stage3/MAP_3D_HIST38_H.tsv` | 2026-10-11T07:43:22Z | `06e9d003…` | 3d 历史 38 案映射 |
| `stage3/MAP_3D_R2D_H.tsv` | 2026-10-11T07:44:31Z | `2f668b83…` | 3d S2R R2-D 映射 |
| `stage3/MAP_3D_S2R2_H.tsv` | 2026-10-11T07:46:28Z | `dc228a92…` | 3d S2R2 17 case 映射 |
| `stage3/EXEC_3C_CORR2.tsv` | 派生执行映射（不是登记；期望列由 CORR_2 机械复制） | — | 执行输入 |

**诚实披露的登记前修订**（均发生在对应登记盖时间戳之前，草稿已保留）：`REG_3B` 的树名由 `B/A` 改为 `BASE/CUR`、表头加 `#`；`REG_3C2` 草稿 v1 被判定器派生版本替换（草稿 `REG_3C2_FFTCHAIN.draft-v1-unfrozen.tsv`，未登记）；`REG_3C3` 由 7 列改为运行器的 10 列格式（草稿 `REG_3C3_CLOSED.draft-7col-unfrozen.tsv`）；`CORR_2` 在盖时间戳前修正了 kottke 与 cache-hit 的两处行号。

**需要说明的登记性质**：`CORR_2`、`REG_3C2`、`MAP_3D_*` 的期望是在观察之后写入的，全部标注 `INFLUENCED`。它们是"观察类别在既定判定规则下的记录"，不是盲预测。

## 4. 三棵树与目标文件哈希

| 树 | 提交 | S4 树 id（`git rev-parse <c>:S4`） | 说明 |
|---|---|---|---|
| B | `37a82e8` | `1d738e64…` | S2R BASE，S3R 之前，无任何 FMM 分配检查 |
| A | `876181c` | `85feec11…` | S2R2 收尾树；与 `aa1c51d`（S2R2 CUR）的 S4 树 id 相同。含 S2 的 FMM 分配检查，**不含** S3R 修复 |
| H | `64eb0b5` | `cb7fc613…` | S3R 修复之后的树（含 `e83255f`、`73e00ef`、`df3bb02`、`35cd7b3`） |

> **角色更正**：本轮前期曾把 A 写成"修复后"，这是错误的。A 是 S3R 之前的树（`S4.cpp:2267` 为无检查的 `malloc`，随后解引用）；A 含 S2 修复（`b00b630`、`de52142`）。已在进度文件中更正（`checkpoints/p05/evidence/p05-s2r3/PROGRESS_CHECKPOINT.txt`）。

**库哈希**（同一台机器，默认选项）：

| 树 | `libS4.a` sha256（前 16 位） | 说明 |
|---|---|---|
| B | `fb9ac3f5…` | 与阶段 3 记录一致 |
| A | `865c5893…` | 与阶段 3 记录一致 |
| H | `f053bfea…` | 与阶段 3 记录一致（阶段 2 的 pristine H 亦为此值） |

整库哈希因调试字符串中的构建路径而不同，故**逐字节一致一律比较目标文件**（各树 24 个目标）：

- B 与 A 不同的目标（7）：`S4.o`、`fmm_FFT.o`、`fmm_PolBasisJones.o`、`fmm_PolBasisNV.o`、`fmm_PolBasisVL.o`、`fmm_closed.o`、`fmm_kottke.o`。
- A 与 H 不同的目标（6）：`S4.o`、`fmm_PolBasisJones.o`、`fmm_PolBasisNV.o`、`fmm_PolBasisVL.o`、`fmm_closed.o`、`fmm_experimental.o`。
- 阶段 2 的 pristine H 与"宏全部关闭的 H 组合"：库哈希相同（`f053bfea…`），24/24 目标逐一一致。

**构建选项原文**（仓库默认，三树相同）：

```
g++ -c -O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC -IS4 -IS4/RNP -IS4/kiss_fft <src> -o <obj>
```

证据：`checkpoints/p05/evidence/p05-s2r3/build3a/OBJECT_IDENTITIES.txt`、`stage3/library-hashes.txt`、`stage4/build-A.log`、`stage4/build-H.log`。

**测试树的组成（均由 `git archive` 导出副本得到，不写 `S4/`）**：

- B 带 seam：`apply_seam_r2.py --families A,B,C,D` 写入 B 导出，库以 `CPPFLAGS=-DS4_TEST_LINEARSOLVE_SEAM -DS4_TEST_LINEARSOLVE_SEAM_NULLINFO -DS4_TEST_ALLOC_SEAM -DS4_TEST_KOTTKE_SEAM` 重建（与 S2R2 的 `seam4-base-37a82e8` 相同方法）。
- A 带 seam：同上，用于 CUR 列（A 的 S4 树 id 与 S2R2 CUR 相同）。
- H 带 seam：`apply_seam_b2.py`（B2，7 站点）之后 `apply_seam_r2.py --families A,C,D`。**family B 不适用于 H**：其 NULL-info 锚点在 H 上匹配 0 次（`checkpoints/p05/evidence/p05-s2r3/build3a/apply-H-ABCD-check.txt`），因 S3R 已把这些 solve 改为 `&solve_info`。H 的宏全部关闭时与 pristine 逐字节一致（24/24）；宏开启时 7 个目标不同（`S4.o`、`fmm_FFT.o`、`fmm_PolBasisJones.o`、`fmm_PolBasisNV.o`、`fmm_PolBasisVL.o`、`fmm_closed.o`、`fmm_kottke.o`）。阶段 2 的 `H_SEAM_VERIFIED.txt`（B2 + C）记录的是 5 个，本轮多出的 `fmm_FFT.o`、`fmm_kottke.o` 来自 A 族与 D 族的写入。

驱动与库的对应：`bin-B/driver-d003`、`bin-A/driver-d003`、`bin-H/driver-d003`（plain，无 seam）；`bin-B/driver-d003-seam`、`bin-A/driver-d003-seam`、`bin-H/driver-d003-seam`（seam）。驱动源码为 HEAD 的 `testing/d003/src/driver_d003.cpp`（sha256 `442b9f2c…`）与 `inject_d003.cpp`（sha256 `0561159d…`）。

## 5. T1 可达性表（此前判不可达或无注入点，而本轮改判的点置顶）

### 5.1 置顶：此前判不可达或无注入点，本轮改判可达

| 点 | 此前判定（出处） | 本轮结论（实测） | 改判依据 |
|---|---|---|---|
| `fmm_closed.cpp` 130 / 133（info=NULL，ID 11 / 12） | UNREACHABLE：驱动 lattice `Lr={1,0,0,1}`，1-D 分支（`REGISTRY_T3_static.tsv`；`P05_S2R_HARNESS_SUPPLEMENT.md`） | **可达**：`closed1d` 模式下 ID 11、12 各 HIT 1 | S2R3 阶段 1 在驱动中新增 `closed1d` 模式，将其 lattice 设为 `{1,0,0,0}`（`driver_d003.cpp:75`）。这是驱动变化使其可达，不是原判断错误 |
| `fmm_closed.cpp` 138（info=NULL，ID 13） | UNREACHABLE：需要 `!use_polarization_basis`（`REGISTRY_T3_static.tsv`） | **可达**：`closed2d` 模式下 ID 13 HIT 1 | 驱动的 `closed2d` 模式（S2R3 阶段 1 新增） |
| `fmm_closed.cpp` 235（info=NULL，ID 14） | UNREACHABLE：tensor 分支仅标量材料（`REGISTRY_T3_static.tsv`） | **可达**：`tensor` 模式下 ID 14 HIT 1 | 驱动的 `tensor` 模式（`XYTENSOR_REAL`，S2R3 阶段 1 新增） |
| `fmm_experimental.cpp` 40（S4_malloc，无检查） | UNREACHABLE：`use_experimental_fmm` 只由 Lua 前端设置（`REGISTRY_T3_static.tsv`；S3 的 `S3-exp40` 行称"无注入点"） | **可达**：`experimental` 模式下 `s4malloc` NTH=1 HIT（192 B） | 驱动的 `experimental` 模式（`driver_d003.cpp:84`，S2R3 阶段 1 新增）；注入手段为既有 `s4malloc`（`--wrap`），**未新增钩子** |
| 缓存命中 `PolBasis{Jones,NV,VL}` 的 work 分配（`jones:346` / `nv:234` / `vl:243` on H） | 公开 API 不可达；"需新增注入点"（S2R2 报告，S3 的 `S3-cache-*` 行，本轮前期的判断） | **可达，内部路由**：`S4FMM_TWICE=slab` + `s4malloc` NTH=7 + `inj_call=2`，尺寸 1296/2592 B，HIT 1 | S2R2 已有此路由（`REGISTRY_T4.tsv`、`REGISTRY_T4_NVVL.tsv`、`T4_NVVL_PROBE_RECORD.txt`）。**本轮前期"注入不了"的判断与该证据冲突，已更正**。路由使用内部接口，**公开 API 路径未测到，不写成"不可达"** |
| `fmm_kottke.cpp` 的 discval `S4_malloc`（S3 的 `S3-kottke85`："无注入点"） | NOT_REGISTERED_NO_INJECTION_POINT（`REG_S3_EXPECTATIONS.tsv`） | **可达**：`s4malloc` NTH=1，16 B，HIT 1 | `CORR_2` 更正：该点已有注入（`s4malloc` 按调用序号）；另一点 work 为 family D |
| `fmm_kottke.cpp` 的 work `fft_alloc_complex(6*ng2)`（本轮新增要求） | 未登记 | **可达**：family D `kottke_alloc:31:1`，n=384，HIT 1 | `fft_alloc_complex` 直接调用 `fftw_malloc`/`KISS_FFT_MALLOC`，**不经过 `S4_malloc`**，故 `--wrap` 不覆盖，需要 family D 内容钩子（`fft_iface.cpp:48-54`） |

### 5.2 其余点的可达性（本轮实测）

| 点 | 路由 | 结论 |
|---|---|---|
| FFT work / discval（`fmm_FFT.cpp` 75 / 83；`fftjones`、`fftnv`、`fftvl`） | `s4malloc` NTH=1 / 2 | 三模式均 HIT（6144 B / 16 B） |
| PolBasis ivalues / work / vfield（三链） | `s4malloc` NTH=3 / 4 / 5 | 三模式均 HIT（192 B / 10720 或 11872 B / 1024 B） |
| PolBasis solve（H，B2 ID 375 / 265 / 273，三链与 jones/nv/vl） | `linearsolve_null2` | HITCOUNT 1，RC first 20 |
| `ComputeLayerModes` 2267 / 2295 / 2408 / 2425、`AddFieldToCache` 3977 | family C id 21 / 22 / 23 / 24 / 25 | HIT（id 25 在 jones/nv/vl 下 HIT，fft 下不调用 AddFieldToCache：HITCOUNT 0） |
| PolBasis solve info=NULL（B/A，family B ID 15 / 16 / 17） | `linearsolve_null` | HIT 1（B 与 A 均可达） |
| 历史 38 案中的 `s2b/ls-kottke-xsite`（跨站点） | `linearsolve:1:1:info` on kottke | HITCOUNT 0，INVALID（设计上不可达，历史期望即 INVALID） |

### 5.3 仍不可达或不可测的点

- **H 上的 family B（`linearsolve_null`，ID 11/15/16/17）**：H 库中 family B 钩子的引用数为 0，HITCOUNT 0。H 的对应求解已改为 info 检查，family B 的 NULL 锚点不存在（第 8.4 节，结构性差异）。
- **公开 API 路径上的缓存命中**：未测到（见 5.1）。

## 6. T2 驱动与历史字节比对

### 6.1 驱动扩展（阶段 1，提交 `8643ffe`）

驱动新增 7 个模式（`experimental`、`closed2d`、`closed1d`、`tensor`、`fftjones`、`fftnv`、`fftvl`），既有 5 个模式（`fft`、`kottke`、`jones`、`nv`、`vl`）不变。历史 10 个控制的输出与 HEAD 前的驱动**逐字节一致**（阶段 1 记录）。

### 6.2 历史字节比对（本轮）

- 历史 CONTROL 矩阵（10 个 `t4/control-*`）在 H 上两次复跑：`hist38-H-run-r1` 与 `hist38-H-run-r2` 的 rc 与日志 sha256 **38/38 逐条相同**（含全部控制行）。
- 历史 38 案在 H 与 CUR（A）上的**观察**（class、rc、rc1）**逐条相同**，差异 0（第 8.2 节）。

## 7. T3 B2 逐站点（阶段 2 的 7 站点，本轮补充的 B/A 模型对照）

**两种模型的含义（任务第 2 节第 3 条，必须区分）**：

- **family B（output model，B 与 A 使用）**：把 `info` 保持为 NULL，只把输出（RHS）覆写为单位阵。失败**不被报告**；结果被污染却返回 0，即 SILENT_SWALLOW 的机理。
- **family B2（failure model，H 使用）**：设置 `*info = 1`（模拟零主元），并同样覆写 RHS。失败**被报告**给调用方；H 的既有检查返回 20 或 1。

**两种模型不同。** 因此下表中 B/A 与 H 的差异**同时包含修复与模型**，不能把它写成修复效果的唯一证据。ComputeLayerModes 与 AddFieldToCache 三树都用 family C（同一模型），其差异可归于修复；PolBasis 与 closed 的 B/A-to-H 差异只能说明"两种模型各自的行为"。

| 站点（H 行） | B 与 A 的对应 | 模型（B/A） | H 模型 | 观察（B / A / H） | 标注 |
|---|---|---|---|---|---|
| closed 134 / ID 11（A 130） | family B 11 | output | B2 | SILENT / SILENT / REPORTED_FAILURE | **模型不同** |
| closed 138 / ID 12（A 133） | family B 12 | output | B2 | SILENT / SILENT / REPORTED_FAILURE | **模型不同** |
| closed 144 / ID 13（A 138） | family B 13 | output | B2 | SILENT / SILENT / REPORTED_FAILURE | **模型不同** |
| closed 244 / ID 14（A 235） | family B 14 | output | B2 | SILENT / SILENT / REPORTED_FAILURE | **模型不同** |
| PolBasisJones 375（A 369） | family B 15 | output | B2 | SILENT / SILENT / REPORTED_FAILURE | **模型不同** |
| PolBasisNV 265（A 260） | family B 16 | output | B2 | SILENT / SILENT / REPORTED_FAILURE | **模型不同** |
| PolBasisVL 273（A 268） | family B 17 | output | B2 | SILENT / SILENT / REPORTED_FAILURE | **模型不同** |

**ID 对应**由 LinearSolve 参数文本核对（而非行号）：A 130 `(Epsilon_inv, &Epsilon2[n+n*n2])` ↔ family B 11 ↔ H 134，依此类推（`REG_3C3_CLOSED.tsv` 头部）。

**阶段 2 的 B2 站点记录**：`REG_B2_EXPECTATIONS.tsv` 登记于运行之前，其中写"no run yet"的行（134、138、244、375、265、273）是**登记时**的状态；之后阶段 2 确实在 `stage2/runs/` 下对这 7 个站点各产生了一个输出文件（`b2-134-closed1d.out` 至 `b2-375-fftjones.out`）。该登记文件未改写。本轮对 7 站点全部重新实测（3b 与 3c.3 的 H 行、`closedH/`、`nth-scan/`）。


## 8. 阶段 3：三列对照与历史矩阵复跑

所有表格由 `checkpoints/p05/evidence/p05-s2r3/stage3/formal-*` 的 raw 记录机械生成；每树两次运行，**两次一致**。hit 列为驱动注入计数；rc1、rc2 为驱动打印的第一次、重试返回码。

### 8.1 运行器回归（3a 与 3b 前缀改动）

改动前后，同一登记（`R2D_EXPECTATIONS.tsv` 的 BASE/CUR 行，26 行）、同一驱动，逐字段比较 raw 记录（去掉日志绝对路径）：

| 树 | 改动前 | 改动后（`bdd2b56` + `d8b4276`） | 字段差异 | index 文本 |
|---|---|---|---|---|
| BASE（seam） | matched 11/13 | matched 11/13 | **0** | 逐字一致 |
| CUR（seam） | matched 12/13 | matched 12/13 | **0** | 逐字一致 |

改动前后的拒绝行为：非法树名的退出码相同（2），错误消息的合法集合由 `{BASE,CUR}` 变为 `{BASE,CUR,H}`，这是允许的唯一差异。

**两个回归基线的前提（已核实）**：旧输出必须用 seam 驱动产生（plain 驱动使 linearsolve/alloc 行全部 INVALID，hit 0）。S2R2 的 BASE、CUR 树即为 seam 构建（`seam4-base-37a82e8`、`seam4-cur-aa1c51d`）。

**与 S2R 历史的交叉核对**：BASE 11/13 与 CUR 12/13 与 `P05_S2R_HARNESS_SUPPLEMENT.md` 的记录一致；其中的 2 条 BASE 不匹配与 1 条 CUR 不匹配是 D-1、D-2 所记的登记错误，未改写。

### 8.2 阶段 3b：八个红点的三列对照（REG_3B_THREECOLUMN.tsv，sha256 `e497c4a9…`）

B、A 列使用 family B（PolBasis，输出模型）或 family C（分配返回 NULL）；H 列 PolBasis 用 B2、其余用 family C。**模型不同**的行已标注。

| 点 | BASE (37a82e8) | CUR (876181c，A) | H (64eb0b5) | 两次一致 | 标注 |
|---|---|---|---|---|---|
| PolBasisJones 369（A 行号） | SILENT_SWALLOW (hit 1) | SILENT_SWALLOW (hit 1) | REPORTED_FAILURE (hit 1) | 是 | **模型不同**（B/A 为输出模型，H 为 B2 失败模型） |
| PolBasisNV 260 | SILENT_SWALLOW (hit 1) | SILENT_SWALLOW (hit 1) | REPORTED_FAILURE (hit 1) | 是 | **模型不同** |
| PolBasisVL 268 | SILENT_SWALLOW (hit 1) | SILENT_SWALLOW (hit 1) | REPORTED_FAILURE (hit 1) | 是 | **模型不同** |
| ComputeLayerModes 2267（family C id 21） | CRASH (hit 1) | CRASH (hit 1) | REPORTED_FAILURE (hit 1) | 是 | 同一模型（family C），差异可归于修复 |
| ComputeLayerModes 2295（id 22） | CRASH (hit 1) | CRASH (hit 1) | REPORTED_FAILURE (hit 1) | 是 | 同一模型 |
| ComputeLayerModes 2408（id 23） | SILENT_SWALLOW (hit 1) | SILENT_SWALLOW (hit 1) | REPORTED_FAILURE (hit 1) | 是 | 同一模型 |
| ComputeLayerModes 2425（id 24） | SILENT_SWALLOW (hit 1) | SILENT_SWALLOW (hit 1) | REPORTED_FAILURE (hit 1) | 是 | 同一模型 |
| AddFieldToCache 3977（id 25，jones） | CRASH (hit 1) | CRASH (hit 1) | REPORTED_FAILURE (hit 1) | 是 | 同一模型 |

**读法**：8 个红点在 B 与 A 上均为红（CRASH 或 SILENT_SWALLOW），在 H 上均为 REPORTED_FAILURE（修后绿）。这是 **S3R 缺失的"修前红、修后绿"装置观察**，不是 P05-S4 验证。PolBasis 三点的 B/A-to-H 差异混合了修复与模型，不能单独归于修复。

### 8.3 阶段 3c：缓存命中与 kottke（执行映射 `EXEC_3C_CORR2.tsv`，期望来自 `CORR_S3_EXPECTATIONS_2.tsv`）

缓存命中行使用 `t4/` 前缀（运行器据此设 `S4FMM_TWICE=slab` 并以 rc2 判定，即 `inj_call=2`）；kottke 行使用普通前缀（rc1 判定）。

| 点 | BASE | CUR | H | 判定依据 |
|---|---|---|---|---|
| cache-hit jones（1296 B，NTH 7） | CRASH（hit 1，信号 11） | REPORTED_FAILURE（rc1 0，rc2 20） | REPORTED_FAILURE（rc1 0，rc2 20） | rc2 |
| cache-hit nv（2592 B，NTH 7） | CRASH | REPORTED_FAILURE（rc1 0，rc2 20） | REPORTED_FAILURE（rc1 0，rc2 20） | rc2 |
| cache-hit vl（2592 B，NTH 7） | CRASH | REPORTED_FAILURE（rc1 0，rc2 20） | REPORTED_FAILURE（rc1 0，rc2 20） | rc2 |
| kottke work `fft_alloc_complex(6*ng2)`，n = 384（family D） | CRASH | REPORTED_FAILURE（rc1 20，rc2 0） | REPORTED_FAILURE（rc1 20，rc2 0） | rc1 |
| kottke discval `S4_malloc`，16 B（NTH 1） | CRASH | REPORTED_FAILURE（rc1 20，rc2 0） | REPORTED_FAILURE（rc1 20，rc2 0） | rc1 |

**关于 cache-hit 的驱动文字**：驱动的 RESULT 行对 cache-hit 运行输出 "injection reached, rc1 0 (failure swallowed)"，这是驱动只看 rc1 的旧逻辑。本判定以 rc2（第二次调用，`inj_call=2`）为准，驱动文字不被使用（任务第 1 节）。驱动为历史文件，未改。

**kottke 两点的 CRASH 与 REPORTED_FAILURE 的对照**：B 上两点均段错误（rc 139，stderr 中 HIT 行先于崩溃输出）；A、H 上两点均为 REPORTED_FAILURE。这给出两点的**失败类别**，而非仅可达性。

**CORR_2 更正（已披露）**：原 `S3-cache-*` 行写"INVALID_OR_HIT，需要新注入点"，与 `REGISTRY_T4` 与 `REGISTRY_T4_NVVL` 的既有路由冲突，已由 CORR_2 另存更正。原 `S3-kottke85` 行写"NOT_REGISTERED，无注入点"，已由 CORR_2 替换为两点。

### 8.4 阶段 3c：fmm_experimental:40、closed 四点、FFT→PolBasis 链

**fmm_experimental:40**（`REG_3C1_EXPERIMENTAL.tsv`，`3c1-exp40`，sha256 `f8322238…`）：

| 树 | 类别 | 证据 |
|---|---|---|
| BASE | CRASH（信号 11，hit 1） | 源码：`fmm_experimental.cpp:40` 之后无检查，`:57-60` 经 NULL 的 `ivalues` 写入 |
| CUR | CRASH（信号 11，hit 1） | 同上（A 无检查） |
| H | REPORTED_FAILURE（rc1 20，hit 1） | 源码 `:44` 返回 20（S3R `35cd7b3`）；与 CORR_1 一致 |

注入手段：既有 `s4malloc`（`--wrap`），**未新增钩子**。原 `S3-exp40` 行写"无注入点"，已由 CORR_1 更正。

**closed 四点**（`REG_3C3_CLOSED.tsv`，sha256 `c640f5a3…`，两次一致）：

| 点（ID：B/A/H） | B（family B 输出模型） | A（family B 输出模型） | H（B2 失败模型） | 标注 |
|---|---|---|---|---|
| closed:130（ID 11；H 134），closed1d | SILENT_SWALLOW（rc1 0） | SILENT_SWALLOW（rc1 0） | REPORTED_FAILURE（rc1 20） | **模型不同** |
| closed:133（ID 12；H 138），closed1d | SILENT_SWALLOW | SILENT_SWALLOW | REPORTED_FAILURE | **模型不同** |
| closed:138（ID 13；H 144），closed2d | SILENT_SWALLOW | SILENT_SWALLOW | REPORTED_FAILURE | **模型不同** |
| closed:235（ID 14；H 244），tensor | SILENT_SWALLOW | SILENT_SWALLOW | REPORTED_FAILURE | **模型不同** |

**closed 的可达性已改判**（第 5.1 节）。B 与 A 的 SILENT 与 H 的 REPORTED 之差来自模型（输出模型与失败模型）与修复两者，不能单独归于修复。

**FFT→PolBasis 链**（`REG_3C2_FFTCHAIN.tsv`，sha256 `5e46f862…`，48 行，两次一致）：

| 模式 | 点（NTH） | BASE | CUR | H |
|---|---|---|---|---|
| fftjones / fftnv / fftvl | FFT work（1） | CRASH | REPORTED_FAILURE | REPORTED_FAILURE |
| 同上 | FFT discval（2） | CRASH | REPORTED_FAILURE | REPORTED_FAILURE |
| 同上 | PolBasis ivalues（3） | CRASH | REPORTED_FAILURE | REPORTED_FAILURE |
| 同上 | PolBasis work（4） | CRASH | REPORTED_FAILURE | REPORTED_FAILURE |
| fftjones | PolBasis vfield（5） | SILENT_SWALLOW | REPORTED_FAILURE | REPORTED_FAILURE |
| fftvl | PolBasis vfield（5） | SILENT_SWALLOW | REPORTED_FAILURE | REPORTED_FAILURE |
| fftnv | PolBasis vfield（5） | **CRASH** | REPORTED_FAILURE | REPORTED_FAILURE |
| fftjones / fftnv / fftvl | PolBasis solve（B2 375 / 265 / 273，仅 H） | — | — | REPORTED_FAILURE |

**[未验证] 的一处**：B 上 PolBasis vfield 的类别按模式不同（fftnv 段错误；fftjones 与 fftvl 吞掉）。`fmm_PolBasisNV.cpp:122` 的 vfield 分配之后、`:129` 写入之前无 NULL 检查，按此推断 NV 段错误；但 `fmm_PolBasisVL.cpp:127` 有同样结构却观察到吞掉，`fmm_PolBasisJones.cpp:167` 也未见 NULL 检查却吞掉。**源码阅读未能完整解释这一分裂**，仅有实测，标 [未验证]。

### 8.5 历史矩阵在 H 上复跑（3d）

映射文件 `MAP_3D_*.tsv` 为新登记（第 3.1 节）。H 行的期望**沿用同一用例的 CUR 期望**（§2 第 4 条(c)）。`matrix_d003.py` 与 `judge_d003.py` 未改。

**(i) 历史 38 案（`MAP_3D_HIST38_H.tsv`）**：

- 两次复跑的 rc 与日志 sha256：**38/38 逐条相同**。`classify`：两次均 `expectation_mismatches=18`，index 逐字一致。
- **H 与 CUR 的观察逐条比较（38 案）：差异 0**（class、rc、rc1 三者均一致）。期望列在两者之间完全相同。

**18 条与历史期望的差异**（全部为"→ REPORTED_FAILURE"，允许方向；但**在 CUR 上已存在**，不由 S3R 引入）：

| 案 | 历史期望 | H 与 CUR 观察 | 说明 |
|---|---|---|---|
| `t5/plan1-{fft,kottke,jones,nv,vl}-ng9`（5） | CRASH | REPORTED_FAILURE | 历史期望写于 S2 修复之前；FFT plan 失败的传播已由 `b00b630` 加入 |
| `t5/exec1-{fft,kottke,jones,nv,vl}-ng9`（5） | SILENT_SWALLOW | REPORTED_FAILURE | 同上（exec 边界模拟，`b00b630`） |
| `t5/scratch{1,2}-fft-ng1`（2） | SILENT_SWALLOW | REPORTED_FAILURE | FFT 执行 scratch 分配的检查，`b00b630` |
| `s2/s4malloc{1,2}-fft-ng9`（2） | CRASH | REPORTED_FAILURE | FFT work / discval 的检查，`b00b630` |
| `s2b/ls-{fft,kottke}-{info,faithful}-k1`（4） | SILENT_SWALLOW | REPORTED_FAILURE | solve_info 检查，`b00b630`（FFT 与 kottke） |

**(ii) S2R R2-D 13 案（`MAP_3D_R2D_H.tsv`，26 行 = 13 案 × BASE/CUR）**：两次复跑一致，matched 6、mismatched 7。逐条：

| 案 | 请求 | CUR 期望 | H 观察 | 类别 | 处理 |
|---|---|---|---|---|---|
| `new/A-fft-info-k1` | linearsolve:1:1:info | REPORTED_FAILURE | REPORTED_FAILURE（rc1 20） | 一致 | — |
| `new/A-kottke-info-k1` | linearsolve:2:1:info | REPORTED_FAILURE | REPORTED_FAILURE | 一致 | — |
| `new/N-jones-id15-k1` | linearsolve_null:15:1 | SILENT_SWALLOW | **INVALID**（hit 0） | **结构性差异** | 见 8.6（用户决定 D-U1） |
| `new/N-nv-id16-k1` | linearsolve_null:16:1 | SILENT_SWALLOW | **INVALID**（hit 0） | **结构性差异** | 见 8.6 |
| `new/N-vl-id17-k1` | linearsolve_null:17:1 | INVALID | INVALID（hit 0） | 巧合匹配，**不计为一致** | 见 8.6 |
| `new/N-closed-id11-k1` | linearsolve_null:11:1 | INVALID | INVALID（hit 0） | 一致（INVALID 为设计结果） | — |
| `new/C-alloc-id21-k1` | alloc:21:1 | CRASH | REPORTED_FAILURE（rc1 20） | 允许方向（S3R `73e00ef`） | — |
| `new/C-alloc-id22-k1` | alloc:22:1 | CRASH | REPORTED_FAILURE | 允许方向（S3R `73e00ef`） | — |
| `new/C-alloc-id23-k1` | alloc:23:1 | SILENT_SWALLOW | REPORTED_FAILURE | 允许方向（S3R `73e00ef`） | — |
| `new/C-alloc-id24-k1` | alloc:24:1 | SILENT_SWALLOW | REPORTED_FAILURE | 允许方向（S3R `73e00ef`） | — |
| `new/C-alloc-id25-k1` | alloc:25:1（jones） | CRASH | REPORTED_FAILURE | 允许方向（S3R `e83255f`） | — |
| `new/C-alloc-id25-fft` | alloc:25:1（fft） | INVALID | INVALID（hit 0） | 一致（fft 不调用 AddFieldToCache） | — |
| `new/F-fmm-s4malloc1-fft` | s4malloc | REPORTED_FAILURE | REPORTED_FAILURE | 一致 | — |

**`N-vl-id17-k1` 的 INVALID 匹配是巧合，不计为一致**：该行的 CUR 期望 INVALID 本身是登记错误（S2R 的 D-1；CUR 实际观察 SILENT_SWALLOW），H 的 INVALID 来自 family B 在 H 上不存在（8.6），二者叠加恰好相等。

**(iii) S2R2 17 case（`MAP_3D_S2R2_H.tsv`）**：两次复跑 **17/17 matched**，逐行差异 0，全部 hit = 1（`t4/cache-hit-work-{k7,nv-k7,vl-k7}`、`t1/kottke-work-k1`、`t2/*` 的 13 个 S4_malloc 点）。S2R2 的 CUR 观察没有同方法的 raw 复跑，故不作逐条 H-CUR 观察比较（仅期望列比对）。

### 8.6 结构性差异（用户决定 D-U1）

`N-jones-id15-k1` 与 `N-nv-id16-k1` 在 H 上的观察为 INVALID（hit 0），CUR 期望为 SILENT_SWALLOW。

- **测得的原因**：H 库中 family-B 钩子 `S4_TEST_LINEARSOLVE_NULLINFO_AFTER` 的引用数为 **0**；`linearsolve_null` 的 ID 11、15、16、17 在 H 上 HITCOUNT 均为 0。
- **机理**（源码）：S3R 提交 `df3bb02` 把 PolBasis 的 `LinearSolve` 从 `NULL` 改为 `&solve_info`，family B 的锚点（`... NULL, NULL);`）在 H 上匹配 0 次（`checkpoints/p05/evidence/p05-s2r3/build3a/apply-H-ABCD-check.txt`），因此 H 上不存在"info=NULL 的求解点"。
- **处理**（用户决定 D-U1）：记为"H 无等价点"，**不计入方向差异**，**不计为一致**，列为**结构性差异**。不新增钩子，不改期望。
- **与 §4 方向规则的关系**：该两行的变化（SILENT → INVALID）不在"向 REPORTED_FAILURE"的允许方向内。用户已决定以结构性差异处理，**本报告不把它解释为修复效果**，也不据此放宽方向规则。


## 9. 阶段 4：Jones 正常路径差异的只读对照（数据，不裁决）

**背景**：S3R 报告 §6.3 记录 `df3bb02` 之后 H 与 A 的 Jones 场有 144 个分量全部不同，最大相对差 1.18e-12。本节在导出副本中复现并比较四种编译选项。**不替用户选择 a、b、c。**

**方法**（脚本 `testing/d003/stage4/opt_jones.sh`，提交 `9d29877`；比较 `testing/d003/stage4/reldiff.py`）：

- 仅重编译 `fmm_PolBasisJones.cpp`，选项原文替换默认的 `-O3 -march=native -fcx-limited-range`；其余编译参数（`-Wall -fno-exceptions -fPIC -IS4 -IS4/RNP -IS4/kiss_fft`）保持不变。
- 其余目标文件取自该树自己的**默认构建**（同一份）：用 `ar r` 替换 `libS4.a` 中的 `fmm_PolBasisJones.o` 一个成员，`ranlib`，再以相同的驱动源码与 `LIBFLAGS` 链接。
- 每个二进制运行两次（first-call 与 retry 两个转储），确认确定性。
- 相对差定义：`rel = |a − b| / max(|a|, |b|)`（两者皆为 0 时取 0），按 144 个分量统计。

**选项原文**：a) `-O0`；b) `-O2 -ffp-contract=off`；c) `-O3 -mno-fma`（保留 `-fcx-limited-range`）；d) 仓库默认 `-O3 -march=native -fcx-limited-range`。

**自检**：选项 d 在 A 与 H 上复现了默认转储与默认目标（`ar` 成员 sha16 `8177bff9…` 与 `fb5f9e33…`，与阶段 3 记录一致）。

| 选项 | 树 | Jones 目标 sha16 | 确定性（run1 = run2） | A vs H：分量数差异 | max rel | median rel | 字节一致 |
|---|---|---|---|---|---|---|---|
| a `-O0` | A | `6e906773…` | 是 | **0 / 144** | 0 | 0 | **是** |
| a `-O0` | H | `c1e33cd2…` | 是 | | | | |
| b `-O2 -ffp-contract=off` | A | `27c14e2a…` | 是 | **0 / 144** | 0 | 0 | **是** |
| b | H | `8e21a9c1…` | 是 | | | | |
| c `-O3 -mno-fma -fcx-limited-range` | A | `ab13bc53…` | 是 | **0 / 144** | 0 | 0 | **是** |
| c | H | `26c67544…` | 是 | | | | |
| d `-O3 -march=native -fcx-limited-range`（默认） | A | `8177bff9…` | 是 | **144 / 144** | **1.1829e-12** | **4.3043e-14** | **否** |
| d | H | `fb5f9e33…` | 是 | | | | |

**最大相对差的位置**（选项 d）：分量 `('H', 50)`。

**retry 转储**：四个选项下，A 与 H 的 retry 转储与 first-call 结果相同（a、b、c 字节一致；d 为 144/144 不同，max rel 1.1829e-12，median 4.3043e-14）。同一树内 first 与 retry 一致（0 差异）。

**NV 与 VL 复核（选项 d，默认构建）**：A 与 H 的 `FMM_MODE=nv` 与 `FMM_MODE=vl` 第一次调用转储**字节一致**（144/144 相同）。

**事实陈述**：
- 在选项 a、b、c 下，A 与 H 的 Jones 场字节一致。
- 在选项 d 下，A 与 H 的 Jones 场 144 个分量全部不同，最大相对差 1.1829e-12，与 S3R 报告的 1.18e-12 一致。
- 两次运行在四个选项下均确定。

**[推断]**：若 a、b、c 字节一致，则 H 与 A 的源码差异（`df3bb02`：`info` 由 NULL 改为指向 `solve_info` 的指针，并增加检查）在这些选项下不产生数值差异；d 下的差异可能来自优化器在 `-march=native`（FMA 与向量化）下对同一函数体的调度不同，而非求解算法改变。**本轮未验证该机理**（未反汇编比较，未做 `-march=native` 去除 FMA 的单独对照）。

**不在本节决定的事项**：是否接受 d 下的容差、是否改变状态通道、是否撤回 commit 3，均属用户决定。本节不选择 a、b、c 中的任何一个。


## 10. 偏离与违规（单一违规次数表）

### 10.1 写仓库外路径的违规尝试（唯一的违规次数表）

依据：`checkpoints/p05/evidence/p05-s2r3/stage3/DEVIATIONS_AND_VIOLATIONS_S2R3_CONT2.txt` 第 A 节。

| # | 轮次 | 命令（摘要） | 是否落盘 | 说明 |
|---|---|---|---|---|
| 1 | 上一轮（S2R3 前一会话，按任务陈述） | `git show ... > /tmp/__never_write` | **无法核实** | 在本仓库全文检索 `never_write`：**无匹配**。无法判断它与更早轮次披露的 `/tmp` 违规（P05_S2_TEST_HARNESS.md 的 P-1：`/tmp/x`、`/tmp/__nope`、`/tmp/__ev_check_ignored`、`/tmp/__files_a`、`/tmp/__a`、`/tmp/__x`）是否为同一次。本报告不把它计为已确认。 |
| — | 本续作（自查） | 无 | — | 回顾本续作全部 shell 命令：未发现任何写入 `/tmp` 或仓库外路径的命令。含 `/tmp` 字面量的两条命令均为只读（一条检索、一条 `ls -A /tmp`）。 |

**本续作的违规次数：0（自查结论，非系统审计）。** 自查不覆盖交互 shell 中的全部命令；strace 抽样只覆盖被跟踪的进程（第 12 节）。

### 10.2 其它偏离（逐条，均已纠正或披露）

| 编号 | 偏离 | 纠正 |
|---|---|---|
| D-1 | 本续作开工时未取 `/tmp` 快照与 strace 开始样本；两次 strace 抽样与 `/tmp` 快照均在结束阶段取得 | 已披露。不能满足 §6 的"开始与结束各一次"要求 |
| D-2 | 后台构建循环的相对重定向在错误目录写出 `res-A.txt`、`res-H.txt` 到仓库根 | 绝对路径核对后删除，未提交 |
| D-3 | `matrix_r2.py run` 收到相对驱动路径，所有行 "could not start driver"（rc None） | 产物隔离至 `regress-3a/failed-relative-path/`，改绝对路径重跑 |
| D-4 | 回归初次使用 plain 驱动，linearsolve/alloc 行全部 INVALID | 原因：未打 seam。改为打 A、B、C、D 族 seam 后重跑 |
| D-5 | 分类时只读 stdout，致使崩溃的 B 运行被判 INVALID | 合并 stdout 与 stderr 后判为 CRASH；正式运行只经运行器 |
| D-6 | 手工分类中 B fftjones NTH5 用了 rc 139，实际为 1 | 按记录改为 SILENT_SWALLOW；记录保留 |
| D-7 | 初期把 A（876181c）写成"修复后"，实为 S3R 之前 | 在进度文件中更正，于 3b 登记前完成 |
| D-8 | 登记格式错误（表头无 `#`、树名用 B/A、一处依据误引阶段 2 记录） | 均在对应登记冻结前修正；草稿保留 |
| D-9 | `CORR_2` 的 case 名为逻辑名 `S3C2-*`，运行器以 `t4/` 前缀决定路由 | 另建执行映射（期望列机械复制），未改任何期望 |
| D-10 | `REG_3C2` 首版 B vfield 期望全部写成 CRASH，与实测分裂不符 | 草稿 v1 保留未登记；以判定器输出重写后冻结（v2） |
| D-11 | 族 C 点 25 在 fft 模式下不可达（HITCOUNT 0） | 在 jones、nv、vl 下测得；3b 使用 jones |
| D-12 | 历史 38 案与 R2D 的期望不匹配项（18、7） | 逐条分类（第 8.5 节）；R2D 的两条结构性差异按用户决定 D-U1 处理 |
| D-13 | 驱动对 cache-hit 运行的 RESULT 行写 "failure swallowed"（只看 rc1） | 判定以 rc2 为准；驱动为历史文件，未改 |
| D-14 | 驱动的检查"失败调用返回分配码 1"写死为 1，而 H 返回 20，实验路径输出显示 FAILED | 判定器不使用该行；驱动未改 |
| D-15 | B 上 PolBasis vfield 的类别按模式分裂，源码阅读未能解释 | 标 [未验证]（第 8.4 节） |
| D-16 | 3c 运行使用 10 列运行器格式，cache-hit 与 kottke 的登记为 9 列 | 机械转换，期望列未变（已核对） |
| D-17 | 3d 因 §8 条件（N-* 行方向外变化）停下，经用户决定 D-U1 后续作 | 按用户决定记录，未擅自放宽规则 |
| D-18 | 阶段 3 的若干子步（3b、3c、3d）未产生 testing/ 代码改动，故无对应提交 | 结果在证据目录与本报告；不以空提交凑数 |

## 11. 仍未闭合缺口

1. **阶段 S2 与 S3 补充仍未签收**：本报告不宣布任何阶段完成。
2. **公开 API 路径上的缓存命中**：未测到。当前只有内部路由 `S4_Simulation_DestroyLayerModes` 覆盖（第 5.1 节）。
3. **H 上的 family B（info=NULL 的 PolBasis 与 closed 求解）**：在 H 上不存在等价点（第 8.6 节，结构性差异）。该类别的 H 侧证据只有 B2 模型，不是同一模型。
4. **B 上 PolBasis vfield 的类别分裂**（fftnv 段错误；fftjones、fftvl 吞掉）：源码阅读未完整解释（[未验证]）。
5. **Jones d 选项的机理**：本轮只给出 [推断]，未做反汇编或 `-march=native` 去 FMA 的单独对照。
6. **模型差异不能分离修复效应**：PolBasis 与 closed 的 B/A-to-H 差异混合了模型与修复。若要单独测修复效应，需要同一模型（同为 family B 或同为 B2）在 A 与 H 上的对照，本轮未做（family B 在 H 上不存在；B2 在 A 上不存在）。
7. **S2R2 的 17 case 缺少同方法的 CUR 复跑**：仅有 H 的复跑与期望比对，没有 H-CUR 逐条观察比较。
8. **`REG_B2_EXPECTATIONS.tsv` 中 6 行 "no run yet"**：登记时状态，之后已运行，本轮已重测；登记文件未改写（第 7 节）。
9. **驱动文字与判定不一致**（D-13、D-14）：历史驱动未改。
10. **七个 info=NULL 站点的注入式红绿证据**：本轮 B/A 列为 family B 输出模型，不是 info=NULL 的失败模型；失败模型只在 H 上测得（B2）。
11. **`fmm_experimental:40` 的 B/A 类别（CRASH）**：为源码推断后实测确认；但 A 与 B 的 `experimental` 路径未经过与 H 相同的全部模式检查。
12. **strace 与 /tmp 审计**：仅为两次抽样（结束阶段），不是穷尽审计；不覆盖交互 shell。
13. **阶段 2 记录的 `closed` 不可达判断**（`REGISTRY_T3_static.tsv`）已被本轮推翻（第 5.1 节）。该登记文件未改写；其结论在报告中标为已被本轮实测取代。
14. **`REG_S3` 的 B 列行号基准**：`REG_S3` 中的 "B line 366" 指的是**带 seam 的 B 导出**中 family-B hook 的行（已核对：`build3a/B/S4/fmm/fmm_PolBasisJones.cpp` 第 366 行）；同一文件纯净导出中的 LinearSolve 行为 361。两者是不同参照基准，不是错误，期望类别不受影响。登记未改写。

## 12. 收尾核对（执行结果）

| 项 | 结果 | 方法 |
|---|---|---|
| `git status` | 报告文件为唯一未跟踪项（本报告提交前）；其余干净 | `git status --porcelain` |
| `S4/` 相对 `64eb0b5` | **0 改动** | `git diff --name-only 64eb0b5 -- S4/` |
| `S4/` 工作区相对 HEAD | **0 改动** | `git status --porcelain -- S4/` |
| 越界路径数（本续作提交相对 `5fb66d5`） | **0**（全部在 `testing/d003/` 与 `checkpoints/p05/` 内） | `git diff --name-only 5fb66d5 HEAD` 过滤 |
| HEAD 与分支 | 提交前 HEAD = `9d29877`；分支 `codex/p05-d003-fft-error-propagation` | `git rev-parse`、`git branch --show-current` |
| `/tmp` 顶层快照 | **结束快照**：0 条目，sha256 `e3b0c442…`。**开始快照未在本续作取得**（第 10.2 节 D-1） | `ls -A /tmp \| sha256sum` |
| strace 抽样 | **两次，均在结束阶段**（第 10.2 节 D-1）。样本 1：`matrix_r2.py run`（H，17 case）385 事件，`/tmp` 0，仓库外写入 open 0。样本 2：`matrix_d003.py run`（A 驱动，38 案）681 事件，`/tmp` 0，仓库外写入 open 0。 | `strace -f -e trace=openat,creat,mkdir,mkdirat,rename,renameat,renameat2,unlink,unlinkat,execve` |

**strace 的限制**：两次抽样不覆盖交互 shell 命令，也不是穷尽审计。它们只能说明被跟踪的进程本身未写入 `/tmp` 或仓库外。

## 13. 对 S3 补充收尾与 P05-S4 的输入

本报告不替用户裁决下列事项，只列出数据与其所处的状态。

**对 S3 补充收尾（ComputeLayerModes、AddFieldToCache、PolBasis info=NULL 的修复）**：

- 八个红点在 B 与 A 上为红，在 H 上为 REPORTED_FAILURE（第 8.2 节），两次一致。这是装置观察，符合"修前红、修后绿"的形式，但**不是验证**。
- S3 声称已处理而装置显示未修好的点（任务所称 `fmm_kottke:78`）：**本轮在 H 上未观察到该点未修好**。H 上 kottke work（family D）与 discval（`s4malloc` NTH=1）均为 REPORTED_FAILURE（第 8.3 节）。
- PolBasis 三点的 B/A-to-H 差异混合了模型，不能作为修复效果的唯一证据（第 7 节）。
- Jones 的 `df3bb02` 正常路径差异仍未裁决（第 9 节）。用户需决定 a、b、c 或容差或撤回。

**对 P05-S4 验证的输入**：

- 缓存命中（jones、nv、vl）的失败类别在 H 上为 REPORTED_FAILURE，可由内部路由复现（第 8.3 节）；公开 API 路径未测（第 11 节第 2 条）。
- H 上的 family-B 类别不存在；P05-S4 若要求 info=NULL 的失败模型，必须接受 B2 作为替代，或在用户批准下新增钩子。
- 历史 38 案、R2D 13 案、S2R2 17 case 的 H 复跑结果（第 8.5 节）可作为 P05-S4 的基线，但其期望列来自历史登记，其中 18 + 2 条与观察不符的历史期望须先由用户处理。
- Jones 数据（第 9 节）为 P05-S4 的正常路径判定提供输入；选择由用户做。
- P05-S4 的"正负对照、失败后模式不安装、同对象重试与全新对象等价、ASan/UBSan 正向对照、不改源码"要求尚未在本续作中检验。

## 14. 遗留问题（上一轮判断的更正）

**上一轮的两项判断与 S2R2 的证据冲突，本轮已更正**：

1. **"nv/vl 缓存命中点公开 API 不可达"**：此判断不准确。准确的是：公开 API 路径未测到；内部路由 `S4FMM_TWICE=slab` + `s4malloc` NTH=7 已测到命中，并已有 S2R2 的证据（`checkpoints/p05/evidence/p05-s2r2/REGISTRY_T4_NVVL.tsv`、`T4_NVVL_PROBE_RECORD.txt`）。
2. **"需新增注入点"**：此判断与 S2R2 证据冲突。S2R2 已有路由，本轮复用，未新增注入点。

**本轮检索过的证据文件**（用于上述更正与 closed、experimental 的可达性判断）：

- `checkpoints/p05/evidence/p05-s2r2/`：`REGISTRY_T4.tsv`、`REGISTRY_T4_NVVL.tsv`、`T4_NVVL_PROBE_RECORD.txt`、`REGISTRY_T2_v2.tsv`、`REGISTRY_T2_v2_SUPPLEMENT.tsv`、`REGISTRY_T3_static.tsv`、`hist38-cur/index.txt`、`hist38-base/index.txt`、`seam4-base-37a82e8/apply.txt`、`seam4-cur-aa1c51d/apply.txt`。
- `checkpoints/p05/evidence/p05-s2r/`：`R2D_EXPECTATIONS.tsv`、`R2D_REGISTRY_TIMESTAMP_UTC.txt`。
- `checkpoints/p05/evidence/p05-s2r3/`：`PROGRESS_CHECKPOINT.txt`、`CONTROL_METHOD_NOTE.txt`、`REGISTRY_T3_T4_EXPECTATIONS.tsv`、`stage2/REG_B2_EXPECTATIONS.tsv`、`stage2/runs/`、`stage3/REG_S3_EXPECTATIONS.tsv`、`stage3/CORR_S3_EXPECTATIONS_1.tsv`。
- 已提交报告：`checkpoints/p05/P05_S2R_HARNESS_SUPPLEMENT.md`（D-1、D-2、D-3）、`checkpoints/p05/P05_S2R2_HARNESS_CLOSEOUT.md`、`checkpoints/p05/P05_S3R_MINIMAL_FIX_SUPPLEMENT.md`（§5、§6.3、§9）。
- 源码与历史提交：`git show` 对 `37a82e8`、`876181c`、`64eb0b5`，以及 `b00b630`、`de52142`、`e83255f`、`73e00ef`、`df3bb02`、`35cd7b3`。

**其它遗留事项**：

- 本轮 3b、3c、3d 未产生 testing/ 代码改动，因此没有对应的单独提交（第 3 节、D-18）。
- 阶段 2 的登记 `REG_B2_EXPECTATIONS.tsv` 与 S2R 的 `R2D_EXPECTATIONS.tsv`、S2R2 的 `REGISTRY_T3_static.tsv` 未改写，其过时的"不可达"或"no run yet"表述在报告中注明已被本轮取代。
- 对 `matrix_d003.py` 与 `judge_d003.py` 未做任何改动。

## 15. 路径清单

**报告与 digest**：

- `checkpoints/p05/P05_S2R3_HARNESS_GAPS.md`（本报告）
- `checkpoints/p05/S1_evidence_digest.txt`（追加段落，见下）

**提交**（仅 `testing/d003/` 与 `checkpoints/p05/`）：

| 提交 | 内容 | 文件 |
|---|---|---|
| `bdd2b56` | 阶段 3a：运行器加入 H 树名 | `testing/d003/matrix_r2.py` |
| `d8b4276` | 阶段 3b：运行器加入 B2 请求前缀 | `testing/d003/matrix_r2.py` |
| `9d29877` | 阶段 4：Jones 选项脚本 | `testing/d003/stage4/opt_jones.sh`、`testing/d003/stage4/reldiff.py` |

**证据目录**（被 `.git/info/exclude` 忽略，不提交）：`checkpoints/p05/evidence/p05-s2r3/`，其中：

- `PROGRESS_CHECKPOINT.txt`：全程进度与偏离。
- `build3a/`：三树导出、库、驱动、OBJECT_IDENTITIES.txt、H_COMPOSITION.txt、STAGE3C_PROBES_H.txt、`_c2_derived.json`。
- `regress-3a/`：运行器回归（PRE 与 POST，PRE_3A_SNAPSHOT.sha256）。
- `stage3/`：登记（REG_*、CORR_*、MAP_3D_*，各 `.sha256` 与 `*_TIMESTAMP_UTC.txt`）、正式运行 `formal-*`、历史矩阵 `hist38-H-run-r*`、`hist-r2d-H-r*`、`hist-s2r2-H-r*`、偏离记录 `DEVIATIONS_AND_VIOLATIONS_S2R3_CONT2.txt`。
- `stage4/`：plain 导出（`plain-A`、`plain-H`）、选项产物（`opt-*`）、`dump/`、`STAGE4_JONES_TABLE.tsv`。
- `strace/`：两次抽样的输出。

**结束状态**：未完成，等待用户审核。

## 16. 结束声明

- 本报告为 P05-S2 补充子任务 S2R3 续作二的报告。**P05-S1、P05-S2、P05-S3、P05-S4 均未宣布完成。**
- **状态：未完成，等待用户审核。**
