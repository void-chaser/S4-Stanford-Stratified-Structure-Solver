# P05-S2R6：统一入口、安全包装与复现自检（D003）

> **状态：未完成，等待用户审核。** 本报告不宣布 P05-S1、P05-S2、P05-S3、P05-S4 任一阶段完成，也不代替用户判定"S2 已完成"。签收由用户决定。
> 本轮所有结果称"装置观察"，不称"验证"。B（`37a82e8`）的结果不是修复证据。

## 0. 定位与未完成声明

- 本报告属于正式阶段 **P05-S2** 的补充子任务 S2R6，不是新阶段。P05 固定五阶段 S1–S5，本轮未引入 S6。历史报告与文件名未改写。
- 阶段定义依据：用户提示词（P05-S2 测试装置：扩展注入器覆盖 S4_malloc、LinearSolve 与两步分支，接入仓库测试目录，源码仅改 testing/ 并允许必要的测试专用 seam）。仓库内无原始计划文档，未搜索原文。
- 本轮目的：把 S2R2–S2R5 累积的装置做成一个可从零复现的统一入口，使 P05-S4 能直接调用，并消除"写入仓库外路径"类违规的根因。

## 1. 授权、边界与用户决定

**授权与边界**：不修改 `S4/` 下任何文件（相对 `64eb0b5` 保持 0 改动）。可修改 `testing/d003/` 与 `checkpoints/p05/`。seam 只应用于 `git archive` 导出副本。不修改 `judge_d003.py`（sha256 `d2d04145…`）、既有 seam 脚本、既有注入器行为、既有登记文件。

**沿用的决定**：L9、L10 为已接受的已知限制；L4、L5 的划分与 B 列恒等模型（标"不是修复证据"）；D-U1、B2 前缀、U-1、U-2。

## 2. 起点、开工与第 0 步快照

- **起点**：HEAD `f5ea8e7`；分支 `codex/p05-d003-fft-error-propagation`；`S4/` 相对 `64eb0b5` 改动 0；工作区开工时干净；`judge_d003.py` sha256 `d2d04145e0561638`。
- **第 0 步（在任何其他命令之前）**：`/tmp` 顶层快照（开始）：**0 条目，sha256 `e3b0c442…`**。抽样 strace（开始，对只读的 `ls -A`）：**27 行，`/tmp` 相关 0**。记录于 `checkpoints/p05/evidence/p05-s2r6/`（`tmp_top_start.*`、`strace_start.txt`）。
- **CPU**：AMD Ryzen 7 3800X（8 核），指令集含 `fma`、`avx2`，**不含 avx512**。编译器 g++ 15.2.0。构建选项：仓库默认 `-O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC`（`Makefile.Linux`）。与 S2R5 记录的 CPU 相同。

## 3. 提交表

| 提交 | 内容 | 范围 |
|---|---|---|
| `58065b8` | R6-1：`testing/d003/safe_run.sh`（安全包装） | 仅 `testing/d003/` |
| `e693892` | R6-2：`testing/d003/run_all.sh`（统一入口）、`testing/d003/summarize_r6.py`（judge/report）、`testing/d003/README.md` | 仅 `testing/d003/` |
| `cd93378` | R6-3 修正：报告清单只覆盖harness输出，并排除其自身 | 仅 `testing/d003/run_all.sh` |
| 本报告提交 | 报告、digest 段落、`registries/s2r6/` 复现包、MANIFEST 追加 | 仅 `checkpoints/p05/` |

本轮提交越界路径数：**0**（`git diff --name-only f5ea8e7 HEAD` 中不属于 `testing/d003/` 与 `checkpoints/p05/` 的路径）。未 amend、未 rebase、未 push、未合并、未动 master/origin。

## 4. R6-1 安全包装测试表（三正例、三反例，另加辅助项）

`testing/d003/safe_run.sh`：计算 REPO，固定 EV 为 `$REPO/checkpoints/p05/evidence/<子目录>`，创建 `$EV/tmp` 并导出 TMPDIR；输出目录经 realpath 解析，若不在仓库内则 exit 2；子命令的绝对路径参数若在仓库外则 exit 2（只读系统路径需 `--allow-system-read`，`/dev/null` 放行）；每次调用记录到 `$EV/safe_run.log`，每次拒绝记录到 `$EV/safe_run_refusals.log`。拒绝发生在任何子命令运行之前。

