# P05-S4 R7 续 9(同一子轮次 R7,不是新阶段):里程碑 M3 —— 状态判定回归(G5、G6)+ U38 分类 + R7 收尾

你是 P05-S4 的验证执行者。本轮仍是 P05-S4 的子轮次 R7,不得出现 P05-S6 或新的子轮次编号。
不得宣布任何阶段完成或签收。不修改 S4/、判定器,以及 testing/d003/ 下的历史装置(只导入或以子进程调用)。
先读 AGENTS.md、STATE.md、checkpoints/p05/P05_S4R7_REPORT_M2_FINAL.md、
P05_S4R6c_REPORT.md、P05_S4R6c_REPORT_ADDENDUM_seam.md、P05_S4R6c2_REPORT_PART2.md、
registries/s4r6c/(预注册 v2、SEAM、SEAM_CONTROL、RESULTS_R6c_STATE、RESULTS_R6c_SEAM、ERRATA_6c)。
证据目录沿用 checkpoints/p05/evidence/p05-s4r7/;已有文件一律不覆盖(U17)。run 标签:F 基线用 m3f1,F2 用 m3r1。
第一步:用 write 把本任务书原文存为 checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT9.md。
<如果用户已在对话中签收 P05-S3,规划者另行写入签收文件;执行者不写签收文件,也不在 STATE 中自行写签收。>

## 0. 操作规则
沿用续 5 第 0 节 A–E(写入只经 safe_run 或 edit/write;只读白名单;git add/commit 允许;只有违反写入规则才立即停下)。
另外:
- 不重新实现任何历史运行器、gdb 脚本或判定器。testing/d003/stage_s4/ 的 run_r6c_state.py、r6c_state_gdb.py、r6c_state.gdb、
  r6c_judge.py、run_r6c_seam_state.py 或 r6c2_seam_state.py、r6c2_seam_judge.py,一律以 `python3 -I -B <原脚本> <参数>` 调用,
  只通过参数换掉驱动路径和输出目录。若原脚本把路径或 sha256 写死,无法用参数替换,
  就复制为 stage_s4r7/<原名>_r7.py,只改这些常量,并把 diff 写进 $EV/RUNNER_DIFF_R7_M3.txt;出现其他改动就停下。
- 每个清单同时写一份标准格式(只有 "sha256  文件名" 两列),用于 sha256sum -c。

## 1. 用户裁决(用 edit 追加到 ERRATA_7.txt 与 RULINGS.tsv)
- U79:M2 里程碑(83a7511)经审核接受。E7-36:SHA256SUMS_M2b_run7.txt 与 SHA256SUMS_M2b_run7prep.txt 每行多了 "copied 时间戳" 两列,
  sha256sum -c 无法直接校验;去掉多余列后校验 0 处不一致。旧文件不改,本段补写标准格式的 *_std.txt。
- U80:M3 开工(U63)。M3 = G5(R6c 177 点状态判定)+ G6(R6c seam 25 点状态判定 + U18 对照 18 行)+ U38 分类 + R7 收尾。
- U81:M3 先在 R7 构建的 F 上复现 R6c 的结果(F 基线,m3f1),复现成功之后再跑 F2(m3r1)。
  F 基线与历史 R6c 的判定(HOLD/VIOLATED/N/A,逐点逐不变量)不一致,记为 ENV_DRIFT 并停下,不跑 F2。
- U82:G5、G6 的 F2 期望 = 历史 R6c 在 F 上的判定,逐点机械复制(I1–I6;I7 仍为 DEFERRED)。
  例外只有一种:点的失败路径经过 RNV1 窗口(pattern_generate_flow_field)。这类点必须在运行前列出,并给出 [源码] 依据;
  规划者预计数量为 0(RNV1 的点不在 177 点中)。

## 2. 准备(一次提交,提交之前不运行任何 M3 注入)
1. 驱动:
   - G5:状态驱动的 dbg 版本(R6c 使用的是 driver_r6b_state.cpp 加对应注入器,以 -O0 -g 构建)。按 R6b、R6c 的链接脚本,
     用 R7 的 F-dbg 与 F2-dbg 库各链接一个,写 $EV/DRIVERS_R7_M3.tsv。
     DRIVERS_R7.tsv 里已有的 r6bstate-F-dbg、r6bstate-F2-dbg,只有在源码和链接方式与 R6c 相同时才能复用,并写明依据。
   - G6:seam 状态驱动(R6c 中的 driver-r6b-seamF、driver-r6b-fmmret-F)。用 build_r7/seam 下的 dbg seam 库(seamF-F/F2、fmmret-F/F2),
     按 run_r6c_seam_dbg_build.sh 与 r6c2_link_fmmret.sh 的方式链接。
   - 编译选项与 R6c 的差异逐项列出(期望 0 项)。
