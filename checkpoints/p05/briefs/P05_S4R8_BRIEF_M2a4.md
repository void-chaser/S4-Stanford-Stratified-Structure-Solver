# 任务：P05-S4 R8 M2a4（r8m2a4）
主题：补齐 M2 执行链（运行器、事实提取、状态分析器、判定器 v2），修正 r8m2a3 判定缺陷，用历史真实 gdb 日志回放验证。
这是 P05-S4 的子轮次，不是新正式阶段。

一、目标与边界
1. 不运行任何 S4 驱动、运行器（--dry-run 除外，见 §6）或 gdb。
2. 可以运行：不链接 S4 的合成数据自检；对已有历史证据的只读回放分析（§5.3）。都经本轮脚本与 safe_run。
3. 不修改 S4/、历史脚本、判定器 judge_d003.py、历史冻结预注册（含 r8m2a2 的 1b60f95c… 与 r8m2a3 的 27e33b27…）。
4. 不做 M2b 正式运行、M2c、M3；不跑 make test；不宣布阶段完成；不询问签收。
5. 不把规划建议登记为裁决；U 表只登记 §3 列出的用户已确认条目。
6. 不重做已有效的构建、搜索表、索引推导。

二、开工读取与门禁
按序读：checkpoints/p05/STATE.md；AGENTS.md；checkpoints/p05/P05_S4R8_M2A3_REPORT.md；checkpoints/p05/briefs/P05_S4R8_BRIEF_M2a3.md；
registries/s4r8/M2/r8m2a3/ 全部小表（尤其 PREREG_M2_EFFECTIVE_R8_M2a3.tsv、CONTROL_MAPPING_R8_M2a3.tsv、INVARIANT_SPEC_R8_M2a3.md、STATE_COLLECTION_PLAN_R8_M2a3.tsv）；
testing/d003/stage_s4/verdict_m2_r8m2a3.py、posctrl_m2_r8m2a3.py、r6c_judge.py、run_r6c_state.py、r6c_state_gdb_r8m2a3.py、driver_r8m2a2_layers_R2.cpp、driver_r6b_state.cpp、inject_r8m2a2_dual_R3.cpp；testing/d003/judge_d003.py；testing/d003/src/driver_d003.cpp。

开工要求：
HEAD=2395f669359795c126f4f4fc2223804c900b06f5
HEAD:S4=6cff923a02baf19e01966b2339755cbf3a5deeef
judge_d003.py sha256=d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb
PREREG_M2_EFFECTIVE_R8_M2a3.tsv sha256=27e33b27ae4a7202e402e223a73f2634b66d70a1288596622be7071280a20a09
git status --short 为空。
只在真实基线异常、无法解释的越界改动、明确安全/完整性硬停止条件下暂停；本轮合法中间产物令工作区非空不是停止理由。
start 门禁记录：历史 __pycache__/.o 基线清单与 mtime、/tmp 顶层只读快照（条目数+sha256）。end 只判新增/变动。

三、本轮登记的用户裁决（RULINGS.tsv 追加；原文照录，来源写「P05-S4 R8 M2a4 任务书 §3」）
U248 M2-02（阶段 e）：接受 r8m2a2 搜索结论 NOT_FOUND_IN_SCOPE；M2-02 在 S4 内不出点，转 S5。
U249 M2-08（类别 C）：接受原网格 NOT_FOUND；1D+FFT 候选（NEEDS_NEW_DRIVER_SCOPE_EXPANSION）不在 S4 扩驱动范围，转 S5 登记。
U250 r8m2a2 已披露的 14 项 safe_run 偏离按执行偏离接受，不追认为合规。
U251 五个 win:64 行（UNRESOLVED_INDEX）：M2b 中先做诊断运行（标 INFLUENCED，不得回填为事前验证）→ 确认索引 → 补预注册冻结 sha256 → 正式两遍运行。本轮只写设计（§7），不运行。
U252 r8m2a3 的结果按以下口径接受：原预注册未变；M2-04 call3 恢复索引、rc3 列、sanitizer UNOBSERVED、I7 与 exp_san 关系等修正有效；但 r8m2a3 的 COMPLETENESS「150/150 PASS / Complete end-to-end evidence chain verified」不成立（无运行器、无事实提取、无 gdb→I 值分析器），由本轮 COMPLETENESS v2 取代；Case J 把 I6 输出差异定为 SCHEMA_ERROR 是设计错误，由本轮更正。
（ERRATA 从 E8-101 起编号，只追加。）

