# P05-S4 R8 M1a 续3a 审核修正第二部分 任务书（原文存档）

> 存档说明：本文件为用户在对话中下发的"审核修正第二部分"任务书原文（r8m1a4audit2），按 §一.4 另存为新的 brief。
> 它不替换、不覆盖原续3a任务书 `P05_S4R8_BRIEF_M1a_CONT3a.md`、恢复补充 `P05_S4R8_BRIEF_M1a_CONT3a_RESUME.md` 与第一部分审核修正任务书 `P05_S4R8_BRIEF_M1a_CONT3a_AUDIT.md`。
> 本文件为第二阶段提交（B 阶段）的一部分。

执行 P05-S4 R8 M1a 续3a 审核修正第二部分（r8m1a4audit2）。

本轮仍属原续3a，不是新阶段，不是续3b。不做失败注入，不运行M1b/M1c，不生成其正式预注册或运行器。
不得修改S4/及任何已提交的testing/d003文件；装置修正一律新增带 r8m1a4audit2 编号的文件。不得宣布阶段完成或签收。
工作量不是停止理由。只有本任务书第九节列出的条件才可停止；任何停下都必须按第九节做真实记录收尾。

〇、用户裁决（随本任务书下发，开工门禁通过后追加到 registries/RULINGS.tsv，5列，来源写"R8 M1a 续3a 审核修正第二部分任务书 §〇"）
U183（E8-63，gdb运行时序）：198次_R3运行暂不作废，也不直接接受。以本轮 §二 配置独立核对、§三 序列比较、§四 追踪器审核作为事后验证；全部通过的配对单元记 POST_HOC_VALIDATED（期望状态 INFLUENCED），可作无注入映射证据；任何一项不符的配对单元作废，列入补跑范围，不得改规则挽回。
U184（E8-65，S3R4新增项事后修正）：B段6组合结论接受（判据未改）。键名映射 caller_function_of_K→caller 接受（仅字段名对应，不改值）。A段K0"紧邻K_init之前"判据不接受作为结论；须按历史定义先冻结规则文件再重算（§五）。首次与r2结果保留不改。
U185（E8-64）：覆盖检查以 _R3 为依据；_R2 保留，标注不作依据。
U186（收尾方式）：新增门禁 gate10_r8m1a4audit2.sh，基线 fbc4668。先把现有31项原样做"存量记录提交"（作为停止记录，原文件不改，矛盾在本轮新报告更正），再做本轮工作，第二次记录提交。
U187（流程）：上一部分未运行start门禁即追加E8-63–E8-65，属执行流程缺陷，不是技术停止。已追加内容经前缀校验后保留，不回退；在新ERRATA中披露。"缺少合格start文件"今后不得作为停止理由：执行者须在开工时自建本轮门禁并先运行start。

一、开工（只读）
1. 依次读：checkpoints/p05/STATE.md、AGENTS.md、PROJECT_ROADMAP.md 的P05行、checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a.md、_CONT3a_RESUME.md、_CONT3a_AUDIT.md、P05_S4R8_REPORT_M1a_CONT3a.md、P05_S4R8_REPORT_M1a_CONT3a_AUDIT.md、registries/s4r8/ERRATA_8.txt 的 E8-55 至 E8-65。
2. 基线（任一不符即停，身份停止）：
   HEAD=fbc46681cecf2a056b17ef77cfac3a1c946e2334；HEAD^=331c022c3d9944cff8e7e63e16c24d33253ce847
   HEAD:S4=6cff923a02baf19e01966b2339755cbf3a5deeef；判定器sha256=d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb
   git diff --name-only HEAD -- testing/d003 为空
   RULINGS.tsv：68691字节，sha256 55359d8c35a7124acc2ccf63c5be3adcc2844a43231aeee5affc3f01584e0215（等于HEAD版本）
   ERRATA_8.txt：工作区50547字节，sha256 884a5f343e897359e91bc0cbd221316f696e843c5299fc5328555130dc614e2b；前41272字节sha256 11574288e401e959b043dc8e8cd9fd11bc030e6147589eda8ab250d2f7046ed7（等于HEAD版本）；历史前缀 13990→72dc6aed…、37669→ff958d24… 仍须成立。
