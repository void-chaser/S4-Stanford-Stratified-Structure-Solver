# P05-S4 R9 M1 第二修正轮任务书（轮次标识 r9m1r3）

## 0. 身份与边界
- P05-S4 子轮次 R9 的 M1 第二修正轮（不是新阶段，不是 M3）。证据目录 checkpoints/p05/evidence/p05-s4r9/m1r3；小表目录 checkpoints/p05/registries/s4r9/M1R3/；报告 checkpoints/p05/P05_S4R9_M1R3_REPORT.md；任务书原文经 safe_run 存为 checkpoints/p05/briefs/P05_S4R9_BRIEF_M1R3.md。
- 目的：①登记 r9m1r2 自身的流程偏差；②修正两处事实口径（G2c_control 未运行行被填成 0/CONTROL_OK；G6 的 I1–I6 未进入判定与比对）；③在"试跑 → 冻结 → 只调用一次"的纪律下重新取得 M1 F4 的 651 行事实。
- 不改 S4/、判定器、历史装置以及任何已提交文件（含 r9m1、r9m1r2 的全部脚本与 registries/s4r9/M1/、M1R2/）。p05-s4r9/m1 与 m1r2 证据目录只读。新脚本放 testing/d003/stage_s4r9/，文件名带 r9m1r3。
- 禁止 git commit --amend、rebase 等改写历史的操作。报告不写收尾提交哈希。不得宣布阶段完成，不得询问是否签收。
- 开工先读：AGENTS.md → STATE.md → 本任务书 → P05_S4R9_M1R2_REPORT.md → P05_S4R9_BRIEF_M1R2.md → registries/s4r9/M1R2/ → registries/s4r9/ERRATA_9.txt。
- 开工门禁：HEAD = 16a789791f792f8814dc8896e03fb1b3f75c6294；HEAD:S4 = 589e15eb11fcb04e031b524f25a443e7921946cf；判定器 sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb；git status --short 为空；/tmp 顶层只读快照（条目数与 sha256）；RULINGS.tsv = 130798 字节、sha 84d3871c…、最大 U 号 U317；ERRATA_9.txt = 19322 字节、sha 0e416f01…、最后一条 E9-20；registries/s4r9/M1R2/SHA256SUMS.txt 全部 OK。任一不符即停。

## 1. 写入与执行纪律（沿用 r9m1r2 §1 第 1–9、12、13 条，以下替换或新增）
1. 每条含写入的命令开头：REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"，然后经 sh testing/d003/safe_run.sh p05-s4r9/m1r3 -- <命令>。没有例外：编译试验、gdb 试验、临时篡改副本都算。
2. 【新】两个时期：
   - 试跑期（记录提交 (i) 之前）：允许任意次试跑、改写、调试，输出只放 $EV/shakedown/<序号>/，每次都经 safe_run 并进事件表。试跑结果不是正式事实，不进入任何总表。
   - 冻结期（(i) 之后）：只允许调用 FROZEN_SCRIPTS_R9M1R3.tsv 中列出的脚本；不得新建、改写任何 testing/d003/ 下的文件（也不得新建 _R2/_R3 变体）。冻结清单必须包括冻结期会调用的全部脚本：posctrl、smoke、formal、verdict、compare、cmp_vs_r9m1r2、summarize、copy_registries、events、sha_sums、gate、report_check。
