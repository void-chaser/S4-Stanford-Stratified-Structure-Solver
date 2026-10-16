# P05-S4 R9 M0+M2 任务书：S3R5 勘误、F4 全套装置、K 继承证明、SOLN 修后验证与 M2 回归（F4）

## 0. 身份与边界
- 本轮是 P05-S4 的子轮次 R9 的 M0 与 M2 两个里程碑（不是新阶段）。轮次标识 `r9m0`/`r9m2`；证据目录 `p05-s4r9/m0`、`p05-s4r9/m2`；小表目录 `checkpoints/p05/registries/s4r9/M0/`、`.../s4r9/M2/`；报告 `checkpoints/p05/P05_S4R9_M2_REPORT.md`（M0 内容并入此报告第一部分）。任务书原文存为 `checkpoints/p05/briefs/P05_S4R9_BRIEF_M0M2.md`。
- 不得宣布任何阶段完成，不得询问是否签收。本轮是 P05-S4 在 F4 上的修后验证与回归；M1 等价重跑与 M3（make test、Python/Lua E2E）不在本轮。
- 开工先读：`AGENTS.md` → `checkpoints/p05/STATE.md` → 本任务书 → `P05_S3R5_CLOSEOUT.md` → `registries/s3r5/` 全部小表 → `P05_S4R8_M2E_REPORT.md` → `registries/s4r8/M2/r8m2e/` 的 PREREG/VERDICT/M2_CONSOLIDATED。
- 开工门禁：HEAD = `a3a74bb32f68f4d330891394b3e660ef106ebfd1`；`git rev-parse HEAD:S4` = `589e15eb11fcb04e031b524f25a443e7921946cf`（F4）；判定器 sha256 = `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`；`git status --short` 为空。任一不符就停下报告。
- **不得修改 `S4/`**（含 seam、RNP、rcwa）。不得修改历史装置与判定器。

## 1. 写入与执行纪律（硬规则，同 s3r5）
1. 每条含写入的命令开头先执行：
   `REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/<m0|m2>; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`
   然后一律经 `sh testing/d003/safe_run.sh p05-s4r9/<m0|m2> -- <命令>` 运行。
2. 写入目标只能以 `$EV/`、`$REPO/testing/d003/`、`$REPO/checkpoints/p05/` 开头。任何以 `/` 开头且不在 `$REPO` 下的路径都不得出现，包括 `/tmp` 和各种占位路径。**不得写入其他轮次的证据目录**（含 `p05-s3r5/`、`p05-s4r8/`）。读取其他轮次的产物（例如 s3r5 的 F4 库）只读、先核对 sha256。脚本里的 EV 常量由命令行参数给出，或硬编码为 `p05-s4r9/<m0|m2>`，不允许任何默认值指向别的轮次。
3. 内联命令不得含 `>` 字符（含 `2>&1`）。需要输出的核对一律写成脚本，经 safe_run 运行。含写入的命令不得用 `2>/dev/null`。核对路径只用 `ls -d` 或 `test -e`。不做沙箱探测，不做反例测试。
4. 新脚本第一行用标准首段，文件名带 `r9` 后缀，放 `testing/d003/stage_s4r9/`。复制历史脚本时：REPO 行换成标准首段（历史脚本多为 `REPO=$(git rev-parse --show-toplevel 2>/dev/null)`，这一行的变化属预期），EV 改为本轮，树/库/驱动路径改为 F4；diff 中其他变化逐条说明，写入 `RUNNER_DIFF_R9.txt`。运行前用 grep 工具查禁止项（`/tmp`、`2>/dev/null`、计划文件里的 `$EV` 字面量、指向 `p05-s4r8/`/`p05-s3r5/` 的写入路径）。正则不得命中标准首段的 `"$EV/tmp"` 和 Python 的 `1 << 20`。草稿查出问题后改正不算违规。
5. Python 一律 `python3 -I -B`。start 门禁记录 `__pycache__`、`.o` 基线清单与 mtime，end 只判本轮新增。
6. 每一次 `rm`、`mv`、重跑覆盖（含门禁重跑）都写进事件表二，注明 safe_run.log 行号。门禁失败后重跑用 `_R2` 新文件名，旧文件保留。脚本先用合成输入跑通，再正式运行。
7. 长输出加 `head`/`tail`，或用 read 的 offset/limit。
8. 停止策略：只有真实基线异常、无法解释的越界改动、第 6 节硬停止条件才停。合法中间产物让工作区非空，不是停止理由。
9. 证据清单中的 `safe_run.log` 按 U288 记录"清单写入时的行数 N 与前 N 行 sha256"。
10. registries 复制不改名；总表合计必须断言等于各分表行数之和。

