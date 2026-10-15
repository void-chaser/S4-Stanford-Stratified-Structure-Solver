# P05-S4 R8 M2a2（r8m2a2）任务书：r8m2a 审核登记 + 门禁修正 + M2 装置构建与完整预注册（不运行 S4 驱动）

> 本轮是 P05-S4 的子轮次 R8 M2a2（M2a 的续轮，不是 M2b）。不宣布任何阶段完成。先读 AGENTS.md 与 checkpoints/p05/STATE.md。
> 本轮**不运行任何 S4 驱动、运行器或 gdb**。允许：读源码与已提交文件；写新装置源码；经脚本编译（库、驱动、sanitizer 版、seam 版）；git archive 导出树；运行**不链接 S4** 的 sanitizer 探针；写设计表与预注册；用合成数据检验判定脚本。
> **工作量不是停止理由。** 只有 §1.5 列出的情况可以停止。每个 M2 项结束时，要么有预注册点，要么有 §4.9 规定的类别和支撑表。"没来得及做"不是合法状态，§4.9 的完整性检查会把它判为 FAIL。
> 第一步：用 **write 工具**把本任务书原文保存为 `checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a2.md`。

## 0. 开工基线（任一不符就停）
- HEAD = `6a4f0031afeda0a3105c9983d5a65a2d847f1488`（r8m2a 记录提交）
- `git rev-parse HEAD:S4` = `6cff923a02baf19e01966b2339755cbf3a5deeef`（F3）
- 判定器 `testing/d003/judge_d003.py` sha256 = `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`
- `RULINGS.tsv` 92855 字节，sha256 `c1632c0f518ff20d3139891230b379772ad6757ef16e60cc7564abf71c19813c`
- `registries/s4r8/ERRATA_8.txt` 67104 字节，sha256 `e559b0110a26f3f039b27a39c1a08924eee4b43e394ddf799cee347706cf7520`（最后一条 E8-90）
- `STATE.md` 7857 字节，sha256 `5554334a11200e9dfc0bb8f371c57e5155f49e71b9dc109a556eaac7531e87ab`
- `registries/s4r8/M2/r8m2a/PREREG_M2_R8_M2a_R2.tsv` sha256 = `557f568a787f3d216c0a412c597cabc41dbc46771f1404691565f3b2ae362e80`
- `registries/s4r8/M2/r8m2a/`：共 20 个文件；`SHA256SUMS.txt` 19 项，`-c` 全部 OK；`SHA256SUMS_END.txt` **不存在**（这是已知缺口，由 §4.0 补上）
- `testing/d003/stage_s4/postcommit_r8m2a.py` 已被跟踪，sha256 = `8063c17108d6b3e9e2c8b4f8d7495375f45e655eae05930dd5a416d55ae38081`
- 开工时 `git status --short` 只允许：`?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a2.md` 与本轮新建的 `?? testing/d003/stage_s4/*r8m2a2*`
- `EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a2`；safe_run 的目录参数为 `p05-s4r8/m2a2`
- `testing/d003/stage_s4/` 下所有已提交文件（含 `*r8m2a*`，也就是上一轮的全部脚本）冻结：不修改，不运行。`evidence/p05-s4r8/` 下其他子目录只读。

## 1. 执行纪律
§1.1–§1.6 **逐条沿用** `checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a.md` 的 §1.1–§1.6（先用 read 读原文）。把其中的 `m2a` 换成 `m2a2`，`r8m2a` 换成 `r8m2a2`，`M2A` 换成 `M2A2`。在此基础上补充以下几点。

- **1.1 补充**：标准首段逐字为
  `REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`
  上一轮的 `*_r8m2a*` 脚本也属于历史脚本。需要它们的功能时，复制为 `*_r8m2a2*`，按复制品规则产出 SRC_DIFF。
