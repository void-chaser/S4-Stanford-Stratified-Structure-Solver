# P05-S4 R9 M2b 任务书：R9 M0+M2 审核勘误、K 继承证明重做、SOLN I6/san 独立补判

## 0. 身份与边界
- P05-S4 子轮次 R9 的 M2b（不是新阶段）。轮次标识 `r9m2b`；证据目录 `checkpoints/p05/evidence/p05-s4r9/m2b`；小表目录 `checkpoints/p05/registries/s4r9/M2b/`；补充报告 `checkpoints/p05/P05_S4R9_M2b_REPORT.md`。任务书原文存为 `checkpoints/p05/briefs/P05_S4R9_BRIEF_M2b.md`。
- 不改写已提交的 R9 文件（报告、VERDICT、K_INHERIT、ERRATA_9 原有行都不改），只追加勘误、新建 `_R2` 文件。
- 不重跑 191 个正式点；不改预注册；不改 `S4/`、判定器和历史装置。不得宣布阶段完成，不得询问是否签收。
- **禁止 `git commit --amend`、rebase 以及任何改写历史的 git 操作。**报告里不写本轮收尾提交的哈希（由 `git log -1` 在报告之外核对）。
- 开工先读：`AGENTS.md` → `STATE.md` → 本任务书 → `P05_S4R9_M2_REPORT.md` → `registries/s4r9/` → `testing/d003/stage_s4r9/{k_inherit_r9.py,verdict_m2_r9.py,facts_m2_r9.py,state_judge_m2_r9.py,posctrl_r9.py}`。
- 开工门禁：HEAD = `ebf3d007b921e64cdb838c714c0ea53299d365c9`；`HEAD:S4` = `589e15eb11fcb04e031b524f25a443e7921946cf`；判定器 sha256 = `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb`；`git status --short` 为空；`registries/s4r9/M0/SHA256SUMS.txt` 与 `M2/SHA256SUMS.txt` 逐项通过。任一不符就停下报告。

## 1. 写入与执行纪律（与 R9 相同，硬规则）
1. 每条含写入的命令开头先执行：`REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2b; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"`，然后经 `sh testing/d003/safe_run.sh p05-s4r9/m2b -- <命令>` 运行。
2. 写入目标只能以 `$EV/`、`$REPO/testing/d003/`、`$REPO/checkpoints/p05/` 开头；不得写其他轮次的证据目录（包括 `p05-s4r9/m0`、`p05-s4r9/m2`、`p05-s4r8/`），这些目录只读。脚本里的 EV 由参数给出或硬编码为 `p05-s4r9/m2b`，不允许默认值指向别的轮次。
3. 内联命令不得含 `>` 字符（含 `2>&1`）；需要输出的核对写成脚本经 safe_run 运行；不用 `2>/dev/null`；核对路径只用 `ls -d`/`test -e`；不做沙箱探测或反例测试。
4. 新脚本放 `testing/d003/stage_s4r9/`，文件名带 `r9m2b`，第一行用标准首段。Python 一律 `python3 -I -B`。运行前用 grep 工具查禁止项（`/tmp`、`2>/dev/null`、指向其他轮次证据目录的写入路径）；正则不得命中标准首段的 `"$EV/tmp"`。
5. 每一次 `rm`、`mv`、重跑覆盖都写进事件表二，**行号由脚本 `events_r9m2b.py` 从 `$EV/safe_run.log` 自动提取**，不手填。门禁重跑用 `_R2` 新文件名。
6. 停止策略：只有真实基线异常、无法解释的越界改动和第 6 节的硬停止条件才停。

