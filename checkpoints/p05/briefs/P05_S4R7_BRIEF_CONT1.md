# P05-S4 R7 续(同一子轮次 R7,不是新阶段):第一段提交 + 里程碑 M1(RNV1 回归)

你是 P05-S4 的验证执行者。本轮仍是 P05-S4 的子轮次 R7(续),不得出现 P05-S6 或新的子轮次编号。
不得宣布任何阶段完成或签收。不修改 S4/。
先读 AGENTS.md、checkpoints/p05/STATE.md、checkpoints/p05/briefs/P05_S4R7_BRIEF.md(R7 原任务书,仍然有效,本任务书只补充和修改),
checkpoints/p05/registries/s4r7/ERRATA_7.txt、checkpoints/p05/evidence/p05-s4r7/R7_PROGRESS_RECORD.txt。
证据目录仍是 checkpoints/p05/evidence/p05-s4r7/(沿用,已有文件一律不覆盖,U17)。
第一步:用 write 把本任务书原文存为 checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT1.md。

## 0. 硬规则
与 R7 原任务书第 0 节相同,另外:
- 每条含写入的命令都经 `sh testing/d003/safe_run.sh p05-s4r7 -- sh -c '...' sh ...` 运行,包括 cmp/sha256sum/grep 的重定向。
- 新运行一律用新的 run 标签(本段从 run2 开始),写进新文件;不在旧目录里追加。
- 不对 $EV/tmp/base_F、base_F2 做任何改动,也不复制进 git。

## 1. 用户裁决(追加到 ERRATA_7.txt 和 RULINGS.tsv;原有行不改)
- U40:E7-3 的根因是 R7 任务书 4.3 节写了 "closed"(规划者错误),驱动只接受 closed2d/closed1d。
  在 E7-3 后追加说明 "根因:任务书错误(规划者)"。4.3 门禁在 run1b 之后视为通过(条件:第 2 节第 2 条的结果表已生成)。
- U41:R7 拆成三个里程碑,每个各提交一次:M1 = G7、G8、4.2 新增点、jones gdb 链、U36 离线表;M2 = G1–G4;
  M3 = G5、G6、U38 分类、R7 收尾报告。三段都属于 R7。
- U42:先做第一段提交(第 2 节),之后再做 M1。
- U43:E7-7:ERRATA_7 写的是 U34–U39 "also appended to RULINGS.tsv",实际 RULINGS.tsv 中没有这些行
  (只读核对:grep "^U3[4-9]" 计数为 0)。本段补上 U34–U43,并如实记录这条不一致。

## 2. 第一段提交(R7 part 1)
1. 门禁复核:HEAD 仍为 8e13729…,HEAD:S4 = F2,判定器 sha256 一致;git status 只有 R7 未跟踪文件。
   写入 $EV/GATE_R7_CONT1.txt(新文件,新脚本 testing/d003/stage_s4r7/r7_gate_cont1.py,或给 r7_gate.py 加参数后另存为新文件;不改 r7_gate.py 的已有行为)。
2. run1b 结果表:新脚本只读 $EV/noinject_r7/run1b/ 已有的输出,对 F 与 F2 的 call1–3 做 cmp,
   解析 stdout 的 RC first / RC retry,写 $EV/RESULTS_R7_NOINJECT_run1b.tsv。不重跑驱动。
   期望(规划者已用 cmp 只读核对,INFLUENCED):9/9 IDENTICAL,rc 0/0。
3. RULINGS.tsv 追加 U34–U43;STATE.md 按 E7-1、E7-2 更新,当前轮次写
   "P05-S4 R7 进行中:门禁、构建、seam diff、无注入等价已完成;注入矩阵未运行;下一步 M1"。保持一页以内。
4. 小型表(GATE_R7、GATE_R7_CONT1、TREE_MANIFEST_R7、BUILD_R7、BUILD_SEAM_R7、DRIVERS_R7、SEAM_DIFF_F_vs_F2_R7、
   RESULTS_R7_NOINJECT_run1、run1b、R7_PROGRESS_RECORD)复制到 checkpoints/p05/registries/s4r7/,写 SHA256SUMS.txt 并逐个比对。
5. 写 checkpoints/p05/P05_S4R7_REPORT_PART1.md(短报告):已完成项、E7-1..E7-7、违规两张表;
   结尾写 "本轮未完成 R7 范围(第一段),等待用户审核",附 git log -1 与 git status --short。
6. 提交范围:checkpoints/p05/(briefs、registries/s4r7、RULINGS、STATE、报告)、testing/d003/stage_s4r7/。
   提交信息:"P05-S4 R7 part 1 (partial): gate, builds, seam diff, no-injection equivalence; injection not run. awaiting user review"。

