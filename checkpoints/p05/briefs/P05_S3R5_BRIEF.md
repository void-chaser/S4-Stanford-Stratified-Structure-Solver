# P05-S3R5 任务书：InitSolution 分配失败修复（RP-R8-M2c-1/1b）、冻结 F4、F4 装置与映射、自检

## 0. 身份与边界
- 本轮是 P05-S3 的子轮次 S3R5（不是新阶段），轮次标识 `s3r5`，证据目录 `p05-s3r5`，小表目录 `checkpoints/p05/registries/s3r5/`，报告 `checkpoints/p05/P05_S3R5_CLOSEOUT.md`。不得宣布任何阶段完成，不得询问是否签收。
- 开工先读：`AGENTS.md` → `checkpoints/p05/STATE.md` → 本任务书 → `checkpoints/p05/P05_S4R8_M2E_REPORT.md` → `checkpoints/p05/registries/s4r8/M2/r8m2d/S3R5_DESIGN_R8_M2d.md` → `checkpoints/p05/P05_S3R4_CLOSEOUT.md`（作为修复轮的格式参考）。本任务书原文存为 `checkpoints/p05/briefs/P05_S3R5_BRIEF.md`。
- 开工门禁：HEAD = `73c9b7b9c3a9e008c214c7cb333212c8ca3856a5`；`git rev-parse HEAD:S4` = `6cff923a02baf19e01966b2339755cbf3a5deeef`（F3）；`testing/d003/judge_d003.py` sha256 = `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`；`git status --short` 为空。任一不符就停下报告。
- **`S4/` 中只允许修改 `S4/S4.cpp` 的 `Simulation_InitSolution` 函数体内第 1760–1774 行这一段**（U283）。其他任何 `S4/` 文件、其他函数、LinearSolve seam 都不改。
- 本轮不运行正式两遍，不冻结 R9 的预注册，不开始 M3，不跑 `make test`。本轮的自检不是修复后验证；修后验证由 P05-S4 R9 在 F4 上完成。

## 1. 写入与执行纪律（硬规则，同 r8m2e）
1. 每条含写入的命令开头先执行：
   `REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`
   然后一律经 `sh testing/d003/safe_run.sh p05-s3r5 -- <命令>` 运行。**唯一例外**：第 4 节 S-D 修改 `S4/S4.cpp` 用 edit 工具（不经 safe_run），在报告中记录 edit 前后该段的 sha256。
2. 写入目标只能以 `$EV/`、`$REPO/testing/d003/`、`$REPO/checkpoints/p05/` 开头；S-D 另外允许写 `$REPO/S4/S4.cpp`；S-K 另外允许写 `$REPO/AGENTS.md` 的第 6 节（U287）。任何以 `/` 开头且不在 `$REPO` 下的路径都不得出现，包括 `/tmp` 和各种占位路径。**不得写入其他轮次的证据目录**（r8m2e 曾两次误写 m2d，见 E8-118）。脚本里的 EV 常量必须由命令行参数给出，或者硬编码为 `p05-s3r5`，不允许任何默认值指向别的轮次。
3. 内联命令中不得出现 `>` 字符（含 `2>&1`）。需要输出的核对一律写成脚本，经 safe_run 运行。含写入的命令不得用 `2>/dev/null`。核对路径只用 `ls -d` 或 `test -e`。不做沙箱探测，不做反例测试。
4. 新脚本第一行用标准首段。运行前用 grep 工具查禁止项：`/tmp`、`2>/dev/null`、计划或命令里出现的 `$EV` 字面量、指向 `p05-s4r8/` 的写入路径。查禁止项的正则不得命中标准首段里的 `"$EV/tmp"`，也不得命中 Python 的 `1 << 20`。草稿查出问题后改正不算违规，违规以实际执行为准。
5. Python 一律用 `python3 -I -B`。start 门禁记录 `__pycache__`、`.o` 的基线清单和 mtime，end 门禁只判本轮新增的。
6. 每一次 `rm`、`mv`、重跑覆盖（含门禁重跑）都写进事件表二，并注明 safe_run.log 行号。脚本先用合成输入跑通，再做正式运行。门禁失败后重跑时，失败的门禁文件不删除，改用 `_R2` 等新文件名，旧文件保留并披露。
7. 探针输出必须写到 `$EV/probe/<脚本名>.txt` 并进入 SHA256SUMS。
8. 长输出一律加 `head`/`tail`，或用 read 工具的 offset/limit。
9. 停止策略：只有真实的基线异常、无法解释的越界改动、或第 5 节的硬停止条件才停。合法的中间产物让工作区非空，不是停止理由。
10. 本轮新增的脚本和表一律带 `s3r5` 后缀；复制到 registries 时不改名。
11. 历史装置（`driver_r6b_state.cpp`、`inject_s3r4_init.cpp`、`inject_r8m2e_aligned.cpp`、`build_r8m2a2_R3.py`、`build_r8m2e.py` 等）只读。需要改动的，复制成带 `s3r5` 后缀的新文件：REPO 行换成标准首段，EV 常量改为 `p05-s3r5`，树和库路径改为 F4。diff 中只允许这几类变化，其他变化要逐条说明。