## 2. 输入事实（规划者已核实，直接使用）
- F-1 K 证明缺陷：`k_inherit_r9.py:279` 取 `min(len(f3), len(f4), K_max+2)`，命中数不等也不判失败；`:294-296` 大小不同时直接 `pass`。实测：KGRP-071（seamF-F4-san, fft NG9, `S4_TEST_ALLOC_HOOK`）F3 命中 4 次、F4 命中 2 次，仍记 PASS；24 组命中数少于 K_max+2；10 组（KGRP-001…009 d003plan，bp `__wrap__Z9S4_mallocm`；KGRP-025 nan）所有命中都是 `arg=None func=… -:0`，没有大小，也没有 S4 帧。
- F-2 SOLN 未经引擎判定的列：`verdict_m2_r9.py:316` 只在 `state_analyzer` 非空时判 `exp_I1..I6`，SOLN 18 行该列是 `-`；`:281` 只对 `item=M2-03` 判 `exp_san`。所以 SOLN 的 `exp_I6=HOLD` 与 9 个 san 行的 `exp_san=0` 都没被引擎判定。规划者只读核对：两遍中 SOLN 的 `call2_sha256` 都等于对照点（`M2-01-CTRL-01/02/03-F4`，按 closed2d-ng1/fft-ng5/kottke-ng5 对应）的 `call2_sha256`，18/18 相同；9 个 san 行两遍的 `san_reports=0`、`san_crash=0`。posctrl R9_5/R9_6 用的是 M2-01-01-F3，设了 `state_analyzer`，不是 SOLN 的配置。
- F-3 HIT 行等价（K 的替代证据）：173 个回归点在 pass1、pass2 中的 `S4FMM HIT` 行（去掉 `caller=0x…`、排序后）与 F3 历史运行一致（来源依次为 `p05-s4r8/m2e/formal/run/passN/<F3点>`、`m2c/run/passN`、`m2b/run/passN`），两遍都是 173/173。
- F-4 历史改写：reflog 显示收尾提交先是 `a7f6044`，再经 `--amend` 变成 `ebf3d00`；报告第 17 节写的是 `a7f6044`。
- F-5 事件表：m0 `safe_run.log` 第 118、119、121 行是 build（第 120 行是 rm）；第 122、123 行是 gdb_audit；第 124、125 行是 noinj；第 127、128 行是 prereg；第 129–139 行是 posctrl（11 次）。m2 `safe_run.log` 第 1/3/5/7 行是 smoke，第 2/4/6 行是 rm，第 9、10 行是 consolidate。报告 §14.2 写的"m0 第 103/105 行"是错的，并且漏掉了多次重跑。
- F-6 冻结后才写的判定装置：`facts_m2_r9.py`、`state_judge_m2_r9.py`、`verdict_m2_r9.py`、`run_*_r9.py`、`posctrl_r9.py` 写于 M0 提交 `bb6f1e8`（05:48）之后。相对 `stage_s4/*_r8m2e.py` 的实质改动：facts 增加从 stdout `R6STATE 1 solution_null` 取 `post_call1_solution`；state_judge 在 `-F3` 对照不存在时改用 `-F4`，并调整 dump 目录查找顺序；verdict 的对照点与 san_ref 做 F3→F4 重映射。这些改动没有记入 RUNNER_DIFF 或 ERRATA。
- F-7 措辞与表头：报告用了"100%""完全符合""全面闭环"；`SUMMARY_R9.txt` 表头写 `VERDICT_SUMMARY_R8_M2d`，FACTS 表头写 `FACTS_R8_M2d`。

## 3. 用户裁决（start 门禁通过后追加到 RULINGS.tsv，5 列）
- **U299**：R9 M0+M2 的正式运行数据采信，191 点的判定不变。F-1、F-2、F-4、F-5、F-6、F-7 记为 E9-1 至 E9-6，追加到 `registries/s4r9/ERRATA_9.txt`，原有行不改。报告不改写，由 `P05_S4R9_M2b_REPORT.md` 补充更正。
- **U300**：K 继承证明按以下规则重做（取代 R9 的 K_INHERIT 结论，原文件保留）：
  (a) 每组在 F3、F4 上各跑一次无注入运行，采集到 K_max+2 次命中为止；两边命中总数必须相等（程序提前结束时，以实际总数相等为准）。
  (b) 每次命中必须同时有大小（或计数器的 id）和 S4 帧（函数 + 文件:行号；行号经 `LINEMAP_F3_F4_S3R5.tsv` 映射）。gdb 在 wrapper 处取不到 S4 帧时，改用 `bt 8` 向外找第一个 `S4/` 帧；plain 驱动没有调试信息时，改用驱动自身的 trace 行（`S4FMM … k=… n=…`，去掉 caller 地址）作为序列。
  (c) 三项都相同的记 `PASS_K_INHERITED_R2`；任一项不同的记 `K_DIVERGENT_R2`；取不到任何序列证据的记 `NO_SEQ_EVIDENCE_R2`，并附 F-3 的 HIT 行等价结果作为替代证据，列入"需用户裁决"。不因结果改 R9 的判定。
- **U301（预留，由用户在审核本轮后决定是否生效）**：若 SOLN 补判 18/18 为 HOLD 且 san 行为 0，RP-R8-M2c-1/1b 带范围声明关闭。本轮只写事实，不写关闭。