- **1.2 补充**：读 F3 或 B 源码一律用 read 工具读本轮导出的 `$EV/tree_F3/`、`$EV/tree_B/`。**不得**内联 `git show`、`git branch`、`head`、`tail`、`wc`。`safe_run.sh` 后面只能接本轮脚本文件，不得接 `sh -c`，也不得接 `true` 之类的命令。
- **1.3 补充**：gdb 脚本（`.gdb`）与 gdb 的 Python 脚本，按 shell 正则检查。
- **1.5 停止条件**：沿用 ①–⑦，另加 ⑧：§4.9 完整性检查 FAIL。
  - end 门禁 FAILS≠0 时**不提交**：停下，报告失败项，等用户处理（U237）。
  - "需要改 `S4/` 才能测"不是停止条件，标 `NEEDS_S4_CHANGE` 即可。
  - 编译失败不是停止条件，标 `BUILD_FAILED` 即可。

## 2. 门禁（第一步做：先跑 start，再做任何追加或生成）
- 用 read 读 `testing/d003/stage_s4/gate_r8m2a.sh`、`gate_check_r8m2a.py`、`gate_allow_r8m2a_start.txt`、`gate_allow_r8m2a_end.txt`、`diff_gate_r8m2a.sh`，用 write 新建对应的五个 `*_r8m2a2*` 文件。只改以下内容：
  - 基线（§0）；
  - 证据目录改为 `p05-s4r8/m2a2`；
  - 输出名改为 `GATE_R8_M2a2_<X>.txt`；
  - 自引用名、允许列表；
  - RULINGS/ERRATA 前缀基准；
  - start 附加核对（§0 中各 sha、r8m2a 的 19 项清单 `-c` OK、`postcommit_r8m2a.py` 已被跟踪）；
  - **构建产物检查改为基线式（U237）**，规则如下。
- **基线式构建产物检查**：
  - start 时扫描 `testing/d003/` 与 `checkpoints/p05/`（排除 `checkpoints/p05/evidence/`），把每个 `__pycache__` 目录及其中的文件、每个 `*.o`、每个 `a.out` 记录为"路径、字节数、mtime（ns）、sha256"，写入 `$EV/STRAY_BASELINE_R8_M2a2.tsv`。门禁文件记录它的 sha256。
  - 开工基线应包含 `testing/d003/__pycache__/judge_d003.cpython-314.pyc`（17900 B）与 `matrix_r2.cpython-314.pyc`（17250 B）。不包含就记 FAIL。
  - end 时重扫，与基线比较。只有**新增或变化**才算 FAIL。基线中已有的条目不删除（U17）。
  - 扫描范围在 start 前固定，之后不得调整。
- end 模式 status 只允许以下各项：
  - ` M`：`checkpoints/p05/STATE.md`、`checkpoints/p05/registries/RULINGS.tsv`、`checkpoints/p05/registries/s4r8/ERRATA_8.txt`
  - `??`：`checkpoints/p05/P05_S4R8_M2A2_REPORT.md`、`checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a2.md`、`checkpoints/p05/registries/s4r8/M2/r8m2a2/*`、`checkpoints/p05/registries/s4r8/M2/r8m2a/GATE_R8_M2a_end*.txt`、`checkpoints/p05/registries/s4r8/M2/r8m2a/POSTCOMMIT_R8_M2a.txt`、`checkpoints/p05/registries/s4r8/M2/r8m2a/SHA256SUMS_END.txt`、`testing/d003/stage_s4/*r8m2a2*`
- end 另外核对：
  - RULINGS、ERRATA 的开工部分作为前缀逐字节不变；
  - `registries/s4r8/M2/r8m2a/` 原有 20 个文件的 sha256 不变（只允许新增 §4.0 的 5 个文件）；
  - 构建产物检查按基线式比较。
- 两份门禁的 FAILS 都必须为 0。

## 3. 裁决与勘误登记（start 门禁通过后做；builder .py + 追加 .sh；5 列；status"生效"；来源"P05-S4 R8 M2a2 任务书 §3"；前缀校验）
### 3.1 RULINGS.tsv 追加
- **U236**：接受 r8m2a（`6a4f003`）以下结果：
  - U229–U235 与 E8-88–E8-90 已登记；
  - A-10 交叉核对 6/6 COVERED_BY_M0，因此 M2-00 无需出点；
  - 装置盘点 8/8 SAME；
  - F3、B 树导出哈希一致；
  - 判定阳性对照 `_R2` PASS（第一次 FAIL 原因为合成设计错误，已披露）。
  
  以下按执行偏离或违规接受，不追认为合规：
  - `6a4f003` 在 end 门禁 FAILS=1 时提交，偏离 U158；
  - `safe_run -- sh -c 'true'` 是违规；
  - 白名单外的内联命令（`git show`、`head/tail/wc`、`git branch`）；
  - 看到失败后三次收窄门禁扫描范围（被 U237 取代）。
  
  r8m2a 只完成了 M2a 范围的一部分，其余在 r8m2a2 完成。
