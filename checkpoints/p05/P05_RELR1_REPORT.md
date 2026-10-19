# P05 交付轮 REL-R1 报告（修复后完整原有功能非破坏性验证）

> 轮次标识：**P05 交付轮 REL-R1**（rel-r1）。P05 的 S1–S5 五个正式阶段已由用户签收（U391，`checkpoints/p05/P05_S5_SIGNOFF.md`）。
> 本轮是交付前的验证轮，**不是 P05 的新阶段**，编号不是 P05-S6；**本轮不修任何东西**，`S4/` 与 S1–S5 的历史文件一律未改。
> 本报告正文在提交 (i) 冻结；正式 end 门禁结果只追加在结尾的附录 C（提交 (ii)）。

## 1 范围

目的：上传前证明 P05 的修缮没有破坏原有功能。判据是**与未修复基线 B 对照的非破坏性**，不是重新认证物理正确性。

- 基线 **B** = `origin/master` `5b72793`（其 `S4/` 与 `37a82e8` 相同，已含 P04）；
- 候选 **F4** = 本轮开工 HEAD `3de6d8b`（`S4/` 树 `589e15eb11fcb04e031b524f25a443e7921946cf`，P05-S3R5 冻结树）；
- 参考 **U** = `7fd00a2`（上游原始 master），只作记录；U 与 B 的差异归 P04，不计入本轮失败。

预注册：`PREREG_RELR1.tsv`（221 个单元，sha256 见下），状态 **INFLUENCED**（期望受源码阅读影响：D003 修复只动失败路径，因此正常输出期望逐字节一致；同时参照 S5R3 的 unit_count=265）。预注册在第一次正式运行之前写定并记录 sha256；运行后没有任何期望被改写，唯一的执行偏离记录在 `ERRATA_RELR1.txt`（见附录 B）。

判定规则（`relr1_verdict.py`，按列名读表，只读 rc、信号、文件 sha256 与 numdiff 结果）：B 通过则 F4 必须通过；B 与 F4 都成功时输出须逐字节一致，否则用仓库自带 `testing/numdiff` 以 1e-12 容差作第二判据（DIFF_WITHIN_TOL），再否则 DIFF；B 失败 F4 失败记 BOTH_FAIL 并注明；同一树两遍结果不同记 FLAKY。

## 2 三棵树

| 树 | 提交 | `S4/` 树哈希（git `rev-parse`） | 导出后重算的 git tree 哈希 | 构建 | 产物 sha256（节选） |
|---|---|---|---|---|---|
| U（记录） | `7fd00a231610bff51f5c7de5f723e3956eab7453` | `06553f72e93aaef1a5c9294f358a7f5afbd42bb1` | 相同 | **U_BUILD_UNAVAILABLE** | —（`trees/U` 内旧 `S4/main_lua.c` 与其自身 `S4_internal.h` 不一致：`Simulation_GetAmplitudes` 传 `S4_LayerID` 而非 `S4_Layer*`；`make S4_pyext` 还调用不存在的 `python`；按任务书 §3.2 记录后继续，不阻塞） |
| B | `5b72793051eb705f0e9b2e5398e1a5f0484da0cb` | `1d738e64f9864a475fdb3de34cd3601605df2c64` | 相同 | OK | `build/S4` `9b05692e7b340d3009e7411f1a5c220245ba85bdd0f7a2af77c3b1798a62e983`；`build/libS4.a` `fb9ac3f5fd2c121619bb6cd464816f97a3085c8e4a2795a2b5037b370110ffba` |
| F4 | `3de6d8bc7a35f036bf5ff6e508f5cdb5ef025505` | `589e15eb11fcb04e031b524f25a443e7921946cf` | 相同 | OK | `build/S4` `fb375c726101ae2d935e929fece54b1867aa0435b24e9fe92bdeda77314396f2`；`build/libS4.a` `a28eaa5d6a0ed347870c9bf9f4c38d16cac23f340cfe17cf1725854f8c6d8b8d` |

三棵树都用 `git archive` 导出到 `checkpoints/p05/evidence/p05-rel-r1/trees/{U,B,F4}/`（全仓树，不注入任何补丁），并用 git tree-object 算法从导出文件重算 `S4/` 哈希，结果与 `git rev-parse <commit>:S4` 完全一致（`TREES_RELR1.tsv`）。B 与 F4 用同一编译器、同一 `Makefile.Linux` 标志构建；两树构建日志的警告各 38 条，**B 与 F4 之间新增警告 0 条、减少 0 条、编译错误 0 行**（`WARN_DIFF_RELR1.txt`）。

## 3 环境

