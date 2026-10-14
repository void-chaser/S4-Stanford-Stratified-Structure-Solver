# P05-S4 R8 M1a 续3a 审核修正补充轮 任务书（原文存档）

> 存档说明：本文件为用户在对话中下发的审核修正任务书原文，按任务书要求另存为新的 audit brief。
> 它不替换、不覆盖原续3a任务书 `P05_S4R8_BRIEF_M1a_CONT3a.md` 与恢复补充 `P05_S4R8_BRIEF_M1a_CONT3a_RESUME.md`。

执行 P05-S4 R8 M1a 续3a 审核修正补充轮。

本轮仍属于原续3a，不是新阶段，不是续3b。
上一轮提交 fbc46681cecf2a056b17ef77cfac3a1c946e2334 保留，不撤销、不改写提交历史，不覆盖旧证据。

本轮先纠正3a证据链和判定器材，不开展续3b。
不做失败注入，不运行M1b/M1c，不生成它们的正式预注册或运行器。
不得修改S4/或任何已提交的testing/d003文件。
所有装置修正通过新增带r8m1a4audit编号的文件实现。
不得宣布阶段完成或签收。

一、开工与范围

先读STATE并核对HEAD，再读PROJECT_ROADMAP的P05行、AGENTS、原3a任务书、恢复任务书和原3a报告。

基线：
HEAD=fbc46681cecf2a056b17ef77cfac3a1c946e2334
HEAD:S4=6cff923a02baf19e01966b2339755cbf3a5deeef
判定器sha256=d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb

允许保留当前未跟踪文件：testing/d003/stage_s4r8/manifest_final_r8m1a4.sh
先核对内容、身份、执行记录和哈希，作为已披露存量处理；若其他改动出现，先调查，不自动纳入允许范围。该存量脚本经审核后可原样纳入本轮记录提交，不删除。

新增证据使用：checkpoints/p05/evidence/p05-s4r8/m1a4audit/
小表：checkpoints/p05/registries/s4r8/M1a/
报告：checkpoints/p05/P05_S4R8_REPORT_M1a_CONT3a_AUDIT.md
原报告保留，通过补充报告和ERRATA纠正。
将本任务书存为新的audit brief。

二、先做完整请求语义重建，禁止只看request字符串

新增请求重建器。逐行从原登记表、ADD_v3及实际历史运行器反查：source_registry、原始来源行、point_id、group、source_tree、run_tree、mode、NG、route、完整环境、argv、request_raw、nth、K、M、site/ID、计数口径、历史预期分类和NOT_REACHED依据。

禁止根据point_id猜nth，禁止缺失参数默认1。
保留原登记表和ADD_v3两个来源，不因关联表替换丢失原行出处。
连接键必须完整并拒绝重复、歧义和未匹配。

明确输出规范化目标：
s4malloc：对应wrapped S4_malloc的第K次；
exec：对应wrapped exec的第K次；
裸plan+nth=N：按对应注入器实际语义解析，不得检查"总malloc至少1"；
plan:N、plancall:K:M、rnv1:M、各seam ID，均按各自装置语义检查。

特别核对历史ADD_v3的44行INVALID_NOT_REACHED。先保留其原预期，不预先强行指定本次重算数量；逐行计算并说明实际结果。只有原来源明确支持才记EXPECTED_NOT_REACHED。本应命中而未命中记UNEXPECTED_NOT_REACHED。原预期未命中但现在实际命中也必须显式列出变化，不得悄悄并入REACHED。

输出完整目标表和旧1026 REACHED判定的逐行差异表。所有1128来源行必须得到解释：实际目标检查、无注入控制、S3R4新增独立复核、或有明确依据的其他状态。1128行不是1128个独立实验，不混淆分母。

三、新增严格离线比较器，首先复算原198次日志

不得修改已提交compare_callseq_r8m1a4.py。新比较器读取原始events、summary、gdb stdout/stderr及运行表，检查文件存在、TSV列数、必需字段、唯一单元身份和对应关系。

严格验证：
1. event_idx连续；
2. 各计数族及各site序号连续，不以最大值替代事件数量；
3. plan/window开闭按ID和上下文准确配对；
4. malloc属于正确上下文，sub_seq连续；
5. END/CLOSE记录的数量等于实际内部明细；
6. summary总量与事件事实一致；
7. EXITED状态、退出记录、信号、trace_error完整；
8. 必需符号解析及真实零调用证据；
9. 所需帧不得为??或缺失；
10. 缺文件、空文件、缺字段不得默认成功。

序列比较至少包含：event_type、真实被计数函数func、caller、序号、上下文、site/ID和内部malloc明细。比较退出和可获取的rc_first/rc_retry事实，不能以进程exit=0代替应用返回码。

只允许原任务书批准的quad→quad_st名称归一。旧比较表保留，新结果用独立audit后缀。如复算发现差异或错误，记录后停止依赖步骤，不得用改规则或改期望消除。

四、审核原追踪器缺口，按证据决定最小补跑

先为全部实际需要的符号建立证据表：断点实际位置、是否pending、location数量、所需族、参数取值来源、实际驱动身份。

重点检查：
1. seam hook通过DWARF读取还是寄存器回退；
2. 如用x86_64 ABI寄存器，原断点是否真在函数入口；
3. REQUIRED_FAMILIES包含plancall/rnv1时，所需plan/window及malloc符号是否完整检查；
4. FinishBreakpoint out_of_scope是否发生；
5. plan/window是否嵌套或重叠；
6. 非正常退出和追踪异常是否被漏报。