## 3. M1 准备
1. 行号清点:F→F2 的 pattern.c 行号有偏移(例如 cg work 1251→1253,rect 1477/1481→1489/1499,tri 1656/1660→1679/1689;以 F2 实际为准)。
   列出 testing/d003/stage_s4/、stage_s3r3/ 中所有含 pattern.c 行号或函数断点的 gdb 脚本和 python,写 $EV/LINEMAP_F_F2_R7.tsv
   (文件、原行号、F2 行号、依据 grep 结果)。需要用到的脚本复制到 stage_s4r7/ 并加 _r7 后缀,只改行号;diff 写入 RUNNER_DIFF_R7.txt。
   S4.cpp 和 fmm/*.cpp 在 F→F2 之间没有改动,行号不变;但要用 git diff 1c11905 a07b5ac --stat 确认这一点并写进表头。
2. 驱动补齐:tri 驱动的 dbg 版本(F、F2,用 build_r7 的 dbg 库)。追加记录到新文件 DRIVERS_R7_cont1.tsv,不改 DRIVERS_R7.tsv。
3. jones/fftjones 窗口映射(4.2):F dbg 上无注入运行 r6dnv1 驱动,jones、fftjones × NG1/5/9;tri 驱动 vl、jones NG9。
   用 gdb 记录 RNV1 窗口内 malloc 的次数、字节数和源码位置,写 $EV/RNV1_JONES_MAP_R7.tsv。
   F 上无注入 rc 非零或无法进入窗口:如实记录,该项停下,不换几何体。

## 4. M1 预注册(全部写完,记录 sha256 和 UTC 时间之后,才运行任何注入;状态 INFLUENCED)
文件 $EV/REGISTRY_S4_PRE_R7_M1.tsv,包含:
- G7:RNV1 36 点(nv/vl/fftnv/fftvl × NG1/5/9 × M1–3)在 F2 dbg 上。F 类别从 registries/s4r6d/RESULTS_R6d_RNV1_pass2_run2.tsv 机械复制(CRASH),
  F2 期望 REPORTED_FAILURE(rc1 = 20,hit 1)。另加列 expected_win1_rc = −11。
- G8:tri nv NG9 M1–3,F 和 F2 各 3 点;期望从 registries/s3r3/REGISTRY_S3R3_SELFCHECK.tsv 第 C2 节复制。
- 4.2 新增:jones/fftjones(F 与 F2)、tri vl/jones NG9(F 与 F2),M 取映射表实测的窗口 malloc 次数。F 期望 CRASH,F2 期望 REPORTED_FAILURE,
  标 "无历史 F 实测;[源码]+映射"。
- 对照:每个 (驱动, 模式, NG) 在 F2 上一行无注入 CONTROL_OK(vl/fftvl NG1 的对照期望 rc 20,依据 run1 无注入结果)。
预注册由脚本生成,脚本提交;来源文件及其 sha256 写在表头。

## 5. M1 运行与判定
- 每点两遍(pass1、pass2,run2 标签),只用无 gdb 运行判定;判定用 judge_d003.classify(只导入)。
- 结果写 $EV/RESULTS_R7_M1_pass{1,2}_run2.tsv,列中包含 win1_rc(解析 R6D_WIN_CLOSE k=1)与 RC first。
- 生成 $EV/REGRESS_R7_M1.tsv:point_id、F 类别、F2 期望、pass1、pass2、verdict
  (MATCH / IMPROVED_AS_EXPECTED / REGRESSION / FLAKY / MISMATCH)。
- gdb 链:jones、fftjones 各抽 1 点(F2 dbg,M=1 与 M=3 各 1 点),逐层读 pattern_generate_flow_field、
  FMMGetEpsilon_PolBasisJones 的返回值,以及 ComputeLayerModes 的 rc。读不到的层写 "未读到",不得用源码补。
  每次 gdb 运行的日志文件名都要唯一(带 run 标签和序号),失败的运行也保留。
- U36 离线表 $EV/VL_NG1_SPLIT_R7.tsv:汇总 S3R3 selfcheck 日志和本段 G7 日志中 vl/fftvl NG1 M1–3 两遍的 win1_rc、k=2/3 的 rc、RC first。
  期望(规划者已读 S3R3 日志,INFLUENCED):win1_rc = −11,k=2、3 = −10,RC first 20。不新增运行。
- 任一组出现 MISMATCH、REGRESSION 或 FLAKY:两遍跑完后停下,写报告等待裁决;不改期望,不重跑覆盖。

## 6. M1 提交
- 小型表(LINEMAP、映射表、预注册及其 sha256 和时间戳、RESULTS、REGRESS_R7_M1、VL_NG1_SPLIT、gdb 链摘要表)复制到 registries/s4r7/,
  写新的 SHA256SUMS_M1.txt 并逐个比对;证据目录写 SHA256SUMS_M1.txt(不收录清单自身与 safe_run.log)。
- 写 P05_S4R7_REPORT_M1.md:门禁;行号清点;映射;预注册摘要;结果两遍与 REGRESS 汇总;gdb 链(写清实测到哪一层);
  离线表;RP-R6d-1 状态(只能写 "F2 回归 REPORTED_FAILURE x/y,两遍",不得写 "已修好" 或 "已验证");
  需要用户裁决的事项(至少:P05-S3 是否签收;M2 是否开工);违规两张表。
  结尾写 "本轮未完成 R7 范围(M1 已完成/未完成),等待用户审核"。
- 更新 STATE.md,提交信息写 "P05-S4 R7 milestone M1 ... awaiting user review"。
- M1 提交之后停下,不进入 M2。

## 7. 停止条件
R7 原任务书第 8 节全部有效,另外:
- 第 2 节第 2 条的 run1b 结果不是 9/9 IDENTICAL;
- 行号清点发现历史脚本的断点在 F2 上无法唯一对应;
- 违规达到第 0 节的阈值。
"未完成" 与 "不可行" 必须区分。