## 2. 输入事实（规划者已核实，直接使用）
- H-1（S3R5 采信）：F4 = `05097a7`，树 `589e15e…`；`S4/S4.cpp` 1760–1773 → 1760–1786（净 +13），F3 第 1774 行及以后的行号在 F4 上 +13（`registries/s3r5/LINEMAP_F3_F4_S3R5.tsv`）。F4 的 dbg/san/plain 库与 init-F4-dbg/san/san-AL 驱动的 sha256 见 `registries/s3r5/BUILD_S3R5.tsv`，产物在 `evidence/p05-s3r5/build/`（只读，先核 sha）。SOLN 的 F4 K 值见 `registries/s3r5/K_MAP_F4_S3R5.tsv`（18 项，与 F3 相同）。
- H-2（S3R5 文书瑕疵，只勘误不重跑）：
  - (a) `P05_S3R5_CLOSEOUT.md` 第 21、34、69、167、246、257 行用了"完全一致/完全保持一致/证实/精确"等强化词；第 167 行"已在第 5 节证实"应为第 6 节；
  - (b) `K_MAP_F4_S3R5.tsv` 中 dbg 1764 行的 `F4_size` 记的是外层 malloc 的 n（215/983 = malloc_aligned size + 23），`F3_size` 记的是 malloc_aligned 的 size（192/960），口径不同；`PASS_EXACT_MATCH` 只比较 k；
  - (c) `R9_INPUTS_S3R5.tsv` 的 GDB_SCRIPT_AUDIT 只审了 4 个脚本。仓库内的行号断点实际有：`stage_s4/win64_diag_r8m2b.gdb:12` `S4/S4.cpp:1894`（F4=1907）；`stage_s4/diag_r8m2c.py:95` 内嵌 `S4/S4.cpp:2445`（F4=2458）；`stage_s4r7/gdb_chain_jones_line_r7.gdb:16` `S4.cpp:2413`（F2 行号）；`stage_s4/m210_b_r8m2a2_R2.gdb`（B 树，不受影响）；`stage_s4/r6_plan14_caller.gdb` `fmm_kottke.cpp:94`（文件未改）；`stage_s1r/layer_probe.gdb`、`nb_probe.gdb`（历史）。"0 个需重写"的结论只对已审的 4 个成立；
  - (d) R9_INPUTS 只列 init 族驱动，未覆盖 M2 回归所需的其他驱动族。