- **U237**：r8m2a end 门禁 `NO_STRAY_BUILD_PRODUCTS_END` 的失败是误报。`testing/d003/__pycache__/` 中两个 pyc 的 mtime 为 2026-10-11 18:28:10 与 19:19:29（+1100），早于 r8m2a start 门禁（2026-10-15 17:18:13 +1100），并且被 `.gitignore` 的 `__pycache__/` 忽略。r8m2a 的脚本用 `python3 -I -B` 运行，不写字节码。r8m2a 报告中"本轮产生（推断）"的说法不成立（E8-91）。这两个文件不删除（U17）。自 r8m2a2 起：构建产物检查采用"start 记录基线、end 只判新增或变化"；end 门禁 FAILS≠0 时不提交，停下等用户处理。
- **U238**：r8m2a 的 M2-01 预注册（`PREREG_M2_R8_M2a_R2.tsv`，sha `557f568a…`）不能判定 I1–I6，原因有三：
  1. G5 规则依赖 gdb 读私有状态（`r6c_judge.py` 读 R6BSTATE、R6BCLM、R6CREQ），需要 `-O0 -g` 的 F3 dbg 库与 dbg 驱动，并配合 `r6c_state.gdb`；而登记的 `init-F3`、`polyinj-F3` 链接的是 F3 plain 库；
  2. 表中缺少 inj_call、k_fail、k_preretry、k_retry、k_before、argv 列；
  3. 没有 I6 所需的对照组。
  
  该表的 I 列作废（E8-92）。rc 与类别列不单独重跑（M1 已覆盖，U225）。M2-01 由 r8m2a2 的新预注册取代。原文件不改。
- **U239**：M2-09 不需要用户裁决。
  - env 取自 `registries/s4r7/REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv` 第 7–8 行：`FMM_MODE=fft;S4FMM_NG=9`，无注入；期望 CONTROL_OK、rc 0，标 INFLUENCED。
  - 驱动按登记意图用 fmmret 族的 plain 驱动：F3 用 `seam-fmmret-F3`（`registries/s4r8/DRIVERS_R8.tsv`），F2 用 `evidence/p05-s4r7/drivers_r7/seam-fmmret-F2/driver`（`registries/s4r7/DRIVERS_R7_SEAM.tsv` 的 fmmret-F2 行，sha 先核对）。
  - "CTRL_SEAM 的全部 fmmret 行"就是这两行。M2-09 共 2 点（F3、F2 各 1）。
  - F3 这一点在 R8 M0 已以 seam-fmmret-F3 跑过两遍 MATCH（`registries/s4r8/RESULTS_R8_D_pass1.tsv` 第 4 行）。M2-09 再跑一次，是为了与 F2 成对比较。
  - G2a 中以 `fmmret:` 开头的注入行已在 M1 覆盖，M2 不重做。
- **U240**：M2-06 的映射与范围。
  - `linearsolve_null2:244` 对应 F3 `S4/fmm/fmm_closed.cpp:244–245`，依据 `testing/d003/seam/apply_seam_b2.py:19,68`，本轮在导出的 F3 树上复核锚点。
  - 该点的返回码已由 M1 的 `R4-CL04-F-F3` 覆盖（MATCH，REPORTED_FAILURE，rc1 20），M2 不重做。
  - K-1 本身问的是有限性检查：[源码] F3 的 `fmm_closed.cpp` 没有 `isfinite`，`fmm_kottke.cpp:312/315` 有。
  - M2-06 测的是张量路径上 solve_info=0 但 Epsilon_inv 非有限的情形：新建 `inject_r8m2a2_nan.cpp`，以复制品规则从 `inject_r4_plan.cpp` 复制，只追加一个请求 `linearsolve_nanbuf:244:K`，在 `S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER` 中把输出写成 NaN，原有分支逐字不变。所需钩子是否存在于 F3 seamF 库，用 nm 脚本核对；不存在时，在 `$EV` 下的导出副本上加打 `apply_seam_r4_buf.py` 另建 seam 库，不改 `S4/`。
  - 期望 [源码]：rc1=0，类别 SILENT_SWALLOW，INFLUENCED。若 M2b 实测如此，就是 K-1 红点候选，按 U4 处理。