| 编号 | 类型 | 命令要点 | 结果 | 落盘（仓库外） |
|---|---|---|---|---|
| POS1 | 正例 | `safe_run.sh p05-s2r6/r6test-pos1 -- sh -c '… > "$EV/out.txt"'` | rc 0，文件在仓库内 | 无 |
| POS2 | 正例 | `safe_run.sh p05-s2r6/r6test-pos2/nested -- …` | rc 0 | 无 |
| POS3 | 正例 | 子命令参数为仓库内绝对路径 | rc 0 | 无 |
| NEG1 | 反例（`..` 逃逸） | `safe_run.sh p05-s2r6/../../../../r6-neg1-escape -- …` | **rc 2**，拒绝原因 `OUT_DIR contains '..'`，已记入拒绝日志，无子命令运行 | 无（解析结果在仓库内，见注） |
| NEG2 | 反例（符号链接逃逸） | `safe_run.sh p05-s2r6/r6-neg2-link/x -- …`（链接指向 `/nonexistent_dir_r6_neg2`） | **rc 2**，拒绝原因 `resolved OUT_DIR is outside the repository`，已记入 | 无（目标未创建） |
| NEG3 | 反例（绝对路径） | 子命令参数 `/nonexistent_dir/x` | **rc 2**，拒绝原因 `absolute path outside the repository`，子命令未运行 | 无（标记文件未写入） |
| NEG4 | 辅助：组件符号链接（仓库内） | 链接解析在仓库内，`OUT_DIR component is a symbolic link` | rc 2，已记入 | 无 |
| SYS1/SYS2 | 辅助：系统只读路径 | `/usr/bin/env` 无参数 rc 2；`--allow-system-read` 时 rc 0 | 符合设计 | 无 |
| SYS3/SYS4 | 辅助：`/dev/null` 放行、`--allow-system-read` 不放行非系统路径 | rc 0 / rc 2 | 符合设计 | 无 |

**注**：NEG1 的字符串 `p05-s2r6/../../../../r6-neg1-escape` 解析后仍在仓库内（`$REPO/r6-neg1-escape`），因此它的拒绝来自 `..` 规则，**不是** realpath 仓库外规则。realpath 仓库外规则由 NEG2 与 NEG3 证明。

**测试过程中的失误（如实记录）**：
1. 首轮 POS1 的目录参数写错，输出落在 `checkpoints/p05/evidence/r6-test/`（仍在仓库内，不是仓库外写入）。已在路径校验后删除该目录。
2. 首版包装对拒绝不留日志。已修复：拒绝经 `refuse()` 记入 `safe_run_refusals.log`。
3. NEG2 测试创建的符号链接，其目标是文件系统根下的占位路径 `/nonexistent_dir_r6_neg2`。链接本身位于 `$EV` 内；目标从未创建或写入（前后 `test -e` 均为不存在）。该命令的**链接目标**是根下路径，属于违规表中的一项（见第 7 节）。

## 5. R6-2 阶段与入口说明

`sh testing/d003/run_all.sh --out <仓库内目录> [--trees B,A,H] [--stage LIST]`

| 阶段 | 作用 | 验证结果 |
|---|---|---|
| export | `git archive`：B=`37a82e8`、A=`876181c`、H=`64eb0b5`；H 的 `testing/` 取 HEAD | B：899 个 blob 与提交逐字节相同（0 不同）。H：S4 70 个 blob、testing 120 个 blob，全部与来源相同。`Cgeom` 为 gitlink（模式 160000），三棵树相同，`git archive` 不展开，非缺陷。 |
| build | 普通库，仓库默认选项 | 三棵树的 `libS4.a` 与冻结的普通库 sha256 逐一相同（B `fb9ac3f5…`、A `865c5893…`、H `f053bfea…`）。 |
| seam | 族库：每族从提交的新导出构建，应用对应 seam 脚本（先 `--check-only`） | 十二个族库逐一与冻结库相同（见第 6 节表）。 |
| drivers | 每库链接一个驱动（LIBFLAGS 与 `run_d003.sh` 相同），记录 sha256 | 驱动二进制逐一不可由记录复现（见第 6.4 节）。 |
| matrix | 按（登记, 树, 族）生成族过滤副本，两遍运行 `matrix_r2.py` | 零站点运行：25 个输入，50 次运行，全部 rc 0。 |
| judge | `summarize_r6.py` 派生状态，UNDECLARED 使阶段失败 | 36 MATCHED，3 STRUCTURAL_DECLARED，0 UNDECLARED。 |
| report | 输出清单 sha256 | 8864 条，全部 OK（修正后）。 |