3. git status --short 经 LC_ALL=C sort 后必须恰为以下31行（存量，U186）：
    M checkpoints/p05/STATE.md
    M checkpoints/p05/registries/s4r8/ERRATA_8.txt
   ?? checkpoints/p05/P05_S4R8_REPORT_M1a_CONT3a_AUDIT.md
   ?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a_AUDIT.md
   ?? checkpoints/p05/registries/s4r8/M1a/ 下13个：ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT.tsv、ADDITIONS_STRICT_R8_M1a4AUDIT_FIRSTRUN_MISMATCH3.tsv、ADDITIONS_STRICT_R8_M1a4AUDIT_R2_MATCH9.tsv、ADDITIONS_STRICT_R8_M1a4AUDIT_R2_MATCH9_SUMMARY.txt、AUDIT_UNITS_VS_HISTORY_R8_M1a4AUDIT.tsv、CALLSEQ_KMAX_R8_M1a4_R3.tsv、CALLSEQ_POINT_COVERAGE_CHECK_R8_M1a4_R3.tsv、CALLSEQ_VALIDITY_R8_M1a4_R3.tsv、COMPARE_UNITS_VS_HISTORY_R8_M1a4AUDIT.tsv、DRIVER_TAG_AUDIT_R8_M1a4.tsv、PRERUN_CHECKS_R8_M1a4AUDIT.txt、SHA256SUMS_M1a4AUDIT.txt、STRICT_RECHECK_CALLSEQ_R8_M1a4AUDIT.tsv、STRICT_RECHECK_CALLSEQ_R8_M1a4AUDIT_SUMMARY.txt
   ?? testing/d003/stage_s4r8/ 下14个：append_errata_r8m1a4audit.py、audit_driver_tags_r8m1a4.py、audit_units_vs_history_r8m1a4audit.py、compare_units_vs_history_r8m1a4audit.py、copy_registries_r8m1a4audit.py、copy_registries_r8m1a4audit_b.py、manifest_evidence_r8m1a4audit.py、manifest_final_r8m1a4.sh、manifest_registries_r8m1a4audit.py、map22_strict_r8m1a4audit.py、prerun_log_r8m1a4audit.sh、strict_recheck_callseq_r8m1a4audit.py、summarize_additions_strict_r8m1a4audit.py
   （registries 下实为14个，以 git status 为准；总数必须为31。）多出或缺少任何一项都先调查，不自动纳入，按身份停止处理。
4. 将本任务书原文存为 checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a_AUDIT2.md（第二阶段提交）。

二、门禁脚本 gate10_r8m1a4audit2.sh（新增，先写后用；不修改gate9）
以 gate9_r8m1a4.sh 为蓝本另写，模式三种：
- startA：检查 HEAD=fbc4668…、HEAD^=331c022…；status 等于 testing/d003/stage_s4r8/gate_allow_r8m1a4audit2_A.txt（即上面31行，排序后逐行完全相等，不用模糊正则）；RULINGS 与 ERRATA_8 按第一节的整文件长度和哈希检查。
- startB：检查 HEAD^=fbc4668…；git diff --name-only fbc4668 HEAD 排序后等于存量提交清单 gate_allow_r8m1a4audit2_A_commit.txt；RULINGS/ERRATA_8 的整文件值从 A_END 门禁文件的 RECORD 行读取，不从参数传入。
- end：从 START_FILE 读取 HEAD、临时区快照、RULINGS/ERRATA_8 长度与哈希，校验"前缀不变 + 只追加"；HEAD 等于 start 时的 HEAD；status 只允许 start 时的项目，加上本轮新增路径（路径中带 m1a4audit2 / AUDIT2，或是 STATE.md、RULINGS.tsv、ERRATA_8.txt 这几个修改项）。
三种模式都要做的共同检查：
- F2/F3 树哈希、判定器、REGISTRY_S3R4C3_D 哈希、testing/d003 tracked 无改动；
- 历史前缀 ERRATA_8 13990/37669 与 PRERUN 5603；
- registries/s4r8/SHA256SUMS.txt：25行，ERRATA_8 一行按前缀，其余用 -c 校验；s3r4c5 清单校验；
- M1a 目录下 SHA256SUMS.txt、_M1a3c_A、_M1a3c_B、_M1a3c_B_END、_M1a4、_M1a4_END、_M1a4AUDIT 七份清单逐份校验，OK 行数等于总行数；
- s4r7 分类复核调用 recheck_s4r7_r8m1a4.py。
输出名与派生名：
- 门禁输出名必须为 GATE_R8_M1a4_AUDIT2_<名>.txt，写入 evidence/p05-s4r8/；
- 派生的复核名为 S4R7_RECHECK_GATE_R8_M1A4_AUDIT2_<名大写>.tsv，必须匹配 recheck 脚本的正则 ^S4R7_RECHECK_GATE_R8_M1A4_[A-Z0-9_]+\.tsv$；
- 两个名字已存在即拒绝（U17）。
临时区快照由调用者取，只允许这一种内联形式：date; ls -A /tmp | wc -l; ls -A /tmp | sha256sum; date
start 门禁未通过（FAILS≠0）：只保留门禁文件和停止说明，不追加、不提交。

