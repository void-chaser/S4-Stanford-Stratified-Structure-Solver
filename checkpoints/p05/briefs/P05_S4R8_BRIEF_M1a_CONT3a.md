# P05-S4 R8 M1a 续3a：完整无注入调用序列映射与新增项映射复核

你是 P05-S4 的验证执行者。

本轮属于 P05-S4 R8 M1a 续3a，不是新阶段。
不得宣布任何阶段完成或签收，不写签收建议。
不修改 S4/，不修改 testing/d003/ 下任何已提交文件。
不做任何失败注入，不运行 M1b/M1c 回归，不生成它们的正式预注册或运行器。
本轮仅完成：
1. 续2c 的接受记录及 E8-55 分类更正；
2. F2→F3 无注入调用序列映射；
3. S3R4 新增项的 F3 映射复核；
4. 门禁、归档、报告及一次记录提交。

工作量不是停止理由。技术停止也必须整理已产生证据；
但身份或完整性门禁未通过时，不得强行提交。

## 0. 开工与路径

先读 checkpoints/p05/STATE.md，并只读核对 HEAD、HEAD:S4、status；
再读 PROJECT_ROADMAP.md 的 P05 行、AGENTS.md、本任务书。
随后将本任务书原文存为：
checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3a.md

基线：
HEAD = 331c022c3d9944cff8e7e63e16c24d33253ce847
F2 提交 = a07b5ac
F2 S4 树 = e124925f5b242486a913b813fa181664f665b048
F3 提交 = 8d8202a
F3 S4 树 = 6cff923a02baf19e01966b2339755cbf3a5deeef
判定器 sha256 =
d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb

证据目录沿用：
checkpoints/p05/evidence/p05-s4r8/
新脚本目录：
testing/d003/stage_s4r8/
小表目录：
checkpoints/p05/registries/s4r8/M1a/
报告：
checkpoints/p05/P05_S4R8_REPORT_M1a_CONT3a.md

新脚本/数据名含 r8m1a4；
新证据/小表名含 M1a4。
已有证据、脚本、清单不覆盖。
ERRATA_8、RULINGS 只追加；STATE 可以摘要更新。

必读：
- 续2c 报告及 brief；
- 续1 brief §5、续2 brief §5；
- gate8_r8m1a3c.sh、recheck_s4r7_r8m1a3c.py；
- DRIVERS_R8_M1a.tsv、DRIVERS_R8_M1a_F2_REUSED.tsv；
- R7 M1/M2/M2_ADD_v3/M2_CTRL_SEAM/M3 登记表；
- R7 实际运行器的驱动选择与环境构造；
- 本轮涉及的注入器源码；
- a1map_c2_v2.sh、a1map_c2.gdb、
  b_map_run_c3.sh、b_map_c3.gdb；
- A1_MAP_SUMMARY_S3R4C2.tsv、B_MAP_C3.tsv、
  R8_ADDITIONS_S3R4C3.tsv。

路径均以仓库根为基准，不把 stage_s4 等简写误作根目录路径。

## 1. 写入、安全与命令规则

所有 shell 执行脚本开头使用：
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"

含写入的执行必须经：
sh testing/d003/safe_run.sh p05-s4r8 -- ...

写入目标只能位于：
$EV/
$REPO/testing/d003/
$REPO/checkpoints/p05/

源码、任务书、数据、报告可用 read/edit/write 工具处理；
运行产物、追加、复制、清单及提交操作用经 safe_run 的新脚本。

Python 启动一律 python3 -I -B。
gdb 内嵌 Python 不受这个启动形式约束，但不得产生 pycache；
启动 gdb 的清洁环境设 PYTHONDONTWRITEBYTECODE=1。
不用 py_compile。

内联 shell：
- 写入只调用一个经 safe_run 的新脚本，不用 sh -c；
- 普通只读核对仅用于 git 身份/状态、sha256、时间；
- 文本读取用 read，搜索用 grep，文件发现用 glob；
- 复杂只读核对需要保存结果时写成新脚本，经 safe_run；
- 内联不得出现任何 > 字符，包括 2>&1；
- 不做拒绝性测试、反例探测或沙箱写入探测；
- 不使用 forbidden git 操作，不删除任何已有文件。

开工、收尾各一次顶层临时区只读快照，允许准确形式：
date -u +%Y-%m-%dT%H:%M:%SZ; ls -A /tmp | wc -l; ls -A /tmp | sha256sum; date -u +%Y-%m-%dT%H:%M:%SZ
结果写入门禁；不得自行填默认值。