四、写入与命令纪律
EV=checkpoints/p05/evidence/p05-s4r8/m2a4
每条含写入命令开头先执行：
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a4; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
一律经 sh testing/d003/safe_run.sh p05-s4r8/m2a4 -- <本轮脚本>；safe_run 后只接本轮新增的 python3 -I -B 脚本或 sh 脚本；不得接内联 python -c、sh -c、mv、mkdir、true 或二进制。内联命令不得含任何 > 字符（含 2>&1）。读文件用 read，检索用 grep/glob。
写入目标只能以 $EV/、$REPO/testing/d003/、$REPO/checkpoints/p05/ 开头；任何以 / 开头且不在 $REPO 下的路径不得出现（含 /tmp 与占位路径）。不做沙箱探测、拒绝性路径测试，不用 2>/dev/null。长输出带 head/tail 或用 read 的 offset/limit。
复制历史脚本时：原件不动，复制品首行 REPO 行换成标准首段（不含 /dev/null），并在 SRC_DIFF_*.txt 中列为预期修改；除本任务书点名的修改外逻辑逐字不变。
每个脚本首次运行前用 grep 工具扫描禁止项（仓库外绝对路径、2>/dev/null、checkout/reset/clean/stash/gc/fsck）；正则不得误中 "$EV/tmp" 与 Python 的 `1 << 20`。未运行的草稿查出后改正不算违规。
新增文件名带 r8m2a4；不改 r8m2a3 及更早已提交脚本。

五、修正内容

5.1 判定缺陷审计 VERDICT_AUDIT_R8_M2a4.tsv（逐条定位到文件:行号、受影响 point_id 与数量）
至少核对并写明以下项目（以源码复核为准，不盲抄）：
D1 verdict_m2_r8m2a3.py:234-236、279-303：I1–I6 只做字符串比较，无 gdb 日志→I 值的分析，r8m2a3 链路中不存在产生 I 值的脚本。
D2 verdict_m2_r8m2a3.py:252-271：对控制映射全部 28 对做逐字节输出比较，含 M2-06（output_call=1）与 M2-07 注入行（output_call=1，失败调用）——必然 OUTPUT_DIFF；d003plan-F3-plain 驱动写 S4FMM_DUMP1/S4FMM_DUMP（driver_d003.cpp:195,222），不产生 callN.txt——必然 MISSING_DUMP。逐点列出受影响 point_id。
D3 I6 不一致被记为 SCHEMA_ERROR，应为 I6=VIOLATED → MISMATCH。
D4 M2-10 exp_class=BASELINE_ONLY 与 judge_d003.classify 输出集合不交，必然 MISMATCH。
D5 M2-04 只核 exp_hit=2 总数；无目标 1/2 分项命中、无 INJECT2 INVALID/SUPPRESSED 检查（inject_r8m2a2_dual_R3.cpp:153,157）、无第二失败层断言。
D6 r6c_judge.py:31-35 的索引表只支持 inj_call∈{1,2}，不支持 M2-04 的事件序列。
D7 M2-03 无非 sanitizer 参照点（U246「rc 与类别与非 sanitizer 运行一致」不可判）；ASAN_OPTIONS/UBSAN_OPTIONS 与 san_reports 计数规则未冻结。
D8 不存在 M2b 运行器与事实提取脚本；COMPLETENESS_R8_M2a3 的 PASS 不成立。
其他你在复核中发现的缺陷一并列入，同样定位。