三、阶段A：存量记录提交（先做）
1. 运行 startA，FAILS=0。
2. 用新增脚本 append_rulings_r8m1a4audit2.py 只追加 U183–U187，追加前后做前缀校验；用新增 append_errata_r8m1a4audit2.py 追加 E8-66：披露 U187 所述流程缺陷，并纠正上一部分报告的四处矛盾，即报告 §1 "任务书假设331c022"不实；§5第2条与§10.1冲突；§5第6条引用的end门禁不存在；§4把§三写成"已完成"，应为"部分完成：十项单元内检查完成，F2↔F3序列比较未做"。正文不写 /tmp 字面量。
3. 复制 startA 门禁到 registries/s4r8/M1a/。
4. 运行 end（START_FILE=startA），FAILS=0。
5. 逐路径 git add：31项存量 + RULINGS.tsv + startA 门禁副本 + gate10 脚本 + 两个 gate_allow 文件 + 两个 append 脚本。不用 -A 或 "."。
   提交信息：P05-S4 R8 M1a cont3a audit part1 stop record (as-is) + rulings U183-U187 + E8-66; awaiting user review
6. 提交后只读核对 HEAD^=fbc4668，并写清单 gate_allow_r8m1a4audit2_A_commit.txt。注意：该文件在提交后新建，归阶段B提交，要在报告里写明这个时间顺序。

四、阶段B-1：§三补全（离线，复用198次原始日志）
1. 运行 startB，FAILS=0。
2. 新增 config_check_r8m1a4audit2.py，逐单元独立核对配置：
   - 实际 cmd_env/argv（CALLSEQ_RUNS_R8_M1a4_R3.tsv 与 gdb.stdout/stderr 中的记录），与单元表、历史运行器推导值是否相等；
   - driver_sha256 是否等于 DRIVERS 登记（R7 无表头表按生成器 printf 的列序读取）；
   - DRIVER_TAG_AUDIT 中 NO_DRIVER_PATH_COLUMN 的8行，改为在库表和驱动目录中解析实际文件并计算 sha256，查不到的记为 EVIDENCE_INSUFFICIENT；
   - 去重键（驱动身份、mode、NG、环境、argv）唯一；
   - F2/F3 配对的两侧只有树不同。
3. 新增 seqcompare_r8m1a4audit2.py（不改 compare_callseq_r8m1a4.py）：只对严格复算 PASS 的单元做 F2↔F3 逐事件比较。
   - 比较字段：event_type、func、caller、seq、sub_seq、上下文（所属 plan/window 的 ID）、site/ID、details 中的内部 malloc 明细；
   - 唯一允许的名称归一：quad→quad_st；
   - rc_first/rc_retry 能从日志取到的就比较，取不到的记 RC_UNAVAILABLE，不能用进程 exit=0 代替；
   - 输出：每对一个状态（IDENTICAL / DIFFERENT / EVIDENCE_INSUFFICIENT），以及差异明细表。
4. 出现 DIFFERENT：受影响的配对标为作废（U183），单独登记"调用序列差异"（不写成S4生产缺陷，不改S4），停止依赖它的步骤；其余单元继续。

