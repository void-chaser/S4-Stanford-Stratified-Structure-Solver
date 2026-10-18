# P05-S4 R9 M1 第三修正轮任务书（轮次标识 r9m1r4）——只读复核与重新收尾，不运行任何 S4 驱动

## 0. 身份与边界
- P05-S4 子轮次 R9 的 M1 第三修正轮（不是新阶段，不是 M3）。证据目录 checkpoints/p05/evidence/p05-s4r9/m1r4；小表目录 checkpoints/p05/registries/s4r9/M1R4/；报告 checkpoints/p05/P05_S4R9_M1R4_REPORT.md；任务书原文经 safe_run 存为 checkpoints/p05/briefs/P05_S4R9_BRIEF_M1R4.md。
- 目的：①把 r9m1r3 的流程偏差（H-1..H-8）按事实登记为勘误；②用新写的独立脚本，以只读方式从 m1r3 冻结的正式事实复算并核证 M1 结果；③按单向顺序重新收尾，门禁真正执行全部断言。
- 本轮**不运行任何 S4 驱动、gdb 或编译**，不调用任何历史脚本（含 r9m1r3 的全部脚本，U233）；需要其逻辑时，复制成本轮新脚本再改。
- 不改 S4/、判定器、历史装置以及任何已提交文件（含 registries/s4r9/M1/、M1R2/、M1R3/ 和 r9m1r3 的全部脚本）。p05-s4r9/m1、m1r2、m1r3 证据目录只读。新脚本放 testing/d003/stage_s4r9/，文件名带 r9m1r4。
- 禁止 git commit --amend、rebase。报告不写收尾提交哈希。不得宣布阶段完成，不得询问是否签收。
- 开工先读：AGENTS.md → STATE.md → 本任务书 → P05_S4R9_M1R3_REPORT.md → P05_S4R9_BRIEF_M1R3.md → registries/s4r9/M1R3/ → registries/s4r9/ERRATA_9.txt。
- 开工门禁：HEAD = 4e9ff8b4bcce3bc2bf9b8098059c381c8c1e4810；HEAD:S4 = 589e15eb11fcb04e031b524f25a443e7921946cf；判定器 sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb；git status --short 为空；/tmp 顶层只读快照（条目数与 sha256）；RULINGS.tsv = 133250 字节、sha 78350022…、最大 U 号 U322；ERRATA_9.txt = 25685 字节、sha a2c70924…、最后一条 E9-28；registries/s4r9/M1R3/SHA256SUMS.txt（sha c25e998a…）26 项全部 OK；s3r5、M0、M2、M2b、M2c、M1、M1R2 各清单全部 OK。任一不符即停。

## 1. 写入与执行纪律
1. 每条含写入的命令开头：REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r4; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"，然后经 sh testing/d003/safe_run.sh p05-s4r9/m1r4 -- <命令>。
2. 【新】仓库内的一切文件创建或修改（脚本、报告、STATE、任务书存档、allow 列表）都必须经 safe_run 完成，**不得使用编辑器的写入或编辑工具直接写仓库文件**。固定写法：safe_run -- python3 -I -B -c "import base64; open('<仓库相对路径>','wb').write(base64.b64decode('<内容>'))"。每次改写都换新文件名（_v2、_v3），不得覆盖已经执行过的文件。
3. 【新】写入目标只能在 $EV/、testing/d003/stage_s4r9/（文件名带 r9m1r4）、checkpoints/p05/（本轮目录、STATE、报告、RULINGS、ERRATA_9 追加）之下。**任何时候写到其他轮次的证据目录都是硬停止：立即停下，不"恢复"，不继续。**脚本里的 EV 等路径常量开工前先 grep 核对，不得残留 m1r2、m1r3。
4. 两个时期：
   - 试跑期（记录提交 (i) 之前）：允许任意次试跑，输出只放 $EV/shakedown/<序号>/，每次都经 safe_run。**end 门禁必须在试跑期以 end 模式对本轮真实目录至少跑通一次**，输出到 shakedown/，结果写进报告的试跑摘要；不通过就换文件名改脚本，直到所有断言都执行完、没有异常退出为止。
   - 冻结期（(i) 之后）：只能调用 FROZEN_SCRIPTS_R9M1R4.tsv 中列出的脚本，且每个只调用 1 次；不得新建或改写 testing/d003/ 下的任何文件。清单至少包括：recert、kmatch、unlogged、summarize_recert、report_check、copy_registries、events、sha_sums、gate、finalize。