5.2 有效预注册 v2：PREREG_M2_EFFECTIVE_R8_M2a4.tsv（另写 .sha256 与 UTC 冻结时间；PREREG_DIFF_R8_M2a4.tsv 记录相对 r8m2a3 的全部差异）
规则：
- 150 个 point_id、driver/env、全部 exp_* 原值不变（diff 中 exp_* 改动必须为 0；如源码证明某 exp_* 必须改，停下列入报告，不得改）。
- 只新增列或填规则列：
  a) class_rule：JUDGE_D003 | BASELINE_ONLY_RULE（M2-10：仅核 rc1/signal/hit 等事实与 gdb 断点记录，类别不由 classify 判）。
  b) output_assertion：I6_ONLY（仅恢复调用对同序号对照调用，比较由状态分析器做）| RECORD_ONLY（记录 sha256 与是否有非有限值，不判）| NONE。M2-06、M2-07 注入行不得做输出相等断言。
  c) 双失败事件列（仅 M2-04，其余写 -）：exp_hit1、exp_hit2、exp_inject2_invalid=0、exp_inject2_suppressed=0、k_before2、k_fail2、fail_layer1、fail_layer2。值由驱动源码与 registries/s4r8/M2/r8m2a2/INDEX_DERIVATION_R8_M2a2_R2*.tsv 推出并写依据（文件:行号）；M2-04-02（PP1、NTH2=4）的 fail_layer2 若无法静态证明，写 UNRESOLVED 并说明，运行时由 R6CREQ/CLM 记录观察，不得猜。
  d) M2-03：san_ref_point_id（非 sanitizer 参照）。REP-INIT/REP-POLY 行参照 M2-01 同 env 测试点；G5/G6 行参照 M1 在 F3 上同 env 的已冻结行（registries/s4r8/M1c/ 与 M1b 体系），写出行号与 sha；找不到的写 NO_REF，该项判 UNJUDGED，不新增点。
  e) san_options：冻结 ASAN_OPTIONS、UBSAN_OPTIONS（须含 log_path 指向 $EV/run/<pass>/<point_id>/ 下，不得指向仓库外），并在 INVARIANT_SPEC_R8_M2a4.md 写明 san_reports 的计数规则（匹配哪些行、跨哪些文件累加）以及 halt/exitcode 对 rc 的影响；I7=HOLD ⇔ san_reports==0。
  f) state_analyzer：本轮新分析器脚本名与 sha256（dbg 行）或 -。
- UNOBSERVED 项在判定中计入 UNJUDGED_BY_DESIGN，不做字符串匹配，不计 MATCH。
- 状态全部保持 INFLUENCED。

5.3 状态分析器 state_judge_m2_r8m2a4.py（从 r6c_judge.py 复制，按复制品规则）
- 改动只限：①索引不再查 U13 写死表，改读预注册每行的 k_before/k_fail/k_preretry/k_retry/retry_call/output_call/control_output_call；②新增双失败事件：I1、I4' 在 k_fail（目标 1 层）判；第二次失败在 k_fail2 判 fail_layer2 的 modes_null；I5 在 (k_preretry..k_retry) 判，且要求 rc3=0；I6 比较 call<output_call> 与对照 call<control_output_call>；③输入路径参数化，输出拒绝覆盖。I1–I6 含义沿用 R6c v2，不重写。
- 输出 HOLD / VIOLATED / N/A / UNJUDGED（缺日志、缺快照、缺 dump 一律 UNJUDGED，不得 HOLD）。
- 回放验证（真实数据阳性对照，只读历史证据，不新运行）：用 checkpoints/p05/evidence/p05-s4r6c/pass1、pass2 下的历史 gdb 日志、dump 与对照，按 REGISTRY_S4_PRE_R6b_STATE_v2.tsv 的索引喂给新分析器，逐点逐不变量与 RESULTS_R6c_STATE.tsv 比较。要求 177 点 × I1–I6 × 两遍差异为 0；有差异则逐条列出原因，不得改分析器去凑（真实实现错误可改，但须重新登记版本并重跑全部回放，披露两版差异）。输出 REPLAY_R6c_R8_M2a4.tsv 与汇总。
- 双失败无历史数据：用合成 gdb 日志覆盖（见 5.6）。