五、阶段B-2：§二 请求语义重建（离线）
新增 reconstruct_requests_r8m1a4audit2.py。逐行处理覆盖表的1128行，从原登记表、ADD_v3（registries/s4r7/REGISTRY_S4_PRE_R7_M2_ADD_v3.tsv）和实际历史运行器（run_m1_r7.py、run_m2_r7.py、run_m2b_all_r7.py、dryrun_m3_r7.py 等），按函数和行号引用反查以下字段：
- 来源：source_registry、原始来源行号；
- 身份与运行配置：point_id、group、source_tree、run_tree、mode、NG、route、完整环境、argv；
- 注入请求：request_raw、nth、K、M、site/ID、计数口径；
- 判定依据：历史预期分类、NOT_REACHED 依据。
硬规则：
- 不得根据 point_id 猜 nth，缺失参数不得默认为1；
- 连接键必须完整，遇到重复、歧义或未匹配即拒绝；
- 两个来源的原行出处都保留。
规范化目标按任务书 CONT3a_AUDIT §二 的口径：
- s4malloc 第K次、exec 第K次；
- 裸 plan + nth=N 按注入器的实际语义解析，不得检查"总malloc至少1"；
- plan:N、plancall:K:M、rnv1:M 以及各 seam ID，各按自己装置的语义检查。
然后用 §四 中 POST_HOC_VALIDATED 的单元计数序列，逐行判定以下状态：REACHED / EXPECTED_NOT_REACHED（原来源明确支持才可用）/ UNEXPECTED_NOT_REACHED / NOW_REACHED_WAS_NOT_REACHED（原预期未命中、现在命中，必须单列）/ CONTROL_NA / ADDITION_SECTION7 / EVIDENCE_INSUFFICIENT。
输出：
1. 完整目标表 REQUEST_TARGETS_R8_M1a4AUDIT2.tsv；
2. ADD_v3 中44行 INVALID_NOT_REACHED 的逐行结论表；
3. 与旧 _R3 结果（1026 REACHED）的逐行差异表；
4. 分母说明：1128 行是来源行，不是 1128 个独立实验。
出现 UNEXPECTED_NOT_REACHED：登记并停止依赖步骤，不改期望。

六、阶段B-3：§四 追踪器审核（只读查询 + 离线）
新增 tracer_audit_r8m1a4audit2.py，以及只读符号查询脚本 symq_r8m1a4audit2.sh（经 safe_run 运行，只用 nm、readelf 和 gdb -batch -nx，输出写到 $EV）。
1. 为 callseq_r8m1a4_gdb.py 实际用到的每个符号建证据表：断点地址是否等于函数入口（与 readelf 的 st_value 对照）、是否 pending、location 数量、所属计数族、参数取值来源（DWARF 还是 x86_64 寄存器回退）、驱动身份。
2. 从原 gdb.stdout/stderr 中离线核对：
   - FinishBreakpoint 是否发生 out_of_scope；
   - plan/window 是否嵌套或重叠；
   - REQUIRED_FAMILIES 含 plancall/rnv1 时，plan/window/malloc 所需符号是否齐全；
   - 非正常退出或回调异常是否被漏报；
   - P0048（U0095/U0096，vl，plan=0）的 plan 断点是否解析成功，要有直接证据。
3. 原日志证明不了的项记 EVIDENCE_INSUFFICIENT，不得推定为"没有发生"。
4. 输出缺口清单、受影响单元和补跑决策。
   - 缺口为空：不补跑。
   - 缺口非空：本轮只做三件事——新追踪器和runner的设计说明；补跑预注册（受影响的完整F2/F3配对、重跑原因、新期望，状态INFLUENCED，记UTC与sha256）；补跑范围表。然后在此计划停止点做记录收尾，补跑留给下一轮。不得放宽原通过条件。

七、阶段B-4：§五 A段K0重算
1. 运行前新增规则文件 K0_RULE_R8_M1a4AUDIT2.txt，记UTC与sha256，状态INFLUENCED（已看过首次结果）。
   - 规则只能依据历史定义：K0=nshapes=0层的n=0窗口外分配（testing/d003/stage_s3r4c2/prereg_a_c2.sh:8、P05_S3R4_CLOSEOUT_CONT2.md §4），以及 K 的判据"第二次WIN_OPEN之前最后一次窗口外malloc"；
   - 规则须基于原 stderr 中 WIN_OPEN 与 OUT_MALLOC 的先后顺序，以及日志里的层或 nshapes 信息；
   - 日志不足以确定层归属时，K0 记 EVIDENCE_INSUFFICIENT，不选值。
2. 新增 summarize_additions_strict_r8m1a4audit2.py（不改前两版），用该规则重算A段3组合，B段原样复算。与冻结期望 EXPECT_ADDITIONS_R8_M1a4.txt（sha256 ec08348f…）逐字段比较。
3. 出现 MISMATCH 或 NOT_UNIQUE：以退出码反映，登记，受影响的 A-U96 映射行不得写成 MAPPING_VERIFIED，并交用户裁决；不得再改规则。
4. 用 v3 结果重做22行严格映射（新增 map22_strict_r8m1a4audit2.py）。