3. 【新】已执行过的脚本不得原地改写（冻结期绝对禁止；试跑期改写须换新文件名并进事件表）。
4. 【新】调用次数：冻结期 posctrl、smoke、formal、verdict、compare 各只调用 1 次。end 门禁从 $EV/safe_run.log 按 (i) 时间点之后的 cmd= 字段计数并断言等于 1；同时断言 (i) 之后没有任何"写入 testing/d003/"的命令（匹配 open('testing/d003/ 与重定向目标）。
5. 【新】冻结期出现脚本错误、断言失败、MISMATCH 或 FLAKY 时：不修脚本、不重跑；保留已产出文件，停下写报告，列入"需用户裁决"。
6. 【新】收尾固定顺序（每步各一次）：summarize → cmp_vs_r9m1r2 → 报告与 STATE 落盘 → report_check（禁用词、报告引用的小表都在 registries、报告中的数字逐项等于源表）→ copy_registries → events（覆盖到此刻 safe_run.log 的最后一条）→ sha_sums（证据目录全部非二进制文件；safe_run.log 单独记录"截至第 N 行的 sha256"）→ end 门禁（只跑一次；断言 events 行数 = 门禁之前的日志条目数，断言 SHA256SUMS 全部 OK）→ finalize（冻结脚本，只做两件事：把门禁文件复制进 registries、重写 registries/SHA256SUMS.txt 并逐个比对）→ 收尾提交 (ii)。门禁之后不得再改报告、STATE、事件表。门禁 FAIL 就停下写附录，不改门禁、不重跑。
7. 措辞：REPORTED_FAILURE 只表示返回码非零；没有日志依据的原因写"原因未查明"；规划者事实与原始文件不符时照实写"规划者事实有误"。

## 2. 输入事实（规划者只读核实；执行者须用脚本按原始文件复核，逐条写"属实/规划者事实有误"）
- G-1 冻结与实际调用不一致：(i) 提交 a413db0 时间 01:51:09Z。m1r2 safe_run.log 中，L29 写入 compare_f3_f4_r9m1r2_R2.py，L30 写入 posctrl_r9m1r2_R2.py，L33 写入 run_smoke_r9m1r2_R2.py，L34 写入 run_formal_r9m1r2_R2.py，L39 写入 run_formal_r9m1r2_R3.py，全部在 (i) 之后。正式事实来自 L40 的 _R3，冒烟来自 L37 的 _R2，等价比对来自 L44 的 compare _R2。FROZEN_SCRIPTS_R9M1R2.tsv 中的 run_formal/run_smoke/compare/posctrl 原件没有产出最终结果。_R2/_R3 相对原件的改动含：inj_call 缺省 None→1、classify 返回值改为 3 元组、清除继承的 S4FMM_* 环境变量、跳过 S4FMM_INJECT=none、比对新增 NOT_RUN 跳过分支。
- G-2 多次调用：L28 posctrl、L31 posctrl_R2；L32 smoke、L35/L37 smoke_R2；L38 formal_R2（runs/formal 下无 FORMAL_FACTS 文件，原因未查明，规划者推测与 RESULTS_R6c_STATE 列名 id/point_id 有关，须核实）、L40 formal_R3（runs/formal_R2）。报告 §8.1"正式运行脚本仅调用 1 次"与日志不符。
- G-3 原地改写后重跑：L36 原地改写 run_smoke_r9m1r2_R2.py 后 L37 重跑；L43 原地改写 compare_f3_f4_r9m1r2_R2.py 后 L44 重跑并覆盖 F3_F4_EQUIV_R9M1R2.tsv。L31 的阳性对照用的是 L29 版的 compare，没有覆盖 L43 版。
- G-4 m1r2 本轮裸写候选（mtime 与日志无对应）：$EV/tmp/test_plain_g、test_dbg_g、gdb_test.cmd、count.cmd、d003-F3-test-dbg、d003plan-F3-test-dbg、d003plan-F4-test-dbg（本地时间 12:31–12:35，即 01:31–01:35Z，位于日志 L13 01:28:30Z 与 L14 01:37:26Z 之间）；posctrl_tampered_pass1/pass2/verdict/agg.tsv、posctrl_case3_verdict/agg.tsv（01:49:05Z，早于 L24 写入 posctrl_r9m1r2.py 的 01:49:27Z）。报告 §11 写 0。
- G-5 收尾顺序：events_r9m1r2.py 在 L52 运行，日志共 65 条，L53–L65 未进事件表；end 门禁在 L53/L56/L60/L63 共运行 4 次，中间 L54、55、57、58、59、61、62、64、65 是内联 exec，改写了报告 §13、registries 与 SHA256SUMS。现在对 m1r2/SHA256SUMS.txt 做 sha256sum -c，有 2 项 FAILED（safe_run.log、tmp/status_now_end.txt），GATE_R9M1R2_end_R4.txt 不在清单内。
- G-6 G2c_control 填值：run_formal_r9m1r2_R3.py:90-97 对 f3_effective_verdict=NOT_RUN_AS_EXPECTED 的 3 行不运行驱动，却填入 rc=0、rc1=0、rc2=0、class=CONTROL_OK。预注册中这 3 行 exp_class=NOT_RUN_REGISTRY_ERROR、env=NOT_RUN。报告 §9.2 把 0/CONTROL_OK 称为"本轮事实"。
- G-7 G6 不变量未判：verdict_r9m1r2.py:132-136 只对 G5 判 I1–I6；compare_f3_f4_r9m1r2_R2.py:91-132 的 F3 侧 G6 读 M1C_F3_STATE_SEAM_R6c_pass1.tsv，I1–I6 全为 "-"，而比对在任一侧为 "-" 时跳过。F3_F4_EQUIV 中 G6 25 行 f3_I* 全为 "-"、f4_I* 有值。F3 侧的 I 值在 registries/s4r8/M1c/r8m1c3/M1C_F3_RESULTS_R6c_SEAM.tsv（如 R4-ACF1-F 两遍均为 HOLD×6）。
- G-8 K 的命中数核对：build_kmap_r9m1r2.py:175-184 只在 8 个模式下比较 plain 与 kmap 的 malloc 命中总数，没有按 26 个 d003/d003plan 组各自的 env 与断点符号比较。K_INHERIT_R9M1R2.tsv 的 m1_points_count 合计 416，与 651 行的对应关系未列出。

## 3. 用户裁决（start 门禁通过后由 append_rulings_r9m1r3.py 按"新文件 = 旧文件 + 新行"追加，5 列，从 U318 起）
- U318：r9m1r2 的冻结后换脚本、多次调用、原地改写重跑、裸写、收尾顺序问题按事实登记为勘误（E9-21 起），不改 r9m1r2 已提交的文件。r9m1r2 的 VERDICT/F3_F4_EQUIV/M1_SUMMARY 降级为"参考结果二"，有效结果以 r9m1r3 为准。r9m1r2 的 K 继承结果（K_INHERIT_R9M1R2，k_inherit 只在 L16/L17 写入并运行一次）、预注册的期望列与 ENGINE_COLUMNS 可以引用，但须经 U321 补核。
- U319：未运行行一律记为未运行：rc/rc1/rc2/rc3/hit 为 "-"，class 为 NOT_RUN_REGISTRY_ERROR，verdict 为 NOT_RUN_AS_EXPECTED；不得填入任何数值或 CONTROL_OK。比对时这类行单列为 NOT_RUN，不计入 EQUIVALENT。
- U320：M1c G6 的 I1–I6 与 point_verdict 必须进入判定和 F3/F4 比对：F4 侧取本轮 RESULTS_R6c_SEAM 中两遍的值；F3 侧取 r8m1c3 的 M1C_F3_RESULTS_R6c_SEAM.tsv；期望取 PREREG_M1_F4_R9M1R2（或本轮新预注册）中的 exp_I1..I6。三方逐字段比对；G5 同理（F3 侧取 M1C_F3_RESULTS_R6c_STATE.tsv）。
- U321：K 补核：对 26 个 d003/d003plan 组，在各组自己的 clean_env 与断点符号下，用 gdb 分别数 plain 与 kmap 的命中数，要求相等（只读复用 m1r2/build 下的 kmap 驱动，核对 sha256 与 BUILD_KMAP_R9M1R2 一致）。另出 K_COVERAGE_R9M1R3.tsv：651 行每行所属的 K 组（或"不需要 K"及理由），组内点数之和与 416 对账。命中数不等的组列入"需用户裁决"，其点照常运行但在总表中单列。
- U322：执行顺序：start 门禁 → 取证复核 G-1..G-8 → 裁决与勘误追加 → K 补核 → 试跑期（新脚本全部写好，在 $EV/shakedown/ 下跑通全流程：posctrl、smoke、formal 全量、verdict、compare、summarize）→ 预注册与口径冻结 → 冻结清单 → start 门禁复核 → 记录提交 (i) → 冻结期：posctrl → smoke → formal → verdict → compare → 收尾（§1-6）→ 收尾提交 (ii)。冻结期每个脚本只调用一次。

## 4. 步骤要点
- S-A 门禁：新建 gate_r9m1r3.sh、gate_check_r9m1r3.py（以 r9m1r2 版为蓝本，差异写入 RUNNER_DIFF_R9M1R3.txt）。end 门禁新增断言：§1-4 的调用计数与"(i) 后无 testing/d003 写入"；FROZEN 清单每个文件的 sha 与 (i) 一致；冻结期 safe_run.log 中被调用的 stage_s4r9 脚本都在清单内；registries/s4r9/M1/ 与 M1R2/ 与 HEAD 16a7897 相同；events 覆盖门禁前全部日志行；证据 SHA256SUMS 全部 OK；FAIL 数以输出文件中 ^FAIL	 行数为准且等于退出码。
- S-B 取证（只读，产出放 $EV）：audit_r9m1r2_r9m1r3.py 复核 G-1..G-8，输出 AUDIT_R9M1R2_R9M1R3.tsv（每项：事实、日志行号/文件行号、复核结论）；从 m1r2 safe_run.log 的 base64 段还原 r9m1r2 全部脚本版本，写入 $EV/forensic/，输出 SCRIPT_VERSIONS_R9M1R3.tsv；对 m1r2 下全部文件做 mtime 与日志关联，输出 BARE_WRITE_AUDIT_R9M1R3.tsv。
- S-C 勘误：append_errata_r9m1r3.py 追加 E9-21 起，至少覆盖 G-1..G-8，以及 r9m1r2 报告中与日志不符的陈述（逐条列报告行号：§8.1 "仅调用 1 次"、§9.1 "I1..I6"、§9.2 "本轮事实 0/CONTROL_OK"、§11 "0"、§12 "无"）。
- S-D K 补核：kcount_r9m1r3.py → K_COUNT_R9M1R3.tsv、K_COVERAGE_R9M1R3.tsv。
- S-E 预注册：prereg_r9m1r3.py 以 PREREG_M1_F4_R9M1R2.tsv（sha 35333fd4…）为来源，只允许按 U319/U320 改动：G2c_control 期望保持 NOT_RUN；G6/G5 的 exp_I1..I6 原值保留。输出 PREREG_M1_F4_R9M1R3.tsv（+ .sha256 + _TIMESTAMP_UTC.txt）与 PREREG_VS_R9M1R2_DIFF_R9M1R3.tsv（逐行列出所有差异；期望列差异应为 0，若不为 0 逐行照实写）。CITED_F2 同理重新生成并核对驱动 sha256。ENGINE_COLUMNS_R9M1R3.txt 在 R9M1R2 版基础上只增加 U319/U320 两节，各自引用历史脚本文件与行号（verdict_m1c_r8m1c3.py 中 RESULTS 的读取与 I 列判定位置）；不能引用的按逐字比对。
- S-F 阳性对照（冻结期，只一次）：posctrl_r9m1r3.py 调用冻结的 verdict 与 compare：① F3 冻结事实作输入，期望 DIFFS=0；② 篡改副本（$EV/tmp/posctrl/，经 safe_run）：M1b G2b 一行 rc1、M1c G5 一行 I1、M1b 一行 rc2（该行合同要求比对 rc2）、M1c G6 一行 I3、M1b G2c_control 一行把 "-" 改成 0，期望恰好检出 5 处；③ 用 r9m1 旧预注册 3894d899 对照本轮正式事实，期望检出 22 行 G2b（数目以复核为准）。posctrl 必须在冒烟前运行，并覆盖冻结版 compare。
- S-G 冒烟与正式运行：冒烟每个 (section × group × driver) 至少 1 行；G1 与 G2b 中同名的 point_id 各取 1 行；G6 至少 2 行（含一行 I4=N/A）。正式两遍在一次调用中完成，输出到事先不存在的 $EV/runs/formal/。每条运行前后核对驱动 sha256。
- S-H 判定与比对：VERDICT_M1_F4_R9M1R3.tsv（两遍一致性；FLAKY、GDB_DIV 单列；G5/G6 两遍 I1–I6 都判）；F3_F4_EQUIV_R9M1R3.tsv（rc1、rc2、rc3、hit、class、I1–I6、env；写明 env 忽略的键；HIT 分开计 NONEMPTY_IDENTICAL、BOTH_EMPTY、NOT_RUN；G6 的 I 列须有非 "-" 的 F3 值，断言 G6 25 行全部参与 I 比对）；R9M1R2_VS_R9M1R3_R9M1R3.tsv（本轮事实与参考结果二逐行比对，差异逐行列出）；M1_SUMMARY_F4_R9M1R3.tsv（断言 F4 651 + CITED F2 651 = 1302，各节和 = 各表行数之和，NOT_RUN 单列）。
- S-I 收尾按 §1-6 固定顺序。报告结构：门禁 → G-1..G-8 复核 → 裁决与勘误 → K 补核 → 试跑期摘要（次数、目录、每次改了什么）→ 预注册与口径 → 阳性对照 → 冒烟 → 正式结果 → 等价比对与参考结果二比对 → 总表 → 事件两张表（含 r9m1r2 补登与本轮裸写自查）→ 需用户裁决（没有就写"无"）。结尾写"本轮已完成/未完成 R9 M1 第二修正范围，等待用户审核"，附 git log -1 与 git status --short。
- STATE.md（≤ 8192 字节）：当前轮次改为 R9 M1R3；S4R9 M1R2 那一行注明"参考结果二，有效结果见 M1R3（U318）"；关键数字加一行；开放项写明下一步为 M3。

## 5. 硬停止条件
1. 开工门禁任一项不符。
2. 追加脚本前缀断言失败，或 U 号/E 号重复。
3. 越界写入、safe_run 以外的写入、改 S4/ 或已提交文件、写其他轮次证据目录、改写 git 历史。
4. 冻结期调用清单外的脚本、改写任何 testing/d003 文件、任一冻结脚本调用超过 1 次。
5. 冻结期脚本报错，或出现 MISMATCH、FLAKY、GDB_DIVERGENT（照实记录，不修不重跑）。
6. 冒烟出现 MISMATCH、GDB_DIVERGENT 或 INVALID：停在冒烟，只分诊。
7. 门禁出现 FAIL。
以下不是硬停止：K 补核中命中数不等的组（单列，列入"需用户裁决"，其余继续）。
