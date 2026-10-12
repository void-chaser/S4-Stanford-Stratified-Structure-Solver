# P05-S3 R3 收尾报告（S3 的子轮次 S3R3，非新阶段）

**状态：本轮已完成 S3R3 范围（门禁、修改前源码确认、RNV1 修复方案 R3、注释 U31、编译检查、自检 A–D、冻结 F2、收尾文件）。本轮未宣布任何阶段完成或签收。P05-S3、P05-S4 未签收。S3-4b 由用户关闭（U29），只关闭此项。自检不是 S4 验证；修复后的验证是 P05-S4 R7 在 F2 上的回归。本轮已完成/未完成 S3R3 范围，等待用户审核。**

规则依据：`AGENTS.md`（含 U33 批准的 F2 两处改动）；任务书 `checkpoints/p05/briefs/P05_S3R3_BRIEF.md`；裁决 `checkpoints/p05/registries/RULINGS.tsv`（U29–U33）；勘误 `checkpoints/p05/ERRATA_S3R3.txt`（用户裁决与 E-S3R3-A、ES3R3-1、ES3R3-2）。

---

## 0. 门禁（S3R3-0）

| 项 | 结果 |
|---|---|
| HEAD（开工） | `cadf25809c80fec1887d07485dc641bbd1693610`，与任务书一致 |
| `HEAD:S4` | `4a6f64927a30537740dd0c8f11f9a5aae5e46ba4`（F），一致 |
| judge_d003.py sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`，一致 |
| registries/s4r6d SHA256SUMS | 19 项全部 OK |
| 工作区 | 仅任务书与 gate 脚本未跟踪，一致 |
| `/tmp` 顶层（开工） | 0 条目，listing sha256 `e3b0c442…b855` |
| 门禁脚本与输出 | `testing/d003/stage_s3r3/s3r3_gate.py`；`checkpoints/p05/evidence/p05-s3r3/GATE_S3R3.txt`；结果 PASS |

注：任务书写作 `registries/s4r6d/`，实际位于 `checkpoints/p05/registries/s4r6d/`（ES3R3-2）。

## 1. 修改前源码确认

见 `checkpoints/p05/evidence/p05-s3r3/PRE_FIX_SOURCE_S3R3.md`（副本 `registries/s3r3/PRE_FIX_SOURCE_S3R3.md`）。要点：

- `cg` 定义 1245、分配 1251；`sparse_linsolve_d` 定义 1327，调用 1404（非 CHOLMOD 分支）、1621（rect）、2056（tri）；`_rect` 1464（分配 1477、1481）；`_tri` 1643（分配 1656、1660）；`pattern_generate_flow_field` 2089。
- **HAVE_LIBCHOLMOD**：构建脚本（`Makefile.Linux`、`Makefile.common`）不定义；R4 普通构建与 R5 dbg 构建的实际命令中均无 `-DHAVE_LIBCHOLMOD`，`build-dbg-F.log` 中 `cholmod` 出现 0 次。结论：不定义，走 `cg` 分支。
- **−11**：`grep -rn -- "-11"` 与 `grep "\-11"` 在 S4/ 中**无匹配**（工具输出：No matches found）；`-9`（pattern.c:1066）与 `-10`（pattern.c:2149）为现有用法。−11 未被占用。
- 三个调用者对非零返回的处理：NV `fmm_PolBasisNV.cpp` 144–149；Jones `fmm_PolBasisJones.cpp` 187–192；VL `fmm_PolBasisVL.cpp` 146–151。任务书给出的行号（NV:144、Jones:187、VL:146）与实测一致（分别为 `if(0 != error)` 行）。
- `pattern.h`：`pattern_generate_flow_field` 声明在 314–322，注释块无返回值说明；本轮**未改 pattern.h**（不在 U32 范围）。

## 2. 修复（S3R3-1）

方案 R3（U30）。改动只在 `S4/pattern/pattern.c` 与 `S4/S4_internal.h` 第 263 行。

| 项 | 内容 |
|---|---|
| `cg`（1245） | 返回 `int`；`malloc` 失败返回 −11；成功路径返回 0；迭代与释放不变 |
| `sparse_linsolve_d`（1327） | 返回 `int`；非 CHOLMOD 分支返回 `cg` 的状态；CHOLMOD 分支（本构建未编译）末尾返回 0，注释说明其 cholmod_* 返回值本就未检查 |
| `_rect`（1464）、`_tri`（1643） | `work`、`iwork` 分配后立即检查；失败时释放已分配者，返回 −1.0；`sparse_linsolve_d` 返回非零时释放 `work`、`iwork` 并返回 −1.0 |
| `pattern_generate_flow_field`（2089） | 在 D016 检查之前加 `if(max_field < 0){ return -11; }`，注释说明 −11 = 内部分配失败；−10、−9 现有含义不变 |
| 正常路径 | 数值与运算顺序未改；`git diff` 显示未改变已有计算行（只有分配、返回值与 static 声明形式变化） |

### 2.1 提交拆分与 diff 摘要

| 提交 | 文件 | diff 行数 | 说明 |
|---|---|---|---|
| `a9679bc` | `S4/pattern/pattern.c` | 59 insertions, 20 deletions | RNV1 修复（方案 R3） |
| `a07b5ac` | `S4/S4_internal.h` | 1 insertion, 1 deletion | 注释 U31（第 263 行） |

两个提交都以 `awaiting user review` 结尾。`git diff --name-only cadf258 a07b5ac -- S4/` 只列出上述两个文件（F→F2 范围确认）。

### 2.2 编译检查（S3R3-1 第 3 条）

构建脚本 `testing/d003/stage_s3r3/build_s3r3.sh`，输出在 `checkpoints/p05/evidence/p05-s3r3/build/`。两棵树：F（`git archive HEAD`）与 F2（F 加两个工作区文件，经 `cp` 导出，之后与提交一致）。每棵树两种构建：dbg（`-O0 -g`，与 R5 相同的覆盖方式）、plain（`-O3 -march=native`，与 R4 相同）。

| 构建 | 告警数 | make rc |
|---|---|---|
| F dbg | 62 | 0 |
| F2 dbg | 62 | 0 |
| F plain | 71 | 0 |
| F2 plain | 71 | 0 |

逐条比较（去掉行号）：dbg 62 对 62，plain 71 对 71，diff 为空，**无新增告警**。pattern.c 唯一的告警（`found_multiple_xsects` 未使用，原 1575 行）为原有。

注：F-dbg 库 sha256 为 `d355468f…`，与 R5 记录的 `b95712a4…` 不同。字节哈希依赖构建路径与 objdir；源码相同（`HEAD:S4` = F）。本轮自检使用本次重建的库（F-dbg、F2-dbg），R6d 的 RNV1 运行使用 R5 库；两者不直接比较字节，只比较 rc 与类别。

## 3. 自检（S3R3-2）

预注册：`checkpoints/p05/evidence/p05-s3r3/REGISTRY_S3R3_SELFCHECK.tsv`（sha256 `38948f0e…df088bf`，UTC `2026-10-12T10:31:36Z`；状态 INFLUENCED）。运行前写入，运行后未改期望。运行器 `testing/d003/stage_s3r3/run_s3r3_selfcheck.py`（新文件，导入 judge_d003.classify，未改判定器）。

### A. RNV1 注入，F2（36 点 × 两遍）

| 结果 | pass1 | pass2 |
|---|---|---|
| REPORTED_FAILURE（rc 0 的 driver rc，rc1 = 20） | 36/36 MATCH | 36/36 MATCH |
| MISMATCH | 0 | 0 |

注意：驱动的进程退出码为 0（driver 自身 PASS/FAIL 不用于判定）；判定依据是 rc1 = 20（`RC first 20`）与 hit = 1，与 judge_d003.classify 的规则一致。

vl NG1、fftvl NG1：注入后 rc1 = 20，rc2 = 20（与其 D016 基线 rc 20 相同的 driver rc，但注入点本身判为 REPORTED_FAILURE，判定器依据 rc1 与 hit；F 树对同点为 CRASH，见 R6d）。这两个点的 rc 20 与 D016 路径的关系**未单独拆分**，在报告中如实说明。

**返回码链（A2，gdb）**：`checkpoints/p05/evidence/p05-s3r3/gdb_chain_F2_nv_ng9_m1.log`、`..._m3.log`、`gdb_chain_finish_F2_nv_ng9_m3.log`。
- M=1（rect `work`，7168 B，pattern.c:1477）：`S4FMM HIT ... window 1 malloc 1, 7168 B`；`R6D_WIN_CLOSE k=1 malloc_in_window=1 rc=-11`；`RC first 20`。
- M=3（cg `work`，4096 B，pattern.c:1251）：`S4FMM HIT ... malloc 3, 4096 B`；`R6D_WIN_CLOSE k=1 ... rc=-11`；`RC first 20`。
- `finish` 运行（M=3）：`FMMGetEpsilon_PolBasisNV`、`pattern_generate_flow_field` 返回点的 `Value returned` 中，`pattern_generate_flow_field` 为 **−11**。`FMMGetEpsilon_PolBasisNV` 的返回值未在 finish 输出中单独读到（finish 日志不完整），但它是 `error = Pattern_GenerateFlowField(...)` 后 `return error`（fmm_PolBasisNV.cpp:149），源码可见。
- `Simulation_ComputeLayerModes` 的返回值由 `RC first 20` 实测（驱动 rc1 = 20）。

链 −11 → PolBasis → ComputeLayerModes 20 在 M=1、M=3 上实测（rc 与窗口关闭返回值）；中间 PolBasisNV 返回值只在源码中确认，未在 gdb 中逐层读到（披露）。

**注意**：A2 的第一次与第二次 gdb 运行失败（脚本参数传递错误与 `finish` 中断），已保留日志；有效结果为 `gdb_chain_F2_nv_ng9_m1.log`（continue 版本）、`gdb_chain_F2_nv_ng9_m3.log`、`gdb_chain_finish_F2_nv_ng9_m3.log`。失败的 `gdb_chain_F2_nv_ng9_m{1,3}.log` 已被后续运行覆盖，未另存（披露：这是覆盖，违反 U17 精神，见第 7 节表二）。

### B. 无注入输出一致（F vs F2）

脚本 `testing/d003/stage_s3r3/run_s3r3_noinject.sh`；结果 `noinject/RESULTS_NOINJECT_S3R3.tsv`（副本 `registries/s3r3/`）。nv、vl、fftnv、fftvl × NG 1、5、9，dump 的 call1/call2/call3 逐字节比较：

| 项 | 结果 |
|---|---|
| 字节比较（4 模式 × 3 NG × 3 文件） | **36/36 IDENTICAL**，0 NOT_IDENTICAL |
| rc（每 run，由 stdout 解析） | nv/fftnv/vl(NG5,9)/fftvl(NG5,9) 为 0；vl NG1、fftvl NG1 为 20（F 与 F2 相同） |

已披露的脚本缺陷：`RESULTS_NOINJECT_S3R3.tsv` 中的 `RUN` 行列数与表头不一致（写入时字段多了一列，且有重复的 `RUN 0` 行，源于脚本里残留的 `$RES.runs` 写入）。这些行不影响 `call*` 比较（比较直接用 `cmp`），rc 已由 `stdout.txt` 重新解析（见上表）。该 TSV 未修复、未覆盖（U17），在此如实披露。

### C. tri 分支（驱动 `testing/d003/stage_s3r3/driver_s3r3_tri.cpp`，晶格 `{1,0,0.5,0.866}`）

**C1（F，无注入，gdb）**：`checkpoints/p05/evidence/p05-s3r3/gdb_branch_tri_F_nv_ng1.log`、`gdb_tri_F_malloc_lines.log`：
- 进入 `pattern_generate_flow_field_tri`（`S3R3BRANCH tri`），**不进入 rect**。
- 窗口内 3 次 malloc：`pattern.c:1656`（`work`，19968 B，NG1）、`pattern.c:1660`（`iwork`，7680 B）、`pattern.c:1251`（cg 的 `work`，6144 B，n=192，由 `sparse_linsolve_d` 从 tri 2056 调用）。
- 无注入 rc 0（NG1 与 NG9 均为 0）。`pattern_get_containment_tree` 的 malloc（806）在窗口之外。

**C2（注入，两遍）**：

| 点 | 树 | 期望 | pass1 | pass2 |
|---|---|---|---|---|
| TRI-F-m1、m2、m3 | F | CRASH | 3/3 CRASH（rc 139，SIGSEGV） | 3/3 CRASH |
| TRI-F2-m1、m2、m3 | F2 | REPORTED_FAILURE | 3/3 REPORTED_FAILURE（rc1 = 20） | 3/3 REPORTED_FAILURE |

**C3（无注入，F vs F2，tri 驱动）**：nv NG9、vl NG9 的 call1/call2/call3 共 6 项，**全部 IDENTICAL**（`tri_noinject/`）。

（C 结论：F 上 tri 分支的三处分配均为无 NULL 检查的裸写；F2 上三处注入均被报告为非零返回。这是自检结果，不是修复后的 S4 验证。）

### D. 冒烟检查

RS-177 的 nv/vl 点（R6c 的 `M-*` 点）的 rc 来自 R6c 的 state 结果表，该表记录的是 point_verdict 与 hit，不是 driver rc；直接复用注入路径不成立（它们用 R4 的 `s4malloc` 注入器，而不是 RNV1 窗口）。因此 D 改为：nv NG9、vl NG9 在 F2 上**无注入**运行，rc 0 与 R6d 基线（nv NG9 rc 0；vl NG9 rc 0）一致。`smoke_F2_nv_ng9.out`、`smoke_F2_vl_ng9.out`。

这是冒烟检查，不是 R6c 矩阵的回归；全矩阵回归属于 R7。

## 4. F2 的哈希

| 项 | 值 |
|---|---|
| F2 提交 | `a07b5accd331376dfd2a02e903c4fefc6425122f`（最后一个修改 S4/ 的提交） |
| `git rev-parse a07b5ac:S4` | `e124925f5b242486a913b813fa181664f665b048` |
| F → F2 `git diff --stat -- S4/` | `S4/pattern/pattern.c`、`S4/S4_internal.h`（仅两个文件） |
| F `HEAD:S4` | `4a6f64927a30537740dd0c8f11f9a5aae5e46ba4` |

AGENTS.md（U33）：第 6 节表格追加 F2 行；开工门禁中的树哈希由 F 改为 F2。仅改这两处（经用户批准）。

## 5. 红点状态

见 `checkpoints/p05/evidence/p05-s3r3/RED_POINTS_STATUS_S3R3.tsv`（副本 `registries/s3r3/`）。

- **RP-R6d-1（RNV1）**：自检通过（F2：36/36 + tri 3/3 REPORTED_FAILURE，两遍）。**未经 S4 验证；未称"已修好""已验证"。** R7 在 F2 上回归。
- RP-R6d-9、RP-R6d-10（注释 U31）：注释已改，行为未改（comment only）。
- 其余红点：按 R6d 账本保持原类别；RP-R6d-13、14、15、16、17 仍 DEFERRED/未运行（R8/R7）。

## 6. S3-4b 关闭（U29）

用户已关闭 S3-4b（带范围声明）。声明全文原样见 `checkpoints/p05/P05_S3_4b_CLOSURE.md`。关闭只针对 S3-4b 一项，不代表 P05-S3 或 P05-S4 签收。

## 7. R7 回归矩阵清单（F2）

R7 在 F2 上回归的来源：

| 项 | 来源文件 |
|---|---|
| R3 | `checkpoints/p05/P05_S4R3_REPORT.md`、`registries/s4r3/` |
| R4 | `checkpoints/p05/P05_S4R4_REPORT.md`、`registries/s4r4/`（plain 构建与 seam） |
| R5 M=2（36 点） | `checkpoints/p05/P05_S4R5_REPORT.md`、`registries/s4r5/` |
| R6-1（twice NTH 12–16，TWICE=slab） | `checkpoints/p05/P05_S4R6_REPORT.md`、`registries/s4r6/` |
| R6c 177 点（state） | `checkpoints/p05/registries/s4r6c/RESULTS_R6c_STATE.tsv`；`P05_S4R6c_REPORT.md` |
| R6c seam 25 点 | `checkpoints/p05/registries/s4r6c/RESULTS_R6c_SEAM.tsv`；`P05_S4R6c_REPORT_ADDENDUM_seam.md` |
| R6d RNV1 72 点（F 36 点 × 两遍，以 F2 重跑） | `checkpoints/p05/registries/s4r6d/REGISTRY_S4_PRE_R6d_RNV1.tsv`；本轮 section A 为 F2 版本的预注册 |
| S3R3 tri 点（C2，F 与 F2 各 3 点） | `checkpoints/p05/registries/s3r3/REGISTRY_S3R3_SELFCHECK.tsv`（section C2） |

注：R7 是 P05-S4 的子轮次，待用户批准后开工。R7 不在本轮执行。

## 8. 需要用户裁决的事项

1. **P05-S3 是否签收**（本轮未签收；S3-4b 已关闭，但 S3 的其他项与签收由用户决定）。
2. **R7 开工**（在 F2 上回归；是否开工由用户决定）。
3. 自检 A 中 vl NG1、fftvl NG1 的 rc 20 与 D016 路径的关系未单独拆分（见第 3 节 A），是否需要 R7 补做。
4. B 侧 vl NG1 rc 20 与 D016 的 B 侧来源仍未解释（RP-R6d-7，R7 处理）。
5. 任务书 3.1 要求写入的 `PRE_FIX_SOURCE_S3R3.md` 已完成；`pattern.h` 未修改（如要同步其返回值注释，需用户批准）。

## 9. 违规披露（AGENTS.md 第 3 节）

### 表一：越界写入尝试（命令自身写了仓库外路径）

无。本轮所有写入目标均在 `$REPO` 下（`checkpoints/p05/`、`testing/d003/`、`S4/`、`AGENTS.md`）。`/tmp` 开始与结束快照均为 0 条目，本轮未产生 `/tmp/dsh-spill-*`。

### 表二：工具/脚本事件

| 轮次 | 命令/工具 | 事件 | 是否落盘 |
|---|---|---|---|
| S3R3 | `printf ... > $EV/tmp/s3r3_tri_malloc_lines.gdb` | 裸跑写入（未经 safe_run.sh）；目标在 `$EV/tmp/`，路径合规 | 是（合规路径） |
| S3R3 | `grep ... | sed ... > $EV/tmp/w_*.txt`（告警比较的临时文件） | 裸跑写入（未经 safe_run.sh）；目标在 `$EV/tmp/`，路径合规 | 是（合规路径） |
| S3R3 | `printf "..." > checkpoints/p05/...` 与 `sha256sum > SHA256SUMS.txt`（部分由 safe_run 包装，部分裸跑） | 有一次证据 SHA256SUMS 把自身也收录，导致 "FAILED"；已用排除自身的列表重写，`sha256sum -c` 全部 OK | 是（合规路径，已修正） |
| S3R3 | `run_s3r3_noinject.sh` 的 `RUN` 行 printf | 脚本字段数与表头不一致，并残留 `$RES.runs` 写入，导致 TSV 中 `RUN` 行格式错误、重复 `RUN 0` 行 | 是（合规路径，未修复，见第 3 节 B） |
| S3R3 | gdb 第一、二次 `s3r3_chain_gdb.gdb` 运行 | 参数传递错误（`S4FMM_INJECT` 为空或双重前缀）与 `finish` 中断运行，产生无效日志；随后被有效运行覆盖（覆盖 `gdb_chain_F2_nv_ng9_m{1,3}.log`） | 是（合规路径；覆盖违反 U17 精神，披露） |
| S3R3 | `edit`/`write` 工具：AGENTS.md、RULINGS.tsv、STATE.md、源码 | 工具写入；目标在仓库内；`edit` 报 "file has not been read"（三次），读取后重试成功 | 不适用 |
| S3R3 | `sed -n` / `grep` / `ls` 读取命令 | 只读，未经 safe_run（不属于含写入命令） | 不适用 |
| S3R3 | 构建脚本 `build_s3r3.sh` 与运行器 | 经 `safe_run.sh p05-s3r3` 运行 | 是（合规） |

说明：表二中"裸跑写入"均在仓库内、路径合规，但未经 `safe_run.sh`，违反 AGENTS 第 3 节。这是执行者的过失，如实列出，不改写为合规。

---

## 10. 结尾

本轮已完成 S3R3 范围：门禁、修改前源码确认、方案 R3 修复（`a9679bc`）、注释 U31（`a07b5ac`）、编译检查（告警无新增）、自检 A–D（A、C 全部按预注册 MATCH，B 36/36 IDENTICAL，D 冒烟 rc 0），冻结 F2（`e124925f…`），收尾文件。本轮未完成的事项：A 中 vl/fftvl NG1 的 rc 20 与 D016 的拆分、RS-177 全矩阵回归、seam 25 点回归、R3–R6c 回归（均属 R7）。

本轮已完成/未完成 S3R3 范围，等待用户审核。P05-S3、P05-S4 未签收。

提交信息末尾写 `awaiting user review`。

---

## 11. 提交后核对

`git log -3`：

```
a07b5ac P05-S3R3 comment (U31): S4/S4_internal.h:263 wording for error code 20 (comment only). awaiting user review
a9679bc P05-S3R3 RNV1 repair (U30, scheme R3): pattern.c cg/sparse_linsolve_d return status, _rect/_tri check work/iwork allocation, flow field returns -11 on internal allocation failure. Normal path unchanged. awaiting user review
cadf258 P05-S4 R6d report section 11 (post-commit check) and registry sync; no change to stage status. awaiting user review
```

收尾提交：`0647e58`（本报告与其余 S3R3 文件）。提交后 `git status --short` 为空（工作区干净）。
