# 任务：P05-S4 R8 M2a3（r8m2a3）
主题：修正 M2 有效预注册的状态采集、双失败恢复索引、对照映射与正式判定完整性。
这是 P05-S4 的子轮次，不是新正式阶段。

一、目标与边界

本轮只完成进入 M2b 前必要的最小装置/预注册修正：
1. 不运行任何 S4 驱动、运行器或 gdb。
2. 可以运行不链接 S4 的合成数据自检，必须经本轮脚本和 safe_run。
3. 不修改 S4/，不修改历史脚本、判定器或历史冻结预注册。
4. 不做 M2b、M2c、M3，不跑 make test，不展开 Python/Lua E2E。
5. 不宣布任何正式阶段完成，不询问签收。
6. 不将本提示词中的规划建议登记成用户已批准的裁决。
7. 不重做已经有效的构建、搜索表和历史证据；只修本任务指定缺口。

二、开工读取与门禁

按顺序读取：
- checkpoints/p05/STATE.md
- AGENTS.md
- PROJECT_ROADMAP.md 的 P05 验收行及阶段收口规则
- checkpoints/p05/P05_S4R8_M2A2_REPORT.md
- checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a2.md
- checkpoints/p05/registries/s4r8/M2/r8m2a2/BRIEF_M2a2_CONT1.md
- 本轮涉及的预注册、索引表、构建表、状态采集脚本及判定脚本

开工要求：
HEAD=c66b7d2ca11927b5de652e5db8cfd8e7e215fbc8
HEAD:S4=6cff923a02baf19e01966b2339755cbf3a5deeef
judge_d003.py sha256=
d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb

开工工作区应干净。只在真实基线异常、无法解释的越界改动、
明确安全/完整性硬停止条件下暂停。
本轮合法中间产物令工作区非空，不是停止理由。

记录 start 门禁、历史 __pycache__/.o 等基线清单与 mtime，
以及 /tmp 顶层只读快照。end 只判新增/变动，不把历史残留误报为本轮产物。

三、写入与命令纪律

本轮 EV：
checkpoints/p05/evidence/p05-s4r8/m2a3

每条含写入命令开头先执行：
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"

后续实际操作必须经：
sh testing/d003/safe_run.sh p05-s4r8/m2a3 -- <本轮脚本>

safe_run 后只接本轮新增的 python3 -I -B 脚本或 sh 脚本；
不得接内联 python -c、sh -c、mv、mkdir、true 或二进制。
内联命令不得含任何 > 字符。
读文件用 read，检索用 grep/glob 工具。

脚本和报告正文可用文件编辑工具创建；脚本的执行及生成物统一走 safe_run。
每个脚本首次运行前扫描禁止路径和命令。
禁止项扫描不得错误匹配合法的 $EV/tmp 或 Python 位移表达式。

禁止仓库外写入，禁止沙箱探测、拒绝性路径测试、
删除历史证据、覆盖历史结果和隐藏 stderr。
不修改 safe_run.sh，不开发同类守卫。

新增脚本名称带 r8m2a3。
复制历史脚本时保留原件；复制品移除不合规 /dev/null 首段，
在 SRC_DIFF 中列为预期修改。
移动或删除之前，必须先核实绝对目标路径；本轮优先不移动、不删除。

四、先做静态审计，生成缺口表

新增 audit_prereg_r8m2a3.py，从文件读取生成：
PREREG_EXECUTABILITY_AUDIT_R8_M2a3.tsv

逐行检查原 150 行：
- point_id 唯一、字段数量、tree/driver/lib 身份；
- 非空预期值是否有实际采集路径；
- exp_I1..I6=HOLD 的行是否指定状态采集器、适用性与控制点；
- gdb_script=- 但要求私有状态的冲突；
- inj_call、快照索引和 retry_call 是否符合实际驱动源码；
- 双目标是否显式覆盖 rc1、rc2、rc3；
- I6 是否绑定同配置控制点和同调用序号；
- sanitizer 的 exp_san 与 I7 的定义及采集方法；
- 正式判定器是否覆盖该行全部适用断言。

