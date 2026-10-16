# P05-S4 R8 M2e（r8m2e）任务书：-FA 装置纠偏（malloc_aligned 注入）、v5/v6 增量正式两遍、合并总表 v6、事件补披露、F4 回归清单更正

## 0. 身份与边界
- 本轮是 P05-S4 的子轮次 R8 M2e，轮次标识 `r8m2e`，证据目录 `p05-s4r8/m2e`，小表目录 `checkpoints/p05/registries/s4r8/M2/r8m2e/`。不得宣布任何阶段完成，不得询问是否签收。
- 开工先读：`AGENTS.md` → `checkpoints/p05/STATE.md` → 本任务书 → `checkpoints/p05/P05_S4R8_M2D_REPORT.md`。把本任务书原文存为 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M2e.md`。M2d 任务书原文缺失，在报告中记一笔"待用户提供后补存"，不要自行重构。
- 开工门禁：HEAD = `be00bf20484d76e84f6ddfcb228032dadd8dcc3c`；`git rev-parse HEAD:S4` = `6cff923a02baf19e01966b2339755cbf3a5deeef`；`testing/d003/judge_d003.py` sha256 = `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`；`git status --short` 为空。任一不符就停下报告。
- 不改 `S4/`。不改任何已提交的脚本和表（含 r8m2d 的全部产物）。需要时把历史脚本复制成带 `r8m2e` 后缀的新脚本：EV 常量改成 m2e，REPO 行换成标准首段（不含 `/dev/null`），diff 中这两处变化属于预期。
- 本轮不开始 S3R5，也不开始 M3。

## 1. 写入与执行纪律（硬规则，同 M2c/M2d）
1. 每条含写入的命令开头先执行：
   `REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2e; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`
   然后一律经 `sh testing/d003/safe_run.sh p05-s4r8/m2e -- <命令>` 运行。
2. 写入目标只能以 `$EV/`、`$REPO/testing/d003/`、`$REPO/checkpoints/p05/` 开头。任何以 `/` 开头且不在 `$REPO` 下的路径都不得出现（含 `/tmp` 及各种占位路径）。
3. 内联命令中不得出现 `>` 字符（含 `2>&1`）。需要输出的核对一律写成脚本，经 safe_run 运行。含写入的命令不得用 `2>/dev/null`。核对路径只用 `ls -d` 或 `test -e`。不做沙箱探测，不做反例测试。
4. 新脚本第一行用标准首段。运行前用 grep 工具查禁止项：`/tmp`、`2>/dev/null`、计划或命令里出现 `$EV` 字面量。查禁止项的正则不得命中标准首段里的 `"$EV/tmp"`，也不得命中 Python 的 `1 << 20`。草稿查出问题后改正不算违规，违规以实际执行为准。
5. Python 一律用 `python3 -I -B`。start 门禁记录 `__pycache__`、`.o` 的基线清单和 mtime，end 门禁只判本轮新增的。
6. **每一次 `rm`、`mv`、重跑覆盖（含 posctrl、copy、门禁重跑）都必须写进事件表二**，写明 safe_run.log 行号。生成的脚本不得删除，不得改名；名字起错就新建正确名字的文件，旧文件留着并披露。
7. **探针输出必须落盘。** 任何诊断或探针脚本的输出都要写到 `$EV/probe/<脚本名>.txt` 并进 SHA256SUMS，不得只打到屏幕。冻结预注册之前跑过的探针，结果必须在 PREREG 的 basis 列里引用。
8. 长输出一律加 `head`/`tail`，或用 read 工具的 offset/limit。
9. 停止策略：只有真实的基线异常、无法解释的越界改动、或第 5 节列出的硬停止条件才停。合法的中间产物让工作区非空不是停止理由。
10. 本轮所有新增脚本和新表都带 `r8m2e` 后缀；registries 复制时不改名。

## 2. 输入事实（规划者已核实，直接使用，不要再列为"需用户裁决"）
- G-1：`S4_FAIL_ALLOC_AT` 只在 `S4_Simulation_Clone` 的作用域里打开：`S4/S4.cpp:65-71` 定义开关，`S4.cpp:733` 是 `S4FailAllocScopeGuard`。`driver_r6b_state.cpp` 不调用 Clone，因此 r8m2d 的 3 个 `-FA` 行不会被注入。这是 r8m2d 任务书 U273 的依据错误（规划者引入），不是执行者的错误。
- G-2：`-FA` 行的 `exp_hit=1` 本来就测不到：驱动只在 `s4fmm_inject_requested()` 为真（即设置了 `S4FMM_INJECT`）时才打印 `S4FMM HITCOUNT`（`driver_r6b_state.cpp:260-262`）。另外 `-FA` 行的 `k_fail=9` 是从 1765 行照抄的。
- G-3：在 `init-F3-san` 下，`S4_malloc`（`S4.cpp:107-113`）调用 `malloc_aligned`，后者在 ASAN 下走 `posix_memalign`（`S4/numalloc.c:59-62`），不经过 `--wrap=malloc`。`--wrap=_Z9S4_mallocm` 拦不到 1764，因为那是 `S4.cpp` 内部的直接调用。而 `lib_F3_san/objs/S4.o` 对 `malloc_aligned` 是外部引用（`nm` 显示 `U malloc_aligned`），定义在 `numalloc.o`（`T malloc_aligned`）。因此链接时加 `-Wl,--wrap=malloc_aligned` 就能拦截 `S4.cpp` 里所有 `S4_malloc` 的底层分配（`rcwa.o` 也是外部引用，同样会被计数）。
- G-4：规划者做过一次只读 gdb 探测（无 dump 目录，仓库内无写入）：在 main 处 `set var s4_fail_alloc_armed = 1` 后，`S4_FAIL_ALLOC_AT=3` 触发于 `S4_malloc(size=960)`（fft-ng5 下 1764 `ab` 的大小）。这条路不采用：没法做成对的不带 gdb 运行，而且要改私有状态。只作为 K 的旁证。
- G-5：r8m2d 冒烟 28 行 × 2 遍：25 MATCH、3 MISMATCH（`-FA`）。S-G 正式两遍没有跑。`M2_CONSOLIDATED_R8_M2d.tsv` 中 28 个 `r8m2d_delta` 行的判定来自冒烟，但没有标注来源。
- G-6：r8m2d 未披露的事件（见 `checkpoints/p05/evidence/p05-s4r8/m2d/safe_run.log`）：
  - 第 4、5 行：两个探针 `test_fail_alloc_r8m2d.py`、`test_gdb_arm_r8m2d.py` 在冻结（13:33:30Z）之前运行，输出没有落盘；
  - posctrl 运行 4 次（13:37–13:46）；
  - 第 18 行：`mv generate_m2d_summary_tables.py generate_summary_tables_r8m2d.py`；
  - 第 19 行：`rm -f .../GATE_R8_M2d_end.txt`，之后重跑 end 门禁；
  - copy_registries 运行 3 次。
  
  报告表二把"run_smoke 冒烟运行"列为事件，属于误列。
- G-7：`REGRESSION_PLAN_F4_R8_M2d.tsv` 中 9 个 `-B-dbg` 行的 `f4_driver` 写成了 `init-F4-dbg`，应为 `init-B-dbg`（仅基线，非修复证据）。清单里没有 1764-san 的可执行注入方式。
- G-8：在 dbg 下，1764 的实测崩溃帧已确认：#0 `__memset_avx2_unaligned_erms`，#1 `S4.cpp:1995`，#4 `driver_r6b_state.cpp:227`（见 `m2d/smoke/run/pass1/SOLN-1764-fft-ng5-F3-dbg-C/gdb.log` 第 80–84 行）。ASAN 下 memset 会被拦截，栈顶可能是 `__asan_memset`、`__interceptor_memset` 或 `___interceptor_memset`。

## 3. 用户裁决（追加到 `checkpoints/p05/registries/RULINGS.tsv`）
- **U276**：r8m2d 的执行链 v5、事实列与判定器 v5、映射表、28 行冒烟中的 25 个 MATCH 予以采信。3 个 `-FA` 的 MISMATCH 保持原记录，不改任何 r8m2d 文件；分诊改为"装置错误（任务书 U273 依据错误：S4_FAIL_ALLOC_AT 仅在 Clone 作用域打开；HITCOUNT 不可观测；k_fail 抄错）"，写入 `TRIAGE_R8_M2e.tsv` 与 ERRATA（E8-115）。
- **U277**：新增注入器 `testing/d003/stage_s4/inject_r8m2e_aligned.cpp`。从 `inject_s3r4_init.cpp` 复制，保留其全部 wrap 转发；新增 `__wrap_malloc_aligned` / `__real_malloc_aligned` 与请求格式 `S4FMM_INJECT=aligned:K`（第 K 次 `malloc_aligned` 返回 NULL，每个进程最多命中一次，计入 `n_hits`，stderr 打印 `S4FMM HIT ...`）。新驱动 `init-F3-san-AL`：源文件同 `init-F3-san`，库为现有 san 库（sha256 `2775b9b2c279…`，不重编），链接参数为 `WRAP_INIT` 加 `-Wl,--wrap=malloc_aligned`。构建脚本 `build_r8m2e.py` 记录驱动 sha256。
- **U278**：K 必须由映射确定，不得假设：用 gdb 在 `__wrap_malloc_aligned` 下断点，每次打 `bt 4`，按 caller 源码行确认 `S4.cpp:1764` 是第几次，3 个组合（closed2d-ng1、fft-ng5、kottke-ng5）各自确认，写 `ALIGNED_MAP_R8_M2e.tsv`，同时记 size（期望与 `S4MALLOC_MAP_R8_M2d.tsv` 中 1764 行的 size 一致）。任一组合找不到唯一的 1764，或 size 不一致，即为硬停止。
- **U279**：v6 增量预注册 3 行 `SOLN-1764-<combo>-F3-san-AL`，原 `-FA` 行标 `SUPERSEDED_BY`。期望值：
  - `exp_rc1`、`exp_rc2`、`exp_rc3` 写 `-`；`exp_signal=0`；`exp_hit=1`；`exp_class=SAN_CRASH`；`exp_san=1`；
  - `exp_crash_call=2`；`exp_crash_site=S4.cpp:1995`（来源 G-8，状态 INFLUENCED）；`exp_post_call1_solution=-`；
  - `k_fail` 用映射得到的 K。
  
  `crash_site` 提取器要把 G-8 列出的 ASAN 拦截帧当作非 S4 帧跳过，这一改动写入新的 `facts_m2_r8m2e.py`，并加阳性对照。
- **U280**：正式两遍的对象 = v5 中 25 个非 `-FA` 行 + v6 的 3 个 `-AL` 行，共 28 行。先对 3 个 `-AL` 行做冒烟（2 遍）并过冒烟门禁 v2（7 项），然后在全新目录 `$EV/formal/` 跑 28 行 × 2 遍。合并总表 v6 中这 28 行的判定只采用正式运行结果，并用新列 `verdict_source ∈ {formal_r8m2b, formal_r8m2c, formal_r8m2e, smoke_r8m2d}` 标明来源；有效行中不得出现 `smoke_*`。
- **U281**：RP-R8-M2c-1b 的 F_CONFIRMED 维持；台账证据列补上正式运行的点号。K-1 维持 U274 关闭。
- **U282**：r8m2d 的未披露事件（G-6）在本轮报告中补披露进表二，标注"r8m2d 遗漏，r8m2e 补"。r8m2d 报告不改。

## 4. 步骤
- **S-A 门禁**：`gate_r8m2e.sh start` 写 `GATE_R8_M2e_start.txt`，内容包括：
  - HEAD、`HEAD:S4`、判定器 sha256、`git status --short`；
  - `/tmp` 顶层只读快照（条目数与 sha256）；
  - r8m2d registries 中 `SHA256SUMS.txt` 逐项比对；
  - `__pycache__` 与 `.o` 的基线清单（含 mtime）。
- **S-B 分诊与勘误**：写 `TRIAGE_R8_M2e.tsv`（3 个 `-FA` 行，按 U276），在 `ERRATA_R8_M2e.txt` 写 E8-115，并追加到 `checkpoints/p05/registries/s4r8/ERRATA_8.txt`。
- **S-C 装置**：
  - 写注入器与构建脚本，构建 `init-F3-san-AL`，输出 `BUILD_R8_M2e.tsv`（sha256、命令、rc）。
  - 无注入运行一次（3 个组合）作为装置对照：期望 rc 0，无 `S4FMM HIT`，HITCOUNT 不出现或为 0（因未设 `S4FMM_INJECT`）。如果出现 ASAN 报告，属于硬停止。
- **S-D 映射**：按 U278 写 `ALIGNED_MAP_R8_M2e.tsv` 与 `ALIGNED_MAP_RAW_R8_M2e.txt`。
- **S-E 预注册 v6**：生成 `PREREG_M2_DELTA_R8_M2e.tsv`（3 行），附 `.sha256` 与 `_TIMESTAMP_UTC.txt`。再写 `PREREG_EFFECTIVE_FORMAL_R8_M2e.tsv`，列出 28 行（25 行 v5 原样转录 + 3 行 v6），并逐行核对与源表逐字节一致（v6 行除外）。冻结之后不得修改。
- **S-F 阳性对照**：`posctrl_m2_r8m2e.py` 调用正式脚本。要求：
  - r8m2d 的 41 项全部回归通过；
  - 新增断言至少覆盖：ASAN 拦截帧的跳过、`aligned:K` 请求解析、HITCOUNT 解析、`verdict_source` 列、有效行不允许 `smoke_*`、合并总表合计断言。
  
  只运行一次；如需重跑，必须进表二。
- **S-G 冒烟**：3 个 `-AL` 行 × 2 遍，写 `$EV/smoke/` 并过 7 项门禁。出现非 MATCH 时先写入分诊表。
- **S-H 正式运行**：`run_formal_r8m2e.py`，28 行 × 2 遍，写入 `$EV/formal/`；目录非空就拒绝运行。产出 `FACTS_pass1/2`、`VERDICT_R8_M2e.tsv`、`SUMMARY_R8_M2e.txt`。FLAKY 和 GDB_DIVERGENT 单独计数。
- **S-I 合并总表 v6**：`M2_CONSOLIDATED_R8_M2e.tsv` 与 `M2_F3_STATUS_R8_M2e.tsv`。断言：
  - 总行数 = 174 + 54 + 28 + 3 = 259；
  - SUPERSEDED = 26 + 28 + 3 = 57，其中第二个 28 是 r8m2d 冒烟的 28 行，它们全部由正式行或 `-AL` 行替代；如果计数方式不同，必须列式说明；
  - 有效行 = 202；
  - 各类别之和 = 202；
  - 有效行中 `verdict_source` 没有 `smoke_*`。
  
  三条断言都要写成脚本输出。
- **S-J F4 回归清单更正**：写 `REGRESSION_PLAN_F4_R8_M2e.tsv`：
  - 修正 G-7（B 行驱动 = `init-B-dbg`，标 BASELINE_ONLY）；
  - 1764-san 改为 `init-F4-san-AL`（同注入器，库换成 F4 san 库）、`S4FMM_INJECT=aligned:K`，并注明 F4 上 K 需重新映射；
  - 另列 S3R5 收口时要做的两项（只登记，不执行）：冻结树上 `make test` 相对 B 无新增失败；Python/Lua 公共 API 的"失败→可见报错→重试恢复"E2E。
- **S-K 收尾**：
  - 红点台账追加 `RED_POINTS_LEDGER_APPEND_R8_M2e.tsv`；
  - 更新 STATE.md（不超过 8192 字节）；
  - 写报告 `checkpoints/p05/P05_S4R8_M2E_REPORT.md`；
  - 把小表复制到 registries 并写 `SHA256SUMS.txt`，逐个比对 sha256；
  - 证据目录写 `SHA256SUMS.txt`；
  - 跑 `gate_r8m2e.sh end`；
  - 提交（信息末尾写 `awaiting user review`），提交前核对 `git status --short`；报告末尾附 `git log -1` 与 `git status --short`。

## 5. 硬停止条件
1. 开工门禁任一项不符。
2. 映射中某组合找不到唯一的 1764，或 size 不一致（U278）。
3. 无注入对照出现 ASAN 报告或 rc≠0。
4. 冒烟中出现被归为"预注册错误"的非 MATCH（按 U270，不得自行改期望）。
5. 正式运行中有效行出现 FLAKY 或 GDB_DIVERGENT。
6. 任何对 `S4/` 的改动，或无法解释的越界写入。

## 6. 报告要求
- "需用户裁决"一节只列规划者确实无法从仓库查到的事项。能查到的请直接给出来源行号。
- 措辞：REPORTED_FAILURE 只表示返回码非零。F3 上的崩溃表征不是修复证据，B 列不是修复证据。不写"100% 证实""完全证实"之类的强化词，写"实测：<点号>，<帧>"。
- 结尾写"本轮已完成/未完成 R8 M2e 范围，等待用户审核"。