八、证据清单、归档、报告、提交
1. 新增证据清单 SHA256SUMS_M1a4AUDIT2.txt，放 $EV。覆盖范围：
   - 198次运行的 events.tsv、summary.json、gdb.stdout.txt、gdb.stderr.txt；
   - 首次运行和部分运行的日志；
   - A/B 九组合的原始日志；
   - 期望文件、源表、装置脚本哈希，PRERUN；
   - 两个 safe_run.log 的快照（活文件，记长度和哈希）。
   树、库、二进制只记身份哈希。清单不收录自身，也不预先宣称覆盖 end/FINAL。
2. 小表复制到 registries/s4r8/M1a/，包括：配置核对、序列比较、目标表、44行表、差异表、追踪器证据表、缺口与补跑范围表、K0规则、v3汇总、22行映射、各门禁副本。复制前先去重，逐个 cmp，并写 SHA256SUMS_M1a4AUDIT2.txt 全部校验。
3. 更新 STATE.md：
   - 写真实状态；
   - 只有 §三/§二/§四/§五 全部无停止、且无需补跑，才可写"可进入续3b（待用户审核）"；
   - 否则写清停止点。
4. 新报告 P05_S4R8_REPORT_M1a_CONT3a_AUDIT2.md，需包含：
   - 修正前后的各状态计数；
   - POST_HOC_VALIDATED、作废、补跑的配对数及理由；
   - 44行逐行结论摘要；
   - 追踪器缺口；
   - K0 结果；
   - 证据清单范围；
   - 门禁、两次提交与 status；
   - 违规两张表；
   - 待裁决项。
   报告末尾附 git log -2 与 git status --short。
5. 运行 end（START_FILE=startB），FAILS=0 后逐路径 git add。
   提交信息：P05-S4 R8 M1a cont3a audit part2: ...; awaiting user review
   提交后只读核对 HEAD^=阶段A提交。最终 status 必须真实为空；提交后不再在仓库内新增文件，FINAL 快照只写入被忽略的证据目录。

九、停止条件（仅此三类）
- 身份/完整性停止：HEAD、树、判定器、历史文件不符；出现未授权路径；写入违规；end FAILS≠0。不得强行提交，报告真实状态，交用户处理。
- start 门禁失败：只保留门禁文件和说明，不追加、不提交。
- 技术停止：出现 DIFFERENT、UNEXPECTED_NOT_REACHED、K0 的 MISMATCH/NOT_UNIQUE、补跑缺口非空（计划停止点）。停掉依赖它的步骤，但不依赖它的步骤继续做完，然后照常做 end 门禁和记录提交。
"需要符号查询""工作量大""缺少合格的 start 文件"都不是停止理由。

十、写入与执行硬规则
- 每条含写入的命令开头先执行：
  REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a4audit2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
- 一律经 sh testing/d003/safe_run.sh p05-s4r8 -- <本轮新增脚本> 运行。
- 写入只限 $EV、testing/d003/stage_s4r8/ 以及 checkpoints/p05/ 下本任务书点名的文件。
- Python 一律用 python3 -I -B，不用 py_compile。
- 脚本运行前用 grep 工具按原任务书的禁止项正则检查，必须0命中，并登记到 PRERUN_CHECKS_R8_M1a4AUDIT2.txt（含 UTC 与 sha256）。未运行的草稿查出问题后改正，不算违规。
- 内联命令不得含任何 > 字符（包括 2>&1）；凡是需要输出的核对，一律写成脚本经 safe_run 运行。唯一例外是第二节给出的临时区快照形式。
- 看文本用 read，搜内容用 grep，找文件用 glob。
- 不删除旧文件，不做拒绝性探测或反例测试，不隐藏 stderr。
- 检查每条命令的真实退出码；后台作业记录 ID 并收集输出。
- 违规按两张表披露：越界写入尝试表、工具/脚本事件表。
- 结尾：只有全部完成且没有停止，才写"本轮已完成 R8 M1a 续3a 审核修正范围，等待用户审核"；否则写"本轮未完成"及具体停止点。本轮不执行续3b。