## 2. 输入事实（规划者已核实，直接使用）
- H-1（r8m2e 结果采信）：合并总表 `M2_CONSOLIDATED_R8_M2e.tsv` 共 259 行：有效 202 行全部 MATCH（formal_r8m2b 147 行、formal_r8m2c 27 行、formal_r8m2e 28 行），SUPERSEDED 57 行。registries 的 33 项 sha256 全部一致，end 门禁 `FAILS=0`。
- H-2（缺陷源码，F3）：`S4/S4.cpp:1760-1773`：
  - 1760–1762：`if(NULL != S->solution){ Simulation_DestroySolution(S); }`，执行后 `S->solution == NULL`（见 `S4.cpp:2857`）；
  - 1763：`S->solution = malloc(sizeof(Solution_))`；
  - 1764：`S->solution->ab = S4_malloc(...)`，在判空之前解引用；
  - 1765：`S->solution->solved = malloc(...)`；
  - 1766–1772：判空后只返回 1，不做清理，`S->solution` 保持非空；
  - 1773：`memset(solved)`。
  - `Solution_` 定义在 `S4.cpp:195-198`，只有 `ab` 和 `solved` 两个成员。`ab` 用 `S4_free` 释放（底层是 `free_aligned`，见 `S4.cpp:149`）；`solved` 用 `free` 释放（见 `S4.cpp:2849-2856`）。
- H-3（调用方）：`Simulation_InitSolution` 的调用点有 `S4.cpp:1803, 2969, 3318, 3565, 4070`、`main_lua.c:2184`、`main_python.c:1274`。重试路径的崩溃点：1764 失败时为 `S4.cpp:1995`（`memset(pab)`），1765 失败时为 `S4.cpp:2021`（`sol->solved[i]`）。
- H-4（F3 装置）：
  - 库：F3 dbg `56f72c58…`（`evidence/p05-s4r8/build_r8/F3-dbg/build/libS4.a`）；F3 san `2775b9b2…`（`evidence/p05-s4r8/m2a2/build_R3/lib_F3_san/libS4.a`）；B dbg 为 `m2a2/build_R3/lib_B_dbg`。
  - 构建参数见 `testing/d003/stage_s4/build_r8m2a2_R3.py:43-53, 187-219`（DBG_FLAGS、SAN_FLAGS、WRAP_INIT）和 `build_r8m2e.py`（`-Wl,--wrap=malloc_aligned`）。
  - F3 上 SOLN 的 K：dbg 的 `init:K` 见 `PREREG_EFFECTIVE_FORMAL_R8_M2e.tsv`（例如 fft-ng5 下 1763=10、1765=12）；san 的 `init:K`（例如 fft-ng5 下 1763=8、1765=9）；`aligned:3`（1764，三个组合都是 3）。