**幂等**：`STAGES.txt` 中同阶段同树列表的 `DONE` 行使阶段跳过；`FAILED` 行不算完成，重跑会再次执行，且两行都保留。已验证：DONE 跳过、FAILED 重跑并保留日志。

**失败**：任一阶段失败即 exit 1，原因写入 stderr 与 `STAGES.txt`。已验证：注入一个被改动的观察类别时 judge 阶段 exit 1 并给出原因。

**族与构建的对应**（来自冻结构建日志的宏集，已逐一复现）：

| 库 | 树 | 宏 | 用于的请求前缀 |
|---|---|---|---|
| plain-B/A/H | B/A/H | 无 | s4malloc（链接期 wrap） |
| AB-B / AB-A（seamAB） | B、A | ALLOC、KOTTKE、LINEARSOLVE、LINEARSOLVE_NULLINFO | alloc、linearsolve_null |
| H-B2（seamH） | H | ALLOC、KOTTKE、LINEARSOLVE、LINEARSOLVE_NULLINFO2 | linearsolve_null2、alloc、s4malloc |
| fmmbuf-B | B | FMMBUF | fmmbuf |
| fmmpert-B | B | FMMPERT | fmmpert |
| fmmret-A / fmmret-H | A、H | FMMRET | fmmret |
| addf-H | H | ADDFIELD | addf |
| b2buf-H | H | LINEARSOLVE_NULLINFO2BUF | linearsolve_null2buf |

**树的标签**：B=`BASE`，A=`CUR`，H=`H`（运行器标签；登记头部确认 BASE=B、CUR=A）。

## 6. R6-3 复现自检比对表

全部在新建的仓库内目录 `checkpoints/p05/evidence/p05-s2r6/repro-R6-3/` 中，从零运行 `run_all.sh` 全部阶段（`--trees B,A,H`），耗时 **87 秒**，退出码 0。

### 6.1 库（十二个族库与普通库）

| 库 | 零起点运行（sha256 前 16 位） | 冻结参照 | 结果 |
|---|---|---|---|
| plain-B | `fb9ac3f5fd2c1216` | S2R3 OBJECT_IDENTITIES | 相同 |
| plain-A | `865c58938e18220a` | S2R3 OBJECT_IDENTITIES | 相同 |
| plain-H | `f053bfea1ef045af` | S2R3 OBJECT_IDENTITIES | 相同 |
| seamAB-A | `0b78df5c58ecd717` | S2R3 build3a/A | 相同 |
| seamAB-B | `d4dd8f69a4709888` | S2R3 build3a/B | 相同（24/24 目标文件相同） |
| seamH | `ee0697dbf4a6216f` | S2R3 build3a/H-combo | 相同（24/24） |
| fmmbuf-B | `93064697a6ab5ec7` | S2R5 r5-1/export-B | 相同（24/24） |
| fmmpert-B | `8fe99ca3e37c8d70` | S2R5 r5-1/export-BPERT | 相同 |
| fmmret-A | `8331b083ce880712` | S2R5 r5-1/export-A | 相同 |
| fmmret-H | `9692a154a0789fc0` | S2R5 r5-1/export-H | 相同 |
| addf-H | `9cd8efab36c9262e` | S2R5 r5-2/export-H-w | 相同 |
| b2buf-H | `28d0402264340c70` | S2R4 r4-1/export-H-buf | 相同 |

### 6.2 比对项