- H-3（M2 有效集，F3）：`registries/s4r8/M2/r8m2e/M2_CONSOLIDATED_R8_M2e.tsv` 共 259 行，`consolidation_status` 不含 SUPERSEDED 的 202 行为有效集。预注册来源依次为 `r8m2b/PREREG_M2_COMBINED_174_R8_M2b.tsv`、`r8m2c/PREREG_M2_DELTA_R8_M2c.tsv`、`r8m2d/PREREG_M2_DELTA_R8_M2d.tsv`、`r8m2e/PREREG_EFFECTIVE_FORMAL_R8_M2e.tsv`、`r8m2e/PREREG_M2_DELTA_R8_M2e.tsv`（`#` 开头的行是注释）。按该行 `verdict_source` 指定的轮次取预注册行，202 行全部能解析。有效集的 (tree, driver) 分布如下，用作断言：
  - B：init-B-dbg 9（SOLN）、r6dnv1-B-dbg 1（M2-10）；F2：seam-fmmret-F2 1（M2-09）；
  - F3：d003-F3-plain 72、d003plan-F3-plain 9、dual-F3-dbg 2、init-F3-dbg 18（SOLN 9 + 非 SOLN 9）、init-F3-san 12（SOLN 6 + 非 SOLN 6）、init-F3-san-AL 3（SOLN）、layers-F3-dbg 8、layers-dual-F3-dbg 2、nan-F3 3、polyinj-F3-dbg 17、polyinj-F3-san 6、r6bseam-seamF-F3 6、r6bstate-F3-dbg 13、r6bstate-F3-san 13、seam-fmmret-F3 1、seamF-F3-san 6；
  - 由此：SOLN 在 F3 上 18 点 + B 9 点；非 SOLN 在 F3 上 **173 点**；B/F2 非 SOLN 2 点。
  - gdb 脚本使用情况：`r6c_state_r8m2a3.gdb` 38 行、`r6c_state_bt_r8m2d.gdb` 18 行、`m210_b_r8m2a2_R2.gdb` 1 行（B），其余 145 行不用 gdb。前两个是函数名断点（`r6_probe`、CLM、GetLayerSolution），不受行号影响。
- H-4（F3 驱动构建来源，复制为 r9 版本）：
  - `stage_s4/build_r8m2a2_R3.py:43-53, 187-221`（init/polyinj/dual/layers/layers-dual/nan(bufseam)/r6bstate-san/init-san/polyinj-san/seamF-san/fmmret-san）；
  - `stage_s4r8/link_drivers_r8.sh:46-53`（d003-F3-plain、d003plan-F3-plain、seam-fmmret-F3，`-O1`）；
  - `stage_s4r8/link_drivers_r8m1.sh:51`（r6bstate-F3-dbg）；
  - `stage_s4r8/link_r6b_seam_r8m1.sh`（r6bseam-seamF-F3）；
  - `stage_s4r8/build_seam_plain_r8.sh`、`build_seam_r8m1.sh`（seam 库）；
  - `stage_s4/build_r8m2e.py`（san-AL，`-Wl,--wrap=malloc_aligned`）。
  - F3 驱动与库的 sha256 见 H-3 中各预注册的 `driver_sha256`/`lib_sha256` 列。
  - seam 补丁 `testing/d003/seam/apply_seam_r2.py`、`apply_seam_b2.py`、`apply_seam_r4_buf.py`、`apply_seam_r5_fmmret.py` 按**精确文本锚点**替换。family C 的站点（layer_modes、pB->q、rwork、work、FieldCache）都不在 InitSolution 内 [源码]。
- H-5（运行与判定装置，复制为 r9 版本）：`stage_s4/run_m2_r8m2e.py`、`run_formal_r8m2e.py`、`facts_m2_r8m2e.py`、`state_judge_m2_r8m2e.py`、`verdict_m2_r8m2e.py`、`posctrl_m2_r8m2e.py`；对照映射 `registries/s4r8/M2/r8m2a3/CONTROL_MAPPING_R8_M2a3.tsv`。
- H-6（历史教训，必须遵守）：
  - `gdb -batch` 的退出码恒为 0，程序 rc 只看日志里的 "exited with code NN"（八进制）；dbg 行按 gdb+nogdb 成对运行，两者不同判 GDB_DIVERGENT；
  - 计划里的路径必须是绝对路径，`ASAN_OPTIONS`/`UBSAN_OPTIONS` 的 `log_path` 在 COMMAND_PLAN 中不得含 `$EV` 字面量；
  - 驱动 printf 走全缓冲，崩溃后 stdout 为空，此时用 bt 中驱动行号判断崩在第几次调用（`driver_r6b_state.cpp:211`=call1，`:227`=call2）；
  - init-*-san 的 S4_malloc 走 posix_memalign，不经 `--wrap=malloc`，san 下的 1764 只能用 init-F4-san-AL（aligned:3）；
  - I6 只比较恢复调用与对照同序号调用，失败调用不做逐字节比对。