- **U241**：M2-02 阶段 e 的搜索范围。
  - 候选包括：`registries/s4r6d/U2_STAGE_R6d.tsv` 与 `SEAM_SITE_STAGE_R6d.tsv` 中的全部注入请求；以及 F3 导出树中位于 `Simulation_ComputeLayerModes` 之外、而在 FMM/FFT 失败传播链上的分配或计划调用（如 GetFieldOnGrid、通量与场缓存路径）[源码]。
  - 逐个写出位置（文件:行号）、阶段定义（ERRATA_6d 的 E6d-3 第 2 条）、是否在 D003 范围内（U5b/E6-4，以及 MEMORY 中的 D003 范围判据：分配或调用点处于"模式或缓存是否被安装"的验收路径，或位于 FMM/FFT 失败传播链上）。
  - 全部在范围外就写 `NOT_FOUND_IN_SCOPE`，去向由用户在审核时裁决。本轮不扩大范围。
- **U242**：M2-08 类别 C 的搜索范围。
  - 模式：{closed1d、closed2d、experimental、fft、kottke、tensor、jones、nv、vl}；NG：2…8。
  - "执行期窗口内有分配"按以下依据判断：F3 源码 [源码]；`registries/s4r3/CALLSEQ.tsv`；`registries/s4r8/M1a/CALLSEQ_POINT_COVERAGE_R8_M1a4_R3.tsv`。本轮不做新的运行。
  - 搜索表每行写依据（文件:行号）。找到配置就出点：rc≠0，且输出缓冲保持哨兵值或不被使用。没找到就写 `NOT_FOUND` 并附表，去向由用户在审核时裁决。
- **U243**：M2-07 的网格固定如下。
  - NG 1…8 × 模式 {closed1d、closed2d、experimental、fft、kottke、tensor、jones、nv、vl}，每格一个无注入对照（d003-F3-plain）。
  - 每个模式加一个代表性注入：`s4malloc`，NTH=1，d003plan-F3-plain，NG=5。
  - 期望：M0、M1 有同 env 观察的取观察值；没有的取 [源码] 推断，一律标 INFLUENCED。
  - 注入格的 exp_rc1 若历史上没有同 env 的确切值，允许写记号 `NZ`（表示"非零"）。判定脚本必须支持该记号。
- **U244**：M2-04 双目标的语义。
  - [源码]：第一处失败后，同一次 ComputeLayerModes 调用即返回，第二处在同一次调用里到不了。因此"一次运行两处失败"定义为：call1 失败，重试 call2 再失败，call3 恢复。
  - (a) 两次失败在同一层；(b) 两次失败在不同层（需要 M2-05 的多层驱动）。
  - 新建 `inject_r8m2a2_dual.cpp`，以复制品规则从 `inject_r4_plan.cpp` 复制，只追加对 `S4FMM_INJECT2` 的独立解析与计数，原有分支逐字不变。
  - 期望：call1、call2 的 rc 非零且无信号；call3 rc=0；每次失败后的 I1–I6 按 M2-01 规则成立。快照索引须由驱动源码推出并写入预注册。
- **U245**：M2-05 的布局为 P0（图案层在第 0 层）、P2（图案层在第 2 层）、PP1（两个图案层，第一个失败）、PP2（两个图案层，第二个失败）。新建 `driver_r8m2a2_layers.cpp`，以复制品规则从 `driver_r6b_state.cpp` 复制，用 env `S4FMM_LAYOUT` 选布局。原布局（不设该变量时）的行为逐字不变。
- **U246**：M2-03 sanitizer。
  - 先跑 `san_probe_r8m2a2.sh`：只编译运行一个不链接 S4 的探针，确认 `-fsanitize=address,undefined` 可用。
  - 可用时，在 `$EV/build/san/` 构建 F3 sanitizer 库与 M2-01、M2-03 所需驱动。
  - 点集：`registries/s4r7/REGRESS_R7_M3.tsv`（G5、G6）中每个（mode × stage × inj_kind）单元格各 1 点，加 M2-01 的 17 个修复点。
  - 判定：sanitizer 报告数为 0，且 rc 与类别与非 sanitizer 运行一致。
  - 工具链不可用时标 `BUILD_FAILED`，不出点。
