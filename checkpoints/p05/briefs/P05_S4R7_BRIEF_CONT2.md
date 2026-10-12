# P05-S4 R7 续 2(同一子轮次 R7,不是新阶段):M1 补遗 + 里程碑 M2(G1–G4 rc 类回归)

你是 P05-S4 的验证执行者。本轮仍是 P05-S4 的子轮次 R7,不得出现 P05-S6 或新的子轮次编号。
不得宣布任何阶段完成或签收。不修改 S4/。
先读 AGENTS.md、checkpoints/p05/STATE.md、checkpoints/p05/briefs/P05_S4R7_BRIEF.md、P05_S4R7_BRIEF_CONT1.md(仍然有效),
checkpoints/p05/registries/s4r7/ERRATA_7.txt、checkpoints/p05/P05_S4R7_REPORT_M1.md。
证据目录沿用 checkpoints/p05/evidence/p05-s4r7/;已有文件一律不覆盖(U17)。本段的 run 标签从 run3 开始。
第一步:用 write 把本任务书原文存为 checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT2.md。

## 0. 硬规则
与 R7 原任务书第 0 节、续 1 第 0 节相同。所有写入经 `sh testing/d003/safe_run.sh p05-s4r7 -- sh -c '...' sh ...`。
已提交的报告(P05_S4R7_REPORT_PART1.md、P05_S4R7_REPORT_M1.md)不改写,更正一律写进 ERRATA_7 或新的附录文件。

## 1. 用户裁决(追加到 ERRATA_7.txt 与 RULINGS.tsv;原有行不改)
- U44:E7-8 认定为预注册生成器与运行器的列错误:生成器把 rc 期望写进 expected_class,运行器从 expected_win1_rc 读期望,
  又要求 expected_class == CONTROL_OK,两边各错一半。原 RESULTS 与 REGRESS 中这 18 行保持 MISMATCH,不改。
  按第 2.2 节离线重新判定,标 POSTHOC。另外:vl/fftvl NG1 的对照 rc1 = 20,按判定器的定义不属于 CONTROL_OK,
  预注册把它写成 CONTROL_OK 本身也是错误,一并记录。
- U45:FMMGetEpsilon_PolBasisJones 那一层的返回值不接受为已知限制,按第 2.1 节用行断点补读(不用 finish)。
- U46:M2 开工。G1–G4 在 R7 构建的 F 与 F2 上都运行(只跑 F 行对应的点,B 不重跑)。
- U47:P05-S3 是否签收,在 M2 里程碑结果交给用户后再决定。
- U48:M1 报告第 5 行的 "F2 上 RNV1 相关点 90/90 MATCH" 措辞错误,正确表述是
  "F2 注入点 63/63 REPORTED_FAILURE(两遍),F 注入点 27/27 CRASH(两遍)"(E7-13)。

## 2. M1 补遗(M1a)
2.1 PolBasisJones 返回值(gdb,F2 dbg,run3)
- 先用 grep -n 在 F2 导出树中确认行号:fmm_PolBasisJones.cpp 中 `Pattern_GenerateFlowField` 失败分支的 `return error;`
  (规划者读到的是 192),以及 S4.cpp 中 `if(0 != fmm_ret){`(规划者读到的是 2413)。行号写入 $EV/LINEMAP_A1_R7.tsv。
- 新 gdb 脚本 testing/d003/stage_s4r7/gdb_chain_jones_line_r7.gdb:
  在这两行设断点,命中后分别 `print error` 与 `print fmm_ret`,然后 `continue`;不使用 finish。
- 点:jones NG9 M1、M3;fftjones NG9 M1。每次运行的日志名唯一(run3_seqN),失败的运行也保留。
- 写 $EV/GDB_CHAIN_SUMMARY_R7_A1.tsv(新文件,不改 GDB_CHAIN_SUMMARY_R7.tsv):
  每点记录 pattern 返回值(引用 M1 的 finish 日志)、PolBasisJones 的 error、S4.cpp 的 fmm_ret、RC first。
  期望(INFLUENCED,[源码]):error = −11,fmm_ret = −11,RC first 20。读不到就写"未读到"。
