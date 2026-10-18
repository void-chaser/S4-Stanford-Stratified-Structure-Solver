# P05-S4 R9 M1 修正轮任务书（轮次标识 r9m1r2）

## 0. 身份与边界
- P05-S4 子轮次 R9 的 M1 修正轮（不是新阶段，不是 M3）。证据目录 checkpoints/p05/evidence/p05-s4r9/m1r2；小表目录 checkpoints/p05/registries/s4r9/M1R2/；报告 checkpoints/p05/P05_S4R9_M1R2_REPORT.md；任务书原文经 safe_run 存为 checkpoints/p05/briefs/P05_S4R9_BRIEF_M1R2.md。
- 目的：纠正 r9m1 的流程问题（记录提交后改预注册、正式运行后改判定并覆盖重跑、门禁放宽、裸写、K 替代证据越界、报告与副本不一致），并在冻结的脚本和预注册下重新取得 M1 F4 的 651 行事实。
- 不改 S4/、判定器、历史装置，以及任何已提交的文件（含 r9m1 的全部脚本、allow 文件、报告、registries/s4r9/M1/ 下全部小表）。r9m1 的证据目录 p05-s4r9/m1 只读。新脚本放 testing/d003/stage_s4r9/，文件名带 r9m1r2。
- 禁止 git commit --amend、rebase 等改写历史的操作。报告不写本轮收尾提交的哈希。不得宣布阶段完成，不得询问是否签收。
- 开工先读：AGENTS.md → STATE.md → 本任务书 → P05_S4R9_M1_REPORT.md → P05_S4R9_BRIEF_M1.md → registries/s4r9/M1/ → registries/s4r9/ERRATA_9.txt → registries/s4r8/M1b/r8m1b1、r8m1b3 → registries/s4r8/M1c/r8m1c3。
- 开工门禁：HEAD = 56b1e43fa4b4b88437d2c49543ee764f39d3ee28；HEAD:S4 = 589e15eb11fcb04e031b524f25a443e7921946cf；判定器 sha256 = d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb；git status --short 为空；/tmp 顶层只读快照（条目数与 sha256）；RULINGS.tsv = 127551 字节、最大 U 号 U311；ERRATA_9.txt 最后一条 E9-13。任一不符即停。

## 1. 写入与执行纪律（沿用 r9m1 §1 全部 9 条，另加 4 条）
1. 每条含写入的命令开头：REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"，然后经 sh testing/d003/safe_run.sh p05-s4r9/m1r2 -- <命令>。
2. 写入目标只能以 $EV/、$REPO/testing/d003/、$REPO/checkpoints/p05/ 开头。其他轮次证据目录（含 p05-s4r9/m1）只读，沿用的产物只核对 sha256。
3. 内联命令不得含 > 字符（含 2>&1）；不用 2>/dev/null（只读命令也不用）；核对路径只用 ls -d 或 test -e；不做沙箱探测或反例测试。
4. 新脚本用标准首段；Python 一律 python3 -I -B；运行前用 grep 工具查禁止项。
5. 每一次 rm、mv、重跑、覆盖都进事件表二，行号由脚本从 $EV/safe_run.log 提取。门禁重跑用 _R2、_R3 等新文件名，并且必须经 safe_run 执行。
6. 停止策略：只有真实基线异常、无法解释的越界改动和 §6 的硬停止条件才停。合法中间产物使工作区非空，不是停止理由。
7. 任何文件都不得经 safe_run 以外的途径写入，包括编辑工具和 $EV/tmp 下的临时测试脚本。临时分析脚本也必须经 safe_run 写入，并进事件表。
8. 活文件（RULINGS.tsv、ERRATA_9.txt）只能由脚本追加：先断言"新文件 = 旧文件字节 + 新行"，再落盘。
9. 门禁 FAILS 以输出文件中 ^FAIL<TAB> 开头的行数为准；Python 以 fails 作退出码；自检 FAIL 行数 = FAILS 且 FAILS = 0。
10. 【新】冻结即不改：记录提交 (i) 中的预注册、ENGINE_COLUMNS、判定/运行/比较脚本，在 (i) 之后不得修改或重新生成。end 门禁逐个断言它们的 sha256 等于 (i) 时的值。allow 文件不得包含 " M " 通配项。
11. 【新】正式运行脚本只调用一次（两遍在同一次调用中完成），输出目录事先不存在；运行中途出错也不得删除或覆盖已产出的结果，改用新目录名 formal_R2 并进事件表。
12. 【新】registries 复制完成后断言：副本与证据原件 sha256 相同；报告中引用的每个小表文件名都在 registries 中存在。
13. 【新】措辞：不写"100%""完全""严格""彻底""证实""精确""全面闭环""完美"。脚本在报告落盘前用 grep 检查这些词，命中数须为 0。