| 项 | 值 |
|---|---|
| Python | Python 3.14.4 |
| Lua | Lua 5.2.4（Lua frontend 用系统 lua5.2 头/库） |
| 编译器 | gcc / g++ (Ubuntu 15.2.0-16ubuntu1) 15.2.0 |
| LAPACK/BLAS | liblapack-dev / liblapack3 / libblas-dev / libblas3 3.12.1-7ubuntu1（系统包） |
| CPU / 内核 | nproc=16；Linux 7.0.0-38-generic |
| 其它 | GNU Make 4.4.1；git 2.53.0；**没有 MPI**（无 mpicc / S4mpi 构建） |

## 4 运行矩阵

预注册了 T1–T8（`PREREG_RELR1.tsv`，sha256 `b0a064fe4cf6c7df34fc19719b6222a3773cf2daed53b3bd124c55e5c41297b8`）。每个 example 使用各自独立的 cwd（`$EV/run/<tree>/<pass>/<example_id>/`），B 与 F4 使用同一超时（3600 s/example）与同一并发度（4）；B 与 F4 各跑两遍。

| 套件 | 内容 | 结果 |
|---|---|---|
| T1 `make test` | B、F4 各跑 2 遍（`test-python` + `test-fast` + `test-lua`） | 4 个日志全部 rc=0；**verdict=NO_NEW_FAILURE**；每个 unittest 单元按单元名逐行对比四遍，FLAKY=0、suite_diff=0、B/F4 失败集均为空；逐日志与 `Ran N`/skipped 对账全部 OK；**unit_count=265**，与 S5R3 的 265 一致 |
| T2 `runtests.sh` 参考 | `testing/testcases.txt` 3 例（simple / fresnel / Fan fig12）+ 整个 `runtests.sh`，B、F4 各一遍 | 8/8 PASS；与仓库内参考数据 numdiff 相对误差：simple 0、fresnel 0、Fan fig12 1.277e-13（容差 1e-12/1e-12/1e-10）；这是本轮仅有的 3 个独立参考 |
| T3 全部 examples | 51 个 `.lua` 扣除 2 个 MPI 后 49 个 × 2 树 × 2 遍 = 196 次运行 | 196/196 完成，无超时、无 FLAKY；**38 个 example 在 B 与 F4 上 stdout/stderr 逐字节一致（SAME）**；11 个在 B 与 F4 上以同一方式失败（BOTH_FAIL，均为既有失败，见 §6）；DIFF=0、NEW_FAIL=0、DIFF_WITHIN_TOL=0 |
| T4 P04 管线 | `testing/p04_run_all.sh` 在 F4 树上运行（B 基线由管线自己导出） | **PASS**：`AGGREGATE.json` `overall=PASS`，38 个步骤全部 ok/expected_defect，unexpected=0（执行偏离见附录 B） |
| T5 P04 附属单测 | `testing/p04_aggregate_test.py`、`testing/d002/test_run_d002.py`，B/F4 各一遍 | 4/4 PASS，两树一致（SAME） |
| T6 C API | `examples/C_api` 在 B、F4 上构建运行，对照提交的 `spec.awk.out` | **BOTH_FAIL**：仓库自带的 `examples/C_api/Makefile` 是 macOS 专用（`-framework Accelerate -lc++`，rc=2）；改用 Linux 库编译同一 `main.c` 时，B 与 F4 都在同一处失败（示例仍用 P04 之前的 C API 名字 `Simulation` 而非 `S4_Simulation`，见路线图 P13 尚未执行）。两树失败完全相同，非本轮回归；`spec.awk.out` 因此未取得对照 |
| T7 新克隆可复现 | 本地 `git clone` 到 `$EV/clone/relr1`（源只读），克隆内 `make test` 一遍 | PASS：克隆 HEAD=`3de6d8b…`，`make test` rc=0，单元集合与 T1 的 F4 **EQUAL_UNIT_SET**（只靠已提交文件即可复现） |
| T8 D003 冒烟（可选） | 任务书 §5 标注“可选” | 预先声明 SKIP_DECLARED：S5R3 的 42 点 E2E 装置已在 S5R3 签收（U391），本轮重复需要再复制一套 S5R3 注入装置，且不改变非破坏性结论；本轮不新增修复验证 |
| U 对照 | 只跑 T2、T3（若能构建） | U_BUILD_UNAVAILABLE（见 §2），未运行；`U_DIFF_RELR1.tsv` 记录该事实 |

## 5 判定类别计数

分类来自 `VERDICT_RELR1.tsv`（334 行比较单元），按列名读取；`SUMMARY_RELR1.txt` 是同一批计数的机器可读版本。下列代码块是报告中的派生数字，end 门禁会逐项与源表比对。