2.2 对照离线重新判定(不重跑)
- 新建 $EV/REGISTRY_S4_PRE_R7_M1_ERRATA_CTRL.txt:说明列错误,逐行给出原注册表中已有的 rc 期望字符串(原样引用,不改数值),
  以及新的判定规则:rc1、rc2、run_rc 与注册字符串相等,且 hit = 0。
  rc 全为 0 的行判 CONTROL_OK;vl/fftvl NG1(rc1 = 20)判 BASELINE_RC_EQUAL(不是 CONTROL_OK)。
- 新脚本只读 m1_selfcheck/M1-CTRL-*/pass{1,2}_run2/nogdb.out,输出 $EV/RESULTS_R7_M1_CTRL_REJUDGE_POSTHOC.tsv。
  期望(INFLUENCED):两遍各 16 行 CONTROL_OK、2 行 BASELINE_RC_EQUAL、0 行不相等。
2.3 校验与状态
- E7-12:registries/s4r7/SHA256SUMS.txt 对 ERRATA_7.txt 校验失败,原因是 M1 追加了 E7-8 到 E7-11,
  而 SHA256SUMS_M1.txt 未收录 ERRATA_7。旧清单不改;本段在 SHA256SUMS_M2.txt 中收录 ERRATA_7、STATE.md 的当前版本。
- STATE.md 中 RNV1(RP-R6d-1)一行更新为 "R7 M1:F2 注入点 63/63 REPORTED_FAILURE,两遍;未称已修好或已验证"。

## 3. M2 准备
3.1 plain seam 库:R4 的 seam 点(seamF 15 点、fmmret-F 10 点)使用的是 R4 的构建方式。
  先从 registries/s4r4/LIBS_R4.tsv 与 R4 报告读出 R4 seam 库的实际编译选项,写入 $EV/BUILD_SEAM_PLAIN_R7.tsv 表头;
  再用新脚本 build_seam_plain_s4r7.sh,按相同选项在 F 与 F2 上构建 seamF 与 fmmret(源码使用 seam_r7/ 中已应用的树的副本)。
  记录告警数、库 sha256。如果读不出 R4 的选项,写 E7-x 并停下这一项。
3.2 驱动:G1–G4 各自的历史驱动或注入器(R3 sweep、R4 matrix/plancall/regress、R5 planm、R6 twice)链接到 R7 的 F 与 F2 plain 库
  (seam 点链接第 3.1 节的库)。写入 $EV/DRIVERS_R7_M2.tsv。
3.3 运行器:历史运行器复制到 stage_s4r7/ 并加 _r7 后缀。只改树标签、驱动路径、sha256 常量、输出目录;diff 写入 $EV/RUNNER_DIFF_R7_M2.txt。
  所有运行器加 `--dry-parse` 选项:只读注册表,检查每一行的期望字段都能被判定代码解析,打印无法解析的行数,不运行 S4。

## 4. M2 预注册(INFLUENCED;写完、记录 sha256 和 UTC 时间之后才能运行)
文件 $EV/REGISTRY_S4_PRE_R7_M2.tsv,由新脚本 make_prereg_m2_r7.py 生成,来源文件及其 sha256 写在表头。
| 组 | 内容 | 来源(F 行) |
|---|---|---|
| G1 | R3 的 149 个 F 行(141 注入 + 8 对照;其中 22 个 plan 点在 R3 中为 INVALID,按 E7-4 携带) | registries/s4r3/RESULTS_R3.tsv |
| G2a | R4 seam 25 点(seamF 15、fmmret-F 10) | registries/s4r4/RESULTS_R4.tsv |
| G2b | R4 plancall 22 个 F 点(两遍) | registries/s4r4/RESULTS_R4_PLANCALL_pass{1,2}.tsv |
| G2c | R4 regress 30 个 F 点 + 7 个对照 | registries/s4r4/REGRESS_R4.tsv、CONTROL_R4.tsv |
| G3 | R5 M=2 的 36 个 F 点 | registries/s4r5/RESULTS_R5_PLANM_pass{1,2}.tsv |
| G4 | R6-1 TWICE=slab 的 12 个 F 点 | registries/s4r6/RESULTS_R6_TWICE_pass{1,2}.tsv |
- 每个点生成两行:tree=F(R7 构建,期望 = 历史 F 类别)与 tree=F2(期望 = 历史 F 类别)。
  依据:F→F2 只改 pattern.c 中的 RNV1 窗口与 S4_internal.h 的注释;G1–G4 的注入点都不在 RNV1 窗口内([源码])。
  如果某个点的注入位置在 pattern.c 内或与 RNV1 窗口重叠,运行前把它单独列出,并写 E7-x 说明。