## 2. 输入事实（规划者只读核实；执行者须用脚本按原始文件复核，不符就照实写"规划者事实有误"）
- F-1 预注册被覆盖：00490a7 中 registries/s4r9/M1/PREREG_M1_F4_R9M1.tsv 的 sha 为 3894d8990c3f…，时间 2026-10-17T15:12:32Z；56b1e43 中同名文件为 d57fcf29e572…，时间 15:24:18Z。两版相差 52 行：G1 有 30 行驱动 d003plan-F4-plain→d003-F4-plain；G2b 有 22 行驱动 d003-F4-plain→d003plan-F4-plain，exp_class INVALID→REPORTED_FAILURE。CITED_F2 表也有同样的 52 行变化（193759a2…→72fa0e4d…）。原因：PLAN_M1B_R8_M1b1.tsv 中 (point_id, tree) 跨组重复（规划者计 104 个键），旧 prereg 只用 point_id 作键。
- F-2 时间线（safe_run.log 行号）：prereg 首次生成在第 22–23 行；冒烟在第 34–39 行（3 个脚本版本）；prereg 重生成在第 40–41 行；冒烟重跑在第 43–44 行；正式运行在第 45/46、49/50、51/52、53/54、60/61 行（5 个脚本版本）；判定在第 47/48、55/56、62 行（verdict_r9m1.py 有 2 个版本）。
- F-3 疑似裸写（safe_run.log 中无对应条目）：GATE_R9M1_end_R3.txt（15:52:04Z）；$EV/tmp/test_diff.py、test_inj_call.py、test_sim.py、test_actual_diff.py、test_actual_m1c.py；$EV/tmp/test_smoke_g5/。
- F-4 gate_allow_r9m1_end_R2.txt 新增 " M checkpoints/p05/registries/s4r9/M1/*" 与 " M testing/d003/stage_s4r9/*"，r9m1 已提交的 prereg_r9m1.py、copy_registries_r9m1.py 在收尾提交中被修改。
- F-5 K：K_INHERIT_R9M1.tsv 中 35 组 NO_SEQ_EVIDENCE_R2，其中 k_max=1 的 6 组（21 点），k_max>1 的 29 组（218 点）；K_INHERIT_RAW 中这些组每次命中都是 arg=None func=None loc=None:0。testing/d003/src 的驱动只输出 HIT/HITCOUNT/MALLOC/WITNESS 行，没有逐次调用的 trace。报告"init 与 polyinj 输出了完全一致的 trace 序列"无原始依据。
- F-6 不一致：registries/s4r9/M1/EVENTS_R9M1.tsv 85 条，证据目录 96 条，报告写 96；registries 门禁文件为 GATE_R9M1_end.txt，报告引用 end_R3。
- F-7 规划者独立复算：F4 正式 pass1 的 M1b 415 行 rc1/rc2/hit 与 F3 冻结结果（RESULTS_M1B_R8_M1b1 与 RESULTS_SUPP_R8_M1b3，按 (group, point_id) 取）逐行相同；pass1 与 pass2 的 M1b 415 行一致。M1c 未复算。