| 比对 | 冻结参照 | 结果 |
|---|---|---|
| 三列表 REG_3B（S2R3），24 行，类别逐行 | 登记 `REG_3B_THREECOLUMN.tsv` | **24/24 逐行相同，0 差异** |
| S2R5 十点三列（150–159，H/A 的 fmmret，B 的 fmmpert） | `R5_1_THREE_COLUMN.tsv` | 30 个单元格（10 点 × 3 树），**0 差异** |
| 族 F 六行（H，两条链） | `REG_R5_2_ADDFIELD*.tsv` 与 S2R5 §4.5 | **6/6**：REPORTED_FAILURE，rc1 20，hit 1 |
| S2R4 七站点（21 行：CUR 族 B 7、H B2 7、H buf 7） | S2R4 closeout §3 观察表（非仅登记期望） | **21/21 观察类别相同** |
| 历史 38 案（H） | `hist38-H-r3/index.txt`，**分类重放**（对冻结原始运行重新分类） | **逐字节相同**（sha256 `ef7aa108…`），18 个 NO 行 |
| 历史 38 案（BASE、CUR） | `hist38-base`、`hist38-cur` 冻结索引 | BASE 38 yes；CUR 20 yes / 18 NO，18 NO 与 H 的集合相同 |
| R2-D 13 案（BASE/CUR，26 行登记） | `R2D_EXPECTATIONS.tsv`，**重新运行** | BASE 11/13，CUR 12/13（两遍一致）。不匹配集合 == 声明的 S2R 集合（见 6.3） |
| S2R2 17 案（CUR） | `MAP_R4_3_S2R2_CUR.tsv`，**重新运行**（两遍） | **17/17**，两遍一致 |
| 矩阵 BASE/CUR/H 行（pass1） | 登记期望 | 48 / 53 / 69 行，**0 不匹配**；pass2 与 pass1 逐行类别相同 |
| 驱动 sha256 | 冻结清单（独立，不含本轮自身） | **1/12 逐字节相同**（addf-H）；其余 11 个的差异原因已证明（见 6.4） |

### 6.3 R2-D 13 案的不匹配集合

| 树 | 行 | 观察 | 登记期望 | 状态 |
|---|---|---|---|---|
| BASE | `new/A-fft-info-k1` | SILENT_SWALLOW | REPORTED_FAILURE | 声明：基线无 solve_info 检查，登记错误（S2R_SUPPLEMENT 第 248 行） |
| BASE | `new/N-vl-id17-k1` | SILENT_SWALLOW | INVALID | 声明：登记错误 D-1（S2R_SUPPLEMENT 第 306 行） |
| CUR | `new/N-vl-id17-k1` | SILENT_SWALLOW | INVALID | 声明：登记错误 D-1 |

三行与 S2R 声明的集合**完全相同**（没有多出，也没有缺少）。这些是已声明的登记错误，不是新的未声明差异。

### 6.4 驱动二进制（sha256）

- 零起点运行的 12 个驱动。其中 **1 个**（`addf-H`，`0486035d…`，601664 字节）与独立冻结记录（`p05-s2r5/r5-2/bin-F/driver-d003-seam`）**逐字节相同**。
- 其余 **11 个不同**。**原因已证明**（不是猜测）：冻结驱动是用当时的注入器修订版构建的，而 HEAD 的注入器此后增加了族钩子（`fa_` 于 `49a71df`，`fp_` 于 `bb59558`）。
  - 证据：冻结 `r5-1/bin-H`（`ade86f42…`，构建于 19:54，早于 `bb59558` 20:01）与新链接的 `fmmret-H`（`c582fa0f…`）的符号差异为 **10 个**（新链接多出 `S4_TEST_ADDFIELD_AFTER`、`S4_TEST_FMMPERT_AFTER` 及 `fa_*`、`fp_*` 状态）。
  - **预测检验**：用 `bb08729` 的注入器（无 `fa_`/`fp_`）链接同一 H-fmmret 库，得到 `ade86f4294b79ff9`，**与冻结 `r5-1/bin-H` 逐字节相同**。
- **因此**：驱动二进制差异是**源修订（注入器）差异，不是构建路径差异**。固定修订即可复现。`run_all.sh` 使用当前 HEAD 的注入器，这一点已记录。
- **修正**：早先认为"结果层不受修订影响"过于宽泛。`bb08729` 注入器不分派 `fmmpert`（10 行）与 `addf`（6 行）两个族；对其余族（`linearsolve_null`、`linearsolve_null2`、`alloc`、`s4malloc`、`fmmret`、`fmmbuf`）两版本都分派，但**未经运行检验**修订差异是否改变结果。

### 6.5 偏离与校正（R6-3 过程中发现，全部已纠正）

