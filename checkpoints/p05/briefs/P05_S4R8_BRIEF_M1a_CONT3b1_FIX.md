# P05-S4 R8 M1a 续3b1补正：完成正式预注册、STATE压缩与记录纠偏

你是本仓库的验证执行者。本轮是P05-S4 R8 M1a续3b1的补正轮，不是新阶段。
本轮标识r8m1a6；不进入续3b2，不宣布M1a或P05-S4完成，不提出阶段签收。

## 0. 范围与基线

本轮只做：
1. 补正续3b1的记录与输入来源问题；
2. 完成M1b/M1c正式预注册；
3. 将STATE压缩到8192字节以内；
4. 完成门禁、归档和一次记录提交。

禁止：
- 修改S4/；
- 修改testing/d003/下任何已提交文件；
- 修改或覆盖历史证据、历史预注册、旧报告、旧允许列表；
- 执行驱动、失败注入、gdb、构建、重新链接；
- 编写M1b/M1c运行器或执行dry-run，留给续3b2；
- amend、rebase、reset或改写历史提交。

基线：
HEAD=f1cbefe84001c5957532133377f77d1d003e48c6
HEAD^=abf3e420f5ba3600e079ecf213612bc1fc2a0aad
HEAD:S4=6cff923a02baf19e01966b2339755cbf3a5deeef
a07b5ac:S4=e124925f5b242486a913b813fa181664f665b048
judge_d003.py sha256=d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb
分支=codex/p05-d003-fft-error-propagation

第一件事读取checkpoints/p05/STATE.md并核对HEAD。
然后读取AGENTS.md、PROJECT_ROADMAP.md的P05行、本任务书，
以及：
- checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a.md §2、§7
- checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3b1.md
- checkpoints/p05/P05_S4R8_REPORT_M1a_CONT3b1.md
- testing/d003/stage_s4r8/make_prereg_r8m1a5.py
- 本轮涉及的R7与S3R4原始登记表、结果表、环境推导脚本。

新脚本位于testing/d003/stage_s4r8/，文件名必须含r8m1a6。
证据目录：
checkpoints/p05/evidence/p05-s4r8/m1a6/
小表目录：
checkpoints/p05/registries/s4r8/M1a/
新表文件名必须含R8_M1a6。
报告：
checkpoints/p05/P05_S4R8_REPORT_M1a_CONT3b1_FIX.md
任务书存档：
checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3b1_FIX.md

## 1. 写入与执行纪律

shell脚本在shebang之后使用标准首段：
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a6; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"

含写入的执行一律：
sh testing/d003/safe_run.sh p05-s4r8/m1a6 -- <本轮新脚本>

Python通过本轮shell包装脚本调用python3 -I -B。
不用sh -c，不用py_compile，不创建仓库外输出。
允许写入目标仅为$EV/、$REPO/testing/d003/、$REPO/checkpoints/p05/。
新输出使用排他创建；已有输出不覆盖，修正版使用_R2等新名字。

读文件用read，搜索用grep，发现路径用glob。
内联shell不得出现任何“>”字符，包括2>&1。
不要用awk/cut/sort管道临时拼核对输出；需要核对写成新脚本。
禁止/dev/null、DEVNULL、heredoc、sed -i、python3 -c、cat >、tee、rm -rf。
禁止仓库外写入占位路径、拒绝性测试和沙箱探测。
不用fsck/gc/prune/stash/checkout/switch/reset/clean。