## 3. 用户裁决（start 门禁通过后由 append_rulings_r9m1r2.py 按 §1-8 追加，5 列，从 U312 起续编）
- U312：r9m1 的预注册覆盖、正式运行覆盖重跑、门禁放宽、裸写，都按事实登记为勘误（E9-14 起），不改 r9m1 已提交的文件。r9m1 的 M1 F4 判定（VERDICT_M1_F4_R9M1、M1_SUMMARY_F4_R9M1）降级为"参考结果"，有效结果以本轮 r9m1r2 为准。
- U313：重新冻结预注册。新脚本 prereg_r9m1r2.py 以 (section, group, point_id) 为键，期望值只从 F3 冻结表机械推导（M1b：PLAN_M1B_R8_M1b1 / PREREG_SUPP_R8_M1b3 / EFFECTIVE_M1B_R8_M1b3；M1c：PREREG_M1C_FACTS_R8_M1c2 / VERDICT_M1C_R8_M1c3），不读任何 F4 运行结果。新增列 inj_call（M1b 取 PREREG_SUPP 或 PLAN 的原值，不用 rc 推断）与 contract（M1b 的 rc2 比对口径，按 R8 M1b 合同原文引用）。断言：651 行；与 d57fcf29 版逐行比对，期望列的差异只允许出现在新增列上，若有其他差异逐行列出、照实写。状态 INFLUENCED，basis 注明"受 r9m1 冒烟与正式运行观察影响"。
- U314：判定口径冻结。verdict_r9m1r2.py 的口径在 (i) 前写入 ENGINE_COLUMNS_R9M1R2.txt：M1b 的 rc2 何时比对、M1c 中 G6c/CTRL_AUX 的 `-` 如何处理，每条都要引用历史判定脚本的文件与行号（如 verdict_m1c_r8m1c3.py:103）。不能引用历史依据的口径，按严格比对处理。
- U315：K 继承重做。29 组 k_max>1 的 NO_SEQ 不适用 U303。init/polyinj 组改用 R9 M0 已有的 init-F3/F4-dbg、polyinj-F3/F4-dbg 做无注入 gdb 映射。d003/d003plan 组从 F3、F4 导出树另建只用于映射的 -g 变体（命名 *-kmap-dbg，编译选项 = 对应 plain 驱动选项 + -g，BUILD_OPTION_DIFF 中只允许 -g 这一项差异）。kmap 驱动的命中总数须等于同 env 下 plain 驱动的命中总数（gdb 计数），然后按 U300 比对序列（大小 + S4 帧，行号经 LINEMAP_F3_F4_S3R5 映射，取不到帧用 bt 8）。三项都相同的记 PASS_K_INHERITED_R3；仍取不到序列的记 NO_SEQ_EVIDENCE_R3，列入"需用户裁决"；DIVERGENT 的组不进入正式运行，列入"需用户裁决"。k_max=1 的 6 组同样先试映射，失败才用 U303 替代证据。kmap 驱动不得用于判定运行。
- U316：执行顺序：start 门禁 → 取证（S-B）→ 裁决与勘误追加 → K 重做 → 预注册与口径冻结 → 记录提交 (i) → 阳性对照 → 冒烟 → 正式两遍 → 判定 → 与 r9m1 参考结果及 F3 冻结事实比对 → 合并总表 → 收尾提交 (ii)。冒烟出现 MISMATCH、GDB_DIVERGENT 或 INVALID 时停在冒烟，只分诊。正式运行中的 MISMATCH 或 FLAKY 照实记录，不改脚本、不重跑覆盖。
- U317：F2 侧 651 行继续引用 r8 冻结判定，CITED_F2 表由 prereg_r9m1r2.py 用同一键规则重新生成，作为新文件，并核对驱动 sha256。