5. 冻结期出现脚本错误、断言失败或核证不一致：不修脚本、不重跑；保留已产出的文件，停下写报告，列入"需用户裁决"。
6. 收尾固定顺序（每步只调用一次，中间不插任何其他命令，包括内联 cp）：报告与 STATE 落盘（经 safe_run）→ report_check → copy_registries → events → sha_sums → end 门禁 → finalize → 收尾提交 (ii)。门禁 FAIL 时，只允许 finalize 之后再用**一条** safe_run 命令给报告追加附录（追加，不改正文），然后提交；其余一律不动。
7. 措辞：没有日志依据的原因写"原因未查明"；规划者给的事实与原始文件不符时，照实写"规划者事实有误"。

## 2. 输入事实（规划者只读核实；执行者必须用 audit 脚本按原始文件复核，逐条写"属实"或"规划者事实有误"）
- H-1 写入他轮证据目录：m1r3 safe_run.log 中，gate_r9m1r3_v2.sh start 在 03:34:41Z 和 03:36:26Z 运行了两次。evidence/p05-s4r9/m1r2/tmp/ 下的 py_checks_start.txt、status_now_start.txt、tmp_snap_start.txt 的 mtime 分别为 14:36:08、14:36:08、14:34:41（+1100），落在这个时间窗内。它们现在的 sha 与 m1r2/SHA256SUMS.txt 第 8136、8138、8142 行一致。报告说"立即执行恢复并还原原始文件"，但 m1r3 日志里没有任何恢复命令。核实：写入的来源命令、恢复用的是什么手段（未查明就写"原因未查明"）。
- H-2 收尾产物在日志外被重新生成：m1r3 的 EVENTS_R9M1R3.tsv（证据与 registries 两份相同，sha 17f9ee9a…）和证据 SHA256SUMS.txt 的 mtime 是 15:42:45/15:42:46（+1100），而日志里最后一次 events 在 04:37:57Z、sha_sums 在 04:38:25Z，04:38:25Z 到 04:44:56Z 之间没有日志记录。EVENTS 的 log_line 是跳过空行后的连续编号（日志物理第 6 行为空行，表中第 6 行却是 "REPO = …"），而 events_r9m1r3.py（冻结版）用 enumerate 物理行号。核实：用冻结版 events 的同一逻辑，对 m1r3 safe_run.log 的前缀重算（写成本轮新脚本，输出到 $EV），逐行比对已提交的 EVENTS。
- H-3 截断哈希标注：m1r3 SHA256SUMS.txt 第 2 行写"up to line 143: 94dc58e3…"，这个 sha 实际等于 safe_run.log 前 162 个物理行的 sha。
- H-4 end 门禁未执行关键断言：gate_check_r9m1r3_v5.py 在 end 模式下读 FROZEN_SCRIPTS_R9M1R2.tsv（第 290、292 行），之后引用 frozen_map 时报 NameError。GATE_R9M1R3_end.txt 里没有 POST_I_CALL_COUNT_*、POST_I_STAGE_SCRIPTS_ALL_FROZEN、EVENTS_COVERS_ALL_LOGS_BEFORE_GATE、EVIDENCE_SHA256SUMS_ALL_OK 这几行。STARTF（gate_r9m1r3_v5.sh 第 37 行）指向 GATE_R9M1R3_start.txt（ALLOW_START sha 0de756e8…，TMP 两项为空）。
- H-5 报告失实：P05_S4R9_M1R3_REPORT.md 第 126 行说 v5"绑定 start_v4 基线"，与 H-4 不符。日志第 82 行（物理行号以脚本为准）`gate_r9m1r3_v4.sh start _v5` 产出 GATE_R9M1R3_start_v5.txt，FAILS=1（STRAY_BASELINE_NOT_PRESENT_BEFORE_START），报告没有披露。
- H-6 收尾步骤重复：report_check 在 04:35:20Z、04:36:15Z、04:36:52Z 共 3 次；events 在 04:37:30Z、04:37:57Z 共 2 次；04:38:11Z 有一条内联 cp（EVENTS 复制进 registries）。任务书 r9m1r3 §1-6 要求每步一次。
- H-7 日志外写入：16a7897..4e9ff8b 新增的 testing/d003/stage_s4r9/*r9m1r3* 文件，以及 P05_S4R9_M1R3_REPORT.md（mtime 15:47:10，晚于 finalize 的 04:46:06Z）、STATE.md（15:34:03），大部分在 m1r3 日志里没有对应的写入命令（日志共 61 条带时间戳的记录）。逐个文件列出：mtime、对应的日志行（没有就写"无"）。
- H-8 K 命中数口径：K_COUNT_R9M1R3.tsv 与 K_INHERIT_R9M1R2.tsv 中有 13 组命中数不同（KGRP-M1-007/012/014：16 对 6；016/018/021/023/025：17 或 16 对 3；017/022：17 对 4；019/024/026：13 对 4）。规划者推测：k_inherit_r9m1r2.py 第 60–72 行只截取 k_max+2 次断点（旧表的 hits 是截取数，不是总数），K_COUNT 用 gdb 计数器数的是总数。须用脚本按 k_max 逐组核对这个推测。

## 3. 用户裁决（start 门禁通过后，由 append_rulings_r9m1r4.py 按"新文件 = 旧文件 + 新行"追加，5 列，从 U323 起）
- U323：r9m1r3 的物理事实（m1r3/runs/formal 下两遍 FORMAL_FACTS，sha 090797d8… 和 85b1f158…）不重跑。r9m1r3 的 VERDICT、F3_F4_EQUIV、M1_SUMMARY 在本轮复核（S-D）通过后成为 M1 的有效结果，本轮报告和 STATE 作为它们的核证。复核不一致时，以本轮独立复算的结果为准，并列入"需用户裁决"。
- U324：H-1 写入 m1r2 证据目录属于硬停止违规，按已披露接受，不追认为合规。现存 3 个文件的内容经本轮核对等于 m1r2 清单记录值，不再处理。
- U325：H-2、H-3、H-6、H-7 按事实登记为勘误。r9m1r3 已提交的 EVENTS、SHA256SUMS 不改，由本轮按冻结逻辑重算的 EVENTS_RECALC_R9M1R3.tsv 和 SHA_RECHECK_R9M1R3.tsv 作为更正件。
- U326：r9m1r3 的 end 门禁没有执行的那几项断言，由本轮 recert 脚本以只读方式补做，结果写进 RECERT_R9M1R3.tsv。GATE_R9M1R3_end.txt 保持原样。
- U327：K 的命中数以 K_COUNT_R9M1R3（总数）为准。K_INHERIT_R9M1R2 中 hits 列的含义按 H-8 的复核结果，在 K_RECON_R9M1R4.tsv 里说明。

## 4. 步骤
- S-A 门禁：新建 gate_r9m1r4.sh、gate_check_r9m1r4.py。要求：
  - 每项检查都包在 try/except 里，异常时写一行 "FAIL\t<名称>\tCHECK_CRASHED\t<异常>" 后继续检查下一项，不得因异常提前退出；
  - FAIL 数以输出文件中 ^FAIL\t 的行数为准，并且等于退出码（封顶 255）；
  - STARTF、清单名、轮次常量集中写在文件头，并由门禁自检一项"常量中不含 m1r2、m1r3"；
  - end 模式至少断言：(i) 之后各冻结脚本调用次数 = 1（按 safe_run.log 的 cmd= 字段计数）；(i) 之后没有写入 testing/d003；FROZEN 清单中每个文件的 sha 与 (i) 时一致；(i) 已提交的文件在收尾时未被修改；EVENTS 行数与每行的 log_line 等于冻结逻辑对"门禁之前的日志物理行"重算的结果；证据 SHA256SUMS 全部 OK，且截断哈希的行号与实际一致；本轮 mtime 晚于开工门禁的仓库文件都能在日志中找到对应写入（UNLOGGED_SELF = 0）；他轮证据目录（m1、m1r2、m1r3）中没有 mtime 晚于本轮开工门禁的文件；registries/s4r9/M1、M1R2、M1R3 与 HEAD 4e9ff8b 相同。
- S-B 取证（只读）：audit_r9m1r3_r9m1r4.py 复核 H-1..H-8，输出 AUDIT_R9M1R3_R9M1R4.tsv（每项：事实、日志物理行号或文件行号、复核结论）。unlogged_r9m1r3.py 对 16a7897..4e9ff8b 中新增或修改的每个文件，以及 m1、m1r2、m1r3 证据目录中 mtime 落在 r9m1r3 时间窗内的每个文件，与 m1r3 日志关联，输出 UNLOGGED_WRITES_R9M1R3.tsv。
- S-C 勘误：append_errata_r9m1r4.py 从 E9-29 起追加，至少覆盖 H-1..H-8，以及 r9m1r3 报告中与事实不符的陈述（逐条列报告行号：第 126 行"绑定 start_v4"、§5 与 §12.2 关于"恢复"的说法、附录 A 只写了"3 项 FAIL"却没说明哪些断言没有执行）。
- S-D 独立复核 recert_r9m1r4.py：只读 m1r3 的冻结产物，不调用 m1r3 的任何脚本，逻辑自己实现：
  1. FORMAL_FACTS pass1/pass2 sha 与 U323 一致，各 651 行；
  2. 按 PREREG_M1_F4_R9M1R3.tsv（sha a7f418de…）独立复算 651 行判定（两遍一致性；G5/G6 两遍的 I1–I6；U319 的 NOT_RUN 规则），逐行比对已提交的 VERDICT_M1_F4_R9M1R3.tsv；
  3. 独立复算 F3/F4 等价：F3 侧 G6 取 registries/s4r8/M1c/r8m1c3/M1C_F3_RESULTS_R6c_SEAM.tsv，G5 取 M1C_F3_RESULTS_R6c_STATE.tsv。断言 G6 的 25 行、G5 的 177 行全部参与 I1–I6 比对；HIT 分开计 NONEMPTY_IDENTICAL、BOTH_EMPTY、NOT_RUN。逐行比对已提交的 F3_F4_EQUIV；
  4. 总表断言：F4 651 + CITED F2 651 = 1302，各节和 = 各表行数之和，NOT_RUN 单列；与已提交的 M1_SUMMARY 一致；
  5. 补做 r9m1r3 门禁没有执行的断言：(i)=289237d 之后各冻结脚本的调用次数、(i) 之后没有写入 testing/d003、FROZEN_SCRIPTS_R9M1R3 中 17 项 sha 不变；
  6. 输出 RECERT_R9M1R3.tsv（每项：断言、期望、实际、结论）。另输出 EVENTS_RECALC_R9M1R3.tsv（按冻结版 events 逻辑重算）和 SHA_RECHECK_R9M1R3.tsv（m1r3 证据清单重新校验，加上截断哈希的正确行号）。
  - 阳性对照：在试跑期用篡改副本（放 $EV/shakedown/posctrl/）验证 recert 能检出：VERDICT 改 1 行、EQUIV 改 1 行 G6 I3、FORMAL_FACTS 改 1 行 rc1、EVENTS 删 1 行，期望恰好各检出 1 处。冻结期再用同一个 recert 脚本做 1 次正式对照（posctrl 模式），结果写 POSCTRL_RECERT_R9M1R4.txt。
- S-E K 对账 kmatch_r9m1r4.py：逐组核对 H-8 的推测（旧 hits 是否等于 min(总数, k_max+2)），以及 K_COVERAGE 416 + 235 = 651。输出 K_RECON_R9M1R4.tsv。
- S-F 汇总 summarize_recert_r9m1r4.py：输出 M1_RECERT_SUMMARY_R9M1R4.tsv（核证项数、一致数、不一致数）。
- S-G 收尾按 §1-6。报告结构：门禁 → H-1..H-8 复核 → 裁决与勘误 → 试跑期摘要（每次试跑：目录、改了什么、门禁 end 模式试跑结果）→ 独立复核结果 → K 对账 → 未记录写入清单 → 事件两张表（表一：越界写入尝试，含 H-1 补登；表二：工具与脚本事件）→ 需用户裁决（没有就写"无"）。结尾写"本轮已完成/未完成 R9 M1 第三修正范围，等待用户审核"，附 git log -1 与 git status --short。
- STATE.md（≤ 8192 字节）：当前轮次改为 R9 M1R4；S4R9 M1R3 那一行注明"物理事实有效，经 M1R4 核证（U323）"；关键数字加一行；开放项写明下一步为 M3（make test、Python/Lua 端到端、U38）。

## 5. 执行顺序
start 门禁 → 取证复核 H-1..H-8 → 裁决与勘误追加 → 试跑期（recert/kmatch/unlogged/summarize 跑通；recert 篡改对照跑通；end 门禁以 end 模式试跑，所有断言执行完、没有异常退出）→ 冻结清单 → start 门禁复核 → 记录提交 (i) → 冻结期：unlogged → recert（posctrl 模式）→ recert（正式）→ kmatch → summarize_recert → 收尾（§1-6）→ 收尾提交 (ii)。recert 的两种模式视为两个清单项，各调用 1 次。

## 6. 硬停止条件
1. 开工门禁任一项不符。
2. 追加脚本的前缀断言失败，或 U 号、E 号重复。
3. 越界写入；safe_run 以外的写入（含编辑器工具）；写他轮证据目录；改 S4/ 或已提交文件；改写 git 历史；运行 S4 驱动、gdb 或编译。
4. 冻结期调用清单外的脚本、改写任何 testing/d003 文件、任一冻结脚本调用超过 1 次。
5. 冻结期脚本报错、核证不一致或阳性对照失败（照实记录，不修不重跑）。
6. 门禁出现 FAIL 或 CHECK_CRASHED（按 §1-6 处理）。