## 3. 用户裁决（追加到 `registries/RULINGS.tsv`，5 列，start 门禁通过后追加）
- **U291**：S3R5 结果采信，作为 R9 的输入（不是签收）。H-2(a)(b)(c)(d) 写成 ES3R5-1 至 ES3R5-4，追加到 `checkpoints/p05/ERRATA_S3R5.txt`，不重跑，不改 s3r5 已提交文件。
- **U292**：R9 分三部分：M0+M2（本轮）；M1（F4 上重跑 M1 1302 行，与 F3 冻结事实等价比对，另发任务书）；M3（阶段收口：`$EV` 导出 F4 树上的 `make test` 相对 B，Python/Lua E2E，只做一次，另发任务书）。B 树与 F2 树未变，M2-10（B）、M2-09 的 F2 侧、9 个 SOLN B 行本轮不重跑，引用 r8m2b/r8m2e 的正式判定，并核对驱动 sha256。
- **U293**：SOLN F4 共 18 点（dbg 9、san 6、san-AL 3）的期望：rc1=1、rc2=0、signal=0、hit=1、class=REPORTED_FAILURE、exp_post_call1_solution=NULL、exp_crash_call=NONE、exp_san=0（san 行）、exp_I6=HOLD（对照为同驱动、同 env、无注入的 F4 对照点，比较 call 2）。状态 INFLUENCED（s3r5 自检 D 已观察到 dbg 行）。K 取 `K_MAP_F4_S3R5.tsv`。
- **U294**：M2 回归 173 点：逐点取 F3 有效预注册行，tree→F4，driver→F4 对应驱动，sha 字段换为 F4 产物，point_id 与 control_point_id 的 `-F3` 后缀改为 `-F4`，其余 exp_* 原样保留（包括 r8m2c/d/e 勘误后的有效值）。状态 INFLUENCED，basis 写"R9 regression of <F3 point_id>"。不得因 F4 结果改期望。
- **U295**：K 继承证明。凡带计数注入的行（`init:K`、`aligned:K`、`S4FMM_NTH`、`win:K` 等），按"驱动族 × 去掉 INJECT 的 env"分组，每组在 F3 与 F4 驱动上各跑一次无注入的 gdb 映射（在注入 wrapper 处下断点，`bt 4`），记录到 K_max+2 为止的 (k, size, 最内层 S4/ 帧的函数与行号)；F3 行号经 LINEMAP 映射到 F4 后，两个序列必须相同。相同则 K 沿用 F3 值；不同则该组的行记 `NOT_RUN_K_DIVERGENT`，不改期望，列入"需用户裁决"。SOLN 组可以直接引用 s3r5 的 K_MAP（需注明 ES3R5-2 的口径说明）。
- **U296**：装置对等。F4 驱动与 F3 对应驱动的编译/链接命令行，去掉树路径后必须逐条相同（`BUILD_OPTION_DIFF_R9.txt`，差异 0 项）；每个 F4 库的告警数等于 F3 对应库；seam 补丁的 apply 报告与 F3 相比只允许行号偏移（1774 之后 +13）。s3r5 的 3 个库和 3 个 init 驱动沿用，不重编，只核 sha，并补做命令行对比。
- **U297**：执行顺序与停止。M0（装置、K 证明、预注册冻结并提交）→ 阳性对照 → 冒烟（单遍）→ 正式两遍 → 判定 → 合并总表。冒烟出现 MISMATCH、GDB_DIVERGENT 或 INVALID 时停在冒烟，只做分诊（核对崩溃帧与日志），不改期望，不进入正式运行。正式运行中的 MISMATCH 或 FLAKY 照实记录，只分诊，不重跑覆盖。
- **U298**：本轮允许精简 STATE.md：第 2 节 R1–R8 的关键数字可以合并成指向各轮报告的一行，开放问题表里已关闭的项可以只留一行摘要。STATE 不超过 8192 字节。

