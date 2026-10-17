# P05-S4 R9 M1 任务书：F4 上重跑 M1（F3 侧 651 行）并与 F3 冻结事实等价比对

## 0. 身份与边界
- P05-S4 子轮次 R9 的 M1（不是新阶段）。轮次标识 r9m1；证据目录 checkpoints/p05/evidence/p05-s4r9/m1；小表目录 checkpoints/p05/registries/s4r9/M1/；报告 checkpoints/p05/P05_S4R9_M1_REPORT.md；任务书原文存为 checkpoints/p05/briefs/P05_S4R9_BRIEF_M1.md（经 safe_run 写入）。
- 本轮做：F4 驱动补齐、K 继承证明、预注册冻结、阳性对照、冒烟、正式两遍、判定、M1 F4 总表。不做 M3（make test、Python/Lua E2E）。
- 不改 S4/、判定器、历史装置，以及任何已提交的 r8/r9/r9m2b/r9m2c 脚本、allow 文件、报告和小表。新脚本放 testing/d003/stage_s4r9/，文件名带 r9m1。
- 禁止 git commit --amend、rebase 等改写历史的操作。报告不写本轮收尾提交的哈希。
- 不得宣布阶段完成，不得询问是否签收。
- 说明：用户此前转来的"Task014 INCOMPLETE（DATA_INVALID）"是 2026-10-03 P04 时期 D001/D002 线的旧输出（归档于 .local-archive/p04-history-20261009T085100Z/audit-workspace/014/），与 P05 无关，本轮不采信、不处理，只在报告 §0 记一句。
- 开工先读：AGENTS.md → STATE.md → 本任务书 → P05_S4R9_M2c_REPORT.md → P05_S4R8_M1C4_REPORT.md → registries/s4r8/M1b/r8m1b3/、M1c/r8m1c3/、M1c/r8m1c4/ → registries/s4r9/M0/（DRIVER_MAP_F3_F4_R9.tsv、BUILD_R9.tsv、K_INHERIT_R9.tsv）→ registries/s4r9/M2b、M2c 的 K/HITSEQ 表。
- 开工门禁：HEAD = 3bb60723b3b23e313fd51d5a54f2258c98ac07eb；HEAD:S4 = 589e15eb11fcb04e031b524f25a443e7921946cf；判定器 sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb；git status --short 为空；/tmp 顶层只读快照（条目数与 sha256）。任一不符即停。