## 4. 步骤
- S-A 门禁：新建 gate_r9m1r2.sh、gate_check_r9m1r2.py，以已提交的 gate_r9m1_R2.sh、gate_check_r9m1.py 为蓝本，原件不动，差异写入 RUNNER_DIFF_R9M1R2.txt。end 门禁新增：§1-10 的冻结文件 sha 断言；registries/s4r9/M1/ 全部文件与 56b1e43 相同；allow 文件无 " M " 项。
- S-B 取证（只读分析，产出放 $EV）：
  1. forensic_r9m1r2.py：从 p05-s4r9/m1/safe_run.log 的 base64 段还原 prereg_r9m1、run_smoke_r9m1、run_formal_r9m1、verdict_r9m1、compare_f3_f4_r9m1 的全部版本，写到 $EV/forensic/<脚本名>_line<N>.py，输出 SCRIPT_VERSIONS_R9M1R2.tsv（行号、UTC、sha256、相对上一版的 diff 行数）与 TIMELINE_R9M1R2.tsv。
  2. 用 git show 00490a7:<path>（经 safe_run 写到 $EV/forensic/）取回旧版 prereg 与 CITED_F2，输出 PREREG_DIFF_R9M1R2.tsv（逐行列出差异字段、旧值、新值），复核 F-1 的 52 行与重复键数。
  3. 离线重判（不重跑程序）：用当前 r9m1 的冒烟事实与正式 pass1/pass2 事实，分别对照旧 prereg（3894d899）和新 prereg（d57fcf29）各判一次，用 r9m1 最终版 verdict 逻辑，输出 REJUDGE_OLD_PREREG_R9M1R2.tsv 与汇总。说明当时冒烟是否会触发 §6-6；冒烟原始输出已被覆盖、无法还原的部分照实写"已覆盖，无法还原"。
  4. bare_write_audit_r9m1r2.py：列出 p05-s4r9/m1 下全部文件的 mtime，与 safe_run.log 的条目时间和命令关联，未关联到的文件列为裸写候选，输出 BARE_WRITE_AUDIT_R9M1R2.tsv。复核 F-3。