- **U247**：本轮为 r8m2a2。结束后停下，等用户审核预注册与 NOT_FOUND 类各项的去向。M2b 只在用户审核后开始。

### 3.2 ERRATA_8.txt 追加（只追加）
- **E8-91**：r8m2a 报告 §14 与最终回复称 `testing/d003/__pycache__` 是"本轮产生（推断）"，这一说法不成立（mtime 证据见 U237）。
- **E8-92**：`PREREG_M2_R8_M2a_R2.tsv` 的 I 列不可判定（U238），由 r8m2a2 预注册的 M2-01 行取代。原表不改。
- **E8-93**：r8m2a 有四处不一致：
  - 设计表 `M2_DESIGN_R8_M2a_R2.tsv` 中 M2-01 的可行性为 `FEASIBLE_NEW_APPARATUS`，报告 §5 写作 `FEASIBLE_EXISTING`；
  - STATE §4 写有 `SHA256SUMS_END.txt`，但该文件不存在；
  - 报告写 STATE 为 7854 字节，提交后实际为 7857 字节；
  - end 门禁文件没有复制进 registries。
  
  前三处由本轮 STATE 与报告更正；最后一处由 §4.0 补上。已提交的原文件不改。
- **E8-94**：r8m2a 把 M2-09 的 env 与 M2-06 的 ID 映射列为"需用户裁决"，但两者都可以从已提交的登记表查到（U239、U240）。
- **E8-95**：`6a4f003` 是在 end 门禁 FAILS=1 时做的提交（U236）。

## 4. 本轮工作（全部输出到 `$EV/`；不运行 S4 驱动）
### 4.0 补登 r8m2a 收尾（`copy_r8m2a_end_r8m2a2.py`）
- 把 `evidence/p05-s4r8/m2a/` 下的 `GATE_R8_M2a_end.txt`、`GATE_R8_M2a_end_R2.txt`、`GATE_R8_M2a_end_R3.txt`、`POSTCOMMIT_R8_M2a.txt` 原名复制到 `registries/s4r8/M2/r8m2a/`。
- 在该目录写 `SHA256SUMS_END.txt`（4 项），并逐个与原件比对。
- 目录中已有的文件不动。复制前先确认 4 个目标都不存在。

### 4.1 树导出与装置核对（`export_r8m2a2.sh`、`nm_check_r8m2a2.sh`）
- 用 `git archive` 导出 `8d8202a S4` 到 `$EV/tree_F3/`，导出 `37a82e8 S4` 到 `$EV/tree_B/`，并核对树哈希。
- 对以下产物重算 sha256 并与记录比较，输出 `REUSE_CHECK_R8_M2a2.tsv`：F3 dbg 库 `evidence/p05-s4r8/build_r8/F3-dbg/build/libS4.a`（BUILD_R8.tsv 的 dbg 行）、F3 plain 库、`drivers_r8m1/{init-F3,polyinj-F3,r6bstate-F3-dbg}`、`drivers_r8/{d003-F3-plain,d003plan-F3-plain,seam-fmmret-F3,seam-seamF-F3}`、`drivers_r7/seam-fmmret-F2`。不一致的不复用。
- 用 nm 核对：F3 seamF 库中是否有 `S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER`、`S4_TEST_LINEARSOLVE_NULLINFO2_AFTER`；F3 dbg 库是否带调试信息。输出 `NM_CHECK_R8_M2a2.tsv`。
- 在 `$EV/tree_F3/` 复核 `fmm_closed.cpp:244–245` 与 `apply_seam_b2.py` 中 id 244 的锚点，输出 `K1_ANCHOR_R8_M2a2.tsv`（[源码]）。