- H-5（r8m2e 文书瑕疵，只勘误，不重跑）：
  - (a) 报告第 126 行写了"100%"，第 225 行写了"完全证实"，违反 M2e 任务书 §6；
  - (b) `SUMMARY_R8_M2e.txt` 第 1 行写成 `VERDICT_SUMMARY_R8_M2d`，`FACTS_pass1.tsv` 和 `FACTS_pass2.tsv` 第 1 行写成 `# FACTS_R8_M2d`；
  - (c) `evidence/p05-s4r8/m2d/safe_run.log` 和 `m2e/safe_run.log` 与各自的 SHA256SUMS 不一致。原因是写完清单后，git add/commit 又追加了两行（m2d 的前 21 行、m2e 的前 28 行与清单哈希一致）；
  - (d) posctrl 运行 3 次、start 门禁运行 5 次，违反"只运行一次"，且有一次在 start 门禁之前就追加了 RULINGS/ERRATA；
  - (e) 两次写入 m2d 证据目录，已披露并删除；
  - (f) `REGRESSION_PLAN_F4_R8_M2e.tsv` 只注明 aligned 的 K 需要重新映射，没有覆盖 `init:K`；F3 行的 `b_baseline_behavior` 写成"对照基线依然崩溃"，措辞不当。
- H-6：`make test`（`Makefile.common:165-214`）会执行 `rm -rf $(OBJDIR)`，并在仓库根目录生成 `.so` 文件。所以它只能在 `$EV` 下的导出树中运行。本轮不跑。

## 3. 用户裁决（追加到 `checkpoints/p05/registries/RULINGS.tsv`，保持 5 列）
- **U283**：批准 P05-S3R5 修改 `S4/S4.cpp` 中 `Simulation_InitSolution` 的第 1760–1774 段，修复 RP-R8-M2c-1/1b。这一授权改变了 S2R4 对 1754/1756（B 行号）的范围划分（承接 U275）。`S4/` 中其他任何内容不改。
- **U284**：修复采用"局部变量分配、全部成功后再挂到 S"的写法，替代 `S3R5_DESIGN_R8_M2d.md` §2.2 的逐步判空写法。要求如下：
  1. 先 `Solution_ *sol = (Solution_*)malloc(sizeof(Solution_));`。若为 NULL，保留原有的 S4_TRACE 和 S4_MSG_ERROR（文字仍为 "Could not allocate solution memory"），返回 1。
  2. 然后**按原顺序**执行 `sol->ab = S4_malloc(...)` 和 `sol->solved = malloc(...)`，即使 ab 已失败也照常执行，保证 F3 与 F4 的分配次数和顺序相同。
  3. 任一为 NULL 时：`if(NULL != sol->ab) S4_free(sol->ab); free(sol->solved); free(sol);`，同样的 TRACE/MSG，返回 1。此时 `S->solution` 保持为 NULL（1760–1762 已保证）。
  4. 全部成功后执行 `memset(sol->solved, 0, ...)` 和 `S->solution = sol;`。
  5. 返回码与消息文本不变，函数其余部分不变。
  修复后的预期 [源码]：1763/1764/1765 任一失败时，调用 1 返回 1，`S->solution == NULL`；重试时重新进入 InitSolution。
- **U285**：提交分三次：
  - (i) 记录提交：任务书、RULINGS、ERRATA、修复前源码确认；
  - (ii) **F4 提交**：只包含 `S4/S4.cpp`，信息为 `fix(p05-s3r5): InitSolution allocation failure cleanup (RP-R8-M2c-1/1b) (awaiting user review)`。它的 `S4/` 树即 F4；
  - (iii) 收尾提交：装置、映射、自检、报告、STATE、AGENTS 第 6 节、registries。