5.4 事实提取 facts_m2_r8m2a4.py
- 从驱动 stdout/stderr 与 gdb 日日志提取：rc（进程退出码）、signal、rc1/rc2/rc3（R6CALLS 行；d003 驱动用其既有 RC 行，规则写明）、hit（HITCOUNT）、hit2、INJECT2 INVALID/SUPPRESSED 计数、san_reports（按 5.2e 冻结规则）、dump 文件 sha256 与非有限值标记。
- 缺失一律写 - 并标 MISSING，不得默认 0。不读驱动 PASS/FAIL 文案。

5.5 判定器 v2 verdict_m2_r8m2a4.py（新文件，只读导入经 sha256 核验的 judge_d003.py）
- 输入：预注册 v2、两遍 FACTS、两遍 STATE（分析器输出）、控制映射；输出路径参数化，拒绝覆盖。
- 类别：class_rule=JUDGE_D003 用 classify；BASELINE_ONLY_RULE 用专门规则。
- I6 不符记 MISMATCH（I6），不记 SCHEMA_ERROR；RECORD_ONLY 只记录。
- 两遍分别对期望比较；FLAKY 单列；M2-03 另比较 rc/类别与 san_ref；NO_REF→UNJUDGED。
- 结构错误（重复/缺失/多余 ID、tree 不符、驱动/库/gdb 脚本 sha 不符）记 SCHEMA_ERROR。
- 汇总断言：MATCH+MISMATCH+FLAKY+UNJUDGED+SCHEMA_ERROR（定义互斥规则）= 150，按 item 再分表；UNJUDGED_BY_DESIGN 与 UNJUDGED_MISSING 分开计数。

5.6 合成阳性对照 posctrl_m2_r8m2a4.py（必须调用 5.3/5.4/5.5 的正式脚本，不得复制逻辑；输出路径参数化）
每例事先写预期（目标 point_id、字段、判定），运行后逐项核对：
A 完全匹配；B 改 rc1；C 仅第二遍改值（FLAKY）；D NZ 对 0 与 20；E 合成 gdb 日志使 I1 违反→分析器 VIOLATED→MISMATCH；
F 双失败 rc3≠0；F2 双失败 hit2=0；F3 出现 INJECT2 SUPPRESSED；F4 第二失败层与 fail_layer2 不符；
G 缺 gdb 日志→UNJUDGED（不是 HOLD、不是 MATCH）；H 重复/缺失/多余 ID；I tree 不符；
J I6 输出不同→MISMATCH(I6)；L M2-07 注入行 call1 输出与对照不同→不报错；M M2-10 rc1=20→MATCH（BASELINE_ONLY_RULE）；
K san_reports≠0→MISMATCH；P sanitizer rc 与 san_ref 不同→MISMATCH；Q san_ref=NO_REF→UNJUDGED；
R 汇总合计≠150 的构造输入→脚本断言失败退出。
合成日志须仿照 r6c_state_gdb_r8m2a3.py 的真实输出格式（R6BSTATE/R6BCLM/R6CREQ）与驱动的 R6CALLS/R6STATE/HITCOUNT 行。
出现第一次失败后修正时，原输出保留，修正版以 _R2 等后缀运行并披露。