### 4.2 设计表 v3（`design_r8m2a2.py` → `M2_DESIGN_R8_M2a2.tsv` 与 `.md`）
- 列与 r8m2a 相同，另加一列 `supersedes`。M2-00 沿用 r8m2a（COVERED_BY_M0）。M2-01…M2-10 按 U238–U246 重写。M3_DEFERRED 保留。
- 可行性类别只允许以下几种：`FEASIBLE_EXISTING`、`FEASIBLE_NEW_APPARATUS`、`COVERED_BY_M0`、`COVERED_BY_M1`、`NEEDS_S4_CHANGE`、`NOT_FOUND`、`NOT_FOUND_IN_SCOPE`、`BUILD_FAILED`、`M3_DEFERRED`。
- 报告中的设计摘要表必须由脚本从本表生成，不得手抄。

### 4.3 新装置源码（只能是 `testing/d003/stage_s4/*r8m2a2*`；复制品一律产出 `SRC_DIFF_R8_M2a2_<名>.txt` 并在报告中逐处说明）
- `inject_r8m2a2_dual.cpp`（U244）、`inject_r8m2a2_nan.cpp`（U240）、`driver_r8m2a2_layers.cpp`（U245）。
- M2-01 的 dbg 链接沿用现有源码（`driver_r6b_state.cpp` + `stage_s3r4/inject_s3r4_init.cpp`；`stage_s3r4c2/driver_s3r4c2_poly.cpp` + `stage_s3r4c3/inject_s3r4c3_poly.cpp`）。不改源码，只改链接选项：用 F3 dbg 库，加 `-O0 -g`。wrap 选项从 `stage_s3r4c2/link_init_c2.sh`、`stage_s3r4c3/link_poly_inj_c3.sh` 用 read 读出，原样照写。
- gdb 脚本：
  - 复制 `stage_s4/r6c_state.gdb`、`r6c_state_gdb.py` 为 `*_r8m2a2*`，只改 source 路径；
  - M2-10 新建 `m210_b_r8m2a2.gdb`，断点位置写成 B 树的文件:行号 [源码]，由 `$EV/tree_B/` 读出。
- C/C++ 源码按 §1.3 的 C 正则检查，必须 0 行。

### 4.4 构建（`build_r8m2a2.sh` → `BUILD_R8_M2a2.tsv`）
- 产物一律落在 `$EV/build/` 下，编译命令显式写 `-o`。
- 至少构建以下产物：
  - `init-F3-dbg`、`polyinj-F3-dbg`（M2-01）；
  - `dual-F3-dbg`（M2-04）；
  - `layers-F3-dbg`，以及 `layers` 与 `dual` 的组合（M2-04(b)、M2-05）；
  - `nan-F3`（M2-06：seamF 库，或 §4.1 判定需要时新建的 buf seam 库）；
  - sanitizer 库与驱动（M2-03）；
  - M2-07 复用 d003、d003plan 的 F3 plain 驱动，不新建；
  - M2-10 若 B 的 dbg 驱动不存在，就在 `$EV/build/B-dbg/` 构建。
- 每一项记录：产物名、路径、sha256、源文件 sha256、库 sha256、编译命令、UTC、rc。
- 失败项标 `BUILD_FAILED`，对应设计项也改标，然后继续其余项。
- 构建出的驱动不运行。

### 4.5 sanitizer 探针（`san_probe_r8m2a2.sh`；不链接 S4）
- 输出 `SAN_PROBE_R8_M2a2.txt`：编译 rc、运行 rc，以及故意越界探针是否被 ASan 报出（以 ASan 报告行为准）。