2. gdb 锚点:列出 r6c_state.gdb、r6c_state_gdb.py、r6c_seam_gdb.gdb 中所有按 文件:行号 设的断点。
   F→F2 只改了 pattern.c 与 S4_internal.h 的注释,所以 S4.cpp 与 fmm/*.cpp 的行号应当不变;用 git diff 1c11905 a07b5ac --stat 确认。
   凡是锚点落在 pattern.c 中的,逐个写出 F2 的新行号;若无法唯一对应,就停下。写 $EV/LINEMAP_M3_R7.tsv。
3. 预注册 $EV/REGISTRY_S4_PRE_R7_M3.tsv(由脚本从 registries/s4r6c 的结果机械复制,源文件 sha256 写在表头):
   G5 177 行 × {F, F2},G6 25 行 + 18 行对照 × {F, F2},期望 = R6c 历史判定(逐不变量);U82 的例外行单独列出。
   写 sha256 与 UTC 时间。
4. dry-run:对每个点打印实际传给驱动的环境,用独立推导(从 R6b、R6c 的预注册和历史规则推导,不读本轮预注册)做断言;
   示例环境至少包括:1 个 R6c state 点、1 个 seam 点、1 个 U18 对照。无法解析 0,断言失败 0,驱动与库的 sha256 全部一致。
5. 用 edit 追加 E7-36 与 U79–U82;同步 STATE;提交准备。
   提交信息:"P05-S4 R7 cont9 prep: M3 drivers, gdb line map, prereg (copied from R6c), dry-run OK. awaiting user review"。

## 3. 运行
1. F 基线(m3f1):G5 177 点与 G6(25 点 + 18 对照)两遍,用历史判定器判定。
   与 R6c 逐点逐不变量比较,输出 $EV/M3_F_BASELINE_VS_R6c.tsv。
   要求 HOLD/VIOLATED/N/A 完全相同,FLAKY 0,GDB_DIVERGENT 0;不满足就停下(U81)。
2. F2(m3r1):同样两遍。输出 RESULTS、判定表,以及 $EV/REGRESS_R7_M3.tsv(逐点:历史 F、F(R7)、F2 pass1、F2 pass2、verdict)。
   期望(INFLUENCED):G5 HOLD 177 / VIOLATED 0;G6 HOLD 25 / VIOLATED 0,对照 18 行与历史相同;FLAKY 0;GDB_DIVERGENT 0;
   F 与 F2 在 rc1、rc2、rc3、hit 以及各不变量的判定上逐点相同。
3. 出现任何不一致:两遍跑完后停下,写报告,不改期望。

## 4. U38 分类(只读,不运行 S4)
$EV/PATTERN_MALLOC_CLASS_R7.tsv:F2 pattern.c 中全部 malloc(按 F2 的行号),每一个写:函数、调用者链([源码])、有无 NULL 检查、
是否在 "模式或缓存安装验收路径 / FMM 或 FFT 失败传播链" 上(按 P05 范围判据),以及建议分类
(IN_D003_CANDIDATE / OUT_OF_SCOPE_D003 / UNCLEAR)。
规划者的初步意见(供核对,不得照抄):806(pattern_get_containment_tree,经 S4.cpp:1730 Simulation_InitSolution)可能是 IN_D003_CANDIDATE;
415、528(面积计算)与 1164(格式化输出)可能是 OUT_OF_SCOPE 或 UNCLEAR。只给建议,裁决归用户。

## 5. R7 收尾
- 红点状态表 $EV/RED_POINTS_STATUS_R7.tsv(以 S3R3 状态表为基础,加 R7_M1、R7_M2、R7_M3 列);
  RP-R6d-1 只写 "F2 回归 REPORTED_FAILURE 63/63(两遍,M1)",不得写 "已修好" 或 "已验证"。
- 报告 checkpoints/p05/P05_S4R7_REPORT_FINAL.md:R7 全部里程碑(PART1、M1、M1a、M2a、M2b run7、M3)的结果汇总;
  作废的运行(run5、run6)及其原因;E7-1..E7-最后;U34..最后;U38 分类建议;
  待用户裁决(至少:U38 分类;R8 的范围与开工;P05-S4 是否签收由用户在 R8 之后决定);违规两张表。
  所有数字都要经核对脚本核对(退出码 0)。结尾写 "本轮已完成/未完成 R7 范围,等待用户审核",附 git log -3 与 git status --short。
- 小型表复制到 registries/s4r7/,写标准格式的 SHA256SUMS_M3.txt 并校验;用 edit 更新 STATE(一页以内)。
- 提交:"P05-S4 R7 milestone M3 and R7 closeout ... awaiting user review"。之后停下。

## 6. 停止条件
- 违反写入规则;
- 编译选项与 R6c 有差异且无法解释;gdb 锚点无法唯一对应;
- dry-run 不通过;准备提交完成之前就运行了 M3;
- F 基线与 R6c 不一致(U81),或者 F2 出现任何 VIOLATED、FLAKY、GDB_DIVERGENT 或与 F 不同;
- 报告数字核对不通过。
"未完成"与"不可行"必须区分。