- **U286**：F4 装置在 `$EV` 下从 F4 提交重新导出构建，包括 dbg 库、san 库、plain 库，以及驱动 `init-F4-dbg`、`init-F4-san`、`init-F4-san-AL`。参数与 F3 对应项逐项相同，只是树不同。B 侧的 `init-B-dbg` 沿用现有产物，不重编，只核对 sha256。F4 上所有 SOLN 的 K（dbg 和 san 的 `init:K`、`aligned:K`）都要在 F4 上用 gdb 按 caller 源码行重新映射，不得沿用 F3 的值。由于 U284 保持分配顺序，预期 K 与 F3 相同；如有不同，记录事实并说明原因，这不算硬停止。
- **U287**：允许修改 `AGENTS.md` 第 6 节：冻结表追加 F4 一行（提交、`S4/` 树哈希、含义为"P05-S3R5 修复后冻结被测树；自检不是 S4 验证，修后验证由 P05-S4 R9 在 F4 上完成"），开工门禁的树哈希改为 F4。AGENTS 其他内容不改。
- **U288**：按 H-5 勘误，不重跑，不改 r8m2e 已提交的文件：
  - (a)(b)(f) 写成 E8-116、E8-117、E8-119；
  - (c) 写成 E8-118 的一部分，并定下规则：自 s3r5 起，证据清单中 `safe_run.log` 改为记录"清单写入时的行数及前 N 行的 sha256"，不再记录整个文件的哈希；
  - (d)(e) 按执行偏离接受，写入 E8-118，不追认为合规。
  
  E8 条目追加到 `checkpoints/p05/registries/s4r8/ERRATA_8.txt`。本轮自身的勘误写到 `checkpoints/p05/ERRATA_S3R5.txt`（编号 ES3R5-n）。
- **U289**：自检范围（不是修后验证）包括：
  - (A) 编译：F4 的 dbg/san/plain 三种库，告警与 F3 对比，不得有新增告警；
  - (B) diff：F3 到 F4 的 `S4/` diff 只涉及 S4.cpp 的 1760–1774 段，并生成行号映射表 LINEMAP_F3_F4（1774 之后的行号偏移量）；
  - (C) 无注入对照：init-F4-dbg 和 init-F4-san 各跑 3 个组合，期望 rc 0，san 报告数为 0；
  - (D) 每个修复位点（1763、1764、1765）× 3 个组合，在 dbg 下单遍运行，只记录事实（rc1、rc2、signal、hit、post_call1_solution、crash_call），不判 MATCH，不写入任何 VERDICT 表。
  
  (D) 的结果不得称为"已修复"或"已验证"。
- **U290**：P05-S4 R9 的预注册不在本轮冻结。本轮只输出 `R9_INPUTS_S3R5.tsv`，列出 R9 需要的全部输入：F4 驱动和库的 sha256、F4 上的 K、F4 行号映射、需要按行号重写的 gdb 脚本清单（检查 `r6c_state_bt_r8m2d.gdb` 等脚本是否使用行号断点）。

## 4. 步骤
- **S-A 开工门禁**：用 `gate_s3r5.sh start` 写 `GATE_S3R5_start.txt`，内容包括：
  - HEAD、`HEAD:S4`、判定器 sha256、`git status --short`；
  - `/tmp` 顶层只读快照（条目数和 sha256）；
  - r8m2e registries 的 `SHA256SUMS.txt` 逐项比对；
  - `__pycache__` 与 `.o` 的基线清单（含 mtime）。
  
  RULINGS 和 ERRATA 的追加必须在 start 门禁通过**之后**进行。
- **S-B 裁决与勘误**：追加 U283–U290；写 E8-116 至 E8-119；建 `ERRATA_S3R5.txt`。
- **S-C 修复前源码确认**：写 `PRE_FIX_SOURCE_S3R5.md`，内容包括：
  - F3 中 1755–1775 行原文；
  - H-3 中 7 个调用点各自对 InitSolution 返回值的处理（行号加原文），确认每处都检查了非零返回；
  - 全仓 `S->solution` / `->solution` 的读写点，判断有没有哪处假设"InitSolution 失败后 solution 非空"，结论标 [源码]。
  
  然后做记录提交 (i)。