### 4.6 预注册（`prereg_r8m2a2.py` → `PREREG_M2_R8_M2a2.tsv`、`.sha256`、`_TIMESTAMP_UTC.txt`、`PREREG_M2_COUNT_R8_M2a2.txt`）
- 列：point_id（`M2-<项>-<序号>-<树>`）、item、tree、driver、driver_sha256、lib_sha256、gdb_script（不用 gdb 的写 `-`）、argv、env（完整键值对）、passes（2）、inj_call、k_before、k_fail、k_preretry、k_retry、retry_call、control_group、exp_rc1、exp_rc2、exp_signal、exp_hit、exp_class、exp_I1…exp_I7、exp_san（M2-03 用）、exp_stage、basis（来源文件:行号）、status。
- 对照组单独成行，`item` 写成 `<项>-CTRL`。M2-01 至少需要 9 个对照组：init 的 closed2d NG1、fft NG5、kottke NG5；poly 的 fft NG1/5/9、kottke NG1/5/9。M2-04、M2-05 的对照组按其布局与 env 生成。
- inj_call 与 k 索引从注入库的计数方式和驱动的快照顺序推出（[源码]，写明文件:行号）。推不出的点标 `UNRESOLVED_INDEX`，不出点，并在汇总中列出。
- I 列的适用性遵循 `registries/s4r6c/REGISTRY_S4_PRE_R6b_STATE_v2.tsv` 头部第 5–20 行：I3 只适用于 PolBasis 模式，其余写 `-`；I7 只在 M2-03 的行中填写。
- 计数文件按 item × tree 计数，**断言各项之和 = 总行数**，并断言每个设计项的点数等于设计表的点数。任一断言失败就不写预注册，输出 FAIL。
- 预注册写完后不得修改。r8m2a 的 17 行不复制、不引用为期望来源。

### 4.7 判定脚本与阳性对照
- `verdict_m2_r8m2a2.py`：以复制品规则从 `verdict_m2_r8m2a.py` 复制。只追加以下三点：
  - 支持 `NZ` 记号；
  - 支持 exp_san；
  - 对照组的读取。
  
  判定器经 sha 校验后只读导入，用 `python3 -I -B` 运行。
- `posctrl_m2_r8m2a2.py`：用 subprocess 调用正式判定脚本，五个情形如下：
  - A：全部等于期望 → MISMATCH 0；
  - B：改一个 rc1 → MISMATCH 1，且该 point_id 出现在输出中；
  - C：pass1 与 pass2 不一致 → FLAKY 1；
  - D：`NZ` 期望遇到观察值 0 → MISMATCH 1，遇到观察值 20 → MISMATCH 0；
  - E：改一个 exp_I 对应的观察值 → MISMATCH 1。
  
  计数如实记录，输出 `POSCTRL_M2_R8_M2a2.txt`，以 `POSCTRL=PASS/FAIL` 结尾。

### 4.8 报告数字核对（`check_report_counts_r8m2a2.py`）
- 报告中写以下核对标记：`M2A2_PREREG_ROWS=`、`M2A2_PREREG_CTRL_ROWS=`、`M2A2_ITEMS_WITH_POINTS=`、`M2A2_ITEMS_NOT_FOUND=`、`M2A2_ITEMS_NOT_FOUND_IN_SCOPE=`、`M2A2_ITEMS_NEEDS_S4_CHANGE=`、`M2A2_ITEMS_BUILD_FAILED=`、`M2A2_BUILD_OK=`、`M2A2_BUILD_FAILED=`、`M2A2_REUSE_DIFFERENT=`、`M2A2_UNRESOLVED_INDEX=`、`M2A2_POSCTRL_{A,B,C,D,E}=`、`M2A2_STRAY_NEW=`。
- 脚本从证据表重算每一项后比对，输出 `REPORT_COUNT_CHECK_R8_M2a2.txt`。

### 4.9 完整性检查（`completeness_r8m2a2.py` → `COMPLETENESS_R8_M2a2.txt`）
- 对 M2-00…M2-10 逐项断言，满足以下之一即可：
  - 预注册点数 > 0；
  - 类别为 `COVERED_BY_M0` / `COVERED_BY_M1`，且附覆盖行号；
  - 类别为 `NOT_FOUND` / `NOT_FOUND_IN_SCOPE`，且附搜索表（M2-02：`STAGE_E_SEARCH_R8_M2a2.tsv`；M2-08：`CATC_SEARCH_R8_M2a2.tsv`），表的行数 > 0；
  - 类别为 `NEEDS_S4_CHANGE`，且附理由；
  - 类别为 `BUILD_FAILED`，且附 BUILD 行。
- 任一项不满足就输出 FAIL，触发停止条件 ⑧。

## 5. 措辞
沿用 r8m2a 任务书 §5。设计与预注册只写"期望"。K-1 的期望写"[源码]：张量分支无有限性检查"，不写"缺陷已确认"。