## 1. 写入与执行纪律（沿用 M2c §1 全部 9 条）
1. 每条含写入的命令开头：REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"，然后经 sh testing/d003/safe_run.sh p05-s4r9/m1 -- <命令>。
2. 写入目标只能以 $EV/、$REPO/testing/d003/、$REPO/checkpoints/p05/ 开头。其他轮次的证据目录（p05-s4r8/*、p05-s3r5、p05-s4r9/m0|m2|m2b|m2c）只读；沿用那里的产物只核对 sha256。
3. 内联命令不得含 > 字符（包括 2>&1）；不用 2>/dev/null；核对路径只用 ls -d 或 test -e；不做沙箱探测，不做反例测试。
4. 新脚本第一段用标准首段；Python 一律 python3 -I -B；运行前用 grep 工具查禁止项。
5. 每一次 rm、mv、重跑、覆盖都进事件表二，行号由脚本从 $EV/safe_run.log 提取。门禁重跑用 _R2、_R3 等新文件名。
6. 停止策略：只有真实基线异常、无法解释的越界改动和 §6 的硬停止条件才停。合法的中间产物使工作区非空，不是停止理由。
7. 任何文件都不得经 safe_run 以外的途径写入，包括用编辑工具直接改文件。
8. 活文件（RULINGS.tsv、ERRATA_9.txt）只能由脚本追加：先断言"新文件 = 旧文件字节 + 新行"，再落盘。
9. 门禁 FAILS 以输出文件中 ^FAIL<TAB> 开头的行数为准（注意 FAILS= 行本身不计）。Python 以 fails 作退出码；脚本自检 FAIL 行数 = FAILS 且 FAILS = 0。

## 2. 输入事实（规划者只读核实；执行者须用脚本按原始文件复核，不符就照实写"规划者事实有误"）
- M1 总表 1302 行 = M1b 830（EFFECTIVE_M1B_R8_M1b3.tsv，F2 415 + F3 415）+ M1c 472（VERDICT_M1C_R8_M1c3.tsv，F2 236 + F3 236）。M1_SUMMARY_R8_M1c4.tsv 合计 MATCH 1252、NOT_REACHED_AS_EXPECTED 44、NOT_RUN_AS_EXPECTED 6、MISMATCH 0。
- F3 侧：M1b 415 行 = MATCH 390 + NOT_REACHED_AS_EXPECTED 22 + NOT_RUN_AS_EXPECTED 3（G2c_control）；M1c 236 行全 MATCH（G5 177、G6 25、G6c 18、CTRL_AUX 16）。
- F3 侧用到的驱动族（从 PREREG_SUPP 与 DRIVER_RUN_RECORD 粗计）：d003-F3-plain、d003plan-F3-plain、r6bstate-F3-dbg、r6bseam-seamF-F3、r6bseam-fmmret-F3、twice-*-F3（约 15 个以上），可能还有 polyinj、init、dual、layers 等。R9 M0 的 DRIVER_MAP_F3_F4_R9.tsv 只有 16 族；twice-* 不在其中，r6bseam-fmmret 对应的 F4 驱动未核实。
- F3→F4 的源码差异只在 S4.cpp 1760–1774（LINEMAP_F3_F4_S3R5.tsv；1774 之后行号 +13）。

## 3. 用户裁决（start 门禁通过后，由 append_rulings_r9m1.py 按 §1-8 追加，5 列，编号从现行 RULINGS 的最大 U 号之后续编；下文以 U306–U311 示意，如有冲突以实际续号为准）
- U306：R9 M1 只在 F4 上重跑 M1 的 F3 侧行（M1b 415 + M1c 236 = 651，以脚本复核数为准）。F2 树未变，F2 侧行不重跑，引用 r8m1b3/r8m1c3 的正式判定并核对驱动 sha256（同 U292 的处理）。合并后总表须断言 = 1302。
- U307：预注册规则。逐行取 F3 的有效行（M1b 用 EFFECTIVE_M1B_R8_M1b3，M1c 用 VERDICT_M1C_R8_M1c3 对应的冻结预注册），tree→F4，driver→F4 对应驱动，sha 字段换为 F4 产物，point_id 的 -F3 后缀改为 -F4，其余 exp_*（含 NOT_REACHED_AS_EXPECTED、NOT_RUN_AS_EXPECTED 与 I1–I6）原样保留。状态 INFLUENCED，basis 写"R9 M1 regression of <F3 point_id>"。不得因 F4 结果改期望。
- U308：S3R5 改动的影响清单。运行前用脚本列出 F3 侧所有"注入点或其 K 映射帧落在 Simulation_InitSolution（F3 行 1754–1774 区间）"的行，输出 IMPACT_S3R5_R9M1.tsv。这些行的期望不得按 F3 原样照抄：按 U293 的 SOLN 规则单列预注册，或标 CITED_M2 并引用 R9 M2/M2b 的判定（二选一，逐行写明）。没有这类行时写"0 行"并附脚本输出。
- U309：K 继承。凡带计数注入的组（S4FMM_NTH、init:K、aligned:K、win:K、twice 的 plan/exec/malloc-K 等），按 U300 规则在 F3、F4 上各跑一次无注入的 gdb 映射：两边命中总数相等；每次命中带大小或计数器 id 与 S4 帧（行号经 LINEMAP 映射）；取不到 S4 帧时用 bt 8 向外找。R9 M0/M2b 已证明的组直接引用（列出组 id 与证据文件、行号），不重跑；新组才跑。HIT 等价表须分开计 BOTH_EMPTY 与 NONEMPTY_IDENTICAL。k_max=1 且取不到序列的组可按 U303 用 HIT 行等价替代，条件是该组注入点两遍都是 NONEMPTY_IDENTICAL。任一组 DIVERGENT：该组的行不进入正式运行，列入"需用户裁决"。
- U310：装置对等。F4 缺的驱动（至少 twice-* 系列，以及 r6bseam-fmmret 若无对应驱动）在 $EV/build 下从 F4 导出（git archive，经 safe_run）重新构建。编译/链接命令行去掉树路径后与 F3 对应驱动逐条相同（BUILD_OPTION_DIFF_R9M1.txt，差异 0 项）；每个库的告警数等于 F3 对应库。已存在的 F4 产物不重编，只核 sha256。
- U311：执行顺序与停止。start 门禁 → 裁决追加与记录提交 (i)（任务书、RULINGS、驱动清单、影响清单、K 证明、预注册与其 sha256 及 UTC 时间戳）→ 阳性对照 → 冒烟（每组 × 每驱动至少 1 行，单遍）→ 正式两遍 → 判定 → 合并总表 → 收尾提交 (ii)。冒烟出现 MISMATCH、GDB_DIVERGENT 或 INVALID 时停在冒烟，只分诊（核对崩溃帧与日志），不改期望，不进正式运行。正式运行中的 MISMATCH 或 FLAKY 照实记录，只分诊，不重跑覆盖。

## 4. 步骤
- S-A 门禁：新建 gate_r9m1.sh 与 gate_check_r9m1.py，以已提交的 gate_r9m2c.sh、gate_check_r9m2c.py 为蓝本复制修改，原件不动，差异写入 RUNNER_DIFF_R9M1.txt。start 与 end 各一次；allow 文件新建为 gate_allow_r9m1_{start,end}.txt。
- S-B 装置：
  1. driver_inventory_r9m1.py → DRIVERS_F3_SIDE_R9M1.tsv：从两份 F3 有效表与 r8m1b3/r8m1c3 运行记录提取 F3 侧全部驱动名与 sha256，逐个映射到 F4（已有 / 需构建 / 无法映射）。"无法映射"非 0 即停下列入报告。
  2. build_r9m1.py：只构建"需构建"项；输出 BUILD_R9M1.tsv、BUILD_OPTION_DIFF_R9M1.txt、WARN_COUNT_R9M1.tsv。
  3. noinj_r9m1.py：每个新建驱动在无注入下运行（每个 env 组合各一次），rc 记事实，sanitizer 报告数记事实。
- S-C K 证明与影响清单：k_inherit_r9m1.py → K_INHERIT_R9M1.tsv、K_INHERIT_RAW_R9M1.txt（含"引用已有证据"的行）；impact_s3r5_r9m1.py → IMPACT_S3R5_R9M1.tsv。
- S-D 预注册：prereg_r9m1.py → PREREG_M1_F4_R9M1.tsv（+ .sha256 + _TIMESTAMP_UTC.txt）与 PREREG_M1_CITED_F2_R9M1.tsv。断言：F4 行数 + CITED 行数 = 1302；F4 行按组 × effective_verdict 的计数等于 F3 侧计数（影响清单中的行单列）。预注册前须核对判定引擎实际读取了哪些 exp_* 列（exp_I1–I6 只在 state_analyzer 非空时判，exp_san 的适用行），把"引擎不读的期望列"列入 ENGINE_COLUMNS_R9M1.txt。记录提交 (i)：start 门禁 FAILS=0 后提交，信息末尾写 awaiting user review。
- S-E 阳性对照：posctrl_r9m1.py 必须调用正式比较/判定脚本（支持输出路径参数），用目标行的真实配置：① 把 F3 冻结结果当"运行结果"输入，期望 DIFFS=0；② 人为篡改 1 个 rc1 与 1 个 I 项的副本（放 $EV/tmp），期望恰好检出 2 处。
- S-F 冒烟与正式运行：run_smoke_r9m1.py、run_formal_r9m1.py（两遍，pass1/pass2 分目录）。每条运行记录驱动 sha256，须与预注册相同。
- S-G 判定与合并：verdict_r9m1.py → VERDICT_M1_F4_R9M1.tsv（逐行 F4 vs 预注册，pass1/pass2 一致性，FLAKY/GDB_DIV 单列）；compare_f3_f4_r9m1.py → F3_F4_EQUIV_R9M1.tsv（逐行逐字段：rc1、rc2、rc3、hit、class、I1–I6、env；HIT 行 BOTH_EMPTY 与 NONEMPTY_IDENTICAL 分开计）；summarize_m1_r9m1.py → M1_SUMMARY_F4_R9M1.tsv（断言 F4 侧 + CITED F2 侧 = 1302，各节和 = 各表行数之和）。
- S-H 收尾：
  - 事件表：events_r9m1.py 读 m1 的 safe_run.log，每条日志条目一行；所有重跑（含 posctrl 多次）都要列。必须在最后一次 safe_run 写入之后再跑一遍；断言总行数 = 日志条目数 + 裸写行数（应为 0）。
  - 报告 P05_S4R9_M1_REPORT.md 结构：门禁（FAIL 行数与 FAILS 一致性）→ 旧 Task014 误投递说明 → 裁决 → 装置 → K 证明 → 影响清单 → 预注册 → 阳性对照 → 冒烟 → 正式结果 → F3/F4 等价 → 总表 → 事件两张表 → 需用户裁决（没有就写"无"）。结尾写"本轮已完成/未完成 R9 M1 范围，等待用户审核"，附 git log -1 与 git status --short。
  - STATE.md（不超过 8192 字节）：当前轮次改为 R9 M1；关键数字加一行；开放项写明下一步为 M3。
  - 小表复制到 registries/s4r9/M1/（不改名），写 SHA256SUMS.txt 并逐个比对；证据目录写 SHA256SUMS.txt（导出树、库、驱动只记 sha256）。
  - end 门禁 FAILS=0 且自检一致后做收尾提交 (ii)，信息末尾写 awaiting user review。提交后只输出 git log -3 --oneline 与 git status --short。

## 5. 措辞
- 不写"100%""完全""严格""彻底""证实""精确""全面闭环"。REPORTED_FAILURE 只表示返回码非零。B 列不是修复证据。
- 没有日志依据的原因写"原因未查明"。规划者事实与原始文件不符时，照实写"规划者事实有误"。

## 6. 硬停止条件
1. 开工门禁任一项不符。
2. 任何追加脚本的前缀断言失败；RULINGS 前缀不等于 3bb6072 版本，或 U 编号重复。
3. 越界写入、safe_run 之外的写入、改动 S4/ 或已提交文件、写入其他轮次证据目录、改写 git 历史。
4. 门禁出现 FAIL：停下写报告，不得改门禁后重跑来消除。
5. 驱动"无法映射"非 0，或 BUILD_OPTION_DIFF 非 0 项：停在装置阶段，写报告。
6. 冒烟出现 MISMATCH、GDB_DIVERGENT 或 INVALID：停在冒烟，只分诊。
以下不是硬停止：K 组 DIVERGENT 或 SUBSTITUTE_NOT_MET。这些组的行不进入正式运行，照实记录，列入"需用户裁决"，其余组继续。