- S-C 裁决与勘误：append_rulings_r9m1r2.py 追加 U312–U317；append_errata_r9m1r2.py 追加 E9-14 起的勘误，每条写事实、证据文件与行号、影响范围、处理方式。至少覆盖 F-1 到 F-6，以及 r9m1 报告中的措辞问题（逐个列行号）。
- S-D K 重做：build_kmap_r9m1r2.py（BUILD_KMAP_R9M1R2.tsv、BUILD_OPTION_DIFF_KMAP_R9M1R2.txt）→ k_inherit_r9m1r2.py（K_INHERIT_R9M1R2.tsv、K_INHERIT_RAW_R9M1R2.txt）。按 U315 判定；HIT 等价表分开计 BOTH_EMPTY 与 NONEMPTY_IDENTICAL。
- S-E 预注册与口径冻结：prereg_r9m1r2.py → PREREG_M1_F4_R9M1R2.tsv（+ .sha256 + _TIMESTAMP_UTC.txt）、PREREG_M1_CITED_F2_R9M1R2.tsv（同）、PREREG_VS_R9M1_DIFF_R9M1R2.tsv；ENGINE_COLUMNS_R9M1R2.txt。同时写好 run_smoke_r9m1r2.py、run_formal_r9m1r2.py、verdict_r9m1r2.py、compare_f3_f4_r9m1r2.py、posctrl_r9m1r2.py（全部支持输出路径参数），记录它们的 sha256 到 FROZEN_SCRIPTS_R9M1R2.tsv。start 门禁 FAILS=0 后做记录提交 (i)，信息末尾写 awaiting user review。
- S-F 阳性对照：posctrl_r9m1r2.py 调用正式的 verdict 与 compare 脚本，用目标行的真实配置：① F3 冻结事实作输入，期望 DIFFS=0；② 篡改副本（$EV/tmp）：M1b G2b 一行 rc1、M1c G5 一行 I1、M1b 一行 rc2（该行合同要求比对 rc2），期望恰好检出 3 处；③ 用旧 prereg（3894d899）对照 r9m1 正式事实，期望检出 F-1 所述的 G2b 22 行（数目以 S-B-3 为准）。
- S-G 冒烟与正式运行：冒烟每个 (section × group × driver) 至少 1 行，单遍，G1 与 G2b 中同名 point_id 的两组各取 1 行。正式两遍按 §1-11 只调用一次。每条运行前后核对驱动 sha256 与预注册相同。
- S-H 判定与比对：verdict_r9m1r2.py → VERDICT_M1_F4_R9M1R2.tsv（pass1/pass2 一致性，FLAKY/GDB_DIV 单列）；compare_f3_f4_r9m1r2.py → F3_F4_EQUIV_R9M1R2.tsv（逐行逐字段：rc1、rc2、rc3、hit、class、I1–I6、env；env 比对须写明哪些键被忽略；HIT 分开计 BOTH_EMPTY 与 NONEMPTY_IDENTICAL）；另出 R9M1_VS_R9M1R2_R9M1R2.tsv（本轮事实与 r9m1 参考事实逐行比对）；summarize_m1_r9m1r2.py → M1_SUMMARY_F4_R9M1R2.tsv（断言 F4 651 + CITED F2 651 = 1302，各节和 = 各表行数之和）。
- S-I 收尾：
  - events_r9m1r2.py：读 m1r2 的 safe_run.log，每条日志一行；另附"r9m1 补登"表（来自 BARE_WRITE_AUDIT 与 TIMELINE）。必须在最后一次 safe_run 写入之后再跑；断言总行数 = 日志条目数 + 裸写行数。
  - 报告结构：门禁 → 取证结论（F-1 到 F-7 逐条复核结果）→ 裁决与勘误 → K 重做 → 预注册与口径 → 阳性对照 → 冒烟 → 正式结果 → F3/F4 等价、与 r9m1 参考结果比对 → 总表 → 事件两张表（含 r9m1 补登）→ 需用户裁决（没有就写"无"）。结尾写"本轮已完成/未完成 R9 M1 修正范围，等待用户审核"，附 git log -1 与 git status --short。
  - STATE.md（≤ 8192 字节）：当前轮次改为 R9 M1R2；关键数字加一行；在 S4R9 M1 那一行注明"参考结果，有效结果见 M1R2（U312）"；开放项写明下一步为 M3。
  - 小表复制到 registries/s4r9/M1R2/（不改名），写 SHA256SUMS.txt 并逐个比对；证据目录写 SHA256SUMS.txt（导出树、kmap 驱动只记 sha256）。
  - end 门禁 FAILS=0 且自检一致后做收尾提交 (ii)，信息末尾写 awaiting user review。提交后只输出 git log -3 --oneline 与 git status --short。

## 5. 措辞
- 见 §1-13。REPORTED_FAILURE 只表示返回码非零。B 列不是修复证据。没有日志依据的原因写"原因未查明"；规划者事实与原始文件不符时照实写"规划者事实有误"。

## 6. 硬停止条件
1. 开工门禁任一项不符。
2. 追加脚本的前缀断言失败、U 号或 E 号重复。
3. 越界写入、safe_run 之外的写入、改动 S4/ 或已提交文件、写入其他轮次证据目录、改写 git 历史。
4. 门禁出现 FAIL：停下写报告，不得改门禁后重跑来消除。
5. (i) 之后任何冻结文件的 sha256 改变。
6. kmap 构建的 BUILD_OPTION_DIFF 出现 -g 以外的差异，或 kmap 与 plain 驱动命中总数不等：停在 K 阶段，写报告。
7. 冒烟出现 MISMATCH、GDB_DIVERGENT 或 INVALID：停在冒烟，只分诊。
以下不是硬停止：K 组 DIVERGENT 或 NO_SEQ_EVIDENCE_R3。这些组的行不进入正式运行（NO_SEQ 组照常运行，但在总表中单列），照实记录，列入"需用户裁决"，其余组继续。