| 编号 | 内容 | 纠正 |
|---|---|---|
| D6-1 | 清单中的 SHA256SUMS 包含其自身，`sha256sum -c` 对该行失败 | 报告阶段改为排除自身与 `trees/`；**原运行记录未改写**，修正清单在 `repro-R6-3/` 之外另存（`report-fix/rf/`，8864 条，全部 OK） |
| D6-2 | 早先的计数把 S2R4 的 CUR 行计为 0（用了运行器标签 `CUR` 查找，而输入标签为任务标签 `A`） | 以正确标签重算：21/21 行运行，0 不匹配 |
| D6-3 | 早先计数中 H 的输入数写为 13（未经计数） | 从 `INPUTS.tsv` 重算：H 11 个输入、69 行；A 7 个、53 行 |
| D6-4 | 早先断言"MAP_R4_3 丢了两行" | 核对：MAP_3D_S2R2_H 与 MAP_R4_3 的 17 个案例集合相同。两行 closed-ivalues 在 `REGISTRY_T2_v2_SUPPLEMENT` 中，且 MAP_3D_S2R2_H 头部声明其**不属于 17**。该断言撤回。 |
| D6-5 | 早先断言"结果层不受注入器修订影响" | 核对：`fmmpert` 与 `addf` 不被旧修订分派。断言收窄（见 6.4） |
| D6-6 | S2R2 的 17 案中 `t4/cache-hit-work-k7` 所在的 `REGISTRY_T4.tsv` 为 13 列，`adapt_registry_t2.py` 拒绝 | 对该行机械派生前 10 列（源 sha256 `034295df…` 与记录一致），运行并与冻结期望比对：17/17 |

## 7. 偏离与违规（单一表，沿用 S2R5 §7 并追加）

依据：`checkpoints/p05/evidence/p05-s2r6/`（证据，不提交）。本表是违规次数的唯一来源。

### 7.1 违规表（写入仓库外路径的尝试，沿用 S2R5 的三行并追加本轮）

| # | 轮次 | 完整命令（摘要） | 是否落盘 | 如何核实 |
|---|---|---|---|---|
| 1 | S2R3 首轮 | `git show … > /tmp/__never_write` | 无法确定 | 同 S2R5 §7.1；与更早某次是否为同一事件无法确定 |
| 2 | S2R4 | `find … > /tmp_no_write_check_placeholder` | 否 | 文件系统拒绝；`ls -la` 确认不存在 |
| 3 | S2R5 R5-1 | `git show … > /tmp_dummy_not_written` | 否 | `ls -d` 确认不存在 |
| 4 | **S2R6 R6-1 首轮 POS1** | 目录参数写错，输出到 `checkpoints/p05/evidence/r6-test/` | **是（仓库内）** | 不是仓库外写入；路径校验后删除该目录（`realpath` 确认目标为仓库内 `r6-test`） |
| 5 | **S2R6 R6-1 NEG2** | `ln -s /nonexistent_dir_r6_neg2 "$LINK"`（链接在 `$EV` 内，目标为根下路径） | **链接落盘（在 `$EV` 内）；目标未创建** | `test -e` 前后均不存在；链接已按已验证路径删除。**链接目标为根下占位路径，计入本表** |
| 6 | **S2R6 R6-2 验证** | `sh testing/d003/run_all.sh --out /tmp/x`（参数为 `/tmp` 字面量） | 否（在任何写入前拒绝） | 退出码 2；`--out` 必须为相对子目录，未创建任何文件 |

**本轮自查**：回顾本轮所有命令记录（`safe_run.log`、`safe_run_refusals.log`、本轮进度检查点），上表第 4–6 行是本轮的仅有事件。其中第 5 行的目标是根下占位路径（不是写入，但符合"占位路径"模式，按违规披露）。第 4 行是仓库内写入，不是仓库外违规，但按规则披露。**这是自查，不是系统审计**：交互 shell 的命令不在 strace 覆盖范围内。

### 7.2 其它偏离