- 对照行的期望列格式必须与运行器的读取方式一致。生成后、计算哈希之前,对每个运行器跑一次 `--dry-parse`,结果写入
  $EV/DRYPARSE_R7_M2.txt,要求无法解析的行数为 0;不为 0 就修生成器重新生成(此时尚未哈希,不算改期望)。
- 如果某个来源组的 F 两遍结果本身不一致,或某些点的类别依赖注入次序,在预注册前写 E7-x,不要猜。

## 5. M2 运行与判定
- 每点两遍(pass1、pass2,run3),判定用 judge_d003.classify(只导入,不修改)。
- 结果写 $EV/RESULTS_R7_M2_<组>_pass{1,2}_run3.tsv。
- 对比表 $EV/REGRESS_R7_M2.tsv:point_id、历史 F 类别、F(R7) pass1/pass2、F2 pass1/pass2、verdict。
  verdict 取值:
  MATCH(四次都等于历史 F 类别)
  REGRESSION(F(R7) 等于历史而 F2 不等)
  ENV_DRIFT(F(R7) 本身不等于历史;此时 F2 与 F(R7) 的比较单独列出)
  FLAKY(两遍不一致)
  MISMATCH(其他)
- 除类别外,F2 与 F(R7) 的 rc、rc1、rc2、hit 逐项比较,不一致的单列。
- 任何 REGRESSION、ENV_DRIFT、FLAKY 或 MISMATCH:该组两遍跑完后停下,写报告;不改期望,不重跑覆盖。

## 6. M2 提交
- 小型表(LINEMAP_A1、GDB_CHAIN_SUMMARY_R7_A1、CTRL 勘误与重新判定表、BUILD_SEAM_PLAIN、DRIVERS_R7_M2、RUNNER_DIFF_R7_M2、
  DRYPARSE、预注册及其 sha256 和时间戳、各组 RESULTS、REGRESS_R7_M2)复制到 registries/s4r7/,
  写 SHA256SUMS_M2.txt(同时收录 ERRATA_7 与 STATE 的当前版本)并逐个比对;证据目录写 SHA256SUMS_M2.txt。
- 写 P05_S4R7_REPORT_M2.md,须包含:
  M1a 的三项结果(Jones 层返回值实测到哪一层;对照 POSTHOC 计数;E7-12、E7-13);
  plain seam 构建;预注册摘要与 dry-parse;每组两遍结果与 REGRESS 汇总(按 verdict 计数);
  F2 与 F(R7) 的 rc 逐项差异;需要用户裁决的事项(至少:P05-S3 是否签收,U47;M3 是否开工);违规两张表。
  结尾写"本轮未完成 R7 范围(M2 已完成/未完成),等待用户审核"。
- 更新 STATE.md(一页以内)。提交信息写 "P05-S4 R7 milestone M2 ... awaiting user review"。
- M2 提交之后停下,不进入 M3。

## 7. 停止条件
R7 原任务书第 8 节与续 1 第 7 节全部有效,另外:
- 第 3.1 节读不出 R4 seam 库的编译选项(只停该项,G2a 标"未运行");
- dry-parse 在哈希前无法做到 0 行无法解析;
- 任一组出现 REGRESSION、ENV_DRIFT、FLAKY 或 MISMATCH(该组两遍跑完后停)。
"未完成"与"不可行"必须区分。