## 4. 步骤
### M0
- **S-A 开工门禁**：用 `gate_r9.sh start` 写 `GATE_R9_start.txt`，内容包括：
  - HEAD、`HEAD:S4`、判定器 sha256、`git status --short`；
  - `/tmp` 顶层只读快照（条目数和 sha256）；
  - `registries/s3r5/SHA256SUMS.txt` 逐项比对；
  - s3r5 产物（3 个库、3 个驱动）与 init-B-dbg 的 sha256；
  - `__pycache__`、`.o` 的基线清单（含 mtime）。
- **S-B 裁决与勘误**：追加 U291–U298；在 `ERRATA_S3R5.txt` 追加 ES3R5-1 至 ES3R5-4；新建 `checkpoints/p05/registries/s4r9/ERRATA_9.txt`（编号 E9-n）。做记录提交 (i)：任务书、RULINGS、ERRATA。
- **S-C 有效集抽取**：用 `effective_set_r9.py` 写 `M2_EFFECTIVE_F3_R9.tsv`（202 行），并断言 H-3 的每个计数，任一计数不符就停。
- **S-D 装置**：从 F4 提交 `git archive`（经 safe_run，以管道传给 tarfile）导出到 `$EV/trees/`，按 H-4 应用 seam，构建 F4 全部所需的库与驱动（按 H-3，除 s3r5 已有的 init 族外，共 15 个驱动族）。写以下文件：
  - `BUILD_R9.tsv`：产物、sha256、命令、rc、告警数，以及 F3 对应项的 sha 与告警数；
  - `BUILD_OPTION_DIFF_R9.txt`；
  - `SEAM_APPLY_DIFF_F3_F4_R9.txt`；
  - `DRIVER_MAP_F3_F4_R9.tsv`：F3 驱动 → F4 驱动 → 双方 sha。
- **S-E 行号断点审计**：用 `gdb_audit_r9.py` 扫描 `testing/d003/` 下全部 `.gdb` 文件和内嵌 gdb 命令的 `.py` 文件中 `文件:行号` 形式的断点，写 `GDB_LINE_AUDIT_R9.tsv`，列为：脚本、行、文件:行号、所属树、F4 映射行、R9 是否使用、处理方式。R9 运行计划用到的脚本，必须全部是函数名断点或已映射到 F4；用到行号断点而未映射的，就停。
- **S-F 无注入对照**：所有 F4 驱动 × 本轮用到的 env 组合各跑一次，期望 rc 0、san 报告 0。写 `probe/noinj_control_r9.txt` 与 `NOINJ_R9.tsv`。出现 rc≠0 或 san 报告时，先查 F3 对应对照的历史值；与 F3 相同，记事实并继续；与 F3 不同，就停。
- **S-G K 继承证明**：按 U295 写 `K_INHERIT_R9.tsv`、`K_INHERIT_RAW_R9.txt`。
- **S-H 预注册**：用 `prereg_r9.py` 生成以下文件，写入时间戳和 `.sha256`：
  - `PREREG_SOLN_F4_R9.tsv`：18 行，含对应的 F4 对照点；
  - `PREREG_REGRESS_F4_R9.tsv`：173 行，含对照点的 F4 版本；
  - `PREREG_CITED_R9.tsv`：引用不跑的 12 行（B 的 SOLN 9 行、M2-10、M2-09 的 F2 侧，以及 SOLN F3 18 行作为对比基准，按需要列出）；
  - `COMMAND_PLAN_R9.tsv`：路径一律绝对，没有 `$EV` 字面量。
  
  断言：18 + 173 = 191 个运行点；各驱动族计数与 H-3 一一对应。
- **S-I M0 提交 (ii)**：提交预注册、sha256、时间戳、装置脚本、M0 小表，提交信息末尾写 `awaiting user review`。**正式运行必须在此提交之后**。