- **S-D 修复**：用 edit 工具按 U284 修改，记录修改前后该段的 sha256。运行 `git diff --stat -- S4/`，确认只改了 `S4/S4.cpp` 一个文件。做 F4 提交 (ii)，记录 F4 提交号和 `git rev-parse HEAD:S4`。
- **S-E 构建**：用 `build_s3r5.py` 从 F4 提交导出树到 `$EV/trees/F4/`（git archive 经管道传给 tarfile），按 U286 构建，写 `BUILD_S3R5.tsv`（sha256、命令、rc、告警数），以及 `WARN_DIFF_F3_F4_S3R5.txt`。
- **S-F 自检 A/B**：写 `DIFF_F3_F4_S3R5.txt` 和 `LINEMAP_F3_F4_S3R5.tsv`。
- **S-G 自检 C**：写 `probe/noinj_control_s3r5.txt`。
- **S-H 映射**：用 `map_k_s3r5.py`。dbg 和 san 的 `init:K` 在 malloc 处下断点，`aligned:K` 在 `__wrap_malloc_aligned` 处下断点，每次都打 `bt 4`，按 caller 源码行找出 1763/1764/1765 各是第几次。3 个组合 × 3 个位点 × 3 种驱动。结果写 `K_MAP_F4_S3R5.tsv` 和 `K_MAP_RAW_S3R5.txt`，并与 F3 的 K 并列对比。
- **S-I 自检 D**：用 `selfcheck_d_s3r5.py`，写 `SELFCHECK_D_S3R5.tsv`，只写事实。
- **S-J R9 输入**：写 `R9_INPUTS_S3R5.tsv`（U290）。另写 `REGRESSION_PLAN_F4_S3R5.tsv`，在 r8m2e 清单的基础上：
  - 所有 F4 行的 K 改为"取 `K_MAP_F4_S3R5.tsv`"；
  - F4 行的期望写为：rc1=1、rc2=0、post_call1_solution=NULL、crash_call=NONE，调用 2 的输出与无注入对照中对应调用逐字节一致（I6）；
  - 改正 H-5(f) 指出的措辞；
  - 追加 M2 健康 175 点在 F4 上回归，以及 M1 在 F3 与 F4 之间等价对比两项（只登记）；
  - 保留两项收口测试（`make test` 在 `$EV` 导出树上运行；Python/Lua E2E 并入 M3）。
- **S-K 收尾**：
  - 按 U287 改 `AGENTS.md` 第 6 节；
  - 更新 STATE.md（不超过 8192 字节）：当前树改为 F4，RP-R8-M2c-1/1b 状态写"S3R5 已修改源码 [源码]，待 R9 修后验证"；
  - 写报告；
  - 把小表复制到 registries，写 `SHA256SUMS.txt`，逐个比对；
  - 证据目录写 `SHA256SUMS.txt`（`safe_run.log` 按 U288 的新规则处理）；
  - 运行 `gate_s3r5.sh end`，期望 `HEAD:S4` = F4；
  - 收尾提交 (iii)，信息末尾写 `awaiting user review`。提交前核对 `git status --short`；报告末尾附上 `git log -3 --oneline`、`git log -1` 和 `git status --short`。

## 5. 硬停止条件
1. 开工门禁任一项不符。
2. S-C 发现有调用方依赖"失败后 solution 非空"，或者有调用方不检查返回值并在之后解引用 `S->solution`。此时停下报告，不修改。
3. F3 到 F4 的 diff 超出 `S4/S4.cpp` 的 1760–1774 段，或者 F4 提交包含 `S4/S4.cpp` 以外的文件。
4. F4 的任一构建失败，或者相对 F3 出现新增告警。
5. 无注入对照出现 rc≠0 或 san 报告。
6. 映射中某组合 × 位点找不到唯一的 caller 行。
7. 任何无法解释的越界写入，或写入了其他轮次的证据目录。

自检 D 的结果不符合 U284 的预期，不算停止条件：如实记录，进入"需用户裁决"。

## 6. 报告要求
- 报告分为：门禁、裁决与勘误、修复前源码确认、修复 diff 全文、F4 提交和树哈希、构建与告警、自检 A–D、K 映射对比、R9 输入、事件两张表、需用户裁决。
- 措辞：
  - 自检 D 写成"自检事实：<点号>，rc1=…，rc2=…"；不得写"已修复""已验证""修复成功"；
  - 不写"100%""完全证实"等强化词；
  - REPORTED_FAILURE 只表示返回码非零；
  - B 列不是修复证据。
- "需用户裁决"一节只列规划者无法从仓库查到的事项，能查到的直接给出来源行号。
- 结尾写"本轮已完成/未完成 S3R5 范围，等待用户审核"。