| 编号 | 偏离 | 纠正 |
|---|---|---|
| D-R6-1 | 任务书要求驱动 sha256 与报告一致，**1/12 一致** | 差异原因为源修订，已证明（6.4）；不伪造一致 |
| D-R6-2 | 任务书"A/B"树名与运行器"CUR/BASE"标签不同 | 映射已记录（第 5 节）；登记头部确认 |
| D-R6-3 | 历史 38 案的**运行**无法用固定驱动复现（运行记录无驱动路径） | 复现限于分类重放（逐字节相同）。不宣称运行复现 |
| D-R6-4 | S2R2 的 `REGISTRY_T4.tsv` 为 13 列，无记录的转换工具 | 对单行机械派生并记录来源（第 6.5 节 D6-6）；未纳入 `run_all.sh` |
| D-R6-5 | `run_all.sh` 的 `matrix` 阶段不含 S2R2 登记与 R2-D 登记 | S2R2 17 与 R2-D 13 为独立步骤（不在入口内），见第 8 节 |

## 8. 仍未闭合缺口与输入

### 8.1 未闭合（须用户裁决或后续处理）

1. **驱动二进制不可由记录逐字节复现**（11/12）。原因已证明为源修订。若要求驱动哈希逐字节一致，需要为每个历史结果固定其注入器修订（或在入口中加入修订选择）。这是设计决定，本轮未做。
2. **历史 38 案的运行不可复现**（运行记录无驱动路径）。当前为分类重放。
3. **`run_all.sh` 不覆盖 S2R2 17 案与 R2-D 13 案**。两者的登记不是 10 字段运行器格式（S2R2）或位于 evidence（R2-D 的运行器格式登记已在 `registries/` 之外）。本轮以独立步骤完成比对，入口未纳入，以免入口依赖 evidence 目录。
4. **注入器修订与族覆盖**：`fmmpert` 与 `addf` 不被旧修订分派。若需用旧修订复现这两族，需用户决定。
5. **13 列的 `REGISTRY_T4.tsv`** 无记录的转换器。当前为单行机械派生。

### 8.2 已知限制（沿用，见 `testing/d003/README.md` 第 6 节）

L1–L10 状态沿用 S2R5；L9、L10 为用户已接受的限制。

### 8.3 对 S3 补充收尾的输入

- 族 E（`fmmret`）与族 F（`addf`）的 H 树状态与调用方检查，装置观察已可由 `run_all.sh` 从零复现（十二个库逐一相同）。
- `fmm_kottke:78`（S3 声称已处理、装置显示未修好的点）：本轮 S2R6 **未修**，仍为最高优先级红点。本轮 REG_3B 的 H 行与 S2R3 逐行相同，未改变其状态。
- B 列（恒等模型）不是修复证据，不得用于 S3 的修复论证。

### 8.4 对 P05-S4 验证的输入

- 统一入口可直接调用：`run_all.sh --out p05-s2r6/<目录>`，输出位于仓库内并带判定摘要。
- 判定依据是 `summarize_r6.py` 的派生状态（MATCHED / STRUCTURAL_DECLARED / UNDECLARED）。P05-S4 的"正负对照"与"失败后模式不安装"需另行设计，本轮未做。
- 驱动须以**当前注入器**构建，或显式固定修订（见 8.1 第 1 项）。

## 9. S2 收敛核对表（最终版，沿用 S2R5 §6 并新增一行）

**判定原则**（沿用）：**已闭合** = 有实测证据且可复核；**已接受为已知限制** = 有明确的用户决定；**未闭合** = 证据不足或存在未解决问题。本表**不代替用户判定"S2 已完成"**。

### 9.1 S2 的定义组成

| # | 组成 | 状态 | 证据与说明 |
|---|---|---|---|
| G1 | 覆盖 S4_malloc | 已闭合（范围内）；范围外已接受为范围决策 | 沿用 S2R5 §6.1 |
| G2 | 覆盖 LinearSolve | 已闭合（范围内）；范围外已接受为范围决策 | 沿用 S2R5 §6.1 |
| G3 | 覆盖两步分支 | 已闭合（按 S2 原报告 §4.3） | 沿用 |
| G4 | 接入仓库测试目录 | 已闭合 | `testing/d003/`，本轮新增 `safe_run.sh`、`run_all.sh`、`summarize_r6.py`、`README.md` |
| G5 | 源码仅改 testing/（允许必要的测试专用 seam） | 已闭合 | `S4/` 相对 `64eb0b5` 为 0 改动 |
| **G6** | **统一入口与可复现性（S2R6 新增）** | **已闭合（范围内，见 9.2 的保留）** | `run_all.sh` 从零运行全部阶段（87 秒，rc 0）；十二个库逐一与冻结相同；三列表、S2R4 七站点、S2R2 17、R2-D 13（不匹配集合 == 声明集合）、族 F 六行均有比对。**保留**：驱动二进制 1/12 逐字节相同（其余原因已证明为源修订）；历史 38 案的运行不可复现（仅分类重放）。 |

