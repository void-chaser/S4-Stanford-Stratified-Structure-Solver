# P05-S4 R8 M2c（r8m2c）任务书：红点分诊、预注册改正（v4 增量）、1763 缺陷表征、判定器 v4、增量两遍运行

## 0. 身份与边界
- 本轮是 P05-S4 的子轮次 R8 M2c，轮次标识 `r8m2c`，证据目录 `p05-s4r8/m2c`。不得宣布任何阶段完成，不得询问是否签收。
- 开工先读：`AGENTS.md` → `checkpoints/p05/STATE.md` → 本任务书 → `checkpoints/p05/P05_S4R8_M2B_REPORT.md`。把本任务书原文存为 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M2c.md`。
- 开工门禁：HEAD = `8f76bb1aea2a7565452dc5958ffca719435feb95`；`git rev-parse HEAD:S4` = `6cff923a02baf19e01966b2339755cbf3a5deeef`；`testing/d003/judge_d003.py` sha256 = `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`；`git status --short` 为空。任一不符就停下报告。
- 不改 `S4/`。不改任何已提交脚本和表（含 r8m2b 的全部产物）。不直接运行已提交的历史脚本；需要时复制成带 `r8m2c` 后缀的新脚本，并改写其中的 EV 常量。
- M3 不开始。

## 1. 写入与执行纪律（硬规则）
1. 每条含写入的命令开头先执行：
   `REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2c; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`
   然后一律经 `sh testing/d003/safe_run.sh p05-s4r8/m2c -- <命令>` 运行。
2. 写入目标只能以 `$EV/`、`$REPO/testing/d003/`、`$REPO/checkpoints/p05/` 开头。任何以 `/` 开头且不在 `$REPO` 下的路径都不得出现（含 `/tmp` 及各种占位路径）。
3. 内联命令中不得出现 `>` 字符（含 `2>&1`）。需要输出的核对一律写成脚本，经 safe_run 运行。含写入的命令不得用 `2>/dev/null`。核对路径只用 `ls -d` 或 `test -e`。不做沙箱探测或反例测试。
4. 新脚本第一行用上面的标准首段（不含 `/dev/null`）。运行前用 grep 工具查禁止项：`/tmp`、`2>/dev/null`、`$EV` 字面量出现在计划或命令里。查禁止项的正则不得命中标准首段里的 `"$EV/tmp"`，也不得命中 Python 的 `1 << 20`。草稿查出问题后改正不算违规，违规以实际执行为准。
5. Python 一律用 `python3 -I -B`。start 门禁要记录 `__pycache__`、`.o` 的基线清单和 mtime，end 门禁只判本轮新增的。**本轮任何删除（`rm`）、移动（`mv`）、重跑覆盖都必须写进事件表。生成的脚本不得删除。**
6. 长输出一律加 `head`/`tail`，或用 read 工具的 offset/limit。
7. 停止策略：只有真实的基线异常、无法解释的越界改动、或本任务书明确列出的硬停止条件才停。合法的中间产物使工作区非空不是停止理由。
8. 本轮所有新增脚本和新表都带 `r8m2c` 后缀。registries 复制时不改名。

## 2. 输入事实（规划者已核实，直接使用，不要再列为"需用户裁决"）
- r8m2b 共 174 点：148 MATCH，26 MISMATCH。红点清单见 `checkpoints/p05/registries/s4r8/M2/r8m2b/RED_POINTS_R8_M2b.tsv`。
- **F1（rc 抄错，9 点）**：M2-01-01..06-F3、M2-03-REP-INIT-01..03-F3。期望来源是 `checkpoints/p05/registries/s4r8/M1a/ADDITIONS_MAPPING_22_R8_M1a6.tsv` 第 1–6 行，`expected_rc1=1`（RP-S3R4-1/U95：806 与 1729 失败返回 1）。v3 写成了 20。
- **F2（G6 env 抄错，10 点）**：v3 用的 env 中，`clm:`、`acf:` 前缀注入器不认识（只认 `alloc:`、`kottke_alloc:`、`linearsolve:`、`linearsolve_null2:` 等，见 `testing/d003/stage_s4/inject_r4_plan.cpp`），结果 hit=0。正确的 env 取自 `checkpoints/p05/registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv` 的 `R4-*-F-F3` 行：
  | v3 id | 历史点 | 正确 env | 期望 |
  |---|---|---|---|
  | G6-01 | R4-CLM1-F | FMM_MODE=fft;S4FMM_INJECT=alloc:21:1;S4FMM_NG=9 | rc1 20, rc2 0, hit 1, REPORTED_FAILURE |
  | G6-03 | R4-CL01-F | FMM_MODE=closed1d;S4FMM_INJECT=linearsolve_null2:134:1;S4FMM_NG=9 | 同上 |
  | G6-04 | R4-AL18-F | FMM_MODE=kottke;S4FMM_INJECT=kottke_alloc:31:1;S4FMM_NG=9 | 同上 |
  | G6-05 | R4-ACF1-F | FMM_MODE=jones;S4FMM_INJECT=alloc:25:1;S4FMM_NG=9 | 同上 |
  | G6-06 | R4-CLM3-F | FMM_MODE=fft;S4FMM_INJECT=alloc:23:1;S4FMM_NG=9 | 同上 |
  G6-02（R4-SI01-F）在 v3 中用 NG=5 跑出了 MATCH，不重做；它的 NG 与历史不一致，只在溯源表里记一笔。
- **F3（vl 原生失败，3 点）**：M2-07-CTRL-vl-ng2/3/4-F3 在预注册里自己写着 `n_G_actual=1`（方格晶格把 NG 截到 1），与 vl-ng1 相同，都是原生 rc 20。
- **F4（假设未复现，1 点）**：M2-06-01-F3（nan-F3，`linearsolve_nanbuf:244:1`）。stderr 中有 `Layer eigensystem returned info = 10`，rc1=20。K-1 所说的静默吞没在该装置上没有出现。
- **F5（S4 真缺陷，3 点）**：M2-03-REP-INIT-04..06-F3（init-F3-san）。san 驱动的外部 malloc 序号与 dbg 不同：closed2d-ng1 的 dbg 中 k=7 是 n=4 的 parent，san 中 k=7 是 n=16 的 `Solution_`。注入后 `S4.cpp:1763` 返回 NULL，1764 行先解引用（1766 才判空），ASAN 报 `SEGV … Simulation_InitSolution S4/S4.cpp:1764`，rc=1，rc1 缺失，被 classify 为 INVALID。B 树同样的代码在 1754–1757 行。另外 [源码]：1764（`ab`，S4_malloc）或 1765（`solved`）失败时返回 1，但 `S->solution` 留着非 NULL；重试时 `Simulation_GetLayerSolution`（约 1798–1815 行）跳过 InitSolution，直接用 NULL 的 `ab`/`solved`。此项**未验证**。
- **F6（判定器宽松）**：`verdict_m2_r8m2b.py:297-310` 只在实测为 VIOLATED 或 UNJUDGED 时报错。期望 HOLD、实测 N/A 被当成通过。受影响：M2-01-01..06 的 I1/I2（InitSolution 路径失败没有失败层），以及 M2-05-P0-F3 的 I2（失败层是 0，没有保留层）。
- **F7（报告与 ERRATA 错误）**：
  - M2-10 实测 `m210_hits=2432`，报告写成了 2362。
  - 三张预注册的冻结时间按 `*_TIMESTAMP_UTC.txt` 应为 06:21:23Z、06:21:23Z、06:34:45Z，报告写的 06:50:52Z 和 07:11:53Z 不符。
  - E8-106 写的状态分析器 sha `89f00f0e6ca4…` 有误，实际是 `89f00f0ef91b927066bad059b58073a47cbf34594d65a35ee7bdddb576a6ff1f`。
- **F8（未披露事件）**：见 `checkpoints/p05/evidence/p05-s4r8/m2b/safe_run.log` 第 15–21 行。
  - `GATE_R8_M2b_end_R1.txt` FAILS=1（本轮产生了 `stage_s4/__pycache__`）
  - `rm -rf testing/d003/stage_s4/__pycache__`
  - `mv` 门禁文件
  - `rm -f testing/d003/stage_s4/postcommit_r8m2b.py`
- **F9（冒烟门禁缺项）**：缺"注入行 hit≥1"检查。G6 在冒烟时已经 hit=0。

## 3. 用户裁决（追加到 `checkpoints/p05/registries/RULINGS.tsv`）
- **U261**：r8m2b 的执行链与 148 个 MATCH 予以采信。26 个 MISMATCH 保持原记录，不改任何 r8m2b 文件。分诊结果按第 2 节 F1–F5 执行，写入 TRIAGE 表。
- **U262**：F1 和 F2 属于预注册转录错误，正确来源早于运行就已存在并提交。允许在 v4 增量表中按来源改正，用新 id（原 id 加 `-C` 后缀），状态写 INFLUENCED。原 v3 行和它的 MISMATCH 保留，并标 `SUPERSEDED_BY`。这不算"通过改期望消除 MISMATCH"，而是有来源行号的转录更正；每一行都必须给出来源文件和行号。
- **U263**：F3 的 vl-ng2/3/4 在 v4 中新建 `-C` 行，`class_rule=NATIVE_FAIL_CONTROL`（与 U255 相同：rc1=20、rc2=20、信号 0、hit=0、classify==INVALID）。依据是预注册自身的 `n_G_actual=1` 加 M0 的 vl NG=1 rc 20。
- **U264**：M2-06-01 保持 MISMATCH，红点台账写"K-1 静默吞没在 nan-F3 model 1 上未复现，F3 报 rc 20"。增设记录型诊断行（RECORD_ONLY），用 gdb 定位是哪一处 `return 20`、NaN 是否到达本征求解。K-1 是否关闭由用户在 M2c 后裁决。
- **U265**：F5 登记为新红点 **RP-R8-M2c-1**（`S4.cpp:1763–1766` 的 Solution_ 分配先解引用后判空），附带 [源码] 子项 RP-R8-M2c-1b（ab/solved 失败后 solution 残留）。本轮只做表征，不修。修不修（S3R5→F4，或转 S5）在 M2c 之后由用户裁决。注意 S2R4 曾把 1754/1756 划在范围外（用户确认）；本裁决不改变这一划分，只登记观察。
- **U266**：REP-INIT-04..06 的本意是"1729 parent 分配在 san 下复现"。v4 按 san 驱动的实测 malloc 映射重新确定 K，新建 `-C` 行。映射按 caller 源码行确认，不按序号假设。
- **U267**：判定器 v4 规则：exp_I* ∈ {HOLD, VIOLATED, N/A} 时与实测严格相等，不等即 MISMATCH；exp 为 `-` 或 UNOBSERVED 时不判。用 v4 离线重判 r8m2b 的 174 点（只重判，不重跑），结果单独成表，不覆盖 r8m2b。
- **U268**：InitSolution 路径失败（M2-01-01..06-C、REP-INIT-*-C）的 exp_I1/exp_I2 写 N/A，另设断言 `INIT_CLEAN`：失败调用之后，所有层 modes_null=1、solution null、cache_count 0。M2-05-P0-F3-C 的 exp_I2 写 N/A，依据是失败层为 0、没有保留层（R6c 规则）。这些都是 INFLUENCED 更正，必须写 ERRATA。
- **U269**：sanitizer 行增加事实列 `san_crash`：san 日志出现 `ERROR: AddressSanitizer: SEGV` 或 `ABORTING` 时记 1。新增派生类别 `SAN_CRASH`，它与 judge_d003.classify 的输出并列，不替换后者。
- **U270**：冒烟门禁 v2 新增两项：(a) `exp_hit≥1` 的行实测 hit≥1；(b) 冒烟中每个非 MATCH 都必须先写入分诊表，归类为 预注册错误 / 装置错误 / 真实行为，才能进入正式运行。归为预注册错误的不得在本轮自行改期望：要么停下报告，要么按已有裁决处理。

## 4. ERRATA（追加到 `checkpoints/p05/registries/s4r8/ERRATA_8.txt`，从 E8-109 起，只追加）
- E8-109：F1 和 F2 的转录错误（逐行列出 v3 值、正确值、来源文件:行号）。
- E8-110：F7 的三处更正（2432；冻结时间；E8-106 的 sha）。
- E8-111：F8 未披露的事件（逐条：命令、是否落盘、影响）。
- E8-112：F6 判定器宽松，以及 U268 的 exp_I 更正。
- E8-113：F9 冒烟门禁缺项。

## 5. 工作步骤

### S-A 门禁、裁决与分诊
1. start 门禁写入 `GATE_R8_M2c_start.txt`：HEAD、HEAD:S4、判定器 sha、`/tmp` 顶层条目数与 sha256、`__pycache__`/`.o` 基线清单与 mtime。
2. 追加 U261–U270 和 E8-109–E8-113。
3. 写 `TRIAGE_R8_M2c.tsv`，26 行，列为：`point_id, r8m2b_verdict, category(F1..F5), evidence(文件:行号或日志行), action(v4 行 id / 诊断行 / 仅登记)`。

### S-B 全量溯源审计（防止还有其他抄错）
写 `SOURCE_TRACE_R8_M2c.tsv`：对 v3 的 150 行，加上 SANREF 19 行和 WIN64 5 行，把 `env`、`exp_rc1`、`exp_rc2`、`exp_hit`、`exp_class` 逐列追溯到来源表的行号（M1、R6c、R7、M0 等表）。每格判为 TRACED_EQUAL、TRACED_DIFF 或 NO_SOURCE。
- 除 F1–F3 以外新发现的 TRACED_DIFF，**不得自行改正**，列入"新增待裁决"表，交用户。
- 断言：审计行数 = 174。

### S-C malloc 映射与 1763 探针装置
1. 写一个新的 gdb 映射脚本 `malloc_map_r8m2c.gdb`：在 `__wrap_malloc` 的外部计数分支，记录 k、n 和 caller 对应的源码行（`info line *caller`）。对以下 9 个组合做计数运行（不注入，INFLUENCED），输出 `MALLOC_MAP_R8_M2c.tsv`：
   - 驱动：init-F3-dbg、init-F3-san、init-B-dbg
   - 组合：closed2d-ng1、fft-ng5、kottke-ng5
   - 映射表必须标出 1729 parent、1763 Solution_、1764 ab（S4_malloc 内部那次 malloc）、1765 solved 各自对应的 k。B 树上对应 1754–1756 行。
2. init-B-dbg：如果没有现成驱动，在 `$EV/build/` 新建。源文件、注入文件、宏和 wrap 都与 init-F3-dbg 相同，只把库换成 B 的 `-O0 -g` 库（用 r6bstate-B-dbg 所用的那个，按 build 记录核对 sha）。写 `BUILD_R8_M2c.tsv`。B 树只作基线，不是修复证据。

### S-D 执行链 v4
新增以下脚本：
- `facts_m2_r8m2c.py`：在 v3 基础上增加 `san_crash` 列；增加从 gdb.log 的 R6BSTATE 推出的 `init_clean`（失败调用之后，所有层 modes_null=1、solution null、cache_count 0）。
- `verdict_m2_r8m2c.py`：
  - 实现 U267 的严格比对；
  - 实现 `INIT_CLEAN`、`SAN_CRASH`、`NATIVE_FAIL_CONTROL`；
  - 优先级：GDB_DIVERGENT > MISMATCH > FLAKY > UNJUDGED_MISSING > UNJUDGED_BY_DESIGN > MATCH；
  - 支持 `SUPERSEDED_BY` 列；
  - 合计断言用参数传入。
- `smoke_gate_r8m2c.py`：在原 5 项门禁之外，加上 U270 的 (a)(b)。
- `posctrl_m2_r8m2c.py`：调用正式脚本，输出路径用参数传入。在 r8m2b 的 27 例之外新增：
  - P1：exp HOLD、实测 N/A → MISMATCH
  - P2：exp N/A、实测 HOLD → MISMATCH
  - P3：ASAN SEGV 日志 → `san_crash=1`、SAN_CRASH
  - P4：注入行 hit=0 → 冒烟门禁 FAIL
  - P5：INIT_CLEAN 断言不成立 → MISMATCH
  - P6：`SUPERSEDED_BY` 行不重复计数
  - P7：NATIVE_FAIL_CONTROL 用于 vl-ng2

  全部 PASS 才能继续。
- 离线重判：用 verdict v4 加 v3 预注册加 r8m2b 的 FACTS/STATE，输出 `REJUDGE_R8_M2b_v4.tsv` 和摘要。预期新增的 MISMATCH 至少有 M2-05-P0-F3；不得事后调整。

### S-E 预注册 v4 增量表（先诊断定索引，再冻结）
1. 诊断（INFLUENCED，写到 `$EV/diag/`，只用来确认 K 是否可达、命中的 caller 行是否正确）：
   - REP-INIT-*-C 的新 K；
   - SOLN 探针的 K；
   - M2-06 的诊断行。

   诊断结果只能用来确定索引（参照 U251/U259 的先例），**不得回填成 exp 预言**。
2. 冻结 `PREREG_M2_DELTA_R8_M2c.tsv`，附 `.sha256` 和 UTC 时间戳文件。报告中引用的时间必须与时间戳文件逐字一致。内容：
   - G6-01/03/04/05/06-C（seamF-F3-san，`san_ref_point_id` 指向对应的 SANREF-C），以及 SANREF-G6-01/03/04/05/06-C（r6bseam-seamF-F3）：env 和期望按第 2 节 F2 表。
   - M2-01-01..06-C 和 M2-03-REP-INIT-01..03-C：exp_rc1=1，其余 exp 不变，exp_I1/I2=N/A，INIT_CLEAN=HOLD。
   - M2-03-REP-INIT-04..06-C：用新 K，期望取对应 M2-01-0x-C 的值，san_ref 指向 M2-01-0x-C。
   - M2-07-CTRL-vl-ng2/3/4-C：NATIVE_FAIL_CONTROL。
   - M2-05-P0-F3-C：exp_I2=N/A。
   - SOLN 探针：
     - 位点：1763 Solution_、1764 ab、1765 solved
     - 组合：closed2d-ng1、fft-ng5、kottke-ng5
     - 驱动：init-F3-dbg（成对运行）、init-F3-san、init-B-dbg（基线）
     - 共 27 行

     期望按 [源码] 预测：
     - 1763：在 1764 行 SIGSEGV，CRASH；san 下为 SAN_CRASH；
     - 1764/1765：rc1=1，然后重试时用 NULL 指针，预测 CRASH。

     basis 列写 `[源码] 未验证`，状态 INFLUENCED。B 行标 BASELINE_ONLY，注明"非修复证据"。
   - M2-06-DIAG-01-F3：RECORD_ONLY。
3. 写 `PREREG_DIFF_R8_M2c.tsv`：每个 `-C` 行相对原行改了哪些列，每处改动都附 U 编号和来源行号。断言：除 U262、U263、U266、U268 允许的列之外，改动数为 0。
4. 断言增量表行数，并在报告中写明公式：主表 150 + SANREF 19 + WIN64 5 + DELTA N = 合计；被替代的行数 S 单独列出。

### S-F 冒烟与正式运行
1. 冒烟：增量表全部行跑一遍，写到 `$EV/smoke/`，过门禁 v2。冒烟中的非 MATCH 必须先写进分诊表（U270）。
2. 正式运行：先完整跑完 pass1 的全部增量行，再完整跑 pass2。输出目录非空就拒绝运行，不覆盖。

### S-G 判定与汇总
输出以下文件：
- `FACTS_R8_M2c_pass{1,2}.tsv`
- `STATE_R8_M2c_pass{1,2}.tsv`
- `VERDICT_R8_M2c.tsv`
- `SUMMARY_R8_M2c.txt`
- `RED_POINTS_R8_M2c.tsv`
- `CLASS_DIST_R8_M2c.tsv`

还要输出 **M2 合并总表** `M2_CONSOLIDATED_R8_M2c.tsv`：用 v4 重判后的 r8m2b 174 行，加上增量行，按 `SUPERSEDED_BY` 合并成"有效结论"。断言：有效行数 = 174 + N − S。

更新红点台账（`RED_POINTS_LEDGER_R6c.tsv` 不改，新建追加表 `RED_POINTS_LEDGER_APPEND_R8_M2c.tsv`），至少包含：RP-R8-M2c-1、RP-R8-M2c-1b、M2-06/K-1 的状态，以及溯源审计中新增的待裁决项。

措辞要求：
- REPORTED_FAILURE 只表示"在该注入下返回码非零"。
- B 列观察不是修复证据。
- 没有实测的写"未验证"或"[源码]"。

### S-H 完整性与收尾
1. `COMPLETENESS_R8_M2c.tsv`：判 JUDGED / UNJUDGED_MISSING / UNJUDGED_BY_DESIGN / NOT_RUN 时依据实际运行记录。IDENTITY_FAIL 的行不得记 PASS。合计断言等于各表行数之和。
2. end 门禁写入 `GATE_R8_M2c_end.txt`。如果有失败后重跑的情况，保留 `_R1`，并写进事件表。
3. 按 AGENTS.md 第 7 节：小表复制到 `checkpoints/p05/registries/s4r8/M2/r8m2c/`（不改名），写 `SHA256SUMS.txt` 并逐个比对；证据目录也写 `SHA256SUMS.txt`；更新 STATE.md（一页以内，改正 STATE 里 M2-01 的"6 MISMATCH"口径，指向分诊表）；写报告 `checkpoints/p05/P05_S4R8_M2C_REPORT.md`。
4. 报告必须包含：
   - 26 点分诊结论；
   - 溯源审计统计；
   - v4 重判与 r8m2b 原判的差异；
   - SOLN 探针结果（逐位点、逐树）；
   - 违规两张表：表一越界写入尝试，表二工具/脚本事件，包含本轮全部 `rm`/`mv`/重跑；
   - 结尾写"本轮已完成/未完成 r8m2c 范围，等待用户审核"，并附 `git log -1` 与 `git status --short`。
5. 提交范围限于 `checkpoints/p05/` 与 `testing/d003/`。提交信息末尾写 `awaiting user review`。

## 6. 交给用户裁决的事项（写进报告末尾，不要自行决定）
1. RP-R8-M2c-1/1b：修（开 S3R5 修复轮，改 `S4.cpp` InitSolution 的分配判空与失败清理，冻结新树 F4，修后回归 M1/M2 相关点），还是转 S5？
2. K-1（M2-06）：是否以"F3 上未复现"关闭？
3. 溯源审计中新增的 TRACED_DIFF 各项如何处置。
4. 进入 M3 的前置条件是否满足：make test 相对基线，Python/Lua 公共 API 的"正常 → 失败可见 → 重试恢复"全链路。