不得把缺证据输出成 HOLD，不得用“有 dbg 符号”代替采集入口。
所有问题定位到 point_id、字段和来源文件行号。

五、修正有效预注册，但不改旧文件

原始文件保持逐字节不变：
registries/s4r8/M2/r8m2a2/PREREG_M2_R8_M2a2.tsv
sha256=
1b60f95ccb1ab4b77e26d71fc1d9bf4f4fee25c29092ae0c3620a6c9e42be7ce

新增本轮 ERRATA，说明缺口、受影响字段及替代关系。
不得改原期望来消除未来 MISMATCH。

生成：
- PREREG_M2_EFFECTIVE_R8_M2a3.tsv
- 对应 sha256 和 UTC 冻结时间
- PREREG_DIFF_R8_M2a3.tsv
- CONTROL_MAPPING_R8_M2a3.tsv
- INVARIANT_SPEC_R8_M2a3.md

要求：
1. 默认保留原 150 个 point_id、driver/env、原事实期望和 60/90 分类。
   不擅自加入 win:64 或 1D+FFT 新范围。
2. 明确 gdb_script/state_collector、采集方式及脚本 sha256。
3. 明确 target_layer、control_point_id、output_call 和 control_output_call。
4. I1–I6 沿用 R6c v2 定义，不重写其含义。
5. 对不适用项写 N/A 或 -；对缺证据项写 UNOBSERVED/UNJUDGED，
   不能以“未采集”冒充“不适用”。
6. 明确 I7 与 sanitizer 报告之间的关系；若同一证据重复使用，要说明，
   不另造未经定义的不变量。
7. 如确需增加辅助控制行，先从源码证明原控制不能复用，
   在设计差异中单独列出、事前冻结；总数必须重新计算，
   不为了维持 150 而留下缺失控制，也不无理由扩点。

特别修正 M2-04：
- 保留同层 NTH2=2、跨层 NTH2=4。
- 显式登记 rc1=20、rc2=20、rc3=0，以及各次失败和恢复断言。
- 第一次失败：call1 前 k=0、失败后 k=1，重试前 k=2。
- 第二次失败：call2 前 k=2、失败后 k=3。
- 最终恢复：call3，恢复前状态为 k=3、恢复后 k=4。
以上需按实际驱动源码复核，不盲抄。
- 两次失败分别指定目标层、请求层获取方式及适用不变量。
- I5/I6 对最终成功恢复必须检查 call3，不再把 call2 当作成功恢复。
- 对照同样比较 call3 的输出。
- 不给第二次失败虚构驱动并未提供的新快照。

六、补齐状态采集与分析脚本

只新增 r8m2a3 文件，不改 r8m2a2 或更早已提交脚本。

优先复用 r6c_state 的只读采集逻辑：
R6BSTATE、R6BCLM、R6CREQ、solved、mode/cache、每次调用输出。

本轮只做静态核验，不运行 gdb。
核实断点符号和驱动快照存在，采集器支持对应驱动布局。
逐点生成 STATE_COLLECTION_PLAN_R8_M2a3.tsv。

sanitizer 行如仍要求 I1–I6：
必须明确可执行的采集方案及其限制。
不得默认 ASan/LSan 在 gdb 下仍与独立运行等价。
如需要 sanitizer 独立运行与 dbg 状态配对运行，
明确两类证据、配对键、各自判定范围，不能把配对 dbg 的结果
冒称 sanitizer 进程中已经观察到的私有状态。
无法做到的列明为未判定，不能声称矩阵完全可判。

七、补正式判定器与合成阳性对照

新增正式 verdict_m2_r8m2a3.py，
只读导入 sha256 核验通过的 judge_d003.py。