## 4. 步骤
- **S-A 门禁**：新写 `gate_r9m2b.sh start/end`（由 `gate_r9.sh` 复制修改，差异写入 `RUNNER_DIFF_R9M2b.txt`）。内容：第 0 节各项、`/tmp` 顶层只读快照（条目数与 sha256）、`__pycache__`/`.o` 基线清单与 mtime。
- **S-B 裁决与勘误**：追加 U299–U301，追加 E9-1 至 E9-6（每条写：事实、证据文件与行号、影响范围、处理方式）。记录提交 (i)。
- **S-C HIT 行等价表**：`hitseq_r9m2b.py` 只读两轮证据，写 `HITSEQ_F3_F4_R9M2b.tsv`（173×2 行：point_id、pass、F4 目录、F3 来源目录、F4 HIT 行 sha、F3 HIT 行 sha、相同/不同）。断言 173/173 两遍都相同；不符就停下分诊。
- **S-D K 证明重做**：
  - `k_inherit_r9m2b.py` 按 U300 运行（只读使用 `p05-s4r9/m0/build/` 与 F3 驱动，运行前核对 sha256）；
  - 写 `K_INHERIT_R9M2b.tsv`、`K_INHERIT_RAW_R9M2b.txt`；
  - 必须专门说明 KGRP-071 两边命中数不同（4 vs 2）的原因，例如 gdb 命令序列提前退出或 `continue` 次数，并附原始日志行；
  - 先用合成 gdb 输出跑通阳性对照：命中数不等 → DIVERGENT；大小不同 → DIVERGENT；无帧 → NO_SEQ_EVIDENCE；全同 → PASS。写 `POSCTRL_K_R9M2b.txt`，全部 PASS 后才正式运行。
- **S-E SOLN 独立补判**：
  - `soln_supp_r9m2b.py` 只读 `p05-s4r9/m2/FACTS_pass{1,2}_R9.tsv` 与 `PREREG_SOLN_F4_R9.tsv`（先核 sha256 `6b41d1dc…`）；
  - 规则：`I6 = HOLD` 当且仅当该点 `call{retry_call}_sha256` 等于对照点 `call{control_output_call}_sha256`（对照 id 中 `-F3`→`-F4`），两遍分别判定；san 行要求 `san_reports == exp_san` 且 `san_crash == 0`；
  - 写 `SOLN_SUPP_JUDGE_R9M2b.tsv`（18 行 × I6_p1、I6_p2、san_p1、san_p2、verdict）；
  - 先做阳性对照 `posctrl_soln_r9m2b.py`，用 SOLN 真实行的副本：篡改 call2 sha → VIOLATED/MISMATCH；san_reports 设为 1 → MISMATCH；不改 → MATCH。全部 PASS 才正式补判。
- **S-F 装置变更登记**：`judge_diff_r9m2b.py` 写 `JUDGE_TOOL_DIFF_R9M2b.txt`，内容为五个 r9 脚本相对各自 r8m2e 原件的统一 diff，并逐段说明。其中会影响判定输入的改动（F-6 三项）单独列出，并说明为什么不影响 191 点：用 F-2/F-3 的事实论证；做不到的写"未验证"。
- **S-G 事件表重建**：`events_r9m2b.py` 读 m0、m2、m2b 三份 `safe_run.log`，生成 `EVENTS_R9_ALL_R9M2b.tsv`（序号、轮次、日志行号、时间、命令前 120 字符、类别：首跑/重跑/rm/门禁），并在表尾加 F-4 的 amend 一行（来源：`git reflog` 只读输出，经脚本写入）。
- **S-H 收尾**：
  - 写 `P05_S4R9_M2b_REPORT.md`，结构为：门禁、裁决与勘误、HIT 等价、K 重做（附 KGRP-071 说明）、SOLN 补判、装置变更、事件两张表、需用户裁决（只列 `K_DIVERGENT_R2`/`NO_SEQ_EVIDENCE_R2` 组，以及 U301 是否生效）；
  - 更新 STATE.md（不超过 8192 字节），把 RP-R8-M2c-1/1b 的状态改为"18 点修后事实 + 补判结果，待用户裁决"；
  - 小表复制到 `registries/s4r9/M2b/`（不改名），写 `SHA256SUMS.txt` 并逐个比对；证据目录也写 `SHA256SUMS.txt`；
  - 运行 end 门禁，然后做收尾提交 (ii)，提交信息末尾写 `awaiting user review`；
  - 提交后只在终端输出 `git log -3 --oneline`、`git status --short`，不回写报告。

## 5. 措辞
- 不写"100%""完全""证实""精确""全面闭环"；REPORTED_FAILURE 只表示返回码非零；SOLN 写"修后验证事实：<点号>，判定 <类别>，补判 I6 <值>"；B 列不是修复证据。
- 结尾写"本轮已完成/未完成 R9 M2b 范围，等待用户审核"。

## 6. 硬停止条件
1. 开工门禁任一项不符。
2. HIT 行等价不是两遍 173/173。
3. 任一阳性对照没有全部 PASS。
4. SOLN 补判出现 VIOLATED 或 san 不符（只分诊，不改期望、不重跑）。
5. 任何越界写入、对 `S4/` 的改动、写入其他轮次证据目录，或改写 git 历史。

`K_DIVERGENT_R2` 不算硬停止：照实记录，列入"需用户裁决"。