运行前逐文件用 grep 工具检查：
/dev/null|DEVNULL|devnull|<<-?\s*['"]?[A-Za-z_]|sed -i|python3 -c|cat >|tee |rm -rf|(^|[^V])/tmp

结果必须为 0 行才能运行。
运行前的未执行草稿可修正，然后重新检查。
检查范围是本轮可执行文件和被消费的数据；
原始历史文档不因正文含历史路径而被要求改写。
不修改冻结 safe_run.sh；它的历史内部实现不算本轮新增违规。
使用 prerun_log_r8m1.sh 记录真实命中数及文件 sha256。

命令失败必须检查实际退出码。
不得用末尾 date 的成功掩盖 safe_run 的失败。
后台作业记录 job id，等待完成后收集，不重复启动。

## 2. 裁决记录：start 门禁通过后追加

RULINGS 每行 5 列、4 个 TAB。
来源为本任务书 §2，只有本任务书被用户下发后才记生效。

U176：
接受续2c A/B 两段提交、静态映射及已披露事件。
接受范围不是阶段签收，也不是动态映射完成。

U177：
E8-55 采用排除注释及明确“不使用”引用的规则。
v3c 原件保留；两处 FFT:90、kottke:94 的有效分类改为 NO；
有效统计 BP_LINE 2、REGISTRY_ONLY 26、NO 3。
生成 USED_IN_M1_CORRECTION_R8_M1a4.tsv，包含旧值、新值、
引用出处和裁决号；不重跑静态映射。
其他映射行号、函数和状态不变。
STATE 同时保留“v3c 历史统计”和“U177 生效统计”的区别。

U178：
采用本任务书 §1 的命令规则。
续2c 的命令偏离仍是执行偏离，不因新规则倒推成历史合规。

U179：
优先用 M1b/M1c 实际对应的 F2/F3 驱动做无注入映射。
不得仅因文件名带 dbg/plain 判定实际构建身份；
逐一核对驱动表的路径、驱动哈希、库身份及驱动族。
不另链 r6dnv1-F3-dbg；U151 的该链接要求由本条替代。
实际驱动若无法可靠获取调用序列，停止报告，不自动换驱动。

U180：
新命名使用 r8m1a4/M1a4。
预计组合数只作工作量参考，不作为覆盖证明或通过条件。

U181：
不采纳“K=1 seam 可全部跳过映射”的建议。
G2a/G6 的 site/ID 钩子仍做无注入计数序列核对。
无注入控制行写 N/A，不写 K1_HIT_CHECKED。
命中数检查仍保留到未来回归，但不能替代本轮映射。

U182：
续3b 才生成正式预注册、逐组计数、dry-run 和回归运行器。
所需映射必须完整、无追踪错误；未完成项不得被 N/A 掩盖。

ERRATA 从 E8-56 起：
记录 E8-55 澄清、本任务书对上一版建议的替换、
实际驱动映射口径、完整 seam 覆盖要求。
另追加续2c 报告的两项记录差异：
1. 正确 sh 调用为 03:35:00Z，误用 Python 为 03:35:59Z；
   “之后用 sh”是时间顺序表述错误；
2. endB 使用独立 SHA256SUMS_M1a3c_B_END.txt，
   不是补入原 B 清单；独立清单已通过。
旧报告不改，作为补充说明记录，不作废结果。

## 3. 开工与收尾门禁

新增 gate9_r8m1a4.sh，参考 gate8；
只保留本轮 start/end 模式，旧脚本不改。

参数：
start <OUT> <TC> <TS>
end <OUT> <START_FILE> <TC> <TS>

任何结果文件已存在则拒绝，不覆盖。
输出名 GATE_R8_M1a4_*.txt；
子 recheck 输出名由 OUT 派生，避免写死重名。
end 从 start 文件读取开工快照和身份，不手填开工值。

共同检查：
- 分支、HEAD、F2/F3 树、判定器；
- F2→F3 S4 差异文件列表排序后恰为原 4 文件；
- REGISTRY_S3R4C3_D.tsv 哈希及 s3r4c5 清单，沿用 gate8；
- s4r7 清单沿用其分类复核规则，不裸跑全部 -c；
- s4r8 根清单 ERRATA_8 按前 13990 字节前缀检查，
  其余静态项校验；
- M1a 目录四份清单：
  SHA256SUMS.txt
  SHA256SUMS_M1a3c_A.txt
  SHA256SUMS_M1a3c_B.txt
  SHA256SUMS_M1a3c_B_END.txt
  均逐项校验；
- 原有 tracked testing/d003 文件与 HEAD 相同。

start 常量：
RULINGS 66509 字节，
77ca58673d471b8122b7c805cbd77c4aac65923c89c800241118132b426376d5
ERRATA_8 37669 字节，
ff958d246e6fb967e2c8f524c9376d48d34833c861fd83651ebff581d6eab725
PRERUN 前 5603 字节，
8eb5c81a07ba467d36c8b6a760cc72e1d817887fe956638c7e598e754d43687d

start 只允许本轮 brief 和本轮新脚本/数据未跟踪；
此前工作区必须干净。
end 在提交前运行，HEAD 仍为 331c022，不检查提交前 HEAD^。
RULINGS、ERRATA、PRERUN 的开工前缀不变。
允许变更限定 STATE、RULINGS、ERRATA、本轮报告/brief、
本轮新脚本及本轮 registries 小表。

门禁参数/命令自身错误允许新输出名 _R2 重跑一次并披露；
哈希、身份、历史文件变化或未授权路径等数据失败不得重跑消除。

## 4. 先生成完整映射需求与期望，再运行

新增 counted_families_r8m1a4.py。

读取 R7 登记表、ADD_v3、实际运行器和 S3R4 新增表，
记录源文件 sha256、来源行号，按键关联，禁止依赖行顺序。

输出：
SOURCE_HASHES_R8_M1a4.tsv
COUNTED_FAMILIES_R8_M1a4.tsv
CALLSEQ_UNITS_R8_M1a4.tsv
CALLSEQ_POINT_COVERAGE_R8_M1a4.tsv
EXPECT_CALLSEQ_R8_M1a4.txt

覆盖表必须将每个未来回归点关联到：
- 一个具体计数族/单元/site；
- 或无注入 N/A；
- 或有原裁决出处的 NOT_RUN。
未识别的请求记 UNMAPPED 并停止。

单元去重键至少包含：
驱动身份、mode、NG、完整无注入环境、argv。
不只按 mode/NG 去重，不能合并 once/twice 或不同驱动族。
同单元可以在一次 gdb 运行中追踪多个所需计数族。

计数语义必须来自对应注入器：
- s4malloc：wrapped S4_malloc 次数；
- exec：wrapped fft_plan_exec 次数；
- plan:N：第 N 次 plan 中的第 N 次 wrapped malloc；
- plancall:K:M：第 K 次 plan 内第 M 次 wrapped malloc；
- rnv1:M：每个 Pattern_GenerateFlowField 窗口内计数重置，
  在首个到达 M 的窗口命中，不能用全进程累计数替代；
- seam：按具体 hook/site/ID 各自计数；
- 新增 A 的 init:K、win:M 与新增 B 的 win:M，
  必须区分注入器不同口径，不混为同一计数族。

环境复用历史构造规则，保留 TWICE、NG、lattice 等语义；
去掉 INJECT、NTH 及所有不需要的 dump/injection 状态。
不从宿主继承任意 FMM_/S4FMM_ 变量。

期望状态 INFLUENCED。
先写入“完整覆盖、无追踪错误、序列相等或唯一允许改名”的期望，
记录 sha256 和 UTC，之后才允许运行。
运行后不得修改该期望。

## 5. 无注入 gdb 追踪

新增 callseq_r8m1a4_gdb.py 与 runner。
gdb 用 -batch -nx，仅函数/符号断点，不用文件行号断点。
不改变 inferior 返回值、寄存器、内存或计数器；
不调用 inferior 的函数来取计数。

追踪规则：
1. 为实际需要的 __wrap_* 和 seam hook 设置断点；
2. plan/window 用入口与 FinishBreakpoint 维护运行期上下文；
3. 所有 stop() 返回 False；
4. 捕获 exited 事件及异常，输出结构化结束记录；
5. pending/unresolved breakpoint、FinishBreakpoint out_of_scope、
   追踪异常不能静默忽略。

记录：
- #0 被计数函数、#1 调用者函数；
- 全局或 per-site 序号；
- plan/window 的序号；
- 每个 plan/window 内 wrapped malloc 的序号及调用者；
- seam 的 site/ID；
- malloc 大小可作辅助核对，不改变原判定规则。

必须同时输出 plan 内 malloc 明细，不能只输出 m 总数。
输出标准 TSV/JSONL 或明确转义字段，不能靠空格 split 解析 C++ 名字。
比较不含地址、参数和文件行号。

无调试参数信息的 plain 二进制：
允许使用明确记录的当前 x86_64 ABI、入口寄存器读取 hook ID，
断点必须在函数入口地址，不能在执行 prologue 后猜参数；
优先使用可获取的 DWARF 参数。
参数/site 无法确定时记 TRACE_ERROR，不默认为 0。

符号缺失：
- 与该单元无关的族：N/A；
- 该请求必需的符号缺失：REQUIRED_SYMBOL_MISSING，停止；
- 不得把必需族 ABSENT_BOTH 当通过。

帧名缺失：
原日志可保留 ??，但所需序列包含无法可靠解析的帧时记 TRACE_ERROR，
不得以 F2/F3 都为 ?? 判相等。
允许通过本二进制符号表解析真实函数名，不臆造名称。

实际运行：
F2 先于 F3；每单元各一次，无注入。
所有运行在 safe_run 管理的新 runner 内。
运行前核对路径与驱动哈希；
env -i，PATH、LANG=C、LC_ALL=C、
PYTHONDONTWRITEBYTECODE=1，加登记的必要环境。
不设 INJECT、NTH；不产生仓库外文件。

原始日志位于 $EV/callseq_r8m1a4/。
输出 CALLSEQ_RUNS_R8_M1a4.tsv：
单元、树、命令/环境、驱动哈希、开始/结束 UTC、
gdb rc、inferior exit、信号、trace_error。

gdb rc=0 本身不证明追踪成功。
无结束记录、异常、信号、超时、必需断点无法解析均 RUN_ERROR。
进程 exit 与 rc_first/rc_retry 区分记录；
无注入已知非零应用返回值按历史事实保留，不冒称 CONTROL_OK。
F2/F3 对应事实不同记 DIFFERENT。

## 6. 比较、有效性及 K/M 可达性

新增 compare_callseq_r8m1a4.py。

唯一名称归一：
F2 shape_get_intersection_area_quad
对应 F3 shape_get_intersection_area_quad_st。
先比较原序列；只因这项归一后相同才写 IDENTICAL_AFTER_RENAME。
其他差异一律 DIFFERENT。

必须比较完整有序事件，包括：
- 被计数函数与调用者；
- plan/window 开闭及内部 malloc 明细；
- seam 的 per-ID 序列；
- 请求相关的进程退出/应用返回事实。
事件数量与结束汇总相符，序号连续，上下文成对闭合。

空序列：
必须有“符号已解析、运行正常、该族确实零调用”的证据。
两条空序列不能单独作为有效通过证据。
对历史预期会命中的点，新出现零调用应判覆盖/可达性错误并停止。

输出：
CALLSEQ_F2_F3_R8_M1a4.tsv
CALLSEQ_VALIDITY_R8_M1a4.tsv
CALLSEQ_KMAX_R8_M1a4.tsv
CALLSEQ_POINT_COVERAGE_CHECK_R8_M1a4.tsv

K/M 检查按真实语义：
- plan:N：检查存在 plan N，且其内部 malloc 数至少 N；
- plancall:K:M：检查 plan K 内部至少 M 次 malloc；
- rnv1:M：检查是否有窗口达到 M，不用全局累计总数；
- seam：检查指定 site/ID 第 K 次调用；
- s4malloc/exec：检查对应序列的 K。

超出不自动放行。
只有来源明确预期 NOT_REACHED 的点，才记 EXPECTED_NOT_REACHED；
原本应命中的点超出，记 UNEXPECTED_NOT_REACHED 并停止。
不通过修改期望消除差异。

## 7. S3R4 新增项映射复核

不要求新增 22 行做 F2→F3 期望照搬；
按原规则只复核 F3 的 init-F3、polyinj-F3 映射。

运行前核对它们与 S3R4 记录中的完整 sha256 一致。
先写 EXPECT_ADDITIONS_R8_M1a4.txt 并记录 sha256、UTC。

A：
closed2d-ng1、fft-ng5、kottke-ng5；
复核 win_open、win_malloc_in_window、outside_malloc_count、
K_init、K0、caller_function_of_K、status。

B：
fft/kottke × NG 1/5/9；
复核 Mtot、Mfirst、n_values、
RC_first、RC_retry、inject_hits。
polygon_breakpoint_hits 沿用历史实际推导口径；
历史是从 n=36/调用者推导的，不伪造为新命中的源码断点。

复制历史脚本为本轮新文件，允许且必须：
- 替换标准首段、证据参数和驱动路径；
- B 循环改为仅 F3；
- 调整输出目录和文件名；
- 使用 -nx；
- 增加输入/哈希/退出状态/无覆盖检查；
- 修正裸 sh -c 或禁止项为等效脚本实现。
这些属于授权的装置调整，不要求“只改路径”。

原件不改，生成 RUNNER_DIFF_R8_M1a4.txt，逐处说明。
A/B 原始绝对地址、load base、源码行号和目录不是相等判据；
核对真实函数身份及计数。
输出 CALLSEQ_ADDITIONS_R8_M1a4.tsv，9 个组合均须有结果，
并建立其与 22 行新增登记项的逐项对应表。
不把 9 个映射组合冒称 22 次注入验证。

## 8. 停止与收尾

技术停止：
UNMAPPED、TRACE_ERROR、RUN_ERROR、DIFFERENT、
UNEXPECTED_NOT_REACHED、新增映射 MISMATCH。
不改规则、不重复运行同一观测来挑结果。
停下剩余运行，保留原件，做记录收尾。

身份/完整性停止：
HEAD/树/判定器/历史文件不符、未经授权路径、
写入违规或 end 门禁 FAIL。
不得强行提交；报告真实状态和未提交文件，交用户处理。

start 门禁未成功：
不执行裁决追加和驱动运行；
不要求一个不存在的成功 start 文件；
只保留失败门禁及停止说明，不提交。

技术停止时可以提交：
前提是 start 成功、end 完整性门禁 FAILS=0。
报告写未完成及停止点，缺少的结果表列为未生成，
不要创建虚假的空结果去满足复制清单。

## 9. 归档、报告与一次提交

复制本轮已生成的小型表、期望、源哈希、裁决追加记录、
分类更正、有效性、逐点覆盖、门禁、脚本差异及新增项对应表
到 registries/s4r8/M1a/，先去重，逐个 cmp。
历史清单不改，新增 SHA256SUMS_M1a4.txt 并全部校验。

原始大日志不提交；证据清单记录其 sha256。
清单不把自己列入，不预先宣称覆盖尚未生成的 end/FINAL 文件。
采用分批清单：
- 主结果清单；
- end 门禁与对应 recheck 的 END 清单；
- 提交后 FINAL 的证据专用清单。
PRERUN/safe_run 活日志按收尾快照记录，不冒称永久全文哈希不变。

STATE：
写真实的运行单元数、比较行数和各状态计数，区分两种分母；
同步新增映射组合和 22 行对应覆盖；
E8-55 写历史统计及 U177 有效分类；
成功写“下一步续3b”，停止时不得这样写。
不写零 DIFFERENT，除非实测确为零。

本轮新报告补充续2c 的记录差异，旧报告不改。
报告必须区分：
准备证据 / 无注入映射 / 尚未做的注入回归。
保留违规两张表、未完成项、待裁决项。

收尾快照后运行 end 门禁。
FAILS=0 后才执行新 commit_rec_r8m1a4.sh：
- 复制 end 门禁和对应 recheck，逐项比对、补 END 清单；
- 逐路径检查、逐个 git add，不用 -A 或 .；
- staged 路径只限本轮批准范围；
- 核对未修改任何既有 testing/d003 tracked 文件；
- 一次提交，末尾 awaiting user review。

成功提交信息：
P05-S4 R8 M1a cont3a: complete no-injection F2-F3 counter/site sequence mapping and S3R4 additions map recheck; E8-55 clarification; awaiting user review

技术停止的提交信息明确 stopped 和停止点。

提交后写 FINAL_GIT_R8_M1a4.txt：
git log -3、HEAD、HEAD^、HEAD:S4、git status --short。
期望 HEAD^ 为 331c022，S4 树不变，status 空。
提交后不修改 tracked 文件。
对话中原样贴出最终 git 记录。

结尾：
“本轮已完成 R8 M1a 续3a 范围，等待用户审核”
或
“本轮未完成 R8 M1a 续3a 范围，等待用户审核”。