必须支持：
- 两遍分别与期望比较，单独输出 MISMATCH 和 FLAKY；
- rc3 与双失败事件断言；
- NZ、信号、命中次数、状态不变量、sanitizer 报告；
- 缺失值和缺失证据明确报错/未判定，不能当作 0 或 HOLD；
- 预注册和两遍结果的重复 ID、缺行、多行、tree 不符检查；
- 控制映射、输出调用序号及实际输出文件存在性检查；
- 基于事实重新分类，不信任驱动 PASS/FAIL 文案。

新增 posctrl_m2_r8m2a3.py，必须调用正式判定脚本，
不得用另一份复制逻辑自证。
所有用例为不链接 S4 的合成数据：
A 完全匹配；
B 改 rc1；
C 仅第二遍改值；
D NZ=0 与 NZ=20；
E 改 I 观察值；
F 双失败后 rc3 非零；
G 缺 gdb 状态；
H 重复/缺失/多余 point_id；
I tree 不符；
J 控制点或输出调用序号错误；
K sanitizer 报告非零。

每例事先给定预期结果，并核对具体失败 point_id/字段。
这里只是合成数据自检，不是路径拒绝测试或沙箱探测。
输出路径由参数指定，拒绝覆盖已有结果。

八、本轮不解决的事项

以下只更新待处理计划，不自行裁决：
- M2-02：有限范围 NOT_FOUND_IN_SCOPE 的结论与既有 S5 去向；
- M2-08：原网格 NOT_FOUND；1D+FFT 类候选另列设计建议；
- 已披露偏离是否接受；
- 五个 win:64 的后续 gdb 索引诊断。

win:64 不混入本轮有效运行矩阵。
给出后续“诊断运行→确认索引→补预注册→正式两遍运行”的方案。
诊断观察必须标 INFLUENCED，不能回填成事前验证。

九、完整性与收尾

生成 COMPLETENESS_R8_M2a3.tsv，逐点证明：
每个非空预期断言都有采集入口、来源、分析规则和必要对照。
仅有点数、非空文件或构建成功，不能判完整性 PASS。

核对：
- 原预注册、历史 registry 与 S4 树不变；
- 新预注册各项合计=总行数；
- 测试/控制计数与设计差异一致；
- 所有引用的脚本和产物身份明确；
- 正式合成自检全部符合预期；
- 无任何实际 S4/gdb 运行；
- 无无法解释的新增越界改动。

端到端证据链仍有缺口时，报告具体 UNJUDGED/BLOCKER，
不以 WORK_COMPLETE 或数字齐全掩盖。

小表原名复制到：
checkpoints/p05/registries/s4r8/M2/r8m2a3/
生成 SHA256SUMS.txt 并逐项校验与证据原件相同。
证据日志、表格生成证据清单；二进制只记哈希，不提交。

更新一页以内 STATE，新增本轮报告和 M2b 交接计划。
历史报告不覆盖，勘误只能追加。
U 表只登记用户已经明确授权的内容，不能把规划建议冒充裁决。

end 门禁只检查范围、安全、冻结身份和证据完整性；
已预期的测试失败不等同于路径门禁失败。
end 门禁 FAILS 非零不得提交。

提交仅限 checkpoints/p05/ 与 testing/d003/，
提交信息以 awaiting user review 结尾。
git add/commit 等写入也放入本轮脚本并经 safe_run，
不得使用 checkout/reset/clean/stash/gc/fsck 等禁用命令。

提交后以本轮 postcommit 脚本只读核对 HEAD、S4 树、
冻结哈希和工作区；postcommit/end 门禁小表也须有可恢复的归档说明，
不得声称已提交一个实际仍被 evidence 忽略的文件。

最终简短中文汇报：
1. 静态审计发现与修正数量；
2. 原 150 行保留情况，新增辅助行及理由（若有）；
3. 双失败的两组失败索引和最终恢复索引；
4. gdb/状态采集与控制映射覆盖数量；
5. 正式合成自检结果；
6. 有效预注册哈希；
7. 尚未解决的真实阻塞与后续建议；
8. 两张违规披露表、start/end 快照；
9. git log -1、git status --short、postcommit 原文。

本轮结束后等待规划者审核，不自行运行 M2b。