### 9.2 已知遗留项（沿用 S2R5 §6.2，本轮无状态变化）

L1–L15 沿用 S2R5 的状态（见 `checkpoints/p05/P05_S2R5_CLOSEOUT.md` §6.2）。本轮未改变任何已闭合项，也未改变任何已接受的限制。

### 9.3 汇总

- **已闭合**：G1–G6（范围内）、L4、L5、L12、L13、L14、L15。
- **已接受为已知限制**：L1、L2、L3、L6、L7、L8、L9、L10；范围决策：L11。
- **未闭合**：见 8.1 的五项（驱动复现、历史 38 案运行、入口未含 S2R2/R2-D、注入器修订、13 列 T4 转换器）。

**本核对表不代替用户判定"S2 已完成"。** 需用户决定：(a) 驱动是否须逐字节复现（若须，需固定修订）；(b) 历史 38 案的分类重放是否足以作为复现依据；(c) S2R2/R2-D 是否纳入入口。

## 10. 收尾核对

| 项 | 开始（第 0 步） | 结束 |
|---|---|---|
| `/tmp` 顶层（条目数，sha256 前 16 位） | 0，`e3b0c442…` | 0，`e3b0c442…`（相同） |
| strace 抽样（`ls -A`，事件行数；`/tmp` 引用） | 27；0 | 27；0（相同） |
| `S4/` 相对 `64eb0b5` 改动 | 0 | 0 |
| 本轮越界提交路径（相对 `f5ea8e7`） | — | 0 |
| 工作区 | 干净 | 见 10.2 |

### 10.1 说明

两对快照均为**抽样**，不是穷尽审计。strace 只跟踪被跟踪的进程，不覆盖交互 shell 命令（第 7.1 节）。结束快照文件：`checkpoints/p05/evidence/p05-s2r6/tmp_top_end.*`、`strace_end.txt`。

### 10.2 工作区

本报告提交前后的 `git status` 见第 12 节的收尾输出。

## 11. 路径清单

**报告与记录**：
- 报告：`checkpoints/p05/P05_S2R6_CLOSEOUT.md`（本文件）
- digest 段落：`checkpoints/p05/S1_evidence_digest.txt`（末尾追加）
- 复现包：`checkpoints/p05/registries/s2r6/`（`frozen/` 11 个副本，`derived/` 4 个派生输入）
- MANIFEST：`checkpoints/p05/registries/MANIFEST.tsv`（追加 16 行；原 74 行字节不变）
- 进度检查点：`checkpoints/p05/evidence/p05-s2r6/PROGRESS_CHECKPOINT.txt`（证据，不提交）

**testing/d003（提交）**：
- `testing/d003/safe_run.sh`（58065b8）
- `testing/d003/run_all.sh`（e693892，cd93378 修正）
- `testing/d003/summarize_r6.py`（e693892）
- `testing/d003/README.md`（e693892）

**证据（不提交）**：
- 零起点运行：`checkpoints/p05/evidence/p05-s2r6/repro-R6-3/`（229 MB，11721 个文件；STAGES.txt、BUILD_OPTIONS.txt、drivers/DRIVERS.tsv、matrix/、report/）
- 修正清单的验证副本：`checkpoints/p05/evidence/p05-s2r6/report-fix/rf/`
- 其它检查：`t-chainB/`、`t-chainAH/`（分阶段运行）、`s2r2-t4/`（S2R2 17 案）、`r2d-R6-3/`（R2-D 13 案）、`judge-neg/`（负对照）
- 调用日志：每个 `safe_run.sh` 输出目录内各有一份 `safe_run.log`（共 46 份；零起点运行为 `repro-R6-3/safe_run.log`）。拒绝日志：`checkpoints/p05/evidence/p05-s2r6/safe_run_refusals.log`（7 条，逐条核对：`..` 逃逸 2 条、绝对路径 2 条、仓库外符号链接 1 条、仓库内组件符号链接 1 条、`/usr/bin/env` 无标志 1 条）。

**状态**：未完成，等待用户审核。P05-S1、P05-S2、P05-S3、P05-S4 均未被宣布完成。