六、运行器 run_m2_r8m2a4.py（本轮只写，只允许 --dry-run）
- 读预注册 v2，为每行每遍生成命令：dbg 行 gdb -batch -x <gdb_script> --args <driver> <argv>；plain 行直接运行；san 行带冻结的 san_options；env 逐键来自预注册；S4FMM_DUMP_DIR=$EV/run/pass<n>/<point_id>/；stdout/stderr 分别落盘；超时值写明；两遍目录分开；拒绝覆盖。
- 运行前逐行核 driver_sha256、lib_sha256（如可得）、gdb_script_sha256，不符则该行不运行并记 IDENTITY_FAIL。
- 正式运行模式在本轮禁止调用；--dry-run 只生成 COMMAND_PLAN_R8_M2a4.tsv（300 行=150×2），不得启动任何驱动或 gdb（用 grep 核对脚本 dry-run 分支不含 subprocess 调用）。
- 运行器输出目录结构与 facts/state/verdict 的输入一一对应，在 INVARIANT_SPEC_R8_M2a4.md 写明。

七、win:64 诊断方案（只写设计 WIN64_DIAG_PLAN_R8_M2a4.md，不运行）
列出 5 行的 env、驱动、诊断用断点（malloc 计数位置、r6_probe、ComputeLayerModes）、要观察的事实、确认索引的判据、补预注册文件名与冻结方式、正式两遍运行与判定入口。所有诊断观察标 INFLUENCED。

八、完整性 COMPLETENESS_R8_M2a4.tsv
逐行逐断言写：运行命令行（COMMAND_PLAN 行号）→事实来源字段（facts 脚本）→分析规则（state 分析器或 verdict 规则）→对照/参照→阳性对照覆盖用例（例号或回放）。任一环缺失写 BLOCKER 并说明；UNJUDGED_BY_DESIGN 单独计数。只有点数齐全、文件非空不能判 PASS。汇总写各状态计数并断言合计=150。

九、收尾
- 核对：两份历史预注册与 S4 树不变；新预注册 exp_* 改动=0；回放差异数；正式阳性对照全符合；dry-run 300 行且无驱动/gdb 启动；无实际 S4/gdb 运行；无越界改动。
- 小表原名复制到 checkpoints/p05/registries/s4r8/M2/r8m2a4/，写 SHA256SUMS.txt 并逐项比对原件；证据目录写 SHA256SUMS.txt；不改名复制。
- 追加 ERRATA（E8-101 起）与 RULINGS（U248–U252）。
- 更新一页以内 STATE.md：当前轮次、本轮数字（审计缺陷数、回放差异、阳性对照通过数、COMPLETENESS 分布、新预注册 sha）；开放项去向按 U248–U251 更新（M2-02、M2-08 转 S5；win:64 转 M2b 诊断）。
- 报告 checkpoints/p05/P05_S4R8_M2A4_REPORT.md，结尾写「本轮已完成 r8m2a4 范围，等待用户审核」，附 git log -1、git status --short。
- end 门禁 FAILS 非零不得提交。git add/commit 放入本轮脚本经 safe_run；提交仅限 checkpoints/p05/ 与 testing/d003/；提交信息以 awaiting user review 结尾。提交后用本轮 postcommit 脚本只读核对 HEAD、S4 树、冻结哈希、工作区，并说明 end/postcommit 小表的归档位置。

十、最终简短中文汇报
1. 判定缺陷审计（D1–D8 及新增）与修正方式；
2. 预注册 v2：exp_* 改动数（必须 0）、新增列、sha256 与冻结时间；
3. M2-04 双事件各项索引、fail_layer1/2 及依据（含 UNRESOLVED 项）；
4. M2-03 参照覆盖（有参照/NO_REF 数）、冻结的 san_options 与计数规则；
5. 历史 R6c 回放结果（177 点×I1–I6×两遍差异数）；
6. 合成阳性对照逐例结果；
7. dry-run 计划行数与身份核对结果；
8. COMPLETENESS 分布与 BLOCKER 清单；
9. 两张违规披露表、start/end 快照；
10. git log -1、git status --short、postcommit 原文。
本轮结束后等待规划者审核，不自行运行 M2b。