原日志可证明的部分离线复核并复用。原日志无法证明的部分标记EVIDENCE_INSUFFICIENT，不得猜测"没有发生"。

如必须补跑：新增追踪器和runner，不修改历史装置。补跑前先输出缺口清单、受影响单元、重跑原因及新期望；期望INFLUENCED，记录UTC及sha256。新期望只修正观测完整性，不能放宽原通过条件。

新追踪器必须：检查必需断点pending/location；ABI回退使用明确函数入口地址；out_of_scope和回调异常显式TRACE_ERROR；正确维护上下文栈，或对不支持的嵌套显式报错；记录真实函数身份和退出事实；runner校验实际环境、argv与登记配置相符，无结束记录、信号、超时及非预期退出不得成功。

只补跑受影响的完整F2/F3配对单元。如缺口确实影响全部单元，说明理由后可完整重跑；不能为了数字好看重复运行挑结果。原首次失败、修正前部分运行和正式运行均保留。

五、重新复核S3R4新增项，禁止硬编码观测

新增汇总器，不修改旧汇总器。先从原9组合原始日志严格解析事实：

A：win_open、win_malloc_in_window、outside_malloc_count、全部K_init/K0候选及caller、唯一性、运行退出状态。UNIQUE必须来自候选集合，不能硬编码。

B：Mtot、Mfirst、每个目标malloc实际n_values及caller、RC_first、RC_retry、inject_hits和运行退出状态。n_values不得硬编码36；RC/hits缺失不得默认0。

polygon_breakpoint_hits继续沿用明确的历史推导口径：由实际n=36及caller事件推导，不能伪装成源码断点命中。

读取并核对冻结EXPECT_ADDITIONS内容与哈希，逐字段比较并输出差异。gdb_rc非零、缺关键字段、无法解析真实函数或退出状态均不得MATCH。任何MISMATCH必须反映到程序退出码和停止状态。

22行新增项必须按键关联具体映射组合及其有效结果；组合缺失、Unknown、MISMATCH不得写MAPPING_VERIFIED。只在原日志缺证据时，按第四节预注册后最小补跑。不得做失败注入。

六、纠正记录和措辞

追加ERRATA，编号核对现有尾号后使用，不重复U176–U182。不把本轮规划者技术发现伪造为用户历史裁决。

原报告保留，补充报告纠正：旧1026 REACHED由弱化检查产生，不能作逐点覆盖证明；旧99 VALID/IDENTICAL为旧程序输出，等待严格复算；新增项哪些字段是硬编码或默认值及其替代证据；首次运行失败不是"运行前草稿调试"；失败门禁和部分运行是否落盘分别说明；提交后HEAD^关系不能写成提交前关系；FINAL快照之后新增未跟踪脚本的时间顺序。

不要把装置缺陷写成S4生产缺陷。若正确检查暴露生产或调用序列差异，单独登记并停止依赖工作，不在本轮改S4。

七、证据清单与收尾

建立完整新增证据清单，并补录本轮消费的原始证据：198次正式运行的events、summary、stdout/stderr；首次失败与部分运行日志；A/B九组合原始日志；期望、源表、装置哈希、PRERUN及safe_run收尾快照。原树、库、二进制仅记录身份哈希，不复制进git。旧清单不覆盖，新增清单明确范围。清单不包含自身，活日志记录快照长度/哈希。小型目标表、严格复算表、差异表、补跑范围表、新增项复核和门禁复制归档并逐个比对哈希。

STATE先将"3a已完成/下一步3b"改为真实审核修正状态；只有全部严格检查及必要补跑完成后才恢复可进入续3b的表述。不得为了保住旧数字省略EXPECTED_NOT_REACHED等状态。

开工与收尾门禁核对冻结树、判定器、历史装置不变、允许改动路径、历史前缀和分类清单规则。不得裸跑所有历史sha256sum -c；沿用历史ERRATA已说明的活文件前缀和规范化清单方法。

start成功、end完整性FAILS=0才做一次记录提交。逐路径git add，不用-A或"."。消息末尾awaiting user review。最终status必须真实为空；提交后不要再新增仓库内未跟踪脚本。FINAL及其清单写入被忽略证据目录。技术停止也做真实记录收尾；身份/完整性失败不得强行提交。

八、写入与执行硬规则

每条含写入的命令开头：
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a4audit; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"

一律经：sh testing/d003/safe_run.sh p05-s4r8 -- <本轮新增脚本>

写入仅限EV、testing/d003及checkpoints/p05批准范围。Python使用python3 -I -B，不用py_compile。脚本运行前按原任务书禁止项正则检查，0命中并登记PRERUN哈希。内联无任何>字符，包括2>&1。文本read、搜索grep、发现glob。顶层临时区快照沿用原任务书明确允许的只读形式。不删除旧文件，不做拒绝性探测，不隐藏stderr。检查真实退出码，后台作业记录ID并收集。

最终输出：修正前/后的各状态计数；复用与补跑单元数量及理由；新增项真实复核结果；完整证据清单范围；门禁、提交与status；尚未完成项。

只有达到上述要求才写："本轮已完成R8 M1a续3a审核修正范围，等待用户审核"。否则写未完成及具体停止点。本轮不执行续3b。