每个将执行的新脚本运行前用grep工具查禁止项：
/dev/null|DEVNULL|devnull|<<-?\s*['"]?[A-Za-z_]|sed -i|python3 -c|cat >|tee |rm -rf|(^|[^V])/tmp

该扫描针对可执行脚本及其实际执行的数据；
任务书存档内的规则文本不作为待执行代码。
标准$EV/tmp不得误判。命中非0时不运行，先纠正未执行草稿。
运行前记录脚本sha256、UTC与检查结果。

仅开工和收尾各允许以下只读快照：
date -u +%Y-%m-%dT%H:%M:%SZ; ls -A /tmp | wc -l; ls -A /tmp | sha256sum; date -u +%Y-%m-%dT%H:%M:%SZ

报告、ERRATA与RULINGS描述临时区使用“根目录临时区”。
工具write/edit仅用于本任务明确授权的文本创建与编辑；
生成表、复制、清单、Git记录与提交等执行写入均走safe_run。

## 2. 开工门禁先行

先完成基线只读核对，工作区必须干净。
随后只创建：
- 本轮任务书存档；
- gate13_r8m1a6.sh；
- gate_allow_r8m1a6_start.txt；
- gate_allow_r8m1a6_end.txt。

start允许列表恰好为上述四个新文件。
end允许：
- 上述四个文件；
- 修改STATE.md、RULINGS.tsv、ERRATA_8.txt；
- 本轮新报告；
- stage_s4r8下文件名含r8m1a6的新增文件；
- registries/s4r8/M1a下文件名含R8_M1a6的新增文件。

允许列表在start前冻结并记录sha256，执行中不得修改。
旧copy_m1a5.sh已是历史文件，保持不动；
本轮复制脚本必须另建copy_r8m1a6.sh。

start检查身份、冻结树、判定器、状态、历史表完整性，
记录RULINGS与ERRATA的字节数和前缀sha256。
STATE大小检查仅为end要求，不能因继承的超长STATE阻止补正开工。
历史清单的活文件、前缀检查及额外copied列按已生效ERRATA处理，
不得要求历史活文件当前全文件哈希等于旧快照。

运行start，FAILS=0后才允许追加记录或执行生成器。
start缺失是执行遗漏，不是技术阻塞。
门禁脚本自身缺陷可在本轮未提交阶段修正，以新输出名重跑，
保留旧输出并披露，不得降低验收标准。

## 3. 本任务书生效后的补充规则与记录纠偏

start通过后，追加U198–U201。
如编号已占用，停止编号追加并报告，不覆盖、不自行重编号。
来源填写本轮任务书§3，状态生效，每行保持5列。

U198：
只对M1的fftvl-ng1与vl-ng1两项无注入对照，
以RESULTS_R7_M1_CTRL_REJUDGE_POSTHOC.tsv两遍一致的事实为基准：
rc_first=20、rc_retry=20、run_rc=0、hit=0。
F2及对应F3均预注册这组事实与BASELINE_RC_EQUAL比较标签。
这不是CONTROL_OK，不是注入修复证据，不关闭D016或NG1可计算性问题。
不得修改judge_d003.py。
若表中保留判定器class，应按冻结判定器记录INVALID，
另设expected_label或comparison_contract=BASELINE_RC_EQUAL，
不得把BASELINE_RC_EQUAL伪装为判定器新类别。
其余16项M1对照按POSTHOC的CONTROL_OK事实生成。
上述18项对照均须验证两遍一致；任何不一致停止相应生成。

U199：
生成器补完仍属于续3b1补正，不转入续3b2。
实现未完成、工作量大、缺少代码不是可接受技术停止条件。
不得硬编码STOP-EXP-2代替实现。

U200：
STATE继续要求8192字节以内，不放宽。
允许把完整历史与详细开放项说明原样归档，
STATE保留每个开放项的标识、状态、去向和链接。
用逐项对照表证明没有丢失开放问题，不要求保留冗长正文。

U201：
允许一次性补齐旧22行新增映射表的提交版来源。
从历史证据目录读取
ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT2_RUN2.tsv，
先与旧audit2/audit3记录的清单、sha256及19/3状态核对，
再逐字复制为registries内带R8_M1a6的输入快照。
生成器只能读取这个registries快照，不直接读取未提交证据路径。
记录原路径、快照路径、字节数、sha256与核对依据。
本轮新建输入快照须明确标识“本轮新增、随本轮提交”，
不得冒称开工前已提交。
若历史完整性无法确认，不凭19/3总数重造原表，登记停止。

追加新ERRATA，编号以现有最大号之后连续追加，不覆盖：
- 旧STOP-EXP-2实际为实现未完成，不是新增技术限制；
- 旧报告“U192进入许可仍待裁决”不准确：许可已生效，
  本轮成果审核与阶段签收是另一回事；
- f1cbefe提交信息声称正式预注册与STATE压缩，与实际状态不符；
- 旧生成器使用证据路径、旧end门禁未复制入registries；
- 旧报告关于提交/end的前后状态不一致。
旧报告和旧提交信息不改，所有纠偏通过本轮记录完成。
旧违规保留为违规，不追认为合规；本轮不得重复。

## 4. STATE压缩

先原样归档当前HEAD的STATE，保存路径、sha256与完整字节。
只保留四部分：
1. 当前轮次、开工HEAD、F3树、判定器与阶段签收状态；
2. 每轮关键数字短摘要和报告链接；
3. 开放问题标识、状态、去向、详情链接；
4. 最近三轮证据与清单位置，其余指向各轮报告。

删除重复历史长段，不能删除或关闭任何未裁决开放项。
生成STATE_ITEM_CROSSWALK_R8_M1a6.tsv：
旧条目标识、旧位置、新位置或详情位置、状态、去向、保留核对结果。
所有旧开放项必须有去处，核对FAIL=0。
STATE最终UTF-8字节数<=8192。
不以“精简有风险”为由停止，采用原文归档加逐项对照控制风险。

STATE不得包含自身最终提交哈希。
明确区分开工HEAD与收尾提交查询方式。
只有两份正式预注册确实存在并完成校验后，才能写“预注册已生成”。

## 5. 完成正式预注册生成器

新增make_prereg_r8m1a6.py，不修改旧生成器。
复用原续3b1任务书§5的完整范围：
- M1b：G7、G8、4.2、G2b、G3、G4、CTRL_SEAM、G2c、G1、G2a；
  另含S3R4新增22行和多边形33组合的F2/F3行。
- M1c：G5 177点、G6 25点、18对照，F2/F3各一套；
  I1–I6按原登记保留，I7=DEFERRED。

输入为原任务书列明的已提交表，
另允许本轮U201输入快照与本轮U193复核产物。
每个输入记录路径、sha256、来源提交或本轮新增状态。
原始来源行号必须为文件物理行号，不用过滤注释后的伪行号。

每行至少包含：
group、point_id、tree、driver_name、driver_sha256、env、
expected_class、expected_rc1、expect_source、callseq_status、
k_source、status=INFLUENCED。
需要时增加expected_rc2、expected_run_rc、expected_hit、
expected_label、comparison_contract及不变量列。
不能用空值掩盖必需字段缺失。

期望：
- U139(a)–(e)、U142、U196、U197及本轮U198；
- F3不得取旧F结果作期望；
- F2两遍class与rc1一致性逐点核对，包括G5、G6及对照，
  不能只完成旧8组计数；
- NOT_REACHED保留原契约，不能改成成功；
- G2c-control六行NOT_RUN_REGISTRY_ERROR保持不运行，
  若保留在表中必须显式标记，计数与实际执行行分开；
- 58个PLANCALL点重新核对请求和两遍STATE；
  G5其余119点保留K_FROM_HISTORY_AGREED及来源；
- 99对CALLSEQ逐行映射，不只核对总数；
- 新增22行保持19个MAPPING_VERIFIED_STRICT与3个
  NOT_VERIFIED_K0_VERIFY_BY_INJECTION；
  后者保留M1b直接注入验证去向，不伪造K0已验证。

环境按matrix_r2.build_env与expected_env_independent_r7规则推导，
不读取ADD环境列作为答案。
驱动仅从已登记驱动表解析；本轮不运行驱动。

输出到本轮EV，文件名带R8_M1a6：
- REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv
- REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv
- PREREG_INPUTS、PREREG_COUNTS、PREREG_STOP
- K_SOURCE_PLANCALL58
- 逐行来源与映射核对表。

计数按实际子组展开，不只写M1总组；
分别记录原始点数、F2行、F3行、控制/不运行行、重复/缺失、OK/BAD。
原M1 81个F2点是历史交叉核对数字，不是可直接硬编码的答案。
新增22行与33组合按原表语义计数，不能重复翻倍。

先在内存完成全部生成和校验：
必需输入存在、键唯一、两遍一致、环境完整、驱动唯一、
映射符合规则、计数无BAD，才排他写出两份正式预注册。
失败时只写停止与诊断记录，不发布半成品正式表。

不要用NotImplementedError、pass、默认0或硬编码停止代替实现。
实现错误可以在冻结前修正并保留诊断；不是用户裁决事项。

两份正式表写完后立即以独立脚本记录UTC与sha256。
冻结后不得改原表；有实质错误新建ERRATA并明确撤回版本，
不能悄悄覆盖。

## 6. 独立核对与旧记录补齐

新增独立核对脚本，直接从源表重算：
- 各组行数、键集合及F2/F3对应；
- 期望来源、环境、驱动sha、callseq_status与K来源；
- 两个BASELINE_RC_EQUAL对照的四项事实；
- G5/G6/18对照完整性、22行及多边形完整性。

核对器不能只读取生成器的OK列，不能复用同一个结果当答案。
这是表内容核对，不是运行器dry-run，不执行任何驱动。

将旧GATE_R8_M1a5_END.txt逐字复制为本轮命名的历史输入快照，
写明“旧轮FAILS=2，非本轮门禁”，记录原件sha256。
补充旧HEAD f1cbefe的完整提交信息；
注明当前补录工作区状态不等于旧提交时状态，
旧提交后干净状态引用已有POST记录，不伪造历史现场。

## 7. 收尾与提交

提交前：
1. 完成新报告，实际完成/未完成状态准确；
2. 完成STATE大小及逐项对照；
3. 冻结预注册记录存在，独立核对FAIL=0；
4. 运行本轮end门禁，FAILS=0。

end读取start记录，不使用错位位置参数。
end检查：
- HEAD仍为开工基线、冻结树与判定器未变；
- 允许列表sha256未变；
- RULINGS、ERRATA旧前缀未变、未截断；
- testing/d003历史文件未修改；
- STATE<=8192且开放项对照通过；
- 两份预注册、冻结记录及独立核对有效；
- 本轮文件命名合规、工作区无越界修改；
- 临时区快照与start一致。

门禁自身不检查尚未生成的自身副本或最终清单，
避免循环依赖。
end完成后再复制所有本轮小表、start/end门禁、输入快照、
STATE历史、核对表与冻结记录到registries。
逐件核对字节及sha256，写新SHA256SUMS_R8_M1a6.txt。
旧SHA256SUMS文件不改。

证据清单覆盖最终日志、表和文本证据；
清单自身、后续POST记录及仍可能追加的safe_run日志
不建立自引用或假冻结。
对此明确列出排除原因；
POST记录生成后另写一个新POST清单，不修改已冻结清单。
如封存safe_run日志，用副本记录该截点，标明原日志为活文件。

归档完成后执行只读收尾核对：
复制件一致、清单OK、允许列表及表哈希未变、git diff范围正确。
再执行提交脚本。
提交脚本自身、复制脚本与全部新输入快照必须在逐路径git add清单中。
不用git add -A或git add .。

完成时提交信息：
P05-S4 R8 M1a cont3b1 fix: formal preregistration, baseline control contract, STATE <=8KiB, record corrections (no runs); awaiting user review

未完成时提交信息必须写实际停止点，不能声称预注册或STATE已完成。

提交后不再修改任何已跟踪文件。
用本轮脚本把完整git log -1、git log -3 --oneline、
git status --short写到EV的新POST文件，并在最终回复贴出真实记录。
status应为空，HEAD:S4不变。

## 8. 停止条件与最终回复

真实停止条件：
身份/完整性失败；非脚本缺陷的start失败；
源表缺失或不可核验；两遍事实不一致；
映射不满足U196；计数BAD无法在规则内消解；
必须改变已冻结允许列表、历史装置或S4才能继续。

发生停止：
登记具体点与依据，继续不依赖该项的工作，
执行end并做如实记录提交。
身份或完整性失败时不追加裁决、不提交受污染内容。
实际执行越界或绕过safe_run时立即停止该执行路径并披露，
不得再做探测验证。

“工作量大”“生成器尚未写完”“STATE精简有风险”
不是新的技术停止条件。

最终回复纯Markdown，不超过40行，无HTML。
列出：真实提交记录、门禁、两份预注册行数与sha256、
独立核对、STATE字节数、归档核对、违规两张表、剩余停止项。
无新增违规也分别写“无”。

结尾二选一：
本轮已完成 R8 M1a 续3b1补正范围，等待用户审核
本轮未完成 R8 M1a 续3b1补正范围（停止点：…），等待用户审核