## 6. 本轮不做
- 不运行 S4 驱动、运行器、gdb。
- 不做 M2b、M2c、M3。
- 除 STATE、RULINGS、ERRATA 的追加，以及 §4.0 的新增文件以外，不修改任何已提交文件。

## 7. 收尾（完成或停止都要做；顺序固定）
1. 先写好 `postcommit_r8m2a2.py`（U17：拒绝覆盖），按 §1.3 检查后随本轮提交，提交后只运行。
2. 用 `copy_registries_r8m2a2.py` 原名复制到 `registries/s4r8/M2/r8m2a2/`，写 `SHA256SUMS.txt` 并逐个比对。复制范围：start 门禁、GATE_DIFF、STRAY_BASELINE、REUSE_CHECK、NM_CHECK、K1_ANCHOR、设计表（tsv 与 md）、全部 SRC_DIFF、BUILD、SAN_PROBE、两份搜索表、预注册三件与 COUNT、POSCTRL、COMPLETENESS、REPORT_COUNT_CHECK（含 `_R2`）。
3. 用 `sums_ev_r8m2a2.py` 在 `$EV/` 写 `SHA256SUMS.txt`（不含 `tmp/`、`build/`、`tree_*/`）。
4. 用 edit 更新 STATE.md，必须 ≤ 8192 字节（用本轮脚本确认）：
   - 本轮开工基线改为 `6a4f003`；当前轮次改为 r8m2a2；
   - 关键数字中 M2a 一行改为"r8m2a 部分 + r8m2a2"，写预注册行数、有点的项数、构建 OK/FAILED 数；
   - 开放问题各行的去向按设计表 v3 更新；
   - 证据位置只保留最近三轮（m2a2、m2a、m1c4），r8m2a 一行注明 `SHA256SUMS_END.txt` 由 r8m2a2 补登（E8-93）。
5. 用 write 写报告 `checkpoints/p05/P05_S4R8_M2A2_REPORT.md`，内容包括：
   - 开工门禁；U236–U247；E8-91–E8-95；§4.0–§4.9 各项结果；
   - 设计摘要表（由脚本生成）；
   - 需要用户裁决的事项：只列 NOT_FOUND / NOT_FOUND_IN_SCOPE / NEEDS_S4_CHANGE / BUILD_FAILED / UNRESOLVED_INDEX，各附支撑表；
   - "运行前检查"与"内联命令自查"两节；违规表一、表二；根目录临时区开工与收尾快照。
   
   结尾写"本轮未完成/已完成 R8 M2a2 范围，等待用户审核"。写完后运行核对脚本；不是 ALL_MATCH 就用 edit 修正报告后以 `_R2` 重跑，两次结果都保留。
6. 跑 end 门禁。**FAILS=0 才能用 `commit_r8m2a2.sh` 提交**（脚本内先核对 status，只 add 指定路径）。FAILS≠0 就停下，不提交，在最终回复中报告失败项（U237）。提交信息：
   `P05-S4 R8 M2a2 (r8m2a2): U236-U247, E8-91..E8-95, r8m2a end-gate registry backfill, baseline stray gate, M2 design v3, new apparatus build (<ok>/<failed>), M2 prereg frozen (<n> rows incl. <c> control), posctrl A-E; no S4 driver run; awaiting user review`
7. 提交后经 safe_run 运行 `postcommit_r8m2a2.py`，在最终回复中原文给出它的输出。此后不再新建任何文件，`git status --short` 应为空。

## 8. 最终回复（简短中文）
列出以下内容：
- U236–U247、E8-91–E8-95 是否已登记；
- §4.0 补登结果；
- 复用核对中不一致的数量；
- 各 M2 项的类别与点数表（含对照行数）；
- 构建 OK/FAILED 数；
- sanitizer 探针结果；
- 预注册总行数与 sha256；
- 阳性对照 A–E 的计数；
- 完整性检查结果；
- 违规表；
- 提交后的 `git log -1` 与 `git status --short`；
- 需要用户裁决的事项（各附支撑表路径）。

不得出现"签收""已修好""已验证"等字样（否定用法也避免）。