### M2
- **S-J 阳性对照**：复制 r8m2e 的阳性对照，并为新增期望（post_call1_solution=NULL、crash_call=NONE、I6 HOLD/VIOLATED）加合成用例。运行一次，写 `POSCTRL_R9.txt`，必须全部 PASS 才能继续。
- **S-K 冒烟**：单遍运行以下各点：
  - SOLN F4 18 点全部；
  - 回归中每个驱动族各 1 点（共 15 点，含 seam-fmmret-F4）。
  
  写 `VERDICT_SMOKE_R9.tsv`。按 U297 决定是否继续。
- **S-L 正式两遍**：191 点 × 2 遍，dbg 行按 gdb+nogdb 成对运行。写 `FACTS_pass1/2_R9.tsv`、`STATE_pass1/2_R9.tsv`、`VERDICT_R9.tsv`、`SUMMARY_R9.txt`，汇总 MATCH、MISMATCH、FLAKY、GDB_DIVERGENT、NOT_RUN_K_DIVERGENT 等各类计数。
- **S-M 合并总表**：写 `M2_CONSOLIDATED_F4_R9.tsv`：191 个 F4 点 + 引用的 B/F2 点，每行注明 F3 对应点的判定。另写 `RED_POINTS_LEDGER_APPEND_R9.tsv`：RP-R8-M2c-1 与 1b 的 F4 事实与点号；状态只写事实与判定类别，是否关闭由用户裁决。
- **S-N 收尾**：
  - 更新 STATE.md（≤ 8192 字节，按 U298 精简）；
  - 写报告；
  - 小表复制到 `registries/s4r9/M0/`、`M2/`，写 `SHA256SUMS.txt`，逐个比对；
  - 证据目录写 `SHA256SUMS.txt`；
  - 运行 `gate_r9.sh end`，期望 `HEAD:S4` 仍为 F4，`S4/` 未改；
  - 收尾提交 (iii)。报告末尾附 `git log -3 --oneline`、`git log -1`、`git status --short`。

## 5. 产物命名
本轮新建的脚本与表一律带 `r9` 或 `R9` 后缀；复制到 registries 时不改名。

## 6. 硬停止条件
1. 开工门禁任一项不符。
2. H-3 的有效集计数不符，或某个 point_id 无法唯一解析出预注册行。
3. 任一 F4 构建失败；相对 F3 出现新增告警或编译命令行差异；seam 补丁 apply 失败或锚点匹配数不为 1。
4. R9 运行计划用到了未映射的行号断点。
5. 无注入对照出现与 F3 历史不同的 rc 或 san 报告。
6. 阳性对照未全部 PASS。
7. 冒烟出现 MISMATCH、GDB_DIVERGENT 或 INVALID（只分诊，不进入正式运行）。
8. 任何无法解释的越界写入、对 `S4/` 的改动，或写入了其他轮次的证据目录。

K 不一致（U295）不算硬停止：对应行记 NOT_RUN_K_DIVERGENT，其余行照常运行。

## 7. 报告要求
- 报告分为：门禁、裁决与勘误、有效集抽取与计数断言、装置与对等、行号断点审计、无注入对照、K 继承、预注册（sha256 与提交号）、阳性对照、冒烟、正式两遍、合并总表、红点台账追加、事件两张表、需用户裁决。
- 措辞：
  - REPORTED_FAILURE 只表示返回码非零；
  - SOLN F4 行写"修后验证事实：<点号>，判定 <类别>"，不写"已修好"；
  - 不写"100%""完全""证实""精确"等强化词；
  - B 列不是修复证据。
- "需用户裁决"一节只列规划者无法从仓库查到的事项，能查到的直接给出来源与行号。预期会有一项：RP-R8-M2c-1/1b 是否关闭，附 F4 正式判定点号。
- 结尾写"本轮已完成/未完成 R9 M0+M2 范围，等待用户审核"。