<!-- COUNTS:BEGIN -->
REGISTRY_ROWS=334
PREREG_UNITS=221
SAME=317
DIFF_WITHIN_TOL=0
DIFF=0
NEW_FAIL=0
FIXED=0
BOTH_FAIL=12
TIMEOUT=0
SKIP_DECLARED=5
FLAKY=0
NON_REGRESSION=PASS
UNIT_COUNT=265
PREREG_SHA256=b0a064fe4cf6c7df34fc19719b6222a3773cf2daed53b3bd124c55e5c41297b8
<!-- COUNTS:END -->

汇总规则：NEW_FAIL=0、DIFF=0、FLAKY=0、TIMEOUT 两树一致（本轮 TIMEOUT=0），故记 **NON_REGRESSION=PASS**。FIXED=0：本轮没有出现“B 失败而 F4 通过”的单元，因此也没有任何“修复”主张。

## 6 例外清单（逐项）

**BOTH_FAIL（12）** —— 全部是两棵树**同样失败**的既有失败，不是本轮回归：

| 单元 | B/F4 | 失败原因（两树一致） |
|---|---|---|
| T3 1d/Christ_PRB_70_125113_2004/fig2b | rc=1/rc=1 | `attempt to call field 'GetRealMaterial' (a nil value)`（示例调用已不在当前 API 中的函数） |
| T3 2d/Li_JOSA_14_2758_1997/ex1_new、ex1_normal、ex1_orig、ex2 | rc=1/rc=1 | 运行到 `GetPoyntingFlux: A singular interface system was encountered …` 后以非零码退出（示例参数/结构自身的既有问题） |
| T3 convergence/1d/binary_grating、Li…/ex1/cellA、cellB、resonance_pos/ref | rc=1/rc=1 | Lua 5.2 下 `loadstring` 为 nil（示例为旧 Lua 版本所写；B 与 F4 相同） |
| T3 convergence/Li…/ex2/fig2 | rc=1/rc=1 | 脚本自身语法错误：`'end' expected (to close 'if' at line 22) near <eof>` |
| T3 magneto/slab | rc=1/rc=1 | 脚本自身语法错误：`unexpected symbol near ']'` |
| T6 C API | 均构建失败 | 见 §4 T6：macOS 专用 Makefile + 示例使用 P04 之前的 C API 名字；两树失败完全相同 |

对这 11 个 T3 失败，B 与 F4 的 rc 都是 1；其中 6 个 stdout/stderr 逐字节一致，另 5 个 stderr 仅在 Lua 报错信息里显示被截断的脚本绝对路径不同（`…/trees/B/…` 与 `…/trees/F4/…`），把显示路径规范化后完全一致。**这些失败在 B 上已经存在，不是本轮引入的。**

**SKIP_DECLARED（5）**：2 个 `examples/MPI_example/*.lua`（需要 MPI 构建，本环境没有 MPI）；1 个 T8（可选，理由见 §4）；2 个 U 树记录项（U_BUILD_UNAVAILABLE）。全部在**运行前**写在预注册里，运行后没有新增跳过。

**其余类别**：DIFF=0、NEW_FAIL=0、FIXED=0、FLAKY=0、TIMEOUT=0、DIFF_WITHIN_TOL=0。没有需要修复或重跑的单元。

## 7 口径与局限

1. **有独立参考的只有 T2 的 3 例**（simple、fresnel、Fan fig12，对照 `testing/` 的 `testcases.txt` 与仓库内参考数据）以及 T6 的 `spec.awk.out`。T6 因示例本身不能构建而未取得对照，见 §4。
2. 其余 46 个 example **只能写“F4 与 B 的输出一致（非回归）”**，**不是**“论文结果已复现”，也不能据此声称物理正确；它们没有独立参考数据。
3. 本环境的局限：Python 3.14、本机系统 LAPACK/BLAS 3.12.1、**没有 MPI**；U 树在本环境不能构建（见 §2）。这些与 P05 现有阶段报告记录的环境不同，可能影响数值细节。
4. 本轮**没有修改任何源码**；`S4/` 零改动（门禁断言）。文中不出现对 D003 的“已修好/已修复验证”措辞：本轮不是修复验证轮，B 列的观察同样不是修复证据。BOTH_FAIL 是既有失败，**不是** REPORTED_FAILURE 注入结果。
5. T4 首次尝试因管线自身的 `git -C <导出树> archive` 在“仓库工作树内的子目录”上只归档该前缀而导出空基线，已按 `ERRATA_RELR1.txt` 改用同一 F4 树的独立克隆重跑；两次尝试的目录都保留在证据目录里。

## 8 违规披露（两张表）

### 表一 越界写入尝试（命令自身写了仓库外路径，即使被拒绝/未落盘）

| 轮次 | 命令 | 是否落盘 |
|---|---|---|
| rel-r1 | 无 | — |

本轮执行者的所有含写入命令都经 `sh testing/d003/safe_run.sh p05-rel-r1 -- …` 运行，写入目标限于 `$EV/`、`testing/d003/`、`checkpoints/p05/`；没有出现 `/tmp` 或仓库外绝对写入目标。

### 表二 工具/脚本事件

| 轮次 | 事件 | 是否落盘 | 说明 |
|---|---|---|---|
| rel-r1 | 项目自带 `testing/s4test/test_lua_regression_negative.sh` 用 `mktemp -d /tmp/s4_lua_neg_XXXXXX` 写 /tmp | 是（其 trap 退出即删；且本环境每条命令在私有 `/tmp` tmpfs 中运行） | 项目套件固有行为，非执行者违规（与 P05-S4 R9 M3a/M3b、U338 同一处理口径）；本轮开始与结束的 /tmp 顶层快照均为 0 项且一致 |
| rel-r1 | 新增脚本与证据表由 agent 的文件写入工具创建（目标：`testing/d003/stage_relr1/`、`checkpoints/p05/evidence/p05-rel-r1/`） | 是 | 不是 shell 命令；目标都在允许目录内；已有装置未改动 |
| rel-r1 | 预注册在首次正式运行前因转义笔误重写过一次（删除后重写，sha256 取最终值） | 是 | 两次写之间没有发生任何正式运行；最终 sha256 记录在 `PREREG_RELR1.tsv.sha256.txt`（utc 03:48:17Z），首次正式运行晚于该时刻 |
| rel-r1 | T4 首次运行失败（空基线导出），失败输出留在 `$EV/p04run/F4_attempt1_git_subdir/` | 是（保留） | 未删除任何证据；原因与重跑方式见 `ERRATA_RELR1.txt` 与 §7.5 |
| rel-r1 | 门禁 `safe_run.log` 由每次调用追加，内容随时间增长 | 是 | 故不纳入 `SHA256SUMS.txt` 的静态清单（已在清单头部注明） |

## 附录 A 写入目标只读审查（摘要）

运行前只读审查了 `testing/p04_run_all.sh`、`testing/runtests.sh`、`Makefile.common` 的 `test` 目标、`examples/C_api/Makefile` 以及这些入口实际调用的辅助脚本（详见 `WRITE_TARGETS_RELR1.tsv`）：它们的写入都落在被调用的导出树内部、`$TMPDIR=$EV/tmp` 或本轮 `$EV/` 输出目录内；唯一的仓库外写入是上面登记的项目自带 `test_lua_regression_negative.sh` 的 `/tmp` 临时目录。T4 只在 F4 树上运行，且排在矩阵最后（它会重建该树的 `build/`）。

## 附录 B 预注册与执行偏离（ERRATA）

见 `ERRATA_RELR1.txt`（ER1）：T4 的执行从“`$EV/trees/F4` 归档导出树”改为“同一 F4 树的独立本地克隆 `$EV/t4src/F4`”，因为归档导出树位于主仓库工作树内，管线的 `git -C ROOT archive 963ccf1` 只会归档该子目录前缀（在 963ccf1 中不存在），导致基线导出为空。克隆在运行前核对了 `HEAD=3de6d8b…` 且 `HEAD:S4=589e15eb…`；期望、超时与比较规则均未改动。

正式 end 门禁结果见附录 C（门禁后追加）。

## 附录 C 正式 end 门禁结果（门禁后只追加）

本附录由 relr1_appendix_c.py 在提交 (i) 之后、按任务书第 8.5 节正式运行一次 `relr1_check.py --phase end` 的结果追加；
正式门禁若 FAILS>0 不修、不重跑，照实写 INCOMPLETE。

| 项 | 值 |
|---|---|
| 门禁文件 | checkpoints/p05/evidence/p05-rel-r1/GATE_RELR1_end.txt |
| 门禁文件 sha256 | `550cafdbe9eeb97ff63c0e930b0889ffefb0a4671230b2388ec26fdc78cf3296` |
| 正式门禁计数 | pass=23 fail=0 total=23 |
| FAILS | 0 |
| FINAL_STATUS | COMPLETE |
| 正式门禁预跑 | GATE_RELR1_pre.txt（同一条只读代码路径，仅 --out 不同） |

### C.1 交付状态

```
$ git log -1
0cdc6d63e10f76b1b7b43d65e7a5a84636f63d64
P05 delivery round REL-R1 (i): non-regression verification report, registries, gate scripts, STATE rows
2026-10-19 15:10:31 +1100

$ git status --short
(empty)
```

### C.2 结论

本轮已完成 P05 交付轮 REL-R1 范围，等待用户审核。
